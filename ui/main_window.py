"""
main_window.py — Main application window.

Layout (3-column responsive grid):
  ┌─────────────────┬─────────────────┬─────────────────┐
  │  File Mgmt      │  Settings       │  Preview        │
  │  (DropZone)     │  (Config)       │  (Split)        │
  │  Progress/Cancel│  Output dest.   ├─────────────────┤
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
from utils import theme


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
        self.configure(fg_color=theme.BG)

        # State
        self._files: list[str] = []
        self._custom_meta: dict = {}
        self._converting = False
        self._stop_event = threading.Event()
        self._queue: queue.Queue = queue.Queue()
        self._converter: Converter | None = None
        self._successful_original_files: set[str] = set()
        self._output_dir: str | None = None      # None → same folder as original
        self._batch_saved_bytes = 0
        self._batch_ok = 0
        self._batch_total = 0

        # Try to initialise converter (may fail if plugin missing)
        try:
            self._converter = Converter()
        except RuntimeError:
            pass  # Error shown on convert

        self._build_ui()
        # Default excluded format
        self._drop_zone.set_excluded_format(".avif")
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
    # Section-card helper
    # ------------------------------------------------------------------
    def _card(self, parent, title_key: str) -> ctk.CTkFrame:
        """Create a titled card and return it (content starts at row 1)."""
        card = ctk.CTkFrame(
            parent, fg_color=theme.CARD, corner_radius=theme.RADIUS,
            border_width=1, border_color=theme.BORDER,
        )
        card.columnconfigure(0, weight=1)
        ctk.CTkLabel(
            card, textvariable=I18N.tvar(card, title_key),
            font=theme.font(12, "bold"), text_color=theme.ACCENT_TEXT, anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(12, 6))
        return card

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=theme.SURFACE, corner_radius=0, height=58)
        header.grid(row=0, column=0, columnspan=3, sticky="ew")
        header.grid_propagate(False)
        header.columnconfigure(1, weight=1)

        logo = ctk.CTkLabel(
            header,
            textvariable=I18N.tvar(header, "title"),
            font=theme.font(19, "bold"),
            text_color=theme.ACCENT_TEXT,
        )
        logo.grid(row=0, column=0, padx=20, pady=10, sticky="w")

        lang_frame = ctk.CTkFrame(header, fg_color="transparent")
        lang_frame.grid(row=0, column=2, padx=20, sticky="e")

        self._lang_var = tk.StringVar(value=I18N.current_lang())
        lang_switch = ctk.CTkSegmentedButton(
            lang_frame,
            values=["en", "es"],
            variable=self._lang_var,
            command=self._on_lang_changed,
            font=theme.font(12),
            fg_color=theme.CARD,
            selected_color=theme.ACCENT,
            selected_hover_color=theme.ACCENT_HOVER,
            unselected_color=theme.CARD_ALT,
        )
        lang_switch.pack(side="right")

    def _on_lang_changed(self, value):
        # Remember current selections before rebuilding translated menus
        prev_speed = self._speed_map.get(self._speed_menu.get(), 5)
        prev_sub_444 = "4:4:4" in self._subsampling_menu.get()

        I18N.set_language(value)

        self._speed_map = {I18N.get("speed_slow"): 2, I18N.get("speed_med"): 5, I18N.get("speed_fast"): 8}
        self._speed_menu.configure(values=list(self._speed_map.keys()))
        for label, spd in self._speed_map.items():
            if spd == prev_speed:
                self._speed_menu.set(label)
                break

        self._subsampling_menu.configure(values=[I18N.get("sub_420"), I18N.get("sub_444")])
        self._subsampling_menu.set(I18N.get("sub_444") if prev_sub_444 else I18N.get("sub_420"))
        self._update_output_dir_label()
        self._set_status_idle()

    # ------------------------------------------------------------------
    # Left panel (File Mgmt + progress)
    # ------------------------------------------------------------------
    def _build_left_panel(self):
        left = ctk.CTkFrame(self, fg_color=theme.SURFACE, corner_radius=theme.RADIUS)
        left.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=12)
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        lbl = ctk.CTkLabel(left, textvariable=I18N.tvar(left, "file_mgmt"),
                           font=theme.font(14, "bold"), text_color=theme.TEXT, anchor="w")
        lbl.grid(row=0, column=0, sticky="w", padx=14, pady=(12, 0))

        self._drop_zone = DropZone(
            left,
            on_files_changed=self._on_files_changed,
            fg_color="transparent",
            corner_radius=0,
        )
        self._drop_zone.grid(row=1, column=0, sticky="nsew")

        # --- Progress bar + status ---
        prog_frame = ctk.CTkFrame(left, fg_color="transparent")
        prog_frame.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 4))
        prog_frame.columnconfigure(0, weight=1)

        self._progress = ctk.CTkProgressBar(
            prog_frame, height=8, corner_radius=4,
            fg_color=theme.CARD_ALT, progress_color=theme.ACCENT,
        )
        self._progress.set(0)
        self._progress.grid(row=0, column=0, sticky="ew")

        self._status_var = tk.StringVar(value=I18N.get("status_idle"))
        self._status_lbl = ctk.CTkLabel(
            prog_frame, textvariable=self._status_var,
            font=theme.font(11), text_color=theme.TEXT_MUTED, anchor="w",
        )
        self._status_lbl.grid(row=1, column=0, sticky="w", pady=(4, 0))

        # --- Convert + Cancel ---
        btn_row = ctk.CTkFrame(left, fg_color="transparent")
        btn_row.grid(row=3, column=0, sticky="ew", padx=14, pady=(4, 8))
        btn_row.columnconfigure(0, weight=1)

        self._convert_btn = ctk.CTkButton(
            btn_row,
            textvariable=I18N.tvar(btn_row, "btn_convert_all"),
            font=theme.font(15, "bold"),
            height=46,
            corner_radius=theme.RADIUS_SM,
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            command=self._start_conversion,
        )
        self._convert_btn.grid(row=0, column=0, sticky="ew")

        self._cancel_btn = ctk.CTkButton(
            btn_row,
            textvariable=I18N.tvar(btn_row, "btn_cancel_conv"),
            font=theme.font(13, "bold"),
            height=46,
            width=120,
            corner_radius=theme.RADIUS_SM,
            fg_color=theme.CARD_ALT,
            hover_color=theme.DANGER_HOVER,
            text_color=theme.TEXT,
            state="disabled",
            command=self._cancel_conversion,
        )
        self._cancel_btn.grid(row=0, column=1, sticky="e", padx=(8, 0))

        self._delete_orig_btn = ctk.CTkButton(
            left,
            textvariable=I18N.tvar(left, "btn_delete_originals"),
            font=theme.font(13, "bold"),
            height=40,
            corner_radius=theme.RADIUS_SM,
            fg_color=theme.DANGER_SOFT,
            hover_color=theme.DANGER_HOVER,
            text_color="#ffb4b4",
            text_color_disabled=theme.TEXT_FAINT,
            border_width=1,
            border_color=theme.DANGER,
            state="disabled",
            command=self._delete_originals,
        )
        self._delete_orig_btn.grid(row=4, column=0, sticky="ew", padx=14, pady=(0, 14))

    # ------------------------------------------------------------------
    # Middle panel (Settings)
    # ------------------------------------------------------------------
    def _build_middle_panel(self):
        mid_outer = ctk.CTkFrame(self, fg_color=theme.SURFACE, corner_radius=theme.RADIUS)
        mid_outer.grid(row=1, column=1, sticky="nsew", padx=6, pady=12)
        mid_outer.columnconfigure(0, weight=1)
        mid_outer.rowconfigure(1, weight=1)

        lbl = ctk.CTkLabel(mid_outer, textvariable=I18N.tvar(mid_outer, "settings_hdr"),
                           font=theme.font(14, "bold"), text_color=theme.TEXT, anchor="w")
        lbl.grid(row=0, column=0, sticky="w", padx=14, pady=(12, 4))

        mid = ctk.CTkScrollableFrame(mid_outer, fg_color="transparent")
        mid.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 8))
        mid.columnconfigure(0, weight=1)

        # 1. Output Format
        fmt_frame = self._card(mid, "fmt_hdr")
        fmt_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=(4, 10))

        self._output_format_var = tk.StringVar(value="AVIF")
        self._format_switch = ctk.CTkSegmentedButton(
            fmt_frame,
            values=["AVIF", "WEBP", "JPG", "PNG"],
            variable=self._output_format_var,
            command=self._on_format_changed,
            font=theme.font(12, "bold"),
            fg_color=theme.CARD_ALT,
            selected_color=theme.ACCENT,
            selected_hover_color=theme.ACCENT_HOVER,
            unselected_color=theme.CARD_ALT,
        )
        self._format_switch.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 14))

        # 2. Settings & Optimization
        opt_frame = self._card(mid, "settings_opt")
        opt_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 10))

        self._q_frame = ctk.CTkFrame(opt_frame, fg_color="transparent")
        self._q_frame.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 2))
        self._q_frame.columnconfigure(1, weight=1)

        ctk.CTkLabel(self._q_frame, textvariable=I18N.tvar(self._q_frame, "q_lbl"),
                     font=theme.font(12), text_color=theme.TEXT).grid(row=0, column=0, sticky="w")
        self._quality_var = tk.IntVar(value=65)
        ctk.CTkLabel(self._q_frame, textvariable=self._quality_var,
                     font=theme.font(12, "bold"), text_color=theme.ACCENT_TEXT).grid(row=0, column=2, sticky="e")
        ctk.CTkSlider(
            self._q_frame, from_=0, to=100, variable=self._quality_var,
            button_color=theme.ACCENT, button_hover_color=theme.ACCENT_HOVER,
            progress_color=theme.ACCENT, fg_color=theme.CARD_ALT,
            command=lambda v: self._quality_var.set(int(v)),
        ).grid(row=1, column=0, columnspan=3, sticky="ew", pady=(2, 0))

        self._speed_lbl = ctk.CTkLabel(opt_frame, textvariable=I18N.tvar(opt_frame, "speed_lbl"),
                                       font=theme.font(12), text_color=theme.TEXT)
        self._speed_lbl.grid(row=2, column=0, sticky="w", padx=14, pady=(8, 0))
        self._speed_map = {I18N.get("speed_slow"): 2, I18N.get("speed_med"): 5, I18N.get("speed_fast"): 8}
        self._speed_menu = ctk.CTkOptionMenu(
            opt_frame, values=list(self._speed_map.keys()), font=theme.font(12),
            fg_color=theme.CARD_ALT, button_color=theme.ACCENT_SOFT,
            button_hover_color=theme.ACCENT_HOVER, dropdown_fg_color=theme.CARD,
        )
        self._speed_menu.grid(row=3, column=0, sticky="ew", padx=14, pady=(2, 2))

        self._sub_lbl = ctk.CTkLabel(opt_frame, textvariable=I18N.tvar(opt_frame, "sub_lbl"),
                                     font=theme.font(12), text_color=theme.TEXT)
        self._sub_lbl.grid(row=4, column=0, sticky="w", padx=14, pady=(8, 0))
        self._subsampling_menu = ctk.CTkOptionMenu(
            opt_frame, values=[I18N.get("sub_420"), I18N.get("sub_444")], font=theme.font(12),
            fg_color=theme.CARD_ALT, button_color=theme.ACCENT_SOFT,
            button_hover_color=theme.ACCENT_HOVER, dropdown_fg_color=theme.CARD,
        )
        self._subsampling_menu.grid(row=5, column=0, sticky="ew", padx=14, pady=(2, 0))

        self._sub_warn_lbl = ctk.CTkLabel(opt_frame, textvariable=I18N.tvar(opt_frame, "sub_warn"),
                                          font=theme.font(10), text_color=theme.TEXT_FAINT)
        self._sub_warn_lbl.grid(row=6, column=0, sticky="w", padx=14, pady=(2, 5))

        # Threads slider (CPU count)
        t_frame = ctk.CTkFrame(opt_frame, fg_color="transparent")
        t_frame.grid(row=7, column=0, sticky="ew", padx=14, pady=(0, 12))
        t_frame.columnconfigure(1, weight=1)
        max_threads = os.cpu_count() or 4
        ctk.CTkLabel(t_frame, textvariable=I18N.tvar(t_frame, "threads_lbl"),
                     font=theme.font(12), text_color=theme.TEXT).grid(row=0, column=0, sticky="w")
        self._threads_var = tk.IntVar(value=max_threads)
        ctk.CTkLabel(t_frame, textvariable=self._threads_var,
                     font=theme.font(12, "bold"), text_color=theme.ACCENT_TEXT).grid(row=0, column=2, sticky="e")
        ctk.CTkSlider(
            t_frame, from_=1, to=max_threads, number_of_steps=max(1, max_threads - 1),
            variable=self._threads_var,
            button_color=theme.ACCENT, button_hover_color=theme.ACCENT_HOVER,
            progress_color=theme.ACCENT, fg_color=theme.CARD_ALT,
            command=lambda v: self._threads_var.set(int(v)),
        ).grid(row=1, column=0, columnspan=3, sticky="ew", pady=(2, 0))

        # 3. Output destination
        out_frame = self._card(mid, "out_hdr")
        out_frame.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 10))
        out_frame.columnconfigure(0, weight=1)

        self._out_dir_var = tk.StringVar(value=I18N.get("out_same_folder"))
        out_lbl = ctk.CTkLabel(
            out_frame, textvariable=self._out_dir_var, font=theme.font(11),
            text_color=theme.TEXT_MUTED, anchor="w", wraplength=330,
        )
        out_lbl.grid(row=1, column=0, columnspan=2, sticky="ew", padx=14, pady=(0, 4))

        out_btns = ctk.CTkFrame(out_frame, fg_color="transparent")
        out_btns.grid(row=2, column=0, columnspan=2, sticky="ew", padx=14, pady=(0, 8))
        out_btns.columnconfigure(0, weight=1)

        ctk.CTkButton(
            out_btns, textvariable=I18N.tvar(out_btns, "btn_choose_folder"),
            font=theme.font(12), height=30, corner_radius=theme.RADIUS_SM,
            fg_color=theme.ACCENT_SOFT, hover_color=theme.ACCENT_HOVER,
            command=self._choose_output_dir,
        ).grid(row=0, column=0, sticky="ew")

        ctk.CTkButton(
            out_btns, textvariable=I18N.tvar(out_btns, "btn_reset_folder"),
            font=theme.font(13), height=30, width=36, corner_radius=theme.RADIUS_SM,
            fg_color=theme.CARD_ALT, hover_color=theme.ACCENT_SOFT,
            command=self._reset_output_dir,
        ).grid(row=0, column=1, padx=(8, 0))

        ctk.CTkLabel(out_frame, textvariable=I18N.tvar(out_frame, "suffix_lbl"),
                     font=theme.font(11), text_color=theme.TEXT_MUTED).grid(
            row=3, column=0, sticky="w", padx=14, pady=(0, 2))
        self._suffix_entry = ctk.CTkEntry(
            out_frame, placeholder_text="-opt", height=30,
            fg_color=theme.CARD_ALT, border_color=theme.BORDER, corner_radius=theme.RADIUS_SM,
        )
        self._suffix_entry.grid(row=4, column=0, columnspan=2, sticky="ew", padx=14, pady=(0, 12))

        # 4. Resizing Options
        res_frame = self._card(mid, "resize_hdr")
        res_frame.grid(row=3, column=0, sticky="ew", padx=8, pady=(0, 10))
        res_frame.columnconfigure(1, weight=1)

        self._resize_var = tk.BooleanVar(value=False)
        ctk.CTkLabel(res_frame, textvariable=I18N.tvar(res_frame, "resize_en"),
                     font=theme.font(12), text_color=theme.TEXT).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 2))
        self._resize_sw = ctk.CTkSwitch(
            res_frame, text="", variable=self._resize_var, command=self._on_resize_toggle,
            progress_color=theme.ACCENT,
        )
        self._resize_sw.grid(row=1, column=1, sticky="e", padx=14, pady=(0, 2))

        wh_frame = ctk.CTkFrame(res_frame, fg_color="transparent")
        wh_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=14, pady=(0, 12))
        wh_frame.columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(wh_frame, textvariable=I18N.tvar(wh_frame, "width"),
                     font=theme.font(11), text_color=theme.TEXT_MUTED).grid(row=0, column=0, sticky="w")
        self._resize_w = ctk.CTkEntry(wh_frame, placeholder_text="1920", height=30,
                                      fg_color=theme.CARD_ALT, border_color=theme.BORDER,
                                      corner_radius=theme.RADIUS_SM)
        self._resize_w.grid(row=1, column=0, sticky="ew", padx=(0, 5))
        self._resize_w.bind("<KeyRelease>", self._on_width_changed)

        ctk.CTkLabel(wh_frame, textvariable=I18N.tvar(wh_frame, "height"),
                     font=theme.font(11), text_color=theme.TEXT_MUTED).grid(row=0, column=1, sticky="w")
        self._resize_h = ctk.CTkEntry(wh_frame, placeholder_text="1080", height=30,
                                      fg_color=theme.CARD_ALT, border_color=theme.BORDER,
                                      corner_radius=theme.RADIUS_SM)
        self._resize_h.grid(row=1, column=1, sticky="ew", padx=(5, 0))
        self._resize_h.bind("<KeyRelease>", self._on_height_changed)

        # 5. Metadata
        meta_frame = self._card(mid, "meta_hdr")
        meta_frame.grid(row=4, column=0, sticky="ew", padx=8, pady=(0, 8))
        meta_frame.columnconfigure(1, weight=1)

        ctk.CTkLabel(meta_frame, textvariable=I18N.tvar(meta_frame, "meta_exif"),
                     font=theme.font(12), text_color=theme.TEXT).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 2))
        self._keep_exif_var = tk.BooleanVar(value=True)
        ctk.CTkSwitch(meta_frame, text="", variable=self._keep_exif_var,
                      progress_color=theme.ACCENT).grid(row=1, column=1, sticky="e", padx=14, pady=(0, 2))

        ctk.CTkLabel(meta_frame, textvariable=I18N.tvar(meta_frame, "meta_iptc"),
                     font=theme.font(12), text_color=theme.TEXT).grid(row=2, column=0, sticky="w", padx=14, pady=(0, 2))
        self._keep_iptc_var = tk.BooleanVar(value=True)
        ctk.CTkSwitch(meta_frame, text="", variable=self._keep_iptc_var,
                      progress_color=theme.ACCENT).grid(row=2, column=1, sticky="e", padx=14, pady=(0, 2))

        meta_btn = ctk.CTkButton(
            meta_frame,
            textvariable=I18N.tvar(meta_frame, "meta_edit"),
            fg_color="transparent",
            border_width=1,
            border_color=theme.BORDER,
            hover_color=theme.ACCENT_SOFT,
            text_color=theme.ACCENT_TEXT,
            corner_radius=theme.RADIUS_SM,
            command=self._open_metadata_editor,
            height=30,
        )
        meta_btn.grid(row=3, column=0, columnspan=2, sticky="ew", padx=14, pady=(6, 12))

        self._on_resize_toggle()

    # ------------------------------------------------------------------
    # Right panel (Preview + History)
    # ------------------------------------------------------------------
    def _build_right_panel(self):
        right = ctk.CTkFrame(self, fg_color=theme.SURFACE, corner_radius=theme.RADIUS)
        right.grid(row=1, column=2, sticky="nsew", padx=(6, 12), pady=12)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(3, weight=1)  # History takes remaining space

        lbl1 = ctk.CTkLabel(right, textvariable=I18N.tvar(right, "preview_hdr"),
                            font=theme.font(14, "bold"), text_color=theme.TEXT, anchor="w")
        lbl1.grid(row=0, column=0, sticky="w", padx=14, pady=(12, 0))

        self._preview = PreviewPanel(right, fg_color=theme.CARD, corner_radius=theme.RADIUS,
                                     border_width=1, border_color=theme.BORDER)
        self._preview.grid(row=1, column=0, sticky="ew", padx=14, pady=10)

        lbl2 = ctk.CTkLabel(right, textvariable=I18N.tvar(right, "hist_hdr"),
                            font=theme.font(14, "bold"), text_color=theme.TEXT, anchor="w")
        lbl2.grid(row=2, column=0, sticky="w", padx=14, pady=(6, 0))

        self._history = HistoryPanel(right, fg_color=theme.CARD, corner_radius=theme.RADIUS,
                                     border_width=1, border_color=theme.BORDER)
        self._history.grid(row=3, column=0, sticky="nsew", padx=14, pady=(10, 14))

    # ==================================================================
    # Event handlers
    # ==================================================================
    def _on_resize_toggle(self):
        is_on = self._resize_var.get()
        state = "normal" if is_on else "disabled"
        self._resize_w.configure(state=state)
        self._resize_h.configure(state=state)

    def _on_format_changed(self, value):
        fmt = value.lower()
        self._drop_zone.set_excluded_format(f".{fmt}")

        if fmt == "avif":
            self._q_frame.grid()
            self._speed_lbl.grid()
            self._speed_menu.grid()
            self._sub_lbl.grid()
            self._subsampling_menu.grid()
            self._sub_warn_lbl.grid()
        elif fmt in ("jpg", "webp"):
            self._q_frame.grid()
            self._speed_lbl.grid_remove()
            self._speed_menu.grid_remove()
            self._sub_lbl.grid_remove()
            self._subsampling_menu.grid_remove()
            self._sub_warn_lbl.grid_remove()
        elif fmt == "png":
            self._q_frame.grid_remove()
            self._speed_lbl.grid_remove()
            self._speed_menu.grid_remove()
            self._sub_lbl.grid_remove()
            self._subsampling_menu.grid_remove()
            self._sub_warn_lbl.grid_remove()

    def _choose_output_dir(self):
        path = filedialog.askdirectory(parent=self)
        if path:
            self._output_dir = path
            self._update_output_dir_label()

    def _reset_output_dir(self):
        self._output_dir = None
        self._update_output_dir_label()

    def _update_output_dir_label(self):
        if self._output_dir:
            self._out_dir_var.set(f"📁 {self._output_dir}")
        else:
            self._out_dir_var.set(I18N.get("out_same_folder"))

    def _set_status_idle(self):
        if not self._converting:
            self._status_var.set(I18N.get("status_idle"))

    def _on_width_changed(self, event):
        if not self._files or not self._resize_var.get() or event.keysym in ("Tab", "Return"):
            return
        try:
            w_str = self._resize_w.get().strip()
            if not w_str:
                return
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
        if not self._files or not self._resize_var.get() or event.keysym in ("Tab", "Return"):
            return
        try:
            h_str = self._resize_h.get().strip()
            if not h_str:
                return
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

        # Disk-space validation on the destination volume
        check_dir = self._output_dir or os.path.dirname(self._files[0])
        try:
            ok, needed, free = DiskValidator.has_enough_space(self._files, check_dir)
            if not ok:
                messagebox.showerror(
                    I18N.get("disk_title"),
                    f"{I18N.get('disk_msg')}\n\n"
                    f"~{format_bytes(needed)} > {format_bytes(free)}",
                    parent=self,
                )
                return
        except Exception:
            pass  # never block conversion on validator errors

        quality = int(self._quality_var.get())
        speed_label = self._speed_menu.get()
        speed = self._speed_map.get(speed_label, 5)
        subsampling = "4:2:0" if "4:2:0" in self._subsampling_menu.get() else "4:4:4"

        resize_enabled = self._resize_var.get()
        resize_w, resize_h = 0, 0
        if resize_enabled:
            w_str, h_str = self._resize_w.get().strip(), self._resize_h.get().strip()
            try:
                resize_w = int(w_str) if w_str else 0
            except ValueError:
                pass
            try:
                resize_h = int(h_str) if h_str else 0
            except ValueError:
                pass

        resize_cfg = {"enabled": resize_enabled, "width": resize_w, "height": resize_h}

        self._converting = True
        self._convert_btn.configure(state="disabled")
        self._cancel_btn.configure(state="normal", fg_color=theme.DANGER)
        self._delete_orig_btn.configure(state="disabled")
        self._stop_event.clear()
        self._successful_original_files.clear()
        self._batch_saved_bytes = 0
        self._batch_ok = 0
        self._batch_total = len(self._files)
        self._progress.set(0)
        self._status_var.set(I18N.get("status_converting"))

        keep_exif = self._keep_exif_var.get()
        keep_iptc = self._keep_iptc_var.get()
        output_format = self._output_format_var.get().lower()
        max_workers = int(self._threads_var.get())
        suffix = self._suffix_entry.get().strip()

        thread = threading.Thread(
            target=self._run_batch,
            args=(self._files.copy(), self._output_dir, quality, keep_exif, keep_iptc,
                  self._custom_meta, speed, subsampling, resize_cfg, output_format,
                  max_workers, suffix),
            daemon=True,
        )
        thread.start()

    def _cancel_conversion(self):
        if self._converting:
            self._stop_event.set()
            self._status_var.set(I18N.get("status_cancel"))
            self._cancel_btn.configure(state="disabled")

    def _run_batch(self, files, output_dir, quality, keep_exif, keep_iptc, custom_meta,
                   speed, subsampling, resize_cfg, output_format, max_workers, suffix):
        import logging
        logger = logging.getLogger(__name__)

        def progress_cb(idx, total, result):
            self._queue.put(("progress", idx, total, result))

        try:
            self._converter.convert_batch(
                input_paths=files,
                output_dir=output_dir,
                quality=quality,
                keep_exif=keep_exif,
                keep_iptc=keep_iptc,
                custom_meta=custom_meta,
                speed=speed,
                subsampling=subsampling,
                resize_cfg=resize_cfg,
                max_workers=max_workers,
                progress_cb=progress_cb,
                stop_event=self._stop_event,
                output_format=output_format,
                suffix=suffix,
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
                    self._history.add_result(result)
                    if total > 0:
                        self._progress.set(idx / total)
                    self._status_var.set(f"{I18N.get('status_converting')} {idx}/{total}")
                    if result.success:
                        self._batch_ok += 1
                        self._batch_saved_bytes += max(0, result.original_size - result.converted_size)
                        self._successful_original_files.add(result.source_path)
                        self._preview.set_before(result.source_path)
                        self._preview.set_after(result.output_path)
                elif msg[0] == "error":
                    logger.error("Poll: conversion error: %s", msg[1] if len(msg) > 1 else "unknown")
                elif msg[0] == "done":
                    was_canceled = self._stop_event.is_set()
                    self._converting = False
                    self._cancel_btn.configure(state="disabled", fg_color=theme.CARD_ALT)
                    n = len(self._files)
                    btn_txt = (f"{I18N.get('btn_convert_all')} ({n} "
                               f"{'Files' if I18N.current_lang() == 'en' else 'Archivos'})") if n else I18N.get('btn_convert_all')
                    self._convert_btn.configure(state="normal", text=btn_txt)

                    if was_canceled:
                        self._status_var.set(I18N.get("status_canceled"))
                    else:
                        self._progress.set(1.0)
                        summary = f"✔ {self._batch_ok}/{self._batch_total}"
                        if self._batch_saved_bytes > 0:
                            summary += f"  •  {I18N.get('summary_saved')}: {format_bytes(self._batch_saved_bytes)}"
                        self._status_var.set(summary)

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
                if ext in ('.png', '.jpeg', '.jpg', '.webp', '.avif') and os.path.exists(fpath):
                    os.remove(fpath)
                    self._successful_original_files.discard(fpath)
                    deleted_count += 1
            except Exception as e:
                logger.error("Failed to delete %s: %s", os.path.basename(fpath), e)

        if deleted_count > 0:
            succ_title = I18N.get("delete_success_title")
            succ_msg = I18N.get("delete_success_msg")
            messagebox.showinfo(succ_title, succ_msg, parent=self)

            if not self._successful_original_files:
                self._delete_orig_btn.configure(state="disabled")

            self._drop_zone.clear_all()
