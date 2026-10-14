"""Testprozesse: Dienstervariablen entfernen, Netz nur lokal und nie auf Port 11434."""
import errno
import ipaddress
import os
import socket
from pathlib import Path

GUARD_DIR = Path(__file__).resolve().parent

_KEEP = {"MIROFISH_SKIP_DOTENV", "MIROFISH_NET_GUARD"}
_PREFIXES = (
    "LLM_",
    "LOCAL_LLM_",
    "ZEP_",
    "FLASK_",
    "OLLAMA_",
    "OPENAI_",
    "ENSEMBLE_",
    "OASIS_",
    "OBSIDIAN_",
    "HYBRID_",
    "MEMORY_",
    "REPORT_AGENT_",
    "CORS_",
)
_EXACT = {"API_TOKEN", "UPLOAD_FOLDER", "SECRET_KEY"}


def _drop(key: str) -> bool:
    if key in _KEEP:
        return False
    if key in _EXACT or key.startswith(_PREFIXES) or key.startswith("MIROFISH_"):
        return True
    lowered = key.lower()
    return lowered == "no_proxy" or lowered.endswith("_proxy")


def _ensure_pythonpath(env) -> None:
    # Kindprozesse importieren app aus dem Quellbaum, nicht aus einem alten Install.
    backend = str(GUARD_DIR.parent.parent)
    guard = str(GUARD_DIR)
    parts = [part for part in env.get("PYTHONPATH", "").split(os.pathsep) if part and part not in {guard, backend}]
    env["PYTHONPATH"] = os.pathsep.join([guard, backend, *parts])


def scrub(env) -> None:
    """Entfernt Dienstervariablen und setzt die Test-Schalter."""
    for key in list(env):
        if _drop(key):
            del env[key]
    env["MIROFISH_SKIP_DOTENV"] = "1"
    env["MIROFISH_NET_GUARD"] = "1"
    env["NO_PROXY"] = "*"
    _ensure_pythonpath(env)


def subprocess_env(overrides=None) -> dict:
    """Kopie der Prozessumgebung ohne Dienstervariablen; overrides gewinnen danach."""
    env = dict(os.environ)
    scrub(env)
    if overrides:
        env.update(overrides)
    env["MIROFISH_SKIP_DOTENV"] = "1"
    env["MIROFISH_NET_GUARD"] = "1"
    _ensure_pythonpath(env)
    return env


def _loopback(host) -> bool:
    text = str(host or "").strip().strip("[]").split("%", 1)[0].lower()
    if text in {"localhost", "127.0.0.1", "::1"}:
        return True
    try:
        return ipaddress.ip_address(text).is_loopback
    except ValueError:
        return False


def _blocked(address):
    if isinstance(address, (str, bytes)) or not isinstance(address, tuple) or len(address) < 2:
        return None
    host, port = address[0], address[1]
    try:
        port_n = int(port)
    except (TypeError, ValueError):
        return f"Hermetischer Test verbietet Verbindung nach {address!r}"
    if port_n == 11434:
        return f"Hermetischer Test verbietet Port 11434 ({host})"
    if not _loopback(host):
        return f"Hermetischer Test verbietet nicht-lokales Ziel {host}:{port_n}"
    return None


def install() -> None:
    """socket.connect bricht fremde Ziele und Port 11434 sofort ab."""
    if getattr(socket.socket.connect, "_mirofish_hermetic", False):
        return
    original = socket.socket.connect
    original_ex = socket.socket.connect_ex

    def connect(self, address):
        reason = _blocked(address)
        if reason:
            raise ConnectionRefusedError(errno.ECONNREFUSED, reason)
        return original(self, address)

    def connect_ex(self, address):
        reason = _blocked(address)
        if reason:
            return errno.ECONNREFUSED
        return original_ex(self, address)

    connect._mirofish_hermetic = True
    socket.socket.connect = connect
    socket.socket.connect_ex = connect_ex
