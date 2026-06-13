"""
gui/dashboard.py
----------------
Dashboard page: stat cards, pie chart, bar chart, system info, live clock,
and module overview grid.
matplotlib is optional — falls back to a canvas chart if unavailable.
psutil is optional — falls back gracefully.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
import platform
import getpass
import datetime

from gui.base_page import BasePage
from utils.helpers import COLORS, FONTS

# Optional dependencies
try:
    import psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    _MPL = True
except Exception:
    _MPL = False


class DashboardPage(BasePage):

    def __init__(self, parent: tk.Widget, navigate_cb=None, **kw):
        """
        navigate_cb : callable(page_key: str) — called when a module card
                      "Open" button is clicked.
        """
        super().__init__(parent,
                         title="Dashboard",
                         subtitle="Mini Operating System Simulator — Overview",
                         accent=COLORS["accent_blue"], **kw)
        self._navigate = navigate_cb
        self._after_ids: list[str] = []
        self.build()

    # ── Build ─────────────────────────────────────────────────────────────────

    def build(self):
        outer = tk.Frame(self.body, bg=COLORS["content_bg"])
        outer.pack(fill="both", expand=True)

        cvs = tk.Canvas(outer, bg=COLORS["content_bg"], highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=cvs.yview)
        cvs.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        cvs.pack(side="left", fill="both", expand=True)

        scroll_f = tk.Frame(cvs, bg=COLORS["content_bg"])
        win = cvs.create_window((0, 0), window=scroll_f, anchor="nw")

        scroll_f.bind("<Configure>", lambda e: cvs.configure(
            scrollregion=cvs.bbox("all")))
        cvs.bind("<Configure>",      lambda e: cvs.itemconfig(win, width=e.width))
        cvs.bind("<MouseWheel>",
                     lambda e: cvs.yview_scroll(int(-1*(e.delta/120)), "units"))

        pad = {"padx": 20, "pady": 10}

        self._build_stat_cards(scroll_f, **pad)

        charts_row = tk.Frame(scroll_f, bg=COLORS["content_bg"])
        charts_row.pack(fill="x", **pad)
        self._build_pie_chart(charts_row)
        self._build_bar_chart(charts_row)

        info_row = tk.Frame(scroll_f, bg=COLORS["content_bg"])
        info_row.pack(fill="x", **pad)
        self._build_system_info(info_row)
        self._build_clock(info_row)

        self._build_module_grid(scroll_f, **pad)

        # Start live clock
        self._tick_clock()

    # ── Stat cards ────────────────────────────────────────────────────────────

    def _build_stat_cards(self, parent, **kw):
        row = tk.Frame(parent, bg=COLORS["content_bg"])
        row.pack(fill="x", **kw)

        defs = [
            ("Total Modules",    "7",     "⊞", COLORS["accent_blue"]),
            ("Total Algorithms", "17",    "⚙", COLORS["accent_purple"]),
            ("CPU Utilization",  "—%",    "⚡", COLORS["accent_green"]),
            ("System Status",    "READY", "●", COLORS["accent_teal"]),
        ]
        self._stat_vars: dict[str, tk.StringVar] = {}
        for title, val, icon, accent in defs:
            var = tk.StringVar(value=val)
            self._stat_vars[title] = var
            card = self._make_stat_card(row, title, var, icon, accent)
            card.pack(side="left", expand=True, fill="x", padx=(0, 10))

        self._poll_cpu()

    def _make_stat_card(self, parent, title, var, icon, accent):
        card = tk.Frame(parent, bg=COLORS["card_bg"],
                        highlightbackground=COLORS["card_border"],
                        highlightthickness=1)
        tk.Frame(card, bg=accent, width=4).pack(side="left", fill="y")
        body = tk.Frame(card, bg=COLORS["card_bg"], padx=12, pady=12)
        body.pack(side="left", fill="both", expand=True)
        top = tk.Frame(body, bg=COLORS["card_bg"])
        top.pack(fill="x")
        tk.Label(top, text=icon, font=("Segoe UI", 22),
                 bg=COLORS["card_bg"], fg=accent).pack(side="right")
        tk.Label(body, text=title, font=FONTS["card_lbl"],
                 bg=COLORS["card_bg"], fg=COLORS["text_secondary"]).pack(anchor="w")
        tk.Label(body, textvariable=var, font=FONTS["card_num"],
                 bg=COLORS["card_bg"], fg=accent).pack(anchor="w")
        return card

    def _poll_cpu(self):
        if _PSUTIL:
            try:
                cpu = psutil.cpu_percent(interval=None)
                self._stat_vars["CPU Utilization"].set(f"{cpu:.0f}%")
            except Exception:
                pass
        aid = self.after(2000, self._poll_cpu)
        self._after_ids.append(aid)

    # ── Pie chart ─────────────────────────────────────────────────────────────

    def _build_pie_chart(self, parent):
        card = self._card_frame(parent, "Module Distribution")
        card.pack(side="left", expand=True, fill="both", padx=(0, 10))

        if not _MPL:
            self._fallback_pie(card)
            return

        labels = ["CPU Sched", "Memory", "Page Repl",
                  "Sync", "Deadlock", "File Mgmt"]
        sizes  = [4, 4, 3, 2, 1, 3]
        colors = [COLORS["gantt"][i % len(COLORS["gantt"])]
                  for i in range(len(labels))]

        fig, ax = plt.subplots(figsize=(3.8, 2.8))
        fig.patch.set_facecolor(COLORS["card_bg"])
        ax.set_facecolor(COLORS["card_bg"])
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=colors, autopct="%1.0f%%",
            startangle=140, pctdistance=0.8,
            textprops={"color": COLORS["text_secondary"], "fontsize": 7})
        for at in autotexts:
            at.set_fontsize(7)
            at.set_color(COLORS["text_primary"])
        ax.set_title("Algorithms by Module",
                     color=COLORS["text_primary"], fontsize=9)
        fig.tight_layout(pad=0.5)

        cvs = FigureCanvasTkAgg(fig, master=card)
        cvs.draw()
        cvs.get_tk_widget().configure(bg=COLORS["card_bg"], highlightthickness=0)
        cvs.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)
        plt.close(fig)

    def _fallback_pie(self, card):
        """Simple canvas pie if matplotlib not available."""
        cvs = tk.Canvas(card, bg=COLORS["card_bg"], height=180,
                        highlightthickness=0)
        cvs.pack(fill="both", expand=True, padx=6, pady=6)
        modules = ["CPU(4)", "Mem(4)", "Page(3)", "Sync(2)", "Deadlock(1)", "File(3)"]
        colors  = COLORS["gantt"][:6]
        import math
        cx, cy, r = 110, 90, 70
        total = 17
        vals  = [4, 4, 3, 2, 1, 3]
        start = 0.0
        for i, (v, col) in enumerate(zip(vals, colors)):
            extent = 360 * v / total
            cvs.create_arc(cx - r, cy - r, cx + r, cy + r,
                            start=start, extent=extent,
                            fill=col, outline="#ffffff")
            start += extent
        # legend
        for i, (m, col) in enumerate(zip(modules, colors)):
            lx = 220
            ly = 20 + i * 26
            cvs.create_rectangle(lx, ly, lx+12, ly+12, fill=col, outline="")
            cvs.create_text(lx+16, ly+6, text=m, anchor="w",
                             font=("Segoe UI", 8), fill=COLORS["text_secondary"])

    # ── Bar chart ─────────────────────────────────────────────────────────────

    def _build_bar_chart(self, parent):
        card = self._card_frame(parent, "Algorithms per Module")
        card.pack(side="left", expand=True, fill="both")

        if not _MPL:
            self._fallback_bar(card)
            return

        modules = ["CPU", "Memory", "Paging", "Sync", "Deadlock", "Files"]
        counts  = [4, 4, 3, 2, 1, 3]
        colors  = [COLORS["gantt"][i] for i in range(len(modules))]

        fig, ax = plt.subplots(figsize=(3.8, 2.8))
        fig.patch.set_facecolor(COLORS["card_bg"])
        ax.set_facecolor(COLORS["card_bg"])
        bars = ax.bar(modules, counts, color=colors, edgecolor="white", linewidth=0.5)
        ax.set_ylabel("# Algorithms", color=COLORS["text_secondary"], fontsize=8)
        ax.tick_params(colors=COLORS["text_secondary"], labelsize=7)
        for spine in ax.spines.values():
            spine.set_edgecolor(COLORS["card_border"])
        ax.set_title("Algorithms per Module",
                     color=COLORS["text_primary"], fontsize=9)
        for bar, v in zip(bars, counts):
            ax.text(bar.get_x() + bar.get_width() / 2, v + 0.05,
                    str(v), ha="center", va="bottom",
                    fontsize=7, color=COLORS["text_primary"])
        ax.set_ylim(0, max(counts) + 1)
        fig.tight_layout(pad=0.5)

        cvs = FigureCanvasTkAgg(fig, master=card)
        cvs.draw()
        cvs.get_tk_widget().configure(bg=COLORS["card_bg"], highlightthickness=0)
        cvs.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)
        plt.close(fig)

    def _fallback_bar(self, card):
        cvs = tk.Canvas(card, bg=COLORS["card_bg"], height=180,
                        highlightthickness=0)
        cvs.pack(fill="both", expand=True, padx=6, pady=6)
        modules = ["CPU", "Mem", "Page", "Sync", "Dead", "File"]
        counts  = [4, 4, 3, 2, 1, 3]
        colors  = COLORS["gantt"][:6]
        max_v   = max(counts)
        bw, gap = 30, 12
        x0, y0, chart_h = 20, 10, 130
        for i, (m, v, col) in enumerate(zip(modules, counts, colors)):
            bh = int(chart_h * v / max_v)
            x  = x0 + i * (bw + gap)
            cvs.create_rectangle(x, y0 + chart_h - bh, x + bw, y0 + chart_h,
                                  fill=col, outline="white")
            cvs.create_text(x + bw // 2, y0 + chart_h - bh - 8,
                             text=str(v), font=("Segoe UI", 8),
                             fill=COLORS["text_primary"])
            cvs.create_text(x + bw // 2, y0 + chart_h + 10,
                             text=m, font=("Segoe UI", 7),
                             fill=COLORS["text_secondary"])

    # ── System info ───────────────────────────────────────────────────────────

    def _build_system_info(self, parent):
        card = self._card_frame(parent, "System Information")
        card.pack(side="left", expand=True, fill="both", padx=(0, 10))

        try:
            info = {
                "OS":      platform.system() + " " + platform.release(),
                "Python":  platform.python_version(),
                "User":    getpass.getuser(),
                "Machine": platform.machine(),
            }
        except Exception:
            info = {"OS": "Unknown"}

        body = tk.Frame(card, bg=COLORS["card_bg"], padx=12, pady=8)
        body.pack(fill="both", expand=True)
        for key, val in info.items():
            row = tk.Frame(body, bg=COLORS["card_bg"])
            row.pack(fill="x", pady=3)
            tk.Label(row, text=key + ":", width=9, anchor="w",
                     font=FONTS["body_bold"], bg=COLORS["card_bg"],
                     fg=COLORS["text_secondary"]).pack(side="left")
            tk.Label(row, text=val, anchor="w",
                     font=FONTS["mono"], bg=COLORS["card_bg"],
                     fg=COLORS["text_primary"]).pack(side="left")

    # ── Live clock ────────────────────────────────────────────────────────────

    def _build_clock(self, parent):
        card = self._card_frame(parent, "Live Clock")
        card.pack(side="left", expand=True, fill="both")

        inner = tk.Frame(card, bg=COLORS["card_bg"])
        inner.pack(fill="both", expand=True, pady=10)

        self._time_var = tk.StringVar(value="--:--:--")
        self._date_var = tk.StringVar(value="")

        tk.Label(inner, textvariable=self._time_var,
                 font=("Segoe UI", 28, "bold"),
                 bg=COLORS["card_bg"], fg=COLORS["accent_blue"]).pack(expand=True)
        tk.Label(inner, textvariable=self._date_var,
                 font=FONTS["small"],
                 bg=COLORS["card_bg"], fg=COLORS["text_secondary"]).pack()

    def _tick_clock(self):
        now = datetime.datetime.now()
        if hasattr(self, "_time_var"):
            self._time_var.set(now.strftime("%H:%M:%S"))
            self._date_var.set(now.strftime("%A, %B %d %Y"))
        aid = self.after(1000, self._tick_clock)
        self._after_ids.append(aid)

    # ── Module grid ───────────────────────────────────────────────────────────

    def _build_module_grid(self, parent, **kw):
        tk.Label(parent, text="Available Modules",
                 font=FONTS["subtitle"], bg=COLORS["content_bg"],
                 fg=COLORS["text_primary"], anchor="w").pack(
            fill="x", padx=20, pady=(10, 4))

        grid = tk.Frame(parent, bg=COLORS["content_bg"])
        grid.pack(fill="x", **kw)

        modules = [
            ("CPU Scheduling",         "⚙",  "FCFS · SJF · Round Robin · Priority",       COLORS["accent_blue"],   "cpu"),
            ("Memory Management",      "▦",  "First Fit · Best Fit · Worst Fit · Next Fit",COLORS["accent_purple"], "memory"),
            ("Page Replacement",       "⇄",  "FIFO · LRU · Optimal",                      COLORS["accent_green"],  "page_replacement"),
            ("Process Synchronization","⇌",  "Producer-Consumer · Semaphore · Mutex",      COLORS["accent_orange"], "synchronization"),
            ("Deadlock Handling",      "⊗",  "Banker's Algorithm · Safety · Need Matrix",  COLORS["accent_red"],    "deadlock"),
            ("File Management",        "📁", "Sequential · Linked · Indexed Allocation",   COLORS["accent_teal"],   "file"),
        ]

        for i, (title, icon, desc, accent, key) in enumerate(modules):
            r, c = divmod(i, 3)
            card = tk.Frame(grid, bg=COLORS["card_bg"],
                            highlightbackground=COLORS["card_border"],
                            highlightthickness=1)
            card.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")
            grid.columnconfigure(c, weight=1)

            tk.Frame(card, bg=accent, height=3).pack(fill="x")
            top = tk.Frame(card, bg=COLORS["card_bg"], padx=12, pady=10)
            top.pack(fill="x")
            tk.Label(top, text=icon, font=("Segoe UI", 18),
                     bg=COLORS["card_bg"], fg=accent).pack(side="left", padx=(0, 8))
            tk.Label(top, text=title, font=FONTS["body_bold"],
                     bg=COLORS["card_bg"], fg=COLORS["text_primary"],
                     anchor="w").pack(side="left")
            tk.Label(card, text=desc, font=FONTS["small"],
                     bg=COLORS["card_bg"], fg=COLORS["text_secondary"],
                     anchor="w", padx=12, wraplength=200,
                     justify="left").pack(fill="x", pady=(0, 4))

            # Open button
            btn_bg    = COLORS["card_bg"]
            btn_hover = "#f0f4ff"
            open_btn  = tk.Button(
                card, text="Open  ›",
                bg=btn_bg, fg=accent,
                activebackground=btn_hover, activeforeground=accent,
                relief="flat", bd=0, font=FONTS["body_bold"],
                padx=12, pady=8, anchor="w", cursor="hand2",
                command=lambda k=key: self._navigate(k) if self._navigate else None
            )
            open_btn.pack(fill="x", pady=(0, 8), padx=12)

    # ── Card frame helper ─────────────────────────────────────────────────────

    def _card_frame(self, parent, title: str) -> tk.Frame:
        card = tk.Frame(parent, bg=COLORS["card_bg"],
                        highlightbackground=COLORS["card_border"],
                        highlightthickness=1)
        tk.Label(card, text=title, font=FONTS["body_bold"],
                 bg=COLORS["card_bg"], fg=COLORS["text_primary"],
                 anchor="w", padx=12, pady=8).pack(fill="x")
        tk.Frame(card, bg=COLORS["card_border"], height=1).pack(fill="x")
        return card

    def destroy(self):
        for aid in self._after_ids:
            try:
                self.after_cancel(aid)
            except Exception:
                pass
        super().destroy()