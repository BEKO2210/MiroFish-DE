#!/usr/bin/env python3
"""Bewertermodelle mit gespeicherten Ensemble-Läufen und Referenzen vergleichen."""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import Config
from app.services.ensemble import EnsembleService, cohens_kappa, load_simulation_posts


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"JSON kann nicht gelesen werden: {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"JSON muss ein Objekt sein: {path}")
    return value


def _run_number(path: Path) -> int:
    try:
        return int(path.name.removeprefix("run_"))
    except ValueError as error:
        raise ValueError(f"Ungültiges Laufverzeichnis: {path}") from error


def discover_runs(ensemble_dir: Path, state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Vorhandene run_N-Verzeichnisse in der Reihenfolge des Ensemble-Zustands finden."""
    runs: List[Dict[str, Any]] = []
    for variant in state.get("variants") or []:
        arm = str(variant.get("key") or "").strip()
        if not arm:
            continue
        candidates = [path for path in (ensemble_dir / arm).glob("run_*") if path.is_dir()]
        for run_dir in sorted(candidates, key=_run_number):
            run = _run_number(run_dir)
            narrative_path = run_dir / "narrative.txt"
            if narrative_path.is_file():
                kind = "narrative"
            elif any((run_dir / f"{platform}_simulation.db").is_file()
                     for platform in ("twitter", "reddit")):
                kind = "simulation"
            else:
                raise ValueError(
                    f"Lauf enthält weder narrative.txt noch Simulations-DB: {run_dir}"
                )
            runs.append({"arm": arm, "run": run, "kind": kind, "path": run_dir})
    if not runs:
        raise ValueError(f"Keine Läufe unter {ensemble_dir} gefunden")
    return runs


def load_reference(reference_dir: Path, arm: str, run: int) -> Dict[str, bool]:
    path = reference_dir / f"ref_{arm}_{run}.json"
    payload = _read_json(path)
    result: Dict[str, bool] = {}
    for outcome_id, raw in payload.items():
        if not isinstance(raw, dict) or not isinstance(raw.get("yes"), bool):
            raise ValueError(
                f"Referenz {path}: {outcome_id!r} braucht das Format {{\"yes\": true|false}}"
            )
        result[str(outcome_id)] = raw["yes"]
    if not result:
        raise ValueError(f"Referenz ist leer: {path}")
    return result


def _prediction(judgment: Any) -> Optional[bool]:
    if not isinstance(judgment, dict):
        return None
    if judgment.get("unclassified") or judgment.get("disputed"):
        return None
    return bool(judgment["yes"]) if isinstance(judgment.get("yes"), bool) else None


def _metric(rows: Iterable[Tuple[Optional[bool], bool]]) -> Dict[str, Any]:
    values = list(rows)
    classified = [(prediction, reference) for prediction, reference in values
                  if prediction is not None]
    pairs = [(bool(prediction), reference) for prediction, reference in classified]
    kappa = cohens_kappa(pairs)
    correct = sum(prediction == reference for prediction, reference in pairs)
    return {
        "agreement": round(correct / len(pairs), 6) if pairs else None,
        "kappa": kappa["kappa"],
        "pairs": len(pairs),
        "unclassified": len(values) - len(pairs),
        "total": len(values),
    }


def _reference_metrics(records: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    def selected(*, kind: Optional[str] = None, outcome_id: Optional[str] = None):
        for record in records:
            if kind is not None and record["kind"] != kind:
                continue
            for oid, reference in record["reference"].items():
                if outcome_id is None or oid == outcome_id:
                    yield record["predictions"].get(oid), reference

    return {
        "overall": _metric(selected()),
        "simulation": _metric(selected(kind="simulation")),
        "narrative": _metric(selected(kind="narrative")),
        "c1": _metric(selected(outcome_id="c1")),
    }


def _pair_metric(
    left_records: Sequence[Dict[str, Any]], right_records: Sequence[Dict[str, Any]]
) -> Dict[str, Any]:
    right_by_run = {(row["arm"], row["run"]): row for row in right_records}
    values: List[Tuple[Optional[bool], Optional[bool]]] = []
    for left in left_records:
        right = right_by_run.get((left["arm"], left["run"]))
        if right is None:
            continue
        outcome_ids = sorted(set(left["predictions"]) | set(right["predictions"]))
        values.extend((left["predictions"].get(oid), right["predictions"].get(oid))
                      for oid in outcome_ids)
    pairs = [(bool(left), bool(right)) for left, right in values
             if left is not None and right is not None]
    metric = cohens_kappa(pairs)
    return {
        **metric,
        "unclassified": len(values) - len(pairs),
        "total": len(values),
    }


def _classify_run(
    service: EnsembleService,
    state: Dict[str, Any],
    run: Dict[str, Any],
    llm: Any,
    context: Dict[str, Any],
) -> Dict[str, Optional[bool]]:
    run_dir, run_number = run["path"], run["run"]
    seed = int(state.get("base_seed") or 0) + run_number
    if run["kind"] == "narrative":
        result, _ = service._classify_narrative_once(
            state,
            (run_dir / "narrative.txt").read_text(encoding="utf-8"),
            seed,
            run_number,
            llm,
            run["arm"],
            context,
        )
    else:
        config_path = run_dir / "simulation_config.json"
        config = _read_json(config_path) if config_path.is_file() else {}
        initial = (config.get("event_config") or {}).get("initial_posts") or []
        result, _ = service._classify_posts_once(
            state,
            load_simulation_posts(run_dir, initial),
            seed,
            run_number,
            run_dir,
            llm,
            context,
        )
    return {str(item["id"]): _prediction(result.get(str(item["id"])))
            for item in state["checklist"]}


def _markdown(report: Dict[str, Any]) -> str:
    lines = [
        "# Bewerter-Benchmark",
        "",
        f"Ensemble: `{report['ensemble_dir']}`  ",
        f"Modus: `{report['mode']}`",
        "",
        "## Referenzvergleich",
        "",
        "| Modell | Bereich | Übereinstimmung | Kappa | klassifiziert / gesamt | unklassifiziert | Dauer (s) |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    labels = {"overall": "gesamt", "simulation": "Simulation",
              "narrative": "Erzählung", "c1": "Primärfrage c1"}
    for model in report["models"]:
        for key, metric in model["metrics"].items():
            agreement = (f"{metric['agreement']:.1%}"
                         if metric["agreement"] is not None else "nicht messbar")
            kappa = f"{metric['kappa']:.4f}" if metric["kappa"] is not None else "nicht messbar"
            lines.append(
                f"| {model['model']} | {labels[key]} | {agreement} | {kappa} | "
                f"{metric['pairs']} / {metric['total']} | {metric['unclassified']} | "
                f"{model['duration_seconds']:.3f} |"
            )
    if report.get("pairs"):
        lines.extend([
            "", "## Modellpaare", "",
            "| Hauptbewerter | Zweitbewerter | Übereinstimmung | Kappa | Paare / gesamt | unklassifiziert |",
            "|---|---|---:|---:|---:|---:|",
        ])
        for row in report["pairs"]:
            agreement = (f"{row['agreement']:.1%}"
                         if row["agreement"] is not None else "nicht messbar")
            kappa = f"{row['kappa']:.4f}" if row["kappa"] is not None else "nicht messbar"
            lines.append(
                f"| {row['primary']} | {row['secondary']} | {agreement} | {kappa} | "
                f"{row['n_pairs']} / {row['total']} | {row['unclassified']} |"
            )
    return "\n".join(lines) + "\n"


def run_benchmark(
    ensemble_dir: Path,
    reference_dir: Path,
    models: Sequence[str],
    output_dir: Path,
    *,
    mode: str = "referenz",
    service: Optional[EnsembleService] = None,
    clock: Callable[[], float] = time.perf_counter,
) -> Dict[str, Any]:
    ensemble_dir, reference_dir, output_dir = map(Path, (ensemble_dir, reference_dir, output_dir))
    if mode not in {"referenz", "paare"}:
        raise ValueError("Modus muss referenz oder paare sein")
    state = _read_json(ensemble_dir / "ensemble.json")
    if not isinstance(state.get("checklist"), list) or not state["checklist"]:
        raise ValueError("ensemble.json enthält keine Checkliste")
    runs = discover_runs(ensemble_dir, state)
    references = {
        (run["arm"], run["run"]): load_reference(reference_dir, run["arm"], run["run"])
        for run in runs
    }
    checklist_ids = {str(item["id"]) for item in state["checklist"]}
    for (arm, run), reference in references.items():
        unknown = sorted(set(reference) - checklist_ids)
        missing = sorted(checklist_ids - set(reference))
        if unknown or missing:
            details = []
            if unknown:
                details.append("unbekannte IDs: " + ", ".join(unknown))
            if missing:
                details.append("fehlende IDs: " + ", ".join(missing))
            raise ValueError(f"Referenz ref_{arm}_{run}.json: " + "; ".join(details))
    model_names = list(dict.fromkeys(
        str(value).strip() for value in models if str(value).strip()
    ))
    if not model_names:
        raise ValueError("Mindestens ein Modellname ist erforderlich")
    if mode == "paare" and len(model_names) < 2:
        raise ValueError("Modus paare erfordert ein Hauptmodell und mindestens einen Kandidaten")
    service = service or EnsembleService(root=output_dir)
    model_rows: List[Dict[str, Any]] = []
    records_by_model: Dict[str, List[Dict[str, Any]]] = {}
    for model in model_names:
        started = clock()
        llm = service._llm_for_model(model)
        context = service._classification_context(llm)
        records = []
        for run in runs:
            reference = references[(run["arm"], run["run"])]
            predictions = _classify_run(service, state, run, llm, context)
            records.append({
                "arm": run["arm"], "run": run["run"], "kind": run["kind"],
                "reference": reference,
                "predictions": {oid: predictions.get(oid) for oid in reference},
            })
        duration = clock() - started
        records_by_model[model] = records
        model_rows.append({
            "model": model,
            "duration_seconds": round(duration, 6),
            "unclassified": sum(
                value is None for row in records for value in row["predictions"].values()
            ),
            "metrics": _reference_metrics(records),
            "runs": records,
        })
    pairs = []
    if mode == "paare":
        primary = next(iter(records_by_model))
        for secondary in list(records_by_model)[1:]:
            pairs.append({
                "primary": primary,
                "secondary": secondary,
                **_pair_metric(records_by_model[primary], records_by_model[secondary]),
            })
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ensemble_dir": str(ensemble_dir.resolve()),
        "reference_dir": str(reference_dir.resolve()),
        "mode": mode,
        "models": model_rows,
        "pairs": pairs,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "rater_benchmark.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "rater_benchmark.md").write_text(_markdown(report), encoding="utf-8")
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ensemble-dir", required=True, type=Path)
    parser.add_argument("--reference-dir", required=True, type=Path)
    parser.add_argument("--models", required=True, nargs="+")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--mode", "--modus", choices=("referenz", "paare"), default="referenz")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    if str(Config.LLM_PROVIDER).lower() != "ollama":
        raise SystemExit(
            "rater_benchmark.py erlaubt nur LLM_PROVIDER=ollama an LOCAL_LLM_BASE_URL"
        )
    try:
        run_benchmark(
            args.ensemble_dir, args.reference_dir, args.models, args.output_dir,
            mode=args.mode,
        )
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Fehler: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
