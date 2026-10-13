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
  color: var(--color-text-primary);
  background-color: var(--color-bg-canvas);
  min-height: 100vh;
}

/* Scrollbalken-Stil */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--color-bg-surface);
}

::-webkit-scrollbar-thumb {
  background: var(--color-border-strong);
  border-radius: 999px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-muted);
}

/* Globaler Button-Stil */
button {
  font-family: inherit;
}
@media (max-width: 768px) {
  /* Fußmenü (~58px) + optional MobileStickyBar (~64px) + Safe-Area */
  body { padding-bottom: calc(130px + env(safe-area-inset-bottom, 0px)); }
  body { background: var(--color-bg-canvas); }
}
h1, h2, h3, .main-title { font-family: var(--font-heading, 'Space Grotesk', system-ui, sans-serif); }
code, pre, .card-id, .mono { font-family: var(--font-mono, 'JetBrains Mono', monospace); }
.api-note { display: none; } /* interne API-Pfade gehören nicht in die Nutzeroberfläche */
@media (max-width: 768px) {
  /* Entwickler-Protokolle am Handy ausblenden: sie überdecken den Inhalt und helfen Nutzern nicht */
  .system-logs, .console-logs { display: none !important; }
  /* Sprache wählt man am Handy unter Einstellungen; im Kopf der Schrittseiten ist dafür kein Platz */
  .language-switcher { display: none !important; }
  /* Berichtstitel: lange Wörter umbrechen, Größe fließend */
  .main-title { font-size: clamp(22px, 6.5vw, 30px) !important; overflow-wrap: anywhere; hyphens: auto; }
  .sub-title { font-size: 15px !important; }
}
</style>
