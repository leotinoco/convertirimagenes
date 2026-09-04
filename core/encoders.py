"""
encoders.py — optional external AVIF encoders driven by ffmpeg.

The built-in Pillow/libaom path is always available and stays the default.
These engines are strictly opt-in alternatives for AVIF output:

  svtav1  SVT-AV1. Roughly 20% smaller files at the same visual quality
          (measured 36.9 KB vs 45.9 KB at SSIM ~0.952, 1200px wide), at the
          cost of a slower per-image encode.
  nvenc   NVIDIA hardware AV1 (NVENC). Measured *slower* than the CPU path for
          batches of stills — creating the CUDA/NVENC session costs far more
          than encoding a single small frame — and with no size advantage.
          Kept as an experimental option.

Both engines only apply to AVIF output, and only to images without an alpha
channel; every other case transparently falls back to the Pillow encoder.
They also do not carry EXIF/IPTC into the output (ffmpeg re-encodes from raw
pixels), which is usually desirable for images published to the web.
"""
from __future__ import annotations

import logging
import shutil
import subprocess
import sys
import threading

logger = logging.getLogger(__name__)

ENGINE_PILLOW = "pillow"
ENGINE_SVTAV1 = "svtav1"
ENGINE_NVENC = "nvenc"
ENGINES = (ENGINE_PILLOW, ENGINE_SVTAV1, ENGINE_NVENC)

# ffmpeg encoder name backing each engine
_FFMPEG_ENCODER = {
    ENGINE_SVTAV1: "libsvtav1",
    ENGINE_NVENC: "av1_nvenc",
}

# Hide the console window ffmpeg would otherwise flash for every image.
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0

_lock = threading.Lock()
_probe_done = False
_ffmpeg_path: str | None = None
_available: set[str] = set()


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------
def _probe() -> None:
    """Locate ffmpeg and record which of our engines it can run. Cached."""
    global _probe_done, _ffmpeg_path, _available
    with _lock:
        if _probe_done:
            return
        _probe_done = True

        _ffmpeg_path = shutil.which("ffmpeg")
        if not _ffmpeg_path:
            logger.info("ffmpeg not found; only the built-in encoder is available")
            return

        try:
            out = subprocess.run(
                [_ffmpeg_path, "-hide_banner", "-encoders"],
                capture_output=True, text=True, timeout=20,
                creationflags=_NO_WINDOW,
            ).stdout
        except Exception as exc:
            logger.warning("Could not query ffmpeg encoders: %s", exc)
            return

        for engine, enc_name in _FFMPEG_ENCODER.items():
            # Encoder lines look like: " V....D av1_nvenc  NVIDIA NVENC av1 ..."
            if any(line.split()[1:2] == [enc_name] for line in out.splitlines()
                   if len(line.split()) >= 2):
                _available.add(engine)

        logger.info("ffmpeg at %s; extra AVIF engines: %s",
                    _ffmpeg_path, ", ".join(sorted(_available)) or "none")


def ffmpeg_path() -> str | None:
    """Absolute path to ffmpeg, or None when it is not installed."""
    _probe()
    return _ffmpeg_path


def engine_available(engine: str) -> bool:
    """True if *engine* can be used on this machine."""
    if engine == ENGINE_PILLOW:
        return True
    _probe()
    return engine in _available


def available_engines() -> dict[str, bool]:
    """Availability of every engine, for building the UI."""
    return {e: engine_available(e) for e in ENGINES}


# ---------------------------------------------------------------------------
# Quality mapping
# ---------------------------------------------------------------------------
def quality_to_cq(quality: int, engine: str) -> int:
    """
    Map the app's 0-100 quality slider onto each encoder's CRF/CQ scale
    (where lower means better). The factors are anchored on measurements at
    1200px: quality 60 matches SVT-AV1 crf 30 and NVENC cq 35 in SSIM.
    """
    factor = 0.75 if engine == ENGINE_SVTAV1 else 0.875
    return max(1, min(63, round((100 - quality) * factor)))


# ---------------------------------------------------------------------------
# Encoding
# ---------------------------------------------------------------------------
def can_encode(engine: str, output_format: str, has_alpha: bool) -> bool:
    """True if *engine* should handle this job (else fall back to Pillow)."""
    if engine == ENGINE_PILLOW:
        return False
    if output_format.lower() != "avif" or has_alpha:
        return False
    return engine_available(engine)


def encode_avif(img, output_path: str, quality: int, engine: str) -> None:
    """
    Encode an RGB Pillow image to AVIF at *output_path* using ffmpeg.

    Raw pixels are piped to ffmpeg, so no intermediate file is written.
    Raises RuntimeError if the encode fails; callers fall back to Pillow.
    """
    exe = ffmpeg_path()
    if not exe:
        raise RuntimeError("ffmpeg is not available")

    enc_name = _FFMPEG_ENCODER.get(engine)
    if not enc_name:
        raise RuntimeError(f"unknown engine: {engine}")

    if img.mode != "RGB":
        img = img.convert("RGB")

    w, h = img.size
    cq = quality_to_cq(quality, engine)

    if engine == ENGINE_SVTAV1:
        codec_args = ["-c:v", "libsvtav1", "-crf", str(cq), "-preset", "6"]
    else:
        codec_args = ["-c:v", "av1_nvenc", "-cq", str(cq), "-preset", "p5"]

    cmd = [
        exe, "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-i", "-",
        *codec_args,
        "-pix_fmt", "yuv420p", "-frames:v", "1",
        # The destination is a temp file without a .avif name, so the container
        # has to be stated explicitly instead of inferred from the extension.
        "-f", "avif", output_path,
    ]

    proc = subprocess.run(
        cmd, input=img.tobytes(), capture_output=True,
        creationflags=_NO_WINDOW,
    )
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"{enc_name} failed: {err[:300]}")
