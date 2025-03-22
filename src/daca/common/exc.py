"""Module for common exceptions for daca package."""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class BaseDacaError(Exception):
    """Base class for DACA errors, such as ParseError and CompileError."""

    message: str = ""
    line: Optional[int] = None
    column: Optional[int] = None
    value: Any = None

    def __post_init__(self):
        if self.message and self.line is not None and self.column is not None:
            self.message = f"{self.message} at L{self.line}:C{self.column}"
        elif self.message and self.line is not None:
            self.message = f"{self.message} at L{self.line}"
        elif self.message:
            pass
        elif self.line is not None and self.column is not None:
            self.message = f"Unexpected {self.value} at L{self.line}:C{self.column}"
        elif self.line is not None:
            self.message = f"Unexpected {self.value} at L{self.line}"
        else:
            self.message = f"Unexpected {self.value}"
        super().__init__(self.message)


class ParseError(BaseDacaError):
    """Error to indicate a problem with parsing a program."""


class CompileError(BaseDacaError):
    """Error to indicate a problem with compiling a program."""
