<template>
  <div class="page">
    <AppHeader />
    <main class="main" v-if="data">
      <header class="head">
        <p class="eyebrow">{{ t('ensemble.eyebrow') }}</p>
        <h1 class="title">{{ data.question || t('ensemble.untitled') }}</h1>
        <p class="meta">
          <span class="chip" :class="`chip--${data.status}`">{{ statusLabel }}</span>
          <span v-if="data.runs">{{ t('ensemble.runsHours', { runs: data.runs, hours: data.hours }) }}</span>
          <span v-if="etaLabel">{{ etaLabel }}</span>
        </p>
        <p v-if="data.current" class="current">
          {{ t('ensemble.current', { variant: currentVariantLabel, run: data.current.run, round: data.current.round }) }}
        </p>
        <p v-if="data.error" class="error" role="alert">{{ data.error }}</p>
      </header>

      <section class="progress" v-if="variants.length" :aria-label="t('ensemble.progressAria')">
        <div v-for="v in variants" :key="v.key" class="prog">
          <div class="prog__row">
            <span class="prog__label">{{ variantLabel(v) }}</span>
            <span class="prog__meta mono">{{ v.done }}/{{ v.total }}</span>
          </div>
          <div class="prog__track" role="progressbar" :aria-valuenow="v.done" :aria-valuemin="0" :aria-valuemax="v.total">
            <div class="prog__fill" :class="{ 'prog__fill--pulse': v.status === 'running' }" :style="{ width: pct(v) + '%' }"></div>
          </div>
        </div>
      </section>

      <!-- Desktop table -->
      <section v-if="checklist.length" class="results results--table" :aria-label="t('ensemble.resultsAria')">
        <table class="grid">
          <thead>
            <tr>
              <th scope="col">{{ t('ensemble.outcome') }}</th>
              <th v-for="v in variants" :key="'h-' + v.key" scope="col">{{ variantLabel(v) }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in checklist" :key="item.id" :class="{ 'row--material': item.in_material }">
              <th scope="row" class="outcome">
                <span>{{ item.text_de && locale === 'de' ? item.text_de : (item.text_en || item.text_de || item.id) }}</span>
                <details v-if="item.in_material" class="material">
                  <summary>{{ t('ensemble.alreadyInMaterial') }}</summary>
                  <p v-if="item.material_snippet" class="snippet">{{ item.material_snippet }}</p>
                </details>
              </th>
              <td v-for="v in variants" :key="item.id + '-' + v.key">
                <CellStat :stat="cell(v.key, item.id)" :t="t" />
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- Mobile cards -->
      <section v-if="checklist.length" class="results results--cards" :aria-label="t('ensemble.resultsAria')">
        <article v-for="item in checklist" :key="'c-' + item.id" class="card" :class="{ 'card--material': item.in_material }">
          <h2 class="card__title">{{ item.text_de && locale === 'de' ? item.text_de : (item.text_en || item.text_de || item.id) }}</h2>
          <details v-if="item.in_material" class="material">
            <summary>{{ t('ensemble.alreadyInMaterial') }}</summary>
            <p v-if="item.material_snippet" class="snippet">{{ item.material_snippet }}</p>
          </details>
          <div v-for="v in variants" :key="'cv-' + item.id + v.key" class="card__row">
            <span class="card__var">{{ variantLabel(v) }}</span>
            <CellStat :stat="cell(v.key, item.id)" :t="t" />
          </div>
        </article>
      </section>

      <section v-if="comparisons.length" class="compare" aria-labelledby="cmp-h">
        <h2 id="cmp-h" class="section-title">{{ t('ensemble.diffTitle') }}</h2>
        <ul class="compare__list">
          <li v-for="(c, i) in comparisons" :key="i">
            <strong>{{ compareVariantLabel(c.variant) }}</strong>
            · {{ outcomeText(c.outcome_id) }}:
            <span class="mono">{{ fmtDiff(c.diff) }}</span>
            <span class="ci">({{ pct01(c.ci_low) }}–{{ pct01(c.ci_high) }})</span>
            — {{ interpretDiff(c) }}
          </li>
        </ul>
      </section>

      <aside class="help">
        <h2 class="section-title">{{ t('ensemble.ciHelpTitle') }}</h2>
        <p>{{ t('ensemble.ciHelpBody') }}</p>
      </aside>
    </main>

    <main v-else-if="loadError" class="main">
      <p class="error" role="alert">{{ loadError }}</p>
    </main>
    <main v-else class="main"><p class="muted">{{ t('common.loading') }}</p></main>

    <MobileStickyBar
      v-if="data && (canCancel || canDelete)"
      :primary-label="canCancel ? t('ensemble.cancel') : t('ensemble.delete')"
      :primary-loading="busy"
      @primary-click="canCancel ? doCancel() : askDelete()"
    />

    <ConfirmSheet
      :open="confirmDelete"
      :title="t('ensemble.deleteTitle')"
      :text="t('ensemble.deleteText')"
      :confirm-label="t('ensemble.delete')"
      :busy="busy"
      danger
      @confirm="doDelete"
      @close="confirmDelete = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, h } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import MobileStickyBar from '../components/MobileStickyBar.vue'
import ConfirmSheet from '../components/ConfirmSheet.vue'
import { getEnsemble, cancelEnsemble, deleteEnsemble } from '../api/ensemble'

const props = defineProps({ ensembleId: String })
const { t, locale } = useI18n()
const router = useRouter()

const data = ref(null)
const loadError = ref('')
const busy = ref(false)
const confirmDelete = ref(false)
let timer = null

const variants = computed(() => data.value?.variants || [])
const checklist = computed(() => data.value?.checklist || [])
const comparisons = computed(() => data.value?.comparisons || [])
const canCancel = computed(() => ['queued', 'running'].includes(data.value?.status))
const canDelete = computed(() => ['completed', 'failed', 'cancelled'].includes(data.value?.status))
const statusLabel = computed(() => t(`ensemble.status.${data.value?.status || 'queued'}`))
const currentVariantLabel = computed(() => {
  const key = data.value?.current?.variant
  const v = variants.value.find((x) => x.key === key)
  return v ? variantLabel(v) : key || '—'
})
const etaLabel = computed(() => {
  const s = data.value?.eta_seconds
  if (s == null) return ''
  return t('ensemble.eta', { time: formatDuration(s) })
})

function variantLabel(v) {
  if (!v) return '—'
  return locale.value === 'en' ? (v.label_en || v.label_de || v.key) : (v.label_de || v.label_en || v.key)
}
function compareVariantLabel(key) {
  const v = variants.value.find((x) => x.key === key)
  return v ? variantLabel(v) : key
}
function outcomeText(id) {
  const item = checklist.value.find((x) => x.id === id)
  if (!item) return id
  return locale.value === 'en' ? (item.text_en || item.text_de || id) : (item.text_de || item.text_en || id)
}
function cell(variantKey, outcomeId) {
  return data.value?.results?.[variantKey]?.[outcomeId] || null
}
function pct(v) {
  if (!v?.total) return 0
  return Math.min(100, Math.round((100 * (v.done || 0)) / v.total))
}
function pct01(x) {
  if (x == null || Number.isNaN(x)) return '—'
  return Math.round(x * 100) + ' %'
}
function fmtDiff(d) {
  if (d == null) return '—'
  const p = Math.round(d * 100)
  return (p > 0 ? '+' : '') + p + ' %'
}
function interpretDiff(c) {
  if (c.ci_low <= 0 && c.ci_high >= 0) return t('ensemble.diffNone')
  if (c.diff > 0) return t('ensemble.diffHigher')
  return t('ensemble.diffLower')
}
function formatDuration(sec) {
  const s = Math.max(0, Math.round(sec))
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  if (h > 0) return t('ensemble.durationHm', { h, m })
  return t('ensemble.durationM', { m: Math.max(1, m) })
}

const CellStat = {
  props: { stat: Object, t: Function },
  setup(p) {
    return () => {
      const st = p.stat
      if (!st) return h('span', { class: 'muted' }, '—')
      const rate = Math.round((st.rate ?? 0) * 100)
      const lo = Math.round((st.ci_low ?? 0) * 100)
      const hi = Math.round((st.ci_high ?? 0) * 100)
      const barLo = Math.max(0, Math.min(100, lo))
      const barHi = Math.max(barLo, Math.min(100, hi))
      return h('div', { class: 'stat' }, [
        h('div', { class: 'stat__text' }, p.t('ensemble.cell', { yes: st.yes, n: st.n, rate, lo, hi })),
        h('div', { class: 'stat__bar', 'aria-hidden': 'true' }, [
          h('i', { style: { left: barLo + '%', width: Math.max(2, barHi - barLo) + '%' } }),
        ]),
        st.evidence?.length
          ? h('details', { class: 'evidence' }, [
              h('summary', p.t('ensemble.evidence', { count: st.evidence.length })),
              h(
                'ul',
                st.evidence.map((e, i) =>
                  h('li', { key: i }, [
                    h('span', { class: 'mono' }, `#${e.run} · ${e.platform || '—'} · ${e.agent || '—'}`),
                    h('p', e.text || ''),
                  ]),
                ),
              ),
            ])
          : null,
      ])
    }
  },
}

async function refresh() {
  try {
    const res = await getEnsemble(props.ensembleId)
    data.value = res?.data || null
    loadError.value = ''
    if (canCancel.value) schedule()
    else clearTimer()
  } catch (e) {
    loadError.value = e.message || t('common.error')
  }
}
function schedule() {
  clearTimer()
  timer = setTimeout(refresh, 2500)
}
function clearTimer() {
  if (timer) {
    clearTimeout(timer)
    timer = null
  }
}

async function doCancel() {
  busy.value = true
  try {
    await cancelEnsemble(props.ensembleId)
    await refresh()
  } catch (e) {
    loadError.value = e.message || t('common.error')
  } finally {
    busy.value = false
  }
}
function askDelete() {
  confirmDelete.value = true
}
async function doDelete() {
  busy.value = true
  try {
    await deleteEnsemble(props.ensembleId)
    confirmDelete.value = false
    router.push('/')
  } catch (e) {
    loadError.value = e.message || t('common.error')
  } finally {
    busy.value = false
  }
}

onMounted(refresh)
onUnmounted(clearTimer)
</script>

<style scoped>
.page { min-height: 100vh; background: var(--color-bg-canvas); color: var(--color-text-primary); }
.main { max-width: 1100px; margin: 0 auto; padding: 20px 16px 120px; }
.head { margin-bottom: 1.5rem; }
.eyebrow { margin: 0 0 4px; font-size: 12px; color: var(--color-text-muted); text-transform: uppercase; letter-spacing: 0.04em; }
.title { font-family: var(--font-heading); font-size: clamp(22px, 5vw, 30px); margin: 0 0 8px; line-height: 1.25; }
.meta { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; color: var(--color-text-secondary); font-size: 14px; margin: 0; }
.current { margin: 8px 0 0; color: var(--color-text-secondary); font-size: 14px; }
.chip { display: inline-flex; align-items: center; min-height: 28px; padding: 0 10px; border-radius: 999px; font-size: 12px; font-weight: 600; background: var(--color-bg-surface-subtle); border: 1px solid var(--color-border-subtle); }
.chip--running, .chip--queued { color: var(--color-warning-text); }
.chip--completed { color: var(--color-success-text); }
.chip--failed, .chip--cancelled { color: var(--color-error-text); }
.error { color: var(--color-error-text); margin-top: 8px; }
.muted { color: var(--color-text-muted); }
.mono { font-family: var(--font-mono, ui-monospace, monospace); }

.progress { display: grid; gap: 12px; margin-bottom: 1.75rem; }
.prog__row { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px; }
.prog__label { font-weight: 600; }
.prog__meta { color: var(--color-text-muted); }
.prog__track { height: 8px; border-radius: 999px; background: var(--color-bg-surface-subtle); overflow: hidden; }
.prog__fill { height: 100%; background: var(--color-brand-primary); border-radius: inherit; transition: width 0.4s ease; }
.prog__fill--pulse { animation: pulse-bar 1.2s ease-in-out infinite; }
@keyframes pulse-bar { 50% { opacity: 0.65; } }

.section-title { font-family: var(--font-heading); font-size: 1.1rem; margin: 0 0 0.6rem; }
.compare { margin: 1.75rem 0; }
.compare__list { margin: 0; padding-left: 1.1rem; color: var(--color-text-secondary); font-size: 14px; line-height: 1.55; }
.compare__list .ci { color: var(--color-text-muted); }
.help { margin-top: 2rem; padding: 1rem 1.1rem; border: 1px solid var(--color-border-subtle); border-radius: var(--radius-md, 8px); background: var(--color-bg-surface-raised); color: var(--color-text-secondary); font-size: 14px; line-height: 1.55; }
.help p { margin: 0; }

.material { margin-top: 6px; font-size: 13px; }
.material summary { cursor: pointer; min-height: 44px; display: inline-flex; align-items: center; color: var(--color-warning-text); font-weight: 600; }
.snippet { margin: 6px 0 0; padding: 8px 10px; background: var(--color-bg-surface-subtle); border-radius: 8px; color: var(--color-text-secondary); }

.results--table { display: none; overflow-x: auto; }
.grid { width: 100%; border-collapse: collapse; font-size: 13px; }
.grid th, .grid td { border: 1px solid var(--color-border-subtle); padding: 10px; vertical-align: top; text-align: left; }
.grid thead th { background: var(--color-bg-surface-subtle); font-family: var(--font-heading); }
.outcome { font-weight: 600; min-width: 160px; }
.row--material { background: color-mix(in srgb, var(--color-warning-text) 6%, transparent); }

.results--cards { display: grid; gap: 12px; }
.card { padding: 14px; border: 1px solid var(--color-border-default); border-radius: var(--radius-md, 8px); background: var(--color-bg-surface-raised); }
.card--material { border-color: color-mix(in srgb, var(--color-warning-text) 45%, var(--color-border-default)); }
.card__title { font-family: var(--font-heading); font-size: 1rem; margin: 0 0 8px; }
.card__row { display: grid; gap: 4px; padding: 10px 0; border-top: 1px solid var(--color-border-subtle); }
.card__var { font-size: 12px; font-weight: 600; color: var(--color-text-muted); }

:deep(.stat__text) { font-size: 13px; line-height: 1.4; }
:deep(.stat__bar) { position: relative; height: 6px; margin-top: 6px; background: var(--color-bg-surface-subtle); border-radius: 999px; overflow: hidden; }
:deep(.stat__bar i) { position: absolute; top: 0; bottom: 0; background: var(--color-brand-primary); border-radius: inherit; opacity: 0.75; }
:deep(.evidence) { margin-top: 6px; font-size: 12px; }
:deep(.evidence summary) { cursor: pointer; min-height: 44px; display: inline-flex; align-items: center; color: var(--color-text-secondary); }
:deep(.evidence ul) { margin: 6px 0 0; padding-left: 1rem; color: var(--color-text-secondary); }
:deep(.evidence p) { margin: 2px 0 8px; }

@media (min-width: 769px) {
  .results--table { display: block; }
  .results--cards { display: none; }
  .main { padding: 28px 24px 80px; }
}
@media (prefers-reduced-motion: reduce) {
  .prog__fill { transition: none; }
  .prog__fill--pulse { animation: none; }
}
</style>
