<template>
  <Transition name="guide-tip">
    <aside
      v-if="open"
      ref="root"
      class="guide-tip"
      role="status"
      data-testid="reliability-hint"
      :style="dragStyle"
      @pointerdown="onDown"
      @pointermove="onMove"
      @pointerup="onUp"
      @pointercancel="onUp"
    >
      <div class="guide-tip__glow" aria-hidden="true"></div>
      <p class="guide-tip__text">{{ message }}</p>
      <router-link
        v-if="linkTo"
        class="guide-tip__link"
        :to="linkTo"
        @click.stop
      >{{ linkLabel }}</router-link>
      <button
        type="button"
        class="guide-tip__close"
        :aria-label="dismissLabel"
        :title="dismissLabel"
        @click.stop="dismiss"
      >
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </aside>
  </Transition>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

const props = defineProps({
  message: { type: String, required: true },
  linkLabel: { type: String, default: '' },
  linkTo: { type: [String, Object], default: '' },
  dismissLabel: { type: String, default: 'Close' },
  storageKey: { type: String, required: true },
})

const DISMISS_PX = 72

const open = ref(false)
const root = ref(null)
const dragX = ref(0)
const dragging = ref(false)
let startX = 0
let pointerId = null

function storageId() {
  return `guide-tip:${props.storageKey}`
}

function readDismissed() {
  try {
    return sessionStorage.getItem(storageId()) === '1'
  } catch {
    return false
  }
}

function writeDismissed() {
  try {
    sessionStorage.setItem(storageId(), '1')
  } catch {
    /* private mode / quota */
  }
}

onMounted(() => {
  if (!readDismissed()) open.value = true
})

const dragStyle = computed(() => {
  if (!dragging.value && dragX.value === 0) return undefined
  const x = dragX.value
  return {
    transform: `translate3d(${x}px, 0, 0)`,
    opacity: String(Math.max(0.25, 1 - Math.abs(x) / 160)),
  }
})

function dismiss() {
  open.value = false
  writeDismissed()
}

function onDown(e) {
  if (e.button != null && e.button !== 0) return
  if (e.target?.closest?.('a, button')) return
  dragging.value = true
  startX = e.clientX
  pointerId = e.pointerId
  root.value?.setPointerCapture?.(e.pointerId)
}

function onMove(e) {
  if (!dragging.value || e.pointerId !== pointerId) return
  dragX.value = e.clientX - startX
}

function onUp(e) {
  if (!dragging.value || (pointerId != null && e.pointerId !== pointerId)) return
  const x = dragX.value
  dragging.value = false
  pointerId = null
  if (Math.abs(x) > DISMISS_PX) dismiss()
  dragX.value = 0
}
</script>

<style scoped>
.guide-tip {
  position: relative;
  display: grid;
  grid-template-columns: 1fr auto;
  grid-template-areas:
    "text close"
    "link close";
  gap: 4px 10px;
  align-items: start;
  margin: 0 0 14px;
  padding: 12px 12px 12px 14px;
  max-width: 100%;
  overflow: hidden;
  border-radius: 14px;
  border: 1px solid var(--color-info-border);
  background: var(--color-info-bg);
  color: var(--color-info-text);
  box-shadow: none;
  touch-action: pan-y;
  cursor: grab;
  user-select: none;
}
.guide-tip:active { cursor: grabbing; }
.guide-tip__glow {
  position: absolute;
  inset: 0 auto 0 0;
  width: 3px;
  background: var(--color-info-text);
  border-radius: 14px 0 0 14px;
}
.guide-tip__text {
  grid-area: text;
  margin: 0;
  font-size: 14px;
  line-height: 1.45;
  color: var(--color-text-primary);
  padding-left: 4px;
}
.guide-tip__link {
  grid-area: link;
  justify-self: start;
  margin-left: 4px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-info-text);
  text-decoration: underline;
  text-underline-offset: 2px;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
}
.guide-tip__close {
  grid-area: close;
  width: 44px;
  height: 44px;
  margin: -6px -6px 0 0;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--color-text-secondary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.2s, transform 0.2s, color 0.2s;
}
.guide-tip__close:hover {
  background: var(--color-bg-surface-subtle);
  color: var(--color-text-primary);
  transform: scale(1.06);
}

.guide-tip-enter-active {
  transition: opacity 0.35s ease, transform 0.4s cubic-bezier(0.22, 1, 0.36, 1);
}
.guide-tip-leave-active {
  transition: opacity 0.28s ease, transform 0.32s cubic-bezier(0.4, 0, 1, 1);
}
.guide-tip-enter-from {
  opacity: 0;
  transform: translate3d(0, -10px, 0) scale(0.98);
}
.guide-tip-leave-to {
  opacity: 0;
  transform: translate3d(40px, 0, 0) scale(0.96);
}

@media (prefers-reduced-motion: reduce) {
  .guide-tip-enter-active,
  .guide-tip-leave-active { transition: none; }
  .guide-tip__close { transition: none; }
}
</style>
