"""
Hybrid-Memory-Provider
Kombiniert lokale Markdown-Dateien (Obsidian) mit Zep Cloud für optimale Retrieval-Performance und menschliche Lesbarkeit
"""

from typing import Dict, Any, List, Optional
from .base import MemoryProvider, MemoryNode, MemoryEdge, MemorySearchResult
from .zep_provider import ZepMemoryProvider
from .obsidian_provider import ObsidianMemoryProvider
from ...utils.logger import get_logger

logger = get_logger('mirofish.memory.hybrid')

class HybridMemoryProvider(MemoryProvider):
    """Hybrid-Provider: Schreibt in beide, sucht bevorzugt in Zep"""
    
    def __init__(self):
        self.zep = ZepMemoryProvider()
        self.obsidian = ObsidianMemoryProvider()

    def initialize(self, simulation_id: str, graph_name: str = "MiroFish Graph") -> str:
        # Obsidian initialisieren (gibt simulation_id zurück)
        self.obsidian.initialize(simulation_id, graph_name)
        # Zep initialisieren (gibt eigene graph_id zurück)
        zep_id = self.zep.initialize(simulation_id, graph_name)
        return zep_id # Wir nutzen die Zep-ID als primäre graph_id

    def set_ontology(self, graph_id: str, ontology: Dict[str, Any]):
        self.obsidian.set_ontology(graph_id, ontology)
        self.zep.set_ontology(graph_id, ontology)

    def add_text(self, graph_id: str, text: str, metadata: Dict[str, Any] = None) -> str:
        # In beide schreiben
        self.obsidian.add_text(graph_id, text, metadata)
        return self.zep.add_text(graph_id, text, metadata)

    def add_activity(self, graph_id: str, agent_name: str, activity_desc: str):
        self.obsidian.add_activity(graph_id, agent_name, activity_desc)
        self.zep.add_activity(graph_id, agent_name, activity_desc)

    def fetch_nodes(self, graph_id: str) -> List[MemoryNode]:
        # Bevorzugt Zep da reichhaltiger
        try:
            return self.zep.fetch_nodes(graph_id)
        except Exception:
            return self.obsidian.fetch_nodes(graph_id)

    def fetch_edges(self, graph_id: str) -> List[MemoryEdge]:
        try:
            return self.zep.fetch_edges(graph_id)
        except Exception:
            return self.obsidian.fetch_edges(graph_id)

    def search(self, graph_id: str, query: str, limit: int = 10, scope: str = "edges") -> MemorySearchResult:
        # Bevorzugt Zep (Semantisch)
        try:
            return self.zep.search(graph_id, query, limit, scope)
        except Exception:
            return self.obsidian.search(graph_id, query, limit, scope)

    def get_node_detail(self, graph_id: str, node_uuid: str) -> Optional[MemoryNode]:
        try:
            return self.zep.get_node_detail(graph_id, node_uuid)
        except Exception:
            return self.obsidian.get_node_detail(graph_id, node_uuid)

    def delete_graph(self, graph_id: str):
        self.zep.delete_graph(graph_id)
        self.obsidian.delete_graph(graph_id)

    def healthcheck(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "provider": "hybrid",
            "zep": self.zep.healthcheck(),
            "obsidian": self.obsidian.healthcheck()
        }
