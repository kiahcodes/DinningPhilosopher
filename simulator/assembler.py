from dataclasses import dataclass
import re

@dataclass
class Instruction:
    op: str
    args: list[str]
    source: str
    line_no: int

class Program:
    def __init__(self, instructions, labels, variables):
        self.instructions = instructions
        self.labels = labels
        self.variables = variables

def strip_comment(line: str) -> str:
    # The project uses ';' for assembly comments.
    return line.split(";", 1)[0].strip()

def parse_number(token: str) -> int:
    token = token.strip().upper()
    if token.endswith("H"):
        return int(token[:-1], 16)
    if token.endswith("B"):
        return int(token[:-1], 2)
    if token.endswith("D"):
        return int(token[:-1], 10)
    return int(token, 10)

def assemble(text: str) -> Program:
    variables = {}
    labels = {}
    instructions = []

    # First pass: collect variables and instruction addresses.
    instruction_index = 0
    for raw in text.splitlines():
        line = strip_comment(raw)
        if not line:
            continue

        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s+DB\s+(.+)$", line, re.I)
        if m:
            variables[m.group(1).upper()] = parse_number(m.group(2)) & 0xFF
            continue

        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):$", line)
        if m:
            labels[m.group(1).upper()] = instruction_index
            continue

        upper = line.upper()
        if upper.startswith((".MODEL", ".STACK", ".DATA", ".CODE", "END")):
            continue

        instruction_index += 1

    # Second pass: create executable instructions.
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = strip_comment(raw)
        if not line:
            continue
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*\s+DB\s+.+$", line, re.I):
            continue
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*:$", line):
            continue
        if line.upper().startswith((".MODEL", ".STACK", ".DATA", ".CODE", "END")):
            continue

        parts = re.split(r"\s+", line, maxsplit=1)
        op = parts[0].upper()
        arg_text = parts[1] if len(parts) == 2 else ""
        args = [a.strip().upper() for a in arg_text.split(",")] if arg_text else []
        instructions.append(Instruction(op, args, line, lineno))

    return Program(instructions, labels, variables)
