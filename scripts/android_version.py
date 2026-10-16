"""Resolve an updater-compatible APK version, including repositories without tags."""

import argparse
import os
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEMVER = re.compile(
    r"v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
)


def parse_version(value):
    match = SEMVER.fullmatch(value)
    if match and match[4]:
        if any(part.isdigit() and len(part) > 1 and part.startswith("0") for part in match[4].split(".")):
            return None
    return match


def version_from_describe(describe, commit_count):
    described = re.fullmatch(r"(.+)-(\d+)-g([0-9a-f]+)", describe)
    if described:
        tag, distance, sha = described.groups()
        version = parse_version(tag)
        if version:
            major, minor, patch, prerelease, _ = version.groups()
            if int(distance) == 0:
                return tag.removeprefix("v")
            if prerelease:
                return f"{major}.{minor}.{patch}-{prerelease}.dev.{distance}+g{sha}"
            return f"{major}.{minor}.{int(patch) + 1}-dev.{distance}+g{sha}"
    version = parse_version(describe)
    if version:
        return describe.removeprefix("v")
    if not re.fullmatch(r"[0-9a-f]+", describe):
        raise ValueError(f"Unexpected git version: {describe}")
    return f"0.0.0-dev.{int(commit_count)}+g{describe}"


def resolve_version(explicit=""):
    if explicit:
        if not parse_version(explicit):
            raise ValueError(f"Android version must be SemVer, got {explicit!r}")
        return explicit.removeprefix("v")
    describe = subprocess.check_output(
        ["git", "describe", "--tags", "--match", "v[0-9]*", "--long", "--always"],
        cwd=ROOT, text=True,
    ).strip()
    count = subprocess.check_output(["git", "rev-list", "--count", "HEAD"], cwd=ROOT, text=True).strip()
    return version_from_describe(describe, count)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="")
    parser.add_argument("--github-env", action="store_true")
    args = parser.parse_args()
    version = resolve_version(args.version)
    print(version)
    if args.github_env:
        with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as output:
            output.write(f"VERSION={version}\nBUILD_VERSION_NAME={version}\n")
