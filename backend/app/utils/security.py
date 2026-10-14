"""Gemeinsame Eingabe- und Pfadsicherheitsregeln fuer die HTTP-API."""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Any


ID_PATTERNS = {
    "project_id": re.compile(r"proj_[A-Za-z0-9_-]{1,64}\Z"),
    "simulation_id": re.compile(r"sim_[A-Za-z0-9_-]{1,64}\Z"),
    "report_id": re.compile(r"report_[A-Za-z0-9]{1,64}\Z"),
    "ensemble_id": re.compile(r"ens_[0-9a-f]{12}\Z"),
    "run_id": re.compile(r"run_[A-Za-z0-9_-]{1,64}\Z"),
    "pipeline_id": re.compile(r"run_[A-Za-z0-9_-]{1,64}\Z"),
    "task_id": re.compile(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z",
        re.IGNORECASE,
    ),
    "entity_uuid": re.compile(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z",
        re.IGNORECASE,
    ),
    # Zep erzeugt mirofish_<hex>; Obsidian nutzt derzeit eine UUID (alte
    # Datenstaende koennen auch eine Simulations-ID enthalten).
    "graph_id": re.compile(
        r"(?:mirofish_[0-9a-f]{16}|sim_[A-Za-z0-9_-]{1,64}|"
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\Z",
        re.IGNORECASE,
    ),
}

_ALIASES = {"pid": "run_id"}

_SECRET_RE = re.compile(
    r"(?i)(?:bearer\s+)[A-Za-z0-9._~+/-]+=*|"
    r"(?:sk|key|token|secret)[-_][A-Za-z0-9._-]{8,}|"
    r"(?:API_TOKEN|LLM_API_KEY|ZEP_API_KEY)\s*=\s*[^\s,;]+"
)
_PATH_RE = re.compile(
    r"(?<![:A-Za-z0-9])(?:/(?:home|tmp|root|etc|var|opt)/[^\s\"'<>]*|"
    r"[A-Za-z]:\\[^\r\n\"'<>]*)"
)


class InvalidIdentifier(ValueError):
    """Eine von aussen gelieferte Kennung entspricht nicht ihrem Format."""


def validate_identifier(kind: str, value: Any, *, optional: bool = False) -> str | None:
    """Prueft API-Kennungen strikt und gibt den unveraenderten Wert zurueck."""
    kind = _ALIASES.get(kind, kind)
    if optional and (value is None or value == ""):
        return None
    pattern = ID_PATTERNS.get(kind)
    if pattern is None:
        raise KeyError(f"Unbekannter Kennungstyp: {kind}")
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise InvalidIdentifier(f"Ungueltige {kind}")
    return value


def validate_known_ids(value: Any) -> None:
    """Prueft bekannte ID-Felder rekursiv in JSON-Objekten."""
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = _ALIASES.get(str(key), str(key))
            if normalized in ID_PATTERNS and child not in (None, ""):
                validate_identifier(normalized, child)
            else:
                validate_known_ids(child)
    elif isinstance(value, list):
        for child in value:
            validate_known_ids(child)


def safe_child(root: str | os.PathLike[str], name: str) -> Path:
    """Liefert genau ein Kind unter *root*; Symlinks und Traversal werden abgewiesen."""
    if not isinstance(name, str) or not name or name in {".", ".."}:
        raise InvalidIdentifier("Ungueltiger Dateiname")
    if "/" in name or "\\" in name or os.path.isabs(name):
        raise InvalidIdentifier("Ungueltiger Dateiname")
    base = Path(root).resolve()
    candidate = base / name
    if candidate.is_symlink():
        raise InvalidIdentifier("Symlinks sind nicht zulaessig")
    resolved = candidate.resolve()
    if resolved.parent != base:
        raise InvalidIdentifier("Pfad liegt ausserhalb des Datenordners")
    return resolved


def safe_upload_name(filename: Any, allowed_extensions: set[str]) -> tuple[str, str]:
    """Normalisiert einen Anzeigenamen und prueft seine Endung."""
    if not isinstance(filename, str) or not filename:
        raise InvalidIdentifier("Ungueltiger Dateiname")
    # Werkzeug ist im Backend vorhanden; der kleine Fallback haelt die reine
    # Validierungsbibliothek auch in den schlanken Offline-Tests importierbar.
    try:
        from werkzeug.utils import secure_filename
        name = secure_filename(filename)
    except ImportError:
        normalized = unicodedata.normalize("NFKD", filename).encode("ascii", "ignore").decode()
        name = re.sub(r"[^A-Za-z0-9_.-]", "_", normalized).strip("._")
    extension = os.path.splitext(name)[1].lower().lstrip('.')
    if not name or not extension or extension not in allowed_extensions:
        raise InvalidIdentifier("Nicht erlaubter Dateityp")
    return name, extension


def sanitize_public_data(value: Any) -> Any:
    """Entfernt Tracebacks, lokale Pfade und typische Geheimnisse aus JSON-Daten."""
    if isinstance(value, dict):
        return {
            key: sanitize_public_data(child)
            for key, child in value.items()
            if str(key).lower() not in {"traceback", "stacktrace"}
        }
    if isinstance(value, list):
        return [sanitize_public_data(child) for child in value]
    if isinstance(value, str):
        if "Traceback (most recent call last)" in value:
            return "Interner Fehler"
        value = _SECRET_RE.sub("[GEHEIMNIS ENTFERNT]", value)
        return _PATH_RE.sub("[PFAD ENTFERNT]", value)
    return value
