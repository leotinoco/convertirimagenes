"""
dnd_utils.py — Cross-platform drag-and-drop path normalization.

Handles the notorious quirks of tkinterdnd2's event.data across
Windows, macOS and Linux:

  - Windows: paths with spaces are wrapped in Tcl-style braces  {C:\Path with Spaces\file.png}
  - macOS:   file:// URIs separated by newlines
  - Linux:   file:// URIs separated by newlines (also \r\n in some DEs)
  - All:     multiple files separated by spaces when no braces are present

The parser intentionally avoids `shlex.split()` on Windows because
backslashes in paths get mangled by POSIX-style shell parsing.
"""
from __future__ import annotations

import logging
import os
import pathlib
import re
import sys
import urllib.parse

logger = logging.getLogger(__name__)

# Supported input image extensions (lowercase, with leading dot)
_VALID_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp", ".tiff", ".tif", ".bmp"})


def parse_drop_paths(raw: str) -> list[str]:
    """
    Parse the raw ``event.data`` string from a tkinterdnd2 ``<<Drop>>``
    event into a clean list of absolute file-system paths.

    Returns only paths that:
      1. Actually exist on disk
      2. Are regular files (not directories / symlinks to dirs)
      3. Have a supported image extension

    Platform handling
    -----------------
    * **Windows** – Tcl wraps paths containing spaces in ``{braces}``.
      Multiple paths are separated by spaces *outside* of braces.
    * **macOS / Linux** – Paths arrive as ``file://``-encoded URIs
      separated by ``\\n`` or ``\\r\\n``.
    """
    if not raw or not raw.strip():
        return []

    tokens: list[str] = []

    # ── macOS / Linux: file:// URI list separated by newlines ──────────
    if raw.strip().startswith("file://"):
        for line in raw.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            # Decode percent-encoded characters  e.g.  %20 → space
            decoded = urllib.parse.unquote(urllib.parse.urlparse(line).path)
            # On Windows, urlparse gives /C:/path – strip leading slash
            if sys.platform == "win32" and decoded.startswith("/"):
                decoded = decoded[1:]
            tokens.append(decoded)

    # ── Windows Tcl-style: {path with spaces} or naked paths ──────────
    else:
        # Regex: match either  {…anything inside braces…}  or a run of
        # non-whitespace characters (a naked path without spaces).
        for match in re.finditer(r'\{([^}]+)\}|(\S+)', raw):
            path = match.group(1) or match.group(2)
            tokens.append(path)

    # ── Validate & normalize ──────────────────────────────────────────
    clean: list[str] = []
    for raw_path in tokens:
        p = pathlib.Path(raw_path.strip())
        try:
            resolved = p.resolve(strict=False)
        except (OSError, ValueError):
            logger.warning("DnD: path resolve failed: %s", raw_path)
            continue

        if not resolved.exists():
            logger.debug("DnD: file does not exist: %s", resolved)
            continue

        if not resolved.is_file():
            logger.debug("DnD: not a regular file: %s", resolved)
            continue

        if resolved.suffix.lower() not in _VALID_EXTENSIONS:
            logger.info(
                "DnD: rejected unsupported extension '%s' for file: %s",
                resolved.suffix, resolved.name,
            )
            continue

        clean.append(str(resolved))

    # Remove any duplicate paths that may sneak in
    seen: set[str] = set()
    deduped: list[str] = []
    for fp in clean:
        key = os.path.normcase(fp)
        if key not in seen:
            seen.add(key)
            deduped.append(fp)

    return deduped
