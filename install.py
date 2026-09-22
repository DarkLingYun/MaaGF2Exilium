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

    # MXU 从安装根目录下的 maafw/ 加载 MaaFramework（内部按 "maafw/MaaFramework.dll"
    # 定位），不像 MFAAvalonia 那样平铺在安装根目录。MaaAgentBinary 也要跟着
    # 放到 maafw/ 下，MaaFramework 按自身库目录寻找它。
    shutil.copytree(
        working_dir / "deps" / "bin",
        install_path / "maafw",
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
        install_path / "maafw" / "MaaAgentBinary",
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

    # 复制 ProjectInterface V2 的多语言词条文件（interface.json 中 $key 显示字段依赖它们）
    # Copy the ProjectInterface V2 language files that interface.json's $key
    # display fields resolve against; without them the GUI shows raw $keys.
    for lang_file in interface.get("languages", {}).values():
        src = working_dir / "assets" / lang_file
        if src.exists():
            shutil.copy2(src, install_path)
        else:
            print(f"Warning: language file referenced by interface.json not found: {lang_file}")

    interface["version"] = version

    # 如果存在嵌入式 Python，则使用它来启动 agent
    if (working_dir / "deps" / "python" / "python.exe").exists():
        if "agent" in interface:
            interface["agent"]["child_exec"] = "python/python.exe"
            interface["agent"]["child_args"] = [
                "-u",
                "./agent/main.py"
            ]
            print("Agent configured to use embedded Python.")

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


def install_agent():
    shutil.copytree(
        working_dir / "agent",
        install_path / "agent",
        dirs_exist_ok=True,
    )


def install_python():
    python_dir = working_dir / "deps" / "python"
    if not python_dir.exists():
        print("Embedded Python not found, skipping.")
        return

    shutil.copytree(
        python_dir,
        install_path / "python",
        dirs_exist_ok=True,
    )
    print("Embedded Python installed successfully.")


def install_MXU():
    # 检查 MXU 目录是否存在
    mxu_dir = working_dir / "MXU"
    if not mxu_dir.exists():
        print("Warning: MXU directory not found. Skipping MXU installation.")
        return

    # 根据操作系统确定可执行文件名和扩展名
    if os.name == "nt":  # Windows
        mxu_exe_name = "mxu.exe"
        install_exe_name = "MaaGF2Exilium.exe"
    else:  # Unix/Linux
        mxu_exe_name = "mxu"
        install_exe_name = "MaaGF2Exilium"

    # 只复制运行需要的东西：
    #   mxu.pdb 是 MXU 的调试符号，win 包内解压后近 300MB，纯属负担
    #   README.md / LICENSE 是 MXU 自己的，留着会覆盖 install_chores() 放的项目文档
    shutil.copytree(
        mxu_dir,
        install_path,
        ignore=shutil.ignore_patterns("*.pdb", "README.md", "LICENSE"),
        dirs_exist_ok=True,
    )

    exe_src = install_path / mxu_exe_name
    if not exe_src.exists():
        print(f"Warning: {mxu_exe_name} not found in {mxu_dir}.")
        return

    exe_dst = install_path / install_exe_name
    exe_src.replace(exe_dst)

    # Unix 上要确保可执行权限（解压出来的位可能丢失）
    if os.name != "nt":
        os.chmod(exe_dst, 0o755)

    print(f"Copied MXU to {install_path}, with {mxu_exe_name} renamed to {install_exe_name}")


if __name__ == "__main__":
    install_resource()
    install_deps()
    install_chores()
    install_agent()
    install_python()
    install_MXU()

    print(f"Install to {install_path} successfully.")