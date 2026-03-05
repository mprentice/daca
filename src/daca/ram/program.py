"""Module for representing and working with RAM programs."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from typing import Optional


class Opname(StrEnum):
    """Enumeration of RAM instruction names."""

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


class Opcode(IntEnum):
    """Enumeration of RAM instructions opcodes."""

    LOAD_DIRECT = 10
    LOAD_LITERAL = 11
    LOAD_INDIRECT = 12
    STORE_DIRECT = 20
    STORE_INDIRECT = 21
    ADD_DIRECT = 30
    ADD_LITERAL = 31
    ADD_INDIRECT = 32
    SUB_DIRECT = 40
    SUB_LITERAL = 41
    SUB_INDIRECT = 42
    MULT_DIRECT = 50
    MULT_LITERAL = 51
    MULT_INDIRECT = 52
    DIV_DIRECT = 60
    DIV_LITERAL = 61
    DIV_INDIRECT = 62
    READ_DIRECT = 70
    READ_INDIRECT = 71
    WRITE_DIRECT = 80
    WRITE_LITERAL = 81
    WRITE_INDIRECT = 82
    JUMP = 90
    JGTZ = 91
    JZERO = 92
    HALT = 99


class OperandFlag(StrEnum):
    LITERAL = "="
    INDIRECT = "*"
    DIRECT = ""


@dataclass(frozen=True)
class Instruction:
    """A single RAM instruction.

    An instruction consists of an opcode and an optional address. An address
    can be an operand or a label.
    """

    opcode: Opcode
    address: Optional[int | str] = None

    def __str__(self) -> str:
        if self.opcode == Opcode.HALT:
            return self.opcode.name
        elif self.opcode in (Opcode.JGTZ, Opcode.JZERO, Opcode.JUMP):
            return f"{self.opcode.name:<5} {self.address}"
        else:
            txt, flag = self.opcode.name.split("_")
            return f"{txt:<5} {OperandFlag[flag].value}{self.address}"


@dataclass(frozen=True)
class Program:
    """A RAM program consists of a sequence of instructions and a jumptable."""

    instructions: Sequence[Instruction]
    jumptable: Mapping[str, int]

    def __str__(self) -> str:
        """Returns the text representation of the program."""
        pad = 0
        if self.jumptable:
            pad = max([len(k) for k in self.jumptable.keys()]) + 3
        jumplabels = {v: k for k, v in self.jumptable.items()}
        lines = []
        for index, inst in enumerate(self.instructions):
            label = jumplabels[index] + ":" if index in jumplabels else ""
            line = f"{label:<{pad}}{inst}"
            lines.append(line)
        return "\n".join(lines)

    @property
    def bytecode(self) -> Sequence[int]:
        """A bytecode representation of the program."""
        buf: list[int] = []
        for inst in self.instructions:
            buf.append(inst.opcode.value)
            if inst.opcode == Opcode.HALT:
                buf.append(0)
            elif inst.opcode in (Opcode.JGTZ, Opcode.JUMP, Opcode.JZERO):
                assert isinstance(inst.address, str)
                buf.append(self.jumptable[inst.address] * 2)
            else:
                assert isinstance(inst.address, int)
                buf.append(inst.address)
        return buf
