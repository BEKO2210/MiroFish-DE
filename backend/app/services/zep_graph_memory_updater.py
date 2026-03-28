"""
Zep-Graph-Speicher-Update-Service
Aktualisiert Agent-Aktivitäten aus der Simulation dynamisch in den Zep-Graphen
"""

import os
import time
import threading
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from queue import Queue, Empty

from zep_cloud.client import Zep

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.zep_graph_memory_updater')


@dataclass
class AgentActivity:
    """Agent-Aktivitätsaufzeichnung"""
    platform: str           # twitter / reddit
    agent_id: int
    agent_name: str
    action_type: str        # CREATE_POST, LIKE_POST, etc.
    action_args: Dict[str, Any]
    round_num: int
    timestamp: str
    
    def to_episode_text(self) -> str:
        """
        Aktivität in Textbeschreibung konvertieren, die an Zep gesendet werden kann
        
        Verwendet natürliche Sprachbeschreibungsformat, damit Zep Entitäten und Beziehungen extrahieren kann
        Keine simulationsbezogenen Präfixe hinzufügen, um Graph-Update-Fehleitung zu vermeiden
        """
        # Je nach Aktivitätstyp unterschiedliche Beschreibungen generieren
        action_descriptions = {
            "CREATE_POST": self._describe_create_post,
            "LIKE_POST": self._describe_like_post,
            "DISLIKE_POST": self._describe_dislike_post,
            "REPOST": self._describe_repost,
            "QUOTE_POST": self._describe_quote_post,
            "FOLLOW": self._describe_follow,
            "CREATE_COMMENT": self._describe_create_comment,
            "LIKE_COMMENT": self._describe_like_comment,
            "DISLIKE_COMMENT": self._describe_dislike_comment,
            "SEARCH_POSTS": self._describe_search,
            "SEARCH_USER": self._describe_search_user,
            "MUTE": self._describe_mute,
        }
        
        describe_func = action_descriptions.get(self.action_type, self._describe_generic)
        description = describe_func()
        
        # Direkt "Agent-Name: Aktivitätsbeschreibung" Format zurückgeben, kein Simulationspräfix hinzufügen
        return f"{self.agent_name}: {description}"
    
    def _describe_create_post(self) -> str:
        content = self.action_args.get("content", "")
        if content:
            return f"Hat einen Beitrag veröffentlicht: 「{content}」"
        return "Hat einen Beitrag veröffentlicht"
    
    def _describe_like_post(self) -> str:
        """Beitrag liken - enthält Originalbeitragstext und Autoreninformationen"""
        post_content = self.action_args.get("post_content", "")
        post_author = self.action_args.get("post_author_name", "")
        
        if post_content and post_author:
            return f"Hat {post_author}s Beitrag gelikt: 「{post_content}」"
        elif post_content:
            return f"Hat einen Beitrag gelikt: 「{post_content}」"
        elif post_author:
            return f"Hat einen Beitrag von {post_author} gelikt"
        return "Hat einen Beitrag gelikt"
    
    def _describe_dislike_post(self) -> str:
        """Beitrag disliken - enthält Originalbeitragstext und Autoreninformationen"""
        post_content = self.action_args.get("post_content", "")
        post_author = self.action_args.get("post_author_name", "")
        
        if post_content and post_author:
            return f"Hat {post_author}s Beitrag disliket: 「{post_content}」"
        elif post_content:
            return f"Hat einen Beitrag disliket: 「{post_content}」"
        elif post_author:
            return f"Hat einen Beitrag von {post_author} disliket"
        return "Hat einen Beitrag disliket"
    
    def _describe_repost(self) -> str:
        """Beitrag reposten - enthält Originalbeitragstext und Autoreninformationen"""
        original_content = self.action_args.get("original_content", "")
        original_author = self.action_args.get("original_author_name", "")
        
        if original_content and original_author:
            return f"Hat {original_author}s Beitrag repostet: 「{original_content}」"
        elif original_content:
            return f"Hat einen Beitrag repostet: 「{original_content}」"
        elif original_author:
            return f"Hat einen Beitrag von {original_author} repostet"
        return "Hat einen Beitrag repostet"
    
    def _describe_quote_post(self) -> str:
        """Beitrag zitieren - enthält Originalbeitragstext, Autoreninformationen und Zitierkommentar"""
        original_content = self.action_args.get("original_content", "")
        original_author = self.action_args.get("original_author_name", "")
        quote_content = self.action_args.get("quote_content", "") or self.action_args.get("content", "")
        
        base = ""
        if original_content and original_author:
            base = f"Hat {original_author}s Beitrag 「{original_content}」 zitiert"
        elif original_content:
            base = f"Hat einen Beitrag 「{original_content}」 zitiert"
        elif original_author:
            base = f"Hat einen Beitrag von {original_author} zitiert"
        else:
            base = "Hat einen Beitrag zitiert"
        
        if quote_content:
            base += f", und kommentiert: 「{quote_content}」"
        return base
    
    def _describe_follow(self) -> str:
        """Benutzer folgen - enthält Namen des gefolgten Benutzers"""
        target_user_name = self.action_args.get("target_user_name", "")
        
        if target_user_name:
            return f"Hat dem Benutzer 「{target_user_name}」 gefolgt"
        return "Hat einem Benutzer gefolgt"
    
    def _describe_create_comment(self) -> str:
        """Kommentar veröffentlichen - enthält Kommentarinhalt und Informationen des kommentierten Beitrags"""
        content = self.action_args.get("content", "")
        post_content = self.action_args.get("post_content", "")
        post_author = self.action_args.get("post_author_name", "")
        
        if content:
            if post_content and post_author:
                return f"Hat unter {post_author}s Beitrag 「{post_content}」 kommentiert: 「{content}」"
            elif post_content:
                return f"Hat unter dem Beitrag 「{post_content}」 kommentiert: 「{content}」"
            elif post_author:
                return f"Hat unter {post_author}s Beitrag kommentiert: 「{content}」"
            return f"Hat kommentiert: 「{content}」"
        return "Hat einen Kommentar veröffentlicht"
    
    def _describe_like_comment(self) -> str:
        """Kommentar liken - enthält Kommentarinhalt und Autoreninformationen"""
        comment_content = self.action_args.get("comment_content", "")
        comment_author = self.action_args.get("comment_author_name", "")
        
        if comment_content and comment_author:
            return f"Hat {comment_author}s Kommentar gelikt: 「{comment_content}」"
        elif comment_content:
            return f"Hat einen Kommentar gelikt: 「{comment_content}」"
        elif comment_author:
            return f"Hat einen Kommentar von {comment_author} gelikt"
        return "Hat einen Kommentar gelikt"
    
    def _describe_dislike_comment(self) -> str:
        """Kommentar disliken - enthält Kommentarinhalt und Autoreninformationen"""
        comment_content = self.action_args.get("comment_content", "")
        comment_author = self.action_args.get("comment_author_name", "")
        
        if comment_content and comment_author:
            return f"Hat {comment_author}s Kommentar disliket: 「{comment_content}」"
        elif comment_content:
            return f"Hat einen Kommentar disliket: 「{comment_content}」"
        elif comment_author:
            return f"Hat einen Kommentar von {comment_author} disliket"
        return "Hat einen Kommentar disliket"
    
    def _describe_search(self) -> str:
        """Beiträge suchen - enthält Suchbegriffe"""
        query = self.action_args.get("query", "") or self.action_args.get("keyword", "")
        return f"Hat nach 「{query}」 gesucht" if query else "Hat eine Suche durchgeführt"
    
    def _describe_search_user(self) -> str:
        """Benutzer suchen - enthält Suchbegriffe"""
        query = self.action_args.get("query", "") or self.action_args.get("username", "")
        return f"Hat nach Benutzer 「{query}」 gesucht" if query else "Hat nach Benutzern gesucht"
    
    def _describe_mute(self) -> str:
        """Benutzer stummschalten - enthält Namen des stummgeschalteten Benutzers"""
        target_user_name = self.action_args.get("target_user_name", "")
        
        if target_user_name:
            return f"Hat den Benutzer 「{target_user_name}」 stummgeschaltet"
        return "Hat einen Benutzer stummgeschaltet"
    
    def _describe_generic(self) -> str:
        # Für unbekannte Aktivitätstypen generische Beschreibung
        return f"Hat {self.action_type} Operation ausgeführt"


class ZepGraphMemoryUpdater:
    """
    Zep-Graph-Speicher-Updater
    
    Überwacht Simulations-Actions-Logdateien, aktualisiert neue Agent-Aktivitäten in Echtzeit in den Zep-Graphen.
    Nach Plattform gruppiert, Batch-Sendung an Zep nach Erreichen von BATCH_SIZE Aktivitäten.
    
    Alle bedeutungsvollen Verhaltensweisen werden in Zep aktualisiert, action_args enthält vollständige Kontextinformationen:
    - Originalbeitragstext von Likes/Dislikes
    - Originalbeitragstext von Reposts/Zitaten
    - Benutzername von Follows/Stummschaltungen
    - Originalkommentartext von Likes/Dislikes
    """
    
    # Batch-Sendungsgröße (wie viele pro Plattform akkumuliert werden, bevor gesendet wird)
    BATCH_SIZE = 5
    
    # Plattformnamen-Zuordnung (für Konsolenanzeige)
    PLATFORM_DISPLAY_NAMES = {
        'twitter': 'Welt 1',
        'reddit': 'Welt 2',
    }
    
    # Sendeintervall (Sekunden), um zu schnelle Anfragen zu vermeiden
    SEND_INTERVAL = 0.5
    
    # Retry-Konfiguration
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # Sekunden
    
    def __init__(self, graph_id: str, api_key: Optional[str] = None):
        """
        Updater initialisieren
        
        Args:
            graph_id: Zep-Graph-ID
            api_key: Zep API Key (optional, standardmäßig aus Konfiguration gelesen)
        """
        self.graph_id = graph_id
        self.api_key = api_key or Config.ZEP_API_KEY
        
        if not self.api_key:
            raise ValueError("ZEP_API_KEY nicht konfiguriert")
        
        self.client = Zep(api_key=self.api_key)
        
        # Aktivitätswarteschlange
        self._activity_queue: Queue = Queue()
        
        # Nach Plattform gruppierte Aktivitätspuffer (jede Plattform akkumuliert eigenständig bis BATCH_SIZE für Batch-Sendung)
        self._platform_buffers: Dict[str, List[AgentActivity]] = {
            'twitter': [],
            'reddit': [],
        }
        self._buffer_lock = threading.Lock()
        
        # Steuerungsflags
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        
        # Statistiken
        self._total_activities = 0  # Tatsächlich zur Warteschlange hinzugefügte Aktivitäten
        self._total_sent = 0        # Erfolgreich an Zep gesendete Batches
        self._total_items_sent = 0  # Erfolgreich an Zep gesendete Aktivitäten
        self._failed_count = 0      # Fehlgeschlagene Batches
        self._skipped_count = 0     # Gefilterte übersprungene Aktivitäten (DO_NOTHING)
        
        logger.info(f"ZepGraphMemoryUpdater Initialisierung abgeschlossen: graph_id={graph_id}, batch_size={self.BATCH_SIZE}")
    
    def _get_platform_display_name(self, platform: str) -> str:
        """Anzeigenamen der Plattform abrufen"""
        return self.PLATFORM_DISPLAY_NAMES.get(platform.lower(), platform)
    
    def start(self):
        """Hintergrund-Worker-Thread starten"""
        if self._running:
            return
        
        self._running = True
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name=f"ZepMemoryUpdater-{self.graph_id[:8]}"
        )
        self._worker_thread.start()
        logger.info(f"ZepGraphMemoryUpdater gestartet: graph_id={self.graph_id}")
    
    def stop(self):
        """Hintergrund-Worker-Thread stoppen"""
        self._running = False
        
        # Verbleibende Aktivitäten senden
        self._flush_remaining()
        
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=10)
        
        logger.info(f"ZepGraphMemoryUpdater gestoppt: graph_id={self.graph_id}, "
                   f"total_activities={self._total_activities}, "
                   f"batches_sent={self._total_sent}, "
                   f"items_sent={self._total_items_sent}, "
                   f"failed={self._failed_count}, "
                   f"skipped={self._skipped_count}")
    
    def add_activity(self, activity: AgentActivity):
        """
        Eine Agent-Aktivität zur Warteschlange hinzufügen
        
        Alle bedeutungsvollen Verhaltensweisen werden zur Warteschlange hinzugefügt, darunter:
        - CREATE_POST (Beitrag veröffentlichen)
        - CREATE_COMMENT (Kommentieren)
        - QUOTE_POST (Beitrag zitieren)
        - SEARCH_POSTS (Beiträge suchen)
        - SEARCH_USER (Benutzer suchen)
        - LIKE_POST/DISLIKE_POST (Beitrag liken/disliken)
        - REPOST (Reposten)
        - FOLLOW (Folgen)
        - MUTE (Stummschalten)
        - LIKE_COMMENT/DISLIKE_COMMENT (Kommentar liken/disliken)
        
        action_args enthält vollständige Kontextinformationen (z.B. Originalbeitragstext, Benutzername usw.).
        
        Args:
            activity: Agent-Aktivitätsaufzeichnung
        """
        # DO_NOTHING-Typ Aktivitäten überspringen
        if activity.action_type == "DO_NOTHING":
            self._skipped_count += 1
            return
        
        self._activity_queue.put(activity)
        self._total_activities += 1
        logger.debug(f"Aktivität zur Zep-Warteschlange hinzugefügt: {activity.agent_name} - {activity.action_type}")
    
    def add_activity_from_dict(self, data: Dict[str, Any], platform: str):
        """
        Aktivität aus Dictionary-Daten hinzufügen
        
        Args:
            data: Aus actions.jsonl analysierte Dictionary-Daten
            platform: Plattformname (twitter/reddit)
        """
        # Ereignistyp-Einträge überspringen
        if "event_type" in data:
            return
        
        activity = AgentActivity(
            platform=platform,
            agent_id=data.get("agent_id", 0),
            agent_name=data.get("agent_name", ""),
            action_type=data.get("action_type", ""),
            action_args=data.get("action_args", {}),
            round_num=data.get("round", 0),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
        )
        
        self.add_activity(activity)
    
    def _worker_loop(self):
        """Hintergrund-Worker-Schleife - Aktivitäten batchweise nach Plattform an Zep senden"""
        while self._running or not self._activity_queue.empty():
            try:
                # Versuchen Aktivität aus Warteschlange zu erhalten (1 Sekunde Timeout)
                try:
                    activity = self._activity_queue.get(timeout=1)
                    
                    # Aktivität zum entsprechenden Plattformpuffer hinzufügen
                    platform = activity.platform.lower()
                    with self._buffer_lock:
                        if platform not in self._platform_buffers:
                            self._platform_buffers[platform] = []
                        self._platform_buffers[platform].append(activity)
                        
                        # Prüfen ob diese Plattform Batch-Größe erreicht hat
                        if len(self._platform_buffers[platform]) >= self.BATCH_SIZE:
                            batch = self._platform_buffers[platform][:self.BATCH_SIZE]
                            self._platform_buffers[platform] = self._platform_buffers[platform][self.BATCH_SIZE:]
                            # Lock freigeben vor Senden
                            self._send_batch_activities(batch, platform)
                            # Sendeintervall, um zu schnelle Anfragen zu vermeiden
                            time.sleep(self.SEND_INTERVAL)
                    
                except Empty:
                    pass
                    
            except Exception as e:
                logger.error(f"Worker-Schleife Ausnahme: {e}")
                time.sleep(1)
    
    def _send_batch_activities(self, activities: List[AgentActivity], platform: str):
        """
        Aktivitäten batchweise an Zep-Graphen senden (zu einem Text zusammengeführt)
        
        Args:
            activities: Agent-Aktivitätsliste
            platform: Plattformname
        """
        if not activities:
            return
        
        # Mehrere Aktivitäten zu einem Text zusammenführen, durch Zeilenumbruch getrennt
        episode_texts = [activity.to_episode_text() for activity in activities]
        combined_text = "\n".join(episode_texts)
        
        # Senden mit Retry
        for attempt in range(self.MAX_RETRIES):
            try:
                self.client.graph.add(
                    graph_id=self.graph_id,
                    type="text",
                    data=combined_text
                )
                
                self._total_sent += 1
                self._total_items_sent += len(activities)
                display_name = self._get_platform_display_name(platform)
                logger.info(f"Erfolgreich {len(activities)} {display_name}-Aktivitäten batchweise an Graph {self.graph_id} gesendet")
                logger.debug(f"Batch-Inhaltsvorschau: {combined_text[:200]}...")
                return
                
            except Exception as e:
                if attempt < self.MAX_RETRIES - 1:
                    logger.warning(f"Batch-Sendung an Zep fehlgeschlagen (Versuch {attempt + 1}/{self.MAX_RETRIES}): {e}")
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                else:
                    logger.error(f"Batch-Sendung an Zep fehlgeschlagen, {self.MAX_RETRIES} Wiederholungen: {e}")
                    self._failed_count += 1
    
    def _flush_remaining(self):
        """Verbleibende Aktivitäten in Warteschlange und Puffern senden"""
        # Zuerst verbleibende Aktivitäten in Warteschlange verarbeiten, zum Puffer hinzufügen
        while not self._activity_queue.empty():
            try:
                activity = self._activity_queue.get_nowait()
                platform = activity.platform.lower()
                with self._buffer_lock:
                    if platform not in self._platform_buffers:
                        self._platform_buffers[platform] = []
                    self._platform_buffers[platform].append(activity)
            except Empty:
                break
        
        # Dann verbleibende Aktivitäten in Plattformpuffern senden (auch wenn unter BATCH_SIZE)
        with self._buffer_lock:
            for platform, buffer in self._platform_buffers.items():
                if buffer:
                    display_name = self._get_platform_display_name(platform)
                    logger.info(f"Sende verbleibende {len(buffer)} Aktivitäten der {display_name}-Plattform")
                    self._send_batch_activities(buffer, platform)
            # Alle Puffer leeren
            for platform in self._platform_buffers:
                self._platform_buffers[platform] = []
    
    def get_stats(self) -> Dict[str, Any]:
        """Statistiken abrufen"""
        with self._buffer_lock:
            buffer_sizes = {p: len(b) for p, b in self._platform_buffers.items()}
        
        return {
            "graph_id": self.graph_id,
            "batch_size": self.BATCH_SIZE,
            "total_activities": self._total_activities,  # Gesamt zur Warteschlange hinzugefügte Aktivitäten
            "batches_sent": self._total_sent,            # Erfolgreich gesendete Batches
            "items_sent": self._total_items_sent,        # Erfolgreich gesendete Aktivitäten
            "failed_count": self._failed_count,          # Fehlgeschlagene Batches
            "skipped_count": self._skipped_count,        # Gefilterte übersprungene Aktivitäten (DO_NOTHING)
            "queue_size": self._activity_queue.qsize(),
            "buffer_sizes": buffer_sizes,                # Größe der Plattformpuffer
            "running": self._running,
        }


class ZepGraphMemoryManager:
    """
    Verwaltet mehrere Simulations-Zep-Graph-Speicher-Updater
    
    Jede Simulation kann ihre eigene Updater-Instanz haben
    """
    
    _updaters: Dict[str, ZepGraphMemoryUpdater] = {}
    _lock = threading.Lock()
    
    @classmethod
    def create_updater(cls, simulation_id: str, graph_id: str) -> ZepGraphMemoryUpdater:
        """
        Graph-Speicher-Updater für Simulation erstellen
        
        Args:
            simulation_id: Simulations-ID
            graph_id: Zep-Graph-ID
            
        Returns:
            ZepGraphMemoryUpdater-Instanz
        """
        with cls._lock:
            # Falls bereits vorhanden, alten zuerst stoppen
            if simulation_id in cls._updaters:
                cls._updaters[simulation_id].stop()
            
            updater = ZepGraphMemoryUpdater(graph_id)
            updater.start()
            cls._updaters[simulation_id] = updater
            
            logger.info(f"Graph-Speicher-Updater erstellt: simulation_id={simulation_id}, graph_id={graph_id}")
            return updater
    
    @classmethod
    def get_updater(cls, simulation_id: str) -> Optional[ZepGraphMemoryUpdater]:
        """Updater der Simulation abrufen"""
        return cls._updaters.get(simulation_id)
    
    @classmethod
    def stop_updater(cls, simulation_id: str):
        """Updater der Simulation stoppen und entfernen"""
        with cls._lock:
            if simulation_id in cls._updaters:
                cls._updaters[simulation_id].stop()
                del cls._updaters[simulation_id]
                logger.info(f"Graph-Speicher-Updater gestoppt: simulation_id={simulation_id}")
    
    # Flag zur Vermeidung wiederholter stop_all-Aufrufe
    _stop_all_done = False
    
    @classmethod
    def stop_all(cls):
        """Alle Updater stoppen"""
        # Wiederholten Aufruf verhindern
        if cls._stop_all_done:
            return
        cls._stop_all_done = True
        
        with cls._lock:
            if cls._updaters:
                for simulation_id, updater in list(cls._updaters.items()):
                    try:
                        updater.stop()
                    except Exception as e:
                        logger.error(f"Updater stoppen fehlgeschlagen: simulation_id={simulation_id}, error={e}")
                cls._updaters.clear()
            logger.info("Alle Graph-Speicher-Updater gestoppt")
    
    @classmethod
    def get_all_stats(cls) -> Dict[str, Dict[str, Any]]:
        """Statistiken aller Updater abrufen"""
        return {
            sim_id: updater.get_stats() 
            for sim_id, updater in cls._updaters.items()
        }
