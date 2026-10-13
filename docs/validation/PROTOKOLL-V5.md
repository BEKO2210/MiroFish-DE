# Vorregistrierung V5: Realitätsabgleich

Status: vor Beginn der Fallauswahl und vor Einsicht in die späteren Ausgänge festzuschreiben.

## Fragestellung und Stichprobenrahmen

Untersucht wird, ob der Schwarm reale kommunalpolitische Reaktionen innerhalb von 14 Tagen besser prognostiziert als ein einzelnes Modell mit demselben Dokument. Der Stichprobenrahmen wird vor der Outcome-Erhebung vollständig festgelegt, zum Beispiel als alle öffentlich dokumentierten Gebührenerhöhungen oder Bäderschließungen in Gemeinden ab 20.000 Einwohnerinnen und Einwohnern in einem abgeschlossenen Kalenderjahr. Ein- und Ausschlussregeln, Suchquellen und Ziehungsverfahren werden vorab datiert dokumentiert.

Der Pilot umfasst acht unabhängig gezogene Fälle. Er dient der Prüfung von Ablauf, Messbarkeit und grober Falsifikation, nicht einer belastbaren Kalibrierungsaussage. Die anschließende konfirmatorische Studie umfasst mindestens 25 Fälle. Fälle sind die statistisch unabhängigen Einheiten; Seeds sind Wiederholungen innerhalb eines Falls.

## Materialschnitt T0 und Kontamination

Für jeden Fall wird ein Zeitpunkt T0 definiert. `ausgangslage.md` enthält ausschließlich Material mit nachprüfbarer Veröffentlichung spätestens zu T0. Spätere Texte und der Ausgang stehen nur in `verlauf.md` und `ergebnisse.json` und werden der Simulation nicht gesendet. Ein Ergebnis, das bereits im T0-Material enthalten oder angekündigt ist (`in_material`), wird nicht gescored.

Vor jedem Lauf wird das konfigurierte Hauptmodell bei Temperatur 0 und ohne Werkzeuge kalt gefragt, ob es den Fall anhand von Ort, Jahr und Thema kennt; der Ausgang wird nicht genannt. Anfrage, Modell, Zeitpunkt und vollständige Antwort werden protokolliert. Bejaht das Modell die Kenntnis, erhält der Fall `contaminated: true`. Kontaminierte Fälle werden nicht mit der Hauptstichprobe vermischt, sondern in `GESAMT.json` und `GESAMT.md` getrennt ausgewiesen. Vorab kann stattdessen festgelegt werden, solche Fälle zu verwerfen oder Eigennamen durch dokumentierte Platzhalter zu ersetzen.

## Kodierbuch und Verblindung

Das Kodierbuch wird von einer Person vor dem ersten Simulationslauf erstellt. Es enthält genau ein binäres Primärergebnis, zum Beispiel „Innerhalb von 14 Tagen erfolgt eine förmliche institutionelle Reaktion“, mit Positiv- und Negativbeispielen, Zeitgrenze, Entscheidungskriterien und zulässigen Quellen. In `ergebnisse.json` trägt genau dieser Eintrag `"primaer": true`; weitere Fragen sind ausschließlich explorativ.

Zwei Personen kodieren unabhängig die reale Akte, ohne Simulationsausgaben oder Armzuordnung zu sehen. Danach wird Cohen's Kappa berechnet und Dissens adjudiziert. Dieselben Personen kodieren die Simulationsausgaben blind gegen Arm und reale Akte. Die Zuordnung von Fällen, Armen und Seeds wird erst nach Abschluss der Kodierung aufgedeckt. Bei Kappa unter 0,6 gilt das Ergebnis als nicht hinreichend messbar.

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

## Arme und Durchführung

Je Fall werden mit gepaarten Seeds zehn Läufe je Arm durchgeführt:

- `baseline` (S): Schwarm;
- `null_document` (D): Dokument und Frage;
- `null_personas` (P): zusätzlich dieselben Personas und Startbeiträge;
- `isolated`: isolierte Agenten als explorative Mechanismusprüfung.

Der Standardaufruf des Werkzeugs umfasst S, D und P. `isolated` wird über `--arms baseline,null_document,null_personas,isolated` ergänzt. Die Prognose eines Falls ist je Arm die Häufigkeit des Primärergebnisses über Seeds, nicht ein einzelner Seed. Seeds werden innerhalb eines Falls zwischen Armen gepaart.

## Zielgröße und Entscheidungsregel

Primäre Zielgröße ist der Brier-Score der Fallhäufigkeiten gegen die adjudizierte reale Kodierung. Berichtet werden der Brier-Score je Arm sowie `Skill(S,D) = 1 − BS_S / BS_D` und `Skill(P,D) = 1 − BS_P / BS_D`. Das 95-%-Intervall entsteht durch 10.000 Bootstrap-Ziehungen ganzer Fälle mit Zurücklegen. Weder Fragen noch Seeds werden als unabhängige Einheiten resampelt.

Zusätzlich wird die Kalibrierungssteigung aus einer logistischen Regression des Ereignisses auf den Logit der prognostizierten Häufigkeit berechnet. Unter acht auswertbaren Fällen lautet der feste Hinweis „Pilot, keine Kalibrierungsaussage“.

Die vorab registrierte Aussage gilt nur als bestanden, wenn gleichzeitig:

- das 95-%-Fall-Bootstrap-Intervall von `Skill(S,D)` vollständig über 0 liegt;
- die Kalibrierungssteigung von S im Intervall [0,5; 1,5] liegt;
- Kappa für das Primärergebnis mindestens 0,6 beträgt.

Fehlt eine erforderliche Größe, lautet das Urteil „nicht prüfbar“; ist mindestens eine prüfbare Bedingung verletzt, „nicht bestanden“. S gegen `isolated` und S gegen P sind sekundäre, explorative Kontraste.

## Falsifikationskriterien

Bereits der Pilot widerspricht der Nutzenbehauptung, wenn der Skill klar negativ ist, S von P praktisch nicht unterscheidbar ist und damit über Rollenzerlegung hinaus kein Schwarmbeitrag sichtbar wird, oder Kappa unter 0,6 liegt. Ein nicht bestandenes oder nicht prüfbares Vorab-Kriterium darf nicht als Bestätigung umgedeutet werden. Kontaminierte Fälle und nachträglich ergänzte Ergebnisse werden nur als Sensitivitätsanalyse berichtet.

## Rechenaufwand

Planwert für den Pilot: 8 Fälle × 4 Arme × 10 Seeds × etwa 15 Minuten = ungefähr 80 GPU-Stunden. Hinzu kommen Ontologie- und Profilvorbereitung, zwei verblindete Kodierungen, Adjudikation und Wiederholungen technisch fehlgeschlagener Läufe. Für mindestens 25 konfirmatorische Fälle sind bei gleichen Annahmen ungefähr 250 GPU-Stunden allein für die Läufe einzuplanen. Es wird kein echter Lauf automatisch gestartet.
