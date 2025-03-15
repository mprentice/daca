import textwrap
from argparse import ArgumentParser, FileType
from dataclasses import dataclass, field
from pprint import pprint
from typing import Iterable, Optional

from daca.common import Token

from .parser import parse, tokenize


class CliArgumentParser(ArgumentParser):
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

        if args.parse:
            ast = parse(tokens)
            if args.verbose:
                pprint(ast)
            else:
                print(ast.serialize())


def main(argv: Optional[list[str]] = None) -> None:
    CliApp().main(argv)


if __name__ == "__main__":
    main()
