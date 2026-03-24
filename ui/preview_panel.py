"""
preview_panel.py — Before/After image preview panel.
"""
from __future__ import annotations

import os
import tkinter as tk
from typing import Optional

import customtkinter as ctk
from PIL import Image

from utils.file_utils import format_bytes, get_file_size

PREVIEW_SIZE = (280, 210)  # max thumbnail size in pixels


def _make_thumbnail(path: str, max_size: tuple[int, int]) -> ctk.CTkImage | None:
    try:
        with Image.open(path) as raw:
            raw.thumbnail(max_size, Image.LANCZOS)
            img = raw.copy()  # detach from file handle so Windows can later overwrite it
        return ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
    except Exception:
        return None


class _PreviewPane(ctk.CTkFrame):
    """Single-side (before or after) preview pane."""

    def __init__(self, master, title: str, **kwargs):
        super().__init__(master, fg_color="#111820", corner_radius=8, **kwargs)
        self.columnconfigure(0, weight=1)

        title_lbl = ctk.CTkLabel(
            self,
            text=title,
            font=("Segoe UI Semibold", 12),
            text_color="#6aadff",
        )
        title_lbl.grid(row=0, column=0, pady=(8, 4))

        # Placeholder area
        self._img_lbl = ctk.CTkLabel(
            self,
            text="—",
            width=PREVIEW_SIZE[0],
            height=PREVIEW_SIZE[1],
            fg_color="#0d1117",
            corner_radius=6,
            font=("Segoe UI", 24),
            text_color="#2a3a4a",
        )
        self._img_lbl.grid(row=1, column=0, padx=8, pady=4)

        self._meta_lbl = ctk.CTkLabel(
            self,
            text="",
            font=("Segoe UI", 10),
            text_color="gray",
        )
        self._meta_lbl.grid(row=2, column=0, pady=(2, 8))

    def set_image(self, path: str | None):
        if path is None or not os.path.exists(path):
            self._img_lbl.configure(image=None, text="—")
            self._meta_lbl.configure(text="")
            return

        thumb = _make_thumbnail(path, PREVIEW_SIZE)
        if thumb:
            self._img_lbl.configure(image=thumb, text="")
            self._img_lbl._image = thumb  # keep ref to avoid GC

            try:
                with Image.open(path) as img:
                    w, h = img.size  # file closed immediately after reading dimensions
            except Exception:
                w, h = 0, 0
            size_str = format_bytes(get_file_size(path))
            self._meta_lbl.configure(text=f"{w}×{h} px  •  {size_str}")
        else:
            self._img_lbl.configure(image=None, text="⚠ No se pudo cargar")


class PreviewPanel(ctk.CTkFrame):
    """Side-by-side before/after preview."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        lbl = ctk.CTkLabel(
            self,
            text="🔍  Vista previa  (Antes → Después)",
            font=("Segoe UI Semibold", 13),
            anchor="w",
        )
        lbl.grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(10, 6))

        self._before = _PreviewPane(self, "Antes")
        self._before.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=(0, 12))

        self._after = _PreviewPane(self, "Después")
        self._after.grid(row=1, column=1, sticky="nsew", padx=(6, 12), pady=(0, 12))

    def set_before(self, path: str | None):
        self._before.set_image(path)

    def set_after(self, path: str | None):
        self._after.set_image(path)

    def clear(self):
        self._before.set_image(None)
        self._after.set_image(None)
