"""V5-Realitätsabgleich: blinder HTTP-Ablauf und deterministische Statistik."""

import json
import math

import pytest

from scripts.validate_case import (
    QUESTION,
    bootstrap_mean_ci,
    build_case_result,
    validate_case,
)


class FakeApi:
    def __init__(self):
        self.posts = []
        self.gets = []
        self.ensemble_payload = None

    def post(self, path, **kwargs):
        self.posts.append((path, kwargs))
        if path == "/api/graph/ontology/generate":
            assert kwargs["data"]["simulation_requirement"] == QUESTION
            assert set(kwargs["files"]) == {"files"}
            assert kwargs["files"]["files"][0] == "ausgangslage.md"
            return {"project_id": "proj_blind"}
        if path == "/api/graph/build":
            return {"task_id": "task_graph"}
        if path == "/api/simulation/create":
            return {"simulation_id": "sim_blind"}
        if path == "/api/simulation/prepare":
            return {"task_id": "task_prepare"}
        if path == "/api/simulation/prepare/status":
            return {"status": "completed"}
        if path == "/api/ensemble/start":
            self.ensemble_payload = kwargs["json_body"]
            return {"ensemble_id": "ens_aaaaaaaaaaaa"}
        raise AssertionError(path)

    def get(self, path, **kwargs):
        self.gets.append(path)
        if path == "/api/graph/task/task_graph":
            return {"status": "completed", "result": {"graph_id": "graph_blind"}}
        if path == "/api/ensemble/ens_aaaaaaaaaaaa":
            custom = self.ensemble_payload["custom_outcomes"]
            checklist = [
                {"id": f"c{index}", "text_de": item["text_de"], "source": "user"}
                for index, item in enumerate(custom, 1)
            ]
            results = {
                "baseline": {
                    "c1": {"yes": 8, "n": 10, "rate": 0.8, "disputed": 0, "unclassified": 0},
                    "c2": {"yes": 2, "n": 10, "rate": 0.2, "disputed": 0, "unclassified": 0},
                },
                "null_model": {
                    "c1": {"yes": 4, "n": 10, "rate": 0.4, "disputed": 0, "unclassified": 0},
                    "c2": {"yes": 6, "n": 10, "rate": 0.6, "disputed": 0, "unclassified": 0},
                },
            }
            reliability = {
                key: {"agreement": 0.9, "kappa": 0.8, "n_pairs": 20, "label": "messbar"}
                for key in ("c1", "c2")
            }
            return {
                "status": "completed",
                "simulation_id": "sim_blind",
                "ensemble_id": "ens_aaaaaaaaaaaa",
                "checklist": checklist,
                "results": results,
                "reliability": reliability,
            }
        raise AssertionError(path)


def _case(tmp_path):
    case = tmp_path / "fall-a"
    case.mkdir()
    (case / "ausgangslage.md").write_text("Nur Wissen vor dem Ereignis.", encoding="utf-8")
    (case / "verlauf.md").write_text("Der echte Verlauf.", encoding="utf-8")
    (case / "ergebnisse.json").write_text(json.dumps([
        {"text_de": "Ereignis A tritt ein.", "eingetreten": True, "quelle": "1"},
        {"text_de": "Ereignis B tritt ein.", "eingetreten": False, "quelle": "2"},
    ]), encoding="utf-8")
    return case


def test_mocked_api_flow_is_blind_and_resumable(tmp_path):
    case = _case(tmp_path)
    output = tmp_path / "results"
    api = FakeApi()
    result = validate_case(
        case,
        runs=10,
        hours=336,
        base="http://test",
        results_dir=output,
        client=api,
        sleep=lambda _: None,
        poll_interval=0,
    )

    assert api.ensemble_payload == {
        "simulation_id": "sim_blind",
        "variants": ["baseline", "null_model"],
        "runs": 10,
        "hours": 336,
        "custom_outcomes": [
            {"text_de": "Ereignis A tritt ein."},
            {"text_de": "Ereignis B tritt ein."},
        ],
    }
    # Weder Wahrheitswert noch Verlauf gelangen in irgendeinen API-Body.
    serialized_calls = json.dumps(api.posts, default=str, ensure_ascii=False)
    assert "eingetreten" not in serialized_calls
    assert "Der echte Verlauf" not in serialized_calls
    state = json.loads((output / "fall-a.state.json").read_text(encoding="utf-8"))
    assert state["project_id"] == "proj_blind"
    assert state["simulation_id"] == "sim_blind"
    assert state["ensemble_id"] == "ens_aaaaaaaaaaaa"
    assert state["ensemble_completed"] is True
    assert result["metrics"]["simulation"]["brier"] == pytest.approx(0.04)
    assert (output / "fall-a.md").is_file()
    assert (output / "GESAMT.md").is_file()

    resumed_api = FakeApi()
    resumed_api.ensemble_payload = api.ensemble_payload
    validate_case(
        case,
        runs=10,
        hours=336,
        base="http://test",
        results_dir=output,
        client=resumed_api,
        sleep=lambda _: None,
        poll_interval=0,
    )
    assert resumed_api.posts == []
    assert resumed_api.gets == ["/api/ensemble/ens_aaaaaaaaaaaa"]


def test_brier_accuracy_and_log_score_known_values():
    outcomes = [
        {"text_de": "A", "eingetreten": True},
        {"text_de": "B", "eingetreten": False},
    ]
    ensemble = {
        "simulation_id": "sim_x",
        "ensemble_id": "ens_x",
        "checklist": [
            {"id": "c1", "text_de": "A", "source": "user"},
            {"id": "c2", "text_de": "B", "source": "user"},
        ],
        "results": {
            "baseline": {
                "c1": {"yes": 8, "n": 10, "rate": 0.8},
                "c2": {"yes": 2, "n": 10, "rate": 0.2},
            },
            "null_model": {
                "c1": {"yes": 4, "n": 10, "rate": 0.4},
                "c2": {"yes": 6, "n": 10, "rate": 0.6},
            },
        },
        "reliability": {
            key: {"agreement": 1.0, "kappa": 1.0, "n_pairs": 20, "label": "messbar"}
            for key in ("c1", "c2")
        },
    }
    result = build_case_result("known", outcomes, ensemble, runs=10, hours=168)
    assert result["metrics"]["simulation"] == {
        "n": 2,
        "brier": pytest.approx(0.04),
        "accuracy_at_0_5": pytest.approx(1.0),
        "log_score": pytest.approx(-math.log(0.8), abs=1e-6),
    }
    assert result["metrics"]["null_model"]["brier"] == pytest.approx(0.36)
    assert result["metrics"]["null_model"]["accuracy_at_0_5"] == 0.0


def test_bootstrap_is_deterministic_with_seed():
    values = [0.01, 0.04, 0.25, 0.64]
    first = bootstrap_mean_ci(values, seed=17, samples=500)
    second = bootstrap_mean_ci(values, seed=17, samples=500)
    assert first == second
    assert first == {"low": 0.025, "high": 0.49}
