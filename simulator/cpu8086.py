from dataclasses import dataclass, field
from .assembler import Program, parse_number

REGS = ("AX", "BX", "CX", "DX", "SI", "DI", "BP", "SP", "IP")

@dataclass
class CPU8086:
    program: Program
    regs: dict = field(default_factory=dict)
    flags: dict = field(default_factory=dict)
    memory: dict = field(default_factory=dict)
    halted: bool = False
    last_instruction: str = ""
    last_event: str = ""
    executed: int = 0

    def __post_init__(self):
        self.regs = {r: 0 for r in REGS}
        self.flags = {"ZF": 0, "CF": 0, "SF": 0, "OF": 0}
        self.memory = {k: v for k, v in self.program.variables.items()}
        self.regs["IP"] = self.program.labels.get("START", 0)

    def reset(self):
        self.regs = {r: 0 for r in REGS}
        self.flags = {"ZF": 0, "CF": 0, "SF": 0, "OF": 0}
        self.memory = {k: v for k, v in self.program.variables.items()}
        self.halted = False
        self.last_instruction = ""
        self.last_event = "CPU reset"
        self.executed = 0
        self.regs["IP"] = self.program.labels.get("START", 0)

    def _value(self, token):
        token = token.upper()
        if token in self.regs:
            return self.regs[token]
        if token in self.memory:
            return self.memory[token]
        return parse_number(token)

    def _set(self, token, value):
        token = token.upper()
        value &= 0xFFFF
        if token in self.regs:
            self.regs[token] = value
        elif token in self.memory:
            self.memory[token] = value & 0xFF
        else:
            raise ValueError(f"Unknown destination: {token}")

    def _set_flags(self, result):
        result &= 0xFFFF
        self.flags["ZF"] = int(result == 0)
        self.flags["SF"] = int(bool(result & 0x8000))

    def step(self):
        if self.halted:
            return

        ip = self.regs["IP"]
        if ip < 0 or ip >= len(self.program.instructions):
            self.halted = True
            self.last_event = "IP outside program"
            return

        ins = self.program.instructions[ip]
        self.last_instruction = ins.source
        self.last_event = ""
        next_ip = ip + 1
        op = ins.op
        a = ins.args

        if op == "MOV":
            self._set(a[0], self._value(a[1]))

        elif op == "INC":
            v = (self._value(a[0]) + 1) & 0xFFFF
            self._set(a[0], v)
            self._set_flags(v)

        elif op == "DEC":
            v = (self._value(a[0]) - 1) & 0xFFFF
            self._set(a[0], v)
            self._set_flags(v)

        elif op == "ADD":
            v = self._value(a[0]) + self._value(a[1])
            self._set(a[0], v)
            self._set_flags(v)

        elif op == "SUB":
            v = self._value(a[0]) - self._value(a[1])
            self._set(a[0], v)
            self._set_flags(v)

        elif op == "CMP":
            result = (self._value(a[0]) - self._value(a[1])) & 0xFFFF
            self._set_flags(result)

        elif op == "JMP":
            next_ip = self.program.labels[a[0]]

        elif op == "JE" or op == "JZ":
            if self.flags["ZF"]:
                next_ip = self.program.labels[a[0]]

        elif op == "JNE" or op == "JNZ":
            if not self.flags["ZF"]:
                next_ip = self.program.labels[a[0]]

        elif op == "NOP":
            pass

        elif op == "HLT":
            self.halted = True

        else:
            raise ValueError(f"Unsupported opcode '{op}' at assembly line {ins.line_no}")

        self.regs["IP"] = next_ip
        self.executed += 1

        # Human-readable event extraction from writes.
        if op == "MOV" and len(a) == 2 and a[0] in self.memory:
            self.last_event = f"{a[0]} <- {self.memory[a[0]]}"
        elif op in ("INC", "DEC") and len(a) >= 1 and a[0] in self.memory:
            self.last_event = f"{a[0]} <- {self.memory[a[0]]}"

    def run(self, max_steps=1000):
        for _ in range(max_steps):
            if self.halted:
                break
            self.step()
