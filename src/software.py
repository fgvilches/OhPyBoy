class MemoryAligned16:
    def __init__(self, size):
        self.buffer = bytearray(size >> 1)
    
    def load8(self, offset):
        return (self.loadU8(offset) << 24) >> 24
    
    def load16(self, offset):
        return (self.loadU16(offset) << 16) >> 16
    
    def loadU8(self, offset):
        index = offset >> 1
        if offset & 1:
            return (self.buffer[index] & 0xFF00) >> 8
        else:
            return self.buffer[index] & 0x00FF
    
    def loadU16(self, offset):
        return self.buffer[offset >> 1]
    
    def load32(self, offset):
        return self.buffer[(offset >> 1) & ~1] | (self.buffer[(offset >> 1) | 1] << 16)
    
    def store8(self, offset, value):
        index = offset >> 1
        self.store16(offset, (value << 8) | value)
    
    def store16(self, offset, value):
        self.buffer[offset >> 1] = value
    
    def store32(self, offset, value):
        index = offset >> 1
        self.buffer[index] = value & 0xFFFF
        self.store16(offset, self.buffer[index])
        self.buffer[index + 1] = value >> 16
        self.store16(offset + 2, self.buffer[index + 1])
    
    def insert(self, start, data):
        self.buffer[start:start+len(data)] = data
    
    def invalidatePage(self, address):
        pass


class GameBoyAdvanceVRAM(MemoryAligned16):
    def __init__(self, size):
        super().__init__(size)
        self.vram = self.buffer


class GameBoyAdvanceOAM(MemoryAligned16):
    def __init__(self, size):
        super().__init__(size)
        self.oam = self.buffer
        self.objs = [GameBoyAdvanceOBJ(self, i) for i in range(128)]
        self.scalerot = [{'a': 1, 'b': 0, 'c': 0, 'd': 1} for _ in range(32)]
    
    def overwrite(self, memory):
        for i in range(len(self.buffer) >> 1):
            self.store16(i << 1, memory[i])
    
    def store16(self, offset, value):
        index = (offset & 0x3F8) >> 3
        obj = self.objs[index]
        scalerot = self.scalerot[index >> 2]
        layer = obj.priority
        disable = obj.disable
        y = obj.y
        if offset & 0x00000006 == 0:
            # Attribute 0
            obj.y = value & 0x00FF
            wasScalerot = obj.scalerot
            obj.scalerot = value & 0x0100
            if obj.scalerot:
                obj.scalerotOam = self.scalerot[obj.scalerotParam]
                obj.doublesize = bool(value & 0x0200)
                obj.disable = 0
                obj.hflip = 0
                obj.vflip = 0
            else:
                obj.doublesize = False
                obj.disable = bool(value & 0x0200)
                if wasScalerot:
                    obj.hflip = obj.scalerotParam & 0x0008
                    obj.vflip = obj.scalerotParam & 0x0010
            obj.mode = (value & 0x0C00) >> 6
            obj.mosaic = bool(value & 0x1000)
            obj.multipalette = bool(value & 0x2000)
            obj.shape = (value & 0xC000) >> 14
            obj.recalcSize()
        elif offset & 0x00000006 == 2:
            # Attribute 1
            obj.x = value & 0x01FF
            if obj.scalerot:
                obj.scalerotParam = (value & 0x3E00) >> 9
                obj.scalerotOam = self.scalerot[obj.scalerotParam]
                obj.hflip = 0
                obj.vflip = 0
                obj.drawScanline = obj.drawScanlineAffine
            else:
                obj.hflip = bool(value & 0x1000)
                obj.vflip = bool(value & 0x2000)
                obj.drawScanline = obj.drawScanlineNormal
            obj.size = (value & 0xC000) >> 14
            obj.recalcSize()
        elif offset & 0x00000006 == 4:
            # Attribute 2
            obj.tileBase = value & 0x03FF
            obj.priority = (value & 0x0C00) >> 10
            obj.palette = (value & 0xF000) >> 8
        elif offset & 0x00000006 == 6:
            # Scaling/rotation parameter
            if index & 0x3 == 0:
                scalerot['a'] = (value << 16) / 0x1000000
            elif index & 0x3 == 1:
                scalerot['b'] = (value << 16) / 0x1000000
            elif index & 0x3 == 2:
                scalerot['c'] = (value << 16) / 0x1000000
            elif index & 0x3 == 3:
                scalerot['d'] = (value << 16) / 0x1000000
        super().store16(offset, value)


class GameBoyAdvanceOBJ:
    def __init__(self, oam, index):
        self.TILE_OFFSET = 0x10000
        self.oam = oam
        self.index = index
        self.x = 0
        self.y = 0
        self.scalerot = 0
        self.doublesize = False
        self.disable = 1
        self.mode = 0
        self.mosaic = False
        self.multipalette = False
        self.shape = 0
        self.scalerotParam = 0
        self.hflip = 0
        self.vflip = 0
        self.tileBase = 0
        self.priority = 0
        self.palette = 0
        self.drawScanline = self.drawScanlineNormal
        self.pushPixel = GameBoyAdvanceSoftwareRenderer.pushPixel
        self.cachedWidth = 8
        self.cachedHeight = 8
    
    def drawScanlineNormal(self, backing, y, yOff, start, end):
        video = self.oam.video
        x = 0
        underflow = 0
        offset = 0
        mask = self.mode | video.target2[video.LAYER_OBJ] | (self.priority << 1)
        if self.mode == 0x10:
            mask |= video.TARGET1_MASK
        if video.blendMode == 1 and video.alphaEnabled:
            mask |= video.target1[video.LAYER_OBJ]
        totalWidth = self.cachedWidth
        if self.x < video.HORIZONTAL_PIXELS:
            if self.x < start:
                underflow = start - self.x
                offset = start
            else:
                underflow = 0
                offset = self.x
            if end < self.cachedWidth + self.x:
                totalWidth = end - self.x
        else:
            underflow = start + 512 - self.x
            offset = start
            if end < self.cachedWidth - underflow:
                totalWidth = end
        localX = 0
        localY = 0
        if not self.vflip:
            localY = y - yOff
        else:
            localY = self.cachedHeight - y + yOff - 1
        localYLo = localY & 0x7
        mosaicX = 0
        tileOffset = 0
        paletteShift = 1 if self.multipalette else 0
        if video.objCharacterMapping:
            tileOffset = ((localY & 0x01F8) * self.cachedWidth) >> 6
        else:
            tileOffset = (localY & 0x01F8) << (2 - paletteShift)
        if self.mosaic:
            mosaicX = video.objMosaicX - 1 - (video.objMosaicX + offset - 1) % video.objMosaicX
            offset += mosaicX
            underflow += mosaicX
        if not self.hflip:
            localX = underflow
        else:
            localX = self.cachedWidth - underflow - 1
        tileRow = video.accessTile(self.TILE_OFFSET + (x & 0x4) * paletteShift, self.tileBase + (tileOffset << paletteShift) + ((localX & 0x01F8) >> (3 - paletteShift)), localYLo << paletteShift)
        for x in range(underflow, totalWidth):
            mosaicX = offset % video.objMosaicX if self.mosaic else 0
            if not self.hflip:
                localX = x - mosaicX
            else:
                localX = self.cachedWidth - (x - mosaicX) - 1
            if not paletteShift:
                if not (x & 0x7) or (self.mosaic and not mosaicX):
                    tileRow = video.accessTile(self.TILE_OFFSET, self.tileBase + tileOffset + (localX >> 3), localYLo)
            else:
                if not (x & 0x3) or (self.mosaic and not mosaicX):
                    tileRow = video.accessTile(self.TILE_OFFSET + (localX & 0x4), self.tileBase + (tileOffset << 1) + ((localX & 0x01F8) >> 2), localYLo << 1)
            self.pushPixel(video.LAYER_OBJ, self, video, tileRow, localX & 0x7, offset, backing, mask, False)
            offset += 1
    
    def drawScanlineAffine(self, backing, y, yOff, start, end):
        video = self.oam.video
        x = 0
        underflow = 0
        offset = 0
        mask = self.mode | video.target2[video.LAYER_OBJ] | (self.priority << 1)
        if self.mode == 0x10:
            mask |= video.TARGET1_MASK
        if video.blendMode == 1 and video.alphaEnabled:
            mask |= video.target1[video.LAYER_OBJ]
        localX = 0
        localY = 0
        yDiff = y - yOff
        tileOffset = 0
        paletteShift = 1 if self.multipalette else 0
        totalWidth = self.cachedWidth << self.doublesize
        totalHeight = self.cachedHeight << self.doublesize
        drawWidth = totalWidth
        if drawWidth > video.HORIZONTAL_PIXELS:
            totalWidth = video.HORIZONTAL_PIXELS
        if self.x < video.HORIZONTAL_PIXELS:
            if self.x < start:
                underflow = start - self.x
                offset = start
            else:
                underflow = 0
                offset = self.x
            if end < drawWidth + self.x:
                drawWidth = end - self.x
        else:
            underflow = start + 512 - self.x
            offset = start
            if end < drawWidth - underflow:
                drawWidth = end
        for x in range(underflow, drawWidth):
            localX = self.scalerotOam['a'] * (x - (totalWidth >> 1)) + self.scalerotOam['b'] * (yDiff - (totalHeight >> 1)) + (self.cachedWidth >> 1)
            localY = self.scalerotOam['c'] * (x - (totalWidth >> 1)) + self.scalerotOam['d'] * (yDiff - (totalHeight >> 1)) + (self.cachedHeight >> 1)
            if self.mosaic:
                localX -= (x % video.objMosaicX) * self.scalerotOam['a'] + (y % video.objMosaicY) * self.scalerotOam['b']
                localY -= (x % video.objMosaicX) * self.scalerotOam['c'] + (y % video.objMosaicY) * self.scalerotOam['d']
            if localX < 0 or localX >= self.cachedWidth or localY < 0 or localY >= self.cachedHeight:
                offset += 1
                continue
            if video.objCharacterMapping:
                tileOffset = ((localY & 0x01F8) * self.cachedWidth) >> 6
            else:
                tileOffset = (localY & 0x01F8) << (2 - paletteShift)
            tileRow = video.accessTile(self.TILE_OFFSET + (localX & 0x4) * paletteShift, self.tileBase + (tileOffset << paletteShift) + ((localX & 0x01F8) >> (3 - paletteShift)), (localY & 0x7) << paletteShift)
            self.pushPixel(video.LAYER_OBJ, self, video, tileRow, localX & 0x7, offset, backing, mask, False)
            offset += 1
    
    def recalcSize(self):
        if self.shape == 0:
            self.cachedHeight = self.cachedWidth = 8 << self.size
        elif self.shape == 1:
            if self.size == 0:
                self.cachedHeight = 8
                self.cachedWidth = 16
            elif self.size == 1:
                self.cachedHeight = 8
                self.cachedWidth = 32
            elif self.size == 2:
                self.cachedHeight = 16
                self.cachedWidth = 32
            elif self.size == 3:
                self.cachedHeight = 32
                self.cachedWidth = 64
        elif self.shape == 2:
            if self.size == 0:
                self.cachedHeight = 16
                self.cachedWidth = 8
            elif self.size == 1:
                self.cachedHeight = 32
                self.cachedWidth = 8
            elif self.size == 2:
                self.cachedHeight = 32
                self.cachedWidth = 16
            elif self.size == 3:
                self.cachedHeight = 64
                self.cachedWidth = 32


class GameBoyAdvancePalette:
    def __init__(self):
        self.colors = [[0] * 0x100, [0] * 0x100]
        self.adjustedColors = [[0] * 0x100, [0] * 0x100]
        self.passthroughColors = [
            self.colors[0],  # BG0
            self.colors[0],  # BG1
            self.colors[0],  # BG2
            self.colors[0],  # BG3
            self.colors[1],  # OBJ
            self.colors[0]  # Backdrop
        ]
        self.blendY = 1
    
    def overwrite(self, memory):
        for i in range(512):
            self.store16(i << 1, memory[i])
    
    def loadU8(self, offset):
        return (self.loadU16(offset) >> (8 * (offset & 1))) & 0xFF
    
    def loadU16(self, offset):
        return self.colors[(offset & 0x200) >> 9][(offset & 0x1FF) >> 1]
    
    def load16(self, offset):
        return (self.loadU16(offset) << 16) >> 16
    
    def load32(self, offset):
        return self.loadU16(offset) | (self.loadU16(offset + 2) << 16)
    
    def store16(self, offset, value):
        type = (offset & 0x200) >> 9
        index = (offset & 0x1FF) >> 1
        self.colors[type][index] = value
        self.adjustedColors[type][index] = self.adjustColor(value)
    
    def store32(self, offset, value):
        self.store16(offset, value & 0xFFFF)
        self.store16(offset + 2, value >> 16)
    
    def invalidatePage(self, address):
        pass
    
    def convert16To32(self, value, input):
        r = (value & 0x001F) << 3
        g = (value & 0x03E0) >> 2
        b = (value & 0x7C00) >> 7
        input[0] = r
        input[1] = g
        input[2] = b
    
    def mix(self, aWeight, aColor, bWeight, bColor):
        ar = (aColor & 0x001F)
        ag = (aColor & 0x03E0) >> 5
        ab = (aColor & 0x7C00) >> 10
        br = (bColor & 0x001F)
        bg = (bColor & 0x03E0) >> 5
        bb = (bColor & 0x7C00) >> 10
        r = min(aWeight * ar + bWeight * br, 0x1F)
        g = min(aWeight * ag + bWeight * bg, 0x1F)
        b = min(aWeight * ab + bWeight * bb, 0x1F)
        return r | (g << 5) | (b << 10)
    
    def makeDarkPalettes(self, layers):
        if self.adjustColor != self.adjustColorDark:
            self.adjustColor = self.adjustColorDark
            self.resetPalettes()
        self.resetPaletteLayers(layers)
    
    def makeBrightPalettes(self, layers):
        if self.adjustColor != self.adjustColorBright:
            self.adjustColor = self.adjustColorBright
            self.resetPalettes()
        self.resetPaletteLayers(layers)
    
    def makeNormalPalettes(self):
        self.passthroughColors[0] = self.colors[0]
        self.passthroughColors[1] = self.colors[0]
        self.passthroughColors[2] = self.colors[0]
        self.passthroughColors[3] = self.colors[0]
        self.passthroughColors[4] = self.colors[1]
        self.passthroughColors[5] = self.colors[0]
    
    def makeSpecialPalette(self, layer):
        self.passthroughColors[layer] = self.adjustedColors[1] if layer == 4 else self.adjustedColors[0]
    
    def makeNormalPalette(self, layer):
        self.passthroughColors[layer] = self.colors[1] if layer == 4 else self.colors[0]
    
    def resetPaletteLayers(self, layers):
        if layers & 0x01:
            self.passthroughColors[0] = self.adjustedColors[0]
        else:
            self.passthroughColors[0] = self.colors[0]
        if layers & 0x02:
            self.passthroughColors[1] = self.adjustedColors[0]
        else:
            self.passthroughColors[1] = self.colors[0]
        if layers & 0x04:
            self.passthroughColors[2] = self.adjustedColors[0]
        else:
            self.passthroughColors[2] = self.colors[0]
        if layers & 0x08:
            self.passthroughColors[3] = self.adjustedColors[0]
        else:
            self.passthroughColors[3] = self.colors[0]
        if layers & 0x10:
            self.passthroughColors[4] = self.adjustedColors[1]
        else:
            self.passthroughColors[4] = self.colors[1]
        if layers & 0x20:
            self.passthroughColors[5] = self.adjustedColors[0]
        else:
            self.passthroughColors[5] = self.colors[0]
    
    def resetPalettes(self):
        outPalette = self.adjustedColors[0]
        inPalette = self.colors[0]
        for i in range(256):
            outPalette[i] = self.adjustColor(inPalette[i])
        outPalette = self.adjustedColors[1]
        inPalette = self.colors[1]
        for i in range(256):
            outPalette[i] = self.adjustColor(inPalette[i])
    
    def accessColor(self, layer, index):
        return self.passthroughColors[layer][index]
    
    def adjustColorDark(self, color):
        r = (color & 0x001F)
        g = (color & 0x03E0) >> 5
        b = (color & 0x7C00) >> 10
        r = r - (r * self.blendY)
        g = g - (g * self.blendY)
        b = b - (b * self.blendY)
        return r | (g << 5) | (b << 10)
    
    def adjustColorBright(self, color):
        r = (color & 0x001F)
        g = (color & 0x03E0) >> 5
        b = (color & 0x7C00) >> 10
        r = r + ((31 - r) * self.blendY)
        g = g + ((31 - g) * self.blendY)
        b = b + ((31 - b) * self.blendY)
        return r | (g << 5) | (b << 10)
    
    def setBlendY(self, y):
        if self.blendY != y:
            self.blendY = y
            self.resetPalettes()
            
class GameBoyAdvanceOBJLayer:
    def __init__(self, video, index):
        self.video = video
        self.bg = False
        self.index = video.LAYER_OBJ
        self.priority = index
        self.enabled = False
        self.objwin = 0

    def drawScanline(self, backing, layer, start, end):
        y = self.video.vcount
        wrappedY = 0
        mosaicY = 0
        obj = None

        if start >= end:
            return

        objs = self.video.oam.objs
        for i in range(len(objs)):
            obj = objs[i]
            if obj.disable:
                continue
            if (obj.mode & self.video.OBJWIN_MASK) != self.objwin:
                continue
            if not (obj.mode & self.video.OBJWIN_MASK) and self.priority != obj.priority:
                continue
            if obj.y < self.video.VERTICAL_PIXELS:
                wrappedY = obj.y
            else:
                wrappedY = obj.y - 256
            if not obj.scalerot:
                totalHeight = obj.cachedHeight
            else:
                totalHeight = obj.cachedHeight << obj.doublesize
            if not obj.mosaic:
                mosaicY = y
            else:
                mosaicY = y - y % self.video.objMosaicY
            if wrappedY <= y and (wrappedY + totalHeight) > y:
                obj.drawScanline(backing, mosaicY, wrappedY, start, end)

    def objComparator(self, a, b):
        return a.index - b.index


class GameBoyAdvanceSoftwareRenderer:
    def __init__(self):
        self.LAYER_BG0 = 0
        self.LAYER_BG1 = 1
        self.LAYER_BG2 = 2
        self.LAYER_BG3 = 3
        self.LAYER_OBJ = 4
        self.LAYER_BACKDROP = 5

        self.HORIZONTAL_PIXELS = 240
        self.VERTICAL_PIXELS = 160

        self.LAYER_MASK = 0x06
        self.BACKGROUND_MASK = 0x01
        self.TARGET2_MASK = 0x08
        self.TARGET1_MASK = 0x10
        self.OBJWIN_MASK = 0x20
        self.WRITTEN_MASK = 0x80

        self.PRIORITY_MASK = self.LAYER_MASK | self.BACKGROUND_MASK

        self.drawBackdrop = GameBoyAdvanceOBJLayer(self, self.LAYER_BACKDROP)
        self.drawBackdrop.bg = True
        self.drawBackdrop.priority = -1
        self.drawBackdrop.enabled = True

    def clear(self, mmu):
        self.palette = GameBoyAdvancePalette()
        self.vram = GameBoyAdvanceVRAM(mmu.SIZE_VRAM)
        self.oam = GameBoyAdvanceOAM(mmu.SIZE_OAM)
        self.oam.video = self
        self.objLayers = [
            GameBoyAdvanceOBJLayer(self, 0),
            GameBoyAdvanceOBJLayer(self, 1),
            GameBoyAdvanceOBJLayer(self, 2),
            GameBoyAdvanceOBJLayer(self, 3)
        ]
        self.objwinLayer = GameBoyAdvanceOBJLayer(self, 4)
        self.objwinLayer.objwin = self.OBJWIN_MASK

        self.backgroundMode = 0
        self.displayFrameSelect = 0
        self.hblankIntervalFree = 0
        self.objCharacterMapping = 0
        self.forcedBlank = 1
        self.win0 = 0
        self.win1 = 0
        self.objwin = 0

        self.vcount = -1

        self.win0Left = 0
        self.win0Right = 240

        self.win1Left = 0
        self.win1Right = 240

        self.win0Top = 0
        self.win0Bottom = 160

        self.win1Top = 0
        self.win1Bottom = 160

        self.windows = [
            {"enabled": [False, False, False, False, False, True], "special": 0},
            {"enabled": [False, False, False, False, False, True], "special": 0},
            {"enabled": [False, False, False, False, False, True], "special": 0},
            {"enabled": [False, False, False, False, False, True], "special": 0}
        ]

        self.target1 = [0] * 5
        self.target2 = [0] * 5
        self.blendMode = 0

        self.blendA = 0
        self.blendB = 0

        self.blendY = 0

        self.bgMosaicX = 1
        self.bgMosaicY = 1
        self.objMosaicX = 1
        self.objMosaicY = 1

        self.lastHblank = 0
        self.nextHblank = self.HDRAW_LENGTH
        self.nextEvent = self.nextHblank

        self.nextHblankIRQ = 0
        self.nextVblankIRQ = 0
        self.nextVcounterIRQ = 0

        self.bg = [
            {
                "bg": True,
                "index": i,
                "enabled": False,
                "video": self,
                "vram": self.vram,
                "priority": 0,
                "charBase": 0,
                "mosaic": False,
                "multipalette": False,
                "screenBase": 0,
                "overflow": 0,
                "size": 0,
                "x": 0,
                "y": 0,
                "refx": 0,
                "refy": 0,
                "dx": 1,
                "dmx": 0,
                "dy": 0,
                "dmy": 1,
                "sx": 0,
                "sy": 0,
                "pushPixel": self.pushPixel,
                "drawScanline": self.drawScanlineBGMode0
            } for i in range(4)
        ]

        self.bgModes = [
            self.drawScanlineBGMode0,
            self.drawScanlineBGMode2,
            self.drawScanlineBGMode2,
            self.drawScanlineBGMode3,
            self.drawScanlineBGMode4,
            self.drawScanlineBGMode5
        ]

        self.drawLayers = [
            self.bg[0],
            self.bg[1],
            self.bg[2],
            self.bg[3],
            self.objLayers[0],
            self.objLayers[1],
            self.objLayers[2],
            self.objLayers[3],
            self.objwinLayer,
            self.drawBackdrop
        ]

        self.objwinActive = False
        self.alphaEnabled = False

        self.scanline = {
            "color": [0] * self.HORIZONTAL_PIXELS,
            "stencil": [0] * self.HORIZONTAL_PIXELS
        }

        self.sharedColor = [0, 0, 0]
        self.sharedMap = {
            "tile": 0,
            "hflip": False,
            "vflip": False,
            "palette": 0
        }

    def clearSubsets(self, mmu, regions):
        if regions & 0x04:
            self.palette.overwrite([0] * (mmu.SIZE_PALETTE >> 1))

        if regions & 0x08:
            self.vram.insert(0, [0] * (mmu.SIZE_VRAM >> 1))

        if regions & 0x10:
            self.oam.overwrite([0] * (mmu.SIZE_OAM >> 1))
            self.oam.video = self

    def freeze(self):
        pass

    def defrost(self, frost):
        pass

    def setBacking(self, backing):
        self.pixelData = backing

        for offset in range(0, self.HORIZONTAL_PIXELS * self.VERTICAL_PIXELS * 4, 4):
            self.pixelData.data[offset] = 0xFF
            self.pixelData.data[offset + 1] = 0xFF
            self.pixelData.data[offset + 2] = 0xFF
            self.pixelData.data[offset + 3] = 0xFF

    def writeDisplayControl(self, value):
        self.backgroundMode = value & 0x0007
        self.displayFrameSelect = value & 0x0010
        self.hblankIntervalFree = value & 0x0020
        self.objCharacterMapping = value & 0x0040
        self.forcedBlank = value & 0x0080
        self.bg[0].enabled = bool(value & 0x0100)
        self.bg[1].enabled = bool(value & 0x0200)
        self.bg[2].enabled = bool(value & 0x0400)
        self.bg[3].enabled = bool(value & 0x0800)
        self.objLayers[0].enabled = bool(value & 0x1000)
        self.objLayers[1].enabled = bool(value & 0x1000)
        self.objLayers[2].enabled = bool(value & 0x1000)
        self.objLayers[3].enabled = bool(value & 0x1000)
        self.win0 = bool(value & 0x2000)
        self.win1 = bool(value & 0x4000)
        self.objwin = bool(value & 0x8000)
        self.objwinLayer.enabled = bool(value & 0x1000) and bool(value & 0x8000)

        self.bg[2].multipalette &= ~0x0001
        self.bg[3].multipalette &= ~0x0001
        if self.backgroundMode > 0:
            self.bg[2].multipalette |= 0x0001
        if self.backgroundMode == 2:
            self.bg[3].multipalette |= 0x0001

        self.resetLayers()

    def writeBackgroundControl(self, bg, value):
        bgData = self.bg[bg]
        bgData.priority = value & 0x0003
        bgData.charBase = (value & 0x000C) << 12
        bgData.mosaic = bool(value & 0x0040)
        bgData.multipalette &= ~0x0080
        if bg < 2 or self.backgroundMode == 0:
            bgData.multipalette |= bool(value & 0x0080)
        bgData.screenBase = (value & 0x1F00) << 3
        bgData.overflow = bool(value & 0x2000)
        bgData.size = (value & 0xC000) >> 14

        self.drawLayers.sort(self.layerComparator)

    def writeBackgroundHOffset(self, bg, value):
        self.bg[bg].x = value & 0x1FF

    def writeBackgroundVOffset(self, bg, value):
        self.bg[bg].y = value & 0x1FF

    def writeBackgroundRefX(self, bg, value):
        self.bg[bg].refx = (value << 4) / 0x1000
        self.bg[bg].sx = self.bg[bg].refx

    def writeBackgroundRefY(self, bg, value):
        self.bg[bg].refy = (value << 4) / 0x1000
        self.bg[bg].sy = self.bg[bg].refy

    def writeBackgroundParamA(self, bg, value):
        self.bg[bg].dx = (value << 16) / 0x1000000

    def writeBackgroundParamB(self, bg, value):
        self.bg[bg].dmx = (value << 16) / 0x1000000

    def writeBackgroundParamC(self, bg, value):
        self.bg[bg].dy = (value << 16) / 0x1000000

    def writeBackgroundParamD(self, bg, value):
        self.bg[bg].dmy = (value << 16) / 0x1000000

    def writeWin0H(self, value):
        self.win0Left = (value & 0xFF00) >> 8
        self.win0Right = min(self.HORIZONTAL_PIXELS, value & 0x00FF)
        if self.win0Left > self.win0Right:
            self.win0Right = self.HORIZONTAL_PIXELS

    def writeWin1H(self, value):
        self.win1Left = (value & 0xFF00) >> 8
        self.win1Right = min(self.HORIZONTAL_PIXELS, value & 0x00FF)
        if self.win1Left > self.win1Right:
            self.win1Right = self.HORIZONTAL_PIXELS

    def writeWin0V(self, value):
        self.win0Top = (value & 0xFF00) >> 8
        self.win0Bottom = min(self.VERTICAL_PIXELS, value & 0x00FF)
        if self.win0Top > self.win0Bottom:
            self.win0Bottom = self.VERTICAL_PIXELS

    def writeWin1V(self, value):
        self.win1Top = (value & 0xFF00) >> 8
        self.win1Bottom = min(self.VERTICAL_PIXELS, value & 0x00FF)
        if self.win1Top > self.win1Bottom:
            self.win1Bottom = self.VERTICAL_PIXELS

    def writeWindow(self, index, value):
        window = self.windows[index]
        window["enabled"][0] = bool(value & 0x01)
        window["enabled"][1] = bool(value & 0x02)
        window["enabled"][2] = bool(value & 0x04)
        window["enabled"][3] = bool(value & 0x08)
        window["enabled"][4] = bool(value & 0x10)
        window["special"] = bool(value & 0x20)

    def writeWinIn(self, value):
        self.writeWindow(0, value)
        self.writeWindow(1, value >> 8)

    def writeWinOut(self, value):
        self.writeWindow(2, value)
        self.writeWindow(3, value >> 8)

    def writeBlendControl(self, value):
        self.target1[0] = bool(value & 0x0001) * self.TARGET1_MASK
        self.target1[1] = bool(value & 0x0002) * self.TARGET1_MASK
        self.target1[2] = bool(value & 0x0004) * self.TARGET1_MASK
        self.target1[3] = bool(value & 0x0008) * self.TARGET1_MASK
        self.target1[4] = bool(value & 0x0010) * self.TARGET1_MASK
        self.target1[5] = bool(value & 0x0020) * self.TARGET1_MASK
        self.target2[0] = bool(value & 0x0100) * self.TARGET2_MASK
        self.target2[1] = bool(value & 0x0200) * self.TARGET2_MASK
        self.target2[2] = bool(value & 0x0400) * self.TARGET2_MASK
        self.target2[3] = bool(value & 0x0800) * self.TARGET2_MASK
        self.target2[4] = bool(value & 0x1000) * self.TARGET2_MASK
        self.target2[5] = bool(value & 0x2000) * self.TARGET2_MASK
        self.blendMode = (value & 0x00C0) >> 6

        if self.blendMode == 1:
            self.palette.makeNormalPalettes()
        elif self.blendMode == 2:
            self.palette.makeBrightPalettes(value & 0x3F)
        elif self.blendMode == 3:
            self.palette.makeDarkPalettes(value & 0x3F)

    def setBlendEnabled(self, layer, enabled, override):
        self.alphaEnabled = enabled and override == 1
        if enabled:
            if override == 1:
                self.palette.makeNormalPalette(layer)
            elif override == 2 or override == 3:
                self.palette.makeSpecialPalette(layer)
        else:
            self.palette.makeNormalPalette(layer)

    def writeBlendAlpha(self, value):
        self.blendA = (value & 0x001F) / 16
        if self.blendA > 1:
            self.blendA = 1
        self.blendB = ((value & 0x1F00) >> 8) / 16
        if self.blendB > 1:
            self.blendB = 1

    def writeBlendY(self, value):
        self.blendY = value
        self.palette.setBlendY(1 if value >= 16 else value / 16)

    def writeMosaic(self, value):
        self.bgMosaicX = (value & 0xF) + 1
        self.bgMosaicY = ((value >> 4) & 0xF) + 1
        self.objMosaicX = ((value >> 8) & 0xF) + 1
        self.objMosaicY = ((value >> 12) & 0xF) + 1

    def resetLayers(self):
        if self.backgroundMode > 1:
            self.bg[0].enabled = False
            self.bg[1].enabled = False
        if self.bg[2].enabled:
            self.bg[2].drawScanline = self.bgModes[self.backgroundMode]
        if self.backgroundMode == 0 or self.backgroundMode == 2:
            if self.bg[3].enabled:
                self.bg[3].drawScanline = self.bgModes[self.backgroundMode]
        else:
            self.bg[3].enabled = False
        self.drawLayers.sort(self.layerComparator)

    def layerComparator(self, a, b):
        diff = b["priority"] - a["priority"]
        if not diff:
            if a["bg"] and not b["bg"]:
                return -1
            elif not a["bg"] and b["bg"]:
                return 1
            return b["index"] - a["index"]
        return diff

    def accessMapMode0(self, base, size, x, yBase, out):
        offset = base + ((x >> 2) & 0x3E) + yBase

        if size & 1:
            offset += (x & 0x100) << 3

        mem = self.vram.loadU16(offset)
        out["tile"] = mem & 0x03FF
        out["hflip"] = bool(mem & 0x0400)
        out["vflip"] = bool(mem & 0x0800)
        out["palette"] = (mem & 0xF000) >> 8

    def accessMapMode1(self, base, size, x, yBase, out):
        offset = base + (x >> 3) + yBase

        out["tile"] = self.vram.loadU8(offset)

    def accessTile(self, base, tile, y):
        offset = base + (tile << 5)
        offset |= y << 2

        return self.vram.load32(offset)

    def pushPixel(self, layer, map, video, row, x, offset, backing, mask, raw):
        index = 0
        if not raw:
            if layer["multipalette"]:
                index = (row >> (x << 3)) & 0xFF
            else:
                index = (row >> (x << 2)) & 0xF
            if not index:
                return
            elif not layer["multipalette"]:
                index |= map["palette"]
        stencil = video.WRITTEN_MASK
        oldStencil = backing["stencil"][offset]
        blend = video.blendMode
        if video.objwinActive:
            if oldStencil & video.OBJWIN_MASK:
                if video.windows[3]["enabled"][layer]:
                    video.setBlendEnabled(layer, video.windows[3]["special"] and video.target1[layer], blend)
                    if video.windows[3]["special"] and video.alphaEnabled:
                        mask |= video.target1[layer]
                    stencil |= video.OBJWIN_MASK
                else:
                    return
            elif video.windows[2]["enabled"][layer]:
                video.setBlendEnabled(layer, video.windows[2]["special"] and video.target1[layer], blend)
                if video.windows[2]["special"] and video.alphaEnabled:
                    mask |= video.target1[layer]
            else:
                return

        if mask & video.TARGET1_MASK and oldStencil & video.TARGET2_MASK:
            video.setBlendEnabled(layer, True, 1)

        pixel = row if raw else video.palette.accessColor(layer, index)

        if mask & video.TARGET1_MASK:
            video.setBlendEnabled(layer, bool(blend), blend)

        highPriority = (mask & video.PRIORITY_MASK) < (oldStencil & video.PRIORITY_MASK)
        if (mask & video.PRIORITY_MASK) == (oldStencil & video.PRIORITY_MASK):
            highPriority = bool(mask & video.BACKGROUND_MASK)

        if not (oldStencil & video.WRITTEN_MASK):
            stencil |= mask
        elif highPriority:
            if mask & video.TARGET1_MASK and oldStencil & video.TARGET2_MASK:
                pixel = video.palette.mix(video.blendA, pixel, video.blendB, backing["color"][offset])
            stencil |= mask & ~video.TARGET1_MASK
        elif (mask & video.PRIORITY_MASK) > (oldStencil & video.PRIORITY_MASK):
            stencil = oldStencil & ~(video.TARGET1_MASK | video.TARGET2_MASK)
            if mask & video.TARGET2_MASK and oldStencil & video.TARGET1_MASK:
                pixel = video.palette.mix(video.blendB, pixel, video.blendA, backing["color"][offset])
            else:
                return
        else:
            return

        if mask & video.OBJWIN_MASK:
            backing["stencil"][offset] |= video.OBJWIN_MASK
            return

        backing["color"][offset] = pixel
        backing["stencil"][offset] = stencil

    def identity(self, x):
        return x

    def drawScanlineBlank(self, backing):
        for x in range(self.HORIZONTAL_PIXELS):
            backing["color"][x] = 0xFFFF
            backing["stencil"][x] = 0

    def prepareScanline(self, backing):
        for x in range(self.HORIZONTAL_PIXELS):
            backing["stencil"][x] = self.target2[self.LAYER_BACKDROP]

    def drawScanline(self, y):
        backing = self.scanline
        if self.forcedBlank:
            self.drawScanlineBlank(backing)
            return
        self.prepareScanline(backing)
        for i in range(len(self.drawLayers)):
            layer = self.drawLayers[i]
            if not layer["enabled"]:
                continue
            self.objwinActive = False
            if not (self.win0 or self.win1 or self.objwin):
                self.setBlendEnabled(layer["index"], self.target1[layer["index"]], self.blendMode)
                layer["drawScanline"](backing, layer, 0, self.HORIZONTAL_PIXELS)
            else:
                firstStart = 0
                firstEnd = self.HORIZONTAL_PIXELS
                lastStart = 0
                lastEnd = self.HORIZONTAL_PIXELS
                if self.win0 and y >= self.win0Top and y < self.win0Bottom:
                    if self.windows[0]["enabled"][layer["index"]]:
                        self.setBlendEnabled(layer["index"], self.windows[0]["special"] and self.target1[layer["index"]], self.blendMode)
                        layer["drawScanline"](backing, layer, self.win0Left, self.win0Right)
                    firstStart = max(firstStart, self.win0Left)
                    firstEnd = min(firstEnd, self.win0Left)
                    lastStart = max(lastStart, self.win0Right)
                    lastEnd = min(lastEnd, self.win0Right)
                if self.win1 and y >= self.win1Top and y < self.win1Bottom:
                    if self.windows[1]["enabled"][layer["index"]]:
                        self.setBlendEnabled(layer["index"], self.windows[1]["special"] and self.target1[layer["index"]], self.blendMode)
                        if not self.windows[0]["enabled"][layer["index"]] and (self.win1Left < firstStart or self.win1Right < lastStart):
                            layer["drawScanline"](backing, layer, self.win1Left, firstStart)
                            layer["drawScanline"](backing, layer, lastEnd, self.win1Right)
                        else:
                            layer["drawScanline"](backing, layer, self.win1Left, self.win1Right)
                    firstStart = max(firstStart, self.win1Left)
                    firstEnd = min(firstEnd, self.win1Left)
                    lastStart = max(lastStart, self.win1Right)
                    lastEnd = min(lastEnd, self.win1Right)
                if self.windows[2]["enabled"][layer["index"]] or (self.objwin and self.windows[3]["enabled"][layer["index"]]):
                    self.objwinActive = self.objwin
                    self.setBlendEnabled(layer["index"], self.windows[2]["special"] and self.target1[layer["index"]], self.blendMode)
                    if firstEnd > lastStart:
                        layer["drawScanline"](backing, layer, 0, self.HORIZONTAL_PIXELS)
                    else:
                        if firstEnd:
                            layer["drawScanline"](backing, layer, 0, firstEnd)
                        if lastStart < self.HORIZONTAL_PIXELS:
                            layer["drawScanline"](backing, layer, lastStart, self.HORIZONTAL_PIXELS)
                        if lastEnd < firstStart:
                            layer["drawScanline"](backing, layer, lastEnd, firstStart)
                self.setBlendEnabled(self.LAYER_BACKDROP, self.target1[self.LAYER_BACKDROP] and self.windows[2]["special"], self.blendMode)
        self.finishScanline(backing)

    def finishScanline(self, backing):
        bd = self.palette.accessColor(self.LAYER_BACKDROP, 0)
        xx = self.vcount * self.HORIZONTAL_PIXELS * 4
        isTarget2 = self.target2[self.LAYER_BACKDROP]
        for x in range(self.HORIZONTAL_PIXELS):
            if backing["stencil"][x] & self.WRITTEN_MASK:
                color = backing["color"][x]
                if isTarget2 and backing["stencil"][x] & self.TARGET1_MASK:
                    color = self.palette.mix(self.blendA, color, self.blendB, bd)
                self.palette.convert16To32(color, self.sharedColor)
            else:
                self.palette.convert16To32(bd, self.sharedColor)
            self.pixelData.data[xx] = self.sharedColor[0]
            self.pixelData.data[xx + 1] = self.sharedColor[1]
            self.pixelData.data[xx + 2] = self.sharedColor[2]
            xx += 4

    def startDraw(self):
        pass

    def finishDraw(self, caller):
        self.bg[2].sx = self.bg[2].refx
        self.bg[2].sy = self.bg[2].refy
        self.bg[3].sx = self.bg[3].refx
        self.bg[3].sy = self.bg[3].refy
        caller.finishDraw(self.pixelData)