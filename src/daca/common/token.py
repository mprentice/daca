"""Module to provide Token and a BufferedTokenStream."""

from collections import deque
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field


@dataclass
class Token:
    """A generic token with a token tag, the token value, line & column."""

    tag: str
    value: str
    line: int
    column: int

    @property
    def span(self) -> range:
        """A range spanning the columns of the token's value."""
        return range(self.column, self.column + len(self.value))

    def __str__(self) -> str:
        return self.value


@dataclass
class BufferedTokenStream(Iterator[Token]):
    """A wrapper around a token stream that provides peeking and transactions.

    Useful for parsers to try a parse, rollback and try again on parse failure.
    """

    stream: Iterable[Token]
    _index: int = field(init=False, default=0)
    _buf: deque[Token] = field(init=False, default_factory=deque)
    _checkpoints: list[int] = field(init=False, default_factory=list)
    _it: Iterator[Token] = field(init=False)

    def __post_init__(self):
        self._it = iter(self.stream)

    def __iter__(self) -> Iterator[Token]:
        return self

    def __next__(self) -> Token:
        return self.next()

    def next(self) -> Token:
        """Return next token in stream."""
        if self._checkpoints:
            if len(self._buf) < self._index + 1:
                self._buf.append(next(self._it))
            self._index += 1
            return self._buf[self._index - 1]

        if self._buf:
            return self._buf.popleft()

        return next(self._it)

    def peek(self, n: int = 1) -> Token:
        """Peek ahead in the token stream by n tokens.

        n must be greater than 0 (default: 1).

        Raises IndexError if n < 0 or the underlying iterator has less than n
        items remaining.
        """
        if n < 1:
            raise IndexError(f"Peek error, {n} must be >= 1")
        # while len(self._buf) < self._index + n:
        #     self._buf.append(next(self._it))
        try:
            for _ in range(self._index + n - len(self._buf)):
                self._buf.append(next(self._it))
        except StopIteration as e:
            raise IndexError(f"Iterator exhausted, cannot peek {n} item(s)") from e
        return self._buf[self._index + n - 1]

    def checkpoint(self) -> None:
        """Begin a transaction and start buffering."""
        self._checkpoints.append(self._index)

    def rollback(self) -> None:
        """Rollback to most recent checkpoint (e.g. on parse failure)."""
        self._index = self._checkpoints.pop()

    def commit(self) -> None:
        """Commit most recent checkpoint (e.g. on parse success)."""
        self._checkpoints.pop()
        if not self._checkpoints:
            # while self._index > 0:
            #     self._index -= 1
            #     self._buf.popleft()
            for _ in range(self._index):
                self._buf.popleft()
            self._index = 0
