"""
Basis-Klasse für Memory-Provider
Definiert das Interface für verschiedene Wissensgraphen-Backends (Zep, Obsidian, Hybrid)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class MemoryNode:
    """Universelle Knoten-Struktur"""
    uuid: str
    name: str
    labels: List[str]
    summary: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[str] = None

@dataclass
class MemoryEdge:
    """Universelle Kanten-Struktur"""
    uuid: str
    name: str
    fact: str
    source_node_uuid: str
    target_node_uuid: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[str] = None
    valid_at: Optional[str] = None
    invalid_at: Optional[str] = None
    expired_at: Optional[str] = None

@dataclass
class MemorySearchResult:
    """Universelles Suchergebnis"""
    query: str
    facts: List[str] = field(default_factory=list)
    nodes: List[MemoryNode] = field(default_factory=list)
    edges: List[MemoryEdge] = field(default_factory=list)
    total_count: int = 0

class MemoryProvider(ABC):
    """Abstrakte Basisklasse für Memory-Provider"""
    
    @abstractmethod
    def initialize(self, simulation_id: str, graph_name: str = "MiroFish Graph") -> str:
        """Initialisiert den Speicher (z.B. Graph erstellen oder Ordner anlegen)"""
        pass

    @abstractmethod
    def set_ontology(self, graph_id: str, ontology: Dict[str, Any]):
        """Setzt die Ontologie-Definition für den Graphen"""
        pass

    @abstractmethod
    def add_text(self, graph_id: str, text: str, metadata: Dict[str, Any] = None) -> str:
        """Fügt einen Textblock zum Speicher hinzu (für Extraktion)"""
        pass

    @abstractmethod
    def add_activity(self, graph_id: str, agent_name: str, activity_desc: str):
        """Fügt eine Agenten-Aktivität zum Speicher hinzu"""
        pass

    @abstractmethod
    def fetch_nodes(self, graph_id: str) -> List[MemoryNode]:
        """Ruft alle Knoten ab"""
        pass

    @abstractmethod
    def fetch_edges(self, graph_id: str) -> List[MemoryEdge]:
        """Ruft alle Kanten ab"""
        pass

    @abstractmethod
    def fetch_node_edges(self, graph_id: str, node_uuid: str) -> List[MemoryEdge]:
        """Ruft alle Kanten eines bestimmten Knotens ab"""
        pass

    @abstractmethod
    def search(self, graph_id: str, query: str, limit: int = 10, scope: str = "edges") -> MemorySearchResult:
        """Führt eine semantische oder Keyword-Suche durch"""
        pass

    @abstractmethod
    def get_node_detail(self, graph_id: str, node_uuid: str) -> Optional[MemoryNode]:
        """Ruft Details zu einem einzelnen Knoten ab"""
        pass

    @abstractmethod
    def delete_graph(self, graph_id: str):
        """Löscht den Graphen oder den Speicherbereich"""
        pass

    @abstractmethod
    def healthcheck(self) -> Dict[str, Any]:
        """Prüft die Verfügbarkeit des Backends"""
        pass
