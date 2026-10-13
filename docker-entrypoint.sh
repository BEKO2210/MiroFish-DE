#!/bin/sh
# Erststart: Einstellungen aus der Vorlage anlegen. Ollama läuft auf dem Gastgeber, nicht im Container.
set -e
mkdir -p /app/data/uploads
if [ ! -f /app/data/.env ]; then
  sed 's#http://localhost:11434#http://host.docker.internal:11434#g' /app/.env.example > /app/data/.env
  echo "MiroFish: Einstellungen angelegt unter data/.env – Modell in der App unter Einstellungen wählen."
fi
ln -sf /app/data/.env /app/.env
[ -L /app/backend/uploads ] || { rm -rf /app/backend/uploads; ln -s /app/data/uploads /app/backend/uploads; }
cd /app/backend
exec .venv/bin/python run.py
