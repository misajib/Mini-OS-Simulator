"""
gui/memory_page.py
------------------
Memory Management module UI — First Fit, Best Fit, Worst Fit, Next Fit + Paging.
Professional dashboard redesign:
  • Fragmentation Analysis Graph (modern, responsive, labelled)
  • Fixed Paging Result card (scrollable, terminal-style)
  • Side-by-side Frag Graph | Allocation Table
  • Paging Result below
  • Improved Allocation Table with proper headings & scrollbars
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk

from gui.base_page import BasePage
from utils.helpers import COLORS, FONTS, parse_int_list
from utils.visualizations import ModernButton, ResultTable
from modules.memory_management import allocate, paging


# ─── palette constants used inside this file ──────────────────────────────────
_C_INT_FRAG  = "#E8624A"   # warm red  – internal fragmentation bars
_C_FREE      = "#5A6478"   # steel grey – free / unallocated blocks
_C_USED      = "#6C63FF"   # indigo    – process used space
_C_GRID      = "#2E3448"   # subtle grid lines on canvas
_C_AXIS_TXT  = "#8B92A5"   # muted axis labels
_C_BAR_GLOW  = "#A89CFF"   # highlight top edge of used bars
_C_CANVAS_BG = "#1A1E2E"   # dark canvas background


class MemoryPage(BasePage):

    ALGORITHMS = {
        "First Fit": "first_fit",
        "Best Fit":  "best_fit",
        "Worst Fit": "worst_fit",
        "Next Fit":  "next_fit",
    }

    def __init__(self, parent: tk.Widget, **kw):
        super().__init__(parent,
                         title="Memory Management",
                         subtitle="First Fit · Best Fit · Worst Fit · Next Fit — Canvas Visualization",
                         accent=COLORS["accent_purple"], **kw)
        self.build()

    # ══════════════════════════════════════════════════════════════════════════
    # TOP-LEVEL BUILD
    # ══════════════════════════════════════════════════════════════════════════

    def build(self):
        outer = tk.Frame(self.body, bg=COLORS["content_bg"])
        outer.pack(fill="both", expand=True, padx=12, pady=10)
        outer.columnconfigure(1, weight=1)
        outer.rowconfigure(0, weight=1)

        # left control panel
        self._build_left(outer).grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # right content area
        right = tk.Frame(outer, bg=COLORS["content_bg"])
        right.grid(row=0, column=1, sticky="nsew")
        self._build_right(right)

    # ══════════════════════════════════════════════════════════════════════════
    # LEFT PANEL – controls
    # ══════════════════════════════════════════════════════════════════════════

    def _build_left(self, parent) -> tk.Frame:
        frame = tk.Frame(parent, bg=COLORS["card_bg"],
                         highlightbackground=COLORS["card_border"],
                         highlightthickness=1, width=285)
        frame.pack_propagate(False)

        # ── Algorithm ──────────────────────────────────────────────────────
        self._sec(frame, "Algorithm")
        self._algo_var = tk.StringVar(value="First Fit")
        for name in self.ALGORITHMS:
            tk.Radiobutton(
                frame, text=name, variable=self._algo_var, value=name,
                bg=COLORS["card_bg"], fg=COLORS["text_primary"],
                selectcolor=COLORS["content_bg"],
                activebackground=COLORS["card_bg"],
                font=FONTS["body"]
            ).pack(anchor="w", padx=18, pady=2)

        self._divider(frame)

        # ── Memory Blocks ─────────────────────────────────────────────────
        self._sec(frame, "Memory Blocks (KB)")
        self._blocks_var = tk.StringVar(value="100 500 200 300 600")
        ttk.Entry(frame, textvariable=self._blocks_var, width=28).pack(
            fill="x", padx=12, pady=(4, 8))

        # ── Process Sizes ─────────────────────────────────────────────────
        self._sec(frame, "Process Sizes (KB)")
        self._procs_var = tk.StringVar(value="212 417 112 426")
        ttk.Entry(frame, textvariable=self._procs_var, width=28).pack(
            fill="x", padx=12, pady=(4, 8))

        self._divider(frame)

        # ── Paging Simulation ─────────────────────────────────────────────
        self._sec(frame, "Paging Simulation")
        pform = tk.Frame(frame, bg=COLORS["card_bg"], padx=12)
        pform.pack(fill="x", pady=4)
        for label, attr, default in [
            ("Process KB:", "_psize_var",   "256"),
            ("Page KB:",    "_pgsize_var",  "64"),
            ("Memory KB:",  "_memsize_var", "1024"),
        ]:
            row = tk.Frame(pform, bg=COLORS["card_bg"])
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label, width=11, anchor="w",
                     font=FONTS["small"], bg=COLORS["card_bg"],
                     fg=COLORS["text_secondary"]).pack(side="left")
            var = tk.StringVar(value=default)
            setattr(self, attr, var)
            ttk.Entry(row, textvariable=var, width=10).pack(side="left")

        ModernButton(frame, "▶  Run Paging",
                     command=self._run_paging, variant="outline").pack(
            fill="x", padx=12, pady=4)

        self._divider(frame)

        ModernButton(frame, "Load Sample Data",
                     command=self._load_sample, variant="outline").pack(
            fill="x", padx=12, pady=4)
        ModernButton(frame, "▶  Run Allocation",
                     command=self._run, variant="primary").pack(
            fill="x", padx=12, pady=(4, 12))

        return frame

    # ══════════════════════════════════════════════════════════════════════════
    # RIGHT PANEL – stats + visualization + tables
    # ══════════════════════════════════════════════════════════════════════════

    def _build_right(self, frame: tk.Frame):
        frame.columnconfigure(0, weight=1)
        # rows: stats(0) | vis(1) | mid-row(2) | paging(3)
        frame.rowconfigure(2, weight=1)

        # ── Row 0: stat cards ─────────────────────────────────────────────
        stat_row = tk.Frame(frame, bg=COLORS["content_bg"])
        stat_row.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        stat_row.columnconfigure((0, 1, 2, 3), weight=1)

        self._stat_vars: dict[str, tk.StringVar] = {}
        for col, (title, accent) in enumerate([
            ("Memory Util %", COLORS["accent_purple"]),
            ("Internal Frag", _C_INT_FRAG),
            ("External Frag", COLORS["accent_red"]),
            ("Unallocated",   COLORS["accent_blue"]),
        ]):
            var = tk.StringVar(value="—")
            self._stat_vars[title] = var
            card = self._mini_stat(stat_row, title, var, accent)
            card.grid(row=0, column=col, sticky="ew", padx=(0, 8 if col < 3 else 0))

        # ── Row 1: memory block visualization ────────────────────────────
        vis_card = self._card(frame, "Memory Block Visualization")
        vis_card.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self._mem_canvas = tk.Canvas(vis_card, bg=COLORS["canvas_bg"],
                                     height=120, highlightthickness=0)
        self._mem_canvas.pack(fill="x", padx=10, pady=10)
        self._mem_canvas.bind("<Configure>", lambda e: self._redraw_if_result())

        # ── Row 2: frag graph (left) + allocation table (right) ──────────
        mid = tk.Frame(frame, bg=COLORS["content_bg"])
        mid.grid(row=2, column=0, sticky="nsew", pady=(0, 8))
        mid.columnconfigure(0, weight=3)
        mid.columnconfigure(1, weight=2)
        mid.rowconfigure(0, weight=1)

        # ── Fragmentation Analysis Graph ─────────────────────────────────
        frag_card = self._card(mid, "Fragmentation Analysis")
        frag_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        frag_card.rowconfigure(2, weight=1)

        # legend
        legend = tk.Frame(frag_card, bg=COLORS["card_bg"])
        legend.pack(fill="x", padx=12, pady=(4, 2))
        for lbl, color in [
            ("Internal Frag", _C_INT_FRAG),
            ("Free Block",    _C_FREE),
            ("Used Space",    _C_USED),
        ]:
            dot = tk.Canvas(legend, width=12, height=12,
                            bg=COLORS["card_bg"], highlightthickness=0)
            dot.create_rectangle(1, 1, 11, 11, fill=color, outline="")
            dot.pack(side="left", padx=(0, 3))
            tk.Label(legend, text=lbl, font=FONTS["small"],
                     bg=COLORS["card_bg"],
                     fg=COLORS["text_secondary"]).pack(side="left", padx=(0, 14))

        frag_wrap = tk.Frame(frag_card, bg=_C_CANVAS_BG)
        frag_wrap.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self._frag_canvas = tk.Canvas(frag_wrap, bg=_C_CANVAS_BG,
                                      highlightthickness=0)
        self._frag_canvas.pack(fill="both", expand=True)
        self._frag_canvas.bind("<Configure>",
                               lambda e: self._redraw_frag_if_result())

        # ── Allocation Table ───────────────────────────────────────────────
        tbl_card = self._card(mid, "Allocation Table")
        tbl_card.grid(row=0, column=1, sticky="nsew")
        self._build_alloc_table(tbl_card)

        # ── Row 3: unallocated label ───────────────────────────────────────
        self._unalloc_label = tk.Label(
            frame, text="", font=FONTS["body"],
            bg=COLORS["content_bg"], fg=COLORS["text_secondary"],
            anchor="w", padx=4)
        self._unalloc_label.grid(row=3, column=0, sticky="ew")

        # ── Row 4: paging result ──────────────────────────────────────────
        pg_card = self._card(frame, "Paging Result")
        pg_card.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        self._build_paging_result(pg_card)

    # ── Allocation Table (Treeview with scrollbars) ───────────────────────────

    def _build_alloc_table(self, parent: tk.Frame):
        cols = ("pid", "sz", "bk", "bsz", "frag")
        headers = {
            "pid":  "Process",
            "sz":   "Size (KB)",
            "bk":   "Block ID",
            "bsz":  "Block (KB)",
            "frag": "Int Frag (KB)",
        }

        container = tk.Frame(parent, bg=COLORS["card_bg"])
        container.pack(fill="both", expand=True, padx=8, pady=8)

        style = ttk.Style()
        style.configure("Alloc.Treeview",
                        background=COLORS["canvas_bg"],
                        foreground=COLORS["text_primary"],
                        fieldbackground=COLORS["canvas_bg"],
                        rowheight=28,
                        font=FONTS["body"])
        style.configure("Alloc.Treeview.Heading",
                        background=COLORS["card_bg"],
                        foreground=COLORS["accent_purple"],
                        font=FONTS["body_bold"],
                        relief="flat")
        style.map("Alloc.Treeview",
                  background=[("selected", COLORS["accent_purple"])],
                  foreground=[("selected", "#ffffff")])

        self._tree = ttk.Treeview(container, columns=cols, show="headings",
                                  style="Alloc.Treeview")
        for col in cols:
            self._tree.heading(col, text=headers[col], anchor="center")
            self._tree.column(col, width=90, minwidth=70, anchor="center",
                              stretch=True)

        vsb = ttk.Scrollbar(container, orient="vertical",
                            command=self._tree.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal",
                            command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set,
                             xscrollcommand=hsb.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        # alternating row tags
        self._tree.tag_configure("odd",  background="#1E2233")
        self._tree.tag_configure("even", background=COLORS["canvas_bg"])
        self._tree.tag_configure("frag_hi",
                                 foreground=_C_INT_FRAG, font=FONTS["body_bold"])

    # ── Paging Result (Text widget, scrollable, terminal-style) ──────────────

    def _build_paging_result(self, parent: tk.Frame):
        container = tk.Frame(parent, bg="#0D1117")
        container.pack(fill="x", padx=10, pady=(0, 10))

        vsb = ttk.Scrollbar(container, orient="vertical")
        hsb = ttk.Scrollbar(container, orient="horizontal")

        self._paging_text = tk.Text(
            container,
            height=12,
            bg="#0D1117",
            fg="#C9D1D9",
            font=("Consolas", 10) if self._font_available("Consolas")
                 else ("Courier", 10),
            relief="flat",
            state="disabled",
            padx=12,
            pady=8,
            insertbackground="#58A6FF",
            selectbackground="#1F6FEB",
            wrap="none",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
        )

        vsb.config(command=self._paging_text.yview)
        hsb.config(command=self._paging_text.xview)

        self._paging_text.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        # colour tags for syntax-style highlighting
        self._paging_text.tag_configure("header",
                                        foreground="#58A6FF",
                                        font=("Consolas", 10, "bold"))
        self._paging_text.tag_configure("key",
                                        foreground="#79C0FF")
        self._paging_text.tag_configure("value",
                                        foreground="#C9D1D9")
        self._paging_text.tag_configure("sep",
                                        foreground="#3D444D")
        self._paging_text.tag_configure("page_entry",
                                        foreground="#7EE787")
        self._paging_text.tag_configure("frag_val",
                                        foreground=_C_INT_FRAG)

        # placeholder
        self._paging_text_insert(
            "  Run Paging Simulation to see results here…", "sep")

    # ══════════════════════════════════════════════════════════════════════════
    # CALLBACKS
    # ══════════════════════════════════════════════════════════════════════════

    def _load_sample(self):
        self._blocks_var.set("100 500 200 300 600")
        self._procs_var.set("212 417 112 426")
        self._algo_var.set("First Fit")

    def _run(self):
        try:
            block_sizes   = parse_int_list(self._blocks_var.get(), "Blocks")
            process_sizes = parse_int_list(self._procs_var.get(), "Processes")
            algo_key      = self.ALGORITHMS[self._algo_var.get()]
            result        = allocate(algo_key, block_sizes, process_sizes)
        except Exception as e:
            self.show_error(str(e))
            return

        self._last_result = result   # store for resize redraws

        self._stat_vars["Memory Util %"].set(f"{result.memory_utilisation:.1f}%")
        self._stat_vars["Internal Frag"].set(f"{result.total_internal_frag} KB")
        self._stat_vars["External Frag"].set(f"{result.total_external_frag} KB")
        self._stat_vars["Unallocated"].set(str(len(result.unallocated)))

        self._draw_memory(result)
        self._draw_frag_graph(result)
        self._populate_alloc_table(result)

        if result.unallocated:
            self._unalloc_label.config(
                text="⚠  Unallocated: " + ", ".join(result.unallocated),
                fg=COLORS["accent_red"])
        else:
            self._unalloc_label.config(
                text="✓  All processes allocated successfully",
                fg=COLORS["accent_green"])

    def _run_paging(self):
        try:
            ps  = int(self._psize_var.get())
            pg  = int(self._pgsize_var.get())
            mem = int(self._memsize_var.get())
            r   = paging(ps, pg, mem)
        except Exception as e:
            self.show_error(str(e))
            return

        # ── build coloured content ─────────────────────────────────────────
        self._paging_text.configure(state="normal")
        self._paging_text.delete("1.0", "end")

        sep = "─" * 42 + "\n"

        def kv(key, val, val_tag="value"):
            self._paging_text.insert("end", f"  {key:<22}", "key")
            self._paging_text.insert("end", f"{val}\n", val_tag)

        self._paging_text.insert("end",
            "  ╔══════════════════════════════════════╗\n"
            "  ║        PAGING SIMULATION RESULT      ║\n"
            "  ╚══════════════════════════════════════╝\n", "header")
        self._paging_text.insert("end", "  " + sep, "sep")

        kv("Process Size",   f"{r.process_size} KB")
        kv("Page Size",      f"{r.page_size} KB")
        kv("Memory Size",    f"{r.memory_size} KB")
        self._paging_text.insert("end", "  " + sep, "sep")

        kv("Total Pages",    str(r.total_pages))
        kv("Total Frames",   str(r.total_frames))
        kv("Used Frames",    str(r.used_frames))
        kv("Free Frames",    str(r.free_frames))
        kv("Internal Frag",  f"{r.internal_frag} KB", "frag_val")
        self._paging_text.insert("end", "  " + sep, "sep")

        self._paging_text.insert("end",
            "  Page Table Mapping\n", "header")
        self._paging_text.insert("end", "  " + sep, "sep")
        self._paging_text.insert("end",
            f"  {'Page':>6}   →   {'Frame':<6}\n", "key")
        self._paging_text.insert("end", "  " + sep, "sep")

        for entry in r.page_table:
            self._paging_text.insert(
                "end",
                f"  {'P' + str(entry.page_no):>6}   →   "
                f"{'F' + str(entry.frame_no):<6}\n",
                "page_entry")

        self._paging_text.configure(state="disabled")
        self._paging_text.see("1.0")   # scroll to top

    # ══════════════════════════════════════════════════════════════════════════
    # DRAWING
    # ══════════════════════════════════════════════════════════════════════════

    def _draw_memory(self, result):
        c = self._mem_canvas
        c.delete("all")
        c.update_idletasks()
        w = c.winfo_width() or 700
        blocks    = result.blocks
        total_mem = sum(b.block_size for b in blocks)
        if total_mem == 0:
            return
        pad_x, pad_y, bar_h = 10, 20, 60
        scale = (w - pad_x * 2) / total_mem
        x = pad_x
        for i, blk in enumerate(blocks):
            bw = blk.block_size * scale
            if blk.allocated_to:
                proc_w = blk.process_size * scale
                frag_w = bw - proc_w
                fill   = COLORS["gantt"][i % len(COLORS["gantt"])]
                c.create_rectangle(x, pad_y, x + proc_w, pad_y + bar_h,
                                   fill=fill, outline="#ffffff", width=1.5)
                if proc_w > 24:
                    c.create_text(x + proc_w / 2, pad_y + bar_h / 2,
                                  text=f"{blk.allocated_to}\n{blk.process_size}K",
                                  font=("Segoe UI", 7, "bold"), fill="#ffffff",
                                  justify="center")
                if frag_w > 2:
                    c.create_rectangle(x + proc_w, pad_y,
                                       x + proc_w + frag_w, pad_y + bar_h,
                                       fill=_C_INT_FRAG,
                                       outline="#ffffff", width=1)
            else:
                c.create_rectangle(x, pad_y, x + bw, pad_y + bar_h,
                                   fill=_C_FREE,
                                   outline="#ffffff", width=1.5)
                if bw > 24:
                    c.create_text(x + bw / 2, pad_y + bar_h / 2,
                                  text=f"Free\n{blk.block_size}K",
                                  font=("Segoe UI", 7),
                                  fill="#CBD5E1",
                                  justify="center")
            c.create_text(x, pad_y + bar_h + 12, text=str(i),
                          font=("Segoe UI", 7), fill=COLORS["text_muted"])
            x += bw

    def _draw_frag_graph(self, result):
        """
        Modern dashboard-style fragmentation bar chart.
        - Per-block grouped bars: Used | Int Frag | (empty = Free block)
        - Axis labels, grid lines, value-above-bar labels
        - Fully responsive to canvas size
        """
        c = self._frag_canvas
        c.delete("all")
        c.update_idletasks()

        W = c.winfo_width()  or 480
        H = c.winfo_height() or 220

        blocks = result.blocks
        n = len(blocks)
        if n == 0:
            return

        # ── layout constants ───────────────────────────────────────────────
        PAD_L   = 52    # y-axis labels
        PAD_R   = 16
        PAD_T   = 24    # room for value labels above bars
        PAD_B   = 36    # x-axis labels
        CW = W - PAD_L - PAD_R   # chart width
        CH = H - PAD_T - PAD_B   # chart height

        max_kb  = max(b.block_size for b in blocks) or 1

        # ── y-axis grid lines ──────────────────────────────────────────────
        GRID_STEPS = 5
        for step in range(1, GRID_STEPS + 1):
            frac = step / GRID_STEPS
            gy   = PAD_T + CH - int(CH * frac)
            c.create_line(PAD_L, gy, PAD_L + CW, gy,
                          fill=_C_GRID, dash=(4, 5))
            kb_label = int(max_kb * frac)
            c.create_text(PAD_L - 6, gy,
                          text=str(kb_label),
                          font=("Segoe UI", 7),
                          fill=_C_AXIS_TXT,
                          anchor="e")

        # axis lines
        c.create_line(PAD_L, PAD_T,
                      PAD_L, PAD_T + CH,
                      fill="#3D444D", width=1)
        c.create_line(PAD_L, PAD_T + CH,
                      PAD_L + CW, PAD_T + CH,
                      fill="#3D444D", width=1)

        # ── bars ──────────────────────────────────────────────────────────
        slot_w  = CW / n
        bar_w   = max(12, int(slot_w * 0.55))
        base_y  = PAD_T + CH

        def kb_px(kb: int) -> int:
            return max(1, int(CH * kb / max_kb))

        for i, blk in enumerate(blocks):
            cx  = PAD_L + i * slot_w + slot_w / 2
            x0  = cx - bar_w / 2
            x1  = cx + bar_w / 2

            if blk.allocated_to:
                used_kb = blk.process_size
                frag_kb = blk.block_size - blk.process_size

                used_h = kb_px(used_kb)
                frag_h = kb_px(frag_kb) if frag_kb > 0 else 0

                # used section (bottom, indigo)
                uy1 = base_y
                uy0 = base_y - used_h
                c.create_rectangle(x0, uy0, x1, uy1,
                                   fill=_C_USED, outline="", width=0)
                # subtle top highlight
                c.create_line(x0, uy0, x1, uy0,
                              fill=_C_BAR_GLOW, width=2)

                # frag section (top of used, red)
                if frag_h > 0:
                    fy1 = uy0
                    fy0 = uy0 - frag_h
                    c.create_rectangle(x0, fy0, x1, fy1,
                                       fill=_C_INT_FRAG, outline="", width=0)

                    # value label above frag bar
                    label_y = fy0 - 5
                    c.create_text(cx, label_y,
                                  text=f"{frag_kb}K",
                                  font=("Segoe UI", 7, "bold"),
                                  fill=_C_INT_FRAG,
                                  anchor="s")
                else:
                    # no frag — label above used bar
                    c.create_text(cx, uy0 - 5,
                                  text=f"0K",
                                  font=("Segoe UI", 7),
                                  fill=_C_AXIS_TXT,
                                  anchor="s")

                # used value inside bar (if tall enough)
                if used_h > 16:
                    c.create_text(cx, (uy0 + uy1) / 2,
                                  text=f"{used_kb}K",
                                  font=("Segoe UI", 7),
                                  fill="#E0E0FF",
                                  anchor="center")

            else:
                # free block — steel grey
                bh  = kb_px(blk.block_size)
                by0 = base_y - bh
                c.create_rectangle(x0, by0, x1, base_y,
                                   fill=_C_FREE, outline="", width=0)
                c.create_line(x0, by0, x1, by0,
                              fill="#8B92A5", width=1)
                if bh > 16:
                    c.create_text(cx, (by0 + base_y) / 2,
                                  text=f"{blk.block_size}K",
                                  font=("Segoe UI", 7),
                                  fill="#CBD5E1",
                                  anchor="center")
                c.create_text(cx, by0 - 5,
                              text="Free",
                              font=("Segoe UI", 7),
                              fill=_C_FREE,
                              anchor="s")

            # x-axis block label
            c.create_text(cx, base_y + 6,
                          text=f"B{i}",
                          font=("Segoe UI", 7, "bold"),
                          fill=_C_AXIS_TXT,
                          anchor="n")

        # y-axis title (rotated via vertical text simulation)
        c.create_text(10, PAD_T + CH // 2,
                      text="KB",
                      font=("Segoe UI", 8),
                      fill=_C_AXIS_TXT,
                      anchor="center")

    # ── Allocation table population ───────────────────────────────────────────

    def _populate_alloc_table(self, result):
        for row in self._tree.get_children():
            self._tree.delete(row)

        for idx, a in enumerate(result.allocations):
            blk = next((b for b in result.blocks
                        if b.block_id == a["block_id"]), None)
            bsz  = blk.block_size if blk else "?"
            frag = a["frag"]
            tag  = "frag_hi" if isinstance(frag, int) and frag > 0 else (
                   "odd" if idx % 2 == 1 else "even")
            self._tree.insert("", "end",
                              values=(a["pid"], a["proc_size"],
                                      a["block_id"], bsz, frag),
                              tags=(tag,))

    # ── Resize helpers ────────────────────────────────────────────────────────

    def _redraw_if_result(self):
        if hasattr(self, "_last_result") and self._last_result:
            self._draw_memory(self._last_result)

    def _redraw_frag_if_result(self):
        if hasattr(self, "_last_result") and self._last_result:
            self._draw_frag_graph(self._last_result)

    # ── Paging text helper ────────────────────────────────────────────────────

    def _paging_text_insert(self, text: str, tag: str = ""):
        self._paging_text.configure(state="normal")
        self._paging_text.delete("1.0", "end")
        self._paging_text.insert("end", text, tag)
        self._paging_text.configure(state="disabled")

    # ── Font probe ────────────────────────────────────────────────────────────

    @staticmethod
    def _font_available(name: str) -> bool:
        try:
            import tkinter.font as tkfont
            return name in tkfont.families()
        except Exception:
            return False

    # ══════════════════════════════════════════════════════════════════════════
    # UI HELPERS
    # ══════════════════════════════════════════════════════════════════════════

    def _sec(self, parent, text):
        f = tk.Frame(parent, bg=COLORS["card_bg"])
        f.pack(fill="x")
        tk.Frame(f, bg=COLORS["accent_purple"], width=3).pack(side="left", fill="y")
        tk.Label(f, text=f"  {text}", font=FONTS["sidebar_hd"],
                 bg=COLORS["card_bg"], fg=COLORS["accent_purple"],
                 pady=5).pack(side="left")

    def _divider(self, parent):
        tk.Frame(parent, bg=COLORS["card_border"], height=1).pack(
            fill="x", pady=4)

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
                 bg=COLORS["card_bg"], fg=COLORS["text_secondary"]).pack(
            pady=(6, 0))
        tk.Label(card, textvariable=var, font=("Segoe UI", 14, "bold"),
                 bg=COLORS["card_bg"], fg=accent).pack(pady=(0, 6))
        return card