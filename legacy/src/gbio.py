
class GameBoyAdvanceIO:
    def __init__(self):
        # Video
        self.DISPCNT = 0x000
        self.GREENSWP = 0x002
        self.DISPSTAT = 0x004
        self.VCOUNT = 0x006
        self.BG0CNT = 0x008
        self.BG1CNT = 0x00a
        self.BG2CNT = 0x00c
        self.BG3CNT = 0x00e
        self.BG0HOFS = 0x010
        self.BG0VOFS = 0x012
        self.BG1HOFS = 0x014
        self.BG1VOFS = 0x016
        self.BG2HOFS = 0x018
        self.BG2VOFS = 0x01a
        self.BG3HOFS = 0x01c
        self.BG3VOFS = 0x01e
        self.BG2PA = 0x020
        self.BG2PB = 0x022
        self.BG2PC = 0x024
        self.BG2PD = 0x026
        self.BG2X_LO = 0x028
        self.BG2X_HI = 0x02a
        self.BG2Y_LO = 0x02c
        self.BG2Y_HI = 0x02e
        self.BG3PA = 0x030
        self.BG3PB = 0x032
        self.BG3PC = 0x034
        self.BG3PD = 0x036
        self.BG3X_LO = 0x038
        self.BG3X_HI = 0x03a
        self.BG3Y_LO = 0x03c
        self.BG3Y_HI = 0x03e
        self.WIN0H = 0x040
        self.WIN1H = 0x042
        self.WIN0V = 0x044
        self.WIN1V = 0x046
        self.WININ = 0x048
        self.WINOUT = 0x04a
        self.MOSAIC = 0x04c
        self.BLDCNT = 0x050
        self.BLDALPHA = 0x052
        self.BLDY = 0x054

        # Sound
        self.SOUND1CNT_LO = 0x060
        self.SOUND1CNT_HI = 0x062
        self.SOUND1CNT_X = 0x064
        self.SOUND2CNT_LO = 0x068
        self.SOUND2CNT_HI = 0x06c
        self.SOUND3CNT_LO = 0x070
        self.SOUND3CNT_HI = 0x072
        self.SOUND3CNT_X = 0x074
        self.SOUND4CNT_LO = 0x078
        self.SOUND4CNT_HI = 0x07c
        self.SOUNDCNT_LO = 0x080
        self.SOUNDCNT_HI = 0x082
        self.SOUNDCNT_X = 0x084
        self.SOUNDBIAS = 0x088
        self.WAVE_RAM0_LO = 0x090
        self.WAVE_RAM0_HI = 0x092
        self.WAVE_RAM1_LO = 0x094
        self.WAVE_RAM1_HI = 0x096
        self.WAVE_RAM2_LO = 0x098
        self.WAVE_RAM2_HI = 0x09a
        self.WAVE_RAM3_LO = 0x09c
        self.WAVE_RAM3_HI = 0x09e
        self.FIFO_A_LO = 0x0a0
        self.FIFO_A_HI = 0x0a2
        self.FIFO_B_LO = 0x0a4
        self.FIFO_B_HI = 0x0a6

        # DMA
        self.DMA0SAD_LO = 0x0b0
        self.DMA0SAD_HI = 0x0b2
        self.DMA0DAD_LO = 0x0b4
        self.DMA0DAD_HI = 0x0b6
        self.DMA0CNT_LO = 0x0b8
        self.DMA0CNT_HI = 0x0ba
        self.DMA1SAD_LO = 0x0bc
        self.DMA1SAD_HI = 0x0be
        self.DMA1DAD_LO = 0x0c0
        self.DMA1DAD_HI = 0x0c2
        self.DMA1CNT_LO = 0x0c4
        self.DMA1CNT_HI = 0x0c6
        self.DMA2SAD_LO = 0x0c8
        self.DMA2SAD_HI = 0x0ca
        self.DMA2DAD_LO = 0x0cc
        self.DMA2DAD_HI = 0x0ce
        self.DMA2CNT_LO = 0x0d0
        self.DMA2CNT_HI = 0x0d2
        self.DMA3SAD_LO = 0x0d4
        self.DMA3SAD_HI = 0x0d6
        self.DMA3DAD_LO = 0x0d8
        self.DMA3DAD_HI = 0x0da
        self.DMA3CNT_LO = 0x0dc
        self.DMA3CNT_HI = 0x0de

        # Timers
        self.TM0CNT_LO = 0x100
        self.TM0CNT_HI = 0x102
        self.TM1CNT_LO = 0x104
        self.TM1CNT_HI = 0x106
        self.TM2CNT_LO = 0x108
        self.TM2CNT_HI = 0x10a
        self.TM3CNT_LO = 0x10c
        self.TM3CNT_HI = 0x10e

        # SIO (note: some of these are repeated)
        self.SIODATA32_LO = 0x120
        self.SIOMULTI0 = 0x120
        self.SIODATA32_HI = 0x122
        self.SIOMULTI1 = 0x122
        self.SIOMULTI2 = 0x124
        self.SIOMULTI3 = 0x126
        self.SIOCNT = 0x128
        self.SIOMLT_SEND = 0x12a
        self.SIODATA8 = 0x12a
        self.RCNT = 0x134
        self.JOYCNT = 0x140
        self.JOY_RECV = 0x150
        self.JOY_TRANS = 0x154
        self.JOYSTAT = 0x158

        # Keypad
        self.KEYINPUT = 0x130
        self.KEYCNT = 0x132

        # Interrupts, etc
        self.IE = 0x200
        self.IF = 0x202
        self.WAITCNT = 0x204
        self.IME = 0x208

        self.POSTFLG = 0x300
        self.HALTCNT = 0x301

        self.DEFAULT_DISPCNT = 0x0080
        self.DEFAULT_SOUNDBIAS = 0x200
        self.DEFAULT_BGPA = 1
        self.DEFAULT_BGPD = 1
        self.DEFAULT_RCNT = 0x8000

    def clear(self):
        self.registers = [0] * (self.cpu.mmu.SIZE_IO // 2)

        self.registers[self.DISPCNT >> 1] = self.DEFAULT_DISPCNT
        self.registers[self.SOUNDBIAS >> 1] = self.DEFAULT_SOUNDBIAS
        self.registers[self.BG2PA >> 1] = self.DEFAULT_BGPA
        self.registers[self.BG2PD >> 1] = self.DEFAULT_BGPD
        self.registers[self.BG3PA >> 1] = self.DEFAULT_BGPA
        self.registers[self.BG3PD >> 1] = self.DEFAULT_BGPD
        self.registers[self.RCNT >> 1] = self.DEFAULT_RCNT

    def freeze(self):
        return {
            'registers': self.registers
        }

    def defrost(self, frost):
        self.registers = frost['registers']
        # Video registers don't serialize themselves
        for i in range(0, self.BLDY + 2, 2):
            self.store16(i, self.registers[i >> 1])

    def load8(self, offset):
        raise NotImplementedError("Unimplemented unaligned I/O access")

    def load16(self, offset):
        return (self.loadU16(offset) << 16) >> 16

    def load32(self, offset):
        offset &= 0xfffffffc
        if offset in [self.DMA0CNT_LO, self.DMA1CNT_LO, self.DMA2CNT_LO, self.DMA3CNT_LO]:
            return self.loadU16(offset | 2) << 16
        elif offset == self.IME:
            return self.loadU16(offset) & 0xffff
        elif offset in [self.JOY_RECV, self.JOY_TRANS]:
            self.core.STUB("Unimplemented JOY register read: 0x" + hex(offset))
            return 0
        return self.loadU16(offset) | (self.loadU16(offset | 2) << 16)

    def loadU8(self, offset):
        odd = offset & 0x0001
        value = self.loadU16(offset & 0xfffe)
        return (value >> (odd << 3)) & 0xff

    def loadU16(self, offset):
        if offset in [self.DISPCNT, self.BG0CNT, self.BG1CNT, self.BG2CNT, self.BG3CNT, self.WININ, self.WINOUT,
                      self.SOUND1CNT_LO, self.SOUND3CNT_LO, self.SOUNDCNT_LO, self.SOUNDCNT_HI, self.SOUNDBIAS,
                      self.BLDCNT, self.BLDALPHA, self.TM0CNT_HI, self.TM1CNT_HI, self.TM2CNT_HI, self.TM3CNT_HI,
                      self.DMA0CNT_HI, self.DMA1CNT_HI, self.DMA2CNT_HI, self.DMA3CNT_HI, self.RCNT, self.WAITCNT,
                      self.IE, self.IF, self.IME, self.POSTFLG]:
            return self.registers[offset >> 1]
        elif offset == self.DISPSTAT:
            return self.registers[offset >> 1] | self.video.readDisplayStat()
        elif offset == self.VCOUNT:
            return self.video.vcount
        elif offset == self.SOUND1CNT_HI or offset == self.SOUND2CNT_LO:
            return self.registers[offset >> 1] & 0xffc0
        elif offset == self.SOUND1CNT_X or offset == self.SOUND2CNT_HI or offset == self.SOUND3CNT_X:
            return self.registers[offset >> 1] & 0x4000
        elif offset == self.SOUND3CNT_HI:
            return self.registers[offset >> 1] & 0xe000
        elif offset == self.SOUND4CNT_LO:
            return self.registers[offset >> 1] & 0xff00
        elif offset == self.SOUND4CNT_HI:
            return self.registers[offset >> 1] & 0x40ff
        elif offset == self.SOUNDCNT_X:
            self.core.STUB("Unimplemented sound register read: SOUNDCNT_X")
            return self.registers[offset >> 1] | 0x0000
        elif offset in [self.TM0CNT_LO, self.TM1CNT_LO, self.TM2CNT_LO, self.TM3CNT_LO]:
            return self.cpu.irq.timerRead(offset // 4)
        elif offset == self.SIOCNT:
            return self.sio.readSIOCNT()
        elif offset == self.KEYINPUT:
            self.keypad.pollGamepads()
            return self.keypad.currentDown
        elif offset == self.KEYCNT:
            self.core.STUB("Unimplemented I/O register read: KEYCNT")
            return 0
        elif offset in [self.BG0HOFS, self.BG0VOFS, self.BG1HOFS, self.BG1VOFS, self.BG2HOFS, self.BG2VOFS,
                        self.BG3HOFS, self.BG3VOFS, self.BG2PA, self.BG2PB, self.BG2PC, self.BG2PD, self.BG3PA,
                        self.BG3PB, self.BG3PC, self.BG3PD, self.BG2X_LO, self.BG2X_HI, self.BG2Y_LO, self.BG2Y_HI,
                        self.BG3X_LO, self.BG3X_HI, self.BG3Y_LO, self.BG3Y_HI, self.WIN0H, self.WIN1H, self.WIN0V,
                        self.WIN1V, self.BLDY, self.DMA0SAD_LO, self.DMA0SAD_HI, self.DMA0DAD_LO, self.DMA0DAD_HI,
                        self.DMA0CNT_LO, self.DMA1SAD_LO, self.DMA1SAD_HI, self.DMA1DAD_LO, self.DMA1DAD_HI,
                        self.DMA1CNT_LO, self.DMA2SAD_LO, self.DMA2SAD_HI, self.DMA2DAD_LO, self.DMA2DAD_HI,
                        self.DMA2CNT_LO, self.DMA3SAD_LO, self.DMA3SAD_HI, self.DMA3DAD_LO, self.DMA3DAD_HI,
                        self.DMA3CNT_LO, self.FIFO_A_LO, self.FIFO_A_HI, self.FIFO_B_LO, self.FIFO_B_HI]:
            self.core.WARN("Read for write-only register: 0x" + hex(offset))
            return self.core.mmu.badMemory.loadU16(0)
        elif offset == self.MOSAIC:
            self.core.WARN("Read for write-only register: 0x" + hex(offset))
            return 0
        elif offset in [self.SIOMULTI0, self.SIOMULTI1, self.SIOMULTI2, self.SIOMULTI3]:
            return self.sio.read((offset - self.SIOMULTI0) >> 1)
        elif offset == self.SIODATA8:
            self.core.STUB("Unimplemented SIO register read: 0x" + hex(offset))
            return 0
        elif offset in [self.JOYCNT, self.JOYSTAT]:
            self.core.STUB("Unimplemented JOY register read: 0x" + hex(offset))
            return 0
        else:
            self.core.WARN("Bad I/O register read: 0x" + hex(offset))
            return self.core.mmu.badMemory.loadU16(0)

    def store8(self, offset, value):
        if offset in [self.WININ, self.WININ | 1, self.WINOUT, self.WINOUT | 1, self.SOUND1CNT_LO, self.SOUND1CNT_LO | 1,
                      self.SOUND1CNT_HI, self.SOUND1CNT_HI | 1, self.SOUND1CNT_X, self.SOUND1CNT_X | 1,
                      self.SOUND2CNT_LO, self.SOUND2CNT_LO | 1, self.SOUND2CNT_HI, self.SOUND2CNT_HI | 1,
                      self.SOUND3CNT_LO, self.SOUND3CNT_LO | 1, self.SOUND3CNT_HI, self.SOUND3CNT_HI | 1,
                      self.SOUND3CNT_X, self.SOUND3CNT_X | 1, self.SOUND4CNT_LO, self.SOUND4CNT_LO | 1,
                      self.SOUND4CNT_HI, self.SOUND4CNT_HI | 1, self.SOUNDCNT_LO, self.SOUNDCNT_LO | 1,
                      self.SOUNDCNT_X, self.IF, self.IME]:
            pass
        elif offset == self.SOUNDBIAS | 1:
            self.STUB_REG("sound", offset)
        elif offset == self.HALTCNT:
            value &= 0x80
            if not value:
                self.core.irq.halt()
            else:
                self.core.STUB("Stop")
            return
        else:
            self.STUB_REG("8-bit I/O", offset)
        if offset & 1:
            value <<= 8
            value |= self.registers[offset >> 1] & 0x00ff
        else:
            value &= 0x00ff
            value |= self.registers[offset >> 1] & 0xff00
        self.store16(offset & 0xffffffe, value)

    def store16(self, offset, value):
        if offset == self.DISPCNT:
            self.video.renderPath.writeDisplayControl(value)
        elif offset == self.DISPSTAT:
            value &= self.video.DISPSTAT_MASK
            self.video.writeDisplayStat(value)
        elif offset == self.BG0CNT:
            self.video.renderPath.writeBackgroundControl(0, value)
        elif offset == self.BG1CNT:
            self.video.renderPath.writeBackgroundControl(1, value)
        elif offset == self.BG2CNT:
            self.video.renderPath.writeBackgroundControl(2, value)
        elif offset == self.BG3CNT:
            self.video.renderPath.writeBackgroundControl(3, value)
        elif offset == self.BG0HOFS:
            self.video.renderPath.writeBackgroundHOffset(0, value)
        elif offset == self.BG0VOFS:
            self.video.renderPath.writeBackgroundVOffset(0, value)
        elif offset == self.BG1HOFS:
            self.video.renderPath.writeBackgroundHOffset(1, value)
        elif offset == self.BG1VOFS:
            self.video.renderPath.writeBackgroundVOffset(1, value)
        elif offset == self.BG2HOFS:
            self.video.renderPath.writeBackgroundHOffset(2, value)
        elif offset == self.BG2VOFS:
            self.video.renderPath.writeBackgroundVOffset(2, value)
        elif offset == self.BG3HOFS:
            self.video.renderPath.writeBackgroundHOffset(3, value)
        elif offset == self.BG3VOFS:
            self.video.renderPath.writeBackgroundVOffset(3, value)
        elif offset == self.BG2X_LO:
            self.video.renderPath.writeBackgroundRefX(2, (self.registers[(offset >> 1) | 1] << 16) | value)
        elif offset == self.BG2X_HI:
            self.video.renderPath.writeBackgroundRefX(2, self.registers[(offset >> 1) ^ 1] | (value << 16))
        elif offset == self.BG2Y_LO:
            self.video.renderPath.writeBackgroundRefY(2, (self.registers[(offset >> 1) | 1] << 16) | value)
        elif offset == self.BG2Y_HI:
            self.video.renderPath.writeBackgroundRefY(2, self.registers[(offset >> 1) ^ 1] | (value << 16))
        elif offset == self.BG2PA:
            self.video.renderPath.writeBackgroundParamA(2, value)
        elif offset == self.BG2PB:
            self.video.renderPath.writeBackgroundParamB(2, value)
        elif offset == self.BG2PC:
            self.video.renderPath.writeBackgroundParamC(2, value)
        elif offset == self.BG2PD:
            self.video.renderPath.writeBackgroundParamD(2, value)
        elif offset == self.BG3X_LO:
            self.video.renderPath.writeBackgroundRefX(3, (self.registers[(offset >> 1) | 1] << 16) | value)
        elif offset == self.BG3X_HI:
            self.video.renderPath.writeBackgroundRefX(3, self.registers[(offset >> 1) ^ 1] | (value << 16))
        elif offset == self.BG3Y_LO:
            self.video.renderPath.writeBackgroundRefY(3, (self.registers[(offset >> 1) | 1] << 16) | value)
        elif offset == self.BG3Y_HI:
            self.video.renderPath.writeBackgroundRefY(3, self.registers[(offset >> 1) ^ 1] | (value << 16))
        elif offset == self.BG3PA:
            self.video.renderPath.writeBackgroundParamA(3, value)
        elif offset == self.BG3PB:
            self.video.renderPath.writeBackgroundParamB(3, value)
        elif offset == self.BG3PC:
            self.video.renderPath.writeBackgroundParamC(3, value)
        elif offset == self.BG3PD:
            self.video.renderPath.writeBackgroundParamD(3, value)
        elif offset == self.WIN0H:
            self.video.renderPath.writeWin0H(value)
        elif offset == self.WIN1H:
            self.video.renderPath.writeWin1H(value)
        elif offset == self.WIN0V:
            self.video.renderPath.writeWin0V(value)
        elif offset == self.WIN1V:
            self.video.renderPath.writeWin1V(value)
        elif offset == self.WININ:
            value &= 0x3f3f
            self.video.renderPath.writeWinIn(value)
        elif offset == self.WINOUT:
            value &= 0x3f3f
            self.video.renderPath.writeWinOut(value)
        elif offset == self.BLDCNT:
            value &= 0x7fff
            self.video.renderPath.writeBlendControl(value)
        elif offset == self.BLDALPHA:
            value &= 0x1f1f
            self.video.renderPath.writeBlendAlpha(value)
        elif offset == self.BLDY:
            value &= 0x001f
            self.video.renderPath.writeBlendY(value)
        elif offset == self.MOSAIC:
            self.video.renderPath.writeMosaic(value)
        elif offset == self.SOUND1CNT_LO:
            value &= 0x007f
            self.audio.writeSquareChannelSweep(0, value)
        elif offset == self.SOUND1CNT_HI:
            self.audio.writeSquareChannelDLE(0, value)
        elif offset == self.SOUND1CNT_X:
            value &= 0xc7ff
            self.audio.writeSquareChannelFC(0, value)
            value &= ~0x8000
        elif offset == self.SOUND2CNT_LO:
            self.audio.writeSquareChannelDLE(1, value)
        elif offset == self.SOUND2CNT_HI:
            value &= 0xc7ff
            self.audio.writeSquareChannelFC(1, value)
            value &= ~0x8000
        elif offset == self.SOUND3CNT_LO:
            value &= 0x00e0
            self.audio.writeChannel3Lo(value)
        elif offset == self.SOUND3CNT_HI:
            value &= 0xe0ff
            self.audio.writeChannel3Hi(value)
        elif offset == self.SOUND3CNT_X:
            value &= 0xc7ff
            self.audio.writeChannel3X(value)
            value &= ~0x8000
        elif offset == self.SOUND4CNT_LO:
            value &= 0xff3f
            self.audio.writeChannel4LE(value)
        elif offset == self.SOUND4CNT_HI:
            value &= 0xc0ff
            self.audio.writeChannel4FC(value)
            value &= ~0x8000
        elif offset == self.SOUNDCNT_LO:
            value &= 0xff77
            self.audio.writeSoundControlLo(value)
        elif offset == self.SOUNDCNT_HI:
            value &= 0xff0f
            self.audio.writeSoundControlHi(value)
        elif offset == self.SOUNDCNT_X:
            value &= 0x0080
            self.audio.writeEnable(value)
        elif offset in [self.WAVE_RAM0_LO, self.WAVE_RAM0_HI, self.WAVE_RAM1_LO, self.WAVE_RAM1_HI,
                        self.WAVE_RAM2_LO, self.WAVE_RAM2_HI, self.WAVE_RAM3_LO, self.WAVE_RAM3_HI]:
            self.audio.writeWaveData(offset - self.WAVE_RAM0_LO, value, 2)
        elif offset in [self.DMA0SAD_LO, self.DMA0DAD_LO, self.DMA1SAD_LO, self.DMA1DAD_LO,
                        self.DMA2SAD_LO, self.DMA2DAD_LO, self.DMA3SAD_LO, self.DMA3DAD_LO]:
            self.store32(offset, (self.registers[(offset >> 1) + 1] << 16) | value)
            return
        elif offset in [self.DMA0SAD_HI, self.DMA0DAD_HI, self.DMA1SAD_HI, self.DMA1DAD_HI,
                        self.DMA2SAD_HI, self.DMA2DAD_HI, self.DMA3SAD_HI, self.DMA3DAD_HI]:
            self.store32(offset - 2, self.registers[(offset >> 1) - 1] | (value << 16))
            return
        elif offset == self.DMA0CNT_LO:
            self.cpu.irq.dmaSetWordCount(0, value)
        elif offset == self.DMA0CNT_HI:
            self.registers[offset >> 1] = value & 0xffe0
            self.cpu.irq.dmaWriteControl(0, value)
            return
        elif offset == self.DMA1CNT_LO:
            self.cpu.irq.dmaSetWordCount(1, value)
        elif offset == self.DMA1CNT_HI:
            self.registers[offset >> 1] = value & 0xffe0
            self.cpu.irq.dmaWriteControl(1, value)
            return
        elif offset == self.DMA2CNT_LO:
            self.cpu.irq.dmaSetWordCount(2, value)
        elif offset == self.DMA2CNT_HI:
            self.registers[offset >> 1] = value & 0xffe0
            self.cpu.irq.dmaWriteControl(2, value)
            return
        elif offset == self.DMA3CNT_LO:
            self.cpu.irq.dmaSetWordCount(3, value)
        elif offset == self.DMA3CNT_HI:
            self.registers[offset >> 1] = value & 0xffe0
            self.cpu.irq.dmaWriteControl(3, value)
            return
        elif offset in [self.TM0CNT_LO, self.TM1CNT_LO, self.TM2CNT_LO, self.TM3CNT_LO]:
            self.cpu.irq.timerSetReload(offset // 4, value)
            return
        elif offset in [self.TM0CNT_HI, self.TM1CNT_HI, self.TM2CNT_HI, self.TM3CNT_HI]:
            value &= 0x00c7
            self.cpu.irq.timerWriteControl(offset // 4, value)
        elif offset in [self.SIOMULTI0, self.SIOMULTI1, self.SIOMULTI2, self.SIOMULTI3, self.SIODATA8]:
            self.STUB_REG("SIO", offset)
        elif offset == self.RCNT:
            self.sio.setMode(((value >> 12) & 0xc) | ((self.registers[self.SIOCNT >> 1] >> 12) & 0x3))
            self.sio.writeRCNT(value)
        elif offset == self.SIOCNT:
            self.sio.setMode(((value >> 12) & 0x3) | ((self.registers[self.RCNT >> 1] >> 12) & 0xc))
            self.sio.writeSIOCNT(value)
            return
        elif offset in [self.JOYCNT, self.JOYSTAT]:
            self.STUB_REG("JOY", offset)
            return
        elif offset in [self.IE, self.IF]:
            self.STUB_REG("JOY", offset)
            return
        elif offset == self.WAITCNT:
            value &= 0xdfff
            self.cpu.mmu.adjustTimings(value)
        elif offset == self.IME:
            value &= 0x0001
            self.cpu.irq.masterEnable(value)
        else:
            self.STUB_REG("I/O", offset)
        self.registers[offset >> 1] = value

    def store32(self, offset, value):
        if offset == self.BG2X_LO:
            value &= 0x0fffffff
            self.video.renderPath.writeBackgroundRefX(2, value)
        elif offset == self.BG2Y_LO:
            value &= 0x0fffffff
            self.video.renderPath.writeBackgroundRefY(2, value)
        elif offset == self.BG3X_LO:
            value &= 0x0fffffff
            self.video.renderPath.writeBackgroundRefX(3, value)
        elif offset == self.BG3Y_LO:
            value &= 0x0fffffff
            self.video.renderPath.writeBackgroundRefY(3, value)
        elif offset in [self.DMA0SAD_LO, self.DMA0DAD_LO, self.DMA1SAD_LO, self.DMA1DAD_LO,
                        self.DMA2SAD_LO, self.DMA2DAD_LO, self.DMA3SAD_LO, self.DMA3DAD_LO]:
            self.store32(offset, (self.registers[(offset >> 1) + 1] << 16) | value)
            return
        elif offset in [self.DMA0SAD_HI, self.DMA0DAD_HI, self.DMA1SAD_HI, self.DMA1DAD_HI,
                        self.DMA2SAD_HI, self.DMA2DAD_HI, self.DMA3SAD_HI, self.DMA3DAD_HI]:
            self.store32(offset - 2, self.registers[(offset >> 1) - 1] | (value << 16))
            return
        elif offset == self.DMA0CNT_LO:
            self.cpu.irq.dmaSetWordCount(0, value)
        elif offset == self.DMA0CNT_HI:
            self.registers[offset >> 1] = value & 0xffe0
            self.cpu.irq.dmaWriteControl(0, value)
            return
        elif offset == self.DMA1CNT_LO:
            self.cpu.irq.dmaSetWordCount(1, value)
        elif offset == self.DMA1CNT_HI:
            self.registers[offset >> 1] = value & 0xffe0
            self.cpu.irq.dmaWriteControl(1, value)
            return
        elif offset == self.DMA2CNT_LO:
            self.cpu.irq.dmaSetWordCount(2, value)
        elif offset == self.DMA2CNT_HI:
            self.registers[offset >> 1] = value & 0xffe0
            self.cpu.irq.dmaWriteControl(2, value)
            return
        elif offset == self.DMA3CNT_LO:
            self.cpu.irq.dmaSetWordCount(3, value)
        elif offset == self.DMA3CNT_HI:
            self.registers[offset >> 1] = value & 0xffe0
            self.cpu.irq.dmaWriteControl(3, value)
            return
        elif offset in [self.TM0CNT_LO, self.TM1CNT_LO, self.TM2CNT_LO, self.TM3CNT_LO]:
            self.cpu.irq.timerSetReload(offset // 4, value)
            return
        elif offset in [self.TM0CNT_HI, self.TM1CNT_HI, self.TM2CNT_HI, self.TM3CNT_HI]:
            value &= 0x00c7
            self.cpu.irq.timerWriteControl(offset // 4, value)
        elif offset in [self.SIOMULTI0, self.SIOMULTI1, self.SIOMULTI2, self.SIOMULTI3, self.SIODATA8]:
            self.STUB_REG("SIO", offset)
        elif offset == self.RCNT:
            self.sio.setMode(((value >> 12) & 0xc) | ((self.registers[self.SIOCNT >> 1] >> 12) & 0x3))
            self.sio.writeRCNT(value)
        elif offset == self.SIOCNT:
            self.sio.setMode(((value >> 12) & 0x3) | ((self.registers[self.RCNT >> 1] >> 12) & 0xc))
            self.sio.writeSIOCNT(value)
            return
        elif offset in [self.JOYCNT, self.JOYSTAT]:
            self.STUB_REG("JOY", offset)
            return
        elif offset in [self.IE, self.IF]:
            self.STUB_REG("JOY", offset)
            return
        elif offset == self.WAITCNT:
            value &= 0xdfff
            self.cpu.mmu.adjustTimings(value)
        elif offset == self.IME:
            value &= 0x0001
            self.cpu.irq.masterEnable(value)
        else:
            self.STUB_REG("I/O", offset)
        self.registers[offset >> 1] = value & 0xffff
        self.registers[(offset >> 1) + 1] = value >> 16

    def invalidatePage(self, address):
        pass

    def STUB_REG(self, type, offset):
        self.core.STUB("Unimplemented " + type + " register write: " + hex(offset))