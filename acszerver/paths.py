"""Assetto Corsa és a dedikált szerver megkeresése a gépen."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

APP_NAME = "ACSzerverKezelo"


def app_data_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home())
    d = Path(base) / APP_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


CONFIG_FILE = app_data_dir() / "config.json"


def load_app_config() -> dict:
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_app_config(cfg: dict) -> None:
    try:
        CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


def _steam_roots() -> list[Path]:
    roots: list[Path] = []
    try:
        import winreg

        for hive, key, value in (
            (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam", "InstallPath"),
        ):
            try:
                with winreg.OpenKey(hive, key) as k:
                    roots.append(Path(winreg.QueryValueEx(k, value)[0]))
            except OSError:
                pass
    except ImportError:
        pass
    roots += [Path(r"C:\Program Files (x86)\Steam"), Path(r"C:\Program Files\Steam")]
    return roots


def steam_libraries() -> list[Path]:
    libs: list[Path] = []
    for root in _steam_roots():
        if not root.is_dir():
            continue
        libs.append(root)
        vdf = root / "steamapps" / "libraryfolders.vdf"
        try:
            text = vdf.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in re.finditer(r'"path"\s+"(.+?)"', text):
            libs.append(Path(m.group(1).replace("\\\\", "\\")))
    # Duplikátumok kiszűrése, sorrend megtartásával
    seen, out = set(), []
    for lib in libs:
        key = str(lib).lower().rstrip("\\/")
        if key not in seen:
            seen.add(key)
            out.append(lib)
    return out


def is_ac_folder(p: Path) -> bool:
    return (p / "content" / "cars").is_dir() and (p / "content" / "tracks").is_dir()


def find_ac_folder() -> Path | None:
    for lib in steam_libraries():
        p = lib / "steamapps" / "common" / "assettocorsa"
        if is_ac_folder(p):
            return Path(os.path.realpath(p))
    return None


def find_server_folder(ac: Path) -> Path | None:
    """A mappát adja vissza, amelyben az acServer.exe van."""
    candidates = [ac / "server"]
    for lib in steam_libraries():
        ds = lib / "steamapps" / "common" / "Assetto Corsa Dedicated Server"
        candidates += [ds / "server", ds]
    for c in candidates:
        if (c / "acServer.exe").is_file():
            return c
    return None
