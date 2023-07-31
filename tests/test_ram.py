from pathlib import Path

from daca.ram import RAM, parse


def test_ram_n_pow_n():
    p = Path(__file__).parent.parent / "examples" / "ch1" / "n_pow_n.ram"
    input_tape = [5]
    program = parse(p.read_text())
    ram = RAM(program, input_tape)
    ram.run()
    assert ram.output_tape == [5**5]
