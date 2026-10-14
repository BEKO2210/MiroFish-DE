# Validierungsstand MiroFish-DE (Stand 14.10.2026)

Zweck: knappe, nüchterne Übersicht für Außenstehende und für andere Modelle, die den Stand bewerten sollen. Alle
Angaben stützen sich auf Dateien in diesem Repository (Verweise jeweils angegeben). Es gibt **keinen Beleg, dass die
Simulation Prognosen liefert, die besser sind als ein einzelnes Sprachmodell oder die Wirklichkeit treffen.** Das
Projekt hat bisher Messwerkzeuge und eine Studienplanung gebaut, aber keine Wirklichkeitsmessung ausgeführt.

## Kurzfassung

- Gebaut: ehrlicher Bericht, Seeds und Manifest, Mehrfachläufe mit Statistik, Gegenproben, Studienprotokoll für den
  Realitätsabgleich (V5), sieben dokumentierte Fälle mit bekanntem Ausgang.
- Gemessen: ein Mehrfachlauf zu einem Hallenbad-Szenario (Nachtlauf 13./14.10.2026). Er belegt die Nutzenbehauptung nicht.
- Nicht gemessen: Trefferquote gegen reale Fälle (V5). Der GPU-Pilot ist **nicht gestartet**.
- Freigabe für den GPU-Pilot: in allen drei Prüfrunden **Nein** (siehe unten). Der Rahmen ist „vorgeschlagen, Start erst
  nach Freigabe des Projektinhabers“.

## Die Stufen V1–V5

Quelle: `docs/ROADMAP.md` (Abschnitt Validierung), Umsetzung in `docs/VALIDIERUNG.md`.

| Stufe | Was sie prüft | Erledigt | Nicht belegt |
|---|---|---|---|
| V1 Ehrlicher Bericht | Ob der Bericht nur ausweist, was simuliert wurde: Abschnitt „Methodik und Grenzen“ aus den Daten, kein Erzählen über den simulierten Zeitraum hinaus, kalibrierte Sprache, Einzellauf = „Szenario“ | Umgesetzt und live (Stand 13.10.2026) | Dass Leser den Bericht tatsächlich richtig einordnen |
| V2 Reproduzierbarkeit | Seeds für Simulation und Sprachmodell, Lauf-Manifest, Ereignis-Log im Export; Kriterium: gleicher Seed → gleiche Aktionen, Nichtdeterminismus gemessen | Seeds, Manifest, `events.jsonl` umgesetzt | Die Messung „gleicher Seed → gleiche Aktionen“ liegt nicht vor; die Gutachten benennen Lücken (Ziehungsreihenfolge, Manifest-Eingabe) |
| V3 Mehrfachlauf | N Läufe mit verschiedenen Seeds, Ergebnis-Checkliste je Lauf per Klassifikator, Häufigkeiten mit Intervallen; Zuverlässigkeit des Messinstruments (V3c) | Maschine und Oberfläche live; Stapel-Klassifikation, eigene Ja/Nein-Fragen, Kappa je Ergebnis, gepaarter exakter McNemar-Test, Holm nur für Exploratives, ein Primärergebnis; KI-Zweitkodierung | Menschliche Zweitkodierung; dass das Instrument auf realen Fällen reliabel ist (Kappa bisher nur an KI-Kodierung der Akten, siehe unten) |
| V4 Gegenproben | Ablationen (`isolated`, `without:<Typ>`, `blind_feed`), Nullmodell(e) als Vergleich, Sensitivität | Ablationen und Nullmodelle `null_document`/`null_personas` implementiert | V4b: Sensitivität mit Eingriffsstärke als Variable ist laut Roadmap offen. Die Ablationen sind laut Gutachten nicht rein (siehe Einordnung) |
| V5 Realitätsabgleich | Blind simulieren auf Material vor dem Ereignis, Ergebnis gegen den tatsächlichen Verlauf werten (Brier-Score, Skill, Kalibrierung) | Vorregistrierung `PROTOKOLL-V5.md`; 8 Fallakten in `faelle/`, davon 7 primär (Freiburg vorab als kontaminiert, nicht gewertet); Treiber `backend/scripts/validate_case.py`, `run_pilot_v5.py`; Trockenlauf gegen API-Attrappe | **Kein echter Lauf.** Keine Skill-Werte, keine Kalibrierung, keine Aussage über reale Treffer. Im Repo liegt kein Ergebnisordner und kein dokumentierter Probelauf |

Weitere offene Punkte laut `docs/ROADMAP.md` (Stand 14.10.2026): menschliche Zweitkodierung; mindestens 25 Fälle für
eine konfirmatorische Aussage (bisher 7 primär, also Pilotcharakter).

## Die drei Prüfrunden vor dem GPU-Pilot (alle 14.10.2026)

Alle drei sind Lesegutachten (nur gelesen, nichts geändert). Alle kamen zu **Freigabe: Nein**.

| Reihenfolge | Prüfer | Datei | Freigabe |
|---|---|---|---|
| 1 | Grok | [PRUEFUNG-V5-GROK-2026-10-14.md](PRUEFUNG-V5-GROK-2026-10-14.md) | Nein |
| 2 | Grok (zweiter Durchgang) | [PRUEFUNG-V5-GROK-2026-10-14-B.md](PRUEFUNG-V5-GROK-2026-10-14-B.md) | Nein |
| 3 | Copilot | [PRUEFUNG-V5-COPILOT-2026-10-14.md](PRUEFUNG-V5-COPILOT-2026-10-14.md) | Nein |

Davor gab es ein Gutachten zum Nachtlauf: [GUTACHTEN-GROK-2026-10-14.md](GUTACHTEN-GROK-2026-10-14.md).

### Runde 1 (Grok)
- Befunde: Protokoll war Vorlage statt Vorregistrierung der Fälle; drei Nein-Kodierungen (Kehl, Niederkassel,
  Wanzleben) sind Quellenlücken; Bögen für Modelle mit Weltwissen erkennbar; Default 168 statt 336 Stunden; ein
  Seed-Absturz verwirft das Ensemble ohne Wiederaufnahme; GPU-Zeit im Protokoll um den Rundenfaktor zu niedrig.
- Umsetzung (laut Prüfung 2 und Commits): Protokoll auf die Fälle und den einheitlichen Primärsatz festgelegt, Freiburg
  vorab kontaminiert und ohne Start, Default 336 Stunden, Kappa ohne Varianz = `null`, Retry und Resume, genau ein
  Primärergebnis.

### Runde 2 (Grok)
- Befunde: Entscheidungsregel widerspricht dem Skript; Kaltfrage sieht den Ordnernamen; Rechenrahmen offen. Zweitkodierung
  nur KI (Kappa 1,0), keine zweite Person; Kalibrierungssteigung bei 7 Fällen nie berechnet; Kappa-Bedingung kann in der
  Gesamtwertung nicht scheitern.
- Umsetzung: Regel gerichtet gemacht, Kaltfrage nimmt den Ort aus `kaltfrage_ort`, Rahmen per `--rahmen pilot-v5`
  erzwungen (Commit `661ee80`, danach Protokoll-Entscheidungen `f21973e`).

### Runde 3 (Copilot)
- Befunde: stiller Messfehler bei Ollama-Ausfall (ausgefallene Klassifikationsstapel zählten als „Nein“); Lücken in der
  Entscheidungsregel (keine Untergrenze gewerteter Fälle, Regel nicht gerichtet); Retry-Schwächen; Kaltfrage nicht
  tragfähig; Agentenmodell ≠ Modell der Nullarme (Konfundierung); stiller Rückfall des Zweitbewerters; Betriebsrisiken
  (Waisenprozesse, Plattenplatz); Primärergebnis womöglich in allen Armen „Ja“ (Varianzproblem, Probelauf gefordert).
- Umsetzung laut Commits `f21973e` und `a14b817`: gerichtete Regel (Skill S/D und S/P über 0, Kappa ≥ 0,6), exakt 7
  Fälle, Rahmenabweichung = „nicht prüfbar“, Backoff bei transienten Fehlern, Freitext-Kaltabruf mit beiden Modellen,
  gleiches Modell für alle Textarme, Zweitbewerter ohne Fallback, Preflight im Treiber, Probelauf-Modus mit synthetischem
  Fall (`probe/`), `blind_feed` aus dem Pilot genommen.
- **Nicht belegt:** Copilot verlangte eine erneute unabhängige Prüfung nach der Umsetzung. Eine solche liegt im
  Repository nicht vor. Der Probelauf (synthetischer Fall, 2 Seeds) ist als Modus implementiert; ein Ergebnis ist nicht
  dokumentiert. Die Umsetzung wurde in diesem Dokument nicht erneut gegen den Code geprüft.

## Bisherige Messergebnisse: Nachtlauf `ens_9c4647555d4b`

Neutrales Hallenbad-Szenario, je 10 × 24 h. Basis = Schwarm mit Vernetzung, isoliert = Agenten nur mit Posten/Nichtstun,
Nullmodell = ein Sprachmodell schreibt die Geschichte. Anteile = Läufe mit dem Ergebnis (isoliert: N = 9, ein Lauf blieb
unklassifiziert). Die Tabelle steht als vorgelegte Auszählung in `GUTACHTEN-GROK-2026-10-14.md`; die zugehörige
`ensemble.json` lag beim Gutachten nicht im Arbeitsbaum vor.

| Ergebnis | Basis | Isoliert | Nullmodell |
|---|---:|---:|---:|
| Elternversammlung | 1/10 | 2/9 | 6/10 |
| Medien bringen Stellungnahme | 10/10 | 9/9 | 3/10 |
| Vereine, gemeinsame Erklärung | 2/10 | 4/9 | 0/10 |
| Opposition fordert Kostenprüfung | 8/10 | 6/9 | 2/10 |
| Debatte Stadtpolitik↔Eltern | 10/10 | 0/9 | 0/10 |
| Medien reagieren nicht | 0/10 | 0/9 | 5/10 |

**Einordnung: Diese Zahlen belegen die Nutzenbehauptung nicht** (Gutachten, Kurzurteil):
- Basis und isoliert trennen sich bei den fünf Ereignis-Ergebnissen nicht.
- Der Abstand zum Nullmodell ist mit Personas, Textmenge und unterschiedlicher Kodierregel vermengt.
- Die Debattenzeile (10/10 gegen 0/9 gegen 0/10) ist durch die Messdefinition erzwungen: Das Nullmodell setzt
  Interaktion fest auf Nein, isolierte Agenten können die verlangte Datenbankkante nicht erzeugen.
- Zwölf Vergleiche ohne Korrektur; nach Korrektur bleibt nichts, was die Behauptung trägt.
- Das Messinstrument war nicht reliabel: Dieselben Daten ergaben in zwei Auswertungen 1/10 und 6/10 (`ROADMAP.md`, V3c).
- Es ist ein Szenario, ein Modell, eine eingefrorene Besetzung; über die Wirklichkeit sagt der Lauf nichts.

Aus dem Nachtlauf folgten Korrekturen (Stapel-Klassifikation, Beleg für Interaktionen, Abwesenheitsfragen, gepaarte
Statistik, angeglichene Nullarme); die Zahlen oben wurden damit nicht neu erhoben.

## Pilotrahmen V5 (`rahmen-pilot-v5.json`)

**Status: vorgeschlagen, Start erst nach Freigabe des Projektinhabers.** Bis dahin wird kein echter Lauf gestartet.

| Größe | Wert |
|---|---|
| Fälle | 7: Karlsfeld, Kehl, Kuppenheim, Neuwied, Niederkassel, Unterschleißheim, Wanzleben (Freiburg nicht gestartet) |
| Arme | `baseline` (Schwarm, S), `null_document` (D), `null_personas` (P) |
| Seeds / Takt / Zeitraum | 5 Seeds, 240 Minuten je Runde, 336 Stunden (84 Runden) |
| Modelle | Textarme `gemma4:e4b-it-qat`; Klassifikation `gemma4:12b-it-qat` + `qwen3.5:9b-agent32k`, kein Seed-Fallback |
| GPU-Schätzung (RTX 3070) | 33–72 h, Mitte rund 50 (Schätzung aus Prüfung 2, nicht gemessen) |
| Entscheidungsregel | „bestanden“ nur, wenn Skill(S,D) und Skill(S,P) ganz über 0 liegen (95-%-Fall-Bootstrap), Kappa ≥ 0,6 und alle 7 Fälle gewertet; sonst „nicht bestanden“ oder „nicht prüfbar“ (`PROTOKOLL-V5.md`) |

Primärergebnis aller Fälle: „Innerhalb von 14 Tagen veröffentlicht mindestens ein organisierter Akteur (Ratsfraktion,
Verein, Verband oder Bürgerinitiative) eine ablehnende Stellungnahme gegen die Maßnahme.“ Wahrheit der 7 Fälle: 4 Ja
(Karlsfeld, Kuppenheim, Neuwied, Unterschleißheim), 3 Nein (Kehl, Niederkassel, Wanzleben; laut Protokoll Quellenlücken).

Bekannte Schwächen des Rahmens: 7 Fälle sind eine Pilotgröße; die Kodierung der realen Ausgänge ist nur KI-zweitkodiert;
die drei Nein-Fälle beruhen auf fehlenden Belegen, nicht auf belegter Abwesenheit; fünf Seeds rastern jede Rate in
Sechsteln; ein einziger Lauf je Fall; Ausgänge liegen bei Modellen mit Weltwissen womöglich teilweise vor (Kaltabruf
soll das prüfen, ersetzt es aber nicht).

## Was der Pilot bestenfalls aussagen kann

- Ob auf diesen 7 Fällen der Schwarm im Brier-Sinn genauer ist als das Einzelmodell mit Dokument (D) und als das
  Einzelmodell mit denselben Personas (P), mit Fall-Bootstrap-Intervall.
- Ob das Instrument mit Kappa ≥ 0,6 messbar ist und ob das Primärergebnis bei diesem Takt überhaupt Varianz zeigt.
- Ein negatives Ergebnis (Skill ≤ 0, Kappa < 0,6) wäre ein Hinweis gegen die Nutzenbehauptung.

## Was der Pilot nie aussagen kann

- Keine Kalibrierung: Dafür sind laut Protokoll mindestens 25 Fälle in eigenem Rahmen nötig; bei weniger gilt der Hinweis
  „Pilot, keine Kalibrierungsaussage“. Auch ein „bestanden“ belegt keine Kalibrierung.
- Keine repräsentative Trefferquote, keine Aussage über andere Fragetypen, Städte, Modelle oder Zeiträume.
- Keine menschliche Interrater-Reliabilität (nur KI-Zweitkodierung) und keine belegte Abwesenheit in den drei
  Quellenlücken-Fällen.
- Kein Vernetzungseffekt: `isolated` ist nicht Teil des Rahmens und eine Ablation unterscheidet sich in mehr als einem
  Merkmal.
- Kein Nachweis über Wirkung realer Eingriffe; die Simulation bildet ein Sprachmodell-Verhalten ab, keine Bevölkerung.
- Mehr Seeds messen die Streuung des Aufbaus, nicht die Wirklichkeit; die unabhängige Einheit ist der Fall.

## Weitere Dateien

- Protokoll (Vorregistrierung, Kodierbuch, Entscheidungsregel, Betrieb): [PROTOKOLL-V5.md](PROTOKOLL-V5.md)
- Fälle und Quellen: [faelle/README.md](faelle/README.md); Zweitkodierung: [zweitkodierung/uebersicht.md](zweitkodierung/uebersicht.md)
- Umsetzung und Statistikgrenzen: [../VALIDIERUNG.md](../VALIDIERUNG.md); Planung: [../ROADMAP.md](../ROADMAP.md)
