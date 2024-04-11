from thumb import ARMCoreThumb
class ARMCoreArm:
    def __init__(self, cpu):
        self.cpu = cpu

        self.addressingMode23Immediate = [
            # 000x0
            lambda rn, offset, condOp: (
                lambda: (
                    self.cpu.gprs.__setitem__(rn, self.cpu.gprs[rn] - offset) if not condOp or condOp() else None
                )
            ),
            # 000xW
            None,
            None,
            None,
            # 00Ux0
            lambda rn, offset, condOp: (
                lambda: (
                    self.cpu.gprs.__setitem__(rn, self.cpu.gprs[rn] + offset) if not condOp or condOp() else None
                )
            ),
            # 00UxW
            None,
            None,
            None,
            # 0P0x0
            lambda rn, offset, condOp: (
                lambda: (
                    self.cpu.gprs.__setitem__(rn, self.cpu.gprs[rn] - offset)
                )
            ),
            # 0P0xW
            lambda rn, offset, condOp: (
                lambda: (
                    self.cpu.gprs.__setitem__(rn, self.cpu.gprs[rn] - offset) if not condOp or condOp() else None
                )
            ),
            None,
            None,
            # 0PUx0
            lambda rn, offset, condOp: (
                lambda: (
                    self.cpu.gprs.__setitem__(rn, self.cpu.gprs[rn] + offset)
                )
            ),
            # 0PUxW
            lambda rn, offset, condOp: (
                lambda: (
                    self.cpu.gprs.__setitem__(rn, self.cpu.gprs[rn] + offset) if not condOp or condOp() else None
                )
            ),
            None,
            None
        ]

        self.addressingMode23Register = [
            # I00x0
            lambda rn, rm, condOp: (
                lambda: (
                    self.cpu.gprs.__setitem__(rn, self.cpu.gprs[rn] - self.cpu.gprs[rm]) if not condOp or condOp() else None
                )
            ),
            # I00xW
            None,
            None,
            None,
            # I0Ux0
            lambda rn, rm, condOp: (
                lambda: (
                    self.cpu.gprs.__setitem__(rn, self.cpu.gprs[rn] + self.cpu.gprs[rm]) if not condOp or condOp() else None
                )
            ),
            # I0UxW
            None,
            None,
            None,
            # IP0x0
            lambda rn, rm, condOp: (
                lambda: (
                    self.cpu.gprs.__setitem__(rn, self.cpu.gprs[rn] - self.cpu.gprs[rm])
                )
            ),
            # IP0xW
            lambda rn, rm, condOp: (
                lambda: (
                    self.cpu.gprs.__setitem__(rn, self.cpu.gprs[rn] - self.cpu.gprs[rm]) if not condOp or condOp() else None
                )
            ),
            None,
            None,
            # IPUx0
            lambda rn, rm, condOp: (
                lambda: (
                    self.cpu.gprs.__setitem__(rn, self.cpu.gprs[rn] + self.cpu.gprs[rm])
                )
            ),
            # IPUxW
            lambda rn, rm, condOp: (
                lambda: (
                    self.cpu.gprs.__setitem__(rn, self.cpu.gprs[rn] + self.cpu.gprs[rm]) if not condOp or condOp() else None
                )
            ),
            None,
            None
        ]

        self.addressingMode2RegisterShifted = [
            # I00x0
            lambda rn, shiftOp, condOp: (
                lambda: (
                    self.cpu.gprs.__setitem__(rn, self.cpu.gprs[rn] - self.cpu.shifterOperand) if not condOp or condOp() else None
                )
            ),
            # I00xW
            None,
            None,
            None,
            # I0Ux0
            lambda rn, shiftOp, condOp: (
                lambda: (
                    self.cpu.gprs.__setitem__(rn, self.cpu.gprs[rn] + self.cpu.shifterOperand) if not condOp or condOp() else None
                )
            ),
            # I0UxW
            None,
            None,
            None,
            # IP0x0
            lambda rn, shiftOp, condOp: (
                lambda: (
                    self.cpu.gprs.__setitem__(rn, self.cpu.gprs[rn] - self.cpu.shifterOperand)
                )
            ),
            # IP0xW
            lambda rn, shiftOp, condOp: (
                lambda: (
                    self.cpu.gprs.__setitem__(rn, self.cpu.gprs[rn] - self.cpu.shifterOperand) if not condOp or condOp() else None
                )
            ),
            None,
            None,
            # IPUx0
            lambda rn, shiftOp, condOp: (
                lambda: (
                    self.cpu.gprs.__setitem__(rn, self.cpu.gprs[rn] + self.cpu.shifterOperand)
                )
            ),
            # IPUxW
            lambda rn, shiftOp, condOp: (
                lambda: (
                    self.cpu.gprs.__setitem__(rn, self.cpu.gprs[rn] + self.cpu.shifterOperand) if not condOp or condOp() else None
                )
            ),
            None,
            None
        ]

        
    def constructAddressingMode1ASR(rs, rm):
        
        def addressing_mode():
            global cpu
            global gprs
            cpu.cycles += 1
            shift = gprs[rs]
            if rs == cpu.PC:
                shift += 4
            shift &= 0xff
            shift_val = gprs[rm]
            if rm == cpu.PC:
                shift_val += 4
            if shift == 0:
                cpu.shifterOperand = shift_val
                cpu.shifterCarryOut = cpu.cpsrC
            elif shift < 32:
                cpu.shifterOperand = shift_val >> shift
                cpu.shifterCarryOut = shift_val & (1 << (shift - 1))
            elif gprs[rm] >> 31:
                cpu.shifterOperand = 0xffffffff
                cpu.shifterCarryOut = 0x80000000
            else:
                cpu.shifterOperand = 0
                cpu.shifterCarryOut = 0
        return addressing_mode

    def constructAddressingMode1Immediate(immediate):
        def addressing_mode():
            global cpu
            cpu.shifterOperand = immediate
            cpu.shifterCarryOut = cpu.cpsrC
        return addressing_mode

    def constructAddressingMode1ImmediateRotate(immediate, rotate):
        def addressing_mode():
            global cpu
            cpu.shifterOperand = (immediate >> rotate) | (immediate << (32 - rotate))
            cpu.shifterCarryOut = cpu.shifterOperand >> 31
        return addressing_mode

    def constructAddressingMode1LSL(rs, rm):
        def addressing_mode():
            global cpu
            global gprs
            cpu.cycles += 1
            shift = gprs[rs]
            if rs == cpu.PC:
                shift += 4
            shift &= 0xff
            shift_val = gprs[rm]
            if rm == cpu.PC:
                shift_val += 4
            if shift == 0:
                cpu.shifterOperand = shift_val
                cpu.shifterCarryOut = cpu.cpsrC
            elif shift < 32:
                cpu.shifterOperand = shift_val << shift
                cpu.shifterCarryOut = shift_val & (1 << (32 - shift))
            elif shift == 32:
                cpu.shifterOperand = 0
                cpu.shifterCarryOut = shift_val & 1
            else:
                cpu.shifterOperand = 0
                cpu.shifterCarryOut = 0
        return addressing_mode

    def constructAddressingMode1LSR(rs, rm):
        def addressing_mode():
            global cpu
            global gprs
            cpu.cycles += 1
            shift = gprs[rs]
            if rs == cpu.PC:
                shift += 4
            shift &= 0xff
            shift_val = gprs[rm]
            if rm == cpu.PC:
                shift_val += 4
            if shift == 0:
                cpu.shifterOperand = shift_val
                cpu.shifterCarryOut = cpu.cpsrC
            elif shift < 32:
                cpu.shifterOperand = shift_val >> shift
                cpu.shifterCarryOut = shift_val & (1 << (shift - 1))
            elif shift == 32:
                cpu.shifterOperand = 0
                cpu.shifterCarryOut = shift_val >> 31
            else:
                cpu.shifterOperand = 0
                cpu.shifterCarryOut = 0
        return addressing_mode

    def constructAddressingMode1ROR(rs, rm):
        def addressing_mode():
            global cpu
            global gprs
            cpu.cycles += 1
            shift = gprs[rs]
            if rs == cpu.PC:
                shift += 4
            shift &= 0xff
            shift_val = gprs[rm]
            if rm == cpu.PC:
                shift_val += 4
            rotate = shift & 0x1f
            if shift == 0:
                cpu.shifterOperand = shift_val
                cpu.shifterCarryOut = cpu.cpsrC
            elif rotate:
                cpu.shifterOperand = (gprs[rm] >> rotate) | (gprs[rm] << (32 - rotate))
                cpu.shifterCarryOut = shift_val & (1 << (rotate - 1))
            else:
                cpu.shifterOperand = shift_val
                cpu.shifterCarryOut = shift_val >> 31
        return addressing_mode

    def constructAddressingMode23Immediate(instruction, immediate, condOp):
        rn = (instruction & 0x000f0000) >> 16
        return addressingMode23Immediate[(instruction & 0x01a00000) >> 21](rn, immediate, condOp)

    def constructAddressingMode23Register(instruction, rm, condOp):
        rn = (instruction & 0x000f0000) >> 16
        return addressingMode23Register[(instruction & 0x01a00000) >> 21](rn, rm, condOp)

    def constructAddressingMode2RegisterShifted(instruction, shiftOp, condOp):
        rn = (instruction & 0x000f0000) >> 16
        return addressingMode2RegisterShifted[(instruction & 0x01a00000) >> 21](rn, shiftOp, condOp)

    def constructAddressingMode4(immediate, rn):
        def addressing_mode():
            global cpu
            global gprs
            addr = gprs[rn] + immediate
            return addr
        return addressing_mode

    def constructAddressingMode4Writeback(immediate, offset, rn, overlap):
        def addressing_mode(write_initial):
            global cpu
            global gprs
            addr = gprs[rn] + immediate
            if write_initial and overlap:
                cpu.mmu.store32(gprs[rn] + immediate - 4, gprs[rn])
            gprs[rn] += offset
            return addr
        return addressing_mode

    def constructADC(rd, rn, shiftOp, condOp):
        def adc():
            global cpu
            global gprs
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            shiftOp()
            shifter_operand = (cpu.shifterOperand & 0xffffffff) + int(cpu.cpsrC)
            gprs[rd] = (gprs[rn] & 0xffffffff) + shifter_operand
        return adc

    def constructADCS(rd, rn, shiftOp, condOp):
        def adcs():
            global cpu
            global gprs
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            shiftOp()
            shifter_operand = (cpu.shifterOperand & 0xffffffff) + int(cpu.cpsrC)
            d = (gprs[rn] & 0xffffffff) + shifter_operand
            if rd == cpu.PC and cpu.hasSPSR():
                cpu.unpackCPSR(cpu.spsr)
            else:
                cpu.cpsrN = d >> 31
                cpu.cpsrZ = not (d & 0xffffffff)
                cpu.cpsrC = d > 0xffffffff
                cpu.cpsrV = (gprs[rn] >> 31 == shifter_operand >> 31 and
                            gprs[rn] >> 31 != d >> 31 and
                            shifter_operand >> 31 != d >> 31)
            gprs[rd] = d
        return adcs

    def constructADD(rd, rn, shiftOp, condOp):
        def add():
            global cpu
            global gprs
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            shiftOp()
            gprs[rd] = (gprs[rn] & 0xffffffff) + (cpu.shifterOperand & 0xffffffff)
        return add

    def constructADDS(rd, rn, shiftOp, condOp):
        def adds():
            global cpu
            global gprs
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            shiftOp()
            d = (gprs[rn] & 0xffffffff) + (cpu.shifterOperand & 0xffffffff)
            if rd == cpu.PC and cpu.hasSPSR():
                cpu.unpackCPSR(cpu.spsr)
            else:
                cpu.cpsrN = d >> 31
                cpu.cpsrZ = not (d & 0xffffffff)
                cpu.cpsrC = d > 0xffffffff
                cpu.cpsrV = (gprs[rn] >> 31 == cpu.shifterOperand >> 31 and
                            gprs[rn] >> 31 != d >> 31 and
                            cpu.shifterOperand >> 31 != d >> 31)
            gprs[rd] = d
        return adds

    def constructAND(rd, rn, shiftOp, condOp):
        def and_():
            global cpu
            global gprs
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            shiftOp()
            gprs[rd] = gprs[rn] & cpu.shifterOperand
        return and_

    def constructANDS(rd, rn, shiftOp, condOp):
        def ands():
            global cpu
            global gprs
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            shiftOp()
            gprs[rd] = gprs[rn] & cpu.shifterOperand
            if rd == cpu.PC and cpu.hasSPSR():
                cpu.unpackCPSR(cpu.spsr)
            else:
                cpu.cpsrN = gprs[rd] >> 31
                cpu.cpsrZ = not (gprs[rd] & 0xffffffff)
                cpu.cpsrC = cpu.shifterCarryOut
        return ands

    def constructB(immediate, condOp):
        def b():
            global cpu
            global gprs
            if condOp and not condOp():
                cpu.mmu.waitPrefetch32(gprs[cpu.PC])
                return
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            gprs[cpu.PC] += immediate
        return b

    def constructBIC(rd, rn, shiftOp, condOp):
        def bic():
            global cpu
            global gprs
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            shiftOp()
            gprs[rd] = gprs[rn] & ~cpu.shifterOperand
        return bic

    def constructBICS(rd, rn, shiftOp, condOp):
        def bics():
            global cpu
            global gprs
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            shiftOp()
            gprs[rd] = gprs[rn] & ~cpu.shifterOperand
            if rd == cpu.PC and cpu.hasSPSR():
                cpu.unpackCPSR(cpu.spsr)
            else:
                cpu.cpsrN = gprs[rd] >> 31
                cpu.cpsrZ = not (gprs[rd] & 0xffffffff)
                cpu.cpsrC = cpu.shifterCarryOut
        return bics

    def constructBL(immediate, condOp):
        def bl():
            global cpu
            global gprs
            if condOp and not condOp():
                cpu.mmu.waitPrefetch32(gprs[cpu.PC])
                return
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            gprs[cpu.LR] = gprs[cpu.PC] - 4
            gprs[cpu.PC] += immediate
        return bl

    def constructBX(rm, condOp):
        def bx():
            global cpu
            global gprs
            if condOp and not condOp():
                cpu.mmu.waitPrefetch32(gprs[cpu.PC])
                return
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            cpu.switchExecMode(gprs[rm] & 0x00000001)
            gprs[cpu.PC] = gprs[rm] & 0xfffffffe
        return bx

    def constructCMN(rd, rn, shiftOp, condOp):
        def cmn():
            global cpu
            global gprs
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            shiftOp()
            alu_out = (gprs[rn] & 0xffffffff) + (cpu.shifterOperand & 0xffffffff)
            cpu.cpsrN = alu_out >> 31
            cpu.cpsrZ = not (alu_out & 0xffffffff)
            cpu.cpsrC = alu_out > 0xffffffff
            cpu.cpsrV = (gprs[rn] >> 31 == cpu.shifterOperand >> 31 and
                        gprs[rn] >> 31 != alu_out >> 31 and
                        cpu.shifterOperand >> 31 != alu_out >> 31)
        return cmn

    def constructCMP(rd, rn, shiftOp, condOp):
        def cmp():
            global cpu
            global gprs
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            shiftOp()
            alu_out = gprs[rn] - cpu.shifterOperand
            cpu.cpsrN = alu_out >> 31
            cpu.cpsrZ = not (alu_out & 0xffffffff)
            cpu.cpsrC = gprs[rn] & 0xffffffff >= cpu.shifterOperand & 0xffffffff
            cpu.cpsrV = (gprs[rn] >> 31 != cpu.shifterOperand >> 31 and
                        gprs[rn] >> 31 != alu_out >> 31)
        return cmp

    def constructEOR(rd, rn, shiftOp, condOp):
        def eor():
            global cpu
            global gprs
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            shiftOp()
            gprs[rd] = gprs[rn] ^ cpu.shifterOperand
        return eor

    def constructEORS(rd, rn, shiftOp, condOp):
        def eors():
            global cpu
            global gprs
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            shiftOp()
            gprs[rd] = gprs[rn] ^ cpu.shifterOperand
            if rd == cpu.PC and cpu.hasSPSR():
                cpu.unpackCPSR(cpu.spsr)
            else:
                cpu.cpsrN = gprs[rd] >> 31
                cpu.cpsrZ = not (gprs[rd] & 0xffffffff)
                cpu.cpsrC = cpu.shifterCarryOut
        return eors

    def constructLDM(rs, address, condOp):
        def ldm():
            global cpu
            global gprs
            global mmu
            mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            addr = address(False)
            total = 0
            m, i = rs, 0
            while m:
                if m & 1:
                    gprs[i] = mmu.load32(addr & 0xfffffffc)
                    addr += 4
                    total += 1
                m >>= 1
                i += 1
            mmu.waitMulti32(addr, total)
            cpu.cycles += 1
        return ldm
    
    def constructLDMS(rs, address, condOp):
        cpu = self.cpu
        gprs = cpu.gprs
        mmu = cpu.mmu
        def ldms():
            mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            addr = address(False)
            total = 0
            mode = cpu.mode
            cpu.switchMode(cpu.MODE_SYSTEM)
            m, i = rs, 0
            while m:
                if m & 1:
                    gprs[i] = mmu.load32(addr & 0xfffffffc)
                    addr += 4
                    total += 1
                m >>= 1
                i += 1
            cpu.switchMode(mode)
            mmu.waitMulti32(addr, total)
            cpu.cycles += 1
        return ldms

    def constructLDR(rd, address, condOp):
        cpu = self.cpu
        gprs = cpu.gprs
        def ldr():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            addr = address()
            gprs[rd] = cpu.mmu.load32(addr)
            cpu.mmu.wait32(addr)
            cpu.cycles += 1
        return ldr

    def constructLDRB(rd, address, condOp):
        cpu = self.cpu
        gprs = cpu.gprs
        def ldrb():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            addr = address()
            gprs[rd] = cpu.mmu.loadU8(addr)
            cpu.mmu.wait(addr)
            cpu.cycles += 1
        return ldrb

    def constructLDRH(rd, address, condOp):
        cpu = self.cpu
        gprs = cpu.gprs
        def ldrh():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            addr = address()
            gprs[rd] = cpu.mmu.loadU16(addr)
            cpu.mmu.wait(addr)
            cpu.cycles += 1
        return ldrh

    def constructLDRSB(rd, address, condOp):
        cpu = self.cpu
        gprs = cpu.gprs
        def ldrsb():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            addr = address()
            gprs[rd] = cpu.mmu.load8(addr)
            cpu.mmu.wait(addr)
            cpu.cycles += 1
        return ldrsb

    def constructLDRSH(rd, address, condOp):
        cpu = self.cpu
        gprs = cpu.gprs
        def ldrsh():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            addr = address()
            gprs[rd] = cpu.mmu.load16(addr)
            cpu.mmu.wait(addr)
            cpu.cycles += 1
        return ldrsh

    def constructMLA(rd, rn, rs, rm, condOp):
        cpu = self.cpu
        gprs = cpu.gprs
        def mla():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            cpu.cycles += 1
            cpu.mmu.waitMul(rs)
            if gprs[rm] & 0xffff0000 and gprs[rs] & 0xffff0000:
                hi = ((gprs[rm] & 0xffff0000) * gprs[rs]) & 0xffffffff
                lo = ((gprs[rm] & 0x0000ffff) * gprs[rs]) & 0xffffffff
                gprs[rd] = (hi + lo + gprs[rn]) & 0xffffffff
            else:
                gprs[rd] = gprs[rm] * gprs[rs] + gprs[rn]
        return mla

    def constructMLAS(rd, rn, rs, rm, condOp):
        cpu = self.cpu
        gprs = cpu.gprs
        def mlas():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            cpu.cycles += 1
            cpu.mmu.waitMul(rs)
            if gprs[rm] & 0xffff0000 and gprs[rs] & 0xffff0000:
                hi = ((gprs[rm] & 0xffff0000) * gprs[rs]) & 0xffffffff
                lo = ((gprs[rm] & 0x0000ffff) * gprs[rs]) & 0xffffffff
                gprs[rd] = (hi + lo + gprs[rn]) & 0xffffffff
            else:
                gprs[rd] = gprs[rm] * gprs[rs] + gprs[rn]
            cpu.cpsrN = gprs[rd] >> 31
            cpu.cpsrZ = not (gprs[rd] & 0xffffffff)
        return mlas

    def constructMOV(rd, rn, shiftOp, condOp):
        cpu = self.cpu
        gprs = cpu.gprs
        def mov():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            shiftOp()
            gprs[rd] = cpu.shifterOperand
        return mov

    def constructMOVS(rd, rn, shiftOp, condOp):
        cpu = self.cpu
        gprs = cpu.gprs
        def movs():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            shiftOp()
            gprs[rd] = cpu.shifterOperand
            if rd == cpu.PC and cpu.hasSPSR():
                cpu.unpackCPSR(cpu.spsr)
            else:
                cpu.cpsrN = gprs[rd] >> 31
                cpu.cpsrZ = not (gprs[rd] & 0xffffffff)
                cpu.cpsrC = cpu.shifterCarryOut
        return movs

    def constructMRS(rd, r, condOp):
        cpu = self.cpu
        gprs = cpu.gprs
        def mrs():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            if r:
                gprs[rd] = cpu.spsr
            else:
                gprs[rd] = cpu.packCPSR()
        return mrs

    def constructMSR(rm, r, instruction, immediate, condOp):
        cpu = self.cpu
        gprs = cpu.gprs
        c = instruction & 0x00010000
        f = instruction & 0x00080000
        def msr():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            if instruction & 0x02000000:
                operand = immediate
            else:
                operand = gprs[rm]
            mask = (c and 0x000000ff) | (f and 0xff000000)
            if r:
                mask &= cpu.USER_MASK | cpu.PRIV_MASK | cpu.STATE_MASK
                cpu.spsr = (cpu.spsr & ~mask) | (operand & mask)
            else:
                if mask & cpu.USER_MASK:
                    cpu.cpsrN = operand >> 31
                    cpu.cpsrZ = operand & 0x40000000
                    cpu.cpsrC = operand & 0x20000000
                    cpu.cpsrV = operand & 0x10000000
                if cpu.mode != cpu.MODE_USER and mask & cpu.PRIV_MASK:
                    cpu.switchMode((operand & 0x0000000f) | 0x00000010)
                    cpu.cpsrI = operand & 0x00000080
                    cpu.cpsrF = operand & 0x00000040
        return msr

    def constructMUL(rd, rs, rm, condOp):
        cpu = self.cpu
        gprs = cpu.gprs
        def mul():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            cpu.mmu.waitMul(gprs[rs])
            if gprs[rm] & 0xffff0000 and gprs[rs] & 0xffff0000:
                hi = ((gprs[rm] & 0xffff0000) * gprs[rs]) | 0
                lo = ((gprs[rm] & 0x0000ffff) * gprs[rs]) | 0
                gprs[rd] = hi + lo
            else:
                gprs[rd] = gprs[rm] * gprs[rs]
        return mul

    def constructMULS(rd, rs, rm, condOp):
        cpu = self.cpu
        gprs = cpu.gprs
        def muls():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            cpu.mmu.waitMul(gprs[rs])
            if gprs[rm] & 0xffff0000 and gprs[rs] & 0xffff0000:
                hi = ((gprs[rm] & 0xffff0000) * gprs[rs]) | 0
                lo = ((gprs[rm] & 0x0000ffff) * gprs[rs]) | 0
                gprs[rd] = hi + lo
            else:
                gprs[rd] = gprs[rm] * gprs[rs]
            cpu.cpsrN = gprs[rd] >> 31
            cpu.cpsrZ = not (gprs[rd] & 0xffffffff)
        return muls

    def constructMVN(rd, rn, shiftOp, condOp):
        cpu = self.cpu
        gprs = cpu.gprs
        def mvn():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            shiftOp()
            gprs[rd] = ~cpu.shifterOperand
        return mvn

    def constructMVNS(rd, rn, shiftOp, condOp):
        cpu = self.cpu
        gprs = cpu.gprs
        def mvns():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            shiftOp()
            gprs[rd] = ~cpu.shifterOperand
            if rd == cpu.PC and cpu.hasSPSR():
                cpu.unpackCPSR(cpu.spsr)
            else:
                cpu.cpsrN = gprs[rd] >> 31
                cpu.cpsrZ = not (gprs[rd] & 0xffffffff)
                cpu.cpsrC = cpu.shifterCarryOut
        return mvns

    def constructORR(rd, rn, shiftOp, condOp):
        cpu = self.cpu
        gprs = cpu.gprs
        def orr():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            shiftOp()
            gprs[rd] = gprs[rn] | cpu.shifterOperand
        return orr

    def constructORRS(rd, rn, shiftOp, condOp):
        cpu = self.cpu
        gprs = cpu.gprs
        def orrs():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            shiftOp()
            gprs[rd] = gprs[rn] | cpu.shifterOperand
            if rd == cpu.PC and cpu.hasSPSR():
                cpu.unpackCPSR(cpu.spsr)
            else:
                cpu.cpsrN = gprs[rd] >> 31
                cpu.cpsrZ = not (gprs[rd] & 0xffffffff)
                cpu.cpsrC = cpu.shifterCarryOut
        return orrs

    def constructRSB(rd, rn, shiftOp, condOp):
        cpu = self.cpu
        gprs = cpu.gprs
        def rsb():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            shiftOp()
            gprs[rd] = cpu.shifterOperand - gprs[rn]
        return rsb

    def constructRSBS(rd, rn, shiftOp, condOp):
        cpu = self.cpu
        gprs = cpu.gprs
        def rsbs():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            shiftOp()
            d = cpu.shifterOperand - gprs[rn]
            if rd == cpu.PC and cpu.hasSPSR():
                cpu.unpackCPSR(cpu.spsr)
            else:
                cpu.cpsrN = d >> 31
                cpu.cpsrZ = not (d & 0xffffffff)
                cpu.cpsrC = cpu.shifterOperand >= gprs[rn]
                cpu.cpsrV = (cpu.shifterOperand >> 31) != (gprs[rn] >> 31) and (cpu.shifterOperand >> 31) != (d >> 31)
            gprs[rd] = d
        return rsbs

    def constructRSC(rd, rn, shiftOp, condOp):
        cpu = self.cpu
        gprs = cpu.gprs
        def rsc():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            shiftOp()
            n = (gprs[rn] >> 0) + (not cpu.cpsrC)

            gprs[rd] = (cpu.shifterOperand >> 0) - n

        return rsc

    def constructRSCS(rd, rn, shiftOp, condOp):
        cpu = self.cpu
        gprs = cpu.gprs
        def rscs():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            shiftOp()
            n = (gprs[rn] >> 0) + (not cpu.cpsrC)

            d = (cpu.shifterOperand >> 0) - n

            if rd == cpu.PC and cpu.hasSPSR():
                cpu.unpackCPSR(cpu.spsr)
            else:
                cpu.cpsrN = d >> 31
                cpu.cpsrZ = not (d & 0xffffffff)
                cpu.cpsrC = gprs[rn] >> 0 >= d >> 0
                cpu.cpsrV = (gprs[rn] >> 31) != (cpu.shifterOperand >> 31) and (gprs[rn] >> 31) != (d >> 31)
            gprs[rd] = d
        return rscs

    def constructSBC(rd, rn, shiftOp, condOp):
        cpu = self.cpu
        gprs = cpu.gprs
        def sbc():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            shiftOp()
            shifterOperand = (cpu.shifterOperand >> 0) + (not cpu.cpsrC)
            gprs[rd] = (gprs[rn] >> 0) - shifterOperand
        return sbc

    def constructSBCS(rd, rn, shiftOp, condOp):
        cpu = self.cpu
        gprs = cpu.gprs
        def sbcs():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            shiftOp()
            shifterOperand = (cpu.shifterOperand >> 0) + (not cpu.cpsrC)
            d = (gprs[rn] >> 0) - shifterOperand
            if rd == cpu.PC and cpu.hasSPSR():
                cpu.unpackCPSR(cpu.spsr)
            else:
                cpu.cpsrN = d >> 31
                cpu.cpsrZ = not (d & 0xffffffff)
                cpu.cpsrC = gprs[rn] >> 0 >= d >> 0
                cpu.cpsrV = (gprs[rn] >> 31) != (shifterOperand >> 31) and (gprs[rn] >> 31) != (d >> 31)
            gprs[rd] = d
        return sbcs
def constructSMLAL(cpu, rd, rn, rs, rm, condOp):
    SHIFT_32 = 1 / 0x100000000
    gprs = cpu.gprs
    def inner():
        cpu.mmu.waitPrefetch32(gprs[cpu.PC])
        if condOp and not condOp():
            return
        cpu.cycles += 2
        cpu.mmu.waitMul(rs)
        hi = (gprs[rm] & 0xffff0000) * gprs[rs]
        lo = (gprs[rm] & 0x0000ffff) * gprs[rs]
        carry = (gprs[rn] >> 0) + hi + lo
        gprs[rn] = carry
        gprs[rd] += int(carry * SHIFT_32)
    return inner  # Make sure to properly close the function
    def constructSMLALS(rd, rn, rs, rm, condOp):
        SHIFT_32 = 1 / 0x100000000
        gprs = cpu.gprs
        def inner():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            cpu.cycles += 2
            cpu.mmu.waitMul(rs)
            hi = (gprs[rm] & 0xffff0000) * gprs[rs]
            lo = (gprs[rm] & 0x0000ffff) * gprs[rs]
            carry = (gprs[rn] >> 0) + hi + lo
            gprs[rn] = carry
            gprs[rd] += int(carry * SHIFT_32)
            cpu.cpsrN = gprs[rd] >> 31
            cpu.cpsrZ = not (gprs[rd] & 0xffffffff or gprs[rn] & 0xffffffff)
        return inner

    def constructSMULL(rd, rn, rs, rm, condOp):
        SHIFT_32 = 1 / 0x100000000
        gprs = cpu.gprs
        def inner():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            cpu.cycles += 1
            cpu.mmu.waitMul(gprs[rs])
            hi = ((gprs[rm] & 0xffff0000) >> 0) * (gprs[rs] >> 0)
            lo = ((gprs[rm] & 0x0000ffff) >> 0) * (gprs[rs] >> 0)
            gprs[rn] = ((hi & 0xffffffff) + (lo & 0xffffffff)) & 0xffffffff
            gprs[rd] = int(hi * SHIFT_32 + lo * SHIFT_32)
        return inner

    def constructSMULLS(rd, rn, rs, rm, condOp):
        SHIFT_32 = 1 / 0x100000000
        gprs = cpu.gprs
        def inner():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            cpu.cycles += 1
            cpu.mmu.waitMul(gprs[rs])
            hi = ((gprs[rm] & 0xffff0000) >> 0) * (gprs[rs] >> 0)
            lo = ((gprs[rm] & 0x0000ffff) >> 0) * (gprs[rs] >> 0)
            gprs[rn] = ((hi & 0xffffffff) + (lo & 0xffffffff)) & 0xffffffff
            gprs[rd] = int(hi * SHIFT_32 + lo * SHIFT_32)
            cpu.cpsrN = gprs[rd] >> 31
            cpu.cpsrZ = not (gprs[rd] & 0xffffffff or gprs[rn] & 0xffffffff)
        return inner

    def constructSTM(rs, address, condOp):
        gprs = cpu.gprs
        mmu = cpu.mmu
        def inner():
            if condOp and not condOp():
                mmu.waitPrefetch32(gprs[cpu.PC])
                return
            mmu.wait32(gprs[cpu.PC])
            addr = address(True)
            total = 0
            m, i = rs, 0
            while m:
                if m & 1:
                    mmu.store32(addr, gprs[i])
                    addr += 4
                    total += 1
                m >>= 1
                i += 1
            mmu.waitMulti32(addr, total)
        return inner

    def constructSTMS(rs, address, condOp):
        gprs = cpu.gprs
        mmu = cpu.mmu
        def inner():
            if condOp and not condOp():
                mmu.waitPrefetch32(gprs[cpu.PC])
                return
            mmu.wait32(gprs[cpu.PC])
            mode = cpu.mode
            addr = address(True)
            total = 0
            m, i = rs, 0
            cpu.switchMode(cpu.MODE_SYSTEM)
            while m:
                if m & 1:
                    mmu.store32(addr, gprs[i])
                    addr += 4
                    total += 1
                m >>= 1
                i += 1
            cpu.switchMode(mode)
            mmu.waitMulti32(addr, total)
        return inner

    def constructSTR(rd, address, condOp):
        gprs = cpu.gprs
        def inner():
            if condOp and not condOp():
                cpu.mmu.waitPrefetch32(gprs[cpu.PC])
                return
            addr = address()
            cpu.mmu.store32(addr, gprs[rd])
            cpu.mmu.wait32(addr)
            cpu.mmu.wait32(gprs[cpu.PC])
        return inner

    def constructSTRB(rd, address, condOp):
        gprs = cpu.gprs
        def inner():
            if condOp and not condOp():
                cpu.mmu.waitPrefetch32(gprs[cpu.PC])
                return
            addr = address()
            cpu.mmu.store8(addr, gprs[rd])
            cpu.mmu.wait(addr)
            cpu.mmu.wait32(gprs[cpu.PC])
        return inner

    def constructSTRH(rd, address, condOp):
        gprs = cpu.gprs
        def inner():
            if condOp and not condOp():
                cpu.mmu.waitPrefetch32(gprs[cpu.PC])
                return
            addr = address()
            cpu.mmu.store16(addr, gprs[rd])
            cpu.mmu.wait(addr)
            cpu.mmu.wait32(gprs[cpu.PC])
        return inner

    def constructSUB(rd, rn, shiftOp, condOp):
        gprs = cpu.gprs
        def inner():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            shiftOp()
            gprs[rd] = gprs[rn] - cpu.shifterOperand
        return inner

    def constructSUBS(rd, rn, shiftOp, condOp):
        gprs = cpu.gprs
        def inner():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            shiftOp()
            d = gprs[rn] - cpu.shifterOperand
            if rd == cpu.PC and cpu.hasSPSR():
                cpu.unpackCPSR(cpu.spsr)
            else:
                cpu.cpsrN = d >> 31
                cpu.cpsrZ = not (d & 0xFFFFFFFF)
                cpu.cpsrC = (gprs[rn] >> 0) >= (cpu.shifterOperand >> 0)
                cpu.cpsrV = (gprs[rn] >> 31) != (cpu.shifterOperand >> 31) and (gprs[rn] >> 31) != (d >> 31)
            gprs[rd] = d
        return inner

    def constructSWI(immediate, condOp):
        gprs = cpu.gprs
        def inner():
            if condOp and not condOp():
                cpu.mmu.waitPrefetch32(gprs[cpu.PC])
                return
            cpu.irq.swi32(immediate)
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
        return inner

    def constructSWP(rd, rn, rm, condOp):
        gprs = cpu.gprs
        def inner():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            cpu.mmu.wait32(gprs[rn])
            cpu.mmu.wait32(gprs[rn])
            d = cpu.mmu.load32(gprs[rn])
            cpu.mmu.store32(gprs[rn], gprs[rm])
            gprs[rd] = d
            cpu.cycles += 1
        return inner

    def constructSWPB(rd, rn, rm, condOp):
        gprs = cpu.gprs
        def inner():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            cpu.mmu.wait(gprs[rn])
            cpu.mmu.wait(gprs[rn])
            d = cpu.mmu.load8(gprs[rn])
            cpu.mmu.store8(gprs[rn], gprs[rm])
            gprs[rd] = d
            cpu.cycles += 1
        return inner

    def constructTEQ(rd, rn, shiftOp, condOp):
        gprs = cpu.gprs
        def inner():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            shiftOp()
            aluOut = gprs[rn] ^ cpu.shifterOperand
            cpu.cpsrN = aluOut >> 31
            cpu.cpsrZ = not (aluOut & 0xffffffff)
            cpu.cpsrC = cpu.shifterCarryOut
        return inner

    def constructTST(rd, rn, shiftOp, condOp):
        gprs = cpu.gprs
        def inner():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            shiftOp()
            aluOut = gprs[rn] & cpu.shifterOperand
            cpu.cpsrN = aluOut >> 31
            cpu.cpsrZ = not (aluOut & 0xffffffff)
            cpu.cpsrC = cpu.shifterCarryOut
        return inner

    def constructUMLAL(rd, rn, rs, rm, condOp):
        SHIFT_32 = 1 / 0x100000000
        gprs = cpu.gprs
        def inner():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            cpu.cycles += 2
            cpu.mmu.waitMul(rs)
            hi = ((gprs[rm] & 0xffff0000) >> 0) * (gprs[rs] >> 0)
            lo = (gprs[rm] & 0x0000ffff) * (gprs[rs] >> 0)
            carry = (gprs[rn] >> 0) + hi + lo
            gprs[rn] = carry
            gprs[rd] += carry * SHIFT_32
        return inner

    def constructUMLALS(rd, rn, rs, rm, condOp):
        SHIFT_32 = 1 / 0x100000000
        gprs = cpu.gprs
        def inner():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            cpu.cycles += 2
            cpu.mmu.waitMul(rs)
            hi = ((gprs[rm] & 0xffff0000) >> 0) * (gprs[rs] >> 0)
            lo = (gprs[rm] & 0x0000ffff) * (gprs[rs] >> 0)
            carry = (gprs[rn] >> 0) + hi + lo
            gprs[rn] = carry
            gprs[rd] += carry * SHIFT_32
            cpu.cpsrN = gprs[rd] >> 31
            cpu.cpsrZ = not (gprs[rd] & 0xffffffff or gprs[rn] & 0xffffffff)
        return inner

    def constructUMULL(rd, rn, rs, rm, condOp):
        SHIFT_32 = 1 / 0x100000000
        gprs = cpu.gprs
        def inner():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            cpu.cycles += 1
            cpu.mmu.waitMul(gprs[rs])
            hi = ((gprs[rm] & 0xffff0000) >> 0) * (gprs[rs] >> 0)
            lo = ((gprs[rm] & 0x0000ffff) >> 0) * (gprs[rs] >> 0)
            gprs[rn] = ((hi & 0xffffffff) + (lo & 0xffffffff)) & 0xffffffff
            gprs[rd] = (hi * SHIFT_32 + lo * SHIFT_32) >> 0
        return inner

    def constructUMULLS(rd, rn, rs, rm, condOp):
        SHIFT_32 = 1 / 0x100000000
        gprs = cpu.gprs
        def inner():
            cpu.mmu.waitPrefetch32(gprs[cpu.PC])
            if condOp and not condOp():
                return
            cpu.cycles += 1
            cpu.mmu.waitMul(gprs[rs])
            hi = ((gprs[rm] & 0xffff0000) >> 0) * (gprs[rs] >> 0)
            lo = ((gprs[rm] & 0x0000ffff) >> 0) * (gprs[rs] >> 0)
            gprs[rn] = ((hi & 0xffffffff) + (lo & 0xffffffff)) & 0xffffffff
            gprs[rd] = (hi * SHIFT_32 + lo * SHIFT_32) >> 0
            cpu.cpsrN = gprs[rd] >> 31
            cpu.cpsrZ = not (gprs[rd] & 0xffffffff or gprs[rn] & 0xffffffff)
        return inner     