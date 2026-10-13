# Graph Report - MiroFish-DE  (2026-10-13)

## Corpus Check
- 122 files · ~481,755 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: (none) 6, .example 1, .lock 1)

## Summary
- 2470 nodes · 4934 edges · 124 communities (69 shown, 55 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 367 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `dd889495`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- logger.py
- SimulationRunner
- Step4Report.vue
- simulation.py
- Process.vue
- Step5Interaction.vue
- .extract_text
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
- ReportManager
- SimulationView.vue
- run_parallel_simulation.py
- ReportAgent
- os
- HistoryDatabase.vue
- interview_agent
- Home.vue
- ReportView.vue
- .generate_report
- 3. Detaillierte Spezifikation nach Seiten und Komponenten
- vue
- InteractionView.vue
- MemoryProvider
- AgentActivity
- ParallelIPCHandler
- SimulationLogManager
- getProject
- package.json
- create_app
- SettingsView.vue
- FilteredEntities
- .interview_agents
- retry.py
- LLMClient
- MobileNav.vue
- ZepGraphMemoryUpdater
- ZepMemoryProvider
- ReportConsoleLogger
- ActionLogger
- ObsidianMemoryProvider
- LLMResponseError
- .search_graph
- MiroFish E2E (Playwright)
- cleanup.py
- OasisProfileGenerator
- services/__init__.py
- EdgeInfo
- NodeInfo
- ThemePicker.vue
- ReportOutline
- Design-System: MiroFish „Editorial Clarity“
- HistoryView.vue
- TextProcessor
- ZepToolsService
- init_logging_for_simulation
- getAgentLog
- MemoryNode
- MemoryEdge
- compilerOptions
- RunView.vue
- GraphPanel.vue
- theme.js
- IPCResponse
- Konkrete Mobile- & Template-Fixes (Mobile First 412 px)
- Übersicht
- SwarmCanvas.vue
- MemorySearchResult
- Design-Audit: MiroFish Web-App (Mobile First & Barrierefreiheit)
- 3. Umfassender Ansichten-Audit (View-by-View Breakdown)
- 2. Bestätigung und Tiefenanalyse der bekannten Kernmängel
- SimulationParameters
- AgentActivityConfig
- system_status
- .panorama_search
- conftest.py
- test_profile_format.py
- _enrich_action_context
- ._set_zep_ontology
- InsightForgeResult
- mirofish-backend
- Konkrete Template-Textersetzungen:
- Mangel 3: Leere Flächen mit einzelnen Rauten-Symbolen
- Mangel 4: Karten der „Simulationsaufzeichnungen“ am Handy links/rechts abgeschnitten
- Mangel 2: Badge „Elegante universelle Schwarm-Intelligenz-Engine“ bricht um
- Mangel 5: Im Prompt-Feld überlappt Badge „Engine: MiroFish-V1.0“ den Platzhaltertext
- Mangel 10: Fehlende Zeitschätzung und Statusführung bei langen Läufen (Minuten bis 1 Stunde)
- MaxTokensWarningFilter
- sample-upload.md
- ._validate_and_process
- ROADMAP.md
- .cleanup_all_simulations
- REPORT-UI.md
- setup_oasis_logging
- setup_oasis_logging
- I18N-Bericht
- simulation.js
- InterviewResult
- MaxTokensWarningFilter
- setup_signal_handlers
- setup_signal_handlers
- router/index.js
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

## Communities (124 total, 55 thin omitted)

### Community 0 - "logger.py"
Cohesion: 0.07
Nodes (12): MemoryFactory, PlatformType, _ensure_utf8_stdout(), get_logger(), setup_logger(), warning(), create_chat_completion(), extract_chat_completion_text() (+4 more)

### Community 1 - "SimulationRunner"
Cohesion: 0.09
Nodes (4): get_run_status_detail(), AgentAction, SimulationRunner, SimulationRunState

### Community 2 - "Step4Report.vue"
Cohesion: 0.03
Nodes (39): activeSectionIndex, activeStep, activeTocIndex, agentLogLine, agentLogs, collapsedSections, completedSections, consoleLogLine (+31 more)

### Community 3 - "simulation.py"
Cohesion: 0.04
Nodes (46): chat_with_report_agent(), delete_report(), download_report(), get_agent_log(), get_console_log(), get_graph_statistics_tool(), get_report(), get_report_progress() (+38 more)

### Community 4 - "Process.vue"
Cohesion: 0.07
Nodes (38): clearPendingUpload(), buildProgress, closeDetailPanel(), currentPhase, currentProjectId, entityTypes, error, fetchGraphData() (+30 more)

### Community 5 - "Step5Interaction.vue"
Cohesion: 0.05
Nodes (41): getSimulationProfilesRealtime(), interviewAgents(), activeTab, addLog(), chatHistory, chatHistoryCache, chatInput, chatInputRef (+33 more)

### Community 7 - "ProjectManager"
Cohesion: 0.08
Nodes (7): delete_project(), generate_ontology(), reset_project(), Project, ProjectManager, ProjectStatus, debug()

### Community 8 - "SimulationConfigGenerator"
Cohesion: 0.09
Nodes (4): PlatformConfig, SimulationConfigGenerator, TimeSimulationConfig, EntityNode

### Community 10 - "Config"
Cohesion: 0.04
Nodes (17): allowed_file(), build_graph(), delete_graph(), get_graph_data(), get_project(), get_task(), list_projects(), list_tasks() (+9 more)

### Community 11 - "Step3Simulation.vue"
Cohesion: 0.08
Nodes (36): getRunStatus(), getRunStatusDetail(), startSimulation(), actionIds, addLog(), allActions, checkPlatformsCompleted(), chronologicalActions (+28 more)

### Community 12 - "mockApi.ts"
Cohesion: 0.06
Nodes (48): devDependencies, @axe-core/playwright, @playwright/test, typescript, name, private, scripts, test (+40 more)

### Community 13 - "Step2EnvSetup.vue"
Cohesion: 0.08
Nodes (43): Offene Frontend-Punkte (nicht angewendet, Umbau läuft parallel), Ausgelassen, Checks, Geändert, npm audit (`cd frontend && npm audit --omit=dev`), Offen, Polish-Report, getPrepareStatus() (+35 more)

### Community 14 - "MainView.vue"
Cohesion: 0.09
Nodes (37): getPendingUpload(), addLog(), buildProgress, currentPhase, currentProjectId, currentStep, error, fetchGraphData() (+29 more)

### Community 15 - "README-EN.md"
Cohesion: 0.05
Nodes (40): Der eine Aufruf, der alles macht, Einzelne Stufen (wenn du selbst steuern willst), Ergebnisse abholen, MiroFish API (für Skripte, Agenten und eigene Oberflächen), Python-Beispiel, 1. Ollama und Modelle, 2a. Start mit Docker (empfohlen), 2b. Start aus dem Quellcode (+32 more)

### Community 16 - "SimulationRunView.vue"
Cohesion: 0.09
Nodes (28): getSimulation(), getSimulationConfig(), addLog(), currentSimulationId, currentStatus, graphData, graphLoading, handleGoBack() (+20 more)

### Community 18 - "run_reddit_simulation"
Cohesion: 0.10
Nodes (7): PlatformActionLogger, create_model(), get_active_agents_for_round(), get_agent_names_from_config(), PlatformSimulation, run_reddit_simulation(), run_twitter_simulation()

### Community 19 - "IPCHandler"
Cohesion: 0.09
Nodes (3): IPCHandler, main(), RedditSimulationRunner

### Community 20 - "IPCHandler"
Cohesion: 0.09
Nodes (3): IPCHandler, main(), TwitterSimulationRunner

### Community 22 - "ReportManager"
Cohesion: 0.10
Nodes (6): check_report_status(), get_report_by_simulation(), get_report_sections(), list_reports(), ReportManager, ReportStatus

### Community 23 - "SimulationView.vue"
Cohesion: 0.10
Nodes (25): closeSimulationEnv(), getEnvStatus(), stopSimulation(), addLog(), checkAndStopRunningSimulation(), currentSimulationId, currentStatus, forceStopSimulation() (+17 more)

### Community 24 - "run_parallel_simulation.py"
Cohesion: 0.13
Nodes (4): CommandType, _utf8_open(), CommandType, CommandType

### Community 26 - "os"
Cohesion: 0.11
Nodes (16): _base(), _dir(), _load(), mark_stale_runs(), _ok(), _path(), pipeline_list(), pipeline_status() (+8 more)

### Community 27 - "HistoryDatabase.vue"
Cohesion: 0.08
Nodes (14): closeModal(), containerStyle, goToProject(), goToReport(), goToSimulation(), historyContainer, hoveringCard, isExpanded (+6 more)

### Community 28 - "interview_agent"
Cohesion: 0.16
Nodes (5): get_env_status(), interview_agent(), interview_agents_batch(), interview_all_agents(), optimize_interview_prompt()

### Community 29 - "Home.vue"
Cohesion: 0.09
Nodes (22): startPipeline(), activeRuns, add(), autopilot, canSubmit, error, fileInput, files (+14 more)

### Community 30 - "ReportView.vue"
Cohesion: 0.08
Nodes (23): { t }, { locale, t }, addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle (+15 more)

### Community 32 - "3. Detaillierte Spezifikation nach Seiten und Komponenten"
Cohesion: 0.06
Nodes (33): 1. Barrierefreiheit (e2e-Befund), 1. Gemeinsame Header-Architektur am Smartphone, 1. Kurzurteil, 1. Mobil-Verhalten, 1. Mobil-Verhalten (`04-durchlauf-mobil.png`), 1. Mobil-Verhalten (Samsung S23 Ultra, 412 px), 1. Problemstellung & IST-Zustand (Screenshots 10 & 11), 2. Befundtabelle (+25 more)

### Community 33 - "vue"
Cohesion: 0.07
Nodes (27): dependencies, axios, d3, vue, vue-i18n, vue-router, devDependencies, vite (+19 more)

### Community 34 - "InteractionView.vue"
Cohesion: 0.10
Nodes (21): getReport(), addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph() (+13 more)

### Community 39 - "SimulationLogManager"
Cohesion: 0.13
Nodes (3): SimulationLogManager, load_config(), main()

### Community 40 - "getProject"
Cohesion: 0.32
Nodes (9): buildGraph(), generateOntology(), getGraphData(), getProject(), getTaskStatus(), requestWithRetry(), service, chatWithReport() (+1 more)

### Community 41 - "package.json"
Cohesion: 0.11
Nodes (17): description, devDependencies, concurrently, engines, node, license, name, scripts (+9 more)

### Community 42 - "create_app"
Cohesion: 0.33
Nodes (5): create_app(), log_request(), log_response(), require_api_token(), token_ok()

### Community 43 - "SettingsView.vue"
Cohesion: 0.11
Nodes (16): baseUrl(), cfg, load(), masked, memoryLabel, models, result, save() (+8 more)

### Community 46 - "retry.py"
Cohesion: 0.13
Nodes (6): retry_with_backoff(), retry_with_backoff_async(), decorator(), decorator(), wrapper(), RetryableAPIClient

### Community 49 - "MobileNav.vue"
Cohesion: 0.29
Nodes (6): listPipelines(), activeCount, poll(), route, { t }, loadRuns()

### Community 55 - "LLMResponseError"
Cohesion: 0.10
Nodes (6): test_llm(), _clean_chat_text(), _is_response_format_unsupported(), LLMResponseError, Neuerungen aus dem Original (666ghj/MiroFish), Prüfung

### Community 57 - "MiroFish E2E (Playwright)"
Cohesion: 0.14
Nodes (12): frontend(), 1. Fußmenü verdeckt Bedienelemente (Handy), 2. Barrierefreiheit (axe serious/critical), Bekannte Befunde (E2E), Nicht als App-Bug gewertet (Tests angepasst), Bekannte App-Fehler, CI, Live gegen eine laufende Instanz (+4 more)

### Community 58 - "cleanup.py"
Cohesion: 0.06
Nodes (49): delete_pipeline(), delete_simulation(), _child(), CleanupBusy, CleanupError, _delete_graph_storage(), delete_pipeline_cascade(), _delete_pipelines_for_simulation() (+41 more)

### Community 59 - "OasisProfileGenerator"
Cohesion: 0.09
Nodes (3): OasisAgentProfile, OasisProfileGenerator, generate_single_profile()

### Community 60 - "services/__init__.py"
Cohesion: 0.14
Nodes (5): CommandStatus, CommandType, IPCCommand, RoundSummary, RunnerStatus

### Community 63 - "ThemePicker.vue"
Cohesion: 0.13
Nodes (21): busy, choose(), chooseOwn(), current, error, input, isDefault, ownColor (+13 more)

### Community 65 - "Design-System: MiroFish „Editorial Clarity“"
Cohesion: 0.08
Nodes (24): 1. Design-Richtung & Philosophie, 2. Typografie, 3.1 Helles Design (Light Mode - Standard), 3.2 Dunkles Design (Dark Mode - `[data-theme="dark"]`), 3. Farbpalette & Nachgerechnete WCAG-AA-Kontraste, 4. Abstands- und Rastersystem, 5.1 Buttons (Schaltflächen), 5.2 Karten (Cards) (+16 more)

### Community 66 - "HistoryView.vue"
Cohesion: 0.15
Nodes (17): deletePipeline(), deleteSimulation(), getSimulationHistory(), confirmDelete(), loadHistory(), deleting, doDelete(), error (+9 more)

### Community 68 - "TextProcessor"
Cohesion: 0.14
Nodes (4): build_task(), TextProcessor, FileParser, split_text_into_chunks()

### Community 71 - "getAgentLog"
Cohesion: 0.25
Nodes (8): getAgentLog(), getConsoleLog(), addLog(), emit, fetchAgentLog(), fetchConsoleLog(), startPolling(), stopPolling()

### Community 74 - "compilerOptions"
Cohesion: 0.17
Nodes (11): compilerOptions, esModuleInterop, module, moduleResolution, noEmit, resolveJsonModule, skipLibCheck, strict (+3 more)

### Community 75 - "RunView.vue"
Cohesion: 0.12
Nodes (15): getPipeline(), STEP_LABELS, STEP_ORDER, cleanedUp, currentDetail, currentLabel, etaText, HINTS (+7 more)

### Community 76 - "GraphPanel.vue"
Cohesion: 0.12
Nodes (13): emit, entityTypes, expandedSelfLoops, graphContainer, graphSvg, handleResize(), props, renderGraph() (+5 more)

### Community 77 - "theme.js"
Cohesion: 0.42
Nodes (11): applyTheme(), contrast(), deriveVars(), ensureContrast(), hexToRgb(), lin(), luminance(), mix() (+3 more)

### Community 79 - "Konkrete Mobile- & Template-Fixes (Mobile First 412 px)"
Cohesion: 0.13
Nodes (15): CSS-Fix (`Home.vue` `<style scoped>`):, CSS-Fix in `Home.vue`:, CSS-Fix in `tokens.css` (wird automatisch wirksam) bzw. `App.vue`:, CSS-Fix (`MainView.vue` `<style scoped>`):, CSS-Fix (`MainView.vue` `<style scoped>`):, Globaler CSS-Klassen-Fix (Drop-in):, Konkrete Mobile- & Template-Fixes (Mobile First 412 px), Mangel 11: Touch-Targets unter 44 px (Löschen-Button, Switcher) (+7 more)

### Community 80 - "Übersicht"
Cohesion: 0.14
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

### Community 90 - "system_status"
Cohesion: 0.11
Nodes (6): list_models(), mask_key(), _ollama_root(), save_config(), system_models(), system_status()

### Community 94 - "_enrich_action_context"
Cohesion: 0.20
Nodes (5): _enrich_action_context(), fetch_new_actions_from_db(), _get_comment_info(), _get_post_info(), _get_user_name()

### Community 95 - "._set_zep_ontology"
Cohesion: 0.14
Nodes (3): normalize_ontology_attribute(), normalize_ontology_attributes(), normalize_ontology_source_targets()

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

### Community 108 - "._validate_and_process"
Cohesion: 0.18
Nodes (3): _ascii_fold(), resolve_entity_name(), _to_pascal_case()

### Community 114 - "I18N-Bericht"
Cohesion: 0.33
Nodes (5): Bewusst nicht übersetzte Stellen, I18N-Bericht, Offene Punkte, Prüfung, Umfang

### Community 115 - "simulation.js"
Cohesion: 0.11
Nodes (10): createSimulation(), prepareSimulation(), creatingSimulation, graphStats, handleEnterEnvSetup(), logContent, props, router (+2 more)

### Community 128 - "router/index.js"
Cohesion: 0.18
Nodes (6): savedLanguage, app, router, routes, isValidHex(), loadTheme()

## Knowledge Gaps
- **501 isolated node(s):** `mirofish-backend`, `docker-entrypoint.sh script`, `name`, `private`, `version` (+496 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1291 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **55 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Neuerungen aus dem Original (666ghj/MiroFish)` connect `LLMResponseError` to `Übersicht`, `Step2EnvSetup.vue`?**
  _High betweenness centrality (0.298) - this node is a cross-community bridge._
- **Are the 33 inferred relationships involving `Config` (e.g. with `allowed_file()` and `build_graph()`) actually correct?**
  _`Config` has 33 INFERRED edges - model-reasoned connections that need verification._
- **What connects `mirofish-backend`, `docker-entrypoint.sh script`, `name` to the rest of the system?**
  _501 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `logger.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06698564593301436 - nodes in this community are weakly interconnected._
- **Why does `Offene Frontend-Punkte (nicht angewendet, Umbau läuft parallel)` connect `Step2EnvSetup.vue` to `Step3Simulation.vue`, `LLMResponseError`?**
  _High betweenness centrality (0.298) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `error()` (e.g. with `generate_ontology()` and `.chat_json()`) actually correct?**
  _`error()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `SimulationRunner` be split into smaller, more focused modules?**
  _Cohesion score 0.09176788124156546 - nodes in this community are weakly interconnected._