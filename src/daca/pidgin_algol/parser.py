"""Parser for Pidgin Algol."""

import abc
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from io import StringIO
from typing import Generator, Iterable, MutableSequence, Optional, TextIO

from daca.common import (
    BaseParser,
    BufferedTokenStream,
    ParseError,
    SimpleRegexLineLexer,
    Token,
)


class Keyword(StrEnum):
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
    whitespace = r"\s+"
    keyword = "(" + "|".join([k.value for k in Keyword]) + ")"
    symbol = r"(\<=|>=|!=|\<-|[;=≠<≤>≥←+*/-])"
    literal_integer = r"\d+"
    literal_id = r"\w+"
    error = r"."


@dataclass
class Lexer(SimpleRegexLineLexer):
    spec: Sequence[tuple[str, str]] = tuple((t.name, t.value) for t in Tag)

    def filter_token(self, token: Token) -> Optional[Token]:
        if token.tag == Tag.whitespace.name:
            return None
        if token.tag == Tag.error.name:
            raise ParseError(line=self.line, column=self.column, value=token.value)
        return super().filter_token(token)


def tokenize(input_stream: str | StringIO | TextIO) -> Generator[Token, None, None]:
    yield from Lexer().tokenize(input_stream)


class BinaryOperator(StrEnum):
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
    @abc.abstractmethod
    def serialize(self) -> str: ...


class UnaryExpression(Expression):
    pass


@dataclass
class LiteralExpression(UnaryExpression):
    value: int

    def serialize(self) -> str:
        return f"{self.value}"


@dataclass
class VariableExpression(UnaryExpression):
    name: str

    def serialize(self) -> str:
        return f"{self.name}"


@dataclass
class BinaryExpression(Expression):
    left: Expression
    operator: BinaryOperator
    right: Expression

    def serialize(self) -> str:
        return f"{self.left.serialize()} {self.operator.value} {self.right.serialize()}"


class Statement(abc.ABC):
    @abc.abstractmethod
    def serialize(self) -> str: ...


@dataclass
class BlockStatement(Statement):
    statements: MutableSequence[Statement] = field(default_factory=list)

    def serialize(self) -> str:
        return (
            "begin\n"
            + ";\n".join(
                [
                    "\n".join(["    " + line for line in b.serialize().split("\n")])
                    for b in self.statements
                ]
            )
            + "\nend"
        )
        s = "\n".join(
            ["begin"]
            + [
                "    " + line
                for b in self.statements
                for line in b.serialize().split("\n")
            ]
            + ["end"]
        )
        return re.sub(r"\s+;", ";", s, flags=re.MULTILINE)


@dataclass
class ReadStatement(Statement):
    variable: VariableExpression

    def serialize(self):
        return f"read {self.variable.serialize()}"


@dataclass
class WriteStatement(Statement):
    value: VariableExpression | LiteralExpression

    def serialize(self):
        return f"write {self.value.serialize()}"


@dataclass
class IfStatement(Statement):
    condition: Expression
    true_body: Statement
    else_body: Optional[Statement] = None

    def serialize(self) -> str:
        if self.else_body:
            return "\n".join(
                [f"if {self.condition.serialize()} then"]
                + ["    " + line for line in self.true_body.serialize().split("\n")]
                + ["else"]
                + ["    " + line for line in self.else_body.serialize().split("\n")]
            )
        return "\n".join(
            [f"if {self.condition.serialize()} then"]
            + ["    " + line for line in self.true_body.serialize().split("\n")]
        )


@dataclass
class WhileStatement(Statement):
    condition: Expression
    body: Statement

    def serialize(self) -> str:
        return "\n".join(
            [f"while {self.condition.serialize()} do"]
            + ["    " + line for line in self.body.serialize().split("\n")]
        )


@dataclass
class AssignmentStatement(Statement):
    variable: VariableExpression
    expression: Expression

    def serialize(self) -> str:
        return f"{self.variable.serialize()} ← {self.expression.serialize()}"


@dataclass
class AST:
    head: BlockStatement

    def serialize(self) -> str:
        return self.head.serialize()


@dataclass
class Parser(BaseParser[AST]):
    """Recursive descent parser for pidgin ALGOL."""

    lexer: Lexer = field(default_factory=Lexer)
    _token_stream: BufferedTokenStream = field(
        init=False, default_factory=lambda: BufferedTokenStream([])
    )

    def parse(self, token_stream: str | StringIO | TextIO | Iterable[Token]) -> AST:
        if isinstance(token_stream, str) or hasattr(token_stream, "read"):
            b = BufferedTokenStream(self.lexer.tokenize(token_stream))  # type: ignore
            self._token_stream = b
        else:
            self._token_stream = BufferedTokenStream(token_stream)
        return AST(head=self.read_block())

    def read_block(self) -> BlockStatement:
        self.assert_token(self.next(), Tag.keyword, Keyword.begin.value)
        block = BlockStatement()
        while self.peek().value != Keyword.end.value:
            block.statements.append(self.read_statement())
            try:
                self.assert_token(self.peek(), Tag.symbol, ";")
                self.next()
            except ParseError:
                self.assert_token(self.peek(), Tag.keyword, Keyword.end.value)
        self.assert_token(self.next(), Tag.keyword, Keyword.end.value)
        return block

    def read_statement(self) -> Statement:
        top = self.peek()
        if top.value == Keyword.begin.value:
            return self.read_block()
        elif top.value == Keyword.read.value:
            return self.read_read()
        elif top.value == Keyword.if_.value:
            return self.read_if()
        elif top.value == Keyword.while_.value:
            return self.read_while()
        elif top.value == Keyword.write.value:
            return self.read_write()
        elif top.tag == Tag.literal_id.name:
            return self.read_assignment()
        else:
            raise ParseError(line=top.line, column=top.column, value=top)

    def read_read(self) -> ReadStatement:
        self.assert_token(self.next(), Tag.keyword, Keyword.read.value)
        return ReadStatement(self.read_variable_expression())

    def read_if(self) -> IfStatement:
        self.assert_token(self.next(), Tag.keyword, Keyword.if_.value)
        condition = self.read_expression()
        self.assert_token(self.next(), Tag.keyword, Keyword.then.value)
        true_body = self.read_statement()
        top = self.peek()
        else_body = None
        if top.value == Keyword.else_.value:
            self.next()
            else_body = self.read_statement()
        return IfStatement(condition, true_body, else_body)

    def read_while(self) -> WhileStatement:
        self.assert_token(self.next(), Tag.keyword, Keyword.while_.value)
        condition = self.read_expression()
        self.assert_token(self.next(), Tag.keyword, Keyword.do.value)
        body = self.read_statement()
        return WhileStatement(condition, body)

    def read_write(self) -> WriteStatement:
        self.assert_token(self.next(), Tag.keyword, Keyword.write.value)
        exp = self.read_unary_expression()
        if not (
            isinstance(exp, VariableExpression) or isinstance(exp, LiteralExpression)
        ):
            raise ParseError(
                f"Unexpected unary expression {exp} of type "
                f"{exp.__class__.__name__} (Expected: variable or literal)"
            )
        return WriteStatement(exp)

    def read_assignment(self) -> AssignmentStatement:
        tgt = self.next()
        self.assert_token(tgt, Tag.literal_id)
        self.assert_token(self.next(), Tag.symbol, ["←", "<-"])
        exp = self.read_expression()
        return AssignmentStatement(VariableExpression(tgt.value), exp)

    def read_expression(self) -> Expression:
        self._token_stream.checkpoint()
        try:
            exp = self.read_binary_expression()
            self._token_stream.commit()
            return exp
        except ParseError:
            self._token_stream.rollback()
        return self.read_unary_expression()

    def read_unary_expression(self) -> UnaryExpression:
        top = self.peek()
        if top.tag == Tag.literal_id.name:
            return self.read_variable_expression()
        elif top.tag == Tag.literal_integer.name:
            return self.read_literal_expression()
        else:
            raise ParseError(
                f"Unexpected token: {top} "
                f"(Expected: {Tag.literal_id.value} or {Tag.literal_integer.value})"
            )

    def read_variable_expression(self) -> VariableExpression:
        tok = self.next()
        self.assert_token(tok, Tag.literal_id)
        return VariableExpression(tok.value)

    def read_literal_expression(self) -> LiteralExpression:
        tok = self.next()
        self.assert_token(tok, Tag.literal_integer)
        return LiteralExpression(int(tok.value))

    def read_binary_expression(self) -> BinaryExpression:
        left = self.read_unary_expression()
        tok = self.next()
        try:
            v = tok.value
            if v == "<=":
                operator = BinaryOperator.le
            elif v == ">=":
                operator = BinaryOperator.ge
            elif v == "!=":
                operator = BinaryOperator.not_equals
            else:
                operator = BinaryOperator(tok.value)
        except ValueError as ex:
            raise ParseError(
                f"Unexpected token: {tok} (Expected binary operator)"
            ) from ex
        right = self.read_expression()
        return BinaryExpression(left, operator, right)

    def next(self) -> Token:
        return next(self._token_stream)

    def peek(self) -> Token:
        return self._token_stream.peek()

    def peek2(self) -> Token:
        return self._token_stream.peek(2)

    def assert_token(
        self, token: Token, tag: Tag, value: Optional[str | list[str]] = None
    ) -> None:
        if token.tag != tag.name or not (
            value is None
            or token.value == value
            or (not isinstance(value, str) and token.value in value)
        ):
            raise ParseError(
                f"Unexpected token: {token} (Expected: {tag.name} ({value}))",
                line=token.line,
                column=token.column,
                value=token,
            )


def parse(token_stream: str | StringIO | TextIO | Iterable[Token]) -> AST:
    return Parser().parse(token_stream)
