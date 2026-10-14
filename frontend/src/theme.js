/**
 * Farbsystem: Jede Zwei-Farben-Combo aus Combo Studio (combo.it-handwerk-stuttgart.de, CC0, 1 Mio. Combos,
 * alle WCAG >= 3:1 in beide Richtungen) wird zu einem vollständigen Satz CSS-Variablen. Die Wahl liegt im
 * Browserspeicher und wird beim Start wieder angewendet.
 */
const KEY = 'mirofish:theme'
export const COMBO_SITE = 'https://combo.it-handwerk-stuttgart.de'

// Standard: MiroFish-Terracotta auf Weiß (identisch zu tokens.css)
export const DEFAULT_THEME = { id: null, a: '#FFFFFF', aName: 'Weiß', b: '#D8401A', bName: 'MiroFish-Orange', mode: 'soft' }

// Aus dem Katalog gezogen (eine je Farbfamilie), echte Combo-Nummern
export const PRESETS = [
  { id: 504297, a: '#FCD3B5', aName: 'Sensual Peach', b: '#130F0B', bName: 'Nuln Oil' },
  { id: 492213, a: '#FCC0B3', aName: 'Ruffled Parasol', b: '#170E0D', bName: 'Nuln Oil' },
  { id: 501429, a: '#4B1B25', aName: 'Vino Tinto', b: '#F7F2F3', bName: 'Bright White' },
  { id: 498331, a: '#FAF3FA', aName: 'Walkie Chalkie', b: '#BD1CC7', bName: 'Fuchsia Flair' },
  { id: 496108, a: '#0C0C11', aName: 'Midnight Oil', b: '#C4BEFE', bName: 'Lavender Tonic' },
  { id: 508892, a: '#0E0F12', aName: 'Ruined Smores', b: '#C8DDFE', bName: 'Arc Light' },
  { id: 508007, a: '#E7F1F6', aName: 'Clear Vision', b: '#0B303F', bName: 'NATO Blue' },
  { id: 495586, a: '#4FDDE9', aName: 'Blue Dacnis', b: '#131E1F', bName: 'Black Feather' },
  { id: 501771, a: '#1B211E', aName: 'Shadow Warrior', b: '#27FBCC', bName: 'Bright Teal' },
  { id: 502834, a: '#191F18', aName: 'Black Emerald', b: '#5FEC3E', bName: 'Miyazaki Verdant' },
  { id: 506296, a: '#C5F83A', aName: 'Yellow Green', b: '#0B0D05', bName: 'Smoky Black' },
  { id: 500894, a: '#F4EFE9', aName: 'Silk Pillow', b: '#57400E', bName: 'Smoked Oak Brown' }
]

// ---- Farbmathematik -------------------------------------------------------
const hexToRgb = (hex) => {
  const h = hex.replace('#', '')
  const n = parseInt(h.length === 3 ? h.split('').map(c => c + c).join('') : h, 16)
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}
const rgbToHex = ([r, g, b]) => '#' + [r, g, b].map(v => Math.round(Math.max(0, Math.min(255, v))).toString(16).padStart(2, '0')).join('')
const lin = (c) => { c /= 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4 }
export const luminance = (hex) => { const [r, g, b] = hexToRgb(hex); return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b) }
export const contrast = (h1, h2) => { const a = luminance(h1), b = luminance(h2); return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05) }
export const mix = (h1, h2, w) => { // w = Anteil von h1
  const a = hexToRgb(h1), b = hexToRgb(h2)
  return rgbToHex(a.map((v, i) => v * w + b[i] * (1 - w)))
}
// Buntheit absolut (max-min): bei "Neutral"-Combos (fast schwarz + getöntes Pastell) gewinnt so das Pastell als Akzent
const saturation = (hex) => { const [r, g, b] = hexToRgb(hex); return Math.max(r, g, b) - Math.min(r, g, b) }
/** Farbe Richtung `towards` schieben, bis der Kontrast zu `bg` erreicht ist (für Fließtext 4.5:1). */
const ensureContrast = (color, bg, min = 4.5, best = false) => {
  const towards = best ? (contrast('#000000', bg) >= contrast('#FFFFFF', bg) ? '#000000' : '#FFFFFF') : luminance(bg) > 0.5 ? '#000000' : '#FFFFFF'
  let c = color
  for (let i = 0; i < 40 && contrast(c, bg) < min; i++) c = mix(c, towards, 0.93)
  return c
}
export const isValidHex = (s) => /^#?[0-9a-f]{6}$/i.test(s || '')
const norm = (s) => ('#' + s.replace('#', '')).toUpperCase()

// Statusfarben behalten ihre Bedeutung (Farbton), passen aber Kontrast/Flächen an die Combo an
const STATUS_HUES = { success: '#15803D', warning: '#A16207', error: '#B91C1C', info: '#1D4ED8' }
function statusVars(canvas) {
  const vars = {}
  for (const [name, hue] of Object.entries(STATUS_HUES)) {
    const bg = mix(hue, canvas, 0.1)
    vars[`--color-${name}-text`] = ensureContrast(hue, bg, 4.5, true)
    vars[`--color-${name}-bg`] = bg
    vars[`--color-${name}-border`] = mix(hue, canvas, 0.4)
  }
  const fill = vars['--color-error-text']
  vars['--color-on-error'] = contrast(fill, '#FFFFFF') >= contrast(fill, '#0F172A') ? '#FFFFFF' : '#0F172A'
  return vars
}

// ---- Ableitung der Variablen ---------------------------------------------
export function deriveVars(theme) {
  const a = norm(theme.a), b = norm(theme.b)
  const light = luminance(a) >= luminance(b) ? a : b
  const dark = light === a ? b : a
  const accentRaw = saturation(a) >= saturation(b) ? a : b
  const full = theme.mode === 'full'
  const lightIsLight = luminance(light) > 0.4
  const canvas = full ? light : (lightIsLight ? mix(light, '#FFFFFF', 0.35) : '#FFFFFF')
  const darkCanvas = luminance(canvas) <= 0.4
  const ink = darkCanvas ? '#FFFFFF' : '#000000'
  const text = ensureContrast(full ? dark : mix(dark, ink, 0.6), canvas, 7)
  const accent = ensureContrast(accentRaw, canvas, 4.5)
  const onAccent = contrast(accent, '#FFFFFF') >= contrast(accent, '#0F172A') ? '#FFFFFF' : '#0F172A'
  const surface = mix(canvas, darkCanvas ? '#FFFFFF' : '#000000', 0.97)
  return {
    '--color-bg-canvas': canvas,
    '--color-bg-surface': surface,
    // Karten und Felder: hellere (bzw. bei dunklem Grund etwas hellere) Abstufung der Combo statt reinem Weiß
    '--color-bg-surface-raised': darkCanvas ? mix(canvas, '#FFFFFF', 0.9) : mix(canvas, '#FFFFFF', 0.45),
    '--color-bg-surface-subtle': mix(canvas, ink, 0.94),
    '--color-text-primary': text,
    '--color-text-secondary': ensureContrast(mix(text, canvas, 0.8), canvas, 7),
    '--color-text-muted': ensureContrast(mix(text, canvas, 0.6), canvas, 4.5),
    '--color-text-inverse': canvas,
    '--color-border-subtle': mix(text, canvas, 0.12),
    '--color-border-default': mix(text, canvas, 0.22),
    '--color-border-strong': mix(text, canvas, 0.45),
    '--color-brand-primary': accent,
    '--color-brand-hover': mix(accent, ink, 0.82),
    '--color-brand-active': mix(accent, ink, 0.7),
    '--color-brand-subtle': mix(accent, canvas, 0.1),
    '--color-brand-border': mix(accent, canvas, 0.45),
    '--color-brand-on-primary': onAccent,
    '--color-focus-ring': accent,
    ...statusVars(canvas),
    '--theme-light': light,
    '--theme-dark': dark
  }
}

export function applyTheme(theme) {
  const root = document.documentElement
  if (!theme || theme.id === null && theme.a === DEFAULT_THEME.a && theme.b === DEFAULT_THEME.b && theme.mode !== 'full') {
    Object.keys(deriveVars(DEFAULT_THEME)).forEach(k => root.style.removeProperty(k))
    root.dataset.themeDark = ''
    return
  }
  const vars = deriveVars(theme)
  Object.entries(vars).forEach(([k, v]) => root.style.setProperty(k, v))
  root.dataset.themeDark = luminance(vars['--color-bg-canvas']) <= 0.4 ? '1' : ''
  const meta = document.querySelector('meta[name="theme-color"]')
  if (meta) meta.setAttribute('content', vars['--color-bg-canvas'])
}

export function saveTheme(theme) {
  try { localStorage.setItem(KEY, JSON.stringify(theme)) } catch (e) { /* privater Modus */ }
  applyTheme(theme)
}
export function loadTheme() {
  try { const t = JSON.parse(localStorage.getItem(KEY) || 'null'); return t && isValidHex(t.a) && isValidHex(t.b) ? t : { ...DEFAULT_THEME } } catch (e) { return { ...DEFAULT_THEME } }
}
export function resetTheme() {
  try { localStorage.removeItem(KEY) } catch (e) { /* egal */ }
  applyTheme(DEFAULT_THEME)
}

// ---- Combo Studio ---------------------------------------------------------
/** Combo per Katalognummer (1 … 1.000.000) laden. */
export async function fetchCombo(id) {
  id = Number(id)
  if (!Number.isInteger(id) || id < 1 || id > 1000000) throw new Error('Combo-Nummer muss zwischen 1 und 1.000.000 liegen')
  const shard = String(Math.floor((id - 1) / 1000)).padStart(4, '0')
  const res = await fetch(`${COMBO_SITE}/api/v1/combos/${shard}.json`)
  if (!res.ok) throw new Error('Combo Studio nicht erreichbar')
  const data = await res.json()
  const row = data.combos.find(c => c[0] === id)
  if (!row) throw new Error('Combo nicht gefunden')
  return { id: row[0], a: row[1], aName: row[2], b: row[3], bName: row[4], style: row[5], family: row[6] }
}
export const randomComboId = () => 1 + Math.floor(Math.random() * 1000000)

/** Eingabe deuten: "482913", "#482913", Link mit #482913, oder "RRGGBB-RRGGBB". */
export function parseComboInput(s) {
  s = (s || '').trim()
  const pair = s.match(/#?([0-9a-f]{6})-([0-9a-f]{6})/i)
  if (pair) return { pair: ['#' + pair[1].toUpperCase(), '#' + pair[2].toUpperCase()] }
  const id = s.match(/#?(\d{1,7})\s*$/)
  if (id) return { id: Number(id[1]) }
  return null
}
