import i18n from '../i18n'

export function formatNumber(value, options = {}) {
  if (value == null) return '—'
  const n = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(n)) return '—'
  const lang = i18n.global.locale.value === 'en' ? 'en-GB' : 'de-DE'
  return new Intl.NumberFormat(lang, options).format(n)
}
