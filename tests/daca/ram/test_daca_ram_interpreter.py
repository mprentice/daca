from daca.ram.interpreter import RAM
from daca.ram.program import Program


def test_ram(n_pow_n_program: Program):
    input_tape = (5,)
    ram = RAM(n_pow_n_program, input_tape)
    ram.run()
    assert len(ram.output_tape) == 1
    assert ram.output_tape[0] == 5**5
    assert ram.step_counter == 49
