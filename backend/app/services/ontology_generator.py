"""
Ontologie-Generierungs-Service
Schnittstelle 1: Analysiert Textinhalt, generiert Entitäts- und Beziehungstyp-Definitionen für Sozialsimulation
"""

import json
from typing import Dict, Any, List, Optional
from ..utils.llm_client import LLMClient


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
- **Hinweis**: Attributnamen können nicht `name`, `uuid`, `group_id`, `created_at`, `summary` sein (diese sind System-reserviert)
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
            max_tokens=4096
        )
        
        # Validieren und Nachbearbeiten
        result = self._validate_and_process(result)
        
        return result
    
    # Maximale Textlänge für LLM (50.000 Zeichen)
    MAX_TEXT_LENGTH_FOR_LLM = 50000
    
    def _build_user_message(
        self,
        document_texts: List[str],
        simulation_requirement: str,
        additional_context: Optional[str]
    ) -> str:
        """Benutzernachricht erstellen"""
        
        # Texte zusammenführen
        combined_text = "\n\n---\n\n".join(document_texts)
        original_length = len(combined_text)
        
        # Bei über 50.000 Zeichen kürzen (betrifft nur LLM-Input, nicht den Graph-Aufbau)
        if len(combined_text) > self.MAX_TEXT_LENGTH_FOR_LLM:
            combined_text = combined_text[:self.MAX_TEXT_LENGTH_FOR_LLM]
            combined_text += f"\n\n...(Originaltext hat {original_length} Zeichen, wurde auf die ersten {self.MAX_TEXT_LENGTH_FOR_LLM} Zeichen für die Ontologie-Analyse gekürzt)..."
        
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
5. Attributnamen können nicht name, uuid, group_id usw. als reservierte Wörter verwenden, stattdessen full_name, org_name usw. verwenden
"""
        
        return message
    
    def _validate_and_process(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Ergebnisse validieren und nachbearbeiten"""
        
        # Sicherstellen, dass erforderliche Felder vorhanden sind
        if "entity_types" not in result:
            result["entity_types"] = []
        if "edge_types" not in result:
            result["edge_types"] = []
        if "analysis_summary" not in result:
            result["analysis_summary"] = ""
        
        # Entitätstypen validieren
        for entity in result["entity_types"]:
            if "attributes" not in entity:
                entity["attributes"] = []
            if "examples" not in entity:
                entity["examples"] = []
            # Sicherstellen, dass description maximal 100 Zeichen hat
            if len(entity.get("description", "")) > 100:
                entity["description"] = entity["description"][:97] + "..."
        
        # Beziehungstypen validieren
        for edge in result["edge_types"]:
            if "source_targets" not in edge:
                edge["source_targets"] = []
            if "attributes" not in edge:
                edge["attributes"] = []
            if len(edge.get("description", "")) > 100:
                edge["description"] = edge["description"][:97] + "..."
        
        # Zep API Limit: maximal 10 benutzerdefinierte Entitätstypen, maximal 10 benutzerdefinierte Kantentypen
        MAX_ENTITY_TYPES = 10
        MAX_EDGE_TYPES = 10
        
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
            
            # Wenn nach dem Hinzufügen mehr als 10 vorhanden, einige bestehende Typen entfernen
            if current_count + needed_slots > MAX_ENTITY_TYPES:
                # Berechnen wie viele entfernt werden müssen
                to_remove = current_count + needed_slots - MAX_ENTITY_TYPES
                # Vom Ende entfernen (wichtigere spezifische Typen vorne beibehalten)
                result["entity_types"] = result["entity_types"][:-to_remove]
            
            # Fallback-Typen hinzufügen
            result["entity_types"].extend(fallbacks_to_add)
        
        # Abschließend sicherstellen, dass Limits nicht überschritten werden (defensive Programmierung)
        if len(result["entity_types"]) > MAX_ENTITY_TYPES:
            result["entity_types"] = result["entity_types"][:MAX_ENTITY_TYPES]
        
        if len(result["edge_types"]) > MAX_EDGE_TYPES:
            result["edge_types"] = result["edge_types"][:MAX_EDGE_TYPES]
        
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
