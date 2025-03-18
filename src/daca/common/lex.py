import abc
import re
from collections import deque
from collections.abc import Generator, Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from functools import cached_property
from io import StringIO, TextIOBase
from typing import Optional


@dataclass
class Token:
    tag: str
    value: str
    line: int
    column: int

    @property
    def span(self) -> range:
        return range(self.column, self.column + len(self.value))


class BaseLexer(abc.ABC):
    @abc.abstractmethod
    def tokenize(
        self, input_stream: str | TextIOBase
    ) -> Generator[Token, None, None]: ...


@dataclass
class LineLexer(BaseLexer):
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
    def tokenize_line(self, s: str) -> Generator[Token, None, None]: ...


@dataclass
class SimpleRegexLineLexer(LineLexer):
    spec: Sequence[tuple[str, str]] = field(kw_only=True)

    @cached_property
    def token_re(self) -> re.Pattern:
        return re.compile("|".join([f"(?P<{tag}>{rex})" for tag, rex in self.spec]))

    def tokenize_line(self, s: str) -> Generator[Token, None, None]:
        # See tokenizer at https://docs.python.org/3/library/re.html#writing-a-tokenizer
        for m in self.token_re.finditer(s):
            tag = m.lastgroup
            value = m.group()

            token = Token(
                tag=str(tag),
                value=value,
                line=self.line,
                column=self.column,
            )
            filtered_token = self.filter_token(token)
            if filtered_token:
                yield filtered_token

            self.column = m.start() + len(value)

    def filter_token(self, token: Token) -> Optional[Token]:
        return token


@dataclass
class BufferedTokenStream(Iterator[Token]):
    stream: Iterable[Token]
    index: int = 0
    buf: deque[Token] = field(default_factory=deque)
    checkpoints: list[int] = field(default_factory=list)
    _it: Iterator[Token] = field(init=False)

    def __post_init__(self):
        self._it = iter(self.stream)

    def __iter__(self) -> Iterator[Token]:
        return self

    def __next__(self) -> Token:
        return self.next()

    def next(self) -> Token:
        if self.checkpoints:
            if len(self.buf) < self.index + 1:
                self.buf.append(next(self._it))
            self.index += 1
            return self.buf[self.index - 1]

        if self.buf:
            return self.buf.popleft()

        return next(self._it)

    def __getitem__(self, index: int) -> Token:
        return self.peek(index + 1)

    def peek(self, n: int = 1) -> Token:
        if n < 1:
            raise IndexError(f"Peek error, {n} must be >= 1")
        # while len(self.buf) < self.index + n:
        #     self.buf.append(next(self._it))
        try:
            for _ in range(self.index + n - len(self.buf)):
                self.buf.append(next(self._it))
        except StopIteration as e:
            raise IndexError(f"Iterator exhausted, cannot peek {n} item(s)") from e
        return self.buf[self.index + n - 1]

    def checkpoint(self) -> None:
        self.checkpoints.append(self.index)

    def rollback(self) -> None:
        self.index = self.checkpoints.pop()

    def commit(self) -> None:
        self.checkpoints.pop()
        if not self.checkpoints:
            # while self.index > 0:
            #     self.index -= 1
            #     self.buf.popleft()
            for _ in range(self.index):
                self.buf.popleft()
            self.index = 0
