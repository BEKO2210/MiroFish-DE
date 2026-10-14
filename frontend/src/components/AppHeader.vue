<template>
  <header class="appbar">
    <router-link to="/" class="appbar__brand" :aria-label="t('nav.homeAria')">
      <img src="/logo-mark.svg" alt="" width="28" height="28" />
      <span>MiroFish</span>
    </router-link>
    <nav class="appbar__nav" :aria-label="t('nav.start')">
      <router-link to="/" :class="{ on: route.path === '/' }">{{ t('nav.start') }}</router-link>
      <router-link to="/history" :class="{ on: route.path.startsWith('/history') }">{{ t('nav.history') }}</router-link>
      <router-link to="/settings" :class="{ on: route.path.startsWith('/settings') }">{{ t('nav.settings') }}</router-link>
    </nav>
    <div class="appbar__right">
      <slot />
      <button type="button" class="appbar__icon" :aria-label="t('nav.colors')" :title="t('nav.colors')" @click="showTheme = true">
        <span class="appbar__swatch"></span>
      </button>
    </div>
    <ThemePicker :open="showTheme" @close="showTheme = false" />
  </header>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import ThemePicker from './ThemePicker.vue'

const route = useRoute()
const { t } = useI18n()
const showTheme = ref(false)
</script>

<style scoped>
.appbar { position: sticky; top: 0; z-index: 30; display: flex; align-items: center; gap: 16px; padding: 10px 16px; min-height: 56px;
  background: color-mix(in srgb, var(--color-bg-canvas) 88%, transparent); backdrop-filter: saturate(180%) blur(14px); -webkit-backdrop-filter: saturate(180%) blur(14px);
  border-bottom: 1px solid var(--color-border-subtle); }
.appbar__brand { display: inline-flex; align-items: center; gap: 10px; min-height: 44px; text-decoration: none; color: var(--color-text-primary); font-family: var(--font-heading); font-weight: 700; font-size: 18px; letter-spacing: -0.01em; }
.appbar__nav { display: none; gap: 4px; margin-left: 8px; }
.appbar__nav a { text-decoration: none; color: var(--color-text-secondary); font-size: 14px; font-weight: 500; padding: 0 12px; min-height: 44px; display: inline-flex; align-items: center; border-radius: 999px; }
.appbar__nav a:hover { background: var(--color-bg-surface-subtle); }
.appbar__nav a.on { background: var(--color-text-primary); color: var(--color-text-inverse); }
.appbar__right { margin-left: auto; display: inline-flex; align-items: center; gap: 8px; }
.appbar__icon { width: 44px; height: 44px; border: 1px solid var(--color-border-subtle); border-radius: 50%; background: var(--color-bg-surface-raised); display: inline-flex; align-items: center; justify-content: center; cursor: pointer; padding: 0; }
.appbar__swatch { width: 18px; height: 18px; border-radius: 50%; background: linear-gradient(135deg, var(--theme-light, #fff) 50%, var(--color-brand-primary) 50%); border: 1px solid var(--color-border-default); }
@media (min-width: 769px) {
  .appbar { padding: 10px 24px; }
  .appbar__nav { display: inline-flex; }
}
</style>
