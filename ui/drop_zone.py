"""
drop_zone.py — Drag-and-drop file selection panel.

Uses the centralized utils/dnd_bootstrap.py for DnD registration and
utils/dnd_utils.py for cross-platform path parsing.
"""
from __future__ import annotations

import logging
import os
import tkinter as tk
from tkinter import filedialog
from typing import Callable

import customtkinter as ctk

from utils.file_utils import is_valid_image, format_bytes, get_file_size
from utils.i18n import I18N
from utils.dnd_bootstrap import is_ready as dnd_is_ready, enable_dnd_on_widget
from utils.dnd_utils import parse_drop_paths
from utils import theme

logger = logging.getLogger(__name__)


class FileRow(ctk.CTkFrame):
    """Single row representing one queued image file."""

    def __init__(self, master, path: str, on_remove: Callable[[str], None], **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.path = path
        self.on_remove = on_remove

        name = os.path.basename(path)
        size = format_bytes(get_file_size(path))

        self.columnconfigure(1, weight=1)

        # Icon label
        icon = ctk.CTkLabel(self, text="🖼", width=24, font=theme.font(14))
        icon.grid(row=0, column=0, padx=(4, 8))

        # File name
        name_lbl = ctk.CTkLabel(
            self,
            text=name,
            anchor="w",
            font=theme.font(12),
            wraplength=280,
        )
        name_lbl.grid(row=0, column=1, sticky="ew")

        # File size
        size_lbl = ctk.CTkLabel(
            self,
            text=size,
            anchor="e",
            font=theme.font(11),
            text_color=theme.TEXT_MUTED,
            width=70,
        )
        size_lbl.grid(row=0, column=2, padx=(4, 4))

        # Remove button
        rm_btn = ctk.CTkButton(
            self,
            text="✕",
            width=24,
            height=24,
            fg_color="transparent",
            hover_color=theme.DANGER_SOFT,
            command=self._remove,
            font=theme.font(11),
        )
        rm_btn.grid(row=0, column=3, padx=(0, 4))

        # Subtle separator
        sep = ctk.CTkFrame(self, height=1, fg_color=theme.BORDER)
        sep.grid(row=1, column=0, columnspan=4, sticky="ew", padx=4, pady=(4, 0))

    def _remove(self):
        self.on_remove(self.path)
        self.destroy()


class DropZone(ctk.CTkFrame):
    """
    File selection panel supporting:
      - Native drag-and-drop  (requires tkinterdnd2)
      - 'Browse' button fallback
      - Scrollable list of queued files
      - Remove individual files
    """

    def __init__(
        self,
        master,
        on_files_changed: Callable[[list[str]], None] | None = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.on_files_changed = on_files_changed
        self._files: list[str] = []
        self._excluded_format: str = ""

        self._build_ui()
        # Schedule DnD registration for next idle loop so the widget tree
        # is fully constructed first (fixes the "not permitted" cursor).
        self.after_idle(self._enable_dnd)

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------
    def _build_ui(self):
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # --- Drop area header ---
        self._header_frame = ctk.CTkFrame(
            self,
            fg_color=theme.CARD,
            corner_radius=theme.RADIUS,
            border_width=2,
            border_color=theme.BORDER,
        )
        self._header_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        self._header_frame.columnconfigure(0, weight=1)
        header = self._header_frame   # local alias for readability below

        dnd_icon = ctk.CTkLabel(
            header,
            textvariable=I18N.tvar(header, "drop_title"),
            font=theme.font(14, "bold"),
            text_color=theme.ACCENT_TEXT,
        )
        dnd_icon.grid(row=0, column=0, padx=12, pady=(10, 2))

        sub = ctk.CTkLabel(
            header,
            textvariable=I18N.tvar(header, "drop_sub"),
            font=theme.font(11),
            text_color=theme.TEXT_MUTED,
        )
        sub.grid(row=1, column=0, pady=(0, 4))

        btn_row = ctk.CTkFrame(header, fg_color="transparent")
        btn_row.grid(row=2, column=0, pady=(4, 10))

        browse_btn = ctk.CTkButton(
            btn_row,
            textvariable=I18N.tvar(btn_row, "btn_browse"),
            width=160,
            height=34,
            font=theme.font(12, "bold"),
            corner_radius=theme.RADIUS_SM,
            fg_color=theme.ACCENT_SOFT,
            hover_color=theme.ACCENT_HOVER,
            command=self._browse,
        )
        browse_btn.pack(side="left", padx=6)

        clear_btn = ctk.CTkButton(
            btn_row,
            textvariable=I18N.tvar(btn_row, "btn_clear"),
            width=130,
            height=34,
            font=theme.font(12),
            corner_radius=theme.RADIUS_SM,
            fg_color=theme.DANGER_SOFT,
            hover_color=theme.DANGER_HOVER,
            command=self.clear_all,
        )
        clear_btn.pack(side="left", padx=6)

        # --- File count label ---
        self._count_var = tk.StringVar(value="0 imágenes seleccionadas")
        count_lbl = ctk.CTkLabel(
            self,
            textvariable=self._count_var,
            font=theme.font(11),
            text_color=theme.TEXT_MUTED,
        )
        count_lbl.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 2))

        # --- Scrollable file list ---
        self._list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=theme.CARD_ALT,
            corner_radius=theme.RADIUS_SM,
            label_text="",
        )
        self._list_frame.grid(
            row=2, column=0, sticky="nsew", padx=12, pady=(0, 12)
        )
        self.rowconfigure(2, weight=1)

    # ------------------------------------------------------------------
    # Drag-and-Drop registration (via centralized bootstrap)
    # ------------------------------------------------------------------
    def _enable_dnd(self):
        """Register this widget tree as a drop target using the bootstrap helper."""
        if not dnd_is_ready():
            logger.info("DnD not available — Browse button is the only input method.")
            return

        enable_dnd_on_widget(
            self,
            on_drop=self._on_drop,
            on_enter=self._on_drag_enter,
            on_leave=self._on_drag_leave,
            recursive=True,
        )
        logger.info("DropZone: DnD targets registered on widget tree.")

    def _on_drag_enter(self, event):
        """Visual feedback: highlight border when dragging over."""
        try:
            self._header_frame.configure(border_color=theme.BORDER_HI)
        except Exception:
            pass

    def _on_drag_leave(self, event):
        """Restore border on drag leave."""
        try:
            self._header_frame.configure(border_color=theme.BORDER)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    def _browse(self):
        types = [("Imágenes", "*.png *.jpg *.jpeg *.webp *.avif")]
        
        if self._excluded_format != ".png":
            types.append(("PNG", "*.png"))
        if self._excluded_format not in (".jpg", ".jpeg"):
            types.append(("JPEG", "*.jpg *.jpeg"))
        if self._excluded_format != ".webp":
            types.append(("WebP", "*.webp"))
        if self._excluded_format != ".avif":
            types.append(("AVIF", "*.avif"))

        paths = filedialog.askopenfilenames(
            title="Seleccionar imágenes",
            filetypes=types,
        )
        if paths:
            self.add_files(list(paths))

    def _on_drop(self, event):
        """
        Parse tkinterdnd2 drop data using the cross-platform normalizer.
        parse_drop_paths already validates existence & extension.
        """
        paths = parse_drop_paths(event.data)
        if paths:
            self.add_files(paths)
        else:
            logger.info("DnD: no valid image files in dropped data.")

        # Restore border in case <<DragLeave>> did not fire
        try:
            self._header_frame.configure(border_color=theme.BORDER)
        except Exception:
            pass

    def _remove_file(self, path: str):
        if path in self._files:
            self._files.remove(path)
        self._update_count()
        if self.on_files_changed:
            self.on_files_changed(self._files.copy())

    def _update_count(self):
        n = len(self._files)
        self._count_var.set(f"{n} imagen{'es' if n != 1 else ''} seleccionada{'s' if n != 1 else ''}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def add_files(self, paths: list[str]):
        added = 0
        for p in paths:
            p = p.strip()
            if not p or not os.path.isfile(p) or not is_valid_image(p) or p in self._files:
                continue
                
            ext = os.path.splitext(p)[1].lower()
            if self._excluded_format and ext == self._excluded_format:
                continue
                
            self._files.append(p)
            row = FileRow(self._list_frame, p, self._remove_file)
            row.pack(fill="x", padx=4, pady=2)
            added += 1
        if added:
            self._update_count()
            if self.on_files_changed:
                self.on_files_changed(self._files.copy())

    def clear_all(self):
        for widget in self._list_frame.winfo_children():
            widget.destroy()
        self._files.clear()
        self._update_count()
        if self.on_files_changed:
            self.on_files_changed([])

    def get_files(self) -> list[str]:
        return self._files.copy()

    def set_excluded_format(self, fmt: str):
        self._excluded_format = fmt.lower()
        # Remove any existing files that match the newly excluded format
        to_remove = []
        for p in self._files:
            if os.path.splitext(p)[1].lower() == self._excluded_format:
                to_remove.append(p)
                
        for p in to_remove:
            self._remove_file(p)
