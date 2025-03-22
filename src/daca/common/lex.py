"""Module to provide abstract base classes (ABC) & utilities for tokenizing."""

import abc
import re
from collections.abc import Generator, Sequence
from dataclasses import dataclass, field
from io import StringIO, TextIOBase

from .token import Token


class BaseLexer(abc.ABC):
    """Abstract base class for tokenizers (lexers)."""

    @abc.abstractmethod
    def tokenize(self, input_stream: str | TextIOBase) -> Generator[Token, None, None]:
        """Generate tokens from a str of TextIO-type input stream."""


@dataclass
class LineLexer(BaseLexer):
    """Abstract base class for a line-based lexer, tokenizing line by line."""

    line: int = 0
    column: int = 0

    def tokenize(self, input_stream: str | TextIOBase) -> Generator[Token, None, None]:
        inp = StringIO(input_stream) if isinstance(input_stream, str) else input_stream
        self.line = -1
        self.column = 0
        while s := inp.readline():
            self.line += 1
            self.column = 0

            yield from self.tokenize_line(s)

    @abc.abstractmethod
    def tokenize_line(self, s: str) -> Generator[Token, None, None]:
        """Generate tokens from a line of text."""


@dataclass
class SimpleRegexLineLexer(LineLexer):
    r"""A simple line-based lexer that uses a regex spec to tokenize.

    The spec is compiled to a regular expression, so the keys in the spec must
    be valid regex group names and the values must be valid regular
    expressions.

    Example:

        >>> lexer = SimpleRegexLineLexer(spec=[('int', r'\d+'), ('any', r'.')])
        >>> [(t.tag, t.value) for t in lexer.tokenize('123!')]
        [('int', '123'), ('any', '!')]
    """

    spec: Sequence[tuple[str, str]] = field(kw_only=True)
    token_re: re.Pattern = field(init=False)

    def __post_init__(self):
        self.token_re = re.compile(
            "|".join([f"(?P<{tag}>{rex})" for tag, rex in self.spec])
        )

    def tokenize_line(self, s: str) -> Generator[Token, None, None]:
        # See tokenizer at https://docs.python.org/3/library/re.html#writing-a-tokenizer
        for m in self.token_re.finditer(s):
            tag = m.lastgroup
            value = m.group()

            yield Token(
                tag=str(tag),
                value=value,
                line=self.line,
                column=self.column,
            )

            self.column = m.start() + len(value)
