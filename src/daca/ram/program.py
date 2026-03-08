"""Module for representing and working with RAM programs."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import IntEnum

from daca.common import pairwise


class Opcode(IntEnum):
    """Enumeration of RAM instructions opcodes."""

    LOAD = 4
    STORE = 8
    ADD = 12
    SUB = 16
    MULT = 20
    DIV = 24
    READ = 28
    WRITE = 32
    JUMP = 36
    JGTZ = 40
    JZERO = 44
    HALT = 48


OPCODE_BITMASK = 0b111100


class OperandType(IntEnum):
    """Enumeration of RAM operand memory access types.

    - DIRECT: Operand is a memory location containing value to use.

    - LITERAL: Operand is a literal integer value.

    - INDIRECT: Operand is a memory location pointing to another memory
                location with the value to use.
    """

    DIRECT = 0
    LITERAL = 1
    INDIRECT = 2


OPTYPE_BITMASK = 0b11


@dataclass(frozen=True)
class Operand:
    """A RAM operand consists of an integer value and a memory access type."""

    value: int = 0
    optype: OperandType = OperandType.DIRECT

    def __str__(self) -> str:
        if self.optype == OperandType.DIRECT:
            return f"{self.value}"
        elif self.optype == OperandType.LITERAL:
            return f"={self.value}"
        else:
            return f"*{self.value}"


@dataclass(frozen=True)
class Instruction:
    """A single RAM instruction.

    An instruction consists of an opcode and an optional address. An address
    can be an operand or a label.
    """

    opcode: Opcode
    address: str | Operand = Operand()

    def __str__(self) -> str:
        if self.opcode == Opcode.HALT:
            return self.opcode.name
        else:
            return f"{self.opcode.name:<5} {self.address}"


@dataclass(frozen=True)
class Program:
    """A RAM program consists of a sequence of instructions and a jumptable."""

    instructions: Sequence[Instruction]
    jumptable: Mapping[str, int]

    def __str__(self) -> str:
        """Returns the text representation of the program."""
        pad = max([len(k) for k in self.jumptable.keys()]) + 2 if self.jumptable else 0
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
            if inst.opcode == Opcode.HALT:
                buf.append(inst.opcode.value)
                buf.append(0)
            elif inst.opcode in (Opcode.JGTZ, Opcode.JUMP, Opcode.JZERO):
                assert isinstance(inst.address, str)
                buf.append(inst.opcode.value)
                buf.append(self.jumptable[inst.address] * 2)
            else:
                assert isinstance(inst.address, Operand)
                buf.append(inst.opcode.value | inst.address.optype.value)
                buf.append(inst.address.value)
        return buf

    @classmethod
    def from_bytecode(
        cls, bytecode: Sequence[int], jumptable: Mapping[str, int] | None = None
    ) -> "Program":
        """Construct a Program from RAM bytecode.

        A jumptable is optional to restore original instruction labels.
        """
        n: int = 1
        new_jumptable: dict[str, int] = dict(jumptable) if jumptable else {}
        jumplabels = {v * 2: k for k, v in new_jumptable.items()}

        instructions: list[Instruction] = []

        for i, a in pairwise(bytecode):
            opcode = Opcode(i & OPCODE_BITMASK)
            if opcode == Opcode.HALT:
                instructions.append(Instruction(opcode=opcode))
            elif opcode in (Opcode.JGTZ, Opcode.JUMP, Opcode.JZERO):
                if a not in jumplabels:
                    lbl = f"lbl{n}"
                    n += 1
                    jumplabels[a] = lbl
                    new_jumptable[lbl] = a // 2
                instructions.append(Instruction(opcode=opcode, address=jumplabels[a]))
            else:
                address = Operand(value=a, optype=OperandType(i & OPTYPE_BITMASK))
                inst = Instruction(opcode=opcode, address=address)
                instructions.append(inst)

        return cls(instructions=instructions, jumptable=new_jumptable)
