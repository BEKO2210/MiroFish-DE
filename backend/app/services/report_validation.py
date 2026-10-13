"""
Deterministische Berichtsmethodik, Vorgabe-Abgleich und Lauf-Manifest (V1/V2).

Kein Sprachmodell: Zahlen und Abgleich kommen nur aus Config, DBs und Text.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import subprocess
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger("mirofish.report_validation")

# Berichtssatz (Umformulierung) vs. Eingabematerial — Unit-Tests / Fixtures
MUSTERSTADT_BUERGERENTSCHEID_SATZ = (
    "Die Oppositionsfraktion kündigt einen Bürgerentscheid an, "
    "während der Oberbürgermeister die Entscheidung verteidigt."
)
MUSTERSTADT_MATERIAL_SATZ = (
    "Die Oppositionsfraktion kündigt einen Bürgerentscheid an und sammelt "
    "Unterschriften. Der Oberbürgermeister verteidigt die Entscheidung mit "
    "dem Klimaziel der Stadt."
)

_WORD_RE = re.compile(r"[a-zA-ZäöüÄÖÜß0-9]+", re.UNICODE)
_BLOCKQUOTE_RE = re.compile(r"(?m)^>\s*(.+)$")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_DIGIT_RE = re.compile(r"\d")

# Stoppwörter DE+EN (Vergleich über Inhaltswörter)
STOPWORDS: Set[str] = {
    # deutsch
    "der", "die", "das", "den", "dem", "des", "ein", "eine", "einer", "einem",
    "einen", "eines", "und", "oder", "aber", "doch", "denn", "weil", "wenn",
    "als", "auch", "nur", "noch", "schon", "sehr", "mehr", "viel", "viele",
    "ist", "sind", "war", "waren", "wird", "werden", "wurde", "wurden",
    "hat", "haben", "hatte", "hatten", "sein", "seine", "seiner", "seinem",
    "ihren", "ihre", "ihrer", "ihr", "ihm", "ihn", "sich", "nicht", "kein",
    "keine", "mit", "ohne", "von", "vom", "zu", "zum", "zur", "für", "auf",
    "in", "im", "an", "am", "bei", "nach", "vor", "über", "unter", "aus",
    "durch", "gegen", "um", "bis", "so", "wie", "was", "wer", "wo", "wann",
    "dass", "daß", "ob", "es", "er", "sie", "wir", "ihr", "diese", "dieser",
    "dieses", "diese", "jenes", "sowie", "bzw", "bzw.", "während", "zwischen",
    "dann", "dort", "hier", "da", "also", "etwa", "man", "mal", "via",
    # englisch
    "the", "a", "an", "and", "or", "but", "if", "as", "also", "only", "very",
    "more", "much", "many", "is", "are", "was", "were", "be", "been", "being",
    "has", "have", "had", "do", "does", "did", "not", "no", "with", "without",
    "of", "to", "for", "on", "in", "at", "by", "from", "into", "over", "under",
    "out", "up", "down", "so", "than", "that", "this", "these", "those", "it",
    "its", "he", "she", "we", "they", "them", "their", "his", "her", "our",
    "your", "which", "who", "whom", "when", "where", "what", "while", "during",
    "between", "about", "into", "via", "per",
}

_PROBABILITY_WORDS = {
    "wahrscheinlich", "wahrscheinlichkeit", "möglicherweise", "moeglicherweise",
    "vermutlich", "tendenziell", "prognose", "prognostiziert", "prognostizieren",
    "chance", "risiko", "risiken", "wahrscheinlichkeits", "vermutung",
    "probably", "probability", "likely", "unlikely", "chance", "risk", "risks",
    "forecast", "predicts", "predicted", "prediction", "possibly", "perhaps",
}

CONTENT_OVERLAP_THRESHOLD = 0.7
MIN_CONTENT_WORDS = 4
STEM_LEN = 6


def normalize_words(text: str) -> List[str]:
    """Kleinbuchstaben, nur Wort-Tokens (Umlaute bleiben)."""
    if not text:
        return []
    return [w.lower() for w in _WORD_RE.findall(text)]


def stem_token(word: str) -> str:
    """Einfacher Stamm: erste STEM_LEN Zeichen."""
    return word[:STEM_LEN] if word else word


def content_stems(text: str) -> List[str]:
    """Inhaltswörter: Stoppwörter weg, Stamm = erste 6 Zeichen."""
    return [
        stem_token(w)
        for w in normalize_words(text)
        if w not in STOPWORDS and not w.isdigit()
    ]


def word_ngrams(words: Sequence[str], n: int = 5) -> Set[Tuple[str, ...]]:
    if len(words) < n:
        return set()
    return {tuple(words[i : i + n]) for i in range(len(words) - n + 1)}


def ngram_overlap_ratio(claim: str, source: str, n: int = 5) -> float:
    """Anteil der Claim-n-Gramme, die im Quelltext vorkommen (0..1). Zusatzinfo."""
    cw = normalize_words(claim)
    claim_grams = word_ngrams(cw, n)
    if not claim_grams:
        if not cw:
            return 0.0
        sw = set(normalize_words(source))
        return sum(1 for w in cw if w in sw) / len(cw)
    source_grams = word_ngrams(normalize_words(source), n)
    return sum(1 for g in claim_grams if g in source_grams) / len(claim_grams)


def split_sentences(text: str) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []
    parts = _SENTENCE_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


def _short_snippet(text: str, limit: int = 120) -> str:
    t = re.sub(r"\s+", " ", (text or "").strip())
    if len(t) <= limit:
        return t
    return t[: limit - 1].rstrip() + "…"


def content_overlap_in_window(claim_stems: Sequence[str], window: str) -> float:
    if not claim_stems:
        return 0.0
    window_set = set(content_stems(window))
    if not window_set:
        return 0.0
    hit = sum(1 for s in claim_stems if s in window_set)
    return hit / len(claim_stems)


def best_content_match(
    claim: str,
    source_text: str,
) -> Tuple[float, str]:
    """
    Beste Inhaltswort-Überdeckung von claim gegen Fenster aus 1–2 Sätzen.
    Returns (ratio, snippet).
    """
    claim_stems = content_stems(claim)
    if len(claim_stems) < MIN_CONTENT_WORDS:
        return 0.0, ""
    sentences = split_sentences(source_text)
    if not sentences:
        # gesamter Block als ein Fenster
        ratio = content_overlap_in_window(claim_stems, source_text)
        return ratio, _short_snippet(source_text) if ratio > 0 else ""

    best_ratio = 0.0
    best_snip = ""
    for i, sent in enumerate(sentences):
        windows = [sent]
        if i + 1 < len(sentences):
            windows.append(f"{sent} {sentences[i + 1]}")
        for window in windows:
            ratio = content_overlap_in_window(claim_stems, window)
            if ratio > best_ratio:
                best_ratio = ratio
                best_snip = _short_snippet(window)
    return best_ratio, best_snip


def _norm_claim_key(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().strip('"').strip("'"))


def _strip_md_noise(text: str) -> str:
    t = re.sub(r"(?m)^#{1,6}\s*", "", text or "")
    t = re.sub(r"(?m)^>\s*", "", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"\1", t)
    t = re.sub(r"\*([^*]+)\*", r"\1", t)
    t = re.sub(r"`([^`]+)`", r"\1", t)
    t = re.sub(r"(?m)^[-*]\s+", "", t)
    return t


def _sentence_has_number_or_probability(sentence: str) -> bool:
    if _DIGIT_RE.search(sentence):
        return True
    words = set(normalize_words(sentence))
    return bool(words & _PROBABILITY_WORDS)


def extract_claims(markdown: str) -> List[Dict[str, Any]]:
    """
    Kernaussagen: Blockzitate, fett gesetzte Stellen (≥ 8 Wörter),
    Sätze mit Zahlen/Wahrscheinlichkeitswörtern. Duplikate → count.
    """
    md = markdown or ""
    counts: Counter = Counter()
    display: Dict[str, str] = {}

    def _add(raw: str) -> None:
        t = _norm_claim_key(raw)
        if not t:
            return
        key = t.lower()
        counts[key] += 1
        display.setdefault(key, t)

    for m in _BLOCKQUOTE_RE.finditer(md):
        _add(m.group(1))

    for m in re.finditer(r"\*\*([^*]+)\*\*", md):
        t = m.group(1).strip()
        if len(normalize_words(t)) >= 8:
            _add(t)

    for sent in split_sentences(_strip_md_noise(md)):
        if _sentence_has_number_or_probability(sent) and len(normalize_words(sent)) >= 6:
            _add(sent)

    return [{"claim": display[k], "count": counts[k]} for k in counts]


def find_material_matches(
    report_markdown: str,
    extracted_text: str = "",
    initial_posts: Optional[Sequence[Dict[str, Any]]] = None,
    threshold: float = CONTENT_OVERLAP_THRESHOLD,
    n: int = 5,
) -> List[Dict[str, Any]]:
    """
    Aussagen, die bereits im Material/Startbeitrag stehen:
    ≥ threshold Inhaltswort-Überdeckung (mind. MIN_CONTENT_WORDS) in 1–2 Sätzen.
    5-Gramm-Wert als ngram_overlap (Zusatzinfo).
    """
    sources: List[Tuple[str, str]] = []
    if extracted_text:
        sources.append(("Material", extracted_text))
    posts = list(initial_posts or [])
    for i, post in enumerate(posts):
        content = post.get("content") if isinstance(post, dict) else str(post)
        if content:
            label = "Startbeitrag" if len(posts) == 1 else f"Startbeitrag[{i}]"
            sources.append((label, content))

    matches: List[Dict[str, Any]] = []
    for item in extract_claims(report_markdown):
        claim = item["claim"]
        if len(content_stems(claim)) < MIN_CONTENT_WORDS:
            continue
        best_ratio = 0.0
        best_ngram = 0.0
        best_src = None
        best_snip = ""
        for label, text in sources:
            ratio, snip = best_content_match(claim, text)
            ng = ngram_overlap_ratio(claim, text, n=n)
            if (ratio, ng) > (best_ratio, best_ngram):
                best_ratio, best_ngram = ratio, ng
                best_src, best_snip = label, snip
        if best_src is not None and best_ratio >= threshold:
            matches.append(
                {
                    "claim": claim,
                    "count": item["count"],
                    "source": best_src,
                    "snippet": best_snip,
                    "overlap": round(best_ratio, 3),
                    "ngram_overlap": round(best_ngram, 3),
                }
            )
    return matches


def _table_count(conn: sqlite3.Connection, table: str) -> int:
    try:
        row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
        return int(row[0]) if row else 0
    except sqlite3.Error:
        return 0


def count_platform_activity(sim_dir: str) -> Dict[str, Dict[str, int]]:
    """Beiträge/Aktionen je Plattform aus SQLite (post, comment, trace)."""
    out: Dict[str, Dict[str, int]] = {}
    for platform in ("twitter", "reddit"):
        db_path = os.path.join(sim_dir, f"{platform}_simulation.db")
        stats = {"posts": 0, "comments": 0, "actions": 0}
        if os.path.isfile(db_path):
            try:
                conn = sqlite3.connect(db_path)
                stats["posts"] = _table_count(conn, "post")
                stats["comments"] = _table_count(conn, "comment")
                stats["actions"] = _table_count(conn, "trace")
                conn.close()
            except sqlite3.Error as e:
                logger.warning(f"DB lesen fehlgeschlagen ({platform}): {e}")
        # Fallback: actions.jsonl zählen
        if stats["actions"] == 0:
            jl = os.path.join(sim_dir, platform, "actions.jsonl")
            if os.path.isfile(jl):
                n = 0
                with open(jl, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if obj.get("action_type") or (
                            obj.get("event_type") not in (
                                "round_start",
                                "round_end",
                                "simulation_start",
                                "simulation_end",
                            )
                            and "agent_id" in obj
                        ):
                            n += 1
                stats["actions"] = n
        out[platform] = stats
    return out


def _sha256_file(path: str) -> Optional[str]:
    if not os.path.isfile(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def git_commit_hash() -> Optional[str]:
    try:
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        r = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=3,
        )
        if r.returncode == 0:
            return r.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def _load_json(path: str) -> Dict[str, Any]:
    if not os.path.isfile(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_simulation_dir(simulation_id: str) -> str:
    return os.path.join(Config.UPLOAD_FOLDER, "simulations", simulation_id)


def resolve_project_dir(project_id: str) -> str:
    return os.path.join(Config.UPLOAD_FOLDER, "projects", project_id)


def load_simulation_context(simulation_id: str) -> Dict[str, Any]:
    """Config, State, Projekttext und Manifest für einen Lauf laden."""
    sim_dir = resolve_simulation_dir(simulation_id)
    config = _load_json(os.path.join(sim_dir, "simulation_config.json"))
    state = _load_json(os.path.join(sim_dir, "state.json"))
    run_state = _load_json(os.path.join(sim_dir, "run_state.json"))
    manifest = _load_json(os.path.join(sim_dir, "manifest.json"))
    project_id = state.get("project_id") or ""
    extracted = ""
    if project_id:
        et_path = os.path.join(resolve_project_dir(project_id), "extracted_text.txt")
        if os.path.isfile(et_path):
            with open(et_path, "r", encoding="utf-8") as f:
                extracted = f.read()
    return {
        "sim_dir": sim_dir,
        "config": config,
        "state": state,
        "run_state": run_state,
        "manifest": manifest,
        "project_id": project_id,
        "extracted_text": extracted,
    }


def build_methodology(
    simulation_id: str,
    report_markdown: str = "",
    run_count: int = 1,
) -> Dict[str, Any]:
    """
    Methodik- und Grenzen-Abschnitt als strukturiertes Dict + Markdown.

    Deterministisch aus Simulationsdaten; run_count ist heute immer 1.
    """
    ctx = load_simulation_context(simulation_id)
    config = ctx["config"]
    run_state = ctx["run_state"]
    manifest = ctx["manifest"]
    time_config = config.get("time_config") or {}
    event_config = config.get("event_config") or {}
    agent_configs = config.get("agent_configs") or []

    hours = int(
        run_state.get("total_simulation_hours")
        or time_config.get("total_simulation_hours")
        or 0
    )
    minutes_per_round = int(time_config.get("minutes_per_round") or 60) or 60
    rounds = int(
        run_state.get("total_rounds")
        or (hours * 60 // minutes_per_round if hours else 0)
    )
    type_counts = Counter(
        (a.get("entity_type") or "Unknown") for a in agent_configs if isinstance(a, dict)
    )
    agent_types = [
        {"type": t, "count": c} for t, c in sorted(type_counts.items(), key=lambda x: (-x[1], x[0]))
    ]
    platform_stats = count_platform_activity(ctx["sim_dir"])
    initial_posts = event_config.get("initial_posts") or []
    llm = Config.get_llm_config()
    model_name = llm.get("model") or Config.LLM_MODEL_NAME
    seed = manifest.get("seed")
    if seed is None:
        seed = run_state.get("seed")
    temperature = manifest.get("temperature")
    if temperature is None:
        temperature = float(os.environ.get("OASIS_LLM_TEMPERATURE", "0.7"))

    already_in_material = find_material_matches(
        report_markdown,
        extracted_text=ctx["extracted_text"],
        initial_posts=initial_posts,
    )

    timestamp = (
        run_state.get("completed_at")
        or run_state.get("started_at")
        or datetime.now().isoformat()
    )

    data: Dict[str, Any] = {
        "run_count": run_count,
        "agent_count": len(agent_configs),
        "agent_types": agent_types,
        "simulation_hours": hours,
        "simulation_rounds": rounds,
        "platform_activity": platform_stats,
        "models": {
            "main": model_name,
            "agents": model_name,
        },
        "initial_posts_count": len(initial_posts),
        "seed": seed,
        "temperature": temperature,
        "timestamp": timestamp,
        "already_in_material": already_in_material,
        "disclaimer": (
            "Ein einzelner Lauf zeigt einen möglichen Verlauf, keine Wahrscheinlichkeit."
        ),
    }
    data["markdown"] = format_methodology_markdown(data)
    return data


def format_methodology_markdown(data: Dict[str, Any]) -> str:
    """Ruhiger Methodik-Abschnitt für full_report.md."""
    lines = [
        "## Methodik und Grenzen",
        "",
        data.get(
            "disclaimer",
            "Ein einzelner Lauf zeigt einen möglichen Verlauf, keine Wahrscheinlichkeit.",
        ),
        "",
        f"- **Läufe:** {data.get('run_count', 1)}",
        f"- **Agenten:** {data.get('agent_count', 0)}",
    ]
    types = data.get("agent_types") or []
    if types:
        type_str = ", ".join(f"{t['type']} ({t['count']})" for t in types)
        lines.append(f"- **Agententypen:** {type_str}")
    lines.append(
        f"- **Simulierte Zeit:** {data.get('simulation_hours', 0)} Stunden "
        f"({data.get('simulation_rounds', 0)} Runden)"
    )
    plat = data.get("platform_activity") or {}
    for name in ("twitter", "reddit"):
        s = plat.get(name) or {}
        lines.append(
            f"- **{name.capitalize()}:** {s.get('posts', 0)} Beiträge, "
            f"{s.get('comments', 0)} Kommentare, {s.get('actions', 0)} Aktionen"
        )
    models = data.get("models") or {}
    lines.append(
        f"- **Modelle:** Haupt={models.get('main', '—')}, "
        f"Agenten={models.get('agents', '—')}"
    )
    lines.append(f"- **Startbeiträge:** {data.get('initial_posts_count', 0)}")
    seed = data.get("seed")
    lines.append(f"- **Seed:** {seed if seed is not None else 'nicht gesetzt'}")
    if data.get("temperature") is not None:
        lines.append(f"- **Temperatur:** {data['temperature']}")
    lines.append(f"- **Zeitpunkt:** {data.get('timestamp', '—')}")

    already = data.get("already_in_material") or []
    lines.extend(["", "### Stand bereits im Material", ""])
    if not already:
        lines.append(
            "Keine Kernaussagen mit ≥70 % Inhaltswort-Überdeckung zum Eingabematerial gefunden."
        )
    else:
        for item in already:
            ov = item.get("overlap", 0)
            src = item.get("source", "")
            cnt = item.get("count") or 1
            ng = item.get("ngram_overlap")
            extras = f" ×{cnt}" if cnt > 1 else ""
            if ng is not None:
                extras += f", 5-Gramm {ng:.0%}"
            lines.append(f"- ({ov:.0%} · {src}{extras}) {item.get('claim', '')}")
            snip = item.get("snippet") or ""
            if snip:
                lines.append(f"  Fundstelle: {snip}")
    lines.append("")
    return "\n".join(lines)


def append_methodology_to_markdown(markdown: str, methodology: Dict[str, Any]) -> str:
    md = methodology.get("markdown") or format_methodology_markdown(methodology)
    base = (markdown or "").rstrip()
    # Doppelten Methodik-Abschnitt vermeiden
    if re.search(r"(?m)^##\s+Methodik und Grenzen\s*$", base):
        base = re.sub(
            r"(?ms)\n*##\s+Methodik und Grenzen\s*\n.*$",
            "",
            base,
        ).rstrip()
    return base + "\n\n---\n\n" + md


def build_model_config_dict(
    seed: Optional[int] = None,
    temperature: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    """camel model_config_dict: seed, Temperatur, reasoning_effort für lokale Anbieter."""
    cfg: Dict[str, Any] = {}
    if seed is not None:
        cfg["seed"] = int(seed)
    if temperature is not None:
        cfg["temperature"] = float(temperature)
    provider = os.environ.get("LLM_PROVIDER", "openai").lower()
    if (
        provider in ("ollama", "lmstudio", "local")
        and os.environ.get("LOCAL_LLM_REASONING", "none").lower() != "on"
    ):
        cfg["reasoning_effort"] = "none"
    return cfg or None


def apply_python_seeds(seed: int) -> None:
    """random / numpy / torch (falls vorhanden) setzen."""
    import random

    random.seed(seed)
    try:
        import numpy as np

        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def collect_events(sim_dir: str) -> List[Dict[str, Any]]:
    """Alle Beiträge/Aktionen für events.jsonl."""
    events: List[Dict[str, Any]] = []
    for platform in ("twitter", "reddit"):
        jl = os.path.join(sim_dir, platform, "actions.jsonl")
        if os.path.isfile(jl):
            with open(jl, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if "action_type" not in obj and "agent_id" not in obj:
                        continue
                    args = obj.get("action_args") or {}
                    text = args.get("content") or args.get("prompt") or obj.get("result")
                    events.append(
                        {
                            "timestamp": obj.get("timestamp"),
                            "round": obj.get("round"),
                            "platform": platform,
                            "agent_id": obj.get("agent_id"),
                            "agent_name": obj.get("agent_name"),
                            "action_type": obj.get("action_type"),
                            "text": text,
                        }
                    )
        # SQLite-Posts ergänzen, falls JSONL leer
        db_path = os.path.join(sim_dir, f"{platform}_simulation.db")
        if not os.path.isfile(db_path):
            continue
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            try:
                rows = conn.execute(
                    "SELECT user_id, content, created_at FROM post ORDER BY created_at"
                ).fetchall()
            except sqlite3.Error:
                rows = []
            for row in rows:
                events.append(
                    {
                        "timestamp": row["created_at"],
                        "round": None,
                        "platform": platform,
                        "agent_id": row["user_id"],
                        "agent_name": None,
                        "action_type": "CREATE_POST",
                        "text": row["content"],
                    }
                )
            conn.close()
        except sqlite3.Error:
            pass
    return events


def write_events_jsonl(sim_dir: str, events: Optional[List[Dict[str, Any]]] = None) -> str:
    path = os.path.join(sim_dir, "events.jsonl")
    if events is None:
        events = collect_events(sim_dir)
    with open(path, "w", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return path


def _agent_model_names() -> Dict[str, str]:
    """Hauptmodell und ggf. Reddit-Boost-Modell (wie run_parallel_simulation.create_model)."""
    llm = Config.get_llm_config()
    main = llm.get("model") or Config.LLM_MODEL_NAME
    # create_model: has_boost = bool(LLM_BOOST_API_KEY); reddit = BOOST_MODEL or main
    if os.environ.get("LLM_BOOST_API_KEY"):
        reddit = os.environ.get("LLM_BOOST_MODEL_NAME") or main
    else:
        reddit = main
    return {
        "main": main,
        "twitter": main,
        "reddit": reddit,
        "agents": main,
    }


def build_manifest(
    sim_dir: str,
    seed: int,
    temperature: float,
    started_at: Optional[str] = None,
    completed_at: Optional[str] = None,
    action_count: Optional[int] = None,
) -> Dict[str, Any]:
    """Manifest aus dem Ordner bauen, in dem simulation_config.json liegt."""
    sim_dir = os.path.abspath(sim_dir)
    config = _load_json(os.path.join(sim_dir, "simulation_config.json"))
    state = _load_json(os.path.join(sim_dir, "state.json"))
    project_id = state.get("project_id") or ""
    simulation_id = (
        config.get("simulation_id")
        or state.get("simulation_id")
        or os.path.basename(sim_dir.rstrip(os.sep))
    )
    requirement = (
        state.get("simulation_requirement")
        or config.get("simulation_requirement")
        or ""
    )
    doc_hashes: Dict[str, str] = {}
    if project_id:
        files_dir = os.path.join(resolve_project_dir(project_id), "files")
        if os.path.isdir(files_dir):
            for name in sorted(os.listdir(files_dir)):
                fp = os.path.join(files_dir, name)
                if os.path.isfile(fp):
                    digest = _sha256_file(fp)
                    if digest:
                        doc_hashes[name] = digest
        et = os.path.join(resolve_project_dir(project_id), "extracted_text.txt")
        digest = _sha256_file(et)
        if digest:
            doc_hashes["extracted_text.txt"] = digest

    config_path = os.path.join(sim_dir, "simulation_config.json")
    config_hash = _sha256_file(config_path)
    profile_hashes: Dict[str, str] = {}
    for name in ("twitter_profiles.csv", "reddit_profiles.json"):
        digest = _sha256_file(os.path.join(sim_dir, name))
        if digest:
            profile_hashes[name] = digest
    initial_posts = (config.get("event_config") or {}).get("initial_posts") or []
    initial_posts_hash = _sha256_text(
        json.dumps(initial_posts, ensure_ascii=False, sort_keys=True)
    )

    if action_count is None:
        plat = count_platform_activity(sim_dir)
        action_count = sum(p.get("actions", 0) for p in plat.values())

    time_config = config.get("time_config") or {}
    minutes_per_round = int(time_config.get("minutes_per_round") or 60) or 60

    return {
        "simulation_id": simulation_id,
        "seed": int(seed),
        "temperature": float(temperature),
        "models": _agent_model_names(),
        "document_sha256": doc_hashes,
        "profile_sha256": profile_hashes,
        "initial_posts_sha256": initial_posts_hash,
        "question_sha256": _sha256_text(requirement),
        "simulation_config_sha256": config_hash,
        "minutes_per_round": minutes_per_round,
        "git_commit": git_commit_hash(),
        "started_at": started_at or datetime.now().isoformat(),
        "completed_at": completed_at,
        "action_count": action_count,
    }


def write_manifest(sim_dir: str, manifest: Dict[str, Any]) -> str:
    path = os.path.join(sim_dir, "manifest.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return path


def update_manifest_completion(sim_dir: str, action_count: Optional[int] = None) -> None:
    path = os.path.join(sim_dir, "manifest.json")
    if not os.path.isfile(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["completed_at"] = datetime.now().isoformat()
    if action_count is None:
        plat = count_platform_activity(sim_dir)
        action_count = sum(p.get("actions", 0) for p in plat.values())
    data["action_count"] = action_count
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
