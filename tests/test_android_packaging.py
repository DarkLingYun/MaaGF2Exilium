import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.prepare_android import ROOT, android_interface, prepare, read_json
from scripts.android_version import parse_version, resolve_version, version_from_describe


class AndroidVersionTests(unittest.TestCase):
    def test_untagged_commit_is_valid_prerelease(self):
        self.assertEqual(version_from_describe("fb67c84", 123), "0.0.0-dev.123+gfb67c84")

    def test_release_tags_and_post_release_builds(self):
        cases = {
            "v1.2.3-0-gabc123": "1.2.3",
            "v1.2.3-4-gabc123": "1.2.4-dev.4+gabc123",
            "v1.2.3-beta.1-0-gabc123": "1.2.3-beta.1",
            "v1.2.3-beta.1-4-gabc123": "1.2.3-beta.1.dev.4+gabc123",
        }
        for describe, expected in cases.items():
            with self.subTest(describe=describe):
                actual = version_from_describe(describe, 123)
                self.assertEqual(actual, expected)
                self.assertIsNotNone(parse_version(actual))

    def test_explicit_version_is_validated(self):
        self.assertEqual(resolve_version("v1.2.3"), "1.2.3")
        for invalid in ("main", "fb67c84", "1.2.3-dev.01", "1.2.3\ninjected=value"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                resolve_version(invalid)


class AndroidPackagingTests(unittest.TestCase):
    def setUp(self):
        temp_root = ROOT / "build" / "android-tests"
        temp_root.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=temp_root)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.interface = json.loads((ROOT / "assets/interface.json").read_text(encoding="utf-8"))
        assets = self.root / "assets"
        assets.mkdir()
        (assets / "interface.json").write_text(json.dumps(self.interface), encoding="utf-8")
        for filename in self.interface["languages"].values():
            (assets / filename).write_bytes((ROOT / "assets" / filename).read_bytes())
        for pack in ("base", "resource_en", "resource_pc"):
            pipeline = assets / "resource" / pack / "pipeline" / "tasks"
            pipeline.mkdir(parents=True)
            (pipeline / "test.json").write_text('{"StartGame": {"action": "Click"}}', encoding="utf-8")
        community = assets / "resource/base/pipeline/tasks/community.json"
        community.write_text(json.dumps({"CommunityDailyHelper": {
            "action": "Custom", "custom_action": "CommunityDailyAction"
        }}), encoding="utf-8")
        ocr = assets / "MaaCommonAssets/OCR/ppocr_v6/medium"
        ocr.mkdir(parents=True)
        for name in ("det.onnx", "rec.onnx", "keys.txt"):
            (ocr / name).write_bytes(b"test model")
        (self.root / "LICENSE").write_text("MIT", encoding="utf-8")

    def test_package_preserves_game_tasks_and_translations_without_desktop_dependencies(self):
        output = prepare(self.root, "v1.2.3", "owner/MaaGF2Exilium")
        interface = json.loads((output / "interface.json").read_text(encoding="utf-8"))
        self.assertEqual(interface["version"], "v1.2.3")
        self.assertEqual(interface["github"], "https://github.com/owner/MaaGF2Exilium")
        self.assertNotIn("agent", interface)
        self.assertNotIn("mirrorchyan_rid", interface)
        self.assertEqual([item["type"] for item in interface["controller"]], ["Adb"])
        self.assertEqual(len(interface["task"]), len(self.interface["task"]) - 1)
        self.assertEqual(interface["option"], self.interface["option"])
        self.assertEqual(len(interface["resource"]), 2)
        self.assertFalse((output / "resource/resource_pc").exists())
        self.assertFalse((output / "resource/base/pipeline/tasks/community.json").exists())
        for name in ("det.onnx", "rec.onnx", "keys.txt"):
            self.assertTrue((output / "resource/base/model/ocr" / name).is_file())
        for filename in interface["languages"].values():
            self.assertTrue((output / filename).is_file())
        self.assertEqual(json.loads((self.root / "assets/interface.json").read_text()), self.interface)

    def test_restage_removes_stale_files(self):
        output = prepare(self.root)
        (output / "obsolete.json").write_text("{}")
        prepare(self.root)
        self.assertFalse((output / "obsolete.json").exists())

    def test_resource_paths_resolve_from_android_install_directory(self):
        output = prepare(self.root)
        interface = read_json(output / "interface.json")
        self.assertEqual([resource["path"] for resource in interface["resource"]],
                         [["resource/base"], ["resource/base", "resource/resource_en"]])
        for resource in interface["resource"]:
            for entry in resource["path"]:
                self.assertNotIn("{PROJECT_DIR}", entry)
                self.assertTrue((output / entry / "pipeline/tasks/test.json").is_file())
        self.assertEqual(read_json(self.root / "assets/interface.json"), self.interface)

    def test_missing_ocr_fails_before_build(self):
        (self.root / "assets/MaaCommonAssets/OCR/ppocr_v6/medium/rec.onnx").unlink()
        with self.assertRaisesRegex(FileNotFoundError, "initialize submodules"):
            prepare(self.root)

    def test_future_custom_callbacks_require_agent_support(self):
        node = self.root / "assets/resource/base/pipeline/tasks/new.json"
        for action in ("Custom", {"type": "Custom", "param": {"custom_action": "NewAction"}}):
            node.write_text(json.dumps({"NewNode": {"action": action}}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "needs an Android agent"):
                prepare(self.root)

    def test_adb_controller_is_required(self):
        interface = copy.deepcopy(self.interface)
        interface["controller"] = [{"name": "PC", "type": "Win32"}]
        with self.assertRaisesRegex(ValueError, "Adb"):
            android_interface(interface, "v1", "owner/MaaGF2Exilium")

    def test_invalid_repository_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "owner/name"):
            prepare(self.root, repository="../other/project")

    def test_pipeline_comments_and_trailing_commas_preserve_string_contents(self):
        path = self.root / "comments.json"
        path.write_text('''{
            // A MaaFramework pipeline comment
            "url": "https://example.com/", /* another comment */
            "text": "literal /* comment */ ,}",
            "values": [1, 2,],
        }''', encoding="utf-8")
        self.assertEqual(read_json(path), {"url": "https://example.com/",
                                         "text": "literal /* comment */ ,}", "values": [1, 2]})


if __name__ == "__main__":
    unittest.main()
