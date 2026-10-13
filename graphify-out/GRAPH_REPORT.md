# Graph Report - mirofish-ux-b  (2026-10-13)

## Corpus Check
- 126 files · ~484,386 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 7, .example 1, .lock 1)

## Summary
- 2495 nodes · 4973 edges · 128 communities (72 shown, 56 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 367 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2ffe5789`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- logger.py
- SimulationRunner
- Step4Report.vue
- SimulationManager
- Process.vue
- Step5Interaction.vue
- simulation_manager.py
- ProjectManager
- SimulationConfigGenerator
- Config
- Step3Simulation.vue
- mockApi.ts
- Step2EnvSetup.vue
- MainView.vue
- README-EN.md
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
- simulation.py
- Home.vue
- ReportView.vue
- route
- 3. Detaillierte Spezifikation nach Seiten und Komponenten
- GraphPanel.vue
- InteractionView.vue
- MemoryProvider
- AgentActivity
- ParallelIPCHandler
- SimulationLogManager
- graph.js
- package.json
- get_logger
- SettingsView.vue
- ZepEntityReader
- ZepToolsService
- retry_with_backoff_async
- OasisAgentProfile
- OntologyGenerator
- ProjectStatus
- ZepGraphMemoryUpdater
- ZepMemoryProvider
- ReportConsoleLogger
- ActionLogger
- ObsidianMemoryProvider
- Übersicht
- .search_graph
- MiroFish E2E (Playwright)
- cleanup.py
- OasisProfileGenerator
- services/__init__.py
- EdgeInfo
- NodeInfo
- ThemePicker.vue
- TaskStatus
- Design-System: MiroFish „Editorial Clarity“
- HistoryView.vue
- build_graph
- TextProcessor
- init_logging_for_simulation
- fetchAgentLog
- MemoryNode
- MemoryEdge
- compilerOptions
- RunView.vue
- simulation.js
- Polish-Report
- pendingUpload.js
- Konkrete Mobile- & Template-Fixes (Mobile First 412 px)
- SwarmCanvas.vue
- MemorySearchResult
- Design-Audit: MiroFish Web-App (Mobile First & Barrierefreiheit)
- 3. Umfassender Ansichten-Audit (View-by-View Breakdown)
- 2. Bestätigung und Tiefenanalyse der bekannten Kernmängel
- UX-REPORT – belkis (Abschnitt 3.1A, 3.3–3.6, global)
- .panorama_search
- conftest.py
- test_profile_format.py
- _enrich_action_context
- GraphBuilderService
- InsightForgeResult
- mirofish-backend
- Konkrete Template-Textersetzungen:
- TaskManager
- Mangel 3: Leere Flächen mit einzelnen Rauten-Symbolen
- Mangel 4: Karten der „Simulationsaufzeichnungen“ am Handy links/rechts abgeschnitten
- Mangel 2: Badge „Elegante universelle Schwarm-Intelligenz-Engine“ bricht um
- Mangel 5: Im Prompt-Feld überlappt Badge „Engine: MiroFish-V1.0“ den Platzhaltertext
- Mangel 10: Fehlende Zeitschätzung und Statusführung bei langen Läufen (Minuten bis 1 Stunde)
- AgentInterview
- MaxTokensWarningFilter
- sample-upload.md
- ontology_generator.py
- ROADMAP.md
- REPORT-UI.md
- setup_oasis_logging
- setup_oasis_logging
- I18N-Bericht
- Step1GraphBuild.vue
- InterviewResult
- MaxTokensWarningFilter
- setup_signal_handlers
- UX-REPORT-codex.md
- setup_signal_handlers
- vue
- MaxTokensWarningFilter
- setup_signal_handlers
- docker-entrypoint.sh

## God Nodes (most connected - your core abstractions)
1. `Config` - 63 edges
2. `error()` - 60 edges
3. `SimulationRunner` - 54 edges
4. `ReportManager` - 48 edges
5. `OasisProfileGenerator` - 34 edges
6. `ZepToolsService` - 34 edges
7. `ProjectManager` - 33 edges
8. `ObsidianMemoryProvider` - 33 edges
9. `SimulationManager` - 33 edges
10. `get_logger()` - 30 edges

## Surprising Connections (you probably didn't know these)
- `Automatisch` --references--> `mark_stale_runs()`  [INFERRED]
  docs/CLEANUP.md → backend/app/api/pipeline.py
- `Übersicht` --references--> `_get_default_platform()`  [INFERRED]
  docs/UPSTREAM.md → backend/app/api/simulation.py
- `Projekt und Graph` --references--> `delete_project_cascade()`  [INFERRED]
  docs/CLEANUP.md → backend/app/services/cleanup.py
- `Simulation löschen` --references--> `delete_simulation_cascade()`  [INFERRED]
  docs/CLEANUP.md → backend/app/services/cleanup.py
- `Durchlauf löschen` --references--> `delete_pipeline_cascade()`  [INFERRED]
  docs/CLEANUP.md → backend/app/services/cleanup.py

## Import Cycles
- None detected.

## Communities (128 total, 56 thin omitted)

### Community 0 - "logger.py"
Cohesion: 0.10
Nodes (5): MemoryFactory, warning(), fetch_all_edges(), fetch_all_nodes(), _fetch_page_with_retry()

### Community 1 - "SimulationRunner"
Cohesion: 0.05
Nodes (8): get_run_status(), get_run_status_detail(), get_simulation_history(), start_simulation(), AgentAction, SimulationRunner, cleanup_handler(), SimulationRunState

### Community 2 - "Step4Report.vue"
Cohesion: 0.03
Nodes (39): activeSectionIndex, activeStep, activeTocIndex, agentLogLine, agentLogs, collapsedSections, completedSections, consoleLogLine (+31 more)

### Community 3 - "SimulationManager"
Cohesion: 0.07
Nodes (11): close_simulation_env(), create_simulation(), get_simulation(), list_simulations(), prepare_simulation(), run_prepare(), stop_simulation(), PlatformType (+3 more)

### Community 4 - "Process.vue"
Cohesion: 0.07
Nodes (36): getProject(), buildProgress, closeDetailPanel(), currentPhase, currentProjectId, entityTypes, error, fetchGraphData() (+28 more)

### Community 5 - "Step5Interaction.vue"
Cohesion: 0.05
Nodes (43): getAgentLog(), getReport(), getSimulationProfilesRealtime(), interviewAgents(), activeTab, addLog(), chatHistory, chatHistoryCache (+35 more)

### Community 6 - "simulation_manager.py"
Cohesion: 0.11
Nodes (5): PlatformConfig, SimulationParameters, TimeSimulationConfig, create_chat_completion(), is_gpt5_family()

### Community 7 - "ProjectManager"
Cohesion: 0.13
Nodes (3): delete_project(), generate_ontology(), ProjectManager

### Community 8 - "SimulationConfigGenerator"
Cohesion: 0.11
Nodes (4): AgentActivityConfig, EventConfig, SimulationConfigGenerator, EntityNode

### Community 10 - "Config"
Cohesion: 0.07
Nodes (9): allowed_file(), list_models(), mask_key(), _ollama_root(), save_config(), system_models(), system_status(), Config (+1 more)

### Community 11 - "Step3Simulation.vue"
Cohesion: 0.08
Nodes (36): getRunStatus(), getRunStatusDetail(), startSimulation(), actionIds, addLog(), allActions, checkPlatformsCompleted(), chronologicalActions (+28 more)

### Community 12 - "mockApi.ts"
Cohesion: 0.06
Nodes (50): devDependencies, @axe-core/playwright, @playwright/test, typescript, name, private, scripts, test (+42 more)

### Community 13 - "Step2EnvSetup.vue"
Cohesion: 0.10
Nodes (37): Offene Frontend-Punkte (nicht angewendet, Umbau läuft parallel), getSimulationConfigRealtime(), prepareSimulation(), addLog(), autoGeneratedRounds, currentStage, customMaxRounds, displayProfiles (+29 more)

### Community 14 - "MainView.vue"
Cohesion: 0.09
Nodes (37): getGraphData(), addLog(), buildProgress, currentPhase, currentProjectId, currentStep, error, fetchGraphData() (+29 more)

### Community 15 - "README-EN.md"
Cohesion: 0.05
Nodes (40): Der eine Aufruf, der alles macht, Einzelne Stufen (wenn du selbst steuern willst), Ergebnisse abholen, MiroFish API (für Skripte, Agenten und eigene Oberflächen), Python-Beispiel, 1. Ollama und Modelle, 2a. Start mit Docker (empfohlen), 2b. Start aus dem Quellcode (+32 more)

### Community 16 - "SimulationRunView.vue"
Cohesion: 0.09
Nodes (30): closeSimulationEnv(), getSimulationConfig(), addLog(), currentSimulationId, currentStatus, graphData, graphLoading, handleGoBack() (+22 more)

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
Cohesion: 0.08
Nodes (4): IPCCommand, IPCResponse, SimulationIPCClient, SimulationIPCServer

### Community 22 - "error"
Cohesion: 0.07
Nodes (22): get_graph_data(), chat_with_report_agent(), check_report_status(), delete_report(), download_report(), generate_report(), get_agent_log(), get_console_log() (+14 more)

### Community 23 - "SimulationView.vue"
Cohesion: 0.09
Nodes (28): getEnvStatus(), getSimulation(), stopSimulation(), addLog(), checkAndStopRunningSimulation(), currentSimulationId, currentStatus, forceStopSimulation() (+20 more)

### Community 24 - "run_parallel_simulation.py"
Cohesion: 0.13
Nodes (4): CommandType, _utf8_open(), CommandType, CommandType

### Community 25 - "ReportAgent"
Cohesion: 0.05
Nodes (5): run_generate(), Report, ReportAgent, ReportOutline, ReportSection

### Community 26 - "os"
Cohesion: 0.07
Nodes (20): _base(), _dir(), _load(), mark_stale_runs(), _ok(), _path(), pipeline_list(), pipeline_status() (+12 more)

### Community 27 - "HistoryDatabase.vue"
Cohesion: 0.08
Nodes (14): closeModal(), containerStyle, goToProject(), goToReport(), goToSimulation(), historyContainer, hoveringCard, isExpanded (+6 more)

### Community 28 - "simulation.py"
Cohesion: 0.06
Nodes (22): download_simulation_config(), download_simulation_script(), generate_profiles(), get_agent_stats(), _get_default_platform(), get_entities_by_type(), get_entity_detail(), get_env_status() (+14 more)

### Community 29 - "Home.vue"
Cohesion: 0.09
Nodes (22): startPipeline(), activeRuns, add(), autopilot, canSubmit, error, fileInput, files (+14 more)

### Community 30 - "ReportView.vue"
Cohesion: 0.08
Nodes (22): { locale, t }, addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph() (+14 more)

### Community 31 - "route"
Cohesion: 0.15
Nodes (5): get_project(), get_task(), list_projects(), list_tasks(), reset_project()

### Community 32 - "3. Detaillierte Spezifikation nach Seiten und Komponenten"
Cohesion: 0.06
Nodes (33): 1. Barrierefreiheit (e2e-Befund), 1. Gemeinsame Header-Architektur am Smartphone, 1. Kurzurteil, 1. Mobil-Verhalten, 1. Mobil-Verhalten (`04-durchlauf-mobil.png`), 1. Mobil-Verhalten (Samsung S23 Ultra, 412 px), 1. Problemstellung & IST-Zustand (Screenshots 10 & 11), 2. Befundtabelle (+25 more)

### Community 33 - "GraphPanel.vue"
Cohesion: 0.05
Nodes (36): dependencies, axios, d3, vue, vue-i18n, vue-router, devDependencies, vite (+28 more)

### Community 34 - "InteractionView.vue"
Cohesion: 0.09
Nodes (21): addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph(), loadReportData() (+13 more)

### Community 39 - "SimulationLogManager"
Cohesion: 0.13
Nodes (3): SimulationLogManager, load_config(), main()

### Community 40 - "graph.js"
Cohesion: 0.38
Nodes (7): buildGraph(), generateOntology(), getTaskStatus(), requestWithRetry(), service, chatWithReport(), generateReport()

### Community 41 - "package.json"
Cohesion: 0.11
Nodes (17): description, devDependencies, concurrently, engines, node, license, name, scripts (+9 more)

### Community 42 - "get_logger"
Cohesion: 0.19
Nodes (8): create_app(), log_request(), log_response(), require_api_token(), token_ok(), _ensure_utf8_stdout(), get_logger(), setup_logger()

### Community 43 - "SettingsView.vue"
Cohesion: 0.11
Nodes (16): baseUrl(), cfg, load(), masked, memoryLabel, models, result, save() (+8 more)

### Community 46 - "retry_with_backoff_async"
Cohesion: 0.15
Nodes (6): retry_with_backoff(), retry_with_backoff_async(), decorator(), decorator(), wrapper(), RetryableAPIClient

### Community 55 - "Übersicht"
Cohesion: 0.19
Nodes (6): _coerce_to_str(), _coerce_to_str_list(), LLMResponseError, Neuerungen aus dem Original (666ghj/MiroFish), Prüfung, Übersicht

### Community 57 - "MiroFish E2E (Playwright)"
Cohesion: 0.14
Nodes (12): frontend(), 1. Fußmenü verdeckt Bedienelemente (Handy), 2. Barrierefreiheit (axe serious/critical), Bekannte Befunde (E2E), Nicht als App-Bug gewertet (Tests angepasst), Bekannte App-Fehler, CI, Live gegen eine laufende Instanz (+4 more)

### Community 58 - "cleanup.py"
Cohesion: 0.06
Nodes (49): delete_pipeline(), delete_simulation(), _child(), CleanupBusy, CleanupError, _delete_graph_storage(), delete_pipeline_cascade(), _delete_pipelines_for_simulation() (+41 more)

### Community 60 - "services/__init__.py"
Cohesion: 0.15
Nodes (5): CommandStatus, CommandType, RoundSummary, RunnerStatus, ZepGraphMemoryManager

### Community 63 - "ThemePicker.vue"
Cohesion: 0.11
Nodes (34): busy, choose(), chooseOwn(), current, error, input, isDefault, ownColor (+26 more)

### Community 65 - "Design-System: MiroFish „Editorial Clarity“"
Cohesion: 0.08
Nodes (24): 1. Design-Richtung & Philosophie, 2. Typografie, 3.1 Helles Design (Light Mode - Standard), 3.2 Dunkles Design (Dark Mode - `[data-theme="dark"]`), 3. Farbpalette & Nachgerechnete WCAG-AA-Kontraste, 4. Abstands- und Rastersystem, 5.1 Buttons (Schaltflächen), 5.2 Karten (Cards) (+16 more)

### Community 66 - "HistoryView.vue"
Cohesion: 0.15
Nodes (17): deletePipeline(), deleteSimulation(), getSimulationHistory(), confirmDelete(), loadHistory(), deleting, doDelete(), error (+9 more)

### Community 67 - "build_graph"
Cohesion: 0.25
Nodes (3): build_graph(), build_task(), debug()

### Community 68 - "TextProcessor"
Cohesion: 0.10
Nodes (4): TextProcessor, FileParser, _read_text_with_fallback(), split_text_into_chunks()

### Community 71 - "fetchAgentLog"
Cohesion: 0.29
Nodes (7): getConsoleLog(), addLog(), emit, fetchAgentLog(), fetchConsoleLog(), startPolling(), stopPolling()

### Community 74 - "compilerOptions"
Cohesion: 0.17
Nodes (11): compilerOptions, esModuleInterop, module, moduleResolution, noEmit, resolveJsonModule, skipLibCheck, strict (+3 more)

### Community 75 - "RunView.vue"
Cohesion: 0.10
Nodes (18): getPipeline(), STEP_LABELS, STEP_ORDER, cleanedUp, currentDetail, currentLabel, etaText, HINTS (+10 more)

### Community 77 - "Polish-Report"
Cohesion: 0.29
Nodes (6): Ausgelassen, Checks, Geändert, npm audit (`cd frontend && npm audit --omit=dev`), Offen, Polish-Report

### Community 78 - "pendingUpload.js"
Cohesion: 0.33
Nodes (5): clearPendingUpload(), getPendingUpload(), state, handleNewProject(), initProject()

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

### Community 89 - "UX-REPORT – belkis (Abschnitt 3.1A, 3.3–3.6, global)"
Cohesion: 0.40
Nodes (4): Abnahme, Nicht angefasst, UX-REPORT – belkis (Abschnitt 3.1A, 3.3–3.6, global), Änderungen

### Community 94 - "_enrich_action_context"
Cohesion: 0.20
Nodes (5): _enrich_action_context(), fetch_new_actions_from_db(), _get_comment_info(), _get_post_info(), _get_user_name()

### Community 95 - "GraphBuilderService"
Cohesion: 0.11
Nodes (3): delete_graph(), GraphBuilderService, GraphInfo

### Community 98 - "Konkrete Template-Textersetzungen:"
Cohesion: 0.50
Nodes (4): 1. In `Home.vue`:, 2. In `Step1GraphBuild.vue`:, Konkrete Template-Textersetzungen:, Mangel 7: Fachjargon in Nutzertexten

### Community 99 - "TaskManager"
Cohesion: 0.13
Nodes (4): _check_simulation_prepared(), get_prepare_status(), Task, TaskManager

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
Cohesion: 0.15
Nodes (7): _ascii_fold(), resolve_entity_name(), _to_pascal_case(), _to_upper_snake_case(), normalize_ontology_attribute(), normalize_ontology_attributes(), normalize_ontology_source_targets()

### Community 114 - "I18N-Bericht"
Cohesion: 0.33
Nodes (5): Bewusst nicht übersetzte Stellen, I18N-Bericht, Offene Punkte, Prüfung, Umfang

### Community 115 - "Step1GraphBuild.vue"
Cohesion: 0.17
Nodes (9): createSimulation(), creatingSimulation, graphStats, handleEnterEnvSetup(), logContent, props, router, selectedOntologyItem (+1 more)

### Community 128 - "vue"
Cohesion: 0.09
Nodes (17): listPipelines(), route, showTheme, { t }, { t }, activeCount, poll(), route (+9 more)

## Knowledge Gaps
- **515 isolated node(s):** `mirofish-backend`, `docker-entrypoint.sh script`, `name`, `private`, `version` (+510 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1309 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **56 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Neuerungen aus dem Original (666ghj/MiroFish)` connect `Übersicht` to `Step2EnvSetup.vue`?**
  _High betweenness centrality (0.291) - this node is a cross-community bridge._
- **Are the 33 inferred relationships involving `Config` (e.g. with `allowed_file()` and `build_graph()`) actually correct?**
  _`Config` has 33 INFERRED edges - model-reasoned connections that need verification._
- **What connects `mirofish-backend`, `docker-entrypoint.sh script`, `name` to the rest of the system?**
  _515 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `logger.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0971322849213691 - nodes in this community are weakly interconnected._
- **Why does `Offene Frontend-Punkte (nicht angewendet, Umbau läuft parallel)` connect `Step2EnvSetup.vue` to `Step3Simulation.vue`, `Übersicht`?**
  _High betweenness centrality (0.290) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `error()` (e.g. with `generate_ontology()` and `.chat_json()`) actually correct?**
  _`error()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `SimulationRunner` be split into smaller, more focused modules?**
  _Cohesion score 0.0505175983436853 - nodes in this community are weakly interconnected._