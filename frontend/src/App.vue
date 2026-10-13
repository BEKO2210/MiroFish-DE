<template>
  <router-view />
  <MobileNav />
</template>

<script setup>
import MobileNav from './components/MobileNav.vue'
</script>

<style>
/* Globale Stil-Zurücksetzung */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: var(--font-body, 'Inter', system-ui, sans-serif); /* Fließtext lesbar; Monospace nur noch für Code/IDs */
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #000000;
  background-color: #ffffff;
  min-height: 100vh;
}

/* Scrollbalken-Stil */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: #000000;
}

::-webkit-scrollbar-thumb:hover {
  background: #333333;
}

/* Globaler Button-Stil */
button {
  font-family: inherit;
}
@media (max-width: 768px) {
  body { padding-bottom: calc(64px + env(safe-area-inset-bottom)); }
}
h1, h2, h3, .main-title { font-family: var(--font-heading, 'Space Grotesk', system-ui, sans-serif); }
code, pre, .card-id, .mono { font-family: var(--font-mono, 'JetBrains Mono', monospace); }
</style>
