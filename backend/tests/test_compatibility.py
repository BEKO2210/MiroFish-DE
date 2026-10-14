import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def legacy_uploads(tmp_path):
    """Small synthetic copy of the persisted layouts seen before V2."""
    uploads = tmp_path / "uploads"
    simulation_id = "sim_0123456789ab"
    simulation = uploads / "simulations" / simulation_id
    simulation.mkdir(parents=True)
    (simulation / "state.json").write_text(json.dumps({
        "simulation_id": simulation_id,
        "project_id": "proj_0123456789ab",
        "graph_id": "mirofish_0123456789abcdef",
        "status": "completed",
        "config_generated": True,
        # profiles_generated was absent in one persisted legacy variant.
        "profiles_count": 1,
    }), encoding="utf-8")
    (simulation / "simulation_config.json").write_text(json.dumps({
        "simulation_requirement": "Anonymisierte Testfrage",
        "time_config": {"total_simulation_hours": 1, "minutes_per_round": 60},
        "agent_configs": [],
        "event_config": {"initial_posts": [], "hot_topics": []},
    }), encoding="utf-8")
    (simulation / "reddit_profiles.json").write_text(json.dumps([
        {"user_id": 1, "name": "Testrolle"}
    ]), encoding="utf-8")
    (simulation / "run_state.json").write_text(json.dumps({
        "simulation_id": simulation_id,
        "runner_status": "completed",
        "current_round": 1,
        "total_rounds": 1,
    }), encoding="utf-8")
    connection = sqlite3.connect(simulation / "reddit_simulation.db")
    connection.execute("CREATE TABLE post (id INTEGER, content TEXT, created_at TEXT)")
    connection.execute("INSERT INTO post VALUES (1, 'Anonymisierter Beitrag', '2025-01-01')")
    connection.commit()
    connection.close()

    report_id = "report_0123456789ab"
    report = uploads / "reports" / report_id
    report.mkdir(parents=True)
    (report / "meta.json").write_text(json.dumps({
        "report_id": report_id,
        "simulation_id": simulation_id,
        "graph_id": "mirofish_0123456789abcdef",
        "simulation_requirement": "Anonymisierte Testfrage",
        "status": "completed",
        "outline": None,
        "markdown_content": "# Anonymisierter Bericht",
        # Legacy reports did not persist methodology.
        "created_at": "2025-01-01T00:00:00",
        "completed_at": "2025-01-01T00:01:00",
        "error": None,
    }), encoding="utf-8")
    (report / "progress.json").write_text(json.dumps({
        "status": "completed", "progress": 100
    }), encoding="utf-8")
    return uploads


def test_legacy_read_endpoints_honor_configured_upload_folder(legacy_uploads):
    backend = Path(__file__).resolve().parents[1]
    script = r'''
import os
from unittest.mock import patch
from app import create_app
from app.config import Config

Config.TESTING = True
Config.UPLOAD_FOLDER = os.environ["COMPAT_FIXTURE"]
Config.OASIS_SIMULATION_DATA_DIR = os.path.join(Config.UPLOAD_FOLDER, "simulations")
with patch("app.services.cleanup.sweep_orphans", return_value=[]), patch(
    "app.api.system.list_models", return_value=(True, [])
):
    client = create_app(Config).test_client()
    checks = (
        client.get("/api/simulation/sim_0123456789ab"),
        client.get("/api/simulation/sim_0123456789ab/profiles"),
        client.get("/api/simulation/sim_0123456789ab/config"),
        client.get("/api/simulation/sim_0123456789ab/run-status"),
        client.get("/api/simulation/sim_0123456789ab/posts"),
        client.get("/api/report/generate/status?report_id=report_0123456789ab"),
    )
    assert [response.status_code for response in checks] == [200, 200, 200, 200, 200, 200]
    assert checks[1].get_json()["data"]["count"] == 1
    assert checks[3].get_json()["data"]["runner_status"] == "completed"
    assert checks[4].get_json()["data"]["total"] == 1
    status = checks[5].get_json()["data"]
    assert status["status"] == "completed"
    assert status["already_completed"] is True
'''
    env = dict(os.environ, COMPAT_FIXTURE=str(legacy_uploads))
    result = subprocess.run(
        [sys.executable, "-c", script], cwd=backend, env=env,
        text=True, capture_output=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
