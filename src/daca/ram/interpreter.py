from collections.abc import MutableMapping, MutableSequence, Sequence
from dataclasses import dataclass, field
from math import log2
from typing import Optional

from .program import OPCODE_BITMASK, OPTYPE_BITMASK, Opcode, OperandType, Program


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

    program: Program | Sequence[int] = (Opcode.HALT.value,)
    input_tape: Sequence[int] = field(default_factory=tuple)
    read_head: int = 0
    location_counter: int = 0
    memory_registers: MutableMapping[int, int] = field(default_factory=lambda: {0: 0})
    output_tape: MutableSequence[int] = field(default_factory=list)
    halted: bool = False
    step_counter: int = 0
    step_cost: int = 0
    _bytecode: Sequence[int] = field(init=False)

    def __post_init__(self):
        self._bytecode = (
            self.program.bytecode if isinstance(self.program, Program) else self.program
        )

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
        i = self._bytecode[self.location_counter] & OPCODE_BITMASK
        t = self._bytecode[self.location_counter] & OPTYPE_BITMASK
        a = self._bytecode[self.location_counter + 1]

        if self.halted:
            raise HaltError(
                f"Attempt to dispatch instruction: {Opcode(i).name} on HALTED machine"
            )

        m = getattr(self, Opcode(i).name)
        if i == Opcode.HALT.value:
            return m()
        elif i in (Opcode.JUMP.value, Opcode.JGTZ.value, Opcode.JZERO.value):
            return m(a)
        else:
            m = getattr(self, Opcode(i).name)
            return m((t, a))

    def LOAD(self, a: tuple[int, int]) -> int:
        """LOAD a: c(0) ← v(a)"""
        self.step_cost += self.t(a)
        self.set_c(0, self.v(a))
        return self.location_counter + 2

    def STORE(self, i: tuple[int, int]) -> int:
        """STORE i: c(i) ← c(0)

        STORE *i: c(c(i)) ← c(0)
        """
        optype, value = i
        if optype == OperandType.INDIRECT.value:
            self.step_cost += (
                log_cost(self.c(0)) + log_cost(value) + log_cost(self.c(value))
            )
            self.set_c(self.c(value), self.c(0))
        else:
            self.step_cost += log_cost(self.c(0)) + log_cost(value)
            self.set_c(value, self.c(0))
        return self.location_counter + 2

    def ADD(self, a: tuple[int, int]) -> int:
        """ADD a: c(0) ← c(0) + v(a)"""
        self.step_cost += log_cost(self.c(0)) + self.t(a)
        self.set_c(0, self.c(0) + self.v(a))
        return self.location_counter + 2

    def SUB(self, a: tuple[int, int]) -> int:
        """SUB a: c(0) ← c(0) - v(a)"""
        self.step_cost += log_cost(self.c(0)) + self.t(a)
        self.set_c(0, self.c(0) - self.v(a))
        return self.location_counter + 2

    def MULT(self, a: tuple[int, int]) -> int:
        """MULT a: c(0) ← c(0) * v(a)"""
        self.step_cost += log_cost(self.c(0)) + self.t(a)
        self.set_c(0, self.c(0) * self.v(a))
        return self.location_counter + 2

    def DIV(self, a: tuple[int, int]) -> int:
        """DIV a: c(0) ← c(0) * v(a)"""
        self.step_cost += log_cost(self.c(0)) + self.t(a)
        self.set_c(0, self.c(0) // self.v(a))
        return self.location_counter + 2

    def READ(self, i: tuple[int, int]) -> int:
        """READ i: c(i) ← current input tape symbol

        READ *i: c(c(i)) ← current input tape symbol

        Input tape head moves one square right.

        If reading past the end of the input tape, the input tape symbol is
        assumed to be 0.
        """
        optype, value = i

        try:
            space = self.input_tape[self.read_head]
        except IndexError:
            space = 0

        self.read_head += 1

        if optype == OperandType.INDIRECT.value:
            self.step_cost += (
                log_cost(space) + log_cost(value) + log_cost(self.c(value))
            )
            self.set_c(self.c(value), space)
        else:
            self.step_cost += log_cost(space) + log_cost(value)
            self.set_c(value, space)

        return self.location_counter + 2

    def WRITE(self, a: tuple[int, int]) -> int:
        """WRITE a: v(a) is printed on the output tape

        Output tape head moves one square right.
        """
        self.step_cost += self.t(a)
        self.output_tape.append(self.v(a))
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

    def v(self, a: tuple[int, int]) -> int:
        """v(a): Return the value for address a.

        Address can be one of:
            =i Literal value of integer i
            i  Integer value stored at register i (default)
            *i Integer value stored at the register number stored in register i
               (indirect address)
        """
        optype, value = a
        if optype == OperandType.LITERAL.value:
            return value
        elif optype == OperandType.INDIRECT:
            return self.c(self.c(value))
        else:
            return self.c(value)

    def t(self, a: tuple[int, int]) -> int:
        """Logarithmic cost t(a) for an operand."""
        optype, value = a
        if optype == OperandType.LITERAL.value:
            return log_cost(value)
        elif optype == OperandType.INDIRECT.value:
            return (
                log_cost(value)
                + log_cost(self.c(value))
                + log_cost(self.c(self.c(value)))
            )
        else:
            return log_cost(a[1]) + log_cost(self.c(value))

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
