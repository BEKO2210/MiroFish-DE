"""Kaskadierendes Aufräumen: richtige Ordner weg, Nachbarprojekt und Laufendes bleiben."""
import json
from datetime import datetime, timedelta

import pytest

from app.config import Config
from app.services.cleanup import (
    CleanupBusy,
    CleanupError,
    delete_pipeline_cascade,
    delete_project_cascade,
    delete_simulation_cascade,
    sweep_orphans,
)

P1 = "proj_aaa111"
P2 = "proj_bbb222"
G1 = "11111111-1111-4111-8111-111111111111"
G2 = "22222222-2222-4222-8222-222222222222"
S1 = "sim_aaa111"
S1B = "sim_aaabbb"
S2 = "sim_bbb222"
R1 = "report_aaa111"
R1B = "report_aaabbb"
R2 = "report_bbb222"
RUN1 = "run_aaa111"
RUN1B = "run_aaabbb"
RUN2 = "run_bbb222"


@pytest.fixture
def upload(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(tmp_path))
    monkeypatch.setattr(Config, "MEMORY_PROVIDER", "obsidian")
    return tmp_path


def _dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def make_project(root, project_id, graph_id, created_at):
    base = root / "projects" / project_id
    (base / "files").mkdir(parents=True)
    (base / "files" / "a.txt").write_text("datei", encoding="utf-8")
    (base / "extracted_text.txt").write_text("text", encoding="utf-8")
    _dump(base / "project.json", {
        "project_id": project_id,
        "graph_id": graph_id,
        "created_at": created_at,
        "name": "Projekt",
    })
    vault = root / "simulations" / graph_id / "vault" / "index"
    vault.mkdir(parents=True, exist_ok=True)
    (vault / "graph_info.json").write_text("{}", encoding="utf-8")


def make_sim(root, simulation_id, project_id, graph_id):
    base = root / "simulations" / simulation_id
    base.mkdir(parents=True, exist_ok=True)
    state = {
        "simulation_id": simulation_id,
        "project_id": project_id,
        "graph_id": graph_id,
        "status": "completed",
    }
    _dump(base / "state.json", state)
    _dump(base / "simulation_config.json", {"project_id": project_id, "graph_id": graph_id})


def make_report(root, report_id, simulation_id, meta_name="metadata.json"):
    base = root / "reports" / report_id
    base.mkdir(parents=True, exist_ok=True)
    _dump(base / meta_name, {"report_id": report_id, "simulation_id": simulation_id})
    (base / "full_report.md").write_text("# Bericht", encoding="utf-8")


def make_run(root, run_id, status="failed", **fields):
    folder = root / "pipelines" / run_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "dokument.txt").write_text("upload", encoding="utf-8")
    state = {
        "pipeline_id": run_id,
        "status": status,
        "project_id": None,
        "graph_id": None,
        "simulation_id": None,
        "report_id": None,
    }
    state.update(fields)
    _dump(root / "pipelines" / f"{run_id}.json", state)


def test_cascade_removes_only_the_finished_simulation(upload):
    now = datetime.now().isoformat()
    make_project(upload, P1, G1, now)
    make_project(upload, P2, G2, now)
    make_sim(upload, S1, P1, G1)
    make_sim(upload, S1B, P1, G1)
    make_sim(upload, S2, P2, G2)
    make_report(upload, R1, S1, "metadata.json")
    make_report(upload, R1B, S1B, "meta.json")
    make_report(upload, R2, S2, "metadata.json")
    make_run(upload, RUN1, status="failed", project_id=P1, graph_id=G1, simulation_id=S1, report_id=R1)
    make_run(upload, RUN1B, status="completed", project_id=P1, graph_id=G1, simulation_id=S1B, report_id=R1B)
    make_run(upload, RUN2, status="completed", project_id=P2, graph_id=G2, simulation_id=S2, report_id=R2)

    removed = delete_simulation_cascade(S1)
    assert f"simulation:{S1}" in removed
    assert f"report:{R1}" in removed
    assert f"pipeline:{RUN1}" in removed
    assert f"project:{P1}" not in removed
    assert not (upload / "simulations" / S1).exists()
    assert not (upload / "reports" / R1).exists()
    assert not (upload / "pipelines" / f"{RUN1}.json").exists()
    assert not (upload / "pipelines" / RUN1).exists()
    # Zweite Simulation desselben Projekts hält Projekt und Graph.
    assert (upload / "projects" / P1 / "extracted_text.txt").is_file()
    assert (upload / "simulations" / G1 / "vault" / "index" / "graph_info.json").is_file()
    assert (upload / "simulations" / S1B / "state.json").is_file()
    assert (upload / "reports" / R1B / "full_report.md").is_file()
    assert (upload / "pipelines" / f"{RUN1B}.json").is_file()
    assert (upload / "pipelines" / RUN1B / "dokument.txt").is_file()
    # Anderes Projekt bleibt vollständig.
    assert (upload / "projects" / P2 / "files" / "a.txt").is_file()
    assert (upload / "simulations" / S2).is_dir()
    assert (upload / "simulations" / G2 / "vault").is_dir()
    assert (upload / "reports" / R2).is_dir()
    assert (upload / "pipelines" / RUN2 / "dokument.txt").is_file()

    removed = delete_simulation_cascade(S1B)
    assert f"simulation:{S1B}" in removed
    assert f"report:{R1B}" in removed
    assert f"pipeline:{RUN1B}" in removed
    assert f"project:{P1}" in removed
    assert f"graph:{G1}" in removed
    assert not (upload / "projects" / P1).exists()
    assert not (upload / "simulations" / G1).exists()
    assert not (upload / "simulations" / S1B).exists()
    assert (upload / "projects" / P2).is_dir()
    assert (upload / "simulations" / S2).is_dir()
    assert (upload / "simulations" / G2).is_dir()


def test_pipeline_cascade_removes_its_project(upload):
    now = datetime.now().isoformat()
    make_project(upload, P1, G1, now)
    make_project(upload, P2, G2, now)
    make_sim(upload, S1, P1, G1)
    make_sim(upload, S2, P2, G2)
    make_report(upload, R1, S1)
    make_report(upload, R2, S2)
    make_run(upload, RUN1, status="failed", project_id=P1, graph_id=G1, simulation_id=S1, report_id=R1)
    make_run(upload, RUN2, status="failed", project_id=P2, graph_id=G2, simulation_id=S2, report_id=R2)

    removed = delete_pipeline_cascade(RUN1)
    assert f"pipeline:{RUN1}" in removed
    assert f"simulation:{S1}" in removed
    assert f"project:{P1}" in removed
    assert f"graph:{G1}" in removed
    assert not (upload / "pipelines" / f"{RUN1}.json").exists()
    assert not (upload / "projects" / P1).exists()
    assert not (upload / "simulations" / S1).exists()
    assert not (upload / "simulations" / G1).exists()
    assert not (upload / "reports" / R1).exists()
    assert (upload / "projects" / P2 / "project.json").is_file()
    assert (upload / "pipelines" / f"{RUN2}.json").is_file()
    assert (upload / "simulations" / S2).is_dir()
    assert (upload / "simulations" / G2).is_dir()


@pytest.mark.parametrize("call,bad", [
    (delete_simulation_cascade, "../etc"),
    (delete_simulation_cascade, "sim_../abc"),
    (delete_simulation_cascade, "sim_ABC"),
    (delete_simulation_cascade, "proj_aaa111"),
    (delete_simulation_cascade, "sim_aaa111/../../etc"),
    (delete_project_cascade, "../"),
    (delete_project_cascade, "proj_AAA"),
    (delete_project_cascade, "not_a_project"),
    (delete_pipeline_cascade, "run_../x"),
    (delete_pipeline_cascade, "pipeline_1"),
    (delete_pipeline_cascade, "run_XYZ"),
])
def test_rejects_path_and_foreign_ids(upload, call, bad):
    now = datetime.now().isoformat()
    make_project(upload, P2, G2, now)
    make_sim(upload, S2, P2, G2)
    with pytest.raises(CleanupError):
        call(bad)
    assert (upload / "projects" / P2 / "extracted_text.txt").is_file()
    assert (upload / "simulations" / S2 / "state.json").is_file()
    assert (upload / "simulations" / G2 / "vault").is_dir()


def test_symlink_outside_upload_is_not_followed(upload):
    outside = upload.parent / "secret-outside"
    outside.mkdir()
    (outside / "keep.txt").write_text("geheim", encoding="utf-8")
    link_parent = upload / "simulations"
    link_parent.mkdir()
    (link_parent / "sim_abcdef").symlink_to(outside)
    with pytest.raises(CleanupError):
        delete_simulation_cascade("sim_abcdef")
    assert (outside / "keep.txt").read_text(encoding="utf-8") == "geheim"
    assert outside.is_dir()


def test_sweep_deletes_only_old_and_unreferenced(upload):
    old = (datetime.now() - timedelta(hours=48)).isoformat()
    young = (datetime.now() - timedelta(hours=1)).isoformat()
    g_old = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    g_young = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
    g_keep = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
    g_run = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
    g_orphan = "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"
    p_old = "proj_01d111"
    p_young = "proj_a10001"
    p_keep = "proj_0e0011"
    p_run = "proj_0c0111"
    sim_keep = "sim_0e0011"
    sim_run = "sim_0c0111"
    run_live = "run_11fe11"

    make_project(upload, p_old, g_old, old)
    make_project(upload, p_young, g_young, young)
    make_project(upload, p_keep, g_keep, old)
    make_sim(upload, sim_keep, p_keep, g_keep)
    make_project(upload, p_run, g_run, old)
    make_sim(upload, sim_run, p_run, g_run)
    make_run(upload, run_live, status="running", project_id=p_run, graph_id=g_run, simulation_id=sim_run)
    orphan = upload / "simulations" / g_orphan / "vault"
    orphan.mkdir(parents=True)
    (orphan / "note.md").write_text("alt", encoding="utf-8")
    junk = upload / "simulations" / "not-a-graph"
    junk.mkdir()
    (junk / "x.txt").write_text("bleiben", encoding="utf-8")
    (upload / "projects" / "fremd").mkdir()
    (upload / "projects" / "fremd" / "x.txt").write_text("bleiben", encoding="utf-8")

    removed = sweep_orphans()
    assert f"project:{p_old}" in removed
    assert f"graph:{g_old}" in removed
    assert f"graph:{g_orphan}" in removed
    assert not (upload / "projects" / p_old).exists()
    assert not (upload / "simulations" / g_old).exists()
    assert not (upload / "simulations" / g_orphan).exists()
    # Junges Projekt ohne Simulation bleibt, sein Graph ebenfalls.
    assert (upload / "projects" / p_young / "project.json").is_file()
    assert (upload / "simulations" / g_young / "vault").is_dir()
    # Projekt mit Simulation bleibt.
    assert (upload / "projects" / p_keep).is_dir()
    assert (upload / "simulations" / sim_keep / "state.json").is_file()
    assert (upload / "simulations" / g_keep / "vault").is_dir()
    # Laufender Durchlauf, sein Projekt und seine Simulation bleiben.
    assert (upload / "pipelines" / f"{run_live}.json").is_file()
    assert (upload / "pipelines" / run_live / "dokument.txt").is_file()
    assert (upload / "projects" / p_run).is_dir()
    assert (upload / "simulations" / sim_run).is_dir()
    assert (upload / "simulations" / g_run / "vault").is_dir()
    assert (junk / "x.txt").is_file()
    assert (upload / "projects" / "fremd" / "x.txt").is_file()

    with pytest.raises(CleanupBusy):
        delete_pipeline_cascade(run_live)
    with pytest.raises(CleanupBusy):
        delete_simulation_cascade(sim_run)
    assert (upload / "pipelines" / f"{run_live}.json").is_file()
    assert (upload / "pipelines" / run_live / "dokument.txt").is_file()
    assert (upload / "projects" / p_run / "project.json").is_file()
    assert (upload / "simulations" / sim_run / "state.json").is_file()
