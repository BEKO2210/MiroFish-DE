"""Startstimulus mit ehrlichem ``seen``: nur true, wenn ``update_memory`` gelang."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Sequence

from .blind_feed import deliver_opening_stimulus

logger = logging.getLogger(__name__)


class _RecordingAgent:
    def __init__(self, agent: Any, failures: Dict[int, str], agent_id: int):
        self._agent = agent
        self._failures = failures
        self._agent_id = agent_id

    def update_memory(self, *args: Any, **kwargs: Any) -> Any:
        try:
            return self._agent.update_memory(*args, **kwargs)
        except Exception as error:
            self._failures[self._agent_id] = str(error) or type(error).__name__
            return None


class _RecordingGraph:
    def __init__(self, graph: Any, failures: Dict[int, str]):
        self._graph = graph
        self._failures = failures

    def get_agents(self):
        return [
            (agent_id, _RecordingAgent(agent, self._failures, int(agent_id)))
            for agent_id, agent in self._graph.get_agents()
        ]


def deliver_opening_stimulus_checked(
    agent_graph: Any,
    posts: Sequence[Dict[str, Any]],
    log_path: str | Path,
    platform_name: str,
) -> Dict[str, Any]:
    """Wie ``deliver_opening_stimulus``, schreibt aber ``seen=false`` bei fehlgeschlagenem update_memory."""
    failures: Dict[int, str] = {}
    document = deliver_opening_stimulus(
        _RecordingGraph(agent_graph, failures), posts, log_path, platform_name
    )
    if failures:
        for entry in document["agents"]:
            agent_id = int(entry["agent_id"])
            if agent_id in failures:
                entry["seen"] = False
                entry["error"] = failures[agent_id]
        Path(log_path).write_text(
            json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.warning(
            "Startstimulus (%s): update_memory fehlgeschlagen für Agenten %s",
            platform_name,
            sorted(failures),
        )
    return document
