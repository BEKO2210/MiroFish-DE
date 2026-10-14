<template>
  <div class="step-nav-bar">
    <div class="step-nav-bar__meta">
      <span class="step-nav-bar__badge">{{ $t('main.schritt') }} {{ currentStep }}/5</span>
      <h2 class="step-nav-bar__title">{{ stepNames[currentStep - 1] }}</h2>
    </div>
    <ol class="step-nav-bar__dots" :aria-label="$t('main.schrittFortschritt')">
      <li v-for="step in 5" :key="step" class="step-dot-wrap">
        <button
          type="button"
          class="step-dot"
          :class="'is-' + stateOf(step)"
          :data-testid="`step-dot-${step}`"
          :data-state="stateOf(step)"
          :aria-current="step === currentStep ? 'step' : undefined"
          :disabled="step > maxUnlockedStep"
          :title="fullLabel(step)"
          @click="$emit('select-step', step)"
        >
          <span class="step-dot__circle" aria-hidden="true">
            <svg v-if="stateOf(step) === 'done'" class="step-dot__check" viewBox="0 0 16 16" fill="none">
              <path d="M3.5 8.5 6.5 11.5 12.5 4.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </span>
          <span class="sr-only">{{ fullLabel(step) }}</span>
        </button>
      </li>
    </ol>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const props = defineProps({
  currentStep: { type: Number, required: true },
  maxUnlockedStep: { type: Number, default: 5 },
  stepNames: { type: Array, required: true },
  /** true nur wenn die aktuelle Stufe wirklich rechnet (läuft/vorbereiten) */
  busy: { type: Boolean, default: false }
})
defineEmits(['select-step'])

const { t } = useI18n()

const STATE_LABEL = {
  done: 'main.stepDone',
  here: 'main.stepHere',
  running: 'main.stepRunning',
  available: 'main.stepAvailable',
  locked: 'main.stepLocked'
}

/** Nachfragen (5) ist nie eine Arbeitsstufe */
function stateOf(step) {
  if (step > props.maxUnlockedStep) return 'locked'
  if (props.busy && step === props.currentStep && step !== 5) return 'running'
  if (step < props.currentStep) return 'done'
  if (step === props.currentStep) return 'here'
  return 'available'
}

function fullLabel(step) {
  return `${props.stepNames[step - 1]}, ${t(STATE_LABEL[stateOf(step)])}`
}
</script>

<style scoped>
.step-nav-bar { display: flex; align-items: center; justify-content: space-between; width: 100%; padding: 4px 0; }
.step-nav-bar__meta { display: flex; flex-direction: column; min-width: 0; }
.step-nav-bar__badge { font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--color-text-secondary); letter-spacing: 0.04em; }
.step-nav-bar__title { font-family: var(--font-heading); font-size: 14px; font-weight: 700; color: var(--color-text-primary); margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.step-nav-bar__dots { display: flex; align-items: center; gap: 6px; list-style: none; margin: 0; padding: 0; }
.step-dot-wrap { display: contents; }
.step-dot { min-width: 44px; min-height: 44px; padding: 0; background: transparent; border: 0; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; }
.step-dot:disabled { cursor: not-allowed; opacity: 0.35; }
.step-dot__circle {
  width: 10px; height: 10px; border-radius: 999px;
  background: var(--color-border-strong);
  border: 2px solid transparent;
  box-sizing: border-box;
  display: inline-flex; align-items: center; justify-content: center;
  transition: width var(--transition-fast), height var(--transition-fast), background var(--transition-fast), border-color var(--transition-fast), box-shadow var(--transition-fast);
  color: var(--color-success-text);
}
.step-dot__check { width: 10px; height: 10px; }
.step-dot.is-done .step-dot__circle {
  width: 16px; height: 16px;
  background: var(--color-success-bg);
  border-color: var(--color-success-text);
  color: var(--color-success-text);
}
.step-dot.is-here .step-dot__circle {
  width: 16px; height: 16px;
  background: transparent;
  border-color: var(--color-brand-primary);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--color-brand-primary) 35%, transparent);
}
.step-dot.is-running .step-dot__circle {
  width: 16px; height: 16px;
  background: color-mix(in srgb, var(--color-brand-primary) 18%, transparent);
  border-color: var(--color-brand-primary);
  animation: step-pulse 1.8s ease-in-out infinite;
}
.step-dot.is-available .step-dot__circle {
  background: transparent;
  border-color: var(--color-border-strong);
}
@keyframes step-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.45; }
}
@media (prefers-reduced-motion: reduce) {
  .step-dot.is-running .step-dot__circle { animation: none; }
}
</style>
