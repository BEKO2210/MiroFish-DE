# Validierung V1/V2

Umsetzung der Roadmap-Stufen **V1 (ehrlicher Bericht)** und **V2 (Reproduzierbarkeit)** (Stand 13.10.2026).

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

Gezielte Unit-Tests: `tests/test_report_validation.py` (Umformulierung Bürgerentscheid vs. Material, neutrale Gegenprobe, Fixtures `tests/fixtures/report_musterstadt.md` + `musterstadt-eingabe.txt`, Mini-DB-Methodik, Manifest).

Manuell: Bericht neu erzeugen; Methodik-Zahlen müssen zur DB passen; Export-ZIP öffnen und `manifest.json` / `events.jsonl` prüfen.
