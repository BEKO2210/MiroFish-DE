"""Docker-Start für Fremde: Loopback-Ersetzung im Entrypoint, LF-Zeilenenden, UID-Ermittlung."""
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_entrypoint_ersetzt_localhost_und_loopback_ip():
    zeile = next(l for l in (ROOT / "docker-entrypoint.sh").read_text().splitlines() if l.lstrip().startswith("sed -E"))
    ausdruck = re.search(r"sed -E '([^']+)'", zeile).group(1)
    eingabe = "A=http://localhost:11434/v1\nB=http://127.0.0.1:11434/v1\nC=http://example.com:11434\n"
    ausgabe = subprocess.run(["sed", "-E", ausdruck], input=eingabe, capture_output=True, text=True, check=True).stdout
    assert ausgabe == (
        "A=http://host.docker.internal:11434/v1\n"
        "B=http://host.docker.internal:11434/v1\n"
        "C=http://example.com:11434\n"
    )


def test_gitattributes_erzwingt_lf_fuer_shellskripte():
    regeln = (ROOT / ".gitattributes").read_text().splitlines()
    assert "*.sh text eol=lf" in regeln
    for skript in ("scripts/start.sh", "docker-entrypoint.sh"):
        assert b"\r" not in (ROOT / skript).read_bytes()


def test_start_sh_setzt_uid_dynamisch(tmp_path):
    wurzel = tmp_path / "r"
    (wurzel / "scripts").mkdir(parents=True)
    (wurzel / "scripts" / "start.sh").write_text((ROOT / "scripts/start.sh").read_text())
    (wurzel / ".env.example").write_text("# MIROFISH_UID=1000\n")
    bin_ = tmp_path / "bin"
    bin_.mkdir()
    docker = bin_ / "docker"
    docker.write_text('#!/bin/sh\necho "$MIROFISH_UID:$MIROFISH_GID" > "$OUT"\n')
    docker.chmod(0o755)
    out = tmp_path / "out"
    env = {**os.environ, "PATH": f"{bin_}:{os.environ['PATH']}", "OUT": str(out)}
    env.pop("MIROFISH_UID", None)
    env.pop("MIROFISH_GID", None)
    subprocess.run(["sh", str(wurzel / "scripts" / "start.sh")], env=env, check=True)
    assert out.read_text().strip() == f"{os.getuid()}:{os.getgid()}"
    (wurzel / ".env").write_text("MIROFISH_UID=4242\nMIROFISH_GID=4343\n")
    subprocess.run(["sh", str(wurzel / "scripts" / "start.sh")], env=env, check=True)
    assert out.read_text().strip() == "4242:4343"
