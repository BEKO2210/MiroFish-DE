# Vorregistrierung V5: Realitätsabgleich (Pilot zur Falsifikation)

Status: Vorregistrierung des Piloten, festgeschrieben vor dem ersten Simulationslauf (14.10.2026). Bis zu diesem Stand wurde kein Lauf für V5 ausgeführt. Spätere Änderungen werden datiert nachgetragen und nicht rückwirkend eingearbeitet.

**Nachtrag 14.10.2026 (Entscheidungen des Orchestrators nach der Freigabeprüfung, vor jedem Lauf):** Die Abschnitte Kaltfrage, Kodierbuch/Zweitbewertung, Arme, Rahmen, Entscheidungsregel und Betrieb sind in diesem Stand überarbeitet (gerichtete Regel, feste Fallmenge, ein Lauf je Fall, gleiches Modell für alle Textarme, Doppelklassifikation ohne Fallback, Probelauf, Freitext-Kaltabruf, Wegfall von `blind_feed`, Betriebsteil). Maßgeblich ist dieser Stand; er wurde vor dem ersten Simulationslauf festgeschrieben. Die nach dem nicht gewerteten Probelauf vorgenommenen technischen Präzisierungen sind im datierten Nachtrag zur Klassifikation dokumentiert.

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

Vor jedem Lauf wird eine **Kaltprüfung als Freitext-Abruf** gegen versteckte Fakten ausgeführt (Entscheidung 14.10.2026; eine Ja/Nein-Selbstauskunft allein genügt nicht, weil sie bei kleinen Modellen schlecht kalibriert ist und ein „Nein“ keine Entwarnung bedeutet). Beide Modelle werden bei Temperatur 0 und ohne Werkzeuge gefragt: das Agentenmodell (`gemma4:e4b-it-qat-16k`) und das Hauptmodell (`gemma4:12b-it-qat-16k`). Je Modell zwei Fragen: (1) Echtfall-Abruf mit `kaltfrage_ort` aus `ergebnisse.json` (echter Ort und Jahr) und dem Thema der Maßnahme: „Was geschah nach diesem Beschluss, welche Akteure äußerten sich, an welchen Daten?“; (2) Bogen-Abruf nur mit dem Text von `ausgangslage.md` und derselben Freitextfrage. Der Ausgang wird nicht genannt, der Ordnername geht nicht an das Modell. Vor dem Senden wird jeder Prompt gegen die starken versteckten Begriffe aus `verlauf.md`, `quellen.md` und `ergebnisse.json` geprüft (Ausgangslage sowie Ort und Jahr der Kaltfrage sind ausgenommen); bei einem Treffer bricht der Lauf mit einer Meldung ab, bevor etwas gesendet wird. Die Freitextantwort wird gegen die versteckten Fakten (Ausgang, Akteure, Daten aus `ergebnisse.json` und `quellen.md`) abgeglichen; trifft sie den Ausgang, benennt sie den Akteur oder das Datum richtig, erhält der Fall `contaminated: true`. Ein „Nein“ oder „weiß nicht“ eines kleinen Modells gilt nicht als Entwarnung, sondern nur als nicht widerlegte Unkenntnis. Prompt, Modell, Zeitpunkt und vollständige Antwort werden je Frage und Modell protokolliert. Kontaminierte Fälle werden nicht mit der Hauptstichprobe vermischt, sondern in `GESAMT.json` und `GESAMT.md` getrennt ausgewiesen.

Externe Kaltprüfung vor dem Start (14.10.2026, Gemini 3.8 Flash, ohne Websuche, nur Bogentext): Freiburg wurde auch nach
zweiter Anonymisierung erkannt (95 %, Ausgang bekannt), weil Konfliktstruktur und Gebührenmodell selbst der
Fingerabdruck sind. Freiburg gilt deshalb vorab als kontaminiert und zählt nicht zur Primäranalyse. Karlsfeld wurde nach
der zweiten Anonymisierung nicht mehr erkannt. Die Primäranalyse umfasst damit 7 Fälle (4 Ja, 3 Nein).

## Kodierbuch, Zweitkodierung und Verblindung

Die Erstkodierung der realen Akte erfolgte durch die Autoren, die die Ausgänge kannten. Das Kodierbuch (unten) wurde vor dem ersten Simulationslauf festgeschrieben.

**Zweitkodierung:** Sie liegt unter `docs/validation/zweitkodierung/` (je Fall `t0.txt`, `quellen-urls.txt`, `kodierung.json`, Übersicht in `uebersicht.md`). Zweitkodierer ist ein **KI-System (GitHub Copilot)**, das blind gegen die Erstkodierung nur T0, die Primärfrage und die Quellenliste erhielt. Ergebnis: Übereinstimmung in 8 von 8 Fällen, Cohen's Kappa 1,0. **Es gab keine zweite menschliche Person.** Der Wert belegt die Reproduzierbarkeit der Kodierung bei vorgegebenen Quellen, nicht eine menschliche Interrater-Reliabilität; die Quellenliste stammt von der Erstkodierung, und die Nein-Fälle (Kehl, Niederkassel, Wanzleben) bleiben Quellenlücken. Eine zweite menschliche Kodierung bleibt für die konfirmatorische Studie erforderlich.

**Klassifikation der Simulationsausgaben (Entscheidung 14.10.2026):** Es gibt **keine blinde menschliche Kodierung**, sondern eine **Doppelklassifikation durch zwei Sprachmodelle**: Hauptbewerter `gemma4:12b-it-qat-16k`, Zweitbewerter `qwen3.5:9b-agent32k`. Beide sehen weder Arm noch reale Akte. Übereinstimmung der Modelle ist keine Validität. Der Zweitbewerter muss ein anderes Modell als der Hauptbewerter sein und vor dem Start geladen sein; ein Rückfall auf das Hauptmodell mit anderem Seed (`seed_fallback`) ist im Pilot ausgeschlossen, ein Lauf mit Fallback wird nicht gewertet. Für alle Arme (S, D, P) gilt dasselbe Klassifikationsinstrument (Haupt- plus Zweitbewerter).

**Nachtrag nach Probelauf 14.10.2026, vor jedem gewerteten Lauf:** Im konkreten Probelauf ließ `qwen3.5:9b` Ergebnis-IDs aus; außerdem war sein wirksames Kontextfenster für die Klassifikation zu klein. Deshalb ist der Zweitbewerter auf die 32k-Variante `qwen3.5:9b-agent32k` festgelegt. Vor jeder Klassifikation wird `num_ctx` für beide Bewerter über Ollama `/api/show` geprüft und das Stapelbudget daraus abgeleitet; fehlt der Parameter, werden konservativ 4096 Tokens angenommen. Passt bereits Anleitung plus Checkliste nicht, bricht die Klassifikation klar ab. Beim Batching bleibt eine Reserve für Nachfragen; überschreitet die ausführliche Nachfrage dennoch das Budget, wird eine kompakte Fassung mit denselben Daten und Kriterien verwendet. Für jede Ergebnis-ID ist auch bei `yes:false` genau ein Eintrag vorgeschrieben. Als geliefert gilt eine ID nur mit einem booleschen oder eindeutig erkannten Ja-/Nein-Wert. Fehlende IDs werden höchstens zweimal gezielt mit denselben Beiträgen und Regeln nachgefragt; die Nachfrage übernimmt ausschließlich die angeforderten IDs und kann keine andere Erstantwort ändern. Danach weiterhin fehlende IDs bleiben `unclassified` und werden niemals still als Nein gewertet. Ein Ja ohne gültigen Beleg wird als Nein gewertet und im Audit mit `evidence_rejected` kenntlich gemacht. Kontextbudget, fehlende IDs vor und nach den Nachfragen sowie verworfene, nicht angeforderte Nachfragezeilen stehen im Klassifikationsaudit.

**Messbarkeit je Fall:** Ein Fall ist je Arm erst messbar, wenn mindestens 4 von 5 Läufen klassifiziert sind (kein Dissens, kein Ausfall). Strittige und unklassifizierte Läufe zählen nicht zu `n` und werden je Arm ausgewiesen. Bei Kappa unter 0,6 gilt das Ergebnis als nicht hinreichend messbar. **Menschliche Stichprobenprüfung:** Nach dem Lauf prüft eine Person eine Stichprobe von mindestens 10 % der Einzelklassifikationen aus `classification.json` (zufällig, vorab nach Arm geschichtet, Arm erst nach der Prüfung aufgedeckt) und berichtet die Abweichungsquote; sie ersetzt keine menschliche Zweitkodierung.

**Degeneriertes Kappa:** Haben beide Bewerter über alle Läufe eines Primärergebnisses keine Varianz (durchweg „Ja“ oder durchweg „Nein“), ist Kappa nicht definiert. Das heißt „Instrument nicht prüfbar“, nicht „widerlegt“, und wird nicht als Beleg gegen die Nutzenbehauptung gewertet; das Urteil lautet dann „nicht prüfbar“ (siehe Entscheidungsregel). Gibt es gar kein auswertbares Bewerterpaar (kein Lauf, den beide klassifiziert haben), ist Kappa `null` und nicht `0,0`.

**Technische Laufqualität (Entscheidung 14.10.2026):** Ein Simulationslauf zählt nur, wenn er mindestens `min_posts` neue Beiträge hat. Im Rahmen ist `min_posts` fest 3 (nicht mehr die Agentenzahl), weil Likes, Kommentare und Follows nicht als Beitrag zählen und passive Agenten legitime Läufe sonst durchfallen ließen. Über den Fehlschlag entscheidet allein `min_posts` und die Fehlerquote; ein fehlendes, leeres oder aktionsloses `actions.jsonl` wird getrennt ausgewiesen (`action_log_status`: `fehlt`, `leer`, `ohne_aktionen`, `vorhanden`). Ohne zählbare Aktion ist die Agenten-Fehlerquote `unbekannt` (nicht 0); sie wird dann nicht gegen den Grenzwert geprüft und macht den Lauf nicht allein zum Fehlschlag. Drei technische Fehlschläge eines Seeds sperren ihn (`attempts_exhausted`); die Meldung nennt dann die Ursache (z. B. zu wenige Beiträge, `min_posts` prüfen).

Zahlen, die auch in der versteckten Frage (`text_de`) stehen, zählen nicht als starker Treffer (die 14 aus „Innerhalb von 14 Tagen“). Steht dieselbe Zahl zugleich als echter Fakt in `verlauf.md` oder `quellen.md`, wird eine Antwort mit dieser Zahl nicht als Treffer erkannt; die Erkennung ist dort schwächer, das ist akzeptiert.

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

`isolated` (isolierte Agenten) ist **nicht Teil des Pilotrahmens**; mit `--rahmen pilot-v5` sind keine Zusatzarme erlaubt. Eine spätere explorative Ausführung ginge nicht in die Entscheidungsregel ein, und ein Unterschied zu S dürfte **nicht als Vernetzungseffekt gelesen werden**, weil sich die Arme in mehr als einem Merkmal unterscheiden. `blind_feed` wurde am 14.10.2026 aus dem Pilot-Protokoll entfernt; er ist nicht Teil des Rahmens.

**Nachtrag vor dem ersten Lauf (14.10.2026, vor Probelauf):** Die Modelle werden in den lokal gebauten Varianten mit 16k-Kontext genutzt (`gemma4:e4b-it-qat-16k`, `gemma4:12b-it-qat-16k`; gleiche Gewichte wie die Basismodelle, nur größeres Kontextfenster), weil die Basismodelle mit kleinem Standardkontext lange Transkripte abschneiden würden. Es lag zu diesem Zeitpunkt kein Ergebnis vor.

**Modelle je Rolle (Entscheidung 14.10.2026):** Alle Textarme (die Agenten von S sowie D und P) nutzen dasselbe Modell, das Agentenmodell `gemma4:e4b-it-qat-16k`. Damit trennt Skill(S,D) Schwarm gegen Einzelmodell, nicht kleines gegen großes Modell. Die Klassifikation nutzt für alle Arme dasselbe Instrument (Haupt- und Zweitbewerter, siehe Kodierbuch). Die Modelle je Rolle stehen im Rahmen (`rahmen-pilot-v5.json`) und werden in `GESAMT` ausgewiesen.

Der Aufruf mit `--rahmen pilot-v5` umfasst genau S, D und P. Die Prognose eines Falls ist je Arm die Häufigkeit des Primärergebnisses über Seeds, nicht ein einzelner Seed. Seeds werden innerhalb eines Falls zwischen Armen gepaart.

## Rahmen

Vorgeschlagen, Start erst nach Freigabe des Projektinhabers. Bis zu dieser Freigabe wird kein echter Lauf gestartet. Freiburg wird nicht gestartet.

| Größe | Wert |
|---|---|
| Fälle | 7 (Primäranalyse, ohne das vorab kontaminierte Freiburg) |
| Arme | `baseline`, `null_document`, `null_personas` |
| Seeds | 5 |
| `minutes_per_round` | 240 |
| `hours` | 336 |
| GPU-Schätzung | 33–72 h, Mitte rund 50 |
| Modelle | Textarme `gemma4:e4b-it-qat-16k`; Klassifikation `gemma4:12b-it-qat-16k` plus `qwen3.5:9b-agent32k`, kein `seed_fallback` |
| Gültige Läufe je Fall | 1 (siehe unten) |
| Probelauf | 1 synthetischer, nicht gewerteter Fall, 2 Seeds |

**Fallmenge und Läufe (Entscheidung 14.10.2026):** Die gewertete Fallmenge muss exakt den 7 Fällen des Rahmens entsprechen (`case_ids` im Rahmen); fehlt ein Fall, ist ein Fremdfall enthalten oder weicht Rahmen oder Armmenge ab, lautet das Urteil „nicht prüfbar“. Je Fall gibt es **einen gültigen Lauf**. Eine Wiederholung ist nur bei technischem Ausfall zulässig (Backend- oder Ollama-Ausfall, Plattenfehler, Abbruch ohne Ergebnis), nie wegen des Ergebnisses; ein Fall wird nicht mit neuem State neu gewürfelt. Alle `ensemble_id` (auch verworfene Läufe, mit Grund) werden im Protokoll geführt.

**Probelauf (Entscheidung 14.10.2026):** Vor dem Pilot läuft ein Probelauf mit einem synthetischen Fall, der nicht zu den 7 gehört und nicht gewertet wird, mit kleinem Rahmen (2 Seeds). Er prüft Varianz der Klassifikation und Kappa. Zeigt er keine Varianz (degeneriertes Kappa), ist das Instrument nicht prüfbar; das ist vor dem Pilotstart zu klären und kein Ergebnis über die Nutzenbehauptung.

Der Aufruf erzwingt diese Werte über `--rahmen pilot-v5`. Die Datei `docs/validation/rahmen-pilot-v5.json` enthält genau dieselben Zahlen. Weicht ein Einzelwert per CLI ab, bricht das Werkzeug mit einer Meldung ab. `GESAMT` protokolliert den Rahmen.

Herleitung der GPU-Schätzung auf einer RTX 3070: 336 Stunden bei 240 Minuten sind 84 Runden. Arm S: 7 Fälle × 5 Seeds × 35–70 Minuten = 20–41 Stunden. D und P: 70 Seeds × 5–10 Minuten = 6–12 Stunden. Vorbereitung 4–11 Stunden, Klassifikation 3–8 Stunden. Summe 33–72 GPU-Stunden, Mitte rund 50. Ohne Wiederholungen seriell etwa zwei bis drei Tage. Der Default-Takt von 60 Minuten ohne `--rahmen` gilt nicht für diesen Piloten.

## Auswertung

**Primär:** 7 Fälle (alle außer dem vorab als kontaminiert eingestuften Freiburg).

**Vorab fixierte Sensitivitätsanalyse:** nur die 4 nicht kontaminierten Fälle ohne Quellenlücke (Karlsfeld, Kuppenheim, Neuwied, Unterschleißheim). Ausgeschlossen werden Kehl, Niederkassel und Wanzleben, deren „Nein“ auf Quellenlücken beruht. Weitere Sensitivitätsanalysen (z. B. ohne kontaminierte Fälle) werden getrennt ausgewiesen; nachträgliche Analysen gelten als explorativ.

Primäre Zielgröße ist der Brier-Score der Fallhäufigkeiten gegen die adjudizierte reale Kodierung. Berichtet werden der Brier-Score je Arm sowie `Skill(S,D) = 1 − BS_S / BS_D`, `Skill(S,P) = 1 − BS_S / BS_P` und `Skill(P,D) = 1 − BS_P / BS_D`. Das 95-%-Intervall entsteht durch 10.000 Bootstrap-Ziehungen ganzer Fälle mit Zurücklegen. Weder Fragen noch Seeds werden als unabhängige Einheiten resampelt.

Zusätzlich wird die Kalibrierungssteigung aus einer logistischen Regression des Ereignisses auf den Logit der prognostizierten Häufigkeit berechnet. Unter 25 auswertbaren Fällen lautet der feste Hinweis „Pilot, keine Kalibrierungsaussage“.

## Entscheidungsregel

Festgeschrieben am 14.10.2026 vor jedem Lauf (gerichtete Regel). Im Pilot (unter 25 gewerteten Fällen) gilt die Aussage nur als bestanden, wenn gleichzeitig alle vier Bedingungen erfüllt sind:

1. das 95-%-Fall-Bootstrap-Intervall von `Skill(S,D) = 1 − BS_S / BS_D` liegt vollständig über 0;
2. das 95-%-Fall-Bootstrap-Intervall von `Skill(S,P) = 1 − BS_S / BS_P` liegt vollständig über 0 (S ist im Brier-Sinn genauer als P; ein bloß von 0 verschiedener Abstand der Ja-Anteile genügt nicht);
3. Kappa beträgt für jedes gewertete Primärergebnis mindestens 0,6 (die KI-Zweitkodierung der realen Akte liefert 1,0, ersetzt aber keine menschliche Zweitkodierung);
4. alle 7 Fälle des Rahmens sind gewertet (Fallmenge exakt wie im Rahmen, ein gültiger Lauf je Fall, Messbarkeit mindestens 4 von 5 klassifizierte Läufe je Arm).

Liegt das Intervall von `Skill(S,D)` vollständig unter 0, lautet der Status „nicht bestanden“, auch wenn andere Größen fehlen. Ist eine andere prüfbare Bedingung verletzt (insbesondere Intervall von `Skill(S,P)` nicht ganz über 0 oder Kappa unter 0,6), lautet das Urteil „nicht bestanden“. Fehlt eine Größe, ist die Fallmenge nicht exakt die des Rahmens oder ist das Instrument nicht prüfbar (degeneriertes Kappa ohne Varianz, Fälle nicht messbar), lautet das Urteil „nicht prüfbar“. „bestanden“ wird nicht nachträglich aufgeweicht. Wird mindestens ein Primärergebnis wegen Kappa unter 0,6 aus der Wertung genommen, zählt `GESAMT` diese Fälle mit Anteil; ist der Anteil größer als 0, lautet das Pilot-Urteil „nicht bestanden (Instrument unzuverlässig)“. Ein nicht definiertes Kappa wegen fehlender Varianz ist davon ausgenommen und führt zu „nicht prüfbar“ (siehe Kodierbuch, degeneriertes Kappa). Die Kalibrierungssteigung wird nur ausgewiesen, mit dem festen Hinweis „Pilot, keine Kalibrierungsaussage“, und ist kein Bestehenskriterium.

Ab 25 gewerteten Fällen (konfirmatorische Studie, eigener Rahmen) gelten dieselben Bedingungen 1 bis 3, Bedingung 4 mit der Fallmenge des dann festgeschriebenen Rahmens, und zusätzlich liegt die Kalibrierungssteigung von S im Intervall [0,5; 1,5].

Alle Vergleiche mit `isolated` sind nicht Teil des Rahmens und gehen nicht in die Entscheidungsregel ein. Wegen des Pilotcharakters kann auch ein „bestanden“ keine Kalibrierung belegen.

## Falsifikationskriterien

Bereits der Pilot widerspricht der Nutzenbehauptung, wenn der Skill klar negativ ist, `Skill(S,P)` nicht über 0 liegt, S also nicht genauer als P ist und damit über Rollenzerlegung hinaus kein Schwarmbeitrag sichtbar wird, oder ein definiertes Kappa unter 0,6 liegt (degeneriertes Kappa ohne Varianz widerlegt nicht, es macht das Instrument nicht prüfbar). Ein nicht bestandenes oder nicht prüfbares Vorab-Kriterium darf nicht als Bestätigung umgedeutet werden. Kontaminierte Fälle und nachträglich ergänzte Ergebnisse werden nur als Sensitivitätsanalyse berichtet. Die Ergebnisse der Sensitivitätsanalysen dürfen das Urteil der Primäranalyse über 7 Fälle nicht ersetzen.

## Rechenaufwand

Der vorgeschlagene Pilotrahmen steht im Abschnitt Rahmen: 33–72 GPU-Stunden, Mitte rund 50. Start erst nach Freigabe des Projektinhabers. Hinzu kommen Ontologie- und Profilvorbereitung, die Doppelklassifikation und menschliche Stichprobenprüfung der Simulationsausgaben, den Probelauf, Adjudikation und Wiederholungen technisch fehlgeschlagener Läufe. Für mindestens 25 konfirmatorische Fälle ist der Aufwand entsprechend hochzurechnen.

## Betrieb (Nachtrag 14.10.2026)

**Preflight vor jedem Fall und vor dem Probelauf:**

- Plattenplatz: freier Platz auf dem Datenträger der Laufordner mindestens so groß, dass alle erwarteten Läufe passen (ca. 105 Laufordner mit OASIS-DB, Transkripten und Audit-JSON); der konkrete Mindestwert wird im Treiber festgelegt und im Lauf protokolliert. Unterschreitung bedeutet Abbruch vor dem Start.
- Modelle geladen: `gemma4:e4b-it-qat-16k`, `gemma4:12b-it-qat-16k` und `qwen3.5:9b-agent32k` sind in Ollama vorhanden und ansprechbar (`/api/tags`). Fehlt der Zweitbewerter, startet der Fall nicht (kein `seed_fallback`).
- Busy-Check: kein anderer laufender Ensemble-, Simulations- oder OASIS-Prozess, keine Waisenprozesse einer früheren Sitzung, GPU nicht anderweitig belegt.

**Neustartverhalten:** Ein Aufruf mit identischem State setzt am letzten dauerhaften Schritt wieder auf; bereits abgeschlossene Seeds werden übersprungen. Ein Backend- oder Ollama-Neustart gilt als technischer Ausfall und rechtfertigt eine Wiederholung nur für den betroffenen, nicht abgeschlossenen Lauf. Vor dem Wiederanlauf sind Preflight und Prüfung auf Waisenprozesse zu wiederholen; die Versuche sind mit `ensemble_id` und Grund zu protokollieren. Ein Lauf mit ausgefallener Klassifikation oder Agentenfehlern wird nicht als gültig mit „Nein“ gezählt, sondern als unklassifiziert ausgewiesen.

**Manueller Reset:** Sind Seed-Versuche oder Resume-Limit ausgeschöpft (`attempts_exhausted`) und der Fall damit gesperrt, ist nach Behebung der Ursache ein manueller Reset nötig: die Ursache beheben (Ollama, Platte), Waisenprozesse beenden, den betroffenen Ensemble-Ordner und `docs/validation/ergebnisse/<fall>.state.json` sichern, die Sperrmarke im Ensemble-Zustand zurücksetzen und den Fall wie ein technisch ausgefallenen Lauf wiederholen. Der Reset wird mit Datum, Grund und allen betroffenen `ensemble_id` in diesem Protokoll nachgetragen; er darf nie dazu dienen, ein unerwünschtes Ergebnis zu ersetzen.
