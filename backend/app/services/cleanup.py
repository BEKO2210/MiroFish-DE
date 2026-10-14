"""
Kaskadierendes Aufräumen von Projekten, Simulationen, Berichten und Durchläufen.

Alles liegt unter Config.UPLOAD_FOLDER. Kennungen werden per Muster geprüft,
jeder Pfad per realpath auf den Upload-Ordner zurückgeführt, bevor gelöscht wird.
Rückgabe ist jeweils die Liste der entfernten Dinge (für Log und API).
"""

import json
import os
import re
import shutil
from datetime import datetime
from typing import Iterator, List, Optional, Tuple

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.cleanup')

# Kennungen, wie sie das Backend vergibt. Alles andere (vor allem "..") wird abgewiesen.
RE_PROJECT = re.compile(r"^proj_[0-9a-f]+$")
RE_SIM = re.compile(r"^sim_[0-9a-f]+$")
RE_REPORT = re.compile(r"^report_[A-Za-z0-9]+$")
RE_RUN = re.compile(r"^run_[0-9a-f]+$")
RE_UUID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

_RUNNER_ACTIVE = ("running", "paused", "starting", "stopping")
_TASK_ACTIVE = ("pending", "processing")
_ENSEMBLE_TERMINAL = ("completed", "failed", "cancelled")


class CleanupError(ValueError):
    """Kennung oder Pfad ist nicht zulässig."""


class CleanupBusy(RuntimeError):
    """Simulation oder Durchlauf läuft noch und darf nicht gelöscht werden."""


def _root() -> str:
    return os.path.realpath(Config.UPLOAD_FOLDER)


def _inside(real: str, root: Optional[str] = None) -> bool:
    root = root or _root()
    return real == root or real.startswith(root + os.sep)


def _require(value: str, pattern: re.Pattern) -> str:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise CleanupError("Ungültige Kennung")
    return value


def _child(parts: List[str], name: str) -> str:
    """Pfad root/parts/name. Symlinks und Ausbrüche aus dem Upload-Ordner werden abgewiesen."""
    if not name or name in (".", "..") or os.sep in name or "/" in name or "\\" in name:
        raise CleanupError("Ungültige Kennung")
    root = _root()
    parent = os.path.realpath(os.path.join(root, *parts))
    if not _inside(parent, root):
        raise CleanupError("Pfad liegt außerhalb des Upload-Ordners")
    lexical = os.path.normpath(os.path.join(parent, name))
    # Ein Symlink könnte auf einen Ordner außerhalb zeigen. Den folgen wir nicht.
    if os.path.islink(lexical):
        raise CleanupError("Pfad liegt außerhalb des Upload-Ordners")
    real = os.path.realpath(lexical)
    if os.path.dirname(real) != parent or not _inside(real, root) or real == root:
        raise CleanupError("Pfad liegt außerhalb des Upload-Ordners")
    return real


def _pipeline_json_path(run_id: str) -> str:
    root = _root()
    parent = os.path.realpath(os.path.join(root, "pipelines"))
    if not _inside(parent, root):
        raise CleanupError("Pfad liegt außerhalb des Upload-Ordners")
    lexical = os.path.normpath(os.path.join(parent, run_id + ".json"))
    if os.path.islink(lexical):
        raise CleanupError("Pfad liegt außerhalb des Upload-Ordners")
    real = os.path.realpath(lexical)
    if os.path.dirname(real) != parent or not _inside(real, root) or real == root:
        raise CleanupError("Pfad liegt außerhalb des Upload-Ordners")
    return real


def _rm_under(path: str) -> bool:
    """Löscht eine Datei oder einen Ordner, aber nie den Upload-Ordner selbst."""
    root = _root()
    if os.path.islink(path):
        raise CleanupError("Pfad liegt außerhalb des Upload-Ordners")
    real = os.path.realpath(path)
    if real == root or not _inside(real, root):
        raise CleanupError("Pfad liegt außerhalb des Upload-Ordners")
    if not os.path.exists(real):
        return False
    if os.path.isdir(real):
        shutil.rmtree(real)
    else:
        os.remove(real)
    return True


def _read_json(path: str) -> Optional[dict]:
    try:
        if not os.path.isfile(path) or os.path.islink(path):
            return None
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def _parse_time(value) -> Optional[datetime]:
    if not isinstance(value, str) or not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed


def _iter_pipelines() -> Iterator[Tuple[str, dict]]:
    folder = os.path.join(_root(), "pipelines")
    if not os.path.isdir(folder):
        return
    for name in os.listdir(folder):
        if not name.endswith(".json"):
            continue
        run_id = name[:-5]
        if not RE_RUN.fullmatch(run_id):
            continue
        try:
            data = _read_json(_pipeline_json_path(run_id)) or {}
        except CleanupError as exc:
            logger.warning(f"Durchlauf-Datei übersprungen ({run_id}): {exc}")
            continue
        yield run_id, data


def _pipeline_ids(simulation_id: Optional[str] = None, project_id: Optional[str] = None,
                  status: Optional[str] = None) -> List[str]:
    found = []
    for run_id, data in _iter_pipelines():
        if simulation_id is not None and data.get("simulation_id") != simulation_id:
            continue
        if project_id is not None and data.get("project_id") != project_id:
            continue
        if status is not None and data.get("status") != status:
            continue
        found.append(run_id)
    return found


def _active_task_reason(*, simulation_id: Optional[str] = None,
                        project_id: Optional[str] = None) -> Optional[str]:
    """Aktive In-Process-Aufgaben finden, bevor ihre Eingaben gelöscht werden."""
    try:
        from ..models.task import TaskManager
        tasks = TaskManager().list_tasks()
    except Exception as exc:
        logger.info(f"Aufgabenstatus nicht prüfbar: {exc}")
        return None
    for task in tasks:
        if task.get("status") not in _TASK_ACTIVE:
            continue
        metadata = task.get("metadata") or {}
        if simulation_id and metadata.get("simulation_id") == simulation_id:
            return "Die Simulation wird gerade vorbereitet. Löschen ist erst nach Abschluss oder Abbruch möglich."
        if project_id and metadata.get("project_id") == project_id:
            return "Das Projekt wird gerade verarbeitet. Löschen ist erst nach Abschluss oder Abbruch möglich."
    return None


def _active_ensemble_reason(*, simulation_id: Optional[str] = None,
                            project_id: Optional[str] = None) -> Optional[str]:
    """Nicht abgeschlossene Ensembles/Piloten schützen ihre Simulation und ihr Projekt."""
    folder = os.path.join(_root(), "ensembles")
    if not os.path.isdir(folder):
        return None
    for name in os.listdir(folder):
        if not re.fullmatch(r"ens_[0-9a-f]{12}", name):
            continue
        state = _read_json(os.path.join(folder, name, "ensemble.json")) or {}
        if state.get("status") in _ENSEMBLE_TERMINAL:
            continue
        referenced_simulation = state.get("simulation_id")
        if simulation_id and referenced_simulation == simulation_id:
            return f"Die Simulation wird vom nicht abgeschlossenen Ensemble/Pilot {name} verwendet."
        if project_id and isinstance(referenced_simulation, str):
            try:
                sim_dir = _child(["simulations"], referenced_simulation)
            except CleanupError:
                continue
            referenced_project, _ = _sim_links(sim_dir) if os.path.isdir(sim_dir) else (None, None)
            if referenced_project == project_id:
                return f"Das Projekt wird vom nicht abgeschlossenen Ensemble/Pilot {name} verwendet."
    return None


def _ensemble_states_for_simulation(simulation_id: str) -> List[dict]:
    folder = os.path.join(_root(), "ensembles")
    if not os.path.isdir(folder):
        return []
    found = []
    for name in os.listdir(folder):
        if not re.fullmatch(r"ens_[0-9a-f]{12}", name):
            continue
        state = _read_json(os.path.join(folder, name, "ensemble.json")) or {}
        if state.get("simulation_id") == simulation_id:
            found.append(state)
    return found


def _sim_links(sim_dir: str) -> Tuple[Optional[str], Optional[str]]:
    """project_id und graph_id aus state.json oder simulation_config.json."""
    project_id = None
    graph_id = None
    for filename in ("state.json", "simulation_config.json"):
        data = _read_json(os.path.join(sim_dir, filename))
        if not data:
            continue
        if not project_id and isinstance(data.get("project_id"), str):
            project_id = data["project_id"]
        if not graph_id and isinstance(data.get("graph_id"), str):
            graph_id = data["graph_id"]
    return project_id, graph_id


def _simulation_ids_for_project(project_id: str) -> List[str]:
    folder = os.path.join(_root(), "simulations")
    if not os.path.isdir(folder):
        return []
    found = []
    for name in os.listdir(folder):
        if not RE_SIM.fullmatch(name):
            continue
        try:
            sim_dir = _child(["simulations"], name)
        except CleanupError:
            continue
        if not os.path.isdir(sim_dir):
            continue
        pid, _graph = _sim_links(sim_dir)
        if pid == project_id:
            found.append(name)
    return found


def _referenced_graph_ids() -> set:
    """Graph-Kennungen, die noch in einer project.json stehen."""
    referenced = set()
    folder = os.path.join(_root(), "projects")
    if not os.path.isdir(folder):
        return referenced
    for name in os.listdir(folder):
        if not RE_PROJECT.fullmatch(name):
            continue
        try:
            proj = _child(["projects"], name)
        except CleanupError:
            continue
        meta = _read_json(os.path.join(proj, "project.json"))
        graph_id = (meta or {}).get("graph_id")
        if isinstance(graph_id, str) and graph_id:
            referenced.add(graph_id.lower())
    return referenced


def _runner_alive(simulation_id: str) -> bool:
    """True, wenn in diesem Prozess noch ein Runner für die Simulation läuft.

    Nur der Speicher zählt. Eine alte run_state.json nach einem Absturz ist kein laufender Prozess.
    """
    try:
        from .simulation_runner import SimulationRunner
    except Exception as exc:
        logger.info(f"Runner-Status nicht prüfbar ({simulation_id}): {exc}")
        return False
    try:
        if simulation_id in SimulationRunner.get_running_simulations():
            return True
        state = SimulationRunner._run_states.get(simulation_id)
        if state is None:
            return False
        status = getattr(getattr(state, "runner_status", None), "value", None) or str(
            getattr(state, "runner_status", "")
        )
        if status not in _RUNNER_ACTIVE:
            return False
        process = SimulationRunner._processes.get(simulation_id)
        # STARTING: der Prozess ist vielleicht noch nicht eingetragen.
        if status == "starting" and process is None:
            return True
        return process is not None and process.poll() is None
    except Exception as exc:
        logger.info(f"Runner-Status nicht prüfbar ({simulation_id}): {exc}")
        return False


def simulation_is_active(simulation_id: str) -> bool:
    """Laufende Simulation oder ein laufender Durchlauf, der sie benutzt."""
    if not isinstance(simulation_id, str) or not RE_SIM.fullmatch(simulation_id):
        return False
    return simulation_delete_block_reason(simulation_id) is not None


def simulation_delete_block_reason(simulation_id: str) -> Optional[str]:
    """Begründung liefern, wenn eine Simulation momentan nicht gelöscht werden darf."""
    if not isinstance(simulation_id, str) or not RE_SIM.fullmatch(simulation_id):
        return None
    if _pipeline_ids(simulation_id=simulation_id, status="running"):
        return "Die Simulation gehört zu einem laufenden Pipeline-Durchlauf."
    reason = _active_task_reason(simulation_id=simulation_id)
    if reason:
        return reason
    sim_dir = _child(["simulations"], simulation_id)
    simulation_state = _read_json(os.path.join(sim_dir, "state.json")) or {}
    if simulation_state.get("status") == "preparing":
        return "Die Simulation wird gerade vorbereitet (Prepare-Status processing)."
    if simulation_state.get("status") == "running":
        return "Die Simulation läuft gerade."
    reason = _active_ensemble_reason(simulation_id=simulation_id)
    if reason:
        return reason
    if _runner_alive(simulation_id):
        return "Die Simulation läuft oder startet gerade."
    if simulation_state.get("source") == "validierung":
        ensembles = _ensemble_states_for_simulation(simulation_id)
        if not ensembles:
            return "Validierungssimulationen sind geschützt, bis ihr Ensemble abgeschlossen, fehlgeschlagen oder abgebrochen ist."
    run_state = _read_json(os.path.join(sim_dir, "run_state.json")) or {}
    if run_state.get("runner_status") in ("running", "starting"):
        return "Die Simulation läuft oder startet gerade (Runner-Status)."
    return None


def project_delete_block_reason(project_id: str) -> Optional[str]:
    if _pipeline_ids(project_id=project_id, status="running"):
        return "Das Projekt gehört zu einem laufenden Pipeline-Durchlauf."
    reason = _active_task_reason(project_id=project_id)
    if reason:
        return reason
    reason = _active_ensemble_reason(project_id=project_id)
    if reason:
        return reason
    simulation_ids = _simulation_ids_for_project(project_id)
    for simulation_id in simulation_ids:
        reason = simulation_delete_block_reason(simulation_id)
        if reason:
            return f"Projekt kann wegen {simulation_id} nicht gelöscht werden: {reason}"
    project = _read_json(os.path.join(_child(["projects"], project_id), "project.json")) or {}
    if project.get("source") == "validierung" and not simulation_ids:
        return "Validierungsprojekte sind geschützt, bis ihr Ensemble abgeschlossen, fehlgeschlagen oder abgebrochen ist."
    return None


def _stop_runner(simulation_id: str) -> None:
    """Laufenden Runner anhalten. Fehlt er schon, wird nur protokolliert."""
    if not _runner_alive(simulation_id):
        return
    try:
        from .simulation_runner import SimulationRunner
        try:
            SimulationRunner.stop_simulation(simulation_id)
        except Exception as exc:
            logger.info(f"Stoppen vor dem Löschen übersprungen ({simulation_id}): {exc}")
            process = SimulationRunner._processes.get(simulation_id)
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except Exception:
                    process.kill()
        SimulationRunner._run_states.pop(simulation_id, None)
        process = SimulationRunner._processes.get(simulation_id)
        if process is None or process.poll() is not None:
            SimulationRunner._processes.pop(simulation_id, None)
    except Exception as exc:
        logger.info(f"Stoppen vor dem Löschen übersprungen ({simulation_id}): {exc}")


def _delete_graph_storage(graph_id: str) -> List[str]:
    """Lokalen Vault (UUID-Ordner) und bei zep/hybrid den Zep-Graphen entfernen.

    Fehler beim Zep-Graphen werden nur protokolliert, das lokale Aufräumen läuft weiter.
    """
    if not isinstance(graph_id, str) or not graph_id:
        return []
    removed = []
    if RE_UUID.fullmatch(graph_id):
        try:
            folder = _child(["simulations"], graph_id)
            if _rm_under(folder):
                removed.append(f"graph:{graph_id}")
        except CleanupError as exc:
            logger.warning(f"Graph-Ordner übersprungen ({graph_id}): {exc}")
    provider = (getattr(Config, "MEMORY_PROVIDER", "") or "").lower()
    if provider in ("zep", "hybrid"):
        try:
            from .memory.factory import MemoryFactory
            memory = MemoryFactory.get_provider()
            if hasattr(memory, "delete_graph"):
                memory.delete_graph(graph_id)
                removed.append(f"zep:{graph_id}")
        except Exception as exc:
            logger.warning(f"Zep-Graph {graph_id} konnte nicht gelöscht werden: {exc}")
    return removed


def _remove_pipeline(run_id: str) -> List[str]:
    removed_any = False
    if _rm_under(_pipeline_json_path(run_id)):
        removed_any = True
    if _rm_under(_child(["pipelines"], run_id)):
        removed_any = True
    return [f"pipeline:{run_id}"] if removed_any else []


def _delete_reports_for(simulation_id: str) -> List[str]:
    """Berichte, deren metadata.json oder meta.json auf diese Simulation zeigt."""
    folder = os.path.join(_root(), "reports")
    if not os.path.isdir(folder):
        return []
    removed = []
    for name in os.listdir(folder):
        if not RE_REPORT.fullmatch(name):
            continue
        try:
            report_dir = _child(["reports"], name)
        except CleanupError as exc:
            logger.warning(f"Bericht übersprungen ({name}): {exc}")
            continue
        if not os.path.isdir(report_dir):
            continue
        owner = None
        for meta_name in ("metadata.json", "meta.json"):
            meta = _read_json(os.path.join(report_dir, meta_name))
            if meta and meta.get("simulation_id"):
                owner = meta.get("simulation_id")
                break
        if owner == simulation_id and _rm_under(report_dir):
            removed.append(f"report:{name}")
    return removed


def _delete_pipelines_for_simulation(simulation_id: str) -> List[str]:
    removed = []
    for run_id, data in list(_iter_pipelines()):
        if data.get("simulation_id") != simulation_id:
            continue
        # Laufende Durchläufe nie anfassen. Der Aufrufer hat das vorher geprüft.
        if data.get("status") == "running":
            continue
        removed.extend(_remove_pipeline(run_id))
    return removed


def delete_project_cascade(project_id: str, *, enforce_protection: bool = True) -> List[str]:
    """Projektordner und den zugehörigen Graph-Speicher löschen."""
    project_id = _require(project_id, RE_PROJECT)
    if enforce_protection:
        reason = project_delete_block_reason(project_id)
        if reason:
            raise CleanupBusy(reason)
    proj = _child(["projects"], project_id)
    meta = _read_json(os.path.join(proj, "project.json"))
    graph_id = (meta or {}).get("graph_id")
    removed = []
    if _rm_under(proj):
        removed.append(f"project:{project_id}")
    if isinstance(graph_id, str) and graph_id:
        removed.extend(_delete_graph_storage(graph_id))
    logger.info(f"Projekt aufgeräumt {project_id}: {removed}")
    return removed


def _maybe_delete_project(project_id: Optional[str], graph_hint: Optional[str] = None) -> List[str]:
    """Projekt nur löschen, wenn keine Simulation und kein laufender Durchlauf es noch braucht."""
    if not isinstance(project_id, str) or not RE_PROJECT.fullmatch(project_id):
        return []
    if _simulation_ids_for_project(project_id):
        return []
    if _pipeline_ids(project_id=project_id, status="running"):
        return []
    # Der übergeordnete Simulations-/Pipeline-Löschvorgang wurde vor seiner ersten
    # Mutation vollständig geprüft; nach Entfernen der letzten Simulation fehlt sonst
    # die Referenz, mit der ein terminales Validierungs-Ensemble nachgewiesen wird.
    removed = delete_project_cascade(project_id, enforce_protection=False)
    already = any(item.startswith("graph:") or item.startswith("zep:") for item in removed)
    if graph_hint and not already and graph_hint.lower() not in _referenced_graph_ids():
        removed.extend(_delete_graph_storage(graph_hint))
    return removed


def delete_simulation_cascade(simulation_id: str) -> List[str]:
    """Simulation, ihre Berichte und Durchlauf-Protokolle löschen.

    Laufende Runner, Vorbereitungen, Durchläufe und Ensembles blockieren das Löschen.
    Das Projekt (samt Graph) folgt nur, wenn keine andere Simulation und kein laufender
    Durchlauf es noch benutzt.
    """
    simulation_id = _require(simulation_id, RE_SIM)
    reason = simulation_delete_block_reason(simulation_id)
    if reason:
        raise CleanupBusy(reason)
    sim_dir = _child(["simulations"], simulation_id)
    project_id, graph_id = _sim_links(sim_dir) if os.path.isdir(sim_dir) else (None, None)
    _stop_runner(simulation_id)
    removed = []
    if _rm_under(sim_dir):
        removed.append(f"simulation:{simulation_id}")
    removed.extend(_delete_reports_for(simulation_id))
    removed.extend(_delete_pipelines_for_simulation(simulation_id))
    removed.extend(_maybe_delete_project(project_id, graph_id))
    logger.info(f"Simulation aufgeräumt {simulation_id}: {removed}")
    return removed


def delete_failed_pipelines() -> List[str]:
    """Alle Durchläufe mit Status failed entfernen. Laufende bleiben unberührt."""
    removed: List[str] = []
    for run_id, data in list(_iter_pipelines()):
        if data.get("status") != "failed":
            continue
        try:
            removed.extend(delete_pipeline_cascade(run_id))
        except CleanupBusy:
            continue
        except Exception as exc:
            logger.error(f"Aufräumen des fehlgeschlagenen Durchlaufs {run_id} fehlgeschlagen: {exc}")
    return removed


def delete_pipeline_cascade(run_id: str) -> List[str]:
    """Protokoll und Upload-Ordner eines Durchlaufs löschen, danach Simulation und Projekt.

    Ein Durchlauf mit Status "running" wird nicht angefasst.
    """
    run_id = _require(run_id, RE_RUN)
    state = _read_json(_pipeline_json_path(run_id)) or {}
    if state.get("status") == "running":
        raise CleanupBusy(
            "Der Durchlauf läuft noch. Warte, bis er fertig ist, bevor du ihn löschst."
        )
    simulation_id = state.get("simulation_id")
    project_id = state.get("project_id")
    graph_id = state.get("graph_id")
    if isinstance(simulation_id, str) and RE_SIM.fullmatch(simulation_id):
        reason = simulation_delete_block_reason(simulation_id)
        if reason:
            raise CleanupBusy(reason)
    if isinstance(project_id, str) and RE_PROJECT.fullmatch(project_id):
        reason = project_delete_block_reason(project_id)
        if reason:
            raise CleanupBusy(reason)
    removed = _remove_pipeline(run_id)
    hint = graph_id if isinstance(graph_id, str) else None
    if isinstance(simulation_id, str) and RE_SIM.fullmatch(simulation_id):
        removed.extend(delete_simulation_cascade(simulation_id))
    project_left = False
    if isinstance(project_id, str) and RE_PROJECT.fullmatch(project_id):
        try:
            project_left = os.path.isdir(_child(["projects"], project_id))
        except CleanupError:
            project_left = False
        if project_left:
            removed.extend(_maybe_delete_project(project_id, hint))
    elif hint and hint.lower() not in _referenced_graph_ids():
        # Durchlauf kannte noch kein Projekt, aber schon einen Graphen.
        removed.extend(_delete_graph_storage(hint))
    logger.info(f"Durchlauf aufgeräumt {run_id}: {removed}")
    return removed


def _project_age_hours(project_id: str) -> Optional[float]:
    proj = _child(["projects"], project_id)
    meta = _read_json(os.path.join(proj, "project.json"))
    created = _parse_time((meta or {}).get("created_at"))
    if created is None:
        try:
            created = datetime.fromtimestamp(os.path.getmtime(proj))
        except OSError:
            return None
    return (datetime.now() - created).total_seconds() / 3600.0


def sweep_orphans(max_age_hours: float = 24) -> List[str]:
    """Alte Projekte ohne Simulation und ohne laufenden Durchlauf entfernen.

    Außerdem Graph-Ordner (UUID unter simulations/), auf die kein Projekt mehr zeigt.
    Laufende Durchläufe und alles, was noch benutzt wird, bleiben liegen.
    """
    removed: List[str] = []
    projects = os.path.join(_root(), "projects")
    if os.path.isdir(projects):
        for name in list(os.listdir(projects)):
            if not RE_PROJECT.fullmatch(name):
                continue
            if _simulation_ids_for_project(name):
                continue
            if _pipeline_ids(project_id=name, status="running"):
                continue
            age = _project_age_hours(name)
            if age is None or age <= max_age_hours:
                continue
            try:
                removed.extend(delete_project_cascade(name))
            except CleanupBusy:
                continue
    referenced = _referenced_graph_ids()
    sims = os.path.join(_root(), "simulations")
    if os.path.isdir(sims):
        for name in list(os.listdir(sims)):
            if not RE_UUID.fullmatch(name):
                continue
            if name.lower() in referenced:
                continue
            try:
                folder = _child(["simulations"], name)
            except CleanupError as exc:
                logger.warning(f"Graph-Ordner übersprungen ({name}): {exc}")
                continue
            if os.path.isdir(folder) and _rm_under(folder):
                removed.append(f"graph:{name}")
    if removed:
        logger.info(f"Verwaiste Daten entfernt: {removed}")
    return removed
