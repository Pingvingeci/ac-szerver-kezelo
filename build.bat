@echo off
setlocal
cd /d "%~dp0"
echo === Fuggosegek telepitese ===
python -m pip install -r requirements.txt || goto :error
echo === Ikon ===
python tools\make_icon.py || goto :error
for /f "usebackq delims=" %%v in (`python -c "from acszerver.version import __version__; print(__version__)"`) do set VERSION=%%v
echo === EXE keszitese (v%VERSION%) ===
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "AC_Szerver_Kezelo" --icon "assets\icon.ico" --add-data "acszerver\ui;acszerver\ui" main.py || goto :error
echo === Telepito keszitese ===
set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
  echo Nincs telepitve az Inno Setup 6 - csak az EXE keszult el.
  goto :done
)
"%ISCC%" /Q /DAppVersion=%VERSION% installer.iss || goto :error
set "SETUP=dist\AC_Szerver_Kezelo_Setup_%VERSION%.exe"
powershell -NoProfile -Command "(Get-FileHash -Algorithm SHA256 '%SETUP%').Hash.ToLower() + '  AC_Szerver_Kezelo_Setup_%VERSION%.exe' | Set-Content -Encoding ascii '%SETUP%.sha256'" || goto :error
echo.
echo Kesz: %SETUP%
:done
if exist build rd /s /q build
if exist AC_Szerver_Kezelo.spec del /q AC_Szerver_Kezelo.spec
goto :eof

:error
echo.
echo HIBA tortent a build kozben.
exit /b 1
