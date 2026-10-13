# UX-REPORT – Cursor Validierung (V1)

## Berichtskopf
- Tag-Text DE/EN: „Szenario-Bericht“ / „Scenario report“ (statt Vorhersage/Forecast).
- Zusätzlicher ruhiger Hinweis: „Szenario aus 1 Lauf“ bzw. „Szenario aus N Läufen“ (`report-run-hint`, Token `--color-text-muted`).

## Methodik-Karte
- Am Ende des Berichtskörpers (`aside.methodology-card`), nur wenn `methodology` vom API kommt und der Bericht fertig ist.
- Token-Farben: `--color-bg-surface-raised`, `--color-border-default`, `--color-text-*`, Heading-Font.
- Inhalt: Disclaimer, Kennzahlen (Läufe, Agenten, Zeit, Plattformen, Modelle, Startbeiträge, Seed, Zeitpunkt), optional „Stand bereits im Material“.

## i18n
- Neue Keys unter `step4.*` in `de.json` / `en.json`.

## E2E
- Report-Fixture um `methodology` ergänzt; Mock liefert das Feld über `GET /api/report/:id`.
- Visuelle Snapshots bei Optikänderung aktualisieren (`PW_PORT=4175 npx playwright test`).

## Abnahme
- `cd frontend && npx vite build`
- `cd e2e && PW_PORT=4175 npx playwright test`
