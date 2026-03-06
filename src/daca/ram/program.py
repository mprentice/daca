"""Module for representing and working with RAM programs."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import IntEnum

from daca.common import triplewise


class Opcode(IntEnum):
    """Enumeration of RAM instructions opcodes."""

    LOAD = 1
    STORE = 2
    ADD = 3
    SUB = 4
    MULT = 5
    DIV = 6
    READ = 7
    WRITE = 8
    JUMP = 9
    JGTZ = 10
    JZERO = 11
    HALT = 12


class OperandType(IntEnum):
    DIRECT = 0
    LITERAL = 1
    INDIRECT = 2


@dataclass(frozen=True)
class Operand:
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
    address: str | Operand = ""

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
                buf.append(0)
            elif inst.opcode in (Opcode.JGTZ, Opcode.JUMP, Opcode.JZERO):
                assert isinstance(inst.address, str)
                buf.append(0)
                buf.append(self.jumptable[inst.address] * 3)
            else:
                assert isinstance(inst.address, Operand)
                buf.append(inst.address.optype.value)
                buf.append(inst.address.value)
        return buf

    @classmethod
    def from_bytecode(
        cls, bytecode: Sequence[int], jumptable: Mapping[str, int] | None = None
    ) -> "Program":
        n: int = 1
        new_jumptable: dict[str, int] = dict(jumptable) if jumptable else {}
        jumplabels = {v * 3: k for k, v in new_jumptable.items()}

        instructions: list[Instruction] = []

        for i, t, a in triplewise(bytecode):
            opcode = Opcode(i)
            if opcode == Opcode.HALT:
                instructions.append(Instruction(opcode=opcode))
            elif opcode in (Opcode.JGTZ, Opcode.JUMP, Opcode.JZERO):
                if a not in jumplabels:
                    lbl = f"lbl{n}"
                    n += 1
                    jumplabels[a] = lbl
                    new_jumptable[lbl] = a // 3
                instructions.append(Instruction(opcode=opcode, address=jumplabels[a]))
            else:
                address = Operand(value=a, optype=OperandType(t))
                inst = Instruction(opcode=opcode, address=address)
                instructions.append(inst)

        return cls(instructions=instructions, jumptable=new_jumptable)
