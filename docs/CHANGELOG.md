# Änderungen vom 13.–14. Oktober 2026

Kurzfassung für Nutzer. Technische Einzelheiten stehen im Git-Verlauf.

## Oberfläche & Bedienung

- Neue Startseite, gemeinsamer Kopf, Fußmenü (Start, Verlauf, Einstellungen), Deutsch und Englisch, wählbare Farb-Combos.
- Ein Klick bis zum Bericht: Der automatische Durchlauf erledigt alle Schritte und zeigt den Fortschritt.
- Handy und Tablet: feste Leiste für die wichtigste Aktion, Wissensgraph mit Zoom und Detailblatt, kein Seitwärtsscrollen, große Tippflächen auch auf kleinen Handys (320/360 px).
- Der Bericht liest sich wie ein Artikel: Inhaltsverzeichnis, Markdown-Download, Drucken/PDF.
- In langen Schritten zeigt die App ein Lebenszeichen („zuletzt aktualisiert vor X s“) und nach 2 Minuten ohne Änderung „dauert länger – läuft noch“; Fehler nennen den nächsten Schritt.
- Die Modellanzeige zeigt, ob lokal oder Cloud gearbeitet wird. Installierte Modelle lassen sich in den Einstellungen auswählen.
- Texte in Alltagssprache; aus „Vorhersage/Prognose“ wurde „Simulation/Szenario“.
- Löschen entfernt jetzt alles zu einem Lauf; abgebrochene Läufe werden aufgeräumt.

## Ehrlichkeit & Verlässlichkeit

- Neue Seite „Wie verlässlich ist MiroFish?“ (Deutsch und Englisch), in der App verlinkt.
- Wegtippbare Hinweise bei Einzellauf, Mehrfachlauf und Treffern aus dem Material.
- Jeder Bericht enthält eine Methodik mit Grenzen und einen Abgleich mit den Vorgaben aus dem Material.
- Einzelläufe nennen keine Wahrscheinlichkeiten mehr.
- Berichte kommen in der Sprache der Frage; der feste chinesische Tagesrhythmus ist entfernt.
- Seeds und ein Lauf-Manifest machen Läufe besser nachvollziehbar. Ein Lauf lässt sich trotzdem nicht exakt wiederholen.

## Mehrfachlauf & Statistik

- Eine Frage wird mehrfach simuliert; die Ergebnisseite zeigt Spannen statt Einzelwerten, mit Belegen aus der Simulation.
- Oben steht eine Zusammenfassung mit der Hauptfrage; weitere Ergebnisse und die Statistik sind aufklappbar („Details für Fachleute“).
- Vergleichsarme wählbar (z. B. ohne Agententyp, Nullmodell), eigene Ja/Nein-Fragen, Rundentakt 1/2/4 Stunden.
- Auswertung korrigiert: lange Läufe werden nicht mehr abgeschnitten, Unklares gilt als „unklassifiziert“ statt als stilles Nein, Neuauswertung ohne neue Simulation möglich.
- Zweites Modell prüft mit; ein Endurteil gibt es nur bei Einigkeit, strittige Fälle stehen separat.
- Bei den Vergleichen zählt ein Ergebnis als Hauptergebnis, alles andere als Erkundung.
- Fehler in der Ablation behoben (Abbruch im Feed-losen Arm, Lecks von Startbeiträgen).

## Validierung (V1–V5)

- V1/V2: Methodik, Seeds und Manifest, Mehrfachlauf mit Gegenproben.
- V3/V4: Zuverlässigkeit des Messinstruments, Vergleich mit Nullmodellen.
- V5: Vergleich mit realen kommunalen Fällen. Protokoll, anonymisierte Ausgangslagen und Prüfungen sind festgeschrieben, ein Trockenlauf ist erfolgt.
- **Der V5-Pilot ist noch nicht gelaufen.** Aussagen zur Treffsicherheit gibt es daher noch nicht.
- Stand und Grenzen: [VALIDIERUNG.md](VALIDIERUNG.md).

## Betrieb & Docker

- Docker-Schnellstart für Fremde: ein Port, Daten in `./data`, Ollama vom Rechner, läuft als normaler Nutzer.
- Port und Projektname per `.env` einstellbar; eine zweite Instanz ist möglich.
- Lokale Modelle brauchen keinen Schlüssel.
- `scripts/busy-check.sh` prüft vor Neustarts, ob noch etwas läuft.
- Automatische Tests auf Handy, Tablet und Desktop (Playwright, auch auf GitHub).

## Sicherheit

- Optionaler API-Schlüssel, zeitkonstant geprüft, im Browser als Cookie statt in der Adresszeile.
- Löschen prüft IDs streng (Schutz vor Pfad-Tricks).
- Ollama ist nicht im Netzwerk erreichbar; Zugriff nur über localhost.
- npm-Sicherheitsupdates, Kontrast und Beschriftungen für Screenreader verbessert.

## Dokumentation

- Anleitung für Gemeinderat, Verein und Bürgerinitiative: [ANLEITUNG.md](ANLEITUNG.md).
- Englische Fassungen: [GUIDE.md](GUIDE.md), [RELIABILITY.md](RELIABILITY.md).
- API, Roadmap und README-Screenshots auf den Stand vom 14.10.2026 gebracht.
