"""
file_utils.py — helpers for path and size formatting
"""
import os
import pathlib

VALID_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def format_bytes(size_bytes: int) -> str:
    """Return a human-readable file size string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024 ** 2:.2f} MB"
    else:
        return f"{size_bytes / 1024 ** 3:.2f} GB"


def is_valid_image(path: str) -> bool:
    """Return True if the file has a supported input extension."""
    ext = pathlib.Path(path).suffix.lower()
    return ext in VALID_EXTENSIONS


def build_output_path(input_path: str, output_dir: str | None = None) -> str:
    """
    Build the output .avif path.

    If *output_dir* is None or empty, the converted file is saved next to the
    original. Otherwise it is saved to *output_dir*.
    """
    src = pathlib.Path(input_path)
    stem = src.stem
    if output_dir:
        dest_dir = pathlib.Path(output_dir)
    else:
        dest_dir = src.parent
    return str(dest_dir / f"{stem}.avif")


def get_file_size(path: str) -> int:
    """Return file size in bytes; 0 if file does not exist."""
    try:
        return os.path.getsize(path)
    except OSError:
        return 0
