from pathlib import Path

import shutil
import sys
import json
import os

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
    # 手动清理整个安装目录，防止旧文件残留，节点变化导致的冲突
    if install_path.exists():
        print(f"Cleaning existing installation directory: {install_path}")
        shutil.rmtree(install_path)
    
    # 确保安装目录存在
    install_path.mkdir(parents=True, exist_ok=True)

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


def install_MFAAvalonia():
    # 检查 MFA 目录是否存在
    mfa_dir = working_dir / "MFA"
    if not mfa_dir.exists():
        print("Warning: MFA directory not found. Skipping MFA installation.")
        return

    # 根据操作系统确定可执行文件名和扩展名
    if os.name == "nt":  # Windows
        mfa_exe_name = "MFAAvalonia.exe"
        install_exe_name = "MaaGF2Exilium.exe"
    else:  # Unix/Linux
        mfa_exe_name = "MFAAvalonia"
        install_exe_name = "MaaGF2Exilium"

    # 复制 MFA 目录下的所有内容
    for item in mfa_dir.iterdir():
        if item.is_file():
            dest_path = install_path / item.name
            # 如果是主可执行文件，则重命名
            if item.name == mfa_exe_name:
                dest_path = install_path / install_exe_name
            
            shutil.copy2(item, dest_path)
            
            # 在 Unix 系统上，如果是可执行文件需要确保可执行权限
            if os.name != "nt" and (item.suffix == ".exe" or item.suffix == "" and os.access(item, os.X_OK)):
                os.chmod(dest_path, 0o755)
                
        elif item.is_dir():
            # 复制子目录
            shutil.copytree(
                item,
                install_path / item.name,
                dirs_exist_ok=True,
            )

    print(f"Copied all MFA contents to {install_path}, with {mfa_exe_name} renamed to {install_exe_name}")


if __name__ == "__main__":
    install_resource()
    install_deps()
    install_chores()
    install_MFAAvalonia()

    print(f"Install to {install_path} successfully.")
