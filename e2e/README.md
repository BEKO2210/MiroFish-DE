# MiroFish E2E (Playwright)

TypeScript-Suite unter `e2e/`, die das gebaute Frontend (`vite preview` auf Port 4173) gegen JSON-Fixtures in `e2e/fixtures/` prüft. Abhängigkeiten liegen nur hier – nicht unter `frontend/` installieren (`frontend/node_modules` ist ein Verweis auf ein anderes Repo).

## Voraussetzungen

- Node 20+
- Chromium für Playwright (lokal oft schon unter `~/.cache/ms-playwright`)
- Optional WebKit für das Projekt **iphone** (`npx playwright install webkit`). Fehlen Host-Bibliotheken, läuft die Suite nur mit Chromium; Status steht in `webkit-status.txt`.

```bash
cd e2e
npm ci          # oder npm install
npx playwright install chromium   # falls nötig
npx playwright install webkit     # optional, iPhone/Safari
```

## Tests starten (Mock-Modus)

Baut das Frontend, startet Preview und mockt alle `/api/*`-Aufrufe:

```bash
cd e2e
npm test
```

Projekte: **handy** (Galaxy-S23-Ultra-Viewport), **iphone** (WebKit, falls startbar), **tablet**, **desktop**. Locale `de-DE`, Zeitzone `Europe/Berlin`, feste Uhrzeit für stabile Screenshots.

## Snapshots aktualisieren

Nach bewussten UI-Änderungen Referenzbilder neu erzeugen:

```bash
cd e2e
npm run test:update
```

Entspricht `playwright test --update-snapshots`. Visual-Tests liegen in `tests/visual.spec.ts` (`fullPage`, Masken für `canvas.swarm` und Zeitangaben, `maxDiffPixelRatio: 0.01`).

## Live gegen eine laufende Instanz

Ohne Mocks, nur Smoke-Tests:

```bash
cd e2e
LIVE_BASE_URL=https://beispiel.example npm run test:live
```

`webServer` entfällt; die Suite ruft die gesetzte Basis-URL auf.

## Bekannte App-Fehler

Echte Frontend-Bugs werden nicht durch gelockerte Assertions versteckt. Sie stehen in [`BEFUNDE.md`](./BEFUNDE.md); der betroffene Test ist mit `test.fail()` markiert („bekannter Fehler, siehe BEFUNDE.md“). Ziel: Suite grün inklusive markierter bekannter Fehler.

Nach jedem Lauf schreibt die Config den WebKit-Status nach `webkit-status.txt` (lokal gitignored).

## CI

Workflow: `.github/workflows/e2e.yml` – `npm ci` in `frontend` und `e2e`, Playwright Chromium+WebKit, `npm test` in `e2e`, bei Fehler Report-Artefakt.
