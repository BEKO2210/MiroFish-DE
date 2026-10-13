"""V3/V4: Statistik, Checkliste, Belege, Varianten und Zustandsmaschine."""

import csv
import json
import sqlite3
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
import app.utils.llm_client as llm_module

from app.config import Config
from app.services.ensemble import (
    EnsembleService,
    apply_without_variant,
    build_post_batches,
    filter_checklist_material_numbers,
    infer_kind,
    load_simulation_posts,
    mark_checklist_material,
    newcombe_difference_interval,
    parse_checklist,
    verified_material_quote,
    verify_classification_evidence,
    wilson_interval,
)
from app.utils.llm_client import LLMClient, estimate_tokens
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


def test_checklist_polarity_is_explicit_or_inferred():
    parsed = parse_checklist({"outcomes": [
        {"text_de": "Im Zeitraum geschieht etwas", "definition": "sichtbar", "polarity": "presence"},
        {"text_de": "Im Zeitraum gibt es keine Reaktion", "definition": "bleibt aus"},
    ] + [
        {"text_de": f"Weiteres Ergebnis {i}", "definition": "sichtbar"}
        for i in range(3)
    ]})
    assert parsed[0]["polarity"] == "presence"
    assert parsed[1]["polarity"] == "absence"


def test_checklist_kind_is_explicit_or_migrated_from_text():
    assert infer_kind("Eine öffentliche Debatte zwischen Stadtpolitik und Eltern findet statt") == "interaction"
    assert infer_kind("Die Stadt veröffentlicht eine Stellungnahme") == "event"
    parsed = parse_checklist({"outcomes": [
        {"text_de": "Eine Diskussion findet statt", "definition": "direkter Austausch"},
        {"text_de": "Eine Meldung erscheint", "definition": "sichtbar", "kind": "event"},
    ] + [
        {"text_de": f"Weiteres Ergebnis {i}", "definition": "sichtbar"}
        for i in range(3)
    ]})
    assert parsed[0]["kind"] == "interaction"
    assert parsed[1]["kind"] == "event"


def test_post_batches_respect_budget_and_order():
    posts = [
        {"post_id": f"twitter:{i}", "agent": "Ada", "text": "x" * 120}
        for i in range(12)
    ]
    prefix = "Anweisung und Checkliste\nBeiträge:\n"
    batches = build_post_batches(posts, prefix, 180)
    assert len(batches) > 1
    assert [post["post_id"] for batch in batches for post in batch] == [
        post["post_id"] for post in posts
    ]
    assert all(
        estimate_tokens(prefix + "\n".join(
            f"[{post['post_id']}] {post['agent']}: {post['text']}" for post in batch
        )) <= 180
        for batch in batches
    )


def test_local_llm_warns_when_estimated_context_is_exceeded(monkeypatch, caplog):
    client = object.__new__(LLMClient)
    client.provider = "ollama"
    client.client = object()
    client.model = "local-test"
    monkeypatch.setenv("LOCAL_LLM_CONTEXT", "10")
    monkeypatch.setattr(llm_module, "create_chat_completion", lambda *args, **kwargs: object())
    with caplog.at_level("WARNING"):
        client._create_completion(
            messages=[{"role": "user", "content": "x" * 30}],
            temperature=0,
            max_tokens=5,
            response_format=None,
        )
    assert "überschreitet das geschätzte Kontextbudget" in caplog.text


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


class BatchLLM:
    def __init__(self, fail=False, positive=False):
        self.calls = 0
        self.fail = fail
        self.positive = positive

    def chat_json(self, messages, **kwargs):
        self.calls += 1
        if self.fail:
            raise ValueError("auch der zweite Versuch ist unparsebar")
        return {"results": [{
            "outcome_id": "o1",
            "yes": self.positive,
            "post_ids": ["twitter:1"] if self.positive else [],
        }]}


def test_100000_char_posts_are_classified_in_multiple_audited_batches(tmp_path):
    llm = BatchLLM()
    service = EnsembleService(llm_factory=lambda: llm, root=tmp_path / "ensembles")
    run_dir = tmp_path / "run"
    posts = [{
        "platform": "twitter",
        "post_id": "twitter:1",
        "agent": "Ada",
        "text": "x" * 100_000,
    }]
    result = service._classify_posts(
        {"checklist": [{
            "id": "o1", "text_de": "Ein Ereignis tritt ein",
            "definition": "beobachtbar", "polarity": "presence",
        }]},
        posts,
        seed=7,
        run_number=1,
        run_dir=run_dir,
    )
    audit = json.loads((run_dir / "classification.json").read_text(encoding="utf-8"))
    assert llm.calls == len(audit["batches"])
    assert len(audit["batches"]) > 1
    assert all(batch["estimated_input_tokens"] <= audit["token_budget"] for batch in audit["batches"])
    assert result["o1"]["yes"] is False


def test_absence_is_yes_only_when_positive_event_is_not_found(tmp_path):
    llm = BatchLLM(positive=False)
    service = EnsembleService(llm_factory=lambda: llm, root=tmp_path / "ensembles")
    result = service._classify_posts(
        {"checklist": [{
            "id": "o1",
            "text_de": "Im simulierten Zeitraum gibt es keine Medienreaktion",
            "definition": "Die Reaktion bleibt aus",
        }]},
        [{"platform": "twitter", "post_id": "twitter:1", "agent": "Ada", "text": "Anderes"}],
        seed=1,
        run_number=3,
    )
    assert result["o1"]["yes"] is True
    assert result["o1"]["evidence"][0]["text"] == "kein passender Beitrag in 1 geprüften Beiträgen"


class PairLLM:
    def chat_json(self, messages, **kwargs):
        return {"results": [
            {"outcome_id": "o2", "yes": True, "post_ids": ["twitter:1"]},
            {"outcome_id": "o6", "yes": False, "post_ids": []},
        ]}


def test_absence_uses_verified_counter_outcome_across_checklist(tmp_path):
    """Regression für o6/o2 aus ens_9c4647555d4b."""
    service = EnsembleService(llm_factory=PairLLM, root=tmp_path / "ensembles")
    result = service._classify_posts(
        {"checklist": [
            {
                "id": "o2",
                "text_de": "Im simulierten Zeitraum veröffentlichen Medienberichte eine offizielle Stellungnahme zur Schließung",
                "definition": "Geprüfter Medienbeleg",
                "polarity": "presence",
                "kind": "event",
            },
            {
                "id": "o6",
                "text_de": "Im simulierten Zeitraum reagieren die Medien nicht auf die Bekanntgabe der Schließung",
                "definition": "Keine Medienreaktion",
                "polarity": "absence",
                "kind": "event",
                "presence_event": "Medien reagieren auf die Bekanntgabe der Schließung",
                "counter_outcome_id": "o2",
            },
        ]},
        [{
            "platform": "twitter", "post_id": "twitter:1", "agent_id": 1,
            "agent": "Zeitung", "text": "Wir veröffentlichen die offizielle Stellungnahme zur Schließung.",
        }],
        seed=1,
        run_number=1,
    )
    assert result["o2"]["yes"] is True
    assert result["o6"] == {"yes": False, "evidence": []}


class InteractionLLM:
    def chat_json(self, messages, **kwargs):
        prompt = messages[-1]["content"]
        if "Agentenkatalog" in prompt:
            return {
                "side_a_label": "Stadtpolitik", "side_a_agent_ids": [1],
                "side_b_label": "Elternvertretung", "side_b_agent_ids": [2],
            }
        evidence_id = "reddit:comment:1" if "reddit:comment:1" in prompt else "reddit:2"
        return {"results": [{"outcome_id": "o5", "yes": True, "post_ids": [evidence_id]}]}


def _interaction_run_db(run_dir, with_comment):
    run_dir.mkdir(parents=True)
    (run_dir / "simulation_config.json").write_text(json.dumps({"agent_configs": [
        {"agent_id": 1, "entity_name": "Stadtrat", "entity_type": "Stadtpolitik"},
        {"agent_id": 2, "entity_name": "Elternrat", "entity_type": "Elternvertretung"},
    ]}), encoding="utf-8")
    db = sqlite3.connect(run_dir / "reddit_simulation.db")
    db.execute("CREATE TABLE user (user_id INTEGER, agent_id INTEGER, name TEXT, user_name TEXT)")
    db.executemany("INSERT INTO user VALUES (?, ?, ?, ?)", [
        (10, 1, "Stadtrat", "stadt"), (20, 2, "Elternrat", "eltern"),
    ])
    db.execute("CREATE TABLE post (post_id INTEGER, user_id INTEGER, content TEXT)")
    db.executemany("INSERT INTO post VALUES (?, ?, ?)", [
        (1, 10, "Die Stadtpolitik erläutert ihre Position in der öffentlichen Debatte."),
        (2, 20, "Die Elternvertretung äußert ihre Position in der öffentlichen Debatte."),
    ])
    if with_comment:
        db.execute("CREATE TABLE comment (comment_id INTEGER, post_id INTEGER, user_id INTEGER, content TEXT)")
        db.execute("INSERT INTO comment VALUES (1, 1, 20, 'Wir antworten auf diese Position.')")
    db.commit()
    db.close()


@pytest.mark.parametrize("with_comment, expected", [(False, False), (True, True)])
def test_interaction_requires_structural_cross_group_evidence(tmp_path, with_comment, expected):
    run_dir = tmp_path / ("baseline" if with_comment else "isolated")
    _interaction_run_db(run_dir, with_comment)
    posts = load_simulation_posts(run_dir)
    service = EnsembleService(llm_factory=InteractionLLM, root=tmp_path / "ensembles")
    result = service._classify_posts(
        {"checklist": [{
            "id": "o5",
            "text_de": "Im simulierten Zeitraum findet eine öffentliche Debatte zwischen Stadtpolitik und Elternvertretern statt",
            "definition": "Beide Seiten diskutieren miteinander",
            "polarity": "presence",
            "kind": "interaction",
        }]},
        posts,
        seed=3,
        run_number=1,
        run_dir=run_dir,
    )
    audit = json.loads((run_dir / "classification.json").read_text(encoding="utf-8"))
    assert result["o5"]["yes"] is expected
    assert audit["interaction_groups"]["o5"]["side_a_agent_ids"] == [1]
    assert audit["interaction_checks"]["o5"]["accepted"] is expected
    if not expected:
        assert audit["interaction_checks"]["o5"]["structural_evidence"] == []


def test_aggregate_reports_presence_absence_consistency_warning(tmp_path):
    service = EnsembleService(root=tmp_path / "ensembles")
    state = {
        "variants": [{"key": "baseline"}],
        "checklist": [
            {"id": "o2", "polarity": "presence"},
            {"id": "o6", "polarity": "absence", "counter_outcome_id": "o2"},
        ],
    }
    service._aggregate(state, {"baseline": [{
        "o2": {"yes": True, "evidence": []},
        "o6": {"yes": True, "evidence": []},
    }]})
    assert state["consistency_warnings"] == [{
        "variant": "baseline",
        "run": 1,
        "absence_outcome_id": "o6",
        "presence_outcome_id": "o2",
        "message": "Presence- und Absence-Ergebnis zum selben Akteur wurden im selben Lauf beide mit Ja klassifiziert.",
    }]


def test_unparseable_batch_is_unclassified_not_no(tmp_path):
    service = EnsembleService(
        llm_factory=lambda: BatchLLM(fail=True), root=tmp_path / "ensembles"
    )
    checklist = [{
        "id": "o1", "text_de": "Ereignis", "definition": "sichtbar", "polarity": "presence",
    }]
    classified = service._classify_posts(
        {"checklist": checklist},
        [{"platform": "twitter", "post_id": "twitter:1", "agent": "Ada", "text": "Text"}],
        seed=1,
        run_number=1,
    )
    state = {"variants": [{"key": "baseline"}], "checklist": checklist}
    service._aggregate(state, {"baseline": [classified]})
    outcome = state["results"]["baseline"]["o1"]
    assert outcome["yes"] == 0
    assert outcome["n"] == 0
    assert outcome["unclassified"] == 1


class NeverRunner:
    @classmethod
    def start_simulation(cls, **kwargs):
        raise AssertionError("Reclassify darf keine Simulation starten")


def test_reclassify_uses_stored_database_and_preserves_results_v1(tmp_path):
    root = tmp_path / "ensembles"
    ensemble_id = "ens_aaaaaaaaaaaa"
    run_dir = root / ensemble_id / "baseline" / "run_1"
    run_dir.mkdir(parents=True)
    (run_dir / "simulation_config.json").write_text(
        json.dumps({"event_config": {"initial_posts": []}}), encoding="utf-8"
    )
    db = sqlite3.connect(run_dir / "twitter_simulation.db")
    db.execute("CREATE TABLE user (user_id INTEGER, agent_id INTEGER, name TEXT, user_name TEXT)")
    db.execute("INSERT INTO user VALUES (0, 0, 'Ada', 'ada')")
    db.execute("CREATE TABLE post (post_id INTEGER, user_id INTEGER, content TEXT)")
    db.execute("INSERT INTO post VALUES (1, 0, 'Ein neuer Aufruf wird veröffentlicht.')")
    db.commit()
    db.close()
    checklist = [{
        "id": f"o{i}", "text_de": f"Ergebnis {i}", "definition": "sichtbar",
        "polarity": "presence", "in_material": False, "material_snippet": "",
    } for i in range(1, 6)]
    old_results = {"baseline": {
        item["id"]: {"yes": 0, "n": 1, "rate": 0.0, "ci_low": 0.0, "ci_high": 0.7935,
                      "unclassified": 0, "evidence": []}
        for item in checklist
    }}
    state = {
        "ensemble_id": ensemble_id,
        "simulation_id": "sim_test",
        "question": "Was geschieht?",
        "status": "completed",
        "created_at": "2026-01-01T00:00:00",
        "finished_at": "2026-01-01T01:00:00",
        "runs": 1,
        "hours": 24,
        "start_hour": 7,
        "variants": [{"key": "baseline", "label_de": "Basislauf", "label_en": "Baseline",
                      "status": "completed", "done": 1, "total": 1}],
        "checklist": checklist,
        "results": old_results,
        "comparisons": [],
        "current": None,
        "eta_seconds": 0,
        "error": None,
        "base_seed": 11,
        "cancel_requested": False,
        "current_runner_id": None,
    }
    (root / ensemble_id / "ensemble.json").write_text(json.dumps(state), encoding="utf-8")
    service = EnsembleService(
        runner_cls=NeverRunner, llm_factory=FakeLLM, root=root, poll_interval=0.001
    )
    service.reclassify(ensemble_id)
    deadline = time.time() + 3
    while time.time() < deadline:
        result = service.get(ensemble_id)
        if result["status"] in {"completed", "failed"}:
            break
        time.sleep(0.01)
    assert result["status"] == "completed", result.get("error")
    assert result["results_v1"] == old_results
    assert result["results"]["baseline"]["o1"]["yes"] == 1
    assert (run_dir / "classification.json").is_file()
