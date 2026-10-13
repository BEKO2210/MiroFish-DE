<template>
  <div class="language-switcher" :aria-label="t('common.language')">
    <button
      type="button"
      class="language-button"
      :class="{ active: locale === 'de' }"
      :aria-pressed="locale === 'de'"
      @click="selectLanguage('de')"
    >DE</button>
    <span class="language-divider">|</span>
    <button
      type="button"
      class="language-button"
      :class="{ active: locale === 'en' }"
      :aria-pressed="locale === 'en'"
      @click="selectLanguage('en')"
    >EN</button>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const { locale, t } = useI18n()

const selectLanguage = (language) => {
  locale.value = language
  localStorage.setItem('lang', language)
  document.documentElement.lang = language
}
</script>

<style scoped>
.language-switcher {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;
  font-size: 12px;
  letter-spacing: 0.08em;
}

.language-button {
  padding: 2px 3px;
  border: 0;
  color: #777;
  background: transparent;
  cursor: pointer;
  font: inherit;
}

.language-button:hover,
.language-button.active {
  color: #000;
  font-weight: 700;
}

.language-divider {
  color: #bbb;
}
</style>
