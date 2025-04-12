"""Command line interface (CLI) for working with the RAM interpreter."""

import textwrap
from argparse import ArgumentParser, FileType
from dataclasses import dataclass, field
from pprint import pprint
from typing import Iterable, Optional

from daca.common import Token

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

        program = parse(tokens)

        if args.parse:
            print(f"{program}")

        if args.no_execute:
            return

        ram = RAM(program, input_tape)

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
            print(" ".join([str(i) for i in ram.output_tape]))


def main(argv: Optional[list[str]] = None) -> None:
    """CLI main method."""
    CliApp().main(argv)


if __name__ == "__main__":
    main()
