import pytest

from daca.common import ParseError
from daca.ram.parser import parse, tokenize


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
