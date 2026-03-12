import argparse
import importlib.resources
from contextlib import closing
from typing import Optional

import daca.ram as ram
import daca.rasp as rasp


def ram_to_rasp(p: ram.Program) -> rasp.Program:
    instructions: list[rasp.Instruction] = []
    pc: int = 0
    new_pcs: list[int] = []
    for i in p.instructions:
        new_pcs.append(pc)
        if (
            isinstance(i.address, ram.Operand)
            and i.address.optype == ram.OperandType.INDIRECT
        ):
            pc += 6
        else:
            pc += 1
    indirect_register = pc * 2
    register_offset = indirect_register + 1
    for pc, inst in enumerate(p.instructions):
        if inst.opcode == ram.Opcode.HALT:
            instructions.append(rasp.Instruction(opcode=rasp.Opcode.HALT))
        elif inst.opcode in (ram.Opcode.JUMP, ram.Opcode.JGTZ, ram.Opcode.JZERO):
            assert isinstance(inst.address, str)
            b: str = inst.address
            dst: int = p.jumptable[b]
            new_dst: int = new_pcs[dst] * 2 + 1
            opcode = rasp.Opcode[inst.opcode.name]
            instructions.append(rasp.Instruction(opcode=opcode, address=new_dst))
        elif (
            isinstance(inst.address, ram.Operand)
            and inst.address.optype == ram.OperandType.DIRECT
        ):
            opcode = rasp.Opcode[inst.opcode.name]
            new_reg = inst.address.value + register_offset
            instructions.append(rasp.Instruction(opcode=opcode, address=new_reg))
        elif (
            isinstance(inst.address, ram.Operand)
            and inst.address.optype == ram.OperandType.INDIRECT
        ):
            instructions.append(
                rasp.Instruction(opcode=rasp.Opcode.STORE, address=indirect_register)
            )
            instructions.append(
                rasp.Instruction(
                    opcode=rasp.Opcode.LOAD,
                    address=inst.address.value + register_offset,
                )
            )
            instructions.append(
                rasp.Instruction(
                    opcode=rasp.Opcode.ADD_LITERAL, address=register_offset
                )
            )
            storage_register: int = new_pcs[pc] * 2 + 1 + 11
            instructions.append(
                rasp.Instruction(opcode=rasp.Opcode.STORE, address=storage_register)
            )
            instructions.append(
                rasp.Instruction(opcode=rasp.Opcode.LOAD, address=indirect_register)
            )
            instructions.append(
                rasp.Instruction(
                    opcode=rasp.Opcode[inst.opcode.name], address=storage_register
                )
            )
        else:
            assert isinstance(inst.address, ram.Operand)
            assert inst.address.optype == ram.OperandType.LITERAL
            opcode = rasp.Opcode[f"{inst.opcode.name}_LITERAL"]
            instructions.append(
                rasp.Instruction(opcode=opcode, address=inst.address.value)
            )
    return rasp.Program(instructions=instructions)


def rasp_to_ram(p: rasp.Program) -> ram.Program:
    ramp = ram.parse(importlib.resources.read_text("examples", "ch1/emulate_rasp.ram"))
    rasp_lc = ramp.jumptable["loadrasp"]
    simulator = list(ramp.instructions[0:rasp_lc])
    rasp_loader: list[ram.Instruction] = []
    for pc, inst in enumerate(p.instructions):
        rasp_loader.append(
            ram.Instruction(
                opcode=ram.Opcode.LOAD,
                address=ram.Operand(
                    value=inst.opcode.value, optype=ram.OperandType.LITERAL
                ),
            )
        )
        rasp_loader.append(
            ram.Instruction(
                opcode=ram.Opcode.STORE,
                address=ram.Operand(value=pc * 2 + 4, optype=ram.OperandType.DIRECT),
            )
        )
        rasp_loader.append(
            ram.Instruction(
                opcode=ram.Opcode.LOAD,
                address=ram.Operand(value=inst.address, optype=ram.OperandType.LITERAL),
            )
        )
        rasp_loader.append(
            ram.Instruction(
                opcode=ram.Opcode.STORE,
                address=ram.Operand(value=pc * 2 + 5, optype=ram.OperandType.DIRECT),
            )
        )

    rasp_loader.append(ram.Instruction(opcode=ram.Opcode.JUMP, address="startrasp"))
    new_jumptable = dict(ramp.jumptable)
    del new_jumptable["readrasp"]
    return ram.Program(
        instructions=tuple(simulator + rasp_loader), jumptable=new_jumptable
    )


def main(argv: Optional[list[str]] = None) -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--from", choices=["ram", "rasp"])
    p.add_argument("--to", choices=["ram", "rasp"])
    p.add_argument("program", type=argparse.FileType("r"))
    args = p.parse_args() if argv is None else p.parse_args(argv)
    with closing(args.program):
        s = args.program.read()
    if getattr(args, "from") == "ram" and args.to == "rasp":
        ram_ast = ram.parse(s)
        rasp_ast = ram_to_rasp(ram_ast)
        print(f"{rasp_ast}")
    elif getattr(args, "from") == "rasp" and args.to == "ram":
        rasp_ast = rasp.parse(s)
        ram_ast = rasp_to_ram(rasp_ast)
        print(f"{ram_ast}")


if __name__ == "__main__":
    main()
