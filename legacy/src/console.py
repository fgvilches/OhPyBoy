import tkinter as tk
from tkinter import messagebox
from gba import *
class Console:
    def __init__(self, gba):
        self.cpu = gba.cpu
        self.gba = gba
        self.ul = tk.Text()
        self.gprs = tk.Text()
        self.memory = Memory(gba.mmu)
        self.breakpoints = []
        self.logQueue = []

        self.activeView = None
        self.paletteView = PaletteViewer(gba.video.renderPath.palette)
        self.tileView = TileViewer(gba.video.renderPath.vram, gba.video.renderPath.palette)
        self.update()

        gba.setLogger(lambda level, message: self.log(level, message))
        self.gba.doStep = lambda: self.testBreakpoints()

    def updateGPRs(self):
        for i in range(16):
            self.gprs.insert(tk.END, hex(self.cpu.gprs[i]) + "\n")

    def updateCPSR(self):
        cpu = self.cpu
        bit = lambda psr, member: getattr(cpu, member)
        cpsrN = bit('cpsrN', 'cpsrN')
        cpsrZ = bit('cpsrZ', 'cpsrZ')
        cpsrC = bit('cpsrC', 'cpsrC')
        cpsrV = bit('cpsrV', 'cpsrV')
        cpsrI = bit('cpsrI', 'cpsrI')
        cpsrT = bit('cpsrT', 'execMode')

        self.ul.tag_configure("enabled", foreground="black")
        self.ul.tag_configure("disabled", foreground="red")

        self.ul.insert(tk.END, "cpsrN: ", "enabled" if cpsrN else "disabled")
        self.ul.insert(tk.END, "cpsrZ: ", "enabled" if cpsrZ else "disabled")
        self.ul.insert(tk.END, "cpsrC: ", "enabled" if cpsrC else "disabled")
        self.ul.insert(tk.END, "cpsrV: ", "enabled" if cpsrV else "disabled")
        self.ul.insert(tk.END, "cpsrI: ", "enabled" if cpsrI else "disabled")
        self.ul.insert(tk.END, "cpsrT: ", "enabled" if cpsrT else "disabled")

        mode = tk.Label()
        mode.pack()
        modeText = ""
        if cpu.mode == cpu.MODE_USER:
            modeText = "USER"
        elif cpu.mode == cpu.MODE_IRQ:
            modeText = "IRQ"
        elif cpu.mode == cpu.MODE_FIQ:
            modeText = "FIQ"
        elif cpu.mode == cpu.MODE_SUPERVISOR:
            modeText = "SVC"
        elif cpu.mode == cpu.MODE_ABORT:
            modeText = "ABORT"
        elif cpu.mode == cpu.MODE_UNDEFINED:
            modeText = "UNDEFINED"
        elif cpu.mode == cpu.MODE_SYSTEM:
            modeText = "SYSTEM"
        else:
            modeText = "???"
        mode.config(text=modeText)

    def log(self, level, message):
        levelText = ""
        if level == self.gba.LOG_ERROR:
            levelText = "[ERROR] "
        elif level == self.gba.LOG_WARN:
            levelText = "[WARN] "
        elif level == self.gba.LOG_STUB:
            levelText = "[STUB] "
        elif level == self.gba.LOG_INFO:
            levelText = "[INFO] "
        elif level == self.gba.LOG_DEBUG:
            levelText = "[DEBUG] "
        self.logQueue.append(levelText + message)
        if level == self.gba.LOG_ERROR:
            self.pause()
        if not self.stillRunning:
            self.flushLog()

    def flushLog(self):
        doScroll = self.ul.yview()[1] == 1.0
        for message in self.logQueue:
            self.ul.insert(tk.END, message + "\n")
        if doScroll:
            self.ul.yview(tk.END)

    def update(self):
        self.updateGPRs()
        self.updateCPSR()
        self.memory.refreshAll()
        if self.activeView:
            self.activeView.redraw()

    def setView(self, view):
        container = tk.Frame()
        container.pack()
        container.pack_propagate(0)
        container.pack(fill=tk.BOTH, expand=True)
        if view:
            view.insertChildren(container)
            view.redraw()
        self.activeView = view

    def step(self):
        try:
            self.cpu.step()
            self.update()
        except Exception as e:
            self.log(self.gba.LOG_DEBUG, str(e))
            raise e

    def runVisible(self):
        if self.stillRunning:
            return

        self.stillRunning = True
        self.run()

    def run(self):
        if self.stillRunning:
            return

        self.stillRunning = True
        self.gba.runStable()

    def runFrame(self):
        if self.stillRunning:
            return

        self.stillRunning = True
        self.gba.step()
        self.pause()

    def pause(self):
        self.stillRunning = False
        self.gba.pause()
        self.update()
        self.flushLog()

    def breakpointHit(self):
        self.pause()
        self.log(self.gba.LOG_DEBUG, 'Hit breakpoint at ' + hex(self.cpu.gprs[self.cpu.PC]))

    def addBreakpoint(self, addr):
        self.breakpoints.append(addr)
        bpLi = tk.Checkbutton()
        bpLi.pack()
        bpLi.config(text=hex(addr))
        bpLi.config(variable=tk.BooleanVar(value=True))
        self.breakpoints.append(bpLi)

    def testBreakpoints(self):
        if self.breakpoints and self.cpu.gprs[self.cpu.PC] in self.breakpoints:
            self.breakpointHit()
            return False
        return self.gba.waitFrame()

class Memory:
    def __init__(self, mmu):
        self.mmu = mmu
        self.ul = tk.Text()
        self.rowHeight = 0
        self.numberRows = 0
        self.scrollTop = 0

        self.ul.bind("<Configure>", self.resize)
        self.ul.bind("<MouseWheel>", self.scroll)

        for i in range(16):
            self.ul.insert(tk.END, hex(i * 16) + "\n")
            for j in range(16):
                self.ul.insert(tk.END, "00 ")
            self.ul.insert(tk.END, "\n")

        self.ul.pack()

    def scroll(self, event):
        self.ul.yview_scroll(-1 * int(event.delta / 120), "units")

    def resize(self, event):
        self.numberRows = int(self.ul.winfo_height() / self.rowHeight) + 2
        if self.numberRows > self.ul.index(tk.END):
            offset = self.ul.index(tk.END) * 16
            for i in range(self.numberRows - self.ul.index(tk.END)):
                self.ul.insert(tk.END, hex(offset) + "\n")
                for j in range(16):
                    self.ul.insert(tk.END, "00 ")
                self.ul.insert(tk.END, "\n")
                offset += 16
        else:
            for i in range(self.ul.index(tk.END) - self.numberRows):
                self.ul.delete(tk.END)

    def refresh(self, row):
        showChanged = False
        if row.oldOffset == row.offset:
            showChanged = True
        else:
            row.oldOffset = row.offset
            showChanged = False

        for i in range(16):
            try:
                newValue = self.mmu.loadU8(row.offset + i)
                if newValue >= 0:
                    newValue = hex(newValue)[2:].zfill(2)
                    if row.children[i + 1].get() == newValue:
                        row.children[i + 1].config(foreground="black")
                    elif showChanged:
                        row.children[i + 1].config(foreground="red")
                        row.children[i + 1].delete(0, tk.END)
                        row.children[i + 1].insert(tk.END, newValue)
                    else:
                        row.children[i + 1].config(foreground="black")
                        row.children[i + 1].delete(0, tk.END)
                        row.children[i + 1].insert(tk.END, newValue)
                else:
                    row.children[i + 1].config(foreground="black")
                    row.children[i + 1].delete(0, tk.END)
                    row.children[i + 1].insert(tk.END, "--")
            except Exception as e:
                row.children[i + 1].config(foreground="black")
                row.children[i + 1].delete(0, tk.END)
                row.children[i + 1].insert(tk.END, "--")

    def refreshAll(self):
        for i in range(self.ul.index(tk.END)):
            self.refresh(self.ul.children[i])

class PaletteViewer:
    def __init__(self, palette):
        self.palette = palette
        self.view = tk.Canvas()

    def insertChildren(self, container):
        self.view.pack()

    def redraw(self):
        self.view.delete("all")
        for p in range(2):
            for y in range(16):
                for x in range(16):
                    color = self.palette.loadU16((p * 256 + y * 16 + x) * 2)
                    r = (color & 0x001F) << 3
                    g = (color & 0x03E0) >> 2
                    b = (color & 0x7C00) >> 7
                    self.view.create_rectangle(x * 15 + 1, y * 15 + p * 255 + 1, x * 15 + 14, y * 15 + p * 255 + 14, fill="#%02x%02x%02x" % (r, g, b))

class TileViewer:
    def __init__(self, vram, palette):
        self.BG_MAP_WIDTH = 256
        self.vram = vram
        self.palette = palette

        self.view = tk.Canvas()

    def insertChildren(self, container):
        self.view.pack()

    def redraw(self):
        self.view.delete("all")
        for t in range(512):
            x = (t % 32) * 8
            y = (t // 32) * 8
            self.drawTile(t, self.activePalette, x, y)

    def drawTile(self, tile, palette, x, y):
        for j in range(8):
            memOffset = (tile << 5) | (j << 2)
            row = self.vram.load32(memOffset)
            for i in range(8):
                index = (row >> (i << 2)) & 0xF
                color = self.palette.loadU16((index << 1) + (palette << 5))
                r = (color & 0x001F) << 3
                g = (color & 0x03E0) >> 2
                b = (color & 0x7C00) >> 7
                self.view.create_rectangle(x + i, y + j, x + i + 1, y + j + 1, fill="#%02x%02x%02x" % (r, g, b))

gba = GameBoyAdvance()  # Replace with your GameBoy Advance object
console = Console(gba)