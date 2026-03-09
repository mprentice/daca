"""Parser for RASP program."""

from io import TextIOBase
from typing import Iterable

from daca.common import BaseParser, BufferedTokenStream, ParseError, Token

from .lexer import Tag, tokenize
from .program import Instruction, Opcode, Program


class Parser(BaseParser[Program]):
    """Parser for RAM programs."""

    def parse(self, token_stream: Iterable[Token]) -> Program:
        """Parse a given token stream into a RAM Program."""
        return _parse(token_stream)


def parse(s: str | TextIOBase | Iterable[Token]) -> Program:
    """Parse a given token stream, input stream, or str into a RAM Program."""
    token_stream: Iterable[Token] = (
        tokenize(s) if isinstance(s, str) or isinstance(s, TextIOBase) else s
    )
    return _parse(token_stream)


def _parse(token_stream: Iterable[Token]) -> Program:
    ts = BufferedTokenStream(token_stream)
    program_counter = 0
    instructions: list[Instruction] = []

    try:
        while True:
            tok = next(ts)
            if tok.tag == Tag.keyword.name and tok.value == Opcode.HALT.name:
                instructions.append(Instruction(opcode=Opcode.HALT))
                program_counter += 1
            elif tok.tag == Tag.keyword.name:
                inst = _parse_instruction(tok, ts)
                instructions.append(inst)
                program_counter += 1
            else:
                raise ParseError(line=tok.line, column=tok.column, value=tok)

    except StopIteration:
        pass

    return Program(instructions)


def _parse_instruction(tok: Token, ts: BufferedTokenStream) -> Instruction:
    if tok.value in (Opcode.JUMP.name, Opcode.JGTZ.name, Opcode.JZERO.name):
        b = int(next(ts).value)
        return Instruction(opcode=Opcode[tok.value], address=b)

    if ts.peek().tag == Tag.equals.name:
        next(ts)
        opcode = Opcode[f"{tok.value}_LITERAL"]
    else:
        opcode = Opcode[tok.value]

    address = int(next(ts).value)

    return Instruction(opcode=opcode, address=address)
