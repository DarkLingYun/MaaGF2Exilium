"""Keep all advertised game tasks guarded, including tasks added in future."""

import json
import unittest
from pathlib import Path

ASSETS = Path(__file__).resolve().parents[1] / "assets"


def read(path):
    return json.loads((ASSETS / path).read_text(encoding="utf-8"))


class ResolutionResourceTests(unittest.TestCase):
    def test_every_game_task_has_a_pc_gate_without_changing_android_actions(self):
        base = read("resource/base/pipeline/tasks/ResolutionChecks.json")
        pc = read("resource/resource_pc/pipeline/tasks/ResolutionChecks.json")
        covered = set()
        for path in (ASSETS / "tasks").glob("*.json"):
            for task in json.loads(path.read_text(encoding="utf-8"))["task"]:
                entry = task["entry"]
                if entry in {"CommunityDailyHelper", "CheckPCResolution"}:
                    continue
                with self.subTest(task=task["name"]):
                    self.assertTrue(entry.startswith("ResolutionCheck_"))
                    self.assertEqual(base[entry]["action"], "DoNothing")
                    self.assertEqual(
                        base[entry]["next"], [entry.removeprefix("ResolutionCheck_")]
                    )
                    self.assertEqual(base[entry]["on_error"], [])
                    self.assertEqual(pc[entry]["action"], "Custom")
                    self.assertEqual(pc[entry]["custom_action"], "CheckPCResolution")
                    covered.add(entry)
        self.assertEqual(covered, set(base))
        self.assertEqual(covered, set(pc))
        self.assertEqual(
            read("tasks/community.json")["task"][0]["entry"], "CommunityDailyHelper"
        )

    def test_pc_scaling_and_optional_check_have_translated_configuration(self):
        interface = read("interface.json")
        for controller in interface["controller"]:
            if controller["type"] == "Win32":
                self.assertEqual(controller["display_short_side"], 720)
        task = read("tasks/startGame.json")["task"][0]
        self.assertEqual(task["entry"], "CheckPCResolution")
        self.assertFalse(task["default_check"])
        self.assertEqual(set(task["controller"]), {"桌面端-前台", "桌面端-后台"})
        for language in interface["languages"].values():
            strings = read(language)
            for key in [task["label"], task["description"]]:
                self.assertTrue(strings[key.removeprefix("$")])
