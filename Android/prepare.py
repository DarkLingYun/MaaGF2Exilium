"""Stage MaaGF2Exilium's Android resources without changing the desktop interface."""

import argparse
import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UNAVAILABLE_ENTRY = "CommunityDailyHelper"


def read_json(path):
    # MaaFramework pipeline files allow comments and trailing commas. Match
    # strings first so URLs, regexes, and comment-like text remain untouched.
    text = path.read_text(encoding="utf-8-sig")
    strings_or_comments = r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*.*?\*/'
    text = re.sub(strings_or_comments, lambda match: match[0] if match[0].startswith('"') else " ",
                  text, flags=re.DOTALL)
    text = re.sub(r'"(?:\\.|[^"\\])*"|,\s*(?=[}\]])',
                  lambda match: match[0] if match[0].startswith('"') else "", text)
    return json.loads(text)


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def android_interface(interface, version, repository):
    # main.py has no registered callbacks. The community task refers to a
    # missing CommunityDailyAction, so it cannot run on Android either.
    interface.pop("agent", None)
    interface.pop("mirrorchyan_rid", None)  # Desktop resource updates are not APK updates.
    interface["controller"] = [item for item in interface["controller"] if item["type"] == "Adb"]
    if not interface["controller"]:
        raise ValueError("Android packaging requires an Adb controller")
    interface["resource"] = [
        item for item in interface["resource"]
        if all("resource_pc" not in path.replace("\\", "/").split("/") for path in item["path"])
    ]
    # MaaFwApp resolves paths relative to its installed PI directory and does
    # not expand the desktop {PROJECT_DIR} placeholder. Use these same paths
    # for copying resources and for the generated interface consumed at runtime.
    for resource in interface["resource"]:
        resource["path"] = [
            path.replace("\\", "/").removeprefix("{PROJECT_DIR}/")
            for path in resource["path"]
        ]
    interface["task"] = [item for item in interface["task"] if item["entry"] != UNAVAILABLE_ENTRY]
    interface["version"] = version
    interface["github"] = f"https://github.com/{repository}"
    interface["url"] = interface["github"]
    return interface


def validate_pipelines(resource):
    for path in resource.rglob("*.json"):
        if "pipeline" not in path.parts:
            continue
        nodes = read_json(path)
        removed = nodes.pop(UNAVAILABLE_ENTRY, None)
        if removed is not None:
            if nodes:
                write_json(path, nodes)
            else:
                path.unlink()
                continue
        for name, node in nodes.items():
            if not isinstance(node, dict):
                continue
            for key in ("action", "recognition"):
                value = node.get(key)
                kind = value.get("type") if isinstance(value, dict) else value
                if kind == "Custom":
                    raise ValueError(f"{path}: {name} needs an Android agent for custom {key}")


def prepare(root=ROOT, version="v0.0.0-dev", repository="DarkLingYun/MaaGF2Exilium"):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("repository must be owner/name")
    output = root / "Android" / "assets"
    # This generated directory is fixed inside the project, never caller-selected.
    if output.exists():
        if output.is_symlink() or not output.resolve().is_relative_to(root.resolve()):
            raise ValueError("Android assets must stay inside the project")
        shutil.rmtree(output)
    output.mkdir(parents=True)
    interface = android_interface(read_json(root / "assets" / "interface.json"), version, repository)
    copied = set()
    for resource in interface["resource"]:
        for entry in resource["path"]:
            relative = Path(entry)
            if relative.is_absolute() or ".." in relative.parts or not relative.parts or relative.parts[0] != "resource":
                raise ValueError(f"Unsupported resource path: {entry}")
            if relative not in copied:
                shutil.copytree(root / "assets" / relative, output / relative, dirs_exist_ok=True)
                copied.add(relative)
    ocr = root / "assets" / "MaaCommonAssets" / "OCR" / "ppocr_v6" / "medium"
    for name in ("det.onnx", "rec.onnx", "keys.txt"):
        if not (ocr / name).is_file():
            raise FileNotFoundError(f"Missing OCR model {ocr / name}; initialize submodules recursively")
    shutil.copytree(ocr, output / "resource" / "base" / "model" / "ocr", dirs_exist_ok=True)
    validate_pipelines(output / "resource")
    for language, filename in interface.get("languages", {}).items():
        translations = read_json(root / "assets" / filename)
        if language == "zh_cn":
            translations.update({"中文资源(模拟器)": "中文资源(安卓)", "英语资源(模拟器)": "英文资源(安卓)",
                                 "服务器选择说明": "请选择设备上已安装的游戏服务器版本"})
        elif language == "en_us":
            translations.update({"中文资源(模拟器)": "Chinese Resource (Android)",
                                 "英语资源(模拟器)": "English Resource (Android)",
                                 "服务器选择说明": "Select the game server version installed on this device."})
        write_json(output / filename, translations)
    shutil.copy2(root / "LICENSE", output / "LICENSE")
    write_json(output / "interface.json", interface)
    print(f"Android resources staged at {output}")
    print("Community daily operations excluded: CommunityDailyAction is not implemented in MaaGF2Exilium.")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="v0.0.0-dev")
    parser.add_argument("--repository", default="DarkLingYun/MaaGF2Exilium")
    args = parser.parse_args()
    prepare(version=args.version, repository=args.repository)
