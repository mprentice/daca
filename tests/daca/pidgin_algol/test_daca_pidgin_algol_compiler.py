import pytest

from daca.common import CompileError
from daca.pidgin_algol.compiler import RamCompiler, compile_to_ram
from daca.ram import RAM


@pytest.fixture
def compiler() -> RamCompiler:
    return RamCompiler()


def test_compile_block_statement(compiler):
    s = "begin read x; write x end"
    p = compiler.compile(s)
    ram = RAM(p)
    ram.run([777])
    assert ram.output_tape == [777]
    s = "begin read x; write x; end"
    p = compiler.compile(s)
    ram = RAM(p)
    ram.run([778])
    assert ram.output_tape == [778]


def test_compile_read_statement_write_statement_variable(compiler):
    s = "begin read x; write x; end"
    p = compiler.compile(s)
    ram = RAM(p)
    ram.run([777])
    assert ram.output_tape == [777]


def test_compile_write_statement_literal(compiler):
    s = "write 997"
    p = compiler.compile(s)
    ram = RAM(p)
    ram.run()
    assert ram.output_tape == [997]


def test_compile_if_statement_x_lt_y(compiler):
    s = "begin read x; read y; if x < y then write 1 end"
    p = compiler.compile(s)
    ram = RAM(p)
    ram.run([1, 2])
    assert ram.output_tape == [1]
    ram.run([2, 2])
    assert ram.output_tape == []


def test_compile_if_statement_x_le_y(compiler):
    s = "begin read x; read y; if x <= y then write 1 end"
    p = compiler.compile(s)
    ram = RAM(p)
    ram.run([2, 2])
    assert ram.output_tape == [1]
    ram.run([3, 2])
    assert ram.output_tape == []


def test_compile_if_statement_x_eq_y(compiler):
    s = "begin read x; read y; if x = y then write 1 end"
    p = compiler.compile(s)
    ram = RAM(p)
    ram.run([2, 2])
    assert ram.output_tape == [1]
    ram.run([1, 2])
    assert ram.output_tape == []


def test_compile_if_statement_x_ne_y(compiler):
    s = "begin read x; read y; if x != y then write 1 end"
    p = compiler.compile(s)
    ram = RAM(p)
    ram.run([1, 2])
    assert ram.output_tape == [1]
    ram.run([2, 2])
    assert ram.output_tape == []


def test_compile_if_statement_x_gt_y(compiler):
    s = "begin read x; read y; if x > y then write 1 end"
    p = compiler.compile(s)
    ram = RAM(p)
    ram.run([2, 1])
    assert ram.output_tape == [1]
    ram.run([2, 2])
    assert ram.output_tape == []


def test_compile_if_statement_x_ge_y(compiler):
    s = "begin read x; read y; if x >= y then write 1 end"
    p = compiler.compile(s)
    ram = RAM(p)
    ram.run([2, 2])
    assert ram.output_tape == [1]
    ram.run([1, 2])
    assert ram.output_tape == []


def test_compile_if_statement_x_lt_literal_zero(compiler):
    s = "begin read x; if x < 0 then write 1 end"
    p = compiler.compile(s)
    ram = RAM(p)
    ram.run([0])
    assert ram.output_tape == []
    ram.run([-1])
    assert ram.output_tape == [1]


def test_compile_if_statement_implied_x_ne_zero(compiler):
    s = "begin read x; if x then write 1 end"
    p = compiler.compile(s)
    ram = RAM(p)
    ram.run([0])
    assert ram.output_tape == []
    ram.run([1])
    assert ram.output_tape == [1]


def test_compile_if_statement_with_else(compiler):
    s = "begin read x; if x < 0 then write 1 else write 0 end"
    p = compiler.compile(s)
    ram = RAM(p)
    ram.run([0])
    assert ram.output_tape == [0]
    ram.run([-1])
    assert ram.output_tape == [1]


def test_compile_while_statement(compiler):
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
    p = compiler.compile(s)
    ram = RAM(p)
    ram.run([0])
    assert ram.output_tape == [0]
    ram.run([2])
    assert ram.output_tape == [2]


def test_compile_assignment_statement(compiler):
    s = "begin x <- 5; write x end"
    p = compiler.compile(s)
    ram = RAM(p)
    ram.run()
    assert ram.output_tape == [5]


def test_compile_comparison_eq_expression(compiler):
    s = "begin read x; x <- x = 1; write x end"
    p = compiler.compile(s)
    ram = RAM(p)
    ram.run([1])
    assert ram.output_tape == [1]
    ram.run([2])
    assert ram.output_tape == [0]


def test_compile_comparison_ne_expression(compiler):
    s = "begin read x; x <- x != 1; write x end"
    p = compiler.compile(s)
    ram = RAM(p)
    ram.run([1])
    assert ram.output_tape == [0]
    ram.run([2])
    assert ram.output_tape == [1]


def test_compile_comparison_lt_expression(compiler):
    s = "begin read x; x <- x < 1; write x end"
    p = compiler.compile(s)
    ram = RAM(p)
    ram.run([1])
    assert ram.output_tape == [0]
    ram.run([0])
    assert ram.output_tape == [1]


def test_compile_comparison_le_expression(compiler):
    s = "begin read x; x <- x <= 1; write x end"
    p = compiler.compile(s)
    ram = RAM(p)
    ram.run([2])
    assert ram.output_tape == [0]
    ram.run([1])
    assert ram.output_tape == [1]


def test_compile_comparison_gt_expression(compiler):
    s = "begin read x; x <- x > 1; write x end"
    p = compiler.compile(s)
    ram = RAM(p)
    ram.run([1])
    assert ram.output_tape == [0]
    ram.run([2])
    assert ram.output_tape == [1]


def test_compile_comparison_ge_expression(compiler):
    s = "begin read x; x <- x >= 1; write x end"
    p = compiler.compile(s)
    ram = RAM(p)
    ram.run([0])
    assert ram.output_tape == [0]
    ram.run([1])
    assert ram.output_tape == [1]


def test_pidgin_algol_compile_to_ram_n_pow_n(n_pow_n: str):
    p = compile_to_ram(n_pow_n)
    r = RAM(p, [2])
    r.run()
    assert r.output_tape[0] == 2**2


def test_pidgin_algol_compile_to_ram_equal_count(equal_count: str):
    p = compile_to_ram(equal_count)
    r = RAM(p)
    r.run([])
    assert r.output_tape[0] == 1
    r.run([1, 2, 1, 1, 2, 1, 2, 2])
    assert r.output_tape[0] == 1
    r.run([1, 2, 1, 1, 2, 1, 2, 2, 2])
    assert not r.output_tape


def test_pidgin_algol_compile_to_ram_error():
    with pytest.raises(CompileError, match="divide by literal 0"):
        _ = compile_to_ram("begin read r1; r1 ← r1 / 0 end")
