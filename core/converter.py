"""
converter.py — core image conversion engine (AVIF / WebP / JPG / PNG).

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

# Register avif plugin as early as possible.
# Pillow >= 11.3 ships native AVIF support; fall back to pillow-avif-plugin.
try:
    import pillow_avif  # noqa: F401  registers itself with Pillow
    AVIF_AVAILABLE = True
except ImportError:
    AVIF_AVAILABLE = False

from PIL import Image, ImageOps, features

if not AVIF_AVAILABLE:
    # Native AVIF support (Pillow 11.3+ compiled with libavif)
    try:
        AVIF_AVAILABLE = features.check("avif")
    except Exception:
        AVIF_AVAILABLE = False

# ---------------------------------------------------------------------------
# Safety: guard against decompression bombs (maliciously large images that
# expand to gigabytes of RAM). Pillow's default (~178 MP) already raises an
# error at 2x the limit; we keep the default but make the failure friendly
# in convert_one instead of crashing the worker thread.
# ---------------------------------------------------------------------------
MAX_PIXELS = Image.MAX_IMAGE_PIXELS  # keep Pillow's safe default

from core import encoders
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

# Output formats supported by the engine
OUTPUT_FORMATS = ("avif", "webp", "jpg", "png")


@dataclass
class ConversionResult:
    source_path: str
    output_path: str
    original_size: int
    converted_size: int
    success: bool
    error: str = ""
    subsampling: str = ""
    engine: str = "pillow"      # encoder that actually produced the file
    savings_pct: float = field(init=False)

    def __post_init__(self):
        if self.original_size > 0:
            self.savings_pct = (
                100.0 * (self.original_size - self.converted_size) / self.original_size
            )
        else:
            self.savings_pct = 0.0


class Converter:
    """Converts PNG/JPG/WebP/AVIF images to AVIF, WebP, JPG or PNG."""

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
        output_format: str = "avif",
        suffix: str = "",
        engine: str = "pillow",
    ) -> ConversionResult:
        """
        Convert a single image.

        Parameters
        ----------
        input_path : str
            Absolute path to the source image.
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
            AVIF encoding effort (0-9). 0-3 is slowest/best, 8-9 is fastest.
        subsampling : str
            Chroma subsampling ("4:2:0" or "4:4:4").
        resize_cfg : dict | None
            {"enabled": bool, "width": int, "height": int}.
        output_format : str
            "avif", "webp", "jpg" or "png".
        suffix : str
            Optional filename suffix, e.g. "-opt" → photo-opt.avif.
        engine : str
            AVIF encoder: "pillow" (built-in, default), "svtav1" or "nvenc".
            The external engines need ffmpeg and only handle AVIF output of
            images without alpha; anything else falls back to Pillow.
        """
        output_path = build_output_path(input_path, output_dir, output_format, suffix)
        original_size = get_file_size(input_path)
        used_engine = "pillow"

        try:
            with Image.open(input_path) as img:
                # 0. Apply EXIF orientation to the pixels so the output never
                #    depends on viewers honouring the Orientation tag. The tag
                #    itself is reset to 1 in load_exif().
                img = ImageOps.exif_transpose(img)

                # 1. Handle resizing if enabled (LANCZOS keeps sharpness).
                if resize_cfg and resize_cfg.get("enabled"):
                    w, h = img.size
                    target_w = resize_cfg.get("width")
                    target_h = resize_cfg.get("height")

                    if target_w and target_w > 0:
                        # Proportional if only width or both provided
                        if not target_h or target_h <= 0:
                            target_h = max(1, round(h * (target_w / w)))
                        img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                    elif target_h and target_h > 0:
                        # Proportional if only height provided
                        target_w = max(1, round(w * (target_h / h)))
                        img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)

                # 2. Normalise mode: AVIF/WebP support RGB and RGBA; JPEG only RGB.
                #    Also handle palette images ("P") that may have transparency.
                has_alpha = (
                    img.mode in ("RGBA", "LA", "PA")
                    or (img.mode == "P" and "transparency" in img.info)
                )

                fmt = output_format.lower()
                if fmt in ("jpg", "jpeg"):
                    # JPEG does not support alpha, paste onto white background
                    if has_alpha:
                        bg = Image.new("RGB", img.size, (255, 255, 255))
                        if img.mode != "RGBA":
                            img = img.convert("RGBA")
                        bg.paste(img, mask=img.split()[3])
                        img = bg
                    elif img.mode != "RGB":
                        img = img.convert("RGB")

                    effective_subsampling = "4:2:0"  # default standard JPEG subsampling
                    save_kwargs: dict = {
                        "format": "JPEG",
                        "quality": quality,
                        "optimize": True,      # extra Huffman-table optimization pass
                        "progressive": True,   # progressive render = better perceived load
                    }
                elif fmt == "png":
                    if img.mode not in ("RGB", "RGBA", "L", "LA"):
                        img = img.convert("RGBA" if has_alpha else "RGB")

                    effective_subsampling = ""
                    save_kwargs = {
                        "format": "PNG",
                        "optimize": True,
                    }
                elif fmt == "webp":
                    if img.mode not in ("RGB", "RGBA"):
                        img = img.convert("RGBA" if has_alpha else "RGB")

                    effective_subsampling = ""
                    save_kwargs = {
                        "format": "WEBP",
                        "quality": quality,
                        "method": 6,           # slowest/best compression method
                    }
                else:  # avif
                    if img.mode not in ("RGB", "RGBA"):
                        img = img.convert("RGBA" if has_alpha else "RGB")
                        has_alpha = img.mode == "RGBA"  # re-check after conversion

                    # Force 4:4:4 chroma subsampling for RGBA images.
                    # 4:2:0 does not carry alpha information correctly in some
                    # libavif builds and will silently drop the transparency.
                    effective_subsampling = "4:4:4" if has_alpha else subsampling

                    save_kwargs = {
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
                tmp_suffix = f".{fmt}.tmp"
                fd, tmp_path = tempfile.mkstemp(suffix=tmp_suffix, dir=dest_dir)
                try:
                    os.close(fd)
                    if encoders.can_encode(engine, fmt, has_alpha):
                        try:
                            encoders.encode_avif(img, tmp_path, quality, engine)
                            used_engine = engine
                        except Exception as exc:
                            # Never fail a conversion because an optional
                            # encoder misbehaved — fall back to Pillow.
                            import logging
                            logging.getLogger(__name__).warning(
                                "Engine '%s' failed on %s, using pillow: %s",
                                engine, os.path.basename(input_path), exc,
                            )
                            img.save(tmp_path, **save_kwargs)
                    else:
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
                engine=used_engine,
            )

        except Image.DecompressionBombError:
            return ConversionResult(
                source_path=input_path,
                output_path=output_path,
                original_size=original_size,
                converted_size=0,
                success=False,
                error="Imagen demasiado grande (posible decompression bomb)",
            )
        except Exception as exc:
            import logging
            from utils.logging_utils import log_exception
            log_exception(logging.getLogger(__name__), "convert_one failed", exc)
            return ConversionResult(
                source_path=input_path,
                output_path=output_path,
                original_size=original_size,
                converted_size=0,
                success=False,
                error=str(exc),
            )

    # ------------------------------------------------------------------
    # Batch (parallel using ThreadPoolExecutor — Pillow releases the GIL
    # during encode, so threads scale well and share memory safely)
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
        output_format: str = "avif",
        suffix: str = "",
        variants: list[dict] | None = None,
        engine: str = "pillow",
    ) -> list[ConversionResult]:
        """
        Convert multiple images in parallel.

        variants : list[dict] | None
            Optional list of output variants, each
            {"resize_cfg": dict | None, "suffix": str}. Every input file is
            converted once per variant (e.g. a 1200px desktop version and an
            800px mobile version in a single batch). When None, each file is
            converted once using *resize_cfg* / *suffix*.
        engine : str
            AVIF encoder for every job: "pillow", "svtav1" or "nvenc".
        """
        import concurrent.futures
        import logging

        logger = logging.getLogger(__name__)

        if variants:
            jobs = [
                (path, v.get("resize_cfg", resize_cfg), v.get("suffix", suffix))
                for path in input_paths
                for v in variants
            ]
        else:
            jobs = [(path, resize_cfg, suffix) for path in input_paths]

        results: list[ConversionResult] = []
        total = len(jobs)

        workers = max_workers if max_workers and max_workers > 0 else (os.cpu_count() or 4)
        workers = max(1, min(workers, total)) if total else 1
        logger.info(
            "Starting batch conversion: %d files, %d outputs, %d workers",
            len(input_paths), total, workers,
        )

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            # Prepare tasks
            futures = {}
            for path, job_resize_cfg, job_suffix in jobs:
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
                    job_resize_cfg,
                    output_format,
                    job_suffix,
                    engine,
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
                    logger.info(
                        "Converted %d/%d: %s → %s",
                        idx, total, os.path.basename(result.source_path),
                        "OK" if result.success else result.error,
                    )
                    if progress_cb:
                        progress_cb(idx, total, result)
                except Exception as exc:
                    path = futures[future]
                    logger.error("Conversion failed for %s: %s", os.path.basename(path), exc)
                    res = ConversionResult(path, "", 0, 0, False, error=str(exc))
                    results.append(res)
                    if progress_cb:
                        progress_cb(idx, total, res)

        return results
