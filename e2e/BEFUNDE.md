# Bekannte Befunde (E2E)

Echte App-Probleme, die die Suite mit `test.fail()` markiert (Kommentar: „bekannter Fehler, siehe BEFUNDE.md“). Suite bleibt grün; wenn ein Fehler behoben ist, schlägt der erwartete Fail fehl und der Eintrag kann entfernt werden.

WebKit-Status bei diesem Lauf: siehe `webkit-status.txt` (Binary vorhanden, Host-Libs fehlen → nur Chromium).

## 1. Fußmenü verdeckt Bedienelemente (Handy)

| Test | Gerät | Route | Was passiert | Screenshot / Artefakt |
|------|-------|-------|--------------|------------------------|
| `smoke.spec.ts` – lädt sauber | handy | `/` | Nach Scroll nach unten liegt der Footer-Link „GitHub“ unter der Oberkante von `.mobile-nav` (bottom ≈ 880, navTop ≈ 856). | `test-results/smoke-Smoke--lädt-sauber-handy/` |
| `smoke.spec.ts` | handy | `/run/run_f68e3af5662f` | Aktionslink „Alles exportieren (ZIP)“ liegt unter dem Fußmenü. | `test-results/smoke-Smoke--run-run-f68e3af5662f-lädt-sauber-handy/` |
| `smoke.spec.ts` | handy | `/process/proj_6fde53d0e82a` | Button „Zur Umgebungseinrichtung“ liegt unter dem Fußmenü. | `test-results/smoke-Smoke--process-…-handy/` |
| `smoke.spec.ts` | handy | `/simulation/sim_2c3b36b2e33f` | Button „← Zurück zur Grapherstellung“ liegt unter dem Fußmenü. | `test-results/smoke-Smoke--simulation-…-handy/` |
| `smoke.spec.ts` | handy | `/interaction/report_6587bcd7e3fa` | Textarea am Seitenende liegt unter dem Fußmenü. | `test-results/smoke-Smoke--interaction-…-handy/` |

Ursache: `body { padding-bottom: … }` reicht nicht für fixe Aktionsleisten / Footer-Inhalte auf Schrittseiten; `.mobile-nav` ist `position: fixed`.

## 2. Barrierefreiheit (axe serious/critical)

| Test | Gerät | Route | Verstöße | Artefakt |
|------|-------|-------|----------|----------|
| `a11y.spec.ts` | handy, tablet, desktop | `/` | `color-contrast` (z. B. Meta-Text `#64748b` auf `#fff7ed`, Ratio 4.48 &lt; 4.5), `label` (Datei-Input ohne zugängliches Label) | `test-results/a11y-…-handy/` usw. |
| `a11y.spec.ts` | handy, tablet, desktop | `/history` | `color-contrast` | `test-results/a11y-…-history-…` |
| `a11y.spec.ts` | handy, tablet, desktop | `/settings` | `color-contrast`, `select-name` (Selects ohne accessible name) | `test-results/a11y-…-settings-…` |
| `a11y.spec.ts` | tablet, desktop | `/report/report_6587bcd7e3fa` | `color-contrast` (u. a.) | `test-results/a11y-…-report-…` |

Hinweis: Auf **handy** ist `/report/...` derzeit ohne serious/critical grün (dort ist `.mobile-nav` ausgeblendet; andere Kontrastflächen greifen offenbar weniger).

## Nicht als App-Bug gewertet (Tests angepasst)

- **Verlauf Löschen / Zeile entfernt:** Zwei Historie-Einträge teilen sich denselben Titeltext; Assertion nutzt jetzt die konkrete Zeile statt `hasText(title)`.
- **Einstellungen Farbwähler-Selektor:** Nach Sprachwechsel auf English matchten Header-Icon und Einstellungs-`rowbtn` beide auf „Colours“ – Klick gezielt auf `main .rowbtn`.
