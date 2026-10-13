<template>
  <div class="main-view">
    <!-- Header -->
    <header class="app-header">
      <div class="header-left">
        <button type="button" class="brand" @click="router.push('/')" :aria-label="$t('nav.homeAria')"><img src="/logo-mark.svg" alt="" width="28" height="28" /><span>MiroFish</span></button>
      </div>
      <StepHeaderCompact class="mobile-step-header" :current-step="currentStep" :max-unlocked-step="currentStep" :step-names="stepNames" @select-step="selectStep" />
      
      <div class="header-center">
        <div class="view-switcher">
          <button 
            v-for="mode in ['graph', 'split', 'workbench']" :data-mode="mode" 
            :key="mode"
            class="switch-btn"
            :class="{ active: viewMode === mode }"
            @click="viewMode = mode"
          >
            {{ { graph: $t('main.graph'), split: $t('common.splitView'), workbench: $t('common.workspace') }[mode] }}
          </button>
        </div>
      </div>

      <div class="header-right">
        <LanguageSwitcher />
        <div class="workflow-step">
          <span class="step-num">{{ $t('main.schritt') }} {{ currentStep }}/5</span>
          <span class="step-name">{{ stepNames[currentStep - 1] }}</span>
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
          :currentPhase="currentPhase"
          @refresh="refreshGraph"
          @toggle-maximize="toggleMaximize('graph')"
        />
      </div>

      <!-- Right Panel: Step Components -->
      <div class="panel-wrapper right" :style="rightPanelStyle">
        <!-- Step 1: Graph erstellen -->
        <Step1GraphBuild 
          v-if="currentStep === 1"
          :currentPhase="currentPhase"
          :projectData="projectData"
          :ontologyProgress="ontologyProgress"
          :buildProgress="buildProgress"
          :graphData="graphData"
          :systemLogs="systemLogs"
          @next-step="handleNextStep"
        />
        <!-- Step 2: Umgebung aufbauen -->
        <Step2EnvSetup
          v-else-if="currentStep === 2"
          :projectData="projectData"
          :graphData="graphData"
          :systemLogs="systemLogs"
          @go-back="handleGoBack"
          @next-step="handleNextStep"
          @add-log="addLog"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import GraphPanel from '../components/GraphPanel.vue'
import Step1GraphBuild from '../components/Step1GraphBuild.vue'
import Step2EnvSetup from '../components/Step2EnvSetup.vue'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'
import StepHeaderCompact from '../components/StepHeaderCompact.vue'
import { generateOntology, getProject, buildGraph, getTaskStatus, getGraphData } from '../api/graph'
import { getPendingUpload, clearPendingUpload } from '../store/pendingUpload'

const { t } = useI18n()

const route = useRoute()
const router = useRouter()

// Layout State
const viewMode = ref(window.innerWidth <= 768 ? 'workbench' : 'split') // graph | split | workbench; am Handy nur eine Spalte

// Step State
const currentStep = ref(1) // 1: Graph erstellen, 2: Umgebung aufbauen, 3: Simulation starten, 4: Bericht generieren, 5: Tiefe Interaktion
const stepNames = computed(() => [
  t('main.graphErstellen'),
  t('main.umgebungAufbauen'),
  t('main.simulationStarten'),
  t('main.berichtGenerieren'),
  t('main.tiefeInteraktion')
])

// Data State
const currentProjectId = ref(route.params.projectId)
const loading = ref(false)
const graphLoading = ref(false)
const error = ref('')
const projectData = ref(null)
const graphData = ref(null)
const currentPhase = ref(-1) // -1: Upload, 0: Ontology, 1: Build, 2: Complete
const ontologyProgress = ref(null)
const buildProgress = ref(null)
const systemLogs = ref([])

// Polling timers
let pollTimer = null
let graphPollTimer = null

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
  if (error.value) return 'error'
  if (currentPhase.value >= 2) return 'completed'
  return 'processing'
})

const statusText = computed(() => {
  if (error.value) return t('common.error')
  if (currentPhase.value >= 2) return t('common.ready')
  if (currentPhase.value === 1) return t('main.graphWirdErstellt')
  if (currentPhase.value === 0) return t('main.ontologieWirdGeneriert')
  return t('common.initializing')
})

// --- Helpers ---
const addLog = (msg) => {
  const time = new Date().toLocaleTimeString('de-DE', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + '.' + new Date().getMilliseconds().toString().padStart(3, '0')
  systemLogs.value.push({ time, msg })
  // Letzte 100 Protokolleinträge behalten
  if (systemLogs.value.length > 100) {
    systemLogs.value.shift()
  }
}

// --- Layout Methods ---
const toggleMaximize = (target) => {
  if (viewMode.value === target) {
    viewMode.value = window.innerWidth <= 768 ? 'workbench' : 'split'
  } else {
    viewMode.value = target
  }
}

const handleNextStep = (params = {}) => {
  if (currentStep.value < 5) {
    currentStep.value++
    addLog(t('main.schrittBetreten', { p0: currentStep.value, p1: stepNames.value[currentStep.value - 1] }))
    
    // Wenn von Schritt 2 zu Schritt 3, Simulationsrunden konfigurieren
    if (currentStep.value === 3 && params.maxRounds) {
      addLog(t('main.customSimulationRounds', { count: params.maxRounds }))
    }
  }
}

const handleGoBack = () => {
  if (currentStep.value > 1) {
    currentStep.value--
    addLog(t('main.zuruckZuSchritt', { p0: currentStep.value, p1: stepNames.value[currentStep.value - 1] }))
  }
}

const selectStep = (step) => {
  if (step <= currentStep.value) currentStep.value = step
}

// --- Data Logic ---

const initProject = async () => {
  addLog(t('main.projectViewInitialized'))
  if (currentProjectId.value === 'new') {
    await handleNewProject()
  } else {
    await loadProject()
  }
}

const handleNewProject = async () => {
  const pending = getPendingUpload()
  if (!pending.isPending || pending.files.length === 0) {
    error.value = t('main.keineAusstehendenDateienGefunden')
    addLog(t('main.fehlerKeineAusstehendenDateienFurNeuesProjekt'))
    return
  }
  
  try {
    loading.value = true
    currentPhase.value = 0
    ontologyProgress.value = { message: t('main.dokumenteWerdenHochgeladenUndAnalysiert') }
    addLog(t('main.ontologieGenerierungStartenDateienWerdenHochgeladen'))
    
    const formData = new FormData()
    pending.files.forEach(f => formData.append('files', f))
    formData.append('simulation_requirement', pending.simulationRequirement)
    
    const res = await generateOntology(formData)
    if (res.success) {
      clearPendingUpload()
      currentProjectId.value = res.data.project_id
      projectData.value = res.data
      
      router.replace({ name: 'Process', params: { projectId: res.data.project_id } })
      ontologyProgress.value = null
      addLog(t('main.ontologieErfolgreichGeneriertFurProjekt', { p0: res.data.project_id }))
      await startBuildGraph()
    } else {
      error.value = res.error || t('main.ontologieGenerierungFehlgeschlagen')
      addLog(t('main.fehlerBeiDerOntologieGenerierung', { p0: error.value }))
    }
  } catch (err) {
    error.value = err.message
    addLog(t('main.newProjectException', { error: err.message }))
  } finally {
    loading.value = false
  }
}

const loadProject = async () => {
  try {
    loading.value = true
    addLog(t('main.projektWirdGeladen', { p0: currentProjectId.value }))
    const res = await getProject(currentProjectId.value)
    if (res.success) {
      projectData.value = res.data
      updatePhaseByStatus(res.data.status)
      addLog(t('main.projektGeladenStatus', { p0: res.data.status }))
      
      if (res.data.status === 'ontology_generated' && !res.data.graph_id) {
        await startBuildGraph()
      } else if (res.data.status === 'graph_building' && res.data.graph_build_task_id) {
        currentPhase.value = 1
        startPollingTask(res.data.graph_build_task_id)
        startGraphPolling()
      } else if (res.data.status === 'graph_completed' && res.data.graph_id) {
        currentPhase.value = 2
        await loadGraph(res.data.graph_id)
      }
    } else {
      error.value = res.error
      addLog(t('main.fehlerBeimLadenDesProjekts', { p0: res.error }))
    }
  } catch (err) {
    error.value = err.message
    addLog(t('main.loadProjectException', { error: err.message }))
  } finally {
    loading.value = false
  }
}

const updatePhaseByStatus = (status) => {
  switch (status) {
    case 'created':
    case 'ontology_generated': currentPhase.value = 0; break;
    case 'graph_building': currentPhase.value = 1; break;
    case 'graph_completed': currentPhase.value = 2; break;
    case 'failed': error.value = t('main.projektFehlgeschlagen'); break;
  }
}

const startBuildGraph = async () => {
  try {
    currentPhase.value = 1
    buildProgress.value = { progress: 0, message: t('main.aufbauWirdGestartet') }
    addLog(t('main.graphAufbauWirdInitiiert'))
    
    const res = await buildGraph({ project_id: currentProjectId.value })
    if (res.success) {
      addLog(t('main.graphAufbauAufgabeGestartetAufgabenId', { p0: res.data.task_id }))
      startGraphPolling()
      startPollingTask(res.data.task_id)
    } else {
      error.value = res.error
      addLog(t('main.fehlerBeimStartenDesAufbaus', { p0: res.error }))
    }
  } catch (err) {
    error.value = err.message
    addLog(t('main.startBuildException', { error: err.message }))
  }
}

const startGraphPolling = () => {
  addLog(t('main.abfrageDerGraphdatenGestartet'))
  fetchGraphData()
  graphPollTimer = setInterval(fetchGraphData, 10000)
}

const fetchGraphData = async () => {
  try {
    // Projektinformationen aktualisieren, um graph_id zu prüfen
    const projRes = await getProject(currentProjectId.value)
    if (projRes.success && projRes.data.graph_id) {
      const gRes = await getGraphData(projRes.data.graph_id)
      if (gRes.success) {
        graphData.value = gRes.data
        const nodeCount = gRes.data.node_count || gRes.data.nodes?.length || 0
        const edgeCount = gRes.data.edge_count || gRes.data.edges?.length || 0
        addLog(t('main.graphDataUpdated', { nodes: nodeCount, edges: edgeCount }))
      }
    }
  } catch (err) {
    console.warn(t('main.graphAbfragefehler'), err)
  }
}

const startPollingTask = (taskId) => {
  pollTaskStatus(taskId)
  pollTimer = setInterval(() => pollTaskStatus(taskId), 2000)
}

const pollTaskStatus = async (taskId) => {
  try {
    const res = await getTaskStatus(taskId)
    if (res.success) {
      const task = res.data
      
      // Fortschrittsnachricht protokollieren, wenn sie sich geändert hat
      if (task.message && task.message !== buildProgress.value?.message) {
        addLog(task.message)
      }
      
      buildProgress.value = { progress: task.progress || 0, message: task.message }
      
      if (task.status === 'completed') {
        addLog(t('main.graphAufbauAbgeschlossen'))
        stopPolling()
        stopGraphPolling() // Abfrage stoppen, finale Ladung durchführen
        currentPhase.value = 2
        
        // Finale Ladung
        const projRes = await getProject(currentProjectId.value)
        if (projRes.success && projRes.data.graph_id) {
            projectData.value = projRes.data
            await loadGraph(projRes.data.graph_id)
        }
      } else if (task.status === 'failed') {
        stopPolling()
        error.value = task.error
        addLog(t('main.graphAufbauFehlgeschlagen', { p0: task.error }))
      }
    }
  } catch (e) {
    console.error(e)
  }
}

const loadGraph = async (graphId) => {
  graphLoading.value = true
  addLog(t('main.vollstandigeGraphdatenWerdenGeladen', { p0: graphId }))
  try {
    const res = await getGraphData(graphId)
    if (res.success) {
      graphData.value = res.data
      addLog(t('main.graphdatenErfolgreichGeladen'))
    } else {
      addLog(t('main.graphdatenKonntenNichtGeladenWerden', { p0: res.error }))
    }
  } catch (e) {
    addLog(t('main.ausnahmeBeimLadenDesGraphen', { p0: e.message }))
  } finally {
    graphLoading.value = false
  }
}

const refreshGraph = () => {
  if (projectData.value?.graph_id) {
    addLog(t('main.manuelleGraphAktualisierungAusgelost'))
    loadGraph(projectData.value.graph_id)
  }
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const stopGraphPolling = () => {
  if (graphPollTimer) {
    clearInterval(graphPollTimer)
    graphPollTimer = null
    addLog(t('main.graphAbfrageGestoppt'))
  }
}

onMounted(() => {
  if (route.query.view === 'graph') {
    viewMode.value = 'graph'
  }
  initProject()
})

onUnmounted(() => {
  stopPolling()
  stopGraphPolling()
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

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--color-text-secondary);
  font-weight: 500;
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
