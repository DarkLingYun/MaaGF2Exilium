import json
import sys

from typing import List
from pathlib import Path

from maa.resource import Resource
from maa.tasker import Tasker, LoggingLevelEnum


def check(dirs: List[Path]) -> bool:
    resource = Resource()

    print(f"Checking {len(dirs)} directories...")

    for rel_dir in dirs:
        print(f"  - {rel_dir}")
        status = resource.post_bundle(rel_dir).wait().status
        if not status.succeeded:
            print(f"Failed to check {rel_dir}.")
            return False

    print("All directories checked.")
    return True


def load_resource_paths(interface_path: Path, project_dir: Path) -> List[dict]:
    """从 interface.json 加载 resource 配置

    按 PI V2 协议，resource.path 中的相对路径是相对于 interface.json
    所在目录解析的（project_dir 即该目录）。绝对路径原样使用。
    """
    with open(interface_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    resources = data.get("resource", [])
    result = []

    for res in resources:
        name = res.get("name", "Unknown")
        paths = res.get("path", [])
        resolved_paths = [
            Path(p) if Path(p).is_absolute() else project_dir / p for p in paths
        ]
        result.append({"name": name, "paths": resolved_paths})

    return result


# assets 目录固定路径
ASSETS_DIR = Path("assets")


def main():
    interface_path = ASSETS_DIR / "interface.json"

    if not interface_path.exists():
        print(f"Error: interface.json not found at {interface_path}")
        sys.exit(1)

    Tasker.set_stdout_level(LoggingLevelEnum.Warn)

    # 加载所有 resource 配置
    resources = load_resource_paths(interface_path, ASSETS_DIR)

    print(f"Found {len(resources)} resource configurations in interface.json\n")

    all_passed = True
    for res in resources:
        name = res["name"]
        paths = res["paths"]
        print(f"=== Checking resource: {name} ===")
        if not check(paths):
            print(f"!!! Resource '{name}' check FAILED !!!\n")
            all_passed = False
        else:
            print(f"Resource '{name}' check PASSED\n")

    if not all_passed:
        print("Some resource checks failed.")
        sys.exit(1)

    print("All resource configurations checked successfully.")


if __name__ == "__main__":
    main()
