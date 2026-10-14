#!/usr/bin/env python3
"""Prompts für den nachträglichen, unabhängigen Zweitbewerter exportieren."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.ensemble import EnsembleService
try:
    from scripts.deferred_rater_common import capture_run_prompts, run_input
except ImportError:  # direkter Aufruf als python scripts/export_rater_prompts.py
    from deferred_rater_common import capture_run_prompts, run_input


def export_prompts(ensemble_dir: Path, out_dir: Path, token_budget: int = 30000) -> int:
    ensemble_dir, out_dir = ensemble_dir.resolve(), out_dir.resolve()
    state = json.loads((ensemble_dir / "ensemble.json").read_text(encoding="utf-8"))
    service = EnsembleService(root=ensemble_dir.parent)
    count = 0
    for variant in state.get("variants") or []:
        arm = str(variant["key"])
        for run_number in range(1, int(state["runs"]) + 1):
            _, source = run_input(ensemble_dir, arm, run_number)
            prompts = capture_run_prompts(
                service, state, arm, run_number, source, token_budget,
            )
            target = out_dir / arm / f"run_{run_number}"
            target.mkdir(parents=True, exist_ok=True)
            for index, prompt in enumerate(prompts, 1):
                (target / f"batch_{index}.json").write_text(
                    json.dumps(prompt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
                )
                count += 1
    (out_dir / "manifest.json").write_text(json.dumps({
        "ensemble_id": state.get("ensemble_id"), "token_budget": token_budget,
        "batches": count,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return count


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ensemble-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--token-budget", type=int, default=30000)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        count = export_prompts(args.ensemble_dir, args.out_dir, args.token_budget)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"Fehler: {error}", file=sys.stderr)
        return 1
    print(f"{count} Bewertungsstapel exportiert: {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
