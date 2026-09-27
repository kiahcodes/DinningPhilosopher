import math
import tkinter as tk
from tkinter import ttk, messagebox

from .model import PHIL_NAMES, FORK_NAMES, STATE_NAMES, snapshot, explain_event

# ----------------------------------------------------------------------
# Palette — light dashboard style: lime page, white cards, one dark card.
# ----------------------------------------------------------------------
PAGE_BG   = "#d3e654"   # outer page background
SHELL_BG  = "#eef1e2"   # the big shell that holds everything
CARD_BG   = "#ffffff"   # white cards
CARD_BORDER = "#e7e9da"
DARK_BG   = "#161616"   # sidebar / dark card
DARK_TEXT = "#f5f5f0"
TEXT      = "#161616"
MUTED     = "#8b8f7a"
LIME      = "#d7f24e"
LIME_DEEP = "#a9c52e"
PURPLE    = "#b7a6f2"
AMBER     = "#f5c451"

PHIL_COLOR = {
    "THINKING": (DARK_BG, DARK_TEXT),
    "HUNGRY":   (AMBER, TEXT),
    "WAITING":  (PURPLE, TEXT),
    "EATING":   (LIME, TEXT),
}
FORK_FREE   = (LIME, TEXT)
FORK_LOCKED = (DARK_BG, DARK_TEXT)

STATUS_COLOR = {
    "STOPPED": MUTED,
    "RUNNING": LIME_DEEP,
    "PAUSED":  "#b8952f",
    "HALTED":  "#c2432f",
    "DEADLOCK DEMO": "#c2432f",
    "SAFE MODE": LIME_DEEP,
}

FONT = "Segoe UI"

# Fork ownership: philosopher index -> (left fork index, right fork index)
_PHIL_FORKS = {0: (0, 1), 1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 0)}

# Shared-memory variable names that represent philosopher/fork state.
_STATE_VARS = {"PHIL1", "PHIL2", "PHIL3", "PHIL4", "PHIL5",
               "FORK1", "FORK2", "FORK3", "FORK4", "FORK5",
               "DEADLOCK", "MODE", "TICK", "CURRENT"}


class DiningGUI:
    def __init__(self, root, cpu, mode_callback=None):
        self.root = root
        self.cpu = cpu
        self.mode_callback = mode_callback
        self.running = False
        self.delay = 100
        self.log = []  # (text, is_write) tuples

        root.title("Dining Philosophers — Virtual 8086")
        root.geometry("1320x880")
        root.minsize(1080, 720)
        root.configure(bg=PAGE_BG)
        self._style()

        self._build()
        self.refresh()

    # ------------------------------------------------------------------
    # Style
    # ------------------------------------------------------------------

    def _style(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(".", background=CARD_BG, foreground=TEXT, font=(FONT, 10))
        style.configure("Shell.TFrame", background=SHELL_BG)
        style.configure("Card.TFrame", background=CARD_BG)
        style.configure("Dark.TFrame", background=DARK_BG)

        style.configure("Card.TLabel", background=CARD_BG, foreground=TEXT)
        style.configure("Muted.TLabel", background=CARD_BG, foreground=MUTED, font=(FONT, 9))
        style.configure("Dark.TLabel", background=DARK_BG, foreground=DARK_TEXT)
        style.configure("DarkMuted.TLabel", background=DARK_BG, foreground="#9a9a94", font=(FONT, 9))

        style.configure("Section.TLabel", background=CARD_BG, foreground=MUTED,
                         font=(FONT, 9, "bold"))
        style.configure("DarkSection.TLabel", background=DARK_BG, foreground="#c8c8c0",
                         font=(FONT, 9, "bold"))

        # Primary buttons: dark pill with light text (like the reference's
        # "Upgrade Now" button); secondary buttons stay a plain outline.
        style.configure("Primary.TButton", font=(FONT, 10, "bold"),
                         background=DARK_BG, foreground=DARK_TEXT,
                         borderwidth=0, padding=8)
        style.map("Primary.TButton",
                  background=[("active", "#2a2a2a")],
                  foreground=[("active", DARK_TEXT)])

        style.configure("Secondary.TButton", font=(FONT, 10),
                         background="#f1f2ea", foreground=TEXT,
                         borderwidth=0, padding=8)
        style.map("Secondary.TButton", background=[("active", "#e5e7d9")])

        style.configure("Card.Horizontal.TScale", background=CARD_BG)

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build(self):
        shell = ttk.Frame(self.root, style="Shell.TFrame", padding=18)
        shell.pack(fill="both", expand=True)

        self._build_header(shell)
        self._build_strip(shell)

        main = ttk.Frame(shell, style="Shell.TFrame")
        main.pack(fill="both", expand=True, pady=(14, 0))

        left = ttk.Frame(main, style="Shell.TFrame")
        left.pack(side="left", fill="both", expand=True)
        self._build_canvas(left)

        right = ttk.Frame(main, width=340, style="Shell.TFrame")
        right.pack(side="right", fill="y", padx=(14, 0))
        right.pack_propagate(False)

        self._build_controls(right)
        self._build_legend(right)
        self._build_state_panels(right)

    def _card(self, parent, **pack_kwargs):
        outer = tk.Frame(parent, bg=CARD_BG, highlightbackground=CARD_BORDER,
                          highlightthickness=1)
        outer.pack(**pack_kwargs)
        return outer

    def _build_header(self, parent):
        card = self._card(parent, fill="x")
        inner = ttk.Frame(card, style="Card.TFrame", padding=(18, 14))
        inner.pack(fill="x")

        title = ttk.Frame(inner, style="Card.TFrame")
        title.pack(side="left")
        ttk.Label(title, text="Dining Philosophers", style="Card.TLabel",
                  font=(FONT, 17, "bold")).pack(side="left")
        badge = tk.Label(title, text="Virtual 8086", bg=LIME, fg=TEXT,
                          font=(FONT, 8, "bold"), padx=8, pady=2)
        badge.pack(side="left", padx=(10, 0))

        right = ttk.Frame(inner, style="Card.TFrame")
        right.pack(side="right")
        self.status = tk.Label(right, text="STOPPED", bg=CARD_BG,
                                fg=STATUS_COLOR["STOPPED"], font=(FONT, 10, "bold"))
        self.status.pack(side="right", padx=(14, 0))
        ttk.Button(right, text="Help", style="Secondary.TButton",
                   command=self.show_help).pack(side="right")

    def _build_strip(self, parent):
        card = self._card(parent, fill="x", pady=(12, 0))
        self.explain_var = tk.StringVar(
            value="Choose a scenario on the right, or step through the program manually.")
        bar = tk.Frame(card, bg=LIME, width=4)
        bar.pack(side="left", fill="y")
        self.explain_label = tk.Label(
            card, textvariable=self.explain_var, bg=CARD_BG, fg=TEXT,
            font=(FONT, 11), anchor="w", justify="left", padx=14, pady=10)
        self.explain_label.pack(fill="x", side="left", expand=True)
        card.bind("<Configure>",
                  lambda e: self.explain_label.config(wraplength=max(e.width - 40, 200)))

    def _build_canvas(self, parent):
        card = self._card(parent, fill="both", expand=True)
        self.canvas = tk.Canvas(card, bg=CARD_BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=2, pady=2)

    def _build_controls(self, parent):
        card = self._card(parent, fill="x", pady=(0, 12))
        box = ttk.Frame(card, style="Card.TFrame", padding=14)
        box.pack(fill="x")

        ttk.Label(box, text="CONTROL", style="Section.TLabel").pack(anchor="w", pady=(0, 8))

        row = ttk.Frame(box, style="Card.TFrame")
        row.pack(fill="x", pady=(0, 6))
        ttk.Button(row, text="Start", style="Primary.TButton",
                   command=self.start).pack(side="left", expand=True, fill="x", padx=(0, 4))
        ttk.Button(row, text="Pause", style="Secondary.TButton",
                   command=self.pause).pack(side="left", expand=True, fill="x", padx=4)
        ttk.Button(row, text="Reset", style="Secondary.TButton",
                   command=self.reset).pack(side="left", expand=True, fill="x", padx=(4, 0))

        ttk.Button(box, text="Step One Instruction", style="Secondary.TButton",
                   command=self.step_once).pack(fill="x", pady=(0, 10))

        ttk.Separator(box).pack(fill="x", pady=(0, 10))
        ttk.Label(box, text="SCENARIOS", style="Section.TLabel").pack(anchor="w", pady=(0, 6))

        ttk.Button(box, text="Run Deadlock Demo", style="Primary.TButton",
                   command=lambda: self.set_mode(0)).pack(fill="x", pady=(0, 6))
        ttk.Button(box, text="Run Deadlock-Prevention Demo", style="Primary.TButton",
                   command=lambda: self.set_mode(1)).pack(fill="x")

        ttk.Separator(box).pack(fill="x", pady=10)

        speed_row = ttk.Frame(box, style="Card.TFrame")
        speed_row.pack(fill="x")
        ttk.Label(speed_row, text="Speed", style="Muted.TLabel").pack(side="left")
        self.speed_label = ttk.Label(speed_row, text=f"{self.delay} ms", style="Muted.TLabel")
        self.speed_label.pack(side="right")

        self._speed_var = tk.IntVar(value=self.delay)

        def _on_speed(val):
            self.delay = int(float(val))
            self.speed_label.config(text=f"{self.delay} ms")

        ttk.Scale(box, from_=15, to=600, orient="horizontal", style="Card.Horizontal.TScale",
                  variable=self._speed_var, command=_on_speed).pack(fill="x", pady=(4, 0))

    def _build_legend(self, parent):
        card = self._card(parent, fill="x", pady=(0, 12))
        box = ttk.Frame(card, style="Card.TFrame", padding=14)
        box.pack(fill="x")

        ttk.Label(box, text="LEGEND", style="Section.TLabel").pack(anchor="w", pady=(0, 8))

        def swatch(row_parent, color, label):
            dot = tk.Canvas(row_parent, width=10, height=10, bg=CARD_BG, highlightthickness=0)
            dot.create_oval(0, 0, 10, 10, fill=color, outline="")
            dot.pack(side="left", padx=(0, 6))
            ttk.Label(row_parent, text=label, style="Card.TLabel", font=(FONT, 9)).pack(side="left")

        philosophers = ttk.Frame(box, style="Card.TFrame")
        philosophers.pack(fill="x", pady=(0, 8))
        for state in ("THINKING", "HUNGRY", "WAITING", "EATING"):
            cell = ttk.Frame(philosophers, style="Card.TFrame")
            cell.pack(side="left", expand=True)
            swatch(cell, PHIL_COLOR[state][0], state.title())

        forks = ttk.Frame(box, style="Card.TFrame")
        forks.pack(fill="x")
        for color, label in ((FORK_FREE[0], "Fork free"), (FORK_LOCKED[0], "Fork locked")):
            cell = ttk.Frame(forks, style="Card.TFrame")
            cell.pack(side="left", expand=True)
            swatch(cell, color, label)

    def _build_state_panels(self, parent):
        card = self._card(parent, fill="both", expand=True)
        box = ttk.Frame(card, style="Dark.TFrame", padding=14)
        box.pack(fill="both", expand=True)

        def mono_text(height):
            return tk.Text(box, height=height, font=("Consolas", 9), wrap="none",
                            state="disabled", bg=DARK_BG, fg=DARK_TEXT,
                            relief="flat", highlightthickness=0,
                            insertbackground=DARK_TEXT, padx=0, pady=0, bd=0)

        ttk.Label(box, text="CPU STATE", style="DarkSection.TLabel").pack(anchor="w", pady=(0, 8))

        ttk.Label(box, text="Registers", style="DarkMuted.TLabel").pack(anchor="w")
        self.cpu_text = mono_text(6)
        self.cpu_text.pack(fill="x", pady=(2, 10))

        ttk.Label(box, text="Memory", style="DarkMuted.TLabel").pack(anchor="w")
        self.mem_text = mono_text(9)
        self.mem_text.pack(fill="x", pady=(2, 10))

        ttk.Label(box, text="Instruction log", style="DarkMuted.TLabel").pack(anchor="w")
        self.log_text = tk.Text(box, font=("Consolas", 9), wrap="none",
                                 state="disabled", bg=DARK_BG, fg=DARK_TEXT,
                                 relief="flat", highlightthickness=0, bd=0)
        self.log_text.tag_configure("highlight", foreground=LIME)
        self.log_text.pack(fill="both", expand=True, pady=(2, 0))

    # ------------------------------------------------------------------
    # Help
    # ------------------------------------------------------------------

    def show_help(self):
        win = tk.Toplevel(self.root)
        win.title("Help")
        win.geometry("560x520")
        win.configure(bg=CARD_BG)
        win.transient(self.root)

        ttk.Button(win, text="Close", style="Primary.TButton",
                   command=win.destroy).pack(side="bottom", pady=12)

        text = tk.Text(win, wrap="word", font=(FONT, 10), padx=20, pady=18,
                        bg=CARD_BG, fg=TEXT, relief="flat", highlightthickness=0)
        text.pack(fill="both", expand=True, side="left")
        scroll = ttk.Scrollbar(win, command=text.yview)
        scroll.pack(side="right", fill="y")
        text.config(yscrollcommand=scroll.set)

        text.tag_configure("h", font=(FONT, 11, "bold"), foreground=TEXT, spacing3=6)
        text.tag_configure("p", font=(FONT, 10), foreground="#3f4238", spacing3=14)

        sections = [
            ("The problem",
             "Five philosophers share a round table with five forks — one between "
             "each pair of neighbors. Eating requires both the left and right fork."),
            ("States",
             "Thinking — idle, no fork needed.\n"
             "Hungry — wants to eat.\n"
             "Waiting — holds one fork, needs the other.\n"
             "Eating — holds both forks."),
            ("Deadlock",
             "If every philosopher takes their left fork first and then waits for "
             "the right one, the waiting forms a closed loop and nobody can proceed. "
             "\"Run Deadlock Demo\" plays this out."),
            ("Prevention",
             "\"Run Deadlock-Prevention Demo\" hands out forks in rounds so philosophers "
             "who don't share a fork eat together, breaking the circular wait."),
            ("Why an 8086 CPU",
             "This logic is written in 8086 assembly (asm/assembly_brain.asm), not "
             "Python. The panels on the right show the emulator's real registers and "
             "memory as that program runs; the strip above the table narrates each "
             "step in plain language."),
        ]
        for heading, body in sections:
            text.insert("end", heading + "\n", "h")
            text.insert("end", body + "\n", "p")

        text.config(state="disabled")

    # ------------------------------------------------------------------
    # Control callbacks
    # ------------------------------------------------------------------

    def _set_status(self, text):
        self.status.config(text=text, fg=STATUS_COLOR.get(text, TEXT))

    def start(self):
        self.running = True
        self._set_status("RUNNING")
        self._loop()

    def pause(self):
        self.running = False
        self._set_status("PAUSED")

    def reset(self):
        self.running = False
        self.cpu.reset()
        self.log.clear()
        self._set_status("STOPPED")
        self.explain_var.set("Reset. Start, step, or choose a scenario to continue.")
        self.refresh()

    def set_mode(self, mode):
        self.cpu.reset()
        self.cpu.memory["MODE"] = mode
        self.cpu.memory["DEADLOCK"] = 0
        self.running = True
        self._set_status("DEADLOCK DEMO" if mode == 0 else "SAFE MODE")
        self._loop()

    def step_once(self):
        self.running = False
        self._set_status("PAUSED")
        try:
            self.cpu.step()
            self._append_log()
            self.refresh()
        except Exception as e:
            messagebox.showerror("CPU error", str(e))

    def _loop(self):
        if not self.running:
            return
        try:
            self.cpu.step()
            self._append_log()
            if self.cpu.halted:
                self.running = False
                self._set_status("HALTED")
            self.refresh()
        except Exception as e:
            self.running = False
            messagebox.showerror("CPU error", str(e))
            return
        self.root.after(self.delay, self._loop)

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _is_write_event(self):
        ev = self.cpu.last_event
        if not ev:
            return False
        var = ev.split("<-")[0].strip().upper()
        return var in _STATE_VARS

    def _append_log(self):
        if self.cpu.last_instruction:
            msg = f"IP={self.cpu.regs['IP']:04X}  {self.cpu.last_instruction}"
            is_write = self._is_write_event()
            if self.cpu.last_event:
                msg += f"   [{self.cpu.last_event}]"
            self.log.append((msg, is_write))
            self.log = self.log[-250:]

    # ------------------------------------------------------------------
    # Refresh / render
    # ------------------------------------------------------------------

    def refresh(self):
        s = snapshot(self.cpu)
        self._draw_table(s)
        self._set_text(self.cpu_text, self._cpu_panel(s))
        self._set_text(self.mem_text, self._memory_panel(s))
        self._refresh_log()
        if self.cpu.executed > 0:
            self.explain_var.set(explain_event(self.cpu))

    def _set_text(self, widget, text):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.config(state="disabled")

    def _refresh_log(self):
        visible = self.log[-80:]
        widget = self.log_text
        widget.config(state="normal")
        widget.delete("1.0", "end")
        for msg, is_write in visible:
            widget.insert("end", msg + "\n", "highlight" if is_write else "")
        widget.config(state="disabled")
        widget.see("end")

    # ------------------------------------------------------------------
    # Panel text helpers
    # ------------------------------------------------------------------

    def _cpu_panel(self, s):
        r = s["registers"]
        f = s["flags"]
        return (
            f"AX {r['AX']:04X}   BX {r['BX']:04X}   CX {r['CX']:04X}   DX {r['DX']:04X}\n"
            f"SI {r['SI']:04X}   DI {r['DI']:04X}   SP {r['SP']:04X}   IP {r['IP']:04X}\n"
            f"ZF {f['ZF']}  SF {f['SF']}  CF {f['CF']}  OF {f['OF']}\n"
            f"Instructions executed: {s['executed']}"
        )

    def _memory_panel(self, s):
        lines = []
        for i, v in enumerate(s["philosophers"], 1):
            lines.append(f"PHIL{i}     {v:02X}h  {STATE_NAMES.get(v, 'UNKNOWN')}")
        lines.append("")
        for i, v in enumerate(s["forks"], 1):
            lines.append(f"FORK{i}     {v:02X}h  {'LOCKED' if v else 'FREE'}")
        lines.append("")
        lines.append(f"CURRENT   P{s['current'] + 1}")
        lines.append(f"MODE      {'SAFE' if s['mode'] else 'DEADLOCK'}")
        lines.append(f"TICK      {s['tick']}")
        lines.append(f"DEADLOCK  {'YES' if s['deadlock'] else 'NO'}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Canvas drawing
    # ------------------------------------------------------------------

    def _draw_table(self, s):
        c = self.canvas
        c.delete("all")
        w = max(c.winfo_width(), 650)
        h = max(c.winfo_height(), 520)
        cx, cy = w * 0.5, h * 0.48
        table_r = min(w, h) * 0.19
        seat_r  = min(w, h) * 0.33
        fork_r  = min(w, h) * 0.235

        phil_pos = {}
        for i in range(5):
            angle = math.radians(-90 + i * 72)
            phil_pos[i] = (cx + seat_r * math.cos(angle),
                           cy + seat_r * math.sin(angle))

        fork_pos = {}
        for i in range(5):
            angle = math.radians(-90 + i * 72 - 36)
            fork_pos[i] = (cx + fork_r * math.cos(angle),
                           cy + fork_r * math.sin(angle))

        c.create_oval(cx - table_r, cy - table_r, cx + table_r, cy + table_r,
                      fill=SHELL_BG, outline=CARD_BORDER, width=2)
        c.create_text(cx, cy, text="8086", fill=MUTED, font=(FONT, 14, "bold"))

        is_deadlock = bool(s["deadlock"])

        for phil_i in range(5):
            px, py = phil_pos[phil_i]
            val = s["philosophers"][phil_i]
            state = STATE_NAMES.get(val, "UNKNOWN")
            left_fork, right_fork = _PHIL_FORKS[phil_i]

            if state == "EATING":
                for fk in (left_fork, right_fork):
                    fx, fy = fork_pos[fk]
                    c.create_line(px, py, fx, fy, fill=LIME_DEEP, width=2, dash=(6, 4))

            elif is_deadlock or (s["mode"] == 0 and state == "WAITING"):
                fx_left, fy_left = fork_pos[left_fork]
                c.create_line(px, py, fx_left, fy_left, fill=AMBER, width=2)

                fx_right, fy_right = fork_pos[right_fork]
                dx, dy = fx_right - px, fy_right - py
                dist = math.hypot(dx, dy) or 1.0
                end_x = fx_right - (dx / dist) * 26
                end_y = fy_right - (dy / dist) * 26
                c.create_line(px, py, end_x, end_y, fill="#c2432f", width=2,
                              dash=(4, 4), arrow="last", arrowshape=(9, 11, 4))

        for i, val in enumerate(s["forks"]):
            x, y = fork_pos[i]
            fill, fg = FORK_LOCKED if val else FORK_FREE
            c.create_oval(x - 20, y - 20, x + 20, y + 20, fill=fill, outline=CARD_BG, width=2)
            c.create_text(x, y, text=f"F{i + 1}", fill=fg, font=(FONT, 9, "bold"))

        for i, val in enumerate(s["philosophers"]):
            x, y = phil_pos[i]
            state = STATE_NAMES.get(val, "UNKNOWN")
            fill, fg = PHIL_COLOR.get(state, (MUTED, TEXT))

            c.create_oval(x - 48, y - 34, x + 48, y + 34, fill=fill, outline=CARD_BG, width=2)
            c.create_text(x, y - 8, text=f"P{i + 1}", fill=fg, font=(FONT, 12, "bold"))
            c.create_text(x, y + 12, text=state.title(), fill=fg, font=(FONT, 8, "bold"))

        if is_deadlock:
            c.create_text(cx, h - 34, text="Deadlock — every philosopher is stuck waiting",
                          fill="#c2432f", font=(FONT, 12, "bold"))
        elif s["mode"] == 1:
            c.create_text(cx, h - 34, text="Safe mode — deadlock prevented",
                          fill=LIME_DEEP, font=(FONT, 12, "bold"))
