"""Regressionstests: Altstände, Teilbarkeit, Docker-Start, Port-Vorrang, Stimulus-seen."""

import csv
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from app.services.ensemble import EnsembleService, ensemble_markdown, prepare_run_directory
from app.services.stimulus_delivery import deliver_opening_stimulus_checked

ROOT = Path(__file__).resolve().parents[2]


def _source(tmp_path, minutes=30):
    src = tmp_path / "src"
    src.mkdir()
    cfg = {"time_config": {"minutes_per_round": minutes}, "agent_configs": []}
    (src / "simulation_config.json").write_text(json.dumps(cfg), encoding="utf-8")
    (src / "reddit_profiles.json").write_text("[]", encoding="utf-8")
    with (src / "twitter_profiles.csv").open("w", newline="", encoding="utf-8") as h:
        csv.DictWriter(h, fieldnames=["user_id"]).writeheader()
    return src


def test_old_ensemble_keeps_config_minutes(tmp_path):
    config = prepare_run_directory(
        _source(tmp_path), tmp_path / "run", "baseline", 24, 7, None
    )
    assert config["time_config"]["minutes_per_round"] == 30


def test_old_ensemble_report_claims_no_takt():
    state = {"status": "completed", "runs": 2, "hours": 24, "variants": [], "checklist": [], "primary_outcome_id": None}
    text = ensemble_markdown(state)
    assert "Rundentakt" not in text


def test_hours_must_be_divisible_by_takt(tmp_path):
    service = EnsembleService(root=tmp_path / "e")
    with pytest.raises(ValueError, match="teilbar"):
        service.start("sim_x", 1, 3, ["baseline"], minutes_per_round=120)
    with pytest.raises(ValueError, match="teilbar"):
        service.start("sim_x", 1, 6, ["baseline"], minutes_per_round=240)


def test_api_returns_400_for_indivisible_hours(tmp_path, monkeypatch):
    from app.api import ensemble as api

    monkeypatch.setattr(api, "service", EnsembleService(root=tmp_path / "e"))
    from flask import Flask

    app = Flask(__name__)
    app.register_blueprint(api.ensemble_bp, url_prefix="/api/ensemble")
    response = app.test_client().post(
        "/api/ensemble/start",
        json={"simulation_id": "sim_x", "hours": 5, "minutes_per_round": 120},
    )
    assert response.status_code == 400
    assert "teilbar" in response.get_json()["error"]


def test_script_defaults_are_unified():
    for name in ("run_parallel", "run_reddit", "run_twitter"):
        text = (ROOT / "backend/scripts" / f"{name}_simulation.py").read_text(encoding="utf-8")
        assert not re.search(r"""get\(['"]minutes_per_round['"], 30\)""", text)


def test_compose_does_not_create_missing_host_paths():
    text = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert len(re.findall(r"^\s+create_host_path: false$", text, re.M)) == 2
    assert "./.env:/app/.env.initial" not in text


def test_start_script_creates_env_and_data_before_compose(tmp_path):
    proj = tmp_path / "proj"
    (proj / "scripts").mkdir(parents=True)
    (proj / "scripts" / "start.sh").write_bytes((ROOT / "scripts/start.sh").read_bytes())
    (proj / ".env.example").write_text("A=1\n", encoding="utf-8")
    fake = tmp_path / "bin"
    fake.mkdir()
    docker = fake / "docker"
    docker.write_text('#!/bin/sh\necho "$@" > "$PWD/docker_args"\n', encoding="utf-8")
    docker.chmod(docker.stat().st_mode | stat.S_IXUSR)
    env = dict(os.environ, PATH=f"{fake}:{os.environ['PATH']}")
    subprocess.run(["sh", str(proj / "scripts/start.sh")], check=True, env=env)
    assert (proj / ".env").is_file() and (proj / "data").is_dir()
    assert (proj / "docker_args").read_text().startswith("compose up -d")


def test_container_flask_port_wins_over_copied_env():
    # Nach dem Import von app.config muss der Prozesswert gelten
    code = (
        "import os;os.environ['FLASK_PORT']='5001';"
        "import app.config;"
        "print(os.environ['FLASK_PORT'])"
    )
    env_path = ROOT / ".env"
    if env_path.exists():
        pytest.skip("echte .env vorhanden – nicht überschreiben")
    env_path.write_text("FLASK_PORT=9999\n", encoding="utf-8")
    try:
        out = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True,
            cwd=ROOT / "backend", check=True,
        ).stdout.strip()
    finally:
        env_path.unlink()
    assert out == "5001"


def test_entrypoint_strips_flask_port_from_copy():
    text = (ROOT / "docker-entrypoint.sh").read_text(encoding="utf-8")
    assert "FLASK_" in text and "grep -v" in text


def test_stimulus_seen_false_when_update_memory_fails(tmp_path):
    class Good:
        def update_memory(self, message, role):
            pass

    class Bad:
        def update_memory(self, message, role):
            raise RuntimeError("kaputt")

    class Graph:
        def get_agents(self):
            return [(0, Good()), (1, Bad())]

    log = tmp_path / "s.json"
    doc = deliver_opening_stimulus_checked(
        Graph(), [{"post_id": 1, "user_id": 0, "content": "x"}], log, "twitter"
    )
    assert [a["seen"] for a in doc["agents"]] == [True, False]
    assert doc["agents"][1]["error"] == "kaputt"
    assert json.loads(log.read_text())["agents"][1]["seen"] is False
