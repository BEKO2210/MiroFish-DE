# UX-REPORT – Cursor v3b (custom_outcomes + reliability)

## Auftrag
- Startdialog: `Step4Report.vue` ConfirmSheet – Abschnitt „Eigene Fragen (optional)“ (max. 6, ≤200 Zeichen, Polarity tritt ein/bleibt aus), POST `custom_outcomes`.
- Ergebnisseite: `EnsembleView.vue` – Zuverlässigkeits-Abzeichen (messbar/unsicher/nicht messbar), „deine Frage“, `strittig: n`, Vergleiche mit `unreliable` ausgegraut; Handy nur Karten.
- i18n DE/EN (`ensemble.custom*`, `ensemble.reliability.*`, …); Farben nur Tokens; Touch ≥ 44 px.
- E2E: Mock-Felder in `e2e/support/mockApi.ts`; Flow „eigene Frage hinzufügen und Mehrfachlauf starten“.

## Verifikation
- `cd frontend && npx vite build` – ok.
- `./e2e/docker-test.sh --update-snapshots` – 143 passed, 13 skipped (bekannter `test.fail` a11y desktop Report).
- `./e2e/docker-test.sh` (ohne Update) – wieder grün; Ensemble-Snapshots geprüft (handy/iphone/desktop): Badges, „deine Frage“, strittig: 2, nicht messbar-Hinweis, unreliable-Vergleich grau.

## Snapshots aktualisiert
- `-ensemble-ens-test-{handy,iphone,tablet,desktop}-*.png`
