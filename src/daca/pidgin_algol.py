"""Module for parsing and compiling pidgin ALGOL."""

import re
from collections.abc import MutableSequence
from dataclasses import dataclass
from enum import StrEnum
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
    literal_int = "<LITERAL INTEGER>"


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


class BinaryOperator(StrEnum):
    equals = "="
    lt = "<"
    le = "≤"
    gt = ">"
    ge = "≥"
    plus = "+"
    minus = "-"
    mult = "*"
    div = "/"


class Expression:
    pass


class UnaryExpression(Expression):
    pass


@dataclass
class LiteralExpression(UnaryExpression):
    value: int


@dataclass
class RegisterExpression(UnaryExpression):
    register: int


@dataclass
class BinaryExpression(Expression):
    left: Expression
    operator: BinaryOperator
    right: Expression


class Statement:
    pass


@dataclass
class BlockStatement(Statement):
    statements: MutableSequence[Statement]


@dataclass
class ReadStatement(Statement):
    register: RegisterExpression


@dataclass
class WriteStatement(Statement):
    register: RegisterExpression


@dataclass
class IfStatement(Statement):
    condition: Expression
    true_body: Statement
    else_body: Optional[Statement] = None


@dataclass
class WhileStatement(Statement):
    condition: Expression
    body: Statement


@dataclass
class AssignmentStatement(Statement):
    target_register: int
    expression: Expression


@dataclass
class AST:
    head: BlockStatement


class Parser:
    pass


class Interpreter:
    pass


class RamCompiler:
    pass
