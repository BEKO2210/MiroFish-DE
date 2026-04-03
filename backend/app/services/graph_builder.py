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
from .memory.factory import MemoryFactory


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
    Verantwortlich für den Aufruf des Memory-Providers zum Aufbau des Wissensgraphen
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.provider = MemoryFactory.get_provider()
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
        """Graph erstellen via Provider"""
        # Wir übergeben eine Dummy-Sim-ID falls nicht vorhanden, 
        # der Provider kümmert sich um die Details.
        return self.provider.initialize(simulation_id=str(uuid.uuid4()), graph_name=name)
    
    def set_ontology(self, graph_id: str, ontology: Dict[str, Any]):
        """Graph-Ontologie setzen"""
        # Die komplexe Pydantic-Logik bleibt hier, da sie Zep-spezifisch ist
        # und wir sie evtl. auch für andere Zwecke brauchen.
        # Wenn der Provider Zep ist, nutzen wir die Zep-API.
        
        if Config.MEMORY_PROVIDER == 'zep':
            self._set_zep_ontology(graph_id, ontology)
        else:
            # Für Obsidian/Hybrid speichern wir sie einfach als Metadaten
            self.provider.set_ontology(graph_id, ontology)

    def _set_zep_ontology(self, graph_id: str, ontology: Dict[str, Any]):
        """Zep-spezifische Ontologie-Logik (verschoben von set_ontology)"""
        import warnings
        from typing import Optional
        from pydantic import Field
        from zep_cloud.external_clients.ontology import EntityModel, EntityText, EdgeModel
        from zep_cloud import EntityEdgeSourceTarget
        
        # Pydantic v2 Warnung über Field(default=None) unterdrücken
        warnings.filterwarnings('ignore', category=UserWarning, module='pydantic')
        
        # Zep reservierte Namen
        RESERVED_NAMES = {'uuid', 'name', 'group_id', 'name_embedding', 'summary', 'created_at'}
        
        def safe_attr_name(attr_name: str) -> str:
            if attr_name.lower() in RESERVED_NAMES:
                return f"entity_{attr_name}"
            return attr_name
        
        # Entitätstypen dynamisch erstellen
        entity_types = {}
        for entity_def in ontology.get("entity_types", []):
            name = entity_def["name"]
            description = entity_def.get("description", f"A {name} entity.")
            attrs = {"__doc__": description}
            annotations = {}
            for attr_def in entity_def.get("attributes", []):
                attr_name = safe_attr_name(attr_def["name"])
                attr_desc = attr_def.get("description", attr_name)
                attrs[attr_name] = Field(description=attr_desc, default=None)
                annotations[attr_name] = Optional[EntityText]
            attrs["__annotations__"] = annotations
            entity_class = type(name, (EntityModel,), attrs)
            entity_types[name] = entity_class
        
        # Kantentypen dynamisch erstellen
        edge_definitions = {}
        for edge_def in ontology.get("edge_types", []):
            name = edge_def["name"]
            description = edge_def.get("description", f"A {name} relationship.")
            attrs = {"__doc__": description}
            annotations = {}
            for attr_def in edge_def.get("attributes", []):
                attr_name = safe_attr_name(attr_def["name"])
                attr_desc = attr_def.get("description", attr_name)
                attrs[attr_name] = Field(description=attr_desc, default=None)
                annotations[attr_name] = Optional[str]
            attrs["__annotations__"] = annotations
            class_name = ''.join(word.capitalize() for word in name.split('_'))
            edge_class = type(class_name, (EdgeModel,), attrs)
            source_targets = [
                EntityEdgeSourceTarget(source=st.get("source", "Entity"), target=st.get("target", "Entity"))
                for st in edge_def.get("source_targets", [])
            ]
            if source_targets:
                edge_definitions[name] = (edge_class, source_targets)
        
        # Zep API aufrufen (Wir nutzen hier direkt den Zep-Client des Providers falls verfügbar)
        if hasattr(self.provider, 'client'):
            if entity_types or edge_definitions:
                self.provider.client.graph.set_ontology(
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
        """Text in Batches zum Graph hinzufügen"""
        episode_ids = []
        total_chunks = len(chunks)
        
        for i in range(0, total_chunks, batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_chunks + batch_size - 1) // batch_size
            
            if progress_callback:
                progress = (i + len(batch_chunks)) / total_chunks
                progress_callback(
                    f"Batch {batch_num}/{total_batches} wird gesendet...",
                    progress
                )
            
            for chunk in batch_chunks:
                try:
                    ep_id = self.provider.add_text(graph_id, chunk)
                    if ep_id: episode_ids.append(ep_id)
                except Exception as e:
                    logger.error(f"Fehler beim Hinzufügen von Text: {e}")
            
            time.sleep(0.5) # Throttle
            
        return episode_ids
    
    def _wait_for_episodes(
        self,
        episode_uuids: List[str],
        progress_callback: Optional[Callable] = None,
        timeout: int = 600
    ):
        """Warten auf Verarbeitung (Nur relevant für Zep)"""
        if Config.MEMORY_PROVIDER != 'zep' or not episode_uuids:
            if progress_callback: progress_callback("Verarbeitung abgeschlossen", 1.0)
            return

        if not hasattr(self.provider, 'client'):
            if progress_callback: progress_callback("Provider hat keinen Client", 1.0)
            return
            
        client = self.provider.client
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
            
            for ep_uuid in list(pending_episodes):
                try:
                    episode = client.graph.episode.get(uuid_=ep_uuid)
                    if getattr(episode, 'processed', False):
                        pending_episodes.remove(ep_uuid)
                        completed_count += 1
                except Exception:
                    pass
            
            elapsed = int(time.time() - start_time)
            if progress_callback:
                progress_callback(
                    f"Zep-Verarbeitung... {completed_count}/{total_episodes} abgeschlossen ({elapsed}s)",
                    completed_count / total_episodes if total_episodes > 0 else 0
                )
            
            if pending_episodes:
                time.sleep(3)
        
        if progress_callback:
            progress_callback(f"Verarbeitung abgeschlossen: {completed_count}/{total_episodes}", 1.0)
    
    def _get_graph_info(self, graph_id: str) -> GraphInfo:
        """Graph-Informationen abrufen via Provider"""
        nodes = self.provider.fetch_nodes(graph_id)
        edges = self.provider.fetch_edges(graph_id)

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
        """Vollständige Graph-Daten abrufen via Provider"""
        nodes = self.provider.fetch_nodes(graph_id)
        edges = self.provider.fetch_edges(graph_id)

        node_map = {n.uuid: n.name or "" for n in nodes}
        
        nodes_data = [
            {
                "uuid": n.uuid,
                "name": n.name,
                "labels": n.labels,
                "summary": n.summary,
                "attributes": n.attributes,
                "created_at": n.created_at,
            } for n in nodes
        ]
        
        edges_data = [
            {
                "uuid": e.uuid,
                "name": e.name,
                "fact": e.fact,
                "source_node_uuid": e.source_node_uuid,
                "target_node_uuid": e.target_node_uuid,
                "source_node_name": node_map.get(e.source_node_uuid, ""),
                "target_node_name": node_map.get(e.target_node_uuid, ""),
                "attributes": e.attributes,
                "created_at": e.created_at,
                "valid_at": e.valid_at,
                "invalid_at": e.invalid_at,
                "expired_at": e.expired_at,
            } for e in edges
        ]
        
        return {
            "graph_id": graph_id,
            "nodes": nodes_data,
            "edges": edges_data,
            "node_count": len(nodes_data),
            "edge_count": len(edges_data),
        }
    
    def delete_graph(self, graph_id: str):
        """Graph löschen via Provider"""
        self.provider.delete_graph(graph_id)

