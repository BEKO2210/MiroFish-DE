<template>
  <div class="home">
    <AppHeader>
      <router-link to="/settings" class="status" :class="status.ready ? 'ok' : 'warn'" :title="status.ready ? 'Modell verbunden' : 'Einstellungen öffnen'">
        <span class="status__dot"></span><span>{{ status.ready ? 'Bereit' : 'Einrichten' }}</span>
      </router-link>
    </AppHeader>

    <!-- Hero: der Schwarm -->
    <section class="hero">
      <SwarmCanvas class="hero__swarm" />
      <div class="hero__inner">
        <h1 class="hero__title">Was passiert<br>als Nächstes?</h1>
        <p class="hero__lead">Lade Dokumente hoch und stelle eine Frage. Hunderte KI-Agenten spielen die Reaktion durch – du bekommst den Bericht.</p>
      </div>
    </section>

    <main class="main">
      <!-- Läuft gerade -->
      <section v-if="activeRuns.length" class="block">
        <router-link v-for="run in activeRuns" :key="run.pipeline_id" :to="`/run/${run.pipeline_id}`" class="live">
          <span class="live__pulse"></span>
          <span class="live__body">
            <span class="live__title">{{ run.requirement }}</span>
            <span class="live__meta">{{ stepLabel(run.current_step) }} · seit {{ fmtTime(run.created_at) }}</span>
          </span>
          <span class="live__chev">›</span>
        </router-link>
      </section>

      <!-- Formular -->
      <section class="block" id="start">
        <form class="form" @submit.prevent="start">
          <h2 class="form__title">Neue Vorhersage</h2>

          <input ref="fileInput" type="file" multiple accept=".pdf,.md,.txt" class="sr-only" @change="onFiles" />
          <div class="drop" :class="{ 'is-over': over, 'has-files': files.length }" role="button" tabindex="0"
               @click="pick" @keydown.enter.prevent="pick" @dragover.prevent="over = true" @dragleave.prevent="over = false" @drop.prevent="onDrop">
            <template v-if="!files.length">
              <svg class="drop__icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5M10 14h5M10 17h5"/></svg>
              <span class="drop__title">Dokumente hinzufügen</span>
              <span class="drop__hint">PDF, Markdown oder Text</span>
            </template>
            <ul v-else class="files" @click.stop>
              <li v-for="(f, i) in files" :key="f.name + i" class="files__item">
                <span class="files__type">{{ f.name.split('.').pop().toUpperCase() }}</span>
                <span class="files__name">{{ f.name }}</span>
                <button type="button" class="files__rm" :aria-label="`${f.name} entfernen`" @click.stop="files.splice(i, 1)">×</button>
              </li>
              <li><button type="button" class="files__add" @click.stop="pick">+ Weitere Datei</button></li>
            </ul>
          </div>

          <label class="field">
            <span class="field__label">Deine Frage</span>
            <textarea v-model="question" class="field__input" rows="3" placeholder="Wie reagieren Anwohner und Einzelhandel in den ersten vier Wochen auf die neuen Parkgebühren?"></textarea>
          </label>

          <label class="switch">
            <input type="checkbox" v-model="autopilot" />
            <span class="switch__track" aria-hidden="true"><span class="switch__thumb"></span></span>
            <span class="switch__text"><strong>Bis zum Bericht durchlaufen</strong><small>Alle Schritte automatisch. Du kannst die Seite schließen.</small></span>
          </label>

          <p v-if="error" class="error" role="alert">{{ error }}</p>
          <button type="submit" class="cta" :disabled="!canSubmit || loading">
            <span v-if="!loading">{{ autopilot ? 'Vorhersage starten' : 'Schritt für Schritt starten' }}</span>
            <span v-else class="cta__busy"><span class="spin"></span>Wird hochgeladen …</span>
          </button>
          <p v-if="!status.ready" class="form__foot"><router-link to="/settings">Erst das Sprachmodell verbinden</router-link></p>
        </form>
      </section>

      <!-- So funktioniert es -->
      <section class="block">
        <h2 class="block__title">So funktioniert es</h2>
        <ol class="how">
          <li class="how__step">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5"/></svg>
            <strong>Dokumente</strong><span>Berichte, Artikel, Protokolle – alles, was die Lage beschreibt.</span>
          </li>
          <li class="how__step">
            <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
            <strong>Welt</strong><span>Daraus entstehen Gruppen, Personen und ihre Beziehungen.</span>
          </li>
          <li class="how__step">
            <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="6" cy="8" r="2"/><circle cx="12" cy="5" r="2"/><circle cx="18" cy="9" r="2"/><circle cx="8" cy="16" r="2"/><circle cx="16" cy="17" r="2"/><path d="M7.5 9.5 10 14M13 7l3.8 1.2M10 15.5l4 1"/></svg>
            <strong>Schwarm</strong><span>Hunderte Agenten reden, reagieren und streiten – über Tage bis Wochen.</span>
          </li>
          <li class="how__step">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 4h14v16H5z"/><path d="M8 9h8M8 13h8M8 17h5"/></svg>
            <strong>Bericht</strong><span>Was wahrscheinlich passiert, wer es treibt, worauf du achten solltest.</span>
          </li>
        </ol>
      </section>

      <!-- Zuletzt -->
      <section v-if="recent.length" class="block">
        <div class="block__head">
          <h2 class="block__title">Zuletzt</h2>
          <router-link to="/history" class="block__link">Alle anzeigen</router-link>
        </div>
        <router-link v-for="r in recent" :key="r.simulation_id" :to="r.report_id ? `/report/${r.report_id}` : `/simulation/${r.simulation_id}`" class="recent">
          <span class="recent__title">{{ r.simulation_requirement || r.project_name || 'Ohne Titel' }}</span>
          <span class="recent__meta">{{ fmtDate(r.created_at) }}<template v-if="r.report_id"> · Bericht</template></span>
        </router-link>
      </section>

      <footer class="foot">MiroFish · Open Source · <a href="https://github.com/BEKO2210/MiroFish-DE" target="_blank" rel="noopener">GitHub</a></footer>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import SwarmCanvas from '../components/SwarmCanvas.vue'
import service from '../api/index'
import { getSimulationHistory } from '../api/simulation'
import { startPipeline, listPipelines, STEP_LABELS } from '../api/pipeline'

const router = useRouter()
const question = ref('')
const files = ref([])
const loading = ref(false)
const error = ref('')
const over = ref(false)
const autopilot = ref(true)
const fileInput = ref(null)
const activeRuns = ref([])
const recent = ref([])
const status = ref({ ready: false })
let timer = null

const canSubmit = computed(() => question.value.trim() && files.value.length > 0)
const stepLabel = (s) => STEP_LABELS[s] || 'Wird vorbereitet'
const fmtTime = (iso) => { try { return new Date(iso).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }) } catch (e) { return '' } }
const fmtDate = (iso) => { try { return new Date(iso).toLocaleDateString('de-DE', { day: '2-digit', month: 'short' }) } catch (e) { return '' } }

const loadStatus = async () => {
  try { const r = await service.get('/api/graph/system/status'); status.value.ready = !!r?.success } catch (e) { status.value.ready = false }
}
const loadRuns = async () => {
  try { activeRuns.value = ((await listPipelines())?.data || []).filter(r => r.status === 'running') } catch (e) { /* optional */ }
}
const loadRecent = async () => {
  try { recent.value = ((await getSimulationHistory())?.data || []).slice(0, 3) } catch (e) { /* optional */ }
}

const pick = () => { if (!loading.value) fileInput.value?.click() }
const onFiles = (e) => { add(Array.from(e.target.files)); e.target.value = '' }
const onDrop = (e) => { over.value = false; if (!loading.value) add(Array.from(e.dataTransfer.files)) }
const add = (list) => {
  const ok = list.filter(f => ['pdf', 'md', 'txt'].includes(f.name.split('.').pop().toLowerCase()))
  error.value = ok.length < list.length ? 'Nur PDF, Markdown (.md) und Text (.txt) werden gelesen.' : ''
  files.value.push(...ok)
}

const start = async () => {
  if (!canSubmit.value || loading.value) return
  error.value = ''
  if (!autopilot.value) {
    const { setPendingUpload } = await import('../store/pendingUpload.js')
    setPendingUpload(files.value, question.value)
    router.push({ name: 'Process', params: { projectId: 'new' } })
    return
  }
  loading.value = true
  try {
    const res = await startPipeline(files.value, question.value)
    router.push(`/run/${res.data.pipeline_id}`)
  } catch (err) {
    error.value = 'Start fehlgeschlagen: ' + (err.response?.data?.error || err.message)
  } finally { loading.value = false }
}

onMounted(() => { loadStatus(); loadRuns(); loadRecent(); timer = setInterval(loadRuns, 15000) })
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.home { min-height: 100vh; background: var(--color-bg-canvas); color: var(--color-text-primary); }
.status { display: inline-flex; align-items: center; gap: 7px; min-height: 36px; padding: 0 12px; border-radius: 999px; border: 1px solid var(--color-border-subtle); background: var(--color-bg-surface-raised); color: var(--color-text-secondary); font-size: 13px; font-weight: 500; text-decoration: none; }
.status__dot { width: 8px; height: 8px; border-radius: 50%; background: var(--color-success-text); }
.status.warn .status__dot { background: var(--color-warning-text); }

/* Hero */
.hero { position: relative; overflow: hidden; min-height: 300px; display: flex; align-items: flex-end; border-bottom: 1px solid var(--color-border-subtle);
  background: radial-gradient(120% 80% at 80% 0%, color-mix(in srgb, var(--color-brand-primary) 10%, transparent), transparent 60%), var(--color-bg-canvas); }
.hero__swarm { position: absolute; inset: 0; }
.hero__inner { position: relative; padding: 48px 16px 28px; max-width: 760px; margin: 0 auto; width: 100%; pointer-events: none; }
.hero__title, .hero__lead { text-shadow: 0 0 18px var(--color-bg-canvas), 0 0 6px var(--color-bg-canvas), 0 0 2px var(--color-bg-canvas); }
.hero__title { font-family: var(--font-heading); font-size: clamp(38px, 10vw, 72px); line-height: .98; letter-spacing: -0.03em; margin: 0 0 14px; font-weight: 700; }
.hero__lead { font-size: 17px; line-height: 1.5; max-width: 34ch; margin: 0; color: var(--color-text-secondary); }

.main { max-width: 760px; margin: 0 auto; padding: 16px 16px 32px; }
.block { margin-top: 24px; }
.block__head { display: flex; align-items: baseline; justify-content: space-between; }
.block__title { font-family: var(--font-heading); font-size: 20px; margin: 0 0 12px; letter-spacing: -0.01em; }
.block__link { font-size: 14px; color: var(--color-brand-primary); text-decoration: none; font-weight: 500; }

.live { display: flex; align-items: center; gap: 12px; text-decoration: none; color: inherit; padding: 12px 14px; border-radius: 14px; border: 1px solid var(--color-brand-border); background: var(--color-brand-subtle); margin-bottom: 8px; }
.live__pulse { width: 10px; height: 10px; border-radius: 50%; background: var(--color-brand-primary); flex: none; animation: pulse 1.6s ease-in-out infinite; }
@keyframes pulse { 0%,100% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--color-brand-primary) 45%, transparent); } 50% { box-shadow: 0 0 0 8px transparent; } }
.live__body { display: flex; flex-direction: column; min-width: 0; flex: 1; }
.live__title { font-weight: 600; font-size: 15px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.live__meta { font-size: 12px; color: var(--color-text-muted); }
.live__chev { font-size: 22px; color: var(--color-text-muted); }

.form { background: var(--color-bg-surface-raised); border: 1px solid var(--color-border-subtle); border-radius: 20px; padding: 18px; box-shadow: var(--shadow-md); }
.form__title { font-family: var(--font-heading); font-size: 22px; margin: 0 0 14px; letter-spacing: -0.01em; }
.form__foot { margin: 10px 0 0; text-align: center; font-size: 14px; }
.form__foot a { color: var(--color-brand-primary); }
.drop { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; min-height: 124px; padding: 16px; border: 1.5px dashed var(--color-border-default); border-radius: 14px; background: var(--color-bg-surface); cursor: pointer; text-align: center; transition: border-color .15s, background .15s; }
.drop:hover, .drop:focus-visible, .drop.is-over { border-color: var(--color-brand-primary); background: var(--color-brand-subtle); outline: none; }
.drop.has-files { align-items: stretch; cursor: default; }
.drop__icon { width: 30px; height: 30px; fill: none; stroke: var(--color-brand-primary); stroke-width: 1.7; stroke-linecap: round; stroke-linejoin: round; margin-bottom: 6px; }
.drop__title { font-weight: 600; font-size: 16px; }
.drop__hint { font-size: 13px; color: var(--color-text-muted); }
.files { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
.files__item { display: flex; align-items: center; gap: 10px; background: var(--color-bg-surface-raised); border: 1px solid var(--color-border-subtle); border-radius: 10px; padding: 6px 6px 6px 10px; }
.files__type { font-size: 11px; font-weight: 700; background: var(--color-text-primary); color: var(--color-text-inverse); border-radius: 6px; padding: 3px 6px; }
.files__name { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 14px; text-align: left; }
.files__rm { width: 36px; height: 36px; border: 0; background: transparent; color: var(--color-text-muted); font-size: 20px; border-radius: 8px; cursor: pointer; }
.files__rm:hover { background: var(--color-error-bg); color: var(--color-error-text); }
.files__add { background: none; border: 0; color: var(--color-brand-primary); font: inherit; font-size: 14px; font-weight: 500; padding: 8px; cursor: pointer; }
.field { display: block; margin-top: 14px; }
.field__label { display: block; font-size: 13px; font-weight: 600; color: var(--color-text-secondary); margin-bottom: 6px; }
.field__input { width: 100%; font: inherit; font-size: 16px; line-height: 1.45; padding: 12px 14px; border: 1px solid var(--color-border-default); border-radius: 12px; background: var(--color-bg-surface-raised); color: inherit; resize: vertical; }
.field__input:focus { outline: none; border-color: var(--color-brand-primary); box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-brand-primary) 15%, transparent); }
.switch { display: flex; align-items: center; gap: 12px; margin-top: 16px; cursor: pointer; }
.switch input { position: absolute; opacity: 0; width: 0; height: 0; }
.switch__track { position: relative; width: 46px; height: 28px; border-radius: 999px; background: var(--color-border-default); transition: background .2s; flex: none; }
.switch__thumb { position: absolute; top: 3px; left: 3px; width: 22px; height: 22px; border-radius: 50%; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,.25); transition: transform .2s; }
.switch input:checked + .switch__track { background: var(--color-brand-primary); }
.switch input:checked + .switch__track .switch__thumb { transform: translateX(18px); }
.switch input:focus-visible + .switch__track { box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-brand-primary) 25%, transparent); }
.switch__text { display: flex; flex-direction: column; font-size: 14px; }
.switch__text small { color: var(--color-text-muted); font-size: 12px; }
.cta { width: 100%; margin-top: 16px; min-height: 54px; border: 0; border-radius: 14px; background: var(--color-brand-primary); color: var(--color-brand-on-primary); font: inherit; font-size: 17px; font-weight: 700; cursor: pointer; transition: transform .08s, filter .15s; }
.cta:hover:not(:disabled) { filter: brightness(.92); }
.cta:active:not(:disabled) { transform: scale(.99); }
.cta:disabled { background: var(--color-bg-surface-subtle); color: var(--color-text-muted); cursor: not-allowed; }
.cta__busy { display: inline-flex; align-items: center; gap: 10px; }
.spin { width: 18px; height: 18px; border: 2px solid color-mix(in srgb, currentColor 35%, transparent); border-top-color: currentColor; border-radius: 50%; animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.error { margin: 12px 0 0; color: var(--color-error-text); font-size: 14px; }

.how { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: 1fr 1fr; gap: 10px; counter-reset: s; }
.how__step { position: relative; display: flex; flex-direction: column; gap: 6px; padding: 16px 14px 14px; border-radius: 16px; background: var(--color-bg-surface); border: 1px solid var(--color-border-subtle); counter-increment: s; }
.how__step::before { content: counter(s); position: absolute; top: 12px; right: 14px; font-family: var(--font-heading); font-size: 12px; font-weight: 700; color: var(--color-text-muted); }
.how__step svg { width: 28px; height: 28px; fill: none; stroke: var(--color-brand-primary); stroke-width: 1.7; stroke-linecap: round; stroke-linejoin: round; }
.how__step strong { font-family: var(--font-heading); font-size: 16px; }
.how__step span { font-size: 13px; line-height: 1.45; color: var(--color-text-secondary); }

.recent { display: flex; flex-direction: column; gap: 2px; text-decoration: none; color: inherit; padding: 12px 0; border-top: 1px solid var(--color-border-subtle); }
.recent:last-of-type { border-bottom: 1px solid var(--color-border-subtle); }
.recent__title { font-weight: 500; font-size: 15px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.recent__meta { font-size: 12px; color: var(--color-text-muted); }
.foot { margin-top: 36px; text-align: center; font-size: 12px; color: var(--color-text-muted); }
.foot a { color: inherit; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }

@media (min-width: 769px) {
  .hero { min-height: 420px; }
  .hero__inner { padding: 72px 24px 48px; max-width: 880px; }
  .hero__lead { font-size: 19px; }
  .main { max-width: 880px; padding: 24px 24px 64px; }
  .form { padding: 28px; }
  .how { grid-template-columns: repeat(4, 1fr); }
}
</style>
