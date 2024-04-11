from arm import ARMCoreArm
from thumb import ARMCoreThumb
class ARMCore:
    def __init__(self):
        self.cycles = 0
        self.SP = 13
        self.LR = 14
        self.PC = 15

        self.MODE_ARM = 0
        self.MODE_THUMB = 1

        self.MODE_USER = 0x10
        self.MODE_FIQ = 0x11
        self.MODE_IRQ = 0x12
        self.MODE_SUPERVISOR = 0x13
        self.MODE_ABORT = 0x17
        self.MODE_UNDEFINED = 0x1b
        self.MODE_SYSTEM = 0x1f

        self.BANK_NONE = 0
        self.BANK_FIQ = 1
        self.BANK_IRQ = 2
        self.BANK_SUPERVISOR = 3
        self.BANK_ABORT = 4
        self.BANK_UNDEFINED = 5

        self.UNALLOC_MASK = 0x0fffff00
        self.USER_MASK = 0xf0000000
        self.PRIV_MASK = 0x000000cf
        self.STATE_MASK = 0x00000020

        self.WORD_SIZE_ARM = 4
        self.WORD_SIZE_THUMB = 2

        self.BASE_RESET = 0x00000000
        self.BASE_UNDEF = 0x00000004
        self.BASE_SWI = 0x00000008
        self.BASE_PABT = 0x0000000c
        self.BASE_DABT = 0x00000010
        self.BASE_IRQ = 0x00000018
        self.BASE_FIQ = 0x0000001c

        self.armCompiler = ARMCoreArm(self)
        self.thumbCompiler = ARMCoreThumb(self)
        #self.generateConds()

        self.gprs = [0] * 16

    def resetCPU(self, startOffset):
        for i in range(self.PC):
            self.gprs[i] = 0
        self.gprs[self.PC] = startOffset + self.WORD_SIZE_ARM

        self.loadInstruction = self.loadInstructionArm
        self.execMode = self.MODE_ARM
        self.instructionWidth = self.WORD_SIZE_ARM

        self.mode = self.MODE_SYSTEM

        self.cpsrI = False
        self.cpsrF = False

        self.cpsrV = False
        self.cpsrC = False
        self.cpsrZ = False
        self.cpsrN = False

        self.bankedRegisters = [
            [0] * 7,
            [0] * 7,
            [0] * 2,
            [0] * 2,
            [0] * 2,
            [0] * 2
        ]
        self.spsr = 0
        self.bankedSPSRs = [0] * 6

        self.cycles = 0

        self.shifterOperand = 0
        self.shifterCarryOut = 0

        self.page = None
        self.pageId = 0
        self.pageRegion = -1

        self.instruction = None

        self.irq.clear()

        gprs = self.gprs
        mmu = self.mmu

    def step(self):
        self.instructionWidth = self.WORD_SIZE_ARM
        address = self.gprs[self.PC] - self.instructionWidth
        instruction = self.load_instruction_arm(address)
        gprs[self.PC] += self.instructionWidth
        self.conditionPassed = True
        instruction()

        if not instruction.writesPC:
            if self.instruction != None:
                if instruction.next == None or instruction.next.page.invalid:
                    instruction.next = self.loadInstruction(gprs[self.PC] - self.instructionWidth)
                self.instruction = instruction.next
        else:
            if self.conditionPassed:
                pc = gprs[self.PC] & 0xfffffffe
                if self.execMode == self.MODE_ARM:
                    mmu.wait32(pc)
                    mmu.waitPrefetch32(pc)
                else:
                    mmu.wait(pc)
                    mmu.waitPrefetch(pc)
                gprs[self.PC] += self.instructionWidth
                if not instruction.fixedJump:
                    self.instruction = None
                elif self.instruction != None:
                    if instruction.next == None or instruction.next.page.invalid:
                        instruction.next = self.loadInstruction(gprs[self.PC] - self.instructionWidth)
                    self.instruction = instruction.next
            else:
                self.instruction = None
        self.irq.updateTimers()
		#self.step = step
    def freeze(self):
        return {
            'gprs': self.gprs[:],
            'mode': self.mode,
            'cpsrI': self.cpsrI,
            'cpsrF': self.cpsrF,
            'cpsrV': self.cpsrV,
            'cpsrC': self.cpsrC,
            'cpsrZ': self.cpsrZ,
            'cpsrN': self.cpsrN,
            'bankedRegisters': [
                self.bankedRegisters[0][:],
                self.bankedRegisters[1][:],
                self.bankedRegisters[2][:],
                self.bankedRegisters[3][:],
                self.bankedRegisters[4][:],
                self.bankedRegisters[5][:]
            ],
            'spsr': self.spsr,
            'bankedSPSRs': self.bankedSPSRs[:],
            'cycles': self.cycles
        }
        
    def defrost(frost):
        self.instruction = None
        self.page = None
        self.pageId = 0
        self.pageRegion = -1
        self.gprs[0] = frost.gprs[0]
        self.gprs[1] = frost.gprs[1]
        self.gprs[2] = frost.gprs[2]
        self.gprs[3] = frost.gprs[3]
        self.gprs[4] = frost.gprs[4]
        self.gprs[5] = frost.gprs[5]
        self.gprs[6] = frost.gprs[6]
        self.gprs[7] = frost.gprs[7]
        self.gprs[8] = frost.gprs[8]
        self.gprs[9] = frost.gprs[9]
        self.gprs[10] = frost.gprs[10]
        self.gprs[11] = frost.gprs[11]
        self.gprs[12] = frost.gprs[12]
        self.gprs[13] = frost.gprs[13]
        self.gprs[14] = frost.gprs[14]
        self.gprs[15] = frost.gprs[15]
        self.mode = frost.mode
        self.cpsrI = frost.cpsrI
        self.cpsrF = frost.cpsrF
        self.cpsrV = frost.cpsrV
        self.cpsrC = frost.cpsrC
        self.cpsrZ = frost.cpsrZ
        self.cpsrN = frost.cpsrN
        self.bankedRegisters[0][0] = frost.bankedRegisters[0][0]
        self.bankedRegisters[0][1] = frost.bankedRegisters[0][1]
        self.bankedRegisters[0][2] = frost.bankedRegisters[0][2]
        self.bankedRegisters[0][3] = frost.bankedRegisters[0][3]
        self.bankedRegisters[0][4] = frost.bankedRegisters[0][4]
        self.bankedRegisters[0][5] = frost.bankedRegisters[0][5]
        self.bankedRegisters[0][6] = frost.bankedRegisters[0][6]
        self.bankedRegisters[1][0] = frost.bankedRegisters[1][0]
        self.bankedRegisters[1][1] = frost.bankedRegisters[1][1]
        self.bankedRegisters[1][2] = frost.bankedRegisters[1][2]
        self.bankedRegisters[1][3] = frost.bankedRegisters[1][3]
        self.bankedRegisters[1][4] = frost.bankedRegisters[1][4]
        self.bankedRegisters[1][5] = frost.bankedRegisters[1][5]
        self.bankedRegisters[1][6] = frost.bankedRegisters[1][6]
        self.bankedRegisters[2][0] = frost.bankedRegisters[2][0]
        self.bankedRegisters[2][1] = frost.bankedRegisters[2][1]
        self.bankedRegisters[3][0] = frost.bankedRegisters[3][0]
        self.bankedRegisters[3][1] = frost.bankedRegisters[3][1]
        self.bankedRegisters[4][0] = frost.bankedRegisters[4][0]
        self.bankedRegisters[4][1] = frost.bankedRegisters[4][1]
        self.bankedRegisters[5][0] = frost.bankedRegisters[5][0]
        self.bankedRegisters[5][1] = frost.bankedRegisters[5][1]
        self.spsr = frost.spsr
        self.bankedSPSRs[0] = frost.bankedSPSRs[0]
        self.bankedSPSRs[1] = frost.bankedSPSRs[1]
        self.bankedSPSRs[2] = frost.bankedSPSRs[2]
        self.bankedSPSRs[3] = frost.bankedSPSRs[3]
        self.bankedSPSRs[4] = frost.bankedSPSRs[4]
        self.bankedSPSRs[5] = frost.bankedSPSRs[5]
        self.cycles = frost.cycles

	
    def fetch_page(self,address):
        self.mmu.invalidate_caches(address & 0xFF000000)
        global page, pageRegion, pageId  # Assuming these are global variables
        region = address >> mmu.BASE_OFFSET
        pageId = mmu.addressToPage(region, address & mmu.OFFSET_MASK)
        if region == pageRegion and pageId == pageId and not page.invalid:
            pageMask = mmu.memory[region].PAGE_MASK
            pageRegion = region
            pageId = pageId
            page = mmu.accessPage(region, pageId)

    def load_instruction_arm(self,address):
        global page, page_mask  # Assuming these are global variables
        next_inst = None
        self.fetch_page(address)
        offset = (address & page_mask) >> 2
        next_inst = page.arm[offset]
        if next_inst:
            return next_inst
        instruction = mmu.load32(address)
        next_inst = compile_arm(instruction)
        next_inst.next = None
        next_inst.page = page
        next_inst.address = address
        next_inst.opcode = instruction
        page.arm[offset] = next_inst
        return next_inst


    def loadInstructionThumb(address):
        next = None
        fetchPage(address)
        offset = (address & pageMask) >> 1
        next = page.thumb[offset]
        if next:
            return next
        instruction = mmu.load16(address)
        next = compileThumb(instruction)
        next.next = None
        next.page = page
        next.address = address
        next.opcode = instruction
        page.thumb[offset] = next
        return next

    def selectBank(mode):
        if mode == MODE_USER or mode == MODE_SYSTEM:
            return BANK_NONE
        elif mode == MODE_FIQ:
            return BANK_FIQ
        elif mode == MODE_IRQ:
            return BANK_IRQ
        elif mode == MODE_SUPERVISOR:
            return BANK_SUPERVISOR
        elif mode == MODE_ABORT:
            return BANK_ABORT
        elif mode == MODE_UNDEFINED:
            return BANK_UNDEFINED
        else:
            raise Exception("Invalid user mode passed to selectBank")

    def switchExecMode(newMode):
        if execMode != newMode:
            execMode = newMode
            if newMode == MODE_ARM:
                instructionWidth = WORD_SIZE_ARM
                loadInstruction = loadInstructionArm
            else:
                instructionWidth = WORD_SIZE_THUMB
                loadInstruction = loadInstructionThumb

    def switchMode(newMode):
        if newMode == mode:
            return
        if newMode != MODE_USER or newMode != MODE_SYSTEM:
            newBank = selectBank(newMode)
            oldBank = selectBank(mode)
            if newBank != oldBank:
                if newMode == MODE_FIQ or mode == MODE_FIQ:
                    oldFiqBank = (oldBank == BANK_FIQ) + 0
                    newFiqBank = (newBank == BANK_FIQ) + 0
                    bankedRegisters[oldFiqBank][2] = gprs[8]
                    bankedRegisters[oldFiqBank][3] = gprs[9]
                    bankedRegisters[oldFiqBank][4] = gprs[10]
                    bankedRegisters[oldFiqBank][5] = gprs[11]
                    bankedRegisters[oldFiqBank][6] = gprs[12]
                    gprs[8] = bankedRegisters[newFiqBank][2]
                    gprs[9] = bankedRegisters[newFiqBank][3]
                    gprs[10] = bankedRegisters[newFiqBank][4]
                    gprs[11] = bankedRegisters[newFiqBank][5]
                    gprs[12] = bankedRegisters[newFiqBank][6]
                bankedRegisters[oldBank][0] = gprs[SP]
                bankedRegisters[oldBank][1] = gprs[LR]
                gprs[SP] = bankedRegisters[newBank][0]
                gprs[LR] = bankedRegisters[newBank][1]

                bankedSPSRs[oldBank] = spsr
                spsr = bankedSPSRs[newBank]
        mode = newMode

    def packCPSR():
        return (
            mode |
            (execMode << 5) |
            (cpsrF << 6) |
            (cpsrI << 7) |
            (cpsrN << 31) |
            (cpsrZ << 30) |
            (cpsrC << 29) |
            (cpsrV << 28)
        )

    def unpackCPSR(spsr):
        switchMode(spsr & 0x0000001f)
        switchExecMode(spsr & 0x00000020)
        cpsrF = spsr & 0x00000040
        cpsrI = spsr & 0x00000080
        cpsrN = spsr & 0x80000000
        cpsrZ = spsr & 0x40000000
        cpsrC = spsr & 0x20000000
        cpsrV = spsr & 0x10000000

        irq.testIRQ()

    def hasSPSR():
        return mode != MODE_SYSTEM and mode != MODE_USER

    def raiseIRQ():
        if cpsrI:
            return
        cpsr = packCPSR()
        instructionWidth = instructionWidth
        switchMode(MODE_IRQ)
        spsr = cpsr
        gprs[LR] = gprs[PC] - instructionWidth + 4
        gprs[PC] = BASE_IRQ + WORD_SIZE_ARM
        instruction = None
        switchExecMode(MODE_ARM)
        cpsrI = True

    def raiseTrap():
        cpsr = packCPSR()
        instructionWidth = instructionWidth
        switchMode(MODE_SUPERVISOR)
        spsr = cpsr
        gprs[LR] = gprs[PC] - instructionWidth
        gprs[PC] = BASE_SWI + WORD_SIZE_ARM
        instruction = None
        switchExecMode(MODE_ARM)
        cpsrI = True

    def badOp(instruction):
        def func():
            raise Exception("Illegal instruction: 0x" + instruction.toString(16))
        func.writesPC = True
        func.fixedJump = False
        return func

    def generate_conds(cpsrZ, cpsrC, cpsrN, cpsrV):
        conds = [
        # EQ
        lambda: cpsrZ,
        # NE
        lambda: not cpsrZ,
        # CS
        lambda: cpsrC,
        # CC
        lambda: not cpsrC,
        # MI
        lambda: cpsrN,
        # PL
        lambda: not cpsrN,
        # VS
        lambda: cpsrV,
        # VC
        lambda: not cpsrV,
        # HI
        lambda: cpsrC and not cpsrZ,
        # LS
        lambda: not cpsrC or cpsrZ,
        # GE
        lambda: not (cpsrN ^ cpsrV),
        # LT
        lambda: cpsrN ^ cpsrV,
        # GT
        lambda: not cpsrZ and not (cpsrN ^ cpsrV),
        # LE
        lambda: cpsrZ or (cpsrN ^ cpsrV),
        # AL
        None,
        None
        ]
        return conds
            
    def barrel_shift_immediate(shift_type, immediate, rm):
        cpu = self
        gprs = self.gprs
        shift_op = self.bad_op
        if shift_type == 0x00000000:
            # LSL
            if immediate:
                def shift_op():
                    cpu.shifter_operand = gprs[rm] << immediate
                    cpu.shifter_carry_out = gprs[rm] & (1 << (32 - immediate))
            else:
                # This boils down to no shift
                def shift_op():
                    cpu.shifter_operand = gprs[rm]
                    cpu.shifter_carry_out = cpu.cpsr_c
            return shift_op
        elif shift_type == 0x00000020:
            # LSR
            if immediate:
                def shift_op():
                    cpu.shifter_operand = gprs[rm] >> immediate
                    cpu.shifter_carry_out = gprs[rm] & (1 << (immediate - 1))
            else:
                def shift_op():
                    cpu.shifter_operand = 0
                    cpu.shifter_carry_out = gprs[rm] & 0x80000000
            return shift_op
        elif shift_type == 0x00000040:
            # ASR
            if immediate:
                def shift_op():
                    cpu.shifter_operand = gprs[rm] >> immediate
                    cpu.shifter_carry_out = gprs[rm] & (1 << (immediate - 1))
            else:
                def shift_op():
                    cpu.shifter_carry_out = gprs[rm] & 0x80000000
                    if cpu.shifter_carry_out:
                        cpu.shifter_operand = 0xffffffff
                    else:
                        cpu.shifter_operand = 0
            return shift_op
        elif shift_type == 0x00000060:
            # ROR
            if immediate:
                def shift_op():
                    cpu.shifter_operand = (gprs[rm] >> immediate) | (gprs[rm] << (32 - immediate))
                    cpu.shifter_carry_out = gprs[rm] & (1 << (immediate - 1))
            else:
                # RRX
                def shift_op():
                    cpu.shifter_operand = (cpu.cpsr_c << 31) | (gprs[rm] >> 1)
                    cpu.shifter_carry_out = gprs[rm] & 0x00000001
            return shift_op
        else:
            return shift_op

    def compile_arm(instruction):
        op = bad_op(instruction)
        i = instruction & 0x0e000000
        cpu = self
        gprs = self.gprs

        condOp = conds[(instruction & 0xf0000000) >> 28]
        if (instruction & 0x0ffffff0) == 0x012fff10:
            # BX
            rm = instruction & 0xf
            op = arm_compiler.construct_bx(rm, condOp)
            op.writesPC = True
            op.fixedJump = False
        elif not (instruction & 0x0c000000) and (i == 0x02000000 or (instruction & 0x00000090) != 0x00000090):
            opcode = instruction & 0x01e00000
            s = instruction & 0x00100000
            shiftsRs = False
            if (opcode & 0x01800000) == 0x01000000 and not s:
                r = instruction & 0x00400000
                if (instruction & 0x00b0f000) == 0x0020f000:
                    # MSR
                    rm = instruction & 0x0000000f
                    immediate = instruction & 0x000000ff
                    rotateImm = (instruction & 0x00000f00) >> 7
                    immediate = (immediate >> rotateImm) | (immediate << (32 - rotateImm))
                    op = arm_compiler.construct_msr(rm, r, instruction, immediate, condOp)
                    op.writesPC = False
                elif (instruction & 0x00bf0000) == 0x000f0000:
                    # MRS
                    rd = (instruction & 0x0000f000) >> 12
                    op = arm_compiler.construct_mrs(rd, r, condOp)
                    op.writesPC = rd == PC
            else:
                # Data processing/FSR transfer
                rn = (instruction & 0x000f0000) >> 16
                rd = (instruction & 0x0000f000) >> 12

                # Parse shifter operand
                shiftType = instruction & 0x00000060
                rm = instruction & 0x0000000f
                shiftOp = lambda: raise_exception("BUG: invalid barrel shifter")
                if instruction & 0x02000000:
                    immediate = instruction & 0x000000ff
                    rotate = (instruction & 0x00000f00) >> 7
                    if not rotate:
                        shiftOp = arm_compiler.construct_addressing_mode1_immediate(immediate)
                    else:
                        shiftOp = arm_compiler.construct_addressing_mode1_immediate_rotate(immediate, rotate)
                elif instruction & 0x00000010:
                    rs = (instruction & 0x00000f00) >> 8
                    shiftsRs = True
                    if shiftType == 0x00000000:
                        # LSL
                        shiftOp = arm_compiler.construct_addressing_mode1_lsl(rs, rm)
                    elif shiftType == 0x00000020:
                        # LSR
                        shiftOp = arm_compiler.construct_addressing_mode1_lsr(rs, rm)
                    elif shiftType == 0x00000040:
                        # ASR
                        shiftOp = arm_compiler.construct_addressing_mode1_asr(rs, rm)
                    elif shiftType == 0x00000060:
                        # ROR
                        shiftOp = arm_compiler.construct_addressing_mode1_ror(rs, rm)
                else:
                    immediate = (instruction & 0x00000f80) >> 7
                    shiftOp = barrel_shift_immediate(shiftType, immediate, rm)

                if opcode == 0x00000000:
                    # AND
                    if s:
                        op = arm_compiler.construct_ands(rd, rn, shiftOp, condOp)
                    else:
                        op = arm_compiler.construct_and(rd, rn, shiftOp, condOp)
                elif opcode == 0x00200000:
                    # EOR
                    if s:
                        op = arm_compiler.construct_eors(rd, rn, shiftOp, condOp)
                    else:
                        op = arm_compiler.construct_eor(rd, rn, shiftOp, condOp)
                elif opcode == 0x00400000:
                    # SUB
                    if s:
                        op = arm_compiler.construct_subs(rd, rn, shiftOp, condOp)
                    else:
                        op = arm_compiler.construct_sub(rd, rn, shiftOp, condOp)
                elif opcode == 0x00600000:
                    # RSB
                    if s:
                        op = arm_compiler.construct_rsbs(rd, rn, shiftOp, condOp)
                    else:
                        op = arm_compiler.construct_rsb(rd, rn, shiftOp, condOp)
                elif opcode == 0x00800000:
                    # ADD
                    if s:
                        op = arm_compiler.construct_adds(rd, rn, shiftOp, condOp)
                    else:
                        op = arm_compiler.construct_add(rd, rn, shiftOp, condOp)
                elif opcode == 0x00a00000:
                    # ADC
                    if s:
                        op = arm_compiler.construct_adcs(rd, rn, shiftOp, condOp)
                    else:
                        op = arm_compiler.construct_adc(rd, rn, shiftOp, condOp)
                elif opcode == 0x00c00000:
                    # SBC
                    if s:
                        op = arm_compiler.construct_sbcs(rd, rn, shiftOp, condOp)
                    else:
                        op = arm_compiler.construct_sbc(rd, rn, shiftOp, condOp)
                elif opcode == 0x00e00000:
                    # RSC
                    if s:
                        op = arm_compiler.construct_rscs(rd, rn, shiftOp, condOp)
                    else:
                        op = arm_compiler.construct_rsc(rd, rn, shiftOp, condOp)
                elif opcode == 0x01000000:
                    # TST
                    op = arm_compiler.construct_tst(rd, rn, shiftOp, condOp)
                elif opcode == 0x01200000:
                    # TEQ
                    op = arm_compiler.construct_teq(rd, rn, shiftOp, condOp)
                elif opcode == 0x01400000:
                    # CMP
                    op = arm_compiler.construct_cmp(rd, rn, shiftOp, condOp)
                elif opcode == 0x01600000:
                    # CMN
                    op = arm_compiler.construct_cmn(rd, rn, shiftOp, condOp)
                elif opcode == 0x01800000:
                    # ORR
                    if s:
                        op = arm_compiler.construct_orrs(rd, rn, shiftOp, condOp)
                    else:
                        op = arm_compiler.construct_orr(rd, rn, shiftOp, condOp)
                elif opcode == 0x01a00000:
                    # MOV
                    if s:
                        op = arm_compiler.construct_movs(rd, rn, shiftOp, condOp)
                    else:
                        op = arm_compiler.construct_mov(rd, rn, shiftOp, condOp)
                elif opcode == 0x01c00000:
                    # BIC
                    if s:
                        op = arm_compiler.construct_bics(rd, rn, shiftOp, condOp)
                    else:
                        op = arm_compiler.construct_bic(rd, rn, shiftOp, condOp)
                elif opcode == 0x01e00000:
                    # MVN
                    if s:
                        op = arm_compiler.construct_mvns(rd, rn, shiftOp, condOp)
                    else:
                        op = arm_compiler.construct_mvn(rd, rn, shiftOp, condOp)

                op.writesPC = rd == PC
        elif (instruction & 0x0fb00ff0) == 0x01000090:
            # Single data swap
            rm = instruction & 0x0000000f
            rd = (instruction >> 12) & 0x0000000f
            rn = (instruction >> 16) & 0x0000000f
            if instruction & 0x00400000:
                op = arm_compiler.construct_swpb(rd, rn, rm, condOp)
            else:
                op = arm_compiler.construct_swp(rd, rn, rm, condOp)
            op.writesPC = rd == PC
        else:
            if i == 0x00000000:
                if (instruction & 0x010000f0) == 0x00000090:
                    # Multiplies
                    rd = (instruction & 0x000f0000) >> 16
                    rn = (instruction & 0x0000f000) >> 12
                    rs = (instruction & 0x00000f00) >> 8
                    rm = instruction & 0x0000000f
                    if instruction & 0x00f00000 == 0x00000000:
                        # MUL
                        op = arm_compiler.construct_mul(rd, rs, rm, condOp)
                    elif instruction & 0x00f00000 == 0x00100000:
                        # MULS
                        op = arm_compiler.construct_muls(rd, rs, rm, condOp)
                    elif instruction & 0x00f00000 == 0x00200000:
                        # MLA
                        op = arm_compiler.construct_mla(rd, rn, rs, rm, condOp)
                    elif instruction & 0x00f00000 == 0x00300000:
                        # MLAS
                        op = arm_compiler.construct_mlas(rd, rn, rs, rm, condOp)
                    elif instruction & 0x00f00000 == 0x00800000:
                        # UMULL
                        op = arm_compiler.construct_umull(rd, rn, rs, rm, condOp)
                    elif instruction & 0x00f00000 == 0x00900000:
                        # UMULLS
                        op = arm_compiler.construct_umulls(rd, rn, rs, rm, condOp)
                    elif instruction & 0x00f00000 == 0x00a00000:
                        # UMLAL
                        op = arm_compiler.construct_umlal(rd, rn, rs, rm, condOp)
                    elif instruction & 0x00f00000 == 0x00b00000:
                        # UMLALS
                        op = arm_compiler.construct_umlals(rd, rn, rs, rm, condOp)
                    elif instruction & 0x00f00000 == 0x00c00000:
                        # SMULL
                        op = arm_compiler.construct_smull(rd, rn, rs, rm, condOp)
                    elif instruction & 0x00f00000 == 0x00d00000:
                        # SMULLS
                        op = arm_compiler.construct_smulls(rd, rn, rs, rm, condOp)
                    elif instruction & 0x00f00000 == 0x00e00000:
                        # SMLAL
                        op = arm_compiler.construct_smlal(rd, rn, rs, rm, condOp)
                    elif instruction & 0x00f00000 == 0x00f00000:
                        # SMLALS
                        op = arm_compiler.construct_smlals(rd, rn, rs, rm, condOp)
                    op.writesPC = rd == PC
                else:
                    # Halfword and signed byte data transfer
                    load = instruction & 0x00100000
                    rd = (instruction & 0x0000f000) >> 12
                    hiOffset = (instruction & 0x00000f00) >> 4
                    loOffset = rm = instruction & 0x0000000f
                    h = instruction & 0x00000020
                    s = instruction & 0x00000040
                    w = instruction & 0x00200000
                    i = instruction & 0x00400000

                    address = None
                    if i:
                        immediate = loOffset | hiOffset
                        address = arm_compiler.construct_addressing_mode23_immediate(instruction, immediate, condOp)
                    else:
                        address = arm_compiler.construct_addressing_mode23_register(instruction, rm, condOp)
                    address.writesPC = w and rn == PC

                    if (instruction & 0x00000090) == 0x00000090:
                        if load:
                            # Load [signed] halfword/byte
                            if h:
                                if s:
                                    # LDRSH
                                    op = arm_compiler.construct_ldrsh(rd, address, condOp)
                                else:
                                    # LDRH
                                    op = arm_compiler.construct_ldrh(rd, address, condOp)
                            else:
                                if s:
                                    # LDRSB
                                    op = arm_compiler.construct_ldrsb(rd, address, condOp)
                        elif not s and h:
                            # STRH
                            op = arm_compiler.construct_strh(rd, address, condOp)
                    op.writesPC = rd == PC or address.writesPC
            elif i == 0x04000000 or i == 0x06000000:
                # LDR/STR
                rd = (instruction & 0x0000f000) >> 12
                load = instruction & 0x00100000
                b = instruction & 0x00400000
                i = instruction & 0x02000000

                address = None
                if i:
                    # Register offset
                    rm = instruction & 0x0000000f
                    shiftType = instruction & 0x00000060
                    shiftImmediate = (instruction & 0x00000f80) >> 7

                    if shiftType or shiftImmediate:
                        shiftOp = barrel_shift_immediate(shiftType, shiftImmediate, rm)
                        address = arm_compiler.construct_addressing_mode2_register_shifted(instruction, shiftOp, condOp)
                    else:
                        address = arm_compiler.construct_addressing_mode23_register(instruction, rm, condOp)
                else:
                    # Immediate
                    offset = instruction & 0x00000fff
                    address = arm_compiler.construct_addressing_mode23_immediate(instruction, offset, condOp)
                if load:
                    if b:
                        # LDRB
                        op = arm_compiler.construct_ldrb(rd, address, condOp)
                    else:
                        # LDR
                        op = arm_compiler.construct_ldr(rd, address, condOp)
                else:
                    if b:
                        # STRB
                        op = arm_compiler.construct_strb(rd, address, condOp)
                    else:
                        # STR
                        op = arm_compiler.construct_str(rd, address, condOp)
                op.writesPC = rd == PC or address.writesPC
            elif i == 0x08000000:
                # Block data transfer
                load = instruction & 0x00100000
                w = instruction & 0x00200000
                user = instruction & 0x00400000
                u = instruction & 0x00800000
                p = instruction & 0x01000000
                rs = instruction & 0x0000ffff
                rn = (instruction & 0x000f0000) >> 16

                address = None
                immediate = 0
                offset = 0
                overlap = False
                if u:
                    if p:
                        immediate = 4
                    for m in range(0x01, 16):
                        if rs & m:
                            if w and i == rn and not offset:
                                rs &= ~m
                                immediate += 4
                                overlap = True
                            offset += 4
                else:
                    if not p:
                        immediate = 4
                    for m in range(0x01, 16):
                        if rs & m:
                            if w and i == rn and not offset:
                                rs &= ~m
                                immediate += 4
                                overlap = True
                            immediate -= 4
                            offset -= 4
                if w:
                    address = arm_compiler.construct_addressing_mode4_writeback(immediate, offset, rn, overlap)
                else:
                    address = arm_compiler.construct_addressing_mode4(immediate, rn)
                if load:
                    # LDM
                    if user:
                        op = arm_compiler.construct_ldms(rs, address, condOp)
                    else:
                        op = arm_compiler.construct_ldm(rs, address, condOp)
                    op.writesPC = bool(rs & (1 << 15))
                else:
                    # STM
                    if user:
                        op = arm_compiler.construct_stms(rs, address, condOp)
                    else:
                        op = arm_compiler.construct_stm(rs, address, condOp)
                    op.writesPC = False
            elif i == 0x0a000000:
                # Branch
                immediate = instruction & 0x00ffffff
                if immediate & 0x00800000:
                    immediate |= 0xff000000
                immediate <<= 2
                link = instruction & 0x01000000
                if link:
                    op = arm_compiler.construct_bl(immediate, condOp)
                else:
                    op = arm_compiler.construct_b(immediate, condOp)
                op.writesPC = True
                op.fixedJump = True
            elif i == 0x0c000000:
                # Coprocessor data transfer
                pass
            elif i == 0x0e000000:
                # Coprocessor data operation/SWI
                if (instruction & 0x0f000000) == 0x0f000000:
                    # SWI
                    immediate = instruction & 0x00ffffff
                    op = arm_compiler.construct_swi(immediate, condOp)
                    op.writesPC = False
        op.execMode = MODE_ARM
        op.fixedJump = op.fixedJump or False
        return op
    
    def compileThumb(self, instruction):
        op = self.badOp(instruction & 0xffff)
        cpu = self
        gprs = self.gprs
        if (instruction & 0xfc00) == 0x4000:
            # Data-processing register
            rm = (instruction & 0x0038) >> 3
            rd = instruction & 0x0007
            if (instruction & 0x03c0) == 0x0000:
                # AND
                op = self.thumbCompiler.constructAND(rd, rm)
            elif (instruction & 0x03c0) == 0x0040:
                # EOR
                op = self.thumbCompiler.constructEOR(rd, rm)
            elif (instruction & 0x03c0) == 0x0080:
                # LSL(2)
                op = self.thumbCompiler.constructLSL2(rd, rm)
            elif (instruction & 0x03c0) == 0x00c0:
                # LSR(2)
                op = self.thumbCompiler.constructLSR2(rd, rm)
            elif (instruction & 0x03c0) == 0x0100:
                # ASR(2)
                op = self.thumbCompiler.constructASR2(rd, rm)
            elif (instruction & 0x03c0) == 0x0140:
                # ADC
                op = self.thumbCompiler.constructADC(rd, rm)
            elif (instruction & 0x03c0) == 0x0180:
                # SBC
                 op = self.thumbCompiler.constructSBC(rd, rm)
            elif (instruction & 0x03c0) == 0x01c0:
                # ROR
                op = self.thumbCompiler.constructROR(rd, rm)
            elif (instruction & 0x03c0) == 0x0200:
                # TST
                op = self.thumbCompiler.constructTST(rd, rm)
            elif (instruction & 0x03c0) == 0x0240:
                # NEG
                op = self.thumbCompiler.constructNEG(rd, rm)
            elif (instruction & 0x03c0) == 0x0280:
                # CMP(2)
                op = self.thumbCompiler.constructCMP2(rd, rm)
            elif (instruction & 0x03c0) == 0x02c0:
                # CMN
                op = self.thumbCompiler.constructCMN(rd, rm)
            elif (instruction & 0x03c0) == 0x0300:
                # ORR
                op = self.thumbCompiler.constructORR(rd, rm)
            elif (instruction & 0x03c0) == 0x0340:
                # MUL
                op = self.thumbCompiler.constructMUL(rd, rm)
            elif (instruction & 0x03c0) == 0x0380:
                # BIC
                op = self.thumbCompiler.constructBIC(rd, rm)
            elif (instruction & 0x03c0) == 0x03c0:
                # MVN
                op = self.thumbCompiler.constructMVN(rd, rm)
                op.writesPC = False
            elif (instruction & 0xfc00) == 0x4400:
                # Special data processing / branch/exchange instruction set
                rm = (instruction & 0x0078) >> 3
                rn = instruction & 0x0007
                h1 = instruction & 0x0080
                rd = rn | (h1 >> 4)
                if (instruction & 0x0300) == 0x0000:
                    # ADD(4)
                    op = self.thumbCompiler.constructADD4(rd, rm)
                    op.writesPC = rd == self.PC
                elif (instruction & 0x0300) == 0x0100:
                    # CMP(3)
                    op = self.thumbCompiler.constructCMP3(rd, rm)
                    op.writesPC = False
                elif (instruction & 0x0300) == 0x0200:
                    # MOV(3)
                    op = self.thumbCompiler.constructMOV3(rd, rm)
                    op.writesPC = rd == self.PC
                elif (instruction & 0x0300) == 0x0300:
                    # BX
                    op = self.thumbCompiler.constructBX(rd, rm)
                    op.writesPC = True
                    op.fixedJump = False
        elif (instruction & 0xf800) == 0x1800:
            # Add/subtract
            rm = (instruction & 0x01c0) >> 6
            rn = (instruction & 0x0038) >> 3
            rd = instruction & 0x0007
            if (instruction & 0x0600) == 0x0000:
                # ADD(3)
                op = self.thumbCompiler.constructADD3(rd, rn, rm)
            elif (instruction & 0x0600) == 0x0200:
                # SUB(3)
                op = self.thumbCompiler.constructSUB3(rd, rn, rm)
            elif (instruction & 0x0600) == 0x0400:
                immediate = (instruction & 0x01c0) >> 6
                if immediate:
                    # ADD(1)
                    op = self.thumbCompiler.constructADD1(rd, rn, immediate)
                else:
                    # MOV(2)
                    op = self.thumbCompiler.constructMOV2(rd, rn, rm)
            elif (instruction & 0x0600) == 0x0600:
                # SUB(1)
                immediate = (instruction & 0x01c0) >> 6
                op = self.thumbCompiler.constructSUB1(rd, rn, immediate)
            op.writesPC = False
        elif not (instruction & 0xe000):
            # Shift by immediate
            rd = instruction & 0x0007
            rm = (instruction & 0x0038) >> 3
            immediate = (instruction & 0x07c0) >> 6
            if (instruction & 0x1800) == 0x0000:
                # LSL(1)
                op = self.thumbCompiler.constructLSL1(rd, rm, immediate)
            elif (instruction & 0x1800) == 0x0800:
                # LSR(1)
                op = self.thumbCompiler.constructLSR1(rd, rm, immediate)
            elif (instruction & 0x1800) == 0x1000:
                # ASR(1)
                op = self.thumbCompiler.constructASR1(rd, rm, immediate)
            elif (instruction & 0x1800) == 0x1800:
                pass
            op.writesPC = False
        elif (instruction & 0xe000) == 0x2000:
            # Add/subtract/compare/move immediate
            immediate = instruction & 0x00ff
            rn = (instruction & 0x0700) >> 8
            if (instruction & 0x1800) == 0x0000:
                # MOV(1)
                op = self.thumbCompiler.constructMOV1(rn, immediate)
            elif (instruction & 0x1800) == 0x0800:
                # CMP(1)
                op = self.thumbCompiler.constructCMP1(rn, immediate)
            elif (instruction & 0x1800) == 0x1000:
                # ADD(2)
                op = self.thumbCompiler.constructADD2(rn, immediate)
            elif (instruction & 0x1800) == 0x1800:
                # SUB(2)
                op = self.thumbCompiler.constructSUB2(rn, immediate)
            op.writesPC = False
        elif (instruction & 0xf800) == 0x4800:
            # LDR(3)
            rd = (instruction & 0x0700) >> 8
            immediate = (instruction & 0x00ff) << 2
            op = self.thumbCompiler.constructLDR3(rd, immediate)
            op.writesPC = False
        elif (instruction & 0xf000) == 0x5000:
            # Load and store with relative offset
            rd = instruction & 0x0007
            rn = (instruction & 0x0038) >> 3
            rm = (instruction & 0x01c0) >> 6
            opcode = instruction & 0x0e00
            if opcode == 0x0000:
                # STR(2)
                op = self.thumbCompiler.constructSTR2(rd, rn, rm)
            elif opcode == 0x0200:
                # STRH(2)
                op = self.thumbCompiler.constructSTRH2(rd, rn, rm)
            elif opcode == 0x0400:
                # STRB(2)
                op = self.thumbCompiler.constructSTRB2(rd, rn, rm)
            elif opcode == 0x0600:
                # LDRSB
                op = self.thumbCompiler.constructLDRSB(rd, rn, rm)
            elif opcode == 0x0800:
                # LDR(2)
                op = self.thumbCompiler.constructLDR2(rd, rn, rm)
            elif opcode == 0x0a00:
                # LDRH(2)
                op = self.thumbCompiler.constructLDRH2(rd, rn, rm)
            elif opcode == 0x0c00:
                # LDRB(2)
                op = self.thumbCompiler.constructLDRB2(rd, rn, rm)
            elif opcode == 0x0e00:
                # LDRSH
                op = self.thumbCompiler.constructLDRSH(rd, rn, rm)
            op.writesPC = False
        elif (instruction & 0xe000) == 0x6000:
            # Load and store with immediate offset
            rd = instruction & 0x0007
            rn = (instruction & 0x0038) >> 3
            immediate = (instruction & 0x07c0) >> 4
            b = instruction & 0x1000
            if b:
                immediate >>= 2
            load = instruction & 0x0800
            if load:
                if b:
                    # LDRB(1)
                    op = self.thumbCompiler.constructLDRB1(rd, rn, immediate)
                else:
                    # LDR(1)
                    op = self.thumbCompiler.constructLDR1(rd, rn, immediate)
            else:
                if b:
                    # STRB(1)
                    op = self.thumbCompiler.constructSTRB1(rd, rn, immediate)
                else:
                    # STR(1)
                    op = self.thumbCompiler.constructSTR1(rd, rn, immediate)
            op.writesPC = False
        elif (instruction & 0xf600) == 0xb400:
            # Push and pop registers
            r = bool(instruction & 0x0100)
            rs = instruction & 0x00ff
            if instruction & 0x0800:
                # POP
                op = self.thumbCompiler.constructPOP(rs, r)
                op.writesPC = r
                op.fixedJump = False
            else:
                # PUSH
                op = self.thumbCompiler.constructPUSH(rs, r)
                op.writesPC = False
        elif instruction & 0x8000:
            if instruction & 0x7000 == 0x0000:
                # Load and store halfword
                rd = instruction & 0x0007
                rn = (instruction & 0x0038) >> 3
                immediate = (instruction & 0x07c0) >> 5
                if instruction & 0x0800:
                    # LDRH(1)
                    op = self.thumbCompiler.constructLDRH1(rd, rn, immediate)
                else:
                    # STRH(1)
                    op = self.thumbCompiler.constructSTRH1(rd, rn, immediate)
                op.writesPC = False
            elif instruction & 0x7000 == 0x1000:
                # SP-relative load and store
                rd = (instruction & 0x0700) >> 8
                immediate = (instruction & 0x00ff) << 2
                load = instruction & 0x0800
                if load:
                    # LDR(4)
                    op = self.thumbCompiler.constructLDR4(rd, immediate)
                else:
                    # STR(3)
                    op = self.thumbCompiler.constructSTR3(rd, immediate)
                op.writesPC = False
            elif instruction & 0x7000 == 0x2000:
                # Load address
                rd = (instruction & 0x0700) >> 8
                immediate = (instruction & 0x00ff) << 2
                if instruction & 0x0800:
                    # ADD(6)
                    op = self.thumbCompiler.constructADD6(rd, immediate)
                else:
                    # ADD(5)
                    op = self.thumbCompiler.constructADD5(rd, immediate)
                op.writesPC = False
            elif instruction & 0x7000 == 0x3000:
                # Miscellaneous
                if not (instruction & 0x0f00):
                    # Adjust stack pointer
                    # ADD(7)/SUB(4)
                    b = instruction & 0x0080
                    immediate = (instruction & 0x7f) << 2
                    if b:
                        immediate = -immediate
                    op = self.thumbCompiler.constructADD7(immediate)
                    op.writesPC = False
            elif instruction & 0x7000 == 0x4000:
                # Multiple load and store
                rn = (instruction & 0x0700) >> 8
                rs = instruction & 0x00ff
                if instruction & 0x0800:
                    # LDMIA
                    op = self.thumbCompiler.constructLDMIA(rn, rs)
                else:
                    # STMIA
                    op = self.thumbCompiler.constructSTMIA(rn, rs)
                op.writesPC = False
            elif instruction & 0x7000 == 0x5000:
                # Conditional branch
                cond = (instruction & 0x0f00) >> 8
                immediate = instruction & 0x00ff
                if cond == 0xf:
                    # SWI
                    op = self.thumbCompiler.constructSWI(immediate)
                    op.writesPC = False
                else:
                    # B(1)
                    if instruction & 0x0080:
                        immediate |= 0xffffff00
                    immediate <<= 1
                    condOp = self.conds[cond]
                    op = self.thumbCompiler.constructB1(immediate, condOp)
                    op.writesPC = True
                    op.fixedJump = True
            elif instruction & 0x7000 == 0x6000 or instruction & 0x7000 == 0x7000:
                # BL(X)
                immediate = instruction & 0x07ff
                h = instruction & 0x1800
                if h == 0x0000:
                    # B(2)
                    if immediate & 0x0400:
                        immediate |= 0xfffff800
                    immediate <<= 1
                    op = self.thumbCompiler.constructB2(immediate)
                    op.writesPC = True
                    op.fixedJump = True
                elif h == 0x0800:
                    # BLX (ARMv5T)
                    pass
                elif h == 0x1000:
                    # BL(1)
                    if immediate & 0x0400:
                        immediate |= 0xfffffc00
                    immediate <<= 12
                    op = self.thumbCompiler.constructBL1(immediate)
                    op.writesPC = False
                elif h == 0x1800:
                    # BL(2)
                    op = self.thumbCompiler.constructBL2(immediate)
                    op.writesPC = True
                    op.fixedJump = False
        else:
            raise Exception("Bad opcode: 0x" + instruction.toString(16))

        op.execMode = self.MODE_THUMB
        op.fixedJump = op.fixedJump or False
        return op   