from argparse import ArgumentParser, FileType
from typing import Optional

from .machine import RAM
from .parser import parse


class CliArgumentParser(ArgumentParser):
    def __init__(self, **kwargs):
        # kwargs["prog"] = "ram"
        kwargs["description"] = "Run specified RAM program on input tape."
        super().__init__(**kwargs)
        self.add_argument(
            "program", type=FileType("r"), nargs=1, help="Program for RAM"
        )
        self.add_argument("input", type=int, nargs="*", help="Program input tape")


class CliApp:
    def main(self, argv: Optional[list[str]] = None) -> None:
        """CLI application main method."""
        arg_parser = CliArgumentParser()
        args = arg_parser.parse_args() if argv is None else arg_parser.parse_args(argv)

        input_tape = tuple(args.input)
        program = parse(args.program[0].read())

        ram = RAM(program, input_tape)

        ram.run()

        print(" ".join([str(i) for i in ram.output_tape]))


def main(argv: Optional[list[str]] = None) -> None:
    """CLI main method."""
    CliApp().main(argv)


if __name__ == "__main__":
    main()
