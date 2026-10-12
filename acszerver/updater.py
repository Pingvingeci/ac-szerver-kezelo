"""Frissítések keresése és telepítése a GitHub Releases alapján.

Egy kiadásban két fájl van: a telepítő (`AC_Szerver_Kezelo_Setup_<verzió>.exe`) és
az ellenőrzőösszege (`...exe.sha256`). Letöltés után a SHA-256 ellenőrzése kötelező,
csak egyező fájlt futtatunk.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

from .version import GITHUB_REPO, __version__

API_LATEST = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
_UA = {"User-Agent": f"ACSzerverKezelo/{__version__}", "Accept": "application/vnd.github+json"}


class UpdateError(Exception):
    pass


def parse_version(v: str) -> tuple[int, ...]:
    nums = re.findall(r"\d+", v or "")
    return tuple(int(n) for n in nums[:3]) or (0,)


def check() -> dict | None:
    """Ha van újabb kiadás, visszaadja az adatait, különben None."""
    if GITHUB_REPO.startswith("OWNER/"):
        return None
    req = urllib.request.Request(API_LATEST, headers=_UA)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            rel = json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:  # még nincs kiadás
            return None
        raise UpdateError(f"A GitHub nem válaszolt ({e.code}).") from None
    except (OSError, ValueError) as e:
        raise UpdateError(f"Nem sikerült frissítést keresni: {e}") from None
    latest = rel.get("tag_name", "")
    if parse_version(latest) <= parse_version(__version__):
        return None
    assets = {a["name"]: a["browser_download_url"] for a in rel.get("assets", [])}
    setup = next((n for n in assets if n.lower().endswith(".exe") and "setup" in n.lower()), None)
    if not setup or f"{setup}.sha256" not in assets:
        return None  # hiányos kiadás – nem ajánljuk fel
    return {
        "version": latest.lstrip("v"),
        "current": __version__,
        "notes": rel.get("body") or "",
        "url": rel.get("html_url", ""),
        "setup_name": setup,
        "setup_url": assets[setup],
        "sha_url": assets[f"{setup}.sha256"],
    }


def cleanup_old_downloads() -> None:
    """A korábbi frissítésekhez letöltött telepítők törlése (induláskor hívjuk)."""
    for d in Path(tempfile.gettempdir()).glob("acszk_update_*"):
        shutil.rmtree(d, ignore_errors=True)


def _download(url: str, dest: Path, progress: Callable[[float], None] | None = None) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": _UA["User-Agent"]})
    with urllib.request.urlopen(req, timeout=30) as r, open(dest, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        while chunk := r.read(256 * 1024):
            f.write(chunk)
            done += len(chunk)
            if progress and total:
                progress(done / total)


def download_and_install(info: dict, progress: Callable[[float], None] | None = None) -> None:
    """Letölti és ellenőrzi a telepítőt, majd elindítja csendes módban. A hívó ezután zárja be a programot."""
    folder = Path(tempfile.mkdtemp(prefix="acszk_update_"))
    setup = folder / info["setup_name"]
    try:
        _download(info["setup_url"], setup, progress)
        sha_req = urllib.request.Request(info["sha_url"], headers={"User-Agent": _UA["User-Agent"]})
        with urllib.request.urlopen(sha_req, timeout=15) as r:
            expected = r.read().decode("ascii", errors="replace").split()[0].strip().lower()
    except OSError as e:
        raise UpdateError(f"A letöltés nem sikerült: {e}") from None
    actual = hashlib.sha256(setup.read_bytes()).hexdigest()
    if actual != expected:
        setup.unlink(missing_ok=True)
        raise UpdateError("A letöltött fájl ellenőrzése nem sikerült (eltérő ellenőrzőösszeg). Nem telepítem.")
    if not getattr(sys, "frozen", False):
        raise UpdateError(f"Fejlesztői módban nem telepítek. A letöltött telepítő: {setup}")
    # /SILENT: csak egy folyamatjelzőt mutat; a telepítő a végén újraindítja a programot
    subprocess.Popen([str(setup), "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CLOSEAPPLICATIONS"], close_fds=True)
