<template>
  <nav class="mobile-nav" aria-label="Hauptnavigation">
    <router-link to="/" class="mobile-nav__item" :class="{ active: route.path === '/' }">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 11.5 12 4l9 7.5"/><path d="M5 10v10h5v-6h4v6h5V10"/></svg>
      <span>Start</span>
    </router-link>
    <router-link to="/history" class="mobile-nav__item" :class="{ active: route.path.startsWith('/history') || route.path.startsWith('/run') }">
      <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/></svg>
      <span>Verlauf</span>
      <i v-if="activeCount" class="mobile-nav__badge" :aria-label="`${activeCount} laufend`"></i>
    </router-link>
    <router-link to="/settings" class="mobile-nav__item" :class="{ active: route.path.startsWith('/settings') }">
      <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></svg>
      <span>Einstellungen</span>
    </router-link>
  </nav>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { listPipelines } from '../api/pipeline'

const route = useRoute()
const activeCount = ref(0)
let timer = null
const poll = async () => {
  try { activeCount.value = ((await listPipelines())?.data || []).filter(r => r.status === 'running').length } catch (e) { /* Anzeige ist optional */ }
}
onMounted(() => { poll(); timer = setInterval(poll, 20000) })
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.mobile-nav { display: none; }
@media (max-width: 768px) {
  .mobile-nav { position: fixed; left: 0; right: 0; bottom: 0; z-index: 50; display: grid; grid-template-columns: repeat(3, 1fr);
    background: color-mix(in srgb, var(--color-bg-surface-raised) 92%, transparent); backdrop-filter: saturate(180%) blur(14px); -webkit-backdrop-filter: saturate(180%) blur(14px);
    border-top: 1px solid var(--color-border-subtle); padding-bottom: env(safe-area-inset-bottom); }
  .mobile-nav__item { position: relative; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 3px; min-height: 58px;
    text-decoration: none; color: var(--color-text-muted); font-size: 11px; font-weight: 500; -webkit-tap-highlight-color: transparent; }
  .mobile-nav__item svg { width: 24px; height: 24px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
  .mobile-nav__item.active { color: var(--color-brand-primary); }
  .mobile-nav__badge { position: absolute; top: 8px; left: calc(50% + 8px); width: 8px; height: 8px; border-radius: 50%; background: var(--color-brand-primary); animation: pulse 1.6s ease-in-out infinite; }
  @keyframes pulse { 0%,100% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--color-brand-primary) 45%, transparent); } 50% { box-shadow: 0 0 0 6px transparent; } }
}
</style>
