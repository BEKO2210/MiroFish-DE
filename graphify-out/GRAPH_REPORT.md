# Graph Report - mirofish-ensemble-fe  (2026-10-13)

## Corpus Check
- 147 files · ~690,923 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 7, .example 1, .lock 1)

## Summary
- 2970 nodes · 5842 edges · 149 communities (91 shown, 58 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 391 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `374af586`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- MemoryProvider
- interview_agent
- Step4Report.vue
- services/__init__.py
- Process.vue
- Step5Interaction.vue
- simulation.py
- ProjectManager
- SimulationConfigGenerator
- pipeline.py
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
- EnsembleView.vue
- SimulationView.vue
- run_reddit_simulation.py
- ZepToolsService
- services/ensemble.py
- HistoryDatabase.vue
- SimulationRunner
- Home.vue
- ReportView.vue
- get_run_status_detail
- 3. Detaillierte Spezifikation nach Seiten und Komponenten
- GraphPanel.vue
- InteractionView.vue
- ZepMemoryProvider
- Config
- AgentActivity
- ParallelIPCHandler
- SimulationLogManager
- graph.js
- package.json
- HistoryView.vue
- SettingsView.vue
- .get_report_by_simulation
- retry_with_backoff_async
- NodeInfo
- OasisAgentProfile
- ZepGraphMemoryUpdater
- ObsidianMemoryProvider
- ReportConsoleLogger
- ActionLogger
- LLMClient
- ReportAgent
- ReportManager
- MiroFish E2E (Playwright)
- cleanup.py
- vue
- typing
- .send_command
- addLog
- ThemePicker.vue
- frontend/package.json
- Design-System: MiroFish „Editorial Clarity“
- EdgeInfo
- OntologyGenerator
- Änderungen
- getReport
- UX-Report: Graph-Höhe mobil (Seiten-Scroll-Regression)
- UX-REPORT – Cursor Live (Audit-2 Nacharbeit)
- compilerOptions
- RunView.vue
- simulation.js
- Any
- Polish-Report
- Konkrete Mobile- & Template-Fixes (Mobile First 412 px)
- get_simulation_timeline
- SwarmCanvas.vue
- get_console_log
- Design-Audit: MiroFish Web-App (Mobile First & Barrierefreiheit)
- 3. Umfassender Ansichten-Audit (View-by-View Breakdown)
- 2. Bestätigung und Tiefenanalyse der bekannten Kernmängel
- test_cleanup.py
- UX-REPORT – belkis (Abschnitt 3.1A, 3.3–3.6, global)
- delete_pipeline_cascade
- IPCResponse
- report_validation.py
- .search_graph
- delete_simulation_cascade
- report.py
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
- vue-i18n
- sample-upload.md
- Roadmap v2 – „so gut, dass es jeder gern benutzt"
- CleanupError
- REPORT-UI.md
- AgentInterview
- setup_oasis_logging
- I18N-Bericht
- Step1GraphBuild.vue
- dependencies
- setup_signal_handlers
- MemoryEdge
- getProject
- ontology_generator.py
- stop_simulation
- UX-REPORT-codex.md
- MemorySearchResult
- UX-REPORT – Cursor Validierung (V1)
- scripts
- get_agent_log
- Zukunftsprognosebericht: Dynamik der Parkgebührenanpassung und die Eskalationspfade zum Bürgerentscheid
- Ausgangslage: Hallenbad Süd in Neuberg
- EnsembleService
- setup_signal_handlers
- emit
- InsightForgeResult
- Any
- PanoramaResult
- szenarien/README.md
- docker-test.sh
- UX-REPORT – Cursor Ensemble (Mehrfachlauf)
- get_simulation_history
- get_graph_statistics_tool
- docker-entrypoint.sh
- busy-check.sh
- FilteredEntities
- MaxTokensWarningFilter

## God Nodes (most connected - your core abstractions)
1. `Config` - 74 edges
2. `error()` - 66 edges
3. `SimulationRunner` - 58 edges
4. `ReportManager` - 49 edges
5. `OasisProfileGenerator` - 34 edges
6. `ZepToolsService` - 34 edges
7. `ProjectManager` - 33 edges
8. `ObsidianMemoryProvider` - 33 edges
9. `SimulationManager` - 33 edges
10. `get_logger()` - 33 edges

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

## Communities (149 total, 58 thin omitted)

### Community 1 - "interview_agent"
Cohesion: 0.10
Nodes (5): get_env_status(), interview_agent(), interview_agents_batch(), interview_all_agents(), optimize_interview_prompt()

### Community 2 - "Step4Report.vue"
Cohesion: 0.02
Nodes (53): activeSectionIndex, activeStep, activeTocIndex, agentLogLine, agentLogs, agentTypeOptions, agentTypesLabel, collapsedSections (+45 more)

### Community 3 - "services/__init__.py"
Cohesion: 0.04
Nodes (9): chat_with_report_agent(), OasisProfileGenerator, generate_single_profile(), SimulationParameters, PlatformType, SimulationManager, SimulationState, SimulationStatus (+1 more)

### Community 4 - "Process.vue"
Cohesion: 0.07
Nodes (36): getPendingUpload(), buildProgress, closeDetailPanel(), currentPhase, currentProjectId, entityTypes, error, graphContainer (+28 more)

### Community 5 - "Step5Interaction.vue"
Cohesion: 0.05
Nodes (32): getSimulationProfilesRealtime(), activeTab, autoGrowChatInput(), autoGrowMobileChatInput(), chatHistory, chatHistoryCache, chatInput, chatInputRef (+24 more)

### Community 6 - "simulation.py"
Cohesion: 0.04
Nodes (26): _check_simulation_prepared(), close_simulation_env(), create_simulation(), download_simulation_config(), download_simulation_script(), generate_profiles(), _get_default_platform(), get_entities_by_type() (+18 more)

### Community 7 - "ProjectManager"
Cohesion: 0.07
Nodes (9): allowed_file(), delete_project(), generate_ontology(), get_project(), list_projects(), reset_project(), Project, ProjectManager (+1 more)

### Community 8 - "SimulationConfigGenerator"
Cohesion: 0.07
Nodes (5): AgentActivityConfig, EventConfig, PlatformConfig, SimulationConfigGenerator, TimeSimulationConfig

### Community 9 - "pipeline.py"
Cohesion: 0.16
Nodes (13): _base(), delete_pipeline(), _dir(), _load(), mark_stale_runs(), _ok(), _path(), pipeline_list() (+5 more)

### Community 10 - "system.py"
Cohesion: 0.16
Nodes (6): list_models(), mask_key(), _ollama_root(), save_config(), system_models(), system_status()

### Community 11 - "Step3Simulation.vue"
Cohesion: 0.07
Nodes (38): getRunStatus(), getRunStatusDetail(), startSimulation(), stopSimulation(), actionIds, addLog(), allActions, checkPlatformsCompleted() (+30 more)

### Community 12 - "mockApi.ts"
Cohesion: 0.05
Nodes (54): devDependencies, @axe-core/playwright, @playwright/test, typescript, name, private, scripts, test (+46 more)

### Community 13 - "Step2EnvSetup.vue"
Cohesion: 0.10
Nodes (37): Offene Frontend-Punkte (nicht angewendet, Umbau läuft parallel), getSimulationConfigRealtime(), prepareSimulation(), addLog(), autoGeneratedRounds, currentStage, customMaxRounds, displayProfiles (+29 more)

### Community 14 - "MainView.vue"
Cohesion: 0.09
Nodes (36): clearPendingUpload(), addLog(), buildProgress, currentPhase, currentProjectId, currentStep, error, graphData (+28 more)

### Community 15 - "README-EN.md"
Cohesion: 0.05
Nodes (40): Der eine Aufruf, der alles macht, Einzelne Stufen (wenn du selbst steuern willst), Ergebnisse abholen, MiroFish API (für Skripte, Agenten und eigene Oberflächen), Python-Beispiel, 1. Ollama und Modelle, 2a. Start mit Docker (empfohlen), 2b. Start aus dem Quellcode (+32 more)

### Community 16 - "SimulationRunView.vue"
Cohesion: 0.08
Nodes (31): closeSimulationEnv(), getEnvStatus(), getSimulationConfig(), addLog(), currentSimulationId, currentStatus, graphData, graphLoading (+23 more)

### Community 18 - "run_reddit_simulation"
Cohesion: 0.08
Nodes (7): PlatformActionLogger, create_model(), get_active_agents_for_round(), get_agent_names_from_config(), PlatformSimulation, run_reddit_simulation(), run_twitter_simulation()

### Community 22 - "EnsembleView.vue"
Cohesion: 0.07
Nodes (27): cancelEnsemble(), deleteEnsemble(), getEnsemble(), busy, canCancel, canDelete, CellStat, checklist (+19 more)

### Community 23 - "SimulationView.vue"
Cohesion: 0.10
Nodes (26): getSimulation(), addLog(), checkAndStopRunningSimulation(), currentSimulationId, currentStatus, forceStopSimulation(), graphData, graphLoading (+18 more)

### Community 24 - "run_reddit_simulation.py"
Cohesion: 0.08
Nodes (11): apply_python_seeds(), build_model_config_dict(), resolve_seed_and_temperature(), CommandType, main(), setup_oasis_logging(), UnicodeFormatter, CommandType (+3 more)

### Community 26 - "services/ensemble.py"
Cohesion: 0.12
Nodes (5): _write_json_atomic(), CommandStatus, CommandType, show_expected_formats(), test_profile_formats()

### Community 27 - "HistoryDatabase.vue"
Cohesion: 0.08
Nodes (14): closeModal(), containerStyle, goToProject(), goToReport(), goToSimulation(), historyContainer, hoveringCard, isExpanded (+6 more)

### Community 28 - "SimulationRunner"
Cohesion: 0.04
Nodes (6): start_simulation(), RunnerStatus, SimulationRunner, cleanup_handler(), SimulationRunState, ZepGraphMemoryManager

### Community 29 - "Home.vue"
Cohesion: 0.09
Nodes (22): startPipeline(), activeRuns, add(), autopilot, canSubmit, error, fileInput, files (+14 more)

### Community 30 - "ReportView.vue"
Cohesion: 0.08
Nodes (22): { locale, t }, addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph() (+14 more)

### Community 31 - "get_run_status_detail"
Cohesion: 0.07
Nodes (4): get_agent_stats(), get_run_status_detail(), get_simulation_actions(), AgentAction

### Community 32 - "3. Detaillierte Spezifikation nach Seiten und Komponenten"
Cohesion: 0.06
Nodes (33): 1. Barrierefreiheit (e2e-Befund), 1. Gemeinsame Header-Architektur am Smartphone, 1. Kurzurteil, 1. Mobil-Verhalten, 1. Mobil-Verhalten (`04-durchlauf-mobil.png`), 1. Mobil-Verhalten (Samsung S23 Ultra, 412 px), 1. Problemstellung & IST-Zustand (Screenshots 10 & 11), 2. Befundtabelle (+25 more)

### Community 33 - "GraphPanel.vue"
Cohesion: 0.10
Nodes (20): closeDetailPanel(), emit, entityTypes, expandedSelfLoops, graphContainer, graphSvg, handleResize(), nodeCountRef (+12 more)

### Community 34 - "InteractionView.vue"
Cohesion: 0.09
Nodes (22): addLog(), currentReportId, currentStatus, graphData, graphLoading, graphPanelRef, leftPanelStyle, loadGraph() (+14 more)

### Community 35 - "ZepMemoryProvider"
Cohesion: 0.12
Nodes (3): MemoryFactory, HybridMemoryProvider, ZepMemoryProvider

### Community 36 - "Config"
Cohesion: 0.15
Nodes (3): Config, main(), upload()

### Community 39 - "SimulationLogManager"
Cohesion: 0.13
Nodes (3): SimulationLogManager, load_config(), main()

### Community 40 - "graph.js"
Cohesion: 0.35
Nodes (7): buildGraph(), generateOntology(), getTaskStatus(), requestWithRetry(), service, chatWithReport(), generateReport()

### Community 41 - "package.json"
Cohesion: 0.11
Nodes (17): description, devDependencies, concurrently, engines, node, license, name, scripts (+9 more)

### Community 42 - "HistoryView.vue"
Cohesion: 0.15
Nodes (17): deletePipeline(), deleteSimulation(), getSimulationHistory(), confirmDelete(), loadHistory(), deleting, doDelete(), error (+9 more)

### Community 43 - "SettingsView.vue"
Cohesion: 0.11
Nodes (16): baseUrl(), cfg, load(), masked, memoryLabel, models, result, save() (+8 more)

### Community 44 - ".get_report_by_simulation"
Cohesion: 0.17
Nodes (3): check_report_status(), get_report_by_simulation(), ReportStatus

### Community 46 - "retry_with_backoff_async"
Cohesion: 0.15
Nodes (6): retry_with_backoff(), retry_with_backoff_async(), decorator(), decorator(), wrapper(), RetryableAPIClient

### Community 49 - "OasisAgentProfile"
Cohesion: 0.11
Nodes (4): _coerce_to_str(), _coerce_to_str_list(), OasisAgentProfile, Übersicht

### Community 54 - "LLMClient"
Cohesion: 0.08
Nodes (7): test_llm(), _clean_chat_text(), _is_response_format_unsupported(), LLMClient, LLMResponseError, Neuerungen aus dem Original (666ghj/MiroFish), Prüfung

### Community 55 - "ReportAgent"
Cohesion: 0.08
Nodes (3): run_generate(), ReportAgent, ReportSection

### Community 56 - "ReportManager"
Cohesion: 0.04
Nodes (10): delete_report(), download_report(), get_report(), get_report_progress(), get_report_sections(), get_single_section(), list_reports(), Report (+2 more)

### Community 57 - "MiroFish E2E (Playwright)"
Cohesion: 0.13
Nodes (13): frontend(), 1. Fußmenü verdeckt Bedienelemente (Handy), 2. Barrierefreiheit (axe serious/critical), 3. iPhone (WebKit): seitliche Scrollleiste, Bekannte Befunde (E2E), Nicht als App-Bug gewertet (Tests angepasst), Bekannte App-Fehler, CI (+5 more)

### Community 58 - "cleanup.py"
Cohesion: 0.15
Nodes (21): _child(), _delete_graph_storage(), _delete_pipelines_for_simulation(), delete_project_cascade(), _delete_reports_for(), _inside(), _iter_pipelines(), _maybe_delete_project() (+13 more)

### Community 59 - "vue"
Cohesion: 0.11
Nodes (15): listPipelines(), route, showTheme, { t }, activeCount, poll(), route, { t } (+7 more)

### Community 60 - "typing"
Cohesion: 0.10
Nodes (6): create_chat_completion(), extract_chat_completion_text(), is_gpt5_family(), fetch_all_edges(), fetch_all_nodes(), _fetch_page_with_retry()

### Community 62 - "addLog"
Cohesion: 0.25
Nodes (11): interviewAgents(), addLog(), emit, saveChatHistory(), scrollToBottom(), selectAgent(), selectReportAgentChat(), sendMessage() (+3 more)

### Community 63 - "ThemePicker.vue"
Cohesion: 0.08
Nodes (44): Grenzen von V3/V4, Prüfung, Rechenzeit und Betrieb, Statistik, V3: Mehrfachlauf, V4: Gegenproben, Validierung V1/V2, Validierung V1–V4 (+36 more)

### Community 64 - "frontend/package.json"
Cohesion: 0.17
Nodes (11): devDependencies, vite, @vitejs/plugin-vue, name, private, type, version, axios (+3 more)

### Community 65 - "Design-System: MiroFish „Editorial Clarity“"
Cohesion: 0.08
Nodes (24): 1. Design-Richtung & Philosophie, 2. Typografie, 3.1 Helles Design (Light Mode - Standard), 3.2 Dunkles Design (Dark Mode - `[data-theme="dark"]`), 3. Farbpalette & Nachgerechnete WCAG-AA-Kontraste, 4. Abstands- und Rastersystem, 5.1 Buttons (Schaltflächen), 5.2 Karten (Cards) (+16 more)

### Community 68 - "OntologyGenerator"
Cohesion: 0.05
Nodes (7): OntologyGenerator, resolve_entity_name(), _to_pascal_case(), TextProcessor, FileParser, _read_text_with_fallback(), split_text_into_chunks()

### Community 70 - "Änderungen"
Cohesion: 0.29
Nodes (6): Abnahme, `GraphPanel.vue`, i18n (`de.json` / `en.json`), `Step1GraphBuild.vue`, UX-Report: Wissensgraph & Schritt 1 (Feinschliff), Änderungen

### Community 71 - "getReport"
Cohesion: 0.18
Nodes (12): listEnsembles(), getAgentLog(), getConsoleLog(), getReport(), fetchAgentLog(), fetchConsoleLog(), loadEnsembleList(), loadMethodology() (+4 more)

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
Cohesion: 0.32
Nodes (11): _dump(), make_project(), make_report(), make_run(), make_sim(), test_cascade_removes_only_the_finished_simulation(), test_delete_failed_pipelines_removes_failed_keeps_running_and_completed(), test_pipeline_cascade_removes_its_project() (+3 more)

### Community 89 - "UX-REPORT – belkis (Abschnitt 3.1A, 3.3–3.6, global)"
Cohesion: 0.40
Nodes (4): Abnahme, Nicht angefasst, UX-REPORT – belkis (Abschnitt 3.1A, 3.3–3.6, global), Änderungen

### Community 90 - "delete_pipeline_cascade"
Cohesion: 0.20
Nodes (9): delete_failed_pipelines(), delete_pipeline_cascade(), Aufräumen, Automatisch, Durchlauf löschen, Projekt und Graph, Simulation löschen, Verlauf (+1 more)

### Community 92 - "report_validation.py"
Cohesion: 0.05
Nodes (44): export_simulation(), append_methodology_to_markdown(), apply_python_seeds(), best_content_match(), build_manifest(), build_methodology(), build_model_config_dict(), collect_events() (+36 more)

### Community 94 - "delete_simulation_cascade"
Cohesion: 0.13
Nodes (7): delete_simulation(), CleanupBusy, delete_simulation_cascade(), _runner_alive(), simulation_is_active(), _stop_runner(), info()

### Community 95 - "report.py"
Cohesion: 0.05
Nodes (13): build_graph(), build_task(), delete_graph(), get_graph_data(), get_task(), list_tasks(), generate_report(), get_generate_status() (+5 more)

### Community 96 - "run_parallel_simulation.py"
Cohesion: 0.09
Nodes (10): CommandType, disable_oasis_logging(), _enrich_action_context(), fetch_new_actions_from_db(), _get_comment_info(), _get_post_info(), _get_user_name(), init_logging_for_simulation() (+2 more)

### Community 98 - "Konkrete Template-Textersetzungen:"
Cohesion: 0.50
Nodes (4): 1. In `Home.vue`:, 2. In `Step1GraphBuild.vue`:, Konkrete Template-Textersetzungen:, Mangel 7: Fachjargon in Nutzertexten

### Community 99 - "logger.py"
Cohesion: 0.09
Nodes (15): cancel_ensemble(), delete_ensemble(), _error(), get_ensemble(), list_ensembles(), mark_stale_ensembles(), start_ensemble(), create_app() (+7 more)

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

### Community 106 - "vue-i18n"
Cohesion: 0.29
Nodes (3): { t }, savedLanguage, vue-i18n

### Community 110 - "CleanupError"
Cohesion: 0.33
Nodes (3): CleanupError, _require(), test_symlink_outside_upload_is_not_followed()

### Community 114 - "I18N-Bericht"
Cohesion: 0.33
Nodes (5): Bewusst nicht übersetzte Stellen, I18N-Bericht, Offene Punkte, Prüfung, Umfang

### Community 115 - "Step1GraphBuild.vue"
Cohesion: 0.17
Nodes (9): createSimulation(), creatingSimulation, graphStats, handleEnterEnvSetup(), logContent, props, router, selectedOntologyItem (+1 more)

### Community 116 - "dependencies"
Cohesion: 0.33
Nodes (6): dependencies, axios, d3, vue, vue-i18n, vue-router

### Community 119 - "getProject"
Cohesion: 0.50
Nodes (5): getGraphData(), getProject(), fetchGraphData(), fetchGraphData(), refreshGraph()

### Community 120 - "ontology_generator.py"
Cohesion: 0.18
Nodes (5): _ascii_fold(), _to_upper_snake_case(), normalize_ontology_attribute(), normalize_ontology_attributes(), normalize_ontology_source_targets()

### Community 125 - "UX-REPORT – Cursor Validierung (V1)"
Cohesion: 0.29
Nodes (6): Abnahme, Berichtskopf, E2E, i18n, Methodik-Karte, UX-REPORT – Cursor Validierung (V1)

### Community 126 - "scripts"
Cohesion: 0.50
Nodes (4): scripts, build, dev, preview

### Community 128 - "Zukunftsprognosebericht: Dynamik der Parkgebührenanpassung und die Eskalationspfade zum Bürgerentscheid"
Cohesion: 0.33
Nodes (5): Agentenverhalten undfraktionsbildende Dynamiken, Chronologie der ersten vier Wochen: Von der Reibung zur Mobilisierung, Emergente Trends und Wahrscheinlichkeit des Bürgerentscheids, Risikoprognose: Soziale Fragmentierung und wirtschaftliche Stagnation, Zukunftsprognosebericht: Dynamik der Parkgebührenanpassung und die Eskalationspfade zum Bürgerentscheid

### Community 129 - "Ausgangslage: Hallenbad Süd in Neuberg"
Cohesion: 0.40
Nodes (4): Ausgangslage: Hallenbad Süd in Neuberg, Entscheidung, Weitere Beteiligte, Wer das Hallenbad Süd heute nutzt

### Community 130 - "EnsembleService"
Cohesion: 0.06
Nodes (29): _agent_id(), apply_without_variant(), ensemble_markdown(), EnsembleService, load_simulation_posts(), mark_checklist_material(), newcombe_difference_interval(), parse_checklist() (+21 more)

### Community 132 - "emit"
Cohesion: 0.50
Nodes (4): startEnsemble(), addLog(), emit, startEnsembleRun()

### Community 138 - "UX-REPORT – Cursor Ensemble (Mehrfachlauf)"
Cohesion: 0.50
Nodes (3): Auftrag A – Mehrfachlauf, Auftrag B – Befunde, UX-REPORT – Cursor Ensemble (Mehrfachlauf)

## Knowledge Gaps
- **586 isolated node(s):** `mirofish-backend`, `docker-entrypoint.sh script`, `docker-test.sh script`, `name`, `private` (+581 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1610 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **58 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Neuerungen aus dem Original (666ghj/MiroFish)` connect `LLMClient` to `OasisAgentProfile`, `Step2EnvSetup.vue`?**
  _High betweenness centrality (0.308) - this node is a cross-community bridge._
- **Are the 40 inferred relationships involving `Config` (e.g. with `allowed_file()` and `build_graph()`) actually correct?**
  _`Config` has 40 INFERRED edges - model-reasoned connections that need verification._
- **What connects `mirofish-backend`, `docker-entrypoint.sh script`, `docker-test.sh script` to the rest of the system?**
  _586 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `MemoryProvider` be split into smaller, more focused modules?**
  _Cohesion score 0.11594202898550725 - nodes in this community are weakly interconnected._
- **Why does `Offene Frontend-Punkte (nicht angewendet, Umbau läuft parallel)` connect `Step2EnvSetup.vue` to `Step3Simulation.vue`, `LLMClient`?**
  _High betweenness centrality (0.308) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `error()` (e.g. with `cancel_ensemble()` and `delete_ensemble()`) actually correct?**
  _`error()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Should `interview_agent` be split into smaller, more focused modules?**
  _Cohesion score 0.09956709956709957 - nodes in this community are weakly interconnected._