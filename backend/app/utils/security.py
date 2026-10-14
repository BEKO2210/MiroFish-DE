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
    # Zep: UUID; Obsidian: sha1[:16] oder der Dateiname als ID.
    "entity_uuid": re.compile(
        r"(?:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|"
        r"[0-9a-f]{16}|(?!\.+\Z)[\w.-]{1,128})\Z",
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
    r"\b(?:sk-[A-Za-z0-9_-]{20,}|Bearer\s+[A-Za-z0-9._~+/=-]{20,})|"
    r"\b(?:API_TOKEN|LLM_API_KEY|ZEP_API_KEY)\s*=\s*[^\s,;]+"
)
_ERROR_FIELDS = {"error", "message"}
_TRANSLIT = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue", "ß": "ss"})
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


def safe_display_name(filename: str) -> str:
    """Anzeigename: nur Verzeichnisanteile und Steuerzeichen entfernen, Unicode bleibt."""
    name = filename.replace("\\", "/").rsplit("/", 1)[-1]
    name = "".join(ch for ch in name if ch.isprintable()).strip()[:200]
    return name or "dokument"


def safe_upload_name(filename: Any, allowed_extensions: set[str]) -> tuple[str, str]:
    """Liefert einen ASCII-sicheren Namen und die Endung (aus dem Originalnamen)."""
    if not isinstance(filename, str) or not filename:
        raise InvalidIdentifier("Ungueltiger Dateiname")
    stem, dot_ext = os.path.splitext(safe_display_name(filename))
    extension = dot_ext.lower().lstrip(".")
    if not extension or extension not in allowed_extensions:
        raise InvalidIdentifier("Nicht erlaubter Dateityp")
    ascii_stem = unicodedata.normalize("NFKD", stem.translate(_TRANSLIT)).encode("ascii", "ignore").decode()
    ascii_stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", ascii_stem).strip("._")
    return f"{ascii_stem or 'dokument'}{dot_ext}", extension


def scrub_text(value: str) -> str:
    if "Traceback (most recent call last)" in value:
        return "Interner Fehler"
    value = _SECRET_RE.sub("[GEHEIMNIS ENTFERNT]", value)
    return _PATH_RE.sub("[PFAD ENTFERNT]", value)


def sanitize_public_data(value: Any) -> Any:
    """Entfernt Tracebacks sowie Pfade/Schluessel aus Fehlerfeldern; Inhalte bleiben unveraendert."""
    if isinstance(value, dict):
        return {
            key: (scrub_text(child) if str(key).lower() in _ERROR_FIELDS and isinstance(child, str)
                  else sanitize_public_data(child))
            for key, child in value.items()
            if str(key).lower() not in {"traceback", "stacktrace"}
        }
    if isinstance(value, list):
        return [sanitize_public_data(child) for child in value]
    return value
