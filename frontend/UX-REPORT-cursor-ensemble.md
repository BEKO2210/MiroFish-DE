# UX-REPORT – Cursor Ensemble (Mehrfachlauf)

## Auftrag A – Mehrfachlauf
- API: `frontend/src/api/ensemble.js` (start, get, list, cancel, delete).
- Seite: `frontend/src/views/EnsembleView.vue`, Route `/ensemble/:ensembleId` — Fortschritt, Ergebnis-Tabelle (Desktop) / Karten (Handy), Comparisons, CI-Erklärung, Abbrechen/Löschen.
- Start in `Step4Report.vue`: Aktionsknopf + ConfirmSheet (Läufe 5/10/20, Stunden, Varianten), Navigation nach Start; Liste unter Methodik-Karte.
- i18n: Namespace `ensemble.*` in `de.json` / `en.json`; Farben nur Tokens; Touch ≥ 44 px; MobileStickyBar.

## Auftrag B – Befunde
- iPhone-HScroll: Ursache `min-width: 450px` + Action-Bar-Zeile; behoben in `Step5Interaction.vue` / `InteractionView.vue`; `IPHONE_HSCROLL` und BEFUNDE-Eintrag entfernt.
- Methodik: `already_in_material` mit claim/text, source, overlap/coverage, snippet, count.
- Markdown: Standalone-`**…**` → `h4`; Inline-`**…**` bleibt `<strong>`; CSS „strong als Überschrift“ entfernt.
- E2E: Mock `/api/ensemble/*`, Route `/ensemble/ens_test`, Flow „Mehrfachlauf starten“; `./docker-test.sh` grün (137 passed, inkl. iPhone ohne HScroll).
- `cd frontend && npx vite build` fehlerfrei.
