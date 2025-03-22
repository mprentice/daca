"""Module for working with Random Access Machines (RAM) and its programs.

Utilities to tokenize and parse files into a RAM Program.

RAM interpreter to run a RAM Program.
"""

from .interpreter import RAM, HaltError, ReadError
from .parser import Lexer, Parser, Tag, parse, tokenize
from .program import (
    Address,
    Instruction,
    JumpTarget,
    Opcode,
    Operand,
    OperandFlag,
    Program,
)
