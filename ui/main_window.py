"""
main_window.py — Main application window.

Layout (3-column responsive grid):
  ┌─────────────────┬─────────────────┬─────────────────┐
  │  File Mgmt      │  Settings       │  Preview        │
  │  (DropZone)     │  (Config)       │  (Split)        │
  │                 │                 ├─────────────────┤
  │                 │                 │  History        │
  └─────────────────┴─────────────────┴─────────────────┘
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
from utils.logging_utils import log_exception
from ui.drop_zone import DropZone
from ui.preview_panel import PreviewPanel
from ui.history_panel import HistoryPanel
from ui.metadata_modal import MetadataModal
from utils.file_utils import format_bytes
from utils.i18n import I18N


class MainWindow(ctk.CTk):
    """Root application window."""

    MIN_W, MIN_H = 1200, 760

    def __init__(self):
        super().__init__()

        # Initialise default lang
        I18N.set_language("en")

        self.title("⚡ ConvertirImagenes")
        self.minsize(self.MIN_W, self.MIN_H)
        self.geometry("1400x820")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # State
        self._files: list[str] = []
        self._custom_meta: dict = {}
        self._converting = False
        self._stop_event = threading.Event()
        self._queue: queue.Queue = queue.Queue()
        self._converter: Converter | None = None
        self._successful_original_files: set[str] = set()

        # Try to initialise converter (may fail if plugin missing)
        try:
            self._converter = Converter()
        except RuntimeError as exc:
            pass  # Error shown on convert

        self._build_ui()
        self.after(100, self._poll_queue)

        # --- Bootstrap TkinterDnD2 AFTER ctk.CTk is fully initialized ---
        # We defer to after_idle so the Tcl interpreter is fully ready
        self.after_idle(self._init_dnd)

    # ==================================================================
    # UI construction
    # ==================================================================
    def _build_ui(self):
        self.columnconfigure(0, weight=1, uniform="col", minsize=400)
        self.columnconfigure(1, weight=1, uniform="col", minsize=400)
        self.columnconfigure(2, weight=1, uniform="col", minsize=400)
        self.rowconfigure(1, weight=1)

        self._build_header()
        self._build_left_panel()
        self._build_middle_panel()
        self._build_right_panel()

    def _init_dnd(self):
        """Deferred DnD bootstrap — runs after the Tcl event loop is active."""
        from utils.dnd_bootstrap import bootstrap_dnd
        if bootstrap_dnd(self):
            # Re-trigger registration on DropZone now that DnD is loaded
            self._drop_zone._enable_dnd()

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="#0f1b2d", corner_radius=0, height=56)
        header.grid(row=0, column=0, columnspan=3, sticky="ew")
        header.grid_propagate(False)
        header.columnconfigure(1, weight=1)

        logo = ctk.CTkLabel(
            header,
            textvariable=I18N.tvar(header, "title"),
            font=("Segoe UI Black", 20),
            text_color="#6aadff",
        )
        logo.grid(row=0, column=0, padx=20, pady=8, sticky="w")

        lang_frame = ctk.CTkFrame(header, fg_color="transparent")
        lang_frame.grid(row=0, column=2, padx=20, sticky="e")
        
        self._lang_var = tk.StringVar(value=I18N.current_lang())
        lang_switch = ctk.CTkSegmentedButton(
            lang_frame, 
            values=["en", "es"],
            variable=self._lang_var,
            command=self._on_lang_changed,
            font=("Segoe UI", 12)
        )
        lang_switch.pack(side="right")

    def _on_lang_changed(self, value):
        I18N.set_language(value)
        # Update dynamic menus if necessary
        self._speed_map = {I18N.get("speed_slow"): 2, I18N.get("speed_med"): 5, I18N.get("speed_fast"): 8}
        self._speed_menu.configure(values=list(self._speed_map.keys()))
        current_opt = self._speed_menu.get()
        # Find which key matches the value, or just reset to default
        self._speed_menu.set(I18N.get("speed_slow"))

        self._subsampling_menu.configure(values=[I18N.get("sub_420"), I18N.get("sub_444")])
        self._subsampling_menu.set(I18N.get("sub_420"))

    # ------------------------------------------------------------------
    # Left panel (File Mgmt)
    # ------------------------------------------------------------------
    def _build_left_panel(self):
        left = ctk.CTkFrame(self, fg_color="#0d1117", corner_radius=0)
        left.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        lbl = ctk.CTkLabel(left, textvariable=I18N.tvar(left, "file_mgmt"), font=("Segoe UI Semibold", 14), anchor="w")
        lbl.grid(row=0, column=0, sticky="w", padx=12, pady=(10, 0))

        self._drop_zone = DropZone(
            left,
            on_files_changed=self._on_files_changed,
            fg_color="#0d1117",
            corner_radius=0,
        )
        self._drop_zone.grid(row=1, column=0, sticky="nsew")

        self._convert_btn = ctk.CTkButton(
            left,
            textvariable=I18N.tvar(left, "btn_convert_all"),
            font=("Segoe UI Semibold", 16),
            height=46,
            fg_color="#1a5fa8",
            hover_color="#2272c8",
            command=self._start_conversion,
        )
        self._convert_btn.grid(row=2, column=0, sticky="ew", padx=12, pady=12)

        self._delete_orig_btn = ctk.CTkButton(
            left,
            textvariable=I18N.tvar(left, "btn_delete_originals"),
            font=("Segoe UI Semibold", 16),
            height=46,
            fg_color="#e63946",
            hover_color="#d62828",
            state="disabled",
            command=self._delete_originals,
        )
        self._delete_orig_btn.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 12))

    # ------------------------------------------------------------------
    # Middle panel (Settings)
    # ------------------------------------------------------------------
    def _build_middle_panel(self):
        mid = ctk.CTkFrame(self, fg_color="#0d1117", corner_radius=0)
        mid.grid(row=1, column=1, sticky="nsew", padx=5, pady=10)
        mid.columnconfigure(0, weight=1)

        lbl = ctk.CTkLabel(mid, textvariable=I18N.tvar(mid, "settings_hdr"), font=("Segoe UI Semibold", 14), anchor="w")
        lbl.grid(row=0, column=0, sticky="w", padx=12, pady=(10, 10))

        # 1. Settings & Optimization
        opt_frame = ctk.CTkFrame(mid, fg_color="#111820", corner_radius=8)
        opt_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 15))
        opt_frame.columnconfigure(0, weight=1)
        
        ctk.CTkLabel(opt_frame, textvariable=I18N.tvar(opt_frame, "settings_opt"), font=("Segoe UI Semibold", 12)).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 5))
        
        q_frame = ctk.CTkFrame(opt_frame, fg_color="transparent")
        q_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 2))
        q_frame.columnconfigure(1, weight=1)
        
        ctk.CTkLabel(q_frame, textvariable=I18N.tvar(q_frame, "q_lbl"), font=("Segoe UI", 12)).grid(row=0, column=0, sticky="w")
        self._quality_var = tk.IntVar(value=65)
        ctk.CTkLabel(q_frame, textvariable=self._quality_var, font=("Segoe UI", 12)).grid(row=0, column=2, sticky="e")
        ctk.CTkSlider(q_frame, from_=0, to=100, variable=self._quality_var, command=lambda v: self._quality_var.set(int(v))).grid(row=1, column=0, columnspan=3, sticky="ew", pady=(2,0))

        ctk.CTkLabel(opt_frame, textvariable=I18N.tvar(opt_frame, "speed_lbl"), font=("Segoe UI", 12)).grid(row=2, column=0, sticky="w", padx=12, pady=(5, 0))
        self._speed_map = {I18N.get("speed_slow"): 2, I18N.get("speed_med"): 5, I18N.get("speed_fast"): 8}
        self._speed_menu = ctk.CTkOptionMenu(opt_frame, values=list(self._speed_map.keys()), font=("Segoe UI", 12))
        self._speed_menu.grid(row=3, column=0, sticky="ew", padx=12, pady=(2, 2))
        
        ctk.CTkLabel(opt_frame, textvariable=I18N.tvar(opt_frame, "sub_lbl"), font=("Segoe UI", 12)).grid(row=4, column=0, sticky="w", padx=12, pady=(5, 0))
        self._subsampling_menu = ctk.CTkOptionMenu(opt_frame, values=[I18N.get("sub_420"), I18N.get("sub_444")], font=("Segoe UI", 12))
        self._subsampling_menu.grid(row=5, column=0, sticky="ew", padx=12, pady=(2, 0))

        ctk.CTkLabel(opt_frame, textvariable=I18N.tvar(opt_frame, "sub_warn"), font=("Segoe UI", 10), text_color="#a0b0c0").grid(row=6, column=0, sticky="w", padx=12, pady=(2, 5))

        # Threads slider (CPU count)
        t_frame = ctk.CTkFrame(opt_frame, fg_color="transparent")
        t_frame.grid(row=7, column=0, sticky="ew", padx=12, pady=(0, 10))
        t_frame.columnconfigure(1, weight=1)
        import os
        max_threads = os.cpu_count() or 4
        ctk.CTkLabel(t_frame, textvariable=I18N.tvar(t_frame, "threads_lbl"), font=("Segoe UI", 12)).grid(row=0, column=0, sticky="w")
        self._threads_var = tk.IntVar(value=max_threads)
        ctk.CTkLabel(t_frame, textvariable=self._threads_var, font=("Segoe UI", 12)).grid(row=0, column=2, sticky="e")
        ctk.CTkSlider(t_frame, from_=1, to=max_threads, number_of_steps=max_threads-1, variable=self._threads_var, command=lambda v: self._threads_var.set(int(v))).grid(row=1, column=0, columnspan=3, sticky="ew", pady=(2,0))

        # 2. Resizing Options
        res_frame = ctk.CTkFrame(mid, fg_color="#111820", corner_radius=8)
        res_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 15))
        res_frame.columnconfigure(1, weight=1)
        
        ctk.CTkLabel(res_frame, textvariable=I18N.tvar(res_frame, "resize_hdr"), font=("Segoe UI Semibold", 12)).grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(10, 5))

        self._resize_var = tk.BooleanVar(value=False)
        ctk.CTkLabel(res_frame, textvariable=I18N.tvar(res_frame, "resize_en"), font=("Segoe UI", 12)).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 2))
        self._resize_sw = ctk.CTkSwitch(res_frame, text="", variable=self._resize_var, command=self._on_resize_toggle)
        self._resize_sw.grid(row=1, column=1, sticky="e", padx=12, pady=(0, 2))

        wh_frame = ctk.CTkFrame(res_frame, fg_color="transparent")
        wh_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 10))
        wh_frame.columnconfigure((0,1), weight=1)
        
        ctk.CTkLabel(wh_frame, textvariable=I18N.tvar(wh_frame, "width"), font=("Segoe UI", 11)).grid(row=0, column=0, sticky="w")
        self._resize_w = ctk.CTkEntry(wh_frame, placeholder_text="1920", height=28)
        self._resize_w.grid(row=1, column=0, sticky="ew", padx=(0, 5))
        self._resize_w.bind("<KeyRelease>", self._on_width_changed)
        
        ctk.CTkLabel(wh_frame, textvariable=I18N.tvar(wh_frame, "height"), font=("Segoe UI", 11)).grid(row=0, column=1, sticky="w")
        self._resize_h = ctk.CTkEntry(wh_frame, placeholder_text="1080", height=28)
        self._resize_h.grid(row=1, column=1, sticky="ew", padx=(5, 0))
        self._resize_h.bind("<KeyRelease>", self._on_height_changed)

        # 3. Metadata
        meta_frame = ctk.CTkFrame(mid, fg_color="#111820", corner_radius=8)
        meta_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))
        meta_frame.columnconfigure(1, weight=1)
        
        ctk.CTkLabel(meta_frame, textvariable=I18N.tvar(meta_frame, "meta_hdr"), font=("Segoe UI Semibold", 12)).grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(10, 5))
        
        ctk.CTkLabel(meta_frame, textvariable=I18N.tvar(meta_frame, "meta_exif"), font=("Segoe UI", 12)).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 2))
        self._keep_exif_var = tk.BooleanVar(value=True)
        ctk.CTkSwitch(meta_frame, text="", variable=self._keep_exif_var).grid(row=1, column=1, sticky="e", padx=12, pady=(0, 2))

        ctk.CTkLabel(meta_frame, textvariable=I18N.tvar(meta_frame, "meta_iptc"), font=("Segoe UI", 12)).grid(row=2, column=0, sticky="w", padx=12, pady=(0, 2))
        self._keep_iptc_var = tk.BooleanVar(value=True)
        ctk.CTkSwitch(meta_frame, text="", variable=self._keep_iptc_var).grid(row=2, column=1, sticky="e", padx=12, pady=(0, 2))

        meta_btn = ctk.CTkButton(
            meta_frame, 
            textvariable=I18N.tvar(meta_frame, "meta_edit"),
            fg_color="transparent", 
            border_width=1, 
            border_color="#2d4a7a",
            hover_color="#1a2b4a",
            command=self._open_metadata_editor,
            height=28
        )
        meta_btn.grid(row=3, column=0, columnspan=2, sticky="ew", padx=12, pady=(5, 10))

        self._on_resize_toggle()

    # ------------------------------------------------------------------
    # Right panel (Preview + History)
    # ------------------------------------------------------------------
    def _build_right_panel(self):
        right = ctk.CTkFrame(self, fg_color="#0d1117", corner_radius=0)
        right.grid(row=1, column=2, sticky="nsew", padx=10, pady=10)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(3, weight=1)  # History takes remaining space

        lbl1 = ctk.CTkLabel(right, textvariable=I18N.tvar(right, "preview_hdr"), font=("Segoe UI Semibold", 14), anchor="w")
        lbl1.grid(row=0, column=0, sticky="w", padx=12, pady=(10, 0))

        self._preview = PreviewPanel(right, fg_color="#111820", corner_radius=8)
        self._preview.grid(row=1, column=0, sticky="ew", padx=12, pady=10)

        lbl2 = ctk.CTkLabel(right, textvariable=I18N.tvar(right, "hist_hdr"), font=("Segoe UI Semibold", 14), anchor="w")
        lbl2.grid(row=2, column=0, sticky="w", padx=12, pady=(10, 0))

        self._history = HistoryPanel(right, fg_color="#111820", corner_radius=8)
        self._history.grid(row=3, column=0, sticky="nsew", padx=12, pady=(10, 12))

    # ==================================================================
    # Event handlers
    # ==================================================================
    def _on_resize_toggle(self):
        is_on = self._resize_var.get()
        state = "normal" if is_on else "disabled"
        self._resize_w.configure(state=state)
        self._resize_h.configure(state=state)

    def _on_width_changed(self, event):
        if not self._files or not self._resize_var.get() or event.keysym in ("Tab", "Return"): return
        try:
            w_str = self._resize_w.get().strip()
            if not w_str: return
            w_val = int(w_str)
            from PIL import Image
            with Image.open(self._files[0]) as img:
                orig_w, orig_h = img.size
            if orig_w > 0:
                h_val = int(orig_h * (w_val / orig_w))
                self._resize_h.delete(0, 'end')
                self._resize_h.insert(0, str(h_val))
        except Exception:
            pass

    def _on_height_changed(self, event):
        if not self._files or not self._resize_var.get() or event.keysym in ("Tab", "Return"): return
        try:
            h_str = self._resize_h.get().strip()
            if not h_str: return
            h_val = int(h_str)
            from PIL import Image
            with Image.open(self._files[0]) as img:
                orig_w, orig_h = img.size
            if orig_h > 0:
                w_val = int(orig_w * (h_val / orig_h))
                self._resize_w.delete(0, 'end')
                self._resize_w.insert(0, str(w_val))
        except Exception:
            pass

    def _open_metadata_editor(self):
        MetadataModal(self, self._custom_meta, self._on_metadata_saved)

    def _on_metadata_saved(self, new_meta: dict):
        self._custom_meta = new_meta

    def _on_files_changed(self, files: list[str]):
        self._files = files
        n = len(files)
        
        if n > 0:
            btn_txt = f"{I18N.get('btn_convert_all')} ({n} {'Files' if I18N.current_lang() == 'en' else 'Archivos'})"
        else:
            btn_txt = I18N.get("btn_convert_all")
            
        # Temporarily bypass stringvar for the dynamic file count in button
        self._convert_btn.configure(textvariable="")
        self._convert_btn.configure(text=btn_txt)

        self._successful_original_files.clear()
        self._delete_orig_btn.configure(state="disabled")

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
            return
        if self._converter is None:
            messagebox.showerror("Error", "pillow-avif-plugin is required.")
            return

        quality = int(self._quality_var.get())
        speed_label = self._speed_menu.get()
        speed = self._speed_map.get(speed_label, 5)
        subsampling = "4:2:0" if "4:2:0" in self._subsampling_menu.get() else "4:4:4"

        resize_enabled = self._resize_var.get()
        resize_w, resize_h = 0, 0
        if resize_enabled:
            w_str, h_str = self._resize_w.get().strip(), self._resize_h.get().strip()
            try: resize_w = int(w_str) if w_str else 0
            except: pass
            try: resize_h = int(h_str) if h_str else 0
            except: pass
            
        resize_cfg = {"enabled": resize_enabled, "width": resize_w, "height": resize_h}

        self._converting = True
        self._convert_btn.configure(state="disabled")
        self._delete_orig_btn.configure(state="disabled")
        self._stop_event.clear()
        self._successful_original_files.clear()

        keep_exif = self._keep_exif_var.get()
        keep_iptc = self._keep_iptc_var.get()

        thread = threading.Thread(
            target=self._run_batch,
            args=(self._files.copy(), None, quality, keep_exif, keep_iptc, self._custom_meta, speed, subsampling, resize_cfg),
            daemon=True,
        )
        thread.start()

    def _run_batch(self, files, output_dir, quality, keep_exif, keep_iptc, custom_meta, speed, subsampling, resize_cfg):
        import logging
        logger = logging.getLogger(__name__)

        def progress_cb(idx, total, result):
            logger.info("Queue put: progress %d/%d %s", idx, total, result.source_path)
            self._queue.put(("progress", idx, total, result))

        try:
            self._converter.convert_batch(
                input_paths  = files,
                output_dir   = output_dir,
                quality      = quality,
                keep_exif    = keep_exif,
                keep_iptc    = keep_iptc,
                custom_meta  = custom_meta,
                speed        = speed,
                subsampling  = subsampling,
                resize_cfg   = resize_cfg,
                progress_cb  = progress_cb,
                stop_event   = self._stop_event,
            )
        except Exception as exc:
            log_exception(logger, "convert_batch raised", exc)
            self._queue.put(("error", str(exc)))
        finally:
            self._queue.put(("done",))

    def _poll_queue(self):
        import logging
        logger = logging.getLogger(__name__)
        
        while not self._queue.empty():
            try:
                msg = self._queue.get_nowait()
            except queue.Empty:
                break

            try:
                if msg[0] == "progress":
                    _, idx, total, result = msg
                    logger.info("Poll: adding result %d/%d to history: %s", idx, total, result.source_path)
                    self._history.add_result(result)
                    if result.success:
                        self._successful_original_files.add(result.source_path)
                        self._preview.set_before(result.source_path)
                        self._preview.set_after(result.output_path)
                elif msg[0] == "error":
                    logger.error("Poll: conversion error: %s", msg[1] if len(msg) > 1 else "unknown")
                elif msg[0] == "done":
                    logger.info("Poll: batch done")
                    self._converting = False
                    n = len(self._files)
                    btn_txt = f"{I18N.get('btn_convert_all')} ({n} {'Files' if I18N.current_lang() == 'en' else 'Archivos'})" if n else I18N.get('btn_convert_all')
                    self._convert_btn.configure(state="normal", text=btn_txt)
                    
                    if len(self._files) > 0 and len(self._successful_original_files) == len(self._files):
                        self._delete_orig_btn.configure(state="normal")
            except Exception as exc:
                log_exception(logger, ("Poll: exception processing message %s" % msg[0]), exc)

        self.after(80, self._poll_queue)

    def _delete_originals(self):
        title = I18N.get("delete_confirm_title")
        msg = I18N.get("delete_confirm_msg")
        if not messagebox.askyesno(title, msg, parent=self):
            return
            
        import logging
        logger = logging.getLogger(__name__)
        
        deleted_count = 0
        for fpath in list(self._successful_original_files):
            try:
                ext = os.path.splitext(fpath)[1].lower()
                if ext in ('.png', '.jpeg', '.jpg') and os.path.exists(fpath):
                    os.remove(fpath)
                    self._successful_original_files.discard(fpath)
                    deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete {fpath}: {e}")
                
        if deleted_count > 0:
            succ_title = I18N.get("delete_success_title")
            succ_msg = I18N.get("delete_success_msg")
            messagebox.showinfo(succ_title, succ_msg, parent=self)
            
            if not self._successful_original_files:
                self._delete_orig_btn.configure(state="disabled")
                
            self._drop_zone.clear_all()
