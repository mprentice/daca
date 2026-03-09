"""Package for common utilities and abstract base classes (ABC)."""

from .exc import CompileError, HaltError, ParseError
from .lexer import BaseLexer, LineLexer, SimpleRegexLineLexer
from .parser import BaseParser
from .token import BufferedTokenStream, Token
from .util import pairwise, triplewise
