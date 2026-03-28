"""
Zep-Retrieval-Tool-Service
Kapselt Tools für Graph-Suche, Node-Lesen, Edge-Abfrage usw. für die Nutzung durch den Report Agent

Kern-Retrieval-Tools (optimiert):
1. InsightForge (Tiefen-Einblick-Retrieval) - Stärkste hybride Suche, automatische Sub-Problem-Generierung und mehrdimensionale Suche
2. PanoramaSearch (Breitensuche) - Vollständige Übersicht erhalten, einschließlich abgelaufener Inhalte
3. QuickSearch (einfache Suche) - Schnelle Suche
"""

import time
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from zep_cloud.client import Zep

from ..config import Config
from ..utils.logger import get_logger
from ..utils.llm_client import LLMClient
from ..utils.zep_paging import fetch_all_nodes, fetch_all_edges

logger = get_logger('mirofish.zep_tools')


@dataclass
class SearchResult:
    """Suchergebnis"""
    facts: List[str]
    edges: List[Dict[str, Any]]
    nodes: List[Dict[str, Any]]
    query: str
    total_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "facts": self.facts,
            "edges": self.edges,
            "nodes": self.nodes,
            "query": self.query,
            "total_count": self.total_count
        }
    
    def to_text(self) -> str:
        """In Textformat konvertieren für LLM-Verständnis"""
        text_parts = [f"Suchanfrage: {self.query}", f"{self.total_count} relevante Informationen gefunden"]
        
        if self.facts:
            text_parts.append("\n### Relevante Fakten:")
            for i, fact in enumerate(self.facts, 1):
                text_parts.append(f"{i}. {fact}")
        
        return "\n".join(text_parts)


@dataclass
class NodeInfo:
    """Node-Information"""
    uuid: str
    name: str
    labels: List[str]
    summary: str
    attributes: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "uuid": self.uuid,
            "name": self.name,
            "labels": self.labels,
            "summary": self.summary,
            "attributes": self.attributes
        }
    
    def to_text(self) -> str:
        """In Textformat konvertieren"""
        entity_type = next((l for l in self.labels if l not in ["Entity", "Node"]), "Unbekannter Typ")
        return f"Entität: {self.name} (Typ: {entity_type})\nZusammenfassung: {self.summary}"


@dataclass
class EdgeInfo:
    """Edge-Information"""
    uuid: str
    name: str
    fact: str
    source_node_uuid: str
    target_node_uuid: str
    source_node_name: Optional[str] = None
    target_node_name: Optional[str] = None
    # Zeitinformationen
    created_at: Optional[str] = None
    valid_at: Optional[str] = None
    invalid_at: Optional[str] = None
    expired_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "uuid": self.uuid,
            "name": self.name,
            "fact": self.fact,
            "source_node_uuid": self.source_node_uuid,
            "target_node_uuid": self.target_node_uuid,
            "source_node_name": self.source_node_name,
            "target_node_name": self.target_node_name,
            "created_at": self.created_at,
            "valid_at": self.valid_at,
            "invalid_at": self.invalid_at,
            "expired_at": self.expired_at
        }
    
    def to_text(self, include_temporal: bool = False) -> str:
        """In Textformat konvertieren"""
        source = self.source_node_name or self.source_node_uuid[:8]
        target = self.target_node_name or self.target_node_uuid[:8]
        base_text = f"Beziehung: {source} --[{self.name}]--> {target}\nFakt: {self.fact}"
        
        if include_temporal:
            valid_at = self.valid_at or "Unbekannt"
            invalid_at = self.invalid_at or "Bis heute"
            base_text += f"\nGültigkeit: {valid_at} - {invalid_at}"
            if self.expired_at:
                base_text += f" (Abgelaufen: {self.expired_at})"
        
        return base_text
    
    @property
    def is_expired(self) -> bool:
        """Ob abgelaufen"""
        return self.expired_at is not None
    
    @property
    def is_invalid(self) -> bool:
        """Ob ungültig"""
        return self.invalid_at is not None


@dataclass
class InsightForgeResult:
    """
    Tiefen-Einblick-Retrieval-Ergebnis (InsightForge)
    Enthält Suchergebnisse für mehrere Sub-Probleme sowie synthetische Analyse
    """
    query: str
    simulation_requirement: str
    sub_queries: List[str]
    
    # Retrieval-Ergebnisse verschiedener Dimensionen
    semantic_facts: List[str] = field(default_factory=list)  # Semantische Suchergebnisse
    entity_insights: List[Dict[str, Any]] = field(default_factory=list)  # Entitäts-Einblicke
    relationship_chains: List[str] = field(default_factory=list)  # Beziehungsketten
    
    # Statistiken
    total_facts: int = 0
    total_entities: int = 0
    total_relationships: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "simulation_requirement": self.simulation_requirement,
            "sub_queries": self.sub_queries,
            "semantic_facts": self.semantic_facts,
            "entity_insights": self.entity_insights,
            "relationship_chains": self.relationship_chains,
            "total_facts": self.total_facts,
            "total_entities": self.total_entities,
            "total_relationships": self.total_relationships
        }
    
    def to_text(self) -> str:
        """In detailliertes Textformat konvertieren für LLM-Verständnis und Berichtszitate"""
        text_parts = [
            f"## Zukunftsprognose-Tiefenanalyse",
            f"Analysefrage: {self.query}",
            f"Prognoseszenario: {self.simulation_requirement}",
            f"\n### Prognose-Datenstatistik",
            f"- Relevante Prognose-Fakten: {self.total_facts}",
            f"- Beteiligte Entitäten: {self.total_entities}",
            f"- Beziehungsketten: {self.total_relationships}"
        ]
        
        # Sub-Probleme
        if self.sub_queries:
            text_parts.append(f"\n### Analysierte Sub-Probleme")
            for i, sq in enumerate(self.sub_queries, 1):
                text_parts.append(f"{i}. {sq}")
        
        # Semantische Suchergebnisse
        if self.semantic_facts:
            text_parts.append(f"\n### 【Wichtige Fakten】(Bitte zitieren Sie diese Originaltexte im Bericht)")
            for i, fact in enumerate(self.semantic_facts, 1):
                text_parts.append(f"{i}. \"{fact}\"")
        
        # Entitäts-Einblicke
        if self.entity_insights:
            text_parts.append(f"\n### 【Kernentitäten】")
            for entity in self.entity_insights:
                text_parts.append(f"- **{entity.get('name', 'Unbekannt')}** ({entity.get('type', 'Entität')})")
                if entity.get('summary'):
                    text_parts.append(f"  Zusammenfassung: \"{entity.get('summary')}\"")
                if entity.get('related_facts'):
                    text_parts.append(f"  Verwandte Fakten: {len(entity.get('related_facts', []))}")
        
        # Beziehungsketten
        if self.relationship_chains:
            text_parts.append(f"\n### 【Beziehungsketten】")
            for chain in self.relationship_chains:
                text_parts.append(f"- {chain}")
        
        return "\n".join(text_parts)


@dataclass
class PanoramaResult:
    """
    Breitensuchergebnis (Panorama)
    Enthält alle relevanten Informationen, einschließlich abgelaufener Inhalte
    """
    query: str
    
    # Alle Nodes
    all_nodes: List[NodeInfo] = field(default_factory=list)
    # Alle Edges (einschließlich abgelaufener)
    all_edges: List[EdgeInfo] = field(default_factory=list)
    # Aktuell gültige Fakten
    active_facts: List[str] = field(default_factory=list)
    # Abgelaufene/ungültige Fakten (Historie)
    historical_facts: List[str] = field(default_factory=list)
    
    # Statistiken
    total_nodes: int = 0
    total_edges: int = 0
    active_count: int = 0
    historical_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "all_nodes": [n.to_dict() for n in self.all_nodes],
            "all_edges": [e.to_dict() for e in self.all_edges],
            "active_facts": self.active_facts,
            "historical_facts": self.historical_facts,
            "total_nodes": self.total_nodes,
            "total_edges": self.total_edges,
            "active_count": self.active_count,
            "historical_count": self.historical_count
        }
    
    def to_text(self) -> str:
        """In Textformat konvertieren (vollständige Version, nicht abgeschnitten)"""
        text_parts = [
            f"## Breitensuchergebnis (Zukunftspanorama-Ansicht)",
            f"Anfrage: {self.query}",
            f"\n### Statistiken",
            f"- Gesamte Nodes: {self.total_nodes}",
            f"- Gesamte Edges: {self.total_edges}",
            f"- Aktuell gültige Fakten: {self.active_count}",
            f"- Historische/abgelaufene Fakten: {self.historical_count}"
        ]
        
        # Aktuell gültige Fakten (vollständige Ausgabe, nicht abgeschnitten)
        if self.active_facts:
            text_parts.append(f"\n### 【Aktuell gültige Fakten】(Simulationsergebnis-Originaltext)")
            for i, fact in enumerate(self.active_facts, 1):
                text_parts.append(f"{i}. \"{fact}\"")
        
        # Historische/abgelaufene Fakten (vollständige Ausgabe, nicht abgeschnitten)
        if self.historical_facts:
            text_parts.append(f"\n### 【Historische/abgelaufene Fakten】(Evolutionsprozess-Aufzeichnung)")
            for i, fact in enumerate(self.historical_facts, 1):
                text_parts.append(f"{i}. \"{fact}\"")
        
        # Wichtige Entitäten (vollständige Ausgabe, nicht abgeschnitten)
        if self.all_nodes:
            text_parts.append(f"\n### 【Beteiligte Entitäten】")
            for node in self.all_nodes:
                entity_type = next((l for l in node.labels if l not in ["Entity", "Node"]), "Entität")
                text_parts.append(f"- **{node.name}** ({entity_type})")
        
        return "\n".join(text_parts)


@dataclass
class AgentInterview:
    """Einzelnes Agent-Interview-Ergebnis"""
    agent_name: str
    agent_role: str  # Rollentyp (z.B.: Student, Lehrer, Medien usw.)
    agent_bio: str  # Kurzbiografie
    question: str  # Interviewfrage
    response: str  # Interviewantwort
    key_quotes: List[str] = field(default_factory=list)  # Wichtige Zitate
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "agent_role": self.agent_role,
            "agent_bio": self.agent_bio,
            "question": self.question,
            "response": self.response,
            "key_quotes": self.key_quotes
        }
    
    def to_text(self) -> str:
        text = f"**{self.agent_name}** ({self.agent_role})\n"
        # Vollständige agent_bio anzeigen, nicht abgeschnitten
        text += f"_Biografie: {self.agent_bio}_\n\n"
        text += f"**F:** {self.question}\n\n"
        text += f"**A:** {self.response}\n"
        if self.key_quotes:
            text += "\n**Wichtige Zitate:**\n"
            for quote in self.key_quotes:
                # Verschiedene Anführungszeichen bereinigen
                clean_quote = quote.replace('\u201c', '').replace('\u201d', '').replace('"', '')
                clean_quote = clean_quote.replace('\u300c', '').replace('\u300d', '')
                clean_quote = clean_quote.strip()
                # Führende Satzzeichen entfernen
                while clean_quote and clean_quote[0] in '，,；;：:、。！？\n\r\t ':
                    clean_quote = clean_quote[1:]
                # Inhalt mit Problemnummern filtern (Problem 1-9)
                skip = False
                for d in '123456789':
                    if f'\u95ee\u9898{d}' in clean_quote:
                        skip = True
                        break
                if skip:
                    continue
                # Zu lange Inhalte abschneiden (nach Punkt abschneiden, nicht hart)
                if len(clean_quote) > 150:
                    dot_pos = clean_quote.find('\u3002', 80)
                    if dot_pos > 0:
                        clean_quote = clean_quote[:dot_pos + 1]
                    else:
                        clean_quote = clean_quote[:147] + "..."
                if clean_quote and len(clean_quote) >= 10:
                    text += f'> "{clean_quote}"\n'
        return text


@dataclass
class InterviewResult:
    """
    Interview-Ergebnis (Interview)
    Enthält Interviewantworten von mehreren simulierten Agents
    """
    interview_topic: str  # Interviewthema
    interview_questions: List[str]  # Interviewfragenliste
    
    # Ausgewählte Agents für das Interview
    selected_agents: List[Dict[str, Any]] = field(default_factory=list)
    # Interviewantworten der einzelnen Agents
    interviews: List[AgentInterview] = field(default_factory=list)
    
    # Begründung für die Agent-Auswahl
    selection_reasoning: str = ""
    # Zusammengefasstes Interview-Abstract
    summary: str = ""
    
    # Statistiken
    total_agents: int = 0
    interviewed_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "interview_topic": self.interview_topic,
            "interview_questions": self.interview_questions,
            "selected_agents": self.selected_agents,
            "interviews": [i.to_dict() for i in self.interviews],
            "selection_reasoning": self.selection_reasoning,
            "summary": self.summary,
            "total_agents": self.total_agents,
            "interviewed_count": self.interviewed_count
        }
    
    def to_text(self) -> str:
        """In detailliertes Textformat konvertieren für LLM-Verständnis und Berichtszitate"""
        text_parts = [
            "## Tiefen-Interview-Bericht",
            f"**Interviewthema:** {self.interview_topic}",
            f"**Interviewanzahl:** {self.interviewed_count} / {self.total_agents} simulierte Agents",
            "\n### Begründung für die Auswahl der Interviewpartner",
            self.selection_reasoning or "(Automatische Auswahl)",
            "\n---",
            "\n### Interview-Protokoll",
        ]

        if self.interviews:
            for i, interview in enumerate(self.interviews, 1):
                text_parts.append(f"\n#### Interview #{i}: {interview.agent_name}")
                text_parts.append(interview.to_text())
                text_parts.append("\n---")
        else:
            text_parts.append("(Keine Interviewaufzeichnungen)\n\n---")

        text_parts.append("\n### Interview-Zusammenfassung und Kernpunkte")
        text_parts.append(self.summary or "(Keine Zusammenfassung)")

        return "\n".join(text_parts)


class ZepToolsService:
    """
    Zep-Retrieval-Tool-Service
    
    【Kern-Retrieval-Tools - optimiert】
    1. insight_forge - Tiefen-Einblick-Retrieval (stärkstes, automatische Sub-Problem-Generierung, mehrdimensionale Suche)
    2. panorama_search - Breitensuche (Vollständige Übersicht erhalten, einschließlich abgelaufener Inhalte)
    3. quick_search - Einfache Suche (schnelle Suche)
    4. interview_agents - Tiefen-Interview (Interview simulierter Agents, Mehrperspektivische Ansichten erhalten)
    
    【Basis-Tools】
    - search_graph - Graph-Semantiksuche
    - get_all_nodes - Alle Nodes des Graphs abrufen
    - get_all_edges - Alle Edges des Graphs abrufen (mit Zeitinformationen)
    - get_node_detail - Detaillierte Node-Informationen abrufen
    - get_node_edges - Mit Node verbundene Edges abrufen
    - get_entities_by_type - Entitäten nach Typ abrufen
    - get_entity_summary - Beziehungszusammenfassung der Entität abrufen
    """
    
    # Retry-Konfiguration
    MAX_RETRIES = 3
    RETRY_DELAY = 2.0
    
    def __init__(self, api_key: Optional[str] = None, llm_client: Optional[LLMClient] = None):
        self.api_key = api_key or Config.ZEP_API_KEY
        if not self.api_key:
            raise ValueError("ZEP_API_KEY nicht konfiguriert")
        
        self.client = Zep(api_key=self.api_key)
        # LLM-Client für InsightForge Sub-Problem-Generierung
        self._llm_client = llm_client
        logger.info("ZepToolsService Initialisierung abgeschlossen")
    
    @property
    def llm(self) -> LLMClient:
        """Lazy-Initialisierung des LLM-Clients"""
        if self._llm_client is None:
            self._llm_client = LLMClient()
        return self._llm_client
    
    def _call_with_retry(self, func, operation_name: str, max_retries: int = None):
        """API-Aufruf mit Retry-Mechanismus"""
        max_retries = max_retries or self.MAX_RETRIES
        last_exception = None
        delay = self.RETRY_DELAY
        
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Zep {operation_name} Versuch {attempt + 1} fehlgeschlagen: {str(e)[:100]}, "
                        f"Wiederholung in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    delay *= 2
                else:
                    logger.error(f"Zep {operation_name} nach {max_retries} Versuchen fehlgeschlagen: {str(e)}")
        
        raise last_exception
    
    def search_graph(
        self, 
        graph_id: str, 
        query: str, 
        limit: int = 10,
        scope: str = "edges"
    ) -> SearchResult:
        """
        Graph-Semantiksuche
        
        Verwendet hybride Suche (Semantik+BM25) im Graph nach relevanten Informationen.
        Wenn Zep Cloud Search API nicht verfügbar, wird auf lokale Keyword-Matching herabgestuft.
        
        Args:
            graph_id: Graph-ID (Standalone Graph)
            query: Suchanfrage
            limit: Anzahl der zurückgegebenen Ergebnisse
            scope: Suchbereich, "edges" oder "nodes"
            
        Returns:
            SearchResult: Suchergebnis
        """
        logger.info(f"Graph-Suche: graph_id={graph_id}, query={query[:50]}...")
        
        # Versuche Zep Cloud Search API zu verwenden
        try:
            search_results = self._call_with_retry(
                func=lambda: self.client.graph.search(
                    graph_id=graph_id,
                    query=query,
                    limit=limit,
                    scope=scope,
                    reranker="cross_encoder"
                ),
                operation_name=f"Graph-Suche(graph={graph_id})"
            )
            
            facts = []
            edges = []
            nodes = []
            
            # Edge-Suchergebnisse analysieren
            if hasattr(search_results, 'edges') and search_results.edges:
                for edge in search_results.edges:
                    if hasattr(edge, 'fact') and edge.fact:
                        facts.append(edge.fact)
                    edges.append({
                        "uuid": getattr(edge, 'uuid_', None) or getattr(edge, 'uuid', ''),
                        "name": getattr(edge, 'name', ''),
                        "fact": getattr(edge, 'fact', ''),
                        "source_node_uuid": getattr(edge, 'source_node_uuid', ''),
                        "target_node_uuid": getattr(edge, 'target_node_uuid', ''),
                    })
            
            # Node-Suchergebnisse analysieren
            if hasattr(search_results, 'nodes') and search_results.nodes:
                for node in search_results.nodes:
                    nodes.append({
                        "uuid": getattr(node, 'uuid_', None) or getattr(node, 'uuid', ''),
                        "name": getattr(node, 'name', ''),
                        "labels": getattr(node, 'labels', []),
                        "summary": getattr(node, 'summary', ''),
                    })
                    # Node-Zusammenfassung zählt auch als Fakt
                    if hasattr(node, 'summary') and node.summary:
                        facts.append(f"[{node.name}]: {node.summary}")
            
            logger.info(f"Suche abgeschlossen: {len(facts)} relevante Fakten gefunden")
            
            return SearchResult(
                facts=facts,
                edges=edges,
                nodes=nodes,
                query=query,
                total_count=len(facts)
            )
            
        except Exception as e:
            logger.warning(f"Zep Search API fehlgeschlagen, Herabstufung auf lokale Suche: {str(e)}")
            # Herabstufung: Lokale Keyword-Matching-Suche verwenden
            return self._local_search(graph_id, query, limit, scope)
    
    def _local_search(
        self, 
        graph_id: str, 
        query: str, 
        limit: int = 10,
        scope: str = "edges"
    ) -> SearchResult:
        """
        Lokale Keyword-Matching-Suche (als Fallback für Zep Search API)
        
        Alle Edges/Nodes abrufen und lokal Keyword-Matching durchführen
        
        Args:
            graph_id: Graph-ID
            query: Suchanfrage
            limit: Anzahl der zurückgegebenen Ergebnisse
            scope: Suchbereich
            
        Returns:
            SearchResult: Suchergebnis
        """
        logger.info(f"Verwende lokale Suche: query={query[:30]}...")
        
        facts = []
        edges_result = []
        nodes_result = []
        
        # Keywords aus Anfrage extrahieren (einfache Tokenisierung)
        query_lower = query.lower()
        keywords = [w.strip() for w in query_lower.replace(',', ' ').replace('，', ' ').split() if len(w.strip()) > 1]
        
        def match_score(text: str) -> int:
            """Berechnet Match-Score zwischen Text und Anfrage"""
            if not text:
                return 0
            text_lower = text.lower()
            # Exakte Anfrage-Übereinstimmung
            if query_lower in text_lower:
                return 100
            # Keyword-Übereinstimmung
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 10
            return score
        
        try:
            if scope in ["edges", "both"]:
                # Alle Edges abrufen und matchen
                all_edges = self.get_all_edges(graph_id)
                scored_edges = []
                for edge in all_edges:
                    score = match_score(edge.fact) + match_score(edge.name)
                    if score > 0:
                        scored_edges.append((score, edge))
                
                # Nach Score sortieren
                scored_edges.sort(key=lambda x: x[0], reverse=True)
                
                for score, edge in scored_edges[:limit]:
                    if edge.fact:
                        facts.append(edge.fact)
                    edges_result.append({
                        "uuid": edge.uuid,
                        "name": edge.name,
                        "fact": edge.fact,
                        "source_node_uuid": edge.source_node_uuid,
                        "target_node_uuid": edge.target_node_uuid,
                    })
            
            if scope in ["nodes", "both"]:
                # Alle Nodes abrufen und matchen
                all_nodes = self.get_all_nodes(graph_id)
                scored_nodes = []
                for node in all_nodes:
                    score = match_score(node.name) + match_score(node.summary)
                    if score > 0:
                        scored_nodes.append((score, node))
                
                scored_nodes.sort(key=lambda x: x[0], reverse=True)
                
                for score, node in scored_nodes[:limit]:
                    nodes_result.append({
                        "uuid": node.uuid,
                        "name": node.name,
                        "labels": node.labels,
                        "summary": node.summary,
                    })
                    if node.summary:
                        facts.append(f"[{node.name}]: {node.summary}")
            
            logger.info(f"Lokale Suche abgeschlossen: {len(facts)} relevante Fakten gefunden")
            
        except Exception as e:
            logger.error(f"Lokale Suche fehlgeschlagen: {str(e)}")
        
        return SearchResult(
            facts=facts,
            edges=edges_result,
            nodes=nodes_result,
            query=query,
            total_count=len(facts)
        )
    
    def get_all_nodes(self, graph_id: str) -> List[NodeInfo]:
        """
        Alle Nodes des Graphs abrufen (paginiert)

        Args:
            graph_id: Graph-ID

        Returns:
            Node-Liste
        """
        logger.info(f"Alle Nodes des Graphs {graph_id} werden abgerufen...")

        nodes = fetch_all_nodes(self.client, graph_id)

        result = []
        for node in nodes:
            node_uuid = getattr(node, 'uuid_', None) or getattr(node, 'uuid', None) or ""
            result.append(NodeInfo(
                uuid=str(node_uuid) if node_uuid else "",
                name=node.name or "",
                labels=node.labels or [],
                summary=node.summary or "",
                attributes=node.attributes or {}
            ))

        logger.info(f"{len(result)} Nodes abgerufen")
        return result

    def get_all_edges(self, graph_id: str, include_temporal: bool = True) -> List[EdgeInfo]:
        """
        Alle Edges des Graphs abrufen (paginiert, mit Zeitinformationen)

        Args:
            graph_id: Graph-ID
            include_temporal: Ob Zeitinformationen eingeschlossen werden sollen (Standard True)

        Returns:
            Edge-Liste (enthält created_at, valid_at, invalid_at, expired_at)
        """
        logger.info(f"Alle Edges des Graphs {graph_id} werden abgerufen...")

        edges = fetch_all_edges(self.client, graph_id)

        result = []
        for edge in edges:
            edge_uuid = getattr(edge, 'uuid_', None) or getattr(edge, 'uuid', None) or ""
            edge_info = EdgeInfo(
                uuid=str(edge_uuid) if edge_uuid else "",
                name=edge.name or "",
                fact=edge.fact or "",
                source_node_uuid=edge.source_node_uuid or "",
                target_node_uuid=edge.target_node_uuid or ""
            )

            # Zeitinformationen hinzufügen
            if include_temporal:
                edge_info.created_at = getattr(edge, 'created_at', None)
                edge_info.valid_at = getattr(edge, 'valid_at', None)
                edge_info.invalid_at = getattr(edge, 'invalid_at', None)
                edge_info.expired_at = getattr(edge, 'expired_at', None)

            result.append(edge_info)

        logger.info(f"{len(result)} Edges abgerufen")
        return result
    
    def get_node_detail(self, node_uuid: str) -> Optional[NodeInfo]:
        """
        Detaillierte Informationen eines einzelnen Nodes abrufen
        
        Args:
            node_uuid: Node-UUID
            
        Returns:
            Node-Information oder None
        """
        logger.info(f"Node-Details abrufen: {node_uuid[:8]}...")
        
        try:
            node = self._call_with_retry(
                func=lambda: self.client.graph.node.get(uuid_=node_uuid),
                operation_name=f"Node-Details abrufen(uuid={node_uuid[:8]}...)"
            )
            
            if not node:
                return None
            
            return NodeInfo(
                uuid=getattr(node, 'uuid_', None) or getattr(node, 'uuid', ''),
                name=node.name or "",
                labels=node.labels or [],
                summary=node.summary or "",
                attributes=node.attributes or {}
            )
        except Exception as e:
            logger.error(f"Node-Details abrufen fehlgeschlagen: {str(e)}")
            return None
    
    def get_node_edges(self, graph_id: str, node_uuid: str) -> List[EdgeInfo]:
        """
        Alle mit einem Node verbundenen Edges abrufen
        
        Durch Abrufen aller Edges des Graphs und Filtern der mit dem angegebenen Node verbundenen Edges
        
        Args:
            graph_id: Graph-ID
            node_uuid: Node-UUID
            
        Returns:
            Edge-Liste
        """
        logger.info(f"Verwandte Edges des Nodes {node_uuid[:8]}... abrufen")
        
        try:
            # Alle Edges des Graphs abrufen und filtern
            all_edges = self.get_all_edges(graph_id)
            
            result = []
            for edge in all_edges:
                # Prüfen ob Edge mit angegebenem Node verbunden ist (als Quelle oder Ziel)
                if edge.source_node_uuid == node_uuid or edge.target_node_uuid == node_uuid:
                    result.append(edge)
            
            logger.info(f"{len(result)} mit Node verbundene Edges gefunden")
            return result
            
        except Exception as e:
            logger.warning(f"Node-Edges abrufen fehlgeschlagen: {str(e)}")
            return []
    
    def get_entities_by_type(
        self, 
        graph_id: str, 
        entity_type: str
    ) -> List[NodeInfo]:
        """
        Entitäten nach Typ abrufen
        
        Args:
            graph_id: Graph-ID
            entity_type: Entitätstyp (z.B. Student, PublicFigure usw.)
            
        Returns:
            Liste der Entitäten des angegebenen Typs
        """
        logger.info(f"Entitäten vom Typ {entity_type} abrufen...")
        
        all_nodes = self.get_all_nodes(graph_id)
        
        filtered = []
        for node in all_nodes:
            # Prüfen ob Labels den angegebenen Typ enthalten
            if entity_type in node.labels:
                filtered.append(node)
        
        logger.info(f"{len(filtered)} Entitäten vom Typ {entity_type} gefunden")
        return filtered
    
    def get_entity_summary(
        self, 
        graph_id: str, 
        entity_name: str
    ) -> Dict[str, Any]:
        """
        Beziehungszusammenfassung der angegebenen Entität abrufen
        
        Sucht alle mit dieser Entität verbundenen Informationen und generiert Zusammenfassung
        
        Args:
            graph_id: Graph-ID
            entity_name: Entitätsname
            
        Returns:
            Entitätszusammenfassungsinformationen
        """
        logger.info(f"Beziehungszusammenfassung der Entität {entity_name} abrufen...")
        
        # Zuerst nach entitätsbezogenen Informationen suchen
        search_result = self.search_graph(
            graph_id=graph_id,
            query=entity_name,
            limit=20
        )
        
        # Versuchen, die Entität in allen Nodes zu finden
        all_nodes = self.get_all_nodes(graph_id)
        entity_node = None
        for node in all_nodes:
            if node.name.lower() == entity_name.lower():
                entity_node = node
                break
        
        related_edges = []
        if entity_node:
            # graph_id-Parameter übergeben
            related_edges = self.get_node_edges(graph_id, entity_node.uuid)
        
        return {
            "entity_name": entity_name,
            "entity_info": entity_node.to_dict() if entity_node else None,
            "related_facts": search_result.facts,
            "related_edges": [e.to_dict() for e in related_edges],
            "total_relations": len(related_edges)
        }
    
    def get_graph_statistics(self, graph_id: str) -> Dict[str, Any]:
        """
        Statistiken des Graphs abrufen
        
        Args:
            graph_id: Graph-ID
            
        Returns:
            Statistiken
        """
        logger.info(f"Statistiken des Graphs {graph_id} abrufen...")
        
        nodes = self.get_all_nodes(graph_id)
        edges = self.get_all_edges(graph_id)
        
        # Entitätstyp-Verteilung statistisch erfassen
        entity_types = {}
        for node in nodes:
            for label in node.labels:
                if label not in ["Entity", "Node"]:
                    entity_types[label] = entity_types.get(label, 0) + 1
        
        # Beziehungstyp-Verteilung statistisch erfassen
        relation_types = {}
        for edge in edges:
            relation_types[edge.name] = relation_types.get(edge.name, 0) + 1
        
        return {
            "graph_id": graph_id,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "entity_types": entity_types,
            "relation_types": relation_types
        }
    
    def get_simulation_context(
        self, 
        graph_id: str,
        simulation_requirement: str,
        limit: int = 30
    ) -> Dict[str, Any]:
        """
        Simulationsbezogene Kontextinformationen abrufen
        
        Integrierte Suche nach allen mit Simulationsanforderungen verbundenen Informationen
        
        Args:
            graph_id: Graph-ID
            simulation_requirement: Simulationsanforderungsbeschreibung
            limit: Mengenlimit für jede Informationskategorie
            
        Returns:
            Simulationskontextinformationen
        """
        logger.info(f"Simulationskontext abrufen: {simulation_requirement[:50]}...")
        
        # Nach simulationsanforderungsbezogenen Informationen suchen
        search_result = self.search_graph(
            graph_id=graph_id,
            query=simulation_requirement,
            limit=limit
        )
        
        # Graph-Statistiken abrufen
        stats = self.get_graph_statistics(graph_id)
        
        # Alle Entitäts-Nodes abrufen
        all_nodes = self.get_all_nodes(graph_id)
        
        # Entitäten mit tatsächlichem Typ filtern (keine reinen Entity-Nodes)
        entities = []
        for node in all_nodes:
            custom_labels = [l for l in node.labels if l not in ["Entity", "Node"]]
            if custom_labels:
                entities.append({
                    "name": node.name,
                    "type": custom_labels[0],
                    "summary": node.summary
                })
        
        return {
            "simulation_requirement": simulation_requirement,
            "related_facts": search_result.facts,
            "graph_statistics": stats,
            "entities": entities[:limit],  # Menge begrenzen
            "total_entities": len(entities)
        }
    
    # ========== Kern-Retrieval-Tools (optimiert) ==========
    
    def insight_forge(
        self,
        graph_id: str,
        query: str,
        simulation_requirement: str,
        report_context: str = "",
        max_sub_queries: int = 5
    ) -> InsightForgeResult:
        """
        【InsightForge - Tiefen-Einblick-Retrieval】
        
        Stärkste hybride Suchfunktion, automatische Problemzerlegung und mehrdimensionale Suche:
        1. Verwendet LLM zur Zerlegung des Problems in mehrere Sub-Probleme
        2. Semantische Suche für jedes Sub-Problem
        3. Verwandte Entitäten extrahieren und deren Detailinformationen abrufen
        4. Beziehungsketten verfolgen
        5. Alle Ergebnisse integrieren und Tiefen-Einblick generieren
        
        Args:
            graph_id: Graph-ID
            query: Benutzerfrage
            simulation_requirement: Simulationsanforderungsbeschreibung
            report_context: Berichtskontext (optional, für präzisere Sub-Problem-Generierung)
            max_sub_queries: Maximale Anzahl von Sub-Problemen
            
        Returns:
            InsightForgeResult: Tiefen-Einblick-Retrieval-Ergebnis
        """
        logger.info(f"InsightForge Tiefen-Einblick-Retrieval: {query[:50]}...")
        
        result = InsightForgeResult(
            query=query,
            simulation_requirement=simulation_requirement,
            sub_queries=[]
        )
        
        # Step 1: Verwende LLM zur Sub-Problem-Generierung
        sub_queries = self._generate_sub_queries(
            query=query,
            simulation_requirement=simulation_requirement,
            report_context=report_context,
            max_queries=max_sub_queries
        )
        result.sub_queries = sub_queries
        logger.info(f"{len(sub_queries)} Sub-Probleme generiert")
        
        # Step 2: Semantische Suche für jedes Sub-Problem
        all_facts = []
        all_edges = []
        seen_facts = set()
        
        for sub_query in sub_queries:
            search_result = self.search_graph(
                graph_id=graph_id,
                query=sub_query,
                limit=15,
                scope="edges"
            )
            
            for fact in search_result.facts:
                if fact not in seen_facts:
                    all_facts.append(fact)
                    seen_facts.add(fact)
            
            all_edges.extend(search_result.edges)
        
        # Suche auch für das Originalproblem durchführen
        main_search = self.search_graph(
            graph_id=graph_id,
            query=query,
            limit=20,
            scope="edges"
        )
        for fact in main_search.facts:
            if fact not in seen_facts:
                all_facts.append(fact)
                seen_facts.add(fact)
        
        result.semantic_facts = all_facts
        result.total_facts = len(all_facts)
        
        # Step 3: Verwandte Entitäts-UUIDs aus Edges extrahieren, nur Informationen dieser Entitäten abrufen (nicht alle Nodes)
        entity_uuids = set()
        for edge_data in all_edges:
            if isinstance(edge_data, dict):
                source_uuid = edge_data.get('source_node_uuid', '')
                target_uuid = edge_data.get('target_node_uuid', '')
                if source_uuid:
                    entity_uuids.add(source_uuid)
                if target_uuid:
                    entity_uuids.add(target_uuid)
        
        # Details aller verwandten Entitäten abrufen (keine Mengenbegrenzung, vollständige Ausgabe)
        entity_insights = []
        node_map = {}  # Für nachfolgende Beziehungsketten-Konstruktion
        
        for uuid in list(entity_uuids):  # Alle Entitäten verarbeiten, nicht abschneiden
            if not uuid:
                continue
            try:
                # Einzelne Detailinformationen jedes verwandten Nodes abrufen
                node = self.get_node_detail(uuid)
                if node:
                    node_map[uuid] = node
                    entity_type = next((l for l in node.labels if l not in ["Entity", "Node"]), "Entität")
                    
                    # Alle mit dieser Entität verbundenen Fakten abrufen (nicht abschneiden)
                    related_facts = [
                        f for f in all_facts 
                        if node.name.lower() in f.lower()
                    ]
                    
                    entity_insights.append({
                        "uuid": node.uuid,
                        "name": node.name,
                        "type": entity_type,
                        "summary": node.summary,
                        "related_facts": related_facts  # Vollständige Ausgabe, nicht abschneiden
                    })
            except Exception as e:
                logger.debug(f"Node {uuid} abrufen fehlgeschlagen: {e}")
                continue
        
        result.entity_insights = entity_insights
        result.total_entities = len(entity_insights)
        
        # Step 4: Alle Beziehungsketten konstruieren (keine Mengenbegrenzung)
        relationship_chains = []
        for edge_data in all_edges:  # Alle Edges verarbeiten, nicht abschneiden
            if isinstance(edge_data, dict):
                source_uuid = edge_data.get('source_node_uuid', '')
                target_uuid = edge_data.get('target_node_uuid', '')
                relation_name = edge_data.get('name', '')
                
                source_name = node_map.get(source_uuid, NodeInfo('', '', [], '', {})).name or source_uuid[:8]
                target_name = node_map.get(target_uuid, NodeInfo('', '', [], '', {})).name or target_uuid[:8]
                
                chain = f"{source_name} --[{relation_name}]--> {target_name}"
                if chain not in relationship_chains:
                    relationship_chains.append(chain)
        
        result.relationship_chains = relationship_chains
        result.total_relationships = len(relationship_chains)
        
        logger.info(f"InsightForge abgeschlossen: {result.total_facts} Fakten, {result.total_entities} Entitäten, {result.total_relationships} Beziehungen")
        return result
    
    def _generate_sub_queries(
        self,
        query: str,
        simulation_requirement: str,
        report_context: str = "",
        max_queries: int = 5
    ) -> List[str]:
        """
        Verwendet LLM zur Sub-Problem-Generierung
        
        Zerlegt komplexe Probleme in mehrere unabhängig retrievable Sub-Probleme
        """
        system_prompt = """Du bist ein professioneller Problemanalyse-Experte. Deine Aufgabe ist es, ein komplexes Problem in mehrere in der simulierten Welt unabhängig beobachtbare Sub-Probleme zu zerlegen.

Anforderungen:
1. Jedes Sub-Problem sollte spezifisch genug sein, um relevantes Agent-Verhalten oder Ereignisse in der simulierten Welt zu finden
2. Sub-Probleme sollten verschiedene Dimensionen des Originalproblems abdecken (z.B.: Wer, Was, Warum, Wie, Wann, Wo)
3. Sub-Probleme sollten mit dem Simulationsszenario zusammenhängen
4. JSON-Format zurückgeben: {"sub_queries": ["Sub-Problem 1", "Sub-Problem 2", ...]}"""

        user_prompt = f"""Simulationsanforderungshintergrund:
{simulation_requirement}

{f"Berichtskontext: {report_context[:500]}" if report_context else ""}

Bitte zerlege die folgende Frage in {max_queries} Sub-Probleme:
{query}

JSON-Format der Sub-Problem-Liste zurückgeben."""

        try:
            response = self.llm.chat_json(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            sub_queries = response.get("sub_queries", [])
            # Sicherstellen dass es eine String-Liste ist
            return [str(sq) for sq in sub_queries[:max_queries]]
            
        except Exception as e:
            logger.warning(f"Sub-Problem-Generierung fehlgeschlagen: {str(e)}, verwende Standard-Sub-Probleme")
            # Fallback: Varianten basierend auf Originalproblem zurückgeben
            return [
                query,
                f"{query} - Hauptbeteiligte",
                f"{query} - Ursachen und Auswirkungen",
                f"{query} - Entwicklungsprozess"
            ][:max_queries]
    
    def panorama_search(
        self,
        graph_id: str,
        query: str,
        include_expired: bool = True,
        limit: int = 50
    ) -> PanoramaResult:
        """
        【PanoramaSearch - Breitensuche】
        
        Vollständige Übersicht erhalten, einschließlich aller relevanten Inhalte und historischer/abgelaufener Informationen:
        1. Alle relevanten Nodes abrufen
        2. Alle Edges abrufen (einschließlich abgelaufener/ungültiger)
        3. Aktuell gültige und historische Informationen klassifizieren und ordnen
        
        Dieses Tool ist geeignet für Szenarien, die ein vollständiges Verständnis von Ereignissen und Verfolgung von Evolutionsprozessen erfordern.
        
        Args:
            graph_id: Graph-ID
            query: Suchanfrage (für Relevanz-Sortierung)
            include_expired: Ob abgelaufene Inhalte eingeschlossen werden sollen (Standard True)
            limit: Limit für zurückgegebene Ergebnisse
            
        Returns:
            PanoramaResult: Breitensuchergebnis
        """
        logger.info(f"PanoramaSearch Breitensuche: {query[:50]}...")
        
        result = PanoramaResult(query=query)
        
        # Alle Nodes abrufen
        all_nodes = self.get_all_nodes(graph_id)
        node_map = {n.uuid: n for n in all_nodes}
        result.all_nodes = all_nodes
        result.total_nodes = len(all_nodes)
        
        # Alle Edges abrufen (mit Zeitinformationen)
        all_edges = self.get_all_edges(graph_id, include_temporal=True)
        result.all_edges = all_edges
        result.total_edges = len(all_edges)
        
        # Fakten klassifizieren
        active_facts = []
        historical_facts = []
        
        for edge in all_edges:
            if not edge.fact:
                continue
            
            # Entitätsnamen zu Fakten hinzufügen
            source_name = node_map.get(edge.source_node_uuid, NodeInfo('', '', [], '', {})).name or edge.source_node_uuid[:8]
            target_name = node_map.get(edge.target_node_uuid, NodeInfo('', '', [], '', {})).name or edge.target_node_uuid[:8]
            
            # Ob abgelaufen/ungültig
            is_historical = edge.is_expired or edge.is_invalid
            
            if is_historical:
                # Historische/abgelaufene Fakten, Zeitmarkierung hinzufügen
                valid_at = edge.valid_at or "Unbekannt"
                invalid_at = edge.invalid_at or edge.expired_at or "Unbekannt"
                fact_with_time = f"[{valid_at} - {invalid_at}] {edge.fact}"
                historical_facts.append(fact_with_time)
            else:
                # Aktuell gültige Fakten
                active_facts.append(edge.fact)
        
        # Relevanz-Sortierung basierend auf Anfrage
        query_lower = query.lower()
        keywords = [w.strip() for w in query_lower.replace(',', ' ').replace('，', ' ').split() if len(w.strip()) > 1]
        
        def relevance_score(fact: str) -> int:
            fact_lower = fact.lower()
            score = 0
            if query_lower in fact_lower:
                score += 100
            for kw in keywords:
                if kw in fact_lower:
                    score += 10
            return score
        
        # Sortieren und begrenzen
        active_facts.sort(key=relevance_score, reverse=True)
        historical_facts.sort(key=relevance_score, reverse=True)
        
        result.active_facts = active_facts[:limit]
        result.historical_facts = historical_facts[:limit] if include_expired else []
        result.active_count = len(active_facts)
        result.historical_count = len(historical_facts)
        
        logger.info(f"PanoramaSearch abgeschlossen: {result.active_count} gültige, {result.historical_count} historische")
        return result
    
    def quick_search(
        self,
        graph_id: str,
        query: str,
        limit: int = 10
    ) -> SearchResult:
        """
        【QuickSearch - Einfache Suche】
        
        Schnelles, leichtgewichtiges Retrieval-Tool:
        1. Direkter Aufruf der Zep-Semantiksuche
        2. Relevanteste Ergebnisse zurückgeben
        3. Geeignet für einfache, direkte Retrieval-Anforderungen
        
        Args:
            graph_id: Graph-ID
            query: Suchanfrage
            limit: Anzahl der zurückgegebenen Ergebnisse
            
        Returns:
            SearchResult: Suchergebnis
        """
        logger.info(f"QuickSearch einfache Suche: {query[:50]}...")
        
        # Direkter Aufruf der vorhandenen search_graph-Methode
        result = self.search_graph(
            graph_id=graph_id,
            query=query,
            limit=limit,
            scope="edges"
        )
        
        logger.info(f"QuickSearch abgeschlossen: {result.total_count} Ergebnisse")
        return result
    
    def interview_agents(
        self,
        simulation_id: str,
        interview_requirement: str,
        simulation_requirement: str = "",
        max_agents: int = 5,
        custom_questions: List[str] = None
    ) -> InterviewResult:
        """
        【InterviewAgents - Tiefen-Interview】
        
        Ruft die echte OASIS-Interview-API auf, interviewt Agents in der laufenden Simulation:
        1. Liest automatisch Profil-Dateien, lernt alle simulierten Agents kennen
        2. Verwendet LLM zur Analyse der Interview-Anforderungen, intelligenteste Auswahl relevanter Agents
        3. Verwendet LLM zur Interviewfragen-Generierung
        4. Ruft /api/simulation/interview/batch Interface für echtes Interview auf (beide Plattformen gleichzeitig)
        5. Integriert alle Interview-Ergebnisse, generiert Interview-Bericht
        
        【Wichtig】Diese Funktion erfordert, dass die Simulationsumgebung läuft (OASIS-Umgebung nicht geschlossen)
        
        【Anwendungsszenarien】
        - Ereignissicht aus verschiedenen Rollenperspektiven verstehen
        - Meinungen und Standpunkte von mehreren Parteien sammeln
        - Echte Antworten simulierter Agents erhalten (nicht LLM-simuliert)
        
        Args:
            simulation_id: Simulations-ID (zur Lokalisierung von Profil-Dateien und Interview-API-Aufruf)
            interview_requirement: Interview-Anforderungsbeschreibung (unstrukturiert, z.B. "Verständnis der Studentenmeinung zu Ereignissen")
            simulation_requirement: Simulationsanforderungshintergrund (optional)
            max_agents: Maximale Anzahl zu interviewender Agents
            custom_questions: Benutzerdefinierte Interviewfragen (optional, falls nicht angegeben automatisch generiert)
            
        Returns:
            InterviewResult: Interview-Ergebnis
        """
        from .simulation_runner import SimulationRunner
        
        logger.info(f"InterviewAgents Tiefen-Interview (echte API): {interview_requirement[:50]}...")
        
        result = InterviewResult(
            interview_topic=interview_requirement,
            interview_questions=custom_questions or []
        )
        
        # Step 1: Profil-Dateien lesen
        profiles = self._load_agent_profiles(simulation_id)
        
        if not profiles:
            logger.warning(f"Keine Profil-Dateien für Simulation {simulation_id} gefunden")
            result.summary = "Keine interviewbaren Agent-Profil-Dateien gefunden"
            return result
        
        result.total_agents = len(profiles)
        logger.info(f"{len(profiles)} Agent-Profile geladen")
        
        # Step 2: Verwendet LLM zur Auswahl zu interviewender Agents (gibt agent_id-Liste zurück)
        selected_agents, selected_indices, selection_reasoning = self._select_agents_for_interview(
            profiles=profiles,
            interview_requirement=interview_requirement,
            simulation_requirement=simulation_requirement,
            max_agents=max_agents
        )
        
        result.selected_agents = selected_agents
        result.selection_reasoning = selection_reasoning
        logger.info(f"{len(selected_agents)} Agents für Interview ausgewählt: {selected_indices}")
        
        # Step 3: Interviewfragen generieren (falls nicht angegeben)
        if not result.interview_questions:
            result.interview_questions = self._generate_interview_questions(
                interview_requirement=interview_requirement,
                simulation_requirement=simulation_requirement,
                selected_agents=selected_agents
            )
            logger.info(f"{len(result.interview_questions)} Interviewfragen generiert")
        
        # Fragen zu einem Interview-Prompt zusammenführen
        combined_prompt = "\n".join([f"{i+1}. {q}" for i, q in enumerate(result.interview_questions)])
        
        # Optimiertes Präfix hinzufügen, Agent-Antwortformat einschränken
        INTERVIEW_PROMPT_PREFIX = (
            "Sie werden gerade interviewt. Bitte beantworten Sie die folgenden Fragen direkt in reinem Text, "
            "basierend auf Ihrem Profil, allen vergangenen Erinnerungen und Handlungen.\n"
            "Antwortanforderungen:\n"
            "1. Direkt in natürlicher Sprache antworten, keine Tools aufrufen\n"
            "2. Kein JSON-Format oder Tool-Aufrufformat zurückgeben\n"
            "3. Keine Markdown-Überschriften verwenden (z.B. #, ##, ###)\n"
            "4. Fragen nacheinander beantworten, jede Antwort beginnt mit「Frage X：」(X ist Fragennummer)\n"
            "5. Zwischen Antworten auf verschiedene Fragen Leerzeile einfügen\n"
            "6. Inhaltliche Antworten geben, jede Frage mindestens 2-3 Sätze beantworten\n\n"
        )
        optimized_prompt = f"{INTERVIEW_PROMPT_PREFIX}{combined_prompt}"
        
        # Step 4: Echte Interview-API aufrufen (keine Plattform angegeben, standardmäßig beide Plattformen gleichzeitig interviewen)
        try:
            # Batch-Interview-Liste erstellen (keine Plattform angegeben, beide Plattformen interviewen)
            interviews_request = []
            for agent_idx in selected_indices:
                interviews_request.append({
                    "agent_id": agent_idx,
                    "prompt": optimized_prompt  # Optimierten Prompt verwenden
                    # Keine Plattform angegeben, API interviewt auf twitter und reddit
                })
            
            logger.info(f"Batch-Interview-API aufrufen (beide Plattformen): {len(interviews_request)} Agents")
            
            # SimulationRunner Batch-Interview-Methode aufrufen (keine Plattform übergeben, beide Plattformen interviewen)
            api_result = SimulationRunner.interview_agents_batch(
                simulation_id=simulation_id,
                interviews=interviews_request,
                platform=None,  # Keine Plattform angegeben, beide Plattformen interviewen
                timeout=180.0   # Beide Plattformen benötigen längeres Timeout
            )
            
            logger.info(f"Interview-API zurückgegeben: {api_result.get('interviews_count', 0)} Ergebnisse, success={api_result.get('success')}")
            
            # Prüfen ob API-Aufruf erfolgreich
            if not api_result.get("success", False):
                error_msg = api_result.get("error", "Unbekannter Fehler")
                logger.warning(f"Interview-API zurückgegeben fehlgeschlagen: {error_msg}")
                result.summary = f"Interview-API-Aufruf fehlgeschlagen: {error_msg}. Bitte OASIS-Simulationsumgebungsstatus prüfen."
                return result
            
            # Step 5: API-Rückgabewert analysieren, AgentInterview-Objekt konstruieren
            # Beide-Plattformen-Modus Rückgabeformat: {"twitter_0": {...}, "reddit_0": {...}, "twitter_1": {...}, ...}
            api_data = api_result.get("result", {})
            results_dict = api_data.get("results", {}) if isinstance(api_data, dict) else {}
            
            for i, agent_idx in enumerate(selected_indices):
                agent = selected_agents[i]
                agent_name = agent.get("realname", agent.get("username", f"Agent_{agent_idx}"))
                agent_role = agent.get("profession", "Unbekannt")
                agent_bio = agent.get("bio", "")
                
                # Interview-Ergebnisse dieses Agents auf beiden Plattformen abrufen
                twitter_result = results_dict.get(f"twitter_{agent_idx}", {})
                reddit_result = results_dict.get(f"reddit_{agent_idx}", {})
                
                twitter_response = twitter_result.get("response", "")
                reddit_response = reddit_result.get("response", "")

                # Mögliche JSON-Tool-Aufruf-Umhüllungen bereinigen
                twitter_response = self._clean_tool_call_response(twitter_response)
                reddit_response = self._clean_tool_call_response(reddit_response)

                # Immer beide Plattformen markieren
                twitter_text = twitter_response if twitter_response else "(Keine Antwort auf dieser Plattform)"
                reddit_text = reddit_response if reddit_response else "(Keine Antwort auf dieser Plattform)"
                response_text = f"【Twitter Plattform-Antwort】\n{twitter_text}\n\n【Reddit Plattform-Antwort】\n{reddit_text}"

                # Wichtige Zitate extrahieren (aus Antworten beider Plattformen)
                import re
                combined_responses = f"{twitter_response} {reddit_response}"

                # Antworttext bereinigen: Markierungen, Nummerierung, Markdown usw. entfernen
                clean_text = re.sub(r'#{1,6}\s+', '', combined_responses)
                clean_text = re.sub(r'\{[^}]*tool_name[^}]*\}', '', clean_text)
                clean_text = re.sub(r'[*_`|>~\-]{2,}', '', clean_text)
                clean_text = re.sub(r'Frage\d+[：:]\s*', '', clean_text)
                clean_text = re.sub(r'【[^】]+】', '', clean_text)

                # Strategie 1 (Haupt): Vollständige Sätze mit Substanz extrahieren
                sentences = re.split(r'[。！？]', clean_text)
                meaningful = [
                    s.strip() for s in sentences
                    if 20 <= len(s.strip()) <= 150
                    and not re.match(r'^[\s\W，,；;：:、]+', s.strip())
                    and not s.strip().startswith(('{', 'Frage'))
                ]
                meaningful.sort(key=len, reverse=True)
                key_quotes = [s + "。" for s in meaningful[:3]]

                # Strategie 2 (Ergänzend): Langtext innerhalb korrekt gepaarter chinesischer Anführungszeichen「」
                if not key_quotes:
                    paired = re.findall(r'\u201c([^\u201c\u201d]{15,100})\u201d', clean_text)
                    paired += re.findall(r'\u300c([^\u300c\u300d]{15,100})\u300d', clean_text)
                    key_quotes = [q for q in paired if not re.match(r'^[，,；;：:、]', q)][:3]
                
                interview = AgentInterview(
                    agent_name=agent_name,
                    agent_role=agent_role,
                    agent_bio=agent_bio[:1000],  # Bio-Längenlimit erweitern
                    question=combined_prompt,
                    response=response_text,
                    key_quotes=key_quotes[:5]
                )
                result.interviews.append(interview)
            
            result.interviewed_count = len(result.interviews)
            
        except ValueError as e:
            # Simulationsumgebung nicht aktiv
            logger.warning(f"Interview-API-Aufruf fehlgeschlagen (Umgebung nicht aktiv?): {e}")
            result.summary = f"Interview fehlgeschlagen: {str(e)}. Simulationsumgebung möglicherweise geschlossen, bitte sicherstellen dass OASIS-Umgebung läuft."
            return result
        except Exception as e:
            logger.error(f"Interview-API-Aufruf Ausnahme: {e}")
            import traceback
            logger.error(traceback.format_exc())
            result.summary = f"Fehler während des Interviews: {str(e)}"
            return result
        
        # Step 6: Interview-Zusammenfassung generieren
        if result.interviews:
            result.summary = self._generate_interview_summary(
                interviews=result.interviews,
                interview_requirement=interview_requirement
            )
        
        logger.info(f"InterviewAgents abgeschlossen: {result.interviewed_count} Agents interviewt (beide Plattformen)")
        return result
    
    @staticmethod
    def _clean_tool_call_response(response: str) -> str:
        """JSON-Tool-Aufruf-Umhüllungen in Agent-Antworten bereinigen, tatsächlichen Inhalt extrahieren"""
        if not response or not response.strip().startswith('{'):
            return response
        text = response.strip()
        if 'tool_name' not in text[:80]:
            return response
        import re as _re
        try:
            data = json.loads(text)
            if isinstance(data, dict) and 'arguments' in data:
                for key in ('content', 'text', 'body', 'message', 'reply'):
                    if key in data['arguments']:
                        return str(data['arguments'][key])
        except (json.JSONDecodeError, KeyError, TypeError):
            match = _re.search(r'"content"\s*:\s*"((?:[^"\\]|\\.)*)"', text)
            if match:
                return match.group(1).replace('\\n', '\n').replace('\\"', '"')
        return response

    def _load_agent_profiles(self, simulation_id: str) -> List[Dict[str, Any]]:
        """Agent-Profil-Dateien der Simulation laden"""
        import os
        import csv
        
        # Profil-Dateipfad erstellen
        sim_dir = os.path.join(
            os.path.dirname(__file__), 
            f'../../uploads/simulations/{simulation_id}'
        )
        
        profiles = []
        
        # Zuerst Reddit JSON-Format versuchen
        reddit_profile_path = os.path.join(sim_dir, "reddit_profiles.json")
        if os.path.exists(reddit_profile_path):
            try:
                with open(reddit_profile_path, 'r', encoding='utf-8') as f:
                    profiles = json.load(f)
                logger.info(f"{len(profiles)} Profile aus reddit_profiles.json geladen")
                return profiles
            except Exception as e:
                logger.warning(f"Lesen von reddit_profiles.json fehlgeschlagen: {e}")
        
        # Twitter CSV-Format versuchen
        twitter_profile_path = os.path.join(sim_dir, "twitter_profiles.csv")
        if os.path.exists(twitter_profile_path):
            try:
                with open(twitter_profile_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # CSV-Format in einheitliches Format konvertieren
                        profiles.append({
                            "realname": row.get("name", ""),
                            "username": row.get("username", ""),
                            "bio": row.get("description", ""),
                            "persona": row.get("user_char", ""),
                            "profession": "Unbekannt"
                        })
                logger.info(f"{len(profiles)} Profile aus twitter_profiles.csv geladen")
                return profiles
            except Exception as e:
                logger.warning(f"Lesen von twitter_profiles.csv fehlgeschlagen: {e}")
        
        return profiles
    
    def _select_agents_for_interview(
        self,
        profiles: List[Dict[str, Any]],
        interview_requirement: str,
        simulation_requirement: str,
        max_agents: int
    ) -> tuple:
        """
        Verwendet LLM zur Auswahl zu interviewender Agents
        
        Returns:
            tuple: (selected_agents, selected_indices, reasoning)
                - selected_agents: Liste vollständiger Informationen ausgewählter Agents
                - selected_indices: Index-Liste ausgewählter Agents (für API-Aufruf)
                - reasoning: Auswahlbegründung
        """
        
        # Agent-Zusammenfassungsliste erstellen
        agent_summaries = []
        for i, profile in enumerate(profiles):
            summary = {
                "index": i,
                "name": profile.get("realname", profile.get("username", f"Agent_{i}")),
                "profession": profile.get("profession", "Unbekannt"),
                "bio": profile.get("bio", "")[:200],
                "interested_topics": profile.get("interested_topics", [])
            }
            agent_summaries.append(summary)
        
        system_prompt = """Du bist ein professioneller Interview-Planungs-Experte. Deine Aufgabe ist es, basierend auf Interview-Anforderungen die besten Interview-Partner aus der Liste simulierter Agents auszuwählen.

Auswahlkriterien:
1. Agent-Identität/Beruf ist relevant für Interviewthema
2. Agent hat möglicherweise einzigartige oder wertvolle Perspektiven
3. Vielfältige Perspektiven auswählen (z.B.: Unterstützer, Gegner, Neutral, Fachleute usw.)
4. Direkt mit Ereignissen verbundene Rollen priorisieren

JSON-Format zurückgeben:
{
    "selected_indices": [Liste ausgewählter Agent-Indizes],
    "reasoning": "Begründung der Auswahl"
}"""

        user_prompt = f"""Interview-Anforderung:
{interview_requirement}

Simulationshintergrund:
{simulation_requirement if simulation_requirement else "Nicht angegeben"}

Verfügbare Agent-Liste (insgesamt {len(agent_summaries)}):
{json.dumps(agent_summaries, ensure_ascii=False, indent=2)}

Bitte wählen Sie maximal {max_agents} Agents für das Interview aus und begründen Sie die Auswahl."""

        try:
            response = self.llm.chat_json(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            selected_indices = response.get("selected_indices", [])[:max_agents]
            reasoning = response.get("reasoning", "Automatische Auswahl basierend auf Relevanz")
            
            # Vollständige Informationen ausgewählter Agents abrufen
            selected_agents = []
            valid_indices = []
            for idx in selected_indices:
                if 0 <= idx < len(profiles):
                    selected_agents.append(profiles[idx])
                    valid_indices.append(idx)
            
            return selected_agents, valid_indices, reasoning
            
        except Exception as e:
            logger.warning(f"LLM Agent-Auswahl fehlgeschlagen, verwende Standardauswahl: {e}")
            # Fallback: Erste N auswählen
            selected = profiles[:max_agents]
            indices = list(range(min(max_agents, len(profiles))))
            return selected, indices, "Verwende Standardauswahl-Strategie"
    
    def _generate_interview_questions(
        self,
        interview_requirement: str,
        simulation_requirement: str,
        selected_agents: List[Dict[str, Any]]
    ) -> List[str]:
        """Verwendet LLM zur Interviewfragen-Generierung"""
        
        agent_roles = [a.get("profession", "Unbekannt") for a in selected_agents]
        
        system_prompt = """Du bist ein professioneller Journalist/Interviewer. Generiere 3-5 Tiefen-Interviewfragen basierend auf Interview-Anforderungen.

Fragenanforderungen:
1. Offene Fragen, detaillierte Antworten fördern
2. Verschiedene Rollen haben möglicherweise unterschiedliche Antworten
3. Fakten, Meinungen, Gefühle und andere Dimensionen abdecken
4. Natürliche Sprache, wie echte Interviews
5. Jede Frage unter 50 Wörtern, prägnant und klar
6. Direkt fragen, keine Hintergrundinformationen oder Präfixe

JSON-Format zurückgeben: {"questions": ["Frage 1", "Frage 2", ...]}"""

        user_prompt = f"""Interview-Anforderung: {interview_requirement}

Simulationshintergrund: {simulation_requirement if simulation_requirement else "Nicht angegeben"}

Interviewpartner-Rollen: {', '.join(agent_roles)}

Bitte generieren Sie 3-5 Interviewfragen."""

        try:
            response = self.llm.chat_json(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5
            )
            
            return response.get("questions", [f"Was halten Sie von {interview_requirement}?"])
            
        except Exception as e:
            logger.warning(f"Interviewfragen-Generierung fehlgeschlagen: {e}")
            return [
                f"Was ist Ihre Meinung zu {interview_requirement}?",
                "Welche Auswirkungen hat dieses Ereignis auf Sie oder Ihre vertretene Gruppe?",
                "Wie sollte dieses Problem gelöst oder verbessert werden?"
            ]
    
    def _generate_interview_summary(
        self,
        interviews: List[AgentInterview],
        interview_requirement: str
    ) -> str:
        """Interview-Zusammenfassung generieren"""
        
        if not interviews:
            return "Keine Interviews abgeschlossen"
        
        # Alle Interview-Inhalte sammeln
        interview_texts = []
        for interview in interviews:
            interview_texts.append(f"【{interview.agent_name} ({interview.agent_role})】\n{interview.response[:500]}")
        
        system_prompt = """Du bist ein professioneller Nachrichtenredakteur. Bitte generieren Sie eine Interview-Zusammenfassung basierend auf Antworten mehrerer Befragter.

Zusammenfassungsanforderungen:
1. Hauptpunkte aller Parteien extrahieren
2. Gemeinsamkeiten und Differenzen der Perspektiven aufzeigen
3. Wertvolle Zitate hervorheben
4. Objektiv und neutral, keine Parteilichkeit
5. Unter 1000 Wörtern

Formatbeschränkungen (muss eingehalten werden):
- Reine Textabsätze verwenden, verschiedene Teile durch Leerzeilen trennen
- Keine Markdown-Überschriften (z.B. #, ##, ###)
- Keine Trennlinien (z.B. ---, ***)
- Bei Zitaten chinesische Anführungszeichen「」verwenden
- **Fettdruck** für Schlüsselwörter verwenden, aber keine andere Markdown-Syntax"""

        user_prompt = f"""Interviewthema: {interview_requirement}

Interview-Inhalte:
{"".join(interview_texts)}

Bitte Interview-Zusammenfassung generieren."""

        try:
            summary = self.llm.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            return summary
            
        except Exception as e:
            logger.warning(f"Interview-Zusammenfassung fehlgeschlagen: {e}")
            # Fallback: Einfache Verkettung
            return f"Insgesamt {len(interviews)} Befragte interviewt, darunter: " + "、".join([i.agent_name for i in interviews])
