"""
System-API-Routen
Status, Konfiguration und Tests
"""

from flask import jsonify

from . import graph_bp  # Wir verwenden den graph_bp für System-Endpunkte
from ..config import Config
from ..utils.llm_client import LLMClient


@graph_bp.route('/system/status', methods=['GET'])
def system_status():
    """System-Status abrufen"""
    return jsonify({
        'success': True,
        'data': {
            'llm_provider': Config.LLM_PROVIDER,
            'llm_model': Config.get_llm_config()['model'],
            'llm_base_url': Config.get_llm_config()['base_url'],
            'is_local_llm': Config.is_local_llm()
        }
    })


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
