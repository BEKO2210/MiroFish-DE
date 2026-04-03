"""
System-API-Routen
Status, Konfiguration und Tests
"""

from flask import jsonify, request

from . import graph_bp  # Wir verwenden den graph_bp für System-Endpunkte
from ..config import Config
from ..utils.llm_client import LLMClient


def mask_key(key):
    if not key or key == 'not-needed-for-local-llm' or key == 'lm-studio':
        return key
    if len(key) > 8:
        return f"{key[:4]}...****{key[-4:]}"
    return "***"

@graph_bp.route('/system/status', methods=['GET'])
def system_status():
    """System-Status abrufen"""
    llm_cfg = Config.get_llm_config()
    return jsonify({
        'success': True,
        'data': {
            'llm_provider': Config.LLM_PROVIDER,
            'llm_model': llm_cfg['model'],
            'llm_base_url': llm_cfg['base_url'],
            'is_local_llm': Config.is_local_llm(),
            'memory_provider': Config.MEMORY_PROVIDER,
            # Detaillierte Konfiguration für das Frontend
            'config': {
                'llm_provider': Config.LLM_PROVIDER,
                'llm_api_key': mask_key(Config.LLM_API_KEY),
                'llm_base_url': Config.LLM_BASE_URL,
                'llm_model_name': Config.LLM_MODEL_NAME,
                'local_llm_base_url': Config.LOCAL_LLM_BASE_URL,
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
