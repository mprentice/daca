from io import StringIO

from daca.common.lexer import SimpleRegexLineLexer
from daca.common.token import BufferedTokenStream, Token

SPEC = (("int", r"\d+"), ("whitespace", r"\s+"))
PROG = "123 345\t789\n10 14\n86"


def test_token():
    v = "test-value"
    n = len(v)
    line, column = 2, 4
    t = Token(tag="test", value=v, line=line, column=column)
    assert t.span == range(column, column + n)


def test_buffered_token_stream_next():
    lex = SimpleRegexLineLexer(spec=SPEC)
    toks = BufferedTokenStream(stream=lex.tokenize(StringIO(PROG)))
    t = next(toks)
    assert t.tag == "int"
    assert t.value == "123"


def test_buffered_token_stream_peek():
    lex = SimpleRegexLineLexer(spec=SPEC)
    toks = BufferedTokenStream(stream=lex.tokenize(StringIO(PROG)))
    t = toks.peek()
    assert t.tag == "int"
    assert t.value == "123"
    t = next(toks)
    assert t.tag == "int"
    assert t.value == "123"


def test_buffered_token_stream_rollback():
    lex = SimpleRegexLineLexer(spec=SPEC)
    toks = BufferedTokenStream(stream=lex.tokenize(StringIO(PROG)))
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
    lex = SimpleRegexLineLexer(spec=SPEC)
    toks = BufferedTokenStream(stream=lex.tokenize(StringIO(PROG)))
    toks.checkpoint()
    t = next(toks)
    assert t.tag == "int"
    t = next(toks)
    assert t.tag == "whitespace"
    toks.commit()
    t = next(toks)
    assert t.tag == "int"
    assert t.value == "345"
