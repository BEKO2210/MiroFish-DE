# Graph Report - mirofish-expert  (2026-10-13)

## Corpus Check
- 89 files · ~402,000 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: (none) 6, .example 1, .lock 1)

## Summary
- 2184 nodes · 4289 edges · 102 communities (71 shown, 31 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 318 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `cede2aba`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- simulation_manager.py
- start_simulation
- Step4Report.vue
- SimulationManager
- Process.vue
- Step5Interaction.vue
- FileParser
- ProjectManager
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
- route
- Home.vue
- ReportView.vue
- ReportManager
- OasisProfileGenerator
- frontend/package.json
- InteractionView.vue
- MemoryProvider
- graph.py
- AgentActivity
- ParallelIPCHandler
- SimulationLogManager
- simulation.js
- package.json
- logger.py
- ObsidianMemoryProvider
- ZepEntityReader
- ZepToolsService
- retry_with_backoff_async
- SimulationRunner
- OntologyGenerator
- ZepMemoryProvider
- ZepGraphMemoryUpdater
- MemoryNode
- ReportConsoleLogger
- ActionLogger
- getGraphData
- zep_provider.py
- build_task
- MemoryEdge
- AgentAction
- route
- stopSimulation
- vue-i18n
- InsightForgeResult
- ThemePicker.vue
- MemorySearchResult
- Design-System: MiroFish „Editorial Clarity“
- HistoryView.vue
- I18N-Bericht
- pendingUpload.js
- main
- fetchAgentLog
- run_twitter_simulation
- RunView.vue
- GraphPanel.vue
- SettingsView.vue
- SimulationIPCServer
- Konkrete Mobile- & Template-Fixes (Mobile First 412 px)
- vue
- SwarmCanvas.vue
- Design-Audit: MiroFish Web-App (Mobile First & Barrierefreiheit)
- 3. Umfassender Ansichten-Audit (View-by-View Breakdown)
- 2. Bestätigung und Tiefenanalyse der bekannten Kernmängel
- services/__init__.py
- MiroFish API (für Skripte, Agenten und eigene Oberflächen)
- .cleanup_all_simulations
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
- `get_project()` --uses--> `ProjectManager`  [INFERRED]
  backend/app/api/graph.py → backend/app/models/project.py
- `reset_project()` --uses--> `ProjectStatus`  [INFERRED]
  backend/app/api/graph.py → backend/app/models/project.py

## Import Cycles
- None detected.

## Communities (102 total, 31 thin omitted)

### Community 0 - "simulation_manager.py"
Cohesion: 0.09
Nodes (5): SimulationParameters, PlatformType, SimulationStatus, show_expected_formats(), test_profile_formats()

### Community 2 - "Step4Report.vue"
Cohesion: 0.03
Nodes (38): activeSectionIndex, activeStep, agentLogLine, agentLogs, collapsedSections, completedSections, consoleLogLine, consoleLogs (+30 more)

### Community 3 - "SimulationManager"
Cohesion: 0.06
Nodes (11): close_simulation_env(), create_simulation(), download_simulation_config(), get_simulation(), get_simulation_config(), get_simulation_history(), get_simulation_profiles(), list_simulations() (+3 more)

### Community 4 - "Process.vue"
Cohesion: 0.07
Nodes (37): buildProgress, closeDetailPanel(), currentPhase, currentProjectId, entityTypes, error, fetchGraphData(), graphContainer (+29 more)

### Community 5 - "Step5Interaction.vue"
Cohesion: 0.05
Nodes (43): getAgentLog(), getReport(), getSimulationProfilesRealtime(), interviewAgents(), activeTab, addLog(), chatHistory, chatHistoryCache (+35 more)

### Community 7 - "ProjectManager"
Cohesion: 0.08
Nodes (5): delete_project(), list_projects(), reset_project(), Project, ProjectManager

### Community 8 - "SimulationConfigGenerator"
Cohesion: 0.08
Nodes (3): AgentActivityConfig, EventConfig, SimulationConfigGenerator

### Community 9 - "TaskManager"
Cohesion: 0.10
Nodes (3): get_prepare_status(), Task, TaskManager

### Community 10 - "GraphBuilderService"
Cohesion: 0.10
Nodes (4): delete_graph(), get_graph_data(), GraphBuilderService, GraphInfo

### Community 11 - "Step3Simulation.vue"
Cohesion: 0.08
Nodes (36): getRunStatus(), getRunStatusDetail(), startSimulation(), actionIds, addLog(), allActions, checkPlatformsCompleted(), chronologicalActions (+28 more)

### Community 12 - "simulation.py"
Cohesion: 0.06
Nodes (12): export_simulation(), get_entities_by_type(), get_graph_entities(), get_simulation_config_realtime(), get_simulation_profiles_realtime(), mask_key(), save_config(), system_status() (+4 more)

### Community 13 - "Step2EnvSetup.vue"
Cohesion: 0.08
Nodes (36): getPrepareStatus(), getSimulationConfigRealtime(), prepareSimulation(), addLog(), autoGeneratedRounds, currentStage, customMaxRounds, displayProfiles (+28 more)

### Community 14 - "MainView.vue"
Cohesion: 0.09
Nodes (38): getProject(), getPendingUpload(), addLog(), buildProgress, currentPhase, currentProjectId, currentStep, error (+30 more)

### Community 15 - "README.md"
Cohesion: 0.05
Nodes (36): 1. Umgebungsvariablen konfigurieren, 2. Abhängigkeiten installieren, 3. Dienste starten, 📄 Danksagung, 1. Configure Environment Variables, 1. Wuhan University Public Opinion Simulation + MiroFish Project Introduction, 2. Dream of the Red Chamber Lost Ending Simulation, 2. Install Dependencies (+28 more)

### Community 16 - "SimulationView.vue"
Cohesion: 0.10
Nodes (21): getSimulation(), addLog(), currentSimulationId, currentStatus, graphData, graphLoading, handleNextStep(), leftPanelStyle (+13 more)

### Community 19 - "IPCHandler"
Cohesion: 0.07
Nodes (5): IPCHandler, main(), RedditSimulationRunner, setup_oasis_logging(), UnicodeFormatter

### Community 20 - "IPCHandler"
Cohesion: 0.07
Nodes (5): IPCHandler, main(), setup_oasis_logging(), TwitterSimulationRunner, UnicodeFormatter

### Community 21 - "SimulationIPCClient"
Cohesion: 0.11
Nodes (3): IPCCommand, IPCResponse, SimulationIPCClient

### Community 22 - "error"
Cohesion: 0.08
Nodes (23): chat_with_report_agent(), check_report_status(), delete_report(), download_report(), generate_report(), get_agent_log(), get_console_log(), get_generate_status() (+15 more)

### Community 23 - "SimulationRunView.vue"
Cohesion: 0.09
Nodes (25): getSimulationConfig(), addLog(), currentSimulationId, currentStatus, graphData, graphLoading, handleNextStep(), isSimulating (+17 more)

### Community 24 - "run_parallel_simulation.py"
Cohesion: 0.06
Nodes (10): CommandType, MaxTokensWarningFilter, setup_signal_handlers(), _utf8_open(), CommandType, MaxTokensWarningFilter, setup_signal_handlers(), CommandType (+2 more)

### Community 25 - "ReportAgent"
Cohesion: 0.10
Nodes (3): run_generate(), ReportAgent, ReportSection

### Community 26 - "os"
Cohesion: 0.15
Nodes (13): _base(), _dir(), _load(), mark_stale_runs(), _ok(), _path(), pipeline_list(), pipeline_status() (+5 more)

### Community 27 - "HistoryDatabase.vue"
Cohesion: 0.08
Nodes (14): closeModal(), containerStyle, goToProject(), goToReport(), goToSimulation(), historyContainer, hoveringCard, isExpanded (+6 more)

### Community 28 - "route"
Cohesion: 0.11
Nodes (7): delete_simulation(), get_env_status(), get_run_status(), interview_agent(), interview_agents_batch(), interview_all_agents(), optimize_interview_prompt()

### Community 29 - "Home.vue"
Cohesion: 0.10
Nodes (21): startPipeline(), activeRuns, add(), autopilot, canSubmit, error, fileInput, files (+13 more)

### Community 30 - "ReportView.vue"
Cohesion: 0.10
Nodes (20): addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph(), loadReportData() (+12 more)

### Community 31 - "ReportManager"
Cohesion: 0.06
Nodes (3): Report, ReportManager, ReportOutline

### Community 32 - "OasisProfileGenerator"
Cohesion: 0.05
Nodes (4): OasisAgentProfile, OasisProfileGenerator, generate_single_profile(), EntityNode

### Community 33 - "frontend/package.json"
Cohesion: 0.09
Nodes (21): dependencies, axios, d3, vue, vue-i18n, vue-router, devDependencies, vite (+13 more)

### Community 34 - "InteractionView.vue"
Cohesion: 0.09
Nodes (21): { locale, t }, addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph() (+13 more)

### Community 36 - "graph.py"
Cohesion: 0.16
Nodes (4): build_graph(), ProjectStatus, TaskStatus, TextProcessor

### Community 40 - "simulation.js"
Cohesion: 0.12
Nodes (9): createSimulation(), creatingSimulation, graphStats, handleEnterEnvSetup(), logContent, props, router, selectedOntologyItem (+1 more)

### Community 41 - "package.json"
Cohesion: 0.11
Nodes (17): description, devDependencies, concurrently, engines, node, license, name, scripts (+9 more)

### Community 42 - "logger.py"
Cohesion: 0.13
Nodes (6): create_app(), log_request(), log_response(), _ensure_utf8_stdout(), get_logger(), setup_logger()

### Community 44 - "ZepEntityReader"
Cohesion: 0.12
Nodes (4): generate_profiles(), get_entity_detail(), FilteredEntities, ZepEntityReader

### Community 45 - "ZepToolsService"
Cohesion: 0.04
Nodes (7): AgentInterview, EdgeInfo, InterviewResult, NodeInfo, PanoramaResult, SearchResult, ZepToolsService

### Community 46 - "retry_with_backoff_async"
Cohesion: 0.15
Nodes (6): retry_with_backoff(), retry_with_backoff_async(), decorator(), decorator(), wrapper(), RetryableAPIClient

### Community 47 - "SimulationRunner"
Cohesion: 0.10
Nodes (4): get_agent_stats(), get_interview_history(), get_simulation_timeline(), SimulationRunner

### Community 54 - "getGraphData"
Cohesion: 0.35
Nodes (8): buildGraph(), generateOntology(), getGraphData(), getTaskStatus(), requestWithRetry(), service, chatWithReport(), generateReport()

### Community 55 - "zep_provider.py"
Cohesion: 0.23
Nodes (4): warning(), fetch_all_edges(), fetch_all_nodes(), _fetch_page_with_retry()

### Community 58 - "AgentAction"
Cohesion: 0.15
Nodes (3): get_run_status_detail(), get_simulation_actions(), AgentAction

### Community 59 - "route"
Cohesion: 0.29
Nodes (3): get_project(), get_task(), list_tasks()

### Community 60 - "stopSimulation"
Cohesion: 0.38
Nodes (7): closeSimulationEnv(), getEnvStatus(), stopSimulation(), handleGoBack(), stopGraphRefresh(), checkAndStopRunningSimulation(), forceStopSimulation()

### Community 61 - "vue-i18n"
Cohesion: 0.29
Nodes (3): { t }, savedLanguage, vue-i18n

### Community 63 - "ThemePicker.vue"
Cohesion: 0.11
Nodes (34): busy, choose(), chooseOwn(), current, error, input, isDefault, ownColor (+26 more)

### Community 65 - "Design-System: MiroFish „Editorial Clarity“"
Cohesion: 0.08
Nodes (24): 1. Design-Richtung & Philosophie, 2. Typografie, 3.1 Helles Design (Light Mode - Standard), 3.2 Dunkles Design (Dark Mode - `[data-theme="dark"]`), 3. Farbpalette & Nachgerechnete WCAG-AA-Kontraste, 4. Abstands- und Rastersystem, 5.1 Buttons (Schaltflächen), 5.2 Karten (Cards) (+16 more)

### Community 66 - "HistoryView.vue"
Cohesion: 0.14
Nodes (17): deleteSimulation(), getSimulationHistory(), confirmDelete(), loadHistory(), deleting, doDelete(), error, fmt() (+9 more)

### Community 67 - "I18N-Bericht"
Cohesion: 0.33
Nodes (5): Bewusst nicht übersetzte Stellen, I18N-Bericht, Offene Punkte, Prüfung, Umfang

### Community 70 - "main"
Cohesion: 0.18
Nodes (3): disable_oasis_logging(), init_logging_for_simulation(), main()

### Community 71 - "fetchAgentLog"
Cohesion: 0.29
Nodes (7): getConsoleLog(), addLog(), emit, fetchAgentLog(), fetchConsoleLog(), startPolling(), stopPolling()

### Community 74 - "run_twitter_simulation"
Cohesion: 0.15
Nodes (7): create_model(), fetch_new_actions_from_db(), get_active_agents_for_round(), get_agent_names_from_config(), load_config(), PlatformSimulation, run_twitter_simulation()

### Community 75 - "RunView.vue"
Cohesion: 0.14
Nodes (14): getPipeline(), STEP_LABELS, STEP_ORDER, currentDetail, currentLabel, etaText, HINTS, load() (+6 more)

### Community 76 - "GraphPanel.vue"
Cohesion: 0.12
Nodes (13): emit, entityTypes, expandedSelfLoops, graphContainer, graphSvg, handleResize(), props, renderGraph() (+5 more)

### Community 77 - "SettingsView.vue"
Cohesion: 0.15
Nodes (11): cfg, load(), masked, memoryLabel, result, save(), saving, showTheme (+3 more)

### Community 79 - "Konkrete Mobile- & Template-Fixes (Mobile First 412 px)"
Cohesion: 0.13
Nodes (15): CSS-Fix (`Home.vue` `<style scoped>`):, CSS-Fix in `Home.vue`:, CSS-Fix in `tokens.css` (wird automatisch wirksam) bzw. `App.vue`:, CSS-Fix (`MainView.vue` `<style scoped>`):, CSS-Fix (`MainView.vue` `<style scoped>`):, Globaler CSS-Klassen-Fix (Drop-in):, Konkrete Mobile- & Template-Fixes (Mobile First 412 px), Mangel 11: Touch-Targets unter 44 px (Löschen-Button, Switcher) (+7 more)

### Community 80 - "vue"
Cohesion: 0.13
Nodes (14): listPipelines(), route, showTheme, { t }, activeCount, poll(), route, { t } (+6 more)

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
Cohesion: 0.11
Nodes (7): PlatformConfig, TimeSimulationConfig, CommandStatus, CommandType, RoundSummary, RunnerStatus, ZepGraphMemoryManager

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
Cohesion: 0.18
Nodes (7): allowed_file(), generate_ontology(), _check_simulation_prepared(), prepare_simulation(), run_prepare(), debug(), info()

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
- **418 isolated node(s):** `mirofish-backend`, `name`, `private`, `version`, `type` (+413 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1155 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **31 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Config` connect `simulation.py` to `simulation_manager.py`, `ProjectManager`, `SimulationConfigGenerator`, `GraphBuilderService`, `ReportLogger`, `error`, `os`, `route`, `ReportManager`, `OasisProfileGenerator`, `MemoryProvider`, `graph.py`, `logger.py`, `ObsidianMemoryProvider`, `ZepEntityReader`, `ZepToolsService`, `SimulationRunner`, `ZepMemoryProvider`, `ReportConsoleLogger`, `zep_provider.py`, `services/__init__.py`, `prepare_simulation`?**
  _High betweenness centrality (0.107) - this node is a cross-community bridge._
- **Are the 30 inferred relationships involving `Config` (e.g. with `allowed_file()` and `build_graph()`) actually correct?**
  _`Config` has 30 INFERRED edges - model-reasoned connections that need verification._
- **What connects `mirofish-backend`, `name`, `private` to the rest of the system?**
  _418 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `simulation_manager.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08888888888888889 - nodes in this community are weakly interconnected._
- **Why does `SimulationRunner` connect `SimulationRunner` to `simulation_manager.py`, `start_simulation`, `SimulationManager`, `.cleanup_all_simulations`, `logger.py`, `simulation.py`, `ZepToolsService`, `SimulationIPCClient`, `services/__init__.py`, `AgentAction`, `route`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Are the 20 inferred relationships involving `SimulationRunner` (e.g. with `close_simulation_env()` and `delete_simulation()`) actually correct?**
  _`SimulationRunner` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Should `start_simulation` be split into smaller, more focused modules?**
  _Cohesion score 0.12 - nodes in this community are weakly interconnected._