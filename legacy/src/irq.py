from dma import GameBoyAdvanceDMA
class GameBoyAdvanceInterruptHandler:
    def __init__(self):
        self.FREQUENCY = 0x1000000

        self.cpu = None
        self.enable = False
        self.timersEnabled = False
        self.dmaog = GameBoyAdvanceDMA()
        self.dma_dat = self.dmaog.data
        self.IRQ_VBLANK = '0x0'
        self.IRQ_HBLANK = '0x1'
        self.IRQ_VCOUNTER = '0x2'
        self.IRQ_TIMER0 = '0x3'
        self.IRQ_TIMER1 = '0x4'
        self.IRQ_TIMER2 = '0x5'
        self.IRQ_TIMER3 = '0x6'
        self.IRQ_SIO = '0x7'
        self.IRQ_DMA0 = '0x8'
        self.IRQ_DMA1 = '0x9'
        self.IRQ_DMA2 = '0xa'
        self.IRQ_DMA3 = '0xb'
        self.IRQ_KEYPAD = '0xc'
        self.IRQ_GAMEPAK = '0xd'

        self.MASK_VBLANK = '0x0001'
        self.MASK_HBLANK = '0x0002'
        self.MASK_VCOUNTER = '0x0004'
        self.MASK_TIMER0 = '0x0008'
        self.MASK_TIMER1 = '0x0010'
        self.MASK_TIMER2 = '0x0020'
        self.MASK_TIMER3 = '0x0040'
        self.MASK_SIO = '0x0080'
        self.MASK_DMA0 = '0x0100'
        self.MASK_DMA1 = '0x0200'
        self.MASK_DMA2 = '0x0400'
        self.MASK_DMA3 = '0x0800'
        self.MASK_KEYPAD = '0x1000'
        self.MASK_GAMEPAK = '0x2000'

    def clear(self):
        self.enable = False
        self.enabledIRQs = 0
        self.interruptFlags = 0

        self.dma = []
        for i in range(4):
            self.dma.append({
                'source': 0,
                'dest': 0,
                'count': 0,
                'nextSource': 0,
                'nextDest': 0,
                'nextCount': 0,
                'srcControl': 0,
                'dstControl': 0,
                'repeat': False,
                'width': 0,
                'drq': False,
                'timing': 0,
                'doIrq': False,
                'enable': False,
                'nextIRQ': 0
            })

        self.timersEnabled = 0
        self.timers = []
        for i in range(4):
            self.timers.append({
                'reload': 0,
                'oldReload': 0,
                'prescaleBits': 0,
                'countUp': False,
                'doIrq': False,
                'enable': False,
                'lastEvent': 0,
                'nextEvent': 0,
                'overflowInterval': 1
            })

        self.nextEvent = 0
        self.springIRQ = False
        self.resetSP()

    def freeze(self):
        return {
            'enable': self.enable,
            'enabledIRQs': self.enabledIRQs,
            'interruptFlags': self.interruptFlags,
            'dma': self.dma,
            'timers': self.timers,
            'nextEvent': self.nextEvent,
            'springIRQ': self.springIRQ
        }

    def defrost(self, frost):
        self.enable = frost['enable']
        self.enabledIRQs = frost['enabledIRQs']
        self.interruptFlags = frost['interruptFlags']
        self.dma = frost['dma']
        self.timers = frost['timers']
        self.timersEnabled = 0
        if self.timers[0]['enable']:
            self.timersEnabled += 1
        if self.timers[1]['enable']:
            self.timersEnabled += 1
        if self.timers[2]['enable']:
            self.timersEnabled += 1
        if self.timers[3]['enable']:
            self.timersEnabled += 1
        self.nextEvent = frost['nextEvent']
        self.springIRQ = frost['springIRQ']

    def updateTimers(self):
        if self.nextEvent > self.cpu.cycles:
            return

        if self.springIRQ:
            self.cpu.raiseIRQ()
            self.springIRQ = False

        self.video.updateTimers(self.cpu)
        self.audio.updateTimers()
        if self.timersEnabled:
            timer = self.timers[0]
            if timer['enable']:
                if self.cpu.cycles >= timer['nextEvent']:
                    timer['lastEvent'] = timer['nextEvent']
                    timer['nextEvent'] += timer['overflowInterval']
                    self.io.registers[self.io.TM0CNT_LO >> 1] = timer['reload']
                    timer['oldReload'] = timer['reload']

                    if timer['doIrq']:
                        self.raiseIRQ(self.IRQ_TIMER0)

                    if self.audio.enabled:
                        if (
                            self.audio.enableChannelA and
                            not self.audio.soundTimerA and
                            self.audio.dmaA >= 0
                        ):
                            self.audio.sampleFifoA()

                        if (
                            self.audio.enableChannelB and
                            not self.audio.soundTimerB and
                            self.audio.dmaB >= 0
                        ):
                            self.audio.sampleFifoB()

                    timer = self.timers[1]
                    if timer['countUp']:
                        if (
                            self.io.registers[self.io.TM1CNT_LO >> 1] ==
                            0x10000
                        ):
                            timer['nextEvent'] = self.cpu.cycles
            timer = self.timers[1]
            if timer['enable']:
                if self.cpu.cycles >= timer['nextEvent']:
                    timer['lastEvent'] = timer['nextEvent']
                    timer['nextEvent'] += timer['overflowInterval']
                    if (
                        not timer['countUp'] or
                        self.io.registers[self.io.TM1CNT_LO >> 1] == 0x10000
                    ):
                        self.io.registers[self.io.TM1CNT_LO >> 1] = timer['reload']
                    timer['oldReload'] = timer['reload']

                    if timer['doIrq']:
                        self.raiseIRQ(self.IRQ_TIMER1)

                    if timer['countUp']:
                        timer['nextEvent'] = 0

                    if self.audio.enabled:
                        if (
                            self.audio.enableChannelA and
                            self.audio.soundTimerA and
                            self.audio.dmaA >= 0
                        ):
                            self.audio.sampleFifoA()

                        if (
                            self.audio.enableChannelB and
                            self.audio.soundTimerB and
                            self.audio.dmaB >= 0
                        ):
                            self.audio.sampleFifoB()

                    timer = self.timers[2]
                    if timer['countUp']:
                        if (
                            self.io.registers[self.io.TM2CNT_LO >> 1] ==
                            0x10000
                        ):
                            timer['nextEvent'] = self.cpu.cycles
            timer = self.timers[2]
            if timer['enable']:
                if self.cpu.cycles >= timer['nextEvent']:
                    timer['lastEvent'] = timer['nextEvent']
                    timer['nextEvent'] += timer['overflowInterval']
                    if (
                        not timer['countUp'] or
                        self.io.registers[self.io.TM2CNT_LO >> 1] == 0x10000
                    ):
                        self.io.registers[self.io.TM2CNT_LO >> 1] = timer['reload']
                    timer['oldReload'] = timer['reload']

                    if timer['doIrq']:
                        self.raiseIRQ(self.IRQ_TIMER2)

                    if timer['countUp']:
                        timer['nextEvent'] = 0

                    timer = self.timers[3]
                    if timer['countUp']:
                        if (
                            self.io.registers[self.io.TM3CNT_LO >> 1] ==
                            0x10000
                        ):
                            timer['nextEvent'] = self.cpu.cycles
            timer = self.timers[3]
            if timer['enable']:
                if self.cpu.cycles >= timer['nextEvent']:
                    timer['lastEvent'] = timer['nextEvent']
                    timer['nextEvent'] += timer['overflowInterval']
                    if (
                        not timer['countUp'] or
                        self.io.registers[self.io.TM3CNT_LO >> 1] == 0x10000
                    ):
                        self.io.registers[self.io.TM3CNT_LO >> 1] = timer['reload']
                    timer['oldReload'] = timer['reload']

                    if timer['doIrq']:
                        self.raiseIRQ(self.IRQ_TIMER3)

                    if timer['countUp']:
                        timer['nextEvent'] = 0

        dma = self.dma[0]
        if (
            dma['enable'] and
            dma['doIrq'] and
            dma['nextIRQ'] and
            self.cpu.cycles >= dma['nextIRQ']
        ):
            dma['nextIRQ'] = 0
            self.raiseIRQ(self.IRQ_DMA0)

        dma = self.dma[1]
        if (
            dma['enable'] and
            dma['doIrq'] and
            dma['nextIRQ'] and
            self.cpu.cycles >= dma['nextIRQ']
        ):
            dma['nextIRQ'] = 0
            self.raiseIRQ(self.IRQ_DMA1)

        dma = self.dma[2]
        if (
            dma['enable'] and
            dma['doIrq'] and
            dma['nextIRQ'] and
            self.cpu.cycles >= dma['nextIRQ']
        ):
            dma['nextIRQ'] = 0
            self.raiseIRQ(self.IRQ_DMA2)

        dma = self.dma[3]
        if (
            dma['enable'] and
            dma['doIrq'] and
            dma['nextIRQ'] and
            self.cpu.cycles >= dma['nextIRQ']
        ):
            dma['nextIRQ'] = 0
            self.raiseIRQ(self.IRQ_DMA3)

        self.pollNextEvent()

    def resetSP(self):
        self.cpu.switchMode(self.cpu.MODE_SUPERVISOR)
        self.cpu.gprs[self.cpu.SP] = 0x3007fe0
        self.cpu.switchMode(self.cpu.MODE_IRQ)
        self.cpu.gprs[self.cpu.SP] = 0x3007fa0
        self.cpu.switchMode(self.cpu.MODE_SYSTEM)
        self.cpu.gprs[self.cpu.SP] = 0x3007f00

    def swi32(self, opcode):
        self.swi(opcode >> 16)

    def swi(self, opcode):
        if self.core.mmu.bios.real:
            self.cpu.raiseTrap()
            return

        if opcode == 0x00:
            # SoftReset
            mem = self.core.mmu.memory[self.core.mmu.REGION_WORKING_IRAM]
            flag = mem.loadU8(0x7ffa)
            for i in range(0x7e00, 0x8000, 4):
                mem.store32(i, 0)
            self.resetSP()
            if not flag:
                self.cpu.gprs[self.cpu.LR] = 0x08000000
            else:
                self.cpu.gprs[self.cpu.LR] = 0x02000000
            self.cpu.switchExecMode(self.cpu.MODE_ARM)
            self.cpu.instruction.writesPC = True
            self.cpu.gprs[self.cpu.PC] = self.cpu.gprs[self.cpu.LR]
        elif opcode == 0x01:
            # RegisterRamReset
            regions = self.cpu.gprs[0]
            if regions & 0x01:
                self.core.mmu.memory[self.core.mmu.REGION_WORKING_RAM] = MemoryBlock(self.core.mmu.SIZE_WORKING_RAM, 9)
            if regions & 0x02:
                for i in range(0, self.core.mmu.SIZE_WORKING_IRAM - 0x200, 4):
                    self.core.mmu.memory[self.core.mmu.REGION_WORKING_IRAM].store32(i, 0)
            if regions & 0x1c:
                self.video.renderPath.clearSubsets(self.core.mmu, regions)
            if regions & 0xe0:
                self.core.STUB("Unimplemented RegisterRamReset")
        elif opcode == 0x02:
            # Halt
            self.halt()
        elif opcode == 0x05:
            # VBlankIntrWait
            self.cpu.gprs[0] = 1
            self.cpu.gprs[1] = 1
        elif opcode == 0x04:
            # IntrWait
            if not self.enable:
                self.io.store16(self.io.IME, 1)
            if not self.cpu.gprs[0] and self.interruptFlags & self.cpu.gprs[1]:
                return
            self.dismissIRQs(0xffffffff)
            self.cpu.raiseTrap()
        elif opcode == 0x06:
            # Div
            result = (self.cpu.gprs[0] | 0) / (self.cpu.gprs[1] | 0)
            mod = (self.cpu.gprs[0] | 0) % (self.cpu.gprs[1] | 0)
            self.cpu.gprs[0] = result | 0
            self.cpu.gprs[1] = mod | 0
            self.cpu.gprs[3] = abs(result | 0)
        elif opcode == 0x07:
            # DivArm
            result = (self.cpu.gprs[1] | 0) / (self.cpu.gprs[0] | 0)
            mod = (self.cpu.gprs[1] | 0) % (self.cpu.gprs[0] | 0)
            self.cpu.gprs[0] = result | 0
            self.cpu.gprs[1] = mod | 0
            self.cpu.gprs[3] = abs(result | 0)
        elif opcode == 0x08:
            # Sqrt
            root = int(self.cpu.gprs[0] ** 0.5)
            self.cpu.gprs[0] = root
        elif opcode == 0x0a:
            # ArcTan2
            x = self.cpu.gprs[0] / 16384
            y = self.cpu.gprs[1] / 16384
            self.cpu.gprs[0] = int((math.atan2(y, x) / (2 * math.pi)) * 0x10000)
        elif opcode == 0x0b:
            # CpuSet
            source = self.cpu.gprs[0]
            dest = self.cpu.gprs[1]
            mode = self.cpu.gprs[2]
            count = mode & 0x000fffff
            fill = mode & 0x01000000
            wordsize = 4 if mode & 0x04000000 else 2
            if fill:
                if wordsize == 4:
                    source &= 0xfffffffc
                    dest &= 0xfffffffc
                    word = self.cpu.mmu.load32(source)
                    for i in range(count):
                        self.cpu.mmu.store32(dest + (i << 2), word)
                else:
                    source &= 0xfffffffe
                    dest &= 0xfffffffe
                    word = self.cpu.mmu.load16(source)
                    for i in range(count):
                        self.cpu.mmu.store16(dest + (i << 1), word)
            else:
                if wordsize == 4:
                    source &= 0xfffffffc
                    dest &= 0xfffffffc
                    for i in range(count):
                        word = self.cpu.mmu.load32(source + (i << 2))
                        self.cpu.mmu.store32(dest + (i << 2), word)
                else:
                    source &= 0xfffffffe
                    dest &= 0xfffffffe
                    for i in range(count):
                        word = self.cpu.mmu.load16(source + (i << 1))
                        self.cpu.mmu.store16(dest + (i << 1), word)
        elif opcode == 0x0c:
            # FastCpuSet
            source = self.cpu.gprs[0] & 0xfffffffc
            dest = self.cpu.gprs[1] & 0xfffffffc
            mode = self.cpu.gprs[2]
            count = mode & 0x000fffff
            count = ((count + 7) >> 3) << 3
            fill = mode & 0x01000000
            if fill:
                word = self.cpu.mmu.load32(source)
                for i in range(count):
                    self.cpu.mmu.store32(dest + (i << 2), word)
            else:
                for i in range(count):
                    word = self.cpu.mmu.load32(source + (i << 2))
                    self.cpu.mmu.store32(dest + (i << 2), word)
        elif opcode == 0x0e:
            # BgAffineSet
            i = self.cpu.gprs[2]
            ox, oy = 0, 0
            cx, cy = 0, 0
            sx, sy = 0, 0
            theta = 0
            offset = self.cpu.gprs[0]
            destination = self.cpu.gprs[1]
            a, b, c, d = 0, 0, 0, 0
            rx, ry = 0, 0
            while i > 0:
                ox = self.core.mmu.load32(offset) / 256
                oy = self.core.mmu.load32(offset + 4) / 256
                cx = self.core.mmu.load16(offset + 8)
                cy = self.core.mmu.load16(offset + 10)
                sx = self.core.mmu.load16(offset + 12) / 256
                sy = self.core.mmu.load16(offset + 14) / 256
                theta = ((self.core.mmu.loadU16(offset + 16) >> 8) / 128) * math.pi
                offset += 20
                a = d = math.cos(theta)
                b = c = math.sin(theta)
                a *= sx
                b *= -sx
                c *= sy
                d *= sy
                rx = ox - (a * cx + b * cy)
                ry = oy - (c * cx + d * cy)
                self.core.mmu.store16(destination, int(a * 256))
                self.core.mmu.store16(destination + 2, int(b * 256))
                self.core.mmu.store16(destination + 4, int(c * 256))
                self.core.mmu.store16(destination + 6, int(d * 256))
                self.core.mmu.store32(destination + 8, int(rx * 256))
                self.core.mmu.store32(destination + 12, int(ry * 256))
                destination += 16
                i -= 1
        elif opcode == 0x0f:
            # ObjAffineSet
            i = self.cpu.gprs[2]
            sx, sy = 0, 0
            theta = 0
            offset = self.cpu.gprs[0]
            destination = self.cpu.gprs[1]
            diff = self.cpu.gprs[3]
            a, b, c, d = 0, 0, 0, 0
            while i > 0:
                sx = self.core.mmu.load16(offset) / 256
                sy = self.core.mmu.load16(offset + 2) / 256
                theta = ((self.core.mmu.loadU16(offset + 4) >> 8) / 128) * math.pi
                offset += 6
                a = d = math.cos(theta)
                b = c = math.sin(theta)
                a *= sx
                b *= -sx
                c *= sy
                d *= sy
                self.core.mmu.store16(destination, int(a * 256))
                self.core.mmu.store16(destination + diff, int(b * 256))
                self.core.mmu.store16(destination + diff * 2, int(c * 256))
                self.core.mmu.store16(destination + diff * 3, int(d * 256))
                destination += diff * 4
                i -= 1
        elif opcode == 0x11:
            # LZ77UnCompWram
            self.lz77(self.cpu.gprs[0], self.cpu.gprs[1], 1)
        elif opcode == 0x12:
            # LZ77UnCompVram
            self.lz77(self.cpu.gprs[0], self.cpu.gprs[1], 2)
        elif opcode == 0x13:
            # HuffUnComp
            self.huffman(self.cpu.gprs[0], self.cpu.gprs[1])
        elif opcode == 0x14:
            # RlUnCompWram
            self.rl(self.cpu.gprs[0], self.cpu.gprs[1], 1)
        elif opcode == 0x15:
            # RlUnCompVram
            self.rl(self.cpu.gprs[0], self.cpu.gprs[1], 2)
        elif opcode == 0x1f:
            # MidiKey2Freq
            key = self.cpu.mmu.load32(self.cpu.gprs[0] + 4)
            self.cpu.gprs[0] = int(key / (2 ** ((180 - self.cpu.gprs[1] - self.cpu.gprs[2] / 256) / 12)))
        else:
            raise Exception("Unimplemented software interrupt: 0x" + hex(opcode)[2:])

    def masterEnable(self, value):
        self.enable = value

        if self.enable and self.enabledIRQs & self.interruptFlags:
            self.cpu.raiseIRQ()

    def setInterruptsEnabled(self, value):
        self.enabledIRQs = value

        if self.enabledIRQs & self.MASK_SIO:
            self.core.STUB("Serial I/O interrupts not implemented")

        if self.enabledIRQs & self.MASK_KEYPAD:
            self.core.STUB("Keypad interrupts not implemented")

        if self.enable and self.enabledIRQs & self.interruptFlags:
            self.cpu.raiseIRQ()

    def pollNextEvent(self):
        nextEvent = self.video.nextEvent
        test = 0

        if self.audio.enabled:
            test = self.audio.nextEvent
            if not nextEvent or test < nextEvent:
                nextEvent = test

        if self.timersEnabled:
            timer = self.timers[0]
            test = timer.nextEvent
            if timer.enable and test and (not nextEvent or test < nextEvent):
                nextEvent = test

            timer = self.timers[1]
            test = timer.nextEvent
            if timer.enable and test and (not nextEvent or test < nextEvent):
                nextEvent = test

            timer = self.timers[2]
            test = timer.nextEvent
            if timer.enable and test and (not nextEvent or test < nextEvent):
                nextEvent = test

            timer = self.timers[3]
            test = timer.nextEvent
            if timer.enable and test and (not nextEvent or test < nextEvent):
                nextEvent = test
        dma = self.dma_dat.head
        if self.dmaog.enable and self.dmaog.doIrq and dma.next != None:
            nextEvent = dma.next

        dma = dma.next
        if self.dmaog.enable and self.dmaog.doIrq and dma.next != None:
            nextEvent = dma.next

        dma = dma.next
        print(dma)
        if self.dmaog.enable and self.dmaog.doIrq and dma.next != None:
            nextEvent = dma.next

        dma = dma.next
        if self.dmaog.enable and self.dmaog.doIrq and dma.next != None:
            nextEvent = dma.next

        self.core.ASSERT(int(nextEvent.data, 0) >= self.cpu.cycles, "Next event is before present")
        self.nextEvent = nextEvent

    def waitForIRQ(self):
        timer = None
        irqPending = (
            self.testIRQ() or
            self.video.hblankIRQ or
            self.video.vblankIRQ or
            self.video.vcounterIRQ
        )
        if self.timersEnabled:
            timer = self.timers[0]
            irqPending = irqPending or timer.doIrq
            timer = self.timers[1]
            irqPending = irqPending or timer.doIrq
            timer = self.timers[2]
            irqPending = irqPending or timer.doIrq
            timer = self.timers[3]
            irqPending = irqPending or timer.doIrq
        if not irqPending:
            return False

        while True:
            self.pollNextEvent()

            if not self.nextEvent:
                return False
            else:
                self.cpu.cycles = self.nextEvent
                self.updateTimers()
                if self.interruptFlags:
                    return True

    def testIRQ(self):
        if self.enable and self.enabledIRQs & self.interruptFlags:
            self.springIRQ = True
            self.nextEvent = self.cpu.cycles
            return True
        return False

    def raiseIRQ(self, irqType):
        self.interruptFlags |= 1 << irqType
        self.io.registers[self.io.IF >> 1] = self.interruptFlags

        if self.enable and self.enabledIRQs & (1 << irqType):
            self.cpu.raiseIRQ()

    def dismissIRQs(self, irqMask):
        self.interruptFlags &= ~irqMask
        self.io.registers[self.io.IF >> 1] = self.interruptFlags

    def dmaSetSourceAddress(self, dma, address):
        self.dma[dma]['source'] = address & 0xfffffffe

    def dmaSetDestAddress(self, dma, address):
        self.dma[dma]['dest'] = address & 0xfffffffe

    def dmaSetWordCount(self, dma, count):
        self.dma[dma]['count'] = count if count else 0x10000 if dma == 3 else 0x4000

    def dmaWriteControl(self, dma, control):
        currentDma = self.dma[dma]
        wasEnabled = currentDma['enable']
        currentDma['dstControl'] = (control & 0x0060) >> 5
        currentDma['srcControl'] = (control & 0x0180) >> 7
        currentDma['repeat'] = bool(control & 0x0200)
        currentDma['width'] = 4 if control & 0x0400 else 2
        currentDma['drq'] = bool(control & 0x0800)
        currentDma['timing'] = (control & 0x3000) >> 12
        currentDma['doIrq'] = bool(control & 0x4000)
        currentDma['enable'] = bool(control & 0x8000)
        currentDma['nextIRQ'] = 0

        if currentDma['drq']:
            self.core.WARN("DRQ not implemented")

        if not wasEnabled and currentDma['enable']:
            currentDma['nextSource'] = currentDma['source']
            currentDma['nextDest'] = currentDma['dest']
            currentDma['nextCount'] = currentDma['count']
            self.cpu.mmu.scheduleDma(dma, currentDma)