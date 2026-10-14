<template>
  <div
    class="step-activity"
    :class="{
      'step-activity--running': active,
      'step-activity--stale': active && stale,
      'step-activity--error': error,
    }"
    data-testid="step-activity"
    role="status"
    :aria-live="active ? 'polite' : 'off'"
  >
    <span
      v-if="active"
      class="step-activity__pulse"
      aria-hidden="true"
      data-testid="step-activity-pulse"
    />
    <span v-else-if="error" class="step-activity__mark" aria-hidden="true">!</span>
    <div class="step-activity__body">
      <strong v-if="label" class="step-activity__label">{{ label }}</strong>
      <p v-if="detail" class="step-activity__detail">{{ detail }}</p>
      <template v-if="active">
        <p v-if="progressText" class="step-activity__meta" data-testid="step-activity-progress">
          {{ progressText }}
        </p>
        <p v-if="elapsedText" class="step-activity__meta" data-testid="step-activity-elapsed">
          {{ elapsedText }}
        </p>
        <p v-if="remainingText" class="step-activity__meta" data-testid="step-activity-remaining">
          {{ remainingText }}
        </p>
        <p v-if="lastPollAt" class="step-activity__poll" data-testid="step-activity-updated">
          {{ t('activity.lastUpdated', { n: secondsSincePoll }) }}
        </p>
        <p v-if="stale" class="step-activity__stale" data-testid="step-activity-stale">
          {{ t('activity.staleHint') }}
        </p>
      </template>
      <p v-if="error" class="step-activity__error" role="alert" data-testid="step-activity-error">
        {{ error }}
      </p>
      <p v-if="error && nextHint" class="step-activity__next" data-testid="step-activity-next">
        {{ nextHint }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { isStale } from '../composables/useLiveness'

const props = defineProps({
  active: { type: Boolean, default: false },
  label: { type: String, default: '' },
  detail: { type: String, default: '' },
  current: { type: Number, default: null },
  total: { type: Number, default: null },
  startedAt: { type: String, default: null },
  /** Server-provided remaining seconds only; null/undefined hides ETA. */
  remainingSeconds: { type: Number, default: null },
  lastPollAt: { type: Number, default: 0 },
  serverUpdatedAt: { type: String, default: null },
  error: { type: String, default: '' },
  nextHint: { type: String, default: '' },
})

const { t } = useI18n()
const nowTick = ref(Date.now())
let timer = null

function bumpNow() {
  nowTick.value = Date.now()
}

function setClockRunning(on) {
  if (on) {
    bumpNow()
    if (!timer) timer = setInterval(bumpNow, 1000)
  } else if (timer) {
    clearInterval(timer)
    timer = null
  }
}

watch(() => props.active, setClockRunning, { immediate: true })
watch(() => props.lastPollAt, () => {
  if (props.active) bumpNow()
})
onUnmounted(() => setClockRunning(false))

const secondsSincePoll = computed(() => {
  if (!props.lastPollAt) return 0
  return Math.max(0, Math.floor((nowTick.value - props.lastPollAt) / 1000))
})

const stale = computed(() => props.active && isStale(props.serverUpdatedAt, nowTick.value))

const progressText = computed(() => {
  if (props.current == null || props.total == null || props.total <= 0) return ''
  return t('activity.progressOf', { current: props.current, total: props.total })
})

function fmtSecs(s) {
  const n = Math.max(0, Math.round(s))
  if (n < 3600) return t('run.min', { n: Math.max(1, Math.round(n / 60)) })
  return t('run.hmin', { h: Math.floor(n / 3600), m: Math.round((n % 3600) / 60) })
}

const elapsedText = computed(() => {
  if (!props.startedAt) return ''
  const start = new Date(props.startedAt).getTime()
  if (Number.isNaN(start)) return ''
  return t('activity.elapsed', { t: fmtSecs((nowTick.value - start) / 1000) })
})

const remainingText = computed(() => {
  if (props.remainingSeconds == null || !Number.isFinite(props.remainingSeconds)) return ''
  return t('activity.remaining', { t: fmtSecs(props.remainingSeconds) })
})
</script>

<style scoped>
.step-activity {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 12px;
  background: var(--color-bg-surface);
  border: 1px solid var(--color-border-subtle);
  color: var(--color-text-primary);
}
.step-activity--running {
  border-color: var(--color-brand-border, var(--color-border-default));
  background: color-mix(in srgb, var(--color-brand-subtle, var(--color-bg-surface)) 70%, var(--color-bg-surface));
}
.step-activity--stale {
  border-color: var(--color-warning-border, var(--color-border-default));
  background: var(--color-warning-bg, var(--color-bg-surface));
}
.step-activity--error {
  border-color: var(--color-error-border);
  background: var(--color-error-bg);
}
.step-activity__pulse {
  flex: none;
  width: 12px;
  height: 12px;
  margin-top: 4px;
  border-radius: 50%;
  background: var(--color-brand-primary);
  box-shadow: 0 0 0 0 color-mix(in srgb, var(--color-brand-primary) 45%, transparent);
  animation: activity-pulse 2.4s ease-out infinite;
}
.step-activity__mark {
  flex: none;
  width: 28px;
  height: 28px;
  min-width: 28px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  background: var(--color-error-text);
  color: var(--color-brand-on-primary);
}
.step-activity__body {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.step-activity__label {
  font-size: 15px;
  font-weight: 650;
  line-height: 1.3;
}
.step-activity__detail,
.step-activity__meta,
.step-activity__poll,
.step-activity__stale,
.step-activity__error,
.step-activity__next {
  margin: 0;
  font-size: 13px;
  line-height: 1.4;
  color: var(--color-text-secondary);
}
.step-activity__poll {
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
}
.step-activity__stale {
  color: var(--color-warning-text, var(--color-text-primary));
  font-weight: 600;
}
.step-activity__error {
  color: var(--color-error-text);
  font-weight: 600;
}
.step-activity__next {
  color: var(--color-text-primary);
}

@keyframes activity-pulse {
  0% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--color-brand-primary) 45%, transparent); }
  70% { box-shadow: 0 0 0 10px transparent; }
  100% { box-shadow: 0 0 0 0 transparent; }
}

@media (prefers-reduced-motion: reduce) {
  .step-activity__pulse {
    animation: none;
    box-shadow: none;
  }
}
</style>
