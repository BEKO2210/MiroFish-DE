"""V5-Realitätsabgleich: blinder HTTP-Ablauf und fallweise Statistik."""
import json
import math

import pytest

from scripts.validate_case import (
    DEFAULT_ARMS,
    QUESTION,
    bootstrap_mean_ci,
    build_case_result,
    build_summary,
    calibration_slope,
    load_outcomes,
    parse_arms,
    validate_case,
)


class FakeApi:
    def __init__(self):
        self.posts, self.gets, self.ensemble_payload = [], [], None

    def post(self, path, **kwargs):
        self.posts.append((path, kwargs))
        if path == "/api/graph/ontology/generate":
            assert kwargs["data"]["simulation_requirement"] == QUESTION
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
            checklist = [{"id": f"c{i}", "text_de": item["text_de"], "source": "user"}
                         for i, item in enumerate(self.ensemble_payload["custom_outcomes"], 1)]
            rates = {
                "baseline": (.8, .2), "null_document": (.4, .6),
                "null_personas": (.7, .3), "isolated": (.6, .4),
            }
            results = {
                arm: {f"c{i}": {"yes": round(rate * 10), "n": 10, "rate": rate,
                                  "disputed": 0, "unclassified": 0}
                      for i, rate in enumerate(values, 1)}
                for arm, values in rates.items() if arm in self.ensemble_payload["variants"]
            }
            reliability = {key: {"agreement": .9, "kappa": .8, "n_pairs": 20, "label": "messbar"}
                           for key in ("c1", "c2")}
            return {"status": "completed", "simulation_id": "sim_blind",
                    "ensemble_id": "ens_aaaaaaaaaaaa", "checklist": checklist,
                    "results": results, "reliability": reliability}
        raise AssertionError(path)


def _case(tmp_path, primary=True):
    case = tmp_path / "fall-a"
    case.mkdir()
    (case / "ausgangslage.md").write_text(
        "# Schulschließung\nOrt: Beispielstadt\nJahr: 2024\nThema: geplante Schulschließung",
        encoding="utf-8",
    )
    (case / "verlauf.md").write_text("Der echte Verlauf.", encoding="utf-8")
    outcomes = [
        {"text_de": "Ereignis A tritt ein.", "eingetreten": True, "quelle": "1", "primaer": primary},
        {"text_de": "Ereignis B tritt ein.", "eingetreten": False, "quelle": "2"},
    ]
    (case / "ergebnisse.json").write_text(json.dumps(outcomes), encoding="utf-8")
    return case


def test_mocked_api_flow_arms_primary_contamination_and_resume(tmp_path):
    case, output, api = _case(tmp_path), tmp_path / "results", FakeApi()
    probes = []

    def checker(identity, prompt):
        probes.append((identity, prompt))
        return {"kennt": True, "begruendung": "Fall ist bekannt"}

    result = validate_case(case, runs=10, hours=336, arms=DEFAULT_ARMS, base="http://test",
                           results_dir=output, client=api, contamination_checker=checker,
                           sleep=lambda _: None, poll_interval=0)
    assert api.ensemble_payload == {
        "simulation_id": "sim_blind", "variants": list(DEFAULT_ARMS), "runs": 10,
        "hours": 336, "custom_outcomes": [{"text_de": "Ereignis A tritt ein."},
                                             {"text_de": "Ereignis B tritt ein."}],
        "primary_outcome_id": "c1",
    }
    serialized = json.dumps(api.posts, default=str, ensure_ascii=False)
    assert "eingetreten" not in serialized and "Der echte Verlauf" not in serialized
    assert probes[0][0] == {"location": "Beispielstadt", "year": "2024",
                            "topic": "geplante Schulschließung"}
    assert "Der echte Verlauf" not in probes[0][1]
    assert result["contaminated"] is True
    assert result["primary_outcome_id"] == "c1"
    assert result["primary_metrics"]["baseline"]["brier"] == pytest.approx(.04)

    resumed = FakeApi()
    resumed.ensemble_payload = api.ensemble_payload
    validate_case(case, runs=10, hours=336, arms=DEFAULT_ARMS, base="http://test",
                  results_dir=output, client=resumed,
                  contamination_checker=lambda *_: pytest.fail("Probe darf nicht wiederholt werden"),
                  sleep=lambda _: None, poll_interval=0)
    assert resumed.posts == []
    assert resumed.gets == ["/api/ensemble/ens_aaaaaaaaaaaa"]


def test_arms_are_selectable_and_validated():
    assert parse_arms("baseline,isolated") == ["baseline", "isolated"]
    with pytest.raises(ValueError, match="Unbekannte Arme"):
        parse_arms("baseline,null_model")


def test_exactly_at_most_one_primary_outcome(tmp_path):
    case = _case(tmp_path)
    outcomes = json.loads((case / "ergebnisse.json").read_text(encoding="utf-8"))
    outcomes[1]["primaer"] = True
    (case / "ergebnisse.json").write_text(json.dumps(outcomes), encoding="utf-8")
    with pytest.raises(ValueError, match="höchstens eine"):
        load_outcomes(case)


def test_brier_per_arm_and_primary_separate():
    outcomes = [{"text_de": "A", "eingetreten": True, "primaer": True},
                {"text_de": "B", "eingetreten": False}]
    ensemble = {
        "checklist": [{"id": "c1", "text_de": "A", "source": "user"},
                      {"id": "c2", "text_de": "B", "source": "user"}],
        "results": {
            "baseline": {"c1": {"n": 10, "yes": 8, "rate": .8}, "c2": {"n": 10, "yes": 2, "rate": .2}},
            "null_document": {"c1": {"n": 10, "yes": 4, "rate": .4}, "c2": {"n": 10, "yes": 6, "rate": .6}},
            "null_personas": {"c1": {"n": 10, "yes": 7, "rate": .7}, "c2": {"n": 10, "yes": 3, "rate": .3}},
        },
        "reliability": {key: {"agreement": 1, "kappa": .8, "n_pairs": 20, "label": "messbar"}
                        for key in ("c1", "c2")},
    }
    result = build_case_result("known", outcomes, ensemble, runs=10, hours=168, arms=DEFAULT_ARMS)
    assert result["metrics"]["baseline"] == {
        "n": 2, "brier": pytest.approx(.04), "accuracy_at_0_5": 1,
        "log_score": pytest.approx(-math.log(.8), abs=1e-6),
    }
    assert result["primary_metrics"]["null_document"]["brier"] == pytest.approx(.36)


def _summary_case(name, actual, rates, *, contaminated=False, exploratory_rate=None):
    rows = [{"primary": True, "measurable": True, "actual": actual,
             "reliability": {"kappa": .8},
             "arms": {arm: {"rate": rate} for arm, rate in rates.items()}}]
    if exploratory_rate is not None:
        rows.append({"primary": False, "measurable": True, "actual": 1 - actual,
                     "reliability": {"kappa": .8},
                     "arms": {arm: {"rate": exploratory_rate} for arm in rates}})
    return {"case": name, "arms": list(rates), "rows": rows, "contaminated": contaminated}


def test_skill_and_bootstrap_use_cases_not_questions():
    cases = [
        _summary_case("a", 1, {"baseline": 1, "null_document": .5, "null_personas": .75}, exploratory_rate=0),
        _summary_case("b", 0, {"baseline": .5, "null_document": .5, "null_personas": .25}, exploratory_rate=1),
        _summary_case("known", 1, {"baseline": 0, "null_document": 1, "null_personas": 0}, contaminated=True),
    ]
    summary = build_summary(cases)
    clean = summary["clean"]
    assert summary["bootstrap_unit"] == "case"
    assert clean["scored_primary_cases"] == 2
    assert clean["brier"]["baseline"] == pytest.approx(.125)
    assert clean["brier"]["null_document"] == pytest.approx(.25)
    assert clean["skill"]["baseline_vs_null_document"]["value"] == pytest.approx(.5)
    assert summary["contaminated"]["case_count"] == 1
    assert clean["calibration"]["baseline"]["note"] == "Pilot, keine Kalibrierungsaussage"
    assert clean["preregistered_criterion"]["status"] == "nicht bestanden"


def test_calibration_slope_known_grouped_data():
    probabilities = [.2] * 10 + [.8] * 10
    actual = [1, 1] + [0] * 8 + [1] * 8 + [0, 0]
    assert calibration_slope(probabilities, actual) == pytest.approx(1, abs=1e-8)


def test_bootstrap_is_deterministic_with_seed():
    values = [.01, .04, .25, .64]
    assert bootstrap_mean_ci(values, seed=17, samples=500) == {"low": .025, "high": .49}
