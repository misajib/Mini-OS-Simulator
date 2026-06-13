"""
gui/file_management_page.py
----------------------------
File Management module UI.

Algorithms: Sequential · Linked · Indexed Allocation
Visualization: Disk block grid canvas + FAT table
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from gui.base_page import BasePage
from utils.helpers import COLORS, FONTS
from utils.visualizations import ModernButton, ResultTable, draw_disk_blocks
from modules.file_management import (
    allocate_sequential, allocate_linked, allocate_indexed
)


class FileManagementPage(BasePage):

    def __init__(self, parent: tk.Widget, **kw):
        super().__init__(parent,
                         title="File Management",
                         subtitle="Sequential · Linked · Indexed Allocation — Disk Visualization",
                         accent=COLORS["accent_teal"], **kw)
        self._file_rows: list[dict] = []
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
                         highlightthickness=1, width=290)
        frame.pack_propagate(False)

        # Algorithm selector
        self._sec(frame, "Allocation Method")
        self._algo_var = tk.StringVar(value="Sequential")
        for name in ("Sequential", "Linked", "Indexed"):
            tk.Radiobutton(
                frame, text=name, variable=self._algo_var, value=name,
                bg=COLORS["card_bg"], fg=COLORS["text_primary"],
                selectcolor=COLORS["content_bg"],
                activebackground=COLORS["card_bg"],
                font=FONTS["body"]
            ).pack(anchor="w", padx=18, pady=2)

        self._divider(frame)

        # Disk size
        self._sec(frame, "Disk Size (blocks)")
        self._disk_var = tk.StringVar(value="64")
        ttk.Spinbox(frame, textvariable=self._disk_var,
                    from_=16, to=256, width=8).pack(anchor="w", padx=12, pady=4)

        self._divider(frame)

        # File entry form
        self._sec(frame, "Add File")
        form = tk.Frame(frame, bg=COLORS["card_bg"], padx=12)
        form.pack(fill="x")

        for row_i, (lbl, attr, default) in enumerate([
            ("File Name:", "_fname_var", "file1.txt"),
            ("Size (blk):", "_fsize_var", "4"),
        ]):
            tk.Label(form, text=lbl, font=FONTS["small"],
                     bg=COLORS["card_bg"], fg=COLORS["text_secondary"],
                     width=10, anchor="w").grid(row=row_i, column=0, pady=3)
            var = tk.StringVar(value=default)
            setattr(self, attr, var)
            ttk.Entry(form, textvariable=var, width=16).grid(
                row=row_i, column=1, pady=3, sticky="ew", padx=4)

        btn_row = tk.Frame(form, bg=COLORS["card_bg"])
        btn_row.grid(row=2, column=0, columnspan=2, pady=8)
        ModernButton(btn_row, "+ Add",  command=self._add_file,   variant="success").pack(side="left", padx=(0, 4))
        ModernButton(btn_row, "✕ Del",  command=self._del_file,   variant="danger").pack(side="left", padx=(0, 4))
        ModernButton(btn_row, "Clear",  command=self._clear_files, variant="ghost").pack(side="left")

        self._divider(frame)

        # File queue
        self._sec(frame, "File Queue")
        self._file_table = ResultTable(
            frame,
            columns=[("Name", "nm", 100), ("Size (blk)", "sz", 80)],
        )
        self._file_table.pack(fill="x", padx=12, pady=4)

        self._divider(frame)
        ModernButton(frame, "Load Sample Files",
                     command=self._load_sample, variant="outline").pack(
            fill="x", padx=12, pady=4)
        ModernButton(frame, "▶  Allocate Disk",
                     command=self._run, variant="primary").pack(
            fill="x", padx=12, pady=(4, 12))

        return frame

    # ── RIGHT PANEL ───────────────────────────────────────────────────────────

    def _build_right(self, parent) -> tk.Frame:
        frame = tk.Frame(parent, bg=COLORS["content_bg"])

        # Stat strip
        stat_row = tk.Frame(frame, bg=COLORS["content_bg"])
        stat_row.pack(fill="x", pady=(0, 10))

        self._stat_vars: dict[str, tk.StringVar] = {}
        for title, accent in [
            ("Disk Util %",   COLORS["accent_teal"]),
            ("Used Blocks",   COLORS["accent_blue"]),
            ("Free Blocks",   COLORS["accent_green"]),
            ("Method",        COLORS["accent_purple"]),
        ]:
            var = tk.StringVar(value="—")
            self._stat_vars[title] = var
            c = self._mini_stat(stat_row, title, var, accent)
            c.pack(side="left", expand=True, fill="x", padx=(0, 8))

        # Disk visualization canvas
        disk_card = self._card(frame, "Disk Block Visualization")
        disk_card.pack(fill="x", pady=(0, 10))

        disk_wrap = tk.Frame(disk_card, bg=COLORS["card_bg"])
        disk_wrap.pack(fill="x", padx=10, pady=8)

        vscroll = ttk.Scrollbar(disk_wrap, orient="vertical")
        vscroll.pack(side="right", fill="y")

        self._disk_canvas = tk.Canvas(
            disk_wrap, bg=COLORS["canvas_bg"], height=160,
            highlightthickness=0,
            yscrollcommand=vscroll.set)
        self._disk_canvas.pack(side="left", fill="x", expand=True)
        vscroll.config(command=self._disk_canvas.yview)

        # Legend
        leg = tk.Frame(disk_card, bg=COLORS["card_bg"])
        leg.pack(fill="x", padx=10, pady=(0, 6))
        tk.Frame(leg, bg=COLORS["grid_line"], width=14, height=14).pack(side="left", padx=(0, 4))
        tk.Label(leg, text="Free", font=FONTS["small"],
                 bg=COLORS["card_bg"], fg=COLORS["text_secondary"]).pack(side="left", padx=(0, 14))
        tk.Label(leg, text="(colored = allocated file)", font=FONTS["small"],
                 bg=COLORS["card_bg"], fg=COLORS["text_secondary"]).pack(side="left")

        # FAT / allocation table
        fat_card = self._card(frame, "File Allocation Table")
        fat_card.pack(fill="both", expand=True)

        self._fat_frame = tk.Frame(fat_card, bg=COLORS["card_bg"])
        self._fat_frame.pack(fill="both", expand=True, padx=10, pady=8)

        # Log
        log_card = self._card(frame, "Allocation Log")
        log_card.pack(fill="x", pady=(10, 0))

        self._log = tk.Text(
            log_card, height=4, bg=COLORS["sidebar_bg"],
            fg=COLORS["sidebar_text"], font=FONTS["mono_small"],
            relief="flat", state="disabled", padx=6, pady=4)
        self._log.pack(fill="x", padx=10, pady=6)
        self._log.tag_configure("ok",  foreground=COLORS["accent_green"])
        self._log.tag_configure("err", foreground=COLORS["accent_red"])

        return frame

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _add_file(self):
        name = self._fname_var.get().strip()
        size_str = self._fsize_var.get().strip()
        if not name:
            self.show_error("File name cannot be empty.")
            return
        try:
            size = int(size_str)
            if size < 1:
                raise ValueError
        except ValueError:
            self.show_error("Size must be a positive integer.")
            return
        self._file_rows.append({"name": name, "size": size})
        self._refresh_file_table()
        # auto-increment suggestion
        try:
            base, ext = name.rsplit(".", 1)
            digits = ""
            letters = ""
            for ch in reversed(base):
                if ch.isdigit():
                    digits = ch + digits
                else:
                    letters = ch + letters
                    break
            if digits:
                new_name = base[:len(base) - len(digits)] + str(int(digits) + 1) + "." + ext
                self._fname_var.set(new_name)
        except Exception:
            pass

    def _del_file(self):
        sel = self._file_table.tree.selection()
        if not sel:
            return
        idx = self._file_table.tree.index(sel[0])
        del self._file_rows[idx]
        self._refresh_file_table()

    def _clear_files(self):
        self._file_rows.clear()
        self._refresh_file_table()

    def _load_sample(self):
        self._file_rows = [
            {"name": "os.exe",    "size": 5},
            {"name": "data.db",   "size": 8},
            {"name": "readme.txt","size": 2},
            {"name": "img.png",   "size": 6},
            {"name": "log.txt",   "size": 3},
        ]
        self._refresh_file_table()
        self._disk_var.set("64")

    def _refresh_file_table(self):
        self._file_table.clear()
        for f in self._file_rows:
            self._file_table.insert([f["name"], f["size"]])

    def _run(self):
        if not self._file_rows:
            self.show_error("Add at least one file.")
            return
        try:
            total = int(self._disk_var.get())
            specs = [(f["name"], f["size"]) for f in self._file_rows]
            algo  = self._algo_var.get()

            if algo == "Sequential":
                result = allocate_sequential(specs, total)
            elif algo == "Linked":
                result = allocate_linked(specs, total)
            elif algo == "Indexed":
                result = allocate_indexed(specs, total)
            else:
                return
        except Exception as e:
            self.show_error(str(e))
            return

        # Stats
        self._stat_vars["Disk Util %"].set(f"{result.utilisation:.1f}%")
        self._stat_vars["Used Blocks"].set(str(result.used_blocks))
        self._stat_vars["Free Blocks"].set(str(result.free_count))
        self._stat_vars["Method"].set(result.method)

        # Disk canvas
        draw_disk_blocks(self._disk_canvas, total, result.block_map)

        # FAT table
        self._build_fat_table(result)

        # Log
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        for line in result.log:
            tag = "ok" if line.startswith("✔") else "err"
            self._log.insert("end", line + "\n", tag)
        self._log.see("end")
        self._log.configure(state="disabled")

    def _build_fat_table(self, result):
        """Rebuild the FAT treeview dynamically based on allocation method."""
        for w in self._fat_frame.winfo_children():
            w.destroy()

        if not result.fat:
            tk.Label(self._fat_frame, text="No allocations.",
                     bg=COLORS["card_bg"], fg=COLORS["text_secondary"],
                     font=FONTS["small"]).pack()
            return

        # Determine columns from FAT rows
        sample = result.fat[0]
        cols   = list(sample.keys())

        table = ResultTable(
            self._fat_frame,
            columns=[(c, 100) for c in cols],
        )
        table.pack(fill="x")

        for row in result.fat:
            table.insert([str(row.get(c, "")) for c in cols])

    # ── UI helpers ────────────────────────────────────────────────────────────

    def _sec(self, parent, text):
        f = tk.Frame(parent, bg=COLORS["card_bg"])
        f.pack(fill="x")
        tk.Frame(f, bg=COLORS["accent_teal"], width=3).pack(side="left", fill="y")
        tk.Label(f, text=f"  {text}", font=FONTS["sidebar_hd"],
                 bg=COLORS["card_bg"], fg=COLORS["accent_teal"],
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
        tk.Label(card, textvariable=var, font=("Segoe UI", 13, "bold"),
                 bg=COLORS["card_bg"], fg=accent).pack(pady=(0, 6))
        return card