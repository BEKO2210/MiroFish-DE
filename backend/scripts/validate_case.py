#!/usr/bin/env python3
"""Dokumentierte Realfälle blind simulieren und fallweise auswerten."""
from __future__ import annotations

import argparse
import json
import math
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
CALIBRATION_PILOT_NOTE = "Unter 25 Fällen nicht als Bestehen zählen"
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


class ApiError(RuntimeError):
    pass


class ApiClient:
    def __init__(self, base: str, session: Any = None) -> None:
        self.base, self.session = base.rstrip("/"), session or requests.Session()

    @staticmethod
    def _unwrap(response: Any) -> Dict[str, Any]:
        try:
            payload = response.json()
        except (TypeError, ValueError) as error:
            raise ApiError(f"Antwort ist kein JSON (HTTP {response.status_code}): "
                           f"{str(getattr(response, 'text', ''))[:200]}") from error
        if response.status_code >= 400 or not payload.get("success", True):
            raise ApiError(str(payload.get("error") or f"HTTP {response.status_code}"))
        data = payload.get("data", payload)
        if not isinstance(data, dict):
            raise ApiError("API-Antwort enthält kein Datenobjekt")
        return data

    def get(self, path: str, *, timeout: int = 30) -> Dict[str, Any]:
        return self._unwrap(self.session.get(f"{self.base}{path}", timeout=timeout))

    def post(self, path: str, *, json_body: Optional[Dict[str, Any]] = None,
             data: Optional[Dict[str, Any]] = None, files: Any = None,
             timeout: int = 60) -> Dict[str, Any]:
        return self._unwrap(self.session.post(f"{self.base}{path}", json=json_body,
                                              data=data, files=files, timeout=timeout))


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


def case_identity(case_dir: Path, *, location: Optional[str] = None,
                  year: Optional[str] = None, topic: Optional[str] = None) -> Dict[str, str]:
    """Merkmale aus T0-Material bestimmen, ohne den späteren Ausgang zu lesen."""
    text = (case_dir / "ausgangslage.md").read_text(encoding="utf-8")
    def field(name: str) -> Optional[str]:
        match = re.search(rf"(?im)^\s*(?:[-*]\s*)?{name}\s*:\s*(.+?)\s*$", text)
        return match.group(1).strip() if match else None
    heading = re.search(r"(?m)^#\s+(.+?)\s*$", text)
    return {"location": str(location or field("Ort") or case_dir.name),
            "year": str(year or field("Jahr") or "nicht angegeben"),
            "topic": str(topic or field("Thema") or (heading.group(1) if heading else case_dir.name))}


def _contamination_prompt(identity: Dict[str, str], material: Optional[str]) -> List[tuple]:
    identity_prompt = (
        "Kennst du den folgenden realen kommunalpolitischen Fall aus deinem Vorwissen? "
        "Nutze keine Werkzeuge und recherchiere nicht. Antworte nur als JSON mit kennt "
        "(boolesch) und begruendung (kurzer Text).\n"
        f"Ort: {identity['location']}\nJahr: {identity['year']}\nThema: {identity['topic']}\n"
        "Der Ausgang wird absichtlich nicht genannt."
    )
    prompts = [("identity", identity_prompt)]
    if material is not None:
        prompts.append(("material",
                        "Kennst du den realen Fall, der in dem folgenden Bogen beschrieben wird, "
                        "aus deinem Vorwissen? Der Text ist der Wortlaut, den die Simulation sieht. "
                        "Nutze keine Werkzeuge und recherchiere nicht. Antworte nur als JSON mit kennt "
                        "(boolesch) und begruendung (kurzer Text).\n"
                        f"{material}\nDer Ausgang wird absichtlich nicht genannt."))
    return prompts


def _read_contamination_answer(answer: Any) -> bool:
    if not isinstance(answer, dict):
        raise ValueError("Kontaminationsprüfung lieferte kein JSON-Objekt")
    known = answer.get("kennt", answer.get("known"))
    if not isinstance(known, bool):
        raise ValueError("Kontaminationsprüfung muss 'kennt' als booleschen Wert liefern")
    return known


def check_contamination(identity: Dict[str, str], llm: Any = None,
                       *, material: Optional[str] = None) -> Dict[str, Any]:
    """Hauptmodell kalt zum echten Fall und, getrennt, zum Bogenwortlaut fragen."""
    if llm is None:
        from app.utils.llm_client import LLMClient
        llm = LLMClient()
    answers: Dict[str, Any] = {}
    known_flags: Dict[str, bool] = {}
    model = "configured-main-model"
    try:
        for kind, prompt in _contamination_prompt(identity, material):
            if callable(llm) and not hasattr(llm, "chat_json"):
                answer = llm(identity, prompt)
                model = str(getattr(llm, "model", "injected-checker"))
            else:
                answer = llm.chat_json(
                    [{"role": "system", "content": "Prüfe nur vorhandenes Fallwissen."},
                     {"role": "user", "content": prompt}],
                    temperature=0, max_tokens=300, seed=BOOTSTRAP_SEED)
                model = str(getattr(llm, "model", "configured-main-model"))
            known_flags[kind] = _read_contamination_answer(answer)
            answers[kind] = answer
    except (ApiError, ValueError):
        raise
    except Exception as error:
        raise ApiError(f"Kontaminationsprüfung mit dem Hauptmodell fehlgeschlagen: {error}") from error
    return {"checked_at": datetime.now(timezone.utc).isoformat(), "model": model,
            "identity": identity, "known": any(known_flags.values()),
            "identity_known": known_flags.get("identity"),
            "material_known": known_flags.get("material"),
            "answer": answers.get("identity"), "material_answer": answers.get("material")}


def _new_state(case_name: str, base: str, runs: int, hours: int, arms: Sequence[str],
               minutes_per_round: int = 60) -> Dict[str, Any]:
    return {"case": case_name, "base": base.rstrip("/"), "runs": runs, "hours": hours,
            "minutes_per_round": minutes_per_round, "arms": list(arms), "question": QUESTION,
            "contamination_check": None,
            "project_id": None, "graph_task_id": None, "graph_id": None,
            "simulation_id": None, "prepare_task_id": None, "prepared": False,
            "ensemble_id": None, "ensemble_completed": False,
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
                                     "project_name": f"Realitätsabgleich: {case_dir.name}"}, timeout=3600)
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
                                   json_body={"simulation_id": state["simulation_id"], "parallel_profile_count": 1})
            state["prepare_task_id"] = prepared.get("task_id")
            state["prepared"] = bool(prepared.get("already_prepared"))
            _save_state(state_path, state)
        while not state.get("prepared"):
            status = client.post("/api/simulation/prepare/status",
                                 json_body={"simulation_id": state["simulation_id"],
                                            "task_id": state.get("prepare_task_id")}, timeout=30)
            value = status.get("status") or status.get("simulation_status")
            if value in {"ready", "completed"} or status.get("already_prepared") or status.get("is_ready"):
                state["prepared"] = True
                _save_state(state_path, state)
            elif value in {"failed", "error"}:
                raise ApiError(str(status.get("error") or "Vorbereitung fehlgeschlagen"))
            else:
                sleep(poll_interval)


def run_ensemble(client: ApiClient, outcomes: Sequence[Dict[str, Any]], state_path: Path,
                 state: Dict[str, Any], *, sleep: Callable[[float], None] = time.sleep,
                 poll_interval: float = 15.0) -> Dict[str, Any]:
    if not state.get("ensemble_id"):
        body = {"simulation_id": state["simulation_id"], "variants": list(state["arms"]),
                "runs": state["runs"], "hours": state["hours"],
                "minutes_per_round": state["minutes_per_round"],
                "custom_outcomes": blind_custom_outcomes(outcomes)}
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
        _save_state(state_path, state)
    resumes = 0
    while True:
        ensemble = client.get(f"/api/ensemble/{state['ensemble_id']}")
        status = ensemble.get("status")
        if status == "completed":
            state["ensemble_completed"] = True
            _save_state(state_path, state)
            return ensemble
        if status == "failed" and resumes < ENSEMBLE_RESUME_ATTEMPTS:
            resumes += 1
            client.post(f"/api/ensemble/{state['ensemble_id']}/resume", timeout=120)
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
                             kontaminiert: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    result = {"schema_version": 2, "case": case_name, "question": QUESTION, "runs": runs,
              "hours": hours, "minutes_per_round": minutes_per_round, "arms": list(arms),
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
                      minutes_per_round: int = 60) -> Dict[str, Any]:
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
                      and all(int(value.get("n") or 0) > 0 for value in arm_values.values()))
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
            "primary_outcome_id": primary_id,
            "contaminated": bool((contamination or {}).get("known", False)),
            "quellenluecke": any(item.get("quellenluecke") is True for item in outcomes),
            "contamination_check": contamination, "simulation_id": ensemble.get("simulation_id"),
            "ensemble_id": ensemble.get("ensemble_id"), "generated_at": datetime.now(timezone.utc).isoformat(),
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
              "Punkte mit Kappa < 0,6, ohne definiertes Kappa, ohne klassifizierte Läufe, mit Fenster "
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


def _summary_group(results: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    observations = []
    for result in results:
        row = next((item for item in result.get("rows", []) if item.get("primary") and item.get("measurable")), None)
        if row:
            observations.append({"case": result.get("case"), "actual": int(row["actual"]),
                                 "kappa": float(row["reliability"]["kappa"]),
                                 "p": {arm: float(row["arms"][arm]["rate"]) for arm in result["arms"]}})
    arms = [arm for arm in ALLOWED_ARMS if observations and all(arm in item["p"] for item in observations)]
    losses = [{arm: (item["p"][arm] - item["actual"]) ** 2 for arm in arms} for item in observations]
    brier = {arm: _rounded(sum(item[arm] for item in losses) / len(losses)) if losses else None for arm in arms}
    brier_ci = {arm: bootstrap_mean_ci([item[arm] for item in losses]) for arm in arms}
    skill = {}
    if "null_document" in arms:
        for arm in ("baseline", "null_personas"):
            if arm in arms:
                denominator = brier["null_document"]
                skill[f"{arm}_vs_null_document"] = {
                    "value": _rounded(None if not denominator else 1 - float(brier[arm]) / denominator),
                    "ci_95": _bootstrap_skill_ci(losses, arm, "null_document")}
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
    kappas = [item["kappa"] for item in observations]
    checks = {"skill_interval_above_zero": skill_above,
              "skill_interval_below_zero": skill_below,
              "kappa_at_least_0_6": None if not kappas else min(kappas) >= .6}
    if not pilot:
        slope = (calibration.get("baseline") or {}).get("slope")
        checks["calibration_slope_0_5_to_1_5"] = None if slope is None else .5 <= slope <= 1.5
    decisive = {key: value for key, value in checks.items() if key != "skill_interval_below_zero"}
    if skill_below is True:
        status = "nicht bestanden"
    elif any(value is False for value in decisive.values()):
        status = "nicht bestanden"
    elif any(value is None for value in decisive.values()):
        status = "nicht prüfbar"
    else:
        status = "bestanden"
    distances = []
    paired_cases = []
    for result in results:
        row = next((item for item in result.get("rows", []) if item.get("primary") and item.get("measurable")), None)
        distance = (result.get("primary_s_vs_p") or {}).get("distance")
        if row and isinstance(distance, (int, float)) and not isinstance(distance, bool):
            distances.append(float(distance))
            paired_cases.append({"case": result.get("case"),
                                 "table": result["primary_s_vs_p"].get("table"),
                                 "distance": round(float(distance), 6)})
    return {"case_count": len(results), "scored_primary_cases": len(observations), "arms": arms,
            "brier": brier, "brier_ci_95": brier_ci, "skill": skill, "calibration": calibration,
            "s_vs_p": {"mean_distance": _rounded(sum(distances) / len(distances)) if distances else None,
                       "ci_95": bootstrap_mean_ci(distances), "cases": paired_cases},
            "minimum_kappa": _rounded(min(kappas)) if kappas else None,
            "preregistered_criterion": {"status": status, "checks": checks}}


def _minutes_protocol(results: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    rows = [{"case": item.get("case"), "minutes_per_round": item["minutes_per_round"]}
            for item in results if isinstance(item.get("minutes_per_round"), int)
            and not isinstance(item.get("minutes_per_round"), bool)]
    return {"values": sorted({row["minutes_per_round"] for row in rows}), "cases": rows}


def build_summary(case_results: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    results = list(case_results)
    clean = [item for item in results if not item.get("contaminated", False)]
    # Ausschluss nur über das Feld, nie über den Ordnernamen.
    sensitivity = [item for item in clean if item.get("quellenluecke") is not True]
    sensitivity_group = _summary_group(sensitivity)
    sensitivity_group["replaces_primary"] = False
    contaminated = [item for item in results if item.get("contaminated", False)]
    declared = []
    for item in contaminated:
        flag = item.get("kontaminiert")
        if isinstance(flag, dict):
            declared.append({"case": item.get("case"), "quelle": flag.get("quelle"),
                             "datum": flag.get("datum")})
    return {"schema_version": 2, "generated_at": datetime.now(timezone.utc).isoformat(),
            "bootstrap_unit": "case", "bootstrap_seed": BOOTSTRAP_SEED,
            "bootstrap_samples": BOOTSTRAP_SAMPLES, "minutes_per_round": _minutes_protocol(results),
            "clean": _summary_group(clean),
            "sensitivity_no_source_gap": sensitivity_group,
            "source_gap_cases": [item.get("case") for item in clean if item.get("quellenluecke") is True],
            "contaminated": _summary_group(contaminated),
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
              "mit Fall-Bootstrap.", "",
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
    lines += ["## Vorab-Kriterium", "",
              f"**{criterion['status']}**. Der Pilotstatus hängt am Skill-Intervall S gegen D "
              "(vollständig über 0) und an Kappa ≥ 0,6. Liegt das Skill-Intervall ganz unter 0, "
              "ist der Status nicht bestanden, auch ohne Kalibrierungssteigung. "
              f"Die Steigung zählt unter {CALIBRATION_MIN_CASES} Fällen nicht als Bestehen.", "",
              contaminated_line]
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


def update_summary(results_dir: Path) -> Dict[str, Any]:
    results = []
    for path in sorted(results_dir.glob("*.json")):
        if path.name == "GESAMT.json" or path.name.endswith(".state.json"):
            continue
        payload = _load_json(path)
        if isinstance(payload, dict) and payload.get("schema_version") == 2 and (
                payload.get("rows") or payload.get("contaminated")):
            results.append(payload)
    summary = build_summary(results)
    _write_json_atomic(results_dir / "GESAMT.json", summary)
    _write_text_atomic(results_dir / "GESAMT.md", summary_markdown(summary))
    return summary


def _write_contaminated(results_dir: Path, case_name: str, result: Dict[str, Any], note: str) -> None:
    _write_json_atomic(results_dir / f"{case_name}.json", result)
    _write_text_atomic(results_dir / f"{case_name}.md", note)
    update_summary(results_dir)


def validate_case(case_dir: Path, *, runs: int = 10, hours: int = 336,
                  arms: Sequence[str] = DEFAULT_ARMS, base: str = "http://127.0.0.1:5002",
                  results_dir: Path = DEFAULT_RESULTS_DIR, client: Optional[ApiClient] = None,
                  contamination_checker: Any = None, location: Optional[str] = None,
                  year: Optional[str] = None, topic: Optional[str] = None,
                  minutes_per_round: int = 60,
                  sleep: Callable[[float], None] = time.sleep, poll_interval: float = 5.0) -> Dict[str, Any]:
    case_dir = case_dir.resolve()
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
            quellenluecke=annotations["quellenluecke"], kontaminiert=flag)
        _write_contaminated(
            results_dir, case_dir.name, result,
            f"# V5-Realitätsabgleich: {case_dir.name}\n\n"
            f"Vorab kontaminiert (Quelle: {flag['quelle']}, Datum: {flag['datum']}). "
            "Die Simulation wurde nicht gestartet.\n")
        raise ValueError(f"Fall {case_dir.name} ist vorab kontaminiert ({flag['quelle']}, {flag['datum']}); "
                         "Simulation nicht gestartet")
    state_path = results_dir / f"{case_dir.name}.state.json"
    state = load_or_create_state(state_path, case_dir.name, base, runs, hours, arms, minutes_per_round)
    if not state.get("contamination_check"):
        material = (case_dir / "ausgangslage.md").read_text(encoding="utf-8")
        state["contamination_check"] = check_contamination(
            case_identity(case_dir, location=location, year=year, topic=topic),
            contamination_checker, material=material)
        _save_state(state_path, state)
    if state["contamination_check"].get("known") is True:
        result = contaminated_case_result(
            case_dir.name, outcomes, state["contamination_check"], runs=runs, hours=hours, arms=arms,
            minutes_per_round=minutes_per_round, quellenluecke=annotations["quellenluecke"])
        _write_contaminated(
            results_dir, case_dir.name, result,
            f"# V5-Realitätsabgleich: {case_dir.name}\n\n"
            "Kontaminationsprüfung: **kennt den Fall**. "
            "Die Simulation wurde vor der Vorbereitung abgebrochen.\n")
        raise ValueError(f"Fall {case_dir.name} ist kontaminiert (Kaltfrage kennt: true); "
                         "Simulation vor der Vorbereitung abgebrochen")
    api = client or ApiClient(base)
    prepare_simulation(api, case_dir, state_path, state, sleep=sleep, poll_interval=poll_interval)
    ensemble = run_ensemble(api, outcomes, state_path, state, sleep=sleep, poll_interval=poll_interval)
    result = build_case_result(case_dir.name, outcomes, ensemble, runs=runs, hours=hours,
                               arms=arms, contamination=state["contamination_check"],
                               minutes_per_round=state["minutes_per_round"])
    _write_json_atomic(results_dir / f"{case_dir.name}.json", result)
    _write_text_atomic(results_dir / f"{case_dir.name}.md", case_markdown(result))
    update_summary(results_dir)
    return result


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_dir", type=Path, help="Ordner mit ausgangslage.md, verlauf.md und ergebnisse.json")
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--hours", type=int, default=336)
    parser.add_argument("--minutes-per-round", type=int, default=60, choices=ALLOWED_MINUTES_PER_ROUND,
                        help="Rundentakt in Minuten, an den Ensemble-Start durchgereicht")
    parser.add_argument("--arms", default=",".join(DEFAULT_ARMS), help="Kommagetrennte V5-Arme")
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
        result = validate_case(arguments.case_dir, runs=arguments.runs, hours=arguments.hours,
                               minutes_per_round=arguments.minutes_per_round,
                               arms=parse_arms(arguments.arms), base=arguments.base,
                               location=arguments.location, year=arguments.year, topic=arguments.topic,
                               **options)
    except (ApiError, OSError, ValueError) as error:
        print(f"Fehler: {error}", file=sys.stderr)
        return 1
    results_dir = arguments.results_dir or DEFAULT_RESULTS_DIR
    print(f"Auswertung geschrieben: {results_dir / (result['case'] + '.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
