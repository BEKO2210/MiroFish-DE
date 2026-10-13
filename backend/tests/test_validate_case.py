"""V5-Realitätsabgleich: blinder HTTP-Ablauf und fallweise Statistik."""
import inspect
import json
import math

import pytest

from scripts.validate_case import (
    ApiError,
    CALIBRATION_PILOT_NOTE,
    DEFAULT_ARMS,
    ENSEMBLE_RESUME_ATTEMPTS,
    QUESTION,
    bootstrap_mean_ci,
    build_case_result,
    build_summary,
    calibration_slope,
    case_markdown,
    load_outcomes,
    outcome_horizon_hours,
    parse_args,
    parse_arms,
    run_ensemble,
    summary_markdown,
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


def test_mocked_api_flow_arms_primary_and_resume(tmp_path):
    case, output, api = _case(tmp_path), tmp_path / "results", FakeApi()
    probes = []

    def checker(identity, prompt):
        probes.append((identity, prompt))
        return {"kennt": False, "begruendung": "unbekannt"}

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
    assert "# Schulschließung" not in probes[0][1]
    assert "# Schulschließung" in probes[1][1]
    assert all("Der echte Verlauf" not in prompt for _, prompt in probes)
    assert result["contaminated"] is False
    assert result["primary_outcome_id"] == "c1"
    assert result["primary_metrics"]["baseline"]["brier"] == pytest.approx(.04)
    assert result["metrics_citable"] is False
    assert "nicht zitierfähig" in case_markdown(result)

    resumed = FakeApi()
    resumed.ensemble_payload = api.ensemble_payload
    validate_case(case, runs=10, hours=336, arms=DEFAULT_ARMS, base="http://test",
                  results_dir=output, client=resumed,
                  contamination_checker=lambda *_: pytest.fail("Probe darf nicht wiederholt werden"),
                  sleep=lambda _: None, poll_interval=0)
    assert resumed.posts == []
    assert resumed.gets == ["/api/ensemble/ens_aaaaaaaaaaaa"]


def test_known_cold_question_aborts_before_prepare(tmp_path):
    case, output, api = _case(tmp_path), tmp_path / "results", FakeApi()
    probes = []

    def checker(identity, prompt):
        probes.append(prompt)
        if "Bogen" in prompt:
            return {"kennt": True, "begruendung": "Bogen erkannt"}
        return {"kennt": False, "begruendung": "Ort unbekannt"}

    with pytest.raises(ValueError, match="kontaminiert"):
        validate_case(case, runs=1, hours=336, arms=DEFAULT_ARMS, base="http://test",
                      results_dir=output, client=api, contamination_checker=checker,
                      sleep=lambda _: None, poll_interval=0)
    assert api.posts == []
    assert any("Bogen" in prompt for prompt in probes)
    saved = json.loads((output / "fall-a.json").read_text(encoding="utf-8"))
    assert saved["contaminated"] is True
    assert saved["aborted_before_prepare"] is True
    state = json.loads((output / "fall-a.state.json").read_text(encoding="utf-8"))
    assert state["contamination_check"]["known"] is True
    assert state["contamination_check"]["material_known"] is True
    assert state["contamination_check"]["identity_known"] is False
    summary = json.loads((output / "GESAMT.json").read_text(encoding="utf-8"))
    assert summary["contaminated_cases"] == ["fall-a"]

    with pytest.raises(ValueError, match="kontaminiert"):
        validate_case(case, runs=1, hours=336, arms=DEFAULT_ARMS, base="http://test",
                      results_dir=output, client=api,
                      contamination_checker=lambda *_: pytest.fail("nicht erneut"),
                      sleep=lambda _: None, poll_interval=0)
    assert api.posts == []


def test_arms_are_selectable_and_validated():
    assert parse_arms("baseline,isolated") == ["baseline", "isolated"]
    with pytest.raises(ValueError, match="Unbekannte Arme"):
        parse_arms("baseline,null_model")


def test_exactly_one_primary_outcome_before_any_call(tmp_path):
    case = _case(tmp_path)
    outcomes = json.loads((case / "ergebnisse.json").read_text(encoding="utf-8"))
    outcomes[1]["primaer"] = True
    (case / "ergebnisse.json").write_text(json.dumps(outcomes), encoding="utf-8")
    with pytest.raises(ValueError, match="genau eine"):
        load_outcomes(case)

    nested = tmp_path / "zero"
    nested.mkdir()
    empty = _case(nested, primary=False)
    api = FakeApi()
    with pytest.raises(ValueError, match="genau eine"):
        validate_case(empty, results_dir=tmp_path / "zero-out", client=api,
                      contamination_checker=lambda *_: pytest.fail("kein API"),
                      sleep=lambda _: None, poll_interval=0)
    assert api.posts == []


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
    assert clean["calibration"]["baseline"]["note"] == CALIBRATION_PILOT_NOTE
    assert clean["preregistered_criterion"]["status"] == "nicht bestanden"
    assert "Abstand Schwarm (S)" in summary_markdown(summary)


def test_calibration_slope_known_grouped_data():
    probabilities = [.2] * 10 + [.8] * 10
    actual = [1, 1] + [0] * 8 + [1] * 8 + [0, 0]
    assert calibration_slope(probabilities, actual) == pytest.approx(1, abs=1e-8)


def test_bootstrap_is_deterministic_with_seed():
    values = [.01, .04, .25, .64]
    assert bootstrap_mean_ci(values, seed=17, samples=500) == {"low": .025, "high": .49}


def test_hours_default_is_two_weeks():
    assert inspect.signature(validate_case).parameters["hours"].default == 336
    assert parse_args(["fall"]).hours == 336


def test_file_in_material_horizon_and_uncitable_pool():
    assert outcome_horizon_hours({"text_de": "Innerhalb von 14 Tagen geschieht etwas"}) == 336
    assert outcome_horizon_hours({"text_de": "Fünf Wochen später", "zeitfenster": "T0+14 Tage"}) == 840
    assert outcome_horizon_hours({"text_de": "innerhalb von sechs Wochen"}) == 1008
    assert outcome_horizon_hours({"text_de": "Innerhalb von 3 Monaten wird die Zahl nicht beziffert"}) == 2160
    outcomes = [
        {"text_de": "Innerhalb von 14 Tagen geschieht A.", "eingetreten": True, "primaer": True},
        {"text_de": "Innerhalb von 3 Monaten wird die Zahl nicht beziffert.", "eingetreten": False},
        {"text_de": "Die Stadt stellt den Betrieb innerhalb von sechs Wochen ein.",
         "eingetreten": True, "in_material": True},
    ]
    ensemble = {
        "checklist": [
            {"id": "c1", "text_de": outcomes[0]["text_de"], "source": "user", "in_material": False},
            {"id": "c2", "text_de": outcomes[1]["text_de"], "source": "user", "in_material": False},
            {"id": "c3", "text_de": outcomes[2]["text_de"], "source": "user", "in_material": False},
        ],
        "results": {"baseline": {
            "c1": {"n": 10, "yes": 8, "rate": .8},
            "c2": {"n": 10, "yes": 2, "rate": .2},
            "c3": {"n": 10, "yes": 9, "rate": .9},
        }},
        "reliability": {key: {"agreement": 1, "kappa": .8, "n_pairs": 20, "label": "messbar"}
                        for key in ("c1", "c2", "c3")},
        "comparisons": [{
            "variant": "null_personas", "outcome_id": "c1",
            "table": {"both_yes": 3, "baseline_only": 2, "variant_only": 1,
                      "both_no": 4, "n_pairs": 10, "unpaired": 0},
        }],
    }
    result = build_case_result("fenster", outcomes, ensemble, runs=10, hours=336, arms=["baseline"])
    assert result["rows"][0]["measurable"] is True
    assert result["rows"][1]["measurable"] is False and result["rows"][1]["beyond_horizon"] is True
    assert result["rows"][2]["measurable"] is False and result["rows"][2]["in_material"] is True
    assert result["metrics"]["baseline"]["n"] == 1
    assert result["metrics_citable"] is False
    assert result["primary_s_vs_p"]["distance"] == pytest.approx(.1)
    assert result["primary_s_vs_p"]["table"]["baseline_only"] == 2


def test_s_vs_p_mean_distance_bootstraps_cases():
    def case(name, distance):
        item = _summary_case(name, 1, {"baseline": 1, "null_document": .5, "null_personas": .5})
        item["primary_s_vs_p"] = {
            "distance": distance,
            "table": {"both_yes": 1, "baseline_only": 2, "variant_only": 0,
                      "both_no": 7, "n_pairs": 10, "unpaired": 0},
        }
        return item

    summary = build_summary([case("a", .2), case("b", .0)])
    contrast = summary["clean"]["s_vs_p"]
    assert contrast["mean_distance"] == pytest.approx(.1)
    assert contrast["ci_95"]["low"] <= .1 <= contrast["ci_95"]["high"]
    assert [item["case"] for item in contrast["cases"]] == ["a", "b"]
    assert "0.1000" in summary_markdown(summary)


def _skill_case(name, actual, baseline, null):
    return _summary_case(name, actual, {
        "baseline": baseline, "null_document": null, "null_personas": baseline,
    })


def test_pilot_status_follows_skill_not_slope():
    above = [_skill_case(f"a{i}", 1, 1, .5) for i in range(2)]
    passed = build_summary(above)["clean"]
    assert passed["calibration"]["baseline"]["slope"] is None
    assert passed["calibration"]["baseline"]["note"] == CALIBRATION_PILOT_NOTE
    assert passed["preregistered_criterion"]["checks"]["skill_interval_above_zero"] is True
    assert "calibration_slope_0_5_to_1_5" not in passed["preregistered_criterion"]["checks"]
    assert passed["preregistered_criterion"]["status"] == "bestanden"

    below = [_skill_case(f"b{i}", 1, 0, .5) for i in range(2)]
    failed = build_summary(below)["clean"]
    assert failed["calibration"]["baseline"]["slope"] is None
    assert failed["skill"]["baseline_vs_null_document"]["ci_95"]["high"] < 0
    assert failed["preregistered_criterion"]["status"] == "nicht bestanden"

    mixed = (
        [_skill_case(f"y{i}", 1, .65, 0) for i in range(3)]
        + [_skill_case("flip0", 0, .65, 1)]
        + [_skill_case(f"n{i}", 0, .35, 1) for i in range(3)]
        + [_skill_case("flip1", 1, .35, 0)]
    )
    steep = build_summary(mixed)["clean"]
    assert steep["scored_primary_cases"] == 8
    assert steep["calibration"]["baseline"]["slope"] == pytest.approx(1.774706, abs=1e-4)
    assert steep["calibration"]["baseline"]["slope"] > 1.5
    assert steep["skill"]["baseline_vs_null_document"]["ci_95"]["low"] > 0
    assert steep["preregistered_criterion"]["status"] == "bestanden"


class _FailedThenDone:
    def __init__(self):
        self.posts, self.gets, self.failures = [], [], 0

    def post(self, path, **kwargs):
        self.posts.append(path)
        if path.endswith("/resume"):
            return {"ensemble_id": "ens_aaaaaaaaaaaa", "status": "queued"}
        raise AssertionError(path)

    def get(self, path, **kwargs):
        self.gets.append(path)
        self.failures += 1
        if self.failures == 1:
            return {"status": "failed", "error": "Seed abgestürzt"}
        return {"status": "completed", "ensemble_id": "ens_aaaaaaaaaaaa"}


def test_failed_ensemble_is_resumed_instead_of_stopping(tmp_path):
    api = _FailedThenDone()
    state_path = tmp_path / "fall.state.json"
    state = {"ensemble_id": "ens_aaaaaaaaaaaa"}
    result = run_ensemble(api, [], state_path, state, sleep=lambda _: None, poll_interval=0)
    assert result["status"] == "completed"
    assert api.posts == ["/api/ensemble/ens_aaaaaaaaaaaa/resume"]
    assert json.loads(state_path.read_text(encoding="utf-8"))["ensemble_completed"] is True


def test_ensemble_resume_is_limited(tmp_path):
    class AlwaysFailed:
        def __init__(self):
            self.posts = []

        def post(self, path, **kwargs):
            self.posts.append(path)
            return {"status": "queued"}

        def get(self, path, **kwargs):
            return {"status": "failed", "error": "Seed tot"}

    api = AlwaysFailed()
    with pytest.raises(ApiError, match="Seed tot"):
        run_ensemble(api, [], tmp_path / "fall.state.json",
                     {"ensemble_id": "ens_aaaaaaaaaaaa"}, sleep=lambda _: None, poll_interval=0)
    assert len(api.posts) == ENSEMBLE_RESUME_ATTEMPTS
