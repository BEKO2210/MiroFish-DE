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
ARM_LABELS = {"baseline": "Schwarm (S)", "null_document": "Dokument-Nullmodell (D)",
              "null_personas": "Persona-Nullmodell (P)", "isolated": "Isoliert"}
TERMINAL_ENSEMBLE_STATUSES = {"completed", "failed", "cancelled"}
BOOTSTRAP_SEED, BOOTSTRAP_SAMPLES = 20261014, 10_000
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
    if primary_count > 1:
        raise ValueError("ergebnisse.json darf höchstens eine Frage mit primaer: true enthalten")
    return outcomes


def blind_custom_outcomes(outcomes: Sequence[Dict[str, Any]]) -> List[Dict[str, str]]:
    return [{"text_de": str(outcome["text_de"]).strip()} for outcome in outcomes]


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


def check_contamination(identity: Dict[str, str], llm: Any = None) -> Dict[str, Any]:
    """Konfiguriertes Hauptmodell kalt, ohne Werkzeuge und ohne Ausgang fragen."""
    if llm is None:
        from app.utils.llm_client import LLMClient
        llm = LLMClient()
    prompt = ("Kennst du den folgenden realen kommunalpolitischen Fall aus deinem Vorwissen? "
              "Nutze keine Werkzeuge und recherchiere nicht. Antworte nur als JSON mit kennt "
              "(boolesch) und begruendung (kurzer Text).\n"
              f"Ort: {identity['location']}\nJahr: {identity['year']}\nThema: {identity['topic']}\n"
              "Der Ausgang wird absichtlich nicht genannt.")
    try:
        if callable(llm) and not hasattr(llm, "chat_json"):
            answer, model = llm(identity, prompt), getattr(llm, "model", "injected-checker")
        else:
            answer = llm.chat_json([{"role": "system", "content": "Prüfe nur vorhandenes Fallwissen."},
                                    {"role": "user", "content": prompt}],
                                   temperature=0, max_tokens=300, seed=BOOTSTRAP_SEED)
            model = getattr(llm, "model", "configured-main-model")
    except Exception as error:
        raise ApiError(f"Kontaminationsprüfung mit dem Hauptmodell fehlgeschlagen: {error}") from error
    if not isinstance(answer, dict):
        raise ValueError("Kontaminationsprüfung lieferte kein JSON-Objekt")
    known = answer.get("kennt", answer.get("known"))
    if not isinstance(known, bool):
        raise ValueError("Kontaminationsprüfung muss 'kennt' als booleschen Wert liefern")
    return {"checked_at": datetime.now(timezone.utc).isoformat(), "model": str(model),
            "identity": identity, "known": known, "answer": answer}


def _new_state(case_name: str, base: str, runs: int, hours: int, arms: Sequence[str]) -> Dict[str, Any]:
    return {"case": case_name, "base": base.rstrip("/"), "runs": runs, "hours": hours,
            "arms": list(arms), "question": QUESTION, "contamination_check": None,
            "project_id": None, "graph_task_id": None, "graph_id": None,
            "simulation_id": None, "prepare_task_id": None, "prepared": False,
            "ensemble_id": None, "ensemble_completed": False,
            "updated_at": datetime.now(timezone.utc).isoformat()}


def _save_state(path: Path, state: Dict[str, Any]) -> None:
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    _write_json_atomic(path, state)


def load_or_create_state(path: Path, case_name: str, base: str, runs: int, hours: int,
                         arms: Sequence[str] = DEFAULT_ARMS) -> Dict[str, Any]:
    if not path.is_file():
        state = _new_state(case_name, base, runs, hours, arms)
        _save_state(path, state)
        return state
    state = _load_json(path)
    expected = {"case": case_name, "base": base.rstrip("/"), "runs": runs, "hours": hours,
                "arms": list(arms), "question": QUESTION}
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


def build_case_result(case_name: str, outcomes: Sequence[Dict[str, Any]], ensemble: Dict[str, Any],
                      *, runs: int, hours: int, arms: Optional[Sequence[str]] = None,
                      contamination: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
        rel, in_material = reliability.get(outcome_id) or {}, bool(item.get("in_material", False))
        kappa = rel.get("kappa")
        measurable = (isinstance(kappa, (int, float)) and float(kappa) >= .6 and not in_material
                      and all(int(value.get("n") or 0) > 0 for value in arm_values.values()))
        rows.append({"outcome_id": outcome_id, "question": text,
                     "primary": outcome.get("primaer") is True,
                     "actual": int(outcome["eingetreten"]), "source": outcome.get("quelle"),
                     "in_material": in_material, "arms": arm_values,
                     "reliability": {key: rel.get(key) for key in ("agreement", "kappa", "n_pairs", "label")},
                     "measurable": measurable})
    def metrics(selected: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
        actual = [row["actual"] for row in selected]
        return {arm: metric_set([float(row["arms"][arm]["rate"]) for row in selected], actual) for arm in arms}
    scored = [row for row in rows if row["measurable"]]
    primary = [row for row in scored if row["primary"]]
    return {"schema_version": 2, "case": case_name, "question": QUESTION, "runs": runs,
            "hours": hours, "arms": arms,
            "primary_outcome_id": next((row["outcome_id"] for row in rows if row["primary"]), None),
            "contaminated": bool((contamination or {}).get("known", False)),
            "contamination_check": contamination, "simulation_id": ensemble.get("simulation_id"),
            "ensemble_id": ensemble.get("ensemble_id"), "generated_at": datetime.now(timezone.utc).isoformat(),
            "rows": rows, "metrics": metrics(scored), "primary_metrics": metrics(primary)}


def _display(value: Any, percent: bool = False) -> str:
    return "–" if value is None else (f"{float(value):.1%}" if percent else f"{float(value):.4f}")


def _escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def case_markdown(result: Dict[str, Any]) -> str:
    arms, check = result["arms"], result.get("contamination_check") or {}
    lines = [f"# V5-Realitätsabgleich: {result['case']}", "", f"Neutrale Frage: „{QUESTION}“", "",
             f"Kontaminationsprüfung: **{'kennt den Fall' if result['contaminated'] else 'kennt den Fall nicht'}** "
             f"(Modell: {_escape(check.get('model', '–'))}).", "",
             f"{result['runs']} Läufe je Arm, {result['hours']} simulierte Stunden. Wahrheitswert, Quellen und "
             "tatsächlicher Verlauf wurden nicht an die Simulation gesendet.", "",
             "| Ergebnis | Typ | tatsächlich | " + " | ".join(ARM_LABELS[a] for a in arms) + " | Kappa |",
             "|---|---|---:|" + "---:|" * len(arms) + "---:|"]
    for row in result["rows"]:
        values = [f"{row['arms'][arm]['yes']}/{row['arms'][arm]['n']} ({float(row['arms'][arm]['rate']):.1%})" for arm in arms]
        lines.append(f"| {_escape(row['question'])} | {'primär' if row['primary'] else 'explorativ'} | {row['actual']} | "
                     + " | ".join(values) + f" | {_display(row['reliability'].get('kappa'))} |")
    lines += ["", "## Brier-Score je Arm", "", "| Arm | alle messbaren Ergebnisse | Primärergebnis |", "|---|---:|---:|"]
    for arm in arms:
        lines.append(f"| {ARM_LABELS[arm]} | {_display(result['metrics'][arm]['brier'])} | "
                     f"{_display(result['primary_metrics'][arm]['brier'])} |")
    lines += ["", "Das Primärergebnis ist konfirmatorisch; alle anderen Ergebnisse sind explorativ. "
              "Punkte mit Kappa < 0,6, ohne klassifizierte Läufe oder bereits im T0-Material enthaltene "
              "Punkte werden nicht gescored."]
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
    for arm in arms:
        slope = calibration_slope([item["p"][arm] for item in observations],
                                  [item["actual"] for item in observations]) if len(observations) >= 8 else None
        calibration[arm] = {"slope": _rounded(slope),
                            "note": None if len(observations) >= 8 else "Pilot, keine Kalibrierungsaussage"}
    interval = (skill.get("baseline_vs_null_document") or {}).get("ci_95")
    slope = (calibration.get("baseline") or {}).get("slope")
    kappas = [item["kappa"] for item in observations]
    checks = {"skill_interval_above_zero": None if interval is None else interval["low"] > 0,
              "calibration_slope_0_5_to_1_5": None if slope is None else .5 <= slope <= 1.5,
              "kappa_at_least_0_6": None if not kappas else min(kappas) >= .6}
    status = ("nicht bestanden" if any(value is False for value in checks.values())
              else "nicht prüfbar" if any(value is None for value in checks.values())
              else "bestanden")
    return {"case_count": len(results), "scored_primary_cases": len(observations), "arms": arms,
            "brier": brier, "brier_ci_95": brier_ci, "skill": skill, "calibration": calibration,
            "minimum_kappa": _rounded(min(kappas)) if kappas else None,
            "preregistered_criterion": {"status": status, "checks": checks}}


def build_summary(case_results: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    results = list(case_results)
    clean = [item for item in results if not item.get("contaminated", False)]
    contaminated = [item for item in results if item.get("contaminated", False)]
    return {"schema_version": 2, "generated_at": datetime.now(timezone.utc).isoformat(),
            "bootstrap_unit": "case", "bootstrap_seed": BOOTSTRAP_SEED,
            "bootstrap_samples": BOOTSTRAP_SAMPLES, "clean": _summary_group(clean),
            "contaminated": _summary_group(contaminated),
            "contaminated_cases": [item.get("case") for item in contaminated]}


def summary_markdown(summary: Dict[str, Any]) -> str:
    group = summary["clean"]
    lines = ["# V5-Realitätsabgleich – Gesamt", "",
             f"{group['scored_primary_cases']} nicht kontaminierte Fälle mit messbarem Primärergebnis. "
             f"Bootstrap über **Fälle** ({summary['bootstrap_samples']} Ziehungen, Seed {summary['bootstrap_seed']}).",
             "", "| Arm | Brier-Score | 95-%-Fall-Bootstrap-KI | Kalibrierungssteigung |",
             "|---|---:|---:|---:|"]
    for arm in group["arms"]:
        cal = group["calibration"][arm]
        interval = group["brier_ci_95"][arm]
        rendered = f"{interval['low']:.4f}–{interval['high']:.4f}" if interval else "–"
        lines.append(f"| {ARM_LABELS[arm]} | {_display(group['brier'][arm])} | {rendered} | "
                     f"{cal['note'] or _display(cal['slope'])} |")
    lines += ["", "## Skill gegen Dokument-Nullmodell (D)", "",
              "| Kontrast | Skill | 95-%-Fall-Bootstrap-KI |", "|---|---:|---:|"]
    for name, item in group["skill"].items():
        interval = item["ci_95"]
        rendered = f"{interval['low']:.4f}–{interval['high']:.4f}" if interval else "–"
        lines.append(f"| {name} | {_display(item['value'])} | {rendered} |")
    criterion = group["preregistered_criterion"]
    lines += ["", "## Vorab-Kriterium", "", f"**{criterion['status']}**: Skill-Intervall vollständig über 0, "
              "Kalibrierungssteigung in [0,5; 1,5] und Kappa ≥ 0,6.", "",
              f"Kontaminierte Fälle ({summary['contaminated']['case_count']}): "
              + (", ".join(summary["contaminated_cases"]) or "keine")
              + ". Sie sind aus der Hauptauswertung ausgeschlossen und im JSON getrennt ausgewiesen."]
    return "\n".join(lines) + "\n"


def update_summary(results_dir: Path) -> Dict[str, Any]:
    results = []
    for path in sorted(results_dir.glob("*.json")):
        if path.name == "GESAMT.json" or path.name.endswith(".state.json"):
            continue
        payload = _load_json(path)
        if isinstance(payload, dict) and payload.get("schema_version") == 2 and payload.get("rows"):
            results.append(payload)
    summary = build_summary(results)
    _write_json_atomic(results_dir / "GESAMT.json", summary)
    _write_text_atomic(results_dir / "GESAMT.md", summary_markdown(summary))
    return summary


def validate_case(case_dir: Path, *, runs: int = 10, hours: int = 168,
                  arms: Sequence[str] = DEFAULT_ARMS, base: str = "http://127.0.0.1:5002",
                  results_dir: Path = DEFAULT_RESULTS_DIR, client: Optional[ApiClient] = None,
                  contamination_checker: Any = None, location: Optional[str] = None,
                  year: Optional[str] = None, topic: Optional[str] = None,
                  sleep: Callable[[float], None] = time.sleep, poll_interval: float = 5.0) -> Dict[str, Any]:
    case_dir = case_dir.resolve()
    validate_case_files(case_dir)
    arms = parse_arms(arms)
    if isinstance(runs, bool) or not 1 <= runs <= 100:
        raise ValueError("runs muss zwischen 1 und 100 liegen")
    if isinstance(hours, bool) or not 1 <= hours <= 336:
        raise ValueError("hours muss zwischen 1 und 336 liegen")
    outcomes = load_outcomes(case_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    state_path = results_dir / f"{case_dir.name}.state.json"
    state = load_or_create_state(state_path, case_dir.name, base, runs, hours, arms)
    if not state.get("contamination_check"):
        state["contamination_check"] = check_contamination(
            case_identity(case_dir, location=location, year=year, topic=topic), contamination_checker)
        _save_state(state_path, state)
    api = client or ApiClient(base)
    prepare_simulation(api, case_dir, state_path, state, sleep=sleep, poll_interval=poll_interval)
    ensemble = run_ensemble(api, outcomes, state_path, state, sleep=sleep, poll_interval=poll_interval)
    result = build_case_result(case_dir.name, outcomes, ensemble, runs=runs, hours=hours,
                               arms=arms, contamination=state["contamination_check"])
    _write_json_atomic(results_dir / f"{case_dir.name}.json", result)
    _write_text_atomic(results_dir / f"{case_dir.name}.md", case_markdown(result))
    update_summary(results_dir)
    return result


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_dir", type=Path, help="Ordner mit ausgangslage.md, verlauf.md und ergebnisse.json")
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--hours", type=int, default=168)
    parser.add_argument("--arms", default=",".join(DEFAULT_ARMS), help="Kommagetrennte V5-Arme")
    parser.add_argument("--base", default="http://127.0.0.1:5002")
    parser.add_argument("--ort", dest="location")
    parser.add_argument("--jahr", dest="year")
    parser.add_argument("--thema", dest="topic")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = parse_args(argv)
    try:
        result = validate_case(arguments.case_dir, runs=arguments.runs, hours=arguments.hours,
                               arms=parse_arms(arguments.arms), base=arguments.base,
                               location=arguments.location, year=arguments.year, topic=arguments.topic)
    except (ApiError, OSError, ValueError) as error:
        print(f"Fehler: {error}", file=sys.stderr)
        return 1
    print(f"Auswertung geschrieben: {DEFAULT_RESULTS_DIR / (result['case'] + '.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
