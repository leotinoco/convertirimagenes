"""
metadata_modal.py - Modal dialog for editing metadata.
"""
from __future__ import annotations

import customtkinter as ctk
import tkinter as tk
from utils.i18n import I18N

class MetadataModal(ctk.CTkToplevel):
    def __init__(self, master, current_meta: dict | None = None, on_save=None):
        super().__init__(master)
        
        self.title("Metadata Editor")
        self.geometry("450x650")
        self.attributes("-topmost", True)
        self.resizable(False, False)
        
        # Keep modal central to master
        if master:
            x = master.winfo_rootx() + (master.winfo_width() // 2) - 200
            y = master.winfo_rooty() + (master.winfo_height() // 2) - 190
            self.geometry(f"+{x}+{y}")
            
        self._on_save_callback = on_save
        self._current_meta = current_meta or {}
        
        self._build_ui()
        self.focus_force()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        ctk.CTkLabel(
            hdr, 
            textvariable=I18N.tvar(hdr, "edit_meta_title"),
            font=("Segoe UI Semibold", 16)
        ).pack(side="left")

        # Form content
        content = ctk.CTkFrame(self, fg_color="#111820")
        content.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        content.columnconfigure(1, weight=1)

        # Form layout
        row = 0
        self._entries = {}
        fields = [
            ("title", "f_title"),
            ("author", "f_author"),
            ("copyright", "f_copy"),
            ("date_created", "f_created"),
            ("date_modified", "f_modified"),
            ("description", "f_desc"),
        ]

        for key, lang_key in fields:
            lbl = ctk.CTkLabel(content, textvariable=I18N.tvar(content, lang_key), font=("Segoe UI", 12))
            lbl.grid(row=row, column=0, sticky="w", padx=10, pady=(10, 0))
            
            val = self._current_meta.get(key, "")
            var = tk.StringVar(value=val)
            self._entries[key] = var
            
            # For description, it would be nice to have a larger entry but CTkTextbox is harder to bind vars to.
            # Entry is fine for this task.
            entry = ctk.CTkEntry(content, textvariable=var, font=("Segoe UI", 12))
            entry.grid(row=row+1, column=0, sticky="ew", padx=10, pady=(4, 10))
            row += 2

        # Footer
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="e", padx=20, pady=(10, 20))
        
        cancel = ctk.CTkButton(
            footer, 
            textvariable=I18N.tvar(footer, "cancel"), 
            font=("Segoe UI", 12),
            width=100,
            fg_color="#3a1a1a",
            hover_color="#5a2a2a",
            command=self.destroy
        )
        cancel.pack(side="left", padx=(0, 10))

        save = ctk.CTkButton(
            footer, 
            textvariable=I18N.tvar(footer, "save"),
            font=("Segoe UI Semibold", 12),
            width=100,
            command=self._save
        )
        save.pack(side="left")

    def _save(self):
        result = {k: v.get().strip() for k, v in self._entries.items() if v.get().strip()}
        if self._on_save_callback:
            self._on_save_callback(result)
        self.destroy()
