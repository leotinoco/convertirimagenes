"""
i18n.py — Simple bilingual support via tkinter StringVars.
"""
from __future__ import annotations

import tkinter as tk

_LANG = "es"

_DICT = {
    "es": {
        "title": "ConvertirImagenes — PNG/JPG → AVIF",
        "drop_title": "⬇ Arrastra imágenes aquí",
        "drop_sub": "PNG, JPG soportados",
        "btn_browse": "📂 Examinar archivos",
        "btn_clear": "🗑 Limpiar lista",
        "file_mgmt": "Gestor de Archivos",
        "btn_convert_all": "▶ Convertir Todo",
        "speed_slow": "Photoshop / Máxima compresión (Lento)",
        "speed_med": "Equilibrado",
        "speed_fast": "Ultra Rápido",
        "sub_420": "4:2:0 (Recomendado para Web)",
        "sub_444": "4:4:4",
        "threads_lbl": "Núcleos a usar (Max Processor)",
        "settings_hdr": "Opciones de Conversión",
        "settings_opt": "Ajustes y Optimización",
        "q_lbl": "Calidad de Compresión",
        "speed_lbl": "Esfuerzo de Compresión",
        "sub_lbl": "Submuestreo de Color (Chroma)",
        "resize_hdr": "Opciones de Redimensionado",
        "resize_en": "Habilitar Redimensionamiento",
        "resize_keep": "Preservar Relación de Aspecto",
        "width": "Ancho (px)",
        "height": "Alto (px)",
        "meta_hdr": "Metadatos",
        "meta_exif": "Preservar EXIF",
        "meta_iptc": "Preservar IPTC",
        "meta_edit": "Modificar Metadatos",
        "preview_hdr": "Vista Previa (Antes → Después)",
        "before": "ANTES",
        "after": "DESPUÉS",
        "hist_hdr": "Historial de Conversiones",
        "hist_clear": "Limpiar Historial",
        "hist_status": "Listo para convertir",
        "edit_meta_title": "Editar Metadatos Reemplazables",
        "save": "Guardar",
        "cancel": "Cancelar",
        "col_file": "Archivo",
        "col_stat": "Estado",
        "col_size": "Tamaño (Antes → Después)",
        "col_saving": "Reducción",
        "col_time": "Hora",
        "col_subsampling": "Chroma",
        "col_action": "Acción",
        "hist_open_folder": "Abrir",
        "f_title": "Título / Nombre del Documento",
        "f_author": "Autor / Artista",
        "f_copy": "Derechos de Autor (Copyright)",
        "f_created": "Fecha de Creación (YYYY:MM:DD HH:MM:SS)",
        "f_modified": "Fecha de Modificación (YYYY:MM:DD HH:MM:SS)",
        "f_desc": "Descripción / Leyenda",
        "sub_warn": "* Si tiene transparencia, se usará automático 4:4:4",
        "status_ready": "Archivos listos.",
        "status_cancel": "Cancelando…",
        "lang_en": "English",
        "lang_es": "Español",
        "completed": "Completado",
        "error": "Error",
        "btn_delete_originals": "🗑 Eliminar archivos originales",
        "delete_confirm_title": "Confirmar eliminación",
        "delete_confirm_msg": "¿Estás seguro de que deseas eliminar los archivos originales (.png, .jpeg, .jpg) que ya fueron convertidos? Esta acción no se puede deshacer.",
        "delete_success_title": "Proceso completado",
        "delete_success_msg": "Los archivos originales se han eliminado correctamente."
    },
    "en": {
        "title": "Image Converter Pro Dashboard",
        "drop_title": "Drag & Drop Images Here",
        "drop_sub": "PNG, JPG supported",
        "btn_browse": "📂 Browse files",
        "btn_clear": "🗑 Clear list",
        "file_mgmt": "File Management",
        "btn_convert_all": "▶ Convert All",
        "speed_slow": "Photoshop / Max Compression (Slow)",
        "speed_med": "Balanced",
        "speed_fast": "Ultra Fast",
        "sub_420": "4:2:0 (Recommended for Web)",
        "sub_444": "4:4:4",
        "threads_lbl": "Max Processors (Cores)",
        "settings_hdr": "Conversion Settings",
        "settings_opt": "Settings & Optimization",
        "q_lbl": "Compression Quality",
        "speed_lbl": "Compression Effort",
        "sub_lbl": "Chroma Subsampling",
        "resize_hdr": "Resizing Options",
        "resize_en": "Enable Resize",
        "resize_keep": "Preserve Aspect Ratio",
        "width": "Width (px)",
        "height": "Height (px)",
        "meta_hdr": "Metadata",
        "meta_exif": "Preserve EXIF",
        "meta_iptc": "Preserve IPTC",
        "meta_edit": "Edit Metadata",
        "preview_hdr": "Preview (Before → After)",
        "before": "BEFORE",
        "after": "AFTER",
        "hist_hdr": "Conversion History",
        "hist_clear": "Clear History",
        "hist_status": "Ready to convert",
        "edit_meta_title": "Edit Replaceable Metadata",
        "save": "Save",
        "cancel": "Cancel",
        "col_file": "Filename",
        "col_stat": "Status",
        "col_size": "Size (Before → After)",
        "col_saving": "Savings",
        "col_time": "Time",
        "col_subsampling": "Chroma",
        "col_action": "Action",
        "hist_open_folder": "Open",
        "f_title": "Title / DocumentName",
        "f_author": "Author / Artist",
        "f_copy": "Copyright",
        "f_created": "Date Created (YYYY:MM:DD HH:MM:SS)",
        "f_modified": "Date Modified (YYYY:MM:DD HH:MM:SS)",
        "f_desc": "Description / Caption",
        "sub_warn": "* If transparent, 4:4:4 is used automatically",
        "status_ready": "Files ready.",
        "status_cancel": "Canceling…",
        "lang_en": "English",
        "lang_es": "Español",
        "completed": "Completed",
        "error": "Error",
        "btn_delete_originals": "🗑 Delete original files",
        "delete_confirm_title": "Confirm Deletion",
        "delete_confirm_msg": "Are you sure you want to delete the original files (.png, .jpeg, .jpg) that have already been converted? This action cannot be undone.",
        "delete_success_title": "Process Completed",
        "delete_success_msg": "The original files have been successfully deleted."
    }
}

class I18N:
    _vars: dict[str, tk.StringVar] = {}

    @classmethod
    def set_language(cls, lang: str):
        global _LANG
        if lang in _DICT:
            _LANG = lang
            cls._update_all()

    @classmethod
    def current_lang(cls) -> str:
        return _LANG

    @classmethod
    def get(cls, key: str) -> str:
        return _DICT[_LANG].get(key, key)

    @classmethod
    def tvar(cls, master, key: str) -> tk.StringVar:
        """Returns a string var that auto-updates when language changes."""
        if key not in cls._vars:
            v = tk.StringVar(master, value=cls.get(key))
            cls._vars[key] = v
        return cls._vars[key]

    @classmethod
    def _update_all(cls):
        for key, var_obj in cls._vars.items():
            if hasattr(var_obj, "set"):
                try:
                    var_obj.set(cls.get(key))
                except tk.TclError:
                    pass  # widget might have been destroyed
