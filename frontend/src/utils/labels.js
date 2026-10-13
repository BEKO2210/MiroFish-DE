/**
 * Lesbare Anzeige von Ontologie-Namen. Daten/API bleiben unverändert.
 * @param {string} name
 * @param {'type'|'relation'} [kind='type']
 * @returns {string}
 */
export function formatLabel(name, kind = 'type') {
  if (name == null || name === '') return ''
  const s = String(name)
  if (kind === 'relation') {
    return s.replace(/_/g, ' ').toLowerCase().trim()
  }
  return s
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .replace(/_/g, ' ')
    .trim()
}
