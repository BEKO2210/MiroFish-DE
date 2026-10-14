#!/usr/bin/env python3
"""Dokumentierte Realfälle blind simulieren und fallweise auswerten."""
from __future__ import annotations

import argparse
import copy
import json
import math
import os
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

import requests

QUESTION = ("Wie reagieren Bürgerinnen, Vereine, Medien und Politik in den ersten zwei "
            "Wochen nach der Bekanntgabe?")
ALLOWED_ARMS = ("baseline", "null_document", "null_personas", "isolated")
DEFAULT_ARMS = ("baseline", "null_document", "null_personas")
ALLOWED_MINUTES_PER_ROUND = (60, 120, 240)
ARM_LABELS = {"baseline": "Schwarm (S)", "null_document": "Dokument-Nullmodell (D)",
              "null_personas": "Persona-Nullmodell (P)", "isolated": "Isoliert"}
TERMINAL_ENSEMBLE_STATUSES = {"completed", "failed", "cancelled"}
BOOTSTRAP_SEED, BOOTSTRAP_SAMPLES = 20261014, 10_000
ENSEMBLE_RESUME_ATTEMPTS = 2
CALIBRATION_MIN_CASES = 25
CALIBRATION_PILOT_NOTE = "Pilot, keine Kalibrierungsaussage"
KAPPA_INSTRUMENT_STATUS = "nicht bestanden (Instrument unzuverlässig)"
PILOT_RULE_INTRO = (
    "Festgeschrieben am 14.10.2026 vor jedem Lauf (gerichtete Regel). Im Pilot (unter 25 gewerteten "
    "Fällen) gilt die Aussage nur als bestanden, wenn gleichzeitig alle vier Bedingungen erfüllt sind:")
PILOT_RULE_CONDITIONS = (
    "1. das 95-%-Fall-Bootstrap-Intervall von `Skill(S,D) = 1 − BS_S / BS_D` liegt vollständig über 0;",
    "2. das 95-%-Fall-Bootstrap-Intervall von `Skill(S,P) = 1 − BS_S / BS_P` liegt vollständig über 0 "
    "(S ist im Brier-Sinn genauer als P; ein bloß von 0 verschiedener Abstand der Ja-Anteile genügt nicht);",
    "3. Kappa beträgt für jedes gewertete Primärergebnis mindestens 0,6 (die KI-Zweitkodierung der "
    "realen Akte liefert 1,0, ersetzt aber keine menschliche Zweitkodierung);",
    "4. alle 7 Fälle des Rahmens sind gewertet (Fallmenge exakt wie im Rahmen, ein gültiger Lauf je Fall, "
    "Messbarkeit mindestens 4 von 5 klassifizierte Läufe je Arm).",
)
PILOT_RULE_CLOSING = (
    "Liegt das Intervall von `Skill(S,D)` vollständig unter 0, lautet der Status „nicht bestanden“, "
    "auch wenn andere Größen fehlen. Ist eine andere prüfbare Bedingung verletzt (insbesondere Intervall "
    "von `Skill(S,P)` nicht ganz über 0 oder Kappa unter 0,6), lautet das Urteil „nicht bestanden“. "
    "Fehlt eine Größe, ist die Fallmenge nicht exakt die des Rahmens oder ist das Instrument nicht "
    "prüfbar (degeneriertes Kappa ohne Varianz, Fälle nicht messbar), lautet das Urteil „nicht prüfbar“. "
    "„bestanden“ wird nicht nachträglich aufgeweicht. Wird mindestens ein Primärergebnis wegen Kappa "
    "unter 0,6 aus der Wertung genommen, zählt `GESAMT` diese Fälle mit Anteil; ist der Anteil größer "
    "als 0, lautet das Pilot-Urteil „nicht bestanden (Instrument unzuverlässig)“. Ein nicht definiertes "
    "Kappa wegen fehlender Varianz ist davon ausgenommen und führt zu „nicht prüfbar“ (siehe Kodierbuch, "
    "degeneriertes Kappa). Die Kalibrierungssteigung wird nur ausgewiesen, mit dem festen Hinweis "
    "„Pilot, keine Kalibrierungsaussage“, und ist kein Bestehenskriterium.")
DECISION_RULE_PILOT = "\n".join([PILOT_RULE_INTRO, *PILOT_RULE_CONDITIONS, PILOT_RULE_CLOSING])
DECISION_RULE_CONFIRMATORY = (
    "Ab 25 gewerteten Fällen (konfirmatorische Studie, eigener Rahmen) gelten dieselben Bedingungen 1 bis 3, "
    "Bedingung 4 mit der Fallmenge des dann festgeschriebenen Rahmens, und zusätzlich liegt die "
    "Kalibrierungssteigung von S im Intervall [0,5; 1,5].")
NOT_TESTABLE = "nicht prüfbar"
PROBE_STATUS = "Probelauf, nicht gewertet"
PROBE_CASE_ID = "probe"
PILOT_V5_FRAME = {
    "id": "pilot-v5",
    "status": "vorgeschlagen, Start erst nach Freigabe des Projektinhabers",
    "cases": 7,
    "arms": ["baseline", "null_document", "null_personas"],
    "seeds": 5,
    "minutes_per_round": 240,
    "hours": 336,
    "gpu_hours_low": 33,
    "gpu_hours_high": 72,
    "gpu_hours_mid": 50,
    "case_ids": [
        "karlsfeld-hallenbad-2023", "kehl-tram-baumfaellungen-2017", "kuppenheim-cuppamare-2024",
        "neuwied-parkgebuehren-2025", "niederkassel-buecherei-2023", "unterschleissheim-wall-2022",
        "wanzleben-grundschule-2025"],
    "models": {
        "agent_model": "gemma4:e4b-it-qat", "arms_s_d_p": "agent_model",
        "classification_main": "gemma4:12b-it-qat", "classification_second": "qwen3.5:9b",
        "seed_fallback": False,
        "cold_question_models": ["gemma4:e4b-it-qat", "gemma4:12b-it-qat"]},
    "probelauf": {"case": "synthetisch, nicht gewertet", "seeds": 2},
    "min_classified_per_arm": 4,
    "valid_runs_per_case": 1,
    "decision_date": "2026-10-14",
}
PROBE_V5_FRAME = {
    **{key: value for key, value in PILOT_V5_FRAME.items() if key not in {"probelauf", "decision_date"}},
    "id": "probe-v5", "status": PROBE_STATUS, "cases": 1, "seeds": 2,
    "case_ids": [PROBE_CASE_ID], "min_classified_per_arm": 1,
    "gpu_hours_low": 0, "gpu_hours_high": 0, "gpu_hours_mid": 0,
}
TRANSIENT_RETRY_SECONDS = 30 * 60
TRANSIENT_BACKOFF_START, TRANSIENT_BACKOFF_CAP = 5.0, 300.0
CONTAMINATION_MIN_WEAK_HITS = 3
CONTAMINATION_MAX_TOKENS = 600
METRICS_NOTE = "Sammel-Brier über alle messbaren Ergebnisse, nicht zitierfähig"
_HORIZON_WORDS = {
    "ein": 1, "eine": 1, "einen": 1, "zwei": 2, "drei": 3, "vier": 4, "fünf": 5,
    "fuenf": 5, "sechs": 6, "sieben": 7, "acht": 8, "neun": 9, "zehn": 10,
    "elf": 11, "zwölf": 12, "zwoelf": 12, "vierzehn": 14,
}
_HORIZON_HOURS = {
    "tag": 24, "tage": 24, "tagen": 24,
    "woche": 168, "wochen": 168,
    "monat": 720, "monate": 720, "monaten": 720,
}
_HORIZON_RE = re.compile(
    r"(?i)(?<!\w)(\d+|ein|eine|einen|zwei|drei|vier|fünf|fuenf|sechs|sieben|acht|neun|zehn|"
    r"elf|zwölf|zwoelf|vierzehn)\s+(tag|tage|tagen|woche|wochen|monat|monate|monaten)\b"
)
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS_DIR = REPOSITORY_ROOT / "docs" / "validation" / "ergebnisse"
PROBE_DIR = REPOSITORY_ROOT / "docs" / "validation" / PROBE_CASE_ID


class ApiError(RuntimeError):
    pass


class TransientApiError(ApiError):
    """HTTP 5xx des Backends: technischer Ausfall, kein inhaltlicher Fehler."""


class ApiClient:
    """HTTP-Client. GET und als wiederholbar markierte POSTs fangen transiente Fehler
    (ConnectionError, Timeout, HTTP 5xx) mit Backoff bis zu `retry_seconds` ab."""

    def __init__(self, base: str, session: Any = None, *,
                 sleep: Callable[[float], None] = time.sleep,
                 retry_seconds: float = TRANSIENT_RETRY_SECONDS,
                 log: Optional[Callable[[str], None]] = None) -> None:
        self.base, self.session = base.rstrip("/"), session or requests.Session()
        token = os.environ.get("API_TOKEN", "").strip()
        headers = getattr(self.session, "headers", None)
        if token and headers is not None:
            headers["Authorization"] = f"Bearer {token}"
        self.sleep, self.retry_seconds, self.log = sleep, retry_seconds, log

    @staticmethod
    def _unwrap(response: Any, *, allow_list: bool = False) -> Any:
        if response.status_code >= 500:
            raise TransientApiError(f"HTTP {response.status_code}: "
                                    f"{str(getattr(response, 'text', ''))[:200]}")
        try:
            payload = response.json()
        except (TypeError, ValueError) as error:
            raise ApiError(f"Antwort ist kein JSON (HTTP {response.status_code}): "
                           f"{str(getattr(response, 'text', ''))[:200]}") from error
        if response.status_code >= 400 or not payload.get("success", True):
            raise ApiError(str(payload.get("error") or f"HTTP {response.status_code}"))
        data = payload.get("data", payload)
        if not (isinstance(data, dict) or (allow_list and isinstance(data, list))):
            raise ApiError("API-Antwort enthält kein Datenobjekt")
        return data

    def _with_retry(self, call: Callable[[], Any]) -> Any:
        waited, delay = 0.0, TRANSIENT_BACKOFF_START
        while True:
            try:
                return call()
            except (requests.ConnectionError, requests.Timeout, TransientApiError) as error:
                if waited + delay > self.retry_seconds:
                    raise
                if self.log:
                    self.log(f"Transienter Fehler ({type(error).__name__}: {str(error)[:120]}), "
                             f"neuer Versuch in {delay:.0f} s ({waited:.0f} von {self.retry_seconds:.0f} s)")
                self.sleep(delay)
                waited += delay
                delay = min(delay * 2, TRANSIENT_BACKOFF_CAP)

    def get(self, path: str, *, timeout: int = 30, allow_list: bool = False) -> Any:
        return self._with_retry(lambda: self._unwrap(
            self.session.get(f"{self.base}{path}", timeout=timeout), allow_list=allow_list))

    def post(self, path: str, *, json_body: Optional[Dict[str, Any]] = None,
             data: Optional[Dict[str, Any]] = None, files: Any = None,
             timeout: int = 60, retry: bool = False) -> Dict[str, Any]:
        def call() -> Dict[str, Any]:
            return self._unwrap(self.session.post(f"{self.base}{path}", json=json_body,
                                                  data=data, files=files, timeout=timeout))
        # Nicht idempotente POSTs (Start, Upload) werden nicht blind wiederholt.
        return self._with_retry(call) if retry else call()


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
    missing = [name for name in ("ausgangslage.md", "verlauf.md", "ergebnisse.json")
               if not (case_dir / name).is_file()]
    if missing:
        raise ValueError("Im Fallordner fehlen: " + ", ".join(missing))


def load_outcomes(case_dir: Path) -> List[Dict[str, Any]]:
    outcomes = _load_json(case_dir / "ergebnisse.json")
    if not isinstance(outcomes, list) or not outcomes:
        raise ValueError("ergebnisse.json muss eine nicht-leere Liste sein")
    seen, primary_count = set(), 0
    for index, outcome in enumerate(outcomes):
        if not isinstance(outcome, dict):
            raise ValueError(f"ergebnisse.json[{index}] ist kein Objekt")
        text, actual, primary = str(outcome.get("text_de") or "").strip(), outcome.get("eingetreten"), outcome.get("primaer", False)
        if not text or len(text) > 200:
            raise ValueError(f"Ungültiger text_de in ergebnisse.json[{index}]")
        if text in seen:
            raise ValueError(f"Doppelte Ergebnisfrage: {text}")
        if not isinstance(actual, bool):
            raise ValueError(f"eingetreten in ergebnisse.json[{index}] muss boolesch sein")
        if not isinstance(primary, bool):
            raise ValueError(f"primaer in ergebnisse.json[{index}] muss boolesch sein")
        seen.add(text)
        primary_count += int(primary)
    if primary_count != 1:
        raise ValueError("ergebnisse.json muss genau eine Frage mit primaer: true enthalten")
    return outcomes


def case_annotations(outcomes: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Vorab-Kontamination und Quellenlücke aus den Frageobjekten, nicht aus dem Ordnernamen."""
    kontaminiert = None
    quellenluecke = False
    for index, outcome in enumerate(outcomes):
        if "quellenluecke" in outcome and not isinstance(outcome.get("quellenluecke"), bool):
            raise ValueError(f"quellenluecke in ergebnisse.json[{index}] muss boolesch sein")
        quellenluecke = quellenluecke or outcome.get("quellenluecke") is True
        if "kontaminiert" not in outcome or outcome.get("kontaminiert") in (None, False):
            continue
        flag = outcome.get("kontaminiert")
        if not isinstance(flag, dict):
            raise ValueError(
                f"kontaminiert in ergebnisse.json[{index}] muss ein Objekt mit quelle und datum sein")
        quelle = str(flag.get("quelle") or "").strip()
        datum = str(flag.get("datum") or "").strip()
        if not quelle or not datum:
            raise ValueError(f"kontaminiert in ergebnisse.json[{index}] braucht quelle und datum")
        parsed = {"quelle": quelle, "datum": datum}
        if kontaminiert and kontaminiert != parsed:
            raise ValueError("kontaminiert ist mehrfach und widersprüchlich gesetzt")
        kontaminiert = parsed
    return {"kontaminiert": kontaminiert, "quellenluecke": quellenluecke}


def validate_minutes_per_round(minutes: Any, hours: int) -> int:
    if isinstance(minutes, bool) or not isinstance(minutes, int) or minutes not in ALLOWED_MINUTES_PER_ROUND:
        raise ValueError("minutes_per_round muss 60, 120 oder 240 sein")
    if (hours * 60) % minutes:
        raise ValueError(
            f"hours ({hours}) muss durch minutes_per_round/60 ({minutes // 60}) teilbar sein; "
            "sonst würden Stunden abgeschnitten")
    return minutes


def blind_custom_outcomes(outcomes: Sequence[Dict[str, Any]]) -> List[Dict[str, str]]:
    blinded = []
    for outcome in outcomes:
        item = {"text_de": str(outcome["text_de"]).strip()}
        polarity = str(outcome.get("polarity") or "").strip().lower()
        if polarity in {"presence", "absence"}:
            item["polarity"] = polarity
        blinded.append(item)
    return blinded


def outcome_horizon_hours(outcome: Dict[str, Any]) -> Optional[int]:
    """Längstes im Fragetext oder Zeitfenster genanntes Fenster, in Stunden."""
    found = []
    for key in ("zeitfenster", "text_de"):
        for match in _HORIZON_RE.finditer(str(outcome.get(key) or "")):
            raw = match.group(1).casefold()
            number = int(raw) if raw.isdigit() else _HORIZON_WORDS[raw]
            found.append(number * _HORIZON_HOURS[match.group(2).casefold()])
    return max(found) if found else None


def beyond_simulated_horizon(outcome: Dict[str, Any], hours: int) -> bool:
    horizon = outcome_horizon_hours(outcome)
    return horizon is not None and horizon > hours


def parse_arms(value: Any) -> List[str]:
    arms = [item.strip() for item in value.split(",")] if isinstance(value, str) else list(value)
    if not arms or any(not arm for arm in arms):
        raise ValueError("--arms muss mindestens einen Arm enthalten")
    if len(set(arms)) != len(arms):
        raise ValueError("--arms enthält einen Arm mehrfach")
    unknown = [arm for arm in arms if arm not in ALLOWED_ARMS]
    if unknown:
        raise ValueError("Unbekannte Arme: " + ", ".join(unknown) + ". Erlaubt: " + ", ".join(ALLOWED_ARMS))
    return arms


def primary_outcome_id(outcomes: Sequence[Dict[str, Any]]) -> Optional[str]:
    return next((f"c{index}" for index, item in enumerate(outcomes, 1) if item.get("primaer") is True), None)


def cold_case_label(outcomes: Sequence[Dict[str, Any]], *, location: Optional[str] = None,
                    year: Optional[str] = None) -> str:
    """Echter Ort und Jahr für die Echtfall-Frage. Nie der Ordnername."""
    if location is not None and str(location).strip():
        label = str(location).strip()
        if year is not None and str(year).strip():
            label = f"{label} {str(year).strip()}"
        return label
    found = []
    for index, outcome in enumerate(outcomes):
        if "kaltfrage_ort" not in outcome:
            continue
        value = outcome.get("kaltfrage_ort")
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"kaltfrage_ort in ergebnisse.json[{index}] muss ein nicht-leerer Text sein")
        found.append(value.strip())
    unique = set(found)
    if len(unique) > 1:
        raise ValueError("kaltfrage_ort ist widersprüchlich gesetzt")
    if not unique:
        raise ValueError(
            "Kaltfrage braucht kaltfrage_ort in ergebnisse.json oder --ort; "
            "der Ordnername wird nicht an das Modell gesendet")
    return unique.pop()


FREE_TEXT_QUESTION = (
    "Was geschah nach diesem Beschluss? Welche Akteure äußerten sich, und an welchen Daten? "
    "Antworte in wenigen Sätzen. Wenn du den Fall nicht kennst, schreibe das ausdrücklich "
    "und erfinde nichts.")
_DATE_RE = re.compile(r"\b\d{1,2}\.\d{1,2}\.(?:\d{4}|\d{2})?(?!\d)")
_NUMBER_RE = re.compile(r"\b\d{2,}\b")
_ACRONYM_RE = re.compile(r"\b[A-ZÄÖÜ]{3,}\b")
_LONG_WORD_RE = re.compile(r"\b[^\W\d_]{8,}\b")


def case_topic(case_dir: Path, topic: Optional[str] = None) -> Optional[str]:
    """Thema der Maßnahme: --thema, sonst die Überschrift von ausgangslage.md (anonymisiert)."""
    if topic and str(topic).strip():
        return str(topic).strip()
    for line in (case_dir / "ausgangslage.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            heading = line.lstrip("# ").strip()
            heading = re.sub(r"(?i)^ausgangslage:\s*", "", heading)
            return heading or None
    return None


def _contamination_prompt(case_label: str, material: Optional[str],
                          topic: Optional[str] = None) -> List[tuple]:
    topic_line = f"Thema der Maßnahme: {topic}\n" if topic else ""
    prompts = [("identity",
                "Kennst du den folgenden realen kommunalpolitischen Fall aus deinem Vorwissen? "
                "Nutze keine Werkzeuge und recherchiere nicht.\n"
                f"Fall: {case_label}\n{topic_line}"
                f"{FREE_TEXT_QUESTION}")]
    if material is not None:
        prompts.append(("material",
                        "Kennst du den realen kommunalpolitischen Fall, der in dem folgenden Bogen "
                        "beschrieben wird, aus deinem Vorwissen? Der Text ist der Wortlaut, den die "
                        "Simulation sieht. Nutze keine Werkzeuge und recherchiere nicht.\n"
                        f"{material}\n{FREE_TEXT_QUESTION}"))
    return prompts


def hidden_terms(outcomes: Sequence[Dict[str, Any]], visible_text: str) -> Dict[str, List[str]]:
    """Stichworte der versteckten Fakten (Datum, Zahl, Kürzel, lange Wörter) aus ergebnisse.json,
    soweit sie nicht schon im sichtbaren Text stehen. Nichts davon wird an ein Modell gesendet."""
    visible = visible_text.casefold()
    source = "\n".join(f"{item.get('text_de') or ''}\n{item.get('quelle') or ''}" for item in outcomes)
    dates = {match.group(0).replace(" ", "") for match in _DATE_RE.finditer(source)}
    rest = _DATE_RE.sub(" ", source)
    strong = {term for term in dates | set(_NUMBER_RE.findall(rest)) | set(_ACRONYM_RE.findall(rest))
              if term.casefold() not in visible}
    weak = {word.casefold() for word in _LONG_WORD_RE.findall(rest) if word.casefold() not in visible}
    weak -= {term.casefold() for term in strong}
    return {"strong": sorted(strong), "weak": sorted(weak)}


def contamination_hits(answer: str, terms: Dict[str, List[str]]) -> Dict[str, Any]:
    """Lokaler Stichwortabgleich: ein starker Treffer oder drei schwache gelten als Treffer des Ausgangs."""
    text = answer.replace(" ", "")
    spaced = answer.casefold()
    strong = [term for term in terms["strong"]
              if (term in text if _DATE_RE.fullmatch(term)
                  else re.search(rf"(?<!\w){re.escape(term)}(?!\w)", answer))]
    weak = [term for term in terms["weak"] if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", spaced)]
    return {"strong_hits": strong, "weak_hits": weak,
            "known": bool(strong) or len(weak) >= CONTAMINATION_MIN_WEAK_HITS}


def check_contamination(case_label: str, llm: Any = None,
                        *, material: Optional[str] = None,
                        forbidden: Optional[str] = None, topic: Optional[str] = None,
                        models: Optional[Sequence[str]] = None,
                        hidden_outcomes: Sequence[Dict[str, Any]] = ()) -> Dict[str, Any]:
    """Freitext-Abruf des Falls bei jedem Modell, lokal gegen die versteckten Fakten abgeglichen.
    `llm` ist ein Aufrufbar (Modell, Prompt) -> Text; ohne Angabe wird der LLMClient genutzt."""
    chosen = list(models) if models else [None]
    prompts = _contamination_prompt(case_label, material, topic)
    if forbidden:
        for _, prompt in prompts:
            if forbidden in prompt:
                raise ValueError("Der Ordnername darf nicht an das Modell gesendet werden")
    probes: List[Dict[str, Any]] = []
    try:
        for model in chosen:
            if llm is not None:
                ask = lambda prompt, model=model: str(llm(model, prompt))
            else:
                from app.utils.llm_client import LLMClient
                client = LLMClient(model=model) if model else LLMClient()
                ask = lambda prompt, client=client: str(client.chat(
                    [{"role": "system", "content": "Prüfe nur vorhandenes Fallwissen."},
                     {"role": "user", "content": prompt}],
                    temperature=0, max_tokens=CONTAMINATION_MAX_TOKENS, seed=BOOTSTRAP_SEED))
            for kind, prompt in prompts:
                answer = ask(prompt)
                terms = hidden_terms(hidden_outcomes, f"{material or ''}\n{prompt}")
                probes.append({"model": model or "configured-main-model", "kind": kind,
                               "prompt": prompt, "answer": answer,
                               "checked_at": datetime.now(timezone.utc).isoformat(),
                               **contamination_hits(answer, terms)})
    except (ApiError, ValueError):
        raise
    except Exception as error:
        raise ApiError(f"Kaltabruf fehlgeschlagen: {error}") from error
    identity_known = any(item["known"] for item in probes if item["kind"] == "identity")
    material_known = (any(item["known"] for item in probes if item["kind"] == "material")
                      if material is not None else None)
    first = {kind: next(item for item in probes if item["kind"] == kind) for kind, _ in prompts}
    return {"checked_at": datetime.now(timezone.utc).isoformat(),
            "model": ", ".join(dict.fromkeys(item["model"] for item in probes)),
            "models": list(dict.fromkeys(item["model"] for item in probes)),
            "identity": {"kaltfrage_ort": case_label}, "known": identity_known or bool(material_known),
            "identity_known": identity_known, "material_known": material_known,
            "answer": first["identity"]["answer"],
            "material_answer": first["material"]["answer"] if material is not None else None,
            "probes": probes}


def _new_state(case_name: str, base: str, runs: int, hours: int, arms: Sequence[str],
               minutes_per_round: int = 60) -> Dict[str, Any]:
    return {"case": case_name, "base": base.rstrip("/"), "runs": runs, "hours": hours,
            "minutes_per_round": minutes_per_round, "arms": list(arms), "question": QUESTION,
            "contamination_check": None,
            "project_id": None, "graph_task_id": None, "graph_id": None,
            "simulation_id": None, "prepare_task_id": None, "prepared": False,
            "ensemble_id": None, "ensemble_completed": False, "ensemble_ids": [],
            "updated_at": datetime.now(timezone.utc).isoformat()}


def _save_state(path: Path, state: Dict[str, Any]) -> None:
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    _write_json_atomic(path, state)


def load_or_create_state(path: Path, case_name: str, base: str, runs: int, hours: int,
                         arms: Sequence[str] = DEFAULT_ARMS,
                         minutes_per_round: int = 60) -> Dict[str, Any]:
    if not path.is_file():
        state = _new_state(case_name, base, runs, hours, arms, minutes_per_round)
        _save_state(path, state)
        return state
    state = _load_json(path)
    expected = {"case": case_name, "base": base.rstrip("/"), "runs": runs, "hours": hours,
                "minutes_per_round": minutes_per_round, "arms": list(arms), "question": QUESTION}
    conflicts = [key for key, value in expected.items() if state.get(key) != value]
    if conflicts:
        raise ValueError("Vorhandener Resume-State passt nicht zu diesem Aufruf: " + ", ".join(conflicts))
    return state


def prepare_simulation(client: ApiClient, case_dir: Path, state_path: Path, state: Dict[str, Any],
                       *, sleep: Callable[[float], None] = time.sleep, poll_interval: float = 5.0) -> None:
    source = case_dir / "ausgangslage.md"
    if not state.get("project_id"):
        with source.open("rb") as handle:
            data = client.post("/api/graph/ontology/generate",
                               files={"files": (source.name, handle, "text/markdown")},
                               data={"simulation_requirement": QUESTION,
                                     "project_name": "Realitätsabgleich"}, timeout=3600)
        state["project_id"] = data["project_id"]
        _save_state(state_path, state)
    if not state.get("graph_id"):
        if not state.get("graph_task_id"):
            task = client.post("/api/graph/build", json_body={"project_id": state["project_id"], "force": True})
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
        state["simulation_id"] = client.post("/api/simulation/create",
                                              json_body={"project_id": state["project_id"]})["simulation_id"]
        _save_state(state_path, state)
    if not state.get("prepared"):
        if not state.get("prepare_task_id"):
            prepared = client.post("/api/simulation/prepare",
                                   json_body={"simulation_id": state["simulation_id"], "parallel_profile_count": 1},
                                   retry=True)
            state["prepare_task_id"] = prepared.get("task_id")
            state["prepared"] = bool(prepared.get("already_prepared"))
            _save_state(state_path, state)
        while not state.get("prepared"):
            status = client.post("/api/simulation/prepare/status",
                                 json_body={"simulation_id": state["simulation_id"],
                                            "task_id": state.get("prepare_task_id")}, timeout=30,
                                 retry=True)
            value = status.get("status") or status.get("simulation_status")
            if value in {"ready", "completed"} or status.get("already_prepared") or status.get("is_ready"):
                state["prepared"] = True
                _save_state(state_path, state)
            elif value in {"failed", "error"}:
                raise ApiError(str(status.get("error") or "Vorbereitung fehlgeschlagen"))
            else:
                sleep(poll_interval)


def _ensemble_attempts_exhausted(ensemble: Dict[str, Any]) -> bool:
    """True, wenn der Seed-Zähler ausgereizt ist und ein weiteres Resume nichts mehr versucht."""
    if ensemble.get("attempts_exhausted") is True:
        return True
    error = str(ensemble.get("error") or "")
    if "Versuche erschöpft" in error or "Versuchen fehlgeschlagen" in error:
        return True
    attempts = ensemble.get("seed_attempts") or {}
    if not isinstance(attempts, dict) or not attempts:
        return False
    for value in attempts.values():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) < 3:
            return False
    return True


def ensemble_start_options(rahmen: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Startparameter nur aus dem Rahmen: Textmodell, strenger Zweitbewerter, Mindestzahl klassifizierter Läufe."""
    if not rahmen:
        return {}
    options: Dict[str, Any] = {}
    models = rahmen.get("models") or {}
    if models.get("agent_model"):
        options["text_model"] = models["agent_model"]
        # Der Dienst unterscheidet das Agentenmodell des Schwarms (`text_model`)
        # vom Textmodell der Nullarme (`arm_model`). Im V5-Rahmen müssen S, D und
        # P ausdrücklich dasselbe Modell verwenden.
        options["arm_model"] = models["agent_model"]
    if models.get("seed_fallback") is False:
        options["strict_second_rater"] = True
    if isinstance(rahmen.get("min_classified_per_arm"), int):
        options["min_classified"] = rahmen["min_classified_per_arm"]
    return options


def run_ensemble(client: ApiClient, outcomes: Sequence[Dict[str, Any]], state_path: Path,
                 state: Dict[str, Any], *, rahmen: Optional[Dict[str, Any]] = None,
                 sleep: Callable[[float], None] = time.sleep,
                 poll_interval: float = 15.0,
                 progress: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
    if not state.get("ensemble_id"):
        body = {"simulation_id": state["simulation_id"], "variants": list(state["arms"]),
                "runs": state["runs"], "hours": state["hours"],
                "minutes_per_round": state["minutes_per_round"],
                "custom_outcomes": blind_custom_outcomes(outcomes)}
        body.update(ensemble_start_options(rahmen))
        primary_id = primary_outcome_id(outcomes)
        if primary_id:
            body["primary_outcome_id"] = primary_id
        try:
            started = client.post("/api/ensemble/start", json_body=body, timeout=120)
        except ApiError as error:
            if {"null_document", "null_personas"}.intersection(state["arms"]):
                raise ApiError("Das Backend kennt die V5-Arme null_document/null_personas noch nicht. "
                               "Bitte Backend und Fall-Werkzeug gemeinsam aktualisieren. "
                               f"Backend-Antwort: {error}") from error
            raise
        state["ensemble_id"] = started["ensemble_id"]
        state.setdefault("ensemble_ids", []).append(
            {"ensemble_id": started["ensemble_id"], "started_at": datetime.now(timezone.utc).isoformat(),
             "grund": "Start"})
        _save_state(state_path, state)
    resumes = int(state.get("ensemble_resumes") or 0)
    last_line = None
    while True:
        ensemble = client.get(f"/api/ensemble/{state['ensemble_id']}")
        status = ensemble.get("status")
        if progress:
            done = ", ".join(f"{item.get('key')} {item.get('done')}/{item.get('total')}"
                             for item in ensemble.get("variants") or [] if isinstance(item, dict))
            line = f"Ensemble {state['ensemble_id']}: {status}; {done}; Restzeit {ensemble.get('eta_seconds')} s"
            if line != last_line:
                progress(line)
                last_line = line
        if status == "completed":
            state["ensemble_completed"] = True
            _save_state(state_path, state)
            return ensemble
        if status == "failed":
            reason = str(ensemble.get("error") or "Ensemble fehlgeschlagen")
            if _ensemble_attempts_exhausted(ensemble):
                raise ApiError(f"Ensemble nach erschöpften Versuchen abgebrochen: {reason}")
            if resumes >= ENSEMBLE_RESUME_ATTEMPTS:
                raise ApiError(
                    f"Resume-Versuche erschöpft ({ENSEMBLE_RESUME_ATTEMPTS}), Abbruch: {reason}")
            resumes += 1
            state["ensemble_resumes"] = resumes
            _save_state(state_path, state)
            try:
                client.post(f"/api/ensemble/{state['ensemble_id']}/resume", timeout=120, retry=True)
            except ApiError as error:
                raise ApiError(f"Resume abgebrochen: {error}") from error
            sleep(poll_interval)
            continue
        if status in TERMINAL_ENSEMBLE_STATUSES:
            raise ApiError(str(ensemble.get("error") or f"Ensemble endete mit {status}"))
        sleep(poll_interval)


def brier_score(probabilities: Sequence[float], actual: Sequence[int]) -> Optional[float]:
    return None if not probabilities else sum((p - y) ** 2 for p, y in zip(probabilities, actual)) / len(probabilities)


def accuracy_score(probabilities: Sequence[float], actual: Sequence[int]) -> Optional[float]:
    return None if not probabilities else sum((p >= .5) == bool(y) for p, y in zip(probabilities, actual)) / len(probabilities)


def log_score(probabilities: Sequence[float], actual: Sequence[int]) -> Optional[float]:
    if not probabilities:
        return None
    losses = []
    for probability, observed in zip(probabilities, actual):
        p = min(1 - 1e-15, max(1e-15, probability))
        losses.append(-(observed * math.log(p) + (1 - observed) * math.log(1 - p)))
    return sum(losses) / len(losses)


def calibration_slope(probabilities: Sequence[float], actual: Sequence[int]) -> Optional[float]:
    """Kalibrierungssteigung aus y ~ 1 + logit(p), per Newton/IRLS."""
    if len(probabilities) != len(actual) or len(probabilities) < 2 or len(set(actual)) < 2:
        return None
    clipped = [min(1 - 1e-6, max(1e-6, p)) for p in probabilities]
    x = [math.log(p / (1 - p)) for p in clipped]
    if max(x) - min(x) < 1e-12:
        return None
    intercept, slope = 0.0, 1.0
    for _ in range(100):
        mu = [1 / (1 + math.exp(-max(-40, min(40, intercept + slope * value)))) for value in x]
        weights = [max(value * (1 - value), 1e-12) for value in mu]
        g0 = sum(y - fitted for y, fitted in zip(actual, mu))
        g1 = sum(value * (y - fitted) for value, y, fitted in zip(x, actual, mu))
        h00, h01 = sum(weights), sum(w * value for w, value in zip(weights, x))
        h11 = sum(w * value * value for w, value in zip(weights, x))
        determinant = h00 * h11 - h01 * h01
        if determinant <= 1e-15:
            return None
        d0, d1 = (g0 * h11 - g1 * h01) / determinant, (h00 * g1 - h01 * g0) / determinant
        intercept, slope = intercept + d0, slope + d1
        if max(abs(d0), abs(d1)) < 1e-9:
            break
    return slope if math.isfinite(slope) and abs(slope) < 100 else None


def _rounded(value: Optional[float]) -> Optional[float]:
    return None if value is None else round(float(value), 6)


def metric_set(probabilities: Sequence[float], actual: Sequence[int]) -> Dict[str, Any]:
    return {"n": len(probabilities), "brier": _rounded(brier_score(probabilities, actual)),
            "accuracy_at_0_5": _rounded(accuracy_score(probabilities, actual)),
            "log_score": _rounded(log_score(probabilities, actual))}


def _primary_s_vs_p(ensemble: Dict[str, Any], primary_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """Gepaarte Seed-Tafel des Primärergebnisses, Abstand als Anteil S minus Anteil P."""
    if not primary_id:
        return None
    for item in ensemble.get("comparisons") or []:
        if item.get("variant") != "null_personas":
            continue
        ids = {str(item.get("outcome_id"))}
        ids.update(str(value) for value in item.get("collapsed_outcome_ids") or [])
        if str(primary_id) not in ids or not isinstance(item.get("table"), dict):
            continue
        table = {
            key: int(item["table"].get(key) or 0)
            for key in ("both_yes", "baseline_only", "variant_only", "both_no", "n_pairs", "unpaired")
        }
        distance = None if table["n_pairs"] <= 0 else round(
            (table["baseline_only"] - table["variant_only"]) / table["n_pairs"], 6)
        return {"table": table, "distance": distance}
    return None


def contaminated_case_result(case_name: str, outcomes: Sequence[Dict[str, Any]],
                             contamination: Dict[str, Any], *, runs: int, hours: int,
                             arms: Sequence[str], minutes_per_round: int = 60,
                             quellenluecke: bool = False,
                             kontaminiert: Optional[Dict[str, str]] = None,
                             rahmen: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    result = {"schema_version": 2, "case": case_name, "question": QUESTION, "runs": runs,
              "hours": hours, "minutes_per_round": minutes_per_round, "arms": list(arms),
              "rahmen": rahmen,
              "primary_outcome_id": primary_outcome_id(outcomes),
              "contaminated": True, "quellenluecke": quellenluecke,
              "contamination_check": contamination,
              "simulation_id": None, "ensemble_id": None,
              "generated_at": datetime.now(timezone.utc).isoformat(),
              "rows": [], "metrics": {}, "primary_metrics": {}, "metrics_citable": False,
              "metrics_note": METRICS_NOTE, "primary_s_vs_p": None,
              "aborted_before_prepare": True}
    if kontaminiert:
        result["kontaminiert"] = kontaminiert
    return result


def build_case_result(case_name: str, outcomes: Sequence[Dict[str, Any]], ensemble: Dict[str, Any],
                      *, runs: int, hours: int, arms: Optional[Sequence[str]] = None,
                      contamination: Optional[Dict[str, Any]] = None,
                      minutes_per_round: int = 60,
                      rahmen: Optional[Dict[str, Any]] = None,
                      ensemble_ids: Optional[Sequence[Dict[str, Any]]] = None) -> Dict[str, Any]:
    min_classified = max(1, int((rahmen or {}).get("min_classified_per_arm") or 1))
    results, reliability = ensemble.get("results") or {}, ensemble.get("reliability") or {}
    arms = list(arms or [arm for arm in ALLOWED_ARMS if arm in results])
    custom = {str(item.get("text_de") or "").strip(): item for item in ensemble.get("checklist") or []
              if item.get("source") == "user"}
    rows = []
    for outcome in outcomes:
        text = str(outcome["text_de"]).strip()
        item = custom.get(text)
        if not item:
            raise ValueError(f"Eigene Ergebnisfrage fehlt in der Ensemble-Antwort: {text}")
        outcome_id, arm_values = str(item["id"]), {}
        for arm in arms:
            value = (results.get(arm) or {}).get(outcome_id)
            if not isinstance(value, dict):
                raise ValueError(f"Variantenresultat {arm} fehlt für {outcome_id}")
            arm_values[arm] = {key: value.get(key, 0) for key in ("yes", "n", "rate", "disputed", "unclassified")}
        rel = reliability.get(outcome_id) or {}
        in_material = outcome.get("in_material") is True or bool(item.get("in_material", False))
        beyond = beyond_simulated_horizon(outcome, hours)
        kappa = rel.get("kappa")
        measurable = (isinstance(kappa, (int, float)) and not isinstance(kappa, bool)
                      and float(kappa) >= .6 and not in_material and not beyond
                      and all(int(value.get("n") or 0) >= min_classified for value in arm_values.values()))
        rows.append({"outcome_id": outcome_id, "question": text,
                     "primary": outcome.get("primaer") is True,
                     "actual": int(outcome["eingetreten"]), "source": outcome.get("quelle"),
                     "in_material": in_material, "beyond_horizon": beyond, "arms": arm_values,
                     "reliability": {key: rel.get(key) for key in ("agreement", "kappa", "n_pairs", "label")},
                     "measurable": measurable})
    def metrics(selected: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
        actual = [row["actual"] for row in selected]
        return {arm: metric_set([float(row["arms"][arm]["rate"]) for row in selected], actual) for arm in arms}
    scored = [row for row in rows if row["measurable"]]
    primary = [row for row in scored if row["primary"]]
    primary_id = next((row["outcome_id"] for row in rows if row["primary"]), None)
    return {"schema_version": 2, "case": case_name, "question": QUESTION, "runs": runs,
            "hours": hours, "minutes_per_round": minutes_per_round, "arms": arms,
            "rahmen": rahmen, "primary_outcome_id": primary_id,
            "contaminated": bool((contamination or {}).get("known", False)),
            "quellenluecke": any(item.get("quellenluecke") is True for item in outcomes),
            "contamination_check": contamination, "simulation_id": ensemble.get("simulation_id"),
            "ensemble_id": ensemble.get("ensemble_id"),
            "ensemble_ids": list(ensemble_ids or [{"ensemble_id": ensemble.get("ensemble_id")}]),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "rows": rows, "metrics": metrics(scored), "primary_metrics": metrics(primary),
            "metrics_citable": False, "metrics_note": METRICS_NOTE,
            "primary_s_vs_p": _primary_s_vs_p(ensemble, primary_id)}


def _display(value: Any, percent: bool = False) -> str:
    return "–" if value is None else (f"{float(value):.1%}" if percent else f"{float(value):.4f}")


def _escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def case_markdown(result: Dict[str, Any]) -> str:
    arms, check = result["arms"], result.get("contamination_check") or {}
    lines = [f"# V5-Realitätsabgleich: {result['case']}", "", f"Neutrale Frage: „{QUESTION}“", "",
             f"Kontaminationsprüfung: **{'kennt den Fall' if result['contaminated'] else 'kennt den Fall nicht'}** "
             f"(Modell: {_escape(check.get('model', '–'))}).", "",
             f"{result['runs']} Läufe je Arm, {result['hours']} simulierte Stunden, "
             f"Rundentakt {result.get('minutes_per_round', 60)} Minuten. Wahrheitswert, Quellen und "
             "tatsächlicher Verlauf wurden nicht an die Simulation gesendet.", "",
             "| Ergebnis | Typ | tatsächlich | " + " | ".join(ARM_LABELS[a] for a in arms) + " | Kappa |",
             "|---|---|---:|" + "---:|" * len(arms) + "---:|"]
    for row in result["rows"]:
        values = [f"{row['arms'][arm]['yes']}/{row['arms'][arm]['n']} ({float(row['arms'][arm]['rate']):.1%})" for arm in arms]
        lines.append(f"| {_escape(row['question'])} | {'primär' if row['primary'] else 'explorativ'} | {row['actual']} | "
                     + " | ".join(values) + f" | {_display(row['reliability'].get('kappa'))} |")
    lines += ["", "## Brier-Score je Arm", "", METRICS_NOTE, "",
              "| Arm | Sammel-Brier (nicht zitierfähig) | Primärergebnis |", "|---|---:|---:|"]
    for arm in arms:
        lines.append(f"| {ARM_LABELS[arm]} | {_display(result['metrics'][arm]['brier'])} | "
                     f"{_display(result['primary_metrics'][arm]['brier'])} |")
    lines += ["", "Das Primärergebnis ist konfirmatorisch; alle anderen Ergebnisse sind explorativ. "
              "Punkte mit Kappa < 0,6, ohne definiertes Kappa, mit zu wenigen klassifizierten Läufen, mit Fenster "
              "jenseits der simulierten Stunden oder mit in_material in der Akte werden nicht gescored. "
              "Der Sammel-Brier ist nicht zitierfähig."]
    return "\n".join(lines) + "\n"


def _percentile(values: Sequence[float], probability: float) -> float:
    if len(values) == 1:
        return float(values[0])
    position = (len(values) - 1) * probability
    low, high = math.floor(position), math.ceil(position)
    return float(values[low] if low == high else values[low] * (high - position) + values[high] * (position - low))


def bootstrap_mean_ci(values: Sequence[float], *, seed: int = BOOTSTRAP_SEED,
                      samples: int = BOOTSTRAP_SAMPLES) -> Optional[Dict[str, float]]:
    if not values:
        return None
    rng, n = random.Random(seed), len(values)
    means = sorted(sum(values[rng.randrange(n)] for _ in range(n)) / n for _ in range(samples))
    return {"low": round(_percentile(means, .025), 6), "high": round(_percentile(means, .975), 6)}


def _bootstrap_skill_ci(cases: Sequence[Dict[str, float]], numerator: str, denominator: str,
                        *, seed: int = BOOTSTRAP_SEED, samples: int = BOOTSTRAP_SAMPLES) -> Optional[Dict[str, float]]:
    if not cases:
        return None
    rng, n, values = random.Random(seed), len(cases), []
    for _ in range(samples):
        sample = [cases[rng.randrange(n)] for _ in range(n)]
        den = sum(item[denominator] for item in sample) / n
        if den > 0:
            values.append(1 - (sum(item[numerator] for item in sample) / n) / den)
    if not values:
        return None
    values.sort()
    return {"low": round(_percentile(values, .025), 6), "high": round(_percentile(values, .975), 6)}


def _kappa_number(row: Dict[str, Any]) -> Optional[float]:
    kappa = (row.get("reliability") or {}).get("kappa")
    if isinstance(kappa, bool) or not isinstance(kappa, (int, float)):
        return None
    return float(kappa)


def _primary_kappa_ok(row: Dict[str, Any]) -> bool:
    value = _kappa_number(row)
    return value is not None and value >= .6


def _primary_row(result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return next((item for item in result.get("rows", []) if item.get("primary")), None)


def _summary_group(results: Sequence[Dict[str, Any]], *, frame: Optional[Dict[str, Any]] = None,
                   issues: Sequence[str] = (), decision: bool = True) -> Dict[str, Any]:
    observations = []
    kappa_excluded = []
    for result in results:
        primary = _primary_row(result)
        kappa = None if primary is None else _kappa_number(primary)
        # Nur ein definiertes Kappa unter 0,6 macht das Instrument unzuverlässig; ohne Varianz ist es nicht prüfbar.
        if primary is not None and kappa is not None and kappa < .6:
            kappa_excluded.append({"case": result.get("case"), "kappa": kappa})
        if primary is not None and primary.get("measurable") and _primary_kappa_ok(primary):
            observations.append({"case": result.get("case"), "actual": int(primary["actual"]),
                                 "kappa": float(primary["reliability"]["kappa"]),
                                 "p": {arm: float(primary["arms"][arm]["rate"]) for arm in result["arms"]}})
    arms = [arm for arm in ALLOWED_ARMS if observations and all(arm in item["p"] for item in observations)]
    losses = [{arm: (item["p"][arm] - item["actual"]) ** 2 for arm in arms} for item in observations]
    brier = {arm: _rounded(sum(item[arm] for item in losses) / len(losses)) if losses else None for arm in arms}
    brier_ci = {arm: bootstrap_mean_ci([item[arm] for item in losses]) for arm in arms}
    skill = {}
    for numerator, denominator in (("baseline", "null_document"), ("null_personas", "null_document"),
                                   ("baseline", "null_personas")):
        if numerator in arms and denominator in arms:
            reference = brier[denominator]
            skill[f"{numerator}_vs_{denominator}"] = {
                "value": _rounded(None if not reference else 1 - float(brier[numerator]) / reference),
                "ci_95": _bootstrap_skill_ci(losses, numerator, denominator)}
    calibration = {}
    pilot = len(observations) < CALIBRATION_MIN_CASES
    for arm in arms:
        slope = calibration_slope([item["p"][arm] for item in observations],
                                  [item["actual"] for item in observations]) if len(observations) >= 8 else None
        calibration[arm] = {"slope": _rounded(slope),
                            "note": CALIBRATION_PILOT_NOTE if pilot else None}
    interval = (skill.get("baseline_vs_null_document") or {}).get("ci_95")
    skill_above = None if interval is None else interval["low"] > 0
    skill_below = None if interval is None else interval["high"] < 0
    sp_interval = (skill.get("baseline_vs_null_personas") or {}).get("ci_95")
    sp_above = None if sp_interval is None else sp_interval["low"] > 0
    kappas = [item["kappa"] for item in observations]
    distances = []
    paired_cases = []
    scored_names = {item["case"] for item in observations}
    for result in results:
        if result.get("case") not in scored_names:
            continue
        distance = (result.get("primary_s_vs_p") or {}).get("distance")
        if not isinstance(distance, (int, float)) or isinstance(distance, bool):
            continue
        distances.append(float(distance))
        paired_cases.append({"case": result.get("case"),
                             "table": result["primary_s_vs_p"].get("table"),
                             "distance": round(float(distance), 6)})
    distance_ci = bootstrap_mean_ci(distances) if len(distances) == len(observations) else None
    kappa_share = round(len(kappa_excluded) / len(results), 6) if results else None
    checks = {"skill_interval_above_zero": skill_above,
              "skill_interval_below_zero": skill_below,
              "skill_s_vs_p_interval_above_zero": sp_above,
              "kappa_at_least_0_6": False if kappa_excluded else (None if not kappas else min(kappas) >= .6)}
    if not pilot:
        slope = (calibration.get("baseline") or {}).get("slope")
        checks["calibration_slope_0_5_to_1_5"] = None if slope is None else .5 <= slope <= 1.5
    frame_issues = list(issues)
    if frame is None:
        frame_issues.append("kein Rahmen, Fallmenge nicht prüfbar")
    else:
        expected = list(frame.get("case_ids") or [])
        if scored_names != set(expected) or len(observations) != int(frame.get("cases") or 0):
            missing = sorted(set(expected) - scored_names)
            foreign = sorted(scored_names - set(expected))
            frame_issues.append(
                f"{len(observations)} statt {frame.get('cases')} gewertete Fälle"
                + (f", fehlen: {', '.join(missing)}" if missing else "")
                + (f", fremd: {', '.join(foreign)}" if foreign else ""))
    decisive = {key: value for key, value in checks.items() if key != "skill_interval_below_zero"}
    if not decision:
        status = "nicht Teil der Entscheidung"
    elif kappa_excluded:
        status = KAPPA_INSTRUMENT_STATUS
    elif skill_below is True:
        status = "nicht bestanden"
    elif frame_issues:
        status = NOT_TESTABLE
    elif any(value is False for value in decisive.values()):
        status = "nicht bestanden"
    elif any(value is None for value in decisive.values()):
        status = NOT_TESTABLE
    else:
        status = "bestanden"
    return {"case_count": len(results), "scored_primary_cases": len(observations), "arms": arms,
            "scored_cases": sorted(scored_names), "frame_issues": frame_issues,
            "pilot": pilot, "brier": brier, "brier_ci_95": brier_ci, "skill": skill,
            "calibration": calibration,
            "s_vs_p": {"mean_distance": _rounded(sum(distances) / len(distances)) if distances else None,
                       "ci_95": distance_ci, "cases": paired_cases},
            "minimum_kappa": _rounded(min(kappas)) if kappas else None,
            "kappa_excluded_primary": kappa_excluded,
            "kappa_excluded_primary_count": len(kappa_excluded),
            "kappa_excluded_primary_share": kappa_share,
            "preregistered_criterion": {"status": status, "checks": checks}}


def _rahmen_protocol(results: Sequence[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    frames = [item.get("rahmen") for item in results]
    if not any(frames):
        return None
    if any(frame is None or frame != frames[0] for frame in frames):
        return {"conflict": True}
    return frames[0]


def _minutes_protocol(results: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    rows = [{"case": item.get("case"), "minutes_per_round": item["minutes_per_round"]}
            for item in results if isinstance(item.get("minutes_per_round"), int)
            and not isinstance(item.get("minutes_per_round"), bool)]
    return {"values": sorted({row["minutes_per_round"] for row in rows}), "cases": rows}


KNOWN_FRAME_IDS = ("pilot-v5", "probe-v5")


def _frame_for(results: Sequence[Dict[str, Any]], frame: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Maßgeblicher Rahmen: übergeben, sonst die Rahmendatei zur einheitlichen Rahmen-ID der Ergebnisse."""
    if frame is not None:
        return frame
    ids = {(item.get("rahmen") or {}).get("id") for item in results if isinstance(item.get("rahmen"), dict)}
    if len(ids) == 1 and next(iter(ids)) in KNOWN_FRAME_IDS:
        try:
            return load_rahmen(next(iter(ids)))
        except (OSError, ValueError):
            return None
    return None


def _frame_rejection(item: Dict[str, Any], frame: Dict[str, Any]) -> Optional[str]:
    if item.get("case") not in (frame.get("case_ids") or []):
        return "Fall nicht im Rahmen"
    if item.get("rahmen") != frame:
        return "Rahmen weicht ab"
    if list(item.get("arms") or []) != list(frame["arms"]):
        return "Arme weichen ab"
    if (item.get("runs"), item.get("hours"), item.get("minutes_per_round")) != (
            frame["seeds"], frame["hours"], frame["minutes_per_round"]):
        return "Seeds, Stunden oder Takt weichen ab"
    return None


def _probe_diagnostics(results: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    rows = []
    for result in results:
        primary = _primary_row(result)
        if primary is None:
            continue
        kappa = _kappa_number(primary)
        rates = {arm: primary["arms"][arm]["rate"] for arm in result.get("arms", [])}
        rows.append({"case": result.get("case"), "kappa": kappa, "kappa_degenerate": kappa is None,
                     "primary_rates": rates,
                     "rate_variance": len({round(float(value), 6) for value in rates.values()}) > 1})
    return {"cases": rows,
            "note": "Probelauf: prüft Varianz der Klassifikation und Kappa; kein Ergebnis zur Nutzenbehauptung."}


def build_summary(case_results: Iterable[Dict[str, Any]],
                  frame: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    results = list(case_results)
    frame = _frame_for(results, frame)
    contaminated = [item for item in results if item.get("contaminated", False)]
    candidates = [item for item in results if not item.get("contaminated", False)]
    rejected, clean = [], []
    for item in candidates:
        reason = _frame_rejection(item, frame) if frame is not None else None
        (rejected if reason else clean).append(
            {"case": item.get("case"), "grund": reason} if reason else item)
    issues = [f"nicht aggregiert: {row['case']} ({row['grund']})" for row in rejected]
    # Ausschluss nur über das Feld, nie über den Ordnernamen.
    sensitivity = [item for item in clean if item.get("quellenluecke") is not True]
    sensitivity_group = _summary_group(sensitivity, frame=frame, decision=False)
    sensitivity_group["replaces_primary"] = False
    declared = []
    for item in contaminated:
        flag = item.get("kontaminiert")
        if isinstance(flag, dict):
            declared.append({"case": item.get("case"), "quelle": flag.get("quelle"),
                             "datum": flag.get("datum")})
    group = _summary_group(clean, frame=frame, issues=issues)
    probe = frame is not None and frame.get("id") == "probe-v5"
    if probe:
        group["preregistered_criterion"]["status"] = PROBE_STATUS
    return {"schema_version": 2, "generated_at": datetime.now(timezone.utc).isoformat(),
            "bootstrap_unit": "case", "bootstrap_seed": BOOTSTRAP_SEED,
            "bootstrap_samples": BOOTSTRAP_SAMPLES, "minutes_per_round": _minutes_protocol(clean),
            "rahmen": frame if frame is not None else _rahmen_protocol(results),
            "models": (frame or {}).get("models"),
            "clean": group,
            "rejected": rejected,
            "ensemble_ids": [{"case": item.get("case"), "ensemble_ids": item.get("ensemble_ids") or []}
                             for item in results],
            "probe": _probe_diagnostics(clean) if probe else None,
            "sensitivity_no_source_gap": sensitivity_group,
            "source_gap_cases": [item.get("case") for item in clean if item.get("quellenluecke") is True],
            "contaminated": _summary_group(contaminated, frame=frame, decision=False),
            "contaminated_cases": [item.get("case") for item in contaminated],
            "contaminated_declared": declared}


def _minutes_sentence(summary: Dict[str, Any]) -> Optional[str]:
    protocol = summary.get("minutes_per_round") or {}
    values = protocol.get("values") or []
    if len(values) == 1:
        return f"Rundentakt: {values[0]} Minuten je Runde."
    if values:
        rendered = ", ".join(f"{row['case']}: {row['minutes_per_round']}" for row in protocol.get("cases") or [])
        return f"Rundentakt je Fall: {rendered}."
    return None


def _brier_table(group: Dict[str, Any]) -> List[str]:
    lines = ["| Arm | Brier-Score | 95-%-Fall-Bootstrap-KI | Kalibrierungssteigung |",
             "|---|---:|---:|---:|"]
    for arm in group["arms"]:
        cal = group["calibration"][arm]
        interval = group["brier_ci_95"][arm]
        rendered = f"{interval['low']:.4f}–{interval['high']:.4f}" if interval else "–"
        slope_cell = _display(cal["slope"])
        if cal.get("note"):
            slope_cell = f"{slope_cell} ({cal['note']})"
        lines.append(f"| {ARM_LABELS[arm]} | {_display(group['brier'][arm])} | {rendered} | {slope_cell} |")
    lines += ["", "| Kontrast | Skill | 95-%-Fall-Bootstrap-KI |", "|---|---:|---:|"]
    for name, item in group["skill"].items():
        interval = item["ci_95"]
        rendered = f"{interval['low']:.4f}–{interval['high']:.4f}" if interval else "–"
        lines.append(f"| {name} | {_display(item['value'])} | {rendered} |")
    return lines


def summary_markdown(summary: Dict[str, Any]) -> str:
    group = summary["clean"]
    lines = ["# V5-Realitätsabgleich – Gesamt", "",
             f"Primäranalyse: {group['case_count']} nicht kontaminierte Fälle, "
             f"davon {group['scored_primary_cases']} mit messbarem Primärergebnis. "
             f"Bootstrap über **Fälle** ({summary['bootstrap_samples']} Ziehungen, Seed {summary['bootstrap_seed']})."]
    takt = _minutes_sentence(summary)
    if takt:
        lines.append(takt)
    lines += ["", "| Arm | Brier-Score | 95-%-Fall-Bootstrap-KI | Kalibrierungssteigung |",
              "|---|---:|---:|---:|"]
    for arm in group["arms"]:
        cal = group["calibration"][arm]
        interval = group["brier_ci_95"][arm]
        rendered = f"{interval['low']:.4f}–{interval['high']:.4f}" if interval else "–"
        slope_cell = _display(cal["slope"])
        if cal.get("note"):
            slope_cell = f"{slope_cell} ({cal['note']})"
        lines.append(f"| {ARM_LABELS[arm]} | {_display(group['brier'][arm])} | {rendered} | {slope_cell} |")
    lines += ["", "## Skill gegen Dokument-Nullmodell (D)", "",
              "| Kontrast | Skill | 95-%-Fall-Bootstrap-KI |", "|---|---:|---:|"]
    for name, item in group["skill"].items():
        interval = item["ci_95"]
        rendered = f"{interval['low']:.4f}–{interval['high']:.4f}" if interval else "–"
        lines.append(f"| {name} | {_display(item['value'])} | {rendered} |")
    contrast = group.get("s_vs_p") or {}
    contrast_interval = contrast.get("ci_95")
    contrast_rendered = (f"{contrast_interval['low']:.4f}–{contrast_interval['high']:.4f}"
                         if contrast_interval else "–")
    lines += ["", "## Abstand Schwarm (S) gegen Persona-Nullmodell (P)", "",
              "Mittlerer gepaarter Abstand des Primärergebnisses (Anteil S minus Anteil P) über Fälle, "
              "mit Fall-Bootstrap. Nur ausgewiesen, kein Bestehenskriterium; maßgeblich ist Skill(S,P).", "",
              f"Mittel: {_display(contrast.get('mean_distance'))}, 95-%-KI: {contrast_rendered}.", ""]
    criterion = group["preregistered_criterion"]
    contaminated_line = (
        f"Kontaminierte Fälle ({summary['contaminated']['case_count']}): "
        + (", ".join(summary["contaminated_cases"]) or "keine")
        + ". Sie sind aus der Hauptauswertung ausgeschlossen und im JSON getrennt ausgewiesen."
    )
    declared = summary.get("contaminated_declared") or []
    if declared:
        detail = "; ".join(
            f"{row['case']} ({row.get('datum') or '–'}: {row.get('quelle') or '–'})" for row in declared)
        contaminated_line += f" Vorab festgelegt: {detail}."
    lines += ["## Vorab-Kriterium", "", f"**{criterion['status']}**", "", DECISION_RULE_PILOT, ""]
    if group.get("pilot") is False:
        lines += [DECISION_RULE_CONFIRMATORY, ""]
    if group.get("frame_issues"):
        lines += ["Gründe für „nicht prüfbar“ bzw. Einschränkungen: " + "; ".join(group["frame_issues"]) + ".", ""]
    if summary.get("probe"):
        lines += ["## Probelauf (nicht gewertet)", "", summary["probe"]["note"], ""]
        for row in summary["probe"]["cases"]:
            lines.append(f"- {row['case']}: Kappa {_display(row['kappa'])}"
                         f"{' (degeneriert, Instrument nicht prüfbar)' if row['kappa_degenerate'] else ''}, "
                         f"Ja-Anteile {row['primary_rates']}, Varianz zwischen Armen: "
                         f"{'ja' if row['rate_variance'] else 'nein'}.")
        lines.append("")
    models = summary.get("models")
    if isinstance(models, dict):
        lines += [f"Modelle: Textarme {models.get('agent_model')}, Klassifikation "
                  f"{models.get('classification_main')} und {models.get('classification_second')}, "
                  f"seed_fallback {models.get('seed_fallback')}, Kaltabruf "
                  f"{', '.join(models.get('cold_question_models') or [])}.", ""]
    listed = [row for row in summary.get("ensemble_ids") or [] if row.get("ensemble_ids")]
    if listed:
        lines += ["Alle ensemble_id je Fall: " + "; ".join(
            f"{row['case']}: " + ", ".join(str(entry.get("ensemble_id")) for entry in row["ensemble_ids"])
            for row in listed) + ".", ""]
    excluded = group.get("kappa_excluded_primary") or []
    if excluded:
        rendered = ", ".join(
            f"{item.get('case')} (Kappa {_display(item.get('kappa'))})" for item in excluded)
        lines.append(
            f"Wegen Kappa aus der Wertung des Primärergebnisses: "
            f"{group.get('kappa_excluded_primary_count')} von {group['case_count']} "
            f"(Anteil {group.get('kappa_excluded_primary_share')}). {rendered}.")
        lines.append("")
    rahmen = summary.get("rahmen")
    if isinstance(rahmen, dict) and rahmen.get("conflict"):
        lines += ["Rahmen widersprüchlich, kein einheitlicher Pilotrahmen.", ""]
    elif isinstance(rahmen, dict):
        lines += [
            f"Rahmen {rahmen.get('id')} ({rahmen.get('status')}): "
            f"{rahmen.get('cases')} Fälle, Arme {', '.join(rahmen.get('arms') or [])}, "
            f"{rahmen.get('seeds')} Seeds, minutes_per_round {rahmen.get('minutes_per_round')}, "
            f"hours {rahmen.get('hours')}, GPU-Schätzung "
            f"{rahmen.get('gpu_hours_low')}–{rahmen.get('gpu_hours_high')} h "
            f"(Mitte {rahmen.get('gpu_hours_mid')}).",
            ""]
    lines.append(contaminated_line)
    sens = summary["sensitivity_no_source_gap"]
    excluded = ", ".join(summary.get("source_gap_cases") or []) or "keine"
    lines += ["", "## Vorab fixierte Sensitivitätsanalyse", "",
              f"{sens['case_count']} nicht kontaminierte Fälle ohne Quellenlücke, "
              f"davon {sens['scored_primary_cases']} mit messbarem Primärergebnis. "
              f"Ausgeschlossen über das Feld quellenluecke: {excluded}. "
              "Diese Auswertung ersetzt das Vorab-Kriterium der Primäranalyse nicht.", ""]
    if sens["arms"]:
        lines.extend(_brier_table(sens))
    else:
        lines.append("Keine gewerteten Fälle.")
    return "\n".join(lines) + "\n"


def update_summary(results_dir: Path, frame: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    results = []
    for path in sorted(results_dir.glob("*.json")):
        if path.name == "GESAMT.json" or path.name.endswith(".state.json"):
            continue
        payload = _load_json(path)
        if isinstance(payload, dict) and payload.get("schema_version") == 2 and (
                payload.get("rows") or payload.get("contaminated")):
            results.append(payload)
    summary = build_summary(results, frame)
    _write_json_atomic(results_dir / "GESAMT.json", summary)
    _write_text_atomic(results_dir / "GESAMT.md", summary_markdown(summary))
    return summary


def _write_contaminated(results_dir: Path, case_name: str, result: Dict[str, Any], note: str,
                        frame: Optional[Dict[str, Any]] = None) -> None:
    _write_json_atomic(results_dir / f"{case_name}.json", result)
    _write_text_atomic(results_dir / f"{case_name}.md", note)
    update_summary(results_dir, frame)


def validate_case(case_dir: Path, *, runs: int = 10, hours: int = 336,
                  arms: Sequence[str] = DEFAULT_ARMS, base: str = "http://127.0.0.1:5002",
                  results_dir: Optional[Path] = None, client: Optional[ApiClient] = None,
                  contamination_checker: Any = None, location: Optional[str] = None,
                  year: Optional[str] = None, topic: Optional[str] = None,
                  minutes_per_round: int = 60, rahmen: Optional[Dict[str, Any]] = None,
                  sleep: Callable[[float], None] = time.sleep, poll_interval: float = 5.0,
                  progress: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
    case_dir = case_dir.resolve()
    if results_dir is None:
        results_dir = DEFAULT_RESULTS_DIR / rahmen["id"] if rahmen else DEFAULT_RESULTS_DIR
    validate_case_files(case_dir)
    arms = parse_arms(arms)
    if isinstance(runs, bool) or not 1 <= runs <= 100:
        raise ValueError("runs muss zwischen 1 und 100 liegen")
    if isinstance(hours, bool) or not 1 <= hours <= 336:
        raise ValueError("hours muss zwischen 1 und 336 liegen")
    minutes_per_round = validate_minutes_per_round(minutes_per_round, hours)
    outcomes = load_outcomes(case_dir)
    annotations = case_annotations(outcomes)
    results_dir.mkdir(parents=True, exist_ok=True)
    if annotations["kontaminiert"]:
        flag = annotations["kontaminiert"]
        result = contaminated_case_result(
            case_dir.name, outcomes,
            {"known": True, "predeclared": True, "quelle": flag["quelle"], "datum": flag["datum"],
             "checked_at": datetime.now(timezone.utc).isoformat(), "model": None, "answer": None},
            runs=runs, hours=hours, arms=arms, minutes_per_round=minutes_per_round,
            quellenluecke=annotations["quellenluecke"], kontaminiert=flag, rahmen=rahmen)
        _write_contaminated(
            results_dir, case_dir.name, result,
            f"# V5-Realitätsabgleich: {case_dir.name}\n\n"
            f"Vorab kontaminiert (Quelle: {flag['quelle']}, Datum: {flag['datum']}). "
            "Die Simulation wurde nicht gestartet.\n", rahmen)
        raise ValueError(f"Fall {case_dir.name} ist vorab kontaminiert ({flag['quelle']}, {flag['datum']}); "
                         "Simulation nicht gestartet")
    if rahmen and case_dir.name not in (rahmen.get("case_ids") or []):
        raise ValueError(f"Fall {case_dir.name} gehört nicht zum Rahmen {rahmen.get('id')}; Abbruch")
    state_path = results_dir / f"{case_dir.name}.state.json"
    state = load_or_create_state(state_path, case_dir.name, base, runs, hours, arms, minutes_per_round)
    if not state.get("contamination_check"):
        material = (case_dir / "ausgangslage.md").read_text(encoding="utf-8")
        state["contamination_check"] = check_contamination(
            cold_case_label(outcomes, location=location, year=year),
            contamination_checker, material=material, forbidden=case_dir.name,
            topic=case_topic(case_dir, topic),
            models=((rahmen or {}).get("models") or {}).get("cold_question_models"),
            hidden_outcomes=outcomes)
        _save_state(state_path, state)
    if state["contamination_check"].get("known") is True:
        result = contaminated_case_result(
            case_dir.name, outcomes, state["contamination_check"], runs=runs, hours=hours, arms=arms,
            minutes_per_round=minutes_per_round, quellenluecke=annotations["quellenluecke"],
            rahmen=rahmen)
        _write_contaminated(
            results_dir, case_dir.name, result,
            f"# V5-Realitätsabgleich: {case_dir.name}\n\n"
            "Kontaminationsprüfung: **kennt den Fall**. "
            "Die Simulation wurde vor der Vorbereitung abgebrochen.\n", rahmen)
        raise ValueError(f"Fall {case_dir.name} ist kontaminiert (Kaltfrage kennt: true); "
                         "Simulation vor der Vorbereitung abgebrochen")
    api = client or ApiClient(base, sleep=sleep, log=progress)
    prepare_simulation(api, case_dir, state_path, state, sleep=sleep, poll_interval=poll_interval)
    ensemble = run_ensemble(api, outcomes, state_path, state, rahmen=rahmen, sleep=sleep,
                            poll_interval=poll_interval, progress=progress)
    result = build_case_result(case_dir.name, outcomes, ensemble, runs=runs, hours=hours,
                               arms=arms, contamination=state["contamination_check"],
                               minutes_per_round=state["minutes_per_round"], rahmen=rahmen,
                               ensemble_ids=state.get("ensemble_ids"))
    _write_json_atomic(results_dir / f"{case_dir.name}.json", result)
    _write_text_atomic(results_dir / f"{case_dir.name}.md", case_markdown(result))
    update_summary(results_dir, rahmen)
    return result


def load_rahmen(name: str) -> Dict[str, Any]:
    if name not in KNOWN_FRAME_IDS:
        raise ValueError(f"Unbekannter Rahmen: {name}")
    path = REPOSITORY_ROOT / "docs" / "validation" / "rahmen-pilot-v5.json"
    payload = _load_json(path)
    if not isinstance(payload, dict):
        raise ValueError("rahmen-pilot-v5.json muss ein Objekt sein")
    for key, value in PILOT_V5_FRAME.items():
        if payload.get(key) != value:
            raise ValueError(
                f"rahmen-pilot-v5.json weicht bei {key} ab: {payload.get(key)!r} statt {value!r}")
    frame = copy.deepcopy(PROBE_V5_FRAME if name == "probe-v5" else
                          {key: payload[key] for key in PILOT_V5_FRAME})
    frame["arms"] = list(frame["arms"])
    return frame


def resolve_invocation(arguments: argparse.Namespace) -> Dict[str, Any]:
    """CLI-Werte. --rahmen pilot-v5 setzt den Pilotrahmen; ein abweichender Einzelwert bricht ab."""
    rahmen_name = "probe-v5" if getattr(arguments, "probe", False) else arguments.rahmen
    if rahmen_name:
        frame = load_rahmen(rahmen_name)
        deviations = []
        if arguments.runs is not None and arguments.runs != frame["seeds"]:
            deviations.append(f"--runs {arguments.runs} weicht vom Rahmenwert {frame['seeds']} ab")
        if arguments.hours is not None and arguments.hours != frame["hours"]:
            deviations.append(f"--hours {arguments.hours} weicht vom Rahmenwert {frame['hours']} ab")
        if (arguments.minutes_per_round is not None
                and arguments.minutes_per_round != frame["minutes_per_round"]):
            deviations.append(
                f"--minutes-per-round {arguments.minutes_per_round} weicht vom Rahmenwert "
                f"{frame['minutes_per_round']} ab")
        if arguments.arms is not None and parse_arms(arguments.arms) != frame["arms"]:
            deviations.append(f"--arms {arguments.arms} weicht vom Rahmen ab")
        if deviations:
            raise ValueError(f"Rahmen {rahmen_name}: " + "; ".join(deviations) + ". Abbruch.")
        return {"runs": frame["seeds"], "hours": frame["hours"],
                "minutes_per_round": frame["minutes_per_round"], "arms": list(frame["arms"]),
                "rahmen": frame}
    return {"runs": 10 if arguments.runs is None else arguments.runs,
            "hours": 336 if arguments.hours is None else arguments.hours,
            "minutes_per_round": 60 if arguments.minutes_per_round is None else arguments.minutes_per_round,
            "arms": parse_arms(arguments.arms) if arguments.arms is not None else list(DEFAULT_ARMS),
            "rahmen": None}


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_dir", type=Path, nargs="?", default=None,
                        help="Ordner mit ausgangslage.md, verlauf.md und ergebnisse.json")
    parser.add_argument("--probe", action="store_true",
                        help="Probelauf mit dem synthetischen Fall docs/validation/probe/ (2 Seeds, nicht gewertet)")
    parser.add_argument("--rahmen", choices=("pilot-v5",), default=None,
                        help="Pilotrahmen; setzt Seeds, Stunden, Takt und Arme")
    parser.add_argument("--runs", type=int, default=None)
    parser.add_argument("--hours", type=int, default=None)
    parser.add_argument("--minutes-per-round", type=int, default=None,
                        choices=ALLOWED_MINUTES_PER_ROUND,
                        help="Rundentakt in Minuten, an den Ensemble-Start durchgereicht")
    parser.add_argument("--arms", default=None, help="Kommagetrennte V5-Arme")
    parser.add_argument("--base", default="http://127.0.0.1:5002")
    parser.add_argument("--results-dir", type=Path, default=None,
                        help="Zielordner für Fallberichte und GESAMT (Standard: docs/validation/ergebnisse)")
    parser.add_argument("--ort", dest="location")
    parser.add_argument("--jahr", dest="year")
    parser.add_argument("--thema", dest="topic")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = parse_args(argv)
    options = {}
    if arguments.results_dir is not None:
        options["results_dir"] = arguments.results_dir
    try:
        if arguments.probe and arguments.rahmen:
            raise ValueError("--probe und --rahmen schließen sich aus")
        if arguments.probe and arguments.case_dir is None:
            arguments.case_dir = PROBE_DIR
        if arguments.case_dir is None:
            raise ValueError("Fallordner fehlt")
        chosen = resolve_invocation(arguments)
        result = validate_case(arguments.case_dir, runs=chosen["runs"], hours=chosen["hours"],
                               minutes_per_round=chosen["minutes_per_round"],
                               arms=chosen["arms"], base=arguments.base, rahmen=chosen["rahmen"],
                               location=arguments.location, year=arguments.year, topic=arguments.topic,
                               **options)
    except (ApiError, OSError, ValueError) as error:
        print(f"Fehler: {error}", file=sys.stderr)
        return 1
    results_dir = arguments.results_dir or (
        DEFAULT_RESULTS_DIR / chosen["rahmen"]["id"] if chosen["rahmen"] else DEFAULT_RESULTS_DIR)
    print(f"Auswertung geschrieben: {results_dir / (result['case'] + '.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
