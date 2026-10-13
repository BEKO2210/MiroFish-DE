"""Mehrfachläufe, Gegenproben und deterministische Ensemble-Auswertung (V3/V4)."""

from __future__ import annotations

import csv
import json
import math
import os
import random
import re
import shutil
import sqlite3
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from ..config import Config
from ..utils.logger import get_logger
from ..utils.llm_client import estimate_tokens
from .report_validation import (
    CONTENT_OVERLAP_THRESHOLD,
    MIN_CONTENT_WORDS,
    best_content_match,
    content_stems,
    load_simulation_context,
)

logger = get_logger("mirofish.ensemble")

Z_95 = 1.959963984540054
TERMINAL_RUNNER_STATES = {"completed", "failed", "stopped"}
ENSEMBLE_STATUSES = {"queued", "running", "completed", "failed", "cancelled"}

VARIANT_LABELS = {
    "baseline": ("Basislauf", "Baseline"),
    "isolated": ("Ohne Vernetzung", "Isolated"),
    "null_model": ("Nullmodell", "Null model"),
}


def wilson_interval(yes: int, n: int, z: float = Z_95) -> Tuple[float, float]:
    """Zweiseitiges Wilson-Score-Intervall für einen Binomialanteil."""
    if n <= 0:
        return 0.0, 0.0
    p = yes / n
    z2 = z * z
    denominator = 1.0 + z2 / n
    center = (p + z2 / (2.0 * n)) / denominator
    half = z * math.sqrt((p * (1.0 - p) + z2 / (4.0 * n)) / n) / denominator
    return max(0.0, center - half), min(1.0, center + half)


def newcombe_difference_interval(
    yes_variant: int,
    n_variant: int,
    yes_baseline: int,
    n_baseline: int,
    z: float = Z_95,
) -> Tuple[float, float]:
    """Newcombe-Methode 10: Differenz zweier unabhängiger Anteile."""
    if n_variant <= 0 or n_baseline <= 0:
        return 0.0, 0.0
    p1 = yes_variant / n_variant
    p2 = yes_baseline / n_baseline
    l1, u1 = wilson_interval(yes_variant, n_variant, z)
    l2, u2 = wilson_interval(yes_baseline, n_baseline, z)
    difference = p1 - p2
    lower = difference - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    upper = difference + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return max(-1.0, lower), min(1.0, upper)


def _round(value: float) -> float:
    return round(float(value), 4)


ABSENCE_RE = re.compile(r"\b(?:nicht|kein(?:e|en|er|es)?|bleibt\s+aus)\b", re.IGNORECASE)


def infer_polarity(text: str) -> str:
    """Alte Checklisten anhand eindeutig negativer Formulierungen migrieren."""
    return "absence" if ABSENCE_RE.search(text or "") else "presence"


def _positive_event_text(item: Dict[str, Any]) -> str:
    explicit = str(item.get("presence_event") or "").strip()
    if explicit:
        return explicit
    text = f"{item.get('text_de', '')} -- {item.get('definition', '')}".strip()
    text = re.sub(r"\bbleibt\s+aus\b", "findet statt", text, flags=re.IGNORECASE)
    text = re.sub(r"\bkeine\b", "eine", text, flags=re.IGNORECASE)
    text = re.sub(r"\bkein\b", "ein", text, flags=re.IGNORECASE)
    text = re.sub(r"\bnicht\b", "", text, flags=re.IGNORECASE)
    return " ".join(text.split())


def parse_checklist(payload: Any) -> List[Dict[str, Any]]:
    """Strikte, aber tolerante Normalisierung einer Modell-Checkliste."""
    if isinstance(payload, dict):
        items = payload.get("outcomes", payload.get("checklist", []))
    else:
        items = payload
    if not isinstance(items, list):
        raise ValueError("Checkliste muss eine Liste enthalten")

    result: List[Dict[str, str]] = []
    seen = set()
    for raw in items:
        if isinstance(raw, str):
            text = raw.strip()
            definition = text
        elif isinstance(raw, dict):
            text = str(raw.get("text_de") or raw.get("text") or "").strip()
            definition = str(raw.get("definition") or text).strip()
        else:
            continue
        key = " ".join(text.lower().split())
        if not text or key in seen:
            continue
        seen.add(key)
        supplied = str(raw.get("polarity") or "").strip().lower() if isinstance(raw, dict) else ""
        polarity = supplied if supplied in {"presence", "absence"} else infer_polarity(f"{text} {definition}")
        item: Dict[str, Any] = {
            "id": f"o{len(result) + 1}",
            "text_de": text,
            "definition": definition,
            "polarity": polarity,
        }
        if isinstance(raw, dict) and str(raw.get("presence_event") or "").strip():
            item["presence_event"] = str(raw["presence_event"]).strip()
        result.append(item)
    if not 5 <= len(result) <= 8:
        raise ValueError("Das Modell muss 5 bis 8 eindeutige Ergebnisse liefern")
    return result


def _number_tokens(text: str) -> set[str]:
    """Zahlen vergleichbar machen (z. B. 3.100 und 3100)."""
    return {
        re.sub(r"\D", "", match.group(0)).lstrip("0") or "0"
        for match in re.finditer(r"(?<!\w)\d+(?:[.,]\d+)*(?:\s*%)?(?!\w)", text or "")
    }


def filter_checklist_material_numbers(
    checklist: Sequence[Dict[str, Any]], material: str
) -> List[Dict[str, Any]]:
    """Ergebnisse mit einer im Material vorkommenden Zahl deterministisch verwerfen."""
    material_numbers = _number_tokens(material)
    if not material_numbers:
        return [dict(item) for item in checklist]
    return [
        dict(item)
        for item in checklist
        if not (
            _number_tokens(
                f"{item.get('text_de', '')} {item.get('definition', '')}"
            )
            & material_numbers
        )
    ]


def verified_material_quote(payload: Any, material: str) -> str:
    """Nur ein als vorhanden bewertetes, normalisiert wörtliches Zitat akzeptieren."""
    if not isinstance(payload, dict) or payload.get("in_material") is not True:
        return ""
    quote = " ".join(str(payload.get("zitat") or "").split())
    normalized_material = " ".join((material or "").split())
    if quote and quote.casefold() in normalized_material.casefold():
        return quote
    return ""


def mark_checklist_material(
    checklist: Sequence[Dict[str, Any]],
    extracted_text: str,
    initial_posts: Sequence[Dict[str, Any]],
    quote_checks: Sequence[Any] = (),
) -> List[Dict[str, Any]]:
    """Checklistenpunkte per Inhaltswortabgleich oder verifiziertem Zitat markieren."""
    sources: List[Tuple[str, str]] = []
    if extracted_text:
        sources.append(("Material", extracted_text))
    for index, post in enumerate(initial_posts):
        text = str(post.get("content") or "") if isinstance(post, dict) else str(post)
        if text:
            sources.append((f"Startbeitrag[{index}]", text))
    quote_material = "\n".join(source for _, source in sources)

    marked = []
    for index, item in enumerate(checklist):
        candidate = dict(item)
        query = f"{candidate.get('text_de', '')} {candidate.get('definition', '')}".strip()
        best_ratio = 0.0
        if len(content_stems(query)) >= MIN_CONTENT_WORDS:
            for _, source in sources:
                ratio, _ = best_content_match(query, source)
                if ratio > best_ratio:
                    best_ratio = ratio
        quote_payload = quote_checks[index] if index < len(quote_checks) else None
        quote = verified_material_quote(quote_payload, quote_material)
        candidate["in_material"] = bool(
            best_ratio >= CONTENT_OVERLAP_THRESHOLD or quote
        )
        candidate["material_snippet"] = quote
        marked.append(candidate)
    return marked


def _variant_label(key: str) -> Tuple[str, str]:
    if key.startswith("without:"):
        kind = key.split(":", 1)[1]
        return f"Ohne {kind}", f"Without {kind}"
    return VARIANT_LABELS[key]


def validate_variants(variants: Any) -> List[str]:
    if not isinstance(variants, list) or not variants:
        raise ValueError("variants muss eine nicht-leere Liste sein")
    clean: List[str] = []
    for value in variants:
        key = str(value).strip()
        without_type = key.split(":", 1)[1].strip() if key.startswith("without:") else ""
        if key not in VARIANT_LABELS and not (
            key.startswith("without:")
            and without_type
            and without_type not in {".", ".."}
            and "/" not in without_type
            and "\\" not in without_type
        ):
            raise ValueError(f"Unbekannte Variante: {key}")
        if key not in clean:
            clean.append(key)
    if "baseline" not in clean:
        raise ValueError("baseline ist als Variante Pflicht")
    return clean


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def _write_json_atomic(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
    os.replace(temporary, path)


def _agent_id(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def apply_without_variant(
    config: Dict[str, Any],
    reddit_profiles: List[Dict[str, Any]],
    twitter_rows: List[Dict[str, str]],
    agent_type: str,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, str]]]:
    """Akteurstyp entfernen und verbleibende IDs lückenlos neu nummerieren."""
    copied = json.loads(json.dumps(config, ensure_ascii=False))
    agents = copied.get("agent_configs") or []
    target = agent_type.casefold()
    removed = {
        _agent_id(agent.get("agent_id"))
        for agent in agents
        if str(agent.get("entity_type") or "").casefold() == target
    }
    removed.discard(None)
    if not removed:
        raise ValueError(f"Akteurstyp nicht vorhanden: {agent_type}")

    kept = [a for a in agents if _agent_id(a.get("agent_id")) not in removed]
    if not kept:
        raise ValueError(f"Variante without:{agent_type} würde alle Agenten entfernen")
    mapping = {
        old: new
        for new, old in enumerate(
            _agent_id(a.get("agent_id")) for a in kept
        )
        if old is not None
    }
    for agent in kept:
        agent["agent_id"] = mapping[_agent_id(agent.get("agent_id"))]
    copied["agent_configs"] = kept

    event = copied.setdefault("event_config", {})
    posts = []
    for post in event.get("initial_posts") or []:
        old = _agent_id(post.get("poster_agent_id"))
        if old in removed or old not in mapping:
            continue
        post["poster_agent_id"] = mapping[old]
        posts.append(post)
    event["initial_posts"] = posts

    reddit_out = []
    for profile in reddit_profiles:
        old = _agent_id(profile.get("user_id"))
        if old in mapping:
            item = dict(profile)
            item["user_id"] = mapping[old]
            reddit_out.append(item)

    twitter_out = []
    for profile in twitter_rows:
        id_field = "user_id" if "user_id" in profile else "agent_id"
        old = _agent_id(profile.get(id_field))
        if old in mapping:
            item = dict(profile)
            item[id_field] = str(mapping[old])
            twitter_out.append(item)
    return copied, reddit_out, twitter_out


def _read_twitter_csv(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _write_twitter_csv(path: Path, fields: Sequence[str], rows: Iterable[Dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def prepare_run_directory(
    source_dir: Path, run_dir: Path, variant: str, hours: int, start_hour: int = 7
) -> Dict[str, Any]:
    """Vorbereitete Profile/Config kopieren und nur die Variante anwenden."""
    run_dir.mkdir(parents=True, exist_ok=False)
    config = _read_json(source_dir / "simulation_config.json")
    reddit_path = source_dir / "reddit_profiles.json"
    twitter_path = source_dir / "twitter_profiles.csv"
    with reddit_path.open("r", encoding="utf-8") as handle:
        reddit = json.load(handle)
    fields, twitter = _read_twitter_csv(twitter_path)

    if variant.startswith("without:"):
        config, reddit, twitter = apply_without_variant(
            config, reddit, twitter, variant.split(":", 1)[1]
        )
    time_config = config.setdefault("time_config", {})
    time_config["total_simulation_hours"] = hours
    time_config["start_hour"] = start_hour
    config["ensemble_variant"] = variant
    config["simulation_id"] = run_dir.name

    _write_json_atomic(run_dir / "simulation_config.json", config)
    with (run_dir / "reddit_profiles.json").open("w", encoding="utf-8") as handle:
        json.dump(reddit, handle, ensure_ascii=False, indent=2)
    _write_twitter_csv(run_dir / "twitter_profiles.csv", fields, twitter)
    source_state = source_dir / "state.json"
    if source_state.is_file():
        shutil.copy2(source_state, run_dir / "state.json")
    return config


def _table_columns(connection: sqlite3.Connection, table: str) -> set[str]:
    try:
        return {str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})")}
    except sqlite3.Error:
        return set()


def load_simulation_posts(
    run_dir: Path,
    initial_posts: Sequence[Dict[str, Any]] = (),
) -> List[Dict[str, Any]]:
    """Beiträge direkt aus OASIS-SQLite lesen; Startbeiträge auslassen."""
    initial = {
        (_agent_id(p.get("poster_agent_id")), " ".join(str(p.get("content") or "").split()))
        for p in initial_posts
        if isinstance(p, dict)
    }
    result: List[Dict[str, Any]] = []
    for platform in ("twitter", "reddit"):
        db_path = run_dir / f"{platform}_simulation.db"
        if not db_path.is_file():
            continue
        connection = sqlite3.connect(str(db_path))
        connection.row_factory = sqlite3.Row
        try:
            columns = _table_columns(connection, "post")
            if not {"content", "user_id"}.issubset(columns):
                continue
            id_column = "post_id" if "post_id" in columns else "rowid"
            users = {}
            if _table_columns(connection, "user"):
                for row in connection.execute(
                    "SELECT user_id, agent_id, name, user_name FROM user"
                ):
                    users[row["user_id"]] = {
                        "agent_id": _agent_id(row["agent_id"]),
                        "name": row["name"] or row["user_name"] or f"Agent {row['agent_id']}",
                    }
            query = f"SELECT {id_column} AS post_id, user_id, content FROM post ORDER BY {id_column}"
            for row in connection.execute(query):
                user = users.get(row["user_id"], {})
                text = " ".join(str(row["content"] or "").split())
                if (user.get("agent_id", _agent_id(row["user_id"])), text) in initial:
                    continue
                result.append(
                    {
                        "platform": platform,
                        "post_id": f"{platform}:{row['post_id']}",
                        "agent": user.get("name") or f"Agent {row['user_id']}",
                        "text": text,
                    }
                )
        finally:
            connection.close()
    return result


def verify_classification_evidence(
    classification: Any,
    posts: Sequence[Dict[str, Any]],
    checklist: Sequence[Dict[str, Any]],
    run_number: int,
) -> Dict[str, Dict[str, Any]]:
    """Ja nur akzeptieren, wenn mindestens eine genannte ID wirklich existiert."""
    if isinstance(classification, dict):
        rows = classification.get("results", classification.get("outcomes", []))
    else:
        rows = classification
    rows = rows if isinstance(rows, list) else []
    by_outcome = {
        str(row.get("outcome_id")): row for row in rows if isinstance(row, dict)
    }
    by_id = {str(post["post_id"]): post for post in posts}
    verified: Dict[str, Dict[str, Any]] = {}
    for item in checklist:
        outcome_id = str(item["id"])
        raw = by_outcome.get(outcome_id)
        if not isinstance(raw, dict):
            verified[outcome_id] = {"yes": False, "evidence": [], "unclassified": True}
            continue
        answer = raw.get("yes", raw.get("answer", False))
        yes = answer is True or str(answer).strip().casefold() in {"ja", "yes", "true", "1"}
        evidence_ids = raw.get("post_ids", raw.get("evidence", []))
        if isinstance(evidence_ids, str):
            evidence_ids = [evidence_ids]
        evidence = []
        for post_id in evidence_ids if isinstance(evidence_ids, list) else []:
            found = by_id.get(str(post_id))
            if found:
                evidence.append({"run": run_number, **found})
        verified[outcome_id] = {"yes": bool(yes and evidence), "evidence": evidence}
    return verified


def _render_post(post: Dict[str, Any]) -> str:
    return f"[{post['post_id']}] {post['agent']}: {post['text']}"


def build_post_batches(
    posts: Sequence[Dict[str, Any]], prompt_prefix: str, token_budget: int
) -> List[List[Dict[str, Any]]]:
    """Beiträge reihenfolgetreu auf Prompts unterhalb des Eingabebudgets verteilen."""
    if token_budget <= estimate_tokens(prompt_prefix):
        raise ValueError("Klassifikationsbudget reicht nicht für Anweisung und Checkliste")

    fragments: List[Dict[str, Any]] = []
    for original in posts:
        post = dict(original)
        if estimate_tokens(f"{prompt_prefix}{_render_post(post)}") <= token_budget:
            fragments.append(post)
            continue
        empty = dict(post, text="")
        available = (token_budget - estimate_tokens(f"{prompt_prefix}{_render_post(empty)}") - 1) * 3
        if available <= 0:
            raise ValueError("Klassifikationsbudget reicht nicht für Beitragsmetadaten")
        text = str(post.get("text") or "")
        for offset in range(0, len(text), available):
            fragments.append(dict(post, text=text[offset:offset + available]))

    if not fragments:
        return [[]]
    batches: List[List[Dict[str, Any]]] = []
    current: List[Dict[str, Any]] = []
    for post in fragments:
        candidate = current + [post]
        compact = "\n".join(_render_post(item) for item in candidate)
        if current and estimate_tokens(prompt_prefix + compact) > token_budget:
            batches.append(current)
            current = [post]
        else:
            current = candidate
        if estimate_tokens(prompt_prefix + "\n".join(_render_post(item) for item in current)) > token_budget:
            raise ValueError("Ein Beitrag überschreitet trotz Aufteilung das Klassifikationsbudget")
    batches.append(current)
    return batches


def _runner_status(state: Any) -> str:
    value = getattr(state, "runner_status", state)
    return str(getattr(value, "value", value)).lower()


class EnsembleService:
    """Persistenter Orchestrator; alle OASIS-Läufe teilen sich eine GPU-Sperre."""

    _gpu_lock = threading.Lock()
    _threads: Dict[str, threading.Thread] = {}
    _threads_lock = threading.Lock()

    def __init__(
        self,
        runner_cls: Any = None,
        llm_factory: Optional[Callable[[], Any]] = None,
        root: Optional[Path] = None,
        poll_interval: float = 1.0,
    ):
        self.runner_cls = runner_cls
        self.llm_factory = llm_factory
        self.root = Path(root or Path(Config.UPLOAD_FOLDER) / "ensembles")
        self.poll_interval = poll_interval
        self._io_lock = threading.RLock()
        self.root.mkdir(parents=True, exist_ok=True)

    def _runner(self):
        if self.runner_cls is None:
            from .simulation_runner import SimulationRunner

            self.runner_cls = SimulationRunner
        return self.runner_cls

    def _llm(self):
        if self.llm_factory is not None:
            return self.llm_factory()
        from ..utils.llm_client import LLMClient

        return LLMClient()

    def _path(self, ensemble_id: str) -> Path:
        suffix = ensemble_id[4:] if ensemble_id.startswith("ens_") else ""
        if len(suffix) != 12 or any(c not in "0123456789abcdef" for c in suffix):
            raise ValueError("Ungültige ensemble_id")
        return self.root / ensemble_id

    def _load(self, ensemble_id: str) -> Optional[Dict[str, Any]]:
        path = self._path(ensemble_id) / "ensemble.json"
        with self._io_lock:
            return _read_json(path) if path.is_file() else None

    def _save(self, state: Dict[str, Any]) -> None:
        # Ein gleichzeitig eintreffender Abbruch darf nicht durch einen
        # Fortschritts-Speichervorgang mit einem älteren False überschrieben werden.
        existing_path = self._path(state["ensemble_id"]) / "ensemble.json"
        with self._io_lock:
            if existing_path.is_file() and _read_json(existing_path).get("cancel_requested"):
                state["cancel_requested"] = True
            state["updated_at"] = datetime.now().isoformat()
            _write_json_atomic(existing_path, state)

    def start(
        self,
        simulation_id: str,
        runs: int,
        hours: int,
        variants: Any,
        start_hour: int = 7,
    ) -> Dict[str, Any]:
        if not isinstance(simulation_id, str) or not simulation_id.startswith("sim_"):
            raise ValueError("simulation_id muss mit sim_ beginnen")
        if isinstance(runs, bool) or not isinstance(runs, int) or not 1 <= runs <= 100:
            raise ValueError("runs muss zwischen 1 und 100 liegen")
        if isinstance(hours, bool) or not isinstance(hours, int) or not 1 <= hours <= 168:
            raise ValueError("hours muss zwischen 1 und 168 liegen")
        if (
            isinstance(start_hour, bool)
            or not isinstance(start_hour, int)
            or not 0 <= start_hour <= 23
        ):
            raise ValueError("start_hour muss zwischen 0 und 23 liegen")
        variants = validate_variants(variants)
        source = Path(Config.UPLOAD_FOLDER) / "simulations" / simulation_id
        required = ("simulation_config.json", "reddit_profiles.json", "twitter_profiles.csv", "state.json")
        missing = [name for name in required if not (source / name).is_file()]
        if missing:
            raise FileNotFoundError("Simulation ist nicht vorbereitet; fehlt: " + ", ".join(missing))
        config = _read_json(source / "simulation_config.json")
        available_types = {
            str(a.get("entity_type") or "").casefold()
            for a in config.get("agent_configs") or []
        }
        for key in variants:
            if key.startswith("without:"):
                selected_type = key.split(":", 1)[1]
                if selected_type.casefold() not in available_types:
                    raise ValueError(f"Akteurstyp nicht vorhanden: {selected_type}")
                remaining = [
                    agent for agent in config.get("agent_configs") or []
                    if str(agent.get("entity_type") or "").casefold() != selected_type.casefold()
                ]
                if not remaining:
                    raise ValueError(f"Variante {key} würde alle Agenten entfernen")

        context = load_simulation_context(simulation_id)
        question = str(
            config.get("simulation_requirement")
            or context["state"].get("simulation_requirement")
            or ""
        )
        ensemble_id = f"ens_{uuid.uuid4().hex[:12]}"
        estimate = self.estimate_seconds(runs, hours, variants, config)
        now = datetime.now().isoformat()
        state = {
            "ensemble_id": ensemble_id,
            "simulation_id": simulation_id,
            "question": question,
            "status": "queued",
            "created_at": now,
            "finished_at": None,
            "runs": runs,
            "hours": hours,
            "start_hour": start_hour,
            "variants": [
                {
                    "key": key,
                    "label_de": _variant_label(key)[0],
                    "label_en": _variant_label(key)[1],
                    "status": "queued",
                    "done": 0,
                    "total": runs,
                }
                for key in variants
            ],
            "checklist": [],
            "results": {},
            "comparisons": [],
            "current": None,
            "eta_seconds": estimate,
            "error": None,
            "base_seed": random.SystemRandom().randint(0, 2**31 - runs - 1),
            "cancel_requested": False,
            "current_runner_id": None,
        }
        self._path(ensemble_id).mkdir(parents=True, exist_ok=False)
        self._save(state)
        thread = threading.Thread(target=self._run_ensemble, args=(ensemble_id,), daemon=True)
        with self._threads_lock:
            self._threads[ensemble_id] = thread
        thread.start()
        return {"ensemble_id": ensemble_id, "estimate_seconds": estimate}

    def get(self, ensemble_id: str) -> Optional[Dict[str, Any]]:
        state = self._load(ensemble_id)
        if state:
            state = dict(state)
            state.pop("cancel_requested", None)
            state.pop("current_runner_id", None)
            state.pop("base_seed", None)
            state.pop("updated_at", None)
        return state

    def reclassify(self, ensemble_id: str) -> Dict[str, Any]:
        """Vorhandene DBs/Erzählungen erneut auswerten, ohne Simulationen zu starten."""
        state = self._load(ensemble_id)
        if not state:
            raise FileNotFoundError(ensemble_id)
        if state.get("status") in {"queued", "running"}:
            raise RuntimeError("Ensemble wird bereits verarbeitet")
        if not state.get("checklist") or not state.get("results"):
            raise RuntimeError("Ensemble besitzt keine abgeschlossene Klassifikation")
        for variant in state["variants"]:
            for run_number in range(1, int(state["runs"]) + 1):
                run_dir = self._path(ensemble_id) / variant["key"] / f"run_{run_number}"
                if not run_dir.is_dir():
                    raise FileNotFoundError(f"Gespeicherter Lauf fehlt: {run_dir}")

        state["results_v1"] = json.loads(json.dumps(state["results"], ensure_ascii=False))
        state["comparisons_v1"] = json.loads(
            json.dumps(state.get("comparisons", []), ensure_ascii=False)
        )
        for item in state["checklist"]:
            item["polarity"] = item.get("polarity") or infer_polarity(
                f"{item.get('text_de', '')} {item.get('definition', '')}"
            )
        state["status"] = "queued"
        state["error"] = None
        state["finished_at"] = None
        state["cancel_requested"] = False
        state["current"] = None
        state["current_runner_id"] = None
        state["eta_seconds"] = None
        for variant in state["variants"]:
            variant["status"] = "queued"
            variant["done"] = 0
        self._save(state)

        thread = threading.Thread(
            target=self._run_reclassification, args=(ensemble_id,), daemon=True
        )
        with self._threads_lock:
            self._threads[ensemble_id] = thread
        thread.start()
        return {"ensemble_id": ensemble_id, "status": "queued"}

    def list(self, simulation_id: Optional[str] = None) -> List[Dict[str, Any]]:
        result = []
        for path in self.root.glob("ens_*/ensemble.json"):
            state = _read_json(path)
            if not state or (simulation_id and state.get("simulation_id") != simulation_id):
                continue
            public = self.get(str(state["ensemble_id"])) or {}
            public.pop("results", None)
            result.append(public)
        return sorted(result, key=lambda item: item.get("created_at", ""), reverse=True)

    def cancel(self, ensemble_id: str) -> None:
        state = self._load(ensemble_id)
        if not state:
            raise FileNotFoundError(ensemble_id)
        if state["status"] in {"completed", "failed", "cancelled"}:
            return
        state["cancel_requested"] = True
        runner_id = state.get("current_runner_id")
        self._save(state)
        if runner_id:
            try:
                self._runner().stop_simulation(runner_id)
            except Exception as error:
                logger.warning(f"Ensemble-Lauf {runner_id} konnte nicht gestoppt werden: {error}")

    def delete(self, ensemble_id: str) -> None:
        state = self._load(ensemble_id)
        if not state:
            raise FileNotFoundError(ensemble_id)
        if state["status"] in {"queued", "running"}:
            raise RuntimeError("Laufendes Ensemble kann nicht gelöscht werden")
        shutil.rmtree(self._path(ensemble_id))

    def mark_stale_runs(self) -> int:
        count = 0
        for path in self.root.glob("ens_*/ensemble.json"):
            state = _read_json(path)
            if state.get("status") not in {"queued", "running"}:
                continue
            state["status"] = "failed"
            state["error"] = "Backend wurde neu gestartet, Ensemble abgebrochen"
            state["finished_at"] = datetime.now().isoformat()
            state["current"] = None
            self._save(state)
            count += 1
        return count

    def estimate_seconds(
        self, runs: int, hours: int, variants: Sequence[str], config: Dict[str, Any]
    ) -> int:
        samples = []
        roots = [Path(Config.UPLOAD_FOLDER) / "simulations", self.root]
        for root in roots:
            if not root.exists():
                continue
            for path in root.rglob("run_state.json"):
                data = _read_json(path)
                try:
                    start = datetime.fromisoformat(data["started_at"])
                    end = datetime.fromisoformat(data["completed_at"])
                    rounds = int(data.get("total_rounds") or 0)
                    if rounds > 0 and end > start:
                        samples.append((end - start).total_seconds() / rounds)
                except (KeyError, TypeError, ValueError):
                    continue
        seconds_per_round = sum(samples) / len(samples) if samples else 40.0
        minutes = int((config.get("time_config") or {}).get("minutes_per_round") or 60)
        rounds = max(1, hours * 60 // max(minutes, 1))
        simulation_variants = sum(1 for key in variants if key != "null_model")
        null_runs = runs if "null_model" in variants else 0
        return max(1, math.ceil(seconds_per_round * (rounds * runs * simulation_variants + null_runs)))

    def _create_checklist(self, state: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        material = context["extracted_text"]
        initial = (context["config"].get("event_config") or {}).get("initial_posts") or []
        comparison_material = "\n".join([
            material,
            *(
                str(post.get("content") or "")
                for post in initial
                if isinstance(post, dict)
            ),
        ])
        llm = self._llm()
        prompt = (
            "Erzeuge 5 bis 8 konkrete, beobachtbare Ja/Nein-Ergebnisse für die Frage. "
            f"Jedes Ergebnis muss innerhalb der simulierten {state['hours']} Stunden beobachtbar "
            "sein und mit ‚Im simulierten Zeitraum …‘ beginnen. Formuliere allgemein mit "
            "Akteursgruppen statt Eigennamen. Übernimm KEINE Zahlen, Schwellen, Namen oder "
            "bereits beschriebenen bzw. angekündigten Ereignisse aus dem Eingabematerial. "
            "Mische mindestens zwei Eskalationen, mindestens zwei Deeskalationen oder "
            "Kompromisse und genau ein Ergebnis ‚keine nennenswerte Reaktion‘. Keine bloßen "
            "Meinungen oder vagen Tendenzen. Setze polarity auf presence, wenn das Ereignis "
            "eintreten muss, und auf absence, wenn sein Ausbleiben das Ergebnis ist. Gib bei "
            "absence zusätzlich in presence_event das konkrete positive Gegenereignis an, nach "
            "dem später gesucht werden soll. Antworte als JSON "
            "{\"outcomes\":[{\"text_de\":...,\"definition\":...,"
            "\"polarity\":\"presence|absence\",\"presence_event\":...}]}.\n\n"
            f"Frage: {state['question']}\nSimulierter Zeitraum: {state['hours']} Stunden\n"
            f"Eingabematerial:\n{material}"
        )
        checklist: List[Dict[str, Any]] = []
        for attempt in range(2):
            retry = (
                "\n\nDer vorherige Entwurf enthielt Zahlen aus dem Material und wurde "
                "verworfen. Erzeuge die vollständige Checkliste neu."
                if attempt else ""
            )
            payload = llm.chat_json(
                [{"role": "system", "content": "Du definierst prüfbare Ergebnisvariablen."},
                 {"role": "user", "content": prompt + retry}],
                temperature=0,
                max_tokens=2000,
                max_attempts=1,
                seed=state["base_seed"],
            )
            generated = parse_checklist(payload)
            checklist = filter_checklist_material_numbers(generated, comparison_material)
            if len(checklist) == len(generated):
                break
        if len(checklist) != len(generated):
            raise ValueError(
                "Checkliste enthält nach zwei Versuchen Zahlen aus dem Material"
            )

        quote_checks = []
        for item in checklist:
            event = f"{item['text_de']} -- {item['definition']}"
            quote_checks.append(llm.chat_json(
                [
                    {"role": "system", "content": "Prüfe streng gegen das Eingabematerial."},
                    {"role": "user", "content": (
                        "Wird dieses Ereignis im Material bereits als geschehen oder angekündigt "
                        "beschrieben? Antworte JSON {\"in_material\":true|false,"
                        "\"zitat\":\"wörtliche Textstelle oder leer\"}.\n\n"
                        f"Ereignis:\n{event}\n\nMaterial:\n{comparison_material}"
                    )},
                ],
                temperature=0,
                max_tokens=500,
                max_attempts=2,
                seed=state["base_seed"],
            ))
        return mark_checklist_material(checklist, material, initial, quote_checks)

    def _null_narrative(self, state: Dict[str, Any], context: Dict[str, Any], seed: int) -> str:
        return self._llm().chat(
            [
                {"role": "system", "content": "Schreibe eine plausible Verlaufserzählung, keine Analyse der Simulation."},
                {"role": "user", "content": (
                    f"Eingabematerial:\n{context['extracted_text']}\n\n"
                    f"Frage: {state['question']}\nZeitraum: {state['hours']} Stunden. "
                    "Erzähle einen möglichen Verlauf innerhalb dieses Zeitraums."
                )},
            ],
            temperature=0.7,
            max_tokens=4000,
            seed=seed,
        )

    def _classify_posts(
        self,
        state: Dict[str, Any],
        posts: Sequence[Dict[str, Any]],
        seed: int,
        run_number: int,
        run_dir: Optional[Path] = None,
    ) -> Dict[str, Dict[str, Any]]:
        checklist_items = [
            dict(item, polarity=item.get("polarity") or infer_polarity(
                f"{item.get('text_de', '')} {item.get('definition', '')}"
            ))
            for item in state["checklist"]
        ]
        checklist = "\n".join(
            f"{item['id']}: {_positive_event_text(item) if item['polarity'] == 'absence' else (str(item.get('text_de', '')) + ' -- ' + str(item.get('definition', '')))}"
            for item in checklist_items
        )
        instruction = (
            "Für jedes aufgeführte positive Ereignis: yes=true nur bei einem eindeutigen Beleg. "
            "Nenne ausschließlich vorhandene IDs und liefere genau eine Zeile je outcome_id. "
            "JSON: {\"results\":[{\"outcome_id\":\"o1\",\"yes\":true,"
            "\"post_ids\":[\"twitter:1\"]}]}.\n\n"
            f"Zu prüfende positive Ereignisse:\n{checklist}\n\nBeiträge:\n"
        )
        system = "Klassifiziere streng nur anhand der gelieferten Beiträge."
        output_tokens = 3000
        configured_budget = int(os.environ.get(
            "ENSEMBLE_CLASSIFICATION_TOKEN_BUDGET",
            str(Config.ENSEMBLE_CLASSIFICATION_TOKEN_BUDGET),
        ))
        context = int(os.environ.get("LOCAL_LLM_CONTEXT", str(Config.LOCAL_LLM_CONTEXT)))
        token_budget = min(configured_budget, context - output_tokens - 256)
        prefix = f"{system}\n{instruction}"
        batches = build_post_batches(posts, prefix, token_budget)
        llm = self._llm()
        audits: List[Dict[str, Any]] = []
        batch_results: List[Dict[str, Dict[str, Any]]] = []
        for index, batch in enumerate(batches, 1):
            compact = "\n".join(_render_post(post) for post in batch)
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": instruction + compact},
            ]
            audit: Dict[str, Any] = {
                "batch": index,
                "post_count": len({str(post.get('post_id')) for post in batch}),
                "estimated_input_tokens": estimate_tokens(messages),
            }
            try:
                if hasattr(llm, "last_raw_response"):
                    llm.last_raw_response = None
                payload = llm.chat_json(
                    messages,
                    temperature=0,
                    max_tokens=output_tokens,
                    max_attempts=2,
                    seed=seed,
                )
                verified = verify_classification_evidence(
                    payload, batch, checklist_items, run_number
                )
                audit["raw_response"] = getattr(llm, "last_raw_response", None) or payload
                audit["parsed_response"] = payload
                audit["verified"] = verified
            except Exception as error:
                verified = {
                    str(item["id"]): {"yes": False, "evidence": [], "unclassified": True}
                    for item in checklist_items
                }
                audit["raw_response"] = getattr(llm, "last_raw_response", None)
                audit["error"] = str(error)
                audit["verified"] = verified
            audits.append(audit)
            batch_results.append(verified)

        combined: Dict[str, Dict[str, Any]] = {}
        for item in checklist_items:
            oid = str(item["id"])
            values = [result[oid] for result in batch_results]
            if any(value.get("unclassified") for value in values):
                combined[oid] = {"yes": False, "evidence": [], "unclassified": True}
                continue
            positive_evidence: List[Dict[str, Any]] = []
            seen_evidence = set()
            for value in values:
                for evidence in value.get("evidence", []):
                    evidence_key = (evidence.get("platform"), evidence.get("post_id"))
                    if evidence_key in seen_evidence:
                        continue
                    seen_evidence.add(evidence_key)
                    positive_evidence.append(evidence)
                    if len(positive_evidence) == 5:
                        break
                if len(positive_evidence) == 5:
                    break
            positive_found = bool(positive_evidence)
            if item["polarity"] == "absence":
                yes = not positive_found
                evidence = ([{
                    "run": run_number,
                    "platform": "classification",
                    "post_id": f"absence:{run_number}:{oid}",
                    "agent": "Klassifikator",
                    "text": f"kein passender Beitrag in {len(posts)} geprüften Beiträgen",
                }] if yes else [])
            else:
                yes = positive_found
                evidence = positive_evidence
            combined[oid] = {"yes": yes, "evidence": evidence}

        audit_document = {
            "run": run_number,
            "post_count": len(posts),
            "token_budget": token_budget,
            "batches": audits,
            "result": combined,
        }
        if run_dir is not None:
            _write_json_atomic(Path(run_dir) / "classification.json", audit_document)
        return combined

    def _classify_narrative(
        self,
        state: Dict[str, Any],
        narrative: str,
        seed: int,
        run_number: int,
        run_dir: Optional[Path] = None,
    ) -> Dict[str, Dict[str, Any]]:
        checklist = "\n".join(
            f"{o['id']}: {_positive_event_text(o) if (o.get('polarity') or infer_polarity(str(o))) == 'absence' else (str(o.get('text_de', '')) + ' -- ' + str(o.get('definition', '')))}"
            for o in state["checklist"]
        )
        try:
            payload = self._llm().chat_json(
                [
                    {"role": "system", "content": "Klassifiziere streng nur anhand der Erzählung."},
                    {"role": "user", "content": (
                        "Prüfe die aufgeführten positiven Ereignisse. JSON: {\"results\":[{"
                        "\"outcome_id\":\"o1\",\"yes\":true,\"snippet\":\"wörtliche kurze "
                        "Textstelle\"}]}. Ja erfordert eine echte Textstelle.\n\n"
                        f"Ereignisse:\n{checklist}\n\nErzählung:\n{narrative}"
                    )},
                ],
                temperature=0,
                max_tokens=3000,
                max_attempts=2,
                seed=seed,
            )
            parse_error = None
        except Exception as error:
            payload = {}
            parse_error = str(error)
        rows = payload.get("results", []) if isinstance(payload, dict) else []
        by_id = {str(r.get("outcome_id")): r for r in rows if isinstance(r, dict)}
        result = {}
        for outcome in state["checklist"]:
            raw = by_id.get(outcome["id"])
            if parse_error or not isinstance(raw, dict):
                result[outcome["id"]] = {"yes": False, "evidence": [], "unclassified": True}
                continue
            answer = raw.get("yes", False)
            snippet = " ".join(str(raw.get("snippet") or "").split())
            valid = bool(snippet and snippet.casefold() in " ".join(narrative.split()).casefold())
            positive_found = bool(answer is True and valid)
            absence = (outcome.get("polarity") or infer_polarity(
                f"{outcome.get('text_de', '')} {outcome.get('definition', '')}"
            )) == "absence"
            yes = not positive_found if absence else positive_found
            result[outcome["id"]] = {
                "yes": yes,
                "evidence": ([{
                    "run": run_number,
                    "platform": "null_model",
                    "post_id": f"null:{run_number}",
                    "agent": "Hauptmodell",
                    "text": ("kein passendes Ereignis in der geprüften Erzählung" if absence else snippet),
                }] if yes else []),
            }
        if run_dir is not None:
            _write_json_atomic(Path(run_dir) / "classification.json", {
                "run": run_number,
                "post_count": 1,
                "batches": [{
                    "batch": 1,
                    "raw_response": payload if not parse_error else None,
                    "error": parse_error,
                    "verified": result,
                }],
                "result": result,
            })
        return result

    def _aggregate(self, state: Dict[str, Any], per_run: Dict[str, List[Dict[str, Any]]]) -> None:
        results = {}
        for variant in state["variants"]:
            key = variant["key"]
            results[key] = {}
            runs = per_run.get(key, [])
            for outcome in state["checklist"]:
                oid = outcome["id"]
                unclassified = sum(
                    1 for row in runs if row.get(oid, {}).get("unclassified")
                )
                classified_runs = [
                    row for row in runs if not row.get(oid, {}).get("unclassified")
                ]
                yes = sum(1 for row in classified_runs if row.get(oid, {}).get("yes"))
                n = len(classified_runs)
                low, high = wilson_interval(yes, n)
                evidence = [
                    item
                    for row in classified_runs
                    for item in row.get(oid, {}).get("evidence", [])
                ][:5]
                results[key][oid] = {
                    "yes": yes,
                    "n": n,
                    "unclassified": unclassified,
                    "rate": _round(yes / n if n else 0.0),
                    "ci_low": _round(low),
                    "ci_high": _round(high),
                    "evidence": evidence,
                }
        state["results"] = results
        comparisons = []
        baseline = results.get("baseline", {})
        for variant in state["variants"]:
            key = variant["key"]
            if key == "baseline":
                continue
            for outcome in state["checklist"]:
                oid = outcome["id"]
                value, base = results[key][oid], baseline[oid]
                low, high = newcombe_difference_interval(
                    value["yes"], value["n"], base["yes"], base["n"]
                )
                comparisons.append({
                    "variant": key,
                    "outcome_id": oid,
                    "diff": _round(value["rate"] - base["rate"]),
                    "ci_low": _round(low),
                    "ci_high": _round(high),
                })
        state["comparisons"] = comparisons

    def _cancelled(self, state: Dict[str, Any]) -> bool:
        fresh = self._load(state["ensemble_id"])
        if fresh and fresh.get("cancel_requested"):
            state["cancel_requested"] = True
        return bool(state.get("cancel_requested"))

    def _run_reclassification(self, ensemble_id: str) -> None:
        state = self._load(ensemble_id)
        if not state:
            return
        try:
            with self._gpu_lock:
                state = self._load(ensemble_id) or state
                if self._cancelled(state):
                    raise InterruptedError
                state["status"] = "running"
                self._save(state)
                per_run: Dict[str, List[Dict[str, Any]]] = {}
                for variant in state["variants"]:
                    key = variant["key"]
                    variant["status"] = "running"
                    per_run[key] = []
                    self._save(state)
                    for run_number in range(1, int(state["runs"]) + 1):
                        if self._cancelled(state):
                            raise InterruptedError
                        seed = int(state["base_seed"]) + run_number
                        run_dir = self._path(ensemble_id) / key / f"run_{run_number}"
                        state["current"] = {"variant": key, "run": run_number, "round": 0}
                        self._save(state)
                        if key == "null_model":
                            narrative_path = run_dir / "narrative.txt"
                            if not narrative_path.is_file():
                                raise FileNotFoundError(f"Gespeicherte Erzählung fehlt: {narrative_path}")
                            classified = self._classify_narrative(
                                state,
                                narrative_path.read_text(encoding="utf-8"),
                                seed,
                                run_number,
                                run_dir,
                            )
                        else:
                            config = _read_json(run_dir / "simulation_config.json")
                            initial = (config.get("event_config") or {}).get("initial_posts") or []
                            posts = load_simulation_posts(run_dir, initial)
                            classified = self._classify_posts(
                                state, posts, seed, run_number, run_dir
                            )
                        per_run[key].append(classified)
                        variant["done"] = run_number
                        self._save(state)
                    variant["status"] = "completed"
                    self._save(state)

                self._aggregate(state, per_run)
                state["status"] = "completed"
                state["finished_at"] = datetime.now().isoformat()
                state["current"] = None
                state["eta_seconds"] = 0
                self._save(state)
        except InterruptedError:
            state = self._load(ensemble_id) or state
            state["status"] = "cancelled"
            state["finished_at"] = datetime.now().isoformat()
            state["current"] = None
            for variant in state["variants"]:
                if variant["status"] in {"queued", "running"}:
                    variant["status"] = "cancelled"
            self._save(state)
        except Exception as error:
            logger.exception(f"Neuklassifikation {ensemble_id} fehlgeschlagen")
            state = self._load(ensemble_id) or state
            state["status"] = "failed"
            state["error"] = str(error)
            state["finished_at"] = datetime.now().isoformat()
            state["current"] = None
            for variant in state["variants"]:
                if variant["status"] == "running":
                    variant["status"] = "failed"
            self._save(state)
        finally:
            with self._threads_lock:
                self._threads.pop(ensemble_id, None)

    def _run_ensemble(self, ensemble_id: str) -> None:
        state = self._load(ensemble_id)
        if not state:
            return
        try:
            with self._gpu_lock:
                state = self._load(ensemble_id) or state
                if self._cancelled(state):
                    raise InterruptedError
                state["status"] = "running"
                self._save(state)
                context = load_simulation_context(state["simulation_id"])
                state["checklist"] = self._create_checklist(state, context)
                self._save(state)
                source = Path(context["sim_dir"])
                per_run: Dict[str, List[Dict[str, Any]]] = {}

                for variant in state["variants"]:
                    key = variant["key"]
                    variant["status"] = "running"
                    per_run[key] = []
                    self._save(state)
                    for run_number in range(1, state["runs"] + 1):
                        if self._cancelled(state):
                            raise InterruptedError
                        seed = state["base_seed"] + run_number
                        run_dir = self._path(ensemble_id) / key / f"run_{run_number}"
                        state["current"] = {"variant": key, "run": run_number, "round": 0}
                        self._save(state)
                        if key == "null_model":
                            run_dir.mkdir(parents=True, exist_ok=False)
                            narrative = self._null_narrative(state, context, seed)
                            (run_dir / "narrative.txt").write_text(narrative, encoding="utf-8")
                            classified = self._classify_narrative(
                                state, narrative, seed, run_number, run_dir
                            )
                        else:
                            config = prepare_run_directory(
                                source,
                                run_dir,
                                key,
                                state["hours"],
                                state.get("start_hour", 7),
                            )
                            runner_id = f"{ensemble_id}_{key.replace(':', '_')}_{run_number}"
                            state["current_runner_id"] = runner_id
                            self._save(state)
                            runner_state = self._runner().start_simulation(
                                simulation_id=runner_id,
                                platform="parallel",
                                seed=seed,
                                simulation_dir=str(run_dir),
                                keep_alive=False,
                            )
                            while _runner_status(runner_state) not in TERMINAL_RUNNER_STATES:
                                if self._cancelled(state):
                                    try:
                                        self._runner().stop_simulation(runner_id)
                                    finally:
                                        raise InterruptedError
                                state["current"]["round"] = int(
                                    getattr(runner_state, "current_round", 0) or 0
                                )
                                self._save(state)
                                time.sleep(self.poll_interval)
                                runner_state = self._runner().get_run_state(runner_id)
                            if _runner_status(runner_state) != "completed":
                                raise RuntimeError(
                                    getattr(runner_state, "error", None)
                                    or f"Simulationslauf endete mit {_runner_status(runner_state)}"
                                )
                            initial = (config.get("event_config") or {}).get("initial_posts") or []
                            posts = load_simulation_posts(run_dir, initial)
                            classified = self._classify_posts(
                                state, posts, seed, run_number, run_dir
                            )
                        per_run[key].append(classified)
                        variant["done"] = run_number
                        state["current_runner_id"] = None
                        remaining = sum(v["total"] - v["done"] for v in state["variants"])
                        state["eta_seconds"] = max(0, round(state["eta_seconds"] * remaining / max(1, remaining + 1)))
                        self._save(state)
                    variant["status"] = "completed"
                    self._save(state)

                self._aggregate(state, per_run)
                state["status"] = "completed"
                state["finished_at"] = datetime.now().isoformat()
                state["current"] = None
                state["eta_seconds"] = 0
                self._save(state)
        except InterruptedError:
            state = self._load(ensemble_id) or state
            state["status"] = "cancelled"
            state["finished_at"] = datetime.now().isoformat()
            state["current"] = None
            state["eta_seconds"] = None
            for variant in state["variants"]:
                if variant["status"] in {"queued", "running"}:
                    variant["status"] = "cancelled"
            self._save(state)
        except Exception as error:
            logger.exception(f"Ensemble {ensemble_id} fehlgeschlagen")
            state = self._load(ensemble_id) or state
            state["status"] = "failed"
            state["error"] = str(error)
            state["finished_at"] = datetime.now().isoformat()
            state["current"] = None
            state["eta_seconds"] = None
            for variant in state["variants"]:
                if variant["status"] == "running":
                    variant["status"] = "failed"
            self._save(state)
        finally:
            with self._threads_lock:
                self._threads.pop(ensemble_id, None)


def ensemble_markdown(state: Dict[str, Any]) -> str:
    """Fertiges Ensemble deterministisch als Berichtsteil formatieren."""
    if state.get("status") != "completed":
        raise ValueError("Mehrfachlauf ist noch nicht abgeschlossen")
    labels = {item["key"]: item["label_de"] for item in state["variants"]}
    outcomes = {item["id"]: item for item in state["checklist"]}
    lines = [
        "## Mehrfachlauf",
        "",
        f"Ausgewertet wurden {state['runs']} Läufe je Variante über jeweils {state['hours']} Stunden.",
        "",
        "| Variante | Ergebnis | Ja / N | Unklassifiziert | Anteil (95-%-Wilson-Intervall) |",
        "|---|---|---:|---:|---:|",
    ]
    for variant in state["variants"]:
        key = variant["key"]
        for oid, value in state["results"].get(key, {}).items():
            outcome = outcomes.get(oid, {"text_de": oid})
            marker = " †" if outcome.get("in_material") else ""
            lines.append(
                f"| {labels[key]} | {outcome['text_de']}{marker} | {value['yes']} / {value['n']} | "
                f"{value.get('unclassified', 0)} | "
                f"{value['rate']:.1%} ({value['ci_low']:.1%}–{value['ci_high']:.1%}) |"
            )
    if state.get("comparisons"):
        lines.extend([
            "",
            "### Unterschiede gegenüber dem Basislauf",
            "",
            "| Variante | Ergebnis | Differenz (95-%-Newcombe-Intervall) |",
            "|---|---|---:|",
        ])
        for comparison in state["comparisons"]:
            outcome = outcomes.get(comparison["outcome_id"], {"text_de": comparison["outcome_id"]})
            lines.append(
                f"| {labels.get(comparison['variant'], comparison['variant'])} | {outcome['text_de']} | "
                f"{comparison['diff']:+.1%} ({comparison['ci_low']:+.1%} bis "
                f"{comparison['ci_high']:+.1%}) |"
            )
    material = [item for item in state["checklist"] if item.get("in_material")]
    if material:
        lines.extend([
            "",
            "† Diese Ergebnisse stehen inhaltlich bereits im Eingabematerial und sind daher keine unabhängige Prognose:",
        ])
        for item in material:
            lines.append(f"- {item['text_de']}: {item['material_snippet']}")
    if "null_model" in state.get("results", {}):
        lines.extend([
            "",
            "Das Nullmodell erzeugt ohne Agenteninteraktion eine einzelne Verlaufserzählung je Seed; "
            "Unterschiede zur Basis zeigen deshalb nicht allein einen kausalen Vernetzungseffekt.",
        ])
    lines.extend([
        "",
        "### Grenzen",
        "",
        "Die Intervalle quantifizieren Streuung zwischen diesen Modellläufen, nicht Unsicherheit über die reale Welt. "
        "Newcombe-Intervalle der Variantenunterschiede behandeln die Läufe als unabhängig. "
        "Gemeinsame Modellfehler, unvollständiges Material und Klassifikationsfehler bleiben bestehen.",
    ])
    return "\n".join(lines) + "\n"
