"""Az acServer.exe futtatása, kimenetének olvasása és leállítása."""
from __future__ import annotations

import ctypes
import subprocess
import threading
import time
from ctypes import wintypes
from pathlib import Path
from typing import Callable

CREATE_NO_WINDOW = 0x08000000


class _JobObject:
    """Windows Job Object: ha a program összeomlik vagy bezárják, az acServer.exe is leáll."""

    def __init__(self) -> None:
        self.handle = None
        try:
            k32 = ctypes.WinDLL("kernel32", use_last_error=True)

            class BASIC(ctypes.Structure):
                _fields_ = [
                    ("PerProcessUserTimeLimit", ctypes.c_int64),
                    ("PerJobUserTimeLimit", ctypes.c_int64),
                    ("LimitFlags", wintypes.DWORD),
                    ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t),
                    ("ActiveProcessLimit", wintypes.DWORD),
                    ("Affinity", ctypes.c_size_t),
                    ("PriorityClass", wintypes.DWORD),
                    ("SchedulingClass", wintypes.DWORD),
                ]

            class IO(ctypes.Structure):
                _fields_ = [(n, ctypes.c_uint64) for n in ("a", "b", "c", "d", "e", "f")]

            class EXTENDED(ctypes.Structure):
                _fields_ = [
                    ("BasicLimitInformation", BASIC),
                    ("IoInfo", IO),
                    ("ProcessMemoryLimit", ctypes.c_size_t),
                    ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t),
                    ("PeakJobMemoryUsed", ctypes.c_size_t),
                ]

            k32.CreateJobObjectW.restype = wintypes.HANDLE
            k32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
            k32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
            k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
            handle = k32.CreateJobObjectW(None, None)
            info = EXTENDED()
            info.BasicLimitInformation.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if handle and k32.SetInformationJobObject(handle, 9, ctypes.byref(info), ctypes.sizeof(info)):
                self.handle = handle
                self._k32 = k32
        except (OSError, AttributeError):
            self.handle = None

    def assign(self, proc: subprocess.Popen) -> None:
        if self.handle:
            self._k32.AssignProcessToJobObject(self.handle, wintypes.HANDLE(int(proc._handle)))


class ServerProcess:
    def __init__(self, on_line: Callable[[str], None], on_exit: Callable[[int], None]) -> None:
        self.on_line = on_line
        self.on_exit = on_exit
        self.proc: subprocess.Popen | None = None
        self._job = _JobObject()
        self._stopping = False

    @property
    def running(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def start(self, server_dir: Path) -> None:
        if self.running:
            raise RuntimeError("A szerver már fut.")
        exe = server_dir / "acServer.exe"
        log_dir = server_dir / "logs" / "session"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / time.strftime("output_%Y%m%d_%H%M%S.log")
        self._stopping = False
        self.proc = subprocess.Popen(
            [str(exe)],
            cwd=str(server_dir),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=CREATE_NO_WINDOW,
        )
        self._job.assign(self.proc)
        threading.Thread(target=self._reader, args=(self.proc, log_path), daemon=True).start()

    def _reader(self, proc: subprocess.Popen, log_path: Path) -> None:
        try:
            with open(log_path, "w", encoding="utf-8") as log:
                assert proc.stdout is not None
                for raw in iter(proc.stdout.readline, b""):
                    line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
                    log.write(line + "\n")
                    log.flush()
                    self.on_line(line)
        except OSError:
            pass
        code = proc.wait()
        self.on_exit(code if not self._stopping else 0)

    def stop(self, timeout: float = 5.0) -> None:
        if not self.running:
            return
        self._stopping = True
        assert self.proc is not None
        self.proc.terminate()
        try:
            self.proc.wait(timeout)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(3)
