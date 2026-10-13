"""
Hilfsfunktionen zur Validierung LLM-generierter Ontologie-Strukturen
(portiert aus Upstream 666ghj/MiroFish: 9506e6f, d2f9e56, e4aa38d)
"""

from typing import Any, Dict, List, Optional


# Zep-Grenzen: maximal 10 eigene Typen, 10 Attribute je Typ, 10 Source-Target-Paare je Kante
MAX_ONTOLOGY_TYPES = 10
MAX_ONTOLOGY_ATTRIBUTES = 10
MAX_ONTOLOGY_SOURCE_TARGETS = 10

# Von Zep reservierte Namen, die nicht als Attributname verwendet werden dürfen
RESERVED_ONTOLOGY_ATTRIBUTE_NAMES = frozenset({
    "uuid",
    "name",
    "group_id",
    "graph_id",
    "name_embedding",
    "summary",
    "created_at",
})

# Ersatzattribut, damit jeder eigene Typ mindestens eine Eigenschaft hat
_FALLBACK_ATTRIBUTE = {
    "name": "details",
    "type": "text",
    "description": "Additional details about this ontology type.",
}


def normalize_ontology_attribute(attribute: Any) -> Optional[Dict[str, Any]]:
    """Gibt eine sichere Attributdefinition zurück oder ``None`` für unbrauchbare Werte.

    Das LLM liefert Attribute manchmal als reine Strings statt als Objekte (Upstream #135).
    """

    if isinstance(attribute, str):
        if not attribute.strip():
            return None
        return {
            "name": attribute,
            "type": "text",
            "description": attribute,
        }

    if not isinstance(attribute, dict):
        return None

    name = attribute.get("name")
    if not isinstance(name, str) or not name.strip():
        return None

    normalized = dict(attribute)
    description = normalized.get("description")
    if not isinstance(description, str) or not description:
        normalized["description"] = name
    return normalized


def normalize_ontology_attributes(attributes: Any) -> List[Dict[str, Any]]:
    """Gibt eine nicht-leere, Zep-kompatible Attributliste innerhalb der Grenzen zurück."""

    if not isinstance(attributes, list):
        attributes = []

    normalized_attributes: List[Dict[str, Any]] = []
    for attribute in attributes:
        normalized = normalize_ontology_attribute(attribute)
        if normalized is None:
            continue
        normalized_attributes.append(normalized)
        if len(normalized_attributes) == MAX_ONTOLOGY_ATTRIBUTES:
            break

    if not normalized_attributes:
        normalized_attributes.append(dict(_FALLBACK_ATTRIBUTE))

    return normalized_attributes


def normalize_ontology_source_targets(
    source_targets: Any,
    *,
    limit: Optional[int] = MAX_ONTOLOGY_SOURCE_TARGETS,
) -> List[Dict[str, str]]:
    """Gibt eindeutige, strukturell gültige Source-Target-Paare innerhalb der Zep-Grenzen zurück."""

    if not isinstance(source_targets, list):
        return []

    normalized_targets: List[Dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for source_target in source_targets:
        if not isinstance(source_target, dict):
            continue
        source = source_target.get("source")
        target = source_target.get("target")
        if not isinstance(source, str) or not source.strip():
            continue
        if not isinstance(target, str) or not target.strip():
            continue

        pair = (source.strip(), target.strip())
        if pair in seen:
            continue
        seen.add(pair)
        normalized_targets.append({"source": pair[0], "target": pair[1]})
        if limit is not None and len(normalized_targets) == limit:
            break

    return normalized_targets
