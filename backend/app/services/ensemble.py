"""Mehrfachläufe, Gegenproben und deterministische Ensemble-Auswertung (V3/V4)."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import random
import re
import shutil
import signal
import sqlite3
import threading
import time
import urllib.request
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
    "blind_feed": ("Blinder Feed", "Blind feed"),
    "null_model": ("Nullmodell", "Null model"),
    "null_document": ("Nullmodell Dokument", "Null model (document)"),
    "null_personas": ("Nullmodell Personas", "Null model (personas)"),
}
# Erster Versuch plus zwei Wiederholungen eines fehlgeschlagenen Stapels oder Seeds.
BATCH_ATTEMPTS = 3
MISSING_ID_FOLLOWUP_ROUNDS = 2
DEFAULT_OLLAMA_NUM_CTX = 4096
CLASSIFICATION_OUTPUT_TOKENS = 3000
CLASSIFICATION_CONTEXT_BUFFER = 256
CLASSIFICATION_FOLLOWUP_RESERVE = 150
SEED_ATTEMPTS = 3
NULL_DOCUMENT_ARMS = frozenset({"null_model", "null_document"})
NULL_PERSONA_ARMS = frozenset({"null_personas"})
NULL_ARMS = NULL_DOCUMENT_ARMS | NULL_PERSONA_ARMS

MAX_ENSEMBLE_HOURS = 336
MAX_CUSTOM_OUTCOMES = 20
ALLOWED_MINUTES_PER_ROUND = frozenset({60, 120, 240})
DEFAULT_MIN_FREE_BYTES = 5 * 1024**3
DEFAULT_MAX_AGENT_ERROR_RATE = 0.5
OLLAMA_WAIT_SECONDS = 30 * 60
ORPHAN_TERM_WAIT_SECONDS = 10.0
PROCESS_START_TIME = time.time()


class ModelServiceUnavailable(RuntimeError):
    """Temporärer Modell-Dienstausfall; darf kein Seed-Versuch sein."""


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


def exact_mcnemar_p(baseline_only: int, variant_only: int) -> float:
    """Zweiseitiger exakter McNemar über die diskordanten Paare.

    Doppelte untere Binomialwahrscheinlichkeit bei p = 1/2, bei 1 gekappt.
    0 gegen 5 → 0,0625; 1 gegen 6 → 0,125; 7 gegen 0 → 0,015625.
    """
    discordant = int(baseline_only) + int(variant_only)
    if discordant <= 0:
        return 1.0
    smaller = min(int(baseline_only), int(variant_only))
    tail = sum(math.comb(discordant, index) for index in range(smaller + 1))
    return min(1.0, 2.0 * tail / (2 ** discordant))


def paired_difference_interval(
    baseline_only: int,
    variant_only: int,
    n_pairs: int,
    z: float = Z_95,
) -> Tuple[float, float]:
    """Wald-Intervall der gepaarten Differenz (Variante − Basis) = (c − b) / n."""
    if n_pairs <= 0:
        return 0.0, 0.0
    difference = (variant_only - baseline_only) / n_pairs
    numerator = (baseline_only + variant_only) - (variant_only - baseline_only) ** 2 / n_pairs
    standard_error = math.sqrt(max(0.0, numerator)) / n_pairs
    lower = difference - z * standard_error
    upper = difference + z * standard_error
    return max(-1.0, lower), min(1.0, upper)


def holm_adjust(p_values: Sequence[float]) -> List[float]:
    """Holm-Adjustierung, monoton in der aufsteigend sortierten p-Reihenfolge."""
    count = len(p_values)
    if not count:
        return []
    adjusted = [1.0] * count
    order = sorted(range(count), key=lambda index: (float(p_values[index]), index))
    running = 0.0
    for rank, index in enumerate(order):
        corrected = min(1.0, (count - rank) * float(p_values[index]))
        running = max(running, corrected)
        adjusted[index] = running
    return adjusted


def _usable_pair_flag(row: Optional[Dict[str, Any]], outcome_id: str) -> Optional[bool]:
    if not isinstance(row, dict):
        return None
    judgment = row.get(outcome_id)
    if not isinstance(judgment, dict) or "yes" not in judgment:
        return None
    if judgment.get("unclassified") or judgment.get("disputed"):
        return None
    return bool(judgment.get("yes"))


def paired_outcome_table(
    baseline_runs: Sequence[Dict[str, Any]],
    variant_runs: Sequence[Dict[str, Any]],
    outcome_id: str,
) -> Dict[str, int]:
    """2×2-Tafel über denselben Laufindex. Unklassifizierte oder strittige Seiten bleiben ungepaart."""
    both_yes = baseline_only = variant_only = both_no = unpaired = 0
    for index in range(max(len(baseline_runs), len(variant_runs))):
        left = _usable_pair_flag(
            baseline_runs[index] if index < len(baseline_runs) else None, outcome_id
        )
        right = _usable_pair_flag(
            variant_runs[index] if index < len(variant_runs) else None, outcome_id
        )
        if left is None or right is None:
            unpaired += 1
            continue
        if left and right:
            both_yes += 1
        elif left:
            baseline_only += 1
        elif right:
            variant_only += 1
        else:
            both_no += 1
    return {
        "both_yes": both_yes,
        "baseline_only": baseline_only,
        "variant_only": variant_only,
        "both_no": both_no,
        "n_pairs": both_yes + baseline_only + variant_only + both_no,
        "unpaired": unpaired,
    }


def canonical_outcome_rows(checklist: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Absence-Gegenstücke mit counter_outcome_id in die Presence-Zeile falten."""
    by_id = {str(item.get("id")): item for item in checklist}
    folded: Dict[str, List[str]] = {}
    skip = set()
    for item in checklist:
        outcome_id = str(item.get("id"))
        counter = str(item.get("counter_outcome_id") or "")
        polarity = stored_polarity(item)
        if polarity != "absence" or counter not in by_id or counter == outcome_id:
            continue
        counter_item = by_id[counter]
        counter_polarity = stored_polarity(counter_item)
        if counter_polarity == "absence":
            continue
        folded.setdefault(counter, []).append(outcome_id)
        skip.add(outcome_id)
    rows = []
    for item in checklist:
        outcome_id = str(item.get("id"))
        if outcome_id in skip:
            continue
        rows.append({
            "outcome_id": outcome_id,
            "collapsed_outcome_ids": list(folded.get(outcome_id, [])),
        })
    return rows


def resolve_primary_outcome_id(
    checklist: Sequence[Dict[str, Any]], requested: Optional[str]
) -> str:
    """Gewählte ID, sonst das erste eigene Ergebnis, sonst das erste automatische."""
    ids = [str(item.get("id")) for item in checklist]
    if requested:
        if requested not in ids:
            raise ValueError(f"primary_outcome_id nicht in der Checkliste: {requested}")
        return requested
    for item in checklist:
        if item.get("source") == "user":
            return str(item["id"])
    if not ids:
        raise ValueError("Checkliste enthält kein Ergebnis")
    return ids[0]


def median_character_count(lengths: Sequence[int]) -> int:
    """Median; bei gerader Anzahl der gerundete Mittelwert der beiden mittleren Werte."""
    ordered = sorted(int(value) for value in lengths)
    if not ordered:
        return 0
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return int(round((ordered[middle - 1] + ordered[middle]) / 2))


def null_arm(key: str) -> Optional[str]:
    """null_model bleibt der Alias von null_document."""
    if key in NULL_DOCUMENT_ARMS:
        return "null_document"
    if key in NULL_PERSONA_ARMS:
        return "null_personas"
    return None


def execution_variant_keys(keys: Sequence[str]) -> List[str]:
    """null_personas liest die Basis-Transkripte und läuft deshalb nicht vor baseline."""
    ordered = [str(key) for key in keys]
    if "baseline" in ordered and "null_personas" in ordered:
        if ordered.index("null_personas") < ordered.index("baseline"):
            ordered.remove("null_personas")
            ordered.insert(ordered.index("baseline") + 1, "null_personas")
    return ordered


def _normalized_span(text: str) -> str:
    return " ".join(str(text or "").split()).casefold()


def span_in_text(span: str, text: str) -> bool:
    """Wörtliche Spanne nach Whitespace-Normalisierung, ohne Großschreibung."""
    normalized = _normalized_span(span)
    return bool(normalized) and normalized in _normalized_span(text)


def _round(value: float, digits: int = 4) -> float:
    return round(float(value), digits)


def cohens_kappa(pairs: Sequence[Tuple[bool, bool]]) -> Dict[str, Any]:
    """Prozentuale Übereinstimmung und Cohen-Kappa für zwei binäre Bewerter."""
    n = len(pairs)
    if not n:
        # Ohne Paar ist Kappa nicht definiert. 0,0 wäre ein echtes, schlechtes Kappa.
        return {"agreement": None, "kappa": None, "n_pairs": 0}
    agreed = sum(1 for left, right in pairs if left == right)
    agreement = agreed / n
    left_yes = sum(1 for left, _ in pairs if left) / n
    right_yes = sum(1 for _, right in pairs if right) / n
    expected = left_yes * right_yes + (1.0 - left_yes) * (1.0 - right_yes)
    if math.isclose(expected, 1.0):
        # Beide Reihen sind konstant. Der Zufall ist dann 1, Kappa ist nicht definiert.
        kappa = None
    else:
        kappa = _round((agreement - expected) / (1.0 - expected))
    return {"agreement": _round(agreement), "kappa": kappa, "n_pairs": n}


def reliability_label(kappa: Optional[float]) -> str:
    if not isinstance(kappa, (int, float)) or isinstance(kappa, bool):
        return "nicht messbar"
    if kappa >= 0.6:
        return "messbar"
    if kappa >= 0.4:
        return "unsicher"
    return "nicht messbar"


def combine_rater_results(
    rater_a: Dict[str, Dict[str, Any]],
    rater_b: Dict[str, Dict[str, Any]],
    checklist: Sequence[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """Konservatives Endurteil: Ja nur bei zwei belegten Ja; Dissens bleibt strittig."""
    combined: Dict[str, Dict[str, Any]] = {}
    for item in checklist:
        oid = str(item["id"])
        left = rater_a.get(oid, {"yes": False, "evidence": [], "unclassified": True})
        right = rater_b.get(oid, {"yes": False, "evidence": [], "unclassified": True})
        edges = _merge_mechanism_edges(left, right)
        if left.get("unclassified") or right.get("unclassified"):
            combined[oid] = {
                "yes": False,
                "evidence": [],
                "unclassified": True,
                "disputed": False,
                "raters": {"a": left, "b": right},
            }
        else:
            disputed = bool(left.get("yes")) != bool(right.get("yes"))
            yes = bool(left.get("yes") and right.get("yes"))
            evidence = []
            if yes:
                for rater, judgment in (("a", left), ("b", right)):
                    for raw in judgment.get("evidence", []):
                        evidence.append({**raw, "rater": rater})
            combined[oid] = {
                "yes": yes,
                "evidence": evidence,
                "unclassified": False,
                "disputed": disputed,
                "raters": {"a": left, "b": right},
            }
        if edges or "mechanism_edges" in left or "mechanism_edges" in right:
            combined[oid]["mechanism_edges"] = edges
    return combined


def _merge_mechanism_edges(
    left: Dict[str, Any], right: Dict[str, Any]
) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    seen = set()
    for judgment in (left, right):
        for edge in judgment.get("mechanism_edges") or []:
            if not isinstance(edge, dict):
                continue
            marker = (edge.get("platform"), edge.get("post_id"), edge.get("text"))
            if marker in seen:
                continue
            seen.add(marker)
            merged.append(edge)
    return merged


ABSENCE_RE = re.compile(r"\b(?:nicht|kein(?:e|en|er|es)?|bleibt\s+aus)\b", re.IGNORECASE)
INTERACTION_RE = re.compile(
    r"\b(?:Debatte|Diskussion|antwortet|reagiert\s+auf)\b|"
    r"\bzwischen\b.+\bund\b",
    re.IGNORECASE | re.DOTALL,
)


def infer_polarity(text: str) -> str:
    """Alte Hilfsfunktion. Die Wertung liest Polarität nur aus dem Feld polarity."""
    return "absence" if ABSENCE_RE.search(text or "") else "presence"


def stored_polarity(item: Any) -> str:
    """Polarität nur aus dem expliziten Feld. Ohne Feld bleibt es Anwesenheit."""
    raw = item.get("polarity") if isinstance(item, dict) else None
    polarity = str(raw or "").strip().lower()
    return polarity if polarity in {"presence", "absence"} else "presence"


def infer_kind(text: str) -> str:
    """Alte Checklisten mit eindeutigem Interaktionswortlaut migrieren."""
    return "interaction" if INTERACTION_RE.search(text or "") else "event"


def _positive_event_text(item: Dict[str, Any]) -> str:
    explicit = str(item.get("presence_event") or "").strip()
    if explicit:
        return explicit
    # Nur die Überschrift umformen: die Definition beschreibt bei Abwesenheits-Ergebnissen weiter das Ausbleiben
    # („ohne jegliche Berichterstattung“) und machte die Frage nach dem Gegenereignis widersprüchlich.
    text = str(item.get('text_de', '')).strip()
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

    result: List[Dict[str, Any]] = []
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
        polarity = stored_polarity(raw) if isinstance(raw, dict) else "presence"
        supplied_kind = str(raw.get("kind") or "").strip().lower() if isinstance(raw, dict) else ""
        kind = supplied_kind if supplied_kind in {"event", "interaction"} else infer_kind(
            f"{text} {definition}"
        )
        item: Dict[str, Any] = {
            "id": f"o{len(result) + 1}",
            "text_de": text,
            "definition": definition,
            "polarity": polarity,
            "kind": kind,
            "source": "auto",
        }
        if isinstance(raw, dict) and str(raw.get("presence_event") or "").strip():
            item["presence_event"] = str(raw["presence_event"]).strip()
        if isinstance(raw, dict) and str(raw.get("counter_outcome_id") or "").strip():
            item["counter_outcome_id"] = str(raw["counter_outcome_id"]).strip()
        result.append(item)
    if not 5 <= len(result) <= 8:
        raise ValueError("Das Modell muss 5 bis 8 eindeutige Ergebnisse liefern")
    ids = {str(item["id"]) for item in result}
    polarity_by_id = {str(item["id"]): item["polarity"] for item in result}
    for item in result:
        counter = str(item.get("counter_outcome_id") or "")
        if (
            item["polarity"] != "absence"
            or counter not in ids
            or counter == item["id"]
            or polarity_by_id.get(counter) != "presence"
        ):
            item.pop("counter_outcome_id", None)
    return result


def validate_custom_outcomes(payload: Any) -> List[Dict[str, Any]]:
    """Optionale benutzerdefinierte Ergebnisfragen streng normalisieren."""
    if payload is None:
        return []
    if not isinstance(payload, list):
        raise ValueError("custom_outcomes muss eine Liste sein")
    if len(payload) > MAX_CUSTOM_OUTCOMES:
        raise ValueError(
            f"custom_outcomes darf höchstens {MAX_CUSTOM_OUTCOMES} Einträge enthalten"
        )
    result = []
    for index, raw in enumerate(payload, 1):
        if not isinstance(raw, dict):
            raise ValueError(f"custom_outcomes[{index - 1}] muss ein Objekt sein")
        text = str(raw.get("text_de") or "").strip()
        if not text or len(text) > 200:
            raise ValueError(
                f"custom_outcomes[{index - 1}].text_de muss 1 bis 200 Zeichen lang sein"
            )
        polarity = str(raw.get("polarity") or "").strip().lower()
        kind = str(raw.get("kind") or "").strip().lower()
        if polarity and polarity not in {"presence", "absence"}:
            raise ValueError("polarity muss presence oder absence sein")
        if kind and kind not in {"event", "interaction"}:
            raise ValueError("kind muss event oder interaction sein")
        result.append({
            "id": f"c{index}",
            "text_de": text,
            "definition": text,
            "polarity": polarity or "presence",
            "kind": kind or infer_kind(text),
            "source": "user",
        })
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
    source_dir: Path,
    run_dir: Path,
    variant: str,
    hours: int,
    start_hour: int = 7,
    minutes_per_round: Optional[int] = 60,
    text_model: Optional[str] = None,
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
    # Ensemble-Override: LLM-Wert ersetzen, alle Arme identisch. None (Altstand): Config-Wert bleibt.
    if minutes_per_round is not None:
        time_config["minutes_per_round"] = minutes_per_round
    config["ensemble_variant"] = variant
    config["simulation_id"] = run_dir.name
    if text_model:
        config["llm_model"] = str(text_model)

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
            user_columns = _table_columns(connection, "user")
            if "user_id" in user_columns:
                agent_expr = "agent_id" if "agent_id" in user_columns else "user_id"
                name_expr = "name" if "name" in user_columns else "NULL"
                username_expr = "user_name" if "user_name" in user_columns else "NULL"
                for row in connection.execute(
                    f"SELECT user_id, {agent_expr} AS agent_id, {name_expr} AS name, "
                    f"{username_expr} AS user_name FROM user"
                ):
                    users[row["user_id"]] = {
                        "agent_id": _agent_id(row["agent_id"]),
                        "name": row["name"] or row["user_name"] or f"Agent {row['agent_id']}",
                    }
            link_columns = [
                name for name in (
                    "original_post_id", "quoted_post_id", "quote_post_id",
                    "reply_to_post_id", "in_reply_to_post_id", "parent_post_id",
                    "replied_post_id",
                ) if name in columns
            ]
            extra = "".join(f", {name}" for name in link_columns)
            query = (
                f"SELECT {id_column} AS post_id, user_id, content{extra} "
                f"FROM post ORDER BY {id_column}"
            )
            post_rows = list(connection.execute(query))
            post_authors = {
                row["post_id"]: users.get(row["user_id"], {}).get(
                    "agent_id", _agent_id(row["user_id"])
                )
                for row in post_rows
            }
            for row in post_rows:
                user = users.get(row["user_id"], {})
                agent_id = user.get("agent_id", _agent_id(row["user_id"]))
                text = " ".join(str(row["content"] or "").split())
                if (agent_id, text) in initial:
                    continue
                item = {
                    "platform": platform,
                    "post_id": f"{platform}:{row['post_id']}",
                    "agent_id": agent_id,
                    "agent": user.get("name") or f"Agent {row['user_id']}",
                    "text": text,
                }
                for link_column in link_columns:
                    target_post_id = row[link_column]
                    if target_post_id is not None and target_post_id in post_authors:
                        item["structural_link"] = {
                            "type": "reply" if "reply" in link_column or "parent" in link_column else "quote_or_repost",
                            "target_post_id": f"{platform}:{target_post_id}",
                            "target_agent_id": post_authors[target_post_id],
                        }
                        break
                result.append(item)

            comment_columns = _table_columns(connection, "comment")
            if {"user_id", "post_id"}.issubset(comment_columns):
                comment_id = "comment_id" if "comment_id" in comment_columns else "rowid"
                content_expr = "content" if "content" in comment_columns else "''"
                for row in connection.execute(
                    f"SELECT {comment_id} AS comment_id, user_id, post_id, "
                    f"{content_expr} AS content FROM comment ORDER BY {comment_id}"
                ):
                    target_agent_id = post_authors.get(row["post_id"])
                    if target_agent_id is None:
                        continue
                    user = users.get(row["user_id"], {})
                    result.append({
                        "platform": platform,
                        "post_id": f"{platform}:comment:{row['comment_id']}",
                        "agent_id": user.get("agent_id", _agent_id(row["user_id"])),
                        "agent": user.get("name") or f"Agent {row['user_id']}",
                        "text": " ".join(str(row["content"] or "").split()),
                        "structural_link": {
                            "type": "comment",
                            "target_post_id": f"{platform}:{row['post_id']}",
                            "target_agent_id": target_agent_id,
                        },
                    })
        finally:
            connection.close()
    return result


def baseline_transcript_lengths(ensemble_dir: Path) -> List[int]:
    """Zeichen der Basis-Beiträge je Lauf, Startbeiträge ausgenommen."""
    baseline = Path(ensemble_dir) / "baseline"
    if not baseline.is_dir():
        return []
    run_dirs = []
    for path in baseline.glob("run_*"):
        if _is_archived_failure(path):
            continue
        try:
            index = int(path.name.split("_", 1)[1])
        except (IndexError, ValueError):
            continue
        run_dirs.append((index, path))
    lengths = []
    for _, run_dir in sorted(run_dirs):
        config = _read_json(run_dir / "simulation_config.json")
        initial = (config.get("event_config") or {}).get("initial_posts") or []
        posts = load_simulation_posts(run_dir, initial)
        lengths.append(sum(len(str(post.get("text") or "")) for post in posts))
    return lengths


def structural_interaction_evidence(
    posts: Sequence[Dict[str, Any]],
    side_a_agent_ids: Sequence[Any],
    side_b_agent_ids: Sequence[Any],
    run_number: int,
) -> List[Dict[str, Any]]:
    """Direkte DB-Verbindungen zwischen den zwei modellseitig bestimmten Gruppen."""
    side_a = {_agent_id(value) for value in side_a_agent_ids}
    side_b = {_agent_id(value) for value in side_b_agent_ids}
    side_a.discard(None)
    side_b.discard(None)
    evidence = []
    for post in posts:
        link = post.get("structural_link")
        if not isinstance(link, dict):
            continue
        source = _agent_id(post.get("agent_id"))
        target = _agent_id(link.get("target_agent_id"))
        if not ((source in side_a and target in side_b) or (source in side_b and target in side_a)):
            continue
        evidence.append({
            "run": run_number,
            **post,
            "text": (
                f"Struktureller Beleg ({link.get('type')}): {post.get('agent')} "
                f"verknüpft auf {link.get('target_post_id')}"
            ),
        })
        if len(evidence) == 5:
            break
    return evidence


def _merge_profile_persona(
    records: Dict[Any, Dict[str, str]], profile_id: Any, persona: str, name: str
) -> None:
    if profile_id is None:
        return
    wanted = str(profile_id).strip()
    if not wanted:
        return
    for record in records.values():
        if str(record.get("agent_id")) != wanted:
            continue
        if persona and len(persona) > len(record.get("persona") or ""):
            record["persona"] = persona
        if name and not record.get("name"):
            record["name"] = name
        return


def persona_records(context: Dict[str, Any]) -> List[Dict[str, str]]:
    """Dieselben Akteure wie die Simulation: Typ, Name und Persona-Text."""
    config = context.get("config") or {}
    records: Dict[Any, Dict[str, str]] = {}
    order: List[Any] = []
    for index, agent in enumerate(config.get("agent_configs") or []):
        if not isinstance(agent, dict):
            continue
        agent_id = agent.get("agent_id")
        key = agent_id if agent_id is not None else f"anon-{index}"
        order.append(key)
        records[key] = {
            "agent_id": "" if agent_id is None else str(agent_id),
            "name": str(agent.get("entity_name") or agent.get("name") or "").strip(),
            "group": str(agent.get("entity_type") or "").strip(),
            "persona": str(
                agent.get("persona") or agent.get("bio") or agent.get("summary") or ""
            ).strip(),
        }
    sim_dir = context.get("sim_dir")
    if sim_dir:
        reddit_path = Path(sim_dir) / "reddit_profiles.json"
        if reddit_path.is_file():
            try:
                profiles = json.loads(reddit_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                profiles = []
            if isinstance(profiles, list):
                for profile in profiles:
                    if not isinstance(profile, dict):
                        continue
                    _merge_profile_persona(
                        records,
                        profile.get("agent_id", profile.get("user_id")),
                        str(profile.get("persona") or profile.get("bio") or "").strip(),
                        str(profile.get("name") or "").strip(),
                    )
        twitter_path = Path(sim_dir) / "twitter_profiles.csv"
        if twitter_path.is_file():
            try:
                _fields, rows = _read_twitter_csv(twitter_path)
            except OSError:
                rows = []
            for row in rows:
                _merge_profile_persona(
                    records,
                    row.get("agent_id") or row.get("user_id"),
                    str(row.get("user_char") or row.get("description") or "").strip(),
                    str(row.get("name") or "").strip(),
                )
    return [records[key] for key in order]


def opening_post_texts(context: Dict[str, Any]) -> List[str]:
    posts = ((context.get("config") or {}).get("event_config") or {}).get("initial_posts") or []
    texts = []
    for post in posts:
        if isinstance(post, dict):
            text = str(post.get("content") or "").strip()
        else:
            text = str(post or "").strip()
        if text:
            texts.append(text)
    return texts


def build_null_run_manifest(
    prompt: str,
    *,
    model: str,
    temperature: float,
    seed: int,
    max_tokens: int,
) -> Dict[str, Any]:
    """Manifest für Nullmodell-Läufe (Prompt-Hash, Modell, Temperatur, Seed, Tokenobergrenze)."""
    return {
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "model": str(model),
        "temperature": float(temperature),
        "seed": int(seed),
        "max_tokens": int(max_tokens),
    }


def compute_run_stats(
    posts: Sequence[Dict[str, Any]] = (),
    *,
    narrative: str = "",
    audit: Optional[Dict[str, Any]] = None,
    run_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Textmengen, Klassifikationsstapel und beobachtbare Feed-Lecks je Lauf."""
    texts = [str(post.get("text") or "") for post in posts]
    if narrative:
        character_count = len(narrative)
        post_count = 0
    else:
        character_count = sum(len(text) for text in texts)
        post_count = len(posts)
    document = audit or {}
    if "raters" in document:
        batches = (document.get("raters") or {}).get("a", {}).get("batches") or []
    else:
        batches = document.get("batches") or []
    leak_stats = measure_blind_feed_usage(run_dir) if run_dir else {
        "search_action_count": 0,
        "trend_action_count": 0,
        "foreign_interaction_count": 0,
    }
    action_count = agent_error_count = 0
    logs_present = logs_nonblank = 0
    if run_dir:
        for platform in ("twitter", "reddit"):
            log_path = Path(run_dir) / platform / "actions.jsonl"
            if not log_path.is_file():
                continue
            logs_present += 1
            try:
                lines = log_path.read_text(encoding="utf-8").splitlines()
                if any(line.strip() for line in lines):
                    logs_nonblank += 1
                for line in lines:
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(row, dict) or "action_type" not in row:
                        continue
                    action_count += 1
                    if row.get("success") is False:
                        agent_error_count += 1
            except OSError:
                logger.warning("Agentenfehlerquote konnte nicht aus %s gelesen werden", log_path)
    contribution_count = 1 if narrative.strip() else post_count
    # Simulationslauf ohne zählbare Aktion: die Quote ist nicht 0, sondern unbekannt.
    # Eine Erzählung (Nullarm) hat absichtlich kein Aktionslog.
    if action_count > 0:
        action_log_status = "vorhanden"
    elif logs_present == 0:
        action_log_status = "fehlt"
    elif logs_nonblank == 0:
        action_log_status = "leer"
    else:
        action_log_status = "ohne_aktionen"
    if run_dir and not narrative.strip() and action_count == 0:
        agent_error_rate: Any = "unbekannt"
    else:
        agent_error_rate = _round(agent_error_count / action_count if action_count else 0.0)
    return {
        "post_count": int(post_count),
        "contribution_count": int(contribution_count),
        "character_count": int(character_count),
        "batch_count": int(len(batches)),
        "agent_action_count": action_count,
        "agent_error_count": agent_error_count,
        "agent_error_rate": agent_error_rate,
        "action_log_status": action_log_status,
        **leak_stats,
    }


def measure_blind_feed_usage(run_dir: Path) -> Dict[str, int]:
    """Search/Trend und Interaktionen mit fremden Beiträgen aus OASIS-Traces."""
    counts = {
        "search_action_count": 0,
        "trend_action_count": 0,
        "foreign_interaction_count": 0,
    }
    target_fields = {
        "like_post": "post_id",
        "repost": "reposted_id",
        "quote_post": "quoted_id",
    }
    for platform in ("twitter", "reddit"):
        db_path = Path(run_dir) / f"{platform}_simulation.db"
        if not db_path.is_file():
            continue
        connection = sqlite3.connect(str(db_path))
        connection.row_factory = sqlite3.Row
        try:
            trace_columns = _table_columns(connection, "trace")
            post_columns = _table_columns(connection, "post")
            if not {"user_id", "action", "info"}.issubset(trace_columns):
                continue
            if not {"post_id", "user_id"}.issubset(post_columns):
                continue
            post_authors = {
                int(row["post_id"]): int(row["user_id"])
                for row in connection.execute("SELECT post_id, user_id FROM post")
            }
            comment_posts: Dict[int, int] = {}
            if {"comment_id", "post_id"}.issubset(_table_columns(connection, "comment")):
                comment_posts = {
                    int(row["comment_id"]): int(row["post_id"])
                    for row in connection.execute("SELECT comment_id, post_id FROM comment")
                }
            for row in connection.execute("SELECT user_id, action, info FROM trace"):
                action = str(row["action"] or "").lower()
                if action == "search_posts":
                    counts["search_action_count"] += 1
                    continue
                if action == "trend":
                    counts["trend_action_count"] += 1
                    continue
                if action not in {*target_fields, "create_comment"}:
                    continue
                try:
                    info = json.loads(row["info"] or "{}")
                except (TypeError, json.JSONDecodeError):
                    continue
                if not isinstance(info, dict):
                    continue
                if action == "create_comment":
                    target_post_id = info.get("post_id")
                    if target_post_id is None:
                        try:
                            target_post_id = comment_posts.get(int(info.get("comment_id")))
                        except (TypeError, ValueError):
                            target_post_id = None
                else:
                    target_post_id = info.get(target_fields[action])
                try:
                    author_id = post_authors.get(int(target_post_id))
                    actor_id = int(row["user_id"])
                except (TypeError, ValueError):
                    continue
                if author_id is not None and actor_id != author_id:
                    counts["foreign_interaction_count"] += 1
        except sqlite3.Error:
            logger.warning("Leak-Statistik konnte nicht aus %s gelesen werden", db_path)
        finally:
            connection.close()
    return counts


def build_null_arm_prompt(
    arm: str,
    *,
    document: str,
    question: str,
    hours: int,
    personas: Sequence[Dict[str, Any]] = (),
    initial_posts: Sequence[str] = (),
    target_characters: Optional[int] = None,
) -> str:
    """Dokument und Frage; null_personas zusätzlich Personas, Startbeiträge, Länge, Gruppen."""
    resolved = null_arm(arm) or "null_document"
    parts = [
        f"Eingabematerial:\n{document}",
        f"Frage: {question}",
        f"Zeitraum: {hours} Stunden.",
        "Erzähle einen möglichen Verlauf innerhalb dieses Zeitraums.",
    ]
    if resolved != "null_personas":
        return "\n\n".join(parts)
    lines = []
    groups: List[str] = []
    for persona in personas:
        name = str(persona.get("name") or "").strip()
        group = str(persona.get("group") or "").strip()
        text = str(persona.get("persona") or "").strip()
        if group and group not in groups:
            groups.append(group)
        label = name or group or "Akteur"
        group_bit = f" ({group})" if group and name else ""
        lines.append(f"- {label}{group_bit}: {text or 'keine weitere Persona'}")
    parts.append("Personas:\n" + ("\n".join(lines) if lines else "- keine"))
    openings = [str(item).strip() for item in initial_posts if str(item).strip()]
    parts.append(
        "Startbeiträge:\n" + (
            "\n".join(f"- {item}" for item in openings) if openings else "- keine"
        )
    )
    if groups:
        parts.append(
            "Jede der folgenden Akteursgruppen muss im Verlauf vorkommen: "
            + ", ".join(groups) + "."
        )
    if target_characters is not None:
        parts.append(
            f"Schreibe ungefähr {int(target_characters)} Zeichen, "
            "orientiert am Median der Basis-Transkripte."
        )
    return "\n\n".join(parts)


def _evidence_pairs(raw: Dict[str, Any]) -> List[Tuple[str, str]]:
    snippet = str(raw.get("snippet") or raw.get("span") or raw.get("text_span") or "")
    entries = raw.get("evidence")
    if isinstance(entries, list) and entries and all(isinstance(item, dict) for item in entries):
        pairs = []
        for entry in entries:
            post_id = entry.get("post_id", entry.get("id"))
            span = entry.get("snippet") or entry.get("span") or entry.get("text_span") or snippet
            if post_id is not None:
                pairs.append((str(post_id), str(span or "")))
        return pairs
    evidence_ids = raw.get("post_ids", entries)
    if isinstance(evidence_ids, str):
        evidence_ids = [evidence_ids]
    pairs = []
    if isinstance(evidence_ids, list):
        for post_id in evidence_ids:
            if isinstance(post_id, dict):
                identifier = post_id.get("post_id", post_id.get("id"))
                span = post_id.get("snippet") or post_id.get("span") or snippet
                if identifier is not None:
                    pairs.append((str(identifier), str(span or "")))
            else:
                pairs.append((str(post_id), snippet))
    return pairs


def verify_classification_evidence(
    classification: Any,
    posts: Sequence[Dict[str, Any]],
    checklist: Sequence[Dict[str, Any]],
    run_number: int,
) -> Dict[str, Dict[str, Any]]:
    """Ja nur mit vorhandener Beitrags-ID und wörtlicher Spanne in genau diesem Beitrag."""
    if isinstance(classification, dict):
        rows = classification.get("results", classification.get("outcomes", []))
    else:
        rows = classification
    rows = rows if isinstance(rows, list) else []
    by_outcome = {
        str(row.get("outcome_id")): row for row in rows if isinstance(row, dict)
    }
    posts_by_id: Dict[str, List[Dict[str, Any]]] = {}
    for post in posts:
        posts_by_id.setdefault(str(post["post_id"]), []).append(post)
    verified: Dict[str, Dict[str, Any]] = {}
    for item in checklist:
        outcome_id = str(item["id"])
        raw = by_outcome.get(outcome_id)
        if not isinstance(raw, dict):
            verified[outcome_id] = {"yes": False, "evidence": [], "unclassified": True}
            continue
        yes = _classification_answer(raw)
        if yes is None:
            verified[outcome_id] = {"yes": False, "evidence": [], "unclassified": True}
            continue
        evidence = []
        for post_id, span in _evidence_pairs(raw):
            match = next(
                (
                    post for post in posts_by_id.get(post_id, [])
                    if span_in_text(span, str(post.get("text") or ""))
                ),
                None,
            )
            if match is not None:
                evidence.append({
                    "run": run_number,
                    **match,
                    "span": _normalized_span(span),
                })
        verified[outcome_id] = {"yes": bool(yes and evidence), "evidence": evidence}
        if yes and not evidence:
            verified[outcome_id]["evidence_rejected"] = True
    return verified


_ERROR_LOG_LIMIT = 180


def _is_archived_failure(path: Path) -> bool:
    """Umbenannter Fehlversuch (`run_<n>.failed-…`), nie ein Ergebnisordner."""
    return ".failed-" in Path(path).name


def _clipped_error(error: Any, limit: int = _ERROR_LOG_LIMIT) -> str:
    """Fehlertext fürs Dienstlog: eine Zeile, ohne JSON- oder Listen-Inhalt."""
    text = " ".join(str(error or "").split())
    for marker in ("{", "["):
        position = text.find(marker)
        if position >= 0:
            text = text[:position]
    text = text.rstrip(" :,-")
    if len(text) > limit:
        text = text[:limit].rstrip() + "…"
    return text


def _error_kind(error: Any) -> str:
    if isinstance(error, BaseException):
        return type(error).__name__
    text = str(error or "").strip()
    match = re.match(r"([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception))\b", text)
    if match:
        return match.group(1)
    return _clipped_error(text, limit=60) or "unbekannt"


def _summarize_error_kinds(*audits: Dict[str, Any]) -> str:
    """Fehlerarten der ausgefallenen Stapel, ohne Texte der Beiträge oder Erzählung."""
    counts: Dict[str, int] = {}
    order: List[str] = []
    for audit in audits:
        if not isinstance(audit, dict):
            continue
        for batch in audit.get("batches") or []:
            if not isinstance(batch, dict) or not batch.get("error"):
                continue
            kind = str(batch.get("error_type") or "").strip() or _error_kind(batch.get("error"))
            if kind not in counts:
                order.append(kind)
                counts[kind] = 0
            counts[kind] += 1
    return ", ".join(f"{kind} ×{counts[kind]}" for kind in order)


def _raise_if_fully_unclassified(
    combined: Dict[str, Dict[str, Any]], *audits: Dict[str, Any],
) -> None:
    if combined and all(value.get("unclassified") for value in combined.values()):
        summary = _summarize_error_kinds(*audits)
        message = "Klassifikationsstapel des Laufs vollständig ausgefallen"
        if summary:
            message += f" ({summary})"
        raise RuntimeError(message)


def chat_json_with_retries(
    llm: Any, messages: Sequence[Dict[str, str]], **kwargs: Any
) -> Tuple[Any, Optional[Any], List[str], List[str]]:
    """Fehlgeschlagenen Stapel bis zu zweimal wiederholen. Der Lauf bleibt danach auswertbar."""
    errors: List[str] = []
    error_types: List[str] = []
    raw = None
    for _ in range(BATCH_ATTEMPTS):
        try:
            if hasattr(llm, "last_raw_response"):
                llm.last_raw_response = None
            payload = llm.chat_json(messages, **kwargs)
            raw = getattr(llm, "last_raw_response", None) or payload
            return payload, raw, errors, error_types
        except Exception as error:
            raw = getattr(llm, "last_raw_response", None)
            errors.append(str(error))
            error_types.append(type(error).__name__)
    return None, raw, errors, error_types


def _classification_answer(row: Any) -> Optional[bool]:
    """Nur echte Booleans und eindeutig erkannte Ja-/Nein-Strings akzeptieren."""
    if not isinstance(row, dict):
        return None
    answer = row.get("yes", row.get("answer"))
    if isinstance(answer, bool):
        return answer
    if isinstance(answer, str):
        normalized = answer.strip().casefold()
        if normalized in {"ja", "yes", "true", "1"}:
            return True
        if normalized in {"nein", "no", "false", "0"}:
            return False
    return None


def _returned_outcome_ids(payload: Any, expected_ids: Iterable[str]) -> set[str]:
    """Nur erwartete IDs mit eindeutigem Ja-/Nein-Wert als geliefert werten."""
    expected = set(expected_ids)
    rows = payload.get("results", []) if isinstance(payload, dict) else []
    if not isinstance(rows, list):
        return set()
    by_outcome = {
        str(row.get("outcome_id")): row
        for row in rows
        if isinstance(row, dict) and str(row.get("outcome_id")) in expected
    }
    return {
        outcome_id for outcome_id, row in by_outcome.items()
        if _classification_answer(row) is not None
    }


def _merge_classification_payload(
    base: Any, addition: Any, requested_ids: Iterable[str],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Nur angefragte Ergebniszeilen übernehmen; übrige fürs Audit zurückgeben."""
    base_rows = base.get("results", []) if isinstance(base, dict) else []
    addition_rows = addition.get("results", []) if isinstance(addition, dict) else []
    rows = [row for row in base_rows if isinstance(row, dict)]
    positions = {str(row.get("outcome_id")): index for index, row in enumerate(rows)}
    requested = set(requested_ids)
    rejected: List[Dict[str, Any]] = []
    for row in addition_rows if isinstance(addition_rows, list) else []:
        if not isinstance(row, dict):
            continue
        outcome_id = str(row.get("outcome_id"))
        if outcome_id not in requested:
            rejected.append(row)
            continue
        if outcome_id in positions:
            rows[positions[outcome_id]] = row
        else:
            positions[outcome_id] = len(rows)
            rows.append(row)
    return {"results": rows}, rejected


def _render_post(post: Dict[str, Any]) -> str:
    return f"[{post['post_id']}] {post['agent']}: {post['text']}"


def build_post_batches(
    posts: Sequence[Dict[str, Any]], prompt_prefix: str, token_budget: int,
    reserve_tokens: int = 0,
) -> List[List[Dict[str, Any]]]:
    """Beiträge reihenfolgetreu auf Prompts unterhalb des Eingabebudgets verteilen."""
    effective_budget = token_budget - max(0, int(reserve_tokens))
    if effective_budget <= estimate_tokens(prompt_prefix):
        raise ValueError("Klassifikationsbudget reicht nicht für Anweisung und Checkliste")

    fragments: List[Dict[str, Any]] = []
    for original in posts:
        post = dict(original)
        if estimate_tokens(f"{prompt_prefix}{_render_post(post)}") <= effective_budget:
            fragments.append(post)
            continue
        empty = dict(post, text="")
        available = (effective_budget - estimate_tokens(f"{prompt_prefix}{_render_post(empty)}") - 1) * 3
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
        if current and estimate_tokens(prompt_prefix + compact) > effective_budget:
            batches.append(current)
            current = [post]
        else:
            current = candidate
        if estimate_tokens(prompt_prefix + "\n".join(_render_post(item) for item in current)) > effective_budget:
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
        health_check: Optional[Callable[[], Sequence[str]]] = None,
        ollama_show: Optional[Callable[[str], Dict[str, Any]]] = None,
        sleep: Callable[[float], None] = time.sleep,
        min_free_bytes: int = DEFAULT_MIN_FREE_BYTES,
        ollama_wait_seconds: float = OLLAMA_WAIT_SECONDS,
    ):
        self.runner_cls = runner_cls
        self.llm_factory = llm_factory
        self.root = Path(root or Path(Config.UPLOAD_FOLDER) / "ensembles")
        self.poll_interval = poll_interval
        self.health_check = health_check
        self.ollama_show = ollama_show
        self.sleep = sleep
        self.min_free_bytes = int(min_free_bytes)
        self.ollama_wait_seconds = float(ollama_wait_seconds)
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

    def _llm_for_model(self, model: Optional[str]):
        if not model:
            return self._llm()
        if self.llm_factory is not None:
            try:
                return self.llm_factory(
                    api_key=Config.LOCAL_LLM_API_KEY,
                    base_url=Config.LOCAL_LLM_BASE_URL,
                    model=model,
                )
            except TypeError:
                client = self.llm_factory()
                try:
                    client.model = model
                except (AttributeError, TypeError):
                    pass
                return client
        from ..utils.llm_client import LLMClient
        return LLMClient(
            api_key=Config.LOCAL_LLM_API_KEY,
            base_url=Config.LOCAL_LLM_BASE_URL,
            model=model,
        )

    @staticmethod
    def _llm_model(llm: Any) -> str:
        return str(getattr(llm, "model", None) or "configured-main-model")

    @staticmethod
    def _reject_same_rater_model(state: Dict[str, Any], primary: Any, secondary: Any) -> None:
        if not state.get("strict_second_rater"):
            return
        primary_name = str(getattr(primary, "model", "") or "").strip()
        secondary_name = str(getattr(secondary, "model", "") or "").strip()
        if primary_name and secondary_name and primary_name == secondary_name:
            raise RuntimeError(
                "Haupt- und Zweitbewerter müssen verschiedene Modellnamen haben"
            )

    def _second_rater_llm(self, primary: Any) -> Tuple[Any, bool]:
        """Zweitmodell am lokalen Server; leere Konfiguration bedeutet Seed-Fallback."""
        model = str(os.environ.get(
            "ENSEMBLE_SECOND_RATER_MODEL", Config.ENSEMBLE_SECOND_RATER_MODEL
        ) or "").strip()
        if not model:
            return primary, True
        if self.llm_factory is not None:
            try:
                return self.llm_factory(
                    api_key=Config.LOCAL_LLM_API_KEY,
                    base_url=Config.LOCAL_LLM_BASE_URL,
                    model=model,
                ), False
            except TypeError:
                # Test-/Integrations-Factories ohne Modellparameter bilden beide Bewerter ab.
                client = self.llm_factory()
                try:
                    client.model = model
                except (AttributeError, TypeError):
                    pass
                return client, False
        from ..utils.llm_client import LLMClient

        client = LLMClient(
            api_key=Config.LOCAL_LLM_API_KEY,
            base_url=Config.LOCAL_LLM_BASE_URL,
            model=model,
        )
        client.provider = "local"
        return client, False

    @staticmethod
    def _ollama_enabled() -> bool:
        return str(getattr(Config, "LLM_PROVIDER", "")).lower() == "ollama"

    def _ollama_models(self) -> Sequence[str]:
        if self.health_check is not None:
            return self.health_check()
        base = str(Config.LOCAL_LLM_BASE_URL).rstrip("/")
        if base.endswith("/v1"):
            base = base[:-3]
        request = urllib.request.Request(base + "/api/tags", method="GET")
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return [
            str(item.get("name") or item.get("model") or "")
            for item in payload.get("models", [])
            if isinstance(item, dict)
        ]

    def _ollama_model_show(self, model: str) -> Dict[str, Any]:
        if self.ollama_show is not None:
            return self.ollama_show(model)
        base = str(Config.LOCAL_LLM_BASE_URL).rstrip("/")
        if base.endswith("/v1"):
            base = base[:-3]
        body = json.dumps({"model": model, "name": model}).encode("utf-8")
        request = urllib.request.Request(
            base + "/api/show",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Ollama /api/show lieferte kein JSON-Objekt")
        return payload

    @staticmethod
    def _num_ctx_from_show(payload: Dict[str, Any]) -> Optional[int]:
        parameters = payload.get("parameters")
        if isinstance(parameters, dict):
            value = parameters.get("num_ctx")
            try:
                return int(value) if value is not None else None
            except (TypeError, ValueError):
                return None
        if isinstance(parameters, str):
            match = re.search(r"(?m)^\s*num_ctx\s+(\d+)\s*$", parameters)
            return int(match.group(1)) if match else None
        return None

    def _classification_context(self, llm: Any) -> Dict[str, Any]:
        """Modellbezogenes Eingabebudget; Ollama ohne num_ctx konservativ mit 4096."""
        model = self._llm_model(llm)
        configured_budget = int(os.environ.get(
            "ENSEMBLE_CLASSIFICATION_TOKEN_BUDGET",
            str(Config.ENSEMBLE_CLASSIFICATION_TOKEN_BUDGET),
        ))
        if self._ollama_enabled():
            try:
                show = self._ollama_model_show(model)
            except Exception as error:
                raise ModelServiceUnavailable(
                    f"Ollama /api/show für Bewertermodell {model} nicht erreichbar: {error}"
                ) from error
            declared = self._num_ctx_from_show(show)
            num_ctx = declared or DEFAULT_OLLAMA_NUM_CTX
            source = "ollama_parameter" if declared else "ollama_default"
        else:
            num_ctx = int(os.environ.get("LOCAL_LLM_CONTEXT", str(Config.LOCAL_LLM_CONTEXT)))
            source = "configured_local_context"
        input_budget = min(
            configured_budget,
            num_ctx - CLASSIFICATION_OUTPUT_TOKENS - CLASSIFICATION_CONTEXT_BUFFER,
        )
        return {
            "model": model,
            "num_ctx": num_ctx,
            "num_ctx_source": source,
            "configured_input_budget": configured_budget,
            "output_tokens": CLASSIFICATION_OUTPUT_TOKENS,
            "buffer_tokens": CLASSIFICATION_CONTEXT_BUFFER,
            "input_budget": input_budget,
        }

    @staticmethod
    def _model_present(required: str, available: Sequence[str]) -> bool:
        wanted = str(required).strip()
        return any(name == wanted or name.split(":", 1)[0] == wanted for name in available)

    def _required_models(self, state: Dict[str, Any]) -> List[str]:
        models = state.get("models") or {}
        required = [
            models.get("agents") or Config.LLM_MODEL_NAME,
            models.get("null_arms") or Config.get_llm_config()["model"],
            models.get("classification_primary") or Config.get_llm_config()["model"],
        ]
        if state.get("strict_second_rater"):
            required.append(
                models.get("classification_secondary")
                or str(os.environ.get(
                    "ENSEMBLE_SECOND_RATER_MODEL", Config.ENSEMBLE_SECOND_RATER_MODEL
                ) or "").strip()
            )
        return list(dict.fromkeys(str(value) for value in required if value))

    def _check_models_once(self, state: Dict[str, Any]) -> None:
        if not self._ollama_enabled() and self.health_check is None:
            return
        try:
            available = self._ollama_models()
        except Exception as error:
            raise ModelServiceUnavailable(f"Ollama /api/tags nicht erreichbar: {error}") from error
        missing = [m for m in self._required_models(state) if not self._model_present(m, available)]
        if missing:
            raise ModelServiceUnavailable(
                "Benötigte Ollama-Modelle fehlen: " + ", ".join(missing)
            )

    def _wait_for_models(self, state: Dict[str, Any]) -> None:
        deadline = time.monotonic() + self.ollama_wait_seconds
        delay = 1.0
        while True:
            try:
                self._check_models_once(state)
                return
            except ModelServiceUnavailable:
                if time.monotonic() >= deadline:
                    raise
                if state.get("ensemble_id") and self._cancelled(state):
                    raise InterruptedError
                self.sleep(min(delay, max(0.0, deadline - time.monotonic())))
                delay = min(delay * 2, 60.0)

    def _check_disk_space(self) -> None:
        free = shutil.disk_usage(self.root).free
        if free < self.min_free_bytes:
            raise RuntimeError(
                f"Zu wenig freier Speicher im Ensemble-Datenverzeichnis: "
                f"{free / 1024**3:.2f} GiB frei, mindestens "
                f"{self.min_free_bytes / 1024**3:.2f} GiB erforderlich"
            )

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
        minutes_per_round: int = 60,
        custom_outcomes: Any = None,
        primary_outcome_id: Optional[str] = None,
        text_model: Optional[str] = None,
        arm_model: Optional[str] = None,
        strict_second_rater: bool = False,
        min_classified: Optional[int] = None,
        min_posts: Any = 1,
        max_agent_error_rate: float = DEFAULT_MAX_AGENT_ERROR_RATE,
    ) -> Dict[str, Any]:
        self._check_disk_space()
        from ..utils.security import validate_identifier
        validate_identifier("simulation_id", simulation_id)
        if isinstance(runs, bool) or not isinstance(runs, int) or not 1 <= runs <= 100:
            raise ValueError("runs muss zwischen 1 und 100 liegen")
        if (
            isinstance(hours, bool)
            or not isinstance(hours, int)
            or not 1 <= hours <= MAX_ENSEMBLE_HOURS
        ):
            raise ValueError(f"hours muss zwischen 1 und {MAX_ENSEMBLE_HOURS} liegen")
        if (
            isinstance(start_hour, bool)
            or not isinstance(start_hour, int)
            or not 0 <= start_hour <= 23
        ):
            raise ValueError("start_hour muss zwischen 0 und 23 liegen")
        if (
            isinstance(minutes_per_round, bool)
            or not isinstance(minutes_per_round, int)
            or minutes_per_round not in ALLOWED_MINUTES_PER_ROUND
        ):
            raise ValueError("minutes_per_round muss 60, 120 oder 240 sein")
        if (hours * 60) % minutes_per_round:
            raise ValueError(
                f"hours ({hours}) muss durch minutes_per_round/60 "
                f"({minutes_per_round // 60}) teilbar sein; sonst würden Stunden abgeschnitten"
            )
        variants = validate_variants(variants)
        if not isinstance(strict_second_rater, bool):
            raise ValueError("strict_second_rater muss boolesch sein")
        if min_classified is None:
            min_classified = runs
        if (
            isinstance(min_classified, bool) or not isinstance(min_classified, int)
            or not 1 <= min_classified <= runs
        ):
            raise ValueError("min_classified muss zwischen 1 und runs liegen")
        if min_posts != "agent_count" and (
            isinstance(min_posts, bool) or not isinstance(min_posts, int) or min_posts < 1
        ):
            raise ValueError("min_posts muss mindestens 1 sein oder 'agent_count'")
        if (
            isinstance(max_agent_error_rate, bool)
            or not isinstance(max_agent_error_rate, (int, float))
            or not 0 <= max_agent_error_rate <= 1
        ):
            raise ValueError("max_agent_error_rate muss zwischen 0 und 1 liegen")
        second_model = str(os.environ.get(
            "ENSEMBLE_SECOND_RATER_MODEL", Config.ENSEMBLE_SECOND_RATER_MODEL
        ) or "").strip()
        if strict_second_rater and not second_model:
            raise ValueError("strict_second_rater verlangt ein konfiguriertes Zweitmodell")
        if strict_second_rater:
            primary_model = str(Config.get_llm_config().get("model") or "").strip()
            if primary_model and primary_model == second_model:
                raise ValueError(
                    "Haupt- und Zweitbewerter müssen verschiedene Modellnamen haben"
                )
        custom_outcomes = validate_custom_outcomes(custom_outcomes)
        if primary_outcome_id is not None:
            if not isinstance(primary_outcome_id, str) or not primary_outcome_id.strip():
                raise ValueError("primary_outcome_id muss eine Ergebnis-ID sein")
            primary_outcome_id = primary_outcome_id.strip()
            known_custom = {item["id"] for item in custom_outcomes}
            if primary_outcome_id.startswith("c") and primary_outcome_id not in known_custom:
                raise ValueError(f"primary_outcome_id nicht vorhanden: {primary_outcome_id}")
        source = Path(Config.UPLOAD_FOLDER) / "simulations" / simulation_id
        required = ("simulation_config.json", "reddit_profiles.json", "twitter_profiles.csv", "state.json")
        missing = [name for name in required if not (source / name).is_file()]
        if missing:
            raise FileNotFoundError("Simulation ist nicht vorbereitet; fehlt: " + ", ".join(missing))
        config = _read_json(source / "simulation_config.json")
        if min_posts == "agent_count":
            agents = [
                agent for agent in (config.get("agent_configs") or [])
                if isinstance(agent, dict)
            ]
            if not agents:
                raise ValueError("min_posts agent_count braucht mindestens einen Agenten")
            min_posts = len(agents)
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
        estimate = self.estimate_seconds(
            runs, hours, variants, config, minutes_per_round=minutes_per_round
        )
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
            "minutes_per_round": minutes_per_round,
            "variants": [
                {
                    "key": key,
                    "label_de": _variant_label(key)[0],
                    "label_en": _variant_label(key)[1],
                    "status": "queued",
                    "done": 0,
                    "total": runs,
                    "text_model": str(
                        (arm_model or Config.get_llm_config()["model"])
                        if null_arm(key) else (text_model or Config.LLM_MODEL_NAME)
                    ),
                    "classification_models": {
                        "primary": str(Config.get_llm_config()["model"]),
                        "secondary": second_model or None,
                    },
                }
                for key in variants
            ],
            "checklist": [],
            "custom_outcomes": custom_outcomes,
            "primary_outcome_id": primary_outcome_id,
            "results": {},
            "comparisons": [],
            "reliability": {},
            "consistency_warnings": [],
            "current": None,
            "eta_seconds": estimate,
            "error": None,
            "base_seed": random.SystemRandom().randint(0, 2**31 - runs - 1),
            "cancel_requested": False,
            "current_runner_id": None,
            "strict_second_rater": bool(strict_second_rater),
            "min_classified": min_classified,
            "min_posts": min_posts,
            "max_agent_error_rate": float(max_agent_error_rate),
            "models": {
                "agents": str(text_model or Config.LLM_MODEL_NAME),
                "null_arms": str(arm_model or Config.get_llm_config()["model"]),
                "classification_primary": str(Config.get_llm_config()["model"]),
                "classification_secondary": second_model or None,
            },
            "arm_models": {
                key: str(
                    (arm_model or Config.get_llm_config()["model"])
                    if null_arm(key) else (text_model or Config.LLM_MODEL_NAME)
                )
                for key in variants
            },
        }
        if strict_second_rater:
            self._check_models_once(state)
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
            if state.get("status") in {"completed", "failed", "cancelled"}:
                state["eta_seconds"] = None
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
            item["source"] = item.get("source") or "auto"
            item["polarity"] = stored_polarity(item)
            item["kind"] = item.get("kind") or infer_kind(
                f"{item.get('text_de', '')} {item.get('definition', '')}"
            )
        state["status"] = "queued"
        state["error"] = None
        state["finished_at"] = None
        state["cancel_requested"] = False
        state["current"] = None
        state["current_runner_id"] = None
        state["consistency_warnings"] = []
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

    def _incomplete_seed_exhausted(self, state: Dict[str, Any]) -> bool:
        """Ein unvollständiger Seed hat das Versuchslimit erreicht. Resume würde nichts mehr versuchen."""
        if state.get("attempts_exhausted") is True:
            return True
        attempts = state.get("seed_attempts") or {}
        if not isinstance(attempts, dict):
            return False
        ensemble_id = str(state.get("ensemble_id") or "")
        for key, count in attempts.items():
            if isinstance(count, bool) or not isinstance(count, (int, float)):
                continue
            if int(count) < SEED_ATTEMPTS:
                continue
            variant, _, run_number = str(key).partition(":")
            if not variant or not run_number.isdigit():
                return True
            run_dir = self._path(ensemble_id) / variant / f"run_{run_number}"
            if self._completed_seed_result(run_dir) is None:
                return True
        return False

    def resume(self, ensemble_id: str) -> Dict[str, Any]:
        """Fehlgeschlagenes oder unvollständiges Ensemble am letzten Seed fortsetzen."""
        state = self._load(ensemble_id)
        if not state:
            raise FileNotFoundError(ensemble_id)
        if state.get("status") == "completed":
            return {"ensemble_id": ensemble_id, "status": "completed"}
        if state.get("status") == "cancelled":
            raise RuntimeError("Abgebrochenes Ensemble wird nicht fortgesetzt")
        if self._incomplete_seed_exhausted(state):
            raise RuntimeError(
                f"Versuche erschöpft ({SEED_ATTEMPTS}), Resume abgebrochen: {state.get('error') or 'kein weiterer Versuch'}"
            )
        self._check_disk_space()
        with self._threads_lock:
            alive = self._threads.get(ensemble_id)
            if alive is not None and alive.is_alive():
                raise RuntimeError("Ensemble wird bereits verarbeitet")
        self._terminate_owned_orphan(state)
        state["status"] = "queued"
        state["error"] = None
        state["finished_at"] = None
        state["cancel_requested"] = False
        state["current"] = None
        state["current_runner_id"] = None
        for variant in state["variants"]:
            if variant.get("status") != "completed":
                variant["status"] = "queued"
        self._save(state)
        thread = threading.Thread(target=self._run_ensemble, args=(ensemble_id,), daemon=True)
        with self._threads_lock:
            self._threads[ensemble_id] = thread
        thread.start()
        return {"ensemble_id": ensemble_id, "status": "queued"}

    def _kill_oasis_in_run_dir(self, run_dir: Path) -> bool:
        """SIGTERM nur, wenn cwd genau dieser Laufordner ist und die Kommandozeile OASIS ist."""
        run_state = _read_json(run_dir / "run_state.json")
        pid = run_state.get("process_pid") if isinstance(run_state, dict) else None
        if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 1:
            return False
        proc = Path("/proc") / str(pid)
        try:
            cwd = Path(os.readlink(proc / "cwd")).resolve()
            command = (proc / "cmdline").read_bytes().replace(b"\0", b" ").decode(
                "utf-8", "replace"
            )
        except (OSError, ValueError):
            return False
        if cwd != run_dir.resolve() or "run_parallel_simulation.py" not in command:
            return False
        try:
            pgid = os.getpgid(pid)
            if pgid == os.getpgrp():
                os.kill(pid, signal.SIGTERM)
            else:
                os.killpg(pgid, signal.SIGTERM)
        except (OSError, ProcessLookupError):
            return False
        if not self._wait_gone(pid, ORPHAN_TERM_WAIT_SECONDS):
            try:
                if pgid == os.getpgrp():
                    os.kill(pid, signal.SIGKILL)
                else:
                    os.killpg(pgid, signal.SIGKILL)
            except (OSError, ProcessLookupError):
                pass
            self._wait_gone(pid, 2.0)
        logger.warning(
            "Verwaisten Ensemble-Prozess im Laufordner %s (PID %s) beendet", run_dir, pid
        )
        return True

    @staticmethod
    def _wait_gone(pid: int, seconds: float) -> bool:
        deadline = time.monotonic() + seconds
        while True:
            try:
                state = Path(f"/proc/{pid}/stat").read_text().rpartition(")")[2].split()[0]
            except (OSError, IndexError):
                return True
            if state in {"Z", "X"}:
                return True
            if time.monotonic() >= deadline:
                return False
            time.sleep(0.1)

    @staticmethod
    def _pid_alive(pid: Any) -> bool:
        if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 1:
            return False
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except OSError:
            return True
        return True

    def _owned_by_live_process(self, ensemble_id: str, state: Dict[str, Any]) -> bool:
        """Gehört das Ensemble einem lebenden Thread/Prozess oder wurde es nach unserem Start geschrieben?"""
        with self._threads_lock:
            thread = self._threads.get(ensemble_id)
            if thread is not None and thread.is_alive():
                return True
        owner = state.get("owner_pid")
        if owner != os.getpid() and self._pid_alive(owner):
            return True
        root = self._path(ensemble_id)
        for path in [root / "ensemble.json", *root.glob("*/run_*/run_state.json")]:
            if path.name == "run_state.json" and _is_archived_failure(path.parent):
                continue
            try:
                if path.stat().st_mtime >= PROCESS_START_TIME:
                    return True
            except OSError:
                continue
        return False

    def _terminate_owned_orphan(self, state: Dict[str, Any]) -> bool:
        """Beendet den OASIS-Prozess dieses Ensembles, auch wenn current schon fehlt."""
        ensemble_id = str(state.get("ensemble_id") or "")
        if not ensemble_id:
            return False
        root = self._path(ensemble_id)
        current = state.get("current") or {}
        variant = str(current.get("variant") or "")
        run_number = current.get("run")
        if variant and isinstance(run_number, int) and not isinstance(run_number, bool):
            runner_id = str(state.get("current_runner_id") or "")
            if not runner_id.startswith(ensemble_id + "_"):
                return False
            return self._kill_oasis_in_run_dir(root / variant / f"run_{run_number}")
        # Nach Neustart ist current schon gelöscht; die PID steht nur noch in run_state.json.
        killed = False
        for path in root.glob("*/run_*/run_state.json"):
            killed = self._kill_oasis_in_run_dir(path.parent) or killed
        return killed

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
            if self._owned_by_live_process(str(state.get("ensemble_id") or path.parent.name), state):
                continue
            state["status"] = "failed"
            state["error"] = "Backend wurde neu gestartet, Ensemble abgebrochen"
            current = state.get("current") or {}
            attempt_key = f"{current.get('variant')}:{current.get('run')}"
            attempts = state.get("seed_attempts") or {}
            if current.get("attempt") and attempt_key in attempts:
                attempts[attempt_key] = max(0, int(attempts[attempt_key]) - 1)
            state["finished_at"] = datetime.now().isoformat()
            state["current"] = None
            self._terminate_owned_orphan(state)
            self._save(state)
            count += 1
        return count

    def estimate_seconds(
        self,
        runs: int,
        hours: int,
        variants: Sequence[str],
        config: Dict[str, Any],
        minutes_per_round: Optional[int] = None,
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
        if minutes_per_round is None:
            minutes = int((config.get("time_config") or {}).get("minutes_per_round") or 60)
        else:
            minutes = int(minutes_per_round)
        rounds = max(1, hours * 60 // max(minutes, 1))
        simulation_variants = sum(1 for key in variants if null_arm(key) is None)
        null_runs = runs * sum(1 for key in variants if null_arm(key))
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
        llm = self._llm_for_model(
            (state.get("models") or {}).get("classification_primary")
        )
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
            "dem später gesucht werden soll. Setze kind auf interaction, wenn das Ergebnis eine "
            "Debatte, Diskussion, Antwort, Reaktion auf einen anderen Akteur oder sonstige "
            "direkte Wechselwirkung zwischen Gruppen verlangt, sonst auf event. Nummeriere die "
            "Ergebnisse in der JSON-Reihenfolge gedanklich als o1, o2 usw. Wenn ein absence-Punkt "
            "das direkte Gegenstück zu einem presence-Punkt derselben Checkliste und desselben "
            "Akteurs ist, setze counter_outcome_id auf dessen ID, sonst auf null. Antworte als JSON "
            "{\"outcomes\":[{\"text_de\":...,\"definition\":...,"
            "\"polarity\":\"presence|absence\",\"kind\":\"event|interaction\","
            "\"presence_event\":...,\"counter_outcome_id\":\"o2|null\"}]}.\n\n"
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

        checklist.extend(dict(item) for item in state.get("custom_outcomes", []))
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

    def _null_narrative(
        self,
        state: Dict[str, Any],
        context: Dict[str, Any],
        seed: int,
        arm: str = "null_document",
        target_characters: Optional[int] = None,
        run_dir: Optional[Path] = None,
    ) -> str:
        resolved = null_arm(arm) or "null_document"
        prompt = build_null_arm_prompt(
            resolved,
            document=str(context.get("extracted_text") or ""),
            question=str(state.get("question") or ""),
            hours=int(state.get("hours") or 0),
            personas=persona_records(context) if resolved == "null_personas" else (),
            initial_posts=opening_post_texts(context) if resolved == "null_personas" else (),
            target_characters=target_characters if resolved == "null_personas" else None,
        )
        max_tokens = 4000
        if resolved == "null_personas" and target_characters is not None:
            max_tokens = max(1, math.ceil(int(target_characters) / 3))
        temperature = 0.7
        llm = self._llm_for_model((state.get("models") or {}).get("null_arms"))
        narrative = llm.chat(
            [
                {"role": "system", "content": "Schreibe eine plausible Verlaufserzählung, keine Analyse der Simulation."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            seed=seed,
        )
        if run_dir is not None:
            _write_json_atomic(
                Path(run_dir) / "manifest.json",
                build_null_run_manifest(
                    prompt,
                    model=self._llm_model(llm),
                    temperature=temperature,
                    seed=seed,
                    max_tokens=max_tokens,
                ),
            )
        return narrative

    def _interaction_groups(
        self,
        llm: Any,
        item: Dict[str, Any],
        posts: Sequence[Dict[str, Any]],
        seed: int,
        run_dir: Optional[Path],
    ) -> Dict[str, Any]:
        """Akteure genau einmal je Interaktionsergebnis zwei Seiten zuordnen."""
        config = _read_json(Path(run_dir) / "simulation_config.json") if run_dir else {}
        catalog: Dict[int, Dict[str, Any]] = {}
        for agent in config.get("agent_configs") or []:
            agent_id = _agent_id(agent.get("agent_id"))
            if agent_id is not None:
                catalog[agent_id] = {
                    "agent_id": agent_id,
                    "name": agent.get("entity_name") or f"Agent {agent_id}",
                    "type": agent.get("entity_type") or "Unknown",
                }
        for post in posts:
            agent_id = _agent_id(post.get("agent_id"))
            if agent_id is not None and agent_id not in catalog:
                catalog[agent_id] = {
                    "agent_id": agent_id,
                    "name": post.get("agent") or f"Agent {agent_id}",
                    "type": "Unknown",
                }
        agents = [catalog[key] for key in sorted(catalog)]
        prompt = (
            "Ordne für dieses Interaktionsergebnis die vorhandenen Agenten den zwei im Text "
            "genannten Seiten zu. Nutze ausschließlich agent_id aus dem Katalog; Typ und Name "
            "sind die Grundlage. Agenten, die zu keiner Seite gehören, bleiben weg. JSON: "
            "{\"side_a_label\":\"...\",\"side_a_agent_ids\":[1],"
            "\"side_b_label\":\"...\",\"side_b_agent_ids\":[2]}.\n\n"
            f"Ergebnis: {item.get('text_de')} -- {item.get('definition')}\n"
            f"Agentenkatalog: {json.dumps(agents, ensure_ascii=False)}"
        )
        try:
            raw = llm.chat_json(
                [
                    {"role": "system", "content": "Du ordnest Simulationsagenten Akteursgruppen zu."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
                max_tokens=1000,
                max_attempts=2,
                seed=seed,
            )
        except Exception as error:
            return {"side_a_agent_ids": [], "side_b_agent_ids": [], "error": str(error)}
        valid_ids = set(catalog)

        def valid_list(key: str) -> List[int]:
            values = raw.get(key, []) if isinstance(raw, dict) else []
            if not isinstance(values, list):
                return []
            result = []
            for value in values:
                agent_id = _agent_id(value)
                if agent_id in valid_ids and agent_id not in result:
                    result.append(agent_id)
            return result

        side_a = valid_list("side_a_agent_ids")
        side_b = valid_list("side_b_agent_ids")
        overlap = set(side_a) & set(side_b)
        side_a = [agent_id for agent_id in side_a if agent_id not in overlap]
        side_b = [agent_id for agent_id in side_b if agent_id not in overlap]
        return {
            "side_a_label": str(raw.get("side_a_label") or "Seite A") if isinstance(raw, dict) else "Seite A",
            "side_a_agent_ids": side_a,
            "side_b_label": str(raw.get("side_b_label") or "Seite B") if isinstance(raw, dict) else "Seite B",
            "side_b_agent_ids": side_b,
            "removed_overlapping_agent_ids": sorted(overlap),
            "raw_response": raw,
        }

    def _classify_posts_once(
        self,
        state: Dict[str, Any],
        posts: Sequence[Dict[str, Any]],
        seed: int,
        run_number: int,
        run_dir: Optional[Path] = None,
        llm: Any = None,
        context_info: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
        checklist_items = [
            dict(
                item,
                polarity=stored_polarity(item),
                kind=item.get("kind") or infer_kind(
                    f"{item.get('text_de', '')} {item.get('definition', '')}"
                ),
            )
            for item in state["checklist"]
        ]
        checklist = "\n".join(
            f"{item['id']}: {_positive_event_text(item) if item['polarity'] == 'absence' else (str(item.get('text_de', '')) + ' -- ' + str(item.get('definition', '')))}"
            for item in checklist_items
        )
        rules = (
            "Für jedes aufgeführte positive Ereignis: yes=true nur bei einem eindeutigen Beleg. "
            "Ein konkreter aufgeführter Punkt kann zugleich ein allgemeineres positives Ereignis "
            "belegen; verwende dann dieselben Beitrags-IDs für alle passenden outcome_ids. "
            "Nenne ausschließlich vorhandene IDs. Liefere FÜR JEDE der folgenden IDs genau "
            "einen Eintrag, ausdrücklich auch bei yes=false; keine ID darf ausgelassen werden. "
            "yes=true nur zusammen mit einer kurzen wörtlichen Textspanne aus dem genannten Beitrag. "
            "JSON: {\"results\":[{\"outcome_id\":\"o1\",\"yes\":true,"
            "\"post_ids\":[\"twitter:1\"],\"snippet\":\"wörtliche Spanne\"}]}."
        )
        instruction = (
            f"{rules}\n\n"
            f"Zu prüfende positive Ereignisse:\n{checklist}\n\nBeiträge:\n"
        )
        system = "Klassifiziere streng nur anhand der gelieferten Beiträge."
        llm = llm or self._llm()
        context_info = dict(context_info or self._classification_context(llm))
        output_tokens = int(context_info["output_tokens"])
        token_budget = int(context_info["input_budget"])
        prefix = f"{system}\n{instruction}"
        try:
            batches = build_post_batches(
                posts, prefix, token_budget,
                reserve_tokens=CLASSIFICATION_FOLLOWUP_RESERVE,
            )
        except ValueError as error:
            raise ValueError(
                f"Klassifikationskontext für Modell {context_info['model']} zu klein "
                f"(num_ctx={context_info['num_ctx']}, Eingabebudget={token_budget}): {error}"
            ) from error
        interaction_groups = {
            str(item["id"]): self._interaction_groups(
                llm, item, posts, seed, run_dir
            )
            for item in checklist_items
            if item.get("kind") == "interaction"
        }
        audits: List[Dict[str, Any]] = []
        batch_results: List[Dict[str, Dict[str, Any]]] = []
        for index, batch in enumerate(batches, 1):
            compact = "\n".join(_render_post(post) for post in batch)
            expected_ids = [str(item["id"]) for item in checklist_items]
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": instruction + compact},
            ]
            audit: Dict[str, Any] = {
                "batch": index,
                "post_count": len({str(post.get('post_id')) for post in batch}),
                "estimated_input_tokens": estimate_tokens(messages),
            }
            payload, raw, errors, error_types = chat_json_with_retries(
                llm,
                messages,
                temperature=0,
                max_tokens=output_tokens,
                max_attempts=2,
                seed=seed,
            )
            audit["attempts"] = (len(errors) + 1) if payload is not None else len(errors)
            audit["raw_response"] = raw
            if payload is None:
                verified = {
                    str(item["id"]): {
                        "yes": False, "evidence": [], "unclassified": True,
                    }
                    for item in checklist_items
                }
                audit["error"] = errors[-1] if errors else "Stapel fehlgeschlagen"
                audit["error_type"] = error_types[-1] if error_types else "unbekannt"
                audit["errors"] = errors
                audit["missing_ids_before_followup"] = list(expected_ids)
                audit["missing_ids_after_followup"] = list(expected_ids)
                audit["followups"] = []
                logger.warning(
                    "Klassifikationsstapel %s fehlgeschlagen (%s): %s",
                    index,
                    audit["error_type"],
                    _clipped_error(audit["error"]),
                )
            else:
                missing = [
                    outcome_id for outcome_id in expected_ids
                    if outcome_id not in _returned_outcome_ids(payload, expected_ids)
                ]
                audit["missing_ids_before_followup"] = list(missing)
                followups: List[Dict[str, Any]] = []
                for followup_round in range(1, MISSING_ID_FOLLOWUP_ROUNDS + 1):
                    if not missing:
                        break
                    missing_set = set(missing)
                    missing_checklist = "\n".join(
                        f"{item['id']}: {_positive_event_text(item) if item['polarity'] == 'absence' else (str(item.get('text_de', '')) + ' -- ' + str(item.get('definition', '')))}"
                        for item in checklist_items if str(item["id"]) in missing_set
                    )
                    followup_instruction = (
                        f"{rules}\n\n"
                        "In der vorigen Antwort fehlten Ergebnis-IDs. Klassifiziere jetzt NUR "
                        "die unten genannten fehlenden IDs nach exakt denselben Regeln und anhand "
                        "derselben Beiträge.\n\n"
                        f"Fehlende positive Ereignisse:\n{missing_checklist}\n\nBeiträge:\n{compact}"
                    )
                    followup_messages = [
                        {"role": "system", "content": system},
                        {"role": "user", "content": followup_instruction},
                    ]
                    compact_followup = False
                    if estimate_tokens(followup_messages) > token_budget:
                        compact_followup = True
                        followup_messages = [
                            {"role": "system", "content": system},
                            {"role": "user", "content": (
                                "JSON results nur für diese IDs, je eine Zeile, yes als Boolean. "
                                "true nur bei eindeutigem Beleg mit vorhandener post_id und "
                                "wörtlichem snippet; derselbe konkrete Beleg darf allgemeinere "
                                "passende Ereignisse belegen. Sonst false.\n"
                                f"{missing_checklist}\nBeiträge:\n{compact}"
                            )},
                        ]
                    if estimate_tokens(followup_messages) > token_budget:
                        raise ValueError(
                            f"Auch kompakte Klassifikationsnachfrage für Modell "
                            f"{context_info['model']} überschreitet das Eingabebudget "
                            f"{token_budget} bei num_ctx={context_info['num_ctx']}"
                        )
                    extra, extra_raw, extra_errors, extra_error_types = chat_json_with_retries(
                        llm,
                        followup_messages,
                        temperature=0,
                        max_tokens=output_tokens,
                        max_attempts=2,
                        seed=seed,
                    )
                    followup_audit: Dict[str, Any] = {
                        "round": followup_round,
                        "requested_ids": list(missing),
                        "attempts": ((len(extra_errors) + 1) if extra is not None
                                     else len(extra_errors)),
                        "raw_response": extra_raw,
                        "compact": compact_followup,
                    }
                    if extra is None:
                        followup_audit["error"] = (
                            extra_errors[-1] if extra_errors else "Nachfrage fehlgeschlagen"
                        )
                        followup_audit["errors"] = extra_errors
                        followup_audit["error_type"] = (
                            extra_error_types[-1] if extra_error_types else "unbekannt"
                        )
                    else:
                        payload, rejected_rows = _merge_classification_payload(
                            payload, extra, missing_set
                        )
                        followup_audit["parsed_response"] = extra
                        followup_audit["rejected_rows"] = rejected_rows
                    missing = [
                        outcome_id for outcome_id in expected_ids
                        if outcome_id not in _returned_outcome_ids(payload, expected_ids)
                    ]
                    followup_audit["missing_ids_after"] = list(missing)
                    followups.append(followup_audit)
                audit["followups"] = followups
                audit["missing_ids_after_followup"] = list(missing)
                verified = verify_classification_evidence(
                    payload, batch, checklist_items, run_number
                )
                audit["parsed_response"] = payload
            audit["verified"] = verified
            audits.append(audit)
            batch_results.append(verified)

        positive_by_outcome: Dict[str, List[Dict[str, Any]]] = {}
        unclassified_by_outcome: Dict[str, bool] = {}
        for item in checklist_items:
            oid = str(item["id"])
            values = [result[oid] for result in batch_results]
            unclassified_by_outcome[oid] = any(value.get("unclassified") for value in values)
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
            positive_by_outcome[oid] = positive_evidence

        combined: Dict[str, Dict[str, Any]] = {}
        interaction_checks: Dict[str, Dict[str, Any]] = {}
        for item in checklist_items:
            oid = str(item["id"])
            counter = str(item.get("counter_outcome_id") or "")
            relevant_ids = [oid] + ([counter] if counter else [])
            if any(unclassified_by_outcome.get(value) for value in relevant_ids):
                combined[oid] = {"yes": False, "evidence": [], "unclassified": True}
                continue
            positive_evidence = list(positive_by_outcome.get(oid, []))
            counter_evidence = positive_by_outcome.get(counter, []) if counter else []
            positive_found = bool(positive_evidence or counter_evidence)
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
            structural: List[Dict[str, Any]] = []
            if item.get("kind") == "interaction":
                groups = interaction_groups.get(oid, {})
                structural = structural_interaction_evidence(
                    posts,
                    groups.get("side_a_agent_ids", []),
                    groups.get("side_b_agent_ids", []),
                    run_number,
                )
                interaction_checks[oid] = {
                    "structural_evidence": structural,
                    "mechanism_edges": structural,
                    "accepted": bool(yes),
                    "note": (
                        "Keine DB-Kante zwischen den zugeordneten Gruppen; "
                        "mechanism_edges bleibt leer. Das Ergebnis folgt der Textspanne."
                        if not structural else
                        "DB-Kante liegt als mechanism_edges vor und ist nicht das Ergebnis."
                    ),
                }
            combined[oid] = {"yes": yes, "evidence": evidence}
            if item.get("kind") == "interaction":
                combined[oid]["mechanism_edges"] = structural

        audit_document = {
            "run": run_number,
            "post_count": len(posts),
            "token_budget": token_budget,
            "context": context_info,
            "batches": audits,
            "interaction_groups": interaction_groups,
            "interaction_checks": interaction_checks,
            "result": combined,
        }
        return combined, audit_document

    def _classify_posts(
        self,
        state: Dict[str, Any],
        posts: Sequence[Dict[str, Any]],
        seed: int,
        run_number: int,
        run_dir: Optional[Path] = None,
    ) -> Dict[str, Dict[str, Any]]:
        primary = self._llm_for_model(
            (state.get("models") or {}).get("classification_primary")
        )
        try:
            secondary, seed_fallback = self._second_rater_llm(primary)
        except Exception as error:
            if state.get("strict_second_rater"):
                raise RuntimeError(f"Zweitmodell konnte nicht initialisiert werden: {error}") from error
            secondary, seed_fallback = primary, True
            secondary_setup_error = str(error)
        else:
            secondary_setup_error = ""
        self._reject_same_rater_model(state, primary, secondary)
        primary_context = self._classification_context(primary)
        secondary_context = (
            primary_context if secondary is primary else self._classification_context(secondary)
        )
        result_a, audit_a = self._classify_posts_once(
            state, posts, seed, run_number, run_dir, primary, primary_context
        )
        second_seed = seed + 1_000_003
        result_b, audit_b = self._classify_posts_once(
            state, posts, second_seed, run_number, run_dir, secondary, secondary_context
        )
        if secondary_setup_error:
            audit_b["fallback_reason"] = (
                "Zweitmodell konnte nicht initialisiert werden; Hauptmodell mit anderem Seed: "
                + secondary_setup_error
            )
        unavailable = bool(audit_b.get("batches")) and all(
            batch.get("error") for batch in audit_b["batches"]
        )
        if unavailable and secondary is not primary:
            if state.get("strict_second_rater"):
                raise RuntimeError("Zweitmodell nicht erreichbar; strikter Zweitbewerter aktiv")
            secondary = primary
            seed_fallback = True
            result_b, audit_b = self._classify_posts_once(
                state, posts, second_seed, run_number, run_dir, secondary, primary_context
            )
            audit_b["fallback_reason"] = "Zweitmodell nicht erreichbar; Hauptmodell mit anderem Seed"
        combined = combine_rater_results(result_a, result_b, state["checklist"])
        audit_document = {
            "run": run_number,
            "post_count": len(posts),
            "raters": {
                "a": {"model": self._llm_model(primary), "seed": seed, **audit_a},
                "b": {
                    "model": self._llm_model(secondary),
                    "seed": second_seed,
                    "seed_fallback": seed_fallback,
                    **audit_b,
                },
            },
            "result": combined,
        }
        if run_dir is not None:
            _write_json_atomic(Path(run_dir) / "classification.json", audit_document)
        _raise_if_fully_unclassified(combined, audit_a, audit_b)
        return combined

    def _classify_narrative_once(
        self,
        state: Dict[str, Any],
        narrative: str,
        seed: int,
        run_number: int,
        llm: Any,
        variant_key: str = "null_model",
        context_info: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
        checklist = "\n".join(
            f"{o['id']}: {_positive_event_text(o) if stored_polarity(o) == 'absence' else (str(o.get('text_de', '')) + ' -- ' + str(o.get('definition', '')))}"
            for o in state["checklist"]
        )
        context_info = dict(context_info or self._classification_context(llm))
        narrative_rules = (
            "Prüfe die aufgeführten positiven Ereignisse. JSON: {\"results\":[{"
            "\"outcome_id\":\"o1\",\"yes\":true,\"snippet\":\"wörtliche kurze "
            "Textstelle\"}]}. Liefere FÜR JEDE der folgenden IDs genau einen Eintrag, "
            "ausdrücklich auch bei yes=false; keine ID darf ausgelassen werden. "
            "Ja erfordert eine wörtliche Textspanne, die das Ereignis trägt, "
            "auch bei Interaktion. Die Datenbankkante ist nicht das Ergebnis."
        )
        messages = [
            {"role": "system", "content": "Klassifiziere streng nur anhand der Erzählung."},
            {"role": "user", "content": (
                f"{narrative_rules}\n\n"
                f"Ereignisse:\n{checklist}\n\nErzählung:\n{narrative}"
            )},
        ]
        token_budget = int(context_info["input_budget"])
        if estimate_tokens(messages) > token_budget:
            raise ValueError(
                f"Klassifikationskontext für Modell {context_info['model']} zu klein "
                f"(num_ctx={context_info['num_ctx']}, Eingabebudget={token_budget}): "
                "Anweisung, Checkliste und Erzählung passen nicht"
            )
        payload, raw, errors, error_types = chat_json_with_retries(
            llm,
            messages,
            temperature=0,
            max_tokens=int(context_info["output_tokens"]),
            max_attempts=2,
            seed=seed,
        )
        parse_error = errors[-1] if payload is None else None
        error_type = error_types[-1] if payload is None and error_types else None
        if parse_error:
            logger.warning(
                "Klassifikationsstapel 1 fehlgeschlagen (%s): %s",
                error_type or "unbekannt",
                _clipped_error(parse_error),
            )
        expected_ids = [str(item["id"]) for item in state["checklist"]]
        missing = (
            expected_ids if payload is None else [
                outcome_id for outcome_id in expected_ids
                if outcome_id not in _returned_outcome_ids(payload, expected_ids)
            ]
        )
        missing_before = list(missing)
        followups: List[Dict[str, Any]] = []
        if payload is not None:
            for followup_round in range(1, MISSING_ID_FOLLOWUP_ROUNDS + 1):
                if not missing:
                    break
                missing_set = set(missing)
                missing_checklist = "\n".join(
                    f"{o['id']}: {_positive_event_text(o) if stored_polarity(o) == 'absence' else (str(o.get('text_de', '')) + ' -- ' + str(o.get('definition', '')))}"
                    for o in state["checklist"] if str(o["id"]) in missing_set
                )
                followup_messages = [
                    {"role": "system", "content": messages[0]["content"]},
                    {"role": "user", "content": (
                        f"{narrative_rules}\n\n"
                        "In der vorigen Antwort fehlten Ergebnis-IDs. Klassifiziere jetzt NUR "
                        "die unten genannten IDs nach exakt denselben Regeln anhand derselben "
                        "Erzählung.\n\n"
                        f"Fehlende Ereignisse:\n{missing_checklist}\n\nErzählung:\n{narrative}"
                    )},
                ]
                compact_followup = False
                if estimate_tokens(followup_messages) > token_budget:
                    compact_followup = True
                    followup_messages = [
                        {"role": "system", "content": messages[0]["content"]},
                        {"role": "user", "content": (
                            "JSON results nur für diese IDs, je eine Zeile, yes als Boolean. "
                            "true nur mit einer wörtlichen, das Ereignis tragenden Textstelle; "
                            "das gilt auch für Interaktionen, eine Datenbankkante genügt nicht. "
                            "Sonst false.\n"
                            f"{missing_checklist}\nErzählung:\n{narrative}"
                        )},
                    ]
                if estimate_tokens(followup_messages) > token_budget:
                    raise ValueError(
                        f"Auch kompakte Klassifikationsnachfrage für Modell "
                        f"{context_info['model']} überschreitet das Eingabebudget "
                        f"{token_budget} bei num_ctx={context_info['num_ctx']}"
                    )
                extra, extra_raw, extra_errors, extra_error_types = chat_json_with_retries(
                    llm, followup_messages, temperature=0,
                    max_tokens=int(context_info["output_tokens"]), max_attempts=2, seed=seed,
                )
                followup_audit: Dict[str, Any] = {
                    "round": followup_round,
                    "requested_ids": list(missing),
                    "attempts": ((len(extra_errors) + 1) if extra is not None
                                 else len(extra_errors)),
                    "raw_response": extra_raw,
                    "compact": compact_followup,
                }
                if extra is None:
                    followup_audit["error"] = (
                        extra_errors[-1] if extra_errors else "Nachfrage fehlgeschlagen"
                    )
                    followup_audit["errors"] = extra_errors
                    followup_audit["error_type"] = (
                        extra_error_types[-1] if extra_error_types else "unbekannt"
                    )
                else:
                    payload, rejected_rows = _merge_classification_payload(
                        payload, extra, missing_set
                    )
                    followup_audit["parsed_response"] = extra
                    followup_audit["rejected_rows"] = rejected_rows
                missing = [
                    outcome_id for outcome_id in expected_ids
                    if outcome_id not in _returned_outcome_ids(payload, expected_ids)
                ]
                followup_audit["missing_ids_after"] = list(missing)
                followups.append(followup_audit)
        rows = payload.get("results", []) if isinstance(payload, dict) else []
        by_id = {str(r.get("outcome_id")): r for r in rows if isinstance(r, dict)}
        positive: Dict[str, Tuple[bool, str]] = {}
        for outcome in state["checklist"]:
            raw_row = by_id.get(outcome["id"])
            if parse_error or not isinstance(raw_row, dict):
                positive[outcome["id"]] = (False, "")
                continue
            answer = _classification_answer(raw_row)
            snippet = " ".join(str(raw_row.get("snippet") or "").split())
            valid = bool(answer is True and span_in_text(snippet, narrative))
            positive[outcome["id"]] = (valid, snippet if valid else "")

        result = {}
        for outcome in state["checklist"]:
            raw_row = by_id.get(outcome["id"])
            counter = str(outcome.get("counter_outcome_id") or "")
            kind = outcome.get("kind") or infer_kind(
                f"{outcome.get('text_de', '')} {outcome.get('definition', '')}"
            )
            interaction = kind == "interaction"
            # Ein geparster Stapel ohne Zeile bleibt unklassifiziert. Nach ausgeschöpften
            # Wiederholungen zählt der Lauf weiter, nur ohne Beleg.
            if parse_error or (
                _classification_answer(raw_row) is None
                or (counter and _classification_answer(by_id.get(counter)) is None)
            ):
                record: Dict[str, Any] = {"yes": False, "evidence": [], "unclassified": True}
                if interaction:
                    record["mechanism_edges"] = []
                result[outcome["id"]] = record
                continue
            positive_found, snippet = positive.get(outcome["id"], (False, ""))
            if counter:
                positive_found = positive_found or positive.get(counter, (False, ""))[0]
            absence = stored_polarity(outcome) == "absence"
            yes = not positive_found if absence else positive_found
            record = {
                "yes": yes,
                "evidence": ([{
                    "run": run_number,
                    "platform": variant_key,
                    "post_id": f"null:{run_number}",
                    "agent": "Hauptmodell",
                    "text": ("kein passendes Ereignis in der geprüften Erzählung" if absence else snippet),
                    "span": snippet,
                }] if yes else []),
            }
            rejected_ids = [outcome["id"]] + ([counter] if counter else [])
            if any(
                _classification_answer(by_id.get(rejected_id)) is True
                and not positive.get(rejected_id, (False, ""))[0]
                for rejected_id in rejected_ids
            ):
                record["evidence_rejected"] = True
            if interaction:
                record["mechanism_edges"] = []
            result[outcome["id"]] = record
        batch_audit = {
            "batch": 1,
            "attempts": (len(errors) + 1) if payload is not None else len(errors),
            "raw_response": raw if not parse_error else None,
            "error": parse_error,
            "verified": result,
        }
        if error_type:
            batch_audit["error_type"] = error_type
        batch_audit["missing_ids_before_followup"] = missing_before
        batch_audit["missing_ids_after_followup"] = list(missing)
        batch_audit["followups"] = followups
        audit = {
            "context": context_info,
            "batches": [batch_audit],
            "result": result,
        }
        return result, audit

    def _classify_narrative(
        self,
        state: Dict[str, Any],
        narrative: str,
        seed: int,
        run_number: int,
        run_dir: Optional[Path] = None,
        variant_key: str = "null_model",
    ) -> Dict[str, Dict[str, Any]]:
        primary = self._llm_for_model(
            (state.get("models") or {}).get("classification_primary")
        )
        try:
            secondary, seed_fallback = self._second_rater_llm(primary)
        except Exception as error:
            if state.get("strict_second_rater"):
                raise RuntimeError(f"Zweitmodell konnte nicht initialisiert werden: {error}") from error
            secondary, seed_fallback = primary, True
            secondary_setup_error = str(error)
        else:
            secondary_setup_error = ""
        self._reject_same_rater_model(state, primary, secondary)
        primary_context = self._classification_context(primary)
        secondary_context = (
            primary_context if secondary is primary else self._classification_context(secondary)
        )
        result_a, audit_a = self._classify_narrative_once(
            state, narrative, seed, run_number, primary, variant_key, primary_context
        )
        second_seed = seed + 1_000_003
        result_b, audit_b = self._classify_narrative_once(
            state, narrative, second_seed, run_number, secondary, variant_key,
            secondary_context,
        )
        if secondary_setup_error:
            audit_b["fallback_reason"] = (
                "Zweitmodell konnte nicht initialisiert werden; Hauptmodell mit anderem Seed: "
                + secondary_setup_error
            )
        if audit_b["batches"][0].get("error") and secondary is not primary:
            if state.get("strict_second_rater"):
                raise RuntimeError("Zweitmodell nicht erreichbar; strikter Zweitbewerter aktiv")
            secondary = primary
            seed_fallback = True
            result_b, audit_b = self._classify_narrative_once(
                state, narrative, second_seed, run_number, secondary, variant_key,
                primary_context,
            )
            audit_b["fallback_reason"] = "Zweitmodell nicht erreichbar; Hauptmodell mit anderem Seed"
        combined = combine_rater_results(result_a, result_b, state["checklist"])
        audit_document = {
                "run": run_number,
                "post_count": 1,
                "raters": {
                    "a": {"model": self._llm_model(primary), "seed": seed, **audit_a},
                    "b": {
                        "model": self._llm_model(secondary), "seed": second_seed,
                        "seed_fallback": seed_fallback, **audit_b,
                    },
                },
                "result": combined,
            }
        if run_dir is not None:
            _write_json_atomic(Path(run_dir) / "classification.json", audit_document)
        _raise_if_fully_unclassified(combined, audit_a, audit_b)
        return combined

    def _aggregate(self, state: Dict[str, Any], per_run: Dict[str, List[Dict[str, Any]]]) -> None:
        results = {}
        consistency_warnings = []
        for variant in state["variants"]:
            key = variant["key"]
            results[key] = {}
            runs = per_run.get(key, [])
            for run_number, row in enumerate(runs, 1):
                for outcome in state["checklist"]:
                    counter = str(outcome.get("counter_outcome_id") or "")
                    if (
                        stored_polarity(outcome) == "absence"
                        and counter
                        and row.get(outcome["id"], {}).get("yes")
                        and row.get(counter, {}).get("yes")
                    ):
                        consistency_warnings.append({
                            "variant": key,
                            "run": run_number,
                            "absence_outcome_id": outcome["id"],
                            "presence_outcome_id": counter,
                            "message": (
                                "Presence- und Absence-Ergebnis zum selben Akteur "
                                "wurden im selben Lauf beide mit Ja klassifiziert."
                            ),
                        })
            for outcome in state["checklist"]:
                oid = outcome["id"]
                unclassified = sum(
                    1 for row in runs if row.get(oid, {}).get("unclassified")
                )
                disputed = sum(
                    1 for row in runs if row.get(oid, {}).get("disputed")
                )
                classified_runs = [
                    row for row in runs
                    if not row.get(oid, {}).get("unclassified")
                    and not row.get(oid, {}).get("disputed")
                ]
                yes = sum(1 for row in classified_runs if row.get(oid, {}).get("yes"))
                n = len(classified_runs)
                low, high = wilson_interval(yes, n) if n else (None, None)
                evidence = [
                    item
                    for row in classified_runs
                    for item in row.get(oid, {}).get("evidence", [])
                ][:5]
                results[key][oid] = {
                    "yes": yes,
                    "n": n,
                    "unclassified": unclassified,
                    "disputed": disputed,
                    "rate": _round(yes / n) if n else None,
                    "ci_low": _round(low) if low is not None else None,
                    "ci_high": _round(high) if high is not None else None,
                    "evidence": evidence,
                    "measurable": n >= int(state.get("min_classified", state.get("runs", 1))),
                }
                if any("mechanism_edges" in (row.get(oid) or {}) for row in runs):
                    results[key][oid]["mechanism_edge_runs"] = sum(
                        1 for row in classified_runs if row.get(oid, {}).get("mechanism_edges")
                    )
        state["results"] = results
        state["unclassified_runs_by_variant"] = {
            key: sum(
                1 for row in runs
                if any(
                    isinstance(value, dict) and value.get("unclassified")
                    for value in row.values()
                )
            )
            for key, runs in per_run.items()
        }
        state["unclassified_runs"] = sum(state["unclassified_runs_by_variant"].values())
        unmeasurable = [
            {"variant": key, "outcome_id": oid, "classified": value["n"]}
            for key, outcomes in results.items()
            for oid, value in outcomes.items()
            if not value["measurable"]
        ]
        state["measurement"] = {
            "min_classified": int(state.get("min_classified", state.get("runs", 1))),
            "measurable": not unmeasurable,
            "unmeasurable": unmeasurable,
        }
        state["consistency_warnings"] = consistency_warnings
        reliability = {}
        for outcome in state["checklist"]:
            oid = outcome["id"]
            pairs: List[Tuple[bool, bool]] = []
            for runs in per_run.values():
                for row in runs:
                    judgment = row.get(oid, {})
                    raters = judgment.get("raters", {})
                    left, right = raters.get("a", {}), raters.get("b", {})
                    if (
                        isinstance(left, dict) and isinstance(right, dict)
                        and not left.get("unclassified") and not right.get("unclassified")
                        and "yes" in left and "yes" in right
                    ):
                        pairs.append((bool(left["yes"]), bool(right["yes"])))
            metric = cohens_kappa(pairs)
            metric["label"] = reliability_label(metric["kappa"])
            reliability[oid] = metric
        state["reliability"] = reliability
        rows = canonical_outcome_rows(state.get("checklist") or [])
        folded_into = {
            collapsed: row["outcome_id"]
            for row in rows
            for collapsed in row["collapsed_outcome_ids"]
        }
        for item in state.get("checklist") or []:
            target = folded_into.get(str(item.get("id")))
            if target:
                item["collapsed_into"] = target
            else:
                item.pop("collapsed_into", None)
        if state.get("checklist"):
            state["primary_outcome_id"] = resolve_primary_outcome_id(
                state["checklist"], state.get("primary_outcome_id") or None
            )
        primary = str(state.get("primary_outcome_id") or "")
        comparisons = []
        baseline_runs = per_run.get("baseline", [])
        marginal_baseline = results.get("baseline", {})
        for variant in state["variants"]:
            key = variant["key"]
            if key == "baseline":
                continue
            variant_runs = per_run.get(key, [])
            for row in rows:
                oid = row["outcome_id"]
                table = paired_outcome_table(baseline_runs, variant_runs, oid)
                value = results[key][oid]
                base = marginal_baseline[oid]
                newcombe_low, newcombe_high = newcombe_difference_interval(
                    value["yes"], value["n"], base["yes"], base["n"]
                )
                paired_low, paired_high = paired_difference_interval(
                    table["baseline_only"], table["variant_only"], table["n_pairs"]
                )
                confirmatory = primary == oid or primary in row["collapsed_outcome_ids"]
                diff = (
                    (table["variant_only"] - table["baseline_only"]) / table["n_pairs"]
                    if table["n_pairs"] else 0.0
                )
                comparisons.append({
                    "variant": key,
                    "outcome_id": oid,
                    "collapsed_outcome_ids": row["collapsed_outcome_ids"],
                    "role": "confirmatory" if confirmatory else "exploratory",
                    "table": table,
                    "diff": _round(diff),
                    "ci_low": _round(paired_low),
                    "ci_high": _round(paired_high),
                    "mcnemar_p": _round(exact_mcnemar_p(
                        table["baseline_only"], table["variant_only"]
                    ), 6),
                    "newcombe": {
                        "ci_low": _round(newcombe_low),
                        "ci_high": _round(newcombe_high),
                    },
                    "unreliable": reliability.get(oid, {}).get("label") == "nicht messbar",
                })
                comparisons[-1]["unreliable"] = bool(
                    comparisons[-1]["unreliable"]
                    or not value.get("measurable")
                    or not base.get("measurable")
                )
        family = [
            comparison for comparison in comparisons
            if comparison["role"] == "exploratory" and comparison["table"]["n_pairs"] > 0
        ]
        adjusted = holm_adjust([comparison["mcnemar_p"] for comparison in family])
        for comparison, holm_p in zip(family, adjusted):
            comparison["holm_p"] = _round(holm_p, 6)
        for comparison in comparisons:
            comparison.setdefault("holm_p", None)
        state["comparisons"] = comparisons
        state["analysis"] = {
            "primary_outcome_id": primary,
            "confirmatory": "exact_mcnemar",
            "paired_interval": "wald",
            "sensitivity": "newcombe_method_10",
            "exploratory_correction": "holm",
            "exploratory_m": len(family),
        }

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
                run_stats: Dict[str, List[Dict[str, Any]]] = {}
                state["run_stats"] = run_stats
                for variant in state["variants"]:
                    key = variant["key"]
                    variant["status"] = "running"
                    per_run[key] = []
                    run_stats[key] = []
                    self._save(state)
                    for run_number in range(1, int(state["runs"]) + 1):
                        if self._cancelled(state):
                            raise InterruptedError
                        seed = int(state["base_seed"]) + run_number
                        run_dir = self._path(ensemble_id) / key / f"run_{run_number}"
                        state["current"] = {"variant": key, "run": run_number, "round": 0}
                        self._save(state)
                        if null_arm(key):
                            narrative_path = run_dir / "narrative.txt"
                            if not narrative_path.is_file():
                                raise FileNotFoundError(f"Gespeicherte Erzählung fehlt: {narrative_path}")
                            narrative = narrative_path.read_text(encoding="utf-8")
                            classified = self._classify_narrative(
                                state,
                                narrative,
                                seed,
                                run_number,
                                run_dir,
                                key,
                            )
                            audit = _read_json(run_dir / "classification.json")
                            stats = compute_run_stats(
                                narrative=narrative, audit=audit, run_dir=run_dir
                            )
                        else:
                            config = _read_json(run_dir / "simulation_config.json")
                            initial = (config.get("event_config") or {}).get("initial_posts") or []
                            posts = load_simulation_posts(run_dir, initial)
                            classified = self._classify_posts(
                                state, posts, seed, run_number, run_dir
                            )
                            audit = _read_json(run_dir / "classification.json")
                            stats = compute_run_stats(posts, audit=audit, run_dir=run_dir)
                        run_stats[key].append({"run": run_number, **stats})
                        per_run[key].append(classified)
                        variant["done"] = run_number
                        self._save(state)
                    variant["status"] = "completed"
                    self._save(state)

                state["run_stats"] = run_stats
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

    @staticmethod
    def _audit_has_batch_failure(payload: Dict[str, Any]) -> bool:
        raters = payload.get("raters")
        documents = list(raters.values()) if isinstance(raters, dict) and raters else [payload]
        return any(
            batch.get("error")
            for document in documents if isinstance(document, dict)
            for batch in (document.get("batches") or []) if isinstance(batch, dict)
        )

    def _completed_seed_result(
        self,
        run_dir: Path,
        state: Optional[Dict[str, Any]] = None,
        key: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        if _is_archived_failure(run_dir):
            return None
        path = run_dir / "classification.json"
        if not path.is_file():
            return None
        payload = _read_json(path)
        result = payload.get("result") if isinstance(payload, dict) else None
        if not isinstance(result, dict) or not result or self._audit_has_batch_failure(payload):
            return None
        if result and all(
            isinstance(value, dict) and value.get("unclassified")
            for value in result.values()
        ):
            return None
        if state is not None and key is not None:
            stats = self._stats_for_run(key, run_dir)
            if not self._run_quality_ok(state, stats, key):
                return None
        return result

    @staticmethod
    def _run_quality_ok(
        state: Dict[str, Any], stats: Dict[str, Any], key: Optional[str] = None,
    ) -> bool:
        if null_arm(key or ""):
            return int(stats.get("contribution_count", 0) or 0) >= 1
        rate = stats.get("agent_error_rate", 0.0)
        minimum = int(state.get("min_posts", 1) or 1)
        if int(stats.get("contribution_count", stats.get("post_count", 0)) or 0) < minimum:
            return False
        if rate == "unbekannt":
            return True
        return float(rate or 0.0) <= float(
            state.get("max_agent_error_rate", DEFAULT_MAX_AGENT_ERROR_RATE))

    def _validate_run_quality(self, state: Dict[str, Any], key: str, run_dir: Path) -> None:
        stats = self._stats_for_run(key, run_dir)
        if null_arm(key):
            if int(stats.get("contribution_count", 0) or 0) < 1:
                raise RuntimeError("Technischer Fehlschlag: Nullarm ohne Erzählung")
            return
        log_status = {
            "fehlt": "Aktionslog fehlt", "leer": "Aktionslog leer",
            "ohne_aktionen": "Aktionslog ohne Aktionen",
        }.get(str(stats.get("action_log_status")), "")
        if int(stats.get("contribution_count", 0)) < int(state.get("min_posts", 1)):
            raise RuntimeError(
                f"Technischer Fehlschlag: nur {stats.get('contribution_count', 0)} Beiträge "
                f"(Minimum {state.get('min_posts', 1)})"
                + (f"; {log_status}" if log_status else "")
            )
        if stats.get("agent_error_rate") == "unbekannt":
            # Ohne Aktionen ist die Quote nicht prüfbar; über den Lauf entscheidet min_posts.
            return
        rate = float(stats.get("agent_error_rate", 0.0) or 0.0)
        limit = float(state.get("max_agent_error_rate", DEFAULT_MAX_AGENT_ERROR_RATE))
        if rate > limit:
            raise RuntimeError(
                f"Technischer Fehlschlag: Agenten-Fehlerquote {rate:.3f} über Grenzwert {limit:.3f}"
            )

    def _stats_for_run(self, key: str, run_dir: Path) -> Dict[str, int]:
        """run_stats aus dem gespeicherten Lauf, auch wenn der Seed nur fortgesetzt wird."""
        audit = _read_json(run_dir / "classification.json")
        if null_arm(key):
            narrative_path = run_dir / "narrative.txt"
            narrative = (
                narrative_path.read_text(encoding="utf-8")
                if narrative_path.is_file() else ""
            )
            return compute_run_stats(narrative=narrative, audit=audit, run_dir=run_dir)
        initial: List[Dict[str, Any]] = []
        config = _read_json(run_dir / "simulation_config.json")
        if config:
            initial = (config.get("event_config") or {}).get("initial_posts") or []
        return compute_run_stats(
            load_simulation_posts(run_dir, initial), audit=audit, run_dir=run_dir
        )

    def _execute_seed(
        self,
        state: Dict[str, Any],
        context: Dict[str, Any],
        source: Path,
        ensemble_id: str,
        key: str,
        run_number: int,
        seed: int,
        run_dir: Path,
    ) -> Dict[str, Any]:
        if null_arm(key):
            run_dir.mkdir(parents=True, exist_ok=False)
            target_characters = None
            if null_arm(key) == "null_personas":
                target_characters = median_character_count(
                    baseline_transcript_lengths(self._path(ensemble_id))
                )
            narrative = self._null_narrative(
                state, context, seed, key, target_characters, run_dir
            )
            (run_dir / "narrative.txt").write_text(narrative, encoding="utf-8")
            result = self._classify_narrative(
                state, narrative, seed, run_number, run_dir, key
            )
            self._validate_run_quality(state, key, run_dir)
            return result
        config = prepare_run_directory(
            source,
            run_dir,
            key,
            state["hours"],
            state.get("start_hour", 7),
            state.get("minutes_per_round"),
            (state.get("models") or {}).get("agents"),
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
            llm_model=(state.get("models") or {}).get("agents"),
        )
        while _runner_status(runner_state) not in TERMINAL_RUNNER_STATES:
            if self._cancelled(state):
                try:
                    self._runner().stop_simulation(runner_id)
                finally:
                    raise InterruptedError
            state["current"]["round"] = int(getattr(runner_state, "current_round", 0) or 0)
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
        result = self._classify_posts(state, posts, seed, run_number, run_dir)
        self._validate_run_quality(state, key, run_dir)
        return result

    def _archive_failed_attempt(
        self,
        state: Dict[str, Any],
        failure_key: str,
        run_dir: Path,
        error: BaseException,
        attempt: int,
    ) -> Optional[Path]:
        """Fehlversuch umbenennen. Der Ordner bleibt und zählt beim freien Plattenplatz mit."""
        if not run_dir.exists():
            return None
        stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        destination = Path(f"{run_dir}.failed-{attempt}-{stamp}")
        extra = 0
        while destination.exists():
            extra += 1
            destination = Path(f"{run_dir}.failed-{attempt}-{stamp}-{extra}")
        run_dir.rename(destination)
        failures = state.setdefault("seed_failures", {})
        if not isinstance(failures, dict):
            failures = {}
            state["seed_failures"] = failures
        bucket = failures.setdefault(failure_key, [])
        if not isinstance(bucket, list):
            bucket = []
            failures[failure_key] = bucket
        text = str(error)
        if len(text) > 2000:
            text = text[:2000] + "…"
        bucket.append({
            "path": str(destination),
            "error": text,
            "at": datetime.now().isoformat(timespec="seconds"),
            "attempt": int(attempt),
        })
        return destination

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
                state["owner_pid"] = os.getpid()
                self._save(state)
                context = load_simulation_context(state["simulation_id"])
                if not state.get("checklist"):
                    state["checklist"] = self._create_checklist(state, context)
                state["primary_outcome_id"] = resolve_primary_outcome_id(
                    state["checklist"], state.get("primary_outcome_id") or None
                )
                self._save(state)
                source = Path(context["sim_dir"])
                per_run: Dict[str, List[Dict[str, Any]]] = {}
                variant_by_key = {item["key"]: item for item in state["variants"]}

                run_stats: Dict[str, List[Dict[str, Any]]] = {}
                state["run_stats"] = run_stats
                for key in execution_variant_keys([item["key"] for item in state["variants"]]):
                    variant = variant_by_key[key]
                    variant["status"] = "running"
                    per_run[key] = []
                    run_stats[key] = []
                    self._save(state)
                    attempts = state.setdefault("seed_attempts", {})
                    for run_number in range(1, state["runs"] + 1):
                        if self._cancelled(state):
                            raise InterruptedError
                        seed = state["base_seed"] + run_number
                        run_dir = self._path(ensemble_id) / key / f"run_{run_number}"
                        state["current"] = {"variant": key, "run": run_number, "round": 0}
                        self._save(state)
                        completed = self._completed_seed_result(run_dir, state, key)
                        if completed is not None:
                            run_stats[key].append({
                                "run": run_number,
                                **self._stats_for_run(key, run_dir),
                            })
                            per_run[key].append(completed)
                            variant["done"] = run_number
                            self._save(state)
                            continue
                        failure_key = f"{key}:{run_number}"
                        if run_dir.exists():
                            prior = int(attempts.get(failure_key, 0) or 0)
                            if prior <= 0:
                                recorded = (state.get("seed_failures") or {}).get(failure_key)
                                prior = len(recorded) + 1 if isinstance(recorded, list) else 1
                            self._archive_failed_attempt(
                                state,
                                failure_key,
                                run_dir,
                                RuntimeError(str(state.get("error") or "unvollständiger Versuch")),
                                prior,
                            )
                        classified = None
                        last_error: Optional[BaseException] = None
                        while int(attempts.get(failure_key, 0)) < SEED_ATTEMPTS:
                            if self._cancelled(state):
                                raise InterruptedError
                            self._check_disk_space()
                            self._wait_for_models(state)
                            attempts[failure_key] = int(attempts.get(failure_key, 0)) + 1
                            state["current"] = {
                                "variant": key,
                                "run": run_number,
                                "round": 0,
                                "attempt": attempts[failure_key],
                            }
                            self._save(state)
                            try:
                                classified = self._execute_seed(
                                    state, context, source, ensemble_id, key,
                                    run_number, seed, run_dir,
                                )
                                break
                            except InterruptedError:
                                raise
                            except Exception as error:
                                try:
                                    self._check_models_once(state)
                                except ModelServiceUnavailable as outage:
                                    attempt_n = int(attempts.get(failure_key, 1) or 1)
                                    attempts[failure_key] = max(0, attempt_n - 1)
                                    last_error = outage
                                    state["current_runner_id"] = None
                                    self._archive_failed_attempt(
                                        state, failure_key, run_dir, outage, attempt_n,
                                    )
                                    self._save(state)
                                    continue
                                last_error = error
                                logger.warning(
                                    f"Ensemble {ensemble_id} Seed {key} Lauf {run_number} "
                                    f"Versuch {attempts[failure_key]} fehlgeschlagen: {error}"
                                )
                                state["current_runner_id"] = None
                                self._archive_failed_attempt(
                                    state,
                                    failure_key,
                                    run_dir,
                                    error,
                                    int(attempts.get(failure_key, 1) or 1),
                                )
                                self._save(state)
                        if classified is None:
                            state["attempts_exhausted"] = True
                            attempts[failure_key] = max(
                                int(attempts.get(failure_key, 0) or 0), SEED_ATTEMPTS)
                            self._save(state)
                            raise RuntimeError(
                                f"Seed {key} Lauf {run_number} nach {SEED_ATTEMPTS} Versuchen "
                                f"fehlgeschlagen und gesperrt (attempts_exhausted): {last_error}"
                                + (" – zu wenige Beiträge: min_posts prüfen, nicht zwingend ein Modellfehler"
                                   if "Beiträge" in str(last_error) else "")
                            )
                        run_stats[key].append({
                            "run": run_number,
                            **self._stats_for_run(key, run_dir),
                        })
                        per_run[key].append(classified)
                        variant["done"] = run_number
                        state["current_runner_id"] = None
                        remaining = sum(v["total"] - v["done"] for v in state["variants"])
                        eta = state.get("eta_seconds")
                        if isinstance(eta, (int, float)) and not isinstance(eta, bool):
                            state["eta_seconds"] = max(
                                0, round(eta * remaining / max(1, remaining + 1))
                            )
                        self._save(state)
                    variant["status"] = "completed"
                    self._save(state)

                state["run_stats"] = run_stats
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
    folded = {
        item["id"] for item in state["checklist"] if item.get("collapsed_into")
    }
    primary = state.get("primary_outcome_id")
    primary_text = outcomes.get(primary, {}).get("text_de", primary or "—")
    lines = [
        "## Mehrfachlauf",
        "",
        f"Ausgewertet wurden {state['runs']} Läufe je Variante über jeweils {state['hours']} Stunden"
        + (
            f" (Rundentakt {state['minutes_per_round']} Minuten). "
            if state.get("minutes_per_round")
            else ". "
        ) +
        "Die Anteile sind Anteile der Seeds dieses Aufbaus.",
        f"Primärergebnis (konfirmatorisch): {primary_text}.",
        f"Unklassifizierte Arm-Läufe: {int(state.get('unclassified_runs', 0))}.",
        (
            f"Messbarkeit: {'gegeben' if (state.get('measurement') or {}).get('measurable', True) else 'nicht gegeben'} "
            f"(mindestens {(state.get('measurement') or {}).get('min_classified', state.get('runs', 0))} "
            "klassifizierte Läufe je Ergebnis)."
        ),
        "",
        "| Variante | Ergebnis | Ja / N | Strittig | Unklassifiziert | Anteil (95-%-Wilson-Intervall) |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for variant in state["variants"]:
        key = variant["key"]
        for oid, value in state["results"].get(key, {}).items():
            if oid in folded:
                continue
            outcome = outcomes.get(oid, {"text_de": oid})
            counterparts = [
                outcomes[other]["text_de"]
                for other in outcomes
                if outcomes[other].get("collapsed_into") == oid
            ]
            suffix = f" (mit Gegenstück: {'; '.join(counterparts)})" if counterparts else ""
            marker = " †" if outcome.get("in_material") else ""
            interval = (
                f"{value['rate']:.1%} ({value['ci_low']:.1%}–{value['ci_high']:.1%})"
                if value.get("rate") is not None
                and value.get("ci_low") is not None
                and value.get("ci_high") is not None
                else "nicht messbar"
            )
            lines.append(
                f"| {labels[key]} | {outcome['text_de']}{suffix}{marker} | {value['yes']} / {value['n']} | "
                f"{value.get('disputed', 0)} | "
                f"{value.get('unclassified', 0)} | "
                f"{interval} |"
            )
    if state.get("run_stats"):
        lines.extend([
            "",
            "### Textmengen je Lauf",
            "",
            "| Variante | Lauf | Beiträge | Zeichen | Stapel | Search | Trend | Fremdinteraktionen |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ])
        for variant in state["variants"]:
            key = variant["key"]
            for row in state["run_stats"].get(key, []):
                lines.append(
                    f"| {labels[key]} | {row.get('run', '—')} | "
                    f"{row.get('post_count', 0)} | {row.get('character_count', 0)} | "
                    f"{row.get('batch_count', 0)} | "
                    f"{row.get('search_action_count', 0)} | "
                    f"{row.get('trend_action_count', 0)} | "
                    f"{row.get('foreign_interaction_count', 0)} |"
                )
    if state.get("reliability"):
        lines.extend([
            "",
            "### Zuverlässigkeit der Doppelbewertung",
            "",
            "| Ergebnis | Übereinstimmung | Cohen's Kappa | Paare | Bewertung |",
            "|---|---:|---:|---:|---|",
        ])
        for oid, metric in state["reliability"].items():
            outcome = outcomes.get(oid, {"text_de": oid})
            agreement = metric.get("agreement")
            agreement_text = (
                "–"
                if isinstance(agreement, bool) or not isinstance(agreement, (int, float))
                else f"{agreement:.1%}"
            )
            lines.append(
                f"| {outcome['text_de']} | {agreement_text} | "
                f"{'–' if metric.get('kappa') is None else format(metric['kappa'], '.2f')} | "
                f"{metric['n_pairs']} | {metric['label']} |"
            )
        if any(value.get("label") == "nicht messbar" for value in state["reliability"].values()):
            lines.extend([
                "",
                "Ergebnisse mit der Bewertung **nicht messbar** werden nicht gedeutet; "
                "zugehörige Variantenvergleiche sind als unzuverlässig markiert.",
            ])
    if state.get("comparisons"):
        lines.extend([
            "",
            "### Unterschiede gegenüber dem Basislauf",
            "",
            "Paartafel über denselben Laufindex: a beide Ja, b nur Basis, c nur Variante, d beide Nein. "
            "Konfirmatorisch ist der exakte McNemar-Test des Primärergebnisses mit gepaartem Wald-Intervall. "
            "Explorative Zeilen tragen Holm-korrigierte p-Werte. Newcombe-Methode 10 ist die Sensitivität "
            "unter unabhängigen Seeds.",
            "",
            "| Variante | Ergebnis | Rolle | Paare (a, b, c, d) | Differenz (gepaartes 95-%-Intervall) | McNemar p | Holm p | Newcombe (Sensitivität) |",
            "|---|---|---|---:|---:|---:|---:|---:|",
        ])
        role_labels = {"confirmatory": "konfirmatorisch", "exploratory": "explorativ"}
        for comparison in state["comparisons"]:
            outcome = outcomes.get(comparison["outcome_id"], {"text_de": comparison["outcome_id"]})
            table = comparison.get("table") or {}
            pairs = (
                f"{table.get('n_pairs', 0)} ({table.get('both_yes', 0)}, "
                f"{table.get('baseline_only', 0)}, {table.get('variant_only', 0)}, "
                f"{table.get('both_no', 0)})"
            )
            if comparison.get("unreliable"):
                diff = "Nicht deuten – unzuverlässige Klassifikation"
            else:
                diff = (
                    f"{comparison['diff']:+.1%} ({comparison['ci_low']:+.1%} bis "
                    f"{comparison['ci_high']:+.1%})"
                )
            holm = comparison.get("holm_p")
            holm_text = "—" if holm is None else f"{holm:.4f}"
            mcnemar = comparison.get("mcnemar_p")
            mcnemar_text = "—" if mcnemar is None else f"{mcnemar:.4f}"
            newcombe = comparison.get("newcombe") or {}
            if "ci_low" in newcombe:
                newcombe_text = f"{newcombe['ci_low']:+.1%} bis {newcombe['ci_high']:+.1%}"
            else:
                newcombe_text = "—"
            lines.append(
                f"| {labels.get(comparison['variant'], comparison['variant'])} | "
                f"{outcome['text_de']} | {role_labels.get(comparison.get('role'), comparison.get('role') or '')} | "
                f"{pairs} | {diff} | {mcnemar_text} | {holm_text} | {newcombe_text} |"
            )
    material = [item for item in state["checklist"] if item.get("in_material")]
    if material:
        lines.extend([
            "",
            "† Diese Ergebnisse stehen inhaltlich bereits im Eingabematerial und sind daher kein unabhängiges Ergebnis:",
        ])
        for item in material:
            lines.append(f"- {item['text_de']}: {item['material_snippet']}")
    null_keys = [key for key in state.get("results", {}) if null_arm(key)]
    if null_keys:
        lines.extend([
            "",
            "Nullarme erzeugen je Seed eine Erzählung ohne Schwarm. "
            "`null_document` und der Alias `null_model` sehen Dokument und Frage. "
            "`null_personas` sieht zusätzlich dieselben Personas und Startbeiträge, "
            "trifft jede Akteursgruppe und zielt auf den Median der Basis-Zeichenlänge. "
            "Interaktion wird in den Nullarmen aus dem Text kodiert. "
            "DB-Kanten stehen getrennt als `mechanism_edges` und sind nicht das Ergebnis. "
            "Jeder Nullmodell-Lauf schreibt `manifest.json` mit Prompt-Hash, Modell, "
            "Temperatur, Seed und Tokenobergrenze.",
        ])
    if any(item["key"] == "blind_feed" for item in state.get("variants", [])):
        lines.extend([
            "",
            "`blind_feed` behält den vollen Aktionskatalog und leert die Beobachtung "
            "fremder Beiträge (leere Empfehlungstabelle, refresh nur eigene Posts). "
            "`isolated` bleibt der Arm mit nur `CREATE_POST` und `DO_NOTHING`.",
        ])
    lines.extend([
        "",
        "### Grenzen",
        "",
        "Die Intervalle quantifizieren Streuung zwischen diesen Seeds, nicht Unsicherheit über die reale Welt. "
        "Das gepaarte Wald-Intervall und der exakte McNemar-Test folgen dem gemeinsamen Seed je Laufindex. "
        "Newcombe-Methode 10 setzt unabhängige Stichproben voraus und ist nur eine Sensitivität. "
        "Gemeinsame Modellfehler, unvollständiges Material und Klassifikationsfehler bleiben bestehen.",
    ])
    return "\n".join(lines) + "\n"
