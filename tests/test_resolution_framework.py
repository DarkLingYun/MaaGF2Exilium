"""Exercise the real MaaFramework task queue and coordinate mapping without a game.

All input goes to RecordingController, never to an OS window or an emulator.
"""

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

import numpy as np
from maa.controller import CustomController
from maa.agent_client import AgentClient
from maa.resource import Resource
from maa.tasker import LoggingLevelEnum, Tasker

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agent"))
from resolution_check import PCResolutionCheck  # noqa: E402


class RecordingController(CustomController):
    def __init__(self, width, height):
        super().__init__()
        self.size = (width, height)
        self.inputs = []

    def connect(self):
        return True

    def request_uuid(self):
        return "resolution-test"

    def get_features(self):
        return 0

    def screencap(self):
        return np.zeros((self.size[1], self.size[0], 3), dtype=np.uint8)

    def click(self, x, y):
        self.inputs.append((x, y))
        return True

    def start_app(self, *args):
        raise AssertionError("Unexpected app start")

    stop_app = swipe = touch_down = touch_move = touch_up = click_key = input_text = (
        key_down
    ) = key_up = start_app


class FrameworkResolutionTests(unittest.TestCase):
    def setUp(self):
        Tasker.set_stdout_level(LoggingLevelEnum.Error)
        self.folder = tempfile.TemporaryDirectory()
        root = Path(self.folder.name)
        (root / "pipeline").mkdir()
        (root / "pipeline" / "test.json").write_text(
            json.dumps(
                {
                    "First": {
                        "recognition": "DirectHit",
                        "action": "Click",
                        "target": [640, 360, 1, 1],
                        "post_delay": 0,
                    },
                    "Second": {
                        "recognition": "DirectHit",
                        "action": "Click",
                        "target": [320, 180, 1, 1],
                        "post_delay": 0,
                    },
                    "GuardFirst": {
                        "recognition": "DirectHit",
                        "action": "Custom",
                        "custom_action": "CheckPCResolution",
                        "next": ["First"],
                        "pre_delay": 0,
                        "post_delay": 0,
                    },
                    "GuardSecond": {
                        "recognition": "DirectHit",
                        "action": "Custom",
                        "custom_action": "CheckPCResolution",
                        "next": ["Second"],
                        "pre_delay": 0,
                        "post_delay": 0,
                    },
                }
            ),
            encoding="utf-8",
        )
        self.resource = Resource()
        self.assertTrue(self.resource.post_bundle(root).wait().succeeded)
        self.ctrl = RecordingController(1920, 1080)
        self.assertTrue(self.ctrl.post_connection().wait().succeeded)
        self.assertTrue(self.ctrl.set_screenshot_target_short_side(720))
        self.tasker = Tasker()
        self.assertTrue(self.tasker.bind(self.resource, self.ctrl))
        self.guard = PCResolutionCheck()
        self.resource.register_custom_action("CheckPCResolution", self.guard)

    def tearDown(self):
        self.tasker.post_stop().wait()
        self.tasker.clear_sinks()
        self.folder.cleanup()

    def test_native_scaling_maps_resource_coordinates_to_original_window(self):
        with contextlib.redirect_stdout(io.StringIO()):
            result = self.tasker.post_task("GuardFirst").wait()
        self.assertTrue(result.succeeded)
        self.assertEqual(self.ctrl.inputs, [(960, 540)])
        self.assertEqual(self.ctrl.cached_image.shape[:2], (720, 1280))

    def test_native_stop_prevents_current_and_queued_input_then_allows_retry(self):
        self.ctrl.size = (1920, 1200)
        # Hold the starting callback until both jobs are enqueued, avoiding a
        # timing-dependent "queue" test that only posts after cancellation.
        entered = threading.Event()
        resume = threading.Event()
        original = self.guard.run

        def blocked(context, argv):
            if argv.node_name == "GuardFirst":
                entered.set()
                if not resume.wait(5):
                    context.tasker.post_stop()
                    return False
            return original(context, argv)

        self.guard.run = blocked
        with contextlib.redirect_stdout(io.StringIO()) as output:
            first = self.tasker.post_task("GuardFirst")
            self.assertTrue(entered.wait(5))
            second = self.tasker.post_task("GuardSecond")
            resume.set()
            first.wait()
            second.wait()
        self.assertFalse(first.succeeded)
        self.assertFalse(second.succeeded)
        self.assertEqual(self.ctrl.inputs, [])
        self.assertIn("1920×1200", output.getvalue())
        deadline = time.monotonic() + 5
        while self.tasker.stopping and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertFalse(self.tasker.stopping)

        self.ctrl.size = (2560, 1440)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(self.tasker.post_task("GuardSecond").wait().succeeded)
        self.assertEqual(self.ctrl.inputs, [(640, 360)])

    @unittest.skipUnless(
        hasattr(AgentClient, "create_tcp"),
        "TCP Agent fixture requires a newer framework",
    )
    def test_agent_rpc_blocks_zero_delay_input_and_recovers_after_resize(self):
        # Real cross-process transport matters: event notifications alone can
        # race with a zero-delay action. The synchronous custom action must not.
        self.resource.unregister_custom_action("CheckPCResolution")
        client = AgentClient.create_tcp()
        client.set_timeout(5000)
        self.assertTrue(client.bind(self.resource))
        self.assertTrue(client.register_sink(self.resource, self.ctrl, self.tasker))
        log_path = Path(self.folder.name) / "agent.log"
        with log_path.open("w", encoding="utf-8") as log:
            kwargs = (
                {"creationflags": subprocess.CREATE_NO_WINDOW}
                if os.name == "nt"
                else {}
            )
            process = subprocess.Popen(
                [
                    sys.executable,
                    str(Path(__file__).with_name("resolution_agent_server.py")),
                    client.identifier,
                ],
                stdout=log,
                stderr=subprocess.STDOUT,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                **kwargs,
            )
            try:
                self.assertTrue(client.connect())
                self.ctrl.size = (1920, 1200)
                first = self.tasker.post_task("GuardFirst")
                second = self.tasker.post_task("GuardSecond")
                first.wait()
                second.wait()
                self.assertFalse(first.succeeded)
                self.assertFalse(second.succeeded)
                self.assertEqual(self.ctrl.inputs, [])
                deadline = time.monotonic() + 5
                while self.tasker.stopping and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.ctrl.size = (1920, 1080)
                self.assertTrue(self.tasker.post_task("GuardFirst").wait().succeeded)
                self.assertEqual(self.ctrl.inputs, [(960, 540)])
            finally:
                self.tasker.post_stop().wait()
                self.tasker.clear_sinks()
                self.ctrl.clear_sinks()
                self.resource.clear_sinks()
                client.disconnect()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    process.wait(timeout=5)
        output = log_path.read_text(encoding="utf-8")
        self.assertIn("1920×1200", output)
        self.assertIn("1920×1080", output)


if __name__ == "__main__":
    unittest.main()
