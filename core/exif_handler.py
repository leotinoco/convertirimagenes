"""
exif_handler.py — EXIF metadata extraction and handling.
"""
from __future__ import annotations

try:
    import piexif
    PIEXIF_AVAILABLE = True
except ImportError:
    PIEXIF_AVAILABLE = False


def load_exif(image_path: str) -> bytes | None:
    """
    Load raw EXIF bytes from *image_path*.

    Returns None if piexif is unavailable or the image has no EXIF data.
    """
    if not PIEXIF_AVAILABLE:
        return None
    try:
        exif_dict = piexif.load(image_path)
        return piexif.dump(exif_dict)
    except Exception:
        return None


def strip_exif(exif_bytes: bytes | None) -> None:
    """Return None — used when the user requests EXIF removal."""
    return None
