import pytest

from daca.common import CompileError
from daca.pidgin_algol import compile_to_ram
from daca.ram import RAM


def test_compile_block_statement():
    s = "begin read x; write x end"
    p = compile_to_ram(s)
    ram = RAM(p.bytecode)
    ram.run([777])
    assert ram.output_tape == [777]
    s = "begin read x; write x; end"
    p = compile_to_ram(s)
    ram = RAM(p.bytecode)
    ram.run([778])
    assert ram.output_tape == [778]


def test_compile_read_statement_write_statement_variable():
    s = "begin read x; write x; end"
    p = compile_to_ram(s)
    ram = RAM(p.bytecode)
    ram.run([777])
    assert ram.output_tape == [777]


def test_compile_write_statement_literal():
    s = "write 997"
    p = compile_to_ram(s)
    ram = RAM(p.bytecode)
    ram.run()
    assert ram.output_tape == [997]


def test_compile_if_statement_x_lt_y():
    s = "begin read x; read y; if x < y then write 1 end"
    p = compile_to_ram(s)
    ram = RAM(p.bytecode)
    ram.run([1, 2])
    assert ram.output_tape == [1]
    ram.run([2, 2])
    assert ram.output_tape == []


def test_compile_if_statement_x_le_y():
    s = "begin read x; read y; if x <= y then write 1 end"
    p = compile_to_ram(s)
    ram = RAM(p.bytecode)
    ram.run([2, 2])
    assert ram.output_tape == [1]
    ram.run([3, 2])
    assert ram.output_tape == []


def test_compile_if_statement_x_eq_y():
    s = "begin read x; read y; if x = y then write 1 end"
    p = compile_to_ram(s)
    ram = RAM(p.bytecode)
    ram.run([2, 2])
    assert ram.output_tape == [1]
    ram.run([1, 2])
    assert ram.output_tape == []


def test_compile_if_statement_x_ne_y():
    s = "begin read x; read y; if x != y then write 1 end"
    p = compile_to_ram(s)
    ram = RAM(p.bytecode)
    ram.run([1, 2])
    assert ram.output_tape == [1]
    ram.run([2, 2])
    assert ram.output_tape == []


def test_compile_if_statement_x_gt_y():
    s = "begin read x; read y; if x > y then write 1 end"
    p = compile_to_ram(s)
    ram = RAM(p.bytecode)
    ram.run([2, 1])
    assert ram.output_tape == [1]
    ram.run([2, 2])
    assert ram.output_tape == []


def test_compile_if_statement_x_ge_y():
    s = "begin read x; read y; if x >= y then write 1 end"
    p = compile_to_ram(s)
    ram = RAM(p.bytecode)
    ram.run([2, 2])
    assert ram.output_tape == [1]
    ram.run([1, 2])
    assert ram.output_tape == []


def test_compile_if_statement_x_lt_literal_zero():
    s = "begin read x; if x < 0 then write 1 end"
    p = compile_to_ram(s)
    ram = RAM(p.bytecode)
    ram.run([0])
    assert ram.output_tape == []
    ram.run([-1])
    assert ram.output_tape == [1]


def test_compile_if_statement_implied_x_ne_zero():
    s = "begin read x; if x then write 1 end"
    p = compile_to_ram(s)
    ram = RAM(p.bytecode)
    ram.run([0])
    assert ram.output_tape == []
    ram.run([1])
    assert ram.output_tape == [1]


def test_compile_if_statement_with_else():
    s = "begin read x; if x < 0 then write 1 else write 0 end"
    p = compile_to_ram(s)
    ram = RAM(p.bytecode)
    ram.run([0])
    assert ram.output_tape == [0]
    ram.run([-1])
    assert ram.output_tape == [1]


def test_compile_while_statement():
    s = """
    begin
      read x;
      y <- 0;
      while x > 0 do
        begin
          x <- x - 1;
          y <- y + 1
      end;
      write y
    end
    """
    p = compile_to_ram(s)
    ram = RAM(p.bytecode)
    ram.run([0])
    assert ram.output_tape == [0]
    ram.run([2])
    assert ram.output_tape == [2]


def test_compile_assignment_statement():
    s = "begin x <- 5; write x end"
    p = compile_to_ram(s)
    ram = RAM(p.bytecode)
    ram.run()
    assert ram.output_tape == [5]


def test_compile_comparison_eq_expression():
    s = "begin read x; x <- x = 1; write x end"
    p = compile_to_ram(s)
    ram = RAM(p.bytecode)
    ram.run([1])
    assert ram.output_tape == [1]
    ram.run([2])
    assert ram.output_tape == [0]


def test_compile_comparison_ne_expression():
    s = "begin read x; x <- x != 1; write x end"
    p = compile_to_ram(s)
    ram = RAM(p.bytecode)
    ram.run([1])
    assert ram.output_tape == [0]
    ram.run([2])
    assert ram.output_tape == [1]


def test_compile_comparison_lt_expression():
    s = "begin read x; x <- x < 1; write x end"
    p = compile_to_ram(s)
    ram = RAM(p.bytecode)
    ram.run([1])
    assert ram.output_tape == [0]
    ram.run([0])
    assert ram.output_tape == [1]


def test_compile_comparison_le_expression():
    s = "begin read x; x <- x <= 1; write x end"
    p = compile_to_ram(s)
    ram = RAM(p.bytecode)
    ram.run([2])
    assert ram.output_tape == [0]
    ram.run([1])
    assert ram.output_tape == [1]


def test_compile_comparison_gt_expression():
    s = "begin read x; x <- x > 1; write x end"
    p = compile_to_ram(s)
    ram = RAM(p.bytecode)
    ram.run([1])
    assert ram.output_tape == [0]
    ram.run([2])
    assert ram.output_tape == [1]


def test_compile_comparison_ge_expression():
    s = "begin read x; x <- x >= 1; write x end"
    p = compile_to_ram(s)
    ram = RAM(p.bytecode)
    ram.run([0])
    assert ram.output_tape == [0]
    ram.run([1])
    assert ram.output_tape == [1]


def test_pidgin_algol_compile_to_ram_n_pow_n(n_pow_n: str):
    p = compile_to_ram(n_pow_n)
    r = RAM(p.bytecode, [2])
    r.run()
    assert r.output_tape[0] == 2**2


def test_pidgin_algol_compile_to_ram_equal_count(equal_count: str):
    p = compile_to_ram(equal_count)
    r = RAM(p.bytecode)
    r.run([])
    assert r.output_tape[0] == 1
    r.run([1, 2, 1, 1, 2, 1, 2, 2])
    assert r.output_tape[0] == 1
    r.run([1, 2, 1, 1, 2, 1, 2, 2, 2])
    assert not r.output_tape


def test_pidgin_algol_compile_to_ram_error():
    with pytest.raises(CompileError, match="divide by literal 0"):
        _ = compile_to_ram("begin read r1; r1 ← r1 / 0 end")
