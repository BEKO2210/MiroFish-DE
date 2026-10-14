"""Gemeinsame, modellfreie Hilfen für Export und Import der Zweitbewertung."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

from app.services.ensemble import EnsembleService, load_simulation_posts, null_arm


CLASSIFICATION_SYSTEMS = {
    "Klassifiziere streng nur anhand der gelieferten Beiträge.": "posts",
    "Klassifiziere streng nur anhand der Erzählung.": "narrative",
}


def context_for_budget(token_budget: int) -> Dict[str, Any]:
    if token_budget < 1:
        raise ValueError("token-budget muss positiv sein")
    return {
        "model": "deferred",
        "num_ctx": token_budget + 4096,
        "num_ctx_source": "deferred_cli",
        "configured_input_budget": token_budget,
        "output_tokens": 3000,
        "buffer_tokens": 256,
        "input_budget": token_budget,
    }


class CaptureLLM:
    model = "deferred"

    def __init__(self, expected_ids: Sequence[str]) -> None:
        self.expected_ids = list(expected_ids)
        self.prompts: List[Dict[str, Any]] = []
        self.last_raw_response: Any = None

    def chat_json(self, messages: Sequence[Dict[str, str]], **_: Any) -> Dict[str, Any]:
        system, user = messages[0]["content"], messages[1]["content"]
        kind = CLASSIFICATION_SYSTEMS.get(system)
        if kind:
            self.prompts.append({
                "system": system,
                "user": user,
                "expected_ids": list(self.expected_ids),
                "kind": kind,
            })
            payload = {"results": [
                {"outcome_id": outcome_id, "yes": False}
                for outcome_id in self.expected_ids
            ]}
        else:
            # Hilfsabruf für Interaktionsgruppen; er gehört nicht zur Zweitbewertung.
            payload = {}
        self.last_raw_response = payload
        return payload


class ReplayLLM:
    model = "deferred"

    def __init__(self, answers: Dict[Tuple[str, str], Any]) -> None:
        self.answers = answers
        self.last_raw_response: Any = None

    def chat_json(self, messages: Sequence[Dict[str, str]], **_: Any) -> Dict[str, Any]:
        key = (messages[0]["content"], messages[1]["content"])
        if key not in self.answers:
            # Offline gibt es insbesondere für fehlende IDs keine Nachfrage.
            raise ValueError("Keine gespeicherte Offline-Antwort für diesen Prompt")
        value = self.answers[key]
        if isinstance(value, BaseException):
            raise value
        self.last_raw_response = value
        return value


def parse_answer(text: str) -> Dict[str, Any]:
    stripped = text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", stripped, re.DOTALL | re.IGNORECASE)
    if fenced:
        stripped = fenced.group(1)
    payload = json.loads(stripped)
    if not isinstance(payload, dict):
        raise ValueError("Antwort-JSON muss ein Objekt sein")
    return payload


def run_input(ensemble_dir: Path, arm: str, run_number: int) -> Tuple[Path, Any]:
    run_dir = ensemble_dir / arm / f"run_{run_number}"
    if null_arm(arm):
        path = run_dir / "narrative.txt"
        return run_dir, path.read_text(encoding="utf-8")
    config = json.loads((run_dir / "simulation_config.json").read_text(encoding="utf-8"))
    initial = (config.get("event_config") or {}).get("initial_posts") or []
    return run_dir, load_simulation_posts(run_dir, initial)


def capture_run_prompts(
    service: EnsembleService, state: Dict[str, Any], arm: str, run_number: int,
    source: Any, token_budget: int,
) -> List[Dict[str, Any]]:
    expected = [str(item["id"]) for item in state["checklist"]]
    llm = CaptureLLM(expected)
    context = context_for_budget(token_budget)
    if null_arm(arm):
        service._classify_narrative_once(
            state, source, 0, run_number, llm, arm, context,
        )
    else:
        service._classify_posts_once(
            state, source, 0, run_number, None, llm, context,
        )
    return llm.prompts


def replay_run(
    service: EnsembleService, state: Dict[str, Any], arm: str, run_number: int,
    source: Any, token_budget: int, prompt_answers: Sequence[Tuple[Dict[str, Any], Any]],
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    answers = {
        (prompt["system"], prompt["user"]): answer
        for prompt, answer in prompt_answers
    }
    llm = ReplayLLM(answers)
    context = context_for_budget(token_budget)
    if null_arm(arm):
        return service._classify_narrative_once(
            state, source, 0, run_number, llm, arm, context,
        )
    return service._classify_posts_once(
        state, source, 0, run_number, None, llm, context,
    )
