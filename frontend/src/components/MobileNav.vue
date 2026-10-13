<template>
  <nav class="mobile-nav" aria-label="Hauptnavigation">
    <router-link to="/" class="mobile-nav__item" :class="{ active: route.path === '/' }">
      <span class="mobile-nav__icon">⌂</span><span>Start</span>
    </router-link>
    <a href="/#history" class="mobile-nav__item" @click.prevent="goHistory">
      <span class="mobile-nav__icon">☰</span><span>Verlauf</span>
    </a>
    <router-link v-if="currentRun" :to="currentRun" class="mobile-nav__item" :class="{ active: route.path === currentRun }">
      <span class="mobile-nav__icon">▶</span><span>Lauf</span>
    </router-link>
    <router-link v-if="currentReport" :to="currentReport" class="mobile-nav__item" :class="{ active: route.path === currentReport }">
      <span class="mobile-nav__icon">▤</span><span>Bericht</span>
    </router-link>
    <button type="button" class="mobile-nav__item" @click="scrollTop">
      <span class="mobile-nav__icon">↑</span><span>Oben</span>
    </button>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

// Letzter Lauf und letzter Bericht aus der aktuellen Adresse oder dem Browserspeicher
const currentRun = computed(() => {
  if (route.params.simulationId) return `/simulation/${route.params.simulationId}`
  const sid = safeGet('mirofish:lastSimulation')
  return sid ? `/simulation/${sid}` : null
})
const currentReport = computed(() => {
  if (route.params.reportId) return `/report/${route.params.reportId}`
  const rid = safeGet('mirofish:lastReport')
  return rid ? `/report/${rid}` : null
})

function safeGet(key) {
  try { return localStorage.getItem(key) } catch (e) { return null }
}
function goHistory() {
  if (route.path !== '/') {
    router.push('/').then(() => setTimeout(() => document.getElementById('history')?.scrollIntoView({ behavior: 'smooth' }), 300))
  } else {
    document.getElementById('history')?.scrollIntoView({ behavior: 'smooth' })
  }
}
function scrollTop() { window.scrollTo({ top: 0, behavior: 'smooth' }) }
</script>

<style scoped>
.mobile-nav {
  display: none;
}
@media (max-width: 768px) {
  .mobile-nav {
    position: fixed;
    left: 0; right: 0; bottom: 0;
    z-index: 5000;
    display: flex;
    justify-content: space-around;
    align-items: stretch;
    height: calc(56px + env(safe-area-inset-bottom));
    padding-bottom: env(safe-area-inset-bottom);
    background: #ffffff;
    border-top: 1px solid #e5e7eb;
    box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.04);
  }
  .mobile-nav__item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 2px;
    min-height: 48px;           /* Tippfläche */
    font-size: 11px;
    font-weight: 600;
    color: #6b7280;
    text-decoration: none;
    background: transparent;
    border: 0;
    font-family: inherit;
  }
  .mobile-nav__item.active { color: #ff5722; }
  .mobile-nav__icon { font-size: 18px; line-height: 1; }
}
</style>
