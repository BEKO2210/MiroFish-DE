FROM python:3.11

# Node.js (>=18) und benötigte Werkzeuge installieren
RUN apt-get update \
  && apt-get install -y --no-install-recommends nodejs npm \
  && rm -rf /var/lib/apt/lists/*

# uv aus dem offiziellen uv-Image kopieren
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

WORKDIR /app

# Zuerst die Abhängigkeitsdateien kopieren, um den Build-Cache zu nutzen
COPY package.json package-lock.json ./
COPY frontend/package.json frontend/package-lock.json ./frontend/
COPY backend/pyproject.toml backend/uv.lock ./backend/

# Abhängigkeiten installieren (Node + Python)
RUN npm ci \
  && npm ci --prefix frontend \
  && cd backend && uv sync --frozen

# Projektquellcode kopieren
COPY . .

EXPOSE 3000 5001

# Frontend und Backend gemeinsam starten (Entwicklungsmodus)
CMD ["npm", "run", "dev"]