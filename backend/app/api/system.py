"""
System-API-Routen
Status, Konfiguration und Tests
"""

from urllib.parse import urlparse

import requests
from flask import jsonify, request

from . import graph_bp  # Wir verwenden den graph_bp für System-Endpunkte
from ..config import Config
from ..utils.llm_client import LLMClient


def mask_key(key):
    if not key or key == 'not-needed-for-local-llm' or key == 'lm-studio':
        return key
    return "***"


def public_url(value):
    """URL ohne Benutzerinfo, Query oder Fragment fuer Statusantworten."""
    parsed = urlparse(value or '')
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        return ''
    host = f"[{parsed.hostname}]" if ':' in parsed.hostname else parsed.hostname
    if parsed.port:
        host += f":{parsed.port}"
    return parsed._replace(netloc=host, query='', fragment='').geturl()

def _ollama_root(base_url):
    """Ollama-Wurzeladresse aus der OpenAI-kompatiblen Adresse (…/v1) ableiten."""
    root = (base_url or '').rstrip('/')
    return root[:-3] if root.endswith('/v1') else root


def list_models(provider, base_url, api_key=None, timeout=4):
    """Installierte Modelle des Modellservers. Gibt (erreichbar, modelle) zurück; modelle = Liste von Dicts mit
    name, size_gb, params, quant, loaded. Ollama liefert Größe und den Ladezustand (/api/ps), andere Server nur Namen."""
    if urlparse(base_url or '').scheme not in ('http', 'https'):
        return False, []
    try:
        if provider == 'ollama':
            root = _ollama_root(base_url)
            tags = requests.get(f"{root}/api/tags", timeout=timeout, allow_redirects=False).json().get('models', [])
            try:
                loaded = {m.get('name') for m in requests.get(f"{root}/api/ps", timeout=timeout, allow_redirects=False).json().get('models', [])}
            except (requests.RequestException, ValueError):
                loaded = set()
            out = []
            for m in tags:
                d = m.get('details') or {}
                families = d.get('families') or [d.get('family') or '']
                if 'embed' in m.get('name', '') or any(f in ('bert', 'nomic-bert') for f in families if f):
                    continue  # Einbettungsmodelle können keinen Text erzeugen
                out.append({'name': m.get('name'), 'size_gb': round((m.get('size') or 0) / 1e9, 1),
                            'params': d.get('parameter_size') or '', 'quant': d.get('quantization_level') or '',
                            'loaded': m.get('name') in loaded})
            return True, sorted(out, key=lambda x: x['name'])
        headers = {'Authorization': f"Bearer {api_key}"} if api_key else {}
        data = requests.get(f"{base_url.rstrip('/')}/models", headers=headers, timeout=timeout, allow_redirects=False).json().get('data', [])
        return True, sorted(({'name': m.get('id'), 'size_gb': None, 'params': '', 'quant': '', 'loaded': False}
                             for m in data if m.get('id')), key=lambda x: x['name'])
    except (requests.RequestException, ValueError):
        return False, []


@graph_bp.route('/system/models', methods=['GET'])
def system_models():
    """Modelle auf dem Modellserver auflisten. Ohne Parameter: der gespeicherte Server; mit provider/base_url: ein
    gerade in den Einstellungen eingetragener Server (noch nicht gespeichert)."""
    llm_cfg = Config.get_llm_config()
    provider = request.args.get('provider') or Config.LLM_PROVIDER
    base_url = request.args.get('base_url') or llm_cfg['base_url']
    # Gespeicherten Schlüssel nur an den gespeicherten Server schicken, nie an eine frei eingegebene Adresse.
    # Lokale/private Adressen bleiben bewusst erlaubt: genau dort läuft Ollama.
    api_key = llm_cfg.get('api_key') if base_url.rstrip('/') == (llm_cfg['base_url'] or '').rstrip('/') else None
    reachable, models = list_models(provider, base_url, api_key)
    return jsonify({'success': True, 'data': {'reachable': reachable, 'models': models}})


@graph_bp.route('/system/status', methods=['GET'])
def system_status():
    """System-Status abrufen: konfigurierte Modelle, ob der Server erreichbar ist und was gerade geladen ist"""
    llm_cfg = Config.get_llm_config()
    reachable, models = list_models(Config.LLM_PROVIDER, llm_cfg['base_url'], llm_cfg.get('api_key'), timeout=2)
    names = {m['name'] for m in models}
    agent_model = Config.LLM_MODEL_NAME if Config.is_local_llm() else llm_cfg['model']
    return jsonify({
        'success': True,
        'data': {
            'llm_provider': Config.LLM_PROVIDER,
            'llm_model': llm_cfg['model'],
            'agent_model': agent_model,
            'llm_base_url': public_url(llm_cfg['base_url']),
            'is_local_llm': Config.is_local_llm(),
            'reachable': reachable,
            # Bei Servern ohne Modellliste (leere Antwort) nicht fälschlich "fehlt" melden
            'model_installed': (llm_cfg['model'] in names) if names else reachable,
            'loaded_models': [m['name'] for m in models if m.get('loaded')],
            'memory_provider': Config.MEMORY_PROVIDER,
            # Detaillierte Konfiguration für das Frontend
            'config': {
                'llm_provider': Config.LLM_PROVIDER,
                'llm_api_key': mask_key(Config.LLM_API_KEY),
                'llm_base_url': public_url(Config.LLM_BASE_URL),
                'llm_model_name': Config.LLM_MODEL_NAME,
                'local_llm_base_url': public_url(Config.LOCAL_LLM_BASE_URL),
                'local_llm_model_name': Config.LOCAL_LLM_MODEL_NAME,
                'local_llm_api_key': mask_key(Config.LOCAL_LLM_API_KEY),
                'zep_api_key': mask_key(Config.ZEP_API_KEY),
                'memory_provider': Config.MEMORY_PROVIDER
            }
        }
    })


@graph_bp.route('/system/config', methods=['POST'])
def save_config():
    """System-Konfiguration speichern"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Keine Daten empfangen'}), 400
            
        Config.save(data)
        return jsonify({
            'success': True,
            'message': 'Konfiguration erfolgreich gespeichert'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@graph_bp.route('/system/test-llm', methods=['POST'])
def test_llm():
    """LLM-Verbindung testen"""
    try:
        client = LLMClient()
        result = client.test_connection()
        
        if result['status'] == 'ok':
            return jsonify({
                'success': True,
                'data': {
                    'provider': result['provider'],
                    'model': result['model'],
                    'base_url': result['base_url'],
                    'response': result['response']
                },
                'message': 'LLM-Verbindung erfolgreich'
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'data': {
                    'provider': result['provider'],
                    'model': result['model'],
                    'base_url': result['base_url']
                }
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
