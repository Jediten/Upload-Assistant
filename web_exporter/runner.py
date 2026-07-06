"""Upload subprocess management.

Handles start/stop/stream of upload.py subprocess with Windows Job Object
support and thread safety.
"""

import os
import shlex
import subprocess
import sys
import threading
import urllib.parse
from typing import Optional, Generator

from .config import BASE_DIR


class UploadRunner:
    """Manages the upload.py subprocess lifecycle."""

    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._process is not None and self._process.poll() is None

    # ──────────────── Process Lifecycle ────────────────

    def start(self, args_str: str) -> subprocess.Popen:
        """Start upload.py with piped I/O for web streaming.

        Returns the Popen process handle.
        Raises RuntimeError if a process is already running.
        """
        with self._lock:
            if self._process and self._process.poll() is None:
                raise RuntimeError("Upload process is already running")

        user_args = shlex.split(args_str)
        upload_script = os.path.join(BASE_DIR, "upload.py")
        full_command = [sys.executable, "-u", upload_script] + user_args

        process = subprocess.Popen(
            full_command,
            cwd=BASE_DIR,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )

        # Windows: attach to Job Object so child dies when parent dies
        self._attach_job_object(process)

        with self._lock:
            self._process = process

        return process

    def start_detached(self, args_str: str) -> None:
        """Start upload.py in a detached window (Windows CMD) or background (Unix)."""
        user_args = shlex.split(args_str)
        upload_script = os.path.join(BASE_DIR, "upload.py")

        if os.name == "nt":
            inner_cmd = subprocess.list2cmdline(
                [sys.executable, "-u", upload_script] + user_args
            )
            start_cmd = [
                "cmd", "/c", "start",
                "Upload Assistant",
                "/D", BASE_DIR,
                "cmd", "/k", inner_cmd,
            ]
            subprocess.Popen(
                start_cmd,
                cwd=BASE_DIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
            )
        else:
            subprocess.Popen(
                [sys.executable, "-u", upload_script] + user_args,
                cwd=BASE_DIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )

    def stop(self) -> bool:
        """Stop the running upload process. Returns True if a process was stopped."""
        with self._lock:
            proc = self._process
            self._process = None

        if proc is None:
            return False

        try:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
        except Exception:
            pass

        return True

    def send_stdin(self, line: str) -> None:
        """Send a line of text to the running process's stdin.

        Raises RuntimeError if no process is running.
        """
        with self._lock:
            proc = self._process

        if proc is None:
            raise RuntimeError("No upload process running")
        if proc.poll() is not None:
            raise RuntimeError("Process already finished")

        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def stream_output(self, args_str: str) -> Generator[str, None, None]:
        """Start process and yield SSE-formatted lines.

        Each yielded string is a complete SSE data line ready to send.
        """
        try:
            process = self.start(args_str)

            for line in process.stdout:
                if line:
                    safe_line = urllib.parse.quote(line.rstrip("\n"))
                    yield f"data: {safe_line}\n\n"

            process.stdout.close()
            process.wait()

            with self._lock:
                self._process = None

            if process.returncode == 0:
                yield "data: [PROCESS_COMPLETE]\n\n"
            else:
                yield "data: [PROCESS_ERROR]\n\n"

        except Exception as e:
            with self._lock:
                self._process = None
            err_line = urllib.parse.quote(f"Server Error: {str(e)}")
            yield f"data: {err_line}\n\n"
            yield "data: [PROCESS_ERROR]\n\n"

    def cleanup(self) -> None:
        """Kill upload process (for use in atexit/signal handlers)."""
        self.stop()

    # ──────────────── Private ────────────────

    @staticmethod
    def _attach_job_object(process: subprocess.Popen) -> None:
        """Windows: assign process to a Job Object with KILL_ON_JOB_CLOSE."""
        if os.name != "nt":
            return
        try:
            import ctypes
            from ctypes import wintypes

            kernel32 = ctypes.windll.kernel32
            JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
            JobObjectBasicLimitInformation = 2

            hJob = kernel32.CreateJobObjectW(None, None)
            if hJob:
                kernel32.AssignProcessToJobObject(hJob, process._handle)

                class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
                    _fields_ = [
                        ("PerProcessUserTimeLimit", wintypes.LARGE_INTEGER),
                        ("PerJobUserTimeLimit", wintypes.LARGE_INTEGER),
                        ("LimitFlags", wintypes.DWORD),
                        ("MinWorkingSetSize", ctypes.c_void_p),
                        ("MaxWorkingSetSize", ctypes.c_void_p),
                        ("ActiveProcessLimit", wintypes.DWORD),
                        ("Affinity", ctypes.c_void_p),
                        ("PriorityClass", wintypes.DWORD),
                        ("SchedulingClass", wintypes.DWORD),
                    ]

                info = JOBOBJECT_BASIC_LIMIT_INFORMATION()
                info.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
                kernel32.SetInformationJobObject(
                    hJob,
                    JobObjectBasicLimitInformation,
                    ctypes.byref(info),
                    ctypes.sizeof(info),
                )
        except Exception:
            pass
