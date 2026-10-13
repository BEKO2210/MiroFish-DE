<template>
  <div class="process-page">
    <!-- Obere Navigationsleiste -->
    <nav class="navbar">
      <button type="button" class="nav-brand" @click="goHome" :aria-label="$t('nav.homeAria')">
        <img src="/logo-mark.svg" alt="" width="28" height="28" />
        <span>MiroFish</span>
      </button>
      
      <!-- Mittlerer Schrittindikator -->
      <div class="nav-center">
        <div class="step-badge">{{ $t('process.step01') }}</div>
        <div class="step-name">{{ $t('process.graphErstellen') }}</div>
      </div>

      <LanguageSwitcher />
      <div class="nav-status">
        <span class="status-dot" :class="statusClass"></span>
        <span class="status-text">{{ statusText }}</span>
      </div>
    </nav>

    <!-- Hauptinhaltsbereich -->
    <div class="main-content">
      <!-- Links: Echtzeit-Graphanzeige -->
      <div class="left-panel" :class="{ 'full-screen': isFullScreen }">
        <div class="panel-header">
          <div class="header-left">
            <span class="header-deco">◆</span>
            <span class="header-title">{{ $t('process.echtzeitWissensgraph') }}</span>
          </div>
          <div class="header-right">
            <template v-if="graphData">
              <span class="stat-item">{{ graphData.node_count || graphData.nodes?.length || 0 }} {{ $t('process.knoten') }}</span>
              <span class="stat-divider">|</span>
              <span class="stat-item">{{ graphData.edge_count || graphData.edges?.length || 0 }} {{ $t('process.beziehungen') }}</span>
              <span class="stat-divider">|</span>
            </template>
            <div class="action-buttons">
                <button class="action-btn" @click="refreshGraph" :disabled="graphLoading" :title="$t('process.refreshGraph')">
                  <span class="icon-refresh" :class="{ 'spinning': graphLoading }">↻</span>
                </button>
                <button class="action-btn" @click="toggleFullScreen" :title="isFullScreen ? $t('process.exitFullscreen') : $t('process.showFullscreen')">
                  <span class="icon-fullscreen">{{ isFullScreen ? '↙' : '↗' }}</span>
                </button>
            </div>
          </div>
        </div>
        
        <div class="graph-container" ref="graphContainer">
          <!-- Graph-Visualisierung -->
          <div v-if="graphData" class="graph-view">
            <svg ref="graphSvg" class="graph-svg"></svg>
            <!-- Aufbau-Hinweis -->
            <div v-if="currentPhase === 1" class="graph-building-hint">
              <span class="building-dot"></span>
              {{ $t('process.liveUpdate') }}
            </div>
            
            <!-- Knoten-/Kanten-Detailbereich -->
            <div v-if="selectedItem" class="detail-panel">
              <div class="detail-panel-header">
                <span class="detail-title">{{ selectedItem.type === 'node' ? $t('process.nodeDetails') : $t('process.relationship') }}</span>
                <span v-if="selectedItem.type === 'node'" class="detail-badge" :style="{ background: selectedItem.color }">
                  {{ selectedItem.entityType }}
                </span>
                <button class="detail-close" @click="closeDetailPanel">×</button>
              </div>
              
              <!-- Knotendetails -->
              <div v-if="selectedItem.type === 'node'" class="detail-content">
                <div class="detail-row">
                  <span class="detail-label">{{ $t('process.name') }}</span>
                  <span class="detail-value highlight">{{ selectedItem.data.name }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">{{ $t('process.uuid') }}</span>
                  <span class="detail-value uuid">{{ selectedItem.data.uuid }}</span>
                </div>
                <div class="detail-row" v-if="selectedItem.data.created_at">
                  <span class="detail-label">{{ $t('process.created') }}</span>
                  <span class="detail-value">{{ formatDate(selectedItem.data.created_at) }}</span>
                </div>

                <!-- Eigenschaften / Attribute -->
                <div class="detail-section" v-if="selectedItem.data.attributes && Object.keys(selectedItem.data.attributes).length > 0">
                  <span class="detail-label">{{ $t('process.properties') }}</span>
                  <div class="properties-list">
                    <div v-for="(value, key) in selectedItem.data.attributes" :key="key" class="property-item">
                      <span class="property-key">{{ key }}:</span>
                      <span class="property-value">{{ value }}</span>
                    </div>
                  </div>
                </div>
                
                <!-- Zusammenfassung -->
                <div class="detail-section" v-if="selectedItem.data.summary">
                  <span class="detail-label">{{ $t('process.summary') }}</span>
                  <p class="detail-summary">{{ selectedItem.data.summary }}</p>
                </div>
                
                <!-- Bezeichnungen -->
                <div class="detail-row" v-if="selectedItem.data.labels?.length">
                  <span class="detail-label">{{ $t('process.labels') }}</span>
                  <div class="detail-labels">
                    <span v-for="label in selectedItem.data.labels" :key="label" class="label-tag">{{ label }}</span>
                  </div>
                </div>
              </div>
              
              <!-- Kantendetails -->
              <div v-else class="detail-content">
                <!-- Beziehungsanzeige -->
                <div class="edge-relation">
                  <span class="edge-source">{{ selectedItem.data.source_name || selectedItem.data.source_node_name }}</span>
                  <span class="edge-arrow">→</span>
                  <span class="edge-type">{{ selectedItem.data.name || selectedItem.data.fact_type || $t('process.relationship') }}</span>
                  <span class="edge-arrow">→</span>
                  <span class="edge-target">{{ selectedItem.data.target_name || selectedItem.data.target_node_name }}</span>
                </div>
                
                <div class="detail-subtitle">{{ $t('process.relationship') }}</div>
                
                <div class="detail-row">
                  <span class="detail-label">{{ $t('process.uuid') }}</span>
                  <span class="detail-value uuid">{{ selectedItem.data.uuid }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">{{ $t('process.label') }}</span>
                  <span class="detail-value">{{ selectedItem.data.name || selectedItem.data.fact_type || $t('process.relationship') }}</span>
                </div>
                <div class="detail-row" v-if="selectedItem.data.fact_type">
                  <span class="detail-label">{{ $t('process.type') }}</span>
                  <span class="detail-value">{{ selectedItem.data.fact_type }}</span>
                </div>
                
                <!-- Fact -->
                <div class="detail-section" v-if="selectedItem.data.fact">
                  <span class="detail-label">{{ $t('process.fact') }}</span>
                  <p class="detail-summary">{{ selectedItem.data.fact }}</p>
                </div>
                
                <!-- Episodes -->
                <div class="detail-section" v-if="selectedItem.data.episodes?.length">
                  <span class="detail-label">{{ $t('process.episodes') }}</span>
                  <div class="episodes-list">
                    <span v-for="ep in selectedItem.data.episodes" :key="ep" class="episode-tag">{{ ep }}</span>
                  </div>
                </div>
                
                <div class="detail-row" v-if="selectedItem.data.created_at">
                  <span class="detail-label">{{ $t('process.created') }}</span>
                  <span class="detail-value">{{ formatDate(selectedItem.data.created_at) }}</span>
                </div>
                <div class="detail-row" v-if="selectedItem.data.valid_at">
                  <span class="detail-label">{{ $t('process.validFrom') }}</span>
                  <span class="detail-value">{{ formatDate(selectedItem.data.valid_at) }}</span>
                </div>
                <div class="detail-row" v-if="selectedItem.data.invalid_at">
                  <span class="detail-label">{{ $t('process.invalidFrom') }}</span>
                  <span class="detail-value">{{ formatDate(selectedItem.data.invalid_at) }}</span>
                </div>
                <div class="detail-row" v-if="selectedItem.data.expired_at">
                  <span class="detail-label">{{ $t('process.expiredAt') }}</span>
                  <span class="detail-value">{{ formatDate(selectedItem.data.expired_at) }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Ladezustand -->
          <div v-else-if="graphLoading" class="graph-loading">
            <div class="loading-animation">
              <div class="loading-ring"></div>
              <div class="loading-ring"></div>
              <div class="loading-ring"></div>
            </div>
            <p class="loading-text">{{ $t('process.loadingGraphData') }}</p>
          </div>
          
          <!-- Warten auf Aufbau -->
          <div v-else-if="currentPhase < 1" class="graph-waiting">
            <div class="waiting-icon">
              <svg viewBox="0 0 100 100" class="network-icon">
                <circle cx="50" cy="20" r="8" fill="none" stroke="var(--color-text-primary)" stroke-width="1.5"/>
                <circle cx="20" cy="60" r="8" fill="none" stroke="var(--color-text-primary)" stroke-width="1.5"/>
                <circle cx="80" cy="60" r="8" fill="none" stroke="var(--color-text-primary)" stroke-width="1.5"/>
                <circle cx="50" cy="80" r="8" fill="none" stroke="var(--color-text-primary)" stroke-width="1.5"/>
                <line x1="50" y1="28" x2="25" y2="54" stroke="var(--color-text-primary)" stroke-width="1"/>
                <line x1="50" y1="28" x2="75" y2="54" stroke="var(--color-text-primary)" stroke-width="1"/>
                <line x1="28" y1="60" x2="72" y2="60" stroke="var(--color-text-primary)" stroke-width="1" stroke-dasharray="4"/>
                <line x1="50" y1="72" x2="26" y2="66" stroke="var(--color-text-primary)" stroke-width="1"/>
                <line x1="50" y1="72" x2="74" y2="66" stroke="var(--color-text-primary)" stroke-width="1"/>
              </svg>
            </div>
            <p class="waiting-text">{{ $t('process.waitingForOntology') }}</p>
            <p class="waiting-hint">{{ $t('process.graphBuildsAfterGeneration') }}</p>
          </div>
          
          <!-- Wird aufgebaut, aber noch keine Daten -->
          <div v-else-if="currentPhase === 1 && !graphData" class="graph-waiting">
            <div class="loading-animation">
              <div class="loading-ring"></div>
              <div class="loading-ring"></div>
              <div class="loading-ring"></div>
            </div>
            <p class="waiting-text">{{ $t('process.graphWirdAufgebaut') }}</p>
            <p class="waiting-hint">{{ $t('process.dataWillAppear') }}</p>
          </div>
          
          <!-- Fehlerzustand -->
          <div v-else-if="error" class="graph-error">
            <span class="error-icon">⚠</span>
            <p>{{ error }}</p>
          </div>
        </div>
        
        <!-- Graph-Legende -->
        <div v-if="graphData" class="graph-legend">
          <div class="legend-item" v-for="type in entityTypes" :key="type.name">
            <span class="legend-dot" :style="{ background: type.color }"></span>
            <span class="legend-label">{{ type.name }}</span>
            <span class="legend-count">{{ type.count }}</span>
          </div>
        </div>
      </div>

      <!-- Rechts: Aufbauprozess-Details -->
      <div class="right-panel" :class="{ 'hidden': isFullScreen }">
        <div class="panel-header dark-header">
          <span class="header-icon">▣</span>
          <span class="header-title">{{ $t('process.buildProcess') }}</span>
        </div>

        <div class="process-content">
          <!-- Phase 1: Ontologie-Generierung -->
          <div class="process-phase" :class="{ 'active': currentPhase === 0, 'completed': currentPhase > 0 }">
            <div class="phase-header">
              <span class="phase-num">01</span>
              <div class="phase-info">
                <div class="phase-title">{{ $t('process.ontologyGeneration') }}</div>
                <div class="phase-api">/api/graph/ontology/generate</div>
              </div>
              <span class="phase-status" :class="getPhaseStatusClass(0)">
                {{ getPhaseStatusText(0) }}
              </span>
            </div>
            
            <div class="phase-detail">
              <div class="detail-section">
                <div class="detail-label">{{ $t('process.interfaceDescription') }}</div>
                <div class="detail-content">
                  {{ $t('process.ontologyDescription') }}
                </div>
              </div>
              
              <!-- Ontologie-Generierungsfortschritt -->
              <div class="detail-section" v-if="ontologyProgress && currentPhase === 0">
                <div class="detail-label">{{ $t('process.generationProgress') }}</div>
                <div class="ontology-progress">
                  <div class="progress-spinner"></div>
                  <span class="progress-text">{{ ontologyProgress.message }}</span>
                </div>
              </div>
              
              <!-- Generierte Ontologie-Informationen -->
              <div class="detail-section" v-if="projectData?.ontology">
                <div class="detail-label">{{ $t('process.generatedEntityTypes', { count: projectData.ontology.entity_types?.length || 0 }) }}</div>
                <div class="entity-tags">
                  <span 
                    v-for="entity in projectData.ontology.entity_types" 
                    :key="entity.name"
                    class="entity-tag"
                  >
                    {{ entity.name }}
                  </span>
                </div>
              </div>
              
              <div class="detail-section" v-if="projectData?.ontology">
                <div class="detail-label">{{ $t('process.generatedRelationshipTypes', { count: projectData.ontology.relation_types?.length || 0 }) }}</div>
                <div class="relation-list">
                  <div 
                    v-for="(rel, idx) in projectData.ontology.relation_types?.slice(0, 5) || []" 
                    :key="idx"
                    class="relation-item"
                  >
                    <span class="rel-source">{{ rel.source_type }}</span>
                    <span class="rel-arrow">→</span>
                    <span class="rel-name">{{ rel.name }}</span>
                    <span class="rel-arrow">→</span>
                    <span class="rel-target">{{ rel.target_type }}</span>
                  </div>
                  <div v-if="(projectData.ontology.relation_types?.length || 0) > 5" class="relation-more">
                    {{ $t('process.moreRelationships', { count: projectData.ontology.relation_types.length - 5 }) }}
                  </div>
                </div>
              </div>
              
              <!-- Wartezustand -->
              <div class="detail-section waiting-state" v-if="!projectData?.ontology && currentPhase === 0 && !ontologyProgress">
                <div class="waiting-hint">{{ $t('process.waitingForOntologyEllipsis') }}</div>
              </div>
            </div>
          </div>

          <!-- Phase 2: Graph-Aufbau -->
          <div class="process-phase" :class="{ 'active': currentPhase === 1, 'completed': currentPhase > 1 }">
            <div class="phase-header">
              <span class="phase-num">02</span>
              <div class="phase-info">
                <div class="phase-title">{{ $t('process.graphBuild') }}</div>
                <div class="phase-api">/api/graph/build</div>
              </div>
              <span class="phase-status" :class="getPhaseStatusClass(1)">
                {{ getPhaseStatusText(1) }}
              </span>
            </div>
            
            <div class="phase-detail">
              <div class="detail-section">
                <div class="detail-label">{{ $t('process.interfaceDescription') }}</div>
                <div class="detail-content">
                  {{ $t('process.graphBuildDescription') }}
                </div>
              </div>
              
              <!-- Warten auf Ontologie-Abschluss -->
              <div class="detail-section waiting-state" v-if="currentPhase < 1">
                <div class="waiting-hint">{{ $t('process.waitingForOntologyCompletion') }}</div>
              </div>
              
              <!-- Aufbaufortschritt -->
              <div class="detail-section" v-if="buildProgress && currentPhase >= 1">
                <div class="detail-label">{{ $t('process.buildProgress') }}</div>
                <div class="progress-bar">
                  <div class="progress-fill" :style="{ width: buildProgress.progress + '%' }"></div>
                </div>
                <div class="progress-info">
                  <span class="progress-message">{{ buildProgress.message }}</span>
                  <span class="progress-percent">{{ buildProgress.progress }}%</span>
                </div>
              </div>
              
              <div class="detail-section" v-if="graphData">
                <div class="detail-label">{{ $t('process.buildResult') }}</div>
                <div class="build-result">
                  <div class="result-item">
                    <span class="result-value">{{ graphData.node_count }}</span>
                    <span class="result-label">{{ $t('process.entityNodes') }}</span>
                  </div>
                  <div class="result-item">
                    <span class="result-value">{{ graphData.edge_count }}</span>
                    <span class="result-label">{{ $t('process.relationshipEdges') }}</span>
                  </div>
                  <div class="result-item">
                    <span class="result-value">{{ entityTypes.length }}</span>
                    <span class="result-label">{{ $t('process.entityTypes') }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Phase 3: Abgeschlossen -->
          <div class="process-phase" :class="{ 'active': currentPhase === 2, 'completed': currentPhase > 2 }">
            <div class="phase-header">
              <span class="phase-num">03</span>
              <div class="phase-info">
                <div class="phase-title">{{ $t('process.buildComplete') }}</div>
                <div class="phase-api">{{ $t('process.readyForNextStep') }}</div>
              </div>
              <span class="phase-status" :class="getPhaseStatusClass(2)">
                {{ getPhaseStatusText(2) }}
              </span>
            </div>
          </div>

          <!-- Nächster-Schritt-Button -->
          <div class="next-step-section" v-if="currentPhase >= 2">
            <button class="next-step-btn" @click="goToNextStep" :disabled="currentPhase < 2">
              {{ $t('process.toEnvironmentSetup') }}
              <span class="btn-arrow">→</span>
            </button>
          </div>
        </div>

        <!-- Projektinformationsbereich -->
        <div class="project-panel">
          <div class="project-header">
            <span class="project-icon">◇</span>
            <span class="project-title">{{ $t('process.projectInformation') }}</span>
          </div>
          <div class="project-details" v-if="projectData">
            <div class="project-item">
              <span class="item-label">{{ $t('process.projectName') }}</span>
              <span class="item-value">{{ projectData.name }}</span>
            </div>
            <div class="project-item">
              <span class="item-label">{{ $t('process.projectId') }}</span>
              <span class="item-value code">{{ projectData.project_id }}</span>
            </div>
            <div class="project-item" v-if="projectData.graph_id">
              <span class="item-label">{{ $t('process.graphId') }}</span>
              <span class="item-value code">{{ projectData.graph_id }}</span>
            </div>
            <div class="project-item">
              <span class="item-label">{{ $t('process.simulationRequirement') }}</span>
              <span class="item-value">{{ projectData.simulation_requirement || '-' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    <MobileStickyBar
      :primary-label="$t('process.toEnvironmentSetup')"
      :primary-disabled="currentPhase < 2"
      @primary-click="goToNextStep"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'
import MobileStickyBar from '../components/MobileStickyBar.vue'
import { generateOntology, getProject, buildGraph, getTaskStatus, getGraphData } from '../api/graph'
import { getPendingUpload, clearPendingUpload } from '../store/pendingUpload'
import * as d3 from 'd3'

const { t } = useI18n()

const route = useRoute()
const router = useRouter()

// Aktuelle Projekt-ID (kann sich von 'new' zur tatsächlichen ID ändern)
const currentProjectId = ref(route.params.projectId)

// Zustand
const loading = ref(true)
const graphLoading = ref(false)
const error = ref('')
const projectData = ref(null)
const graphData = ref(null)
const buildProgress = ref(null)
const ontologyProgress = ref(null) // Ontologie-Generierungsfortschritt
const currentPhase = ref(-1) // -1: Hochladen, 0: Ontologie-Generierung, 1: Graph-Aufbau, 2: Abgeschlossen
const selectedItem = ref(null) // Ausgewählter Knoten oder Kante
const isFullScreen = ref(false)

// DOM-Referenzen
const graphContainer = ref(null)
const graphSvg = ref(null)

// Polling-Timer
let pollTimer = null

// Berechnete Eigenschaften
const statusClass = computed(() => {
  if (error.value) return 'error'
  if (currentPhase.value >= 2) return 'completed'
  return 'processing'
})

const statusText = computed(() => {
  if (error.value) return t('process.aufbauFehlgeschlagen')
  if (currentPhase.value >= 2) return t('process.aufbauAbgeschlossen')
  if (currentPhase.value === 1) return t('process.graphWirdAufgebaut')
  if (currentPhase.value === 0) return t('process.ontologieWirdGeneriert')
  return t('common.initializing')
})

const entityTypes = computed(() => {
  if (!graphData.value?.nodes) return []
  
  const typeMap = {}
  const colors = ['var(--color-brand-primary)', 'var(--color-info-text)', 'var(--color-success-text)', 'var(--color-warning-text)', 'var(--color-error-text)', 'var(--color-text-secondary)']
  
  graphData.value.nodes.forEach(node => {
    const type = node.labels?.find(l => l !== 'Entity') || t('process.entity')
    if (!typeMap[type]) {
      typeMap[type] = { name: type, count: 0, color: colors[Object.keys(typeMap).length % colors.length] }
    }
    typeMap[type].count++
  })
  
  return Object.values(typeMap)
})

// Methoden
const goHome = () => {
  router.push('/')
}

const goToNextStep = () => {
  // TODO: Zur Umgebungseinrichtung wechseln
  alert(t('process.environmentSetupInDevelopment'))
}

const toggleFullScreen = () => {
  isFullScreen.value = !isFullScreen.value
  // Wait for transition to finish then re-render graph
  setTimeout(() => {
    renderGraph()
  }, 350) 
}

// Detailbereich schließen
const closeDetailPanel = () => {
  selectedItem.value = null
}

// Datum formatieren
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('de-DE', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return dateStr
  }
}

// Knoten auswählen
const selectNode = (nodeData, color) => {
  selectedItem.value = {
    type: 'node',
    data: nodeData,
    color: color,
    entityType: nodeData.labels?.find(l => l !== 'Entity' && l !== 'Node') || t('process.entity')
  }
}

// Kante auswählen
const selectEdge = (edgeData) => {
  selectedItem.value = {
    type: 'edge',
    data: edgeData
  }
}

const getPhaseStatusClass = (phase) => {
  if (currentPhase.value > phase) return 'completed'
  if (currentPhase.value === phase) return 'active'
  return 'pending'
}

const getPhaseStatusText = (phase) => {
  if (currentPhase.value > phase) return t('common.completed')
  if (currentPhase.value === phase) {
    if (phase === 1 && buildProgress.value) {
      return `${buildProgress.value.progress}%`
    }
    return t('common.processing')
  }
  return t('common.pending')
}

// Initialisierung - Neues Projekt erstellen oder bestehendes laden
const initProject = async () => {
  const paramProjectId = route.params.projectId
  
  if (paramProjectId === 'new') {
    // Neues Projekt: Hochzuladende Daten aus dem Store abrufen
    await handleNewProject()
  } else {
    // Bestehendes Projekt laden
    currentProjectId.value = paramProjectId
    await loadProject()
  }
}

// Neues Projekt verarbeiten - ontology/generate API aufrufen
const handleNewProject = async () => {
  const pending = getPendingUpload()
  
  if (!pending.isPending || pending.files.length === 0) {
    error.value = t('process.keineDateienZumHochladenVorhandenBitteZur')
    loading.value = false
    return
  }
  
  try {
    loading.value = true
    currentPhase.value = 0 // Ontologie-Generierungsphase
    ontologyProgress.value = { message: t('process.dateienWerdenHochgeladenUndDokumenteAnalysiert') }
    
    // FormData erstellen
    const formDataObj = new FormData()
    pending.files.forEach(file => {
      formDataObj.append('files', file)
    })
    formDataObj.append('simulation_requirement', pending.simulationRequirement)
    
    // Ontologie-Generierungs-API aufrufen
    const response = await generateOntology(formDataObj)
    
    if (response.success) {
      // Hochzuladende Daten löschen
      clearPendingUpload()
      
      // Projekt-ID und Daten aktualisieren
      currentProjectId.value = response.data.project_id
      projectData.value = response.data
      
      // URL aktualisieren (ohne Seite neu zu laden)
      router.replace({
        name: 'Process',
        params: { projectId: response.data.project_id }
      })
      
      ontologyProgress.value = null
      
      // Automatisch Graph-Aufbau starten
      await startBuildGraph()
    } else {
      error.value = response.error || t('process.ontologieGenerierungFehlgeschlagen')
    }
  } catch (err) {
    console.error('Handle new project error:', err)
    error.value = t('process.projektinitialisierungFehlgeschlagen') + (err.message || t('common.unknownError'))
  } finally {
    loading.value = false
  }
}

// Bestehende Projektdaten laden
const loadProject = async () => {
  try {
    loading.value = true
    const response = await getProject(currentProjectId.value)
    
    if (response.success) {
      projectData.value = response.data
      updatePhaseByStatus(response.data.status)
      
      // Automatisch Graph-Aufbau starten
      if (response.data.status === 'ontology_generated' && !response.data.graph_id) {
        await startBuildGraph()
      }
      
      // Weiter den laufenden Aufbau-Task abfragen
      if (response.data.status === 'graph_building' && response.data.graph_build_task_id) {
        currentPhase.value = 1
        startPollingTask(response.data.graph_build_task_id)
      }
      
      // Abgeschlossenen Graph laden
      if (response.data.status === 'graph_completed' && response.data.graph_id) {
        currentPhase.value = 2
        await loadGraph(response.data.graph_id)
      }
    } else {
      error.value = response.error || t('process.projektLadenFehlgeschlagen')
    }
  } catch (err) {
    console.error('Load project error:', err)
    error.value = t('process.projektLadenFehlgeschlagen2') + (err.message || t('common.unknownError'))
  } finally {
    loading.value = false
  }
}

const updatePhaseByStatus = (status) => {
  switch (status) {
    case 'created':
    case 'ontology_generated':
      currentPhase.value = 0
      break
    case 'graph_building':
      currentPhase.value = 1
      break
    case 'graph_completed':
      currentPhase.value = 2
      break
    case 'failed':
      error.value = projectData.value?.error || t('process.verarbeitungFehlgeschlagen')
      break
  }
}

// Graph-Aufbau starten
const startBuildGraph = async () => {
  try {
    currentPhase.value = 1
    // Anfangsfortschritt setzen
    buildProgress.value = {
      progress: 0,
      message: t('process.graphAufbauWirdGestartet')
    }
    
    const response = await buildGraph({ project_id: currentProjectId.value })
    
    if (response.success) {
      buildProgress.value.message = t('process.graphAufbauAufgabeWurdeGestartet')
      
      // task_id für Polling speichern
      const taskId = response.data.task_id
      
      // Graph-Daten-Polling starten (unabhängig vom Aufgabenstatus-Polling)
      startGraphPolling()
      
      // Aufgabenstatus-Polling starten
      startPollingTask(taskId)
    } else {
      error.value = response.error || t('process.graphAufbauStartenFehlgeschlagen')
      buildProgress.value = null
    }
  } catch (err) {
    console.error(t('process.buildGraphError'), err)
    error.value = t('process.graphAufbauStartenFehlgeschlagen2') + (err.message || t('common.unknownError'))
    buildProgress.value = null
  }
}

// Graph-Daten-Polling-Timer
let graphPollTimer = null

// Graph-Daten-Polling starten
const startGraphPolling = () => {
  // Sofort einmal abrufen
  fetchGraphData()
  
  // Alle 10 Sekunden automatisch Graph-Daten abrufen
  graphPollTimer = setInterval(async () => {
    await fetchGraphData()
  }, 10000)
}

// Graph manuell aktualisieren
const refreshGraph = async () => {
  graphLoading.value = true
  await fetchGraphData()
  graphLoading.value = false
}

// Graph-Daten-Polling stoppen
const stopGraphPolling = () => {
  if (graphPollTimer) {
    clearInterval(graphPollTimer)
    graphPollTimer = null
  }
}

// Graph-Daten abrufen
const fetchGraphData = async () => {
  try {
    // Zuerst Projektinfo abrufen um graph_id zu erhalten
    const projectResponse = await getProject(currentProjectId.value)
    
    if (projectResponse.success && projectResponse.data.graph_id) {
      const graphId = projectResponse.data.graph_id
      projectData.value = projectResponse.data
      
      // Graph-Daten abrufen
      const graphResponse = await getGraphData(graphId)
      
      if (graphResponse.success && graphResponse.data) {
        const newData = graphResponse.data
        const newNodeCount = newData.node_count || newData.nodes?.length || 0
        const oldNodeCount = graphData.value?.node_count || graphData.value?.nodes?.length || 0
        
        console.log(t('process.fetchingGraphDataNodes'), newNodeCount, 'edges:', newData.edge_count || newData.edges?.length || 0)
        
        // Bei Datenänderung Rendering aktualisieren
        if (newNodeCount !== oldNodeCount || !graphData.value) {
          graphData.value = newData
          await nextTick()
          renderGraph()
        }
      }
    }
  } catch (err) {
    console.log(t('process.graphDataFetch'), err.message || 'not ready')
  }
}

// Aufgabenstatus abfragen
const startPollingTask = (taskId) => {
  // Sofort eine Abfrage ausführen
  pollTaskStatus(taskId)
  
  // Dann periodisch abfragen
  pollTimer = setInterval(() => {
    pollTaskStatus(taskId)
  }, 2000)
}

// Aufgabenstatus abfragen
const pollTaskStatus = async (taskId) => {
  try {
    const response = await getTaskStatus(taskId)
    
    if (response.success) {
      const task = response.data
      
      // Fortschrittsanzeige aktualisieren
      buildProgress.value = {
        progress: task.progress || 0,
        message: task.message || t('common.processingEllipsis')
      }
      
      console.log('Task status:', task.status, 'Progress:', task.progress)
      
      if (task.status === 'completed') {
        console.log(t('process.graphAufbauAbgeschlossenVollstandigeDatenWerdenGeladen'))
        
        stopPolling()
        stopGraphPolling()
        currentPhase.value = 2
        
        // Fortschrittsanzeige auf Abgeschlossen aktualisieren
        buildProgress.value = {
          progress: 100,
          message: t('process.aufbauAbgeschlossenGraphWirdGeladen')
        }
        
        // Projektdaten neu laden um graph_id zu erhalten
        const projectResponse = await getProject(currentProjectId.value)
        if (projectResponse.success) {
          projectData.value = projectResponse.data
          
          // Endgültig vollständige Graph-Daten laden
          if (projectResponse.data.graph_id) {
            console.log(t('process.vollstandigenGraphLaden'), projectResponse.data.graph_id)
            await loadGraph(projectResponse.data.graph_id)
            console.log(t('process.graphErfolgreichGeladen'))
          }
        }
        
        // Fortschrittsanzeige löschen
        buildProgress.value = null
      } else if (task.status === 'failed') {
        stopPolling()
        stopGraphPolling()
        error.value = t('process.graphAufbauFehlgeschlagen') + (task.error || t('common.unknownError'))
        buildProgress.value = null
      }
    }
  } catch (err) {
    console.error('Poll task error:', err)
  }
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// Graph-Daten laden
const loadGraph = async (graphId) => {
  try {
    graphLoading.value = true
    const response = await getGraphData(graphId)
    
    if (response.success) {
      graphData.value = response.data
      await nextTick()
      renderGraph()
    }
  } catch (err) {
    console.error(t('process.loadGraphError'), err)
  } finally {
    graphLoading.value = false
  }
}

// Graph rendern (D3.js)
const renderGraph = () => {
  if (!graphSvg.value || !graphData.value) {
    console.log('Cannot render: svg or data missing')
    return
  }
  
  const container = graphContainer.value
  if (!container) {
    console.log('Cannot render: container missing')
    return
  }
  
  // Container-Abmessungen abrufen
  const rect = container.getBoundingClientRect()
  const width = rect.width || 800
  const height = (rect.height || 600) - 60
  
  if (width <= 0 || height <= 0) {
    console.log('Cannot render: invalid dimensions', width, height)
    return
  }
  
  console.log(t('process.renderingGraph'), width, 'x', height)
  
  const svg = d3.select(graphSvg.value)
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)
  
  svg.selectAll('*').remove()
  
  // Knotendaten verarbeiten
  const nodesData = graphData.value.nodes || []
  const edgesData = graphData.value.edges || []
  
  if (nodesData.length === 0) {
    console.log('No nodes to render')
    // Leeren Zustand anzeigen
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', height / 2)
      .attr('text-anchor', 'middle')
      .attr('fill', 'var(--color-text-muted)')
      .text(t('process.wartenAufGraphDaten'))
    return
  }
  
  // Knotenzuordnung für Namenssuche erstellen
  const nodeMap = {}
  nodesData.forEach(n => {
    nodeMap[n.uuid] = n
  })
  
  const nodes = nodesData.map(n => ({
    id: n.uuid,
    name: n.name || t('process.unknown'),
    type: n.labels?.find(l => l !== 'Entity' && l !== 'Node') || t('process.entity'),
    rawData: n // Originaldaten speichern
  }))
  
  // Knoten-ID-Menge zum Filtern gültiger Kanten erstellen
  const nodeIds = new Set(nodes.map(n => n.id))
  
  const edges = edgesData
    .filter(e => nodeIds.has(e.source_node_uuid) && nodeIds.has(e.target_node_uuid))
    .map(e => ({
      source: e.source_node_uuid,
      target: e.target_node_uuid,
      type: e.fact_type || e.name || t('process.relationship'),
      rawData: {
        ...e,
        source_name: nodeMap[e.source_node_uuid]?.name || t('process.unknown'),
        target_name: nodeMap[e.target_node_uuid]?.name || t('process.unknown')
      }
    }))
  
  console.log('Nodes:', nodes.length, 'Edges:', edges.length)
  
  // Farbzuordnung
  const types = [...new Set(nodes.map(n => n.type))]
  const colorScale = d3.scaleOrdinal()
    .domain(types)
    .range(['var(--color-brand-primary)', 'var(--color-info-text)', 'var(--color-success-text)', 'var(--color-warning-text)', 'var(--color-error-text)', 'var(--color-text-secondary)'])
  
  // Kräftebasiertes Layout
  const simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(edges).id(d => d.id).distance(100).strength(0.5))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(40))
    .force('x', d3.forceX(width / 2).strength(0.05))
    .force('y', d3.forceY(height / 2).strength(0.05))
  
  // Zoom-Funktion hinzufügen
  const g = svg.append('g')
  
  svg.call(d3.zoom()
    .extent([[0, 0], [width, height]])
    .scaleExtent([0.2, 4])
    .on('zoom', (event) => {
      g.attr('transform', event.transform)
    }))
  
  // Kanten zeichnen (mit klickbarer transparenter breiter Linie)
  const linkGroup = g.append('g')
    .attr('class', 'links')
    .selectAll('g')
    .data(edges)
    .enter()
    .append('g')
    .style('cursor', 'pointer')
    .on('click', (event, d) => {
      event.stopPropagation()
      selectEdge(d.rawData)
    })
  
  // Sichtbare dünne Linie
  const link = linkGroup.append('line')
    .attr('stroke', 'var(--color-border-strong)')
    .attr('stroke-width', 1.5)
    .attr('stroke-opacity', 0.6)
  
  // Transparente breite Linie für Klick
  linkGroup.append('line')
    .attr('stroke', 'transparent')
    .attr('stroke-width', 10)
  
  // Kantenbeschriftungen
  const linkLabel = g.append('g')
    .attr('class', 'link-labels')
    .selectAll('text')
    .data(edges)
    .enter()
    .append('text')
    .attr('font-size', '9px')
    .attr('fill', 'var(--color-text-muted)')
    .attr('text-anchor', 'middle')
    .text(d => d.type.length > 15 ? d.type.substring(0, 12) + '...' : d.type)
  
  // Knoten zeichnen
  const node = g.append('g')
    .attr('class', 'nodes')
    .selectAll('g')
    .data(nodes)
    .enter()
    .append('g')
    .style('cursor', 'pointer')
    .on('click', (event, d) => {
      event.stopPropagation()
      selectNode(d.rawData, colorScale(d.type))
    })
    .call(d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended))
  
  node.append('circle')
    .attr('r', 10)
    .attr('fill', d => colorScale(d.type))
    .attr('stroke', 'var(--color-bg-surface-raised)')
    .attr('stroke-width', 2)
    .attr('class', 'node-circle')
  
  node.append('text')
    .attr('dx', 14)
    .attr('dy', 4)
    .text(d => d.name?.substring(0, 12) || '')
    .attr('font-size', '11px')
    .attr('fill', 'var(--color-text-primary)')
    .attr('font-family', 'JetBrains Mono, monospace')
  
  // Klick auf leere Fläche schließt Detailpanel
  svg.on('click', () => {
    closeDetailPanel()
  })
  
  simulation.on('tick', () => {
    // Position aller Kanten aktualisieren (sichtbare Linie und transparenter Klickbereich)
    linkGroup.selectAll('line')
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)
    
    // Position der Kantenbeschriftungen aktualisieren
    linkLabel
      .attr('x', d => (d.source.x + d.target.x) / 2)
      .attr('y', d => (d.source.y + d.target.y) / 2 - 5)
    
    node.attr('transform', d => `translate(${d.x},${d.y})`)
  })
  
  function dragstarted(event) {
    if (!event.active) simulation.alphaTarget(0.3).restart()
    event.subject.fx = event.subject.x
    event.subject.fy = event.subject.y
  }
  
  function dragged(event) {
    event.subject.fx = event.x
    event.subject.fy = event.y
  }
  
  function dragended(event) {
    if (!event.active) simulation.alphaTarget(0)
    event.subject.fx = null
    event.subject.fy = null
  }
}

// Graph-Datenänderungen beobachten
watch(graphData, () => {
  if (graphData.value) {
    nextTick(() => renderGraph())
  }
})

// Lebenszyklus
onMounted(() => {
  initProject()
})

onUnmounted(() => {
  stopPolling()
  stopGraphPolling()
})
</script>

<style scoped>
.process-page {
  min-height: 100vh;
  background: var(--color-bg-surface-raised);
  font-family: var(--font-body);
  overflow: hidden; /* Prevent body scroll in fullscreen */
}

/* Navigationsleiste */
.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 56px;
  background: color-mix(in srgb, var(--color-bg-canvas) 88%, transparent);
  color: var(--color-text-primary);
  border-bottom: 1px solid var(--color-border-subtle);
  backdrop-filter: saturate(180%) blur(14px);
  -webkit-backdrop-filter: saturate(180%) blur(14px);
  z-index: 10;
  position: relative;
}

.nav-brand {
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
  letter-spacing: normal;
  cursor: pointer;
  transition: opacity 0.2s;
}

.nav-brand:hover {
  opacity: 0.8;
}

.nav-center {
  display: flex;
  align-items: center;
  gap: 12px;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.step-badge {
  background: var(--color-brand-subtle);
  color: var(--color-brand-primary);
  border: 1px solid var(--color-brand-border);
  padding: 2px 8px;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: normal;
  border-radius: 2px;
}

.step-name {
  font-size: 0.85rem;
  letter-spacing: normal;
  color: var(--color-text-primary);
}

.nav-status {
  display: flex;
  align-items: center;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-text-secondary);
  margin-right: 8px;
}

.status-dot.processing {
  background: var(--color-brand-primary);
  animation: pulse 1.5s infinite;
}

.status-dot.completed {
  background: var(--color-success-text);
}

.status-dot.error {
  background: var(--color-error-text);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-text {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
}

/* Hauptinhaltsbereich */
.main-content {
  display: flex;
  height: calc(100vh - 56px);
  position: relative;
}

/* Linkes Panel - 50% Standard */
.left-panel {
  width: 50%;
  flex: none; /* Fixed width initially */
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--color-border-default);
  transition: width 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  background: var(--color-bg-surface-raised);
  z-index: 5;
}

.left-panel.full-screen {
  width: 100%;
  border-right: none;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  border-bottom: 1px solid var(--color-border-default);
  background: var(--color-bg-surface-raised);
  height: 50px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-deco {
  color: var(--color-brand-primary);
  font-size: 0.8rem;
}

.header-title {
  font-size: 0.85rem;
  font-weight: 600;
  letter-spacing: normal;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 0.75rem;
  color: var(--color-text-secondary);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-val {
  font-weight: 600;
  color: var(--color-text-primary);
}

.stat-divider {
  color: var(--color-border-subtle);
}

.action-buttons {
    display: flex;
    align-items: center;
    gap: 8px;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: transparent;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--color-text-secondary);
  border-radius: 2px;
}

.action-btn:hover:not(:disabled) {
  background: var(--color-bg-surface-subtle);
  color: var(--color-text-primary);
}

.action-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.icon-refresh, .icon-fullscreen {
  font-size: 1rem;
  line-height: 1;
}

.icon-refresh.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Graph-Container */
.graph-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.graph-loading,
.graph-waiting,
.graph-error {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.loading-animation {
  position: relative;
  width: 80px;
  height: 80px;
  margin: 0 auto 20px;
}

.loading-ring {
  position: absolute;
  border: 2px solid transparent;
  border-radius: 50%;
  animation: ring-rotate 1.5s linear infinite;
}

.loading-ring:nth-child(1) {
  width: 80px;
  height: 80px;
  border-top-color: var(--color-text-primary);
}

.loading-ring:nth-child(2) {
  width: 60px;
  height: 60px;
  top: 10px;
  left: 10px;
  border-right-color: var(--color-brand-primary);
  animation-delay: 0.2s;
}

.loading-ring:nth-child(3) {
  width: 40px;
  height: 40px;
  top: 20px;
  left: 20px;
  border-bottom-color: var(--color-text-secondary);
  animation-delay: 0.4s;
}

@keyframes ring-rotate {
  to { transform: rotate(360deg); }
}

.loading-text,
.waiting-text {
  font-size: 0.9rem;
  color: var(--color-text-primary);
  margin: 0 0 8px;
}

.waiting-hint {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  margin: 0;
}

.waiting-icon {
  margin-bottom: 20px;
}

.network-icon {
  width: 100px;
  height: 100px;
  opacity: 0.6;
}

.graph-view {
  width: 100%;
  height: 100%;
  position: relative;
}

.graph-svg {
  width: 100%;
  height: 100%;
  display: block;
}

.graph-building-hint {
  position: absolute;
  bottom: 16px;
  left: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  border: 1px solid var(--color-brand-primary);
  font-size: 0.8rem;
  color: var(--color-brand-primary);
}

.building-dot {
  width: 8px;
  height: 8px;
  background: var(--color-brand-primary);
  border-radius: 50%;
  animation: pulse 1s infinite;
}

/* Knoten-/Kanten-Detailpanel */
.detail-panel {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 320px;
  max-height: calc(100% - 32px);
  background: var(--color-bg-surface-raised);
  border: 1px solid var(--color-border-default);
  box-shadow: 0 4px 20px color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  z-index: 100;
}

.detail-panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--color-bg-surface-subtle);
  border-bottom: 1px solid var(--color-border-default);
}

.detail-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.detail-badge {
  padding: 2px 10px;
  font-size: 0.75rem;
  color: var(--color-text-inverse);
  border-radius: 2px;
}

.detail-close {
  margin-left: auto;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  font-size: 1.2rem;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: color 0.2s;
}

.detail-close:hover {
  color: var(--color-text-primary);
}

.detail-content {
  padding: 16px;
  overflow-y: auto;
  flex: 1;
}

.detail-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: 12px;
}

.detail-label {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  min-width: 70px;
  flex-shrink: 0;
}

.detail-value {
  font-size: 0.85rem;
  color: var(--color-text-primary);
  word-break: break-word;
}

.detail-value.uuid {
  font-family: var(--font-body);
  font-size: 0.75rem;
  color: var(--color-text-secondary);
}

.detail-section {
  margin-bottom: 12px;
}

.detail-summary {
  margin: 8px 0 0 0;
  font-size: 0.85rem;
  color: var(--color-text-primary);
  line-height: 1.6;
  padding: 10px;
  background: var(--color-bg-surface-subtle);
  border-left: 3px solid var(--color-brand-primary);
}

.detail-labels {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.label-tag {
  padding: 2px 8px;
  font-size: 0.75rem;
  background: var(--color-border-subtle);
  border: 1px solid var(--color-border-default);
  color: var(--color-text-secondary);
}

/* Kanten-Beziehungsanzeige */
.edge-relation {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
  padding: 12px;
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-default);
}

.edge-source,
.edge-target {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--color-text-primary);
}

.edge-arrow {
  color: var(--color-text-muted);
}

.edge-type {
  padding: 2px 8px;
  font-size: 0.75rem;
  background: var(--color-brand-primary);
  color: var(--color-text-inverse);
}

.detail-value.highlight {
  font-weight: 600;
  color: var(--color-text-primary);
}

.detail-subtitle {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 16px 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-border-default);
}

/* Eigenschaftsliste */
.properties-list {
  margin-top: 8px;
  padding: 10px;
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-default);
}

.property-item {
  display: flex;
  margin-bottom: 6px;
  font-size: 0.85rem;
}

.property-item:last-child {
  margin-bottom: 0;
}

.property-key {
  color: var(--color-text-secondary);
  margin-right: 8px;
  font-family: var(--font-body);
}

.property-value {
  color: var(--color-text-primary);
  word-break: break-word;
}

/* Episodenliste */
.episodes-list {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.episode-tag {
  display: block;
  padding: 6px 10px;
  font-size: 0.75rem;
  font-family: var(--font-body);
  background: var(--color-border-subtle);
  border: 1px solid var(--color-border-default);
  color: var(--color-text-secondary);
  word-break: break-all;
}

.error-icon {
  font-size: 2rem;
  display: block;
  margin-bottom: 10px;
}

/* Graph-Legende */
.graph-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 12px 24px;
  border-top: 1px solid var(--color-border-default);
  background: var(--color-bg-surface-subtle);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.legend-label {
  color: var(--color-text-primary);
}

.legend-count {
  color: var(--color-text-muted);
}

/* Rechtes Panel - 50% Standard */
.right-panel {
  width: 50%;
  flex: none;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-surface-raised);
  transition: width 0.35s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s ease, transform 0.3s ease;
  overflow: hidden;
  opacity: 1;
}

.right-panel.hidden {
  width: 0;
  opacity: 0;
  transform: translateX(20px);
  pointer-events: none;
}

.right-panel .panel-header.dark-header {
  background: var(--color-text-primary);
  color: var(--color-text-inverse);
  border-bottom: none;
}

.right-panel .header-icon {
  color: var(--color-brand-primary);
  margin-right: 8px;
}

/* Prozessinhalt */
.process-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

/* Prozessphase */
.process-phase {
  margin-bottom: 24px;
  border: 1px solid var(--color-border-default);
  opacity: 0.5;
  transition: all 0.3s;
}

.process-phase.active,
.process-phase.completed {
  opacity: 1;
}

.process-phase.active {
  border-color: var(--color-brand-primary);
}

.process-phase.completed {
  border-color: var(--color-success-text);
}

.phase-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px;
  background: var(--color-bg-surface-subtle);
  border-bottom: 1px solid var(--color-border-default);
}

.process-phase.active .phase-header {
  background: var(--color-warning-bg);
}

.process-phase.completed .phase-header {
  background: var(--color-success-bg);
}

.phase-num {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-border-default);
  line-height: 1;
}

.process-phase.active .phase-num {
  color: var(--color-brand-primary);
}

.process-phase.completed .phase-num {
  color: var(--color-success-text);
}

.phase-info {
  flex: 1;
}

.phase-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 4px;
}

.phase-api {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  font-family: var(--font-body);
}

.phase-status {
  font-size: 0.75rem;
  padding: 4px 10px;
  background: var(--color-border-subtle);
  color: var(--color-text-secondary);
}

.phase-status.active {
  background: var(--color-brand-primary);
  color: var(--color-text-inverse);
}

.phase-status.completed {
  background: var(--color-success-text);
  color: var(--color-text-inverse);
}

/* Phasendetails */
.phase-detail {
  padding: 16px;
}

/* Entitäts-Tags */
.entity-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.entity-tag {
  font-size: 0.75rem;
  padding: 4px 10px;
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-default);
  color: var(--color-text-primary);
}

/* Beziehungsliste */
.relation-list {
  font-size: 0.8rem;
}

.relation-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px dashed var(--color-border-subtle);
}

.relation-item:last-child {
  border-bottom: none;
}

.rel-source,
.rel-target {
  color: var(--color-text-primary);
}

.rel-arrow {
  color: var(--color-border-strong);
}

.rel-name {
  color: var(--color-brand-primary);
  font-weight: 500;
}

.relation-more {
  padding-top: 8px;
  color: var(--color-text-muted);
  font-size: 0.75rem;
}

/* Ontologie-Generierungsfortschritt */
.ontology-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--color-warning-bg);
  border: 1px solid var(--color-warning-border);
}

.progress-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-warning-border);
  border-top-color: var(--color-brand-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.progress-text {
  font-size: 0.85rem;
  color: var(--color-text-primary);
}

/* Wartezustand */
.waiting-state {
  padding: 16px;
  background: var(--color-bg-surface-subtle);
  border: 1px dashed var(--color-border-default);
  text-align: center;
}

.waiting-hint {
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

/* Fortschrittsbalken */
.progress-bar {
  height: 6px;
  background: var(--color-border-default);
  margin-bottom: 8px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-brand-primary);
  transition: width 0.3s;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
}

.progress-message {
  color: var(--color-text-secondary);
}

.progress-percent {
  color: var(--color-brand-primary);
  font-weight: 600;
}

/* Aufbauergebnis */
.build-result {
  display: flex;
  gap: 16px;
}

.result-item {
  flex: 1;
  text-align: center;
  padding: 12px;
  background: var(--color-bg-surface-subtle);
}

.result-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}

.result-label {
  font-size: 0.7rem;
  color: var(--color-text-muted);
  text-transform: none;
  letter-spacing: normal;
}

/* Nächster-Schritt-Schaltfläche */
.next-step-section {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--color-border-default);
}

.next-step-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 16px;
  background: var(--color-text-primary);
  color: var(--color-text-inverse);
  border: none;
  font-size: 1rem;
  font-weight: 500;
  letter-spacing: normal;
  cursor: pointer;
  transition: all 0.2s;
}

.next-step-btn:hover:not(:disabled) {
  background: var(--color-brand-primary);
}

.next-step-btn:disabled {
  background: var(--color-border-strong);
  cursor: not-allowed;
}

.btn-arrow {
  font-size: 1.2rem;
}

/* Projektinformationspanel */
.project-panel {
  border-top: 1px solid var(--color-border-default);
  background: var(--color-bg-surface-subtle);
}

.project-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 24px;
  border-bottom: 1px solid var(--color-border-default);
}

.project-icon {
  color: var(--color-brand-primary);
}

.project-title {
  font-size: 0.85rem;
  font-weight: 600;
}

.project-details {
  padding: 16px 24px;
}

.project-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 8px 0;
  border-bottom: 1px dashed var(--color-border-default);
  font-size: 0.8rem;
}

.project-item:last-child {
  border-bottom: none;
}

.item-label {
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.item-value {
  color: var(--color-text-primary);
  text-align: right;
  max-width: 60%;
  word-break: break-all;
}

.item-value.code {
  font-family: var(--font-body);
  font-size: 0.75rem;
  color: var(--color-text-secondary);
}

/* Responsiv */
@media (max-width: 1024px) {
  .main-content {
    flex-direction: column;
  }
  
  .left-panel {
    width: 100% !important;
    border-right: none;
    border-bottom: 1px solid var(--color-border-default);
    height: 50vh;
  }
  
  .right-panel {
    width: 100% !important;
    height: 50vh;
    opacity: 1 !important;
    transform: none !important;
  }
  
  .right-panel.hidden {
      display: none;
  }
}

@media (max-width: 768px) {
  .process-page { overflow-x: hidden; padding-bottom: calc(130px + env(safe-area-inset-bottom)); }
  .next-step-section { display: none; }
  .navbar { height: auto; min-height: 56px; padding: 6px 16px; flex-wrap: wrap; gap: 8px; }
  .nav-center { position: static; order: 3; width: 100%; transform: none; justify-content: center; }
  .nav-status { margin-left: auto; }
  .main-content { height: auto; min-height: calc(100dvh - 116px); }
  .left-panel, .right-panel { height: auto; min-height: 50dvh; min-width: 0; }
  .panel-header { padding-inline: 16px; flex-wrap: wrap; gap: 8px; }
  .right-content, .project-details { padding-inline: 16px; }
  button, [role="button"], input, select, textarea { min-height: var(--touch-target-min); }
  .detail-panel { inset-inline: 8px; width: auto; }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; transition-duration: .01ms !important; }
}
</style>
