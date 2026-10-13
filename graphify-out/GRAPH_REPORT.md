# Graph Report - mirofish-ensemble-be  (2026-10-13)

## Corpus Check
- 143 files · ~664,332 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 7, .example 1, .lock 1)

## Summary
- 2875 nodes · 5717 edges · 150 communities (75 shown, 75 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 388 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7c02209a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- MemoryProvider
- SimulationRunner
- Step4Report.vue
- simulation.py
- Process.vue
- Step5Interaction.vue
- ProjectManager
- SimulationConfigGenerator
- EnsembleService
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
- ReportOutline
- SimulationView.vue
- run_reddit_simulation.py
- .generate_report
- services/__init__.py
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
- graph.js
- package.json
- vue
- SettingsView.vue
- .filter_defined_entities
- ZepToolsService
- retry_with_backoff_async
- OasisAgentProfile
- OntologyGenerator
- _coerce_to_str
- ZepGraphMemoryUpdater
- ObsidianMemoryProvider
- ReportConsoleLogger
- ActionLogger
- LLMClient
- ReportAgent
- ReportManager
- MiroFish E2E (Playwright)
- cleanup.py
- OasisProfileGenerator
- Config
- services/ensemble.py
- .get_all_nodes
- ThemePicker.vue
- vue-router
- Design-System: MiroFish „Editorial Clarity“
- TwitterSimulationRunner
- os
- .extract_text
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
- EntityNode
- SwarmCanvas.vue
- Design-Audit: MiroFish Web-App (Mobile First & Barrierefreiheit)
- 3. Umfassender Ansichten-Audit (View-by-View Breakdown)
- 2. Bestätigung und Tiefenanalyse der bekannten Kernmängel
- .send_command
- .search_graph
- UX-REPORT – belkis (Abschnitt 3.1A, 3.3–3.6, global)
- router/index.js
- IPCResponse
- report_validation.py
- test_profile_format.py
- run_parallel_simulation.py
- graph.py
- EdgeInfo
- mirofish-backend
- Konkrete Template-Textersetzungen:
- app/__init__.py
- Mangel 3: Leere Flächen mit einzelnen Rauten-Symbolen
- Mangel 4: Karten der „Simulationsaufzeichnungen“ am Handy links/rechts abgeschnitten
- Mangel 2: Badge „Elegante universelle Schwarm-Intelligenz-Engine“ bricht um
- Mangel 5: Im Prompt-Feld überlappt Badge „Engine: MiroFish-V1.0“ den Platzhaltertext
- Mangel 10: Fehlende Zeitschätzung und Statusführung bei langen Läufen (Minuten bis 1 Stunde)
- MemoryNode
- addLog
- sample-upload.md
- Roadmap v2 – „so gut, dass es jeder gern benutzt"
- REPORT-UI.md
- .get_all_edges
- setup_oasis_logging
- I18N-Bericht
- Step1GraphBuild.vue
- MemoryEdge
- api/ensemble.py
- .cleanup_all_simulations
- UX-REPORT-codex.md
- MemorySearchResult
- UX-REPORT – Cursor Validierung (V1)
- .plan_outline
- Zukunftsprognosebericht: Dynamik der Parkgebührenanpassung und die Eskalationspfade zum Bürgerentscheid
- Ausgangslage: Hallenbad Süd in Neuberg
- .chat_json
- setup_signal_handlers
- setup_signal_handlers
- pendingUpload.js
- szenarien/README.md
- docker-test.sh
- InsightForgeResult
- docker-entrypoint.sh
- InterviewResult
- AgentInterview
- _get_report_id_for_simulation
- run_prepare

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

## Communities (150 total, 75 thin omitted)

### Community 1 - "SimulationRunner"
Cohesion: 0.09
Nodes (8): get_env_status(), get_run_status(), get_run_status_detail(), interview_agent(), interview_agents_batch(), interview_all_agents(), optimize_interview_prompt(), SimulationRunner

### Community 2 - "Step4Report.vue"
Cohesion: 0.03
Nodes (42): activeSectionIndex, activeStep, activeTocIndex, agentLogLine, agentLogs, agentTypesLabel, collapsedSections, completedSections (+34 more)

### Community 3 - "simulation.py"
Cohesion: 0.04
Nodes (31): _check_simulation_prepared(), close_simulation_env(), create_simulation(), download_simulation_config(), download_simulation_script(), generate_profiles(), get_agent_stats(), _get_default_platform() (+23 more)

### Community 4 - "Process.vue"
Cohesion: 0.07
Nodes (36): getProject(), buildProgress, closeDetailPanel(), currentPhase, currentProjectId, entityTypes, error, fetchGraphData() (+28 more)

### Community 5 - "Step5Interaction.vue"
Cohesion: 0.05
Nodes (28): getSimulationProfilesRealtime(), activeTab, chatHistory, chatHistoryCache, chatInput, chatInputRef, chatMessages, chatTarget (+20 more)

### Community 7 - "ProjectManager"
Cohesion: 0.07
Nodes (9): allowed_file(), delete_project(), generate_ontology(), get_project(), list_projects(), reset_project(), chat_with_report_agent(), Project (+1 more)

### Community 8 - "SimulationConfigGenerator"
Cohesion: 0.08
Nodes (3): EventConfig, SimulationConfigGenerator, SimulationParameters

### Community 9 - "EnsembleService"
Cohesion: 0.10
Nodes (20): _agent_id(), ensemble_markdown(), EnsembleService, load_simulation_posts(), parse_checklist(), prepare_run_directory(), _read_json(), _read_twitter_csv() (+12 more)

### Community 10 - "system.py"
Cohesion: 0.14
Nodes (7): list_models(), mask_key(), _ollama_root(), save_config(), system_models(), system_status(), test_llm()

### Community 11 - "Step3Simulation.vue"
Cohesion: 0.07
Nodes (38): getRunStatus(), getRunStatusDetail(), startSimulation(), stopSimulation(), actionIds, addLog(), allActions, checkPlatformsCompleted() (+30 more)

### Community 12 - "mockApi.ts"
Cohesion: 0.06
Nodes (52): devDependencies, @axe-core/playwright, @playwright/test, typescript, name, private, scripts, test (+44 more)

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
Cohesion: 0.08
Nodes (31): closeSimulationEnv(), getEnvStatus(), getSimulationConfig(), addLog(), currentSimulationId, currentStatus, graphData, graphLoading (+23 more)

### Community 18 - "run_reddit_simulation"
Cohesion: 0.08
Nodes (7): PlatformActionLogger, create_model(), get_active_agents_for_round(), get_agent_names_from_config(), PlatformSimulation, run_reddit_simulation(), run_twitter_simulation()

### Community 23 - "SimulationView.vue"
Cohesion: 0.10
Nodes (26): getSimulation(), addLog(), checkAndStopRunningSimulation(), currentSimulationId, currentStatus, forceStopSimulation(), graphData, graphLoading (+18 more)

### Community 24 - "run_reddit_simulation.py"
Cohesion: 0.08
Nodes (11): apply_python_seeds(), build_model_config_dict(), resolve_seed_and_temperature(), CommandType, main(), MaxTokensWarningFilter, setup_oasis_logging(), UnicodeFormatter (+3 more)

### Community 26 - "services/__init__.py"
Cohesion: 0.13
Nodes (7): AgentActivityConfig, PlatformConfig, TimeSimulationConfig, CommandStatus, CommandType, RunnerStatus, ZepGraphMemoryManager

### Community 27 - "HistoryDatabase.vue"
Cohesion: 0.08
Nodes (17): deleteSimulation(), closeModal(), confirmDelete(), containerStyle, goToProject(), goToReport(), goToSimulation(), historyContainer (+9 more)

### Community 29 - "Home.vue"
Cohesion: 0.08
Nodes (24): startPipeline(), getSimulationHistory(), activeRuns, add(), autopilot, canSubmit, error, fileInput (+16 more)

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

### Community 42 - "vue"
Cohesion: 0.10
Nodes (24): deletePipeline(), listPipelines(), route, showTheme, { t }, { t }, activeCount, poll() (+16 more)

### Community 43 - "SettingsView.vue"
Cohesion: 0.11
Nodes (16): baseUrl(), cfg, load(), masked, memoryLabel, models, result, save() (+8 more)

### Community 46 - "retry_with_backoff_async"
Cohesion: 0.15
Nodes (6): retry_with_backoff(), retry_with_backoff_async(), decorator(), decorator(), wrapper(), RetryableAPIClient

### Community 48 - "OntologyGenerator"
Cohesion: 0.06
Nodes (11): _coerce_to_str_list(), _ascii_fold(), OntologyGenerator, resolve_entity_name(), _to_pascal_case(), _to_upper_snake_case(), normalize_ontology_attribute(), normalize_ontology_attributes() (+3 more)

### Community 54 - "LLMClient"
Cohesion: 0.09
Nodes (8): FileParser, split_text_into_chunks(), _clean_chat_text(), _contains_additional_json_container(), LLMClient, create_chat_completion(), extract_chat_completion_text(), is_gpt5_family()

### Community 56 - "ReportManager"
Cohesion: 0.03
Nodes (19): check_report_status(), delete_report(), download_report(), generate_report(), get_agent_log(), get_console_log(), get_generate_status(), get_graph_statistics_tool() (+11 more)

### Community 57 - "MiroFish E2E (Playwright)"
Cohesion: 0.13
Nodes (13): frontend(), 1. Fußmenü verdeckt Bedienelemente (Handy), 2. Barrierefreiheit (axe serious/critical), 3. iPhone (WebKit): seitliche Scrollleiste, Bekannte Befunde (E2E), Nicht als App-Bug gewertet (Tests angepasst), Bekannte App-Fehler, CI (+5 more)

### Community 58 - "cleanup.py"
Cohesion: 0.06
Nodes (53): delete_pipeline(), mark_stale_runs(), delete_simulation(), _child(), CleanupBusy, CleanupError, delete_failed_pipelines(), _delete_graph_storage() (+45 more)

### Community 60 - "Config"
Cohesion: 0.09
Nodes (8): Config, MemoryFactory, PlatformType, ZepEntityReader, get_logger(), fetch_all_edges(), fetch_all_nodes(), _fetch_page_with_retry()

### Community 61 - "services/ensemble.py"
Cohesion: 0.11
Nodes (9): apply_without_variant(), newcombe_difference_interval(), wilson_interval(), _stub(), FakeLLM, FakeRunner, test_newcombe_method_10_known_value(), test_wilson_known_value() (+1 more)

### Community 63 - "ThemePicker.vue"
Cohesion: 0.08
Nodes (44): Grenzen von V3/V4, Prüfung, Rechenzeit und Betrieb, Statistik, V3: Mehrfachlauf, V4: Gegenproben, Validierung V1/V2, Validierung V1–V4 (+36 more)

### Community 64 - "vue-router"
Cohesion: 0.09
Nodes (22): dependencies, axios, d3, vue, vue-i18n, vue-router, devDependencies, vite (+14 more)

### Community 65 - "Design-System: MiroFish „Editorial Clarity“"
Cohesion: 0.08
Nodes (24): 1. Design-Richtung & Philosophie, 2. Typografie, 3.1 Helles Design (Light Mode - Standard), 3.2 Dunkles Design (Dark Mode - `[data-theme="dark"]`), 3. Farbpalette & Nachgerechnete WCAG-AA-Kontraste, 4. Abstands- und Rastersystem, 5.1 Buttons (Schaltflächen), 5.2 Karten (Cards) (+16 more)

### Community 67 - "os"
Cohesion: 0.17
Nodes (11): _base(), _dir(), _load(), _ok(), _path(), pipeline_list(), pipeline_status(), _run() (+3 more)

### Community 70 - "Änderungen"
Cohesion: 0.29
Nodes (6): Abnahme, `GraphPanel.vue`, i18n (`de.json` / `en.json`), `Step1GraphBuild.vue`, UX-Report: Wissensgraph & Schritt 1 (Feinschliff), Änderungen

### Community 71 - "getReport"
Cohesion: 0.20
Nodes (10): getAgentLog(), getConsoleLog(), getReport(), addLog(), emit, fetchAgentLog(), fetchConsoleLog(), loadMethodology() (+2 more)

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

### Community 89 - "UX-REPORT – belkis (Abschnitt 3.1A, 3.3–3.6, global)"
Cohesion: 0.40
Nodes (4): Abnahme, Nicht angefasst, UX-REPORT – belkis (Abschnitt 3.1A, 3.3–3.6, global), Änderungen

### Community 90 - "router/index.js"
Cohesion: 0.20
Nodes (4): savedLanguage, app, router, routes

### Community 92 - "report_validation.py"
Cohesion: 0.06
Nodes (44): export_simulation(), mark_checklist_material(), append_methodology_to_markdown(), apply_python_seeds(), best_content_match(), build_manifest(), build_methodology(), build_model_config_dict() (+36 more)

### Community 94 - "run_parallel_simulation.py"
Cohesion: 0.08
Nodes (11): CommandType, disable_oasis_logging(), _enrich_action_context(), fetch_new_actions_from_db(), _get_comment_info(), _get_post_info(), _get_user_name(), init_logging_for_simulation() (+3 more)

### Community 95 - "graph.py"
Cohesion: 0.04
Nodes (14): build_graph(), build_task(), delete_graph(), get_graph_data(), get_task(), list_tasks(), ProjectStatus, Task (+6 more)

### Community 98 - "Konkrete Template-Textersetzungen:"
Cohesion: 0.50
Nodes (4): 1. In `Home.vue`:, 2. In `Step1GraphBuild.vue`:, Konkrete Template-Textersetzungen:, Mangel 7: Fachjargon in Nutzertexten

### Community 99 - "app/__init__.py"
Cohesion: 0.12
Nodes (9): mark_stale_ensembles(), create_app(), log_request(), log_response(), require_api_token(), token_ok(), _ensure_utf8_stdout(), setup_logger() (+1 more)

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

### Community 106 - "addLog"
Cohesion: 0.22
Nodes (13): interviewAgents(), addLog(), emit, loadAgentLogs(), loadReportData(), saveChatHistory(), scrollToBottom(), selectAgent() (+5 more)

### Community 114 - "I18N-Bericht"
Cohesion: 0.33
Nodes (5): Bewusst nicht übersetzte Stellen, I18N-Bericht, Offene Punkte, Prüfung, Umfang

### Community 115 - "Step1GraphBuild.vue"
Cohesion: 0.17
Nodes (9): createSimulation(), creatingSimulation, graphStats, handleEnterEnvSetup(), logContent, props, router, selectedOntologyItem (+1 more)

### Community 119 - "api/ensemble.py"
Cohesion: 0.44
Nodes (6): cancel_ensemble(), delete_ensemble(), _error(), get_ensemble(), list_ensembles(), start_ensemble()

### Community 125 - "UX-REPORT – Cursor Validierung (V1)"
Cohesion: 0.29
Nodes (6): Abnahme, Berichtskopf, E2E, i18n, Methodik-Karte, UX-REPORT – Cursor Validierung (V1)

### Community 128 - "Zukunftsprognosebericht: Dynamik der Parkgebührenanpassung und die Eskalationspfade zum Bürgerentscheid"
Cohesion: 0.33
Nodes (5): Agentenverhalten undfraktionsbildende Dynamiken, Chronologie der ersten vier Wochen: Von der Reibung zur Mobilisierung, Emergente Trends und Wahrscheinlichkeit des Bürgerentscheids, Risikoprognose: Soziale Fragmentierung und wirtschaftliche Stagnation, Zukunftsprognosebericht: Dynamik der Parkgebührenanpassung und die Eskalationspfade zum Bürgerentscheid

### Community 129 - "Ausgangslage: Hallenbad Süd in Neuberg"
Cohesion: 0.40
Nodes (4): Ausgangslage: Hallenbad Süd in Neuberg, Entscheidung, Weitere Beteiligte, Wer das Hallenbad Süd heute nutzt

### Community 130 - ".chat_json"
Cohesion: 0.12
Nodes (3): _is_response_format_unsupported(), LLMResponseError, Prüfung

### Community 135 - "pendingUpload.js"
Cohesion: 0.33
Nodes (5): clearPendingUpload(), getPendingUpload(), state, handleNewProject(), initProject()

## Knowledge Gaps
- **555 isolated node(s):** `mirofish-backend`, `docker-entrypoint.sh script`, `docker-test.sh script`, `name`, `private` (+550 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1539 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **75 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Neuerungen aus dem Original (666ghj/MiroFish)` connect `OntologyGenerator` to `.chat_json`, `Step2EnvSetup.vue`?**
  _High betweenness centrality (0.303) - this node is a cross-community bridge._
- **Are the 40 inferred relationships involving `Config` (e.g. with `allowed_file()` and `build_graph()`) actually correct?**
  _`Config` has 40 INFERRED edges - model-reasoned connections that need verification._
- **What connects `mirofish-backend`, `docker-entrypoint.sh script`, `docker-test.sh script` to the rest of the system?**
  _555 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `MemoryProvider` be split into smaller, more focused modules?**
  _Cohesion score 0.10276679841897234 - nodes in this community are weakly interconnected._
- **Why does `Offene Frontend-Punkte (nicht angewendet, Umbau läuft parallel)` connect `Step2EnvSetup.vue` to `OntologyGenerator`, `Step3Simulation.vue`?**
  _High betweenness centrality (0.300) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `error()` (e.g. with `cancel_ensemble()` and `delete_ensemble()`) actually correct?**
  _`error()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Should `SimulationRunner` be split into smaller, more focused modules?**
  _Cohesion score 0.09113300492610837 - nodes in this community are weakly interconnected._