"""Module to provide BaseParser abstract base class."""

import abc
from collections.abc import Iterable

from .token import Token


class BaseParser[T](abc.ABC):
    """Abstract base class for parsers.

    A parser takes in a stream of tokens and turns them into the result type of
    the parser, T.
    """

    @abc.abstractmethod
    def parse(self, token_stream: Iterable[Token]) -> T:
        """Parse a stream of tokens and return the parse result."""
