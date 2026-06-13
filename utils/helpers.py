"""
utils/helpers.py
----------------
Shared constants, input validators, and formatting helpers.
All pure functions — no Tkinter imports allowed here.
"""

from __future__ import annotations
from typing import Any


# ── Colour palette ────────────────────────────────────────────────────────────
COLORS = {
    # Sidebar
    "sidebar_bg":       "#1e2130",
    "sidebar_hover":    "#2d3250",
    "sidebar_active":   "#424769",
    "sidebar_text":     "#c8cce8",
    "sidebar_icon":     "#7c84b0",
    "sidebar_accent":   "#7c83d1",

    # Content area
    "content_bg":       "#f4f6fb",
    "card_bg":          "#ffffff",
    "card_border":      "#e4e8f0",

    # Typography
    "text_primary":     "#1a1d2e",
    "text_secondary":   "#6b7280",
    "text_muted":       "#9ca3af",

    # Accent / status
    "accent_blue":      "#4f6ef7",
    "accent_green":     "#22c55e",
    "accent_orange":    "#f97316",
    "accent_red":       "#ef4444",
    "accent_purple":    "#a855f7",
    "accent_teal":      "#14b8a6",
    "accent_yellow":    "#eab308",
    "accent_pink":      "#ec4899",

    # Gantt / chart sequence
    "gantt": [
        "#4f6ef7", "#22c55e", "#f97316", "#a855f7",
        "#14b8a6", "#ef4444", "#eab308", "#ec4899",
        "#06b6d4", "#84cc16",
    ],

    # Button states
    "btn_primary":       "#4f6ef7",
    "btn_primary_hover": "#3b5bdb",
    "btn_danger":        "#ef4444",
    "btn_success":       "#22c55e",

    # Canvas / neutral
    "canvas_bg":  "#ffffff",
    "grid_line":  "#e9ecef",
    "border":     "#dee2e6",
}

# ── Font definitions ──────────────────────────────────────────────────────────
FONTS = {
    "title":      ("Segoe UI", 18, "bold"),
    "subtitle":   ("Segoe UI", 13, "bold"),
    "body":       ("Segoe UI", 11),
    "body_bold":  ("Segoe UI", 11, "bold"),
    "small":      ("Segoe UI", 10),
    "mono":       ("Consolas",  11),
    "mono_small": ("Consolas",  10),
    "sidebar":    ("Segoe UI", 11),
    "sidebar_hd": ("Segoe UI",  9, "bold"),
    "card_num":   ("Segoe UI", 26, "bold"),
    "card_lbl":   ("Segoe UI", 10),
}

# ── App constants ─────────────────────────────────────────────────────────────
APP_TITLE   = "Mini OS Simulator"
APP_VERSION = "2.0.0"
WIN_WIDTH   = 1300
WIN_HEIGHT  = 800
SIDEBAR_W   = 230

# ── Sidebar nav items (label, icon, page_key) ─────────────────────────────────
NAV_ITEMS = [
    ("Dashboard",              "⊞", "dashboard"),
    ("CPU Scheduling",         "⚙", "cpu"),
    ("Memory Management",      "▦", "memory"),
    ("Page Replacement",       "⇄", "page_replacement"),
    ("Process Synchronization","⇌", "synchronization"),
    ("Deadlock Handling",      "⊗", "deadlock"),
    ("File Management",        "📁","file"),
]


# ── Input validators ──────────────────────────────────────────────────────────

def validate_positive_int(value: Any, name: str = "Value") -> int:
    try:
        v = int(value)
    except (ValueError, TypeError):
        raise ValueError(f"{name} must be an integer, got: {value!r}")
    if v <= 0:
        raise ValueError(f"{name} must be > 0, got {v}")
    return v


def validate_non_negative_int(value: Any, name: str = "Value") -> int:
    try:
        v = int(value)
    except (ValueError, TypeError):
        raise ValueError(f"{name} must be an integer, got: {value!r}")
    if v < 0:
        raise ValueError(f"{name} must be >= 0, got {v}")
    return v


def parse_int_list(raw: str, name: str = "List") -> list[int]:
    """Parse a comma/space-separated string into a list of integers."""
    raw = raw.replace(",", " ")
    parts = raw.split()
    if not parts:
        raise ValueError(f"{name} cannot be empty.")
    result = []
    for p in parts:
        try:
            result.append(int(p))
        except ValueError:
            raise ValueError(f"{name}: '{p}' is not a valid integer.")
    return result


def parse_matrix(raw: str, rows: int, cols: int,
                 name: str = "Matrix") -> list[list[int]]:
    """Parse a whitespace/comma/semicolon-delimited string into a rows×cols matrix."""
    raw = raw.replace(";", "\n").replace(",", " ")
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    if len(lines) != rows:
        raise ValueError(
            f"{name}: expected {rows} rows, got {len(lines)}. "
            "Separate rows with newlines or semicolons."
        )
    matrix = []
    for i, line in enumerate(lines):
        parts = line.split()
        if len(parts) != cols:
            raise ValueError(
                f"{name} row {i+1}: expected {cols} values, got {len(parts)}."
            )
        try:
            matrix.append([int(x) for x in parts])
        except ValueError:
            raise ValueError(f"{name} row {i+1}: non-integer value found.")
    return matrix


def fmt_float(v: float, decimals: int = 2) -> str:
    return f"{v:.{decimals}f}"


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))