import pytest

from daca.common import ParseError
from daca.ram import Instruction, Opcode, parse


def test_program_parse(n_pow_n: str):
    p = parse(n_pow_n)
    assert p is not None


def test_program_serialize(n_pow_n: str):
    p = parse(n_pow_n)
    assert p == parse(str(p))


def test_parse_label_and_halt():
    p = parse("stopit: HALT")
    assert p.jumptable["stopit"] == 0
    assert p.instructions[0].opcode == Opcode.HALT


@pytest.mark.parametrize(
    "opcode",
    [
        Opcode.STORE,
        Opcode.READ,
        Opcode.LOAD,
        Opcode.ADD,
        Opcode.SUB,
        Opcode.MULT,
        Opcode.DIV,
        Opcode.WRITE,
    ],
)
def test_parse_direct(opcode: Opcode):
    inst = parse(f"{opcode.name} 1").instructions[0]
    assert inst.opcode == opcode
    assert inst.address.value == 1


@pytest.mark.parametrize(
    "opcode",
    [
        Opcode.STORE,
        Opcode.READ,
        Opcode.LOAD,
        Opcode.ADD,
        Opcode.SUB,
        Opcode.MULT,
        Opcode.DIV,
        Opcode.WRITE,
    ],
)
def test_parse_indirect(opcode: Opcode):
    inst: Instruction = parse(f"{opcode.name} *1").instructions[0]
    assert inst.opcode == opcode
    assert inst.address.value == 1


@pytest.mark.parametrize(
    "opcode",
    [Opcode.LOAD, Opcode.ADD, Opcode.SUB, Opcode.MULT, Opcode.DIV, Opcode.WRITE],
)
def test_parse_literal(opcode: Opcode):
    inst: Instruction = parse(f"{opcode.name} =1").instructions[0]
    assert inst.opcode == opcode
    assert inst.address.value == 1


def test_parse_literal_error():
    with pytest.raises(ParseError):
        parse("STORE =1")
    with pytest.raises(ParseError):
        parse("READ =1")


@pytest.mark.parametrize("opcode", [Opcode.JUMP, Opcode.JGTZ, Opcode.JZERO])
def test_parse_jump(opcode: Opcode):
    inst: Instruction = parse(f"{opcode.name} mylabel").instructions[0]
    assert inst.opcode == opcode
    assert inst.address == "mylabel"
