"""
disk_validator.py — check available disk space before batch conversion.
"""
import shutil
import os


class DiskValidator:
    # Safety margin: reserve at least this many extra bytes beyond estimated need
    SAFETY_MARGIN = 50 * 1024 * 1024  # 50 MB

    @staticmethod
    def get_free_bytes(directory: str) -> int:
        """Return free bytes on the volume containing *directory*."""
        try:
            total, used, free = shutil.disk_usage(directory)
            return free
        except OSError:
            return 0

    @staticmethod
    def estimate_needed(input_paths: list[str], quality: int) -> int:
        """
        Rough estimate of total output size.

        AVIF at quality≈85 ≈ 30% of original; at 65 ≈ 15%; at 35 ≈ 8%.
        We use a conservative 40% to never underestimate.
        """
        total_input = sum(
            os.path.getsize(p) for p in input_paths if os.path.isfile(p)
        )
        return int(total_input * 0.40) + DiskValidator.SAFETY_MARGIN

    @classmethod
    def has_enough_space(
        cls, input_paths: list[str], output_dir: str, quality: int = 65
    ) -> tuple[bool, int, int]:
        """
        Check if *output_dir* has enough free space.

        Returns (ok, needed_bytes, free_bytes).
        """
        needed = cls.estimate_needed(input_paths, quality)
        free = cls.get_free_bytes(output_dir)
        return free >= needed, needed, free
