# Validierung V1–V4

Umsetzung der Roadmap-Stufen **V1 (ehrlicher Bericht)**, **V2 (Reproduzierbarkeit)**,
**V3 (Mehrfachlauf)** und **V4 (Gegenproben)** (Stand 13.10.2026).

## Was V1 leistet

- Deterministischer Abschnitt **„Methodik und Grenzen“** aus Laufdaten (kein LLM): Läufe, Agenten + Typen, simulierte Stunden/Runden, Beiträge/Aktionen je Plattform (SQLite `twitter_simulation.db` / `reddit_simulation.db`), Modelle, Startbeiträge, Seed, Zeitpunkt.
- Fester Satz: *„Ein einzelner Lauf zeigt einen möglichen Verlauf, keine Wahrscheinlichkeit.“*
- API-Feld `methodology` am Bericht (`GET /api/report/<id>`), zusätzlich angehängt an `full_report.md`.
- **Vorgabe-Abgleich:** Kernaussagen (Blockzitate, fett ≥ 8 Wörter, Sätze mit Zahlen/Wahrscheinlichkeitswörtern; Duplikate mit Zähler) gegen `extracted_text.txt` und jeden `initial_post`. Vergleich über **Inhaltswörter** (Kleinschreibung, Umlaute, Stoppwörter DE+EN weg, Stamm = erste 6 Zeichen): Treffer, wenn ≥ 70 % der Inhaltswörter (mind. 4) in einem Fenster aus 1–2 aufeinanderfolgenden Sätzen vorkommen. Ausgabe je Treffer: Aussage, Quelle (Material/Startbeitrag), kurze Fundstelle, Überdeckung %; 5-Gramm-Wert nur als Zusatzinfo.
- Prompt-Regeln: harte Zeitgrenze in Stunden/Tagen, keine Wahrscheinlichkeiten bei Einzellauf, Forderung ≠ Ereignis, Zitate nur aus Simulation, Titel „Szenario-Bericht“.
- Frontend (`Step4Report.vue`): Hinweis „Szenario aus 1 Lauf“ / „N Läufe“, Methodik-Infokarte am Ende (Token-Farben, DE/EN).

## Was V2 leistet

- **Seed** beim Start (`POST /api/simulation/start` optional `seed`, sonst zufällig) → `--seed` an `run_*_simulation.py`, dort `random` / `numpy` / `torch`, LLM `model_config_dict` mit `seed` + `temperature` (`OASIS_LLM_TEMPERATURE`, Standard 0,7); `reasoning_effort` für lokale Anbieter bleibt.
- **`manifest.json`** im Simulationsordner: SHA-256 der Dokumente und der Frage, Modelle, Seed, Temperatur, Hash der `simulation_config.json`, git-Commit (falls verfügbar), Start/Ende, Aktionszahl.
- **Export:** ZIP enthält zusätzlich `events.jsonl` (Zeit, Runde, Plattform, Agent, Typ, Text) und `manifest.json` (bei Bedarf nachgezogen).

## Prüfung

```bash
cd backend && python3 -m pytest -q tests
cd frontend && npx vite build
cd e2e && PW_PORT=4175 npx playwright test
```

Gezielte Unit-Tests: `tests/test_report_validation.py` (Umformulierung Bürgerentscheid vs. Material, neutrale
Gegenprobe, Fixtures `tests/fixtures/report_musterstadt.md` + `musterstadt-eingabe.txt`, Mini-DB-Methodik, Manifest)
und `tests/test_ensemble.py` (Wilson/Newcombe, Checklisten-Parsing, Belegprüfung, Akteursentfernung,
Zustandsmaschine mit gemocktem Runner).

Manuell: Bericht neu erzeugen; Methodik-Zahlen müssen zur DB passen; Export-ZIP öffnen und `manifest.json` / `events.jsonl` prüfen.

## V3: Mehrfachlauf

Ein Ensemble beginnt mit einer bereits vorbereiteten Simulation. Profile und `simulation_config.json` werden für jeden
Lauf kopiert, nicht neu erzeugt. Damit bleiben Akteursauswahl und Personas konstant; nur der Seed ändert sich nach dem
Schema `Basisseed + Laufnummer`. Die gewünschte Dauer ersetzt `total_simulation_hours`. Alle OASIS-Läufe werden seriell
ausgeführt, damit nie zwei Läufe gleichzeitig die GPU bzw. das lokale Hauptmodell beanspruchen. Die Daten liegen unter
`uploads/ensembles/<ensemble_id>/<variante>/run_<n>/`, der Zustand in `ensemble.json`. Nach einem Backend-Neustart wird
ein zuvor laufendes oder wartendes Ensemble als fehlgeschlagen markiert, weil sein Hintergrundthread nicht fortgesetzt
werden kann.

Vor dem ersten Lauf erzeugt das Hauptmodell bei Temperatur 0 und festem Seed fünf bis acht konkrete
Ja/Nein-Ergebnisse aus Frage und Eingabematerial. Jeder Punkt beginnt mit „Im simulierten Zeitraum …“, muss innerhalb
der eingestellten Stunden beobachtbar und allgemein über Akteursgruppen formuliert sein. Die Auswahl mischt Eskalation,
Deeskalation/Kompromiss und genau einen Fall ohne nennenswerte Reaktion. Zahlen und Schwellen aus dem Material sind
verboten; ein deterministischer, formatnormalisierter Zahlenabgleich verwirft entsprechende Entwürfe und lässt die
vollständige Checkliste höchstens zweimal erzeugen.

Zusätzlich zum Inhaltswortabgleich aus V1 fragt eine zweite Prüfung pro Ergebnis bei Temperatur 0 und festem Seed, ob
das Ereignis im Material bereits als geschehen oder angekündigt beschrieben ist. Ein positives Modellurteil zählt nur,
wenn das gelieferte Zitat nach Whitespace-Normalisierung wörtlich im Material vorkommt. `in_material` ist wahr, sobald
Inhaltswortabgleich oder verifiziertes Zitat treffen; `material_snippet` enthält ausschließlich das verifizierte Zitat
(bei einem reinen Inhaltsworttreffer bleibt es leer). Eine solche Markierung
verhindert keine Auswertung, warnt aber vor einer scheinbaren Prognose, die nur die Vorgabe wiederholt.

`POST /api/ensemble/start` akzeptiert außerdem `start_hour` (0–23, Standard 7). Der Wert wird im Ensemble-Zustand und
damit in `GET /api/ensemble/<id>` ausgegeben sowie in jede Laufkonfiguration geschrieben. Runde null beginnt zu dieser
Uhrzeit; weitere Runden addieren `minutes_per_round`, einschließlich des Tageswechsels nach Mitternacht. Dadurch nutzen
Aktivitätsfenster und Aktionslogs dieselbe simulierte Uhrzeit.

Nach jedem Lauf werden die Beiträge unmittelbar aus `twitter_simulation.db` und `reddit_simulation.db` gelesen. Der
Klassifikator erhält keine Berichte. Ein Ja zählt nur, wenn das Modell mindestens eine vorhandene, plattformqualifizierte
Beitrags-ID wie `twitter:17` nennt. Unbekannte IDs verwerfen das Ja. Startbeiträge werden anhand von Autor und Text aus
der Auswertungsmenge entfernt. Dadurch können vorgegebene Aussagen nicht allein durch ihre technische Einspeisung als
Simulationsergebnis zählen.

`POST /api/ensemble/start` akzeptiert optional bis zu sechs eigene Ergebnisfragen als
`custom_outcomes: [{"text_de": "…", "polarity": "presence|absence", "kind": "event|interaction"}]`.
`text_de` ist Pflicht und auf 200 Zeichen begrenzt; Polarität und Art sind optional und werden andernfalls aus dem Text
abgeleitet. Die Punkte werden mit IDs `c1` bis `c6` an die automatische Checkliste angehängt. Jeder Checklistenpunkt
weist seine Herkunft als `source: "auto"` oder `source: "user"` aus. Eigene Punkte durchlaufen denselben
Materialabgleich, dieselbe Belegprüfung und dieselbe Klassifikation wie automatisch erzeugte Punkte.

## V3c: Zuverlässigkeit des Messinstruments

Jeder gespeicherte Lauf wird zweimal unabhängig klassifiziert. Bewerter A nutzt das konfigurierte Hauptmodell;
Bewerter B nutzt `ENSEMBLE_SECOND_RATER_MODEL` (Standard `qwen3.5:9b`) am selben lokalen OpenAI-kompatiblen Server.
Ist das Zweitmodell leer konfiguriert, nicht initialisierbar oder bei allen Klassifikationsstapeln nicht erreichbar,
wird das Hauptmodell mit einem anderen Seed verwendet. `classification.json` enthält Modell, Seed, Rohantwort,
geprüfte Belege und Urteil beider Bewerter sowie das gemeinsame Endurteil.

Das Endurteil ist nur dann Ja, wenn beide Bewerter nach der bestehenden Belegprüfung Ja urteilen. Ja/Nein-Dissens ist
`disputed`, nicht Nein, und wird ebenso wie `unclassified` aus `n`, Rate und Wilson-Intervall ausgeschlossen.
`results.<variante>.<ergebnis>.disputed` weist diese Fälle separat aus. Nicht klassifizierbare Urteile eines Bewerters
ergeben weiterhin `unclassified`.

Über alle Varianten und Läufe werden je Ergebnis die binären, auf beiden Seiten klassifizierten Urteilspaare
zusammengeführt. `reliability.<outcome_id>` enthält Prozent-Übereinstimmung (`agreement`), Cohen's Kappa (`kappa`),
Paarzahl (`n_pairs`) und die Bewertung `messbar` (Kappa ≥ 0,6), `unsicher` (0,4 ≤ Kappa < 0,6) oder
`nicht messbar` (Kappa < 0,4). Bei zwei identischen konstanten Urteilsreihen wird das mathematisch sonst undefinierte
Kappa für diese Anzeige als 1,0 behandelt; ohne auswertbares Paar als 0,0. Vergleiche nicht messbarer Ergebnisse tragen
`unreliable: true` und werden im Markdown-Bericht ausdrücklich nicht gedeutet. Die Doppelbewertung und
Zuverlässigkeitsberechnung gelten unverändert für `reclassify`; es werden dabei keine Simulationen neu gestartet.

## V4: Gegenproben

- `baseline`: unveränderte vorbereitete Simulation.
- `isolated`: Agenten behalten Persona, Frage und Ausgangsmaterial, erhalten aber nur `CREATE_POST` und `DO_NOTHING`.
  Feed-, Empfehlungs-, Such-, Trend-, Follow- und Interaktionsaktionen sind entfernt. In OASIS werden fremde Inhalte
  über diese Plattformaktionen und die Empfehlungstabelle in die Beobachtung gebracht; ein bloßer Wechsel auf den
  Zufalls-Recommender würde weiterhin fremde Beiträge zeigen. Die reduzierte Aktionsoberfläche garantiert dagegen,
  dass ein isolierter Agent keine Beiträge anderer Agenten sieht. Die Gegenprobe misst daher fehlende Vernetzung,
  zugleich aber auch fehlende Reaktionsaktionen – diese Kopplung ist bei der Interpretation zu nennen.
- `without:<AgentTyp>`: Alle Agenten des Typs werden aus beiden Profildateien und der Aktivitätskonfiguration entfernt.
  Ihre Startbeiträge entfallen ebenfalls; verbleibende IDs werden lückenlos neu nummeriert, weil OASIS an mehreren
  Stellen fortlaufende IDs voraussetzt.
- `null_model`: Keine OASIS-Simulation. Das Hauptmodell erhält Eingabedokument, Frage und Zeitraum und schreibt pro Seed
  eine Verlaufserzählung. Die Checkliste wird gegen diese Erzählung klassifiziert; als Beleg gilt nur eine tatsächlich
  enthaltene Textstelle. Das Nullmodell zeigt, welche Ergebnisse bereits ein einzelner Erzähler ohne Agenteninteraktion
  produziert.

Die Isolationsentscheidung folgt der OASIS-Implementierung: `Platform.update_rec_table` befüllt die Empfehlungstabellen;
`REFRESH`, `TREND` und Such-/Interaktionsaktionen machen diese Inhalte für Agenten nutzbar. OASIS bietet Random-, Reddit-,
Twitter- und TWHIN-Recommender, aber keinen eingebauten Recommender „nur eigene Beiträge“. Deshalb wird keine vorhandene
Empfehlungsoption zweckentfremdet, sondern die Sichtbarkeit an der Aktionsgrenze geschlossen.

## Statistik

Für jedes Ergebnis und jede Variante werden `Ja`, `N`, Anteil und ein zweiseitiges 95-%-Wilson-Score-Intervall ohne
Kontinuitätskorrektur ausgegeben. Bei `N = 0` ist das technische Intervall `[0, 0]`; `N` umfasst nur Läufe mit
übereinstimmendem, klassifiziertem Doppelurteil und kann daher kleiner als `runs` sein. Variantenunterschiede sind
`Anteil(Variante) − Anteil(baseline)`. Das 95-%-Intervall der Differenz wird nach Newcombe, Methode 10, aus den vier
Wilson-Grenzen zusammengesetzt und auf `[-1, 1]` begrenzt. Die reine Python-Implementierung wird gegen bekannte
Zahlenwerte getestet.

Der deterministische Markdown-Abschnitt **„Mehrfachlauf“** enthält die Ergebnistabelle einschließlich strittiger und
unklassifizierter Läufe, Wilson-Intervalle, die Zuverlässigkeit je Ergebnis, Hinweise auf bereits im Material vorhandene
Punkte, den Nullmodell-Vergleich und feste Grenzen. Nicht messbare Ergebnisse werden nicht interpretiert. Dafür wird
kein weiteres Modell aufgerufen.

## Rechenzeit und Betrieb

Die Startschätzung verwendet abgeschlossene `run_state.json`-Zeitstempel aus bisherigen Einzel- und Ensemble-Läufen:
Wandzeit geteilt durch tatsächliche Rundenzahl. Ohne Messwerte gelten 40 Sekunden je Runde. Geschätzt werden alle noch
ausstehenden Runden; ein Nullmodell-Lauf zählt als eine Modellrunde. `eta_seconds` sinkt nach abgeschlossenen Läufen.
Die Schätzung kann bei wechselnder Agentenzahl, Anbieterlast oder Kontextlänge deutlich abweichen.

Ein Ensemble kann abgebrochen werden. Der aktive OASIS-Prozess wird über den vorhandenen Runner beendet, noch nicht
begonnene Varianten werden als abgebrochen markiert. Löschen ist während `queued` oder `running` absichtlich gesperrt.
Es wird kein automatischer echter Testlauf gestartet.

## Grenzen von V3/V4

- Mehr Seeds messen Modell- und Aktionsstreuung, nicht die Trefferwahrscheinlichkeit in der realen Welt.
- Gleiche Profile und dasselbe Hauptmodell erzeugen abhängige systematische Fehler, auch wenn die statistischen
  Differenzintervalle unabhängige Binomialstichproben voraussetzen.
- Modellanbieter können Seeds ignorieren oder trotz Seed nicht vollständig deterministisch rechnen.
- Die automatische Checkliste und Klassifikation können relevante Ereignisse auslassen oder falsch einordnen. Die
  geprüften Beitrags-IDs machen positive Urteile auditierbar, ersetzen aber keine fachliche Blindbewertung.
- `isolated` entfernt zugleich Vernetzung und soziale Reaktionsmöglichkeiten. Der Unterschied ist keine reine Schätzung
  eines einzelnen Empfehlungsalgorithmus-Effekts.
- `without:<AgentTyp>` verändert bei entfernten Startbeiträgen sowohl Akteursbestand als auch Ausgangsimpuls. Genau das
  ist für die angeforderte Gegenprobe beabsichtigt, muss aber bei kausalen Aussagen beachtet werden.

## Fehler im ersten Nachtlauf und Korrektur

Im Nachtlauf `ens_9c4647555d4b` wurden alle Beiträge eines Laufs in einer einzigen LLM-Anfrage klassifiziert. Besonders
die isolierten Läufe erzeugten etwa 95.000–100.000 Zeichen (rund 32.000 geschätzte Token). Das lokale Modell hatte
jedoch nur 16.384 Token Kontext. Ollama kürzte die Eingabe still am Anfang; damit fehlten Anweisung und Checkliste, und
die Klassifikation ergab fälschlich durchgehend Nein. Auch die Basisläufe mit etwa 8.000–13.000 Token lagen zu nahe an
der Grenze. Außerdem konnte das negative Ergebnis „Medien reagieren nicht“ technisch nie Ja werden, weil jedes Ja
einen Belegbeitrag verlangte.

Die Korrektur klassifiziert Beiträge nun in reihenfolgetreuen Stapeln. Anweisung, Checkliste und Beiträge bleiben unter
`ENSEMBLE_CLASSIFICATION_TOKEN_BUDGET` (Standard 9.000 geschätzte Eingabetoken bei Zeichen/3); zusätzlich wird Platz
für die Ausgabe innerhalb von `LOCAL_LLM_CONTEXT` (Standard 16.384) reserviert. Selbst ein einzelner überlanger Beitrag
wird dafür in prüfbare Textfragmente zerlegt. `classification.json` im jeweiligen Laufverzeichnis hält je Stapel die
Modellantwort, das geprüfte Ergebnis, die Größe und die Tokenschätzung fest. Belege werden vereinigt und auf fünf pro
Ergebnis begrenzt.

Jeder Checklistenpunkt besitzt die Polarität `presence` oder `absence`. Bei alten Checklisten wird `absence` aus
Formulierungen mit „nicht“, „keine/kein“ oder „bleibt aus“ abgeleitet. Für ein Abwesenheitsergebnis sucht der Prompt
nach dem positiven Gegenereignis; nur wenn es in keinem vollständig klassifizierten Stapel belegt ist, lautet das
Ergebnis Ja. Der Auditbeleg nennt dann „kein passender Beitrag in N geprüften Beiträgen“.

Eine nach zwei Inhaltsversuchen nicht parsebare Stapelantwort wird nicht mehr als Nein behandelt. Der betreffende Lauf
ist für das Ergebnis `unclassified`, wird aus `n` und damit aus Anteil und Wilson-Intervall entfernt und separat unter
`results.<variant>.<outcome>.unclassified` sowie in der Berichtstabelle ausgewiesen.

Bestehende Ensembles können mit `POST /api/ensemble/<id>/reclassify` ohne neue Simulation ausgewertet werden. Der
Hintergrundlauf liest ausschließlich die gespeicherten SQLite-Datenbanken beziehungsweise Nullmodell-Erzählungen,
verwendet dieselbe Checkliste und berechnet Ergebnisse und Vergleiche neu. Der vorherige Ergebnisstand bleibt als
`results_v1` erhalten; Fortschritt und Abschluss sind wie beim ursprünglichen Lauf über `GET /api/ensemble/<id>`
sichtbar.

## Gültigkeitskorrekturen: Abwesenheit, Interaktion und Konsistenz

Checklistenpunkte besitzen zusätzlich `kind: event|interaction`. Neue Checklisten lassen das Feld direkt erzeugen;
bei älteren Checklisten werden Formulierungen mit „zwischen … und“, „Debatte“, „Diskussion“, „antwortet“ oder
„reagiert auf“ als `interaction` migriert. Für jeden solchen Punkt ordnet das Hauptmodell einmal je Lauf anhand von
`entity_type` und `entity_name` die vorhandenen Agenten-IDs den zwei genannten Seiten zu. Zuordnung, Modellantwort,
strukturelle Funde und Entscheidung stehen in `classification.json`.

Ein semantischer Texttreffer allein genügt für Interaktionen nicht mehr. Zusätzlich muss die OASIS-SQLite-DB eine
direkte Verbindung zwischen Agenten der beiden zugeordneten Seiten enthalten: einen Reddit-Datensatz aus `comment`
mit `post_id`, einen Twitter-Post mit `original_post_id` (Quote/Repost) oder eine von der verwendeten OASIS-Version
gespeicherte Reply-/Parent-Post-Verknüpfung. Kommentare werden mit der qualifizierten ID
`reddit:comment:<comment_id>` ebenfalls dem Textklassifikator vorgelegt. Getrennte `CREATE_POST`-Beiträge beider
Seiten sind kein struktureller Beleg und führen mit einem entsprechenden Audit-Hinweis zu Nein. Das Nullmodell hat
keine solche DB-Verbindung; Interaktionsergebnisse sind dort deshalb Nein.

Ein `absence`-Punkt nennt bei der Erzeugung in `counter_outcome_id` den passenden `presence`-Punkt derselben
Checkliste, sofern es ihn gibt. Verifizierte Belege dieses Gegenpunkts werden stapelübergreifend ebenfalls als Beleg
des positiven Gegenereignisses behandelt. Damit können beispielsweise „Medien reagieren nicht“ und eine belegte
offizielle Medien-Stellungnahme nicht gleichzeitig als Ja gewertet werden. Nach jeder Laufklassifikation prüft die
Aggregation dennoch alle explizit verknüpften Presence-/Absence-Paare. Etwaige doppelte Ja-Wertungen werden mit
Variante, Lauf und beiden Ergebnis-IDs unter `consistency_warnings` im Ensemble-Ergebnis ausgewiesen.

Regressionstests decken das konkrete Paar o2/o6 aus `ens_9c4647555d4b`, eine isolierte DB ohne Kommentare, eine
Basis-DB mit gruppenübergreifendem Kommentar sowie die Konsistenzwarnung ab.

Zusätzliche Regressionstests decken bekannte Cohen-Kappa-Werte und die Grenzfälle ohne Varianz bzw. ohne Paare, die
konservative Zwei-Ja-Regel, die Abgrenzung `disputed` zu Nein, den Ausschluss strittiger Läufe aus `n`, die
Zuverlässigkeitsmarkierung von Vergleichen sowie Validierung, Herkunft und Materialprüfung eigener Ergebnisfragen ab.
