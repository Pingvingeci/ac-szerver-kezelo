"""Pályák, autók és időjárások beolvasása, valamint a szerver tartalmának előkészítése ("pack")."""
from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

# Ezzel jelöljük a szerver mappájában azt a tartalmat, amit mi másoltunk be (modok).
PACK_MARKER = ".acszk_packed"
SKIP_TRACK_SUBDIRS = {"ui", "skins", "data", "ai", "extension", "texture", "textures", "sfx"}


def load_ui_json(path: Path) -> dict:
    """Az AC ui_*.json fájljai gyakran nem szabványosak (sortörés a szövegben, vessző a végén)."""
    try:
        raw = path.read_bytes()
    except OSError:
        return {}
    text = None
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        return {}
    for candidate in (text, re.sub(r",\s*([}\]])", r"\1", text)):
        try:
            data = json.loads(candidate, strict=False)
            if isinstance(data, dict):
                return data
        except ValueError:
            pass
    data = {}
    for key in ("name", "brand", "pitboxes", "length", "country"):
        m = re.search(r'"%s"\s*:\s*"([^"]*)"' % key, text)
        if m:
            data[key] = m.group(1)
    return data


def _to_int(value) -> int | None:
    m = re.search(r"\d+", str(value or ""))
    return int(m.group()) if m else None


@dataclass
class TrackLayout:
    track_id: str
    layout: str  # "" ha a pályának nincs külön layoutja
    name: str
    pitboxes: int | None
    length: str
    country: str
    preview: Path | None
    is_mod: bool

    @property
    def key(self) -> str:
        return f"{self.track_id}|{self.layout}"


@dataclass
class Car:
    car_id: str
    name: str
    brand: str
    skins: list[str] = field(default_factory=list)
    is_mod: bool = False


def _is_official(server_dir: Path | None, kind: str, item_id: str) -> bool:
    """A Kunos szerver eszköz a gyári tartalmat előre tartalmazza; amit mi másolunk be, azt megjelöljük."""
    if server_dir is None:
        return item_id.startswith("ks_")
    d = server_dir / "content" / kind / item_id
    return d.is_dir() and not (d / PACK_MARKER).exists()


def scan_tracks(ac: Path, server_dir: Path | None) -> list[TrackLayout]:
    result: list[TrackLayout] = []
    tracks_dir = ac / "content" / "tracks"
    for tdir in sorted(tracks_dir.iterdir(), key=lambda p: p.name.lower()):
        if not tdir.is_dir():
            continue
        tid = tdir.name
        is_mod = not _is_official(server_dir, "tracks", tid)
        ui = tdir / "ui"
        layouts: list[tuple[str, Path]] = []
        if ui.is_dir():
            for sub in sorted(ui.iterdir()):
                if sub.is_dir() and (sub / "ui_track.json").is_file() and (tdir / sub.name).is_dir():
                    layouts.append((sub.name, sub))
            if (ui / "ui_track.json").is_file() and (not layouts or (tdir / "data").is_dir()):
                layouts.insert(0, ("", ui))
        if not layouts:
            if (tdir / "data").is_dir():
                layouts.append(("", ui))
            else:
                continue
        for layout, uidir in layouts:
            info = load_ui_json(uidir / "ui_track.json")
            name = str(info.get("name") or tid).strip()
            preview = uidir / "preview.png"
            result.append(
                TrackLayout(
                    track_id=tid,
                    layout=layout,
                    name=name,
                    pitboxes=_to_int(info.get("pitboxes")),
                    length=str(info.get("length") or ""),
                    country=str(info.get("country") or ""),
                    preview=preview if preview.is_file() else None,
                    is_mod=is_mod,
                )
            )
    return result


def scan_cars(ac: Path, server_dir: Path | None) -> list[Car]:
    cars: list[Car] = []
    for cdir in sorted((ac / "content" / "cars").iterdir(), key=lambda p: p.name.lower()):
        if not cdir.is_dir():
            continue
        # Adat nélküli autó (pl. meg nem vásárolt DLC) nem használható szerveren
        if not (cdir / "data.acd").is_file() and not (cdir / "data").is_dir():
            continue
        info = load_ui_json(cdir / "ui" / "ui_car.json")
        skins_dir = cdir / "skins"
        skins = sorted(p.name for p in skins_dir.iterdir() if p.is_dir()) if skins_dir.is_dir() else []
        cars.append(
            Car(
                car_id=cdir.name,
                name=str(info.get("name") or cdir.name).strip(),
                brand=str(info.get("brand") or "").strip(),
                skins=skins,
                is_mod=not _is_official(server_dir, "cars", cdir.name),
            )
        )
    return cars


def scan_weathers(ac: Path) -> list[str]:
    wdir = ac / "content" / "weather"
    if not wdir.is_dir():
        return ["3_clear"]
    names = sorted(p.name for p in wdir.iterdir() if p.is_dir())
    return names or ["3_clear"]


# ---------------------------------------------------------------- pack

def _copy_if_needed(src: Path, dst: Path, only_missing: bool = False) -> bool:
    if dst.is_file():
        if only_missing:
            return False
        s, d = src.stat(), dst.stat()
        if s.st_size == d.st_size and int(s.st_mtime) == int(d.st_mtime):
            return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def pack_track(ac: Path, server_dir: Path, track_id: str, layout: str, log: Callable[[str], None]) -> None:
    src = ac / "content" / "tracks" / track_id
    dst = server_dir / "content" / "tracks" / track_id
    official = _is_official(server_dir, "tracks", track_id)
    copied = 0
    for f in src.glob("models*.ini"):
        copied += _copy_if_needed(f, dst / f.name, official)
    if (src / "data").is_dir():
        for f in (src / "data").glob("*.ini"):
            copied += _copy_if_needed(f, dst / "data" / f.name, official)
    for sub in src.iterdir():
        if sub.is_dir() and sub.name.lower() not in SKIP_TRACK_SUBDIRS and (sub / "data").is_dir():
            for f in (sub / "data").glob("*.ini"):
                copied += _copy_if_needed(f, dst / sub.name / "data" / f.name, official)
    surfaces = dst / layout / "data" / "surfaces.ini" if layout else dst / "data" / "surfaces.ini"
    if not surfaces.is_file():
        raise RuntimeError(
            f"A(z) „{track_id}” pályához nem található surfaces.ini"
            f"{' (layout: ' + layout + ')' if layout else ''}. A pálya valószínűleg hibásan van telepítve."
        )
    if not official:
        (dst / PACK_MARKER).touch()
    if copied:
        log(f"Pálya adatai bemásolva a szerverhez: {track_id} ({copied} fájl)")


def pack_car(ac: Path, server_dir: Path, car_id: str, log: Callable[[str], None]) -> None:
    src = ac / "content" / "cars" / car_id
    dst = server_dir / "content" / "cars" / car_id
    official = _is_official(server_dir, "cars", car_id)
    copied = 0
    if (src / "data.acd").is_file():
        copied += _copy_if_needed(src / "data.acd", dst / "data.acd", official)
    elif (src / "data").is_dir():
        for f in (src / "data").rglob("*"):
            if f.is_file():
                copied += _copy_if_needed(f, dst / "data" / f.relative_to(src / "data"), official)
    else:
        raise RuntimeError(f"A(z) „{car_id}” autónak nincs adata (data.acd vagy data mappa).")
    if not official:
        (dst / PACK_MARKER).touch()
    if copied:
        log(f"Autó adatai bemásolva a szerverhez: {car_id}")
