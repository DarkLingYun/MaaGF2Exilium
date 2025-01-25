import os
import requests
import os
import zipfile
import re
import platform
from tqdm import tqdm


def get_architecture():
    arch = platform.machine().lower()
    arch_mapping = {
        "amd64": "x86_64",
        "x86_64": "x86_64",
        "aarch64": "aarch64",
        "arm64": "aarch64",
    }
    return arch_mapping.get(arch, arch)


def download_maa_framework(output_path="deps"):
    """
    下载 MaaFramework 的最新版本

    参数:
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

        # 查找匹配的资源文件
        pattern = f"MAA-win-x86_64"
        matching_assets = [
            asset for asset in release_data["assets"] if pattern in asset["name"]
        ]

        if not matching_assets:
            raise Exception(f"No matching assets found for: MAA-win-x86_64")

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
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            file_list = zip_ref.namelist()
            with tqdm(total=len(file_list), desc="Extracting", unit="files") as pbar:
                for file in file_list:
                    zip_ref.extract(file, output_path)
                    pbar.update(1)
        os.remove(file_path)

    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
    except Exception as e:
        print(f"Error: {e}")


def download_mfa_wpf(output_path="MFA"):
    """
    下载 MFAWPF的最新版本

    参数:
    output_path: 输出目录
    """
    # 创建输出目录
    os.makedirs(output_path, exist_ok=True)

    # GitHub API 地址
    api_url = "https://api.github.com/repos/SweetSmellFox/MFAWPF/releases/latest"

    try:
        # 获取最新版本信息
        response = requests.get(api_url)
        response.raise_for_status()
        release_data = response.json()

        # 查找匹配的资源文件
        pattern = f"MFAWPF"
        matching_assets = [
            asset for asset in release_data["assets"] if pattern in asset["name"]
        ]

        if not matching_assets:
            raise Exception(f"No matching assets found for: MFAWPF")

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
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            file_list = zip_ref.namelist()
            with tqdm(total=len(file_list), desc="Extracting", unit="files") as pbar:
                for file in file_list:
                    zip_ref.extract(file, output_path)
                    pbar.update(1)
        os.remove(file_path)

    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    arch = get_architecture()
    if os.name == "nt" and arch == "x86_64":
        download_maa_framework()
        download_mfa_wpf()
    else:
        print("当前系统不是 x86_64 的 Windows 系统，请等待后续开发")
