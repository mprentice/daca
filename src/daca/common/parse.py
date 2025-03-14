import abc
from collections.abc import Iterable

from .lex import Token


class BaseParser[T](abc.ABC):
    @abc.abstractmethod
    def parse(self, token_stream: Iterable[Token]) -> T:
        ...
