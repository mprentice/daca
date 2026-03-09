from collections.abc import Sequence
from io import TextIOBase

from daca.common import Token

from .parser import parse
from .program import Program


def compile(program: str | TextIOBase | Sequence[Token] | Program) -> Sequence[int]:
    p: Program = program if isinstance(program, Program) else parse(program)
    return p.bytecode


def decompile(s: str | TextIOBase | Sequence[int]) -> Program:
    t: str | Sequence[int] = s.read() if isinstance(s, TextIOBase) else s
    bytecode: Sequence[int] = [int(i) for i in t.split()] if isinstance(t, str) else t

    return Program.from_bytecode(bytecode=bytecode)
