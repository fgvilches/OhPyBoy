import numpy as np
import sounddevice as sd

class GameBoyAdvanceAudio:
    def __init__(self, cpu):
        self.cpu = cpu
        self.core = cpu
        self.sampleInterval = 0.0000625  # 1 / 16000
        self.bufferSize = 4096
        self.maxSamples = self.bufferSize << 2
        self.resampleRatio = 1.0 
        self.buffers = [
            np.zeros(self.maxSamples),
            np.zeros(self.maxSamples)
        ]
        self.sampleMask = self.maxSamples - 1
        self.jsAudio = sd.OutputStream(
            samplerate=32768,
            channels=2,
            callback=self.audioProcess,
            blocksize=self.bufferSize
        )
        self.masterEnable = True
        self.masterVolume = 1.0
        self.SOUND_MAX = 0x400
        self.FIFO_MAX = 0x200
        self.PSG_MAX = 0x080
        self.clear()

    def clear(self):
        self.fifoA = []
        self.fifoB = []
        self.fifoASample = 0
        self.fifoBSample = 0
        self.enabled = False
        self.enableChannel3 = False
        self.enableChannel4 = False
        self.enableChannelA = False
        self.enableChannelB = False
        self.enableRightChannelA = False
        self.enableLeftChannelA = False
        self.enableRightChannelB = False
        self.enableLeftChannelB = False
        self.playingChannel3 = False
        self.playingChannel4 = False
        self.volumeLeft = 0
        self.volumeRight = 0
        self.ratioChannelA = 1
        self.ratioChannelB = 1
        self.enabledLeft = 0
        self.enabledRight = 0
        self.dmaA = -1
        self.dmaB = -1
        self.soundTimerA = 0
        self.soundTimerB = 0
        self.soundRatio = 1
        self.soundBias = 0x200
        self.squareChannels = [
            {
                "enabled": False,
                "playing": False,
                "sample": 0,
                "duty": 0.5,
                "increment": 0,
                "step": 0,
                "initialVolume": 60,
                "volume": 60,
                "frequency": 0,
                "interval": 0,
                "sweepSteps": 0,
                "sweepIncrement": 0,
                "sweepInterval": 0,
                "doSweep": False,
                "raise": 0,
                "lower": 0,
                "nextStep": 0,
                "timed": False,
                "length": 0,
                "end": 0
            }
            for _ in range(2)
        ]
        self.waveData = np.zeros(32, dtype=np.uint8)
        self.channel3Dimension = 0
        self.channel3Bank = 0
        self.channel3Volume = 0
        self.channel3Interval = 0
        self.channel3Next = 0
        self.channel3Length = 0
        self.channel3Timed = False
        self.channel3End = 0
        self.channel3Pointer = 0
        self.channel3Sample = 0
        self.cpuFrequency = 0
        self.channel4 = {
            "sample": 0,
            "lfsr": 0,
            "width": 15,
            "interval": 0,
            "increment": 0,
            "step": 0,
            "initialVolume": 60,
            "volume": 60,
            "nextStep": 0,
            "timed": False,
            "length": 0,
            "end": 0
        }
        self.nextEvent = 0
        self.nextSample = 0
        self.outputPointer = 0
        self.samplePointer = 0
        self.backup = 0
        self.totalSamples = 0
        self.jsAudio.start()

    def freeze(self):
        return {
            "nextSample": self.nextSample
        }

    def defrost(self, frost):
        self.nextSample = frost["nextSample"]

    def pause(self, paused):
        if paused:
            self.jsAudio.stop()
        else:
            self.jsAudio.start()

    def updateTimers(self):
        cycles = self.cpu.cycles
        if not self.enabled or (cycles < self.nextEvent and cycles < self.nextSample):
            return

        if cycles >= self.nextEvent:
            channel = self.squareChannels[0]
            self.nextEvent = float("inf")
            if channel["playing"]:
                self.updateSquareChannel(channel, cycles)

            channel = self.squareChannels[1]
            if channel["playing"]:
                self.updateSquareChannel(channel, cycles)

            if self.enableChannel3 and self.playingChannel3:
                if cycles >= self.channel3Next:
                    if self.channel3Write:
                        sample = self.waveData[self.channel3Pointer >> 1]
                        self.channel3Sample = (((sample >> ((self.channel3Pointer & 1) << 2)) & 0xF) - 0x8) / 8
                        self.channel3Pointer = (self.channel3Pointer + 1)
                        if self.channel3Dimension and self.channel3Pointer >= 64:
                            self.channel3Pointer -= 64
                        elif not self.channel3Bank and self.channel3Pointer >= 32:
                            self.channel3Pointer -= 32
                        elif self.channel3Pointer >= 64:
                            self.channel3Pointer -= 32
                    self.channel3Next += self.channel3Interval
                    if self.channel3Interval and self.nextEvent > self.channel3Next:
                        self.nextEvent = self.channel3Next

                if self.channel3Timed and cycles >= self.channel3End:
                    self.playingChannel3 = False

            if self.enableChannel4 and self.playingChannel4:
                if self.channel4["timed"] and cycles >= self.channel4["end"]:
                    self.playingChannel4 = False
                else:
                    if cycles >= self.channel4["next"]:
                        self.channel4["lfsr"] >>= 1
                        sample = self.channel4["lfsr"] & 1
                        self.channel4["lfsr"] |= (((self.channel4["lfsr"] >> 1) & 1) ^ sample) << (self.channel4["width"] - 1)
                        self.channel4["next"] += self.channel4["interval"]
                        self.channel4["sample"] = (sample - 0.5) * 2 * self.channel4["volume"]

                    self.updateEnvelope(self.channel4, cycles)

                    if self.nextEvent > self.channel4["next"]:
                        self.nextEvent = self.channel4["next"]

                    if self.channel4["timed"] and self.nextEvent > self.channel4["end"]:
                        self.nextEvent = self.channel4["end"]

        if cycles >= self.nextSample:
            self.sample()
            self.nextSample += self.sampleInterval

        self.nextEvent = np.ceil(self.nextEvent)
        if self.nextEvent < cycles or self.nextSample < cycles:
            self.updateTimers()

    def writeEnable(self, value):
        self.enabled = bool(value)
        self.nextEvent = self.cpu.cycles
        self.nextSample = self.nextEvent
        self.updateTimers()
        self.core.irq.pollNextEvent()

    def writeSoundControlLo(self, value):
        #print(value, type(value))
        #alue = int(value, 16)  # Convert hex string to integer
        self.masterVolumeLeft = value & 0x7
        self.masterVolumeRight = (value >> 4) & 0x7
        self.enabledLeft = (value >> 8) & 0xf
        self.enabledRight = (value >> 12) & 0xf

        self.setSquareChannelEnabled(
            self.squareChannels[0],
            (self.enabledLeft | self.enabledRight) & 0x1
        )
        self.setSquareChannelEnabled(
            self.squareChannels[1],
            (self.enabledLeft | self.enabledRight) & 0x2
        )
        self.enableChannel3 = bool((self.enabledLeft | self.enabledRight) & 0x4)
        self.setChannel4Enabled(bool((self.enabledLeft | self.enabledRight) & 0x8))

        self.updateTimers()
        self.core.irq.pollNextEvent()

    def writeSoundControlHi(self, value):
        #value = int(value, 16)  # Convert hex string to integer

        if value & 0x0003 == 0:
            self.soundRatio = 0.25
        elif value & 0x0003 == 1:
            self.soundRatio = 0.50
        elif value & 0x0003 == 2:
            self.soundRatio = 1

        self.ratioChannelA = (((value & 0x0004) >> 2) + 1) * 0.5
        self.ratioChannelB = (((value & 0x0008) >> 3) + 1) * 0.5

        self.enableRightChannelA = bool(value & 0x0100)
        self.enableLeftChannelA = bool(value & 0x0200)
        self.enableChannelA = bool(value & 0x0300)
        self.soundTimerA = bool(value & 0x0400)
        if value & 0x0800:
            self.fifoA = []

        self.enableRightChannelB = bool(value & 0x1000)
        self.enableLeftChannelB = bool(value & 0x2000)
        self.enableChannelB = bool(value & 0x3000)
        self.soundTimerB = bool(value & 0x4000)
        if value & 0x8000:
            self.fifoB = []

    def resetSquareChannel(self, channel):
        if channel["step"]:
            channel["nextStep"] = self.cpu.cycles + channel["step"]

        if channel["enabled"] and not channel["playing"]:
            channel["raise"] = self.cpu.cycles
            channel["lower"] = channel["raise"] + channel["duty"] * channel["interval"]
            channel["end"] = self.cpu.cycles + channel["length"]
            self.nextEvent = self.cpu.cycles

        channel["playing"] = channel["enabled"]
        self.updateTimers()
        self.core.irq.pollNextEvent()

    def setSquareChannelEnabled(self, channel, enable):
        if not (channel["enabled"] and channel["playing"]) and enable:
            channel["enabled"] = bool(enable)
            self.updateTimers()
            self.core.irq.pollNextEvent()
        else:
            channel["enabled"] = bool(enable)

    def writeSquareChannelSweep(self, channelId, value):
        channel = self.squareChannels[channelId]
        channel["sweepSteps"] = value & 0x07
        channel["sweepIncrement"] = -1 if value & 0x08 else 1
        channel["sweepInterval"] = ((value >> 4) & 0x7) * self.cpuFrequency / 128
        channel["doSweep"] = bool(channel["sweepInterval"])
        channel["nextSweep"] = self.cpu.cycles + channel["sweepInterval"]
        self.resetSquareChannel(channel)

    def writeSquareChannelDLE(self, channelId, value):
        channel = self.squareChannels[channelId]
        duty = (value >> 6) & 0x3
        if duty == 0:
            channel["duty"] = 0.125
        elif duty == 1:
            channel["duty"] = 0.25
        elif duty == 2:
            channel["duty"] = 0.5
        elif duty == 3:
            channel["duty"] = 0.75
        self.writeChannelLE(channel, value)
        self.resetSquareChannel(channel)

    def writeSquareChannelFC(self, channelId, value):
        channel = self.squareChannels[channelId]
        frequency = value & 2047
        channel["frequency"] = frequency
        channel["interval"] = (self.cpuFrequency * (2048 - frequency)) / 131072
        channel["timed"] = bool(value & 0x4000)

        if value & 0x8000:
            self.resetSquareChannel(channel)
            channel["volume"] = channel["initialVolume"]

    def updateSquareChannel(self, channel, cycles):
        if channel["timed"] and cycles >= channel["end"]:
            channel["playing"] = False
            return

        if channel["doSweep"] and cycles >= channel["nextSweep"]:
            channel["frequency"] += channel["sweepIncrement"] * (channel["frequency"] >> channel["sweepSteps"])
            if channel["frequency"] < 0:
                channel["frequency"] = 0
            elif channel["frequency"] > 2047:
                channel["frequency"] = 2047
                channel["playing"] = False
                return
            channel["interval"] = (self.cpuFrequency * (2048 - channel["frequency"])) / 131072
            channel["nextSweep"] += channel["sweepInterval"]

        if cycles >= channel["raise"]:
            channel["sample"] = channel["volume"]
            channel["lower"] = channel["raise"] + channel["duty"] * channel["interval"]
            channel["raise"] += channel["interval"]
        elif cycles >= channel["lower"]:
            channel["sample"] = -channel["volume"]
            channel["lower"] += channel["interval"]

        self.updateEnvelope(channel, cycles)

        if self.nextEvent > channel["raise"]:
            self.nextEvent = channel["raise"]

        if self.nextEvent > channel["lower"]:
            self.nextEvent = channel["lower"]

        if channel["timed"] and self.nextEvent > channel["end"]:
            self.nextEvent = channel["end"]

        if channel["doSweep"] and self.nextEvent > channel["nextSweep"]:
            self.nextEvent = channel["nextSweep"]

    def writeChannel3Lo(self, value):
        self.channel3Dimension = value & 0x20
        self.channel3Bank = value & 0x40
        enable = value & 0x80
        if not self.channel3Write and enable:
            self.channel3Write = enable
            self.resetChannel3()
        else:
            self.channel3Write = enable

    def writeChannel3Hi(self, value):
        self.channel3Length = (self.cpuFrequency * (0x100 - (value & 0xff))) / 256
        volume = (value >> 13) & 0x7
        if volume == 0:
            self.channel3Volume = 0
        elif volume == 1:
            self.channel3Volume = 1
        elif volume == 2:
            self.channel3Volume = 0.5
        elif volume == 3:
            self.channel3Volume = 0.25
        else:
            self.channel3Volume = 0.75

    def writeChannel3X(self, value):
        self.channel3Interval = (self.cpuFrequency * (2048 - (value & 0x7ff))) / 2097152
        self.channel3Timed = bool(value & 0x4000)
        if self.channel3Write:
            self.resetChannel3()

    def resetChannel3(self):
        self.channel3Next = self.cpu.cycles
        self.nextEvent = self.channel3Next
        self.channel3End = self.cpu.cycles + self.channel3Length
        self.playingChannel3 = self.channel3Write
        self.updateTimers()
        self.core.irq.pollNextEvent()

    def writeWaveData(self, offset, data, width):
        if not self.channel3Bank:
            offset += 16
        if width == 2:
            self.waveData[offset] = data & 0xff
            data >>= 8
            offset += 1
        self.waveData[offset] = data & 0xff

    def setChannel4Enabled(self, enable):
        if not self.enableChannel4 and enable:
            self.channel4["next"] = self.cpu.cycles
            self.channel4["end"] = self.cpu.cycles + self.channel4["length"]
            self.enableChannel4 = True
            self.playingChannel4 = True
            self.nextEvent = self.cpu.cycles
            self.updateEnvelope(self.channel4, self.nextEvent)
            self.updateTimers()
            self.core.irq.pollNextEvent()
        else:
            self.enableChannel4 = enable

    def writeChannel4LE(self, value):
        self.writeChannelLE(self.channel4, value)
        self.resetChannel4()

    def writeChannel4FC(self, value):
        self.channel4["timed"] = bool(value & 0x4000)

        r = value & 0x7
        if not r:
            r = 0.5
        s = (value >> 4) & 0xf
        interval = (self.cpuFrequency * (r * (2 << s))) / 524288
        if interval != self.channel4["interval"]:
            self.channel4["interval"] = interval
            self.resetChannel4()

        width = 7 if value & 0x8 else 15
        if width != self.channel4["width"]:
            self.channel4["width"] = width
            self.resetChannel4()

        if value & 0x8000:
            self.resetChannel4()

    def resetChannel4(self):
        if self.channel4["width"] == 15:
            self.channel4["lfsr"] = 0x4000
        else:
            self.channel4["lfsr"] = 0x40
        self.channel4["volume"] = self.channel4["initialVolume"]
        if self.channel4["step"]:
            self.channel4["nextStep"] = self.cpu.cycles + self.channel4["step"]
        self.channel4["end"] = self.cpu.cycles + self.channel4["length"]
        self.channel4["next"] = self.cpu.cycles
        self.nextEvent = self.channel4["next"]
        self.playingChannel4 = self.enableChannel4
        self.updateTimers()
        self.core.irq.pollNextEvent()

    def writeChannelLE(self, channel, value):
        channel["length"] = self.cpuFrequency * ((0x40 - (value & 0x3f)) / 256)
        channel["increment"] = 1 / 16 if value & 0x0800 else -1 / 16
        channel["initialVolume"] = ((value >> 12) & 0xf) / 16
        channel["step"] = self.cpuFrequency * (((value >> 8) & 0x7) / 64)

    def updateEnvelope(self, channel, cycles):
        if channel["step"]:
            if cycles >= channel["nextStep"]:
                channel["volume"] += channel["increment"]
                if channel["volume"] > 1:
                    channel["volume"] = 1
                elif channel["volume"] < 0:
                    channel["volume"] = 0
                channel["nextStep"] += channel["step"]

            if self.nextEvent > channel["nextStep"]:
                self.nextEvent = channel["nextStep"]

    def appendToFifoA(self, value):
        if len(self.fifoA) > 28:
            self.fifoA = self.fifoA[-28:]
        for _ in range(4):
            b = (value & 0xff) << 24
            value >>= 8
            self.fifoA.append(b / 0x80000000)

    def appendToFifoB(self, value):
        if len(self.fifoB) > 28:
            self.fifoB = self.fifoB[-28:]
        for _ in range(4):
            b = (value & 0xff) << 24
            value >>= 8
            self.fifoB.append(b / 0x80000000)

    def sampleFifoA(self):
        if len(self.fifoA) <= 16:
            dma = self.core.irq.dma[self.dmaA]
            dma.nextCount = 4
            self.core.mmu.serviceDma(self.dmaA, dma)
        self.fifoASample = self.fifoA.pop(0)

    def sampleFifoB(self):
        if len(self.fifoB) <= 16:
            dma = self.core.irq.dma[self.dmaB]
            dma.nextCount = 4
            self.core.mmu.serviceDma(self.dmaB, dma)
        self.fifoBSample = self.fifoB.pop(0)

    def scheduleFIFODma(self, number, info):
        if info.dest == self.cpu.mmu.BASE_IO | self.cpu.irq.io.FIFO_A_LO:
            info.dstControl = 2
            self.dmaA = number
        elif info.dest == self.cpu.mmu.BASE_IO | self.cpu.irq.io.FIFO_B_LO:
            info.dstControl = 2
            self.dmaB = number
        else:
            self.core.WARN("Tried to schedule FIFO DMA for non-FIFO destination")

    def sample(self):
        sampleLeft = 0
        sampleRight = 0
        sample = 0
        channel = None

        channel = self.squareChannels[0]
        if channel["playing"]:
            sample = channel["sample"] * self.soundRatio * self.PSG_MAX
            if self.enabledLeft & 0x1:
                sampleLeft += sample
            if self.enabledRight & 0x1:
                sampleRight += sample

        channel = self.squareChannels[1]
        if channel["playing"]:
            sample = channel["sample"] * self.soundRatio * self.PSG_MAX
            if self.enabledLeft & 0x2:
                sampleLeft += sample
            if self.enabledRight & 0x2:
                sampleRight += sample

        if self.playingChannel3:
            sample = self.channel3Sample * self.soundRatio * self.channel3Volume * self.PSG_MAX
            if self.enabledLeft & 0x4:
                sampleLeft += sample
            if self.enabledRight & 0x4:
                sampleRight += sample

        if self.playingChannel4:
            sample = self.channel4["sample"] * self.soundRatio * self.PSG_MAX
            if self.enabledLeft & 0x8:
                sampleLeft += sample
            if self.enabledRight & 0x8:
                sampleRight += sample

        if self.enableChannelA:
            sample = self.fifoASample * self.FIFO_MAX * self.ratioChannelA
            if self.enableLeftChannelA:
                sampleLeft += sample
            if self.enableRightChannelA:
                sampleRight += sample

        if self.enableChannelB:
            sample = self.fifoBSample * self.FIFO_MAX * self.ratioChannelB
            if self.enableLeftChannelB:
                sampleLeft += sample
            if self.enableRightChannelB:
                sampleRight += sample

        samplePointer = self.samplePointer
        sampleLeft *= self.masterVolume / self.SOUND_MAX
        sampleLeft = max(min(sampleLeft, 1), -1)
        sampleRight *= self.masterVolume / self.SOUND_MAX
        sampleRight = max(min(sampleRight, 1), -1)
        if self.buffers:
            self.buffers[0][samplePointer] = sampleLeft
            self.buffers[1][samplePointer] = sampleRight
        self.samplePointer = (samplePointer + 1) & self.sampleMask

    def audioProcess(self, outdata, frames, time, status):
        if self.masterEnable:
            i = 0
            o = self.outputPointer
            while i < frames:
                if o >= self.maxSamples:
                    o -= self.maxSamples
                if int(o) == self.samplePointer:
                    self.backup += 1
                    break
                outdata[i, 0] = self.buffers[0][int(o)]
                outdata[i, 1] = self.buffers[1][int(o)]
                i += 1
                o += self.resampleRatio
            while i < frames:
                outdata[i, 0] = 0
                outdata[i, 1] = 0
                i += 1
            self.outputPointer = o
            self.totalSamples += frames
        else:
            outdata[:, 0] = 0
            outdata[:, 1] = 0

    def writeSoundFIFO(self, value):
        if len(self.fifoA) < self.FIFO_MAX:
            self.fifoA.append(value)
        elif len(self.fifoB) < self.FIFO_MAX:
            self.fifoB.append(value)
        else:
            # FIFO is full, handle overflow or error condition
            pass