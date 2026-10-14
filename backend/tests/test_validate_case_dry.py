"""Trockenlauf: validate_case.py über alle acht Akten gegen eine lokale API-Attrappe."""
import json
import os
import subprocess
import sys
import threading
from pathlib import Path

from flask import Flask, jsonify, request
from werkzeug.serving import make_server

from scripts.validate_case import BOOTSTRAP_SAMPLES, DEFAULT_ARMS, PILOT_V5_FRAME, QUESTION

CASES = Path(__file__).resolve().parents[2] / "docs" / "validation" / "faelle"
SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_case.py"
FREIBURG = "freiburg-bewohnerparken-2021"
ARMS = list(DEFAULT_ARMS)
NOW = "2026-10-14T12:00:00"


class DryRun:
    def __init__(self):
        self.bodies = []
        self.starts = []
        self.uploads = []
        self.chats = 0
        self.chat_prompts = []
        self.ensembles = {}
        self._projects = {}
        self._tasks = {}
        self._sims = {}
        self._n = 0
        self._lock = threading.Lock()

    def _seq(self, prefix: str) -> str:
        self._n += 1
        return f"{prefix}{self._n:012d}"


def _envelope(data):
    return jsonify({"success": True, "data": data})


def _result_cell(rate: float, runs: int) -> dict:
    yes = int(round(rate * runs))
    return {"yes": yes, "n": runs, "unclassified": 0, "disputed": 0, "rate": round(yes / runs, 6),
            "ci_low": 0.2, "ci_high": 0.9, "evidence": []}


def _comparison(variant: str, outcome_id: str, primary_id: str) -> dict:
    table = {"both_yes": 6, "baseline_only": 2, "variant_only": 1, "both_no": 1,
             "n_pairs": 10, "unpaired": 0}
    confirmatory = outcome_id == primary_id
    return {"variant": variant, "outcome_id": outcome_id, "collapsed_outcome_ids": [],
            "role": "confirmatory" if confirmatory else "exploratory", "table": table,
            "diff": round((table["variant_only"] - table["baseline_only"]) / table["n_pairs"], 6),
            "ci_low": -0.4, "ci_high": 0.2, "mcnemar_p": 1.0,
            "newcombe": {"ci_low": -0.5, "ci_high": 0.3},
            "unreliable": False, "holm_p": None if confirmatory else 0.5}


def _completed_ensemble(body: dict, ensemble_id: str) -> dict:
    custom = body["custom_outcomes"]
    runs = int(body["runs"])
    primary = body.get("primary_outcome_id")
    rates = {"baseline": 0.8, "null_document": 0.4, "null_personas": 0.7}
    checklist = []
    for index, item in enumerate(custom, 1):
        entry = {"id": f"c{index}", "text_de": item["text_de"], "definition": item["text_de"],
                 "polarity": item.get("polarity") or "presence", "kind": "event", "source": "user",
                 "in_material": False}
        checklist.append(entry)
    results = {
        arm: {entry["id"]: _result_cell(rates[arm], runs) for entry in checklist}
        for arm in body["variants"]
    }
    comparisons = [
        _comparison(arm, entry["id"], primary)
        for arm in body["variants"] if arm != "baseline"
        for entry in checklist
    ]
    reliability = {entry["id"]: {"agreement": 0.9, "kappa": 0.8, "n_pairs": 20, "label": "messbar"}
                   for entry in checklist}
    run_stats = {}
    for arm in body["variants"]:
        narrative = arm != "baseline"
        run_stats[arm] = [{
            "run": number, "post_count": 0 if narrative else 4,
            "character_count": 800 if narrative else 400, "batch_count": 1,
            "search_action_count": 0, "trend_action_count": 0, "foreign_interaction_count": 0,
        } for number in range(1, runs + 1)]
    return {
        "ensemble_id": ensemble_id, "simulation_id": body["simulation_id"],
        "question": QUESTION, "status": "completed", "created_at": NOW, "finished_at": NOW,
        "runs": runs, "hours": body["hours"], "start_hour": 7,
        "minutes_per_round": body["minutes_per_round"],
        "variants": [{"key": arm, "label_de": arm, "label_en": arm, "status": "completed",
                      "done": runs, "total": runs} for arm in body["variants"]],
        "checklist": checklist, "custom_outcomes": custom, "primary_outcome_id": primary,
        "results": results, "comparisons": comparisons, "reliability": reliability,
        "run_stats": run_stats, "consistency_warnings": [], "current": None,
        "eta_seconds": 0, "error": None,
        "analysis": {"primary_outcome_id": primary, "confirmatory": "exact_mcnemar",
                     "paired_interval": "wald", "sensitivity": "newcombe_method_10",
                     "exploratory_correction": "holm",
                     "exploratory_m": sum(1 for item in comparisons if item["role"] == "exploratory")},
    }


def _build_app(state: DryRun) -> Flask:
    app = Flask(__name__)

    @app.before_request
    def _capture():
        state.bodies.append(request.get_data(cache=True) or b"")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/v1/chat/completions")
    def chat():
        body = request.get_json(silent=True) or {}
        text = "\n".join(
            str(item.get("content") or "")
            for item in body.get("messages") or [] if isinstance(item, dict))
        with state._lock:
            state.chats += 1
            state.chat_prompts.append(text)
        content = json.dumps({"known": False, "begruendung": "im Trockenlauf unbekannt"},
                             ensure_ascii=False)
        return jsonify({"id": "chatcmpl-dry", "object": "chat.completion", "created": 1710000000,
                        "model": "dry-run", "choices": [{"index": 0, "message": {
                            "role": "assistant", "content": content}, "finish_reason": "stop"}],
                        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}})

    @app.post("/api/graph/ontology/generate")
    def ontology():
        uploaded = request.files.get("files")
        raw = uploaded.read() if uploaded else b""
        case = "unbekannt"
        for folder in CASES.iterdir():
            sheet = folder / "ausgangslage.md"
            if sheet.is_file() and sheet.read_bytes() == raw:
                case = folder.name
                break
        project_name = request.form.get("project_name") or ""
        with state._lock:
            project_id = state._seq("proj_")
            state._projects[project_id] = case
            state.uploads.append({"case": case, "filename": uploaded.filename if uploaded else None,
                                  "requirement": request.form.get("simulation_requirement")})
        text_length = len(raw)
        return _envelope({"project_id": project_id, "project_name": project_name,
                          "ontology": {"entity_types": [], "edge_types": []},
                          "analysis_summary": "Trockenlauf",
                          "files": [{"filename": uploaded.filename if uploaded else "", "size": text_length}],
                          "total_text_length": text_length})

    @app.post("/api/graph/build")
    def build():
        project_id = (request.get_json(silent=True) or {}).get("project_id")
        with state._lock:
            task_id = state._seq("task_")
            graph_id = "mirofish_" + task_id
            state._tasks[task_id] = {"project_id": project_id, "graph_id": graph_id}
        return _envelope({"project_id": project_id, "task_id": task_id,
                          "message": "Graph-Aufbau-Aufgabe gestartet"})

    @app.get("/api/graph/task/<task_id>")
    def graph_task(task_id):
        task = state._tasks[task_id]
        return _envelope({"task_id": task_id, "task_type": "graph_build", "status": "completed",
                          "created_at": NOW, "updated_at": NOW, "progress": 100,
                          "message": "abgeschlossen", "progress_detail": {},
                          "result": {"graph_id": task["graph_id"], "graph_info": {},
                                     "chunks_processed": 1},
                          "error": None, "metadata": {}})

    @app.post("/api/simulation/create")
    def create_simulation():
        body = request.get_json(silent=True) or {}
        project_id = body.get("project_id")
        with state._lock:
            simulation_id = state._seq("sim_")
            state._sims[simulation_id] = state._projects[project_id]
            graph_id = next(item["graph_id"] for item in state._tasks.values()
                            if item["project_id"] == project_id)
        return _envelope({"simulation_id": simulation_id, "project_id": project_id,
                          "graph_id": graph_id, "status": "created", "enable_twitter": True,
                          "enable_reddit": True, "created_at": NOW, "updated_at": NOW,
                          "entities_count": 0, "profiles_count": 0, "entity_types": [],
                          "error": None})

    @app.post("/api/simulation/prepare")
    def prepare():
        body = request.get_json(silent=True) or {}
        with state._lock:
            task_id = state._seq("task_")
        return _envelope({"simulation_id": body.get("simulation_id"), "task_id": task_id,
                          "status": "preparing", "message": "Vorbereitungsaufgabe gestartet",
                          "already_prepared": False})

    @app.post("/api/simulation/prepare/status")
    def prepare_status():
        body = request.get_json(silent=True) or {}
        return _envelope({"task_id": body.get("task_id"), "simulation_id": body.get("simulation_id"),
                          "status": "completed", "progress": 100,
                          "message": "Vorbereitung abgeschlossen", "already_prepared": True,
                          "prepare_info": {}})

    @app.post("/api/ensemble/start")
    def ensemble_start():
        body = request.get_json(silent=True) or {}
        with state._lock:
            ensemble_id = state._seq("ens_")
            case = state._sims[body["simulation_id"]]
            document = _completed_ensemble(body, ensemble_id)
            state.ensembles[ensemble_id] = document
            state.starts.append({"case": case, "body": body})
        return _envelope({"ensemble_id": ensemble_id, "estimate_seconds": 1})

    @app.get("/api/ensemble/<ensemble_id>")
    def ensemble_get(ensemble_id):
        document = state.ensembles.get(ensemble_id)
        if document is None:
            return jsonify({"success": False, "error": f"Ensemble nicht gefunden: {ensemble_id}"}), 404
        return _envelope(document)

    return app


class _Server:
    def __init__(self, app: Flask):
        self.httpd = make_server("127.0.0.1", 0, app)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self.httpd.shutdown()
        self.thread.join(timeout=5)


def _run_case(case: Path, results: Path, base: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    for key in list(env):
        if key.lower().endswith("_proxy") or key.lower() == "no_proxy":
            env.pop(key, None)
    env.update({"NO_PROXY": "*", "LLM_PROVIDER": "openai", "LLM_API_KEY": "dry-run",
                "LLM_BASE_URL": f"{base}/v1", "LLM_MODEL_NAME": "dry-run",
                "OPENAI_API_KEY": "dry-run", "OPENAI_BASE_URL": f"{base}/v1"})
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(case), "--rahmen", "pilot-v5",
         "--base", base, "--results-dir", str(results)],
        cwd=SCRIPT.parent.parent, env=env, capture_output=True, text=True, timeout=120,
        check=False)


def test_dry_run_covers_all_eight_cases(tmp_path):
    folders = sorted(path for path in CASES.iterdir() if path.is_dir())
    assert [path.name for path in folders].count(FREIBURG) == 1
    assert len(folders) == 8
    state = DryRun()
    server = _Server(_build_app(state))
    server.start()
    base = f"http://127.0.0.1:{server.port}"
    results = tmp_path / "ergebnisse"
    try:
        import urllib.request
        with urllib.request.urlopen(base + "/health", timeout=5) as response:
            assert response.status == 200
        finished = {}
        for case in folders:
            finished[case.name] = _run_case(case, results, base)
    finally:
        server.stop()

    freiburg = finished[FREIBURG]
    assert freiburg.returncode == 1, freiburg.stderr
    assert "vorab kontaminiert" in freiburg.stderr
    for name, completed in finished.items():
        if name == FREIBURG:
            continue
        assert completed.returncode == 0, completed.stderr

    assert len(state.starts) == 7
    started = {item["case"] for item in state.starts}
    assert FREIBURG not in started
    assert started == {path.name for path in folders if path.name != FREIBURG}
    for item in state.starts:
        body = item["body"]
        assert body["runs"] == PILOT_V5_FRAME["seeds"]
        assert body["hours"] == 336
        assert body["minutes_per_round"] == 240
        assert body["variants"] == ARMS
        assert body["primary_outcome_id"] == "c1"
        assert body["text_model"] == PILOT_V5_FRAME["models"]["agent_model"]
        assert body["arm_model"] == PILOT_V5_FRAME["models"]["agent_model"]
        assert body["strict_second_rater"] is True
        assert body["min_classified"] == PILOT_V5_FRAME["min_classified_per_arm"]
        blinded = json.dumps(body["custom_outcomes"], ensure_ascii=False)
        assert "eingetreten" not in blinded
        assert "quellenluecke" not in blinded
        assert "kontaminiert" not in blinded
        assert "kodierhinweis" not in blinded
        assert "kaltfrage_ort" not in blinded
        for outcome in body["custom_outcomes"]:
            assert set(outcome) <= {"text_de", "polarity"}
    assert {item["filename"] for item in state.uploads} == {"ausgangslage.md"}
    assert {item["requirement"] for item in state.uploads} == {QUESTION}
    assert FREIBURG not in {item["case"] for item in state.uploads}

    blob = b"\n".join(state.bodies)
    assert b"eingetreten" not in blob
    assert b"verlauf.md" not in blob
    for case in folders:
        assert (case / "verlauf.md").read_bytes() not in blob
    assert state.chats == 28  # 2 Modelle x 2 Fragen x 7 Fälle
    for ensemble in state.ensembles.values():
        assert ensemble["status"] == "completed"
        for key in ("results", "comparisons", "reliability", "run_stats"):
            assert ensemble[key]

    summary = json.loads((results / "GESAMT.json").read_text(encoding="utf-8"))
    markdown = (results / "GESAMT.md").read_text(encoding="utf-8")
    assert summary["clean"]["case_count"] == 7
    assert summary["clean"]["scored_primary_cases"] == 7
    assert summary["sensitivity_no_source_gap"]["case_count"] == 4
    assert summary["sensitivity_no_source_gap"]["scored_primary_cases"] == 4
    assert summary["sensitivity_no_source_gap"]["replaces_primary"] is False
    assert summary["contaminated_cases"] == [FREIBURG]
    assert summary["source_gap_cases"] == [
        "kehl-tram-baumfaellungen-2017", "niederkassel-buecherei-2023",
        "wanzleben-grundschule-2025"]
    assert summary["bootstrap_samples"] == BOOTSTRAP_SAMPLES
    assert summary["bootstrap_unit"] == "case"
    skill = summary["clean"]["skill"]["baseline_vs_null_document"]
    assert isinstance(skill["value"], float)
    assert skill["ci_95"]["low"] <= skill["ci_95"]["high"]
    persona = summary["clean"]["skill"]["null_personas_vs_null_document"]
    assert isinstance(persona["value"], float)
    assert isinstance(persona["ci_95"]["low"], float)
    assert summary["clean"]["brier_ci_95"]["baseline"]["low"] <= summary["clean"]["brier_ci_95"]["baseline"]["high"]
    assert isinstance(summary["clean"]["s_vs_p"]["mean_distance"], float)
    assert summary["clean"]["s_vs_p"]["ci_95"]["low"] <= summary["clean"]["s_vs_p"]["ci_95"]["high"]
    assert summary["minutes_per_round"]["values"] == [240]
    assert summary["rahmen"] == PILOT_V5_FRAME
    assert "Rahmen pilot-v5 (vorgeschlagen, Start erst nach Freigabe des Projektinhabers)" in markdown
    assert "Pilot, keine Kalibrierungsaussage" in markdown
    labels = {}
    for folder in folders:
        outcomes = json.loads((folder / "ergebnisse.json").read_text(encoding="utf-8"))
        found = {item["kaltfrage_ort"] for item in outcomes if "kaltfrage_ort" in item}
        assert len(found) == 1
        labels[folder.name] = found.pop()
    identity = [prompt for prompt in state.chat_prompts if "\nFall: " in prompt]
    sheets = [prompt for prompt in state.chat_prompts if "folgenden Bogen" in prompt]
    assert len(identity) == 14 and len(sheets) == 14
    for name, label in labels.items():
        hits = [prompt for prompt in identity if f"Fall: {label}\n" in prompt]
        if name == FREIBURG:
            assert hits == []
            assert all(label not in prompt for prompt in state.chat_prompts)
        else:
            assert len(hits) == 2
        assert all(label not in prompt for prompt in sheets)
    blob_text = blob.decode("utf-8", errors="replace")
    for folder in folders:
        assert folder.name not in blob_text
        assert all(folder.name not in prompt for prompt in state.chat_prompts)
    assert "Primäranalyse: 7 nicht kontaminierte Fälle" in markdown
    assert "4 nicht kontaminierte Fälle ohne Quellenlücke" in markdown
    assert f"{BOOTSTRAP_SAMPLES} Ziehungen" in markdown
    assert "baseline_vs_null_document" in markdown

    skipped = json.loads((results / f"{FREIBURG}.json").read_text(encoding="utf-8"))
    assert skipped["runs"] == PILOT_V5_FRAME["seeds"]
    assert skipped["rahmen"]["id"] == "pilot-v5"
    assert skipped["contaminated"] is True and skipped["aborted_before_prepare"] is True
    assert skipped["ensemble_id"] is None
    assert not (results / f"{FREIBURG}.state.json").exists()
    for name in started:
        saved = json.loads((results / f"{name}.json").read_text(encoding="utf-8"))
        assert saved["runs"] == PILOT_V5_FRAME["seeds"]
        assert saved["hours"] == 336 and saved["minutes_per_round"] == 240
        assert saved["rahmen"]["id"] == "pilot-v5"
        assert saved["contaminated"] is False
        assert saved["contamination_check"]["known"] is False
        assert len(saved["contamination_check"]["probes"]) == 4
        assert {p["model"] for p in saved["contamination_check"]["probes"]} == set(PILOT_V5_FRAME["models"]["cold_question_models"])
        assert all(p["prompt"] and p["answer"] for p in saved["contamination_check"]["probes"])
        assert len(saved["ensemble_ids"]) == 1
        assert saved["primary_metrics"]["baseline"]["n"] == 1


def test_probe_mode_runs_two_seeds_and_is_not_scored(tmp_path):
    probe = CASES.parent / "probe"
    state = DryRun()
    server = _Server(_build_app(state))
    server.start()
    base = f"http://127.0.0.1:{server.port}"
    results = tmp_path / "probe-out"
    env = dict(os.environ, LLM_BASE_URL=base + "/v1", LLM_API_KEY="dry", LLM_MODEL_NAME="dry-run")
    try:
        done = subprocess.run(
            [sys.executable, str(SCRIPT), "--probe", "--base", base, "--results-dir", str(results)],
            cwd=SCRIPT.parent.parent, env=env, capture_output=True, text=True, timeout=120,
            check=False)
    finally:
        server.stop()
    assert done.returncode == 0, done.stderr
    assert len(state.starts) == 1
    assert state.starts[0]["body"]["runs"] == 2
    saved = json.loads((results / "probe.json").read_text(encoding="utf-8"))
    assert saved["rahmen"]["id"] == "probe-v5"
    summary = json.loads((results / "GESAMT.json").read_text(encoding="utf-8"))
    assert summary["clean"]["preregistered_criterion"]["status"] == "Probelauf, nicht gewertet"
    assert (probe / "ausgangslage.md").exists()
