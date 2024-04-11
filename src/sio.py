class GameBoyAdvanceSIO:
    def __init__(self):
        self.SIO_NORMAL_8 = 0
        self.SIO_NORMAL_32 = 1
        self.SIO_MULTI = 2
        self.SIO_UART = 3
        self.SIO_GPIO = 8
        self.SIO_JOYBUS = 12

        self.BAUD = [9600, 38400, 57600, 115200]
        self.clear()

    def clear(self):
        self.mode = self.SIO_GPIO
        self.sd = False

        self.irq = False
        self.multiplayer = {
            'baud': 0,
            'si': 0,
            'id': 0,
            'error': 0,
            'busy': 0,
            'states': [0xffff, 0xffff, 0xffff, 0xffff]
        }

        self.linkLayer = None

    def setMode(self, mode):
        if mode & 0x8:
            mode &= 0xc
        else:
            mode &= 0x3
        self.mode = mode

        print("Setting SIO mode to " + hex(mode))

    def writeRCNT(self, value):
        if self.mode != self.SIO_GPIO:
            return

        print("General purpose serial not supported")

    def writeSIOCNT(self, value):
        if self.mode == self.SIO_NORMAL_8:
            print("8-bit transfer unsupported")
        elif self.mode == self.SIO_NORMAL_32:
            print("32-bit transfer unsupported")
        elif self.mode == self.SIO_MULTI:
            self.multiplayer['baud'] = value & 0x0003
            if self.linkLayer:
                self.linkLayer.setBaud(self.BAUD[self.multiplayer['baud']])

            if not self.multiplayer['si']:
                self.multiplayer['busy'] = value & 0x0080
                if self.linkLayer and self.multiplayer['busy']:
                    self.linkLayer.startMultiplayerTransfer()
            self.irq = value & 0x4000
        elif self.mode == self.SIO_UART:
            print("UART unsupported")
        elif self.mode == self.SIO_GPIO:
            pass
        elif self.mode == self.SIO_JOYBUS:
            print("JOY BUS unsupported")

    def readSIOCNT(self):
        value = (self.mode << 12) & 0xffff
        if self.mode == self.SIO_NORMAL_8:
            print("8-bit transfer unsupported")
        elif self.mode == self.SIO_NORMAL_32:
            print("32-bit transfer unsupported")
        elif self.mode == self.SIO_MULTI:
            value |= self.multiplayer['baud']
            value |= self.multiplayer['si']
            value |= int(self.sd) << 3
            value |= self.multiplayer['id'] << 4
            value |= self.multiplayer['error']
            value |= self.multiplayer['busy']
            value |= int(self.multiplayer['irq']) << 14
        elif self.mode == self.SIO_UART:
            print("UART unsupported")
        elif self.mode == self.SIO_GPIO:
            pass
        elif self.mode == self.SIO_JOYBUS:
            print("JOY BUS unsupported")
        return value

    def read(self, slot):
        if self.mode == self.SIO_NORMAL_32:
            print("32-bit transfer unsupported")
        elif self.mode == self.SIO_MULTI:
            return self.multiplayer['states'][slot]
        elif self.mode == self.SIO_UART:
            print("UART unsupported")
        else:
            print("Reading from transfer register in unsupported mode")
        return 0