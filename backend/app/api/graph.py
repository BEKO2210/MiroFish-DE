"""
Graph-bezogene API-Routen
Verwendet Projekt-Kontext-Mechanismus, serverseitige Persistenz
"""

import os
import traceback
import threading
from flask import request, jsonify

from . import graph_bp
from ..config import Config
from ..services.ontology_generator import OntologyGenerator
from ..services.graph_builder import GraphBuilderService
from ..services.text_processor import TextProcessor
from ..utils.file_parser import FileParser
from ..utils.logger import get_logger
from ..models.task import TaskManager, TaskStatus
from ..models.project import ProjectManager, ProjectStatus

# Logger abrufen
logger = get_logger('mirofish.api')


def allowed_file(filename: str) -> bool:
    """Prüft ob Dateiendung erlaubt ist"""
    if not filename or '.' not in filename:
        return False
    ext = os.path.splitext(filename)[1].lower().lstrip('.')
    return ext in Config.ALLOWED_EXTENSIONS


# ============== Projektverwaltung-Schnittstellen ==============

@graph_bp.route('/project/<project_id>', methods=['GET'])
def get_project(project_id: str):
    """
    Projektdetails abrufen
    """
    project = ProjectManager.get_project(project_id)
    
    if not project:
        return jsonify({
            "success": False,
            "error": f"Projekt nicht gefunden: {project_id}"
        }), 404
    
    return jsonify({
        "success": True,
        "data": project.to_dict()
    })


@graph_bp.route('/project/list', methods=['GET'])
def list_projects():
    """
    Alle Projekte auflisten
    """
    limit = request.args.get('limit', 50, type=int)
    projects = ProjectManager.list_projects(limit=limit)
    
    return jsonify({
        "success": True,
        "data": [p.to_dict() for p in projects],
        "count": len(projects)
    })


@graph_bp.route('/project/<project_id>', methods=['DELETE'])
def delete_project(project_id: str):
    """
    Projekt löschen
    """
    success = ProjectManager.delete_project(project_id)
    
    if not success:
        return jsonify({
            "success": False,
            "error": f"Projekt nicht gefunden oder Löschung fehlgeschlagen: {project_id}"
        }), 404
    
    return jsonify({
        "success": True,
        "message": f"Projekt gelöscht: {project_id}"
    })


@graph_bp.route('/project/<project_id>/reset', methods=['POST'])
def reset_project(project_id: str):
    """
    Projektstatus zurücksetzen (zum Neuaufbau des Graphen)
    """
    project = ProjectManager.get_project(project_id)
    
    if not project:
        return jsonify({
            "success": False,
            "error": f"Projekt nicht gefunden: {project_id}"
        }), 404
    
    # Zurücksetzen auf Status "Ontologie generiert"
    if project.ontology:
        project.status = ProjectStatus.ONTOLOGY_GENERATED
    else:
        project.status = ProjectStatus.CREATED
    
    project.graph_id = None
    project.graph_build_task_id = None
    project.error = None
    ProjectManager.save_project(project)
    
    return jsonify({
        "success": True,
        "message": f"Projekt zurückgesetzt: {project_id}",
        "data": project.to_dict()
    })


# ============== Schnittstelle 1: Datei hochladen und Ontologie generieren ==============

@graph_bp.route('/ontology/generate', methods=['POST'])
def generate_ontology():
    """
    Schnittstelle 1: Dateien hochladen, Ontologie-Definition analysieren und generieren

    Anfragemethode: multipart/form-data

    Parameter:
        files: Hochgeladene Dateien (PDF/MD/TXT), mehrere möglich
        simulation_requirement: Simulationsanforderung (Pflichtfeld)
        project_name: Projektname (optional)
        additional_context: Zusätzliche Erläuterungen (optional)

    Rückgabe:
        {
            "success": true,
            "data": {
                "project_id": "proj_xxxx",
                "ontology": {
                    "entity_types": [...],
                    "edge_types": [...],
                    "analysis_summary": "..."
                },
                "files": [...],
                "total_text_length": 12345
            }
        }
    """
    try:
        logger.info("=== Ontologie-Definition wird generiert ===")

        # Parameter abrufen
        simulation_requirement = request.form.get('simulation_requirement', '')
        project_name = request.form.get('project_name', 'Unnamed Project')
        additional_context = request.form.get('additional_context', '')
        
        logger.debug(f"Projektname: {project_name}")
        logger.debug(f"Simulationsanforderung: {simulation_requirement[:100]}...")
        
        if not simulation_requirement:
            return jsonify({
                "success": False,
                "error": "Bitte geben Sie eine Simulationsanforderung an (simulation_requirement)"
            }), 400
        
        # Hochgeladene Dateien abrufen
        uploaded_files = request.files.getlist('files')
        if not uploaded_files or all(not f.filename for f in uploaded_files):
            return jsonify({
                "success": False,
                "error": "Bitte laden Sie mindestens eine Dokumentdatei hoch"
            }), 400
        
        # Projekt erstellen
        project = ProjectManager.create_project(name=project_name)
        project.simulation_requirement = simulation_requirement
        logger.info(f"Projekt erstellt: {project.project_id}")

        # Dateien speichern und Text extrahieren
        document_texts = []
        all_text = ""
        
        for file in uploaded_files:
            if file and file.filename and allowed_file(file.filename):
                # Datei im Projektverzeichnis speichern
                file_info = ProjectManager.save_file_to_project(
                    project.project_id, 
                    file, 
                    file.filename
                )
                project.files.append({
                    "filename": file_info["original_filename"],
                    "size": file_info["size"]
                })
                
                # Text extrahieren
                text = FileParser.extract_text(file_info["path"])
                text = TextProcessor.preprocess_text(text)
                document_texts.append(text)
                all_text += f"\n\n=== {file_info['original_filename']} ===\n{text}"
        
        if not document_texts:
            ProjectManager.delete_project(project.project_id)
            return jsonify({
                "success": False,
                "error": "Kein Dokument konnte verarbeitet werden, bitte prüfen Sie das Dateiformat"
            }), 400
        
        # Extrahierten Text speichern
        project.total_text_length = len(all_text)
        ProjectManager.save_extracted_text(project.project_id, all_text)
        logger.info(f"Textextraktion abgeschlossen, insgesamt {len(all_text)} Zeichen")

        # Ontologie generieren
        logger.info("LLM wird aufgerufen, um Ontologie-Definition zu generieren...")
        generator = OntologyGenerator()
        ontology = generator.generate(
            document_texts=document_texts,
            simulation_requirement=simulation_requirement,
            additional_context=additional_context if additional_context else None
        )
        
        # Ontologie im Projekt speichern
        entity_count = len(ontology.get("entity_types", []))
        edge_count = len(ontology.get("edge_types", []))
        logger.info(f"Ontologie-Generierung abgeschlossen: {entity_count} Entitätstypen, {edge_count} Beziehungstypen")
        
        project.ontology = {
            "entity_types": ontology.get("entity_types", []),
            "edge_types": ontology.get("edge_types", [])
        }
        project.analysis_summary = ontology.get("analysis_summary", "")
        project.status = ProjectStatus.ONTOLOGY_GENERATED
        ProjectManager.save_project(project)
        logger.info(f"=== Ontologie-Generierung abgeschlossen === Projekt-ID: {project.project_id}")
        
        return jsonify({
            "success": True,
            "data": {
                "project_id": project.project_id,
                "project_name": project.name,
                "ontology": project.ontology,
                "analysis_summary": project.analysis_summary,
                "files": project.files,
                "total_text_length": project.total_text_length
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Schnittstelle 2: Graph aufbauen ==============

@graph_bp.route('/build', methods=['POST'])
def build_graph():
    """
    Schnittstelle 2: Graph anhand der project_id aufbauen

    Anfrage (JSON):
        {
            "project_id": "proj_xxxx",  // Pflichtfeld, von Schnittstelle 1
            "graph_name": "Graphname",  // Optional
            "chunk_size": 500,          // Optional, Standard 500
            "chunk_overlap": 50         // Optional, Standard 50
        }

    Rückgabe:
        {
            "success": true,
            "data": {
                "project_id": "proj_xxxx",
                "task_id": "task_xxxx",
                "message": "Graph-Aufbau-Aufgabe gestartet"
            }
        }
    """
    try:
        logger.info("=== Graph-Aufbau wird gestartet ===")

        # Konfiguration prüfen
        errors = []
        if not Config.ZEP_API_KEY:
            errors.append("ZEP_API_KEY nicht konfiguriert")
        if errors:
            logger.error(f"Konfigurationsfehler: {errors}")
            return jsonify({
                "success": False,
                "error": "Konfigurationsfehler: " + "; ".join(errors)
            }), 500
        
        # Anfrage auswerten
        data = request.get_json() or {}
        project_id = data.get('project_id')
        logger.debug(f"Anfrageparameter: project_id={project_id}")
        
        if not project_id:
            return jsonify({
                "success": False,
                "error": "Bitte geben Sie eine project_id an"
            }), 400
        
        # Projekt abrufen
        project = ProjectManager.get_project(project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": f"Projekt nicht gefunden: {project_id}"
            }), 404
        
        # Projektstatus prüfen
        force = data.get('force', False)  # Neuaufbau erzwingen
        
        if project.status == ProjectStatus.CREATED:
            return jsonify({
                "success": False,
                "error": "Projekt hat noch keine Ontologie, bitte zuerst /ontology/generate aufrufen"
            }), 400
        
        if project.status == ProjectStatus.GRAPH_BUILDING and not force:
            return jsonify({
                "success": False,
                "error": "Graph wird gerade aufgebaut, bitte nicht erneut einreichen. Für erzwungenen Neuaufbau bitte force: true hinzufügen",
                "task_id": project.graph_build_task_id
            }), 400
        
        # Bei erzwungenem Neuaufbau Status zurücksetzen
        if force and project.status in [ProjectStatus.GRAPH_BUILDING, ProjectStatus.FAILED, ProjectStatus.GRAPH_COMPLETED]:
            project.status = ProjectStatus.ONTOLOGY_GENERATED
            project.graph_id = None
            project.graph_build_task_id = None
            project.error = None
        
        # Konfiguration abrufen
        graph_name = data.get('graph_name', project.name or 'MiroFish Graph')
        chunk_size = data.get('chunk_size', project.chunk_size or Config.DEFAULT_CHUNK_SIZE)
        chunk_overlap = data.get('chunk_overlap', project.chunk_overlap or Config.DEFAULT_CHUNK_OVERLAP)
        
        # Projektkonfiguration aktualisieren
        project.chunk_size = chunk_size
        project.chunk_overlap = chunk_overlap
        
        # Extrahierten Text abrufen
        text = ProjectManager.get_extracted_text(project_id)
        if not text:
            return jsonify({
                "success": False,
                "error": "Kein extrahierter Textinhalt gefunden"
            }), 400
        
        # Ontologie abrufen
        ontology = project.ontology
        if not ontology:
            return jsonify({
                "success": False,
                "error": "Keine Ontologie-Definition gefunden"
            }), 400
        
        # Asynchrone Aufgabe erstellen
        task_manager = TaskManager()
        task_id = task_manager.create_task(f"Graph aufbauen: {graph_name}")
        logger.info(f"Graph-Aufbau-Aufgabe erstellt: task_id={task_id}, project_id={project_id}")
        
        # Projektstatus aktualisieren
        project.status = ProjectStatus.GRAPH_BUILDING
        project.graph_build_task_id = task_id
        ProjectManager.save_project(project)
        
        # Hintergrundaufgabe starten
        def build_task():
            build_logger = get_logger('mirofish.build')
            try:
                build_logger.info(f"[{task_id}] Graph-Aufbau wird gestartet...")
                task_manager.update_task(
                    task_id, 
                    status=TaskStatus.PROCESSING,
                    message="Graph-Aufbau-Dienst wird initialisiert..."
                )
                
                # Graph-Aufbau-Dienst erstellen
                builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)
                
                # Chunking
                task_manager.update_task(
                    task_id,
                    message="Text wird aufgeteilt...",
                    progress=5
                )
                chunks = TextProcessor.split_text(
                    text, 
                    chunk_size=chunk_size, 
                    overlap=chunk_overlap
                )
                total_chunks = len(chunks)
                
                # Graph erstellen
                task_manager.update_task(
                    task_id,
                    message="Zep-Graph wird erstellt...",
                    progress=10
                )
                graph_id = builder.create_graph(name=graph_name)
                
                # graph_id des Projekts aktualisieren
                project.graph_id = graph_id
                ProjectManager.save_project(project)
                
                # Ontologie festlegen
                task_manager.update_task(
                    task_id,
                    message="Ontologie-Definition wird festgelegt...",
                    progress=15
                )
                builder.set_ontology(graph_id, ontology)
                
                # Text hinzufügen (progress_callback Signatur ist (msg, progress_ratio))
                def add_progress_callback(msg, progress_ratio):
                    progress = 15 + int(progress_ratio * 40)  # 15% - 55%
                    task_manager.update_task(
                        task_id,
                        message=msg,
                        progress=progress
                    )
                
                task_manager.update_task(
                    task_id,
                    message=f"Beginne mit dem Hinzufügen von {total_chunks} Textblöcken...",
                    progress=15
                )
                
                episode_uuids = builder.add_text_batches(
                    graph_id, 
                    chunks,
                    batch_size=3,
                    progress_callback=add_progress_callback
                )
                
                # Auf Abschluss der Zep-Verarbeitung warten (Status jeder Episode prüfen)
                task_manager.update_task(
                    task_id,
                    message="Warte auf Zep-Datenverarbeitung...",
                    progress=55
                )
                
                def wait_progress_callback(msg, progress_ratio):
                    progress = 55 + int(progress_ratio * 35)  # 55% - 90%
                    task_manager.update_task(
                        task_id,
                        message=msg,
                        progress=progress
                    )
                
                builder._wait_for_episodes(episode_uuids, wait_progress_callback)
                
                # Graphdaten abrufen
                task_manager.update_task(
                    task_id,
                    message="Graphdaten werden abgerufen...",
                    progress=95
                )
                graph_data = builder.get_graph_data(graph_id)
                
                # Projektstatus aktualisieren
                project.status = ProjectStatus.GRAPH_COMPLETED
                ProjectManager.save_project(project)
                
                node_count = graph_data.get("node_count", 0)
                edge_count = graph_data.get("edge_count", 0)
                build_logger.info(f"[{task_id}] Graph-Aufbau abgeschlossen: graph_id={graph_id}, Knoten={node_count}, Kanten={edge_count}")
                
                # Abgeschlossen
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    message="Graph-Aufbau abgeschlossen",
                    progress=100,
                    result={
                        "project_id": project_id,
                        "graph_id": graph_id,
                        "node_count": node_count,
                        "edge_count": edge_count,
                        "chunk_count": total_chunks
                    }
                )
                
            except Exception as e:
                # Projektstatus auf fehlgeschlagen setzen
                build_logger.error(f"[{task_id}] Graph-Aufbau fehlgeschlagen: {str(e)}")
                build_logger.debug(traceback.format_exc())
                
                project.status = ProjectStatus.FAILED
                project.error = str(e)
                ProjectManager.save_project(project)
                
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    message=f"Aufbau fehlgeschlagen: {str(e)}",
                    error=traceback.format_exc()
                )
        
        # Hintergrund-Thread starten
        thread = threading.Thread(target=build_task, daemon=True)
        thread.start()
        
        return jsonify({
            "success": True,
            "data": {
                "project_id": project_id,
                "task_id": task_id,
                "message": "Graph-Aufbau-Aufgabe gestartet, Fortschritt über /task/{task_id} abfragen"
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Aufgabenabfrage-Schnittstellen ==============

@graph_bp.route('/task/<task_id>', methods=['GET'])
def get_task(task_id: str):
    """
    Aufgabenstatus abfragen
    """
    task = TaskManager().get_task(task_id)
    
    if not task:
        return jsonify({
            "success": False,
            "error": f"Aufgabe nicht gefunden: {task_id}"
        }), 404
    
    return jsonify({
        "success": True,
        "data": task.to_dict()
    })


@graph_bp.route('/tasks', methods=['GET'])
def list_tasks():
    """
    Alle Aufgaben auflisten
    """
    tasks = TaskManager().list_tasks()
    
    return jsonify({
        "success": True,
        "data": [t.to_dict() for t in tasks],
        "count": len(tasks)
    })


# ============== Graphdaten-Schnittstellen ==============

@graph_bp.route('/data/<graph_id>', methods=['GET'])
def get_graph_data(graph_id: str):
    """
    Graphdaten abrufen (Knoten und Kanten)
    """
    try:
        if not Config.ZEP_API_KEY:
            return jsonify({
                "success": False,
                "error": "ZEP_API_KEY nicht konfiguriert"
            }), 500
        
        builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)
        graph_data = builder.get_graph_data(graph_id)
        
        return jsonify({
            "success": True,
            "data": graph_data
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@graph_bp.route('/delete/<graph_id>', methods=['DELETE'])
def delete_graph(graph_id: str):
    """
    Zep-Graph löschen
    """
    try:
        if not Config.ZEP_API_KEY:
            return jsonify({
                "success": False,
                "error": "ZEP_API_KEY nicht konfiguriert"
            }), 500
        
        builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)
        builder.delete_graph(graph_id)
        
        return jsonify({
            "success": True,
            "message": f"Graph gelöscht: {graph_id}"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500
