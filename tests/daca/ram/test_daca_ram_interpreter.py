from collections.abc import Sequence

from daca.ram import RAM


def test_ram(n_pow_n_compiled_program: Sequence[int]):
    input_tape = (5,)
    ram = RAM(n_pow_n_compiled_program, input_tape)
    ram.run()
    assert len(ram.output_tape) == 1
    assert ram.output_tape[0] == 5**5
    assert ram.step_counter == 49
