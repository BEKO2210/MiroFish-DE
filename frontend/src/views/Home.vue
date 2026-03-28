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
.home-container {
  min-height: 100vh;
  background: #ffffff;
  color: #000000;
}

/* Navigation */
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 40px;
  border-bottom: 1px solid #eaeaea;
}

.nav-brand {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  font-size: 20px;
  letter-spacing: 2px;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 20px;
}

.github-link {
  color: #666;
  text-decoration: none;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: color 0.2s;
}

.github-link:hover {
  color: #000;
}

.arrow {
  font-size: 12px;
}

/* Main Content */
.main-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 40px;
}

/* Hero Section */
.hero-section {
  display: flex;
  gap: 60px;
  margin-bottom: 80px;
  min-height: 500px;
}

.hero-left {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.hero-right {
  width: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
}

.tag-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.orange-tag {
  background: #ff5722;
  color: white;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  border-radius: 4px;
}

.version-text {
  font-size: 12px;
  color: #999;
  font-family: 'JetBrains Mono', monospace;
}

.main-title {
  font-size: 42px;
  font-weight: 800;
  line-height: 1.2;
  margin-bottom: 24px;
  letter-spacing: -0.5px;
}

.gradient-text {
  background: linear-gradient(90deg, #ff5722, #ff9800);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-desc {
  font-size: 16px;
  line-height: 1.7;
  color: #444;
  margin-bottom: 20px;
}

.hero-desc p {
  margin-bottom: 16px;
}

.highlight-bold {
  font-weight: 700;
  color: #000;
}

.highlight-orange {
  color: #ff5722;
  font-weight: 700;
}

.highlight-code {
  font-family: 'JetBrains Mono', monospace;
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 14px;
}

.slogan-text {
  font-size: 14px;
  color: #666;
  font-style: italic;
}

.blinking-cursor {
  animation: blink 1s infinite;
  font-weight: 300;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.decoration-square {
  width: 60px;
  height: 60px;
  border: 3px solid #000;
  margin-top: 30px;
  transform: rotate(45deg);
}

/* Logo */
.logo-container {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.hero-logo {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.1);
}

.scroll-down-btn {
  position: absolute;
  bottom: 20px;
  width: 40px;
  height: 40px;
  border: 2px solid #000;
  background: transparent;
  border-radius: 50%;
  font-size: 18px;
  cursor: pointer;
  transition: all 0.2s;
}

.scroll-down-btn:hover {
  background: #000;
  color: #fff;
}

/* Dashboard Section */
.dashboard-section {
  display: flex;
  gap: 40px;
  margin-top: 60px;
}

.left-panel {
  flex: 1;
  padding-right: 20px;
}

.right-panel {
  width: 500px;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
  margin-bottom: 20px;
  font-family: 'JetBrains Mono', monospace;
}

.status-dot {
  color: #4caf50;
}

.section-title {
  font-size: 32px;
  font-weight: 800;
  margin-bottom: 12px;
}

.section-desc {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
  margin-bottom: 30px;
}

/* Metrics */
.metrics-row {
  display: flex;
  gap: 16px;
  margin-bottom: 40px;
}

.metric-card {
  flex: 1;
  border: 1px solid #eaeaea;
  padding: 20px;
  border-radius: 8px;
}

.metric-value {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 4px;
}

.metric-label {
  font-size: 12px;
  color: #999;
}

/* Steps */
.steps-container {
  border: 1px solid #eaeaea;
  border-radius: 8px;
  overflow: hidden;
}

.steps-header {
  padding: 16px 20px;
  background: #f9f9f9;
  border-bottom: 1px solid #eaeaea;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.diamond-icon {
  color: #ff5722;
}

.workflow-list {
  padding: 10px 0;
}

.workflow-item {
  display: flex;
  gap: 16px;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.workflow-item:last-child {
  border-bottom: none;
}

.step-num {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: #999;
  min-width: 24px;
}

.step-info {
  flex: 1;
}

.step-title {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 4px;
}

.step-desc {
  font-size: 12px;
  color: #888;
  line-height: 1.5;
}

/* Console Box */
.console-box {
  border: 2px solid #000;
  border-radius: 8px;
  padding: 24px;
  background: #fafafa;
}

.console-section {
  margin-bottom: 24px;
}

.console-section:last-child {
  margin-bottom: 0;
}

.console-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.console-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 600;
  color: #000;
}

.console-meta {
  font-size: 11px;
  color: #999;
}

/* Upload Zone */
.upload-zone {
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
}

.upload-zone:hover,
.upload-zone.drag-over {
  border-color: #ff5722;
  background: #fff5f2;
}

.upload-zone.has-files {
  border-style: solid;
  border-color: #4caf50;
  padding: 20px;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.upload-icon {
  font-size: 32px;
  color: #999;
}

.upload-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.upload-hint {
  font-size: 12px;
  color: #999;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #f5f5f5;
  border-radius: 6px;
}

.file-icon {
  font-size: 16px;
}

.file-name {
  flex: 1;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: #ff4444;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.remove-btn:hover {
  background: #cc0000;
}

/* Console Divider */
.console-divider {
  display: flex;
  align-items: center;
  text-align: center;
  margin: 20px 0;
  color: #999;
  font-size: 11px;
}

.console-divider::before,
.console-divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid #ddd;
}

.console-divider span {
  padding: 0 10px;
}

/* Input */
.input-wrapper {
  position: relative;
}

.code-input {
  width: 100%;
  padding: 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  line-height: 1.6;
  resize: vertical;
  min-height: 120px;
  background: #fff;
}

.code-input:focus {
  outline: none;
  border-color: #ff5722;
}

.model-badge {
  position: absolute;
  bottom: 10px;
  right: 10px;
  font-size: 10px;
  color: #999;
  background: #f5f5f5;
  padding: 4px 8px;
  border-radius: 4px;
}

/* Start Button */
.btn-section {
  margin-top: 20px;
}

.start-engine-btn {
  width: 100%;
  padding: 16px 24px;
  background: #000;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.2s;
}

.start-engine-btn:hover:not(:disabled) {
  background: #333;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.start-engine-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.btn-arrow {
  font-size: 18px;
}

/* Responsive */
@media (max-width: 1024px) {
  .hero-section {
    flex-direction: column;
  }
  
  .hero-right {
    width: 100%;
  }
  
  .dashboard-section {
    flex-direction: column;
  }
  
  .right-panel {
    width: 100%;
  }
  
  .main-title {
    font-size: 32px;
  }
}

@media (max-width: 768px) {
  .main-content {
    padding: 20px;
  }
  
  .navbar {
    padding: 16px 20px;
  }
  
  .main-title {
    font-size: 28px;
  }
  
  .metrics-row {
    flex-direction: column;
  }
}
</style>
