"""
test_dnd_utils.py — Unit tests for parse_drop_paths.
"""
import os
import sys
import pathlib
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from utils.dnd_utils import parse_drop_paths


class TestDnDUtils(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="dnd_test_")
        
        # Create some test files with resolved paths to avoid Windows short/long name mismatch
        self.png_path = str(pathlib.Path(self.tmp, "image.png").resolve())
        self.avif_path = str(pathlib.Path(self.tmp, "image.avif").resolve())
        self.txt_path = str(pathlib.Path(self.tmp, "doc.txt").resolve())
        self.tiff_path = str(pathlib.Path(self.tmp, "image.tiff").resolve())
        
        for path in (self.png_path, self.avif_path, self.txt_path, self.tiff_path):
            with open(path, "w") as f:
                f.write("dummy content")

    def tearDown(self):
        # Clean up temp files
        for name in os.listdir(self.tmp):
            try:
                os.remove(os.path.join(self.tmp, name))
            except OSError:
                pass
        try:
            os.rmdir(self.tmp)
        except OSError:
            pass

    def test_parse_valid_files(self):
        # Test dragging multiple files (Windows style brace format)
        raw_data = f"{{{self.png_path}}} {{{self.avif_path}}}"
        parsed = parse_drop_paths(raw_data)
        
        # Both png and avif should be accepted
        self.assertEqual(len(parsed), 2)
        norm_parsed = [os.path.normpath(p) for p in parsed]
        self.assertIn(self.png_path, norm_parsed)
        self.assertIn(self.avif_path, norm_parsed)

    def test_parse_rejects_unsupported_extensions(self):
        # Test txt and tiff are rejected (tiff was in old list, txt never was)
        raw_data = f"{{{self.txt_path}}} {{{self.tiff_path}}}"
        parsed = parse_drop_paths(raw_data)
        self.assertEqual(len(parsed), 0)

    def test_parse_rejects_nonexistent_files(self):
        nonexistent = os.path.normpath(os.path.join(self.tmp, "does_not_exist.png"))
        raw_data = f"{{{nonexistent}}}"
        parsed = parse_drop_paths(raw_data)
        self.assertEqual(len(parsed), 0)

    def test_parse_mac_linux_file_uris(self):
        # Test file:// URI parsing
        png_uri = pathlib.Path(self.png_path).as_uri()
        avif_uri = pathlib.Path(self.avif_path).as_uri()
        raw_data = f"{png_uri}\n{avif_uri}"
        parsed = parse_drop_paths(raw_data)
        
        self.assertEqual(len(parsed), 2)
        norm_parsed = [os.path.normpath(p) for p in parsed]
        self.assertIn(self.png_path, norm_parsed)
        self.assertIn(self.avif_path, norm_parsed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
