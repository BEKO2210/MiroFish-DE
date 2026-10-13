# Graph Report - MiroFish-DE  (2026-10-13)

## Corpus Check
- 84 files · ~392,189 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 5, .example 1, .lock 1)

## Summary
- 2121 nodes · 4194 edges · 110 communities (65 shown, 45 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 318 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1af7fbaf`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- report_agent.py
- SimulationRunner
- Step4Report.vue
- SimulationManager
- Process.vue
- Step5Interaction.vue
- FileParser
- graph.py
- SimulationConfigGenerator
- TaskManager
- GraphBuilderService
- Step3Simulation.vue
- simulation.py
- Step2EnvSetup.vue
- MainView.vue
- README.md
- SimulationView.vue
- ReportLogger
- run_reddit_simulation
- IPCHandler
- IPCHandler
- SimulationIPCClient
- error
- SimulationRunView.vue
- run_parallel_simulation.py
- ReportAgent
- os
- HistoryDatabase.vue
- interview_agent
- Home.vue
- ReportView.vue
- ReportManager
- OasisProfileGenerator
- vue-router
- InteractionView.vue
- MemoryProvider
- .generate_report
- AgentActivity
- ParallelIPCHandler
- SimulationLogManager
- simulation.js
- package.json
- logger.py
- ObsidianMemoryProvider
- ZepEntityReader
- Any
- retry_with_backoff_async
- Any
- OntologyGenerator
- ZepMemoryProvider
- ZepGraphMemoryUpdater
- MemoryNode
- ReportConsoleLogger
- ActionLogger
- getProject
- LLMClient
- .search_graph
- MemoryEdge
- AgentAction
- OasisAgentProfile
- EdgeInfo
- NodeInfo
- ThemePicker.vue
- MemorySearchResult
- Design-System: MiroFish „Editorial Clarity“
- HistoryView.vue
- ZepToolsService
- main
- getAgentLog
- run_twitter_simulation
- RunView.vue
- GraphPanel.vue
- vue
- SimulationIPCServer
- Konkrete Mobile- & Template-Fixes (Mobile First 412 px)
- router/index.js
- SwarmCanvas.vue
- .generate_profile_from_entity
- Design-Audit: MiroFish Web-App (Mobile First & Barrierefreiheit)
- 3. Umfassender Ansichten-Audit (View-by-View Breakdown)
- 2. Bestätigung und Tiefenanalyse der bekannten Kernmängel
- MemoryFactory
- services/__init__.py
- MiroFish API (für Skripte, Agenten und eigene Oberflächen)
- ZepGraphMemoryManager
- PanoramaResult
- ReportSection
- _enrich_action_context
- mirofish-backend
- Konkrete Template-Textersetzungen:
- prepare_simulation
- Mangel 3: Leere Flächen mit einzelnen Rauten-Symbolen
- Mangel 4: Karten der „Simulationsaufzeichnungen“ am Handy links/rechts abgeschnitten
- Mangel 2: Badge „Elegante universelle Schwarm-Intelligenz-Engine“ bricht um
- Mangel 5: Im Prompt-Feld überlappt Badge „Engine: MiroFish-V1.0“ den Platzhaltertext
- Mangel 10: Fehlende Zeitschätzung und Statusführung bei langen Läufen (Minuten bis 1 Stunde)
- ROADMAP.md

## God Nodes (most connected - your core abstractions)
1. `Config` - 58 edges
2. `error()` - 57 edges
3. `SimulationRunner` - 52 edges
4. `ReportManager` - 49 edges
5. `OasisProfileGenerator` - 34 edges
6. `ZepToolsService` - 34 edges
7. `ProjectManager` - 33 edges
8. `ObsidianMemoryProvider` - 33 edges
9. `SimulationManager` - 33 edges
10. `get_logger()` - 29 edges

## Surprising Connections (you probably didn't know these)
- `create_app()` --uses--> `Config`  [INFERRED]
  backend/app/__init__.py → backend/app/config.py
- `create_app()` --uses--> `SimulationRunner`  [INFERRED]
  backend/app/__init__.py → backend/app/services/simulation_runner.py
- `allowed_file()` --uses--> `Config`  [INFERRED]
  backend/app/api/graph.py → backend/app/config.py
- `generate_ontology()` --uses--> `OntologyGenerator`  [INFERRED]
  backend/app/api/graph.py → backend/app/services/ontology_generator.py
- `generate_ontology()` --uses--> `TextProcessor`  [INFERRED]
  backend/app/api/graph.py → backend/app/services/text_processor.py

## Import Cycles
- None detected.

## Communities (110 total, 45 thin omitted)

### Community 0 - "report_agent.py"
Cohesion: 0.09
Nodes (4): warning(), fetch_all_edges(), fetch_all_nodes(), _fetch_page_with_retry()

### Community 1 - "SimulationRunner"
Cohesion: 0.10
Nodes (4): get_run_status(), SimulationRunner, cleanup_handler(), SimulationRunState

### Community 2 - "Step4Report.vue"
Cohesion: 0.03
Nodes (37): activeSectionIndex, activeStep, agentLogLine, agentLogs, collapsedSections, completedSections, consoleLogLine, consoleLogs (+29 more)

### Community 3 - "SimulationManager"
Cohesion: 0.12
Nodes (3): get_simulation_history(), SimulationManager, SimulationState

### Community 4 - "Process.vue"
Cohesion: 0.06
Nodes (39): clearPendingUpload(), getPendingUpload(), state, buildProgress, closeDetailPanel(), currentPhase, currentProjectId, entityTypes (+31 more)

### Community 5 - "Step5Interaction.vue"
Cohesion: 0.05
Nodes (40): getSimulationProfilesRealtime(), interviewAgents(), activeTab, addLog(), chatHistory, chatHistoryCache, chatInput, chatInputRef (+32 more)

### Community 6 - "FileParser"
Cohesion: 0.12
Nodes (3): FileParser, _read_text_with_fallback(), split_text_into_chunks()

### Community 7 - "graph.py"
Cohesion: 0.07
Nodes (11): allowed_file(), delete_project(), generate_ontology(), get_project(), get_task(), list_projects(), list_tasks(), reset_project() (+3 more)

### Community 9 - "TaskManager"
Cohesion: 0.10
Nodes (4): get_prepare_status(), Task, TaskManager, TaskStatus

### Community 10 - "GraphBuilderService"
Cohesion: 0.07
Nodes (6): build_task(), delete_graph(), get_graph_data(), GraphBuilderService, GraphInfo, TextProcessor

### Community 11 - "Step3Simulation.vue"
Cohesion: 0.08
Nodes (34): getRunStatus(), getRunStatusDetail(), actionIds, addLog(), allActions, checkPlatformsCompleted(), chronologicalActions, doStartSimulation() (+26 more)

### Community 12 - "simulation.py"
Cohesion: 0.08
Nodes (9): delete_simulation(), export_simulation(), _get_report_id_for_simulation(), get_simulation_config_realtime(), get_simulation_profiles_realtime(), mask_key(), save_config(), system_status() (+1 more)

### Community 13 - "Step2EnvSetup.vue"
Cohesion: 0.09
Nodes (35): getPrepareStatus(), getSimulationConfigRealtime(), prepareSimulation(), addLog(), autoGeneratedRounds, currentStage, customMaxRounds, displayProfiles (+27 more)

### Community 14 - "MainView.vue"
Cohesion: 0.10
Nodes (35): addLog(), buildProgress, currentPhase, currentProjectId, currentStep, error, fetchGraphData(), graphData (+27 more)

### Community 15 - "README.md"
Cohesion: 0.05
Nodes (36): 1. Umgebungsvariablen konfigurieren, 2. Abhängigkeiten installieren, 3. Dienste starten, 📄 Danksagung, 1. Configure Environment Variables, 1. Wuhan University Public Opinion Simulation + MiroFish Project Introduction, 2. Dream of the Red Chamber Lost Ending Simulation, 2. Install Dependencies (+28 more)

### Community 16 - "SimulationView.vue"
Cohesion: 0.10
Nodes (26): closeSimulationEnv(), getEnvStatus(), getSimulation(), stopSimulation(), handleGoBack(), addLog(), checkAndStopRunningSimulation(), currentSimulationId (+18 more)

### Community 19 - "IPCHandler"
Cohesion: 0.07
Nodes (5): IPCHandler, main(), RedditSimulationRunner, setup_oasis_logging(), UnicodeFormatter

### Community 20 - "IPCHandler"
Cohesion: 0.07
Nodes (5): IPCHandler, main(), setup_oasis_logging(), TwitterSimulationRunner, UnicodeFormatter

### Community 21 - "SimulationIPCClient"
Cohesion: 0.12
Nodes (3): IPCCommand, IPCResponse, SimulationIPCClient

### Community 22 - "error"
Cohesion: 0.07
Nodes (29): check_report_status(), delete_report(), get_agent_log(), get_console_log(), get_generate_status(), get_graph_statistics_tool(), get_report(), get_report_by_simulation() (+21 more)

### Community 23 - "SimulationRunView.vue"
Cohesion: 0.10
Nodes (25): getSimulationConfig(), addLog(), currentSimulationId, currentStatus, graphData, graphLoading, handleNextStep(), isSimulating (+17 more)

### Community 24 - "run_parallel_simulation.py"
Cohesion: 0.06
Nodes (10): CommandType, MaxTokensWarningFilter, setup_signal_handlers(), _utf8_open(), CommandType, MaxTokensWarningFilter, setup_signal_handlers(), CommandType (+2 more)

### Community 25 - "ReportAgent"
Cohesion: 0.16
Nodes (3): chat_with_report_agent(), run_generate(), ReportAgent

### Community 26 - "os"
Cohesion: 0.19
Nodes (12): _base(), _dir(), _load(), mark_stale_runs(), _ok(), _path(), pipeline_list(), pipeline_status() (+4 more)

### Community 27 - "HistoryDatabase.vue"
Cohesion: 0.08
Nodes (13): closeModal(), containerStyle, goToProject(), goToReport(), goToSimulation(), historyContainer, hoveringCard, isExpanded (+5 more)

### Community 28 - "interview_agent"
Cohesion: 0.14
Nodes (5): get_env_status(), interview_agent(), interview_agents_batch(), interview_all_agents(), optimize_interview_prompt()

### Community 29 - "Home.vue"
Cohesion: 0.10
Nodes (17): startPipeline(), activeRuns, add(), autopilot, canSubmit, error, fileInput, files (+9 more)

### Community 30 - "ReportView.vue"
Cohesion: 0.11
Nodes (19): addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph(), loadReportData() (+11 more)

### Community 31 - "ReportManager"
Cohesion: 0.12
Nodes (3): download_report(), get_report_sections(), ReportManager

### Community 33 - "vue-router"
Cohesion: 0.09
Nodes (21): dependencies, axios, d3, vue, vue-router, devDependencies, vite, @vitejs/plugin-vue (+13 more)

### Community 34 - "InteractionView.vue"
Cohesion: 0.11
Nodes (20): getReport(), addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph() (+12 more)

### Community 40 - "simulation.js"
Cohesion: 0.12
Nodes (9): createSimulation(), startSimulation(), creatingSimulation, graphStats, handleEnterEnvSetup(), logContent, props, router (+1 more)

### Community 41 - "package.json"
Cohesion: 0.11
Nodes (17): description, devDependencies, concurrently, engines, node, license, name, scripts (+9 more)

### Community 42 - "logger.py"
Cohesion: 0.12
Nodes (7): create_app(), log_request(), log_response(), _ensure_utf8_stdout(), get_logger(), setup_logger(), main()

### Community 44 - "ZepEntityReader"
Cohesion: 0.13
Nodes (4): get_entities_by_type(), get_entity_detail(), FilteredEntities, ZepEntityReader

### Community 46 - "retry_with_backoff_async"
Cohesion: 0.15
Nodes (6): retry_with_backoff(), retry_with_backoff_async(), decorator(), decorator(), wrapper(), RetryableAPIClient

### Community 47 - "Any"
Cohesion: 0.12
Nodes (3): get_agent_stats(), get_interview_history(), get_simulation_timeline()

### Community 54 - "getProject"
Cohesion: 0.32
Nodes (9): buildGraph(), generateOntology(), getGraphData(), getProject(), getTaskStatus(), requestWithRetry(), service, chatWithReport() (+1 more)

### Community 58 - "AgentAction"
Cohesion: 0.15
Nodes (3): get_run_status_detail(), get_simulation_actions(), AgentAction

### Community 59 - "OasisAgentProfile"
Cohesion: 0.11
Nodes (3): OasisAgentProfile, show_expected_formats(), test_profile_formats()

### Community 63 - "ThemePicker.vue"
Cohesion: 0.12
Nodes (32): busy, choose(), chooseOwn(), current, error, input, ownColor, random() (+24 more)

### Community 65 - "Design-System: MiroFish „Editorial Clarity“"
Cohesion: 0.08
Nodes (24): 1. Design-Richtung & Philosophie, 2. Typografie, 3.1 Helles Design (Light Mode - Standard), 3.2 Dunkles Design (Dark Mode - `[data-theme="dark"]`), 3. Farbpalette & Nachgerechnete WCAG-AA-Kontraste, 4. Abstands- und Rastersystem, 5.1 Buttons (Schaltflächen), 5.2 Karten (Cards) (+16 more)

### Community 66 - "HistoryView.vue"
Cohesion: 0.11
Nodes (19): listPipelines(), deleteSimulation(), getSimulationHistory(), confirmDelete(), loadHistory(), activeCount, poll(), route (+11 more)

### Community 70 - "main"
Cohesion: 0.18
Nodes (3): disable_oasis_logging(), init_logging_for_simulation(), main()

### Community 71 - "getAgentLog"
Cohesion: 0.25
Nodes (8): getAgentLog(), getConsoleLog(), addLog(), emit, fetchAgentLog(), fetchConsoleLog(), startPolling(), stopPolling()

### Community 74 - "run_twitter_simulation"
Cohesion: 0.15
Nodes (7): create_model(), fetch_new_actions_from_db(), get_active_agents_for_round(), get_agent_names_from_config(), load_config(), PlatformSimulation, run_twitter_simulation()

### Community 75 - "RunView.vue"
Cohesion: 0.15
Nodes (13): getPipeline(), STEP_LABELS, STEP_ORDER, currentDetail, currentLabel, etaText, HINTS, load() (+5 more)

### Community 76 - "GraphPanel.vue"
Cohesion: 0.12
Nodes (12): emit, entityTypes, expandedSelfLoops, graphContainer, graphSvg, handleResize(), props, renderGraph() (+4 more)

### Community 77 - "vue"
Cohesion: 0.14
Nodes (13): route, showTheme, cfg, load(), masked, memoryLabel, result, save() (+5 more)

### Community 79 - "Konkrete Mobile- & Template-Fixes (Mobile First 412 px)"
Cohesion: 0.13
Nodes (15): CSS-Fix (`Home.vue` `<style scoped>`):, CSS-Fix in `Home.vue`:, CSS-Fix in `tokens.css` (wird automatisch wirksam) bzw. `App.vue`:, CSS-Fix (`MainView.vue` `<style scoped>`):, CSS-Fix (`MainView.vue` `<style scoped>`):, Globaler CSS-Klassen-Fix (Drop-in):, Konkrete Mobile- & Template-Fixes (Mobile First 412 px), Mangel 11: Touch-Targets unter 44 px (Löschen-Button, Switcher) (+7 more)

### Community 80 - "router/index.js"
Cohesion: 0.33
Nodes (3): app, router, routes

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

### Community 87 - "services/__init__.py"
Cohesion: 0.09
Nodes (9): AgentActivityConfig, EventConfig, PlatformConfig, SimulationParameters, TimeSimulationConfig, CommandStatus, CommandType, RoundSummary (+1 more)

### Community 89 - "MiroFish API (für Skripte, Agenten und eigene Oberflächen)"
Cohesion: 0.33
Nodes (5): Der eine Aufruf, der alles macht, Einzelne Stufen (wenn du selbst steuern willst), Ergebnisse abholen, MiroFish API (für Skripte, Agenten und eigene Oberflächen), Python-Beispiel

### Community 94 - "_enrich_action_context"
Cohesion: 0.25
Nodes (4): _enrich_action_context(), _get_comment_info(), _get_post_info(), _get_user_name()

### Community 98 - "Konkrete Template-Textersetzungen:"
Cohesion: 0.50
Nodes (4): 1. In `Home.vue`:, 2. In `Step1GraphBuild.vue`:, Konkrete Template-Textersetzungen:, Mangel 7: Fachjargon in Nutzertexten

### Community 99 - "prepare_simulation"
Cohesion: 0.12
Nodes (10): build_graph(), generate_report(), _check_simulation_prepared(), prepare_simulation(), run_prepare(), start_simulation(), PlatformType, SimulationStatus (+2 more)

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

## Knowledge Gaps
- **389 isolated node(s):** `mirofish-backend`, `name`, `private`, `version`, `type` (+384 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1103 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **45 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Config` connect `simulation.py` to `report_agent.py`, `SimulationRunner`, `graph.py`, `SimulationConfigGenerator`, `GraphBuilderService`, `ReportLogger`, `error`, `os`, `ReportManager`, `OasisProfileGenerator`, `MemoryProvider`, `logger.py`, `ObsidianMemoryProvider`, `ZepEntityReader`, `ZepMemoryProvider`, `ReportConsoleLogger`, `LLMClient`, `ZepToolsService`, `Any`, `MemoryFactory`, `services/__init__.py`, `prepare_simulation`?**
  _High betweenness centrality (0.108) - this node is a cross-community bridge._
- **Are the 30 inferred relationships involving `Config` (e.g. with `allowed_file()` and `build_graph()`) actually correct?**
  _`Config` has 30 INFERRED edges - model-reasoned connections that need verification._
- **What connects `mirofish-backend`, `name`, `private` to the rest of the system?**
  _389 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `report_agent.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09485815602836879 - nodes in this community are weakly interconnected._
- **Why does `SimulationRunner` connect `SimulationRunner` to `report_agent.py`, `SimulationManager`, `prepare_simulation`, `ZepGraphMemoryManager`, `ZepToolsService`, `logger.py`, `simulation.py`, `Any`, `SimulationIPCClient`, `error`, `services/__init__.py`, `AgentAction`, `interview_agent`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Are the 20 inferred relationships involving `SimulationRunner` (e.g. with `close_simulation_env()` and `delete_simulation()`) actually correct?**
  _`SimulationRunner` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Should `SimulationRunner` be split into smaller, more focused modules?**
  _Cohesion score 0.09747899159663866 - nodes in this community are weakly interconnected._