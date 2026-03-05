from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from dataclasses import dataclass, field
from math import log2
from typing import ClassVar, Optional

from .program import Instruction, Opcode, OperandFlag


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

    program: Sequence[int] = (Opcode.HALT.value,)
    input_tape: Sequence[int] = field(default_factory=tuple)
    read_head: int = 0
    location_counter: int = 0
    memory_registers: MutableMapping[int, int] = field(default_factory=lambda: {0: 0})
    output_tape: MutableSequence[int] = field(default_factory=list)
    halted: bool = False
    step_counter: int = 0
    step_cost: int = 0

    dispatch_table: ClassVar[Mapping[int, str]] = {
        Opcode.LOAD_DIRECT.value: Opcode.LOAD_DIRECT.name.split("_")[0],
        Opcode.LOAD_LITERAL.value: Opcode.LOAD_LITERAL.name.split("_")[0],
        Opcode.LOAD_INDIRECT.value: Opcode.LOAD_INDIRECT.name.split("_")[0],
        Opcode.STORE_DIRECT.value: Opcode.STORE_DIRECT.name.split("_")[0],
        Opcode.STORE_INDIRECT.value: Opcode.STORE_INDIRECT.name.split("_")[0],
        Opcode.ADD_DIRECT.value: Opcode.ADD_DIRECT.name.split("_")[0],
        Opcode.ADD_LITERAL.value: Opcode.ADD_LITERAL.name.split("_")[0],
        Opcode.ADD_INDIRECT.value: Opcode.ADD_INDIRECT.name.split("_")[0],
        Opcode.SUB_DIRECT.value: Opcode.SUB_DIRECT.name.split("_")[0],
        Opcode.SUB_LITERAL.value: Opcode.SUB_LITERAL.name.split("_")[0],
        Opcode.SUB_INDIRECT.value: Opcode.SUB_INDIRECT.name.split("_")[0],
        Opcode.MULT_DIRECT.value: Opcode.MULT_DIRECT.name.split("_")[0],
        Opcode.MULT_LITERAL.value: Opcode.MULT_LITERAL.name.split("_")[0],
        Opcode.MULT_INDIRECT.value: Opcode.MULT_INDIRECT.name.split("_")[0],
        Opcode.DIV_DIRECT.value: Opcode.DIV_DIRECT.name.split("_")[0],
        Opcode.DIV_LITERAL.value: Opcode.DIV_LITERAL.name.split("_")[0],
        Opcode.DIV_INDIRECT.value: Opcode.DIV_INDIRECT.name.split("_")[0],
        Opcode.READ_DIRECT.value: Opcode.READ_DIRECT.name.split("_")[0],
        Opcode.READ_INDIRECT.value: Opcode.READ_INDIRECT.name.split("_")[0],
        Opcode.WRITE_DIRECT.value: Opcode.WRITE_DIRECT.name.split("_")[0],
        Opcode.WRITE_LITERAL.value: Opcode.WRITE_LITERAL.name.split("_")[0],
        Opcode.WRITE_INDIRECT.value: Opcode.WRITE_INDIRECT.name.split("_")[0],
        Opcode.JUMP.value: Opcode.JUMP.name,
        Opcode.JGTZ.value: Opcode.JGTZ.name,
        Opcode.JZERO.value: Opcode.JZERO.name,
        Opcode.HALT.value: Opcode.HALT.name,
    }

    dispatch_flag: ClassVar[Mapping[int, OperandFlag]] = {
        Opcode.LOAD_DIRECT.value: OperandFlag.DIRECT,
        Opcode.LOAD_LITERAL.value: OperandFlag.LITERAL,
        Opcode.LOAD_INDIRECT.value: OperandFlag.INDIRECT,
        Opcode.STORE_DIRECT.value: OperandFlag.DIRECT,
        Opcode.STORE_INDIRECT.value: OperandFlag.INDIRECT,
        Opcode.ADD_DIRECT.value: OperandFlag.DIRECT,
        Opcode.ADD_LITERAL.value: OperandFlag.LITERAL,
        Opcode.ADD_INDIRECT.value: OperandFlag.INDIRECT,
        Opcode.SUB_DIRECT.value: OperandFlag.DIRECT,
        Opcode.SUB_LITERAL.value: OperandFlag.LITERAL,
        Opcode.SUB_INDIRECT.value: OperandFlag.INDIRECT,
        Opcode.MULT_DIRECT.value: OperandFlag.DIRECT,
        Opcode.MULT_LITERAL.value: OperandFlag.LITERAL,
        Opcode.MULT_INDIRECT.value: OperandFlag.INDIRECT,
        Opcode.DIV_DIRECT.value: OperandFlag.DIRECT,
        Opcode.DIV_LITERAL.value: OperandFlag.LITERAL,
        Opcode.DIV_INDIRECT.value: OperandFlag.INDIRECT,
        Opcode.READ_DIRECT.value: OperandFlag.DIRECT,
        Opcode.READ_INDIRECT.value: OperandFlag.INDIRECT,
        Opcode.WRITE_DIRECT.value: OperandFlag.DIRECT,
        Opcode.WRITE_LITERAL.value: OperandFlag.LITERAL,
        Opcode.WRITE_INDIRECT.value: OperandFlag.INDIRECT,
    }

    def reset(self) -> None:
        self.read_head = 0
        self.location_counter = 0
        self.memory_registers = {0: 0}
        self.output_tape = []
        self.halted = False
        self.step_counter = 0
        self.step_cost = 0

    def run(self, input_tape: Optional[Sequence[int]] = None) -> None:
        """Run the machine until reaching a halting state.

        Steps through the next instruction until halting by repeatedly calling
        the step method.

        Throws:
            HaltError if the machine is in a halted state.
            ReadError if attempting to read past the end of the input tape.
        """
        if input_tape is not None:
            self.input_tape = input_tape
        self.reset()
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
        self.location_counter = self.dispatch()
        self.step_counter += 1

    def dispatch(self) -> int:
        """Dispatch and run one instruction (one step).

        Returns location counter for next instruction.
        """
        i, a = self.program[self.location_counter : self.location_counter + 2]

        if self.halted:
            inst = Instruction(Opcode(i), a)
            raise HaltError(
                f"Attempt to dispatch instruction: {inst} on halted machine state"
            )

        m = getattr(self, self.dispatch_table[i])
        if i == Opcode.HALT.value:
            return m()
        elif i in (Opcode.JUMP.value, Opcode.JGTZ.value, Opcode.JZERO.value):
            return m(a)
        else:
            flag = self.dispatch_flag[i]
            return m(a, flag)

    def LOAD(self, a: int, flag: OperandFlag) -> int:
        """LOAD a: c(0) ← v(a)"""
        self.step_cost += self.t(a, flag)
        self.set_c(0, self.v(a, flag))
        return self.location_counter + 2

    def STORE(self, i: int, flag: OperandFlag) -> int:
        """STORE i: c(i) ← c(0)

        STORE *i: c(c(i)) ← c(0)
        """
        if flag == OperandFlag.INDIRECT:
            self.step_cost += log_cost(self.c(0)) + log_cost(i) + log_cost(self.c(i))
            self.set_c(self.c(i), self.c(0))
        else:
            self.step_cost += log_cost(self.c(0)) + log_cost(i)
            self.set_c(i, self.c(0))
        return self.location_counter + 2

    def ADD(self, a: int, flag: OperandFlag) -> int:
        """ADD a: c(0) ← c(0) + v(a)"""
        self.step_cost += log_cost(self.c(0)) + self.t(a, flag)
        self.set_c(0, self.c(0) + self.v(a, flag))
        return self.location_counter + 2

    def SUB(self, a: int, flag: OperandFlag) -> int:
        """SUB a: c(0) ← c(0) - v(a)"""
        self.step_cost += log_cost(self.c(0)) + self.t(a, flag)
        self.set_c(0, self.c(0) - self.v(a, flag))
        return self.location_counter + 2

    def MULT(self, a: int, flag: OperandFlag) -> int:
        """MULT a: c(0) ← c(0) * v(a)"""
        self.step_cost += log_cost(self.c(0)) + self.t(a, flag)
        self.set_c(0, self.c(0) * self.v(a, flag))
        return self.location_counter + 2

    def DIV(self, a: int, flag: OperandFlag) -> int:
        """DIV a: c(0) ← c(0) * v(a)"""
        self.step_cost += log_cost(self.c(0)) + self.t(a, flag)
        self.set_c(0, self.c(0) // self.v(a, flag))
        return self.location_counter + 2

    def READ(self, i: int, flag: OperandFlag) -> int:
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

        if flag == OperandFlag.INDIRECT:
            self.step_cost += log_cost(space) + log_cost(i) + log_cost(self.c(i))
            self.set_c(self.c(i), space)
        else:
            self.step_cost += log_cost(space) + log_cost(i)
            self.set_c(i, space)

        return self.location_counter + 2

    def WRITE(self, a: int, flag: OperandFlag) -> int:
        """WRITE a: v(a) is printed on the output tape

        Output tape head moves one square right.
        """
        self.step_cost += self.t(a, flag)
        self.output_tape.append(self.v(a, flag))
        return self.location_counter + 2

    def JUMP(self, b: int) -> int:
        """JUMP b: set location counter to instruction labeled b"""
        self.step_cost += 1
        return b

    def JGTZ(self, b: int) -> int:
        """JGTZ b: conditionally set location counter to instruction labeled b

        If c(0) > 0: set location counter to instruction labeled b

        Otherwise, set location counter to next instruction"""
        self.step_cost += log_cost(self.c(0))
        if self.c(0) > 0:
            return b
        else:
            return self.location_counter + 2

    def JZERO(self, b: int) -> int:
        """JZERO b: conditionally set location counter to instruction labeled b

        If c(0) = 0: set location counter to instruction labeled b

        Otherwise, set location counter to next instruction"""
        self.step_cost += log_cost(self.c(0))
        if self.c(0) == 0:
            return b
        else:
            return self.location_counter + 2

    def HALT(self) -> int:
        """Halt execution of machine."""
        self.step_cost += 1
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

    def v(self, a: int, flag: OperandFlag = OperandFlag.DIRECT) -> int:
        """v(a): Return the value for address a.

        Address can be one of:
            =i Literal value of integer i
            i  Integer value stored at register i (default)
            *i Integer value stored at the register number stored in register i
               (indirect address)

        Set flag to OperandFlag.INDIRECT or OperandFlag.LITERAL as appropriate.
        """
        if flag == OperandFlag.LITERAL:
            return a
        elif flag == OperandFlag.INDIRECT:
            return self.c(self.c(a))
        else:
            return self.c(a)

    def t(self, a: int, flag: OperandFlag = OperandFlag.DIRECT) -> int:
        """Logarithmic cost t(a) for an operand.

        Set flag to OperandFlag.INDIRECT or OperandFlag.LITERAL as appropriate.
        """
        if flag == OperandFlag.LITERAL:
            return log_cost(a)
        elif flag == OperandFlag.INDIRECT:
            return log_cost(a) + log_cost(self.c(a)) + log_cost(self.c(self.c(a)))
        else:
            return log_cost(a) + log_cost(self.c(a))

    @property
    def log_space_cost(self) -> int:
        """Logarithmic space cost of the RAM's memory."""
        return sum(log_cost(i) for i in self.memory_registers.values())

    @property
    def uniform_space_cost(self) -> int:
        """Uniform space cost of the RAM's memory."""
        return len(self.memory_registers.values())


def log_cost(i: int) -> int:
    """Logarithmic cost function for integers."""
    return 1 if i == 0 else int(log2(abs(i))) + 1
