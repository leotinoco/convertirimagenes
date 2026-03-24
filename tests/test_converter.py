"""
test_converter.py — Unit tests for the core AVIF conversion engine.

These tests create small synthetic PNG images in a temp dir, convert them
to AVIF at different quality levels, and verify:
  1. The output file exists and has a .avif extension.
  2. The file can be re-opened by Pillow (valid AVIF).
  3. High-quality output is larger than low-quality output.
  4. The original filename stem is preserved.
  5. RGBA images convert without errors.
"""
import os
import pathlib
import sys
import tempfile
import unittest

# Ensure the project root is importable
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

try:
    import pillow_avif  # noqa: F401
    AVIF_AVAILABLE = True
except ImportError:
    AVIF_AVAILABLE = False

from PIL import Image


@unittest.skipUnless(AVIF_AVAILABLE, "pillow-avif-plugin not installed")
class TestConverter(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Create a temp directory and a pair of synthetic test images."""
        from core.converter import Converter
        cls.conv = Converter()
        cls.tmp = tempfile.mkdtemp(prefix="avif_test_")

        # 800×600 RGB gradient
        cls.png_path = os.path.join(cls.tmp, "test_rgb.png")
        img_rgb = Image.new("RGB", (800, 600))
        pixels = [(x % 256, y % 256, (x + y) % 256) for y in range(600) for x in range(800)]
        img_rgb.putdata(pixels)
        img_rgb.save(cls.png_path, format="PNG")

        # 400×300 RGBA (transparency check)
        cls.rgba_path = os.path.join(cls.tmp, "test_rgba.png")
        img_rgba = Image.new("RGBA", (400, 300), (100, 150, 200, 128))
        img_rgba.save(cls.rgba_path, format="PNG")

    # ------------------------------------------------------------------
    def _convert(self, preset: str, path: str | None = None):
        src = path or self.png_path
        out_dir = os.path.join(self.tmp, preset)
        os.makedirs(out_dir, exist_ok=True)
        return self.conv.convert_one(src, out_dir, quality_preset=preset)

    # ------------------------------------------------------------------
    def test_output_extension_is_avif(self):
        result = self._convert("medium")
        self.assertTrue(result.output_path.endswith(".avif"), result.output_path)

    def test_filename_stem_preserved(self):
        result = self._convert("medium")
        src_stem  = pathlib.Path(self.png_path).stem
        out_stem  = pathlib.Path(result.output_path).stem
        self.assertEqual(src_stem, out_stem)

    def test_success_flag(self):
        result = self._convert("high")
        self.assertTrue(result.success, msg=result.error)

    def test_output_file_exists(self):
        result = self._convert("high")
        self.assertTrue(os.path.isfile(result.output_path))

    def test_avif_is_readable_by_pillow(self):
        result = self._convert("medium")
        with Image.open(result.output_path) as img:
            self.assertIsNotNone(img)

    def test_high_quality_larger_than_low_quality(self):
        r_high = self._convert("high")
        r_low  = self._convert("low")
        self.assertGreater(
            r_high.converted_size,
            r_low.converted_size,
            msg=(
                f"Expected high ({r_high.converted_size}B) > "
                f"low ({r_low.converted_size}B)"
            ),
        )

    def test_savings_pct_positive(self):
        result = self._convert("medium")
        self.assertGreaterEqual(result.savings_pct, 0.0)

    def test_rgba_conversion(self):
        result = self._convert("medium", path=self.rgba_path)
        self.assertTrue(result.success, msg=result.error)
        self.assertTrue(os.path.isfile(result.output_path))

    def test_all_three_presets_produce_files(self):
        for preset in ("high", "medium", "low"):
            with self.subTest(preset=preset):
                result = self._convert(preset)
                self.assertTrue(result.success, msg=f"{preset}: {result.error}")
                self.assertGreater(result.converted_size, 0)


class TestFileUtils(unittest.TestCase):
    def test_format_bytes_bytes(self):
        from utils.file_utils import format_bytes
        self.assertEqual(format_bytes(512), "512 B")

    def test_format_bytes_kb(self):
        from utils.file_utils import format_bytes
        self.assertIn("KB", format_bytes(2048))

    def test_format_bytes_mb(self):
        from utils.file_utils import format_bytes
        self.assertIn("MB", format_bytes(1_500_000))

    def test_is_valid_image(self):
        from utils.file_utils import is_valid_image
        self.assertTrue(is_valid_image("photo.JPG"))
        self.assertTrue(is_valid_image("image.png"))
        self.assertFalse(is_valid_image("document.pdf"))

    def test_build_output_path_same_dir(self):
        import pathlib
        from utils.file_utils import build_output_path
        src = str(pathlib.Path.home() / "photo.jpg")
        out = build_output_path(src)
        out_path = pathlib.Path(out)
        self.assertEqual(out_path.suffix, ".avif")
        self.assertEqual(out_path.stem, "photo")
        self.assertEqual(out_path.parent, pathlib.Path(src).parent)

    def test_build_output_path_custom_dir(self):
        import pathlib, tempfile
        from utils.file_utils import build_output_path
        with tempfile.TemporaryDirectory() as d:
            out = build_output_path(str(pathlib.Path(d) / "photo.jpg"), d)
            out_path = pathlib.Path(out)
            self.assertEqual(out_path.suffix, ".avif")
            self.assertEqual(out_path.stem, "photo")
            self.assertEqual(str(out_path.parent), d)


if __name__ == "__main__":
    unittest.main(verbosity=2)
