"""
OASIS-Simulations-Runner
Führt die Simulation im Hintergrund aus und zeichnet die Aktionen jedes Agents auf, unterstützt Echtzeit-Statusüberwachung
"""

import os
import sys
import json
import time
import asyncio
import threading
import subprocess
import signal
import atexit
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from queue import Queue

from ..config import Config
from ..utils.logger import get_logger
from .zep_graph_memory_updater import ZepGraphMemoryManager
from .simulation_ipc import SimulationIPCClient, CommandType, IPCResponse

logger = get_logger('mirofish.simulation_runner')

# Markierung, ob Bereinigungsfunktion registriert wurde
_cleanup_registered = False

# Plattformerkennung
IS_WINDOWS = sys.platform == 'win32'


class RunnerStatus(str, Enum):
    """Runner-Status"""
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentAction:
    """Agent-Aktionsaufzeichnung"""
    round_num: int
    timestamp: str
    platform: str  # twitter / reddit
    agent_id: int
    agent_name: str
    action_type: str  # CREATE_POST, LIKE_POST, etc.
    action_args: Dict[str, Any] = field(default_factory=dict)
    result: Optional[str] = None
    success: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_num": self.round_num,
            "timestamp": self.timestamp,
            "platform": self.platform,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "action_type": self.action_type,
            "action_args": self.action_args,
            "result": self.result,
            "success": self.success,
        }


@dataclass
class RoundSummary:
    """Runden-Zusammenfassung"""
    round_num: int
    start_time: str
    end_time: Optional[str] = None
    simulated_hour: int = 0
    twitter_actions: int = 0
    reddit_actions: int = 0
    active_agents: List[int] = field(default_factory=list)
    actions: List[AgentAction] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_num": self.round_num,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "simulated_hour": self.simulated_hour,
            "twitter_actions": self.twitter_actions,
            "reddit_actions": self.reddit_actions,
            "active_agents": self.active_agents,
            "actions_count": len(self.actions),
            "actions": [a.to_dict() for a in self.actions],
        }


@dataclass
class SimulationRunState:
    """Simulationslaufstatus (Echtzeit)"""
    simulation_id: str
    runner_status: RunnerStatus = RunnerStatus.IDLE
    
    # Fortschrittsinformationen
    current_round: int = 0
    total_rounds: int = 0
    simulated_hours: int = 0
    total_simulation_hours: int = 0
    
    # Plattform-spezifische Runden und Simulationszeit (für Dual-Plattform-Parallelanzeige)
    twitter_current_round: int = 0
    reddit_current_round: int = 0
    twitter_simulated_hours: int = 0
    reddit_simulated_hours: int = 0
    
    # Plattformstatus
    twitter_running: bool = False
    reddit_running: bool = False
    twitter_actions_count: int = 0
    reddit_actions_count: int = 0
    
    # Plattform-Abschlussstatus (erkannt durch simulation_end-Ereignis in actions.jsonl)
    twitter_completed: bool = False
    reddit_completed: bool = False
    
    # Runden-Zusammenfassungen
    rounds: List[RoundSummary] = field(default_factory=list)
    
    # Aktuelle Aktionen (für Frontend-Echtzeitanzeige)
    recent_actions: List[AgentAction] = field(default_factory=list)
    max_recent_actions: int = 50
    
    # Zeitstempel
    started_at: Optional[str] = None
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    
    # Fehlerinformationen
    error: Optional[str] = None
    
    # Prozess-ID (zum Stoppen)
    process_pid: Optional[int] = None
    
    def add_action(self, action: AgentAction):
        """Aktion zur Liste aktueller Aktionen hinzufügen"""
        self.recent_actions.insert(0, action)
        if len(self.recent_actions) > self.max_recent_actions:
            self.recent_actions = self.recent_actions[:self.max_recent_actions]
        
        if action.platform == "twitter":
            self.twitter_actions_count += 1
        else:
            self.reddit_actions_count += 1
        
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "simulation_id": self.simulation_id,
            "runner_status": self.runner_status.value,
            "current_round": self.current_round,
            "total_rounds": self.total_rounds,
            "simulated_hours": self.simulated_hours,
            "total_simulation_hours": self.total_simulation_hours,
            "progress_percent": round(self.current_round / max(self.total_rounds, 1) * 100, 1),
            # Plattform-spezifische Runden und Zeit
            "twitter_current_round": self.twitter_current_round,
            "reddit_current_round": self.reddit_current_round,
            "twitter_simulated_hours": self.twitter_simulated_hours,
            "reddit_simulated_hours": self.reddit_simulated_hours,
            "twitter_running": self.twitter_running,
            "reddit_running": self.reddit_running,
            "twitter_completed": self.twitter_completed,
            "reddit_completed": self.reddit_completed,
            "twitter_actions_count": self.twitter_actions_count,
            "reddit_actions_count": self.reddit_actions_count,
            "total_actions_count": self.twitter_actions_count + self.reddit_actions_count,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "process_pid": self.process_pid,
        }
    
    def to_detail_dict(self) -> Dict[str, Any]:
        """Detaillierte Informationen inkl. aktueller Aktionen"""
        result = self.to_dict()
        result["recent_actions"] = [a.to_dict() for a in self.recent_actions]
        result["rounds_count"] = len(self.rounds)
        return result


class SimulationRunner:
    """
    Simulations-Runner
    
    Verantwortlich für:
    1. Ausführen der OASIS-Simulation im Hintergrundprozess
    2. Parsen von Ausführungsprotokollen, Aufzeichnen der Aktionen jedes Agents
    3. Bereitstellung der Echtzeit-Statusabfrage-Schnittstelle
    4. Unterstützung von Pause/Stopp/Wiederaufnahme
    """
    
    # Speicherverzeichnis für Laufstatus
    RUN_STATE_DIR = os.path.join(
        os.path.dirname(__file__),
        '../../uploads/simulations'
    )
    
    # Skriptverzeichnis
    SCRIPTS_DIR = os.path.join(
        os.path.dirname(__file__),
        '../../scripts'
    )
    
    # Laufstatus im Speicher
    _run_states: Dict[str, SimulationRunState] = {}
    _processes: Dict[str, subprocess.Popen] = {}
    _action_queues: Dict[str, Queue] = {}
    _monitor_threads: Dict[str, threading.Thread] = {}
    _stdout_files: Dict[str, Any] = {}  # Speicherung von stdout Datei-Handles
    _stderr_files: Dict[str, Any] = {}  # Speicherung von stderr Datei-Handles
    
    # Graphenspeicher-Update-Konfiguration
    _graph_memory_enabled: Dict[str, bool] = {}  # simulation_id -> enabled
    
    @classmethod
    def get_run_state(cls, simulation_id: str) -> Optional[SimulationRunState]:
        """Laufstatus abrufen"""
        if simulation_id in cls._run_states:
            return cls._run_states[simulation_id]
        
        # Versuchen, aus Datei zu laden
        state = cls._load_run_state(simulation_id)
        if state:
            cls._run_states[simulation_id] = state
        return state
    
    @classmethod
    def _load_run_state(cls, simulation_id: str) -> Optional[SimulationRunState]:
        """Laufstatus aus Datei laden"""
        state_file = os.path.join(cls.RUN_STATE_DIR, simulation_id, "run_state.json")
        if not os.path.exists(state_file):
            return None
        
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            state = SimulationRunState(
                simulation_id=simulation_id,
                runner_status=RunnerStatus(data.get("runner_status", "idle")),
                current_round=data.get("current_round", 0),
                total_rounds=data.get("total_rounds", 0),
                simulated_hours=data.get("simulated_hours", 0),
                total_simulation_hours=data.get("total_simulation_hours", 0),
                # Plattform-spezifische Runden und Zeit
                twitter_current_round=data.get("twitter_current_round", 0),
                reddit_current_round=data.get("reddit_current_round", 0),
                twitter_simulated_hours=data.get("twitter_simulated_hours", 0),
                reddit_simulated_hours=data.get("reddit_simulated_hours", 0),
                twitter_running=data.get("twitter_running", False),
                reddit_running=data.get("reddit_running", False),
                twitter_completed=data.get("twitter_completed", False),
                reddit_completed=data.get("reddit_completed", False),
                twitter_actions_count=data.get("twitter_actions_count", 0),
                reddit_actions_count=data.get("reddit_actions_count", 0),
                started_at=data.get("started_at"),
                updated_at=data.get("updated_at", datetime.now().isoformat()),
                completed_at=data.get("completed_at"),
                error=data.get("error"),
                process_pid=data.get("process_pid"),
            )
            
            # Aktuelle Aktionen laden
            actions_data = data.get("recent_actions", [])
            for a in actions_data:
                state.recent_actions.append(AgentAction(
                    round_num=a.get("round_num", 0),
                    timestamp=a.get("timestamp", ""),
                    platform=a.get("platform", ""),
                    agent_id=a.get("agent_id", 0),
                    agent_name=a.get("agent_name", ""),
                    action_type=a.get("action_type", ""),
                    action_args=a.get("action_args", {}),
                    result=a.get("result"),
                    success=a.get("success", True),
                ))
            
            return state
        except Exception as e:
            logger.error(f"Laden des Laufstatus fehlgeschlagen: {str(e)}")
            return None
    
    @classmethod
    def _save_run_state(cls, state: SimulationRunState):
        """Laufstatus in Datei speichern"""
        sim_dir = os.path.join(cls.RUN_STATE_DIR, state.simulation_id)
        os.makedirs(sim_dir, exist_ok=True)
        state_file = os.path.join(sim_dir, "run_state.json")
        
        data = state.to_detail_dict()
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        cls._run_states[state.simulation_id] = state
    
    @classmethod
    def start_simulation(
        cls,
        simulation_id: str,
        platform: str = "parallel",  # twitter / reddit / parallel
        max_rounds: int = None,  # Maximale Simulationsrunden (optional, zum Kürzen zu langer Simulationen)
        enable_graph_memory_update: bool = False,  # Ob Aktivitäten in Zep-Graphen aktualisiert werden sollen
        graph_id: str = None  # Zep-Graphen-ID (erforderlich, wenn Graphen-Update aktiviert)
    ) -> SimulationRunState:
        """
        Simulation starten
        
        Args:
            simulation_id: Simulations-ID
            platform: Ausführungsplattform (twitter/reddit/parallel)
            max_rounds: Maximale Simulationsrunden (optional, zum Kürzen zu langer Simulationen)
            enable_graph_memory_update: Ob Agent-Aktivitäten dynamisch in Zep-Graphen aktualisiert werden sollen
            graph_id: Zep-Graphen-ID (erforderlich, wenn Graphen-Update aktiviert)
            
        Returns:
            SimulationRunState
        """
        # Prüfen, ob bereits läuft
        existing = cls.get_run_state(simulation_id)
        if existing and existing.runner_status in [RunnerStatus.RUNNING, RunnerStatus.STARTING]:
            raise ValueError(f"Simulation läuft bereits: {simulation_id}")
        
        # Simulationskonfiguration laden
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        config_path = os.path.join(sim_dir, "simulation_config.json")
        
        if not os.path.exists(config_path):
            raise ValueError(f"Simulationskonfiguration existiert nicht, bitte rufen Sie zuerst die /prepare Schnittstelle auf")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Laufstatus initialisieren
        time_config = config.get("time_config", {})
        total_hours = time_config.get("total_simulation_hours", 72)
        minutes_per_round = time_config.get("minutes_per_round", 30)
        total_rounds = int(total_hours * 60 / minutes_per_round)
        
        # Wenn maximale Runden angegeben, kürzen
        if max_rounds is not None and max_rounds > 0:
            original_rounds = total_rounds
            total_rounds = min(total_rounds, max_rounds)
            if total_rounds < original_rounds:
                logger.info(f"Runden gekürzt: {original_rounds} -> {total_rounds} (max_rounds={max_rounds})")
        
        state = SimulationRunState(
            simulation_id=simulation_id,
            runner_status=RunnerStatus.STARTING,
            total_rounds=total_rounds,
            total_simulation_hours=total_hours,
            started_at=datetime.now().isoformat(),
        )
        
        cls._save_run_state(state)
        
        # Wenn Graphenspeicher-Update aktiviert, Updater erstellen
        if enable_graph_memory_update:
            if not graph_id:
                raise ValueError("graph_id muss angegeben werden, wenn Graphenspeicher-Update aktiviert ist")
            
            try:
                ZepGraphMemoryManager.create_updater(simulation_id, graph_id)
                cls._graph_memory_enabled[simulation_id] = True
                logger.info(f"Graphenspeicher-Update aktiviert: simulation_id={simulation_id}, graph_id={graph_id}")
            except Exception as e:
                logger.error(f"Erstellen des Graphenspeicher-Updaters fehlgeschlagen: {e}")
                cls._graph_memory_enabled[simulation_id] = False
        else:
            cls._graph_memory_enabled[simulation_id] = False
        
        # Bestimmen, welches Skript ausgeführt werden soll (Skripte im backend/scripts/ Verzeichnis)
        if platform == "twitter":
            script_name = "run_twitter_simulation.py"
            state.twitter_running = True
        elif platform == "reddit":
            script_name = "run_reddit_simulation.py"
            state.reddit_running = True
        else:
            script_name = "run_parallel_simulation.py"
            state.twitter_running = True
            state.reddit_running = True
        
        script_path = os.path.join(cls.SCRIPTS_DIR, script_name)
        
        if not os.path.exists(script_path):
            raise ValueError(f"Skript existiert nicht: {script_path}")
        
        # Aktionswarteschlange erstellen
        action_queue = Queue()
        cls._action_queues[simulation_id] = action_queue
        
        # Simulationsprozess starten
        try:
            # Ausführungsbefehl mit vollständigem Pfad aufbauen
            # Neue Protokollstruktur:
            #   twitter/actions.jsonl - Twitter-Aktionsprotokoll
            #   reddit/actions.jsonl  - Reddit-Aktionsprotokoll
            #   simulation.log        - Hauptprozessprotokoll
            
            cmd = [
                sys.executable,  # Python-Interpreter
                script_path,
                "--config", config_path,  # Verwende vollständigen Konfigurationsdateipfad
            ]
            
            # Wenn maximale Runden angegeben, zu Befehlszeilenargumenten hinzufügen
            if max_rounds is not None and max_rounds > 0:
                cmd.extend(["--max-rounds", str(max_rounds)])
            
            # Hauptprotokolldatei erstellen, um stdout/stderr-Puffer-Überlauf zu vermeiden
            main_log_path = os.path.join(sim_dir, "simulation.log")
            main_log_file = open(main_log_path, 'w', encoding='utf-8')
            
            # Umgebungsvariablen für Unterprozess setzen, um UTF-8-Kodierung auf Windows sicherzustellen
            # Behebt Probleme mit Drittanbieter-Bibliotheken (wie OASIS), die Dateien ohne Kodierungsangabe lesen
            env = os.environ.copy()
            env['PYTHONUTF8'] = '1'  # Python 3.7+ unterstützt dies, lässt open() standardmäßig UTF-8 verwenden
            env['PYTHONIOENCODING'] = 'utf-8'  # Sicherstellen, dass stdout/stderr UTF-8 verwenden
            
            # Arbeitsverzeichnis auf Simulationsverzeichnis setzen (Datenbanken etc. werden hier erstellt)
            # Verwendet start_new_session=True, um neue Prozessgruppe zu erstellen, damit alle Unterprozesse über os.killpg beendet werden können
            process = subprocess.Popen(
                cmd,
                cwd=sim_dir,
                stdout=main_log_file,
                stderr=subprocess.STDOUT,  # stderr auch in dieselbe Datei schreiben
                text=True,
                encoding='utf-8',  # Kodierung explizit angeben
                bufsize=1,
                env=env,  # Umgebung mit UTF-8-Einstellungen übergeben
                start_new_session=True,  # Neue Prozessgruppe erstellen, um alle zugehörigen Prozesse beim Server-Stop zu beenden
            )
            
            # Datei-Handles für späteres Schließen speichern
            cls._stdout_files[simulation_id] = main_log_file
            cls._stderr_files[simulation_id] = None  # Kein separates stderr mehr benötigt
            
            state.process_pid = process.pid
            state.runner_status = RunnerStatus.RUNNING
            cls._processes[simulation_id] = process
            cls._save_run_state(state)
            
            # Überwachungsthread starten
            monitor_thread = threading.Thread(
                target=cls._monitor_simulation,
                args=(simulation_id,),
                daemon=True
            )
            monitor_thread.start()
            cls._monitor_threads[simulation_id] = monitor_thread
            
            logger.info(f"Simulation erfolgreich gestartet: {simulation_id}, pid={process.pid}, platform={platform}")
            
        except Exception as e:
            state.runner_status = RunnerStatus.FAILED
            state.error = str(e)
            cls._save_run_state(state)
            raise
        
        return state
    
    @classmethod
    def _monitor_simulation(cls, simulation_id: str):
        """Simulationsprozess überwachen, Aktionsprotokolle parsen"""
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        
        # Neue Protokollstruktur: Plattform-spezifische Aktionsprotokolle
        twitter_actions_log = os.path.join(sim_dir, "twitter", "actions.jsonl")
        reddit_actions_log = os.path.join(sim_dir, "reddit", "actions.jsonl")
        
        process = cls._processes.get(simulation_id)
        state = cls.get_run_state(simulation_id)
        
        if not process or not state:
            return
        
        twitter_position = 0
        reddit_position = 0
        
        try:
            while process.poll() is None:  # Prozess läuft noch
                # Twitter-Aktionsprotokoll lesen
                if os.path.exists(twitter_actions_log):
                    twitter_position = cls._read_action_log(
                        twitter_actions_log, twitter_position, state, "twitter"
                    )
                
                # Reddit-Aktionsprotokoll lesen
                if os.path.exists(reddit_actions_log):
                    reddit_position = cls._read_action_log(
                        reddit_actions_log, reddit_position, state, "reddit"
                    )
                
                # Status aktualisieren
                cls._save_run_state(state)
                time.sleep(2)
            
            # Nach Prozessende Protokoll ein letztes Mal lesen
            if os.path.exists(twitter_actions_log):
                cls._read_action_log(twitter_actions_log, twitter_position, state, "twitter")
            if os.path.exists(reddit_actions_log):
                cls._read_action_log(reddit_actions_log, reddit_position, state, "reddit")
            
            # Prozess beendet
            exit_code = process.returncode
            
            if exit_code == 0:
                state.runner_status = RunnerStatus.COMPLETED
                state.completed_at = datetime.now().isoformat()
                logger.info(f"Simulation abgeschlossen: {simulation_id}")
            else:
                state.runner_status = RunnerStatus.FAILED
                # Fehlerinformationen aus Hauptprotokolldatei lesen
                main_log_path = os.path.join(sim_dir, "simulation.log")
                error_info = ""
                try:
                    if os.path.exists(main_log_path):
                        with open(main_log_path, 'r', encoding='utf-8') as f:
                            error_info = f.read()[-2000:]  # Letzte 2000 Zeichen nehmen
                except Exception:
                    pass
                state.error = f"Prozess-Exit-Code: {exit_code}, Fehler: {error_info}"
                logger.error(f"Simulation fehlgeschlagen: {simulation_id}, error={state.error}")
            
            state.twitter_running = False
            state.reddit_running = False
            cls._save_run_state(state)
            
        except Exception as e:
            logger.error(f"Überwachungsthread-Ausnahme: {simulation_id}, error={str(e)}")
            state.runner_status = RunnerStatus.FAILED
            state.error = str(e)
            cls._save_run_state(state)
        
        finally:
            # Graphenspeicher-Updater stoppen
            if cls._graph_memory_enabled.get(simulation_id, False):
                try:
                    ZepGraphMemoryManager.stop_updater(simulation_id)
                    logger.info(f"Graphenspeicher-Update gestoppt: simulation_id={simulation_id}")
                except Exception as e:
                    logger.error(f"Stoppen des Graphenspeicher-Updaters fehlgeschlagen: {e}")
                cls._graph_memory_enabled.pop(simulation_id, None)
            
            # Prozessressourcen bereinigen
            cls._processes.pop(simulation_id, None)
            cls._action_queues.pop(simulation_id, None)
            
            # Protokolldatei-Handles schließen
            if simulation_id in cls._stdout_files:
                try:
                    cls._stdout_files[simulation_id].close()
                except Exception:
                    pass
                cls._stdout_files.pop(simulation_id, None)
            if simulation_id in cls._stderr_files and cls._stderr_files[simulation_id]:
                try:
                    cls._stderr_files[simulation_id].close()
                except Exception:
                    pass
                cls._stderr_files.pop(simulation_id, None)
    
    @classmethod
    def _read_action_log(
        cls, 
        log_path: str, 
        position: int, 
        state: SimulationRunState,
        platform: str
    ) -> int:
        """
        Aktionsprotokolldatei lesen
        
        Args:
            log_path: Protokolldateipfad
            position: Letzte Leseposition
            state: Laufstatusobjekt
            platform: Plattformname (twitter/reddit)
            
        Returns:
            Neue Leseposition
        """
        # Prüfen, ob Graphenspeicher-Update aktiviert ist
        graph_memory_enabled = cls._graph_memory_enabled.get(state.simulation_id, False)
        graph_updater = None
        if graph_memory_enabled:
            graph_updater = ZepGraphMemoryManager.get_updater(state.simulation_id)
        
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                f.seek(position)
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            action_data = json.loads(line)
                            
                            # Ereignistyp-Einträge verarbeiten
                            if "event_type" in action_data:
                                event_type = action_data.get("event_type")
                                
                                # simulation_end-Ereignis erkennen, Plattform als abgeschlossen markieren
                                if event_type == "simulation_end":
                                    if platform == "twitter":
                                        state.twitter_completed = True
                                        state.twitter_running = False
                                        logger.info(f"Twitter-Simulation abgeschlossen: {state.simulation_id}, total_rounds={action_data.get('total_rounds')}, total_actions={action_data.get('total_actions')}")
                                    elif platform == "reddit":
                                        state.reddit_completed = True
                                        state.reddit_running = False
                                        logger.info(f"Reddit-Simulation abgeschlossen: {state.simulation_id}, total_rounds={action_data.get('total_rounds')}, total_actions={action_data.get('total_actions')}")
                                    
                                    # Prüfen, ob alle aktivierten Plattformen abgeschlossen sind
                                    # Wenn nur eine Plattform läuft, nur diese prüfen
                                    # Wenn zwei Plattformen laufen, müssen beide abgeschlossen sein
                                    all_completed = cls._check_all_platforms_completed(state)
                                    if all_completed:
                                        state.runner_status = RunnerStatus.COMPLETED
                                        state.completed_at = datetime.now().isoformat()
                                        logger.info(f"Alle Plattform-Simulationen abgeschlossen: {state.simulation_id}")
                                
                                # Rundeninformationen aktualisieren (aus round_end-Ereignis)
                                elif event_type == "round_end":
                                    round_num = action_data.get("round", 0)
                                    simulated_hours = action_data.get("simulated_hours", 0)
                                    
                                    # Plattform-spezifische Runden und Zeit aktualisieren
                                    if platform == "twitter":
                                        if round_num > state.twitter_current_round:
                                            state.twitter_current_round = round_num
                                        state.twitter_simulated_hours = simulated_hours
                                    elif platform == "reddit":
                                        if round_num > state.reddit_current_round:
                                            state.reddit_current_round = round_num
                                        state.reddit_simulated_hours = simulated_hours
                                    
                                    # Gesamtrunde als Maximum beider Plattformen
                                    if round_num > state.current_round:
                                        state.current_round = round_num
                                    # Gesamtzeit als Maximum beider Plattformen
                                    state.simulated_hours = max(state.twitter_simulated_hours, state.reddit_simulated_hours)
                                
                                continue
                            
                            action = AgentAction(
                                round_num=action_data.get("round", 0),
                                timestamp=action_data.get("timestamp", datetime.now().isoformat()),
                                platform=platform,
                                agent_id=action_data.get("agent_id", 0),
                                agent_name=action_data.get("agent_name", ""),
                                action_type=action_data.get("action_type", ""),
                                action_args=action_data.get("action_args", {}),
                                result=action_data.get("result"),
                                success=action_data.get("success", True),
                            )
                            state.add_action(action)
                            
                            # Runde aktualisieren
                            if action.round_num and action.round_num > state.current_round:
                                state.current_round = action.round_num
                            
                            # Wenn Graphenspeicher-Update aktiviert, Aktivität an Zep senden
                            if graph_updater:
                                graph_updater.add_activity_from_dict(action_data, platform)
                            
                        except json.JSONDecodeError:
                            pass
                return f.tell()
        except Exception as e:
            logger.warning(f"Lesen des Aktionsprotokolls fehlgeschlagen: {log_path}, error={e}")
            return position
    
    @classmethod
    def _check_all_platforms_completed(cls, state: SimulationRunState) -> bool:
        """
        Prüfen, ob alle aktivierten Plattformen die Simulation abgeschlossen haben
        
        Durch Prüfung der entsprechenden actions.jsonl-Datei auf Existenz wird bestimmt, welche Plattformen aktiviert sind
        
        Returns:
            True, wenn alle aktivierten Plattformen abgeschlossen sind
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, state.simulation_id)
        twitter_log = os.path.join(sim_dir, "twitter", "actions.jsonl")
        reddit_log = os.path.join(sim_dir, "reddit", "actions.jsonl")
        
        # Prüfen, welche Plattformen aktiviert sind (durch Dateiexistenz)
        twitter_enabled = os.path.exists(twitter_log)
        reddit_enabled = os.path.exists(reddit_log)
        
        # Wenn Plattform aktiviert, aber nicht abgeschlossen, False zurückgeben
        if twitter_enabled and not state.twitter_completed:
            return False
        if reddit_enabled and not state.reddit_completed:
            return False
        
        # Mindestens eine Plattform aktiviert und abgeschlossen
        return twitter_enabled or reddit_enabled
    
    @classmethod
    def _terminate_process(cls, process: subprocess.Popen, simulation_id: str, timeout: int = 10):
        """
        Prozess und Unterprozesse plattformübergreifend beenden
        
        Args:
            process: Zu beendender Prozess
            simulation_id: Simulations-ID (für Protokoll)
            timeout: Zeitlimit für Warten auf Prozessende (Sekunden)
        """
        if IS_WINDOWS:
            # Windows: Verwendet taskkill-Befehl zum Beenden des Prozessbaums
            # /F = Erzwingen, /T = Prozessbaum beenden (inkl. Unterprozesse)
            logger.info(f"Beende Prozessbaum (Windows): simulation={simulation_id}, pid={process.pid}")
            try:
                # Zuerst graceful beenden versuchen
                subprocess.run(
                    ['taskkill', '/PID', str(process.pid), '/T'],
                    capture_output=True,
                    timeout=5
                )
                try:
                    process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    # Erzwungenes Beenden
                    logger.warning(f"Prozess nicht responsiv, erzwungenes Beenden: {simulation_id}")
                    subprocess.run(
                        ['taskkill', '/F', '/PID', str(process.pid), '/T'],
                        capture_output=True,
                        timeout=5
                    )
                    process.wait(timeout=5)
            except Exception as e:
                logger.warning(f"taskkill fehlgeschlagen, versuche terminate: {e}")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        else:
            # Unix: Verwendet Prozessgruppen-Beendigung
            # Da start_new_session=True verwendet wurde, ist Prozessgruppen-ID gleich Hauptprozess-PID
            pgid = os.getpgid(process.pid)
            logger.info(f"Beende Prozessgruppe (Unix): simulation={simulation_id}, pgid={pgid}")
            
            # Zuerst SIGTERM an gesamte Prozessgruppe senden
            os.killpg(pgid, signal.SIGTERM)
            
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                # Wenn nach Timeout noch nicht beendet, SIGKILL erzwingen
                logger.warning(f"Prozessgruppe nicht responsiv auf SIGTERM, erzwungenes Beenden: {simulation_id}")
                os.killpg(pgid, signal.SIGKILL)
                process.wait(timeout=5)
    
    @classmethod
    def stop_simulation(cls, simulation_id: str) -> SimulationRunState:
        """Simulation stoppen"""
        state = cls.get_run_state(simulation_id)
        if not state:
            raise ValueError(f"Simulation existiert nicht: {simulation_id}")
        
        if state.runner_status not in [RunnerStatus.RUNNING, RunnerStatus.PAUSED]:
            raise ValueError(f"Simulation läuft nicht: {simulation_id}, status={state.runner_status}")
        
        state.runner_status = RunnerStatus.STOPPING
        cls._save_run_state(state)
        
        # Prozess beenden
        process = cls._processes.get(simulation_id)
        if process and process.poll() is None:
            try:
                cls._terminate_process(process, simulation_id)
            except ProcessLookupError:
                # Prozess existiert bereits nicht mehr
                pass
            except Exception as e:
                logger.error(f"Beenden der Prozessgruppe fehlgeschlagen: {simulation_id}, error={e}")
                # Fallback zum direkten Prozess-Beenden
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except Exception:
                    process.kill()
        
        state.runner_status = RunnerStatus.STOPPED
        state.twitter_running = False
        state.reddit_running = False
        state.completed_at = datetime.now().isoformat()
        cls._save_run_state(state)
        
        # Graphenspeicher-Updater stoppen
        if cls._graph_memory_enabled.get(simulation_id, False):
            try:
                ZepGraphMemoryManager.stop_updater(simulation_id)
                logger.info(f"Graphenspeicher-Update gestoppt: simulation_id={simulation_id}")
            except Exception as e:
                logger.error(f"Stoppen des Graphenspeicher-Updaters fehlgeschlagen: {e}")
            cls._graph_memory_enabled.pop(simulation_id, None)
        
        logger.info(f"Simulation gestoppt: {simulation_id}")
        return state
    
    @classmethod
    def _read_actions_from_file(
        cls,
        file_path: str,
        default_platform: Optional[str] = None,
        platform_filter: Optional[str] = None,
        agent_id: Optional[int] = None,
        round_num: Optional[int] = None
    ) -> List[AgentAction]:
        """
        Aktionen aus einzelner Aktionsdatei lesen
        
        Args:
            file_path: Aktionsprotokolldateipfad
            default_platform: Standardplattform (wenn Aktionsdatensatz kein platform-Feld enthält)
            platform_filter: Plattform filtern
            agent_id: Agent-ID filtern
            round_num: Runde filtern
        """
        if not os.path.exists(file_path):
            return []
        
        actions = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    
                    # Nicht-Aktions-Einträge überspringen (wie simulation_start, round_start, round_end usw.)
                    if "event_type" in data:
                        continue
                    
                    # Einträge ohne agent_id überspringen (keine Agent-Aktionen)
                    if "agent_id" not in data:
                        continue
                    
                    # Plattform abrufen: Priorität hat platform im Datensatz, sonst Standardplattform
                    record_platform = data.get("platform") or default_platform or ""
                    
                    # Filtern
                    if platform_filter and record_platform != platform_filter:
                        continue
                    if agent_id is not None and data.get("agent_id") != agent_id:
                        continue
                    if round_num is not None and data.get("round") != round_num:
                        continue
                    
                    actions.append(AgentAction(
                        round_num=data.get("round", 0),
                        timestamp=data.get("timestamp", ""),
                        platform=record_platform,
                        agent_id=data.get("agent_id", 0),
                        agent_name=data.get("agent_name", ""),
                        action_type=data.get("action_type", ""),
                        action_args=data.get("action_args", {}),
                        result=data.get("result"),
                        success=data.get("success", True),
                    ))
                    
                except json.JSONDecodeError:
                    continue
        
        return actions
    
    @classmethod
    def get_all_actions(
        cls,
        simulation_id: str,
        platform: Optional[str] = None,
        agent_id: Optional[int] = None,
        round_num: Optional[int] = None
    ) -> List[AgentAction]:
        """
        Vollständige Aktionshistorie aller Plattformen abrufen (keine Paginierungsbegrenzung)
        
        Args:
            simulation_id: Simulations-ID
            platform: Plattform filtern (twitter/reddit)
            agent_id: Agent filtern
            round_num: Runde filtern
            
        Returns:
            Vollständige Aktionsliste (nach Zeitstempel sortiert, neue zuerst)
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        actions = []
        
        # Twitter-Aktionsdatei lesen (plattform automatisch als twitter basierend auf Dateipfad setzen)
        twitter_actions_log = os.path.join(sim_dir, "twitter", "actions.jsonl")
        if not platform or platform == "twitter":
            actions.extend(cls._read_actions_from_file(
                twitter_actions_log,
                default_platform="twitter",  # platform-Feld automatisch füllen
                platform_filter=platform,
                agent_id=agent_id, 
                round_num=round_num
            ))
        
        # Reddit-Aktionsdatei lesen (plattform automatisch als reddit basierend auf Dateipfad setzen)
        reddit_actions_log = os.path.join(sim_dir, "reddit", "actions.jsonl")
        if not platform or platform == "reddit":
            actions.extend(cls._read_actions_from_file(
                reddit_actions_log,
                default_platform="reddit",  # platform-Feld automatisch füllen
                platform_filter=platform,
                agent_id=agent_id,
                round_num=round_num
            ))
        
        # Wenn plattform-spezifische Dateien nicht existieren, altes einzelnes Dateiformat versuchen
        if not actions:
            actions_log = os.path.join(sim_dir, "actions.jsonl")
            actions = cls._read_actions_from_file(
                actions_log,
                default_platform=None,  # Altes Format sollte platform-Feld enthalten
                platform_filter=platform,
                agent_id=agent_id,
                round_num=round_num
            )
        
        # Nach Zeitstempel sortieren (neue zuerst)
        actions.sort(key=lambda x: x.timestamp, reverse=True)
        
        return actions
    
    @classmethod
    def get_actions(
        cls,
        simulation_id: str,
        limit: int = 100,
        offset: int = 0,
        platform: Optional[str] = None,
        agent_id: Optional[int] = None,
        round_num: Optional[int] = None
    ) -> List[AgentAction]:
        """
        Aktionshistorie abrufen (mit Paginierung)
        
        Args:
            simulation_id: Simulations-ID
            limit: Rückgabelimit
            offset: Offset
            platform: Plattform filtern
            agent_id: Agent filtern
            round_num: Runde filtern
            
        Returns:
            Aktionsliste
        """
        actions = cls.get_all_actions(
            simulation_id=simulation_id,
            platform=platform,
            agent_id=agent_id,
            round_num=round_num
        )
        
        # Paginierung
        return actions[offset:offset + limit]
    
    @classmethod
    def get_timeline(
        cls,
        simulation_id: str,
        start_round: int = 0,
        end_round: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Simulations-Zeitlinie abrufen (nach Runden zusammengefasst)
        
        Args:
            simulation_id: Simulations-ID
            start_round: Start-Runde
            end_round: End-Runde
            
        Returns:
            Zusammenfassungsinformationen pro Runde
        """
        actions = cls.get_actions(simulation_id, limit=10000)
        
        # Nach Runden gruppieren
        rounds: Dict[int, Dict[str, Any]] = {}
        
        for action in actions:
            round_num = action.round_num
            
            if round_num < start_round:
                continue
            if end_round is not None and round_num > end_round:
                continue
            
            if round_num not in rounds:
                rounds[round_num] = {
                    "round_num": round_num,
                    "twitter_actions": 0,
                    "reddit_actions": 0,
                    "active_agents": set(),
                    "action_types": {},
                    "first_action_time": action.timestamp,
                    "last_action_time": action.timestamp,
                }
            
            r = rounds[round_num]
            
            if action.platform == "twitter":
                r["twitter_actions"] += 1
            else:
                r["reddit_actions"] += 1
            
            r["active_agents"].add(action.agent_id)
            r["action_types"][action.action_type] = r["action_types"].get(action.action_type, 0) + 1
            r["last_action_time"] = action.timestamp
        
        # In Liste konvertieren
        result = []
        for round_num in sorted(rounds.keys()):
            r = rounds[round_num]
            result.append({
                "round_num": round_num,
                "twitter_actions": r["twitter_actions"],
                "reddit_actions": r["reddit_actions"],
                "total_actions": r["twitter_actions"] + r["reddit_actions"],
                "active_agents_count": len(r["active_agents"]),
                "active_agents": list(r["active_agents"]),
                "action_types": r["action_types"],
                "first_action_time": r["first_action_time"],
                "last_action_time": r["last_action_time"],
            })
        
        return result
    
    @classmethod
    def get_agent_stats(cls, simulation_id: str) -> List[Dict[str, Any]]:
        """
        Statistiken für jeden Agenten abrufen
        
        Returns:
            Agent-Statistikliste
        """
        actions = cls.get_actions(simulation_id, limit=10000)
        
        agent_stats: Dict[int, Dict[str, Any]] = {}
        
        for action in actions:
            agent_id = action.agent_id
            
            if agent_id not in agent_stats:
                agent_stats[agent_id] = {
                    "agent_id": agent_id,
                    "agent_name": action.agent_name,
                    "total_actions": 0,
                    "twitter_actions": 0,
                    "reddit_actions": 0,
                    "action_types": {},
                    "first_action_time": action.timestamp,
                    "last_action_time": action.timestamp,
                }
            
            stats = agent_stats[agent_id]
            stats["total_actions"] += 1
            
            if action.platform == "twitter":
                stats["twitter_actions"] += 1
            else:
                stats["reddit_actions"] += 1
            
            stats["action_types"][action.action_type] = stats["action_types"].get(action.action_type, 0) + 1
            stats["last_action_time"] = action.timestamp
        
        # Nach Gesamtaktionen sortieren
        result = sorted(agent_stats.values(), key=lambda x: x["total_actions"], reverse=True)
        
        return result
    
    @classmethod
    def cleanup_simulation_logs(cls, simulation_id: str) -> Dict[str, Any]:
        """
        Simulationslaufprotokolle bereinigen (für Neustart der Simulation)
        
        Löscht folgende Dateien:
        - run_state.json
        - twitter/actions.jsonl
        - reddit/actions.jsonl
        - simulation.log
        - stdout.log / stderr.log
        - twitter_simulation.db (Simulationsdatenbank)
        - reddit_simulation.db (Simulationsdatenbank)
        - env_status.json (Umgebungsstatus)
        
        Hinweis: Konfigurationsdateien (simulation_config.json) und Profile-Dateien werden nicht gelöscht
        
        Args:
            simulation_id: Simulations-ID
            
        Returns:
            Bereinigungsergebnisinformationen
        """
        import shutil
        
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        
        if not os.path.exists(sim_dir):
            return {"success": True, "message": "Simulationsverzeichnis existiert nicht, keine Bereinigung erforderlich"}
        
        cleaned_files = []
        errors = []
        
        # Liste zu löschender Dateien (inkl. Datenbankdateien)
        files_to_delete = [
            "run_state.json",
            "simulation.log",
            "stdout.log",
            "stderr.log",
            "twitter_simulation.db",  # Twitter-Plattform-Datenbank
            "reddit_simulation.db",   # Reddit-Plattform-Datenbank
            "env_status.json",        # Umgebungsstatusdatei
        ]
        
        # Liste zu bereinigender Verzeichnisse (enthält Aktionsprotokolle)
        dirs_to_clean = ["twitter", "reddit"]
        
        # Dateien löschen
        for filename in files_to_delete:
            file_path = os.path.join(sim_dir, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    cleaned_files.append(filename)
                except Exception as e:
                    errors.append(f"Löschen von {filename} fehlgeschlagen: {str(e)}")
        
        # Aktionsprotokolle in Plattformverzeichnissen bereinigen
        for dir_name in dirs_to_clean:
            dir_path = os.path.join(sim_dir, dir_name)
            if os.path.exists(dir_path):
                actions_file = os.path.join(dir_path, "actions.jsonl")
                if os.path.exists(actions_file):
                    try:
                        os.remove(actions_file)
                        cleaned_files.append(f"{dir_name}/actions.jsonl")
                    except Exception as e:
                        errors.append(f"Löschen von {dir_name}/actions.jsonl fehlgeschlagen: {str(e)}")
        
        # Laufstatus im Speicher bereinigen
        if simulation_id in cls._run_states:
            del cls._run_states[simulation_id]
        
        logger.info(f"Simulationsprotokollbereinigung abgeschlossen: {simulation_id}, gelöschte Dateien: {cleaned_files}")
        
        return {
            "success": len(errors) == 0,
            "cleaned_files": cleaned_files,
            "errors": errors if errors else None
        }
    
    # Markierung zur Vermeidung doppelter Bereinigung
    _cleanup_done = False
    
    @classmethod
    def cleanup_all_simulations(cls):
        """
        Alle laufenden Simulationsprozesse bereinigen
        
        Wird beim Server-Shutdown aufgerufen, um sicherzustellen, dass alle Unterprozesse beendet werden
        """
        # Doppelte Bereinigung verhindern
        if cls._cleanup_done:
            return
        cls._cleanup_done = True
        
        # Prüfen, ob Bereinigung erforderlich ist (um unnötige Protokolle zu vermeiden)
        has_processes = bool(cls._processes)
        has_updaters = bool(cls._graph_memory_enabled)
        
        if not has_processes and not has_updaters:
            return  # Nichts zu bereinigen, stille Rückkehr
        
        logger.info("Bereinige alle Simulationsprozesse...")
        
        # Zuerst alle Graphenspeicher-Updater stoppen (stop_all protokolliert intern)
        try:
            ZepGraphMemoryManager.stop_all()
        except Exception as e:
            logger.error(f"Stoppen der Graphenspeicher-Updater fehlgeschlagen: {e}")
        cls._graph_memory_enabled.clear()
        
        # Dictionary kopieren, um Modifikation während Iteration zu vermeiden
        processes = list(cls._processes.items())
        
        for simulation_id, process in processes:
            try:
                if process.poll() is None:  # Prozess läuft noch
                    logger.info(f"Beende Simulationsprozess: {simulation_id}, pid={process.pid}")
                    
                    try:
                        # Plattformübergreifende Prozessbeendigung verwenden
                        cls._terminate_process(process, simulation_id, timeout=5)
                    except (ProcessLookupError, OSError):
                        # Prozess existiert möglicherweise nicht mehr, direktes Beenden versuchen
                        try:
                            process.terminate()
                            process.wait(timeout=3)
                        except Exception:
                            process.kill()
                    
                    # run_state.json aktualisieren
                    state = cls.get_run_state(simulation_id)
                    if state:
                        state.runner_status = RunnerStatus.STOPPED
                        state.twitter_running = False
                        state.reddit_running = False
                        state.completed_at = datetime.now().isoformat()
                        state.error = "Server heruntergefahren, Simulation beendet"
                        cls._save_run_state(state)
                    
                    # Gleichzeitig state.json aktualisieren, Status auf stopped setzen
                    try:
                        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
                        state_file = os.path.join(sim_dir, "state.json")
                        logger.info(f"Versuche state.json zu aktualisieren: {state_file}")
                        if os.path.exists(state_file):
                            with open(state_file, 'r', encoding='utf-8') as f:
                                state_data = json.load(f)
                            state_data['status'] = 'stopped'
                            state_data['updated_at'] = datetime.now().isoformat()
                            with open(state_file, 'w', encoding='utf-8') as f:
                                json.dump(state_data, f, indent=2, ensure_ascii=False)
                            logger.info(f"state.json-Status auf stopped aktualisiert: {simulation_id}")
                        else:
                            logger.warning(f"state.json existiert nicht: {state_file}")
                    except Exception as state_err:
                        logger.warning(f"Aktualisieren von state.json fehlgeschlagen: {simulation_id}, error={state_err}")
                        
            except Exception as e:
                logger.error(f"Prozessbereinigung fehlgeschlagen: {simulation_id}, error={e}")
        
        # Datei-Handles bereinigen
        for simulation_id, file_handle in list(cls._stdout_files.items()):
            try:
                if file_handle:
                    file_handle.close()
            except Exception:
                pass
        cls._stdout_files.clear()
        
        for simulation_id, file_handle in list(cls._stderr_files.items()):
            try:
                if file_handle:
                    file_handle.close()
            except Exception:
                pass
        cls._stderr_files.clear()
        
        # Speicherstatus bereinigen
        cls._processes.clear()
        cls._action_queues.clear()
        
        logger.info("Simulationsprozessbereinigung abgeschlossen")
    
    @classmethod
    def register_cleanup(cls):
        """
        Bereinigungsfunktion registrieren
        
        Wird beim Start der Flask-Anwendung aufgerufen, um sicherzustellen, dass alle Simulationsprozesse beim Server-Shutdown beendet werden
        """
        global _cleanup_registered
        
        if _cleanup_registered:
            return
        
        # Im Flask-Debug-Modus nur im reloader-Unterprozess bereinigen (der Prozess, der die Anwendung tatsächlich ausführt)
        # WERKZEUG_RUN_MAIN=true zeigt den reloader-Unterprozess an
        # Wenn kein Debug-Modus, ist diese Umgebungsvariable nicht vorhanden, Bereinigung trotzdem erforderlich
        is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
        is_debug_mode = os.environ.get('FLASK_DEBUG') == '1' or os.environ.get('WERKZEUG_RUN_MAIN') is not None
        
        # Im Debug-Modus nur im reloader-Unterprozess registrieren; im Nicht-Debug-Modus immer registrieren
        if is_debug_mode and not is_reloader_process:
            _cleanup_registered = True  # Als registriert markieren, um wiederholte Versuche im Unterprozess zu verhindern
            return
        
        # Originale Signal-Handler speichern
        original_sigint = signal.getsignal(signal.SIGINT)
        original_sigterm = signal.getsignal(signal.SIGTERM)
        # SIGHUP existiert nur auf Unix-Systemen (macOS/Linux), nicht auf Windows
        original_sighup = None
        has_sighup = hasattr(signal, 'SIGHUP')
        if has_sighup:
            original_sighup = signal.getsignal(signal.SIGHUP)
        
        def cleanup_handler(signum=None, frame=None):
            """Signal-Handler: Zuerst Simulationsprozesse bereinigen, dann originale Handler aufrufen"""
            # Nur protokollieren, wenn Prozesse bereinigt werden müssen
            if cls._processes or cls._graph_memory_enabled:
                logger.info(f"Signal {signum} empfangen, beginne Bereinigung...")
            cls.cleanup_all_simulations()
            
            # Originale Signal-Handler aufrufen, damit Flask normal beendet
            if signum == signal.SIGINT and callable(original_sigint):
                original_sigint(signum, frame)
            elif signum == signal.SIGTERM and callable(original_sigterm):
                original_sigterm(signum, frame)
            elif has_sighup and signum == signal.SIGHUP:
                # SIGHUP: Gesendet beim Terminal-Schließen
                if callable(original_sighup):
                    original_sighup(signum, frame)
                else:
                    # Standardverhalten: Normal beenden
                    sys.exit(0)
            else:
                # Wenn originale Handler nicht aufrufbar (wie SIG_DFL), Standardverhalten
                raise KeyboardInterrupt
        
        # atexit-Handler als Backup registrieren
        atexit.register(cls.cleanup_all_simulations)
        
        # Signal-Handler registrieren (nur im Hauptthread)
        try:
            # SIGTERM: Standard-Signal für kill-Befehl
            signal.signal(signal.SIGTERM, cleanup_handler)
            # SIGINT: Ctrl+C
            signal.signal(signal.SIGINT, cleanup_handler)
            # SIGHUP: Terminal geschlossen (nur Unix-Systeme)
            if has_sighup:
                signal.signal(signal.SIGHUP, cleanup_handler)
        except ValueError:
            # Nicht im Hauptthread, nur atexit verwenden
            logger.warning("Signal-Handler können nicht registriert werden (nicht im Hauptthread), verwende nur atexit")
        
        _cleanup_registered = True
    
    @classmethod
    def get_running_simulations(cls) -> List[str]:
        """
        Liste aller laufenden Simulations-IDs abrufen
        """
        running = []
        for sim_id, process in cls._processes.items():
            if process.poll() is None:
                running.append(sim_id)
        return running
    
    # ============== Interview-Funktion ==============
    
    @classmethod
    def check_env_alive(cls, simulation_id: str) -> bool:
        """
        Prüfen, ob die Simulationsumgebung aktiv ist (Interview-Befehle empfangen kann)

        Args:
            simulation_id: Simulations-ID

        Returns:
            True, wenn Umgebung aktiv, False, wenn Umgebung geschlossen
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        if not os.path.exists(sim_dir):
            return False

        ipc_client = SimulationIPCClient(sim_dir)
        return ipc_client.check_env_alive()

    @classmethod
    def get_env_status_detail(cls, simulation_id: str) -> Dict[str, Any]:
        """
        Detaillierte Simulationsumgebungs-Statusinformationen abrufen

        Args:
            simulation_id: Simulations-ID

        Returns:
            Status-Detail-Dictionary mit status, twitter_available, reddit_available, timestamp
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        status_file = os.path.join(sim_dir, "env_status.json")
        
        default_status = {
            "status": "stopped",
            "twitter_available": False,
            "reddit_available": False,
            "timestamp": None
        }
        
        if not os.path.exists(status_file):
            return default_status
        
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                status = json.load(f)
            return {
                "status": status.get("status", "stopped"),
                "twitter_available": status.get("twitter_available", False),
                "reddit_available": status.get("reddit_available", False),
                "timestamp": status.get("timestamp")
            }
        except (json.JSONDecodeError, OSError):
            return default_status

    @classmethod
    def interview_agent(
        cls,
        simulation_id: str,
        agent_id: int,
        prompt: str,
        platform: str = None,
        timeout: float = 60.0
    ) -> Dict[str, Any]:
        """
        Einzelnen Agent interviewen

        Args:
            simulation_id: Simulations-ID
            agent_id: Agent-ID
            prompt: Interviewfrage
            platform: Plattform angeben (optional)
                - "twitter": Nur Twitter-Plattform interviewen
                - "reddit": Nur Reddit-Plattform interviewen
                - None: Bei Dual-Plattform-Simulation beide Plattformen interviewen, Ergebnisse zusammenführen
            timeout: Zeitlimit (Sekunden)

        Returns:
            Interview-Ergebnis-Dictionary

        Raises:
            ValueError: Simulation existiert nicht oder Umgebung läuft nicht
            TimeoutError: Zeitlimit beim Warten auf Antwort überschritten
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        if not os.path.exists(sim_dir):
            raise ValueError(f"Simulation existiert nicht: {simulation_id}")

        ipc_client = SimulationIPCClient(sim_dir)

        if not ipc_client.check_env_alive():
            raise ValueError(f"Simulationsumgebung läuft nicht oder ist geschlossen, Interview kann nicht ausgeführt werden: {simulation_id}")

        logger.info(f"Interview-Befehl senden: simulation_id={simulation_id}, agent_id={agent_id}, platform={platform}")

        response = ipc_client.send_interview(
            agent_id=agent_id,
            prompt=prompt,
            platform=platform,
            timeout=timeout
        )

        if response.status.value == "completed":
            return {
                "success": True,
                "agent_id": agent_id,
                "prompt": prompt,
                "result": response.result,
                "timestamp": response.timestamp
            }
        else:
            return {
                "success": False,
                "agent_id": agent_id,
                "prompt": prompt,
                "error": response.error,
                "timestamp": response.timestamp
            }
    
    @classmethod
    def interview_agents_batch(
        cls,
        simulation_id: str,
        interviews: List[Dict[str, Any]],
        platform: str = None,
        timeout: float = 120.0
    ) -> Dict[str, Any]:
        """
        Mehrere Agents im Batch interviewen

        Args:
            simulation_id: Simulations-ID
            interviews: Interview-Liste, jedes Element enthält {"agent_id": int, "prompt": str, "platform": str(optional)}
            platform: Standardplattform (optional, wird durch platform jedes Interviewelements überschrieben)
                - "twitter": Standardmäßig nur Twitter-Plattform interviewen
                - "reddit": Standardmäßig nur Reddit-Plattform interviewen
                - None: Bei Dual-Plattform-Simulation beide Plattformen pro Agent interviewen
            timeout: Zeitlimit (Sekunden)

        Returns:
            Batch-Interview-Ergebnis-Dictionary

        Raises:
            ValueError: Simulation existiert nicht oder Umgebung läuft nicht
            TimeoutError: Zeitlimit beim Warten auf Antwort überschritten
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        if not os.path.exists(sim_dir):
            raise ValueError(f"Simulation existiert nicht: {simulation_id}")

        ipc_client = SimulationIPCClient(sim_dir)

        if not ipc_client.check_env_alive():
            raise ValueError(f"Simulationsumgebung läuft nicht oder ist geschlossen, Interview kann nicht ausgeführt werden: {simulation_id}")

        logger.info(f"Batch-Interview-Befehl senden: simulation_id={simulation_id}, count={len(interviews)}, platform={platform}")

        response = ipc_client.send_batch_interview(
            interviews=interviews,
            platform=platform,
            timeout=timeout
        )

        if response.status.value == "completed":
            return {
                "success": True,
                "interviews_count": len(interviews),
                "result": response.result,
                "timestamp": response.timestamp
            }
        else:
            return {
                "success": False,
                "interviews_count": len(interviews),
                "error": response.error,
                "timestamp": response.timestamp
            }
    
    @classmethod
    def interview_all_agents(
        cls,
        simulation_id: str,
        prompt: str,
        platform: str = None,
        timeout: float = 180.0
    ) -> Dict[str, Any]:
        """
        Alle Agents interviewen (globales Interview)

        Verwendet dieselbe Frage für alle Agents in der Simulation

        Args:
            simulation_id: Simulations-ID
            prompt: Interviewfrage (alle Agents verwenden dieselbe Frage)
            platform: Plattform angeben (optional)
                - "twitter": Nur Twitter-Plattform interviewen
                - "reddit": Nur Reddit-Plattform interviewen
                - None: Bei Dual-Plattform-Simulation beide Plattformen pro Agent interviewen
            timeout: Zeitlimit (Sekunden)

        Returns:
            Globales Interview-Ergebnis-Dictionary
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        if not os.path.exists(sim_dir):
            raise ValueError(f"Simulation existiert nicht: {simulation_id}")

        # Alle Agent-Informationen aus Konfigurationsdatei abrufen
        config_path = os.path.join(sim_dir, "simulation_config.json")
        if not os.path.exists(config_path):
            raise ValueError(f"Simulationskonfiguration existiert nicht: {simulation_id}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        agent_configs = config.get("agent_configs", [])
        if not agent_configs:
            raise ValueError(f"Keine Agents in Simulationskonfiguration: {simulation_id}")

        # Batch-Interview-Liste aufbauen
        interviews = []
        for agent_config in agent_configs:
            agent_id = agent_config.get("agent_id")
            if agent_id is not None:
                interviews.append({
                    "agent_id": agent_id,
                    "prompt": prompt
                })

        logger.info(f"Globales Interview-Befehl senden: simulation_id={simulation_id}, agent_count={len(interviews)}, platform={platform}")

        return cls.interview_agents_batch(
            simulation_id=simulation_id,
            interviews=interviews,
            platform=platform,
            timeout=timeout
        )
    
    @classmethod
    def close_simulation_env(
        cls,
        simulation_id: str,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """
        Simulationsumgebung schließen (nicht den Simulationsprozess stoppen)
        
        Sendet Befehl zum Schließen der Umgebung an die Simulation, damit diese den Befehlswartemodus beendet
        
        Args:
            simulation_id: Simulations-ID
            timeout: Zeitlimit (Sekunden)
            
        Returns:
            Betriebsergebnis-Dictionary
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        if not os.path.exists(sim_dir):
            raise ValueError(f"Simulation existiert nicht: {simulation_id}")
        
        ipc_client = SimulationIPCClient(sim_dir)
        
        if not ipc_client.check_env_alive():
            return {
                "success": True,
                "message": "Umgebung bereits geschlossen"
            }
        
        logger.info(f"Befehl zum Schließen der Umgebung senden: simulation_id={simulation_id}")
        
        try:
            response = ipc_client.send_close_env(timeout=timeout)
            
            return {
                "success": response.status.value == "completed",
                "message": "Befehl zum Schließen der Umgebung gesendet",
                "result": response.result,
                "timestamp": response.timestamp
            }
        except TimeoutError:
            # Zeitlimit kann auftreten, wenn Umgebung gerade schließt
            return {
                "success": True,
                "message": "Befehl zum Schließen der Umgebung gesendet (Zeitlimit beim Warten auf Antwort, Umgebung schließt möglicherweise gerade)"
            }
    
    @classmethod
    def _get_interview_history_from_db(
        cls,
        db_path: str,
        platform_name: str,
        agent_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Interview-Historie aus einzelner Datenbank abrufen"""
        import sqlite3
        
        if not os.path.exists(db_path):
            return []
        
        results = []
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            if agent_id is not None:
                cursor.execute("""
                    SELECT user_id, info, created_at
                    FROM trace
                    WHERE action = 'interview' AND user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (agent_id, limit))
            else:
                cursor.execute("""
                    SELECT user_id, info, created_at
                    FROM trace
                    WHERE action = 'interview'
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))
            
            for user_id, info_json, created_at in cursor.fetchall():
                try:
                    info = json.loads(info_json) if info_json else {}
                except json.JSONDecodeError:
                    info = {"raw": info_json}
                
                results.append({
                    "agent_id": user_id,
                    "response": info.get("response", info),
                    "prompt": info.get("prompt", ""),
                    "timestamp": created_at,
                    "platform": platform_name
                })
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Lesen der Interview-Historie fehlgeschlagen ({platform_name}): {e}")
        
        return results

    @classmethod
    def get_interview_history(
        cls,
        simulation_id: str,
        platform: str = None,
        agent_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Interview-Historie abrufen (aus Datenbank lesen)
        
        Args:
            simulation_id: Simulations-ID
            platform: Plattformtyp (reddit/twitter/None)
                - "reddit": Nur Reddit-Historie abrufen
                - "twitter": Nur Twitter-Historie abrufen
                - None: Historie beider Plattformen abrufen
            agent_id: Agent-ID angeben (optional, nur Historie dieses Agents)
            limit: Rückgabelimit pro Plattform
            
        Returns:
            Interview-Historie-Liste
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        
        results = []
        
        # Zu abfragende Plattformen bestimmen
        if platform in ("reddit", "twitter"):
            platforms = [platform]
        else:
            # Wenn keine Plattform angegeben, beide abfragen
            platforms = ["twitter", "reddit"]
        
        for p in platforms:
            db_path = os.path.join(sim_dir, f"{p}_simulation.db")
            platform_results = cls._get_interview_history_from_db(
                db_path=db_path,
                platform_name=p,
                agent_id=agent_id,
                limit=limit
            )
            results.extend(platform_results)
        
        # Nach Zeit absteigend sortieren
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Wenn mehrere Plattformen abgefragt, Gesamtzahl begrenzen
        if len(platforms) > 1 and len(results) > limit:
            results = results[:limit]
        
        return results
