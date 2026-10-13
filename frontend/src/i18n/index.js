import { createI18n } from 'vue-i18n'
import de from './de.json'
import en from './en.json'

const savedLanguage = localStorage.getItem('lang')
const browserLanguage = navigator.language?.toLowerCase().startsWith('en') ? 'en' : 'de'
const initialLanguage = ['de', 'en'].includes(savedLanguage) ? savedLanguage : browserLanguage

document.documentElement.lang = initialLanguage

export default createI18n({
  legacy: false,
  locale: initialLanguage,
  fallbackLocale: 'de',
  messages: { de, en }
})
