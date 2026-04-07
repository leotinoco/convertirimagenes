"""
history_panel.py — scrollable conversion history panel.

Uses a simple CTkFrame with pack() for guaranteed visibility of results.
Each result shows filename, status, sizes, savings %, and timestamp.
"""
from __future__ import annotations

import logging
import os
import tkinter as tk
import time

import customtkinter as ctk

from utils.file_utils import format_bytes
from utils.i18n import I18N
from utils.logging_utils import log_exception

logger = logging.getLogger(__name__)


class HistoryPanel(ctk.CTkFrame):
    """Shows a scrollable list of completed conversion results."""

    MAX_ENTRIES = 200

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._entries: list[dict] = []
        self._row_widgets: list[ctk.CTkFrame] = []
        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # ── Column headers ────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="#0d1520", corner_radius=0, height=30)
        hdr.grid(row=0, column=0, sticky="ew", padx=4, pady=(8, 0))
        hdr.grid_propagate(False)
        hdr.columnconfigure(0, weight=3)
        hdr.columnconfigure(1, weight=2)
        hdr.columnconfigure(2, weight=3)
        hdr.columnconfigure(3, weight=2)
        hdr.columnconfigure(4, weight=1)

        for col, key in enumerate(["col_file", "col_stat", "col_size", "col_saving", "col_time"]):
            ctk.CTkLabel(
                hdr,
                textvariable=I18N.tvar(hdr, key),
                font=("Segoe UI Semibold", 11),
                text_color="#6b7b8d",
                anchor="w",
            ).grid(row=0, column=col, sticky="w", padx=8, pady=4)

        # ── Scrollable results area ───────────────────────────────────
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="#0f1a26", corner_radius=0
        )
        self._scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=2)
        self._scroll.columnconfigure(0, weight=1)

        # ── Bottom bar ────────────────────────────────────────────────
        bot = ctk.CTkFrame(self, fg_color="transparent", height=36)
        bot.grid(row=2, column=0, sticky="ew", padx=8, pady=(4, 8))

        self._clear_btn = ctk.CTkButton(
            bot,
            textvariable=I18N.tvar(bot, "hist_clear"),
            width=110,
            height=28,
            font=("Segoe UI", 11),
            fg_color="transparent",
            border_width=1,
            border_color="#2d4a7a",
            hover_color="#1a2b4a",
            command=self.clear,
        )
        self._clear_btn.pack(side="left")

        self._count_var = tk.StringVar(value="")
        self._count_lbl = ctk.CTkLabel(
            bot,
            textvariable=self._count_var,
            font=("Segoe UI", 11),
            text_color="#22c55e",
        )
        self._count_lbl.pack(side="right")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def add_result(self, result) -> None:
        """Append a ConversionResult to the history."""
        try:
            entry = {
                "source":         result.source_path,
                "output":         result.output_path,
                "original_size":  result.original_size,
                "converted_size": result.converted_size,
                "savings_pct":    result.savings_pct,
                "success":        result.success,
                "error":          result.error or "",
                "timestamp":      time.time(),
            }
            self._entries.append(entry)
            self._create_row(entry)
            self._update_count()

            logger.info(
                "History: added %s (%.1f%% savings)",
                os.path.basename(result.source_path),
                result.savings_pct,
            )
        except Exception as exc:
            log_exception(logger, "History.add_result failed", exc)

    def clear(self):
        for w in self._row_widgets:
            try:
                w.destroy()
            except Exception:
                pass
        self._row_widgets.clear()
        self._entries.clear()
        self._count_var.set("")

    def get_entries(self) -> list[dict]:
        return self._entries.copy()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _create_row(self, entry: dict):
        """Build a single result row inside the scroll frame."""
        # Alternating background for readability
        idx = len(self._row_widgets)
        bg = "#111e2e" if idx % 2 == 0 else "#0f1a26"

        row = ctk.CTkFrame(self._scroll, fg_color=bg, corner_radius=4, height=36)
        row.pack(fill="x", padx=2, pady=1, expand=False)
        row.pack_propagate(False)
        row.columnconfigure(0, weight=3)
        row.columnconfigure(1, weight=2)
        row.columnconfigure(2, weight=3)
        row.columnconfigure(3, weight=2)
        row.columnconfigure(4, weight=1)

        # 1) Filename
        fname = os.path.basename(entry["source"])
        ctk.CTkLabel(
            row, text=fname, font=("Segoe UI", 11),
            text_color="#d0d8e0", anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=8, pady=4)

        # 2) Status
        if entry["success"]:
            status_text = f"✔ {I18N.get('completed')}"
            status_color = "#22c55e"
        else:
            status_text = f"✖ {I18N.get('error')}"
            status_color = "#ef4444"

        ctk.CTkLabel(
            row, text=status_text, font=("Segoe UI Semibold", 11),
            text_color=status_color, anchor="w",
        ).grid(row=0, column=1, sticky="w", padx=4, pady=4)

        # 3) Size (Before → After)
        if entry["success"]:
            orig = format_bytes(entry["original_size"])
            conv = format_bytes(entry["converted_size"])
            size_text = f"{orig} → {conv}"
            size_color = "#a0b0c0"
        else:
            size_text = entry["error"][:30] if entry["error"] else "—"
            size_color = "#ef4444"

        ctk.CTkLabel(
            row, text=size_text, font=("Segoe UI", 11),
            text_color=size_color, anchor="w",
        ).grid(row=0, column=2, sticky="w", padx=4, pady=4)

        # 4) Savings %
        if entry["success"] and entry["original_size"] > 0:
            pct = entry["savings_pct"]
            if pct > 0:
                saving_text = f"-{pct:.1f}%"
                saving_color = "#22c55e"
            else:
                saving_text = f"+{abs(pct):.1f}%"
                saving_color = "#ef4444"
        else:
            saving_text = "—"
            saving_color = "#6b7b8d"

        ctk.CTkLabel(
            row, text=saving_text, font=("Segoe UI Semibold", 11),
            text_color=saving_color, anchor="w",
        ).grid(row=0, column=3, sticky="w", padx=4, pady=4)

        # 5) Time
        ts = time.strftime("%H:%M:%S", time.localtime(entry.get("timestamp", time.time())))
        ctk.CTkLabel(
            row, text=ts, font=("Segoe UI", 11),
            text_color="#6b7b8d", anchor="w",
        ).grid(row=0, column=4, sticky="w", padx=4, pady=4)

        self._row_widgets.append(row)

        # Force scroll to bottom to show latest result
        self._scroll.update_idletasks()
        try:
            self._scroll._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass

        # Enforce max entries
        while len(self._row_widgets) > self.MAX_ENTRIES:
            old = self._row_widgets.pop(0)
            old.destroy()
            self._entries.pop(0)

    def _update_count(self):
        n = len(self._entries)
        ok = sum(1 for e in self._entries if e["success"])
        if n > 0:
            self._count_var.set(f"✔ {ok}/{n}")
        else:
            self._count_var.set("")
