from abc import ABC
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum, StrEnum, auto
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
    value: T


@dataclass(frozen=True)
class JumpTarget(Address[str]):
    pass


class OperandFlag(Enum):
    literal = auto()
    direct = auto()
    indirect = auto()


@dataclass(frozen=True)
class Operand(Address[int]):
    flag: OperandFlag = OperandFlag.direct


@dataclass(frozen=True)
class Instruction:
    """Representation of a single RAM instruction.

    An instruction consists of an opcode and an optional address. An address
    can be an operand or a label. An instruction cannot be modified.

    """

    opcode: Opcode
    address: Optional[Address] = None


@dataclass(frozen=True)
class Program:
    """Representation of a RAM program. Cannot be modified."""

    instructions: Sequence[Instruction]
    jumptable: Mapping[JumpTarget, int]

    def serialize(self):
        pad = 0
        if self.jumptable:
            pad = max([len(k.value) for k in self.jumptable.keys()]) + 3
        jumplabels = {v: k for k, v in self.jumptable.items()}
        lines = []
        for index, inst in enumerate(self.instructions):
            label = jumplabels[index].value + ":" if index in jumplabels else ""
            address = ""
            if isinstance(inst.address, JumpTarget):
                address = inst.address.value
            elif (
                isinstance(inst.address, Operand)
                and inst.address.flag == OperandFlag.literal
            ):
                address = f"={inst.address.value}"
            elif (
                isinstance(inst.address, Operand)
                and inst.address.flag == OperandFlag.indirect
            ):
                address = f"*{inst.address.value}"
            elif (
                isinstance(inst.address, Operand)
                and inst.address.flag == OperandFlag.direct
            ):
                address = f"{inst.address.value}"
            line = f"{label:<{pad}}{inst.opcode.value:<7}{address}".rstrip()
            lines.append(line)
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.serialize()
