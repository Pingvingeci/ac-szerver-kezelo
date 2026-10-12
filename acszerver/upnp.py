"""Egyszerű UPnP IGD kliens (külső függőség nélkül) a router portjainak megnyitásához."""
from __future__ import annotations

import socket
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from xml.sax.saxutils import escape

SSDP_ADDR = ("239.255.255.250", 1900)
SEARCH_TARGETS = (
    "urn:schemas-upnp-org:device:InternetGatewayDevice:1",
    "urn:schemas-upnp-org:device:InternetGatewayDevice:2",
    "urn:schemas-upnp-org:service:WANIPConnection:1",
    "urn:schemas-upnp-org:service:WANPPPConnection:1",
    # Néhány router csak az általános keresésre válaszol
    "upnp:rootdevice",
    "ssdp:all",
)


class UPnPError(Exception):
    pass


@dataclass
class Gateway:
    control_url: str
    service_type: str
    local_ip: str


def _local_ip_towards(host: str) -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((host, 1900))
        return s.getsockname()[0]
    finally:
        s.close()


def _ssdp_locations(timeout: float) -> list[str]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    # A multicastot az internet felé néző kártyán küldjük ki (különben a Windows
    # választhat virtuális adaptert is, pl. WSL / Hyper-V / VPN)
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.connect(("8.8.8.8", 80))
        lan_ip = probe.getsockname()[0]
        probe.close()
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(lan_ip))
        sock.bind((lan_ip, 0))
    except OSError:
        pass
    sock.settimeout(0.5)
    locations: list[str] = []
    def send_all() -> None:
        for st in SEARCH_TARGETS:
            msg = (
                "M-SEARCH * HTTP/1.1\r\n"
                "HOST: 239.255.255.250:1900\r\n"
                'MAN: "ssdp:discover"\r\n'
                "MX: 2\r\n"
                f"ST: {st}\r\n\r\n"
            )
            sock.sendto(msg.encode(), SSDP_ADDR)

    try:
        # Az UDP csomagok elveszhetnek, ezért időnként újraküldjük a keresést
        send_all()
        deadline = time.monotonic() + timeout
        next_resend = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            if time.monotonic() >= next_resend:
                send_all()
                next_resend = time.monotonic() + 1.0
            try:
                data, _ = sock.recvfrom(4096)
            except socket.timeout:
                continue
            for line in data.decode(errors="replace").split("\r\n"):
                if line.lower().startswith("location:"):
                    loc = line.split(":", 1)[1].strip()
                    if loc not in locations:
                        locations.append(loc)
                        # Az első válasz után már csak rövid ideig várunk a többire
                        deadline = min(deadline, time.monotonic() + 0.6)
    finally:
        sock.close()
    return locations


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _services(location: str) -> list[tuple[str, str]]:
    with urllib.request.urlopen(location, timeout=4) as r:
        root = ET.fromstring(r.read())
    base = location
    for el in root.iter():
        if _local(el.tag) == "URLBase" and el.text and el.text.strip():
            base = el.text.strip()
    found = []
    for svc in root.iter():
        if _local(svc.tag) != "service":
            continue
        fields = {_local(c.tag): (c.text or "").strip() for c in svc}
        st = fields.get("serviceType", "")
        if "WANIPConnection" in st or "WANPPPConnection" in st:
            found.append((st, urljoin(base, fields.get("controlURL", ""))))
    # A WANIPConnection a gyakoribb, azt próbáljuk először
    found.sort(key=lambda x: 0 if "WANIPConnection" in x[0] else 1)
    return found


def _soap(gw: Gateway, action: str, args: list[tuple[str, object]], timeout: float = 5) -> dict:
    inner = "".join(f"<{k}>{escape(str(v))}</{k}>" for k, v in args)
    body = (
        '<?xml version="1.0"?>'
        '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
        's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body>'
        f'<u:{action} xmlns:u="{gw.service_type}">{inner}</u:{action}>'
        "</s:Body></s:Envelope>"
    ).encode("utf-8")
    req = urllib.request.Request(
        gw.control_url,
        data=body,
        headers={
            "Content-Type": 'text/xml; charset="utf-8"',
            "SOAPAction": f'"{gw.service_type}#{action}"',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            root = ET.fromstring(r.read())
    except urllib.error.HTTPError as e:
        code, desc = "", ""
        try:
            err = ET.fromstring(e.read())
            for el in err.iter():
                if _local(el.tag) == "errorCode":
                    code = el.text or ""
                elif _local(el.tag) == "errorDescription":
                    desc = el.text or ""
        except ET.ParseError:
            pass
        raise UPnPError(f"{action}: {code} {desc}".strip()) from None
    except (urllib.error.URLError, OSError) as e:
        raise UPnPError(f"{action}: a router nem válaszol ({e})") from None
    return {_local(el.tag): (el.text or "") for el in root.iter() if len(el) == 0}


def discover(timeout: float = 4.0) -> Gateway:
    locations = _ssdp_locations(timeout)
    if not locations:
        raise UPnPError("Nem található UPnP-képes router (lehet, hogy a routeren ki van kapcsolva az UPnP).")
    last_error = None
    for loc in locations:
        try:
            services = _services(loc)
        except (OSError, ET.ParseError, urllib.error.URLError) as e:
            last_error = e
            continue
        host = urlparse(loc).hostname or ""
        try:
            local_ip = _local_ip_towards(host)
        except OSError:
            continue
        candidates = [Gateway(url, st, local_ip) for st, url in services]
        for gw in candidates:
            try:
                if get_external_ip(gw):
                    return gw
            except UPnPError as e:
                last_error = e
        if candidates:
            return candidates[0]
    raise UPnPError(f"A router nem támogatja a port nyitást UPnP-n keresztül. ({last_error or 'nincs WAN szolgáltatás'})")


def discover_upstream(router_ext_ip: str, timeout: float = 3.0) -> Gateway | None:
    """Dupla NAT esetén a router előtti eszköz (pl. szolgáltatói modem) megkeresése.

    A multicast nem jut át a routeren, ezért a modem valószínű címeire közvetlen (unicast)
    keresést küldünk. A modemen nyitott portokat a router külső címére irányítjuk.
    """
    parts = router_ext_ip.split(".")
    if len(parts) != 4:
        return None
    prefix = ".".join(parts[:3])
    hosts = [h for h in (f"{prefix}.1", f"{prefix}.254") if h != router_ext_ip]
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.5)
    locations: list[str] = []
    try:
        for host in hosts:
            for st in ("ssdp:all", "upnp:rootdevice", SEARCH_TARGETS[0]):
                msg = (
                    "M-SEARCH * HTTP/1.1\r\n"
                    f"HOST: {host}:1900\r\n"
                    'MAN: "ssdp:discover"\r\n'
                    "MX: 2\r\n"
                    f"ST: {st}\r\n\r\n"
                )
                try:
                    sock.sendto(msg.encode(), (host, 1900))
                except OSError:
                    pass
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                data, _ = sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                break
            for line in data.decode(errors="replace").split("\r\n"):
                if line.lower().startswith("location:"):
                    loc = line.split(":", 1)[1].strip()
                    if loc not in locations:
                        locations.append(loc)
                        deadline = min(deadline, time.monotonic() + 0.6)
    finally:
        sock.close()
    for loc in locations:
        try:
            services = _services(loc)
        except (OSError, ET.ParseError, urllib.error.URLError):
            continue
        for st, url in services:
            gw = Gateway(url, st, router_ext_ip)
            try:
                get_external_ip(gw)
                return gw
            except UPnPError:
                continue
    return None


def get_external_ip(gw: Gateway) -> str:
    return _soap(gw, "GetExternalIPAddress", []).get("NewExternalIPAddress", "").strip()


def add_port_mapping(gw: Gateway, port: int, protocol: str, description: str) -> None:
    def _add(lease: int) -> None:
        _soap(
            gw,
            "AddPortMapping",
            [
                ("NewRemoteHost", ""),
                ("NewExternalPort", port),
                ("NewProtocol", protocol),
                ("NewInternalPort", port),
                ("NewInternalClient", gw.local_ip),
                ("NewEnabled", 1),
                ("NewPortMappingDescription", description),
                ("NewLeaseDuration", lease),
            ],
        )

    try:
        _add(0)
    except UPnPError as e:
        if "718" in str(e):  # ConflictInMappingEntry: régi szabály, töröljük és újra próbáljuk
            delete_port_mapping(gw, port, protocol)
            _add(0)
            return
        # Néhány router nem fogad el végtelen időtartamot
        try:
            _add(24 * 3600)
        except UPnPError:
            raise e from None


def delete_port_mapping(gw: Gateway, port: int, protocol: str) -> None:
    try:
        _soap(
            gw,
            "DeletePortMapping",
            [("NewRemoteHost", ""), ("NewExternalPort", port), ("NewProtocol", protocol)],
            timeout=3,
        )
    except UPnPError:
        pass
