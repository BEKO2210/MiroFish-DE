# Graph Report - mirofish-ux-d  (2026-10-13)

## Corpus Check
- 130 files · ~543,855 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 7, .example 1, .lock 1)

## Summary
- 2524 nodes · 5020 edges · 109 communities (72 shown, 37 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 367 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c3995194`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Config
- SimulationRunState
- Step4Report.vue
- SimulationManager
- Process.vue
- Step5Interaction.vue
- delete_simulation_cascade
- ProjectManager
- SimulationConfigGenerator
- test_cleanup.py
- system.py
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
- ReportManager
- SimulationView.vue
- run_reddit_simulation.py
- .generate_report
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
- getGraphData
- package.json
- app/__init__.py
- SettingsView.vue
- ZepEntityReader
- Any
- retry_with_backoff_async
- OasisAgentProfile
- ontology_generator.py
- .get_project
- ZepGraphMemoryUpdater
- ObsidianMemoryProvider
- ReportConsoleLogger
- action_logger.py
- .chat_json
- .chat
- ZepToolsService
- MiroFish E2E (Playwright)
- cleanup.py
- OasisProfileGenerator
- services/__init__.py
- delete_pipeline_cascade
- AgentAction
- ThemePicker.vue
- TaskManager
- Design-System: MiroFish „Editorial Clarity“
- .cleanup_all_simulations
- build_graph
- FileParser
- Änderungen
- getAgentLog
- .list_projects
- UX-REPORT – Cursor Live (Audit-2 Nacharbeit)
- compilerOptions
- RunView.vue
- CleanupError
- generate_ontology
- Konkrete Mobile- & Template-Fixes (Mobile First 412 px)
- SwarmCanvas.vue
- _is_response_format_unsupported
- Design-Audit: MiroFish Web-App (Mobile First & Barrierefreiheit)
- 3. Umfassender Ansichten-Audit (View-by-View Breakdown)
- 2. Bestätigung und Tiefenanalyse der bekannten Kernmängel
- UX-REPORT – belkis (Abschnitt 3.1A, 3.3–3.6, global)
- sys
- test_profile_format.py
- run_parallel_simulation.py
- GraphBuilderService
- mirofish-backend
- Konkrete Template-Textersetzungen:
- _check_simulation_prepared
- Mangel 3: Leere Flächen mit einzelnen Rauten-Symbolen
- Mangel 4: Karten der „Simulationsaufzeichnungen“ am Handy links/rechts abgeschnitten
- Mangel 2: Badge „Elegante universelle Schwarm-Intelligenz-Engine“ bricht um
- Mangel 5: Im Prompt-Feld überlappt Badge „Engine: MiroFish-V1.0“ den Platzhaltertext
- Mangel 10: Fehlende Zeitschätzung und Statusführung bei langen Läufen (Minuten bis 1 Stunde)
- sample-upload.md
- ROADMAP.md
- REPORT-UI.md
- setup_oasis_logging
- setup_oasis_logging
- I18N-Bericht
- simulation.js
- UX-REPORT-codex.md
- vue-i18n
- docker-entrypoint.sh

## God Nodes (most connected - your core abstractions)
1. `Config` - 63 edges
2. `error()` - 61 edges
3. `SimulationRunner` - 54 edges
4. `ReportManager` - 48 edges
5. `OasisProfileGenerator` - 34 edges
6. `ZepToolsService` - 34 edges
7. `ProjectManager` - 33 edges
8. `ObsidianMemoryProvider` - 33 edges
9. `SimulationManager` - 33 edges
10. `get_logger()` - 30 edges

## Surprising Connections (you probably didn't know these)
- `Projekt und Graph` --references--> `delete_project_cascade()`  [INFERRED]
  docs/CLEANUP.md → backend/app/services/cleanup.py
- `Simulation löschen` --references--> `delete_simulation_cascade()`  [INFERRED]
  docs/CLEANUP.md → backend/app/services/cleanup.py
- `Verwaiste Reste` --references--> `sweep_orphans()`  [INFERRED]
  docs/CLEANUP.md → backend/app/services/cleanup.py
- `Automatisch` --references--> `mark_stale_runs()`  [INFERRED]
  docs/CLEANUP.md → backend/app/api/pipeline.py
- `Übersicht` --references--> `_get_default_platform()`  [INFERRED]
  docs/UPSTREAM.md → backend/app/api/simulation.py

## Import Cycles
- None detected.

## Communities (109 total, 37 thin omitted)

### Community 0 - "Config"
Cohesion: 0.07
Nodes (10): allowed_file(), Config, MemoryFactory, get_logger(), create_chat_completion(), extract_chat_completion_text(), is_gpt5_family(), fetch_all_edges() (+2 more)

### Community 2 - "Step4Report.vue"
Cohesion: 0.03
Nodes (39): activeSectionIndex, activeStep, activeTocIndex, agentLogLine, agentLogs, collapsedSections, completedSections, consoleLogLine (+31 more)

### Community 3 - "SimulationManager"
Cohesion: 0.08
Nodes (7): chat_with_report_agent(), prepare_simulation(), run_prepare(), PlatformType, SimulationManager, SimulationState, SimulationStatus

### Community 4 - "Process.vue"
Cohesion: 0.06
Nodes (40): clearPendingUpload(), getPendingUpload(), state, buildProgress, closeDetailPanel(), currentPhase, currentProjectId, entityTypes (+32 more)

### Community 5 - "Step5Interaction.vue"
Cohesion: 0.05
Nodes (42): getReport(), getSimulationProfilesRealtime(), interviewAgents(), activeTab, addLog(), chatHistory, chatHistoryCache, chatInput (+34 more)

### Community 6 - "delete_simulation_cascade"
Cohesion: 0.15
Nodes (8): delete_simulation(), CleanupBusy, delete_simulation_cascade(), _runner_alive(), simulation_is_active(), _stop_runner(), info(), test_symlink_outside_upload_is_not_followed()

### Community 8 - "SimulationConfigGenerator"
Cohesion: 0.06
Nodes (7): AgentActivityConfig, EventConfig, PlatformConfig, SimulationConfigGenerator, SimulationParameters, TimeSimulationConfig, EntityNode

### Community 9 - "test_cleanup.py"
Cohesion: 0.29
Nodes (11): _dump(), make_project(), make_report(), make_run(), make_sim(), test_cascade_removes_only_the_finished_simulation(), test_delete_failed_pipelines_removes_failed_keeps_running_and_completed(), test_pipeline_cascade_removes_its_project() (+3 more)

### Community 10 - "system.py"
Cohesion: 0.10
Nodes (7): list_models(), mask_key(), _ollama_root(), save_config(), system_models(), system_status(), test_llm()

### Community 11 - "Step3Simulation.vue"
Cohesion: 0.07
Nodes (37): getRunStatus(), getRunStatusDetail(), startSimulation(), actionIds, addLog(), allActions, checkPlatformsCompleted(), chronologicalActions (+29 more)

### Community 12 - "mockApi.ts"
Cohesion: 0.06
Nodes (51): devDependencies, @axe-core/playwright, @playwright/test, typescript, name, private, scripts, test (+43 more)

### Community 13 - "Step2EnvSetup.vue"
Cohesion: 0.08
Nodes (43): Offene Frontend-Punkte (nicht angewendet, Umbau läuft parallel), Ausgelassen, Checks, Geändert, npm audit (`cd frontend && npm audit --omit=dev`), Offen, Polish-Report, getSimulationConfigRealtime() (+35 more)

### Community 14 - "MainView.vue"
Cohesion: 0.09
Nodes (37): getProject(), addLog(), buildProgress, currentPhase, currentProjectId, currentStep, error, fetchGraphData() (+29 more)

### Community 15 - "README-EN.md"
Cohesion: 0.05
Nodes (40): Der eine Aufruf, der alles macht, Einzelne Stufen (wenn du selbst steuern willst), Ergebnisse abholen, MiroFish API (für Skripte, Agenten und eigene Oberflächen), Python-Beispiel, 1. Ollama und Modelle, 2a. Start mit Docker (empfohlen), 2b. Start aus dem Quellcode (+32 more)

### Community 16 - "SimulationRunView.vue"
Cohesion: 0.08
Nodes (31): closeSimulationEnv(), getSimulation(), getSimulationConfig(), addLog(), currentSimulationId, currentStatus, graphData, graphLoading (+23 more)

### Community 18 - "run_reddit_simulation"
Cohesion: 0.08
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

### Community 22 - "ReportManager"
Cohesion: 0.05
Nodes (17): check_report_status(), delete_report(), download_report(), generate_report(), get_agent_log(), get_console_log(), get_generate_status(), get_report() (+9 more)

### Community 23 - "SimulationView.vue"
Cohesion: 0.09
Nodes (27): getEnvStatus(), stopSimulation(), addLog(), checkAndStopRunningSimulation(), currentSimulationId, currentStatus, forceStopSimulation(), graphData (+19 more)

### Community 24 - "run_reddit_simulation.py"
Cohesion: 0.09
Nodes (6): CommandType, MaxTokensWarningFilter, setup_signal_handlers(), CommandType, MaxTokensWarningFilter, setup_signal_handlers()

### Community 25 - ".generate_report"
Cohesion: 0.10
Nodes (4): run_generate(), Report, ReportOutline, ReportSection

### Community 26 - "os"
Cohesion: 0.15
Nodes (14): _base(), delete_pipeline(), _dir(), _load(), mark_stale_runs(), _ok(), _path(), pipeline_list() (+6 more)

### Community 27 - "HistoryDatabase.vue"
Cohesion: 0.07
Nodes (18): getSimulationHistory(), closeModal(), confirmDelete(), containerStyle, goToProject(), goToReport(), goToSimulation(), historyContainer (+10 more)

### Community 28 - "simulation.py"
Cohesion: 0.05
Nodes (34): close_simulation_env(), create_simulation(), download_simulation_config(), download_simulation_script(), export_simulation(), generate_profiles(), get_agent_stats(), _get_default_platform() (+26 more)

### Community 29 - "Home.vue"
Cohesion: 0.09
Nodes (22): startPipeline(), activeRuns, add(), autopilot, canSubmit, error, fileInput, files (+14 more)

### Community 30 - "ReportView.vue"
Cohesion: 0.09
Nodes (21): addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph(), loadReportData() (+13 more)

### Community 31 - "route"
Cohesion: 0.29
Nodes (3): get_project(), get_task(), list_tasks()

### Community 32 - "3. Detaillierte Spezifikation nach Seiten und Komponenten"
Cohesion: 0.06
Nodes (33): 1. Barrierefreiheit (e2e-Befund), 1. Gemeinsame Header-Architektur am Smartphone, 1. Kurzurteil, 1. Mobil-Verhalten, 1. Mobil-Verhalten (`04-durchlauf-mobil.png`), 1. Mobil-Verhalten (Samsung S23 Ultra, 412 px), 1. Problemstellung & IST-Zustand (Screenshots 10 & 11), 2. Befundtabelle (+25 more)

### Community 33 - "GraphPanel.vue"
Cohesion: 0.05
Nodes (42): dependencies, axios, d3, vue, vue-i18n, vue-router, devDependencies, vite (+34 more)

### Community 34 - "InteractionView.vue"
Cohesion: 0.09
Nodes (21): addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph(), loadReportData() (+13 more)

### Community 38 - "ParallelIPCHandler"
Cohesion: 0.14
Nodes (3): load_config(), main(), ParallelIPCHandler

### Community 40 - "getGraphData"
Cohesion: 0.35
Nodes (8): buildGraph(), generateOntology(), getGraphData(), getTaskStatus(), requestWithRetry(), service, chatWithReport(), generateReport()

### Community 41 - "package.json"
Cohesion: 0.11
Nodes (17): description, devDependencies, concurrently, engines, node, license, name, scripts (+9 more)

### Community 42 - "app/__init__.py"
Cohesion: 0.11
Nodes (8): create_app(), log_request(), log_response(), require_api_token(), token_ok(), _ensure_utf8_stdout(), setup_logger(), main()

### Community 43 - "SettingsView.vue"
Cohesion: 0.11
Nodes (16): baseUrl(), cfg, load(), masked, memoryLabel, models, result, save() (+8 more)

### Community 45 - "Any"
Cohesion: 0.06
Nodes (5): AgentInterview, EdgeInfo, InsightForgeResult, InterviewResult, PanoramaResult

### Community 46 - "retry_with_backoff_async"
Cohesion: 0.15
Nodes (6): retry_with_backoff(), retry_with_backoff_async(), decorator(), decorator(), wrapper(), RetryableAPIClient

### Community 48 - "ontology_generator.py"
Cohesion: 0.05
Nodes (13): _coerce_to_str(), _coerce_to_str_list(), _ascii_fold(), OntologyGenerator, resolve_entity_name(), _to_pascal_case(), _to_upper_snake_case(), LLMResponseError (+5 more)

### Community 49 - ".get_project"
Cohesion: 0.16
Nodes (3): reset_project(), Project, ProjectStatus

### Community 51 - "ObsidianMemoryProvider"
Cohesion: 0.05
Nodes (6): MemoryEdge, MemoryNode, MemorySearchResult, HybridMemoryProvider, ObsidianMemoryProvider, ZepMemoryProvider

### Community 56 - "ZepToolsService"
Cohesion: 0.06
Nodes (7): get_graph_statistics_tool(), search_graph_tool(), ReportAgent, NodeInfo, SearchResult, ZepToolsService, LLMClient

### Community 57 - "MiroFish E2E (Playwright)"
Cohesion: 0.14
Nodes (12): frontend(), 1. Fußmenü verdeckt Bedienelemente (Handy), 2. Barrierefreiheit (axe serious/critical), Bekannte Befunde (E2E), Nicht als App-Bug gewertet (Tests angepasst), Bekannte App-Fehler, CI, Live gegen eine laufende Instanz (+4 more)

### Community 58 - "cleanup.py"
Cohesion: 0.15
Nodes (21): _child(), _delete_graph_storage(), _delete_pipelines_for_simulation(), delete_project_cascade(), _delete_reports_for(), _inside(), _iter_pipelines(), _maybe_delete_project() (+13 more)

### Community 60 - "services/__init__.py"
Cohesion: 0.09
Nodes (7): TaskStatus, CommandStatus, CommandType, RoundSummary, RunnerStatus, ZepGraphMemoryManager, _contains_additional_json_container()

### Community 61 - "delete_pipeline_cascade"
Cohesion: 0.20
Nodes (9): delete_failed_pipelines(), delete_pipeline_cascade(), Aufräumen, Automatisch, Durchlauf löschen, Projekt und Graph, Simulation löschen, Verlauf (+1 more)

### Community 63 - "ThemePicker.vue"
Cohesion: 0.11
Nodes (34): busy, choose(), chooseOwn(), current, error, input, isDefault, ownColor (+26 more)

### Community 65 - "Design-System: MiroFish „Editorial Clarity“"
Cohesion: 0.08
Nodes (24): 1. Design-Richtung & Philosophie, 2. Typografie, 3.1 Helles Design (Light Mode - Standard), 3.2 Dunkles Design (Dark Mode - `[data-theme="dark"]`), 3. Farbpalette & Nachgerechnete WCAG-AA-Kontraste, 4. Abstands- und Rastersystem, 5.1 Buttons (Schaltflächen), 5.2 Karten (Cards) (+16 more)

### Community 67 - "build_graph"
Cohesion: 0.17
Nodes (4): build_graph(), build_task(), Task, debug()

### Community 70 - "Änderungen"
Cohesion: 0.29
Nodes (6): Abnahme, `GraphPanel.vue`, i18n (`de.json` / `en.json`), `Step1GraphBuild.vue`, UX-Report: Wissensgraph & Schritt 1 (Feinschliff), Änderungen

### Community 71 - "getAgentLog"
Cohesion: 0.25
Nodes (8): getAgentLog(), getConsoleLog(), addLog(), emit, fetchAgentLog(), fetchConsoleLog(), startPolling(), stopPolling()

### Community 73 - "UX-REPORT – Cursor Live (Audit-2 Nacharbeit)"
Cohesion: 0.33
Nodes (5): Abnahme, E2E, Handy: Seiten-Scroll statt Innen-Scroll (Schritt-Seiten), Texte, UX-REPORT – Cursor Live (Audit-2 Nacharbeit)

### Community 74 - "compilerOptions"
Cohesion: 0.17
Nodes (11): compilerOptions, esModuleInterop, module, moduleResolution, noEmit, resolveJsonModule, skipLibCheck, strict (+3 more)

### Community 75 - "RunView.vue"
Cohesion: 0.05
Nodes (45): deletePipeline(), getPipeline(), listPipelines(), STEP_LABELS, STEP_ORDER, deleteSimulation(), route, showTheme (+37 more)

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

### Community 94 - "run_parallel_simulation.py"
Cohesion: 0.08
Nodes (11): CommandType, disable_oasis_logging(), _enrich_action_context(), fetch_new_actions_from_db(), _get_comment_info(), _get_post_info(), _get_user_name(), init_logging_for_simulation() (+3 more)

### Community 95 - "GraphBuilderService"
Cohesion: 0.08
Nodes (6): delete_graph(), get_graph_data(), GraphBuilderService, GraphInfo, TextProcessor, split_text_into_chunks()

### Community 98 - "Konkrete Template-Textersetzungen:"
Cohesion: 0.50
Nodes (4): 1. In `Home.vue`:, 2. In `Step1GraphBuild.vue`:, Konkrete Template-Textersetzungen:, Mangel 7: Fachjargon in Nutzertexten

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

### Community 115 - "simulation.js"
Cohesion: 0.10
Nodes (10): createSimulation(), getPrepareStatus(), creatingSimulation, graphStats, handleEnterEnvSetup(), logContent, props, router (+2 more)

### Community 128 - "vue-i18n"
Cohesion: 0.20
Nodes (4): { t }, { locale, t }, savedLanguage, vue-i18n

## Knowledge Gaps
- **526 isolated node(s):** `mirofish-backend`, `docker-entrypoint.sh script`, `name`, `private`, `version` (+521 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1325 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **37 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Neuerungen aus dem Original (666ghj/MiroFish)` connect `ontology_generator.py` to `Step2EnvSetup.vue`, `.chat`?**
  _High betweenness centrality (0.301) - this node is a cross-community bridge._
- **Are the 33 inferred relationships involving `Config` (e.g. with `allowed_file()` and `build_graph()`) actually correct?**
  _`Config` has 33 INFERRED edges - model-reasoned connections that need verification._
- **What connects `mirofish-backend`, `docker-entrypoint.sh script`, `name` to the rest of the system?**
  _526 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Config` be split into smaller, more focused modules?**
  _Cohesion score 0.0656010656010656 - nodes in this community are weakly interconnected._
- **Why does `Offene Frontend-Punkte (nicht angewendet, Umbau läuft parallel)` connect `Step2EnvSetup.vue` to `ontology_generator.py`, `Step3Simulation.vue`?**
  _High betweenness centrality (0.301) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `error()` (e.g. with `generate_ontology()` and `.chat_json()`) actually correct?**
  _`error()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `Step4Report.vue` be split into smaller, more focused modules?**
  _Cohesion score 0.030303030303030304 - nodes in this community are weakly interconnected._