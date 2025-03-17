from dataclasses import dataclass, field
from io import StringIO
from typing import TextIO

from daca.common import CompileError
from daca.ram import (
    Address,
    Instruction,
    JumpTarget,
    Opcode,
    Operand,
    OperandFlag,
    Program,
)

from .parser import (
    AST,
    AssignmentStatement,
    BinaryExpression,
    BinaryOperator,
    BlockStatement,
    Expression,
    IfStatement,
    LiteralExpression,
    Parser,
    ReadStatement,
    Statement,
    UnaryExpression,
    VariableExpression,
    WhileStatement,
    WriteStatement,
)


def is_comparison_operator(op: BinaryOperator) -> bool:
    return op in (
        BinaryOperator.equals,
        BinaryOperator.not_equals,
        BinaryOperator.lt,
        BinaryOperator.le,
        BinaryOperator.gt,
        BinaryOperator.ge,
    )


def is_arithmetic_operator(op: BinaryOperator) -> bool:
    return op in (
        BinaryOperator.plus,
        BinaryOperator.minus,
        BinaryOperator.mult,
        BinaryOperator.div,
    )


def is_zero(exp: Expression) -> bool:
    return isinstance(exp, LiteralExpression) and exp.value == 0


@dataclass
class RamCompiler:
    parser: Parser = field(default_factory=Parser)
    _var_map: dict[str, int] = field(init=False, default_factory=dict)
    _jumptable: dict[JumpTarget, int] = field(init=False, default_factory=dict)
    _reverse_jumptable: dict[int, JumpTarget] = field(init=False, default_factory=dict)
    _pc: int = 0
    _if_counter: int = 0
    _while_counter: int = 0
    _comp_counter: int = 0

    def compile(self, p: str | StringIO | TextIO | AST) -> Program:
        ast: AST = p if isinstance(p, AST) else self.parser.parse(p)
        self._var_map.clear()
        self._jumptable.clear()
        self._reverse_jumptable.clear()
        self._pc = 0
        instructions: list[Instruction] = self.compile_statement(ast.head)
        instructions.append(Instruction(opcode=Opcode.HALT))
        self._pc += 1
        return Program(instructions.copy(), self._jumptable.copy())

    def compile_statement(self, statement: Statement) -> list[Instruction]:
        if isinstance(statement, BlockStatement):
            insts = self.compile_block_statement(statement)
        elif isinstance(statement, ReadStatement):
            insts = [self.compile_read_statement(statement)]
            self._pc += 1
        elif isinstance(statement, WriteStatement):
            insts = [self.compile_write_statement(statement)]
            self._pc += 1
        elif isinstance(statement, IfStatement):
            insts = self.compile_if_statement(statement)
        elif isinstance(statement, WhileStatement):
            insts = self.compile_while_statement(statement)
        elif isinstance(statement, AssignmentStatement):
            insts = self.compile_assignment_statement(statement)
        else:
            raise CompileError(
                line=statement.line, column=statement.column, value=statement
            )
        return insts

    def compile_block_statement(self, block: BlockStatement) -> list[Instruction]:
        return [s for stmt in block.statements for s in self.compile_statement(stmt)]

    def compile_read_statement(self, s: ReadStatement) -> Instruction:
        if s.variable.name not in self._var_map:
            self._var_map[s.variable.name] = len(self._var_map) + 1
        register = self._var_map[s.variable.name]
        return Instruction(
            Opcode.READ, Operand(value=register, flag=OperandFlag.direct)
        )

    def compile_write_statement(self, s: WriteStatement) -> Instruction:
        if isinstance(s.value, LiteralExpression):
            return Instruction(
                Opcode.WRITE, Operand(value=s.value.value, flag=OperandFlag.literal)
            )
        elif isinstance(s.value, VariableExpression):
            if s.value.name not in self._var_map:
                self._var_map[s.value.name] = len(self._var_map) + 1
            register = self._var_map[s.value.name]
            return Instruction(
                Opcode.WRITE, Operand(value=register, flag=OperandFlag.direct)
            )
        else:
            raise CompileError(line=s.line, column=s.column, value=s.value)

    def compile_if_statement(self, s: IfStatement) -> list[Instruction]:
        self._if_counter += 1
        ic = self._if_counter

        # Build condition instructions list
        cond_insts = self.compile_expression(s.condition)
        # We'll need to add a jump to else or endif
        self._pc += 1

        # Build true body instructions list
        true_insts = self.compile_statement(s.true_body)

        # Build false (else) body instructions list
        else_insts = []

        if s.else_body:
            # If there's an else body, we'll need to add an unconditional jump
            # to true body instructions list
            self._pc += 1

            # Add jump to else body to condition instructions list
            jt = self._update_jumptable(f"else{ic}")
            cond_insts.append(Instruction(opcode=Opcode.JZERO, address=jt))

            # Build else body instructions list
            else_insts = self.compile_statement(s.else_body)

            # Add jump to end to true body instructions list
            jt = self._update_jumptable(f"endif{ic}")
            true_insts.append(Instruction(opcode=Opcode.JUMP, address=jt))

        else:
            # Add jump to end to condition instructions list
            jt = self._update_jumptable(f"endif{ic}")
            cond_insts.append(Instruction(opcode=Opcode.JZERO, address=jt))

        return cond_insts + true_insts + else_insts

    def compile_while_statement(self, s: WhileStatement) -> list[Instruction]:
        self._while_counter += 1
        wc = self._while_counter

        # Need a jump target at the beginning of the while to repeat
        while_target = self._update_jumptable(f"while{wc}")

        # Build condition instructions list
        cond_insts = self.compile_expression(s.condition)
        # We'll need to add a jump to end while
        self._pc += 1

        body_insts = self.compile_statement(s.body)
        # Add a jump to beginning of while
        body_insts.append(Instruction(opcode=Opcode.JUMP, address=while_target))
        self._pc += 1

        # Add jump to end to condition instructions list
        end_target = self._update_jumptable(f"endwhile{wc}")
        cond_insts.append(Instruction(opcode=Opcode.JZERO, address=end_target))

        return cond_insts + body_insts

    def compile_assignment_statement(self, s: AssignmentStatement) -> list[Instruction]:
        exp_insts = self.compile_expression(s.expression)
        if s.variable.name not in self._var_map:
            self._var_map[s.variable.name] = len(self._var_map) + 1
        register = self._var_map[s.variable.name]
        exp_insts.append(
            Instruction(
                opcode=Opcode.STORE,
                address=Operand(value=register, flag=OperandFlag.direct),
            )
        )
        self._pc += 1
        return exp_insts

    def compile_expression(self, exp: Expression) -> list[Instruction]:
        if isinstance(exp, UnaryExpression):
            insts = [self.compile_unary_expression(exp)]
            self._pc += 1
        elif isinstance(exp, BinaryExpression):
            insts = self.compile_binary_expression(exp)
        else:
            raise CompileError(line=exp.line, column=exp.column, value=exp)
        return insts

    def compile_unary_expression(self, exp: UnaryExpression) -> Instruction:
        if isinstance(exp, LiteralExpression):
            return self.compile_literal_expression(exp)
        elif isinstance(exp, VariableExpression):
            return self.compile_variable_expression(exp)
        else:
            raise CompileError(line=exp.line, column=exp.column, value=exp)

    def compile_literal_expression(self, exp: LiteralExpression) -> Instruction:
        return Instruction(
            opcode=Opcode.LOAD,
            address=Operand(value=exp.value, flag=OperandFlag.literal),
        )

    def compile_variable_expression(self, exp: VariableExpression) -> Instruction:
        if exp.name not in self._var_map:
            self._var_map[exp.name] = len(self._var_map) + 1
        register = self._var_map[exp.name]
        return Instruction(
            opcode=Opcode.LOAD,
            address=Operand(value=register, flag=OperandFlag.direct),
        )

    def compile_binary_expression(self, exp: BinaryExpression) -> list[Instruction]:
        insts: list[Instruction] = []

        # Small optimization if RHS is a simple literal or variable
        if isinstance(exp.right, LiteralExpression):
            address = Operand(value=exp.right.value, flag=OperandFlag.literal)
        elif isinstance(exp.right, VariableExpression):
            name = exp.right.name
            if name not in self._var_map:
                self._var_map[name] = len(self._var_map) + 1
            register = self._var_map[name]
            address = Operand(value=register, flag=OperandFlag.direct)
        else:
            # Calculate RHS
            insts.extend(self.compile_expression(exp.right))

            # Store the result temporarily
            register = len(self._var_map) + 1
            self._var_map[f"<<RESERVE REGISTER {register}"] = register
            address = Operand(value=register, flag=OperandFlag.direct)

            insts.append(Instruction(opcode=Opcode.STORE, address=address))
            self._pc += 1

        # Calculate LHS
        insts.extend(self.compile_expression(exp.left))

        # Apply binary operator
        op = exp.operator
        if is_comparison_operator(op):
            insts.extend(self._compile_comparison_expression(exp, address))
        elif is_arithmetic_operator(op):
            insts.extend(self._compile_arithmetic_expression(exp, address))
        else:
            raise CompileError(
                message=f"Invalid binary operator {op} for binary expression {exp}",
                line=exp.line,
                column=exp.column,
                value=op,
            )

        return insts

    def _compile_comparison_expression(
        self, exp: BinaryExpression, address: Address
    ) -> list[Instruction]:
        insts: list[Instruction] = []
        op = exp.operator
        is_zero_flag = is_zero(exp.right)
        neg_one = Operand(value=-1, flag=OperandFlag.literal)
        pos_one = Operand(value=1, flag=OperandFlag.literal)
        zero = Operand(value=0, flag=OperandFlag.literal)
        self._comp_counter += 1

        def add_instructions(
            with_mult: bool, jumper: Opcode, branch1_pos: bool
        ) -> None:
            self._pc += 3
            if not is_zero_flag:
                insts.append(Instruction(opcode=Opcode.SUB, address=address))
                self._pc += 1
            if with_mult:
                insts.append(Instruction(opcode=Opcode.MULT, address=neg_one))
                self._pc += 1

            lbl = "zero" if jumper == Opcode.JZERO else "gtz"
            jt = self._update_jumptable(f"{lbl}{self._comp_counter}")
            insts.append(Instruction(opcode=jumper, address=jt))
            write_val = pos_one if branch1_pos else zero
            insts.append(Instruction(opcode=Opcode.LOAD, address=write_val))
            self._pc += 1
            jt = self._update_jumptable(f"endcmp{self._comp_counter}")
            insts.append(Instruction(opcode=Opcode.JUMP, address=jt))
            write_val = zero if branch1_pos else pos_one
            insts.append(Instruction(opcode=Opcode.LOAD, address=write_val))

        if op == BinaryOperator.equals:
            add_instructions(with_mult=False, jumper=Opcode.JZERO, branch1_pos=False)
        elif op == BinaryOperator.not_equals:
            add_instructions(with_mult=False, jumper=Opcode.JZERO, branch1_pos=True)
        elif op == BinaryOperator.lt:
            add_instructions(with_mult=True, jumper=Opcode.JGTZ, branch1_pos=True)
        elif op == BinaryOperator.le:
            add_instructions(with_mult=False, jumper=Opcode.JGTZ, branch1_pos=True)
        elif op == BinaryOperator.gt:
            add_instructions(with_mult=False, jumper=Opcode.JGTZ, branch1_pos=False)
        elif op == BinaryOperator.ge:
            add_instructions(with_mult=True, jumper=Opcode.JGTZ, branch1_pos=False)
        else:
            raise CompileError(
                message=f"Invalid binary operator {op} for comparison expression {exp}",
                line=exp.line,
                column=exp.column,
                value=op,
            )

        return insts

    def _compile_arithmetic_expression(
        self, exp: BinaryExpression, address: Address
    ) -> list[Instruction]:
        insts: list[Instruction] = []
        op = exp.operator
        is_zero_flag = is_zero(exp.right)
        if op == BinaryOperator.plus:
            if not is_zero_flag:
                insts.append(Instruction(opcode=Opcode.ADD, address=address))
                self._pc += 1
        elif op == BinaryOperator.minus:
            if not is_zero_flag:
                insts.append(Instruction(opcode=Opcode.SUB, address=address))
                self._pc += 1
        elif op == BinaryOperator.mult:
            if is_zero_flag:
                insts.append(
                    Instruction(
                        opcode=Opcode.LOAD,
                        address=Operand(value=0, flag=OperandFlag.literal),
                    )
                )
            else:
                insts.append(Instruction(opcode=Opcode.MULT, address=address))
            self._pc += 1
        elif op == BinaryOperator.div:
            if is_zero_flag:
                raise CompileError(
                    message=f"Attempt to divide by literal 0 in {exp}",
                    line=exp.line,
                    column=exp.column,
                    value=address,
                )
            insts.append(Instruction(opcode=Opcode.DIV, address=address))
            self._pc += 1
        else:
            raise CompileError(
                message=f"Invalid binary operator {op} for arithmetic expression {exp}",
                line=exp.line,
                column=exp.column,
                value=op,
            )
        return insts

    def _update_jumptable(self, tgt: str) -> JumpTarget:
        try:
            return self._reverse_jumptable[self._pc]
        except KeyError:
            pass
        jt = JumpTarget(value=tgt)
        self._jumptable[jt] = self._pc
        self._reverse_jumptable[self._pc] = jt
        return jt


def compile_to_ram(program: str | StringIO | TextIO | AST) -> Program:
    return RamCompiler().compile(program)
