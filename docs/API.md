# MiroFish API (für Skripte, Agenten und eigene Oberflächen)

Basis-URL: `http://<host>:5002` (lokal) bzw. deine Tailscale-Adresse. Alle Antworten sind JSON mit `success` und `data`
oder `error`. Ist in der `.env` ein `API_TOKEN` gesetzt, braucht jeder Aufruf den Header `Authorization: Bearer <token>`
(Skripte, Agenten). Im Browser einmal `https://<host>/?token=<token>` öffnen: das Token wird als geschütztes Cookie
gespeichert und aus der Adresse entfernt. Ohne `API_TOKEN` ist die API offen – dann nur in einem geschützten Netz betreiben.

## Der eine Aufruf, der alles macht

```bash
curl -X POST http://localhost:5002/api/pipeline/start \
  -F "files=@bericht.pdf" -F "files=@notizen.md" \
  -F "simulation_requirement=Wie reagiert die Öffentlichkeit in der ersten Woche auf ...?"
# -> {"success": true, "data": {"pipeline_id": "run_…"}}

curl http://localhost:5002/api/pipeline/run_…      # Fortschritt: Stufe, Detail, Prozent, Fehler
curl http://localhost:5002/api/pipeline/list       # alle Durchläufe
```

Stufen: `ontology` → `graph` → `create` → `prepare` → `simulate` → `report`. Am Ende enthält die Antwort
`simulation_id` und `report_id`.

## Ergebnisse abholen

```bash
curl http://localhost:5002/api/report/<report_id>                 # Bericht als JSON (markdown_content)
curl -OJ http://localhost:5002/api/report/<report_id>/download    # Bericht als Datei
curl -OJ http://localhost:5002/api/simulation/<simulation_id>/export   # kompletter Lauf als ZIP
curl "http://localhost:5002/api/simulation/<simulation_id>/posts?platform=twitter&limit=50"
curl http://localhost:5002/api/simulation/<simulation_id>/run-status
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
| Systemstatus / Modell testen | `GET /api/graph/system/status`, `POST /api/graph/system/test-llm` |

## Python-Beispiel

```python
import requests, time
base = "http://localhost:5002"
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
