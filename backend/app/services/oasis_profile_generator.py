"""
OASIS Agent Profile Generator
Konvertiert Entitäten aus dem Zep-Graphen in das OASIS-Simulationsplattformat

Verbesserungen:
1. Nutzt Zep-Retrieval-Funktionen für die Anreicherung von Knoteninformationen
2. Optimierte Prompts für die Generierung sehr detaillierter Profile
3. Unterscheidung zwischen individuellen Entitäten und abstrakten Gruppenentitäten
"""

import json
import random
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from openai import OpenAI
from zep_cloud.client import Zep

from ..config import Config
from ..utils.logger import get_logger
from .zep_entity_reader import EntityNode, ZepEntityReader

logger = get_logger('mirofish.oasis_profile')


@dataclass
class OasisAgentProfile:
    """OASIS Agent Profile Datenstruktur"""
    # Allgemeine Felder
    user_id: int
    user_name: str
    name: str
    bio: str
    persona: str
    
    # Optionale Felder - Reddit-Stil
    karma: int = 1000
    
    # Optionale Felder - Twitter-Stil
    friend_count: int = 100
    follower_count: int = 150
    statuses_count: int = 500
    
    # Zusätzliche Profilinformationen
    age: Optional[int] = None
    gender: Optional[str] = None
    mbti: Optional[str] = None
    country: Optional[str] = None
    profession: Optional[str] = None
    interested_topics: List[str] = field(default_factory=list)
    
    # Quellentitätsinformationen
    source_entity_uuid: Optional[str] = None
    source_entity_type: Optional[str] = None
    
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    
    def to_reddit_format(self) -> Dict[str, Any]:
        """In Reddit-Plattformformat konvertieren"""
        profile = {
            "user_id": self.user_id,
            "username": self.user_name,  # OASIS Bibliothek erfordert Feldname username (ohne Unterstrich)
            "name": self.name,
            "bio": self.bio,
            "persona": self.persona,
            "karma": self.karma,
            "created_at": self.created_at,
        }
        
        # Zusätzliche Profilinformationen hinzufügen (falls vorhanden)
        if self.age:
            profile["age"] = self.age
        if self.gender:
            profile["gender"] = self.gender
        if self.mbti:
            profile["mbti"] = self.mbti
        if self.country:
            profile["country"] = self.country
        if self.profession:
            profile["profession"] = self.profession
        if self.interested_topics:
            profile["interested_topics"] = self.interested_topics
        
        return profile
    
    def to_twitter_format(self) -> Dict[str, Any]:
        """In Twitter-Plattformformat konvertieren"""
        profile = {
            "user_id": self.user_id,
            "username": self.user_name,  # OASIS Bibliothek erfordert Feldname username (ohne Unterstrich)
            "name": self.name,
            "bio": self.bio,
            "persona": self.persona,
            "friend_count": self.friend_count,
            "follower_count": self.follower_count,
            "statuses_count": self.statuses_count,
            "created_at": self.created_at,
        }
        
        # Zusätzliche Profilinformationen hinzufügen
        if self.age:
            profile["age"] = self.age
        if self.gender:
            profile["gender"] = self.gender
        if self.mbti:
            profile["mbti"] = self.mbti
        if self.country:
            profile["country"] = self.country
        if self.profession:
            profile["profession"] = self.profession
        if self.interested_topics:
            profile["interested_topics"] = self.interested_topics
        
        return profile
    
    def to_dict(self) -> Dict[str, Any]:
        """In vollständiges Dictionary-Format konvertieren"""
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "name": self.name,
            "bio": self.bio,
            "persona": self.persona,
            "karma": self.karma,
            "friend_count": self.friend_count,
            "follower_count": self.follower_count,
            "statuses_count": self.statuses_count,
            "age": self.age,
            "gender": self.gender,
            "mbti": self.mbti,
            "country": self.country,
            "profession": self.profession,
            "interested_topics": self.interested_topics,
            "source_entity_uuid": self.source_entity_uuid,
            "source_entity_type": self.source_entity_type,
            "created_at": self.created_at,
        }


class OasisProfileGenerator:
    """
    OASIS Profile Generator
    
    Konvertiert Entitäten aus dem Zep-Graphen in OASIS-Simulations-Agent-Profile
    
    Optimierte Funktionen:
    1. Nutzt Zep-Graphen-Retrieval für umfangreicheren Kontext
    2. Generiert sehr detaillierte Profile (inkl. Grundinformationen, Berufserfahrung, Persönlichkeitsmerkmale, Social-Media-Verhalten usw.)
    3. Unterscheidung zwischen individuellen Entitäten und abstrakten Gruppenentitäten
    """
    
    # MBTI-Typenliste
    MBTI_TYPES = [
        "INTJ", "INTP", "ENTJ", "ENTP",
        "INFJ", "INFP", "ENFJ", "ENFP",
        "ISTJ", "ISFJ", "ESTJ", "ESFJ",
        "ISTP", "ISFP", "ESTP", "ESFP"
    ]
    
    # Liste häufiger Länder
    COUNTRIES = [
        "China", "US", "UK", "Japan", "Germany", "France", 
        "Canada", "Australia", "Brazil", "India", "South Korea"
    ]
    
    # Individuelle Entitätstypen (erfordern konkrete Profilgenerierung)
    INDIVIDUAL_ENTITY_TYPES = [
        "student", "alumni", "professor", "person", "publicfigure", 
        "expert", "faculty", "official", "journalist", "activist"
    ]
    
    # Gruppen-/Institutionstypen (erfordern repräsentative Profilgenerierung)
    GROUP_ENTITY_TYPES = [
        "university", "governmentagency", "organization", "ngo", 
        "mediaoutlet", "company", "institution", "group", "community"
    ]
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        zep_api_key: Optional[str] = None,
        graph_id: Optional[str] = None
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model_name = model_name or Config.LLM_MODEL_NAME
        
        if not self.api_key:
            raise ValueError("LLM_API_KEY nicht konfiguriert")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        # Zep-Client für Retrieval-Kontextanreicherung
        self.zep_api_key = zep_api_key or Config.ZEP_API_KEY
        self.zep_client = None
        self.graph_id = graph_id
        
        if self.zep_api_key:
            try:
                self.zep_client = Zep(api_key=self.zep_api_key)
            except Exception as e:
                logger.warning(f"Zep-Client-Initialisierung fehlgeschlagen: {e}")
    
    def generate_profile_from_entity(
        self, 
        entity: EntityNode, 
        user_id: int,
        use_llm: bool = True
    ) -> OasisAgentProfile:
        """
        Generiert OASIS Agent Profile aus Zep-Entität
        
        Args:
            entity: Zep-Entitätsknoten
            user_id: Benutzer-ID (für OASIS)
            use_llm: Ob LLM für detaillierte Profilerstellung verwendet werden soll
            
        Returns:
            OasisAgentProfile
        """
        entity_type = entity.get_entity_type() or "Entity"
        
        # Basisinformationen
        name = entity.name
        user_name = self._generate_username(name)
        
        # Kontextinformationen aufbauen
        context = self._build_entity_context(entity)
        
        if use_llm:
            # Detailliertes Profil mit LLM generieren
            profile_data = self._generate_profile_with_llm(
                entity_name=name,
                entity_type=entity_type,
                entity_summary=entity.summary,
                entity_attributes=entity.attributes,
                context=context
            )
        else:
            # Basisprofil mit Regeln generieren
            profile_data = self._generate_profile_rule_based(
                entity_name=name,
                entity_type=entity_type,
                entity_summary=entity.summary,
                entity_attributes=entity.attributes
            )
        
        return OasisAgentProfile(
            user_id=user_id,
            user_name=user_name,
            name=name,
            bio=profile_data.get("bio", f"{entity_type}: {name}"),
            persona=profile_data.get("persona", entity.summary or f"A {entity_type} named {name}."),
            karma=profile_data.get("karma", random.randint(500, 5000)),
            friend_count=profile_data.get("friend_count", random.randint(50, 500)),
            follower_count=profile_data.get("follower_count", random.randint(100, 1000)),
            statuses_count=profile_data.get("statuses_count", random.randint(100, 2000)),
            age=profile_data.get("age"),
            gender=profile_data.get("gender"),
            mbti=profile_data.get("mbti"),
            country=profile_data.get("country"),
            profession=profile_data.get("profession"),
            interested_topics=profile_data.get("interested_topics", []),
            source_entity_uuid=entity.uuid,
            source_entity_type=entity_type,
        )
    
    def _generate_username(self, name: str) -> str:
        """Benutzernamen generieren"""
        # Entferne Sonderzeichen, konvertiere zu Kleinbuchstaben
        username = name.lower().replace(" ", "_")
        username = ''.join(c for c in username if c.isalnum() or c == '_')
        
        # Füge zufälliges Suffix hinzu, um Duplikate zu vermeiden
        suffix = random.randint(100, 999)
        return f"{username}_{suffix}"
    
    def _search_zep_for_entity(self, entity: EntityNode) -> Dict[str, Any]:
        """
        Nutzt Zep-Graphen-Hybrid-Suchfunktion, um umfangreiche entitätsbezogene Informationen zu erhalten
        
        Zep hat keine integrierte Hybrid-Such-Schnittstelle, daher müssen Edges und Nodes separat durchsucht und dann zusammengeführt werden.
        Verwendet parallele Anfragen für gleichzeitige Suche, um Effizienz zu steigern.
        
        Args:
            entity: Entitätsknotenobjekt
            
        Returns:
            Dictionary mit facts, node_summaries, context
        """
        import concurrent.futures
        
        if not self.zep_client:
            return {"facts": [], "node_summaries": [], "context": ""}
        
        entity_name = entity.name
        
        results = {
            "facts": [],
            "node_summaries": [],
            "context": ""
        }
        
        # graph_id ist für die Suche erforderlich
        if not self.graph_id:
            logger.debug(f"Überspringe Zep-Retrieval: graph_id nicht gesetzt")
            return results
        
        comprehensive_query = f"Alle Informationen, Aktivitäten, Ereignisse, Beziehungen und Hintergründe über {entity_name}"
        
        def search_edges():
            """Suche nach Edges (Fakten/Beziehungen) - mit Retry-Mechanismus"""
            max_retries = 3
            last_exception = None
            delay = 2.0
            
            for attempt in range(max_retries):
                try:
                    return self.zep_client.graph.search(
                        query=comprehensive_query,
                        graph_id=self.graph_id,
                        limit=30,
                        scope="edges",
                        reranker="rrf"
                    )
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.debug(f"Zep Edge-Suche Versuch {attempt + 1} fehlgeschlagen: {str(e)[:80]}, wiederhole...")
                        time.sleep(delay)
                        delay *= 2
                    else:
                        logger.debug(f"Zep Edge-Suche nach {max_retries} Versuchen fehlgeschlagen: {e}")
            return None
        
        def search_nodes():
            """Suche nach Nodes (Entitätszusammenfassungen) - mit Retry-Mechanismus"""
            max_retries = 3
            last_exception = None
            delay = 2.0
            
            for attempt in range(max_retries):
                try:
                    return self.zep_client.graph.search(
                        query=comprehensive_query,
                        graph_id=self.graph_id,
                        limit=20,
                        scope="nodes",
                        reranker="rrf"
                    )
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.debug(f"Zep Node-Suche Versuch {attempt + 1} fehlgeschlagen: {str(e)[:80]}, wiederhole...")
                        time.sleep(delay)
                        delay *= 2
                    else:
                        logger.debug(f"Zep Node-Suche nach {max_retries} Versuchen fehlgeschlagen: {e}")
            return None
        
        try:
            # Parallele Ausführung von Edge- und Node-Suche
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                edge_future = executor.submit(search_edges)
                node_future = executor.submit(search_nodes)
                
                # Ergebnisse abrufen
                edge_result = edge_future.result(timeout=30)
                node_result = node_future.result(timeout=30)
            
            # Edge-Suchergebnisse verarbeiten
            all_facts = set()
            if edge_result and hasattr(edge_result, 'edges') and edge_result.edges:
                for edge in edge_result.edges:
                    if hasattr(edge, 'fact') and edge.fact:
                        all_facts.add(edge.fact)
            results["facts"] = list(all_facts)
            
            # Node-Suchergebnisse verarbeiten
            all_summaries = set()
            if node_result and hasattr(node_result, 'nodes') and node_result.nodes:
                for node in node_result.nodes:
                    if hasattr(node, 'summary') and node.summary:
                        all_summaries.add(node.summary)
                    if hasattr(node, 'name') and node.name and node.name != entity_name:
                        all_summaries.add(f"Verwandte Entität: {node.name}")
            results["node_summaries"] = list(all_summaries)
            
            # Kontext zusammenstellen
            context_parts = []
            if results["facts"]:
                context_parts.append("Fakt-Informationen:\n" + "\n".join(f"- {f}" for f in results["facts"][:20]))
            if results["node_summaries"]:
                context_parts.append("Verwandte Entitäten:\n" + "\n".join(f"- {s}" for s in results["node_summaries"][:10]))
            results["context"] = "\n\n".join(context_parts)
            
            logger.info(f"Zep-Hybrid-Retrieval abgeschlossen: {entity_name}, {len(results['facts'])} Fakten, {len(results['node_summaries'])} verwandte Nodes erhalten")
            
        except concurrent.futures.TimeoutError:
            logger.warning(f"Zep-Retrieval-Timeout ({entity_name})")
        except Exception as e:
            logger.warning(f"Zep-Retrieval fehlgeschlagen ({entity_name}): {e}")
        
        return results
    
    def _build_entity_context(self, entity: EntityNode) -> str:
        """
        Vollständige Kontextinformationen für die Entität aufbauen
        
        Enthält:
        1. Edge-Informationen der Entität selbst (Fakten)
        2. Detaillierte Informationen über verbundene Nodes
        3. Angereicherte Informationen aus dem Zep-Hybrid-Retrieval
        """
        context_parts = []
        
        # 1. Entitätsattribute hinzufügen
        if entity.attributes:
            attrs = []
            for key, value in entity.attributes.items():
                if value and str(value).strip():
                    attrs.append(f"- {key}: {value}")
            if attrs:
                context_parts.append("### Entitätsattribute\n" + "\n".join(attrs))
        
        # 2. Verwandte Edge-Informationen (Fakten/Beziehungen) hinzufügen
        existing_facts = set()
        if entity.related_edges:
            relationships = []
            for edge in entity.related_edges:  # Keine Begrenzung
                fact = edge.get("fact", "")
                edge_name = edge.get("edge_name", "")
                direction = edge.get("direction", "")
                
                if fact:
                    relationships.append(f"- {fact}")
                    existing_facts.add(fact)
                elif edge_name:
                    if direction == "outgoing":
                        relationships.append(f"- {entity.name} --[{edge_name}]--> (verwandte Entität)")
                    else:
                        relationships.append(f"- (verwandte Entität) --[{edge_name}]--> {entity.name}")
            
            if relationships:
                context_parts.append("### Verwandte Fakten und Beziehungen\n" + "\n".join(relationships))
        
        # 3. Detaillierte Informationen über verbundene Nodes hinzufügen
        if entity.related_nodes:
            related_info = []
            for node in entity.related_nodes:  # Keine Begrenzung
                node_name = node.get("name", "")
                node_labels = node.get("labels", [])
                node_summary = node.get("summary", "")
                
                # Standard-Labels filtern
                custom_labels = [l for l in node_labels if l not in ["Entity", "Node"]]
                label_str = f" ({', '.join(custom_labels)})" if custom_labels else ""
                
                if node_summary:
                    related_info.append(f"- **{node_name}**{label_str}: {node_summary}")
                else:
                    related_info.append(f"- **{node_name}**{label_str}")
            
            if related_info:
                context_parts.append("### Verbundene Entitätsinformationen\n" + "\n".join(related_info))
        
        # 4. Umfangreichere Informationen mit Zep-Hybrid-Retrieval abrufen
        zep_results = self._search_zep_for_entity(entity)
        
        if zep_results.get("facts"):
            # Deduplizierung: Vorhandene Fakten ausschließen
            new_facts = [f for f in zep_results["facts"] if f not in existing_facts]
            if new_facts:
                context_parts.append("### Aus Zep abgerufene Fakt-Informationen\n" + "\n".join(f"- {f}" for f in new_facts[:15]))
        
        if zep_results.get("node_summaries"):
            context_parts.append("### Aus Zep abgerufene verwandte Nodes\n" + "\n".join(f"- {s}" for s in zep_results["node_summaries"][:10]))
        
        return "\n\n".join(context_parts)
    
    def _is_individual_entity(self, entity_type: str) -> bool:
        """Prüft, ob es sich um einen individuellen Entitätstyp handelt"""
        return entity_type.lower() in self.INDIVIDUAL_ENTITY_TYPES
    
    def _is_group_entity(self, entity_type: str) -> bool:
        """Prüft, ob es sich um einen Gruppen-/Institutionstyp handelt"""
        return entity_type.lower() in self.GROUP_ENTITY_TYPES
    
    def _generate_profile_with_llm(
        self,
        entity_name: str,
        entity_type: str,
        entity_summary: str,
        entity_attributes: Dict[str, Any],
        context: str
    ) -> Dict[str, Any]:
        """
        Generiert sehr detaillierte Profile mit LLM
        
        Unterscheidung nach Entitätstyp:
        - Individuelle Entitäten: Generierung konkreter Charakterprofile
        - Gruppen-/Institutionen: Generierung repräsentativer Kontoprofile
        """
        
        is_individual = self._is_individual_entity(entity_type)
        
        if is_individual:
            prompt = self._build_individual_persona_prompt(
                entity_name, entity_type, entity_summary, entity_attributes, context
            )
        else:
            prompt = self._build_group_persona_prompt(
                entity_name, entity_type, entity_summary, entity_attributes, context
            )

        # Mehrere Generierungsversuche bis zum Erfolg oder max. Retries
        max_attempts = 3
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt(is_individual)},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7 - (attempt * 0.1)  # Temperatur bei jedem Retry reduzieren
                    # Kein max_tokens, damit LLM frei arbeiten kann
                )
                
                content = response.choices[0].message.content
                
                # Prüfen, ob die Ausgabe abgeschnitten wurde (finish_reason nicht 'stop')
                finish_reason = response.choices[0].finish_reason
                if finish_reason == 'length':
                    logger.warning(f"LLM-Ausgabe abgeschnitten (Versuch {attempt+1}), versuche Reparatur...")
                    content = self._fix_truncated_json(content)
                
                # JSON parsen versuchen
                try:
                    result = json.loads(content)
                    
                    # Erforderliche Felder validieren
                    if "bio" not in result or not result["bio"]:
                        result["bio"] = entity_summary[:200] if entity_summary else f"{entity_type}: {entity_name}"
                    if "persona" not in result or not result["persona"]:
                        result["persona"] = entity_summary or f"{entity_name} ist ein {entity_type}."
                    
                    return result
                    
                except json.JSONDecodeError as je:
                    logger.warning(f"JSON-Parsing fehlgeschlagen (Versuch {attempt+1}): {str(je)[:80]}")
                    
                    # JSON reparieren versuchen
                    result = self._try_fix_json(content, entity_name, entity_type, entity_summary)
                    if result.get("_fixed"):
                        del result["_fixed"]
                        return result
                    
                    last_error = je
                    
            except Exception as e:
                logger.warning(f"LLM-Aufruf fehlgeschlagen (Versuch {attempt+1}): {str(e)[:80]}")
                last_error = e
                import time
                time.sleep(1 * (attempt + 1))  # Exponentielles Backoff
        
        logger.warning(f"LLM-Profilgenerierung fehlgeschlagen ({max_attempts} Versuche): {last_error}, verwende Regelbasierte Generierung")
        return self._generate_profile_rule_based(
            entity_name, entity_type, entity_summary, entity_attributes
        )
    
    def _fix_truncated_json(self, content: str) -> str:
        """Repariert abgeschnittenes JSON (durch max_tokens-Limit)"""
        import re
        
        # Wenn JSON abgeschnitten wurde, versuche zu schließen
        content = content.strip()
        
        # Unvollständige Klammern zählen
        open_braces = content.count('{') - content.count('}')
        open_brackets = content.count('[') - content.count(']')
        
        # Prüfen, ob ungeschlossene Strings vorhanden sind
        # Einfache Prüfung: Wenn das letzte Zeichen nicht Komma oder geschlossene Klammer ist, wurde der String möglicherweise abgeschnitten
        if content and content[-1] not in '",}]':
            # Versuche, String zu schließen
            content += '"'
        
        # Klammern schließen
        content += ']' * open_brackets
        content += '}' * open_braces
        
        return content
    
    def _try_fix_json(self, content: str, entity_name: str, entity_type: str, entity_summary: str = "") -> Dict[str, Any]:
        """Versucht, beschädigtes JSON zu reparieren"""
        import re
        
        # 1. Zuerst abgeschnittene Fälle reparieren
        content = self._fix_truncated_json(content)
        
        # 2. Versuche, JSON-Teil zu extrahieren
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            json_str = json_match.group()
            
            # 3. Zeilenumbruch-Probleme in Strings behandeln
            # Alle String-Werte finden und Zeilenumbrüche darin ersetzen
            def fix_string_newlines(match):
                s = match.group(0)
                # Tatsächliche Zeilenumbrüche im String durch Leerzeichen ersetzen
                s = s.replace('\n', ' ').replace('\r', ' ')
                # Überflüssige Leerzeichen reduzieren
                s = re.sub(r'\s+', ' ', s)
                return s
            
            # JSON-String-Werte matchen
            json_str = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', fix_string_newlines, json_str)
            
            # 4. Parsing versuchen
            try:
                result = json.loads(json_str)
                result["_fixed"] = True
                return result
            except json.JSONDecodeError as e:
                # 5. Wenn immer noch fehlschlägt, aggressivere Reparatur versuchen
                try:
                    # Alle Steuerzeichen entfernen
                    json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', json_str)
                    # Alle zusammenhängenden Leerzeichen ersetzen
                    json_str = re.sub(r'\s+', ' ', json_str)
                    result = json.loads(json_str)
                    result["_fixed"] = True
                    return result
                except:
                    pass
        
        # 6. Versuche, Teile der Informationen aus dem Inhalt zu extrahieren
        bio_match = re.search(r'"bio"\s*:\s*"([^"]*)"', content)
        persona_match = re.search(r'"persona"\s*:\s*"([^"]*)', content)  # Möglicherweise abgeschnitten
        
        bio = bio_match.group(1) if bio_match else (entity_summary[:200] if entity_summary else f"{entity_type}: {entity_name}")
        persona = persona_match.group(1) if persona_match else (entity_summary or f"{entity_name} ist ein {entity_type}.")
        
        # Wenn aussagekräftige Inhalte extrahiert wurden, als repariert markieren
        if bio_match or persona_match:
            logger.info(f"Teilinformationen aus beschädigtem JSON extrahiert")
            return {
                "bio": bio,
                "persona": persona,
                "_fixed": True
            }
        
        # 7. Vollständiger Fehler, Basisstruktur zurückgeben
        logger.warning(f"JSON-Reparatur fehlgeschlagen, gebe Basisstruktur zurück")
        return {
            "bio": entity_summary[:200] if entity_summary else f"{entity_type}: {entity_name}",
            "persona": entity_summary or f"{entity_name} ist ein {entity_type}."
        }
    
    def _get_system_prompt(self, is_individual: bool) -> str:
        """System-Prompt abrufen"""
        base_prompt = "Du bist ein Experte für Social-Media-Benutzerprofil-Generierung. Erstelle detaillierte, realistische Profile für die öffentlichkeitswirksame Simulation und stelle die realen Gegebenheiten maximal dar. Muss gültiges JSON-Format zurückgeben, alle String-Werte dürfen keine nicht-escaped Zeilenumbrüche enthalten. Verwende Deutsch."
        return base_prompt
    
    def _build_individual_persona_prompt(
        self,
        entity_name: str,
        entity_type: str,
        entity_summary: str,
        entity_attributes: Dict[str, Any],
        context: str
    ) -> str:
        """Detaillierten Persona-Prompt für individuelle Entitäten aufbauen"""
        
        attrs_str = json.dumps(entity_attributes, ensure_ascii=False) if entity_attributes else "Keine"
        context_str = context[:3000] if context else "Kein zusätzlicher Kontext"
        
        return f"""Generiere ein detailliertes Social-Media-Benutzerprofil für die Entität, stelle die realen Gegebenheiten maximal dar.

Entitätsname: {entity_name}
Entitätstyp: {entity_type}
Entitätszusammenfassung: {entity_summary}
Entitätsattribute: {attrs_str}

Kontextinformationen:
{context_str}

Bitte generiere JSON mit folgenden Feldern:

1. bio: Social-Media-Bio, 200 Zeichen
2. persona: Detaillierte Profilbeschreibung (2000 Zeichen reiner Text), muss enthalten:
   - Grundinformationen (Alter, Beruf, Bildungshintergrund, Wohnort)
   - Hintergrund (wichtige Erfahrungen, Verbindung zu Ereignissen, soziale Beziehungen)
   - Persönlichkeitsmerkmale (MBTI-Typ, Kernpersönlichkeit, Emotionsausdrucksweise)
   - Social-Media-Verhalten (Posting-Frequenz, Inhaltspräferenz, Interaktionsstil, Sprachmerkmale)
   - Standpunkt (Einstellung zu Themen, was die Person verärgern/bewegen könnte)
   - Besondere Merkmale (Ausrufe, besondere Erfahrungen, persönliche Hobbys)
   - Persönliche Erinnerungen (wichtiger Teil des Profils: Verbindung der Person zu Ereignissen und bisherige Handlungen/Reaktionen in Ereignissen)
3. age: Alterszahl (muss Ganzzahl sein)
4. gender: Geschlecht, muss Englisch sein: "male" oder "female"
5. mbti: MBTI-Typ (z.B. INTJ, ENFP usw.)
6. country: Land (verwende Deutsch, z.B. "Deutschland")
7. profession: Beruf
8. interested_topics: Array interessierter Themen

Wichtig:
- Alle Feldwerte müssen Strings oder Zahlen sein, keine Zeilenumbrüche verwenden
- Persona muss ein zusammenhängender Text sein
- Verwende Deutsch (außer gender-Feld muss Englisch male/female sein)
- Inhalt muss mit Entitätsinformationen übereinstimmen
- Age muss gültige Ganzzahl sein, gender muss "male" oder "female" sein
"""

    def _build_group_persona_prompt(
        self,
        entity_name: str,
        entity_type: str,
        entity_summary: str,
        entity_attributes: Dict[str, Any],
        context: str
    ) -> str:
        """Detaillierten Persona-Prompt für Gruppen-/Institutionen aufbauen"""
        
        attrs_str = json.dumps(entity_attributes, ensure_ascii=False) if entity_attributes else "Keine"
        context_str = context[:3000] if context else "Kein zusätzlicher Kontext"
        
        return f"""Generiere ein detailliertes Social-Media-Konto-Setup für eine Institution/Gruppen-Entität, stelle die realen Gegebenheiten maximal dar.

Entitätsname: {entity_name}
Entitätstyp: {entity_type}
Entitätszusammenfassung: {entity_summary}
Entitätsattribute: {attrs_str}

Kontextinformationen:
{context_str}

Bitte generiere JSON mit folgenden Feldern:

1. bio: Offizielles Konto-Bio, 200 Zeichen, professionell und angemessen
2. persona: Detaillierte Konto-Setup-Beschreibung (2000 Zeichen reiner Text), muss enthalten:
   - Institutionelle Grundinformationen (offizieller Name, Art der Institution, Gründungshintergrund, Hauptaufgaben)
   - Kontopositionierung (Kontotyp, Zielpublikum, Kernfunktionen)
   - Sprechstil (Sprachmerkmale, häufige Ausdrücke, Tabuthemen)
   - Inhaltsmerkmale (Inhaltstypen, Veröffentlichungsfrequenz, aktive Zeitfenster)
   - Standpunkt (offizielle Position zu Kernthemen, Umgang mit Kontroversen)
   - Besondere Hinweise (repräsentierte Gruppenprofile, Betriebsgewohnheiten)
   - Institutionelle Erinnerungen (wichtiger Teil des Institutionen-Profils: Verbindung der Institution zu Ereignissen und bisherige Handlungen/Reaktionen in Ereignissen)
3. age: Fest 30 (virtuelles Alter des Institutskontos)
4. gender: Fest "other" (Institutskonten verwenden other für Nicht-Personen)
5. mbti: MBTI-Typ, zur Beschreibung des Kontostils, z.B. ISTJ für streng/konservativ
6. country: Land (verwende Deutsch, z.B. "Deutschland")
7. profession: Beschreibung der institutionellen Funktionen
8. interested_topics: Array der Aufmerksamkeitsbereiche

Wichtig:
- Alle Feldwerte müssen Strings oder Zahlen sein, keine Nullwerte erlaubt
- Persona muss ein zusammenhängender Text sein, keine Zeilenumbrüche verwenden
- Verwende Deutsch (außer gender-Feld muss Englisch "other" sein)
- Age muss Ganzzahl 30 sein, gender muss String "other" sein
- Institutskonto-Äußerungen müssen der Identitätsposition entsprechen"""
    
    def _generate_profile_rule_based(
        self,
        entity_name: str,
        entity_type: str,
        entity_summary: str,
        entity_attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Basisprofil mit Regeln generieren"""
        
        # Je nach Entitätstyp unterschiedliche Profile generieren
        entity_type_lower = entity_type.lower()
        
        if entity_type_lower in ["student", "alumni"]:
            return {
                "bio": f"{entity_type} with interests in academics and social issues.",
                "persona": f"{entity_name} is a {entity_type.lower()} who is actively engaged in academic and social discussions. They enjoy sharing perspectives and connecting with peers.",
                "age": random.randint(18, 30),
                "gender": random.choice(["male", "female"]),
                "mbti": random.choice(self.MBTI_TYPES),
                "country": random.choice(self.COUNTRIES),
                "profession": "Student",
                "interested_topics": ["Education", "Social Issues", "Technology"],
            }
        
        elif entity_type_lower in ["publicfigure", "expert", "faculty"]:
            return {
                "bio": f"Expert and thought leader in their field.",
                "persona": f"{entity_name} is a recognized {entity_type.lower()} who shares insights and opinions on important matters. They are known for their expertise and influence in public discourse.",
                "age": random.randint(35, 60),
                "gender": random.choice(["male", "female"]),
                "mbti": random.choice(["ENTJ", "INTJ", "ENTP", "INTP"]),
                "country": random.choice(self.COUNTRIES),
                "profession": entity_attributes.get("occupation", "Expert"),
                "interested_topics": ["Politics", "Economics", "Culture & Society"],
            }
        
        elif entity_type_lower in ["mediaoutlet", "socialmediaplatform"]:
            return {
                "bio": f"Official account for {entity_name}. News and updates.",
                "persona": f"{entity_name} is a media entity that reports news and facilitates public discourse. The account shares timely updates and engages with the audience on current events.",
                "age": 30,  # Virtuelles Alter der Institution
                "gender": "other",  # Institution verwendet other
                "mbti": "ISTJ",  # Institutsstil: streng/konservativ
                "country": "Deutschland",
                "profession": "Media",
                "interested_topics": ["General News", "Current Events", "Public Affairs"],
            }
        
        elif entity_type_lower in ["university", "governmentagency", "ngo", "organization"]:
            return {
                "bio": f"Official account of {entity_name}.",
                "persona": f"{entity_name} is an institutional entity that communicates official positions, announcements, and engages with stakeholders on relevant matters.",
                "age": 30,  # Virtuelles Alter der Institution
                "gender": "other",  # Institution verwendet other
                "mbti": "ISTJ",  # Institutsstil: streng/konservativ
                "country": "Deutschland",
                "profession": entity_type,
                "interested_topics": ["Public Policy", "Community", "Official Announcements"],
            }
        
        else:
            # Standardprofil
            return {
                "bio": entity_summary[:150] if entity_summary else f"{entity_type}: {entity_name}",
                "persona": entity_summary or f"{entity_name} is a {entity_type.lower()} participating in social discussions.",
                "age": random.randint(25, 50),
                "gender": random.choice(["male", "female"]),
                "mbti": random.choice(self.MBTI_TYPES),
                "country": random.choice(self.COUNTRIES),
                "profession": entity_type,
                "interested_topics": ["General", "Social Issues"],
            }
    
    def set_graph_id(self, graph_id: str):
        """Graphen-ID für Zep-Retrieval setzen"""
        self.graph_id = graph_id
    
    def generate_profiles_from_entities(
        self,
        entities: List[EntityNode],
        use_llm: bool = True,
        progress_callback: Optional[callable] = None,
        graph_id: Optional[str] = None,
        parallel_count: int = 5,
        realtime_output_path: Optional[str] = None,
        output_platform: str = "reddit"
    ) -> List[OasisAgentProfile]:
        """
        Batch-Generierung von Agent-Profilen aus Entitäten (unterstützt parallele Generierung)
        
        Args:
            entities: Entitätsliste
            use_llm: Ob LLM für detaillierte Profilerstellung verwendet werden soll
            progress_callback: Fortschritts-Callback-Funktion (current, total, message)
            graph_id: Graphen-ID für Zep-Retrieval zur Anreicherung mit mehr Kontext
            parallel_count: Anzahl paralleler Generierungen, Standard 5
            realtime_output_path: Echtzeit-Schreibpfad (falls angegeben, nach jeder Generierung einmal schreiben)
            output_platform: Ausgabeplattformformat ("reddit" oder "twitter")
            
        Returns:
            Agent Profile Liste
        """
        import concurrent.futures
        from threading import Lock
        
        # graph_id für Zep-Retrieval setzen
        if graph_id:
            self.graph_id = graph_id
        
        total = len(entities)
        profiles = [None] * total  # Liste vorauszuweisen, um Reihenfolge zu erhalten
        completed_count = [0]  # Liste verwenden, um in Closure modifizierbar zu sein
        lock = Lock()
        
        # Hilfsfunktion für Echtzeitspeicherung in Datei
        def save_profiles_realtime():
            """Generierte Profiles in Echtzeit in Datei speichern"""
            if not realtime_output_path:
                return
            
            with lock:
                # Bereits generierte Profiles filtern
                existing_profiles = [p for p in profiles if p is not None]
                if not existing_profiles:
                    return
                
                try:
                    if output_platform == "reddit":
                        # Reddit JSON-Format
                        profiles_data = [p.to_reddit_format() for p in existing_profiles]
                        with open(realtime_output_path, 'w', encoding='utf-8') as f:
                            json.dump(profiles_data, f, ensure_ascii=False, indent=2)
                    else:
                        # Twitter CSV-Format
                        import csv
                        profiles_data = [p.to_twitter_format() for p in existing_profiles]
                        if profiles_data:
                            fieldnames = list(profiles_data[0].keys())
                            with open(realtime_output_path, 'w', encoding='utf-8', newline='') as f:
                                writer = csv.DictWriter(f, fieldnames=fieldnames)
                                writer.writeheader()
                                writer.writerows(profiles_data)
                except Exception as e:
                    logger.warning(f"Echtzeitspeicherung der Profiles fehlgeschlagen: {e}")
        
        def generate_single_profile(idx: int, entity: EntityNode) -> tuple:
            """Arbeitsfunktion für einzelne Profilgenerierung"""
            entity_type = entity.get_entity_type() or "Entity"
            
            try:
                profile = self.generate_profile_from_entity(
                    entity=entity,
                    user_id=idx,
                    use_llm=use_llm
                )
                
                # Generiertes Profil in Echtzeit an Konsole und Log ausgeben
                self._print_generated_profile(entity.name, entity_type, profile)
                
                return idx, profile, None
                
            except Exception as e:
                logger.error(f"Profilgenerierung für Entität {entity.name} fehlgeschlagen: {str(e)}")
                # Basisprofil erstellen
                fallback_profile = OasisAgentProfile(
                    user_id=idx,
                    user_name=self._generate_username(entity.name),
                    name=entity.name,
                    bio=f"{entity_type}: {entity.name}",
                    persona=entity.summary or f"A participant in social discussions.",
                    source_entity_uuid=entity.uuid,
                    source_entity_type=entity_type,
                )
                return idx, fallback_profile, str(e)
        
        logger.info(f"Beginne parallele Generierung von {total} Agent-Profilen (Parallelität: {parallel_count})...")
        print(f"\n{'='*60}")
        print(f"Beginne Agent-Profil-Generierung - Insgesamt {total} Entitäten, Parallelität: {parallel_count}")
        print(f"{'='*60}\n")
        
        # Thread-Pool für parallele Ausführung verwenden
        with concurrent.futures.ThreadPoolExecutor(max_workers=parallel_count) as executor:
            # Alle Tasks übermitteln
            future_to_entity = {
                executor.submit(generate_single_profile, idx, entity): (idx, entity)
                for idx, entity in enumerate(entities)
            }
            
            # Ergebnisse sammeln
            for future in concurrent.futures.as_completed(future_to_entity):
                idx, entity = future_to_entity[future]
                entity_type = entity.get_entity_type() or "Entity"
                
                try:
                    result_idx, profile, error = future.result()
                    profiles[result_idx] = profile
                    
                    with lock:
                        completed_count[0] += 1
                        current = completed_count[0]
                    
                    # Echtzeitspeicherung in Datei
                    save_profiles_realtime()
                    
                    if progress_callback:
                        progress_callback(
                            current, 
                            total, 
                            f"Abgeschlossen {current}/{total}: {entity.name} ({entity_type})"
                        )
                    
                    if error:
                        logger.warning(f"[{current}/{total}] {entity.name} verwendet Fallback-Profil: {error}")
                    else:
                        logger.info(f"[{current}/{total}] Profil erfolgreich generiert: {entity.name} ({entity_type})")
                        
                except Exception as e:
                    logger.error(f"Ausnahme bei der Verarbeitung der Entität {entity.name}: {str(e)}")
                    with lock:
                        completed_count[0] += 1
                    profiles[idx] = OasisAgentProfile(
                        user_id=idx,
                        user_name=self._generate_username(entity.name),
                        name=entity.name,
                        bio=f"{entity_type}: {entity.name}",
                        persona=entity.summary or "A participant in social discussions.",
                        source_entity_uuid=entity.uuid,
                        source_entity_type=entity_type,
                    )
                    # Echtzeitspeicherung in Datei (auch für Fallback-Profil)
                    save_profiles_realtime()
        
        print(f"\n{'='*60}")
        print(f"Profilgenerierung abgeschlossen! Insgesamt {len([p for p in profiles if p])} Agents generiert")
        print(f"{'='*60}\n")
        
        return profiles
    
    def _print_generated_profile(self, entity_name: str, entity_type: str, profile: OasisAgentProfile):
        """Generiertes Profil in Echtzeit an Konsole ausgeben (vollständiger Inhalt, nicht abgeschnitten)"""
        separator = "-" * 70
        
        # Vollständigen Ausgabeinhalt aufbauen (nicht abschneiden)
        topics_str = ', '.join(profile.interested_topics) if profile.interested_topics else 'Keine'
        
        output_lines = [
            f"\n{separator}",
            f"[Generiert] {entity_name} ({entity_type})",
            f"{separator}",
            f"Benutzername: {profile.user_name}",
            f"",
            f"【Bio】",
            f"{profile.bio}",
            f"",
            f"【Detailliertes Profil】",
            f"{profile.persona}",
            f"",
            f"【Grundattribute】",
            f"Alter: {profile.age} | Geschlecht: {profile.gender} | MBTI: {profile.mbti}",
            f"Beruf: {profile.profession} | Land: {profile.country}",
            f"Interessenthemen: {topics_str}",
            separator
        ]
        
        output = "\n".join(output_lines)
        
        # Nur an Konsole ausgeben (Vermeidung von Duplikaten, Logger gibt keinen vollständigen Inhalt aus)
        print(output)
    
    def save_profiles(
        self,
        profiles: List[OasisAgentProfile],
        file_path: str,
        platform: str = "reddit"
    ):
        """
        Profile in Datei speichern (basierend auf Plattform das richtige Format wählen)
        
        OASIS-Plattformformat-Anforderungen:
        - Twitter: CSV-Format
        - Reddit: JSON-Format
        
        Args:
            profiles: Profile-Liste
            file_path: Dateipfad
            platform: Plattformtyp ("reddit" oder "twitter")
        """
        if platform == "twitter":
            self._save_twitter_csv(profiles, file_path)
        else:
            self._save_reddit_json(profiles, file_path)
    
    def _save_twitter_csv(self, profiles: List[OasisAgentProfile], file_path: str):
        """
        Twitter-Profile als CSV-Format speichern (entspricht OASIS-Offizielleanforderungen)
        
        OASIS Twitter erfordert CSV-Felder:
        - user_id: Benutzer-ID (beginnt bei 0 basierend auf CSV-Reihenfolge)
        - name: Echter Benutzername
        - username: Benutzername im System
        - user_char: Detaillierte Profilbeschreibung (injiziert in LLM-System-Prompt, steuert Agent-Verhalten)
        - description: Kurze öffentliche Bio (wird auf Benutzerprofilseite angezeigt)
        
        Unterschied user_char vs description:
        - user_char: Interne Verwendung, LLM-System-Prompt, bestimmt wie Agent denkt und handelt
        - description: Externe Anzeige, Bio für andere Benutzer sichtbar
        """
        import csv
        
        # Sicherstellen, dass Dateierweiterung .csv ist
        if not file_path.endswith('.csv'):
            file_path = file_path.replace('.json', '.csv')
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # OASIS-erforderte Header schreiben
            headers = ['user_id', 'name', 'username', 'user_char', 'description']
            writer.writerow(headers)
            
            # Datenzeilen schreiben
            for idx, profile in enumerate(profiles):
                # user_char: Vollständiges Profil (bio + persona), für LLM-System-Prompt
                user_char = profile.bio
                if profile.persona and profile.persona != profile.bio:
                    user_char = f"{profile.bio} {profile.persona}"
                # Zeilenumbrüche behandeln (im CSV durch Leerzeichen ersetzen)
                user_char = user_char.replace('\n', ' ').replace('\r', ' ')
                
                # description: Kurze Bio, für externe Anzeige
                description = profile.bio.replace('\n', ' ').replace('\r', ' ')
                
                row = [
                    idx,                    # user_id: Sequentielle ID beginnend bei 0
                    profile.name,           # name: Echter Name
                    profile.user_name,      # username: Benutzername
                    user_char,              # user_char: Vollständiges Profil (interne LLM-Verwendung)
                    description             # description: Kurze Bio (externe Anzeige)
                ]
                writer.writerow(row)
        
        logger.info(f"{len(profiles)} Twitter-Profile gespeichert nach {file_path} (OASIS CSV-Format)")
    
    def _normalize_gender(self, gender: Optional[str]) -> str:
        """
        Gender-Feld in OASIS-erfordertes Englisch-Format normalisieren
        
        OASIS erfordert: male, female, other
        """
        if not gender:
            return "other"
        
        gender_lower = gender.lower().strip()
        
        # Deutsch-Zuordnung
        gender_map = {
            "männlich": "male",
            "weiblich": "female",
            "institution": "other",
            "andere": "other",
            # Englisch bereits vorhanden
            "male": "male",
            "female": "female",
            "other": "other",
        }
        
        return gender_map.get(gender_lower, "other")
    
    def _save_reddit_json(self, profiles: List[OasisAgentProfile], file_path: str):
        """
        Reddit-Profile als JSON-Format speichern
        
        Verwendet Format konsistent mit to_reddit_format(), stellt sicher, dass OASIS korrekt lesen kann.
        Muss user_id-Feld enthalten, das ist der Schlüssel für OASIS agent_graph.get_agent()!
        
        Erforderliche Felder:
        - user_id: Benutzer-ID (Ganzzahl, für Matching mit initial_posts poster_agent_id)
        - username: Benutzername
        - name: Anzeigename
        - bio: Bio
        - persona: Detailliertes Profil
        - age: Alter (Ganzzahl)
        - gender: "male", "female" oder "other"
        - mbti: MBTI-Typ
        - country: Land
        """
        data = []
        for idx, profile in enumerate(profiles):
            # Format konsistent mit to_reddit_format()
            item = {
                "user_id": profile.user_id if profile.user_id is not None else idx,  # Wichtig: Muss user_id enthalten
                "username": profile.user_name,
                "name": profile.name,
                "bio": profile.bio[:150] if profile.bio else f"{profile.name}",
                "persona": profile.persona or f"{profile.name} is a participant in social discussions.",
                "karma": profile.karma if profile.karma else 1000,
                "created_at": profile.created_at,
                # OASIS-erforderliche Felder - Stelle sicher, dass alle Standardwerte haben
                "age": profile.age if profile.age else 30,
                "gender": self._normalize_gender(profile.gender),
                "mbti": profile.mbti if profile.mbti else "ISTJ",
                "country": profile.country if profile.country else "Deutschland",
            }
            
            # Optionale Felder
            if profile.profession:
                item["profession"] = profile.profession
            if profile.interested_topics:
                item["interested_topics"] = profile.interested_topics
            
            data.append(item)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"{len(profiles)} Reddit-Profile gespeichert nach {file_path} (JSON-Format, enthält user_id-Feld)")
    
    # Alten Methodennamen als Alias beibehalten, Abwärtskompatibilität sicherstellen
    def save_profiles_to_json(
        self,
        profiles: List[OasisAgentProfile],
        file_path: str,
        platform: str = "reddit"
    ):
        """[Veraltet] Bitte verwenden Sie die Methode save_profiles()"""
        logger.warning("save_profiles_to_json ist veraltet, bitte verwenden Sie die Methode save_profiles")
        self.save_profiles(profiles, file_path, platform)
