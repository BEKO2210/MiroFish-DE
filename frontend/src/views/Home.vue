<template>
  <div class="home-container">
    <!-- Top Navigation -->
    <nav class="navbar">
      <div class="nav-brand">MIROFISH</div>
      <div class="nav-links">
        <a href="https://github.com/BEKO2210/MiroFish-DE" target="_blank" class="github-link">
          GitHub besuchen <span class="arrow">↗</span>
        </a>
      </div>
    </nav>

    <div class="main-content">
      <!-- Hero Section -->
      <section class="hero-section">
        <div class="hero-left">
          <div class="tag-row">
            <span class="orange-tag">Elegante universelle Schwarm-Intelligenz-Engine</span>
            <span class="version-text">/ v0.1-Preview</span>
          </div>
          
          <h1 class="main-title">
            Lade beliebigen Bericht hoch<br>
            <span class="gradient-text">Erkenne die Zukunft sofort</span>
            <br>
            <span class="gradient-text">MiroFish ist jetzt auf Deutsch verfügbar.</span>
          </h1>
          
          <div class="hero-desc">
            <p>
              Selbst mit nur einem Text kann <span class="highlight-bold">MiroFish</span> basierend auf den darin enthaltenen Realitäts-Samen automatisch eine parallele Welt mit bis zu <span class="highlight-orange">Millionen Agenten</span> generieren. Durch die Gott-Perspektive können Variablen injiziert werden, um in komplexen Gruppeninteraktionen <span class="highlight-code">"lokal optimale Lösungen"</span> in dynamischen Umgebungen zu finden.
            </p>
            <p class="slogan-text">
              Lass die Zukunft in der Agenten-Gruppe vorausspielen, lass Entscheidungen nach hunderten Kämpfen triumphieren<span class="blinking-cursor">_</span>
            </p>
          </div>
           
          <div class="decoration-square"></div>
        </div>
        
        <div class="hero-right">
          <!-- Logo Area -->
          <div class="logo-container">
            <img src="../assets/logo/MiroFish_logo_left.jpeg" alt="MiroFish Logo" class="hero-logo" />
          </div>
          
          <button class="scroll-down-btn" @click="scrollToBottom">
            ↓
          </button>
        </div>
      </section>

      <!-- Dashboard Section -->
      <section class="dashboard-section">
        <!-- Left Panel: Status & Steps -->
        <div class="left-panel">
          <div class="panel-header">
            <span class="status-dot">■</span> Systemstatus
          </div>
          
          <h2 class="section-title">Bereit</h2>
          <p class="section-desc">
            Vorhersage-Engine im Standby. Lade unstrukturierte Daten hoch, um die Simulationssequenz zu initialisieren.
          </p>
          
          <!-- Metrics Cards -->
          <div class="metrics-row">
            <div class="metric-card">
              <div class="metric-value">Kostengünstig</div>
              <div class="metric-label">Durchschnittlich 5$/Simulation</div>
            </div>
            <div class="metric-card">
              <div class="metric-value">Hochverfügbar</div>
              <div class="metric-label">Bis zu Millionen Agenten</div>
            </div>
          </div>

          <!-- Workflow Steps -->
          <div class="steps-container">
            <div class="steps-header">
               <span class="diamond-icon">◇</span> Workflow-Sequenz
            </div>
            <div class="workflow-list">
              <div class="workflow-item">
                <span class="step-num">01</span>
                <div class="step-info">
                  <div class="step-title">Graphen-Aufbau</div>
                  <div class="step-desc">Realitäts-Samen-Extraktion & Individuen-/Gruppen-Gedächtnis-Injektion & GraphRAG-Aufbau</div>
                </div>
              </div>
              <div class="workflow-item">
                <span class="step-num">02</span>
                <div class="step-info">
                  <div class="step-title">Umgebungsaufbau</div>
                  <div class="step-desc">Entitätsbeziehungs-Extraktion & Charakter-Generierung & Umgebungskonfiguration</div>
                </div>
              </div>
              <div class="workflow-item">
                <span class="step-num">03</span>
                <div class="step-info">
                  <div class="step-title">Simulation starten</div>
                  <div class="step-desc">Duale Plattform-Parallel-Simulation & automatische Vorhersagebedarfsanalyse</div>
                </div>
              </div>
              <div class="workflow-item">
                <span class="step-num">04</span>
                <div class="step-info">
                  <div class="step-title">Berichtsgenerierung</div>
                  <div class="step-desc">ReportAgent mit reichhaltigem Toolset für tiefe Interaktion</div>
                </div>
              </div>
              <div class="workflow-item">
                <span class="step-num">05</span>
                <div class="step-info">
                  <div class="step-title">Tiefe Interaktion</div>
                  <div class="step-desc">Gespräch mit beliebiger Person in der simulierten Welt & Dialog mit ReportAgent</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Panel: Interactive Console -->
        <div class="right-panel">
          <div class="console-box">
            <!-- Upload Area -->
            <div class="console-section">
              <div class="console-header">
                <span class="console-label">01 / Realitäts-Samen</span>
                <span class="console-meta">Unterstützt: PDF, MD, TXT</span>
              </div>
              
              <div 
                class="upload-zone"
                :class="{ 'drag-over': isDragOver, 'has-files': files.length > 0 }"
                @dragover.prevent="handleDragOver"
                @dragleave.prevent="handleDragLeave"
                @drop.prevent="handleDrop"
                @click="triggerFileInput"
              >
                <input
                  ref="fileInput"
                  type="file"
                  multiple
                  accept=".pdf,.md,.txt"
                  @change="handleFileSelect"
                  style="display: none"
                  :disabled="loading"
                />
                
                <div v-if="files.length === 0" class="upload-placeholder">
                  <div class="upload-icon">↑</div>
                  <div class="upload-title">Dateien hier ablegen</div>
                  <div class="upload-hint">oder klicke zum Durchsuchen</div>
                </div>
                
                <div v-else class="file-list">
                  <div v-for="(file, index) in files" :key="index" class="file-item">
                    <span class="file-icon">📄</span>
                    <span class="file-name">{{ file.name }}</span>
                    <button @click.stop="removeFile(index)" class="remove-btn">×</button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Divider -->
            <div class="console-divider">
              <span>Eingabeparameter</span>
            </div>

            <!-- Input Area -->
            <div class="console-section">
              <div class="console-header">
                <span class="console-label">>_ 02 / Simulations-Prompt</span>
              </div>
              <div class="input-wrapper">
                <textarea
                  v-model="formData.simulationRequirement"
                  class="code-input"
                  placeholder="// Beschreibe Simulations- oder Vorhersagebedarf in natürlicher Sprache (z.B.: Wie würde die Öffentlichkeit reagieren, wenn Universität X eine bestimmte Entscheidung trifft?)"
                  rows="6"
                  :disabled="loading"
                ></textarea>
                <div class="model-badge">Engine: MiroFish-V1.0</div>
              </div>
            </div>

            <!-- Start Button -->
            <div class="console-section btn-section">
              <button 
                class="start-engine-btn"
                @click="startSimulation"
                :disabled="!canSubmit || loading"
              >
                <span v-if="!loading">Engine starten</span>
                <span v-else>Initialisiere...</span>
                <span class="btn-arrow">→</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- History Database -->
      <HistoryDatabase />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import HistoryDatabase from '../components/HistoryDatabase.vue'

const router = useRouter()

// Form data
const formData = ref({
  simulationRequirement: ''
})

// File list
const files = ref([])

// State
const loading = ref(false)
const error = ref('')
const isDragOver = ref(false)

// File input ref
const fileInput = ref(null)

// Computed: can submit
const canSubmit = computed(() => {
  return formData.value.simulationRequirement.trim() !== '' && files.value.length > 0
})

// Trigger file selection
const triggerFileInput = () => {
  if (!loading.value) {
    fileInput.value?.click()
  }
}

// Handle file selection
const handleFileSelect = (event) => {
  const selectedFiles = Array.from(event.target.files)
  addFiles(selectedFiles)
}

// Handle drag events
const handleDragOver = (e) => {
  if (!loading.value) {
    isDragOver.value = true
  }
}

const handleDragLeave = (e) => {
  isDragOver.value = false
}

const handleDrop = (e) => {
  isDragOver.value = false
  if (loading.value) return
  
  const droppedFiles = Array.from(e.dataTransfer.files)
  addFiles(droppedFiles)
}

// Add files
const addFiles = (newFiles) => {
  const validFiles = newFiles.filter(file => {
    const ext = file.name.split('.').pop().toLowerCase()
    return ['pdf', 'md', 'txt'].includes(ext)
  })
  files.value.push(...validFiles)
}

// Remove file
const removeFile = (index) => {
  files.value.splice(index, 1)
}

// Scroll to bottom
const scrollToBottom = () => {
  window.scrollTo({
    top: document.body.scrollHeight,
    behavior: 'smooth'
  })
}

// Start simulation
const startSimulation = () => {
  if (!canSubmit.value || loading.value) return
  
  import('../store/pendingUpload.js').then(({ setPendingUpload }) => {
    setPendingUpload(files.value, formData.value.simulationRequirement)
    
    router.push({
      name: 'Process',
      params: { projectId: 'new' }
    })
  })
}
</script>

<style scoped>
/* CSS bleibt unverändert */
</style>
