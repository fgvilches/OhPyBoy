from savedata import FlashSavedata

class MemoryView:
    def __init__(self, memory, offset=0):
        self.buffer = memory
        self.view = memory[offset:] if offset else memory
        self.mask = len(memory) - 1
        self.reset_mask()

    def reset_mask(self):
        self.mask8 = self.mask & 0xffffffff
        self.mask16 = self.mask & 0xfffffffe
        self.mask32 = self.mask & 0xfffffffc
    
    def load8(self, offset):
        return self.view[offset & self.mask8]

    def load16(self, offset):
        return self.view[offset & self.mask16]

    def loadU8(self, offset):
        return self.view[offset & self.mask8]

    def loadU16(self, offset):
        return self.view[offset & self.mask16]

    def load32(self, offset):
        rotate = (offset & 3) << 3
        mem = self.view[offset & self.mask32]
        return (mem >> rotate) | (mem << (32 - rotate))

    def store8(self, offset, value):
        self.view[offset & self.mask8] = value

    def store16(self, offset, value):
        self.view[offset & self.mask16] = value

    def store32(self, offset, value):
        self.view[offset & self.mask32] = value

    def invalidatePage(self, address):
        pass

    def replaceData(self, memory, offset=0):
        self.buffer = memory
        self.view = memory[offset:] if offset else memory
        self.reset_mask()

class MemoryBlock(MemoryView):
    def __init__(self, size, cacheBits):
        super().__init__(bytearray(size))
        self.ICACHE_PAGE_BITS = cacheBits
        self.PAGE_MASK = (2 << self.ICACHE_PAGE_BITS) - 1
        self.icache = [None] * (size >> (self.ICACHE_PAGE_BITS + 1))

    def invalidatePage(self, address):
        page = self.icache[(address & self.mask) >> self.ICACHE_PAGE_BITS]
        if page:
            page['invalid'] = True


class ROMView(MemoryView):
    def __init__(self, rom, offset=0):
        super().__init__(rom, offset)
        self.ICACHE_PAGE_BITS = 10
        self.PAGE_MASK = (2 << self.ICACHE_PAGE_BITS) - 1
        self.icache = [None] * (len(rom) >> (self.ICACHE_PAGE_BITS + 1))
        self.mask = 0x01ffffff
        self.reset_mask()

    def store8(self, offset, value):
        pass

    def store16(self, offset, value):
        if 0xc4 <= offset < 0xca:
            if not self.gpio:
                self.gpio = self.mmu.allocGPIO(self)
            self.gpio.store16(offset, value)

    def store32(self, offset, value):
        if 0xc4 <= offset < 0xca:
            if not self.gpio:
                self.gpio = self.mmu.allocGPIO(self)
            self.gpio.store32(offset, value)


class BIOSView(MemoryView):
    def __init__(self, rom, offset=0):
        super().__init__(rom, offset)
        self.ICACHE_PAGE_BITS = 16
        self.PAGE_MASK = (2 << self.ICACHE_PAGE_BITS) - 1
        self.icache = [None]

    def load8(self, offset):
        if offset >= len(self.buffer):
            return -1
        return self.view[offset]

    def load16(self, offset):
        if offset >= len(self.buffer):
            return -1
        return self.view[offset]

    def loadU8(self, offset):
        if offset >= len(self.buffer):
            return -1
        return self.view[offset]

    def loadU16(self, offset):
        if offset >= len(self.buffer):
            return -1
        return self.view[offset]

    def load32(self, offset):
        if offset >= len(self.buffer):
            return -1
        return self.view[offset]

    def store8(self, offset, value):
        pass

    def store16(self, offset, value):
        pass

    def store32(self, offset, value):
        pass


class BadMemory:
    def __init__(self, mmu, cpu):
        self.cpu = cpu
        self.mmu = mmu

    def load8(self, offset):
        return self.mmu.load8(
            self.cpu.gprs[self.cpu.PC] -
            self.cpu.instructionWidth +
            (offset & 0x3)
        )

    def load16(self, offset):
        return self.mmu.load16(
            self.cpu.gprs[self.cpu.PC] -
            self.cpu.instructionWidth +
            (offset & 0x2)
        )

    def loadU8(self, offset):
        return self.mmu.loadU8(
            self.cpu.gprs[self.cpu.PC] -
            self.cpu.instructionWidth +
            (offset & 0x3)
        )

    def loadU16(self, offset):
        return self.mmu.loadU16(
            self.cpu.gprs[self.cpu.PC] -
            self.cpu.instructionWidth +
            (offset & 0x2)
        )

    def load32(self, offset):
        if self.cpu.execMode == self.cpu.MODE_ARM:
            return self.mmu.load32(
                self.cpu.gprs[self.cpu.gprs.PC] - self.cpu.instructionWidth
            )
        else:
            halfword = self.mmu.loadU16(
                self.cpu.gprs[self.cpu.PC] - self.cpu.instructionWidth
            )
            return halfword | (halfword << 16)

    def store8(self, offset, value):
        pass

    def store16(self, offset, value):
        pass

    def store32(self, offset, value):
        pass

    def invalidatePage(self, address):
        pass


class GameBoyAdvanceMMU:
    def __init__(self):
        self.REGION_BIOS = 0x0
        self.REGION_WORKING_RAM = 0x2
        self.REGION_WORKING_IRAM = 0x3
        self.REGION_IO = 0x4
        self.REGION_PALETTE_RAM = 0x5
        self.REGION_VRAM = 0x6
        self.REGION_OAM = 0x7
        self.REGION_CART0 = 0x8
        self.REGION_CART1 = 0xa
        self.REGION_CART2 = 0xc
        self.REGION_CART_SRAM = 0xe

        self.BASE_BIOS = 0x00000000
        self.BASE_WORKING_RAM = 0x02000000
        self.BASE_WORKING_IRAM = 0x03000000
        self.BASE_IO = 0x04000000
        self.BASE_PALETTE_RAM = 0x05000000
        self.BASE_VRAM = 0x06000000
        self.BASE_OAM = 0x07000000
        self.BASE_CART0 = 0x08000000
        self.BASE_CART1 = 0x0a000000
        self.BASE_CART2 = 0x0c000000
        self.BASE_CART_SRAM = 0x0e000000

        self.BASE_MASK = 0x0f000000
        self.BASE_OFFSET = 24
        self.OFFSET_MASK = 0x00ffffff

        self.SIZE_BIOS = 0x00004000
        self.SIZE_WORKING_RAM = 0x00040000
        self.SIZE_WORKING_IRAM = 0x00008000
        self.SIZE_IO = 0x00000400
        self.SIZE_PALETTE_RAM = 0x00000400
        self.SIZE_VRAM = 0x00018000
        self.SIZE_OAM = 0x00000400
        self.SIZE_CART0 = 0x02000000
        self.SIZE_CART1 = 0x02000000
        self.SIZE_CART2 = 0x02000000
        self.SIZE_CART_SRAM = 0x00008000
        self.SIZE_CART_FLASH512 = 0x00010000
        self.SIZE_CART_FLASH1M = 0x00020000
        self.SIZE_CART_EEPROM = 0x00002000

        self.DMA_TIMING_NOW = 0
        self.DMA_TIMING_VBLANK = 1
        self.DMA_TIMING_HBLANK = 2
        self.DMA_TIMING_CUSTOM = 3

        self.DMA_INCREMENT = 0
        self.DMA_DECREMENT = 1
        self.DMA_FIXED = 2
        self.DMA_INCREMENT_RELOAD = 3

        self.DMA_OFFSET = [1, -1, 0, 1]

        #self.WAITSTATES = [0, 0, 2, 0, 0, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4]
        #self.WAITSTATES_32 = [0, 0, 5, 0, 0, 1, 0, 1, 7, 7, 9, 9, 13, 13, 8]
        #self.WAITSTATES_SEQ = [0, 0, 2, 0, 0, 0, 0, 0, 2, 2, 4, 4, 8, 8, 4]
        #self.WAITSTATES_SEQ_32 = [0, 0, 5, 0, 0, 1, 0, 1, 5, 5, 9, 9, 17, 17, 8]
        #self.NULLWAIT = [0] * 256
        self.WAITSTATES = [0] * 256
        self.WAITSTATES_32 = [0] * 256
        self.WAITSTATES_SEQ = [0] * 256
        self.WAITSTATES_SEQ_32 = [0] * 256
        self.NULLWAIT = [0] * 256
        for i in range(15, 256):
            pass
        #for i in range(15, 256):
        #    self.WAITSTATES[i] = 0
        #    self.WAITSTATES_32[i] = 0
        #    self.WAITSTATES_SEQ[i] = 0
        #    self.WAITSTATES_SEQ_32[i] = 0
        #    self.NULLWAIT[i] = 0

        self.ROM_WS = [4, 3, 2, 8]
        self.ROM_WS_SEQ = [[2, 1], [4, 1], [8, 1]]

        self.ICACHE_PAGE_BITS = 8
        self.PAGE_MASK = (2 << self.ICACHE_PAGE_BITS) - 1

        self.bios = None

        self.memory = {}
        
    def mmap(self, region, obj):
        self.memory[region] = obj

    def invalidate_caches(self, address):
        region = address >> self.BASE_OFFSET
        if region < 255:
            mem_block = self.memory[region]
            if hasattr(mem_block, 'invalidatePage'):
                mem_block.invalidatePage(address)

    def clear(self):
        self.badMemory = BadMemory(self, self.cpu)
        self.memory = [
            self.bios,
            self.badMemory,
            MemoryBlock(self.SIZE_WORKING_RAM, 9),
            MemoryBlock(self.SIZE_WORKING_IRAM, 7),
            None,  # This is owned by GameBoyAdvanceIO
            None,  # This is owned by GameBoyAdvancePalette
            None,  # This is owned by GameBoyAdvanceVRAM
            None,  # This is owned by GameBoyAdvanceOAM
            self.badMemory,
            self.badMemory,
            self.badMemory,
            self.badMemory,
            self.badMemory,
            self.badMemory,
            self.badMemory,
            self.badMemory,  # Unused
        ]
        for i in range(16, 256):
            self.memory[i] = self.badMemory
        self.memory[255] = self.badMemory
        self.waitstates = self.WAITSTATES[:]
        self.waitstatesSeq = self.WAITSTATES_SEQ[:]
        self.waitstates32 = self.WAITSTATES_32[:]
        self.waitstatesSeq32 = self.WAITSTATES_SEQ_32[:]
        self.waitstatesPrefetch = self.WAITSTATES_SEQ[:]
        self.waitstatesPrefetch32 = self.WAITSTATES_SEQ_32[:]

        self.cart = None
        self.save = None

        self.DMA_REGISTER = [
            self.core.io.DMA0CNT_HI >> 1,
            self.core.io.DMA1CNT_HI >> 1,
            self.core.io.DMA2CNT_HI >> 1,
            self.core.io.DMA3CNT_HI >> 1,
        ]

    def freeze(self):
        return {
            'ram': self.memory[self.REGION_WORKING_RAM].buffer,
            'iram': self.memory[self.REGION_WORKING_IRAM].buffer,
        }

    def defrost(self, frost):
        self.memory[self.REGION_WORKING_RAM].replaceData(frost['ram'])
        self.memory[self.REGION_WORKING_IRAM].replaceData(frost['iram'])

    def loadBios(self, bios, real):
        self.bios = BIOSView(bios)
        self.bios.real = bool(real)

    def loadRom(self, data, raw=False, process=None):
        global rom
        rom = data
        cart = {
            'title': None,
            'code': None,
            'maker': None,
            'memory': data,
            'saveType': None,
        }

        lo = ROMView(rom)
        if lo.view[0xb2] != 0x96:
            return None

        lo.mmu = self  # Needed for GPIO
        self.memory[self.REGION_CART0] = lo
        self.memory[self.REGION_CART1] = lo
        self.memory[self.REGION_CART2] = lo

        if len(rom) > 0x01000000:
            hi = ROMView(rom, 0x01000000)
            self.memory[self.REGION_CART0 + 1] = hi
            self.memory[self.REGION_CART1 + 1] = hi
            self.memory[self.REGION_CART2 + 1] = hi

        if process:
            name = ''.join(chr(lo.view[i + 0xa0]) for i in range(12) if lo.view[i + 0xa0])
            cart['title'] = name

            code = ''.join(chr(lo.view[i + 0xac]) for i in range(4) if lo.view[i + 0xac])
            cart['code'] = code

            maker = ''.join(chr(lo.view[i + 0xb0]) for i in range(2) if lo.view[i + 0xb0])
            cart['maker'] = maker

            state = ''
            terminal = False
            for i in range(0xe4, len(rom)):
                next_char = chr(lo.view[i])
                state += next_char
                if state in ['F', 'FL', 'FLA', 'FLAS', 'FLASH', 'FLASH_', 'FLASH5', 'FLASH51', 'FLASH512', 'FLASH512_', 'FLASH1', 'FLASH1M', 'FLASH1M_', 'S', 'SR', 'SRA', 'SRAM', 'SRAM_', 'E', 'EE', 'EEP', 'EEPR', 'EEPRO', 'EEPROM', 'EEPROM_']:
                    pass
                elif state in ['FLASH_V', 'FLASH512_V']:
                    terminal = True
                    break
                elif state in ['FLASH1M_V']:
                    terminal = True
                    break
                elif state in ['SRAM_V']:
                    terminal = True
                    break
                elif state in ['EEPROM_V']:
                    terminal = True
                    break
                else:
                    state = next_char

            if terminal:
                cart['saveType'] = state
                if state in ['FLASH_V', 'FLASH512_V']:
                    self.save = self.memory[self.REGION_CART_SRAM] = FlashSavedata(self.SIZE_CART_FLASH512)
                elif state in ['FLASH1M_V']:
                    self.save = self.memory[self.REGION_CART_SRAM] = FlashSavedata(self.SIZE_CART_FLASH1M)
                elif state in ['SRAM_V']:
                    self.save = self.memory[self.REGION_CART_SRAM] = SRAMSavedata(self.SIZE_CART_SRAM)
                elif state in ['EEPROM_V']:
                    self.save = self.memory[self.REGION_CART2 + 1] = EEPROMSavedata(self.SIZE_CART_EEPROM, self)
            if not self.save:
                self.save = self.memory[self.REGION_CART_SRAM] = SRAMSavedata(self.SIZE_CART_SRAM)

        self.cart = cart
        return cart

    def loadSavedata(self, save):
        self.save.replaceData(save)

    def load8(self, offset):
        return self.memory[offset >> self.BASE_OFFSET].load8(offset & self.OFFSET_MASK)

    def load16(self, offset):
        return self.memory[offset >> self.BASE_OFFSET].load16(offset & self.OFFSET_MASK)

    def load32(self, offset):
        return self.memory[offset >> self.BASE_OFFSET].load32(offset & self.OFFSET_MASK)

    def loadU8(self, offset):
        return self.memory[offset >> self.BASE_OFFSET].loadU8(offset & self.OFFSET_MASK)

    def loadU16(self, offset):
        return self.memory[offset >> self.BASE_OFFSET].loadU16(offset & self.OFFSET_MASK)

    def store8(self, offset, value):
        masked_offset = offset & self.OFFSET_MASK
        memory = self.memory[offset >> self.BASE_OFFSET]
        memory.store8(masked_offset, value)
        memory.invalidatePage(masked_offset)

    def store16(self, offset, value):
        masked_offset = offset & self.OFFSET_MASK
        memory = self.memory[offset >> self.BASE_OFFSET]
        memory.store16(masked_offset, value)
        memory.invalidatePage(masked_offset)

    def store32(self, offset, value):
        masked_offset = offset & self.OFFSET_MASK
        memory = self.memory[offset >> self.BASE_OFFSET]
        memory.store32(masked_offset, value)
        memory.invalidatePage(masked_offset)
        memory.invalidatePage(masked_offset + 2)

    def waitPrefetch(self, memory):
        self.cpu.cycles += 1 + self.waitstatesPrefetch[memory >> self.BASE_OFFSET]

    def waitPrefetch32(self, memory):
        self.cpu.cycles += 1 + self.waitstatesPrefetch32[memory >> self.BASE_OFFSET]

    def wait(self, memory):
        self.cpu.cycles += 1 + self.waitstates[memory >> self.BASE_OFFSET]

    def wait32(self, memory):
        self.cpu.cycles += 1 + self.waitstates32[memory >> self.BASE_OFFSET]

    def waitSeq(self, memory):
        self.cpu.cycles += 1 + self.waitstatesSeq[memory >> self.BASE_OFFSET]

    def waitSeq32(self, memory):
        self.cpu.cycles += 1 + self.waitstatesSeq32[memory >> self.BASE_OFFSET]

    def waitMul(self, rs):
        if rs & 0xffffff00 == 0xffffff00 or not (rs & 0xffffff00):
            self.cpu.cycles += 1
        elif rs & 0xffff0000 == 0xffff0000 or not (rs & 0xffff0000):
            self.cpu.cycles += 2
        elif rs & 0xff000000 == 0xff000000 or not (rs & 0xff000000):
            self.cpu.cycles += 3
        else:
            self.cpu.cycles += 4

    def waitMulti32(self, memory, seq):
        self.cpu.cycles += 1 + self.waitstates32[memory >> self.BASE_OFFSET]
        self.cpu.cycles += (1 + self.waitstatesSeq32[memory >> self.BASE_OFFSET]) * (seq - 1)

    def addressToPage(self, region, address):
        return address >> self.memory[region].ICACHE_PAGE_BITS

    def accessPage(self, region, page_id):
        memory = self.memory[region]
        page = memory.icache[page_id]
        if not page or page['invalid']:
            page = {
                'thumb': [None] * (1 << memory.ICACHE_PAGE_BITS),
                'arm': [None] * (1 << (memory.ICACHE_PAGE_BITS - 1)),
                'invalid': False,
            }
            memory.icache[page_id] = page
        return page

    def scheduleDma(self, number, info):
        if info.timing == self.DMA_TIMING_NOW:
            self.serviceDma(number, info)
        elif info.timing == self.DMA_TIMING_HBLANK:
            pass  # Handled implicitly
        elif info.timing == self.DMA_TIMING_VBLANK:
            pass  # Handled implicitly
        elif info.timing == self.DMA_TIMING_CUSTOM:
            if number == 0:
                self.core.WARN("Discarding invalid DMA0 scheduling")
            elif number == 1 or number == 2:
                self.cpu.irq.audio.scheduleFIFODma(number, info)
            elif number == 3:
                self.cpu.irq.video.scheduleVCaptureDma(dma, info)

    def runHblankDmas(self):
        for dma in self.cpu.irq.dma:
            if dma.enable and dma.timing == self.DMA_TIMING_HBLANK:
                self.serviceDma(i, dma)

    def runVblankDmas(self):
        for dma in self.cpu.irq.dma:
            if dma.enable and dma.timing == self.DMA_TIMING_VBLANK:
                self.serviceDma(i, dma)

    def serviceDma(self, number, info):
        if not info.enable:
            return

        width = info.width
        source_offset = self.DMA_OFFSET[info.srcControl] * width
        dest_offset = self.DMA_OFFSET[info.dstControl] * width
        words_remaining = info.nextCount
        source = info.nextSource & self.OFFSET_MASK
        dest = info.nextDest & self.OFFSET_MASK
        source_region = info.nextSource >> self.BASE_OFFSET
        dest_region = info.nextDest >> self.BASE_OFFSET
        source_block = self.memory[source_region]
        dest_block = self.memory[dest_region]
        source_view = None
        dest_view = None
        source_mask = 0xffffffff
        dest_mask = 0xffffffff

        if dest_block.ICACHE_PAGE_BITS:
            end_page = (dest + words_remaining * width) >> dest_block.ICACHE_PAGE_BITS
            for i in range(dest >> dest_block.ICACHE_PAGE_BITS, end_page + 1):
                dest_block.invalidatePage(i << dest_block.ICACHE_PAGE_BITS)

        if dest_region == self.REGION_WORKING_RAM or dest_region == self.REGION_WORKING_IRAM:
            dest_view = dest_block.view
            dest_mask = dest_block.mask

        if source_region == self.REGION_WORKING_RAM or source_region == self.REGION_WORKING_IRAM or source_region == self.REGION_CART0 or source_region == self.REGION_CART1:
            source_view = source_block.view
            source_mask = source_block.mask

        if source_block and dest_block:
            if source_view and dest_view:
                if width == 4:
                    source &= 0xfffffffc
                    dest &= 0xfffffffc
                    while words_remaining:
                        word = source_view.getInt32(source & source_mask)
                        dest_view.setInt32(dest & dest_mask, word)
                        source += source_offset
                        dest += dest_offset
                        words_remaining -= 1
                else:
                    while words_remaining:
                        word = source_view.getUint16(source & source_mask)
                        dest_view.setUint16(dest & dest_mask, word)
                        source += source_offset
                        dest += dest_offset
                        words_remaining -= 1
            elif source_view:
                if width == 4:
                    source &= 0xfffffffc
                    dest &= 0xfffffffc
                    while words_remaining:
                        word = source_view.getInt32(source & source_mask, True)
                        dest_block.store32(dest, word)
                        source += source_offset
                        dest += dest_offset
                        words_remaining -= 1
                else:
                    while words_remaining:
                        word = source_view.getUint16(source & source_mask, True)
                        dest_block.store16(dest, word)
                        source += source_offset
                        dest += dest_offset
                        words_remaining -= 1
            else:
                if width == 4:
                    source &= 0xfffffffc
                    dest &= 0xfffffffc
                    while words_remaining:
                        word = source_block.load32(source)
                        dest_block.store32(dest, word)
                        source += source_offset
                        dest += dest_offset
                        words_remaining -= 1
                else:
                    while words_remaining:
                        word = source_block.loadU16(source)
                        dest_block.store16(dest, word)
                        source += source_offset
                        dest += dest_offset
                        words_remaining -= 1
        else:
            self.core.WARN("Invalid DMA")

        if info.doIrq:
            info.nextIRQ = self.cpu.cycles + 2
            info.nextIRQ += (self.waitstates32[source_region] + self.waitstates32[dest_region]) if width == 4 else (self.waitstates[source_region] + self.waitstates[dest_region])
            info.nextIRQ += (info.count - 1) * ((self.waitstatesSeq32[source_region] + self.waitstatesSeq32[dest_region]) if width == 4 else (self.waitstatesSeq[source_region] + self.waitstatesSeq[dest_region]))

        info.nextSource = source | (source_region << self.BASE_OFFSET)
        info.nextDest = dest | (dest_region << self.BASE_OFFSET)
        info.nextCount = words_remaining

        if not info.repeat:
            info.enable = False

            # Clear the enable bit in memory
            io = self.memory[self.REGION_IO]
            io.registers[self.DMA_REGISTER[number]] &= 0x7fe0
        else:
            info.nextCount = info.count
            if info.dstControl == self.DMA_INCREMENT_RELOAD:
                info.nextDest = info.dest
            self.scheduleDma(number, info)

    def adjustTimings(self, word):
        sram = word & 0x0003
        ws0 = (word & 0x000c) >> 2
        ws0seq = (word & 0x0010) >> 4
        ws1 = (word & 0x0060) >> 5
        ws1seq = (word & 0x0080) >> 7
        ws2 = (word & 0x0300) >> 8
        ws2seq = (word & 0x0400) >> 10
        prefetch = bool(word & 0x4000)

        self.waitstates[self.REGION_CART_SRAM] = self.ROM_WS[sram]
        self.waitstatesSeq[self.REGION_CART_SRAM] = self.ROM_WS[sram]
        self.waitstates32[self.REGION_CART_SRAM] = self.ROM_WS[sram]
        self.waitstatesSeq32[self.REGION_CART_SRAM] = self.ROM_WS[sram]

        self.waitstates[self.REGION_CART0] = self.waitstates[self.REGION_CART0 + 1] = self.ROM_WS[ws0]
        self.waitstates[self.REGION_CART1] = self.waitstates[self.REGION_CART1 + 1] = self.ROM_WS[ws1]
        self.waitstates[self.REGION_CART2] = self.waitstates[self.REGION_CART2 + 1] = self.ROM_WS[ws2]

        self.waitstatesSeq[self.REGION_CART0] = self.waitstatesSeq[self.REGION_CART0 + 1] = self.ROM_WS_SEQ[0][ws0seq]
        self.waitstatesSeq[self.REGION_CART1] = self.waitstatesSeq[self.REGION_CART1 + 1] = self.ROM_WS_SEQ[1][ws1seq]
        self.waitstatesSeq[self.REGION_CART2] = self.waitstatesSeq[self.REGION_CART2 + 1] = self.ROM_WS_SEQ[2][ws2seq]

        self.waitstates32[self.REGION_CART0] = self.waitstates32[self.REGION_CART0 + 1] = self.waitstates[self.REGION_CART0] + 1 + self.waitstatesSeq[self.REGION_CART0]
        self.waitstates32[self.REGION_CART1] = self.waitstates32[self.REGION_CART1 + 1] = self.waitstates[self.REGION_CART1] + 1 + self.waitstatesSeq[self.REGION_CART1]
        self.waitstates32[self.REGION_CART2] = self.waitstates32[self.REGION_CART2 + 1] = self.waitstates[self.REGION_CART2] + 1 + self.waitstatesSeq[self.REGION_CART2]

        self.waitstatesSeq32[self.REGION_CART0] = self.waitstatesSeq32[self.REGION_CART0 + 1] = 2 * self.waitstatesSeq[self.REGION_CART0] + 1
        self.waitstatesSeq32[self.REGION_CART1] = self.waitstatesSeq32[self.REGION_CART1 + 1] = 2 * self.waitstatesSeq[self.REGION_CART1] + 1
        self.waitstatesSeq32[self.REGION_CART2] = self.waitstatesSeq32[self.REGION_CART2 + 1] = 2 * self.waitstatesSeq[self.REGION_CART2] + 1

        if prefetch:
            self.waitstatesPrefetch[self.REGION_CART0] = self.waitstatesPrefetch[self.REGION_CART0 + 1] = 0
            self.waitstatesPrefetch[self.REGION_CART1] = self.waitstatesPrefetch[self.REGION_CART1 + 1] = 0
            self.waitstatesPrefetch[self.REGION_CART2] = self.waitstatesPrefetch[self.REGION_CART2 + 1] = 0
            self.waitstatesPrefetch32[self.REGION_CART0] = self.waitstatesPrefetch32[self.REGION_CART0 + 1] = 0
            self.waitstatesPrefetch32[self.REGION_CART1] = self.waitstatesPrefetch32[self.REGION_CART1 + 1] = 0
            self.waitstatesPrefetch32[self.REGION_CART2] = self.waitstatesPrefetch32[self.REGION_CART2 + 1] = 0
        else:
            self.waitstatesPrefetch[self.REGION_CART0] = self.waitstatesPrefetch[self.REGION_CART0 + 1] = self.waitstatesSeq[self.REGION_CART0]
            self.waitstatesPrefetch[self.REGION_CART1] = self.waitstatesPrefetch[self.REGION_CART1 + 1] = self.waitstatesSeq[self.REGION_CART1]
            self.waitstatesPrefetch[self.REGION_CART2] = self.waitstatesPrefetch[self.REGION_CART2 + 1] = self.waitstatesSeq[self.REGION_CART2]
            self.waitstatesPrefetch32[self.REGION_CART0] = self.waitstatesPrefetch32[self.REGION_CART0 + 1] = self.waitstatesSeq32[self.REGION_CART0]
            self.waitstatesPrefetch32[self.REGION_CART1] = self.waitstatesPrefetch32[self.REGION_CART1 + 1] = self.waitstatesSeq32[self.REGION_CART1]
            self.waitstatesPrefetch32[self.REGION_CART2] = self.waitstatesPrefetch32[self.REGION_CART2 + 1] = self.waitstatesSeq32[self.REGION_CART2]

    def saveNeedsFlush(self):
        return self.save.writePending

    def flushSave(self):
        self.save.writePending = False

    def allocGPIO(self, rom):
        return GameBoyAdvanceGPIO(self.core, rom)