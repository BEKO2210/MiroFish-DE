# Neuerungen aus dem Original (666ghj/MiroFish)

Stand: 13.10.2026. Gesichtet wurden alle Commits `985f89f..upstream/main` ohne Merges, also alles seit unserer
Abzweigung am 06.03.2026. Weil unser Code übersetzt ist und es keine gemeinsame git-Historie gibt, wurde jede
Änderung von Hand portiert, mit deutschen Kommentaren.

Nicht einzeln aufgeführt sind:

- **Star History:** 7657031, 14e7201, 39d8491, 117ed37, b5b53ac, 0f67b29, a97ba4f, 4ebb2ed
- **README/Doku:** faa1511, fa0f651, 0e9420e, 1536a79
- **Upstream-i18n:** etwa 30 Commits mit „i18n“ im Titel, dazu backend `t()`, Accept-Language und Locale-Dateien.
  Wir haben unsere eigene Zweisprachigkeit mit vue-i18n v9.

## Übersicht

| Commit | Thema | Entscheidung | Grund |
|---|---|---|---|
| e9cac5f | Flask-Debug standardmäßig an, auf 0.0.0.0 | übernommen | Sicherheitslücke: Über den Werkzeug-Debugger lässt sich beliebiger Code ausführen. `FLASK_DEBUG` steht jetzt standardmäßig auf `False`, `validate()` warnt, wenn der Debug-Modus an ist. |
| 32fa3c8 | doppeltes `to_dict()` in `/api/graph/tasks` | übernommen | Gleicher Fehler bei uns: `list_tasks()` liefert schon Dicts, deshalb gab es bei jedem Aufruf einen AttributeError. |
| e3350a9 | Entitätsnamen in PascalCase, Kanten in SCREAMING_SNAKE_CASE, Duplikate | übernommen | Lokale Modelle liefern oft `snake_case` oder doppelte Typen. Eigene Ergänzung: Umlaute werden vorher in ASCII umgeschrieben (`_ascii_fold`), sonst würde aus „Bürger“ „BRger“. |
| a07841e | Attribute als String → TypeError (#135) | übernommen | Der Absturz in `set_ontology` trat bei uns ebenso auf. Ab jetzt wird zentral in `utils/ontology.py` normalisiert. |
| 9506e6f | Attribute zentral normalisieren | übernommen | neue Datei `backend/app/utils/ontology.py` |
| d2f9e56 | Zep-Grenzen der Ontologie (10 Typen, 10 Attribute, `graph_id` reserviert, `entities={}`) | übernommen | in `graph_builder._set_zep_ontology` und im Prompt |
| e4aa38d | Zep-Cloud-Modernisierung (zep-cloud 3.25, Cursor-Paging, Ingestion-Barrieren) | teilweise | **Übernommen:** die robuste Endfassung von `_validate_and_process` (Skalare, Namenszuordnung, `source_targets` nach Kürzung auflösen) und `normalize_ontology_source_targets`. **Verworfen:** der Rest. Er umfasst rund 4000 Zeilen, setzt den SDK-Sprung auf 3.25 voraus und baut Graph, Simulation und Report um. Bei uns ist Zep optional und hinter Memory-Providern gekapselt, ein Port würde Obsidian/Hybrid gefährden. |
| 407c391 | Zep-Timeouts intern | verworfen | baut auf e4aa38d auf (`utils/zep.py`, Konstanten), die wir nicht haben |
| 54bd7a3 | vollständiger Zep-Entitätskontext | übernommen (Kern) | `ZepMemoryProvider.fetch_node_edges` lädt jetzt alle Kanten des Graphen und filtert in beide Richtungen, wie es der Obsidian-Provider schon tut. Das Validierungsskript für Zep Cloud wurde nicht übernommen. |
| 0d8c23a | unterstützte Zep-Methode für Knotenkanten | übernommen (über 54bd7a3) | Fehler bestätigt: `graph.node.get_entity_edges` gibt es in zep-cloud 3.13.0 nicht, die Wheel-Datei wurde geprüft. Bisher lieferte die Methode deshalb immer still `[]`. |
| e58d4f1 | `max_items` für `fetch_all_edges` (#513) | übernommen | Ohne Grenze wächst der Speicher unbegrenzt. Jetzt gilt eine Grenze von 5000 wie bei den Knoten. |
| 7d6f6bb | Parameterreihenfolge Edge-Paging | übernommen | `max_items` steht als letzter Parameter, damit positionsbasierte Aufrufe kompatibel bleiben |
| f0e936a | lange Texte für die Ontologie stichprobenartig verteilen | übernommen | Bisher wurde nur der Anfang (50.000 Zeichen) gelesen. Jetzt fließen bis zu 60 gleichmäßig verteilte Blöcke ein (Anfang, Mitte, Ende). Der Prompt-Text ist deutsch. |
| f0d487f | Ontologie-JSON härten | übernommen (Backend) | `LLMResponseError`, `chat_json(max_attempts)`, strenges Parsen (abgeschnittenes, leeres oder mehrfaches JSON), Rückfall ohne `response_format`, Projekt wird bei Fehlschlag auf FAILED gesetzt, HTTP 502 bei LLM-Fehlern, kein Traceback in der Antwort. **Abweichungen:** Der erste Versuch läuft mit `max_tokens=8192` statt `None`, damit kleine lokale Modelle nicht bis zum Kontextende laufen. Nur der Wiederholversuch läuft ohne Grenze. Unerwartete Fehler zeigen weiter ihren Text (z. B. „Ollama nicht erreichbar“), weil Pipeline und Oberfläche ihn anzeigen. Der Frontend-Teil (`api/index.js`) folgt später, siehe unten. |
| f7138e0 | GPT-5-Familie: Fehler 500 | übernommen (Endstand e67a52e) | neue Datei `utils/openai_chat_compat.py`. Lokale Anbieter sind nicht betroffen, der Pfad greift nur bei Modellnamen mit `gpt-5…`. `extra_body` mit `reasoning_effort: "none"` wird unverändert durchgereicht (getestet). |
| e67a52e | GPT-5-Behandlung eng halten | übernommen | wie oben, angewendet in `llm_client`, `oasis_profile_generator` und `simulation_config_generator` |
| 41fc932 | strukturierte Profilfelder normalisieren | übernommen (Endstand 9f80ad6) | Lokale Modelle liefern `bio`, `persona` oder `interested_topics` oft als dict oder list |
| 9f80ad6 | Profilfelder im `__post_init__` normalisieren | übernommen | `_coerce_to_str` / `_coerce_to_str_list` in `OasisAgentProfile` |
| c415387 | Leerzeichen im Profilmodell | übernommen | in 9f80ad6 enthalten |
| 1d96b09 | erfundene `<tool_result>`-Blöcke entfernen | übernommen | Kleine lokale Modelle halluzinieren Tool-Ergebnisse besonders oft. Neue Prompt-Regel 5 „Keine erfundenen Daten“. |
| f0e3794 | Bereinigung überall | übernommen | alle Stellen in `report_agent.py`, an denen eine Assistant-Antwort in den Verlauf geht, dazu Final Answer und Chat |
| aaf3ea0 | Standardplattform „reddit“ verliert Twitter-Daten (#150) | übernommen (Backend) | `_get_default_platform()` für profiles, profiles/realtime, posts und comments. Bei comments ist die Plattform zusätzlich auf `twitter`/`reddit` beschränkt (Pfadschutz). Der Frontend-Teil folgt später. |
| b651883 | Twitter-Profile aus CSV laden | übernommen | `get_profiles()` las bisher `twitter_profiles.json`, die es nie gibt |
| 05bea4a | Step2-Polling nach Fehlschlag beenden | übernommen (Backend) | `profiles_generated` im State; realtime-Endpunkte liefern `status`, `error` und `generation_stage="failed"`. Ein FAILED-Status meldet die Aufgabe nicht mehr als „completed“. Ohne Entitäten wird ein Fehler ausgelöst, und alte Fehler werden beim Neustart zurückgesetzt. Der Frontend-Teil folgt später. |
| 8b41460 | Fehlerstatus der Simulation hat Vorrang | später Frontend | siehe unten |
| 867b54c | Polling beenden, wenn die Simulation fehlschlägt | später Frontend | siehe unten |
| e6a5021 | Verlaufskarten: lokales Datum statt UTC | später Frontend | siehe unten |
| 442d5fd | Chatverlauf verliert gleichlautende Nachrichten | später Frontend | siehe unten |
| c81d628 | verwundbare npm-Abhängigkeiten | später Frontend | Versionen siehe unten, nicht geändert |
| 223b283 | axios/rollup/picomatch (3× high) | später Frontend | Versionen siehe unten, nicht geändert |
| 7c7c7a2 | axios fest pinnen | später Frontend | überholt durch c81d628 (`^1.18.1`) |
| 65df257 | vue-i18n v9 → v11 | verworfen | Teil der Upstream-i18n. Hinweis: vue-i18n v9 wird nicht mehr gepflegt, ein eigenes Upgrade sollte beim Frontend-Umbau geprüft werden. |
| fe2fd5b | CVE-2025-14009 (nltk) | übernommen | `uv lock --upgrade-package nltk` ergibt nltk 3.9.2 → **3.10.3** (Upstream: 3.10.0) mit neuer Abhängigkeit `defusedxml` |
| 3f4d561 | Python auf 3.11–3.12 begrenzen | übernommen | `requires-python = ">=3.11,<3.13"`. `uv.lock` wurde neu aufgelöst, dabei fielen nur die cp313/cp314-Wheels weg. |
| daec4b6 | Typangaben, `FileParser.is_supported()` | teilweise | Die Typangabe an `Config.validate() -> list[str]` ist übernommen. Der Helfer `is_supported()` ist verworfen, weil er nirgends genutzt wird, ebenso die Typangaben im Logger (nur Kosmetik). |
| 898f3b5 | manuelles Docker-Publishing nur auf Wunsch | verworfen | Wir haben keine GitHub-Workflows |
| 564a560 | Docker-Image für arm64 | verworfen | wie oben |

**Bilanz:** 37 Commits geprüft. 24 übernommen, davon bei f0d487f, aaf3ea0 und 05bea4a nur der Backend-Teil (der
Frontend-Teil ist vorgemerkt). 2 teilweise übernommen (e4aa38d, daec4b6), 4 verworfen, 7 für das Frontend vorgemerkt.

## Offene Frontend-Punkte (nicht angewendet, Umbau läuft parallel)

Die Zeilenangaben beziehen sich auf den Stand dieses Commits.

1. **Simulation schlägt fehl → Polling stoppen, Fehler hat Vorrang** (867b54c + 8b41460).
   `frontend/src/components/Step3Simulation.vue`, `fetchRunStatus` (ab Z. 492), Bedingung Z. 515/521:
   - `const isFailed = data.runner_status === 'failed'` ergänzen.
   - `isFailed` **vor** `isCompleted || platformsCompleted` prüfen. Dann `addLog(<simFailed> + (data.error ? ': ' + data.error : ''))`,
     `phase.value = 2`, `stopPolling()`, `emit('update-status', 'error')`.
   - Der i18n-Schlüssel für „Simulation fehlgeschlagen“ gehört in `de.json` und `en.json`.
2. **Step2: Polling nach fehlgeschlagener Vorbereitung beenden** (05bea4a). Das Backend liefert die Felder schon.
   `frontend/src/components/Step2EnvSetup.vue`:
   - Helfer `handlePrepareFailure(message)` anlegen: `stopPolling()`, `stopProfilesPolling()`, `stopConfigPolling()`,
     Fehler-Log, `emit('update-status', 'error')`.
   - `pollPrepareStatus` (ab Z. 849), Zweig `data.status === 'failed'` (Z. ~900): den Helfer aufrufen. Bisher läuft das
     Config-Polling weiter.
   - `fetchConfigRealtime` (ab Z. 967): Gleich nach `const data = res.data` gilt: Bei `data.status === 'failed' || data.error`
     wird `handlePrepareFailure(data.error)` aufgerufen und die Funktion verlassen.
   - `loadPreparedData` (ab Z. 1023): Das Fehlerverhalten ist dasselbe. Der `else`-Zweig (Z. 1049) startet das
     Config-Polling nur bei `configState.is_generating`, sonst wird ein Fehler gemeldet. Der `catch`-Zweig ruft
     `handlePrepareFailure`.
3. **Plattform nicht fest auf „reddit“ setzen** (aaf3ea0). Das Backend wählt jetzt selbst.
   - `frontend/src/api/simulation.js` Z. 40, 49, 118: Der Standard `platform = 'reddit'` entfällt. `platform` wird nur
     mitgeschickt, wenn es gesetzt ist.
   - `Step2EnvSetup.vue` Z. 915 und `Step5Interaction.vue` Z. 900: `getSimulationProfilesRealtime(props.simulationId)`
     ohne `'reddit'` aufrufen.
4. **Verlaufskarten zeigen bei Nicht-UTC ein falsches Datum** (e6a5021).
   `frontend/src/components/HistoryDatabase.vue`, `formatDate` Z. 316–320: Statt `toISOString().slice(0, 10)` wird das
   Datum aus `getFullYear()`, `getMonth()+1` und `getDate()` zusammengesetzt (`padStart(2,'0')`).
5. **Chatverlauf verliert frühere gleichlautende Nachrichten** (442d5fd).
   `frontend/src/components/Step5Interaction.vue`: Z. 666 `.filter(msg => msg.role !== 'user' || msg.content !== message)`
   und Z. 702 `.filter(msg => msg.content !== message)` werden jeweils durch `.slice(0, -1)` ersetzt.
6. **Backend-Fehlertext bei HTTP-Fehlern anzeigen** (Frontend-Teil von f0d487f).
   `frontend/src/api/index.js`, Fehler-Interceptor: Hier wird
   `const apiError = error.response?.data?.error || error.response?.data?.message` gesetzt. Wenn das ein nicht-leerer
   String ist, gilt `error.message = apiError`. Sonst sieht man bei 500/502 nur „Request failed with status code …“.
7. **npm-Sicherheitsupdates** (c81d628, 223b283, 7c7c7a2). Nichts geändert, der Stand ist notiert:

   | Paket | Datei | bei uns (package.json / lock) | Upstream |
   |---|---|---|---|
   | axios | frontend/package.json | `^1.13.2` / 1.13.2 | `^1.18.1` (lock 1.18.1) |
   | vite | frontend/package.json | `^7.2.4` / 7.2.7 | `^7.3.6` (lock 7.3.6) |
   | rollup | frontend lock (transitiv) | 4.53.3 | 4.60.1 |
   | picomatch | frontend lock (transitiv) | 4.0.3 | 4.0.4 |
   | esbuild | frontend lock (transitiv) | 0.25.12 | 0.28.1 |
   | postcss | frontend lock (transitiv) | 8.5.6 | 8.5.22 |
   | nanoid | frontend lock (transitiv) | 3.3.11 | 3.3.16 |
   | follow-redirects / form-data / hasown | frontend lock (transitiv) | 1.15.11 / 4.0.5 / 2.0.2 | 1.16.0 / 4.0.6 / 2.0.4 |
   | proxy-from-env | frontend lock (transitiv) | 1.1.0 | 2.1.0 |
   | concurrently | package.json (Wurzel) | `^9.1.2` / 9.2.1 | `^9.2.4` (lock 9.2.4, shell-quote 1.9.0) |

## Prüfung

- `cd backend && python3 -m compileall -q app scripts` läuft ohne Fehler durch.
- Ein Rauchtest mit Stubs für openai, flask und zep_cloud lief erfolgreich. Geprüft wurden:
  - JSON-Parser: abgeschnitten, leer, Array oder mehrere Werte führen zu `LLMResponseError`; Text nach dem Objekt wird ignoriert.
  - `chat_json`: Der Wiederholversuch läuft ohne `max_tokens`, `extra_body` mit `reasoning_effort` bleibt erhalten.
  - GPT-5-Pfad: ohne `temperature`, mit `max_completion_tokens`.
  - Ontologie: Normalisierung (Duplikate, Skalare, Umlaute, Kanten nach Kürzung) und Stichproben aus langem Text
    (≤ 50.000 Zeichen, das Ende ist enthalten).
  - `_strip_fake_tool_results` und die Profilfeld-Normalisierung.
- Ein echter Durchlauf gegen Ollama oder Zep fehlt noch, denn in diesem Worktree ist kein venv installiert.
