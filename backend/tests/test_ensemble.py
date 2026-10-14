"""V3/V4: Statistik, Checkliste, Belege, Varianten und Zustandsmaschine."""

import csv
import json
import os
import sqlite3
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
import app.utils.llm_client as llm_module
from app.services import ensemble as ensemble_module

from app.config import Config
from app.services.blind_feed import (
    deliver_opening_stimulus,
    install_blind_feed,
    is_blind_feed,
    own_post_rows,
)
from app.services.ensemble import (
    ALLOWED_MINUTES_PER_ROUND,
    EnsembleService,
    apply_without_variant,
    build_null_arm_prompt,
    build_null_run_manifest,
    build_post_batches,
    canonical_outcome_rows,
    SEED_ATTEMPTS,
    cohens_kappa,
    combine_rater_results,
    compute_run_stats,
    ensemble_markdown,
    exact_mcnemar_p,
    execution_variant_keys,
    filter_checklist_material_numbers,
    holm_adjust,
    infer_kind,
    load_simulation_posts,
    mark_checklist_material,
    measure_blind_feed_usage,
    median_character_count,
    newcombe_difference_interval,
    paired_difference_interval,
    paired_outcome_table,
    parse_checklist,
    prepare_run_directory,
    reliability_label,
    resolve_primary_outcome_id,
    validate_custom_outcomes,
    validate_variants,
    verified_material_quote,
    verify_classification_evidence,
    wilson_interval,
)
from app.services.report_validation import build_manifest
from app.utils.llm_client import LLMClient, estimate_tokens
from app.utils.simulation_time import (
    hours_covered_by_round,
    peak_multiplier_for_hours,
    simulation_clock,
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


def test_cohens_kappa_known_value_and_no_variance_edges():
    metric = cohens_kappa([
        (True, True), (True, True), (True, False), (False, False),
        (False, False), (False, True), (False, False), (True, True),
    ])
    assert metric == {"agreement": 0.75, "kappa": 0.5, "n_pairs": 8}
    assert cohens_kappa([(True, True)] * 4) == {
        "agreement": 1.0, "kappa": None, "n_pairs": 4,
    }
    assert cohens_kappa([(False, False)] * 3)["kappa"] is None
    assert cohens_kappa([]) == {"agreement": None, "kappa": None, "n_pairs": 0}
    assert reliability_label(0.6) == "messbar"
    assert reliability_label(0.4) == "unsicher"
    assert reliability_label(0.3999) == "nicht messbar"
    assert reliability_label(None) == "nicht messbar"


def test_empty_rater_pairs_stay_undefined_in_the_report(tmp_path):
    service = EnsembleService(root=tmp_path / "ensembles")
    state = {
        "runs": 1,
        "hours": 2,
        "status": "completed",
        "variants": [{"key": "baseline", "label_de": "Basislauf"}],
        "checklist": [{"id": "o1", "text_de": "Ereignis", "polarity": "presence"}],
    }
    service._aggregate(state, {"baseline": [{
        "o1": {"yes": False, "unclassified": False, "disputed": False},
    }]})
    metric = state["reliability"]["o1"]
    assert metric == {
        "agreement": None, "kappa": None, "n_pairs": 0, "label": "nicht messbar",
    }
    report = ensemble_markdown(state)
    assert "| Ereignis | – | – | 0 | nicht messbar |" in report


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
    assert custom[1]["polarity"] == "presence"
    assert validate_custom_outcomes(
        [{"text_de": "Die Stadt kann die Zahl nicht beziffern", "polarity": "absence"}]
    )[0]["polarity"] == "absence"
    assert validate_custom_outcomes(
        [{"text_de": "Die Stadt kann die Zahl nicht beziffern"}]
    )[0]["polarity"] == "presence"
    with pytest.raises(ValueError, match="höchstens 20"):
        validate_custom_outcomes([{"text_de": str(i)} for i in range(21)])
    with pytest.raises(ValueError, match="1 bis 200"):
        validate_custom_outcomes([{"text_de": "x" * 201}])
    with pytest.raises(ValueError, match="polarity"):
        validate_custom_outcomes([{"text_de": "Frage", "polarity": "maybe"}])


def test_checklist_polarity_is_explicit_or_inferred():
    parsed = parse_checklist({"outcomes": [
        {"text_de": "Im Zeitraum geschieht etwas", "definition": "sichtbar", "polarity": "presence"},
        {"text_de": "Im Zeitraum gibt es keine Reaktion", "definition": "bleibt aus"},
        {"text_de": "Ausdrückliche Abwesenheit", "definition": "sichtbar", "polarity": "absence"},
    ] + [
        {"text_de": f"Weiteres Ergebnis {i}", "definition": "sichtbar"}
        for i in range(3)
    ]})
    assert parsed[0]["polarity"] == "presence"
    assert parsed[1]["polarity"] == "presence"
    assert parsed[2]["polarity"] == "absence"


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


def test_post_batches_leave_requested_followup_reserve():
    posts = [
        {"post_id": f"twitter:{i}", "agent": "Ada", "text": "x" * 180}
        for i in range(8)
    ]
    prefix = "Anweisung und Checkliste\nBeiträge:\n"
    batches = build_post_batches(posts, prefix, 240, reserve_tokens=40)
    assert len(batches) > 1
    assert all(
        estimate_tokens(prefix + "\n".join(
            f"[{post['post_id']}] {post['agent']}: {post['text']}" for post in batch
        )) <= 200
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


def test_hours_covered_by_round_spans_multi_hour_takt():
    assert hours_covered_by_round(0, 60, 7) == [7]
    assert hours_covered_by_round(0, 240, 7) == [7, 8, 9, 10]
    assert hours_covered_by_round(0, 240, 22) == [22, 23, 0, 1]
    # 14 Tage à 4-h-Runden → 84 Runden
    assert 14 * 24 * 60 // 240 == 84
    assert peak_multiplier_for_hours(
        [7, 8, 9, 10], [9, 10], [0, 1, 2], 1.5, 0.3
    ) == 1.5


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
    assert result["o2"] == {
        "yes": False, "evidence": [], "evidence_rejected": True,
    }
    assert result["o3"] == {
        "yes": False, "evidence": [], "evidence_rejected": True,
    }


def test_evidence_audit_distinguishes_explicit_no_from_rejected_yes():
    posts = [{
        "platform": "twitter", "post_id": "twitter:1", "agent": "Ada",
        "text": "Ein anderer Vorgang.",
    }]
    result = verify_classification_evidence(
        {"results": [
            {"outcome_id": "o1", "yes": "nein"},
            {"outcome_id": "o2", "yes": "ja", "post_ids": ["twitter:1"],
             "snippet": "nicht vorhanden"},
        ]},
        posts,
        [{"id": "o1"}, {"id": "o2"}],
        1,
    )
    assert result["o1"] == {"yes": False, "evidence": []}
    assert result["o2"]["evidence_rejected"] is True


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


def test_minutes_per_round_validation_happens_before_start(tmp_path):
    service = EnsembleService(root=tmp_path / "ensembles")
    for value in (30, 90, 0, True, "60", 180):
        with pytest.raises(ValueError, match="minutes_per_round"):
            service.start("sim_test", 1, 2, ["baseline"], minutes_per_round=value)
    assert ALLOWED_MINUTES_PER_ROUND == frozenset({60, 120, 240})


def test_prepare_run_directory_overrides_minutes_per_round(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "simulation_config.json").write_text(
        json.dumps({
            "time_config": {
                "total_simulation_hours": 48,
                "minutes_per_round": 60,
                "start_hour": 7,
            },
            "agent_configs": [],
        }),
        encoding="utf-8",
    )
    (source / "reddit_profiles.json").write_text("[]", encoding="utf-8")
    with (source / "twitter_profiles.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["user_id", "name"])
        writer.writeheader()
    run_dir = tmp_path / "run_1"
    config = prepare_run_directory(
        source, run_dir, "baseline", hours=336, start_hour=9, minutes_per_round=240
    )
    assert config["time_config"]["minutes_per_round"] == 240
    assert config["time_config"]["total_simulation_hours"] == 336
    assert config["time_config"]["start_hour"] == 9
    assert 336 * 60 // 240 == 84
    written = json.loads((run_dir / "simulation_config.json").read_text(encoding="utf-8"))
    assert written["time_config"]["minutes_per_round"] == 240


def test_manifest_records_minutes_per_round(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(tmp_path))
    sim = tmp_path / "ensembles" / "ens_x" / "baseline" / "run_1"
    sim.mkdir(parents=True)
    (sim / "simulation_config.json").write_text(
        json.dumps({
            "simulation_id": "run_1",
            "simulation_requirement": "Frage?",
            "time_config": {"minutes_per_round": 120, "total_simulation_hours": 24},
            "event_config": {"initial_posts": []},
        }),
        encoding="utf-8",
    )
    (sim / "state.json").write_text(
        json.dumps({"project_id": "proj_x", "simulation_requirement": "Frage?"}),
        encoding="utf-8",
    )
    (sim / "reddit_profiles.json").write_text("[]", encoding="utf-8")
    with (sim / "twitter_profiles.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["user_id", "name"])
        writer.writeheader()
    project = tmp_path / "projects" / "proj_x"
    project.mkdir(parents=True)
    (project / "extracted_text.txt").write_text("x", encoding="utf-8")
    manifest = build_manifest(str(sim), seed=1, temperature=0.7)
    assert manifest["minutes_per_round"] == 120


def test_ensemble_accepts_two_weeks_and_rejects_longer_horizon(tmp_path):
    service = EnsembleService(root=tmp_path / "ensembles")
    # 336 besteht die Zeitvalidierung und scheitert erst an der fehlenden Vorbereitung.
    with pytest.raises(FileNotFoundError):
        service.start("sim_test", 1, 336, ["baseline"])
    with pytest.raises(ValueError, match="336"):
        service.start("sim_test", 1, 337, ["baseline"])


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
        "sim_test", 2, 12, ["baseline"], start_hour=13, minutes_per_round=120,
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
    assert state["minutes_per_round"] == 120
    assert 12 * 60 // state["minutes_per_round"] == 6
    first_config = json.loads(
        (tmp_path / "ensembles" / started["ensemble_id"] / "baseline" / "run_1" /
         "simulation_config.json").read_text(encoding="utf-8")
    )
    assert first_config["time_config"]["start_hour"] == 13
    assert first_config["time_config"]["minutes_per_round"] == 120
    md = ensemble_markdown(state)
    assert "Rundentakt 120 Minuten" in md


class FlakyRunner:
    calls = []
    states = {}

    @classmethod
    def start_simulation(cls, simulation_id, simulation_dir, **kwargs):
        cls.calls.append(simulation_id)
        if len(cls.calls) == 1:
            state = SimpleNamespace(runner_status="failed", current_round=0, error="gpu ausgefallen")
            cls.states[simulation_id] = state
            return state
        return FakeRunner.start_simulation(simulation_id, simulation_dir, **kwargs)

    @classmethod
    def get_run_state(cls, simulation_id):
        if simulation_id in FakeRunner.states:
            return FakeRunner.states[simulation_id]
        return cls.states[simulation_id]


def _wait_ensemble(service, ensemble_id):
    deadline = time.time() + 3
    state = service.get(ensemble_id)
    while time.time() < deadline:
        state = service.get(ensemble_id)
        if state["status"] in {"completed", "failed"}:
            break
        time.sleep(0.01)
    return state


def test_failed_seed_is_retried_and_kept_in_n(tmp_path, monkeypatch):
    FlakyRunner.calls, FlakyRunner.states = [], {}
    FakeRunner.states = {}
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(tmp_path))
    _prepared_simulation(tmp_path)
    service = EnsembleService(
        runner_cls=FlakyRunner, llm_factory=FakeLLM,
        root=tmp_path / "ensembles", poll_interval=0.001,
    )
    started = service.start("sim_test", 1, 2, ["baseline"])
    state = _wait_ensemble(service, started["ensemble_id"])
    assert state["status"] == "completed", state.get("error")
    assert len(FlakyRunner.calls) == 2
    assert state["results"]["baseline"]["o1"]["n"] == 1
    stored = service._load(started["ensemble_id"])
    assert stored["seed_attempts"]["baseline:1"] == 2
    baseline = tmp_path / "ensembles" / started["ensemble_id"] / "baseline"
    archived = [path for path in baseline.iterdir() if ".failed-" in path.name]
    assert len(archived) == 1
    assert archived[0].name.startswith("run_1.failed-1-")
    assert (archived[0] / "simulation_config.json").is_file()
    assert (baseline / "run_1" / "classification.json").is_file()
    failure = stored["seed_failures"]["baseline:1"][0]
    assert failure["path"] == str(archived[0])
    assert "gpu ausgefallen" in failure["error"]
    assert failure["at"]
    (archived[0] / "classification.json").write_text(json.dumps({
        "result": {"o1": {"yes": True, "unclassified": False}},
    }), encoding="utf-8")
    assert service._completed_seed_result(archived[0], stored, "baseline") is None


def test_exhausted_seed_refuses_further_resume(tmp_path, monkeypatch):
    class DyingRunner:
        calls = []

        @classmethod
        def start_simulation(cls, simulation_id, simulation_dir, **kwargs):
            cls.calls.append(simulation_id)
            raise RuntimeError("gpu tot")

        @classmethod
        def get_run_state(cls, simulation_id):
            raise AssertionError(simulation_id)

        @classmethod
        def stop_simulation(cls, simulation_id):
            return None

    DyingRunner.calls = []
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(tmp_path))
    _prepared_simulation(tmp_path)
    service = EnsembleService(
        runner_cls=DyingRunner, llm_factory=FakeLLM,
        root=tmp_path / "ensembles", poll_interval=0.001,
    )
    started = service.start("sim_test", 1, 2, ["baseline"])
    state = _wait_ensemble(service, started["ensemble_id"])
    assert state["status"] == "failed", state.get("error")
    assert state["attempts_exhausted"] is True
    stored = service._load(started["ensemble_id"])
    assert stored["seed_attempts"]["baseline:1"] == SEED_ATTEMPTS
    assert len(DyingRunner.calls) == SEED_ATTEMPTS
    archived = list(
        (tmp_path / "ensembles" / started["ensemble_id"] / "baseline").glob("run_1.failed-*")
    )
    assert len(archived) == SEED_ATTEMPTS
    with pytest.raises(RuntimeError, match="Versuche erschöpft"):
        service.resume(started["ensemble_id"])
    assert len(DyingRunner.calls) == SEED_ATTEMPTS
    assert service._load(started["ensemble_id"])["seed_attempts"]["baseline:1"] == SEED_ATTEMPTS
    assert len(list(
        (tmp_path / "ensembles" / started["ensemble_id"] / "baseline").glob("run_1.failed-*")
    )) == SEED_ATTEMPTS


def test_resume_continues_incomplete_ensemble(tmp_path, monkeypatch):
    FakeRunner.states = {}
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(tmp_path))
    _prepared_simulation(tmp_path)
    ensemble_id = "ens_bbbbbbbbbbbb"
    root = tmp_path / "ensembles" / ensemble_id
    run_dir = root / "baseline" / "run_1"
    run_dir.mkdir(parents=True)
    checklist = [{
        "id": f"o{i}", "text_de": f"Ergebnis {i}", "definition": "sichtbar",
        "polarity": "presence", "source": "auto",
    } for i in range(1, 6)]
    result = {
        f"o{i}": {
            "yes": i == 1, "evidence": [], "unclassified": False, "disputed": False,
            "raters": {"a": {"yes": i == 1}, "b": {"yes": i == 1}},
        }
        for i in range(1, 6)
    }
    (run_dir / "classification.json").write_text(
        json.dumps({"result": result}), encoding="utf-8"
    )
    state = {
        "ensemble_id": ensemble_id, "simulation_id": "sim_test", "question": "Was geschieht?",
        "status": "failed", "error": "Seed abgestürzt", "created_at": "2026-01-01T00:00:00",
        "finished_at": "2026-01-01T01:00:00", "runs": 2, "hours": 12, "start_hour": 7,
        "variants": [{"key": "baseline", "label_de": "Basislauf", "label_en": "Baseline",
                      "status": "failed", "done": 1, "total": 2}],
        "checklist": checklist, "custom_outcomes": [], "primary_outcome_id": "o1",
        "results": {}, "comparisons": [], "reliability": {}, "consistency_warnings": [],
        "current": None, "eta_seconds": None, "base_seed": 11, "cancel_requested": False,
        "current_runner_id": None, "seed_attempts": {"baseline:1": 1},
    }
    (root / "ensemble.json").write_text(json.dumps(state), encoding="utf-8")
    calls = []

    class RecordingRunner(FakeRunner):
        @classmethod
        def start_simulation(cls, simulation_id, simulation_dir, **kwargs):
            calls.append(simulation_id)
            return super().start_simulation(simulation_id, simulation_dir, **kwargs)

    service = EnsembleService(
        runner_cls=RecordingRunner, llm_factory=FakeLLM, root=tmp_path / "ensembles",
        poll_interval=0.001,
    )
    service.resume(ensemble_id)
    finished = _wait_ensemble(service, ensemble_id)
    assert finished["status"] == "completed", finished.get("error")
    # Ein altes Resultat ohne Laufbeiträge ist nach der Qualitätsprüfung nicht vollständig.
    assert calls == [f"{ensemble_id}_baseline_1", f"{ensemble_id}_baseline_2"]
    assert finished["variants"][0]["done"] == 2
    assert finished["results"]["baseline"]["o1"]["n"] == 2
    assert finished["results"]["baseline"]["o1"]["yes"] == 2
    assert SEED_ATTEMPTS == 3


def test_resume_records_run_stats_and_minutes_per_round(tmp_path, monkeypatch):
    FakeRunner.states = {}
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(tmp_path))
    _prepared_simulation(tmp_path)
    ensemble_id = "ens_cccccccccccc"
    root = tmp_path / "ensembles" / ensemble_id
    run_dir = root / "baseline" / "run_1"
    run_dir.mkdir(parents=True)
    stored_text = "Gespeicherter Beitrag des ersten Seeds."
    db = sqlite3.connect(run_dir / "twitter_simulation.db")
    db.execute(
        "CREATE TABLE user (user_id INTEGER, agent_id INTEGER, name TEXT, user_name TEXT)"
    )
    db.execute("INSERT INTO user VALUES (0, 0, 'Ada', 'ada')")
    db.execute("CREATE TABLE post (post_id INTEGER, user_id INTEGER, content TEXT)")
    db.execute("INSERT INTO post VALUES (1, 0, ?)", (stored_text,))
    db.commit()
    db.close()
    actions = run_dir / "twitter" / "actions.jsonl"
    actions.parent.mkdir(parents=True, exist_ok=True)
    actions.write_text(
        json.dumps({"action_type": "create_post", "success": True}) + "\n",
        encoding="utf-8",
    )
    checklist = [{
        "id": f"o{i}", "text_de": f"Ergebnis {i}", "definition": "sichtbar",
        "polarity": "presence", "source": "auto",
    } for i in range(1, 6)]
    result = {
        f"o{i}": {
            "yes": i == 1, "evidence": [], "unclassified": False, "disputed": False,
            "raters": {"a": {"yes": i == 1}, "b": {"yes": i == 1}},
        }
        for i in range(1, 6)
    }
    (run_dir / "classification.json").write_text(json.dumps({
        "result": result,
        "raters": {"a": {"batches": [{}]}},
    }), encoding="utf-8")
    state = {
        "ensemble_id": ensemble_id, "simulation_id": "sim_test", "question": "Was geschieht?",
        "status": "failed", "error": "Seed abgestürzt", "created_at": "2026-01-01T00:00:00",
        "finished_at": "2026-01-01T01:00:00", "runs": 2, "hours": 12, "start_hour": 7,
        "minutes_per_round": 240,
        "variants": [{"key": "baseline", "label_de": "Basislauf", "label_en": "Baseline",
                      "status": "failed", "done": 1, "total": 2}],
        "checklist": checklist, "custom_outcomes": [], "primary_outcome_id": "o1",
        "results": {}, "comparisons": [], "reliability": {}, "consistency_warnings": [],
        "current": None, "eta_seconds": None, "base_seed": 11, "cancel_requested": False,
        "current_runner_id": None, "seed_attempts": {"baseline:1": 1},
    }
    (root / "ensemble.json").write_text(json.dumps(state), encoding="utf-8")
    calls = []

    class RecordingRunner(FakeRunner):
        @classmethod
        def start_simulation(cls, simulation_id, simulation_dir, **kwargs):
            calls.append(simulation_id)
            return super().start_simulation(simulation_id, simulation_dir, **kwargs)

    service = EnsembleService(
        runner_cls=RecordingRunner, llm_factory=FakeLLM, root=tmp_path / "ensembles",
        poll_interval=0.001,
    )
    service.resume(ensemble_id)
    finished = _wait_ensemble(service, ensemble_id)
    assert finished["status"] == "completed", finished.get("error")
    assert calls == [f"{ensemble_id}_baseline_2"]
    assert finished["minutes_per_round"] == 240
    assert not (run_dir / "simulation_config.json").is_file()
    resumed_posts = load_simulation_posts(run_dir)
    assert resumed_posts[0]["text"] == stored_text
    fresh_config = json.loads(
        (root / "baseline" / "run_2" / "simulation_config.json").read_text(encoding="utf-8")
    )
    assert fresh_config["time_config"]["minutes_per_round"] == 240
    rows = finished["run_stats"]["baseline"]
    assert [row["run"] for row in rows] == [1, 2]
    assert rows[0] == {
        "run": 1,
        "post_count": 1,
        "contribution_count": 1,
        "character_count": len(stored_text),
        "batch_count": 1,
        "agent_action_count": 1,
        "agent_error_count": 0,
        "agent_error_rate": 0.0,
        "action_log_status": "vorhanden",
        "search_action_count": 0,
        "trend_action_count": 0,
        "foreign_interaction_count": 0,
    }
    assert rows[1]["post_count"] == 1
    assert rows[1]["character_count"] == len("Ein neuer Aufruf wird veröffentlicht.")
    assert rows[1]["batch_count"] >= 1
    md = ensemble_markdown(finished)
    assert "Rundentakt 240 Minuten" in md
    assert f"| Basislauf | 1 | 1 | {len(stored_text)} | 1 |" in md


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


class MissingIdLLM:
    model = "missing-id-model"

    def __init__(self, fill_on_followup):
        self.fill_on_followup = fill_on_followup
        self.calls = 0

    def chat_json(self, messages, **kwargs):
        self.calls += 1
        is_followup = "vorigen Antwort fehlten" in messages[-1]["content"]
        outcome_id = "o2" if is_followup and self.fill_on_followup else "o1"
        return {"results": [{
            "outcome_id": outcome_id,
            "yes": False,
            "post_ids": [],
            "snippet": "",
        }]}


class RepeatingFollowupLLM:
    model = "repeating-followup-model"

    def __init__(self):
        self.calls = 0

    def chat_json(self, messages, **kwargs):
        self.calls += 1
        if self.calls == 1:
            return {"results": [{"outcome_id": "o1", "yes": False}]}
        return {"results": [
            {"outcome_id": "o1", "yes": True, "post_ids": ["twitter:1"],
             "snippet": "Anderes"},
            {"outcome_id": "o2", "yes": False},
        ]}


class InvalidAnswerLLM:
    model = "invalid-answer-model"

    def __init__(self, answer=None):
        self.answer = answer
        self.calls = 0

    def chat_json(self, messages, **kwargs):
        self.calls += 1
        return {"results": [
            {"outcome_id": "o1", "yes": self.answer},
            {"outcome_id": "o2", "yes": "nein"},
        ]}


def _two_outcome_state():
    return {"checklist": [
        {"id": "o1", "text_de": "Ereignis eins", "definition": "sichtbar",
         "polarity": "presence"},
        {"id": "o2", "text_de": "Ereignis zwei", "definition": "sichtbar",
         "polarity": "presence"},
    ]}


def test_missing_id_followup_completes_the_batch(tmp_path):
    llm = MissingIdLLM(fill_on_followup=True)
    service = EnsembleService(llm_factory=lambda: llm, root=tmp_path / "ensembles")
    result, audit = service._classify_posts_once(
        _two_outcome_state(),
        [{"post_id": "twitter:1", "agent": "Ada", "text": "Anderes"}],
        seed=1, run_number=1, llm=llm,
    )

    assert llm.calls == 2
    assert result["o2"] == {"yes": False, "evidence": []}
    batch = audit["batches"][0]
    assert batch["missing_ids_before_followup"] == ["o2"]
    assert batch["missing_ids_after_followup"] == []
    assert batch["followups"][0]["requested_ids"] == ["o2"]


def test_permanently_missing_id_stays_unclassified(tmp_path):
    llm = MissingIdLLM(fill_on_followup=False)
    service = EnsembleService(llm_factory=lambda: llm, root=tmp_path / "ensembles")
    result, audit = service._classify_posts_once(
        _two_outcome_state(),
        [{"post_id": "twitter:1", "agent": "Ada", "text": "Anderes"}],
        seed=1, run_number=1, llm=llm,
    )

    assert llm.calls == 3
    assert result["o2"] == {"yes": False, "evidence": [], "unclassified": True}
    batch = audit["batches"][0]
    assert batch["missing_ids_before_followup"] == ["o2"]
    assert batch["missing_ids_after_followup"] == ["o2"]
    assert len(batch["followups"]) == 2


def test_followup_cannot_change_unrequested_first_answer(tmp_path):
    llm = RepeatingFollowupLLM()
    service = EnsembleService(llm_factory=lambda: llm, root=tmp_path / "ensembles")
    result, audit = service._classify_posts_once(
        _two_outcome_state(),
        [{"post_id": "twitter:1", "agent": "Ada", "text": "Anderes"}],
        seed=1, run_number=1, llm=llm,
    )

    assert result["o1"] == {"yes": False, "evidence": []}
    followup = audit["batches"][0]["followups"][0]
    assert followup["requested_ids"] == ["o2"]
    assert [row["outcome_id"] for row in followup["rejected_rows"]] == ["o1"]


def test_oversized_verbose_followup_uses_compact_prompt(tmp_path, monkeypatch):
    llm = RepeatingFollowupLLM()
    service = EnsembleService(llm_factory=lambda: llm, root=tmp_path / "ensembles")

    def fake_estimate_tokens(value):
        return 501 if "vorigen Antwort fehlten" in str(value) else 100

    monkeypatch.setattr(ensemble_module, "estimate_tokens", fake_estimate_tokens)
    result, audit = service._classify_posts_once(
        _two_outcome_state(),
        [{"post_id": "twitter:1", "agent": "Ada", "text": "Anderes"}],
        seed=1,
        run_number=1,
        llm=llm,
        context_info={
            "model": llm.model, "num_ctx": 4096, "input_budget": 500,
            "output_tokens": 3000,
        },
    )

    assert result["o2"] == {"yes": False, "evidence": []}
    assert audit["batches"][0]["followups"][0]["compact"] is True


@pytest.mark.parametrize("invalid_answer", [None, "unklar", 1])
def test_invalid_yes_value_is_followed_up_then_unclassified(tmp_path, invalid_answer):
    llm = InvalidAnswerLLM(invalid_answer)
    service = EnsembleService(llm_factory=lambda: llm, root=tmp_path / "ensembles")
    result, audit = service._classify_posts_once(
        _two_outcome_state(),
        [{"post_id": "twitter:1", "agent": "Ada", "text": "Anderes"}],
        seed=1, run_number=1, llm=llm,
    )

    assert llm.calls == 3
    assert result["o1"] == {"yes": False, "evidence": [], "unclassified": True}
    assert result["o2"] == {"yes": False, "evidence": []}
    assert audit["batches"][0]["missing_ids_before_followup"] == ["o1"]
    assert audit["batches"][0]["missing_ids_after_followup"] == ["o1"]


def test_ollama_show_controls_classification_context_without_network(tmp_path, monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return json.dumps({"parameters": "temperature 0\nnum_ctx 32768\n"}).encode()

    requests = []

    def fake_urlopen(request, timeout):
        requests.append((request, timeout))
        return Response()

    monkeypatch.setattr(Config, "LLM_PROVIDER", "ollama")
    monkeypatch.setattr(Config, "LOCAL_LLM_BASE_URL", "http://ollama.test/v1")
    monkeypatch.setattr(ensemble_module.urllib.request, "urlopen", fake_urlopen)
    service = EnsembleService(root=tmp_path / "ensembles")
    context = service._classification_context(NamedBatchLLM("qwen3.5:9b-agent32k"))

    assert context == {
        "model": "qwen3.5:9b-agent32k",
        "num_ctx": 32768,
        "num_ctx_source": "ollama_parameter",
        "configured_input_budget": Config.ENSEMBLE_CLASSIFICATION_TOKEN_BUDGET,
        "output_tokens": 3000,
        "buffer_tokens": 256,
        "input_budget": Config.ENSEMBLE_CLASSIFICATION_TOKEN_BUDGET,
    }
    request, timeout = requests[0]
    assert request.full_url == "http://ollama.test/api/show"
    assert json.loads(request.data) == {
        "model": "qwen3.5:9b-agent32k", "name": "qwen3.5:9b-agent32k",
    }
    assert timeout == 10


def test_ollama_show_without_num_ctx_uses_conservative_default(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "LLM_PROVIDER", "ollama")
    service = EnsembleService(
        root=tmp_path / "ensembles",
        ollama_show=lambda _model: {"parameters": "temperature 0.2"},
    )
    context = service._classification_context(NamedBatchLLM("plain-model"))
    assert context["num_ctx"] == 4096
    assert context["num_ctx_source"] == "ollama_default"
    assert context["input_budget"] == 840


def test_too_small_ollama_context_fails_before_classification(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "LLM_PROVIDER", "ollama")
    llm = NamedBatchLLM("tiny-model")
    service = EnsembleService(
        root=tmp_path / "ensembles",
        ollama_show=lambda _model: {"parameters": "num_ctx 3200"},
    )
    with pytest.raises(ValueError, match=r"tiny-model.*num_ctx=3200.*Anweisung und Checkliste"):
        service._classify_posts_once(
            _two_outcome_state(),
            [{"post_id": "twitter:1", "agent": "Ada", "text": "Anderes"}],
            seed=1, run_number=1, llm=llm,
        )
    assert llm.calls == 0


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


def test_negated_wording_without_polarity_stays_presence(tmp_path):
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
    assert result["o1"]["yes"] is False


def test_absence_is_yes_only_when_positive_event_is_not_found(tmp_path):
    llm = BatchLLM(positive=False)
    service = EnsembleService(llm_factory=lambda: llm, root=tmp_path / "ensembles")
    result = service._classify_posts(
        {"checklist": [{
            "id": "o1",
            "text_de": "Im simulierten Zeitraum gibt es keine Medienreaktion",
            "definition": "Die Reaktion bleibt aus",
            "polarity": "absence",
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


def test_failed_batch_retries_twice_then_fails_the_run(tmp_path):
    llm = BatchLLM(fail=True)
    service = EnsembleService(llm_factory=lambda: llm, root=tmp_path / "ensembles")
    checklist = [{
        "id": "o1", "text_de": "Ereignis", "definition": "sichtbar", "polarity": "presence",
    }]
    run_dir = tmp_path / "run"
    with pytest.raises(RuntimeError, match=r"vollständig ausgefallen \(ValueError ×2\)"):
        service._classify_posts(
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
    assert audit["result"]["o1"]["unclassified"] is True


def test_batch_failure_logs_kind_without_payload(tmp_path, monkeypatch):
    secret = "GEHEIMER_BEITRAG_XYZ"
    loud = BatchLLM(fail=True)

    def chat_json(self, messages, **kwargs):
        self.calls += 1
        raise TimeoutError(f"Zeitüberschreitung raw={{{secret}}}")

    monkeypatch.setattr(BatchLLM, "chat_json", chat_json)
    warnings = []

    def capture(message, *args, **kwargs):
        warnings.append(message % args if args else str(message))

    monkeypatch.setattr(ensemble_module.logger, "warning", capture)
    service = EnsembleService(llm_factory=lambda: loud, root=tmp_path / "ensembles")
    with pytest.raises(RuntimeError, match=r"vollständig ausgefallen \(TimeoutError ×2\)") as raised:
        service._classify_posts(
            {"checklist": [{
                "id": "o1", "text_de": "Ereignis", "definition": "sichtbar", "polarity": "presence",
            }]},
            [{"platform": "twitter", "post_id": "twitter:1", "agent": "Ada", "text": secret}],
            seed=1, run_number=1, run_dir=tmp_path / "run",
        )
    assert secret not in str(raised.value)
    logged = [line for line in warnings if line.startswith("Klassifikationsstapel")]
    assert logged
    assert all(secret not in line for line in logged)
    assert all("TimeoutError" in line for line in logged)
    assert "Zeitüberschreitung raw=" in logged[0]


def test_error_kind_summary_counts_types_only():
    from app.services.ensemble import _clipped_error, _summarize_error_kinds
    assert _clipped_error("Zeitüberschreitung raw={GEHEIM} [liste]") == "Zeitüberschreitung raw="
    summary = _summarize_error_kinds(
        {"batches": [
            {"error": "Zeitüberschreitung {GEHEIM}", "error_type": "TimeoutError"},
            {"error": "json kaputt", "error_type": "ValueError"},
        ]},
        {"batches": [{"error": "nochmal", "error_type": "TimeoutError"}]},
    )
    assert summary == "TimeoutError ×2, ValueError ×1"
    assert "GEHEIM" not in summary


def test_classification_failure_archives_attempt_with_audit(tmp_path, monkeypatch):
    class FailLLM(FakeLLM):
        def chat_json(self, messages, **kwargs):
            blob = "\n".join(str(item.get("content") or "") for item in messages)
            if "Klassifiziere" in blob:
                raise ValueError("Parser defekt {GEHEIMTEXT}")
            return super().chat_json(messages, **kwargs)

    FakeRunner.states = {}
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(tmp_path))
    _prepared_simulation(tmp_path)
    service = EnsembleService(
        runner_cls=FakeRunner, llm_factory=lambda: FailLLM(),
        root=tmp_path / "ensembles", poll_interval=0.001,
    )
    started = service.start("sim_test", 1, 2, ["baseline"])
    state = _wait_ensemble(service, started["ensemble_id"])
    assert state["status"] == "failed", state.get("error")
    assert "GEHEIMTEXT" not in (state.get("error") or "")
    assert "ValueError" in (state.get("error") or "")
    stored = service._load(started["ensemble_id"])
    failures = stored["seed_failures"]["baseline:1"]
    assert len(failures) == SEED_ATTEMPTS
    assert stored["seed_attempts"]["baseline:1"] == SEED_ATTEMPTS
    baseline = tmp_path / "ensembles" / started["ensemble_id"] / "baseline"
    assert not (baseline / "run_1").exists()
    archived = sorted(baseline.glob("run_1.failed-*"))
    assert len(archived) == SEED_ATTEMPTS
    audit = json.loads((archived[0] / "classification.json").read_text(encoding="utf-8"))
    assert "Parser defekt {GEHEIMTEXT}" in audit["raters"]["a"]["batches"][0]["error"]
    assert failures[0]["path"] == str(archived[0])
    assert "ValueError" in failures[0]["error"]
    assert "GEHEIMTEXT" not in failures[0]["error"]
    assert service._completed_seed_result(archived[0]) is None


def test_baseline_lengths_ignore_archived_failures(tmp_path):
    from app.services.ensemble import baseline_transcript_lengths

    def write_run(path: Path, text: str) -> None:
        path.mkdir(parents=True)
        (path / "simulation_config.json").write_text(
            json.dumps({"event_config": {"initial_posts": []}}), encoding="utf-8"
        )
        db = sqlite3.connect(path / "twitter_simulation.db")
        db.execute(
            "CREATE TABLE user (user_id INTEGER, agent_id INTEGER, name TEXT, user_name TEXT)"
        )
        db.execute("INSERT INTO user VALUES (0, 0, 'Ada', 'ada')")
        db.execute("CREATE TABLE post (post_id INTEGER, user_id INTEGER, content TEXT)")
        db.execute("INSERT INTO post VALUES (1, 0, ?)", (text,))
        db.commit()
        db.close()

    root = tmp_path / "ens"
    write_run(root / "baseline" / "run_1", "kurz")
    write_run(
        root / "baseline" / "run_1.failed-1-20261014T120000",
        "dieser text ist viel laenger und darf nicht zaehlen",
    )
    assert baseline_transcript_lengths(root) == [len("kurz")]


def test_resume_does_not_read_archived_failure_as_result(tmp_path, monkeypatch):
    FakeRunner.states = {}
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(tmp_path))
    _prepared_simulation(tmp_path)
    ensemble_id = "ens_eeeeeeeeeeee"
    root = tmp_path / "ensembles" / ensemble_id
    archived = root / "baseline" / "run_1.failed-1-20261014T120000"
    archived.mkdir(parents=True)
    (archived / "classification.json").write_text(json.dumps({
        "result": {"o1": {"yes": False, "evidence": [], "unclassified": False}},
    }), encoding="utf-8")
    (archived / "marker.txt").write_text("behalten", encoding="utf-8")
    checklist = [{
        "id": f"o{i}", "text_de": f"Ergebnis {i}", "definition": "sichtbar",
        "polarity": "presence", "source": "auto",
    } for i in range(1, 6)]
    state = {
        "ensemble_id": ensemble_id, "simulation_id": "sim_test", "question": "Was geschieht?",
        "status": "failed", "error": "Seed abgestürzt", "created_at": "2026-01-01T00:00:00",
        "finished_at": "2026-01-01T01:00:00", "runs": 1, "hours": 2, "start_hour": 7,
        "variants": [{"key": "baseline", "label_de": "Basislauf", "label_en": "Baseline",
                      "status": "failed", "done": 0, "total": 1}],
        "checklist": checklist, "custom_outcomes": [], "primary_outcome_id": "o1",
        "results": {}, "comparisons": [], "reliability": {}, "consistency_warnings": [],
        "current": None, "eta_seconds": None, "base_seed": 11, "cancel_requested": False,
        "current_runner_id": None, "seed_attempts": {},
        "seed_failures": {"baseline:1": [{
            "path": str(archived), "error": "alt", "at": "2026-10-14T12:00:00", "attempt": 1,
        }]},
    }
    (root / "ensemble.json").write_text(json.dumps(state), encoding="utf-8")
    calls = []

    class RecordingRunner(FakeRunner):
        @classmethod
        def start_simulation(cls, simulation_id, simulation_dir, **kwargs):
            calls.append(simulation_id)
            return super().start_simulation(simulation_id, simulation_dir, **kwargs)

    service = EnsembleService(
        runner_cls=RecordingRunner, llm_factory=FakeLLM,
        root=tmp_path / "ensembles", poll_interval=0.001,
    )
    service.resume(ensemble_id)
    finished = _wait_ensemble(service, ensemble_id)
    assert finished["status"] == "completed", finished.get("error")
    assert calls == [f"{ensemble_id}_baseline_1"]
    assert finished["results"]["baseline"]["o1"]["yes"] == 1
    assert finished["results"]["baseline"]["o1"]["n"] == 1
    assert (archived / "marker.txt").read_text(encoding="utf-8") == "behalten"
    assert service._load(ensemble_id)["seed_failures"]["baseline:1"][0]["error"] == "alt"


def test_low_disk_keeps_archived_failures(tmp_path, monkeypatch):
    service = EnsembleService(root=tmp_path / "ensembles", min_free_bytes=5 * 1024**3)
    archived = (
        tmp_path / "ensembles" / "ens_aaaaaaaaaaaa" / "baseline"
        / "run_1.failed-1-20261014T120000"
    )
    archived.mkdir(parents=True)
    marker = archived / "classification.json"
    marker.write_text('{"error": "bleibt"}', encoding="utf-8")
    monkeypatch.setattr(
        ensemble_module.shutil, "disk_usage",
        lambda _path: SimpleNamespace(total=10, used=9, free=1024),
    )
    with pytest.raises(RuntimeError, match="Zu wenig freier Speicher"):
        service._check_disk_space()
    assert marker.read_text(encoding="utf-8") == '{"error": "bleibt"}'


def test_archived_run_state_does_not_keep_ensemble_alive(tmp_path, monkeypatch):
    service = EnsembleService(root=tmp_path / "ensembles")
    path = _running_ensemble(tmp_path)
    failed = path.parent / "baseline" / "run_1.failed-1-20261014T120000"
    failed.mkdir(parents=True)
    (failed / "run_state.json").write_text("{}", encoding="utf-8")
    old = time.time() - 600
    os.utime(path, (old, old))
    monkeypatch.setattr(ensemble_module, "PROCESS_START_TIME", time.time() - 60)
    assert service.mark_stale_runs() == 1


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


class InvalidNarrativeAnswerLLM:
    model = "invalid-narrative-answer"

    def __init__(self):
        self.calls = 0

    def chat_json(self, messages, **kwargs):
        self.calls += 1
        return {"results": [{"outcome_id": "o1", "yes": "unklar"}]}


def test_invalid_narrative_yes_is_followed_up_then_unclassified(tmp_path):
    llm = InvalidNarrativeAnswerLLM()
    service = EnsembleService(llm_factory=lambda: llm, root=tmp_path / "ensembles")
    result, audit = service._classify_narrative_once(
        {"checklist": [{
            "id": "o1", "text_de": "Ein Ereignis findet statt",
            "definition": "sichtbar", "polarity": "presence", "kind": "event",
        }]},
        "Es geschieht nichts Einschlägiges.",
        seed=2,
        run_number=1,
        llm=llm,
        context_info={
            "model": llm.model, "num_ctx": 4096, "input_budget": 800,
            "output_tokens": 3000,
        },
    )

    assert llm.calls == 3
    assert result["o1"] == {"yes": False, "evidence": [], "unclassified": True}
    assert audit["batches"][0]["missing_ids_before_followup"] == ["o1"]
    assert audit["batches"][0]["missing_ids_after_followup"] == ["o1"]


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


def test_blind_feed_variant_accepted_and_own_rows():
    assert is_blind_feed("blind_feed")
    assert not is_blind_feed("isolated")
    assert "blind_feed" in validate_variants(["baseline", "blind_feed", "isolated"])
    posts = [
        {"user_id": 0, "post_id": 1, "content": "mein"},
        {"user_id": 1, "post_id": 2, "content": "fremd"},
    ]
    assert own_post_rows(posts, 0) == [posts[0]]


def test_blind_feed_clears_rec_and_refresh_returns_own_only():
    import asyncio

    class FakeUtils:
        def __init__(self, posts):
            self.posts = posts
            self.deleted = False
            self._rows = []

        def _execute_db_command(self, query, params=None, commit=False):
            if "DELETE FROM rec" in query:
                self.deleted = True
                self._rows = []
            elif "FROM post WHERE user_id" in query:
                uid = params[0]
                self._rows = [
                    (p["post_id"], p["user_id"], None, p["content"], None, 0, 0, 0, 0)
                    for p in self.posts if p["user_id"] == uid
                ]
            else:
                self._rows = []

        def _add_comments_to_posts(self, results):
            return [
                {
                    "post_id": row[0],
                    "user_id": row[1],
                    "content": row[3],
                    "comments": [
                        {"user_id": row[1], "content": "eigener Kommentar"},
                        {"user_id": 99, "content": "fremder Kommentar"},
                    ],
                }
                for row in results
            ]

    class FakeCursor:
        def __init__(self, utils):
            self._utils = utils

        def fetchall(self):
            return list(self._utils._rows)

    class FakePlatform:
        def __init__(self):
            posts = [
                {"post_id": 1, "user_id": 0, "content": "eigen"},
                {"post_id": 2, "user_id": 1, "content": "fremd"},
            ]
            self.pl_utils = FakeUtils(posts)
            self.db_cursor = FakeCursor(self.pl_utils)

        async def update_rec_table(self):
            return None

        async def refresh(self, agent_id):
            return {"success": True, "posts": [{"post_id": 2, "user_id": 1}]}

    async def exercise():
        platform = FakePlatform()
        install_blind_feed(platform)
        await platform.update_rec_table()
        assert platform.pl_utils.deleted is True
        seen = await platform.refresh(0)
        assert seen["success"] is True
        assert [p["user_id"] for p in seen["posts"]] == [0]
        assert all(p["content"] == "eigen" for p in seen["posts"])
        assert seen["posts"][0]["comments"] == [
            {"user_id": 0, "content": "eigener Kommentar"}
        ]
        empty = await platform.refresh(7)
        assert empty == {"success": True, "posts": []}

        # Wie oasis Platform.running(): agent_id nur bei mindestens zwei Parametern.
        action_function = getattr(platform, "refresh")
        code = action_function.__code__
        params = {}
        if len(code.co_varnames[:code.co_argcount]) >= 2:
            params["agent_id"] = 0
        dispatched = await action_function(**params)
        assert [p["user_id"] for p in dispatched["posts"]] == [0]

    asyncio.run(exercise())


def test_opening_stimulus_logged_once_per_agent(tmp_path):
    class FakeAgent:
        def __init__(self):
            self.memory = []

        def update_memory(self, message, role):
            self.memory.append((role, message.content))

    class FakeGraph:
        def get_agents(self):
            return [(0, FakeAgent()), (1, FakeAgent())]

    log_path = tmp_path / "stimulus_log.json"
    posts = [{"post_id": 9, "user_id": 0, "content": "Startimpuls"}]
    document = deliver_opening_stimulus(FakeGraph(), posts, log_path, "twitter")
    assert log_path.is_file()
    assert document["agents"][0]["seen"] is True
    assert document["agents"][1]["seen_post_ids"] == [9]
    assert len(document["agents"]) == 2


def test_blind_feed_opening_stimulus_is_own_only(tmp_path):
    class FakeAgent:
        def __init__(self):
            self.memory = []

        def update_memory(self, message, role):
            self.memory.append(message.content)

    agents = {0: FakeAgent(), 1: FakeAgent()}

    class FakeGraph:
        def get_agents(self):
            return list(agents.items())

    posts = [
        {"post_id": 9, "user_id": 0, "content": "nur null"},
        {"post_id": 10, "user_id": 1, "content": "nur eins"},
    ]
    document = deliver_opening_stimulus(
        FakeGraph(), posts, tmp_path / "stimulus.json", "reddit", own_only=True
    )
    assert document["own_only"] is True
    assert document["agents"][0]["seen_post_ids"] == [9]
    assert document["agents"][1]["seen_post_ids"] == [10]
    assert "nur eins" not in agents[0].memory[0]
    assert "nur null" not in agents[1].memory[0]


def test_measure_blind_feed_usage_from_oasis_trace(tmp_path):
    db_path = tmp_path / "reddit_simulation.db"
    connection = sqlite3.connect(db_path)
    connection.executescript("""
        CREATE TABLE post (post_id INTEGER PRIMARY KEY, user_id INTEGER);
        CREATE TABLE comment (
            comment_id INTEGER PRIMARY KEY, post_id INTEGER, user_id INTEGER
        );
        CREATE TABLE trace (user_id INTEGER, action TEXT, info TEXT);
        INSERT INTO post VALUES (10, 1), (11, 2), (12, 1);
        INSERT INTO comment VALUES (20, 11, 1), (21, 10, 1);
    """)
    rows = [
        (1, "search_posts", {"query": "x"}),
        (1, "trend", {"posts": []}),
        (1, "like_post", {"post_id": 11}),
        (1, "repost", {"reposted_id": 12}),
        (1, "quote_post", {"quoted_id": 11}),
        (1, "create_comment", {"comment_id": 20}),
        (1, "create_comment", {"comment_id": 21}),
    ]
    connection.executemany(
        "INSERT INTO trace VALUES (?, ?, ?)",
        [(user_id, action, json.dumps(info)) for user_id, action, info in rows],
    )
    connection.commit()
    connection.close()

    assert measure_blind_feed_usage(tmp_path) == {
        "search_action_count": 1,
        "trend_action_count": 1,
        "foreign_interaction_count": 3,
    }


def test_run_stats_and_markdown_table():
    stats = compute_run_stats(
        [{"text": "abcd"}, {"text": "ef"}],
        audit={"raters": {"a": {"batches": [{}, {}]}}},
    )
    assert stats == {
        "post_count": 2,
        "contribution_count": 2,
        "character_count": 6,
        "batch_count": 2,
        "agent_action_count": 0,
        "agent_error_count": 0,
        "agent_error_rate": 0.0,
        "action_log_status": "fehlt",
        "search_action_count": 0,
        "trend_action_count": 0,
        "foreign_interaction_count": 0,
    }
    null_stats = compute_run_stats(
        narrative="hello",
        audit={"batches": [{}]},
    )
    assert null_stats["post_count"] == 0
    assert null_stats["character_count"] == 5
    assert null_stats["batch_count"] == 1
    state = {
        "status": "completed",
        "runs": 1,
        "hours": 24,
        "primary_outcome_id": "o1",
        "variants": [
            {"key": "baseline", "label_de": "Basislauf"},
            {"key": "blind_feed", "label_de": "Blinder Feed"},
        ],
        "checklist": [{
            "id": "o1", "text_de": "Ereignis", "definition": "x",
            "polarity": "presence", "kind": "event",
        }],
        "results": {
            "baseline": {"o1": {
                "yes": 1, "n": 1, "disputed": 0, "unclassified": 0,
                "rate": 1.0, "ci_low": 0.2, "ci_high": 1.0,
            }},
            "blind_feed": {"o1": {
                "yes": 0, "n": 1, "disputed": 0, "unclassified": 0,
                "rate": 0.0, "ci_low": 0.0, "ci_high": 0.8,
            }},
        },
        "run_stats": {
            "baseline": [{"run": 1, "post_count": 3, "character_count": 40, "batch_count": 1}],
            "blind_feed": [{"run": 1, "post_count": 2, "character_count": 10, "batch_count": 1}],
        },
        "comparisons": [],
        "reliability": {},
    }
    md = ensemble_markdown(state)
    assert "### Textmengen je Lauf" in md
    assert "| Basislauf | 1 | 3 | 40 | 1 | 0 | 0 | 0 |" in md
    assert "Fremdinteraktionen" in md
    assert "blind_feed" in md.lower() or "Blinder Feed" in md


def test_null_run_manifest_fields(tmp_path):
    manifest = build_null_run_manifest(
        "Prompt-Text",
        model="local-model",
        temperature=0.7,
        seed=11,
        max_tokens=4000,
    )
    assert set(manifest) == {
        "prompt_sha256", "model", "temperature", "seed", "max_tokens",
    }
    assert manifest["model"] == "local-model"
    assert manifest["temperature"] == 0.7
    assert manifest["seed"] == 11
    assert manifest["max_tokens"] == 4000
    assert len(manifest["prompt_sha256"]) == 64

    class CaptureLLM:
        model = "capture-model"

        def chat(self, messages, **kwargs):
            return "Erzählung."

    service = EnsembleService(llm_factory=lambda: CaptureLLM(), root=tmp_path / "ensembles")
    run_dir = tmp_path / "null_document" / "run_1"
    run_dir.mkdir(parents=True)
    service._null_narrative(
        {"question": "Was?", "hours": 24},
        {"extracted_text": "Dokument.", "config": {}},
        seed=5,
        arm="null_document",
        run_dir=run_dir,
    )
    written = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert written["seed"] == 5
    assert written["max_tokens"] == 4000
    assert written["temperature"] == 0.7
    assert written["model"] == "capture-model"
    assert written["prompt_sha256"]


@pytest.mark.parametrize("status", ["completed", "failed", "cancelled"])
def test_get_liefert_keine_restzeit_bei_beendeten_laeufen(tmp_path, status):
    service = EnsembleService(llm_factory=lambda: None, root=tmp_path / "ensembles")
    path = tmp_path / "ensembles" / "ens_cccccccccccc" / "ensemble.json"
    path.parent.mkdir(parents=True)
    raw = {"ensemble_id": "ens_cccccccccccc", "status": status, "eta_seconds": 75, "created_at": "2025-10-13"}
    path.write_text(json.dumps(raw), encoding="utf-8")
    before = path.read_text(encoding="utf-8")

    assert service.get("ens_cccccccccccc")["eta_seconds"] is None
    assert service.list()[0]["eta_seconds"] is None
    assert path.read_text(encoding="utf-8") == before


def test_get_behaelt_restzeit_bei_laufendem_ensemble(tmp_path):
    service = EnsembleService(llm_factory=lambda: None, root=tmp_path / "ensembles")
    path = tmp_path / "ensembles" / "ens_dddddddddddd" / "ensemble.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"ensemble_id": "ens_dddddddddddd", "status": "running", "eta_seconds": 75}), encoding="utf-8")
    assert service.get("ens_dddddddddddd")["eta_seconds"] == 75


def test_null_parse_error_is_unclassified_and_run_fails(tmp_path):
    llm = BatchLLM(fail=True)
    service = EnsembleService(llm_factory=lambda: llm, root=tmp_path / "ensembles")
    run_dir = tmp_path / "null" / "run_1"
    with pytest.raises(RuntimeError, match=r"vollständig ausgefallen \(ValueError ×2\)"):
        service._classify_narrative(
            {"checklist": [{
                "id": "o1", "text_de": "Ereignis", "definition": "sichtbar",
                "polarity": "absence",
            }]},
            "Kein relevanter Text.", 4, 1, run_dir, "null_document",
        )
    audit = json.loads((run_dir / "classification.json").read_text(encoding="utf-8"))
    assert audit["result"]["o1"] == {
        "yes": False,
        "evidence": [],
        "unclassified": True,
        "disputed": False,
        "raters": {
            "a": {"yes": False, "evidence": [], "unclassified": True},
            "b": {"yes": False, "evidence": [], "unclassified": True},
        },
    }


def test_completed_seed_rejects_stored_batch_failure(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "classification.json").write_text(json.dumps({
        "raters": {"a": {"batches": [{"error": "timeout"}]}},
        "result": {"o1": {"yes": False, "unclassified": True}},
    }), encoding="utf-8")
    service = EnsembleService(root=tmp_path / "ensembles")
    assert service._completed_seed_result(run_dir) is None
    (run_dir / "classification.json").write_text(json.dumps({
        "batches": [{"error": "parse_error"}],
        "result": {"o1": {"yes": False, "unclassified": True}},
    }), encoding="utf-8")
    assert service._completed_seed_result(run_dir) is None


def test_health_wait_does_not_consume_seed_attempt(tmp_path, monkeypatch):
    FakeRunner.states = {}
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(tmp_path))
    _prepared_simulation(tmp_path)
    checks = []

    def health():
        checks.append(1)
        if len(checks) == 1:
            raise OSError("Ollama startet neu")
        return [Config.LLM_MODEL_NAME, Config.get_llm_config()["model"],
                Config.ENSEMBLE_SECOND_RATER_MODEL]

    service = EnsembleService(
        runner_cls=FakeRunner, llm_factory=FakeLLM,
        root=tmp_path / "ensembles", poll_interval=0.001,
        health_check=health, sleep=lambda _seconds: None,
    )
    started = service.start("sim_test", 1, 2, ["baseline"])
    state = _wait_ensemble(service, started["ensemble_id"])
    assert state["status"] == "completed", state.get("error")
    assert len(checks) >= 2
    assert service._load(started["ensemble_id"])["seed_attempts"]["baseline:1"] == 1


def test_models_are_recorded_per_role_and_arm(tmp_path, monkeypatch):
    FakeRunner.states = {}
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(tmp_path))
    _prepared_simulation(tmp_path)
    service = EnsembleService(
        runner_cls=FakeRunner, llm_factory=FakeLLM,
        root=tmp_path / "ensembles", poll_interval=0.001,
    )
    started = service.start(
        "sim_test", 1, 2, ["baseline", "null_document"],
        text_model="agent-model", arm_model="arm-model",
    )
    state = _wait_ensemble(service, started["ensemble_id"])
    assert state["status"] == "completed", state.get("error")
    assert state["arm_models"] == {
        "baseline": "agent-model", "null_document": "arm-model",
    }
    assert {item["key"]: item["text_model"] for item in state["variants"]} == state["arm_models"]
    config = json.loads((
        tmp_path / "ensembles" / started["ensemble_id"] / "baseline" / "run_1"
        / "simulation_config.json"
    ).read_text(encoding="utf-8"))
    assert config["llm_model"] == "agent-model"
    manifest = json.loads((
        tmp_path / "ensembles" / started["ensemble_id"] / "null_document" / "run_1"
        / "manifest.json"
    ).read_text(encoding="utf-8"))
    assert manifest["model"] == "arm-model"


def test_strict_second_rater_rejects_missing_model(tmp_path, monkeypatch):
    monkeypatch.delenv("ENSEMBLE_SECOND_RATER_MODEL", raising=False)
    monkeypatch.setattr(Config, "ENSEMBLE_SECOND_RATER_MODEL", "")
    service = EnsembleService(root=tmp_path / "ensembles")
    with pytest.raises(ValueError, match="Zweitmodell"):
        service.start(
            "sim_test", 1, 2, ["baseline"], strict_second_rater=True,
        )


def test_min_classified_marks_result_unmeasurable(tmp_path):
    service = EnsembleService(root=tmp_path / "ensembles")
    state = {
        "runs": 5, "min_classified": 4,
        "variants": [{"key": "baseline"}],
        "checklist": [{"id": "o1", "polarity": "presence"}],
    }
    classified = {"yes": False, "unclassified": False, "disputed": False}
    missing = {"yes": False, "unclassified": True, "disputed": False}
    service._aggregate(
        state,
        {"baseline": [{"o1": classified}] * 3 + [{"o1": missing}] * 2},
    )
    assert state["results"]["baseline"]["o1"]["measurable"] is False
    assert state["measurement"]["measurable"] is False
    assert state["unclassified_runs"] == 2


def test_fully_unclassified_arm_has_no_rate_or_interval(tmp_path):
    service = EnsembleService(root=tmp_path / "ensembles")
    state = {
        "runs": 2, "min_classified": 1, "status": "completed", "hours": 2,
        "variants": [{"key": "baseline", "label_de": "Basislauf"}],
        "checklist": [{"id": "c1", "text_de": "Primärfrage", "polarity": "presence"}],
        "primary_outcome_id": "c1",
    }
    missing = {"yes": False, "unclassified": True, "disputed": False}
    service._aggregate(state, {"baseline": [{"c1": missing}, {"c1": missing}]})

    stat = state["results"]["baseline"]["c1"]
    assert stat["n"] == 0
    assert stat["rate"] is None
    assert stat["ci_low"] is None
    assert stat["ci_high"] is None
    report = ensemble_markdown(state)
    assert "0 / 0" in report
    assert "nicht messbar" in report
    assert "0.0% (0.0%–0.0%)" not in report


def test_run_stats_agent_error_rate_and_quality_gate(tmp_path):
    run_dir = tmp_path / "run"
    log = run_dir / "twitter" / "actions.jsonl"
    log.parent.mkdir(parents=True)
    log.write_text("\n".join([
        json.dumps({"action_type": "post", "success": False}),
        json.dumps({"action_type": "post", "success": True}),
    ]), encoding="utf-8")
    stats = compute_run_stats([{"text": "Beitrag"}], run_dir=run_dir)
    assert stats["agent_error_count"] == 1
    assert stats["agent_error_rate"] == 0.5
    service = EnsembleService(root=tmp_path / "ensembles")
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(service, "_stats_for_run", lambda _key, _run_dir: stats)
    with pytest.raises(RuntimeError, match="Fehlerquote"):
        service._validate_run_quality(
            {"min_posts": 1, "max_agent_error_rate": 0.49}, "baseline", run_dir,
        )
    monkeypatch.undo()

    empty = {**stats, "contribution_count": 0, "agent_error_rate": 0.0}
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(service, "_stats_for_run", lambda _key, _run_dir: empty)
    with pytest.raises(RuntimeError, match="nur 0 Beiträge"):
        service._validate_run_quality(
            {"min_posts": 1, "max_agent_error_rate": 1.0}, "baseline", run_dir,
        )
    monkeypatch.undo()

    missing = tmp_path / "missing-log"
    missing.mkdir()
    assert compute_run_stats([{"text": "Beitrag"}], run_dir=missing)["action_log_status"] == "fehlt"
    # Entscheidung allein über min_posts: genug Beiträge ohne Aktionslog sind kein Fehlschlag
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        service, "_stats_for_run",
        lambda _key, _run_dir: compute_run_stats([{"text": "Beitrag"}], run_dir=missing),
    )
    service._validate_run_quality(
        {"min_posts": 1, "max_agent_error_rate": 1.0}, "baseline", missing,
    )
    monkeypatch.undo()
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        service, "_stats_for_run", lambda _key, _run_dir: compute_run_stats([], run_dir=missing)
    )
    with pytest.raises(RuntimeError, match="Aktionslog fehlt"):
        service._validate_run_quality(
            {"min_posts": 1, "max_agent_error_rate": 1.0}, "baseline", missing,
        )
    monkeypatch.undo()
    blank = tmp_path / "blank-log"
    (blank / "twitter").mkdir(parents=True)
    (blank / "twitter" / "actions.jsonl").write_text("", encoding="utf-8")
    assert compute_run_stats([{"text": "x"}], run_dir=blank)["action_log_status"] == "leer"
    events_only = tmp_path / "events-log"
    (events_only / "twitter").mkdir(parents=True)
    (events_only / "twitter" / "actions.jsonl").write_text('{"event": "x"}\n', encoding="utf-8")
    assert compute_run_stats(
        [{"text": "x"}], run_dir=events_only
    )["action_log_status"] == "ohne_aktionen"
    null_dir = tmp_path / "null_document"
    null_dir.mkdir()
    (null_dir / "narrative.txt").write_text("Eine kurze Erzählung.", encoding="utf-8")
    (null_dir / "classification.json").write_text("{}", encoding="utf-8")
    service._validate_run_quality(
        {"min_posts": 5, "max_agent_error_rate": 0.0}, "null_document", null_dir,
    )
    narrative_stats = compute_run_stats(narrative="Eine kurze Erzählung.", run_dir=null_dir)
    assert narrative_stats["contribution_count"] == 1
    assert narrative_stats["agent_error_rate"] == 0.0


def test_disk_preflight_rejects_seed_start(tmp_path, monkeypatch):
    service = EnsembleService(root=tmp_path / "ensembles", min_free_bytes=5 * 1024**3)
    monkeypatch.setattr(
        ensemble_module.shutil, "disk_usage",
        lambda _path: SimpleNamespace(total=10, used=9, free=1024),
    )
    with pytest.raises(RuntimeError, match="Zu wenig freier Speicher"):
        service.start("sim_test", 1, 2, ["baseline"])


def test_strict_second_rater_rejects_model_missing_from_ollama(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(tmp_path))
    _prepared_simulation(tmp_path)
    service = EnsembleService(
        root=tmp_path / "ensembles",
        health_check=lambda: [Config.LLM_MODEL_NAME, Config.get_llm_config()["model"]],
    )
    with pytest.raises(RuntimeError, match="Modelle fehlen"):
        service.start(
            "sim_test", 1, 2, ["baseline"], strict_second_rater=True,
        )


def test_stale_backend_restart_does_not_consume_attempt(tmp_path, monkeypatch):
    monkeypatch.setattr(ensemble_module, "PROCESS_START_TIME", time.time() + 60)
    service = EnsembleService(root=tmp_path / "ensembles")
    path = tmp_path / "ensembles" / "ens_aaaaaaaaaaaa" / "ensemble.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({
        "ensemble_id": "ens_aaaaaaaaaaaa", "status": "running",
        "current": {"variant": "baseline", "run": 1, "attempt": 2},
        "seed_attempts": {"baseline:1": 2},
    }), encoding="utf-8")
    assert service.mark_stale_runs() == 1
    assert service._load("ens_aaaaaaaaaaaa")["seed_attempts"]["baseline:1"] == 1


def test_resume_orphan_cleanup_only_targets_owned_run(tmp_path, monkeypatch):
    service = EnsembleService(root=tmp_path / "ensembles")
    ensemble_id = "ens_bbbbbbbbbbbb"
    run_dir = tmp_path / "ensembles" / ensemble_id / "baseline" / "run_1"
    run_dir.mkdir(parents=True)
    (run_dir / "run_state.json").write_text(
        json.dumps({"process_pid": 4321}), encoding="utf-8"
    )
    state = {
        "ensemble_id": ensemble_id,
        "current_runner_id": f"{ensemble_id}_baseline_1",
        "current": {"variant": "baseline", "run": 1},
    }
    killed = []
    monkeypatch.setattr(ensemble_module.os, "readlink", lambda _path: str(run_dir))
    monkeypatch.setattr(Path, "read_bytes", lambda _path: b"python run_parallel_simulation.py\0")
    monkeypatch.setattr(ensemble_module.os, "getpgid", lambda pid: pid)
    monkeypatch.setattr(
        ensemble_module.os, "killpg", lambda pgid, sig: killed.append((pgid, sig))
    )
    assert service._terminate_owned_orphan(state) is True
    assert killed == [(4321, ensemble_module.signal.SIGTERM)]

    killed.clear()
    monkeypatch.setattr(ensemble_module.os, "readlink", lambda _path: str(tmp_path / "other"))
    assert service._terminate_owned_orphan(state) is False
    assert killed == []


def test_orphan_without_current_kills_only_that_run_folder(tmp_path, monkeypatch):
    service = EnsembleService(root=tmp_path / "ensembles")
    ensemble_id = "ens_0a0a0a0a0a0a"
    own = tmp_path / "ensembles" / ensemble_id / "baseline" / "run_1"
    wrong_cwd = tmp_path / "ensembles" / ensemble_id / "baseline" / "run_2"
    wrong_command = tmp_path / "ensembles" / ensemble_id / "isolated" / "run_1"
    tiny = tmp_path / "ensembles" / ensemble_id / "blind_feed" / "run_1"
    foreign = tmp_path / "ensembles" / "ens_0b0b0b0b0b0b" / "baseline" / "run_1"
    folders = {own: 4321, wrong_cwd: 5555, wrong_command: 111, tiny: 1, foreign: 9999}
    for directory, pid in folders.items():
        directory.mkdir(parents=True)
        (directory / "run_state.json").write_text(
            json.dumps({"process_pid": pid}), encoding="utf-8"
        )
    cwd = {
        "4321": own,
        "5555": tmp_path / "elsewhere",
        "111": wrong_command,
        "9999": foreign,
    }

    def readlink(path):
        return str(cwd[Path(path).parent.name])

    def read_bytes(self):
        if self.parent.name == "111":
            return b"python something_else.py\0"
        return b"python run_parallel_simulation.py\0"

    killed = []
    monkeypatch.setattr(ensemble_module.os, "readlink", readlink)
    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    monkeypatch.setattr(ensemble_module.os, "getpgid", lambda pid: pid)
    monkeypatch.setattr(
        ensemble_module.os, "killpg", lambda pgid, sig: killed.append((pgid, sig))
    )
    assert service._terminate_owned_orphan({
        "ensemble_id": ensemble_id, "current": None, "current_runner_id": None,
    }) is True
    assert killed == [(4321, ensemble_module.signal.SIGTERM)]

    (tmp_path / "ensembles" / ensemble_id / "ensemble.json").write_text(json.dumps({
        "ensemble_id": ensemble_id, "status": "running",
        "current": {"variant": "baseline", "run": 1, "attempt": 1},
        "seed_attempts": {"baseline:1": 1},
    }), encoding="utf-8")
    killed.clear()
    monkeypatch.setattr(ensemble_module, "PROCESS_START_TIME", time.time() + 60)
    assert service.mark_stale_runs() == 1
    assert service._load(ensemble_id)["current"] is None
    assert killed == [(4321, ensemble_module.signal.SIGTERM)]


def test_resume_terminates_orphan_before_restarting_seed(tmp_path, monkeypatch):
    FakeRunner.states = {}
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(tmp_path))
    _prepared_simulation(tmp_path)
    ensemble_id = "ens_dddddddddddd"
    root = tmp_path / "ensembles" / ensemble_id
    root.mkdir(parents=True)
    (root / "ensemble.json").write_text(json.dumps({
        "ensemble_id": ensemble_id, "simulation_id": "sim_test", "question": "Was geschieht?",
        "status": "failed", "error": "Backend wurde neu gestartet, Ensemble abgebrochen",
        "created_at": "2026-01-01T00:00:00", "finished_at": "2026-01-01T01:00:00",
        "runs": 1, "hours": 2, "start_hour": 7,
        "variants": [{"key": "baseline", "label_de": "Basislauf", "label_en": "Baseline",
                      "status": "failed", "done": 0, "total": 1}],
        "checklist": [], "custom_outcomes": [], "primary_outcome_id": None,
        "results": {}, "comparisons": [], "reliability": {}, "consistency_warnings": [],
        "current": None, "eta_seconds": None, "base_seed": 11, "cancel_requested": False,
        "current_runner_id": None,
    }), encoding="utf-8")
    events = []
    original = EnsembleService._terminate_owned_orphan

    def spy(self, loaded):
        events.append(("terminate", loaded.get("current")))
        return original(self, loaded)

    monkeypatch.setattr(EnsembleService, "_terminate_owned_orphan", spy)

    class RecordingRunner(FakeRunner):
        @classmethod
        def start_simulation(cls, simulation_id, simulation_dir, **kwargs):
            events.append(("start", simulation_id))
            return super().start_simulation(simulation_id, simulation_dir, **kwargs)

    service = EnsembleService(
        runner_cls=RecordingRunner, llm_factory=FakeLLM,
        root=tmp_path / "ensembles", poll_interval=0.001,
    )
    service.resume(ensemble_id)
    finished = _wait_ensemble(service, ensemble_id)
    assert finished["status"] == "completed", finished.get("error")
    assert events[0] == ("terminate", None)
    assert events[1][0] == "start"


def test_strict_second_rater_rejects_same_model_name(tmp_path, monkeypatch):
    monkeypatch.delenv("ENSEMBLE_SECOND_RATER_MODEL", raising=False)
    monkeypatch.setattr(Config, "LLM_PROVIDER", "openai")
    monkeypatch.setattr(Config, "LLM_MODEL_NAME", "gleiches-modell")
    monkeypatch.setattr(Config, "ENSEMBLE_SECOND_RATER_MODEL", "gleiches-modell")
    service = EnsembleService(root=tmp_path / "ensembles")
    with pytest.raises(ValueError, match="verschiedene Modellnamen"):
        service.start("sim_test", 1, 2, ["baseline"], strict_second_rater=True)

    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(tmp_path))
    monkeypatch.setattr(Config, "ENSEMBLE_SECOND_RATER_MODEL", "anderes-modell")
    with pytest.raises(FileNotFoundError):
        service.start("sim_test", 1, 2, ["baseline"], strict_second_rater=True)


def test_baseline_below_agent_count_retries_the_seed(tmp_path, monkeypatch):
    FakeRunner.states = {}
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(tmp_path))
    _prepared_simulation(tmp_path)
    config_path = tmp_path / "simulations" / "sim_test" / "simulation_config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["agent_configs"] = [
        {"agent_id": index, "entity_type": "Person"} for index in range(3)
    ]
    config_path.write_text(json.dumps(config), encoding="utf-8")
    service = EnsembleService(
        runner_cls=FakeRunner, llm_factory=FakeLLM,
        root=tmp_path / "ensembles", poll_interval=0.001,
    )
    started = service.start("sim_test", 1, 2, ["baseline"], min_posts="agent_count")
    state = _wait_ensemble(service, started["ensemble_id"])
    assert state["status"] == "failed", state.get("error")
    assert state["min_posts"] == 3
    assert "Beiträge" in (state.get("error") or "")
    assert "unbekannt" not in (state.get("error") or "")
    assert state["attempts_exhausted"] is True
    stored = service._load(started["ensemble_id"])
    assert stored["seed_attempts"]["baseline:1"] == SEED_ATTEMPTS


def test_missing_action_log_is_unknown_and_retries_the_seed(tmp_path, monkeypatch):
    class NoActionLogRunner(FakeRunner):
        calls = []

        @classmethod
        def start_simulation(cls, simulation_id, simulation_dir, **kwargs):
            cls.calls.append(simulation_id)
            started = super().start_simulation(simulation_id, simulation_dir, **kwargs)
            log = Path(simulation_dir) / "twitter" / "actions.jsonl"
            log.unlink(missing_ok=True)
            return started

    NoActionLogRunner.calls = []
    FakeRunner.states = {}
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(tmp_path))
    _prepared_simulation(tmp_path)
    bare = tmp_path / "bare"
    bare.mkdir()
    (bare / "twitter").mkdir()
    (bare / "twitter" / "actions.jsonl").write_text('{"success": false}\n', encoding="utf-8")
    assert compute_run_stats([{"text": "Beitrag"}], run_dir=bare)["action_log_status"] == "ohne_aktionen"
    service = EnsembleService(
        runner_cls=NoActionLogRunner, llm_factory=FakeLLM,
        root=tmp_path / "ensembles", poll_interval=0.001,
    )
    started = service.start("sim_test", 1, 2, ["baseline"], min_posts=5)
    state = _wait_ensemble(service, started["ensemble_id"])
    assert state["status"] == "failed", state.get("error")
    assert "Beiträge" in (state.get("error") or "")
    assert "Aktionslog fehlt" in (state.get("error") or "")
    assert "attempts_exhausted" in (state.get("error") or "")
    assert state["attempts_exhausted"] is True
    assert len(NoActionLogRunner.calls) == SEED_ATTEMPTS
    stored = service._load(started["ensemble_id"])
    assert stored["seed_attempts"]["baseline:1"] == SEED_ATTEMPTS


def _running_ensemble(tmp_path, ensemble_id="ens_cccccccccccc", owner_pid=None):
    path = tmp_path / "ensembles" / ensemble_id / "ensemble.json"
    path.parent.mkdir(parents=True)
    state = {
        "ensemble_id": ensemble_id, "status": "running",
        "current": {"variant": "baseline", "run": 1, "attempt": 1},
        "seed_attempts": {"baseline:1": 1},
    }
    if owner_pid is not None:
        state["owner_pid"] = owner_pid
    path.write_text(json.dumps(state), encoding="utf-8")
    return path


def test_stale_sweep_ignores_runs_written_after_backend_start(tmp_path):
    service = EnsembleService(root=tmp_path / "ensembles")
    _running_ensemble(tmp_path)
    assert service.mark_stale_runs() == 0
    assert service._load("ens_cccccccccccc")["status"] == "running"


def test_stale_sweep_ignores_run_state_written_after_backend_start(tmp_path, monkeypatch):
    service = EnsembleService(root=tmp_path / "ensembles")
    path = _running_ensemble(tmp_path)
    run_state = path.parent / "baseline" / "run_1" / "run_state.json"
    run_state.parent.mkdir(parents=True)
    run_state.write_text("{}", encoding="utf-8")
    old = time.time() - 600
    os.utime(path, (old, old))
    monkeypatch.setattr(ensemble_module, "PROCESS_START_TIME", time.time() - 60)
    assert service.mark_stale_runs() == 0


def test_stale_sweep_ignores_ensemble_of_live_foreign_process(tmp_path, monkeypatch):
    service = EnsembleService(root=tmp_path / "ensembles")
    path = _running_ensemble(tmp_path, owner_pid=os.getppid())
    monkeypatch.setattr(ensemble_module, "PROCESS_START_TIME", time.time() + 60)
    assert os.getppid() != os.getpid()
    assert service.mark_stale_runs() == 0
    path.write_text(path.read_text().replace(str(os.getppid()), "999999999"), encoding="utf-8")
    assert service.mark_stale_runs() == 1


def test_stale_sweep_ignores_ensemble_with_live_thread(tmp_path, monkeypatch):
    import threading
    service = EnsembleService(root=tmp_path / "ensembles")
    _running_ensemble(tmp_path)
    monkeypatch.setattr(ensemble_module, "PROCESS_START_TIME", time.time() + 60)
    release = threading.Event()
    thread = threading.Thread(target=release.wait, daemon=True)
    thread.start()
    service._threads["ens_cccccccccccc"] = thread
    try:
        assert service.mark_stale_runs() == 0
    finally:
        release.set()
        thread.join()
        service._threads.pop("ens_cccccccccccc", None)
    assert service.mark_stale_runs() == 1


def _orphan_setup(tmp_path, monkeypatch):
    service = EnsembleService(root=tmp_path / "ensembles")
    ensemble_id = "ens_dddddddddddd"
    run_dir = tmp_path / "ensembles" / ensemble_id / "baseline" / "run_1"
    run_dir.mkdir(parents=True)
    (run_dir / "run_state.json").write_text(json.dumps({"process_pid": 4321}), encoding="utf-8")
    monkeypatch.setattr(ensemble_module.os, "readlink", lambda _path: str(run_dir))
    monkeypatch.setattr(Path, "read_bytes", lambda _path: b"python run_parallel_simulation.py\0")
    return service, run_dir


def test_orphan_kill_skips_own_process_group(tmp_path, monkeypatch):
    service, run_dir = _orphan_setup(tmp_path, monkeypatch)
    sent = []
    monkeypatch.setattr(ensemble_module.os, "getpgid", lambda pid: os.getpgrp())
    monkeypatch.setattr(ensemble_module.os, "killpg", lambda pgid, sig: sent.append(("pg", sig)))
    monkeypatch.setattr(ensemble_module.os, "kill", lambda pid, sig: sent.append((pid, sig)))
    monkeypatch.setattr(EnsembleService, "_wait_gone", staticmethod(lambda pid, s: True))
    assert service._kill_oasis_in_run_dir(run_dir) is True
    assert all(entry[0] != "pg" for entry in sent)


def test_orphan_kill_escalates_to_sigkill_after_wait(tmp_path, monkeypatch):
    service, run_dir = _orphan_setup(tmp_path, monkeypatch)
    sent, waits = [], []
    monkeypatch.setattr(ensemble_module.os, "getpgid", lambda pid: 7777)
    monkeypatch.setattr(ensemble_module.os, "killpg", lambda pgid, sig: sent.append(sig))

    def wait(pid, seconds):
        waits.append(seconds)
        return False

    monkeypatch.setattr(EnsembleService, "_wait_gone", staticmethod(wait))
    assert service._kill_oasis_in_run_dir(run_dir) is True
    assert sent == [ensemble_module.signal.SIGTERM, ensemble_module.signal.SIGKILL]
    assert waits[0] == ensemble_module.ORPHAN_TERM_WAIT_SECONDS


def test_orphan_kill_no_sigkill_when_process_exits(tmp_path, monkeypatch):
    service, run_dir = _orphan_setup(tmp_path, monkeypatch)
    sent = []
    monkeypatch.setattr(ensemble_module.os, "getpgid", lambda pid: 7777)
    monkeypatch.setattr(ensemble_module.os, "killpg", lambda pgid, sig: sent.append(sig))
    monkeypatch.setattr(EnsembleService, "_wait_gone", staticmethod(lambda pid, s: True))
    assert service._kill_oasis_in_run_dir(run_dir) is True
    assert sent == [ensemble_module.signal.SIGTERM]


def test_create_app_skips_stale_sweep_on_switch(tmp_path):
    import subprocess
    import sys
    backend = Path(__file__).resolve().parents[1]
    script = (
        "import os\n"
        "from unittest.mock import patch\n"
        "from app import create_app\n"
        "from app.config import Config\n"
        "Config.TESTING = True\n"
        "calls = []\n"
        "with patch('app.api.ensemble.mark_stale_ensembles', lambda: calls.append('ens')), "
        "patch('app.api.pipeline.mark_stale_runs', lambda: calls.append('pipe')), "
        "patch('app.api.system.list_models', return_value=(True, [])):\n"
        "    create_app(Config)\n"
        "print('CALLS=' + ','.join(calls))\n"
    )

    def run(value):
        env = {**os.environ, "UPLOAD_FOLDER": str(tmp_path)}
        env.pop("MIROFISH_SKIP_STALE_SWEEP", None)
        if value:
            env["MIROFISH_SKIP_STALE_SWEEP"] = value
        done = subprocess.run([sys.executable, "-c", script], cwd=backend, env=env,
                              capture_output=True, text=True, timeout=120)
        assert done.returncode == 0, done.stderr
        return next(line for line in done.stdout.splitlines() if line.startswith('CALLS='))[6:]

    assert run("1") == ""
    assert run("") == "ens,pipe"
