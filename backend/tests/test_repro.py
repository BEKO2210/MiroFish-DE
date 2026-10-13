"""Reproduzierbarkeit: Plattform-RNG, Manifest-Hashes, Aktionsabstand."""
import json
import sys
from pathlib import Path

import pytest

from app.config import Config
from app.services.report_validation import build_manifest

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from repro_check import (  # noqa: E402
    compare_action_logs,
    load_actions,
    normalize_text,
    sequential_identity,
    text_jaccard,
)
from repro_seed import (  # noqa: E402
    make_platform_numpy,
    make_platform_rng,
    platform_seed,
)


def test_platform_streams_deterministic_and_independent():
    seed = 12345
    tw_a = make_platform_rng(seed, "twitter")
    tw_b = make_platform_rng(seed, "twitter")
    rd = make_platform_rng(seed, "reddit")
    assert platform_seed(seed, "twitter") != platform_seed(seed, "reddit")
    seq_tw = [tw_a.random() for _ in range(20)]
    assert [tw_b.random() for _ in range(20)] == seq_tw
    seq_rd = [rd.random() for _ in range(20)]
    assert seq_rd != seq_tw
    # Interleaved draws must not affect the other stream
    tw2 = make_platform_rng(seed, "twitter")
    rd2 = make_platform_rng(seed, "reddit")
    mixed_tw, mixed_rd = [], []
    for _ in range(10):
        mixed_tw.append(tw2.random())
        mixed_rd.append(rd2.random())
    assert mixed_tw == seq_tw[:10]
    assert mixed_rd == seq_rd[:10]


def test_platform_numpy_deterministic():
    np_tw = make_platform_numpy(99, "twitter")
    np_rd = make_platform_numpy(99, "reddit")
    if np_tw is None:
        pytest.skip("numpy nicht installiert")
    a = np_tw.random(5)
    b = make_platform_numpy(99, "twitter").random(5)
    assert list(a) == list(b)
    assert list(np_rd.random(5)) != list(a)


def test_manifest_hashes_from_real_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(tmp_path))
    # Ensemble-artiger Pfad — nicht uploads/simulations/<id>
    sim = tmp_path / "ensembles" / "ens_x" / "baseline" / "run_1"
    sim.mkdir(parents=True)
    config = {
        "simulation_id": "ens_x_baseline_1",
        "simulation_requirement": "Was geschieht?",
        "event_config": {"initial_posts": [{"content": "Startimpuls", "poster_agent_id": 0}]},
        "agent_configs": [{"agent_id": 0}],
        "time_config": {"total_simulation_hours": 1, "minutes_per_round": 60},
    }
    (sim / "simulation_config.json").write_text(
        json.dumps(config, ensure_ascii=False), encoding="utf-8"
    )
    (sim / "state.json").write_text(
        json.dumps({"project_id": "proj_x", "simulation_requirement": "Was geschieht?"}),
        encoding="utf-8",
    )
    (sim / "twitter_profiles.csv").write_text("user_id,name\n0,Bot\n", encoding="utf-8")
    (sim / "reddit_profiles.json").write_text('[{"user_id": 0}]', encoding="utf-8")
    proj = tmp_path / "projects" / "proj_x"
    proj.mkdir(parents=True)
    (proj / "extracted_text.txt").write_text("Material", encoding="utf-8")
    (proj / "files").mkdir()
    (proj / "files" / "doc.md").write_text("# Doc", encoding="utf-8")

    # Falsche ID würde leeren Ordner treffen — sim_dir ist maßgeblich
    wrong = tmp_path / "simulations" / "ens_x_baseline_1"
    assert not wrong.exists()

    m = build_manifest(str(sim), seed=7, temperature=0.7)
    assert m["simulation_id"] == "ens_x_baseline_1"
    assert m["simulation_config_sha256"]
    assert m["initial_posts_sha256"]
    assert m["profile_sha256"]["twitter_profiles.csv"]
    assert m["profile_sha256"]["reddit_profiles.json"]
    assert m["question_sha256"]
    assert "doc.md" in m["document_sha256"]
    assert m["models"]["twitter"]
    assert m["models"]["reddit"]

    monkeypatch.setenv("LLM_BOOST_API_KEY", "boost-key")
    monkeypatch.setenv("LLM_BOOST_MODEL_NAME", "boost-model-x")
    m2 = build_manifest(str(sim), seed=7, temperature=0.7)
    assert m2["models"]["reddit"] == "boost-model-x"
    assert m2["models"]["twitter"] == m2["models"]["main"]
    assert m2["models"]["twitter"] != "boost-model-x"


def _write_actions(sim: Path, platform: str, rows: list) -> None:
    d = sim / platform
    d.mkdir(parents=True, exist_ok=True)
    with (d / "actions.jsonl").open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def test_action_distance_identical_and_divergent(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    actions = [
        {"event_type": "round_start", "round": 1},
        {
            "action_type": "CREATE_POST",
            "agent_id": 1,
            "action_args": {"content": "  Hallo   Welt "},
        },
        {
            "action_type": "LIKE_POST",
            "agent_id": 2,
            "action_args": {},
        },
        {"event_type": "round_end", "round": 1},
    ]
    _write_actions(a, "twitter", actions)
    _write_actions(b, "twitter", actions)
    _write_actions(a, "reddit", [])
    _write_actions(b, "reddit", [])

    m = compare_action_logs(a, b)
    assert m["count_a"] == 2
    assert m["sequential_identity"] == 1.0
    assert m["text_jaccard"] == 1.0
    assert normalize_text("  Hallo   Welt ") == "hallo welt"
    assert load_actions(a)[0][2] == "hallo welt"

    _write_actions(
        b,
        "twitter",
        [
            {
                "action_type": "CREATE_POST",
                "agent_id": 1,
                "action_args": {"content": "ganz anderer text"},
            },
            {
                "action_type": "LIKE_POST",
                "agent_id": 9,
                "action_args": {},
            },
        ],
    )
    m2 = compare_action_logs(a, b)
    assert m2["sequential_identity"] == 0.0
    assert m2["text_jaccard"] == 0.0

    assert sequential_identity([], []) == 1.0
    assert text_jaccard([], []) == 1.0
