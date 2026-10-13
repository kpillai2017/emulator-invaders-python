# Placeholder for Cpu class Python port
# The C++ Cpu.cpp is very large and complex. This is a stub for integration.
# You will need to port the full logic for a working emulator.
from util import Util
from memory import Memory
from iohandler import Io

# Precomputed even-parity lookup for 0..255
_PARITY_TABLE = tuple(bin(i).count('1') % 2 == 0 for i in range(256))

class Cpu:
    def __init__(self):
        self.cpuUtil = Util()
        self.cpuMemory = None
        self.cpuMemoryPtr = None
        self.cpuIo = None
        # Registers and flags (add as needed)
        self.PC = 0
        self.A = 0
        self.B = 0
        self.C = 0
        self.D = 0
        self.E = 0
        self.H = 0
        self.L = 0
        self.BC = 0
        self.DE = 0
        self.HL = 0
        self.SIGN = False
        self.ZERO = False
        self.HALFCARRY = False
        self.PARITY = False
        self.CARRY = False
        self.INTERRUPT = False
        self.CRASHED = False
        self.count_instructions = 0
        self.interrupt_alternate = 0
        self.instruction_per_frame = 4000  # Number of instructions to run per frame
        self.debugOutputPtr = ""
        self._dispatch = self._build_dispatch_table()

    def init(self, m: Memory, io: Io):
        self.cpuMemory = m
        self.cpuMemoryPtr = m.get_memory_ptr()
        self.cpuIo = io
        self.reset()
        self.debugOutputPtr = ""
        return True

    def reset(self):
        self.PC = 0
        self.A = 0
        self.B = 0
        self.C = 0
        self.D = 0
        self.E = 0
        self.H = 0
        self.L = 0
        self.BC = 0
        self.DE = 0
        self.HL = 0
        self.SIGN = False
        self.ZERO = False
        self.HALFCARRY = False
        self.PARITY = False
        self.CARRY = False
        self.INTERRUPT = False
        self.CRASHED = False
        self.count_instructions = 0
        self.interrupt_alternate = 0

    def _build_dispatch_table(self):
        """Build a 256-entry opcode -> bound-method table (replaces the long if/elif chain)."""
        table = [self.execute_undefined] * 256
        groups = (
            ((0x00,), self.execute_nop),
            ((0xc2, 0xc3, 0xca, 0xd2, 0xda, 0xf2, 0xfa), self.execute_jmp),       # JNZ, JMP, JZ, JNC, JC, JP, JM
            ((0x01, 0x11, 0x21, 0x31), self.execute_lxi),                         # LXI
            ((0x06, 0x0e, 0x16, 0x1e, 0x26, 0x2e, 0x36, 0x3e), self.execute_mvi), # MVI
            ((0xcd, 0xc4, 0xcc, 0xd4, 0xdc), self.execute_call),                  # CALL, CNZ, CZ, CNC, CC
            ((0x0a, 0x1a, 0x3a), self.execute_lda),                               # LDAX B, LDAX D, LDA
            ((0x70, 0x71, 0x72, 0x73, 0x74, 0x75, 0x77), self.execute_movhl),     # MOV M,r
            ((0x03, 0x13, 0x23, 0x33), self.execute_inx),                         # INX
            ((0x0b, 0x1b, 0x2b, 0x3b), self.execute_dcx),                         # DCX
            ((0x05, 0x0d, 0x15, 0x1d, 0x25, 0x2d, 0x35, 0x3d), self.execute_dec), # DCR
            ((0x04, 0x0c, 0x14, 0x1c, 0x24, 0x2c, 0x34, 0x3c), self.execute_inc), # INR
            ((0xc0, 0xc8, 0xc9, 0xd0, 0xd8), self.execute_ret),                   # RNZ, RZ, RET, RNC, RC
            (tuple(range(0x40, 0x70)) + tuple(range(0x78, 0x80)), self.execute_mov),  # MOV r,r / MOV r,M
            ((0xb8, 0xb9, 0xba, 0xbb, 0xbc, 0xbd, 0xbe, 0xbf, 0xfe), self.execute_cmp),
            ((0xc5, 0xd5, 0xe5, 0xf5), self.execute_push),
            ((0xc1, 0xd1, 0xe1, 0xf1), self.execute_pop),
            ((0x09, 0x19, 0x29, 0x39), self.execute_dad),
            ((0xeb,), self.execute_xchg),
            ((0xe3,), self.execute_xthl),
            ((0xd3,), self.execute_outp),
            ((0xdb,), self.execute_inp),
            ((0xe9,), self.execute_pchl),
            ((0xc7, 0xcf, 0xd7, 0xdf, 0xe7, 0xef, 0xf7, 0xff), self.execute_rst),
            ((0x07,), self.execute_rlc),
            ((0x17,), self.execute_ral),
            ((0x0f,), self.execute_rrc),
            ((0x1f,), self.execute_rar),
            ((0xa0, 0xa1, 0xa2, 0xa3, 0xa4, 0xa5, 0xa6, 0xa7, 0xe6), self.execute_and),
            ((0x80, 0x81, 0x82, 0x83, 0x84, 0x85, 0x86, 0x87, 0xc6), self.execute_add),
            ((0x02, 0x12, 0x32), self.execute_sta),
            ((0xa8, 0xa9, 0xaa, 0xab, 0xac, 0xad, 0xae, 0xaf, 0xee), self.execute_xor),
            ((0xf3,), self.execute_di),
            ((0xfb,), self.execute_ei),
            ((0x37,), self.execute_stc),
            ((0x3f,), self.execute_cmc),
            ((0xb0, 0xb1, 0xb2, 0xb3, 0xb4, 0xb5, 0xb6, 0xb7, 0xf6), self.execute_or),
            ((0x90, 0x91, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0xd6), self.execute_sub),
            ((0x2a,), self.execute_lhld),
            ((0x22,), self.execute_shld),
            ((0x9e,), self.execute_sbbm),
            ((0xde,), self.execute_sbbi),
            ((0x27,), self.execute_daa),
            ((0x2f,), self.execute_cma),
            ((0x88, 0x89, 0x8a, 0x8b, 0x8c, 0x8d, 0x8e, 0x8f, 0xce), self.execute_adc),
            # 0x76 (HLT) and anything not listed fall through to execute_undefined
        )
        for opcodes, handler in groups:
            for op in opcodes:
                table[op] = handler
        return table

    def execute_undefined(self):
        self.debugOutputPtr = f"Undefined instruction: {self.cpuUtil.hbyte(self.current_inst)}"
        self.CRASHED = True
        print(self.debugOutputPtr)

    def run(self):
        # Run about one frame's worth of instruction code.
        # Hot loop: attribute lookups are hoisted into locals for speed.
        dispatch = self._dispatch
        mem = self.cpuMemoryPtr
        half_instruction_per_frame = self.instruction_per_frame // 2
        for _ in range(self.instruction_per_frame):
            if self.CRASHED:
                return
            pc = self.PC
            self.disassembly_pc = pc
            op = mem[pc]
            self.PC = (pc + 1) & 0xFFFF
            self.current_inst = op
            dispatch[op]()

            self.count_instructions += 1
            if self.count_instructions >= half_instruction_per_frame:
                if self.INTERRUPT:
                    self.call_interrupt(0x08 if self.interrupt_alternate == 0 else 0x10)
                self.interrupt_alternate = 1 - self.interrupt_alternate
                self.count_instructions = 0

    def execute_instruction(self):
        # Execute a single instruction (kept for single-stepping/debugging)
        self.disassembly_pc = self.PC
        self.current_inst = self.fetch_rom_byte()
        self._dispatch[self.current_inst]()

        self.count_instructions += 1
        half_instruction_per_frame = self.instruction_per_frame // 2
        if self.count_instructions >= half_instruction_per_frame:
            if self.INTERRUPT:
                self.call_interrupt(0x08 if self.interrupt_alternate == 0 else 0x10)
            self.interrupt_alternate = 1 - self.interrupt_alternate
            self.count_instructions = 0

    def call_interrupt(self, in_address):
        # Implements interrupt call: disables interrupts, pushes PC, jumps to in_address
        self.INTERRUPT = False
        self.push_stack(self.PC)
        self.PC = in_address & 0xFFFF

    def execute_nop(self):
        # Implements NOP: No operation
        pass

    def execute_jmp(self):
        condition = True
        data16 = self.fetch_rom_short() & 0xFFFF
        if self.current_inst == 0xc2:
            condition = not self.ZERO
        elif self.current_inst == 0xca:
            condition = self.ZERO
        elif self.current_inst == 0xd2:
            condition = not self.CARRY
        elif self.current_inst == 0xda:
            condition = self.CARRY
        elif self.current_inst == 0xf2:
            condition = not self.SIGN
        elif self.current_inst == 0xfa:
            condition = self.SIGN

        if condition:
            self.PC = data16

    def execute_lxi(self):
        data16 = self.fetch_rom_short() & 0xFFFF
        if self.current_inst == 0x01:
            self.set_BC(data16)
        elif self.current_inst == 0x11:
            self.set_DE(data16)
        elif self.current_inst == 0x21:
            self.set_HL(data16)
        elif self.current_inst == 0x31:
            self.set_SP(data16)

    def execute_mvi(self):
        data8 = self.fetch_rom_byte() & 0xFF
        if self.current_inst == 0x3e:
            self.set_A(data8)
        elif self.current_inst == 0x06:
            self.set_B(data8)   
        elif self.current_inst == 0x0e:
            self.set_C(data8)
        elif self.current_inst == 0x16:
            self.set_D(data8)
        elif self.current_inst == 0x1e:
            self.set_E(data8)
        elif self.current_inst == 0x26:
            self.set_H(data8)
        elif self.current_inst == 0x2e:
            self.set_L(data8)
        elif self.current_inst == 0x36:
            self.write_byte(self.HL, data8)

    # --- Instruction implementations (stubs, to be filled in as needed) ---
    def execute_call(self):
        # Implements CALL and conditional CALL instructions
        data16 = self.fetch_rom_short() & 0xFFFF
        condition = True
        if self.current_inst == 0xc4:  # CNZ
            condition = not self.ZERO
        elif self.current_inst == 0xcc:  # CZ
            condition = self.ZERO
        elif self.current_inst == 0xd4:  # CNC
            condition = not self.CARRY
        elif self.current_inst == 0xdc:  # CC
            condition = self.CARRY
        # 0xcd is unconditional CALL

        if condition:
            self.push_stack(self.PC)
            self.PC = data16

    def execute_ret(self):
        # Implements RET and conditional RET instructions
        condition = True

        if self.current_inst == 0xc0:  # RNZ
            condition = not self.ZERO
        elif self.current_inst == 0xc8:  # RZ
            condition = self.ZERO
        elif self.current_inst == 0xd0:  # RNC
            condition = not self.CARRY
        elif self.current_inst == 0xd8:  # RC
            condition = self.CARRY
        # 0xc9 is unconditional RET

        if condition:
            self.PC = self.pop_stack()

    def execute_lda(self):
        # Implements LDA, LDAX B, LDAX D instructions
        if self.current_inst == 0x0a:  # LDAX B (A <- (BC))
            source = self.BC
        elif self.current_inst == 0x1a:  # LDAX D (A <- (DE))
            source = self.DE
        elif self.current_inst == 0x3a:  # LDA addr
            source = self.fetch_rom_short()

        self.set_A(self.read_byte(source & 0xFFFF))

    def execute_push(self):
        # Implements PUSH B, D, H, PSW
        if self.current_inst == 0xc5:  # PUSH B
            value = self.BC
        elif self.current_inst == 0xd5:  # PUSH D
            value = self.DE
        elif self.current_inst == 0xe5:  # PUSH H
            value = self.HL
        elif self.current_inst == 0xf5:  # PUSH PSW (A and flags)
            # Pack flags into the lower byte
            value = (self.A << 8) & 0xFFFF
            if (self.SIGN):
                value |= 0x80
            if (self.ZERO):
                value |= 0x40
            if (self.INTERRUPT):
                value |= 0x20
            if (self.HALFCARRY):
                value |= 0x10
            if (self.CARRY):
                value |= 0x01

        self.push_stack(value & 0xFFFF)

    def execute_pop(self):
        # Implements POP B, D, H, PSW
        value = self.pop_stack() & 0xFFFF

        if self.current_inst == 0xc1:  # POP B
            self.set_BC(value)
        elif self.current_inst == 0xd1:  # POP D
            self.set_DE(value)
        elif self.current_inst == 0xe1:  # POP H
            self.set_HL(value)
        elif self.current_inst == 0xf1:  # POP PSW (A and flags)
            self.A = (value >> 8) & 0xFF
            flags = value & 0xFF
            self.SIGN     = bool(flags & 0x80)
            self.ZERO     = bool(flags & 0x40)
            self.INTERRUPT= bool(flags & 0x20)
            self.HALFCARRY= bool(flags & 0x10)
            self.CARRY    = bool(flags & 0x01)
        else:
            return  # Unknown POP

    def execute_movhl(self):
        # Implements MOV M, r and MOV r, M instructions (HL indirect addressing)
        # Opcodes: 0x77, 0x70-0x75
        # 0x77: MOV M, A
        # 0x70: MOV M, B
        # 0x71: MOV M, C
        # 0x72: MOV M, D
        # 0x73: MOV M, E
        # 0x74: MOV M, H
        # 0x75: MOV M, L
        # MOV r, M is handled in execute_mov()

        if self.current_inst == 0x77:  # MOV M, A
            self.write_byte(self.HL, self.A)
        elif self.current_inst == 0x70:  # MOV M, B
            self.write_byte(self.HL, self.B)
        elif self.current_inst == 0x71:  # MOV M, C
            self.write_byte(self.HL, self.C)
        elif self.current_inst == 0x72:  # MOV M, D
            self.write_byte(self.HL, self.D)
        elif self.current_inst == 0x73:  # MOV M, E
            self.write_byte(self.HL, self.E)
        elif self.current_inst == 0x74:  # MOV M, H
            self.write_byte(self.HL, self.H)
        elif self.current_inst == 0x75:  # MOV M, L
            self.write_byte(self.HL, self.L)

    def execute_mov(self):
        # Implements MOV r1, r2 and MOV r, M and MOV M, r (0x40-0x7F, except 0x76 HLT)
        inst = self.current_inst
        if inst == 0x7f:      # MOV A, A
            self.set_A(self.A)
        elif inst == 0x78:    # MOV A, B
            self.set_A(self.B)
        elif inst == 0x79:    # MOV A, C
            self.set_A(self.C)
        elif inst == 0x7a:    # MOV A, D
            self.set_A(self.D)
        elif inst == 0x7b:    # MOV A, E
            self.set_A(self.E)
        elif inst == 0x7c:    # MOV A, H
            self.set_A(self.H)
        elif inst == 0x7d:    # MOV A, L
            self.set_A(self.L)
        elif inst == 0x7e:    # MOV A, M
            self.set_A(self.read_byte(self.HL))
        elif inst == 0x47:    # MOV B, A
            self.set_B(self.A)
        elif inst == 0x40:    # MOV B, B
            self.set_B(self.B)
        elif inst == 0x41:    # MOV B, C
            self.set_B(self.C)
        elif inst == 0x42:    # MOV B, D
            self.set_B(self.D)
        elif inst == 0x43:    # MOV B, E
            self.set_B(self.E)
        elif inst == 0x44:    # MOV B, H
            self.set_B(self.H)
        elif inst == 0x45:    # MOV B, L
            self.set_B(self.L)
        elif inst == 0x46:    # MOV B, M
            self.set_B(self.read_byte(self.HL))
        elif inst == 0x4f:    # MOV C, A
            self.set_C(self.A)
        elif inst == 0x48:    # MOV C, B
            self.set_C(self.B)
        elif inst == 0x49:    # MOV C, C
            self.set_C(self.C)
        elif inst == 0x4a:    # MOV C, D
            self.set_C(self.D)
        elif inst == 0x4b:    # MOV C, E
            self.set_C(self.E)
        elif inst == 0x4c:    # MOV C, H
            self.set_C(self.H)
        elif inst == 0x4d:    # MOV C, L
            self.set_C(self.L)
        elif inst == 0x4e:    # MOV C, M
            self.set_C(self.read_byte(self.HL))
        elif inst == 0x57:    # MOV D, A
            self.set_D(self.A)
        elif inst == 0x50:    # MOV D, B
            self.set_D(self.B)
        elif inst == 0x51:    # MOV D, C
            self.set_D(self.C)
        elif inst == 0x52:    # MOV D, D
            self.set_D(self.D)
        elif inst == 0x53:    # MOV D, E
            self.set_D(self.E)
        elif inst == 0x54:    # MOV D, H
            self.set_D(self.H)
        elif inst == 0x55:    # MOV D, L
            self.set_D(self.L)
        elif inst == 0x56:    # MOV D, M
            self.set_D(self.read_byte(self.HL))
        elif inst == 0x5f:    # MOV E, A
            self.set_E(self.A)
        elif inst == 0x58:    # MOV E, B
            self.set_E(self.B)
        elif inst == 0x59:    # MOV E, C
            self.set_E(self.C)
        elif inst == 0x5a:    # MOV E, D
            self.set_E(self.D)
        elif inst == 0x5b:    # MOV E, E
            self.set_E(self.E)
        elif inst == 0x5c:    # MOV E, H
            self.set_E(self.H)
        elif inst == 0x5d:    # MOV E, L
            self.set_E(self.L)
        elif inst == 0x5e:    # MOV E, M
            self.set_E(self.read_byte(self.HL))
        elif inst == 0x67:    # MOV H, A
            self.set_H(self.A)
        elif inst == 0x60:    # MOV H, B
            self.set_H(self.B)
        elif inst == 0x61:    # MOV H, C
            self.set_H(self.C)
        elif inst == 0x62:    # MOV H, D
            self.set_H(self.D)
        elif inst == 0x63:    # MOV H, E
            self.set_H(self.E)
        elif inst == 0x64:    # MOV H, H
            self.set_H(self.H)
        elif inst == 0x65:    # MOV H, L
            self.set_H(self.L)
        elif inst == 0x66:    # MOV H, M
            self.set_H(self.read_byte(self.HL))
        elif inst == 0x6f:    # MOV L, A
            self.set_L(self.A)
        elif inst == 0x68:    # MOV L, B
            self.set_L(self.B)
        elif inst == 0x69:    # MOV L, C
            self.set_L(self.C)
        elif inst == 0x6a:    # MOV L, D
            self.set_L(self.D)
        elif inst == 0x6b:    # MOV L, E
            self.set_L(self.E)
        elif inst == 0x6c:    # MOV L, H
            self.set_L(self.H)
        elif inst == 0x6d:    # MOV L, L
            self.set_L(self.L)
        elif inst == 0x6e:    # MOV L, M
            self.set_L(self.read_byte(self.HL))

    def execute_inx(self):
        # Implements INX B, INX D, INX H, INX SP
        if self.current_inst == 0x03:  # INX B
            self.set_BC((self.BC + 1) & 0xFFFF)
        elif self.current_inst == 0x13:  # INX D
            self.set_DE((self.DE + 1) & 0xFFFF)
        elif self.current_inst == 0x23:  # INX H
            self.set_HL((self.HL + 1) & 0xFFFF)
        elif self.current_inst == 0x33:  # INX SP
            self.set_SP((self.SP + 1) & 0xFFFF)

    def execute_dad(self):
         # Implements DAD B, DAD D, DAD H, DAD SP
        # Adds the specified register pair to HL PILLAI
        if self.current_inst == 0x09:  # DAD B
            self.add_hl(self.BC)
        elif self.current_inst == 0x19:  # DAD D
            self.add_hl(self.DE)
        elif self.current_inst == 0x29:  # DAD H
            self.add_hl(self.HL)
        elif self.current_inst == 0x39:  # DAD SP
            self.add_hl(self.SP)

    def add_hl(self, inValue):
        value = self.HL + inValue
        self.set_HL(value & 0xFFFF)
        self.CARRY = (value > 0xFFFF)  # Check overflow before masking

    def execute_dcx(self):
         # Implements DCX B, DCX D, DCX H, DCX SP
        if self.current_inst == 0x0b:  # DCX B
            self.set_BC((self.BC - 1) & 0xFFFF)
        elif self.current_inst == 0x1b:  # DCX D
            self.set_DE((self.DE - 1) & 0xFFFF)
        elif self.current_inst == 0x2b:  # DCX H
            self.set_HL((self.HL - 1) & 0xFFFF)
        elif self.current_inst == 0x3b:  # DCX SP
            self.set_SP((self.SP - 1) & 0xFFFF)

    def execute_dec(self):
        # Implements DEC r and DEC M instructions
        # 0x05: DEC B, 0x0d: DEC C, 0x15: DEC D, 0x1d: DEC E,
        # 0x25: DEC H, 0x2d: DEC L, 0x35: DEC M, 0x3d: DEC A
        if self.current_inst == 0x3d:
            self.set_A(self.perform_dec(self.A) & 0xFF)
        elif self.current_inst == 0x05:
            self.set_B(self.perform_dec(self.B) & 0xFF)
        elif self.current_inst == 0x0d:
            self.set_C(self.perform_dec(self.C) & 0xFF)
        elif self.current_inst == 0x15:
            self.set_D(self.perform_dec(self.D) & 0xFF)
        elif self.current_inst == 0x1d:
            self.set_E(self.perform_dec(self.E) & 0xFF)
        elif self.current_inst == 0x25:
            self.set_H(self.perform_dec(self.H) & 0xFF)
        elif self.current_inst == 0x2d:
            self.set_L(self.perform_dec(self.L) & 0xFF)
        elif self.current_inst == 0x35:
            data8 = self.read_byte(self.HL) & 0xFF
            self.write_byte(self.HL, self.perform_dec(data8) & 0xFF)

    def execute_inc(self):
        # Implements INC r and INC M instructions
        # 0x04: INC B, 0x0c: INC C, 0x14: INC D, 0x1c: INC E,
        # 0x24: INC H, 0x2c: INC L, 0x34: INC M, 0x3c: INC A
        if self.current_inst == 0x3c:
            self.set_A(self.perform_inc(self.A) & 0xFF)
        elif self.current_inst == 0x04:
         self.set_B(self.perform_inc(self.B) & 0xFF)
        elif self.current_inst == 0x0c:
         self.set_C(self.perform_inc(self.C) & 0xFF)
        elif self.current_inst == 0x14:
         self.set_D(self.perform_inc(self.D) & 0xFF)
        elif self.current_inst == 0x1c:
         self.set_E(self.perform_inc(self.E) & 0xFF)
        elif self.current_inst == 0x24:
         self.set_H(self.perform_inc(self.H) & 0xFF)
        elif self.current_inst == 0x2c:
         self.set_L(self.perform_inc(self.L) & 0xFF)
        elif self.current_inst == 0x34:
            data8 = self.read_byte(self.HL) & 0xFF
            self.write_byte(self.HL, self.perform_inc(data8) & 0xFF)

    def execute_and(self):
        # Implements ANA r, ANA M, ANI data
        if self.current_inst == 0xa7:
            self.perform_and(self.A)
        elif self.current_inst == 0xa0:
            self.perform_and(self.B)
        elif self.current_inst == 0xa1:
            self.perform_and(self.C)
        elif self.current_inst == 0xa2:
            self.perform_and(self.D)
        elif self.current_inst == 0xa3:
            self.perform_and(self.E)
        elif self.current_inst == 0xa4:
            self.perform_and(self.H)
        elif self.current_inst == 0xa5:
            self.perform_and(self.L)
        elif self.current_inst == 0xa6:
            self.perform_and(self.read_byte(self.HL))
        elif self.current_inst == 0xe6:  # ANI data
            immediate = self.fetch_rom_byte() & 0xFF
            self.perform_and(immediate)

    def execute_xor(self):
        # Implements XRA r, XRA M, XRI data
        if self.current_inst == 0xaf:  # XRA A
            self.perform_xor(self.A)
        elif self.current_inst == 0xa8:  # XRA A
            self.perform_xor(self.B)
        elif self.current_inst == 0xa9:  # XRA C
            self.perform_xor(self.C)
        elif self.current_inst == 0xaa:  # XRA D
            self.perform_xor(self.D)
        elif self.current_inst == 0xab:  # XRA E
            self.perform_xor(self.E)
        elif self.current_inst == 0xac:  # XRA H
            self.perform_xor(self.H)
        elif self.current_inst == 0xad:  # XRA L
            self.perform_xor(self.L)
        elif self.current_inst == 0xae:  # XRA M
            self.perform_xor(self.read_byte(self.HL))
        elif self.current_inst == 0xee:  # XRI data
            immediate = self.fetch_rom_byte() & 0xFF
            self.perform_xor(immediate)

    def execute_or(self):
        # Implements ORA r, ORA M, ORI data
        if self.current_inst == 0xb7:  # ORA A
            self.perform_or(self.A)
        elif self.current_inst == 0xb0:  # ORA B
            self.perform_or(self.B)
        elif self.current_inst == 0xb1:  # ORA C
            self.perform_or(self.C)
        elif self.current_inst == 0xb2:  # ORA D
            self.perform_or(self.D)
        elif self.current_inst == 0xb3:  # ORA E
            self.perform_or(self.E)
        elif self.current_inst == 0xb4:  # ORA H
            self.perform_or(self.H)
        elif self.current_inst == 0xb5:  # ORA L
            self.perform_or(self.L)
        elif self.current_inst == 0xb6:  # ORA M
            self.perform_or(self.read_byte(self.HL))
        elif self.current_inst == 0xf6:  # ORI data
            immediate = self.fetch_rom_byte() & 0xFF
            self.perform_or(immediate)

    def execute_add(self):
         # Implements ADD r, ADD M, ADI data, ADD A
        if self.current_inst == 0x87:  # ADD A
            self.perform_byte_add(self.A)
        elif self.current_inst == 0x80:  # ADD B
            self.perform_byte_add(self.B)
        elif self.current_inst == 0x81:  # ADD C
            self.perform_byte_add(self.C)
        elif self.current_inst == 0x82:  # ADD D
            self.perform_byte_add(self.D)
        elif self.current_inst == 0x83:  # ADD E
            self.perform_byte_add(self.E)
        elif self.current_inst == 0x84:  # ADD H
            self.perform_byte_add(self.H)
        elif self.current_inst == 0x85:  # ADD L
            self.perform_byte_add(self.L)
        elif self.current_inst == 0x86:  # ADD M
            self.perform_byte_add(self.read_byte(self.HL))
        elif self.current_inst == 0xc6:  # ADI data
            immediate = self.fetch_rom_byte() & 0xFF
            self.perform_byte_add(immediate)

    def execute_adc(self):
        # Implements ADC r, ADC M, ACI data
        carryvalue = (1 if self.CARRY else 0) & 0xFF

        if self.current_inst == 0x8f:  # ADC A
            self.perform_byte_add(self.A + carryvalue)
        elif self.current_inst == 0x88:  # ADC B
            self.perform_byte_add(self.B + carryvalue)
        elif self.current_inst == 0x89:  # ADC C
            self.perform_byte_add(self.C + carryvalue)
        elif self.current_inst == 0x8a:  # ADC D
            self.perform_byte_add(self.D + carryvalue)
        elif self.current_inst == 0x8b:  # ADC E
            self.perform_byte_add(self.E + carryvalue)
        elif self.current_inst == 0x8c:  # ADC H
            self.perform_byte_add(self.H + carryvalue)
        elif self.current_inst == 0x8d:  # ADC L
            self.perform_byte_add(self.L + carryvalue)
        elif self.current_inst == 0x8e:  # ADC M
            self.perform_byte_add(self.read_byte(self.HL), carryvalue)
        elif self.current_inst == 0xce:  # ACI data
            immediate = self.fetch_rom_byte() & 0xFF
            self.perform_byte_add(immediate, carryvalue)

    def execute_sub(self):
        # Implements SUB r, SUB M, SUI data, SUB A
        if self.current_inst == 0x97:  # SUB A
            self.perform_byte_sub(self.A)
        elif self.current_inst == 0x90:  # SUB B
            self.perform_byte_sub(self.B)
        elif self.current_inst == 0x91:  # SUB C
            self.perform_byte_sub(self.C)
        elif self.current_inst == 0x92:  # SUB D
            self.perform_byte_sub(self.D)
        elif self.current_inst == 0x93:  # SUB E
            self.perform_byte_sub(self.E)
        elif self.current_inst == 0x94:  # SUB H
            self.perform_byte_sub(self.H)
        elif self.current_inst == 0x95:  # SUB L
            self.perform_byte_sub(self.L)
        elif self.current_inst == 0x96:  # SUB M
            self.perform_byte_sub(self.read_byte(self.HL))
        elif self.current_inst == 0xd6:  # SUI data
            immediate = self.fetch_rom_byte() & 0xFF
            self.perform_byte_sub(immediate)
    
    def execute_sbbm(self):
        # Implements SBB M (Subtract with borrow, opcode 0x9E)
        m = self.read_byte((self.H << 8) | self.L)
        c = int(self.CARRY)
        r = self.A - m - c
        f = r & 0xFF

        self.SIGN = bool(f & 0x80)
        self.ZERO = f == 0
        self.PARITY = self.parity(f)
        self.CARRY = r < 0
        self.HALFCARRY = ((self.A & 0x0F) - (m & 0x0F) - c) < 0
        self.set_A(f)

    def execute_sbbi(self):
        # Implements SBBI (Subtract immediate with borrow, opcode 0xDE)
        immediate = self.fetch_rom_byte() & 0xFF
        carryvalue = (1 if self.CARRY else 0) & 0xFF
        self.perform_byte_sub(immediate, carryvalue)

    def execute_cmp(self):
        # Implements CMP r and CPI instructions
        # 0xb8: CMP B, 0xb9: CMP C, ..., 0xbf: CMP A, 0xbe: CMP M, 0xfe: CPI data
        if self.current_inst == 0xbf:  # CMP B
            value = self.A & 0xFF
        elif self.current_inst == 0xb8:  # CMP B
            value = self.B & 0xFF
        elif self.current_inst == 0xb9:  # CMP C
            value = self.C & 0xFF
        elif self.current_inst == 0xba:  # CMP D
            value = self.D & 0xFF
        elif self.current_inst == 0xbb:  # CMP E
            value = self.E & 0xFF
        elif self.current_inst == 0xbc:  # CMP H
            value = self.H & 0xFF
        elif self.current_inst == 0xbd:  # CMP L
            value = self.L & 0xFF
        elif self.current_inst == 0xbe:  # CMP A
            value = self.read_byte(self.HL) & 0xFF
        elif self.current_inst == 0xfe:  # CPI data
            value = self.fetch_rom_byte() & 0xFF

        self.perform_comp_sub(value)

    def execute_xchg(self):
        # Implements XCHG: Exchange DE and HL register pairs
        # self.DE, self.HL = self.HL, self.DE
        temp = self.DE & 0xFFFF
        self.set_DE(self.HL)
        self.set_HL(temp)

    def execute_xthl(self):
        # Implements XTHL: Exchange top of stack with HL
        # Swap HL <-> (SP), (SP+1)
        temp = self.H & 0xFF
        self.set_H(self.read_byte(self.SP + 1) & 0xFF)
        self.write_byte(self.SP + 1, temp)

        temp = self.L & 0xFF
        self.set_L(self.read_byte(self.SP) & 0xFF)
        self.write_byte(self.SP, temp)

    def execute_outp(self):
        # Implements OUT instruction (0xD3)
        # Output accumulator to port specified by next byte
        port = self.fetch_rom_byte() & 0xFF
        if self.cpuIo:
            self.cpuIo.output_port(port, self.A)

    def execute_inp(self):
        # Implements IN instruction (0xDB)
        # Input from port specified by next byte into accumulator
        port = self.fetch_rom_byte() & 0xFF
        if self.cpuIo:
            self.set_A(self.cpuIo.input_port(port))

    def execute_pchl(self):
          # Implements PCHL: Jump to address in HL
        self.PC = self.HL

    def execute_rst(self):
        # Implements RST n (where n = 0-7, opcodes: 0xC7, 0xCF, 0xD7, 0xDF, 0xE7, 0xEF, 0xF7, 0xFF)
        # Push PC to stack and jump to n*8
        if self.current_inst == 0xc7:
            address = 0x00
        elif self.current_inst == 0xcf:
            address = 0x08
        elif self.current_inst == 0xd7:
            address = 0x10
        elif self.current_inst == 0xdf:
            address = 0x18
        elif self.current_inst == 0xe7:
            address = 0x20
        elif self.current_inst == 0xef:
            address = 0x28
        elif self.current_inst == 0xf7:
            address = 0x30
        elif self.current_inst == 0xff:
            address = 0x38

        self.push_stack(self.PC)
        self.PC = address & 0xFFFF

    def execute_rlc(self):
        # Implements RLC: Rotate accumulator left
        # The high bit (bit 7) is rotated into both the carry flag and bit 0
        self.set_A(((self.A << 1) | (self.A >> 7)) & 0xFF)
        self.CARRY = bool((self.A & 0x01))

    def execute_ral(self):
        # Implements RAL: Rotate accumulator left through carry
        # The high bit (bit 7) goes into carry, carry goes into bit 0
        temp = self.A & 0xFF
        self.set_A(temp << 1)  # Shift left (set_A masks to 8 bits)
        if self.CARRY:
            self.set_A(self.A | 0x01)  # Set bit 0 if carry is set
        self.CARRY = bool((temp & 0x80))  # Save the high bit to carry

    def execute_rrc(self):
        # Implements RRC: Rotate accumulator right
        # The low bit (bit 0) is rotated into both the carry flag and bit 7
        self.set_A(((self.A >> 1) | (self.A << 7)) & 0xFF)
        self.CARRY = bool(self.A & 0x80)

    def execute_rar(self):
         # Implements RAR: Rotate accumulator right through carry
        # The low bit (bit 0) goes into carry, carry goes into bit 7
        temp = self.A & 0xFF
        self.set_A((self.A >> 1) & 0xFF)
        if self.CARRY:
            self.set_A(self.A | 0x80)
        self.CARRY = bool(temp & 0x01)  # Save the low bit to carry

    def execute_sta(self):
        # Implements STA addr, STAX B, STAX D instructions
        if self.current_inst == 0x02:  # STAX B (store A at (BC))
            self.write_byte(self.BC, self.A)
        elif self.current_inst == 0x12:  # STAX D (store A at (DE))
            self.write_byte(self.DE, self.A)
        elif self.current_inst == 0x32:  # STA addr
            immediate = self.fetch_rom_short() & 0xFFFF
            self.write_byte(immediate, self.A)

    def execute_di(self):
        # Implements DI: Disable interrupts
        self.INTERRUPT = False

    def execute_ei(self):
        # Implements EI: Enable interrupts
        self.INTERRUPT = True

    def execute_stc(self):
        # Implements STC: Set carry flag
        self.CARRY = True

    def execute_cmc(self):
        # Implements CMC: Complement carry flag
        self.CARRY = not self.CARRY

    def execute_lhld(self):
        # Implements LHLD addr: Load HL direct from memory (HL = [addr], [addr+1])
        immediate = self.fetch_rom_short() & 0xFFFF
        self.set_HL(self.read_short(immediate))

    def execute_shld(self):
        # Implements SHLD addr: Store HL direct to memory ([addr] = L, [addr+1] = H)
        immediate = self.fetch_rom_short() & 0xFFFF
        self.write_short(immediate, self.HL)

    def execute_daa(self):
        # Implements DAA: Decimal Adjust Accumulator
        # This instruction adjusts the accumulator for BCD addition
        if (self.A & 0x0F) > 9 or self.HALFCARRY:
            # If the lower nibble is greater than 9 or half-carry is set, adjust it
            self.A = (self.A + 0x06) & 0xFF
            self.HALFCARRY = True
        else:
            self.HALFCARRY = False
        
        if (self.A > 0x9F) or self.CARRY:
            # If the accumulator is greater than 0x9F or carry is set, adjust it
            self.A = (self.A + 0x60) & 0xFF
            self.CARRY = True
        else:
            self.CARRY = False
        
        self.set_flag_zero_sign()

    def execute_cma(self):
        # Implements CMA: Complement accumulator (A <- ~A)
        # self.A = (~self.A) & 0xFF
        self.set_A(self.A ^ 0xFF)

    def fetch_rom_byte(self):
        b = self.cpuMemoryPtr[self.PC]
        self.PC = (self.PC + 1) & 0xFFFF
        return b & 0xFF

    def fetch_rom_short(self):
        s = (self.cpuMemoryPtr[self.PC + 1] << 8) + (self.cpuMemoryPtr[self.PC])
        self.PC = (self.PC + 2) & 0xFFFF
        return (s & 0xFFFF)
    
    def set_A(self, inByte):
        self.A = inByte & 0xFF

    def set_B(self, inByte):
        self.B = inByte & 0xFF
        self.BC = ((self.B << 8) + self.C) & 0xFFFF

    def set_C(self, inByte):
        self.C = inByte & 0xFF
        self.BC = ((self.B << 8) + self.C) & 0xFFFF

    def set_D(self, inByte):
        self.D = inByte & 0xFF
        self.DE = ((self.D << 8) + self.E) & 0xFFFF
    
    def set_E(self, inByte):
        self.E = inByte & 0xFF
        self.DE = ((self.D << 8) + self.E) & 0xFFFF

    def set_H(self, inByte):
        self.H = inByte & 0xFF
        self.HL = ((self.H << 8) + self.L) & 0xFFFF

    def set_L(self, inByte):
        self.L = inByte & 0xFF
        self.HL = ((self.H << 8) + self.L) & 0xFFFF

    def set_BC(self, inShort):
        self.BC = inShort & 0xFFFF
        self.B = (self.BC >> 8) & 0xFF
        self.C = self.BC & 0xFF

    def set_DE(self, inShort):
        self.DE = inShort & 0xFFFF
        self.D = (self.DE >> 8) & 0xFF
        self.E = self.DE & 0xFF

    def set_HL(self, inShort):
        self.HL = inShort & 0xFFFF
        self.H = (self.HL >> 8) & 0xFF
        self.L = self.HL & 0xFF

    def set_SP(self, inShort):
        self.SP = inShort & 0xFFFF

    def read_byte(self, inAddr):
        return (self.cpuMemoryPtr[inAddr & 0xFFFF] & 0xFF)
    
    def read_short(self, inAddr):
        return (((self.cpuMemoryPtr[inAddr + 1] << 8) + (self.cpuMemoryPtr[inAddr])) & 0xFFFF)
    
    def write_byte(self, inAddr, inByte):
        self.cpuMemoryPtr[inAddr & 0xFFFF] = inByte & 0xFF

    def write_short(self, inAddr, inWord):
        self.cpuMemoryPtr[inAddr & 0xFFFF] = inWord & 0xFF
        self.cpuMemoryPtr[(inAddr + 1) & 0xFFFF] = (inWord >> 8) & 0xFF

    def push_stack(self, inValue):
        # Stack grows downward
        self.SP = (self.SP - 2) & 0xFFFF
        self.write_short(self.SP, inValue)

    def pop_stack(self):
        value = self.read_short(self.SP)
        self.SP = (self.SP + 2) & 0xFFFF
        return value
    
    def set_flag_zero_sign(self):
        self.ZERO = (self.A == 0)
        self.SIGN = ((self.A & 0x80) != 0)

    def perform_and(self, inByte):
        self.set_A(self.A & inByte)
        self.CARRY = False
        self.HALFCARRY = False
        self.set_flag_zero_sign()

    def perform_xor(self, inByte):
        self.set_A(self.A ^ inByte)
        self.CARRY = False
        self.HALFCARRY = False
        self.set_flag_zero_sign()

    def perform_or(self, inByte):
        self.set_A(self.A | inByte)
        self.CARRY = False
        self.HALFCARRY = False
        self.set_flag_zero_sign()

    def perform_byte_add(self, inByte, inCarryValue=0):
        value = self.A + inByte + inCarryValue
        self.HALFCARRY = bool((self.A ^ inByte ^ value) & 0x10)
        self.set_A(value)
        self.CARRY = (value > 0xFF)
        self.set_flag_zero_sign()

    def perform_inc(self, inByte):
        value = (inByte + 1) & 0xFFFF
        self.HALFCARRY = ((value & 0x0F) != 0)
        self.ZERO = ((value & 0xFF) == 0)  # Zero flag must test the whole byte, not just the low nibble
        self.SIGN = bool(value & 0x80)
        return value
    
    def perform_dec(self, inByte):
        value = (inByte - 1) & 0xFFFF
        self.HALFCARRY = ((value & 0x0F) == 0)
        self.ZERO = ((value & 0xFF) == 0)
        self.SIGN = bool(value & 0x80)
        return value
    
    def perform_byte_sub(self, inByte, inCarryByte=0):
        value = ((self.A - inByte - inCarryByte) & 0xFF)
        self.CARRY = ((value >= self.A) and (inByte | inCarryByte))
        self.HALFCARRY = bool((self.A ^ inByte ^ value) & 0x10)
        self.set_A(value)
        self.set_flag_zero_sign()

    def perform_comp_sub(self, inByte):
        value = (self.A - inByte) & 0xFF
        self.CARRY = (value >= self.A) and bool(inByte)
        self.HALFCARRY = bool((self.A ^ inByte ^ value) & 0x10)
        self.ZERO = (value == 0)
        self.SIGN = bool(value & 0x80)
    
    def parity(self, value):
        return _PARITY_TABLE[value & 0xFF]

    def get_debug_output(self):
        return self.debugOutputPtr

    def free(self):
        # Release references to memory and IO for cleanup
        self.cpuMemory = None
        self.cpuMemoryPtr = None
        self.cpuIo = None
