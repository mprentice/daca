from daca.pidgin_algol.ast import (
    AssignmentStatement,
    BinaryOperator,
    BlockStatement,
    IfStatement,
    ReadStatement,
    WhileStatement,
    WriteStatement,
)
from daca.pidgin_algol.parser import parse


def test_read_block():
    s: BlockStatement = parse("begin write 1; write 2 end").head
    assert isinstance(s, BlockStatement)


def test_read_read():
    s: ReadStatement = parse("read x1").head
    assert isinstance(s, ReadStatement)
    assert s.variable.name == "x1"


def test_read_if():
    s: IfStatement = parse("if x1 != x2 then x3 <- 4 else c3 <- 19").head
    assert isinstance(s, IfStatement)
    assert s.condition.left.name == "x1"
    assert s.condition.operator == BinaryOperator.not_equals
    assert s.condition.right.name == "x2"


def test_read_while():
    s: WhileStatement = parse("while x1 do x1 <- x1 - 1").head
    assert isinstance(s, WhileStatement)
    assert s.condition.name == "x1"


def test_read_write():
    s: WriteStatement = parse("write x1").head
    assert isinstance(s, WriteStatement)
    assert s.value.name == "x1"
    s = parse("write 1").head
    assert s.value.value == 1


def test_read_assignment():
    s: AssignmentStatement = parse("x1 <- 5").head
    assert isinstance(s, AssignmentStatement)
    assert s.variable.name == "x1"
    assert s.expression.value == 5
