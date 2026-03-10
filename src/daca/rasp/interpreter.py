from collections.abc import MutableMapping, MutableSequence, Sequence
from dataclasses import dataclass, field
from math import log2
from typing import Optional

from daca.common import HaltError

from .program import Opcode, Program


@dataclass
class RASP:
    """A random access stored program (RASP) models a one-accumulator computer.

    A RASP consists of a read-only input tape, a write-only output tape, and
    registers (memory). Instructions are permitted to modify themselves. Memory
    is an arbitrarily large sequence of integer registers. Memory is
    initialized with a 0 in register 0, and registers 1 to 2 * n filled with
    the program's bytecode, where n is the number of instructions.

    The machine execution methods (LOAD, STORE, ADD, JUMP, etc.) are in all
    caps and should not be called directly.

    The run and step methods raise errors if the machine is in a halted state.

    """

    program: Program | Sequence[int] = (Opcode.HALT.value,)
    input_tape: Sequence[int] = field(default_factory=tuple)
    read_head: int = 0
    location_counter: int = 1
    memory_registers: MutableMapping[int, int] = field(default_factory=lambda: {0: 0})
    output_tape: MutableSequence[int] = field(default_factory=list)
    halted: bool = False
    step_counter: int = 0
    step_cost: int = 0

    def __post_init__(self):
        self.reset()

    def reset(self) -> None:
        self.read_head = 0
        self.location_counter = 1
        self.memory_registers = {0: 0}
        self.output_tape = []
        self.halted = False
        self.step_counter = 0
        self.step_cost = 0
        bytecode = (
            self.program.bytecode if isinstance(self.program, Program) else self.program
        )
        self.memory_registers.update({idx + 1: b for idx, b in enumerate(bytecode)})

    def run(self, input_tape: Optional[Sequence[int]] = None) -> None:
        """Run the machine until reaching a halting state.

        Steps through the next instruction until halting by repeatedly calling
        the step method.

        Throws:
            HaltError if the machine is in a halted state.
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
        """
        if self.halted:
            raise HaltError("Attempt to step program on halted machine state")
        self.location_counter = self.dispatch()
        self.step_counter += 1

    def dispatch(self) -> int:
        """Dispatch and run one instruction (one step).

        Returns location counter for next instruction.
        """
        i = self.memory_registers[self.location_counter]
        a = self.memory_registers[self.location_counter + 1]

        if self.halted:
            raise HaltError(
                f"Attempt to dispatch instruction: {Opcode(i).name} on HALTED machine"
            )

        m = getattr(self, Opcode(i).name)
        if i == Opcode.HALT.value:
            return m()
        else:
            return m(a)

    def LOAD(self, a: int) -> int:
        """LOAD a: c(0) ← v(a)"""
        self.step_cost += self.t(a)
        self.set_c(0, self.v(a))
        return self.location_counter + 2

    def LOAD_LITERAL(self, a: int) -> int:
        """LOAD a: c(0) ← v(a)"""
        self.step_cost += self.t_literal(a)
        self.set_c(0, self.v_literal(a))
        return self.location_counter + 2

    def STORE(self, i: int) -> int:
        """STORE i: c(i) ← c(0)"""
        self.step_cost += log_cost(self.c(0)) + log_cost(i)
        self.set_c(i, self.c(0))
        return self.location_counter + 2

    def ADD(self, a: int) -> int:
        """ADD a: c(0) ← c(0) + v(a)"""
        self.step_cost += log_cost(self.c(0)) + self.t(a)
        self.set_c(0, self.c(0) + self.v(a))
        return self.location_counter + 2

    def ADD_LITERAL(self, a: int) -> int:
        """ADD a: c(0) ← c(0) + v(a)"""
        self.step_cost += log_cost(self.c(0)) + self.t_literal(a)
        self.set_c(0, self.c(0) + self.v_literal(a))
        return self.location_counter + 2

    def SUB(self, a: int) -> int:
        """SUB a: c(0) ← c(0) - v(a)"""
        self.step_cost += log_cost(self.c(0)) + self.t(a)
        self.set_c(0, self.c(0) - self.v(a))
        return self.location_counter + 2

    def SUB_LITERAL(self, a: int) -> int:
        """SUB a: c(0) ← c(0) - v(a)"""
        self.step_cost += log_cost(self.c(0)) + self.t_literal(a)
        self.set_c(0, self.c(0) - self.v_literal(a))
        return self.location_counter + 2

    def MULT(self, a: int) -> int:
        """MULT a: c(0) ← c(0) * v(a)"""
        self.step_cost += log_cost(self.c(0)) + self.t(a)
        self.set_c(0, self.c(0) * self.v(a))
        return self.location_counter + 2

    def MULT_LITERAL(self, a: int) -> int:
        """MULT a: c(0) ← c(0) * v(a)"""
        self.step_cost += log_cost(self.c(0)) + self.t_literal(a)
        self.set_c(0, self.c(0) * self.v_literal(a))
        return self.location_counter + 2

    def DIV(self, a: int) -> int:
        """DIV a: c(0) ← c(0) * v(a)"""
        self.step_cost += log_cost(self.c(0)) + self.t(a)
        self.set_c(0, self.c(0) // self.v(a))
        return self.location_counter + 2

    def DIV_LITERAL(self, a: int) -> int:
        """DIV a: c(0) ← c(0) * v(a)"""
        self.step_cost += log_cost(self.c(0)) + self.t_literal(a)
        self.set_c(0, self.c(0) // self.v_literal(a))
        return self.location_counter + 2

    def READ(self, i: int) -> int:
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

        self.step_cost += log_cost(space) + log_cost(i)
        self.set_c(i, space)

        return self.location_counter + 2

    def WRITE(self, a: int) -> int:
        """WRITE a: v(a) is printed on the output tape

        Output tape head moves one square right.
        """
        self.step_cost += self.t(a)
        self.output_tape.append(self.v(a))
        return self.location_counter + 2

    def WRITE_LITERAL(self, a: int) -> int:
        """WRITE a: v(a) is printed on the output tape

        Output tape head moves one square right.
        """
        self.step_cost += self.t_literal(a)
        self.output_tape.append(self.v_literal(a))
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

    def v(self, a: int) -> int:
        """v(a): Return the value for address a.

        Address can be one of:
            =i Literal value of integer i
            i  Integer value stored at register i (default)
        """
        return self.c(a)

    def v_literal(self, a: int) -> int:
        """v(a): Return the value for address a.

        Address can be one of:
            =i Literal value of integer i
            i  Integer value stored at register i (default)
        """
        return a

    def t(self, a: int) -> int:
        """Logarithmic cost t(a) for an operand."""
        return log_cost(a) + log_cost(self.c(a)) + log_cost(self.location_counter)

    def t_literal(self, a: int) -> int:
        """Logarithmic cost t(a) for an operand."""
        return log_cost(a) + log_cost(self.location_counter)

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
