from __future__ import annotations

import socket
import subprocess
import threading
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


DEFAULT_READINESS_TIMEOUT_SECONDS = 5.0
DEFAULT_POLL_INTERVAL_SECONDS = 0.05


@dataclass
class ReadinessConfig:
    mode: str
    port: int | None = None
    marker: str | None = None
    timeout_seconds: float = DEFAULT_READINESS_TIMEOUT_SECONDS
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS


@dataclass
class StreamState:
    stdout_lines: deque[str]
    stderr_lines: deque[str]
    stdout_thread: threading.Thread | None
    stderr_thread: threading.Thread | None


def infer_readiness_config(runtime_section: dict) -> ReadinessConfig:
    """Infer readiness behavior from runtime settings.

    Priority:
    1. Explicit readiness_probe settings.
    2. Fallback to TCP when runtime.port is configured.
    3. Otherwise immediate-ready mode.
    """
    readiness_probe = runtime_section.get("readiness_probe")
    if isinstance(readiness_probe, dict):
        method = readiness_probe.get("method")
        if method == "tcp":
            port = readiness_probe.get("port")
            if isinstance(port, int) and port > 0:
                return ReadinessConfig(mode="tcp", port=port)
        if method == "stdout":
            marker = readiness_probe.get("marker")
            if isinstance(marker, str) and marker.strip():
                return ReadinessConfig(mode="stdout", marker=marker)

    runtime_port = runtime_section.get("port")
    if isinstance(runtime_port, int) and runtime_port > 0:
        return ReadinessConfig(mode="tcp", port=runtime_port)

    return ReadinessConfig(mode="immediate")


def start_server(
    command: list[str],
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.Popen[str]:
    return subprocess.Popen(
        command,
        cwd=str(cwd) if cwd is not None else None,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )


def _stream_pipe(
    pipe,
    sink: deque[str],
    callback: Callable[[str], None] | None,
) -> None:
    if pipe is None:
        return
    for line in iter(pipe.readline, ""):
        sink.append(line)
        if callback is not None:
            callback(line)
    pipe.close()


def stream_output(
    process: subprocess.Popen[str],
    stdout_callback: Callable[[str], None] | None = None,
    stderr_callback: Callable[[str], None] | None = None,
) -> StreamState:
    stdout_lines: deque[str] = deque(maxlen=1024)
    stderr_lines: deque[str] = deque(maxlen=1024)

    stdout_thread: threading.Thread | None = None
    stderr_thread: threading.Thread | None = None

    if process.stdout is not None:
        stdout_thread = threading.Thread(
            target=_stream_pipe,
            args=(process.stdout, stdout_lines, stdout_callback),
            daemon=True,
        )
        stdout_thread.start()

    if process.stderr is not None:
        stderr_thread = threading.Thread(
            target=_stream_pipe,
            args=(process.stderr, stderr_lines, stderr_callback),
            daemon=True,
        )
        stderr_thread.start()

    return StreamState(
        stdout_lines=stdout_lines,
        stderr_lines=stderr_lines,
        stdout_thread=stdout_thread,
        stderr_thread=stderr_thread,
    )


def _is_tcp_ready(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def wait_until_ready(
    process: subprocess.Popen[str],
    readiness: ReadinessConfig,
    stream_state: StreamState | None = None,
) -> bool:
    if readiness.mode == "immediate":
        return True

    start_time = time.monotonic()
    timeout_seconds = max(0.0, readiness.timeout_seconds)
    poll_interval = max(0.01, readiness.poll_interval_seconds)

    while (time.monotonic() - start_time) <= timeout_seconds:
        if process.poll() is not None:
            return False

        if readiness.mode == "tcp":
            if isinstance(readiness.port, int) and readiness.port > 0 and _is_tcp_ready(readiness.port):
                return True

        elif readiness.mode == "stdout":
            if stream_state is None:
                return False
            marker = readiness.marker or ""
            if marker and any(marker in line for line in stream_state.stdout_lines):
                return True

        time.sleep(poll_interval)

    return False


def shutdown_server(process: subprocess.Popen[str], timeout_seconds: float = 3.0) -> int:
    """Attempt graceful termination first, then force kill if needed."""
    if process.poll() is not None:
        return int(process.returncode or 0)

    process.terminate()
    try:
        return process.wait(timeout=max(0.1, timeout_seconds))
    except subprocess.TimeoutExpired:
        process.kill()
        return process.wait()