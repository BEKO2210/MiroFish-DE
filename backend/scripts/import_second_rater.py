#!/usr/bin/env python3
"""Gespeicherte Antworten eines nachträglichen Zweitbewerters importieren."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.ensemble import (
    EnsembleService,
    _write_json_atomic,
    combine_rater_results,
)
try:
    from scripts.deferred_rater_common import parse_answer, replay_run, run_input
except ImportError:  # direkter Aufruf als python scripts/import_second_rater.py
    from deferred_rater_common import parse_answer, replay_run, run_input


def _batch_number(path: Path) -> int:
    return int(path.stem.split("_", 1)[1])


def _load_prompt_answers(directory: Path) -> List[Tuple[Dict[str, Any], Any]]:
    result: List[Tuple[Dict[str, Any], Any]] = []
    for prompt_path in sorted(directory.glob("batch_*.json"), key=_batch_number):
        prompt = json.loads(prompt_path.read_text(encoding="utf-8"))
        answer_path = prompt_path.with_suffix(".answer.txt")
        try:
            answer: Any = parse_answer(answer_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError) as error:
            # Offline keine Nachfrage und kein stilles Nein: dieser Stapel bleibt unklassifiziert.
            answer = ValueError(f"Ungültige oder fehlende Offline-Antwort: {error}")
        result.append((prompt, answer))
    if not result:
        raise ValueError(f"Keine batch_*.json in {directory}")
    return result


def import_second_rater(
    ensemble_dir: Path, prompts_dir: Path, model: str,
) -> Dict[str, Any]:
    ensemble_dir, prompts_dir = ensemble_dir.resolve(), prompts_dir.resolve()
    model = model.strip()
    if not model:
        raise ValueError("model darf nicht leer sein")
    state_path = ensemble_dir / "ensemble.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("second_rater") != "deferred":
        raise ValueError("Ensemble wurde nicht mit second_rater=deferred gestartet")
    primary_model = str((state.get("models") or {}).get("classification_primary") or "").strip()
    if state.get("strict_second_rater") and model == primary_model:
        raise ValueError("Haupt- und Zweitbewerter müssen verschiedene Modellnamen haben")
    manifest = json.loads((prompts_dir / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("ensemble_id") != state.get("ensemble_id"):
        raise ValueError("Prompt-Export gehört zu einem anderen Ensemble")
    token_budget = int(manifest.get("token_budget") or 30000)
    service = EnsembleService(root=ensemble_dir.parent)
    pending: List[Tuple[Path, Dict[str, Any]]] = []
    per_run: Dict[str, List[Dict[str, Any]]] = {}

    for variant in state.get("variants") or []:
        arm = str(variant["key"])
        per_run[arm] = []
        for run_number in range(1, int(state["runs"]) + 1):
            run_dir, source = run_input(ensemble_dir, arm, run_number)
            classification_path = run_dir / "classification.json"
            classification = json.loads(classification_path.read_text(encoding="utf-8"))
            rater_a = ((classification.get("raters") or {}).get("a") or {}).get("result")
            if not isinstance(rater_a, dict):
                raise ValueError(f"Hauptbewertung fehlt in {classification_path}")
            prompt_answers = _load_prompt_answers(prompts_dir / arm / f"run_{run_number}")
            rater_b, audit_b = replay_run(
                service, state, arm, run_number, source, token_budget, prompt_answers,
            )
            combined = combine_rater_results(rater_a, rater_b, state["checklist"])
            classification["raters"]["b"] = {
                "model": model, "seed": None, "seed_fallback": False, **audit_b,
            }
            classification["result"] = combined
            classification["second_rater_status"] = "vollständig"
            pending.append((classification_path, classification))
            per_run[arm].append(combined)

    # Erst nach vollständiger Prüfung schreiben; das Original bleibt daneben erhalten.
    for classification_path, classification in pending:
        backup = classification_path.with_name("classification.primary-only.json")
        if not backup.exists():
            shutil.copy2(classification_path, backup)
        _write_json_atomic(classification_path, classification)

    state["second_rater_status"] = "vollständig"
    state["results_preliminary"] = False
    state["models"]["classification_secondary"] = model
    for variant in state.get("variants") or []:
        variant.setdefault("classification_models", {})["secondary"] = model
    service._aggregate(state, per_run)
    service._save(state)
    return state


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ensemble-dir", type=Path, required=True)
    parser.add_argument("--prompts-dir", type=Path, required=True)
    parser.add_argument("--model", required=True)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        state = import_second_rater(args.ensemble_dir, args.prompts_dir, args.model)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"Fehler: {error}", file=sys.stderr)
        return 1
    print(f"Zweitbewertung vollständig importiert: {state['ensemble_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
