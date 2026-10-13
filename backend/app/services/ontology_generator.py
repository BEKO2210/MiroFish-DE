"""
Ontologie-Generierungs-Service
Schnittstelle 1: Analysiert Textinhalt, generiert Entitäts- und Beziehungstyp-Definitionen für Sozialsimulation
"""

import json
import logging
import re
import unicodedata
from typing import Dict, Any, List, Optional
from ..utils.llm_client import LLMClient
from ..utils.file_parser import split_text_into_chunks
from ..utils.ontology import (
    MAX_ONTOLOGY_TYPES,
    normalize_ontology_attributes,
    normalize_ontology_source_targets,
)

logger = logging.getLogger(__name__)


def _ascii_fold(name: str) -> str:
    """Umlaute/Akzente in ASCII umschreiben (lokale Modelle liefern trotz Vorgabe teils deutsche Typnamen;
    ohne diesen Schritt würde 'Bürger' zu 'BRger')."""
    for src, dst in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("Ä", "Ae"), ("Ö", "Oe"), ("Ü", "Ue"), ("ß", "ss")):
        name = name.replace(src, dst)
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")


def _to_pascal_case(name: str) -> str:
    """Beliebige Namensform in PascalCase umwandeln (z.B. 'works_for' -> 'WorksFor', 'person' -> 'Person')"""
    # An nicht-alphanumerischen Zeichen trennen
    parts = re.split(r'[^a-zA-Z0-9]+', _ascii_fold(name))
    # Zusätzlich an camelCase-Grenzen trennen (z.B. 'camelCase' -> ['camel', 'Case'])
    words = []
    for part in parts:
        words.extend(re.sub(r'([a-z])([A-Z])', r'\1_\2', part).split('_'))
    # Jedes Wort großschreiben, leere Teile verwerfen
    result = ''.join(word.capitalize() for word in words if word)
    return result if result else 'Unknown'


def _to_upper_snake_case(name: str) -> str:
    """Freie oder camelCase-Namen in SCREAMING_SNAKE_CASE umwandeln (Zep-Vorgabe für Kantentypen)"""
    separated = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', _ascii_fold(name).strip())
    normalized = re.sub(r'[^a-zA-Z0-9]+', '_', separated).strip('_').upper()
    if not normalized:
        return "UNKNOWN"
    if normalized[0].isdigit():
        normalized = f"REL_{normalized}"
    return normalized


# System-Prompt für Ontologie-Generierung
ONTOLOGY_SYSTEM_PROMPT = """Du bist ein professioneller Experte für Knowledge-Graph-Ontologie-Design. Deine Aufgabe ist es, die gegebenen Textinhalte und Simulationsanforderungen zu analysieren und Entitäts- und Beziehungstypen für die **Social-Media-Meinungssimulation** zu entwerfen.

**Wichtig: Du musst gültige JSON-Daten ausgeben, ohne zusätzliche Inhalte.**

## Kernaufgaben-Hintergrund

Wir bauen ein **Social-Media-Meinungssimulationssystem**. In diesem System:
- Jede Entität ist ein "Konto" oder "Subjekt", das in sozialen Medien seine Stimme erheben, interagieren und Informationen verbreiten kann
- Entitäten beeinflussen sich gegenseitig, teilen, kommentieren und reagieren aufeinander
- Wir müssen die Reaktionen der verschiedenen Parteien und die Informationsverbreitungspfade bei Meinungsereignissen simulieren

Daher **müssen Entitäten real existierende Subjekte sein, die in sozialen Medien ihre Stimme erheben und interagieren können**:

**Erlaubt sind**:
- Konkrete Personen (öffentliche Persönlichkeiten, Beteiligte, Meinungsführer, Experten, Gelehrte, gewöhnliche Menschen)
- Unternehmen (einschließlich ihrer offiziellen Konten)
- Organisationen (Universitäten, Verbände, NGOs, Gewerkschaften usw.)
- Regierungsbehörden, Aufsichtsbehörden
- Medienorganisationen (Zeitungen, Fernsehsender, selbstveröffentlichte Medien, Websites)
- Social-Media-Plattformen selbst
- Spezifische Gruppenvertreter (z.B. Alumni-Vereinigungen, Fangruppen, Interessenvertretungen usw.)

**Nicht erlaubt sind**:
- Abstrakte Konzepte (wie "öffentliche Meinung", "Emotion", "Trend")
- Themen (wie "akademische Integrität", "Bildungsreform")
- Meinungen/Einstellungen (wie "Unterstützer", "Gegner")

## Ausgabeformat

Bitte gib JSON-Format aus mit folgender Struktur:

```json
{
    "entity_types": [
        {
            "name": "Entitätstyp-Name (Englisch, PascalCase)",
            "description": "Kurze Beschreibung (Englisch, max. 100 Zeichen)",
            "attributes": [
                {
                    "name": "Attributname (Englisch, snake_case)",
                    "type": "text",
                    "description": "Attributbeschreibung"
                }
            ],
            "examples": ["Beispielentität 1", "Beispielentität 2"]
        }
    ],
    "edge_types": [
        {
            "name": "Beziehungstyp-Name (Englisch, UPPER_SNAKE_CASE)",
            "description": "Kurze Beschreibung (Englisch, max. 100 Zeichen)",
            "source_targets": [
                {"source": "Quellentitätstyp", "target": "Zielentitätstyp"}
            ],
            "attributes": []
        }
    ],
    "analysis_summary": "Kurze Analyse des Textinhalts (Deutsch)"
}
```

## Design-Richtlinien (extrem wichtig!)

### 1. Entitätstyp-Design - muss streng eingehalten werden

**Anzahl-Anforderung: Genau 10 Entitätstypen**

**Hierarchie-Anforderung (muss sowohl spezifische als auch Auffangtypen enthalten)**:

Deine 10 Entitätstypen müssen folgende Hierarchie enthalten:

A. **Auffangtypen (muss enthalten sein, als letzte 2 in der Liste)**:
   - `Person`: Auffangtyp für alle natürlichen Personen. Wenn eine Person nicht zu einer anderen spezifischeren Personenart gehört, wird sie dieser Kategorie zugeordnet.
   - `Organization`: Auffangtyp für alle Organisationen. Wenn eine Organisation nicht zu einer anderen spezifischeren Organisation gehört, wird sie dieser Kategorie zugeordnet.

B. **Spezifische Typen (8 Stück, je nach Textinhalt gestaltet)**:
   - Entwerfe spezifischere Typen für die Hauptrollen, die im Text auftauchen
   - Zum Beispiel: Wenn der Text akademische Ereignisse behandelt, können `Student`, `Professor`, `University` vorkommen
   - Zum Beispiel: Wenn der Text Geschäftsereignisse behandelt, können `Company`, `CEO`, `Employee` vorkommen

**Warum Auffangtypen benötigt werden**:
- Im Text tauchen verschiedene Personen auf, wie "Grund- und Mittelschullehrer", "Passant A", "ein Netizen"
- Wenn kein spezieller Typ passt, sollten sie der Kategorie `Person` zugeordnet werden
- Gleiches gilt für kleine Organisationen, temporäre Gruppen usw., die der Kategorie `Organization` zugeordnet werden sollten

**Design-Prinzipien für spezifische Typen**:
- Identifiziere aus dem Text häufig auftretende oder Schlüsselrollen
- Jeder spezifische Typ sollte klare Grenzen haben und nicht überlappen
- Die Beschreibung muss klar den Unterschied zwischen diesem Typ und dem Auffangtyp erklären

### 2. Beziehungstyp-Design

- Anzahl: 6-10 Stück
- Beziehungen sollten reale Verbindungen in Social-Media-Interaktionen widerspiegeln
- Stelle sicher, dass source_targets deine definierten Entitätstypen abdecken

### 3. Attribut-Design

- Jeder Entitätstyp hat 1-3 Schlüsselattribute
- **Hinweis**: Attributnamen können nicht `name`, `uuid`, `group_id`, `graph_id`, `created_at`, `summary` sein (diese sind System-reserviert)
- Empfohlen werden: `full_name`, `title`, `role`, `position`, `location`, `description` usw.

## Entitätstyp-Referenz

**Personen (spezifisch)**:
- Student: Schüler/Student
- Professor: Professor/Gelehrter
- Journalist: Journalist
- Celebrity: Star/Influencer
- Executive: Manager
- Official: Regierungsbeamter
- Lawyer: Anwalt
- Doctor: Arzt

**Personen (Auffangtyp)**:
- Person: Jede natürliche Person (verwenden, wenn nicht zu den obigen spezifischen Typen gehörig)

**Organisationen (spezifisch)**:
- University: Hochschule/Universität
- Company: Unternehmen
- GovernmentAgency: Regierungsbehörde
- MediaOutlet: Medienorganisation
- Hospital: Krankenhaus
- School: Grund-/Mittelschule
- NGO: Nichtregierungsorganisation

**Organisationen (Auffangtyp)**:
- Organization: Jede Organisation (verwenden, wenn nicht zu den obigen spezifischen Typen gehörig)

## Beziehungstyp-Referenz

- WORKS_FOR: Arbeitet bei
- STUDIES_AT: Studiert an
- AFFILIATED_WITH: Verbunden mit
- REPRESENTS: Vertritt
- REGULATES: Reguliert
- REPORTS_ON: Berichtet über
- COMMENTS_ON: Kommentiert
- RESPONDS_TO: Reagiert auf
- SUPPORTS: Unterstützt
- OPPOSES: Widerspricht/Lehnt ab
- COLLABORATES_WITH: Arbeitet zusammen mit
- COMPETES_WITH: Konkurriert mit
"""


class OntologyGenerator:
    """
    Ontologie-Generator
    Analysiert Textinhalte, generiert Entitäts- und Beziehungstyp-Definitionen
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()
    
    def generate(
        self,
        document_texts: List[str],
        simulation_requirement: str,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ontologie-Definition generieren
        
        Args:
            document_texts: Liste der Dokumenttexte
            simulation_requirement: Simulationsanforderungsbeschreibung
            additional_context: Zusätzlicher Kontext
            
        Returns:
            Ontologie-Definition (entity_types, edge_types etc.)
        """
        # Benutzernachricht erstellen
        user_message = self._build_user_message(
            document_texts, 
            simulation_requirement,
            additional_context
        )
        
        messages = [
            {"role": "system", "content": ONTOLOGY_SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
        
        # LLM aufrufen
        result = self.llm_client.chat_json(
            messages=messages,
            temperature=0.3,
            # Strukturierte Ontologie-Antworten können 4096 Tokens überschreiten. Abgeschnittenes JSON
            # (finish_reason=length) wird genau einmal ohne Token-Grenze erneut angefragt. Erster Versuch
            # bleibt begrenzt, damit kleine lokale Modelle nicht bis zum Kontextende in Schleifen laufen.
            max_tokens=8192,
            max_attempts=2,
        )
        
        # Validieren und Nachbearbeiten
        result = self._validate_and_process(result)
        
        return result
    
    # Maximale Textlänge für LLM (50.000 Zeichen)
    MAX_TEXT_LENGTH_FOR_LLM = 50000
    LONG_TEXT_CHUNK_SIZE = 8000
    LONG_TEXT_CHUNK_OVERLAP = 200
    MAX_LONG_TEXT_CHUNKS = 60
    MIN_LONG_TEXT_EXCERPT = 400
    
    def _build_user_message(
        self,
        document_texts: List[str],
        simulation_requirement: str,
        additional_context: Optional[str]
    ) -> str:
        """Benutzernachricht erstellen"""
        
        # Lange Texte werden über den ganzen Text verteilt gesampelt statt nur am Anfang gekürzt
        # (betrifft nur LLM-Input, nicht den Graph-Aufbau)
        combined_text = self._build_document_context(document_texts)
        
        message = f"""## Simulationsanforderung

{simulation_requirement}

## Dokumenteninhalt

{combined_text}
"""
        
        if additional_context:
            message += f"""
## Zusätzliche Hinweise

{additional_context}
"""
        
        message += """
Bitte entwerfe basierend auf dem obigen Inhalt Entitäts- und Beziehungstypen für die Meinungssimulation.

**Zwingend einzuhaltende Regeln**:
1. Es müssen genau 10 Entitätstypen ausgegeben werden
2. Die letzten 2 müssen Auffangtypen sein: Person (Auffang für Personen) und Organization (Auffang für Organisationen)
3. Die ersten 8 sind spezifische Typen, die je nach Textinhalt gestaltet werden
4. Alle Entitätstypen müssen real existierende Subjekte sein, die ihre Stimme erheben können, keine abstrakten Konzepte
5. Attributnamen können nicht name, uuid, group_id, graph_id usw. als reservierte Wörter verwenden, stattdessen full_name, org_name usw. verwenden
"""
        
        return message
    
    def _build_document_context(self, document_texts: List[str]) -> str:
        """Dokumentkontext für die Ontologie-Analyse bauen; lange Texte werden über alle Chunks
        gleichmäßig gesampelt, statt nur den Anfang abzuschneiden."""

        combined_text = "\n\n---\n\n".join(document_texts)
        original_length = len(combined_text)

        if original_length <= self.MAX_TEXT_LENGTH_FOR_LLM:
            return combined_text

        chunks = self._collect_document_chunks(document_texts)
        if not chunks:
            return ""

        selected_chunks = self._select_representative_chunks(chunks)
        excerpt_budget = self._calculate_excerpt_budget(len(selected_chunks))
        context = self._render_chunked_context(
            selected_chunks=selected_chunks,
            original_length=original_length,
            total_chunks=len(chunks),
            excerpt_limit=excerpt_budget,
        )

        while len(context) > self.MAX_TEXT_LENGTH_FOR_LLM and excerpt_budget > self.MIN_LONG_TEXT_EXCERPT:
            excerpt_budget = max(self.MIN_LONG_TEXT_EXCERPT, int(excerpt_budget * 0.85))
            context = self._render_chunked_context(
                selected_chunks=selected_chunks,
                original_length=original_length,
                total_chunks=len(chunks),
                excerpt_limit=excerpt_budget,
            )

        if len(context) > self.MAX_TEXT_LENGTH_FOR_LLM:
            marker = "\n\n...(Chunk-Kontext wurde auf die Längengrenze der Ontologie-Analyse gekürzt)..."
            context = context[:self.MAX_TEXT_LENGTH_FOR_LLM - len(marker)] + marker

        return context

    def _collect_document_chunks(self, document_texts: List[str]) -> List[Dict[str, Any]]:
        """Chunks pro Dokument sammeln; Dokument- und Chunk-Nummer bleiben für den Prompt erhalten."""

        all_chunks: List[Dict[str, Any]] = []
        for doc_index, text in enumerate(document_texts, 1):
            doc_chunks = split_text_into_chunks(
                text,
                chunk_size=self.LONG_TEXT_CHUNK_SIZE,
                overlap=self.LONG_TEXT_CHUNK_OVERLAP,
            )
            total_doc_chunks = len(doc_chunks)
            for chunk_index, chunk in enumerate(doc_chunks, 1):
                all_chunks.append({
                    "document_index": doc_index,
                    "chunk_index": chunk_index,
                    "total_document_chunks": total_doc_chunks,
                    "text": chunk,
                })

        return all_chunks

    def _select_representative_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Gleichmäßig verteilte Stichprobe aus allen Chunks (Anfang, Mitte und Ende)."""

        if len(chunks) <= self.MAX_LONG_TEXT_CHUNKS:
            return chunks

        if self.MAX_LONG_TEXT_CHUNKS <= 1:
            return [chunks[0]]

        last_index = len(chunks) - 1
        selected_indexes = {
            round(i * last_index / (self.MAX_LONG_TEXT_CHUNKS - 1))
            for i in range(self.MAX_LONG_TEXT_CHUNKS)
        }
        return [chunks[i] for i in sorted(selected_indexes)]

    def _calculate_excerpt_budget(self, selected_count: int) -> int:
        """Zeichenbudget pro Chunk anhand der Anzahl ausgewählter Chunks berechnen."""

        header_budget = 600
        chunk_header_budget = 120 * selected_count
        available = max(
            self.MIN_LONG_TEXT_EXCERPT * selected_count,
            self.MAX_TEXT_LENGTH_FOR_LLM - header_budget - chunk_header_budget,
        )
        return max(self.MIN_LONG_TEXT_EXCERPT, available // max(selected_count, 1))

    def _render_chunked_context(
        self,
        selected_chunks: List[Dict[str, Any]],
        original_length: int,
        total_chunks: int,
        excerpt_limit: int,
    ) -> str:
        """Chunk-Kontext für lange Texte als Prompt-Text aufbereiten."""

        lines = [
            (
                f"[Automatische Chunk-Zusammenfassung für lange Texte] Der Originaltext hat {original_length} Zeichen "
                f"und wurde für eine Analyse über den gesamten Text in {total_chunks} Textblöcke aufgeteilt."
            ),
            (
                f"Unten stehen Auszüge aus {len(selected_chunks)} repräsentativen Textblöcken "
                "(Anfang, Mitte und Ende). Entwirf die Ontologie anhand dieser Hinweise aus dem gesamten Text, "
                "nicht nur anhand des ersten Abschnitts."
            ),
        ]

        for chunk in selected_chunks:
            excerpt = self._excerpt_text(chunk["text"], excerpt_limit)
            lines.append(
                "\n".join([
                    (
                        f"--- Dokument {chunk['document_index']} / "
                        f"Block {chunk['chunk_index']}/{chunk['total_document_chunks']} ---"
                    ),
                    excerpt,
                ])
            )

        return "\n\n".join(lines)

    @staticmethod
    def _excerpt_text(text: str, char_limit: int) -> str:
        """Bei langen Chunks Anfang und Ende behalten, damit nicht jeder Chunk wieder nur am Anfang gekürzt wird."""

        text = text.strip()
        if len(text) <= char_limit:
            return text

        marker = "\n...(Mittelteil dieses Blocks ausgelassen)...\n"
        if char_limit <= len(marker) + 20:
            return text[:char_limit]

        remaining = char_limit - len(marker)
        head_len = remaining // 2
        tail_len = remaining - head_len
        return f"{text[:head_len].rstrip()}{marker}{text[-tail_len:].lstrip()}"

    def _validate_and_process(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Ergebnisse validieren und nachbearbeiten"""
        if not isinstance(result, dict):
            raise ValueError("Ontologie-Ergebnis muss ein JSON-Objekt sein")

        raw_entities = result.get("entity_types")
        raw_edges = result.get("edge_types")
        if not isinstance(raw_entities, list):
            raw_entities = []
        if not isinstance(raw_edges, list):
            raw_edges = []
        if not isinstance(result.get("analysis_summary"), str):
            result["analysis_summary"] = ""

        # Entitätseinträge normalisieren, bevor Felder gelesen werden: LLMs liefern
        # gelegentlich einen bloßen String, null oder einen anderen Skalar.
        # Namen werden in PascalCase umgewandelt (Zep-Vorgabe), Duplikate entfernt.
        entity_name_map: Dict[str, str] = {}
        processed_entities: List[Dict[str, Any]] = []
        seen_entity_names = set()
        for raw_entity in raw_entities:
            if isinstance(raw_entity, str):
                entity = {"name": raw_entity}
            elif isinstance(raw_entity, dict):
                entity = dict(raw_entity)
            else:
                logger.warning("Ontologie-Entitätseintrag ist kein Objekt und wird ignoriert")
                continue

            original_name = entity.get("name")
            if not isinstance(original_name, str) or not original_name.strip():
                logger.warning("Ontologie-Entität ohne brauchbaren Namen wird ignoriert")
                continue
            original_name = original_name.strip()
            normalized_name = _to_pascal_case(original_name)
            if normalized_name == "Unknown":
                continue
            if normalized_name in seen_entity_names:
                logger.warning(f"Doppelter Entitätstyp '{normalized_name}' bei der Validierung entfernt")
                entity_name_map[original_name] = normalized_name
                entity_name_map[original_name.lower()] = normalized_name
                continue

            if normalized_name != original_name:
                logger.warning(
                    f"Entitätstyp-Name '{original_name}' automatisch in '{normalized_name}' umgewandelt"
                )
            entity["name"] = normalized_name
            # LLM-Ausgabe normalisieren, Zep-Feldgrenzen einhalten und mindestens
            # ein Attribut je eigenem Typ garantieren
            entity["attributes"] = normalize_ontology_attributes(
                entity.get("attributes", [])
            )
            if not isinstance(entity.get("examples"), list):
                entity["examples"] = []
            # Sicherstellen, dass description maximal 100 Zeichen hat
            description = entity.get("description")
            if not isinstance(description, str) or not description:
                description = f"A {normalized_name} entity."
            entity["description"] = (
                description[:97] + "..." if len(description) > 100 else description
            )

            seen_entity_names.add(normalized_name)
            processed_entities.append(entity)
            entity_name_map[original_name] = normalized_name
            entity_name_map[original_name.lower()] = normalized_name
            entity_name_map[normalized_name] = normalized_name
            entity_name_map[normalized_name.lower()] = normalized_name

        result["entity_types"] = processed_entities

        # Fallback-Typen-Definition
        person_fallback = {
            "name": "Person",
            "description": "Any individual person not fitting other specific person types.",
            "attributes": [
                {"name": "full_name", "type": "text", "description": "Full name of the person"},
                {"name": "role", "type": "text", "description": "Role or occupation"}
            ],
            "examples": ["ordinary citizen", "anonymous netizen"]
        }
        
        organization_fallback = {
            "name": "Organization",
            "description": "Any organization not fitting other specific organization types.",
            "attributes": [
                {"name": "org_name", "type": "text", "description": "Name of the organization"},
                {"name": "org_type", "type": "text", "description": "Type of organization"}
            ],
            "examples": ["small business", "community group"]
        }
        
        # Prüfen ob Fallback-Typen bereits vorhanden sind
        entity_names = {e["name"] for e in result["entity_types"]}
        has_person = "Person" in entity_names
        has_organization = "Organization" in entity_names
        
        # Hinzuzufügende Fallback-Typen
        fallbacks_to_add = []
        if not has_person:
            fallbacks_to_add.append(person_fallback)
        if not has_organization:
            fallbacks_to_add.append(organization_fallback)
        
        if fallbacks_to_add:
            current_count = len(result["entity_types"])
            needed_slots = len(fallbacks_to_add)
            
            # Zep API Limit: maximal 10 eigene Entitätstypen; bei Überschreitung bestehende Typen entfernen
            if current_count + needed_slots > MAX_ONTOLOGY_TYPES:
                # Berechnen wie viele entfernt werden müssen
                to_remove = current_count + needed_slots - MAX_ONTOLOGY_TYPES
                # Vom Ende entfernen (wichtigere spezifische Typen vorne beibehalten)
                result["entity_types"] = result["entity_types"][:-to_remove]
            
            # Fallback-Typen hinzufügen
            result["entity_types"].extend(fallbacks_to_add)
        
        # Abschließend sicherstellen, dass Limits nicht überschritten werden (defensive Programmierung)
        result["entity_types"] = result["entity_types"][:MAX_ONTOLOGY_TYPES]

        # Kanten-Endpunkte erst nach Fallback/Kürzung auflösen, damit keine Kante
        # auf einen Typ verweist, der wegen der Zep-Grenzen entfernt wurde
        valid_entity_names = {entity["name"] for entity in result["entity_types"]}
        for name in valid_entity_names:
            entity_name_map[name] = name
            entity_name_map[name.lower()] = name

        def resolve_entity_name(value: str) -> Optional[str]:
            stripped = value.strip()
            if stripped == "Entity":
                return stripped
            mapped = entity_name_map.get(stripped) or entity_name_map.get(stripped.lower())
            if mapped in valid_entity_names:
                return mapped
            pascal_name = _to_pascal_case(stripped)
            return pascal_name if pascal_name in valid_entity_names else None

        # Beziehungstypen validieren (Namen in SCREAMING_SNAKE_CASE, Duplikate entfernen)
        processed_edges: List[Dict[str, Any]] = []
        seen_edge_names = set()
        for raw_edge in raw_edges:
            if isinstance(raw_edge, str):
                # Ein bloßer Kantenname hat keine Endpunkte und lässt sich nicht sicher
                # in Zep anlegen. Ignorieren statt eine Beziehung zu erfinden.
                logger.warning(f"Ontologie-Kante ohne source_targets wird ignoriert: {raw_edge}")
                continue
            elif isinstance(raw_edge, dict):
                edge = dict(raw_edge)
            else:
                logger.warning("Ontologie-Kanteneintrag ist kein Objekt und wird ignoriert")
                continue

            original_name = edge.get("name")
            if not isinstance(original_name, str) or not original_name.strip():
                logger.warning("Ontologie-Kante ohne brauchbaren Namen wird ignoriert")
                continue
            normalized_name = _to_upper_snake_case(original_name)
            if normalized_name == "UNKNOWN" or normalized_name in seen_edge_names:
                if normalized_name in seen_edge_names:
                    logger.warning(f"Doppelter Kantentyp '{normalized_name}' bei der Validierung entfernt")
                continue
            if normalized_name != original_name:
                logger.warning(
                    f"Kantentyp-Name '{original_name}' automatisch in '{normalized_name}' umgewandelt"
                )
            edge["name"] = normalized_name

            # source_targets auf die (ggf. umbenannten) gültigen Entitätstypen abbilden
            normalized_targets = []
            for source_target in normalize_ontology_source_targets(
                edge.get("source_targets", []),
                limit=None,
            ):
                source = resolve_entity_name(source_target["source"])
                target = resolve_entity_name(source_target["target"])
                if source and target:
                    normalized_targets.append({"source": source, "target": target})
            edge["source_targets"] = normalize_ontology_source_targets(
                normalized_targets
            )
            edge["attributes"] = normalize_ontology_attributes(
                edge.get("attributes", [])
            )
            description = edge.get("description")
            if not isinstance(description, str) or not description:
                description = f"A {normalized_name} relationship."
            edge["description"] = (
                description[:97] + "..." if len(description) > 100 else description
            )

            seen_edge_names.add(normalized_name)
            processed_edges.append(edge)
            if len(processed_edges) == MAX_ONTOLOGY_TYPES:
                break

        result["edge_types"] = processed_edges
        
        return result
    
    def generate_python_code(self, ontology: Dict[str, Any]) -> str:
        """
        Ontologie-Definition in Python-Code konvertieren (ähnlich ontology.py)
        
        Args:
            ontology: Ontologie-Definition
            
        Returns:
            Python-Code-String
        """
        code_lines = [
            '"""',
            'Benutzerdefinierte Entitätstyp-Definitionen',
            'Automatisch von MiroFish generiert, für Sozialsimulation',
            '"""',
            '',
            'from pydantic import Field',
            'from zep_cloud.external_clients.ontology import EntityModel, EntityText, EdgeModel',
            '',
            '',
            '# ============== Entitätstyp-Definitionen ==============',
            '',
        ]
        
        # Entitätstypen generieren
        for entity in ontology.get("entity_types", []):
            name = entity["name"]
            desc = entity.get("description", f"A {name} entity.")
            
            code_lines.append(f'class {name}(EntityModel):')
            code_lines.append(f'    """{desc}"""')
            
            attrs = entity.get("attributes", [])
            if attrs:
                for attr in attrs:
                    attr_name = attr["name"]
                    attr_desc = attr.get("description", attr_name)
                    code_lines.append(f'    {attr_name}: EntityText = Field(')
                    code_lines.append(f'        description="{attr_desc}",')
                    code_lines.append(f'        default=None')
                    code_lines.append(f'    )')
            else:
                code_lines.append('    pass')
            
            code_lines.append('')
            code_lines.append('')
        
        code_lines.append('# ============== Beziehungstyp-Definitionen ==============')
        code_lines.append('')
        
        # Beziehungstypen generieren
        for edge in ontology.get("edge_types", []):
            name = edge["name"]
            # In PascalCase-Klassennamen konvertieren
            class_name = ''.join(word.capitalize() for word in name.split('_'))
            desc = edge.get("description", f"A {name} relationship.")
            
            code_lines.append(f'class {class_name}(EdgeModel):')
            code_lines.append(f'    """{desc}"""')
            
            attrs = edge.get("attributes", [])
            if attrs:
                for attr in attrs:
                    attr_name = attr["name"]
                    attr_desc = attr.get("description", attr_name)
                    code_lines.append(f'    {attr_name}: EntityText = Field(')
                    code_lines.append(f'        description="{attr_desc}",')
                    code_lines.append(f'        default=None')
                    code_lines.append(f'    )')
            else:
                code_lines.append('    pass')
            
            code_lines.append('')
            code_lines.append('')
        
        # Typ-Wörterbuch generieren
        code_lines.append('# ============== Typ-Konfiguration ==============')
        code_lines.append('')
        code_lines.append('ENTITY_TYPES = {')
        for entity in ontology.get("entity_types", []):
            name = entity["name"]
            code_lines.append(f'    "{name}": {name},')
        code_lines.append('}')
        code_lines.append('')
        code_lines.append('EDGE_TYPES = {')
        for edge in ontology.get("edge_types", []):
            name = edge["name"]
            class_name = ''.join(word.capitalize() for word in name.split('_'))
            code_lines.append(f'    "{name}": {class_name},')
        code_lines.append('}')
        code_lines.append('')
        
        # Source-Targets-Zuordnung für Kanten generieren
        code_lines.append('EDGE_SOURCE_TARGETS = {')
        for edge in ontology.get("edge_types", []):
            name = edge["name"]
            source_targets = edge.get("source_targets", [])
            if source_targets:
                st_list = ', '.join([
                    f'{{"source": "{st.get("source", "Entity")}", "target": "{st.get("target", "Entity")}"}}'
                    for st in source_targets
                ])
                code_lines.append(f'    "{name}": [{st_list}],')
        code_lines.append('}')
        
        return '\n'.join(code_lines)
