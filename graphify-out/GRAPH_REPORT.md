# Graph Report - MiroFish-DE  (2026-10-13)

## Corpus Check
- 68 files · ~373,278 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 5, .example 1, .lock 1)

## Summary
- 1890 nodes · 3778 edges · 98 communities (47 shown, 51 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 301 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8f560505`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- simulation_runner.py
- SimulationRunner
- Step4Report.vue
- simulation.py
- Process.vue
- Step5Interaction.vue
- services/__init__.py
- ProjectManager
- SimulationConfigGenerator
- SimulationManager
- TaskManager
- Step3Simulation.vue
- Config
- Step2EnvSetup.vue
- MainView.vue
- README-EN.md
- SimulationView.vue
- ReportLogger
- run_reddit_simulation
- IPCHandler
- IPCHandler
- IPCResponse
- report.py
- SimulationRunView.vue
- run_parallel_simulation.py
- ReportAgent
- FileParser
- HistoryDatabase.vue
- SimulationIPCClient
- Home.vue
- ReportView.vue
- ReportManager
- OasisProfileGenerator
- frontend/package.json
- InteractionView.vue
- MemoryProvider
- ._get_report_folder
- AgentActivity
- ParallelIPCHandler
- SimulationLogManager
- vue
- package.json
- prepare_simulation
- ObsidianMemoryProvider
- ZepEntityReader
- Any
- retry_with_backoff_async
- GraphPanel.vue
- LLMClient
- ZepMemoryProvider
- ZepGraphMemoryUpdater
- MemoryNode
- ReportConsoleLogger
- ActionLogger
- getGraphData
- .generate_profile_from_entity
- .search_graph
- MemoryEdge
- OasisAgentProfile
- ReportOutline
- EdgeInfo
- .get_all_nodes
- ZepToolsService
- MemorySearchResult
- get_console_log
- .panorama_search
- _enrich_action_context
- getAgentLog
- SimulationParameters
- AgentInterview
- setup_oasis_logging
- setup_oasis_logging
- InsightForgeResult
- get_single_section
- init_logging_for_simulation
- closeModal
- MaxTokensWarningFilter
- setup_signal_handlers
- MaxTokensWarningFilter
- setup_signal_handlers
- MaxTokensWarningFilter
- setup_signal_handlers
- fetchStatus
- mirofish-backend

## God Nodes (most connected - your core abstractions)
1. `Config` - 52 edges
2. `error()` - 52 edges
3. `SimulationRunner` - 50 edges
4. `ReportManager` - 46 edges
5. `OasisProfileGenerator` - 34 edges
6. `ProjectManager` - 33 edges
7. `SimulationManager` - 32 edges
8. `ZepToolsService` - 30 edges
9. `ObsidianMemoryProvider` - 28 edges
10. `get_logger()` - 28 edges

## Surprising Connections (you probably didn't know these)
- `create_app()` --uses--> `SimulationRunner`  [INFERRED]
  backend/app/__init__.py → backend/app/services/simulation_runner.py
- `log_request()` --calls--> `get_logger()`  [EXTRACTED]
  backend/app/__init__.py → backend/app/utils/logger.py
- `log_response()` --calls--> `get_logger()`  [EXTRACTED]
  backend/app/__init__.py → backend/app/utils/logger.py
- `reset_project()` --uses--> `ProjectStatus`  [INFERRED]
  backend/app/api/graph.py → backend/app/models/project.py
- `generate_ontology()` --uses--> `ProjectStatus`  [INFERRED]
  backend/app/api/graph.py → backend/app/models/project.py

## Import Cycles
- None detected.

## Communities (98 total, 51 thin omitted)

### Community 0 - "simulation_runner.py"
Cohesion: 0.09
Nodes (4): get_logger(), fetch_all_edges(), fetch_all_nodes(), _fetch_page_with_retry()

### Community 1 - "SimulationRunner"
Cohesion: 0.06
Nodes (5): start_simulation(), AgentAction, SimulationRunner, cleanup_handler(), SimulationRunState

### Community 2 - "Step4Report.vue"
Cohesion: 0.03
Nodes (37): activeSectionIndex, activeStep, agentLogLine, agentLogs, collapsedSections, completedSections, consoleLogLine, consoleLogs (+29 more)

### Community 3 - "simulation.py"
Cohesion: 0.08
Nodes (26): get_graph_statistics_tool(), search_graph_tool(), create_simulation(), download_simulation_config(), download_simulation_script(), generate_profiles(), get_agent_stats(), get_entities_by_type() (+18 more)

### Community 4 - "Process.vue"
Cohesion: 0.06
Nodes (41): getProject(), clearPendingUpload(), getPendingUpload(), state, startSimulation(), buildProgress, closeDetailPanel(), currentPhase (+33 more)

### Community 5 - "Step5Interaction.vue"
Cohesion: 0.05
Nodes (40): getSimulationProfilesRealtime(), interviewAgents(), activeTab, addLog(), chatHistory, chatHistoryCache, chatInput, chatInputRef (+32 more)

### Community 6 - "services/__init__.py"
Cohesion: 0.06
Nodes (11): delete_graph(), get_graph_data(), ProjectStatus, TaskStatus, GraphBuilderService, MemoryFactory, RoundSummary, RunnerStatus (+3 more)

### Community 7 - "ProjectManager"
Cohesion: 0.07
Nodes (8): delete_project(), generate_ontology(), get_project(), list_projects(), reset_project(), chat_with_report_agent(), Project, ProjectManager

### Community 8 - "SimulationConfigGenerator"
Cohesion: 0.07
Nodes (6): AgentActivityConfig, EventConfig, PlatformConfig, SimulationConfigGenerator, TimeSimulationConfig, EntityNode

### Community 9 - "SimulationManager"
Cohesion: 0.08
Nodes (8): close_simulation_env(), get_simulation(), get_simulation_history(), stop_simulation(), PlatformType, SimulationManager, SimulationState, SimulationStatus

### Community 10 - "TaskManager"
Cohesion: 0.06
Nodes (5): get_task(), list_tasks(), Task, TaskManager, GraphInfo

### Community 11 - "Step3Simulation.vue"
Cohesion: 0.08
Nodes (35): getRunStatus(), getRunStatusDetail(), startSimulation(), actionIds, addLog(), allActions, checkPlatformsCompleted(), chronologicalActions (+27 more)

### Community 12 - "Config"
Cohesion: 0.08
Nodes (11): allowed_file(), mask_key(), save_config(), system_status(), Config, create_app(), log_request(), log_response() (+3 more)

### Community 13 - "Step2EnvSetup.vue"
Cohesion: 0.09
Nodes (35): getPrepareStatus(), getSimulationConfigRealtime(), prepareSimulation(), addLog(), autoGeneratedRounds, currentStage, customMaxRounds, displayProfiles (+27 more)

### Community 14 - "MainView.vue"
Cohesion: 0.10
Nodes (35): addLog(), buildProgress, currentPhase, currentProjectId, currentStep, error, fetchGraphData(), graphData (+27 more)

### Community 15 - "README-EN.md"
Cohesion: 0.05
Nodes (35): 1. Umgebungsvariablen konfigurieren, 2. Abhängigkeiten installieren, 3. Dienste starten, 📄 Danksagung, 1. Configure Environment Variables, 1. Wuhan University Public Opinion Simulation + MiroFish Project Introduction, 2. Dream of the Red Chamber Lost Ending Simulation, 2. Install Dependencies (+27 more)

### Community 16 - "SimulationView.vue"
Cohesion: 0.08
Nodes (24): closeSimulationEnv(), getEnvStatus(), stopSimulation(), addLog(), checkAndStopRunningSimulation(), currentSimulationId, currentStatus, forceStopSimulation() (+16 more)

### Community 18 - "run_reddit_simulation"
Cohesion: 0.10
Nodes (8): PlatformActionLogger, create_model(), fetch_new_actions_from_db(), get_active_agents_for_round(), get_agent_names_from_config(), PlatformSimulation, run_reddit_simulation(), run_twitter_simulation()

### Community 19 - "IPCHandler"
Cohesion: 0.09
Nodes (3): IPCHandler, main(), RedditSimulationRunner

### Community 20 - "IPCHandler"
Cohesion: 0.09
Nodes (3): IPCHandler, main(), TwitterSimulationRunner

### Community 21 - "IPCResponse"
Cohesion: 0.10
Nodes (5): CommandStatus, CommandType, IPCCommand, IPCResponse, SimulationIPCServer

### Community 22 - "report.py"
Cohesion: 0.11
Nodes (11): check_report_status(), download_report(), generate_report(), get_agent_log(), get_generate_status(), get_report(), get_report_by_simulation(), get_report_sections() (+3 more)

### Community 23 - "SimulationRunView.vue"
Cohesion: 0.09
Nodes (27): getSimulation(), getSimulationConfig(), addLog(), currentSimulationId, currentStatus, graphData, graphLoading, handleGoBack() (+19 more)

### Community 24 - "run_parallel_simulation.py"
Cohesion: 0.12
Nodes (4): CommandType, _utf8_open(), CommandType, CommandType

### Community 25 - "ReportAgent"
Cohesion: 0.11
Nodes (3): run_generate(), ReportAgent, ReportSection

### Community 26 - "FileParser"
Cohesion: 0.10
Nodes (4): build_task(), FileParser, _read_text_with_fallback(), split_text_into_chunks()

### Community 27 - "HistoryDatabase.vue"
Cohesion: 0.08
Nodes (11): getSimulationHistory(), containerStyle, historyContainer, hoveringCard, isExpanded, loadHistory(), loading, projects (+3 more)

### Community 28 - "SimulationIPCClient"
Cohesion: 0.12
Nodes (4): interview_agent(), interview_agents_batch(), optimize_interview_prompt(), SimulationIPCClient

### Community 29 - "Home.vue"
Cohesion: 0.09
Nodes (17): addFiles(), canSubmit, configData, fileInput, files, formData, handleDrop(), handleFileSelect() (+9 more)

### Community 30 - "ReportView.vue"
Cohesion: 0.11
Nodes (20): getReport(), addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph() (+12 more)

### Community 31 - "ReportManager"
Cohesion: 0.12
Nodes (4): delete_report(), get_report_progress(), list_reports(), ReportManager

### Community 33 - "frontend/package.json"
Cohesion: 0.10
Nodes (20): dependencies, axios, d3, vue, vue-router, devDependencies, vite, @vitejs/plugin-vue (+12 more)

### Community 34 - "InteractionView.vue"
Cohesion: 0.11
Nodes (19): addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph(), loadReportData() (+11 more)

### Community 39 - "SimulationLogManager"
Cohesion: 0.15
Nodes (3): SimulationLogManager, load_config(), main()

### Community 40 - "vue"
Cohesion: 0.12
Nodes (13): createSimulation(), creatingSimulation, graphStats, handleEnterEnvSetup(), logContent, props, router, selectedOntologyItem (+5 more)

### Community 41 - "package.json"
Cohesion: 0.11
Nodes (17): description, devDependencies, concurrently, engines, node, license, name, scripts (+9 more)

### Community 42 - "prepare_simulation"
Cohesion: 0.16
Nodes (8): build_graph(), _check_simulation_prepared(), _get_report_id_for_simulation(), prepare_simulation(), run_prepare(), debug(), info(), warning()

### Community 46 - "retry_with_backoff_async"
Cohesion: 0.15
Nodes (6): retry_with_backoff(), retry_with_backoff_async(), decorator(), decorator(), wrapper(), RetryableAPIClient

### Community 47 - "GraphPanel.vue"
Cohesion: 0.12
Nodes (12): emit, entityTypes, expandedSelfLoops, graphContainer, graphSvg, handleResize(), props, renderGraph() (+4 more)

### Community 48 - "LLMClient"
Cohesion: 0.17
Nodes (3): test_llm(), OntologyGenerator, LLMClient

### Community 54 - "getGraphData"
Cohesion: 0.35
Nodes (8): buildGraph(), generateOntology(), getGraphData(), getTaskStatus(), requestWithRetry(), service, chatWithReport(), generateReport()

### Community 58 - "OasisAgentProfile"
Cohesion: 0.27
Nodes (3): OasisAgentProfile, show_expected_formats(), test_profile_formats()

### Community 62 - ".get_all_nodes"
Cohesion: 0.31
Nodes (4): NodeInfo, get_entity_summary(), get_graph_statistics(), get_simulation_context()

### Community 70 - "_enrich_action_context"
Cohesion: 0.25
Nodes (4): _enrich_action_context(), _get_comment_info(), _get_post_info(), _get_user_name()

### Community 71 - "getAgentLog"
Cohesion: 0.25
Nodes (8): getAgentLog(), getConsoleLog(), addLog(), emit, fetchAgentLog(), fetchConsoleLog(), startPolling(), stopPolling()

### Community 85 - "closeModal"
Cohesion: 0.50
Nodes (4): closeModal(), goToProject(), goToReport(), goToSimulation()

### Community 92 - "fetchStatus"
Cohesion: 0.67
Nodes (3): error, fetchStatus(), saveSettings()

## Knowledge Gaps
- **291 isolated node(s):** `mirofish-backend`, `name`, `private`, `version`, `type` (+286 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 980 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **51 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Config` connect `Config` to `simulation_runner.py`, `OasisProfileGenerator`, `simulation.py`, `services/__init__.py`, `ProjectManager`, `SimulationConfigGenerator`, `prepare_simulation`, `ObsidianMemoryProvider`, `LLMClient`, `ZepMemoryProvider`, `ReportLogger`, `ReportConsoleLogger`, `report.py`, `ZepToolsService`, `ReportManager`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `Config` (e.g. with `allowed_file()` and `build_graph()`) actually correct?**
  _`Config` has 26 INFERRED edges - model-reasoned connections that need verification._
- **What connects `mirofish-backend`, `name`, `private` to the rest of the system?**
  _291 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `simulation_runner.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08978174603174603 - nodes in this community are weakly interconnected._
- **Why does `SimulationRunner` connect `SimulationRunner` to `simulation_runner.py`, `simulation.py`, `services/__init__.py`, `SimulationManager`, `Config`, `SimulationIPCClient`, `ZepToolsService`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Are the 18 inferred relationships involving `SimulationRunner` (e.g. with `close_simulation_env()` and `get_agent_stats()`) actually correct?**
  _`SimulationRunner` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Should `SimulationRunner` be split into smaller, more focused modules?**
  _Cohesion score 0.05711263881544157 - nodes in this community are weakly interconnected._