#!/bin/sh
# Erststart: Einstellungen aus der Vorlage anlegen. Ollama läuft auf dem Gastgeber, nicht im Container.
set -e
mkdir -p /app/data/uploads
if [ ! -f /app/data/.env ]; then
  template=/app/.env.example
  [ -f /app/.env.initial ] && template=/app/.env.initial
  sed 's#http://localhost:11434#http://host.docker.internal:11434#g' "$template" > /app/data/.env
  echo "MiroFish: Einstellungen aus .env nach data/.env übernommen."
fi
cd /app/backend
exec .venv/bin/python run.py
