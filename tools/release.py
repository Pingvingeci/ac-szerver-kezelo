"""Új verzió kiadása a GitHubra.

Használat:
  python tools/release.py 1.1.0 "Mi változott: ...\n- új funkció\n- javítás"

Lépések: verziószám beírása -> build.bat (exe + telepítő + sha256) -> git commit és címke
-> feltöltés -> GitHub kiadás a telepítővel. A programok induláskor ezt a kiadást találják meg.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = ROOT / "acszerver" / "version.py"


def run(*cmd: str, capture: bool = False) -> str:
    print(">", " ".join(cmd))
    res = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=capture)
    if res.returncode != 0:
        if capture:
            print(res.stdout, res.stderr)
        raise SystemExit(f"Hiba: {' '.join(cmd)}")
    return (res.stdout or "").strip()


def tool(name: str, fallback: str) -> str:
    return shutil.which(name) or fallback


def main() -> None:
    if len(sys.argv) < 3 or not re.fullmatch(r"\d+\.\d+\.\d+", sys.argv[1]):
        print(__doc__)
        raise SystemExit(1)
    version, notes = sys.argv[1], sys.argv[2].replace("\\n", "\n")
    git = tool("git", r"C:\Program Files\Git\cmd\git.exe")
    gh = tool("gh", r"C:\Program Files\GitHub CLI\gh.exe")

    run(gh, "auth", "status", capture=True)
    if run(git, "status", "--porcelain", capture=True):
        raise SystemExit("Vannak nem commitolt változások. Előbb commitold őket.")

    text = VERSION_FILE.read_text(encoding="utf-8")
    VERSION_FILE.write_text(re.sub(r'__version__ = "[^"]*"', f'__version__ = "{version}"', text), encoding="utf-8")

    run("cmd", "/c", str(ROOT / "build.bat"))
    setup = ROOT / "dist" / f"AC_Szerver_Kezelo_Setup_{version}.exe"
    sha = setup.with_name(setup.name + ".sha256")
    if not setup.is_file() or not sha.is_file():
        raise SystemExit("Nem készült el a telepítő.")

    tag = f"v{version}"
    run(git, "add", "-A")
    if run(git, "status", "--porcelain", capture=True):
        run(git, "commit", "-m", f"Kiadás: {tag}")
    run(git, "tag", tag)
    run(git, "push")
    run(git, "push", "origin", tag)
    run(gh, "release", "create", tag, str(setup), str(sha), "--title", tag, "--notes", notes)
    print(f"\nKész: {tag} kiadva.")


if __name__ == "__main__":
    main()
