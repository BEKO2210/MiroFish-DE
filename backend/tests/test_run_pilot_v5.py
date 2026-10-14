"""Tests für Treiber, Retry und Kaltabruf-Hilfen des V5-Pilots (ohne echten Lauf)."""
import json

import pytest
import requests

from scripts import run_pilot_v5 as driver
from scripts import validate_case as vc


class _Resp:
    def __init__(self, status=200, payload=None):
        self.status_code, self._payload, self.text = status, payload if payload is not None else {
            "success": True, "data": {"ok": 1}}, "x"

    def json(self):
        return self._payload


class _Session:
    def __init__(self, outcomes):
        self.outcomes, self.calls = list(outcomes), 0

    def _next(self, *_, **__):
        self.calls += 1
        item = self.outcomes.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    get = post = _next


def _client(outcomes, retry_seconds=1800):
    waits = []
    session = _Session(outcomes)
    return vc.ApiClient("http://x", session, sleep=waits.append, retry_seconds=retry_seconds), session, waits


def test_get_retries_transient_errors_with_backoff():
    client, session, waits = _client([requests.ConnectionError("weg"), requests.Timeout("zu lang"),
                                      _Resp(503), _Resp()])
    assert client.get("/p") == {"ok": 1}
    assert session.calls == 4
    assert waits == [5, 10, 20]


def test_retry_budget_is_thirty_minutes():
    client, session, waits = _client([requests.ConnectionError("weg")] * 100)
    with pytest.raises(requests.ConnectionError):
        client.get("/p")
    assert 1500 <= sum(waits) <= 1800
    assert max(waits) == 300


def test_post_retries_only_when_marked_and_client_errors_are_final():
    plain, session, _ = _client([requests.ConnectionError("weg"), _Resp()])
    with pytest.raises(requests.ConnectionError):
        plain.post("/ensemble/start", json_body={})
    assert session.calls == 1
    marked, session, waits = _client([_Resp(502), _Resp()])
    assert marked.post("/simulation/prepare", json_body={}, retry=True) == {"ok": 1}
    assert waits == [5]
    failing, session, _ = _client([_Resp(400, {"success": False, "error": "kaputt"})])
    with pytest.raises(vc.ApiError):
        failing.get("/p")
    assert session.calls == 1


def test_hidden_terms_and_local_matching():
    outcomes = [{
        "text_de": "Innerhalb von 14 Tagen lehnt der Rat den Antrag ab.",
        "quelle": "Beschluss der DLRG am 07.05.2024, 120 Plätze",
    }]
    terms = vc.hidden_terms(
        outcomes, "Der Rat berät den Antrag.", verlauf="innerhalb von 14 Tagen",
    )
    assert "07.05.2024" in terms["strong"] and "120" in terms["strong"] and "DLRG" in terms["strong"]
    assert "14" not in terms["strong"]
    assert vc.contamination_hits("Am 07.05.2024 beschloss der Rat.", terms)["known"] is True
    assert vc.contamination_hits("Ich kenne den Fall nicht.", terms)["known"] is False
    assert vc.contamination_hits("nur die Zahl 14 aus der Frage", terms)["known"] is False

    secret = "GEHEIMQUELLE-KENNZEICHEN-NICHT-SENDEN"
    sourced = vc.hidden_terms(
        [{"text_de": "Innerhalb von 14 Tagen geschieht etwas.", "quelle": ""}],
        "sichtbarer Text",
        quellen=f"{secret}\nDie Akte nennt 88 Vorgänge.",
    )
    assert "88" in sourced["strong"] and "14" not in sourced["strong"]
    prompts = []

    def ask(model, prompt):
        prompts.append(prompt)
        return "Ich kenne den Fall nicht."

    vc.check_contamination(
        "Ort", ask, material="Material ohne Geheimnis.",
        hidden_outcomes=[{"text_de": "Innerhalb von 14 Tagen geschieht etwas.", "quelle": ""}],
        verlauf="Im Verlauf stehen 120 eigene Tage.",
        quellen=secret,
    )
    joined = "\n".join(prompts)
    assert prompts and secret not in joined and "120" not in joined


def test_ensemble_start_options_only_from_frame():
    assert vc.ensemble_start_options(None) == {}
    options = vc.ensemble_start_options(vc.load_rahmen("pilot-v5"))
    assert options == {"text_model": vc.PILOT_V5_FRAME["models"]["agent_model"],
                       "arm_model": vc.PILOT_V5_FRAME["models"]["agent_model"],
                       "strict_second_rater": True,
                       "min_classified": vc.PILOT_V5_FRAME["min_classified_per_arm"],
                       "min_posts": "agent_count"}


def test_probe_frame_is_two_seeds_single_case():
    probe = vc.load_rahmen("probe-v5")
    assert probe["seeds"] == 2 and probe["case_ids"] == ["probe"]
    assert vc.PROBE_DIR.is_dir()


class _Fake:
    def __init__(self, models, listed):
        self.models, self.listed = models, listed

    def get(self, path, allow_list=False, **_):
        if path == "/api/system/models":
            return {"reachable": True, "models": [{"name": name} for name in self.models]}
        return self.listed


def test_preflight_reports_disk_models_and_busy():
    frame = vc.load_rahmen("pilot-v5")
    ok = _Fake(driver.required_models(frame), [{"ensemble_id": "e1", "status": "completed"}])
    report = driver.preflight(ok, frame, data_dir=driver.DEFAULT_DATA_DIR, min_free_gb=1,
                              disk_free_gb=lambda _: 100)
    assert report["problems"] == []
    bad = _Fake(driver.required_models(frame)[:1], [{"ensemble_id": "e2", "status": "running"}])
    with pytest.raises(driver.PreflightError) as error:
        driver.preflight(bad, frame, data_dir=driver.DEFAULT_DATA_DIR, min_free_gb=50,
                         disk_free_gb=lambda _: 10)
    text = str(error.value)
    assert "Plattenplatz" in text and "Modelle fehlen" in text and "belegt" in text and "e2" in text


def test_run_pilot_runs_seven_in_order_and_resumes_after_failure(tmp_path, monkeypatch):
    frame = vc.load_rahmen("pilot-v5")
    monkeypatch.setattr(driver, "preflight", lambda *a, **k: {"free_gb": 99})
    order, failed_once, logs, sleeps = [], [], [], []

    def run_case(case_dir, **kwargs):
        name = case_dir.name
        order.append(name)
        if name == frame["case_ids"][2] and not failed_once:
            failed_once.append(1)
            raise vc.ApiError("Backend weg")
        vc._write_json_atomic(kwargs["results_dir"] / f"{name}.json",
                              {"schema_version": 2, "rows": [1], "case": name})
        return {}

    monkeypatch.setattr(vc, "update_summary", lambda d, f: {"clean": {"preregistered_criterion": {
        "status": "nicht prüfbar"}}})
    outcome = driver.run_pilot(frame, cases_dir=tmp_path / "faelle", results_dir=tmp_path / "out",
                               base="http://x", client=object(), log=logs.append,
                               sleep=sleeps.append, run_case=run_case)
    assert order[:2] == frame["case_ids"][:2]
    assert order.count(frame["case_ids"][2]) == 2
    assert set(outcome["cases"]) == set(frame["case_ids"]) and len(frame["case_ids"]) == 7
    assert all(value == "abgeschlossen" for value in outcome["cases"].values())
    assert sleeps and any("Resume" in line for line in logs)
    assert outcome["stopped"] is None


def test_run_pilot_stops_when_attempts_exhausted(tmp_path, monkeypatch):
    frame = vc.load_rahmen("pilot-v5")
    monkeypatch.setattr(driver, "preflight", lambda *a, **k: {"free_gb": 99})

    def run_case(*_, **__):
        raise vc.ApiError("immer kaputt")

    outcome = driver.run_pilot(frame, cases_dir=tmp_path, results_dir=tmp_path / "out", base="x",
                               client=object(), log=lambda _: None, sleep=lambda _: None,
                               run_case=run_case, max_attempts=2)
    assert outcome["stopped"]["case"] == frame["case_ids"][0]
    assert len(json.dumps(outcome)) > 0
