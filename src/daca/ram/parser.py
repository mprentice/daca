"""Parser for RAM program."""

from dataclasses import dataclass, field
from io import TextIOBase
from typing import Iterable

from daca.common import BaseParser, BufferedTokenStream, ParseError, Token

from .ast import Tag
from .lexer import Lexer
from .program import Instruction, JumpTarget, Opcode, Operand, OperandFlag, Program


@dataclass
class Parser(BaseParser[Program]):
    """Parser for RAM programs."""

    lexer: Lexer = field(default_factory=Lexer)

    def parse(self, token_stream: str | TextIOBase | Iterable[Token]) -> Program:
        """Parse a given token stream into a RAM Program."""
        if isinstance(token_stream, (str, TextIOBase)):
            b = BufferedTokenStream(self.lexer.tokenize(token_stream))
        else:
            b = BufferedTokenStream(token_stream)
        return self._parse_token_stream(b)

    def _parse_token_stream(self, ts: BufferedTokenStream) -> Program:
        program_counter = 0
        jumptable: dict[JumpTarget, int] = {}
        instructions = []

        try:
            while True:
                tok = next(ts)
                if tok.tag == Tag.keyword.name and tok.value == Opcode.HALT.name:
                    instructions.append(Instruction(Opcode.HALT))
                    program_counter += 1
                elif ts.peek().tag == Tag.colon.name:
                    next(ts)
                    jumptable[JumpTarget(tok.value)] = program_counter
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
        if tok.value in (
            Opcode.JUMP.name,
            Opcode.JGTZ.name,
            Opcode.JZERO.name,
        ):
            b = next(ts).value
            return Instruction(Opcode(tok.value), JumpTarget(value=b))
        elif tok.value in (
            Opcode.STORE.name,
            Opcode.READ.name,
        ):
            if ts.peek().tag == Tag.star.name:
                next(ts)
                i = int(next(ts).value)
                return Instruction(
                    Opcode(tok.value),
                    Operand(value=i, flag=OperandFlag.indirect),
                )
            elif ts.peek().tag == Tag.equals.name:
                raise ParseError(
                    message=(
                        f"{tok.value} instruction cannot accept "
                        f"literal value ={ts.peek(2).value}"
                    ),
                    line=ts.peek().line,
                    column=ts.peek().column,
                    value=ts.peek(),
                )
            else:
                i = int(next(ts).value)
                return Instruction(
                    Opcode(tok.value),
                    Operand(value=i, flag=OperandFlag.direct),
                )
        elif tok.value in (
            Opcode.LOAD.name,
            Opcode.ADD.name,
            Opcode.SUB.name,
            Opcode.MULT.name,
            Opcode.DIV.name,
            Opcode.WRITE.name,
        ):
            if ts.peek().tag == Tag.star.name:
                next(ts)
                a = int(next(ts).value)
                return Instruction(
                    Opcode(tok.value),
                    Operand(value=a, flag=OperandFlag.indirect),
                )
            elif ts.peek().tag == Tag.equals.name:
                next(ts)
                a = int(next(ts).value)
                return Instruction(
                    Opcode(tok.value),
                    Operand(value=a, flag=OperandFlag.literal),
                )
            else:
                a = int(next(ts).value)
                return Instruction(
                    Opcode(tok.value),
                    Operand(value=a, flag=OperandFlag.direct),
                )
        raise ParseError(line=tok.line, column=tok.column, value=tok)


def parse(s: str | TextIOBase | Iterable[Token]) -> Program:
    """Parse a given token stream, input stream, or str into a RAM Program."""
    return Parser().parse(s)
