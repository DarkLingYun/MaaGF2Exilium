"""Build latest MaaFramework and matching Android Python runtimes.

Run with Python >=3.11, pip and uv installed. Agent dependencies come from
pyproject.toml's project.dependencies; desktop requirements.txt supplies version
preferences, not extra packages. Explicit Android exceptions belong in
tool.maagf2exilium.android.overrides. Generated resolution files stay in .maafw/.
"""

import argparse
import json
import runpy
import shutil
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path

try:
    from packaging.requirements import Requirement
    from packaging.utils import canonicalize_name
except ImportError:
    from pip._vendor.packaging.requirements import Requirement
    from pip._vendor.packaging.utils import canonicalize_name


ROOT = Path(__file__).resolve().parents[1]
PLATFORMS = {"arm64-v8a": "aarch64-linux-android", "x86_64": "x86_64-linux-android"}
# Chaquopy release numbers are independent of CPython versions (same mapping as M9A).
CHAQUOPY_INDEXES = {"3.13": "https://chaquo.com/pypi-13.1/"}


def validate_core(bundle, abi, python_version, framework_version):
    manifest = json.loads((bundle / "agent-core.json").read_text(encoding="utf-8"))
    if (manifest.get("abi") != abi or manifest.get("python") != python_version
            or manifest.get("provides", {}).get("maafw") != framework_version):
        raise ValueError(f"Android agent core does not match MaaFramework {framework_version} / {abi}")
    if not (bundle / "bin" / "python3").is_file():
        raise FileNotFoundError(f"Missing Android Python executable for {abi}")
    return manifest


def core_metadata(manifest, directory):
    """Describe already-bundled packages to the resolver, including transitive constraints.

    These metadata-only wheels are NEVER installed. Core packages have no Android
    PyPI wheel in some cases (notably maa); their authoritative versions come from
    the downloaded core manifest. The core already contains their own dependencies.
    """
    requirements = []
    for name, version in manifest["provides"].items():
        stem = f"{canonicalize_name(name).replace('-', '_')}-{version}"
        wheel = directory / f"{stem}-py3-none-any.whl"
        with zipfile.ZipFile(wheel, "w") as archive:
            archive.writestr(f"{stem}.dist-info/METADATA",
                             f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n")
            archive.writestr(f"{stem}.dist-info/WHEEL",
                             "Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n")
            archive.writestr(f"{stem}.dist-info/RECORD", "")
        requirements.append(f"{name} @ {wheel.as_uri()}")
    return requirements


def resolve_dependencies(root, manifest, abi, directory):
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = project["project"]["dependencies"]
    overrides = project.get("tool", {}).get("maagf2exilium", {}).get("android", {}).get("overrides", [])
    provided = {canonicalize_name(name) for name in manifest["provides"]}
    for entry in overrides:
        requirement = Requirement(entry)
        if (canonicalize_name(requirement.name) in provided or not requirement.specifier
                or requirement.url or requirement.marker or requirement.extras):
            raise ValueError(f"Invalid Android override {entry!r}: use a version constraint for a non-core package")
    minor = ".".join(manifest["python"].split(".")[:2])
    if minor not in CHAQUOPY_INDEXES:
        raise ValueError(f"Add a verified Chaquopy index for CPython {minor} before building")
    index = CHAQUOPY_INDEXES[minor]
    directory.mkdir(parents=True, exist_ok=True)
    inputs = directory / "requirements.in"
    inputs.write_text("\n".join([*dependencies, *core_metadata(manifest, directory)]) + "\n", encoding="utf-8")
    exceptions = directory / "overrides.txt"
    exceptions.write_text("\n".join(overrides) + "\n", encoding="utf-8")
    resolved = directory / "resolved.txt"
    # uv treats an existing output file as preferences: dev-only packages aren't
    # roots, and a desktop pin cannot force an incompatible Android wheel/version.
    desktop = root / "requirements.txt"
    resolved.write_text(desktop.read_text(encoding="utf-8") if desktop.exists() else "", encoding="utf-8")
    try:
        subprocess.run([
            "uv", "pip", "compile", str(inputs), "--no-config", "--no-header", "--no-annotate",
            "--python-version", manifest["python"], "--python-platform", PLATFORMS[abi],
            "--only-binary", ":all:", "--index", index,
            "--index", "https://chaquo.com/pypi-upstream/", "--default-index", "https://pypi.org/simple",
            *(["--overrides", str(exceptions)] if overrides else []),
            "--output-file", str(resolved),
        ], cwd=root, check=True)
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            f"Cannot resolve Android dependencies for {abi}. Check the error above, shared "
            "project.dependencies and tool.maagf2exilium.android.overrides; no automatic out-of-range downgrade."
        ) from error
    # Install the complete resolved closure with --no-deps, so pip cannot resolve
    # markers against the build host or overwrite the core with desktop wheels.
    packages = []
    for line in resolved.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            if canonicalize_name(Requirement(line).name) not in provided:
                packages.append(line)
    requirements = directory / "requirements.txt"
    requirements.write_text("".join(f"{package}\n" for package in packages), encoding="utf-8")
    print(f"Android {abi} dependencies: {', '.join(packages) or '(core only)'}", flush=True)
    return requirements, index


def build_runtime(abis, root=ROOT):
    if not abis or len(set(abis)) != len(abis) or not set(abis) <= PLATFORMS.keys():
        raise ValueError("abis must contain arm64-v8a and/or x86_64, without duplicates")
    frontend = root / "Android" / "MaaFwApp"
    builder = frontend / "scripts" / "build_agent_bundle.py"
    output = root / "Android" / "agent-dist"
    # Remove stale ABIs when switching from a universal to a single-ABI APK.
    if output.is_symlink() or output.resolve().parent != (root / "Android").resolve():
        raise ValueError("Android agent-dist must stay inside the project")
    if output.exists():
        shutil.rmtree(output)

    # Resolve latest once; force deployment because the downloader's fast path
    # compares file sizes, which cannot distinguish equal-sized library versions.
    subprocess.run([
        sys.executable, str(frontend / "scripts" / "setup_maa_framework.py"),
        "--force",
        "--abi", "all" if len(abis) == 2 else abis[0],
    ], cwd=frontend, check=True)
    version = (frontend / ".maafwversion").read_text(encoding="utf-8").strip().removeprefix("v")
    helpers = runpy.run_path(str(builder))
    python_version = helpers["CORE_PY"]
    core_tag = f"{python_version}-maafw{version}"
    for abi in abis:
        try:
            core = helpers["fetch_core"](abi, helpers["CORE_REPO"], core_tag, helpers["WORK_DIR"])
        except OSError as error:
            raise RuntimeError(f"Cannot obtain agent core {core_tag} / {abi}; a matching release is required") from error
        manifest = validate_core(core, abi, python_version, version)
        requirements, index = resolve_dependencies(
            root, manifest, abi, helpers["WORK_DIR"] / "dependencies" / core_tag / abi)
        subprocess.run([
            sys.executable, str(builder), "--out", str(output), "--core-tag", core_tag, "--abi", abi,
            "--requirements", str(requirements), "--no-deps", "--extra-index-url", index,
        ], cwd=frontend, check=True)
        validate_core(output / abi / "bundle", abi, python_version, version)
    print(f"Verified MaaFramework {version} + agent core {core_tag}: {', '.join(abis)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--abis", default="arm64-v8a", help="Comma-separated APK ABIs")
    args = parser.parse_args()
    build_runtime(args.abis.split(","))
