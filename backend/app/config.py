"""
Konfigurationsverwaltung
Konfiguration einheitlich aus der .env-Datei im Projektwurzelverzeichnis laden
"""

import os
from dotenv import load_dotenv

# .env-Datei des Projektwurzelverzeichnisses laden
# Pfad: MiroFish/.env (relativ zu backend/app/config.py)
project_root_env = os.path.join(os.path.dirname(__file__), '../../.env')

if os.path.exists(project_root_env):
    load_dotenv(project_root_env, override=True)
else:
    # Wenn keine .env im Wurzelverzeichnis, Umgebungsvariablen laden (für Produktionsumgebung)
    load_dotenv(override=True)


class Config:
    """Flask-Konfigurationsklasse"""
    
    # Flask-Konfiguration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'mirofish-secret-key')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # JSON-Konfiguration - ASCII-Escaping deaktivieren, Unicode direkt anzeigen (statt \uXXXX-Format)
    JSON_AS_ASCII = False
    
    # LLM-Konfiguration (einheitliches OpenAI-Format)
    LLM_API_KEY = os.environ.get('LLM_API_KEY')
    LLM_BASE_URL = os.environ.get('LLM_BASE_URL', 'https://api.openai.com/v1')
    LLM_MODEL_NAME = os.environ.get('LLM_MODEL_NAME', 'gpt-4o-mini')
    
    # Zep-Konfiguration
    ZEP_API_KEY = os.environ.get('ZEP_API_KEY')
    
    # Datei-Upload-Konfiguration
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'md', 'txt', 'markdown'}
    
    # Textverarbeitungskonfiguration
    DEFAULT_CHUNK_SIZE = 500  # Standard-Chunk-Größe
    DEFAULT_CHUNK_OVERLAP = 50  # Standard-Überlappungsgröße
    
    # OASIS-Simulationskonfiguration
    OASIS_DEFAULT_MAX_ROUNDS = int(os.environ.get('OASIS_DEFAULT_MAX_ROUNDS', '10'))
    OASIS_SIMULATION_DATA_DIR = os.path.join(os.path.dirname(__file__), '../uploads/simulations')
    
    # OASIS-Plattform verfügbare Aktionskonfiguration
    OASIS_TWITTER_ACTIONS = [
        'CREATE_POST', 'LIKE_POST', 'REPOST', 'FOLLOW', 'DO_NOTHING', 'QUOTE_POST'
    ]
    OASIS_REDDIT_ACTIONS = [
        'LIKE_POST', 'DISLIKE_POST', 'CREATE_POST', 'CREATE_COMMENT',
        'LIKE_COMMENT', 'DISLIKE_COMMENT', 'SEARCH_POSTS', 'SEARCH_USER',
        'TREND', 'REFRESH', 'DO_NOTHING', 'FOLLOW', 'MUTE'
    ]
    
    # Report Agent-Konfiguration
    REPORT_AGENT_MAX_TOOL_CALLS = int(os.environ.get('REPORT_AGENT_MAX_TOOL_CALLS', '5'))
    REPORT_AGENT_MAX_REFLECTION_ROUNDS = int(os.environ.get('REPORT_AGENT_MAX_REFLECTION_ROUNDS', '2'))
    REPORT_AGENT_TEMPERATURE = float(os.environ.get('REPORT_AGENT_TEMPERATURE', '0.5'))
    
    @classmethod
    def validate(cls):
        """Erforderliche Konfiguration validieren"""
        errors = []
        if not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY nicht konfiguriert")
        if not cls.ZEP_API_KEY:
            errors.append("ZEP_API_KEY nicht konfiguriert")
        return errors

