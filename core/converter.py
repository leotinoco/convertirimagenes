"""
converter.py — core AVIF conversion engine.

Quality / speed presets
------------------------
Preset      quality   speed   Description
------      -------   -----   -----------
high        80        6       Best visual fidelity, larger files
medium      60        4       Balanced (default)
low         30        2       Max compression, smallest files
"""
from __future__ import annotations

import os
import pathlib
import shutil
import tempfile
import threading
from dataclasses import dataclass, field
from typing import Callable

# Register avif plugin as early as possible
try:
    import pillow_avif  # noqa: F401  registers itself with Pillow
    AVIF_AVAILABLE = True
except ImportError:
    AVIF_AVAILABLE = False

from PIL import Image

from core.exif_handler import load_exif
from utils.file_utils import build_output_path, get_file_size

# ---------------------------------------------------------------------------
# Quality presets
# ---------------------------------------------------------------------------
PRESETS: dict[str, dict] = {
    "high":   {"quality": 80, "speed": 6,  "label": "Alta calidad"},
    "medium": {"quality": 60, "speed": 4,  "label": "Calidad media"},
    "low":    {"quality": 30, "speed": 2,  "label": "Baja calidad"},
}

SPEED_LABELS = {
    "fast":   4,
    "good":   6,
    "best":   8,
}


@dataclass
class ConversionResult:
    source_path: str
    output_path: str
    original_size: int
    converted_size: int
    success: bool
    error: str = ""
    savings_pct: float = field(init=False)

    def __post_init__(self):
        if self.original_size > 0:
            self.savings_pct = (
                100.0 * (self.original_size - self.converted_size) / self.original_size
            )
        else:
            self.savings_pct = 0.0


class Converter:
    """Converts PNG/JPG images to AVIF format."""

    def __init__(self):
        if not AVIF_AVAILABLE:
            raise RuntimeError(
                "pillow-avif-plugin no está instalado.\n"
                "Ejecuta: pip install pillow-avif-plugin"
            )

    # ------------------------------------------------------------------
    # Single file
    # ------------------------------------------------------------------
    def convert_one(
        self,
        input_path: str,
        output_dir: str | None = None,
        quality_preset: str = "medium",
        keep_exif: bool = True,
        encoding_speed: str = "good",
    ) -> ConversionResult:
        """
        Convert a single image to AVIF.

        Parameters
        ----------
        input_path : str
            Absolute path to the source PNG/JPG.
        output_dir : str | None
            Destination directory. None → same directory as source.
        quality_preset : str
            One of "high", "medium", "low".
        keep_exif : bool
            If True, copy EXIF from source to output (if available).
        encoding_speed : str
            One of "fast", "good", "best". Overrides the preset speed.
        """
        preset = PRESETS.get(quality_preset, PRESETS["medium"])
        quality = preset["quality"]
        speed = SPEED_LABELS.get(encoding_speed, preset["speed"])

        output_path = build_output_path(input_path, output_dir)
        original_size = get_file_size(input_path)

        try:
            with Image.open(input_path) as img:
                # Normalise mode: AVIF supports RGB and RGBA
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGBA" if "A" in img.mode else "RGB")

                save_kwargs: dict = {
                    "format": "AVIF",
                    "quality": quality,
                    "speed": speed,
                }

                if keep_exif:
                    exif_bytes = load_exif(input_path)
                    if exif_bytes:
                        save_kwargs["exif"] = exif_bytes

                # Ensure destination directory exists
                pathlib.Path(output_path).parent.mkdir(parents=True, exist_ok=True)

                # Write to a temp file first, then atomically replace.
                # This avoids Windows file-lock issues when overwriting an
                # existing .avif (e.g. on a repeated conversion of the same batch).
                dest_dir = str(pathlib.Path(output_path).parent)
                fd, tmp_path = tempfile.mkstemp(suffix=".avif.tmp", dir=dest_dir)
                try:
                    os.close(fd)  # Pillow opens by path, not fd
                    img.save(tmp_path, **save_kwargs)
                    # Replace destination atomically (works even if dest exists)
                    shutil.move(tmp_path, output_path)
                except Exception:
                    # Clean up temp file on failure
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
                    raise

            converted_size = get_file_size(output_path)
            return ConversionResult(
                source_path=input_path,
                output_path=output_path,
                original_size=original_size,
                converted_size=converted_size,
                success=True,
            )

        except Exception as exc:
            return ConversionResult(
                source_path=input_path,
                output_path=output_path,
                original_size=original_size,
                converted_size=0,
                success=False,
                error=str(exc),
            )

    # ------------------------------------------------------------------
    # Batch (threaded, calls progress_cb after each file)
    # ------------------------------------------------------------------
    def convert_batch(
        self,
        input_paths: list[str],
        output_dir: str | None = None,
        quality_preset: str = "medium",
        keep_exif: bool = True,
        encoding_speed: str = "good",
        progress_cb: Callable[[int, int, ConversionResult], None] | None = None,
        stop_event: threading.Event | None = None,
    ) -> list[ConversionResult]:
        """
        Convert multiple images, optionally reporting progress.

        *progress_cb* receives (current_index, total, result) after each file.
        *stop_event* can be set externally to cancel mid-batch.
        """
        results: list[ConversionResult] = []
        total = len(input_paths)
        for idx, path in enumerate(input_paths, start=1):
            if stop_event and stop_event.is_set():
                print(f"[converter] stop_event set, aborting at [{idx}/{total}]")
                break
            print(f"[converter] starting [{idx}/{total}]: {path}")
            result = self.convert_one(
                path, output_dir, quality_preset, keep_exif, encoding_speed
            )
            print(f"[converter] finished [{idx}/{total}]: success={result.success} error={result.error!r}")
            results.append(result)
            if progress_cb:
                progress_cb(idx, total, result)
        return results
