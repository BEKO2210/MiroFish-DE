<template>
  <div class="main-view">
    <!-- Header -->
    <header class="app-header">
      <div class="header-left">
        <button type="button" class="brand" @click="router.push('/')" :aria-label="$t('nav.homeAria')"><img src="/logo-mark.svg" alt="" width="28" height="28" /><span>MiroFish</span></button>
      </div>
      <StepHeaderCompact class="mobile-step-header" :current-step="5" :max-unlocked-step="5" :step-names="stepNames" @select-step="selectStep" />
      
      <div class="header-center">
        <div class="view-switcher">
          <button 
            v-for="mode in ['graph', 'split', 'workbench']" :data-mode="mode" 
            :key="mode"
            class="switch-btn"
            :class="{ active: viewMode === mode }"
            @click="viewMode = mode"
          >
            {{ { graph: $t('interactionView.graph'), split: $t('common.splitView'), workbench: $t('common.workspace') }[mode] }}
          </button>
        </div>
      </div>

      <div class="header-right">
        <LanguageSwitcher />
        <div class="workflow-step">
          <span class="step-num">{{ $t('interactionView.schritt55') }}</span>
          <span class="step-name">{{ $t('interactionView.tiefeInteraktion') }}</span>
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
          :currentPhase="5"
          :isSimulating="false"
          @refresh="refreshGraph"
          @toggle-maximize="toggleMaximize('graph')"
        />
      </div>

      <!-- Right Panel: Step5 Tiefe Interaktion -->
      <div class="panel-wrapper right" :style="rightPanelStyle">
        <Step5Interaction
          :reportId="currentReportId"
          :simulationId="simulationId"
          :systemLogs="systemLogs"
          @add-log="addLog"
          @update-status="updateStatus"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import GraphPanel from '../components/GraphPanel.vue'
import Step5Interaction from '../components/Step5Interaction.vue'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'
import StepHeaderCompact from '../components/StepHeaderCompact.vue'
import { getProject, getGraphData } from '../api/graph'
import { getSimulation } from '../api/simulation'
import { getReport } from '../api/report'

const { t } = useI18n()

const route = useRoute()
const router = useRouter()

// Props
const props = defineProps({
  reportId: String
})

// Layout-Status - Standardmäßig zur Arbeitsbereich-Ansicht wechseln
const viewMode = ref(window.innerWidth <= 768 ? 'workbench' : 'split')
const stepNames = computed(() => [t('main.graphErstellen'), t('main.umgebungAufbauen'), t('main.simulationStarten'), t('main.berichtGenerieren'), t('main.tiefeInteraktion')])

// Data State
const currentReportId = ref(route.params.reportId)
const simulationId = ref(null)
const projectData = ref(null)
const graphData = ref(null)
const graphLoading = ref(false)
const systemLogs = ref([])
const currentStatus = ref('ready') // ready | processing | completed | error

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
  if (currentStatus.value === 'processing') return t('common.processing')
  return t('common.ready')
})

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

const selectStep = (step) => {
  if (step === 4) router.push({ name: 'Report', params: { reportId: currentReportId.value } })
  if (step === 3 && simulationId.value) router.push({ name: 'SimulationRun', params: { simulationId: simulationId.value } })
  if (step === 2 && simulationId.value) router.push({ name: 'Simulation', params: { simulationId: simulationId.value } })
  if (step === 1 && projectData.value?.project_id) router.push({ name: 'Process', params: { projectId: projectData.value.project_id } })
}

// --- Data Logic ---
const loadReportData = async () => {
  try {
    addLog(t('interactionView.berichtsdatenWerdenGeladen', { p0: currentReportId.value }))

    // Berichtsinformationen abrufen, um simulation_id zu erhalten
    const reportRes = await getReport(currentReportId.value)
    if (reportRes.success && reportRes.data) {
      const reportData = reportRes.data
      simulationId.value = reportData.simulation_id
      
      if (simulationId.value) {
        // Simulationsinformationen abrufen
        const simRes = await getSimulation(simulationId.value)
        if (simRes.success && simRes.data) {
          const simData = simRes.data
          
          // Projektinformationen abrufen
          if (simData.project_id) {
            const projRes = await getProject(simData.project_id)
            if (projRes.success && projRes.data) {
              projectData.value = projRes.data
              addLog(t('interactionView.projektErfolgreichGeladen', { p0: projRes.data.project_id }))

              // Graphdaten abrufen
              if (projRes.data.graph_id) {
                await loadGraph(projRes.data.graph_id)
              }
            }
          }
        }
      }
    } else {
      addLog(t('interactionView.abrufenDerBerichtsinformationenFehlgeschlagen', { p0: reportRes.error || t('common.unknownError') }))
    }
  } catch (err) {
    addLog(t('interactionView.loadException', { error: err.message }))
  }
}

const loadGraph = async (graphId) => {
  graphLoading.value = true
  
  try {
    const res = await getGraphData(graphId)
    if (res.success) {
      graphData.value = res.data
      addLog(t('interactionView.graphdatenErfolgreichGeladen'))
    }
  } catch (err) {
    addLog(t('interactionView.graphLadenFehlgeschlagen', { p0: err.message }))
  } finally {
    graphLoading.value = false
  }
}

const refreshGraph = () => {
  if (projectData.value?.graph_id) {
    loadGraph(projectData.value.graph_id)
  }
}

// Watch route params
watch(() => route.params.reportId, (newId) => {
  if (newId && newId !== currentReportId.value) {
    currentReportId.value = newId
    loadReportData()
  }
}, { immediate: true })

onMounted(() => {
  addLog(t('interactionView.initialized'))
  loadReportData()
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

.status-indicator.ready .dot { background: var(--color-success-text); }
.status-indicator.processing .dot { background: var(--color-warning-text); animation: pulse 1s infinite; }
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
  .panel-wrapper.left {
    height: calc(100dvh - 168px - 64px - 58px - env(safe-area-inset-bottom, 0px));
    min-height: 420px;
    overflow: hidden;
  }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; }
}
</style>
