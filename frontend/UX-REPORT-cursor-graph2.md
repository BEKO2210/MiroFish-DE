# UX-Report: Graph-Höhe mobil (Seiten-Scroll-Regression)

## Problem
Nach der Umstellung auf Seiten-Scroll am Handy (`height: auto` auf `.main-view` / `.panel-wrapper`) hatte das Graph-Panel nur noch `min-height`. Prozent-Höhen (`height: 100%`) am `.graph-panel` / `.graph-container` kollabierten → D3 zeichnete in ~150 px; Knoten klebten oben, darunter leerer Streifen.

## Änderungen

### Schritt-Views (`MainView`, `SimulationView`, `SimulationRunView`, `ReportView`, `InteractionView`)
Am Handy (≤ 768 px) hat `.panel-wrapper.left` jetzt eine **feste** Höhe:
`height: calc(100dvh - 168px - 64px - 58px - env(safe-area-inset-bottom, 0px))` (Kopf / StickyBar / Fußmenü), `min-height: 420px`, `overflow: hidden`. Tablet/Desktop unverändert.

### `GraphPanel.vue`
- Mobil: `.graph-panel` / `.graph-container` füllen die Panel-Höhe (`height: 100%`, `min-height: 420px`).
- `ResizeObserver`: bei Größenänderung mit bereits gezeichnetem Graph → SVG-Maße + `zoomToFit` (ohne neue Force-Simulation); sonst `renderGraph`.

### E2E
- `mockApi.ts`: Graph-Fixture mit 10 Knoten / 8 Kanten im Backend-Format (`uuid`, `source_node_uuid`, …).
- `smoke.spec.ts`: Test handy+tablet für `/process/…?view=graph` (Canvas ≥ 400 px, Knotenspread > 30 % der Höhe).
- `visual.spec.ts`: Snapshot Graph-Ansicht am Handy (`process-graph-view-handy-handy-linux.png`).

## Gegenprobe
Mit altem `min-height: calc(100dvh - 200px)` schlägt der neue Smoke-Test fehl (`canvasH: 150`). Mit Fix grün.

## Abnahme
1. `cd frontend && npx vite build` — OK.
2. `cd e2e && npx playwright test` — 95 passed, 7 skipped (kein neuer BEFUNDE-Eintrag; Desktop-Report-a11y weiter als bekannter `test.fail`).
3. Snapshot Graph-Ansicht handy geprüft: Zeichenfläche nutzt den Viewport, Knoten verteilt.
