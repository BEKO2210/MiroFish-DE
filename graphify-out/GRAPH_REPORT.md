# Graph Report - MiroFish-DE  (2026-10-13)

## Corpus Check
- 141 files · ~659,564 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: (none) 6, .example 1, .lock 1)

## Summary
- 2788 nodes · 5446 edges · 143 communities (83 shown, 60 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 374 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `97b09189`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- MemoryProvider
- interview_agent
- Step4Report.vue
- SimulationManager
- Process.vue
- Step5Interaction.vue
- simulation.py
- graph.py
- SimulationConfigGenerator
- pipeline.py
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
- SimulationView.vue
- run_reddit_simulation.py
- .generate_report
- simulation_runner.py
- HistoryDatabase.vue
- SimulationRunner
- Home.vue
- ReportView.vue
- AgentAction
- 3. Detaillierte Spezifikation nach Seiten und Komponenten
- GraphPanel.vue
- InteractionView.vue
- ZepMemoryProvider
- OasisProfileGenerator
- AgentActivity
- ParallelIPCHandler
- SimulationLogManager
- getGraphData
- package.json
- HistoryView.vue
- SettingsView.vue
- ZepEntityReader
- ZepToolsService
- retry_with_backoff_async
- OasisAgentProfile
- OntologyGenerator
- Übersicht
- ZepGraphMemoryUpdater
- ObsidianMemoryProvider
- ReportConsoleLogger
- ActionLogger
- LLMClient
- ReportAgent
- error
- MiroFish E2E (Playwright)
- cleanup.py
- vue-i18n
- os
- RedditSimulationRunner
- ThemePicker.vue
- frontend/package.json
- Design-System: MiroFish „Editorial Clarity“
- TwitterSimulationRunner
- TaskManager
- TextProcessor
- Änderungen
- fetchAgentLog
- UX-Report: Graph-Höhe mobil (Seiten-Scroll-Regression)
- UX-REPORT – Cursor Live (Audit-2 Nacharbeit)
- compilerOptions
- RunView.vue
- simulation.js
- Any
- Polish-Report
- Konkrete Mobile- & Template-Fixes (Mobile First 412 px)
- EntityNode
- SwarmCanvas.vue
- Design-Audit: MiroFish Web-App (Mobile First & Barrierefreiheit)
- 3. Umfassender Ansichten-Audit (View-by-View Breakdown)
- 2. Bestätigung und Tiefenanalyse der bekannten Kernmängel
- SimulationRunState
- test_cleanup.py
- UX-REPORT – belkis (Abschnitt 3.1A, 3.3–3.6, global)
- delete_pipeline_cascade
- SimulationIPCServer
- report_validation.py
- test_profile_format.py
- delete_simulation_cascade
- GraphBuilderService
- run_parallel_simulation.py
- mirofish-backend
- Konkrete Template-Textersetzungen:
- logger.py
- Mangel 3: Leere Flächen mit einzelnen Rauten-Symbolen
- Mangel 4: Karten der „Simulationsaufzeichnungen“ am Handy links/rechts abgeschnitten
- Mangel 2: Badge „Elegante universelle Schwarm-Intelligenz-Engine“ bricht um
- Mangel 5: Im Prompt-Feld überlappt Badge „Engine: MiroFish-V1.0“ den Platzhaltertext
- Mangel 10: Fehlende Zeitschätzung und Statusführung bei langen Läufen (Minuten bis 1 Stunde)
- MemoryNode
- zep_provider.py
- sample-upload.md
- Roadmap v2 – „so gut, dass es jeder gern benutzt"
- REPORT-UI.md
- ontology_generator.py
- .assemble_full_report
- I18N-Bericht
- Step1GraphBuild.vue
- MemoryEdge
- graph_builder.py
- _runner_alive
- UX-REPORT-codex.md
- MemorySearchResult
- UX-REPORT – Cursor Validierung (V1)
- Any
- Zukunftsprognosebericht: Dynamik der Parkgebührenanpassung und die Eskalationspfade zum Bürgerentscheid
- Ausgangslage: Hallenbad Süd in Neuberg
- conftest.py
- setup_signal_handlers
- setup_signal_handlers
- InsightForgeResult
- InterviewResult
- PanoramaResult
- szenarien/README.md
- docker-test.sh
- Validierung V1/V2
- _get_report_id_for_simulation
- build_task
- docker-entrypoint.sh
- busy-check.sh

## God Nodes (most connected - your core abstractions)
1. `Config` - 70 edges
2. `error()` - 61 edges
3. `SimulationRunner` - 55 edges
4. `ReportManager` - 49 edges
5. `OasisProfileGenerator` - 34 edges
6. `ZepToolsService` - 34 edges
7. `ProjectManager` - 33 edges
8. `ObsidianMemoryProvider` - 33 edges
9. `SimulationManager` - 33 edges
10. `get_logger()` - 31 edges

## Surprising Connections (you probably didn't know these)
- `Projekt und Graph` --references--> `delete_project_cascade()`  [INFERRED]
  docs/CLEANUP.md → backend/app/services/cleanup.py
- `Simulation löschen` --references--> `delete_simulation_cascade()`  [INFERRED]
  docs/CLEANUP.md → backend/app/services/cleanup.py
- `Verwaiste Reste` --references--> `sweep_orphans()`  [INFERRED]
  docs/CLEANUP.md → backend/app/services/cleanup.py
- `Was V2 leistet` --references--> `random()`  [INFERRED]
  docs/VALIDIERUNG.md → frontend/src/components/ThemePicker.vue
- `Übersicht` --references--> `_get_default_platform()`  [INFERRED]
  docs/UPSTREAM.md → backend/app/api/simulation.py

## Import Cycles
- None detected.

## Communities (143 total, 60 thin omitted)

### Community 1 - "interview_agent"
Cohesion: 0.10
Nodes (5): get_env_status(), interview_agent(), interview_agents_batch(), interview_all_agents(), optimize_interview_prompt()

### Community 2 - "Step4Report.vue"
Cohesion: 0.03
Nodes (42): activeSectionIndex, activeStep, activeTocIndex, agentLogLine, agentLogs, agentTypesLabel, collapsedSections, completedSections (+34 more)

### Community 3 - "SimulationManager"
Cohesion: 0.06
Nodes (8): close_simulation_env(), get_simulation(), get_simulation_history(), start_simulation(), stop_simulation(), SimulationManager, SimulationState, SimulationStatus

### Community 4 - "Process.vue"
Cohesion: 0.07
Nodes (40): getProject(), clearPendingUpload(), getPendingUpload(), buildProgress, closeDetailPanel(), currentPhase, currentProjectId, entityTypes (+32 more)

### Community 5 - "Step5Interaction.vue"
Cohesion: 0.05
Nodes (43): getAgentLog(), getReport(), getSimulationProfilesRealtime(), interviewAgents(), activeTab, addLog(), chatHistory, chatHistoryCache (+35 more)

### Community 6 - "simulation.py"
Cohesion: 0.04
Nodes (18): create_simulation(), download_simulation_config(), download_simulation_script(), get_agent_stats(), _get_default_platform(), get_entities_by_type(), get_interview_history(), get_run_status() (+10 more)

### Community 7 - "graph.py"
Cohesion: 0.06
Nodes (15): allowed_file(), build_graph(), delete_graph(), delete_project(), generate_ontology(), get_graph_data(), get_project(), get_task() (+7 more)

### Community 8 - "SimulationConfigGenerator"
Cohesion: 0.10
Nodes (3): AgentActivityConfig, EventConfig, SimulationConfigGenerator

### Community 9 - "pipeline.py"
Cohesion: 0.16
Nodes (13): _base(), delete_pipeline(), _dir(), _load(), _ok(), _path(), pipeline_list(), pipeline_status() (+5 more)

### Community 10 - "Config"
Cohesion: 0.09
Nodes (10): export_simulation(), list_models(), mask_key(), _ollama_root(), save_config(), system_models(), system_status(), test_llm() (+2 more)

### Community 11 - "Step3Simulation.vue"
Cohesion: 0.07
Nodes (36): getRunStatus(), getRunStatusDetail(), actionIds, addLog(), allActions, checkPlatformsCompleted(), chronologicalActions, doStartSimulation() (+28 more)

### Community 12 - "mockApi.ts"
Cohesion: 0.06
Nodes (52): devDependencies, @axe-core/playwright, @playwright/test, typescript, name, private, scripts, test (+44 more)

### Community 13 - "Step2EnvSetup.vue"
Cohesion: 0.09
Nodes (38): Neuerungen aus dem Original (666ghj/MiroFish), Offene Frontend-Punkte (nicht angewendet, Umbau läuft parallel), Prüfung, getSimulationConfigRealtime(), addLog(), autoGeneratedRounds, currentStage, customMaxRounds (+30 more)

### Community 14 - "MainView.vue"
Cohesion: 0.09
Nodes (36): addLog(), buildProgress, currentPhase, currentProjectId, currentStep, error, fetchGraphData(), graphData (+28 more)

### Community 15 - "README-EN.md"
Cohesion: 0.05
Nodes (40): Der eine Aufruf, der alles macht, Einzelne Stufen (wenn du selbst steuern willst), Ergebnisse abholen, MiroFish API (für Skripte, Agenten und eigene Oberflächen), Python-Beispiel, 1. Ollama und Modelle, 2a. Start mit Docker (empfohlen), 2b. Start aus dem Quellcode (+32 more)

### Community 16 - "SimulationRunView.vue"
Cohesion: 0.08
Nodes (31): getEnvStatus(), getSimulation(), getSimulationConfig(), addLog(), currentSimulationId, currentStatus, graphData, graphLoading (+23 more)

### Community 18 - "run_reddit_simulation"
Cohesion: 0.08
Nodes (9): PlatformActionLogger, create_model(), _enrich_action_context(), fetch_new_actions_from_db(), get_active_agents_for_round(), get_agent_names_from_config(), PlatformSimulation, run_reddit_simulation() (+1 more)

### Community 21 - "SimulationIPCClient"
Cohesion: 0.11
Nodes (3): IPCCommand, IPCResponse, SimulationIPCClient

### Community 23 - "SimulationView.vue"
Cohesion: 0.09
Nodes (27): closeSimulationEnv(), stopSimulation(), addLog(), checkAndStopRunningSimulation(), currentSimulationId, currentStatus, forceStopSimulation(), graphData (+19 more)

### Community 24 - "run_reddit_simulation.py"
Cohesion: 0.07
Nodes (13): apply_python_seeds(), build_model_config_dict(), resolve_seed_and_temperature(), CommandType, main(), MaxTokensWarningFilter, setup_oasis_logging(), UnicodeFormatter (+5 more)

### Community 26 - "simulation_runner.py"
Cohesion: 0.18
Nodes (4): CommandStatus, CommandType, RunnerStatus, ZepGraphMemoryManager

### Community 27 - "HistoryDatabase.vue"
Cohesion: 0.08
Nodes (17): deleteSimulation(), closeModal(), confirmDelete(), containerStyle, goToProject(), goToReport(), goToSimulation(), historyContainer (+9 more)

### Community 29 - "Home.vue"
Cohesion: 0.08
Nodes (24): startPipeline(), state, activeRuns, add(), autopilot, canSubmit, error, fileInput (+16 more)

### Community 30 - "ReportView.vue"
Cohesion: 0.09
Nodes (21): addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph(), loadReportData() (+13 more)

### Community 32 - "3. Detaillierte Spezifikation nach Seiten und Komponenten"
Cohesion: 0.06
Nodes (33): 1. Barrierefreiheit (e2e-Befund), 1. Gemeinsame Header-Architektur am Smartphone, 1. Kurzurteil, 1. Mobil-Verhalten, 1. Mobil-Verhalten (`04-durchlauf-mobil.png`), 1. Mobil-Verhalten (Samsung S23 Ultra, 412 px), 1. Problemstellung & IST-Zustand (Screenshots 10 & 11), 2. Befundtabelle (+25 more)

### Community 33 - "GraphPanel.vue"
Cohesion: 0.09
Nodes (22): closeDetailPanel(), emit, entityTypes, expandedSelfLoops, graphContainer, graphSvg, handleResize(), nodeCountRef (+14 more)

### Community 34 - "InteractionView.vue"
Cohesion: 0.08
Nodes (22): { locale, t }, addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph() (+14 more)

### Community 39 - "SimulationLogManager"
Cohesion: 0.15
Nodes (3): SimulationLogManager, load_config(), main()

### Community 40 - "getGraphData"
Cohesion: 0.60
Nodes (5): buildGraph(), generateOntology(), getGraphData(), getTaskStatus(), service

### Community 41 - "package.json"
Cohesion: 0.11
Nodes (17): description, devDependencies, concurrently, engines, node, license, name, scripts (+9 more)

### Community 42 - "HistoryView.vue"
Cohesion: 0.11
Nodes (22): deletePipeline(), listPipelines(), STEP_LABELS, STEP_ORDER, getSimulationHistory(), activeCount, poll(), route (+14 more)

### Community 43 - "SettingsView.vue"
Cohesion: 0.11
Nodes (16): baseUrl(), cfg, load(), masked, memoryLabel, models, result, save() (+8 more)

### Community 44 - "ZepEntityReader"
Cohesion: 0.13
Nodes (4): generate_profiles(), get_entity_detail(), get_graph_entities(), ZepEntityReader

### Community 45 - "ZepToolsService"
Cohesion: 0.05
Nodes (5): AgentInterview, EdgeInfo, NodeInfo, SearchResult, ZepToolsService

### Community 46 - "retry_with_backoff_async"
Cohesion: 0.15
Nodes (6): retry_with_backoff(), retry_with_backoff_async(), decorator(), decorator(), wrapper(), RetryableAPIClient

### Community 49 - "Übersicht"
Cohesion: 0.19
Nodes (3): _coerce_to_str(), _coerce_to_str_list(), Übersicht

### Community 54 - "LLMClient"
Cohesion: 0.10
Nodes (5): _clean_chat_text(), _contains_additional_json_container(), _is_response_format_unsupported(), LLMClient, LLMResponseError

### Community 56 - "error"
Cohesion: 0.07
Nodes (21): chat_with_report_agent(), check_report_status(), delete_report(), download_report(), generate_report(), get_agent_log(), get_console_log(), get_generate_status() (+13 more)

### Community 57 - "MiroFish E2E (Playwright)"
Cohesion: 0.13
Nodes (13): frontend(), 1. Fußmenü verdeckt Bedienelemente (Handy), 2. Barrierefreiheit (axe serious/critical), 3. iPhone (WebKit): seitliche Scrollleiste, Bekannte Befunde (E2E), Nicht als App-Bug gewertet (Tests angepasst), Bekannte App-Fehler, CI (+5 more)

### Community 58 - "cleanup.py"
Cohesion: 0.15
Nodes (21): _child(), _delete_graph_storage(), _delete_pipelines_for_simulation(), delete_project_cascade(), _delete_reports_for(), _inside(), _iter_pipelines(), _maybe_delete_project() (+13 more)

### Community 59 - "vue-i18n"
Cohesion: 0.12
Nodes (10): route, showTheme, { t }, { t }, savedLanguage, app, router, routes (+2 more)

### Community 60 - "os"
Cohesion: 0.08
Nodes (8): PlatformConfig, SimulationParameters, TimeSimulationConfig, PlatformType, FilteredEntities, create_chat_completion(), extract_chat_completion_text(), is_gpt5_family()

### Community 63 - "ThemePicker.vue"
Cohesion: 0.11
Nodes (34): busy, choose(), chooseOwn(), current, error, input, isDefault, ownColor (+26 more)

### Community 64 - "frontend/package.json"
Cohesion: 0.09
Nodes (21): dependencies, axios, d3, vue, vue-i18n, vue-router, devDependencies, vite (+13 more)

### Community 65 - "Design-System: MiroFish „Editorial Clarity“"
Cohesion: 0.08
Nodes (24): 1. Design-Richtung & Philosophie, 2. Typografie, 3.1 Helles Design (Light Mode - Standard), 3.2 Dunkles Design (Dark Mode - `[data-theme="dark"]`), 3. Farbpalette & Nachgerechnete WCAG-AA-Kontraste, 4. Abstands- und Rastersystem, 5.1 Buttons (Schaltflächen), 5.2 Karten (Cards) (+16 more)

### Community 67 - "TaskManager"
Cohesion: 0.09
Nodes (7): _check_simulation_prepared(), get_prepare_status(), prepare_simulation(), run_prepare(), Task, TaskManager, debug()

### Community 68 - "TextProcessor"
Cohesion: 0.10
Nodes (4): TextProcessor, FileParser, _read_text_with_fallback(), split_text_into_chunks()

### Community 70 - "Änderungen"
Cohesion: 0.29
Nodes (6): Abnahme, `GraphPanel.vue`, i18n (`de.json` / `en.json`), `Step1GraphBuild.vue`, UX-Report: Wissensgraph & Schritt 1 (Feinschliff), Änderungen

### Community 71 - "fetchAgentLog"
Cohesion: 0.25
Nodes (8): getConsoleLog(), addLog(), emit, fetchAgentLog(), fetchConsoleLog(), loadMethodology(), startPolling(), stopPolling()

### Community 72 - "UX-Report: Graph-Höhe mobil (Seiten-Scroll-Regression)"
Cohesion: 0.25
Nodes (7): Abnahme, E2E, Gegenprobe, Problem, Schritt-Views (`MainView`, `SimulationView`, `SimulationRunView`, `ReportView`, `InteractionView`), UX-Report: Graph-Höhe mobil (Seiten-Scroll-Regression), Änderungen

### Community 73 - "UX-REPORT – Cursor Live (Audit-2 Nacharbeit)"
Cohesion: 0.33
Nodes (5): Abnahme, E2E, Handy: Seiten-Scroll statt Innen-Scroll (Schritt-Seiten), Texte, UX-REPORT – Cursor Live (Audit-2 Nacharbeit)

### Community 74 - "compilerOptions"
Cohesion: 0.17
Nodes (11): compilerOptions, esModuleInterop, module, moduleResolution, noEmit, resolveJsonModule, skipLibCheck, strict (+3 more)

### Community 75 - "RunView.vue"
Cohesion: 0.11
Nodes (16): getPipeline(), cleanedUp, currentDetail, currentLabel, etaText, HINTS, load(), loadError (+8 more)

### Community 76 - "simulation.js"
Cohesion: 0.17
Nodes (6): requestWithRetry(), chatWithReport(), generateReport(), getPrepareStatus(), prepareSimulation(), startSimulation()

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

### Community 88 - "test_cleanup.py"
Cohesion: 0.29
Nodes (11): _dump(), make_project(), make_report(), make_run(), make_sim(), test_cascade_removes_only_the_finished_simulation(), test_delete_failed_pipelines_removes_failed_keeps_running_and_completed(), test_pipeline_cascade_removes_its_project() (+3 more)

### Community 89 - "UX-REPORT – belkis (Abschnitt 3.1A, 3.3–3.6, global)"
Cohesion: 0.40
Nodes (4): Abnahme, Nicht angefasst, UX-REPORT – belkis (Abschnitt 3.1A, 3.3–3.6, global), Änderungen

### Community 90 - "delete_pipeline_cascade"
Cohesion: 0.19
Nodes (10): mark_stale_runs(), delete_failed_pipelines(), delete_pipeline_cascade(), Aufräumen, Automatisch, Durchlauf löschen, Projekt und Graph, Simulation löschen (+2 more)

### Community 92 - "report_validation.py"
Cohesion: 0.06
Nodes (41): append_methodology_to_markdown(), apply_python_seeds(), best_content_match(), build_manifest(), build_methodology(), build_model_config_dict(), collect_events(), content_overlap_in_window() (+33 more)

### Community 94 - "delete_simulation_cascade"
Cohesion: 0.18
Nodes (6): delete_simulation(), CleanupBusy, CleanupError, delete_simulation_cascade(), _require(), test_symlink_outside_upload_is_not_followed()

### Community 96 - "run_parallel_simulation.py"
Cohesion: 0.08
Nodes (9): CommandType, disable_oasis_logging(), _get_comment_info(), _get_post_info(), _get_user_name(), init_logging_for_simulation(), MaxTokensWarningFilter, setup_signal_handlers() (+1 more)

### Community 98 - "Konkrete Template-Textersetzungen:"
Cohesion: 0.50
Nodes (4): 1. In `Home.vue`:, 2. In `Step1GraphBuild.vue`:, Konkrete Template-Textersetzungen:, Mangel 7: Fachjargon in Nutzertexten

### Community 99 - "logger.py"
Cohesion: 0.11
Nodes (9): create_app(), log_request(), log_response(), require_api_token(), token_ok(), _ensure_utf8_stdout(), get_logger(), setup_logger() (+1 more)

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

### Community 106 - "zep_provider.py"
Cohesion: 0.23
Nodes (3): fetch_all_edges(), fetch_all_nodes(), _fetch_page_with_retry()

### Community 112 - "ontology_generator.py"
Cohesion: 0.24
Nodes (4): _ascii_fold(), resolve_entity_name(), _to_pascal_case(), _to_upper_snake_case()

### Community 114 - "I18N-Bericht"
Cohesion: 0.33
Nodes (5): Bewusst nicht übersetzte Stellen, I18N-Bericht, Offene Punkte, Prüfung, Umfang

### Community 115 - "Step1GraphBuild.vue"
Cohesion: 0.17
Nodes (9): createSimulation(), creatingSimulation, graphStats, handleEnterEnvSetup(), logContent, props, router, selectedOntologyItem (+1 more)

### Community 120 - "graph_builder.py"
Cohesion: 0.27
Nodes (3): normalize_ontology_attribute(), normalize_ontology_attributes(), normalize_ontology_source_targets()

### Community 121 - "_runner_alive"
Cohesion: 0.33
Nodes (3): _runner_alive(), simulation_is_active(), _stop_runner()

### Community 125 - "UX-REPORT – Cursor Validierung (V1)"
Cohesion: 0.29
Nodes (6): Abnahme, Berichtskopf, E2E, i18n, Methodik-Karte, UX-REPORT – Cursor Validierung (V1)

### Community 128 - "Zukunftsprognosebericht: Dynamik der Parkgebührenanpassung und die Eskalationspfade zum Bürgerentscheid"
Cohesion: 0.33
Nodes (5): Agentenverhalten undfraktionsbildende Dynamiken, Chronologie der ersten vier Wochen: Von der Reibung zur Mobilisierung, Emergente Trends und Wahrscheinlichkeit des Bürgerentscheids, Risikoprognose: Soziale Fragmentierung und wirtschaftliche Stagnation, Zukunftsprognosebericht: Dynamik der Parkgebührenanpassung und die Eskalationspfade zum Bürgerentscheid

### Community 129 - "Ausgangslage: Hallenbad Süd in Neuberg"
Cohesion: 0.40
Nodes (4): Ausgangslage: Hallenbad Süd in Neuberg, Entscheidung, Weitere Beteiligte, Wer das Hallenbad Süd heute nutzt

### Community 138 - "Validierung V1/V2"
Cohesion: 0.40
Nodes (4): Prüfung, Validierung V1/V2, Was V1 leistet, Was V2 leistet

## Knowledge Gaps
- **553 isolated node(s):** `mirofish-backend`, `docker-entrypoint.sh script`, `docker-test.sh script`, `name`, `private` (+548 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1522 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **60 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Neuerungen aus dem Original (666ghj/MiroFish)` connect `Step2EnvSetup.vue` to `Übersicht`?**
  _High betweenness centrality (0.289) - this node is a cross-community bridge._
- **Are the 38 inferred relationships involving `Config` (e.g. with `allowed_file()` and `build_graph()`) actually correct?**
  _`Config` has 38 INFERRED edges - model-reasoned connections that need verification._
- **What connects `mirofish-backend`, `docker-entrypoint.sh script`, `docker-test.sh script` to the rest of the system?**
  _553 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `MemoryProvider` be split into smaller, more focused modules?**
  _Cohesion score 0.07862903225806452 - nodes in this community are weakly interconnected._
- **Why does `Offene Frontend-Punkte (nicht angewendet, Umbau läuft parallel)` connect `Step2EnvSetup.vue` to `Step3Simulation.vue`?**
  _High betweenness centrality (0.289) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `error()` (e.g. with `generate_ontology()` and `.chat_json()`) actually correct?**
  _`error()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `interview_agent` be split into smaller, more focused modules?**
  _Cohesion score 0.10476190476190476 - nodes in this community are weakly interconnected._