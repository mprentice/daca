"""Command line interface (CLI) for working with the RAM interpreter."""

import json
import textwrap
from argparse import ArgumentParser, FileType
from contextlib import closing
from dataclasses import dataclass, field
from pprint import pprint
from typing import Iterable, Optional

from daca.common import Token

from .compiler import compile, decompile
from .interpreter import RAM
from .lexer import tokenize
from .parser import parse


class CliArgumentParser(ArgumentParser):
    """Argument parser for RAM CLI."""

    def __init__(self):
        super().__init__(
            prog="ram", description="Run specified RAM program on input tape."
        )
        self.add_argument(
            "--no-execute",
            "-n",
            action="store_true",
            default=False,
            help="Don't execute PROGRAM.",
        )
        self.add_argument(
            "--tokenize",
            "-t",
            action="store_true",
            default=False,
            help="Show tokenization of PROGRAM",
        )
        self.add_argument(
            "--parse",
            "-p",
            action="store_true",
            default=False,
            help="Show serialization of parsed PROGRAM",
        )
        self.add_argument(
            "--compile",
            "-c",
            action="store_true",
            default=False,
            help="Show compilation of PROGRAM.",
        )
        self.add_argument(
            "--decompile",
            "-d",
            action="store_true",
            default=False,
            help="Show decompilation of compiled PROGRAM.",
        )
        self.add_argument(
            "--verbose",
            "-v",
            action="store_true",
            default=False,
            help="Show verbose output for debugging",
        )
        self.add_argument(
            "program",
            type=FileType("r"),
            help="Program for RAM",
            metavar="PROGRAM",
        )
        self.add_argument(
            "input", type=int, nargs="*", help="Program input tape", metavar="CELL"
        )


@dataclass
class CliApp:
    """Application for running RAM CLI."""

    arg_parser: CliArgumentParser = field(default_factory=CliArgumentParser)

    def main(self, argv: Optional[list[str]] = None) -> None:
        """CLI application main method."""
        args = (
            self.arg_parser.parse_args()
            if argv is None
            else self.arg_parser.parse_args(argv)
        )

        input_tape = tuple(args.input)

        if (
            args.decompile
            or args.program.name.lower().endswith(".ramc")
            or args.program.buffer.peek(1).decode().strip().startswith("{")
        ):
            with closing(args.program):
                d = json.load(args.program)
            instructions = d["instructions"]
            if args.decompile:
                jumptable = d.get("jumptable")
                ast = decompile(instructions, jumptable)
                print(f"{ast}")
            ram = RAM(instructions, input_tape)
        else:
            with closing(args.program):
                tokens: Iterable[Token] = tokenize(args.program)

                if args.tokenize:
                    tokens = list(tokens)
                    if args.verbose:
                        pprint(tokens)
                    else:
                        tok_vals = [t.value for t in tokens]
                        print(
                            "\n".join(
                                textwrap.wrap(
                                    "«" + "» «".join(tok_vals) + "»", width=80
                                )
                            )
                        )

                ast = parse(tokens)
            if args.parse:
                print(f"{ast}")

            program = compile(ast)

            if args.compile:
                print(json.dumps({"instructions": program, "jumptable": ast.jumptable}))

            ram = RAM(program, input_tape)

        if args.no_execute:
            return

        ram.run()

        if args.verbose:
            print(f"Input tape: {input_tape}")
            print(f"# of steps: {ram.step_counter}")
            print(f"# of memory registers: {ram.uniform_space_cost}")
            print(f"Total step log cost: {ram.step_cost}")
            print(f"Total space log cost: {ram.log_space_cost}")
            print(f"Halted: {ram.halted}")
            try:
                print(f"Output tape: {ram.output_tape}")
            except ValueError as e:
                if "Exceeds the limit" in str(e):
                    n = len(ram.output_tape)
                    print(f"Output tape: [<{n} item(s)>] (contents too large to show)")
                else:
                    raise
        else:
            if len(ram.output_tape) == 1:
                print(ram.output_tape[0])
            else:
                pprint(ram.output_tape)


def main(argv: Optional[list[str]] = None) -> None:
    """CLI main method."""
    CliApp().main(argv)


if __name__ == "__main__":
    main()
