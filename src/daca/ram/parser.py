"""Parser for RAM program."""

from io import TextIOBase
from typing import Iterable

from daca.common import BaseParser, BufferedTokenStream, ParseError, Token

from .lexer import Tag, tokenize
from .program import Instruction, Opcode, Operand, OperandType, Program


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
    jumptable: dict[str, int] = {}
    instructions = []

    try:
        while True:
            tok = next(ts)
            if tok.tag == Tag.keyword.name and tok.value == Opcode.HALT.name:
                instructions.append(Instruction(opcode=Opcode.HALT))
                program_counter += 1
            elif ts.peek().tag == Tag.colon.name:
                next(ts)
                jumptable[tok.value] = program_counter
            elif tok.tag == Tag.keyword.name:
                inst = _parse_instruction(tok, ts)
                instructions.append(inst)
                program_counter += 1
            else:
                raise ParseError(line=tok.line, column=tok.column, value=tok)

    except StopIteration:
        pass

    return Program(tuple(instructions), jumptable)


def _parse_instruction(tok: Token, ts: BufferedTokenStream) -> Instruction:
    if tok.value in (Opcode.JUMP.name, Opcode.JGTZ.name, Opcode.JZERO.name):
        b = next(ts).value
        return Instruction(opcode=Opcode[tok.value], address=b)

    if ts.peek().tag == Tag.star.name:
        next(ts)
        optype = OperandType.INDIRECT
    elif ts.peek().tag == Tag.equals.name:
        next(ts)
        optype = OperandType.LITERAL
    else:
        optype = OperandType.DIRECT

    if (
        tok.value in (Opcode.STORE.name, Opcode.READ.name)
        and optype == OperandType.LITERAL
    ):
        v = ts.peek()
        msg = f"{tok.value} instruction cannot accept literal value ={v.value}"
        raise ParseError(message=msg, line=v.line, column=v.column, value=v)

    opcode = Opcode[tok.value]
    v = int(next(ts).value)
    address = Operand(value=v, optype=optype)

    return Instruction(opcode=opcode, address=address)
