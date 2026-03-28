<template>
  <div class="main-view">
    <!-- Header -->
    <header class="app-header">
      <div class="header-left">
        <div class="brand" @click="router.push('/')">MIROFISH</div>
      </div>
      
      <div class="header-center">
        <div class="view-switcher">
          <button 
            v-for="mode in ['graph', 'split', 'workbench']" 
            :key="mode"
            class="switch-btn"
            :class="{ active: viewMode === mode }"
            @click="viewMode = mode"
          >
            {{ { graph: 'Graph', split: 'Zweispaltig', workbench: 'Arbeitsbereich' }[mode] }}
          </button>
        </div>
      </div>

      <div class="header-right">
        <div class="workflow-step">
          <span class="step-num">Schritt 2/5</span>
          <span class="step-name">Umgebungsaufbau</span>
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
          :currentPhase="2"
          @refresh="refreshGraph"
          @toggle-maximize="toggleMaximize('graph')"
        />
      </div>

      <!-- Right Panel: Step2 Umgebungsaufbau -->
      <div class="panel-wrapper right" :style="rightPanelStyle">
        <Step2EnvSetup
          :simulationId="currentSimulationId"
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import GraphPanel from '../components/GraphPanel.vue'
import Step2EnvSetup from '../components/Step2EnvSetup.vue'
import { getProject, getGraphData } from '../api/graph'
import { getSimulation, stopSimulation, getEnvStatus, closeSimulationEnv } from '../api/simulation'

const route = useRoute()
const router = useRouter()

// Props
const props = defineProps({
  simulationId: String
})

// Layout State
const viewMode = ref('split')

// Data State
const currentSimulationId = ref(route.params.simulationId)
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
  if (currentStatus.value === 'error') return 'Fehler'
  if (currentStatus.value === 'completed') return 'Bereit'
  return 'Vorbereitung'
})

// --- Helpers ---
const addLog = (msg) => {
  const time = new Date().toLocaleTimeString('de-DE', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + '.' + new Date().getMilliseconds().toString().padStart(3, '0')
  systemLogs.value.push({ time, msg })
  if (systemLogs.value.length > 100) {
    systemLogs.value.shift()
  }
}

const updateStatus = (status) => {
  currentStatus.value = status
}

// --- Layout Methods ---
const toggleMaximize = (target) => {
  if (viewMode.value === target) {
    viewMode.value = 'split'
  } else {
    viewMode.value = target
  }
}

const handleGoBack = () => {
  // Zurück zur Prozessseite
  if (projectData.value?.project_id) {
    router.push({ name: 'Process', params: { projectId: projectData.value.project_id } })
  } else {
    router.push('/')
  }
}

const handleNextStep = (params = {}) => {
  addLog('Schritt 3 betreten: Simulation starten')

  // Simulationsrunden-Konfiguration protokollieren
  if (params.maxRounds) {
    addLog(`Benutzerdefinierte Simulationsrunden: ${params.maxRounds} Runden`)
  } else {
    addLog('Automatisch konfigurierte Simulationsrunden werden verwendet')
  }
  
  // Routenparameter erstellen
  const routeParams = {
    name: 'SimulationRun',
    params: { simulationId: currentSimulationId.value }
  }
  
  // Bei benutzerdefinierten Runden über Query-Parameter übergeben
  if (params.maxRounds) {
    routeParams.query = { maxRounds: params.maxRounds }
  }
  
  // Zu Schritt 3 navigieren
  router.push(routeParams)
}

// --- Data Logic ---

/**
 * Laufende Simulation prüfen und beenden
 * Wenn der Benutzer von Schritt 3 zu Schritt 2 zurückkehrt, wird davon ausgegangen, dass die Simulation beendet werden soll
 */
const checkAndStopRunningSimulation = async () => {
  if (!currentSimulationId.value) return
  
  try {
    // Zuerst prüfen, ob die Simulationsumgebung aktiv ist
    const envStatusRes = await getEnvStatus({ simulation_id: currentSimulationId.value })
    
    if (envStatusRes.success && envStatusRes.data?.env_alive) {
      addLog('Laufende Simulationsumgebung erkannt, wird geschlossen...')

      // Versuchen, die Simulationsumgebung ordnungsgemäß zu schließen
      try {
        const closeRes = await closeSimulationEnv({ 
          simulation_id: currentSimulationId.value,
          timeout: 10  // 10 Sekunden Timeout
        })
        
        if (closeRes.success) {
          addLog('Simulationsumgebung geschlossen')
        } else {
          addLog(`Schließen der Simulationsumgebung fehlgeschlagen: ${closeRes.error || 'Unbekannter Fehler'}`)
          // Bei fehlgeschlagenem ordnungsgemäßen Schließen erzwungenen Stopp versuchen
          await forceStopSimulation()
        }
      } catch (closeErr) {
        addLog(`Ausnahme beim Schließen der Simulationsumgebung: ${closeErr.message}`)
        // Bei Ausnahme beim ordnungsgemäßen Schließen erzwungenen Stopp versuchen
        await forceStopSimulation()
      }
    } else {
      // Umgebung nicht aktiv, aber Prozess könnte noch laufen, Simulationsstatus prüfen
      const simRes = await getSimulation(currentSimulationId.value)
      if (simRes.success && simRes.data?.status === 'running') {
        addLog('Simulationsstatus als laufend erkannt, wird gestoppt...')
        await forceStopSimulation()
      }
    }
  } catch (err) {
    // Fehlgeschlagene Umgebungsstatusprüfung beeinflusst den weiteren Ablauf nicht
    console.warn('Prüfung des Simulationsstatus fehlgeschlagen:', err)
  }
}

/**
 * Simulation erzwungen stoppen
 */
const forceStopSimulation = async () => {
  try {
    const stopRes = await stopSimulation({ simulation_id: currentSimulationId.value })
    if (stopRes.success) {
      addLog('Simulation erzwungen gestoppt')
    } else {
      addLog(`Erzwungener Stopp der Simulation fehlgeschlagen: ${stopRes.error || 'Unbekannter Fehler'}`)
    }
  } catch (err) {
    addLog(`Ausnahme beim erzwungenen Stopp der Simulation: ${err.message}`)
  }
}

const loadSimulationData = async () => {
  try {
    addLog(`Simulationsdaten werden geladen: ${currentSimulationId.value}`)

    // Simulationsinformationen abrufen
    const simRes = await getSimulation(currentSimulationId.value)
    if (simRes.success && simRes.data) {
      const simData = simRes.data
      
      // Projektinformationen abrufen
      if (simData.project_id) {
        const projRes = await getProject(simData.project_id)
        if (projRes.success && projRes.data) {
          projectData.value = projRes.data
          addLog(`Projekt erfolgreich geladen: ${projRes.data.project_id}`)

          // Graphdaten abrufen
          if (projRes.data.graph_id) {
            await loadGraph(projRes.data.graph_id)
          }
        }
      }
    } else {
      addLog(`Laden der Simulationsdaten fehlgeschlagen: ${simRes.error || 'Unbekannter Fehler'}`)
    }
  } catch (err) {
    addLog(`Ladeausnahme: ${err.message}`)
  }
}

const loadGraph = async (graphId) => {
  graphLoading.value = true
  try {
    const res = await getGraphData(graphId)
    if (res.success) {
      graphData.value = res.data
      addLog('Graphdaten erfolgreich geladen')
    }
  } catch (err) {
    addLog(`Graph laden fehlgeschlagen: ${err.message}`)
  } finally {
    graphLoading.value = false
  }
}

const refreshGraph = () => {
  if (projectData.value?.graph_id) {
    loadGraph(projectData.value.graph_id)
  }
}

onMounted(async () => {
  addLog('SimulationView initialisiert')

  // Laufende Simulation prüfen und beenden (wenn Benutzer von Schritt 3 zurückkehrt)
  await checkAndStopRunningSimulation()
  
  // Simulationsdaten laden
  loadSimulationData()
})
</script>

<style scoped>
.main-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #FFF;
  overflow: hidden;
  font-family: 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
}

/* Header */
.app-header {
  height: 60px;
  border-bottom: 1px solid #EAEAEA;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #FFF;
  z-index: 100;
  position: relative;
}

.brand {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  font-size: 18px;
  letter-spacing: 1px;
  cursor: pointer;
}

.header-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.view-switcher {
  display: flex;
  background: #F5F5F5;
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
  color: #666;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.switch-btn.active {
  background: #FFF;
  color: #000;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
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
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  color: #999;
}

.step-name {
  font-weight: 700;
  color: #000;
}

.step-divider {
  width: 1px;
  height: 14px;
  background-color: #E0E0E0;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #CCC;
}

.status-indicator.processing .dot { background: #FF5722; animation: pulse 1s infinite; }
.status-indicator.completed .dot { background: #4CAF50; }
.status-indicator.error .dot { background: #F44336; }

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
  border-right: 1px solid #EAEAEA;
}
</style>

