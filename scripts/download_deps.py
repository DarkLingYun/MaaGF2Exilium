import os
import requests
import os
import zipfile
import tarfile
import platform
from tqdm import tqdm


def get_platform_and_arch():
    """
    获取当前平台和架构信息
    返回格式: (platform, arch)
    platform: win, osx, linux
    arch: x64, arm64
    """
    system = platform.system().lower()
    machine = platform.machine().lower()

    # 平台映射
    platform_mapping = {
        "windows": "win",
        "darwin": "osx",
        "linux": "linux",
    }

    # 架构映射
    arch_mapping = {
        "amd64": "x64",
        "x86_64": "x64",
        "aarch64": "arm64",
        "arm64": "arm64",
    }

    platform_name = platform_mapping.get(system, system)
    arch_name = arch_mapping.get(machine, machine)

    return platform_name, arch_name


def get_maa_framework_names(platform_name, arch_name):
    """
    获取 MaaFramework 的平台和架构名称
    MaaFramework 使用 macos/x86_64/aarch64 格式
    """
    # MaaFramework 平台映射
    maa_platform_mapping = {
        "win": "win",
        "osx": "macos",  # MaaFramework 使用 macos 而不是 osx
        "linux": "linux",
    }
    
    # MaaFramework 架构映射
    maa_arch_mapping = {
        "x64": "x86_64",   # MaaFramework 使用 x86_64 而不是 x64
        "arm64": "aarch64", # MaaFramework 使用 aarch64 而不是 arm64
    }
    
    maa_platform = maa_platform_mapping.get(platform_name, platform_name)
    maa_arch = maa_arch_mapping.get(arch_name, arch_name)
    
    return maa_platform, maa_arch


def extract_archive(file_path, output_path):
    """
    根据文件扩展名自动选择解压方式
    支持 .zip, .tar.gz, .tar 格式
    """
    filename = os.path.basename(file_path)
    
    try:
        if filename.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                with tqdm(total=len(file_list), desc="Extracting", unit="files") as pbar:
                    for file in file_list:
                        zip_ref.extract(file, output_path)
                        pbar.update(1)
        
        elif filename.endswith('.tar.gz') or filename.endswith('.tgz'):
            with tarfile.open(file_path, 'r:gz') as tar_ref:
                file_list = tar_ref.getnames()
                with tqdm(total=len(file_list), desc="Extracting", unit="files") as pbar:
                    for member in tar_ref:
                        tar_ref.extract(member, output_path, filter='data')
                        pbar.update(1)
        
        elif filename.endswith('.tar'):
            with tarfile.open(file_path, 'r') as tar_ref:
                file_list = tar_ref.getnames()
                with tqdm(total=len(file_list), desc="Extracting", unit="files") as pbar:
                    for member in tar_ref:
                        tar_ref.extract(member, output_path, filter='data')
                        pbar.update(1)
        
        else:
            raise Exception(f"Unsupported archive format: {filename}")
            
        print(f"Successfully extracted {filename}")
        
    except Exception as e:
        raise Exception(f"Failed to extract {filename}: {e}")


def download_maa_framework(platform_name, arch_name, output_path="deps"):
    """
    下载 MaaFramework 的最新版本

    参数:
    platform_name: 平台名称 (win, osx, linux)
    arch_name: 架构名称 (x64, arm64)
    output_path: 输出目录
    """
    # 创建输出目录
    os.makedirs(output_path, exist_ok=True)

    # GitHub API 地址
    api_url = "https://api.github.com/repos/MaaXYZ/MaaFramework/releases/latest"

    try:
        # 获取最新版本信息
        response = requests.get(api_url)
        response.raise_for_status()
        release_data = response.json()

        # 获取 MaaFramework 特定的平台和架构名称
        maa_platform, maa_arch = get_maa_framework_names(platform_name, arch_name)
        
        # 构建平台特定的文件名模式 (格式: MAA-{platform}-{arch}-v{version}.zip)
        pattern = f"-{maa_platform}-{maa_arch}-"

        matching_assets = [
            asset
            for asset in release_data["assets"]
            if asset["name"].startswith("MAA-") and pattern in asset["name"] and asset["name"].endswith(".zip")
        ]

        if not matching_assets:
            # 列出所有可用的资产进行调试
            available_assets = [asset["name"] for asset in release_data["assets"] if asset["name"].startswith("MAA-")]
            raise Exception(
                f"No matching MaaFramework assets found for platform: {maa_platform}-{maa_arch}. "
                f"Available assets: {', '.join(available_assets)}"
            )

        asset = matching_assets[0]
        download_url = asset["browser_download_url"]
        filename = asset["name"]
        file_size = asset["size"]

        # 下载文件
        response = requests.get(download_url, stream=True)
        response.raise_for_status()

        file_path = os.path.join(output_path, filename)
        with open(file_path, "wb") as f:
            with tqdm(
                total=file_size,
                unit="iB",
                unit_scale=True,
                unit_divisor=1024,
                desc=filename,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    size = f.write(chunk)
                    pbar.update(size)

        # 解压文件，然后删除压缩包
        extract_archive(file_path, output_path)
        os.remove(file_path)

    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
    except Exception as e:
        print(f"Error: {e}")


def download_mfa_avalonia(platform_name, arch_name, output_path="MFA"):
    """
    下载 MFAAvalonia的最新版本（跨平台Avalonia版本）

    参数:
    platform_name: 平台名称 (win, osx, linux)
    arch_name: 架构名称 (x64, arm64)
    output_path: 输出目录
    """
    # 创建输出目录
    os.makedirs(output_path, exist_ok=True)

    # GitHub API 地址
    api_url = "https://api.github.com/repos/SweetSmellFox/MFAAvalonia/releases/latest"

    try:
        # 获取最新版本信息
        response = requests.get(api_url)
        response.raise_for_status()
        release_data = response.json()

        # 构建平台特定的文件名模式 (匹配格式: MFAAvalonia-v1.6.5-osx-x64.tar.gz)
        pattern = f"-{platform_name}-{arch_name}"

        matching_assets = [
            asset
            for asset in release_data["assets"]
            if asset["name"].startswith("MFAAvalonia-") and pattern in asset["name"] and (asset["name"].endswith(".tar.gz") or asset["name"].endswith(".zip"))
        ]

        if not matching_assets:
            # 列出所有可用的资产进行调试
            available_assets = [asset["name"] for asset in release_data["assets"] if asset["name"].startswith("MFAAvalonia-")]
            raise Exception(
                f"No matching MFAAvalonia assets found for platform: {platform_name}-{arch_name}. "
                f"Available assets: {', '.join(available_assets)}"
            )

        asset = matching_assets[0]
        download_url = asset["browser_download_url"]
        filename = asset["name"]
        file_size = asset["size"]

        # 下载文件
        response = requests.get(download_url, stream=True)
        response.raise_for_status()

        file_path = os.path.join(output_path, filename)
        with open(file_path, "wb") as f:
            with tqdm(
                total=file_size,
                unit="iB",
                unit_scale=True,
                unit_divisor=1024,
                desc=filename,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    size = f.write(chunk)
                    pbar.update(size)

        # 解压文件，然后删除压缩包
        extract_archive(file_path, output_path)
        os.remove(file_path)

    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    platform_name, arch_name = get_platform_and_arch()

    print(f"检测到平台: {platform_name}, 架构: {arch_name}")

    # 检查是否支持该平台和架构组合
    supported_combinations = [
        ("win", "x64"),
        ("win", "arm64"),
        ("osx", "x64"),
        ("osx", "arm64"),
        ("linux", "x64"),
        ("linux", "arm64"),
    ]

    if (platform_name, arch_name) not in supported_combinations:
        print(f"不支持的平台和架构组合: {platform_name}-{arch_name}")
        print(
            f"支持的组合: {', '.join([f'{p}-{a}' for p, a in supported_combinations])}"
        )
        exit(1)

    try:
        # 下载 MaaFramework
        print("下载 MaaFramework...")
        download_maa_framework(platform_name, arch_name)
        
        # 下载 MFAAvalonia
        print("下载 MFAAvalonia...")
        download_mfa_avalonia(platform_name, arch_name)

        print("下载完成！")
    except Exception as e:
        print(f"下载失败: {e}")
        exit(1)
