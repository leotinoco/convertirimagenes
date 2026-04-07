"""
app.py — Entry point for ConvertirImagenes AVIF converter.

Usage:
    python app.py
    
    # Or double-click ConvertirImagenes.bat on Windows

PyInstaller packaging (see also ConvertirImagenes.spec):
    pyinstaller ConvertirImagenes.spec
"""
import sys
import os
import logging

# Configure root logger so DnD and converter messages are visible
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-28s  %(levelname)-7s  %(message)s",
)

# Load environment variables (optional .env file)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Make sure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
from ui.main_window import MainWindow


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    window = MainWindow()
    window.mainloop()


if __name__ == "__main__":
    main()
