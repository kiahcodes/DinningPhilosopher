from pathlib import Path
import tkinter as tk

from .assembler import assemble
from .cpu8086 import CPU8086
from .gui import DiningGUI

ROOT = Path(__file__).resolve().parents[1]
ASM_FILE = ROOT / "asm" / "assembly_brain.asm"

def main():
    source = ASM_FILE.read_text(encoding="utf-8")
    program = assemble(source)
    cpu = CPU8086(program)

    root = tk.Tk()
    DiningGUI(root, cpu, None)
    root.mainloop()

if __name__ == "__main__":
    main()
