from collections.abc import Mapping, Sequence
from io import TextIOBase
from typing import Optional

from daca.common import Token, pairwise

from .parser import parse
from .program import Instruction, Opcode, Program


class Compiler:
    def compile(self, p: Program) -> Sequence[int]:
        return p.bytecode


class Decompiler:
    def decompile(
        self, s: Sequence[int], jumptable: Optional[Mapping[str, int]] = None
    ) -> Program:
        n = 1
        jt: dict[str, int] = dict(jumptable) if jumptable else {}
        jumplabels = {v * 2: k for k, v in jt.items()}
        p = []
        for i, a in pairwise(s):
            opcode = Opcode(i)
            if opcode == Opcode.HALT:
                p.append(Instruction(opcode))
            elif opcode in (Opcode.JGTZ, Opcode.JUMP, Opcode.JZERO):
                if a not in jumplabels:
                    lbl = f"lbl{n}"
                    n += 1
                    jumplabels[a] = lbl
                    jt[lbl] = a // 2
                p.append(Instruction(opcode, jumplabels[a]))
            else:
                p.append(Instruction(opcode, a))
        return Program(p, jt)


def compile(program: str | TextIOBase | Sequence[Token] | Program) -> Sequence[int]:
    p = program if isinstance(program, Program) else parse(program)
    return Compiler().compile(p)


def decompile(
    s: str | TextIOBase | Sequence[int], jumptable: Optional[Mapping[str, int]] = None
) -> Program:
    t = s.read() if isinstance(s, TextIOBase) else s
    u = [int(i) for i in t.split()] if isinstance(t, str) else t
    return Decompiler().decompile(u, jumptable)
