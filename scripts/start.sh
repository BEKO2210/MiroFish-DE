#!/bin/sh
# Startet MiroFish per Docker. Legt .env und data/ als aktueller Benutzer an, damit Docker
# weder ein Verzeichnis ./.env noch ein root-eigenes data/ erzeugt.
set -e
cd "$(dirname "$0")/.."
[ -f .env ] || cp .env.example .env
mkdir -p data
docker compose up -d --build "$@"
