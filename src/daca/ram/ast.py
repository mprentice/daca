"""Grammar/AST (abstract syntax tree) for RAM program.

Since a RAM program is simple, just the token tags for tokenization.
"""

from enum import StrEnum

from .program import Opcode


class Tag(StrEnum):
    """Token tags and corresponding regular expressions to match them."""

    whitespace = r"\s+"
    colon = r"\:"
    equals = r"\="
    star = r"\*"
    literal_integer = r"[-]?\d+"
    keyword = "(" + "|".join([o.value for o in Opcode]) + ")"
    literal_id = r"\w+"
    error = r"."
