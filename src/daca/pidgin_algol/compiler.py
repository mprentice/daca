from dataclasses import dataclass, field
from io import StringIO
from typing import TextIO

from daca.ram import Program

from .parser import AST, Parser


@dataclass
class RamCompiler:
    parser: Parser = field(default_factory=Parser)

    def compile(self, p: str | StringIO | TextIO | AST) -> Program:
        ast = p if isinstance(p, AST) else self.parser.parse(p)
        print(ast.head)
        return Program([], {})


def compile_to_ram(program: str | StringIO | TextIO | AST) -> Program:
    return RamCompiler().compile(program)
