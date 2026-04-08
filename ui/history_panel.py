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

from utils.file_utils import format_bytes, show_in_file_explorer
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
        self._hdr_canvas = tk.Canvas(self, bg="#0d1520", highlightthickness=0, height=30)
        self._hdr_canvas.grid(row=0, column=0, sticky="ew", padx=4, pady=(8, 0))
        
        self._COL_WIDTHS = [280, 100, 70, 160, 90, 80, 90]
        
        self._hdr_frame = ctk.CTkFrame(self._hdr_canvas, fg_color="#0d1520", corner_radius=0, height=30, width=sum(self._COL_WIDTHS))
        self._hdr_frame.pack_propagate(False)
        self._hdr_window = self._hdr_canvas.create_window((0, 0), window=self._hdr_frame, anchor="nw")

        for col, key in enumerate(["col_file", "col_stat", "col_subsampling", "col_size", "col_saving", "col_time", "col_action"]):
            cell = ctk.CTkFrame(self._hdr_frame, width=self._COL_WIDTHS[col], height=30, fg_color="transparent")
            cell.grid_propagate(False)
            cell.pack_propagate(False)
            cell.grid(row=0, column=col, sticky="w")
            ctk.CTkLabel(
                cell,
                textvariable=I18N.tvar(self, key),
                font=("Segoe UI Semibold", 11),
                text_color="#6b7b8d",
                anchor="w",
            ).pack(side="left", padx=8, fill="x", expand=True)

        # ── 2D Scrollable area ───────────────────────────────────
        self._canvas_container = ctk.CTkFrame(self, fg_color="transparent")
        self._canvas_container.grid(row=1, column=0, sticky="nsew", padx=4, pady=2)
        self._canvas_container.rowconfigure(0, weight=1)
        self._canvas_container.columnconfigure(0, weight=1)

        self._canvas = tk.Canvas(self._canvas_container, bg="#0f1a26", highlightthickness=0)
        self._canvas.grid(row=0, column=0, sticky="nsew")

        self._v_scroll = ctk.CTkScrollbar(self._canvas_container, orientation="vertical", command=self._canvas.yview)
        self._v_scroll.grid(row=0, column=1, sticky="ns")

        def _on_hscroll(*args):
            self._canvas.xview(*args)
            self._hdr_canvas.xview(*args)

        self._h_scroll = ctk.CTkScrollbar(self._canvas_container, orientation="horizontal", command=_on_hscroll)
        self._h_scroll.grid(row=1, column=0, sticky="ew")

        def _sync_xscroll(first, last):
            self._h_scroll.set(first, last)
            self._hdr_canvas.xview_moveto(first)

        self._canvas.configure(yscrollcommand=self._v_scroll.set, xscrollcommand=_sync_xscroll)

        self._scroll = ctk.CTkFrame(self._canvas, fg_color="#0f1a26")
        self._canvas_window = self._canvas.create_window((0, 0), window=self._scroll, anchor="nw")

        def _on_frame_configure(event):
            self._canvas.configure(scrollregion=self._canvas.bbox("all"))
            self._hdr_canvas.configure(scrollregion=self._hdr_canvas.bbox("all"))
            
        self._scroll.bind("<Configure>", _on_frame_configure)

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
                "subsampling":    getattr(result, "subsampling", ""),
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

        row = ctk.CTkFrame(self._scroll, fg_color=bg, corner_radius=4, height=36, width=sum(self._COL_WIDTHS))
        row.pack(fill="x", padx=2, pady=1, expand=False)
        row.pack_propagate(False)
        row.grid_propagate(False)

        def make_cell(col_idx):
            cell = ctk.CTkFrame(row, width=self._COL_WIDTHS[col_idx], height=36, fg_color="transparent")
            cell.grid_propagate(False)
            cell.pack_propagate(False)
            cell.grid(row=0, column=col_idx, sticky="w")
            return cell

        # 1) Filename
        cell0 = make_cell(0)
        fname = os.path.basename(entry["source"])
        ctk.CTkLabel(
            cell0, text=fname, font=("Segoe UI", 11),
            text_color="#d0d8e0", anchor="w",
        ).pack(side="left", padx=8, fill="x", expand=True)

        # 2) Status
        cell1 = make_cell(1)
        if entry["success"]:
            status_text = f"✔ {I18N.get('completed')}"
            status_color = "#22c55e"
        else:
            status_text = f"✖ {I18N.get('error')}"
            status_color = "#ef4444"

        ctk.CTkLabel(
            cell1, text=status_text, font=("Segoe UI Semibold", 11),
            text_color=status_color, anchor="w",
        ).pack(side="left", padx=4, fill="x", expand=True)

        # 2b) Subsampling
        cell2 = make_cell(2)
        subsampling_text = entry.get("subsampling", "") or "—"
        ctk.CTkLabel(
            cell2, text=subsampling_text, font=("Segoe UI", 11),
            text_color="#a0b0c0", anchor="w",
        ).pack(side="left", padx=4, fill="x", expand=True)

        # 3) Size (Before → After)
        cell3 = make_cell(3)
        if entry["success"]:
            orig = format_bytes(entry["original_size"])
            conv = format_bytes(entry["converted_size"])
            size_text = f"{orig} → {conv}"
            size_color = "#a0b0c0"
        else:
            size_text = entry["error"][:30] if entry["error"] else "—"
            size_color = "#ef4444"

        ctk.CTkLabel(
            cell3, text=size_text, font=("Segoe UI", 11),
            text_color=size_color, anchor="w",
        ).pack(side="left", padx=4, fill="x", expand=True)

        # 4) Savings %
        cell4 = make_cell(4)
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
            cell4, text=saving_text, font=("Segoe UI Semibold", 11),
            text_color=saving_color, anchor="w",
        ).pack(side="left", padx=4, fill="x", expand=True)

        # 5) Time
        cell5 = make_cell(5)
        ts = time.strftime("%H:%M:%S", time.localtime(entry.get("timestamp", time.time())))
        ctk.CTkLabel(
            cell5, text=ts, font=("Segoe UI", 11),
            text_color="#6b7b8d", anchor="w",
        ).pack(side="left", padx=4, fill="x", expand=True)

        # 6) Action
        cell6 = make_cell(6)
        def _open_folder():
            target = entry["output"] if entry["success"] and entry["output"] else entry["source"]
            show_in_file_explorer(target)

        ctk.CTkButton(
            cell6, text=I18N.get("hist_open_folder"), font=("Segoe UI", 11),
            width=60, height=24,
            fg_color="transparent", hover_color="#1a2b4a",
            text_color="#3b82f6", anchor="center",
            command=_open_folder
        ).pack(side="right", padx=8)

        self._row_widgets.append(row)

        # Force scroll to bottom to show latest result
        self._canvas.update_idletasks()
        try:
            self._canvas.yview_moveto(1.0)
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
