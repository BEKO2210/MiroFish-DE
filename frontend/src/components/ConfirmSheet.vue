<template>
  <Teleport to="body">
    <Transition name="sheet">
      <div v-if="open" class="backdrop" @click.self="$emit('close')">
        <section class="sheet" role="alertdialog" aria-modal="true" :aria-label="title">
          <h2 class="sheet__title">{{ title }}</h2>
          <p v-if="text" class="sheet__text">{{ text }}</p>
          <div v-if="$slots.default" class="sheet__body"><slot /></div>
          <div class="sheet__actions">
            <button type="button" class="btn" :disabled="busy" @click="$emit('close')">{{ t('confirm.cancel') }}</button>
            <button type="button" class="btn btn--confirm" :class="{ 'btn--danger': danger }" :disabled="busy" @click="$emit('confirm')">
              <span v-if="!busy">{{ confirmLabel }}</span><span v-else class="spin"></span>
            </button>
          </div>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
defineProps({ open: Boolean, title: String, text: String, confirmLabel: { type: String, default: 'OK' }, busy: Boolean, danger: Boolean })
defineEmits(['confirm', 'close'])
</script>

<style scoped>
.backdrop { position: fixed; inset: 0; z-index: 110; background: rgba(0,0,0,.4); display: flex; align-items: flex-end; justify-content: center; }
.sheet { width: 100%; max-width: 520px; max-height: calc(100dvh - 24px); display: flex; flex-direction: column; background: var(--color-bg-surface-raised); color: var(--color-text-primary); border-radius: 20px 20px 0 0; padding: 22px 20px calc(20px + env(safe-area-inset-bottom)); box-shadow: 0 -8px 40px rgba(0,0,0,.2); }
.sheet__title { font-family: var(--font-heading); font-size: 19px; margin: 0 0 6px; }
.sheet__text { margin: 0 0 18px; font-size: 14px; line-height: 1.5; color: var(--color-text-secondary); }
.sheet__body { margin: 0 0 18px; flex: 1 1 auto; min-height: 0; overflow-y: auto; overscroll-behavior: contain; }
.sheet__actions { flex: none; display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.btn { min-height: 48px; border-radius: 12px; border: 1px solid var(--color-border-subtle); background: var(--color-bg-surface-raised); color: inherit; font: inherit; font-weight: 600; font-size: 15px; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; }
.btn--confirm { background: var(--color-brand-primary); border-color: var(--color-brand-primary); color: var(--color-brand-on-primary); }
.btn--danger { background: var(--color-error-text); border-color: var(--color-error-text); color: #fff; }
.btn:disabled { opacity: .6; cursor: not-allowed; }
.spin { width: 18px; height: 18px; border: 2px solid rgba(255,255,255,.4); border-top-color: #fff; border-radius: 50%; animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.sheet-enter-active, .sheet-leave-active { transition: opacity .2s; }
.sheet-enter-active .sheet, .sheet-leave-active .sheet { transition: transform .25s cubic-bezier(.16,1,.3,1); }
.sheet-enter-from, .sheet-leave-to { opacity: 0; }
.sheet-enter-from .sheet, .sheet-leave-to .sheet { transform: translateY(40px); }
@media (min-width: 769px) { .backdrop { align-items: center; } .sheet { border-radius: 20px; padding: 24px; } }
</style>
