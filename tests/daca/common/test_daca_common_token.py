from daca.common.lex import SimpleRegexLineLexer
from daca.common.token import BufferedTokenStream, Token


def test_token():
    v = "test-value"
    n = len(v)
    line, column = 2, 4
    t = Token(tag="test", value=v, line=line, column=column)
    assert t.span == range(column, column + n)


def test_buffered_token_stream_next():
    lex = SimpleRegexLineLexer(spec=(("int", r"\d+"), ("whitespace", r"\s+")))
    toks = BufferedTokenStream(stream=lex.tokenize("123 345\t789\n10 14\n86"))
    t = next(toks)
    assert t.tag == "int"
    assert t.value == "123"


def test_buffered_token_stream_peek():
    lex = SimpleRegexLineLexer(spec=(("int", r"\d+"), ("whitespace", r"\s+")))
    toks = BufferedTokenStream(stream=lex.tokenize("123 345\t789\n10 14\n86"))
    t = toks.peek()
    assert t.tag == "int"
    assert t.value == "123"
    t = next(toks)
    assert t.tag == "int"
    assert t.value == "123"


def test_buffered_token_stream_rollback():
    lex = SimpleRegexLineLexer(spec=(("int", r"\d+"), ("whitespace", r"\s+")))
    toks = BufferedTokenStream(stream=lex.tokenize("123 345\t789\n10 14\n86"))
    toks.checkpoint()
    t = next(toks)
    assert t.tag == "int"
    t = next(toks)
    assert t.tag == "whitespace"
    assert t.value == " "
    toks.rollback()
    t = next(toks)
    assert t.tag == "int"
    assert t.value == "123"


def test_buffered_token_stream_commit():
    lex = SimpleRegexLineLexer(spec=(("int", r"\d+"), ("whitespace", r"\s+")))
    toks = BufferedTokenStream(stream=lex.tokenize("123 345\t789\n10 14\n86"))
    toks.checkpoint()
    t = next(toks)
    assert t.tag == "int"
    t = next(toks)
    assert t.tag == "whitespace"
    toks.commit()
    t = next(toks)
    assert t.tag == "int"
    assert t.value == "345"
