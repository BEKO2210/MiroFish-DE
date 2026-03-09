"""
MiroFish Backend Startpunkt
"""

import os
import sys

# Windows-Konsolen-Encoding-Problem lösen: UTF-8 vor allen Imports setzen
if sys.platform == 'win32':
    # Umgebungsvariablen setzen um UTF-8 sicherzustellen
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    # Standardausgabeströme auf UTF-8 umkonfigurieren
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Projektwurzelverzeichnis zum Pfad hinzufügen
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.config import Config


def main():
    """Hauptfunktion"""
    # Konfiguration validieren
    errors = Config.validate()
    if errors:
        print("Konfigurationsfehler:")
        for err in errors:
            print(f"  - {err}")
        print("\nBitte prüfen Sie die Konfiguration in der .env-Datei")
        sys.exit(1)
    
    # Anwendung erstellen
    app = create_app()
    
    # Ausführungskonfiguration abrufen
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5001))
    debug = Config.DEBUG
    
    # Dienst starten
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    main()

