from dataclasses import dataclass, field
from io import StringIO
from typing import TextIO

from daca.common import CompileError
from daca.ram import Instruction, JumpTarget, Opcode, Operand, OperandFlag, Program

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
        # Calculate RHS
        insts = self.compile_expression(exp.right)

        # Store the result temporarily
        register = len(self._var_map) + 1
        self._var_map[f"<<RESERVE REGISTER {register}"] = register
        insts.append(
            Instruction(
                opcode=Opcode.STORE,
                address=Operand(value=register, flag=OperandFlag.direct),
            )
        )
        self._pc += 1

        # Calculate LHS
        insts.extend(self.compile_expression(exp.left))

        # Apply binary operator
        op = exp.operator
        if op == BinaryOperator.equals:
            self._comp_counter += 1
            insts.append(
                Instruction(
                    opcode=Opcode.SUB,
                    address=Operand(value=register, flag=OperandFlag.direct),
                )
            )
            self._pc += 4
            jt = self._update_jumptable(f"zero{self._comp_counter}")
            insts.append(Instruction(opcode=Opcode.JZERO, address=jt))
            insts.append(
                Instruction(
                    opcode=Opcode.LOAD,
                    address=Operand(value=0, flag=OperandFlag.literal),
                )
            )
            self._pc += 1
            jt = self._update_jumptable(f"endcmp{self._comp_counter}")
            insts.append(Instruction(opcode=Opcode.JUMP, address=jt))
            insts.append(
                Instruction(
                    opcode=Opcode.LOAD,
                    address=Operand(value=1, flag=OperandFlag.literal),
                )
            )
        elif op == BinaryOperator.not_equals:
            self._comp_counter += 1
            insts.append(
                Instruction(
                    opcode=Opcode.SUB,
                    address=Operand(value=register, flag=OperandFlag.direct),
                )
            )
            self._pc += 4
            jt = self._update_jumptable(f"zero{self._comp_counter}")
            insts.append(Instruction(opcode=Opcode.JZERO, address=jt))
            insts.append(
                Instruction(
                    opcode=Opcode.LOAD,
                    address=Operand(value=1, flag=OperandFlag.literal),
                )
            )
            self._pc += 1
            jt = self._update_jumptable(f"endcmp{self._comp_counter}")
            insts.append(Instruction(opcode=Opcode.JUMP, address=jt))
            insts.append(
                Instruction(
                    opcode=Opcode.LOAD,
                    address=Operand(value=0, flag=OperandFlag.literal),
                )
            )
        elif op == BinaryOperator.lt:
            self._comp_counter += 1
            insts.append(
                Instruction(
                    opcode=Opcode.SUB,
                    address=Operand(value=register, flag=OperandFlag.direct),
                )
            )
            insts.append(
                Instruction(
                    opcode=Opcode.MULT,
                    address=Operand(value=-1, flag=OperandFlag.literal),
                )
            )
            self._pc += 5
            jt = self._update_jumptable(f"gtz{self._comp_counter}")
            insts.append(Instruction(opcode=Opcode.JGTZ, address=jt))
            insts.append(
                Instruction(
                    opcode=Opcode.LOAD,
                    address=Operand(value=1, flag=OperandFlag.literal),
                )
            )
            self._pc += 1
            jt = self._update_jumptable(f"endcmp{self._comp_counter}")
            insts.append(Instruction(opcode=Opcode.JUMP, address=jt))
            insts.append(
                Instruction(
                    opcode=Opcode.LOAD,
                    address=Operand(value=0, flag=OperandFlag.literal),
                )
            )
        elif op == BinaryOperator.le:
            self._comp_counter += 1
            insts.append(
                Instruction(
                    opcode=Opcode.SUB,
                    address=Operand(value=register, flag=OperandFlag.direct),
                )
            )
            self._pc += 4
            jt = self._update_jumptable(f"gtz{self._comp_counter}")
            insts.append(Instruction(opcode=Opcode.JGTZ, address=jt))
            insts.append(
                Instruction(
                    opcode=Opcode.LOAD,
                    address=Operand(value=1, flag=OperandFlag.literal),
                )
            )
            self._pc += 1
            jt = self._update_jumptable(f"endcmp{self._comp_counter}")
            insts.append(Instruction(opcode=Opcode.JUMP, address=jt))
            insts.append(
                Instruction(
                    opcode=Opcode.LOAD,
                    address=Operand(value=0, flag=OperandFlag.literal),
                )
            )
        elif op == BinaryOperator.gt:
            self._comp_counter += 1
            insts.append(
                Instruction(
                    opcode=Opcode.SUB,
                    address=Operand(value=register, flag=OperandFlag.direct),
                )
            )
            self._pc += 4
            jt = self._update_jumptable(f"gtz{self._comp_counter}")
            insts.append(Instruction(opcode=Opcode.JGTZ, address=jt))
            insts.append(
                Instruction(
                    opcode=Opcode.LOAD,
                    address=Operand(value=0, flag=OperandFlag.literal),
                )
            )
            self._pc += 1
            jt = self._update_jumptable(f"endcmp{self._comp_counter}")
            insts.append(Instruction(opcode=Opcode.JUMP, address=jt))
            insts.append(
                Instruction(
                    opcode=Opcode.LOAD,
                    address=Operand(value=1, flag=OperandFlag.literal),
                )
            )
        elif op == BinaryOperator.ge:
            self._comp_counter += 1
            insts.append(
                Instruction(
                    opcode=Opcode.SUB,
                    address=Operand(value=register, flag=OperandFlag.direct),
                )
            )
            insts.append(
                Instruction(
                    opcode=Opcode.MULT,
                    address=Operand(value=-1, flag=OperandFlag.literal),
                )
            )
            self._pc += 5
            jt = self._update_jumptable(f"gtz{self._comp_counter}")
            insts.append(Instruction(opcode=Opcode.JGTZ, address=jt))
            insts.append(
                Instruction(
                    opcode=Opcode.LOAD,
                    address=Operand(value=0, flag=OperandFlag.literal),
                )
            )
            self._pc += 1
            jt = self._update_jumptable(f"endcmp{self._comp_counter}")
            insts.append(Instruction(opcode=Opcode.JUMP, address=jt))
            insts.append(
                Instruction(
                    opcode=Opcode.LOAD,
                    address=Operand(value=1, flag=OperandFlag.literal),
                )
            )
        elif op == BinaryOperator.plus:
            insts.append(
                Instruction(
                    opcode=Opcode.ADD,
                    address=Operand(value=register, flag=OperandFlag.direct),
                )
            )
            self._pc += 1
        elif op == BinaryOperator.minus:
            insts.append(
                Instruction(
                    opcode=Opcode.SUB,
                    address=Operand(value=register, flag=OperandFlag.direct),
                )
            )
            self._pc += 1
        elif op == BinaryOperator.mult:
            insts.append(
                Instruction(
                    opcode=Opcode.MULT,
                    address=Operand(value=register, flag=OperandFlag.direct),
                )
            )
            self._pc += 1
        elif op == BinaryOperator.div:
            insts.append(
                Instruction(
                    opcode=Opcode.DIV,
                    address=Operand(value=register, flag=OperandFlag.direct),
                )
            )
            self._pc += 1
        else:
            raise CompileError(
                message=f"Invalid binary operator {op} for binary expression {exp}",
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
