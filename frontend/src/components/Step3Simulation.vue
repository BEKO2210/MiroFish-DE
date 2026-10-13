<template>
  <div class="simulation-panel">
    <!-- Obere Steuerleiste -->
    <div class="control-bar">
      <div class="status-group">
        <!-- Twitter Plattform-Fortschritt -->
        <div class="platform-status twitter" :class="{ active: runStatus.twitter_running, completed: runStatus.twitter_completed }">
          <div class="platform-header">
            <svg class="platform-icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
            </svg>
            <span class="platform-name">{{ $t('step3.infoPlaza') }}</span>
            <span v-if="runStatus.twitter_completed" class="status-badge">
              <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="3">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
            </span>
          </div>
          <div class="platform-stats">
            <span class="stat">
              <span class="stat-label">{{ $t('step3.round') }}</span>
              <span class="stat-value mono">{{ runStatus.twitter_current_round || 0 }}<span class="stat-total">/{{ runStatus.total_rounds || maxRounds || '-' }}</span></span>
            </span>
            <span class="stat">
              <span class="stat-label">{{ $t('step3.vergangeneZeit') }}</span>
              <span class="stat-value mono">{{ twitterElapsedTime }}</span>
            </span>
            <span class="stat">
              <span class="stat-label">{{ $t('step3.acts') }}</span>
              <span class="stat-value mono">{{ runStatus.twitter_actions_count || 0 }}</span>
            </span>
          </div>
          <!-- Verfügbare Aktionen Tooltip -->
          <div class="actions-tooltip">
            <div class="tooltip-title">{{ $t('step3.verfugbareAktionen') }}</div>
            <div class="tooltip-actions">
              <span class="tooltip-action">{{ $t('step3.post') }}</span>
              <span class="tooltip-action">{{ $t('step3.like') }}</span>
              <span class="tooltip-action">{{ $t('step3.repost') }}</span>
              <span class="tooltip-action">{{ $t('step3.quote') }}</span>
              <span class="tooltip-action">{{ $t('step3.follow') }}</span>
              <span class="tooltip-action">{{ $t('step3.idle') }}</span>
            </div>
          </div>
        </div>
        
        <!-- Reddit Plattform-Fortschritt -->
        <div class="platform-status reddit" :class="{ active: runStatus.reddit_running, completed: runStatus.reddit_completed }">
          <div class="platform-header">
            <svg class="platform-icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
            </svg>
            <span class="platform-name">{{ $t('step3.topicCommunity') }}</span>
            <span v-if="runStatus.reddit_completed" class="status-badge">
              <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="3">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
            </span>
          </div>
          <div class="platform-stats">
            <span class="stat">
              <span class="stat-label">{{ $t('step3.round') }}</span>
              <span class="stat-value mono">{{ runStatus.reddit_current_round || 0 }}<span class="stat-total">/{{ runStatus.total_rounds || maxRounds || '-' }}</span></span>
            </span>
            <span class="stat">
              <span class="stat-label">{{ $t('step3.vergangeneZeit') }}</span>
              <span class="stat-value mono">{{ redditElapsedTime }}</span>
            </span>
            <span class="stat">
              <span class="stat-label">{{ $t('step3.acts') }}</span>
              <span class="stat-value mono">{{ runStatus.reddit_actions_count || 0 }}</span>
            </span>
          </div>
          <!-- Verfügbare Aktionen Tooltip -->
          <div class="actions-tooltip">
            <div class="tooltip-title">{{ $t('step3.verfugbareAktionen') }}</div>
            <div class="tooltip-actions">
              <span class="tooltip-action">{{ $t('step3.post') }}</span>
              <span class="tooltip-action">{{ $t('step3.comment') }}</span>
              <span class="tooltip-action">{{ $t('step3.like') }}</span>
              <span class="tooltip-action">{{ $t('step3.dislike') }}</span>
              <span class="tooltip-action">{{ $t('step3.search') }}</span>
              <span class="tooltip-action">{{ $t('step3.trend') }}</span>
              <span class="tooltip-action">{{ $t('step3.follow') }}</span>
              <span class="tooltip-action">{{ $t('step3.mute') }}</span>
              <span class="tooltip-action">{{ $t('step3.refresh') }}</span>
              <span class="tooltip-action">{{ $t('step3.idle') }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="action-controls">
        <button 
          class="action-btn primary"
          :disabled="phase !== 2 || isGeneratingReport"
          @click="handleNextStep"
        >
          <span v-if="isGeneratingReport" class="loading-spinner-small"></span>
          {{ isGeneratingReport ? $t('step3.wirdGestartet') : $t('step3.generateResultsReport') }}
          <span v-if="!isGeneratingReport" class="arrow-icon">→</span>
        </button>
      </div>
    </div>

    <!-- Hauptinhalt: Duale Zeitleiste -->
    <div class="main-content-area" ref="scrollContainer">
      <!-- Zeitleisten-Kopfzeile -->
      <div class="timeline-header" v-if="allActions.length > 0">
        <div class="timeline-stats">
          <span class="total-count">{{ $t('step3.ereignisseGesamt') }} <span class="mono">{{ allActions.length }}</span></span>
          <span class="platform-breakdown">
            <span class="breakdown-item twitter">
              <svg class="mini-icon" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
              <span class="mono">{{ twitterActionsCount }}</span>
            </span>
            <span class="breakdown-divider">/</span>
            <span class="breakdown-item reddit">
              <svg class="mini-icon" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>
              <span class="mono">{{ redditActionsCount }}</span>
            </span>
          </span>
        </div>
      </div>
      
      <!-- Zeitleisten-Feed -->
      <div class="timeline-feed">
        <div class="timeline-axis"></div>
        
        <TransitionGroup name="timeline-item">
          <div 
            v-for="action in chronologicalActions" 
            :key="action._uniqueId || action.id || `${action.timestamp}-${action.agent_id}`" 
            class="timeline-item"
            :class="action.platform"
          >
            <div class="timeline-marker">
              <div class="marker-dot"></div>
            </div>
            
            <div class="timeline-card">
              <div class="card-header">
                <div class="agent-info">
                  <div class="avatar-placeholder">{{ (action.agent_name || 'A')[0] }}</div>
                  <span class="agent-name">{{ action.agent_name }}</span>
                </div>
                
                <div class="header-meta">
                  <div class="platform-indicator">
                    <svg v-if="action.platform === 'twitter'" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
                    <svg v-else viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>
                  </div>
                  <div class="action-badge" :class="getActionTypeClass(action.action_type)">
                    {{ getActionTypeLabel(action.action_type) }}
                  </div>
                </div>
              </div>
              
              <div class="card-body">
                <!-- CREATE_POST: Beitrag erstellen -->
                <div v-if="action.action_type === 'CREATE_POST' && action.action_args?.content" class="content-text main-text">
                  {{ action.action_args.content }}
                </div>

                <!-- QUOTE_POST: Beitrag zitieren -->
                <template v-if="action.action_type === 'QUOTE_POST'">
                  <div v-if="action.action_args?.quote_content" class="content-text">
                    {{ action.action_args.quote_content }}
                  </div>
                  <div v-if="action.action_args?.original_content" class="quoted-block">
                    <div class="quote-header">
                      <svg class="icon-small" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
                      <span class="quote-label">@{{ action.action_args.original_author_name || $t('step3.user') }}</span>
                    </div>
                    <div class="quote-text">
                      {{ truncateContent(action.action_args.original_content, 150) }}
                    </div>
                  </div>
                </template>

                <!-- REPOST: Beitrag teilen -->
                <template v-if="action.action_type === 'REPOST'">
                  <div class="repost-info">
                    <svg class="icon-small" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="17 1 21 5 17 9"></polyline><path d="M3 11V9a4 4 0 0 1 4-4h14"></path><polyline points="7 23 3 19 7 15"></polyline><path d="M21 13v2a4 4 0 0 1-4 4H3"></path></svg>
                    <span class="repost-label">{{ $t('step3.repostedBy', { user: action.action_args?.original_author_name || $t('step3.user') }) }}</span>
                  </div>
                  <div v-if="action.action_args?.original_content" class="repost-content">
                    {{ truncateContent(action.action_args.original_content, 200) }}
                  </div>
                </template>

                <!-- LIKE_POST: Beitrag liken -->
                <template v-if="action.action_type === 'LIKE_POST'">
                  <div class="like-info">
                    <svg class="icon-small filled" viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
                    <span class="like-label">{{ $t('step3.likedPostBy', { user: action.action_args?.post_author_name || $t('step3.user') }) }}</span>
                  </div>
                  <div v-if="action.action_args?.post_content" class="liked-content">
                    "{{ truncateContent(action.action_args.post_content, 120) }}"
                  </div>
                </template>

                <!-- CREATE_COMMENT: Kommentar erstellen -->
                <template v-if="action.action_type === 'CREATE_COMMENT'">
                  <div v-if="action.action_args?.content" class="content-text">
                    {{ action.action_args.content }}
                  </div>
                  <div v-if="action.action_args?.post_id" class="comment-context">
                    <svg class="icon-small" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>
                    <span>{{ $t('step3.replyToPost', { id: action.action_args.post_id }) }}</span>
                  </div>
                </template>

                <!-- SEARCH_POSTS: Beiträge suchen -->
                <template v-if="action.action_type === 'SEARCH_POSTS'">
                  <div class="search-info">
                    <svg class="icon-small" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                    <span class="search-label">{{ $t('step3.searchQuery') }}</span>
                    <span class="search-query">"{{ action.action_args?.query || '' }}"</span>
                  </div>
                </template>

                <!-- FOLLOW: Benutzer folgen -->
                <template v-if="action.action_type === 'FOLLOW'">
                  <div class="follow-info">
                    <svg class="icon-small" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="20" y1="8" x2="20" y2="14"></line><line x1="23" y1="11" x2="17" y2="11"></line></svg>
                    <span class="follow-label">{{ $t('step3.nowFollowing', { user: action.action_args?.target_user || action.action_args?.user_id || $t('step3.user') }) }}</span>
                  </div>
                </template>

                <!-- UPVOTE / DOWNVOTE -->
                <template v-if="action.action_type === 'UPVOTE_POST' || action.action_type === 'DOWNVOTE_POST'">
                  <div class="vote-info">
                    <svg v-if="action.action_type === 'UPVOTE_POST'" class="icon-small" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="18 15 12 9 6 15"></polyline></svg>
                    <svg v-else class="icon-small" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
                    <span class="vote-label">{{ action.action_type === 'UPVOTE_POST' ? $t('step3.upvoted') : $t('step3.downvoted') }}</span>
                  </div>
                  <div v-if="action.action_args?.post_content" class="voted-content">
                    "{{ truncateContent(action.action_args.post_content, 120) }}"
                  </div>
                </template>

                <!-- DO_NOTHING: Keine Aktion (Leerlauf) -->
                <template v-if="action.action_type === 'DO_NOTHING'">
                  <div class="idle-info">
                    <svg class="icon-small" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                    <span class="idle-label">{{ $t('step3.actionSkipped') }}</span>
                  </div>
                </template>

                <!-- Allgemeiner Fallback: Unbekannter Typ oder Content, der oben nicht behandelt wurde -->
                <div v-if="!['CREATE_POST', 'QUOTE_POST', 'REPOST', 'LIKE_POST', 'CREATE_COMMENT', 'SEARCH_POSTS', 'FOLLOW', 'UPVOTE_POST', 'DOWNVOTE_POST', 'DO_NOTHING'].includes(action.action_type) && action.action_args?.content" class="content-text">
                  {{ action.action_args.content }}
                </div>
              </div>

              <div class="card-footer">
                <span class="time-tag">R{{ action.round_num }} • {{ formatActionTime(action.timestamp) }}</span>
                <!-- Plattform-Tag entfernt, da es jetzt im Header ist -->
              </div>
            </div>
          </div>
        </TransitionGroup>

        <div v-if="allActions.length === 0" class="waiting-state">
          <div class="pulse-ring"></div>
          <span>{{ $t('step3.waitingForAgentActions') }}</span>
        </div>
      </div>
    </div>

    <!-- Untere Info / Protokolle -->
    <div class="system-logs">
      <div class="log-header">
        <span class="log-title">{{ $t('step3.simulationMonitor') }}</span>
      </div>
      <div class="log-content" ref="logContent">
        <div class="log-line" v-for="(log, idx) in systemLogs" :key="idx">
          <span class="log-time">{{ log.time }}</span>
          <span class="log-msg">{{ log.msg }}</span>
        </div>
      </div>
    </div>
    <MobileStickyBar
      :primary-label="$t('step3.generateResultsReport')"
      :primary-disabled="phase !== 2"
      :primary-loading="isGeneratingReport"
      @primary-click="handleNextStep"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { 
  startSimulation, 
  stopSimulation,
  getRunStatus, 
  getRunStatusDetail
} from '../api/simulation'
import { generateReport } from '../api/report'
import MobileStickyBar from './MobileStickyBar.vue'

const { t } = useI18n()

const props = defineProps({
  simulationId: String,
  maxRounds: Number, // Maximale Rundenanzahl aus Step2
  minutesPerRound: {
    type: Number,
    default: 30 // Standard: 30 Minuten pro Runde
  },
  projectData: Object,
  graphData: Object,
  systemLogs: Array
})

const emit = defineEmits(['go-back', 'next-step', 'add-log', 'update-status'])

const router = useRouter()

// Zustand
const isGeneratingReport = ref(false)
const phase = ref(0) // 0: Nicht gestartet, 1: Läuft, 2: Abgeschlossen
const isStarting = ref(false)
const isStopping = ref(false)
const startError = ref(null)
const runStatus = ref({})
const allActions = ref([]) // Alle Aktionen (inkrementell gesammelt)
const actionIds = ref(new Set()) // Aktions-ID-Set zur Deduplizierung
const scrollContainer = ref(null)

// Computed
// Aktionen in chronologischer Reihenfolge anzeigen (neueste unten)
const chronologicalActions = computed(() => {
  return allActions.value
})

// Aktionszähler pro Plattform
const twitterActionsCount = computed(() => {
  return allActions.value.filter(a => a.platform === 'twitter').length
})

const redditActionsCount = computed(() => {
  return allActions.value.filter(a => a.platform === 'reddit').length
})

// Simulierte vergangene Zeit formatieren (basierend auf Runden und Minuten pro Runde)
const formatElapsedTime = (currentRound) => {
  if (!currentRound || currentRound <= 0) return '0h 0m'
  const totalMinutes = currentRound * props.minutesPerRound
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  return `${hours}h ${minutes}m`
}

// Simulierte vergangene Zeit der Twitter-Plattform
const twitterElapsedTime = computed(() => {
  return formatElapsedTime(runStatus.value.twitter_current_round || 0)
})

// Simulierte vergangene Zeit der Reddit-Plattform
const redditElapsedTime = computed(() => {
  return formatElapsedTime(runStatus.value.reddit_current_round || 0)
})

// Methods
const addLog = (msg) => {
  emit('add-log', msg)
}

// Alle Zustände zurücksetzen (für Neustart der Simulation)
const resetAllState = () => {
  phase.value = 0
  runStatus.value = {}
  allActions.value = []
  actionIds.value = new Set()
  prevTwitterRound.value = 0
  prevRedditRound.value = 0
  startError.value = null
  isStarting.value = false
  isStopping.value = false
  stopPolling()  // Vorherige Abfragen stoppen, falls vorhanden
}

// Simulation starten
const doStartSimulation = async () => {
  if (!props.simulationId) {
    addLog(t('step3.fehlerSimulationidFehlt'))
    return
  }

  // Alle Zustände zurücksetzen, um Einflüsse der vorherigen Simulation zu vermeiden
  resetAllState()

  isStarting.value = true
  startError.value = null
  addLog(t('step3.paralleleDualPlattformSimulationWirdGestartet'))
  emit('update-status', 'processing')
  
  try {
    const params = {
      simulation_id: props.simulationId,
      platform: 'parallel',
      force: true,  // Neustart erzwingen
      enable_graph_memory_update: true  // Dynamische Graph-Aktualisierung aktivieren
    }
    
    if (props.maxRounds) {
      params.max_rounds = props.maxRounds
    addLog(t('step3.maxRoundsSet', { count: props.maxRounds }))
    }
    
    addLog(t('step3.dynamischerGraphAktualisierungsmodusAktiviert'))
    
    const res = await startSimulation(params)
    
    if (res.success && res.data) {
      if (res.data.force_restarted) {
        addLog(t('step3.alteSimulationsprotokolleBereinigtSimulationWirdNeuGestartet'))
      }
      addLog(t('step3.simulationsengineErfolgreichGestartet'))
      addLog(`  ├─ PID: ${res.data.process_pid || '-'}`)
      
      phase.value = 1
      runStatus.value = res.data
      
      startStatusPolling()
      startDetailPolling()
    } else {
      startError.value = res.error || t('step3.startFehlgeschlagen')
      addLog(t('step3.startFehlgeschlagen2', { p0: res.error || t('common.unknownError') }))
      emit('update-status', 'error')
    }
  } catch (err) {
    startError.value = err.message
    addLog(t('step3.startException', { error: err.message }))
    emit('update-status', 'error')
  } finally {
    isStarting.value = false
  }
}

// Simulation stoppen
const handleStopSimulation = async () => {
  if (!props.simulationId) return
  
  isStopping.value = true
  addLog(t('step3.simulationWirdGestoppt'))
  
  try {
    const res = await stopSimulation({ simulation_id: props.simulationId })
    
    if (res.success) {
      addLog(t('step3.simulationGestoppt'))
      phase.value = 2
      stopPolling()
      emit('update-status', 'completed')
    } else {
      addLog(t('step3.stoppenFehlgeschlagen', { p0: res.error || t('common.unknownError') }))
    }
  } catch (err) {
    addLog(t('step3.stopException', { error: err.message }))
  } finally {
    isStopping.value = false
  }
}

// Statusabfrage
let statusTimer = null
let detailTimer = null

const startStatusPolling = () => {
  statusTimer = setInterval(fetchRunStatus, 2000)
}

const startDetailPolling = () => {
  detailTimer = setInterval(fetchRunStatusDetail, 3000)
}

const stopPolling = () => {
  if (statusTimer) {
    clearInterval(statusTimer)
    statusTimer = null
  }
  if (detailTimer) {
    clearInterval(detailTimer)
    detailTimer = null
  }
}

// Vorherige Runde pro Plattform verfolgen, um Änderungen zu erkennen und zu protokollieren
const prevTwitterRound = ref(0)
const prevRedditRound = ref(0)

const fetchRunStatus = async () => {
  if (!props.simulationId) return
  
  try {
    const res = await getRunStatus(props.simulationId)
    
    if (res.success && res.data) {
      const data = res.data
      
      runStatus.value = data
      
      // Rundenänderungen pro Plattform erkennen und protokollieren
      if (data.twitter_current_round > prevTwitterRound.value) {
        addLog(`[Plaza] R${data.twitter_current_round}/${data.total_rounds} | T:${data.twitter_simulated_hours || 0}h | A:${data.twitter_actions_count}`)
        prevTwitterRound.value = data.twitter_current_round
      }
      
      if (data.reddit_current_round > prevRedditRound.value) {
        addLog(`[Community] R${data.reddit_current_round}/${data.total_rounds} | T:${data.reddit_simulated_hours || 0}h | A:${data.reddit_actions_count}`)
        prevRedditRound.value = data.reddit_current_round
      }
      
      // Prüfen, ob die Simulation fehlgeschlagen oder abgeschlossen ist
      const isFailed = data.runner_status === 'failed'
      const isCompleted = data.runner_status === 'completed' || data.runner_status === 'stopped'
      
      // Zusätzliche Prüfung: Falls das Backend runner_status noch nicht aktualisiert hat,
      // aber die Plattformen bereits als abgeschlossen gemeldet sind
      const platformsCompleted = checkPlatformsCompleted(data)
      
      if (isFailed) {
        addLog(t('step3.simulationFehlgeschlagen') + (data.error ? ': ' + data.error : ''))
        phase.value = 2
        stopPolling()
        emit('update-status', 'error')
      } else if (isCompleted || platformsCompleted) {
        if (platformsCompleted && !isCompleted) {
          addLog(t('step3.allPlatformSimulationsFinished'))
        }
        addLog(t('step3.simulationAbgeschlossen'))
        phase.value = 2
        stopPolling()
        emit('update-status', 'completed')
      }
    }
  } catch (err) {
    console.warn(t('step3.laufzeitstatusKonnteNichtAbgerufenWerden'), err)
  }
}

// Prüfen, ob alle aktivierten Plattformen abgeschlossen sind
const checkPlatformsCompleted = (data) => {
  // Wenn keine Plattformdaten vorhanden, false zurückgeben
  if (!data) return false

  // Abschlussstatus jeder Plattform prüfen
  const twitterCompleted = data.twitter_completed === true
  const redditCompleted = data.reddit_completed === true

  // Prüfen, ob alle aktivierten Plattformen abgeschlossen sind
  // Plattform gilt als aktiviert, wenn count > 0 oder running einmal true war
  const twitterEnabled = (data.twitter_actions_count > 0) || data.twitter_running || twitterCompleted
  const redditEnabled = (data.reddit_actions_count > 0) || data.reddit_running || redditCompleted

  // Wenn keine Plattform aktiviert ist, false zurückgeben
  if (!twitterEnabled && !redditEnabled) return false

  // Prüfen, ob alle aktivierten Plattformen abgeschlossen sind
  if (twitterEnabled && !twitterCompleted) return false
  if (redditEnabled && !redditCompleted) return false
  
  return true
}

const fetchRunStatusDetail = async () => {
  if (!props.simulationId) return
  
  try {
    const res = await getRunStatusDetail(props.simulationId)
    
    if (res.success && res.data) {
      // Vollständige Aktionsliste über all_actions abrufen
      const serverActions = res.data.all_actions || []
      
      // Neue Aktionen inkrementell hinzufügen (mit Deduplizierung)
      let newActionsAdded = 0
      serverActions.forEach(action => {
        // Eindeutige ID generieren
        const actionId = action.id || `${action.timestamp}-${action.platform}-${action.agent_id}-${action.action_type}`
        
        if (!actionIds.value.has(actionId)) {
          actionIds.value.add(actionId)
          allActions.value.push({
            ...action,
            _uniqueId: actionId
          })
          newActionsAdded++
        }
      })
      
      // Kein automatisches Scrollen, damit der Benutzer die Zeitleiste frei durchsehen kann
      // Neue Aktionen werden unten angehängt
    }
  } catch (err) {
    console.warn(t('step3.detailstatusKonnteNichtAbgerufenWerden'), err)
  }
}

// Hilfsfunktionen
const getActionTypeLabel = (type) => {
  const labels = {
    'CREATE_POST': t('step3.post'),
    'REPOST': t('step3.repost'),
    'LIKE_POST': t('step3.like'),
    'CREATE_COMMENT': t('step3.comment'),
    'LIKE_COMMENT': t('step3.like'),
    'DO_NOTHING': t('step3.idle'),
    'FOLLOW': t('step3.follow'),
    'SEARCH_POSTS': t('step3.search'),
    'QUOTE_POST': t('step3.quote'),
    'UPVOTE_POST': t('step3.upvoted'),
    'DOWNVOTE_POST': t('step3.downvoted')
  }
  return labels[type] || t('common.none')
}

const getActionTypeClass = (type) => {
  const classes = {
    'CREATE_POST': 'badge-post',
    'REPOST': 'badge-action',
    'LIKE_POST': 'badge-action',
    'CREATE_COMMENT': 'badge-comment',
    'LIKE_COMMENT': 'badge-action',
    'QUOTE_POST': 'badge-post',
    'FOLLOW': 'badge-meta',
    'SEARCH_POSTS': 'badge-meta',
    'UPVOTE_POST': 'badge-action',
    'DOWNVOTE_POST': 'badge-action',
    'DO_NOTHING': 'badge-idle'
  }
  return classes[type] || 'badge-default'
}

const truncateContent = (content, maxLength = 100) => {
  if (!content) return ''
  if (content.length > maxLength) return content.substring(0, maxLength) + '...'
  return content
}

const formatActionTime = (timestamp) => {
  if (!timestamp) return ''
  try {
    return new Date(timestamp).toLocaleTimeString('de-DE', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return ''
  }
}

const handleNextStep = async () => {
  if (!props.simulationId) {
    addLog(t('step3.fehlerSimulationidFehlt'))
    return
  }

  if (isGeneratingReport.value) {
    addLog(t('step3.berichtgenerierungsanfrageGesendetBitteWarten'))
    return
  }

  isGeneratingReport.value = true
  addLog(t('step3.berichterstellungWirdGestartet'))
  
  try {
    const res = await generateReport({
      simulation_id: props.simulationId,
      force_regenerate: true
    })
    
    if (res.success && res.data) {
      const reportId = res.data.report_id
      addLog(t('step3.berichterstellungsaufgabeGestartet', { p0: reportId }))

      // Zur Berichtsseite navigieren
      router.push({ name: 'Report', params: { reportId } })
    } else {
      addLog(t('step3.startDerBerichterstellungFehlgeschlagen', { p0: res.error || t('common.unknownError') }))
      isGeneratingReport.value = false
    }
  } catch (err) {
    addLog(t('step3.ausnahmeBeimStartenDerBerichterstellung', { p0: err.message }))
    isGeneratingReport.value = false
  }
}

// Protokoll nach unten scrollen
const logContent = ref(null)
watch(() => props.systemLogs?.length, () => {
  nextTick(() => {
    if (logContent.value) {
      logContent.value.scrollTop = logContent.value.scrollHeight
    }
  })
})

onMounted(async () => {
  addLog(t('step3.initialized'))
  if (!props.simulationId) return
  // Laufende oder schon gelaufene Simulation nur anzeigen: doStartSimulation startet mit force neu und löscht
  // dabei die bisherigen Ergebnisse. Gestartet wird nur, was noch nie lief (Weg aus Schritt 2).
  try {
    const d = (await getRunStatus(props.simulationId))?.data
    if (d && ['running', 'starting'].includes(d.runner_status)) {
      runStatus.value = d
      phase.value = 1
      emit('update-status', 'processing')
      startStatusPolling()
      startDetailPolling()
      return
    }
    if (d && ((d.current_round || 0) > 0 || ['completed', 'stopped', 'failed'].includes(d.runner_status))) {
      runStatus.value = d
      phase.value = 2
      await fetchRunStatusDetail()
      emit('update-status', 'completed')
      return
    }
  } catch (err) {
    startError.value = t('step3.laufzeitstatusKonnteNichtAbgerufenWerden')
    return
  }
  doStartSimulation()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.simulation-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-surface-raised);
  font-family: var(--font-body);
  overflow: hidden;
}

/* --- Control Bar --- */
.control-bar {
  background: var(--color-bg-surface-raised);
  padding: 12px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--color-border-subtle);
  z-index: 10;
  height: 64px;
}

.status-group {
  display: flex;
  gap: 12px;
}

/* Platform Status Cards */
.platform-status {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 6px 12px;
  border-radius: 4px;
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-subtle);
  opacity: 0.7;
  transition: all 0.3s;
  min-width: 140px;
  position: relative;
  cursor: pointer;
}

.platform-status.active {
  opacity: 1;
  border-color: var(--color-text-primary);
  background: var(--color-bg-surface-raised);
}

.platform-status.completed {
  opacity: 1;
  border-color: var(--color-success-text);
  background: var(--color-success-bg);
}

/* Actions Tooltip */
.actions-tooltip {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-top: 8px;
  padding: 10px 14px;
  background: var(--color-text-primary);
  color: var(--color-text-inverse);
  border-radius: 4px;
  box-shadow: 0 4px 12px color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s ease;
  z-index: 100;
  min-width: 180px;
  pointer-events: none;
}

.actions-tooltip::before {
  content: '';
  position: absolute;
  top: -6px;
  left: 50%;
  transform: translateX(-50%);
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-bottom: 6px solid var(--color-text-primary);
}

.platform-status:hover .actions-tooltip {
  opacity: 1;
  visibility: visible;
}

.tooltip-title {
  font-size: 10px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: none;
  letter-spacing: normal;
  margin-bottom: 8px;
}

.tooltip-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tooltip-action {
  font-size: 10px;
  font-weight: 600;
  padding: 3px 8px;
  background: color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  border-radius: 2px;
  color: var(--color-text-inverse);
  letter-spacing: normal;
}

.platform-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 2px;
}

.platform-name {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-text-primary);
  text-transform: none;
  letter-spacing: normal;
}

.platform-status.twitter .platform-icon { color: var(--color-text-primary); }
.platform-status.reddit .platform-icon { color: var(--color-text-primary); }

.platform-stats {
  display: flex;
  gap: 10px;
}

.stat {
  display: flex;
  align-items: baseline;
  gap: 3px;
}

.stat-label {
  font-size: 8px;
  color: var(--color-text-muted);
  font-weight: 600;
  text-transform: none;
  letter-spacing: normal;
}

.stat-value {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.stat-total, .stat-unit {
  font-size: 9px;
  color: var(--color-text-muted);
  font-weight: 400;
}

.status-badge {
  margin-left: auto;
  color: var(--color-success-text);
  display: flex;
  align-items: center;
}

/* Action Button */
.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  font-size: 13px;
  font-weight: 600;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-transform: none;
  letter-spacing: normal;
}

.action-btn.primary {
  background: var(--color-text-primary);
  color: var(--color-text-inverse);
}

.action-btn.primary:hover:not(:disabled) {
  background: var(--color-text-primary);
}

.action-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

/* --- Main Content Area --- */
.main-content-area {
  flex: 1;
  overflow-y: auto;
  position: relative;
  background: var(--color-bg-surface-raised);
}

/* Timeline Header */
.timeline-header {
  position: sticky;
  top: 0;
  background: color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  backdrop-filter: blur(8px);
  padding: 12px 24px;
  border-bottom: 1px solid var(--color-border-subtle);
  z-index: 5;
  display: flex;
  justify-content: center;
}

.timeline-stats {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 11px;
  color: var(--color-text-secondary);
  background: var(--color-bg-surface-subtle);
  padding: 4px 12px;
  border-radius: 20px;
}

.total-count {
  font-weight: 600;
  color: var(--color-text-primary);
}

.platform-breakdown {
  display: flex;
  align-items: center;
  gap: 8px;
}

.breakdown-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.breakdown-divider { color: var(--color-border-default); }
.breakdown-item.twitter { color: var(--color-text-primary); }
.breakdown-item.reddit { color: var(--color-text-primary); }

/* --- Timeline Feed --- */
.timeline-feed {
  padding: 24px 0;
  position: relative;
  min-height: 100%;
  max-width: 900px;
  margin: 0 auto;
}

.timeline-axis {
  position: absolute;
  left: 50%;
  top: 0;
  bottom: 0;
  width: 1px;
  background: var(--color-border-subtle); /* Cleaner line */
  transform: translateX(-50%);
}

.timeline-item {
  display: flex;
  justify-content: center;
  margin-bottom: 32px;
  position: relative;
  width: 100%;
}

.timeline-marker {
  position: absolute;
  left: 50%;
  top: 24px;
  width: 10px;
  height: 10px;
  background: var(--color-bg-surface-raised);
  border: 1px solid var(--color-border-strong);
  border-radius: 50%;
  transform: translateX(-50%);
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
}

.marker-dot {
  width: 4px;
  height: 4px;
  background: var(--color-border-strong);
  border-radius: 50%;
}

.timeline-item.twitter .marker-dot { background: var(--color-text-primary); }
.timeline-item.reddit .marker-dot { background: var(--color-text-primary); }
.timeline-item.twitter .timeline-marker { border-color: var(--color-text-primary); }
.timeline-item.reddit .timeline-marker { border-color: var(--color-text-primary); }

/* Card Layout */
.timeline-card {
  width: calc(100% - 48px);
  background: var(--color-bg-surface-raised);
  border-radius: 2px;
  padding: 16px 20px;
  border: 1px solid var(--color-border-subtle);
  box-shadow: 0 2px 10px color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  position: relative;
  transition: all 0.2s;
}

.timeline-card:hover {
  box-shadow: 0 4px 12px color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  border-color: var(--color-border-default);
}

/* Left side (Twitter) */
.timeline-item.twitter {
  justify-content: flex-start;
  padding-right: 50%;
}
.timeline-item.twitter .timeline-card {
  margin-left: auto;
  margin-right: 32px; /* Gap from axis */
}

/* Right side (Reddit) */
.timeline-item.reddit {
  justify-content: flex-end;
  padding-left: 50%;
}
.timeline-item.reddit .timeline-card {
  margin-right: auto;
  margin-left: 32px; /* Gap from axis */
}

/* Card Content Styles */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-bg-surface-subtle);
}

.agent-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar-placeholder {
  width: 24px;
  height: 24px;
  background: var(--color-text-primary);
  color: var(--color-text-inverse);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  text-transform: none;
}

.agent-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.platform-indicator {
  color: var(--color-text-muted);
  display: flex;
  align-items: center;
}

.action-badge {
  font-size: 9px;
  padding: 2px 6px;
  border-radius: 2px;
  font-weight: 600;
  text-transform: none;
  letter-spacing: normal;
  border: 1px solid transparent;
}

/* Monochromatic Badges */
.badge-post { background: var(--color-border-subtle); color: var(--color-text-primary); border-color: var(--color-border-default); }
.badge-comment { background: var(--color-border-subtle); color: var(--color-text-secondary); border-color: var(--color-border-default); }
.badge-action { background: var(--color-bg-surface-raised); color: var(--color-text-secondary); border: 1px solid var(--color-border-default); }
.badge-meta { background: var(--color-bg-surface-subtle); color: var(--color-text-muted); border: 1px dashed var(--color-border-default); }
.badge-idle { opacity: 0.5; }

.content-text {
  font-size: 13px;
  line-height: 1.6;
  color: var(--color-text-primary);
  margin-bottom: 10px;
}

.content-text.main-text {
  font-size: 14px;
  color: var(--color-text-primary);
}

/* Info Blocks (Quote, Repost, etc) */
.quoted-block, .repost-content {
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-subtle);
  padding: 10px 12px;
  border-radius: 2px;
  margin-top: 8px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.quote-header, .repost-info, .like-info, .search-info, .follow-info, .vote-info, .idle-info, .comment-context {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
  font-size: 11px;
  color: var(--color-text-secondary);
}

.icon-small {
  color: var(--color-text-muted);
}
.icon-small.filled {
  color: var(--color-text-muted); /* Keep icons neutral unless highlighted */
}

.search-query {
  font-family: var(--font-body);
  background: var(--color-border-subtle);
  padding: 0 4px;
  border-radius: 2px;
}

.card-footer {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
  font-size: 10px;
  color: var(--color-border-strong);
  font-family: var(--font-body);
}

/* Waiting State */
.waiting-state {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  color: var(--color-border-strong);
  font-size: 12px;
  text-transform: none;
  letter-spacing: normal;
}

.pulse-ring {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid var(--color-border-subtle);
  animation: ripple 2s infinite;
}

@keyframes ripple {
  0% { transform: scale(0.8); opacity: 1; border-color: var(--color-border-strong); }
  100% { transform: scale(2.5); opacity: 0; border-color: var(--color-border-subtle); }
}

/* Animation */
.timeline-item-enter-active,
.timeline-item-leave-active {
  transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
}

.timeline-item-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.timeline-item-leave-to {
  opacity: 0;
}

/* Logs */
.system-logs {
  background: var(--color-text-primary);
  color: var(--color-border-default);
  padding: 16px;
  font-family: var(--font-body);
  border-top: 1px solid var(--color-text-primary);
  flex-shrink: 0;
}

.log-header {
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid var(--color-text-primary);
  padding-bottom: 8px;
  margin-bottom: 8px;
  font-size: 10px;
  color: var(--color-text-secondary);
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
  display: flex;
  gap: 12px;
  line-height: 1.5;
}

.log-time { color: var(--color-text-secondary); min-width: 75px; }
.log-msg { color: var(--color-border-strong); word-break: break-all; }
.mono { font-family: var(--font-body); }

/* Loading spinner for button */
.loading-spinner-small {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  border-top-color: var(--color-text-inverse);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-right: 6px;
}
/* Mobile-first polish */
button, [role="button"], input, select, textarea { min-height: var(--touch-target-min); }
h1, h2, h3, h4, h5, h6, .platform-name { font-family: var(--font-heading); }
.timeline-card, .content-text, .agent-name { overflow-wrap: anywhere; word-break: break-word; }
@media (max-width: 768px) {
  .action-controls { display: none; }
  .simulation-panel { min-width: 0; }
  .control-bar { height: auto; padding: 12px 16px; align-items: stretch; flex-direction: column; gap: 12px; }
  .status-group { display: grid; grid-template-columns: 1fr; gap: 8px; }
  .platform-status { width: 100%; min-width: 0; }
  .action-controls, .action-btn { width: 100%; }
  .main-content-area { padding: 0 16px calc(80px + env(safe-area-inset-bottom)); }
  .timeline-header { padding-inline: 0; }
  .timeline-feed { padding: 16px 0; }
  .timeline-axis { left: 10px; transform: none; }
  .timeline-item, .timeline-item.twitter, .timeline-item.reddit { justify-content: flex-start; padding: 0 0 0 28px; margin-bottom: 16px; }
  .timeline-marker { left: 10px; }
  .timeline-card, .timeline-item.twitter .timeline-card, .timeline-item.reddit .timeline-card { width: 100%; margin: 0; padding: 14px; }
  .card-header { gap: 8px; }
  .actions-tooltip { display: none; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; transition-duration: .01ms !important; }
}
</style>
