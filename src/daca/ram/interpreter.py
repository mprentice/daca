from collections.abc import MutableMapping, MutableSequence, Sequence
from dataclasses import dataclass, field

from .program import Instruction, JumpTarget, Opcode, Operand, OperandFlag, Program


class HaltError(ValueError):
    """Thrown when trying to execute a halted RAM."""


class ReadError(IndexError):
    """Thrown when trying to read past end of input tape."""


@dataclass
class RAM:
    """A random access machine (RAM) models a one-accumulator computer.

    A RAM consists of a read-only input tape, a write-only output tape, a
    program, and registers (memory). Instructions are not permitted to modify
    themselves. Memory is an arbitrarily large sequence of integer registers.

    The machine execution methods (LOAD, STORE, ADD, JUMP, etc.) are in all
    caps and should not be called directly.

    The run and step methods raise errors if the machine is in a halted state.
    """

    program: Program
    input_tape: Sequence[int] = field(default_factory=tuple)
    read_head: int = 0
    location_counter: int = 0
    memory_registers: MutableMapping[int, int] = field(default_factory=lambda: {0: 0})
    output_tape: MutableSequence[int] = field(default_factory=list)
    halted: bool = False
    step_counter: int = 0

    def run(self) -> None:
        """Run the machine until reaching a halting state.

        Steps through the next instruction until halting by repeatedly calling
        the step method.

        Throws:
            HaltError if the machine is in a halted state.
            ReadError if attempting to read past the end of the input tape.

        """
        while not self.halted:
            self.step()

    def step(self) -> None:
        """Execute the next instruction.

        Throws:
            HaltError if the machine is in a halted state.
            ReadError if attempting to read past the end of the input tape.

        """
        if self.halted:
            raise HaltError("Attempt to step program on halted machine state")
        self.location_counter = self.dispatch(
            self.program.instructions[self.location_counter]
        )
        self.step_counter += 1

    def dispatch(self, ins: Instruction) -> int:
        """Dispatch and run one instruction (one step).

        Returns location counter for next instruction.
        """
        if self.halted:
            raise HaltError(
                f"Attempt to dispatch instruction: {ins} on halted machine state"
            )
        m = getattr(self, ins.opcode.value)
        a = ins.address
        if ins.opcode == Opcode.HALT:
            return m()
        else:
            return m(a)

    def LOAD(self, a: Operand) -> int:
        """LOAD a: c(0) ← v(a)"""
        self.set_c(0, self.v(a))
        return self.location_counter + 1

    def STORE(self, i: Operand) -> int:
        """STORE i: c(i) ← c(0)

        STORE *i: c(c(i)) ← c(0)
        """
        if i.flag == OperandFlag.indirect:
            self.set_c(self.c(i.value), self.c(0))
        else:
            self.set_c(i.value, self.c(0))
        return self.location_counter + 1

    def ADD(self, a: Operand) -> int:
        """ADD a: c(0) ← c(0) + v(a)"""
        self.set_c(0, self.c(0) + self.v(a))
        return self.location_counter + 1

    def SUB(self, a: Operand) -> int:
        """SUB a: c(0) ← c(0) - v(a)"""
        self.set_c(0, self.c(0) - self.v(a))
        return self.location_counter + 1

    def MULT(self, a: Operand) -> int:
        """MULT a: c(0) ← c(0) * v(a)"""
        self.set_c(0, self.c(0) * self.v(a))
        return self.location_counter + 1

    def DIV(self, a: Operand) -> int:
        """DIV a: c(0) ← c(0) * v(a)"""
        self.set_c(0, self.c(0) // self.v(a))
        return self.location_counter + 1

    def READ(self, i: Operand) -> int:
        """READ i: c(i) ← current input tape symbol

        READ *i: c(c(i)) ← current input tape symbol

        Input tape head moves one square right.

        If reading past the end of the input tape, the input tape symbol is
        assumed to be 0.
        """
        try:
            space = self.input_tape[self.read_head]
        except IndexError:
            space = 0

        self.read_head += 1

        if i.flag == OperandFlag.indirect:
            self.set_c(self.c(i.value), space)
        else:
            self.set_c(i.value, space)

        return self.location_counter + 1

    def WRITE(self, a: Operand) -> int:
        """WRITE a: v(a) is printed on the output tape

        Output tape head moves one square right.
        """
        self.output_tape.append(self.v(a))
        return self.location_counter + 1

    def JUMP(self, b: JumpTarget) -> int:
        """JUMP b: set location counter to instruction labeled b"""
        return self.program.jumptable[b]

    def JGTZ(self, b: JumpTarget) -> int:
        """JGTZ b: conditionally set location counter to instruction labeled b

        If c(0) > 0: set location counter to instruction labeled b

        Otherwise, set location counter to next instruction"""
        if self.c(0) > 0:
            return self.program.jumptable[b]
        else:
            return self.location_counter + 1

    def JZERO(self, b: JumpTarget) -> int:
        """JZERO b: conditionally set location counter to instruction labeled b

        If c(0) = 0: set location counter to instruction labeled b

        Otherwise, set location counter to next instruction"""
        if self.c(0) == 0:
            return self.program.jumptable[b]
        else:
            return self.location_counter + 1

    def HALT(self) -> int:
        """Halt execution of machine."""
        self.halted = True
        return self.location_counter

    def c(self, i: int) -> int:
        """c(i): Return the value stored at register i."""
        try:
            return self.memory_registers[i]
        except KeyError as ex:
            raise IndexError(f"Read from uninitialized memory register {i}") from ex

    def set_c(self, i: int, v: int) -> None:
        """c(i) ← v: Set the value at register i to v."""
        self.memory_registers[i] = v

    def v(self, a: Operand) -> int:
        """v(a): Return the value for address a.

        Address can be one of:
            =i Literal value of integer i
            i  Integer value stored at register i
            *i Integer value stored at the register number stored in register i
               (indirect address)

        """
        if a.flag == OperandFlag.literal:
            return a.value
        elif a.flag == OperandFlag.indirect:
            return self.c(self.c(a.value))
        else:
            return self.c(a.value)
