import json
import sqlite3

from app.services.ensemble import EnsembleService
from scripts.rater_benchmark import run_benchmark


class FakeLLM:
    def __init__(self, model):
        self.model = model
        self.calls = []

    def chat_json(self, messages, **kwargs):
        self.calls.append((messages, kwargs))
        text = messages[-1]["content"]
        # Das zweite Modell verfehlt absichtlich nur den klaren Erzählungsbeleg.
        yes = "KLARER BELEG" in text and not (
            self.model == "kandidat" and "Erzählung:" in text
        )
        return {
            "results": [{
                "outcome_id": "c1",
                "yes": yes,
                "post_ids": ["twitter:1"] if "Beiträge:" in text and yes else [],
                "snippet": "KLARER BELEG" if yes else "",
            }]
        }


def _simulation_db(path):
    connection = sqlite3.connect(path)
    connection.executescript("""
        CREATE TABLE user (user_id INTEGER, agent_id INTEGER, name TEXT, user_name TEXT);
        CREATE TABLE post (post_id INTEGER, user_id INTEGER, content TEXT);
        INSERT INTO user VALUES (1, 1, 'Akteur', 'akteur');
        INSERT INTO post VALUES (1, 1, 'KLARER BELEG');
    """)
    connection.commit()
    connection.close()


def test_benchmark_uses_production_classifiers_and_writes_both_formats(tmp_path):
    ensemble = tmp_path / "ensemble"
    references = tmp_path / "references"
    output = tmp_path / "output"
    (ensemble / "baseline" / "run_1").mkdir(parents=True)
    (ensemble / "null_document" / "run_1").mkdir(parents=True)
    references.mkdir()
    state = {
        "base_seed": 40,
        "variants": [{"key": "baseline"}, {"key": "null_document"}],
        "checklist": [{
            "id": "c1", "text_de": "Stellungnahme", "definition": "Ablehnung",
            "polarity": "presence", "kind": "event",
        }],
    }
    (ensemble / "ensemble.json").write_text(json.dumps(state), encoding="utf-8")
    (ensemble / "baseline" / "run_1" / "simulation_config.json").write_text(
        '{"event_config":{"initial_posts":[]}}', encoding="utf-8"
    )
    _simulation_db(ensemble / "baseline" / "run_1" / "twitter_simulation.db")
    (ensemble / "null_document" / "run_1" / "narrative.txt").write_text(
        "Hier steht ein KLARER BELEG.", encoding="utf-8"
    )
    for arm in ("baseline", "null_document"):
        (references / f"ref_{arm}_1.json").write_text(
            '{"c1":{"yes":true}}', encoding="utf-8"
        )

    clients = {}

    def factory(*, model=None, **_kwargs):
        clients[model] = FakeLLM(model)
        return clients[model]

    service = EnsembleService(root=tmp_path / "service", llm_factory=factory)
    ticks = iter((1.0, 3.0, 10.0, 13.5))
    report = run_benchmark(
        ensemble, references, ["gemma", "kandidat"], output,
        mode="paare", service=service, clock=lambda: next(ticks),
    )

    assert report["models"][0]["metrics"]["overall"]["agreement"] == 1.0
    assert report["models"][0]["metrics"]["simulation"]["pairs"] == 1
    assert report["models"][0]["metrics"]["narrative"]["pairs"] == 1
    assert report["models"][0]["metrics"]["c1"]["pairs"] == 2
    assert report["models"][1]["metrics"]["overall"]["agreement"] == 0.5
    assert report["pairs"][0]["primary"] == "gemma"
    assert report["pairs"][0]["secondary"] == "kandidat"
    assert report["pairs"][0]["agreement"] == 0.5
    assert report["models"][1]["duration_seconds"] == 3.5
    assert (output / "rater_benchmark.json").is_file()
    markdown = (output / "rater_benchmark.md").read_text(encoding="utf-8")
    assert "Primärfrage c1" in markdown
    assert "| gemma | kandidat |" in markdown
    assert all(len(client.calls) == 2 for client in clients.values())


def test_invalid_reference_boolean_is_rejected(tmp_path):
    ensemble = tmp_path / "ensemble"
    references = tmp_path / "references"
    run_dir = ensemble / "null_document" / "run_1"
    run_dir.mkdir(parents=True)
    references.mkdir()
    (ensemble / "ensemble.json").write_text(json.dumps({
        "variants": [{"key": "null_document"}],
        "checklist": [{"id": "c1"}],
    }), encoding="utf-8")
    (run_dir / "narrative.txt").write_text("Text", encoding="utf-8")
    (references / "ref_null_document_1.json").write_text(
        '{"c1":{"yes":"ja"}}', encoding="utf-8"
    )

    service = EnsembleService(root=tmp_path / "service", llm_factory=lambda **_: FakeLLM("x"))
    try:
        run_benchmark(ensemble, references, ["x"], tmp_path / "out", service=service)
    except ValueError as error:
        assert "true|false" in str(error)
    else:
        raise AssertionError("Ungültige Referenz wurde akzeptiert")
