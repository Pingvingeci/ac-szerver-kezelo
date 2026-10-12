# AC Szerver Kezelő

Windowsos program, amivel pár kattintással összerakhatsz és elindíthatsz egy **Assetto Corsa** dedikált szervert. A szerver mindig annak a gépén fut, aki a programot elindítja, ezért az `.exe` bárkinek átküldhető.

## Mit tud?

- **Összeállítás:** a Pálya és az Autók sávba a **+** gombbal lehet hozzáadni. A választó ablak kereshető, előnézeti képeket mutat, és szűrni lehet benne gyári vagy modolt tartalomra. Autónként beállítható a helyek száma és a skin.
- **Szabályok:** sessionök (szabadedzés, időmérő, verseny körre vagy időre), időjárás, napszak, hőmérséklet, a pálya tapadása, segédletek (ABS, TC stb.), sérülés, üzemanyag- és gumikopás, kötelező boxkiállás.
- **Szerver:** név, jelszó, admin jelszó, portok. A beállítások presetként elmenthetők, és át is küldhetők.
- **Hálózat:**
  - a portokat UPnP-vel automatikusan megnyitja a routeren;
  - felismeri a dupla NAT-ot és a CGNAT-ot;
  - egy gombbal tűzfal szabályt ad hozzá;
  - kívülről teszteli, hogy elérhető-e a szerver;
  - Content Manager meghívó linket és kész meghívó szöveget készít.
- **Napló:** a szerver élő kimenete.

## Ami a futtatáshoz kell

1. Windows 10 vagy 11. A felülethez használt Edge WebView2 ezekben már benne van.
2. Telepített **Assetto Corsa** (Steam).
3. Telepített **Assetto Corsa Dedicated Server**. Steamben: Könyvtár → a lenyíló listában jelöld be az **Eszközök** (Tools) kategóriát → *Assetto Corsa Dedicated Server* → Telepítés. Sok gépen az AC `server` mappájában már eleve megvan.

Pythont nem kell telepíteni, elég az `AC_Szerver_Kezelo.exe`.

## Használat

1. Indítsd el az `AC_Szerver_Kezelo.exe`-t. Az AC mappáját magától megkeresi, és ha nem találja, rákérdez.
2. Az **Összeállítás** oldalon add hozzá a pályát és az autókat a **+** gombbal.
3. Ha kell, állítsd be a szabályokat és a szerver nevét vagy jelszavát.
4. Kattints a **Szerver indítása** gombra.
5. A **Hálózat** oldalon másold ki a meghívó linket, és küldd el a barátaidnak.

## Automatikus hálózatbeállítás

Elég a **Szerver indítása** gombra kattintani, a többi magától lefut:

1. **Tűzfal:** ha a Windows tűzfal be van kapcsolva, és még nincs szabály, hozzáadja. Ezt a Windows egyszer engedélyezteti (UAC).
2. **Port nyitás** a routeren (UPnP). Dupla NAT esetén, ha a szolgáltatói modem is támogatja az UPnP-t, **a modemen is** (a routered felé).
3. **Elérhetőség teszt:** egy értesítés megmondja, hogy a barátaid el tudják-e érni a szervert.

Leállításkor a program minden port nyitást töröl. Csak akkor kell kézzel beállítani valamit, ha a router vagy a modem nem támogatja az UPnP-t, illetve CGNAT esetén (lásd lent).

## Internetes játék: ha a barátok nem tudnak csatlakozni

A **Hálózat** oldal megmondja, mi a helyzet:

| Állapot | Teendő |
|---|---|
| ✔ Minden rendben | Az UPnP megnyitja a portokat, nincs további teendő. |
| ⚠ Dupla NAT | A routered előtt van még egy eszköz (pl. a szolgáltató modemje). A modemen is állíts be port forwardingot a routered felé (**TCP+UDP 9600, TCP 8081**), vagy kapcsold a modemet bridge módba. |
| ✖ CGNAT | A szolgáltatód nem ad saját nyilvános IP-t. Használj VPN-t (Radmin VPN / ZeroTier / Tailscale), vagy kérj nyilvános IP-t a szolgáltatótól. |
| UPnP nem elérhető | Állíts be port forwardingot kézzel a routeren: TCP+UDP 9600 és TCP 8081 a géped helyi IP-jére. |

Mindig érdemes megnyomni a **Tűzfal szabály** gombot. Utána a szerver futása közben az **Elérhetőség teszt** megmondja, hogy kívülről látszik-e a szerver.

Ha modolt autót vagy pályát választasz, azt a barátaidnak is telepíteniük kell.

## Hol vannak a fájlok?

- A program beállításai: `%APPDATA%\ACSzerverKezelo\config.json`
- A szerver konfigurációja: `<AC>\server\cfg\server_cfg.ini` és `entry_list.ini`
- Az eredeti szerver konfiguráció mentése (az első indításkor készül): `<AC>\server\cfg\eredeti_mentes\`
- A szerver naplói: `<AC>\server\logs\session\`

## Telepítés és frissítés

- Töltsd le a legújabb `AC_Szerver_Kezelo_Setup_x.y.z.exe` fájlt a GitHub tároló **Releases** oldaláról, és futtasd.
- A telepítéshez nem kell rendszergazdai jog. Alapból a saját felhasználód `Programs` mappájába telepít, de a helyet szabadon választhatod. Start menü és asztali ikon is készül.
- Ha a Windows azt írja, hogy „A Windows megvédte a számítógépet”, kattints a **További információ**, majd a **Futtatás mindenképp** gombra. A program nincs digitálisan aláírva.
- **Frissítés:** a program induláskor és utána 6 óránként magától megnézi, van-e új verzió. Ha van, felül megjelenik egy sáv: **„Mi változott?”** / **„Frissítés most”**. Frissítéskor letölti a telepítőt, ellenőrzi az ellenőrzőösszegét (SHA-256), telepíti, és újraindul. A beállításaid megmaradnak. Kézzel is kereshetsz: Szerver oldal → *Program* → **Frissítés keresése**.
- **Eltávolítás:** Gépház → Alkalmazások → AC Szerver Kezelő → Eltávolítás.

## Build (.exe és telepítő készítése forrásból)

Python 3.11 vagy újabb kell hozzá, a telepítőhöz pedig Inno Setup 6. A projekt mappájában futtasd:

```
build.bat
```

A kész fájlok: `dist\AC_Szerver_Kezelo.exe` és `dist\AC_Szerver_Kezelo_Setup_<verzió>.exe` (+ `.sha256`).

### Új verzió kiadása

GitHub CLI kell hozzá, bejelentkezve (`gh auth login`):

```
python tools/release.py 1.1.0 "- Új funkció\n- Javítás"
```

Ez beírja a verziószámot, elkészíti a telepítőt, commitol, címkéz, feltölt, és létrehozza a GitHub kiadást. A programok innen találják meg az új verziót.

Fejlesztés közben a forrásból is indítható:

```
pip install -r requirements.txt
python main.py
```

(`python main.py --debug` esetén a böngésző fejlesztői eszközei is elérhetők.)

## Felépítés

```
main.py                  indítófájl (pywebview ablak)
acszerver/api.py         a felület és a Python háttér közötti híd
acszerver/paths.py       az AC és a szerver megkeresése (Steam könyvtárak)
acszerver/content.py     pályák és autók beolvasása, a szerver tartalmának előkészítése
acszerver/config_writer.py   server_cfg.ini és entry_list.ini előállítása
acszerver/server_process.py  az acServer.exe futtatása és leállítása
acszerver/upnp.py        UPnP port nyitás (külső függőség nélkül)
acszerver/network.py     IP-k, CGNAT felismerés, porttesztelés, tűzfal
acszerver/ui/            a felület (HTML / CSS / JS)
tools/make_icon.py       az ikon elkészítése
```
