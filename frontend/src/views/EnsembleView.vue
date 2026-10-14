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
          <span v-if="data.minutes_per_round">{{ t('ensemble.minutesPerRound', { minutes: data.minutes_per_round }) }}</span>
          <span v-if="etaLabel">{{ etaLabel }}</span>
        </p>
        <p v-if="data.current" class="current">
          {{ t('ensemble.current', { variant: currentVariantLabel, run: data.current.run, round: data.current.round }) }}
        </p>
        <p v-if="data.error" class="error" role="alert">{{ data.error }}</p>
      </header>

      <ReliabilityHint
        storage-key="ensemble"
        :message="t('reliability.ensembleHint')"
        :link-label="t('reliability.link')"
        link-to="/verlaesslichkeit"
        :dismiss-label="t('reliability.dismiss')"
      />

      <aside class="meaning" aria-labelledby="meaning-title">
        <h2 id="meaning-title" class="meaning__title">{{ t('ensemble.meaningTitle') }}</h2>
        <p>{{ t('ensemble.meaningBody') }}</p>
        <p>{{ t('ensemble.meaningLimit') }}</p>
      </aside>

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

      <section v-if="runStatsGroups.length" class="run-stats" :aria-label="t('ensemble.runStatsAria')">
        <h2 class="section-title">{{ t('ensemble.runStatsTitle') }}</h2>
        <div class="run-stats--table">
          <table class="grid run-stats__grid">
            <thead>
              <tr>
                <th scope="col">{{ t('ensemble.runStatsVariant') }}</th>
                <th scope="col">{{ t('ensemble.runStatsRun') }}</th>
                <th scope="col">{{ t('ensemble.runStatsPosts') }}</th>
                <th scope="col">{{ t('ensemble.runStatsChars') }}</th>
                <th scope="col">{{ t('ensemble.runStatsBatches') }}</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="g in runStatsGroups" :key="'rst-' + g.key">
                <tr v-for="row in g.rows" :key="'rst-' + g.key + '-' + row.run">
                  <th scope="row">{{ g.label }}</th>
                  <td class="mono">{{ row.run }}</td>
                  <td class="mono">{{ row.post_count }}</td>
                  <td class="mono">{{ row.character_count }}</td>
                  <td class="mono">{{ row.batch_count }}</td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
        <ul class="run-stats--list">
          <li v-for="g in runStatsGroups" :key="'rsl-' + g.key" class="run-stats__group">
            <h3 class="run-stats__variant">{{ g.label }}</h3>
            <ul class="run-stats__runs">
              <li v-for="row in g.rows" :key="'rsl-' + g.key + '-' + row.run" class="run-stats__run">
                <span class="run-stats__run-label">{{ t('ensemble.runStatsRun') }} {{ row.run }}</span>
                <dl class="run-stats__dl">
                  <div><dt>{{ t('ensemble.runStatsPosts') }}</dt><dd class="mono">{{ row.post_count }}</dd></div>
                  <div><dt>{{ t('ensemble.runStatsChars') }}</dt><dd class="mono">{{ row.character_count }}</dd></div>
                  <div><dt>{{ t('ensemble.runStatsBatches') }}</dt><dd class="mono">{{ row.batch_count }}</dd></div>
                </dl>
              </li>
            </ul>
          </li>
        </ul>
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
                <div class="outcome__head">
                  <span>{{ outcomeLabel(item) }}</span>
                  <span v-if="item.source === 'user'" class="tag-user">{{ t('ensemble.yourQuestion') }}</span>
                  <span v-if="item.kind === 'interaction'" class="tag-mechanism">{{ t('ensemble.mechanismTag') }}</span>
                </div>
                <ReliabilityBadge :rel="reliabilityFor(item.id)" :t="t" />
                <p v-if="item.in_material" class="material-in-hint">{{ t('reliability.inMaterialHint') }}</p>
                <details v-if="item.in_material" class="material">
                  <summary>{{ t('ensemble.alreadyInMaterial') }}</summary>
                  <p v-if="item.material_snippet" class="snippet">{{ item.material_snippet }}</p>
                </details>
              </th>
              <td
                v-for="v in variants"
                :key="item.id + '-' + v.key"
                :class="{ 'mechanism-blocked': isMechanismBlocked(item, v.key) }"
              >
                <p v-if="isMechanismBlocked(item, v.key)" class="mechanism-blocked__text">
                  {{ t('ensemble.mechanismUnavailable') }}
                </p>
                <CellStat v-else :stat="cell(v.key, item.id)" :t="t" />
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- Mobile cards (no horizontal table scroll) -->
      <section v-if="checklist.length" class="results results--cards" :aria-label="t('ensemble.resultsAria')">
        <article v-for="item in checklist" :key="'c-' + item.id" class="card" :class="{ 'card--material': item.in_material }">
          <div class="card__head">
            <h2 class="card__title">{{ outcomeLabel(item) }}</h2>
            <span v-if="item.source === 'user'" class="tag-user">{{ t('ensemble.yourQuestion') }}</span>
            <span v-if="item.kind === 'interaction'" class="tag-mechanism">{{ t('ensemble.mechanismTag') }}</span>
          </div>
          <ReliabilityBadge :rel="reliabilityFor(item.id)" :t="t" />
          <p v-if="item.in_material" class="material-in-hint">{{ t('reliability.inMaterialHint') }}</p>
          <details v-if="item.in_material" class="material">
            <summary>{{ t('ensemble.alreadyInMaterial') }}</summary>
            <p v-if="item.material_snippet" class="snippet">{{ item.material_snippet }}</p>
          </details>
          <div
            v-for="v in variants"
            :key="'cv-' + item.id + v.key"
            class="card__row"
            :class="{ 'mechanism-blocked': isMechanismBlocked(item, v.key) }"
          >
            <span class="card__var">{{ variantLabel(v) }}</span>
            <p v-if="isMechanismBlocked(item, v.key)" class="mechanism-blocked__text">
              {{ t('ensemble.mechanismUnavailable') }}
            </p>
            <CellStat v-else :stat="cell(v.key, item.id)" :t="t" />
          </div>
        </article>
      </section>

      <section v-if="comparisons.length" class="compare" aria-labelledby="cmp-h">
        <h2 id="cmp-h" class="section-title">{{ t('ensemble.diffTitle') }}</h2>
        <ul class="compare__list">
          <li
            v-for="(c, i) in comparisons"
            :key="i"
            class="compare__item"
            :class="{
              'compare__item--unreliable': c.unreliable,
              'compare__item--confirmatory': isConfirmatory(c),
              'compare__item--exploratory': !isConfirmatory(c),
              'compare__item--blocked': isComparisonBlocked(c),
            }"
          >
            <div class="compare__heading">
              <strong>{{ compareVariantLabel(c.variant) }}</strong>
              <span>· {{ outcomeText(c.outcome_id) }}</span>
              <span v-if="isComparisonBlocked(c)" class="compare__badge">{{ t('ensemble.mechanismTag') }}</span>
              <span v-else-if="isConfirmatory(c)" class="compare__badge compare__badge--confirmatory">{{ t('ensemble.confirmatory') }}</span>
              <span v-else class="compare__badge">{{ t('ensemble.exploratory') }}</span>
            </div>
            <p v-if="isComparisonBlocked(c)" class="compare__body">{{ t('ensemble.mechanismUnavailable') }}</p>
            <p v-else class="compare__body">
              <span class="mono">{{ fmtDiff(c.diff) }} · {{ fmtDiffCi(c.ci_low, c.ci_high) }}</span>
              — {{ interpretDiff(c) }}
              <span v-if="!isConfirmatory(c)" class="compare__warning"> · {{ t('ensemble.exploratoryWarning') }}</span>
              <span v-if="hasPValues(c)" class="compare__tests mono"> · {{ formatPValues(c) }}</span>
            </p>
          </li>
        </ul>
      </section>

      <aside class="help">
        <h2 class="section-title">{{ t('ensemble.ciHelpTitle') }}</h2>
        <p>{{ t('ensemble.ciHelpBody') }}</p>
      </aside>

      <footer v-if="canCancel || canGoReport || canDelete" class="foot">
        <button
          v-if="canCancel"
          type="button"
          class="foot__primary foot__primary--neutral foot__desk"
          :disabled="busy"
          @click="askCancel"
        >{{ t('ensemble.cancel') }}</button>
        <button
          v-else-if="canGoReport"
          type="button"
          class="foot__primary foot__desk"
          :disabled="busy"
          @click="goToReport"
        >{{ t('ensemble.toReport') }}</button>
        <button
          v-if="canDelete"
          type="button"
          class="foot__delete"
          :disabled="busy"
          @click="askDelete"
        >{{ t('ensemble.delete') }}</button>
      </footer>
    </main>

    <main v-else-if="loadError" class="main">
      <p class="error" role="alert">{{ loadError }}</p>
    </main>
    <main v-else class="main"><p class="muted">{{ t('common.loading') }}</p></main>

    <MobileStickyBar
      v-if="data && (canCancel || canGoReport)"
      :primary-label="canCancel ? t('ensemble.cancel') : t('ensemble.toReport')"
      :primary-neutral="canCancel"
      :primary-loading="busy"
      @primary-click="canCancel ? askCancel() : goToReport()"
    />

    <ConfirmSheet
      :open="confirmCancel"
      :title="t('ensemble.cancelTitle')"
      :text="t('ensemble.cancelText')"
      :confirm-label="t('ensemble.cancel')"
      :busy="busy"
      @confirm="doCancel"
      @close="confirmCancel = false"
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
import ReliabilityHint from '../components/ReliabilityHint.vue'
import { getEnsemble, cancelEnsemble, deleteEnsemble } from '../api/ensemble'
import { getSimulationHistory } from '../api/simulation'

const props = defineProps({ ensembleId: String })
const { t, locale } = useI18n()
const router = useRouter()

const data = ref(null)
const loadError = ref('')
const busy = ref(false)
const confirmDelete = ref(false)
const confirmCancel = ref(false)
let timer = null

const VARIANT_I18N = {
  blind_feed: 'ensemble.variantLabelBlindFeed',
  null_document: 'ensemble.variantLabelNullDocument',
  null_personas: 'ensemble.variantLabelNullPersonas',
  null_model: 'ensemble.variantLabelNullDocument',
}

const variants = computed(() => data.value?.variants || [])
const checklist = computed(() => data.value?.checklist || [])
const comparisons = computed(() => data.value?.comparisons || [])
const canCancel = computed(() => ['queued', 'running'].includes(data.value?.status))
const canDelete = computed(() => ['completed', 'failed', 'cancelled'].includes(data.value?.status))
const canGoReport = computed(() => canDelete.value && !!data.value?.simulation_id)
const statusLabel = computed(() => t(`ensemble.status.${data.value?.status || 'queued'}`))
const currentVariantLabel = computed(() => {
  const key = data.value?.current?.variant
  if (!key) return '—'
  return variantLabel(variants.value.find((x) => x.key === key) || { key })
})
const etaLabel = computed(() => {
  if (!['queued', 'running'].includes(data.value?.status)) return ''
  const s = data.value?.eta_seconds
  if (s == null) return ''
  return t('ensemble.eta', { time: formatDuration(s) })
})
const runStatsGroups = computed(() => {
  const stats = data.value?.run_stats
  if (!stats || typeof stats !== 'object') return []
  return variants.value.flatMap((v) => {
    const raw = stats[v.key]
    if (!Array.isArray(raw) || !raw.length) return []
    return [{
      key: v.key,
      label: variantLabel(v),
      rows: raw.map((row, i) => ({
        run: row.run ?? i + 1,
        post_count: Number(row.post_count) || 0,
        character_count: Number(row.character_count) || 0,
        batch_count: Number(row.batch_count) || 0,
      })),
    }]
  })
})

function pickLocale(de, en, fallback) {
  return locale.value === 'en' ? (en || de || fallback) : (de || en || fallback)
}
function variantLabel(v) {
  if (!v) return '—'
  const i18nKey = VARIANT_I18N[v.key]
  if (i18nKey) return t(i18nKey)
  return pickLocale(v.label_de, v.label_en, v.key)
}
function compareVariantLabel(key) {
  return variantLabel(variants.value.find((x) => x.key === key) || { key })
}
function outcomeLabel(item) {
  if (!item) return '—'
  return pickLocale(item.text_de, item.text_en, item.id)
}
function outcomeText(id) {
  const item = checklist.value.find((x) => x.id === id)
  return item ? outcomeLabel(item) : id
}
function cell(variantKey, outcomeId) {
  return data.value?.results?.[variantKey]?.[outcomeId] || null
}
function reliabilityFor(outcomeId) {
  return data.value?.reliability?.[outcomeId] || null
}
function isMechanismBlocked(item, variantKey) {
  if (item?.kind !== 'interaction') return false
  return variantKey === 'isolated' || variantKey === 'null_model' || variantKey?.startsWith('null_')
}
function isComparisonBlocked(c) {
  const item = checklist.value.find((x) => x.id === c?.outcome_id)
  return isMechanismBlocked(item, c?.variant)
}
function isConfirmatory(c) {
  const primaryId = data.value?.primary_outcome_id
  if (c?.role) return c.role === 'confirmatory'
  if (primaryId) return c?.outcome_id === primaryId
  return false
}
function validP(value) {
  return value !== null && value !== '' && Number.isFinite(Number(value))
}
function mcnemarP(c) { return c?.mcnemar_p ?? c?.p_mcnemar }
function holmP(c) { return c?.holm_p ?? c?.p_holm }
function hasPValues(c) {
  return validP(mcnemarP(c)) || validP(holmP(c))
}
function formatP(value) {
  const p = Number(value)
  if (p < 0.001) return '< 0.001'
  return p.toFixed(3).replace(/0+$/, '').replace(/\.$/, '')
}
function formatPValues(c) {
  const values = []
  if (validP(mcnemarP(c))) values.push(t('ensemble.pMcnemar', { value: formatP(mcnemarP(c)) }))
  if (validP(holmP(c))) values.push(t('ensemble.pHolm', { value: formatP(holmP(c)) }))
  return values.join(' · ')
}
function pct(v) {
  if (!v?.total) return 0
  return Math.min(100, Math.round((100 * (v.done || 0)) / v.total))
}
/** Prozentpunkte mit Unicode-Minus und Vorzeichen bei positiven Werten. */
function fmtPp(x) {
  if (x == null || Number.isNaN(x)) return '—'
  const p = Math.round(x * 100)
  if (p === 0) return '0'
  return (p > 0 ? '+' : '−') + Math.abs(p)
}
function fmtDiff(d) {
  if (d == null) return '—'
  return t('ensemble.diffValue', { value: fmtPp(d) })
}
function fmtDiffCi(low, high) {
  return t('ensemble.diffCi', { low: fmtPp(low), high: fmtPp(high) })
}
function interpretDiff(c) {
  if (c.unreliable) return t('ensemble.compareUnreliable')
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

function relKey(label) {
  if (label === 'messbar') return 'messbar'
  if (label === 'unsicher') return 'unsicher'
  return 'nichtMessbar'
}

const ReliabilityBadge = {
  props: { rel: Object, t: Function },
  setup(p) {
    return () => {
      const rel = p.rel
      if (!rel?.label) return null
      const key = relKey(rel.label)
      const kids = [
        h('span', { class: ['rel-badge', `rel-badge--${key}`] }, p.t(`ensemble.reliability.${key}`)),
      ]
      if (key === 'nichtMessbar') {
        kids.push(h('span', { class: 'rel-hint' }, p.t('ensemble.reliabilityUnmeasurableHint')))
      }
      if (rel.kappa != null || rel.agreement != null) {
        kids.push(
          h('details', { class: 'rel-details' }, [
            h('summary', p.t('ensemble.reliabilityKappaSummary')),
            h('p', { class: 'rel-details__body' }, [
              rel.kappa != null
                ? h('span', { class: 'mono' }, p.t('ensemble.reliabilityKappa', { kappa: Number(rel.kappa).toFixed(2) }))
                : null,
              ' ',
              p.t('ensemble.reliabilityKappaHelp'),
            ]),
          ]),
        )
      }
      return h('div', { class: 'rel' }, kids)
    }
  },
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
      const disputed = Number(st.disputed) || 0
      return h('div', { class: 'stat' }, [
        h('div', { class: 'stat__text' }, [
          p.t('ensemble.cell', { yes: st.yes, n: st.n, rate, lo, hi }),
          disputed > 0
            ? h('span', { class: 'stat__disputed' }, ` · ${p.t('ensemble.disputed', { n: disputed })}`)
            : null,
        ]),
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

function askCancel() {
  confirmCancel.value = true
}
async function doCancel() {
  busy.value = true
  try {
    await cancelEnsemble(props.ensembleId)
    confirmCancel.value = false
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
async function goToReport() {
  const simId = data.value?.simulation_id
  if (!simId) return
  busy.value = true
  try {
    const res = await getSimulationHistory(50)
    const hit = (res?.data || []).find((s) => s.simulation_id === simId && s.report_id)
    if (hit?.report_id) {
      router.push(`/report/${hit.report_id}`)
      return
    }
    const cached = localStorage.getItem('mirofish:lastReport')
    if (cached) router.push(`/report/${cached}`)
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

.meaning { margin: 0 0 1.5rem; padding: 1rem 1.1rem; border: 1px solid var(--color-info-border); border-radius: var(--radius-md, 8px); background: var(--color-info-bg); color: var(--color-info-text); font-size: 14px; line-height: 1.5; }
.meaning__title { margin: 0 0 0.35rem; font-family: var(--font-heading); font-size: 1rem; color: var(--color-text-primary); }
.meaning p { margin: 0.25rem 0 0; }

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
.compare__list { display: grid; gap: 8px; margin: 0; padding: 0; list-style: none; color: var(--color-text-secondary); font-size: 14px; line-height: 1.55; }
.compare__item { padding: 10px 12px; border-left: 3px solid var(--color-border-default); background: var(--color-bg-surface-raised); }
.compare__item--confirmatory { border-color: var(--color-success-border); background: var(--color-success-bg); }
.compare__item--exploratory, .compare__item--blocked { color: var(--color-text-muted); background: var(--color-bg-surface-subtle); }
.compare__item--unreliable { color: var(--color-text-muted); opacity: 0.72; }
.compare__heading { display: flex; flex-wrap: wrap; align-items: center; gap: 4px; }
.compare__body { margin: 4px 0 0; }
.compare__badge, .tag-mechanism { display: inline-flex; align-items: center; min-height: 24px; padding: 0 7px; border: 1px solid var(--color-border-default); border-radius: 999px; background: var(--color-bg-surface-raised); color: var(--color-text-secondary); font-size: 11px; font-weight: 700; }
.compare__badge--confirmatory { border-color: var(--color-success-border); background: var(--color-success-bg); color: var(--color-success-text); }
.compare__warning { font-weight: 600; }
.compare__tests { white-space: normal; }
.help { margin-top: 2rem; padding: 1rem 1.1rem; border: 1px solid var(--color-border-subtle); border-radius: var(--radius-md, 8px); background: var(--color-bg-surface-raised); color: var(--color-text-secondary); font-size: 14px; line-height: 1.55; }
.help p { margin: 0; }

.foot { margin-top: 2.5rem; padding-top: 1.25rem; border-top: 1px solid var(--color-border-subtle); display: flex; flex-direction: column; align-items: flex-start; gap: 12px; }
.foot__primary {
  display: none;
  min-height: 48px;
  padding: 0 18px;
  border-radius: var(--radius-lg, 12px);
  border: 1px solid transparent;
  font: inherit;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  background: var(--color-brand-primary);
  color: var(--color-brand-on-primary);
}
.foot__primary--neutral {
  background: var(--color-bg-surface-raised);
  color: var(--color-text-primary);
  border-color: var(--color-border-default);
}
.foot__primary:disabled, .foot__delete:disabled { opacity: 0.6; cursor: not-allowed; }
.foot__delete {
  min-height: 44px;
  padding: 0;
  border: none;
  background: none;
  font: inherit;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-error-text);
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 3px;
}

.material-in-hint {
  margin: 6px 0 0;
  font-size: 12px;
  line-height: 1.4;
  color: var(--color-warning-text);
}
.material { margin-top: 6px; font-size: 13px; }
.material summary { cursor: pointer; min-height: 44px; display: inline-flex; align-items: center; color: var(--color-warning-text); font-weight: 600; }
.snippet { margin: 6px 0 0; padding: 8px 10px; background: var(--color-bg-surface-subtle); border-radius: 8px; color: var(--color-text-secondary); }

.outcome__head { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.tag-user {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 8px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: var(--color-info-text);
  background: var(--color-info-bg);
  border: 1px solid var(--color-info-border);
}

:deep(.rel) { display: grid; gap: 4px; margin-top: 8px; }
:deep(.rel-badge) {
  display: inline-flex;
  align-items: center;
  align-self: start;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid transparent;
}
:deep(.rel-badge--messbar) {
  color: var(--color-success-text);
  background: var(--color-success-bg);
  border-color: var(--color-success-border);
}
:deep(.rel-badge--unsicher) {
  color: var(--color-warning-text);
  background: var(--color-warning-bg);
  border-color: var(--color-warning-border);
}
:deep(.rel-badge--nichtMessbar) {
  color: var(--color-text-muted);
  background: var(--color-bg-surface-subtle);
  border-color: var(--color-border-subtle);
}
:deep(.rel-hint) { font-size: 12px; color: var(--color-text-muted); line-height: 1.4; }
:deep(.rel-details) { font-size: 12px; color: var(--color-text-secondary); }
:deep(.rel-details summary) {
  cursor: pointer;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
}
:deep(.rel-details__body) { margin: 4px 0 0; line-height: 1.45; }

.results--table { display: none; overflow-x: auto; }
.grid { width: 100%; border-collapse: collapse; font-size: 13px; }
.grid th, .grid td { border: 1px solid var(--color-border-subtle); padding: 10px; vertical-align: top; text-align: left; }
.grid thead th { background: var(--color-bg-surface-subtle); font-family: var(--font-heading); }
.outcome { font-weight: 600; min-width: 160px; }
.row--material { background: color-mix(in srgb, var(--color-warning-text) 6%, transparent); }
.mechanism-blocked { background: var(--color-bg-surface-subtle); color: var(--color-text-muted); }
.mechanism-blocked__text { margin: 0; font-size: 12px; line-height: 1.4; }

.run-stats { margin: 0 0 1.75rem; }
.run-stats--table { display: none; }
.run-stats--list { display: grid; gap: 12px; margin: 0; padding: 0; list-style: none; }
.run-stats__group {
  padding: 14px;
  border: 1px solid var(--color-border-default);
  border-radius: var(--radius-md, 8px);
  background: var(--color-bg-surface-raised);
}
.run-stats__variant { margin: 0 0 8px; font-family: var(--font-heading); font-size: 1rem; }
.run-stats__runs { margin: 0; padding: 0; list-style: none; display: grid; gap: 8px; }
.run-stats__run { padding: 10px 0; border-top: 1px solid var(--color-border-subtle); }
.run-stats__run-label { display: block; font-size: 12px; font-weight: 600; color: var(--color-text-muted); margin-bottom: 6px; }
.run-stats__dl { margin: 0; display: grid; gap: 6px; }
.run-stats__dl > div { display: flex; justify-content: space-between; gap: 12px; font-size: 13px; }
.run-stats__dl dt { margin: 0; color: var(--color-text-secondary); }
.run-stats__dl dd { margin: 0; }

.results--cards { display: grid; gap: 12px; }
.card { padding: 14px; border: 1px solid var(--color-border-default); border-radius: var(--radius-md, 8px); background: var(--color-bg-surface-raised); }
.card--material { border-color: color-mix(in srgb, var(--color-warning-text) 45%, var(--color-border-default)); }
.card__head { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 4px; }
.card__title { font-family: var(--font-heading); font-size: 1rem; margin: 0; }
.card__row { display: grid; gap: 4px; padding: 10px 0; border-top: 1px solid var(--color-border-subtle); }
.card__var { font-size: 12px; font-weight: 600; color: var(--color-text-muted); }

:deep(.stat__text) { font-size: 13px; line-height: 1.4; }
:deep(.stat__disputed) { color: var(--color-warning-text); font-weight: 600; }
:deep(.stat__bar) { position: relative; height: 6px; margin-top: 6px; background: var(--color-bg-surface-subtle); border-radius: 999px; overflow: hidden; }
:deep(.stat__bar i) { position: absolute; top: 0; bottom: 0; background: var(--color-brand-primary); border-radius: inherit; opacity: 0.75; }
:deep(.evidence) { margin-top: 6px; font-size: 12px; }
:deep(.evidence summary) { cursor: pointer; min-height: 44px; display: inline-flex; align-items: center; color: var(--color-text-secondary); }
:deep(.evidence ul) { margin: 6px 0 0; padding-left: 1rem; color: var(--color-text-secondary); }
:deep(.evidence p) { margin: 2px 0 8px; }

@media (min-width: 769px) {
  .results--table { display: block; }
  .results--cards { display: none; }
  .run-stats--table { display: block; }
  .run-stats--list { display: none; }
  .main { padding: 28px 24px 80px; }
  .foot__desk { display: inline-flex; align-items: center; justify-content: center; }
}
@media (prefers-reduced-motion: reduce) {
  .prog__fill { transition: none; }
  .prog__fill--pulse { animation: none; }
}
</style>
