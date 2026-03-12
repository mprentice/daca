"""Tokenizer for RAM program."""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from io import StringIO, TextIOBase
from typing import Generator

from daca.common import ParseError, SimpleRegexLineLexer, Token

from .program import Opcode


class Tag(StrEnum):
    """Token tags and corresponding regular expressions to match them."""

    comment = r"#.*$"
    whitespace = r"\s+"
    colon = r"\:"
    equals = r"\="
    star = r"\*"
    literal_integer = r"[-]?\d+"
    keyword = "(" + "|".join([o.name for o in Opcode]) + ")"
    literal_id = r"\w+"
    error = r"."


@dataclass
class Lexer(SimpleRegexLineLexer):
    """Lexer for RAM programs."""

    spec: Sequence[tuple[str, str]] = tuple((t.name, t.value) for t in Tag)

    def tokenize_line(self, s: str) -> Generator[Token, None, None]:
        for token in super().tokenize_line(s):
            if token.tag == Tag.whitespace.name or token.tag == Tag.comment.name:
                # skip whitespace and comment tokens
                continue
            elif token.tag == Tag.error.name:
                raise ParseError(line=self.line, column=self.column, value=token.value)
            yield token


def tokenize(input_stream: str | TextIOBase) -> Generator[Token, None, None]:
    """Create a token stream from an input stream or str."""
    yield from Lexer().tokenize(
        StringIO(input_stream) if isinstance(input_stream, str) else input_stream
    )
