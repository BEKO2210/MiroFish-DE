# MiroFish API (für Skripte, Agenten und eigene Oberflächen)

Basis-URL: `http://127.0.0.1:5001` (lokal; Port aus `FLASK_PORT`, Standard 5001) bzw. deine Tailscale-Adresse. Alle Antworten sind JSON mit `success` und `data`
oder `error`. Ist in der `.env` ein `API_TOKEN` gesetzt, braucht jeder Aufruf den Header `Authorization: Bearer <token>`
(Skripte, Agenten); sonst antwortet die API mit HTTP 401 (`API-Schlüssel fehlt oder ist falsch`). Im Browser einmal `https://<host>/?token=<token>` öffnen: das Token wird als geschütztes Cookie
gespeichert und aus der Adresse entfernt. Ohne `API_TOKEN` ist die API offen – dann nur in einem geschützten Netz betreiben.

## Der eine Aufruf, der alles macht

```bash
curl -X POST http://127.0.0.1:5001/api/pipeline/start \
  -F "files=@bericht.pdf" -F "files=@notizen.md" \
  -F "simulation_requirement=Wie reagiert die Öffentlichkeit in der ersten Woche auf ...?"
# -> {"success": true, "data": {"pipeline_id": "run_…"}}

curl http://127.0.0.1:5001/api/pipeline/run_…      # Fortschritt: Stufe, Detail, Prozent, Fehler
curl http://127.0.0.1:5001/api/pipeline/list       # alle Durchläufe
```

Stufen: `ontology` → `graph` → `create` → `prepare` → `simulate` → `report`. Am Ende enthält die Antwort
`simulation_id` und `report_id`.

## Ergebnisse abholen

```bash
curl http://127.0.0.1:5001/api/report/<report_id>                 # Bericht als JSON (markdown_content)
curl -OJ http://127.0.0.1:5001/api/report/<report_id>/download    # Bericht als Datei
curl -OJ http://127.0.0.1:5001/api/simulation/<simulation_id>/export   # kompletter Lauf als ZIP
curl "http://127.0.0.1:5001/api/simulation/<simulation_id>/posts?platform=twitter&limit=50"
curl http://127.0.0.1:5001/api/simulation/<simulation_id>/run-status
```

## Einzelne Stufen (wenn du selbst steuern willst)

| Schritt | Aufruf |
|---|---|
| Dokumente + Frage → Ontologie | `POST /api/graph/ontology/generate` (multipart: `files`, `simulation_requirement`) |
| Wissensgraph bauen | `POST /api/graph/build` `{"project_id": "...", "force": true}` → `GET /api/graph/task/<task_id>` |
| Simulation anlegen | `POST /api/simulation/create` `{"project_id": "..."}` |
| Agenten vorbereiten | `POST /api/simulation/prepare` `{"simulation_id": "..."}` → `POST /api/simulation/prepare/status` |
| Simulation starten | `POST /api/simulation/start` `{"simulation_id": "..."}` → `GET /api/simulation/<id>/run-status` |
| Bericht | `POST /api/report/generate` `{"simulation_id": "..."}` → `POST /api/report/generate/status` |
| Agenten befragen | `POST /api/simulation/interview` `{"simulation_id": "...", "agent_id": 3, "question": "..."}` |
| Lauf löschen | `DELETE /api/simulation/<simulation_id>` (entfernt auch die Berichte) |
| Systemstatus / Modelle | `GET /api/system/status`, `GET /api/system/models` (siehe unten), `POST /api/graph/system/test-llm` |

## Mehrfachläufe (Ensemble)

Ein Ensemble startet viele Läufe derselben vorbereiteten Simulation mit verschiedenen Seeds, klassifiziert jedes
Ergebnis je Lauf und vergleicht die Varianten mit der Basis. Voraussetzung: die Simulation (`sim_…`) ist vorbereitet
(`simulation_config.json`, Profile, `state.json` vorhanden), sonst 404.

```bash
curl -X POST http://127.0.0.1:5001/api/ensemble/start -H "Content-Type: application/json" -d '{
  "simulation_id": "sim_…",
  "runs": 10,
  "hours": 24,
  "start_hour": 7,
  "minutes_per_round": 60,
  "variants": ["baseline", "isolated", "blind_feed", "null_document", "null_personas"],
  "custom_outcomes": [
    {"text_de": "Es wird zu einer Unterschriftensammlung aufgerufen", "polarity": "presence", "kind": "event"}
  ],
  "primary_outcome_id": "c1"
}'
# -> {"success": true, "data": {"ensemble_id": "ens_…", "estimate_seconds": 1234}}
```

| Parameter | Standard | Regel |
|---|---|---|
| `simulation_id` | – | Pflicht, beginnt mit `sim_` |
| `runs` | 10 | ganze Zahl 1–100 |
| `hours` | 24 | ganze Zahl 1–336 |
| `start_hour` | 7 | ganze Zahl 0–23 (Startstunde der simulierten Uhr, `time_config.start_hour`) |
| `minutes_per_round` | 60 | nur 60, 120 oder 240. `hours × 60` muss durch `minutes_per_round` teilbar sein (z. B. 24 h mit 240 ✓, 10 h mit 240 ✗), sonst 400 |
| `variants` | `["baseline"]` | nicht leer, `baseline` ist Pflicht (siehe unten) |
| `custom_outcomes` | – | optionale Liste, höchstens 20 Einträge (siehe unten) |
| `primary_outcome_id` | – | ID des einen konfirmatorischen Ergebnisses |

Alle Zahlen müssen echte ganze Zahlen sein (keine Strings, keine Booleans). Fehler: 400 bei ungültigen Werten,
404 wenn die Simulation nicht vorbereitet ist, 500 sonst.

**Varianten (`variants`)**

| Schlüssel | Bedeutung |
|---|---|
| `baseline` | Basislauf (Pflicht; Bezugspunkt aller Vergleiche) |
| `isolated` | Ohne Vernetzung |
| `blind_feed` | Blinder Feed |
| `null_document` | Nullmodell Dokument: ein einzelnes Modell erzählt die Geschichte aus dem Material (`null_model` ist ein Alias) |
| `null_personas` | Nullmodell Personas; liest die Basis-Transkripte und läuft daher immer nach `baseline` |
| `without:<Akteurstyp>` | Ohne eine Akteursgruppe, z. B. `without:Student`; der Typ muss in der Simulation vorkommen und darf nicht alle Agenten entfernen |

Doppelte Einträge werden entfernt; ein unbekannter Schlüssel ergibt 400.

**Eigene Ergebnisfragen (`custom_outcomes`)**: Liste von Objekten. `text_de` ist Pflicht (1–200 Zeichen). Optional:
`polarity` = `presence` (etwas tritt ein) oder `absence` (etwas bleibt aus), `kind` = `event` (Ereignis) oder
`interaction` (Wechselwirkung zwischen Gruppen). Fehlt ein Feld, wird es aus dem Text abgeleitet. Die IDs vergibt der
Server in Reihenfolge: `c1`, `c2`, … Die automatisch aus der Frage erzeugte Checkliste hat eigene IDs.

**Primärergebnis (`primary_outcome_id`)**: genau dieses Ergebnis gilt als konfirmatorisch, alle anderen als
explorativ. Ohne Angabe wird das erste eigene Ergebnis (`c1`), sonst das erste der automatischen Checkliste
verwendet. Eine ID der Form `cN`, die nicht in `custom_outcomes` steht, ergibt 400; eine ID, die später nicht in der
Checkliste steht, lässt den Lauf fehlschlagen.

### Weitere Aufrufe

```bash
curl http://127.0.0.1:5001/api/ensemble/list                       # alle Ensembles (ohne results), neueste zuerst
curl "http://127.0.0.1:5001/api/ensemble/list?simulation_id=sim_…"  # nur zu einer Simulation
curl http://127.0.0.1:5001/api/ensemble/ens_…                       # Zustand und Ergebnisse
curl -X POST http://127.0.0.1:5001/api/ensemble/ens_…/cancel        # abbrechen (gestoppt wird auch der laufende Lauf)
curl -X POST http://127.0.0.1:5001/api/ensemble/ens_…/reclassify    # neu auswerten, ohne zu simulieren
curl -X DELETE http://127.0.0.1:5001/api/ensemble/ens_…             # löschen
```

**Reklassifizieren**: wertet die gespeicherten Datenbanken bzw. Erzählungen erneut aus; es werden keine Simulationen
gestartet. Antwort `{"ensemble_id": "ens_…", "status": "queued"}`; der Fortschritt steht wie sonst in `GET`. Die
bisherigen Werte bleiben in `results_v1` und `comparisons_v1` erhalten. 404: unbekannt oder gespeicherter Lauf fehlt;
409: Ensemble läuft noch (`queued`/`running`) oder hat keine abgeschlossene Klassifikation.

**Löschen**: entfernt das Ensemble mit allen Läufen von der Platte. 404 wenn unbekannt, 409 solange es `queued` oder
`running` ist (erst `cancel`). `cancel` bei bereits beendetem Ensemble ist wirkungslos (Antwort trotzdem `success`).

### Antwort von `GET /api/ensemble/<id>`

`status` ist `queued`, `running`, `completed`, `failed` oder `cancelled`. Wichtige Felder:

| Feld | Inhalt |
|---|---|
| `ensemble_id`, `simulation_id`, `question`, `created_at`, `finished_at`, `error`, `eta_seconds`, `current` | Kopfdaten und Fortschritt |
| `runs`, `hours`, `start_hour`, `minutes_per_round` | die beim Start gewählten Parameter |
| `variants` | je Variante `key`, `label_de`, `label_en`, `status`, `done`, `total` |
| `checklist` | Ergebnisse: `id`, `text_de`, `definition`, `polarity`, `kind`, `source` (`auto`/`user`); bei Gegenstücken `counter_outcome_id` bzw. `collapsed_into` |
| `custom_outcomes`, `primary_outcome_id` | wie gesendet bzw. aufgelöst |
| `results` | `results[variante][ergebnis_id]` mit `yes`, `n`, `unclassified`, `disputed`, `rate`, `ci_low`, `ci_high` (95-%-Wilson-Intervall), `evidence` (höchstens 5 Belege). `n` zählt nur Läufe, die weder unklassifiziert noch strittig sind |
| `comparisons` | je Variante ≠ `baseline` und je Ergebnis eine Zeile (siehe unten) |
| `reliability` | je Ergebnis die Übereinstimmung der zwei Bewerter (siehe unten) |
| `run_stats` | `run_stats[variante]` = Liste je Lauf (siehe unten) |
| `consistency_warnings` | Presence- und Absence-Ergebnis zum selben Akteur im selben Lauf beide mit Ja |
| `analysis` | Verfahren: `primary_outcome_id`, `confirmatory` = `exact_mcnemar`, `paired_interval` = `wald`, `sensitivity` = `newcombe_method_10`, `exploratory_correction` = `holm`, `exploratory_m` (Zahl der explorativen Tests) |

Nicht enthalten sind Seeds und interne Steuerfelder. `GET /list` liefert dieselben Felder ohne `results`.

**`comparisons`** (Variante gegen Basis, gepaart über denselben Laufindex):

| Feld | Inhalt |
|---|---|
| `variant`, `outcome_id`, `collapsed_outcome_ids` | Vergleich; Absence-Gegenstücke sind in die Presence-Zeile gefaltet |
| `role` | `confirmatory` (nur das Primärergebnis) oder `exploratory` |
| `table` | 2×2-Tafel: `both_yes`, `baseline_only`, `variant_only`, `both_no`, `n_pairs`, `unpaired` (unklassifizierte/strittige Seiten bleiben ungepaart) |
| `diff`, `ci_low`, `ci_high` | gepaarte Differenz (Variante − Basis) mit Wald-Intervall |
| `mcnemar_p` | exakter zweiseitiger McNemar-Test über die diskordanten Paare |
| `holm_p` | Holm-adjustierter p-Wert, nur bei explorativen Vergleichen mit `n_pairs` > 0; sonst `null` |
| `newcombe` | `ci_low`, `ci_high`: Newcombe-Intervall (Methode 10) der Differenz aus den ungepaarten Anteilen, als Sensitivitätsprüfung |
| `unreliable` | `true`, wenn das Ergebnis in `reliability` „nicht messbar“ ist |

**`reliability[ergebnis_id]`**: `agreement` (Anteil gleicher Urteile), `kappa` (Cohens Kappa), `n_pairs` und `label`:
`messbar` (κ ≥ 0,6), `unsicher` (κ ≥ 0,4), sonst `nicht messbar`. Das Endurteil ist konservativ: Ja nur, wenn beide
Bewerter Ja sagen; Dissens zählt als `disputed`. Hinweis zu `kappa`: in diesem Stand liefert die API bei konstanten,
identischen Reihen `1.0` und ohne Paare `0.0`. Der Zweig `v5gate` (noch nicht gemerged) gibt stattdessen `null`
zurück, wenn Kappa mangels Varianz nicht definiert ist; Skripte sollten `null` daher tolerieren.

**`run_stats[variante]`**: je Lauf `run`, `post_count`, `character_count` (bei Nullmodellen Länge der Erzählung,
`post_count` = 0), `batch_count` (Klassifikationsstapel) sowie die Fremdnutzung im blinden Feed:
`search_action_count` (Suchaktionen), `trend_action_count` (Trendaktionen), `foreign_interaction_count`
(Interaktionen mit Beiträgen anderer: like, repost, quote).

## Systemstatus und Modelle

```bash
curl http://127.0.0.1:5001/api/system/status
curl http://127.0.0.1:5001/api/system/models
curl "http://127.0.0.1:5001/api/system/models?provider=ollama&base_url=http://127.0.0.1:11434/v1"
```

(Die älteren Pfade `/api/graph/system/status` und `/api/graph/system/models` bleiben gültig.)

`status` liefert `llm_provider`, `llm_model`, `agent_model`, `llm_base_url`, `is_local_llm`, `reachable`,
`model_installed`, `loaded_models` (aktuell geladene Modelle), `memory_provider` und `config` (Einstellungen; Schlüssel
maskiert). `models` liefert `{"reachable": bool, "models": [{"name", "size_gb", "params", "quant", "loaded"}]}`; bei
Ollama kommen die Werte aus `/api/tags` und `/api/ps` (Einbettungsmodelle ausgeblendet), bei anderen OpenAI-kompatiblen
Servern nur die Namen. Ohne Parameter wird der gespeicherte Server abgefragt, mit `provider` und `base_url` ein noch
nicht gespeicherter. Der gespeicherte API-Schlüssel geht nie an eine frei angegebene Adresse.

## Python-Beispiel

```python
import requests, time
base = "http://127.0.0.1:5001"
r = requests.post(f"{base}/api/pipeline/start",
                  files=[("files", open("bericht.pdf", "rb"))],
                  data={"simulation_requirement": "Wie reagiert ...?"}).json()
pid = r["data"]["pipeline_id"]
while True:
    s = requests.get(f"{base}/api/pipeline/{pid}").json()["data"]
    print(s["status"], s["current_step"], s["steps"][s["current_step"]]["detail"] if s["current_step"] else "")
    if s["status"] in ("completed", "failed"):
        break
    time.sleep(30)
if s["status"] == "completed":
    print(requests.get(f"{base}/api/report/{s['report_id']}").json()["data"]["markdown_content"])
```
