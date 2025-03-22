"""Module to provide BaseParser abstract base class."""

import abc
from collections.abc import Iterable
from io import TextIOBase

from .token import Token


class BaseParser[T](abc.ABC):
    """Abstract base class for parsers.

    A parser takes in some text or a stream of tokens and turns them into the
    result type of the parser, T.
    """

    @abc.abstractmethod
    def parse(self, token_stream: str | TextIOBase | Iterable[Token]) -> T:
        """Parse text or a stream of tokens and return the parse result."""
