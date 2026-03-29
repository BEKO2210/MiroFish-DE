"""
Report Agent Service
Uses LangChain + Zep to implement ReACT mode for simulation report generation

Features:
1. Generate reports based on simulation requirements and Zep graph information
2. First plan the table of contents structure, then generate content section by section
3. Each section uses ReACT multi-round thinking and reflection mode
4. Support dialogue with users, autonomously calling retrieval tools during conversation
"""

import os
import json
import time
import re
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..config import Config
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger
from .zep_tools import (
    ZepToolsService, 
    SearchResult, 
    InsightForgeResult, 
    PanoramaResult,
    InterviewResult
)

logger = get_logger('mirofish.report_agent')


class ReportLogger:
    """
    Report Agent Detailed Log Recorder
    
    Generates agent_log.jsonl file in the report folder, recording every detailed action.
    Each line is a complete JSON object containing timestamp, action type, detailed content, etc.
    """
    
    def __init__(self, report_id: str):
        """
        Initialize the log recorder
        
        Args:
            report_id: Report ID used to determine the log file path
        """
        self.report_id = report_id
        self.log_file_path = os.path.join(
            Config.UPLOAD_FOLDER, 'reports', report_id, 'agent_log.jsonl'
        )
        self.start_time = datetime.now()
        self._ensure_log_file()
    
    def _ensure_log_file(self):
        """Ensure the log file directory exists"""
        log_dir = os.path.dirname(self.log_file_path)
        os.makedirs(log_dir, exist_ok=True)
    
    def _get_elapsed_time(self) -> float:
        """Get elapsed time since start (seconds)"""
        return (datetime.now() - self.start_time).total_seconds()
    
    def log(
        self, 
        action: str, 
        stage: str,
        details: Dict[str, Any],
        section_title: str = None,
        section_index: int = None
    ):
        """
        Record a log entry
        
        Args:
            action: Action type, e.g., 'start', 'tool_call', 'llm_response', 'section_complete'
            stage: Current stage, e.g., 'planning', 'generating', 'completed'
            details: Detailed content dictionary, not truncated
            section_title: Current section title (optional)
            section_index: Current section index (optional)
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": round(self._get_elapsed_time(), 2),
            "report_id": self.report_id,
            "action": action,
            "stage": stage,
            "section_title": section_title,
            "section_index": section_index,
            "details": details
        }
        
        # Append to JSONL file
        with open(self.log_file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    def log_start(self, simulation_id: str, graph_id: str, simulation_requirement: str):
        """Record report generation start"""
        self.log(
            action="report_start",
            stage="pending",
            details={
                "simulation_id": simulation_id,
                "graph_id": graph_id,
                "simulation_requirement": simulation_requirement,
                "message": "Berichtgenerierungsaufgabe gestartet"
            }
        )
    
    def log_planning_start(self):
        """Record outline planning start"""
        self.log(
            action="planning_start",
            stage="planning",
            details={"message": "Beginne mit der Gliederungsplanung"}
        )
    
    def log_planning_context(self, context: Dict[str, Any]):
        """Record context information obtained during planning"""
        self.log(
            action="planning_context",
            stage="planning",
            details={
                "message": "Simulationskontextinformationen abrufen",
                "context": context
            }
        )
    
    def log_planning_complete(self, outline_dict: Dict[str, Any]):
        """Record outline planning completion"""
        self.log(
            action="planning_complete",
            stage="planning",
            details={
                "message": "Gliederungsplanung abgeschlossen",
                "outline": outline_dict
            }
        )
    
    def log_section_start(self, section_title: str, section_index: int):
        """Record section generation start"""
        self.log(
            action="section_start",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={"message": f"Beginne mit der Generierung des Kapitels: {section_title}"}
        )
    
    def log_react_thought(self, section_title: str, section_index: int, iteration: int, thought: str):
        """Record ReACT thinking process"""
        self.log(
            action="react_thought",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "iteration": iteration,
                "thought": thought,
                "message": f"ReACT Runde {iteration} Überlegung"
            }
        )
    
    def log_tool_call(
        self, 
        section_title: str, 
        section_index: int,
        tool_name: str, 
        parameters: Dict[str, Any],
        iteration: int
    ):
        """Record tool call"""
        self.log(
            action="tool_call",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "iteration": iteration,
                "tool_name": tool_name,
                "parameters": parameters,
                "message": f"Tool aufrufen: {tool_name}"
            }
        )
    
    def log_tool_result(
        self,
        section_title: str,
        section_index: int,
        tool_name: str,
        result: str,
        iteration: int
    ):
        """Record tool call result (full content, not truncated)"""
        self.log(
            action="tool_result",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "iteration": iteration,
                "tool_name": tool_name,
                "result": result,  # Complete result, not truncated
                "result_length": len(result),
                "message": f"Tool {tool_name} hat Ergebnis zurückgegeben"
            }
        )
    
    def log_llm_response(
        self,
        section_title: str,
        section_index: int,
        response: str,
        iteration: int,
        has_tool_calls: bool,
        has_final_answer: bool
    ):
        """Record LLM response (full content, not truncated)"""
        self.log(
            action="llm_response",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "iteration": iteration,
                "response": response,  # Complete response, not truncated
                "response_length": len(response),
                "has_tool_calls": has_tool_calls,
                "has_final_answer": has_final_answer,
                "message": f"LLM-Antwort (Tool-Aufruf: {has_tool_calls}, Finale Antwort: {has_final_answer})"
            }
        )
    
    def log_section_content(
        self,
        section_title: str,
        section_index: int,
        content: str,
        tool_calls_count: int
    ):
        """Record section content generation completion (only records content, does not indicate entire section completion)"""
        self.log(
            action="section_content",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "content": content,  # Complete content, not truncated
                "content_length": len(content),
                "tool_calls_count": tool_calls_count,
                "message": f"Kapitel {section_title} Inhaltsgenerierung abgeschlossen"
            }
        )
    
    def log_section_full_complete(
        self,
        section_title: str,
        section_index: int,
        full_content: str
    ):
        """
        Record section generation completion

        Frontend should listen to this log to determine if a section is truly complete and get the full content
        """
        self.log(
            action="section_complete",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "content": full_content,
                "content_length": len(full_content),
                "message": f"Kapitel {section_title} Generierung abgeschlossen"
            }
        )
    
    def log_report_complete(self, total_sections: int, total_time_seconds: float):
        """Record report generation completion"""
        self.log(
            action="report_complete",
            stage="completed",
            details={
                "total_sections": total_sections,
                "total_time_seconds": round(total_time_seconds, 2),
                "message": "Berichtgenerierung abgeschlossen"
            }
        )
    
    def log_error(self, error_message: str, stage: str, section_title: str = None):
        """Record error"""
        self.log(
            action="error",
            stage=stage,
            section_title=section_title,
            section_index=None,
            details={
                "error": error_message,
                "message": f"Fehler aufgetreten: {error_message}"
            }
        )


class ReportConsoleLogger:
    """
    Report Agent Console Log Recorder
    
    Writes console-style logs (INFO, WARNING, etc.) to console_log.txt in the report folder.
    These logs differ from agent_log.jsonl as they are plain text console output.
    """
    
    def __init__(self, report_id: str):
        """
        Initialize the console log recorder
        
        Args:
            report_id: Report ID used to determine the log file path
        """
        self.report_id = report_id
        self.log_file_path = os.path.join(
            Config.UPLOAD_FOLDER, 'reports', report_id, 'console_log.txt'
        )
        self._ensure_log_file()
        self._file_handler = None
        self._setup_file_handler()
    
    def _ensure_log_file(self):
        """Ensure the log file directory exists"""
        log_dir = os.path.dirname(self.log_file_path)
        os.makedirs(log_dir, exist_ok=True)
    
    def _setup_file_handler(self):
        """Setup file handler to write logs to file"""
        import logging
        
        # Create file handler
        self._file_handler = logging.FileHandler(
            self.log_file_path,
            mode='a',
            encoding='utf-8'
        )
        self._file_handler.setLevel(logging.INFO)
        
        # Use same concise format as console
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        self._file_handler.setFormatter(formatter)
        
        # Add to report_agent related loggers
        loggers_to_attach = [
            'mirofish.report_agent',
            'mirofish.zep_tools',
        ]
        
        for logger_name in loggers_to_attach:
            target_logger = logging.getLogger(logger_name)
            # Avoid duplicate additions
            if self._file_handler not in target_logger.handlers:
                target_logger.addHandler(self._file_handler)
    
    def close(self):
        """Close file handler and remove from logger"""
        import logging
        
        if self._file_handler:
            loggers_to_detach = [
                'mirofish.report_agent',
                'mirofish.zep_tools',
            ]
            
            for logger_name in loggers_to_detach:
                target_logger = logging.getLogger(logger_name)
                if self._file_handler in target_logger.handlers:
                    target_logger.removeHandler(self._file_handler)
            
            self._file_handler.close()
            self._file_handler = None
    
    def __del__(self):
        """Ensure file handler is closed on destruction"""
        self.close()


class ReportStatus(str, Enum):
    """Report Status"""
    PENDING = "pending"
    PLANNING = "planning"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ReportSection:
    """Report Section"""
    title: str
    content: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content
        }

    def to_markdown(self, level: int = 2) -> str:
        """Convert to Markdown format"""
        md = f"{'#' * level} {self.title}\n\n"
        if self.content:
            md += f"{self.content}\n\n"
        return md


@dataclass
class ReportOutline:
    """Report Outline"""
    title: str
    summary: str
    sections: List[ReportSection]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "summary": self.summary,
            "sections": [s.to_dict() for s in self.sections]
        }
    
    def to_markdown(self) -> str:
        """Convert to Markdown format"""
        md = f"# {self.title}\n\n"
        md += f"> {self.summary}\n\n"
        for section in self.sections:
            md += section.to_markdown()
        return md


@dataclass
class Report:
    """Complete Report"""
    report_id: str
    simulation_id: str
    graph_id: str
    simulation_requirement: str
    status: ReportStatus
    outline: Optional[ReportOutline] = None
    markdown_content: str = ""
    created_at: str = ""
    completed_at: str = ""
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "simulation_id": self.simulation_id,
            "graph_id": self.graph_id,
            "simulation_requirement": self.simulation_requirement,
            "status": self.status.value,
            "outline": self.outline.to_dict() if self.outline else None,
            "markdown_content": self.markdown_content,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "error": self.error
        }


# ═══════════════════════════════════════════════════════════════
# Prompt Template Constants
# ═══════════════════════════════════════════════════════════════

# ── Tool Descriptions ──

TOOL_DESC_INSIGHT_FORGE = """\
【Tiefgehende Einblicke - Leistungsstarkes Retrieval-Tool】
Dies ist unser leistungsstarkes Retrieval-Tool, speziell für Tiefenanalysen entwickelt. Es wird:
1. Ihre Frage automatisch in mehrere Unterfragen zerlegen
2. Informationen aus dem Simulationsgraphen aus mehreren Dimensionen abrufen
3. Ergebnisse aus semantischer Suche, Entitätsanalyse und Beziehungsketten-Verfolgung integrieren
4. Die umfassendsten und tiefgründigsten Retrieval-Ergebnisse zurückgeben

【Anwendungsszenarien】
- Tiefe Analyse eines Themas erforderlich
- Mehrere Aspekte eines Ereignisses verstehen nötig
- Reichhaltiges Material für Berichtskapitel benötigt

【Rückgabeinhalt】
- Relevante Fakten im Original (direkt zitierbar)
- Kern-Entitäts-Einblicke
- Beziehungsketten-Analyse"""

TOOL_DESC_PANORAMA_SEARCH = """\
【Breitensuche - Gesamtübersicht erhalten】
Dieses Tool wird verwendet, um eine vollständige Gesamtübersicht der Simulationsergebnisse zu erhalten, besonders geeignet, um den Entwicklungsprozess von Ereignissen zu verstehen. Es wird:
1. Alle relevanten Knoten und Beziehungen abrufen
2. Aktuell gültige Fakten von historischen/abgelaufenen Fakten unterscheiden
3. Helfen zu verstehen, wie sich die öffentliche Meinung entwickelt hat

【Anwendungsszenarien】
- Vollständigen Entwicklungsverlauf eines Ereignisses verstehen
- Öffentlichkeitswandel in verschiedenen Phasen vergleichen
- Umfassende Entitäts- und Beziehungsinformationen erhalten

【Rückgabeinhalt】
- Aktuell gültige Fakten (neueste Simulationsergebnisse)
- Historische/abgelaufene Fakten (Entwicklungsaufzeichnungen)
- Alle beteiligten Entitäten"""

TOOL_DESC_QUICK_SEARCH = """\
【Einfache Suche - Schnelles Retrieval】
Leichtgewichtiges Schnell-Retrieval-Tool, geeignet für einfache, direkte Informationsabfragen.

【Anwendungsszenarien】
- Schnelle Suche nach einer bestimmten Information
- Überprüfung eines Fakts
- Einfache Informationsabfrage

【Rückgabeinhalt】
- Liste der relevantesten Fakten zur Abfrage"""

TOOL_DESC_INTERVIEW_AGENTS = """\
【Tiefeninterview - Echte Agent-Interviews (Dual-Plattform)】
Ruft die Interview-API der OASIS-Simulationsumgebung auf, um echte Interviews mit laufenden Simulations-Agenten durchzuführen!
Dies ist keine LLM-Simulation, sondern ruft echte Interview-Schnittstellen auf, um Original-Antworten der Simulations-Agenten zu erhalten.
Standardmäßig werden beide Plattformen Twitter und Reddit gleichzeitig interviewt, um umfassendere Perspektiven zu erhalten.

Funktionsablauf:
1. Automatisches Lesen der Charakterdateien, um alle Simulations-Agenten zu verstehen
2. Intelligente Auswahl der für das Interviewthema relevantesten Agenten (z.B. Studenten, Medien, Behörden)
3. Automatische Generierung von Interviewfragen
4. Aufruf der /api/simulation/interview/batch Schnittstelle für echte Interviews auf beiden Plattformen
5. Integration aller Interviewergebnisse, Bereitstellung von Mehr-Perspektiven-Analyse

【Anwendungsszenarien】
- Meinungen aus verschiedenen Rollenperspektiven zum Ereignis verstehen (Wie sehen Studenten das? Wie sehen Medien das? Was sagen Behörden?)
- Meinungen und Standpunkte verschiedener Parteien sammeln
- Echte Antworten der Simulations-Agenten erhalten (aus der OASIS-Simulationsumgebung)
- Bericht lebendiger machen mit "Interviewprotokollen"

【Rückgabeinhalt】
- Identitätsinformationen der interviewten Agenten
- Interview-Antworten der Agenten auf Twitter und Reddit
- Schlüsselzitate (direkt zitierbar)
- Interviewzusammenfassung und Standpunktvergleich

【Wichtig】Erfordert, dass die OASIS-Simulationsumgebung läuft, um diese Funktion zu nutzen!"""

# ── Outline Planning Prompt ──

PLAN_SYSTEM_PROMPT = """\
Sie sind ein Experte für das Verfassen von "Zukunftsprognose-Berichten" mit einer "Gottes-Perspektive" auf die simulierte Welt – Sie können das Verhalten, die Äußerungen und Interaktionen jedes Agenten in der Simulation durchschauen.

【Kernkonzept】
Wir haben eine simulierte Welt aufgebaut und spezifische "Simulationsanforderungen" als Variable injiziert. Das Evolutionsergebnis der simulierten Welt ist eine Vorhersage dessen, was in der Zukunft passieren könnte. Was Sie beobachten, sind keine "Experimentdaten", sondern eine "Vorschau auf die Zukunft".

【Ihre Aufgabe】
Verfassen Sie einen "Zukunftsprognose-Bericht", der folgende Fragen beantwortet:
1. Was ist in der Zukunft unter unseren Bedingungen passiert?
2. Wie reagieren und handeln verschiedene Agenten (Bevölkerungsgruppen)?
3. Welche zukünftigen Trends und Risiken deckt diese Simulation auf?

【Berichtspositionierung】
- ✅ Dies ist ein zukunftsorientierter Prognosebericht basierend auf Simulationen, der zeigt "Was wäre wenn, wie sieht die Zukunft aus"
- ✅ Fokus auf Prognoseergebnissen: Ereignisverlauf, Gruppenreaktionen, emergente Phänomene, potenzielle Risiken
- ✅ Agenten-Verhalten in der simulierten Welt ist eine Vorhersage des zukünftigen Bevölkerungsverhaltens
- ❌ Keine Analyse des aktuellen Realitätsstatus
- ❌ Keine allgemeinen öffentlichen Meinungsübersichten

【Abschnittsanzahl-Beschränkung】
- Mindestens 2 Kapitel, maximal 5 Kapitel
- Keine Unterkapitel erforderlich, jedes Kapitel enthält direkt den vollständigen Inhalt
- Inhalt sollte prägnant sein, fokussiert auf Kernprognose-Erkenntnisse
- Kapitelstruktur wird basierend auf Prognoseergebnissen selbstständig entworfen

Bitte geben Sie den Berichtsentwurf im JSON-Format aus, Format wie folgt:
{
    "title": "Berichtstitel",
    "summary": "Berichtszusammenfassung (Ein Satz, der die Kernprognose-Erkenntnis zusammenfasst)",
    "sections": [
        {
            "title": "Kapiteltitel",
            "description": "Beschreibung des Kapitelinhalts"
        }
    ]
}

Hinweis: Das sections-Array muss mindestens 2 und maximal 5 Elemente enthalten!"""

PLAN_USER_PROMPT_TEMPLATE = """\
【Prognoseszenario-Einstellung】
Die Variablen, die wir in die simulierte Welt injiziert haben (Simulationsanforderungen): {simulation_requirement}

【Simulationswelt-Größe】
- Anzahl der an der Simulation teilnehmenden Entitäten: {total_nodes}
- Anzahl der zwischen Entitäten erzeugten Beziehungen: {total_edges}
- Entitätstyp-Verteilung: {entity_types}
- Anzahl aktiver Agenten: {total_entities}

【Beispiele zukünftiger Fakten aus der Simulationsprognose】
{related_facts_json}

Bitte betrachten Sie diese Zukunftsvorschau aus der "Gottes-Perspektive":
1. Welchen Zustand zeigt die Zukunft unter unseren Bedingungen?
2. Wie reagieren und handeln verschiedene Bevölkerungsgruppen (Agenten)?
3. Welche beachtenswerten zukünftigen Trends deckt diese Simulation auf?

Entwerfen Sie basierend auf den Prognoseergebnissen die am besten geeignete Berichtskapitelstruktur.

【Erneute Erinnerung】Berichtskapitelanzahl: Mindestens 2, maximal 5, Inhalt sollte prägnant auf Kernprognose-Erkenntnisse fokussiert sein."""

# ── Section Generation Prompt ──

SECTION_SYSTEM_PROMPT_TEMPLATE = """\
Sie sind ein Experte für das Verfassen von "Zukunftsprognose-Berichten" und schreiben gerade ein Kapitel des Berichts.

Berichtstitel: {report_title}
Berichtszusammenfassung: {report_summary}
Prognoseszenario (Simulationsanforderung): {simulation_requirement}

Aktuell zu schreibendes Kapitel: {section_title}

═══════════════════════════════════════════════════════════════
【Kernkonzept】
═══════════════════════════════════════════════════════════════

Die simulierte Welt ist eine Probe für die Zukunft. Wir haben spezifische Bedingungen (Simulationsanforderungen) in die simulierte Welt injiziert,
das Verhalten und die Interaktionen der Agenten in der Simulation sind eine Vorhersage des zukünftigen Bevölkerungsverhaltens.

Ihre Aufgabe ist:
- Aufdecken, was in der Zukunft unter den festgelegten Bedingungen passiert ist
- Vorhersagen, wie verschiedene Bevölkerungsgruppen (Agenten) reagieren und handeln
- Entdecken beachtenswerter zukünftiger Trends, Risiken und Chancen

❌ Nicht als Analyse des aktuellen Realitätsstatus schreiben
✅ Fokus auf "Wie wird die Zukunft sein" – Simulationsergebnisse sind die vorhergesagte Zukunft

═══════════════════════════════════════════════════════════════
【Wichtigste Regel - Muss befolgt werden】
═══════════════════════════════════════════════════════════════

1. 【Muss Tools aufrufen, um die simulierte Welt zu beobachten】
   - Sie beobachten die Zukunftsprobe aus der "Gottes-Perspektive"
   - Alle Inhalte müssen aus Ereignissen und Agenten-Äußerungen in der simulierten Welt stammen
   - Verwenden Sie nicht Ihr eigenes Wissen, um Berichtsinhalte zu schreiben
   - Jedes Kapitel muss mindestens 3-mal Tools aufrufen (maximal 5-mal), um die simulierte Welt zu beobachten, sie repräsentiert die Zukunft

2. 【Muss Agenten-Originaläußerungen zitieren】
   - Agenten-Äußerungen und -Verhalten sind Vorhersagen des zukünftigen Bevölkerungsverhaltens
   - Verwenden Sie Zitat-Formate in Berichten, um diese Vorhersagen zu zeigen, z.B.:
     > "Eine bestimmte Bevölkerungsgruppe wird sagen: Originalinhalt..."
   - Diese Zitate sind Kernbeweise der Simulationsprognose

3. 【Sprachkonsistenz - Zitatinhalte müssen in die Berichtssprache übersetzt werden】
   - Tool-Rückgabeinhalte können englische oder gemischte Ausdrücke enthalten
   - Wenn Simulationsanforderungen und Materialoriginaltexte auf Chinesisch sind, muss der Bericht vollständig auf Chinesisch verfasst werden
   - Wenn Sie englische oder gemischte Inhalte aus Tool-Rückgaben zitieren, müssen Sie sie in fließendes Chinesisch übersetzen, bevor Sie sie in den Bericht schreiben
   - Behalten Sie die ursprüngliche Bedeutung bei, stellen Sie natürliche Ausdrücke sicher
   - Diese Regel gilt sowohl für den Haupttext als auch für Zitatblöcke (> Format)

4. 【Prognoseergebnisse treu wiedergeben】
   - Berichtsinhalte müssen repräsentative Simulationsergebnisse aus der simulierten Welt widerspiegeln
   - Fügen Sie keine Informationen hinzu, die in der Simulation nicht existieren
   - Wenn Informationen zu einem bestimmten Aspekt unzureichend sind, geben Sie dies ehrlich an

═══════════════════════════════════════════════════════════════
【⚠️ Format-Spezifikation - Extrem wichtig!】
═══════════════════════════════════════════════════════════════

【Ein Kapitel = Kleinste Inhaltseinheit】
- Jedes Kapitel ist die kleinste Bausteineinheit des Berichts
- ❌ Verwenden Sie KEINE Markdown-Überschriften (#, ##, ###, #### usw.) innerhalb des Kapitels
- ❌ Fügen Sie KEINE Kapitelhauptüberschrift am Anfang des Inhalts hinzu
- ✅ Kapitelüberschriften werden automatisch vom System hinzugefügt, Sie müssen nur reinen Textinhalt schreiben
- ✅ Verwenden Sie **Fettdruck**, Absatztrennung, Zitate, Listen zur Inhaltsorganisation, aber keine Überschriften

【Korrektes Beispiel】
```
Dieses Kapitel analysiert die Verbreitungssituation der öffentlichen Meinung zum Ereignis. Durch tiefe Analyse der Simulationsdaten fanden wir...

**Erste Veröffentlichungs- und Auslösephase**

Weibo fungierte als Hauptort der ersten Informationen und übernahm die Kernfunktion der Erstveröffentlichung:

> "Weibo trug 68% der Erstveröffentlichungs-Lautstärke bei..."

**Emotionsverstärkungsphase**

Die Douyin-Plattform verstärkte den Einfluss des Ereignisses weiter:

- Starke visuelle Wirkung
- Hoher emotionaler Resonanzgrad
```

【Falsches Beispiel】
```
## Executive Summary          ← Falsch! Fügen Sie keine Überschriften hinzu
### 1. Erste Veröffentlichungsphase     ← Falsch! Verwenden Sie KEINE ### für Unterabschnitte
#### 1.1 Detaillierte Analyse   ← Falsch! Verwenden Sie KEINE #### für Unterteilungen

Dieses Kapitel analysiert...
```

═══════════════════════════════════════════════════════════════
【Verfügbare Retrieval-Tools】（3-5 Aufrufe pro Kapitel）
═══════════════════════════════════════════════════════════════

{tools_description}

【Tool-Nutzungsempfehlungen - Bitte verschiedene Tools mischen, nicht nur eines verwenden】
- insight_forge: Tiefgehende Einblicksanalyse, automatische Problemzerlegung und mehrdimensionale Fakten- und Beziehungsabfrage
- panorama_search: Weitwinkel-Panorama-Suche, Verständnis des Ereignisgesamtbilds, Zeitlinie und Entwicklungsprozess
- quick_search: Schnelle Überprüfung eines bestimmten Informationspunkts
- interview_agents: Interview-Simulations-Agenten, Erhalt erster-Person-Perspektiven und echter Reaktionen verschiedener Rollen

═══════════════════════════════════════════════════════════════
【Arbeitsablauf】
═══════════════════════════════════════════════════════════════

Bei jeder Antwort können Sie nur eine der folgenden beiden Dinge tun (nicht beides gleichzeitig):

Option A - Tool aufrufen:
Geben Sie Ihre Überlegung aus, dann rufen Sie ein Tool mit folgendem Format auf:
<tool_call>
{{"name": "Tool-Name", "parameters": {{"Parametername": "Parameterwert"}}}}
</tool_call>
Das System führt das Tool aus und gibt das Ergebnis zurück. Sie müssen und können keine Tool-Rückgabeergebnisse selbst schreiben.

Option B - Endgültigen Inhalt ausgeben:
Wenn Sie durch Tools genügend Informationen erhalten haben, geben Sie den Kapitelinhalt mit "Final Answer:" als Präfix aus.

⚠️ Streng verboten:
- Verboten, Tool-Aufruf und Final Answer in einer Antwort zu kombinieren
- Verboten, Tool-Rückgabeergebnisse (Observation) selbst zu erfinden, alle Tool-Ergebnisse werden vom System injiziert
- Maximal ein Tool pro Antwort aufrufen

═══════════════════════════════════════════════════════════════
【Anforderungen an den Kapitelinhalt】
═══════════════════════════════════════════════════════════════

1. Inhalt muss auf Tool-abgerufenen Simulationsdaten basieren
2. Zitieren Sie ausgiebig Originaltexte, um Simulationseffekte zu zeigen
3. Verwenden Sie Markdown-Format (aber keine Überschriften verwenden):
   - Verwenden Sie **Fetttext**, um Schwerpunkte zu markieren (anstelle von Unterüberschriften)
   - Verwenden Sie Listen (- oder 1.2.3.), um Hauptpunkte zu organisieren
   - Verwenden Sie Leerzeilen, um verschiedene Absätze zu trennen
   - ❌ Verwenden Sie KEINE #, ##, ###, #### oder andere Überschriftssyntax
4. 【Zitat-Format-Spezifikation - Muss als eigener Absatz stehen】
   Zitate müssen eigenständige Absätze sein, mit einer Leerzeile davor und danach, nicht im Absatz gemischt:

   ✅ Korrektes Format:
   ```
   Die Antwort der Schule wurde als mangelhaft an Substanz empfunden.

   > "Das Reaktionsmuster der Schule erscheint starr und langsam in der sich schnell verändernden Social-Media-Umgebung."

   Diese Bewertung spiegelt die allgemeine Unzufriedenheit der Öffentlichkeit wider.
   ```

   ❌ Falsches Format:
   ```
   Die Antwort der Schule wurde als mangelhaft an Substanz empfunden.> "Das Reaktionsmuster der Schule..." Diese Bewertung spiegelt...
   ```
5. Halten Sie logische Kohärenz mit anderen Kapiteln
6. 【Wiederholung vermeiden】Lesen Sie sorgfältig den untenstehenden bereits fertigen Kapitelinhalt, wiederholen Sie keine gleichen Informationen
7. 【Erneute Betonung】Fügen Sie KEINE Überschriften hinzu! Verwenden Sie **Fettdruck** anstelle von Unterkapitelüberschriften"""

SECTION_USER_PROMPT_TEMPLATE = """\
Fertige Kapitelinhalt (bitte sorgfältig lesen, Wiederholungen vermeiden):
{previous_content}

═══════════════════════════════════════════════════════════════
【Aktuelle Aufgabe】Kapitel schreiben: {section_title}
═══════════════════════════════════════════════════════════════

【Wichtige Erinnerung】
1. Lesen Sie sorgfältig die oben fertigen Kapitel, vermeiden Sie die Wiederholung gleicher Inhalte!
2. Müssen vor dem Start Tools aufrufen, um Simulationsdaten zu erhalten
3. Bitte verschiedene Tools mischen, nicht nur eines verwenden
4. Berichtsinhalt muss aus Retrieval-Ergebnissen stammen, nicht aus eigenem Wissen

【⚠️ Format-Warnung - Muss befolgt werden】
- ❌ Schreiben Sie KEINE Überschriften (#, ##, ###, #### sind alle nicht erlaubt)
- ❌ Schreiben Sie NICHT "{section_title}" als Anfang
- ✅ Kapitelüberschriften werden automatisch vom System hinzugefügt
- ✅ Schreiben Sie direkt den Haupttext, verwenden Sie **Fettdruck** anstelle von Unterkapitelüberschriften

Bitte beginnen Sie:
1. Zuerst überlegen (Thought), welche Informationen dieses Kapitel benötigt
2. Dann Tool aufrufen (Action), um Simulationsdaten zu erhalten
3. Nach Sammeln ausreichender Informationen Final Answer ausgeben (reiner Text, keine Überschriften)"""

# ── ReACT Loop Message Templates ──

REACT_OBSERVATION_TEMPLATE = """\
Observation (Retrieval-Ergebnis):

═══ Tool {tool_name} Rückgabe ═══
{result}

═══════════════════════════════════════════════════════════════
Tool {tool_calls_count}/{max_tool_calls} mal aufgerufen（Verwendet: {used_tools_str}）{unused_hint}
- Wenn Informationen ausreichend: Geben Sie Kapitelinhalt mit "Final Answer:" als Präfix aus (muss obigen Originaltext zitieren)
- Wenn mehr Informationen benötigt: Rufen Sie ein Tool auf, um weiter zu recherchieren
═══════════════════════════════════════════════════════════════"""

REACT_INSUFFICIENT_TOOLS_MSG = (
    "【Hinweis】Sie haben nur {tool_calls_count} mal Tools aufgerufen, mindestens {min_tool_calls} mal erforderlich."
    "Bitte rufen Sie Tools auf, um mehr Simulationsdaten zu erhalten, dann geben Sie Final Answer aus. {unused_hint}"
)

REACT_INSUFFICIENT_TOOLS_MSG_ALT = (
    "Aktuell nur {tool_calls_count} mal Tools aufgerufen, mindestens {min_tool_calls} mal erforderlich."
    "Bitte rufen Sie Tools auf, um Simulationsdaten zu erhalten. {unused_hint}"
)

REACT_TOOL_LIMIT_MSG = (
    "Tool-Aufruf-Anzahl hat Limit erreicht（{tool_calls_count}/{max_tool_calls}）, kann keine Tools mehr aufrufen."
    'Bitte geben Sie sofort basierend auf den erhaltenen Informationen den Kapitelinhalt mit "Final Answer:" als Präfix aus.'
)

REACT_UNUSED_TOOLS_HINT = "\n💡 Sie haben noch nicht verwendet: {unused_list}, empfohlen, verschiedene Tools für mehrdimensionale Informationen zu nutzen"

REACT_FORCE_FINAL_MSG = "Tool-Aufruf-Limit erreicht, bitte geben Sie direkt Final Answer: aus und generieren Sie den Kapitelinhalt."

# ── Chat Prompt ──

CHAT_SYSTEM_PROMPT_TEMPLATE = """\
Sie sind ein prägnanter und effizienter Simulationsprognose-Assistent.

【Hintergrund】
Prognosebedingungen: {simulation_requirement}

【Bereits generierte Analyseberichte】
{report_content}

【Regeln】
1. Priorisieren Sie die Beantwortung von Fragen basierend auf obenstehendem Berichtsinhalt
2. Beantworten Sie Fragen direkt, vermeiden Sie umfangreiche Überlegungsdiskussionen
3. Rufen Sie Tools nur ab, wenn der Berichtsinhalt nicht ausreicht, um Fragen zu beantworten
4. Antworten sollten prägnant, klar und strukturiert sein

【Verfügbare Tools】（Nur bei Bedarf verwenden, maximal 1-2 Aufrufe）
{tools_description}

【Tool-Aufruf-Format】
<tool_call>
{{"name": "Tool-Name", "parameters": {{"Parametername": "Parameterwert"}}}}
</tool_call>

【Antwortstil】
- Prägnant und direkt, keine langen Reden
- Verwenden Sie > Format, um Schlüsselinhalte zu zitieren
- Priorisieren Sie Schlussfolgerungen, dann Erklärungen"""

CHAT_OBSERVATION_SUFFIX = "\n\nBitte beantworten Sie die Frage prägnant."


# ═══════════════════════════════════════════════════════════════
# ReportAgent Main Class
# ═══════════════════════════════════════════════════════════════


class ReportAgent:
    """
    Report Agent - Simulation Report Generation Agent

    Uses ReACT (Reasoning + Acting) mode:
    1. Planning phase: Analyze simulation requirements, plan report structure
    2. Generation phase: Generate content section by section, each section can call tools multiple times
    3. Reflection phase: Check content completeness and accuracy
    """
    
    # Maximum tool calls (per section)
    MAX_TOOL_CALLS_PER_SECTION = 5
    
    # Maximum reflection rounds
    MAX_REFLECTION_ROUNDS = 3
    
    # Maximum tool calls in chat
    MAX_TOOL_CALLS_PER_CHAT = 2
    
    def __init__(
        self, 
        graph_id: str,
        simulation_id: str,
        simulation_requirement: str,
        llm_client: Optional[LLMClient] = None,
        zep_tools: Optional[ZepToolsService] = None
    ):
        """
        Initialize Report Agent
        
        Args:
            graph_id: Graph ID
            simulation_id: Simulation ID
            simulation_requirement: Simulation requirement description
            llm_client: LLM client (optional)
            zep_tools: Zep tools service (optional)
        """
        self.graph_id = graph_id
        self.simulation_id = simulation_id
        self.simulation_requirement = simulation_requirement
        
        self.llm = llm_client or LLMClient()
        self.zep_tools = zep_tools or ZepToolsService()
        
        # Tool definitions
        self.tools = self._define_tools()
        
        # Log recorder (initialized in generate_report)
        self.report_logger: Optional[ReportLogger] = None
        # Console log recorder (initialized in generate_report)
        self.console_logger: Optional[ReportConsoleLogger] = None
        
        logger.info(f"ReportAgent Initialisierung abgeschlossen: graph_id={graph_id}, simulation_id={simulation_id}")
    
    def _define_tools(self) -> Dict[str, Dict[str, Any]]:
        """Define available tools"""
        return {
            "insight_forge": {
                "name": "insight_forge",
                "description": TOOL_DESC_INSIGHT_FORGE,
                "parameters": {
                    "query": "Das Problem oder Thema, das Sie tiefgehend analysieren möchten",
                    "report_context": "Kontext des aktuellen Berichtskapitels (optional, hilft bei präziserer Unterfragen-Generierung)"
                }
            },
            "panorama_search": {
                "name": "panorama_search",
                "description": TOOL_DESC_PANORAMA_SEARCH,
                "parameters": {
                    "query": "Suchanfrage, verwendet für Relevanz-Sortierung",
                    "include_expired": "Ob abgelaufene/historische Inhalte einbezogen werden sollen (Standard True)"
                }
            },
            "quick_search": {
                "name": "quick_search",
                "description": TOOL_DESC_QUICK_SEARCH,
                "parameters": {
                    "query": "Suchanfrage-String",
                    "limit": "Anzahl der zurückgegebenen Ergebnisse (optional, Standard 10)"
                }
            },
            "interview_agents": {
                "name": "interview_agents",
                "description": TOOL_DESC_INTERVIEW_AGENTS,
                "parameters": {
                    "interview_topic": "Interview-Thema oder Bedarfsbeschreibung (z.B.: 'Meinungen von Studenten zum Schlafsaal-Formaldehyd-Vorfall verstehen')",
                    "max_agents": "Maximale Anzahl zu interviewender Agenten (optional, Standard 5, Maximum 10)"
                }
            }
        }
    
    def _execute_tool(self, tool_name: str, parameters: Dict[str, Any], report_context: str = "") -> str:
        """
        Execute tool call
        
        Args:
            tool_name: Tool name
            parameters: Tool parameters
            report_context: Report context (for InsightForge)
            
        Returns:
            Tool execution result (text format)
        """
        logger.info(f"Tool ausführen: {tool_name}, Parameter: {parameters}")
        
        try:
            if tool_name == "insight_forge":
                query = parameters.get("query", "")
                ctx = parameters.get("report_context", "") or report_context
                result = self.zep_tools.insight_forge(
                    graph_id=self.graph_id,
                    query=query,
                    simulation_requirement=self.simulation_requirement,
                    report_context=ctx
                )
                return result.to_text()
            
            elif tool_name == "panorama_search":
                # Breadth search - get full picture
                query = parameters.get("query", "")
                include_expired = parameters.get("include_expired", True)
                if isinstance(include_expired, str):
                    include_expired = include_expired.lower() in ['true', '1', 'yes']
                result = self.zep_tools.panorama_search(
                    graph_id=self.graph_id,
                    query=query,
                    include_expired=include_expired
                )
                return result.to_text()
            
            elif tool_name == "quick_search":
                # Simple search - quick retrieval
                query = parameters.get("query", "")
                limit = parameters.get("limit", 10)
                if isinstance(limit, str):
                    limit = int(limit)
                result = self.zep_tools.quick_search(
                    graph_id=self.graph_id,
                    query=query,
                    limit=limit
                )
                return result.to_text()
            
            elif tool_name == "interview_agents":
                # Deep interview - call real OASIS interview API to get simulation agent responses (dual platform)
                interview_topic = parameters.get("interview_topic", parameters.get("query", ""))
                max_agents = parameters.get("max_agents", 5)
                if isinstance(max_agents, str):
                    max_agents = int(max_agents)
                max_agents = min(max_agents, 10)
                result = self.zep_tools.interview_agents(
                    simulation_id=self.simulation_id,
                    interview_requirement=interview_topic,
                    simulation_requirement=self.simulation_requirement,
                    max_agents=max_agents
                )
                return result.to_text()
            
            # ========== Backward compatible old tools (internally redirected to new tools) ==========
            
            elif tool_name == "search_graph":
                # Redirect to quick_search
                logger.info("search_graph wurde zu quick_search umgeleitet")
                return self._execute_tool("quick_search", parameters, report_context)
            
            elif tool_name == "get_graph_statistics":
                result = self.zep_tools.get_graph_statistics(self.graph_id)
                return json.dumps(result, ensure_ascii=False, indent=2)
            
            elif tool_name == "get_entity_summary":
                entity_name = parameters.get("entity_name", "")
                result = self.zep_tools.get_entity_summary(
                    graph_id=self.graph_id,
                    entity_name=entity_name
                )
                return json.dumps(result, ensure_ascii=False, indent=2)
            
            elif tool_name == "get_simulation_context":
                # Redirect to insight_forge as it's more powerful
                logger.info("get_simulation_context wurde zu insight_forge umgeleitet")
                query = parameters.get("query", self.simulation_requirement)
                return self._execute_tool("insight_forge", {"query": query}, report_context)
            
            elif tool_name == "get_entities_by_type":
                entity_type = parameters.get("entity_type", "")
                nodes = self.zep_tools.get_entities_by_type(
                    graph_id=self.graph_id,
                    entity_type=entity_type
                )
                result = [n.to_dict() for n in nodes]
                return json.dumps(result, ensure_ascii=False, indent=2)
            
            else:
                return f"Unbekanntes Tool: {tool_name}. Bitte verwenden Sie eines der folgenden Tools: insight_forge, panorama_search, quick_search"
                
        except Exception as e:
            logger.error(f"Tool-Ausführung fehlgeschlagen: {tool_name}, Fehler: {str(e)}")
            return f"Tool-Ausführung fehlgeschlagen: {str(e)}"
    
    # Valid tool names set, used for bare JSON fallback parsing validation
    VALID_TOOL_NAMES = {"insight_forge", "panorama_search", "quick_search", "interview_agents"}

    def _parse_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse tool calls from LLM response

        Supported formats (by priority):
        1. <tool_call>{"name": "tool_name", "parameters": {...}}</tool_call>
        2. Bare JSON (the entire response or a single line is a tool call JSON)
        """
        tool_calls = []

        # Format 1: XML style (standard format)
        xml_pattern = r'<tool_call>\s*(\{.*?\})\s*</tool_call>'
        for match in re.finditer(xml_pattern, response, re.DOTALL):
            try:
                call_data = json.loads(match.group(1))
                tool_calls.append(call_data)
            except json.JSONDecodeError:
                pass

        if tool_calls:
            return tool_calls

        # Format 2: Fallback - LLM outputs bare JSON directly (without <tool_call> tags)
        # Only try when format 1 doesn't match, to avoid mis-matching JSON in the body
        stripped = response.strip()
        if stripped.startswith('{') and stripped.endswith('}'):
            try:
                call_data = json.loads(stripped)
                if self._is_valid_tool_call(call_data):
                    tool_calls.append(call_data)
                    return tool_calls
            except json.JSONDecodeError:
                pass

        # Response may contain thinking text + bare JSON, try to extract the last JSON object
        json_pattern = r'(\{"(?:name|tool)"\s*:.*?\})\s*$'
        match = re.search(json_pattern, stripped, re.DOTALL)
        if match:
            try:
                call_data = json.loads(match.group(1))
                if self._is_valid_tool_call(call_data):
                    tool_calls.append(call_data)
            except json.JSONDecodeError:
                pass

        return tool_calls

    def _is_valid_tool_call(self, data: dict) -> bool:
        """Validate whether the parsed JSON is a valid tool call"""
        # Support both {"name": ..., "parameters": ...} and {"tool": ..., "params": ...} key names
        tool_name = data.get("name") or data.get("tool")
        if tool_name and tool_name in self.VALID_TOOL_NAMES:
            # Standardize key names to name / parameters
            if "tool" in data:
                data["name"] = data.pop("tool")
            if "params" in data and "parameters" not in data:
                data["parameters"] = data.pop("params")
            return True
        return False
    
    def _get_tools_description(self) -> str:
        """Generate tool description text"""
        desc_parts = ["Verfügbare Tools:"]
        for name, tool in self.tools.items():
            params_desc = ", ".join([f"{k}: {v}" for k, v in tool["parameters"].items()])
            desc_parts.append(f"- {name}: {tool['description']}")
            if params_desc:
                desc_parts.append(f"  Parameter: {params_desc}")
        return "\n".join(desc_parts)
    
    def plan_outline(
        self, 
        progress_callback: Optional[Callable] = None
    ) -> ReportOutline:
        """
        Plan report outline
        
        Use LLM to analyze simulation requirements and plan the report structure
        
        Args:
            progress_callback: Progress callback function
            
        Returns:
            ReportOutline: Report outline
        """
        logger.info("Beginne mit der Gliederungsplanung...")
        
        if progress_callback:
            progress_callback("planning", 0, "Simulationsanforderungen analysieren...")
        
        # First get simulation context
        context = self.zep_tools.get_simulation_context(
            graph_id=self.graph_id,
            simulation_requirement=self.simulation_requirement
        )
        
        if progress_callback:
            progress_callback("planning", 30, "Berichtgliederung generieren...")
        
        system_prompt = PLAN_SYSTEM_PROMPT
        user_prompt = PLAN_USER_PROMPT_TEMPLATE.format(
            simulation_requirement=self.simulation_requirement,
            total_nodes=context.get('graph_statistics', {}).get('total_nodes', 0),
            total_edges=context.get('graph_statistics', {}).get('total_edges', 0),
            entity_types=list(context.get('graph_statistics', {}).get('entity_types', {}).keys()),
            total_entities=context.get('total_entities', 0),
            related_facts_json=json.dumps(context.get('related_facts', [])[:10], ensure_ascii=False, indent=2),
        )

        try:
            response = self.llm.chat_json(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            if progress_callback:
                progress_callback("planning", 80, "Gliederungsstruktur parsen...")
            
            # Parse outline
            sections = []
            for section_data in response.get("sections", []):
                sections.append(ReportSection(
                    title=section_data.get("title", ""),
                    content=""
                ))
            
            outline = ReportOutline(
                title=response.get("title", "Simulationsanalysebericht"),
                summary=response.get("summary", ""),
                sections=sections
            )
            
            if progress_callback:
                progress_callback("planning", 100, "Gliederungsplanung abgeschlossen")
            
            logger.info(f"Gliederungsplanung abgeschlossen: {len(sections)} Kapitel")
            return outline
            
        except Exception as e:
            logger.error(f"Gliederungsplanung fehlgeschlagen: {str(e)}")
            # Return default outline (3 sections, as fallback)
            return ReportOutline(
                title="Zukunftsprognose-Bericht",
                summary="Zukunftstrends und Risikoanalyse basierend auf Simulationsprognosen",
                sections=[
                    ReportSection(title="Prognoseszenario und Kernbefunde"),
                    ReportSection(title="Analyse des Bevölkerungsverhaltens"),
                    ReportSection(title="Trendausblick und Risikohinweise")
                ]
            )
    
    def _generate_section_react(
        self, 
        section: ReportSection,
        outline: ReportOutline,
        previous_sections: List[str],
        progress_callback: Optional[Callable] = None,
        section_index: int = 0
    ) -> str:
        """
        Generate single section content using ReACT mode
        
        ReACT loop:
        1. Thought - Analyze what information is needed
        2. Action - Call tools to get information
        3. Observation - Analyze tool return results
        4. Repeat until information is sufficient or max iterations reached
        5. Final Answer - Generate section content
        
        Args:
            section: Section to generate
            outline: Complete outline
            previous_sections: Previous sections' content (for maintaining coherence)
            progress_callback: Progress callback
            section_index: Section index (for logging)
            
        Returns:
            Section content (Markdown format)
        """
        logger.info(f"ReACT Generierung Kapitel: {section.title}")
        
        # Record section start log
        if self.report_logger:
            self.report_logger.log_section_start(section.title, section_index)
        
        system_prompt = SECTION_SYSTEM_PROMPT_TEMPLATE.format(
            report_title=outline.title,
            report_summary=outline.summary,
            simulation_requirement=self.simulation_requirement,
            section_title=section.title,
            tools_description=self._get_tools_description(),
        )

        # Build user prompt - pass each completed section with max 4000 characters
        if previous_sections:
            previous_parts = []
            for sec in previous_sections:
                # Each section max 4000 characters
                truncated = sec[:4000] + "..." if len(sec) > 4000 else sec
                previous_parts.append(truncated)
            previous_content = "\n\n---\n\n".join(previous_parts)
        else:
            previous_content = "(Dies ist das erste Kapitel)"
        
        user_prompt = SECTION_USER_PROMPT_TEMPLATE.format(
            previous_content=previous_content,
            section_title=section.title,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # ReACT loop
        tool_calls_count = 0
        max_iterations = 5  # Maximum iterations
        min_tool_calls = 3  # Minimum tool calls
        conflict_retries = 0  # Consecutive conflict count for simultaneous tool call and Final Answer
        used_tools = set()  # Record used tool names
        all_tools = {"insight_forge", "panorama_search", "quick_search", "interview_agents"}

        # Report context, used for InsightForge sub-question generation
        report_context = f"Kapiteltitel: {section.title}\nSimulationsanforderung: {self.simulation_requirement}"
        
        for iteration in range(max_iterations):
            if progress_callback:
                progress_callback(
                    "generating", 
                    int((iteration / max_iterations) * 100),
                    f"Tiefenrecherche und Schreiben ({tool_calls_count}/{self.MAX_TOOL_CALLS_PER_SECTION})"
                )
            
            # Call LLM
            response = self.llm.chat(
                messages=messages,
                temperature=0.5,
                max_tokens=4096
            )

            # Check if LLM returns None (API exception or empty content)
            if response is None:
                logger.warning(f"Kapitel {section.title} Iteration {iteration + 1}: LLM gibt None zurück")
                # If iterations remain, add message and retry
                if iteration < max_iterations - 1:
                    messages.append({"role": "assistant", "content": "(Leere Antwort)"})
                    messages.append({"role": "user", "content": "Bitte fahren Sie mit der Inhaltsgenerierung fort."})
                    continue
                # Last iteration also returns None, break to forced completion
                break

            logger.debug(f"LLM-Antwort: {response[:200]}...")

            # Parse once, reuse results
            tool_calls = self._parse_tool_calls(response)
            has_tool_calls = bool(tool_calls)
            has_final_answer = "Final Answer:" in response

            # ── Conflict handling: LLM outputs both tool call and Final Answer ──
            if has_tool_calls and has_final_answer:
                conflict_retries += 1
                logger.warning(
                    f"Kapitel {section.title} Runde {iteration+1}: "
                    f"LLM gibt gleichzeitig Tool-Aufruf und Final Answer aus (Konflikt {conflict_retries})"
                )

                if conflict_retries <= 2:
                    # First two times: discard this response, require LLM to respond again
                    messages.append({"role": "assistant", "content": response})
                    messages.append({
                        "role": "user",
                        "content": (
                            "【Formatfehler】Sie haben in einer Antwort sowohl Tool-Aufruf als auch Final Answer enthalten, das ist nicht erlaubt.\n"
                            "Bei jeder Antwort können Sie nur eine der folgenden zwei Dinge tun:\n"
                            "- Ein Tool aufrufen (geben Sie einen <tool_call>-Block aus, schreiben Sie kein Final Answer)\n"
                            "- Endgültigen Inhalt ausgeben (beginnen Sie mit 'Final Answer:', enthalten Sie kein <tool_call>)\n"
                            "Bitte antworten Sie erneut und tun Sie nur eine Sache."
                        ),
                    })
                    continue
                else:
                    # Third time: degrade handling, truncate to first tool call, force execution
                    logger.warning(
                        f"Kapitel {section.title}: {conflict_retries} aufeinanderfolgende Konflikte, "
                        "wird auf Abschneiden und Ausführen des ersten Tool-Aufrufs herabgestuft"
                    )
                    first_tool_end = response.find('</tool_call>')
                    if first_tool_end != -1:
                        response = response[:first_tool_end + len('</tool_call>')]
                        tool_calls = self._parse_tool_calls(response)
                        has_tool_calls = bool(tool_calls)
                    has_final_answer = False
                    conflict_retries = 0

            # Record LLM response log
            if self.report_logger:
                self.report_logger.log_llm_response(
                    section_title=section.title,
                    section_index=section_index,
                    response=response,
                    iteration=iteration + 1,
                    has_tool_calls=has_tool_calls,
                    has_final_answer=has_final_answer
                )

            # ── Case 1: LLM outputs Final Answer ──
            if has_final_answer:
                # Insufficient tool calls, reject and require more tool calls
                if tool_calls_count < min_tool_calls:
                    messages.append({"role": "assistant", "content": response})
                    unused_tools = all_tools - used_tools
                    unused_hint = f"(Diese Tools wurden noch nicht verwendet, empfohlen: {', '.join(unused_tools)})" if unused_tools else ""
                    messages.append({
                        "role": "user",
                        "content": REACT_INSUFFICIENT_TOOLS_MSG.format(
                            tool_calls_count=tool_calls_count,
                            min_tool_calls=min_tool_calls,
                            unused_hint=unused_hint,
                        ),
                    })
                    continue

                # Normal completion
                final_answer = response.split("Final Answer:")[-1].strip()
                logger.info(f"Kapitel {section.title} Generierung abgeschlossen（Tool-Aufrufe: {tool_calls_count}mal）")

                if self.report_logger:
                    self.report_logger.log_section_content(
                        section_title=section.title,
                        section_index=section_index,
                        content=final_answer,
                        tool_calls_count=tool_calls_count
                    )
                return final_answer

            # ── Case 2: LLM attempts to call tool ──
            if has_tool_calls:
                # Tool quota exhausted → inform clearly, require Final Answer output
                if tool_calls_count >= self.MAX_TOOL_CALLS_PER_SECTION:
                    messages.append({"role": "assistant", "content": response})
                    messages.append({
                        "role": "user",
                        "content": REACT_TOOL_LIMIT_MSG.format(
                            tool_calls_count=tool_calls_count,
                            max_tool_calls=self.MAX_TOOL_CALLS_PER_SECTION,
                        ),
                    })
                    continue

                # Only execute first tool call
                call = tool_calls[0]
                if len(tool_calls) > 1:
                    logger.info(f"LLM versucht {len(tool_calls)} Tools aufzurufen, führt nur das erste aus: {call['name']}")

                if self.report_logger:
                    self.report_logger.log_tool_call(
                        section_title=section.title,
                        section_index=section_index,
                        tool_name=call["name"],
                        parameters=call.get("parameters", {}),
                        iteration=iteration + 1
                    )

                result = self._execute_tool(
                    call["name"],
                    call.get("parameters", {}),
                    report_context=report_context
                )

                if self.report_logger:
                    self.report_logger.log_tool_result(
                        section_title=section.title,
                        section_index=section_index,
                        tool_name=call["name"],
                        result=result,
                        iteration=iteration + 1
                    )

                tool_calls_count += 1
                used_tools.add(call['name'])

                # Build unused tools hint
                unused_tools = all_tools - used_tools
                unused_hint = ""
                if unused_tools and tool_calls_count < self.MAX_TOOL_CALLS_PER_SECTION:
                    unused_hint = REACT_UNUSED_TOOLS_HINT.format(unused_list="、".join(unused_tools))

                messages.append({"role": "assistant", "content": response})
                messages.append({
                    "role": "user",
                    "content": REACT_OBSERVATION_TEMPLATE.format(
                        tool_name=call["name"],
                        result=result,
                        tool_calls_count=tool_calls_count,
                        max_tool_calls=self.MAX_TOOL_CALLS_PER_SECTION,
                        used_tools_str=", ".join(used_tools),
                        unused_hint=unused_hint,
                    ),
                })
                continue

            # ── Case 3: Neither tool call nor Final Answer ──
            messages.append({"role": "assistant", "content": response})

            if tool_calls_count < min_tool_calls:
                # Insufficient tool calls, recommend unused tools
                unused_tools = all_tools - used_tools
                unused_hint = f"(Diese Tools wurden noch nicht verwendet, empfohlen: {', '.join(unused_tools)})" if unused_tools else ""

                messages.append({
                    "role": "user",
                    "content": REACT_INSUFFICIENT_TOOLS_MSG_ALT.format(
                        tool_calls_count=tool_calls_count,
                        min_tool_calls=min_tool_calls,
                        unused_hint=unused_hint,
                    ),
                })
                continue

            # Sufficient tool calls, LLM output content but without "Final Answer:" prefix
            # Directly accept this content as final answer, no more empty loops
            logger.info(f"Kapitel {section.title} 'Final Answer:'-Präfix nicht erkannt, akzeptiere LLM-Ausgabe direkt als endgültigen Inhalt（Tool-Aufrufe: {tool_calls_count}mal）")
            final_answer = response.strip()

            if self.report_logger:
                self.report_logger.log_section_content(
                    section_title=section.title,
                    section_index=section_index,
                    content=final_answer,
                    tool_calls_count=tool_calls_count
                )
            return final_answer
        
        # Maximum iterations reached, force content generation
        logger.warning(f"Kapitel {section.title} maximale Iterationen erreicht, erzwinge Generierung")
        messages.append({"role": "user", "content": REACT_FORCE_FINAL_MSG})
        
        response = self.llm.chat(
            messages=messages,
            temperature=0.5,
            max_tokens=4096
        )

        # Check if LLM returns None during forced completion
        if response is None:
            logger.error(f"Kapitel {section.title} LLM gibt None beim erzwungenen Abschluss zurück, verwende Standardfehlermeldung")
            final_answer = f"(Dieses Kapitel wurde nicht generiert: LLM gibt leere Antwort zurück, bitte versuchen Sie es später erneut)"
        elif "Final Answer:" in response:
            final_answer = response.split("Final Answer:")[-1].strip()
        else:
            final_answer = response
        
        # Record section content generation completion log
        if self.report_logger:
            self.report_logger.log_section_content(
                section_title=section.title,
                section_index=section_index,
                content=final_answer,
                tool_calls_count=tool_calls_count
            )
        
        return final_answer
    
    def generate_report(
        self, 
        progress_callback: Optional[Callable[[str, int, str], None]] = None,
        report_id: Optional[str] = None
    ) -> Report:
        """
        Generate complete report (real-time output by section)
        
        Each section is saved to folder immediately after generation, no need to wait for entire report completion.
        File structure:
        reports/{report_id}/
            meta.json       - Report metadata
            outline.json    - Report outline
            progress.json   - Generation progress
            section_01.md   - Section 1
            section_02.md   - Section 2
            ...
            full_report.md  - Complete report
        
        Args:
            progress_callback: Progress callback function (stage, progress, message)
            report_id: Report ID (optional, auto-generated if not provided)
            
        Returns:
            Report: Complete report
        """
        import uuid
        
        # If no report_id provided, auto-generate
        if not report_id:
            report_id = f"report_{uuid.uuid4().hex[:12]}"
        start_time = datetime.now()
        
        report = Report(
            report_id=report_id,
            simulation_id=self.simulation_id,
            graph_id=self.graph_id,
            simulation_requirement=self.simulation_requirement,
            status=ReportStatus.PENDING,
            created_at=datetime.now().isoformat()
        )
        
        # Completed section title list (for progress tracking)
        completed_section_titles = []
        
        try:
            # Initialization: Create report folder and save initial state
            ReportManager._ensure_report_folder(report_id)
            
            # Initialize log recorder (structured log agent_log.jsonl)
            self.report_logger = ReportLogger(report_id)
            self.report_logger.log_start(
                simulation_id=self.simulation_id,
                graph_id=self.graph_id,
                simulation_requirement=self.simulation_requirement
            )
            
            # Initialize console log recorder (console_log.txt)
            self.console_logger = ReportConsoleLogger(report_id)
            
            ReportManager.update_progress(
                report_id, "pending", 0, "Bericht initialisieren...",
                completed_sections=[]
            )
            ReportManager.save_report(report)
            
            # Stage 1: Plan outline
            report.status = ReportStatus.PLANNING
            ReportManager.update_progress(
                report_id, "planning", 5, "Beginne mit der Gliederungsplanung...",
                completed_sections=[]
            )
            
            # Record planning start log
            self.report_logger.log_planning_start()
            
            if progress_callback:
                progress_callback("planning", 0, "Beginne mit der Gliederungsplanung...")
            
            outline = self.plan_outline(
                progress_callback=lambda stage, prog, msg: 
                    progress_callback(stage, prog // 5, msg) if progress_callback else None
            )
            report.outline = outline
            
            # Record planning completion log
            self.report_logger.log_planning_complete(outline.to_dict())
            
            # Save outline to file
            ReportManager.save_outline(report_id, outline)
            ReportManager.update_progress(
                report_id, "planning", 15, f"Gliederungsplanung abgeschlossen, insgesamt {len(outline.sections)} Kapitel",
                completed_sections=[]
            )
            ReportManager.save_report(report)
            
            logger.info(f"Gliederung in Datei gespeichert: {report_id}/outline.json")
            
            # Stage 2: Generate by section (section-by-section saving)
            report.status = ReportStatus.GENERATING
            
            total_sections = len(outline.sections)
            generated_sections = []  # Save content for context
            
            for i, section in enumerate(outline.sections):
                section_num = i + 1
                base_progress = 20 + int((i / total_sections) * 70)
                
                # Update progress
                ReportManager.update_progress(
                    report_id, "generating", base_progress,
                    f"Generiere Kapitel: {section.title} ({section_num}/{total_sections})",
                    current_section=section.title,
                    completed_sections=completed_section_titles
                )
                
                if progress_callback:
                    progress_callback(
                        "generating", 
                        base_progress, 
                        f"Generiere Kapitel: {section.title} ({section_num}/{total_sections})"
                    )
                
                # Generate main section content
                section_content = self._generate_section_react(
                    section=section,
                    outline=outline,
                    previous_sections=generated_sections,
                    progress_callback=lambda stage, prog, msg:
                        progress_callback(
                            stage, 
                            base_progress + int(prog * 0.7 / total_sections),
                            msg
                        ) if progress_callback else None,
                    section_index=section_num
                )
                
                section.content = section_content
                generated_sections.append(f"## {section.title}\n\n{section_content}")

                # Save section
                ReportManager.save_section(report_id, section_num, section)
                completed_section_titles.append(section.title)

                # Record section completion log
                full_section_content = f"## {section.title}\n\n{section_content}"

                if self.report_logger:
                    self.report_logger.log_section_full_complete(
                        section_title=section.title,
                        section_index=section_num,
                        full_content=full_section_content.strip()
                    )

                logger.info(f"Kapitel gespeichert: {report_id}/section_{section_num:02d}.md")
                
                # Update progress
                ReportManager.update_progress(
                    report_id, "generating", 
                    base_progress + int(70 / total_sections),
                    f"Kapitel {section.title} abgeschlossen",
                    current_section=None,
                    completed_sections=completed_section_titles
                )
            
            # Stage 3: Assemble complete report
            if progress_callback:
                progress_callback("generating", 95, "Vollständigen Bericht zusammenstellen...")
            
            ReportManager.update_progress(
                report_id, "generating", 95, "Vollständigen Bericht zusammenstellen...",
                completed_sections=completed_section_titles
            )
            
            # Use ReportManager to assemble complete report
            report.markdown_content = ReportManager.assemble_full_report(report_id, outline)
            report.status = ReportStatus.COMPLETED
            report.completed_at = datetime.now().isoformat()
            
            # Calculate total time
            total_time_seconds = (datetime.now() - start_time).total_seconds()
            
            # Record report completion log
            if self.report_logger:
                self.report_logger.log_report_complete(
                    total_sections=total_sections,
                    total_time_seconds=total_time_seconds
                )
            
            # Save final report
            ReportManager.save_report(report)
            ReportManager.update_progress(
                report_id, "completed", 100, "Berichtgenerierung abgeschlossen",
                completed_sections=completed_section_titles
            )
            
            if progress_callback:
                progress_callback("completed", 100, "Berichtgenerierung abgeschlossen")
            
            logger.info(f"Berichtgenerierung abgeschlossen: {report_id}")
            
            # Close console log recorder
            if self.console_logger:
                self.console_logger.close()
                self.console_logger = None
            
            return report
            
        except Exception as e:
            logger.error(f"Berichtgenerierung fehlgeschlagen: {str(e)}")
            report.status = ReportStatus.FAILED
            report.error = str(e)
            
            # Record error log
            if self.report_logger:
                self.report_logger.log_error(str(e), "failed")
            
            # Save failure status
            try:
                ReportManager.save_report(report)
                ReportManager.update_progress(
                    report_id, "failed", -1, f"Berichtgenerierung fehlgeschlagen: {str(e)}",
                    completed_sections=completed_section_titles
                )
            except Exception:
                pass  # Ignore save failure errors
            
            # Close console log recorder
            if self.console_logger:
                self.console_logger.close()
                self.console_logger = None
            
            return report
    
    def chat(
        self, 
        message: str,
        chat_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Chat with Report Agent
        
        Agent can autonomously call retrieval tools to answer questions during conversation
        
        Args:
            message: User message
            chat_history: Chat history
            
        Returns:
            {
                "response": "Agent reply",
                "tool_calls": [List of called tools],
                "sources": [Information sources]
            }
        """
        logger.info(f"Report Agent Dialog: {message[:50]}...")
        
        chat_history = chat_history or []
        
        # Get already generated report content
        report_content = ""
        try:
            report = ReportManager.get_report_by_simulation(self.simulation_id)
            if report and report.markdown_content:
                # Limit report length to avoid excessive context
                report_content = report.markdown_content[:15000]
                if len(report.markdown_content) > 15000:
                    report_content += "\n\n... [Berichtsinhalt wurde abgeschnitten] ..."
        except Exception as e:
            logger.warning(f"Berichtsinhalt abrufen fehlgeschlagen: {e}")
        
        system_prompt = CHAT_SYSTEM_PROMPT_TEMPLATE.format(
            simulation_requirement=self.simulation_requirement,
            report_content=report_content if report_content else "(Noch kein Bericht)",
            tools_description=self._get_tools_description(),
        )

        # Build messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add chat history
        for h in chat_history[-10:]:  # Limit history length
            messages.append(h)
        
        # Add user message
        messages.append({
            "role": "user", 
            "content": message
        })
        
        # ReACT loop (simplified)
        tool_calls_made = []
        max_iterations = 2  # Reduce iterations
        
        for iteration in range(max_iterations):
            response = self.llm.chat(
                messages=messages,
                temperature=0.5
            )
            
            # Parse tool calls
            tool_calls = self._parse_tool_calls(response)
            
            if not tool_calls:
                # No tool calls, return response directly
                clean_response = re.sub(r'<tool_call>.*?</tool_call>', '', response, flags=re.DOTALL)
                clean_response = re.sub(r'\[TOOL_CALL\].*?\)', '', clean_response)
                
                return {
                    "response": clean_response.strip(),
                    "tool_calls": tool_calls_made,
                    "sources": [tc.get("parameters", {}).get("query", "") for tc in tool_calls_made]
                }
            
            # Execute tool calls (limit quantity)
            tool_results = []
            for call in tool_calls[:1]:  # Max 1 tool call per iteration
                if len(tool_calls_made) >= self.MAX_TOOL_CALLS_PER_CHAT:
                    break
                result = self._execute_tool(call["name"], call.get("parameters", {}))
                tool_results.append({
                    "tool": call["name"],
                    "result": result[:1500]  # Limit result length
                })
                tool_calls_made.append(call)
            
            # Add results to messages
            messages.append({"role": "assistant", "content": response})
            observation = "\n".join([f"[{r['tool']}-Ergebnis]\n{r['result']}" for r in tool_results])
            messages.append({
                "role": "user",
                "content": observation + CHAT_OBSERVATION_SUFFIX
            })
        
        # Maximum iterations reached, get final response
        final_response = self.llm.chat(
            messages=messages,
            temperature=0.5
        )
        
        # Clean response
        clean_response = re.sub(r'<tool_call>.*?</tool_call>', '', final_response, flags=re.DOTALL)
        clean_response = re.sub(r'\[TOOL_CALL\].*?\)', '', clean_response)
        
        return {
            "response": clean_response.strip(),
            "tool_calls": tool_calls_made,
            "sources": [tc.get("parameters", {}).get("query", "") for tc in tool_calls_made]
        }


class ReportManager:
    """
    Report Manager
    
    Responsible for report persistence storage and retrieval
    
    File structure (section-by-section output):
    reports/
      {report_id}/
        meta.json          - Report metadata and status
        outline.json       - Report outline
        progress.json      - Generation progress
        section_01.md      - Section 1
        section_02.md      - Section 2
        ...
        full_report.md     - Complete report
    """
    
    # Report storage directory
    REPORTS_DIR = os.path.join(Config.UPLOAD_FOLDER, 'reports')
    
    @classmethod
    def _ensure_reports_dir(cls):
        """Ensure report root directory exists"""
        os.makedirs(cls.REPORTS_DIR, exist_ok=True)
    
    @classmethod
    def _get_report_folder(cls, report_id: str) -> str:
        """Get report folder path"""
        return os.path.join(cls.REPORTS_DIR, report_id)
    
    @classmethod
    def _ensure_report_folder(cls, report_id: str) -> str:
        """Ensure report folder exists and return path"""
        folder = cls._get_report_folder(report_id)
        os.makedirs(folder, exist_ok=True)
        return folder
    
    @classmethod
    def _get_report_path(cls, report_id: str) -> str:
        """Get report metadata file path"""
        return os.path.join(cls._get_report_folder(report_id), "meta.json")
    
    @classmethod
    def _get_report_markdown_path(cls, report_id: str) -> str:
        """Get complete report Markdown file path"""
        return os.path.join(cls._get_report_folder(report_id), "full_report.md")
    
    @classmethod
    def _get_outline_path(cls, report_id: str) -> str:
        """Get outline file path"""
        return os.path.join(cls._get_report_folder(report_id), "outline.json")
    
    @classmethod
    def _get_progress_path(cls, report_id: str) -> str:
        """Get progress file path"""
        return os.path.join(cls._get_report_folder(report_id), "progress.json")
    
    @classmethod
    def _get_section_path(cls, report_id: str, section_index: int) -> str:
        """Get section Markdown file path"""
        return os.path.join(cls._get_report_folder(report_id), f"section_{section_index:02d}.md")
    
    @classmethod
    def _get_agent_log_path(cls, report_id: str) -> str:
        """Get Agent log file path"""
        return os.path.join(cls._get_report_folder(report_id), "agent_log.jsonl")
    
    @classmethod
    def _get_console_log_path(cls, report_id: str) -> str:
        """Get console log file path"""
        return os.path.join(cls._get_report_folder(report_id), "console_log.txt")
    
    @classmethod
    def get_console_log(cls, report_id: str, from_line: int = 0) -> Dict[str, Any]:
        """
        Get console log content
        
        This is the console output log (INFO, WARNING, etc.) during report generation,
        different from the structured log in agent_log.jsonl.
        
        Args:
            report_id: Report ID
            from_line: Which line to start reading from (for incremental fetch, 0 means from beginning)
            
        Returns:
            {
                "logs": [List of log lines],
                "total_lines": Total lines,
                "from_line": Starting line number,
                "has_more": Whether there are more logs
            }
        """
        log_path = cls._get_console_log_path(report_id)
        
        if not os.path.exists(log_path):
            return {
                "logs": [],
                "total_lines": 0,
                "from_line": 0,
                "has_more": False
            }
        
        logs = []
        total_lines = 0
        
        with open(log_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                total_lines = i + 1
                if i >= from_line:
                    # Keep original log line, remove trailing newline
                    logs.append(line.rstrip('\n\r'))
        
        return {
            "logs": logs,
            "total_lines": total_lines,
            "from_line": from_line,
            "has_more": False  # Read to end
        }

    @classmethod
    def get_console_log_stream(cls, report_id: str) -> List[str]:
        """Get complete console log (fetch all at once)"""
        result = cls.get_console_log(report_id, from_line=0)
        return result["logs"]

    @classmethod
    def get_agent_log(cls, report_id: str, from_line: int = 0) -> Dict[str, Any]:
        """
        Get Agent log content

        Args:
            report_id: Report ID
            from_line: Which line to start reading from (for incremental fetch, 0 means from beginning)

        Returns:
            {
                "logs": [List of log entries],
                "total_lines": Total lines,
                "from_line": Starting line number,
                "has_more": Whether there are more logs
            }
        """
        log_path = cls._get_agent_log_path(report_id)

        if not os.path.exists(log_path):
            return {
                "logs": [],
                "total_lines": 0,
                "from_line": 0,
                "has_more": False
            }

        logs = []
        total_lines = 0

        with open(log_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                total_lines = i + 1
                if i >= from_line:
                    try:
                        log_entry = json.loads(line.strip())
                        logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue

        return {
            "logs": logs,
            "total_lines": total_lines,
            "from_line": from_line,
            "has_more": False  # Read to end
        }

    @classmethod
    def get_agent_log_stream(cls, report_id: str) -> List[Dict[str, Any]]:
        """Get complete Agent log (fetch all at once)"""
        result = cls.get_agent_log(report_id, from_line=0)
        return result["logs"]

    @classmethod
    def save_outline(cls, report_id: str, outline: ReportOutline) -> None:
        """Save report outline"""
        cls._ensure_report_folder(report_id)

        with open(cls._get_outline_path(report_id), 'w', encoding='utf-8') as f:
            json.dump(outline.to_dict(), f, ensure_ascii=False, indent=2)

        logger.info(f"Gliederung gespeichert: {report_id}")

    @classmethod
    def save_section(
        cls,
        report_id: str,
        section_index: int,
        section: ReportSection
    ) -> str:
        """
        Save a single section

        Called immediately after each section is generated for section-by-section output.

        Args:
            report_id: Report ID
            section_index: Section index (starting from 1)
            section: Section object

        Returns:
            Saved file path
        """
        cls._ensure_report_folder(report_id)

        # Build section Markdown content - clean possible duplicate titles
        cleaned_content = cls._clean_section_content(section.content, section.title)
        md_content = f"## {section.title}\n\n"
        if cleaned_content:
            md_content += f"{cleaned_content}\n\n"

        # Save file
        file_suffix = f"section_{section_index:02d}.md"
        file_path = os.path.join(cls._get_report_folder(report_id), file_suffix)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        logger.info(f"Kapitel gespeichert: {report_id}/{file_suffix}")
        return file_path

    @classmethod
    def _clean_section_content(cls, content: str, section_title: str) -> str:
        """
        Clean section content

        1. Remove duplicate Markdown heading lines at the beginning that match section title
        2. Convert all ### and lower level headings to bold text
        """
        import re

        if not content:
            return content

        content = content.strip()
        lines = content.split('\n')
        cleaned_lines = []
        skip_next_empty = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            heading_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)

            if heading_match:
                level = len(heading_match.group(1))
                title_text = heading_match.group(2).strip()

                # Check for duplicate title within first 5 lines
                if i < 5:
                    if title_text == section_title or title_text.replace(' ', '') == section_title.replace(' ', ''):
                        skip_next_empty = True
                        continue

                # Convert all heading levels to bold
                cleaned_lines.append(f"**{title_text}**")
                cleaned_lines.append("")
                continue

            if skip_next_empty and stripped == '':
                skip_next_empty = False
                continue

            skip_next_empty = False
            cleaned_lines.append(line)

        # Remove leading empty lines
        while cleaned_lines and cleaned_lines[0].strip() == '':
            cleaned_lines.pop(0)

        # Remove leading separators
        while cleaned_lines and cleaned_lines[0].strip() in ['---', '***', '___']:
            cleaned_lines.pop(0)
            while cleaned_lines and cleaned_lines[0].strip() == '':
                cleaned_lines.pop(0)

        return '\n'.join(cleaned_lines)

    @classmethod
    def update_progress(
        cls,
        report_id: str,
        status: str,
        progress: int,
        message: str,
        current_section: str = None,
        completed_sections: List[str] = None
    ) -> None:
        """Update report generation progress"""
        cls._ensure_report_folder(report_id)

        progress_data = {
            "status": status,
            "progress": progress,
            "message": message,
            "current_section": current_section,
            "completed_sections": completed_sections or [],
            "updated_at": datetime.now().isoformat()
        }

        with open(cls._get_progress_path(report_id), 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)

    @classmethod
    def get_progress(cls, report_id: str) -> Optional[Dict[str, Any]]:
        """Get report generation progress"""
        path = cls._get_progress_path(report_id)

        if not os.path.exists(path):
            return None

        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @classmethod
    def get_generated_sections(cls, report_id: str) -> List[Dict[str, Any]]:
        """Get list of generated sections"""
        folder = cls._get_report_folder(report_id)

        if not os.path.exists(folder):
            return []

        sections = []
        for filename in sorted(os.listdir(folder)):
            if filename.startswith('section_') and filename.endswith('.md'):
                file_path = os.path.join(folder, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                parts = filename.replace('.md', '').split('_')
                section_index = int(parts[1])

                sections.append({
                    "filename": filename,
                    "section_index": section_index,
                    "content": content
                })

        return sections

    @classmethod
    def assemble_full_report(cls, report_id: str, outline: ReportOutline) -> str:
        """Assemble complete report from saved section files"""
        folder = cls._get_report_folder(report_id)

        md_content = f"# {outline.title}\n\n"
        md_content += f"> {outline.summary}\n\n"
        md_content += f"---\n\n"

        sections = cls.get_generated_sections(report_id)
        for section_info in sections:
            md_content += section_info["content"]

        md_content = cls._post_process_report(md_content, outline)

        full_path = cls._get_report_markdown_path(report_id)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        logger.info(f"Vollständiger Bericht zusammengestellt: {report_id}")
        return md_content

    @classmethod
    def _post_process_report(cls, content: str, outline: ReportOutline) -> str:
        """
        Post-process report content

        1. Remove duplicate headings
        2. Keep report main title (#) and section titles (##), remove other levels
        3. Clean extra blank lines and separators
        """
        import re

        lines = content.split('\n')
        processed_lines = []
        prev_was_heading = False

        section_titles = set()
        for section in outline.sections:
            section_titles.add(section.title)

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            heading_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)

            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()

                # Check for duplicate title in recent lines
                is_duplicate = False
                for j in range(max(0, len(processed_lines) - 5), len(processed_lines)):
                    prev_line = processed_lines[j].strip()
                    prev_match = re.match(r'^(#{1,6})\s+(.+)$', prev_line)
                    if prev_match:
                        prev_title = prev_match.group(2).strip()
                        if prev_title == title:
                            is_duplicate = True
                            break

                if is_duplicate:
                    i += 1
                    while i < len(lines) and lines[i].strip() == '':
                        i += 1
                    continue

                if level == 1:
                    if title == outline.title:
                        processed_lines.append(line)
                        prev_was_heading = True
                    elif title in section_titles:
                        processed_lines.append(f"## {title}")
                        prev_was_heading = True
                    else:
                        processed_lines.append(f"**{title}**")
                        processed_lines.append("")
                        prev_was_heading = False
                elif level == 2:
                    if title in section_titles or title == outline.title:
                        processed_lines.append(line)
                        prev_was_heading = True
                    else:
                        processed_lines.append(f"**{title}**")
                        processed_lines.append("")
                        prev_was_heading = False
                else:
                    processed_lines.append(f"**{title}**")
                    processed_lines.append("")
                    prev_was_heading = False

                i += 1
                continue

            elif stripped == '---' and prev_was_heading:
                i += 1
                continue

            elif stripped == '' and prev_was_heading:
                if processed_lines and processed_lines[-1].strip() != '':
                    processed_lines.append(line)
                prev_was_heading = False

            else:
                processed_lines.append(line)
                prev_was_heading = False

            i += 1

        # Clean consecutive blank lines (keep max 2)
        result_lines = []
        empty_count = 0
        for line in processed_lines:
            if line.strip() == '':
                empty_count += 1
                if empty_count <= 2:
                    result_lines.append(line)
            else:
                empty_count = 0
                result_lines.append(line)

        return '\n'.join(result_lines)

    @classmethod
    def save_report(cls, report: Report) -> None:
        """Save report metadata and complete report"""
        cls._ensure_report_folder(report.report_id)

        # Save metadata JSON
        with open(cls._get_report_path(report.report_id), 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)

        # Save outline
        if report.outline:
            cls.save_outline(report.report_id, report.outline)

        # Save complete Markdown report
        if report.markdown_content:
            with open(cls._get_report_markdown_path(report.report_id), 'w', encoding='utf-8') as f:
                f.write(report.markdown_content)

        logger.info(f"Bericht gespeichert: {report.report_id}")

    @classmethod
    def get_report(cls, report_id: str) -> Optional[Report]:
        """Get report"""
        path = cls._get_report_path(report_id)

        if not os.path.exists(path):
            # Compatibility with old format
            old_path = os.path.join(cls.REPORTS_DIR, f"{report_id}.json")
            if os.path.exists(old_path):
                path = old_path
            else:
                return None

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        outline = None
        if data.get('outline'):
            outline_data = data['outline']
            sections = []
            for s in outline_data.get('sections', []):
                sections.append(ReportSection(
                    title=s['title'],
                    content=s.get('content', '')
                ))
            outline = ReportOutline(
                title=outline_data['title'],
                summary=outline_data['summary'],
                sections=sections
            )

        markdown_content = data.get('markdown_content', '')
        if not markdown_content:
            full_report_path = cls._get_report_markdown_path(report_id)
            if os.path.exists(full_report_path):
                with open(full_report_path, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()

        return Report(
            report_id=data['report_id'],
            simulation_id=data['simulation_id'],
            graph_id=data['graph_id'],
            simulation_requirement=data['simulation_requirement'],
            status=ReportStatus(data['status']),
            outline=outline,
            markdown_content=markdown_content,
            created_at=data.get('created_at', ''),
            completed_at=data.get('completed_at', ''),
            error=data.get('error')
        )

    @classmethod
    def get_report_by_simulation(cls, simulation_id: str) -> Optional[Report]:
        """Get report by simulation ID"""
        cls._ensure_reports_dir()

        for item in os.listdir(cls.REPORTS_DIR):
            item_path = os.path.join(cls.REPORTS_DIR, item)
            if os.path.isdir(item_path):
                report = cls.get_report(item)
                if report and report.simulation_id == simulation_id:
                    return report
            elif item.endswith('.json'):
                report_id = item[:-5]
                report = cls.get_report(report_id)
                if report and report.simulation_id == simulation_id:
                    return report

        return None

    @classmethod
    def list_reports(cls, simulation_id: Optional[str] = None, limit: int = 50) -> List[Report]:
        """List reports"""
        cls._ensure_reports_dir()

        reports = []
        for item in os.listdir(cls.REPORTS_DIR):
            item_path = os.path.join(cls.REPORTS_DIR, item)
            if os.path.isdir(item_path):
                report = cls.get_report(item)
                if report:
                    if simulation_id is None or report.simulation_id == simulation_id:
                        reports.append(report)
            elif item.endswith('.json'):
                report_id = item[:-5]
                report = cls.get_report(report_id)
                if report:
                    if simulation_id is None or report.simulation_id == simulation_id:
                        reports.append(report)

        # Sort by creation time descending
        reports.sort(key=lambda r: r.created_at, reverse=True)

        return reports[:limit]

    @classmethod
    def delete_report(cls, report_id: str) -> bool:
        """Delete report (entire folder)"""
        import shutil

        folder_path = cls._get_report_folder(report_id)

        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            shutil.rmtree(folder_path)
            logger.info(f"Berichtsordner gelöscht: {report_id}")
            return True

        # Compatibility with old format
        deleted = False
        old_json_path = os.path.join(cls.REPORTS_DIR, f"{report_id}.json")
        old_md_path = os.path.join(cls.REPORTS_DIR, f"{report_id}.md")

        if os.path.exists(old_json_path):
            os.remove(old_json_path)
            deleted = True
        if os.path.exists(old_md_path):
            os.remove(old_md_path)
            deleted = True

        return deleted
