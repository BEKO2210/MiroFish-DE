#!/usr/bin/env python3
"""Nichtdeterminismus messen: denselben Seed zweimal laufen, Aktionslogs vergleichen.

Usage:
  python repro_check.py <sim_dir> [--seed N] [--max-rounds N] [--work-dir DIR]
  python repro_check.py --compare-only <dir_a> <dir_b>

Startet zwei Kopien über run_parallel_simulation.py (wie der Runner: --config,
--seed, --no-wait). Gibt Reihenfolge-Identität und Jaccard der Texte aus.
GPU-Lauf nicht in CI — Vergleichslogik mit Fixture-Logs testen.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

_SCRIPTS = Path(__file__).resolve().parent
_WS_RE = re.compile(r"\s+")

ActionKey = Tuple[str, Any, str]  # action_type, agent, normalized text


def normalize_text(text: str) -> str:
    return _WS_RE.sub(" ", (text or "").strip().lower())


def _action_text(entry: Dict[str, Any]) -> str:
    args = entry.get("action_args") or {}
    for key in ("content", "text", "body", "quote_content", "comment"):
        val = args.get(key)
        if isinstance(val, str) and val.strip():
            return val
    result = entry.get("result")
    if isinstance(result, str):
        return result
    return ""


def load_actions(sim_dir: str | Path) -> List[ActionKey]:
    """Aktionszeilen aus twitter/ und reddit/actions.jsonl (ohne round_start/end)."""
    root = Path(sim_dir)
    out: List[ActionKey] = []
    for platform in ("twitter", "reddit"):
        path = root / platform / "actions.jsonl"
        if not path.is_file():
            continue
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("event_type"):
                    continue
                action_type = entry.get("action_type")
                if not action_type:
                    continue
                agent = entry.get("agent_id")
                if agent is None:
                    agent = entry.get("agent_name", "")
                out.append(
                    (str(action_type), agent, normalize_text(_action_text(entry)))
                )
    return out


def sequential_identity(a: Sequence[ActionKey], b: Sequence[ActionKey]) -> float:
    """Anteil identischer Aktionen an derselben Position (über min-Länge; 1.0 wenn beide leer)."""
    if not a and not b:
        return 1.0
    n = max(len(a), len(b))
    if n == 0:
        return 1.0
    matched = sum(1 for i in range(min(len(a), len(b))) if a[i] == b[i])
    return matched / n


def text_jaccard(a: Sequence[ActionKey], b: Sequence[ActionKey]) -> float:
    """Jaccard über normalisierte Aktionstexte (leere Texte ignoriert)."""
    sa = {t for _, _, t in a if t}
    sb = {t for _, _, t in b if t}
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def compare_action_logs(dir_a: str | Path, dir_b: str | Path) -> Dict[str, Any]:
    actions_a = load_actions(dir_a)
    actions_b = load_actions(dir_b)
    return {
        "count_a": len(actions_a),
        "count_b": len(actions_b),
        "sequential_identity": sequential_identity(actions_a, actions_b),
        "text_jaccard": text_jaccard(actions_a, actions_b),
    }


_COPY_NAMES = (
    "simulation_config.json",
    "state.json",
    "twitter_profiles.csv",
    "reddit_profiles.json",
)


def prepare_run_copy(source: Path, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=False)
    for name in _COPY_NAMES:
        src = source / name
        if src.is_file():
            shutil.copy2(src, dest / name)
    config_path = dest / "simulation_config.json"
    if not config_path.is_file():
        raise FileNotFoundError(f"Keine simulation_config.json in {source}")
    return config_path


def run_simulation_cli(
    config_path: Path,
    seed: int,
    max_rounds: Optional[int] = None,
    script: Optional[Path] = None,
) -> int:
    """Wie SimulationRunner: python run_parallel_simulation.py --config --seed --no-wait."""
    script = script or (_SCRIPTS / "run_parallel_simulation.py")
    cmd = [
        sys.executable,
        str(script),
        "--config",
        str(config_path),
        "--seed",
        str(seed),
        "--no-wait",
    ]
    if max_rounds is not None and max_rounds > 0:
        cmd.extend(["--max-rounds", str(max_rounds)])
    env = os.environ.copy()
    env["MIROFISH_SIM_SEED"] = str(seed)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        cmd,
        cwd=str(config_path.parent),
        env=env,
        check=False,
    )
    return int(proc.returncode)


def measure_repro(
    sim_dir: Path,
    seed: int,
    max_rounds: Optional[int] = None,
    work_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    cleanup = work_dir is None
    root = Path(work_dir) if work_dir else Path(tempfile.mkdtemp(prefix="repro_check_"))
    try:
        a = root / "run_a"
        b = root / "run_b"
        cfg_a = prepare_run_copy(sim_dir, a)
        cfg_b = prepare_run_copy(sim_dir, b)
        code_a = run_simulation_cli(cfg_a, seed=seed, max_rounds=max_rounds)
        code_b = run_simulation_cli(cfg_b, seed=seed, max_rounds=max_rounds)
        metrics = compare_action_logs(a, b)
        metrics["exit_a"] = code_a
        metrics["exit_b"] = code_b
        metrics["seed"] = seed
        metrics["run_a"] = str(a)
        metrics["run_b"] = str(b)
        return metrics
    finally:
        if cleanup and root.is_dir():
            # shortcut: behalten bei Misserfolg wäre nützlich; Aufrufer nutzt --work-dir
            pass


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Gleichen Seed zweimal laufen und Aktionslogs vergleichen"
    )
    parser.add_argument(
        "sim_dir",
        nargs="?",
        help="Vorbereiteter Simulationsordner mit simulation_config.json",
    )
    parser.add_argument("--seed", type=int, default=None, help="Seed (Standard: aus run_state oder 0)")
    parser.add_argument("--max-rounds", type=int, default=None)
    parser.add_argument("--work-dir", type=str, default=None, help="Arbeitsordner für die zwei Kopien")
    parser.add_argument(
        "--compare-only",
        nargs=2,
        metavar=("DIR_A", "DIR_B"),
        help="Nur vorhandene Aktionslogs vergleichen (kein GPU-Lauf)",
    )
    args = parser.parse_args(argv)

    if args.compare_only:
        metrics = compare_action_logs(args.compare_only[0], args.compare_only[1])
        print(json.dumps(metrics, ensure_ascii=False, indent=2))
        return 0

    if not args.sim_dir:
        parser.error("sim_dir oder --compare-only erforderlich")
    sim_dir = Path(args.sim_dir).resolve()
    if not (sim_dir / "simulation_config.json").is_file():
        print(f"Fehler: keine simulation_config.json in {sim_dir}", file=sys.stderr)
        return 2

    seed = args.seed
    if seed is None:
        run_state = sim_dir / "run_state.json"
        if run_state.is_file():
            try:
                seed = int(json.loads(run_state.read_text(encoding="utf-8")).get("seed", 0))
            except (OSError, ValueError, TypeError):
                seed = 0
        else:
            seed = 0

    metrics = measure_repro(
        sim_dir,
        seed=seed,
        max_rounds=args.max_rounds,
        work_dir=Path(args.work_dir) if args.work_dir else None,
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(
        f"sequential_identity={metrics['sequential_identity']:.4f} "
        f"text_jaccard={metrics['text_jaccard']:.4f}",
        file=sys.stderr,
    )
    return 0 if metrics.get("exit_a", 0) == 0 and metrics.get("exit_b", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
