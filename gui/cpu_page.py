"""
gui/cpu_page.py
---------------
CPU Scheduling module UI — FCFS, SJF, Priority, Round Robin.
"""

from __future__ import annotations
import datetime
import tkinter as tk
from tkinter import ttk

from gui.base_page import BasePage
from utils.helpers import COLORS, FONTS
from utils.visualizations import ResultTable, ModernButton
from modules.cpu_scheduling import Process, fcfs, sjf, priority_sched, round_robin


class CPUPage(BasePage):

    ALGORITHMS = {
        "FCFS — First Come First Serve": "fcfs",
        "SJF  — Shortest Job First":     "sjf",
        "Priority Scheduling":           "priority",
        "Round Robin":                   "rr",
    }

    def __init__(self, parent: tk.Widget, **kw):
        super().__init__(parent,
                         title="CPU Scheduling",
                         subtitle="FCFS · SJF · Priority · Round Robin — Gantt Chart",
                         accent=COLORS["accent_blue"], **kw)
        self._processes: list[dict] = []
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
                         highlightthickness=1, width=290)
        frame.pack_propagate(False)

        self._sec(frame, "Algorithm")
        self._algo_var = tk.StringVar(value=list(self.ALGORITHMS.keys())[0])
        cb = ttk.Combobox(frame, textvariable=self._algo_var,
                          values=list(self.ALGORITHMS.keys()),
                          state="readonly", width=30)
        cb.pack(fill="x", padx=12, pady=(0, 6))
        cb.bind("<<ComboboxSelected>>", self._on_algo_change)

        qrow = tk.Frame(frame, bg=COLORS["card_bg"])
        qrow.pack(fill="x", padx=12, pady=4)
        tk.Label(qrow, text="Time Quantum:", font=FONTS["small"],
                 bg=COLORS["card_bg"], fg=COLORS["text_secondary"]).pack(side="left")
        self._quantum_var    = tk.StringVar(value="2")
        self._quantum_entry  = ttk.Entry(qrow, textvariable=self._quantum_var, width=6)
        self._quantum_entry.pack(side="left", padx=6)
        self._quantum_entry.configure(state="disabled")

        self._divider(frame)
        self._sec(frame, "Add Process")

        form = tk.Frame(frame, bg=COLORS["card_bg"], padx=12)
        form.pack(fill="x")
        for label, attr, default in [
            ("PID",      "_pid_var",      "P1"),
            ("Arrival",  "_arrival_var",  "0"),
            ("Burst",    "_burst_var",    "4"),
            ("Priority", "_priority_var", "1"),
        ]:
            row = tk.Frame(form, bg=COLORS["card_bg"])
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label, width=8, anchor="w",
                     font=FONTS["small"], bg=COLORS["card_bg"],
                     fg=COLORS["text_secondary"]).pack(side="left")
            var = tk.StringVar(value=default)
            setattr(self, attr, var)
            ttk.Entry(row, textvariable=var, width=14).pack(side="left", padx=4)

        btn_row = tk.Frame(form, bg=COLORS["card_bg"])
        btn_row.pack(fill="x", pady=8)
        ModernButton(btn_row, "+ Add",    command=self._add_proc,    variant="success").pack(side="left", padx=(0, 4))
        ModernButton(btn_row, "✕ Delete", command=self._del_proc,    variant="danger").pack(side="left", padx=(0, 4))
        ModernButton(btn_row, "Clear",    command=self._clear_procs, variant="ghost").pack(side="left")

        self._divider(frame)
        self._sec(frame, "Process Queue")
        self._proc_table = ResultTable(
            frame,
            columns=[("PID", "pid", 60), ("AT", "at", 55),
                     ("BT",  "bt",  55), ("Pri","pr", 50)],
        )
        self._proc_table.pack(fill="x", padx=12, pady=4, ipady=4)

        self._divider(frame)
        ModernButton(frame, "Load Sample Data",
                     command=self._load_sample, variant="outline").pack(
            fill="x", padx=12, pady=4)
        ModernButton(frame, "▶  Run Simulation",
                     command=self._run, variant="primary").pack(
            fill="x", padx=12, pady=(4, 12))
        return frame

    # ── RIGHT ─────────────────────────────────────────────────────────────────

    def _build_right(self, parent) -> tk.Frame:
        frame = tk.Frame(parent, bg=COLORS["content_bg"])

        stat_row = tk.Frame(frame, bg=COLORS["content_bg"])
        stat_row.pack(fill="x", pady=(0, 10))
        self._stat_vars: dict[str, tk.StringVar] = {}
        for title, accent in [
            ("Avg Waiting",    COLORS["accent_blue"]),
            ("Avg Turnaround", COLORS["accent_purple"]),
            ("CPU Util %",     COLORS["accent_green"]),
            ("Throughput",     COLORS["accent_teal"]),
        ]:
            var = tk.StringVar(value="—")
            self._stat_vars[title] = var
            c = self._mini_stat(stat_row, title, var, accent)
            c.pack(side="left", expand=True, fill="x", padx=(0, 8))

        res_card = self._card(frame, "Results Table")
        res_card.pack(fill="x", pady=(0, 10))
        self._result_table = ResultTable(
            res_card,
            columns=[
                ("PID","pid",60), ("AT","at",60), ("BT","bt",60),
                ("Pri","pr", 50), ("CT","ct",80), ("TAT","tat",80),
                ("WT", "wt",80),  ("RT","rt",80),
            ],
        )
        self._result_table.pack(fill="x", padx=10, pady=8, ipady=6)

        gantt_card = self._card(frame, "Gantt Chart")
        gantt_card.pack(fill="x")
        gantt_wrap = tk.Frame(gantt_card, bg=COLORS["card_bg"])
        gantt_wrap.pack(fill="x", padx=10, pady=8)
        hscroll = ttk.Scrollbar(gantt_wrap, orient="horizontal")
        hscroll.pack(side="bottom", fill="x")
        self._gantt_canvas = tk.Canvas(
            gantt_wrap, bg=COLORS["canvas_bg"], height=90,
            xscrollcommand=hscroll.set, highlightthickness=0)
        self._gantt_canvas.pack(fill="x")
        hscroll.config(command=self._gantt_canvas.xview)

        log_card = self._card(frame, "Execution Log")
        log_card.pack(fill="x", pady=(10, 0))
        self._log = tk.Text(
            log_card, height=5, bg=COLORS["sidebar_bg"],
            fg=COLORS["sidebar_text"], font=FONTS["mono_small"],
            relief="flat", state="disabled", padx=8, pady=6)
        self._log.pack(fill="x", padx=10, pady=6)
        return frame

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_algo_change(self, _=None):
        key   = self.ALGORITHMS.get(self._algo_var.get(), "")
        state = "normal" if key == "rr" else "disabled"
        self._quantum_entry.configure(state=state)

    def _add_proc(self):
        try:
            pid = self._pid_var.get().strip()
            if not pid:
                raise ValueError("PID cannot be empty.")
            at  = int(self._arrival_var.get())
            bt  = int(self._burst_var.get())
            pri = int(self._priority_var.get())
            if bt <= 0:  raise ValueError("Burst time must be > 0.")
            if at < 0:   raise ValueError("Arrival time must be >= 0.")
            if any(p["pid"] == pid for p in self._processes):
                raise ValueError(f"PID '{pid}' already exists.")
            self._processes.append({"pid": pid, "at": at, "bt": bt, "priority": pri})
            self._refresh_proc_table()
            try:
                n = int(pid[1:]) + 1
                self._pid_var.set(f"P{n}")
            except Exception:
                pass
        except ValueError as e:
            self.show_error(str(e))

    def _del_proc(self):
        sel = self._proc_table.tree.selection()
        if not sel:
            return
        idx = self._proc_table.tree.index(sel[0])
        del self._processes[idx]
        self._refresh_proc_table()

    def _clear_procs(self):
        self._processes.clear()
        self._refresh_proc_table()

    def _load_sample(self):
        self._processes = [
            {"pid": "P1", "at": 0, "bt": 6, "priority": 3},
            {"pid": "P2", "at": 1, "bt": 8, "priority": 1},
            {"pid": "P3", "at": 2, "bt": 7, "priority": 4},
            {"pid": "P4", "at": 3, "bt": 3, "priority": 2},
            {"pid": "P5", "at": 4, "bt": 4, "priority": 5},
        ]
        self._refresh_proc_table()
        self._log_msg("Sample data loaded (5 processes).")

    def _refresh_proc_table(self):
        self._proc_table.clear()
        for p in self._processes:
            self._proc_table.insert([p["pid"], p["at"], p["bt"], p["priority"]])

    def _run(self):
        if not self._processes:
            self.show_error("Add at least one process.")
            return
        algo_label = self._algo_var.get()
        algo_key   = self.ALGORITHMS[algo_label]
        procs      = [Process(p["pid"], p["at"], p["bt"], p["priority"])
                      for p in self._processes]
        try:
            if   algo_key == "fcfs":     results, gantt, avg_wt, avg_tat = fcfs(procs)
            elif algo_key == "sjf":      results, gantt, avg_wt, avg_tat = sjf(procs)
            elif algo_key == "priority": results, gantt, avg_wt, avg_tat = priority_sched(procs)
            elif algo_key == "rr":
                q = int(self._quantum_var.get())
                if q < 1: raise ValueError("Quantum must be >= 1.")
                results, gantt, avg_wt, avg_tat = round_robin(procs, q)
            else:
                return
        except Exception as e:
            self.show_error(str(e))
            return

        self._result_table.clear()
        for r in results:
            self._result_table.insert([
                r["pid"], r["at"], r["bt"], r["priority"],
                r["ct"],  r["tat"], r["wt"], r["rt"],
            ])

        span = (gantt[-1][2] - gantt[0][1]) if gantt else 1
        util = round((sum(r["bt"] for r in results) / span * 100) if span > 0 else 100.0, 1)
        thr  = round(len(results) / span, 3) if span > 0 else 0

        self._stat_vars["Avg Waiting"].set(f"{avg_wt:.2f}")
        self._stat_vars["Avg Turnaround"].set(f"{avg_tat:.2f}")
        self._stat_vars["CPU Util %"].set(f"{util}%")
        self._stat_vars["Throughput"].set(str(thr))

        self._draw_gantt(gantt)
        self._log_msg(f"[{algo_label}]  Processes: {len(results)} | "
                      f"AvgWT: {avg_wt} | AvgTAT: {avg_tat} | CPU: {util}%")

    def _draw_gantt(self, gantt: list):
        self._gantt_canvas.delete("all")
        if not gantt:
            return
        colors    = COLORS["gantt"]
        pid_color: dict[str, str] = {}
        color_idx = 0
        total_span = gantt[-1][2] - gantt[0][1]
        SCALE = max(10, min(60, int(700 / max(total_span, 1))))
        BAR_Y1, BAR_Y2, TS_Y = 14, 58, 74
        x = 20
        drawn_ts: set[int] = set()
        for pid, start, end in gantt:
            if pid not in pid_color:
                pid_color[pid] = colors[color_idx % len(colors)]
                color_idx += 1
            col   = pid_color[pid]
            seg_w = max((end - start) * SCALE, 12)
            self._gantt_canvas.create_rectangle(
                x, BAR_Y1, x + seg_w, BAR_Y2,
                fill=col, outline="#ffffff", width=1.5)
            if seg_w > 20:
                self._gantt_canvas.create_text(
                    x + seg_w / 2, (BAR_Y1 + BAR_Y2) / 2,
                    text=str(pid), fill="#ffffff",
                    font=("Segoe UI", 8, "bold"))
            if start not in drawn_ts:
                self._gantt_canvas.create_text(
                    x, TS_Y, text=str(start),
                    font=("Segoe UI", 7), fill=COLORS["text_secondary"])
                drawn_ts.add(start)
            x += seg_w
        if gantt:
            self._gantt_canvas.create_text(
                x, TS_Y, text=str(gantt[-1][2]),
                font=("Segoe UI", 7), fill=COLORS["text_secondary"])
        self._gantt_canvas.configure(scrollregion=(0, 0, x + 30, 90))

    def _log_msg(self, msg: str):
        self._log.configure(state="normal")
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self._log.insert("end", f"[{ts}] {msg}\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    # ── UI helpers ────────────────────────────────────────────────────────────

    def _sec(self, parent, text):
        f = tk.Frame(parent, bg=COLORS["card_bg"])
        f.pack(fill="x")
        tk.Frame(f, bg=COLORS["accent_blue"], width=3).pack(side="left", fill="y")
        tk.Label(f, text=f"  {text}", font=FONTS["sidebar_hd"],
                 bg=COLORS["card_bg"], fg=COLORS["accent_blue"],
                 pady=5).pack(side="left")

    def _divider(self, parent):
        tk.Frame(parent, bg=COLORS["card_border"], height=1).pack(fill="x", pady=6)

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
        tk.Label(card, textvariable=var, font=("Segoe UI", 15, "bold"),
                 bg=COLORS["card_bg"], fg=accent).pack(pady=(0, 6))
        return card