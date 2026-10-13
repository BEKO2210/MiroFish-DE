<template>
  <div class="main-view">
    <!-- Header -->
    <header class="app-header">
      <div class="header-left">
        <button type="button" class="brand" @click="router.push('/')" :aria-label="$t('nav.homeAria')"><img src="/logo-mark.svg" alt="" width="28" height="28" /><span>MiroFish</span></button>
      </div>
      <StepHeaderCompact class="mobile-step-header" :current-step="3" :max-unlocked-step="3" :step-names="stepNames" @select-step="selectStep" />
      
      <div class="header-center">
        <div class="view-switcher">
          <button 
            v-for="mode in ['graph', 'split', 'workbench']" :data-mode="mode" 
            :key="mode"
            class="switch-btn"
            :class="{ active: viewMode === mode }"
            @click="viewMode = mode"
          >
            {{ { graph: $t('simulationRunView.graph'), split: $t('common.splitView'), workbench: $t('common.workspace') }[mode] }}
          </button>
        </div>
      </div>

      <div class="header-right">
        <LanguageSwitcher />
        <div class="workflow-step">
          <span class="step-num">{{ $t('simulationRunView.schritt35') }}</span>
          <span class="step-name">{{ $t('simulationRunView.simulationStarten') }}</span>
        </div>
        <div class="step-divider"></div>
        <span class="status-indicator" :class="statusClass">
          <span class="dot"></span>
          {{ statusText }}
        </span>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="content-area">
      <!-- Left Panel: Graph -->
      <div class="panel-wrapper left" :style="leftPanelStyle">
        <GraphPanel 
          :graphData="graphData"
          :loading="graphLoading"
          :currentPhase="3"
          :isSimulating="isSimulating"
          @refresh="refreshGraph"
          @toggle-maximize="toggleMaximize('graph')"
        />
      </div>

      <!-- Right Panel: Step3 Simulation starten -->
      <div class="panel-wrapper right" :style="rightPanelStyle">
        <Step3Simulation
          :simulationId="currentSimulationId"
          :maxRounds="maxRounds"
          :minutesPerRound="minutesPerRound"
          :projectData="projectData"
          :graphData="graphData"
          :systemLogs="systemLogs"
          @go-back="handleGoBack"
          @next-step="handleNextStep"
          @add-log="addLog"
          @update-status="updateStatus"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import GraphPanel from '../components/GraphPanel.vue'
import Step3Simulation from '../components/Step3Simulation.vue'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'
import StepHeaderCompact from '../components/StepHeaderCompact.vue'
import { getProject, getGraphData } from '../api/graph'
import { getSimulation, getSimulationConfig, stopSimulation, closeSimulationEnv, getEnvStatus } from '../api/simulation'

const { t } = useI18n()

const route = useRoute()
const router = useRouter()

// Props
const props = defineProps({
  simulationId: String
})

// Layout State
const viewMode = ref(window.innerWidth <= 768 ? 'workbench' : 'split')
const stepNames = computed(() => [t('main.graphErstellen'), t('main.umgebungAufbauen'), t('main.simulationStarten'), t('main.berichtGenerieren'), t('main.tiefeInteraktion')])

// Data State
const currentSimulationId = ref(route.params.simulationId)
// maxRounds direkt bei Initialisierung aus Query-Parametern abrufen, damit Unterkomponenten sofort den Wert erhalten
const maxRounds = ref(route.query.maxRounds ? parseInt(route.query.maxRounds) : null)
const minutesPerRound = ref(30) // Standard: 30 Minuten pro Runde
const projectData = ref(null)
const graphData = ref(null)
const graphLoading = ref(false)
const systemLogs = ref([])
const currentStatus = ref('processing') // processing | completed | error

// --- Computed Layout Styles ---
const leftPanelStyle = computed(() => {
  if (viewMode.value === 'graph') return { width: '100%', opacity: 1, transform: 'translateX(0)' }
  if (viewMode.value === 'workbench') return { width: '0%', opacity: 0, transform: 'translateX(-20px)' }
  return { width: '50%', opacity: 1, transform: 'translateX(0)' }
})

const rightPanelStyle = computed(() => {
  if (viewMode.value === 'workbench') return { width: '100%', opacity: 1, transform: 'translateX(0)' }
  if (viewMode.value === 'graph') return { width: '0%', opacity: 0, transform: 'translateX(20px)' }
  return { width: '50%', opacity: 1, transform: 'translateX(0)' }
})

// --- Status Computed ---
const statusClass = computed(() => {
  return currentStatus.value
})

const statusText = computed(() => {
  if (currentStatus.value === 'error') return t('common.error')
  if (currentStatus.value === 'completed') return t('common.completed')
  return t('common.running')
})

const isSimulating = computed(() => currentStatus.value === 'processing')

// --- Helpers ---
const addLog = (msg) => {
  const time = new Date().toLocaleTimeString('de-DE', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + '.' + new Date().getMilliseconds().toString().padStart(3, '0')
  systemLogs.value.push({ time, msg })
  if (systemLogs.value.length > 200) {
    systemLogs.value.shift()
  }
}

const updateStatus = (status) => {
  currentStatus.value = status
}

// --- Layout Methods ---
const toggleMaximize = (target) => {
  if (viewMode.value === target) {
    viewMode.value = window.innerWidth <= 768 ? 'workbench' : 'split'
  } else {
    viewMode.value = target
  }
}

const handleGoBack = async () => {
  // Vor der Rückkehr zu Schritt 2 die laufende Simulation schließen
  addLog(t('simulationRunView.vorbereitungZurRuckkehrZuSchritt2Simulation'))

  // Abfrage stoppen
  stopGraphRefresh()
  
  try {
    // Zuerst versuchen, die Simulationsumgebung ordnungsgemäß zu schließen
    const envStatusRes = await getEnvStatus({ simulation_id: currentSimulationId.value })
    
    if (envStatusRes.success && envStatusRes.data?.env_alive) {
      addLog(t('simulationRunView.simulationsumgebungWirdGeschlossen'))
      try {
        await closeSimulationEnv({ 
          simulation_id: currentSimulationId.value,
          timeout: 10
        })
        addLog(t('simulationRunView.environmentClosed'))
      } catch (closeErr) {
        addLog(t('simulationRunView.schliessenDerSimulationsumgebungFehlgeschlagenErzwungenerStoppWird'))
        try {
          await stopSimulation({ simulation_id: currentSimulationId.value })
          addLog(t('simulationRunView.simulationErzwungenGestoppt'))
        } catch (stopErr) {
          addLog(t('simulationRunView.erzwungenerStoppFehlgeschlagen', { p0: stopErr.message }))
        }
      }
    } else {
      // Umgebung nicht aktiv, prüfen ob Prozess gestoppt werden muss
      if (isSimulating.value) {
        addLog(t('simulationRunView.simulationsprozessWirdGestoppt'))
        try {
          await stopSimulation({ simulation_id: currentSimulationId.value })
          addLog(t('simulationRunView.simulationGestoppt'))
        } catch (err) {
          addLog(t('simulationRunView.simulationStoppenFehlgeschlagen', { p0: err.message }))
        }
      }
    }
  } catch (err) {
    addLog(t('simulationRunView.prufungDesSimulationsstatusFehlgeschlagen', { p0: err.message }))
  }
  
  // Zurück zu Schritt 2 (Umgebungsaufbau)
  router.push({ name: 'Simulation', params: { simulationId: currentSimulationId.value } })
}

const selectStep = (step) => {
  if (step === 2) handleGoBack()
  if (step === 1 && projectData.value?.project_id) router.push({ name: 'Process', params: { projectId: projectData.value.project_id } })
}

const handleNextStep = () => {
  // Die Step3Simulation-Komponente behandelt Berichterstellung und Routenwechsel direkt
  // Diese Methode dient nur als Fallback
  addLog(t('simulationRunView.schritt4BetretenBerichterstellung'))
}

// --- Data Logic ---
const loadSimulationData = async () => {
  try {
    addLog(t('simulationRunView.simulationsdatenWerdenGeladen', { p0: currentSimulationId.value }))

    // Simulationsinformationen abrufen
    const simRes = await getSimulation(currentSimulationId.value)
    if (simRes.success && simRes.data) {
      const simData = simRes.data
      
      // Simulationskonfiguration abrufen, um minutes_per_round zu erhalten
      try {
        const configRes = await getSimulationConfig(currentSimulationId.value)
        if (configRes.success && configRes.data?.time_config?.minutes_per_round) {
          minutesPerRound.value = configRes.data.time_config.minutes_per_round
          addLog(t('simulationRunView.zeitkonfigurationMinutenProRunde', { p0: minutesPerRound.value }))
        }
      } catch (configErr) {
        addLog(t('simulationRunView.zeitkonfigurationKonnteNichtAbgerufenWerdenStandardwertWird', { p0: minutesPerRound.value }))
      }
      
      // Projektinformationen abrufen
      if (simData.project_id) {
        const projRes = await getProject(simData.project_id)
        if (projRes.success && projRes.data) {
          projectData.value = projRes.data
          addLog(t('simulationRunView.projektErfolgreichGeladen', { p0: projRes.data.project_id }))

          // Graphdaten abrufen
          if (projRes.data.graph_id) {
            await loadGraph(projRes.data.graph_id)
          }
        }
      }
    } else {
      addLog(t('simulationRunView.ladenDerSimulationsdatenFehlgeschlagen', { p0: simRes.error || t('common.unknownError') }))
    }
  } catch (err) {
    addLog(t('simulationRunView.loadException', { error: err.message }))
  }
}

const loadGraph = async (graphId) => {
  // Während der Simulation kein Vollbild-Laden bei automatischer Aktualisierung anzeigen, um Flackern zu vermeiden
  // Bei manueller Aktualisierung oder initialem Laden wird Laden angezeigt
  if (!isSimulating.value) {
    graphLoading.value = true
  }
  
  try {
    const res = await getGraphData(graphId)
    if (res.success) {
      graphData.value = res.data
      if (!isSimulating.value) {
        addLog(t('simulationRunView.graphdatenErfolgreichGeladen'))
      }
    }
  } catch (err) {
    addLog(t('simulationRunView.graphLadenFehlgeschlagen', { p0: err.message }))
  } finally {
    graphLoading.value = false
  }
}

const refreshGraph = () => {
  if (projectData.value?.graph_id) {
    loadGraph(projectData.value.graph_id)
  }
}

// --- Auto Refresh Logic ---
let graphRefreshTimer = null

const startGraphRefresh = () => {
  if (graphRefreshTimer) return
  addLog(t('simulationRunView.echtzeitGraphAktualisierungAktiviert30s'))
  // Sofort einmal aktualisieren, dann alle 30 Sekunden
  graphRefreshTimer = setInterval(refreshGraph, 30000)
}

const stopGraphRefresh = () => {
  if (graphRefreshTimer) {
    clearInterval(graphRefreshTimer)
    graphRefreshTimer = null
    addLog(t('simulationRunView.echtzeitGraphAktualisierungGestoppt'))
  }
}

watch(isSimulating, (newValue) => {
  if (newValue) {
    startGraphRefresh()
  } else {
    stopGraphRefresh()
  }
}, { immediate: true })

onMounted(() => {
  addLog(t('simulationRunView.initialized'))

  // maxRounds-Konfiguration protokollieren (Wert wurde bei Initialisierung aus Query-Parametern abgerufen)
  if (maxRounds.value) {
    addLog(t('simulationRunView.customSimulationRounds', { count: maxRounds.value }))
}
  
  loadSimulationData()
})

onUnmounted(() => {
  stopGraphRefresh()
})
</script>

<style scoped>
.main-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-surface-raised);
  overflow: hidden;
  font-family: var(--font-body);
}

/* Header */
.app-header {
  height: 60px;
  border-bottom: 1px solid var(--color-border-subtle);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: var(--color-bg-surface-raised);
  z-index: 100;
  position: relative;
}

.header-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.brand {
  font-family: var(--font-body);
  font-weight: 800;
  font-size: 18px;
  letter-spacing: normal;
  cursor: pointer;
}

.view-switcher {
  display: flex;
  background: var(--color-bg-surface-subtle);
  padding: 4px;
  border-radius: 6px;
  gap: 4px;
}

.switch-btn {
  border: none;
  background: transparent;
  padding: 6px 16px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.switch-btn.active {
  background: var(--color-bg-surface-raised);
  color: var(--color-text-primary);
  box-shadow: 0 2px 4px color-mix(in srgb, var(--color-text-primary) 12%, transparent);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.workflow-step {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.step-num {
  font-family: var(--font-body);
  font-weight: 700;
  color: var(--color-text-muted);
}

.step-name {
  font-weight: 700;
  color: var(--color-text-primary);
}

.step-divider {
  width: 1px;
  height: 14px;
  background-color: var(--color-border-default);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-border-strong);
}

.status-indicator.processing .dot { background: var(--color-brand-primary); animation: pulse 1s infinite; }
.status-indicator.completed .dot { background: var(--color-success-text); }
.status-indicator.error .dot { background: var(--color-error-text); }

@keyframes pulse { 50% { opacity: 0.5; } }

/* Content */
.content-area {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
}

.panel-wrapper {
  height: 100%;
  overflow: hidden;
  transition: width 0.4s cubic-bezier(0.25, 0.8, 0.25, 1), opacity 0.3s ease, transform 0.3s ease;
  will-change: width, opacity, transform;
}

.panel-wrapper.left {
  border-right: 1px solid var(--color-border-subtle);
}
@media (max-width: 768px) {
  /* Am Handy nie zwei Spalten: die sichtbare Tafel bekommt die volle Breite, die ausgeblendete verschwindet ganz.
     !important, weil die Breiten als Inline-Stile aus leftPanelStyle/rightPanelStyle kommen. */
  .content-area { flex-direction: column; }
  .panel-wrapper { width: 100% !important; transform: none !important; }
  .panel-wrapper[style*="width: 0%"] { display: none !important; }
  .app-header { flex-wrap: wrap; padding: 8px 12px; gap: 6px; height: auto; min-height: auto; flex-shrink: 0; overflow: visible; align-items: flex-start; }
  .header-center { order: 3; width: 100%; justify-content: flex-start; overflow-x: auto; }
  .header-right { gap: 6px; }
  .step-divider { display: none; }
  .step-name { white-space: nowrap; }
  [data-mode="split"] { display: none !important; } /* zwei Spalten gibt es am Handy nicht */
}
.mobile-step-header { display: none; }
/* Ruhige, durchscheinende Kopfzeile wie in AppHeader. */
.app-header {
  min-height: 60px;
  height: auto;
  background: color-mix(in srgb, var(--color-bg-canvas) 88%, transparent);
  backdrop-filter: saturate(180%) blur(14px);
  -webkit-backdrop-filter: saturate(180%) blur(14px);
  position: sticky;
  top: 0;
}

.brand {
  appearance: none;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-height: 44px;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--color-text-primary);
  font-family: var(--font-heading);
  font-size: 18px;
  font-weight: 700;
}

.view-switcher { border-radius: var(--radius-md); border: 1px solid var(--color-border-subtle); }
.switch-btn { min-height: 36px; font-family: var(--font-body); border-radius: var(--radius-sm); }
.switch-btn:focus-visible, .brand:focus-visible { outline: 2px solid var(--color-focus-ring); outline-offset: 2px; }

@media (max-width: 768px) {
  .mobile-step-header { display: flex; order: 2; width: 100%; }
  .header-right { display: none; }
  .header-center { order: 3; }
  /* Seite scrollt selbst; kein fester Innen-Scroll über dem Fußmenü */
  .main-view { height: auto; min-height: 0; min-width: 0; overflow: visible; }
  .app-header { padding: 8px 12px; }
  .header-left, .header-right { min-width: 0; }
  .header-center { position: static; transform: none; overflow: visible; }
  .view-switcher { width: 100%; }
  .switch-btn { flex: 1; min-height: 44px; padding-inline: 8px; }
  .workflow-step, .status-indicator { font-size: var(--font-size-xs); }
  .content-area { flex: none; height: auto; overflow: visible; min-width: 0; }
  .panel-wrapper {
    min-width: 0;
    height: auto;
    overflow: visible;
    will-change: auto;
    padding-bottom: 0;
  }
  .panel-wrapper.left { min-height: calc(100dvh - 200px); }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; }
}
</style>
