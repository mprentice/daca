"""Command line interface (CLI) for working with the Pidgin Algol language."""

import textwrap
from argparse import ArgumentParser, FileType
from dataclasses import dataclass, field
from pprint import pprint
from typing import Iterable, Optional

from daca.common import Token
from daca.ram import RAM

from .compiler import compile_to_ram
from .lex import tokenize
from .parse import parse


class CliArgumentParser(ArgumentParser):
    """Argument parser for Pidgin Algol CLI."""

    def __init__(self):
        super().__init__(prog="palgol", description="Run a pidgin ALGOL program")
        self.add_argument(
            "--no-execute",
            "-n",
            action="store_true",
            default=False,
            help="Only parse PROGRAM, don't execute it.",
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
            help="Show PROGRAM compiled to RAM",
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
            help="Pidgin ALGOL program file",
            metavar="PROGRAM",
        )
        self.add_argument(
            "input", type=int, nargs="*", help="Program input tape", metavar="CELL"
        )


@dataclass
class CliApp:
    """Application for parsing, compiling, and running a Pidgin Algol program."""

    arg_parser: CliArgumentParser = field(default_factory=CliArgumentParser)

    def main(self, argv: Optional[list[str]] = None) -> None:
        """CLI application main method."""
        args = (
            self.arg_parser.parse_args()
            if argv is None
            else self.arg_parser.parse_args(argv)
        )

        # input_tape = tuple(args.input)
        program_file = args.program
        tokens: Iterable[Token] = tokenize(program_file)

        if args.tokenize:
            tokens = list(tokens)
            if args.verbose:
                pprint(tokens)
            else:
                tok_vals = [t.value for t in tokens]
                print(
                    "\n".join(textwrap.wrap("«" + "» «".join(tok_vals) + "»", width=80))
                )

        ast = parse(tokens)

        if args.parse:
            if args.verbose:
                print("Parsed pidgin algol program:\n")
            print(f"{ast}")
            print()

        ram_program = compile_to_ram(ast)

        if args.compile:
            if args.verbose:
                print("RAM instructions for compiled pidgin algol program:\n")
            print(f"{ram_program}")
            print()

        if args.no_execute:
            if args.verbose:
                print("--no-execute mode specified, skipping program execution")
            return

        input_tape = tuple(args.input)
        ram = RAM(ram_program, input_tape)

        ram.run()

        if args.verbose:
            print("RAM execution complete.\n")
            print(f"Input tape: {input_tape}")
            print(f"# of steps: {ram.step_counter}")
            print(f"Halted: {ram.halted}")
            print(f"Output tape: {ram.output_tape}")
        else:
            print(" ".join([str(i) for i in ram.output_tape]))


def main(argv: Optional[list[str]] = None) -> None:
    """CLI main method."""
    CliApp().main(argv)


if __name__ == "__main__":
    main()
