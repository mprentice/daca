import pytest

from daca.common import ParseError
from daca.ram.lex import tokenize


def test_tokenize_n_pow_n(n_pow_n: str):
    toks = list(tokenize(n_pow_n))
    assert len(toks) > 10


def test_tokenize_error():
    with pytest.raises(ParseError):
        list(tokenize("STORE &1"))
