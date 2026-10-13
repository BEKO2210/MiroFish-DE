#!/usr/bin/env bash
# Vor einem Backend-Neustart: läuft gerade etwas (Durchlauf, Simulation, Vorbereitung, Bericht)? Exit 1 = beschäftigt.
B=${1:-http://127.0.0.1:5002}
python3 - "$B" <<'PY'
import json, sys, urllib.request
b = sys.argv[1]
def get(p):
    try: return json.load(urllib.request.urlopen(b + p, timeout=8)).get("data") or []
    except Exception as e: return []
busy = []
busy += [f"Durchlauf {p['pipeline_id']}" for p in get("/api/pipeline/list") if p.get("status") == "running"]
busy += [f"Simulation {s['simulation_id']} ({s.get('runner_status')})" for s in get("/api/simulation/history")
         if s.get("runner_status") in ("running", "starting", "paused") or s.get("status") == "preparing"]
tasks = get("/api/graph/tasks")
tasks = tasks.get("tasks", tasks) if isinstance(tasks, dict) else tasks
busy += [f"Aufgabe {t.get('task_type')} {t.get('task_id')}" for t in tasks if t.get("status") in ("pending", "processing")]
print("\n".join(busy) if busy else "frei")
sys.exit(1 if busy else 0)
PY
