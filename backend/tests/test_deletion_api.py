"""HTTP-Vertrag und Herkunftsfelder des Löschschutzes (ohne externe Dienste)."""
import json

from flask import Flask

from app.config import Config
from app.models.project import ProjectManager
from app.models.task import TaskManager, TaskStatus
from app.services.simulation_manager import SimulationManager


def _simulation_app():
    from app.api.simulation import get_prepare_status, get_simulation

    app = Flask(__name__)
    app.add_url_rule("/api/simulation/prepare/status", view_func=get_prepare_status,
                     methods=["POST"])
    app.add_url_rule("/api/simulation/<simulation_id>", view_func=get_simulation, methods=["GET"])
    return app


def test_unknown_simulation_is_404_for_prepare_status_and_get(tmp_path, monkeypatch):
    simulations = tmp_path / "simulations"
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(tmp_path))
    monkeypatch.setattr(SimulationManager, "SIMULATION_DATA_DIR", str(simulations))
    client = _simulation_app().test_client()

    response = client.post("/api/simulation/prepare/status", json={"simulation_id": "sim_abcdef"})
    assert response.status_code == 404
    assert "nicht gefunden" in response.get_json()["error"]
    response = client.get("/api/simulation/sim_abcdef")
    assert response.status_code == 404


def test_source_is_persisted_and_exposed_by_project_and_simulation(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(tmp_path))
    monkeypatch.setattr(ProjectManager, "PROJECTS_DIR", str(tmp_path / "projects"))
    monkeypatch.setattr(SimulationManager, "SIMULATION_DATA_DIR", str(tmp_path / "simulations"))

    project = ProjectManager.create_project("Realitätsabgleich", source="validierung")
    simulation = SimulationManager().create_simulation(
        project.project_id, "11111111-1111-4111-8111-111111111111", source=project.source
    )
    stored_project = json.loads(
        (tmp_path / "projects" / project.project_id / "project.json").read_text(encoding="utf-8")
    )
    stored_simulation = json.loads(
        (tmp_path / "simulations" / simulation.simulation_id / "state.json").read_text(encoding="utf-8")
    )
    assert stored_project["source"] == "validierung"
    assert stored_simulation["source"] == "validierung"
    # Diese Dictionaries sind zugleich die Grundlage der Projektliste und von /simulation/history.
    assert ProjectManager.get_project(project.project_id).to_dict()["source"] == "validierung"
    assert SimulationManager().get_simulation(simulation.simulation_id).to_dict()["source"] == "validierung"


def test_pipeline_list_returns_source(tmp_path, monkeypatch):
    from app.api import pipeline as pipeline_api

    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(tmp_path))
    pipeline = tmp_path / "pipelines"
    pipeline.mkdir()
    (pipeline / "run_aaaaaaaaaaaa.json").write_text(json.dumps({
        "pipeline_id": "run_aaaaaaaaaaaa", "status": "completed",
        "created_at": "2026-10-14T22:20:00", "source": "validierung",
    }), encoding="utf-8")
    app = Flask(__name__)
    app.add_url_rule("/api/pipeline/list", view_func=pipeline_api.pipeline_list, methods=["GET"])
    response = app.test_client().get("/api/pipeline/list")
    assert response.status_code == 200
    assert response.get_json()["data"][0]["source"] == "validierung"


def test_delete_routes_return_409_before_mutating_active_objects(tmp_path, monkeypatch):
    from app.api.graph import delete_project
    from app.api.pipeline import delete_pipeline
    from app.api.simulation import delete_simulation

    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(tmp_path))
    monkeypatch.setattr(ProjectManager, "PROJECTS_DIR", str(tmp_path / "projects"))
    monkeypatch.setattr(SimulationManager, "SIMULATION_DATA_DIR", str(tmp_path / "simulations"))
    project_id, simulation_id, run_id = "proj_abcdef", "sim_abcdef", "run_abcdef"
    project_dir = tmp_path / "projects" / project_id
    simulation_dir = tmp_path / "simulations" / simulation_id
    pipeline_dir = tmp_path / "pipelines"
    project_dir.mkdir(parents=True)
    simulation_dir.mkdir(parents=True)
    pipeline_dir.mkdir(parents=True)
    (project_dir / "project.json").write_text(json.dumps({
        "project_id": project_id, "name": "P", "status": "graph_completed",
        "created_at": "2026-10-14T20:00:00", "updated_at": "2026-10-14T20:00:00",
    }), encoding="utf-8")
    (simulation_dir / "state.json").write_text(json.dumps({
        "simulation_id": simulation_id, "project_id": project_id, "graph_id": "graph",
        "status": "preparing",
    }), encoding="utf-8")
    (pipeline_dir / f"{run_id}.json").write_text(json.dumps({
        "pipeline_id": run_id, "status": "failed", "project_id": project_id,
        "simulation_id": simulation_id, "graph_id": "graph",
    }), encoding="utf-8")

    tasks = TaskManager()
    tasks._tasks.clear()
    task_id = tasks.create_task("simulation_prepare", {
        "simulation_id": simulation_id, "project_id": project_id,
    })
    tasks.update_task(task_id, status=TaskStatus.PROCESSING)
    app = Flask(__name__)
    app.add_url_rule("/api/simulation/<simulation_id>", view_func=delete_simulation,
                     methods=["DELETE"])
    app.add_url_rule("/api/graph/project/<project_id>", view_func=delete_project,
                     methods=["DELETE"])
    app.add_url_rule("/api/pipeline/<pid>", view_func=delete_pipeline, methods=["DELETE"])
    client = app.test_client()

    for path in (f"/api/simulation/{simulation_id}", f"/api/graph/project/{project_id}",
                 f"/api/pipeline/{run_id}"):
        response = client.delete(path)
        assert response.status_code == 409
        assert "Abschluss oder Abbruch" in response.get_json()["error"] or "vorbereitet" in response.get_json()["error"]
    assert (project_dir / "project.json").is_file()
    assert (simulation_dir / "state.json").is_file()
    assert (pipeline_dir / f"{run_id}.json").is_file()
    tasks._tasks.clear()
