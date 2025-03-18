import abc
from collections.abc import Iterable
from io import TextIOBase

from .lex import Token


class BaseParser[T](abc.ABC):
    @abc.abstractmethod
    def parse(self, token_stream: str | TextIOBase | Iterable[Token]) -> T: ...
