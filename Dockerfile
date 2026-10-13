# Produktionsbild: Frontend wird gebaut und vom Backend auf einem Port ausgeliefert.
FROM node:20-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npx vite build

FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/
WORKDIR /app

# Python-Abhängigkeiten exakt aus dem Lockfile (eigene Schicht für den Build-Cache)
COPY backend/pyproject.toml backend/uv.lock ./backend/
RUN cd backend && uv sync --frozen --no-dev --no-install-project

COPY backend/ ./backend/
COPY --from=web /web/dist ./frontend/dist
COPY .env.example docker-entrypoint.sh ./

# Daten (Einstellungen, Uploads, Simulationen, Berichte) liegen im Volume /app/data
ENV FLASK_HOST=0.0.0.0 FLASK_PORT=5001 FLASK_DEBUG=false PYTHONUNBUFFERED=1
EXPOSE 5001
ENTRYPOINT ["sh", "/app/docker-entrypoint.sh"]
