"""Module for working with Random Access Machines (RAM) and its programs.

Utilities to tokenize and parse files into a RAM Program.

RAM interpreter to run a RAM Program.
"""

from .ast import Tag
from .interpreter import RAM, HaltError, ReadError
from .lexer import Lexer, tokenize
from .parser import Parser, parse
from .program import (
    Address,
    Instruction,
    JumpTarget,
    Opcode,
    Operand,
    OperandFlag,
    Program,
)
