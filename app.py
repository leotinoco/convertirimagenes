"""
app.py — Entry point for ConvertirImagenes AVIF converter.

Usage:
    python app.py

Drag-and-drop strategy
-----------------------
tkinterdnd2 requires its Tcl extension to be loaded into the Tk interpreter.
Correct approach: call TkinterDnD._require(window) AFTER the CTk window is
created. This loads the DnD extension into the existing interpreter without
touching the class hierarchy (patching __bases__ breaks ctk internals).
"""
import sys
import os

# Make sure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk

# Check availability early (no side-effects yet)
try:
    import tkinterdnd2 as _tkdnd
    _DND_AVAILABLE = True
except ImportError:
    _DND_AVAILABLE = False

from ui.main_window import MainWindow


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    window = MainWindow()

    # Load DnD Tcl extension into the running interpreter AFTER CTk init
    if _DND_AVAILABLE:
        try:
            _tkdnd.TkinterDnD._require(window)
        except Exception:
            pass   # silently fall back to Browse button

    window.mainloop()


if __name__ == "__main__":
    main()
