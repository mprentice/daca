"""Random Access Machine (RAM)

This module contains an implementation of a random access machine (RAM) and
a simple parser for its instruction set.
"""

import argparse
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Optional


class HaltError(ValueError):
    """Thrown when trying to execute a halted RAM."""


class ReadError(IndexError):
    """Thrown when trying to read past end of input tape."""


class Opcode(StrEnum):
    """Enumeration of RAM instructions opcodes."""

    LOAD = "LOAD"
    STORE = "STORE"
    ADD = "ADD"
    SUB = "SUB"
    MULT = "MULT"
    DIV = "DIV"
    READ = "READ"
    WRITE = "WRITE"
    JUMP = "JUMP"
    JGTZ = "JGTZ"
    JZERO = "JZERO"
    HALT = "HALT"


@dataclass(frozen=True)
class Instruction:
    """Representation of a single RAM instruction.

    An instruction consists of an opcode and an optional address. An address
    can be an operand or a label. An instruction cannot be modified.

    """

    opcode: Opcode
    address: Optional[str] = None


@dataclass(frozen=True)
class Program:
    """Representation of a RAM program. Cannot be modified."""

    instructions: Sequence[Instruction]
    jumptable: Mapping[str, int]

    def serialize(self):
        pad = 0
        if self.jumptable:
            pad = max([len(k) for k in self.jumptable.keys()]) + 3
        jumplabels = {v: k for k, v in self.jumptable.items()}
        lines = []
        for index, inst in enumerate(self.instructions):
            label = jumplabels[index] + ": " if index in jumplabels else ""
            address = inst.address or ""
            line = f"{label:<{pad}}{inst.opcode.value:<7}{address}".rstrip()
            lines.append(line)
        return "\n".join(lines)

    @classmethod
    def parse(cls, s: str) -> "Program":
        index = 0
        jumptable = {}
        instructions = []
        opcode = None
        for tok in s.split():
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
        return cls(tuple(instructions), jumptable)


@dataclass
class RAM:
    """A random access machine (RAM) models a one-accumulator computer.

    A RAM consists of a read-only input tape, a write-only output tape, a
    program, and registers (memory). Instructions are not permitted to modify
    themselves. Memory is an arbitrarily large sequence of integer registers.

    The machine execution methods (LOAD, STORE, ADD, JUMP, etc.) are in all
    caps and should not be called directly.

    The run and step methods raise errors if the machine is in a halted state.
    """

    program: Program
    input_tape: Sequence[int] = field(default_factory=tuple)
    read_head: int = 0
    location_counter: int = 0
    memory_registers: MutableMapping[int, int] = field(default_factory=lambda: {0: 0})
    output_tape: MutableSequence[int] = field(default_factory=list)
    halted: bool = False
    step_counter: int = 0

    def run(self) -> None:
        """Run the machine until reaching a halting state.

        Steps through the next instruction until halting by repeatedly calling
        the step method.

        Throws:
            HaltError if the machine is in a halted state.
            ReadError if attempting to read past the end of the input tape.

        """
        while not self.halted:
            self.step()

    def step(self) -> None:
        """Execute the next instruction.

        Throws:
            HaltError if the machine is in a halted state.
            ReadError if attempting to read past the end of the input tape.

        """
        if self.halted:
            raise HaltError("Attempt to step program on halted machine state")
        self.location_counter = self.dispatch(
            self.program.instructions[self.location_counter]
        )
        self.step_counter += 1

    def dispatch(self, ins: Instruction) -> int:
        """Dispatch and run one instruction (one step).

        Returns location counter for next instruction.
        """
        if self.halted:
            raise HaltError(
                f"Attempt to dispatch instruction: {ins} on halted machine state"
            )
        if ins.opcode == Opcode.HALT:
            return self.HALT()
        m = getattr(self, ins.opcode.value)
        return m(ins.address)

    def LOAD(self, a: str) -> int:
        """LOAD a: c(0) <- v(a)"""
        self.set_c(0, self.v(a))
        return self.location_counter + 1

    def STORE(self, i: str) -> int:
        """STORE i: c(i) <- c(0)

        STORE *i: c(c(i)) <- c(0)
        """
        if i.startswith("*"):
            self.set_c(self.c(int(i[1:])), self.c(0))
        else:
            self.set_c(int(i), self.c(0))
        return self.location_counter + 1

    def ADD(self, a: str) -> int:
        """ADD a: c(0) <- c(0) + v(a)"""
        self.set_c(0, self.c(0) + self.v(a))
        return self.location_counter + 1

    def SUB(self, a: str) -> int:
        """SUB a: c(0) <- c(0) - v(a)"""
        self.set_c(0, self.c(0) - self.v(a))
        return self.location_counter + 1

    def MULT(self, a: str) -> int:
        """MULT a: c(0) <- c(0) * v(a)"""
        self.set_c(0, self.c(0) * self.v(a))
        return self.location_counter + 1

    def DIV(self, a: str) -> int:
        """DIV a: c(0) <- c(0) * v(a)"""
        self.set_c(0, self.c(0) // self.v(a))
        return self.location_counter + 1

    def READ(self, i: str) -> int:
        """READ i: c(i) <- current input tape symbol

        READ *i: c(c(i)) <- current input tape symbol

        Input tape head moves one square right.
        """
        try:
            if i.startswith("*"):
                self.set_c(self.c(int(i[1:])), self.input_tape[self.read_head])
            else:
                self.set_c(int(i), self.input_tape[self.read_head])
        except IndexError as ex:
            self.halted = True
            raise ReadError("Tried to read past end of input tape.") from ex
        self.read_head += 1
        return self.location_counter + 1

    def WRITE(self, a: str) -> int:
        """WRITE a: v(a) is printed on the output tape

        Output tape head moves one square right.
        """
        self.output_tape.append(self.v(a))
        return self.location_counter + 1

    def JUMP(self, b: str) -> int:
        """JUMP b: set location counter to instruction labeled b"""
        return self.program.jumptable[b]

    def JGTZ(self, b: str) -> int:
        """JGTZ b: conditionally set location counter to instruction labeled b

        If c(0) > 0: set location counter to instruction labeled b

        Otherwise, set location counter to next instruction"""
        if self.c(0) > 0:
            return self.program.jumptable[b]
        else:
            return self.location_counter + 1

    def JZERO(self, b: str) -> int:
        """JZERO b: conditionally set location counter to instruction labeled b

        If c(0) = 0: set location counter to instruction labeled b

        Otherwise, set location counter to next instruction"""
        if self.c(0) == 0:
            return self.program.jumptable[b]
        else:
            return self.location_counter + 1

    def HALT(self) -> int:
        """Halt execution of machine."""
        self.halted = True
        return self.location_counter

    def c(self, i: int) -> int:
        """c(i): Return the value stored at register i."""
        try:
            return self.memory_registers[i]
        except KeyError as ex:
            raise IndexError(f"Read from uninitialized memory register {i}") from ex

    def set_c(self, i: int, v: int) -> None:
        """c(i) <- v: Set the value at register i to v."""
        self.memory_registers[i] = v

    def v(self, a: str) -> int:
        """v(a): Return the value for address a.

        Address can be one of:
            =i Literal value of integer i
            i  Integer value stored at register i
            *i Integer value stored at the register number stored in register i
               (indirect address)

        """
        if a.startswith("="):
            return int(a[1:])
        elif a.startswith("*"):
            return self.c(self.c(int(a[1:])))
        else:
            return self.c(int(a))


def make_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run specified RAM program on input tape."
    )
    parser.add_argument(
        "program", type=argparse.FileType("r"), nargs=1, help="Program for RAM"
    )
    parser.add_argument("input", type=int, nargs="*", help="Program input tape")
    return parser


def main(argv: Optional[list[str]] = None) -> None:
    parser = make_arg_parser()
    args = parser.parse_args() if argv is None else parser.parse_args(argv)

    input_tape = tuple(args.input)
    program = Program.parse(args.program[0].read())

    ram = RAM(program, input_tape)

    ram.run()

    print(" ".join([str(i) for i in ram.output_tape]))


if __name__ == "__main__":
    main()
