# Vorregistrierung V5: Realitätsabgleich (Pilot zur Falsifikation)

Status: Vorregistrierung des Piloten, festgeschrieben vor dem ersten Simulationslauf (14.10.2026). Bis zu diesem Stand wurde kein Lauf für V5 ausgeführt. Spätere Änderungen werden datiert nachgetragen und nicht rückwirkend eingearbeitet.

## Einordnung des Piloten

- **Pilot zur Falsifikation.** Der Pilot prüft Ablauf, Messbarkeit und ob die Nutzenbehauptung grob widerlegt wird. Er liefert **keine Kalibrierungsaussage**; belastbare Kalibrierung setzt mindestens 25 Fälle voraus (konfirmatorische Studie). Fälle sind die statistisch unabhängigen Einheiten; Seeds sind Wiederholungen innerhalb eines Falls.
- **Die Autoren kannten die Ausgänge bei der Fallauswahl.** Die acht Fälle wurden nicht nach einem vorab festgelegten Ziehungsverfahren aus einem Stichprobenrahmen gezogen, sondern bewusst ausgewählt, und die Ausgänge lagen bei der Auswahl und der Quellenerhebung vor. Das Ergebnis kann daher weder als repräsentativ noch als blind erhoben gelten; die Vorregistrierung betrifft nur Analyse, Kodierregeln und Entscheidungsregel, nicht die Fallauswahl.
- Es gibt nur Fälle mit auffindbarem Presseecho (Medienverzerrung); die Fälle decken wenige Arten ab (Gebühren, Schließungen, Baumfällungen).

## Fragestellung

Untersucht wird, ob der Schwarm (Arm S) reale kommunalpolitische Reaktionen innerhalb von 14 Tagen besser prognostiziert als ein einzelnes Modell mit demselben Dokument (Arm D) und ob ein etwaiger Vorteil über die bloße Rollenzerlegung mit denselben Personas (Arm P) hinausgeht.

## Fälle (8)

Je Fall ein Ordner unter `docs/validation/faelle/` mit `ausgangslage.md` (T0-Material, anonymisiert), `verlauf.md`, `ergebnisse.json` und `quellen.md` (Quellen, T0-Prüfung). T0 ist der Tag des Beschlusses (Unterschleißheim: Tag der Ausschussentscheidung).

| # | Fallordner | T0 | Primärergebnis (adjudiziert) | Quellenlücke |
|---|---|---|---|---|
| 1 | `freiburg-bewohnerparken-2021` | 14.12.2021 | Ja (CDU-Fraktion, 17.12.2021) | nein |
| 2 | `karlsfeld-hallenbad-2023` | 02.03.2023 | Ja (TSV-Schwimmabteilung, 03.03.2023) | nein |
| 3 | `kehl-tram-baumfaellungen-2017` | 22.02.2017 | Nein (dokumentierte Negativsuche) | **ja** |
| 4 | `kuppenheim-cuppamare-2024` | 06.05.2024 | Ja (DLRG, 07.05.2024) | nein |
| 5 | `neuwied-parkgebuehren-2025` | 13.11.2025 | Ja (AfD-Fraktion, 16.11.2025) | nein |
| 6 | `niederkassel-buecherei-2023` | 14.02.2023 | Nein (frühester Beleg 13.03.2023) | **ja** |
| 7 | `unterschleissheim-wall-2022` | 30.11.2022 | Ja (BUND Naturschutz, 06.12.2022) | nein |
| 8 | `wanzleben-grundschule-2025` | 28.08.2025 | Nein (kein datierter Beleg im Fenster) | **ja** |

Die Primärergebnisse wurden mit den Quellen erhoben, bevor diese Vorregistrierung festgeschrieben wurde. Sie sind in dieser Tabelle offengelegt, weil sie nicht verblindet erhoben wurden (siehe Einordnung).

## Primärsatz (einheitlich für alle 8 Fälle)

„Innerhalb von 14 Tagen veröffentlicht mindestens ein organisierter Akteur (Ratsfraktion, Verein, Verband oder Bürgerinitiative) eine ablehnende Stellungnahme gegen die Maßnahme.“

Genau dieser Satz ist in jeder `ergebnisse.json` die einzige Frage mit `"primaer": true`. Weitere Fragen sind ausschließlich explorativ. Jede Frage trägt ein Feld `"polarity"`: `"absence"`, wenn die Aussage das Ausbleiben oder Fortbestehen eines Zustands meint (z. B. „bleiben bestehen“, „wird nicht ausgeweitet“), sonst `"presence"`; `eingetreten` gibt in beiden Fällen an, ob die Aussage zutrifft. Kodierhinweise stehen nicht im Fragetext, sondern in einem eigenen Feld `kodierhinweis`, das den Simulationsarmen nicht gesendet wird.

## Materialschnitt T0 und Kontamination

`ausgangslage.md` enthält ausschließlich Material mit nachprüfbarer Veröffentlichung spätestens zu T0; die Ausnahme „Ereignis an T0, erst danach berichtet“ (Beschlussinhalt und in der Sitzung genannte Gründe) ist je Fall in der T0-Prüfung in `quellen.md` dokumentiert. Jede Zeile von `ausgangslage.md` ist dort einer Quelle mit Datum zugeordnet; Tatsachen ohne Quelle ≤ T0 wurden entfernt. Spätere Texte und der Ausgang stehen nur in `verlauf.md`, `ergebnisse.json` und `quellen.md` und werden der Simulation nicht gesendet. Ein Ergebnis, das bereits im T0-Material enthalten oder angekündigt ist (`in_material`), wird nicht gescored.

Anonymisierung: In `ausgangslage.md` sind Eigennamen, Ortsnamen und einmalige Zahlen entfernt oder gerundet (Größenordnungen statt exakter Werte, „Nachbarland“ statt Ortsnamen), damit das Modell den Fall nicht über Fingerabdrücke erinnert. Die Originalwerte stehen in `quellen.md`. Anonymisierung ersetzt die Kontaminationsprüfung nicht.

Vor jedem Lauf wird das konfigurierte Hauptmodell bei Temperatur 0 und ohne Werkzeuge kalt gefragt, ob es den Fall anhand von Ort, Jahr und Thema kennt; der Ausgang wird nicht genannt. Anfrage, Modell, Zeitpunkt und vollständige Antwort werden protokolliert. Bejaht das Modell die Kenntnis, erhält der Fall `contaminated: true`. Kontaminierte Fälle werden nicht mit der Hauptstichprobe vermischt, sondern in `GESAMT.json` und `GESAMT.md` getrennt ausgewiesen.

Externe Kaltprüfung vor dem Start (14.10.2026, Gemini 3.8 Flash, ohne Websuche, nur Bogentext): Freiburg wurde auch nach
zweiter Anonymisierung erkannt (95 %, Ausgang bekannt), weil Konfliktstruktur und Gebührenmodell selbst der
Fingerabdruck sind. Freiburg gilt deshalb vorab als kontaminiert und zählt nicht zur Primäranalyse. Karlsfeld wurde nach
der zweiten Anonymisierung nicht mehr erkannt. Die Primäranalyse umfasst damit 7 Fälle (4 Ja, 3 Nein).

## Kodierbuch, Zweitkodierung und Verblindung

Die Erstkodierung der realen Akte erfolgte durch die Autoren, die die Ausgänge kannten. Das Kodierbuch (unten) wurde vor dem ersten Simulationslauf festgeschrieben.

**Zweitkodierung:** Sie liegt unter `docs/validation/zweitkodierung/` (je Fall `t0.txt`, `quellen-urls.txt`, `kodierung.json`, Übersicht in `uebersicht.md`). Zweitkodierer ist ein **KI-System (GitHub Copilot)**, das blind gegen die Erstkodierung nur T0, die Primärfrage und die Quellenliste erhielt. Ergebnis: Übereinstimmung in 8 von 8 Fällen, Cohen's Kappa 1,0. **Es gab keine zweite menschliche Person.** Der Wert belegt die Reproduzierbarkeit der Kodierung bei vorgegebenen Quellen, nicht eine menschliche Interrater-Reliabilität; die Quellenliste stammt von der Erstkodierung, und die Nein-Fälle (Kehl, Niederkassel, Wanzleben) bleiben Quellenlücken. Eine zweite menschliche Kodierung bleibt für die konfirmatorische Studie erforderlich.

Die Simulationsausgaben werden blind gegen Arm und reale Akte kodiert; die Zuordnung von Fällen, Armen und Seeds wird erst nach Abschluss der Kodierung aufgedeckt. Bei Kappa unter 0,6 gilt das Ergebnis als nicht hinreichend messbar.

Kodierbuch-Vorlage:

| Feld | Vorab festzulegender Inhalt |
|---|---|
| Ergebnis-ID | stabile Kennung |
| Primär | genau einmal „ja“ |
| Ergebnisfrage | binäre, beobachtbare Aussage |
| Zeitfenster | T0 bis T0 + 14 Tage |
| Ja-Kriterium | notwendige und hinreichende Belege |
| Nein-Kriterium | vollständige Suche ohne Ja-Beleg |
| Ausschluss | `in_material`, fehlende Akte, unklare Zeit |
| Quellen | zulässige Quellentypen |
| Beispiele | mindestens ein Ja- und ein Nein-Beispiel |

### Kodierbuch-Eintrag Primärergebnis (gilt für alle 8 Pilotfälle)

| Feld | Inhalt |
|---|---|
| Ergebnis-ID | `primaer` |
| Primär | ja (genau einmal je Fall; in `ergebnisse.json` als einzige Frage `"primaer": true`) |
| Ergebnisfrage | Innerhalb von 14 Tagen veröffentlicht mindestens ein organisierter Akteur (Ratsfraktion, Verein, Verband oder Bürgerinitiative) eine ablehnende Stellungnahme gegen die Maßnahme. |
| Zeitgrenze | T0 (Tag des Beschlusses) bis T0 + 14 Tage, beide Tage eingeschlossen; maßgeblich ist das Veröffentlichungsdatum der Stellungnahme, nicht das Abrufdatum |
| Ja-Kriterium | Mindestens eine datierte Veröffentlichung im Fenster (Pressemitteilung, Website oder Amtsblatt-Beitrag des Akteurs, offener Brief oder wörtliches Zitat eines benannten Vertreters in einem Pressebericht), die die Maßnahme ausdrücklich ablehnt oder scharf kritisiert. Mit wörtlicher Belegstelle und Datum in `quellen.md` |
| Nein-Kriterium | Dokumentierte Suche (abgerufene Quellen und Suchläufe in `quellen.md`) ohne datierten Beleg im Fenster. Quellenlücke bleibt als Einschränkung vermerkt |
| Zulässige Quellen | Eigene Veröffentlichungen der Akteure (auch Eigendarstellung), Lokalpresse, Rundfunk, Amtsblatt und Fraktionsbeiträge, Pressemitteilungen von Stadt und Fraktionen. Ergebnisse von Websuchen allein zählen nicht als Beleg |
| Nicht zulässig | Äußerungen Einzelner ohne Akteurszugehörigkeit (z. B. einzelne Eltern oder Bürger), Reaktionen vor T0, undatierte Belege, bloße Besorgnis ohne Ablehnung der Maßnahme, Debattenbeiträge in der Beschlusssitzung ohne eigene Veröffentlichung |
| Ausschluss | `in_material`, fehlende Akte, unklare Zeit |
| Positivbeispiele | Karlsfeld: Leiter der TSV-Schwimmabteilung am 03.03.2023, „ein Schlag ins Gesicht“. Neuwied: AfD-Fraktion, Pressemitteilung vom 16.11.2025. Unterschleißheim: Offener Brief BUND Naturschutz vom 06.12.2022 |
| Negativbeispiele | Niederkassel: Stellungnahmen des Fördervereins erst am 13.03.2023 (Tag 27) bzw. vor T0. Wanzleben: Bürgerinitiative nur undatiert belegt, Kommentar erst am Tag 21; Kehl: dokumentierte Negativsuche |

Die frühere Primärfrage „Beschluss binnen 14 Tagen aufgehoben oder geändert“ war in den fünf zuerst erfassten Fällen (Karlsfeld, Neuwied, Niederkassel, Unterschleißheim, Wanzleben) durchgehend „Nein“ und taugt ohne Streuung nicht als Messgröße; sie bleibt als explorative Frage `beschluss_aufgehoben` (ohne `primaer`) erhalten.

**Basisrate:** Das Primärergebnis ist in 5 von 8 Fällen „Ja“ (62,5 %; Freiburg, Karlsfeld, Kuppenheim, Neuwied, Unterschleißheim). Ein Skill-Vergleich muss diese Basisrate schlagen (Brier-Skill gegenüber der konstanten Vorhersage 0,625). Bei nur 8 Fällen ist die Basisrate extrem ungenau (Wilson-95-%-Intervall etwa 31–86 %). Die drei „Nein“-Kodierungen (Kehl, Niederkassel, Wanzleben) beruhen auf Quellenlücken, nicht auf belegter Abwesenheit, und können zu konservativ sein; Medienverzerrung begünstigt laute Reaktionen. In der Primäranalyse ohne Freiburg: 4 von 7 „Ja“ (57 %).

## Arme

Primär ausgewertet werden drei Arme:

- `baseline` (S): Schwarm;
- `null_document` (D): einzelnes Modell mit Dokument und Frage;
- `null_personas` (P): einzelnes Modell zusätzlich mit denselben Personas und Startbeiträgen.

`isolated` (isolierte Agenten) und `blind_feed` (voller Aktionsraum, leerer Feed) sind **ausschließlich explorativ**. Ein Unterschied zu S darf **nicht als Vernetzungseffekt gelesen werden**, weil sich die Arme in mehr als einem Merkmal unterscheiden (z. B. Aktionsraum, Feed, Interaktion). Sie gehen weder in die Entscheidungsregel noch in die Falsifikationskriterien ein.

Der Standardaufruf des Werkzeugs umfasst S, D und P; explorative Arme werden über `--arms` ergänzt. Die Prognose eines Falls ist je Arm die Häufigkeit des Primärergebnisses über Seeds, nicht ein einzelner Seed. Seeds werden innerhalb eines Falls zwischen Armen gepaart.

## Rahmen

Rundentakt und Seedzahl: siehe Abschnitt Rahmen, wird vor Start festgelegt. Der GPU-Rahmen (Hardware, Modell, Laufzeit je Lauf, Gesamtaufwand) ist offen und wird datiert nachgetragen, bevor der erste Lauf startet. Es wird kein echter Lauf automatisch gestartet.

## Auswertung

**Primär:** 7 Fälle (alle außer dem vorab als kontaminiert eingestuften Freiburg).

**Vorab fixierte Sensitivitätsanalyse:** nur die 4 nicht kontaminierten Fälle ohne Quellenlücke (Karlsfeld, Kuppenheim, Neuwied, Unterschleißheim). Ausgeschlossen werden Kehl, Niederkassel und Wanzleben, deren „Nein“ auf Quellenlücken beruht. Weitere Sensitivitätsanalysen (z. B. ohne kontaminierte Fälle) werden getrennt ausgewiesen; nachträgliche Analysen gelten als explorativ.

Primäre Zielgröße ist der Brier-Score der Fallhäufigkeiten gegen die adjudizierte reale Kodierung. Berichtet werden der Brier-Score je Arm sowie `Skill(S,D) = 1 − BS_S / BS_D` und `Skill(P,D) = 1 − BS_P / BS_D`. Das 95-%-Intervall entsteht durch 10.000 Bootstrap-Ziehungen ganzer Fälle mit Zurücklegen. Weder Fragen noch Seeds werden als unabhängige Einheiten resampelt.

Zusätzlich wird die Kalibrierungssteigung aus einer logistischen Regression des Ereignisses auf den Logit der prognostizierten Häufigkeit berechnet. Unter 25 auswertbaren Fällen lautet der feste Hinweis „Pilot, keine Kalibrierungsaussage“.

## Entscheidungsregel

Die vorab registrierte Aussage gilt nur als bestanden, wenn gleichzeitig:

- das 95-%-Fall-Bootstrap-Intervall von `Skill(S,D)` vollständig über 0 liegt;
- die Kalibrierungssteigung von S im Intervall [0,5; 1,5] liegt;
- Kappa für das Primärergebnis mindestens 0,6 beträgt (die KI-Zweitkodierung liefert 1,0, ersetzt aber keine menschliche Zweitkodierung).

Wegen des Pilotcharakters kann auch ein „bestanden“ keine Kalibrierung belegen. Fehlt eine erforderliche Größe, lautet das Urteil „nicht prüfbar“; ist mindestens eine prüfbare Bedingung verletzt, „nicht bestanden“. S gegen P, S gegen `isolated` und S gegen `blind_feed` sind sekundäre, explorative Kontraste.

## Falsifikationskriterien

Bereits der Pilot widerspricht der Nutzenbehauptung, wenn der Skill klar negativ ist, S von P praktisch nicht unterscheidbar ist und damit über Rollenzerlegung hinaus kein Schwarmbeitrag sichtbar wird, oder Kappa unter 0,6 liegt. Ein nicht bestandenes oder nicht prüfbares Vorab-Kriterium darf nicht als Bestätigung umgedeutet werden. Kontaminierte Fälle und nachträglich ergänzte Ergebnisse werden nur als Sensitivitätsanalyse berichtet. Die Ergebnisse der Sensitivitätsanalysen dürfen das Urteil der Primäranalyse über 7 Fälle nicht ersetzen.

## Rechenaufwand

Offen; siehe Abschnitt Rahmen. Hinzu kommen Ontologie- und Profilvorbereitung, die blinde Kodierung der Simulationsausgaben, Adjudikation und Wiederholungen technisch fehlgeschlagener Läufe. Für mindestens 25 konfirmatorische Fälle ist der Aufwand entsprechend hochzurechnen.
