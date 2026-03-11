"""Module for representing and working with RASP programs."""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import IntEnum

from daca.common import pairwise


class Opcode(IntEnum):
    """Enumeration of RASP instructions opcodes."""

    LOAD = 1
    LOAD_LITERAL = 2
    STORE = 3
    ADD = 4
    ADD_LITERAL = 5
    SUB = 6
    SUB_LITERAL = 7
    MULT = 8
    MULT_LITERAL = 9
    DIV = 10
    DIV_LITERAL = 11
    READ = 12
    WRITE = 13
    WRITE_LITERAL = 14
    JUMP = 15
    JGTZ = 16
    JZERO = 17
    HALT = 18


@dataclass(frozen=True)
class Instruction:
    """A single RASP instruction.

    An instruction consists of an opcode and an optional address.
    """

    opcode: Opcode
    address: int = 0

    def __str__(self) -> str:
        if self.opcode == Opcode.HALT:
            return self.opcode.name
        elif self.opcode.name.endswith("_LITERAL"):
            return f"{self.opcode.name.split('_')[0]:<5} ={self.address}"
        else:
            return f"{self.opcode.name:<5} {self.address}"


@dataclass(frozen=True)
class Program:
    """A RASP program consists of a sequence of instructions.

    It is very similar to a RAM program except that:

    1. There is no indirect memory access operand type.

    2. The program is stored in registers 1 through 2 * n, where n is the
       number of instructions. Each instruction takes two (2) registers, one
       for the opcode and one for the address.

    3. There is no jumptable since jump addresses must be a literal integer
       value.
    """

    instructions: Sequence[Instruction]

    def __str__(self) -> str:
        """Returns the text representation of the program."""
        return "\n".join([f"{inst}" for inst in self.instructions])

    @property
    def bytecode(self) -> Sequence[int]:
        """A bytecode representation of the program."""
        buf: list[int] = []
        for inst in self.instructions:
            buf.append(inst.opcode.value)
            buf.append(inst.address)
        return buf

    @classmethod
    def from_bytecode(cls, bytecode: Sequence[int]) -> "Program":
        """Construct a Program from RASP bytecode."""
        instructions: list[Instruction] = []
        for i, a in pairwise(bytecode):
            instructions.append(Instruction(opcode=Opcode(i), address=a))
        return cls(instructions=instructions)
