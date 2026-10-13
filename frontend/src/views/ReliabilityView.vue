<template>
  <div class="page">
    <AppHeader />
    <main class="main">
      <p class="eyebrow">{{ t('reliability.eyebrow') }}</p>
      <article class="guide" v-html="html"></article>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import AppHeader from '../components/AppHeader.vue'
import { reliabilityMarkdown } from '../data/reliabilityContent.js'
import { renderGuideMarkdown } from '../utils/formatRichText.js'

const { t, locale } = useI18n()

const html = computed(() =>
  renderGuideMarkdown(reliabilityMarkdown[locale.value] || reliabilityMarkdown.de),
)
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--color-bg-canvas);
  color: var(--color-text-primary);
}
.main {
  max-width: 680px;
  margin: 0 auto;
  padding: 20px 16px 48px;
  overflow-x: hidden;
}
.eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}
.guide {
  font-size: 15px;
  line-height: 1.55;
  overflow-wrap: anywhere;
  word-break: break-word;
}
.guide :deep(.guide-h1) {
  font-family: var(--font-heading);
  font-size: 1.65rem;
  letter-spacing: -0.02em;
  margin: 0 0 1rem;
  line-height: 1.25;
  color: var(--color-text-primary);
}
.guide :deep(.guide-h2),
.guide :deep(.guide-h3),
.guide :deep(.guide-h4) {
  font-family: var(--font-heading);
  margin: 1.4rem 0 0.55rem;
  line-height: 1.3;
  color: var(--color-text-primary);
}
.guide :deep(.guide-h2) { font-size: 1.25rem; }
.guide :deep(.guide-h3) { font-size: 1.1rem; }
.guide :deep(.guide-h4) { font-size: 1rem; }
.guide :deep(.guide-p) {
  margin: 0 0 0.85rem;
  color: var(--color-text-secondary);
}
.guide :deep(.guide-hr) {
  border: none;
  border-top: 1px solid var(--color-border-subtle);
  margin: 1.25rem 0;
}
.guide :deep(.guide-ul),
.guide :deep(.guide-ol) {
  margin: 0 0 1rem;
  padding-left: 1.25rem;
  color: var(--color-text-secondary);
}
.guide :deep(.guide-ul) { list-style: disc; }
.guide :deep(.guide-ol) { list-style: decimal; }
.guide :deep(li) { margin: 0.35rem 0; }
.guide :deep(.guide-check) {
  list-style: none;
  margin-left: -1.25rem;
  padding: 10px 12px;
  border-radius: 10px;
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-subtle);
}
.guide :deep(.guide-check)::before {
  content: '☐ ';
  color: var(--color-brand-primary);
}
.guide :deep(strong) { color: var(--color-text-primary); font-weight: 650; }
.guide :deep(em) { font-style: italic; }

@media (min-width: 769px) {
  .main { padding: 28px 24px 64px; }
  .guide :deep(.guide-h1) { font-size: 1.9rem; }
}
</style>
