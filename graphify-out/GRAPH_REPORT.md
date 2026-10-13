# Graph Report - mirofish-upstream  (2026-10-13)

## Corpus Check
- 92 files · ~405,494 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: (none) 6, .example 1, .lock 1)

## Summary
- 2400 nodes · 4621 edges · 124 communities (60 shown, 64 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 345 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `73cbb0cd`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- services/__init__.py
- SimulationRunner
- Step4Report.vue
- SimulationManager
- Process.vue
- Step5Interaction.vue
- FileParser
- ProjectManager
- EntityNode
- TaskManager
- GraphBuilderService
- Step3Simulation.vue
- system_status
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
- RedditSimulationRunner
- run_parallel_simulation.py
- .chat
- Config
- HistoryDatabase.vue
- interview_agent
- Home.vue
- ReportView.vue
- ReportManager
- frontend/package.json
- InteractionView.vue
- ZepMemoryProvider
- AgentActivity
- ParallelIPCHandler
- SimulationLogManager
- simulation.js
- package.json
- get_logger
- ObsidianMemoryProvider
- ZepEntityReader
- ZepToolsService
- retry_with_backoff_async
- OntologyGenerator
- ZepGraphMemoryUpdater
- MemoryNode
- ReportConsoleLogger
- ActionLogger
- ReportAgent
- report_agent.py
- .search_graph
- .save_project
- simulation.py
- OasisProfileGenerator
- EdgeInfo
- NodeInfo
- ThemePicker.vue
- Design-System: MiroFish „Editorial Clarity“
- HistoryView.vue
- build_graph
- init_logging_for_simulation
- getAgentLog
- generate_ontology
- RunView.vue
- GraphPanel.vue
- route
- SimulationIPCServer
- Konkrete Mobile- & Template-Fixes (Mobile First 412 px)
- Übersicht
- SwarmCanvas.vue
- OasisAgentProfile
- Design-Audit: MiroFish Web-App (Mobile First & Barrierefreiheit)
- 3. Umfassender Ansichten-Audit (View-by-View Breakdown)
- 2. Bestätigung und Tiefenanalyse der bekannten Kernmängel
- SimulationParameters
- AgentActivityConfig
- SimulationConfigGenerator
- MiroFish API (für Skripte, Agenten und eigene Oberflächen)
- save_config
- .panorama_search
- ReportSection
- test_profile_format.py
- _enrich_action_context
- list_projects
- mirofish-backend
- Konkrete Template-Textersetzungen:
- prepare_simulation
- Mangel 3: Leere Flächen mit einzelnen Rauten-Symbolen
- Mangel 4: Karten der „Simulationsaufzeichnungen“ am Handy links/rechts abgeschnitten
- Mangel 2: Badge „Elegante universelle Schwarm-Intelligenz-Engine“ bricht um
- Mangel 5: Im Prompt-Feld überlappt Badge „Engine: MiroFish-V1.0“ den Platzhaltertext
- Mangel 10: Fehlende Zeitschätzung und Statusführung bei langen Läufen (Minuten bis 1 Stunde)
- .generate_config
- ROADMAP.md
- ._parse_time_config
- setup_oasis_logging
- setup_oasis_logging
- I18N-Bericht
- InsightForgeResult
- InterviewResult
- AgentInterview
- MaxTokensWarningFilter
- setup_signal_handlers
- MaxTokensWarningFilter
- setup_signal_handlers

## God Nodes (most connected - your core abstractions)
1. `Config` - 58 edges
2. `error()` - 58 edges
3. `SimulationRunner` - 52 edges
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
- `Übersicht` --references--> `OasisAgentProfile`  [INFERRED]
  docs/UPSTREAM.md → backend/app/services/oasis_profile_generator.py
- `Übersicht` --references--> `_ascii_fold()`  [INFERRED]
  docs/UPSTREAM.md → backend/app/services/ontology_generator.py
- `Prüfung` --references--> `LLMResponseError`  [INFERRED]
  docs/UPSTREAM.md → backend/app/utils/llm_client.py
- `Übersicht` --references--> `LLMResponseError`  [INFERRED]
  docs/UPSTREAM.md → backend/app/utils/llm_client.py

## Import Cycles
- None detected.

## Communities (124 total, 64 thin omitted)

### Community 0 - "services/__init__.py"
Cohesion: 0.06
Nodes (9): CommandStatus, CommandType, RoundSummary, RunnerStatus, TextProcessor, FilteredEntities, fetch_all_edges(), fetch_all_nodes() (+1 more)

### Community 1 - "SimulationRunner"
Cohesion: 0.08
Nodes (5): get_run_status_detail(), AgentAction, SimulationRunner, cleanup_handler(), SimulationRunState

### Community 2 - "Step4Report.vue"
Cohesion: 0.03
Nodes (38): activeSectionIndex, activeStep, agentLogLine, agentLogs, collapsedSections, completedSections, consoleLogLine, consoleLogs (+30 more)

### Community 3 - "SimulationManager"
Cohesion: 0.05
Nodes (9): close_simulation_env(), create_simulation(), get_simulation(), get_simulation_history(), stop_simulation(), PlatformType, SimulationManager, SimulationState (+1 more)

### Community 4 - "Process.vue"
Cohesion: 0.07
Nodes (41): getGraphData(), getProject(), getPendingUpload(), fetchGraphData(), buildProgress, closeDetailPanel(), currentPhase, currentProjectId (+33 more)

### Community 5 - "Step5Interaction.vue"
Cohesion: 0.05
Nodes (41): getSimulationProfilesRealtime(), interviewAgents(), activeTab, addLog(), chatHistory, chatHistoryCache, chatInput, chatInputRef (+33 more)

### Community 10 - "GraphBuilderService"
Cohesion: 0.06
Nodes (4): delete_graph(), get_graph_data(), GraphBuilderService, GraphInfo

### Community 11 - "Step3Simulation.vue"
Cohesion: 0.08
Nodes (35): getRunStatus(), getRunStatusDetail(), actionIds, addLog(), allActions, checkPlatformsCompleted(), chronologicalActions, doStartSimulation() (+27 more)

### Community 13 - "Step2EnvSetup.vue"
Cohesion: 0.09
Nodes (36): Offene Frontend-Punkte (nicht angewendet, Umbau läuft parallel), getPrepareStatus(), getSimulationConfigRealtime(), addLog(), autoGeneratedRounds, currentStage, customMaxRounds, displayProfiles (+28 more)

### Community 14 - "MainView.vue"
Cohesion: 0.09
Nodes (36): clearPendingUpload(), addLog(), buildProgress, currentPhase, currentProjectId, currentStep, error, graphData (+28 more)

### Community 15 - "README.md"
Cohesion: 0.05
Nodes (36): 1. Umgebungsvariablen konfigurieren, 2. Abhängigkeiten installieren, 3. Dienste starten, 📄 Danksagung, 1. Configure Environment Variables, 1. Wuhan University Public Opinion Simulation + MiroFish Project Introduction, 2. Dream of the Red Chamber Lost Ending Simulation, 2. Install Dependencies (+28 more)

### Community 16 - "SimulationRunView.vue"
Cohesion: 0.05
Nodes (53): closeSimulationEnv(), getEnvStatus(), getSimulation(), getSimulationConfig(), stopSimulation(), addLog(), currentSimulationId, currentStatus (+45 more)

### Community 18 - "run_reddit_simulation"
Cohesion: 0.10
Nodes (7): PlatformActionLogger, create_model(), get_active_agents_for_round(), get_agent_names_from_config(), PlatformSimulation, run_reddit_simulation(), run_twitter_simulation()

### Community 20 - "IPCHandler"
Cohesion: 0.09
Nodes (3): IPCHandler, main(), TwitterSimulationRunner

### Community 21 - "SimulationIPCClient"
Cohesion: 0.12
Nodes (3): IPCCommand, IPCResponse, SimulationIPCClient

### Community 22 - "error"
Cohesion: 0.11
Nodes (19): chat_with_report_agent(), check_report_status(), delete_report(), generate_report(), get_agent_log(), get_console_log(), get_generate_status(), get_graph_statistics_tool() (+11 more)

### Community 24 - "run_parallel_simulation.py"
Cohesion: 0.09
Nodes (6): CommandType, _utf8_open(), CommandType, MaxTokensWarningFilter, setup_signal_handlers(), CommandType

### Community 26 - "Config"
Cohesion: 0.10
Nodes (15): _base(), _dir(), _load(), mark_stale_runs(), _ok(), _path(), pipeline_list(), pipeline_status() (+7 more)

### Community 27 - "HistoryDatabase.vue"
Cohesion: 0.08
Nodes (16): closeModal(), confirmDelete(), containerStyle, goToProject(), goToReport(), goToSimulation(), historyContainer, hoveringCard (+8 more)

### Community 28 - "interview_agent"
Cohesion: 0.12
Nodes (5): get_env_status(), interview_agent(), interview_agents_batch(), interview_all_agents(), optimize_interview_prompt()

### Community 29 - "Home.vue"
Cohesion: 0.07
Nodes (27): startPipeline(), route, showTheme, { t }, state, activeRuns, add(), autopilot (+19 more)

### Community 30 - "ReportView.vue"
Cohesion: 0.09
Nodes (21): { locale, t }, addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph() (+13 more)

### Community 31 - "ReportManager"
Cohesion: 0.04
Nodes (5): download_report(), run_generate(), Report, ReportManager, ReportOutline

### Community 33 - "frontend/package.json"
Cohesion: 0.09
Nodes (21): dependencies, axios, d3, vue, vue-i18n, vue-router, devDependencies, vite (+13 more)

### Community 34 - "InteractionView.vue"
Cohesion: 0.10
Nodes (21): getReport(), addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph() (+13 more)

### Community 35 - "ZepMemoryProvider"
Cohesion: 0.06
Nodes (6): MemoryEdge, MemoryProvider, MemorySearchResult, MemoryFactory, HybridMemoryProvider, ZepMemoryProvider

### Community 39 - "SimulationLogManager"
Cohesion: 0.13
Nodes (3): SimulationLogManager, load_config(), main()

### Community 40 - "simulation.js"
Cohesion: 0.10
Nodes (18): buildGraph(), generateOntology(), getTaskStatus(), requestWithRetry(), service, chatWithReport(), generateReport(), createSimulation() (+10 more)

### Community 41 - "package.json"
Cohesion: 0.11
Nodes (17): description, devDependencies, concurrently, engines, node, license, name, scripts (+9 more)

### Community 42 - "get_logger"
Cohesion: 0.19
Nodes (6): create_app(), log_request(), log_response(), _ensure_utf8_stdout(), get_logger(), setup_logger()

### Community 44 - "ZepEntityReader"
Cohesion: 0.10
Nodes (5): generate_profiles(), get_entities_by_type(), get_entity_detail(), get_graph_entities(), ZepEntityReader

### Community 46 - "retry_with_backoff_async"
Cohesion: 0.15
Nodes (6): retry_with_backoff(), retry_with_backoff_async(), decorator(), decorator(), wrapper(), RetryableAPIClient

### Community 48 - "OntologyGenerator"
Cohesion: 0.06
Nodes (8): _ascii_fold(), OntologyGenerator, resolve_entity_name(), _to_pascal_case(), _to_upper_snake_case(), normalize_ontology_attribute(), normalize_ontology_attributes(), normalize_ontology_source_targets()

### Community 55 - "report_agent.py"
Cohesion: 0.06
Nodes (9): split_text_into_chunks(), _clean_chat_text(), _contains_additional_json_container(), _is_response_format_unsupported(), LLMClient, LLMResponseError, create_chat_completion(), extract_chat_completion_text() (+1 more)

### Community 57 - ".save_project"
Cohesion: 0.18
Nodes (3): reset_project(), Project, ProjectStatus

### Community 58 - "simulation.py"
Cohesion: 0.06
Nodes (15): download_simulation_config(), download_simulation_script(), get_agent_stats(), _get_default_platform(), get_interview_history(), get_run_status(), get_simulation_actions(), get_simulation_comments() (+7 more)

### Community 63 - "ThemePicker.vue"
Cohesion: 0.11
Nodes (34): busy, choose(), chooseOwn(), current, error, input, isDefault, ownColor (+26 more)

### Community 65 - "Design-System: MiroFish „Editorial Clarity“"
Cohesion: 0.08
Nodes (24): 1. Design-Richtung & Philosophie, 2. Typografie, 3.1 Helles Design (Light Mode - Standard), 3.2 Dunkles Design (Dark Mode - `[data-theme="dark"]`), 3. Farbpalette & Nachgerechnete WCAG-AA-Kontraste, 4. Abstands- und Rastersystem, 5.1 Buttons (Schaltflächen), 5.2 Karten (Cards) (+16 more)

### Community 66 - "HistoryView.vue"
Cohesion: 0.05
Nodes (38): listPipelines(), deleteSimulation(), getSimulationHistory(), { t }, activeCount, poll(), route, { t } (+30 more)

### Community 68 - "build_graph"
Cohesion: 0.18
Nodes (3): build_graph(), build_task(), debug()

### Community 71 - "getAgentLog"
Cohesion: 0.25
Nodes (8): getAgentLog(), getConsoleLog(), addLog(), emit, fetchAgentLog(), fetchConsoleLog(), startPolling(), stopPolling()

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

### Community 80 - "Übersicht"
Cohesion: 0.27
Nodes (3): _coerce_to_str(), _coerce_to_str_list(), Übersicht

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

### Community 94 - "_enrich_action_context"
Cohesion: 0.20
Nodes (5): _enrich_action_context(), fetch_new_actions_from_db(), _get_comment_info(), _get_post_info(), _get_user_name()

### Community 98 - "Konkrete Template-Textersetzungen:"
Cohesion: 0.50
Nodes (4): 1. In `Home.vue`:, 2. In `Step1GraphBuild.vue`:, Konkrete Template-Textersetzungen:, Mangel 7: Fachjargon in Nutzertexten

### Community 99 - "prepare_simulation"
Cohesion: 0.08
Nodes (10): _check_simulation_prepared(), delete_simulation(), get_prepare_status(), _get_report_id_for_simulation(), prepare_simulation(), run_prepare(), start_simulation(), Task (+2 more)

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

### Community 114 - "I18N-Bericht"
Cohesion: 0.33
Nodes (5): Bewusst nicht übersetzte Stellen, I18N-Bericht, Offene Punkte, Prüfung, Umfang

## Knowledge Gaps
- **417 isolated node(s):** `mirofish-backend`, `name`, `private`, `version`, `type` (+412 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1330 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **64 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Neuerungen aus dem Original (666ghj/MiroFish)` connect `.chat` to `Übersicht`, `Step2EnvSetup.vue`?**
  _High betweenness centrality (0.362) - this node is a cross-community bridge._
- **Are the 30 inferred relationships involving `Config` (e.g. with `allowed_file()` and `build_graph()`) actually correct?**
  _`Config` has 30 INFERRED edges - model-reasoned connections that need verification._
- **What connects `mirofish-backend`, `name`, `private` to the rest of the system?**
  _417 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `services/__init__.py` be split into smaller, more focused modules?**
  _Cohesion score 0.060362173038229376 - nodes in this community are weakly interconnected._
- **Why does `Offene Frontend-Punkte (nicht angewendet, Umbau läuft parallel)` connect `Step2EnvSetup.vue` to `.chat`, `Step3Simulation.vue`?**
  _High betweenness centrality (0.361) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `error()` (e.g. with `generate_ontology()` and `.chat_json()`) actually correct?**
  _`error()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `SimulationRunner` be split into smaller, more focused modules?**
  _Cohesion score 0.08084163898117387 - nodes in this community are weakly interconnected._