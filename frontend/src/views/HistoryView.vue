<template>
  <div class="page">
    <AppHeader />
    <main class="main">
      <div class="page__head">
        <h1 class="page__title">{{ t('hist.title') }}</h1>
        <router-link to="/" class="btn btn--primary btn--sm">{{ t('hist.new') }}</router-link>
      </div>

      <div v-if="loading && !items.length" class="list" aria-busy="true">
        <div v-for="i in 3" :key="i" class="row row--skeleton"><div class="sk sk--t"></div><div class="sk sk--s"></div></div>
      </div>

      <div v-else-if="!items.length" class="empty">
        <img src="/logo-mark.svg" alt="" width="48" height="48" />
        <p>{{ t('hist.empty') }}</p>
        <router-link to="/" class="btn btn--primary">{{ t('hist.emptyCta') }}</router-link>
      </div>

      <section v-else class="list">
        <article v-for="it in items" :key="it.key" class="row" :class="{ 'row--running': it.state === 'running' }">
          <component :is="it.href ? 'router-link' : 'div'" :to="it.href" class="row__main">
            <span class="chip" :class="`chip--${it.state}`">
              <i v-if="it.state === 'running'" class="chip__pulse"></i>{{ it.stateLabel }}
            </span>
            <h2 class="row__title">{{ it.title }}</h2>
            <p class="row__meta">{{ it.date }}<template v-if="it.meta"> · {{ it.meta }}</template></p>
            <div v-if="it.state === 'running' && it.progress != null" class="row__bar"><div :style="{ width: it.progress + '%' }"></div></div>
          </component>
          <div class="row__actions">
            <router-link v-if="it.reportHref" :to="it.reportHref" class="act" :title="t('run.openReport')">
              <svg viewBox="0 0 24 24"><path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4M9 12h6M9 16h6"/></svg><span>{{ t('hist.report') }}</span>
            </router-link>
            <a v-if="it.exportHref" :href="it.exportHref" class="act" :title="t('hist.exportTitle')" download>
              <svg viewBox="0 0 24 24"><path d="M12 4v11m0 0 4-4m-4 4-4-4"/><path d="M4 17v2a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-2"/></svg><span>{{ t('hist.export') }}</span>
            </a>
            <button v-if="it.simulationId && it.state !== 'running'" type="button" class="act act--danger" @click="askDelete(it)">
              <svg viewBox="0 0 24 24"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/></svg><span>{{ t('hist.delete') }}</span>
            </button>
          </div>
        </article>
      </section>
      <p v-if="error" class="error" role="alert">{{ error }}</p>
    </main>

    <ConfirmSheet :open="!!pending" :title="t('hist.confirmTitle')" :text="pending ? t('hist.confirmText', { title: pending.title }) : ''"
                  :confirm-label="t('hist.delete')" :busy="deleting" danger @confirm="doDelete" @close="pending = null" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import AppHeader from '../components/AppHeader.vue'
import ConfirmSheet from '../components/ConfirmSheet.vue'
import { getSimulationHistory, deleteSimulation } from '../api/simulation'
import { listPipelines } from '../api/pipeline'

const { t, locale } = useI18n()
const items = ref([])
const loading = ref(true)
const error = ref('')
const pending = ref(null)
const deleting = ref(false)
let timer = null

const fmt = (iso) => { try { return new Date(iso).toLocaleString(locale.value === 'en' ? 'en-GB' : 'de-DE', { dateStyle: 'medium', timeStyle: 'short' }) } catch (e) { return '' } }
const stateLabel = (s) => t({ running: 'hist.sRunning', completed: 'hist.sCompleted', failed: 'hist.sFailed', idle: 'hist.sIdle', progress: 'hist.sProgress' }[s] || 'hist.sIdle')
const stepLabel = (s) => (s ? t(`steps.${s}`) : t('run.preparing'))

const load = async () => {
  try {
    const [pipes, sims] = await Promise.all([
      listPipelines().then(r => r?.data || []).catch(() => []),
      getSimulationHistory().then(r => r?.data || []).catch(() => [])
    ])
    const bySim = new Map(pipes.filter(p => p.simulation_id).map(p => [p.simulation_id, p]))
    const out = []
    // Laufende oder gescheiterte Durchläufe, die noch keine Simulation haben
    for (const p of pipes) {
      if (p.simulation_id && sims.some(s => s.simulation_id === p.simulation_id)) continue
      if (p.status === 'completed') continue
      out.push({
        key: p.pipeline_id, title: p.requirement, date: fmt(p.created_at), state: p.status === 'running' ? 'running' : 'failed',
        stateLabel: stateLabel(p.status === 'running' ? 'running' : 'failed'), meta: p.status === 'running' ? stepLabel(p.current_step) : (p.error || '').slice(0, 80),
        href: `/run/${p.pipeline_id}`, created: p.created_at
      })
    }
    for (const s of sims) {
      const p = bySim.get(s.simulation_id)
      const running = p?.status === 'running'
      const done = (s.current_round || 0) > 0 && s.current_round >= (s.total_rounds || 0) && (s.total_rounds || 0) > 0
      const state = running ? 'running' : s.report_id ? 'completed' : done ? 'completed' : (s.current_round || 0) > 0 ? 'progress' : p?.status === 'failed' ? 'failed' : 'idle'
      const title = s.simulation_requirement || s.project_name || t('start.untitled')
      out.push({
        key: s.simulation_id, simulationId: s.simulation_id, title, date: fmt(s.created_at), state, stateLabel: stateLabel(state),
        meta: running ? stepLabel(p.current_step) : s.total_rounds ? t('hist.rounds', { cur: s.current_round || 0, total: s.total_rounds }) : '',
        progress: running ? null : undefined,
        href: running ? `/run/${p.pipeline_id}` : s.report_id ? `/report/${s.report_id}` : `/simulation/${s.simulation_id}`,
        reportHref: s.report_id ? `/report/${s.report_id}` : null,
        exportHref: `/api/simulation/${s.simulation_id}/export`, created: s.created_at
      })
    }
    out.sort((a, b) => (a.state === 'running') - (b.state === 'running') || new Date(a.created) - new Date(b.created)).reverse()
    items.value = out
    error.value = ''
  } catch (e) {
    error.value = t('hist.loadFailed')
  } finally { loading.value = false }
}

const askDelete = (it) => { pending.value = it }
const doDelete = async () => {
  if (!pending.value) return
  deleting.value = true
  try {
    await deleteSimulation(pending.value.simulationId)
    items.value = items.value.filter(i => i.key !== pending.value.key)
    pending.value = null
  } catch (e) {
    error.value = t('hist.deleteFailed', { msg: e.response?.data?.error || e.message })
  } finally { deleting.value = false }
}

onMounted(() => { load(); timer = setInterval(load, 15000) })
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.page { min-height: 100vh; background: var(--color-bg-canvas); color: var(--color-text-primary); }
.main { max-width: 760px; margin: 0 auto; padding: 20px 16px 32px; }
.page__head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
.page__title { font-family: var(--font-heading); font-size: 26px; margin: 0; letter-spacing: -0.01em; }
.list { display: flex; flex-direction: column; gap: 10px; }
.row { display: flex; flex-direction: column; background: var(--color-bg-surface-raised); border: 1px solid var(--color-border-subtle); border-radius: 16px; overflow: hidden; box-shadow: var(--shadow-sm); }
.row--running { border-color: var(--color-brand-border); }
.row__main { display: block; padding: 14px 16px 12px; text-decoration: none; color: inherit; }
.row__title { font-family: var(--font-body); font-size: 15px; font-weight: 600; line-height: 1.35; margin: 8px 0 4px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.row__meta { margin: 0; font-size: 12px; color: var(--color-text-muted); }
.row__bar { height: 3px; background: var(--color-border-subtle); border-radius: 999px; margin-top: 10px; overflow: hidden; }
.row__bar div { height: 100%; background: var(--color-brand-primary); }
.chip { display: inline-flex; align-items: center; gap: 6px; font-size: 11px; font-weight: 600; letter-spacing: .02em; padding: 3px 8px; border-radius: 999px; background: var(--color-bg-surface-subtle); color: var(--color-text-secondary); }
.chip--running { background: var(--color-brand-subtle); color: var(--color-brand-primary); }
.chip--completed { background: var(--color-success-bg); color: var(--color-success-text); }
.chip--failed { background: var(--color-error-bg); color: var(--color-error-text); }
.chip--progress { background: var(--color-warning-bg); color: var(--color-warning-text); }
.chip__pulse { width: 7px; height: 7px; border-radius: 50%; background: currentColor; animation: pulse 1.6s ease-in-out infinite; }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: .35; } }
.row__actions { display: flex; border-top: 1px solid var(--color-border-subtle); }
.row__actions:empty { display: none; }
.act { flex: 1; min-height: 44px; border-radius: 0; box-shadow: none; -webkit-appearance: none; appearance: none; display: inline-flex; align-items: center; justify-content: center; gap: 6px; border: 0; background: transparent; color: var(--color-text-secondary); font: inherit; font-size: 13px; font-weight: 500; cursor: pointer; text-decoration: none; }
.act + .act { border-left: 1px solid var(--color-border-subtle); }
.act svg { width: 18px; height: 18px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.act:hover { background: var(--color-bg-surface-subtle); }
.act--danger { color: var(--color-error-text); }
.act--danger:hover { background: var(--color-error-bg); }
.empty { text-align: center; padding: 48px 16px; color: var(--color-text-muted); display: flex; flex-direction: column; align-items: center; gap: 14px; }
.btn { display: inline-flex; align-items: center; justify-content: center; min-height: 44px; padding: 0 18px; border-radius: 12px; border: 1px solid var(--color-border-subtle); background: var(--color-bg-surface-raised); color: inherit; text-decoration: none; font-weight: 600; font-size: 15px; white-space: nowrap; }
.btn--primary { background: var(--color-brand-primary); border-color: var(--color-brand-primary); color: var(--color-brand-on-primary); }
.btn--sm { min-height: 38px; font-size: 14px; padding: 0 14px; }
.error { color: var(--color-error-text); font-size: 14px; margin-top: 12px; }
.row--skeleton { padding: 16px; flex-direction: column; gap: 10px; }
.sk { border-radius: 8px; background: linear-gradient(90deg, var(--color-bg-surface-subtle) 25%, var(--color-bg-surface) 50%, var(--color-bg-surface-subtle) 75%); background-size: 200% 100%; animation: shimmer 1.4s infinite; }
.sk--t { height: 18px; width: 70%; } .sk--s { height: 12px; width: 40%; }
@keyframes shimmer { to { background-position: -200% 0; } }
@media (min-width: 769px) {
  .main { padding: 32px 24px 64px; max-width: 880px; }
}
</style>
