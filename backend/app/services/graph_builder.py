"""
Graph-Aufbau-Dienst
Schnittstelle 2: Verwendung der Zep API zum Aufbau eines Standalone Graph
"""

import os
import uuid
import time
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass

from zep_cloud.client import Zep
from zep_cloud import EpisodeData, EntityEdgeSourceTarget

from ..config import Config
from ..models.task import TaskManager, TaskStatus
from ..utils.zep_paging import fetch_all_nodes, fetch_all_edges
from .text_processor import TextProcessor


@dataclass
class GraphInfo:
    """Graph-Informationen"""
    graph_id: str
    node_count: int
    edge_count: int
    entity_types: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "entity_types": self.entity_types,
        }


class GraphBuilderService:
    """
    Graph-Aufbau-Dienst
    Verantwortlich für den Aufruf der Zep API zum Aufbau des Wissensgraphen
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or Config.ZEP_API_KEY
        if not self.api_key:
            raise ValueError("ZEP_API_KEY nicht konfiguriert")
        
        self.client = Zep(api_key=self.api_key)
        self.task_manager = TaskManager()
    
    def build_graph_async(
        self,
        text: str,
        ontology: Dict[str, Any],
        graph_name: str = "MiroFish Graph",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        batch_size: int = 3
    ) -> str:
        """
        Graph asynchron aufbauen
        
        Args:
            text: Eingabetext
            ontology: Ontologie-Definition (Ausgabe von Schnittstelle 1)
            graph_name: Graph-Name
            chunk_size: Textblockgröße
            chunk_overlap: Block-Überlappungsgröße
            batch_size: Anzahl der Blöcke pro Batch
            
        Returns:
            Aufgaben-ID
        """
        # Aufgabe erstellen
        task_id = self.task_manager.create_task(
            task_type="graph_build",
            metadata={
                "graph_name": graph_name,
                "chunk_size": chunk_size,
                "text_length": len(text),
            }
        )
        
        # Aufbau im Hintergrund-Thread ausführen
        thread = threading.Thread(
            target=self._build_graph_worker,
            args=(task_id, text, ontology, graph_name, chunk_size, chunk_overlap, batch_size)
        )
        thread.daemon = True
        thread.start()
        
        return task_id
    
    def _build_graph_worker(
        self,
        task_id: str,
        text: str,
        ontology: Dict[str, Any],
        graph_name: str,
        chunk_size: int,
        chunk_overlap: int,
        batch_size: int
    ):
        """Graph-Aufbau-Worker-Thread"""
        try:
            self.task_manager.update_task(
                task_id,
                status=TaskStatus.PROCESSING,
                progress=5,
                message="Graph-Aufbau wird gestartet..."
            )
            
            # 1. Graph erstellen
            graph_id = self.create_graph(graph_name)
            self.task_manager.update_task(
                task_id,
                progress=10,
                message=f"Graph erstellt: {graph_id}"
            )
            
            # 2. Ontologie setzen
            self.set_ontology(graph_id, ontology)
            self.task_manager.update_task(
                task_id,
                progress=15,
                message="Ontologie gesetzt"
            )
            
            # 3. Text aufteilen
            chunks = TextProcessor.split_text(text, chunk_size, chunk_overlap)
            total_chunks = len(chunks)
            self.task_manager.update_task(
                task_id,
                progress=20,
                message=f"Text in {total_chunks} Blöcke aufgeteilt"
            )
            
            # 4. Daten in Batches senden
            episode_uuids = self.add_text_batches(
                graph_id, chunks, batch_size,
                lambda msg, prog: self.task_manager.update_task(
                    task_id,
                    progress=20 + int(prog * 0.4),  # 20-60%
                    message=msg
                )
            )
            
            # 5. Auf Zep-Verarbeitung warten
            self.task_manager.update_task(
                task_id,
                progress=60,
                message="Warten auf Zep-Datenverarbeitung..."
            )
            
            self._wait_for_episodes(
                episode_uuids,
                lambda msg, prog: self.task_manager.update_task(
                    task_id,
                    progress=60 + int(prog * 0.3),  # 60-90%
                    message=msg
                )
            )
            
            # 6. Graph-Informationen abrufen
            self.task_manager.update_task(
                task_id,
                progress=90,
                message="Graph-Informationen werden abgerufen..."
            )
            
            graph_info = self._get_graph_info(graph_id)
            
            # Abgeschlossen
            self.task_manager.complete_task(task_id, {
                "graph_id": graph_id,
                "graph_info": graph_info.to_dict(),
                "chunks_processed": total_chunks,
            })
            
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            self.task_manager.fail_task(task_id, error_msg)
    
    def create_graph(self, name: str) -> str:
        """Zep-Graph erstellen (öffentliche Methode)"""
        graph_id = f"mirofish_{uuid.uuid4().hex[:16]}"
        
        self.client.graph.create(
            graph_id=graph_id,
            name=name,
            description="MiroFish Social Simulation Graph"
        )
        
        return graph_id
    
    def set_ontology(self, graph_id: str, ontology: Dict[str, Any]):
        """Graph-Ontologie setzen (öffentliche Methode)"""
        import warnings
        from typing import Optional
        from pydantic import Field
        from zep_cloud.external_clients.ontology import EntityModel, EntityText, EdgeModel
        
        # Pydantic v2 Warnung über Field(default=None) unterdrücken
        # Dies ist die von Zep SDK geforderte Verwendung, Warnungen stammen von dynamischer Klassenerstellung und können sicher ignoriert werden
        warnings.filterwarnings('ignore', category=UserWarning, module='pydantic')
        
        # Zep reservierte Namen, können nicht als Attributnamen verwendet werden
        RESERVED_NAMES = {'uuid', 'name', 'group_id', 'name_embedding', 'summary', 'created_at'}
        
        def safe_attr_name(attr_name: str) -> str:
            """Reservierte Namen in sichere Namen umwandeln"""
            if attr_name.lower() in RESERVED_NAMES:
                return f"entity_{attr_name}"
            return attr_name
        
        # Entitätstypen dynamisch erstellen
        entity_types = {}
        for entity_def in ontology.get("entity_types", []):
            name = entity_def["name"]
            description = entity_def.get("description", f"A {name} entity.")
            
            # Attribut-Dictionary und Typ-Annotationen erstellen (Pydantic v2 erfordert)
            attrs = {"__doc__": description}
            annotations = {}
            
            for attr_def in entity_def.get("attributes", []):
                attr_name = safe_attr_name(attr_def["name"])  # Sicheren Namen verwenden
                attr_desc = attr_def.get("description", attr_name)
                # Zep API benötigt Field description, dies ist erforderlich
                attrs[attr_name] = Field(description=attr_desc, default=None)
                annotations[attr_name] = Optional[EntityText]  # Typ-Annotation
            
            attrs["__annotations__"] = annotations
            
            # Klasse dynamisch erstellen
            entity_class = type(name, (EntityModel,), attrs)
            entity_class.__doc__ = description
            entity_types[name] = entity_class
        
        # Kantentypen dynamisch erstellen
        edge_definitions = {}
        for edge_def in ontology.get("edge_types", []):
            name = edge_def["name"]
            description = edge_def.get("description", f"A {name} relationship.")
            
            # Attribut-Dictionary und Typ-Annotationen erstellen
            attrs = {"__doc__": description}
            annotations = {}
            
            for attr_def in edge_def.get("attributes", []):
                attr_name = safe_attr_name(attr_def["name"])  # Sicheren Namen verwenden
                attr_desc = attr_def.get("description", attr_name)
                # Zep API benötigt Field description, dies ist erforderlich
                attrs[attr_name] = Field(description=attr_desc, default=None)
                annotations[attr_name] = Optional[str]  # Kanten-Attribute verwenden str-Typ
            
            attrs["__annotations__"] = annotations
            
            # Klasse dynamisch erstellen
            class_name = ''.join(word.capitalize() for word in name.split('_'))
            edge_class = type(class_name, (EdgeModel,), attrs)
            edge_class.__doc__ = description
            
            # source_targets erstellen
            source_targets = []
            for st in edge_def.get("source_targets", []):
                source_targets.append(
                    EntityEdgeSourceTarget(
                        source=st.get("source", "Entity"),
                        target=st.get("target", "Entity")
                    )
                )
            
            if source_targets:
                edge_definitions[name] = (edge_class, source_targets)
        
        # Zep API aufrufen um Ontologie zu setzen
        if entity_types or edge_definitions:
            self.client.graph.set_ontology(
                graph_ids=[graph_id],
                entities=entity_types if entity_types else None,
                edges=edge_definitions if edge_definitions else None,
            )
    
    def add_text_batches(
        self,
        graph_id: str,
        chunks: List[str],
        batch_size: int = 3,
        progress_callback: Optional[Callable] = None
    ) -> List[str]:
        """Text in Batches zum Graph hinzufügen, alle Episode-UUIDs zurückgeben"""
        episode_uuids = []
        total_chunks = len(chunks)
        
        for i in range(0, total_chunks, batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_chunks + batch_size - 1) // batch_size
            
            if progress_callback:
                progress = (i + len(batch_chunks)) / total_chunks
                progress_callback(
                    f"Batch {batch_num}/{total_batches} wird gesendet ({len(batch_chunks)} Blöcke)...",
                    progress
                )
            
            # Episode-Daten erstellen
            episodes = [
                EpisodeData(data=chunk, type="text")
                for chunk in batch_chunks
            ]
            
            # An Zep senden
            try:
                batch_result = self.client.graph.add_batch(
                    graph_id=graph_id,
                    episodes=episodes
                )
                
                # Zurückgegebene Episode-UUIDs sammeln
                if batch_result and isinstance(batch_result, list):
                    for ep in batch_result:
                        ep_uuid = getattr(ep, 'uuid_', None) or getattr(ep, 'uuid', None)
                        if ep_uuid:
                            episode_uuids.append(ep_uuid)
                
                # Zu schnelle Anfragen vermeiden
                time.sleep(1)
                
            except Exception as e:
                if progress_callback:
                    progress_callback(f"Batch {batch_num} Senden fehlgeschlagen: {str(e)}", 0)
                raise
        
        return episode_uuids
    
    def _wait_for_episodes(
        self,
        episode_uuids: List[str],
        progress_callback: Optional[Callable] = None,
        timeout: int = 600
    ):
        """Auf Verarbeitung aller Episoden warten (durch Abfrage des processed-Status jeder Episode)"""
        if not episode_uuids:
            if progress_callback:
                progress_callback("Kein Warten erforderlich (keine Episoden)", 1.0)
            return
        
        start_time = time.time()
        pending_episodes = set(episode_uuids)
        completed_count = 0
        total_episodes = len(episode_uuids)
        
        if progress_callback:
            progress_callback(f"Warten auf Verarbeitung von {total_episodes} Textblöcken...", 0)
        
        while pending_episodes:
            if time.time() - start_time > timeout:
                if progress_callback:
                    progress_callback(
                        f"Einige Textblöcke haben Timeout, {completed_count}/{total_episodes} abgeschlossen",
                        completed_count / total_episodes
                    )
                break
            
            # Verarbeitungsstatus jeder Episode prüfen
            for ep_uuid in list(pending_episodes):
                try:
                    episode = self.client.graph.episode.get(uuid_=ep_uuid)
                    is_processed = getattr(episode, 'processed', False)
                    
                    if is_processed:
                        pending_episodes.remove(ep_uuid)
                        completed_count += 1
                        
                except Exception as e:
                    # Einzelne Abfragefehler ignorieren, fortfahren
                    pass
            
            elapsed = int(time.time() - start_time)
            if progress_callback:
                progress_callback(
                    f"Zep-Verarbeitung... {completed_count}/{total_episodes} abgeschlossen, {len(pending_episodes)} ausstehend ({elapsed}s)",
                    completed_count / total_episodes if total_episodes > 0 else 0
                )
            
            if pending_episodes:
                time.sleep(3)  # Alle 3 Sekunden prüfen
        
        if progress_callback:
            progress_callback(f"Verarbeitung abgeschlossen: {completed_count}/{total_episodes}", 1.0)
    
    def _get_graph_info(self, graph_id: str) -> GraphInfo:
        """Graph-Informationen abrufen"""
        # Knoten abrufen (paginiert)
        nodes = fetch_all_nodes(self.client, graph_id)

        # Kanten abrufen (paginiert)
        edges = fetch_all_edges(self.client, graph_id)

        # Entitätstypen zählen
        entity_types = set()
        for node in nodes:
            if node.labels:
                for label in node.labels:
                    if label not in ["Entity", "Node"]:
                        entity_types.add(label)

        return GraphInfo(
            graph_id=graph_id,
            node_count=len(nodes),
            edge_count=len(edges),
            entity_types=list(entity_types)
        )
    
    def get_graph_data(self, graph_id: str) -> Dict[str, Any]:
        """
        Vollständige Graph-Daten abrufen (mit Detailinformationen)
        
        Args:
            graph_id: Graph-ID
            
        Returns:
            Dictionary mit nodes und edges, einschließlich Zeitinformationen, Attributen und weiteren Detaildaten
        """
        nodes = fetch_all_nodes(self.client, graph_id)
        edges = fetch_all_edges(self.client, graph_id)

        # Knotenzuordnung zum Abrufen von Knotennamen erstellen
        node_map = {}
        for node in nodes:
            node_map[node.uuid_] = node.name or ""
        
        nodes_data = []
        for node in nodes:
            # Erstellungszeit abrufen
            created_at = getattr(node, 'created_at', None)
            if created_at:
                created_at = str(created_at)
            
            nodes_data.append({
                "uuid": node.uuid_,
                "name": node.name,
                "labels": node.labels or [],
                "summary": node.summary or "",
                "attributes": node.attributes or {},
                "created_at": created_at,
            })
        
        edges_data = []
        for edge in edges:
            # Zeitinformationen abrufen
            created_at = getattr(edge, 'created_at', None)
            valid_at = getattr(edge, 'valid_at', None)
            invalid_at = getattr(edge, 'invalid_at', None)
            expired_at = getattr(edge, 'expired_at', None)
            
            # Episoden abrufen
            episodes = getattr(edge, 'episodes', None) or getattr(edge, 'episode_ids', None)
            if episodes and not isinstance(episodes, list):
                episodes = [str(episodes)]
            elif episodes:
                episodes = [str(e) for e in episodes]
            
            # fact_type abrufen
            fact_type = getattr(edge, 'fact_type', None) or edge.name or ""
            
            edges_data.append({
                "uuid": edge.uuid_,
                "name": edge.name or "",
                "fact": edge.fact or "",
                "fact_type": fact_type,
                "source_node_uuid": edge.source_node_uuid,
                "target_node_uuid": edge.target_node_uuid,
                "source_node_name": node_map.get(edge.source_node_uuid, ""),
                "target_node_name": node_map.get(edge.target_node_uuid, ""),
                "attributes": edge.attributes or {},
                "created_at": str(created_at) if created_at else None,
                "valid_at": str(valid_at) if valid_at else None,
                "invalid_at": str(invalid_at) if invalid_at else None,
                "expired_at": str(expired_at) if expired_at else None,
                "episodes": episodes or [],
            })
        
        return {
            "graph_id": graph_id,
            "nodes": nodes_data,
            "edges": edges_data,
            "node_count": len(nodes_data),
            "edge_count": len(edges_data),
        }
    
    def delete_graph(self, graph_id: str):
        """Graph löschen"""
        self.client.graph.delete(graph_id=graph_id)

