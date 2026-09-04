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

        # 800×600 RGB pseudo-photographic image (gradient + deterministic
        # noise). A pure gradient compresses to ~2 KB as PNG — smaller than
        # any AVIF — which made savings assertions encoder-dependent.
        import random
        rnd = random.Random(42)
        cls.png_path = os.path.join(cls.tmp, "test_rgb.png")
        img_rgb = Image.new("RGB", (800, 600))
        pixels = [
            (
                min(255, x % 256 + rnd.randint(0, 40)),
                min(255, y % 256 + rnd.randint(0, 40)),
                min(255, (x + y) % 256 + rnd.randint(0, 40)),
            )
            for y in range(600) for x in range(800)
        ]
        img_rgb.putdata(pixels)
        img_rgb.save(cls.png_path, format="PNG")

        # 400×300 RGBA (transparency check)
        cls.rgba_path = os.path.join(cls.tmp, "test_rgba.png")
        img_rgba = Image.new("RGBA", (400, 300), (100, 150, 200, 128))
        img_rgba.save(cls.rgba_path, format="PNG")

    # ------------------------------------------------------------------
    def _convert(self, preset: str, path: str | None = None, output_format: str = "avif"):
        src = path or self.png_path
        out_dir = os.path.join(self.tmp, preset)
        os.makedirs(out_dir, exist_ok=True)
        from core.converter import PRESETS
        cfg = PRESETS[preset]
        return self.conv.convert_one(
            src,
            out_dir,
            quality=cfg["quality"],
            speed=cfg["speed"],
            output_format=output_format,
        )

    # ------------------------------------------------------------------
    def test_output_extension_is_avif(self):
        result = self._convert("medium")
        self.assertTrue(result.output_path.endswith(".avif"), result.output_path)

    def test_output_extension_is_jpg(self):
        result = self._convert("medium", output_format="jpg")
        self.assertTrue(result.output_path.endswith(".jpg"), result.output_path)

    def test_rgba_to_jpg_white_bg(self):
        result = self._convert("medium", path=self.rgba_path, output_format="jpg")
        self.assertTrue(result.success, msg=result.error)
        self.assertTrue(os.path.isfile(result.output_path))
        with Image.open(result.output_path) as img:
            self.assertEqual(img.mode, "RGB")

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

    def test_output_extension_is_webp(self):
        result = self._convert("medium", output_format="webp")
        self.assertTrue(result.success, msg=result.error)
        self.assertTrue(result.output_path.endswith(".webp"), result.output_path)
        with Image.open(result.output_path) as img:
            self.assertEqual(img.format, "WEBP")

    def test_rgba_to_webp_keeps_alpha(self):
        result = self._convert("medium", path=self.rgba_path, output_format="webp")
        self.assertTrue(result.success, msg=result.error)
        with Image.open(result.output_path) as img:
            self.assertEqual(img.mode, "RGBA")

    def test_all_three_presets_produce_files(self):
        for preset in ("high", "medium", "low"):
            with self.subTest(preset=preset):
                result = self._convert(preset)
                self.assertTrue(result.success, msg=f"{preset}: {result.error}")
                self.assertGreater(result.converted_size, 0)

    # ------------------------------------------------------------------
    # Fixed-width resize (proportional height)
    # ------------------------------------------------------------------
    def test_fixed_width_keeps_aspect_ratio(self):
        out_dir = os.path.join(self.tmp, "fixed_width")
        os.makedirs(out_dir, exist_ok=True)
        result = self.conv.convert_one(
            self.png_path, out_dir, quality=60,
            resize_cfg={"enabled": True, "width": 400, "height": 0},
        )
        self.assertTrue(result.success, msg=result.error)
        with Image.open(result.output_path) as img:
            # Source is 800×600 → width 400 must give height 300
            self.assertEqual(img.size, (400, 300))

    def test_batch_variants_two_widths(self):
        out_dir = os.path.join(self.tmp, "variants")
        os.makedirs(out_dir, exist_ok=True)
        variants = [
            {"resize_cfg": {"enabled": True, "width": 400, "height": 0}, "suffix": "_400px"},
            {"resize_cfg": {"enabled": True, "width": 200, "height": 0}, "suffix": "_200px"},
        ]
        results = self.conv.convert_batch(
            [self.png_path], out_dir, quality=60, variants=variants,
        )
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r.success for r in results),
                        msg="; ".join(r.error for r in results if not r.success))

        by_name = {os.path.basename(r.output_path): r for r in results}
        self.assertIn("test_rgb_400px.avif", by_name)
        self.assertIn("test_rgb_200px.avif", by_name)

        with Image.open(by_name["test_rgb_400px.avif"].output_path) as img:
            self.assertEqual(img.size, (400, 300))
        with Image.open(by_name["test_rgb_200px.avif"].output_path) as img:
            self.assertEqual(img.size, (200, 150))

    def test_batch_variants_multiple_files(self):
        out_dir = os.path.join(self.tmp, "variants_multi")
        os.makedirs(out_dir, exist_ok=True)
        variants = [
            {"resize_cfg": {"enabled": True, "width": 400, "height": 0}, "suffix": "_400px"},
            {"resize_cfg": {"enabled": True, "width": 200, "height": 0}, "suffix": "_200px"},
        ]
        results = self.conv.convert_batch(
            [self.png_path, self.rgba_path], out_dir, quality=60, variants=variants,
        )
        # 2 files × 2 widths = 4 outputs
        self.assertEqual(len(results), 4)
        self.assertTrue(all(r.success for r in results),
                        msg="; ".join(r.error for r in results if not r.success))
        names = {os.path.basename(r.output_path) for r in results}
        self.assertEqual(names, {
            "test_rgb_400px.avif", "test_rgb_200px.avif",
            "test_rgba_400px.avif", "test_rgba_200px.avif",
        })


class TestEncoderSelection(unittest.TestCase):
    """Engine routing rules — these hold with or without ffmpeg installed."""

    def test_pillow_always_available(self):
        from core import encoders
        self.assertTrue(encoders.engine_available(encoders.ENGINE_PILLOW))

    def test_available_engines_lists_all(self):
        from core import encoders
        avail = encoders.available_engines()
        self.assertEqual(set(avail), set(encoders.ENGINES))

    def test_quality_mapping_anchors(self):
        """Quality 60 matches the measured SSIM-equivalent settings."""
        from core import encoders
        self.assertEqual(encoders.quality_to_cq(60, encoders.ENGINE_SVTAV1), 30)
        self.assertEqual(encoders.quality_to_cq(60, encoders.ENGINE_NVENC), 35)

    def test_quality_mapping_is_monotonic_and_clamped(self):
        from core import encoders
        for eng in (encoders.ENGINE_SVTAV1, encoders.ENGINE_NVENC):
            with self.subTest(engine=eng):
                # Higher quality → lower CRF/CQ
                self.assertLess(encoders.quality_to_cq(90, eng),
                                encoders.quality_to_cq(30, eng))
                # Never leaves the valid range
                self.assertGreaterEqual(encoders.quality_to_cq(100, eng), 1)
                self.assertLessEqual(encoders.quality_to_cq(0, eng), 63)

    def test_pillow_engine_never_delegates(self):
        from core import encoders
        self.assertFalse(encoders.can_encode(encoders.ENGINE_PILLOW, "avif", False))

    def test_non_avif_formats_fall_back(self):
        from core import encoders
        for fmt in ("webp", "jpg", "png"):
            with self.subTest(fmt=fmt):
                self.assertFalse(encoders.can_encode(encoders.ENGINE_SVTAV1, fmt, False))

    def test_alpha_images_fall_back(self):
        from core import encoders
        self.assertFalse(encoders.can_encode(encoders.ENGINE_SVTAV1, "avif", True))

    def test_unknown_engine_raises(self):
        from core import encoders
        from PIL import Image
        with self.assertRaises(RuntimeError):
            encoders.encode_avif(Image.new("RGB", (8, 8)), "x.avif", 60, "bogus")


@unittest.skipUnless(AVIF_AVAILABLE, "pillow-avif-plugin not installed")
class TestExternalEngines(unittest.TestCase):
    """Real encodes through ffmpeg; skipped when an engine is unavailable."""

    @classmethod
    def setUpClass(cls):
        from core.converter import Converter
        cls.conv = Converter()
        cls.tmp = tempfile.mkdtemp(prefix="engine_test_")

        import random
        rnd = random.Random(11)
        cls.rgb = os.path.join(cls.tmp, "photo.png")
        img = Image.new("RGB", (600, 400))
        img.putdata([
            (min(255, x % 256 + rnd.randint(0, 30)),
             min(255, y % 256 + rnd.randint(0, 30)),
             min(255, (x + y) % 256 + rnd.randint(0, 30)))
            for y in range(400) for x in range(600)
        ])
        img.save(cls.rgb)

        cls.rgba = os.path.join(cls.tmp, "logo.png")
        Image.new("RGBA", (200, 150), (10, 90, 200, 120)).save(cls.rgba)

    def _run(self, engine, src=None, output_format="avif"):
        out_dir = os.path.join(self.tmp, f"{engine}_{output_format}")
        os.makedirs(out_dir, exist_ok=True)
        return self.conv.convert_one(
            src or self.rgb, out_dir, quality=60,
            output_format=output_format, engine=engine, keep_exif=False,
        )

    def test_svtav1_produces_valid_avif(self):
        from core import encoders
        if not encoders.engine_available(encoders.ENGINE_SVTAV1):
            self.skipTest("libsvtav1 not available in ffmpeg")
        r = self._run(encoders.ENGINE_SVTAV1)
        self.assertTrue(r.success, msg=r.error)
        self.assertEqual(r.engine, "svtav1")
        with Image.open(r.output_path) as img:
            self.assertEqual(img.format, "AVIF")
            self.assertEqual(img.size, (600, 400))

    def test_nvenc_produces_valid_avif(self):
        from core import encoders
        if not encoders.engine_available(encoders.ENGINE_NVENC):
            self.skipTest("av1_nvenc not available in ffmpeg")
        r = self._run(encoders.ENGINE_NVENC)
        self.assertTrue(r.success, msg=r.error)
        # NVENC can be listed but unusable (no GPU / driver); a fallback to
        # pillow is a correct outcome, a failed conversion is not.
        self.assertIn(r.engine, ("nvenc", "pillow"))
        with Image.open(r.output_path) as img:
            self.assertEqual(img.format, "AVIF")

    def test_alpha_falls_back_to_pillow_and_keeps_transparency(self):
        from core import encoders
        if not encoders.engine_available(encoders.ENGINE_SVTAV1):
            self.skipTest("libsvtav1 not available in ffmpeg")
        r = self._run(encoders.ENGINE_SVTAV1, src=self.rgba)
        self.assertTrue(r.success, msg=r.error)
        self.assertEqual(r.engine, "pillow")
        with Image.open(r.output_path) as img:
            self.assertEqual(img.mode, "RGBA")

    def test_non_avif_format_falls_back_to_pillow(self):
        from core import encoders
        if not encoders.engine_available(encoders.ENGINE_SVTAV1):
            self.skipTest("libsvtav1 not available in ffmpeg")
        r = self._run(encoders.ENGINE_SVTAV1, output_format="webp")
        self.assertTrue(r.success, msg=r.error)
        self.assertEqual(r.engine, "pillow")
        self.assertTrue(r.output_path.endswith(".webp"))

    def test_svtav1_is_smaller_than_pillow_at_same_quality(self):
        """The whole point of the SVT-AV1 engine: fewer bytes."""
        from core import encoders
        if not encoders.engine_available(encoders.ENGINE_SVTAV1):
            self.skipTest("libsvtav1 not available in ffmpeg")
        r_pil = self._run(encoders.ENGINE_PILLOW)
        r_svt = self._run(encoders.ENGINE_SVTAV1)
        self.assertTrue(r_pil.success and r_svt.success)
        self.assertLess(r_svt.converted_size, r_pil.converted_size)

    def test_batch_passes_engine_through(self):
        from core import encoders
        if not encoders.engine_available(encoders.ENGINE_SVTAV1):
            self.skipTest("libsvtav1 not available in ffmpeg")
        out_dir = os.path.join(self.tmp, "batch_engine")
        os.makedirs(out_dir, exist_ok=True)
        results = self.conv.convert_batch(
            [self.rgb], out_dir, quality=60,
            engine=encoders.ENGINE_SVTAV1, keep_exif=False,
        )
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].success, msg=results[0].error)
        self.assertEqual(results[0].engine, "svtav1")


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
        self.assertTrue(is_valid_image("image.webp"))
        self.assertTrue(is_valid_image("image.avif"))
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

        # Test jpg format and overwrite prevention
        out_jpg = build_output_path(src, output_format="jpg")
        out_jpg_path = pathlib.Path(out_jpg)
        self.assertEqual(out_jpg_path.suffix, ".jpg")
        self.assertEqual(out_jpg_path.stem, "photo_converted")

    def test_build_output_path_with_suffix(self):
        import pathlib
        from utils.file_utils import build_output_path
        src = str(pathlib.Path.home() / "photo.jpg")
        out = pathlib.Path(build_output_path(src, output_format="avif", suffix="-opt"))
        self.assertEqual(out.stem, "photo-opt")
        self.assertEqual(out.suffix, ".avif")

    def test_build_output_path_px_suffix(self):
        import pathlib
        from utils.file_utils import build_output_path
        src = str(pathlib.Path.home() / "fotografia40.jpg")
        out = pathlib.Path(build_output_path(src, output_format="avif", suffix="_1200px"))
        self.assertEqual(out.name, "fotografia40_1200px.avif")

    def test_sanitize_suffix_strips_unsafe_chars(self):
        from utils.file_utils import sanitize_suffix
        self.assertEqual(sanitize_suffix('-opt'), '-opt')
        self.assertEqual(sanitize_suffix('../evil'), '..evil')
        self.assertEqual(sanitize_suffix('a/b\\c:d*e'), 'abcde')
        self.assertEqual(sanitize_suffix(None), '')

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
