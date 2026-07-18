"""
theme.py — Centralized design tokens for the whole UI.

Single source of truth for colors, fonts and radii so every panel
looks consistent and the palette can be changed in one place.
"""
from __future__ import annotations

import sys

# ── Color palette (modern dark) ──────────────────────────────────────
BG          = "#0a0e14"   # app background
SURFACE     = "#10161f"   # column panels
CARD        = "#151d29"   # cards / sections
CARD_ALT    = "#1a2433"   # alternating rows, inputs
BORDER      = "#243247"   # subtle borders
BORDER_HI   = "#3b82f6"   # highlighted borders (drag-over, focus)

ACCENT       = "#3b82f6"  # primary action
ACCENT_HOVER = "#2563eb"
ACCENT_SOFT  = "#1e3a5f"  # subdued accent surfaces
ACCENT_TEXT  = "#7ab5ff"  # accent-tinted text / titles

SUCCESS      = "#22c55e"
DANGER       = "#ef4444"
DANGER_HOVER = "#dc2626"
DANGER_SOFT  = "#3f1d24"
WARNING      = "#f59e0b"

TEXT       = "#e6edf3"    # primary text
TEXT_MUTED = "#94a3b8"    # secondary text
TEXT_FAINT = "#64748b"    # tertiary text / placeholders

# ── Radii ────────────────────────────────────────────────────────────
RADIUS      = 12          # cards
RADIUS_SM   = 8           # inputs, buttons

# ── Typography (cross-platform) ──────────────────────────────────────
if sys.platform == "win32":
    _FAMILY = "Segoe UI"
elif sys.platform == "darwin":
    _FAMILY = "Helvetica Neue"
else:
    _FAMILY = "DejaVu Sans"


def font(size: int = 12, weight: str = "normal") -> tuple:
    """Return a Tk font tuple. weight: 'normal' | 'bold'."""
    if weight == "bold":
        return (_FAMILY, size, "bold")
    return (_FAMILY, size)
