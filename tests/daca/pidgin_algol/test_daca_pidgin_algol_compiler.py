from pathlib import Path

import pytest

from daca.common import CompileError
from daca.pidgin_algol import compile_to_ram
from daca.ram import RAM


@pytest.fixture
def n_pow_n(pytestconfig) -> str:
    p = Path(pytestconfig.rootdir) / "examples" / "ch1" / "n_pow_n.algol"
    return p.read_text()


@pytest.fixture
def equal_count(pytestconfig) -> str:
    p = Path(pytestconfig.rootdir) / "examples" / "ch1" / "equal_count.algol"
    return p.read_text()


def test_pidgin_algol_compile_to_ram_n_pow_n(n_pow_n: str):
    p = compile_to_ram(n_pow_n)
    r = RAM(p, [5])
    r.run()
    assert r.output_tape[0] == 3125


def test_pidgin_algol_compile_to_ram_equal_count(equal_count: str):
    p = compile_to_ram(equal_count)
    r = RAM(p, [])
    r.run()
    assert r.output_tape[0] == 1
    r = RAM(p, [1, 2, 1, 1, 2, 1, 2, 2])
    r.run()
    assert r.output_tape[0] == 1
    r = RAM(p, [1, 2, 1, 1, 2, 1, 2, 2, 2])
    r.run()
    assert not r.output_tape


def test_pidgin_algol_compile_to_ram_error():
    with pytest.raises(CompileError, match="divide by literal 0"):
        _ = compile_to_ram("begin read r1; r1 ← r1 / 0 end")
