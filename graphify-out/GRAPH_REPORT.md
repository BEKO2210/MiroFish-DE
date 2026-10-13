# Graph Report - MiroFish-DE  (2026-10-13)

## Corpus Check
- 93 files · ~406,735 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 5, .example 1, .lock 1)

## Summary
- 2466 nodes · 4700 edges · 142 communities (71 shown, 71 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 346 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f09d732b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Config
- SimulationRunState
- Step4Report.vue
- SimulationManager
- Process.vue
- Step5Interaction.vue
- file_parser.py
- ProjectManager
- graph.py
- ._build_graph_worker
- Step3Simulation.vue
- Step2EnvSetup.vue
- MainView.vue
- README.md
- SimulationRunView.vue
- ReportLogger
- run_reddit_simulation
- IPCHandler
- IPCHandler
- SimulationIPCClient
- error
- SimulationView.vue
- run_parallel_simulation.py
- ReportAgent
- os
- HistoryDatabase.vue
- interview_agent
- Home.vue
- ReportView.vue
- ._get_report_folder
- OasisAgentProfile
- frontend/package.json
- InteractionView.vue
- MemoryProvider
- AgentActivity
- ParallelIPCHandler
- SimulationLogManager
- simulation.js
- package.json
- app/__init__.py
- SettingsView.vue
- EntityNode
- Any
- retry_with_backoff_async
- Any
- LLMClient
- vue
- ZepGraphMemoryUpdater
- ObsidianMemoryProvider
- ReportConsoleLogger
- action_logger.py
- .chat_json
- .search_graph
- .save_project
- simulation.py
- OasisProfileGenerator
- services/__init__.py
- EdgeInfo
- .insight_forge
- ThemePicker.vue
- AgentAction
- Design-System: MiroFish „Editorial Clarity“
- HistoryView.vue
- build_task
- ZepToolsService
- init_logging_for_simulation
- fetchAgentLog
- generate_ontology
- RunView.vue
- GraphPanel.vue
- route
- SimulationIPCServer
- Konkrete Mobile- & Template-Fixes (Mobile First 412 px)
- Any
- SwarmCanvas.vue
- Design-Audit: MiroFish Web-App (Mobile First & Barrierefreiheit)
- 3. Umfassender Ansichten-Audit (View-by-View Breakdown)
- 2. Bestätigung und Tiefenanalyse der bekannten Kernmängel
- SimulationParameters
- AgentActivityConfig
- SimulationConfigGenerator
- MiroFish API (für Skripte, Agenten und eigene Oberflächen)
- system.py
- PanoramaResult
- SimulationRunner
- test_profile_format.py
- _enrich_action_context
- ._set_zep_ontology
- list_projects
- mirofish-backend
- Konkrete Template-Textersetzungen:
- TaskManager
- Mangel 3: Leere Flächen mit einzelnen Rauten-Symbolen
- Mangel 4: Karten der „Simulationsaufzeichnungen“ am Handy links/rechts abgeschnitten
- Mangel 2: Badge „Elegante universelle Schwarm-Intelligenz-Engine“ bricht um
- Mangel 5: Im Prompt-Feld überlappt Badge „Engine: MiroFish-V1.0“ den Platzhaltertext
- Mangel 10: Fehlende Zeitschätzung und Statusführung bei langen Läufen (Minuten bis 1 Stunde)
- .generate_config
- ontology_generator.py
- ROADMAP.md
- .cleanup_all_simulations
- ._parse_time_config
- setup_oasis_logging
- setup_oasis_logging
- I18N-Bericht
- Step1GraphBuild.vue
- Übersicht
- .get_all_nodes
- InterviewResult
- README-EN.md
- MaxTokensWarningFilter
- setup_signal_handlers
- setup_signal_handlers
- 🚀 Schnellstart
- 🚀 Quick Start
- vue-i18n
- ProjectStatus
- test_llm
- Option 1: Quellcode-Deployment (empfohlen)
- Option 1: Source Code Deployment (Recommended)
- MaxTokensWarningFilter
- setup_signal_handlers
- 🎬 Demo Videos
- docker-entrypoint.sh

## God Nodes (most connected - your core abstractions)
1. `Config` - 59 edges
2. `error()` - 58 edges
3. `SimulationRunner` - 53 edges
4. `ReportManager` - 50 edges
5. `OasisProfileGenerator` - 35 edges
6. `SimulationManager` - 35 edges
7. `ZepToolsService` - 34 edges
8. `ProjectManager` - 33 edges
9. `ObsidianMemoryProvider` - 33 edges
10. `get_logger()` - 29 edges

## Surprising Connections (you probably didn't know these)
- `Übersicht` --references--> `_get_default_platform()`  [INFERRED]
  docs/UPSTREAM.md → backend/app/api/simulation.py
- `Übersicht` --references--> `_coerce_to_str()`  [INFERRED]
  docs/UPSTREAM.md → backend/app/services/oasis_profile_generator.py
- `Übersicht` --references--> `_coerce_to_str_list()`  [INFERRED]
  docs/UPSTREAM.md → backend/app/services/oasis_profile_generator.py
- `Übersicht` --references--> `OasisAgentProfile`  [INFERRED]
  docs/UPSTREAM.md → backend/app/services/oasis_profile_generator.py
- `Übersicht` --references--> `_ascii_fold()`  [INFERRED]
  docs/UPSTREAM.md → backend/app/services/ontology_generator.py

## Import Cycles
- None detected.

## Communities (142 total, 71 thin omitted)

### Community 0 - "Config"
Cohesion: 0.08
Nodes (6): Config, MemoryFactory, get_logger(), fetch_all_edges(), fetch_all_nodes(), _fetch_page_with_retry()

### Community 2 - "Step4Report.vue"
Cohesion: 0.03
Nodes (38): activeSectionIndex, activeStep, agentLogLine, agentLogs, collapsedSections, completedSections, consoleLogLine, consoleLogs (+30 more)

### Community 3 - "SimulationManager"
Cohesion: 0.05
Nodes (9): close_simulation_env(), get_simulation(), get_simulation_config(), get_simulation_history(), stop_simulation(), PlatformType, SimulationManager, SimulationState (+1 more)

### Community 4 - "Process.vue"
Cohesion: 0.06
Nodes (40): clearPendingUpload(), getPendingUpload(), state, buildProgress, closeDetailPanel(), currentPhase, currentProjectId, entityTypes (+32 more)

### Community 5 - "Step5Interaction.vue"
Cohesion: 0.05
Nodes (43): getAgentLog(), getReport(), getSimulationProfilesRealtime(), interviewAgents(), activeTab, addLog(), chatHistory, chatHistoryCache (+35 more)

### Community 9 - "graph.py"
Cohesion: 0.10
Nodes (4): delete_graph(), TaskStatus, GraphBuilderService, TextProcessor

### Community 11 - "Step3Simulation.vue"
Cohesion: 0.08
Nodes (36): getRunStatus(), getRunStatusDetail(), startSimulation(), actionIds, addLog(), allActions, checkPlatformsCompleted(), chronologicalActions (+28 more)

### Community 13 - "Step2EnvSetup.vue"
Cohesion: 0.09
Nodes (36): Offene Frontend-Punkte (nicht angewendet, Umbau läuft parallel), getPrepareStatus(), getSimulationConfigRealtime(), addLog(), autoGeneratedRounds, currentStage, customMaxRounds, displayProfiles (+28 more)

### Community 14 - "MainView.vue"
Cohesion: 0.09
Nodes (42): buildGraph(), generateOntology(), getGraphData(), getProject(), getTaskStatus(), service, addLog(), buildProgress (+34 more)

### Community 15 - "README.md"
Cohesion: 0.17
Nodes (11): 📄 Danksagung, 📝 Hinweis zu diesem Repository, 🌐 Live-Demo, Lokaler Betrieb mit Ollama (Stand 13.10.2026), 🚀 Neu in dieser Fassung (Oktober 2026), 🚀 Neuigkeiten & Aktuelle Updates (April 2026), 📈 Projektstatistik, ⚡ Projektübersicht (+3 more)

### Community 16 - "SimulationRunView.vue"
Cohesion: 0.09
Nodes (29): getEnvStatus(), getSimulation(), getSimulationConfig(), addLog(), currentSimulationId, currentStatus, graphData, graphLoading (+21 more)

### Community 18 - "run_reddit_simulation"
Cohesion: 0.10
Nodes (7): PlatformActionLogger, create_model(), get_active_agents_for_round(), get_agent_names_from_config(), PlatformSimulation, run_reddit_simulation(), run_twitter_simulation()

### Community 19 - "IPCHandler"
Cohesion: 0.09
Nodes (3): IPCHandler, main(), RedditSimulationRunner

### Community 20 - "IPCHandler"
Cohesion: 0.09
Nodes (3): IPCHandler, main(), TwitterSimulationRunner

### Community 21 - "SimulationIPCClient"
Cohesion: 0.11
Nodes (3): IPCCommand, IPCResponse, SimulationIPCClient

### Community 22 - "error"
Cohesion: 0.10
Nodes (21): chat_with_report_agent(), check_report_status(), delete_report(), download_report(), generate_report(), get_agent_log(), get_console_log(), get_generate_status() (+13 more)

### Community 23 - "SimulationView.vue"
Cohesion: 0.10
Nodes (24): closeSimulationEnv(), stopSimulation(), addLog(), checkAndStopRunningSimulation(), currentSimulationId, currentStatus, forceStopSimulation(), graphData (+16 more)

### Community 24 - "run_parallel_simulation.py"
Cohesion: 0.11
Nodes (5): CommandType, _utf8_open(), CommandType, CommandType, MaxTokensWarningFilter

### Community 26 - "os"
Cohesion: 0.09
Nodes (18): _base(), _dir(), _load(), mark_stale_runs(), _ok(), _path(), pipeline_list(), pipeline_status() (+10 more)

### Community 27 - "HistoryDatabase.vue"
Cohesion: 0.08
Nodes (14): closeModal(), containerStyle, goToProject(), goToReport(), goToSimulation(), historyContainer, hoveringCard, isExpanded (+6 more)

### Community 28 - "interview_agent"
Cohesion: 0.12
Nodes (5): get_env_status(), interview_agent(), interview_agents_batch(), interview_all_agents(), optimize_interview_prompt()

### Community 29 - "Home.vue"
Cohesion: 0.09
Nodes (22): startPipeline(), activeRuns, add(), autopilot, canSubmit, error, fileInput, files (+14 more)

### Community 30 - "ReportView.vue"
Cohesion: 0.10
Nodes (20): addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph(), loadReportData() (+12 more)

### Community 31 - "._get_report_folder"
Cohesion: 0.05
Nodes (3): run_generate(), Report, ReportOutline

### Community 33 - "frontend/package.json"
Cohesion: 0.09
Nodes (21): dependencies, axios, d3, vue, vue-i18n, vue-router, devDependencies, vite (+13 more)

### Community 34 - "InteractionView.vue"
Cohesion: 0.09
Nodes (21): { locale, t }, addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph() (+13 more)

### Community 39 - "SimulationLogManager"
Cohesion: 0.13
Nodes (3): SimulationLogManager, load_config(), main()

### Community 40 - "simulation.js"
Cohesion: 0.20
Nodes (4): requestWithRetry(), chatWithReport(), generateReport(), prepareSimulation()

### Community 41 - "package.json"
Cohesion: 0.11
Nodes (17): description, devDependencies, concurrently, engines, node, license, name, scripts (+9 more)

### Community 42 - "app/__init__.py"
Cohesion: 0.11
Nodes (8): create_app(), log_request(), log_response(), require_api_token(), token_ok(), _ensure_utf8_stdout(), setup_logger(), main()

### Community 43 - "SettingsView.vue"
Cohesion: 0.11
Nodes (16): baseUrl(), cfg, load(), masked, memoryLabel, models, result, save() (+8 more)

### Community 44 - "EntityNode"
Cohesion: 0.11
Nodes (5): get_entities_by_type(), get_entity_detail(), EntityNode, FilteredEntities, ZepEntityReader

### Community 46 - "retry_with_backoff_async"
Cohesion: 0.15
Nodes (6): retry_with_backoff(), retry_with_backoff_async(), decorator(), decorator(), wrapper(), RetryableAPIClient

### Community 49 - "vue"
Cohesion: 0.13
Nodes (14): listPipelines(), route, showTheme, { t }, activeCount, poll(), route, { t } (+6 more)

### Community 51 - "ObsidianMemoryProvider"
Cohesion: 0.05
Nodes (5): MemoryNode, MemorySearchResult, HybridMemoryProvider, ObsidianMemoryProvider, ZepMemoryProvider

### Community 58 - "simulation.py"
Cohesion: 0.05
Nodes (18): create_simulation(), delete_simulation(), download_simulation_config(), download_simulation_script(), generate_profiles(), get_agent_stats(), _get_default_platform(), get_interview_history() (+10 more)

### Community 60 - "services/__init__.py"
Cohesion: 0.18
Nodes (4): CommandStatus, CommandType, RunnerStatus, ZepGraphMemoryManager

### Community 63 - "ThemePicker.vue"
Cohesion: 0.11
Nodes (34): busy, choose(), chooseOwn(), current, error, input, isDefault, ownColor (+26 more)

### Community 65 - "Design-System: MiroFish „Editorial Clarity“"
Cohesion: 0.08
Nodes (24): 1. Design-Richtung & Philosophie, 2. Typografie, 3.1 Helles Design (Light Mode - Standard), 3.2 Dunkles Design (Dark Mode - `[data-theme="dark"]`), 3. Farbpalette & Nachgerechnete WCAG-AA-Kontraste, 4. Abstands- und Rastersystem, 5.1 Buttons (Schaltflächen), 5.2 Karten (Cards) (+16 more)

### Community 66 - "HistoryView.vue"
Cohesion: 0.14
Nodes (17): deleteSimulation(), getSimulationHistory(), confirmDelete(), loadHistory(), deleting, doDelete(), error, fmt() (+9 more)

### Community 71 - "fetchAgentLog"
Cohesion: 0.29
Nodes (7): getConsoleLog(), addLog(), emit, fetchAgentLog(), fetchConsoleLog(), startPolling(), stopPolling()

### Community 75 - "RunView.vue"
Cohesion: 0.14
Nodes (14): getPipeline(), STEP_LABELS, STEP_ORDER, currentDetail, currentLabel, etaText, HINTS, load() (+6 more)

### Community 76 - "GraphPanel.vue"
Cohesion: 0.12
Nodes (12): emit, entityTypes, expandedSelfLoops, graphContainer, graphSvg, handleResize(), props, renderGraph() (+4 more)

### Community 77 - "route"
Cohesion: 0.20
Nodes (3): get_project(), get_task(), list_tasks()

### Community 79 - "Konkrete Mobile- & Template-Fixes (Mobile First 412 px)"
Cohesion: 0.13
Nodes (15): CSS-Fix (`Home.vue` `<style scoped>`):, CSS-Fix in `Home.vue`:, CSS-Fix in `tokens.css` (wird automatisch wirksam) bzw. `App.vue`:, CSS-Fix (`MainView.vue` `<style scoped>`):, CSS-Fix (`MainView.vue` `<style scoped>`):, Globaler CSS-Klassen-Fix (Drop-in):, Konkrete Mobile- & Template-Fixes (Mobile First 412 px), Mangel 11: Touch-Targets unter 44 px (Löschen-Button, Switcher) (+7 more)

### Community 81 - "SwarmCanvas.vue"
Cohesion: 0.21
Nodes (8): accent(), agents, el, ink(), onVis(), pointer, props, step()

### Community 83 - "Design-Audit: MiroFish Web-App (Mobile First & Barrierefreiheit)"
Cohesion: 0.20
Nodes (8): 1. Executive Summary & Zielgruppen-Kontext, 4.1 Nachgerechnete Kontrastwerte des Ist-Zustands, 4.2 Ergonomie & Touch-Targets, 4. Barrierefreiheit (a11y) & WCAG-AA-Kontrast-Audit, 5. Mängel-Matrix und Priorisierung, Design-Audit: MiroFish Web-App (Mobile First & Barrierefreiheit), Die Kernzielgruppe, Gesamteinschätzung des Ist-Zustands

### Community 84 - "3. Umfassender Ansichten-Audit (View-by-View Breakdown)"
Cohesion: 0.20
Nodes (10): 3.1 Globale Basis (`App.vue`, `index.html`), 3.2 Startseite / Landing & Setup (`Home.vue`), 3.3 Simulationshistorie (`HistoryDatabase.vue`), 3.4 Prozess- und Arbeitsbereich-Shell (`MainView.vue`, `SimulationView.vue`, etc.), 3.5 Schritt 1: Wissensgraph & Dokumentenverarbeitung (`Step1GraphBuild.vue`, `GraphPanel.vue`), 3.6 Schritt 2: Simulationsumgebung & Akteure (`Step2EnvSetup.vue`), 3.7 Schritt 3: Simulationslauf & Langzeit-Wartezustand (`Step3Simulation.vue`), 3.8 Schritt 4: Berichterstellung (`Step4Report.vue`) (+2 more)

### Community 85 - "2. Bestätigung und Tiefenanalyse der bekannten Kernmängel"
Cohesion: 0.25
Nodes (8): 2. Bestätigung und Tiefenanalyse der bekannten Kernmängel, Mangel 1: Hero-Überschrift am Handy riesig und 4 Zeilen, Mangel 2: Badge „Elegante universelle Schwarm-Intelligenz-Engine“ bricht um, Mangel 3: Leere Flächen mit einzelnen Rauten-Symbolen, Mangel 4: Karten der „Simulationsaufzeichnungen“ am Handy links/rechts abgeschnitten (horizontaler Überlauf), Mangel 5: Im Prompt-Feld überlappt Badge „Engine: MiroFish-V1.0“ den Platzhaltertext, Mangel 6: Monospace-Fließtext ist schwer lesbar, Mangel 7: Fachjargon in Nutzertexten

### Community 89 - "MiroFish API (für Skripte, Agenten und eigene Oberflächen)"
Cohesion: 0.33
Nodes (5): Der eine Aufruf, der alles macht, Einzelne Stufen (wenn du selbst steuern willst), Ergebnisse abholen, MiroFish API (für Skripte, Agenten und eigene Oberflächen), Python-Beispiel

### Community 90 - "system.py"
Cohesion: 0.13
Nodes (6): list_models(), mask_key(), _ollama_root(), save_config(), system_models(), system_status()

### Community 94 - "_enrich_action_context"
Cohesion: 0.20
Nodes (5): _enrich_action_context(), fetch_new_actions_from_db(), _get_comment_info(), _get_post_info(), _get_user_name()

### Community 95 - "._set_zep_ontology"
Cohesion: 0.21
Nodes (3): normalize_ontology_attribute(), normalize_ontology_attributes(), normalize_ontology_source_targets()

### Community 98 - "Konkrete Template-Textersetzungen:"
Cohesion: 0.50
Nodes (4): 1. In `Home.vue`:, 2. In `Step1GraphBuild.vue`:, Konkrete Template-Textersetzungen:, Mangel 7: Fachjargon in Nutzertexten

### Community 99 - "TaskManager"
Cohesion: 0.07
Nodes (13): build_graph(), _check_simulation_prepared(), get_graph_entities(), get_prepare_status(), _get_report_id_for_simulation(), prepare_simulation(), run_prepare(), start_simulation() (+5 more)

### Community 100 - "Mangel 3: Leere Flächen mit einzelnen Rauten-Symbolen"
Cohesion: 0.50
Nodes (4): CSS-Fix in `Home.vue`:, Mangel 3: Leere Flächen mit einzelnen Rauten-Symbolen, Template-Fix in `HistoryDatabase.vue` (Zeile 73-77):, Template-Fix in `Home.vue`:

### Community 101 - "Mangel 4: Karten der „Simulationsaufzeichnungen“ am Handy links/rechts abgeschnitten"
Cohesion: 0.67
Nodes (3): CSS-Fix (`HistoryDatabase.vue` `<style scoped>`):, Mangel 4: Karten der „Simulationsaufzeichnungen“ am Handy links/rechts abgeschnitten, Skript-Fix (`HistoryDatabase.vue` `<script setup>`):

### Community 102 - "Mangel 2: Badge „Elegante universelle Schwarm-Intelligenz-Engine“ bricht um"
Cohesion: 0.67
Nodes (3): CSS-Fix (`Home.vue` `<style scoped>`):, Mangel 2: Badge „Elegante universelle Schwarm-Intelligenz-Engine“ bricht um, Template-Fix:

### Community 103 - "Mangel 5: Im Prompt-Feld überlappt Badge „Engine: MiroFish-V1.0“ den Platzhaltertext"
Cohesion: 0.67
Nodes (3): CSS-Fix (`Home.vue` `<style scoped>`):, Mangel 5: Im Prompt-Feld überlappt Badge „Engine: MiroFish-V1.0“ den Platzhaltertext, Template-Fix (`Home.vue`):

### Community 104 - "Mangel 10: Fehlende Zeitschätzung und Statusführung bei langen Läufen (Minuten bis 1 Stunde)"
Cohesion: 0.67
Nodes (3): CSS-Fix (`Step3Simulation.vue` `<style scoped>`):, Mangel 10: Fehlende Zeitschätzung und Statusführung bei langen Läufen (Minuten bis 1 Stunde), Template-Fix (`Step3Simulation.vue`):

### Community 108 - "ontology_generator.py"
Cohesion: 0.22
Nodes (4): _ascii_fold(), resolve_entity_name(), _to_pascal_case(), _to_upper_snake_case()

### Community 114 - "I18N-Bericht"
Cohesion: 0.33
Nodes (5): Bewusst nicht übersetzte Stellen, I18N-Bericht, Offene Punkte, Prüfung, Umfang

### Community 115 - "Step1GraphBuild.vue"
Cohesion: 0.18
Nodes (9): createSimulation(), creatingSimulation, graphStats, handleEnterEnvSetup(), logContent, props, router, selectedOntologyItem (+1 more)

### Community 116 - "Übersicht"
Cohesion: 0.20
Nodes (4): LLMResponseError, Neuerungen aus dem Original (666ghj/MiroFish), Prüfung, Übersicht

### Community 119 - "README-EN.md"
Cohesion: 0.18
Nodes (10): 📄 Acknowledgments, 📬 Join the Conversation, 🌐 Live Demo, 🚀 New in this edition (October 2026), Our Vision, ⚡ Overview, 📈 Project Statistics, 🚀 Recent Updates (April 2026) (+2 more)

### Community 126 - "🚀 Schnellstart"
Cohesion: 0.25
Nodes (8): 1. Ollama und Modelle, 2a. Start mit Docker (empfohlen), 2b. Start aus dem Quellcode, Bedienung, Cloud-Modelle, Option 2: Docker-Deployment, 🚀 Schnellstart, Zugriff von anderen Geräten und für Agenten

### Community 127 - "🚀 Quick Start"
Cohesion: 0.25
Nodes (8): 1. Ollama and models, 2a. Run with Docker (recommended), 2b. Run from source, Access from other devices and for agents, Cloud models, Option 2: Docker Deployment, 🚀 Quick Start, Using it

### Community 128 - "vue-i18n"
Cohesion: 0.29
Nodes (3): { t }, savedLanguage, vue-i18n

### Community 131 - "Option 1: Quellcode-Deployment (empfohlen)"
Cohesion: 0.40
Nodes (5): 1. Umgebungsvariablen konfigurieren, 2. Abhängigkeiten installieren, 3. Dienste starten, Option 1: Quellcode-Deployment (empfohlen), Voraussetzungen

### Community 132 - "Option 1: Source Code Deployment (Recommended)"
Cohesion: 0.40
Nodes (5): 1. Configure Environment Variables, 2. Install Dependencies, 3. Start Services, Option 1: Source Code Deployment (Recommended), Prerequisites

### Community 136 - "🎬 Demo Videos"
Cohesion: 0.67
Nodes (3): 1. Wuhan University Public Opinion Simulation + MiroFish Project Introduction, 2. Dream of the Red Chamber Lost Ending Simulation, 🎬 Demo Videos

## Knowledge Gaps
- **436 isolated node(s):** `mirofish-backend`, `docker-entrypoint.sh script`, `name`, `private`, `version` (+431 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1387 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **71 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Neuerungen aus dem Original (666ghj/MiroFish)` connect `Übersicht` to `Step2EnvSetup.vue`?**
  _High betweenness centrality (0.339) - this node is a cross-community bridge._
- **Are the 31 inferred relationships involving `Config` (e.g. with `allowed_file()` and `build_graph()`) actually correct?**
  _`Config` has 31 INFERRED edges - model-reasoned connections that need verification._
- **What connects `mirofish-backend`, `docker-entrypoint.sh script`, `name` to the rest of the system?**
  _436 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Config` be split into smaller, more focused modules?**
  _Cohesion score 0.08076923076923077 - nodes in this community are weakly interconnected._
- **Why does `Offene Frontend-Punkte (nicht angewendet, Umbau läuft parallel)` connect `Step2EnvSetup.vue` to `Step3Simulation.vue`, `Übersicht`?**
  _High betweenness centrality (0.338) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `error()` (e.g. with `generate_ontology()` and `.chat_json()`) actually correct?**
  _`error()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `SimulationRunState` be split into smaller, more focused modules?**
  _Cohesion score 0.11956521739130435 - nodes in this community are weakly interconnected._