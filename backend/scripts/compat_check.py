#!/usr/bin/env python3
"""Read-only compatibility check for persisted MiroFish upload data.

The source tree is checksummed, copied to a temporary directory and never
mounted directly into the application.  Only endpoints used to display
existing data are exercised; model discovery is replaced with a local stub.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPOSITORY_DIR = BACKEND_DIR.parent


@dataclass
class Check:
    endpoint: str
    object_id: str
    status: int | None
    error: str = ""
    objects: int = 1

    @property
    def passed(self) -> bool:
        return self.status is not None and 200 <= self.status < 300 and not self.error


def tree_digest(root: Path) -> str:
    """Hash paths, file contents and symlink targets without following links."""
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root).as_posix().encode()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        if path.is_symlink():
            target = path.readlink().as_posix().encode()
            digest.update(b"L" + len(target).to_bytes(8, "big") + target)
        elif path.is_file():
            digest.update(b"F")
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
        elif path.is_dir():
            digest.update(b"D")
    return digest.hexdigest()


def directory_ids(root: Path, directory: str, prefix: str) -> list[str]:
    base = root / directory
    if not base.is_dir():
        return []
    return sorted(
        path.name
        for path in base.iterdir()
        if path.is_dir() and path.name.startswith(prefix)
    )


def pipeline_ids(root: Path) -> list[str]:
    base = root / "pipelines"
    if not base.is_dir():
        return []
    return sorted(path.stem for path in base.glob("run_*.json") if path.is_file())


def _safe_error(response: Any) -> str:
    """Return a bounded API error only, never persisted response content."""
    try:
        payload = response.get_json(silent=True)
    except Exception:
        payload = None
    if isinstance(payload, dict):
        error = payload.get("error") or payload.get("message")
        if isinstance(error, str):
            return error.replace("\n", " ")[:300]
        if payload.get("success") is False:
            return "Antwort enthält success=false"
    return ""


def run_checks(upload_root: Path) -> list[Check]:
    # Config must be redirected before importing modules whose storage roots are
    # class attributes initialized at import time.
    sys.path.insert(0, str(BACKEND_DIR))
    from app import create_app
    from app.config import Config

    Config.TESTING = True
    Config.SKIP_STALE_SWEEP = True
    os.environ["MIROFISH_SKIP_STALE_SWEEP"] = "1"
    Config.UPLOAD_FOLDER = str(upload_root)
    Config.OASIS_SIMULATION_DATA_DIR = str(upload_root / "simulations")
    Config.LLM_PROVIDER = "ollama"
    Config.LOCAL_LLM_BASE_URL = "http://compat.invalid/v1"
    Config.LOCAL_LLM_MODEL_NAME = "compat-model"

    projects = directory_ids(upload_root, "projects", "proj_")
    simulations = directory_ids(upload_root, "simulations", "sim_")
    reports = directory_ids(upload_root, "reports", "report_")
    ensembles = directory_ids(upload_root, "ensembles", "ens_")
    pipelines = pipeline_ids(upload_root)

    fake_models = (
        True,
        [{"name": "compat-model", "size_gb": 0.0, "params": "test", "quant": "", "loaded": True}],
    )
    # pipeline.py performs a startup orphan sweep. It is useful in production,
    # but a compatibility read must preserve every copied object for checking.
    with patch("app.services.cleanup.sweep_orphans", return_value=[]), patch(
        "app.api.system.list_models", return_value=fake_models
    ):
        app = create_app(Config)
        client = app.test_client()

        calls: list[
            tuple[str, str, Callable[[], Any], Callable[[Any], str] | None, int]
        ] = []

        def add(
            endpoint: str,
            object_id: str,
            call: Callable[[], Any],
            validator: Callable[[Any], str] | None = None,
            objects: int = 1,
        ) -> None:
            calls.append((endpoint, object_id, call, validator, objects))

        def validates_count(expected: int) -> Callable[[Any], str]:
            def validate(response: Any) -> str:
                payload = response.get_json(silent=True) or {}
                data = payload.get("data")
                actual = len(data) if isinstance(data, list) else payload.get("count")
                if actual == expected:
                    return ""
                return f"Liste enthält {actual!r} statt {expected} Objekten"

            return validate

        add(
            "GET /api/graph/project/list", "Projekte",
            lambda: client.get("/api/graph/project/list"),
            validates_count(len(projects)), len(projects),
        )
        for project_id in projects:
            add(
                "GET /api/graph/project/{id}", project_id,
                lambda project_id=project_id: client.get(
                    f"/api/graph/project/{project_id}"
                ),
            )

        add(
            "GET /api/simulation/list", "Simulationen",
            lambda: client.get("/api/simulation/list"),
            validates_count(len(simulations)), len(simulations),
        )
        add(
            "GET /api/simulation/history", "Simulationen",
            lambda: client.get("/api/simulation/history?limit=1000"),
            validates_count(len(simulations)), len(simulations),
        )
        simulation_gets = (
            ("GET /api/simulation/{id}", ""),
            ("GET /api/simulation/{id}/profiles", "/profiles"),
            ("GET /api/simulation/{id}/profiles/realtime", "/profiles/realtime"),
            ("GET /api/simulation/{id}/config", "/config"),
            ("GET /api/simulation/{id}/config/realtime", "/config/realtime"),
            ("GET /api/simulation/{id}/run-status", "/run-status"),
            ("GET /api/simulation/{id}/run-status/detail", "/run-status/detail"),
            ("GET /api/simulation/{id}/posts", "/posts?limit=50&offset=0"),
            ("GET /api/simulation/{id}/timeline", "/timeline?start_round=0"),
            ("GET /api/simulation/{id}/agent-stats", "/agent-stats"),
            ("GET /api/simulation/{id}/actions", "/actions?limit=100&offset=0"),
        )
        for simulation_id in simulations:
            for label, suffix in simulation_gets:
                add(
                    label, simulation_id,
                    lambda simulation_id=simulation_id, suffix=suffix: client.get(
                        f"/api/simulation/{simulation_id}{suffix}"
                    ),
                )
            add(
                "POST /api/simulation/prepare/status (nur lesend)", simulation_id,
                lambda simulation_id=simulation_id: client.post(
                    "/api/simulation/prepare/status",
                    json={"simulation_id": simulation_id},
                ),
            )
            add(
                "POST /api/simulation/env-status (nur lesend)", simulation_id,
                lambda simulation_id=simulation_id: client.post(
                    "/api/simulation/env-status",
                    json={"simulation_id": simulation_id},
                ),
            )
            add("GET /api/report/by-simulation/{id}", simulation_id,
                lambda simulation_id=simulation_id: client.get(f"/api/report/by-simulation/{simulation_id}"))
            add("GET /api/report/check/{id}", simulation_id,
                lambda simulation_id=simulation_id: client.get(f"/api/report/check/{simulation_id}"))

        add(
            "GET /api/report/list", "Berichte",
            lambda: client.get("/api/report/list?limit=1000"),
            validates_count(len(reports)), len(reports),
        )
        for report_id in reports:
            add("GET /api/report/{id} (inkl. Methodik)", report_id,
                lambda report_id=report_id: client.get(f"/api/report/{report_id}"),
                lambda response: "Methodik fehlt" if not (
                    ((response.get_json(silent=True) or {}).get("data") or {}).get(
                        "methodology"
                    )
                ) else "")
            add("GET /api/report/generate/status", report_id,
                lambda report_id=report_id: client.get(
                    "/api/report/generate/status",
                    query_string={"report_id": report_id},
                ))
            add("GET /api/report/{id}/agent-log", report_id,
                lambda report_id=report_id: client.get(f"/api/report/{report_id}/agent-log?from_line=0"))
            add("GET /api/report/{id}/console-log", report_id,
                lambda report_id=report_id: client.get(f"/api/report/{report_id}/console-log?from_line=0"))

        add(
            "GET /api/ensemble/list", "Mehrfachläufe",
            lambda: client.get("/api/ensemble/list"),
            validates_count(len(ensembles)), len(ensembles),
        )
        for ensemble_id in ensembles:
            def validate_markdown(response: Any) -> str:
                payload = response.get_json(silent=True) or {}
                state = payload.get("data")
                if not isinstance(state, dict) or state.get("status") != "completed":
                    return ""
                try:
                    from app.services.ensemble import ensemble_markdown
                    markdown = ensemble_markdown(state)
                except Exception as error:
                    return f"Markdown nicht erzeugbar: {type(error).__name__}: {error}"
                return "" if markdown.strip() else "Markdown ist leer"

            add("GET /api/ensemble/{id} + Markdown", ensemble_id,
                lambda ensemble_id=ensemble_id: client.get(f"/api/ensemble/{ensemble_id}"), validate_markdown)

        add(
            "GET /api/pipeline/list", "Pipelines",
            lambda: client.get("/api/pipeline/list"),
            validates_count(len(pipelines)), len(pipelines),
        )
        for pipeline_id in pipelines:
            add("GET /api/pipeline/{id}", pipeline_id,
                lambda pipeline_id=pipeline_id: client.get(f"/api/pipeline/{pipeline_id}"))

        add(
            "GET /api/system/status (Ollama gemockt)", "System",
            lambda: client.get("/api/system/status"),
        )
        add(
            "GET /api/system/models (Ollama gemockt)", "System",
            lambda: client.get("/api/system/models"),
        )

        results: list[Check] = []
        for endpoint, object_id, call, validator, objects in calls:
            try:
                response = call()
                error = _safe_error(response) if not 200 <= response.status_code < 300 else ""
                if not error and validator is not None:
                    error = validator(response)
                results.append(Check(endpoint, object_id, response.status_code, error, objects))
            except Exception as error:  # keep checking every remaining object
                results.append(Check(endpoint, object_id, None, f"{type(error).__name__}: {error}", objects))
        return results


def print_summary(results: list[Check]) -> None:
    grouped: dict[str, list[Check]] = {}
    for result in results:
        grouped.setdefault(result.endpoint, []).append(result)
    print("Endpunkt\tObjekte\tErgebnis")
    for endpoint, checks in grouped.items():
        failures = [check for check in checks if not check.passed]
        outcome = "OK" if not failures else f"FEHLER {len(failures)}/{len(checks)}"
        print(f"{endpoint}\t{sum(check.objects for check in checks)}\t{outcome}")
    failures = [result for result in results if not result.passed]
    if failures:
        print("\nFehler:")
        for failure in failures:
            status = failure.status if failure.status is not None else "EXCEPTION"
            print(f"- {failure.endpoint} [{failure.object_id}]: {status} {failure.error}".rstrip())
    print(f"\nGesamt: {len(results) - len(failures)}/{len(results)} erfolgreich")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "uploads",
        nargs="?",
        type=Path,
        default=REPOSITORY_DIR / ".compatdata" / "uploads",
        help="Quellverzeichnis der Upload-Daten (Standard: .compatdata/uploads)",
    )
    args = parser.parse_args()
    source = args.uploads.resolve()
    if not source.is_dir():
        parser.error(f"Upload-Verzeichnis nicht gefunden: {source}")

    before = tree_digest(source)
    with tempfile.TemporaryDirectory(prefix="mirofish-compat-") as temporary:
        copied_uploads = Path(temporary) / "uploads"
        shutil.copytree(source, copied_uploads, symlinks=True)
        results = run_checks(copied_uploads)
    after = tree_digest(source)

    print_summary(results)
    print(f"Original-Prüfsumme unverändert: {'JA' if before == after else 'NEIN'}")
    return 0 if all(result.passed for result in results) and before == after else 1


if __name__ == "__main__":
    raise SystemExit(main())
