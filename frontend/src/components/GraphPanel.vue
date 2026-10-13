<template>
  <div class="graph-panel">
    <div class="panel-header">
      <div class="panel-header__row-top">
        <h2 class="panel-title">{{ $t('graph.wissensgraph') }}</h2>
        <button
          v-if="graphData && entityTypes.length"
          type="button"
          class="legend-toggle-btn"
          :class="{ 'is-active': showLegend }"
          :aria-expanded="showLegend"
          @click="showLegend = !showLegend"
        >
          <span class="legend-toggle-btn__dot" aria-hidden="true"></span>
          <span>{{ $t('graph.legende') }}</span>
        </button>
      </div>
      <div class="panel-header__row-toolbar">
        <div class="header-tools">
          <button type="button" class="tool-btn" @click="$emit('refresh')" :disabled="loading" :aria-label="$t('graph.graphAktualisieren')">
            <span class="icon-refresh" :class="{ 'spinning': loading }" aria-hidden="true">↻</span>
            <span class="btn-text">{{ $t('common.refresh') }}</span>
          </button>
          <button type="button" class="tool-btn" @click="$emit('toggle-maximize')" :aria-label="$t('graph.maximierenWiederherstellen')">
            <span class="icon-maximize" aria-hidden="true">⛶</span>
            <span class="btn-text desktop-only">{{ $t('graph.fullscreen') }}</span>
          </button>
          <div v-if="graphData" class="edge-labels-control">
            <label class="toggle-switch-compact" for="edge-label-toggle">
              <input id="edge-label-toggle" type="checkbox" v-model="showEdgeLabels" />
              <span class="slider" aria-hidden="true"></span>
              <span class="toggle-label">{{ $t('graph.kanten') }}</span>
            </label>
          </div>
        </div>
      </div>
    </div>
    
    <div class="graph-container" ref="graphContainer">
      <!-- Graph-Visualisierung -->
      <div v-if="graphData" class="graph-view">
        <svg ref="graphSvg" class="graph-svg"></svg>
        
        <!-- Aufbau-/Simulationshinweis -->
        <div v-if="currentPhase === 1 || isSimulating" class="graph-building-hint graph-building-hint--top" role="status" aria-live="polite">
          <div class="memory-icon-wrapper">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="memory-icon">
              <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 4.44-4.04z" />
              <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-4.44-4.04z" />
            </svg>
          </div>
          {{ isSimulating ? $t('graph.graphragLangzeitKurzzeitgedachtnisWirdAktualisiert') : $t('graph.liveUpdate') }}
        </div>
        
        <!-- Hinweis nach Simulationsende -->
        <div v-if="showSimulationFinishedHint" class="graph-building-hint finished-hint">
          <div class="hint-icon-wrapper">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="hint-icon">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="16" x2="12" y2="12"></line>
              <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
          </div>
          <span class="hint-text">{{ $t('graph.esWerdenNochWenigeInhalteVerarbeitetBitte') }}</span>
          <button class="hint-close-btn" @click="dismissFinishedHint" :title="$t('graph.hinweisSchliessen')">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        
        <!-- Knoten-/Kantendetail-Panel -->
        <div v-if="selectedItem" class="detail-panel">
          <div class="detail-panel-header">
            <span class="detail-title">{{ selectedItem.type === 'node' ? $t('graph.nodeDetails') : $t('graph.relationship') }}</span>
            <span v-if="selectedItem.type === 'node'" class="detail-type-badge" :style="{ background: selectedItem.color, color: 'var(--color-bg-surface-raised)' }">
              {{ formatLabel(selectedItem.entityType) }}
            </span>
            <button class="detail-close" @click="closeDetailPanel">×</button>
          </div>
          
          <!-- Knotendetails -->
          <div v-if="selectedItem.type === 'node'" class="detail-content">
            <div class="detail-row">
              <span class="detail-label">{{ $t('graph.name') }}</span>
              <span class="detail-value">{{ selectedItem.data.name }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">{{ $t('graph.uuid') }}</span>
              <span class="detail-value uuid-text">{{ selectedItem.data.uuid }}</span>
            </div>
            <div class="detail-row" v-if="selectedItem.data.created_at">
              <span class="detail-label">{{ $t('graph.erstellt') }}</span>
              <span class="detail-value">{{ formatDateTime(selectedItem.data.created_at) }}</span>
            </div>

            <!-- Eigenschaften -->
            <div class="detail-section" v-if="selectedItem.data.attributes && Object.keys(selectedItem.data.attributes).length > 0">
              <div class="section-title">{{ $t('graph.eigenschaften') }}</div>
              <div class="properties-list">
                <div v-for="(value, key) in selectedItem.data.attributes" :key="key" class="property-item">
                  <span class="property-key">{{ key }}:</span>
                  <span class="property-value">{{ value || $t('common.none') }}</span>
                </div>
              </div>
            </div>
            
            <!-- Zusammenfassung -->
            <div class="detail-section" v-if="selectedItem.data.summary">
              <div class="section-title">{{ $t('graph.zusammenfassung') }}</div>
              <div class="summary-text">{{ selectedItem.data.summary }}</div>
            </div>
            
            <!-- Bezeichnungen -->
            <div class="detail-section" v-if="selectedItem.data.labels && selectedItem.data.labels.length > 0">
              <div class="section-title">{{ $t('graph.bezeichnungen') }}</div>
              <div class="labels-list">
                <span v-for="label in selectedItem.data.labels" :key="label" class="label-tag">
                  {{ formatLabel(label) }}
                </span>
              </div>
            </div>
          </div>
          
          <!-- Kantendetails -->
          <div v-else class="detail-content">
            <!-- Selbstschleifen-Gruppendetails -->
            <template v-if="selectedItem.data.isSelfLoopGroup">
              <div class="edge-relation-header self-loop-header">
                {{ selectedItem.data.source_name }} {{ $t('graph.selbstbeziehungen') }}
                <span class="self-loop-count">{{ selectedItem.data.selfLoopCount }} {{ $t('graph.eintrage') }}</span>
              </div>
              
              <div class="self-loop-list">
                <div 
                  v-for="(loop, idx) in selectedItem.data.selfLoopEdges" 
                  :key="loop.uuid || idx" 
                  class="self-loop-item"
                  :class="{ expanded: expandedSelfLoops.has(loop.uuid || idx) }"
                >
                  <div 
                    class="self-loop-item-header"
                    @click="toggleSelfLoop(loop.uuid || idx)"
                  >
                    <span class="self-loop-index">#{{ idx + 1 }}</span>
                    <span class="self-loop-name">{{ formatLabel(loop.name || loop.fact_type || 'RELATED', 'relation') }}</span>
                    <span class="self-loop-toggle">{{ expandedSelfLoops.has(loop.uuid || idx) ? '−' : '+' }}</span>
                  </div>
                  
                  <div class="self-loop-item-content" v-show="expandedSelfLoops.has(loop.uuid || idx)">
                    <div class="detail-row" v-if="loop.uuid">
                      <span class="detail-label">{{ $t('graph.uuid') }}</span>
                      <span class="detail-value uuid-text">{{ loop.uuid }}</span>
                    </div>
                    <div class="detail-row" v-if="loop.fact">
                      <span class="detail-label">{{ $t('graph.fakt') }}</span>
                      <span class="detail-value fact-text">{{ loop.fact }}</span>
                    </div>
                    <div class="detail-row" v-if="loop.fact_type">
                      <span class="detail-label">{{ $t('graph.typ') }}</span>
                      <span class="detail-value">{{ loop.fact_type }}</span>
                    </div>
                    <div class="detail-row" v-if="loop.created_at">
                      <span class="detail-label">{{ $t('graph.erstellt') }}</span>
                      <span class="detail-value">{{ formatDateTime(loop.created_at) }}</span>
                    </div>
                    <div v-if="loop.episodes && loop.episodes.length > 0" class="self-loop-episodes">
                      <span class="detail-label">{{ $t('graph.episoden') }}</span>
                      <div class="episodes-list compact">
                        <span v-for="ep in loop.episodes" :key="ep" class="episode-tag small">{{ ep }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </template>
            
            <!-- Normale Kantendetails -->
            <template v-else>
              <div class="edge-relation-header">
                {{ selectedItem.data.source_name }} → {{ formatLabel(selectedItem.data.name || 'RELATED_TO', 'relation') }} → {{ selectedItem.data.target_name }}
              </div>
              
              <div class="detail-row">
                <span class="detail-label">{{ $t('graph.uuid') }}</span>
                <span class="detail-value uuid-text">{{ selectedItem.data.uuid }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">{{ $t('graph.label') }}</span>
                <span class="detail-value">{{ formatLabel(selectedItem.data.name || 'RELATED_TO', 'relation') }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">{{ $t('graph.type') }}</span>
                <span class="detail-value">{{ selectedItem.data.fact_type || $t('graph.unknown') }}</span>
              </div>
              <div class="detail-row" v-if="selectedItem.data.fact">
                <span class="detail-label">{{ $t('graph.fact') }}</span>
                <span class="detail-value fact-text">{{ selectedItem.data.fact }}</span>
              </div>
              
              <!-- Episoden -->
              <div class="detail-section" v-if="selectedItem.data.episodes && selectedItem.data.episodes.length > 0">
                <div class="section-title">{{ $t('graph.episodes') }}</div>
                <div class="episodes-list">
                  <span v-for="ep in selectedItem.data.episodes" :key="ep" class="episode-tag">
                    {{ ep }}
                  </span>
                </div>
              </div>
              
              <div class="detail-row" v-if="selectedItem.data.created_at">
                <span class="detail-label">{{ $t('graph.created') }}</span>
                <span class="detail-value">{{ formatDateTime(selectedItem.data.created_at) }}</span>
              </div>
              <div class="detail-row" v-if="selectedItem.data.valid_at">
                <span class="detail-label">{{ $t('graph.validFrom') }}</span>
                <span class="detail-value">{{ formatDateTime(selectedItem.data.valid_at) }}</span>
              </div>
            </template>
          </div>
        </div>
      </div>
      
      <!-- Ladezustand -->
      <div v-else-if="loading" class="graph-state">
        <div class="loading-spinner"></div>
        <p>{{ $t('graph.loadingGraphData') }}</p>
      </div>

      <!-- Warte-/Leerzustand -->
      <div v-else class="graph-state">
        <div class="empty-icon">❖</div>
        <p class="empty-text">{{ $t('graph.waitingForOntology') }}</p>
      </div>
    </div>

    <!-- Legende unten (Bottom Left) -->
    <div v-if="graphData && entityTypes.length" class="graph-legend" :class="{ 'is-open': showLegend }" role="region" :aria-label="$t('graph.artenVonAkteuren')">
      <div class="legend-header">
        <span class="legend-title">{{ $t('graph.artenVonAkteuren') }}</span>
        <button type="button" class="legend-close-btn" @click="showLegend = false" :aria-label="$t('common.close')">×</button>
      </div>
      <div class="legend-items">
        <div class="legend-item" v-for="type in entityTypes" :key="type.name">
          <span class="legend-dot" :style="{ background: type.color }"></span>
          <span class="legend-label">{{ formatLabel(type.name) }}</span>
        </div>
      </div>
    </div>
    
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import * as d3 from 'd3'
import { useI18n } from 'vue-i18n'
import { formatLabel } from '../utils/labels.js'

const { t } = useI18n()

const props = defineProps({
  graphData: Object,
  loading: Boolean,
  currentPhase: Number,
  isSimulating: Boolean
})

const emit = defineEmits(['refresh', 'toggle-maximize'])

const graphContainer = ref(null)
const graphSvg = ref(null)
const selectedItem = ref(null)
const showEdgeLabels = ref(true) // Kantenbezeichnungen standardmäßig anzeigen
const expandedSelfLoops = ref(new Set()) // Aufgeklappte Selbstschleifen-Einträge
const showSimulationFinishedHint = ref(false) // Hinweis nach Simulationsende
const wasSimulating = ref(false) // Verfolgt, ob vorher simuliert wurde
const showLegend = ref(typeof window !== 'undefined' && window.matchMedia('(min-width: 1024px)').matches)

const nodeCountRef = ref(0)

const updateNodeLabelVisibility = () => {
  if (!nodeLabelsRef) return
  const selectedUuid = selectedItem.value?.type === 'node' ? selectedItem.value.data?.uuid : null
  const alwaysShow = nodeCountRef.value > 0 && nodeCountRef.value <= 60
  const k = currentZoomK > 0 ? currentZoomK : 1
  const basePx = typeof window !== 'undefined' && window.innerWidth <= 768 ? 12 : 11
  // Bildschirmgröße = SVG-px * Zoom; mind. 11 px sichtbar halten
  const screenPx = alwaysShow ? Math.max(basePx, 11 / k) : basePx
  nodeLabelsRef
    .style('opacity', d => {
      if (alwaysShow) return 1
      if (currentZoomK >= 0.6) return 1
      if (selectedUuid && d.rawData?.uuid === selectedUuid) return 1
      return 0
    })
    .attr('font-size', `${screenPx}px`)
}

const updateEdgeLabelVisibility = () => {
  if (!linkLabelsRef) return
  const hideAll = !showEdgeLabels.value
  const selectedUuid = selectedItem.value?.type === 'node' ? selectedItem.value.data?.uuid : null
  const selectedEdgeUuid = selectedItem.value?.type === 'edge' ? selectedItem.value.data?.uuid : null
  const showFor = (d) => {
    if (hideAll) return false
    if (currentZoomK >= 0.8) return true
    if (selectedEdgeUuid && d.rawData?.uuid === selectedEdgeUuid) return true
    if (selectedUuid) {
      const srcUuid = d.source?.rawData?.uuid
      const tgtUuid = d.target?.rawData?.uuid
      if (srcUuid === selectedUuid || tgtUuid === selectedUuid) return true
    }
    return false
  }
  linkLabelsRef.style('display', d => (showFor(d) ? 'block' : 'none'))
  if (linkLabelBgRef) {
    linkLabelBgRef.style('display', d => (showFor(d) ? 'block' : 'none'))
  }
}

// Hinweis nach Simulationsende schließen
const dismissFinishedHint = () => {
  showSimulationFinishedHint.value = false
}

// Überwacht isSimulating-Änderungen, erkennt Simulationsende
watch(() => props.isSimulating, (newValue, oldValue) => {
  if (wasSimulating.value && !newValue) {
    // Von Simulation zu Nicht-Simulation gewechselt, Hinweis anzeigen
    showSimulationFinishedHint.value = true
  }
  wasSimulating.value = newValue
}, { immediate: true })

// Selbstschleifen-Eintrag auf-/zuklappen
const toggleSelfLoop = (id) => {
  const newSet = new Set(expandedSelfLoops.value)
  if (newSet.has(id)) {
    newSet.delete(id)
  } else {
    newSet.add(id)
  }
  expandedSelfLoops.value = newSet
}

// Entitätstypen für die Legende berechnen
const entityTypes = computed(() => {
  if (!props.graphData?.nodes) return []
  const typeMap = {}
  // Ansprechende Farbpalette
  const colors = [
    'var(--color-brand-primary)', 'var(--color-info-text)', 'var(--color-success-text)',
    'var(--color-warning-text)', 'var(--color-error-text)', 'var(--color-text-secondary)'
  ]
  
  props.graphData.nodes.forEach(node => {
    const type = node.labels?.find(l => l !== 'Entity') || t('graph.entity')
    if (!typeMap[type]) {
      typeMap[type] = { name: type, count: 0, color: colors[Object.keys(typeMap).length % colors.length] }
    }
    typeMap[type].count++
  })
  return Object.values(typeMap)
})

// Datum/Uhrzeit formatieren
const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('de-DE', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })
  } catch {
    return dateStr
  }
}

const closeDetailPanel = () => {
  selectedItem.value = null
  expandedSelfLoops.value = new Set() // Aufklappstatus zurücksetzen
  updateNodeLabelVisibility()
}

let currentSimulation = null
let linkLabelsRef = null
let linkLabelBgRef = null
let nodeLabelsRef = null
let currentZoomK = 1
let resizeObserver = null
let zoomBehavior = null
let fitTimer = null

const zoomToFit = (paddingPercent = 0.88, animate = true) => {
  if (!graphSvg.value || !graphContainer.value || !zoomBehavior) return
  const svg = d3.select(graphSvg.value)
  const group = svg.select('g')
  if (group.empty()) return
  const bounds = group.node().getBBox()
  const fullWidth = graphContainer.value.clientWidth
  const fullHeight = graphContainer.value.clientHeight
  if (!bounds.width || !bounds.height || !fullWidth || !fullHeight) return
  const scale = Math.max(0.15, Math.min(1.8, paddingPercent / Math.max(bounds.width / fullWidth, bounds.height / fullHeight)))
  const transform = d3.zoomIdentity
    .translate(fullWidth / 2 - scale * (bounds.x + bounds.width / 2), fullHeight / 2 - scale * (bounds.y + bounds.height / 2))
    .scale(scale)
  const target = animate ? svg.transition().duration(400) : svg
  target.call(zoomBehavior.transform, transform)
}

const renderGraph = () => {
  if (!graphSvg.value || !props.graphData) return
  
  // Vorherige Simulation stoppen
  if (currentSimulation) {
    currentSimulation.stop()
  }
  
  const container = graphContainer.value
  const width = container.clientWidth
  const height = container.clientHeight
  if (width <= 0 || height <= 0) return
  
  const svg = d3.select(graphSvg.value)
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)
    
  svg.selectAll('*').remove()
  nodeLabelsRef = null
  currentZoomK = 1
  
  const nodesData = props.graphData.nodes || []
  const edgesData = props.graphData.edges || []
  
  if (nodesData.length === 0) return

  // Prep data
  const nodeMap = {}
  nodesData.forEach(n => nodeMap[n.uuid] = n)
  
  const nodes = nodesData.map(n => ({
    id: n.uuid,
    name: n.name || t('graph.unknown'),
    type: n.labels?.find(l => l !== 'Entity') || t('graph.entity'),
    rawData: n
  }))
  
  const nodeIds = new Set(nodes.map(n => n.id))
  
  // Kantendaten verarbeiten, Anzahl und Index der Kanten zwischen gleichen Knotenpaaren berechnen
  const edgePairCount = {}
  const selfLoopEdges = {} // Selbstschleifen-Kanten nach Knoten gruppiert
  const tempEdges = edgesData
    .filter(e => nodeIds.has(e.source_node_uuid) && nodeIds.has(e.target_node_uuid))
  
  // Kantenanzahl zwischen Knotenpaaren zählen, Selbstschleifen sammeln
  tempEdges.forEach(e => {
    if (e.source_node_uuid === e.target_node_uuid) {
      // Selbstschleife - in Array sammeln
      if (!selfLoopEdges[e.source_node_uuid]) {
        selfLoopEdges[e.source_node_uuid] = []
      }
      selfLoopEdges[e.source_node_uuid].push({
        ...e,
        source_name: nodeMap[e.source_node_uuid]?.name,
        target_name: nodeMap[e.target_node_uuid]?.name
      })
    } else {
      const pairKey = [e.source_node_uuid, e.target_node_uuid].sort().join('_')
      edgePairCount[pairKey] = (edgePairCount[pairKey] || 0) + 1
    }
  })
  
  // Aktuellen Kantenindex pro Knotenpaar verfolgen
  const edgePairIndex = {}
  const processedSelfLoopNodes = new Set() // Bereits verarbeitete Selbstschleifen-Knoten
  
  const edges = []
  
  tempEdges.forEach(e => {
    const isSelfLoop = e.source_node_uuid === e.target_node_uuid
    
    if (isSelfLoop) {
      // Selbstschleifen-Kante - pro Knoten nur eine zusammengefasste Selbstschleife hinzufügen
      if (processedSelfLoopNodes.has(e.source_node_uuid)) {
        return // Bereits verarbeitet, überspringen
      }
      processedSelfLoopNodes.add(e.source_node_uuid)
      
      const allSelfLoops = selfLoopEdges[e.source_node_uuid]
      const nodeName = nodeMap[e.source_node_uuid]?.name || t('graph.unknown')
      
      edges.push({
        source: e.source_node_uuid,
        target: e.target_node_uuid,
        type: 'SELF_LOOP',
        name: `Selbstbeziehungen (${allSelfLoops.length})`,
        curvature: 0,
        isSelfLoop: true,
        rawData: {
          isSelfLoopGroup: true,
          source_name: nodeName,
          target_name: nodeName,
          selfLoopCount: allSelfLoops.length,
          selfLoopEdges: allSelfLoops // Alle Selbstschleifen-Kantendetails speichern
        }
      })
      return
    }
    
    const pairKey = [e.source_node_uuid, e.target_node_uuid].sort().join('_')
    const totalCount = edgePairCount[pairKey]
    const currentIndex = edgePairIndex[pairKey] || 0
    edgePairIndex[pairKey] = currentIndex + 1
    
    // Prüfen, ob die Kantenrichtung mit der normalisierten Richtung übereinstimmt (Quell-UUID < Ziel-UUID)
    const isReversed = e.source_node_uuid > e.target_node_uuid
    
    // Krümmung berechnen: bei mehreren Kanten verteilen, einzelne Kante als Gerade
    let curvature = 0
    if (totalCount > 1) {
      // Krümmung gleichmäßig verteilen, deutliche Unterscheidung sicherstellen
      // Krümmungsbereich steigt mit Kantenanzahl
      const curvatureRange = Math.min(1.2, 0.6 + totalCount * 0.15)
      curvature = ((currentIndex / (totalCount - 1)) - 0.5) * curvatureRange * 2
      
      // Bei umgekehrter Kantenrichtung Krümmung umkehren
      // So werden alle Kanten im selben Bezugssystem verteilt und überlappen nicht
      if (isReversed) {
        curvature = -curvature
      }
    }
    
    edges.push({
      source: e.source_node_uuid,
      target: e.target_node_uuid,
      type: e.fact_type || e.name || t('graph.relationship'),
      name: e.name || e.fact_type || t('graph.relationship'),
      curvature,
      isSelfLoop: false,
      pairIndex: currentIndex,
      pairTotal: totalCount,
      rawData: {
        ...e,
        source_name: nodeMap[e.source_node_uuid]?.name,
        target_name: nodeMap[e.target_node_uuid]?.name
      }
    })
  })
    
  // Color scale
  const colorMap = {}
  entityTypes.value.forEach(t => colorMap[t.name] = t.color)
  const getColor = (type) => colorMap[type] || 'var(--color-text-muted)'

  // Simulation - Knotenabstand dynamisch nach Kantenanzahl anpassen
  const simulation = d3.forceSimulation(nodes)
    .alphaMin(0.005)
    .force('link', d3.forceLink(edges).id(d => d.id).distance(d => {
      // Abstand dynamisch nach Kantenanzahl zwischen Knotenpaar anpassen
      // Basisabstand 150, pro zusätzlicher Kante 50 mehr
      const baseDistance = 150
      const edgeCount = d.pairTotal || 1
      return baseDistance + (edgeCount - 1) * 50
    }))
    .force('charge', d3.forceManyBody().strength(-400))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collide', d3.forceCollide().radius(d => {
      // Radius aus Beschriftungsbreite, damit Text nicht über Text liegt
      const labelLen = (d.name || '').length
      return Math.max(28, 12 + labelLen * 3.2)
    }).iterations(2))
    // Anziehungskraft zur Mitte hinzufügen, damit isolierte Knotengruppen zum Zentrum gravitieren
    .force('x', d3.forceX(width / 2).strength(0.04))
    .force('y', d3.forceY(height / 2).strength(0.04))
  
  currentSimulation = simulation

  const g = svg.append('g')
  
  // Zoom: Mausrad, Ein-Finger-Verschieben und Pinch-Zoom.
  zoomBehavior = d3.zoom().extent([[0, 0], [width, height]]).scaleExtent([0.15, 3.5]).on('zoom', (event) => {
    g.attr('transform', event.transform)
    currentZoomK = event.transform.k
    updateNodeLabelVisibility()
    updateEdgeLabelVisibility()
  })
  svg.call(zoomBehavior).style('touch-action', 'none')
  currentZoomK = 1
  nodeCountRef.value = nodes.length

  // Kanten - path-Element für Kurvenunterstützung verwenden
  const linkGroup = g.append('g').attr('class', 'links')
  
  // Kurvenpfad berechnen
  const getLinkPath = (d) => {
    const sx = d.source.x, sy = d.source.y
    const tx = d.target.x, ty = d.target.y
    
    // Selbstschleife erkennen
    if (d.isSelfLoop) {
      // Selbstschleife: Kreisbogen vom Knoten weg und zurück zeichnen
      const loopRadius = 30
      // Von der rechten Seite des Knotens starten und zurückkehren
      const x1 = sx + 8  // Startpunkt-Versatz
      const y1 = sy - 4
      const x2 = sx + 8  // Endpunkt-Versatz
      const y2 = sy + 4
      // Selbstschleife mit Kreisbogen zeichnen (sweep-flag=1 im Uhrzeigersinn)
      return `M${x1},${y1} A${loopRadius},${loopRadius} 0 1,1 ${x2},${y2}`
    }
    
    if (d.curvature === 0) {
      // Gerade Linie
      return `M${sx},${sy} L${tx},${ty}`
    }
    
    // Kurven-Kontrollpunkt berechnen - dynamisch nach Kantenanzahl und Abstand anpassen
    const dx = tx - sx, dy = ty - sy
    const dist = Math.sqrt(dx * dx + dy * dy)
    // Versatz senkrecht zur Verbindungslinie, proportional zur Distanz berechnet
    // Je mehr Kanten, desto größer der Versatzanteil
    const pairTotal = d.pairTotal || 1
    const offsetRatio = 0.25 + pairTotal * 0.05 // Basis 25%, pro zusätzlicher Kante 5% mehr
    const baseOffset = Math.max(35, dist * offsetRatio)
    const offsetX = -dy / dist * d.curvature * baseOffset
    const offsetY = dx / dist * d.curvature * baseOffset
    const cx = (sx + tx) / 2 + offsetX
    const cy = (sy + ty) / 2 + offsetY
    
    return `M${sx},${sy} Q${cx},${cy} ${tx},${ty}`
  }
  
  // Kurvenmittelpunkt berechnen (für Beschriftungspositionierung)
  const getLinkMidpoint = (d) => {
    const sx = d.source.x, sy = d.source.y
    const tx = d.target.x, ty = d.target.y
    
    // Selbstschleife erkennen
    if (d.isSelfLoop) {
      // Selbstschleifen-Beschriftung: oberhalb des Knotennamens, damit beide lesbar bleiben
      return { x: sx + 70, y: sy - 38 }
    }
    
    if (d.curvature === 0) {
      return { x: (sx + tx) / 2, y: (sy + ty) / 2 }
    }
    
    // Mittelpunkt der quadratischen Bézierkurve bei t=0.5
    const dx = tx - sx, dy = ty - sy
    const dist = Math.sqrt(dx * dx + dy * dy)
    const pairTotal = d.pairTotal || 1
    const offsetRatio = 0.25 + pairTotal * 0.05
    const baseOffset = Math.max(35, dist * offsetRatio)
    const offsetX = -dy / dist * d.curvature * baseOffset
    const offsetY = dx / dist * d.curvature * baseOffset
    const cx = (sx + tx) / 2 + offsetX
    const cy = (sy + ty) / 2 + offsetY
    
    // Quadratische Bézierkurven-Formel B(t) = (1-t)²P0 + 2(1-t)tP1 + t²P2, t=0.5
    const midX = 0.25 * sx + 0.5 * cx + 0.25 * tx
    const midY = 0.25 * sy + 0.5 * cy + 0.25 * ty
    
    return { x: midX, y: midY }
  }
  
  const link = linkGroup.selectAll('path')
    .data(edges)
    .enter().append('path')
    .attr('stroke', 'var(--color-border-strong)')
    .attr('stroke-width', 1.5)
    .attr('fill', 'none')
    .style('cursor', 'pointer')
    .on('click', (event, d) => {
      event.stopPropagation()
      // Stil der zuvor ausgewählten Kante zurücksetzen
      linkGroup.selectAll('path').attr('stroke', 'var(--color-border-strong)').attr('stroke-width', 1.5)
      linkLabelBg.attr('fill', 'var(--color-bg-surface-raised)')
      linkLabels.attr('fill', 'var(--color-text-secondary)')
      // Aktuell ausgewählte Kante hervorheben
      d3.select(event.target).attr('stroke', 'var(--color-info-text)').attr('stroke-width', 3)
      
      selectedItem.value = {
        type: 'edge',
        data: d.rawData
      }
    })

  // Kantenbeschriftung-Hintergrund (weißer Hintergrund für bessere Lesbarkeit)
  const linkLabelBg = linkGroup.selectAll('rect')
    .data(edges)
    .enter().append('rect')
    .attr('fill', 'var(--color-bg-surface-raised)')
    .attr('rx', 3)
    .attr('ry', 3)
    .style('cursor', 'pointer')
    .style('pointer-events', 'all')
    .style('display', 'none')
    .on('click', (event, d) => {
      event.stopPropagation()
      linkGroup.selectAll('path').attr('stroke', 'var(--color-border-strong)').attr('stroke-width', 1.5)
      linkLabelBg.attr('fill', 'var(--color-bg-surface-raised)')
      linkLabels.attr('fill', 'var(--color-text-secondary)')
      // Zugehörige Kante hervorheben
      link.filter(l => l === d).attr('stroke', 'var(--color-info-text)').attr('stroke-width', 3)
      d3.select(event.target).attr('fill', 'var(--color-info-bg)')

      selectedItem.value = {
        type: 'edge',
        data: d.rawData
      }
    })

  // Link labels – Halo, Anzeige ab Zoom 0.8 oder ausgewähltem Knoten
  const linkLabels = linkGroup.selectAll('text')
    .data(edges)
    .enter().append('text')
    .text(d => formatLabel(d.name, 'relation'))
    .attr('font-size', '11px')
    .attr('fill', 'var(--color-text-secondary)')
    .attr('text-anchor', 'middle')
    .attr('dominant-baseline', 'middle')
    .attr('stroke', 'var(--color-bg-canvas)')
    .attr('stroke-width', 3)
    .attr('paint-order', 'stroke')
    .style('cursor', 'pointer')
    .style('pointer-events', 'all')
    .style('font-family', 'var(--font-body)')
    .style('display', 'none')
    .on('click', (event, d) => {
      event.stopPropagation()
      linkGroup.selectAll('path').attr('stroke', 'var(--color-border-strong)').attr('stroke-width', 1.5)
      linkLabelBg.attr('fill', 'var(--color-bg-surface-raised)')
      linkLabels.attr('fill', 'var(--color-text-secondary)')
      // Zugehörige Kante hervorheben
      link.filter(l => l === d).attr('stroke', 'var(--color-info-text)').attr('stroke-width', 3)
      d3.select(event.target).attr('fill', 'var(--color-info-text)')
      
      selectedItem.value = {
        type: 'edge',
        data: d.rawData
      }
    })
  
  // Referenzen speichern für externe Sichtbarkeitssteuerung
  linkLabelsRef = linkLabels
  linkLabelBgRef = linkLabelBg

  // Nodes group
  const nodeGroup = g.append('g').attr('class', 'nodes')
  
  // Node circles
  const node = nodeGroup.selectAll('circle')
    .data(nodes)
    .enter().append('circle')
    .attr('r', 10)
    .attr('fill', d => getColor(d.type))
    .attr('stroke', 'var(--color-bg-surface-raised)')
    .attr('stroke-width', 2.5)
    .style('cursor', 'pointer')
    .call(d3.drag()
      .on('start', (event, d) => {
        // Nur Position merken, Simulation nicht neustarten (Klick von Drag unterscheiden)
        d.fx = d.x
        d.fy = d.y
        d._dragStartX = event.x
        d._dragStartY = event.y
        d._isDragging = false
      })
      .on('drag', (event, d) => {
        // Prüfen, ob wirklich gezogen wird (Bewegung über Schwellenwert)
        const dx = event.x - d._dragStartX
        const dy = event.y - d._dragStartY
        const distance = Math.sqrt(dx * dx + dy * dy)
        
        if (!d._isDragging && distance > 3) {
          // Erst beim ersten echten Ziehen die Simulation neustarten
          d._isDragging = true
          simulation.alphaTarget(0.3).restart()
        }
        
        if (d._isDragging) {
          d.fx = event.x
          d.fy = event.y
        }
      })
      .on('end', (event, d) => {
        // Simulation nur allmählich stoppen, wenn tatsächlich gezogen wurde
        if (d._isDragging) {
          simulation.alphaTarget(0)
        }
        d.fx = null
        d.fy = null
        d._isDragging = false
      })
    )
    .on('click', (event, d) => {
      event.stopPropagation()
      // Alle Knotenstile zurücksetzen
      node.attr('stroke', 'var(--color-bg-surface-raised)').attr('stroke-width', 2.5)
      linkGroup.selectAll('path').attr('stroke', 'var(--color-border-strong)').attr('stroke-width', 1.5)
      // Ausgewählten Knoten hervorheben
      d3.select(event.target).attr('stroke', 'var(--color-error-text)').attr('stroke-width', 4)
      // Mit diesem Knoten verbundene Kanten hervorheben
      link.filter(l => l.source.id === d.id || l.target.id === d.id)
        .attr('stroke', 'var(--color-error-text)')
        .attr('stroke-width', 2.5)
      
      selectedItem.value = {
        type: 'node',
        data: d.rawData,
        entityType: d.type,
        color: getColor(d.type)
      }
      updateNodeLabelVisibility()
    })
    .on('mouseenter', (event, d) => {
      if (!selectedItem.value || selectedItem.value.data?.uuid !== d.rawData.uuid) {
        d3.select(event.target).attr('stroke', 'var(--color-text-primary)').attr('stroke-width', 3)
      }
    })
    .on('mouseleave', (event, d) => {
      if (!selectedItem.value || selectedItem.value.data?.uuid !== d.rawData.uuid) {
        d3.select(event.target).attr('stroke', 'var(--color-bg-surface-raised)').attr('stroke-width', 2.5)
      }
    })

  // Node Labels – Halo gegen Überlappung mit Kanten/Knoten
  const nodeLabels = nodeGroup.selectAll('text')
    .data(nodes)
    .enter().append('text')
    .text(d => {
      const limit = window.innerWidth <= 768 ? 14 : 20
      return d.name.length > limit ? `${d.name.substring(0, limit)}…` : d.name
    })
    .attr('font-size', window.innerWidth <= 768 ? '12px' : '11px')
    .attr('fill', 'var(--color-text-primary)')
    .attr('font-weight', '500')
    .attr('dx', 14)
    .attr('dy', 4)
    .attr('stroke', 'var(--color-bg-canvas)')
    .attr('stroke-width', 3)
    .attr('paint-order', 'stroke')
    .style('pointer-events', 'none')
    .style('font-family', 'var(--font-body)')
  nodeLabelsRef = nodeLabels
  updateNodeLabelVisibility()
  updateEdgeLabelVisibility()

  let tickCount = 0
  simulation.on('tick', () => {
    tickCount += 1
    // Kurvenpfade aktualisieren
    link.attr('d', d => getLinkPath(d))
    
    // Kantenbeschriftungspositionen aktualisieren (ohne Rotation, horizontal besser lesbar)
    linkLabels.each(function(d) {
      const mid = getLinkMidpoint(d)
      d3.select(this)
        .attr('x', mid.x)
        .attr('y', mid.y)
        .attr('transform', '') // Rotation entfernen, horizontal halten
    })
    
    // Kantenbeschriftung-Hintergrund aktualisieren
    linkLabelBg.each(function(d, i) {
      const mid = getLinkMidpoint(d)
      const textEl = linkLabels.nodes()[i]
      const bbox = textEl.getBBox()
      d3.select(this)
        .attr('x', mid.x - bbox.width / 2 - 4)
        .attr('y', mid.y - bbox.height / 2 - 2)
        .attr('width', bbox.width + 8)
        .attr('height', bbox.height + 4)
        .attr('transform', '') // Rotation entfernen
    })

    node
      .attr('cx', d => d.x)
      .attr('cy', d => d.y)

    nodeLabels
      .attr('x', d => d.x)
      .attr('y', d => d.y)

    if (tickCount >= 300) simulation.stop()
  })
  simulation.on('end', () => zoomToFit(0.88))
  clearTimeout(fitTimer)
  fitTimer = setTimeout(() => zoomToFit(0.88), 450)
  
  // Klick auf leere Fläche schließt Detailbereich
  svg.on('click', () => {
    selectedItem.value = null
    node.attr('stroke', 'var(--color-bg-surface-raised)').attr('stroke-width', 2.5)
    linkGroup.selectAll('path').attr('stroke', 'var(--color-border-strong)').attr('stroke-width', 1.5)
    linkLabelBg.attr('fill', 'var(--color-bg-surface-raised)')
    linkLabels.attr('fill', 'var(--color-text-secondary)')
    updateNodeLabelVisibility()
  })
}

watch(selectedItem, () => {
  updateNodeLabelVisibility()
  updateEdgeLabelVisibility()
})

watch(() => props.graphData, () => {
  nextTick(renderGraph)
}, { deep: true })

watch(showEdgeLabels, () => updateEdgeLabelVisibility())

onMounted(() => {
  resizeObserver = new ResizeObserver((entries) => {
    const entry = entries[0]
    if (entry?.contentRect.width > 0 && entry.contentRect.height > 0) nextTick(renderGraph)
  })
  if (graphContainer.value) resizeObserver.observe(graphContainer.value)
})

onUnmounted(() => {
  resizeObserver?.disconnect()
  clearTimeout(fitTimer)
  if (currentSimulation) {
    currentSimulation.stop()
  }
})
</script>

<style scoped>
.graph-panel {
  position: relative;
  width: 100%;
  height: 100%;
  background-color: var(--color-bg-surface-subtle);
  background-image: radial-gradient(var(--color-border-strong) 1.5px, transparent 1.5px);
  background-size: 24px 24px;
  overflow: hidden;
}

.panel-header {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  padding: 16px 20px;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(to bottom, color-mix(in srgb, var(--color-text-primary) 12%, transparent), color-mix(in srgb, var(--color-text-primary) 12%, transparent));
  pointer-events: none;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  pointer-events: auto;
}

.header-tools {
  pointer-events: auto;
  display: flex;
  gap: 10px;
  align-items: center;
}

.tool-btn {
  height: 32px;
  padding: 0 12px;
  border: 1px solid var(--color-border-default);
  background: var(--color-bg-surface-raised);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  cursor: pointer;
  color: var(--color-text-secondary);
  transition: all 0.2s;
  box-shadow: 0 2px 4px color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  font-size: 13px;
}

.tool-btn:hover {
  background: var(--color-bg-surface-subtle);
  color: var(--color-text-primary);
  border-color: var(--color-border-strong);
}

.tool-btn .btn-text {
  font-size: 12px;
}

.icon-refresh.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

.graph-container {
  width: 100%;
  height: 100%;
}

.graph-view, .graph-svg {
  width: 100%;
  height: 100%;
  display: block;
}

.graph-state {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: var(--color-text-muted);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.2;
}

/* Entity Types Legend - Bottom Left */
.graph-legend {
  position: absolute;
  bottom: 24px;
  left: 24px;
  background: color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid var(--color-border-subtle);
  box-shadow: 0 4px 16px color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  z-index: 10;
}

.legend-title {
  display: block;
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: 10px;
  text-transform: none;
  letter-spacing: normal;
}

.legend-items {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 16px;
  max-width: 320px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-label {
  white-space: nowrap;
}

/* Edge Labels Toggle - Top Right */
.edge-labels-toggle {
  position: absolute;
  top: 60px;
  right: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--color-bg-surface-raised);
  padding: 8px 14px;
  border-radius: 20px;
  border: 1px solid var(--color-border-default);
  box-shadow: 0 2px 8px color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  z-index: 10;
}

.toggle-switch {
  position: relative;
  display: inline-block;
  width: 40px;
  height: 22px;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--color-border-default);
  border-radius: 22px;
  transition: 0.3s;
}

.slider:before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 3px;
  bottom: 3px;
  background: var(--color-bg-surface-raised);
  border-radius: 50%;
  transition: 0.3s;
}

input:checked + .slider {
  background-color: var(--color-info-text);
}

input:checked + .slider:before {
  transform: translateX(18px);
}

.toggle-label {
  font-size: 12px;
  color: var(--color-text-secondary);
}

/* Detail Panel - Right Side */
.detail-panel {
  position: absolute;
  top: 60px;
  right: 20px;
  width: 320px;
  max-height: calc(100% - 100px);
  background: var(--color-bg-surface-raised);
  border: 1px solid var(--color-border-subtle);
  border-radius: 10px;
  box-shadow: 0 8px 32px color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  overflow: hidden;
  font-family: var(--font-body);
  font-size: 13px;
  z-index: 20;
  display: flex;
  flex-direction: column;
}

.detail-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: var(--color-bg-surface-subtle);
  border-bottom: 1px solid var(--color-border-subtle);
  flex-shrink: 0;
}

.detail-title {
  font-weight: 600;
  color: var(--color-text-primary);
  font-size: 14px;
}

.detail-type-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
  margin-left: auto;
  margin-right: 12px;
}

.detail-close {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: var(--color-text-muted);
  line-height: 1;
  padding: 0;
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
  margin-bottom: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.detail-label {
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 500;
  min-width: 80px;
}

.detail-value {
  color: var(--color-text-primary);
  flex: 1;
  word-break: break-word;
}

.detail-value.uuid-text {
  font-family: var(--font-body);
  font-size: 11px;
  color: var(--color-text-secondary);
}

.detail-value.fact-text {
  line-height: 1.5;
  color: var(--color-text-secondary);
}

.detail-section {
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid var(--color-border-subtle);
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: 10px;
}

.properties-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.property-item {
  display: flex;
  gap: 8px;
}

.property-key {
  color: var(--color-text-muted);
  font-weight: 500;
  min-width: 90px;
}

.property-value {
  color: var(--color-text-primary);
  flex: 1;
}

.summary-text {
  line-height: 1.6;
  color: var(--color-text-secondary);
  font-size: 12px;
}

.labels-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.label-tag {
  display: inline-block;
  padding: 4px 12px;
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-default);
  border-radius: 16px;
  font-size: 11px;
  color: var(--color-text-secondary);
}

.episodes-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.episode-tag {
  display: inline-block;
  padding: 6px 10px;
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-default);
  border-radius: 6px;
  font-family: var(--font-body);
  font-size: 11px;
  color: var(--color-text-secondary);
  word-break: break-all;
}

/* Edge relation header */
.edge-relation-header {
  background: var(--color-bg-surface-subtle);
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
  line-height: 1.5;
  word-break: break-word;
}

/* Building hint */
.graph-building-hint {
  position: absolute;
  bottom: 160px; /* Moved up from 80px */
  left: 50%;
  transform: translateX(-50%);
  background: color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  backdrop-filter: blur(8px);
  color: var(--color-text-inverse);
  padding: 10px 20px;
  border-radius: 30px;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 4px 20px color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  font-weight: 500;
  letter-spacing: normal;
  z-index: 100;
}

.memory-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  animation: breathe 2s ease-in-out infinite;
}

.memory-icon {
  width: 18px;
  height: 18px;
  color: var(--color-success-text);
}

@keyframes breathe {
  0%, 100% { opacity: 0.7; transform: scale(1); filter: drop-shadow(0 0 2px color-mix(in srgb, var(--color-text-primary) 12%, transparent)); }
  50% { opacity: 1; transform: scale(1.15); filter: drop-shadow(0 0 8px color-mix(in srgb, var(--color-text-primary) 12%, transparent)); }
}

/* Hinweisstil nach Simulationsende */
.graph-building-hint.finished-hint {
  background: color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-text-primary) 12%, transparent);
}

.finished-hint .hint-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
}

.finished-hint .hint-icon {
  width: 18px;
  height: 18px;
  color: var(--color-text-inverse);
}

.finished-hint .hint-text {
  flex: 1;
  white-space: nowrap;
}

.hint-close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  background: color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  color: var(--color-text-inverse);
  transition: all 0.2s;
  margin-left: 8px;
  flex-shrink: 0;
}

.hint-close-btn:hover {
  background: color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  transform: scale(1.1);
}

/* Loading spinner */
.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-border-default);
  border-top-color: var(--color-info-text);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

/* Self-loop styles */
.self-loop-header {
  display: flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, var(--color-success-bg) 0%, var(--color-success-bg) 100%);
  border: 1px solid var(--color-success-border);
}

.self-loop-count {
  margin-left: auto;
  font-size: 11px;
  color: var(--color-text-secondary);
  background: color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  padding: 2px 8px;
  border-radius: 10px;
}

.self-loop-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.self-loop-item {
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-subtle);
  border-radius: 8px;
}

.self-loop-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: var(--color-bg-surface-subtle);
  cursor: pointer;
  transition: background 0.2s;
}

.self-loop-item-header:hover {
  background: var(--color-border-subtle);
}

.self-loop-item.expanded .self-loop-item-header {
  background: var(--color-border-default);
}

.self-loop-index {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
  background: var(--color-border-default);
  padding: 2px 6px;
  border-radius: 4px;
}

.self-loop-name {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-primary);
  flex: 1;
}

.self-loop-toggle {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-muted);
  background: var(--color-border-default);
  border-radius: 4px;
  transition: all 0.2s;
}

.self-loop-item.expanded .self-loop-toggle {
  background: var(--color-border-strong);
  color: var(--color-text-secondary);
}

.self-loop-item-content {
  padding: 12px;
  border-top: 1px solid var(--color-border-subtle);
}

.self-loop-item-content .detail-row {
  margin-bottom: 8px;
}

.self-loop-item-content .detail-label {
  font-size: 11px;
  min-width: 60px;
}

.self-loop-item-content .detail-value {
  font-size: 12px;
}

.self-loop-episodes {
  margin-top: 8px;
}

.episodes-list.compact {
  flex-direction: row;
  flex-wrap: wrap;
  gap: 4px;
}

.episode-tag.small {
  padding: 3px 6px;
  font-size: 11px;
}
/* Responsiver, überlappungsfreier Graphkopf */
.graph-panel {
  background-color: var(--color-bg-canvas);
  background-image: radial-gradient(color-mix(in srgb, var(--color-border-strong) 20%, transparent) 1px, transparent 1px);
  background-size: 28px 28px;
}
.panel-header {
  z-index: 15;
  padding: 12px 16px;
  background: color-mix(in srgb, var(--color-bg-canvas) 88%, transparent);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--color-border-subtle);
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
  pointer-events: auto;
}
.panel-header__row-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-width: 0;
}
.panel-header__row-toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}
.panel-title { margin: 0; font-size: 15px; font-weight: 700; white-space: nowrap; }
.header-tools {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 8px;
  justify-content: flex-end;
}
.tool-btn { min-width: 44px; min-height: 44px; height: 44px; border-radius: var(--radius-md); font-family: var(--font-body); font-weight: 600; }
.legend-toggle-btn {
  min-height: 44px;
  min-width: 44px;
  padding: 0 12px;
  border-radius: var(--radius-full);
  border: 1px solid var(--color-border-default);
  background: var(--color-bg-surface-raised);
  color: var(--color-text-secondary);
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.legend-toggle-btn.is-active { border-color: var(--color-border-strong); color: var(--color-text-primary); }
.legend-toggle-btn__dot { width: 7px; height: 7px; border-radius: 50%; background: var(--color-brand-primary); }
.edge-labels-control { display: flex; align-items: center; flex-shrink: 0; }
.toggle-switch-compact { display: inline-flex; align-items: center; gap: 8px; min-height: 44px; cursor: pointer; user-select: none; }
.toggle-switch-compact input { position: absolute; opacity: 0; width: 0; height: 0; }
.toggle-switch-compact .slider { width: 38px; height: 22px; border-radius: var(--radius-full); background: var(--color-border-strong); position: relative; transition: background-color var(--transition-fast); flex-shrink: 0; }
.toggle-switch-compact .slider::before { content: ""; position: absolute; top: 3px; left: 3px; width: 16px; height: 16px; border-radius: 50%; background: var(--color-bg-surface-raised); transition: transform var(--transition-fast); box-shadow: var(--shadow-sm); }
.toggle-switch-compact input:checked + .slider { background: var(--color-brand-primary); }
.toggle-switch-compact input:checked + .slider::before { transform: translateX(16px); }
.toggle-switch-compact .toggle-label { font-size: 12px; font-weight: 600; color: var(--color-text-secondary); white-space: nowrap; }
.graph-building-hint,
.graph-building-hint.finished-hint {
  top: 116px;
  bottom: auto;
  background: var(--color-bg-surface-raised);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border-default);
  box-shadow: var(--shadow-md);
  padding: 6px 14px;
  border-radius: var(--radius-full);
  max-width: 90%;
  text-align: center;
  z-index: 12;
}
.finished-hint .hint-icon { color: var(--color-text-primary); }
.hint-close-btn { color: var(--color-text-primary); background: var(--color-bg-surface-subtle); min-width: 44px; min-height: 44px; }
.graph-legend {
  display: none;
  background: var(--color-bg-surface-raised);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  border: 1px solid var(--color-border-subtle);
}
.graph-legend.is-open { display: block; }
.legend-title { color: var(--color-text-secondary); font-size: 12px; font-weight: 700; margin: 0; }
.legend-header { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 8px; }
.legend-close-btn {
  border: 0;
  background: transparent;
  color: var(--color-text-muted);
  font-size: 20px;
  min-width: 44px;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.detail-close { min-width: 44px; min-height: 44px; }

/* Mobile-first polish */
button, [role="button"] { min-height: var(--touch-target-min); }
h1, h2, h3, h4, h5, h6, .panel-title { font-family: var(--font-heading); }
.detail-value, .property-value, .relation-text { overflow-wrap: anywhere; word-break: break-word; }
@media (max-width: 768px) {
  .panel-header { padding: 10px 12px; }
  .panel-header__row-toolbar { width: 100%; justify-content: flex-end; }
  .header-tools { gap: 6px; flex-wrap: wrap; }
  .tool-btn { min-width: 44px; height: 44px; padding-inline: 10px; }
  .desktop-only { display: none; }
  .toggle-switch-compact { gap: 6px; }
  .toggle-switch-compact .toggle-label { max-width: 72px; line-height: 1.15; white-space: normal; }
  .graph-building-hint { top: 112px; width: max-content; }
  .graph-legend { left: 8px; right: 8px; bottom: calc(64px + env(safe-area-inset-bottom, 0px)); max-width: none; }
  .detail-panel { top: auto; inset-inline: 8px; bottom: calc(8px + env(safe-area-inset-bottom, 0px)); width: auto; max-width: none; max-height: 62%; border-radius: var(--radius-xl) var(--radius-xl) var(--radius-md) var(--radius-md); }
  .detail-panel-header { min-height: 52px; }
  .graph-svg { touch-action: none; }
}
@media (min-width: 1024px) {
  .panel-header {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    flex-wrap: nowrap;
    padding: 10px 20px;
    gap: 12px;
  }
  .panel-header__row-top { flex: 1 1 auto; min-width: 0; }
  .panel-header__row-toolbar { flex: 0 0 auto; flex-wrap: nowrap; }
  .header-tools { flex-wrap: nowrap; }
  .graph-building-hint { top: 72px; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; transition-duration: .01ms !important; }
}
</style>
