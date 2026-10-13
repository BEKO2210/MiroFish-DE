# Graph Report - mirofish-i18n  (2026-10-13)

## Corpus Check
- 80 files · ~384,971 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: (none) 6, .example 1, .lock 1)

## Summary
- 2030 nodes · 3987 edges · 101 communities (45 shown, 56 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 305 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `69458ac8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Config
- SimulationRunner
- Step4Report.vue
- SimulationManager
- Process.vue
- Step5Interaction.vue
- graph.py
- ProjectManager
- SimulationConfigGenerator
- codemod-i18n.mjs
- GraphBuilderService
- Step3Simulation.vue
- system.py
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
- TextProcessor
- HistoryDatabase.vue
- simulation.py
- Home.vue
- ReportView.vue
- ReportManager
- GraphPanel.vue
- InteractionView.vue
- ZepMemoryProvider
- .generate_report
- AgentActivity
- ParallelIPCHandler
- SimulationLogManager
- vue
- package.json
- TaskManager
- ObsidianMemoryProvider
- ZepEntityReader
- Any
- retry_with_backoff_async
- LLMClient
- OntologyGenerator
- ZepGraphMemoryUpdater
- ZepToolsService
- ReportConsoleLogger
- action_logger.py
- getGraphData
- OasisAgentProfile
- .search_graph
- simulation_runner.py
- test_profile_format.py
- OasisProfileGenerator
- ReportOutline
- EdgeInfo
- .get_all_nodes
- .insight_forge
- MemorySearchResult
- EntityNode
- simulation.js
- .panorama_search
- _enrich_action_context
- getAgentLog
- SimulationParameters
- InterviewResult
- setup_oasis_logging
- setup_oasis_logging
- ref_vue_i18n
- zep_tools.py
- init_logging_for_simulation
- services/__init__.py
- setup_signal_handlers
- MaxTokensWarningFilter
- setup_signal_handlers
- setup_signal_handlers
- mirofish-backend
- MaxTokensWarningFilter
- logger.py
- TASK.md

## God Nodes (most connected - your core abstractions)
1. `error()` - 55 edges
2. `Config` - 54 edges
3. `SimulationRunner` - 51 edges
4. `ReportManager` - 46 edges
5. `ZepToolsService` - 35 edges
6. `OasisProfileGenerator` - 34 edges
7. `ProjectManager` - 33 edges
8. `ObsidianMemoryProvider` - 33 edges
9. `SimulationManager` - 32 edges
10. `get_logger()` - 28 edges

## Surprising Connections (you probably didn't know these)
- `create_app()` --uses--> `SimulationRunner`  [INFERRED]
  backend/app/__init__.py → backend/app/services/simulation_runner.py
- `allowed_file()` --uses--> `Config`  [INFERRED]
  backend/app/api/graph.py → backend/app/config.py
- `reset_project()` --uses--> `ProjectStatus`  [INFERRED]
  backend/app/api/graph.py → backend/app/models/project.py
- `generate_ontology()` --uses--> `ProjectStatus`  [INFERRED]
  backend/app/api/graph.py → backend/app/models/project.py
- `generate_ontology()` --uses--> `OntologyGenerator`  [INFERRED]
  backend/app/api/graph.py → backend/app/services/ontology_generator.py

## Import Cycles
- None detected.

## Communities (101 total, 56 thin omitted)

### Community 0 - "Config"
Cohesion: 0.13
Nodes (7): Config, create_app(), log_request(), log_response(), get_logger(), setup_logger(), main()

### Community 1 - "SimulationRunner"
Cohesion: 0.05
Nodes (7): get_run_status_detail(), start_simulation(), stop_simulation(), AgentAction, SimulationRunner, cleanup_handler(), SimulationRunState

### Community 2 - "Step4Report.vue"
Cohesion: 0.03
Nodes (38): activeSectionIndex, activeStep, agentLogLine, agentLogs, collapsedSections, completedSections, consoleLogLine, consoleLogs (+30 more)

### Community 3 - "SimulationManager"
Cohesion: 0.10
Nodes (6): close_simulation_env(), get_simulation(), get_simulation_history(), SimulationManager, SimulationState, SimulationStatus

### Community 4 - "Process.vue"
Cohesion: 0.07
Nodes (39): getProject(), clearPendingUpload(), buildProgress, closeDetailPanel(), currentPhase, currentProjectId, entityTypes, error (+31 more)

### Community 5 - "Step5Interaction.vue"
Cohesion: 0.05
Nodes (41): getSimulationProfilesRealtime(), interviewAgents(), activeTab, addLog(), chatHistory, chatHistoryCache, chatInput, chatInputRef (+33 more)

### Community 6 - "graph.py"
Cohesion: 0.13
Nodes (3): allowed_file(), ProjectStatus, TaskStatus

### Community 7 - "ProjectManager"
Cohesion: 0.07
Nodes (9): delete_project(), generate_ontology(), get_project(), list_projects(), list_tasks(), reset_project(), create_simulation(), Project (+1 more)

### Community 9 - "codemod-i18n.mjs"
Cohesion: 0.07
Nodes (29): de, en, translations, unchanged, addMessage(), apply, catalog, commonValues (+21 more)

### Community 10 - "GraphBuilderService"
Cohesion: 0.08
Nodes (3): get_graph_data(), GraphBuilderService, GraphInfo

### Community 11 - "Step3Simulation.vue"
Cohesion: 0.07
Nodes (37): getRunStatus(), getRunStatusDetail(), startSimulation(), stopSimulation(), actionIds, addLog(), allActions, checkPlatformsCompleted() (+29 more)

### Community 12 - "system.py"
Cohesion: 0.13
Nodes (4): mask_key(), save_config(), system_status(), test_llm()

### Community 13 - "Step2EnvSetup.vue"
Cohesion: 0.09
Nodes (35): getPrepareStatus(), getSimulationConfigRealtime(), addLog(), autoGeneratedRounds, currentStage, customMaxRounds, displayProfiles, emit (+27 more)

### Community 14 - "MainView.vue"
Cohesion: 0.09
Nodes (36): addLog(), buildProgress, currentPhase, currentProjectId, currentStep, error, fetchGraphData(), graphData (+28 more)

### Community 15 - "README.md"
Cohesion: 0.05
Nodes (36): 1. Umgebungsvariablen konfigurieren, 2. Abhängigkeiten installieren, 3. Dienste starten, 📄 Danksagung, 1. Configure Environment Variables, 1. Wuhan University Public Opinion Simulation + MiroFish Project Introduction, 2. Dream of the Red Chamber Lost Ending Simulation, 2. Install Dependencies (+28 more)

### Community 16 - "SimulationView.vue"
Cohesion: 0.10
Nodes (24): getEnvStatus(), getSimulation(), addLog(), checkAndStopRunningSimulation(), currentSimulationId, currentStatus, forceStopSimulation(), graphData (+16 more)

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

### Community 22 - "error"
Cohesion: 0.09
Nodes (24): delete_graph(), chat_with_report_agent(), check_report_status(), delete_report(), download_report(), generate_report(), get_agent_log(), get_console_log() (+16 more)

### Community 23 - "SimulationRunView.vue"
Cohesion: 0.09
Nodes (28): closeSimulationEnv(), getSimulationConfig(), addLog(), currentSimulationId, currentStatus, graphData, graphLoading, handleGoBack() (+20 more)

### Community 24 - "run_parallel_simulation.py"
Cohesion: 0.11
Nodes (5): CommandType, _utf8_open(), CommandType, CommandType, MaxTokensWarningFilter

### Community 26 - "TextProcessor"
Cohesion: 0.09
Nodes (5): build_task(), TextProcessor, FileParser, _read_text_with_fallback(), split_text_into_chunks()

### Community 27 - "HistoryDatabase.vue"
Cohesion: 0.08
Nodes (16): getSimulationHistory(), closeModal(), containerStyle, goToProject(), goToReport(), goToSimulation(), historyContainer, hoveringCard (+8 more)

### Community 28 - "simulation.py"
Cohesion: 0.08
Nodes (16): download_simulation_config(), download_simulation_script(), get_agent_stats(), get_env_status(), get_interview_history(), get_run_status(), get_simulation_comments(), get_simulation_config() (+8 more)

### Community 29 - "Home.vue"
Cohesion: 0.07
Nodes (24): getPendingUpload(), state, addFiles(), canSubmit, configData, error, fetchStatus(), fileInput (+16 more)

### Community 30 - "ReportView.vue"
Cohesion: 0.10
Nodes (20): addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph(), loadReportData() (+12 more)

### Community 33 - "GraphPanel.vue"
Cohesion: 0.05
Nodes (32): dependencies, axios, d3, vue, vue-router, devDependencies, vite, @vitejs/plugin-vue (+24 more)

### Community 34 - "InteractionView.vue"
Cohesion: 0.10
Nodes (20): addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph(), loadReportData() (+12 more)

### Community 35 - "ZepMemoryProvider"
Cohesion: 0.06
Nodes (5): MemoryEdge, MemoryProvider, MemoryFactory, HybridMemoryProvider, ZepMemoryProvider

### Community 39 - "SimulationLogManager"
Cohesion: 0.13
Nodes (3): SimulationLogManager, load_config(), main()

### Community 40 - "vue"
Cohesion: 0.12
Nodes (14): createSimulation(), creatingSimulation, graphStats, handleEnterEnvSetup(), logContent, props, router, selectedOntologyItem (+6 more)

### Community 41 - "package.json"
Cohesion: 0.11
Nodes (17): description, devDependencies, concurrently, engines, node, license, name, scripts (+9 more)

### Community 42 - "TaskManager"
Cohesion: 0.09
Nodes (12): build_graph(), get_task(), _check_simulation_prepared(), get_prepare_status(), _get_report_id_for_simulation(), prepare_simulation(), run_prepare(), Task (+4 more)

### Community 44 - "ZepEntityReader"
Cohesion: 0.13
Nodes (5): generate_profiles(), get_entities_by_type(), get_entity_detail(), get_graph_entities(), ZepEntityReader

### Community 46 - "retry_with_backoff_async"
Cohesion: 0.15
Nodes (6): retry_with_backoff(), retry_with_backoff_async(), decorator(), decorator(), wrapper(), RetryableAPIClient

### Community 54 - "getGraphData"
Cohesion: 0.31
Nodes (9): buildGraph(), generateOntology(), getGraphData(), getTaskStatus(), requestWithRetry(), service, chatWithReport(), generateReport() (+1 more)

### Community 57 - "simulation_runner.py"
Cohesion: 0.15
Nodes (3): RoundSummary, RunnerStatus, ZepGraphMemoryManager

### Community 62 - ".get_all_nodes"
Cohesion: 0.22
Nodes (4): NodeInfo, get_entity_summary(), get_graph_statistics(), get_simulation_context()

### Community 70 - "_enrich_action_context"
Cohesion: 0.20
Nodes (5): _enrich_action_context(), fetch_new_actions_from_db(), _get_comment_info(), _get_post_info(), _get_user_name()

### Community 71 - "getAgentLog"
Cohesion: 0.25
Nodes (8): getAgentLog(), getConsoleLog(), addLog(), emit, fetchAgentLog(), fetchConsoleLog(), startPolling(), stopPolling()

### Community 78 - "zep_tools.py"
Cohesion: 0.18
Nodes (3): fetch_all_edges(), fetch_all_nodes(), _fetch_page_with_retry()

### Community 87 - "services/__init__.py"
Cohesion: 0.15
Nodes (6): AgentActivityConfig, EventConfig, PlatformConfig, TimeSimulationConfig, CommandStatus, CommandType

### Community 99 - "logger.py"
Cohesion: 0.12
Nodes (3): PlatformType, FilteredEntities, _ensure_utf8_stdout()

## Knowledge Gaps
- **327 isolated node(s):** `mirofish-backend`, `name`, `private`, `version`, `type` (+322 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1088 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **56 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Config` connect `Config` to `SimulationRunner`, `graph.py`, `ProjectManager`, `SimulationConfigGenerator`, `GraphBuilderService`, `system.py`, `ReportLogger`, `error`, `simulation.py`, `ReportManager`, `._generate_profile_with_llm`, `ZepMemoryProvider`, `TaskManager`, `ObsidianMemoryProvider`, `ZepEntityReader`, `LLMClient`, `ZepToolsService`, `ReportConsoleLogger`, `simulation_runner.py`, `OasisProfileGenerator`, `zep_tools.py`, `services/__init__.py`, `logger.py`?**
  _High betweenness centrality (0.107) - this node is a cross-community bridge._
- **Are the 27 inferred relationships involving `Config` (e.g. with `allowed_file()` and `build_graph()`) actually correct?**
  _`Config` has 27 INFERRED edges - model-reasoned connections that need verification._
- **What connects `mirofish-backend`, `name`, `private` to the rest of the system?**
  _327 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Config` be split into smaller, more focused modules?**
  _Cohesion score 0.12698412698412698 - nodes in this community are weakly interconnected._
- **Why does `OasisProfileGenerator` connect `OasisProfileGenerator` to `Config`, `._generate_profile_with_llm`, `EntityNode`, `logger.py`, `SimulationManager`, `._search_zep_for_entity`, `ZepEntityReader`, `system.py`, `OasisAgentProfile`, `services/__init__.py`, `test_profile_format.py`, `simulation.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `SimulationRunner` (e.g. with `close_simulation_env()` and `get_agent_stats()`) actually correct?**
  _`SimulationRunner` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Should `SimulationRunner` be split into smaller, more focused modules?**
  _Cohesion score 0.045454545454545456 - nodes in this community are weakly interconnected._