"""
gui/page_replacement_page.py
-----------------------------
Page Replacement module UI — FIFO, LRU, Optimal.

Fixed:
  - parse_int_list imported from utils.helpers (not visualizations)
  - ModernButton import path corrected to utils.visualizations
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from gui.base_page import BasePage
from utils.helpers import COLORS, FONTS, parse_int_list
from utils.visualizations import ModernButton
from modules.page_replacement import run as pr_run


class PageReplacementPage(BasePage):

    def __init__(self, parent: tk.Widget, **kw):
        super().__init__(parent,
                         title="Page Replacement",
                         subtitle="FIFO · LRU · Optimal — frame-by-frame visualisation",
                         accent=COLORS["accent_green"], **kw)
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
                         highlightthickness=1, width=280)
        frame.pack_propagate(False)

        self._sec(frame, "Configuration")

        tk.Label(frame, text="Reference String (e.g. 7 0 1 2 0 3):",
                 font=FONTS["small"], bg=COLORS["card_bg"],
                 fg=COLORS["text_secondary"]).pack(anchor="w", padx=12, pady=(8, 2))
        self._ref_var = tk.StringVar(value="7 0 1 2 0 3 0 4 2 3 0 3 2 1 2 0 1 7 0 1")
        ttk.Entry(frame, textvariable=self._ref_var, width=28).pack(
            fill="x", padx=12, pady=4)

        tk.Label(frame, text="Number of Frames:",
                 font=FONTS["small"], bg=COLORS["card_bg"],
                 fg=COLORS["text_secondary"]).pack(anchor="w", padx=12)
        self._frames_var = tk.StringVar(value="3")
        ttk.Spinbox(frame, textvariable=self._frames_var,
                    from_=1, to=10, width=8).pack(anchor="w", padx=12, pady=4)

        self._divider(frame)
        self._sec(frame, "Algorithm")

        self._algo_var = tk.StringVar(value="FIFO")
        for alg in ("FIFO", "LRU", "Optimal"):
            tk.Radiobutton(
                frame, text=alg, variable=self._algo_var, value=alg,
                bg=COLORS["card_bg"], fg=COLORS["text_primary"],
                selectcolor=COLORS["content_bg"],
                activebackground=COLORS["card_bg"],
                font=FONTS["body"]
            ).pack(anchor="w", padx=18, pady=2)

        self._divider(frame)

        ModernButton(frame, "Load Demo String",
                     command=self._load_demo, variant="outline").pack(
            fill="x", padx=12, pady=4)
        ModernButton(frame, "▶  Run Simulation",
                     command=self._run, variant="primary").pack(
            fill="x", padx=12, pady=(4, 12))

        return frame

    # ── RIGHT ─────────────────────────────────────────────────────────────────

    def _build_right(self, parent) -> tk.Frame:
        frame = tk.Frame(parent, bg=COLORS["content_bg"])

        # Stat strip
        stat_row = tk.Frame(frame, bg=COLORS["content_bg"])
        stat_row.pack(fill="x", pady=(0, 10))

        self._stat_vars: dict[str, tk.StringVar] = {}
        for title, accent in [
            ("Page Faults",  COLORS["accent_red"]),
            ("Page Hits",    COLORS["accent_green"]),
            ("Hit Ratio",    COLORS["accent_teal"]),
            ("Fault Ratio",  COLORS["accent_orange"]),
        ]:
            var = tk.StringVar(value="—")
            self._stat_vars[title] = var
            c = self._mini_stat(stat_row, title, var, accent)
            c.pack(side="left", expand=True, fill="x", padx=(0, 8))

        # Frame table canvas (scrollable horizontally)
        vis_card = self._card(frame, "Frame State Table")
        vis_card.pack(fill="both", expand=True)

        wrap = tk.Frame(vis_card, bg=COLORS["card_bg"])
        wrap.pack(fill="both", expand=True, padx=10, pady=8)

        hscroll = ttk.Scrollbar(wrap, orient="horizontal")
        hscroll.pack(side="bottom", fill="x")
        vscroll = ttk.Scrollbar(wrap, orient="vertical")
        vscroll.pack(side="right", fill="y")

        self._frame_canvas = tk.Canvas(
            wrap, bg=COLORS["canvas_bg"],
            xscrollcommand=hscroll.set,
            yscrollcommand=vscroll.set,
            highlightthickness=0)
        self._frame_canvas.pack(side="left", fill="both", expand=True)
        hscroll.config(command=self._frame_canvas.xview)
        vscroll.config(command=self._frame_canvas.yview)

        # Legend
        leg = tk.Frame(vis_card, bg=COLORS["card_bg"])
        leg.pack(fill="x", padx=10, pady=(0, 6))
        for color, lbl in [
            (COLORS["accent_red"],   "Page Fault"),
            (COLORS["accent_green"], "Page Hit"),
        ]:
            tk.Frame(leg, bg=color, width=14, height=14).pack(side="left", padx=(0, 4))
            tk.Label(leg, text=lbl, font=FONTS["small"],
                     bg=COLORS["card_bg"], fg=COLORS["text_secondary"]).pack(
                side="left", padx=(0, 14))

        return frame

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _load_demo(self):
        self._ref_var.set("7 0 1 2 0 3 0 4 2 3 0 3 2 1 2 0 1 7 0 1")
        self._frames_var.set("3")

    def _run(self):
        try:
            refs   = parse_int_list(self._ref_var.get(), "Reference String")
            n      = int(self._frames_var.get())
            algo   = self._algo_var.get()
            result = pr_run(algo, refs, n)
        except Exception as e:
            self.show_error(str(e))
            return

        self._stat_vars["Page Faults"].set(str(result.page_faults))
        self._stat_vars["Page Hits"].set(str(result.page_hits))
        self._stat_vars["Hit Ratio"].set(f"{result.hit_ratio * 100:.1f}%")
        self._stat_vars["Fault Ratio"].set(f"{result.fault_ratio * 100:.1f}%")

        self._draw_frame_table(result)

    def _draw_frame_table(self, result):
        c = self._frame_canvas
        c.delete("all")

        cell_w, cell_h = 44, 30
        x0, y0         = 16, 16
        n_frames        = result.n_frames

        for col, step in enumerate(result.steps):
            cx = x0 + col * cell_w
            hdr_color = (COLORS["accent_red"] if step.is_fault
                         else COLORS["accent_green"])
            c.create_rectangle(cx, y0, cx + cell_w, y0 + cell_h,
                                fill=hdr_color, outline="#ffffff", width=1)
            c.create_text(cx + cell_w // 2, y0 + cell_h // 2,
                          text=str(step.reference),
                          font=("Segoe UI", 9, "bold"), fill="#ffffff")
            c.create_text(cx + cell_w // 2, y0 + cell_h + 10,
                          text="F" if step.is_fault else "H",
                          font=("Segoe UI", 8, "bold"), fill=hdr_color)
            for row in range(n_frames):
                ry  = y0 + cell_h + 22 + row * cell_h
                val = step.frames[row]
                fill = COLORS["content_bg"] if val is None else "#dbeafe"
                c.create_rectangle(cx, ry, cx + cell_w, ry + cell_h,
                                   fill=fill, outline=COLORS["card_border"])
                if val is not None:
                    c.create_text(cx + cell_w // 2, ry + cell_h // 2,
                                  text=str(val),
                                  font=("Segoe UI", 9),
                                  fill=COLORS["text_primary"])

        total_h = y0 + cell_h + 22 + n_frames * cell_h + 20
        total_w = x0 + len(result.steps) * cell_w + 20
        c.configure(scrollregion=(0, 0, total_w, total_h))

    # ── UI helpers ────────────────────────────────────────────────────────────

    def _sec(self, parent, text):
        f = tk.Frame(parent, bg=COLORS["card_bg"])
        f.pack(fill="x")
        tk.Frame(f, bg=COLORS["accent_green"], width=3).pack(side="left", fill="y")
        tk.Label(f, text=f"  {text}", font=FONTS["sidebar_hd"],
                 bg=COLORS["card_bg"], fg=COLORS["accent_green"],
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