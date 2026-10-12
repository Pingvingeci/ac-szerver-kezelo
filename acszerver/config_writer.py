"""server_cfg.ini és entry_list.ini előállítása."""
from __future__ import annotations

import random
import shutil
from dataclasses import dataclass, field
from pathlib import Path

RANDOM_SKIN = "Véletlenszerű"

# Az aszfalt tapadása százalékban (a csúszka tartománya): 80 = drift, 90 = közepes, 100 = teljes tapadás
GRIP_MIN, GRIP_MAX = 80, 100

ASSIST_LEVELS = {"Tiltva": 0, "Autó szerint": 1, "Kötelező": 2}


@dataclass
class CarEntry:
    car_id: str
    slots: int
    skin: str  # RANDOM_SKIN vagy egy skin mappa neve
    skins: list[str] = field(default_factory=list)


@dataclass
class ServerSettings:
    name: str
    password: str
    admin_password: str
    tcp_port: int
    udp_port: int
    http_port: int
    register_lobby: bool
    pickup_mode: bool
    loop_mode: bool
    track_id: str
    layout: str
    cars: list[CarEntry]
    practice: tuple[bool, int]
    qualify: tuple[bool, int]
    race_enabled: bool
    race_by_laps: bool
    race_value: int
    race_wait: int
    weather: str
    hour: float
    ambient: int
    road_offset: int
    track_grip: int
    abs_level: int
    tc_level: int
    stability: bool
    autoclutch: bool
    blankets: bool
    virtual_mirror: bool
    damage: int
    fuel_rate: int
    tyre_wear: int
    tyres_out: int
    pit_mandatory: bool
    pit_start: int
    pit_end: int

    @property
    def total_slots(self) -> int:
        return sum(c.slots for c in self.cars)


def sun_angle(hour: float) -> int:
    """8:00 → -80, 13:00 → 0, 18:00 → 80 (így számol az AC is)."""
    return int(round(max(-80.0, min(80.0, (hour - 13.0) * 16.0))))


def _clean(text: str) -> str:
    return text.replace("\r", " ").replace("\n", " ").strip()


def build_server_cfg(s: ServerSettings) -> str:
    car_ids = list(dict.fromkeys(c.car_id for c in s.cars))
    # Állandó tapadás: a megadott értéken indul, nem véletlenszerű, és menet közben sem változik
    start = max(GRIP_MIN, min(GRIP_MAX, s.track_grip))
    rnd, transfer, gain = 0, 100, 1000000
    pit_start, pit_end = (s.pit_start, s.pit_end) if s.pit_mandatory else (0, 0)
    lines = [
        "[SERVER]",
        f"NAME={_clean(s.name)}",
        f"CARS={';'.join(car_ids)}",
        f"CONFIG_TRACK={s.layout}",
        f"TRACK={s.track_id}",
        f"SUN_ANGLE={sun_angle(s.hour)}",
        f"PASSWORD={_clean(s.password)}",
        f"ADMIN_PASSWORD={_clean(s.admin_password)}",
        f"UDP_PORT={s.udp_port}",
        f"TCP_PORT={s.tcp_port}",
        f"HTTP_PORT={s.http_port}",
        f"MAX_BALLAST_KG=150",
        *([f"RACE_PIT_WINDOW_START={pit_start}", f"RACE_PIT_WINDOW_END={pit_end}"] if s.pit_mandatory else []),
        f"QUALIFY_MAX_WAIT_PERC=120",
        f"REVERSED_GRID_RACE_POSITIONS=0",
        f"LOCKED_ENTRY_LIST=0",
        f"PICKUP_MODE_ENABLED={int(s.pickup_mode)}",
        f"LOOP_MODE={int(s.loop_mode)}",
        f"SLEEP_TIME=1",
        f"CLIENT_SEND_INTERVAL_HZ=18",
        f"SEND_BUFFER_SIZE=0",
        f"RECV_BUFFER_SIZE=0",
        f"RACE_OVER_TIME=180",
        f"KICK_QUORUM=85",
        f"VOTING_QUORUM=80",
        f"VOTE_DURATION=20",
        f"BLACKLIST_MODE=1",
        f"FUEL_RATE={s.fuel_rate}",
        f"DAMAGE_MULTIPLIER={s.damage}",
        f"TYRE_WEAR_RATE={s.tyre_wear}",
        f"ALLOWED_TYRES_OUT={s.tyres_out}",
        f"ABS_ALLOWED={s.abs_level}",
        f"TC_ALLOWED={s.tc_level}",
        f"STABILITY_ALLOWED={int(s.stability)}",
        f"AUTOCLUTCH_ALLOWED={int(s.autoclutch)}",
        f"TYRE_BLANKETS_ALLOWED={int(s.blankets)}",
        f"FORCE_VIRTUAL_MIRROR={int(s.virtual_mirror)}",
        f"REGISTER_TO_LOBBY={int(s.register_lobby)}",
        f"MAX_CLIENTS={s.total_slots}",
        f"NUM_THREADS=2",
        f"UDP_PLUGIN_LOCAL_PORT=0",
        f"UDP_PLUGIN_ADDRESS=",
        f"AUTH_PLUGIN_ADDRESS=",
        f"LEGAL_TYRES=",
        f"RACE_EXTRA_LAP=0",
        f"RACE_GAS_PENALTY_DISABLED=0",
        f"RESULT_SCREEN_TIME=60",
        f"START_RULE=0",
        f"TIME_OF_DAY_MULT=1",
        f"WELCOME_MESSAGE=",
        "",
    ]
    if s.practice[0]:
        lines += ["[PRACTICE]", "NAME=Practice", f"TIME={s.practice[1]}", "IS_OPEN=1", ""]
    if s.qualify[0]:
        lines += ["[QUALIFY]", "NAME=Qualify", f"TIME={s.qualify[1]}", "IS_OPEN=1", ""]
    if s.race_enabled:
        lines += ["[RACE]", "NAME=Race"]
        if s.race_by_laps:
            lines += [f"LAPS={s.race_value}", "TIME=0"]
        else:
            lines += ["LAPS=0", f"TIME={s.race_value}"]
        lines += [f"WAIT_TIME={s.race_wait}", "IS_OPEN=1", ""]
    lines += [
        "[DYNAMIC_TRACK]",
        f"SESSION_START={start}",
        f"RANDOMNESS={rnd}",
        f"SESSION_TRANSFER={transfer}",
        f"LAP_GAIN={gain}",
        "",
        "[WEATHER_0]",
        f"GRAPHICS={s.weather}",
        f"BASE_TEMPERATURE_AMBIENT={s.ambient}",
        f"BASE_TEMPERATURE_ROAD={s.road_offset}",
        "VARIATION_AMBIENT=1",
        "VARIATION_ROAD=1",
        "",
    ]
    return "\n".join(lines)


def build_entry_list(s: ServerSettings) -> str:
    lines: list[str] = []
    idx = 0
    for car in s.cars:
        if car.skin == RANDOM_SKIN:
            pool = list(car.skins)
            random.shuffle(pool)
            skins = [pool[i % len(pool)] if pool else "" for i in range(car.slots)]
        else:
            skins = [car.skin] * car.slots
        for skin in skins:
            lines += [
                f"[CAR_{idx}]",
                f"MODEL={car.car_id}",
                f"SKIN={skin}",
                "SPECTATOR_MODE=0",
                "DRIVERNAME=",
                "TEAM=",
                "GUID=",
                "BALLAST=0",
                "RESTRICTOR=0",
                "",
            ]
            idx += 1
    return "\n".join(lines)


def write_configs(server_dir: Path, s: ServerSettings) -> Path:
    cfg_dir = server_dir / "cfg"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    # Az eredeti konfigurációt egyszer elmentjük, hogy vissza lehessen állítani
    backup = cfg_dir / "eredeti_mentes"
    if not backup.exists():
        backup.mkdir()
        for name in ("server_cfg.ini", "entry_list.ini"):
            if (cfg_dir / name).is_file():
                shutil.copy2(cfg_dir / name, backup / name)
    (cfg_dir / "server_cfg.ini").write_text(build_server_cfg(s), encoding="utf-8")
    (cfg_dir / "entry_list.ini").write_text(build_entry_list(s), encoding="utf-8")
    return cfg_dir
