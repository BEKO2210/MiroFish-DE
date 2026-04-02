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
    
    # LLM-Provider: 'openai', 'lmstudio', 'ollama', 'local'
    # 'openai' = OpenAI API (oder kompatible APIs wie Azure, DashScope)
    # 'lmstudio' = LM Studio lokaler Server (OpenAI-kompatibel)
    # 'ollama' = Ollama lokaler Server (OpenAI-kompatibel)
    # 'local' = Generischer lokaler Endpunkt
    LLM_PROVIDER = os.environ.get('LLM_PROVIDER', 'openai').lower()
    
    # LLM-Konfiguration (einheitliches OpenAI-Format)
    LLM_API_KEY = os.environ.get('LLM_API_KEY')
    LLM_BASE_URL = os.environ.get('LLM_BASE_URL', 'https://api.openai.com/v1')
    LLM_MODEL_NAME = os.environ.get('LLM_MODEL_NAME', 'gpt-4o-mini')
    
    # Lokale LLM-Konfiguration (für LM Studio/Ollama)
    LOCAL_LLM_BASE_URL = os.environ.get('LOCAL_LLM_BASE_URL', 'http://localhost:1234/v1')
    LOCAL_LLM_MODEL_NAME = os.environ.get('LOCAL_LLM_MODEL_NAME', 'whiterabbitneo-2.5-qwen-2.5-coder-7b')
    LOCAL_LLM_API_KEY = os.environ.get('LOCAL_LLM_API_KEY', 'not-needed-for-local-llm')
    
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
    def get_llm_config(cls):
        """LLM-Konfiguration basierend auf Provider zurückgeben"""
        if cls.LLM_PROVIDER in ('lmstudio', 'ollama', 'local'):
            return {
                'api_key': cls.LOCAL_LLM_API_KEY,
                'base_url': cls.LOCAL_LLM_BASE_URL,
                'model': cls.LOCAL_LLM_MODEL_NAME
            }
        else:  # openai oder andere API-basierte Provider
            return {
                'api_key': cls.LLM_API_KEY,
                'base_url': cls.LLM_BASE_URL,
                'model': cls.LLM_MODEL_NAME
            }
    
    @classmethod
    def is_local_llm(cls):
        """Prüfen ob ein lokales LLM verwendet wird"""
        return cls.LLM_PROVIDER in ('lmstudio', 'ollama', 'local')
    
    @classmethod
    def save(cls, config_data: dict):
        """Konfiguration in .env-Datei speichern und aktuelle Klasse aktualisieren"""
        # Aktuelle .env laden oder neue erstellen
        env_path = project_root_env
        
        # Mapping von config_data keys zu .env keys
        mapping = {
            'llm_provider': 'LLM_PROVIDER',
            'llm_api_key': 'LLM_API_KEY',
            'llm_base_url': 'LLM_BASE_URL',
            'llm_model_name': 'LLM_MODEL_NAME',
            'local_llm_base_url': 'LOCAL_LLM_BASE_URL',
            'local_llm_model_name': 'LOCAL_LLM_MODEL_NAME',
            'local_llm_api_key': 'LOCAL_LLM_API_KEY',
            'zep_api_key': 'ZEP_API_KEY'
        }
        
        # Bestehende .env lesen
        lines = []
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        
        # Schlüssel aktualisieren oder hinzufügen
        updated_keys = set()
        new_lines = []
        
        for line in lines:
            line_strip = line.strip()
            if line_strip and not line_strip.startswith('#') and '=' in line_strip:
                key = line_strip.split('=')[0].strip()
                # Prüfen ob dieser Key in unserem Mapping ist
                config_key = next((k for k, v in mapping.items() if v == key), None)
                if config_key and config_key in config_data:
                    new_val = str(config_data[config_key])
                    # Maskierte Werte ignorieren
                    if new_val == '***' or '...****' in new_val:
                        new_lines.append(line)
                        updated_keys.add(key)
                        continue
                        
                    new_lines.append(f"{key}={new_val}\n")
                    updated_keys.add(key)
                    # Auch Klassenattribut aktualisieren
                    setattr(cls, key, new_val)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        # Neue Schlüssel hinzufügen
        for config_key, env_key in mapping.items():
            if env_key not in updated_keys and config_key in config_data:
                new_val = str(config_data[config_key])
                if new_val == '***' or '...****' in new_val:
                    continue
                
                # Auto-Korrektur für lokale URLs: /v1 anhängen falls vergessen
                if env_key == 'LOCAL_LLM_BASE_URL' and new_val.startswith('http') and not new_val.endswith('/v1'):
                    new_val = new_val.rstrip('/') + '/v1'
                    
                new_lines.append(f"{env_key}={new_val}\n")
                setattr(cls, env_key, new_val)
        
        # In .env schreiben
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
            
        # Umgebungsvariablen für aktuellen Prozess aktualisieren
        for config_key, env_key in mapping.items():
            if config_key in config_data:
                new_val = str(config_data[config_key])
                if new_val == '***' or '...****' in new_val:
                    continue
                
                # Auch hier Auto-Korrektur
                if env_key == 'LOCAL_LLM_BASE_URL' and new_val.startswith('http') and not new_val.endswith('/v1'):
                    new_val = new_val.rstrip('/') + '/v1'
                    
                os.environ[env_key] = new_val
        
        return True

    @classmethod
    def validate(cls):
        """Erforderliche Konfiguration validieren"""
        errors = []
        
        # Bei API-basierten Providern (nicht lokal) wird API-Key benötigt
        if not cls.is_local_llm() and not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY nicht konfiguriert")
        
        # ZEP ist immer erforderlich
        if not cls.ZEP_API_KEY:
            errors.append("ZEP_API_KEY nicht konfiguriert")
            
        # Warnung statt Fehler wenn Keys maskiert sind
        if cls.ZEP_API_KEY and '...****' in cls.ZEP_API_KEY:
            print("⚠️ ZEP_API_KEY ist maskiert. Bitte im Frontend aktualisieren.")
            
        return errors
