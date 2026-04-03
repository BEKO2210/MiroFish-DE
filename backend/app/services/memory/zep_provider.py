"""
Zep-Wissensgraph-Provider
Implementiert das MemoryProvider-Interface unter Verwendung der Zep Cloud API
"""

import uuid
from typing import Dict, Any, List, Optional
from zep_cloud.client import Zep
from zep_cloud import EpisodeData

from .base import MemoryProvider, MemoryNode, MemoryEdge, MemorySearchResult
from ...config import Config
from ...utils.logger import get_logger
from ...utils.zep_paging import fetch_all_nodes, fetch_all_edges

logger = get_logger('mirofish.memory.zep')

class ZepMemoryProvider(MemoryProvider):
    """Memory-Provider für Zep Cloud"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or Config.ZEP_API_KEY
        if not self.api_key:
            raise ValueError("ZEP_API_KEY nicht konfiguriert")
        self.client = Zep(api_key=self.api_key)

    def initialize(self, simulation_id: str, graph_name: str = "MiroFish Graph") -> str:
        """Erstellt einen neuen Zep-Graphen"""
        graph_id = f"mirofish_{uuid.uuid4().hex[:16]}"
        self.client.graph.create(
            graph_id=graph_id,
            name=graph_name,
            description=f"Simulation {simulation_id}"
        )
        return graph_id

    def set_ontology(self, graph_id: str, ontology: Dict[str, Any]):
        """Delegiert an die Logik von GraphBuilderService (wird dort refactored)"""
        # Hier nutzen wir vorerst die Logik aus GraphBuilderService
        # Da diese komplex ist und Pydantic-Klassen generiert, 
        # belassen wir sie vorerst dort und rufen sie ggf. über einen Helper auf.
        # Aber für das Interface implementieren wir es hier.
        from ..graph_builder import GraphBuilderService
        builder = GraphBuilderService(api_key=self.api_key)
        builder.set_ontology(graph_id, ontology)

    def add_text(self, graph_id: str, text: str, metadata: Dict[str, Any] = None) -> str:
        """Fügt Text zum Zep-Graphen hinzu"""
        episodes = [EpisodeData(data=text, type="text")]
        result = self.client.graph.add_batch(graph_id=graph_id, episodes=episodes)
        if result and isinstance(result, list) and len(result) > 0:
            return getattr(result[0], 'uuid_', '') or getattr(result[0], 'uuid', '')
        return ""

    def add_activity(self, graph_id: str, agent_name: str, activity_desc: str):
        """Fügt Agenten-Aktivität als Text-Episode hinzu"""
        combined_text = f"{agent_name}: {activity_desc}"
        self.client.graph.add(
            graph_id=graph_id,
            type="text",
            data=combined_text
        )

    def fetch_nodes(self, graph_id: str) -> List[MemoryNode]:
        """Ruft alle Knoten ab und konvertiert sie"""
        zep_nodes = fetch_all_nodes(self.client, graph_id)
        return [
            MemoryNode(
                uuid=getattr(n, 'uuid_', '') or getattr(n, 'uuid', ''),
                name=n.name or "",
                labels=n.labels or [],
                summary=n.summary or "",
                attributes=n.attributes or {},
                created_at=str(getattr(n, 'created_at', ''))
            ) for n in zep_nodes
        ]

    def fetch_edges(self, graph_id: str) -> List[MemoryEdge]:
        """Ruft alle Kanten ab und konvertiert sie"""
        zep_edges = fetch_all_edges(self.client, graph_id)
        return [
            MemoryEdge(
                uuid=getattr(e, 'uuid_', '') or getattr(e, 'uuid', ''),
                name=e.name or "",
                fact=e.fact or "",
                source_node_uuid=e.source_node_uuid or "",
                target_node_uuid=e.target_node_uuid or "",
                attributes=e.attributes or {},
                created_at=str(getattr(e, 'created_at', '')),
                valid_at=str(getattr(e, 'valid_at', '')) if getattr(e, 'valid_at', None) else None,
                invalid_at=str(getattr(e, 'invalid_at', '')) if getattr(e, 'invalid_at', None) else None,
                expired_at=str(getattr(e, 'expired_at', '')) if getattr(e, 'expired_at', None) else None
            ) for e in zep_edges
        ]

    def fetch_node_edges(self, graph_id: str, node_uuid: str) -> List[MemoryEdge]:
        """Ruft alle Kanten eines bestimmten Knotens ab"""
        try:
            zep_edges = self.client.graph.node.get_entity_edges(node_uuid=node_uuid)
            return [
                MemoryEdge(
                    uuid=getattr(e, 'uuid_', '') or getattr(e, 'uuid', ''),
                    name=e.name or "",
                    fact=e.fact or "",
                    source_node_uuid=e.source_node_uuid or "",
                    target_node_uuid=e.target_node_uuid or "",
                    attributes=e.attributes or {},
                    created_at=str(getattr(e, 'created_at', ''))
                ) for e in zep_edges
            ]
        except Exception:
            return []

    def search(self, graph_id: str, query: str, limit: int = 10, scope: str = "edges") -> MemorySearchResult:
        """Führt eine Zep-Suche durch"""
        try:
            search_results = self.client.graph.search(
                graph_id=graph_id,
                query=query,
                limit=limit,
                scope=scope
            )
            
            facts = []
            nodes = []
            edges = []
            
            if hasattr(search_results, 'edges') and search_results.edges:
                for e in search_results.edges:
                    facts.append(getattr(e, 'fact', ''))
                    edges.append(MemoryEdge(
                        uuid=getattr(e, 'uuid_', '') or getattr(e, 'uuid', ''),
                        name=getattr(e, 'name', ''),
                        fact=getattr(e, 'fact', ''),
                        source_node_uuid=getattr(e, 'source_node_uuid', ''),
                        target_node_uuid=getattr(e, 'target_node_uuid', '')
                    ))
            
            if hasattr(search_results, 'nodes') and search_results.nodes:
                for n in search_results.nodes:
                    nodes.append(MemoryNode(
                        uuid=getattr(n, 'uuid_', '') or getattr(n, 'uuid', ''),
                        name=getattr(n, 'name', ''),
                        labels=getattr(n, 'labels', []),
                        summary=getattr(n, 'summary', '')
                    ))
                    if getattr(n, 'summary', None):
                        facts.append(f"[{n.name}]: {n.summary}")
            
            return MemorySearchResult(
                query=query,
                facts=facts,
                nodes=nodes,
                edges=edges,
                total_count=len(facts)
            )
        except Exception as e:
            logger.error(f"Zep-Suche fehlgeschlagen: {e}")
            return MemorySearchResult(query=query)

    def get_node_detail(self, graph_id: str, node_uuid: str) -> Optional[MemoryNode]:
        """Ruft Details eines Knotens ab"""
        try:
            n = self.client.graph.node.get(uuid_=node_uuid)
            if not n: return None
            return MemoryNode(
                uuid=getattr(n, 'uuid_', '') or getattr(n, 'uuid', ''),
                name=n.name or "",
                labels=n.labels or [],
                summary=n.summary or "",
                attributes=n.attributes or {}
            )
        except Exception:
            return None

    def delete_graph(self, graph_id: str):
        """Löscht den Zep-Graphen"""
        self.client.graph.delete(graph_id=graph_id)

    def healthcheck(self) -> Dict[str, Any]:
        """Prüft Zep-Status"""
        try:
            # Einfacher API-Aufruf zum Testen
            self.client.graph.list()
            return {"status": "ok", "provider": "zep"}
        except Exception as e:
            return {"status": "error", "provider": "zep", "error": str(e)}
