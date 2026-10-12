"""AC Szerver Kezelő – indítófájl."""
import os
import sys

import webview

from acszerver.api import Api


def resource(rel: str) -> str:
    """Fájl elérési útja fejlesztéskor és a PyInstaller által csomagolt .exe-ben is."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


def main() -> None:
    api = Api()
    window = webview.create_window(
        "AC Szerver Kezelő",
        resource(os.path.join("acszerver", "ui", "index.html")),
        js_api=api,
        width=1360,
        height=880,
        min_size=(1100, 720),
        background_color="#0a0c11",
    )
    api._attach(window)
    window.events.closing += api._on_closing
    try:
        webview.start(gui="edgechromium", debug="--debug" in sys.argv)
    finally:
        api._shutdown()


if __name__ == "__main__":
    main()
