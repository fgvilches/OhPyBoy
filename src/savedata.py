class SRAMSavedata:

    def __init__(self, size):
        super().__init__(bytearray(size), 0)
        self.writePending = False

    def store8(self, offset, value):
        self.view[offset] = value
        self.writePending = True

    def store16(self, offset, value):
        self.view[offset] = value & 0xFF
        self.view[offset + 1] = (value >> 8) & 0xFF
        self.writePending = True

    def store32(self, offset, value):
        self.view[offset] = value & 0xFF
        self.view[offset + 1] = (value >> 8) & 0xFF
        self.view[offset + 2] = (value >> 16) & 0xFF
        self.view[offset + 3] = (value >> 24) & 0xFF
        self.writePending = True


class FlashSavedata:

    def __init__(self, size):
        self.size = size
        self.data = bytearray(size)
        self.COMMAND_WIPE = 0x10
        self.COMMAND_ERASE_SECTOR = 0x30
        self.COMMAND_ERASE = 0x80
        self.COMMAND_ID = 0x90
        self.COMMAND_WRITE = 0xa0
        self.COMMAND_SWITCH_BANK = 0xb0
        self.COMMAND_TERMINATE_ID = 0xf0

        self.ID_PANASONIC = 0x1b32
        self.ID_SANYO = 0x1362

        self.bank0 = self.view
        if size > 0x00010000:
            self.id = self.ID_SANYO
            self.bank1 = self.view[0x00010000:]
        else:
            self.id = self.ID_PANASONIC
            self.bank1 = None
        self.bank = self.bank0

        self.idMode = False
        self.writePending = False

        self.first = 0
        self.second = 0
        self.command = 0
        self.pendingCommand = 0

    def load8(self, offset):
        if self.idMode and offset < 2:
            return (self.id >> (offset << 3)) & 0xff
        elif offset < 0x10000:
            return self.bank[offset]
        else:
            return 0

    def load16(self, offset):
        return (self.load8(offset) & 0xff) | (self.load8(offset + 1) << 8)

    def load32(self, offset):
        return (
            (self.load8(offset) & 0xff) |
            (self.load8(offset + 1) << 8) |
            (self.load8(offset + 2) << 16) |
            (self.load8(offset + 3) << 24)
        )

    def loadU8(self, offset):
        return self.load8(offset) & 0xff

    def loadU16(self, offset):
        return (self.loadU8(offset) & 0xff) | (self.loadU8(offset + 1) << 8)

    def store8(self, offset, value):
        if self.command == 0:
            if offset == 0x5555:
                if self.second == 0x55:
                    if value == self.COMMAND_ERASE:
                        self.pendingCommand = value
                    elif value == self.COMMAND_ID:
                        self.idMode = True
                    elif value == self.COMMAND_TERMINATE_ID:
                        self.idMode = False
                    else:
                        self.command = value
                    self.second = 0
                    self.first = 0
                else:
                    self.command = 0
                    self.first = value
                    self.idMode = False
            elif offset == 0x2aaa and self.first == 0xaa:
                self.first = 0
                if self.pendingCommand:
                    self.command = self.pendingCommand
                else:
                    self.second = value
        elif self.command == self.COMMAND_ERASE:
            if value == self.COMMAND_WIPE:
                if offset == 0x5555:
                    for i in range(0, len(self.view), 4):
                        self.view[i:i+4] = bytearray([0xFF, 0xFF, 0xFF, 0xFF])
            elif value == self.COMMAND_ERASE_SECTOR:
                if (offset & 0x0fff) == 0:
                    for i in range(offset, offset + 0x1000, 4):
                        self.bank[i:i+4] = bytearray([0xFF, 0xFF, 0xFF, 0xFF])
            self.pendingCommand = 0
            self.command = 0
        elif self.command == self.COMMAND_WRITE:
            self.bank[offset] = value
            self.command = 0
            self.writePending = True
        elif self.command == self.COMMAND_SWITCH_BANK:
            if self.bank1 and offset == 0:
                if value == 1:
                    self.bank = self.bank1
                else:
                    self.bank = self.bank0
            self.command = 0

    def store16(self, offset, value):
        raise Exception('Unaligned save to flash!')

    def store32(self, offset, value):
        raise Exception('Unaligned save to flash!')

    def replaceData(self, memory):
        bank = self.view is self.bank1
        self.view = memory
        self.bank0 = self.view
        if len(memory) > 0x00010000:
            self.bank1 = self.view[0x00010000:]
        else:
            self.bank1 = None
        self.bank = self.bank1 if bank else self.bank0
        
    def __getitem__(self, item):
        return self.data[item]

    @property
    def view(self):
        return self
class EEPROMSavedata:
    def __init__(self, size, mmu):
        super().__init__(bytearray(size), 0)

        self.writeAddress = 0
        self.readBitsRemaining = 0
        self.readAddress = 0

        self.command = 0
        self.commandBitsRemaining = 0

        self.realSize = 0
        self.addressBits = 0
        self.writePending = False

        self.dma = mmu.core.irq.dma[3]

        self.COMMAND_NULL = 0
        self.COMMAND_PENDING = 1
        self.COMMAND_WRITE = 2
        self.COMMAND_READ_PENDING = 3
        self.COMMAND_READ = 4

    def load8(self, offset):
        raise Exception('Unsupported 8-bit access!')

    def load16(self, offset):
        return self.loadU16(offset)

    def loadU8(self, offset):
        raise Exception('Unsupported 8-bit access!')

    def loadU16(self, offset):
        if self.command != self.COMMAND_READ or not self.dma.enable:
            return 1
        self.readBitsRemaining -= 1
        if self.readBitsRemaining < 64:
            step = 63 - self.readBitsRemaining
            data = self.view[(self.readAddress + step) >> 3] >> (0x7 - (step & 0x7))
            if not self.readBitsRemaining:
                self.command = self.COMMAND_NULL
            return data & 0x1
        return 0

    def load32(self, offset):
        raise Exception('Unsupported 32-bit access!')

    def store8(self, offset, value):
        raise Exception('Unsupported 8-bit access!')

    def store16(self, offset, value):
        if self.command == self.COMMAND_NULL:
            self.command = value & 0x1
        elif self.command == self.COMMAND_PENDING:
            self.command <<= 1
            self.command |= value & 0x1
            if self.command == self.COMMAND_WRITE:
                if not self.realSize:
                    bits = self.dma.count - 67
                    self.realSize = 8 << bits
                    self.addressBits = bits
                self.commandBitsRemaining = self.addressBits + 64 + 1
                self.writeAddress = 0
            else:
                if not self.realSize:
                    bits = self.dma.count - 3
                    self.realSize = 8 << bits
                    self.addressBits = bits
                self.commandBitsRemaining = self.addressBits + 1
                self.readAddress = 0
        elif self.command == self.COMMAND_WRITE:
            if self.commandBitsRemaining > 64:
                self.writeAddress <<= 1
                self.writeAddress |= (value & 0x1) << 6
            elif self.commandBitsRemaining <= 0:
                self.command = self.COMMAND_NULL
                self.writePending = True
            else:
                current = self.view[self.writeAddress >> 3]
                current &= ~(1 << (0x7 - (self.writeAddress & 0x7)))
                current |= (value & 0x1) << (0x7 - (self.writeAddress & 0x7))
                self.view[self.writeAddress >> 3] = current
                self.writeAddress += 1
            self.commandBitsRemaining -= 1
        elif self.command == self.COMMAND_READ_PENDING:
            if self.commandBitsRemaining > 0:
                self.readAddress <<= 1
                if value & 0x1:
                    self.readAddress |= 0x40
            else:
                self.readBitsRemaining = 68
                self.command = self.COMMAND_READ

    def store32(self, offset, value):
        raise Exception('Unsupported 32-bit access!')

    def replaceData(self, memory):
        self.view = memory