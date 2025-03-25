from pathlib import Path

import pytest

from daca.ram.parse import parse
from daca.ram.program import Program


@pytest.fixture
def n_pow_n_file(pytestconfig) -> Path:
    return Path(pytestconfig.rootdir) / "examples" / "ch1" / "n_pow_n.ram"


@pytest.fixture
def n_pow_n(n_pow_n_file: Path) -> str:
    return n_pow_n_file.read_text()


@pytest.fixture
def n_pow_n_program(n_pow_n: str) -> Program:
    return parse(n_pow_n)
