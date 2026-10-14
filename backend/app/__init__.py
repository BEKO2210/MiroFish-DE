"""
MiroFish Backend - Flask-Anwendungsfabrik
"""

import hmac
import ipaddress
import os
import warnings
from urllib.parse import urlencode

# Unterdrückt Warnungen vom multiprocessing resource_tracker (aus Bibliotheken von Drittanbietern wie transformers)
# Muss vor allen anderen Importen gesetzt werden
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask, request, send_from_directory, jsonify, redirect
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Config
from .utils.logger import setup_logger, get_logger


def create_app(config_class=Config):
    """Flask-Anwendungsfabrik-Funktion"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    # Tailscale/Reverse-Proxies uebermitteln HTTPS per X-Forwarded-Proto. Das ist
    # insbesondere fuer das Secure-Flag des Token-Cookies relevant.
    # X-Forwarded-For wird bewusst NICHT vertraut (x_for=0): die Zugriffspruefung
    # nutzt die echte Peer-Adresse und laesst sich nicht per Header faelschen.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=0, x_proto=1, x_host=1)
    
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
        # compare_digest immer ausfuehren; Typ und Laenge des konfigurierten Tokens
        # werden nicht durch einen vorzeitigen normalen Stringvergleich verraten.
        candidate = given if isinstance(given, str) else ''
        return bool(api_token) and hmac.compare_digest(candidate.encode(), api_token.encode())

    @app.before_request
    def require_api_token():
        if not api_token or request.method == 'OPTIONS':
            return None
        if not request.path.startswith('/api/'):
            given = request.args.get('token', '')
            if given and token_ok(given):
                rest = [(k, v) for k, v in request.args.items(multi=True) if k != 'token']
                target = request.path + ('?' + urlencode(rest) if rest else '')
                resp = redirect(target)  # Token aus der Adresszeile entfernen
                resp.set_cookie('mirofish_token', given, max_age=365 * 24 * 3600, httponly=True,
                                samesite='Strict', secure=request.is_secure, path='/')
                return resp
            return None
        auth = request.headers.get('Authorization', '')
        given = auth[7:] if auth.startswith('Bearer ') else request.cookies.get('mirofish_token', '')
        if not token_ok(given):
            return jsonify({"success": False, "error": "API-Schlüssel fehlt oder ist falsch"}), 401
        return None

    # Same-origin braucht kein CORS. Fuer getrennte Entwicklungs-Frontends sind
    # ausschliesslich explizite Urspruenge erlaubt; '*' wird nie akzeptiert.
    if app.config.get('CORS_ORIGINS'):
        from flask_cors import CORS
        CORS(app, resources={r"/api/*": {"origins": list(app.config['CORS_ORIGINS'])}},
             supports_credentials=True)

    @app.before_request
    def validate_api_input():
        """Zentrale Absicherung auch fuer spaeter hinzugefuegte API-Routen."""
        if not request.path.startswith('/api/'):
            return None
        sensitive_system_endpoints = {
            'graph.system_models', 'graph.save_config', 'graph.test_llm',
            'system_models',
        }
        if not api_token and request.endpoint in sensitive_system_endpoints:
            try:
                # Echte Peer-Adresse; private/Docker-Bridge-Netze zaehlen als lokal.
                peer = ipaddress.ip_address(request.environ.get('REMOTE_ADDR') or '')
                is_local = peer.is_loopback or peer.is_private
            except ValueError:
                is_local = False
            if not is_local:
                return jsonify({
                    "success": False,
                    "error": "Systemeinstellungen sind ohne API_TOKEN nur lokal erreichbar",
                }), 403
        from .utils.security import ID_PATTERNS, InvalidIdentifier, validate_identifier, validate_known_ids
        try:
            for key, value in (request.view_args or {}).items():
                if key in ID_PATTERNS or key == 'pid':
                    validate_identifier(key, value)
            for key in ID_PATTERNS:
                if key in request.args:
                    validate_identifier(key, request.args.get(key), optional=True)
                if key in request.form:
                    validate_identifier(key, request.form.get(key), optional=True)
            if request.is_json:
                validate_known_ids(request.get_json(silent=True))
        except InvalidIdentifier:
            return jsonify({"success": False, "error": "Ungueltige Kennung"}), 400
        return None
    
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
            body = request.get_json(silent=True)
            keys = sorted(body) if isinstance(body, dict) else []
            logger.debug(f"JSON-Anfrage mit Feldern: {keys}")
    
    @app.after_request
    def log_response(response):
        logger = get_logger('mirofish.request')
        logger.debug(f"Antwort: {response.status_code}")
        # Von Route-Handlern gefangene Exceptions duerfen weder Tracebacks noch
        # lokale Pfade oder Provider-Schluessel an Clients zurueckgeben.
        if request.path.startswith('/api/') and response.status_code >= 500:
            from .utils.security import scrub_text
            payload = response.get_json(silent=True) if response.is_json else None
            message = payload.get('error') if isinstance(payload, dict) else None
            status_code = response.status_code
            if status_code in (502, 503, 504) and isinstance(message, str) and message:
                # Gezielt erzeugte Gateway-/Verfuegbarkeitsfehler behalten ihre bereinigte Meldung.
                response = jsonify({"success": False, "error": scrub_text(message)})
                response.status_code = status_code
            else:
                response = jsonify({"success": False, "error": "Interner Serverfehler"})
                response.status_code = 500
        elif request.path.startswith('/api/') and response.is_json:
            from .utils.security import sanitize_public_data
            payload = response.get_json(silent=True)
            sanitized = sanitize_public_data(payload)
            if sanitized != payload:
                status_code = response.status_code
                response = jsonify(sanitized)
                response.status_code = status_code
        return response

    @app.errorhandler(413)
    def request_too_large(_error):
        return jsonify({"success": False, "error": "Upload ist zu gross"}), 413

    @app.errorhandler(Exception)
    def unhandled_error(error):
        from werkzeug.exceptions import HTTPException
        if isinstance(error, HTTPException):
            return error
        logger.exception("Unbehandelter Fehler in der API")
        return jsonify({"success": False, "error": "Interner Serverfehler"}), 500
    
    # Blueprints registrieren
    from .api import graph_bp, simulation_bp, report_bp
    app.register_blueprint(graph_bp, url_prefix='/api/graph')
    # Kurze, sprechende System-URLs; die bisherigen /api/graph/system/*-Routen bleiben kompatibel.
    app.add_url_rule('/api/system/status', 'system_status', app.view_functions['graph.system_status'])
    app.add_url_rule('/api/system/models', 'system_models', app.view_functions['graph.system_models'])
    app.register_blueprint(simulation_bp, url_prefix='/api/simulation')
    app.register_blueprint(report_bp, url_prefix='/api/report')
    from .api.ensemble import ensemble_bp, mark_stale_ensembles
    app.register_blueprint(ensemble_bp, url_prefix='/api/ensemble')
    skip_sweep = bool(
        os.environ.get('MIROFISH_SKIP_STALE_SWEEP', '').strip().lower() in {'1', 'true', 'yes'}
        or getattr(config_class, 'SKIP_STALE_SWEEP', False)
    )
    if not skip_sweep:
        mark_stale_ensembles()
    from .api.pipeline import pipeline_bp, mark_stale_runs
    app.register_blueprint(pipeline_bp, url_prefix='/api/pipeline')
    if not skip_sweep:
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
