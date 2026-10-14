<template>
  <router-link v-if="state.loaded" to="/settings" class="priv" :class="isLocal ? 'priv--local' : 'priv--cloud'"
    :title="label" :aria-label="label" data-testid="privacy-badge">
    <svg v-if="isLocal" class="priv__ico" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>
    <svg v-else class="priv__ico" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 18a4 4 0 0 1-.5-7.97A5.5 5.5 0 0 1 17 8.5a4.75 4.75 0 0 1 0 9.5z"/></svg>
    <span class="priv__text">{{ isLocal ? t('privacy.localShort') : t('privacy.cloudShort', { provider: name }) }}</span>
  </router-link>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useLlmLocality, refreshLlmStatus } from '../composables/useLlmLocality'

const { t } = useI18n()
const { state, isLocal, provider } = useLlmLocality()
const name = computed(() => provider.value || t('privacy.unknownProvider'))
const label = computed(() => isLocal.value ? t('privacy.local') : t('privacy.cloud', { provider: name.value }))

onMounted(() => { if (!state.loaded) refreshLlmStatus() })
</script>

<style scoped>
.priv { display: inline-flex; align-items: center; justify-content: center; gap: 6px; min-width: 44px; min-height: 44px; box-sizing: border-box; padding: 0; border-radius: 999px; text-decoration: none; font-size: 13px; font-weight: 500; border: 1px solid var(--color-border-subtle); background: var(--color-bg-surface-raised); color: var(--color-text-secondary); }
.priv--cloud { color: var(--color-warning-text); background: var(--color-warning-bg); border-color: var(--color-warning-border); font-weight: 600; }
.priv__text { display: none; }
@media (min-width: 769px) {
  .priv { padding: 0 14px; }
  .priv__text { display: inline; max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
}
</style>
