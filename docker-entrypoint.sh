#!/bin/sh
# Erststart: Einstellungen aus der Vorlage anlegen. Ollama läuft auf dem Gastgeber, nicht im Container.
set -e
mkdir -p /app/data/uploads
if [ ! -f /app/data/.env ]; then
  template=/app/.env.example
  [ -f /app/.env.initial ] && template=/app/.env.initial
  sed -E 's#(localhost|127\.0\.0\.1):11434#host.docker.internal:11434#g' "$template" \
    | { grep -v '^[[:space:]]*FLASK_\(PORT\|HOST\)=' || true; } > /app/data/.env
  echo "MiroFish: Einstellungen aus .env nach data/.env übernommen."
fi
cd /app/backend
exec .venv/bin/python run.py
