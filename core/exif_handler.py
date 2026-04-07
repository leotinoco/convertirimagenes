"""
exif_handler.py — EXIF metadata extraction and handling.
"""
from __future__ import annotations

try:
    import piexif
    PIEXIF_AVAILABLE = True
except ImportError:
    PIEXIF_AVAILABLE = False


def load_exif(image_path: str, custom_meta: dict | None = None) -> bytes | None:
    """
    Load raw EXIF bytes from *image_path* and optionally apply custom_meta.
    custom_meta is a dict with keys: 'title', 'author', 'copyright', 'description'.
    Returns None if piexif is unavailable.
    """
    if not PIEXIF_AVAILABLE:
        return None
    try:
        try:
            exif_dict = piexif.load(image_path)
        except Exception:
            # Create empty if invalid or missing
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}}

        if custom_meta:
            # Standard TIFF/EXIF tags in 0th and Exif IFD
            if "description" in custom_meta:
                exif_dict["0th"][piexif.ImageIFD.ImageDescription] = custom_meta["description"].encode("utf-8")
            if "title" in custom_meta:
                exif_dict["0th"][piexif.ImageIFD.DocumentName] = custom_meta["title"].encode("utf-8")
            if "author" in custom_meta:
                exif_dict["0th"][piexif.ImageIFD.Artist] = custom_meta["author"].encode("utf-8")
            if "copyright" in custom_meta:
                exif_dict["0th"][piexif.ImageIFD.Copyright] = custom_meta["copyright"].encode("utf-8")
            if "date_created" in custom_meta:
                exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = custom_meta["date_created"].encode("utf-8")
            if "date_modified" in custom_meta:
                exif_dict["0th"][piexif.ImageIFD.DateTime] = custom_meta["date_modified"].encode("utf-8")

        return piexif.dump(exif_dict)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None


def strip_exif(exif_bytes: bytes | None) -> None:
    """Return None — used when the user requests EXIF removal."""
    return None
