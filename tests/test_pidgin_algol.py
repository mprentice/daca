from pathlib import Path

import pytest

from daca.pidgin_algol import TokenType, tokenize


@pytest.fixture
def n_pow_n_file() -> Path:
    return Path(__file__).parent.parent / "examples" / "ch1" / "n_pow_n.algol"


@pytest.fixture
def n_pow_n(n_pow_n_file: Path) -> str:
    return n_pow_n_file.read_text()


def test_lexer(n_pow_n: str):
    toks = [t for t in tokenize(n_pow_n)]
    assert len(toks) == 47
    assert toks[0].type_ == TokenType.begin
    assert toks[-1].type_ == TokenType.end
    assert toks[-1].line > 0
    assert toks[-1].pos > 0
    assert toks[2].type_ == TokenType.id_
    assert toks[2].col > 0
