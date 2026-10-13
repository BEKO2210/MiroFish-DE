# UX-REPORT – Cursor Live (Audit-2 Nacharbeit)

Kurzliste der Änderungen nach Live-Abnahme mit echten Daten.

## Handy: Seiten-Scroll statt Innen-Scroll (Schritt-Seiten)
- `MainView`, `SimulationView`, `SimulationRunView`, `ReportView`, `InteractionView`: am Handy (`≤768px`) keine feste `main-view`-Höhe mehr; `content-area` / `panel-wrapper` `height: auto`, `overflow: visible`, `will-change: auto`.
- Kopf (`StepHeaderCompact` + Graph/Arbeitsbereich) `flex-shrink: 0`, vollständig sichtbar, sticky.
- `Step1`–`Step5`: Hauptpanels ohne inneren `overflow-y`-Scroll am Handy; unterer Abstand = StickyBar + Fußmenü + Safe-Area.
- `MobileStickyBar`: `Teleport` nach `body` (fixed hängt nicht mehr an Panel-`transform`/`will-change`) → sitzt direkt über dem Fußmenü.
- `tokens.css`: `body`-Padding am Handy nach dem Reset (`padding: 0` hatte App.vue überschrieben).

## Texte
- „Tiefeninteraktion“ / „Tiefe Interaktion“ → DE **Nachfragen stellen**, EN **Ask follow-up questions** (`de.json` / `en.json`).

## E2E
- `smoke.spec.ts`: Handy-Checks für `/report/...` und `/interaction/...` (Seiten-Scroll, kein Inner-Overflow, letzter Absatz über StickyBar).
- Mock `agent-log` liefert Outline/Abschnitte aus Report-Fixture (vorher leer → kein Inhalt).
- Visuelle Snapshots aktualisiert (Handy/Tablet/Desktop wo betroffen).

## Abnahme
- `cd frontend && npx vite build` – ok
- `cd e2e && npx playwright test` – grün (bekanntes a11y `test.fail` Report Desktop bleibt in BEFUNDE.md)
