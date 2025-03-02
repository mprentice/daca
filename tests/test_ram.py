from pathlib import Path

import pytest

from daca.ram import RAM, parse


@pytest.fixture
def n_pow_n_file() -> Path:
    return Path(__file__).parent.parent / "examples" / "ch1" / "n_pow_n.ram"


@pytest.fixture
def n_pow_n(n_pow_n_file: Path) -> str:
    return n_pow_n_file.read_text()


def test_program_parse(n_pow_n: str):
    p = parse(n_pow_n)
    assert p is not None


def test_program_serialize(n_pow_n: str):
    p = parse(n_pow_n)
    s = p.serialize()
    assert p == parse(s)


def test_ram(n_pow_n: str):
    program = parse(n_pow_n)
    input_tape = (5,)
    ram = RAM(program, input_tape)
    ram.run()
    assert len(ram.output_tape) == 1
    assert ram.output_tape[0] == 5**5
    assert ram.step_counter == 49
