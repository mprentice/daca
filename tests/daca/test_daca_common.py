from daca.common import BufferedTokenStream, SimpleRegexLineLexer, Token


def test_token():
    v = "test-value"
    n = len(v)
    line, column = 2, 4
    t = Token(tag="test", value=v, line=line, column=column)
    assert t.span == range(column, column + n)


def test_simple_regex_line_lexer():
    lex = SimpleRegexLineLexer(spec=(("int", r"\d+"), ("anything", r".")))
    toks = list(lex.tokenize("123\n&"))
    assert toks[0].tag == "int"
    assert toks[0].value == "123"
    assert toks[0].line == 0
    assert toks[0].column == 0
    assert toks[1].tag == "anything"
    assert toks[1].value == "&"
    assert toks[1].line == 1
    assert toks[1].column == 0


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


def test_buffered_token_stream_getitem():
    lex = SimpleRegexLineLexer(spec=(("int", r"\d+"), ("whitespace", r"\s+")))
    toks = BufferedTokenStream(stream=lex.tokenize("123 345\t789\n10 14\n86"))
    t = toks[2]
    assert t.tag == "int"
    assert t.value == "345"
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
