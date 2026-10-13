# Graph Report - MiroFish-DE  (2026-10-13)

## Corpus Check
- 68 files · ~374,146 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 5, .example 1, .lock 1)

## Summary
- 1899 nodes · 3807 edges · 100 communities (46 shown, 54 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 302 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7e5edfd7`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Config
- SimulationRunner
- Step4Report.vue
- simulation.py
- Process.vue
- Step5Interaction.vue
- graph.py
- ProjectManager
- SimulationConfigGenerator
- GraphBuilderService
- Step3Simulation.vue
- system.py
- Step2EnvSetup.vue
- MainView.vue
- README-EN.md
- SimulationView.vue
- ReportLogger
- run_reddit_simulation
- IPCHandler
- IPCHandler
- IPCResponse
- error
- SimulationRunView.vue
- run_reddit_simulation.py
- ReportAgent
- FileParser
- HistoryDatabase.vue
- interview_agent
- Home.vue
- ReportView.vue
- ReportManager
- frontend/package.json
- InteractionView.vue
- MemoryProvider
- .generate_report
- AgentActivity
- ParallelIPCHandler
- SimulationLogManager
- simulation.js
- package.json
- run_prepare
- ObsidianMemoryProvider
- ZepEntityReader
- ZepToolsService
- retry.py
- GraphPanel.vue
- services/__init__.py
- ZepMemoryProvider
- ZepGraphMemoryUpdater
- MemoryNode
- ActionLogger
- getProject
- .generate_profile_from_entity
- .search_graph
- MemoryEdge
- OasisAgentProfile
- OasisProfileGenerator
- ReportOutline
- EdgeInfo
- .get_all_nodes
- .insight_forge
- MemorySearchResult
- RedditSimulationRunner
- TwitterSimulationRunner
- .panorama_search
- run_parallel_simulation.py
- fetchAgentLog
- Any
- setup_oasis_logging
- setup_oasis_logging
- addLog
- zep_paging.py
- loadProject
- vue
- report.js
- pendingUpload.js
- ReportSection
- closeModal
- AgentActivityConfig
- setup_signal_handlers
- setup_signal_handlers
- fetchStatus
- mirofish-backend
- PlatformType

## God Nodes (most connected - your core abstractions)
1. `error()` - 55 edges
2. `Config` - 54 edges
3. `SimulationRunner` - 51 edges
4. `ReportManager` - 46 edges
5. `OasisProfileGenerator` - 34 edges
6. `ProjectManager` - 33 edges
7. `ObsidianMemoryProvider` - 33 edges
8. `SimulationManager` - 32 edges
9. `ZepToolsService` - 30 edges
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

## Communities (100 total, 54 thin omitted)

### Community 0 - "Config"
Cohesion: 0.08
Nodes (11): Config, create_app(), log_request(), log_response(), ReportConsoleLogger, SimulationParameters, ZepGraphMemoryManager, _ensure_utf8_stdout() (+3 more)

### Community 1 - "SimulationRunner"
Cohesion: 0.04
Nodes (7): get_env_status(), get_run_status_detail(), SimulationIPCClient, AgentAction, SimulationRunner, cleanup_handler(), SimulationRunState

### Community 2 - "Step4Report.vue"
Cohesion: 0.03
Nodes (37): activeSectionIndex, activeStep, agentLogLine, agentLogs, collapsedSections, completedSections, consoleLogLine, consoleLogs (+29 more)

### Community 3 - "simulation.py"
Cohesion: 0.06
Nodes (29): _check_simulation_prepared(), close_simulation_env(), create_simulation(), download_simulation_config(), download_simulation_script(), get_agent_stats(), get_graph_entities(), get_interview_history() (+21 more)

### Community 4 - "Process.vue"
Cohesion: 0.07
Nodes (25): buildProgress, closeDetailPanel(), currentPhase, currentProjectId, entityTypes, fetchGraphData(), graphContainer, graphData (+17 more)

### Community 5 - "Step5Interaction.vue"
Cohesion: 0.05
Nodes (25): activeTab, chatHistory, chatHistoryCache, chatInput, chatInputRef, chatMessages, chatTarget, collapsedSections (+17 more)

### Community 6 - "graph.py"
Cohesion: 0.08
Nodes (6): allowed_file(), build_task(), ProjectStatus, TaskStatus, TextProcessor, split_text_into_chunks()

### Community 7 - "ProjectManager"
Cohesion: 0.08
Nodes (9): build_graph(), delete_project(), generate_ontology(), get_project(), list_projects(), reset_project(), Project, ProjectManager (+1 more)

### Community 10 - "GraphBuilderService"
Cohesion: 0.05
Nodes (8): delete_graph(), get_graph_data(), get_task(), list_tasks(), Task, TaskManager, GraphBuilderService, GraphInfo

### Community 11 - "Step3Simulation.vue"
Cohesion: 0.08
Nodes (36): generateReport(), getRunStatus(), getRunStatusDetail(), startSimulation(), actionIds, addLog(), allActions, checkPlatformsCompleted() (+28 more)

### Community 12 - "system.py"
Cohesion: 0.11
Nodes (4): mask_key(), save_config(), system_status(), test_llm()

### Community 13 - "Step2EnvSetup.vue"
Cohesion: 0.09
Nodes (34): getPrepareStatus(), getSimulationConfigRealtime(), addLog(), autoGeneratedRounds, currentStage, customMaxRounds, displayProfiles, emit (+26 more)

### Community 14 - "MainView.vue"
Cohesion: 0.10
Nodes (34): addLog(), buildProgress, currentPhase, currentProjectId, currentStep, error, graphData, graphLoading (+26 more)

### Community 15 - "README-EN.md"
Cohesion: 0.05
Nodes (35): 1. Umgebungsvariablen konfigurieren, 2. Abhängigkeiten installieren, 3. Dienste starten, 📄 Danksagung, 1. Configure Environment Variables, 1. Wuhan University Public Opinion Simulation + MiroFish Project Introduction, 2. Dream of the Red Chamber Lost Ending Simulation, 2. Install Dependencies (+27 more)

### Community 16 - "SimulationView.vue"
Cohesion: 0.10
Nodes (24): closeSimulationEnv(), getEnvStatus(), stopSimulation(), addLog(), checkAndStopRunningSimulation(), currentSimulationId, currentStatus, forceStopSimulation() (+16 more)

### Community 18 - "run_reddit_simulation"
Cohesion: 0.10
Nodes (7): PlatformActionLogger, create_model(), get_active_agents_for_round(), get_agent_names_from_config(), PlatformSimulation, run_reddit_simulation(), run_twitter_simulation()

### Community 21 - "IPCResponse"
Cohesion: 0.10
Nodes (5): CommandStatus, CommandType, IPCCommand, IPCResponse, SimulationIPCServer

### Community 22 - "error"
Cohesion: 0.09
Nodes (19): chat_with_report_agent(), check_report_status(), delete_report(), generate_report(), get_agent_log(), get_console_log(), get_generate_status(), get_graph_statistics_tool() (+11 more)

### Community 23 - "SimulationRunView.vue"
Cohesion: 0.09
Nodes (27): getSimulation(), getSimulationConfig(), addLog(), currentSimulationId, currentStatus, graphData, graphLoading, handleGoBack() (+19 more)

### Community 24 - "run_reddit_simulation.py"
Cohesion: 0.12
Nodes (4): CommandType, MaxTokensWarningFilter, CommandType, MaxTokensWarningFilter

### Community 27 - "HistoryDatabase.vue"
Cohesion: 0.08
Nodes (11): getSimulationHistory(), containerStyle, historyContainer, hoveringCard, isExpanded, loadHistory(), loading, projects (+3 more)

### Community 28 - "interview_agent"
Cohesion: 0.25
Nodes (4): interview_agent(), interview_agents_batch(), interview_all_agents(), optimize_interview_prompt()

### Community 29 - "Home.vue"
Cohesion: 0.09
Nodes (17): addFiles(), canSubmit, configData, fileInput, files, formData, handleDrop(), handleFileSelect() (+9 more)

### Community 30 - "ReportView.vue"
Cohesion: 0.11
Nodes (19): addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph(), loadReportData() (+11 more)

### Community 31 - "ReportManager"
Cohesion: 0.13
Nodes (3): download_report(), get_report_sections(), ReportManager

### Community 33 - "frontend/package.json"
Cohesion: 0.10
Nodes (20): dependencies, axios, d3, vue, vue-router, devDependencies, vite, @vitejs/plugin-vue (+12 more)

### Community 34 - "InteractionView.vue"
Cohesion: 0.11
Nodes (19): addLog(), currentReportId, currentStatus, graphData, graphLoading, leftPanelStyle, loadGraph(), loadReportData() (+11 more)

### Community 40 - "simulation.js"
Cohesion: 0.12
Nodes (9): createSimulation(), prepareSimulation(), creatingSimulation, graphStats, handleEnterEnvSetup(), logContent, props, router (+1 more)

### Community 41 - "package.json"
Cohesion: 0.11
Nodes (17): description, devDependencies, concurrently, engines, node, license, name, scripts (+9 more)

### Community 44 - "ZepEntityReader"
Cohesion: 0.12
Nodes (4): generate_profiles(), get_entities_by_type(), get_entity_detail(), ZepEntityReader

### Community 46 - "retry.py"
Cohesion: 0.12
Nodes (6): retry_with_backoff(), retry_with_backoff_async(), decorator(), decorator(), wrapper(), RetryableAPIClient

### Community 47 - "GraphPanel.vue"
Cohesion: 0.12
Nodes (12): emit, entityTypes, expandedSelfLoops, graphContainer, graphSvg, handleResize(), props, renderGraph() (+4 more)

### Community 48 - "services/__init__.py"
Cohesion: 0.07
Nodes (7): OntologyGenerator, PlatformConfig, TimeSimulationConfig, RoundSummary, RunnerStatus, FilteredEntities, LLMClient

### Community 54 - "getProject"
Cohesion: 0.42
Nodes (8): buildGraph(), generateOntology(), getGraphData(), getProject(), getTaskStatus(), requestWithRetry(), service, fetchGraphData()

### Community 58 - "OasisAgentProfile"
Cohesion: 0.18
Nodes (3): OasisAgentProfile, show_expected_formats(), test_profile_formats()

### Community 62 - ".get_all_nodes"
Cohesion: 0.31
Nodes (4): NodeInfo, get_entity_summary(), get_graph_statistics(), get_simulation_context()

### Community 70 - "run_parallel_simulation.py"
Cohesion: 0.08
Nodes (12): CommandType, disable_oasis_logging(), _enrich_action_context(), fetch_new_actions_from_db(), _get_comment_info(), _get_post_info(), _get_user_name(), init_logging_for_simulation() (+4 more)

### Community 71 - "fetchAgentLog"
Cohesion: 0.29
Nodes (7): getConsoleLog(), addLog(), emit, fetchAgentLog(), fetchConsoleLog(), startPolling(), stopPolling()

### Community 77 - "addLog"
Cohesion: 0.21
Nodes (13): getSimulationProfilesRealtime(), interviewAgents(), addLog(), emit, loadProfiles(), saveChatHistory(), scrollToBottom(), selectAgent() (+5 more)

### Community 78 - "zep_paging.py"
Cohesion: 0.24
Nodes (3): fetch_all_edges(), fetch_all_nodes(), _fetch_page_with_retry()

### Community 79 - "loadProject"
Cohesion: 0.31
Nodes (10): error, initProject(), loadGraph(), loadProject(), pollTaskStatus(), startBuildGraph(), startPollingTask(), stopGraphPolling() (+2 more)

### Community 80 - "vue"
Cohesion: 0.29
Nodes (5): app, router, routes, vue, vue-router

### Community 81 - "report.js"
Cohesion: 0.33
Nodes (5): chatWithReport(), getAgentLog(), getReport(), loadAgentLogs(), loadReportData()

### Community 82 - "pendingUpload.js"
Cohesion: 0.33
Nodes (5): clearPendingUpload(), getPendingUpload(), state, startSimulation(), handleNewProject()

### Community 85 - "closeModal"
Cohesion: 0.50
Nodes (4): closeModal(), goToProject(), goToReport(), goToSimulation()

### Community 92 - "fetchStatus"
Cohesion: 0.67
Nodes (3): error, fetchStatus(), saveSettings()

## Knowledge Gaps
- **291 isolated node(s):** `mirofish-backend`, `name`, `private`, `version`, `type` (+286 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 981 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **54 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Config` connect `Config` to `._generate_profile_with_llm`, `SimulationRunner`, `simulation.py`, `MemoryProvider`, `graph.py`, `ProjectManager`, `SimulationConfigGenerator`, `GraphBuilderService`, `ObsidianMemoryProvider`, `ZepEntityReader`, `system.py`, `ZepToolsService`, `services/__init__.py`, `ZepMemoryProvider`, `ReportLogger`, `error`, `OasisProfileGenerator`, `ReportManager`?**
  _High betweenness centrality (0.106) - this node is a cross-community bridge._
- **Are the 27 inferred relationships involving `Config` (e.g. with `allowed_file()` and `build_graph()`) actually correct?**
  _`Config` has 27 INFERRED edges - model-reasoned connections that need verification._
- **What connects `mirofish-backend`, `name`, `private` to the rest of the system?**
  _291 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Config` be split into smaller, more focused modules?**
  _Cohesion score 0.0782472613458529 - nodes in this community are weakly interconnected._
- **Why does `OasisProfileGenerator` connect `OasisProfileGenerator` to `Config`, `._generate_profile_with_llm`, `simulation.py`, `._search_zep_for_entity`, `SimulationConfigGenerator`, `ZepEntityReader`, `system.py`, `services/__init__.py`, `.generate_profile_from_entity`, `OasisAgentProfile`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `SimulationRunner` (e.g. with `close_simulation_env()` and `get_agent_stats()`) actually correct?**
  _`SimulationRunner` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Should `SimulationRunner` be split into smaller, more focused modules?**
  _Cohesion score 0.042758205359831374 - nodes in this community are weakly interconnected._