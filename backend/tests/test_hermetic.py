"""Die Suite darf weder eine Projekt-.env noch Port 11434 noch fremde Hosts erreichen."""
import socket
import subprocess
import sys

import pytest

from net_guard import subprocess_env


def test_subprocess_env_entfernt_dienste_und_behaelt_override(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:11434/v1")
    monkeypatch.setenv("API_TOKEN", "geheim")
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    env = subprocess_env({"LLM_BASE_URL": "http://127.0.0.1:9/v1", "LLM_API_KEY": "dry"})
    assert env["MIROFISH_SKIP_DOTENV"] == "1"
    assert env["MIROFISH_NET_GUARD"] == "1"
    assert env["LLM_BASE_URL"] == "http://127.0.0.1:9/v1"
    assert env["LLM_API_KEY"] == "dry"
    assert "API_TOKEN" not in env
    assert "OLLAMA_HOST" not in env


def test_port_11434_wird_sofort_abgewiesen():
    sock = socket.socket()
    sock.settimeout(1)
    try:
        with pytest.raises(ConnectionRefusedError, match="Hermetischer Test verbietet"):
            sock.connect(("127.0.0.1", 11434))
    finally:
        sock.close()


def test_fremdes_ziel_wird_sofort_abgewiesen():
    sock = socket.socket()
    sock.settimeout(1)
    try:
        with pytest.raises(ConnectionRefusedError, match="Hermetischer Test verbietet"):
            sock.connect(("203.0.113.1", 9))
    finally:
        sock.close()


def test_loopback_anderer_port_bleibt_erlaubt():
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]
    client = socket.socket()
    client.settimeout(2)
    try:
        client.connect(("127.0.0.1", port))
    finally:
        client.close()
        server.close()


def test_kindprozess_blockiert_ollama_port():
    code = (
        "import socket\n"
        "sock = socket.socket()\n"
        "sock.settimeout(1)\n"
        "try:\n"
        "    sock.connect(('127.0.0.1', 11434))\n"
        "except OSError as exc:\n"
        "    print(exc)\n"
        "else:\n"
        "    print('CONNECTED')\n"
    )
    done = subprocess.run(
        [sys.executable, "-c", code], env=subprocess_env(),
        capture_output=True, text=True, timeout=10, check=False,
    )
    assert done.returncode == 0, done.stderr
    assert "Hermetischer Test verbietet" in done.stdout
    assert "CONNECTED" not in done.stdout
