import contextlib
import io
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agent"))
from resolution_check import (  # noqa: E402
    PCResolutionCheck,
    check_controller,
    format_result,
    validate_resolution,
)


class ResolutionTests(unittest.TestCase):
    def test_same_ratio_resolutions_use_one_coordinate_space(self):
        for size in [
            (1280, 720),
            (1600, 900),
            (1920, 1080),
            (2560, 1440),
            (3840, 2160),
        ]:
            with self.subTest(size=size):
                self.assertFalse(validate_resolution(size, (1280, 720)).error)

    def test_rejects_wrong_ratios_even_if_image_was_stretched(self):
        for size in [(1280, 800), (2560, 1600), (3440, 1440), (1360, 768), (1366, 768)]:
            with self.subTest(size=size):
                self.assertEqual(validate_resolution(size, (1280, 720)).error, "ratio")

    def test_rejects_small_and_portrait_windows(self):
        for size in [(960, 540), (720, 1280), (1080, 1920)]:
            with self.subTest(size=size):
                self.assertEqual(
                    validate_resolution(size, (1280, 720)).error, "minimum"
                )

    def test_rejects_wrong_scaled_size_and_empty_capture(self):
        self.assertEqual(
            validate_resolution((1920, 1080), (1920, 1080)).error, "scaling"
        )
        self.assertEqual(validate_resolution((0, 0), (1280, 720)).error, "capture")
        self.assertEqual(validate_resolution((1920, 1080), (0, 0)).error, "capture")

    def test_reports_current_and_target_dimensions_in_both_languages(self):
        result = validate_resolution((2560, 1600), (1152, 720))
        for english in [False, True]:
            message = format_result(result, english)
            self.assertIn("2560×1600", message)
            self.assertIn("1152×720", message)
            self.assertIn("1280×720", message)
            self.assertNotIn("\n", message)

    @staticmethod
    def controller(raw=(1920, 1080), scaled=(1280, 720), kind="win32"):
        return SimpleNamespace(
            info={"type": kind},
            resolution=raw,
            cached_image=np.zeros((scaled[1], scaled[0], 3), dtype=np.uint8),
            post_screencap=Mock(
                return_value=SimpleNamespace(
                    wait=lambda: SimpleNamespace(succeeded=True)
                )
            ),
        )

    def test_fresh_capture_replaces_a_previous_valid_resolution(self):
        ctrl = self.controller()
        self.assertFalse(check_controller(ctrl).error)
        ctrl.resolution = (1280, 800)
        ctrl.cached_image = np.zeros((720, 1152, 3), dtype=np.uint8)
        self.assertEqual(check_controller(ctrl).error, "ratio")
        self.assertEqual(ctrl.post_screencap.call_count, 2)

    @patch("resolution_check.time.sleep")
    def test_failed_capture_does_not_reuse_valid_cached_image(self, sleep):
        ctrl = self.controller()
        ctrl.post_screencap.return_value.wait = lambda: SimpleNamespace(succeeded=False)
        self.assertEqual(check_controller(ctrl).error, "capture")
        self.assertEqual(ctrl.post_screencap.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    @patch("resolution_check.time.sleep")
    def test_retry_can_recover_but_known_wrong_size_does_not_retry(self, sleep):
        ctrl = self.controller()
        ctrl.post_screencap.side_effect = [
            RuntimeError("not ready"),
            ctrl.post_screencap.return_value,
        ]
        self.assertFalse(check_controller(ctrl).error)
        self.assertEqual(sleep.call_count, 1)
        wrong = self.controller(raw=(1920, 1200))
        self.assertEqual(check_controller(wrong).error, "ratio")
        self.assertEqual(wrong.post_screencap.call_count, 1)

    def invoke_guard(self, ctrl):
        tasker = SimpleNamespace(controller=ctrl, post_stop=Mock())
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            success = PCResolutionCheck().run(SimpleNamespace(tasker=tasker), None)
        self.assertEqual(success, not tasker.post_stop.called)
        return tasker, output.getvalue()

    def test_invalid_target_stops_and_reports_then_can_retry_after_fix(self):
        ctrl = self.controller(raw=(1920, 1200))
        tasker, output = self.invoke_guard(ctrl)
        tasker.post_stop.assert_called_once()
        self.assertIn("1920×1200", output)
        ctrl.resolution = (1920, 1080)
        tasker, output = self.invoke_guard(ctrl)
        tasker.post_stop.assert_not_called()
        self.assertIn("1280×720", output)

    def test_missing_controller_is_not_silently_allowed(self):
        tasker, output = self.invoke_guard(SimpleNamespace())
        tasker.post_stop.assert_called_once()
        self.assertIn("0×0", output)

    def test_old_framework_does_not_need_controller_info_or_pi_environment(self):
        ctrl = self.controller()
        del ctrl.info
        tasker, output = self.invoke_guard(ctrl)
        tasker.post_stop.assert_not_called()
        self.assertIn("1920×1080", output)


if __name__ == "__main__":
    unittest.main()
