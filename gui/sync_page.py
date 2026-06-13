"""
gui/sync_page.py
----------------
Process Synchronization — Producer-Consumer with animated buffer.

Fixed:
  - ModernButton imported from utils.visualizations (correct path)
  - AgentState imported from modules.synchronization (correct path)
  - All other logic unchanged from working version
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from gui.base_page import BasePage
from utils.helpers import COLORS, FONTS
from utils.visualizations import ModernButton
from modules.synchronization import ProducerConsumerSim, AgentState


_STATE_LABEL = {
    AgentState.IDLE:      ("IDLE",      COLORS["text_secondary"]),
    AgentState.PRODUCING: ("PRODUCING", COLORS["accent_green"]),
    AgentState.CONSUMING: ("CONSUMING", COLORS["accent_blue"]),
    AgentState.WAITING:   ("WAITING",   COLORS["accent_orange"]),
    AgentState.BLOCKED:   ("BLOCKED",   COLORS["accent_red"]),
}


class SyncPage(BasePage):

    TICK_MS = 600    # ms per simulation tick

    def __init__(self, parent: tk.Widget, **kw):
        super().__init__(parent,
                         title="Process Synchronization",
                         subtitle="Producer-Consumer · Bounded Buffer · Semaphore · Mutex",
                         accent=COLORS["accent_orange"], **kw)
        self._sim: ProducerConsumerSim | None = None
        self._after_id = None
        self._running  = False
        self.build()

    def build(self):
        root = tk.Frame(self.body, bg=COLORS["content_bg"])
        root.pack(fill="both", expand=True, padx=12, pady=10)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)

        self._build_left(root).grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self._build_right(root).grid(row=0, column=1, sticky="nsew")

    # ── LEFT ─────────────────────────────────────────────────────────────────

    def _build_left(self, parent) -> tk.Frame:
        frame = tk.Frame(parent, bg=COLORS["card_bg"],
                         highlightbackground=COLORS["card_border"],
                         highlightthickness=1, width=250)
        frame.pack_propagate(False)

        self._sec(frame, "Configuration")

        tk.Label(frame, text="Buffer Size:", font=FONTS["small"],
                 bg=COLORS["card_bg"], fg=COLORS["text_secondary"]).pack(
            anchor="w", padx=12, pady=(10, 2))
        self._buf_size_var = tk.StringVar(value="5")
        ttk.Spinbox(frame, textvariable=self._buf_size_var,
                    from_=2, to=12, width=8).pack(anchor="w", padx=12, pady=2)

        tk.Label(frame, text="Speed (ms/tick):", font=FONTS["small"],
                 bg=COLORS["card_bg"], fg=COLORS["text_secondary"]).pack(
            anchor="w", padx=12, pady=(8, 2))
        self._speed_var = tk.IntVar(value=600)
        ttk.Scale(frame, variable=self._speed_var,
                  from_=100, to=2000, orient="horizontal").pack(
            fill="x", padx=12, pady=2)

        self._divider(frame)
        self._sec(frame, "Controls")

        ModernButton(frame, "▶  Start",   command=self._start,  variant="success").pack(fill="x", padx=12, pady=4)
        ModernButton(frame, "⏸  Pause",   command=self._pause,  variant="outline").pack(fill="x", padx=12, pady=4)
        ModernButton(frame, "▶  Resume",  command=self._resume, variant="primary").pack(fill="x", padx=12, pady=4)
        ModernButton(frame, "↺  Reset",   command=self._reset,  variant="danger").pack(fill="x", padx=12, pady=4)

        self._divider(frame)
        self._sec(frame, "Semaphores")

        sem_grid = tk.Frame(frame, bg=COLORS["card_bg"], padx=12)
        sem_grid.pack(fill="x", pady=8)

        for i, (label, attr, color) in enumerate([
            ("Empty  :", "_sem_empty_var", COLORS["accent_teal"]),
            ("Full   :", "_sem_full_var",  COLORS["accent_purple"]),
            ("Mutex  :", "_mutex_var",     COLORS["accent_orange"]),
        ]):
            tk.Label(sem_grid, text=label, font=FONTS["body_bold"],
                     bg=COLORS["card_bg"],
                     fg=COLORS["text_secondary"]).grid(row=i, column=0, sticky="w", pady=3)
            var = tk.StringVar(value="—")
            setattr(self, attr, var)
            tk.Label(sem_grid, textvariable=var, font=FONTS["mono"],
                     bg=COLORS["card_bg"], fg=color,
                     width=10).grid(row=i, column=1, sticky="w")

        return frame

    # ── RIGHT ─────────────────────────────────────────────────────────────────

    def _build_right(self, parent) -> tk.Frame:
        frame = tk.Frame(parent, bg=COLORS["content_bg"])

        # Agent status row
        agent_row = tk.Frame(frame, bg=COLORS["content_bg"])
        agent_row.pack(fill="x", pady=(0, 10))

        for agent_name, accent in [
            ("Producer", COLORS["accent_green"]),
            ("Consumer", COLORS["accent_blue"]),
        ]:
            card = tk.Frame(agent_row, bg=COLORS["card_bg"],
                            highlightbackground=accent, highlightthickness=2)
            card.pack(side="left", expand=True, fill="x", padx=(0, 8), ipady=6, ipadx=10)
            tk.Label(card, text=agent_name, font=FONTS["body_bold"],
                     bg=COLORS["card_bg"], fg=accent).pack(pady=(6, 2))
            state_var = tk.StringVar(value="IDLE")
            state_lbl = tk.Label(card, textvariable=state_var,
                                  font=("Segoe UI", 12, "bold"),
                                  bg=COLORS["card_bg"],
                                  fg=COLORS["text_secondary"])
            state_lbl.pack()
            setattr(self, f"_{agent_name.lower()}_state_var",  state_var)
            setattr(self, f"_{agent_name.lower()}_state_lbl",  state_lbl)

        # Stat strip
        stat_row = tk.Frame(frame, bg=COLORS["content_bg"])
        stat_row.pack(fill="x", pady=(0, 10))

        self._stat_vars: dict[str, tk.StringVar] = {}
        for title, accent in [
            ("Produced",    COLORS["accent_green"]),
            ("Consumed",    COLORS["accent_blue"]),
            ("Tick",        COLORS["accent_purple"]),
            ("Buffer Used", COLORS["accent_orange"]),
        ]:
            var = tk.StringVar(value="0")
            self._stat_vars[title] = var
            c = self._mini_stat(stat_row, title, var, accent)
            c.pack(side="left", expand=True, fill="x", padx=(0, 8))

        # Buffer visualisation
        buf_card = self._card(frame, "Buffer State")
        buf_card.pack(fill="x", pady=(0, 10))

        self._buf_canvas = tk.Canvas(buf_card, bg=COLORS["canvas_bg"],
                                     height=80, highlightthickness=0)
        self._buf_canvas.pack(fill="x", padx=10, pady=10)

        # Log
        log_card = self._card(frame, "Event Log")
        log_card.pack(fill="both", expand=True)

        log_wrap = tk.Frame(log_card, bg=COLORS["card_bg"])
        log_wrap.pack(fill="both", expand=True, padx=10, pady=6)

        self._log = tk.Text(
            log_wrap, bg=COLORS["sidebar_bg"], fg=COLORS["sidebar_text"],
            font=FONTS["mono_small"], relief="flat",
            state="disabled", padx=6, pady=4)
        log_vsb = ttk.Scrollbar(log_wrap, orient="vertical",
                                 command=self._log.yview)
        self._log.configure(yscrollcommand=log_vsb.set)
        self._log.pack(side="left", fill="both", expand=True)
        log_vsb.pack(side="right", fill="y")

        self._log.tag_configure("green",  foreground=COLORS["accent_green"])
        self._log.tag_configure("red",    foreground=COLORS["accent_red"])
        self._log.tag_configure("orange", foreground=COLORS["accent_orange"])
        self._log.tag_configure("dim",    foreground=COLORS["text_muted"])

        return frame

    # ── Simulation control ────────────────────────────────────────────────────

    def _start(self):
        if self._running:
            return
        try:
            buf_size = int(self._buf_size_var.get())
        except ValueError:
            buf_size = 5
        self._sim = ProducerConsumerSim(buffer_size=buf_size)
        self._sim.start()
        self._running = True
        self._tick()

    def _pause(self):
        self._running = False
        if self._after_id:
            self.after_cancel(self._after_id)

    def _resume(self):
        if self._sim and not self._running:
            self._running = True
            self._tick()

    def _reset(self):
        self._running = False
        if self._after_id:
            self.after_cancel(self._after_id)
        if self._sim:
            self._sim.reset()
            state = self._sim.get_state()
            self._render(state)
        self._clear_log()

    def _tick(self):
        if not self._running or self._sim is None:
            return
        state = self._sim.tick()
        self._render(state)
        delay = max(100, self._speed_var.get())
        self._after_id = self.after(delay, self._tick)

    # ── Rendering ─────────────────────────────────────────────────────────────

    def _render(self, state):
        self._sem_empty_var.set(str(state.semaphore_empty))
        self._sem_full_var.set(str(state.semaphore_full))
        self._mutex_var.set("LOCKED" if state.mutex else "FREE")

        for agent, state_attr, lbl_attr in [
            ("producer", "producer_state", "_producer_state_var"),
            ("consumer", "consumer_state", "_consumer_state_var"),
        ]:
            s = getattr(state, state_attr)
            label, color = _STATE_LABEL.get(s, ("?", COLORS["text_secondary"]))
            getattr(self, lbl_attr).set(label)
            getattr(self, f"_{agent}_state_lbl").configure(fg=color)

        self._stat_vars["Produced"].set(str(state.produced_count))
        self._stat_vars["Consumed"].set(str(state.consumed_count))
        self._stat_vars["Tick"].set(str(state.tick))
        used = sum(1 for x in state.buffer if x is not None)
        self._stat_vars["Buffer Used"].set(f"{used}/{state.buffer_size}")

        self._draw_buffer(state)

        if state.log:
            self._append_log(state.log[-2:])

    def _draw_buffer(self, state):
        c = self._buf_canvas
        c.delete("all")
        c.update_idletasks()
        w        = c.winfo_width() or 600
        n        = state.buffer_size
        cell_w   = min(60, (w - 40) // max(n, 1))
        cell_h   = 50
        total_w  = n * cell_w
        x0       = (w - total_w) // 2
        y0       = 15

        for i, val in enumerate(state.buffer):
            x1, y1 = x0 + i * cell_w, y0
            x2, y2 = x1 + cell_w - 4, y1 + cell_h
            if val is not None:
                fill = COLORS["accent_blue"]
                text = str(val)
                fg   = "#ffffff"
            else:
                fill = COLORS["grid_line"]
                text = ""
                fg   = COLORS["text_muted"]
            c.create_rectangle(x1, y1, x2, y2,
                                fill=fill, outline="#ffffff", width=1.5)
            if text:
                c.create_text((x1 + x2) // 2, (y1 + y2) // 2,
                               text=text, font=("Segoe UI", 10, "bold"),
                               fill=fg)

        c.create_text(w // 2, y0 + cell_h + 12,
                      text=f"Buffer: {sum(1 for v in state.buffer if v is not None)}"
                           f" / {state.buffer_size} slots used",
                      font=FONTS["small"], fill=COLORS["text_secondary"])

    def _append_log(self, lines: list[str]):
        self._log.configure(state="normal")
        for line in lines:
            tag = ""
            if "✔" in line:
                tag = "green"
            elif "BLOCKED" in line:
                tag = "red"
            elif "Waiting" in line or "Producing" in line:
                tag = "orange"
            else:
                tag = "dim"
            self._log.insert("end", line + "\n", tag)
        self._log.see("end")
        self._log.configure(state="disabled")

    def _clear_log(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")

    # ── UI helpers ────────────────────────────────────────────────────────────

    def _sec(self, parent, text):
        f = tk.Frame(parent, bg=COLORS["card_bg"])
        f.pack(fill="x")
        tk.Frame(f, bg=COLORS["accent_orange"], width=3).pack(side="left", fill="y")
        tk.Label(f, text=f"  {text}", font=FONTS["sidebar_hd"],
                 bg=COLORS["card_bg"], fg=COLORS["accent_orange"],
                 pady=5).pack(side="left")

    def _divider(self, parent):
        tk.Frame(parent, bg=COLORS["card_border"], height=1).pack(fill="x", pady=4)

    def _card(self, parent, title: str) -> tk.Frame:
        card = tk.Frame(parent, bg=COLORS["card_bg"],
                        highlightbackground=COLORS["card_border"],
                        highlightthickness=1)
        tk.Label(card, text=title, font=FONTS["body_bold"],
                 bg=COLORS["card_bg"], fg=COLORS["text_primary"],
                 anchor="w", padx=10, pady=6).pack(fill="x")
        tk.Frame(card, bg=COLORS["card_border"], height=1).pack(fill="x")
        return card

    def _mini_stat(self, parent, title, var, accent) -> tk.Frame:
        card = tk.Frame(parent, bg=COLORS["card_bg"],
                        highlightbackground=accent, highlightthickness=1)
        tk.Label(card, text=title, font=FONTS["card_lbl"],
                 bg=COLORS["card_bg"], fg=COLORS["text_secondary"]).pack(pady=(6, 0))
        tk.Label(card, textvariable=var, font=("Segoe UI", 14, "bold"),
                 bg=COLORS["card_bg"], fg=accent).pack(pady=(0, 6))
        return card

    def destroy(self):
        self._running = False
        if self._after_id:
            self.after_cancel(self._after_id)
        super().destroy()