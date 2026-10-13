<template>
  <div class="report-panel">
    <!-- Main Split Layout -->
    <div class="main-split-layout">
      <!-- LEFT PANEL: Report Style -->
      <div class="left-panel report-style" ref="leftPanel">
        <div v-if="reportOutline" class="article-shell">
          <nav class="report-toc" :aria-label="$t('step4.contents')">
            <p class="toc-label">{{ $t('step4.contents') }}</p>
            <ol class="toc-list">
              <li v-for="(section, idx) in reportOutline.sections" :key="'toc-' + idx">
                <button
                  type="button"
                  class="toc-link"
                  :class="{ 'is-current': activeTocIndex === idx }"
                  @click="scrollToSection(idx)"
                >
                  <span class="toc-num">{{ String(idx + 1).padStart(2, '0') }}</span>
                  <span class="toc-title">{{ section.title }}</span>
                </button>
              </li>
            </ol>
          </nav>

          <div class="report-content-wrapper">
          <!-- Report Header -->
          <header class="report-header-block">
            <div class="report-meta">
              <span class="report-tag">{{ $t('step4.vorhersagebericht') }}</span>
              <span v-if="runCountLabel" class="report-run-hint">{{ runCountLabel }}</span>
            </div>
            <h1 class="main-title">{{ reportOutline.title }}</h1>
            <p class="sub-title">{{ reportOutline.summary }}</p>
            <div class="report-actions">
              <a
                class="report-action"
                :href="`/api/report/${reportId}/download`"
                download
              >{{ $t('step4.downloadMarkdown') }}</a>
              <button type="button" class="report-action" @click="printReport">
                {{ $t('step4.printPdf') }}
              </button>
              <button
                v-if="isComplete && simulationId"
                type="button"
                class="report-action"
                @click="openEnsembleSheet"
              >{{ $t('ensemble.start') }}</button>
            </div>
          </header>

          <!-- Sections List -->
          <div class="sections-list">
            <div 
              v-for="(section, idx) in reportOutline.sections" 
              :key="idx"
              :id="'report-section-' + idx"
              class="report-section-item"
              :class="{ 
                'is-active': currentSectionIndex === idx + 1,
                'is-completed': isSectionCompleted(idx + 1),
                'is-pending': !isSectionCompleted(idx + 1) && currentSectionIndex !== idx + 1
              }"
            >
              <div class="section-header-row" @click="toggleSectionCollapse(idx)" :class="{ 'clickable': isSectionCompleted(idx + 1) }">
                <span class="section-number">{{ String(idx + 1).padStart(2, '0') }}</span>
                <h2 class="section-title">{{ section.title }}</h2>
                <button
                  v-if="isSectionCompleted(idx + 1)"
                  type="button"
                  class="collapse-toggle"
                  :aria-expanded="!collapsedSections.has(idx)"
                  :aria-label="collapsedSections.has(idx) ? $t('step4.expandSection') : $t('step4.collapseSection')"
                  @click.stop="toggleSectionCollapse(idx)"
                >
                  <svg 
                    class="collapse-icon" 
                    :class="{ 'is-collapsed': collapsedSections.has(idx) }"
                    viewBox="0 0 24 24" 
                    width="20" 
                    height="20" 
                    fill="none" 
                    stroke="currentColor" 
                    stroke-width="2"
                    aria-hidden="true"
                  >
                    <polyline points="6 9 12 15 18 9"></polyline>
                  </svg>
                </button>
              </div>
              
              <div class="section-body" v-show="!collapsedSections.has(idx)">
                <!-- Completed Content -->
                <div v-if="generatedSections[idx + 1]" class="generated-content" v-html="renderMarkdown(generatedSections[idx + 1])"></div>
                
                <!-- Loading State -->
                <div v-else-if="currentSectionIndex === idx + 1" class="loading-state">
                  <div class="loading-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <circle cx="12" cy="12" r="10" stroke-width="4" stroke="var(--color-border-default)"></circle>
                      <path d="M12 2a10 10 0 0 1 10 10" stroke-width="4" stroke="var(--color-text-secondary)" stroke-linecap="round"></path>
                    </svg>
                  </div>
                  <span class="loading-text">{{ section.title }} {{ $t('step4.wirdGeneriert') }}</span>
                </div>
              </div>
            </div>

            <!-- V1: Methodik und Grenzen (deterministisch) -->
            <aside v-if="methodology && isComplete" class="methodology-card" aria-labelledby="methodology-heading">
              <h2 id="methodology-heading" class="methodology-title">{{ $t('step4.methodologyTitle') }}</h2>
              <p class="methodology-disclaimer">{{ methodology.disclaimer || $t('step4.methodologyDisclaimer') }}</p>
              <ul class="methodology-list">
                <li>{{ $t('step4.methodologyRuns', { count: methodology.run_count ?? 1 }) }}</li>
                <li>{{ $t('step4.methodologyAgents', { count: methodology.agent_count ?? 0, types: agentTypesLabel }) }}</li>
                <li>{{ $t('step4.methodologyTime', { hours: methodology.simulation_hours ?? 0, rounds: methodology.simulation_rounds ?? 0 }) }}</li>
                <li v-for="(plat, name) in (methodology.platform_activity || {})" :key="name">
                  {{ $t('step4.methodologyPlatform', { platform: name, posts: plat.posts ?? 0, comments: plat.comments ?? 0, actions: plat.actions ?? 0 }) }}
                </li>
                <li>{{ $t('step4.methodologyModels', { main: methodology.models?.main || '—', agents: methodology.models?.agents || '—' }) }}</li>
                <li>{{ $t('step4.methodologyInitialPosts', { count: methodology.initial_posts_count ?? 0 }) }}</li>
                <li>{{ $t('step4.methodologySeed', { seed: methodology.seed != null ? methodology.seed : $t('step4.methodologySeedMissing') }) }}</li>
                <li v-if="methodology.timestamp">{{ $t('step4.methodologyTimestamp', { time: methodology.timestamp }) }}</li>
              </ul>
              <div v-if="(methodology.already_in_material || []).length" class="methodology-material">
                <h3 class="methodology-subtitle">{{ $t('step4.methodologyAlreadyInMaterial') }}</h3>
                <ul>
                  <li v-for="(item, i) in methodology.already_in_material" :key="i" class="material-item">
                    <p class="material-item__claim">
                      <span class="methodology-overlap mono">{{ Math.round(((item.overlap ?? item.coverage ?? item.ratio) || 0) * 100) }}%</span>
                      {{ item.claim || item.text }}
                      <span v-if="item.count > 1" class="material-item__count">×{{ item.count }}</span>
                    </p>
                    <p v-if="item.source" class="material-item__source">{{ $t('step4.methodologyMaterialSource', { source: item.source }) }}</p>
                    <details v-if="item.snippet" class="material-item__snip">
                      <summary>{{ $t('step4.methodologyMaterialSnippet') }}</summary>
                      <p>{{ item.snippet }}</p>
                    </details>
                  </li>
                </ul>
              </div>
              <div v-if="ensembleList.length" class="ensemble-list">
                <h3 class="methodology-subtitle">{{ $t('ensemble.listTitle') }}</h3>
                <ul>
                  <li v-for="ens in ensembleList" :key="ens.ensemble_id">
                    <router-link :to="{ name: 'Ensemble', params: { ensembleId: ens.ensemble_id } }">
                      {{ ens.ensemble_id }}
                      <span class="muted">· {{ $t('ensemble.status.' + (ens.status || 'queued')) }} · {{ ens.runs }}×{{ ens.hours }}h</span>
                    </router-link>
                  </li>
                </ul>
              </div>
            </aside>
          </div>
          </div>
        </div>

        <!-- Waiting State -->
        <div v-if="!reportOutline" class="waiting-placeholder">
          <div class="waiting-animation">
            <div class="waiting-ring"></div>
            <div class="waiting-ring"></div>
            <div class="waiting-ring"></div>
          </div>
          <span class="waiting-text">{{ $t('step4.wartenAufBerichtsAgent') }}</span>
        </div>
      </div>
    </div>

    <details class="report-origin">
      <summary class="report-origin-summary">{{ $t('step4.howItWasMade') }}</summary>
      <div class="origin-body">
      <!-- RIGHT PANEL: Workflow Timeline -->
      <div class="right-panel" ref="rightPanel">
        <div class="panel-header" :class="`panel-header--${activeStep.status}`" v-if="!isComplete">
          <span class="header-dot" v-if="activeStep.status === 'active'"></span>
          <span class="header-index mono">{{ activeStep.noLabel }}</span>
          <span class="header-title">{{ activeStep.title }}</span>
          <span class="header-meta mono" v-if="activeStep.meta">{{ activeStep.meta }}</span>
        </div>

        <!-- Workflow Overview (flat, status-based palette) -->
        <div class="workflow-overview" v-if="agentLogs.length > 0 || reportOutline">
          <div class="workflow-metrics">
            <div class="metric">
              <span class="metric-label">{{ $t('step4.abschnitte') }}</span>
              <span class="metric-value mono">{{ completedSections }}/{{ totalSections }}</span>
            </div>
            <div class="metric">
              <span class="metric-label">{{ $t('step4.vergangen') }}</span>
              <span class="metric-value mono">{{ formatElapsedTime }}</span>
            </div>
            <div class="metric">
              <span class="metric-label">{{ $t('step4.werkzeuge') }}</span>
              <span class="metric-value mono">{{ totalToolCalls }}</span>
            </div>
            <div class="metric metric-right">
              <span class="metric-pill" :class="`pill--${statusClass}`">{{ statusText }}</span>
            </div>
          </div>

          <div class="workflow-steps" v-if="workflowSteps.length > 0">
            <div
              v-for="(step, sidx) in workflowSteps"
              :key="step.key"
              class="wf-step"
              :class="`wf-step--${step.status}`"
            >
              <div class="wf-step-connector">
                <div class="wf-step-dot"></div>
                <div class="wf-step-line" v-if="sidx < workflowSteps.length - 1"></div>
              </div>

              <div class="wf-step-content">
                <div class="wf-step-title-row">
                  <span class="wf-step-index mono">{{ step.noLabel }}</span>
                  <span class="wf-step-title">{{ step.title }}</span>
                  <span class="wf-step-meta mono" v-if="step.meta">{{ step.meta }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Nächster Schritt Button - nach Abschluss anzeigen -->
          <button v-if="isComplete" class="next-step-btn" @click="goToInteraction">
            <span>{{ $t('step4.zurTiefeninteraktion') }}</span>
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="5" y1="12" x2="19" y2="12"></line>
              <polyline points="12 5 19 12 12 19"></polyline>
            </svg>
          </button>

          <div class="workflow-divider"></div>
        </div>

        <div class="workflow-timeline">
          <TransitionGroup name="timeline-item">
            <div 
              v-for="(log, idx) in displayLogs" 
              :key="log.timestamp + '-' + idx"
              class="timeline-item"
              :class="getTimelineItemClass(log, idx, displayLogs.length)"
            >
              <!-- Timeline Connector -->
              <div class="timeline-connector">
                <div class="connector-dot" :class="getConnectorClass(log, idx, displayLogs.length)"></div>
                <div class="connector-line" v-if="idx < displayLogs.length - 1"></div>
              </div>
              
              <!-- Timeline Content -->
              <div class="timeline-content">
                <div class="timeline-header">
                  <span class="action-label">{{ getActionLabel(log.action) }}</span>
                  <span class="action-time">{{ formatTime(log.timestamp) }}</span>
                </div>
                
                <!-- Action Body - Different for each type -->
                <div class="timeline-body" :class="{ 'collapsed': isLogCollapsed(log) }" @click="toggleLogExpand(log)">
                  
                  <!-- Report Start -->
                  <template v-if="log.action === 'report_start'">
                    <div class="info-row">
                      <span class="info-key">{{ $t('step4.simulation') }}</span>
                      <span class="info-val mono">{{ log.details?.simulation_id }}</span>
                    </div>
                    <div class="info-row" v-if="log.details?.simulation_requirement">
                      <span class="info-key">{{ $t('step4.anforderung') }}</span>
                      <span class="info-val">{{ log.details.simulation_requirement }}</span>
                    </div>
                  </template>

                  <!-- Planning -->
                  <template v-if="log.action === 'planning_start'">
                    <div class="status-message planning">{{ log.details?.message }}</div>
                  </template>
                  <template v-if="log.action === 'planning_complete'">
                    <div class="status-message success">{{ log.details?.message }}</div>
                    <div class="outline-badge" v-if="log.details?.outline">
                      {{ log.details.outline.sections?.length || 0 }} Abschnitte geplant
                    </div>
                  </template>

                  <!-- Section Start -->
                  <template v-if="log.action === 'section_start'">
                    <div class="section-tag">
                      <span class="tag-num">#{{ log.section_index }}</span>
                      <span class="tag-title">{{ log.section_title }}</span>
                    </div>
                  </template>
                  
                  <!-- Abschnittsinhalt generiert (Inhalt erstellt, aber Abschnitt evtl. noch nicht abgeschlossen) -->
                  <template v-if="log.action === 'section_content'">
                    <div class="section-tag content-ready">
                      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 20h9"></path>
                        <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
                      </svg>
                      <span class="tag-title">{{ log.section_title }}</span>
                    </div>
                  </template>

                  <!-- Abschnitt abgeschlossen (Abschnittsgenerierung abgeschlossen) -->
                  <template v-if="log.action === 'section_complete'">
                    <div class="section-tag completed">
                      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"></polyline>
                      </svg>
                      <span class="tag-title">{{ log.section_title }}</span>
                    </div>
                  </template>

                  <!-- Tool Call -->
                  <template v-if="log.action === 'tool_call'">
                    <div class="tool-badge" :class="'tool-' + getToolColor(log.details?.tool_name)">
                      <!-- Deep Insight - Lightbulb -->
                      <svg v-if="getToolIcon(log.details?.tool_name) === 'lightbulb'" class="tool-icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12.5V17a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-2.5A7 7 0 0 0 12 2z"></path>
                      </svg>
                      <!-- Panorama Search - Globe -->
                      <svg v-else-if="getToolIcon(log.details?.tool_name) === 'globe'" class="tool-icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
                      </svg>
                      <!-- Agent Interview - Users -->
                      <svg v-else-if="getToolIcon(log.details?.tool_name) === 'users'" class="tool-icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                        <circle cx="9" cy="7" r="4"></circle>
                        <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"></path>
                      </svg>
                      <!-- Quick Search - Zap -->
                      <svg v-else-if="getToolIcon(log.details?.tool_name) === 'zap'" class="tool-icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
                      </svg>
                      <!-- Graph Stats - Chart -->
                      <svg v-else-if="getToolIcon(log.details?.tool_name) === 'chart'" class="tool-icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="20" x2="18" y2="10"></line>
                        <line x1="12" y1="20" x2="12" y2="4"></line>
                        <line x1="6" y1="20" x2="6" y2="14"></line>
                      </svg>
                      <!-- Entity Query - Database -->
                      <svg v-else-if="getToolIcon(log.details?.tool_name) === 'database'" class="tool-icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                        <ellipse cx="12" cy="5" rx="9" ry="3"></ellipse>
                        <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path>
                        <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path>
                      </svg>
                      <!-- Default - Tool -->
                      <svg v-else class="tool-icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path>
                      </svg>
                      {{ getToolDisplayName(log.details?.tool_name) }}
                    </div>
                    <div v-if="log.details?.parameters && expandedLogs.has(log.timestamp)" class="tool-params">
                      <pre>{{ formatParams(log.details.parameters) }}</pre>
                    </div>
                  </template>

                  <!-- Tool Result -->
                  <template v-if="log.action === 'tool_result'">
                    <div class="result-wrapper" :class="'result-' + log.details?.tool_name">
                      <!-- Hide result-meta for tools that show stats in their own header -->
                      <div v-if="!['interview_agents', 'insight_forge', 'panorama_search', 'quick_search'].includes(log.details?.tool_name)" class="result-meta">
                        <span class="result-tool">{{ getToolDisplayName(log.details?.tool_name) }}</span>
                        <span class="result-size">{{ formatResultSize(log.details?.result_length) }}</span>
                      </div>
                      
                      <!-- Structured Result Display -->
                      <div v-if="!showRawResult[log.timestamp]" class="result-structured">
                        <!-- Interview Agents - Special Display -->
                        <template v-if="log.details?.tool_name === 'interview_agents'">
                          <InterviewDisplay :result="parseInterview(log.details.result)" :result-length="log.details?.result_length" />
                        </template>
                        
                        <!-- Insight Forge -->
                        <template v-else-if="log.details?.tool_name === 'insight_forge'">
                          <InsightDisplay :result="parseInsightForge(log.details.result)" :result-length="log.details?.result_length" />
                        </template>
                        
                        <!-- Panorama Search -->
                        <template v-else-if="log.details?.tool_name === 'panorama_search'">
                          <PanoramaDisplay :result="parsePanorama(log.details.result)" :result-length="log.details?.result_length" />
                        </template>
                        
                        <!-- Quick Search -->
                        <template v-else-if="log.details?.tool_name === 'quick_search'">
                          <QuickSearchDisplay :result="parseQuickSearch(log.details.result)" :result-length="log.details?.result_length" />
                        </template>
                        
                        <!-- Default -->
                        <template v-else>
                          <pre class="raw-preview">{{ truncateText(log.details?.result, 300) }}</pre>
                        </template>
                      </div>
                      
                      <!-- Raw Result -->
                      <div v-else class="result-raw">
                        <pre>{{ log.details?.result }}</pre>
                      </div>
                    </div>
                  </template>

                  <!-- LLM Response -->
                  <template v-if="log.action === 'llm_response'">
                    <div class="llm-meta">
                      <span class="meta-tag">{{ $t('step4.iteration', { count: log.details?.iteration }) }}</span>
                      <span class="meta-tag" :class="{ active: log.details?.has_tool_calls }">
                        {{ $t('step4.toolsValue', { value: log.details?.has_tool_calls ? $t('step4.yes') : $t('step4.no') }) }}
                      </span>
                      <span class="meta-tag" :class="{ active: log.details?.has_final_answer, 'final-answer': log.details?.has_final_answer }">
                        {{ $t('step4.finalAnswerValue', { value: log.details?.has_final_answer ? $t('step4.yes') : $t('step4.no') }) }}
                      </span>
                    </div>
                    <!-- Bei Endantwort spezielle Benachrichtigung anzeigen -->
                    <div v-if="log.details?.has_final_answer" class="final-answer-hint">
                      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"></polyline>
                      </svg>
                      <span>{{ $t('step4.sectionContentGenerated', { title: log.section_title }) }}</span>
                    </div>
                    <div v-if="expandedLogs.has(log.timestamp) && log.details?.response" class="llm-content">
                      <pre>{{ log.details.response }}</pre>
                    </div>
                  </template>

                  <!-- Report Complete -->
                  <template v-if="log.action === 'report_complete'">
                    <div class="complete-banner">
                      <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                        <polyline points="22 4 12 14.01 9 11.01"></polyline>
                      </svg>
                      <span>{{ $t('step4.reportGenerationCompleted') }}</span>
                    </div>
                  </template>
                </div>

                <!-- Footer: Elapsed Time + Action Buttons -->
                <div class="timeline-footer" v-if="log.elapsed_seconds || (log.action === 'tool_call' && log.details?.parameters) || log.action === 'tool_result' || (log.action === 'llm_response' && log.details?.response)">
                  <span v-if="log.elapsed_seconds" class="elapsed-badge">+{{ log.elapsed_seconds.toFixed(1) }}s</span>
                  <span v-else class="elapsed-placeholder"></span>
                  
                  <div class="footer-actions">
                    <!-- Tool Call: Show/Hide Params -->
                    <button v-if="log.action === 'tool_call' && log.details?.parameters" class="action-btn" @click.stop="toggleLogExpand(log)">
                      {{ expandedLogs.has(log.timestamp) ? $t('step4.hideParameters') : $t('step4.showParameters') }}
                    </button>
                    
                    <!-- Tool Result: Raw/Structured View -->
                    <button v-if="log.action === 'tool_result'" class="action-btn" @click.stop="toggleRawResult(log.timestamp, $event)">
                      {{ showRawResult[log.timestamp] ? $t('step4.structuredView') : $t('step4.rawData') }}
                    </button>
                    
                    <!-- LLM Response: Show/Hide Response -->
                    <button v-if="log.action === 'llm_response' && log.details?.response" class="action-btn" @click.stop="toggleLogExpand(log)">
                      {{ expandedLogs.has(log.timestamp) ? $t('step4.hideResponse') : $t('step4.showResponse') }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </TransitionGroup>

          <!-- Empty State -->
          <div v-if="agentLogs.length === 0 && !isComplete" class="workflow-empty">
            <div class="empty-pulse"></div>
            <span>{{ $t('step4.waitingForAgentActivity') }}</span>
          </div>
        </div>
      </div>
      </div>
    </details>

    <!-- Bottom Console Logs – Desktop eingeklappt -->
    <details class="console-logs">
      <summary>{{ $t('common.showProtocol') }}</summary>
      <div class="log-content" ref="logContent">
        <div class="log-line" v-for="(log, idx) in consoleLogs" :key="idx">
          <span class="log-msg" :class="getLogLevelClass(log)">{{ log }}</span>
        </div>
      </div>
    </details>
    <MobileStickyBar
      v-if="isComplete"
      :primary-label="$t('step4.zurTiefeninteraktion')"
      :secondary-label="simulationId ? $t('ensemble.startShort') : ''"
      @primary-click="goToInteraction"
      @secondary-click="openEnsembleSheet"
    />

    <ConfirmSheet
      :open="ensembleSheetOpen"
      :title="t('ensemble.startTitle')"
      :text="t('ensemble.startHint')"
      :confirm-label="t('ensemble.startConfirm')"
      :busy="ensembleStarting"
      @confirm="startEnsembleRun"
      @close="ensembleSheetOpen = false"
    >
      <div class="ens-form">
        <fieldset class="ens-field">
          <legend>{{ t('ensemble.runsLabel') }}</legend>
          <div class="ens-pills">
            <button
              v-for="n in [5, 10, 20]"
              :key="n"
              type="button"
              class="ens-pill"
              :class="{ 'is-on': ensembleRuns === n }"
              @click="ensembleRuns = n"
            >{{ n }}</button>
          </div>
        </fieldset>
        <label class="ens-field">
          <span>{{ t('ensemble.hoursLabel') }}</span>
          <input v-model.number="ensembleHours" type="number" min="1" max="168" class="ens-input" />
        </label>
        <fieldset class="ens-field">
          <legend>{{ t('ensemble.variantsLabel') }}</legend>
          <label class="ens-check"><input type="checkbox" checked disabled /> {{ t('ensemble.variantBaseline') }}</label>
          <label class="ens-check"><input v-model="ensembleIsolated" type="checkbox" /> {{ t('ensemble.variantIsolated') }}</label>
          <label class="ens-check"><input v-model="ensembleNull" type="checkbox" /> {{ t('ensemble.variantNull') }}</label>
          <label v-for="at in agentTypeOptions" :key="at" class="ens-check">
            <input v-model="ensembleWithout" type="checkbox" :value="'without:' + at" />
            {{ t('ensemble.variantWithout', { type: at }) }}
          </label>
        </fieldset>
        <fieldset class="ens-field ens-custom">
          <legend>{{ t('ensemble.customQuestionsTitle') }}</legend>
          <p class="ens-custom__hint">{{ t('ensemble.customQuestionsHint') }}</p>
          <div v-for="(row, i) in customOutcomes" :key="i" class="ens-custom__row">
            <label class="ens-custom__text">
              <span class="sr-only">{{ t('ensemble.customQuestionLabel', { n: i + 1 }) }}</span>
              <input
                v-model="row.text"
                type="text"
                maxlength="200"
                class="ens-custom__input"
                :class="{ 'is-invalid': row.text.trim().length > 200 }"
                :placeholder="t('ensemble.customQuestionPlaceholder')"
              />
              <span class="ens-custom__count" :class="{ 'is-warn': row.text.length >= 180 }">{{ row.text.length }}/200</span>
            </label>
            <div class="ens-custom__polarity" role="group" :aria-label="t('ensemble.customPolarityLabel')">
              <button
                type="button"
                class="ens-pill ens-pill--sm"
                :class="{ 'is-on': row.polarity === 'presence' }"
                @click="row.polarity = 'presence'"
              >{{ t('ensemble.customPolarityPresence') }}</button>
              <button
                type="button"
                class="ens-pill ens-pill--sm"
                :class="{ 'is-on': row.polarity === 'absence' }"
                @click="row.polarity = 'absence'"
              >{{ t('ensemble.customPolarityAbsence') }}</button>
            </div>
            <button
              type="button"
              class="ens-custom__remove"
              :aria-label="t('ensemble.customQuestionsRemove')"
              @click="removeCustomOutcome(i)"
            >×</button>
          </div>
          <button
            v-if="customOutcomes.length < 6"
            type="button"
            class="ens-custom__add"
            @click="addCustomOutcome"
          >{{ t('ensemble.customQuestionsAdd') }}</button>
          <p v-if="customOutcomesError" class="ens-custom__error" role="alert">{{ customOutcomesError }}</p>
        </fieldset>
        <p class="ens-eta">{{ t('ensemble.estimate', { time: estimateLabel }) }}</p>
      </div>
    </ConfirmSheet>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick, h, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { getAgentLog, getConsoleLog, getReport } from '../api/report'
import { startEnsemble, listEnsembles } from '../api/ensemble'
import MobileStickyBar from './MobileStickyBar.vue'
import ConfirmSheet from './ConfirmSheet.vue'

const { t } = useI18n()

const router = useRouter()

const props = defineProps({
  reportId: String,
  simulationId: String,
  systemLogs: Array
})

const emit = defineEmits(['add-log', 'update-status'])

// Navigation
const goToInteraction = () => {
  if (props.reportId) {
    router.push({ name: 'Interaction', params: { reportId: props.reportId } })
  }
}

const printReport = () => {
  window.print()
}

const ensembleSheetOpen = ref(false)
const ensembleStarting = ref(false)
const ensembleRuns = ref(10)
const ensembleHours = ref(24)
const ensembleIsolated = ref(true)
const ensembleNull = ref(true)
const ensembleWithout = ref([])
const ensembleList = ref([])
const customOutcomes = ref([])
const customOutcomesError = ref('')

const addCustomOutcome = () => {
  if (customOutcomes.value.length >= 6) return
  customOutcomes.value.push({ text: '', polarity: 'presence' })
}
const removeCustomOutcome = (i) => {
  customOutcomes.value.splice(i, 1)
  customOutcomesError.value = ''
}
const buildCustomOutcomesPayload = () => {
  const rows = customOutcomes.value
    .map((r) => ({ text_de: (r.text || '').trim(), polarity: r.polarity === 'absence' ? 'absence' : 'presence' }))
    .filter((r) => r.text_de.length > 0)
  if (rows.length > 6) return { error: t('ensemble.customTooMany'), rows: [] }
  if (rows.some((r) => r.text_de.length > 200)) return { error: t('ensemble.customTooLong'), rows: [] }
  return { error: '', rows }
}

const agentTypeOptions = computed(() => {
  const types = methodology.value?.agent_types || []
  return [...new Set(types.map((x) => x.type).filter(Boolean))]
})

const estimateSeconds = computed(() => {
  const variants = 1 + (ensembleIsolated.value ? 1 : 0) + (ensembleNull.value ? 1 : 0) + ensembleWithout.value.length
  // Rough client-side preview; server returns authoritative estimate_seconds
  return Math.max(60, Math.round(ensembleRuns.value * ensembleHours.value * variants * 12))
})

const estimateLabel = computed(() => {
  const s = estimateSeconds.value
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  if (h > 0) return t('ensemble.durationHm', { h, m })
  return t('ensemble.durationM', { m: Math.max(1, m) })
})

const openEnsembleSheet = () => {
  if (!props.simulationId) return
  customOutcomes.value = []
  customOutcomesError.value = ''
  ensembleSheetOpen.value = true
}

const startEnsembleRun = async () => {
  if (!props.simulationId) return
  const { error, rows } = buildCustomOutcomesPayload()
  if (error) {
    customOutcomesError.value = error
    return
  }
  customOutcomesError.value = ''
  ensembleStarting.value = true
  try {
    const variants = ['baseline']
    if (ensembleIsolated.value) variants.push('isolated')
    if (ensembleNull.value) variants.push('null_model')
    variants.push(...ensembleWithout.value)
    const payload = {
      simulation_id: props.simulationId,
      runs: ensembleRuns.value,
      hours: ensembleHours.value,
      variants,
    }
    if (rows.length) payload.custom_outcomes = rows
    const res = await startEnsemble(payload)
    const id = res?.data?.ensemble_id
    ensembleSheetOpen.value = false
    if (id) router.push({ name: 'Ensemble', params: { ensembleId: id } })
  } catch (e) {
    emit('add-log', e.message || String(e))
  } finally {
    ensembleStarting.value = false
  }
}

const loadEnsembleList = async () => {
  if (!props.simulationId) return
  try {
    const res = await listEnsembles(props.simulationId)
    ensembleList.value = Array.isArray(res?.data) ? res.data : []
  } catch (e) {
    ensembleList.value = []
  }
}

watch(
  () => props.simulationId,
  (id) => {
    if (id && isComplete.value) loadEnsembleList()
  },
)

const runCountLabel = computed(() => {
  const n = methodology.value?.run_count
  if (n == null && !isComplete.value) return ''
  const count = n ?? 1
  return count === 1
    ? t('step4.scenarioFromOneRun')
    : t('step4.scenarioFromNRuns', { count })
})

const agentTypesLabel = computed(() => {
  const types = methodology.value?.agent_types || []
  if (!types.length) return '—'
  return types.map((x) => `${x.type} (${x.count})`).join(', ')
})

const loadMethodology = async () => {
  if (!props.reportId) return
  try {
    const res = await getReport(props.reportId)
    const data = res?.data?.methodology != null ? res.data : (res?.data?.data || res?.data)
    if (data?.methodology) {
      methodology.value = data.methodology
    }
    await loadEnsembleList()
  } catch (e) {
    /* Methodik optional — Bericht bleibt lesbar */
  }
}

const activeTocIndex = ref(0)

const scrollToSection = (idx) => {
  activeTocIndex.value = idx
  const el = document.getElementById('report-section-' + idx)
  if (!el) return
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  el.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' })
}

// State
const agentLogs = ref([])
const consoleLogs = ref([])
const agentLogLine = ref(0)
const consoleLogLine = ref(0)
const reportOutline = ref(null)
const currentSectionIndex = ref(null)
const generatedSections = ref({})
const expandedContent = ref(new Set())
const expandedLogs = ref(new Set())
const collapsedSections = ref(new Set())
const isComplete = ref(false)
const methodology = ref(null)
const startTime = ref(null)
const leftPanel = ref(null)
const rightPanel = ref(null)
const logContent = ref(null)
const showRawResult = reactive({})

// Toggle functions
const toggleRawResult = (timestamp, event) => {
  // Position der Schaltfläche relativ zum Viewport speichern
  const button = event?.target
  const buttonRect = button?.getBoundingClientRect()
  const buttonTopBeforeToggle = buttonRect?.top
  
  // Status umschalten
  showRawResult[timestamp] = !showRawResult[timestamp]
  
  // Nach DOM-Aktualisierung Scrollposition anpassen, damit die Schaltfläche an derselben Stelle bleibt
  if (button && buttonTopBeforeToggle !== undefined && rightPanel.value) {
    nextTick(() => {
      const newButtonRect = button.getBoundingClientRect()
      const buttonTopAfterToggle = newButtonRect.top
      const scrollDelta = buttonTopAfterToggle - buttonTopBeforeToggle
      
      // Scrollposition anpassen
      rightPanel.value.scrollTop += scrollDelta
    })
  }
}

const toggleSectionContent = (idx) => {
  if (!generatedSections.value[idx + 1]) return
  const newSet = new Set(expandedContent.value)
  if (newSet.has(idx)) {
    newSet.delete(idx)
  } else {
    newSet.add(idx)
  }
  expandedContent.value = newSet
}

const toggleSectionCollapse = (idx) => {
  // Nur abgeschlossene Abschnitte können eingeklappt werden
  if (!generatedSections.value[idx + 1]) return
  const newSet = new Set(collapsedSections.value)
  if (newSet.has(idx)) {
    newSet.delete(idx)
  } else {
    newSet.add(idx)
  }
  collapsedSections.value = newSet
}

const toggleLogExpand = (log) => {
  const newSet = new Set(expandedLogs.value)
  if (newSet.has(log.timestamp)) {
    newSet.delete(log.timestamp)
  } else {
    newSet.add(log.timestamp)
  }
  expandedLogs.value = newSet
}

const isLogCollapsed = (log) => {
  if (['tool_call', 'tool_result', 'llm_response'].includes(log.action)) {
    return !expandedLogs.value.has(log.timestamp)
  }
  return false
}

// Tool configurations with display names and colors
const toolConfig = {
  'insight_forge': {
    name: t('step4.deepInsight'),
    color: 'purple',
    icon: 'lightbulb' // Glühbirnen-Symbol - steht für Einsicht
  },
  'panorama_search': {
    name: t('step4.panoramaSearchTool'),
    color: 'blue',
    icon: 'globe' // Globus-Symbol - steht für Panoramasuche
  },
  'interview_agents': {
    name: t('step4.agentInterview'),
    color: 'green',
    icon: 'users' // Benutzer-Symbol - steht für Gespräch
  },
  'quick_search': {
    name: t('step4.quickSearchTool'),
    color: 'orange',
    icon: 'zap' // Blitz-Symbol - steht für Schnelligkeit
  },
  'get_graph_statistics': {
    name: t('step4.graphStats'),
    color: 'cyan',
    icon: 'chart' // Diagramm-Symbol - steht für Statistik
  },
  'get_entities_by_type': {
    name: t('step4.entityQuery'),
    color: 'pink',
    icon: 'database' // Datenbank-Symbol - steht für Entitäten
  }
}

const getToolDisplayName = (toolName) => {
  return toolConfig[toolName]?.name || toolName
}

const getToolColor = (toolName) => {
  return toolConfig[toolName]?.color || 'gray'
}

const getToolIcon = (toolName) => {
  return toolConfig[toolName]?.icon || 'tool'
}

// Parse functions
const parseInsightForge = (text) => {
  const result = {
    query: '',
    simulationRequirement: '',
    stats: { facts: 0, entities: 0, relationships: 0 },
    subQueries: [],
    facts: [],
    entities: [],
    relations: []
  }
  
  try {
    // Analysefrage extrahieren
    const queryMatch = text.match(/Analysefrage:\s*(.+?)(?:\n|$)/)
    if (queryMatch) result.query = queryMatch[1].trim()
    
    // Vorhersageszenario extrahieren
    const reqMatch = text.match(/Prognoseszenario:\s*(.+?)(?:\n|$)/)
    if (reqMatch) result.simulationRequirement = reqMatch[1].trim()
    
    // Statistikdaten extrahieren - Format "Relevante Prognose-Fakten: X" abgleichen
    const factMatch = text.match(/Relevante Prognose-Fakten:\s*(\d+)/)
    const entityMatch = text.match(/Beteiligte Entitäten:\s*(\d+)/)
    const relMatch = text.match(/Beziehungsketten:\s*(\d+)/)
    if (factMatch) result.stats.facts = parseInt(factMatch[1])
    if (entityMatch) result.stats.entities = parseInt(entityMatch[1])
    if (relMatch) result.stats.relationships = parseInt(relMatch[1])
    
    // Unterfragen extrahieren - vollständig, ohne Mengenbegrenzung
    const subQSection = text.match(/### Analysierte Teilfragen\n([\s\S]*?)(?=\n###|$)/)
    if (subQSection) {
      const lines = subQSection[1].split('\n').filter(l => l.match(/^\d+\./))
      result.subQueries = lines.map(l => l.replace(/^\d+\.\s*/, '').trim()).filter(Boolean)
    }
    
    // Schlüsselfakten extrahieren - vollständig, ohne Mengenbegrenzung
    const factsSection = text.match(/### 【Wichtige Fakten】[\s\S]*?\n([\s\S]*?)(?=\n###|$)/)
    if (factsSection) {
      const lines = factsSection[1].split('\n').filter(l => l.match(/^\d+\./))
      result.facts = lines.map(l => {
        const match = l.match(/^\d+\.\s*"?(.+?)"?\s*$/)
        return match ? match[1].replace(/^"|"$/g, '').trim() : l.replace(/^\d+\.\s*/, '').trim()
      }).filter(Boolean)
    }
    
    // Kernentitäten extrahieren - vollständig, mit Zusammenfassung und Anzahl zugehöriger Fakten
    const entitySection = text.match(/### 【Kernentitäten】\n([\s\S]*?)(?=\n###|$)/)
    if (entitySection) {
      const entityText = entitySection[1]
      // Entitätsblöcke nach "- **" aufteilen
      const entityBlocks = entityText.split(/\n(?=- \*\*)/).filter(b => b.trim().startsWith('- **'))
      result.entities = entityBlocks.map(block => {
        const nameMatch = block.match(/^-\s*\*\*(.+?)\*\*\s*\((.+?)\)/)
        const summaryMatch = block.match(/Zusammenfassung:\s*"?(.+?)"?(?:\n|$)/)
        const relatedMatch = block.match(/Verwandte Fakten:\s*(\d+)/)
        return {
          name: nameMatch ? nameMatch[1].trim() : '',
          type: nameMatch ? nameMatch[2].trim() : '',
          summary: summaryMatch ? summaryMatch[1].trim() : '',
          relatedFactsCount: relatedMatch ? parseInt(relatedMatch[1]) : 0
        }
      }).filter(e => e.name)
    }
    
    // Beziehungsketten extrahieren - vollständig, ohne Mengenbegrenzung
    const relSection = text.match(/### 【Beziehungsketten】\n([\s\S]*?)(?=\n###|$)/)
    if (relSection) {
      const lines = relSection[1].split('\n').filter(l => l.trim().startsWith('-'))
      result.relations = lines.map(l => {
        const match = l.match(/^-\s*(.+?)\s*--\[(.+?)\]-->\s*(.+)$/)
        if (match) {
          return { source: match[1].trim(), relation: match[2].trim(), target: match[3].trim() }
        }
        return null
      }).filter(Boolean)
    }
  } catch (e) {
    console.warn('Parse insight_forge failed:', e)
  }
  
  return result
}

const parsePanorama = (text) => {
  const result = {
    query: '',
    stats: { nodes: 0, edges: 0, activeFacts: 0, historicalFacts: 0 },
    activeFacts: [],
    historicalFacts: [],
    entities: []
  }
  
  try {
    // Abfrage extrahieren
    const queryMatch = text.match(/Abfrage:\s*(.+?)(?:\n|$)/)
    if (queryMatch) result.query = queryMatch[1].trim()
    
    // Statistikdaten extrahieren
    const nodesMatch = text.match(/Gesamtanzahl der Knoten:\s*(\d+)/)
    const edgesMatch = text.match(/Gesamtanzahl der Kanten:\s*(\d+)/)
    const activeMatch = text.match(/Aktuell gültige Fakten:\s*(\d+)/)
    const histMatch = text.match(/Historische\/abgelaufene Fakten:\s*(\d+)/)
    if (nodesMatch) result.stats.nodes = parseInt(nodesMatch[1])
    if (edgesMatch) result.stats.edges = parseInt(edgesMatch[1])
    if (activeMatch) result.stats.activeFacts = parseInt(activeMatch[1])
    if (histMatch) result.stats.historicalFacts = parseInt(histMatch[1])
    
    // Aktuelle gültige Fakten extrahieren - vollständig, ohne Mengenbegrenzung
    const activeSection = text.match(/### 【Aktuell gültige Fakten】[\s\S]*?\n([\s\S]*?)(?=\n###|$)/)
    if (activeSection) {
      const lines = activeSection[1].split('\n').filter(l => l.match(/^\d+\./))
      result.activeFacts = lines.map(l => {
        // Nummerierung und Anführungszeichen entfernen
        const factText = l.replace(/^\d+\.\s*/, '').replace(/^"|"$/g, '').trim()
        return factText
      }).filter(Boolean)
    }
    
    // Historische/abgelaufene Fakten extrahieren - vollständig, ohne Mengenbegrenzung
    const histSection = text.match(/### 【Historische\/abgelaufene Fakten】[\s\S]*?\n([\s\S]*?)(?=\n###|$)/)
    if (histSection) {
      const lines = histSection[1].split('\n').filter(l => l.match(/^\d+\./))
      result.historicalFacts = lines.map(l => {
        const factText = l.replace(/^\d+\.\s*/, '').replace(/^"|"$/g, '').trim()
        return factText
      }).filter(Boolean)
    }
    
    // Beteiligte Entitäten extrahieren - vollständig, ohne Mengenbegrenzung
    const entitySection = text.match(/### 【Beteiligte Entitäten】\n([\s\S]*?)(?=\n###|$)/)
    if (entitySection) {
      const lines = entitySection[1].split('\n').filter(l => l.trim().startsWith('-'))
      result.entities = lines.map(l => {
        const match = l.match(/^-\s*\*\*(.+?)\*\*\s*\((.+?)\)/)
        if (match) return { name: match[1].trim(), type: match[2].trim() }
        return null
      }).filter(Boolean)
    }
  } catch (e) {
    console.warn('Parse panorama failed:', e)
  }
  
  return result
}

const parseInterview = (text) => {
  const result = {
    topic: '',
    agentCount: '',
    successCount: 0,
    totalCount: 0,
    selectionReason: '',
    interviews: [],
    summary: ''
  }
  
  try {
    // Interviewthema extrahieren
    const topicMatch = text.match(/\*\*Interviewthema:\*\*\s*(.+?)(?:\n|$)/)
    if (topicMatch) result.topic = topicMatch[1].trim()
    
    // Anzahl Interviewter extrahieren (z.B. "5 / 9 simulierte Agenten")
    const countMatch = text.match(/\*\*Anzahl der Interviewten:\*\*\s*(\d+)\s*\/\s*(\d+)/)
    if (countMatch) {
      result.successCount = parseInt(countMatch[1])
      result.totalCount = parseInt(countMatch[2])
      result.agentCount = `${countMatch[1]} / ${countMatch[2]}`
    }
    
    // Auswahlbegründung der Interviewpartner extrahieren
    const reasonMatch = text.match(/### Auswahlgrund der Interviewpartner\n([\s\S]*?)(?=\n---\n|\n### Interviewprotokoll)/)
    if (reasonMatch) {
      result.selectionReason = reasonMatch[1].trim()
    }
    
    // Individuelle Auswahlbegründungen parsen
    const parseIndividualReasons = (reasonText) => {
      const reasons = {}
      if (!reasonText) return reasons
      
      const lines = reasonText.split(/\n+/)
      let currentName = null
      let currentReason = []
      
      for (const line of lines) {
        let headerMatch = null
        let name = null
        let reasonStart = null
        
        // Format 1: Zahl. **Name（index=X）**：Begründung
        // Beispiel: 1. **Alumni_345 (index=1)**: Als Alumnus der Universität...
        headerMatch = line.match(/^\d+\.\s*\*\*([^*（(]+)(?:[（(]index\s*=?\s*\d+[)）])?\*\*[：:]\s*(.*)/)
        if (headerMatch) {
          name = headerMatch[1].trim()
          reasonStart = headerMatch[2]
        }
        
        // Format 2: - Auswahl Name (index X): Begründung  (chinesisch: 选择Name)
        // Beispiel: - Auswahl Eltern_601 (index 0): Als Vertreter der Elterngruppe...
        if (!headerMatch) {
          headerMatch = line.match(/^-\s*(?:选择|Auswahl:?|Ausgewählt:?|Wahl:?)\s*([^（(]+)(?:[（(]index\s*=?\s*\d+[)）])?[：:]\s*(.*)/)
          if (headerMatch) {
            name = headerMatch[1].trim()
            reasonStart = headerMatch[2]
          }
        }
        
        // Format 3: - **Name（index X）**：Begründung
        // Beispiel: - **Eltern_601 (index 0)**: Als Vertreter der Elterngruppe...
        if (!headerMatch) {
          headerMatch = line.match(/^-\s*\*\*([^*（(]+)(?:[（(]index\s*=?\s*\d+[)）])?\*\*[：:]\s*(.*)/)
          if (headerMatch) {
            name = headerMatch[1].trim()
            reasonStart = headerMatch[2]
          }
        }
        
        if (name) {
          // Begründung der vorherigen Person speichern
          if (currentName && currentReason.length > 0) {
            reasons[currentName] = currentReason.join(' ').trim()
          }
          // Neue Person beginnen
          currentName = name
          currentReason = reasonStart ? [reasonStart.trim()] : []
        } else if (currentName && line.trim() && !line.match(/^未选|^综上|^最终选择|^Nicht ausgewählt|^Zusammenfassend|^Fazit|^Endgültige Auswahl/)) {
          // Fortsetzungszeile der Begründung (Abschlussabsätze ausschließen)
          currentReason.push(line.trim())
        }
      }
      
      // Begründung der letzten Person speichern
      if (currentName && currentReason.length > 0) {
        reasons[currentName] = currentReason.join(' ').trim()
      }
      
      return reasons
    }
    
    const individualReasons = parseIndividualReasons(result.selectionReason)
    
    // Jeden Interviewdatensatz extrahieren
    const interviewBlocks = text.split(/#### Interview #\d+:/).slice(1)
    
    interviewBlocks.forEach((block, index) => {
      const interview = {
        num: index + 1,
        title: '',
        name: '',
        role: '',
        bio: '',
        selectionReason: '',
        questions: [],
        twitterAnswer: '',
        redditAnswer: '',
        quotes: []
      }
      
      // Titel extrahieren (z.B. "Student", "Lehrkraft" usw.)
      const titleMatch = block.match(/^(.+?)\n/)
      if (titleMatch) interview.title = titleMatch[1].trim()
      
      // Name und Rolle extrahieren
      const nameRoleMatch = block.match(/\*\*(.+?)\*\*\s*\((.+?)\)/)
      if (nameRoleMatch) {
        interview.name = nameRoleMatch[1].trim()
        interview.role = nameRoleMatch[2].trim()
        // Auswahlbegründung dieser Person setzen
        interview.selectionReason = individualReasons[interview.name] || ''
      }
      
      // Kurzbiografie extrahieren
      const bioMatch = block.match(/_Kurzprofil:\s*([\s\S]*?)_\n/)
      if (bioMatch) {
        interview.bio = bioMatch[1].trim().replace(/\.\.\.$/, '...')
      }
      
      // Fragenliste extrahieren
      const qMatch = block.match(/\*\*Q:\*\*\s*([\s\S]*?)(?=\n\n\*\*A:\*\*|\*\*A:\*\*)/)
      if (qMatch) {
        const qText = qMatch[1].trim()
        // Fragen nach Nummerierung aufteilen
        const questions = qText.split(/\n\d+\.\s+/).filter(q => q.trim())
        if (questions.length > 0) {
          // Wenn die erste Frage mit "1." beginnt, Sonderbehandlung erforderlich
          const firstQ = qText.match(/^1\.\s+(.+)/)
          if (firstQ) {
            interview.questions = [firstQ[1].trim(), ...questions.slice(1).map(q => q.trim())]
          } else {
            interview.questions = questions.map(q => q.trim())
          }
        }
      }
      
      // Antworten extrahieren - nach Twitter und Reddit getrennt
      const answerMatch = block.match(/\*\*A:\*\*\s*([\s\S]*?)(?=\*\*Key Quote|$)/)
      if (answerMatch) {
        const answerText = answerMatch[1].trim()
        
        // Twitter- und Reddit-Antworten trennen
        const twitterMatch = answerText.match(/【Twitter Plattform-Antwort】\n?([\s\S]*?)(?=【Reddit Plattform-Antwort】|$)/)
        const redditMatch = answerText.match(/【Reddit Plattform-Antwort】\n?([\s\S]*?)$/)
        
        if (twitterMatch) {
          interview.twitterAnswer = twitterMatch[1].trim()
        }
        if (redditMatch) {
          interview.redditAnswer = redditMatch[1].trim()
        }
        
        // Plattform-Fallback-Logik (Kompatibilität mit altem Format: nur eine Plattformmarkierung)
        if (!twitterMatch && redditMatch) {
          // Nur Reddit-Antwort vorhanden, nur bei echtem Text als Standard kopieren
          if (interview.redditAnswer && interview.redditAnswer !== '(Keine Antwort auf dieser Plattform)') {
            interview.twitterAnswer = interview.redditAnswer
          }
        } else if (twitterMatch && !redditMatch) {
          if (interview.twitterAnswer && interview.twitterAnswer !== '(Keine Antwort auf dieser Plattform)') {
            interview.redditAnswer = interview.twitterAnswer
          }
        } else if (!twitterMatch && !redditMatch) {
          // Keine Plattformmarkierung (sehr altes Format), Gesamttext als Antwort
          interview.twitterAnswer = answerText
        }
      }
      
      // Schlüsselzitate extrahieren (kompatibel mit verschiedenen Anführungszeichenformaten)
      const quotesMatch = block.match(/\*\*Key Quote:\*\*\n([\s\S]*?)(?=\n---|\n####|$)/)
      if (quotesMatch) {
        const quotesText = quotesMatch[1]
        // Bevorzugt > "text" Format abgleichen
        let quoteMatches = quotesText.match(/> "([^"]+)"/g)
        // Fallback: > “text” (chinesische Anführungszeichen) abgleichen
        if (!quoteMatches) {
          quoteMatches = quotesText.match(/> [\u201C"]([^\u201D"]+)[\u201D"]/g)
        }
        if (quoteMatches) {
          interview.quotes = quoteMatches
            .map(q => q.replace(/^> [\u201C"]|[\u201D"]$/g, '').trim())
            .filter(q => q)
        }
      }
      
      if (interview.name || interview.title) {
        result.interviews.push(interview)
      }
    })
    
    // Interviewzusammenfassung extrahieren
    const summaryMatch = text.match(/### Interview-Zusammenfassung und Kernpunkte\n([\s\S]*?)$/)
    if (summaryMatch) {
      result.summary = summaryMatch[1].trim()
    }
  } catch (e) {
    console.warn('Parse interview failed:', e)
  }
  
  return result
}

const parseQuickSearch = (text) => {
  const result = {
    query: '',
    count: 0,
    facts: [],
    edges: [],
    nodes: []
  }
  
  try {
    // Suchabfrage extrahieren
    const queryMatch = text.match(/Suchanfrage:\s*(.+?)(?:\n|$)/)
    if (queryMatch) result.query = queryMatch[1].trim()
    
    // Ergebnisanzahl extrahieren
    const countMatch = text.match(/Gefunden\s*(\d+)\s*Einträge/)
    if (countMatch) result.count = parseInt(countMatch[1])
    
    // Relevante Fakten extrahieren - vollständig, ohne Mengenbegrenzung
    const factsSection = text.match(/### Relevante Fakten:\n([\s\S]*)$/)
    if (factsSection) {
      const lines = factsSection[1].split('\n').filter(l => l.match(/^\d+\./))
      result.facts = lines.map(l => l.replace(/^\d+\.\s*/, '').trim()).filter(Boolean)
    }
    
    // Kanteninformationen extrahieren (falls vorhanden)
    const edgesSection = text.match(/### Relevante Kanten:\n([\s\S]*?)(?=\n###|$)/)
    if (edgesSection) {
      const lines = edgesSection[1].split('\n').filter(l => l.trim().startsWith('-'))
      result.edges = lines.map(l => {
        const match = l.match(/^-\s*(.+?)\s*--\[(.+?)\]-->\s*(.+)$/)
        if (match) {
          return { source: match[1].trim(), relation: match[2].trim(), target: match[3].trim() }
        }
        return null
      }).filter(Boolean)
    }
    
    // Knoteninformationen extrahieren (falls vorhanden)
    const nodesSection = text.match(/### Relevante Knoten:\n([\s\S]*?)(?=\n###|$)/)
    if (nodesSection) {
      const lines = nodesSection[1].split('\n').filter(l => l.trim().startsWith('-'))
      result.nodes = lines.map(l => {
        const match = l.match(/^-\s*\*\*(.+?)\*\*\s*\((.+?)\)/)
        if (match) return { name: match[1].trim(), type: match[2].trim() }
        const simpleMatch = l.match(/^-\s*(.+)$/)
        if (simpleMatch) return { name: simpleMatch[1].trim(), type: '' }
        return null
      }).filter(Boolean)
    }
  } catch (e) {
    console.warn('Parse quick_search failed:', e)
  }
  
  return result
}

// ========== Sub Components ==========

// Insight Display Component - Enhanced with full data rendering (Interview-like style)
const InsightDisplay = {
  props: ['result', 'resultLength'],
  setup(props) {
    const activeTab = ref('facts') // 'facts', 'entities', 'relations', 'subqueries'
    const expandedFacts = ref(false)
    const expandedEntities = ref(false)
    const expandedRelations = ref(false)
    const INITIAL_SHOW_COUNT = 5
    
    // Format result size for display
    const formatSize = (length) => {
      if (!length) return ''
      if (length >= 1000) {
        return t('step4.characterCountK', { count: (length / 1000).toFixed(1) })
      }
      return t('step4.characterCount', { count: length })
    }
    
    return () => h('div', { class: 'insight-display' }, [
      // Header Section - like interview header
      h('div', { class: 'insight-header' }, [
        h('div', { class: 'header-main' }, [
          h('div', { class: 'header-title' }, t('step4.deepAnalysis')),
          h('div', { class: 'header-stats' }, [
            h('span', { class: 'stat-item' }, [
              h('span', { class: 'stat-value' }, props.result.stats.facts || props.result.facts.length),
              h('span', { class: 'stat-label' }, t('step4.facts'))
            ]),
            h('span', { class: 'stat-divider' }, '/'),
            h('span', { class: 'stat-item' }, [
              h('span', { class: 'stat-value' }, props.result.stats.entities || props.result.entities.length),
              h('span', { class: 'stat-label' }, t('step4.entities'))
            ]),
            h('span', { class: 'stat-divider' }, '/'),
            h('span', { class: 'stat-item' }, [
              h('span', { class: 'stat-value' }, props.result.stats.relationships || props.result.relations.length),
              h('span', { class: 'stat-label' }, t('step4.relationships'))
            ]),
            props.resultLength && h('span', { class: 'stat-divider' }, '·'),
            props.resultLength && h('span', { class: 'stat-size' }, formatSize(props.resultLength))
          ])
        ]),
        props.result.query && h('div', { class: 'header-topic' }, props.result.query),
        props.result.simulationRequirement && h('div', { class: 'header-scenario' }, [
          h('span', { class: 'scenario-label' }, t('step4.predictionScenario')),
          h('span', { class: 'scenario-text' }, props.result.simulationRequirement)
        ])
      ]),
      
      // Tab Navigation
      h('div', { class: 'insight-tabs' }, [
        h('button', {
          class: ['insight-tab', { active: activeTab.value === 'facts' }],
          onClick: () => { activeTab.value = 'facts' }
        }, [
          h('span', { class: 'tab-label' }, t('step4.currentKeyMemoriesCount', { count: props.result.facts.length }))
        ]),
        h('button', {
          class: ['insight-tab', { active: activeTab.value === 'entities' }],
          onClick: () => { activeTab.value = 'entities' }
        }, [
          h('span', { class: 'tab-label' }, t('step4.coreEntitiesCount', { count: props.result.entities.length }))
        ]),
        h('button', {
          class: ['insight-tab', { active: activeTab.value === 'relations' }],
          onClick: () => { activeTab.value = 'relations' }
        }, [
          h('span', { class: 'tab-label' }, t('step4.relationshipChainsCount', { count: props.result.relations.length }))
        ]),
        props.result.subQueries.length > 0 && h('button', {
          class: ['insight-tab', { active: activeTab.value === 'subqueries' }],
          onClick: () => { activeTab.value = 'subqueries' }
        }, [
          h('span', { class: 'tab-label' }, t('step4.subQuestionsCount', { count: props.result.subQueries.length }))
        ])
      ]),
      
      // Tab Content
      h('div', { class: 'insight-content' }, [
        // Facts Tab
        activeTab.value === 'facts' && props.result.facts.length > 0 && h('div', { class: 'facts-panel' }, [
          h('div', { class: 'panel-header' }, [
            h('span', { class: 'panel-title' }, t('step4.latestKeyFacts')),
            h('span', { class: 'panel-count' }, t('step4.totalEntries', { count: props.result.facts.length }))
          ]),
          h('div', { class: 'facts-list' },
            (expandedFacts.value ? props.result.facts : props.result.facts.slice(0, INITIAL_SHOW_COUNT)).map((fact, i) => 
              h('div', { class: 'fact-item', key: i }, [
                h('span', { class: 'fact-number' }, i + 1),
                h('div', { class: 'fact-content' }, fact)
              ])
            )
          ),
          props.result.facts.length > INITIAL_SHOW_COUNT && h('button', {
            class: 'expand-btn',
            onClick: () => { expandedFacts.value = !expandedFacts.value }
          }, expandedFacts.value ? t('step4.collapse') : t('step4.showAllEntries', { count: props.result.facts.length }))
        ]),
        
        // Entities Tab
        activeTab.value === 'entities' && props.result.entities.length > 0 && h('div', { class: 'entities-panel' }, [
          h('div', { class: 'panel-header' }, [
            h('span', { class: 'panel-title' }, t('step4.coreEntities')),
            h('span', { class: 'panel-count' }, t('step4.totalItems', { count: props.result.entities.length }))
          ]),
          h('div', { class: 'entities-grid' },
            (expandedEntities.value ? props.result.entities : props.result.entities.slice(0, 12)).map((entity, i) => 
              h('div', { class: 'entity-tag', key: i, title: entity.summary || '' }, [
                h('span', { class: 'entity-name' }, entity.name),
                h('span', { class: 'entity-type' }, entity.type),
                entity.relatedFactsCount > 0 && h('span', { class: 'entity-fact-count' }, t('step4.entries', { count: entity.relatedFactsCount }))
              ])
            )
          ),
          props.result.entities.length > 12 && h('button', {
            class: 'expand-btn',
            onClick: () => { expandedEntities.value = !expandedEntities.value }
          }, expandedEntities.value ? t('step4.collapse') : t('step4.showAllItems', { count: props.result.entities.length }))
        ]),
        
        // Relations Tab
        activeTab.value === 'relations' && props.result.relations.length > 0 && h('div', { class: 'relations-panel' }, [
          h('div', { class: 'panel-header' }, [
            h('span', { class: 'panel-title' }, t('step4.relationshipChains')),
            h('span', { class: 'panel-count' }, t('step4.totalEntries', { count: props.result.relations.length }))
          ]),
          h('div', { class: 'relations-list' },
            (expandedRelations.value ? props.result.relations : props.result.relations.slice(0, INITIAL_SHOW_COUNT)).map((rel, i) => 
              h('div', { class: 'relation-item', key: i }, [
                h('span', { class: 'rel-source' }, rel.source),
                h('span', { class: 'rel-arrow' }, [
                  h('span', { class: 'rel-line' }),
                  h('span', { class: 'rel-label' }, rel.relation),
                  h('span', { class: 'rel-line' })
                ]),
                h('span', { class: 'rel-target' }, rel.target)
              ])
            )
          ),
          props.result.relations.length > INITIAL_SHOW_COUNT && h('button', {
            class: 'expand-btn',
            onClick: () => { expandedRelations.value = !expandedRelations.value }
          }, expandedRelations.value ? t('step4.collapse') : t('step4.showAllEntries', { count: props.result.relations.length }))
        ]),
        
        // Sub-queries Tab
        activeTab.value === 'subqueries' && props.result.subQueries.length > 0 && h('div', { class: 'subqueries-panel' }, [
          h('div', { class: 'panel-header' }, [
            h('span', { class: 'panel-title' }, t('step4.generatedSubQuestions')),
            h('span', { class: 'panel-count' }, t('step4.totalItems', { count: props.result.subQueries.length }))
          ]),
          h('div', { class: 'subqueries-list' },
            props.result.subQueries.map((sq, i) => 
              h('div', { class: 'subquery-item', key: i }, [
                h('span', { class: 'subquery-number' }, `Q${i + 1}`),
                h('div', { class: 'subquery-text' }, sq)
              ])
            )
          )
        ]),
        
        // Empty state
        activeTab.value === 'facts' && props.result.facts.length === 0 && h('div', { class: 'empty-state' }, t('step4.noCurrentKeyMemories')),
        activeTab.value === 'entities' && props.result.entities.length === 0 && h('div', { class: 'empty-state' }, t('step4.noCoreEntities')),
        activeTab.value === 'relations' && props.result.relations.length === 0 && h('div', { class: 'empty-state' }, t('step4.noRelationshipChains'))
      ])
    ])
  }
}

// Panorama Display Component - Enhanced with Active/Historical tabs
const PanoramaDisplay = {
  props: ['result', 'resultLength'],
  setup(props) {
    const activeTab = ref('active') // 'active', 'historical', 'entities'
    const expandedActive = ref(false)
    const expandedHistorical = ref(false)
    const expandedEntities = ref(false)
    const INITIAL_SHOW_COUNT = 5
    
    // Format result size for display
    const formatSize = (length) => {
      if (!length) return ''
      if (length >= 1000) {
        return t('step4.characterCountK', { count: (length / 1000).toFixed(1) })
      }
      return t('step4.characterCount', { count: length })
    }
    
    return () => h('div', { class: 'panorama-display' }, [
      // Header Section
      h('div', { class: 'panorama-header' }, [
        h('div', { class: 'header-main' }, [
          h('div', { class: 'header-title' }, t('step4.panoramaSearch')),
          h('div', { class: 'header-stats' }, [
            h('span', { class: 'stat-item' }, [
              h('span', { class: 'stat-value' }, props.result.stats.nodes),
              h('span', { class: 'stat-label' }, t('step4.nodes'))
            ]),
            h('span', { class: 'stat-divider' }, '/'),
            h('span', { class: 'stat-item' }, [
              h('span', { class: 'stat-value' }, props.result.stats.edges),
              h('span', { class: 'stat-label' }, t('step4.edges'))
            ]),
            props.resultLength && h('span', { class: 'stat-divider' }, '·'),
            props.resultLength && h('span', { class: 'stat-size' }, formatSize(props.resultLength))
          ])
        ]),
        props.result.query && h('div', { class: 'header-topic' }, props.result.query)
      ]),
      
      // Tab Navigation
      h('div', { class: 'panorama-tabs' }, [
        h('button', {
          class: ['panorama-tab', { active: activeTab.value === 'active' }],
          onClick: () => { activeTab.value = 'active' }
        }, [
          h('span', { class: 'tab-label' }, t('step4.currentValidMemoriesCount', { count: props.result.activeFacts.length }))
        ]),
        h('button', {
          class: ['panorama-tab', { active: activeTab.value === 'historical' }],
          onClick: () => { activeTab.value = 'historical' }
        }, [
          h('span', { class: 'tab-label' }, t('step4.historicalMemoriesCount', { count: props.result.historicalFacts.length }))
        ]),
        h('button', {
          class: ['panorama-tab', { active: activeTab.value === 'entities' }],
          onClick: () => { activeTab.value = 'entities' }
        }, [
          h('span', { class: 'tab-label' }, t('step4.involvedEntitiesCount', { count: props.result.entities.length }))
        ])
      ]),
      
      // Tab Content
      h('div', { class: 'panorama-content' }, [
        // Active Facts Tab
        activeTab.value === 'active' && h('div', { class: 'facts-panel active-facts' }, [
          h('div', { class: 'panel-header' }, [
            h('span', { class: 'panel-title' }, t('step4.currentValidMemories')),
            h('span', { class: 'panel-count' }, t('step4.totalEntries', { count: props.result.activeFacts.length }))
          ]),
          props.result.activeFacts.length > 0 ? h('div', { class: 'facts-list' },
            (expandedActive.value ? props.result.activeFacts : props.result.activeFacts.slice(0, INITIAL_SHOW_COUNT)).map((fact, i) => 
              h('div', { class: 'fact-item active', key: i }, [
                h('span', { class: 'fact-number' }, i + 1),
                h('div', { class: 'fact-content' }, fact)
              ])
            )
          ) : h('div', { class: 'empty-state' }, t('step4.noCurrentValidMemories')),
          props.result.activeFacts.length > INITIAL_SHOW_COUNT && h('button', {
            class: 'expand-btn',
            onClick: () => { expandedActive.value = !expandedActive.value }
          }, expandedActive.value ? t('step4.collapse') : t('step4.showAllEntries', { count: props.result.activeFacts.length }))
        ]),
        
        // Historical Facts Tab
        activeTab.value === 'historical' && h('div', { class: 'facts-panel historical-facts' }, [
          h('div', { class: 'panel-header' }, [
            h('span', { class: 'panel-title' }, t('step4.historicalMemories')),
            h('span', { class: 'panel-count' }, t('step4.totalEntries', { count: props.result.historicalFacts.length }))
          ]),
          props.result.historicalFacts.length > 0 ? h('div', { class: 'facts-list' },
            (expandedHistorical.value ? props.result.historicalFacts : props.result.historicalFacts.slice(0, INITIAL_SHOW_COUNT)).map((fact, i) => 
              h('div', { class: 'fact-item historical', key: i }, [
                h('span', { class: 'fact-number' }, i + 1),
                h('div', { class: 'fact-content' }, [
                  // Versuche Zeitinformationen [time - time] zu extrahieren
                  (() => {
                    const timeMatch = fact.match(/^\[(.+?)\]\s*(.*)$/)
                    if (timeMatch) {
                      return [
                        h('span', { class: 'fact-time' }, timeMatch[1]),
                        h('span', { class: 'fact-text' }, timeMatch[2])
                      ]
                    }
                    return h('span', { class: 'fact-text' }, fact)
                  })()
                ])
              ])
            )
          ) : h('div', { class: 'empty-state' }, t('step4.noHistoricalMemories')),
          props.result.historicalFacts.length > INITIAL_SHOW_COUNT && h('button', {
            class: 'expand-btn',
            onClick: () => { expandedHistorical.value = !expandedHistorical.value }
          }, expandedHistorical.value ? t('step4.collapse') : t('step4.showAllEntries', { count: props.result.historicalFacts.length }))
        ]),
        
        // Entities Tab
        activeTab.value === 'entities' && h('div', { class: 'entities-panel' }, [
          h('div', { class: 'panel-header' }, [
            h('span', { class: 'panel-title' }, t('step4.involvedEntities')),
            h('span', { class: 'panel-count' }, t('step4.totalItems', { count: props.result.entities.length }))
          ]),
          props.result.entities.length > 0 ? h('div', { class: 'entities-grid' },
            (expandedEntities.value ? props.result.entities : props.result.entities.slice(0, 8)).map((entity, i) => 
              h('div', { class: 'entity-tag', key: i }, [
                h('span', { class: 'entity-name' }, entity.name),
                entity.type && h('span', { class: 'entity-type' }, entity.type)
              ])
            )
          ) : h('div', { class: 'empty-state' }, t('step4.noInvolvedEntities')),
          props.result.entities.length > 8 && h('button', {
            class: 'expand-btn',
            onClick: () => { expandedEntities.value = !expandedEntities.value }
          }, expandedEntities.value ? t('step4.collapse') : t('step4.showAllItems', { count: props.result.entities.length }))
        ])
      ])
    ])
  }
}

// Interview Display Component - Conversation Style (Q&A Format)
const InterviewDisplay = {
  props: ['result', 'resultLength'],
  setup(props) {
    // Format result size for display
    const formatSize = (length) => {
      if (!length) return ''
      if (length >= 1000) {
        return t('step4.characterCountK', { count: (length / 1000).toFixed(1) })
      }
      return t('step4.characterCount', { count: length })
    }
    
    // Clean quote text - remove leading list numbers to avoid double numbering
    const cleanQuoteText = (text) => {
      if (!text) return ''
      // Remove leading patterns like `1. ", "2. ", "1、", "（1）", "(1)` etc.
      return text.replace(/^\s*\d+[\.\、\)）]\s*/, '').trim()
    }
    
    const activeIndex = ref(0)
    const expandedAnswers = ref(new Set())
    // Unabhängigen Plattformauswahlstatus für jedes Frage-Antwort-Paar pflegen
    const platformTabs = reactive({}) // { 'agentIdx-qIdx': 'twitter' | 'reddit' }
    
    // Aktuelle Plattformauswahl einer Frage abrufen
    const getPlatformTab = (agentIdx, qIdx) => {
      const key = `${agentIdx}-${qIdx}`
      return platformTabs[key] || 'twitter'
    }
    
    // Plattformauswahl einer Frage festlegen
    const setPlatformTab = (agentIdx, qIdx, platform) => {
      const key = `${agentIdx}-${qIdx}`
      platformTabs[key] = platform
    }
    
    const toggleAnswer = (key) => {
      const newSet = new Set(expandedAnswers.value)
      if (newSet.has(key)) {
        newSet.delete(key)
      } else {
        newSet.add(key)
      }
      expandedAnswers.value = newSet
    }
    
    const formatAnswer = (text, expanded) => {
      if (!text) return ''
      if (expanded || text.length <= 400) return text
      return text.substring(0, 400) + '...'
    }
    
    // Prüfen, ob es sich um Plattform-Platzhaltertext handelt
    const isPlaceholderText = (text) => {
      if (!text) return true
      const t = text.trim()
      return t === '(Diese Plattform hat keine Antwort erhalten)' || t === '(Diese Plattform hat keine Antwort erhalten)' || t === '[Keine Antwort]'
    }

    // Versuche Antworten nach Fragennummern aufzuteilen
    const splitAnswerByQuestions = (answerText, questionCount) => {
      if (!answerText || questionCount <= 0) return [answerText]
      if (isPlaceholderText(answerText)) return ['']

      // Zwei Nummerierungsformate werden unterstützt:
      // 1. "Frage X:" bzw. "「Frage X：」" (neues Backend-Format; chinesisches "问题X：" weiter akzeptiert)
      // 2. "1. " oder "1. " (Zahl+Punkt, altes Format kompatibel)
      let matches = []
      let match

      // Bevorzugt das `Frage X:`-Format versuchen
      const cnPattern = /(?:^|[\r\n]+)「?(?:问题|Frage)\s*(\d+)[：:]」?\s*/g
      while ((match = cnPattern.exec(answerText)) !== null) {
        matches.push({
          num: parseInt(match[1]),
          index: match.index,
          fullMatch: match[0]
        })
      }

      // Falls nicht gefunden, auf `Zahl.` Format zurückfallen
      if (matches.length === 0) {
        const numPattern = /(?:^|[\r\n]+)(\d+)\.\s+/g
        while ((match = numPattern.exec(answerText)) !== null) {
          matches.push({
            num: parseInt(match[1]),
            index: match.index,
            fullMatch: match[0]
          })
        }
      }

      // Wenn keine oder nur eine Nummerierung gefunden, Gesamttext zurückgeben
      if (matches.length <= 1) {
        const cleaned = answerText
          .replace(/^「?(?:问题|Frage)\s*\d+[：:]」?\s*/, '')
          .replace(/^\d+\.\s+/, '')
          .trim()
        return [cleaned || answerText]
      }

      // Einzelne Teile nach Nummerierung extrahieren
      const parts = []
      for (let i = 0; i < matches.length; i++) {
        const current = matches[i]
        const next = matches[i + 1]

        const startIdx = current.index + current.fullMatch.length
        const endIdx = next ? next.index : answerText.length

        let part = answerText.substring(startIdx, endIdx).trim()
        part = part.replace(/[\r\n]+$/, '').trim()
        parts.push(part)
      }

      if (parts.length > 0 && parts.some(p => p)) {
        return parts
      }

      return [answerText]
    }
    
    // Antwort zu einer bestimmten Frage abrufen
    const getAnswerForQuestion = (interview, qIdx, platform) => {
      const answer = platform === 'twitter' ? interview.twitterAnswer : (interview.redditAnswer || interview.twitterAnswer)
      if (!answer || isPlaceholderText(answer)) return answer || ''

      const questionCount = interview.questions?.length || 1
      const answers = splitAnswerByQuestions(answer, questionCount)

      // Aufteilung erfolgreich und Index gültig
      if (answers.length > 1 && qIdx < answers.length) {
        return answers[qIdx] || ''
      }

      // Aufteilung fehlgeschlagen: Erste Frage erhält vollständige Antwort, Rest leer
      return qIdx === 0 ? answer : ''
    }
    
    // Prüfen, ob eine Frage Antworten von beiden Plattformen hat (Platzhaltertext filtern)
    const hasMultiplePlatforms = (interview, qIdx) => {
      if (!interview.twitterAnswer || !interview.redditAnswer) return false
      const twitterAnswer = getAnswerForQuestion(interview, qIdx, 'twitter')
      const redditAnswer = getAnswerForQuestion(interview, qIdx, 'reddit')
      // Beide Plattformen haben echte Antworten (kein Platzhaltertext) und unterschiedliche Inhalte
      return !isPlaceholderText(twitterAnswer) && !isPlaceholderText(redditAnswer) && twitterAnswer !== redditAnswer
    }
    
    return () => h('div', { class: 'interview-display' }, [
      // Header Section
      h('div', { class: 'interview-header' }, [
        h('div', { class: 'header-main' }, [
          h('div', { class: 'header-title' }, t('step4.agentInterview')),
          h('div', { class: 'header-stats' }, [
            h('span', { class: 'stat-item' }, [
              h('span', { class: 'stat-value' }, props.result.successCount || props.result.interviews.length),
              h('span', { class: 'stat-label' }, t('step4.interviewed'))
            ]),
            props.result.totalCount > 0 && h('span', { class: 'stat-divider' }, '/'),
            props.result.totalCount > 0 && h('span', { class: 'stat-item' }, [
              h('span', { class: 'stat-value' }, props.result.totalCount),
              h('span', { class: 'stat-label' }, t('step4.total'))
            ]),
            props.resultLength && h('span', { class: 'stat-divider' }, '·'),
            props.resultLength && h('span', { class: 'stat-size' }, formatSize(props.resultLength))
          ])
        ]),
        props.result.topic && h('div', { class: 'header-topic' }, props.result.topic)
      ]),
      
      // Agent Selector Tabs
      props.result.interviews.length > 0 && h('div', { class: 'agent-tabs' }, 
        props.result.interviews.map((interview, i) => h('button', {
          class: ['agent-tab', { active: activeIndex.value === i }],
          key: i,
          onClick: () => { activeIndex.value = i }
        }, [
          h('span', { class: 'tab-avatar' }, interview.name ? interview.name.charAt(0) : (i + 1)),
          h('span', { class: 'tab-name' }, interview.title || interview.name || `Agent ${i + 1}`)
        ]))
      ),
      
      // Active Interview Detail
      props.result.interviews.length > 0 && h('div', { class: 'interview-detail' }, [
        // Agent Profile Card
        h('div', { class: 'agent-profile' }, [
          h('div', { class: 'profile-avatar' }, props.result.interviews[activeIndex.value]?.name?.charAt(0) || 'A'),
          h('div', { class: 'profile-info' }, [
            h('div', { class: 'profile-name' }, props.result.interviews[activeIndex.value]?.name || t('step4.agent')),
            h('div', { class: 'profile-role' }, props.result.interviews[activeIndex.value]?.role || ''),
            props.result.interviews[activeIndex.value]?.bio && h('div', { class: 'profile-bio' }, props.result.interviews[activeIndex.value].bio)
          ])
        ]),
        
        // Auswahlbegründung
        props.result.interviews[activeIndex.value]?.selectionReason && h('div', { class: 'selection-reason' }, [
          h('div', { class: 'reason-label' }, t('step4.selectionReason')),
          h('div', { class: 'reason-content' }, props.result.interviews[activeIndex.value].selectionReason)
        ]),
        
        // Frage-Antwort-Gesprächsverlauf
        h('div', { class: 'qa-thread' }, 
          (props.result.interviews[activeIndex.value]?.questions?.length > 0 
            ? props.result.interviews[activeIndex.value].questions 
            : [props.result.interviews[activeIndex.value]?.question || t('step4.noQuestionAvailable')]
          ).map((question, qIdx) => {
            const interview = props.result.interviews[activeIndex.value]
            const currentPlatform = getPlatformTab(activeIndex.value, qIdx)
            const answerText = getAnswerForQuestion(interview, qIdx, currentPlatform)
            const hasDualPlatform = hasMultiplePlatforms(interview, qIdx)
            const expandKey = `${activeIndex.value}-${qIdx}`
            const isExpanded = expandedAnswers.value.has(expandKey)
            const isPlaceholder = isPlaceholderText(answerText)

            return h('div', { class: 'qa-pair', key: qIdx }, [
              // Question Block
              h('div', { class: 'qa-question' }, [
                h('div', { class: 'qa-badge q-badge' }, `Q${qIdx + 1}`),
                h('div', { class: 'qa-content' }, [
                  h('div', { class: 'qa-sender' }, t('step4.interviewer')),
                  h('div', { class: 'qa-text' }, question)
                ])
              ]),

              // Answer Block
              answerText && h('div', { class: ['qa-answer', { 'answer-placeholder': isPlaceholder }] }, [
                h('div', { class: 'qa-badge a-badge' }, `A${qIdx + 1}`),
                h('div', { class: 'qa-content' }, [
                  h('div', { class: 'qa-answer-header' }, [
                    h('div', { class: 'qa-sender' }, interview?.name || t('step4.agent')),
                    // Dualplattform-Umschaltfläche (nur bei echten Antworten von beiden Plattformen anzeigen)
                    hasDualPlatform && h('div', { class: 'platform-switch' }, [
                      h('button', {
                        class: ['platform-btn', { active: currentPlatform === 'twitter' }],
                        onClick: (e) => { e.stopPropagation(); setPlatformTab(activeIndex.value, qIdx, 'twitter') }
                      }, [
                        h('svg', { class: 'platform-icon', viewBox: '0 0 24 24', width: 12, height: 12, fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
                          h('circle', { cx: '12', cy: '12', r: '10' }),
                          h('line', { x1: '2', y1: '12', x2: '22', y2: '12' }),
                          h('path', { d: 'M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z' })
                        ]),
                        h('span', {}, t('step4.world1'))
                      ]),
                      h('button', {
                        class: ['platform-btn', { active: currentPlatform === 'reddit' }],
                        onClick: (e) => { e.stopPropagation(); setPlatformTab(activeIndex.value, qIdx, 'reddit') }
                      }, [
                        h('svg', { class: 'platform-icon', viewBox: '0 0 24 24', width: 12, height: 12, fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
                          h('path', { d: 'M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z' })
                        ]),
                        h('span', {}, t('step4.world2'))
                      ])
                    ])
                  ]),
                  h('div', {
                    class: ['qa-text', 'answer-text', { 'placeholder-text': isPlaceholder }],
                    innerHTML: isPlaceholder
                      ? answerText
                      : formatAnswer(answerText, isExpanded)
                          .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                          .replace(/\n/g, '<br>')
                  }),
                  // Ein-/Ausklappen-Schaltfläche (bei Platzhaltertext nicht anzeigen)
                  !isPlaceholder && answerText.length > 400 && h('button', {
                    class: 'expand-answer-btn',
                    onClick: () => toggleAnswer(expandKey)
                  }, isExpanded ? t('step4.showLess') : t('step4.showMore'))
                ])
              ])
            ])
          })
        ),
        
        // Key Quotes Section
        props.result.interviews[activeIndex.value]?.quotes?.length > 0 && h('div', { class: 'quotes-section' }, [
          h('div', { class: 'quotes-header' }, t('step4.keyQuotes')),
          h('div', { class: 'quotes-list' },
            props.result.interviews[activeIndex.value].quotes.slice(0, 3).map((quote, qi) => {
              const cleanedQuote = cleanQuoteText(quote)
              const displayQuote = cleanedQuote.length > 200 ? cleanedQuote.substring(0, 200) + '...' : cleanedQuote
              return h('blockquote', { 
                key: qi, 
                class: 'quote-item',
                innerHTML: renderMarkdown(displayQuote)
              })
            })
          )
        ])
      ]),

      // Summary Section (Collapsible)
      props.result.summary && h('div', { class: 'summary-section' }, [
        h('div', { class: 'summary-header' }, t('step4.interviewSummary')),
        h('div', { 
          class: 'summary-content',
          innerHTML: renderMarkdown(props.result.summary.length > 500 ? props.result.summary.substring(0, 500) + '...' : props.result.summary)
        })
      ])
    ])
  }
}

// Quick Search Display Component - Enhanced with full data rendering
const QuickSearchDisplay = {
  props: ['result', 'resultLength'],
  setup(props) {
    const activeTab = ref('facts') // 'facts', 'edges', 'nodes'
    const expandedFacts = ref(false)
    const INITIAL_SHOW_COUNT = 5
    
    // Check if there are edges or nodes to show tabs
    const hasEdges = computed(() => props.result.edges && props.result.edges.length > 0)
    const hasNodes = computed(() => props.result.nodes && props.result.nodes.length > 0)
    const showTabs = computed(() => hasEdges.value || hasNodes.value)
    
    // Format result size for display
    const formatSize = (length) => {
      if (!length) return ''
      if (length >= 1000) {
        return t('step4.characterCountK', { count: (length / 1000).toFixed(1) })
      }
      return t('step4.characterCount', { count: length })
    }
    
    return () => h('div', { class: 'quick-search-display' }, [
      // Header Section
      h('div', { class: 'quicksearch-header' }, [
        h('div', { class: 'header-main' }, [
          h('div', { class: 'header-title' }, t('step4.quickSearch')),
          h('div', { class: 'header-stats' }, [
            h('span', { class: 'stat-item' }, [
              h('span', { class: 'stat-value' }, props.result.count || props.result.facts.length),
              h('span', { class: 'stat-label' }, t('step4.results'))
            ]),
            props.resultLength && h('span', { class: 'stat-divider' }, '·'),
            props.resultLength && h('span', { class: 'stat-size' }, formatSize(props.resultLength))
          ])
        ]),
        props.result.query && h('div', { class: 'header-query' }, [
          h('span', { class: 'query-label' }, t('step4.searchLabel')),
          h('span', { class: 'query-text' }, props.result.query)
        ])
      ]),
      
      // Tab Navigation (only show if there are edges or nodes)
      showTabs.value && h('div', { class: 'quicksearch-tabs' }, [
        h('button', {
          class: ['quicksearch-tab', { active: activeTab.value === 'facts' }],
          onClick: () => { activeTab.value = 'facts' }
        }, [
          h('span', { class: 'tab-label' }, t('step4.factsCount', { count: props.result.facts.length }))
        ]),
        hasEdges.value && h('button', {
          class: ['quicksearch-tab', { active: activeTab.value === 'edges' }],
          onClick: () => { activeTab.value = 'edges' }
        }, [
          h('span', { class: 'tab-label' }, t('step4.relationshipsCount', { count: props.result.edges.length }))
        ]),
        hasNodes.value && h('button', {
          class: ['quicksearch-tab', { active: activeTab.value === 'nodes' }],
          onClick: () => { activeTab.value = 'nodes' }
        }, [
          h('span', { class: 'tab-label' }, t('step4.nodesCount', { count: props.result.nodes.length }))
        ])
      ]),
      
      // Content Area
      h('div', { class: ['quicksearch-content', { 'no-tabs': !showTabs.value }] }, [
        // Facts (always show if no tabs, or when facts tab is active)
        ((!showTabs.value) || activeTab.value === 'facts') && h('div', { class: 'facts-panel' }, [
          !showTabs.value && h('div', { class: 'panel-header' }, [
            h('span', { class: 'panel-title' }, t('step4.searchResults')),
            h('span', { class: 'panel-count' }, t('step4.totalEntries', { count: props.result.facts.length }))
          ]),
          props.result.facts.length > 0 ? h('div', { class: 'facts-list' },
            (expandedFacts.value ? props.result.facts : props.result.facts.slice(0, INITIAL_SHOW_COUNT)).map((fact, i) => 
              h('div', { class: 'fact-item', key: i }, [
                h('span', { class: 'fact-number' }, i + 1),
                h('div', { class: 'fact-content' }, fact)
              ])
            )
          ) : h('div', { class: 'empty-state' }, t('step4.noRelevantResults')),
          props.result.facts.length > INITIAL_SHOW_COUNT && h('button', {
            class: 'expand-btn',
            onClick: () => { expandedFacts.value = !expandedFacts.value }
          }, expandedFacts.value ? t('step4.collapse') : t('step4.showAllEntries', { count: props.result.facts.length }))
        ]),
        
        // Edges Tab
        activeTab.value === 'edges' && hasEdges.value && h('div', { class: 'edges-panel' }, [
          h('div', { class: 'panel-header' }, [
            h('span', { class: 'panel-title' }, t('step4.relatedRelationships')),
            h('span', { class: 'panel-count' }, t('step4.totalEntries', { count: props.result.edges.length }))
          ]),
          h('div', { class: 'edges-list' },
            props.result.edges.map((edge, i) => 
              h('div', { class: 'edge-item', key: i }, [
                h('span', { class: 'edge-source' }, edge.source),
                h('span', { class: 'edge-arrow' }, [
                  h('span', { class: 'edge-line' }),
                  h('span', { class: 'edge-label' }, edge.relation),
                  h('span', { class: 'edge-line' })
                ]),
                h('span', { class: 'edge-target' }, edge.target)
              ])
            )
          )
        ]),
        
        // Nodes Tab
        activeTab.value === 'nodes' && hasNodes.value && h('div', { class: 'nodes-panel' }, [
          h('div', { class: 'panel-header' }, [
            h('span', { class: 'panel-title' }, t('step4.relatedNodes')),
            h('span', { class: 'panel-count' }, t('step4.totalItems', { count: props.result.nodes.length }))
          ]),
          h('div', { class: 'nodes-grid' },
            props.result.nodes.map((node, i) => 
              h('div', { class: 'node-tag', key: i }, [
                h('span', { class: 'node-name' }, node.name),
                node.type && h('span', { class: 'node-type' }, node.type)
              ])
            )
          )
        ])
      ])
    ])
  }
}

// Computed
const statusClass = computed(() => {
  if (isComplete.value) return 'completed'
  if (agentLogs.value.length > 0) return 'processing'
  return 'pending'
})

const statusText = computed(() => {
  if (isComplete.value) return t('common.completed')
  if (agentLogs.value.length > 0) return t('common.generating')
  return t('step4.waiting')
})

const totalSections = computed(() => {
  return reportOutline.value?.sections?.length || 0
})

const completedSections = computed(() => {
  return Object.keys(generatedSections.value).length
})

const progressPercent = computed(() => {
  if (totalSections.value === 0) return 0
  return Math.round((completedSections.value / totalSections.value) * 100)
})

const totalToolCalls = computed(() => {
  return agentLogs.value.filter(l => l.action === 'tool_call').length
})

const formatElapsedTime = computed(() => {
  if (!startTime.value) return '0s'
  const lastLog = agentLogs.value[agentLogs.value.length - 1]
  const elapsed = lastLog?.elapsed_seconds || 0
  if (elapsed < 60) return `${Math.round(elapsed)}s`
  const mins = Math.floor(elapsed / 60)
  const secs = Math.round(elapsed % 60)
  return `${mins}m ${secs}s`
})

const displayLogs = computed(() => {
  return agentLogs.value
})

// Workflow steps overview (status-based, no nested cards)
const activeSectionIndex = computed(() => {
  if (isComplete.value) return null
  if (currentSectionIndex.value) return currentSectionIndex.value
  if (totalSections.value > 0 && completedSections.value < totalSections.value) return completedSections.value + 1
  return null
})

const isPlanningDone = computed(() => {
  return !!reportOutline.value?.sections?.length || agentLogs.value.some(l => l.action === 'planning_complete')
})

const isPlanningStarted = computed(() => {
  return agentLogs.value.some(l => l.action === 'planning_start' || l.action === 'report_start')
})

const isFinalizing = computed(() => {
  return !isComplete.value && isPlanningDone.value && totalSections.value > 0 && completedSections.value >= totalSections.value
})

// Aktuell aktiver Schritt (für Anzeige oben)
const activeStep = computed(() => {
  const steps = workflowSteps.value
  // Den aktuell aktiven Schritt finden
  const active = steps.find(s => s.status === 'active')
  if (active) return active
  
  // Wenn kein aktiver Schritt, den letzten abgeschlossenen zurückgeben
  const doneSteps = steps.filter(s => s.status === 'done')
  if (doneSteps.length > 0) return doneSteps[doneSteps.length - 1]
  
  // Andernfalls ersten Schritt zurückgeben
  return steps[0] || { noLabel: '--', title: t('step4.waitingToStart'), status: 'todo', meta: '' }
})

const workflowSteps = computed(() => {
  const steps = []

  // Planning / Outline
  const planningStatus = isPlanningDone.value ? 'done' : (isPlanningStarted.value ? 'active' : 'todo')
  steps.push({
    key: 'planning',
    noLabel: 'PL',
    title: t('step4.planningOutline'),
    status: planningStatus,
    meta: planningStatus === 'active' ? t('step4.inProgressUpper') : ''
  })

  // Sections (if outline exists)
  const sections = reportOutline.value?.sections || []
  sections.forEach((section, i) => {
    const idx = i + 1
    const status = (isComplete.value || !!generatedSections.value[idx])
      ? 'done'
      : (activeSectionIndex.value === idx ? 'active' : 'todo')

    steps.push({
      key: `section-${idx}`,
      noLabel: String(idx).padStart(2, '0'),
      title: section.title,
      status,
      meta: status === 'active' ? t('step4.inProgressUpper') : ''
    })
  })

  // Complete
  const completeStatus = isComplete.value ? 'done' : (isFinalizing.value ? 'active' : 'todo')
  steps.push({
    key: 'complete',
    noLabel: 'OK',
    title: t('common.completed'),
    status: completeStatus,
    meta: completeStatus === 'active' ? t('step4.completingUpper') : ''
  })

  return steps
})

// Methods
const addLog = (msg) => {
  emit('add-log', msg)
}

const isSectionCompleted = (sectionIndex) => {
  return !!generatedSections.value[sectionIndex]
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  try {
    return new Date(timestamp).toLocaleTimeString('de-DE', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch {
    return ''
  }
}

const formatParams = (params) => {
  if (!params) return ''
  try {
    return JSON.stringify(params, null, 2)
  } catch {
    return String(params)
  }
}

const formatResultSize = (length) => {
  if (!length) return ''
  if (length < 1000) return t('step4.characterCount', { count: length })
  return t('step4.characterCountK', { count: (length / 1000).toFixed(1) })
}

const truncateText = (text, maxLen) => {
  if (!text) return ''
  if (text.length <= maxLen) return text
  return text.substring(0, maxLen) + '...'
}

const renderMarkdown = (content) => {
  if (!content) return ''

  let processedContent = content.replace(/^##\s+.+\n+/, '')
  let html = processedContent.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre class="code-block"><code>$2</code></pre>')
  html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
  html = html.replace(/^#### (.+)$/gm, '<h5 class="md-h5">$1</h5>')
  html = html.replace(/^### (.+)$/gm, '<h4 class="md-h4">$1</h4>')
  html = html.replace(/^## (.+)$/gm, '<h3 class="md-h3">$1</h3>')
  html = html.replace(/^# (.+)$/gm, '<h2 class="md-h2">$1</h2>')
  // Standalone **Zeile** → echte Zwischenüberschrift (nicht erst per CSS)
  html = html.replace(/^\s*\*\*(.+?)\*\*\s*$/gm, '<h4 class="md-h4">$1</h4>')
  html = html.replace(/^> (.+)$/gm, '<blockquote class="md-quote">$1</blockquote>')
  html = html.replace(/^(\s*)- (.+)$/gm, (match, indent, text) => {
    const level = Math.floor(indent.length / 2)
    return `<li class="md-li" data-level="${level}">${text}</li>`
  })
  html = html.replace(/^(\s*)(\d+)\. (.+)$/gm, (match, indent, num, text) => {
    const level = Math.floor(indent.length / 2)
    return `<li class="md-oli" data-level="${level}">${text}</li>`
  })
  html = html.replace(/(<li class="md-li"[^>]*>.*?<\/li>\s*)+/g, '<ul class="md-ul">$&</ul>')
  html = html.replace(/(<li class="md-oli"[^>]*>.*?<\/li>\s*)+/g, '<ol class="md-ol">$&</ol>')
  html = html.replace(/<\/li>\s+<li/g, '</li><li')
  html = html.replace(/<ul class="md-ul">\s+/g, '<ul class="md-ul">')
  html = html.replace(/<ol class="md-ol">\s+/g, '<ol class="md-ol">')
  html = html.replace(/\s+<\/ul>/g, '</ul>')
  html = html.replace(/\s+<\/ol>/g, '</ol>')
  // Inline-Fett/Kursiv nach Block-Konvertierung — bleibt im Absatz
  html = html.replace(/\*\*([^*\n]+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*([^*\n]+?)\*/g, '<em>$1</em>')
  html = html.replace(/_([^_\n]+?)_/g, '<em>$1</em>')
  html = html.replace(/^---$/gm, '<hr class="md-hr">')
  html = html.replace(/\n\n/g, '</p><p class="md-p">')
  html = html.replace(/\n/g, '<br>')
  html = '<p class="md-p">' + html + '</p>'
  html = html.replace(/<p class="md-p"><\/p>/g, '')
  html = html.replace(/<p class="md-p">(<h[2-5])/g, '$1')
  html = html.replace(/(<\/h[2-5]>)<\/p>/g, '$1')
  html = html.replace(/<p class="md-p">(<ul|<ol|<blockquote|<pre|<hr)/g, '$1')
  html = html.replace(/(<\/ul>|<\/ol>|<\/blockquote>|<\/pre>)<\/p>/g, '$1')
  html = html.replace(/<br>\s*(<ul|<ol|<blockquote)/g, '$1')
  html = html.replace(/(<\/ul>|<\/ol>|<\/blockquote>)\s*<br>/g, '$1')
  html = html.replace(/<p class="md-p">(<br>\s*)+(<ul|<ol|<blockquote|<pre|<hr)/g, '$2')
  html = html.replace(/(<br>\s*){2,}/g, '<br>')
  html = html.replace(/(<\/ol>|<\/ul>|<\/blockquote>)<br>(<p|<div)/g, '$1$2')
  // h4 die in p landeten herauslösen
  html = html.replace(/<p class="md-p">(<h4\b[^>]*>[\s\S]*?<\/h4>)<\/p>/g, '$1')
  html = html.replace(/<p class="md-p">([\s\S]*?)<h4\b/g, '<p class="md-p">$1</p><h4')
  html = html.replace(/<\/h4><\/p>/g, '</h4>')

  const tokens = html.split(/(<ol class="md-ol">(?:<li class="md-oli"[^>]*>[\s\S]*?<\/li>)+<\/ol>)/g)
  let olCounter = 0
  let inSequence = false
  for (let i = 0; i < tokens.length; i++) {
    if (tokens[i].startsWith('<ol class="md-ol">')) {
      const liCount = (tokens[i].match(/<li class="md-oli"/g) || []).length
      if (liCount === 1) {
        olCounter++
        if (olCounter > 1) tokens[i] = tokens[i].replace('<ol class="md-ol">', `<ol class="md-ol" start="${olCounter}">`)
        inSequence = true
      } else {
        olCounter = 0
        inSequence = false
      }
    } else if (inSequence && /<h[2-5]/.test(tokens[i])) {
      olCounter = 0
      inSequence = false
    }
  }
  return tokens.join('')
}

const getTimelineItemClass = (log, idx, total) => {
  const isLatest = idx === total - 1 && !isComplete.value
  const isMilestone = log.action === 'section_complete' || log.action === 'report_complete'
  return {
    'node--active': isLatest,
    'node--done': !isLatest && isMilestone,
    'node--muted': !isLatest && !isMilestone,
    'node--tool': log.action === 'tool_call' || log.action === 'tool_result'
  }
}

const getConnectorClass = (log, idx, total) => {
  const isLatest = idx === total - 1 && !isComplete.value
  if (isLatest) return 'dot-active'
  if (log.action === 'section_complete' || log.action === 'report_complete') return 'dot-done'
  return 'dot-muted'
}

const getActionLabel = (action) => {
  const labels = {
    'report_start': t('step4.reportStarted'),
    'planning_start': t('step4.planning'),
    'planning_complete': t('step4.planComplete'),
    'section_start': t('step4.sectionStarted'),
    'section_content': t('step4.contentReady'),
    'section_complete': t('step4.sectionComplete'),
    'tool_call': t('step4.toolCall'),
    'tool_result': t('step4.toolResult'),
    'llm_response': t('step4.llmResponse'),
    'report_complete': t('common.completed')
  }
  return labels[action] || action
}

const getLogLevelClass = (log) => {
  if (log.includes('ERROR') || log.includes('Fehler')) return 'error'
  if (log.includes('WARNING') || log.includes('Warnung')) return 'warning'
  // INFO verwendet Standardfarbe, nicht als Erfolg markieren
  return ''
}

// Polling
let agentLogTimer = null
let consoleLogTimer = null

const fetchAgentLog = async () => {
  if (!props.reportId) return
  
  try {
    const res = await getAgentLog(props.reportId, agentLogLine.value)
    
    if (res.success && res.data) {
      const newLogs = res.data.logs || []
      
      if (newLogs.length > 0) {
        newLogs.forEach(log => {
          agentLogs.value.push(log)
          
          if (log.action === 'planning_complete' && log.details?.outline) {
            reportOutline.value = log.details.outline
          }
          
          if (log.action === 'section_start') {
            currentSectionIndex.value = log.section_index
          }

          // section_complete - Abschnittsgenerierung abgeschlossen
          if (log.action === 'section_complete') {
            if (log.details?.content) {
              generatedSections.value[log.section_index] = log.details.content
              // Gerade generierten Abschnitt automatisch aufklappen
              expandedContent.value.add(log.section_index - 1)
              currentSectionIndex.value = null
            }
          }
          
          if (log.action === 'report_complete') {
            isComplete.value = true
            currentSectionIndex.value = null  // Sicherstellen, dass der Ladezustand gelöscht wird
            emit('update-status', 'completed')
            stopPolling()
            loadMethodology()
            // Scrolllogik einheitlich im nextTick nach der Schleife verarbeiten
          }
          
          if (log.action === 'report_start') {
            startTime.value = new Date(log.timestamp)
          }
        })
        
        agentLogLine.value = res.data.from_line + newLogs.length
        
        nextTick(() => {
          if (rightPanel.value) {
            // Bei abgeschlossener Aufgabe nach oben scrollen; sonst nach unten zum neuesten Log
            if (isComplete.value) {
              rightPanel.value.scrollTop = 0
            } else {
              rightPanel.value.scrollTop = rightPanel.value.scrollHeight
            }
          }
        })
      }
    }
  } catch (err) {
    console.warn('Failed to fetch agent log:', err)
  }
}

// Endantwort-Inhalt extrahieren - Abschnittsinhalte aus LLM-Antwort extrahieren
const extractFinalContent = (response) => {
  if (!response) return null
  
  // Versuche Inhalt innerhalb des <final_answer>-Tags zu extrahieren
  const finalAnswerTagMatch = response.match(/<final_answer>([\s\S]*?)<\/final_answer>/)
  if (finalAnswerTagMatch) {
    return finalAnswerTagMatch[1].trim()
  }
  
  // Versuche Inhalt nach Final Answer: zu finden (verschiedene Formate)
  // Format 1: Final Answer:\n\nInhalt
  // Format 2: Final Answer: Inhalt
  const finalAnswerMatch = response.match(/Final\s*Answer:\s*\n*([\s\S]*)$/i)
  if (finalAnswerMatch) {
    return finalAnswerMatch[1].trim()
  }
  
  // Versuche Inhalt nach Endgültige Antwort: zu finden
  const chineseFinalMatch = response.match(/(?:最终答案|Endgültige Antwort|Finale Antwort|Abschließende Antwort)[:：]\s*\n*([\s\S]*)$/i)
  if (chineseFinalMatch) {
    return chineseFinalMatch[1].trim()
  }
  
  // Wenn mit ## oder # oder > beginnend, möglicherweise direkter Markdown-Inhalt
  const trimmedResponse = response.trim()
  if (trimmedResponse.match(/^[#>]/)) {
    return trimmedResponse
  }
  
  // Bei langem Inhalt mit Markdown-Format versuchen, Denkprozess zu entfernen und zurückzugeben
  if (response.length > 300 && (response.includes('**') || response.includes('>'))) {
    // Denkprozess mit Thought:-Anfang entfernen
    const thoughtMatch = response.match(/^Thought:[\s\S]*?(?=\n\n[^T]|\n\n$)/i)
    if (thoughtMatch) {
      const afterThought = response.substring(thoughtMatch[0].length).trim()
      if (afterThought.length > 100) {
        return afterThought
      }
    }
  }
  
  return null
}

const fetchConsoleLog = async () => {
  if (!props.reportId) return
  
  try {
    const res = await getConsoleLog(props.reportId, consoleLogLine.value)
    
    if (res.success && res.data) {
      const newLogs = res.data.logs || []
      
      if (newLogs.length > 0) {
        consoleLogs.value.push(...newLogs)
        consoleLogLine.value = res.data.from_line + newLogs.length
        
        nextTick(() => {
          if (logContent.value) {
            logContent.value.scrollTop = logContent.value.scrollHeight
          }
        })
      }
    }
  } catch (err) {
    console.warn('Failed to fetch console log:', err)
  }
}

const startPolling = () => {
  if (agentLogTimer || consoleLogTimer) return
  
  fetchAgentLog()
  fetchConsoleLog()
  
  agentLogTimer = setInterval(fetchAgentLog, 2000)
  consoleLogTimer = setInterval(fetchConsoleLog, 1500)
}

const stopPolling = () => {
  if (agentLogTimer) {
    clearInterval(agentLogTimer)
    agentLogTimer = null
  }
  if (consoleLogTimer) {
    clearInterval(consoleLogTimer)
    consoleLogTimer = null
  }
}

// Lifecycle
onMounted(() => {
  if (props.reportId) {
    addLog(t('step4.reportAgentInitialized', { id: props.reportId }))
    startPolling()
  }
})

onUnmounted(() => {
  stopPolling()
})

watch(() => props.reportId, (newId) => {
  if (newId) {
    agentLogs.value = []
    consoleLogs.value = []
    agentLogLine.value = 0
    consoleLogLine.value = 0
    reportOutline.value = null
    currentSectionIndex.value = null
    generatedSections.value = {}
    expandedContent.value = new Set()
    expandedLogs.value = new Set()
    collapsedSections.value = new Set()
    isComplete.value = false
    methodology.value = null
    startTime.value = null
    
    startPolling()
  }
}, { immediate: true })
</script>

<style scoped>
.report-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-surface-subtle);
  font-family: var(--font-body);
  overflow: hidden;
}

/* Main Split Layout — der Bericht füllt die Fläche, das Protokoll liegt darunter */
.main-split-layout {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

/* Panel Headers */
.panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px;
  background: var(--color-bg-surface-raised);
  border-bottom: 1px solid var(--color-border-default);
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
  text-transform: none;
  letter-spacing: normal;
  position: sticky;
  top: 0;
  z-index: 10;
}

.header-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-text-primary);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  margin-right: 10px;
  flex-shrink: 0;
  animation: pulse-dot 1.5s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% {
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  }
  50% {
    box-shadow: 0 0 0 5px color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  }
}

.header-index {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-muted);
  margin-right: 10px;
  flex-shrink: 0;
}

.header-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-transform: none;
  letter-spacing: 0;
}

.header-meta {
  margin-left: auto;
  font-size: 10px;
  font-weight: 600;
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

/* Panel header status variants */
.panel-header--active {
  background: var(--color-bg-surface-subtle);
  border-color: var(--color-text-primary);
}

.panel-header--active .header-index {
  color: var(--color-text-primary);
}

.panel-header--active .header-title {
  color: var(--color-text-primary);
}

.panel-header--active .header-meta {
  color: var(--color-text-primary);
}

.panel-header--done {
  background: var(--color-bg-surface-subtle);
}

.panel-header--done .header-index {
  color: var(--color-success-text);
}

.panel-header--todo .header-index,
.panel-header--todo .header-title {
  color: var(--color-text-muted);
}

/* Left Panel - Report Style */
.left-panel.report-style {
  width: 100%;
  min-width: 0;
  flex: 1;
  min-height: 0;
  background: var(--color-bg-canvas);
  border-right: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  padding: 28px 16px 72px;
}

.left-panel::-webkit-scrollbar {
  width: 6px;
}

.left-panel::-webkit-scrollbar-track {
  background: transparent;
}

.left-panel::-webkit-scrollbar-thumb {
  background: transparent;
  border-radius: 3px;
  transition: background 0.3s ease;
}

.left-panel:hover::-webkit-scrollbar-thumb {
  background: color-mix(in srgb, var(--color-text-primary) 12%, transparent);
}

.left-panel::-webkit-scrollbar-thumb:hover {
  background: color-mix(in srgb, var(--color-text-primary) 12%, transparent);
}

/* Report column: ~68 characters, centered. TOC sits beside it from 1024px. */
.article-shell {
  width: min(100%, 68ch);
  margin-inline: auto;
  font-size: 17px;
}

.report-toc {
  display: none;
}

.report-content-wrapper {
  max-width: 68ch;
  margin: 0 auto;
  width: 100%;
  font-size: inherit;
}

.report-header-block {
  margin-bottom: 2.5rem;
}

.report-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.report-tag {
  background: transparent;
  color: var(--color-brand-primary);
  font-family: var(--font-body);
  font-size: var(--font-size-xs);
  font-weight: 600;
  padding: 0;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.report-run-hint {
  color: var(--color-text-muted);
  font-family: var(--font-body);
  font-size: var(--font-size-xs);
  font-weight: 500;
  letter-spacing: 0.02em;
}

.methodology-card {
  margin-top: 2.5rem;
  padding: 1.25rem 1.35rem;
  background: var(--color-bg-surface-raised);
  border: 1px solid var(--color-border-default);
  border-radius: var(--radius-md, 6px);
  color: var(--color-text-secondary);
}

.methodology-title {
  font-family: var(--font-heading);
  font-size: var(--font-size-lg, 1.125rem);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 0.5rem 0;
}

.methodology-disclaimer {
  margin: 0 0 1rem 0;
  color: var(--color-text-secondary);
  font-size: 0.95rem;
  line-height: 1.5;
}

.methodology-list {
  margin: 0;
  padding-left: 1.1rem;
  font-size: 0.9rem;
  line-height: 1.55;
  color: var(--color-text-secondary);
}

.methodology-subtitle {
  font-family: var(--font-heading);
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 1.1rem 0 0.4rem 0;
}

.methodology-material ul {
  margin: 0;
  padding-left: 0;
  list-style: none;
  font-size: 0.875rem;
  line-height: 1.5;
}

.material-item {
  margin: 0 0 0.85rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--color-border-subtle);
}
.material-item:last-child { border-bottom: 0; margin-bottom: 0; padding-bottom: 0; }
.material-item__claim { margin: 0 0 4px; color: var(--color-text-primary); }
.material-item__count { color: var(--color-text-muted); margin-left: 4px; }
.material-item__source { margin: 0; font-size: 0.8rem; color: var(--color-text-muted); }
.material-item__snip summary {
  cursor: pointer;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  color: var(--color-text-secondary);
  font-size: 0.8rem;
}
.material-item__snip p {
  margin: 4px 0 0;
  padding: 8px 10px;
  background: var(--color-bg-surface-subtle);
  border-radius: 8px;
  color: var(--color-text-secondary);
}

.methodology-overlap {
  color: var(--color-text-muted);
  margin-right: 0.35rem;
  font-size: 0.8rem;
}

.ensemble-list ul {
  margin: 0;
  padding-left: 0;
  list-style: none;
  font-size: 0.9rem;
}
.ensemble-list li { margin: 0 0 6px; }
.ensemble-list a {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
  min-height: 44px;
  color: var(--color-brand-primary);
  text-decoration: none;
  font-weight: 600;
}
.ensemble-list .muted { color: var(--color-text-muted); font-weight: 400; }

.ens-form { display: grid; gap: 14px; }
.ens-field { margin: 0; padding: 0; border: 0; display: grid; gap: 8px; font-size: 14px; color: var(--color-text-secondary); }
.ens-field legend, .ens-field > span { font-weight: 600; color: var(--color-text-primary); }
.ens-pills { display: flex; flex-wrap: wrap; gap: 8px; }
.ens-pill {
  min-height: 44px;
  min-width: 44px;
  padding: 0 14px;
  border-radius: 12px;
  border: 1px solid var(--color-border-default);
  background: var(--color-bg-surface-raised);
  color: var(--color-text-primary);
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}
.ens-pill.is-on {
  background: var(--color-brand-primary);
  border-color: var(--color-brand-primary);
  color: var(--color-brand-on-primary);
}
.ens-input {
  min-height: 44px;
  padding: 0 12px;
  border-radius: 12px;
  border: 1px solid var(--color-border-default);
  background: var(--color-bg-surface-raised);
  color: inherit;
  font: inherit;
  max-width: 120px;
}
.ens-check {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 44px;
  color: var(--color-text-primary);
}
.ens-check input { width: 20px; height: 20px; }
.ens-eta { margin: 0; font-size: 13px; color: var(--color-text-muted); }
.ens-custom__hint { margin: 0; font-size: 13px; line-height: 1.45; color: var(--color-text-muted); font-weight: 400; }
.ens-custom__row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  align-items: start;
  padding: 10px 0;
  border-top: 1px solid var(--color-border-subtle);
}
.ens-custom__text { display: grid; gap: 4px; grid-column: 1 / -1; }
.ens-custom__input {
  min-height: 44px;
  width: 100%;
  padding: 0 12px;
  border-radius: 12px;
  border: 1px solid var(--color-border-default);
  background: var(--color-bg-surface-raised);
  color: inherit;
  font: inherit;
  box-sizing: border-box;
}
.ens-custom__input.is-invalid { border-color: var(--color-error-text); }
.ens-custom__count { font-size: 12px; color: var(--color-text-muted); justify-self: end; }
.ens-custom__count.is-warn { color: var(--color-warning-text); }
.ens-custom__polarity { display: flex; flex-wrap: wrap; gap: 8px; }
.ens-pill--sm { font-size: 13px; padding: 0 12px; }
.ens-custom__remove {
  min-width: 44px;
  min-height: 44px;
  border: 1px solid var(--color-border-subtle);
  border-radius: 12px;
  background: var(--color-bg-surface-subtle);
  color: var(--color-text-secondary);
  font: inherit;
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
}
.ens-custom__add {
  min-height: 44px;
  padding: 0 14px;
  border-radius: 12px;
  border: 1px dashed var(--color-border-default);
  background: transparent;
  color: var(--color-text-primary);
  font: inherit;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  justify-self: start;
}
.ens-custom__error { margin: 0; font-size: 13px; color: var(--color-error-text); }
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.report-id {
  font-size: 11px;
  color: var(--color-text-muted);
  font-weight: 500;
  letter-spacing: normal;
}

.main-title {
  font-family: var(--font-heading);
  font-size: var(--font-size-display);
  font-weight: 700;
  color: var(--color-text-primary);
  line-height: var(--line-height-tight);
  margin: 0 0 0.6em 0;
  letter-spacing: -0.02em;
}

.sub-title {
  font-family: var(--font-body);
  font-size: 1.0625rem;
  color: var(--color-text-secondary);
  font-style: normal;
  line-height: 1.6;
  margin: 0;
  font-weight: 400;
  max-width: 68ch;
}

.report-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 1.25rem;
}

.report-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 44px;
  padding: 0 16px;
  border-radius: var(--radius-full);
  border: 1px solid var(--color-border-default);
  background: var(--color-bg-surface);
  color: var(--color-text-primary);
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
  font-weight: 600;
  line-height: 1.2;
  text-decoration: none;
  cursor: pointer;
}

.report-action:hover {
  border-color: var(--color-brand-primary);
  color: var(--color-brand-primary);
}

.report-action:focus-visible {
  outline: 2px solid var(--color-focus-ring);
  outline-offset: 2px;
}

.header-divider {
  height: 1px;
  background: var(--color-border-subtle);
  width: 100%;
}

/* Sections List */
.sections-list {
  display: flex;
  flex-direction: column;
  gap: 2.75rem;
}

.report-section-item {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-header-row {
  display: flex;
  align-items: center;
  gap: 10px;
  transition: background-color 0.2s ease;
  padding: 4px 0;
  margin: 0;
  border-radius: var(--radius-md);
}

.section-header-row.clickable {
  cursor: pointer;
}

.section-header-row.clickable:hover {
  background-color: var(--color-bg-surface-subtle);
}

.collapse-toggle {
  margin-left: auto;
  width: 44px;
  height: 44px;
  min-width: 44px;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: 0;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  flex-shrink: 0;
}

.collapse-toggle:hover {
  background: var(--color-bg-surface-subtle);
  color: var(--color-text-primary);
}

.collapse-toggle:focus-visible {
  outline: 2px solid var(--color-focus-ring);
  outline-offset: 2px;
}

.collapse-icon {
  display: block;
  color: currentColor;
  transition: transform 0.3s ease;
  pointer-events: none;
}

.collapse-icon.is-collapsed {
  transform: rotate(-90deg);
}

.section-number {
  font-family: var(--font-body);
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  font-weight: 600;
  letter-spacing: 0.04em;
  font-variant-numeric: tabular-nums;
}

.section-title {
  font-family: var(--font-heading);
  font-size: var(--font-size-h2);
  font-weight: 600;
  line-height: var(--line-height-heading);
  color: var(--color-text-primary);
  margin: 0;
  letter-spacing: -0.015em;
  transition: color 0.3s ease;
}

/* States */
.report-section-item.is-pending .section-title {
  color: var(--color-border-strong);
}

.report-section-item.is-active .section-title,
.report-section-item.is-completed .section-title {
  color: var(--color-text-primary);
}

.section-body {
  padding-left: 0;
  overflow: hidden;
}

.report-section-item {
  scroll-margin-top: 16px;
}

/* Generated Content */
.generated-content {
  font-family: var(--font-body);
  font-size: 1em;
  line-height: 1.7;
  color: var(--color-text-primary);
  max-width: 68ch;
}

.generated-content :deep(p),
.generated-content :deep(.md-p) {
  margin: 0 0 1em;
  color: var(--color-text-primary);
}

.generated-content :deep(p:last-child) {
  margin-bottom: 0;
}

.generated-content :deep(.md-h2),
.generated-content :deep(.md-h3),
.generated-content :deep(.md-h4),
.generated-content :deep(.md-h5) {
  font-family: var(--font-heading);
  color: var(--color-text-primary);
  line-height: var(--line-height-heading);
  margin-top: 1.75em;
  margin-bottom: 0.45em;
  font-weight: 600;
  letter-spacing: -0.015em;
}

.generated-content :deep(.md-h2) { font-size: 1.35rem; }
.generated-content :deep(.md-h3) { font-size: 1.2rem; }
.generated-content :deep(.md-h4) { font-size: 1.05rem; }
.generated-content :deep(.md-h5) { font-size: 1rem; }

.generated-content :deep(.md-h2:first-child),
.generated-content :deep(.md-h3:first-child),
.generated-content :deep(.md-h4:first-child),
.generated-content :deep(.md-h5:first-child) {
  margin-top: 0;
}

.generated-content :deep(.md-ul),
.generated-content :deep(.md-ol) {
  padding-left: 1.4em;
  margin: 0 0 1em;
}

.generated-content :deep(.md-li),
.generated-content :deep(.md-oli) {
  margin: 0.35em 0;
  padding-left: 0.2em;
}

.generated-content :deep(.md-li[data-level="1"]),
.generated-content :deep(.md-oli[data-level="1"]) { margin-left: 1.25em; }
.generated-content :deep(.md-li[data-level="2"]),
.generated-content :deep(.md-oli[data-level="2"]) { margin-left: 2.5em; }

.generated-content :deep(.md-quote) {
  border: 0;
  border-left: 3px solid var(--color-brand-primary);
  background: var(--color-bg-surface);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
  padding: 0.9em 1.15em;
  margin: 1.4em 0;
  color: var(--color-text-secondary);
  font-style: normal;
  font-family: var(--font-body);
  line-height: 1.7;
}

.generated-content :deep(.md-hr) {
  border: 0;
  border-top: 1px solid var(--color-border-subtle);
  margin: 2em 0;
}

.generated-content :deep(.code-block) {
  background: var(--color-bg-surface-subtle);
  padding: 12px;
  border-radius: 6px;
  font-family: var(--font-body);
  font-size: 12px;
  overflow-x: auto;
  margin: 1em 0;
  border: 1px solid var(--color-border-default);
}

.generated-content :deep(strong) {
  font-weight: 600;
  color: var(--color-text-primary);
}

/* Loading State */
.loading-state {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--color-text-secondary);
  font-size: 14px;
  margin-top: 4px;
}

.loading-icon {
  width: 18px;
  height: 18px;
  animation: spin 1s linear infinite;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-text {
  font-family: var(--font-heading);
  font-size: 15px;
  color: var(--color-text-secondary);
}

.cursor-blink {
  display: inline-block;
  width: 8px;
  height: 14px;
  background: var(--color-info-text);
  opacity: 0.5;
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 0; }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Content Styles Override for this view */
.generated-content :deep(.md-h2) {
  font-family: var(--font-heading);
}


/* Slide Content Transition */
.slide-content-enter-active {
  transition: opacity 0.3s ease-out;
}

.slide-content-leave-active {
  transition: opacity 0.2s ease-in;
}

.slide-content-enter-from,
.slide-content-leave-to {
  opacity: 0;
}

.slide-content-enter-to,
.slide-content-leave-from {
  opacity: 1;
}

/* Waiting Placeholder */
.waiting-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  padding: 40px;
  color: var(--color-text-muted);
}

.waiting-animation {
  position: relative;
  width: 48px;
  height: 48px;
}

.waiting-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 2px solid var(--color-border-default);
  border-radius: 50%;
  animation: ripple 2s cubic-bezier(0.4, 0, 0.2, 1) infinite;
}

.waiting-ring:nth-child(2) {
  animation-delay: 0.4s;
}

.waiting-ring:nth-child(3) {
  animation-delay: 0.8s;
}

@keyframes ripple {
  0% { transform: scale(0.5); opacity: 1; }
  100% { transform: scale(2); opacity: 0; }
}

.waiting-text {
  font-size: 14px;
}

/* Arbeitsprotokoll: für Leser zugeklappt */
.report-origin {
  flex-shrink: 0;
  border-top: 1px solid var(--color-border-subtle);
  background: var(--color-bg-surface);
}

.report-origin-summary {
  display: flex;
  align-items: center;
  min-height: 44px;
  padding: 0 16px;
  cursor: pointer;
  font-family: var(--font-body);
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-secondary);
  list-style: none;
}

.report-origin-summary::-webkit-details-marker {
  display: none;
}

.report-origin-summary::before {
  content: '';
  width: 0;
  height: 0;
  margin-right: 10px;
  border-top: 5px solid transparent;
  border-bottom: 5px solid transparent;
  border-left: 6px solid var(--color-text-muted);
  transition: transform var(--transition-fast);
}

.report-origin[open] > .report-origin-summary::before {
  transform: rotate(90deg);
}

.report-origin-summary:focus-visible {
  outline: 2px solid var(--color-focus-ring);
  outline-offset: -2px;
}

.origin-body {
  border-top: 1px solid var(--color-border-subtle);
}

.origin-body .right-panel {
  max-height: min(46vh, 480px);
  overflow-y: auto;
}

/* Right Panel */
.right-panel {
  flex: 1;
  background: var(--color-bg-surface-raised);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.right-panel::-webkit-scrollbar {
  width: 6px;
}

.right-panel::-webkit-scrollbar-track {
  background: transparent;
}

.right-panel::-webkit-scrollbar-thumb {
  background: transparent;
  border-radius: 3px;
  transition: background 0.3s ease;
}

.right-panel:hover::-webkit-scrollbar-thumb {
  background: color-mix(in srgb, var(--color-text-primary) 12%, transparent);
}

.right-panel::-webkit-scrollbar-thumb:hover {
  background: color-mix(in srgb, var(--color-text-primary) 12%, transparent);
}

.mono {
  font-family: var(--font-body);
}

/* Workflow Overview */
.workflow-overview {
  padding: 16px 20px 0 20px;
}

.workflow-metrics {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.metric {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
}

.metric-right {
  margin-left: auto;
}

.metric-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: none;
  letter-spacing: normal;
}

.metric-value {
  font-size: 12px;
  color: var(--color-text-primary);
}

.metric-pill {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: normal;
  text-transform: none;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid var(--color-border-default);
  background: var(--color-bg-surface-subtle);
  color: var(--color-text-secondary);
}

.metric-pill.pill--processing {
  background: var(--color-bg-surface-subtle);
  border-color: var(--color-text-primary);
  color: var(--color-text-primary);
}

.metric-pill.pill--completed {
  background: var(--color-success-bg);
  border-color: var(--color-success-border);
  color: var(--color-success-text);
}

.metric-pill.pill--pending {
  background: transparent;
  border-style: dashed;
  color: var(--color-text-secondary);
}

.workflow-steps {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-bottom: 10px;
}

.wf-step {
  display: grid;
  grid-template-columns: 24px 1fr;
  gap: 12px;
  padding: 10px 12px;
  border: 1px solid var(--color-border-subtle);
  border-radius: 8px;
  background: var(--color-bg-surface-raised);
}

.wf-step--active {
  background: var(--color-bg-surface-subtle);
  border-color: var(--color-text-primary);
}

.wf-step--done {
  background: var(--color-bg-surface-subtle);
  border-color: var(--color-border-default);
}

.wf-step--todo {
  background: transparent;
  border-color: var(--color-border-default);
  border-style: dashed;
}

.wf-step-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 24px;
  flex-shrink: 0;
}

.wf-step-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--color-border-strong);
  border: 2px solid var(--color-bg-surface-raised);
  z-index: 1;
}

.wf-step-line {
  width: 2px;
  flex: 1;
  background: var(--color-border-subtle);
  margin-top: -2px;
}

.wf-step--active .wf-step-dot {
  background: var(--color-text-primary);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-text-primary) 12%, transparent);
}

.wf-step--done .wf-step-dot {
  background: var(--color-success-text);
}

.wf-step-title-row {
  display: flex;
  align-items: baseline;
  gap: 10px;
  min-width: 0;
}

.wf-step-index {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-text-muted);
  letter-spacing: normal;
  flex-shrink: 0;
}

.wf-step-title {
  font-family: var(--font-heading);
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1.35;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wf-step-meta {
  margin-left: auto;
  font-size: 10px;
  font-weight: 700;
  color: var(--color-text-primary);
  text-transform: none;
  letter-spacing: normal;
  flex-shrink: 0;
}

.wf-step--todo .wf-step-title,
.wf-step--todo .wf-step-index {
  color: var(--color-text-muted);
}

.workflow-divider {
  height: 1px;
  background: var(--color-border-subtle);
  margin: 14px 0 0 0;
}

/* Workflow Timeline */
.workflow-timeline {
  padding: 14px 20px 24px;
  flex: 1;
}

.timeline-item {
  display: grid;
  grid-template-columns: 24px 1fr;
  gap: 12px;
  padding: 10px 12px;
  margin-bottom: 10px;
  border: 1px solid var(--color-border-subtle);
  border-radius: 8px;
  background: var(--color-bg-surface-raised);
  transition: background-color 0.15s ease, border-color 0.15s ease;
}

.timeline-item:hover {
  background: var(--color-bg-surface-subtle);
  border-color: var(--color-border-default);
}

.timeline-item.node--active {
  background: var(--color-bg-surface-subtle);
  border-color: var(--color-text-primary);
}

.timeline-item.node--active:hover {
  background: var(--color-bg-surface-subtle);
  border-color: var(--color-text-primary);
}

.timeline-item.node--done {
  background: var(--color-bg-surface-subtle);
  border-color: var(--color-border-default);
}

.timeline-item.node--done:hover {
  background: var(--color-bg-surface-subtle);
  border-color: var(--color-border-default);
}

.timeline-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 24px;
  flex-shrink: 0;
}

.connector-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--color-border-strong);
  border: 2px solid var(--color-bg-surface-raised);
  z-index: 1;
}

.connector-line {
  width: 2px;
  flex: 1;
  background: var(--color-border-subtle);
  margin-top: -2px;
}

/* Connector dot: status only */
.dot-active {
  background: var(--color-text-primary);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-text-primary) 12%, transparent);
}

.dot-done {
  background: var(--color-success-text);
}

.dot-muted {
  background: var(--color-border-strong);
}

.timeline-content {
  min-width: 0;
  background: transparent;
  border: none;
  border-radius: 0;
  padding: 0;
  margin: 0;
  transition: none;
}

.timeline-content:hover {
  box-shadow: none;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.action-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-primary);
  text-transform: none;
  letter-spacing: normal;
}

.action-time {
  font-size: 11px;
  color: var(--color-text-muted);
  font-family: var(--font-body);
}

.timeline-body {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.timeline-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--color-border-subtle);
}

.elapsed-placeholder {
  flex-shrink: 0;
}

.footer-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.elapsed-badge {
  font-size: 11px;
  color: var(--color-text-secondary);
  background: var(--color-border-subtle);
  padding: 2px 8px;
  border-radius: 10px;
  font-family: var(--font-body);
}

/* Timeline Body Elements */
.info-row {
  display: flex;
  gap: 8px;
  margin-bottom: 6px;
}

.info-key {
  font-size: 11px;
  color: var(--color-text-muted);
  min-width: 80px;
}

.info-val {
  color: var(--color-text-primary);
}

.status-message {
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  border: 1px solid transparent;
}

.status-message.planning {
  background: var(--color-bg-surface-subtle);
  border-color: var(--color-text-primary);
  color: var(--color-text-primary);
}

.status-message.success {
  background: var(--color-success-bg);
  border-color: var(--color-success-border);
  color: var(--color-success-text);
}

.outline-badge {
  display: inline-block;
  margin-top: 8px;
  padding: 4px 10px;
  background: var(--color-bg-surface-subtle);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border-default);
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.section-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-default);
  border-radius: 6px;
}

.section-tag.content-ready {
  background: var(--color-bg-surface-subtle);
  border: 1px dashed var(--color-text-primary);
}

.section-tag.content-ready svg {
  color: var(--color-text-primary);
}


.section-tag.completed {
  background: var(--color-success-bg);
  border: 1px solid var(--color-success-border);
}

.section-tag.completed svg {
  color: var(--color-success-text);
}

.tag-num {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-text-secondary);
}

.section-tag.completed .tag-num {
  color: var(--color-success-text);
}

.tag-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.tool-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--color-bg-surface-subtle);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border-default);
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.tool-icon {
  flex-shrink: 0;
}

/* Tool Colors - Purple (Deep Insight) */
.tool-badge.tool-purple {
  background: linear-gradient(135deg, var(--color-info-bg) 0%, var(--color-info-bg) 100%);
  border-color: var(--color-info-border);
  color: var(--color-info-text);
}
.tool-badge.tool-purple .tool-icon {
  stroke: var(--color-info-text);
}

/* Tool Colors - Blue (Panorama Search) */
.tool-badge.tool-blue {
  background: linear-gradient(135deg, var(--color-info-bg) 0%, var(--color-info-bg) 100%);
  border-color: var(--color-info-border);
  color: var(--color-info-text);
}
.tool-badge.tool-blue .tool-icon {
  stroke: var(--color-info-text);
}

/* Tool Colors - Green (Agent Interview) */
.tool-badge.tool-green {
  background: linear-gradient(135deg, var(--color-success-bg) 0%, var(--color-success-bg) 100%);
  border-color: var(--color-success-border);
  color: var(--color-success-text);
}
.tool-badge.tool-green .tool-icon {
  stroke: var(--color-success-text);
}

/* Tool Colors - Orange (Quick Search) */
.tool-badge.tool-orange {
  background: linear-gradient(135deg, var(--color-warning-bg) 0%, var(--color-warning-bg) 100%);
  border-color: var(--color-warning-border);
  color: var(--color-brand-primary);
}
.tool-badge.tool-orange .tool-icon {
  stroke: var(--color-warning-text);
}

/* Tool Colors - Cyan (Graph Stats) */
.tool-badge.tool-cyan {
  background: linear-gradient(135deg, var(--color-info-bg) 0%, var(--color-info-bg) 100%);
  border-color: var(--color-info-border);
  color: var(--color-info-text);
}
.tool-badge.tool-cyan .tool-icon {
  stroke: var(--color-info-text);
}

/* Tool Colors - Pink (Entity Query) */
.tool-badge.tool-pink {
  background: linear-gradient(135deg, var(--color-error-bg) 0%, var(--color-error-bg) 100%);
  border-color: var(--color-error-border);
  color: var(--color-error-text);
}
.tool-badge.tool-pink .tool-icon {
  stroke: var(--color-error-text);
}

/* Tool Colors - Gray (Default) */
.tool-badge.tool-gray {
  background: linear-gradient(135deg, var(--color-bg-surface-subtle) 0%, var(--color-border-subtle) 100%);
  border-color: var(--color-border-strong);
  color: var(--color-text-primary);
}
.tool-badge.tool-gray .tool-icon {
  stroke: var(--color-text-secondary);
}

.tool-params {
  margin-top: 10px;
  background: transparent;
  border-radius: 0;
  padding: 10px 0 0 0;
  border-top: 1px dashed var(--color-border-subtle);
  overflow-x: auto;
}

.tool-params pre {
  margin: 0;
  font-family: var(--font-body);
  font-size: 11px;
  color: var(--color-text-secondary);
  white-space: pre-wrap;
  word-break: break-all;
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-default);
  border-radius: 6px;
  padding: 10px;
}

/* Unified Action Buttons */
.action-btn {
  background: var(--color-border-subtle);
  border: 1px solid var(--color-border-default);
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.action-btn:hover {
  background: var(--color-border-default);
  color: var(--color-text-primary);
  border-color: var(--color-border-strong);
}

/* Result Wrapper */
.result-wrapper {
  background: transparent;
  border: none;
  border-top: 1px solid var(--color-border-subtle);
  border-radius: 0;
  padding: 12px 0 0 0;
}

.result-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.result-tool {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.result-size {
  font-size: 10px;
  color: var(--color-text-secondary);
  font-family: var(--font-body);
}

.result-raw {
  margin-top: 10px;
  max-height: 300px;
  overflow-y: auto;
}

.result-raw pre {
  margin: 0;
  font-family: var(--font-body);
  font-size: 11px;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--color-text-primary);
  background: var(--color-bg-surface-raised);
  border: 1px solid var(--color-border-default);
  padding: 10px;
  border-radius: 6px;
}

.raw-preview {
  margin: 0;
  font-family: var(--font-body);
  font-size: 11px;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--color-text-secondary);
}

/* Legacy toggle-raw removed - using unified .action-btn */

/* LLM Response */
.llm-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.meta-tag {
  font-size: 11px;
  padding: 3px 8px;
  background: var(--color-border-subtle);
  color: var(--color-text-secondary);
  border-radius: 4px;
}

.meta-tag.active {
  background: var(--color-info-bg);
  color: var(--color-info-text);
}

.meta-tag.final-answer {
  background: var(--color-success-bg);
  color: var(--color-success-text);
  font-weight: 600;
}

.final-answer-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  padding: 10px 14px;
  background: var(--color-success-bg);
  border: 1px solid var(--color-success-border);
  border-radius: 6px;
  color: var(--color-success-text);
  font-size: 12px;
  font-weight: 500;
}

.final-answer-hint svg {
  flex-shrink: 0;
}

.llm-content {
  margin-top: 10px;
  max-height: 200px;
  overflow-y: auto;
}

.llm-content pre {
  margin: 0;
  font-family: var(--font-body);
  font-size: 11px;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--color-text-secondary);
  background: var(--color-border-subtle);
  padding: 10px;
  border-radius: 6px;
}

/* Complete Banner */
.complete-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--color-success-bg);
  border: 1px solid var(--color-success-border);
  border-radius: 8px;
  color: var(--color-success-text);
  font-weight: 600;
  font-size: 14px;
}

.next-step-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: calc(100% - 40px);
  margin: 4px 20px 0 20px;
  padding: 14px 20px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-inverse);
  background: var(--color-text-primary);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.next-step-btn:hover {
  background: var(--color-text-primary);
}

.next-step-btn svg {
  transition: transform 0.2s ease;
}

.next-step-btn:hover svg {
  transform: translateX(4px);
}

/* Workflow Empty */
.workflow-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--color-text-muted);
  font-size: 13px;
}

.empty-pulse {
  width: 24px;
  height: 24px;
  background: var(--color-border-default);
  border-radius: 50%;
  margin-bottom: 16px;
  animation: pulse-ring 1.5s infinite;
}

@keyframes pulse-ring {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.2); opacity: 0.5; }
}

/* Timeline Transitions */
.timeline-item-enter-active {
  transition: all 0.4s ease;
}

.timeline-item-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

/* ========== Structured Result Display Components ========== */

/* Common Styles - using :deep() for dynamic components */
:deep(.stat-row) {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

:deep(.stat-box) {
  flex: 1;
  background: var(--color-bg-surface-raised);
  border: 1px solid var(--color-border-default);
  border-radius: 6px;
  padding: 10px 8px;
  text-align: center;
}

:deep(.stat-box .stat-num) {
  display: block;
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text-primary);
  font-family: var(--font-body);
}

:deep(.stat-box .stat-label) {
  display: block;
  font-size: 10px;
  color: var(--color-text-muted);
  margin-top: 2px;
  text-transform: none;
  letter-spacing: normal;
}

:deep(.stat-box.highlight) {
  background: var(--color-success-bg);
  border-color: var(--color-success-border);
}

:deep(.stat-box.highlight .stat-num) {
  color: var(--color-success-text);
}

:deep(.stat-box.muted) {
  background: var(--color-bg-surface-subtle);
  border-color: var(--color-border-default);
}

:deep(.stat-box.muted .stat-num) {
  color: var(--color-text-secondary);
}

:deep(.query-display) {
  background: var(--color-bg-surface-subtle);
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 12px;
  color: var(--color-text-primary);
  margin-bottom: 12px;
  border: 1px solid var(--color-border-default);
  line-height: 1.5;
}

:deep(.expand-details) {
  background: var(--color-bg-surface-raised);
  border: 1px solid var(--color-border-default);
  padding: 8px 14px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
}

:deep(.expand-details:hover) {
  border-color: var(--color-border-strong);
  color: var(--color-text-primary);
}

:deep(.detail-content) {
  margin-top: 14px;
  background: var(--color-bg-surface-raised);
  border: 1px solid var(--color-border-default);
  border-radius: 8px;
  padding: 14px;
}

:deep(.section-label) {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: none;
  letter-spacing: normal;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--color-border-subtle);
}

/* Facts Section */
:deep(.facts-section) {
  margin-bottom: 14px;
}

:deep(.fact-row) {
  display: flex;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid var(--color-border-subtle);
}

:deep(.fact-row:last-child) {
  border-bottom: none;
}

:deep(.fact-row.active) {
  background: var(--color-success-bg);
  margin: 0 -10px;
  padding: 8px 10px;
  border-radius: 6px;
  border-bottom: none;
}

:deep(.fact-idx) {
  min-width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-border-subtle);
  border-radius: 6px;
  font-size: 10px;
  font-weight: 700;
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

:deep(.fact-row.active .fact-idx) {
  background: var(--color-success-border);
  color: var(--color-success-text);
}

:deep(.fact-text) {
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

/* Entities Section */
:deep(.entities-section) {
  margin-bottom: 14px;
}

:deep(.entity-chips) {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

:deep(.entity-chip) {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-default);
  border-radius: 6px;
  padding: 6px 12px;
}

:deep(.chip-name) {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-primary);
}

:deep(.chip-type) {
  font-size: 10px;
  color: var(--color-text-muted);
  background: var(--color-border-default);
  padding: 1px 6px;
  border-radius: 3px;
}

/* Relations Section */
:deep(.relations-section) {
  margin-bottom: 14px;
}

:deep(.relation-row) {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  flex-wrap: wrap;
  border-bottom: 1px solid var(--color-border-subtle);
}

:deep(.relation-row:last-child) {
  border-bottom: none;
}

:deep(.rel-node) {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-primary);
  background: var(--color-border-subtle);
  padding: 4px 10px;
  border-radius: 4px;
}

:deep(.rel-edge) {
  font-size: 10px;
  font-weight: 600;
  color: var(--color-text-inverse);
  background: var(--color-info-text);
  padding: 3px 10px;
  border-radius: 10px;
}

/* ========== Interview Display - Conversation Style ========== */
:deep(.interview-display) {
  padding: 0;
}

/* Header */
:deep(.interview-display .interview-header) {
  padding: 0;
  background: transparent;
  border-bottom: none;
  margin-bottom: 16px;
}

:deep(.interview-display .header-main) {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.interview-display .header-title) {
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: -0.01em;
}

:deep(.interview-display .header-stats) {
  display: flex;
  align-items: center;
  gap: 6px;
}

:deep(.interview-display .stat-item) {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

:deep(.interview-display .stat-value) {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-info-text);
  font-family: var(--font-body);
}

:deep(.interview-display .stat-label) {
  font-size: 11px;
  color: var(--color-text-muted);
  text-transform: lowercase;
}

:deep(.interview-display .stat-divider) {
  color: var(--color-border-strong);
  font-size: 12px;
}

:deep(.interview-display .stat-size) {
  font-size: 11px;
  color: var(--color-text-muted);
  font-family: var(--font-body);
}

:deep(.interview-display .header-topic) {
  margin-top: 4px;
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

/* Agent Tabs - Card Style */
:deep(.interview-display .agent-tabs) {
  display: flex;
  gap: 8px;
  padding: 0 0 14px 0;
  background: transparent;
  border-bottom: 1px solid var(--color-border-subtle);
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: thin;
  scrollbar-color: var(--color-border-default) transparent;
}

:deep(.interview-display .agent-tabs::-webkit-scrollbar) {
  height: 4px;
}

:deep(.interview-display .agent-tabs::-webkit-scrollbar-track) {
  background: transparent;
}

:deep(.interview-display .agent-tabs::-webkit-scrollbar-thumb) {
  background: var(--color-border-default);
  border-radius: 2px;
}

:deep(.interview-display .agent-tabs::-webkit-scrollbar-thumb:hover) {
  background: var(--color-border-strong);
}

:deep(.interview-display .agent-tab) {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-default);
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

:deep(.interview-display .agent-tab:hover) {
  background: var(--color-border-subtle);
  border-color: var(--color-border-strong);
  color: var(--color-text-primary);
}

:deep(.interview-display .agent-tab.active) {
  background: linear-gradient(135deg, var(--color-info-bg) 0%, var(--color-info-bg) 100%);
  border-color: var(--color-info-border);
  color: var(--color-text-secondary);
  box-shadow: 0 1px 2px color-mix(in srgb, var(--color-text-primary) 12%, transparent);
}

:deep(.interview-display .tab-avatar) {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-border-default);
  color: var(--color-text-secondary);
  font-size: 10px;
  font-weight: 700;
  border-radius: 50%;
  flex-shrink: 0;
}

:deep(.interview-display .agent-tab:hover .tab-avatar) {
  background: var(--color-border-strong);
}

:deep(.interview-display .agent-tab.active .tab-avatar) {
  background: var(--color-info-text);
  color: var(--color-text-inverse);
}

:deep(.interview-display .tab-name) {
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Interview Detail */
:deep(.interview-display .interview-detail) {
  padding: 12px 0;
  background: transparent;
}

/* Agent Profile - No card */
:deep(.interview-display .agent-profile) {
  display: flex;
  gap: 12px;
  padding: 0;
  background: transparent;
  border: none;
  margin-bottom: 16px;
}

:deep(.interview-display .profile-avatar) {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-border-default);
  color: var(--color-text-secondary);
  font-size: 14px;
  font-weight: 600;
  border-radius: 50%;
  flex-shrink: 0;
}

:deep(.interview-display .profile-info) {
  flex: 1;
  min-width: 0;
}

:deep(.interview-display .profile-name) {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 2px;
}

:deep(.interview-display .profile-role) {
  font-size: 11px;
  color: var(--color-text-secondary);
  margin-bottom: 4px;
}

:deep(.interview-display .profile-bio) {
  font-size: 11px;
  color: var(--color-text-muted);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Auswahlbegründung */
:deep(.interview-display .selection-reason) {
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-default);
  border-radius: 8px;
  padding: 12px 14px;
  margin-bottom: 16px;
}

:deep(.interview-display .reason-label) {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: none;
  letter-spacing: normal;
  margin-bottom: 6px;
}

:deep(.interview-display .reason-content) {
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

/* Q&A Thread - Clean list */
:deep(.interview-display .qa-thread) {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

:deep(.interview-display .qa-pair) {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: 0;
}

:deep(.interview-display .qa-question),
:deep(.interview-display .qa-answer) {
  display: flex;
  gap: 12px;
}

:deep(.interview-display .qa-badge) {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-body);
  font-size: 10px;
  font-weight: 700;
  border-radius: 4px;
  flex-shrink: 0;
}

:deep(.interview-display .q-badge) {
  background: transparent;
  color: var(--color-text-muted);
  border: 1px solid var(--color-border-default);
}

:deep(.interview-display .a-badge) {
  background: var(--color-info-text);
  color: var(--color-text-inverse);
  border: 1px solid var(--color-info-text);
}

:deep(.interview-display .qa-content) {
  flex: 1;
  min-width: 0;
}

:deep(.interview-display .qa-sender) {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
  margin-bottom: 4px;
  text-transform: none;
  letter-spacing: normal;
}

:deep(.interview-display .qa-text) {
  font-size: 13px;
  color: var(--color-text-primary);
  line-height: 1.6;
}

:deep(.interview-display .qa-answer) {
  background: transparent;
  padding: 0;
  border: none;
  margin-top: 0;
}

:deep(.interview-display .answer-placeholder) {
  opacity: 0.6;
}

:deep(.interview-display .placeholder-text) {
  font-style: italic;
  color: var(--color-text-muted);
}

:deep(.interview-display .qa-answer-header) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

/* Platform Switch */
:deep(.interview-display .platform-switch) {
  display: flex;
  gap: 2px;
  background: transparent;
  padding: 0;
  border-radius: 0;
}

:deep(.interview-display .platform-btn) {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all 0.15s ease;
}

:deep(.interview-display .platform-btn:hover) {
  color: var(--color-text-secondary);
}

:deep(.interview-display .platform-btn.active) {
  background: transparent;
  color: var(--color-info-text);
  border-color: var(--color-border-default);
  box-shadow: none;
}

:deep(.interview-display .platform-icon) {
  flex-shrink: 0;
}

:deep(.interview-display .answer-text) {
  font-size: 13px;
  color: var(--color-text-primary);
  line-height: 1.6;
}

:deep(.interview-display .answer-text strong) {
  color: var(--color-text-primary);
  font-weight: 600;
}

:deep(.interview-display .expand-answer-btn) {
  display: inline-block;
  margin-top: 8px;
  padding: 0;
  background: transparent;
  border: none;
  border-bottom: 1px dotted var(--color-border-strong);
  border-radius: 0;
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all 0.15s ease;
}

:deep(.interview-display .expand-answer-btn:hover) {
  background: transparent;
  color: var(--color-text-secondary);
  border-bottom-style: solid;
}

/* Quotes Section - Clean list */
:deep(.interview-display .quotes-section) {
  background: transparent;
  border: none;
  border-top: 1px solid var(--color-border-subtle);
  border-radius: 0;
  padding: 16px 0 0 0;
  margin-top: 16px;
}

:deep(.interview-display .quotes-header) {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: none;
  letter-spacing: normal;
  margin-bottom: 12px;
}

:deep(.interview-display .quotes-list) {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

:deep(.interview-display .quote-item) {
  margin: 0;
  padding: 12px 14px 12px 16px;
  background: var(--color-bg-surface);
  border: 0;
  border-left: 3px solid var(--color-brand-primary);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
  font-family: var(--font-body);
  font-size: 0.95em;
  font-style: normal;
  color: var(--color-text-secondary);
  line-height: 1.7;
}

/* Summary Section */
:deep(.interview-display .summary-section) {
  margin-top: 20px;
  padding: 16px 0 0 0;
  background: transparent;
  border: none;
  border-top: 1px solid var(--color-border-subtle);
  border-radius: 0;
}

:deep(.interview-display .summary-header) {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: none;
  letter-spacing: normal;
  margin-bottom: 8px;
}

:deep(.interview-display .summary-content) {
  font-size: 13px;
  color: var(--color-text-primary);
  line-height: 1.6;
}

/* Markdown styles in summary */
:deep(.interview-display .summary-content h2),
:deep(.interview-display .summary-content h3),
:deep(.interview-display .summary-content h4),
:deep(.interview-display .summary-content h5) {
  margin: 12px 0 8px 0;
  font-weight: 600;
  color: var(--color-text-primary);
}

:deep(.interview-display .summary-content h2) {
  font-size: 15px;
}

:deep(.interview-display .summary-content h3) {
  font-size: 14px;
}

:deep(.interview-display .summary-content h4),
:deep(.interview-display .summary-content h5) {
  font-size: 13px;
}

:deep(.interview-display .summary-content p) {
  margin: 8px 0;
}

:deep(.interview-display .summary-content strong) {
  font-weight: 600;
  color: var(--color-text-primary);
}

:deep(.interview-display .summary-content em) {
  font-style: italic;
}

:deep(.interview-display .summary-content ul),
:deep(.interview-display .summary-content ol) {
  margin: 8px 0;
  padding-left: 20px;
}

:deep(.interview-display .summary-content li) {
  margin: 4px 0;
}

:deep(.interview-display .summary-content blockquote) {
  margin: 1em 0;
  padding: 0.85em 1em;
  background: var(--color-bg-surface);
  border: 0;
  border-left: 3px solid var(--color-brand-primary);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
  color: var(--color-text-secondary);
  font-family: var(--font-body);
  font-style: normal;
  line-height: 1.7;
}

/* Markdown styles in quotes */
:deep(.interview-display .quote-item strong) {
  font-weight: 600;
  color: var(--color-text-primary);
}

:deep(.interview-display .quote-item em) {
  font-style: italic;
}

/* ========== Enhanced Insight Display Styles ========== */
:deep(.insight-display) {
  padding: 0;
}

:deep(.insight-header) {
  padding: 12px 16px;
  background: linear-gradient(135deg, var(--color-info-bg) 0%, var(--color-info-bg) 100%);
  border-radius: 8px 8px 0 0;
  border: 1px solid var(--color-info-border);
  border-bottom: none;
}

:deep(.insight-header .header-main) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

:deep(.insight-header .header-title) {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-info-text);
}

:deep(.insight-header .header-stats) {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
}

:deep(.insight-header .stat-item) {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

:deep(.insight-header .stat-value) {
  font-family: var(--font-body);
  font-weight: 700;
  color: var(--color-info-text);
}

:deep(.insight-header .stat-label) {
  color: var(--color-info-text);
  font-size: 10px;
}

:deep(.insight-header .stat-divider) {
  color: var(--color-info-border);
  margin: 0 4px;
}

:deep(.insight-header .stat-size) {
  font-family: var(--font-body);
  font-size: 10px;
  color: var(--color-text-muted);
}

:deep(.insight-header .header-topic) {
  font-size: 13px;
  color: var(--color-info-text);
  line-height: 1.5;
}

:deep(.insight-header .header-scenario) {
  margin-top: 6px;
  font-size: 11px;
  color: var(--color-info-text);
}

:deep(.insight-header .scenario-label) {
  font-weight: 600;
}

:deep(.insight-tabs) {
  display: flex;
  gap: 2px;
  padding: 8px 12px;
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-default);
  border-top: none;
}

:deep(.insight-tab) {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
}

:deep(.insight-tab:hover) {
  background: var(--color-border-subtle);
  color: var(--color-text-primary);
}

:deep(.insight-tab.active) {
  background: var(--color-bg-surface-raised);
  color: var(--color-info-text);
  border-color: var(--color-info-border);
  box-shadow: 0 1px 2px color-mix(in srgb, var(--color-text-primary) 12%, transparent);
}


:deep(.insight-content) {
  padding: 12px;
  background: var(--color-bg-surface-raised);
  border: 1px solid var(--color-border-default);
  border-top: none;
  border-radius: 0 0 8px 8px;
}

:deep(.insight-display .panel-header) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-border-subtle);
}

:deep(.insight-display .panel-title) {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-primary);
}

:deep(.insight-display .panel-count) {
  font-size: 10px;
  color: var(--color-text-muted);
}

:deep(.insight-display .facts-list),
:deep(.insight-display .relations-list),
:deep(.insight-display .subqueries-list) {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

:deep(.insight-display .entities-grid) {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

:deep(.insight-display .fact-item) {
  display: flex;
  gap: 10px;
  padding: 10px 12px;
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-default);
  border-radius: 6px;
}

:deep(.insight-display .fact-number) {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-border-default);
  border-radius: 50%;
  font-family: var(--font-body);
  font-size: 10px;
  font-weight: 700;
  color: var(--color-text-secondary);
}

:deep(.insight-display .fact-content) {
  flex: 1;
  font-size: 12px;
  color: var(--color-text-primary);
  line-height: 1.6;
}

/* Entity Tag Styles - Compact multi-column layout */
:deep(.insight-display .entity-tag) {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-default);
  border-radius: 6px;
  cursor: default;
  transition: all 0.15s ease;
}

:deep(.insight-display .entity-tag:hover) {
  background: var(--color-border-subtle);
  border-color: var(--color-border-strong);
}

:deep(.insight-display .entity-tag .entity-name) {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-primary);
}

:deep(.insight-display .entity-tag .entity-type) {
  font-size: 9px;
  color: var(--color-info-text);
  background: var(--color-info-bg);
  padding: 1px 4px;
  border-radius: 3px;
}

:deep(.insight-display .entity-tag .entity-fact-count) {
  font-size: 9px;
  color: var(--color-text-muted);
  margin-left: 2px;
}

/* Legacy entity card styles for backwards compatibility */
:deep(.insight-display .entity-card) {
  padding: 12px;
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-default);
  border-radius: 8px;
}

:deep(.insight-display .entity-header) {
  display: flex;
  align-items: center;
  gap: 10px;
}

:deep(.insight-display .entity-info) {
  flex: 1;
}

:deep(.insight-display .entity-card .entity-name) {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
}

:deep(.insight-display .entity-card .entity-type) {
  font-size: 10px;
  color: var(--color-info-text);
  background: var(--color-info-bg);
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-block;
  margin-top: 2px;
}

:deep(.insight-display .entity-card .entity-fact-count) {
  font-size: 10px;
  color: var(--color-text-muted);
  background: var(--color-border-subtle);
  padding: 2px 6px;
  border-radius: 4px;
}

:deep(.insight-display .entity-summary) {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--color-border-default);
  font-size: 11px;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

/* Relation Item Styles */
:deep(.insight-display .relation-item) {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-default);
  border-radius: 6px;
}

:deep(.insight-display .rel-source),
:deep(.insight-display .rel-target) {
  padding: 4px 8px;
  background: var(--color-bg-surface-raised);
  border: 1px solid var(--color-border-strong);
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-primary);
}

:deep(.insight-display .rel-arrow) {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
}

:deep(.insight-display .rel-line) {
  flex: 1;
  height: 1px;
  background: var(--color-border-strong);
}

:deep(.insight-display .rel-label) {
  padding: 2px 6px;
  background: var(--color-info-bg);
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
  color: var(--color-info-text);
  white-space: nowrap;
}

/* Sub-query Styles */
:deep(.insight-display .subquery-item) {
  display: flex;
  gap: 10px;
  padding: 10px 12px;
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-default);
  border-radius: 6px;
}

:deep(.insight-display .subquery-number) {
  flex-shrink: 0;
  padding: 2px 6px;
  background: var(--color-info-text);
  border-radius: 4px;
  font-family: var(--font-body);
  font-size: 10px;
  font-weight: 700;
  color: var(--color-text-inverse);
}

:deep(.insight-display .subquery-text) {
  font-size: 12px;
  color: var(--color-text-primary);
  line-height: 1.5;
}

/* Expand Button */
:deep(.insight-display .expand-btn),
:deep(.panorama-display .expand-btn),
:deep(.quick-search-display .expand-btn) {
  display: block;
  width: 100%;
  margin-top: 12px;
  padding: 8px 12px;
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-default);
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
  text-align: center;
}

:deep(.insight-display .expand-btn:hover),
:deep(.panorama-display .expand-btn:hover),
:deep(.quick-search-display .expand-btn:hover) {
  background: var(--color-border-subtle);
  color: var(--color-text-primary);
  border-color: var(--color-border-strong);
}

/* Empty State */
:deep(.insight-display .empty-state),
:deep(.panorama-display .empty-state),
:deep(.quick-search-display .empty-state) {
  padding: 24px;
  text-align: center;
  font-size: 12px;
  color: var(--color-text-muted);
}

/* ========== Enhanced Panorama Display Styles ========== */
:deep(.panorama-display) {
  padding: 0;
}

:deep(.panorama-header) {
  padding: 12px 16px;
  background: linear-gradient(135deg, var(--color-info-bg) 0%, var(--color-info-bg) 100%);
  border-radius: 8px 8px 0 0;
  border: 1px solid var(--color-info-border);
  border-bottom: none;
}

:deep(.panorama-header .header-main) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

:deep(.panorama-header .header-title) {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-info-text);
}

:deep(.panorama-header .header-stats) {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
}

:deep(.panorama-header .stat-item) {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

:deep(.panorama-header .stat-value) {
  font-family: var(--font-body);
  font-weight: 700;
  color: var(--color-info-text);
}

:deep(.panorama-header .stat-label) {
  color: var(--color-info-border);
  font-size: 10px;
}

:deep(.panorama-header .stat-divider) {
  color: var(--color-info-border);
  margin: 0 4px;
}

:deep(.panorama-header .stat-size) {
  font-family: var(--font-body);
  font-size: 10px;
  color: var(--color-text-muted);
}

:deep(.panorama-header .header-topic) {
  font-size: 13px;
  color: var(--color-info-text);
  line-height: 1.5;
}

:deep(.panorama-tabs) {
  display: flex;
  gap: 2px;
  padding: 8px 12px;
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-default);
  border-top: none;
}

:deep(.panorama-tab) {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
}

:deep(.panorama-tab:hover) {
  background: var(--color-border-subtle);
  color: var(--color-text-primary);
}

:deep(.panorama-tab.active) {
  background: var(--color-bg-surface-raised);
  color: var(--color-info-text);
  border-color: var(--color-info-border);
  box-shadow: 0 1px 2px color-mix(in srgb, var(--color-text-primary) 12%, transparent);
}


:deep(.panorama-content) {
  padding: 12px;
  background: var(--color-bg-surface-raised);
  border: 1px solid var(--color-border-default);
  border-top: none;
  border-radius: 0 0 8px 8px;
}

:deep(.panorama-display .panel-header) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-border-subtle);
}

:deep(.panorama-display .panel-title) {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-primary);
}

:deep(.panorama-display .panel-count) {
  font-size: 10px;
  color: var(--color-text-muted);
}

:deep(.panorama-display .facts-list) {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

:deep(.panorama-display .fact-item) {
  display: flex;
  gap: 10px;
  padding: 10px 12px;
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-default);
  border-radius: 6px;
}

:deep(.panorama-display .fact-item.active) {
  background: var(--color-bg-surface-subtle);
  border-color: var(--color-border-default);
}

:deep(.panorama-display .fact-item.historical) {
  background: var(--color-bg-surface-subtle);
  border-color: var(--color-border-default);
}

:deep(.panorama-display .fact-number) {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-border-default);
  border-radius: 50%;
  font-family: var(--font-body);
  font-size: 10px;
  font-weight: 700;
  color: var(--color-text-secondary);
}

:deep(.panorama-display .fact-item.active .fact-number) {
  background: var(--color-border-default);
  color: var(--color-text-secondary);
}

:deep(.panorama-display .fact-item.historical .fact-number) {
  background: var(--color-text-muted);
  color: var(--color-text-inverse);
}

:deep(.panorama-display .fact-content) {
  flex: 1;
  font-size: 12px;
  color: var(--color-text-primary);
  line-height: 1.6;
}

:deep(.panorama-display .fact-time) {
  display: block;
  font-size: 10px;
  color: var(--color-text-muted);
  margin-bottom: 4px;
  font-family: var(--font-body);
}

:deep(.panorama-display .fact-text) {
  display: block;
}

/* Entities Grid */
:deep(.panorama-display .entities-grid) {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

:deep(.panorama-display .entity-tag) {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-default);
  border-radius: 6px;
}

:deep(.panorama-display .entity-name) {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-primary);
}

:deep(.panorama-display .entity-type) {
  font-size: 10px;
  color: var(--color-info-text);
  background: var(--color-info-bg);
  padding: 2px 6px;
  border-radius: 4px;
}

/* ========== Enhanced Quick Search Display Styles ========== */
:deep(.quick-search-display) {
  padding: 0;
}

:deep(.quicksearch-header) {
  padding: 12px 16px;
  background: linear-gradient(135deg, var(--color-warning-bg) 0%, var(--color-warning-bg) 100%);
  border-radius: 8px 8px 0 0;
  border: 1px solid var(--color-warning-border);
  border-bottom: none;
}

:deep(.quicksearch-header .header-main) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

:deep(.quicksearch-header .header-title) {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-brand-primary);
}

:deep(.quicksearch-header .header-stats) {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
}

:deep(.quicksearch-header .stat-item) {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

:deep(.quicksearch-header .stat-value) {
  font-family: var(--font-body);
  font-weight: 700;
  color: var(--color-warning-text);
}

:deep(.quicksearch-header .stat-label) {
  color: var(--color-brand-primary);
  font-size: 10px;
}

:deep(.quicksearch-header .stat-divider) {
  color: var(--color-warning-border);
  margin: 0 4px;
}

:deep(.quicksearch-header .stat-size) {
  font-family: var(--font-body);
  font-size: 10px;
  color: var(--color-text-muted);
}

:deep(.quicksearch-header .header-query) {
  font-size: 13px;
  color: var(--color-brand-border);
  line-height: 1.5;
}

:deep(.quicksearch-header .query-label) {
  font-weight: 600;
}

:deep(.quicksearch-tabs) {
  display: flex;
  gap: 2px;
  padding: 8px 12px;
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-default);
  border-top: none;
}

:deep(.quicksearch-tab) {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
}

:deep(.quicksearch-tab:hover) {
  background: var(--color-border-subtle);
  color: var(--color-text-primary);
}

:deep(.quicksearch-tab.active) {
  background: var(--color-bg-surface-raised);
  color: var(--color-warning-text);
  border-color: var(--color-warning-border);
  box-shadow: 0 1px 2px color-mix(in srgb, var(--color-text-primary) 12%, transparent);
}


:deep(.quicksearch-content) {
  padding: 12px;
  background: var(--color-bg-surface-raised);
  border: 1px solid var(--color-border-default);
  border-top: none;
  border-radius: 0 0 8px 8px;
}

/* When there are no tabs, content connects directly to header */
:deep(.quicksearch-content.no-tabs) {
  border-top: none;
}

:deep(.quick-search-display .panel-header) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-border-subtle);
}

:deep(.quick-search-display .panel-title) {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-primary);
}

:deep(.quick-search-display .panel-count) {
  font-size: 10px;
  color: var(--color-text-muted);
}

:deep(.quick-search-display .facts-list) {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

:deep(.quick-search-display .fact-item) {
  display: flex;
  gap: 10px;
  padding: 10px 12px;
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-default);
  border-radius: 6px;
}

:deep(.quick-search-display .fact-item.active) {
  background: var(--color-bg-surface-subtle);
  border-color: var(--color-border-default);
}

:deep(.quick-search-display .fact-number) {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-border-default);
  border-radius: 50%;
  font-family: var(--font-body);
  font-size: 10px;
  font-weight: 700;
  color: var(--color-text-secondary);
}

:deep(.quick-search-display .fact-item.active .fact-number) {
  background: var(--color-border-default);
  color: var(--color-text-secondary);
}

:deep(.quick-search-display .fact-content) {
  flex: 1;
  font-size: 12px;
  color: var(--color-text-primary);
  line-height: 1.6;
}

/* Edges Panel */
:deep(.quick-search-display .edges-list) {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

:deep(.quick-search-display .edge-item) {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-default);
  border-radius: 6px;
}

:deep(.quick-search-display .edge-source),
:deep(.quick-search-display .edge-target) {
  padding: 4px 8px;
  background: var(--color-bg-surface-raised);
  border: 1px solid var(--color-border-strong);
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-primary);
}

:deep(.quick-search-display .edge-arrow) {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
}

:deep(.quick-search-display .edge-line) {
  flex: 1;
  height: 1px;
  background: var(--color-border-strong);
}

:deep(.quick-search-display .edge-label) {
  padding: 2px 6px;
  background: var(--color-warning-bg);
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
  color: var(--color-brand-primary);
  white-space: nowrap;
}

/* Nodes Grid */
:deep(.quick-search-display .nodes-grid) {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

:deep(.quick-search-display .node-tag) {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-default);
  border-radius: 6px;
}

:deep(.quick-search-display .node-name) {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-primary);
}

:deep(.quick-search-display .node-type) {
  font-size: 10px;
  color: var(--color-warning-text);
  background: var(--color-warning-bg);
  padding: 2px 6px;
  border-radius: 4px;
}

/* Console Logs - konsistent mit Step3Simulation.vue */
.console-logs {
  background: var(--color-bg-surface-subtle);
  color: var(--color-text-secondary);
  padding: 8px 16px;
  font-family: var(--font-body);
  border-top: 1px solid var(--color-border-subtle);
  flex-shrink: 0;
}
.console-logs > summary {
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
  list-style: none;
  min-height: 32px;
  display: flex;
  align-items: center;
}
.console-logs > summary::-webkit-details-marker { display: none; }
.console-logs[open] { padding-bottom: 12px; }
.console-logs[open] > summary {
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--color-border-subtle);
}

.log-header {
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid var(--color-border-subtle);
  padding-bottom: 8px;
  margin-bottom: 8px;
  font-size: 10px;
  color: var(--color-text-secondary);
}

.log-title {
  text-transform: none;
  letter-spacing: normal;
}

.log-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  height: 100px;
  overflow-y: auto;
  padding-right: 4px;
}

.log-content::-webkit-scrollbar { width: 4px; }
.log-content::-webkit-scrollbar-thumb { background: var(--color-text-primary); border-radius: 2px; }

.log-line {
  font-size: 11px;
  line-height: 1.5;
}

.log-msg {
  color: var(--color-border-strong);
  word-break: break-all;
}

.log-msg.error { color: var(--color-error-text); }
.log-msg.warning { color: var(--color-warning-text); }
.log-msg.success { color: var(--color-success-text); }
/* Mobile-first polish */
button, [role="button"], input, select, textarea { min-height: var(--touch-target-min); }
.toc-link { min-height: 0; }
h1, h2, h3, h4, h5, h6, .main-title, .section-title { font-family: var(--font-heading); }
.report-id { display: none; }
.generated-content, .tool-content, .timeline-content { overflow-wrap: anywhere; word-break: break-word; }
.generated-content { overflow-wrap: break-word; word-break: normal; }

.toc-label {
  margin: 0 0 10px;
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.toc-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.toc-link {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  width: 100%;
  padding: 4px 2px;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-secondary);
  font-family: var(--font-body);
  font-size: var(--font-size-xs);
  font-weight: 500;
  line-height: 1.4;
  text-align: left;
  cursor: pointer;
}

.toc-link:hover,
.toc-link.is-current {
  color: var(--color-text-primary);
}

.toc-link:focus-visible {
  outline: 2px solid var(--color-focus-ring);
  outline-offset: 2px;
}

.toc-num {
  flex-shrink: 0;
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
}

.toc-link.is-current .toc-num {
  color: var(--color-brand-primary);
}

.toc-title {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

@media (min-width: 1024px) {
  .left-panel.report-style { padding: 40px 32px 80px; }
  .article-shell {
    width: min(100%, calc(68ch + 220px));
    font-size: 18px;
    display: grid;
    grid-template-columns: 180px minmax(0, 68ch);
    column-gap: 40px;
    align-items: start;
  }
  .report-toc {
    display: block;
    position: sticky;
    top: 24px;
  }
  .sub-title { font-size: 1.2rem; }
}

@media (max-width: 1023px) {
  .report-panel { overflow-y: auto; }
  .main-split-layout { overflow: visible; flex: none; }
  .left-panel.report-style { overflow: visible; height: auto; flex: none; }
}

@media (max-width: 768px) {
  .next-step-btn { display: none; }
  .report-panel,
  .main-split-layout {
    height: auto;
    overflow: visible;
  }
  .report-main {
    padding-bottom: calc(64px + 58px + env(safe-area-inset-bottom, 0px));
  }
  .left-panel.report-style, .right-panel { width: 100%; min-width: 0; height: auto; overflow: visible; border-right: 0; }
  .left-panel.report-style { padding: 24px 16px 40px; border-bottom: 0; }
  .origin-body { max-height: none; overflow: visible; }
  .origin-body .right-panel { max-height: none; overflow: visible; }
  .workflow-metrics { flex-wrap: wrap; }
  .metric { min-width: calc(50% - 8px); }
  .footer-actions, .action-btn, .next-step-btn { width: 100%; }
}

@media print {
  .report-panel,
  .main-split-layout,
  .left-panel.report-style,
  .article-shell {
    height: auto !important;
    overflow: visible !important;
    width: 100% !important;
    max-width: none !important;
    min-width: 0 !important;
    display: block !important;
    background: var(--color-bg-canvas) !important;
    color: var(--color-text-primary) !important;
    border: 0 !important;
    padding: 0 !important;
  }
  .report-content-wrapper,
  .generated-content {
    max-width: 68ch !important;
    margin-left: auto !important;
    margin-right: auto !important;
    background: transparent !important;
    color: var(--color-text-primary) !important;
  }
  .report-origin,
  .report-actions,
  .report-toc,
  .collapse-toggle,
  .waiting-placeholder,
  .loading-state,
  button {
    display: none !important;
  }
  .section-body { display: block !important; }
  .main-title,
  .section-title,
  .sub-title,
  .generated-content,
  .generated-content :deep(*) {
    color: var(--color-text-primary) !important;
    background: transparent !important;
  }
  .generated-content :deep(.md-quote) {
    background: var(--color-bg-canvas) !important;
    border-left-color: var(--color-brand-primary) !important;
  }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; transition-duration: .01ms !important; }
}
</style>
