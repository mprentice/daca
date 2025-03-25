from daca.pidgin_algol.ast import Tag
from daca.pidgin_algol.lex import tokenize


def test_tokenize_n_pow_n_algol_program(n_pow_n: str):
    toks = [t for t in tokenize(n_pow_n)]
    assert len(toks) > 1
    assert toks[0].tag == Tag.keyword.name
    assert toks[-1].tag == Tag.keyword.name
    assert toks[-1].line > 0
    assert toks[2].tag == Tag.literal_id.name
    assert toks[2].column > 0
