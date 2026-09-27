# Dining Philosophers — Virtual 8086 Project

A Microprocessors & Interfacing innovative assignment in which the **8086 Assembly program is the brain** and a Python GUI is only the visual/debugging layer.

## Architecture

```text
                    8086 ASSEMBLY
                         |
                         v
                 assembly_brain.asm
                         |
                  Virtual 8086 CPU
                         |
              +----------+----------+
              |                     |
          CPU Registers        Shared Memory
              |                     |
              +----------+----------+
                         |
                         v
                  Python GUI
                         |
             Dining Philosophers View
```

The Python program does NOT contain the Dining Philosophers algorithm. It loads and executes the assembly program instruction-by-instruction using a small educational 8086 subset emulator.

## Project structure

- `asm/assembly_brain.asm` — main 8086 assembly program.
- `simulator/cpu8086.py` — educational 8086 subset emulator.
- `simulator/assembler.py` — parser for the assembly subset.
- `simulator/model.py` — state model exposed by the CPU memory.
- `simulator/gui.py` — Tkinter visual interface.
- `simulator/main.py` — application entry point.
- `docs/PROJECT_NOTES.md` — explanation for viva/presentation.

## Requirements

- Python 3.10+
- Windows/Linux/macOS
- EMU8086 is optional, but recommended for demonstrating the assembly source separately.

No external Python packages are required.

## Run

From the project folder:

```bash
python -m simulator.main
```

or on Windows:

```bash
py -m simulator.main
```

## What the simulator demonstrates

1. Five philosophers.
2. Five shared forks.
3. THINKING / HUNGRY / WAITING / EATING states.
4. Deadlock-prone behavior.
5. Deadlock detection.
6. A deadlock-prevention mode based on asymmetric fork ordering.
7. CPU registers, instruction pointer, flags and memory.
8. Single-step execution.
9. Execution log.

## Important academic point

The Python GUI is presentation/debugging infrastructure. The resource-management decisions are encoded in `assembly_brain.asm`.

The emulator intentionally supports a small educational subset of 8086 instructions rather than pretending to be a complete commercial 8086 emulator.
