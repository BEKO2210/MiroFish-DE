"""
Simulations-IPC-Kommunikationsmodul
Für die Interprozesskommunikation zwischen Flask-Backend und Simulationsskript

Einfaches Befehls-/Antwortmuster über das Dateisystem:
1. Flask schreibt Befehle in das commands/-Verzeichnis
2. Simulationsskript fragt das Befehlsverzeichnis ab, führt Befehle aus und schreibt Antworten in das responses/-Verzeichnis
3. Flask fragt das Antwortverzeichnis ab, um Ergebnisse zu erhalten
"""

import os
import json
import time
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..utils.logger import get_logger

logger = get_logger('mirofish.simulation_ipc')


class CommandType(str, Enum):
    """Befehlstyp"""
    INTERVIEW = "interview"           # Einzelnes Agent-Interview
    BATCH_INTERVIEW = "batch_interview"  # Batch-Interview
    CLOSE_ENV = "close_env"           # Umgebung schließen


class CommandStatus(str, Enum):
    """Befehlsstatus"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class IPCCommand:
    """IPC-Befehl"""
    command_id: str
    command_type: CommandType
    args: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "command_id": self.command_id,
            "command_type": self.command_type.value,
            "args": self.args,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IPCCommand':
        return cls(
            command_id=data["command_id"],
            command_type=CommandType(data["command_type"]),
            args=data.get("args", {}),
            timestamp=data.get("timestamp", datetime.now().isoformat())
        )


@dataclass
class IPCResponse:
    """IPC-Antwort"""
    command_id: str
    status: CommandStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "command_id": self.command_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IPCResponse':
        return cls(
            command_id=data["command_id"],
            status=CommandStatus(data["status"]),
            result=data.get("result"),
            error=data.get("error"),
            timestamp=data.get("timestamp", datetime.now().isoformat())
        )


class SimulationIPCClient:
    """
    Simulations-IPC-Client (Flask-seitig)
    
    Zum Senden von Befehlen an den Simulationsprozess und Warten auf Antworten
    """
    
    def __init__(self, simulation_dir: str):
        """
        IPC-Client initialisieren
        
        Args:
            simulation_dir: Simulationsdatenverzeichnis
        """
        self.simulation_dir = simulation_dir
        self.commands_dir = os.path.join(simulation_dir, "ipc_commands")
        self.responses_dir = os.path.join(simulation_dir, "ipc_responses")
        
        # Sicherstellen, dass Verzeichnisse existieren
        os.makedirs(self.commands_dir, exist_ok=True)
        os.makedirs(self.responses_dir, exist_ok=True)
    
    def send_command(
        self,
        command_type: CommandType,
        args: Dict[str, Any],
        timeout: float = 60.0,
        poll_interval: float = 0.5
    ) -> IPCResponse:
        """
        Befehl senden und auf Antwort warten
        
        Args:
            command_type: Befehlstyp
            args: Befehlsparameter
            timeout: Timeout (Sekunden)
            poll_interval: Abfrageintervall (Sekunden)
            
        Returns:
            IPCResponse
            
        Raises:
            TimeoutError: Timeout beim Warten auf Antwort
        """
        command_id = str(uuid.uuid4())
        command = IPCCommand(
            command_id=command_id,
            command_type=command_type,
            args=args
        )
        
        # Befehlsdatei schreiben
        command_file = os.path.join(self.commands_dir, f"{command_id}.json")
        with open(command_file, 'w', encoding='utf-8') as f:
            json.dump(command.to_dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"IPC-Befehl gesendet: {command_type.value}, command_id={command_id}")
        
        # Auf Antwort warten
        response_file = os.path.join(self.responses_dir, f"{command_id}.json")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if os.path.exists(response_file):
                try:
                    with open(response_file, 'r', encoding='utf-8') as f:
                        response_data = json.load(f)
                    response = IPCResponse.from_dict(response_data)
                    
                    # Befehls- und Antwortdateien bereinigen
                    try:
                        os.remove(command_file)
                        os.remove(response_file)
                    except OSError:
                        pass
                    
                    logger.info(f"IPC-Antwort empfangen: command_id={command_id}, status={response.status.value}")
                    return response
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Antwort konnte nicht geparst werden: {e}")
            
            time.sleep(poll_interval)
        
        # Timeout
        logger.error(f"Timeout beim Warten auf IPC-Antwort: command_id={command_id}")
        
        # Befehlsdatei bereinigen
        try:
            os.remove(command_file)
        except OSError:
            pass
        
        raise TimeoutError(f"Timeout beim Warten auf Befehlsantwort ({timeout}s)")
    
    def send_interview(
        self,
        agent_id: int,
        prompt: str,
        platform: str = None,
        timeout: float = 60.0
    ) -> IPCResponse:
        """
        Einzelnen Agent-Interview-Befehl senden
        
        Args:
            agent_id: Agent ID
            prompt: Interviewfrage
            platform: Plattform angeben (optional)
                - "twitter": Nur Twitter-Plattform interviewen
                - "reddit": Nur Reddit-Plattform interviewen  
                - None: Bei Dual-Plattform-Simulation beide Plattformen interviewen, bei Single-Plattform die jeweilige Plattform
            timeout: Timeout
            
        Returns:
            IPCResponse, result-Feld enthält Interviewergebnisse
        """
        args = {
            "agent_id": agent_id,
            "prompt": prompt
        }
        if platform:
            args["platform"] = platform
            
        return self.send_command(
            command_type=CommandType.INTERVIEW,
            args=args,
            timeout=timeout
        )
    
    def send_batch_interview(
        self,
        interviews: List[Dict[str, Any]],
        platform: str = None,
        timeout: float = 120.0
    ) -> IPCResponse:
        """
        Batch-Interview-Befehl senden
        
        Args:
            interviews: Interviewliste, jedes Element enthält {"agent_id": int, "prompt": str, "platform": str(optional)}
            platform: Standardplattform (optional, wird durch platform jedes Interviewelements überschrieben)
                - "twitter": Standardmäßig nur Twitter-Plattform interviewen
                - "reddit": Standardmäßig nur Reddit-Plattform interviewen
                - None: Bei Dual-Plattform-Simulation beide Plattformen pro Agent interviewen
            timeout: Timeout
            
        Returns:
            IPCResponse, result-Feld enthält alle Interviewergebnisse
        """
        args = {"interviews": interviews}
        if platform:
            args["platform"] = platform
            
        return self.send_command(
            command_type=CommandType.BATCH_INTERVIEW,
            args=args,
            timeout=timeout
        )
    
    def send_close_env(self, timeout: float = 30.0) -> IPCResponse:
        """
        Befehl zum Schließen der Umgebung senden
        
        Args:
            timeout: Timeout
            
        Returns:
            IPCResponse
        """
        return self.send_command(
            command_type=CommandType.CLOSE_ENV,
            args={},
            timeout=timeout
        )
    
    def check_env_alive(self) -> bool:
        """
        Prüfen, ob die Simulationsumgebung aktiv ist
        
        Durch Prüfung der env_status.json-Datei ermittelt
        """
        status_file = os.path.join(self.simulation_dir, "env_status.json")
        if not os.path.exists(status_file):
            return False
        
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                status = json.load(f)
            return status.get("status") == "alive"
        except (json.JSONDecodeError, OSError):
            return False


class SimulationIPCServer:
    """
    Simulations-IPC-Server (Simulationsskript-seitig)
    
    Fragt das Befehlsverzeichnis ab, führt Befehle aus und gibt Antworten zurück
    """
    
    def __init__(self, simulation_dir: str):
        """
        IPC-Server initialisieren
        
        Args:
            simulation_dir: Simulationsdatenverzeichnis
        """
        self.simulation_dir = simulation_dir
        self.commands_dir = os.path.join(simulation_dir, "ipc_commands")
        self.responses_dir = os.path.join(simulation_dir, "ipc_responses")
        
        # Sicherstellen, dass Verzeichnisse existieren
        os.makedirs(self.commands_dir, exist_ok=True)
        os.makedirs(self.responses_dir, exist_ok=True)
        
        # Umgebungsstatus
        self._running = False
    
    def start(self):
        """Server als aktiv markieren"""
        self._running = True
        self._update_env_status("alive")
    
    def stop(self):
        """Server als gestoppt markieren"""
        self._running = False
        self._update_env_status("stopped")
    
    def _update_env_status(self, status: str):
        """Umgebungsstatusdatei aktualisieren"""
        status_file = os.path.join(self.simulation_dir, "env_status.json")
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump({
                "status": status,
                "timestamp": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
    
    def poll_commands(self) -> Optional[IPCCommand]:
        """
        Befehlsverzeichnis abfragen, ersten ausstehenden Befehl zurückgeben
        
        Returns:
            IPCCommand 或 None
        """
        if not os.path.exists(self.commands_dir):
            return None
        
        # Befehlsdateien nach Zeit sortiert abrufen
        command_files = []
        for filename in os.listdir(self.commands_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.commands_dir, filename)
                command_files.append((filepath, os.path.getmtime(filepath)))
        
        command_files.sort(key=lambda x: x[1])
        
        for filepath, _ in command_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return IPCCommand.from_dict(data)
            except (json.JSONDecodeError, KeyError, OSError) as e:
                logger.warning(f"Befehlsdatei konnte nicht gelesen werden: {filepath}, {e}")
                continue
        
        return None
    
    def send_response(self, response: IPCResponse):
        """
        Antwort senden
        
        Args:
            response: IPC-Antwort
        """
        response_file = os.path.join(self.responses_dir, f"{response.command_id}.json")
        with open(response_file, 'w', encoding='utf-8') as f:
            json.dump(response.to_dict(), f, ensure_ascii=False, indent=2)
        
        # Befehlsdatei löschen
        command_file = os.path.join(self.commands_dir, f"{response.command_id}.json")
        try:
            os.remove(command_file)
        except OSError:
            pass
    
    def send_success(self, command_id: str, result: Dict[str, Any]):
        """Erfolgsantwort senden"""
        self.send_response(IPCResponse(
            command_id=command_id,
            status=CommandStatus.COMPLETED,
            result=result
        ))
    
    def send_error(self, command_id: str, error: str):
        """Fehlerantwort senden"""
        self.send_response(IPCResponse(
            command_id=command_id,
            status=CommandStatus.FAILED,
            error=error
        ))
