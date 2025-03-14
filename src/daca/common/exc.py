from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ParseError(Exception):
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
