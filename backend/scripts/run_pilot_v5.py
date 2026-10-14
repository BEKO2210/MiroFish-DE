#!/usr/bin/env python3
"""V5-Pilot fahren: Preflight, die 7 Fälle nacheinander, Wiederanlauf nach Ausfall, Fortschrittslog.

Der Treiber ändert keine Regeln: Rahmen, Fallmenge und Auswertung stammen aus validate_case.py
und docs/validation/rahmen-pilot-v5.json. Mit --probe läuft stattdessen der synthetische Probefall.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

try:
    from scripts import validate_case as vc
except ImportError:  # Aufruf als python scripts/run_pilot_v5.py
    import validate_case as vc  # type: ignore[no-redef]

DEFAULT_MIN_FREE_GB = 40.0
DEFAULT_MAX_ATTEMPTS = 4
DEFAULT_WAIT_SECONDS = 120.0
MAX_WAIT_SECONDS = 1800.0
CASES_DIR = vc.REPOSITORY_ROOT / "docs" / "validation" / "faelle"
DEFAULT_DATA_DIR = vc.REPOSITORY_ROOT / "backend" / "uploads"
# Ein Wiederanlauf lohnt nicht, wenn das Backend die Versuche gesperrt hat: dann ist der manuelle Reset nötig.
PERMANENT_MARKERS = ("erschöpft", "Resume abgebrochen")


class PreflightError(RuntimeError):
    pass


class RunLog:
    def __init__(self, path: Path, echo: bool = True) -> None:
        self.path, self.echo = path, echo
        path.parent.mkdir(parents=True, exist_ok=True)

    def __call__(self, message: str) -> None:
        line = f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {message}"
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        if self.echo:
            print(line, flush=True)


def required_models(frame: Dict[str, Any]) -> List[str]:
    models = frame["models"]
    names = [models["agent_model"], models["classification_main"],
             *models.get("cold_question_models", [])]
    return list(dict.fromkeys(names))


def free_disk_gb(path: Path) -> float:
    target = path
    while not target.exists() and target != target.parent:
        target = target.parent
    return shutil.disk_usage(target).free / 1e9


def preflight(client: Any, frame: Dict[str, Any], *, data_dir: Path, min_free_gb: float,
              own_ensemble_ids: Sequence[str] = (), ignore_busy: bool = False,
              disk_free_gb: Callable[[Path], float] = free_disk_gb) -> Dict[str, Any]:
    """Plattenplatz, Modelle und Auslastung prüfen. Wirft PreflightError mit allen Befunden."""
    problems: List[str] = []
    free = disk_free_gb(data_dir)
    if free < min_free_gb:
        problems.append(f"Plattenplatz: {free:.1f} GB frei, mindestens {min_free_gb:.1f} GB nötig")
    models: Dict[str, Any] = {"reachable": None, "missing": []}
    try:
        data = client.get("/api/system/models")
        names = {str(item.get("name")) for item in data.get("models") or [] if isinstance(item, dict)}
        models = {"reachable": bool(data.get("reachable")),
                  "missing": [name for name in required_models(frame) if name not in names],
                  "installed": sorted(names)}
        if not models["reachable"]:
            problems.append("Modellserver (Ollama) nicht erreichbar")
        elif models["missing"]:
            problems.append("Modelle fehlen in Ollama: " + ", ".join(models["missing"])
                            + " (für den lokalen Lauf erforderlich)")
    except (vc.ApiError, OSError) as error:
        problems.append(f"Modellliste nicht abrufbar: {error}")
    busy: List[Dict[str, Any]] = []
    try:
        listed = client.get("/api/ensemble/list", allow_list=True)
        busy = [{"ensemble_id": item.get("ensemble_id"), "status": item.get("status")}
                for item in listed if isinstance(item, dict)
                and item.get("status") not in vc.TERMINAL_ENSEMBLE_STATUSES
                and item.get("ensemble_id") not in set(own_ensemble_ids)]
        if busy and not ignore_busy:
            problems.append("Backend ist belegt, laufende fremde Ensembles: "
                            + ", ".join(f"{row['ensemble_id']} ({row['status']})" for row in busy)
                            + ". Erst beenden oder bewusst mit --ignore-busy fortfahren")
    except (vc.ApiError, OSError) as error:
        problems.append(f"Ensemble-Liste nicht abrufbar: {error}")
    report = {"checked_at": datetime.now(timezone.utc).isoformat(), "free_gb": round(free, 1),
              "min_free_gb": min_free_gb, "models": models, "busy": busy, "problems": problems}
    if problems:
        raise PreflightError("; ".join(problems))
    return report


def _state_ensemble_ids(results_dir: Path) -> List[str]:
    found = []
    for path in sorted(results_dir.glob("*.state.json")):
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        found.extend(str(item.get("ensemble_id")) for item in state.get("ensemble_ids") or []
                     if isinstance(item, dict) and item.get("ensemble_id"))
    return found


def _is_done(results_dir: Path, case_name: str) -> bool:
    path = results_dir / f"{case_name}.json"
    if not path.is_file():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(payload, dict) and payload.get("schema_version") == 2 and bool(
        payload.get("rows") or payload.get("contaminated"))


def run_pilot(frame: Dict[str, Any], *, cases_dir: Path, results_dir: Path, base: str,
              client: Any, log: Callable[[str], None], data_dir: Path = DEFAULT_DATA_DIR,
              min_free_gb: float = DEFAULT_MIN_FREE_GB, ignore_busy: bool = False,
              max_attempts: int = DEFAULT_MAX_ATTEMPTS, wait_seconds: float = DEFAULT_WAIT_SECONDS,
              sleep: Callable[[float], None] = time.sleep,
              run_case: Callable[..., Dict[str, Any]] = vc.validate_case,
              **case_options: Any) -> Dict[str, Any]:
    """Fälle des Rahmens in Rahmenreihenfolge. Nach Ausfall mit demselben State neu anlaufen (Resume)."""
    results_dir.mkdir(parents=True, exist_ok=True)
    outcome: Dict[str, Any] = {"cases": {}, "stopped": None}
    for index, name in enumerate(frame["case_ids"], 1):
        if _is_done(results_dir, name):
            log(f"[{index}/{len(frame['case_ids'])}] {name}: Ergebnis liegt vor, übersprungen")
            outcome["cases"][name] = "vorhanden"
            continue
        for attempt in range(1, max_attempts + 1):
            log(f"[{index}/{len(frame['case_ids'])}] {name}: Versuch {attempt}/{max_attempts}")
            try:
                report = preflight(client, frame, data_dir=data_dir, min_free_gb=min_free_gb,
                                   own_ensemble_ids=_state_ensemble_ids(results_dir),
                                   ignore_busy=ignore_busy)
                vc._write_json_atomic(results_dir / "preflight.json", report)
                log(f"{name}: Preflight in Ordnung, {report['free_gb']} GB frei")
                run_case(cases_dir / name, runs=frame["seeds"], hours=frame["hours"],
                         minutes_per_round=frame["minutes_per_round"], arms=frame["arms"], base=base,
                         results_dir=results_dir, rahmen=frame, client=client, progress=log,
                         **case_options)
                log(f"{name}: abgeschlossen")
                outcome["cases"][name] = "abgeschlossen"
                break
            except ValueError as error:
                if "kontaminiert" in str(error):
                    log(f"{name}: kontaminiert, nicht gewertet ({error})")
                    outcome["cases"][name] = "kontaminiert"
                    break
                log(f"{name}: Konfigurationsfehler, Abbruch: {error}")
                outcome["stopped"] = {"case": name, "grund": str(error)}
                return outcome
            except (vc.ApiError, PreflightError, OSError) as error:
                permanent = any(marker in str(error) for marker in PERMANENT_MARKERS)
                log(f"{name}: Ausfall ({type(error).__name__}: {error})")
                if permanent or attempt == max_attempts:
                    why = ("Versuche im Backend gesperrt, manueller Reset nötig (Protokoll, Abschnitt Betrieb)"
                           if permanent else "Wiederanläufe erschöpft")
                    log(f"{name}: {why}. Pilot angehalten; derselbe Aufruf setzt am State wieder auf.")
                    outcome["stopped"] = {"case": name, "grund": f"{why}: {error}"}
                    return outcome
                wait = min(wait_seconds * 2 ** (attempt - 1), MAX_WAIT_SECONDS)
                log(f"{name}: Wiederanlauf (Resume) in {wait:.0f} s")
                sleep(wait)
    summary = vc.update_summary(results_dir, frame)
    log("GESAMT geschrieben: Urteil "
        f"{summary['clean']['preregistered_criterion']['status']}")
    outcome["status"] = summary["clean"]["preregistered_criterion"]["status"]
    return outcome


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://127.0.0.1:5002")
    parser.add_argument("--probe", action="store_true",
                        help="Probelauf mit dem synthetischen Fall statt der 7 Pilotfälle")
    parser.add_argument("--cases-dir", type=Path, default=None)
    parser.add_argument("--results-dir", type=Path, default=None)
    parser.add_argument("--log", type=Path, default=None, help="Logdatei (Standard: <Ergebnisordner>/pilot.log)")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR,
                        help="Datenträger der Laufordner für den Plattenplatz-Check")
    parser.add_argument("--min-free-gb", type=float, default=DEFAULT_MIN_FREE_GB)
    parser.add_argument("--max-attempts", type=int, default=DEFAULT_MAX_ATTEMPTS)
    parser.add_argument("--wait-seconds", type=float, default=DEFAULT_WAIT_SECONDS)
    parser.add_argument("--ignore-busy", action="store_true")
    parser.add_argument("--preflight-only", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = parse_args(argv)
    try:
        frame = vc.load_rahmen("probe-v5" if arguments.probe else "pilot-v5")
    except (OSError, ValueError) as error:
        print(f"Fehler: {error}", file=sys.stderr)
        return 1
    results_dir = arguments.results_dir or vc.DEFAULT_RESULTS_DIR / frame["id"]
    cases_dir = arguments.cases_dir or (vc.PROBE_DIR.parent if arguments.probe else CASES_DIR)
    log = RunLog(arguments.log or results_dir / "pilot.log")
    client = vc.ApiClient(arguments.base, log=log)
    log(f"Start {frame['id']}: Fälle {', '.join(frame['case_ids'])}, Basis {arguments.base}")
    if arguments.preflight_only:
        try:
            report = preflight(client, frame, data_dir=arguments.data_dir,
                               min_free_gb=arguments.min_free_gb, ignore_busy=arguments.ignore_busy)
        except PreflightError as error:
            log(f"Preflight fehlgeschlagen: {error}")
            return 1
        log(f"Preflight in Ordnung: {json.dumps(report, ensure_ascii=False)}")
        return 0
    outcome = run_pilot(frame, cases_dir=cases_dir, results_dir=results_dir, base=arguments.base,
                        client=client, log=log, data_dir=arguments.data_dir,
                        min_free_gb=arguments.min_free_gb, ignore_busy=arguments.ignore_busy,
                        max_attempts=arguments.max_attempts, wait_seconds=arguments.wait_seconds)
    if outcome["stopped"]:
        return 1
    log(f"Fertig: {json.dumps(outcome['cases'], ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
