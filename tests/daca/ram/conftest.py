import importlib.resources
from pathlib import Path

import pytest

from daca.ram import Program, parse


@pytest.fixture
def n_pow_n_file() -> Path:
    with importlib.resources.path("examples", "ch1/n_pow_n.ram") as p:
        yield p


@pytest.fixture
def n_pow_n(n_pow_n_file: Path) -> str:
    return n_pow_n_file.read_text()


@pytest.fixture
def n_pow_n_program(n_pow_n: str) -> Program:
    return parse(n_pow_n)
