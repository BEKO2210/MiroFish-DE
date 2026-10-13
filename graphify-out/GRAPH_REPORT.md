# Graph Report - MiroFish-DE  (2026-10-13)

## Corpus Check
- 70 files · ~376,038 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 5, .example 1, .lock 1)

## Summary
- 1936 nodes · 3923 edges · 98 communities (48 shown, 50 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 311 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f7d47cd1`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- simulation_runner.py
- SimulationRunner
- Step4Report.vue
- SimulationManager
- Process.vue
- Step5Interaction.vue
- TextProcessor
- ProjectManager
- SimulationConfigGenerator
- graph.py
- GraphBuilderService
- Step3Simulation.vue
- Config
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
- simulation.py
- Home.vue
- ReportView.vue
- ReportManager
- GraphPanel.vue
- InteractionView.vue
- MemoryProvider
- .generate_report
- AgentActivity
- ParallelIPCHandler
- SimulationLogManager
- Step1GraphBuild.vue
- package.json
- logger.py
- ObsidianMemoryProvider
- ZepEntityReader
- ZepToolsService
- retry_with_backoff_async
- Any
- OntologyGenerator
- ZepMemoryProvider
- ZepGraphMemoryUpdater
- MemoryNode
- ReportConsoleLogger
- ActionLogger
- getGraphData
- json
- .search_graph
- MemoryEdge
- AgentAction
- OasisProfileGenerator
- Any
- EdgeInfo
- .get_all_nodes
- InsightForgeResult
- MemorySearchResult
- .get_project
- .get_all_edges
- init_logging_for_simulation
- getAgentLog
- SimulationParameters
- InterviewResult
- setup_oasis_logging
- setup_oasis_logging
- .save_project
- build_graph
- generate_report
- vue-router
- simulation.js
- AgentInterview
- setup_signal_handlers
- services/__init__.py
- ._get_report_folder
- MaxTokensWarningFilter
- setup_signal_handlers
- _get_comment_info
- mirofish-backend
- prepare_simulation

## God Nodes (most connected - your core abstractions)
1. `Config` - 57 edges
2. `error()` - 57 edges
3. `SimulationRunner` - 52 edges
4. `ReportManager` - 48 edges
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
- `get_project()` --uses--> `ProjectManager`  [INFERRED]
  backend/app/api/graph.py → backend/app/models/project.py
- `list_projects()` --uses--> `ProjectManager`  [INFERRED]
  backend/app/api/graph.py → backend/app/models/project.py
- `reset_project()` --uses--> `ProjectManager`  [INFERRED]
  backend/app/api/graph.py → backend/app/models/project.py

## Import Cycles
- None detected.

## Communities (98 total, 50 thin omitted)

### Community 0 - "simulation_runner.py"
Cohesion: 0.10
Nodes (3): fetch_all_edges(), fetch_all_nodes(), _fetch_page_with_retry()

### Community 1 - "SimulationRunner"
Cohesion: 0.08
Nodes (5): start_simulation(), SimulationRunner, cleanup_handler(), SimulationRunState, ZepGraphMemoryManager

### Community 2 - "Step4Report.vue"
Cohesion: 0.03
Nodes (37): activeSectionIndex, activeStep, agentLogLine, agentLogs, collapsedSections, completedSections, consoleLogLine, consoleLogs (+29 more)

### Community 3 - "SimulationManager"
Cohesion: 0.08
Nodes (9): download_simulation_config(), get_simulation(), get_simulation_config(), get_simulation_history(), get_simulation_profiles(), list_simulations(), stop_simulation(), SimulationManager (+1 more)

### Community 4 - "Process.vue"
Cohesion: 0.07
Nodes (39): getProject(), clearPendingUpload(), getPendingUpload(), buildProgress, closeDetailPanel(), currentPhase, currentProjectId, entityTypes (+31 more)

### Community 5 - "Step5Interaction.vue"
Cohesion: 0.05
Nodes (40): getSimulationProfilesRealtime(), interviewAgents(), activeTab, addLog(), chatHistory, chatHistoryCache, chatInput, chatInputRef (+32 more)

### Community 6 - "TextProcessor"
Cohesion: 0.09
Nodes (4): TextProcessor, FileParser, _read_text_with_fallback(), split_text_into_chunks()

### Community 7 - "ProjectManager"
Cohesion: 0.13
Nodes (3): delete_project(), generate_ontology(), ProjectManager

### Community 9 - "graph.py"
Cohesion: 0.08
Nodes (6): get_task(), list_tasks(), get_prepare_status(), Task, TaskManager, TaskStatus

### Community 10 - "GraphBuilderService"
Cohesion: 0.08
Nodes (4): delete_graph(), get_graph_data(), GraphBuilderService, GraphInfo

### Community 11 - "Step3Simulation.vue"
Cohesion: 0.08
Nodes (34): getRunStatus(), getRunStatusDetail(), actionIds, addLog(), allActions, checkPlatformsCompleted(), chronologicalActions, doStartSimulation() (+26 more)

### Community 12 - "Config"
Cohesion: 0.10
Nodes (7): allowed_file(), mask_key(), save_config(), system_status(), test_llm(), Config, main()

### Community 13 - "Step2EnvSetup.vue"
Cohesion: 0.09
Nodes (35): getPrepareStatus(), getSimulationConfigRealtime(), prepareSimulation(), addLog(), autoGeneratedRounds, currentStage, customMaxRounds, displayProfiles (+27 more)

### Community 14 - "MainView.vue"
Cohesion: 0.10
Nodes (35): addLog(), buildProgress, currentPhase, currentProjectId, currentStep, error, fetchGraphData(), graphData (+27 more)

### Community 15 - "README.md"
Cohesion: 0.05
Nodes (36): 1. Umgebungsvariablen konfigurieren, 2. Abhängigkeiten installieren, 3. Dienste starten, 📄 Danksagung, 1. Configure Environment Variables, 1. Wuhan University Public Opinion Simulation + MiroFish Project Introduction, 2. Dream of the Red Chamber Lost Ending Simulation, 2. Install Dependencies (+28 more)

### Community 16 - "SimulationView.vue"
Cohesion: 0.10
Nodes (24): closeSimulationEnv(), getEnvStatus(), getSimulation(), addLog(), checkAndStopRunningSimulation(), currentSimulationId, currentStatus, forceStopSimulation() (+16 more)

### Community 18 - "run_reddit_simulation"
Cohesion: 0.10
Nodes (9): PlatformActionLogger, create_model(), _enrich_action_context(), fetch_new_actions_from_db(), get_active_agents_for_round(), get_agent_names_from_config(), PlatformSimulation, run_reddit_simulation() (+1 more)

### Community 19 - "IPCHandler"
Cohesion: 0.09
Nodes (3): IPCHandler, main(), RedditSimulationRunner

### Community 20 - "IPCHandler"
Cohesion: 0.09
Nodes (3): IPCHandler, main(), TwitterSimulationRunner

### Community 21 - "SimulationIPCClient"
Cohesion: 0.08
Nodes (6): CommandStatus, CommandType, IPCCommand, IPCResponse, SimulationIPCClient, SimulationIPCServer

### Community 22 - "error"
Cohesion: 0.10
Nodes (18): check_report_status(), get_agent_log(), get_console_log(), get_graph_statistics_tool(), get_report(), get_report_by_simulation(), get_report_progress(), get_report_sections() (+10 more)

### Community 23 - "SimulationRunView.vue"
Cohesion: 0.09
Nodes (27): getSimulationConfig(), stopSimulation(), addLog(), currentSimulationId, currentStatus, graphData, graphLoading, handleGoBack() (+19 more)

### Community 24 - "run_parallel_simulation.py"
Cohesion: 0.08
Nodes (8): CommandType, _get_post_info(), _get_user_name(), MaxTokensWarningFilter, _utf8_open(), CommandType, CommandType, MaxTokensWarningFilter

### Community 26 - "os"
Cohesion: 0.14
Nodes (16): _base(), _dir(), _load(), mark_stale_runs(), _ok(), _path(), pipeline_list(), pipeline_status() (+8 more)

### Community 27 - "HistoryDatabase.vue"
Cohesion: 0.08
Nodes (17): deleteSimulation(), getSimulationHistory(), closeModal(), confirmDelete(), containerStyle, goToProject(), goToReport(), goToSimulation() (+9 more)

### Community 28 - "simulation.py"
Cohesion: 0.10
Nodes (12): create_simulation(), delete_simulation(), get_agent_stats(), get_env_status(), get_interview_history(), get_run_status(), get_simulation_actions(), interview_agent() (+4 more)

### Community 29 - "Home.vue"
Cohesion: 0.07
Nodes (23): state, addFiles(), canSubmit, configData, error, fetchStatus(), fileInput, files (+15 more)

### Community 30 - "ReportView.vue"
Cohesion: 0.11
Nodes (19): addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph(), loadReportData() (+11 more)

### Community 31 - "ReportManager"
Cohesion: 0.20
Nodes (3): download_report(), list_reports(), ReportManager

### Community 33 - "GraphPanel.vue"
Cohesion: 0.05
Nodes (32): dependencies, axios, d3, vue, vue-router, devDependencies, vite, @vitejs/plugin-vue (+24 more)

### Community 34 - "InteractionView.vue"
Cohesion: 0.11
Nodes (20): getReport(), addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph() (+12 more)

### Community 39 - "SimulationLogManager"
Cohesion: 0.15
Nodes (3): SimulationLogManager, load_config(), main()

### Community 40 - "Step1GraphBuild.vue"
Cohesion: 0.20
Nodes (8): createSimulation(), creatingSimulation, graphStats, handleEnterEnvSetup(), logContent, props, router, selectedOntologyItem

### Community 41 - "package.json"
Cohesion: 0.11
Nodes (17): description, devDependencies, concurrently, engines, node, license, name, scripts (+9 more)

### Community 42 - "logger.py"
Cohesion: 0.11
Nodes (9): _check_simulation_prepared(), get_graph_entities(), create_app(), log_request(), log_response(), _ensure_utf8_stdout(), get_logger(), info() (+1 more)

### Community 44 - "ZepEntityReader"
Cohesion: 0.14
Nodes (3): generate_profiles(), FilteredEntities, ZepEntityReader

### Community 46 - "retry_with_backoff_async"
Cohesion: 0.15
Nodes (6): retry_with_backoff(), retry_with_backoff_async(), decorator(), decorator(), wrapper(), RetryableAPIClient

### Community 49 - "ZepMemoryProvider"
Cohesion: 0.12
Nodes (3): MemoryFactory, HybridMemoryProvider, ZepMemoryProvider

### Community 54 - "getGraphData"
Cohesion: 0.35
Nodes (8): buildGraph(), generateOntology(), getGraphData(), getTaskStatus(), requestWithRetry(), service, chatWithReport(), generateReport()

### Community 58 - "AgentAction"
Cohesion: 0.15
Nodes (3): get_run_status_detail(), get_simulation_timeline(), AgentAction

### Community 59 - "OasisProfileGenerator"
Cohesion: 0.08
Nodes (5): OasisAgentProfile, OasisProfileGenerator, generate_single_profile(), show_expected_formats(), test_profile_formats()

### Community 65 - ".get_project"
Cohesion: 0.18
Nodes (3): get_project(), list_projects(), reset_project()

### Community 71 - "getAgentLog"
Cohesion: 0.25
Nodes (8): getAgentLog(), getConsoleLog(), addLog(), emit, fetchAgentLog(), fetchConsoleLog(), startPolling(), stopPolling()

### Community 78 - "build_graph"
Cohesion: 0.22
Nodes (4): build_graph(), build_task(), ProjectStatus, debug()

### Community 79 - "generate_report"
Cohesion: 0.22
Nodes (4): generate_report(), run_generate(), get_generate_status(), ReportStatus

### Community 80 - "vue-router"
Cohesion: 0.17
Nodes (9): currentReport, currentRun, route, router, safeGet(), app, router, routes (+1 more)

### Community 87 - "services/__init__.py"
Cohesion: 0.14
Nodes (5): AgentActivityConfig, EventConfig, PlatformConfig, TimeSimulationConfig, RoundSummary

### Community 99 - "prepare_simulation"
Cohesion: 0.29
Nodes (4): prepare_simulation(), run_prepare(), PlatformType, SimulationStatus

## Knowledge Gaps
- **294 isolated node(s):** `mirofish-backend`, `name`, `private`, `version`, `type` (+289 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 995 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **50 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Config` connect `Config` to `simulation_runner.py`, `SimulationRunner`, `ProjectManager`, `SimulationConfigGenerator`, `graph.py`, `GraphBuilderService`, `ReportLogger`, `error`, `os`, `simulation.py`, `ReportManager`, `._generate_profile_with_llm`, `MemoryProvider`, `logger.py`, `ObsidianMemoryProvider`, `ZepToolsService`, `ZepMemoryProvider`, `ReportConsoleLogger`, `json`, `OasisProfileGenerator`, `build_graph`?**
  _High betweenness centrality (0.100) - this node is a cross-community bridge._
- **Are the 29 inferred relationships involving `Config` (e.g. with `allowed_file()` and `build_graph()`) actually correct?**
  _`Config` has 29 INFERRED edges - model-reasoned connections that need verification._
- **What connects `mirofish-backend`, `name`, `private` to the rest of the system?**
  _294 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `simulation_runner.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09990749306197964 - nodes in this community are weakly interconnected._
- **Why does `OasisProfileGenerator` connect `OasisProfileGenerator` to `simulation_runner.py`, `._generate_profile_with_llm`, `SimulationManager`, `._search_zep_for_entity`, `SimulationConfigGenerator`, `Config`, `ZepEntityReader`, `services/__init__.py`, `simulation.py`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Are the 20 inferred relationships involving `SimulationRunner` (e.g. with `close_simulation_env()` and `delete_simulation()`) actually correct?**
  _`SimulationRunner` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Should `SimulationRunner` be split into smaller, more focused modules?**
  _Cohesion score 0.07822410147991543 - nodes in this community are weakly interconnected._