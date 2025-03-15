import abc
from collections.abc import Iterable
from io import StringIO
from typing import TextIO

from .lex import Token


class BaseParser[T](abc.ABC):
    @abc.abstractmethod
    def parse(self, token_stream: str | StringIO | TextIO | Iterable[Token]) -> T: ...
