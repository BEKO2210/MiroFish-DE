# Bekannte Befunde (E2E)

Echte App-Probleme, die die Suite mit `test.fail()` markiert (Kommentar: „bekannter Fehler, siehe BEFUNDE.md“). Suite bleibt grün; wenn ein Fehler behoben ist, schlägt der erwartete Fail fehl und der Eintrag kann entfernt werden.

WebKit-Status bei diesem Lauf: siehe `webkit-status.txt` (Binary vorhanden, Host-Libs fehlen → nur Chromium).

## 1. Fußmenü verdeckt Bedienelemente (Handy)

| Test | Gerät | Route | Was passiert | Screenshot / Artefakt |
|------|-------|-------|--------------|------------------------|
| – | – | – | Keine offenen Befunde: Startseite, Durchlauf und alle Schritt-Seiten sind behoben (Daumen-Leiste, Safe-Area). | – |

Behoben mit `MobileStickyBar` und Safe-Area-Abstand (UX Teil A + B).

## 2. Barrierefreiheit (axe serious/critical)

| Test | Gerät | Route | Verstöße | Artefakt |
|------|-------|-------|----------|----------|
| `a11y.spec.ts` | desktop | `/report/report_6587bcd7e3fa` | `color-contrast` (u. a.) | `test-results/a11y-…-report-…` |

Hinweis: `/`, `/history`, `/settings` (Kontrast Marken-/Meta-Text, Labels/Selects, Datei-Input) sind behoben. Auf **handy** war `/report/...` bereits ohne serious/critical grün.

## 3. iPhone (WebKit): seitliche Scrollleiste

| Test | Gerät | Route | Was passiert |
|------|-------|-------|--------------|
| `smoke.spec.ts` – lädt sauber | iphone | `/interaction/report_6587bcd7e3fa` | `scrollWidth > innerWidth` – die Nachfragen-Seite scrollt in Safari seitlich (in Chromium nicht). Gefunden im Playwright-Container (e2e/docker-test.sh). |

## Nicht als App-Bug gewertet (Tests angepasst)

- **Verlauf Löschen / Zeile entfernt:** Zwei Historie-Einträge teilen sich denselben Titeltext; Assertion nutzt jetzt die konkrete Zeile statt `hasText(title)`.
- **Einstellungen Farbwähler-Selektor:** Nach Sprachwechsel auf English matchten Header-Icon und Einstellungs-`rowbtn` beide auf „Colours“ – Klick gezielt auf `main .rowbtn`.
