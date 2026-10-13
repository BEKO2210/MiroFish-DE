"""V1/V2: Methodik, Vorgabe-Abgleich, Manifest — ohne Sprachmodell."""
import json
import sqlite3
from pathlib import Path

import pytest

from app.config import Config
from app.services.report_validation import (
    MUSTERSTADT_BUERGERENTSCHEID_SATZ,
    MUSTERSTADT_MATERIAL_SATZ,
    append_methodology_to_markdown,
    build_manifest,
    build_methodology,
    content_stems,
    extract_claims,
    find_material_matches,
    ngram_overlap_ratio,
    write_events_jsonl,
    write_manifest,
)

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def upload(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(tmp_path))
    return tmp_path


def _make_sim(upload: Path, sim_id: str = "sim_aabbcc"):
    sim = upload / "simulations" / sim_id
    sim.mkdir(parents=True)
    config = {
        "time_config": {
            "total_simulation_hours": 24,
            "minutes_per_round": 60,
        },
        "event_config": {
            "initial_posts": [
                {"content": MUSTERSTADT_MATERIAL_SATZ, "poster_agent_id": 1}
            ]
        },
        "agent_configs": [
            {"agent_id": 0, "entity_type": "MediaOutlet"},
            {"agent_id": 1, "entity_type": "Person"},
            {"agent_id": 2, "entity_type": "Person"},
        ],
        "simulation_requirement": "Was passiert mit dem Bürgerentscheid?",
    }
    (sim / "simulation_config.json").write_text(
        json.dumps(config, ensure_ascii=False), encoding="utf-8"
    )
    (sim / "state.json").write_text(
        json.dumps(
            {
                "project_id": "proj_aabbcc",
                "simulation_requirement": config["simulation_requirement"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (sim / "run_state.json").write_text(
        json.dumps(
            {
                "total_simulation_hours": 24,
                "total_rounds": 24,
                "seed": 42,
                "temperature": 0.7,
                "started_at": "2026-10-13T09:00:00",
                "completed_at": "2026-10-13T09:20:00",
            }
        ),
        encoding="utf-8",
    )
    # Mini-Twitter-DB
    db = sim / "twitter_simulation.db"
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE post (user_id INTEGER, content TEXT, created_at TEXT)"
    )
    conn.execute(
        "INSERT INTO post VALUES (1, ?, '2026-10-13T09:01:00')",
        (MUSTERSTADT_MATERIAL_SATZ,),
    )
    conn.execute(
        "INSERT INTO post VALUES (2, 'Kurzer Kommentar zur Parkgebühr.', '2026-10-13T09:02:00')"
    )
    conn.execute("CREATE TABLE trace (user_id INTEGER, action TEXT, info TEXT, created_at TEXT)")
    conn.execute(
        "INSERT INTO trace VALUES (1, 'create_post', '{}', '2026-10-13T09:01:00')"
    )
    conn.execute(
        "INSERT INTO trace VALUES (2, 'create_post', '{}', '2026-10-13T09:02:00')"
    )
    conn.commit()
    conn.close()

    proj = upload / "projects" / "proj_aabbcc"
    proj.mkdir(parents=True)
    (proj / "extracted_text.txt").write_text(
        "Hintergrund Musterstadt.\n" + MUSTERSTADT_MATERIAL_SATZ + "\nEnde.",
        encoding="utf-8",
    )
    (proj / "files").mkdir()
    (proj / "files" / "quelle.md").write_text("# Quelle\nParkgebühren", encoding="utf-8")
    return sim_id, sim


def test_musterstadt_paraphrase_content_match():
    """Umformulierung: Berichtssatz vs. Material — muss Treffer sein."""
    claim_md = f'> "{MUSTERSTADT_BUERGERENTSCHEID_SATZ}"'
    matches = find_material_matches(
        claim_md,
        extracted_text=MUSTERSTADT_MATERIAL_SATZ,
        initial_posts=[{"content": MUSTERSTADT_MATERIAL_SATZ}],
    )
    assert len(matches) >= 1
    assert matches[0]["overlap"] >= 0.7
    assert matches[0]["source"] in ("Material", "Startbeitrag")
    assert matches[0].get("snippet")
    assert "ngram_overlap" in matches[0]
    # 5-Gramme allein würden hier oft scheitern — Zusatzinfo behalten
    assert ngram_overlap_ratio(
        MUSTERSTADT_BUERGERENTSCHEID_SATZ, MUSTERSTADT_MATERIAL_SATZ
    ) < 0.7


def test_neutral_no_match():
    """Neutrale Gegenprobe: kein inhaltlicher Bezug → kein Treffer."""
    claim_md = (
        '> "Die Forschung zu Quantencomputing erfordert Kühlung nahe dem '
        'absoluten Nullpunkt und spezielle Labore."'
    )
    matches = find_material_matches(
        claim_md,
        extracted_text=MUSTERSTADT_MATERIAL_SATZ,
        initial_posts=[{"content": MUSTERSTADT_MATERIAL_SATZ}],
    )
    assert matches == []


def test_musterstadt_fixture_files():
    """Echte Musterstadt-Dateien → mindestens ein Material-Treffer."""
    report = (FIXTURES / "report_musterstadt.md").read_text(encoding="utf-8")
    material = (FIXTURES / "musterstadt-eingabe.txt").read_text(encoding="utf-8")
    matches = find_material_matches(report, extracted_text=material)
    assert len(matches) >= 1
    assert any(
        "Oppositionsfraktion" in m["claim"] and m["overlap"] >= 0.7 for m in matches
    )
    # Duplikate der Kernaussage zusammengefasst
    opp = next(m for m in matches if "Oppositionsfraktion" in m["claim"])
    assert opp["count"] >= 3


def test_extract_claims_dedup_and_probability():
    md = (
        f'> "{MUSTERSTADT_BUERGERENTSCHEID_SATZ}"\n\n'
        f'> "{MUSTERSTADT_BUERGERENTSCHEID_SATZ}"\n\n'
        "Die Wahrscheinlichkeit eines Bürgerentscheids liegt bei 80 Prozent.\n"
    )
    claims = extract_claims(md)
    by_text = {c["claim"]: c["count"] for c in claims}
    assert by_text[MUSTERSTADT_BUERGERENTSCHEID_SATZ] == 2
    assert any("80" in c["claim"] or "Wahrscheinlichkeit" in c["claim"] for c in claims)
    assert len(content_stems(MUSTERSTADT_BUERGERENTSCHEID_SATZ)) >= 4


def test_methodology_from_sample_db(upload):
    sim_id, _ = _make_sim(upload)
    report_md = (
        "## Verlauf\n\n"
        f'> "{MUSTERSTADT_BUERGERENTSCHEID_SATZ}"\n\n'
        "In diesem Lauf blieb es bei der Ankündigung.\n"
    )
    data = build_methodology(sim_id, report_markdown=report_md, run_count=1)
    assert data["run_count"] == 1
    assert data["agent_count"] == 3
    assert data["simulation_hours"] == 24
    assert data["simulation_rounds"] == 24
    assert data["platform_activity"]["twitter"]["posts"] == 2
    assert data["platform_activity"]["twitter"]["actions"] == 2
    assert data["initial_posts_count"] == 1
    assert data["seed"] == 42
    assert "keine Wahrscheinlichkeit" in data["disclaimer"]
    assert any(
        MUSTERSTADT_BUERGERENTSCHEID_SATZ[:40] in m["claim"]
        for m in data["already_in_material"]
    )
    md = append_methodology_to_markdown("# Bericht\n\nInhalt\n", data)
    assert "## Methodik und Grenzen" in md
    assert "Stand bereits im Material" in md
    assert "Inhaltswort" in md or "Fundstelle" in md or "Material" in md


def test_manifest_content(upload):
    sim_id, sim = _make_sim(upload)
    manifest = build_manifest(
        sim_id, seed=42, temperature=0.7, started_at="2026-10-13T09:00:00"
    )
    assert manifest["seed"] == 42
    assert manifest["temperature"] == 0.7
    assert manifest["simulation_config_sha256"]
    assert manifest["question_sha256"]
    assert "extracted_text.txt" in manifest["document_sha256"]
    assert "quelle.md" in manifest["document_sha256"]
    assert "models" in manifest
    path = write_manifest(str(sim), manifest)
    assert Path(path).is_file()
    events_path = write_events_jsonl(str(sim))
    lines = Path(events_path).read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 2
    first = json.loads(lines[0])
    assert first["platform"] == "twitter"
    assert first["action_type"] == "CREATE_POST"
