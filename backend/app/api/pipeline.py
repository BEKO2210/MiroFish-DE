"""Automatischer Durchlauf: Dokumente + Frage rein, Bericht raus.

Treibt die bestehenden HTTP-Schnittstellen dieses Backends der Reihe nach an (Ontologie -> Graph -> Simulation
anlegen -> vorbereiten -> starten -> Bericht) und hält den Zustand in uploads/pipelines/<id>.json. Dadurch bleibt
jede Stufe unverändert und einzeln nutzbar; der Durchlauf ist nur ein geduldiger Klient davon.
"""
import json
import os
import re
from contextlib import ExitStack
import threading
import time
import traceback
import uuid
from datetime import datetime

import requests
from flask import Blueprint, jsonify, request

from ..config import Config
from ..utils.logger import get_logger

pipeline_bp = Blueprint('pipeline', __name__)
logger = get_logger('mirofish.pipeline')


def mark_stale_runs():
    """Beim Start: 'running' heißt, der Thread ist mit dem Prozess gestorben.

    Solche Durchläufe werden als abgebrochen gespeichert. Anschließend werden alle
    Durchläufe mit Status 'failed' (inkl. der gerade markierten) samt Daten entfernt.
    Laufende fasst das Aufräumen nie an. Danach verwaiste Projekte und Graph-Ordner.
    """
    from ..services.cleanup import delete_failed_pipelines, sweep_orphans
    try:
        names = list(os.listdir(_dir()))
    except OSError as exc:
        logger.error(f"Durchläufe konnten nicht gelesen werden: {exc}")
        names = []
    for name in names:
        if not name.endswith('.json'):
            continue
        pid = name[:-5]
        st = _load(pid)
        if not st or st.get("status") != "running":
            continue
        st["status"] = "failed"
        st["error"] = "Backend wurde neu gestartet, Durchlauf abgebrochen"
        _save(st)
        logger.warning(f"Durchlauf {st.get('pipeline_id', pid)} als abgebrochen markiert (Neustart)")
    try:
        removed = delete_failed_pipelines()
        if removed:
            logger.info(f"Fehlgeschlagene/abgebrochene Durchläufe aufgeräumt: {removed}")
    except Exception as exc:
        logger.error(f"Aufräumen fehlgeschlagener Durchläufe fehlgeschlagen: {exc}")
    try:
        removed = sweep_orphans()
        if removed:
            logger.info(f"Verwaiste Daten entfernt: {removed}")
    except Exception as exc:
        logger.error(f"Aufräumen verwaister Daten fehlgeschlagen: {exc}")

STEPS = ["ontology", "graph", "create", "prepare", "simulate", "report"]
STEP_LABELS = {
    "ontology": "Dokumente lesen und Ontologie ableiten",
    "graph": "Wissensgraph aufbauen",
    "create": "Simulation anlegen",
    "prepare": "Agenten und Umgebung vorbereiten",
    "simulate": "Simulation läuft",
    "report": "Bericht schreiben",
}


def _dir():
    d = os.path.join(Config.UPLOAD_FOLDER, 'pipelines')
    os.makedirs(d, exist_ok=True)
    return d


def _path(pid):
    return os.path.join(_dir(), f"{pid}.json")


def _load(pid):
    p = _path(pid)
    if not os.path.exists(p):
        return None
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save(state):
    state["updated_at"] = datetime.now().isoformat()
    tmp = _path(state["pipeline_id"]) + ".tmp"
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, _path(state["pipeline_id"]))


def _base():
    port = int(os.environ.get('FLASK_PORT', 5002))
    return f"http://127.0.0.1:{port}"


def _ok(resp):
    try:
        data = resp.json()
    except ValueError:
        raise RuntimeError(f"Antwort ist kein JSON (HTTP {resp.status_code}): {resp.text[:200]}")
    if resp.status_code >= 400 or not data.get("success", True):
        raise RuntimeError(data.get("error") or f"HTTP {resp.status_code}")
    return data.get("data", data)


def _set(state, step, status, detail="", **extra):
    detail = re.sub(r"^\[\w+\]\s*", "", str(detail or ""))  # technische Präfixe wie "[generating]" weg
    state["steps"][step].update({"status": status, "detail": detail, **extra})
    state["current_step"] = step
    _save(state)


def _run(pid, files, requirement, project_name):
    """Läuft in einem Thread. Jede Stufe wartet geduldig; Fehler beenden den Durchlauf mit Angabe der Stufe."""
    state = _load(pid) or {}
    base = _base()
    s = requests.Session()
    try:
        # 1 Ontologie (Upload + Frage)
        _set(state, "ontology", "running")
        with ExitStack() as stack:
            payload = [("files", (name, stack.enter_context(open(path, "rb")))) for name, path in files]
            data = _ok(s.post(f"{base}/api/graph/ontology/generate", files=payload,
                              data={"simulation_requirement": requirement, "project_name": project_name}, timeout=3600))
        project_id = data["project_id"]
        state["project_id"] = project_id
        onto = data.get("ontology") or {}
        _set(state, "ontology", "done", f"{len(onto.get('entity_types', []))} Arten von Beteiligten, "
                                        f"{len(onto.get('edge_types', []))} Arten von Beziehungen")

        # 2 Graph
        _set(state, "graph", "running")
        task = _ok(s.post(f"{base}/api/graph/build", json={"project_id": project_id, "force": True}, timeout=60))["task_id"]
        while True:
            t = _ok(s.get(f"{base}/api/graph/task/{task}", timeout=30))
            _set(state, "graph", "running", t.get("message", ""), progress=t.get("progress", 0))
            if t.get("status") == "completed":
                r = t.get("result") or {}
                state["graph_id"] = r.get("graph_id")
                _set(state, "graph", "done", f"{r.get('node_count', 0)} Beteiligte und Themen, {r.get('edge_count', 0)} Verbindungen gefunden")
                break
            if t.get("status") == "failed":
                raise RuntimeError(t.get("error") or "Graph-Aufbau fehlgeschlagen")
            time.sleep(5)

        # 3 Simulation anlegen
        _set(state, "create", "running")
        sim = _ok(s.post(f"{base}/api/simulation/create", json={"project_id": project_id}, timeout=60))
        sim_id = sim["simulation_id"]
        state["simulation_id"] = sim_id
        _set(state, "create", "done", "Simulation angelegt")

        # 4 Vorbereiten (Profile + Konfiguration). Der Fortschritt hängt an der task_id dieser einen Aufgabe; ohne sie
        # meldet der Status-Endpunkt "nicht gestartet", und ein erneutes /prepare würde eine weitere, parallel
        # laufende Vorbereitung starten (so entstanden früher Hunderte gleichzeitiger Aufgaben).
        _set(state, "prepare", "running")
        prep = _ok(s.post(f"{base}/api/simulation/prepare", json={"simulation_id": sim_id, "parallel_profile_count": 1}, timeout=60))
        task_id = prep.get("task_id")
        while not prep.get("already_prepared"):
            st = _ok(s.post(f"{base}/api/simulation/prepare/status",
                            json={"simulation_id": sim_id, "task_id": task_id}, timeout=30))
            status = st.get("status") or st.get("simulation_status")
            prog = st.get("progress") or st.get("progress_percent") or 0
            _set(state, "prepare", "running", st.get("message") or st.get("current_step") or "", progress=prog)
            if status in ("ready", "completed") or st.get("already_prepared") or st.get("is_ready"):
                break
            if status in ("failed", "error"):
                raise RuntimeError(st.get("error") or "Vorbereitung fehlgeschlagen")
            time.sleep(10)
        n = prep.get("expected_entities_count") or prep.get("entities_count")
        _set(state, "prepare", "done", f"{n} Agenten" if n else "Agenten bereit")

        # 5 Simulation
        _set(state, "simulate", "running")
        _ok(s.post(f"{base}/api/simulation/start", json={"simulation_id": sim_id}, timeout=120))
        while True:
            rs = _ok(s.get(f"{base}/api/simulation/{sim_id}/run-status", timeout=30))
            _set(state, "simulate", "running",
                 f"Runde {rs.get('current_round', 0)}, {rs.get('twitter_actions_count', 0) + rs.get('reddit_actions_count', 0)} Aktionen bisher",
                 progress=rs.get("progress_percent", 0))
            if rs.get("runner_status") == "completed":
                _set(state, "simulate", "done", f"{rs.get('twitter_actions_count', 0) + rs.get('reddit_actions_count', 0)} Aktionen")
                break
            if rs.get("runner_status") in ("failed", "stopped"):
                raise RuntimeError(rs.get("error") or "Die Simulation wurde abgebrochen" if rs.get("runner_status") == "stopped" else "Die Simulation ist fehlgeschlagen")
            time.sleep(15)

        # 6 Bericht
        _set(state, "report", "running")
        rep = _ok(s.post(f"{base}/api/report/generate", json={"simulation_id": sim_id}, timeout=60))
        report_id, task_id = rep.get("report_id"), rep.get("task_id")
        state["report_id"] = report_id
        while True:
            st = _ok(s.post(f"{base}/api/report/generate/status",
                            json={"simulation_id": sim_id, "report_id": report_id, "task_id": task_id}, timeout=30))
            _set(state, "report", "running", st.get("message") or st.get("current_step") or "", progress=st.get("progress", 0))
            if st.get("status") == "completed":
                _set(state, "report", "done", "Bericht fertig")
                break
            if st.get("status") in ("failed", "error"):
                raise RuntimeError(st.get("error") or "Berichtsgenerierung fehlgeschlagen")
            time.sleep(15)

        state["status"] = "completed"
        state["completed_at"] = datetime.now().isoformat()
        _save(state)
    except Exception as e:
        logger.error(f"Durchlauf {pid} fehlgeschlagen in Stufe {state.get('current_step')}: {e}\n{traceback.format_exc()}")
        state["status"] = "failed"
        state["error"] = str(e)
        step = state.get("current_step")
        if step and isinstance(state.get("steps"), dict) and step in state["steps"]:
            state["steps"][step]["status"] = "failed"
            state["steps"][step]["detail"] = str(e)[:300]
        _save(state)
        # Der Fehler steht im Log. In der Oberfläche soll er nicht auftauchen:
        # der Durchlauf wird samt Daten entfernt, der Client sieht danach 404.
        try:
            from ..services.cleanup import delete_pipeline_cascade
            removed = delete_pipeline_cascade(pid)
            logger.info(f"Fehlgeschlagener Durchlauf aufgeräumt ({pid}): {removed}")
        except Exception as cleanup_error:
            logger.error(f"Aufräumen nach Fehlschlag {pid} fehlgeschlagen: {cleanup_error}")


@pipeline_bp.route('/start', methods=['POST'])
def start_pipeline():
    """multipart: files[] (PDF/MD/TXT), simulation_requirement, project_name (optional). Antwort: pipeline_id."""
    requirement = request.form.get('simulation_requirement', '').strip()
    if not requirement:
        return jsonify({"success": False, "error": "Bitte eine Frage oder Simulationsanforderung angeben"}), 400
    uploads = request.files.getlist('files')
    if not uploads:
        return jsonify({"success": False, "error": "Bitte mindestens eine Datei (PDF, MD, TXT) hochladen"}), 400
    pid = f"run_{uuid.uuid4().hex[:12]}"
    folder = os.path.join(_dir(), pid)
    os.makedirs(folder, exist_ok=True)
    files = []
    for f in uploads:
        name = os.path.basename(f.filename or "dokument.txt")
        path = os.path.join(folder, name)
        f.save(path)
        files.append((name, path))
    state = {
        "pipeline_id": pid, "status": "running", "created_at": datetime.now().isoformat(),
        "requirement": requirement, "project_name": request.form.get('project_name') or requirement[:60],
        "files": [n for n, _ in files], "current_step": None,
        "steps": {k: {"label": STEP_LABELS[k], "status": "pending", "detail": "", "progress": 0} for k in STEPS},
        "project_id": None, "graph_id": None, "simulation_id": None, "report_id": None, "error": None,
    }
    _save(state)
    threading.Thread(target=_run, args=(pid, files, requirement, state["project_name"]), daemon=True,
                     name=f"pipeline-{pid}").start()
    logger.info(f"Durchlauf gestartet: {pid} ({len(files)} Dateien)")
    return jsonify({"success": True, "data": {"pipeline_id": pid}})


@pipeline_bp.route('/<pid>', methods=['GET'])
def pipeline_status(pid):
    state = _load(pid)
    if not state:
        return jsonify({"success": False, "error": f"Durchlauf nicht gefunden: {pid}"}), 404
    return jsonify({"success": True, "data": state})


@pipeline_bp.route('/<pid>', methods=['DELETE'])
def delete_pipeline(pid):
    """Durchlauf löschen, inklusive Simulation und Projekt, wenn nichts anderes sie noch braucht.

    Läuft der Durchlauf noch, bleibt alles liegen.
    """
    from ..services.cleanup import CleanupBusy, CleanupError, delete_pipeline_cascade
    if not re.fullmatch(r"run_[0-9a-f]+", pid or ""):
        return jsonify({"success": False, "error": "Ungültige Durchlauf-ID"}), 400
    if not _load(pid):
        return jsonify({"success": False, "error": "Durchlauf nicht gefunden"}), 404
    try:
        removed = delete_pipeline_cascade(pid)
    except CleanupBusy:
        return jsonify({
            "success": False,
            "error": "Der Durchlauf läuft noch. Warte, bis er fertig ist, bevor du ihn löschst.",
        }), 409
    except CleanupError as exc:
        logger.info(f"Löschen abgewiesen ({pid}): {exc}")
        return jsonify({"success": False, "error": "Ungültiger Pfad"}), 400
    except Exception as exc:
        logger.error(f"Löschen fehlgeschlagen ({pid}): {exc}")
        return jsonify({"success": False, "error": "Löschen fehlgeschlagen."}), 500
    return jsonify({"success": True, "data": {"pipeline_id": pid, "deleted": removed}})


@pipeline_bp.route('/list', methods=['GET'])
def pipeline_list():
    items = []
    for name in sorted(os.listdir(_dir()), reverse=True):
        if name.endswith('.json'):
            st = _load(name[:-5])
            if st:
                items.append({k: st.get(k) for k in ("pipeline_id", "status", "created_at", "completed_at", "requirement",
                                                      "current_step", "simulation_id", "report_id", "error")})
    return jsonify({"success": True, "data": items[:50]})
