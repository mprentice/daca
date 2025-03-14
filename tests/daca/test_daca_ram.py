from pathlib import Path

import pytest

from daca.common import ParseError
from daca.ram import RAM, parse, tokenize


@pytest.fixture
def n_pow_n_file(pytestconfig) -> Path:
    return Path(pytestconfig.rootdir) / "examples" / "ch1" / "n_pow_n.ram"


@pytest.fixture
def n_pow_n(n_pow_n_file: Path) -> str:
    return n_pow_n_file.read_text()


def test_tokenize_n_pow_n(n_pow_n: str):
    toks = list(tokenize(n_pow_n))
    assert len(toks) > 10


def test_tokenize_error():
    with pytest.raises(ParseError):
        list(tokenize("STORE &1"))


def test_program_parse(n_pow_n: str):
    p = parse(n_pow_n)
    assert p is not None


def test_program_parse_error():
    with pytest.raises(ParseError):
        parse("STORE =1")


def test_program_serialize(n_pow_n: str):
    p = parse(n_pow_n)
    assert p == parse(p.serialize())


def test_ram(n_pow_n: str):
    program = parse(n_pow_n)
    input_tape = (5,)
    ram = RAM(program, input_tape)
    ram.run()
    assert len(ram.output_tape) == 1
    assert ram.output_tape[0] == 5**5
    assert ram.step_counter == 49
