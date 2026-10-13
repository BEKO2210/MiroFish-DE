# Graph Report - MiroFish-DE  (2026-10-13)

## Corpus Check
- 148 files · ~735,298 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: (none) 6, .example 1, .lock 1)

## Summary
- 3072 nodes · 5986 edges · 149 communities (84 shown, 65 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 394 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0d26cf28`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- interview_agent
- Step4Report.vue
- SimulationManager
- Process.vue
- Step5Interaction.vue
- error
- graph.py
- SimulationConfigGenerator
- EnsembleService
- app/__init__.py
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
- EnsembleView.vue
- SimulationView.vue
- run_parallel_simulation.py
- test_ensemble.py
- simulation_runner.py
- HistoryDatabase.vue
- SimulationRunState
- Home.vue
- ReportView.vue
- AgentAction
- 3. Detaillierte Spezifikation nach Seiten und Komponenten
- GraphPanel.vue
- InteractionView.vue
- ZepMemoryProvider
- AgentActivity
- ParallelIPCHandler
- SimulationLogManager
- simulation.js
- package.json
- HistoryView.vue
- SettingsView.vue
- get_simulation_profiles_realtime
- ZepToolsService
- retry_with_backoff_async
- EntityNode
- OasisProfileGenerator
- ZepGraphMemoryUpdater
- ObsidianMemoryProvider
- ReportConsoleLogger
- ActionLogger
- LLMClient
- ReportAgent
- ReportManager
- .generate_config
- os
- vue
- logger.py
- services/__init__.py
- addLog
- ThemePicker.vue
- frontend/package.json
- Design-System: MiroFish „Editorial Clarity“
- FileParser
- .cleanup_all_simulations
- ontology_generator.py
- Änderungen
- getReport
- UX-Report: Graph-Höhe mobil (Seiten-Scroll-Regression)
- UX-REPORT – Cursor Live (Audit-2 Nacharbeit)
- compilerOptions
- RunView.vue
- Any
- Any
- Konkrete Mobile- & Template-Fixes (Mobile First 412 px)
- newcombe_difference_interval
- SwarmCanvas.vue
- Design-Audit: MiroFish Web-App (Mobile First & Barrierefreiheit)
- 3. Umfassender Ansichten-Audit (View-by-View Breakdown)
- 2. Bestätigung und Tiefenanalyse der bekannten Kernmängel
- ReportOutline
- .generate_profiles_from_entities
- UX-REPORT – belkis (Abschnitt 3.1A, 3.3–3.6, global)
- get_env_status
- Config
- setup_oasis_logging
- SimulationRunner
- GraphBuilderService
- _enrich_action_context
- mirofish-backend
- Konkrete Template-Textersetzungen:
- create_app
- Mangel 3: Leere Flächen mit einzelnen Rauten-Symbolen
- Mangel 4: Karten der „Simulationsaufzeichnungen“ am Handy links/rechts abgeschnitten
- Mangel 2: Badge „Elegante universelle Schwarm-Intelligenz-Engine“ bricht um
- Mangel 5: Im Prompt-Feld überlappt Badge „Engine: MiroFish-V1.0“ den Platzhaltertext
- Mangel 10: Fehlende Zeitschätzung und Statusführung bei langen Läufen (Minuten bis 1 Stunde)
- .plan_outline
- file_parser.py
- sample-upload.md
- Roadmap v2 – „so gut, dass es jeder gern benutzt"
- mark_checklist_material
- REPORT-UI.md
- setup_oasis_logging
- I18N-Bericht
- Step1GraphBuild.vue
- SimulationParameters
- setup_signal_handlers
- fetch_all_edges
- init_logging_for_simulation
- conftest.py
- setup_logger
- UX-REPORT-codex.md
- setup_signal_handlers
- UX-REPORT – Cursor Validierung (V1)
- MaxTokensWarningFilter
- Zukunftsprognosebericht: Dynamik der Parkgebührenanpassung und die Eskalationspfade zum Bürgerentscheid
- Ausgangslage: Hallenbad Süd in Neuberg
- services/ensemble.py
- setup_signal_handlers
- emit
- InterviewResult
- PanoramaResult
- szenarien/README.md
- docker-test.sh
- UX-REPORT – Cursor Ensemble (Mehrfachlauf)
- docker-entrypoint.sh
- busy-check.sh
- ZepEntityReader
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
- `Übersicht` --references--> `_get_default_platform()`  [INFERRED]
  docs/UPSTREAM.md → backend/app/api/simulation.py
- `Projekt und Graph` --references--> `delete_project_cascade()`  [INFERRED]
  docs/CLEANUP.md → backend/app/services/cleanup.py
- `Simulation löschen` --references--> `delete_simulation_cascade()`  [INFERRED]
  docs/CLEANUP.md → backend/app/services/cleanup.py
- `Durchlauf löschen` --references--> `delete_pipeline_cascade()`  [INFERRED]
  docs/CLEANUP.md → backend/app/services/cleanup.py
- `Verwaiste Reste` --references--> `sweep_orphans()`  [INFERRED]
  docs/CLEANUP.md → backend/app/services/cleanup.py

## Import Cycles
- None detected.

## Communities (149 total, 65 thin omitted)

### Community 1 - "interview_agent"
Cohesion: 0.12
Nodes (4): interview_agent(), interview_agents_batch(), interview_all_agents(), optimize_interview_prompt()

### Community 2 - "Step4Report.vue"
Cohesion: 0.02
Nodes (53): activeSectionIndex, activeStep, activeTocIndex, agentLogLine, agentLogs, agentTypeOptions, agentTypesLabel, collapsedSections (+45 more)

### Community 3 - "SimulationManager"
Cohesion: 0.04
Nodes (16): _check_simulation_prepared(), close_simulation_env(), _get_report_id_for_simulation(), get_simulation(), get_simulation_history(), list_simulations(), prepare_simulation(), run_prepare() (+8 more)

### Community 4 - "Process.vue"
Cohesion: 0.06
Nodes (40): clearPendingUpload(), getPendingUpload(), state, buildProgress, closeDetailPanel(), currentPhase, currentProjectId, entityTypes (+32 more)

### Community 5 - "Step5Interaction.vue"
Cohesion: 0.05
Nodes (32): getSimulationProfilesRealtime(), activeTab, autoGrowChatInput(), autoGrowMobileChatInput(), chatHistory, chatHistoryCache, chatInput, chatInputRef (+24 more)

### Community 6 - "error"
Cohesion: 0.04
Nodes (31): chat_with_report_agent(), check_report_status(), delete_report(), generate_report(), get_agent_log(), get_console_log(), get_generate_status(), get_graph_statistics_tool() (+23 more)

### Community 7 - "graph.py"
Cohesion: 0.05
Nodes (16): allowed_file(), build_graph(), delete_project(), generate_ontology(), get_graph_data(), get_project(), get_task(), list_projects() (+8 more)

### Community 9 - "EnsembleService"
Cohesion: 0.20
Nodes (4): EnsembleService, ChecklistRetryLLM, test_checklist_number_retry_stops_after_two_attempts(), test_checklist_prompt_retries_after_material_number()

### Community 10 - "app/__init__.py"
Cohesion: 0.08
Nodes (8): list_models(), mask_key(), _ollama_root(), save_config(), system_models(), system_status(), test_llm(), main()

### Community 11 - "Step3Simulation.vue"
Cohesion: 0.07
Nodes (36): getRunStatus(), getRunStatusDetail(), actionIds, addLog(), allActions, checkPlatformsCompleted(), chronologicalActions, doStartSimulation() (+28 more)

### Community 12 - "mockApi.ts"
Cohesion: 0.05
Nodes (55): devDependencies, @axe-core/playwright, @playwright/test, typescript, name, private, scripts, test (+47 more)

### Community 13 - "Step2EnvSetup.vue"
Cohesion: 0.08
Nodes (43): Offene Frontend-Punkte (nicht angewendet, Umbau läuft parallel), Ausgelassen, Checks, Geändert, npm audit (`cd frontend && npm audit --omit=dev`), Offen, Polish-Report, getPrepareStatus() (+35 more)

### Community 14 - "MainView.vue"
Cohesion: 0.09
Nodes (36): addLog(), buildProgress, currentPhase, currentProjectId, currentStep, error, fetchGraphData(), graphData (+28 more)

### Community 15 - "README-EN.md"
Cohesion: 0.05
Nodes (40): Der eine Aufruf, der alles macht, Einzelne Stufen (wenn du selbst steuern willst), Ergebnisse abholen, MiroFish API (für Skripte, Agenten und eigene Oberflächen), Python-Beispiel, 1. Ollama und Modelle, 2a. Start mit Docker (empfohlen), 2b. Start aus dem Quellcode (+32 more)

### Community 16 - "SimulationRunView.vue"
Cohesion: 0.08
Nodes (31): closeSimulationEnv(), getSimulationConfig(), stopSimulation(), addLog(), currentSimulationId, currentStatus, graphData, graphLoading (+23 more)

### Community 18 - "run_reddit_simulation"
Cohesion: 0.06
Nodes (8): PlatformActionLogger, create_model(), get_active_agents_for_round(), get_agent_names_from_config(), load_config(), PlatformSimulation, run_reddit_simulation(), run_twitter_simulation()

### Community 22 - "EnsembleView.vue"
Cohesion: 0.07
Nodes (32): cancelEnsemble(), deleteEnsemble(), getEnsemble(), busy, canCancel, canDelete, canGoReport, CellStat (+24 more)

### Community 23 - "SimulationView.vue"
Cohesion: 0.09
Nodes (26): getGraphData(), getEnvStatus(), addLog(), checkAndStopRunningSimulation(), currentSimulationId, currentStatus, forceStopSimulation(), graphData (+18 more)

### Community 24 - "run_parallel_simulation.py"
Cohesion: 0.09
Nodes (9): simulation_clock(), apply_python_seeds(), build_model_config_dict(), resolve_seed_and_temperature(), _utf8_open(), CommandType, main(), CommandType (+1 more)

### Community 25 - "test_ensemble.py"
Cohesion: 0.10
Nodes (10): filter_checklist_material_numbers(), _number_tokens(), parse_checklist(), FakeLLM, FakeRunner, _prepared_simulation(), test_checklist_number_filter_normalizes_material_numbers(), test_checklist_parsing_and_validation() (+2 more)

### Community 27 - "HistoryDatabase.vue"
Cohesion: 0.08
Nodes (14): closeModal(), containerStyle, goToProject(), goToReport(), goToSimulation(), historyContainer, hoveringCard, isExpanded (+6 more)

### Community 29 - "Home.vue"
Cohesion: 0.09
Nodes (22): startPipeline(), activeRuns, add(), autopilot, canSubmit, error, fileInput, files (+14 more)

### Community 30 - "ReportView.vue"
Cohesion: 0.08
Nodes (22): { locale, t }, addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph() (+14 more)

### Community 32 - "3. Detaillierte Spezifikation nach Seiten und Komponenten"
Cohesion: 0.06
Nodes (33): 1. Barrierefreiheit (e2e-Befund), 1. Gemeinsame Header-Architektur am Smartphone, 1. Kurzurteil, 1. Mobil-Verhalten, 1. Mobil-Verhalten (`04-durchlauf-mobil.png`), 1. Mobil-Verhalten (Samsung S23 Ultra, 412 px), 1. Problemstellung & IST-Zustand (Screenshots 10 & 11), 2. Befundtabelle (+25 more)

### Community 33 - "GraphPanel.vue"
Cohesion: 0.09
Nodes (22): closeDetailPanel(), emit, entityTypes, expandedSelfLoops, graphContainer, graphSvg, handleResize(), nodeCountRef (+14 more)

### Community 34 - "InteractionView.vue"
Cohesion: 0.08
Nodes (25): getProject(), getSimulation(), addLog(), currentReportId, currentStatus, graphData, graphLoading, graphPanelRef (+17 more)

### Community 35 - "ZepMemoryProvider"
Cohesion: 0.07
Nodes (3): MemorySearchResult, HybridMemoryProvider, ZepMemoryProvider

### Community 40 - "simulation.js"
Cohesion: 0.17
Nodes (9): buildGraph(), generateOntology(), getTaskStatus(), requestWithRetry(), service, chatWithReport(), generateReport(), prepareSimulation() (+1 more)

### Community 41 - "package.json"
Cohesion: 0.11
Nodes (17): description, devDependencies, concurrently, engines, node, license, name, scripts (+9 more)

### Community 42 - "HistoryView.vue"
Cohesion: 0.14
Nodes (18): deletePipeline(), deleteSimulation(), getSimulationHistory(), confirmDelete(), loadHistory(), goToReport(), deleting, doDelete() (+10 more)

### Community 43 - "SettingsView.vue"
Cohesion: 0.11
Nodes (16): baseUrl(), cfg, load(), masked, memoryLabel, models, result, save() (+8 more)

### Community 44 - "get_simulation_profiles_realtime"
Cohesion: 0.11
Nodes (5): _get_default_platform(), get_simulation_comments(), get_simulation_posts(), get_simulation_profiles(), get_simulation_profiles_realtime()

### Community 45 - "ZepToolsService"
Cohesion: 0.05
Nodes (6): AgentInterview, EdgeInfo, InsightForgeResult, NodeInfo, SearchResult, ZepToolsService

### Community 46 - "retry_with_backoff_async"
Cohesion: 0.15
Nodes (6): retry_with_backoff(), retry_with_backoff_async(), decorator(), decorator(), wrapper(), RetryableAPIClient

### Community 49 - "OasisProfileGenerator"
Cohesion: 0.09
Nodes (7): _coerce_to_str(), _coerce_to_str_list(), OasisAgentProfile, OasisProfileGenerator, show_expected_formats(), test_profile_formats(), Übersicht

### Community 54 - "LLMClient"
Cohesion: 0.06
Nodes (9): _clean_chat_text(), _is_response_format_unsupported(), LLMClient, LLMResponseError, create_chat_completion(), extract_chat_completion_text(), is_gpt5_family(), Neuerungen aus dem Original (666ghj/MiroFish) (+1 more)

### Community 56 - "ReportManager"
Cohesion: 0.10
Nodes (3): download_report(), Report, ReportManager

### Community 57 - ".generate_config"
Cohesion: 0.15
Nodes (3): AgentActivityConfig, EventConfig, PlatformConfig

### Community 58 - "os"
Cohesion: 0.05
Nodes (63): _base(), delete_pipeline(), _dir(), _load(), mark_stale_runs(), _ok(), _path(), pipeline_list() (+55 more)

### Community 59 - "vue"
Cohesion: 0.09
Nodes (17): listPipelines(), route, showTheme, { t }, { t }, activeCount, poll(), route (+9 more)

### Community 60 - "logger.py"
Cohesion: 0.09
Nodes (4): MemoryEdge, MemoryProvider, MemoryFactory, get_logger()

### Community 61 - "services/__init__.py"
Cohesion: 0.10
Nodes (6): CommandStatus, CommandType, IPCCommand, IPCResponse, SimulationIPCClient, SimulationIPCServer

### Community 62 - "addLog"
Cohesion: 0.25
Nodes (11): interviewAgents(), addLog(), emit, saveChatHistory(), scrollToBottom(), selectAgent(), selectReportAgentChat(), sendMessage() (+3 more)

### Community 63 - "ThemePicker.vue"
Cohesion: 0.08
Nodes (44): Grenzen von V3/V4, Prüfung, Rechenzeit und Betrieb, Statistik, V3: Mehrfachlauf, V4: Gegenproben, Validierung V1/V2, Validierung V1–V4 (+36 more)

### Community 64 - "frontend/package.json"
Cohesion: 0.09
Nodes (21): dependencies, axios, d3, vue, vue-i18n, vue-router, devDependencies, vite (+13 more)

### Community 65 - "Design-System: MiroFish „Editorial Clarity“"
Cohesion: 0.08
Nodes (24): 1. Design-Richtung & Philosophie, 2. Typografie, 3.1 Helles Design (Light Mode - Standard), 3.2 Dunkles Design (Dark Mode - `[data-theme="dark"]`), 3. Farbpalette & Nachgerechnete WCAG-AA-Kontraste, 4. Abstands- und Rastersystem, 5.1 Buttons (Schaltflächen), 5.2 Karten (Cards) (+16 more)

### Community 68 - "ontology_generator.py"
Cohesion: 0.08
Nodes (8): _ascii_fold(), OntologyGenerator, resolve_entity_name(), _to_pascal_case(), _to_upper_snake_case(), normalize_ontology_attribute(), normalize_ontology_attributes(), normalize_ontology_source_targets()

### Community 70 - "Änderungen"
Cohesion: 0.29
Nodes (6): Abnahme, `GraphPanel.vue`, i18n (`de.json` / `en.json`), `Step1GraphBuild.vue`, UX-Report: Wissensgraph & Schritt 1 (Feinschliff), Änderungen

### Community 71 - "getReport"
Cohesion: 0.18
Nodes (12): listEnsembles(), getAgentLog(), getConsoleLog(), getReport(), fetchAgentLog(), fetchConsoleLog(), loadEnsembleList(), loadMethodology() (+4 more)

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
Cohesion: 0.10
Nodes (18): getPipeline(), STEP_LABELS, STEP_ORDER, cleanedUp, currentDetail, currentLabel, etaText, HINTS (+10 more)

### Community 76 - "Any"
Cohesion: 0.26
Nodes (6): _read_json(), validate_variants(), _variant_label(), verify_classification_evidence(), test_evidence_must_reference_existing_post(), test_start_hour_validation_happens_before_start()

### Community 79 - "Konkrete Mobile- & Template-Fixes (Mobile First 412 px)"
Cohesion: 0.13
Nodes (15): CSS-Fix (`Home.vue` `<style scoped>`):, CSS-Fix in `Home.vue`:, CSS-Fix in `tokens.css` (wird automatisch wirksam) bzw. `App.vue`:, CSS-Fix (`MainView.vue` `<style scoped>`):, CSS-Fix (`MainView.vue` `<style scoped>`):, Globaler CSS-Klassen-Fix (Drop-in):, Konkrete Mobile- & Template-Fixes (Mobile First 412 px), Mangel 11: Touch-Targets unter 44 px (Löschen-Button, Switcher) (+7 more)

### Community 80 - "newcombe_difference_interval"
Cohesion: 0.22
Nodes (5): newcombe_difference_interval(), _round(), wilson_interval(), test_newcombe_method_10_known_value(), test_wilson_known_value()

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

### Community 92 - "Config"
Cohesion: 0.05
Nodes (45): export_simulation(), Config, append_methodology_to_markdown(), apply_python_seeds(), best_content_match(), build_manifest(), build_methodology(), build_model_config_dict() (+37 more)

### Community 95 - "GraphBuilderService"
Cohesion: 0.05
Nodes (7): build_task(), delete_graph(), get_prepare_status(), Task, TaskManager, GraphBuilderService, GraphInfo

### Community 96 - "_enrich_action_context"
Cohesion: 0.13
Nodes (5): _enrich_action_context(), fetch_new_actions_from_db(), _get_comment_info(), _get_post_info(), _get_user_name()

### Community 98 - "Konkrete Template-Textersetzungen:"
Cohesion: 0.50
Nodes (4): 1. In `Home.vue`:, 2. In `Step1GraphBuild.vue`:, Konkrete Template-Textersetzungen:, Mangel 7: Fachjargon in Nutzertexten

### Community 99 - "create_app"
Cohesion: 0.07
Nodes (25): cancel_ensemble(), delete_ensemble(), _error(), get_ensemble(), list_ensembles(), mark_stale_ensembles(), start_ensemble(), create_app() (+17 more)

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

### Community 109 - "Roadmap v2 – „so gut, dass es jeder gern benutzt""
Cohesion: 0.50
Nodes (3): Roadmap v2 – „so gut, dass es jeder gern benutzt", Stand Validierung 13.10.2026 abends, Validierung (ab 13.10.2026) – vom Szenariogenerator zur prüfbaren Prognose

### Community 110 - "mark_checklist_material"
Cohesion: 0.40
Nodes (3): mark_checklist_material(), verified_material_quote(), test_material_quote_must_be_normalized_verbatim()

### Community 114 - "I18N-Bericht"
Cohesion: 0.33
Nodes (5): Bewusst nicht übersetzte Stellen, I18N-Bericht, Offene Punkte, Prüfung, Umfang

### Community 115 - "Step1GraphBuild.vue"
Cohesion: 0.17
Nodes (9): createSimulation(), creatingSimulation, graphStats, handleEnterEnvSetup(), logContent, props, router, selectedOntologyItem (+1 more)

### Community 117 - "setup_signal_handlers"
Cohesion: 0.13
Nodes (3): CommandType, MaxTokensWarningFilter, setup_signal_handlers()

### Community 118 - "fetch_all_edges"
Cohesion: 0.21
Nodes (3): fetch_all_edges(), fetch_all_nodes(), _fetch_page_with_retry()

### Community 125 - "UX-REPORT – Cursor Validierung (V1)"
Cohesion: 0.29
Nodes (6): Abnahme, Berichtskopf, E2E, i18n, Methodik-Karte, UX-REPORT – Cursor Validierung (V1)

### Community 128 - "Zukunftsprognosebericht: Dynamik der Parkgebührenanpassung und die Eskalationspfade zum Bürgerentscheid"
Cohesion: 0.33
Nodes (5): Agentenverhalten undfraktionsbildende Dynamiken, Chronologie der ersten vier Wochen: Von der Reibung zur Mobilisierung, Emergente Trends und Wahrscheinlichkeit des Bürgerentscheids, Risikoprognose: Soziale Fragmentierung und wirtschaftliche Stagnation, Zukunftsprognosebericht: Dynamik der Parkgebührenanpassung und die Eskalationspfade zum Bürgerentscheid

### Community 129 - "Ausgangslage: Hallenbad Süd in Neuberg"
Cohesion: 0.40
Nodes (4): Ausgangslage: Hallenbad Süd in Neuberg, Entscheidung, Weitere Beteiligte, Wer das Hallenbad Süd heute nutzt

### Community 130 - "services/ensemble.py"
Cohesion: 0.12
Nodes (11): _agent_id(), apply_without_variant(), ensemble_markdown(), load_simulation_posts(), prepare_run_directory(), _read_twitter_csv(), _runner_status(), _table_columns() (+3 more)

### Community 132 - "emit"
Cohesion: 0.50
Nodes (4): startEnsemble(), addLog(), emit, startEnsembleRun()

### Community 138 - "UX-REPORT – Cursor Ensemble (Mehrfachlauf)"
Cohesion: 0.50
Nodes (3): Auftrag A – Mehrfachlauf, Auftrag B – Befunde, UX-REPORT – Cursor Ensemble (Mehrfachlauf)

### Community 143 - "ZepEntityReader"
Cohesion: 0.12
Nodes (4): generate_profiles(), get_entities_by_type(), FilteredEntities, ZepEntityReader

## Knowledge Gaps
- **588 isolated node(s):** `mirofish-backend`, `docker-entrypoint.sh script`, `docker-test.sh script`, `name`, `private` (+583 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1694 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **65 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Neuerungen aus dem Original (666ghj/MiroFish)` connect `LLMClient` to `OasisProfileGenerator`, `Step2EnvSetup.vue`?**
  _High betweenness centrality (0.301) - this node is a cross-community bridge._
- **Are the 40 inferred relationships involving `Config` (e.g. with `allowed_file()` and `build_graph()`) actually correct?**
  _`Config` has 40 INFERRED edges - model-reasoned connections that need verification._
- **What connects `mirofish-backend`, `docker-entrypoint.sh script`, `docker-test.sh script` to the rest of the system?**
  _588 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `interview_agent` be split into smaller, more focused modules?**
  _Cohesion score 0.12418300653594772 - nodes in this community are weakly interconnected._
- **Why does `Offene Frontend-Punkte (nicht angewendet, Umbau läuft parallel)` connect `Step2EnvSetup.vue` to `Step3Simulation.vue`, `LLMClient`?**
  _High betweenness centrality (0.301) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `error()` (e.g. with `cancel_ensemble()` and `delete_ensemble()`) actually correct?**
  _`error()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Should `Step4Report.vue` be split into smaller, more focused modules?**
  _Cohesion score 0.024691358024691357 - nodes in this community are weakly interconnected._