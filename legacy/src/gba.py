from core import ARMCore
from mmu import GameBoyAdvanceMMU
from irq import GameBoyAdvanceInterruptHandler
from gbio import GameBoyAdvanceIO
from audio import GameBoyAdvanceAudio
from video import GameBoyAdvanceVideo
#from keypad import GameBoyAdvanceKeypad
from sio import GameBoyAdvanceSIO
class GameBoyAdvance:
    def __init__(self):
        self.LOG_ERROR = 1
        self.LOG_WARN = 2
        self.LOG_STUB = 4
        self.LOG_INFO = 8
        self.LOG_DEBUG = 16

        self.SYS_ID = "com.fgvilches.gbapy"

        self.logLevel = self.LOG_ERROR | self.LOG_WARN

        self.rom = None

        self.cpu = ARMCore()
        self.cycles = self.cpu.cycles
        self.mmu = GameBoyAdvanceMMU()
        self.irq = GameBoyAdvanceInterruptHandler()
        self.io = GameBoyAdvanceIO()
        self.audio = GameBoyAdvanceAudio(self.cpu)
        self.video = GameBoyAdvanceVideo()
        #self.keypad = GameBoyAdvanceKeypad()
        #self.sio = GameBoyAdvanceSIO()

        # TODO: simplify this graph
        self.cpu.mmu = self.mmu
        self.cpu.irq = self.irq

        self.mmu.cpu = self.cpu
        self.mmu.core = self

        self.irq.cpu = self.cpu
        self.irq.io = self.io
        self.irq.audio = self.audio
        self.irq.video = self.video
        self.irq.core = self

        self.io.cpu = self.cpu
        self.io.audio = self.audio
        self.io.video = self.video
        #self.io.keypad = self.keypad
        #self.io.sio = self.sio
        self.io.core = self

        self.audio.cpu = self.cpu
        self.audio.core = self

        self.video.cpu = self.cpu
        self.video.core = self

        #self.keypad.core = self

        #self.sio.core = self

        #self.keypad.registerHandlers()
        self.doStep = self.waitFrame
        self.paused = False

        self.seenFrame = False
        self.seenSave = False
        self.lastVblank = 0

        self.queue = None
        self.reportFPS = None
        self.throttle = 16  # This is rough, but the 2/3ms difference gives us a good overhead

    def queueFrame(f):
        self.queue = window.setTimeout(f, self.throttle)

        window.queueFrame = queueFrame

        window.URL = window.URL or window.webkitURL
        def handle_vblank():
            self.seenFrame = True

            self.video.vblankCallback = handle_vblank


    def setCanvas(self, canvas):
        if canvas.offsetWidth != 240 or canvas.offsetHeight != 160:
            self.indirectCanvas = document.createElement("canvas")
            self.indirectCanvas.setAttribute("height", "160")
            self.indirectCanvas.setAttribute("width", "240")
            self.targetCanvas = canvas
            self.setCanvasDirect(self.indirectCanvas)
            targetContext = canvas.getContext("2d")
            self.video.drawCallback = lambda: targetContext.drawImage(
                self.indirectCanvas,
                0,
                0,
                canvas.width,
                canvas.height
            )
        else:
            self.setCanvasDirect(canvas)

    def setCanvasDirect(self, canvas):
        self.context = canvas.getContext("2d")
        self.video.setBacking(self.context)

    def setBios(self, bios, real):
        self.mmu.loadBios(bios, real)

    def setRom(self, rom):
        self.reset()

        self.rom = self.mmu.loadRom(rom, True)
        if not self.rom:
            return False
        self.retrieveSavedata()
        return True

    def hasRom(self):
        return bool(self.rom)

    def loadRomFromFile(self, romFile, callback):
        reader = FileReader()
        reader.onload = lambda e: callback(self.setRom(e.target.result))
        reader.readAsArrayBuffer(romFile)

    def reset(self):
        self.audio.pause(True)

        self.mmu.clear()
        self.io.clear()
        self.audio.clear()
        self.video.clear()
        self.sio.clear()

        self.mmu.mmap(self.mmu.REGION_IO, self.io)
        self.mmu.mmap(self.mmu.REGION_PALETTE_RAM, self.video.renderPath.palette)
        self.mmu.mmap(self.mmu.REGION_VRAM, self.video.renderPath.vram)
        self.mmu.mmap(self.mmu.REGION_OAM, self.video.renderPath.oam)

        self.cpu.resetCPU(0)

    def step(self):
        while self.doStep():
            self.cpu.step()

    def waitFrame(self):
        seen = self.seenFrame
        self.seenFrame = False
        return not seen

    def pause(self):
        self.paused = True
        self.audio.pause(True)
        if self.queue:
            clearTimeout(self.queue)
            self.queue = None

    def advanceFrame(self):
        self.step()
        if self.seenSave:
            if not self.mmu.saveNeedsFlush():
                self.storeSavedata()
                self.seenSave = False
            else:
                self.mmu.flushSave()
        elif self.mmu.saveNeedsFlush():
            self.seenSave = True
            self.mmu.flushSave()

    def runStable(self):
        if self.interval:
            return  # Already running
        timer = 0
        frames = 0
        start = Date.now()
        self.paused = False
        self.audio.pause(False)

        def runFunc():
            nonlocal timer, frames, start
            try:
                timer += Date.now() - start
                if self.paused:
                    return
                else:
                    queueFrame(runFunc)
                start = Date.now()
                self.advanceFrame()
                frames += 1
                if frames == 60:
                    self.reportFPS((frames * 1000) / timer)
                    frames = 0
                    timer = 0
            except Exception as exception:
                self.ERROR(exception)
                if hasattr(exception, "stack"):
                    self.logStackTrace(exception.stack.split("\n"))
                raise exception

        queueFrame(runFunc)

    def setSavedata(self, data):
        self.mmu.loadSavedata(data)

    def loadSavedataFromFile(self, saveFile):
        reader = FileReader()
        reader.onload = lambda e: self.setSavedata(e.target.result)
        reader.readAsArrayBuffer(saveFile)

    def decodeSavedata(self, string):
        self.setSavedata(self.decodeBase64(string))

    def decodeBase64(self, string):
        length = (len(string) * 3) // 4
        if string[-2] == "=":
            length -= 2
        elif string[-1] == "=":
            length -= 1
        buffer = ArrayBuffer(length)
        view = Uint8Array(buffer)
        bits = re.findall(r"....", string)
        for i in range(0, length, 3):
            s = atob(bits.pop(0))
            view[i] = ord(s[0])
            view[i + 1] = ord(s[1])
            view[i + 2] = ord(s[2])
        if i < length:
            s = atob(bits.pop(0))
            view[i] = ord(s[0])
            if len(s) > 1:
                view[i + 1] = ord(s[1])

        return buffer

    def encodeBase64(self, view):
        data = []
        wordstring = []
        for i in range(view.byteLength):
            b = view.getUint8(i, True)
            wordstring.append(chr(b))
            while len(wordstring) >= 3:
                triplet = wordstring[:3]
                wordstring = wordstring[3:]
                data.append(btoa("".join(triplet)))
        if wordstring:
            data.append(btoa("".join(wordstring)))

        return "".join(data)

    def downloadSavedata(self):
        sram = self.mmu.save
        if not sram:
            self.WARN("No save data available")
            return None
        if window.URL:
            url = window.URL.createObjectURL(
                Blob([sram.buffer], {"type": "application/octet-stream"})
            )
            window.open(url)
        else:
            data = self.encodeBase64(sram.view)
            window.open(
                "data:application/octet-stream;base64," + data,
                self.rom.code + ".sav"
            )

    def storeSavedata(self):
        sram = self.mmu.save
        try:
            storage = window.localStorage
            storage[self.SYS_ID + "." + self.mmu.cart.code] = self.encodeBase64(
                sram.view
            )
        except Exception as e:
            self.WARN("Could not store savedata! " + str(e))

    def retrieveSavedata(self):
        try:
            storage = window.localStorage
            data = storage[self.SYS_ID + "." + self.mmu.cart.code]
            if data:
                self.decodeSavedata(data)
                return True
        except Exception as e:
            self.WARN("Could not retrieve savedata! " + str(e))
        return False

    def freeze(self):
        return {
            "cpu": self.cpu.freeze(),
            "mmu": self.mmu.freeze(),
            "irq": self.irq.freeze(),
            "io": self.io.freeze(),
            "audio": self.audio.freeze(),
            "video": self.video.freeze()
        }

    def defrost(self, frost):
        self.cpu.defrost(frost["cpu"])
        self.mmu.defrost(frost["mmu"])
        self.audio.defrost(frost["audio"])
        self.video.defrost(frost["video"])
        self.irq.defrost(frost["irq"])
        self.io.defrost(frost["io"])

    def log(self, level, message):
        pass

    def setLogger(self, logger):
        self.log = logger

    def logStackTrace(self, stack):
        overflow = len(stack) - 32
        self.ERROR("Stack trace follows:")
        if overflow > 0:
            self.log(-1, "> (Too many frames)")
        for frame in stack[max(overflow, 0):]:
            self.log(-1, "> " + frame)

    def ERROR(self, error):
        if self.logLevel & self.LOG_ERROR:
            self.log(self.LOG_ERROR, error)

    def WARN(self, warn):
        if self.logLevel & self.LOG_WARN:
            self.log(self.LOG_WARN, warn)

    def STUB(self, func):
        if self.logLevel & self.LOG_STUB:
            self.log(self.LOG_STUB, func)

    def INFO(self, info):
        if self.logLevel & self.LOG_INFO:
            self.log(self.LOG_INFO, info)

    def DEBUG(self, info):
        if self.logLevel & self.LOG_DEBUG:
            self.log(self.LOG_DEBUG, info)

    def ASSERT_UNREACHED(self, err):
        raise Exception("Should be unreached: " + err)

    def ASSERT(self, test, err):
        if not test:
            raise Exception("Assertion failed: " + err)