"""Parser for RASP program."""

from io import TextIOBase
from typing import Iterable

from daca.common import BaseParser, BufferedTokenStream, ParseError, Token

from .lexer import Tag, tokenize
from .program import Instruction, Opcode, Program


class Parser(BaseParser[Program]):
    """Parser for RASP programs."""

    def __init__(self):
        self.reset()

    def reset(self) -> None:
        self.token_stream = BufferedTokenStream([])
        self.jumptable: dict[str, int] = {}

    def parse(self, token_stream: Iterable[Token]) -> Program:
        """Parse a given token stream into a RASP Program."""
        self.reset()
        self.token_stream = BufferedTokenStream(token_stream)
        self._build_jumptable()

        instructions: list[Instruction] = []

        try:
            while True:
                tok = next(self.token_stream)
                if tok.tag == Tag.keyword.name and tok.value == Opcode.HALT.name:
                    instructions.append(Instruction(opcode=Opcode.HALT))
                elif self.token_stream.peek().tag == Tag.colon.name:
                    # jumptable already built, skip over jump target
                    next(self.token_stream)
                elif tok.tag == Tag.keyword.name:
                    instructions.append(self._parse_instruction(tok))
                else:
                    raise ParseError(line=tok.line, column=tok.column, value=tok)

        except StopIteration:
            pass

        return Program(instructions)

    def _build_jumptable(self) -> None:
        pc = 1
        self.token_stream.checkpoint()  # save at start of program

        for tok in self.token_stream:
            if (
                tok.tag == Tag.literal_id.name
                and self.token_stream.peek().tag == Tag.colon.name
            ):
                self.jumptable[tok.value] = pc
                pass
            elif tok.tag == Tag.keyword.name:
                pc += 2

        self.token_stream.rollback()  # reset to beginning of token stream

    def _parse_instruction(self, tok: Token) -> Instruction:
        if tok.value in (Opcode.JUMP.name, Opcode.JGTZ.name, Opcode.JZERO.name):
            b = self._parse_operand()
            return Instruction(opcode=Opcode[tok.value], address=b)

        if self.token_stream.peek().tag == Tag.equals.name:
            next(self.token_stream)
            opcode = Opcode[f"{tok.value}_LITERAL"]
        else:
            opcode = Opcode[tok.value]

        address = self._parse_operand()

        return Instruction(opcode=opcode, address=address)

    def _parse_operand(self) -> int:
        tok = next(self.token_stream)
        try:
            if tok.tag == Tag.literal_integer.name:
                return int(tok.value)
            elif (
                tok.tag == Tag.literal_id.name
                and self.token_stream.peek().tag == Tag.literal_integer.name
            ):
                lc = self.jumptable[tok.value]
                b = int(next(self.token_stream).value)
                return lc + b
            elif tok.tag == Tag.literal_id.name:
                return self.jumptable[tok.value]
        except KeyError as ex:
            raise ParseError(
                f"Unknown label {tok.value}",
                line=tok.line,
                column=tok.column,
                value=tok,
            ) from ex
        except ValueError as ex:
            raise ParseError(line=tok.line, column=tok.column, value=tok) from ex

        raise ParseError(line=tok.line, column=tok.column, value=tok)


def parse(s: str | TextIOBase | Iterable[Token]) -> Program:
    """Parse a given token stream, input stream, or str into a RASP Program."""
    token_stream: Iterable[Token] = (
        tokenize(s) if isinstance(s, str) or isinstance(s, TextIOBase) else s
    )
    return Parser().parse(token_stream)
