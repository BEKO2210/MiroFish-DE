"""
MiroFish Backend - Flask-Anwendungsfabrik
"""

import hmac
import os
import warnings

# Unterdrückt Warnungen vom multiprocessing resource_tracker (aus Bibliotheken von Drittanbietern wie transformers)
# Muss vor allen anderen Importen gesetzt werden
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask, request, send_from_directory, jsonify, redirect
from flask_cors import CORS

from .config import Config
from .utils.logger import setup_logger, get_logger


def create_app(config_class=Config):
    """Flask-Anwendungsfabrik-Funktion"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # JSON-Kodierung einstellen: Stellt sicher, dass Chinesisch direkt angezeigt wird (nicht im \uXXXX-Format)
    # Flask >= 2.3 verwendet app.json.ensure_ascii, ältere Versionen verwenden die JSON_ASASCII-Konfiguration
    if hasattr(app, 'json') and hasattr(app.json, 'ensure_ascii'):
        app.json.ensure_ascii = False
    
    # Protokollierung einrichten
    logger = setup_logger('mirofish')
    
    # Startinformationen nur im Reloader-Unterprozess ausgeben (verhindert doppelte Ausgabe im Debug-Modus)
    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    debug_mode = app.config.get('DEBUG', False)
    should_log_startup = not debug_mode or is_reloader_process
    
    if should_log_startup:
        logger.info("=" * 50)
        logger.info("MiroFish Backend wird gestartet...")
        logger.info("=" * 50)
    
    # Optionaler API-Schlüssel: ist API_TOKEN gesetzt, brauchen alle /api/*-Aufrufe den Header
    # Authorization: Bearer <token> (Agenten, Skripte) oder das Cookie, das der Browser einmalig über einen Link
    # /?token=<token> bekommt. So steht das Token nie in API-URLs oder Zugriffsprotokollen.
    # Ohne API_TOKEN bleibt die API offen (z. B. nur auf localhost oder im Tailscale-Netz).
    api_token = os.environ.get('API_TOKEN', '').strip()

    def token_ok(given):
        return bool(given) and hmac.compare_digest(given.encode(), api_token.encode())

    @app.before_request
    def require_api_token():
        if not api_token:
            return None
        if not request.path.startswith('/api/'):
            given = request.args.get('token', '')
            if given and token_ok(given):
                resp = redirect(request.path)  # Token aus der Adresszeile entfernen
                resp.set_cookie('mirofish_token', given, max_age=365 * 24 * 3600, httponly=True,
                                samesite='Strict', secure=request.is_secure)
                return resp
            return None
        auth = request.headers.get('Authorization', '')
        given = auth[7:] if auth.startswith('Bearer ') else request.cookies.get('mirofish_token', '')
        if not token_ok(given):
            return jsonify({"success": False, "error": "API-Schlüssel fehlt oder ist falsch"}), 401
        return None

    # CORS aktivieren
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Registriert Bereinigungsfunktionen für Simulationsprozesse (stellt sicher, dass alle Simulationsprozesse beim Server-Shutdown beendet werden)
    from .services.simulation_runner import SimulationRunner
    SimulationRunner.register_cleanup()
    if should_log_startup:
        logger.info("Bereinigungsfunktionen für Simulationsprozesse wurden registriert")
    
    # Anfrageprotokollierungs-Middleware
    @app.before_request
    def log_request():
        logger = get_logger('mirofish.request')
        logger.debug(f"Anfrage: {request.method} {request.path}")
        if request.content_type and 'json' in request.content_type:
            logger.debug(f"Anfragekörper: {request.get_json(silent=True)}")
    
    @app.after_request
    def log_response(response):
        logger = get_logger('mirofish.request')
        logger.debug(f"Antwort: {response.status_code}")
        return response
    
    # Blueprints registrieren
    from .api import graph_bp, simulation_bp, report_bp
    app.register_blueprint(graph_bp, url_prefix='/api/graph')
    app.register_blueprint(simulation_bp, url_prefix='/api/simulation')
    app.register_blueprint(report_bp, url_prefix='/api/report')
    from .api.pipeline import pipeline_bp, mark_stale_runs
    app.register_blueprint(pipeline_bp, url_prefix='/api/pipeline')
    mark_stale_runs()
    
    # Gesundheitscheck
    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'MiroFish Backend'}
    
    if should_log_startup:
        logger.info("MiroFish Backend-Start abgeschlossen")
    
    # Gebautes Frontend (frontend/dist) vom selben Ursprung ausliefern: ein Port, keine Host-Kopplung im Client
    dist = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'dist'))

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def frontend(path):
        if path.startswith('api/'):
            return jsonify({"success": False, "error": "Not Found"}), 404
        target = os.path.join(dist, path)
        if path and os.path.isfile(target):
            return send_from_directory(dist, path)
        if os.path.isfile(os.path.join(dist, 'index.html')):
            return send_from_directory(dist, 'index.html')
        return "Frontend nicht gebaut: cd frontend && npx vite build", 503

    return app
