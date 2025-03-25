from pathlib import Path

import pytest

from daca.pidgin_algol.ast import AST
from daca.pidgin_algol.parser import parse


@pytest.fixture
def n_pow_n_file(pytestconfig) -> Path:
    return Path(pytestconfig.rootdir) / "examples" / "ch1" / "n_pow_n.algol"


@pytest.fixture
def n_pow_n(n_pow_n_file: Path) -> str:
    return n_pow_n_file.read_text()


@pytest.fixture
def n_pow_n_ast(n_pow_n: str) -> AST:
    return parse(n_pow_n)


@pytest.fixture
def equal_count_file(pytestconfig) -> Path:
    return Path(pytestconfig.rootdir) / "examples" / "ch1" / "equal_count.algol"


@pytest.fixture
def equal_count(equal_count_file: Path) -> str:
    return equal_count_file.read_text()


@pytest.fixture
def equal_count_ast(equal_count: str) -> AST:
    return parse(equal_count)
