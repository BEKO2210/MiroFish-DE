<template>
  <div class="run">
    <header class="topbar">
      <router-link to="/" class="back" :aria-label="t('run.backAria')">{{ t('run.back') }}</router-link>
      <span class="topbar__title">{{ t('run.title') }}</span>
      <span class="topbar__spacer"></span>
    </header>

    <main class="main">
      <!-- Ladezustand -->
      <div v-if="!state && !loadError && !cleanedUp" class="skeleton" aria-busy="true">
        <div class="sk sk--title"></div>
        <div class="sk sk--line"></div>
        <div class="sk sk--block"></div>
      </div>

      <div v-else-if="cleanedUp" class="cleaned">
        <p>{{ t('run.cleanedUp') }}</p>
        <router-link to="/" class="btn btn--primary">{{ t('run.goHome') }}</router-link>
      </div>

      <p v-else-if="loadError" class="error" role="alert">{{ loadError }}</p>

      <template v-else>
        <section class="head">
          <p class="eyebrow">{{ fmtDate(state.created_at) }} · {{ t('run.files', { n: (state.files || []).length }) }}</p>
          <h1 class="title">{{ state.requirement }}</h1>

          <!-- Gesamtstatus -->
          <div class="status" :class="`status--${state.status}`">
            <template v-if="state.status === 'running'">
              <span class="orb" aria-hidden="true"><span></span><span></span><span></span></span>
              <div>
                <strong>{{ currentLabel }}</strong>
                <small>{{ currentDetail || t('run.preparing') }}</small>
              </div>
            </template>
            <template v-else-if="state.status === 'completed'">
              <span class="check" aria-hidden="true">✓</span>
              <div><strong>{{ t('run.done') }}</strong><small>{{ t('run.duration', { d: fmtDuration(state.created_at, state.completed_at) }) }}</small></div>
            </template>
            <template v-else>
              <span class="cross" aria-hidden="true">!</span>
              <div><strong>{{ t('run.stopped') }}</strong><small>{{ t('hist.sFailed') }}</small></div>
            </template>
          </div>

          <!-- Gesamtfortschritt -->
          <div class="bar" role="progressbar" :aria-valuenow="overall" aria-valuemin="0" aria-valuemax="100">
            <div class="bar__fill" :class="{ 'bar__fill--live': state.status === 'running' }" :style="{ width: overall + '%' }"></div>
          </div>
          <p class="bar__meta">
            <span>{{ overall }} %</span>
            <span v-if="state.status === 'running'">{{ etaText }}</span>
          </p>
        </section>

        <!-- Schritte -->
        <ol class="timeline">
          <li v-for="(key, i) in STEP_ORDER" :key="key" class="step" :class="`step--${state.steps[key].status}`">
            <span class="step__marker">
              <span v-if="state.steps[key].status === 'done'">✓</span>
              <span v-else-if="state.steps[key].status === 'failed'">!</span>
              <span v-else-if="state.steps[key].status === 'running'" class="step__spin"></span>
              <span v-else>{{ i + 1 }}</span>
            </span>
            <div class="step__body">
              <div class="step__row">
                <span class="step__label">{{ t(`steps.${key}`) }}</span>
                <span v-if="state.steps[key].status === 'running' && state.steps[key].progress" class="step__pct">{{ Math.round(state.steps[key].progress) }} %</span>
              </div>
              <p v-if="state.steps[key].status === 'failed'" class="step__detail">{{ t('hist.sFailed') }}</p>
              <p v-else-if="state.steps[key].detail" class="step__detail">{{ state.steps[key].detail }}</p>
              <p v-else-if="state.steps[key].status === 'running'" class="step__detail step__detail--hint">{{ t(HINTS[key]) }}</p>
              <div v-if="state.steps[key].status === 'running'" class="step__bar">
                <div class="step__bar-fill" :style="{ width: (state.steps[key].progress || 0) + '%' }"></div>
              </div>
            </div>
          </li>
        </ol>

        <!-- Aktionen -->
        <section class="actions">
          <router-link v-if="state.report_id" :to="`/report/${state.report_id}`" class="btn btn--primary">{{ t('run.openReport') }}</router-link>
          <router-link v-if="state.simulation_id" :to="`/simulation/${state.simulation_id}/start`" class="btn">{{ t('run.openSim') }}</router-link>
          <router-link v-if="state.project_id" :to="`/process/${state.project_id}?view=graph`" class="btn">{{ t('run.openGraph') }}</router-link>
          <a v-if="state.simulation_id && state.status !== 'running'" :href="`/api/simulation/${state.simulation_id}/export`" class="btn" download>{{ t('run.export') }}</a>
        </section>

        <p v-if="state.status === 'running'" class="hint">
          {{ t('run.closeHint') }}
        </p>
      </template>
    </main>

    <MobileStickyBar
      v-if="stickyPrimary"
      :primary-label="stickyPrimary.label"
      :secondary-label="stickySecondary ? stickySecondary.label : ''"
      @primary-click="router.push(stickyPrimary.to)"
      @secondary-click="stickySecondary && router.push(stickySecondary.to)"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import MobileStickyBar from '../components/MobileStickyBar.vue'
import { getPipeline, STEP_ORDER } from '../api/pipeline'

const props = defineProps({ pipelineId: { type: String, required: true } })
const router = useRouter()
const { t, locale } = useI18n()
const state = ref(null)
const loadError = ref('')
const cleanedUp = ref(false)
let timer = null

const stickyPrimary = computed(() => {
  if (!state.value) return null
  if (state.value.report_id) return { label: t('run.openReport'), to: `/report/${state.value.report_id}` }
  if (state.value.simulation_id) return { label: t('run.openSim'), to: `/simulation/${state.value.simulation_id}/start` }
  return null
})
const stickySecondary = computed(() => {
  if (!state.value?.report_id || !state.value?.simulation_id) return null
  return { label: t('run.openSim'), to: `/simulation/${state.value.simulation_id}/start` }
})

// Gewichte nach typischer Dauer, Summe 100
const WEIGHTS = { ontology: 10, graph: 15, create: 2, prepare: 13, simulate: 50, report: 10 }
const HINTS = { ontology: 'steps.hOntology', graph: 'steps.hGraph', create: 'steps.hCreate', prepare: 'steps.hPrepare', simulate: 'steps.hSimulate', report: 'steps.hReport' }

const overall = computed(() => {
  if (!state.value) return 0
  if (state.value.status === 'completed') return 100
  let sum = 0
  for (const k of STEP_ORDER) {
    const s = state.value.steps[k]
    if (s.status === 'done') sum += WEIGHTS[k]
    else if (s.status === 'running') sum += WEIGHTS[k] * Math.min(100, s.progress || 0) / 100
  }
  return Math.round(sum)
})
const currentLabel = computed(() => (state.value?.current_step ? t(`steps.${state.value.current_step}`) : t('run.starting')))
const currentDetail = computed(() => state.value?.steps?.[state.value.current_step]?.detail || '')

// Grobe Restzeit: bisher verbrauchte Zeit hochgerechnet auf den Gesamtfortschritt
const etaText = computed(() => {
  if (!state.value || overall.value < 5) return t('run.eta')
  const elapsed = (Date.now() - new Date(state.value.created_at).getTime()) / 1000
  const remaining = elapsed * (100 - overall.value) / overall.value
  if (remaining < 90) return t('run.etaSoon')
  if (remaining < 3600) return t('run.etaMin', { n: Math.round(remaining / 60) })
  return t('run.etaH', { n: (remaining / 3600).toFixed(1) })
})

const fmtDate = (iso) => { try { return new Date(iso).toLocaleString(locale.value === 'en' ? 'en-GB' : 'de-DE', { dateStyle: 'medium', timeStyle: 'short' }) } catch (e) { return '' } }
const fmtDuration = (a, b) => {
  const s = Math.max(0, (new Date(b) - new Date(a)) / 1000)
  if (s < 3600) return t('run.min', { n: Math.round(s / 60) })
  return t('run.hmin', { h: Math.floor(s / 3600), m: Math.round((s % 3600) / 60) })
}

const load = async () => {
  try {
    const res = await getPipeline(props.pipelineId)
    state.value = res.data
    loadError.value = ''
    cleanedUp.value = false
    if (state.value.status !== 'running') { clearInterval(timer); timer = null }
  } catch (err) {
    if (err.response?.status === 404) {
      state.value = null
      loadError.value = ''
      cleanedUp.value = true
      clearInterval(timer)
      timer = null
      return
    }
    if (!state.value) loadError.value = t('run.notFound', { msg: err.response?.data?.error || err.message })
  }
}

watch(() => state.value?.simulation_id, (id) => { if (id) try { localStorage.setItem('mirofish:lastSimulation', id) } catch (e) {} })
watch(() => state.value?.report_id, (id) => { if (id) try { localStorage.setItem('mirofish:lastReport', id) } catch (e) {} })

onMounted(() => { load(); timer = setInterval(load, 5000) })
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.run { min-height: 100vh; background: var(--color-bg-canvas); color: var(--color-text-primary); }
.topbar { position: sticky; top: 0; z-index: 20; display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; padding: 10px 16px; background: color-mix(in srgb, var(--color-bg-canvas) 86%, transparent); backdrop-filter: saturate(180%) blur(12px); border-bottom: 1px solid var(--color-border-subtle); }
.back { color: var(--color-brand-primary); text-decoration: none; font-size: 16px; padding: 8px 0; min-height: 44px; display: inline-flex; align-items: center; }
.topbar__title { font-family: var(--font-heading); font-weight: 600; font-size: 16px; }
.main { max-width: 720px; margin: 0 auto; padding: 20px 16px 48px; }

.skeleton { display: flex; flex-direction: column; gap: 12px; padding-top: 8px; }
.sk { border-radius: 10px; background: linear-gradient(90deg, var(--color-bg-surface-subtle) 25%, var(--color-bg-surface) 50%, var(--color-bg-surface-subtle) 75%); background-size: 200% 100%; animation: shimmer 1.4s infinite; }
.sk--title { height: 28px; width: 70%; } .sk--line { height: 14px; width: 45%; } .sk--block { height: 160px; }
@keyframes shimmer { to { background-position: -200% 0; } }

.eyebrow { font-size: 13px; color: var(--color-text-muted); margin: 0 0 6px; }
.title { font-family: var(--font-heading); font-size: clamp(20px, 5vw, 28px); line-height: 1.25; margin: 0 0 16px; letter-spacing: -0.01em; }

.status { display: flex; align-items: center; gap: 14px; padding: 14px 16px; border-radius: 14px; background: var(--color-bg-surface); border: 1px solid var(--color-border-subtle); }
.status div { display: flex; flex-direction: column; min-width: 0; }
.status strong { font-size: 16px; }
.status small { font-size: 13px; color: var(--color-text-muted); }
.status--completed { background: var(--color-success-bg); border-color: var(--color-success-border); }
.status--failed { background: var(--color-error-bg); border-color: var(--color-error-border); }
.orb { position: relative; width: 36px; height: 36px; flex: none; }
.orb span { position: absolute; inset: 0; border-radius: 50%; border: 2px solid var(--color-brand-primary); opacity: 0; animation: ripple 2.1s ease-out infinite; }
.orb span:nth-child(2) { animation-delay: .7s; } .orb span:nth-child(3) { animation-delay: 1.4s; }
.orb::after { content: ''; position: absolute; inset: 12px; border-radius: 50%; background: var(--color-brand-primary); }
@keyframes ripple { 0% { transform: scale(.35); opacity: .9; } 100% { transform: scale(1.1); opacity: 0; } }
.check, .cross { width: 36px; height: 36px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-weight: 700; flex: none; }
.check { background: var(--color-success-text); color: var(--color-brand-on-primary); } .cross { background: var(--color-error-text); color: var(--color-brand-on-primary); }

.bar { height: 10px; border-radius: 999px; background: var(--color-border-subtle); overflow: hidden; margin-top: 14px; }
.bar__fill { height: 100%; background: var(--color-brand-primary); border-radius: 999px; transition: width .6s ease; }
.bar__fill--live { background-image: linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,.35) 50%, rgba(255,255,255,0) 100%); background-size: 200% 100%; animation: shimmer 1.8s linear infinite; }
.bar__meta { display: flex; justify-content: space-between; font-size: 13px; color: var(--color-text-muted); margin: 6px 0 0; font-variant-numeric: tabular-nums; }

.timeline { list-style: none; margin: 24px 0 0; padding: 0; }
.step { display: flex; gap: 14px; position: relative; padding-bottom: 18px; }
.step:not(:last-child)::before { content: ''; position: absolute; left: 15px; top: 32px; bottom: 0; width: 2px; background: var(--color-border-subtle); }
.step--done:not(:last-child)::before { background: var(--color-success-text); }
.step__marker { width: 32px; height: 32px; border-radius: 50%; flex: none; display: inline-flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; background: var(--color-bg-surface-raised); border: 2px solid var(--color-border-default); color: var(--color-text-muted); position: relative; z-index: 1; }
.step--done .step__marker { background: var(--color-success-text); border-color: var(--color-success-text); color: var(--color-brand-on-primary); }
.step--running .step__marker { border-color: var(--color-brand-primary); color: var(--color-brand-primary); }
.step--failed .step__marker { background: var(--color-error-text); border-color: var(--color-error-text); color: var(--color-brand-on-primary); }
.step__spin { width: 14px; height: 14px; border: 2px solid color-mix(in srgb, var(--color-brand-primary) 30%, transparent); border-top-color: var(--color-brand-primary); border-radius: 50%; animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.step__body { flex: 1; min-width: 0; padding-top: 5px; }
.step__row { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; }
.step__label { font-weight: 600; font-size: 15px; }
.step--pending .step__label { color: var(--color-border-strong); font-weight: 500; }
.step__pct { font-size: 13px; color: var(--color-brand-primary); font-variant-numeric: tabular-nums; }
.step__detail { margin: 4px 0 0; font-size: 13px; color: var(--color-text-secondary); }
.step__detail--hint { color: var(--color-text-muted); }
.step__bar { height: 4px; border-radius: 999px; background: var(--color-border-subtle); margin-top: 8px; overflow: hidden; }
.step__bar-fill { height: 100%; background: var(--color-brand-primary); transition: width .6s ease; }

.actions { display: flex; flex-direction: column; gap: 10px; margin-top: 8px; }
.btn { display: flex; align-items: center; justify-content: center; min-height: 48px; border-radius: 12px; border: 1px solid var(--color-border-subtle); background: var(--color-bg-surface-raised); color: inherit; text-decoration: none; font-weight: 600; font-size: 15px; }
.btn--primary { background: var(--color-brand-primary); border-color: var(--color-brand-primary); color: var(--color-brand-on-primary); }
.hint { margin: 18px 0 0; font-size: 13px; color: var(--color-text-secondary); text-align: center; line-height: 1.5; }
.error { color: var(--color-error-text); }
.cleaned { text-align: center; padding: 32px 8px; display: flex; flex-direction: column; align-items: center; gap: 16px; }
.cleaned p { margin: 0; font-size: 16px; line-height: 1.5; }

@media (max-width: 768px) {
  .main { padding-bottom: calc(120px + env(safe-area-inset-bottom, 0px)); }
  .actions { display: none; }
}

@media (min-width: 769px) {
  .main { padding: 32px 24px 64px; }
  .actions { flex-direction: row; flex-wrap: wrap; }
  .actions .btn { flex: 1 1 200px; }
}

@media (min-width: 1024px) {
  .main {
    max-width: 860px;
    padding: 40px 32px 80px;
  }

  .timeline {
    margin-top: 32px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .orb span,
  .step__spin,
  .bar__fill--live,
  .sk { animation: none !important; }
}
</style>
