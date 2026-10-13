<template>
  <div class="page">
    <AppHeader />
    <main class="main">
      <h1 class="page__title">{{ t('settings.title') }}</h1>

      <!-- Zustand -->
      <section class="card card--status" :class="status.ready ? 'ok' : 'warn'">
        <span class="dot"></span>
        <div class="card--status__text">
          <strong v-if="status.ready">{{ t('settings.ready') }}</strong>
          <strong v-else>{{ t('settings.notReady') }}</strong>
          <small v-if="status.ready">{{ status.llm_model }}<template v-if="status.loaded"> · {{ t('settings.loadedNow') }}</template> · {{ t('settings.memoryIs', { where: memoryLabel }) }}</small>
          <small v-else>{{ t('settings.notReadyHint') }}</small>
        </div>
      </section>

      <!-- Modell -->
      <section class="card">
        <h2 class="card__title">{{ t('settings.model') }}</h2>
        <p class="card__sub">{{ t('settings.modelHint') }}</p>
        <label class="field">
          <span class="field__label">{{ t('settings.provider') }}</span>
          <select v-model="cfg.llm_provider" class="field__input">
            <option value="ollama">{{ t('settings.pOllama') }}</option>
            <option value="lmstudio">{{ t('settings.pLmstudio') }}</option>
            <option value="local">{{ t('settings.pLocal') }}</option>
            <option value="openai">OpenAI</option>
          </select>
        </label>
        <template v-if="cfg.llm_provider === 'openai'">
          <label class="field"><span class="field__label">{{ t('settings.apiKey') }}</span><input type="password" v-model="cfg.llm_api_key" class="field__input" placeholder="sk-…" autocomplete="off"></label>
          <label class="field"><span class="field__label">{{ t('settings.address') }}</span><input type="url" v-model="cfg.llm_base_url" class="field__input" placeholder="https://api.openai.com/v1"></label>
          <label class="field"><span class="field__label">{{ t('settings.modelName') }}</span>
            <select v-if="models.length" v-model="cfg.llm_model_name" class="field__input">
              <option v-for="m in withCurrent(models, cfg.llm_model_name)" :key="m.name" :value="m.name">{{ m.name }}</option>
            </select>
            <input v-else type="text" v-model="cfg.llm_model_name" class="field__input" placeholder="gpt-4o-mini"></label>
        </template>
        <template v-else>
          <label class="field"><span class="field__label">{{ t('settings.address') }}</span><input type="url" v-model="cfg.local_llm_base_url" class="field__input" placeholder="http://127.0.0.1:11434/v1"></label>
          <div class="field">
            <div class="field__row">
              <span class="field__label">{{ t('settings.mainModel') }}</span>
              <button type="button" class="linkbtn linkbtn--sm" :disabled="scanning" @click="scan">
                <span v-if="scanning" class="spin spin--sm"></span>{{ scanning ? t('settings.scanning') : t('settings.rescan') }}
              </button>
            </div>
            <select v-if="models.length" v-model="cfg.local_llm_model_name" class="field__input">
              <option v-for="m in withCurrent(models, cfg.local_llm_model_name)" :key="m.name" :value="m.name">{{ optionLabel(m) }}</option>
            </select>
            <input v-else type="text" v-model="cfg.local_llm_model_name" class="field__input" :placeholder="t('settings.modelPh')">
            <span class="field__hint">{{ models.length ? t('settings.mainModelHint') : (scanned ? t('settings.noModels') : t('settings.modelNameHint')) }}</span>
          </div>
          <div class="field">
            <span class="field__label">{{ t('settings.agentModel') }}</span>
            <select v-if="models.length" v-model="cfg.llm_model_name" class="field__input">
              <option v-for="m in withCurrent(models, cfg.llm_model_name)" :key="m.name" :value="m.name">{{ optionLabel(m) }}</option>
            </select>
            <input v-else type="text" v-model="cfg.llm_model_name" class="field__input" :placeholder="t('settings.modelPh')">
            <span class="field__hint">{{ t('settings.agentModelHint') }}</span>
          </div>
          <label class="field"><span class="field__label">{{ t('settings.localKey') }}</span><input type="password" v-model="cfg.local_llm_api_key" class="field__input" autocomplete="off"></label>
        </template>
      </section>

      <!-- Gedächtnis -->
      <section class="card">
        <h2 class="card__title">{{ t('settings.memory') }}</h2>
        <p class="card__sub">{{ t('settings.memoryHint') }}</p>
        <label class="field">
          <span class="field__label">{{ t('settings.storage') }}</span>
          <select v-model="cfg.memory_provider" class="field__input">
            <option value="obsidian">{{ t('settings.mLocal') }}</option>
            <option value="zep">Zep Cloud</option>
            <option value="hybrid">{{ t('settings.mHybrid') }}</option>
          </select>
        </label>
        <label class="field" v-if="cfg.memory_provider !== 'obsidian'">
          <span class="field__label">{{ t('settings.zepKey') }}</span>
          <input type="password" v-model="cfg.zep_api_key" class="field__input" autocomplete="off">
        </label>
        <p v-if="masked" class="notice">{{ t('settings.masked') }}</p>
      </section>

      <div class="actions">
        <button type="button" class="btn btn--primary" :disabled="saving" @click="save">{{ saving ? t('settings.saving') : t('settings.save') }}</button>
        <button type="button" class="btn" :disabled="testing" @click="test"><span v-if="testing" class="spin"></span>{{ testing ? t('settings.testing') : t('settings.test') }}</button>
      </div>
      <p v-if="result" class="notice" :class="result.ok ? 'notice--ok' : 'notice--err'" role="status">{{ result.text }}</p>

      <!-- Darstellung -->
      <section class="card">
        <h2 class="card__title">{{ t('settings.look') }}</h2>
        <button type="button" class="rowbtn" @click="showTheme = true">
          <span class="swatch"></span>
          <span class="rowbtn__text"><strong>{{ t('settings.colors') }}</strong><small>{{ t('settings.colorsHint') }}</small></span>
          <span class="rowbtn__chev">›</span>
        </button>
        <div class="langrow">
          <span class="langrow__label">{{ t('settings.language') }}</span>
          <div class="seg" role="radiogroup" :aria-label="t('settings.language')">
            <button type="button" role="radio" :aria-checked="locale === 'de'" :class="{ on: locale === 'de' }" @click="setLang('de')">Deutsch</button>
            <button type="button" role="radio" :aria-checked="locale === 'en'" :class="{ on: locale === 'en' }" @click="setLang('en')">English</button>
          </div>
        </div>
      </section>

      <!-- Über -->
      <section class="card card--about">
        <img src="/logo-mark.svg" alt="" width="36" height="36" />
        <div>
          <strong>MiroFish</strong>
          <small>{{ t('settings.aboutText') }}</small>
          <a href="https://github.com/BEKO2210/MiroFish-DE" target="_blank" rel="noopener">{{ t('settings.source') }}</a>
        </div>
      </section>
    </main>
    <ThemePicker :open="showTheme" @close="showTheme = false" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import AppHeader from '../components/AppHeader.vue'
import ThemePicker from '../components/ThemePicker.vue'
import service from '../api/index'

const { t, locale } = useI18n()
const setLang = (l) => { locale.value = l; try { localStorage.setItem('lang', l) } catch (e) { /* privater Modus */ } document.documentElement.lang = l }
const status = ref({ ready: false, llm_model: '', memory_provider: '' })
const cfg = ref({ llm_provider: 'ollama', llm_api_key: '', llm_base_url: '', llm_model_name: '', local_llm_base_url: '', local_llm_model_name: '', local_llm_api_key: '', zep_api_key: '', memory_provider: 'obsidian' })
const saving = ref(false), testing = ref(false), result = ref(null), showTheme = ref(false)
const memoryLabel = computed(() => ({ obsidian: t('settings.wLocal'), zep: t('settings.wZep'), hybrid: t('settings.wHybrid') }[status.value.memory_provider] || status.value.memory_provider))
const masked = computed(() => Object.values(cfg.value).some(v => typeof v === 'string' && v.includes('...****')))

const models = ref([]), scanning = ref(false), scanned = ref(false)
const baseUrl = () => (cfg.value.llm_provider === 'openai' ? cfg.value.llm_base_url : cfg.value.local_llm_base_url)
// Installierte Modelle vom eingetragenen Server holen (auch vor dem Speichern)
const scan = async () => {
  scanning.value = true
  try {
    const res = await service.get('/api/graph/system/models', { params: { provider: cfg.value.llm_provider, base_url: baseUrl() } })
    models.value = res?.data?.models || []
  } catch (e) { models.value = [] } finally { scanning.value = false; scanned.value = true }
}
// Gespeichertes Modell, das (noch) nicht installiert ist, trotzdem als Option zeigen
const withCurrent = (list, cur) => (cur && !list.some(m => m.name === cur) ? [{ name: cur, missing: true }, ...list] : list)
const optionLabel = (m) => {
  if (m.missing) return `${m.name} · ${t('settings.notInstalled')}`
  const parts = [m.name]
  if (m.size_gb) parts.push(`${m.size_gb.toLocaleString(locale.value === 'en' ? 'en-GB' : 'de-DE')} GB`)
  if (m.loaded) parts.push(t('settings.loadedNow'))
  return parts.join(' · ')
}
const load = async () => {
  try {
    const res = await service.get('/api/graph/system/status')
    if (res?.success) {
      const d = res.data
      status.value = { ready: d.reachable && d.model_installed, llm_model: d.llm_model, memory_provider: d.memory_provider, loaded: (d.loaded_models || []).includes(d.llm_model) }
      if (d.config) cfg.value = { ...cfg.value, ...d.config }
    }
  } catch (e) { status.value.ready = false }
}
watch(() => [cfg.value.llm_provider, baseUrl()], () => { scanned.value = false; models.value = [] })
const save = async () => {
  saving.value = true; result.value = null
  try {
    const res = await service.post('/api/graph/system/config', cfg.value)
    if (res?.success) { result.value = { ok: true, text: t('settings.saved') }; await load(); scan() }
  } catch (e) { result.value = { ok: false, text: t('settings.saveFailed', { msg: e.response?.data?.error || e.message }) } }
  finally { saving.value = false }
}
const test = async () => {
  testing.value = true; result.value = null
  try {
    const res = await service.post('/api/graph/system/test-llm')
    if (res?.success) result.value = { ok: true, text: t('settings.testOk', { model: res.data.model }) }
  } catch (e) { result.value = { ok: false, text: t('settings.testFailed', { msg: e.response?.data?.error || e.message }) } }
  finally { testing.value = false }
}
onMounted(async () => { await load(); scan() })
</script>

<style scoped>
.page { min-height: 100vh; background: var(--color-bg-canvas); color: var(--color-text-primary); }
.main { max-width: 680px; margin: 0 auto; padding: 20px 16px 32px; }
.page__title { font-family: var(--font-heading); font-size: 26px; margin: 0 0 14px; letter-spacing: -0.01em; }
.card { background: var(--color-bg-surface-raised); border: 1px solid var(--color-border-subtle); border-radius: 16px; padding: 18px; margin-bottom: 12px; }
.card__title { font-family: var(--font-heading); font-size: 17px; margin: 0; }
.card__sub { margin: 4px 0 10px; font-size: 13px; color: var(--color-text-muted); }
.card--status { display: flex; align-items: center; gap: 12px; }
.card--status .dot { width: 12px; height: 12px; border-radius: 50%; background: var(--color-success-text); box-shadow: 0 0 0 4px var(--color-success-bg); flex: none; }
.card--status.warn .dot { background: var(--color-warning-text); box-shadow: 0 0 0 4px var(--color-warning-bg); }
.card--status__text { display: flex; flex-direction: column; }
.card--status__text small { color: var(--color-text-muted); font-size: 13px; }
.field { display: block; margin-top: 12px; }
.field__label { display: block; font-size: 13px; font-weight: 600; color: var(--color-text-secondary); margin-bottom: 6px; }
.field__input { width: 100%; font: inherit; font-size: 16px; padding: 12px 14px; border: 1px solid var(--color-border-default); border-radius: 12px; background: var(--color-bg-surface-raised); color: inherit; }
.field__input:focus { outline: none; border-color: var(--color-brand-primary); box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-brand-primary) 15%, transparent); }
.field__row { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 6px; }
.field__row .field__label { margin-bottom: 0; }
.linkbtn--sm { display: inline-flex; align-items: center; gap: 6px; background: none; border: 0; color: var(--color-brand-primary); font: inherit; font-size: 13px; font-weight: 600; cursor: pointer; padding: 6px 0; min-height: 32px; }
.spin--sm { width: 12px; height: 12px; }
.field__hint { display: block; font-size: 12px; color: var(--color-text-muted); margin-top: 6px; }
.actions { display: flex; gap: 10px; margin: 4px 0 12px; }
.btn { flex: 1; min-height: 48px; border-radius: 12px; border: 1px solid var(--color-border-subtle); background: var(--color-bg-surface-raised); color: inherit; font: inherit; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; gap: 8px; }
.btn--primary { background: var(--color-brand-primary); border-color: var(--color-brand-primary); color: var(--color-brand-on-primary); }
.btn:disabled { opacity: .6; cursor: not-allowed; }
.spin { width: 16px; height: 16px; border: 2px solid var(--color-border-default); border-top-color: var(--color-brand-primary); border-radius: 50%; animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.notice { margin: 10px 0 0; padding: 10px 12px; border-radius: 10px; background: var(--color-warning-bg); color: var(--color-warning-text); font-size: 14px; }
.notice--ok { background: var(--color-success-bg); color: var(--color-success-text); }
.notice--err { background: var(--color-error-bg); color: var(--color-error-text); }
.rowbtn { width: 100%; display: flex; align-items: center; gap: 12px; margin-top: 10px; padding: 10px 4px; background: none; border: 0; font: inherit; color: inherit; cursor: pointer; text-align: left; min-height: 52px; }
.rowbtn__text { display: flex; flex-direction: column; flex: 1; }
.rowbtn__text small { color: var(--color-text-muted); font-size: 12px; }
.rowbtn__chev { font-size: 22px; color: var(--color-text-muted); }
.swatch { width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, var(--theme-light, #fff) 50%, var(--color-brand-primary) 50%); border: 1px solid var(--color-border-default); }
.langrow { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 10px 4px 0; border-top: 1px solid var(--color-border-subtle); margin-top: 6px; }
.langrow__label { font-weight: 600; }
.seg { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; padding: 4px; background: var(--color-bg-surface-subtle); border-radius: 12px; min-width: 200px; }
.seg button { min-height: 40px; border: 0; border-radius: 9px; background: transparent; font: inherit; font-weight: 600; font-size: 14px; color: var(--color-text-secondary); cursor: pointer; }
.seg button.on { background: var(--color-bg-surface-raised); color: var(--color-text-primary); box-shadow: 0 1px 3px rgba(0,0,0,.12); }
.card--about { display: flex; gap: 14px; align-items: flex-start; }
.card--about div { display: flex; flex-direction: column; gap: 4px; }
.card--about small { color: var(--color-text-muted); font-size: 13px; line-height: 1.45; }
.card--about a { color: var(--color-brand-primary); font-size: 14px; }
@media (min-width: 769px) { .main { padding: 32px 24px 64px; } }
</style>
