"""
dnd_bootstrap.py — Safe TkinterDnD2 initialization with graceful degradation.

This module centralizes the *entire* DnD setup sequence so that every module
can import a single bool (`DND_READY`) and a helper (`enable_dnd_on_widget`)
without caring about how the Tcl extension was loaded.

Compatibility notes
-------------------
* **All platforms**  – ``tkinterdnd2 >= 0.6`` ships pre-built ``tkdnd`` Tcl
  binaries inside the package for Windows (x86, x64, arm64), Linux (x64,
  arm64) and macOS (Intel and Apple Silicon), including Tcl 9 builds.
  ``_require(root)`` loads the right one into the interpreter, so the old
  ``tkinterdnd2-universal`` fork for Apple Silicon is no longer needed.
* **Other architectures**  – If no bundled binary matches, ``_require`` fails
  and we degrade gracefully (the "Browse files" button still works).

PyInstaller
-----------
When freezing with PyInstaller, the hidden Tcl extension files inside
``tkinterdnd2`` are NOT collected automatically.  You **must** use::

    --collect-data tkinterdnd2

or, in the ``.spec`` file::

    from PyInstaller.utils.hooks import collect_data_files
    datas += collect_data_files('tkinterdnd2')

Otherwise the packaged executable will silently lack DnD support.
"""
from __future__ import annotations

import logging
import sys
import tkinter as tk

logger = logging.getLogger(__name__)

# ── Module-level state ─────────────────────────────────────────────────
DND_READY: bool = False
_DND_FILES: str | None = None   # Will hold the DND_FILES constant once loaded


def _try_import():
    """Attempt to import tkinterdnd2 and cache the DND_FILES constant."""
    global _DND_FILES
    try:
        from tkinterdnd2 import DND_FILES
        _DND_FILES = DND_FILES
        return True
    except ImportError:
        logger.warning(
            "tkinterdnd2 is not installed — Drag & Drop will not be available. "
            "Install it with:  pip install tkinterdnd2"
        )
        return False


def bootstrap_dnd(root: tk.Tk) -> bool:
    """
    Load the tkdnd Tcl extension into *root*'s interpreter and monkey-patch
    ``tk.Widget`` so that ``drop_target_register`` / ``dnd_bind`` are
    available on every widget.

    Returns ``True`` on success, ``False`` on graceful degradation.
    This function is **idempotent** — calling it twice is safe.
    """
    global DND_READY

    if DND_READY:
        return True

    if not _try_import():
        return False

    try:
        from tkinterdnd2 import TkinterDnD
        # Load the Tcl extension into the running interpreter
        TkinterDnD._require(root)

        # Monkey-patch tk.Widget so *all* widgets inherit DnD methods
        for method_name in ("drop_target_register", "dnd_bind", "drag_source_register"):
            if not hasattr(tk.Widget, method_name):
                setattr(
                    tk.Widget,
                    method_name,
                    getattr(TkinterDnD.DnDWrapper, method_name),
                )

        DND_READY = True
        logger.info("TkinterDnD2 loaded successfully — Drag & Drop is active.")
        return True

    except Exception as exc:
        # Typical failure: tkdnd Tcl binaries missing or incompatible arch
        DND_READY = False
        logger.error(
            "Failed to initialize TkinterDnD2 (%s: %s). "
            "The application will continue without Drag & Drop support. "
            "Try updating it: pip install --upgrade tkinterdnd2",
            type(exc).__name__,
            exc,
        )
        return False


def is_ready() -> bool:
    """Check if DnD has been successfully bootstrapped (reads live state)."""
    return DND_READY


def get_dnd_files_constant() -> str | None:
    """Return the ``DND_FILES`` constant, or ``None`` if DnD is not available."""
    return _DND_FILES


def enable_dnd_on_widget(
    widget: tk.Widget,
    on_drop,
    on_enter=None,
    on_leave=None,
    *,
    recursive: bool = True,
):
    """
    Register a widget (and optionally all its children) as a drop target.

    Parameters
    ----------
    widget : tk.Widget
        The widget to register.
    on_drop : callable
        Callback for ``<<Drop>>`` events.
    on_enter, on_leave : callable, optional
        Callbacks for enter/leave visual feedback.
    recursive : bool
        If True, also registers all child widgets and internal CTk canvases.
    """
    if not is_ready() or _DND_FILES is None:
        return

    def _register(w):
        try:
            w.drop_target_register(_DND_FILES)
            w.dnd_bind("<<Drop>>", on_drop)
            if on_enter:
                w.dnd_bind("<<DragEnter>>", on_enter)
            if on_leave:
                w.dnd_bind("<<DragLeave>>", on_leave)
        except Exception:
            pass

        # CustomTkinter wraps an internal _canvas for drawing
        canvas = getattr(w, "_canvas", None)
        if canvas is not None:
            try:
                canvas.drop_target_register(_DND_FILES)
                canvas.dnd_bind("<<Drop>>", on_drop)
                if on_enter:
                    canvas.dnd_bind("<<DragEnter>>", on_enter)
                if on_leave:
                    canvas.dnd_bind("<<DragLeave>>", on_leave)
            except Exception:
                pass

        if recursive:
            for child in w.winfo_children():
                _register(child)

    _register(widget)
