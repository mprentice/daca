"""Tokenizer for RAM program."""

from collections.abc import Sequence
from dataclasses import dataclass
from io import TextIOBase
from typing import Generator

from daca.common import ParseError, SimpleRegexLineLexer, Token

from .ast import Tag


@dataclass
class Lexer(SimpleRegexLineLexer):
    """Lexer for RAM programs."""

    spec: Sequence[tuple[str, str]] = tuple((t.name, t.value) for t in Tag)

    def tokenize_line(self, s: str) -> Generator[Token, None, None]:
        for token in super().tokenize_line(s):
            if token.tag == Tag.whitespace.name:
                continue
            if token.tag == Tag.error.name:
                raise ParseError(line=self.line, column=self.column, value=token.value)
            yield token


def tokenize(input_stream: str | TextIOBase) -> Generator[Token, None, None]:
    """Create a token stream from an input stream or str."""
    yield from Lexer().tokenize(input_stream)
