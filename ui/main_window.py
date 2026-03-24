"""
main_window.py — Main application window.

Layout (3-column responsive grid):
  ┌──────────────────────┬──────────────────────┐
  │  LEFT: Drop Zone     │  RIGHT: Config +      │
  │        File List     │         Preview       │
  ├──────────────────────┤                       │
  │  Progress + Status   │                       │
  ├──────────────────────┴──────────────────────┤
  │  History Panel                               │
  └──────────────────────────────────────────────┘
"""
from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from core.converter import Converter, PRESETS
from core.disk_validator import DiskValidator
from ui.drop_zone import DropZone
from ui.preview_panel import PreviewPanel
from ui.history_panel import HistoryPanel
from utils.file_utils import format_bytes


class MainWindow(ctk.CTk):
    """Root application window."""

    APP_TITLE   = "ConvertirImagenes — PNG/JPG → AVIF"
    MIN_W, MIN_H = 1100, 760

    def __init__(self):
        super().__init__()
        self.title(self.APP_TITLE)
        self.minsize(self.MIN_W, self.MIN_H)
        self.geometry("1200x820")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # State
        self._files: list[str] = []
        self._converting = False
        self._stop_event = threading.Event()
        self._queue: queue.Queue = queue.Queue()
        self._converter: Converter | None = None

        # Try to initialise converter (may fail if plugin missing)
        try:
            self._converter = Converter()
        except RuntimeError as exc:
            pass  # We'll show the error when user tries to convert

        self._build_ui()
        self.after(100, self._poll_queue)

    # ==================================================================
    # UI construction
    # ==================================================================
    def _build_ui(self):
        self.columnconfigure(0, weight=2, minsize=420)
        self.columnconfigure(1, weight=3, minsize=540)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(3, weight=1)

        self._build_header()
        self._build_left_panel()
        self._build_right_panel()
        self._build_progress_bar()
        self._build_history()

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="#0f1b2d", corner_radius=0, height=56)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_propagate(False)
        header.columnconfigure(1, weight=1)

        logo = ctk.CTkLabel(
            header,
            text="⚡ ConvertirImagenes",
            font=("Segoe UI Black", 20),
            text_color="#6aadff",
        )
        logo.grid(row=0, column=0, padx=20, pady=8, sticky="w")

        subtitle = ctk.CTkLabel(
            header,
            text="PNG / JPG  →  AVIF  —  Conversor de alto rendimiento",
            font=("Segoe UI", 12),
            text_color="#4a7aaa",
        )
        subtitle.grid(row=0, column=1, padx=8, sticky="w")

    # ------------------------------------------------------------------
    # Left panel: drop zone + status
    # ------------------------------------------------------------------
    def _build_left_panel(self):
        left = ctk.CTkFrame(self, fg_color="#0d1117", corner_radius=0)
        left.grid(row=1, column=0, rowspan=2, sticky="nsew", padx=(0, 1))
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)

        self._drop_zone = DropZone(
            left,
            on_files_changed=self._on_files_changed,
            fg_color="#0d1117",
            corner_radius=0,
        )
        self._drop_zone.grid(row=0, column=0, sticky="nsew")

        # Convert button
        self._convert_btn = ctk.CTkButton(
            left,
            text="▶  Convertir a AVIF",
            font=("Segoe UI Black", 14),
            height=46,
            fg_color="#1a5fa8",
            hover_color="#2272c8",
            command=self._start_conversion,
        )
        self._convert_btn.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 4))

        self._cancel_btn = ctk.CTkButton(
            left,
            text="⏹  Cancelar",
            font=("Segoe UI", 13),
            height=36,
            fg_color="#3a1a1a",
            hover_color="#5a2a2a",
            command=self._cancel_conversion,
            state="disabled",
        )
        self._cancel_btn.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))

    # ------------------------------------------------------------------
    # Right panel: config + preview
    # ------------------------------------------------------------------
    def _build_right_panel(self):
        right = ctk.CTkFrame(self, fg_color="#0d1117", corner_radius=0)
        right.grid(row=1, column=1, sticky="nsew")
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        self._build_config(right)
        self._preview = PreviewPanel(right, fg_color="#0d1117", corner_radius=0)
        self._preview.grid(row=1, column=0, sticky="nsew")

    def _build_config(self, parent):
        cfg = ctk.CTkFrame(parent, fg_color="#111820", corner_radius=10)
        cfg.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        cfg.columnconfigure((0, 1, 2, 3), weight=1)

        # ---- Quality preset ----
        q_lbl = ctk.CTkLabel(
            cfg, text="🎯  Calidad de compresión",
            font=("Segoe UI Semibold", 12), anchor="w"
        )
        q_lbl.grid(row=0, column=0, columnspan=4, sticky="w", padx=12, pady=(10, 4))

        self._quality_var = tk.StringVar(value="medium")
        quality_opts = [
            ("🏅 Alta calidad",       "high",   "#14532d", "#22c55e"),
            ("⚖  Calidad media",      "medium", "#1e3a5f", "#6aadff"),
            ("📦 Baja calidad",       "low",    "#4a1a00", "#f97316"),
        ]
        self._q_buttons: dict[str, ctk.CTkButton] = {}
        for col, (label, value, bg, fg) in enumerate(quality_opts):
            btn = ctk.CTkButton(
                cfg,
                text=label,
                font=("Segoe UI", 12),
                fg_color=bg if value == "medium" else "#1c2533",
                hover_color=bg,
                border_width=2,
                border_color=fg if value == "medium" else "#2a3a4a",
                command=lambda v=value: self._set_quality(v),
            )
            btn.grid(row=1, column=col, padx=6, pady=(0, 10), sticky="ew")
            self._q_buttons[value] = btn
        self._set_quality("medium")

        # ---- Encoding speed ----
        s_lbl = ctk.CTkLabel(
            cfg, text="⚡  Velocidad de codificación",
            font=("Segoe UI Semibold", 12), anchor="w"
        )
        s_lbl.grid(row=2, column=0, columnspan=2, sticky="w", padx=12, pady=(4, 4))

        self._speed_var = tk.StringVar(value="good")
        speed_menu = ctk.CTkOptionMenu(
            cfg,
            values=["fast  (rápido)", "good  (bueno)", "best  (mejor)"],
            variable=None,
            command=self._on_speed_change,
            font=("Segoe UI", 12),
            dropdown_font=("Segoe UI", 12),
            width=200,
        )
        speed_menu.set("good  (bueno)")
        speed_menu.grid(row=2, column=2, columnspan=2, padx=6, pady=(4, 10), sticky="ew")
        self._speed_menu = speed_menu

        # ---- Options row ----
        opts = ctk.CTkFrame(cfg, fg_color="transparent")
        opts.grid(row=3, column=0, columnspan=4, sticky="ew", padx=12, pady=(0, 4))

        # EXIF checkbox
        self._keep_exif_var = tk.BooleanVar(value=True)
        exif_cb = ctk.CTkCheckBox(
            opts,
            text="Preservar metadatos EXIF",
            variable=self._keep_exif_var,
            font=("Segoe UI", 12),
            checkbox_width=18,
            checkbox_height=18,
        )
        exif_cb.pack(side="left", padx=(0, 20))

        # Destination folder
        dest_frame = ctk.CTkFrame(opts, fg_color="transparent")
        dest_frame.pack(side="right", fill="x", expand=True)

        ctk.CTkLabel(
            dest_frame,
            text="📁  Carpeta destino:",
            font=("Segoe UI", 12),
        ).pack(side="left", padx=(0, 6))

        self._dest_var = tk.StringVar(value="")
        dest_entry = ctk.CTkEntry(
            dest_frame,
            textvariable=self._dest_var,
            placeholder_text="(misma carpeta origen)",
            width=200,
            font=("Segoe UI", 11),
        )
        dest_entry.pack(side="left", padx=(0, 4))

        browse_dest = ctk.CTkButton(
            dest_frame,
            text="…",
            width=32,
            height=28,
            font=("Segoe UI", 13),
            fg_color="#2a3a4a",
            hover_color="#3a4a5a",
            command=self._browse_dest,
        )
        browse_dest.pack(side="left")

        # Padding bottom
        ctk.CTkLabel(cfg, text="").grid(row=4, column=0, pady=2)

    # ------------------------------------------------------------------
    # Progress + status bar
    # ------------------------------------------------------------------
    def _build_progress_bar(self):
        prog_frame = ctk.CTkFrame(self, fg_color="#0a0f16", corner_radius=0, height=64)
        prog_frame.grid(row=2, column=1, sticky="ew", padx=0)
        prog_frame.grid_propagate(False)
        prog_frame.columnconfigure(0, weight=1)

        self._progress_bar = ctk.CTkProgressBar(
            prog_frame, mode="determinate", height=10, corner_radius=4
        )
        self._progress_bar.set(0)
        self._progress_bar.grid(row=0, column=0, sticky="ew", padx=16, pady=(10, 4))

        self._status_var = tk.StringVar(value="Listo. Selecciona imágenes para comenzar.")
        status_lbl = ctk.CTkLabel(
            prog_frame,
            textvariable=self._status_var,
            font=("Segoe UI", 11),
            anchor="w",
            text_color="#8aafcf",
        )
        status_lbl.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 8))

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------
    def _build_history(self):
        self._history = HistoryPanel(
            self, fg_color="#0d1117", corner_radius=0
        )
        self._history.grid(row=3, column=0, columnspan=2, sticky="nsew")

    # ==================================================================
    # Event handlers
    # ==================================================================
    def _set_quality(self, value: str):
        self._quality_var.set(value)
        colors = {
            "high":   ("#14532d", "#22c55e"),
            "medium": ("#1e3a5f", "#6aadff"),
            "low":    ("#4a1a00", "#f97316"),
        }
        for k, btn in self._q_buttons.items():
            is_sel = k == value
            bg, fg = colors[k]
            btn.configure(
                fg_color=bg if is_sel else "#1c2533",
                border_color=fg if is_sel else "#2a3a4a",
            )

    def _on_speed_change(self, choice: str):
        # extract first word
        self._speed_var.set(choice.split()[0])

    def _browse_dest(self):
        folder = filedialog.askdirectory(title="Seleccionar carpeta destino")
        if folder:
            self._dest_var.set(folder)

    def _on_files_changed(self, files: list[str]):
        self._files = files
        n = len(files)
        self._status_var.set(
            f"{n} imagen{'es' if n != 1 else ''} en cola." if n
            else "Lista vacía. Arrastra o examina imágenes."
        )
        # Show preview of first file
        if files:
            self._preview.set_before(files[0])
            self._preview.set_after(None)
        else:
            self._preview.clear()

    # ==================================================================
    # Conversion
    # ==================================================================
    def _start_conversion(self):
        if self._converting:
            return
        if not self._files:
            messagebox.showwarning(
                "Sin imágenes",
                "Selecciona al menos una imagen antes de convertir.",
            )
            return
        if self._converter is None:
            messagebox.showerror(
                "Plugin no disponible",
                "pillow-avif-plugin no está instalado.\n"
                "Ejecuta: pip install pillow-avif-plugin",
            )
            return

        output_dir = self._dest_var.get().strip() or None
        check_dir  = output_dir or os.path.dirname(self._files[0])

        # Disk space validation
        ok, needed, free = DiskValidator.has_enough_space(
            self._files, check_dir, quality=60
        )
        if not ok:
            answer = messagebox.askyesno(
                "Espacio insuficiente",
                f"Espacio libre:    {format_bytes(free)}\n"
                f"Espacio estimado: {format_bytes(needed)}\n\n"
                f"¿Deseas continuar de todas formas?",
            )
            if not answer:
                return

        # Lock UI
        self._converting = True
        self._convert_btn.configure(state="disabled")
        self._cancel_btn.configure(state="normal")
        self._progress_bar.set(0)
        self._stop_event.clear()

        quality_preset = self._quality_var.get()
        keep_exif      = self._keep_exif_var.get()
        speed          = self._speed_var.get().split()[0]  # "fast", "good", "best"

        thread = threading.Thread(
            target=self._run_batch,
            args=(self._files.copy(), output_dir, quality_preset, keep_exif, speed),
            daemon=True,
        )
        thread.start()

    def _run_batch(self, files, output_dir, quality_preset, keep_exif, speed):

        def progress_cb(idx, total, result):
            self._queue.put(("progress", idx, total, result))

        try:
            self._converter.convert_batch(
                input_paths    = files,
                output_dir     = output_dir,
                quality_preset = quality_preset,
                keep_exif      = keep_exif,
                encoding_speed = speed,
                progress_cb    = progress_cb,
                stop_event     = self._stop_event,
            )
        except Exception as exc:
            self._queue.put(("error", str(exc)))
        finally:
            self._queue.put(("done",))

    def _cancel_conversion(self):
        self._stop_event.set()
        self._status_var.set("Cancelando…")

    def _poll_queue(self):
        """Drain the inter-thread queue on the main thread."""
        try:
            while True:
                msg = self._queue.get_nowait()
                if msg[0] == "progress":
                    _, idx, total, result = msg
                    pct = idx / total
                    self._progress_bar.set(pct)
                    verb = "✔" if result.success else "✘"
                    import os as _os
                    name = _os.path.basename(result.source_path)
                    self._status_var.set(
                        f"{verb} [{idx}/{total}]  {name}  "
                        f"({format_bytes(result.original_size)} → "
                        f"{format_bytes(result.converted_size)})"
                    )
                    self._history.add_result(result)
                    # Update after-preview with the latest successful file
                    if result.success:
                        self._preview.set_before(result.source_path)
                        self._preview.set_after(result.output_path)

                elif msg[0] == "error":
                    _, err_msg = msg
                    self._status_var.set(f"⚠ Error inesperado: {err_msg}")

                elif msg[0] == "done":
                    self._converting = False
                    self._convert_btn.configure(state="normal")
                    self._cancel_btn.configure(state="disabled")
                    if self._stop_event.is_set():
                        self._status_var.set("⏹ Conversión cancelada por el usuario.")
                    else:
                        self._status_var.set(
                            f"✔ Conversión completada — {len(self._files)} imagen(es) procesada(s)."
                        )
                    self._progress_bar.set(1.0)
        except queue.Empty:
            pass
        self.after(80, self._poll_queue)
