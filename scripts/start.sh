#!/bin/sh
# Startet MiroFish per Docker. Legt .env und data/ als aktueller Benutzer an, damit Docker
# weder ein Verzeichnis ./.env noch ein root-eigenes data/ erzeugt.
set -e
cd "$(dirname "$0")/.."
[ -f .env ] || cp .env.example .env
mkdir -p data
# UID/GID des aktuellen Benutzers verwenden (macOS: 501, Mehrbenutzer-Linux), außer sie sind in .env oder der Umgebung gesetzt.
env_val() { sed -n "s/^$1=\([0-9][0-9]*\).*/\1/p" .env | tail -n 1; }
export MIROFISH_UID="${MIROFISH_UID:-$(env_val MIROFISH_UID)}"
export MIROFISH_GID="${MIROFISH_GID:-$(env_val MIROFISH_GID)}"
export MIROFISH_UID="${MIROFISH_UID:-$(id -u)}"
export MIROFISH_GID="${MIROFISH_GID:-$(id -g)}"
docker compose up -d --build "$@"
