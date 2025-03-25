"""Parser for Pidgin Algol."""

from dataclasses import dataclass, field
from io import TextIOBase
from typing import Iterable, Optional

from daca.common import BaseParser, BufferedTokenStream, ParseError, Token

from .ast import (
    AST,
    AssignmentStatement,
    BinaryExpression,
    BinaryOperator,
    BlockStatement,
    Expression,
    IfStatement,
    Keyword,
    LiteralExpression,
    ReadStatement,
    Statement,
    Tag,
    UnaryExpression,
    UnaryNegationExpression,
    VariableExpression,
    WhileStatement,
    WriteStatement,
)
from .lexer import Lexer


@dataclass
class Parser(BaseParser[AST]):
    """Recursive descent parser for pidgin ALGOL."""

    lexer: Lexer = field(default_factory=Lexer)
    _token_stream: BufferedTokenStream = field(
        init=False, default_factory=lambda: BufferedTokenStream([])
    )

    def parse(self, token_stream: str | TextIOBase | Iterable[Token]) -> AST:
        if isinstance(token_stream, (str, TextIOBase)):
            b = BufferedTokenStream(self.lexer.tokenize(token_stream))
            self._token_stream = b
        else:
            self._token_stream = BufferedTokenStream(token_stream)
        return AST(head=self.read_statement())

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

    def read_block(self) -> BlockStatement:
        begin_token = self.next()
        self.assert_token(begin_token, Tag.keyword, Keyword.begin.value)
        stmts: list[Statement] = []
        while self.peek().value != Keyword.end.value:
            stmts.append(self.read_statement())
            try:
                self.assert_token(self.peek(), Tag.symbol, ";")
                self.next()
            except ParseError:
                self.assert_token(self.peek(), Tag.keyword, Keyword.end.value)
        self.assert_token(self.next(), Tag.keyword, Keyword.end.value)
        return BlockStatement(statements=stmts)

    def read_read(self) -> ReadStatement:
        read_token = self.next()
        self.assert_token(read_token, Tag.keyword, Keyword.read.value)
        return ReadStatement(variable=self.read_variable_expression())

    def read_if(self) -> IfStatement:
        if_token = self.next()
        self.assert_token(if_token, Tag.keyword, Keyword.if_.value)
        condition = self.read_expression()
        self.assert_token(self.next(), Tag.keyword, Keyword.then.value)
        true_body = self.read_statement()
        top = self.peek()
        else_body = None
        if top.value == Keyword.else_.value:
            self.next()
            else_body = self.read_statement()
        return IfStatement(
            condition=condition, true_body=true_body, else_body=else_body
        )

    def read_while(self) -> WhileStatement:
        while_token = self.next()
        self.assert_token(while_token, Tag.keyword, Keyword.while_.value)
        condition = self.read_expression()
        self.assert_token(self.next(), Tag.keyword, Keyword.do.value)
        body = self.read_statement()
        return WhileStatement(condition=condition, body=body)

    def read_write(self) -> WriteStatement:
        write_token = self.next()
        self.assert_token(write_token, Tag.keyword, Keyword.write.value)
        exp = self.read_unary_expression()
        if not (
            isinstance(exp, VariableExpression) or isinstance(exp, LiteralExpression)
        ):
            raise ParseError(
                f"Unexpected unary expression {exp} of type "
                f"{exp.__class__.__name__} (Expected: variable or literal)"
            )
        return WriteStatement(value=exp)

    def read_assignment(self) -> AssignmentStatement:
        tgt = self.next()
        self.assert_token(tgt, Tag.literal_id)
        self.assert_token(self.next(), Tag.symbol, ["←", "<-"])
        exp = self.read_expression()
        return AssignmentStatement(
            variable=VariableExpression(name=tgt.value),
            expression=exp,
        )

    def read_expression(self) -> Expression:
        self._token_stream.checkpoint()
        try:
            exp = self.read_binary_expression()
            self._token_stream.commit()
            return exp
        except (ParseError, StopIteration):
            self._token_stream.rollback()
        return self.read_unary_expression()

    def read_unary_expression(self) -> UnaryExpression:
        top = self.peek()
        if top.tag == Tag.literal_id.name:
            return self.read_variable_expression()
        elif top.tag == Tag.literal_integer.name:
            return self.read_literal_expression()
        elif top.tag == Tag.symbol.name and top.value == "-":
            return self.read_negation_expression()
        else:
            raise ParseError(
                f"Unexpected token: {top} "
                f"(Expected: {Tag.literal_id.value} or {Tag.literal_integer.value})"
            )

    def read_variable_expression(self) -> VariableExpression:
        tok = self.next()
        self.assert_token(tok, Tag.literal_id)
        return VariableExpression(name=tok.value)

    def read_literal_expression(self) -> LiteralExpression:
        tok = self.next()
        self.assert_token(tok, Tag.literal_integer)
        return LiteralExpression(value=int(tok.value))

    def read_negation_expression(self) -> UnaryNegationExpression:
        tok = self.next()
        self.assert_token(tok, Tag.symbol, "-")
        exp = self.read_unary_expression()
        return UnaryNegationExpression(exp=exp)

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
        return BinaryExpression(left=left, operator=operator, right=right)

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


def parse(token_stream: str | TextIOBase | Iterable[Token]) -> AST:
    return Parser().parse(token_stream)
