"""
Memory-Entitätslese- und Filterdienst (früher ZepEntityReader)
Liest Knoten via Provider und filtert Knoten, die vordefinierten Entitätstypen entsprechen
"""

import time
from typing import Dict, Any, List, Optional, Set, Callable, TypeVar
from dataclasses import dataclass, field

from .memory.factory import MemoryFactory
from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.zep_entity_reader')

# Für generischen Rückgabetyp
T = TypeVar('T')


@dataclass
class EntityNode:
    """Entitätsknoten-Datenstruktur"""
    uuid: str
    name: str
    labels: List[str]
    summary: str
    attributes: Dict[str, Any]
    # Zugehörige Kanteninformationen
    related_edges: List[Dict[str, Any]] = field(default_factory=list)
    # Zugehörige andere Knoteninformationen
    related_nodes: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "uuid": self.uuid,
            "name": self.name,
            "labels": self.labels,
            "summary": self.summary,
            "attributes": self.attributes,
            "related_edges": self.related_edges,
            "related_nodes": self.related_nodes,
        }
    
    def get_entity_type(self) -> Optional[str]:
        """Entitätstyp abrufen (Standard-Entity-Label ausschließen)"""
        for label in self.labels:
            if label not in ["Entity", "Node"]:
                return label
        return None


@dataclass
class FilteredEntities:
    """Gefilterte Entitätenmenge"""
    entities: List[EntityNode]
    entity_types: Set[str]
    total_count: int
    filtered_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entities": [e.to_dict() for e in self.entities],
            "entity_types": list(self.entity_types),
            "total_count": self.total_count,
            "filtered_count": self.filtered_count,
        }


class ZepEntityReader:
    """
    Memory-Entitätslese- und Filterdienst
    
    Hauptfunktionen:
    1. Alle Knoten via Provider lesen
    2. Knoten filtern, die vordefinierten Entitätstypen entsprechen
    3. Zugehörige Kanten via Provider abrufen
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.provider = MemoryFactory.get_provider()
    
    def get_all_nodes(self, graph_id: str) -> List[Dict[str, Any]]:
        """Alle Knoten via Provider abrufen"""
        logger.info(f"Alle Knoten des Graphen {graph_id} werden abgerufen...")
        mem_nodes = self.provider.fetch_nodes(graph_id)
        
        return [
            {
                "uuid": n.uuid,
                "name": n.name,
                "labels": n.labels,
                "summary": n.summary,
                "attributes": n.attributes,
            } for n in mem_nodes
        ]

    def get_all_edges(self, graph_id: str) -> List[Dict[str, Any]]:
        """Alle Kanten via Provider abrufen"""
        logger.info(f"Alle Kanten des Graphen {graph_id} werden abgerufen...")
        mem_edges = self.provider.fetch_edges(graph_id)
        
        return [
            {
                "uuid": e.uuid,
                "name": e.name,
                "fact": e.fact,
                "source_node_uuid": e.source_node_uuid,
                "target_node_uuid": e.target_node_uuid,
                "attributes": e.attributes,
            } for e in mem_edges
        ]
    
    def get_node_edges(self, graph_id: str, node_uuid: str) -> List[Dict[str, Any]]:
        """Zugehörige Kanten eines Knotens via Provider abrufen"""
        mem_edges = self.provider.fetch_node_edges(graph_id, node_uuid)
        return [
            {
                "uuid": e.uuid,
                "name": e.name,
                "fact": e.fact,
                "source_node_uuid": e.source_node_uuid,
                "target_node_uuid": e.target_node_uuid,
                "attributes": e.attributes,
            } for e in mem_edges
        ]
    
    def filter_defined_entities(
        self, 
        graph_id: str,
        defined_entity_types: Optional[List[str]] = None,
        enrich_with_edges: bool = True
    ) -> FilteredEntities:
        """Knoten filtern via Provider-Daten"""
        logger.info(f"Filterung der Entitäten des Graphen {graph_id} wird gestartet...")
        
        all_nodes = self.get_all_nodes(graph_id)
        total_count = len(all_nodes)
        
        all_edges = self.get_all_edges(graph_id) if enrich_with_edges else []
        node_map = {n["uuid"]: n for n in all_nodes}
        
        filtered_entities = []
        entity_types_found = set()
        
        for node in all_nodes:
            labels = node.get("labels", [])
            custom_labels = [l for l in labels if l not in ["Entity", "Node"]]
            
            if not custom_labels:
                continue
            
            if defined_entity_types:
                matching_labels = [l for l in custom_labels if l in defined_entity_types]
                if not matching_labels:
                    continue
                entity_type = matching_labels[0]
            else:
                entity_type = custom_labels[0]
            
            entity_types_found.add(entity_type)
            
            entity = EntityNode(
                uuid=node["uuid"],
                name=node["name"],
                labels=labels,
                summary=node["summary"],
                attributes=node["attributes"],
            )
            
            if enrich_with_edges:
                related_edges = []
                related_node_uuids = set()
                
                for edge in all_edges:
                    if edge["source_node_uuid"] == node["uuid"]:
                        related_edges.append({
                            "direction": "outgoing",
                            "edge_name": edge["name"],
                            "fact": edge["fact"],
                            "target_node_uuid": edge["target_node_uuid"],
                        })
                        related_node_uuids.add(edge["target_node_uuid"])
                    elif edge["target_node_uuid"] == node["uuid"]:
                        related_edges.append({
                            "direction": "incoming",
                            "edge_name": edge["name"],
                            "fact": edge["fact"],
                            "source_node_uuid": edge["source_node_uuid"],
                        })
                        related_node_uuids.add(edge["source_node_uuid"])
                
                entity.related_edges = related_edges
                
                related_nodes = []
                for related_node_uuid in related_node_uuids:
                    if related_node_uuid in node_map:
                        related_node = node_map[related_node_uuid]
                        related_nodes.append({
                            "uuid": related_node["uuid"],
                            "name": related_node["name"],
                            "labels": related_node["labels"],
                            "summary": related_node.get("summary", ""),
                        })
                
                entity.related_nodes = related_nodes
            
            filtered_entities.append(entity)
        
        return FilteredEntities(
            entities=filtered_entities,
            entity_types=entity_types_found,
            total_count=total_count,
            filtered_count=len(filtered_entities),
        )

    def get_entity_with_context(
        self, 
        graph_id: str, 
        entity_uuid: str
    ) -> Optional[EntityNode]:
        """Einzelne Entität mit Kontext via Provider abrufen"""
        try:
            mem_node = self.provider.get_node_detail(graph_id, entity_uuid)
            if not mem_node:
                return None
            
            edges = self.get_node_edges(graph_id, entity_uuid)
            all_nodes = self.get_all_nodes(graph_id)
            node_map = {n["uuid"]: n for n in all_nodes}
            
            related_edges = []
            related_node_uuids = set()
            
            for edge in edges:
                if edge["source_node_uuid"] == entity_uuid:
                    related_edges.append({
                        "direction": "outgoing",
                        "edge_name": edge["name"],
                        "fact": edge["fact"],
                        "target_node_uuid": edge["target_node_uuid"],
                    })
                    related_node_uuids.add(edge["target_node_uuid"])
                else:
                    related_edges.append({
                        "direction": "incoming",
                        "edge_name": edge["name"],
                        "fact": edge["fact"],
                        "source_node_uuid": edge["source_node_uuid"],
                    })
                    related_node_uuids.add(edge["source_node_uuid"])
            
            related_nodes = []
            for related_node_uuid in related_node_uuids:
                if related_node_uuid in node_map:
                    related_node = node_map[related_node_uuid]
                    related_nodes.append({
                        "uuid": related_node["uuid"],
                        "name": related_node["name"],
                        "labels": related_node["labels"],
                        "summary": related_node.get("summary", ""),
                    })
            
            return EntityNode(
                uuid=mem_node.uuid,
                name=mem_node.name,
                labels=mem_node.labels,
                summary=mem_node.summary,
                attributes=mem_node.attributes,
                related_edges=related_edges,
                related_nodes=related_nodes,
            )
        except Exception as e:
            logger.error(f"Abrufen der Entität {entity_uuid} fehlgeschlagen: {str(e)}")
            return None

    def get_entities_by_type(
        self, 
        graph_id: str, 
        entity_type: str,
        enrich_with_edges: bool = True
    ) -> List[EntityNode]:
        """Alle Entitäten eines bestimmten Typs abrufen"""
        result = self.filter_defined_entities(
            graph_id=graph_id,
            defined_entity_types=[entity_type],
            enrich_with_edges=enrich_with_edges
        )
        return result.entities
