"""Grammar/AST (abstract syntax tree) for Pidgin Algol program."""

import abc
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Optional


class Keyword(StrEnum):
    """Pidgin Algol keywords."""

    begin = "begin"
    end = "end"
    read = "read"
    if_ = "if"
    then = "then"
    else_ = "else"
    while_ = "while"
    do = "do"
    write = "write"


class Tag(StrEnum):
    """Token tags and corresponding regular expressions to match them."""

    whitespace = r"\s+"
    keyword = "(" + "|".join([k.value for k in Keyword]) + ")"
    literal_integer = r"[-]?\d+"
    symbol = r"(\<=|>=|!=|\<-|[;=≠<≤>≥←+*/-])"
    literal_id = r"\w+"
    error = r"."


class BinaryOperator(StrEnum):
    """Operators that have a left-hand side (LHS) and right-hand side (RHS)."""

    equals = "="
    not_equals = "≠"
    lt = "<"
    le = "≤"
    gt = ">"
    ge = "≥"
    plus = "+"
    minus = "-"
    mult = "*"
    div = "/"


class Expression(abc.ABC):
    """Abstract base class (ABC) for pidgin algol expressions."""


class UnaryExpression(Expression):
    """Abstract base class (ABC) for pidgin algol unary expressions."""

    pass


@dataclass(frozen=True)
class LiteralExpression(UnaryExpression):
    """An integer literal."""

    value: int

    def __str__(self) -> str:
        return f"{self.value}"


@dataclass(frozen=True)
class VariableExpression(UnaryExpression):
    """A variable, e.g. x1"""

    name: str

    def __str__(self) -> str:
        return f"{self.name}"


@dataclass(frozen=True)
class BinaryExpression(Expression):
    """A binary expression, <left> <operator> <right>"""

    left: Expression
    operator: BinaryOperator
    right: Expression

    def __str__(self) -> str:
        return f"{self.left} {self.operator.value} {self.right}"


@dataclass(frozen=True)
class UnaryNegationExpression(UnaryExpression):
    """A unary negation expression, -<exp>"""

    exp: UnaryExpression

    def __str__(self) -> str:
        return f"-{self.exp}"


class Statement(abc.ABC):
    """Abstract base class (ABC) for a pidgin algol statement."""


@dataclass(frozen=True)
class BlockStatement(Statement):
    """A block statement.

    begin
      <statement 1>;
      <statement 2>;
      ...
      <statement n>
    end
    """

    statements: Sequence[Statement] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            "begin\n"
            + ";\n".join(
                [
                    "\n".join(["    " + line for line in str(b).split("\n")])
                    for b in self.statements
                ]
            )
            + "\nend"
        )


@dataclass(frozen=True)
class ReadStatement(Statement):
    """A read statement, read <variable>"""

    variable: VariableExpression

    def __str__(self):
        return f"read {self.variable}"


@dataclass(frozen=True)
class WriteStatement(Statement):
    """A read statement.

    write <value> where <value> is a variable or integer literal.
    """

    value: VariableExpression | LiteralExpression

    def __str__(self):
        return f"write {self.value}"


@dataclass(frozen=True)
class IfStatement(Statement):
    """An if statement, if <condition> then <true_body> [else <else_body>]"""

    condition: Expression
    true_body: Statement
    else_body: Optional[Statement] = None

    def __str__(self) -> str:
        if self.else_body:
            return "\n".join(
                [f"if {self.condition} then"]
                + ["    " + line for line in str(self.true_body).split("\n")]
                + ["else"]
                + ["    " + line for line in str(self.else_body).split("\n")]
            )
        return "\n".join(
            [f"if {self.condition} then"]
            + ["    " + line for line in str(self.true_body).split("\n")]
        )


@dataclass(frozen=True)
class WhileStatement(Statement):
    """A while statement, while <condition> do <body>"""

    condition: Expression
    body: Statement

    def __str__(self) -> str:
        return "\n".join(
            [f"while {self.condition} do"]
            + ["    " + line for line in str(self.body).split("\n")]
        )


@dataclass(frozen=True)
class AssignmentStatement(Statement):
    """An assignment statement, <variable> ← <expression>"""

    variable: VariableExpression
    expression: Expression

    def __str__(self) -> str:
        return f"{self.variable} ← {self.expression}"


@dataclass(frozen=True)
class AST:
    """An abstract syntax tree (AST) for a parsed Pidgin Algol program."""

    head: Statement

    def __str__(self) -> str:
        return str(self.head)
