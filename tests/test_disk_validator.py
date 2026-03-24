"""
test_disk_validator.py — Unit tests for DiskValidator.
"""
import os
import sys
import pathlib
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from core.disk_validator import DiskValidator


class TestDiskValidator(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="disk_val_test_")
        # Create three dummy 1 MB files
        self.input_files = []
        for i in range(3):
            p = os.path.join(self.tmp, f"img{i}.png")
            with open(p, "wb") as f:
                f.write(b"\x00" * 1_000_000)
            self.input_files.append(p)

    def test_get_free_bytes_positive(self):
        free = DiskValidator.get_free_bytes(self.tmp)
        self.assertGreater(free, 0)

    def test_estimate_needed_positive(self):
        needed = DiskValidator.estimate_needed(self.input_files, quality=60)
        self.assertGreater(needed, 0)

    def test_estimate_includes_safety_margin(self):
        needed = DiskValidator.estimate_needed(self.input_files, quality=60)
        self.assertGreaterEqual(needed, DiskValidator.SAFETY_MARGIN)

    def test_has_enough_space_returns_tuple(self):
        ok, needed, free = DiskValidator.has_enough_space(
            self.input_files, self.tmp
        )
        self.assertIsInstance(ok, bool)
        self.assertIsInstance(needed, int)
        self.assertIsInstance(free, int)

    def test_existing_temp_dir_likely_has_space(self):
        """A freshly created temp dir on a working machine should have space."""
        ok, needed, free = DiskValidator.has_enough_space(
            self.input_files, self.tmp
        )
        # 3 MB input → ~50 MB margin. Should be fine on any dev machine.
        self.assertTrue(ok, msg=f"Needed {needed}, Free {free}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
