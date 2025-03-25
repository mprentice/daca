"""Module for representing and working with RAM programs."""

from abc import ABC
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Optional


class Opcode(StrEnum):
    """Enumeration of RAM instructions opcodes."""

    LOAD = "LOAD"
    STORE = "STORE"
    ADD = "ADD"
    SUB = "SUB"
    MULT = "MULT"
    DIV = "DIV"
    READ = "READ"
    WRITE = "WRITE"
    JUMP = "JUMP"
    JGTZ = "JGTZ"
    JZERO = "JZERO"
    HALT = "HALT"


@dataclass(frozen=True)
class Address[T: int | str](ABC):
    """ABC for instruction jump targets or operands."""

    value: T


@dataclass(frozen=True)
class JumpTarget(Address[str]):
    """Jump target label."""

    def __str__(self) -> str:
        return self.value


class OperandFlag(StrEnum):
    """Enumeration of operand type.

    An operand's value can be an integer literal, or a direct or indirect
    register reference.
    """

    literal = "="
    direct = ""
    indirect = "*"


@dataclass(frozen=True)
class Operand(Address[int]):
    """Instruction operand. The flag indicates the type of the operand."""

    flag: OperandFlag = OperandFlag.direct

    def __str__(self) -> str:
        return f"{self.flag.value}{self.value}"


@dataclass(frozen=True)
class Instruction:
    """A single RAM instruction.

    An instruction consists of an opcode and an optional address. An address
    can be an operand or a label.
    """

    opcode: Opcode
    address: Optional[Address] = None

    def __str__(self) -> str:
        if self.address:
            return f"{self.opcode.value} {self.address}"
        else:
            return f"{self.opcode.value}"


@dataclass(frozen=True)
class Program:
    """A RAM program consists of a sequence of instructions and a jumptable."""

    instructions: Sequence[Instruction]
    jumptable: Mapping[JumpTarget, int]

    def __str__(self) -> str:
        """Returns the text representation of the program."""
        pad = 0
        if self.jumptable:
            pad = max([len(k.value) for k in self.jumptable.keys()]) + 3
        jumplabels = {v: k for k, v in self.jumptable.items()}
        lines = []
        for index, inst in enumerate(self.instructions):
            label = jumplabels[index].value + ":" if index in jumplabels else ""
            address = "" if inst.address is None else str(inst.address)
            line = f"{label:<{pad}}{inst.opcode.value:<7}{address}".rstrip()
            lines.append(line)
        return "\n".join(lines)
