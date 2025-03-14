from pathlib import Path

import pytest

from daca.pidgin_algol import tokenize


@pytest.fixture
def n_pow_n_file(pytestconfig) -> Path:
    return Path(pytestconfig.rootdir) / "examples" / "ch1" / "n_pow_n.algol"


@pytest.fixture
def n_pow_n(n_pow_n_file: Path) -> str:
    return n_pow_n_file.read_text()


def test_tokenize_n_pow_n_algol_program(n_pow_n: str):
    toks = [t for t in tokenize(n_pow_n)]
    assert len(toks) > 1
    assert toks[0].tag == "keyword"
    assert toks[-1].tag == "keyword"
    assert toks[-1].line > 0
    assert toks[2].tag == "register"
    assert toks[2].column > 0
