class ARMCoreThumb:
    def __init__(self, cpu):
        self.cpu = cpu
    
    def constructADC(self, rd, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def adc():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            m = (gprs[rm] >> 0) + int(cpu.cpsrC)
            oldD = gprs[rd]
            d = (oldD >> 0) + m
            oldDn = oldD >> 31
            dn = d >> 31
            mn = m >> 31
            cpu.cpsrN = dn
            cpu.cpsrZ = not (d & 0xffffffff)
            cpu.cpsrC = d > 0xffffffff
            cpu.cpsrV = oldDn == mn and oldDn != dn and mn != dn
            gprs[rd] = d
        return adc
    
    def constructADD1(self, rd, rn, immediate):
        cpu = self.cpu
        gprs = cpu.gprs
        def add():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            d = (gprs[rn] >> 0) + immediate
            cpu.cpsrN = d >> 31
            cpu.cpsrZ = not (d & 0xffffffff)
            cpu.cpsrC = d > 0xffffffff
            cpu.cpsrV = not (gprs[rn] >> 31) and ((gprs[rn] >> 31) ^ d) >> 31 and d >> 31
            gprs[rd] = d
        return add
    
    def constructADD2(self, rn, immediate):
        cpu = self.cpu
        gprs = cpu.gprs
        def add():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            d = (gprs[rn] >> 0) + immediate
            cpu.cpsrN = d >> 31
            cpu.cpsrZ = not (d & 0xffffffff)
            cpu.cpsrC = d > 0xffffffff
            cpu.cpsrV = not (gprs[rn] >> 31) and (gprs[rn] ^ d) >> 31 and (immediate ^ d) >> 31
            gprs[rn] = d
        return add
    
    def constructADD3(self, rd, rn, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def add():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            d = (gprs[rn] >> 0) + (gprs[rm] >> 0)
            cpu.cpsrN = d >> 31
            cpu.cpsrZ = not (d & 0xffffffff)
            cpu.cpsrC = d > 0xffffffff
            cpu.cpsrV = not ((gprs[rn] ^ gprs[rm]) >> 31) and (gprs[rn] ^ d) >> 31 and (gprs[rm] ^ d) >> 31
            gprs[rd] = d
        return add
    
    def constructADD4(self, rd, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def add():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            gprs[rd] += gprs[rm]
        return add
    
    def constructADD5(self, rd, immediate):
        cpu = self.cpu
        gprs = cpu.gprs
        def add():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            gprs[rd] = (gprs[cpu.PC] & 0xfffffffc) + immediate
        return add
    
    def constructADD6(self, rd, immediate):
        cpu = self.cpu
        gprs = cpu.gprs
        def add():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            gprs[rd] = gprs[cpu.SP] + immediate
        return add
    
    def constructADD7(self, immediate):
        cpu = self.cpu
        gprs = cpu.gprs
        def add():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            gprs[cpu.SP] += immediate
        return add
    
    def constructAND(self, rd, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def and_():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            gprs[rd] = gprs[rd] & gprs[rm]
            cpu.cpsrN = gprs[rd] >> 31
            cpu.cpsrZ = not (gprs[rd] & 0xffffffff)
        return and_
    
    def constructASR1(self, rd, rm, immediate):
        cpu = self.cpu
        gprs = cpu.gprs
        def asr():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            if immediate == 0:
                cpu.cpsrC = gprs[rm] >> 31
                if cpu.cpsrC:
                    gprs[rd] = 0xffffffff
                else:
                    gprs[rd] = 0
            else:
                cpu.cpsrC = gprs[rm] & (1 << (immediate - 1))
                gprs[rd] = gprs[rm] >> immediate
            cpu.cpsrN = gprs[rd] >> 31
            cpu.cpsrZ = not (gprs[rd] & 0xffffffff)
        return asr
    
    def constructASR2(self, rd, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def asr():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            rs = gprs[rm] & 0xff
            if rs:
                if rs < 32:
                    cpu.cpsrC = gprs[rd] & (1 << (rs - 1))
                    gprs[rd] >>= rs
                else:
                    cpu.cpsrC = gprs[rd] >> 31
                    if cpu.cpsrC:
                        gprs[rd] = 0xffffffff
                    else:
                        gprs[rd] = 0
            cpu.cpsrN = gprs[rd] >> 31
            cpu.cpsrZ = not (gprs[rd] & 0xffffffff)
        return asr
    
    def constructB1(self, immediate, condOp):
        cpu = self.cpu
        gprs = cpu.gprs
        def b():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            if condOp():
                gprs[cpu.PC] += immediate
        return b
    
    def constructB2(self, immediate):
        cpu = self.cpu
        gprs = cpu.gprs
        def b():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            gprs[cpu.PC] += immediate
        return b
    
    def constructBIC(self, rd, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def bic():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            gprs[rd] = gprs[rd] & ~gprs[rm]
            cpu.cpsrN = gprs[rd] >> 31
            cpu.cpsrZ = not (gprs[rd] & 0xffffffff)
        return bic
    
    def constructBL1(self, immediate):
        cpu = self.cpu
        gprs = cpu.gprs
        def bl():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            gprs[cpu.LR] = gprs[cpu.PC] + immediate
        return bl
    
    def constructBL2(self, immediate):
        cpu = self.cpu
        gprs = cpu.gprs
        def bl():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            pc = gprs[cpu.PC]
            gprs[cpu.PC] = gprs[cpu.LR] + (immediate << 1)
            gprs[cpu.LR] = pc - 1
        return bl
    
    def constructBX(self, rd, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def bx():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            cpu.switchExecMode(gprs[rm] & 0x00000001)
            misalign = 0
            if rm == 15:
                misalign = gprs[rm] & 0x00000002
            gprs[cpu.PC] = gprs[rm] & (0xfffffffe - misalign)
        return bx
    
    def constructCMN(self, rd, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def cmn():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            aluOut = (gprs[rd] >> 0) + (gprs[rm] >> 0)
            cpu.cpsrN = aluOut >> 31
            cpu.cpsrZ = not (aluOut & 0xffffffff)
            cpu.cpsrC = aluOut > 0xffffffff
            cpu.cpsrV = gprs[rd] >> 31 == gprs[rm] >> 31 and gprs[rd] >> 31 != aluOut >> 31 and gprs[rm] >> 31 != aluOut >> 31
        return cmn
    
    def constructCMP1(self, rn, immediate):
        cpu = self.cpu
        gprs = cpu.gprs
        def cmp():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            aluOut = gprs[rn] - immediate
            cpu.cpsrN = aluOut >> 31
            cpu.cpsrZ = not (aluOut & 0xffffffff)
            cpu.cpsrC = gprs[rn] >> 0 >= immediate
            cpu.cpsrV = gprs[rn] >> 31 and (gprs[rn] ^ aluOut) >> 31
        return cmp
    
    def constructCMP2(self, rd, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def cmp():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            d = gprs[rd]
            m = gprs[rm]
            aluOut = d - m
            an = aluOut >> 31
            dn = d >> 31
            cpu.cpsrN = an
            cpu.cpsrZ = not (aluOut & 0xffffffff)
            cpu.cpsrC = d >> 0 >= m >> 0
            cpu.cpsrV = dn != m >> 31 and dn != an
        return cmp
    
    def constructCMP3(self, rd, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def cmp():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            aluOut = gprs[rd] - gprs[rm]
            cpu.cpsrN = aluOut >> 31
            cpu.cpsrZ = not (aluOut & 0xffffffff)
            cpu.cpsrC = gprs[rd] >> 0 >= gprs[rm] >> 0
            cpu.cpsrV = (gprs[rd] ^ gprs[rm]) >> 31 and (gprs[rd] ^ aluOut) >> 31
        return cmp
    
    def constructEOR(self, rd, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def eor():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            gprs[rd] = gprs[rd] ^ gprs[rm]
            cpu.cpsrN = gprs[rd] >> 31
            cpu.cpsrZ = not (gprs[rd] & 0xffffffff)
        return eor
    
    def constructLDMIA(self, rn, rs):
        cpu = self.cpu
        gprs = cpu.gprs
        def ldmia():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            address = gprs[rn]
            total = 0
            m, i = 0x01, 0
            while i < 8:
                if rs & m:
                    gprs[i] = cpu.mmu.load32(address)
                    address += 4
                    total += 1
                m <<= 1
                i += 1
            cpu.mmu.waitMulti32(address, total)
            if not ((1 << rn) & rs):
                gprs[rn] = address
        return ldmia
    
    def constructLDR1(self, rd, rn, immediate):
        cpu = self.cpu
        gprs = cpu.gprs
        def ldr():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            n = gprs[rn] + immediate
            gprs[rd] = cpu.mmu.load32(n)
            cpu.mmu.wait32(n)
            cpu.cycles += 1
        return ldr
    
    def constructLDR2(self, rd, rn, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def ldr():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            gprs[rd] = cpu.mmu.load32(gprs[rn] + gprs[rm])
            cpu.mmu.wait32(gprs[rn] + gprs[rm])
            cpu.cycles += 1
        return ldr
    
    def constructLDR3(self, rd, immediate):
        cpu = self.cpu
        gprs = cpu.gprs
        def ldr():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            gprs[rd] = cpu.mmu.load32((gprs[cpu.PC] & 0xfffffffc) + immediate)
            cpu.mmu.wait32(gprs[cpu.PC])
            cpu.cycles += 1
        return ldr
    
    def constructLDR4(self, rd, immediate):
        cpu = self.cpu
        gprs = cpu.gprs
        def ldr():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            gprs[rd] = cpu.mmu.load32(gprs[cpu.SP] + immediate)
            cpu.mmu.wait32(gprs[cpu.SP] + immediate)
            cpu.cycles += 1
        return ldr
    
    def constructLDRB1(self, rd, rn, immediate):
        cpu = self.cpu
        gprs = cpu.gprs
        def ldrb():
            n = gprs[rn] + immediate
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            gprs[rd] = cpu.mmu.loadU8(n)
            cpu.mmu.wait(n)
            cpu.cycles += 1
        return ldrb
    
    def constructLDRB2(self, rd, rn, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def ldrb():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            gprs[rd] = cpu.mmu.loadU8(gprs[rn] + gprs[rm])
            cpu.mmu.wait(gprs[rn] + gprs[rm])
            cpu.cycles += 1
        return ldrb
    
    def constructLDRH1(self, rd, rn, immediate):
        cpu = self.cpu
        gprs = cpu.gprs
        def ldrh():
            n = gprs[rn] + immediate
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            gprs[rd] = cpu.mmu.loadU16(n)
            cpu.mmu.wait(n)
            cpu.cycles += 1
        return ldrh
    
    def constructLDRH2(self, rd, rn, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def ldrh():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            gprs[rd] = cpu.mmu.loadU16(gprs[rn] + gprs[rm])
            cpu.mmu.wait(gprs[rn] + gprs[rm])
            cpu.cycles += 1
        return ldrh
    
    def constructLDRSB(self, rd, rn, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def ldrsb():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            gprs[rd] = cpu.mmu.load8(gprs[rn] + gprs[rm])
            cpu.mmu.wait(gprs[rn] + gprs[rm])
            cpu.cycles += 1
        return ldrsb
    
    def constructLDRSH(self, rd, rn, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def ldrsh():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            gprs[rd] = cpu.mmu.load16(gprs[rn] + gprs[rm])
            cpu.mmu.wait(gprs[rn] + gprs[rm])
            cpu.cycles += 1
        return ldrsh
    
    def constructLSL1(self, rd, rm, immediate):
        cpu = self.cpu
        gprs = cpu.gprs
        def lsl():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            if immediate == 0:
                gprs[rd] = gprs[rm]
            else:
                cpu.cpsrC = gprs[rm] & (1 << (32 - immediate))
                gprs[rd] = gprs[rm] << immediate
            cpu.cpsrN = gprs[rd] >> 31
            cpu.cpsrZ = not (gprs[rd] & 0xffffffff)
        return lsl
    
    def constructLSL2(self, rd, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def lsl():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            rs = gprs[rm] & 0xff
            if rs:
                if rs < 32:
                    cpu.cpsrC = gprs[rd] & (1 << (32 - rs))
                    gprs[rd] <<= rs
                else:
                    if rs > 32:
                        cpu.cpsrC = 0
                    else:
                        cpu.cpsrC = gprs[rd] & 0x00000001
                    gprs[rd] = 0
            cpu.cpsrN = gprs[rd] >> 31
            cpu.cpsrZ = not (gprs[rd] & 0xffffffff)
        return lsl
    
    def constructLSR1(self, rd, rm, immediate):
        cpu = self.cpu
        gprs = cpu.gprs
        def lsr():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            if immediate == 0:
                cpu.cpsrC = gprs[rm] >> 31
                gprs[rd] = 0
            else:
                cpu.cpsrC = gprs[rm] & (1 << (immediate - 1))
                gprs[rd] = gprs[rm] >> immediate
            cpu.cpsrN = 0
            cpu.cpsrZ = not (gprs[rd] & 0xffffffff)
        return lsr
    
    def constructLSR2(self, rd, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def lsr():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            rs = gprs[rm] & 0xff
            if rs:
                if rs < 32:
                    cpu.cpsrC = gprs[rd] & (1 << (rs - 1))
                    gprs[rd] >>= rs
                else:
                    if rs > 32:
                        cpu.cpsrC = 0
                    else:
                        cpu.cpsrC = gprs[rd] >> 31
                    gprs[rd] = 0
            cpu.cpsrN = gprs[rd] >> 31
            cpu.cpsrZ = not (gprs[rd] & 0xffffffff)
        return lsr
    
    def constructMOV1(self, rn, immediate):
        cpu = self.cpu
        gprs = cpu.gprs
        def mov():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            gprs[rn] = immediate
            cpu.cpsrN = immediate >> 31
            cpu.cpsrZ = not (immediate & 0xffffffff)
        return mov
    
    def constructMOV2(self, rd, rn, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def mov():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            d = gprs[rn]
            cpu.cpsrN = d >> 31
            cpu.cpsrZ = not (d & 0xffffffff)
            cpu.cpsrC = 0
            cpu.cpsrV = 0
            gprs[rd] = d
        return mov
    
    def constructMOV3(self, rd, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def mov():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            gprs[rd] = gprs[rm]
        return mov
    
    def constructMUL(self, rd, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def mul():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            cpu.mmu.waitMul(gprs[rm])
            if gprs[rm] & 0xffff0000 and gprs[rd] & 0xffff0000:
                hi = ((gprs[rd] & 0xffff0000) * gprs[rm]) & 0xffffffff
                lo = ((gprs[rd] & 0x0000ffff) * gprs[rm]) & 0xffffffff
                gprs[rd] = (hi + lo) & 0xffffffff
            else:
                gprs[rd] *= gprs[rm]
            cpu.cpsrN = gprs[rd] >> 31
            cpu.cpsrZ = not (gprs[rd] & 0xffffffff)
        return mul
    
    def constructMVN(self, rd, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def mvn():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            gprs[rd] = ~gprs[rm]
            cpu.cpsrN = gprs[rd] >> 31
            cpu.cpsrZ = not (gprs[rd] & 0xffffffff)
        return mvn
    
    def constructNEG(self, rd, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def neg():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            d = -gprs[rm]
            cpu.cpsrN = d >> 31
            cpu.cpsrZ = not (d & 0xffffffff)
            cpu.cpsrC = 0 >= d >> 0
            cpu.cpsrV = gprs[rm] >> 31 and d >> 31
            gprs[rd] = d
        return neg
    
    def constructORR(self, rd, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def orr():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            gprs[rd] = gprs[rd] | gprs[rm]
            cpu.cpsrN = gprs[rd] >> 31
            cpu.cpsrZ = not (gprs[rd] & 0xffffffff)
        return orr
    
    def constructPOP(self, rs, r):
        cpu = self.cpu
        gprs = cpu.gprs
        def pop():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            cpu.cycles += 1
            address = gprs[cpu.SP]
            total = 0
            m, i = 0x01, 0
            while i < 8:
                if rs & m:
                    cpu.mmu.waitSeq32(address)
                    gprs[i] = cpu.mmu.load32(address)
                    address += 4
                    total += 1
                m <<= 1
                i += 1
            if r:
                gprs[cpu.PC] = cpu.mmu.load32(address) & 0xfffffffe
                address += 4
                total += 1
            cpu.mmu.waitMulti32(address, total)
            gprs[cpu.SP] = address
        return pop
    
    def constructPUSH(self, rs, r):
        cpu = self.cpu
        gprs = cpu.gprs
        def push():
            address = gprs[cpu.SP] - 4
            total = 0
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            if r:
                cpu.mmu.store32(address, gprs[cpu.LR])
                address -= 4
                total += 1
            m, i = 0x80, 7
            while m:
                if rs & m:
                    cpu.mmu.store32(address, gprs[i])
                    address -= 4
                    total += 1
                    break
                m >>= 1
                i -= 1
            m >>= 1
            i -= 1
            while m:
                if rs & m:
                    cpu.mmu.store32(address, gprs[i])
                    address -= 4
                    total += 1
                m >>= 1
                i -= 1
            cpu.mmu.waitMulti32(address, total)
            gprs[cpu.SP] = address + 4
        return push
    
    def constructROR(self, rd, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def ror():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            rs = gprs[rm] & 0xff
            if rs:
                r4 = rs & 0x1f
                if r4 > 0:
                    cpu.cpsrC = gprs[rd] & (1 << (r4 - 1))
                    gprs[rd] = (gprs[rd] >> r4) | (gprs[rd] << (32 - r4))
                else:
                    cpu.cpsrC = gprs[rd] >> 31
            cpu.cpsrN = gprs[rd] >> 31
            cpu.cpsrZ = not (gprs[rd] & 0xffffffff)
        return ror
    
    def constructSBC(self, rd, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def sbc():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            m = (gprs[rm] >> 0) + (1 - cpu.cpsrC)
            d = (gprs[rd] >> 0) - m
            cpu.cpsrN = d >> 31
            cpu.cpsrZ = not (d & 0xffffffff)
            cpu.cpsrC = gprs[rd] >> 0 >= d >> 0
            cpu.cpsrV = (gprs[rd] ^ m) >> 31 and (gprs[rd] ^ d) >> 31
            gprs[rd] = d
        return sbc
    
    def constructSTMIA(self, rn, rs):
        cpu = self.cpu
        gprs = cpu.gprs
        def stmia():
            cpu.mmu.wait(gprs[cpu.PC])
            address = gprs[rn]
            total = 0
            m, i = 0x01, 0
            while i < 8:
                if rs & m:
                    cpu.mmu.store32(address, gprs[i])
                    address += 4
                    total += 1
                    break
                m <<= 1
                i += 1
            m <<= 1
            i += 1
            while i < 8:
                if rs & m:
                    cpu.mmu.store32(address, gprs[i])
                    address += 4
                    total += 1
                m <<= 1
                i += 1
            cpu.mmu.waitMulti32(address, total)
            gprs[rn] = address
        return stmia
    
    def constructSTR1(self, rd, rn, immediate):
        cpu = self.cpu
        gprs = cpu.gprs
        def str():
            n = gprs[rn] + immediate
            cpu.mmu.store32(n, gprs[rd])
            cpu.mmu.wait(gprs[cpu.PC])
            cpu.mmu.wait32(n)
        return str
    
    def constructSTR2(self, rd, rn, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def str():
            cpu.mmu.store32(gprs[rn] + gprs[rm], gprs[rd])
            cpu.mmu.wait(gprs[cpu.PC])
            cpu.mmu.wait32(gprs[rn] + gprs[rm])
        return str
    
    def constructSTR3(self, rd, immediate):
        cpu = self.cpu
        gprs = cpu.gprs
        def str():
            cpu.mmu.store32(gprs[cpu.SP] + immediate, gprs[rd])
            cpu.mmu.wait(gprs[cpu.PC])
            cpu.mmu.wait32(gprs[cpu.SP] + immediate)
        return str
    
    def constructSTRB1(self, rd, rn, immediate):
        cpu = self.cpu
        gprs = cpu.gprs
        def strb():
            n = gprs[rn] + immediate
            cpu.mmu.store8(n, gprs[rd])
            cpu.mmu.wait(gprs[cpu.PC])
            cpu.mmu.wait(n)
        return strb
    
    def constructSTRB2(self, rd, rn, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def strb():
            cpu.mmu.store8(gprs[rn] + gprs[rm], gprs[rd])
            cpu.mmu.wait(gprs[cpu.PC])
            cpu.mmu.wait(gprs[rn] + gprs[rm])
        return strb
    
    def constructSTRH1(self, rd, rn, immediate):
        cpu = self.cpu
        gprs = cpu.gprs
        def strh():
            n = gprs[rn] + immediate
            cpu.mmu.store16(n, gprs[rd])
            cpu.mmu.wait(gprs[cpu.PC])
            cpu.mmu.wait(n)
        return strh
    
    def constructSTRH2(self, rd, rn, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def strh():
            cpu.mmu.store16(gprs[rn] + gprs[rm], gprs[rd])
            cpu.mmu.wait(gprs[cpu.PC])
            cpu.mmu.wait(gprs[rn] + gprs[rm])
        return strh
    
    def constructSUB1(self, rd, rn, immediate):
        cpu = self.cpu
        gprs = cpu.gprs
        def sub():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            d = gprs[rn] - immediate
            cpu.cpsrN = d >> 31
            cpu.cpsrZ = not (d & 0xffffffff)
            cpu.cpsrC = gprs[rn] >> 0 >= immediate
            cpu.cpsrV = gprs[rn] >> 31 and (gprs[rn] ^ d) >> 31
            gprs[rd] = d
        return sub
    
    def constructSUB2(self, rn, immediate):
        cpu = self.cpu
        gprs = cpu.gprs
        def sub():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            d = gprs[rn] - immediate
            cpu.cpsrN = d >> 31
            cpu.cpsrZ = not (d & 0xffffffff)
            cpu.cpsrC = gprs[rn] >> 0 >= immediate
            cpu.cpsrV = gprs[rn] >> 31 and (gprs[rn] ^ d) >> 31
            gprs[rn] = d
        return sub
    
    def constructSUB3(self, rd, rn, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def sub():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            d = gprs[rn] - gprs[rm]
            cpu.cpsrN = d >> 31
            cpu.cpsrZ = not (d & 0xffffffff)
            cpu.cpsrC = gprs[rn] >> 0 >= gprs[rm] >> 0
            cpu.cpsrV = (gprs[rn] ^ gprs[rm]) >> 31 and (gprs[rn] ^ d) >> 31
            gprs[rd] = d
        return sub
    
    def constructSWI(self, immediate):
        cpu = self.cpu
        gprs = cpu.gprs
        def swi():
            cpu.irq.swi(immediate)
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
        return swi
    
    def constructTST(self, rd, rm):
        cpu = self.cpu
        gprs = cpu.gprs
        def tst():
            cpu.mmu.waitPrefetch(gprs[cpu.PC])
            aluOut = gprs[rd] & gprs[rm]
            cpu.cpsrN = aluOut >> 31
            cpu.cpsrZ = not (aluOut & 0xffffffff)
        return tst