"""
Projekt-Kontextverwaltung
Zur serverseitigen Persistierung des Projektstatus, um zu vermeiden, dass der Frontend zwischen Schnittstellen große Datenmengen übertragen muss
"""

import os
import json
import uuid
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field, asdict
from ..config import Config


class ProjectStatus(str, Enum):
    """Projektstatus"""
    CREATED = "created"              # Gerade erstellt, Dateien wurden hochgeladen
    ONTOLOGY_GENERATED = "ontology_generated"  # Ontologie wurde generiert
    GRAPH_BUILDING = "graph_building"    # Graph wird erstellt
    GRAPH_COMPLETED = "graph_completed"  # Graph-Erstellung abgeschlossen
    FAILED = "failed"                # Fehlgeschlagen


@dataclass
class Project:
    """Projektdatenmodell"""
    project_id: str
    name: str
    status: ProjectStatus
    created_at: str
    updated_at: str
    
    # Dateiinformationen
    files: List[Dict[str, str]] = field(default_factory=list)  # [{filename, path, size}]
    total_text_length: int = 0
    
    # Ontologieinformationen (wird nach Generierung durch Schnittstelle 1 gefüllt)
    ontology: Optional[Dict[str, Any]] = None
    analysis_summary: Optional[str] = None
    
    # Graphinformationen (wird nach Abschluss von Schnittstelle 2 gefüllt)
    graph_id: Optional[str] = None
    graph_build_task_id: Optional[str] = None
    
    # Konfiguration
    simulation_requirement: Optional[str] = None
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    # Fehlerinformationen
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert in ein Dictionary"""
        return {
            "project_id": self.project_id,
            "name": self.name,
            "status": self.status.value if isinstance(self.status, ProjectStatus) else self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "files": self.files,
            "total_text_length": self.total_text_length,
            "ontology": self.ontology,
            "analysis_summary": self.analysis_summary,
            "graph_id": self.graph_id,
            "graph_build_task_id": self.graph_build_task_id,
            "simulation_requirement": self.simulation_requirement,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Erstellt aus einem Dictionary"""
        status = data.get('status', 'created')
        if isinstance(status, str):
            status = ProjectStatus(status)
        
        return cls(
            project_id=data['project_id'],
            name=data.get('name', 'Unnamed Project'),
            status=status,
            created_at=data.get('created_at', ''),
            updated_at=data.get('updated_at', ''),
            files=data.get('files', []),
            total_text_length=data.get('total_text_length', 0),
            ontology=data.get('ontology'),
            analysis_summary=data.get('analysis_summary'),
            graph_id=data.get('graph_id'),
            graph_build_task_id=data.get('graph_build_task_id'),
            simulation_requirement=data.get('simulation_requirement'),
            chunk_size=data.get('chunk_size', 500),
            chunk_overlap=data.get('chunk_overlap', 50),
            error=data.get('error')
        )


class ProjectManager:
    """Projekt-Manager - Verantwortlich für die persistente Speicherung und Abfrage von Projekten"""
    
    # Stammverzeichnis für die Projektspeicherung
    PROJECTS_DIR = os.path.join(Config.UPLOAD_FOLDER, 'projects')
    
    @classmethod
    def _ensure_projects_dir(cls):
        """Stellt sicher, dass das Projektverzeichnis existiert"""
        os.makedirs(cls.PROJECTS_DIR, exist_ok=True)
    
    @classmethod
    def _get_project_dir(cls, project_id: str) -> str:
        """Gibt den Pfad zum Projektverzeichnis zurück"""
        return os.path.join(cls.PROJECTS_DIR, project_id)
    
    @classmethod
    def _get_project_meta_path(cls, project_id: str) -> str:
        """Gibt den Pfad zur Projekt-Metadatendatei zurück"""
        return os.path.join(cls._get_project_dir(project_id), 'project.json')
    
    @classmethod
    def _get_project_files_dir(cls, project_id: str) -> str:
        """Gibt das Verzeichnis für die Projektspeicherung zurück"""
        return os.path.join(cls._get_project_dir(project_id), 'files')
    
    @classmethod
    def _get_project_text_path(cls, project_id: str) -> str:
        """Gibt den Speicherpfad für den extrahierten Text des Projekts zurück"""
        return os.path.join(cls._get_project_dir(project_id), 'extracted_text.txt')
    
    @classmethod
    def create_project(cls, name: str = "Unnamed Project") -> Project:
        """
        Erstellt ein neues Projekt
        
        Args:
            name: Projektname
            
        Returns:
            Neu erstelltes Project-Objekt
        """
        cls._ensure_projects_dir()
        
        project_id = f"proj_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        
        project = Project(
            project_id=project_id,
            name=name,
            status=ProjectStatus.CREATED,
            created_at=now,
            updated_at=now
        )
        
        # Erstellt die Projektverzeichnisstruktur
        project_dir = cls._get_project_dir(project_id)
        files_dir = cls._get_project_files_dir(project_id)
        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(files_dir, exist_ok=True)
        
        # Speichert die Projektmetadaten
        cls.save_project(project)
        
        return project
    
    @classmethod
    def save_project(cls, project: Project) -> None:
        """Speichert die Projektmetadaten"""
        project.updated_at = datetime.now().isoformat()
        meta_path = cls._get_project_meta_path(project.project_id)
        
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(project.to_dict(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def get_project(cls, project_id: str) -> Optional[Project]:
        """
        Ruft ein Projekt ab
        
        Args:
            project_id: Projekt-ID
            
        Returns:
            Project-Objekt, gibt None zurück wenn nicht vorhanden
        """
        meta_path = cls._get_project_meta_path(project_id)
        
        if not os.path.exists(meta_path):
            return None
        
        with open(meta_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return Project.from_dict(data)
    
    @classmethod
    def list_projects(cls, limit: int = 50) -> List[Project]:
        """
        Listet alle Projekte auf
        
        Args:
            limit: Begrenzung der Anzahl der zurückgegebenen Projekte
            
        Returns:
            Projektliste, sortiert nach Erstellungszeit in absteigender Reihenfolge
        """
        cls._ensure_projects_dir()
        
        projects = []
        for project_id in os.listdir(cls.PROJECTS_DIR):
            project = cls.get_project(project_id)
            if project:
                projects.append(project)
        
        # Sortiert nach Erstellungszeit in absteigender Reihenfolge
        projects.sort(key=lambda p: p.created_at, reverse=True)
        
        return projects[:limit]
    
    @classmethod
    def delete_project(cls, project_id: str) -> bool:
        """
        Löscht ein Projekt und alle seine Dateien
        
        Args:
            project_id: Projekt-ID
            
        Returns:
            Ob das Löschen erfolgreich war
        """
        project_dir = cls._get_project_dir(project_id)
        
        if not os.path.exists(project_dir):
            return False
        
        shutil.rmtree(project_dir)
        return True
    
    @classmethod
    def save_file_to_project(cls, project_id: str, file_storage, original_filename: str) -> Dict[str, str]:
        """
        Speichert eine hochgeladene Datei im Projektverzeichnis
        
        Args:
            project_id: Projekt-ID
            file_storage: Flask FileStorage-Objekt
            original_filename: Ursprünglicher Dateiname
            
        Returns:
            Dateiinformations-Dictionary {filename, path, size}
        """
        files_dir = cls._get_project_files_dir(project_id)
        os.makedirs(files_dir, exist_ok=True)
        
        # Generiert einen sicheren Dateinamen
        ext = os.path.splitext(original_filename)[1].lower()
        safe_filename = f"{uuid.uuid4().hex[:8]}{ext}"
        file_path = os.path.join(files_dir, safe_filename)
        
        # Speichert die Datei
        file_storage.save(file_path)
        
        # Ruft die Dateigröße ab
        file_size = os.path.getsize(file_path)
        
        return {
            "original_filename": original_filename,
            "saved_filename": safe_filename,
            "path": file_path,
            "size": file_size
        }
    
    @classmethod
    def save_extracted_text(cls, project_id: str, text: str) -> None:
        """Speichert den extrahierten Text"""
        text_path = cls._get_project_text_path(project_id)
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(text)
    
    @classmethod
    def get_extracted_text(cls, project_id: str) -> Optional[str]:
        """Ruft den extrahierten Text ab"""
        text_path = cls._get_project_text_path(project_id)
        
        if not os.path.exists(text_path):
            return None
        
        with open(text_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @classmethod
    def get_project_files(cls, project_id: str) -> List[str]:
        """Ruft alle Dateipfade des Projekts ab"""
        files_dir = cls._get_project_files_dir(project_id)
        
        if not os.path.exists(files_dir):
            return []
        
        return [
            os.path.join(files_dir, f) 
            for f in os.listdir(files_dir) 
            if os.path.isfile(os.path.join(files_dir, f))
        ]
