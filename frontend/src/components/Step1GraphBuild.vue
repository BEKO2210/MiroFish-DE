<template>
  <div class="workbench-panel">
    <div class="scroll-container">
      <!-- Step 01: Ontology -->
      <div class="step-card" :class="{ 'active': currentPhase === 0, 'completed': currentPhase > 0 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">01</span>
            <span class="step-title">{{ $t('step1.ontologieGenerierung') }}</span>
          </div>
          <div class="step-status">
            <span v-if="currentPhase > 0" class="badge success">{{ $t('common.completed') }}</span>
            <span v-else-if="currentPhase === 0" class="badge processing">{{ $t('common.generating') }}</span>
            <span v-else class="badge pending">{{ $t('common.pending') }}</span>
          </div>
        </div>
        
        <div class="card-content">
          <p class="description">
            {{ $t('step1.llmAnalysiertDokumenteninhaltUndSimulationsanforderungenExtrahiertRealit') }}
          </p>

          <!-- Loading / Progress -->
          <StepActivity
            v-if="currentPhase === 0 && (ontologyProgress || activityPollAt)"
            class="step-activity-slot"
            :active="true"
            :label="$t('step1.ontologieGenerierung')"
            :detail="ontologyProgress?.message || $t('step1.dokumentWirdAnalysiert')"
            :last-poll-at="activityPollAt"
            :server-updated-at="activityUpdatedAt"
            :error="activityError"
            :next-hint="activityError ? $t('activity.errorNext') : ''"
          />

          <!-- Detail Overlay -->
          <div v-if="selectedOntologyItem" class="ontology-detail-overlay">
            <div class="detail-header">
               <div class="detail-title-group">
                  <span class="detail-type-badge">{{ selectedOntologyItem.itemType === 'entity' ? $t('step1.entity') : $t('step1.relationship') }}</span>
                  <span class="detail-name">{{ selectedOntologyItem.itemType === 'entity' ? formatLabel(selectedOntologyItem.name) : formatLabel(selectedOntologyItem.name, 'relation') }}</span>
               </div>
               <button class="close-btn" @click="selectedOntologyItem = null">×</button>
            </div>
            <div class="detail-body">
               <div class="detail-desc">{{ selectedOntologyItem.description }}</div>
               
               <!-- Attributes -->
               <div class="detail-section" v-if="selectedOntologyItem.attributes?.length">
                  <span class="section-label">{{ $t('step1.attribute') }}</span>
                  <div class="attr-list">
                     <div v-for="attr in selectedOntologyItem.attributes" :key="attr.name" class="attr-item">
                        <span class="attr-name">{{ attr.name }}</span>
                        <span class="attr-type">({{ attr.type }})</span>
                        <span class="attr-desc">{{ attr.description }}</span>
                     </div>
                  </div>
               </div>

               <!-- Examples (Entity) -->
               <div class="detail-section" v-if="selectedOntologyItem.examples?.length">
                  <span class="section-label">{{ $t('step1.beispiele') }}</span>
                  <div class="example-list">
                     <span v-for="ex in selectedOntologyItem.examples" :key="ex" class="example-tag">{{ ex }}</span>
                  </div>
               </div>

               <!-- Source/Target (Relation) -->
               <div class="detail-section" v-if="selectedOntologyItem.source_targets?.length">
                  <span class="section-label">{{ $t('step1.verbindungen') }}</span>
                  <div class="conn-list">
                     <div v-for="(conn, idx) in selectedOntologyItem.source_targets" :key="idx" class="conn-item">
                        <span class="conn-node">{{ formatLabel(conn.source) }}</span>
                        <span class="conn-arrow">→</span>
                        <span class="conn-node">{{ formatLabel(conn.target) }}</span>
                     </div>
                  </div>
               </div>
            </div>
          </div>

          <!-- Generated Entity Tags -->
          <div v-if="projectData?.ontology?.entity_types" class="tags-container" :class="{ 'dimmed': selectedOntologyItem }">
            <span class="tag-label">{{ $t('step1.generierteEntitatstypen') }}</span>
            <div class="tags-list">
              <span 
                v-for="entity in projectData.ontology.entity_types" 
                :key="entity.name" 
                class="entity-tag clickable"
                @click="selectOntologyItem(entity, 'entity')"
              >
                {{ formatLabel(entity.name) }}
              </span>
            </div>
          </div>

          <!-- Generated Relation Tags -->
          <div v-if="projectData?.ontology?.edge_types" class="tags-container" :class="{ 'dimmed': selectedOntologyItem }">
            <span class="tag-label">{{ $t('step1.generierteBeziehungstypen') }}</span>
            <div class="tags-list">
              <span 
                v-for="rel in projectData.ontology.edge_types" 
                :key="rel.name" 
                class="entity-tag clickable"
                @click="selectOntologyItem(rel, 'relation')"
              >
                {{ formatLabel(rel.name, 'relation') }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 02: Graph Build -->
      <div class="step-card" :class="{ 'active': currentPhase === 1, 'completed': currentPhase > 1 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">02</span>
            <span class="step-title">{{ $t('step1.graphragAufbau') }}</span>
          </div>
          <div class="step-status">
            <span v-if="currentPhase > 1" class="badge success">{{ $t('common.completed') }}</span>
            <span v-else-if="currentPhase === 1" class="badge processing">{{ buildProgress?.progress || 0 }}%</span>
            <span v-else class="badge pending">{{ $t('common.pending') }}</span>
          </div>
        </div>

        <div class="card-content">
          <p class="description">
            {{ $t('step1.basierendAufDerGeneriertenOntologieWerdenDokumente') }}
          </p>
          
          <StepActivity
            v-if="currentPhase === 1"
            class="step-activity-slot"
            :active="true"
            :label="$t('step1.graphragAufbau')"
            :detail="graphActivityDetail"
            :last-poll-at="activityPollAt"
            :server-updated-at="activityUpdatedAt"
            :error="activityError"
            :next-hint="activityError ? $t('activity.errorNext') : ''"
          />

          <!-- Stats Cards -->
          <div class="stats-grid">
            <div class="stat-card">
              <span class="stat-value">{{ graphStats.nodes }}</span>
              <span class="stat-label">{{ $t('step1.entitatsknoten') }}</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">{{ graphStats.edges }}</span>
              <span class="stat-label">{{ $t('step1.beziehungskanten') }}</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">{{ graphStats.types }}</span>
              <span class="stat-label">{{ $t('step1.schemaTypen') }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 03: Complete -->
      <div class="step-card" :class="{ 'active': currentPhase === 2, 'completed': currentPhase >= 2 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">03</span>
            <span class="step-title">{{ $t('step1.erstellungAbgeschlossen') }}</span>
          </div>
          <div class="step-status">
            <span v-if="currentPhase >= 2" class="badge success">{{ $t('common.completed') }}</span>
          </div>
        </div>
        
        <div class="card-content">
          <p class="description">{{ $t('step1.grapherstellungAbgeschlossenBitteFahrenSieMitDem') }}</p>
          <button 
            class="action-btn" 
            :disabled="currentPhase < 2 || creatingSimulation"
            @click="handleEnterEnvSetup"
          >
            <span v-if="creatingSimulation" class="spinner-sm"></span>
            {{ creatingSimulation ? $t('step1.wirdErstellt') : $t('step1.toEnvironmentSetup') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Bottom Info / Logs – Desktop eingeklappt, Handy via App.vue ausgeblendet -->
    <details class="system-logs">
      <summary>{{ $t('common.showProtocol') }}</summary>
      <div class="log-content" ref="logContent">
        <div class="log-line" v-for="(log, idx) in systemLogs" :key="idx">
          <span class="log-time">{{ log.time }}</span>
          <span class="log-msg">{{ log.msg }}</span>
        </div>
      </div>
    </details>
    <MobileStickyBar
      :primary-label="$t('step1.toEnvironmentSetup')"
      :primary-disabled="currentPhase < 2"
      :primary-loading="creatingSimulation"
      @primary-click="handleEnterEnvSetup"
    />
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { createSimulation } from '../api/simulation'
import MobileStickyBar from './MobileStickyBar.vue'
import StepActivity from './StepActivity.vue'
import { formatLabel } from '../utils/labels.js'

const { t } = useI18n()

const router = useRouter()

const props = defineProps({
  currentPhase: { type: Number, default: 0 },
  projectData: Object,
  ontologyProgress: Object,
  buildProgress: Object,
  graphData: Object,
  systemLogs: { type: Array, default: () => [] },
  activityPollAt: { type: Number, default: 0 },
  activityUpdatedAt: { type: String, default: null },
  activityError: { type: String, default: '' },
})

defineEmits(['next-step'])

const selectedOntologyItem = ref(null)
const logContent = ref(null)
const creatingSimulation = ref(false)

// Umgebungseinrichtung betreten - Simulation erstellen und weiterleiten
const handleEnterEnvSetup = async () => {
  if (!props.projectData?.project_id || !props.projectData?.graph_id) {
    console.error(t('step1.projektOderGraphinformationenFehlen'))
    return
  }
  
  creatingSimulation.value = true
  
  try {
    const res = await createSimulation({
      project_id: props.projectData.project_id,
      graph_id: props.projectData.graph_id,
      enable_twitter: true,
      enable_reddit: true
    })
    
    if (res.success && res.data?.simulation_id) {
      // Zur Simulationsseite weiterleiten
      router.push({
        name: 'Simulation',
        params: { simulationId: res.data.simulation_id }
      })
    } else {
      console.error(t('step1.erstellungDerSimulationFehlgeschlagen'), res.error)
      alert(t('step1.erstellungDerSimulationFehlgeschlagen2') + (res.error || t('common.unknownError')))
    }
  } catch (err) {
    console.error(t('step1.ausnahmeBeiDerSimulationserstellung'), err)
    alert(t('step1.ausnahmeBeiDerSimulationserstellung2') + err.message)
  } finally {
    creatingSimulation.value = false
  }
}

const selectOntologyItem = (item, type) => {
  selectedOntologyItem.value = { ...item, itemType: type }
}

const graphActivityDetail = computed(() => {
  const msg = props.buildProgress?.message || t('common.processingEllipsis')
  const pct = props.buildProgress?.progress
  if (pct == null) return msg
  return `${msg} (${Math.round(pct)} %)`
})

const graphStats = computed(() => {
  const nodes = props.graphData?.node_count || props.graphData?.nodes?.length || 0
  const edges = props.graphData?.edge_count || props.graphData?.edges?.length || 0
  const types = props.projectData?.ontology?.entity_types?.length || 0
  return { nodes, edges, types }
})

const formatDate = (dateStr) => {
  if (!dateStr) return '--:--:--'
  const d = new Date(dateStr)
  return d.toLocaleTimeString('de-DE', { hour12: false }) + '.' + d.getMilliseconds()
}

// Protokolle automatisch scrollen
watch(() => props.systemLogs.length, () => {
  nextTick(() => {
    if (logContent.value) {
      logContent.value.scrollTop = logContent.value.scrollHeight
    }
  })
})
</script>

<style scoped>
.workbench-panel {
  height: 100%;
  background-color: var(--color-bg-surface-subtle);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.scroll-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.step-card {
  background: var(--color-bg-surface-raised);
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  border: 1px solid var(--color-border-subtle);
  transition: all 0.3s ease;
  position: relative; /* For absolute overlay */
}

.step-card.active {
  border-color: var(--color-brand-primary);
  box-shadow: 0 4px 12px color-mix(in srgb, var(--color-brand-primary) 8%, transparent);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.step-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.step-num {
  font-family: var(--font-body);
  font-size: 20px;
  font-weight: 700;
  color: var(--color-border-default);
}

.step-card.active .step-num,
.step-card.completed .step-num {
  color: var(--color-text-primary);
}

.step-title {
  font-weight: 600;
  font-size: 14px;
  letter-spacing: normal;
}

.badge {
  font-size: 10px;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
  text-transform: none;
}

.badge.success { background: var(--color-success-bg); color: var(--color-success-text); }
.badge.processing { background: var(--color-brand-primary); color: var(--color-text-inverse); }
.badge.accent { background: var(--color-brand-primary); color: var(--color-text-inverse); }
.badge.pending { background: var(--color-bg-surface-subtle); color: var(--color-text-muted); }

.api-note {
  font-family: var(--font-body);
  font-size: 10px;
  color: var(--color-text-muted);
  margin-bottom: 8px;
}

.description {
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.5;
  margin-bottom: 16px;
}

/* Step 01 Tags */
.tags-container {
  margin-top: 12px;
  transition: opacity 0.3s;
}

.tags-container.dimmed {
    opacity: 0.3;
    pointer-events: none;
}

.tag-label {
  display: block;
  font-size: 10px;
  color: var(--color-text-muted);
  margin-bottom: 8px;
  font-weight: 600;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.entity-tag {
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-subtle);
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 11px;
  color: var(--color-text-primary);
  font-family: var(--font-body);
  transition: all 0.2s;
}

.entity-tag.clickable {
    cursor: pointer;
}

.entity-tag.clickable:hover {
    background: var(--color-border-default);
    border-color: var(--color-border-strong);
}

/* Ontology Detail Overlay */
.ontology-detail-overlay {
    position: absolute;
    top: 60px; /* Below header roughly */
    left: 20px;
    right: 20px;
    bottom: 20px;
    background: color-mix(in srgb, var(--color-text-primary) 12%, transparent);
    backdrop-filter: blur(4px);
    z-index: 10;
    border: 1px solid var(--color-border-subtle);
    box-shadow: 0 4px 20px color-mix(in srgb, var(--color-text-primary) 12%, transparent);
    border-radius: 6px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }

.detail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid var(--color-border-subtle);
    background: var(--color-bg-surface-subtle);
}

.detail-title-group {
    display: flex;
    align-items: center;
    gap: 8px;
}

.detail-type-badge {
    font-size: 9px;
    font-weight: 700;
    color: var(--color-text-inverse);
    background: var(--color-text-primary);
    padding: 2px 6px;
    border-radius: 2px;
    text-transform: none;
}

.detail-name {
    font-size: 14px;
    font-weight: 700;
    font-family: var(--font-body);
}

.close-btn {
    background: none;
    border: none;
    font-size: 18px;
    color: var(--color-text-muted);
    cursor: pointer;
    line-height: 1;
}

.close-btn:hover {
    color: var(--color-text-primary);
}

.detail-body {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
}

.detail-desc {
    font-size: 12px;
    color: var(--color-text-secondary);
    line-height: 1.5;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px dashed var(--color-border-subtle);
}

.detail-section {
    margin-bottom: 16px;
}

.section-label {
    display: block;
    font-size: 10px;
    font-weight: 600;
    color: var(--color-text-muted);
    margin-bottom: 8px;
}

.attr-list, .conn-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.attr-item {
    font-size: 11px;
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    align-items: baseline;
    padding: 4px;
    background: var(--color-bg-surface-subtle);
    border-radius: 4px;
}

.attr-name {
    font-family: var(--font-body);
    font-weight: 600;
    color: var(--color-text-primary);
}

.attr-type {
    color: var(--color-text-muted);
    font-size: 10px;
}

.attr-desc {
    color: var(--color-text-secondary);
    flex: 1;
    min-width: 150px;
}

.example-list {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}

.example-tag {
    font-size: 11px;
    background: var(--color-bg-surface-raised);
    border: 1px solid var(--color-border-default);
    padding: 3px 8px;
    border-radius: 12px;
    color: var(--color-text-secondary);
}

.conn-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 11px;
    padding: 6px;
    background: var(--color-bg-surface-subtle);
    border-radius: 4px;
    font-family: var(--font-body);
}

.conn-node {
    font-weight: 600;
    color: var(--color-text-primary);
}

.conn-arrow {
    color: var(--color-border-strong);
}

/* Step 02 Stats */
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12px;
  background: var(--color-bg-surface-subtle);
  padding: 16px;
  border-radius: 6px;
}

.stat-card {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text-primary);
  font-family: var(--font-body);
}

.stat-label {
  font-size: 9px;
  color: var(--color-text-muted);
  text-transform: none;
  margin-top: 4px;
  display: block;
}

/* Step 03 Button */
.action-btn {
  width: 100%;
  background: var(--color-text-primary);
  color: var(--color-text-inverse);
  border: none;
  padding: 14px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.action-btn:hover:not(:disabled) {
  opacity: 0.8;
}

.action-btn:disabled {
  background: var(--color-border-strong);
  cursor: not-allowed;
}

.step-activity-slot {
  margin-bottom: 12px;
}
.progress-section {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: var(--color-brand-primary);
  margin-bottom: 12px;
}

.spinner-sm {
  width: 14px;
  height: 14px;
  border: 2px solid var(--color-warning-border);
  border-top-color: var(--color-brand-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* System Logs – dezente Token-Zeile, eingeklappt */
.system-logs {
  background: var(--color-bg-surface-subtle);
  color: var(--color-text-secondary);
  padding: 8px 16px;
  font-family: var(--font-body);
  border-top: 1px solid var(--color-border-subtle);
  flex-shrink: 0;
}
.system-logs > summary {
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
  list-style: none;
  min-height: 32px;
  display: flex;
  align-items: center;
}
.system-logs > summary::-webkit-details-marker { display: none; }
.system-logs[open] { padding-bottom: 12px; }
.system-logs[open] > summary {
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--color-border-subtle);
}

.log-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  height: 80px;
  overflow-y: auto;
  padding-right: 4px;
}

.log-content::-webkit-scrollbar {
  width: 4px;
}

.log-content::-webkit-scrollbar-thumb {
  background: var(--color-border-strong);
  border-radius: 2px;
}

.log-line {
  font-size: 11px;
  display: flex;
  gap: 12px;
  line-height: 1.5;
}

.log-time {
  color: var(--color-text-secondary);
  min-width: 75px;
}

.log-msg {
  color: var(--color-border-strong);
  word-break: break-all;
}
/* Mobile-first polish */
button, [role="button"], input, select, textarea { min-height: var(--touch-target-min); }
h1, h2, h3, h4, h5, h6, .step-title { font-family: var(--font-heading); }
.workbench-panel, .scroll-container, .step-card { min-width: 0; }
.step-card, .description, .log-msg, .detail-value { overflow-wrap: anywhere; }
@media (max-width: 768px) {
  .workbench-panel,
  .scroll-container {
    height: auto;
    overflow: visible;
  }
  .step-card:last-child .action-btn { display: none; }
  .scroll-container { padding: 16px 16px calc(64px + 58px + env(safe-area-inset-bottom, 0px)); gap: 16px; }
  .step-card { width: 100%; padding: 16px; border-radius: var(--radius-lg); }
  .card-header, .step-info { align-items: flex-start; }
  .card-header { gap: 12px; }
  .ontology-detail-overlay { inset: 52px 8px 8px; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; transition-duration: .01ms !important; }
}
</style>
