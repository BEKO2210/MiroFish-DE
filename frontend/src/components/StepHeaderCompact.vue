<template>
  <div class="step-nav-bar">
    <div class="step-nav-bar__meta">
      <span class="step-nav-bar__badge">{{ $t('main.schritt') }} {{ currentStep }}/5</span>
      <h2 class="step-nav-bar__title">{{ stepNames[currentStep - 1] }}</h2>
    </div>
    <div class="step-nav-bar__dots" role="tablist" :aria-label="$t('main.schrittFortschritt')">
      <button
        v-for="step in 5"
        :key="step"
        type="button"
        role="tab"
        class="step-dot"
        :class="{ 'is-active': step === currentStep, 'is-passed': step < currentStep, 'is-locked': step > maxUnlockedStep }"
        :aria-selected="step === currentStep"
        :disabled="step > maxUnlockedStep"
        @click="$emit('select-step', step)"
        :title="`${stepNames[step - 1]}`"
      >
        <span class="step-dot__circle"></span>
        <span class="sr-only">{{ stepNames[step - 1] }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  currentStep: { type: Number, required: true },
  maxUnlockedStep: { type: Number, default: 5 },
  stepNames: { type: Array, required: true }
})
defineEmits(['select-step'])
</script>

<style scoped>
.step-nav-bar { display: flex; align-items: center; justify-content: space-between; width: 100%; padding: 4px 0; }
.step-nav-bar__meta { display: flex; flex-direction: column; min-width: 0; }
.step-nav-bar__badge { font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--color-text-secondary); letter-spacing: 0.04em; }
.step-nav-bar__title { font-family: var(--font-heading); font-size: 14px; font-weight: 700; color: var(--color-text-primary); margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.step-nav-bar__dots { display: flex; align-items: center; gap: 6px; }
.step-dot { min-width: 32px; min-height: 36px; padding: 0; background: transparent; border: 0; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; }
.step-dot:disabled { cursor: not-allowed; opacity: 0.35; }
.step-dot__circle { width: 8px; height: 8px; border-radius: 999px; background: var(--color-border-strong); transition: all var(--transition-fast); }
.step-dot.is-active .step-dot__circle { width: 22px; background: var(--color-brand-primary); }
.step-dot.is-passed .step-dot__circle { background: var(--color-success-text); }
</style>
