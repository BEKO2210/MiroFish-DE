/**
 * Sichere Anzeige von Beitragstexten: Escape-Reste bereinigen,
 * HTML escapen, dann *kursiv* / **fett** und Zeilenumbrüche.
 * @param {string} text
 * @returns {string} HTML-Fragment (nur em/strong/br)
 */
export function formatRichText(text) {
  if (text == null || text === '') return ''
  let s = String(text)
  s = s.replace(/\\"/g, '"').replace(/\\n/g, '\n').replace(/\\t/g, '\t')
  s = s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
  s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  s = s.replace(/\*(.+?)\*/g, '<em>$1</em>')
  s = s.replace(/\n/g, '<br>')
  return s
}
