"""Checks every application's pods.yml against what Pods reads, and against its Quadlet files.

Run from the repository root: python3 .github/scripts/check-manifests.py
"""

import pathlib
import re
import sys

import yaml

QUADLET_EXTENSIONS = {".container", ".pod", ".volume", ".network", ".kube", ".image", ".build"}
REQUIRED_KEYS = ["name", "label", "description", "author", "icon", "category"]
NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
ICON = re.compile(r"^i-[a-z0-9]+(-[a-z0-9]+)+$")
URL = re.compile(r"^https?://\S+$")
SECRET = re.compile(r"^Secret=([^,\s]+)", re.MULTILINE)


def quadlet_files(directory: pathlib.Path) -> list[pathlib.Path]:
    return sorted(path for path in directory.iterdir() if path.is_file() and path.suffix in QUADLET_EXTENSIONS)


def check(directory: pathlib.Path) -> list[str]:
    errors = []
    manifest = yaml.safe_load((directory / "pods.yml").read_text())

    if not isinstance(manifest, dict):
        return ["pods.yml has no keys"]

    if manifest.get("version") != 1:
        errors.append("version must be 1")

    for key in REQUIRED_KEYS:
        if not isinstance(manifest.get(key), str) or not manifest[key].strip():
            errors.append(f"{key} is required")

    if manifest.get("name") != directory.name:
        errors.append(f"name must be the directory's name, {directory.name}")

    if isinstance(manifest.get("name"), str) and not NAME.match(manifest["name"]):
        errors.append("name isn't a valid application name")

    if isinstance(manifest.get("icon"), str) and not ICON.match(manifest["icon"]):
        errors.append("icon must be an Iconify name such as i-lucide-database")

    for key in ["website", "repository"]:
        if key in manifest and not URL.match(str(manifest[key])):
            errors.append(f"{key} must be an http(s) URL")

    sources = manifest.get("sources") or {}
    directories = [directory / str(source.get("path", "")) for source in sources.values()] or [directory]

    for name, source in sources.items():
        path = directory / str(source.get("path", ""))

        if not path.is_dir() or ".." in str(source.get("path", "")):
            errors.append(f"source {name}: {source.get('path')} isn't a directory next to pods.yml")

    declared = set((manifest.get("secrets") or {}).keys())

    for path in directories:
        files = quadlet_files(path) if path.is_dir() else []

        if not files:
            errors.append(f"{path.relative_to(directory.parent)} has no Quadlet files")

        for file in files:
            for secret in SECRET.findall(file.read_text()):
                if secret not in declared:
                    errors.append(f"{file.relative_to(directory.parent)} uses secret {secret}, which pods.yml doesn't describe")

    return errors


def main() -> int:
    failed = False

    for manifest in sorted(pathlib.Path(".").glob("*/pods.yml")):
        errors = check(manifest.parent)

        for error in errors:
            print(f"::error file={manifest}::{manifest.parent.name}: {error}")

        failed = failed or bool(errors)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
