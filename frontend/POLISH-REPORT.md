# Polish-Report

Stand: 2026-10-13. Worktree `mirofish-polish` only.

## Geändert

| Datei | Kurz |
|---|---|
| `frontend/src/components/Step3Simulation.vue` | `isFailed` vor Complete; Log, Phase 2, Polling stop, Status `error` |
| `frontend/src/components/Step2EnvSetup.vue` | `handlePrepareFailure`; failed-Zweige in Prepare/Config/Load; Profiles ohne `'reddit'` |
| `frontend/src/api/simulation.js` | `platform` nur noch optional mitschicken (Profiles/Posts) |
| `frontend/src/components/Step5Interaction.vue` | Chat-History `.slice(0, -1)`; Profiles ohne `'reddit'` |
| `frontend/src/api/index.js` | HTTP-Fehlertext aus `response.data.error/message` in `error.message` |
| `frontend/src/views/RunView.vue` | „Wissensgraph ansehen“ bei `project_id`, Ziel `?view=graph` |
| `frontend/src/views/HistoryView.vue` | Aktion „Graph“ mit Knoten-SVG → `/process/<project_id>?view=graph` |
| `frontend/src/views/MainView.vue` | `route.query.view === 'graph'` setzt `viewMode` auf `graph` |
| `frontend/src/i18n/de.json` / `en.json` | `step3.simulationFehlgeschlagen`, `hist.graph`, `hist.graphTitle` |
| `frontend/package.json` | axios `^1.18.1`, vite `^7.3.6`; Symlink `node_modules` entfernt, neu installiert |
| `package.json` (Wurzel) | concurrently `^9.2.4` |

## Checks

- `cd frontend && npx vite build` — ok (vite 7.3.7)
- `cd backend && python3 -m compileall -q app` — ok

## npm audit (`cd frontend && npm audit --omit=dev`)

Installiert u. a.: axios **1.20.0**, vite **7.3.7**.

Ergebnis: **5 high**, 0 critical/moderate/low.

| Paket | Severity | Hinweis |
|---|---|---|
| `vue` / `@vue/server-renderer` | high | XSS (GHSA-g2v6-rqmx-r4w6), Fix via `npm audit fix` |
| `nanoid` | high | transitiv |
| `postcss` | high | transitiv |
| `source-map-js` | high | transitiv |

Wurzel (`concurrently`): nach `npm install` **0** Vulnerabilities.

## Offen

- `npm audit fix` für vue/transitiv nicht ausgeführt (nur Versionsbump axios/vite/concurrently laut Auftrag).
- Punkt 4 bleibt bewusst unberührt.
