from software import GameBoyAdvanceSoftwareRenderer
class GameBoyAdvanceVideo:
    def __init__(self):
        try:
            self.renderPath = GameBoyAdvanceRenderProxy()
        except Exception as err:
            print("Service worker renderer couldn't load. Save states (not save files) may be glitchy")
            self.renderPath = GameBoyAdvanceSoftwareRenderer()
        self.nextEvent = None  # Add the nextEvent attribute
        self.CYCLES_PER_PIXEL = 4
        self.HORIZONTAL_PIXELS = 240
        self.HBLANK_PIXELS = 68
        self.HDRAW_LENGTH = 1006
        self.HBLANK_LENGTH = 226
        self.HORIZONTAL_LENGTH = 1232

        self.VERTICAL_PIXELS = 160
        self.VBLANK_PIXELS = 68
        self.VERTICAL_TOTAL_PIXELS = 228

        self.TOTAL_LENGTH = 280896

        self.drawCallback = lambda: None
        self.vblankCallback = lambda: None

    def clear(self):
        self.renderPath.clear(self.cpu.mmu)

        # DISPSTAT
        self.DISPSTAT_MASK = 0xff38
        self.inHblank = False
        self.inVblank = False
        self.vcounter = 0
        self.vblankIRQ = 0
        self.hblankIRQ = 0
        self.vcounterIRQ = 0
        self.vcountSetting = 0

        # VCOUNT
        self.vcount = -1

        self.lastHblank = 0
        self.nextHblank = self.HDRAW_LENGTH
        self.nextEvent = self.nextHblank

        self.nextHblankIRQ = 0
        self.nextVblankIRQ = 0
        self.nextVcounterIRQ = 0

    def freeze(self):
        return {
            "inHblank": self.inHblank,
            "inVblank": self.inVblank,
            "vcounter": self.vcounter,
            "vblankIRQ": self.vblankIRQ,
            "hblankIRQ": self.hblankIRQ,
            "vcounterIRQ": self.vcounterIRQ,
            "vcountSetting": self.vcountSetting,
            "vcount": self.vcount,
            "lastHblank": self.lastHblank,
            "nextHblank": self.nextHblank,
            "nextEvent": self.nextEvent,
            "nextHblankIRQ": self.nextHblankIRQ,
            "nextVblankIRQ": self.nextVblankIRQ,
            "nextVcounterIRQ": self.nextVcounterIRQ,
            "renderPath": self.renderPath.freeze(self.core.encodeBase64)
        }

    def defrost(self, frost):
        self.inHblank = frost["inHblank"]
        self.inVblank = frost["inVblank"]
        self.vcounter = frost["vcounter"]
        self.vblankIRQ = frost["vblankIRQ"]
        self.hblankIRQ = frost["hblankIRQ"]
        self.vcounterIRQ = frost["vcounterIRQ"]
        self.vcountSetting = frost["vcountSetting"]
        self.vcount = frost["vcount"]
        self.lastHblank = frost["lastHblank"]
        self.nextHblank = frost["nextHblank"]
        self.nextEvent = frost["nextEvent"]
        self.nextHblankIRQ = frost["nextHblankIRQ"]
        self.nextVblankIRQ = frost["nextVblankIRQ"]
        self.nextVcounterIRQ = frost["nextVcounterIRQ"]
        self.renderPath.defrost(frost["renderPath"], self.core.decodeBase64)

    def setBacking(self, backing):
        pixelData = backing.createImageData(self.HORIZONTAL_PIXELS, self.VERTICAL_PIXELS)
        self.context = backing

        # Clear backing first
        offset = 0
        while offset < self.HORIZONTAL_PIXELS * self.VERTICAL_PIXELS * 4:
            pixelData.data[offset] = 0xff
            pixelData.data[offset + 1] = 0xff
            pixelData.data[offset + 2] = 0xff
            pixelData.data[offset + 3] = 0xff
            offset += 4

        self.renderPath.setBacking(pixelData)

    def updateTimers(self, cpu):
        cycles = cpu.cycles

        if self.nextEvent <= cycles:
            if self.inHblank:
                # End Hblank
                self.inHblank = False
                self.nextEvent = self.nextHblank

                self.vcount += 1

                if self.vcount == self.VERTICAL_PIXELS:
                    self.inVblank = True
                    self.renderPath.finishDraw(self)
                    self.nextVblankIRQ = self.nextEvent + self.TOTAL_LENGTH
                    self.cpu.mmu.runVblankDmas()
                    if self.vblankIRQ:
                        self.cpu.irq.raiseIRQ(self.cpu.irq.IRQ_VBLANK)
                    self.vblankCallback()
                elif self.vcount == self.VERTICAL_TOTAL_PIXELS - 1:
                    self.inVblank = False
                elif self.vcount == self.VERTICAL_TOTAL_PIXELS:
                    self.vcount = 0
                    self.renderPath.startDraw()

                self.vcounter = self.vcount == self.vcountSetting
                if self.vcounter and self.vcounterIRQ:
                    self.cpu.irq.raiseIRQ(self.cpu.irq.IRQ_VCOUNTER)
                    self.nextVcounterIRQ += self.TOTAL_LENGTH

                if self.vcount < self.VERTICAL_PIXELS:
                    self.renderPath.drawScanline(self.vcount)
            else:
                # Begin Hblank
                self.inHblank = True
                self.lastHblank = self.nextHblank
                self.nextEvent = self.lastHblank + self.HBLANK_LENGTH
                self.nextHblank = self.nextEvent + self.HDRAW_LENGTH
                self.nextHblankIRQ = self.nextHblank

                if self.vcount < self.VERTICAL_PIXELS:
                    self.cpu.mmu.runHblankDmas()
                if self.hblankIRQ:
                    self.cpu.irq.raiseIRQ(self.cpu.irq.IRQ_HBLANK)

    def writeDisplayStat(self, value):
        self.vblankIRQ = value & 0x0008
        self.hblankIRQ = value & 0x0010
        self.vcounterIRQ = value & 0x0020
        self.vcountSetting = (value & 0xff00) >> 8

        if self.vcounterIRQ:
            # FIXME: this can be too late if we're in the middle of an Hblank
            self.nextVcounterIRQ = self.nextHblank + self.HBLANK_LENGTH + (self.vcountSetting - self.vcount) * self.HORIZONTAL_LENGTH
            if self.nextVcounterIRQ < self.nextEvent:
                self.nextVcounterIRQ += self.TOTAL_LENGTH

    def readDisplayStat(self):
        return self.inVblank | (self.inHblank << 1) | (self.vcounter << 2)

    def finishDraw(self, pixelData):
        self.context.putImageData(pixelData, 0, 0)
        self.drawCallback()