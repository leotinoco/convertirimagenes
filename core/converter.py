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
    subsampling: str = ""
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
        quality: int = 65,
        keep_exif: bool = True,
        keep_iptc: bool = False,
        custom_meta: dict | None = None,
        speed: int = 5,
        subsampling: str = "4:2:0",
        resize_cfg: dict | None = None,
    ) -> ConversionResult:
        """
        Convert a single image to AVIF.

        Parameters
        ----------
        input_path : str
            Absolute path to the source PNG/JPG.
        output_dir : str | None
            Destination directory. None → same directory as source.
        quality : int
            Compression quality (0-100).
        keep_exif : bool
            If True, copy EXIF from source to output (if available).
        keep_iptc : bool
            If True, copy IPTC from source to output (if available).
        custom_meta: dict | None
            Custom metadata to inject into EXIF fields.
        speed : int
            Encoding effort (0-9). 0-3 is slowest/best, 8-9 is fastest.
        subsampling : str
            Chroma subsampling ("4:2:0" or "4:4:4").
        resize_cfg : dict | None
            {"enabled": bool, "width": int, "height": int}.
        """
        output_path = build_output_path(input_path, output_dir)
        original_size = get_file_size(input_path)

        try:
            with Image.open(input_path) as img:
                # 1. Handle resizing if enabled
                if resize_cfg and resize_cfg.get("enabled"):
                    w, h = img.size
                    target_w = resize_cfg.get("width")
                    target_h = resize_cfg.get("height")

                    if target_w and target_w > 0:
                        # Proportional if only width or both provided
                        if not target_h or target_h <= 0:
                            target_h = int(h * (target_w / w))
                        
                        img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                    elif target_h and target_h > 0:
                        # Proportional if only height provided
                        target_w = int(w * (target_h / h))
                        img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)

                # 2. Normalise mode: AVIF supports RGB and RGBA
                #    Also handle palette images ("P") that may have transparency.
                has_alpha = (
                    img.mode in ("RGBA", "LA", "PA")
                    or (img.mode == "P" and "transparency" in img.info)
                )
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGBA" if has_alpha else "RGB")
                    has_alpha = img.mode == "RGBA"  # re-check after conversion

                # Force 4:4:4 chroma subsampling for RGBA images.
                # 4:2:0 does not carry alpha information correctly in some
                # libavif builds and will silently drop the transparency.
                effective_subsampling = "4:4:4" if has_alpha else subsampling

                save_kwargs: dict = {
                    "format": "AVIF",
                    "quality": quality,
                    "speed": speed,
                    "subsampling": effective_subsampling,
                }

                if keep_iptc:
                    iptc_bytes = img.info.get("iptc")
                    if iptc_bytes:
                        save_kwargs["iptc"] = iptc_bytes

                if keep_exif or custom_meta:
                    exif_bytes = load_exif(input_path, custom_meta)
                    if exif_bytes:
                        save_kwargs["exif"] = exif_bytes

                # Ensure destination directory exists
                pathlib.Path(output_path).parent.mkdir(parents=True, exist_ok=True)

                # Write to a temp file first, then atomically replace.
                dest_dir = str(pathlib.Path(output_path).parent)
                fd, tmp_path = tempfile.mkstemp(suffix=".avif.tmp", dir=dest_dir)
                try:
                    os.close(fd)
                    img.save(tmp_path, **save_kwargs)
                    shutil.move(tmp_path, output_path)
                except Exception:
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
                subsampling=effective_subsampling,
            )

        except Exception as exc:
            import traceback
            traceback.print_exc()
            return ConversionResult(
                source_path=input_path,
                output_path=output_path,
                original_size=original_size,
                converted_size=0,
                success=False,
                error=str(exc),
            )

    # ------------------------------------------------------------------
    # Batch (parallel using ProcessPoolExecutor)
    # ------------------------------------------------------------------
    def convert_batch(
        self,
        input_paths: list[str],
        output_dir: str | None = None,
        quality: int = 65,
        keep_exif: bool = True,
        keep_iptc: bool = False,
        custom_meta: dict | None = None,
        speed: int = 5,
        subsampling: str = "4:2:0",
        resize_cfg: dict | None = None,
        max_workers: int | None = None,
        progress_cb: Callable[[int, int, ConversionResult], None] | None = None,
        stop_event: threading.Event | None = None,
    ) -> list[ConversionResult]:
        """
        Convert multiple images in parallel.
        """
        import concurrent.futures
        import os
        import logging

        logger = logging.getLogger(__name__)

        results: list[ConversionResult] = []
        total = len(input_paths)
        
        workers = max_workers if max_workers is not None else (os.cpu_count() or 4)
        logger.info("Starting batch conversion: %d files, %d workers", total, workers)

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            # Prepare tasks
            futures = {}
            for path in input_paths:
                if stop_event and stop_event.is_set():
                    break
                
                future = executor.submit(
                    self.convert_one,
                    path,
                    output_dir,
                    quality,
                    keep_exif,
                    keep_iptc,
                    custom_meta,
                    speed,
                    subsampling,
                    resize_cfg
                )
                futures[future] = path

            # Collect results as they finish
            for idx, future in enumerate(concurrent.futures.as_completed(futures), start=1):
                if stop_event and stop_event.is_set():
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
                
                try:
                    result = future.result()
                    results.append(result)
                    logger.info("Converted %d/%d: %s → %s", idx, total, result.source_path, "OK" if result.success else result.error)
                    if progress_cb:
                        progress_cb(idx, total, result)
                except Exception as exc:
                    path = futures[future]
                    logger.error("Conversion failed for %s: %s", path, exc)
                    res = ConversionResult(path, "", 0, 0, False, error=str(exc))
                    results.append(res)
                    if progress_cb:
                        progress_cb(idx, total, res)

        return results


def _run_convert_one_wrapper(converter, *args, **kwargs):
    """
    Helper function to call convert_one inside a separate process.
    ProcessPoolExecutor requires the target to be a top-level function.
    """
    return converter.convert_one(*args, **kwargs)
