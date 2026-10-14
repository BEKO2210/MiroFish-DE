import i18n from '../i18n'

export function formatNumber(value, options = {}) {
  const n = Number(value)
  if (!Number.isFinite(n)) return String(value)
  const lang = i18n.global.locale.value === 'en' ? 'en-GB' : 'de-DE'
  return new Intl.NumberFormat(lang, options).format(n)
}
