import pytest

from daca.common.exc import CompileError, ParseError


def test_parse_error():
    with pytest.raises(ParseError, match="<SENTINEL> at"):
        raise ParseError(message="<SENTINEL>", line=1, column=1, value="<SENTINEL>")
    with pytest.raises(ParseError, match="<SENTINEL> at"):
        raise ParseError(message="<SENTINEL>", line=1, value="<SENTINEL>")
    with pytest.raises(ParseError, match="<SENTINEL>"):
        raise ParseError(message="<SENTINEL>", value="<SENTINEL>")
    with pytest.raises(ParseError, match="Unexpected <SENTINEL> at"):
        raise ParseError(line=1, column=1, value="<SENTINEL>")
    with pytest.raises(ParseError, match="Unexpected <SENTINEL> at"):
        raise ParseError(line=1, value="<SENTINEL>")
    with pytest.raises(ParseError, match="Unexpected <SENTINEL>"):
        raise ParseError(value="<SENTINEL>")
    with pytest.raises(CompileError):
        raise CompileError(value="<SENTINEL>")
