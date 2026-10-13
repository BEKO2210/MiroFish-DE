# Validierungsfälle: Übersicht

Fünf abgeschlossene kommunale Entscheidungen in Deutschland. Je Fall: neutrale `ausgangslage.md` (ohne Reaktionen),
`verlauf.md`, `ergebnisse.json` (Aussagen mit `eingetreten` wahr/falsch) und `quellen.md` (abgerufene Quellen mit
wörtlichen Belegstellen). Alle Quellen wurden am 14.10.2026 abgerufen und geprüft.

| Fall | Ort | Datum (Beschluss) | T0 | Primärergebnis (14 Tage nach T0) | Art | Quellen | Fragen | Anteil eingetreten |
|------|-----|-------------------|----|-----------------------------------|-----|---------|--------|--------------------|
| karlsfeld-hallenbad-2023 | Karlsfeld (Bayern) | 02.03.2023 | 02.03.2023 | Beschluss förmlich aufgehoben/geändert: Nein | Hallenbad-Schließung | 12 | 8 | 5/8 (62,5 %) |
| niederkassel-buecherei-2023 | Niederkassel (NRW) | 14.02.2023 | 14.02.2023 | wie oben: Nein | Bücherei-Schließung | 7 | 5 (4 scorebar, 1 `in_material`) | 3/4 (75 %) |
| unterschleissheim-wall-2022 | Unterschleißheim (Bayern) | 30.11.2022 (Ausschuss), 02.02.2023 (Stadtrat) | 30.11.2022 | wie oben: Nein | Baumfällung / Wallsanierung | 8 (Nr. 8 ohne Beleg) | 6 | 5/6 (83 %) |
| wanzleben-grundschule-2025 | Wanzleben-Börde (Sachsen-Anhalt) | 28.08.2025 | 28.08.2025 | wie oben: Nein | Grundschul-Schließung | 8 | 4 | 2/4 (50 %) |
| neuwied-parkgebuehren-2025 | Neuwied (Rheinland-Pfalz) | 13.11.2025 | 13.11.2025 | wie oben: Nein | Parkgebühren-Verdopplung | 8 | 6 (5 scorebar, 1 `in_material`) | 4/5 (80 %) |
| **Summe** | | | | 0/5 Ja | | 43 | 29 | 19/27 scorebar (70 %) |

T0 = Tag des Beschlusses; `ausgangslage.md` enthält nur Tatsachen aus Quellen mit Veröffentlichung ≤ T0 (Prüftabelle je Fall in
`quellen.md`). Genau eine Frage je Fall trägt `"primaer": true`; das Kodierbuch steht ebenfalls in `quellen.md`. Neuwied hat
5 scorebare belegte Fragen und gilt damit nicht als „schwacher Fall“.

## Grenzen

- **Medienverzerrung:** Quellen sind überwiegend Lokalpresse, Rundfunk und Pressemitteilungen. Große, laute Reaktionen
  (Proteste, Petitionen) werden berichtet, kleine Reaktionen (Gespräche, einzelne Beschwerden, stilles Ausweichen) selten.
  „Eingetreten = falsch“ bedeutet daher oft nur „nicht berichtet bzw. nur belegt, dass der Beschluss blieb“.
- **Fragenauswahl:** Aussagen ohne tragende Quelle wurden entfernt statt als „falsch“ gewertet. Das verzerrt den Anteil
  „eingetreten“ eher nach oben; reines Nichterwähnen gilt nie als Gegenbeleg.
- **Kleine Stichprobe:** Fünf Fälle, 29 Fragen; Anteile sind Größenordnungen, keine Genauigkeitsmaße. Die Fälle
  decken nur wenige Arten ab und sind nicht repräsentativ (u. a. nur Fälle mit Presseecho, meist Protest-Fälle).
- **Zeitfenster und Datierung:** Viele Ereignisse sind nicht taggenau datiert; Reaktionen vor dem Beschluss (z. B.
  Petitionen) zählen nicht. Einige Belege stammen erst von nach dem Fenster (z. B. Neuwied: 23.02.2026, 29.04.2026).
- **T0-Schnitt:** Beschlussinhalt und in der Sitzung genannte Gründe sind Ereignisse an T0, wurden aber erst nach T0 berichtet (dokumentierte Ausnahme). Das T0-Material enthält teils schon Kritik (Niederkassel: Förderverein am 10.02.2023); Quellen mit unklarem Datum (Niederkassel [1], Stadt-Pressemitteilung Neuwied Juni 2025) sind in `quellen.md` vermerkt.
- **Keine Varianz im Primärergebnis:** Alle fünf Primärergebnisse sind „Nein“; für Brier-Vergleiche braucht der Pilot Fälle mit positivem Primärergebnis.
- **Parteiische Quellen:** Pressemitteilungen von Stadt und Fraktionen sind Eigendarstellungen; Zitate sind ihre Aussagen,
  keine unabhängige Bestätigung.
- **Lesbarkeit:** Nicht jede Quelle war automatisch auswertbar (z. B. ein Bild-PDF in Wanzleben); solche Quellen tragen
  keine Belege.
- **Suchergebnisse:** Antworten von Websuchen wurden nicht als Beleg übernommen; sie enthielten teils falsche Details.
- **Einzelheiten:** Ortsnamen sind in `ausgangslage.md` zu Fiktivnamen anonymisiert, die Zuordnung steht in `verlauf.md`.
