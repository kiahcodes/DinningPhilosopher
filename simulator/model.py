PHIL_NAMES = ["P1", "P2", "P3", "P4", "P5"]
FORK_NAMES = ["F1", "F2", "F3", "F4", "F5"]

STATE_NAMES = {
    0: "THINKING",
    1: "HUNGRY",
    2: "EATING",
    3: "WAITING",
}

def snapshot(cpu):
    return {
        "philosophers": [cpu.memory.get(f"PHIL{i}", 0) for i in range(1, 6)],
        "forks": [cpu.memory.get(f"FORK{i}", 0) for i in range(1, 6)],
        "current": cpu.memory.get("CURRENT", 0),
        "mode": cpu.memory.get("MODE", 0),
        "tick": cpu.memory.get("TICK", 0),
        "deadlock": cpu.memory.get("DEADLOCK", 0),
        "registers": dict(cpu.regs),
        "flags": dict(cpu.flags),
        "ip": cpu.regs["IP"],
        "instruction": cpu.last_instruction,
        "event": cpu.last_event,
        "executed": cpu.executed,
    }


def explain_event(cpu):
    """Translate the CPU's last action into a plain-English sentence.

    Aimed at someone with zero background in assembly or the Dining
    Philosophers problem: no register names, no hex, no jargon.
    """
    instr = (cpu.last_instruction or "").strip()
    event = (cpu.last_event or "").strip()
    op = instr.split()[0].upper() if instr else ""

    if not event:
        if op == "NOP":
            return "The CPU pauses for a beat — this stands in for a philosopher spending time eating or thinking."
        if op in ("JMP", "JE", "JZ", "JNE", "JNZ"):
            return "The CPU jumps to the next stage of the program to continue the simulation."
        if op == "HLT":
            return "The program has finished running (CPU halted)."
        if op in ("MOV", "INC", "DEC", "ADD", "SUB", "CMP"):
            return "The CPU does some internal bookkeeping (updating a counter or register)."
        if instr:
            return "Running the next instruction..."
        return "Ready. Press Start, Step, or pick a mode below to begin."

    var, _, raw_val = event.partition("<-")
    var = var.strip().upper()
    try:
        val = int(raw_val.strip())
    except ValueError:
        val = None

    if var.startswith("PHIL") and var[4:].isdigit():
        name = f"Philosopher {var[4:]}"
        meaning = {
            0: f"{name} goes back to THINKING — done eating, doesn't need a fork right now.",
            1: f"{name} gets HUNGRY and wants to eat.",
            2: f"{name} picks up both forks and starts EATING. 🍽",
            3: f"{name} is stuck WAITING — it has one fork but needs a second one.",
        }
        return meaning.get(val, f"{name}'s status changes.")

    if var.startswith("FORK") and var[4:].isdigit():
        name = f"Fork {var[4:]}"
        if val:
            return f"{name} is picked up — it becomes LOCKED (in use)."
        return f"{name} is set back down — it becomes FREE for someone else to use."

    if var == "DEADLOCK":
        if val:
            return ("🔴 DEADLOCK! Every philosopher is holding one fork and waiting on a "
                    "neighbor who will never let go. Nobody can eat — the system is stuck.")
        return "No deadlock — the table is running smoothly."

    if var == "MODE":
        if val:
            return "🛡 Switching to SAFE MODE — forks are handed out in an order that prevents circular waiting."
        return "⚠ Switching to DEADLOCK MODE — every philosopher will grab their left fork first."

    if var == "CURRENT":
        return f"The CPU is now looking at Philosopher {val + 1}."

    if var == "TICK":
        return "One CPU clock cycle passes."

    return f"{var} changes to {val}."
