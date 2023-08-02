"""This module contains an implementation of a random access machine (RAM) and
a simple parser for its instruction set.

Classes:
    RAM: Implementation of the random access machine.
    Program: Represents a RAM program, including instructions and jumptable.
    Instruction: Represents a single RAM instruction.

Functions:
    parse(s): Parse the input string and return an instance of Program.
    main(argv): Entry point for the command line application to run a RAM
                program.

Exceptions:
    HaltError: Thrown when trying to execute a halted RAM.
    ReadError: Thrown when trying to read past end of input tape.

"""

import argparse


class RAM:
    """A random access machine (RAM) models a one-accumulator computer.

    A RAM consists of a read-only input tape, a write-only output tape, a
    program, and registers (memory). Instructions are not permitted to modify
    themselves. Memory is an arbitrarily large sequence of integer registers.

    The machine execution methods (LOAD, STORE, ADD, JUMP, etc.) are in all
    caps and should not be called directly.

    The run and step methods raise errors if the machine is in a halted state.

    Attributes:
        program (Program): RAM program being executed
        input_tape (list): The input tape for the RAM
        read_head (int): Index of the read head for the input_tape
        output_tape (list): The output tape for the RAM. The write head is
                            always at the end of the tape.
        registers (dict): Arbitrarily large RAM memory, implemented as a mapping
                          from register index (int) to register value (int)
        lc (int): Location counter for next program instruction to execute
        halted (bool): True if the machine is halted or in a bad state

    """

    def __init__(self, program, input_tape=None):
        """Create a new RAM machine with given program and input tape.

        Args:
            program (Program): Program for the machine to run
            input_tape (list): Input tape for the machine (optional, default
                               is a blank tape)

        """
        self.program = program
        self.input_tape = input_tape if input_tape is not None else list()
        self.read_head = 0
        self.output_tape = list()
        self.registers = {0: 0}
        self.lc = 0
        self.halted = False

    def run(self):
        """Run the machine until reaching a halting state.

        Steps through the next instruction until halting by repeatedly calling
        the step method.

        Throws:
            HaltError if the machine is in a halted state.
            ReadError if attempting to read past the end of the input tape.

        """
        while not self.halted:
            self.step()

    def step(self):
        """Execute the next instruction.

        Throws:
            HaltError if the machine is in a halted state.
            ReadError if attempting to read past the end of the input tape.

        """
        if self.halted:
            raise HaltError("Attempt to step program on halted machine state")
        self.lc = self._dispatch(self.program.instructions[self.lc])

    def _dispatch(self, ins):
        if ins.opcode == "HALT":
            return self.HALT()
        m = getattr(self, ins.opcode)
        return m(ins.address)

    def LOAD(self, a):
        self.set_c(0, self.v(a))
        return self.lc + 1

    def STORE(self, i):
        if i[:1] == "*":
            self.set_c(self.c(int(i[1:])), self.c(0))
        else:
            self.set_c(int(i), self.c(0))
        return self.lc + 1

    def ADD(self, a):
        self.set_c(0, self.c(0) + self.v(a))
        return self.lc + 1

    def SUB(self, a):
        self.set_c(0, self.c(0) - self.v(a))
        return self.lc + 1

    def MULT(self, a):
        self.set_c(0, self.c(0) * self.v(a))
        return self.lc + 1

    def DIV(self, a):
        self.set_c(0, self.c(0) / self.v(a))
        return self.lc + 1

    def READ(self, i):
        try:
            if i[:1] == "*":
                self.set_c(self.c(int(i[1:])), self.input_tape[self.read_head])
            else:
                self.set_c(int(i), self.input_tape[self.read_head])
        except IndexError:
            self.halted = True
            raise ReadError("Tried to read past end of input tape.")
        self.read_head += 1
        return self.lc + 1

    def WRITE(self, a):
        self.output_tape.append(self.v(a))
        return self.lc + 1

    def JUMP(self, b):
        return self.program.jumptable[b]

    def JGTZ(self, b):
        if self.c(0) > 0:
            return self.program.jumptable[b]
        else:
            return self.lc + 1

    def JZERO(self, b):
        if self.c(0) == 0:
            return self.program.jumptable[b]
        else:
            return self.lc + 1

    def HALT(self):
        self.halted = True
        return self.lc

    def c(self, i):
        """c(i): Return the value stored at register i."""
        return self.registers[i]

    def set_c(self, i, v):
        """c(i) <- v: Set the value at register i to v."""
        self.registers[i] = v

    def v(self, address):
        """v(address): Return the value for address.

        Address can be one of:
            =i Literal value of integer i
            i  Integer value stored at register i
            *i Integer value stored at the register number stored in register i
               (indirect address)

        """
        if address[:1] == "=":
            return int(address[1:])
        elif address[:1] == "*":
            return self.c(self.c(int(address[1:])))
        else:
            return self.c(int(address))

    def ascii_draw(self):
        """Return a representation of the machine's current state as ASCII art."""
        o = list()
        o.append("I: " + self._ascii_tape(self.input_tape))
        o.append("   " + self._ascii_tape_head(self.input_tape, self.read_head, "^"))
        o.append(self._ascii_ram())
        o.append(
            "   " + self._ascii_tape_head(self.output_tape, len(self.output_tape), "v")
        )
        o.append("O: " + self._ascii_tape(self.output_tape))
        return "\n".join(o)

    def _ascii_tape(self, tape):
        try:
            max_cell = max(len(str(i)) for i in tape)
            fmt = "{:^" + str(max_cell) + "}"
            return "[" + "][".join(fmt.format(c) for c in tape) + "]"
        except ValueError:
            return "[_]"

    def _ascii_tape_head(self, tape, index, symbol):
        try:
            cell_width = 2 + max(len(str(i)) for i in tape)
            return " " * (cell_width * index + 1) + symbol
        except ValueError:
            return " " + symbol

    def _ascii_ram(self):
        return ""

    def __repr__(self):
        return "RAM({}, {})".format(repr(self.program), repr(self.input_tape))

    __str__ = __repr__


class Program:
    def __init__(self, instructions, jumptable):
        self.instructions = instructions
        self.jumptable = jumptable

    def emit(self):
        left = self._label_column()
        right = self.instructions
        return "\n".join([lft + str(rgt) for lft, rgt in zip(left, right)])

    def _label_column(self):
        sep = ": "
        indent = max([0] + [len(k) + len(sep) for k in self.jumptable.keys()])
        prefix = " " * indent
        label_column = [prefix] * len(self.instructions)
        for label, line in self.jumptable.iteritems():
            label_column[line] = (label + sep).ljust(indent)
        return label_column

    def __str__(self):
        return self.emit()


class Instruction:
    """
    Representation of a single RAM instruction.

    An instruction consists of an opcode and an optional address. An address
    can be an operand or a label.

    """

    def __init__(self, opcode, address=None):
        self.opcode = opcode
        self.address = address

    def __repr__(self):
        return "Instruction({}, {})".format(self.opcode, self.address)

    def __str__(self):
        if self.address is None:
            return self.opcode
        else:
            return str(self.opcode) + " " + str(self.address)


class HaltError(ValueError):
    """Thrown when trying to execute a halted RAM."""


class ReadError(IndexError):
    """Thrown when trying to read past end of input tape."""


def parse(s):
    index = 0
    jumptable = dict()
    instructions = list()
    acc = None
    for tok in s.split():
        if acc is None and tok == "HALT":
            instructions.append(Instruction("HALT"))
            index += 1
        elif acc is None and tok[-1] == ":":
            jumptable[tok[:-1]] = index
        elif acc is None:
            acc = tok
        else:
            instructions.append(Instruction(acc, tok))
            acc = None
            index += 1
    return Program(instructions, jumptable)


def main():
    parser = argparse.ArgumentParser(
        description="Run specified RAM program on input tape."
    )
    parser.add_argument(
        "program", type=argparse.FileType("r"), nargs=1, help="Program for RAM"
    )
    parser.add_argument("input", type=int, nargs="*", help="Program input tape")
    args = parser.parse_args()
    program = parse(args.program[0].read())
    input_tape = args.input
    ram = RAM(program, input_tape)
    ram.run()
    print(" ".join([str(i) for i in ram.output_tape]))


if __name__ == "__main__":
    main()
