"""Parser for RAM program."""

from typing import TextIO

from .machine import Instruction, Opcode, Program


def parse(s: str | TextIO) -> Program:
    text = s if isinstance(s, str) else s.read()

    index = 0
    jumptable = {}
    instructions = []
    opcode = None
    for tok in text.split():
        if opcode is None and tok == "HALT":
            instructions.append(Instruction(Opcode("HALT")))
            index += 1
        elif opcode is None and tok[-1] == ":":
            label = tok[:-1]
            jumptable[label] = index
        elif opcode is None:
            opcode = tok
        else:
            address = tok
            instructions.append(Instruction(Opcode(opcode), address))
            opcode = None
            index += 1

    return Program(instructions, jumptable)
