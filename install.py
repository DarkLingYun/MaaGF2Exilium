from pathlib import Path

import shutil
import sys
import json

from configure import configure_ocr_model


working_dir = Path(__file__).parent
install_path = working_dir / Path("install")
version = len(sys.argv) > 1 and sys.argv[1] or "v0.0.1"


def install_deps():
    if not (working_dir / "deps" / "bin").exists():
        print('Please download the MaaFramework to "deps" first.')
        print('请先下载 MaaFramework 到 "deps"。')
        sys.exit(1)

    shutil.copytree(
        working_dir / "deps" / "bin",
        install_path,
        ignore=shutil.ignore_patterns(
            "*MaaDbgControlUnit*",
            "*MaaThriftControlUnit*",
            "*MaaRpc*",
            "*MaaHttp*",
        ),
        dirs_exist_ok=True,
    )
    shutil.copytree(
        working_dir / "deps" / "share" / "MaaAgentBinary",
        install_path / "MaaAgentBinary",
        dirs_exist_ok=True,
    )


def install_resource():
    # 手动清理资源目录，防止旧文件残留，节点变化导致的冲突
    resource_dir_to_clean = install_path / "resource"
    if resource_dir_to_clean.exists():
        print(f"正在清理已存在的资源目录: {resource_dir_to_clean}")
        shutil.rmtree(resource_dir_to_clean)

    configure_ocr_model()

    shutil.copytree(
        working_dir / "assets" / "resource",
        install_path / "resource",
        dirs_exist_ok=True,
    )
    shutil.copy2(
        working_dir / "assets" / "interface.json",
        install_path,
    )

    with open(install_path / "interface.json", "r", encoding="utf-8") as f:
        interface = json.load(f)

    interface["version"] = version

    with open(install_path / "interface.json", "w", encoding="utf-8") as f:
        json.dump(interface, f, ensure_ascii=False, indent=4)


def install_chores():
    shutil.copy2(
        working_dir / "README.md",
        install_path,
    )
    shutil.copy2(
        working_dir / "LICENSE",
        install_path,
    )


def install_mfawpf():
    mfa_exe_path = working_dir / "MFA" / "MFAWPF.exe"
    install_exe_path = install_path / "MaaGF2Exilium.exe"

    if mfa_exe_path.exists():
        shutil.copy2(
            mfa_exe_path,
            install_exe_path,
        )
        print(f"Copied MFAWPF.exe to {install_exe_path}")
    else:
        print("Warning: MFA/MFAWPF.exe not found. Skipping copy operation.")


if __name__ == "__main__":
    install_deps()
    install_resource()
    install_chores()
    install_mfawpf()

    print(f"Install to {install_path} successfully.")
