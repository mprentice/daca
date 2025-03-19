import textwrap
from argparse import ArgumentParser, FileType
from dataclasses import dataclass, field
from pprint import pprint
from typing import Iterable, Optional

from daca.common import Token

from .interpreter import RAM
from .parser import parse, tokenize


class CliArgumentParser(ArgumentParser):
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
            print(program.serialize())

        if args.no_execute:
            return

        ram = RAM(program, input_tape)

        ram.run()

        if args.verbose:
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
