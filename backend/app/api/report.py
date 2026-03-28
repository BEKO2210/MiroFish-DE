"""
Report-API-Routen
Stellt Schnittstellen für Simulationsbericht-Generierung, -Abruf und -Dialog bereit
"""

import os
import traceback
import threading
from flask import request, jsonify, send_file

from . import report_bp
from ..config import Config
from ..services.report_agent import ReportAgent, ReportManager, ReportStatus
from ..services.simulation_manager import SimulationManager
from ..models.project import ProjectManager
from ..models.task import TaskManager, TaskStatus
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.report')


# ============== Berichtsgenerierungs-Schnittstellen ==============

@report_bp.route('/generate', methods=['POST'])
def generate_report():
    """
    Simulationsanalysebericht generieren (asynchrone Aufgabe)
    
    Dies ist eine zeitaufwändige Operation, die Schnittstelle gibt sofort eine task_id zurück.
    Fortschritt über GET /api/report/generate/status abfragen.
    
    Anfrage (JSON):
        {
            "simulation_id": "sim_xxxx",    // Pflichtfeld, Simulations-ID
            "force_regenerate": false        // Optional, erzwungene Neugenerierung
        }
    
    Rückgabe:
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "task_id": "task_xxxx",
                "status": "generating",
                "message": "Berichtsgenerierungsaufgabe gestartet"
            }
        }
    """
    try:
        data = request.get_json() or {}
        
        simulation_id = data.get('simulation_id')
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "Bitte geben Sie eine simulation_id an"
            }), 400
        
        force_regenerate = data.get('force_regenerate', False)
        
        # Simulationsinformationen abrufen
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)
        
        if not state:
            return jsonify({
                "success": False,
                "error": f"Simulation nicht gefunden: {simulation_id}"
            }), 404
        
        # Prüfen ob bereits ein Bericht vorhanden ist
        if not force_regenerate:
            existing_report = ReportManager.get_report_by_simulation(simulation_id)
            if existing_report and existing_report.status == ReportStatus.COMPLETED:
                return jsonify({
                    "success": True,
                    "data": {
                        "simulation_id": simulation_id,
                        "report_id": existing_report.report_id,
                        "status": "completed",
                        "message": "Bericht bereits vorhanden",
                        "already_generated": True
                    }
                })
        
        # Projektinformationen abrufen
        project = ProjectManager.get_project(state.project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": f"Projekt nicht gefunden: {state.project_id}"
            }), 404
        
        graph_id = state.graph_id or project.graph_id
        if not graph_id:
            return jsonify({
                "success": False,
                "error": "Graph-ID fehlt, bitte stellen Sie sicher, dass der Graph erstellt wurde"
            }), 400
        
        simulation_requirement = project.simulation_requirement
        if not simulation_requirement:
            return jsonify({
                "success": False,
                "error": "Simulationsanforderungsbeschreibung fehlt"
            }), 400
        
        # report_id vorab generieren, um sie sofort an das Frontend zurückzugeben
        import uuid
        report_id = f"report_{uuid.uuid4().hex[:12]}"
        
        # Asynchrone Aufgabe erstellen
        task_manager = TaskManager()
        task_id = task_manager.create_task(
            task_type="report_generate",
            metadata={
                "simulation_id": simulation_id,
                "graph_id": graph_id,
                "report_id": report_id
            }
        )
        
        # Hintergrundaufgabe definieren
        def run_generate():
            try:
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.PROCESSING,
                    progress=0,
                    message="Report Agent wird initialisiert..."
                )
                
                # Report Agent erstellen
                agent = ReportAgent(
                    graph_id=graph_id,
                    simulation_id=simulation_id,
                    simulation_requirement=simulation_requirement
                )
                
                # Fortschritts-Callback
                def progress_callback(stage, progress, message):
                    task_manager.update_task(
                        task_id,
                        progress=progress,
                        message=f"[{stage}] {message}"
                    )
                
                # Bericht generieren (vorab generierte report_id übergeben)
                report = agent.generate_report(
                    progress_callback=progress_callback,
                    report_id=report_id
                )
                
                # Bericht speichern
                ReportManager.save_report(report)
                
                if report.status == ReportStatus.COMPLETED:
                    task_manager.complete_task(
                        task_id,
                        result={
                            "report_id": report.report_id,
                            "simulation_id": simulation_id,
                            "status": "completed"
                        }
                    )
                else:
                    task_manager.fail_task(task_id, report.error or "Berichtsgenerierung fehlgeschlagen")
                
            except Exception as e:
                logger.error(f"Berichtsgenerierung fehlgeschlagen: {str(e)}")
                task_manager.fail_task(task_id, str(e))
        
        # Hintergrund-Thread starten
        thread = threading.Thread(target=run_generate, daemon=True)
        thread.start()
        
        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "report_id": report_id,
                "task_id": task_id,
                "status": "generating",
                "message": "Berichtsgenerierungsaufgabe gestartet, Fortschritt über /api/report/generate/status abfragen",
                "already_generated": False
            }
        })
        
    except Exception as e:
        logger.error(f"Start der Berichtsgenerierungsaufgabe fehlgeschlagen: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/generate/status', methods=['POST'])
def get_generate_status():
    """
    Fortschritt der Berichtsgenerierungsaufgabe abfragen
    
    Anfrage (JSON):
        {
            "task_id": "task_xxxx",         // Optional, task_id von generate
            "simulation_id": "sim_xxxx"     // Optional, Simulations-ID
        }
    
    Rückgabe:
        {
            "success": true,
            "data": {
                "task_id": "task_xxxx",
                "status": "processing|completed|failed",
                "progress": 45,
                "message": "..."
            }
        }
    """
    try:
        data = request.get_json() or {}
        
        task_id = data.get('task_id')
        simulation_id = data.get('simulation_id')
        
        # Wenn simulation_id angegeben, zuerst prüfen ob bereits ein fertiger Bericht vorhanden ist
        if simulation_id:
            existing_report = ReportManager.get_report_by_simulation(simulation_id)
            if existing_report and existing_report.status == ReportStatus.COMPLETED:
                return jsonify({
                    "success": True,
                    "data": {
                        "simulation_id": simulation_id,
                        "report_id": existing_report.report_id,
                        "status": "completed",
                        "progress": 100,
                        "message": "Bericht bereits generiert",
                        "already_completed": True
                    }
                })
        
        if not task_id:
            return jsonify({
                "success": False,
                "error": "Bitte geben Sie eine task_id oder simulation_id an"
            }), 400
        
        task_manager = TaskManager()
        task = task_manager.get_task(task_id)
        
        if not task:
            return jsonify({
                "success": False,
                "error": f"Aufgabe nicht gefunden: {task_id}"
            }), 404
        
        return jsonify({
            "success": True,
            "data": task.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Aufgabenstatus-Abfrage fehlgeschlagen: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============== Berichtsabruf-Schnittstellen ==============

@report_bp.route('/<report_id>', methods=['GET'])
def get_report(report_id: str):
    """
    Berichtsdetails abrufen
    
    Rückgabe:
        {
            "success": true,
            "data": {
                "report_id": "report_xxxx",
                "simulation_id": "sim_xxxx",
                "status": "completed",
                "outline": {...},
                "markdown_content": "...",
                "created_at": "...",
                "completed_at": "..."
            }
        }
    """
    try:
        report = ReportManager.get_report(report_id)
        
        if not report:
            return jsonify({
                "success": False,
                "error": f"Bericht nicht gefunden: {report_id}"
            }), 404
        
        return jsonify({
            "success": True,
            "data": report.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Abrufen des Berichts fehlgeschlagen: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/by-simulation/<simulation_id>', methods=['GET'])
def get_report_by_simulation(simulation_id: str):
    """
    Bericht nach Simulations-ID abrufen
    
    Rückgabe:
        {
            "success": true,
            "data": {
                "report_id": "report_xxxx",
                ...
            }
        }
    """
    try:
        report = ReportManager.get_report_by_simulation(simulation_id)
        
        if not report:
            return jsonify({
                "success": False,
                "error": f"Kein Bericht für diese Simulation: {simulation_id}",
                "has_report": False
            }), 404
        
        return jsonify({
            "success": True,
            "data": report.to_dict(),
            "has_report": True
        })
        
    except Exception as e:
        logger.error(f"Abrufen des Berichts fehlgeschlagen: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/list', methods=['GET'])
def list_reports():
    """
    Alle Berichte auflisten
    
    Query-Parameter:
        simulation_id: Nach Simulations-ID filtern (optional)
        limit: Rückgabelimit (Standard 50)
    
    Rückgabe:
        {
            "success": true,
            "data": [...],
            "count": 10
        }
    """
    try:
        simulation_id = request.args.get('simulation_id')
        limit = request.args.get('limit', 50, type=int)
        
        reports = ReportManager.list_reports(
            simulation_id=simulation_id,
            limit=limit
        )
        
        return jsonify({
            "success": True,
            "data": [r.to_dict() for r in reports],
            "count": len(reports)
        })
        
    except Exception as e:
        logger.error(f"Auflisten der Berichte fehlgeschlagen: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/<report_id>/download', methods=['GET'])
def download_report(report_id: str):
    """
    Bericht herunterladen (Markdown-Format)
    
    Gibt Markdown-Datei zurück
    """
    try:
        report = ReportManager.get_report(report_id)
        
        if not report:
            return jsonify({
                "success": False,
                "error": f"Bericht nicht gefunden: {report_id}"
            }), 404
        
        md_path = ReportManager._get_report_markdown_path(report_id)
        
        if not os.path.exists(md_path):
            # Wenn MD-Datei nicht existiert, temporäre Datei generieren
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write(report.markdown_content)
                temp_path = f.name
            
            return send_file(
                temp_path,
                as_attachment=True,
                download_name=f"{report_id}.md"
            )
        
        return send_file(
            md_path,
            as_attachment=True,
            download_name=f"{report_id}.md"
        )
        
    except Exception as e:
        logger.error(f"Herunterladen des Berichts fehlgeschlagen: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/<report_id>', methods=['DELETE'])
def delete_report(report_id: str):
    """Bericht löschen"""
    try:
        success = ReportManager.delete_report(report_id)
        
        if not success:
            return jsonify({
                "success": False,
                "error": f"Bericht nicht gefunden: {report_id}"
            }), 404
        
        return jsonify({
            "success": True,
            "message": f"Bericht gelöscht: {report_id}"
        })
        
    except Exception as e:
        logger.error(f"Löschen des Berichts fehlgeschlagen: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Report Agent Dialog-Schnittstellen ==============

@report_bp.route('/chat', methods=['POST'])
def chat_with_report_agent():
    """
    Mit Report Agent dialogisieren
    
    Der Report Agent kann in Dialogen eigenständig Abfrage-Tools aufrufen, um Fragen zu beantworten
    
    Anfrage (JSON):
        {
            "simulation_id": "sim_xxxx",        // Pflichtfeld, Simulations-ID
            "message": "Bitte erklären Sie den Meinungstrend",    // Pflichtfeld, Benutzernachricht
            "chat_history": [                   // Optional, Dialogverlauf
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."}
            ]
        }
    
    Rückgabe:
        {
            "success": true,
            "data": {
                "response": "Agent-Antwort...",
                "tool_calls": [Aufgerufene Tools],
                "sources": [Informationsquellen]
            }
        }
    """
    try:
        data = request.get_json() or {}
        
        simulation_id = data.get('simulation_id')
        message = data.get('message')
        chat_history = data.get('chat_history', [])
        
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "Bitte geben Sie eine simulation_id an"
            }), 400
        
        if not message:
            return jsonify({
                "success": False,
                "error": "Bitte geben Sie eine message an"
            }), 400
        
        # Simulations- und Projektinformationen abrufen
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)
        
        if not state:
            return jsonify({
                "success": False,
                "error": f"Simulation nicht gefunden: {simulation_id}"
            }), 404
        
        project = ProjectManager.get_project(state.project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": f"Projekt nicht gefunden: {state.project_id}"
            }), 404
        
        graph_id = state.graph_id or project.graph_id
        if not graph_id:
            return jsonify({
                "success": False,
                "error": "Graph-ID fehlt"
            }), 400
        
        simulation_requirement = project.simulation_requirement or ""
        
        # Agent erstellen und Dialog führen
        agent = ReportAgent(
            graph_id=graph_id,
            simulation_id=simulation_id,
            simulation_requirement=simulation_requirement
        )
        
        result = agent.chat(message=message, chat_history=chat_history)
        
        return jsonify({
            "success": True,
            "data": result
        })
        
    except Exception as e:
        logger.error(f"Dialog fehlgeschlagen: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Berichtsfortschritt und Abschnitt-Schnittstellen ==============

@report_bp.route('/<report_id>/progress', methods=['GET'])
def get_report_progress(report_id: str):
    """
    Berichtsgenerierungsfortschritt abrufen (Echtzeit)
    
    Rückgabe:
        {
            "success": true,
            "data": {
                "status": "generating",
                "progress": 45,
                "message": "Abschnitt wird generiert: Wichtige Erkenntnisse",
                "current_section": "Wichtige Erkenntnisse",
                "completed_sections": ["Zusammenfassung", "Simulationshintergrund"],
                "updated_at": "2025-12-09T..."
            }
        }
    """
    try:
        progress = ReportManager.get_progress(report_id)
        
        if not progress:
            return jsonify({
                "success": False,
                "error": f"Bericht nicht gefunden oder Fortschrittsinformationen nicht verfügbar: {report_id}"
            }), 404
        
        return jsonify({
            "success": True,
            "data": progress
        })
        
    except Exception as e:
        logger.error(f"Abrufen des Berichtsfortschritts fehlgeschlagen: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/<report_id>/sections', methods=['GET'])
def get_report_sections(report_id: str):
    """
    Liste der generierten Abschnitte abrufen (abschnittsweise Ausgabe)
    
    Das Frontend kann diese Schnittstelle abfragen, um generierte Abschnittsinhalte abzurufen, ohne auf den gesamten Bericht warten zu müssen
    
    Rückgabe:
        {
            "success": true,
            "data": {
                "report_id": "report_xxxx",
                "sections": [
                    {
                        "filename": "section_01.md",
                        "section_index": 1,
                        "content": "## 执行摘要\\n\\n..."
                    },
                    ...
                ],
                "total_sections": 3,
                "is_complete": false
            }
        }
    """
    try:
        sections = ReportManager.get_generated_sections(report_id)
        
        # Berichtsstatus abrufen
        report = ReportManager.get_report(report_id)
        is_complete = report is not None and report.status == ReportStatus.COMPLETED
        
        return jsonify({
            "success": True,
            "data": {
                "report_id": report_id,
                "sections": sections,
                "total_sections": len(sections),
                "is_complete": is_complete
            }
        })
        
    except Exception as e:
        logger.error(f"Abrufen der Abschnittsliste fehlgeschlagen: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/<report_id>/section/<int:section_index>', methods=['GET'])
def get_single_section(report_id: str, section_index: int):
    """
    Einzelnen Abschnitt abrufen
    
    Rückgabe:
        {
            "success": true,
            "data": {
                "filename": "section_01.md",
                "content": "## 执行摘要\\n\\n..."
            }
        }
    """
    try:
        section_path = ReportManager._get_section_path(report_id, section_index)
        
        if not os.path.exists(section_path):
            return jsonify({
                "success": False,
                "error": f"Abschnitt nicht gefunden: section_{section_index:02d}.md"
            }), 404
        
        with open(section_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            "success": True,
            "data": {
                "filename": f"section_{section_index:02d}.md",
                "section_index": section_index,
                "content": content
            }
        })
        
    except Exception as e:
        logger.error(f"Abrufen des Abschnittsinhalts fehlgeschlagen: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Berichtstatus-Prüfschnittstellen ============== 

@report_bp.route('/check/<simulation_id>', methods=['GET'])
def check_report_status(simulation_id: str):
    """
    Prüfen, ob die Simulation einen Bericht hat, und den Berichtsstatus ermitteln
    
    Wird verwendet, um im Frontend zu entscheiden, ob die Interview-Funktion freigeschaltet wird
    
    Rückgabe:
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "has_report": true,
                "report_status": "completed",
                "report_id": "report_xxxx",
                "interview_unlocked": true
            }
        }
    """
    try:
        report = ReportManager.get_report_by_simulation(simulation_id)
        
        has_report = report is not None
        report_status = report.status.value if report else None
        report_id = report.report_id if report else None
        
        # Interview wird nur freigeschaltet, wenn der Bericht abgeschlossen ist
        interview_unlocked = has_report and report.status == ReportStatus.COMPLETED
        
        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "has_report": has_report,
                "report_status": report_status,
                "report_id": report_id,
                "interview_unlocked": interview_unlocked
            }
        })
        
    except Exception as e:
        logger.error(f"Berichtstatus-Prüfung fehlgeschlagen: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Agent-Log-Schnittstellen ============== 

@report_bp.route('/<report_id>/agent-log', methods=['GET'])
def get_agent_log(report_id: str):
    """
    Detaillierte Ausführungslogs des Report Agents abrufen
    
    Echtzeit-Abruf jeder Aktion während der Berichtserstellung, einschließlich:
    - Berichtsstart, Planungsstart/-abschluss
    - Start jedes Abschnitts, Tool-Aufrufe, LLM-Antworten, Abschluss
    - Berichtsabschluss oder -fehler
    
    Query-Parameter:
        from_line: Zeilennummer, ab der gelesen werden soll (optional, Standard 0, für inkrementellen Abruf)
    
    Rückgabe:
        {
            "success": true,
            "data": {
                "logs": [
                    {
                        "timestamp": "2025-12-13T...",
                        "elapsed_seconds": 12.5,
                        "report_id": "report_xxxx",
                        "action": "tool_call",
                        "stage": "generating",
                        "section_title": "Zusammenfassung",
                        "section_index": 1,
                        "details": {
                            "tool_name": "insight_forge",
                            "parameters": {...},
                            ...
                        }
                    },
                    ...
                ],
                "total_lines": 25,
                "from_line": 0,
                "has_more": false
            }
        }
    """
    try:
        from_line = request.args.get('from_line', 0, type=int)
        
        log_data = ReportManager.get_agent_log(report_id, from_line=from_line)
        
        return jsonify({
            "success": True,
            "data": log_data
        })
        
    except Exception as e:
        logger.error(f"Abrufen des Agent-Logs fehlgeschlagen: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/<report_id>/agent-log/stream', methods=['GET'])
def stream_agent_log(report_id: str):
    """
    Vollständige Agent-Logs abrufen (einmaliger Abruf aller Logs)
    
    Rückgabe:
        {
            "success": true,
            "data": {
                "logs": [...],
                "count": 25
            }
        }
    """
    try:
        logs = ReportManager.get_agent_log_stream(report_id)
        
        return jsonify({
            "success": True,
            "data": {
                "logs": logs,
                "count": len(logs)
            }
        })
        
    except Exception as e:
        logger.error(f"获取Agent日志失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Konsolen-Log-Schnittstellen ============== 

@report_bp.route('/<report_id>/console-log', methods=['GET'])
def get_console_log(report_id: str):
    """
    Konsolenausgabe-Logs des Report Agents abrufen
    
    Echtzeit-Abruf der Konsolenausgabe während der Berichtserstellung (INFO, WARNING usw.),
    Dies unterscheidet sich von den strukturierten JSON-Logs der agent-log-Schnittstelle,
    es handelt sich um Logs im reinen Textformat im Konsolenstil.
    
    Query-Parameter:
        from_line: Zeilennummer, ab der gelesen werden soll (optional, Standard 0, für inkrementellen Abruf)
    
    Rückgabe:
        {
            "success": true,
            "data": {
                "logs": [
                    "[19:46:14] INFO: Suche abgeschlossen: 15 relevante Fakten gefunden",
                    "[19:46:14] INFO: Graph-Suche: graph_id=xxx, query=...",
                    ...
                ],
                "total_lines": 100,
                "from_line": 0,
                "has_more": false
            }
        }
    """
    try:
        from_line = request.args.get('from_line', 0, type=int)
        
        log_data = ReportManager.get_console_log(report_id, from_line=from_line)
        
        return jsonify({
            "success": True,
            "data": log_data
        })
        
    except Exception as e:
        logger.error(f"Abrufen der Konsolen-Logs fehlgeschlagen: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/<report_id>/console-log/stream', methods=['GET'])
def stream_console_log(report_id: str):
    """
    Vollständige Konsolen-Logs abrufen (einmaliger Abruf aller Logs)
    
    Rückgabe:
        {
            "success": true,
            "data": {
                "logs": [...],
                "count": 100
            }
        }
    """
    try:
        logs = ReportManager.get_console_log_stream(report_id)
        
        return jsonify({
            "success": True,
            "data": {
                "logs": logs,
                "count": len(logs)
            }
        })
        
    except Exception as e:
        logger.error(f"获取控制台日志失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Tool-Aufruf-Schnittstellen (zur Fehlersuche) ============== 

@report_bp.route('/tools/search', methods=['POST'])
def search_graph_tool():
    """
    Graph-Suchtool-Schnittstelle (zur Fehlersuche)
    
    Anfrage (JSON):
        {
            "graph_id": "mirofish_xxxx",
            "query": "Suchanfrage",
            "limit": 10
        }
    """
    try:
        data = request.get_json() or {}
        
        graph_id = data.get('graph_id')
        query = data.get('query')
        limit = data.get('limit', 10)
        
        if not graph_id or not query:
            return jsonify({
                "success": False,
                "error": "Bitte graph_id und query angeben"
            }), 400
        
        from ..services.zep_tools import ZepToolsService
        
        tools = ZepToolsService()
        result = tools.search_graph(
            graph_id=graph_id,
            query=query,
            limit=limit
        )
        
        return jsonify({
            "success": True,
            "data": result.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Graph-Suche fehlgeschlagen: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/tools/statistics', methods=['POST'])
def get_graph_statistics_tool():
    """
    Graph-Statistiktool-Schnittstelle (zur Fehlersuche)
    
    Anfrage (JSON):
        {
            "graph_id": "mirofish_xxxx"
        }
    """
    try:
        data = request.get_json() or {}
        
        graph_id = data.get('graph_id')
        
        if not graph_id:
            return jsonify({
                "success": False,
                "error": "Bitte graph_id angeben"
            }), 400
        
        from ..services.zep_tools import ZepToolsService
        
        tools = ZepToolsService()
        result = tools.get_graph_statistics(graph_id)
        
        return jsonify({
            "success": True,
            "data": result
        })
        
    except Exception as e:
        logger.error(f"Abrufen der Graph-Statistik fehlgeschlagen: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500
