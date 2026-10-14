"""Vertragstest vom V5-Falltreiber bis zum echten Flask-Ensemble-Dienst."""
from __future__ import annotations

import csv
import importlib.util
import json
import re
import sqlite3
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit

import pytest

import app.services.ensemble as ensemble_module
from app.config import Config
from app.services.ensemble import EnsembleService
from app.services.report_validation import resolve_project_dir, resolve_simulation_dir
from scripts import validate_case as vc


ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / "docs" / "validation" / "faelle"
PILOT_CASES = ("karlsfeld-hallenbad-2023", "kehl-tram-baumfaellungen-2017")


class FlaskResponse:
    def __init__(self, response):
        self._response = response
        self.status_code = response.status_code
        self.text = response.get_data(as_text=True)

    def json(self):
        return self._response.get_json()


class FlaskSession:
    """Kleine requests-kompatible Hülle um den echten Flask-Testclient."""

    def __init__(self, client):
        self.client = client

    @staticmethod
    def _path(url):
        parsed = urlsplit(url)
        return parsed.path + (("?" + parsed.query) if parsed.query else "")

    def get(self, url, **_):
        return FlaskResponse(self.client.get(self._path(url)))

    def post(self, url, json=None, data=None, files=None, **_):
        if files:
            multipart = dict(data or {})
            multipart.update({key: (handle, name) for key, (name, handle, _mime) in files.items()})
            response = self.client.post(self._path(url), data=multipart)
        else:
            response = self.client.post(self._path(url), json=json, data=data)
        return FlaskResponse(response)


class SyntheticRunner:
    """OASIS-Grenze: schreibt eine echte, vom Dienst gelesene Plattform-DB."""

    states = {}

    @classmethod
    def start_simulation(cls, simulation_id, simulation_dir, **_):
        run_dir = Path(simulation_dir)
        connection = sqlite3.connect(run_dir / "twitter_simulation.db")
        connection.execute(
            "CREATE TABLE user (user_id INTEGER, agent_id INTEGER, name TEXT, user_name TEXT)"
        )
        connection.execute("INSERT INTO user VALUES (1, 1, 'Verein', 'verein')")
        connection.execute("CREATE TABLE post (post_id INTEGER, user_id INTEGER, content TEXT)")
        for post_id, text in enumerate((
            "Der Verein veröffentlicht eine deutliche Stellungnahme.",
            "Der Verein bekräftigt seine Stellungnahme erneut.",
            "Der Verein ruft zu einer Aussprache auf.",
        ), start=1):
            connection.execute("INSERT INTO post VALUES (?, 1, ?)", (post_id, text))
        connection.commit()
        connection.close()
        actions = run_dir / "twitter" / "actions.jsonl"
        actions.parent.mkdir(parents=True, exist_ok=True)
        actions.write_text(
            json.dumps({"action_type": "create_post", "success": True}) + "\n",
            encoding="utf-8",
        )
        state = SimpleNamespace(runner_status="completed", current_round=1, error=None)
        cls.states[simulation_id] = state
        return state

    @classmethod
    def get_run_state(cls, simulation_id):
        return cls.states[simulation_id]

    @classmethod
    def stop_simulation(cls, _simulation_id):
        return None


class LLMRecorder:
    def __init__(self):
        self.prompts = []
        self.models = []
        self.failed_batches = 0
        self.fail_one_batch = False

    def factory(self, *_, model=None, **__):
        return BoundaryLLM(self, model or "configured-main-model")


class BoundaryLLM:
    """LLM-Grenze für Ontologie/Nullarm/Klassifikation mit Prompt-Audit."""

    def __init__(self, recorder, model):
        self.recorder = recorder
        self.model = model
        recorder.models.append(model)

    def _prompt(self, messages):
        text = "\n".join(str(item.get("content") or "") for item in messages)
        self.recorder.prompts.append(text)
        return text

    def chat(self, messages, **_):
        self._prompt(messages)
        return (
            "Der Verein veröffentlicht eine deutliche Stellungnahme. "
            "Eine Bürgerinitiative diskutiert die Maßnahme öffentlich."
        )

    def chat_json(self, messages, **_):
        text = self._prompt(messages)
        if "Erzeuge 5 bis 8" in text:
            return {"outcomes": [
                {
                    "text_de": f"Im simulierten Zeitraum wird Reaktion {index} sichtbar",
                    "definition": f"Beobachtbare allgemeine Reaktion {index}",
                    "polarity": "presence",
                    "kind": "event",
                }
                for index in range(1, 6)
            ]}
        if "Wird dieses Ereignis im Material" in text:
            return {"in_material": False, "zitat": ""}
        if "Zu prüfende positive Ereignisse" in text and self.recorder.fail_one_batch:
            # BATCH_ATTEMPTS == 3: Erst wenn alle Parser-Versuche scheitern, ist
            # der gesamte Stapel unklassifiziert und der Seed wird wiederholt.
            if self.recorder.failed_batches < 3:
                self.recorder.failed_batches += 1
                raise ValueError("synthetischer Klassifikationsausfall")
        ids = list(dict.fromkeys(re.findall(r"(?m)^((?:o|c)\d+):", text)))
        if "Beiträge:" in text:
            return {"results": [{
                "outcome_id": oid,
                "yes": True,
                "post_ids": ["twitter:1"],
                "snippet": "veröffentlicht eine deutliche Stellungnahme",
            } for oid in ids]}
        return {"results": [{
            "outcome_id": oid,
            "yes": False,
            "snippet": "",
        } for oid in ids]}


def _load_real_create_app():
    """conftest hält app absichtlich leicht; nur dieser Test lädt die Fabrik nach."""
    package = sys.modules["app"]
    path = Path(__file__).resolve().parents[1] / "app" / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        "app", path, submodule_search_locations=[str(path.parent)]
    )
    assert spec and spec.loader
    package.__file__ = str(path)
    package.__spec__ = spec
    spec.loader.exec_module(package)
    return package.create_app


def _write_prepared_simulation(upload_root: Path, simulation_id: str, case_dir: Path) -> None:
    sim = upload_root / "simulations" / simulation_id
    sim.mkdir(parents=True)
    project_id = "proj_" + simulation_id.removeprefix("sim_")
    (upload_root / "projects" / project_id).mkdir(parents=True)
    (upload_root / "projects" / project_id / "extracted_text.txt").write_text(
        (case_dir / "ausgangslage.md").read_text(encoding="utf-8"), encoding="utf-8"
    )
    config = {
        "simulation_id": simulation_id,
        "simulation_requirement": vc.QUESTION,
        "llm_model": vc.PILOT_V5_FRAME["models"]["agent_model"],
        "time_config": {"total_simulation_hours": 1, "minutes_per_round": 60},
        "agent_configs": [{"agent_id": 1, "entity_name": "Verein", "entity_type": "Verein"}],
        "event_config": {"initial_posts": []},
    }
    (sim / "simulation_config.json").write_text(json.dumps(config), encoding="utf-8")
    (sim / "state.json").write_text(json.dumps({"project_id": project_id}), encoding="utf-8")
    (sim / "reddit_profiles.json").write_text(
        json.dumps([{"user_id": 1, "name": "Verein"}]), encoding="utf-8"
    )
    with (sim / "twitter_profiles.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["user_id", "name"])
        writer.writeheader()
        writer.writerow({"user_id": 1, "name": "Verein"})


def _seed_driver_state(results_dir, case_dir, simulation_id, frame):
    state = vc._new_state(
        case_dir.name, "http://flask.test", frame["seeds"], frame["hours"],
        frame["arms"], frame["minutes_per_round"],
    )
    state.update({
        "project_id": "proj_prepared",
        "graph_task_id": "task_prepared",
        "graph_id": "graph_prepared",
        "simulation_id": simulation_id,
        "prepare_task_id": "task_prepared",
        "prepared": True,
    })
    vc._save_state(results_dir / f"{case_dir.name}.state.json", state)


def _wait_for_threads():
    deadline = time.time() + 5
    while EnsembleService._threads and time.time() < deadline:
        time.sleep(0.01)
    assert not EnsembleService._threads


@pytest.fixture
def pilot_stack(tmp_path, monkeypatch):
    upload_root = tmp_path / "uploads"
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(upload_root))
    monkeypatch.setattr(Config, "OASIS_SIMULATION_DATA_DIR", str(upload_root / "simulations"))
    monkeypatch.setattr(Config, "LLM_PROVIDER", "ollama")
    monkeypatch.setattr(Config, "LOCAL_LLM_MODEL_NAME", "gemma4:12b-it-qat-16k")
    monkeypatch.setattr(Config, "ENSEMBLE_SECOND_RATER_MODEL", "qwen3.5:9b-agent32k")
    # Die Resolver beziehen ihre Wurzeln aus Config; diese Assertions schützen den Test vor
    # versehentlichem Schreiben in backend/uploads.
    assert Path(resolve_simulation_dir("sim_guard")).parent == upload_root / "simulations"
    assert Path(resolve_project_dir("proj_guard")).parent == upload_root / "projects"

    recorder = LLMRecorder()
    tag_checks = []
    combined_results = []
    original_combine = ensemble_module.combine_rater_results

    def recording_combine(*args, **kwargs):
        result = original_combine(*args, **kwargs)
        combined_results.append(result)
        return result

    monkeypatch.setattr(ensemble_module, "combine_rater_results", recording_combine)

    def ollama_tags():
        tag_checks.append(True)
        return ["gemma4:e4b-it-qat-16k", "gemma4:12b-it-qat-16k", "qwen3.5:9b-agent32k"]

    def ollama_show(_model):
        return {"parameters": "num_ctx 32768"}

    service = EnsembleService(
        runner_cls=SyntheticRunner,
        llm_factory=recorder.factory,
        root=upload_root / "ensembles",
        poll_interval=0.001,
        health_check=ollama_tags,
        ollama_show=ollama_show,
        min_free_bytes=0,
    )
    import app.api.ensemble as ensemble_api
    monkeypatch.setattr(ensemble_api, "service", service)
    create_app = _load_real_create_app()
    app = create_app()
    app.config.update(TESTING=True)
    api = vc.ApiClient(
        "http://flask.test", session=FlaskSession(app.test_client()),
        sleep=lambda _: None, retry_seconds=0,
    )
    yield upload_root, recorder, tag_checks, combined_results, api, app.test_client(), service
    _wait_for_threads()


def test_probe_and_two_real_cases_reach_real_service(pilot_stack, tmp_path):
    upload_root, recorder, tag_checks, combined_results, api, _client, service = pilot_stack
    cold_prompts = []

    def cold_check(_model, prompt):
        cold_prompts.append(prompt)
        return "Ich kenne den Fall nicht."

    completed = []
    runs = [
        (vc.PROBE_DIR, vc.load_rahmen("probe-v5"), tmp_path / "probe-results"),
        *[
            (CASES / name, vc.load_rahmen("pilot-v5"), tmp_path / "pilot-results")
            for name in PILOT_CASES
        ],
    ]
    for index, (case_dir, frame, results_dir) in enumerate(runs, 1):
        results_dir.mkdir(parents=True, exist_ok=True)
        simulation_id = f"sim_{index:012x}"
        _write_prepared_simulation(upload_root, simulation_id, case_dir)
        _seed_driver_state(results_dir, case_dir, simulation_id, frame)
        # Ein echter Klassifikationsstapel scheitert in allen drei Parser-Versuchen. Der Dienst muss den
        # Lauf als unklassifiziert verwerfen und denselben Seed technisch wiederholen.
        if case_dir == vc.PROBE_DIR:
            recorder.fail_one_batch = True
        result = vc.validate_case(
            case_dir,
            runs=frame["seeds"], hours=frame["hours"],
            minutes_per_round=frame["minutes_per_round"], arms=frame["arms"],
            base="http://flask.test", results_dir=results_dir, client=api,
            contamination_checker=cold_check, rahmen=frame,
            sleep=lambda _: None, poll_interval=0.001,
        )
        completed.append((case_dir, frame, results_dir, result))

    assert tag_checks, "Der strenge Zweitbewerter muss gegen Ollama /api/tags geprüft werden"
    probe_state = service._load(completed[0][3]["ensemble_id"])
    assert recorder.failed_batches == 3
    failed_judgment = next(
        result for result in combined_results
        if result and all(item.get("unclassified") for item in result.values())
    )
    assert all(item["yes"] is False for item in failed_judgment.values())
    assert all(item["unclassified"] is True for item in failed_judgment.values())
    assert probe_state["seed_attempts"]["baseline:1"] == 2
    assert probe_state["results"]["baseline"]["c1"]["n"] == 2
    assert probe_state["results"]["baseline"]["c1"]["unclassified"] == 0

    agent_model = vc.PILOT_V5_FRAME["models"]["agent_model"]
    for _case_dir, frame, _results_dir, result in completed:
        state = service._load(result["ensemble_id"])
        assert state["runs"] == frame["seeds"]
        assert state["hours"] == frame["hours"]
        assert state["minutes_per_round"] == frame["minutes_per_round"]
        assert [item["key"] for item in state["variants"]] == frame["arms"]
        assert state["strict_second_rater"] is True
        assert state["min_classified"] == frame["min_classified_per_arm"]
        assert state["min_posts"] == 3
        assert state["models"]["agents"] == agent_model
        assert state["models"]["null_arms"] == agent_model
        assert set(state["arm_models"].values()) == {agent_model}
        ensemble_root = upload_root / "ensembles" / result["ensemble_id"]
        baseline_config = json.loads((
            ensemble_root / "baseline" / "run_1" / "simulation_config.json"
        ).read_text(encoding="utf-8"))
        assert baseline_config["llm_model"] == agent_model
        assert baseline_config["time_config"] == {
            "total_simulation_hours": frame["hours"],
            "minutes_per_round": frame["minutes_per_round"],
            "start_hour": 7,
        }
        for arm in ("null_document", "null_personas"):
            manifest = json.loads((
                ensemble_root / arm / "run_1" / "manifest.json"
            ).read_text(encoding="utf-8"))
            assert manifest["model"] == agent_model

    probe_summary = json.loads((tmp_path / "probe-results" / "GESAMT.json").read_text())
    pilot_summary = json.loads((tmp_path / "pilot-results" / "GESAMT.json").read_text())
    assert probe_summary["clean"]["preregistered_criterion"]["status"] == vc.PROBE_STATUS
    # Zwei von sieben Rahmenfällen dürfen nach der präregistrierten Regel nicht als
    # bestanden oder nicht bestanden umgedeutet werden.
    assert pilot_summary["clean"]["preregistered_criterion"]["status"] == vc.NOT_TESTABLE
    assert "2 statt 7 gewertete Fälle" in " ".join(pilot_summary["clean"]["frame_issues"])

    all_prompts = "\n".join(cold_prompts + recorder.prompts)
    assert "eingetreten" not in all_prompts.casefold()
    for case_dir, *_ in completed:
        verlauf = (case_dir / "verlauf.md").read_text(encoding="utf-8").strip()
        assert verlauf not in all_prompts
        quellen_path = case_dir / "quellen.md"
        if quellen_path.is_file():
            assert quellen_path.read_text(encoding="utf-8").strip() not in all_prompts
        visible = (
            (case_dir / "ausgangslage.md").read_text(encoding="utf-8")
            + (case_dir / "ergebnisse.json").read_text(encoding="utf-8")
        )
        hidden_only_lines = [
            line.lstrip("- ").strip()
            for line in verlauf.splitlines()
            if len(line.lstrip("- ").strip()) >= 40
            and line.lstrip("- ").strip() not in visible
        ]
        assert all(line not in all_prompts for line in hidden_only_lines)


def test_start_contract_rejects_unknown_and_deviating_values(pilot_stack, tmp_path):
    upload_root, _recorder, _tags, _combined, _api, client, _service = pilot_stack
    simulation_id = "sim_ffffffffffff"
    _write_prepared_simulation(upload_root, simulation_id, vc.PROBE_DIR)
    base = {
        "simulation_id": simulation_id,
        "runs": 2,
        "hours": 336,
        "minutes_per_round": 240,
        "variants": list(vc.DEFAULT_ARMS),
    }
    response = client.post("/api/ensemble/start", json={**base, "minute_per_round": 240})
    assert response.status_code == 400
    assert "Unbekannte Startparameter: minute_per_round" in response.get_json()["error"]

    response = client.post("/api/ensemble/start", json={**base, "minutes_per_round": 30})
    assert response.status_code == 400
    assert "minutes_per_round muss 60, 120 oder 240 sein" in response.get_json()["error"]

    args = vc.parse_args([str(vc.PROBE_DIR), "--rahmen", "pilot-v5", "--runs", "2"])
    with pytest.raises(ValueError, match="weicht vom Rahmenwert 5 ab"):
        vc.resolve_invocation(args)
