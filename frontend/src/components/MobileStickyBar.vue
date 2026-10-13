<!-- frontend/src/components/MobileStickyBar.vue -->
<template>
  <aside class="mobile-sticky-bar" role="region" :aria-label="ariaLabel || primaryLabel">
    <div class="mobile-sticky-bar__container">
      <button
        v-if="secondaryLabel"
        type="button"
        class="sticky-btn sticky-btn--secondary"
        :disabled="secondaryDisabled || primaryLoading"
        @click="$emit('secondary-click')"
      >
        <span>{{ secondaryLabel }}</span>
      </button>

      <button
        type="button"
        class="sticky-btn sticky-btn--primary"
        :class="{ 'is-loading': primaryLoading }"
        :disabled="primaryDisabled || primaryLoading"
        @click="$emit('primary-click')"
      >
        <span v-if="primaryLoading" class="sticky-btn__spinner" aria-hidden="true"></span>
        <span class="sticky-btn__label">{{ primaryLabel }}</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
defineProps({
  primaryLabel: { type: String, required: true },
  primaryDisabled: { type: Boolean, default: false },
  primaryLoading: { type: Boolean, default: false },
  secondaryLabel: { type: String, default: '' },
  secondaryDisabled: { type: Boolean, default: false },
  ariaLabel: { type: String, default: '' }
})
defineEmits(['primary-click', 'secondary-click'])
</script>

<style scoped>
.mobile-sticky-bar {
  display: none;
}

@media (max-width: 768px) {
  .mobile-sticky-bar {
    display: block;
    position: fixed;
    left: 0;
    right: 0;
    bottom: calc(58px + env(safe-area-inset-bottom, 0px));
    z-index: 45;
    background: color-mix(in srgb, var(--color-bg-canvas) 92%, transparent);
    backdrop-filter: saturate(180%) blur(16px);
    -webkit-backdrop-filter: saturate(180%) blur(16px);
    border-top: 1px solid var(--color-border-subtle);
    padding: 8px 16px;
    box-shadow: 0 -4px 16px rgba(15, 23, 42, 0.06);
  }

  .mobile-sticky-bar__container {
    display: flex;
    align-items: center;
    gap: 10px;
    max-width: 600px;
    margin: 0 auto;
  }

  .sticky-btn {
    flex: 1;
    min-height: 48px;
    border-radius: var(--radius-lg, 12px);
    font-family: var(--font-body);
    font-size: 15px;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 0 16px;
    border: 1px solid transparent;
    cursor: pointer;
    touch-action: manipulation;
    transition: transform var(--transition-fast), opacity var(--transition-fast), background-color var(--transition-fast);
  }

  .sticky-btn:active:not(:disabled) {
    transform: scale(0.98);
  }

  .sticky-btn--primary {
    background: var(--color-brand-primary);
    color: var(--color-brand-on-primary);
    box-shadow: 0 2px 8px color-mix(in srgb, var(--color-brand-primary) 30%, transparent);
  }

  .sticky-btn--primary:disabled {
    background: var(--color-bg-surface-subtle);
    color: var(--color-text-muted);
    border-color: var(--color-border-subtle);
    box-shadow: none;
    cursor: not-allowed;
  }

  .sticky-btn--secondary {
    flex: 0 0 auto;
    min-width: 110px;
    background: var(--color-bg-surface-raised);
    color: var(--color-text-secondary);
    border-color: var(--color-border-default);
  }

  .sticky-btn__spinner {
    width: 16px;
    height: 16px;
    border: 2px solid color-mix(in srgb, currentColor 30%, transparent);
    border-top-color: currentColor;
    border-radius: 50%;
    animation: spin-sticky 0.8s linear infinite;
  }
}

@keyframes spin-sticky {
  to { transform: rotate(360deg); }
}

@media (prefers-reduced-motion: reduce) {
  .sticky-btn {
    transition: none !important;
  }
  .sticky-btn__spinner {
    animation-duration: 2s !important;
  }
}
</style>
