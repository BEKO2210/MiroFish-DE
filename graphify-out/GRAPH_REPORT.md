# Graph Report - MiroFish-DE  (2026-10-13)

## Corpus Check
- 131 files · ~546,350 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: (none) 6, .example 1, .lock 1)

## Summary
- 2534 nodes · 5030 edges · 121 communities (83 shown, 38 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 368 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `161b8593`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- graph_builder.py
- interview_agent
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
- run_parallel_simulation.py
- .generate_report
- pipeline.py
- HistoryDatabase.vue
- SimulationRunner
- Home.vue
- ReportView.vue
- HistoryView.vue
- 3. Detaillierte Spezifikation nach Seiten und Komponenten
- GraphPanel.vue
- InteractionView.vue
- AgentActivity
- ParallelIPCHandler
- SimulationLogManager
- graph.js
- package.json
- vue-router
- SettingsView.vue
- ZepEntityReader
- ZepToolsService
- retry.py
- OasisAgentProfile
- ontology_generator.py
- Übersicht
- ZepGraphMemoryUpdater
- ObsidianMemoryProvider
- ReportConsoleLogger
- action_logger.py
- LLMClient
- ReportAgent
- error
- MiroFish E2E (Playwright)
- cleanup.py
- OasisProfileGenerator
- Config
- delete_pipeline_cascade
- ThemePicker.vue
- frontend/package.json
- Design-System: MiroFish „Editorial Clarity“
- ReportOutline
- build_graph
- graph.py
- Änderungen
- getAgentLog
- UX-Report: Graph-Höhe mobil (Seiten-Scroll-Regression)
- UX-REPORT – Cursor Live (Audit-2 Nacharbeit)
- compilerOptions
- RunView.vue
- simulation.js
- vue
- Polish-Report
- Konkrete Mobile- & Template-Fixes (Mobile First 412 px)
- SwarmCanvas.vue
- Design-Audit: MiroFish Web-App (Mobile First & Barrierefreiheit)
- 3. Umfassender Ansichten-Audit (View-by-View Breakdown)
- 2. Bestätigung und Tiefenanalyse der bekannten Kernmängel
- dependencies
- init_logging_for_simulation
- UX-REPORT – belkis (Abschnitt 3.1A, 3.3–3.6, global)
- scripts
- build_task
- conftest.py
- test_profile_format.py
- _enrich_action_context
- GraphBuilderService
- MaxTokensWarningFilter
- mirofish-backend
- Konkrete Template-Textersetzungen:
- simulation.py
- Mangel 3: Leere Flächen mit einzelnen Rauten-Symbolen
- Mangel 4: Karten der „Simulationsaufzeichnungen“ am Handy links/rechts abgeschnitten
- Mangel 2: Badge „Elegante universelle Schwarm-Intelligenz-Engine“ bricht um
- Mangel 5: Im Prompt-Feld überlappt Badge „Engine: MiroFish-V1.0“ den Platzhaltertext
- Mangel 10: Fehlende Zeitschätzung und Statusführung bei langen Läufen (Minuten bis 1 Stunde)
- setup_signal_handlers
- MaxTokensWarningFilter
- sample-upload.md
- Roadmap v2 – „so gut, dass es jeder gern benutzt"
- REPORT-UI.md
- setup_oasis_logging
- setup_oasis_logging
- I18N-Bericht
- Step1GraphBuild.vue
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

## Communities (121 total, 38 thin omitted)

### Community 0 - "graph_builder.py"
Cohesion: 0.08
Nodes (5): MemoryProvider, MemoryFactory, fetch_all_edges(), fetch_all_nodes(), _fetch_page_with_retry()

### Community 1 - "interview_agent"
Cohesion: 0.11
Nodes (5): get_env_status(), interview_agent(), interview_agents_batch(), interview_all_agents(), optimize_interview_prompt()

### Community 2 - "Step4Report.vue"
Cohesion: 0.03
Nodes (39): activeSectionIndex, activeStep, activeTocIndex, agentLogLine, agentLogs, collapsedSections, completedSections, consoleLogLine (+31 more)

### Community 3 - "SimulationManager"
Cohesion: 0.07
Nodes (8): close_simulation_env(), get_simulation(), get_simulation_history(), stop_simulation(), PlatformType, SimulationManager, SimulationState, SimulationStatus

### Community 4 - "Process.vue"
Cohesion: 0.07
Nodes (39): getProject(), getPendingUpload(), buildProgress, closeDetailPanel(), currentPhase, currentProjectId, entityTypes, error (+31 more)

### Community 5 - "Step5Interaction.vue"
Cohesion: 0.05
Nodes (41): getSimulationProfilesRealtime(), interviewAgents(), activeTab, addLog(), chatHistory, chatHistoryCache, chatInput, chatInputRef (+33 more)

### Community 6 - "delete_simulation_cascade"
Cohesion: 0.12
Nodes (10): delete_simulation(), CleanupBusy, CleanupError, delete_simulation_cascade(), _require(), _runner_alive(), simulation_is_active(), _stop_runner() (+2 more)

### Community 7 - "ProjectManager"
Cohesion: 0.08
Nodes (7): delete_project(), generate_ontology(), get_project(), list_projects(), reset_project(), Project, ProjectManager

### Community 8 - "SimulationConfigGenerator"
Cohesion: 0.07
Nodes (5): AgentActivityConfig, EventConfig, SimulationConfigGenerator, SimulationParameters, EntityNode

### Community 9 - "test_cleanup.py"
Cohesion: 0.29
Nodes (11): _dump(), make_project(), make_report(), make_run(), make_sim(), test_cascade_removes_only_the_finished_simulation(), test_delete_failed_pipelines_removes_failed_keeps_running_and_completed(), test_pipeline_cascade_removes_its_project() (+3 more)

### Community 10 - "system.py"
Cohesion: 0.10
Nodes (6): list_models(), mask_key(), _ollama_root(), save_config(), system_models(), system_status()

### Community 11 - "Step3Simulation.vue"
Cohesion: 0.07
Nodes (38): getRunStatus(), getRunStatusDetail(), startSimulation(), stopSimulation(), actionIds, addLog(), allActions, checkPlatformsCompleted() (+30 more)

### Community 12 - "mockApi.ts"
Cohesion: 0.06
Nodes (51): devDependencies, @axe-core/playwright, @playwright/test, typescript, name, private, scripts, test (+43 more)

### Community 13 - "Step2EnvSetup.vue"
Cohesion: 0.10
Nodes (37): Offene Frontend-Punkte (nicht angewendet, Umbau läuft parallel), getSimulationConfigRealtime(), prepareSimulation(), addLog(), autoGeneratedRounds, currentStage, customMaxRounds, displayProfiles (+29 more)

### Community 14 - "MainView.vue"
Cohesion: 0.09
Nodes (38): getGraphData(), clearPendingUpload(), addLog(), buildProgress, currentPhase, currentProjectId, currentStep, error (+30 more)

### Community 15 - "README-EN.md"
Cohesion: 0.05
Nodes (40): Der eine Aufruf, der alles macht, Einzelne Stufen (wenn du selbst steuern willst), Ergebnisse abholen, MiroFish API (für Skripte, Agenten und eigene Oberflächen), Python-Beispiel, 1. Ollama und Modelle, 2a. Start mit Docker (empfohlen), 2b. Start aus dem Quellcode (+32 more)

### Community 16 - "SimulationRunView.vue"
Cohesion: 0.08
Nodes (31): closeSimulationEnv(), getEnvStatus(), getSimulationConfig(), addLog(), currentSimulationId, currentStatus, graphData, graphLoading (+23 more)

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
Cohesion: 0.09
Nodes (4): IPCCommand, IPCResponse, SimulationIPCClient, SimulationIPCServer

### Community 22 - "ReportManager"
Cohesion: 0.10
Nodes (5): download_report(), get_generate_status(), get_report_sections(), ReportManager, ReportStatus

### Community 23 - "SimulationView.vue"
Cohesion: 0.10
Nodes (26): getSimulation(), addLog(), checkAndStopRunningSimulation(), currentSimulationId, currentStatus, forceStopSimulation(), graphData, graphLoading (+18 more)

### Community 24 - "run_parallel_simulation.py"
Cohesion: 0.08
Nodes (7): CommandType, _utf8_open(), CommandType, MaxTokensWarningFilter, setup_signal_handlers(), CommandType, setup_signal_handlers()

### Community 26 - "pipeline.py"
Cohesion: 0.16
Nodes (13): _base(), delete_pipeline(), _dir(), _load(), mark_stale_runs(), _ok(), _path(), pipeline_list() (+5 more)

### Community 27 - "HistoryDatabase.vue"
Cohesion: 0.08
Nodes (14): closeModal(), containerStyle, goToProject(), goToReport(), goToSimulation(), historyContainer, hoveringCard, isExpanded (+6 more)

### Community 28 - "SimulationRunner"
Cohesion: 0.06
Nodes (8): get_interview_history(), get_run_status(), get_run_status_detail(), start_simulation(), AgentAction, SimulationRunner, cleanup_handler(), SimulationRunState

### Community 29 - "Home.vue"
Cohesion: 0.09
Nodes (22): startPipeline(), activeRuns, add(), autopilot, canSubmit, error, fileInput, files (+14 more)

### Community 30 - "ReportView.vue"
Cohesion: 0.08
Nodes (22): { locale, t }, addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph() (+14 more)

### Community 31 - "HistoryView.vue"
Cohesion: 0.15
Nodes (17): deletePipeline(), deleteSimulation(), getSimulationHistory(), confirmDelete(), loadHistory(), deleting, doDelete(), error (+9 more)

### Community 32 - "3. Detaillierte Spezifikation nach Seiten und Komponenten"
Cohesion: 0.06
Nodes (33): 1. Barrierefreiheit (e2e-Befund), 1. Gemeinsame Header-Architektur am Smartphone, 1. Kurzurteil, 1. Mobil-Verhalten, 1. Mobil-Verhalten (`04-durchlauf-mobil.png`), 1. Mobil-Verhalten (Samsung S23 Ultra, 412 px), 1. Problemstellung & IST-Zustand (Screenshots 10 & 11), 2. Befundtabelle (+25 more)

### Community 33 - "GraphPanel.vue"
Cohesion: 0.10
Nodes (20): closeDetailPanel(), emit, entityTypes, expandedSelfLoops, graphContainer, graphSvg, handleResize(), nodeCountRef (+12 more)

### Community 34 - "InteractionView.vue"
Cohesion: 0.09
Nodes (22): getReport(), addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph() (+14 more)

### Community 39 - "SimulationLogManager"
Cohesion: 0.13
Nodes (3): SimulationLogManager, load_config(), main()

### Community 40 - "graph.js"
Cohesion: 0.38
Nodes (7): buildGraph(), generateOntology(), getTaskStatus(), requestWithRetry(), service, chatWithReport(), generateReport()

### Community 41 - "package.json"
Cohesion: 0.11
Nodes (17): description, devDependencies, concurrently, engines, node, license, name, scripts (+9 more)

### Community 42 - "vue-router"
Cohesion: 0.16
Nodes (10): listPipelines(), activeCount, poll(), route, { t }, app, router, routes (+2 more)

### Community 43 - "SettingsView.vue"
Cohesion: 0.11
Nodes (16): baseUrl(), cfg, load(), masked, memoryLabel, models, result, save() (+8 more)

### Community 44 - "ZepEntityReader"
Cohesion: 0.11
Nodes (5): generate_profiles(), get_entities_by_type(), get_entity_detail(), get_graph_entities(), ZepEntityReader

### Community 45 - "ZepToolsService"
Cohesion: 0.04
Nodes (8): AgentInterview, EdgeInfo, InsightForgeResult, InterviewResult, NodeInfo, PanoramaResult, SearchResult, ZepToolsService

### Community 46 - "retry.py"
Cohesion: 0.12
Nodes (6): retry_with_backoff(), retry_with_backoff_async(), decorator(), decorator(), wrapper(), RetryableAPIClient

### Community 48 - "ontology_generator.py"
Cohesion: 0.08
Nodes (8): _ascii_fold(), OntologyGenerator, resolve_entity_name(), _to_pascal_case(), _to_upper_snake_case(), normalize_ontology_attribute(), normalize_ontology_attributes(), normalize_ontology_source_targets()

### Community 49 - "Übersicht"
Cohesion: 0.19
Nodes (6): _coerce_to_str(), _coerce_to_str_list(), LLMResponseError, Neuerungen aus dem Original (666ghj/MiroFish), Prüfung, Übersicht

### Community 51 - "ObsidianMemoryProvider"
Cohesion: 0.04
Nodes (6): MemoryEdge, MemoryNode, MemorySearchResult, HybridMemoryProvider, ObsidianMemoryProvider, ZepMemoryProvider

### Community 54 - "LLMClient"
Cohesion: 0.08
Nodes (7): test_llm(), _clean_chat_text(), _is_response_format_unsupported(), LLMClient, create_chat_completion(), extract_chat_completion_text(), is_gpt5_family()

### Community 56 - "error"
Cohesion: 0.11
Nodes (18): chat_with_report_agent(), check_report_status(), delete_report(), get_agent_log(), get_console_log(), get_graph_statistics_tool(), get_report(), get_report_by_simulation() (+10 more)

### Community 57 - "MiroFish E2E (Playwright)"
Cohesion: 0.14
Nodes (12): frontend(), 1. Fußmenü verdeckt Bedienelemente (Handy), 2. Barrierefreiheit (axe serious/critical), Bekannte Befunde (E2E), Nicht als App-Bug gewertet (Tests angepasst), Bekannte App-Fehler, CI, Live gegen eine laufende Instanz (+4 more)

### Community 58 - "cleanup.py"
Cohesion: 0.16
Nodes (20): _child(), _delete_graph_storage(), _delete_pipelines_for_simulation(), delete_project_cascade(), _delete_reports_for(), _inside(), _iter_pipelines(), _maybe_delete_project() (+12 more)

### Community 60 - "Config"
Cohesion: 0.06
Nodes (19): Config, create_app(), log_request(), log_response(), require_api_token(), token_ok(), PlatformConfig, TimeSimulationConfig (+11 more)

### Community 61 - "delete_pipeline_cascade"
Cohesion: 0.20
Nodes (9): delete_failed_pipelines(), delete_pipeline_cascade(), Aufräumen, Automatisch, Durchlauf löschen, Projekt und Graph, Simulation löschen, Verlauf (+1 more)

### Community 63 - "ThemePicker.vue"
Cohesion: 0.11
Nodes (34): busy, choose(), chooseOwn(), current, error, input, isDefault, ownColor (+26 more)

### Community 64 - "frontend/package.json"
Cohesion: 0.17
Nodes (11): devDependencies, vite, @vitejs/plugin-vue, name, private, type, version, axios (+3 more)

### Community 65 - "Design-System: MiroFish „Editorial Clarity“"
Cohesion: 0.08
Nodes (24): 1. Design-Richtung & Philosophie, 2. Typografie, 3.1 Helles Design (Light Mode - Standard), 3.2 Dunkles Design (Dark Mode - `[data-theme="dark"]`), 3. Farbpalette & Nachgerechnete WCAG-AA-Kontraste, 4. Abstands- und Rastersystem, 5.1 Buttons (Schaltflächen), 5.2 Karten (Cards) (+16 more)

### Community 67 - "build_graph"
Cohesion: 0.11
Nodes (6): build_graph(), generate_report(), ProjectStatus, Task, TaskStatus, debug()

### Community 68 - "graph.py"
Cohesion: 0.08
Nodes (7): allowed_file(), get_task(), list_tasks(), TextProcessor, FileParser, _read_text_with_fallback(), split_text_into_chunks()

### Community 70 - "Änderungen"
Cohesion: 0.29
Nodes (6): Abnahme, `GraphPanel.vue`, i18n (`de.json` / `en.json`), `Step1GraphBuild.vue`, UX-Report: Wissensgraph & Schritt 1 (Feinschliff), Änderungen

### Community 71 - "getAgentLog"
Cohesion: 0.25
Nodes (8): getAgentLog(), getConsoleLog(), addLog(), emit, fetchAgentLog(), fetchConsoleLog(), startPolling(), stopPolling()

### Community 72 - "UX-Report: Graph-Höhe mobil (Seiten-Scroll-Regression)"
Cohesion: 0.20
Nodes (9): zoomToFit(), Abnahme, E2E, Gegenprobe, `GraphPanel.vue`, Problem, Schritt-Views (`MainView`, `SimulationView`, `SimulationRunView`, `ReportView`, `InteractionView`), UX-Report: Graph-Höhe mobil (Seiten-Scroll-Regression) (+1 more)

### Community 73 - "UX-REPORT – Cursor Live (Audit-2 Nacharbeit)"
Cohesion: 0.33
Nodes (5): Abnahme, E2E, Handy: Seiten-Scroll statt Innen-Scroll (Schritt-Seiten), Texte, UX-REPORT – Cursor Live (Audit-2 Nacharbeit)

### Community 74 - "compilerOptions"
Cohesion: 0.17
Nodes (11): compilerOptions, esModuleInterop, module, moduleResolution, noEmit, resolveJsonModule, skipLibCheck, strict (+3 more)

### Community 75 - "RunView.vue"
Cohesion: 0.10
Nodes (18): getPipeline(), STEP_LABELS, STEP_ORDER, cleanedUp, currentDetail, currentLabel, etaText, HINTS (+10 more)

### Community 77 - "vue"
Cohesion: 0.25
Nodes (5): route, showTheme, { t }, state, vue

### Community 78 - "Polish-Report"
Cohesion: 0.29
Nodes (6): Ausgelassen, Checks, Geändert, npm audit (`cd frontend && npm audit --omit=dev`), Offen, Polish-Report

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

### Community 86 - "dependencies"
Cohesion: 0.33
Nodes (6): dependencies, axios, d3, vue, vue-i18n, vue-router

### Community 89 - "UX-REPORT – belkis (Abschnitt 3.1A, 3.3–3.6, global)"
Cohesion: 0.40
Nodes (4): Abnahme, Nicht angefasst, UX-REPORT – belkis (Abschnitt 3.1A, 3.3–3.6, global), Änderungen

### Community 90 - "scripts"
Cohesion: 0.50
Nodes (4): scripts, build, dev, preview

### Community 94 - "_enrich_action_context"
Cohesion: 0.20
Nodes (5): _enrich_action_context(), fetch_new_actions_from_db(), _get_comment_info(), _get_post_info(), _get_user_name()

### Community 95 - "GraphBuilderService"
Cohesion: 0.07
Nodes (5): delete_graph(), get_graph_data(), TaskManager, GraphBuilderService, GraphInfo

### Community 98 - "Konkrete Template-Textersetzungen:"
Cohesion: 0.50
Nodes (4): 1. In `Home.vue`:, 2. In `Step1GraphBuild.vue`:, Konkrete Template-Textersetzungen:, Mangel 7: Fachjargon in Nutzertexten

### Community 99 - "simulation.py"
Cohesion: 0.08
Nodes (18): _check_simulation_prepared(), create_simulation(), download_simulation_config(), export_simulation(), get_agent_stats(), _get_default_platform(), get_prepare_status(), _get_report_id_for_simulation() (+10 more)

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

### Community 115 - "Step1GraphBuild.vue"
Cohesion: 0.17
Nodes (9): createSimulation(), creatingSimulation, graphStats, handleEnterEnvSetup(), logContent, props, router, selectedOntologyItem (+1 more)

### Community 128 - "vue-i18n"
Cohesion: 0.29
Nodes (3): { t }, savedLanguage, vue-i18n

## Knowledge Gaps
- **531 isolated node(s):** `mirofish-backend`, `docker-entrypoint.sh script`, `name`, `private`, `version` (+526 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1331 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **38 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Neuerungen aus dem Original (666ghj/MiroFish)` connect `Übersicht` to `Step2EnvSetup.vue`?**
  _High betweenness centrality (0.300) - this node is a cross-community bridge._
- **Are the 33 inferred relationships involving `Config` (e.g. with `allowed_file()` and `build_graph()`) actually correct?**
  _`Config` has 33 INFERRED edges - model-reasoned connections that need verification._
- **What connects `mirofish-backend`, `docker-entrypoint.sh script`, `name` to the rest of the system?**
  _531 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `graph_builder.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07676767676767676 - nodes in this community are weakly interconnected._
- **Why does `Offene Frontend-Punkte (nicht angewendet, Umbau läuft parallel)` connect `Step2EnvSetup.vue` to `Übersicht`, `Step3Simulation.vue`?**
  _High betweenness centrality (0.300) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `error()` (e.g. with `generate_ontology()` and `.chat_json()`) actually correct?**
  _`error()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `interview_agent` be split into smaller, more focused modules?**
  _Cohesion score 0.11255411255411256 - nodes in this community are weakly interconnected._