"""
gui/base_page.py
----------------
BasePage: every module page inherits from this.
Provides a standard header + scrollable content area.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from utils.helpers import COLORS, FONTS


class BasePage(tk.Frame):
    """
    Standard page layout:
        ┌─ header bar (title + subtitle) ──────────────────────┐
        │ thin accent line                                       │
        └─ body (scrollable if needed) ─────────────────────────┘
    """

    PAGE_BG = COLORS["content_bg"]

    def __init__(self, parent: tk.Widget, title: str,
                 subtitle: str = "", accent: str = COLORS["accent_blue"],
                 **kw):
        super().__init__(parent, bg=self.PAGE_BG, **kw)
        self._accent = accent
        self._build_header(title, subtitle, accent)
        # Body frame — subclasses pack/grid widgets here
        self.body = tk.Frame(self, bg=self.PAGE_BG)
        self.body.pack(fill="both", expand=True)
     

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self, title: str, subtitle: str, accent: str):
        hdr = tk.Frame(self, bg=COLORS["card_bg"],
                       highlightbackground=COLORS["card_border"],
                       highlightthickness=1)
        hdr.pack(fill="x", side="top")

        inner = tk.Frame(hdr, bg=COLORS["card_bg"])
        inner.pack(fill="x", padx=20, pady=12)

        # Left accent bar
        tk.Frame(inner, bg=accent, width=4).pack(side="left", fill="y", padx=(0, 12))

        text_col = tk.Frame(inner, bg=COLORS["card_bg"])
        text_col.pack(side="left", fill="y")

        tk.Label(text_col, text=title, font=FONTS["title"],
                 bg=COLORS["card_bg"], fg=COLORS["text_primary"],
                 anchor="w").pack(anchor="w")

        if subtitle:
            tk.Label(text_col, text=subtitle, font=FONTS["small"],
                     bg=COLORS["card_bg"],
                     fg=COLORS["text_secondary"], anchor="w").pack(anchor="w")

        # Thin bottom accent line
        tk.Frame(hdr, bg=accent, height=2).pack(fill="x", side="bottom")

    # ── Error / info helpers ──────────────────────────────────────────────────

    def show_error(self, msg: str):
        messagebox.showerror("Error", msg, parent=self)

    def show_info(self, msg: str):
        messagebox.showinfo("Info", msg, parent=self)

        # ── Reusable UI Helpers ───────────────────────────────────────────────

    def _sec(self, parent, text):
        frame = tk.Frame(parent, bg=COLORS["card_bg"])
        frame.pack(fill="x")

        tk.Frame(
            frame,
            bg=self._accent,
            width=3
        ).pack(side="left", fill="y")

        tk.Label(
            frame,
            text=f"  {text}",
            font=FONTS.get("sidebar_hd", ("Segoe UI", 10, "bold")),
            bg=COLORS["card_bg"],
            fg=self._accent,
            pady=5
        ).pack(side="left")

    def _divider(self, parent):
        tk.Frame(
            parent,
            bg=COLORS["card_border"],
            height=1
        ).pack(fill="x", pady=4)

    def _card(self, parent, title: str):
        card = tk.Frame(
            parent,
            bg=COLORS["card_bg"],
            highlightbackground=COLORS["card_border"],
            highlightthickness=1
        )

        tk.Label(
            card,
            text=title,
            font=FONTS.get("body_bold", ("Segoe UI", 10, "bold")),
            bg=COLORS["card_bg"],
            fg=COLORS["text_primary"],
            anchor="w",
            padx=10,
            pady=6
        ).pack(fill="x")

        tk.Frame(
            card,
            bg=COLORS["card_border"],
            height=1
        ).pack(fill="x")

        return card

    def _mini_stat(self, parent, title, var, accent):
        card = tk.Frame(
            parent,
            bg=COLORS["card_bg"],
            highlightbackground=accent,
            highlightthickness=1
        )

        tk.Label(
            card,
            text=title,
            font=FONTS.get("card_lbl", ("Segoe UI", 9)),
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"]
        ).pack(pady=(6, 0))

        tk.Label(
            card,
            textvariable=var,
            font=("Segoe UI", 14, "bold"),
            bg=COLORS["card_bg"],
            fg=accent
        ).pack(pady=(0, 6))

        return card
    # ── Subclass hook — called after __init__ to build page body ──────────────

    def build(self):
        """Override in subclasses to populate self.body."""
        pass