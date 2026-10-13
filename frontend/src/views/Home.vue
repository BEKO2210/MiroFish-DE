<template>
  <div class="home">
    <!-- Kopfzeile -->
    <header class="topbar">
      <router-link to="/" class="brand" aria-label="MiroFish Startseite">
        <img src="/logo-mark.svg" alt="" class="brand__mark" width="28" height="28" />
        <span class="brand__name">MiroFish</span>
      </router-link>
      <div class="topbar__right">
        <button type="button" class="status-pill" :class="systemStatus.ready ? 'ok' : 'warn'" @click="showSettings = !showSettings"
                :title="systemStatus.ready ? `${systemStatus.llm_model} · ${systemStatus.memory_provider}` : 'Einstellungen öffnen'">
          <span class="status-pill__dot"></span>
          <span class="status-pill__text">{{ systemStatus.ready ? 'Bereit' : 'Einrichten' }}</span>
        </button>
        <button type="button" class="icon-btn" aria-label="Farben wählen" title="Farben" @click="showTheme = true">
          <span class="icon-btn__swatch"></span>
        </button>
        <a href="https://github.com/BEKO2210/MiroFish-DE" target="_blank" rel="noopener" class="topbar__link">GitHub</a>
      </div>
    </header>
    <ThemePicker :open="showTheme" @close="showTheme = false" />

    <main class="main">
      <!-- Hero: kurz, klar -->
      <section class="hero">
        <p class="eyebrow">Schwarm-Simulation mit KI-Agenten · läuft auf deinem Rechner</p>
        <h1 class="hero__title">Was passiert als Nächstes?</h1>
        <p class="hero__lead">
          Lade einen Bericht, einen Artikel oder Notizen hoch und stelle eine Frage. MiroFish baut daraus eine Welt aus
          Interessengruppen, lässt sie Tage bis Wochen interagieren und schreibt dir einen Vorhersagebericht.
        </p>
        <ol class="steps" aria-label="So funktioniert es">
          <li><span class="steps__num">1</span><span>Hochladen</span></li>
          <li><span class="steps__num">2</span><span>Frage stellen</span></li>
          <li><span class="steps__num">3</span><span>Simulation läuft</span></li>
          <li><span class="steps__num">4</span><span>Bericht lesen</span></li>
        </ol>
      </section>

      <!-- Laufende Durchläufe -->
      <section v-if="activeRuns.length" class="section">
        <h2 class="section__title">Läuft gerade</h2>
        <router-link v-for="run in activeRuns" :key="run.pipeline_id" :to="`/run/${run.pipeline_id}`" class="run-card">
          <span class="run-card__pulse"></span>
          <span class="run-card__body">
            <span class="run-card__title">{{ run.requirement }}</span>
            <span class="run-card__meta">{{ stepLabel(run.current_step) }} · gestartet {{ fmtTime(run.created_at) }}</span>
          </span>
          <span class="run-card__arrow">›</span>
        </router-link>
      </section>

      <!-- Neue Vorhersage -->
      <section class="section" id="start">
        <div class="card">
          <h2 class="card__title">Neue Vorhersage</h2>

          <input ref="fileInput" type="file" multiple accept=".pdf,.md,.txt" class="sr-only" @change="handleFileSelect" />
          <div class="dropzone" :class="{ 'is-over': isDragOver, 'has-files': files.length }"
               role="button" tabindex="0" @click="triggerFileInput" @keydown.enter.prevent="triggerFileInput"
               @dragover.prevent="handleDragOver" @dragleave.prevent="handleDragLeave" @drop.prevent="handleDrop">
            <template v-if="!files.length">
              <span class="dropzone__icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 16V4m0 0 4 4m-4-4-4 4"/><path d="M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/></svg>
              </span>
              <span class="dropzone__title">Dokumente auswählen</span>
              <span class="dropzone__hint">PDF, Markdown oder Text · mehrere möglich</span>
            </template>
            <ul v-else class="filelist" @click.stop>
              <li v-for="(file, i) in files" :key="file.name + i" class="filelist__item">
                <span class="filelist__type">{{ file.name.split('.').pop().toUpperCase() }}</span>
                <span class="filelist__name">{{ file.name }}</span>
                <button type="button" class="filelist__remove" :aria-label="`${file.name} entfernen`" @click.stop="removeFile(i)">×</button>
              </li>
              <li class="filelist__add"><button type="button" @click.stop="triggerFileInput">+ Weitere Datei</button></li>
            </ul>
          </div>

          <label class="field">
            <span class="field__label">Deine Frage</span>
            <textarea v-model="formData.simulationRequirement" class="field__input" rows="3"
                      placeholder="Zum Beispiel: Wie reagieren Anwohner und Einzelhandel in den ersten vier Wochen auf die neuen Parkgebühren?"></textarea>
            <span class="field__hint">Eine konkrete Frage mit Zeitraum liefert den besten Bericht.</span>
          </label>

          <label class="switch">
            <input type="checkbox" v-model="autopilot" />
            <span class="switch__track" aria-hidden="true"><span class="switch__thumb"></span></span>
            <span class="switch__text">
              <strong>Bis zum Bericht durchlaufen lassen</strong>
              <small>Alle Schritte automatisch. Du kannst die Seite schließen und später wiederkommen.</small>
            </span>
          </label>

          <p v-if="error" class="error" role="alert">{{ error }}</p>

          <button type="button" class="cta" :disabled="!canSubmit || loading" @click="start">
            <span v-if="!loading">{{ autopilot ? 'Vorhersage starten' : 'Schritt für Schritt starten' }}</span>
            <span v-else class="cta__loading"><span class="spinner"></span> Wird hochgeladen …</span>
          </button>
          <p class="card__foot">
            <span v-if="systemStatus.ready">Modell: {{ systemStatus.llm_model }} · Gedächtnis: {{ memoryLabel }} · 0 € pro Lauf</span>
            <button v-else type="button" class="linkbtn" @click="showSettings = true">Erst das Modell einrichten</button>
          </p>
        </div>
      </section>

      <!-- Einstellungen -->
      <section class="section" v-show="showSettings" id="settings">
        <div class="card">
          <div class="card__head">
            <h2 class="card__title">Einstellungen</h2>
            <button type="button" class="linkbtn" @click="showSettings = false">Schließen</button>
          </div>
          <div v-if="isConfigMasked" class="notice">
            Einige Schlüssel sind maskiert. Zum Ändern bitte neu eingeben.
          </div>
          <label class="field">
            <span class="field__label">Gedächtnis (Wissensgraph)</span>
            <select v-model="configData.memory_provider" class="field__input">
              <option value="obsidian">Lokal (Markdown auf diesem Rechner)</option>
              <option value="zep">Zep Cloud</option>
              <option value="hybrid">Hybrid (lokal + Zep)</option>
            </select>
            <span class="field__hint" v-if="configData.memory_provider === 'obsidian'">Kein Konto nötig – alles bleibt auf diesem Rechner.</span>
            <span class="field__hint" v-else>Braucht einen Zep-API-Schlüssel.</span>
          </label>
          <label class="field">
            <span class="field__label">Sprachmodell</span>
            <select v-model="configData.llm_provider" class="field__input">
              <option value="ollama">Ollama (lokal)</option>
              <option value="lmstudio">LM Studio (lokal)</option>
              <option value="local">Anderer lokaler Endpunkt</option>
              <option value="openai">OpenAI (Cloud)</option>
            </select>
          </label>
          <template v-if="configData.llm_provider === 'openai'">
            <label class="field"><span class="field__label">API-Schlüssel</span><input type="password" v-model="configData.llm_api_key" class="field__input" placeholder="sk-…"></label>
            <label class="field"><span class="field__label">Basis-URL</span><input type="text" v-model="configData.llm_base_url" class="field__input" placeholder="https://api.openai.com/v1"></label>
            <label class="field"><span class="field__label">Modell</span><input type="text" v-model="configData.llm_model_name" class="field__input" placeholder="gpt-4o-mini"></label>
          </template>
          <template v-else>
            <label class="field"><span class="field__label">Adresse des lokalen Modells</span><input type="text" v-model="configData.local_llm_base_url" class="field__input" placeholder="http://127.0.0.1:11434/v1"></label>
            <label class="field"><span class="field__label">Modellname</span><input type="text" v-model="configData.local_llm_model_name" class="field__input" placeholder="z. B. gemma4:12b-it-qat-16k"></label>
            <label class="field"><span class="field__label">Schlüssel (meist nicht nötig)</span><input type="password" v-model="configData.local_llm_api_key" class="field__input"></label>
          </template>
          <label class="field" v-if="configData.memory_provider !== 'obsidian'">
            <span class="field__label">Zep-API-Schlüssel</span>
            <input type="password" v-model="configData.zep_api_key" class="field__input" placeholder="Zep Cloud API Key">
          </label>
          <div class="actions">
            <button type="button" class="btn btn--primary" :disabled="saving" @click="saveSettings">{{ saving ? 'Speichert …' : 'Speichern' }}</button>
            <button type="button" class="btn" :disabled="testing" @click="testLlmConnection">{{ testing ? 'Prüft …' : 'Verbindung prüfen' }}</button>
          </div>
          <p v-if="testResult" class="notice" :class="testResult.success ? 'notice--ok' : 'notice--err'">{{ testResult.message }}</p>
        </div>
      </section>

      <!-- Verlauf -->
      <section class="section">
        <HistoryDatabase />
      </section>

      <footer class="foot">
        <span>MiroFish · lokal, ohne Cloud · <a href="https://github.com/BEKO2210/MiroFish-DE" target="_blank" rel="noopener">Quellcode (AGPL-3.0)</a></span>
      </footer>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import HistoryDatabase from '../components/HistoryDatabase.vue'
import ThemePicker from '../components/ThemePicker.vue'
import service from '../api/index'
import { startPipeline, listPipelines, STEP_LABELS } from '../api/pipeline'

const router = useRouter()
const formData = ref({ simulationRequirement: '' })
const files = ref([])
const loading = ref(false)
const error = ref('')
const isDragOver = ref(false)
const autopilot = ref(true)
const fileInput = ref(null)
const activeRuns = ref([])
let runsTimer = null

// Einstellungen
const showSettings = ref(false)
const showTheme = ref(false)
const saving = ref(false)
const testing = ref(false)
const testResult = ref(null)
const systemStatus = ref({ ready: false, llm_provider: '-', llm_model: '-', is_local_llm: false, memory_provider: '-' })
const configData = ref({
  llm_provider: 'ollama', llm_api_key: '', llm_base_url: '', llm_model_name: '',
  local_llm_base_url: '', local_llm_model_name: '', local_llm_api_key: '', zep_api_key: '', memory_provider: 'obsidian'
})
const isConfigMasked = computed(() =>
  (configData.value.zep_api_key && configData.value.zep_api_key.includes('...****')) ||
  (configData.value.llm_provider === 'openai' && configData.value.llm_api_key && configData.value.llm_api_key.includes('...****')))
const memoryLabel = computed(() => ({ obsidian: 'lokal', zep: 'Zep Cloud', hybrid: 'Hybrid' }[systemStatus.value.memory_provider] || systemStatus.value.memory_provider))
const canSubmit = computed(() => formData.value.simulationRequirement.trim() !== '' && files.value.length > 0)

const fetchStatus = async () => {
  try {
    const res = await service.get('/api/graph/system/status')
    if (res && res.success) {
      const data = res.data
      systemStatus.value = { ready: true, llm_provider: data.llm_provider, llm_model: data.llm_model, is_local_llm: data.is_local_llm, memory_provider: data.memory_provider }
      if (data.config) configData.value = { ...data.config }
    }
  } catch (err) {
    console.error('Systemstatus nicht abrufbar:', err)
    systemStatus.value.ready = false
  }
}
const saveSettings = async () => {
  saving.value = true
  try {
    const res = await service.post('/api/graph/system/config', configData.value)
    if (res && res.success) { testResult.value = { success: true, message: 'Gespeichert.' }; await fetchStatus() }
  } catch (err) {
    testResult.value = { success: false, message: 'Speichern fehlgeschlagen: ' + (err.response?.data?.error || err.message) }
  } finally { saving.value = false }
}
const testLlmConnection = async () => {
  testing.value = true; testResult.value = null
  try {
    const res = await service.post('/api/graph/system/test-llm')
    if (res && res.success) testResult.value = { success: true, message: `Verbindung steht. Modell: ${res.data.model}` }
  } catch (err) {
    testResult.value = { success: false, message: 'Keine Verbindung: ' + (err.response?.data?.error || err.message) }
  } finally { testing.value = false }
}

const loadRuns = async () => {
  try {
    const res = await listPipelines()
    activeRuns.value = (res?.data || []).filter(r => r.status === 'running')
  } catch (e) { /* Liste ist optional */ }
}
const stepLabel = (s) => STEP_LABELS[s] || 'Wird vorbereitet'
const fmtTime = (iso) => { try { return new Date(iso).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }) } catch (e) { return '' } }

// Dateien
const triggerFileInput = () => { if (!loading.value) fileInput.value?.click() }
const handleFileSelect = (e) => { addFiles(Array.from(e.target.files)); e.target.value = '' }
const handleDragOver = () => { if (!loading.value) isDragOver.value = true }
const handleDragLeave = () => { isDragOver.value = false }
const handleDrop = (e) => { isDragOver.value = false; if (!loading.value) addFiles(Array.from(e.dataTransfer.files)) }
const addFiles = (newFiles) => {
  const ok = newFiles.filter(f => ['pdf', 'md', 'txt'].includes(f.name.split('.').pop().toLowerCase()))
  if (ok.length < newFiles.length) error.value = 'Nur PDF, Markdown (.md) und Text (.txt) werden gelesen.'
  else error.value = ''
  files.value.push(...ok)
}
const removeFile = (i) => files.value.splice(i, 1)

// Start
const start = async () => {
  if (!canSubmit.value || loading.value) return
  error.value = ''
  if (!autopilot.value) {
    const { setPendingUpload } = await import('../store/pendingUpload.js')
    setPendingUpload(files.value, formData.value.simulationRequirement)
    router.push({ name: 'Process', params: { projectId: 'new' } })
    return
  }
  loading.value = true
  try {
    const res = await startPipeline(files.value, formData.value.simulationRequirement)
    router.push(`/run/${res.data.pipeline_id}`)
  } catch (err) {
    error.value = 'Start fehlgeschlagen: ' + (err.response?.data?.error || err.message)
  } finally { loading.value = false }
}

onMounted(() => { fetchStatus(); loadRuns(); runsTimer = setInterval(loadRuns, 15000) })
onUnmounted(() => clearInterval(runsTimer))
</script>

<style scoped>
.home { min-height: 100vh; background: var(--color-bg-canvas); color: var(--color-text-primary); }
.topbar { position: sticky; top: 0; z-index: 20; display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 10px 16px; background: color-mix(in srgb, var(--color-bg-canvas) 86%, transparent); backdrop-filter: saturate(180%) blur(12px); border-bottom: 1px solid var(--color-border-subtle); }
.brand { display: flex; align-items: center; gap: 10px; text-decoration: none; color: inherit; }
.brand__mark { width: 28px; height: 28px; }
.brand__name { font-family: var(--font-heading); font-weight: 700; font-size: 18px; letter-spacing: -0.01em; }
.topbar__right { display: flex; align-items: center; gap: 10px; }
.icon-btn { width: 40px; height: 40px; border: 1px solid var(--color-border-subtle); border-radius: 50%; background: var(--color-bg-surface-raised); display: inline-flex; align-items: center; justify-content: center; cursor: pointer; padding: 0; }
.icon-btn__swatch { width: 18px; height: 18px; border-radius: 50%; background: linear-gradient(135deg, var(--theme-light, #fff) 50%, var(--color-brand-primary) 50%); border: 1px solid var(--color-border-default); }
.topbar__link { color: var(--color-text-secondary); text-decoration: none; font-size: 14px; padding: 8px 4px; }
.status-pill { display: inline-flex; align-items: center; gap: 6px; border: 1px solid var(--color-border-subtle); background: var(--color-bg-surface-raised); border-radius: 999px;
  padding: 6px 10px; font: inherit; font-size: 13px; color: var(--color-text-secondary); cursor: pointer; min-height: 36px; }
.status-pill__dot { width: 8px; height: 8px; border-radius: 50%; background: var(--color-success-text); box-shadow: 0 0 0 3px rgba(21,128,61,.15); }
.status-pill.warn .status-pill__dot { background: var(--color-warning-text); box-shadow: 0 0 0 3px rgba(180,83,9,.15); }

.main { max-width: 760px; margin: 0 auto; padding: 24px 16px 40px; }
.section { margin-top: 24px; }
.section__title { font-family: var(--font-heading); font-size: 15px; font-weight: 600; color: var(--color-text-secondary); margin: 0 0 10px; letter-spacing: .02em; text-transform: uppercase; }

.hero { padding: 8px 0 4px; }
.eyebrow { margin: 0 0 8px; font-size: 13px; color: var(--color-text-muted); }
.hero__title { font-family: var(--font-heading); font-size: clamp(30px, 7vw, 44px); line-height: 1.08; letter-spacing: -0.02em; margin: 0 0 12px; }
.hero__lead { font-size: 16px; line-height: 1.55; color: var(--color-text-secondary); margin: 0 0 16px; max-width: 60ch; }
.steps { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 8px; }
.steps li { display: inline-flex; align-items: center; gap: 8px; font-size: 13px; color: var(--color-text-secondary); background: var(--color-bg-surface); border: 1px solid var(--color-border-subtle); border-radius: 999px; padding: 6px 12px 6px 6px; }
.steps__num { width: 22px; height: 22px; border-radius: 50%; background: var(--color-text-primary); color: var(--color-text-inverse); font-size: 12px; font-weight: 700; display: inline-flex; align-items: center; justify-content: center; }

.card { background: var(--color-bg-surface-raised); border: 1px solid var(--color-border-subtle); border-radius: 16px; padding: 18px; box-shadow: 0 1px 2px rgba(15,23,42,.04), 0 8px 24px -16px rgba(15,23,42,.18); }
.card__head { display: flex; justify-content: space-between; align-items: center; }
.card__title { font-family: var(--font-heading); font-size: 20px; margin: 0 0 14px; }
.card__foot { margin: 12px 0 0; font-size: 13px; color: var(--color-text-muted); text-align: center; }
.linkbtn { background: none; border: 0; color: var(--color-brand-primary); font: inherit; font-size: 14px; cursor: pointer; padding: 8px 0; text-decoration: underline; }

.dropzone { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; min-height: 120px; padding: 16px; border: 1.5px dashed var(--color-border-default); border-radius: 12px; background: var(--color-bg-surface); cursor: pointer; transition: border-color .15s, background .15s; text-align: center; }
.dropzone:hover, .dropzone:focus-visible, .dropzone.is-over { border-color: var(--color-brand-primary); background: var(--color-brand-subtle); outline: none; }
.dropzone.has-files { align-items: stretch; cursor: default; }
.dropzone__icon { color: var(--color-brand-primary); }
.dropzone__title { font-weight: 600; }
.dropzone__hint { font-size: 13px; color: var(--color-text-muted); }
.filelist { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; width: 100%; }
.filelist__item { display: flex; align-items: center; gap: 10px; background: var(--color-bg-surface-raised); border: 1px solid var(--color-border-subtle); border-radius: 10px; padding: 8px 8px 8px 10px; }
.filelist__type { font-family: var(--font-mono); font-size: 11px; background: var(--color-text-primary); color: var(--color-text-inverse); border-radius: 6px; padding: 3px 6px; }
.filelist__name { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 14px; text-align: left; }
.filelist__remove { width: 36px; height: 36px; border: 0; background: transparent; color: var(--color-text-muted); font-size: 20px; border-radius: 8px; cursor: pointer; }
.filelist__remove:hover { background: var(--color-error-bg); color: var(--color-error-text); }
.filelist__add button { background: none; border: 0; color: var(--color-brand-primary); font: inherit; font-size: 14px; padding: 8px; cursor: pointer; }

.field { display: block; margin-top: 14px; }
.field__label { display: block; font-size: 13px; font-weight: 600; color: var(--color-text-secondary); margin-bottom: 6px; }
.field__input { width: 100%; font: inherit; font-size: 16px; line-height: 1.45; padding: 12px 14px; border: 1px solid var(--color-border-default); border-radius: 12px; background: var(--color-bg-surface-raised); color: inherit; resize: vertical; }
.field__input:focus { outline: none; border-color: var(--color-brand-primary); box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-brand-primary) 15%, transparent); }
.field__hint { display: block; font-size: 12px; color: var(--color-text-muted); margin-top: 6px; }

.switch { display: flex; align-items: center; gap: 12px; margin-top: 16px; cursor: pointer; }
.switch input { position: absolute; opacity: 0; width: 0; height: 0; }
.switch__track { position: relative; width: 44px; height: 26px; border-radius: 999px; background: var(--color-border-default); transition: background .2s; flex: none; }
.switch__thumb { position: absolute; top: 3px; left: 3px; width: 20px; height: 20px; border-radius: 50%; background: var(--color-bg-surface-raised); box-shadow: 0 1px 3px rgba(0,0,0,.25); transition: transform .2s; }
.switch input:checked + .switch__track { background: var(--color-brand-primary); }
.switch input:checked + .switch__track .switch__thumb { transform: translateX(18px); }
.switch input:focus-visible + .switch__track { box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-brand-primary) 25%, transparent); }
.switch__text { display: flex; flex-direction: column; font-size: 14px; }
.switch__text small { color: var(--color-text-muted); font-size: 12px; }

.cta { width: 100%; margin-top: 16px; min-height: 52px; border: 0; border-radius: 14px; background: var(--color-brand-primary); color: var(--color-brand-on-primary); font: inherit; font-size: 17px; font-weight: 700; cursor: pointer; transition: transform .08s, background .15s; }
.cta:hover:not(:disabled) { background: var(--color-brand-hover); }
.cta:active:not(:disabled) { transform: scale(.99); }
.cta:disabled { background: var(--color-border-subtle); color: var(--color-border-strong); cursor: not-allowed; }
.cta__loading { display: inline-flex; align-items: center; gap: 10px; }
.spinner { width: 18px; height: 18px; border: 2px solid color-mix(in srgb, var(--color-brand-on-primary) 40%, transparent); border-top-color: var(--color-brand-on-primary); border-radius: 50%; animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.error { margin: 12px 0 0; color: var(--color-error-text); font-size: 14px; }

.run-card { display: flex; align-items: center; gap: 12px; text-decoration: none; color: inherit; background: var(--color-bg-surface-raised); border: 1px solid var(--color-border-subtle); border-radius: 14px; padding: 12px 14px; margin-bottom: 8px; }
.run-card__pulse { width: 10px; height: 10px; border-radius: 50%; background: var(--color-brand-primary); flex: none; animation: pulse 1.6s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--color-brand-primary) 45%, transparent); } 50% { box-shadow: 0 0 0 8px color-mix(in srgb, var(--color-brand-primary) 0%, transparent); } }
.run-card__body { display: flex; flex-direction: column; min-width: 0; flex: 1; }
.run-card__title { font-weight: 600; font-size: 15px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.run-card__meta { font-size: 12px; color: var(--color-text-muted); }
.run-card__arrow { font-size: 22px; color: var(--color-border-strong); }

.notice { margin: 10px 0 0; padding: 10px 12px; border-radius: 10px; background: var(--color-brand-subtle); color: var(--color-brand-hover); font-size: 14px; }
.notice--ok { background: var(--color-success-bg); color: var(--color-success-text); }
.notice--err { background: var(--color-error-bg); color: var(--color-error-text); }
.actions { display: flex; gap: 10px; margin-top: 16px; }
.btn { flex: 1; min-height: 44px; border-radius: 12px; border: 1px solid var(--color-border-subtle); background: var(--color-bg-surface-raised); font: inherit; font-weight: 600; cursor: pointer; }
.btn--primary { background: var(--color-text-primary); color: var(--color-text-inverse); border-color: var(--color-text-primary); }
.btn:disabled { opacity: .6; cursor: not-allowed; }
.foot { margin-top: 40px; text-align: center; font-size: 12px; color: var(--color-text-muted); }
.foot a { color: inherit; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }

@media (min-width: 769px) {
  .main { padding: 40px 24px 60px; max-width: 880px; }
  .topbar { padding: 12px 24px; }
  .hero { padding: 16px 0 8px; }
  .card { padding: 24px; }
}
</style>
