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
  s = escapeHtml(s)
  s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  s = s.replace(/\*(.+?)\*/g, '<em>$1</em>')
  s = s.replace(/\n/g, '<br>')
  return s
}

function escapeHtml(s) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function formatInline(s) {
  return escapeHtml(s)
    .replace(/\*\*([^*\n]+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*\n]+?)\*/g, '<em>$1</em>')
}

/**
 * Markdown für Leitfäden: Überschriften, Listen, Checklisten, Absätze.
 * @param {string} text
 * @returns {string} HTML
 */
export function renderGuideMarkdown(text) {
  if (text == null || text === '') return ''
  const lines = String(text).replace(/\r\n/g, '\n').split('\n')
  const out = []
  let listType = null

  function closeList() {
    if (!listType) return
    out.push(listType === 'ol' ? '</ol>' : '</ul>')
    listType = null
  }

  function openList(type) {
    if (listType === type) return
    closeList()
    out.push(type === 'ol' ? '<ol class="guide-ol">' : '<ul class="guide-ul">')
    listType = type
  }

  function pushLi(html, className) {
    out.push(className ? `<li class="${className}">${html}</li>` : `<li>${html}</li>`)
  }

  for (const raw of lines) {
    const trimmed = raw.trimEnd().trim()
    if (!trimmed) {
      closeList()
      continue
    }
    if (/^---+$/.test(trimmed)) {
      closeList()
      out.push('<hr class="guide-hr">')
      continue
    }
    const heading = trimmed.match(/^(#{1,4})\s+(.+)$/)
    if (heading) {
      closeList()
      const tag = `h${heading[1].length}`
      out.push(`<${tag} class="guide-${tag}">${formatInline(heading[2])}</${tag}>`)
      continue
    }
    const check = trimmed.match(/^- \[[ xX]\]\s+(.+)$/)
    if (check) {
      openList('ul')
      pushLi(formatInline(check[1]), 'guide-check')
      continue
    }
    const ul = trimmed.match(/^[-*]\s+(.+)$/)
    if (ul) {
      openList('ul')
      pushLi(formatInline(ul[1]))
      continue
    }
    const ol = trimmed.match(/^\d+\.\s+(.+)$/)
    if (ol) {
      openList('ol')
      pushLi(formatInline(ol[1]))
      continue
    }
    closeList()
    out.push(`<p class="guide-p">${formatInline(trimmed)}</p>`)
  }
  closeList()
  return out.join('')
}
