# Bekannte Befunde (E2E)

Echte App-Probleme, die die Suite mit `test.fail()` markiert (Kommentar: „bekannter Fehler, siehe BEFUNDE.md“). Suite bleibt grün; wenn ein Fehler behoben ist, schlägt der erwartete Fail fehl und der Eintrag kann entfernt werden.

WebKit-Status bei diesem Lauf: siehe `webkit-status.txt` (Binary vorhanden, Host-Libs fehlen → nur Chromium).

## 1. Fußmenü verdeckt Bedienelemente (Handy)

| Test | Gerät | Route | Was passiert | Screenshot / Artefakt |
|------|-------|-------|--------------|------------------------|
| `smoke.spec.ts` | handy | `/process/proj_6fde53d0e82a` | Button „Zur Umgebungseinrichtung“ liegt unter dem Fußmenü. | `test-results/smoke-Smoke--process-…-handy/` |
| `smoke.spec.ts` | handy | `/simulation/sim_2c3b36b2e33f` | Button „← Zurück zur Grapherstellung“ liegt unter dem Fußmenü. | `test-results/smoke-Smoke--simulation-…-handy/` |
| `smoke.spec.ts` | handy | `/interaction/report_6587bcd7e3fa` | Textarea am Seitenende liegt unter dem Fußmenü. | `test-results/smoke-Smoke--interaction-…-handy/` |

Ursache: Schrittseiten (`Process` / `Simulation` / `Interaction`) – Scope eines anderen Agents. Startseite und Durchlauf sind mit Safe-Area + `MobileStickyBar` behoben.

## 2. Barrierefreiheit (axe serious/critical)

| Test | Gerät | Route | Verstöße | Artefakt |
|------|-------|-------|----------|----------|
| `a11y.spec.ts` | tablet, desktop | `/report/report_6587bcd7e3fa` | `color-contrast` (u. a.) | `test-results/a11y-…-report-…` |

Hinweis: `/`, `/history`, `/settings` (Kontrast Marken-/Meta-Text, Labels/Selects, Datei-Input) sind behoben. Auf **handy** war `/report/...` bereits ohne serious/critical grün.

## Nicht als App-Bug gewertet (Tests angepasst)

- **Verlauf Löschen / Zeile entfernt:** Zwei Historie-Einträge teilen sich denselben Titeltext; Assertion nutzt jetzt die konkrete Zeile statt `hasText(title)`.
- **Einstellungen Farbwähler-Selektor:** Nach Sprachwechsel auf English matchten Header-Icon und Einstellungs-`rowbtn` beide auf „Colours“ – Klick gezielt auf `main .rowbtn`.
