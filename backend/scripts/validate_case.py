#!/usr/bin/env python3
"""Einen dokumentierten Realfall blind simulieren und gegen den Verlauf werten.

Das Skript benutzt ausschließlich die öffentliche HTTP-API. Die tatsächlichen
Ergebnisse werden erst nach Abschluss des Ensembles mit dessen Resultaten verbunden.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

import requests


QUESTION = (
    "Wie reagieren Bürgerinnen, Vereine, Medien und Politik in den ersten zwei "
    "Wochen nach der Bekanntgabe?"
)
VARIANTS = ["baseline", "null_model"]
TERMINAL_ENSEMBLE_STATUSES = {"completed", "failed", "cancelled"}
BOOTSTRAP_SEED = 20261014
BOOTSTRAP_SAMPLES = 10_000
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS_DIR = REPOSITORY_ROOT / "docs" / "validation" / "ergebnisse"


class ApiError(RuntimeError):
    pass


class ApiClient:
    def __init__(self, base: str, session: Any = None) -> None:
        self.base = base.rstrip("/")
        self.session = session or requests.Session()

    @staticmethod
    def _unwrap(response: Any) -> Dict[str, Any]:
        try:
            payload = response.json()
        except (TypeError, ValueError) as error:
            raise ApiError(
                f"Antwort ist kein JSON (HTTP {response.status_code}): "
                f"{str(getattr(response, 'text', ''))[:200]}"
            ) from error
        if response.status_code >= 400 or not payload.get("success", True):
            raise ApiError(str(payload.get("error") or f"HTTP {response.status_code}"))
        data = payload.get("data", payload)
        if not isinstance(data, dict):
            raise ApiError("API-Antwort enthält kein Datenobjekt")
        return data

    def get(self, path: str, *, timeout: int = 30) -> Dict[str, Any]:
        return self._unwrap(self.session.get(f"{self.base}{path}", timeout=timeout))

    def post(
        self,
        path: str,
        *,
        json_body: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Any = None,
        timeout: int = 60,
    ) -> Dict[str, Any]:
        return self._unwrap(
            self.session.post(
                f"{self.base}{path}",
                json=json_body,
                data=data,
                files=files,
                timeout=timeout,
            )
        )


def _write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def _write_json_atomic(path: Path, payload: Dict[str, Any]) -> None:
    _write_text_atomic(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_case_files(case_dir: Path) -> None:
    if not case_dir.is_dir():
        raise ValueError(f"Fallordner nicht gefunden: {case_dir}")
    missing = [
        name
        for name in ("ausgangslage.md", "verlauf.md", "ergebnisse.json")
        if not (case_dir / name).is_file()
    ]
    if missing:
        raise ValueError("Im Fallordner fehlen: " + ", ".join(missing))


def load_outcomes(case_dir: Path) -> List[Dict[str, Any]]:
    outcomes = _load_json(case_dir / "ergebnisse.json")
    if not isinstance(outcomes, list) or not outcomes:
        raise ValueError("ergebnisse.json muss eine nicht-leere Liste sein")
    seen = set()
    for index, outcome in enumerate(outcomes):
        if not isinstance(outcome, dict):
            raise ValueError(f"ergebnisse.json[{index}] ist kein Objekt")
        text = str(outcome.get("text_de") or "").strip()
        actual = outcome.get("eingetreten")
        if not text or len(text) > 200:
            raise ValueError(f"Ungültiger text_de in ergebnisse.json[{index}]")
        if text in seen:
            raise ValueError(f"Doppelte Ergebnisfrage: {text}")
        if not isinstance(actual, bool):
            raise ValueError(f"eingetreten in ergebnisse.json[{index}] muss boolesch sein")
        seen.add(text)
    return outcomes


def blind_custom_outcomes(outcomes: Sequence[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Absichtlich nur den vorab formulierten Text an die Simulation geben."""
    return [{"text_de": str(outcome["text_de"]).strip()} for outcome in outcomes]


def _new_state(case_name: str, base: str, runs: int, hours: int) -> Dict[str, Any]:
    return {
        "case": case_name,
        "base": base.rstrip("/"),
        "runs": runs,
        "hours": hours,
        "question": QUESTION,
        "project_id": None,
        "graph_task_id": None,
        "graph_id": None,
        "simulation_id": None,
        "prepare_task_id": None,
        "prepared": False,
        "ensemble_id": None,
        "ensemble_completed": False,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def _save_state(path: Path, state: Dict[str, Any]) -> None:
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    _write_json_atomic(path, state)


def load_or_create_state(
    path: Path, case_name: str, base: str, runs: int, hours: int
) -> Dict[str, Any]:
    if not path.is_file():
        state = _new_state(case_name, base, runs, hours)
        _save_state(path, state)
        return state
    state = _load_json(path)
    expected = {
        "case": case_name,
        "base": base.rstrip("/"),
        "runs": runs,
        "hours": hours,
        "question": QUESTION,
    }
    conflicts = [key for key, value in expected.items() if state.get(key) != value]
    if conflicts:
        raise ValueError(
            "Vorhandener Resume-State passt nicht zu diesem Aufruf: "
            + ", ".join(conflicts)
        )
    return state


def prepare_simulation(
    client: ApiClient,
    case_dir: Path,
    state_path: Path,
    state: Dict[str, Any],
    *,
    sleep: Callable[[float], None] = time.sleep,
    poll_interval: float = 5.0,
) -> None:
    source = case_dir / "ausgangslage.md"
    if not state.get("project_id"):
        with source.open("rb") as handle:
            data = client.post(
                "/api/graph/ontology/generate",
                files={"files": (source.name, handle, "text/markdown")},
                data={
                    "simulation_requirement": QUESTION,
                    "project_name": f"Realitätsabgleich: {case_dir.name}",
                },
                timeout=3600,
            )
        state["project_id"] = data["project_id"]
        _save_state(state_path, state)

    if not state.get("graph_id"):
        if not state.get("graph_task_id"):
            task = client.post(
                "/api/graph/build",
                json_body={"project_id": state["project_id"], "force": True},
            )
            state["graph_task_id"] = task["task_id"]
            _save_state(state_path, state)
        while True:
            task = client.get(f"/api/graph/task/{state['graph_task_id']}")
            if task.get("status") == "completed":
                state["graph_id"] = (task.get("result") or {}).get("graph_id")
                if not state["graph_id"]:
                    raise ApiError("Graph-Aufgabe endete ohne graph_id")
                _save_state(state_path, state)
                break
            if task.get("status") == "failed":
                raise ApiError(str(task.get("error") or "Graph-Aufbau fehlgeschlagen"))
            sleep(poll_interval)

    if not state.get("simulation_id"):
        simulation = client.post(
            "/api/simulation/create",
            json_body={"project_id": state["project_id"]},
        )
        state["simulation_id"] = simulation["simulation_id"]
        _save_state(state_path, state)

    if not state.get("prepared"):
        if not state.get("prepare_task_id"):
            prepared = client.post(
                "/api/simulation/prepare",
                json_body={
                    "simulation_id": state["simulation_id"],
                    "parallel_profile_count": 1,
                },
            )
            state["prepare_task_id"] = prepared.get("task_id")
            if prepared.get("already_prepared"):
                state["prepared"] = True
            _save_state(state_path, state)
        while not state.get("prepared"):
            status = client.post(
                "/api/simulation/prepare/status",
                json_body={
                    "simulation_id": state["simulation_id"],
                    "task_id": state.get("prepare_task_id"),
                },
                timeout=30,
            )
            value = status.get("status") or status.get("simulation_status")
            if (
                value in {"ready", "completed"}
                or status.get("already_prepared")
                or status.get("is_ready")
            ):
                state["prepared"] = True
                _save_state(state_path, state)
                break
            if value in {"failed", "error"}:
                raise ApiError(str(status.get("error") or "Vorbereitung fehlgeschlagen"))
            sleep(poll_interval)


def run_ensemble(
    client: ApiClient,
    outcomes: Sequence[Dict[str, Any]],
    state_path: Path,
    state: Dict[str, Any],
    *,
    sleep: Callable[[float], None] = time.sleep,
    poll_interval: float = 15.0,
) -> Dict[str, Any]:
    if not state.get("ensemble_id"):
        started = client.post(
            "/api/ensemble/start",
            json_body={
                "simulation_id": state["simulation_id"],
                "variants": VARIANTS,
                "runs": state["runs"],
                "hours": state["hours"],
                "custom_outcomes": blind_custom_outcomes(outcomes),
            },
            timeout=120,
        )
        state["ensemble_id"] = started["ensemble_id"]
        _save_state(state_path, state)

    while True:
        ensemble = client.get(f"/api/ensemble/{state['ensemble_id']}")
        status = ensemble.get("status")
        if status == "completed":
            state["ensemble_completed"] = True
            _save_state(state_path, state)
            return ensemble
        if status in TERMINAL_ENSEMBLE_STATUSES:
            raise ApiError(str(ensemble.get("error") or f"Ensemble endete mit {status}"))
        sleep(poll_interval)


def brier_score(probabilities: Sequence[float], actual: Sequence[int]) -> Optional[float]:
    if not probabilities:
        return None
    return sum((p - y) ** 2 for p, y in zip(probabilities, actual)) / len(probabilities)


def accuracy_score(probabilities: Sequence[float], actual: Sequence[int]) -> Optional[float]:
    if not probabilities:
        return None
    return sum((p >= 0.5) == bool(y) for p, y in zip(probabilities, actual)) / len(probabilities)


def log_score(probabilities: Sequence[float], actual: Sequence[int]) -> Optional[float]:
    """Mittlerer negativer logarithmischer Score; kleiner ist besser."""
    if not probabilities:
        return None
    epsilon = 1e-15
    losses = []
    for probability, observed in zip(probabilities, actual):
        p = min(1.0 - epsilon, max(epsilon, probability))
        losses.append(-(observed * math.log(p) + (1 - observed) * math.log(1 - p)))
    return sum(losses) / len(losses)


def _rounded(value: Optional[float]) -> Optional[float]:
    return None if value is None else round(float(value), 6)


def metric_set(probabilities: Sequence[float], actual: Sequence[int]) -> Dict[str, Any]:
    return {
        "n": len(probabilities),
        "brier": _rounded(brier_score(probabilities, actual)),
        "accuracy_at_0_5": _rounded(accuracy_score(probabilities, actual)),
        "log_score": _rounded(log_score(probabilities, actual)),
    }


def build_case_result(
    case_name: str,
    outcomes: Sequence[Dict[str, Any]],
    ensemble: Dict[str, Any],
    *,
    runs: int,
    hours: int,
) -> Dict[str, Any]:
    checklist = ensemble.get("checklist") or []
    custom_by_text = {
        str(item.get("text_de") or "").strip(): item
        for item in checklist
        if item.get("source") == "user"
    }
    results = ensemble.get("results") or {}
    reliability = ensemble.get("reliability") or {}
    rows = []
    for outcome in outcomes:
        text = str(outcome["text_de"]).strip()
        item = custom_by_text.get(text)
        if not item:
            raise ValueError(f"Eigene Ergebnisfrage fehlt in der Ensemble-Antwort: {text}")
        outcome_id = str(item["id"])
        baseline = (results.get("baseline") or {}).get(outcome_id)
        null_model = (results.get("null_model") or {}).get(outcome_id)
        if not isinstance(baseline, dict) or not isinstance(null_model, dict):
            raise ValueError(f"Variantenresultat fehlt für {outcome_id}")
        reliability_value = reliability.get(outcome_id) or {}
        reliability_label = str(reliability_value.get("label") or "nicht messbar")
        measurable = (
            reliability_label != "nicht messbar"
            and int(baseline.get("n") or 0) > 0
            and int(null_model.get("n") or 0) > 0
        )
        rows.append({
            "outcome_id": outcome_id,
            "question": text,
            "actual": 1 if outcome["eingetreten"] else 0,
            "source": outcome.get("quelle"),
            "simulation": {
                key: baseline.get(key, 0)
                for key in ("yes", "n", "rate", "disputed", "unclassified")
            },
            "null_model": {
                key: null_model.get(key, 0)
                for key in ("yes", "n", "rate", "disputed", "unclassified")
            },
            "reliability": {
                key: reliability_value.get(key)
                for key in ("agreement", "kappa", "n_pairs", "label")
            },
            "measurable": measurable,
        })

    scored = [row for row in rows if row["measurable"]]
    actual = [row["actual"] for row in scored]
    simulation = [float(row["simulation"]["rate"]) for row in scored]
    null_model = [float(row["null_model"]["rate"]) for row in scored]
    naive = [0.5] * len(scored)
    return {
        "schema_version": 1,
        "case": case_name,
        "question": QUESTION,
        "runs": runs,
        "hours": hours,
        "simulation_id": ensemble.get("simulation_id"),
        "ensemble_id": ensemble.get("ensemble_id"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rows": rows,
        "metrics": {
            "simulation": metric_set(simulation, actual),
            "null_model": metric_set(null_model, actual),
            "naive_0_5": metric_set(naive, actual),
        },
    }


def _display_metric(value: Any, *, percent: bool = False) -> str:
    if value is None:
        return "–"
    return f"{float(value):.1%}" if percent else f"{float(value):.4f}"


def _escape_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def case_markdown(result: Dict[str, Any]) -> str:
    lines = [
        f"# V5-Realitätsabgleich: {result['case']}",
        "",
        f"Neutrale Frage: „{QUESTION}“",
        "",
        f"{result['runs']} Läufe je Variante, {result['hours']} simulierte Stunden. "
        "Nur die Ausgangslage und die Texte der Ergebnisfragen gingen an die Simulation; "
        "`eingetreten` und der tatsächliche Verlauf wurden nicht gesendet.",
        "",
        "| Frage | eingetreten | Simulation | Nullmodell | Zuverlässigkeit |",
        "|---|---:|---:|---:|---|",
    ]
    for row in result["rows"]:
        sim, null, rel = row["simulation"], row["null_model"], row["reliability"]
        reliability = (
            f"{rel.get('label') or 'nicht messbar'}; Kappa "
            f"{_display_metric(rel.get('kappa'))}, "
            f"Üb. {_display_metric(rel.get('agreement'), percent=True)}"
        )
        if sim.get("disputed") or null.get("disputed"):
            reliability += (
                f"; strittig Simulation {sim.get('disputed', 0)}, "
                f"Nullmodell {null.get('disputed', 0)}"
            )
        lines.append(
            f"| {_escape_cell(row['question'])} | {row['actual']} | "
            f"{sim['yes']}/{sim['n']} ({float(sim['rate']):.1%}) | "
            f"{null['yes']}/{null['n']} ({float(null['rate']):.1%}) | "
            f"{reliability} |"
        )
    lines.extend([
        "",
        "## Kennzahlen",
        "",
        "| Variante | Fragen | Brier-Score | Trefferquote (Schwelle 0,5) | Log-Score |",
        "|---|---:|---:|---:|---:|",
    ])
    labels = {
        "simulation": "Simulation",
        "null_model": "Nullmodell",
        "naive_0_5": "Naive Basisrate 0,5",
    }
    for key, label in labels.items():
        metric = result["metrics"][key]
        lines.append(
            f"| {label} | {metric['n']} | {_display_metric(metric['brier'])} | "
            f"{_display_metric(metric['accuracy_at_0_5'], percent=True)} | "
            f"{_display_metric(metric['log_score'])} |"
        )
    excluded = [row for row in result["rows"] if not row["measurable"]]
    lines.extend([
        "",
        "Brier- und Log-Score sind Verluste (kleiner ist besser). Die Trefferquote wertet "
        "eine Rate ab 0,5 als Ja. Strittige Einzelläufe sind bereits aus `N` ausgeschlossen.",
    ])
    if excluded:
        lines.extend(["", "## Nicht messbare Ergebnisse", ""])
        for row in excluded:
            lines.append(f"- {row['question']}")
    return "\n".join(lines) + "\n"


def _percentile(sorted_values: Sequence[float], probability: float) -> float:
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    position = (len(sorted_values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(sorted_values[lower])
    fraction = position - lower
    return float(sorted_values[lower] * (1 - fraction) + sorted_values[upper] * fraction)


def bootstrap_mean_ci(
    values: Sequence[float],
    *,
    seed: int = BOOTSTRAP_SEED,
    samples: int = BOOTSTRAP_SAMPLES,
) -> Optional[Dict[str, float]]:
    if not values:
        return None
    rng = random.Random(seed)
    n = len(values)
    means = sorted(
        sum(values[rng.randrange(n)] for _ in range(n)) / n
        for _ in range(samples)
    )
    return {
        "low": round(_percentile(means, 0.025), 6),
        "high": round(_percentile(means, 0.975), 6),
    }


def build_summary(case_results: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    case_results = list(case_results)
    rows = [
        row
        for result in case_results
        for row in result.get("rows", [])
        if row.get("measurable")
    ]
    losses = {
        "simulation": [
            (float(row["simulation"]["rate"]) - int(row["actual"])) ** 2
            for row in rows
        ],
        "null_model": [
            (float(row["null_model"]["rate"]) - int(row["actual"])) ** 2
            for row in rows
        ],
        "naive_0_5": [(0.5 - int(row["actual"])) ** 2 for row in rows],
    }
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_samples": BOOTSTRAP_SAMPLES,
        "case_count": len({result.get("case") for result in case_results}),
        "question_count": len(rows),
        "brier": {
            key: {
                "value": _rounded(sum(values) / len(values)) if values else None,
                "ci_95": bootstrap_mean_ci(values),
            }
            for key, values in losses.items()
        },
    }


def summary_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# V5-Realitätsabgleich – Gesamt",
        "",
        f"{summary['case_count']} Fälle, {summary['question_count']} messbare Fragen. "
        f"95-%-Bootstrap-Konfidenzintervalle über Fragen "
        f"({summary['bootstrap_samples']} Ziehungen, Seed {summary['bootstrap_seed']}).",
        "",
        "| Verfahren | Brier-Score | 95-%-Bootstrap-KI |",
        "|---|---:|---:|",
    ]
    labels = {
        "simulation": "Simulation",
        "null_model": "Nullmodell",
        "naive_0_5": "Naive Basisrate 0,5",
    }
    for key, label in labels.items():
        item = summary["brier"][key]
        interval = item["ci_95"]
        rendered_interval = (
            f"{interval['low']:.4f}–{interval['high']:.4f}" if interval else "–"
        )
        lines.append(f"| {label} | {_display_metric(item['value'])} | {rendered_interval} |")
    lines.extend([
        "",
        "Ausgeschlossen sind Ergebnisse ohne klassifizierte Läufe oder mit der "
        "Zuverlässigkeitsbewertung „nicht messbar“. Alle drei Verfahren werden auf "
        "demselben gepaarten Fragensatz verglichen; kleiner ist besser.",
    ])
    return "\n".join(lines) + "\n"


def update_summary(results_dir: Path) -> Dict[str, Any]:
    case_results = []
    for path in sorted(results_dir.glob("*.json")):
        if path.name == "GESAMT.json" or path.name.endswith(".state.json"):
            continue
        payload = _load_json(path)
        if isinstance(payload, dict) and payload.get("schema_version") == 1 and payload.get("rows"):
            case_results.append(payload)
    summary = build_summary(case_results)
    _write_json_atomic(results_dir / "GESAMT.json", summary)
    _write_text_atomic(results_dir / "GESAMT.md", summary_markdown(summary))
    return summary


def validate_case(
    case_dir: Path,
    *,
    runs: int = 10,
    hours: int = 168,
    base: str = "http://127.0.0.1:5002",
    results_dir: Path = DEFAULT_RESULTS_DIR,
    client: Optional[ApiClient] = None,
    sleep: Callable[[float], None] = time.sleep,
    poll_interval: float = 5.0,
) -> Dict[str, Any]:
    case_dir = case_dir.resolve()
    validate_case_files(case_dir)
    if isinstance(runs, bool) or not 1 <= runs <= 100:
        raise ValueError("runs muss zwischen 1 und 100 liegen")
    if isinstance(hours, bool) or not 1 <= hours <= 336:
        raise ValueError("hours muss zwischen 1 und 336 liegen")
    outcomes = load_outcomes(case_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    state_path = results_dir / f"{case_dir.name}.state.json"
    state = load_or_create_state(state_path, case_dir.name, base, runs, hours)
    api = client or ApiClient(base)
    prepare_simulation(
        api, case_dir, state_path, state, sleep=sleep, poll_interval=poll_interval
    )
    ensemble = run_ensemble(
        api,
        outcomes,
        state_path,
        state,
        sleep=sleep,
        poll_interval=poll_interval,
    )
    result = build_case_result(
        case_dir.name, outcomes, ensemble, runs=runs, hours=hours
    )
    _write_json_atomic(results_dir / f"{case_dir.name}.json", result)
    _write_text_atomic(results_dir / f"{case_dir.name}.md", case_markdown(result))
    update_summary(results_dir)
    return result


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_dir", type=Path, help="Ordner mit ausgangslage.md, verlauf.md und ergebnisse.json")
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--hours", type=int, default=168)
    parser.add_argument("--base", default="http://127.0.0.1:5002")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = parse_args(argv)
    try:
        result = validate_case(
            arguments.case_dir,
            runs=arguments.runs,
            hours=arguments.hours,
            base=arguments.base,
        )
    except (ApiError, OSError, ValueError) as error:
        print(f"Fehler: {error}", file=sys.stderr)
        return 1
    print(f"Auswertung geschrieben: {DEFAULT_RESULTS_DIR / (result['case'] + '.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
