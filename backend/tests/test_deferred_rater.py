"""Hermetische Tests für Export, Offline-Import und Deferred-Dienstmodus."""
import json
import sqlite3
from pathlib import Path

import pytest

from app.services.ensemble import EnsembleService
from scripts.export_rater_prompts import export_prompts
from scripts.import_second_rater import import_second_rater


CHECKLIST = [
    {"id": "c1", "text_de": "Ereignis eins", "definition": "Ereignis eins", "polarity": "presence"},
    {"id": "c2", "text_de": "Ereignis zwei", "definition": "Ereignis zwei", "polarity": "presence"},
]


def _write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _ensemble(tmp_path: Path) -> Path:
    root = tmp_path / "ensembles" / "ens_deadbeef1234"
    state = {
        "ensemble_id": root.name,
        "simulation_id": "sim_test",
        "status": "completed",
        "runs": 4,
        "hours": 2,
        "variants": [{"key": "baseline", "label_de": "Basislauf", "classification_models": {
            "primary": "gemma4:12b-it-qat-16k", "secondary": None,
        }}],
        "checklist": CHECKLIST,
        "primary_outcome_id": "c1",
        "strict_second_rater": True,
        "second_rater": "deferred",
        "second_rater_status": "ausstehend",
        "results_preliminary": True,
        "min_classified": 1,
        "models": {"classification_primary": "gemma4:12b-it-qat-16k", "classification_secondary": None},
    }
    _write_json(root / "ensemble.json", state)
    for run in range(1, 5):
        run_dir = root / "baseline" / f"run_{run}"
        _write_json(run_dir / "simulation_config.json", {"event_config": {"initial_posts": []}})
        connection = sqlite3.connect(run_dir / "twitter_simulation.db")
        connection.execute("CREATE TABLE post (post_id INTEGER, user_id INTEGER, content TEXT)")
        connection.execute(
            "INSERT INTO post VALUES (1, 7, ?)", ("Ereignis eins und Ereignis zwei",),
        )
        connection.commit()
        connection.close()
        evidence = [{
            "run": run, "platform": "twitter", "post_id": "twitter:1",
            "agent": "Agent 7", "text": "Ereignis eins und Ereignis zwei", "span": "ereignis eins",
        }]
        primary = {
            "c1": {"yes": True, "evidence": evidence},
            "c2": {"yes": False, "evidence": []},
        }
        _write_json(run_dir / "classification.json", {
            "run": run, "second_rater_status": "ausstehend",
            "raters": {"a": {"model": "gemma4:12b-it-qat-16k", "seed": run,
                              "batches": [], "result": primary}},
            "result": {key: {**value, "raters": {"a": value}, "preliminary": True}
                       for key, value in primary.items()},
        })
    return root


def _answer(path: Path, text: str) -> None:
    path.with_suffix(".answer.txt").write_text(text, encoding="utf-8")


def test_export_is_stable_and_import_handles_all_offline_answer_cases(tmp_path):
    ensemble = _ensemble(tmp_path)
    first, second = tmp_path / "prompts-a", tmp_path / "prompts-b"
    assert export_prompts(ensemble, first) == 4
    assert export_prompts(ensemble, second) == 4
    assert [p.relative_to(first) for p in sorted(first.rglob("*.json"))] == [
        p.relative_to(second) for p in sorted(second.rglob("*.json"))]
    for left in sorted(first.rglob("*.json")):
        assert left.read_bytes() == (second / left.relative_to(first)).read_bytes()

    batches = [first / "baseline" / f"run_{run}" / "batch_1.json" for run in range(1, 5)]
    _answer(batches[0], json.dumps({"results": [
        {"outcome_id": "c1", "yes": True, "post_ids": ["twitter:1"], "snippet": "Ereignis eins"},
        {"outcome_id": "c2", "yes": False},
    ]}))
    _answer(batches[1], json.dumps({"results": [
        {"outcome_id": "c1", "yes": False},
    ]}))
    _answer(batches[2], "```json\n" + json.dumps({"results": [
        {"outcome_id": "c1", "yes": True, "post_ids": ["twitter:1"], "snippet": "Ereignis eins"},
        {"outcome_id": "c2", "yes": True, "post_ids": ["twitter:1"], "snippet": "Ereignis zwei"},
    ]}) + "\n```")
    _answer(batches[3], "{kaputt")

    state = import_second_rater(ensemble, first, "gemini-3.8-flash-high (agy)")
    assert state["second_rater_status"] == "vollständig"
    assert state["results_preliminary"] is False
    assert state["models"]["classification_secondary"] == "gemini-3.8-flash-high (agy)"
    assert state["reliability"]["c1"]["n_pairs"] == 3
    assert state["reliability"]["c1"]["agreement"] == pytest.approx(2 / 3, abs=1e-4)
    assert state["results"]["baseline"]["c1"]["disputed"] == 1
    assert state["results"]["baseline"]["c1"]["unclassified"] == 1
    assert state["results"]["baseline"]["c2"]["disputed"] == 1
    assert state["results"]["baseline"]["c2"]["unclassified"] == 2
    run_two = json.loads((ensemble / "baseline" / "run_2" / "classification.json").read_text())
    assert run_two["result"]["c2"]["unclassified"] is True
    assert (ensemble / "baseline" / "run_2" / "classification.primary-only.json").is_file()


class _PrimaryLLM:
    model = "gemma4:12b-it-qat-16k"
    last_raw_response = None

    def chat_json(self, messages, **kwargs):
        payload = {"results": [{"outcome_id": "c1", "yes": False}]}
        self.last_raw_response = payload
        return payload


def test_service_deferred_mode_calls_only_primary_and_marks_preliminary(tmp_path):
    calls = []

    def factory(**kwargs):
        calls.append(kwargs)
        return _PrimaryLLM()

    service = EnsembleService(root=tmp_path / "ensembles", llm_factory=factory)
    run_dir = tmp_path / "run"
    state = {
        "checklist": [CHECKLIST[0]], "second_rater": "deferred",
        "second_rater_status": "ausstehend", "models": {
            "classification_primary": "gemma4:12b-it-qat-16k",
        },
    }
    result = service._classify_posts(
        state, [{"platform": "twitter", "post_id": "twitter:1", "agent": "A", "text": "anderes"}],
        seed=1, run_number=1, run_dir=run_dir,
    )
    audit = json.loads((run_dir / "classification.json").read_text())
    assert len(calls) == 1
    assert set(audit["raters"]) == {"a"}
    assert audit["second_rater_status"] == "ausstehend"
    assert result["c1"]["preliminary"] is True

    aggregate = {
        "runs": 1, "min_classified": 1, "hours": 2,
        "second_rater_status": "ausstehend", "primary_outcome_id": "c1",
        "variants": [{"key": "baseline"}, {"key": "null_document"}],
        "checklist": [CHECKLIST[0]],
    }
    service._aggregate(aggregate, {"baseline": [result], "null_document": [result]})
    assert aggregate["reliability"] == {}
    assert aggregate["comparisons"] == []
