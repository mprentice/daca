"""Parser for RAM program."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from io import StringIO
from typing import Generator, Iterable, Optional, TextIO

from daca.common import (
    BaseParser,
    BufferedTokenStream,
    ParseError,
    SimpleRegexLineLexer,
    Token,
)

from .program import Instruction, JumpTarget, Opcode, Operand, OperandFlag, Program


class Tag(StrEnum):
    whitespace = r"\s+"
    colon = r"\:"
    equals = r"\="
    star = r"\*"
    literal_integer = r"\d+"
    keyword = "(" + "|".join([o.value for o in Opcode]) + ")"
    literal_id = r"\w+"
    error = r"."


@dataclass
class Lexer(SimpleRegexLineLexer):
    spec: Sequence[tuple[str, str]] = tuple((t.name, t.value) for t in Tag)

    def filter_token(self, token: Token) -> Optional[Token]:
        if token.tag == Tag.whitespace.name:
            return None
        if token.tag == Tag.error.name:
            raise ParseError(line=self.line, column=self.column, value=token.value)
        return super().filter_token(token)


def tokenize(input_stream: str | StringIO | TextIO) -> Generator[Token, None, None]:
    yield from Lexer().tokenize(input_stream)


@dataclass
class Parser(BaseParser[Program]):
    lexer: Lexer = field(default_factory=Lexer)

    def parse(self, token_stream: str | StringIO | TextIO | Iterable[Token]) -> Program:
        if isinstance(token_stream, str) or hasattr(token_stream, "read"):
            b = BufferedTokenStream(self.lexer.tokenize(token_stream))  # type: ignore
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


def parse(s: str | StringIO | TextIO | Iterable[Token]) -> Program:
    return Parser().parse(s)
