<template>
  <router-view />
</template>

<script setup>
// Vue Router für Seitenverwaltung verwenden
</script>

<style>
/* Globale Stil-Zurücksetzung */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'JetBrains Mono', 'Space Grotesk', 'Noto Sans SC', monospace;
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
</style>
