"""
history_panel.py — scrollable conversion history panel.
"""
from __future__ import annotations

import os
import tkinter as tk

import customtkinter as ctk

from utils.file_utils import format_bytes


class HistoryRow(ctk.CTkFrame):
    def __init__(self, master, index: int, entry: dict, **kwargs):
        super().__init__(master, fg_color="#111820", corner_radius=6, **kwargs)
        self.columnconfigure(1, weight=1)

        status_color = "#22c55e" if entry["success"] else "#ef4444"
        status_icon  = "✔" if entry["success"] else "✘"

        # Index + status
        idx_lbl = ctk.CTkLabel(
            self,
            text=f"{index:02d}  {status_icon}",
            font=("Segoe UI Semibold", 12),
            text_color=status_color,
            width=40,
        )
        idx_lbl.grid(row=0, column=0, padx=(8, 4), pady=6, sticky="ns")

        # File name
        name_lbl = ctk.CTkLabel(
            self,
            text=os.path.basename(entry["source"]),
            font=("Segoe UI", 11),
            anchor="w",
        )
        name_lbl.grid(row=0, column=1, sticky="ew", padx=4)

        if entry["success"]:
            orig  = format_bytes(entry["original_size"])
            conv  = format_bytes(entry["converted_size"])
            pct   = entry["savings_pct"]
            arrow = "▼" if pct >= 0 else "▲"
            color = "#22c55e" if pct >= 0 else "#ef4444"
            stats = f"{orig} → {conv}  ({arrow}{abs(pct):.1f}%)"
        else:
            stats = f"Error: {entry['error'][:60]}"
            color = "#ef4444"

        stats_lbl = ctk.CTkLabel(
            self,
            text=stats,
            font=("Segoe UI", 11),
            text_color=color,
            anchor="e",
        )
        stats_lbl.grid(row=0, column=2, padx=(4, 8), sticky="e")


class HistoryPanel(ctk.CTkFrame):
    """Shows a scrollable list of completed conversion results."""

    MAX_ENTRIES = 200

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._entries: list[dict] = []
        self._counter = 0
        self._build_ui()

    def _build_ui(self):
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # Header row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
        header.columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="📋  Historial de conversiones",
            font=("Segoe UI Semibold", 13),
            anchor="w",
        )
        title.pack(side="left")

        clear_btn = ctk.CTkButton(
            header,
            text="Limpiar",
            width=70,
            height=26,
            font=("Segoe UI", 11),
            fg_color="#2a2a2a",
            hover_color="#3a1a1a",
            command=self.clear,
        )
        clear_btn.pack(side="right")

        # Scrollable area
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="#0d1117", corner_radius=8
        )
        self._scroll.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        # Empty state label
        self._empty_lbl = ctk.CTkLabel(
            self._scroll,
            text="Sin conversiones todavía",
            font=("Segoe UI", 12),
            text_color="gray",
        )
        self._empty_lbl.pack(pady=24)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def add_result(self, result) -> None:
        """Append a ConversionResult to the history."""
        if self._empty_lbl.winfo_exists():
            self._empty_lbl.pack_forget()

        self._counter += 1
        entry = {
            "source":         result.source_path,
            "output":         result.output_path,
            "original_size":  result.original_size,
            "converted_size": result.converted_size,
            "savings_pct":    result.savings_pct,
            "success":        result.success,
            "error":          result.error,
        }
        self._entries.append(entry)

        row = HistoryRow(self._scroll, self._counter, entry)
        row.pack(fill="x", padx=4, pady=2)

        # Enforce max entries (UI only — keep data)
        children = self._scroll.winfo_children()
        if len(children) > self.MAX_ENTRIES:
            children[0].destroy()

    def clear(self):
        for w in self._scroll.winfo_children():
            w.destroy()
        self._entries.clear()
        self._counter = 0
        self._empty_lbl = ctk.CTkLabel(
            self._scroll,
            text="Sin conversiones todavía",
            font=("Segoe UI", 12),
            text_color="gray",
        )
        self._empty_lbl.pack(pady=24)

    def get_entries(self) -> list[dict]:
        return self._entries.copy()
