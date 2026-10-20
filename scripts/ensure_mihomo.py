#!/usr/bin/env python3
"""Install the latest stable official mihomo release on demand."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

API_URL = "https://api.github.com/repos/MetaCubeX/mihomo/releases/latest"
USER_AGENT = "codex-mihomo-skill/1.0"
DEFAULT_MIRROR = "https://gh-proxy.com/"
DATA_DIR = Path(__file__).resolve().parents[1] / ".mihomo"


class MihomoError(RuntimeError):
    """An expected install or platform error."""


def current_platform() -> tuple[str, str]:
    systems = {"Darwin": "darwin", "Linux": "linux", "Windows": "windows"}
    machines = {
        "x86_64": "amd64", "amd64": "amd64", "i386": "386", "i686": "386",
        "aarch64": "arm64", "arm64": "arm64", "armv7l": "armv7", "armv7": "armv7",
    }
    system = systems.get(platform.system())
    machine = machines.get(platform.machine().lower())
    if not system or not machine:
        raise MihomoError(f"Unsupported platform: system={platform.system()!r}, architecture={platform.machine()!r}")
    return system, machine


def core_path(system: str, architecture: str) -> Path:
    name = "mihomo.exe" if system == "windows" else "mihomo"
    return DATA_DIR / "bin" / f"{system}-{architecture}" / name


def fetch_latest_release() -> dict:
    request = urllib.request.Request(API_URL, headers={"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise MihomoError(f"Could not retrieve the latest mihomo release: {exc}") from exc


def asset_candidates(system: str, architecture: str, tag: str) -> list[str]:
    extension = "zip" if system == "windows" else "gz"
    architecture_names = [architecture] + (["arm64-v8"] if architecture == "arm64" else [])
    candidates = []
    for arch_name in architecture_names:
        candidates.extend([
            f"mihomo-{system}-{arch_name}-{tag}.{extension}",
            f"mihomo-{system}-{arch_name}-compatible-{tag}.{extension}",
            f"mihomo-{system}-{arch_name}-v1-{tag}.{extension}",
        ])
    return candidates


def choose_asset(release: dict, system: str, architecture: str) -> dict:
    tag = release.get("tag_name")
    if not isinstance(tag, str) or not tag:
        raise MihomoError("Latest release metadata did not include a tag name")
    assets = {asset.get("name"): asset for asset in release.get("assets", [])}
    for candidate in asset_candidates(system, architecture, tag):
        if candidate in assets:
            return assets[candidate]
    available = ", ".join(sorted(name for name in assets if isinstance(name, str)))
    raise MihomoError(f"No official stable mihomo asset matches {system}-{architecture} for {tag}. Available assets: {available}")


def download_and_verify(asset: dict, tag: str, destination: Path, mirror: str | None) -> None:
    direct_url, digest = asset.get("browser_download_url"), asset.get("digest")
    if not isinstance(direct_url, str) or not direct_url:
        raise MihomoError("The selected release asset has no download URL")
    if not isinstance(digest, str) or not digest.startswith("sha256:"):
        raise MihomoError("The selected release asset has no SHA-256 digest to verify")
    expected, digestor = digest.removeprefix("sha256:").lower(), hashlib.sha256()
    name = str(asset.get("name", "mihomo asset"))
    urls = []
    if mirror:
        official_path = f"https://github.com/MetaCubeX/mihomo/releases/download/{tag}/{name}"
        urls.append((mirror.rstrip("/") + "/" + official_path, "mirror"))
    urls.append((direct_url, "official release"))
    last_error = None
    for url, source in urls:
        digestor = hashlib.sha256()
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
                    digestor.update(chunk)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError) as exc:
            destination.unlink(missing_ok=True)
            last_error = exc
            if source == "mirror":
                print("mihomo installer: mirror download failed; retrying official release", file=sys.stderr)
                continue
            raise MihomoError(f"Could not download {name}: {exc}") from exc
        actual = digestor.hexdigest().lower()
        if actual != expected:
            destination.unlink(missing_ok=True)
            raise MihomoError(f"SHA-256 verification failed: expected {expected}, got {actual}")
        return
    raise MihomoError(f"Could not download {name}: {last_error}")


def extract_core(archive: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mihomo-extract-") as temp_dir:
        temporary_core = Path(temp_dir) / target.name
        if archive.suffix == ".gz":
            with gzip.open(archive, "rb") as source, temporary_core.open("wb") as output:
                shutil.copyfileobj(source, output)
        elif archive.suffix == ".zip":
            with zipfile.ZipFile(archive) as package:
                names = [name for name in package.namelist() if Path(name).name.lower() in {"mihomo", "mihomo.exe"}]
                if len(names) != 1:
                    raise MihomoError("The release archive does not contain exactly one mihomo executable")
                with package.open(names[0]) as source, temporary_core.open("wb") as output:
                    shutil.copyfileobj(source, output)
        else:
            raise MihomoError(f"Unsupported archive type: {archive.name}")
        temporary_core.chmod(temporary_core.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        os.replace(temporary_core, target)


def verify_core(path: Path) -> None:
    try:
        result = subprocess.run([str(path), "-v"], capture_output=True, text=True, timeout=15, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        raise MihomoError(f"Downloaded core could not be executed: {exc}") from exc
    if result.returncode != 0:
        raise MihomoError(f"Downloaded core failed its version check: {result.stderr.strip() or result.stdout.strip()}")


def ensure(force: bool, mirror: str | None) -> Path:
    system, architecture = current_platform()
    target = core_path(system, architecture)
    if target.exists() and not force:
        verify_core(target)
        return target
    release = fetch_latest_release()
    asset = choose_asset(release, system, architecture)
    with tempfile.TemporaryDirectory(prefix="mihomo-download-") as temp_dir:
        archive = Path(temp_dir) / str(asset["name"])
        download_and_verify(asset, str(release["tag_name"]), archive, mirror)
        extract_core(archive, target)
    verify_core(target)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ensure", action="store_true", help="Install if missing and print the executable path")
    parser.add_argument("--print-path", action="store_true", help="Print the expected executable path without downloading")
    parser.add_argument("--force", action="store_true", help="Replace an existing core with the latest stable release (requires --ensure)")
    parser.add_argument("--mirror", default=os.environ.get("MIHOMO_GITHUB_MIRROR", DEFAULT_MIRROR), help="Release mirror base URL; use an empty value with --direct to disable")
    parser.add_argument("--direct", action="store_true", help="Skip the default mirror and download directly from GitHub")
    args = parser.parse_args()
    if not args.ensure and not args.print_path:
        parser.error("choose --ensure or --print-path")
    if args.force and not args.ensure:
        parser.error("--force requires --ensure")
    try:
        if args.print_path:
            system, architecture = current_platform()
            print(core_path(system, architecture))
        if args.ensure:
            print(ensure(args.force, None if args.direct else args.mirror))
    except MihomoError as exc:
        print(f"mihomo installer error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
