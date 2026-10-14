# Validierungsfälle: Übersicht

Acht abgeschlossene kommunale Entscheidungen in Deutschland. Je Fall: neutrale `ausgangslage.md` (ohne Reaktionen),
`verlauf.md`, `ergebnisse.json` (Aussagen mit `eingetreten` wahr/falsch) und `quellen.md` (abgerufene Quellen mit
wörtlichen Belegstellen). Alle Quellen wurden am 14.10.2026 abgerufen und geprüft.

Einheitliches Primärergebnis für alle Fälle: „Innerhalb von 14 Tagen veröffentlicht mindestens ein organisierter Akteur
(Ratsfraktion, Verein, Verband oder Bürgerinitiative) eine ablehnende Stellungnahme gegen die Maßnahme.“ (Kodierbuch in
`../PROTOKOLL-V5.md`, Belegstellen im Abschnitt „Primärergebnis“ je `quellen.md`.) Die frühere Primärfrage (Beschluss binnen
14 Tagen aufgehoben/geändert) war in den ersten fünf Fällen überall „Nein“ und bleibt als explorative Frage
`beschluss_aufgehoben` erhalten.

| Fall | Ort | Datum (Beschluss) | T0 | Primärergebnis (Ja/Nein) | Art | Quellen | Fragen | Anteil eingetreten |
|------|-----|-------------------|----|--------------------------|-----|---------|--------|--------------------|
| freiburg-bewohnerparken-2021 | Freiburg (Baden-Württemberg) | 14.12.2021 | 14.12.2021 | **Ja** (CDU-Fraktion, 17.12.2021) | Bewohnerparkgebühren | 7 | 7 | 4/7 (57 %) |
| kehl-tram-baumfaellungen-2017 | Kehl (Baden-Württemberg) | 22.02.2017 | 22.02.2017 | **Nein** (Negativsuche) | Baumfällung / Tram | 7 | 7 | 4/7 (57 %) |
| kuppenheim-cuppamare-2024 | Kuppenheim (Baden-Württemberg) | 06.05.2024 | 06.05.2024 | **Ja** (DLRG, 07.05.2024) | Hallenbad-Schließung | 7 | 7 | 4/7 (57 %) |
| karlsfeld-hallenbad-2023 | Karlsfeld (Bayern) | 02.03.2023 | 02.03.2023 | **Ja** (TSV-Schwimmabteilung, 03.03.2023) | Hallenbad-Schließung | 12 | 9 | 6/9 (67 %) |
| niederkassel-buecherei-2023 | Niederkassel (NRW) | 14.02.2023 | 14.02.2023 | **Nein** (frühester Beleg 13.03.2023) | Bücherei-Schließung | 7 | 6 (5 scorebar, 1 `in_material`) | 3/5 (60 %) |
| unterschleissheim-wall-2022 | Unterschleißheim (Bayern) | 30.11.2022 (Ausschuss), 02.02.2023 (Stadtrat) | 30.11.2022 | **Ja** (BUND Naturschutz, 06.12.2022) | Baumfällung / Wallsanierung | 8 (Nr. 8 ohne Beleg) | 7 | 6/7 (86 %) |
| wanzleben-grundschule-2025 | Wanzleben-Börde (Sachsen-Anhalt) | 28.08.2025 | 28.08.2025 | **Nein** (kein datierter Beleg im Fenster) | Grundschul-Schließung | 8 | 5 | 2/5 (40 %) |
| neuwied-parkgebuehren-2025 | Neuwied (Rheinland-Pfalz) | 13.11.2025 | 13.11.2025 | **Ja** (AfD-Fraktion, 16.11.2025) | Parkgebühren-Verdopplung | 8 | 7 (6 scorebar, 1 `in_material`) | 5/6 (83 %) |
| **Summe** | | | | **Katalog 5/8 Ja; Primär 4/7 Ja** | | 64 | 55 | 34/53 scorebar (64 %) |

T0 = Tag des Beschlusses; `ausgangslage.md` enthält nur Tatsachen aus Quellen mit Veröffentlichung ≤ T0 (Prüftabelle „T0-Prüfung“
je Fall in `quellen.md`, jetzt für alle acht Fälle; Ausnahme: Beschluss und in der Sitzung genannte Gründe als Ereignis an T0).
Genau eine Frage je Fall trägt `"primaer": true`; jede Frage trägt `"polarity"` (`presence` oder `absence`, Ausbleiben bzw.
Fortbestehen). Kodierhinweise stehen nicht im Fragetext. Neuwied hat 6 scorebare belegte Fragen und gilt damit nicht als
„schwacher Fall“.

**Felder in `ergebnisse.json`:** `kontaminiert` (Objekt mit `quelle` und `datum`) und `quellenluecke` (boolesch) stehen an der
Frage, nicht am Ordnernamen. `kontaminiert` trägt nur Freiburg, mit Quelle und Datum der externen Kaltprüfung vom 2026-10-14.
`quellenluecke: true` tragen Kehl, Niederkassel und Wanzleben. `kaltfrage_ort` (Text, echter Ort und Jahr, zum Beispiel
„Kehl 2017“) steht je Fall an der Primärfrage. Die Echtfall-Kaltfrage nutzt nur dieses Feld oder `--ort`; der Ordnername
geht nicht an das Modell. Die Bogen-Frage erhält nur den Text von `ausgangslage.md`. `backend/scripts/validate_case.py`
liest die Felder aus den Frageobjekten.

**Basisrate:** Im Katalog aller acht Akten ist das Primärergebnis 5-mal „Ja“ (62,5 %; Wilson-95-%-Intervall etwa 31–86 %).
Freiburg ist vorab kontaminiert und zählt nicht zur Primäranalyse. Primär bleiben 7 Fälle, davon 4 „Ja“ (Karlsfeld, Kuppenheim,
Neuwied, Unterschleißheim) und 3 „Nein“ (57 %). Mit 7 Fällen ist die Basisrate nur grob bestimmt.

Vorvereinbarte Auswertung (Protokoll und `backend/scripts/validate_case.py`): **Primär** die 7 nicht kontaminierten Fälle.
**Sensitivität** die 4 nicht kontaminierten Fälle ohne Quellenlücke (Karlsfeld, Kuppenheim, Neuwied, Unterschleißheim). Kehl,
Niederkassel und Wanzleben bleiben über `quellenluecke` in der Primäranalyse und fallen aus der Sensitivität. Berichtet wird
der Brier-Score je Arm sowie `Skill(S,D) = 1 − BS_S / BS_D` und `Skill(P,D) = 1 − BS_P / BS_D`. Das 95-%-Intervall entsteht
durch 10.000 Bootstrap-Ziehungen ganzer Fälle. Arme: S (`baseline`), D (`null_document`), P (`null_personas`); `isolated` und
`blind_feed` nur explorativ, nicht als Vernetzungseffekt lesbar.

## Grenzen

- **Medienverzerrung:** Quellen sind überwiegend Lokalpresse, Rundfunk und Pressemitteilungen. Große, laute Reaktionen
  (Proteste, Petitionen) werden berichtet, kleine Reaktionen (Gespräche, einzelne Beschwerden, stilles Ausweichen) selten.
  „Eingetreten = falsch“ bedeutet daher oft nur „nicht berichtet bzw. nur belegt, dass der Beschluss blieb“.
- **Fragenauswahl:** Aussagen ohne tragende Quelle wurden entfernt statt als „falsch“ gewertet. Das verzerrt den Anteil
  „eingetreten“ eher nach oben; reines Nichterwähnen gilt nie als Gegenbeleg.
- **Kleine Stichprobe:** Acht Akten, davon sieben in der Primäranalyse, 55 Fragen. Anteile sind Größenordnungen, keine
  Genauigkeitsmaße. Die Fälle decken nur wenige Arten ab und sind nicht repräsentativ (u. a. nur Fälle mit Presseecho,
  meist Protest-Fälle).
- **Zeitfenster und Datierung:** Viele Ereignisse sind nicht taggenau datiert; Reaktionen vor dem Beschluss (z. B.
  Petitionen) zählen nicht. Einige Belege stammen erst von nach dem Fenster (z. B. Neuwied: 23.02.2026, 29.04.2026).
- **T0-Schnitt:** Beschlussinhalt und in der Sitzung genannte Gründe sind Ereignisse an T0, wurden aber erst nach T0 berichtet (dokumentierte Ausnahme). Das T0-Material enthält teils schon Kritik (Niederkassel: Förderverein am 10.02.2023); Quellen mit unklarem Datum (Niederkassel [1], Stadt-Pressemitteilung Neuwied Juni 2025) sind in `quellen.md` vermerkt.
- **Wenig Varianz im Primärergebnis:** Katalog 5/8 „Ja“, Primäranalyse ohne das vorab kontaminierte Freiburg 4/7 „Ja“.
  Die drei „Nein“ (Kehl, Niederkassel, Wanzleben) beruhen auf Quellenlücken (`quellenluecke`), nicht auf belegter
  Abwesenheit. Sie bleiben in der Primäranalyse und sind aus der Sensitivität ausgeschlossen.
- **Parteiische Quellen:** Pressemitteilungen von Stadt und Fraktionen sind Eigendarstellungen; Zitate sind ihre Aussagen,
  keine unabhängige Bestätigung.
- **Lesbarkeit:** Nicht jede Quelle war automatisch auswertbar (z. B. ein Bild-PDF in Wanzleben); solche Quellen tragen
  keine Belege.
- **Suchergebnisse:** Antworten von Websuchen wurden nicht als Beleg übernommen; sie enthielten teils falsche Details.
- **Anonymisierung:** `ausgangslage.md` enthält keine Eigennamen und keine einmaligen Fingerabdrücke (exakte Zahlen, Ortsnamen,
  Stimmverhältnisse); Zahlen sind auf Größenordnungen gerundet, Ortsnamen durch Fiktivnamen oder neutrale Umschreibungen
  ersetzt. Die Originalwerte und die Zuordnung stehen in `quellen.md` bzw. `verlauf.md`. Anonymisierung ersetzt die
  Kontaminationsprüfung nicht.
- **Fallauswahl:** Die Autoren kannten die Ausgänge bei der Fallauswahl. Der Satz steht auch in `../PROTOKOLL-V5.md`;
  der Pilot dient der Falsifikation, keine Kalibrierungsaussage unter 25 Fällen.
- **Zweitkodierung:** `../zweitkodierung/` (KI-Zweitkodierer GitHub Copilot, blind; 8/8 Übereinstimmung, Kappa 1,0). Es gab
  keine zweite menschliche Person.
