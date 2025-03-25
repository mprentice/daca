from daca.common.lexer import SimpleRegexLineLexer


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
