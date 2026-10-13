"""V3/V4: Statistik, Checkliste, Belege, Varianten und Zustandsmaschine."""

import csv
import json
import sqlite3
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.config import Config
from app.services.ensemble import (
    EnsembleService,
    apply_without_variant,
    newcombe_difference_interval,
    parse_checklist,
    verify_classification_evidence,
    wilson_interval,
)


def test_wilson_known_value():
    low, high = wilson_interval(5, 10)
    assert low == pytest.approx(0.236593, abs=1e-6)
    assert high == pytest.approx(0.763407, abs=1e-6)
    assert wilson_interval(0, 0) == (0.0, 0.0)


def test_newcombe_method_10_known_value():
    low, high = newcombe_difference_interval(7, 10, 3, 10)
    # Newcombe (1998), Methode 10: Wilson-Komponenten per MOVER kombiniert.
    assert low == pytest.approx(-0.028820, abs=1e-6)
    assert high == pytest.approx(0.671824, abs=1e-6)
    reverse = newcombe_difference_interval(3, 10, 7, 10)
    assert reverse[0] == pytest.approx(-high)
    assert reverse[1] == pytest.approx(-low)


def test_checklist_parsing_and_validation():
    parsed = parse_checklist(
        {"outcomes": [
            {"text_de": f"Beobachtbares Ergebnis {i}", "definition": f"Definition {i}"}
            for i in range(1, 6)
        ]}
    )
    assert [item["id"] for item in parsed] == ["o1", "o2", "o3", "o4", "o5"]
    with pytest.raises(ValueError):
        parse_checklist(["eins", "zwei"])


def test_evidence_must_reference_existing_post():
    checklist = [{"id": "o1"}, {"id": "o2"}]
    posts = [{
        "platform": "twitter",
        "post_id": "twitter:7",
        "agent": "Ada",
        "text": "Eine Gruppe startet eine Unterschriftensammlung.",
    }]
    result = verify_classification_evidence(
        {"results": [
            {"outcome_id": "o1", "yes": True, "post_ids": ["twitter:7"]},
            {"outcome_id": "o2", "yes": True, "post_ids": ["reddit:999"]},
        ]},
        posts,
        checklist,
        2,
    )
    assert result["o1"]["yes"] is True
    assert result["o1"]["evidence"][0]["run"] == 2
    assert result["o2"] == {"yes": False, "evidence": []}


def test_without_variant_removes_agents_profiles_and_initial_posts():
    config = {
        "agent_configs": [
            {"agent_id": 0, "entity_type": "Person"},
            {"agent_id": 1, "entity_type": "Partei"},
            {"agent_id": 2, "entity_type": "Person"},
        ],
        "event_config": {"initial_posts": [
            {"poster_agent_id": 1, "content": "Partei-Start"},
            {"poster_agent_id": 2, "content": "Person-Start"},
        ]},
    }
    reddit = [{"user_id": i, "name": str(i)} for i in range(3)]
    twitter = [{"user_id": str(i), "name": str(i)} for i in range(3)]
    changed, reddit_out, twitter_out = apply_without_variant(
        config, reddit, twitter, "Partei"
    )
    assert [a["agent_id"] for a in changed["agent_configs"]] == [0, 1]
    assert all(a["entity_type"] == "Person" for a in changed["agent_configs"])
    assert changed["event_config"]["initial_posts"] == [
        {"poster_agent_id": 1, "content": "Person-Start"}
    ]
    assert [p["user_id"] for p in reddit_out] == [0, 1]
    assert [p["user_id"] for p in twitter_out] == ["0", "1"]


class FakeLLM:
    def chat_json(self, messages, **kwargs):
        text = messages[-1]["content"]
        if "Erzeuge 5 bis 8" in text:
            return {"outcomes": [
                {"text_de": f"Ergebnis {i} wird sichtbar", "definition": f"Eindeutiges Ereignis {i}"}
                for i in range(1, 6)
            ]}
        return {"results": [
            {"outcome_id": f"o{i}", "yes": i == 1, "post_ids": ["twitter:1"]}
            for i in range(1, 6)
        ]}

    def chat(self, messages, **kwargs):
        return "Eine kurze Erzählung."


class FakeRunner:
    states = {}

    @classmethod
    def start_simulation(cls, simulation_id, simulation_dir, **kwargs):
        run_dir = Path(simulation_dir)
        db = sqlite3.connect(run_dir / "twitter_simulation.db")
        db.execute("CREATE TABLE user (user_id INTEGER, agent_id INTEGER, name TEXT, user_name TEXT)")
        db.execute("INSERT INTO user VALUES (0, 0, 'Ada', 'ada')")
        db.execute("CREATE TABLE post (post_id INTEGER, user_id INTEGER, content TEXT)")
        db.execute("INSERT INTO post VALUES (1, 0, 'Ein neuer Aufruf wird veröffentlicht.')")
        db.commit()
        db.close()
        state = SimpleNamespace(runner_status="completed", current_round=1, error=None)
        cls.states[simulation_id] = state
        return state

    @classmethod
    def get_run_state(cls, simulation_id):
        return cls.states[simulation_id]


def _prepared_simulation(upload: Path) -> None:
    sim = upload / "simulations" / "sim_test"
    sim.mkdir(parents=True)
    config = {
        "simulation_requirement": "Was geschieht?",
        "time_config": {"total_simulation_hours": 24, "minutes_per_round": 60},
        "agent_configs": [{"agent_id": 0, "entity_type": "Person"}],
        "event_config": {"initial_posts": []},
    }
    (sim / "simulation_config.json").write_text(json.dumps(config), encoding="utf-8")
    (sim / "state.json").write_text(json.dumps({"project_id": "proj_test"}), encoding="utf-8")
    (sim / "reddit_profiles.json").write_text(
        json.dumps([{"user_id": 0, "name": "Ada"}]), encoding="utf-8"
    )
    with (sim / "twitter_profiles.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["user_id", "name"])
        writer.writeheader()
        writer.writerow({"user_id": 0, "name": "Ada"})
    project = upload / "projects" / "proj_test"
    project.mkdir(parents=True)
    (project / "extracted_text.txt").write_text("Ausgangsmaterial ohne Ergebnis.", encoding="utf-8")


def test_state_machine_with_mocked_runner(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(tmp_path))
    _prepared_simulation(tmp_path)
    service = EnsembleService(
        runner_cls=FakeRunner,
        llm_factory=FakeLLM,
        root=tmp_path / "ensembles",
        poll_interval=0.001,
    )
    started = service.start("sim_test", 2, 12, ["baseline"])
    deadline = time.time() + 3
    while time.time() < deadline:
        state = service.get(started["ensemble_id"])
        if state["status"] in {"completed", "failed"}:
            break
        time.sleep(0.01)
    assert state["status"] == "completed", state.get("error")
    assert state["variants"][0]["done"] == 2
    assert state["results"]["baseline"]["o1"]["yes"] == 2
    assert state["results"]["baseline"]["o1"]["n"] == 2
