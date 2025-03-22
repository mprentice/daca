from dataclasses import dataclass, field, replace
from io import TextIOBase

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
    UnaryNegationExpression,
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


@dataclass(frozen=True)
class ConditionAction:
    with_mult: bool
    jump_to_body: bool
    jumper: Opcode


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
    _comp_action: dict[BinaryOperator, ConditionAction] = field(
        init=False, default_factory=dict
    )
    _pos_one: Operand = Operand(value=1, flag=OperandFlag.literal)
    _zero: Operand = Operand(value=0, flag=OperandFlag.literal)
    _mult_neg_one: Instruction = Instruction(
        opcode=Opcode.MULT, address=Operand(value=-1, flag=OperandFlag.literal)
    )

    def __post_init__(self):
        self._comp_action[BinaryOperator.equals] = ConditionAction(
            with_mult=False, jump_to_body=True, jumper=Opcode.JZERO
        )
        self._comp_action[BinaryOperator.not_equals] = ConditionAction(
            with_mult=False, jump_to_body=False, jumper=Opcode.JZERO
        )
        self._comp_action[BinaryOperator.lt] = ConditionAction(
            with_mult=True, jump_to_body=True, jumper=Opcode.JGTZ
        )
        self._comp_action[BinaryOperator.le] = ConditionAction(
            with_mult=False, jump_to_body=False, jumper=Opcode.JGTZ
        )
        self._comp_action[BinaryOperator.gt] = ConditionAction(
            with_mult=False, jump_to_body=True, jumper=Opcode.JGTZ
        )
        self._comp_action[BinaryOperator.ge] = ConditionAction(
            with_mult=True, jump_to_body=False, jumper=Opcode.JGTZ
        )

    def compile(self, p: str | TextIOBase | AST) -> Program:
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
            raise CompileError(value=statement)
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
            raise CompileError(value=s.value)

    def _assert_comparison(self, condition: Expression) -> BinaryExpression:
        if isinstance(condition, BinaryExpression):
            if is_comparison_operator(condition.operator):
                return condition
            else:
                raise CompileError(
                    message=f"operator must be a comparison in {condition}",
                    value=condition.operator,
                )
        else:
            raise CompileError(
                message=f"condition {condition} must be a BinaryExpression",
                value=condition,
            )

    def _build_condition_instructions(
        self, condition: Expression, body_label: str
    ) -> tuple[list[Instruction], ConditionAction]:
        # Build condition instructions list
        if isinstance(condition, BinaryExpression) and is_comparison_operator(
            condition.operator
        ):
            if is_zero(condition.right):
                cond_insts = self.compile_expression(condition.left)
            else:
                new_expr = replace(condition, operator=BinaryOperator.minus)
                cond_insts = self.compile_expression(new_expr)

            action: ConditionAction = self._comp_action[condition.operator]
        else:
            # If it's not a BinaryExpression with comparison operator, assume
            # an implied condition ≠ 0
            cond_insts = self.compile_expression(condition)
            action = self._comp_action[BinaryOperator.not_equals]

        if action.with_mult:
            cond_insts.append(self._mult_neg_one)
            self._pc += 1

        if action.jump_to_body:
            # Add 2 b/c we'll need to add a jump to else or endif later
            self._pc += 2
            jt = self._update_jumptable(body_label)
            cond_insts.append(Instruction(opcode=action.jumper, address=jt))
        else:
            # We'll need to add a jump to else or endif
            self._pc += 1

        return (cond_insts, action)

    def compile_if_statement(self, s: IfStatement) -> list[Instruction]:
        self._if_counter += 1
        ic = self._if_counter

        cond_insts, action = self._build_condition_instructions(s.condition, f"if{ic}")

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
            if action.jump_to_body:
                # jumper jumped to body, so false needs to jump to else
                cond_insts.append(Instruction(opcode=Opcode.JUMP, address=jt))
            else:
                # jumper needs to jump to else
                cond_insts.append(Instruction(opcode=action.jumper, address=jt))

            # Build else body instructions list
            else_insts = self.compile_statement(s.else_body)

            # Add jump to end to true body instructions list
            jt = self._update_jumptable(f"endif{ic}")
            true_insts.append(Instruction(opcode=Opcode.JUMP, address=jt))

        else:
            # Add jump to end to condition instructions list
            jt = self._update_jumptable(f"endif{ic}")
            if action.jump_to_body:
                # jumper jumped to body, so false needs to jump to end
                cond_insts.append(Instruction(opcode=Opcode.JUMP, address=jt))
            else:
                # jumper needs to jump to end
                cond_insts.append(Instruction(opcode=action.jumper, address=jt))

        return cond_insts + true_insts + else_insts

    def compile_while_statement(self, s: WhileStatement) -> list[Instruction]:
        self._while_counter += 1
        wc = self._while_counter

        # Need a jump target at the beginning of the while to repeat
        while_target = self._update_jumptable(f"while{wc}")

        cond_insts, action = self._build_condition_instructions(
            s.condition, f"continue{wc}"
        )

        body_insts = self.compile_statement(s.body)

        # Add a jump to beginning of while
        body_insts.append(Instruction(opcode=Opcode.JUMP, address=while_target))
        self._pc += 1

        # Add jump to end to condition instructions list
        end_target = self._update_jumptable(f"endwhile{wc}")
        if action.jump_to_body:
            # jumper jumped to body, so false needs to jump to end while
            cond_insts.append(Instruction(opcode=Opcode.JUMP, address=end_target))
        else:
            # jumper needs to jump to end while
            cond_insts.append(Instruction(opcode=action.jumper, address=end_target))

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
            insts = self.compile_unary_expression(exp)
        elif isinstance(exp, BinaryExpression):
            insts = self.compile_binary_expression(exp)
        else:
            raise CompileError(value=exp)
        return insts

    def compile_unary_expression(self, exp: UnaryExpression) -> list[Instruction]:
        if isinstance(exp, LiteralExpression):
            return self.compile_literal_expression(exp)
        elif isinstance(exp, VariableExpression):
            return self.compile_variable_expression(exp)
        elif isinstance(exp, UnaryNegationExpression):
            return self.compile_unary_negation_expression(exp)
        else:
            raise CompileError(value=exp)

    def compile_literal_expression(self, exp: LiteralExpression) -> list[Instruction]:
        self._pc += 1
        return [
            Instruction(
                opcode=Opcode.LOAD,
                address=Operand(value=exp.value, flag=OperandFlag.literal),
            )
        ]

    def compile_variable_expression(self, exp: VariableExpression) -> list[Instruction]:
        if exp.name not in self._var_map:
            self._var_map[exp.name] = len(self._var_map) + 1
        register = self._var_map[exp.name]
        self._pc += 1
        return [
            Instruction(
                opcode=Opcode.LOAD,
                address=Operand(value=register, flag=OperandFlag.direct),
            )
        ]

    def compile_unary_negation_expression(
        self, exp: UnaryNegationExpression
    ) -> list[Instruction]:
        if isinstance(exp.exp, LiteralExpression):
            self._pc += 1
            return [
                Instruction(
                    opcode=Opcode.LOAD,
                    address=Operand(value=-exp.exp.value, flag=OperandFlag.literal),
                )
            ]
        insts = self.compile_expression(exp.exp)
        insts.append(self._mult_neg_one)
        self._pc += 1
        return insts

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
                value=op,
            )

        return insts

    def _compile_comparison_expression(
        self, exp: BinaryExpression, address: Address
    ) -> list[Instruction]:
        insts: list[Instruction] = []
        self._comp_counter += 1
        cc = self._comp_counter

        if not is_zero(exp.right):
            insts.append(Instruction(opcode=Opcode.SUB, address=address))
            self._pc += 1

        action: ConditionAction = self._comp_action[exp.operator]

        if action.with_mult:
            insts.append(self._mult_neg_one)
            self._pc += 1

        load_1 = self._zero if action.jump_to_body else self._pos_one
        load_2 = self._pos_one if action.jump_to_body else self._zero

        self._pc += 3
        jt = self._update_jumptable(f"cmp{cc}")

        insts.append(Instruction(opcode=action.jumper, address=jt))
        insts.append(Instruction(opcode=Opcode.LOAD, address=load_1))

        self._pc += 1
        jt = self._update_jumptable(f"endcmp{cc}")

        insts.append(Instruction(opcode=Opcode.JUMP, address=jt))
        insts.append(Instruction(opcode=Opcode.LOAD, address=load_2))

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
                    value=address,
                )
            insts.append(Instruction(opcode=Opcode.DIV, address=address))
            self._pc += 1
        else:
            raise CompileError(
                message=f"Invalid binary operator {op} for arithmetic expression {exp}",
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


def compile_to_ram(program: str | TextIOBase | AST) -> Program:
    return RamCompiler().compile(program)
