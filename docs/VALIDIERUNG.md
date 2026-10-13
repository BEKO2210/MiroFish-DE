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

Vor dem ersten Lauf erzeugt das Hauptmodell bei Temperatur 0 und festem Seed einmalig fünf bis acht konkrete
Ja/Nein-Ergebnisse aus Frage und Eingabematerial. Jeder Punkt muss beobachtbar formuliert sein. Derselbe
Inhaltswortabgleich wie in V1 markiert, ob ein Ergebnis bereits im Material oder in einem Startbeitrag enthalten ist;
die Fundstelle bleibt sichtbar. Eine solche Markierung verhindert keine Auswertung, warnt aber vor einer scheinbaren
Prognose, die nur die Vorgabe wiederholt.

Nach jedem Lauf werden die Beiträge unmittelbar aus `twitter_simulation.db` und `reddit_simulation.db` gelesen. Der
Klassifikator erhält keine Berichte. Ein Ja zählt nur, wenn das Modell mindestens eine vorhandene, plattformqualifizierte
Beitrags-ID wie `twitter:17` nennt. Unbekannte IDs verwerfen das Ja. Startbeiträge werden anhand von Autor und Text aus
der Auswertungsmenge entfernt. Dadurch können vorgegebene Aussagen nicht allein durch ihre technische Einspeisung als
Simulationsergebnis zählen.

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
Kontinuitätskorrektur ausgegeben. Bei `N = 0` ist das technische Intervall `[0, 0]`; ein abgeschlossenes Ensemble hat
regulär `N = runs`. Variantenunterschiede sind `Anteil(Variante) − Anteil(baseline)`. Das 95-%-Intervall der Differenz
wird nach Newcombe, Methode 10, aus den vier Wilson-Grenzen zusammengesetzt und auf `[-1, 1]` begrenzt. Die reine
Python-Implementierung wird gegen bekannte Zahlenwerte getestet.

Der deterministische Markdown-Abschnitt **„Mehrfachlauf“** enthält die Ergebnistabelle, Wilson-Intervalle, Hinweise auf
bereits im Material vorhandene Punkte, den Nullmodell-Vergleich und feste Grenzen. Dafür wird kein weiteres Modell
aufgerufen.

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
