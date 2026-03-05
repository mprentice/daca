"""Parser for RAM program."""

from io import TextIOBase
from typing import Iterable

from daca.common import BaseParser, BufferedTokenStream, ParseError, Token

from .lexer import Tag, tokenize
from .program import Instruction, Opcode, OperandFlag, Opname, Program


class Parser(BaseParser[Program]):
    """Parser for RAM programs."""

    def parse(self, token_stream: Iterable[Token]) -> Program:
        """Parse a given token stream into a RAM Program."""
        ts = BufferedTokenStream(token_stream)
        program_counter = 0
        jumptable: dict[str, int] = {}
        instructions = []

        try:
            while True:
                tok = next(ts)
                if tok.tag == Tag.keyword.name and tok.value == Opname.HALT.name:
                    instructions.append(Instruction(Opcode.HALT))
                    program_counter += 1
                elif ts.peek().tag == Tag.colon.name:
                    next(ts)
                    jumptable[tok.value] = program_counter
                elif tok.tag == Tag.keyword.name:
                    inst = self._parse_instruction(tok, ts)
                    instructions.append(inst)
                    program_counter += 1
                else:
                    raise ParseError(line=tok.line, column=tok.column, value=tok)

        except StopIteration:
            pass

        return Program(tuple(instructions), jumptable)

    def _parse_instruction(self, tok: Token, ts: BufferedTokenStream) -> Instruction:
        if tok.value in (Opname.JUMP.name, Opname.JGTZ.name, Opname.JZERO.name):
            b = next(ts).value
            return Instruction(Opcode[tok.value], b)

        if ts.peek().tag == Tag.star.name:
            next(ts)
            flag = OperandFlag.INDIRECT
        elif ts.peek().tag == Tag.equals.name:
            next(ts)
            flag = OperandFlag.LITERAL
        else:
            flag = OperandFlag.DIRECT

        if (
            tok.value in (Opname.STORE.name, Opname.READ.name)
            and flag == OperandFlag.LITERAL
        ):
            v = ts.peek()
            msg = f"{tok.value} instruction cannot accept literal value ={v.value}"
            raise ParseError(message=msg, line=v.line, column=v.column, value=v)

        a = int(next(ts).value)
        opcode = Opcode[f"{tok.value}_{flag.name}"]
        return Instruction(opcode, a)


def parse(s: str | TextIOBase | Iterable[Token]) -> Program:
    """Parse a given token stream, input stream, or str into a RAM Program."""
    return Parser().parse(
        tokenize(s) if isinstance(s, str) or isinstance(s, TextIOBase) else s
    )
