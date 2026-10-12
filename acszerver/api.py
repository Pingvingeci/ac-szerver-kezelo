"""A webes felület és a Python háttér közötti híd (pywebview js_api).

A pywebview csak a nem aláhúzással kezdődő metódusokat teszi elérhetővé a JavaScript számára.
"""
from __future__ import annotations

import base64
import ctypes
import io
import ipaddress
import json
import os
import secrets
import threading
import time
import urllib.parse
import winreg
from ctypes import wintypes
from pathlib import Path

from PIL import Image

from . import config_writer as cw
from . import content, network, paths, updater, upnp
from .version import GITHUB_REPO, __version__
from .server_process import ServerProcess

UPNP_DESC = "AC Szerver Kezelo"

DEFAULTS: dict[str, object] = {
    "server.name": "AC szerver",
    "server.password": "",
    "server.admin_password": "",
    "server.tcp_port": "9600",
    "server.udp_port": "9600",
    "server.http_port": "8081",
    "server.register_lobby": True,
    "server.pickup_mode": True,
    "server.loop_mode": True,
    "server.upnp": True,
    "practice.enabled": True,
    "practice.minutes": "15",
    "qualify.enabled": True,
    "qualify.minutes": "10",
    "race.enabled": True,
    "race.mode": "laps",
    "race.value": "10",
    "race.wait": "60",
    "weather.graphics": "3_clear",
    "weather.hour": 14.0,
    "weather.ambient": "22",
    "weather.road": "6",
    "track.grip": "90",
    "assist.abs": "1",
    "assist.tc": "1",
    "assist.stability": False,
    "assist.autoclutch": True,
    "assist.blankets": True,
    "assist.mirror": False,
    "real.damage": "100",
    "real.fuel": "100",
    "real.wear": "100",
    "real.tyres_out": "2",
    "pit.mandatory": False,
    "pit.start": "5",
    "pit.end": "15",
}


_CHOICES = {
    "assist.abs": {"0", "1", "2"},
    "assist.tc": {"0", "1", "2"},
    "race.mode": {"laps", "time"},
    "real.tyres_out": {"0", "1", "2", "3", "4"},
}
_LEGACY = {"Tiltva": "0", "Autó szerint": "1", "Kötelező": "2", "Körszám": "laps", "Perc": "time"}


def clean_values(raw: dict) -> dict:
    """Ismeretlen kulcsok kiszűrése és a régi (szöveges) formátumú értékek átalakítása."""
    out: dict = {}
    for key, value in (raw or {}).items():
        if key not in DEFAULTS:
            continue
        default = DEFAULTS[key]
        if isinstance(default, bool):
            out[key] = bool(value)
        elif isinstance(default, float):
            try:
                out[key] = float(value)
            except (TypeError, ValueError):
                pass
        else:
            v = _LEGACY.get(str(value), str(value))
            if key in _CHOICES and v not in _CHOICES[key]:
                continue
            out[key] = v
    return out


class ValidationError(Exception):
    def __init__(self, message: str, page: str) -> None:
        super().__init__(message)
        self.page = page


def _set_clipboard(text: str) -> bool:
    u32 = ctypes.WinDLL("user32", use_last_error=True)
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    u32.OpenClipboard.argtypes = [wintypes.HWND]
    u32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    u32.SetClipboardData.restype = wintypes.HANDLE
    k32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    k32.GlobalAlloc.restype = wintypes.HGLOBAL
    k32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    k32.GlobalLock.restype = ctypes.c_void_p
    k32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    data = text.encode("utf-16-le") + b"\x00\x00"
    for _ in range(10):
        if u32.OpenClipboard(None):
            break
        time.sleep(0.05)
    else:
        return False
    try:
        u32.EmptyClipboard()
        h = k32.GlobalAlloc(0x0002, len(data))
        ptr = k32.GlobalLock(h)
        ctypes.memmove(ptr, data, len(data))
        k32.GlobalUnlock(h)
        return bool(u32.SetClipboardData(13, h))  # CF_UNICODETEXT
    finally:
        u32.CloseClipboard()


class Api:
    def __init__(self) -> None:
        self._window = None
        self._cfg = paths.load_app_config()
        self._ac: Path | None = None
        self._server_dir: Path | None = None
        self._tracks: dict[str, content.TrackLayout] = {}
        self._cars: dict[str, content.Car] = {}
        self._weathers: list[str] = ["3_clear"]
        self._thumbs: dict[str, str | None] = {}
        self._gateway: upnp.Gateway | None = None
        self._mapped: list[tuple[int, str]] = []
        self._public_ip: str | None = None
        self._started_at: float | None = None
        self._op_lock = threading.Lock()
        self._allow_close = False
        self._last_nat: dict | None = None
        self._update_info: dict | None = None
        self._log_buf: list[str] = []
        self._log_lock = threading.Lock()
        self._server = ServerProcess(on_line=self._on_line, on_exit=self._on_exit)
        threading.Thread(target=self._log_flusher, daemon=True).start()
        threading.Thread(target=updater.cleanup_old_downloads, daemon=True).start()

    # ------------------------------------------------------------ belső

    def _attach(self, window) -> None:
        self._window = window

    def _emit(self, event: str, data) -> None:
        if self._window is None:
            return
        try:
            self._window.evaluate_js(f"window.onBackend && window.onBackend({json.dumps(event)}, {json.dumps(data)})")
        except Exception:  # noqa: BLE001 – az ablak már bezárulhatott
            pass

    def _log(self, msg: str) -> None:
        self._on_line("[Kezelő] " + msg)

    def _on_line(self, line: str) -> None:
        with self._log_lock:
            self._log_buf.append(line)

    def _log_flusher(self) -> None:
        while True:
            time.sleep(0.15)
            with self._log_lock:
                lines, self._log_buf = self._log_buf, []
            if lines:
                self._emit("log", lines)

    def _on_exit(self, code: int) -> None:
        if code != 0:
            self._log(f"A szerver váratlanul leállt (kilépési kód: {code}). Nézd meg a naplót a hiba okáért.")
            self._close_ports()
        self._started_at = None
        self._emit("status", self.status())

    def _dialog(self, kind: str, **kw):
        import webview

        fd = getattr(webview, "FileDialog", None)
        const = getattr(fd, kind) if fd else getattr(webview, f"{kind}_DIALOG")
        return self._window.create_file_dialog(const, **kw)

    # ------------------------------------------------------------ indulás, tartalom

    def init(self) -> dict:
        ac = None
        saved = self._cfg.get("ac_path")
        if saved and paths.is_ac_folder(Path(saved)):
            ac = Path(saved)
        if ac is None:
            ac = paths.find_ac_folder()
        if ac is None:
            return {"need_ac": True, "defaults": self._defaults()}
        return self._load_ac(ac)

    def _defaults(self) -> dict:
        d = dict(DEFAULTS)
        d["server.admin_password"] = secrets.token_urlsafe(6)
        return d

    def _load_ac(self, ac: Path) -> dict:
        ac = Path(os.path.realpath(ac))
        self._ac = ac
        self._server_dir = paths.find_server_folder(ac)
        self._cfg["ac_path"] = str(ac)
        paths.save_app_config(self._cfg)
        self._scan()
        values = self._defaults()
        last = self._cfg.get("last") or {}
        values.update(clean_values(last.get("values") or {}))
        if not values.get("server.admin_password"):
            values["server.admin_password"] = secrets.token_urlsafe(6)
        return {
            "need_ac": False,
            "ac_path": str(ac),
            "server_path": str(self._server_dir) if self._server_dir else None,
            "defaults": self._defaults(),
            "values": values,
            **self._content_payload(),
            "status": self.status(),
        }

    def _scan(self) -> None:
        assert self._ac is not None
        self._tracks = {t.key: t for t in content.scan_tracks(self._ac, self._server_dir)}
        self._cars = {c.car_id: c for c in content.scan_cars(self._ac, self._server_dir)}
        self._weathers = content.scan_weathers(self._ac)
        self._thumbs.clear()

    def _content_payload(self) -> dict:
        return {
            "tracks": [
                {
                    "key": t.key, "id": t.track_id, "layout": t.layout, "name": t.name,
                    "pitboxes": t.pitboxes, "length": t.length, "country": t.country, "mod": t.is_mod,
                }
                for t in self._tracks.values()
            ],
            "cars": sorted(
                (
                    {"id": c.car_id, "name": c.name, "brand": c.brand, "skins": c.skins, "mod": c.is_mod}
                    for c in self._cars.values()
                ),
                key=lambda c: c["name"].lower(),
            ),
            "weathers": self._weathers,
        }

    def choose_ac_folder(self) -> dict:
        res = self._dialog("FOLDER")
        if not res:
            return {"cancelled": True}
        p = Path(res[0] if isinstance(res, (list, tuple)) else res)
        if not paths.is_ac_folder(p):
            return {"error": "Ez nem az Assetto Corsa mappája (nincs benne content\\cars és content\\tracks)."}
        if self._server.running:
            return {"error": "Előbb állítsd le a szervert."}
        return self._load_ac(p)

    def rescan(self) -> dict:
        if not self._ac:
            return {"error": "Nincs kiválasztva Assetto Corsa mappa."}
        self._scan()
        return self._content_payload()

    def thumb(self, kind: str, item_id: str, skin: str | None = None) -> str | None:
        """Előnézeti kép kicsinyítve, data URL-ként."""
        key = f"{kind}|{item_id}|{skin or ''}"
        if key in self._thumbs:
            return self._thumbs[key]
        path = None
        if kind == "track" and item_id in self._tracks:
            path = self._tracks[item_id].preview
        elif kind == "car" and item_id in self._cars and self._ac:
            car = self._cars[item_id]
            skins = [skin] if skin and skin in car.skins else car.skins
            for s in skins[:3]:
                p = self._ac / "content" / "cars" / item_id / "skins" / s / "preview.jpg"
                if p.is_file():
                    path = p
                    break
        url = None
        if path:
            try:
                img = Image.open(path).convert("RGB")
                img.thumbnail((560, 316))
                buf = io.BytesIO()
                img.save(buf, "JPEG", quality=82)
                url = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
            except OSError:
                url = None
        self._thumbs[key] = url
        return url

    # ------------------------------------------------------------ beállítások

    def _int(self, values: dict, key: str, label: str, lo: int, hi: int, page: str) -> int:
        raw = str(values.get(key, DEFAULTS.get(key, ""))).strip()
        try:
            val = int(float(raw))
        except ValueError:
            raise ValidationError(f"„{label}”: egész számot adj meg (most: „{raw}”).", page) from None
        if not lo <= val <= hi:
            raise ValidationError(f"„{label}”: {lo} és {hi} közötti érték lehet (most: {val}).", page)
        return val

    def _build_settings(self, preset: dict) -> cw.ServerSettings:
        v = {**DEFAULTS, **clean_values(preset.get("values") or {})}
        t = self._tracks.get(preset.get("track") or "")
        if not t:
            raise ValidationError("Adj hozzá egy pályát az Összeállítás oldalon.", "build")
        cars: list[cw.CarEntry] = []
        for c in preset.get("cars") or []:
            car = self._cars.get(c.get("id", ""))
            if not car:
                continue
            try:
                slots = int(c.get("slots", 1))
            except (TypeError, ValueError):
                raise ValidationError(f"„{car.name}”: a helyek száma egész szám legyen.", "build") from None
            if slots < 1:
                raise ValidationError(f"„{car.name}”: legalább 1 hely kell.", "build")
            cars.append(cw.CarEntry(car.car_id, slots, c.get("skin") or cw.RANDOM_SKIN, car.skins))
        if not cars:
            raise ValidationError("Adj hozzá legalább egy autót az Összeállítás oldalon.", "build")
        total = sum(c.slots for c in cars)
        if t.pitboxes and total > t.pitboxes:
            raise ValidationError(
                f"A(z) {t.name} pályán csak {t.pitboxes} pit box van, de {total} helyet adtál meg. Csökkentsd az autók számát.",
                "build",
            )
        name = str(v["server.name"]).strip()
        if not name:
            raise ValidationError("Adj nevet a szervernek.", "server")
        tcp = self._int(v, "server.tcp_port", "TCP port", 1024, 65535, "server")
        udp = self._int(v, "server.udp_port", "UDP port", 1024, 65535, "server")
        http = self._int(v, "server.http_port", "HTTP port", 1024, 65535, "server")
        if http == tcp:
            raise ValidationError("A HTTP port nem lehet ugyanaz, mint a TCP port.", "server")
        practice = (bool(v["practice.enabled"]), self._int(v, "practice.minutes", "Szabadedzés hossza", 1, 1440, "rules"))
        qualify = (bool(v["qualify.enabled"]), self._int(v, "qualify.minutes", "Időmérő hossza", 1, 1440, "rules"))
        race_enabled = bool(v["race.enabled"])
        if not (practice[0] or qualify[0] or race_enabled):
            raise ValidationError("Legalább egy sessiont kapcsolj be.", "rules")
        pit_mandatory = bool(v["pit.mandatory"])
        pit_start = self._int(v, "pit.start", "Boxablak kezdete", 0, 1000, "rules")
        pit_end = self._int(v, "pit.end", "Boxablak vége", 0, 1000, "rules")
        if pit_mandatory and pit_start >= pit_end:
            raise ValidationError("A boxablak vége legyen később, mint a kezdete.", "rules")
        weather = str(v["weather.graphics"])
        if weather not in self._weathers:
            weather = self._weathers[0]
        return cw.ServerSettings(
            name=name,
            password=str(v["server.password"]),
            admin_password=str(v["server.admin_password"]) or secrets.token_urlsafe(6),
            tcp_port=tcp, udp_port=udp, http_port=http,
            register_lobby=bool(v["server.register_lobby"]),
            pickup_mode=bool(v["server.pickup_mode"]),
            loop_mode=bool(v["server.loop_mode"]),
            track_id=t.track_id, layout=t.layout, cars=cars,
            practice=practice, qualify=qualify,
            race_enabled=race_enabled,
            race_by_laps=str(v["race.mode"]) != "time",
            race_value=self._int(v, "race.value", "Verseny hossza", 1, 1000, "rules"),
            race_wait=self._int(v, "race.wait", "Várakozás a rajt előtt", 0, 3600, "rules"),
            weather=weather,
            hour=max(8.0, min(18.0, float(v["weather.hour"]))),
            ambient=self._int(v, "weather.ambient", "Levegő hőmérséklete", -20, 50, "rules"),
            road_offset=self._int(v, "weather.road", "Aszfalt többlet hőmérséklete", -10, 40, "rules"),
            track_grip=self._int(v, "track.grip", "Aszfalt tapadása", cw.GRIP_MIN, cw.GRIP_MAX, "rules"),
            abs_level=self._int(v, "assist.abs", "ABS", 0, 2, "rules"),
            tc_level=self._int(v, "assist.tc", "TC", 0, 2, "rules"),
            stability=bool(v["assist.stability"]),
            autoclutch=bool(v["assist.autoclutch"]),
            blankets=bool(v["assist.blankets"]),
            virtual_mirror=bool(v["assist.mirror"]),
            damage=self._int(v, "real.damage", "Sérülés", 0, 100, "rules"),
            fuel_rate=self._int(v, "real.fuel", "Üzemanyag-fogyasztás", 0, 500, "rules"),
            tyre_wear=self._int(v, "real.wear", "Gumikopás", 0, 500, "rules"),
            tyres_out=self._int(v, "real.tyres_out", "Max. kerék kint", 0, 4, "rules"),
            pit_mandatory=pit_mandatory, pit_start=pit_start, pit_end=pit_end,
        )

    def save_last(self, preset: dict) -> bool:
        self._cfg["last"] = {"values": preset.get("values") or {}}
        paths.save_app_config(self._cfg)
        return True

    def save_preset(self, preset: dict) -> dict:
        name = str((preset.get("values") or {}).get("server.name") or "preset").replace(" ", "_")
        res = self._dialog("SAVE", save_filename=f"{name}.json", file_types=("AC szerver preset (*.json)",))
        if not res:
            return {"cancelled": True}
        path = Path(res[0] if isinstance(res, (list, tuple)) else res)
        if path.suffix.lower() != ".json":
            path = path.with_suffix(".json")
        try:
            data = {"version": 1, **preset}
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as e:
            return {"error": f"Nem sikerült menteni: {e}"}
        return {"ok": True, "path": str(path)}

    def load_preset(self) -> dict:
        res = self._dialog("OPEN", file_types=("AC szerver preset (*.json)",))
        if not res:
            return {"cancelled": True}
        try:
            preset = json.loads(Path(res[0]).read_text(encoding="utf-8"))
            if not isinstance(preset, dict):
                raise ValueError
        except (OSError, ValueError):
            return {"error": "Ez a fájl nem érvényes preset."}
        preset["values"] = clean_values(preset.get("values") or {})
        missing = []
        track = preset.get("track")
        if track and track not in self._tracks:
            missing.append("pálya: " + track.replace("|", " ").strip())
        for c in preset.get("cars") or []:
            if c.get("id") not in self._cars:
                missing.append("autó: " + str(c.get("id")))
        return {"ok": True, "preset": preset, "missing": missing}

    # ------------------------------------------------------------ szerver

    def status(self) -> dict:
        return {
            "running": self._server.running,
            "started_at": self._started_at,
            "server_ok": self._server_dir is not None,
            "busy": self._op_lock.locked(),
        }

    def start(self, preset: dict) -> dict:
        if not self._server_dir or not self._ac:
            return {"ok": False, "error": "Nem található az acServer.exe. Telepítsd a Steamben az „Assetto Corsa Dedicated Server” eszközt."}
        if not self._op_lock.acquire(blocking=False):
            return {"ok": False, "error": "Egy művelet már folyamatban van."}
        try:
            if self._server.running:
                return {"ok": False, "error": "A szerver már fut."}
            try:
                s = self._build_settings(preset)
            except ValidationError as e:
                return {"ok": False, "error": str(e), "page": e.page}
            self.save_last(preset)
            for port, udp in ((s.tcp_port, False), (s.udp_port, True), (s.http_port, False)):
                if network.port_in_use(port, udp):
                    return {
                        "ok": False,
                        "error": f"A(z) {port} ({'UDP' if udp else 'TCP'}) port foglalt. Valószínűleg már fut egy AC szerver, "
                                 "vagy egy másik program használja. Állítsd le, vagy a Szerver oldalon adj meg másik portot.",
                        "page": "server",
                    }
            try:
                self._log("Pálya és autók előkészítése a szerverhez…")
                content.pack_track(self._ac, self._server_dir, s.track_id, s.layout, self._log)
                for car_id in dict.fromkeys(c.car_id for c in s.cars):
                    content.pack_car(self._ac, self._server_dir, car_id, self._log)
                cfg_dir = cw.write_configs(self._server_dir, s)
                self._log(f"Konfiguráció elmentve: {cfg_dir}")
                self._server.start(self._server_dir)
            except (OSError, RuntimeError) as e:
                self._log(f"Indítás sikertelen: {e}")
                return {"ok": False, "error": str(e)}
            self._started_at = time.time()
            self._log("acServer.exe elindítva.")
            use_upnp = bool((preset.get("values") or {}).get("server.upnp", True))
            threading.Thread(target=self._after_start, args=(s, use_upnp), daemon=True).start()
            return {"ok": True, "status": self.status()}
        finally:
            self._op_lock.release()

    def stop(self) -> dict:
        with self._op_lock:
            self._server.stop()
            self._close_ports()
            self._started_at = None
        self._log("Szerver leállítva.")
        return self.status()

    def _after_start(self, s: cw.ServerSettings, use_upnp: bool) -> None:
        """Indítás után minden hálózati lépés magától lefut: tűzfal, UPnP, elérhetőség teszt."""
        try:
            if self._server_dir and network.firewall_enabled() and not network.firewall_rules_exist():
                self._log("A Windows tűzfal be van kapcsolva: szabály hozzáadása (a Windows egyszer engedélyt kér)…")
                self._emit("toast", {"kind": "info", "text": "A Windows engedélyt kér a tűzfal szabályhoz – kattints az „Igen” gombra. Ez csak egyszer kell."})
                ok = network.add_firewall_rules(
                    str(self._server_dir / "acServer.exe"), [s.tcp_port, s.http_port], [s.udp_port]
                )
                self._log("Tűzfal szabályok hozzáadva." if ok else "A tűzfal szabály hozzáadása nem sikerült.")
            upnp_state = "off"
            if use_upnp:
                upnp_state = "ok" if self._open_ports(s) else "failed"
            time.sleep(2)
            if not self._server.running:
                return
            self._emit("reach", {"state": "testing"})
            ip = self._public_ip or network.public_ip()
            self._public_ip = ip
            res = network.check_port_external(ip, s.http_port) if ip else None
            if not self._server.running:
                return
            state = {True: "open", False: "closed", None: "error"}[res]
            self._log(
                "Automatikus elérhetőség teszt: "
                + {"open": "a szerver kívülről elérhető.", "closed": "a szerver kívülről NEM érhető el.", "error": "a teszt nem sikerült."}[state]
            )
            self._emit("reach", {"state": state, "ip": ip, "nat": self._last_nat, "upnp": upnp_state})
        except Exception as e:  # noqa: BLE001 – a háttérellenőrzés hibája ne állítsa le a szervert
            self._log(f"Automatikus hálózati ellenőrzés hiba: {e}")

    def _open_ports(self, s: cw.ServerSettings) -> bool:
        try:
            gw = self._gateway or upnp.discover()
            self._gateway = gw
            wanted = [(s.tcp_port, "TCP"), (s.udp_port, "UDP"), (s.http_port, "TCP")]
            ports_txt = ", ".join(f"{p}/{pr}" for p, pr in wanted)
            for port, proto in wanted:
                upnp.add_port_mapping(gw, port, proto, UPNP_DESC)
                self._mapped.append((gw, port, proto))
            self._log(f"UPnP: portok megnyitva a routeren ({ports_txt}).")
            where = "a routeren"
            # Dupla NAT: a router előtti eszközön (szolgáltatói modem) is megnyitjuk a portokat
            try:
                ext = upnp.get_external_ip(gw)
                for _level in range(2):
                    if not ext or not network.is_non_public(ext) or network.is_cgnat(ext):
                        break
                    up = upnp.discover_upstream(ext)
                    if up is None:
                        self._log(
                            f"A routered előtt van még egy eszköz (külső cím: {ext}), de az nem támogatja az automatikus "
                            "port nyitást. Ha a barátaid nem tudnak csatlakozni, ott kell port forwardingot beállítani."
                        )
                        break
                    for port, proto in wanted:
                        upnp.add_port_mapping(up, port, proto, UPNP_DESC)
                        self._mapped.append((up, port, proto))
                    self._log(f"UPnP: portok megnyitva a szolgáltatói modemen is ({ports_txt} → {ext}).")
                    where = "a routeren és a modemen"
                    ext = upnp.get_external_ip(up)
            except upnp.UPnPError as e:
                self._log(f"A szolgáltatói modemen nem sikerült megnyitni a portokat: {e}")
            self._emit("toast", {"kind": "ok", "text": f"Portok automatikusan megnyitva {where}."})
            return True
        except upnp.UPnPError as e:
            self._log(f"UPnP nem sikerült: {e}. Ha a barátaid nem tudnak csatlakozni, állíts be port forwardingot kézzel.")
            self._emit("toast", {"kind": "warn", "text": "A portokat nem sikerült automatikusan megnyitni (UPnP)."})
            return False

    def _close_ports(self) -> None:
        for gw, port, proto in self._mapped:
            upnp.delete_port_mapping(gw, port, proto)
        self._mapped = []

    # ------------------------------------------------------------ hálózat

    def network(self) -> dict:
        local = network.all_local_ips() or [network.primary_local_ip()]
        self._public_ip = network.public_ip()
        info: dict = {
            "local": [{"ip": ip, "desc": network.describe_ip(ip)} for ip in local],
            "public": self._public_ip,
        }
        ext = ""
        gw = None
        try:
            # Ha korábban már megtaláltuk a routert, először azt kérdezzük meg
            if self._gateway:
                try:
                    ext = upnp.get_external_ip(self._gateway)
                    gw = self._gateway
                except upnp.UPnPError:
                    gw = None
            if gw is None:
                gw = upnp.discover()
                ext = upnp.get_external_ip(gw)
            self._gateway = gw
            info["upnp"] = {"ok": True, "text": f"UPnP elérhető (router külső címe: {ext or '?'})"}
        except upnp.UPnPError as e:
            gw = None
            info["upnp"] = {"ok": False, "text": str(e)}

        pub = self._public_ip
        if gw and ext and pub and ext == pub:
            nat = ("ok", "A routerednek nyilvános IP-je van, a port nyitás működni fog.")
        elif gw and ext and network.is_non_public(ext):
            try:
                cgnat = ipaddress.ip_address(ext) in ipaddress.ip_network("100.64.0.0/10")
            except ValueError:
                cgnat = False
            if cgnat:
                nat = ("bad", "CGNAT: a szolgáltatód nem ad saját nyilvános IP-t, így kívülről nem érhető el a szerver. "
                              "Megoldás: Radmin VPN / ZeroTier / Tailscale, vagy kérj nyilvános IP-t a szolgáltatótól.")
            elif upnp.discover_upstream(ext) is not None:
                nat = ("ok", f"Dupla NAT van (a routered előtt a szolgáltató modemje áll), de a modem is támogatja az "
                             "automatikus port nyitást: indításkor a program mindkét eszközön megnyitja a portokat.")
            else:
                nat = ("warn", f"Dupla NAT: a routered ({ext}) előtt van még egy eszköz, valószínűleg a szolgáltató modemje. "
                               "Ha az indítás utáni elérhetőség teszt sikeres, nincs teendő. Ha nem, a modemen is állíts be "
                               "port forwardingot a routered felé (TCP+UDP 9600, TCP 8081), kapcsold a modemet bridge módba, "
                               "vagy használj VPN-t (Radmin VPN / ZeroTier / Tailscale).")
        elif not gw:
            nat = ("unknown", "Nem tudom automatikusan ellenőrizni. Indítsd el a szervert, és futtasd az elérhetőség tesztet.")
        else:
            nat = ("unknown", "A router és a publikus IP eltér, lehet dupla NAT. Futtasd az elérhetőség tesztet.")
        info["nat"] = {"level": nat[0], "text": nat[1]}
        self._last_nat = info["nat"]
        info["gateway_ip"] = gw.local_ip if gw else None
        return info

    def port_test(self, http_port) -> dict:
        if not self._server.running:
            return {"result": "not_running"}
        ip = self._public_ip or network.public_ip()
        if not ip:
            return {"result": "no_ip"}
        res = network.check_port_external(ip, int(http_port))
        self._log(
            "Elérhetőség teszt: "
            + {True: "a szerver kívülről elérhető.", False: "a szerver kívülről NEM érhető el.", None: "a teszt nem sikerült."}[res]
        )
        return {"result": {True: "open", False: "closed", None: "error"}[res], "ip": ip}

    def firewall(self, tcp_port, udp_port, http_port) -> dict:
        if not self._server_dir:
            return {"ok": False}
        self._log("Tűzfal szabály hozzáadása…")
        ok = network.add_firewall_rules(
            str(self._server_dir / "acServer.exe"), [int(tcp_port), int(http_port)], [int(udp_port)]
        )
        self._log("Tűzfal szabályok hozzáadva." if ok else "A tűzfal szabályok hozzáadása nem sikerült (vagy megszakítottad).")
        return {"ok": ok}

    def join(self, http_port, password: str = "") -> dict:
        """A host csatlakozása a saját szerveréhez a Content Manageren keresztül."""
        if not self._server.running:
            return {"error": "A szerver nem fut."}
        try:
            winreg.CloseKey(winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "acmanager"))
        except OSError:
            return {"error": "A Content Manager nincs telepítve, ezért nem tudok automatikusan csatlakozni. "
                             "A sima AC-ben az Online menüben a szerver nevével találod meg."}
        query = {"ip": "127.0.0.1", "httpPort": int(http_port)}
        if password:
            query["password"] = password
        try:
            os.startfile("acmanager://race/online/join?" + urllib.parse.urlencode(query))
        except OSError as e:
            return {"error": f"Nem sikerült elindítani a Content Managert: {e}"}
        return {"ok": True}

    def links(self, ip: str, http_port) -> dict:
        web, app = network.cm_links(ip, int(http_port))
        return {"web": web, "app": app}

    def copy(self, text: str) -> bool:
        try:
            return _set_clipboard(text)
        except OSError:
            return False

    # ------------------------------------------------------------ frissítések

    def app_version(self) -> dict:
        return {"version": __version__, "repo": GITHUB_REPO}

    def check_update(self) -> dict:
        try:
            info = updater.check()
        except updater.UpdateError as e:
            return {"error": str(e)}
        self._update_info = info
        return {"update": info}

    def install_update(self) -> dict:
        info = self._update_info
        if not info:
            return {"error": "Nincs letölthető frissítés."}

        def work() -> None:
            try:
                updater.download_and_install(info, lambda p: self._emit("update_progress", round(p * 100)))
            except updater.UpdateError as e:
                self._emit("update_failed", str(e))
                return
            # A telepítő elindult: leállítjuk a szervert, és bezárjuk a programot
            self.quit()

        threading.Thread(target=work, daemon=True).start()
        return {"ok": True}

    # ------------------------------------------------------------ bezárás

    def _on_closing(self) -> bool:
        if self._allow_close or not self._server.running:
            return True
        # A GUI szálon nem várhatunk a JavaScriptre, ezért külön szálon kérdezünk rá
        threading.Thread(target=self._emit, args=("confirm_close", {}), daemon=True).start()
        return False

    def quit(self) -> None:
        self._allow_close = True
        self._shutdown()
        threading.Thread(target=self._window.destroy, daemon=True).start()

    def _shutdown(self) -> None:
        try:
            self._server.stop()
        finally:
            self._close_ports()
