import os
import subprocess
import sys
from pathlib import Path

import pytest

from app.utils.security import (
    InvalidIdentifier,
    safe_child,
    safe_display_name,
    safe_upload_name,
    sanitize_public_data,
    validate_identifier,
    validate_known_ids,
)
from app.config import Config


@pytest.mark.parametrize(
    ("kind", "valid"),
    [
        ("project_id", "proj_0123456789ab"),
        ("simulation_id", "sim_0123456789ab"),
        ("report_id", "report_0123456789ab"),
        ("ensemble_id", "ens_0123456789ab"),
        ("run_id", "run_0123456789ab"),
        ("graph_id", "mirofish_0123456789abcdef"),
        ("graph_id", "01234567-89ab-cdef-0123-456789abcdef"),
    ],
)
def test_identifier_patterns_reject_traversal_and_absolute_paths(kind, valid):
    assert validate_identifier(kind, valid) == valid
    for malicious in ("../" + valid, valid + "/..", "/tmp/x", "..", valid + "\\x"):
        with pytest.raises(InvalidIdentifier):
            validate_identifier(kind, malicious)


def test_nested_body_ids_are_validated():
    validate_known_ids({"simulation_id": "sim_0123456789ab", "nested": []})
    with pytest.raises(InvalidIdentifier):
        validate_known_ids({"nested": [{"report_id": "../../etc/passwd"}]})


def test_safe_child_rejects_escape_and_symlink(tmp_path):
    assert safe_child(tmp_path, "sim_0123456789ab").parent == tmp_path.resolve()
    with pytest.raises(InvalidIdentifier):
        safe_child(tmp_path, "../outside")
    outside = tmp_path.parent / "outside"
    outside.mkdir(exist_ok=True)
    (tmp_path / "link").symlink_to(outside, target_is_directory=True)
    with pytest.raises(InvalidIdentifier):
        safe_child(tmp_path, "link")


def test_upload_name_is_normalized_and_extension_limited():
    assert safe_upload_name("Notizen 1.MD", {"md", "txt"}) == ("Notizen_1.MD", "md")
    assert safe_upload_name("报告.pdf", {"pdf"}) == ("dokument.pdf", "pdf")
    assert safe_upload_name("Übersicht.txt", {"txt"}) == ("Uebersicht.txt", "txt")
    assert safe_display_name("../x/报告 Übersicht.pdf") == "报告 Übersicht.pdf"
    with pytest.raises(InvalidIdentifier):
        safe_upload_name("payload.py", {"md", "txt"})
    with pytest.raises(InvalidIdentifier):
        safe_upload_name("ohne-endung", {"md", "txt"})


def test_entity_uuid_accepts_obsidian_ids_but_not_traversal():
    for ok in ("123e4567-e89b-12d3-a456-426614174000", "0123456789abcdef", "Notiz-1.md"):
        assert validate_identifier("entity_uuid", ok) == ok
    for bad in ("..", "a/b", "x" * 129, "a b"):
        with pytest.raises(InvalidIdentifier):
            validate_identifier("entity_uuid", bad)


def test_sanitizer_keeps_content_and_masks_error_secrets():
    content = {
        "report": "Risk-Management, Task-Force, token_budget_exceeded, bearer of bad news, /opt/data",
        "posts": ["Ask-Anything", "Desk-Research", "key_performance_indicators"],
    }
    assert sanitize_public_data(content) == content
    err = sanitize_public_data({
        "error": "sk-abcdefghijklmnopqrstuvwx und Bearer abcdefghijklmnopqrstuvwxyz0123 in /home/u/x.py",
    })["error"]
    assert "sk-abc" not in err and "Bearer abc" not in err and "/home/u" not in err


def test_public_error_data_redacts_tracebacks_paths_and_keys():
    data = sanitize_public_data({
        "error": "Fehler in /home/user/app.py mit sk-abcdefghijklmnopqrstu",
        "traceback": "Traceback (most recent call last): ...",
        "nested": [{"message": "ZEP_API_KEY=supersecretvalue"}],
    })
    assert "traceback" not in data
    serialized = repr(data)
    assert "/home/user" not in serialized
    assert "sk-abcdefghijklmnopqrstu" not in serialized
    assert "supersecretvalue" not in serialized


def test_debug_is_forced_off_and_config_rejects_env_injection():
    assert Config.DEBUG is False
    with pytest.raises(ValueError):
        Config.save({"llm_model_name": "ok\nAPI_TOKEN=eingeschleust"})
    with pytest.raises(ValueError):
        Config.save({"llm_base_url": "file:///etc/passwd"})


@pytest.mark.parametrize("mode", ["token", "open"])
def test_real_app_enforces_auth_cookie_ids_cors_and_sanitized_errors(tmp_path, mode):
    """Startet die echte Factory mit kleinen Dummy-Blueprints, ohne einen echten Lauf."""
    pytest.importorskip("flask")
    backend = Path(__file__).resolve().parents[1]
    script = r'''
import os, sys, types
from flask import Blueprint, jsonify
MODE = os.environ['T_MODE']
os.environ.pop('API_TOKEN', None)
if MODE == 'token':
    os.environ['API_TOKEN'] = 'very-secret-token'
sys.path.insert(0, os.getcwd())
from app import create_app
from app.config import Config

api = types.ModuleType('app.api')
api.__path__ = []
api.graph_bp = Blueprint('graph', __name__)
api.simulation_bp = Blueprint('simulation', __name__)
api.report_bp = Blueprint('report', __name__)
@api.graph_bp.get('/system/status')
def system_status(): return jsonify(success=True)
@api.graph_bp.get('/system/models')
def system_models(): return jsonify(success=True)
@api.simulation_bp.get('/<simulation_id>')
def simulation(simulation_id): return jsonify(success=True)
@api.report_bp.get('/boom')
def boom(): return jsonify(success=False, error='/secret/path', traceback='stack'), 500
@api.report_bp.get('/down')
def down(): return jsonify(success=False, error='LLM nicht erreichbar /home/u/x sk-abcdefghijklmnopqrstuvwx'), 503
@api.report_bp.get('/text')
def text(): return jsonify(success=True, data={'t': 'Risk-Management /opt/x token_budget_exceeded'})
@api.report_bp.post('/echo')
def echo(): return jsonify(success=True)
sys.modules['app.api'] = api

ensemble = types.ModuleType('app.api.ensemble')
ensemble.ensemble_bp = Blueprint('ensemble', __name__)
@ensemble.ensemble_bp.post('/<ensemble_id>/reclassify')
def reclassify(ensemble_id): return jsonify(success=True)
ensemble.mark_stale_ensembles = lambda: 0
sys.modules['app.api.ensemble'] = ensemble
pipeline = types.ModuleType('app.api.pipeline')
pipeline.pipeline_bp = Blueprint('pipeline', __name__)
pipeline.mark_stale_runs = lambda: 0
sys.modules['app.api.pipeline'] = pipeline
services = types.ModuleType('app.services'); services.__path__ = []
runner = types.ModuleType('app.services.simulation_runner')
class SimulationRunner:
    @staticmethod
    def register_cleanup(): pass
runner.SimulationRunner = SimulationRunner
sys.modules['app.services'] = services
sys.modules['app.services.simulation_runner'] = runner

class TestConfig(Config):
    TESTING = True
    CORS_ORIGINS = ()
    MAX_CONTENT_LENGTH = 128
app = create_app(TestConfig)
c = app.test_client()
if MODE == 'open':
    ep = '/api/system/models'
    docker = {'REMOTE_ADDR': '172.18.0.1'}
    assert c.get(ep, environ_overrides={'REMOTE_ADDR': '127.0.0.1'}).status_code == 200
    assert c.get(ep, environ_overrides=docker).status_code == 200
    assert c.get(ep, environ_overrides={'REMOTE_ADDR': '93.184.216.34'},
                 headers={'X-Forwarded-For': '127.0.0.1'}).status_code == 403
    assert c.get(ep, environ_overrides=docker, headers={'X-Forwarded-For': '8.8.8.8'}).status_code == 200
    sys.exit(0)
assert c.get('/api/system/status').status_code == 401
h = {'Authorization': 'Bearer very-secret-token'}
assert c.get('/api/system/status', headers=h).status_code == 200
assert c.post('/api/ensemble/ens_0123456789ab/reclassify', headers=h).status_code == 200
assert c.get('/api/simulation/../../etc/passwd', headers=h).status_code in (400, 404)
assert c.get('/api/system/status?simulation_id=../bad', headers=h).status_code == 400
r = c.get('/api/report/boom', headers={**h, 'Origin': 'https://evil.example'})
assert r.status_code == 500 and r.json == {'success': False, 'error': 'Interner Serverfehler'}
assert 'Access-Control-Allow-Origin' not in r.headers
r = c.post('/api/report/echo', headers={**h, 'Content-Type': 'application/json'},
           data='{"message":"' + ('x' * 512) + '"}')
assert r.status_code == 413 and r.json['error'] == 'Upload ist zu gross'
assert c.options('/api/system/status').status_code != 401
r = c.get('/api/report/down', headers=h)
assert r.status_code == 503 and r.json['error'].startswith('LLM nicht erreichbar')
assert '/home/u' not in r.json['error'] and 'sk-abc' not in r.json['error']
assert c.get('/api/report/text', headers=h).json['data']['t'] == 'Risk-Management /opt/x token_budget_exceeded'
r = c.get('/some/page?a=1&token=very-secret-token&b=x')
assert r.status_code == 302 and r.headers['Location'] == '/some/page?a=1&b=x'
r = c.get('/?token=very-secret-token', headers={'X-Forwarded-Proto': 'https'})
cookie = r.headers['Set-Cookie']
assert 'HttpOnly' in cookie and 'SameSite=Strict' in cookie and 'Secure' in cookie
'''
    result = subprocess.run(
        [sys.executable, "-c", script], cwd=backend, text=True,
        capture_output=True, env={**os.environ, "PYTHONPATH": str(backend), "T_MODE": mode}, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_script_api_client_sends_api_token_from_environment(monkeypatch):
    from scripts.validate_case import ApiClient

    monkeypatch.setenv("API_TOKEN", "abc123")
    assert ApiClient("http://x").session.headers["Authorization"] == "Bearer abc123"
    monkeypatch.delenv("API_TOKEN")
    assert "Authorization" not in ApiClient("http://x").session.headers
