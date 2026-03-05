from collections.abc import Sequence
from pathlib import Path

import pytest

from daca.ram import Program, compile, parse


@pytest.fixture
def n_pow_n_file(pytestconfig) -> Path:
    return Path(pytestconfig.rootdir) / "examples" / "ch1" / "n_pow_n.ram"


@pytest.fixture
def n_pow_n(n_pow_n_file: Path) -> str:
    return n_pow_n_file.read_text()


@pytest.fixture
def n_pow_n_program(n_pow_n: str) -> Program:
    return parse(n_pow_n)


@pytest.fixture
def n_pow_n_compiled_program(n_pow_n_program: Program) -> Sequence[int]:
    return compile(n_pow_n_program)
