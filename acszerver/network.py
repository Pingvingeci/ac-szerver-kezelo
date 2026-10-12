"""IP-címek, CGNAT felismerés, külső port teszt és Windows tűzfal szabályok."""
from __future__ import annotations

import ipaddress
import json
import socket
import time
import subprocess
import tempfile
import urllib.parse
from pathlib import Path
import urllib.request

CREATE_NO_WINDOW = 0x08000000
FIREWALL_RULE_PREFIX = "AC Szerver Kezelo"
_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ACSzerverKezelo"}


def primary_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def all_local_ips() -> list[str]:
    ips = []
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if not ip.startswith("127.") and ip not in ips:
                ips.append(ip)
    except OSError:
        pass
    return ips


def describe_ip(ip: str) -> str:
    """Felismeri a népszerű VPN-ek címtartományait."""
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return ""
    if addr in ipaddress.ip_network("26.0.0.0/8"):
        return "Radmin VPN"
    if addr in ipaddress.ip_network("100.64.0.0/10"):
        return "Tailscale"
    if addr in ipaddress.ip_network("172.22.0.0/16") or addr in ipaddress.ip_network("10.147.0.0/16"):
        return "ZeroTier (valószínűleg)"
    if addr.is_private:
        return "helyi hálózat"
    return ""


def public_ip() -> str | None:
    for url in ("https://api.ipify.org", "https://ifconfig.me/ip", "https://icanhazip.com"):
        try:
            req = urllib.request.Request(url, headers=_UA)
            with urllib.request.urlopen(req, timeout=6) as r:
                ip = r.read().decode().strip()
            ipaddress.ip_address(ip)
            return ip
        except (OSError, ValueError):
            continue
    return None


def is_non_public(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return True
    return addr.is_private or addr in ipaddress.ip_network("100.64.0.0/10")


def is_cgnat(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip) in ipaddress.ip_network("100.64.0.0/10")
    except ValueError:
        return False


def check_port_external(ip: str, port: int) -> bool | None:
    """Kívülről ellenőrzi, hogy a TCP port elérhető-e. None = a teszt nem sikerült."""
    # check-host.net: több országból próbál csatlakozni a megadott TCP porthoz
    def get(url: str):
        req = urllib.request.Request(url, headers={**_UA, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())

    try:
        host = urllib.parse.quote(f"{ip}:{port}")
        req_id = get(f"https://check-host.net/check-tcp?host={host}&max_nodes=3")["request_id"]
        results: dict = {}
        for _ in range(12):
            time.sleep(2)
            results = get(f"https://check-host.net/check-result/{req_id}")
            if results and all(v is not None for v in results.values()):
                break
    except (OSError, ValueError, KeyError):
        return None
    answers = [v[0] for v in results.values() if isinstance(v, list) and v and isinstance(v[0], dict)]
    if any("address" in a for a in answers):
        return True
    if answers:
        return False
    return None


def port_in_use(port: int, udp: bool = False) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM if udp else socket.SOCK_STREAM)
    try:
        s.bind(("0.0.0.0", port))
        return False
    except OSError:
        return True
    finally:
        s.close()


def firewall_enabled() -> bool:
    """Be van-e kapcsolva a Windows tűzfal valamelyik profilja (nyelvfüggetlen lekérdezés)."""
    try:
        out = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", "@(Get-NetFirewallProfile | Where-Object Enabled).Count"],
            capture_output=True, text=True, creationflags=CREATE_NO_WINDOW, timeout=20,
        )
        return int(out.stdout.strip() or "1") > 0
    except (OSError, subprocess.SubprocessError, ValueError):
        return True  # bizonytalan esetben inkább adjuk hozzá a szabályt


def firewall_rules_exist() -> bool:
    try:
        out = subprocess.run(
            ["netsh", "advfirewall", "firewall", "show", "rule", f"name={FIREWALL_RULE_PREFIX} TCP"],
            capture_output=True,
            creationflags=CREATE_NO_WINDOW,
            timeout=10,
        )
        return out.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def add_firewall_rules(acserver_exe: str, tcp_ports: list[int], udp_ports: list[int]) -> bool:
    """Rendszergazdaként (UAC ablak) hozzáadja a tűzfal szabályokat. True, ha utána léteznek."""
    tcp = ",".join(str(p) for p in sorted(set(tcp_ports)))
    udp = ",".join(str(p) for p in sorted(set(udp_ports)))
    n = FIREWALL_RULE_PREFIX
    cmds = [
        f'netsh advfirewall firewall delete rule name="{n} TCP"',
        f'netsh advfirewall firewall delete rule name="{n} UDP"',
        f'netsh advfirewall firewall delete rule name="{n} acServer"',
        f'netsh advfirewall firewall add rule name="{n} TCP" dir=in action=allow protocol=TCP localport={tcp}',
        f'netsh advfirewall firewall add rule name="{n} UDP" dir=in action=allow protocol=UDP localport={udp}',
        f'netsh advfirewall firewall add rule name="{n} acServer" dir=in action=allow program="{acserver_exe}"',
    ]
    # Ideiglenes .cmd fájl, így nem kell az idézőjeleket több rétegen át escape-elni
    bat = Path(tempfile.gettempdir()) / "acszk_firewall.cmd"
    bat.write_text(
        "@echo off\r\nchcp 65001 >nul\r\n" + "\r\n".join(c + " >nul" for c in cmds) + "\r\n",
        encoding="utf-8",
    )
    ps = (
        "Start-Process -FilePath cmd.exe -Verb RunAs -Wait -WindowStyle Hidden "
        f"-ArgumentList '/c', '\"{bat}\"'"
    )
    try:
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", ps],
            creationflags=CREATE_NO_WINDOW,
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    finally:
        try:
            bat.unlink()
        except OSError:
            pass
    return firewall_rules_exist()


def cm_links(ip: str, http_port: int) -> tuple[str, str]:
    query = f"ip={ip}&httpPort={http_port}"
    return (
        f"https://acstuff.club/s/q:race/online/join?{query}",
        f"acmanager://race/online/join?{query}",
    )
