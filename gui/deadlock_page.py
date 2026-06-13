"""
gui/deadlock_page.py
--------------------
Deadlock Handling — Banker's Algorithm UI.

Features:
  - Configure n processes and m resource types
  - Enter Available, Allocation, Maximum matrices
  - Run safety algorithm
  - Display: Need matrix, Safe sequence, Step log, Safe/Unsafe state badge
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from gui.base_page import BasePage
from utils.helpers import COLORS, FONTS, parse_matrix, parse_int_list
from utils.visualizations import ModernButton
from modules.deadlock import bankers


class DeadlockPage(BasePage):

    def __init__(self, parent: tk.Widget, **kw):
        super().__init__(parent,
                         title="Deadlock Handling",
                         subtitle="Banker's Algorithm · Safety Algorithm · Need Matrix · Safe Sequence",
                         accent=COLORS["accent_red"], **kw)
        self.build()

    def build(self):
        root = tk.Frame(self.body, bg=COLORS["content_bg"])
        root.pack(fill="both", expand=True, padx=12, pady=10)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)

        self._build_left(root).grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self._build_right(root).grid(row=0, column=1, sticky="nsew")

    # ── LEFT PANEL ────────────────────────────────────────────────────────────

    def _build_left(self, parent) -> tk.Frame:
        frame = tk.Frame(parent, bg=COLORS["card_bg"],
                         highlightbackground=COLORS["card_border"],
                         highlightthickness=1, width=300)
        frame.pack_propagate(False)

        self._sec(frame, "Configuration")

        # n processes / m resources
        cfg = tk.Frame(frame, bg=COLORS["card_bg"], padx=12)
        cfg.pack(fill="x", pady=(6, 0))

        for row_i, (lbl, attr, default) in enumerate([
            ("Processes (n):", "_n_var", "5"),
            ("Resources (m):", "_m_var", "3"),
        ]):
            tk.Label(cfg, text=lbl, font=FONTS["small"],
                     bg=COLORS["card_bg"], fg=COLORS["text_secondary"],
                     width=14, anchor="w").grid(row=row_i, column=0, pady=3)
            var = tk.StringVar(value=default)
            setattr(self, attr, var)
            ttk.Spinbox(cfg, textvariable=var, from_=1, to=20,
                        width=6).grid(row=row_i, column=1, pady=3, sticky="w")

        self._divider(frame)

        # Available resources
        self._sec(frame, "Available Resources")
        tk.Label(frame, text="Space-separated (one per resource):",
                 font=FONTS["small"], bg=COLORS["card_bg"],
                 fg=COLORS["text_secondary"]).pack(anchor="w", padx=12)
        self._avail_var = tk.StringVar(value="3 3 2")
        ttk.Entry(frame, textvariable=self._avail_var, width=28).pack(
            fill="x", padx=12, pady=4)

        self._divider(frame)

        # Allocation matrix
        self._sec(frame, "Allocation Matrix")
        tk.Label(frame, text="One row per process (rows separated by newlines):",
                 font=FONTS["small"], bg=COLORS["card_bg"],
                 fg=COLORS["text_secondary"], wraplength=240).pack(anchor="w", padx=12)
        self._alloc_text = tk.Text(frame, height=6, width=28,
                                    bg=COLORS["canvas_bg"],
                                    fg=COLORS["text_primary"],
                                    font=FONTS["mono_small"],
                                    relief="flat", padx=6, pady=4)
        self._alloc_text.pack(fill="x", padx=12, pady=4)
        self._alloc_text.insert("1.0", "0 1 0\n2 0 0\n3 0 2\n2 1 1\n0 0 2")

        self._divider(frame)

        # Maximum matrix
        self._sec(frame, "Maximum Matrix")
        self._max_text = tk.Text(frame, height=6, width=28,
                                  bg=COLORS["canvas_bg"],
                                  fg=COLORS["text_primary"],
                                  font=FONTS["mono_small"],
                                  relief="flat", padx=6, pady=4)
        self._max_text.pack(fill="x", padx=12, pady=4)
        self._max_text.insert("1.0", "7 5 3\n3 2 2\n9 0 2\n2 2 2\n4 3 3")

        self._divider(frame)

        ModernButton(frame, "Load Classic Example",
                     command=self._load_example, variant="outline").pack(
            fill="x", padx=12, pady=4)
        ModernButton(frame, "▶  Run Banker's Algorithm",
                     command=self._run, variant="primary").pack(
            fill="x", padx=12, pady=(4, 12))

        return frame

    # ── RIGHT PANEL ───────────────────────────────────────────────────────────

    def _build_right(self, parent) -> tk.Frame:
        frame = tk.Frame(parent, bg=COLORS["content_bg"])

        # Safe/Unsafe status banner
        self._status_var  = tk.StringVar(value="Run the algorithm to check safety.")
        self._status_frame = tk.Frame(frame, bg=COLORS["card_bg"],
                                       highlightbackground=COLORS["card_border"],
                                       highlightthickness=1)
        self._status_frame.pack(fill="x", pady=(0, 10))
        self._status_lbl = tk.Label(
            self._status_frame, textvariable=self._status_var,
            font=("Segoe UI", 13, "bold"),
            bg=COLORS["card_bg"], fg=COLORS["text_secondary"],
            anchor="center", pady=12)
        self._status_lbl.pack(fill="x")

        # Safe sequence
        seq_card = self._card(frame, "Safe Sequence")
        seq_card.pack(fill="x", pady=(0, 10))
        self._seq_var = tk.StringVar(value="—")
        tk.Label(seq_card, textvariable=self._seq_var,
                 font=FONTS["mono"], bg=COLORS["card_bg"],
                 fg=COLORS["accent_teal"], anchor="w",
                 padx=12, pady=8).pack(fill="x")

        # Need matrix display
        need_card = self._card(frame, "Need Matrix  (Maximum − Allocation)")
        need_card.pack(fill="x", pady=(0, 10))

        self._need_canvas = tk.Canvas(
            need_card, bg=COLORS["canvas_bg"], height=160, highlightthickness=0)
        self._need_canvas.pack(fill="x", padx=10, pady=8)

        # Step log
        log_card = self._card(frame, "Safety Algorithm Steps")
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

        self._log.tag_configure("safe",   foreground=COLORS["accent_green"])
        self._log.tag_configure("unsafe", foreground=COLORS["accent_red"])
        self._log.tag_configure("step",   foreground=COLORS["accent_blue"])
        self._log.tag_configure("dim",    foreground=COLORS["text_muted"])

        return frame

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _load_example(self):
        """Load the classic Banker's Algorithm textbook example."""
        self._n_var.set("5")
        self._m_var.set("3")
        self._avail_var.set("3 3 2")
        self._alloc_text.delete("1.0", "end")
        self._alloc_text.insert("1.0", "0 1 0\n2 0 0\n3 0 2\n2 1 1\n0 0 2")
        self._max_text.delete("1.0", "end")
        self._max_text.insert("1.0", "7 5 3\n3 2 2\n9 0 2\n2 2 2\n4 3 3")

    def _run(self):
        try:
            n = int(self._n_var.get())
            m = int(self._m_var.get())

            available  = parse_int_list(self._avail_var.get(), "Available")
            if len(available) != m:
                raise ValueError(f"Available must have {m} values, got {len(available)}.")

            alloc_raw  = self._alloc_text.get("1.0", "end").strip()
            max_raw    = self._max_text.get("1.0", "end").strip()

            allocation = parse_matrix(alloc_raw, n, m, "Allocation")
            maximum    = parse_matrix(max_raw,   n, m, "Maximum")

            result = bankers(available, allocation, maximum)
        except Exception as e:
            self.show_error(str(e))
            return

        # Status banner
        if result.is_safe:
            self._status_var.set("✔  SAFE STATE — System will not deadlock")
            self._status_lbl.configure(fg=COLORS["accent_green"])
            self._status_frame.configure(
                highlightbackground=COLORS["accent_green"])
        else:
            self._status_var.set("✘  UNSAFE STATE — Deadlock possible!")
            self._status_lbl.configure(fg=COLORS["accent_red"])
            self._status_frame.configure(
                highlightbackground=COLORS["accent_red"])

        # Safe sequence
        if result.safe_sequence:
            seq = " → ".join(f"P{i}" for i in result.safe_sequence)
            self._seq_var.set(seq)
        else:
            self._seq_var.set("No safe sequence found.")

        # Need matrix canvas
        self._draw_need_matrix(result.need, n, m)

        # Step log
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        for line in result.steps:
            if "✔" in line or "SAFE" in line:
                tag = "safe"
            elif "✘" in line or "UNSAFE" in line:
                tag = "unsafe"
            elif "Step" in line:
                tag = "step"
            else:
                tag = "dim"
            self._log.insert("end", line + "\n", tag)
        self._log.see("end")
        self._log.configure(state="disabled")

    def _draw_need_matrix(self, need: list[list[int]], n: int, m: int):
        c = self._need_canvas
        c.delete("all")
        c.update_idletasks()

        cw, ch = 50, 28
        x0, y0 = 60, 10

        # Column headers (R0, R1, …)
        c.create_text(x0 - 30, y0 + ch // 2,
                      text="P\\R", font=("Segoe UI", 8, "bold"),
                      fill=COLORS["text_secondary"])
        for j in range(m):
            cx = x0 + j * cw
            c.create_rectangle(cx, y0, cx + cw, y0 + ch,
                                fill=COLORS["sidebar_active"],
                                outline="#ffffff")
            c.create_text(cx + cw // 2, y0 + ch // 2,
                          text=f"R{j}", font=("Segoe UI", 8, "bold"),
                          fill="#ffffff")

        for i, row in enumerate(need):
            ry = y0 + (i + 1) * ch
            # Row header
            c.create_text(x0 - 14, ry + ch // 2,
                          text=f"P{i}", font=("Segoe UI", 8, "bold"),
                          fill=COLORS["text_secondary"])
            for j, val in enumerate(row):
                cx   = x0 + j * cw
                fill = COLORS["accent_teal"] if val > 0 else COLORS["card_bg"]
                c.create_rectangle(cx, ry, cx + cw, ry + ch,
                                   fill=fill, outline=COLORS["card_border"])
                c.create_text(cx + cw // 2, ry + ch // 2,
                              text=str(val), font=("Segoe UI", 9),
                              fill="#ffffff" if val > 0 else COLORS["text_primary"])

        total_h = y0 + (n + 1) * ch + 10
        total_w = x0 + m * cw + 10
        c.configure(scrollregion=(0, 0, total_w, total_h),
                    height=min(total_h, 200))

    # ── UI helpers ────────────────────────────────────────────────────────────

    def _sec(self, parent, text):
        f = tk.Frame(parent, bg=COLORS["card_bg"])
        f.pack(fill="x")
        tk.Frame(f, bg=COLORS["accent_red"], width=3).pack(side="left", fill="y")
        tk.Label(f, text=f"  {text}", font=FONTS["sidebar_hd"],
                 bg=COLORS["card_bg"], fg=COLORS["accent_red"],
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