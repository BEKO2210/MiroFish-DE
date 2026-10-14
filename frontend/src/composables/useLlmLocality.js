import { reactive, computed } from 'vue'
import service from '../api/index'

const LOCAL_PROVIDERS = ['ollama', 'lmstudio', 'local']
const KNOWN = [
  [/openai\.com$/, 'OpenAI'],
  [/anthropic\.com$/, 'Anthropic'],
  [/openrouter\.ai$/, 'OpenRouter'],
  [/groq\.com$/, 'Groq'],
  [/mistral\.ai$/, 'Mistral'],
  [/googleapis\.com$/, 'Google'],
  [/deepseek\.com$/, 'DeepSeek'],
  [/together\.(ai|xyz)$/, 'Together AI'],
  [/azure\.com$/, 'Azure OpenAI'],
]

const state = reactive({ loaded: false, provider: '', host: '' })

function hostOf(url) {
  const m = String(url || '').trim().match(/^(?:[a-z][a-z0-9+.-]*:\/\/)?(?:[^@/]*@)?(\[[^\]]+\]|[^:/?#]+)/i)
  return m ? m[1].replace(/^\[|\]$/g, '').toLowerCase() : ''
}

/** localhost, Docker-Host, LAN, Tailscale (100.64/10, *.ts.net) */
export function isPrivateHost(host) {
  if (!host) return false
  if (host === 'localhost' || host === '::1' || host === 'host.docker.internal') return true
  if (/\.(local|lan|internal|ts\.net)$/.test(host)) return true
  if (host.startsWith('fe80:') || /^f[cd][0-9a-f]{2}:/.test(host)) return true
  const p = host.match(/^(\d+)\.(\d+)\.(\d+)\.(\d+)$/)
  if (!p) return false
  const [a, b] = [Number(p[1]), Number(p[2])]
  return a === 127 || a === 10 || (a === 192 && b === 168) || (a === 172 && b >= 16 && b <= 31)
    || (a === 100 && b >= 64 && b <= 127) || (a === 169 && b === 254)
}

function cloudName(host) {
  for (const [re, name] of KNOWN) if (re.test(host)) return name
  return host || ''
}

/** Nur Anbieter und Host werden gehalten – nie Schlüssel oder volle Adresse. */
export function setLlmStatus(d) {
  const cfg = d?.config || {}
  state.provider = String(d?.llm_provider || cfg.llm_provider || '').toLowerCase()
  state.host = hostOf(d?.llm_base_url || cfg.llm_base_url || '')
  state.loaded = true
}

export async function refreshLlmStatus() {
  try {
    const res = await service.get('/api/graph/system/status')
    if (res?.success) setLlmStatus(res.data)
  } catch { /* Anzeige bleibt aus */ }
}

export function useLlmLocality() {
  const isLocal = computed(() => {
    if (LOCAL_PROVIDERS.includes(state.provider)) return true
    return isPrivateHost(state.host)
  })
  const provider = computed(() => cloudName(state.host) || state.provider)
  return { state, isLocal, provider }
}
