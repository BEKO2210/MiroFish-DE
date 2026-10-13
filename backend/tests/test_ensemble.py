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
    build_null_arm_prompt,
    build_post_batches,
    canonical_outcome_rows,
    cohens_kappa,
    combine_rater_results,
    exact_mcnemar_p,
    execution_variant_keys,
    filter_checklist_material_numbers,
    holm_adjust,
    infer_kind,
    load_simulation_posts,
    mark_checklist_material,
    median_character_count,
    newcombe_difference_interval,
    paired_difference_interval,
    paired_outcome_table,
    parse_checklist,
    reliability_label,
    resolve_primary_outcome_id,
    validate_custom_outcomes,
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


def test_cohens_kappa_known_value_and_no_variance_edges():
    metric = cohens_kappa([
        (True, True), (True, True), (True, False), (False, False),
        (False, False), (False, True), (False, False), (True, True),
    ])
    assert metric == {"agreement": 0.75, "kappa": 0.5, "n_pairs": 8}
    assert cohens_kappa([(True, True)] * 4) == {
        "agreement": 1.0, "kappa": 1.0, "n_pairs": 4,
    }
    assert cohens_kappa([]) == {"agreement": 0.0, "kappa": 0.0, "n_pairs": 0}
    assert reliability_label(0.6) == "messbar"
    assert reliability_label(0.4) == "unsicher"
    assert reliability_label(0.3999) == "nicht messbar"


def test_joint_verdict_requires_two_yes_and_disagreement_is_not_no():
    checklist = [{"id": "o1"}, {"id": "o2"}, {"id": "o3"}]
    evidence = [{"post_id": "twitter:1"}]
    result = combine_rater_results(
        {
            "o1": {"yes": True, "evidence": evidence},
            "o2": {"yes": True, "evidence": evidence},
            "o3": {"yes": False, "evidence": []},
        },
        {
            "o1": {"yes": True, "evidence": evidence},
            "o2": {"yes": False, "evidence": []},
            "o3": {"yes": False, "evidence": []},
        },
        checklist,
    )
    assert result["o1"]["yes"] is True
    assert {item["rater"] for item in result["o1"]["evidence"]} == {"a", "b"}
    assert result["o2"]["yes"] is False
    assert result["o2"]["disputed"] is True
    assert result["o3"]["disputed"] is False


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


def test_custom_outcomes_validation_and_normalization():
    custom = validate_custom_outcomes([
        {"text_de": "Wird ein Bürgerbegehren angekündigt?", "polarity": "presence"},
        {"text_de": "Es findet keine Diskussion statt", "kind": "interaction"},
    ])
    assert [item["id"] for item in custom] == ["c1", "c2"]
    assert all(item["source"] == "user" for item in custom)
    assert custom[1]["polarity"] == "absence"
    with pytest.raises(ValueError, match="höchstens 6"):
        validate_custom_outcomes([{"text_de": str(i)} for i in range(7)])
    with pytest.raises(ValueError, match="1 bis 200"):
        validate_custom_outcomes([{"text_de": "x" * 201}])
    with pytest.raises(ValueError, match="polarity"):
        validate_custom_outcomes([{"text_de": "Frage", "polarity": "maybe"}])


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


def test_evidence_requires_id_and_literal_span_in_that_post():
    checklist = [{"id": "o1"}, {"id": "o2"}, {"id": "o3"}]
    posts = [
        {
            "platform": "twitter",
            "post_id": "twitter:7",
            "agent": "Ada",
            "text": "Eine Gruppe startet eine Unterschriftensammlung.",
        },
        {
            "platform": "reddit",
            "post_id": "reddit:3",
            "agent": "Bea",
            "text": "Die Opposition fordert eine Kostenprüfung.",
        },
    ]
    result = verify_classification_evidence(
        {"results": [
            {
                "outcome_id": "o1", "yes": True, "post_ids": ["twitter:7"],
                "snippet": "startet eine Unterschriftensammlung",
            },
            {"outcome_id": "o2", "yes": True, "post_ids": ["reddit:999"],
             "snippet": "Kostenprüfung"},
            {
                "outcome_id": "o3", "yes": True, "post_ids": ["twitter:7"],
                "snippet": "fordert eine Kostenprüfung",
            },
        ]},
        posts,
        checklist,
        2,
    )
    assert result["o1"]["yes"] is True
    assert result["o1"]["evidence"][0]["run"] == 2
    assert result["o1"]["evidence"][0]["span"] == "startet eine unterschriftensammlung"
    assert result["o2"] == {"yes": False, "evidence": []}
    assert result["o3"] == {"yes": False, "evidence": []}


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
            {
                "outcome_id": f"o{i}",
                "yes": i == 1,
                "post_ids": ["twitter:1"],
                "snippet": "Ein neuer Aufruf wird veröffentlicht.",
            }
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


def test_custom_outcomes_are_appended_and_checked_against_material(tmp_path):
    llm = ChecklistRetryLLM()
    service = EnsembleService(llm_factory=lambda: llm, root=tmp_path / "ensembles")
    checklist = service._create_checklist(
        {
            "question": "Was geschieht?", "hours": 2, "base_seed": 41,
            "custom_outcomes": validate_custom_outcomes([
                {"text_de": "Eine Unterschriftensammlung wird angekündigt"}
            ]),
        },
        {
            "extracted_text": "Eine Unterschriftensammlung wird angekündigt.",
            "config": {"event_config": {"initial_posts": []}},
        },
    )
    assert [item["id"] for item in checklist[-1:]] == ["c1"]
    assert checklist[-1]["source"] == "user"
    assert checklist[-1]["in_material"] is True


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
    started = service.start(
        "sim_test", 2, 12, ["baseline"], start_hour=13,
        custom_outcomes=[{"text_de": "Eine eigene Ergebnisfrage wird erfüllt"}],
    )
    deadline = time.time() + 3
    while time.time() < deadline:
        state = service.get(started["ensemble_id"])
        if state["status"] in {"completed", "failed"}:
            break
        time.sleep(0.01)
    assert state["status"] == "completed", state.get("error")
    assert state["variants"][0]["done"] == 2
    assert state["primary_outcome_id"] == "c1"
    assert state["results"]["baseline"]["o1"]["yes"] == 2
    assert state["results"]["baseline"]["o1"]["n"] == 2
    assert state["checklist"][-1]["id"] == "c1"
    assert state["checklist"][-1]["source"] == "user"
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
            "snippet": "Ereignis" if self.positive else "",
        }]}


class NamedBatchLLM(BatchLLM):
    def __init__(self, model, **kwargs):
        super().__init__(**kwargs)
        self.model = model


def test_unreachable_second_model_falls_back_to_main_model_with_other_seed(tmp_path):
    main = NamedBatchLLM("main", positive=True)
    broken = NamedBatchLLM("second", fail=True)

    def factory(**kwargs):
        return broken if kwargs.get("model") else main

    run_dir = tmp_path / "run"
    service = EnsembleService(llm_factory=factory, root=tmp_path / "ensembles")
    result = service._classify_posts(
        {"checklist": [{
            "id": "o1", "text_de": "Ereignis", "definition": "sichtbar",
            "polarity": "presence",
        }]},
        [{"platform": "twitter", "post_id": "twitter:1", "agent": "Ada", "text": "Ereignis"}],
        seed=9,
        run_number=1,
        run_dir=run_dir,
    )
    audit = json.loads((run_dir / "classification.json").read_text(encoding="utf-8"))
    assert result["o1"]["yes"] is True
    assert audit["raters"]["a"]["model"] == "main"
    assert audit["raters"]["b"]["model"] == "main"
    assert audit["raters"]["b"]["seed"] != audit["raters"]["a"]["seed"]
    assert audit["raters"]["b"]["seed_fallback"] is True
    assert "nicht erreichbar" in audit["raters"]["b"]["fallback_reason"]


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
    batches_a = audit["raters"]["a"]["batches"]
    batches_b = audit["raters"]["b"]["batches"]
    assert llm.calls == len(batches_a) + len(batches_b)
    assert len(batches_a) > 1
    assert all(
        batch["estimated_input_tokens"] <= audit["raters"]["a"]["token_budget"]
        for batch in batches_a
    )
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
            {
                "outcome_id": "o2", "yes": True, "post_ids": ["twitter:1"],
                "snippet": "offizielle Stellungnahme",
            },
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
    assert result["o6"]["yes"] is False
    assert result["o6"]["disputed"] is False
    assert result["o6"]["evidence"] == []


class InteractionLLM:
    def chat_json(self, messages, **kwargs):
        prompt = messages[-1]["content"]
        if "Agentenkatalog" in prompt:
            return {
                "side_a_label": "Stadtpolitik", "side_a_agent_ids": [1],
                "side_b_label": "Elternvertretung", "side_b_agent_ids": [2],
            }
        if "reddit:comment:1" in prompt:
            return {"results": [{
                "outcome_id": "o5", "yes": True, "post_ids": ["reddit:comment:1"],
                "snippet": "Wir antworten auf diese Position.",
            }]}
        return {"results": [{
            "outcome_id": "o5", "yes": True, "post_ids": ["reddit:2"],
            "snippet": "ihre Position in der öffentlichen Debatte",
        }]}


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


@pytest.mark.parametrize("with_comment", [False, True])
def test_interaction_text_is_the_outcome_and_edges_stay_separate(tmp_path, with_comment):
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
    assert result["o5"]["yes"] is True
    assert bool(result["o5"]["mechanism_edges"]) is with_comment
    rater_a = audit["raters"]["a"]
    assert rater_a["interaction_groups"]["o5"]["side_a_agent_ids"] == [1]
    assert rater_a["interaction_checks"]["o5"]["accepted"] is True
    assert bool(rater_a["interaction_checks"]["o5"]["mechanism_edges"]) is with_comment


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


def test_aggregate_excludes_disputes_and_flags_unreliable_comparison(tmp_path):
    service = EnsembleService(root=tmp_path / "ensembles")
    state = {
        "variants": [{"key": "baseline"}, {"key": "isolated"}],
        "checklist": [{"id": "o1"}],
    }
    agreed_yes = {
        "yes": True, "evidence": [], "disputed": False,
        "raters": {
            "a": {"yes": True, "evidence": []},
            "b": {"yes": True, "evidence": []},
        },
    }
    disputed = {
        "yes": False, "evidence": [], "disputed": True,
        "raters": {
            "a": {"yes": True, "evidence": []},
            "b": {"yes": False, "evidence": []},
        },
    }
    service._aggregate(state, {
        "baseline": [{"o1": agreed_yes}],
        "isolated": [{"o1": disputed}],
    })
    assert state["results"]["isolated"]["o1"]["disputed"] == 1
    assert state["results"]["isolated"]["o1"]["n"] == 0
    assert state["reliability"]["o1"]["n_pairs"] == 2
    assert state["reliability"]["o1"]["label"] == "nicht messbar"
    assert state["comparisons"][0]["unreliable"] is True


def test_failed_batch_retries_twice_then_stays_in_n(tmp_path):
    llm = BatchLLM(fail=True)
    service = EnsembleService(llm_factory=lambda: llm, root=tmp_path / "ensembles")
    checklist = [{
        "id": "o1", "text_de": "Ereignis", "definition": "sichtbar", "polarity": "presence",
    }]
    run_dir = tmp_path / "run"
    classified = service._classify_posts(
        {"checklist": checklist},
        [{"platform": "twitter", "post_id": "twitter:1", "agent": "Ada", "text": "Text"}],
        seed=1,
        run_number=1,
        run_dir=run_dir,
    )
    audit = json.loads((run_dir / "classification.json").read_text(encoding="utf-8"))
    assert audit["raters"]["a"]["batches"][0]["attempts"] == 3
    assert "error" in audit["raters"]["a"]["batches"][0]
    assert llm.calls == 6
    state = {"variants": [{"key": "baseline"}], "checklist": checklist}
    service._aggregate(state, {"baseline": [classified]})
    outcome = state["results"]["baseline"]["o1"]
    assert classified["o1"]["unclassified"] is False
    assert outcome["yes"] == 0
    assert outcome["n"] == 1
    assert outcome["unclassified"] == 0


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


def test_positive_event_ignores_negated_definition():
    """Regression ens_9c4647555d4b/o6: die Definition beschreibt das Ausbleiben und darf nicht mitgeschickt werden."""
    from app.services.ensemble import _positive_event_text
    item = {
        "id": "o6",
        "text_de": "Im simulierten Zeitraum reagieren die Medien nicht auf die Bekanntgabe der Schließung.",
        "definition": "Bleibt die Bekanntgabe der Schließung in den relevanten Medienkanälen ohne jegliche "
                      "Berichterstattung oder Kommentar unbedient?",
        "polarity": "absence",
    }
    text = _positive_event_text(item)
    assert "nicht" not in text and "ohne" not in text and "unbedient" not in text
    assert "reagieren die Medien" in text


def test_exact_mcnemar_matches_known_discordant_pairs():
    assert exact_mcnemar_p(0, 5) == pytest.approx(0.0625)
    assert exact_mcnemar_p(1, 6) == pytest.approx(0.125)
    assert exact_mcnemar_p(7, 0) == pytest.approx(0.015625)
    assert exact_mcnemar_p(3, 3) == 1.0
    assert exact_mcnemar_p(0, 0) == 1.0


def test_paired_wald_interval_known_value():
    low, high = paired_difference_interval(1, 6, 10)
    assert (6 - 1) / 10 == pytest.approx(0.5)
    # Z_95 = 1,959963984540054, SE = sqrt(4,5) / 10.
    assert low == pytest.approx(0.0842288527, abs=1e-9)
    assert high == pytest.approx(0.9157711473, abs=1e-9)
    assert paired_difference_interval(0, 0, 0) == (0.0, 0.0)


def test_holm_known_stepdown():
    # Sortiert 0,01 / 0,03 / 0,04; Faktoren 3, 2, 1; dann monoton.
    assert holm_adjust([0.04, 0.01, 0.03]) == pytest.approx([0.06, 0.03, 0.06])
    assert holm_adjust([0.2]) == pytest.approx([0.2])
    assert holm_adjust([]) == []


def test_pairs_follow_run_index_not_pooled_margins():
    baseline = [
        {"o1": {"yes": True}},
        {"o1": {"yes": False}},
        {"o1": {"yes": True, "unclassified": True}},
    ]
    variant = [
        {"o1": {"yes": False, "unclassified": True}},
        {"o1": {"yes": True}},
        {"o1": {"yes": False}},
    ]
    table = paired_outcome_table(baseline, variant, "o1")
    assert table == {
        "both_yes": 0,
        "baseline_only": 0,
        "variant_only": 1,
        "both_no": 0,
        "n_pairs": 1,
        "unpaired": 2,
    }


def test_aggregate_stores_paired_table_holm_and_collapses_counterparts(tmp_path):
    service = EnsembleService(root=tmp_path / "ensembles")

    def flag(yes):
        return {"yes": yes, "evidence": []}

    baseline = []
    variant = []
    for index in range(7):
        baseline.append({"o1": flag(False), "o2": flag(False), "o3": flag(False), "o6": flag(True)})
        variant.append({
            "o1": flag(index == 0),
            "o2": flag(index < 5),
            "o3": flag(True),
            "o6": flag(False),
        })
    state = {
        "variants": [{"key": "baseline"}, {"key": "isolated"}, {"key": "null_document"}],
        "primary_outcome_id": "o1",
        "checklist": [
            {"id": "o1", "source": "auto", "polarity": "presence", "text_de": "Eltern"},
            {"id": "o2", "source": "auto", "polarity": "presence", "text_de": "Stellungnahme"},
            {"id": "o3", "source": "auto", "polarity": "presence", "text_de": "Kosten"},
            {
                "id": "o6", "source": "auto", "polarity": "absence", "text_de": "Medien nicht",
                "counter_outcome_id": "o2",
            },
        ],
    }
    service._aggregate(state, {
        "baseline": baseline,
        "isolated": variant,
        "null_document": variant,
    })
    by_outcome = {}
    for comparison in state["comparisons"]:
        if comparison["variant"] == "isolated":
            by_outcome[comparison["outcome_id"]] = comparison
    assert set(by_outcome) == {"o1", "o2", "o3"}
    assert "o6" not in {item["outcome_id"] for item in state["comparisons"]}
    assert by_outcome["o2"]["collapsed_outcome_ids"] == ["o6"]
    assert state["checklist"][3]["collapsed_into"] == "o2"
    assert by_outcome["o2"]["table"]["variant_only"] == 5
    assert by_outcome["o2"]["table"]["baseline_only"] == 0
    assert by_outcome["o2"]["table"]["n_pairs"] == 7
    assert by_outcome["o3"]["mcnemar_p"] == pytest.approx(0.015625)
    assert by_outcome["o2"]["mcnemar_p"] == pytest.approx(0.0625)
    assert by_outcome["o1"]["role"] == "confirmatory"
    assert by_outcome["o1"]["holm_p"] is None
    assert by_outcome["o2"]["role"] == "exploratory"
    assert by_outcome["o3"]["role"] == "exploratory"
    # Familie: o2 und o3 mal zwei Varianten. Die zwei p=0,015625 werden mit Faktor 4
    # zu 0,0625; die zwei p=0,0625 danach monoton auf 0,125.
    assert by_outcome["o3"]["holm_p"] == pytest.approx(0.0625)
    assert by_outcome["o2"]["holm_p"] == pytest.approx(0.125)
    assert state["analysis"]["exploratory_m"] == 4
    assert "newcombe" in by_outcome["o1"]
    assert canonical_outcome_rows(state["checklist"])[1]["collapsed_outcome_ids"] == ["o6"]


def test_primary_outcome_defaults_to_first_user_then_first_auto():
    checklist = [
        {"id": "o1", "source": "auto"},
        {"id": "c1", "source": "user"},
        {"id": "c2", "source": "user"},
    ]
    assert resolve_primary_outcome_id(checklist, None) == "c1"
    assert resolve_primary_outcome_id(checklist, "o1") == "o1"
    assert resolve_primary_outcome_id(
        [{"id": "o1", "source": "auto"}, {"id": "o2", "source": "auto"}], None
    ) == "o1"
    with pytest.raises(ValueError, match="nicht in der Checkliste"):
        resolve_primary_outcome_id(checklist, "o9")


def test_null_personas_prompt_contains_personas_posts_groups_and_length():
    personas = [{
        "name": "Ada",
        "group": "Eltern",
        "persona": "Ada setzt sich für das Hallenbad ein.",
    }]
    posts = ["Die Stadt erhöht die Gebühr."]
    prompt = build_null_arm_prompt(
        "null_personas",
        document="Das Hallenbad soll schließen.",
        question="Was geschieht?",
        hours=24,
        personas=personas,
        initial_posts=posts,
        target_characters=1200,
    )
    assert "Ada setzt sich für das Hallenbad ein." in prompt
    assert "Eltern" in prompt
    assert "Die Stadt erhöht die Gebühr." in prompt
    assert "1200" in prompt
    assert "Akteursgruppen" in prompt
    document = build_null_arm_prompt(
        "null_document",
        document="Das Hallenbad soll schließen.",
        question="Was geschieht?",
        hours=24,
        personas=personas,
        initial_posts=posts,
        target_characters=1200,
    )
    assert "Ada setzt sich" not in document
    assert "Gebühr" not in document
    alias = build_null_arm_prompt(
        "null_model",
        document="Das Hallenbad soll schließen.",
        question="Was geschieht?",
        hours=24,
    )
    assert alias == document
    assert execution_variant_keys(
        ["null_personas", "isolated", "baseline"]
    ) == ["isolated", "baseline", "null_personas"]
    assert median_character_count([100, 400]) == 250
    assert median_character_count([100, 300, 200]) == 200


def test_null_personas_narrative_prompt_uses_context_personas(tmp_path):
    captured = {}

    class CaptureLLM:
        def chat(self, messages, **kwargs):
            captured["content"] = messages[-1]["content"]
            captured["max_tokens"] = kwargs["max_tokens"]
            return "Erzählung mit Eltern."

        def chat_json(self, messages, **kwargs):
            return {"results": []}

    service = EnsembleService(llm_factory=lambda: CaptureLLM(), root=tmp_path / "ensembles")
    service._null_narrative(
        {"question": "Was geschieht?", "hours": 24},
        {
            "extracted_text": "Dokument über das Bad.",
            "config": {
                "agent_configs": [{
                    "agent_id": 0,
                    "entity_name": "Ada",
                    "entity_type": "Eltern",
                    "persona": "Ada setzt sich für das Hallenbad ein.",
                }],
                "event_config": {"initial_posts": [{
                    "poster_agent_id": 0,
                    "content": "Startbeitrag der Eltern.",
                }]},
            },
        },
        seed=3,
        arm="null_personas",
        target_characters=900,
    )
    assert "Ada setzt sich für das Hallenbad ein." in captured["content"]
    assert "Startbeitrag der Eltern." in captured["content"]
    assert "Eltern" in captured["content"]
    assert captured["max_tokens"] == 300


class SpanMissLLM:
    def chat_json(self, messages, **kwargs):
        prompt = messages[-1]["content"]
        if "Agentenkatalog" in prompt:
            return {
                "side_a_label": "Stadtpolitik", "side_a_agent_ids": [1],
                "side_b_label": "Elternvertretung", "side_b_agent_ids": [2],
            }
        return {"results": [{
            "outcome_id": "o5", "yes": True, "post_ids": ["reddit:comment:1"],
            "snippet": "diese Spanne steht nicht im Beitrag",
        }]}


def test_db_edge_does_not_turn_a_missing_span_into_yes(tmp_path):
    run_dir = tmp_path / "baseline"
    _interaction_run_db(run_dir, True)
    posts = load_simulation_posts(run_dir)
    service = EnsembleService(llm_factory=SpanMissLLM, root=tmp_path / "ensembles")
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
    assert result["o5"]["yes"] is False
    assert result["o5"]["mechanism_edges"]


class NarrativeLLM:
    def chat_json(self, messages, **kwargs):
        return {"results": [{
            "outcome_id": "o1",
            "yes": True,
            "snippet": "Eltern antworten dem Stadtrat",
        }]}


def test_null_interaction_is_coded_from_text(tmp_path):
    service = EnsembleService(llm_factory=NarrativeLLM, root=tmp_path / "ensembles")
    result = service._classify_narrative(
        {"checklist": [{
            "id": "o1",
            "text_de": "Eine Debatte zwischen Eltern und Stadtrat findet statt",
            "definition": "direkte Antwort",
            "polarity": "presence",
            "kind": "interaction",
        }]},
        "Die Eltern antworten dem Stadtrat noch am selben Tag.",
        seed=2,
        run_number=1,
        variant_key="null_personas",
    )
    assert result["o1"]["yes"] is True
    assert result["o1"]["mechanism_edges"] == []
    assert result["o1"]["evidence"][0]["platform"] == "null_personas"


class RetryThenYes:
    def __init__(self):
        self.failures_left = 2
        self.calls = 0

    def chat_json(self, messages, **kwargs):
        self.calls += 1
        if self.failures_left:
            self.failures_left -= 1
            raise ValueError("Stapel unparsebar")
        return {"results": [{
            "outcome_id": "o1",
            "yes": True,
            "post_ids": ["twitter:1"],
            "snippet": "Unterschriftensammlung",
        }]}


def test_batch_succeeds_on_third_attempt(tmp_path):
    llm = RetryThenYes()
    service = EnsembleService(llm_factory=lambda: llm, root=tmp_path / "ensembles")
    run_dir = tmp_path / "run"
    result = service._classify_posts(
        {"checklist": [{
            "id": "o1", "text_de": "Sammlung", "definition": "sichtbar",
            "polarity": "presence", "kind": "event",
        }]},
        [{
            "platform": "twitter", "post_id": "twitter:1", "agent": "Ada",
            "text": "Wir starten eine Unterschriftensammlung.",
        }],
        seed=4,
        run_number=1,
        run_dir=run_dir,
    )
    audit = json.loads((run_dir / "classification.json").read_text(encoding="utf-8"))
    assert audit["raters"]["a"]["batches"][0]["attempts"] == 3
    assert "error" not in audit["raters"]["a"]["batches"][0]
    assert result["o1"]["yes"] is True
    assert llm.calls == 4
