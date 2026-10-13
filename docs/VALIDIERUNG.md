# Validierung V1–V4

Umsetzung der Roadmap-Stufen **V1 (ehrlicher Bericht)**, **V2 (Reproduzierbarkeit)**,
**V3 (Mehrfachlauf)** und **V4 (Gegenproben)** (Stand 13.10.2026; Auswertung und Nullmodell 14.10.2026).

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

## Reproduzierbarkeit

Twitter und Reddit ziehen nicht mehr aus dem globalen `random`. Vor `asyncio.gather` entsteht je Plattform ein eigener
`random.Random`-Strom (und ein NumPy-`Generator`) aus `SHA-256(seed:plattform)`. Aktive Agenten je Runde nutzen nur
diesen Strom; die Ziehungsreihenfolge hängt damit nicht an der LLM-Latenz der anderen Plattform.

`build_manifest` liest den Ordner, in dem `simulation_config.json` liegt (`sim_dir`), nicht
`uploads/simulations/<simulation_id>`. Ensemble-Läufe unter `uploads/ensembles/.../run_n/` bekommen damit echte Hashes
für Config, Profile (`twitter_profiles.csv`, `reddit_profiles.json`), Startbeiträge und Frage. Die Modellnamen stehen
getrennt als `models.twitter` und `models.reddit` (Reddit kann `LLM_BOOST_*` nutzen).

Nichtdeterminismus messen (gleicher Seed, zwei Kopien, Aktionslogs):

```bash
cd backend && python3 scripts/repro_check.py <sim_dir> --seed <n> --max-rounds 2
# nur Vergleich ohne Lauf:
python3 scripts/repro_check.py --compare-only <run_a> <run_b>
```

Ausgegeben werden `sequential_identity` (Anteil identischer Aktionen Typ/Agent/normalisierter Text in Reihenfolge)
und `text_jaccard` (Jaccard der Aktionstexte). Unit-Tests prüfen Ströme, Manifest-Hashes und das Abstandsmaß an
Beispiel-Logs. Ein gemessener GPU-Doppelwert für das Hallenbad-Szenario steht hier noch aus (Lauf bewusst nicht
automatisch gestartet); sobald vorhanden, als Zahl nachtragen und als Untergrenze in Intervallinterpretationen
verwenden. Lokale Anbieter können den LLM-`seed` ignorieren — das bleibt eine eigene Grenze.

## Prüfung

```bash
cd backend && python3 -m pytest -q tests
cd frontend && npx vite build
cd e2e && PW_PORT=4175 npx playwright test
```

Gezielte Unit-Tests: `tests/test_report_validation.py` (Umformulierung Bürgerentscheid vs. Material, neutrale
Gegenprobe, Fixtures `tests/fixtures/report_musterstadt.md` + `musterstadt-eingabe.txt`, Mini-DB-Methodik, Manifest)
und `tests/test_ensemble.py` (Wilson/Newcombe, exakter McNemar, gepaartes Wald-Intervall, Holm, Paarbildung,
Stapelwiederholung, Textspanne, `null_personas`-Prompt, Checklisten-Parsing, Akteursentfernung, Zustandsmaschine
mit gemocktem Runner).

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
Klassifikator erhält keine Berichte. Ein Ja zählt nur, wenn das Modell eine vorhandene, plattformqualifizierte
Beitrags-ID wie `twitter:17` nennt und eine wörtliche Textspanne liefert, die nach Leerraum-Normalisierung und ohne
Rücksicht auf Groß- und Kleinschreibung in genau diesem Beitrag steht. Unbekannte IDs und Spannen, die nur in einem
anderen Beitrag vorkommen, verwerfen das Ja. Dieselbe Spannenregel gilt in den Nullarmen gegen die Erzählung.
Startbeiträge werden anhand von Autor und Text aus der Auswertungsmenge entfernt. Dadurch können vorgegebene Aussagen
nicht allein durch ihre technische Einspeisung als Simulationsergebnis zählen.

`POST /api/ensemble/start` akzeptiert optional bis zu 20 eigene Ergebnisfragen als
`custom_outcomes: [{"text_de": "…", "polarity": "presence|absence", "kind": "event|interaction"}]`.
`text_de` ist Pflicht und auf 200 Zeichen begrenzt; Polarität und Art sind optional und werden andernfalls aus dem Text
abgeleitet. Die Punkte werden mit IDs `c1` bis `c6` an die automatische Checkliste angehängt. Jeder Checklistenpunkt
weist seine Herkunft als `source: "auto"` oder `source: "user"` aus. Eigene Punkte durchlaufen denselben
Materialabgleich, dieselbe Belegprüfung und dieselbe Klassifikation wie automatisch erzeugte Punkte.

`POST /api/ensemble/start` akzeptiert optional `primary_outcome_id`. Ohne Angabe wird nach dem Erzeugen der Checkliste
das erste eigene Ergebnis (`source: user`) gewählt, sonst das erste automatische. Eine unbekannte ID bricht den Lauf ab.
Nur dieses Primärergebnis ist konfirmatorisch; die übrigen Vergleiche sind explorativ. Ist die gewählte ID ein
Abwesenheitsgegenstück, das in die Presence-Zeile gefaltet wird, ist diese kanonische Zeile konfirmatorisch.

## V3c: Zuverlässigkeit des Messinstruments

Jeder gespeicherte Lauf wird zweimal unabhängig klassifiziert. Bewerter A nutzt das konfigurierte Hauptmodell;
Bewerter B nutzt `ENSEMBLE_SECOND_RATER_MODEL` (Standard `qwen3.5:9b`) am selben lokalen OpenAI-kompatiblen Server.
Ist das Zweitmodell leer konfiguriert, nicht initialisierbar oder bei allen Klassifikationsstapeln nicht erreichbar,
wird das Hauptmodell mit einem anderen Seed verwendet. `classification.json` enthält Modell, Seed, Rohantwort,
geprüfte Belege und Urteil beider Bewerter sowie das gemeinsame Endurteil.

Das Endurteil ist nur dann Ja, wenn beide Bewerter nach der Belegprüfung Ja urteilen. Ja/Nein-Dissens ist
`disputed`, nicht Nein, und wird ebenso wie `unclassified` aus `n`, Rate, Wilson-Intervall und Paartafel ausgeschlossen.
`results.<variante>.<ergebnis>.disputed` weist diese Fälle separat aus. Fehlt in einer erfolgreich geparsten
Stapelantwort die Zeile eines Ergebnisses, bleibt dieses Ergebnis `unclassified`. Ein Stapel, der nach drei Versuchen
weiterhin keine parsebare Antwort liefert, ist kein `unclassified`: ohne positiven Textbeleg bleibt der Lauf in `n`
(Anwesenheit → Nein, Abwesenheit ohne positiven Beleg → Ja).

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
  Like, Repost, Follow, Quote (Twitter) sowie Kommentar, Suche, Trend, Refresh, Votes, Follow, Mute (Reddit) entfallen.
  Die Gegenprobe misst fehlende Vernetzung und zugleich fehlende Reaktionsaktionen – diese Kopplung ist bei der
  Interpretation zu nennen. `isolated` bleibt der „nur Posten“-Arm.
- `blind_feed`: Voller Aktionskatalog wie in der Basis. Die Beobachtung fremder Beiträge wird geleert: In OASIS füllt
  `Platform.update_rec_table` die Tabelle `rec`; die passive Beobachtung läuft über `SocialEnvironment.get_posts_env`
  → `refresh` (Twitter zusätzlich Followee-Posts). OASIS hat keinen Recommender „nur eigene Beiträge“. Für
  `blind_feed` setzt MiroFish deshalb `update_rec_table` auf `DELETE FROM rec` und ersetzt `refresh` so, dass nur
  eigene Posts zurückkommen (ohne Follow-Zweig). Search/Trend bleiben als Aktionen wählbar; die Standardbeobachtung
  nicht. Damit trennt der Arm Beobachtung von Aktionsraum.
- `without:<AgentTyp>`: Alle Agenten des Typs werden aus beiden Profildateien und der Aktivitätskonfiguration entfernt.
  Ihre Startbeiträge entfallen ebenfalls; verbleibende IDs werden lückenlos neu nummeriert, weil OASIS an mehreren
  Stellen fortlaufende IDs voraussetzt.
- `null_document`: Keine OASIS-Simulation. Das Hauptmodell erhält Eingabedokument, Frage und Zeitraum und schreibt pro
  Seed eine Verlaufserzählung. Die Checkliste wird gegen diese Erzählung mit derselben Spannenregel klassifiziert.
  Der Arm zeigt, welche Ergebnisse bereits ein einzelner Erzähler ohne Agenten produziert. Pro Lauf liegt
  `manifest.json` mit Prompt-Hash, Modell, Temperatur, Seed und Tokenobergrenze im Laufordner.
- `null_model`: Alias von `null_document`. Der gespeicherte Schlüssel bleibt, damit ältere Starts weiter funktionieren.
- `null_personas`: Ebenfalls eine Erzählung ohne Schwarm, zusätzlich mit denselben Personas und Startbeiträgen. Die
  Ausgabelänge zielt auf den Median der Zeichen der Basis-Transkripte (Startbeiträge nicht mitgezählt; bei gerader
  Anzahl der gerundete Mittelwert der beiden mittleren Längen). Jede Akteursgruppe muss im Verlauf vorkommen. Steht
  `null_personas` vor `baseline`, läuft sie unmittelbar danach, weil sie die Basis-Transkripte liest. Ebenfalls mit
  `manifest.json` wie bei `null_document`.

Startbeiträge: Nach Runde 0 werden die in der Plattform-DB liegenden Öffnungsposts jedem Agenten einmal als gelesener
Stimulus in die Agenten-Erinnerung geschrieben und unter `twitter/stimulus_log.json` bzw. `reddit/stimulus_log.json`
(Einzelplattform: `stimulus_log.json`) protokolliert. Ohne diesen Nachweis gilt der Arm nicht als „gleiche Information“.

Je Lauf speichert das Ensemble unter `run_stats` Beitragszahl, Zeichenzahl und Stapelzahl; der Markdown-Abschnitt
„Mehrfachlauf“ zeigt sie als Zusatztabelle „Textmengen je Lauf“, damit Textmengen-Effekte sichtbar bleiben.

## Statistik

Je Ergebnis und Variante bleiben `Ja`, `N`, Anteil und ein zweiseitiges 95-%-Wilson-Score-Intervall ohne
Kontinuitätskorrektur die Randverteilung. Bei `N = 0` ist das technische Intervall `[0, 0]`. `N` umfasst nur Läufe mit
übereinstimmendem, klassifiziertem Doppelurteil und kann daher kleiner als `runs` sein. `disputed` und `unclassified`
zählen nicht in `N`.

Die Inferenz folgt dem gepaarten Design (gemeinsamer Seed je Laufindex). Für jedes kanonische Ergebnis und jede
Nicht-Basis-Variante speichert der Vergleich die 2×2-Tafel `table`: `both_yes` (a), `baseline_only` (b),
`variant_only` (c), `both_no` (d), `n_pairs`, `unpaired`. Gepaart wird nur, wenn beide Seiten am selben Index
klassifiziert und weder `disputed` noch `unclassified` sind.

Konfirmatorisch ist der exakte zweiseitige McNemar-Test (`mcnemar_p`, verdoppelte untere Binomialwahrscheinlichkeit
bei p = 1/2) für das Primärergebnis in jeder Nicht-Basis-Variante. `role` ist dann `confirmatory`, `holm_p` bleibt
leer. Alle übrigen Ergebnis×Variante-Vergleiche sind `exploratory`. Für diese Familie mit `n_pairs > 0` wird die
Holm-Korrektur ausgewiesen (`holm_p`, `analysis.exploratory_m`). Leere Paartafeln bleiben explorativ und gehen nicht
in die Familie ein.

Das gepaarte Differenzintervall (Variante − Basis) = (c − b) / n ist ein Wald-Intervall mit
SE = sqrt((b + c) − (c − b)² / n) / n und demselben z wie das Wilson-Intervall. Es liegt in `diff`, `ci_low` und
`ci_high` des Vergleichs, ist auf [-1, 1] begrenzt und bei `n_pairs = 0` gleich [0, 0]. Die Oberfläche liest diese
Grenzen; enthält das Intervall die 0, erscheint weiterhin „kein belastbarer Unterschied“. Der gespeicherte
konfirmatorische Test ist `mcnemar_p`. Newcombe, Methode 10, steht nur unter `newcombe` als Sensitivität unter der
Annahme unabhängiger Stichproben. `analysis` hält `confirmatory: exact_mcnemar`, `paired_interval: wald`,
`sensitivity: newcombe_method_10` und `exploratory_correction: holm`.

Logische Gegenstücke (`counter_outcome_id` eines `absence`-Punkts auf einen `presence`-Punkt) werden in der Inferenz
zu einer Zeile zusammengelegt (`collapsed_outcome_ids`, am Abwesenheitspunkt `collapsed_into`). Die Randverteilungen
beider IDs bleiben in `results`. Die Warnung bei doppeltem Ja beider Gegenstücke bleibt.

Der deterministische Markdown-Abschnitt **„Mehrfachlauf“** nennt das Primärergebnis, überspringt gefaltete
Abwesenheitszeilen und zeigt Paartafel, gepaartes Wald-Intervall, McNemar, Holm und Newcombe als Sensitivität, dazu
Wilson-Intervalle der Randverteilung, strittige und unklassifizierte Läufe, die Zuverlässigkeit je Ergebnis, Hinweise
auf bereits im Material vorhandene Punkte und die Nullarme. Nicht messbare Ergebnisse werden nicht interpretiert.
Dafür wird kein weiteres Modell aufgerufen.

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
- Gleiche Profile und dasselbe Hauptmodell erzeugen abhängige systematische Fehler. Der konfirmatorische Test und das
  Wald-Intervall nutzen die Paarung über den gemeinsamen Seed. Newcombe-Methode 10 setzt unabhängige Stichproben voraus
  und ist nur die Sensitivität.
- Modellanbieter können Seeds ignorieren oder trotz Seed nicht vollständig deterministisch rechnen.
- Die automatische Checkliste und Klassifikation können relevante Ereignisse auslassen oder falsch einordnen. Die
  geprüften Beitrags-IDs machen positive Urteile auditierbar, ersetzen aber keine fachliche Blindbewertung.
- `isolated` entfernt zugleich Vernetzung und soziale Reaktionsmöglichkeiten. Der Unterschied ist keine reine Schätzung
  eines einzelnen Empfehlungsalgorithmus-Effekts. Für die reine Beobachtungsablation ist `blind_feed` zuständig;
  Search/Trend können dort weiterhin fremde Inhalte liefern, wenn Agenten sie aktiv wählen.
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

Ein Stapel wird bis zu zweimal wiederholt (drei Versuche). Liefert er danach keine parsebare Antwort, fällt der Lauf
nicht aus `N`: ohne positiven Textbeleg bleibt er in Anteil und Wilson-Intervall (Anwesenheit → Nein, Abwesenheit ohne
positiven Beleg → Ja). Fehlt in einer erfolgreich geparsten Antwort die Zeile eines Ergebnisses, bleibt dieses Ergebnis
`unclassified`, zählt nicht in `N` und erscheint unter `results.<variant>.<outcome>.unclassified` sowie in der
Berichtstabelle. `classification.json` hält je Stapel `attempts`, die Rohantwort und den Fehler fest.

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

Das Ergebnis einer Interaktion ist in allen Armen die Textspanne: Ja nur, wenn sie im genannten Beitrag beziehungsweise
in der Erzählung steht. Eine OASIS-SQLite-Kante zwischen den zugeordneten Seiten — Reddit-Kommentar mit `post_id`,
Twitter-Post mit `original_post_id` (Quote/Repost) oder eine gespeicherte Reply-/Parent-Verknüpfung — liegt als eigene
Mechanismusvariable `mechanism_edges` am Urteil und wird in `mechanism_edge_runs` gezählt. Sie dreht das Ja nicht um
und ersetzt den Textbeleg nicht. Getrennte `CREATE_POST`-Beiträge beider Seiten erzeugen keine Kante. Kommentare
werden mit der qualifizierten ID `reddit:comment:<comment_id>` dem Textklassifikator vorgelegt. In den Nullarmen ist
`mechanism_edges` leer; die Interaktion wird aus dem Erzähltext kodiert.

Ein `absence`-Punkt nennt bei der Erzeugung in `counter_outcome_id` den passenden `presence`-Punkt derselben
Checkliste, sofern es ihn gibt. Verifizierte Belege dieses Gegenpunkts werden stapelübergreifend ebenfalls als Beleg
des positiven Gegenereignisses behandelt. Damit können beispielsweise „Medien reagieren nicht“ und eine belegte
offizielle Medien-Stellungnahme nicht gleichzeitig als Ja gewertet werden. Nach jeder Laufklassifikation prüft die
Aggregation dennoch alle explizit verknüpften Presence-/Absence-Paare. Etwaige doppelte Ja-Wertungen werden mit
Variante, Lauf und beiden Ergebnis-IDs unter `consistency_warnings` im Ensemble-Ergebnis ausgewiesen.

Regressionstests decken das konkrete Paar o2/o6 aus `ens_9c4647555d4b`, die Trennung von Texturteil und
`mechanism_edges` (Kante ohne Spanne bleibt Nein; Nullarm kodiert Interaktion aus dem Text), die Konsistenzwarnung,
bekannte McNemar- und Holm-Werte, die Paarbildung über den Laufindex, die Stapelwiederholung mit Verbleib in `N`, die
Textspannenregel und den `null_personas`-Prompt ab.

Zusätzliche Regressionstests decken bekannte Cohen-Kappa-Werte und die Grenzfälle ohne Varianz bzw. ohne Paare, die
konservative Zwei-Ja-Regel, die Abgrenzung `disputed` zu Nein, den Ausschluss strittiger Läufe aus `n`, die
Zuverlässigkeitsmarkierung von Vergleichen sowie Validierung, Herkunft und Materialprüfung eigener Ergebnisfragen ab.

## V5 Realitätsabgleich – Ablauf und Kennzahlen

Das vorregistrierte Studiendesign steht in `docs/validation/PROTOKOLL-V5.md`.
`backend/scripts/validate_case.py` führt einen dokumentierten Realfall blind gegen die bestehende HTTP-API aus:

```bash
cd backend
python3 scripts/validate_case.py ../docs/validation/faelle/<fall> --runs 10 --hours 336 \
  --ort Beispielstadt --jahr 2025 --thema Bäderschließung
```

Der Standardwert von `--hours` bleibt aus Kompatibilitäts- und Laufzeitgründen 168. Für die in der neutralen Frage
genannten ersten zwei Wochen sind 336 Stunden anzugeben. `--base` zeigt standardmäßig auf
`http://127.0.0.1:5002`.

Die Standardarme sind `baseline` (S), `null_document` (D) und `null_personas` (P). Mit
`--arms baseline,null_document,null_personas,isolated` kommt der explorative Isolationsarm hinzu. Ein älteres Backend,
das D oder P noch nicht unterstützt, führt zu einer verständlichen Aktualisierungsfehlermeldung; die Namen werden
nicht still auf das frühere, methodisch nicht vergleichbare `null_model` zurückgebogen.

Das Skript lädt als einziges Dokument `ausgangslage.md` hoch und verwendet immer die neutrale Frage „Wie reagieren
Bürgerinnen, Vereine, Medien und Politik in den ersten zwei Wochen nach der Bekanntgabe?“. Es erzeugt Ontologie und
Graph, legt die Simulation an und wartet bis zum Ende der Vorbereitung. Noch vor diesen Modellaufrufen fragt es das
konfigurierte Hauptmodell bei Temperatur 0 und ohne Werkzeuge anhand von Ort, Jahr und Thema nach Fallkenntnis. Der
Ausgang wird nicht genannt. Anfrageparameter und Antwort stehen im Resume-State und im Fallergebnis. Bekannte Fälle
tragen `contaminated: true` und werden in der Gesamtauswertung separat geführt.

Die Texte `text_de` aus `ergebnisse.json` gehen als eigene Ergebnisfragen ein. Optional markiert genau ein Eintrag
`"primaer": true`; dessen stabile ID sendet das Werkzeug als `primary_outcome_id` im Start-POST. Mehrere Markierungen
werden vor jedem API-Aufruf abgewiesen. `eingetreten`, `verlauf.md` und Quellen werden niemals gesendet. Erst nach dem
Ensemble verbindet das Skript die Häufigkeiten mit den dokumentierten Wahrheitswerten. Das Primärergebnis wird
konfirmatorisch, alle übrigen Fragen werden getrennt als explorativ ausgewiesen.

Die API akzeptiert für Ensembles nun 1 bis 336 Stunden und bis zu 20 eigene Ergebnisfragen. An der Zeitachse war keine
weitere technische Grenze nötig: `total_simulation_hours` wird in die kopierte Laufkonfiguration geschrieben, die
Rundenzahl ergibt sich aus `hours * 60 / minutes_per_round`, und Tageszeit sowie Tageswechsel werden fortlaufend
berechnet. Bei 30 Minuten pro Runde sind zwei Wochen 672 Runden je OASIS-Lauf. Zehn Basisläufe können daher je nach
Agentenzahl und Modell mehrere Tage dauern. Die vorhandene ETA skaliert mit der tatsächlichen Rundenzahl; das
D und P zählen je Seed jeweils als eine Modellrunde.

Nach jedem dauerhaften Schritt speichert das Skript Projekt-, Graph-Aufgaben-, Graph-, Simulations-, Vorbereitungs-
und Ensemble-ID in `docs/validation/ergebnisse/<fall>.state.json`. Ein identischer Aufruf setzt am letzten bekannten
Schritt wieder auf. Abweichende Basis-URL, Laufzahl, Stundenzahl oder Armauswahl werden bei vorhandenem State
abgewiesen, damit keine Ergebnisse verschiedener Konfigurationen vermischt werden.

Die fallbezogenen Dateien `docs/validation/ergebnisse/<fall>.md` und `.json` enthalten je eigener Frage den echten
Wert, `yes/n` und Rate je Arm sowie Übereinstimmung, Cohen's Kappa und Messbarkeitslabel der
Doppelbewertung. Strittige beziehungsweise unklassifizierte Einzelläufe stehen separat und zählen wie in V3 nicht zu
`n`. Fragen mit `n = 0`, Kappa unter 0,6 oder `in_material: true` werden ausgewiesen, aber nicht gescored.

Für die verbleibenden, gepaarten Fragen werden berechnet:

- **Brier-Score:** Mittelwert von `(p - y)²`, mit Vorhersagerate `p` und Beobachtung `y` in `{0, 1}`.
- **Trefferquote:** Anteil richtiger Ja/Nein-Entscheidungen; eine Rate `p >= 0,5` gilt als Ja.
- **Log-Score:** mittlerer negativer Log-Likelihood-Verlust; Wahrscheinlichkeiten werden nur für den Logarithmus auf
  `[10⁻¹⁵, 1 - 10⁻¹⁵]` begrenzt. Bei Brier- und Log-Score ist kleiner besser.

`GESAMT.md` und `GESAMT.json` werden aus allen Fall-JSONs der Schema-Version 2 neu aufgebaut. Pro Fall geht ausschließlich
die Seed-Häufigkeit des messbaren Primärergebnisses ein. Ausgegeben werden Brier-Score je Arm, `1 − BS_S/BS_D` und
`1 − BS_P/BS_D`. Das perzentile 95-%-Intervall resampelt 10.000-mal ganze Fälle mit Zurücklegen (fester Seed 20261014),
niemals Fragen oder Seeds. Kontaminierte Fälle bilden eine eigene Gruppe.

Die Kalibrierungssteigung wird ohne Statistikbibliothek per logistischer Regression von Ereignissen auf den Logit der
Arm-Häufigkeit geschätzt. Bei weniger als acht auswertbaren Fällen erscheint fest „Pilot, keine
Kalibrierungsaussage“. Das vorab registrierte Kriterium wird als „bestanden“, „nicht bestanden“ oder „nicht prüfbar“
ausgegeben: Das Skill-Intervall S gegen D muss vollständig über 0 liegen, die Steigung von S in [0,5; 1,5] und das
Kappa des Primärergebnisses mindestens 0,6. Die konfirmatorische Stichprobe umfasst mindestens 25 Fälle.
