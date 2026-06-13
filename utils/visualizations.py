"""
utils/visualizations.py
-----------------------
Reusable Canvas-based drawing helpers and GUI widgets.
Used across all GUI pages.  No business logic here.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from utils.helpers import COLORS, FONTS


# ── Modern button ─────────────────────────────────────────────────────────────

class ModernButton(tk.Button):
    """Flat button with hover effect."""

    _VARIANTS = {
        "primary": ("#4f6ef7", "#ffffff", "#3b5bdb"),
        "danger":  ("#ef4444", "#ffffff", "#dc2626"),
        "success": ("#22c55e", "#ffffff", "#16a34a"),
        "ghost":   ("#f4f6fb", "#1a1d2e", "#e4e8f0"),
        "outline": ("#ffffff", "#4f6ef7", "#e0e7ff"),
    }

    def __init__(self, parent: tk.Widget, text: str, command=None,
                 variant: str = "primary", **kw):
        bg, fg, hover = self._VARIANTS.get(variant, self._VARIANTS["primary"])
        super().__init__(
            parent, text=text, command=command,
            bg=bg, fg=fg,
            activebackground=hover, activeforeground=fg,
            relief="flat", bd=0, padx=16, pady=7,
            font=FONTS["body_bold"], cursor="hand2", **kw
        )
        self._bg, self._hover = bg, hover
        self.bind("<Enter>", lambda _: self.config(bg=self._hover))
        self.bind("<Leave>", lambda _: self.config(bg=self._bg))


# ── Result table ──────────────────────────────────────────────────────────────

class ResultTable(tk.Frame):
    """
    A ttk.Treeview with scrollbars.

    columns: list of either
        (heading, width)           — 2-tuple
        (heading, tag, width)      — 3-tuple  (heading + ignored tag + width)
    """

    def __init__(self, parent: tk.Widget, columns: list[tuple], **kw):
        super().__init__(parent, bg=COLORS["card_bg"], **kw)

        # Normalise to (heading, width)
        normalised: list[tuple[str, int]] = []
        for col in columns:
            if len(col) == 3:
                normalised.append((str(col[0]), int(col[2])))
            else:
                normalised.append((str(col[0]), int(col[1])))

        col_ids = [c[0] for c in normalised]

        style = ttk.Style()
        style.configure("RT.Treeview",
                         background=COLORS["card_bg"],
                         foreground=COLORS["text_primary"],
                         rowheight=26,
                         fieldbackground=COLORS["card_bg"],
                         font=FONTS["body"])
        style.configure("RT.Treeview.Heading",
                         background=COLORS["sidebar_active"],
                         foreground="#ffffff",
                         font=FONTS["body_bold"])
        style.map("RT.Treeview",
                  background=[("selected", COLORS["accent_blue"])],
                  foreground=[("selected", "#ffffff")])

        self._tree = ttk.Treeview(self, columns=col_ids, show="headings",
                                   style="RT.Treeview")
        for heading, width in normalised:
            self._tree.heading(heading, text=heading)
            self._tree.column(heading, width=width, anchor="center", minwidth=40)

        vsb = ttk.Scrollbar(self, orient="vertical",   command=self._tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    def clear(self):
        self._tree.delete(*self._tree.get_children())

    def insert(self, values: list, tag: str = ""):
        self._tree.insert("", "end", values=values, tags=(tag,) if tag else ())

    def tag_config(self, tag: str, **kw):
        self._tree.tag_configure(tag, **kw)

    @property
    def tree(self) -> ttk.Treeview:
        return self._tree


# ── Gantt chart ───────────────────────────────────────────────────────────────

def draw_gantt(canvas: tk.Canvas, gantt: list[tuple],
               total_time: int = 0, height: int = 80) -> None:
    """
    Draw a Gantt chart on *canvas*.
    gantt items: (pid_label, start, end)
    """
    canvas.delete("all")
    canvas.update_idletasks()
    w = canvas.winfo_width() or 800

    if not gantt:
        return
    if total_time == 0:
        total_time = gantt[-1][2]
    if total_time == 0:
        return

    padding_left  = 50
    padding_right = 20
    bar_h   = 36
    bar_y   = (height - bar_h) // 2
    chart_w = w - padding_left - padding_right
    scale   = chart_w / total_time
    colors  = COLORS["gantt"]

    canvas.configure(bg=COLORS["canvas_bg"])
    pid_color: dict[str, str] = {}
    color_idx = 0

    for pid, start, end in gantt:
        if pid not in pid_color:
            pid_color[pid] = colors[color_idx % len(colors)]
            color_idx += 1
        x1 = padding_left + start * scale
        x2 = padding_left + end   * scale
        col = pid_color[pid]
        canvas.create_rectangle(x1, bar_y, x2, bar_y + bar_h,
                                 fill=col, outline="#ffffff", width=1.5)
        bar_w = x2 - x1
        if bar_w > 22:
            canvas.create_text((x1 + x2) / 2, bar_y + bar_h / 2,
                                text=str(pid), fill="#ffffff",
                                font=("Segoe UI", 9, "bold"))

    shown: set[int] = set()
    for _, start, end in gantt:
        for t in (start, end):
            if t not in shown:
                x = padding_left + t * scale
                canvas.create_text(x, bar_y + bar_h + 10,
                                    text=str(t), font=("Segoe UI", 8),
                                    fill=COLORS["text_secondary"])
                shown.add(t)


# ── Memory block visualiser ───────────────────────────────────────────────────

def draw_memory_blocks(canvas: tk.Canvas,
                        blocks: list[dict],
                        canvas_height: int = 200) -> None:
    canvas.delete("all")
    canvas.update_idletasks()
    w = canvas.winfo_width() or 800
    total = sum(b["size"] for b in blocks)
    if total == 0:
        return

    x, pad_y, bar_h = 10, 30, 80
    scale = (w - 20) / total

    for i, blk in enumerate(blocks):
        bw = blk["size"] * scale
        if blk.get("allocated_to"):
            fill  = COLORS["gantt"][i % len(COLORS["gantt"])]
            label = f"{blk['allocated_to']}\n{blk['size']}KB"
        else:
            fill  = COLORS["grid_line"]
            label = f"Free\n{blk['size']}KB"

        canvas.create_rectangle(x, pad_y, x + bw, pad_y + bar_h,
                                 fill=fill, outline="#ffffff", width=1.5)
        if bw > 30:
            canvas.create_text(x + bw / 2, pad_y + bar_h / 2,
                                text=label, font=("Segoe UI", 8),
                                fill="#ffffff" if blk.get("allocated_to")
                                              else COLORS["text_secondary"],
                                justify="center")
        x += bw


# ── Disk block visualiser ─────────────────────────────────────────────────────

def draw_disk_blocks(canvas: tk.Canvas,
                      n_blocks: int,
                      allocations: dict[int, str],
                      cols: int = 16) -> None:
    canvas.delete("all")
    cell = 36
    pad  = 10
    rows = (n_blocks + cols - 1) // cols

    for i in range(n_blocks):
        r, c = divmod(i, cols)
        x = pad + c * cell
        y = pad + r * cell
        label = allocations.get(i)
        fill  = (COLORS["gantt"][hash(label) % len(COLORS["gantt"])]
                 if label else COLORS["grid_line"])
        canvas.create_rectangle(x, y, x + cell - 2, y + cell - 2,
                                 fill=fill, outline="#ffffff", width=1)
        text   = label[:2] if label else str(i)
        tcolor = "#ffffff" if label else COLORS["text_muted"]
        canvas.create_text(x + cell // 2 - 1, y + cell // 2 - 1,
                            text=text, font=("Segoe UI", 7), fill=tcolor)

    canvas.configure(scrollregion=(0, 0,
                                    pad + cols * cell + pad,
                                    pad + rows * cell + pad))