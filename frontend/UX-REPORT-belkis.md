# UX-REPORT – belkis (Abschnitt 3.1A, 3.3–3.6, global)

## Änderungen

- **Neu:** `frontend/src/components/MobileStickyBar.vue` – Daumenzonen-Aktionsleiste über dem Fußmenü (Props laut Spezifikation).
- **Startseite (`Home.vue`):** Zweispaltiges Desktop-Layout ab 1024 px; mobil Sticky-Bar für „Vorhersage starten“, Datei-Input mit `label for="doc-upload"`, Safe-Area-Padding, Hero-Typografie `clamp(28px, 7vw, 42px)`, Meta-Text auf Brand-Flächen mit `--color-text-secondary`.
- **Nachbesserung Startseite:** Am Handy/Tablet (≤ 1023 px) per `display: contents` + `order` die Reihenfolge Hero → laufende Durchläufe → Formular „Neue Vorhersage“ → „So funktioniert es“ → „Zuletzt“ → Fußzeile (kein doppeltes Markup); Desktop-Zweispaltigkeit unverändert.
- **Verlauf (`HistoryView.vue`):** Touch-Ziele 48 px, Desktop-Kartenraster, Safe-Area, klarere Aktionsfarben.
- **Einstellungen (`SettingsView.vue`):** Labels/`id`/`aria-label` für Selects und Inputs; Sticky-Bar Speichern/Prüfen; Desktop-Zweispaltengitter.
- **Durchlauf (`RunView.vue`):** Sticky-Bar für Bericht/Simulation; Aktionen mobil ausgeblendet; Safe-Area; `prefers-reduced-motion` für Spinner/Pulse.
- **Global:** `App.vue` unterer Abstand für Fußmenü + Sticky-Bar; `tokens.css` Kontrast Marke/Meta (`#C2410C`, dunkleres `--color-text-muted`) und Reduced-Motion.
- **i18n:** `start.uploadLabel` in `de.json` / `en.json`.
- **E2E:** Mock `pipeline/list` + DELETE-Pipeline; Flow-Test „Abbruch ohne Simulation“; `test.fail`/BEFUNDE für behobene a11y-/Smoke-Fälle Start & Durchlauf entfernt; Visual-Snapshots aktualisiert.

## Abnahme

1. `cd frontend && npx vite build` – ok  
2. `cd e2e && npx playwright test --update-snapshots --grep "Screenshot /$"` – ok (handy/tablet/desktop)  
3. `cd e2e && npx playwright test` – 87 passed  
4. Handy-Snapshot `/`: Reihenfolge Hero → Live → Formular → „So funktioniert es“ → „Zuletzt“ → Fuß bestätigt

## Nicht angefasst

GraphPanel, MainView, SimulationView, SimulationRunView, ReportView, InteractionView, Process, Step*.vue (anderer Agent).
