"""
Obsidian-Markdown-Memory-Provider
Speichert den Wissensgraphen lokal als Markdown-Dateien in einer Obsidian-Vault-Struktur
"""

import os
import hashlib
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import asdict

from .base import MemoryProvider, MemoryNode, MemoryEdge, MemorySearchResult
from ...config import Config
from ...utils.logger import get_logger
from ...utils.llm_client import LLMClient

logger = get_logger('mirofish.memory.obsidian')

class ObsidianMemoryProvider(MemoryProvider):
    """Memory-Provider für lokale Markdown-Dateien (Obsidian-kompatibel)"""
    
    def __init__(self, vault_root: Optional[str] = None):
        # Basis-Verzeichnis für Vaults
        self.base_root = vault_root or os.path.join(Config.UPLOAD_FOLDER, 'simulations')
        self._llm_client = None # Lazy loading

    @property
    def llm(self) -> LLMClient:
        if self._llm_client is None:
            self._llm_client = LLMClient()
        return self._llm_client

    def _get_vault_path(self, graph_id: str) -> str:
        """Pfad zum spezifischen Vault für diesen Graphen/Simulation"""
        # Wenn graph_id eine simulation_id enthält (z.B. sim_...)
        return os.path.join(self.base_root, graph_id, 'vault')

    def initialize(self, simulation_id: str, graph_name: str = "MiroFish Graph") -> str:
        """Initialisiert die Ordnerstruktur für den Obsidian Vault"""
        vault_path = self._get_vault_path(simulation_id)
        subdirs = ['agents', 'events', 'orgs', 'relations', 'episodes', 'index']
        
        for sd in subdirs:
            os.makedirs(os.path.join(vault_path, sd), exist_ok=True)
            
        # Index-Datei erstellen
        index_file = os.path.join(vault_path, 'index', 'graph_info.json')
        if not os.path.exists(index_file):
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "id": simulation_id,
                    "name": graph_name,
                    "created_at": datetime.now().isoformat(),
                    "provider": "obsidian"
                }, f, indent=2)
                
        return simulation_id # Bei Obsidian ist graph_id = simulation_id

    def set_ontology(self, graph_id: str, ontology: Dict[str, Any]):
        """Speichert die Ontologie im Vault"""
        vault_path = self._get_vault_path(graph_id)
        with open(os.path.join(vault_path, 'index', 'ontology.json'), 'w', encoding='utf-8') as f:
            json.dump(ontology, f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------ Extraktion (lokal, mit Toren)
    EXTRACT_SYSTEM = (
        "Du extrahierst aus einem deutschen Text einen Wissensgraphen. Antworte NUR mit einem JSON-Objekt der Form "
        '{"entities": [{"name": "...", "type": "<EntityType>", "summary": "ein Satz", "attributes": {}}], '
        '"relations": [{"source": "<Entity-Name>", "target": "<Entity-Name>", "type": "<EdgeType>", "fact": "ein Satz"}]}. '
        "Erlaubt sind nur die genannten Typen. Namen kurz und eindeutig (z. B. 'Einzelhandelsverband', 'Oberbürgermeister'), "
        "Zusammenfassungen und Fakten auf Deutsch, nur Inhalte aus dem Text, nichts erfinden."
    )

    @staticmethod
    def _uuid_for(entity_type: str, name: str) -> str:
        return hashlib.sha1(f"{entity_type.lower()}|{name.strip().lower()}".encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _safe(name: str) -> str:
        return re.sub(r'[\\/*?:"<>|]', "", name).strip().replace(" ", "_")[:80] or "unbenannt"

    def _ontology(self, vault_path: str) -> Dict[str, Any]:
        path = os.path.join(vault_path, 'index', 'ontology.json')
        if not os.path.exists(path):
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _extract(self, text: str, entity_types: List[str], edge_types: List[str]) -> Dict[str, Any]:
        """Ein LLM-Aufruf, ein Reparaturversuch; alles weitere entscheiden die Tore in add_text."""
        user = (f"Entitätstypen: {', '.join(entity_types) or 'Person, Organisation, Ereignis, Thema'}\n"
                f"Beziehungstypen: {', '.join(edge_types) or 'bezieht_sich_auf'}\n\nTEXT:\n{text}")
        messages = [{"role": "system", "content": self.EXTRACT_SYSTEM}, {"role": "user", "content": user}]
        for attempt in range(2):
            try:
                result = self.llm.chat_json(messages, temperature=0.1, max_tokens=3000)
                if isinstance(result, dict) and isinstance(result.get("entities"), list):
                    return result
            except Exception as e:
                logger.warning(f"ObsidianProvider: Extraktion Versuch {attempt + 1} fehlgeschlagen: {e}")
        return {"entities": [], "relations": []}

    def add_text(self, graph_id: str, text: str, metadata: Dict[str, Any] = None) -> str:
        """Speichert die Episode und extrahiert Entitäten und Beziehungen per LLM in den Vault.

        Tore (deterministisch): Typ muss in der Ontologie stehen, Name nicht leer, Beziehung nur zwischen bekannten
        Entitäten; gleiche (Typ, Name) werden zusammengeführt (uuid = sha1(Typ|Name))."""
        vault_path = self._get_vault_path(graph_id)
        os.makedirs(os.path.join(vault_path, 'episodes'), exist_ok=True)
        os.makedirs(os.path.join(vault_path, 'entities'), exist_ok=True)
        os.makedirs(os.path.join(vault_path, 'relations'), exist_ok=True)

        episode_id = f"ep_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"
        with open(os.path.join(vault_path, 'episodes', f"{episode_id}.md"), 'w', encoding='utf-8') as f:
            f.write(f"---\nid: {episode_id}\ndate: {datetime.now().isoformat()}\n---\n\n{text}")

        ontology = self._ontology(vault_path)
        entity_types = [e.get("name") for e in ontology.get("entity_types", []) if e.get("name")]
        edge_types = [e.get("name") for e in ontology.get("edge_types", []) if e.get("name")]
        type_lookup = {t.lower(): t for t in entity_types}
        edge_lookup = {t.lower(): t for t in edge_types}

        result = self._extract(text, entity_types, edge_types)
        known = {n.uuid: n for n in self.fetch_nodes(graph_id)}
        by_name = {n.name.lower(): n.uuid for n in known.values()}
        kept_e = dropped_e = kept_r = dropped_r = 0

        for ent in result.get("entities", []):
            if not isinstance(ent, dict):
                dropped_e += 1; continue
            name = str(ent.get("name") or "").strip()
            etype = type_lookup.get(str(ent.get("type") or "").strip().lower()) if entity_types else str(ent.get("type") or "Entity")
            if not name or not etype:
                dropped_e += 1; continue
            uuid = self._uuid_for(etype, name)
            summary = str(ent.get("summary") or "").strip()
            attrs = ent.get("attributes") if isinstance(ent.get("attributes"), dict) else {}
            folder = os.path.join(vault_path, 'entities', self._safe(etype))
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, f"{uuid}.md")
            if os.path.exists(path):
                with open(path, 'r+', encoding='utf-8') as f:
                    if summary and f"- {summary}\n" not in f.read():
                        f.write(f"- {summary}\n")
            else:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(f"---\nuuid: {uuid}\nname: {name}\ntype: {etype}\nattributes: {json.dumps(attrs, ensure_ascii=False)}\n---\n\n"
                            f"# {name}\n\n## Zusammenfassung\n{summary}\n\n## Fakten\n")
            known[uuid] = MemoryNode(uuid=uuid, name=name, labels=[etype], summary=summary, attributes=attrs)
            by_name[name.lower()] = uuid
            kept_e += 1

        for rel in result.get("relations", []):
            if not isinstance(rel, dict):
                dropped_r += 1; continue
            src = by_name.get(str(rel.get("source") or "").strip().lower())
            dst = by_name.get(str(rel.get("target") or "").strip().lower())
            fact = str(rel.get("fact") or "").strip()
            rtype = edge_lookup.get(str(rel.get("type") or "").strip().lower()) if edge_types else str(rel.get("type") or "related_to")
            if not (src and dst and fact and rtype) or src == dst:
                dropped_r += 1; continue
            ruuid = hashlib.sha1(f"{src}|{rtype}|{dst}|{fact.lower()}".encode("utf-8")).hexdigest()[:16]
            rpath = os.path.join(vault_path, 'relations', f"{ruuid}.json")
            if not os.path.exists(rpath):
                with open(rpath, 'w', encoding='utf-8') as f:
                    json.dump({"uuid": ruuid, "name": rtype, "fact": fact, "source_node_uuid": src, "target_node_uuid": dst,
                               "attributes": {"episode": episode_id}, "created_at": datetime.now().isoformat()}, f,
                              ensure_ascii=False, indent=2)
            for node_uuid in (src, dst):  # Fakt auch in die Entitätsdatei, damit die Keyword-Suche ihn findet
                node = known.get(node_uuid)
                if node:
                    npath = os.path.join(vault_path, 'entities', self._safe(node.labels[0]), f"{node_uuid}.md")
                    if os.path.exists(npath):
                        with open(npath, 'r+', encoding='utf-8') as f:
                            if f"- {fact}\n" not in f.read():
                                f.write(f"- {fact}\n")
            kept_r += 1

        logger.info(f"ObsidianProvider: Episode {episode_id}: {kept_e} Entitäten ({dropped_e} verworfen), "
                    f"{kept_r} Beziehungen ({dropped_r} verworfen)")
        return episode_id

    def add_activity(self, graph_id: str, agent_name: str, activity_desc: str):
        """Ergänzt die Aktivität in der Agenten-Datei oder einem globalen Log"""
        vault_path = self._get_vault_path(graph_id)
        
        # Agenten-Dateinamen sanitisieren
        safe_name = re.sub(r'[\\/*?:"<>|]', "", agent_name).replace(" ", "_")
        agent_file = os.path.join(vault_path, 'agents', f"{safe_name}.md")
        
        mode = 'a' if os.path.exists(agent_file) else 'w'
        with open(agent_file, mode, encoding='utf-8') as f:
            if mode == 'w':
                f.write(f"---\nname: {agent_name}\ntype: agent\n---\n\n# {agent_name}\n\n## Aktivitäten\n")
            f.write(f"- [{datetime.now().strftime('%H:%M:%S')}] {activity_desc}\n")

    @staticmethod
    def _read_entity_file(path: str, fallback_type: str) -> Optional[MemoryNode]:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        meta = {}
        m = re.match(r"---\n(.*?)\n---\n", content, re.S)
        if m:
            for line in m.group(1).splitlines():
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip()
        try:
            attrs = json.loads(meta.get("attributes", "{}"))
        except Exception:
            attrs = {}
        body = content[m.end():] if m else content
        sm = re.search(r"## Zusammenfassung\n(.*?)(?:\n## |\Z)", body, re.S)
        summary = (sm.group(1).strip() if sm else body.strip()[:500])
        facts = re.findall(r"^- (.+)$", body, re.M)
        if facts:
            summary = (summary + " " + " ".join(facts[:8])).strip()
        uuid = meta.get("uuid") or os.path.basename(path)[:-3]
        return MemoryNode(uuid=uuid, name=meta.get("name") or os.path.basename(path)[:-3].replace("_", " "),
                          labels=[meta.get("type") or fallback_type], summary=summary, attributes=attrs,
                          created_at=meta.get("date"))

    def fetch_nodes(self, graph_id: str) -> List[MemoryNode]:
        """Entitäten aus entities/<Typ>/*.md (Frontmatter) plus die alten Ordner agents/, orgs/, events/"""
        vault_path = self._get_vault_path(graph_id)
        nodes: List[MemoryNode] = []
        ent_root = os.path.join(vault_path, 'entities')
        if os.path.isdir(ent_root):
            for etype in sorted(os.listdir(ent_root)):
                tdir = os.path.join(ent_root, etype)
                if not os.path.isdir(tdir):
                    continue
                for file in sorted(os.listdir(tdir)):
                    if file.endswith('.md'):
                        nodes.append(self._read_entity_file(os.path.join(tdir, file), etype))
        for folder in ['agents', 'orgs', 'events']:
            folder_path = os.path.join(vault_path, folder)
            if not os.path.exists(folder_path):
                continue
            for file in os.listdir(folder_path):
                if file.endswith('.md'):
                    nodes.append(MemoryNode(uuid=file[:-3], name=file[:-3].replace("_", " "),
                                            labels=[folder.rstrip('s').capitalize()],
                                            summary=f"Dokumentierte Entität in {folder}"))
        return nodes

    def fetch_edges(self, graph_id: str) -> List[MemoryEdge]:
        """Liest Relationen (aktuell rudimentär aus relations/ Ordner)"""
        vault_path = self._get_vault_path(graph_id)
        edges = []
        rel_path = os.path.join(vault_path, 'relations')
        if not os.path.exists(rel_path): return []
        
        for file in os.listdir(rel_path):
            if file.endswith('.json'):
                try:
                    with open(os.path.join(rel_path, file), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        edges.append(MemoryEdge(**data))
                except Exception:
                    pass
        return edges

    def fetch_node_edges(self, graph_id: str, node_uuid: str) -> List[MemoryEdge]:
        """Filtert alle Kanten für einen bestimmten Knoten"""
        all_edges = self.fetch_edges(graph_id)
        return [e for e in all_edges if e.source_node_uuid == node_uuid or e.target_node_uuid == node_uuid]

    def search(self, graph_id: str, query: str, limit: int = 10, scope: str = "edges") -> MemorySearchResult:
        """Einfache Keyword-Suche in allen Markdown-Dateien"""
        vault_path = self._get_vault_path(graph_id)
        results = []
        query_lower = query.lower()
        
        # Durchsuche Episoden und Agenten
        for root, _, files in os.walk(vault_path):
            for file in files:
                if file.endswith('.md'):
                    path = os.path.join(root, file)
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if query_lower in content.lower():
                            # Einen Ausschnitt als Fakt extrahieren
                            lines = content.split('\n')
                            for line in lines:
                                if query_lower in line.lower() and len(line.strip()) > 10:
                                    results.append(line.strip())
                                    if len(results) >= limit: break
                if len(results) >= limit: break
            if len(results) >= limit: break
            
        return MemorySearchResult(
            query=query,
            facts=results,
            total_count=len(results)
        )

    def get_node_detail(self, graph_id: str, node_uuid: str) -> Optional[MemoryNode]:
        """Details einer Entität (neuer und alter Vault-Aufbau)"""
        for node in self.fetch_nodes(graph_id):
            if node.uuid == node_uuid:
                return node
        return None

    def delete_graph(self, graph_id: str):
        """Löscht den Vault-Ordner (Vorsicht!)"""
        import shutil
        vault_path = self._get_vault_path(graph_id)
        if os.path.exists(vault_path):
            shutil.rmtree(vault_path)

    def healthcheck(self) -> Dict[str, Any]:
        """Prüft ob das Upload-Verzeichnis beschreibbar ist"""
        try:
            os.makedirs(self.base_root, exist_ok=True)
            return {"status": "ok", "provider": "obsidian", "root": self.base_root}
        except Exception as e:
            return {"status": "error", "provider": "obsidian", "error": str(e)}
