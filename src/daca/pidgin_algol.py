"""Module for parsing and compiling pidgin ALGOL."""

import argparse
import re
from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Iterable, MutableSequence
from dataclasses import dataclass, field
from enum import StrEnum
from pprint import pprint
from textwrap import wrap
from typing import Generator, Optional, TextIO


class ParseError(Exception):
    pass


class TokenType(StrEnum):
    begin = "begin"
    end = "end"
    read = "read"
    if_ = "if"
    then = "then"
    else_ = "else"
    while_ = "while"
    do = "do"
    write = "write"
    semicolon = ";"
    equals = "="
    not_equals = "≠"
    lt = "<"
    le = "≤"
    gt = ">"
    ge = "≥"
    left_arrow = "←"
    plus = "+"
    minus = "-"
    mult = "*"
    div = "/"
    id_ = "<IDENTIFIER>"
    literal_int = "<INTEGER LITERAL>"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"


@dataclass
class Token:
    type_: TokenType
    val: str
    line: int
    col: int
    pos: int

    @property
    def span(self) -> range:
        return range(self.pos, self.pos + len(self.val))

    @property
    def column_span(self) -> range:
        return range(self.col, self.col + len(self.val))


class Lexer:
    def tokenize(self, input_stream: str | TextIO) -> Generator[Token, None, None]:
        s = input_stream if isinstance(input_stream, str) else input_stream.read()

        symbols = (
            TokenType.semicolon,
            TokenType.equals,
            TokenType.not_equals,
            TokenType.lt,
            TokenType.le,
            TokenType.gt,
            TokenType.ge,
            TokenType.left_arrow,
            TokenType.plus,
            TokenType.minus,
            TokenType.mult,
            TokenType.div,
        )
        symbol_values = tuple(k.value for k in symbols)
        keywords = (
            TokenType.begin,
            TokenType.end,
            TokenType.read,
            TokenType.if_,
            TokenType.then,
            TokenType.else_,
            TokenType.while_,
            TokenType.do,
            TokenType.write,
        )
        keyword_alt = "|".join([k.value for k in keywords])
        keyword_rex = re.compile(f"({keyword_alt})")
        int_rex = re.compile(r"\d+")
        id_rex = re.compile(r"[a-z][a-z0-9]*")

        pos = 0
        line = 0
        col = 0

        while pos < len(s):
            if s[pos : pos + 2] == "\r\n":
                pos += 2
                line += 1
                col = 0
                continue
            if s[pos : pos + 1] in ("\r", "\n"):
                pos += 1
                line += 1
                col = 0
                continue
            if s[pos].isspace():
                pos += 1
                col += 1
                continue

            if s[pos] in symbol_values:
                tok = s[pos]
                typ = TokenType(tok)
            elif m := keyword_rex.match(s, pos):
                tok = m.group(0)
                typ = TokenType(tok)
            elif m := int_rex.match(s, pos):
                tok = m.group(0)
                typ = TokenType.literal_int
            elif m := id_rex.match(s, pos):
                tok = m.group(0)
                typ = TokenType.id_
            else:
                raise ParseError(
                    f'Lexer encountered unexpected character "{s[pos]}" in input stream'
                )

            yield Token(typ, tok, line, col, pos)
            pos += len(tok)
            col += len(tok)


def tokenize(input_stream: str | TextIO) -> Generator[Token, None, None]:
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


class Expression(ABC):
    @abstractmethod
    def serialize(self) -> str:
        ...


class UnaryExpression(Expression):
    pass


@dataclass
class LiteralExpression(UnaryExpression):
    value: int

    def serialize(self) -> str:
        return f"{self.value}"


@dataclass
class VariableExpression(UnaryExpression):
    id_: str

    def serialize(self) -> str:
        return f"{self.id_}"


@dataclass
class BinaryExpression(Expression):
    left: Expression
    operator: BinaryOperator
    right: Expression

    def serialize(self) -> str:
        return f"{self.left.serialize()} {self.operator.value} {self.right.serialize()}"


class Statement(ABC):
    @abstractmethod
    def serialize(self) -> str:
        ...


class NullStatement(Statement):
    def serialize(self) -> str:
        return ";"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


@dataclass
class BlockStatement(Statement):
    statements: MutableSequence[Statement] = field(default_factory=list)

    def serialize(self) -> str:
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
        return (
            f"{self.variable.serialize()} "
            f"{TokenType.left_arrow.value} "
            f"{self.expression.serialize()}"
        )


@dataclass
class AST:
    head: BlockStatement

    def serialize(self) -> str:
        return self.head.serialize()


class Parser:
    """Recursive descent parser for pidgin ALGOL."""

    def __init__(self):
        self._it = None
        self._buffer = deque()

    def parse(self, token_stream: Iterable[Token]) -> AST:
        self._it = iter(token_stream)
        return AST(head=self.read_block())

    def read_block(self) -> BlockStatement:
        self.assert_token(self.next(), TokenType.begin)
        block = BlockStatement()
        while self.peek().type_ != TokenType.end:
            block.statements.append(self.read_statement())
        self.assert_token(self.next(), TokenType.end)
        return block

    def read_statement(self) -> Statement:
        top = self.peek()
        if top.type_ == TokenType.begin:
            return self.read_block()
        elif top.type_ == TokenType.read:
            return self.read_read()
        elif top.type_ == TokenType.if_:
            return self.read_if()
        elif top.type_ == TokenType.while_:
            return self.read_while()
        elif top.type_ == TokenType.write:
            return self.read_write()
        elif top.type_ == TokenType.id_:
            return self.read_assignment()
        elif top.type_ == TokenType.semicolon:
            self.next()
            return NullStatement()
        else:
            raise ParseError(f"Unexpected token: {top} trying to read next statement")

    def read_read(self) -> ReadStatement:
        self.assert_token(self.next(), TokenType.read)
        return ReadStatement(self.read_variable_expression())

    def read_if(self) -> IfStatement:
        self.assert_token(self.next(), TokenType.if_)
        condition = self.read_expression()
        self.assert_token(self.next(), TokenType.then)
        true_body = self.read_statement()
        top = self.peek()
        else_body = None
        if top.type_ == TokenType.else_:
            self.next()
            else_body = self.read_statement()
        return IfStatement(condition, true_body, else_body)

    def read_while(self) -> WhileStatement:
        self.assert_token(self.next(), TokenType.while_)
        condition = self.read_expression()
        self.assert_token(self.next(), TokenType.do)
        body = self.read_statement()
        return WhileStatement(condition, body)

    def read_write(self) -> WriteStatement:
        self.assert_token(self.next(), TokenType.write)
        return WriteStatement(self.read_unary_expression())

    def read_assignment(self) -> AssignmentStatement:
        tgt = self.next()
        self.assert_token(tgt, TokenType.id_)
        self.assert_token(self.next(), TokenType.left_arrow)
        exp = self.read_expression()
        return AssignmentStatement(VariableExpression(tgt.val), exp)

    def read_expression(self) -> Expression:
        top2 = self.peek2()
        if top2.val in {k.value for k in BinaryOperator}:
            return self.read_binary_expression()
        return self.read_unary_expression()

    def read_unary_expression(self) -> UnaryExpression:
        top = self.peek()
        if top.type_ == TokenType.id_:
            return self.read_variable_expression()
        elif top.type_ == TokenType.literal_int:
            return self.read_literal_expression()
        else:
            raise ParseError(
                f"Unexpected token: {top} "
                "(Expected: {TokenType.id_.value} or {TokenType.literal_int.value})"
            )

    def read_variable_expression(self) -> VariableExpression:
        tok = self.next()
        self.assert_token(tok, TokenType.id_)
        return VariableExpression(tok.val)

    def read_literal_expression(self) -> LiteralExpression:
        tok = self.next()
        self.assert_token(tok, TokenType.literal_int)
        return LiteralExpression(int(tok.val))

    def read_binary_expression(self) -> BinaryExpression:
        left = self.read_unary_expression()
        tok = self.next()
        try:
            operator = BinaryOperator(tok.val)
        except ValueError as ex:
            raise ParseError(
                f"Unexpected token: {tok} (Expected binary operator)"
            ) from ex
        right = self.read_expression()
        return BinaryExpression(left, operator, right)

    def next(self) -> Token:
        if self._buffer:
            return self._buffer.popleft()
        return next(self._it)

    def peek(self) -> Token:
        if not self._buffer:
            self._buffer.append(next(self._it))
        return self._buffer[0]

    def peek2(self) -> Token:
        while len(self._buffer) < 2:
            self._buffer.append(next(self._it))
        return self._buffer[1]

    def assert_token(self, token: Token, type_: TokenType) -> None:
        if token.type_ != type_:
            raise ParseError(f"Unexpected token: {token} (Expected: {type_.value})")


def parse(token_stream: Iterable[Token]) -> AST:
    return Parser().parse(token_stream)


class Interpreter:
    pass


class RamCompiler:
    pass


class App:
    """CLI application for working with pidgin ALGOL programs."""

    def __init__(self):
        self._argument_parser = None

    @property
    def argument_parser(self) -> argparse.ArgumentParser:
        """CLI argument parser for RAM application."""
        if self._argument_parser:
            return self._argument_parser

        self._argument_parser = argparse.ArgumentParser(
            description="Work with a pidgin ALGOL program"
        )
        self._argument_parser.add_argument(
            "--tokenize",
            "-t",
            action="store_true",
            default=False,
            help="Show tokenization of PROGRAM",
        )
        self._argument_parser.add_argument(
            "--parse",
            "-p",
            action="store_true",
            default=False,
            help="Show serialization of parsed PROGRAM",
        )
        self._argument_parser.add_argument(
            "--verbose",
            "-v",
            action="store_true",
            default=False,
            help="Show verbose output for debugging",
        )
        self._argument_parser.add_argument(
            "--compact",
            "-c",
            action="store_true",
            default=False,
            help="Show compact output in verbose mode (no pretty-print)",
        )
        self._argument_parser.add_argument(
            "program",
            type=argparse.FileType("r"),
            nargs=1,
            help="Pidgin ALGOL program file",
            metavar="PROGRAM",
        )
        self._argument_parser.add_argument(
            "input", type=int, nargs="*", help="Program input tape", metavar="CELL"
        )
        return self._argument_parser

    def run(self, argv: Optional[list[str]] = None):
        """CLI application main run method."""
        parser = self.argument_parser
        args = parser.parse_args() if argv is None else parser.parse_args(argv)

        # input_tape = tuple(args.input)

        program_text = args.program[0].read()

        if args.tokenize:
            toks = [t for t in tokenize(program_text)]
            if args.verbose:
                if args.compact:
                    print(f"{toks}")
                else:
                    pprint(toks)
            else:
                tok_vals = [t.val for t in toks]
                print("\n".join(wrap("«" + "» «".join(tok_vals) + "»", width=80)))

        if args.parse:
            ast = parse(tokenize(program_text))
            if args.verbose:
                if args.compact:
                    print(f"{ast}")
                else:
                    pprint(ast)
            else:
                print(ast.serialize())


if __name__ == "__main__":
    App().run()
