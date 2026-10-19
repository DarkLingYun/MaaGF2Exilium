"""Stage MaaGF2Exilium's Android resources without changing the desktop interface."""

import argparse
import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENT_ENTRY = "agent/main.py"


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


def agent_entry(argument):
    """Normalize the agent path: desktop uses {PROJECT_DIR}/agent/main.py, MXU uses ./agent/main.py."""
    if not isinstance(argument, str):
        return None
    return argument.replace("\\", "/").removeprefix("{PROJECT_DIR}/").removeprefix("./")


def android_interface(interface, version, repository):
    # The Android profile launches this same entry point using its bundled Python.
    # The profile supplies its own executable and args, so only the relative entry
    # path matters here.
    agent = interface.get("agent")
    arguments = agent.get("child_args") if isinstance(agent, dict) else None
    if (not isinstance(agent, dict) or not agent.get("child_exec")
            or not isinstance(arguments, list) or len(arguments) != 2
            or arguments[0] != "-u" or agent_entry(arguments[1]) != AGENT_ENTRY):
        raise ValueError("Android profile requires a single Python agent at agent/main.py")
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
    interface["version"] = version
    interface["github"] = f"https://github.com/{repository}"
    interface["url"] = interface["github"]
    return interface


def copy_interface_imports(interface, source_root, target_root, seen=None):
    """Copy PI `import` fragments into the staged interface, keeping relative paths.

    MaaFwApp resolves imports against the PI root, so an APK built from a split
    interface must contain the same task/option fragments as the desktop one.
    """
    seen = set() if seen is None else seen
    for import_path in interface.get("import", []) or []:
        relative = Path(import_path)
        if relative.is_absolute() or ".." in relative.parts or not relative.parts:
            raise ValueError(f"Invalid interface import path: {import_path}")
        source = source_root / relative
        if not source.is_file():
            raise FileNotFoundError(f"interface.json imports missing file: {import_path}")
        destination = target_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        resolved = source.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        copy_interface_imports(read_json(source), source.parent, destination.parent, seen)


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
    if not (root / "agent" / "main.py").is_file():
        raise FileNotFoundError("Missing Python agent entry point: agent/main.py")
    shutil.copytree(root / "agent", output / "agent", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
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
    copy_interface_imports(interface, root / "assets", output)
    print(f"Android resources staged at {output}")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="v0.0.0-dev")
    parser.add_argument("--repository", default="DarkLingYun/MaaGF2Exilium")
    args = parser.parse_args()
    prepare(version=args.version, repository=args.repository)
