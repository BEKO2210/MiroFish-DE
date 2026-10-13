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
    filter_checklist_material_numbers,
    mark_checklist_material,
    newcombe_difference_interval,
    parse_checklist,
    verified_material_quote,
    verify_classification_evidence,
    wilson_interval,
)
from app.utils.simulation_time import simulation_clock


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


def test_checklist_number_filter_normalizes_material_numbers():
    checklist = [
        {"text_de": "Es werden 3100 Unterstützende genannt", "definition": "Schwelle"},
        {"text_de": "Akteursgruppen suchen einen Kompromiss", "definition": "Beobachtbar"},
    ]
    assert filter_checklist_material_numbers(
        checklist, "Im Material stehen mehr als 3.100 Unterschriften."
    ) == [checklist[1]]


def test_material_quote_must_be_normalized_verbatim():
    material = "Eine öffentliche   Informationsveranstaltung ist angekündigt."
    valid = {"in_material": True, "zitat": "öffentliche Informationsveranstaltung ist angekündigt"}
    invented = {"in_material": True, "zitat": "eine Bürgerversammlung findet statt"}
    assert verified_material_quote(valid, material) == valid["zitat"]
    assert verified_material_quote(invented, material) == ""

    marked = mark_checklist_material(
        [{"id": "o1", "text_de": "Neues Ereignis", "definition": "ohne Worttreffer"}],
        material,
        [],
        [valid],
    )
    assert marked[0]["in_material"] is True
    assert marked[0]["material_snippet"] == valid["zitat"]
    rejected = mark_checklist_material(
        [{"id": "o1", "text_de": "Neues Ereignis", "definition": "ohne Worttreffer"}],
        material,
        [],
        [invented],
    )[0]
    assert rejected["in_material"] is False
    assert rejected["material_snippet"] == ""


def test_simulation_clock_starts_at_configured_hour_and_crosses_midnight():
    assert simulation_clock(0, 30, 7) == (1, 7)
    assert simulation_clock(1, 30, 7) == (1, 7)
    assert simulation_clock(34, 30, 7) == (2, 0)


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


class ChecklistRetryLLM:
    def __init__(self, always_contaminated=False):
        self.generation_prompts = []
        self.generation_kwargs = []
        self.always_contaminated = always_contaminated

    def chat_json(self, messages, **kwargs):
        prompt = messages[-1]["content"]
        if "Erzeuge 5 bis 8" in prompt:
            self.generation_prompts.append(prompt)
            self.generation_kwargs.append(kwargs)
            words = ["Eskalation", "Protest", "Dialog", "Kompromiss", "Ruhe"]
            outcomes = [
                {
                    "text_de": f"Im simulierten Zeitraum wird {word} sichtbar",
                    "definition": f"Beobachtbares Ereignis {word}",
                }
                for word in words
            ]
            if self.always_contaminated or len(self.generation_prompts) == 1:
                outcomes[0]["text_de"] += " mit 3100 Beteiligten"
            return {"outcomes": outcomes}
        return {"in_material": False, "zitat": ""}


def test_checklist_prompt_retries_after_material_number(tmp_path):
    llm = ChecklistRetryLLM()
    service = EnsembleService(llm_factory=lambda: llm, root=tmp_path / "ensembles")
    checklist = service._create_checklist(
        {"question": "Was geschieht?", "hours": 2, "base_seed": 41},
        {
            "extracted_text": "Es wurden 3.100 Unterschriften genannt.",
            "config": {"event_config": {"initial_posts": []}},
        },
    )
    assert len(checklist) == 5
    assert len(llm.generation_prompts) == 2
    assert "simulierten 2 Stunden" in llm.generation_prompts[0]
    assert "Im simulierten Zeitraum" in llm.generation_prompts[0]
    assert llm.generation_kwargs[0]["temperature"] == 0
    assert llm.generation_kwargs[0]["seed"] == 41
    assert llm.generation_kwargs[0]["max_attempts"] == 1
    assert all("3100" not in item["text_de"] for item in checklist)


def test_checklist_number_retry_stops_after_two_attempts(tmp_path):
    llm = ChecklistRetryLLM(always_contaminated=True)
    service = EnsembleService(llm_factory=lambda: llm, root=tmp_path / "ensembles")
    with pytest.raises(ValueError, match="nach zwei Versuchen"):
        service._create_checklist(
            {"question": "Was geschieht?", "hours": 2, "base_seed": 41},
            {
                "extracted_text": "Es wurden 3.100 Unterschriften genannt.",
                "config": {"event_config": {"initial_posts": []}},
            },
        )
    assert len(llm.generation_prompts) == 2


def test_start_hour_validation_happens_before_start(tmp_path):
    service = EnsembleService(root=tmp_path / "ensembles")
    for value in (-1, 24, True, "7"):
        with pytest.raises(ValueError, match="start_hour"):
            service.start("sim_test", 1, 2, ["baseline"], start_hour=value)


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
    started = service.start("sim_test", 2, 12, ["baseline"], start_hour=13)
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
    assert state["start_hour"] == 13
    first_config = json.loads(
        (tmp_path / "ensembles" / started["ensemble_id"] / "baseline" / "run_1" /
         "simulation_config.json").read_text(encoding="utf-8")
    )
    assert first_config["time_config"]["start_hour"] == 13
