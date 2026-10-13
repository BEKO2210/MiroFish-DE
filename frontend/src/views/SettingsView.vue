<template>
  <div class="page">
    <AppHeader />
    <main class="main">
      <h1 class="page__title">Einstellungen</h1>

      <!-- Zustand -->
      <section class="card card--status" :class="status.ready ? 'ok' : 'warn'">
        <span class="dot"></span>
        <div class="card--status__text">
          <strong v-if="status.ready">Bereit – Modell antwortet</strong>
          <strong v-else>Noch nicht verbunden</strong>
          <small v-if="status.ready">{{ status.llm_model }} · Gedächtnis {{ memoryLabel }}</small>
          <small v-else>Trage unten die Adresse deines Sprachmodells ein und prüfe die Verbindung.</small>
        </div>
      </section>

      <!-- Modell -->
      <section class="card">
        <h2 class="card__title">Sprachmodell</h2>
        <p class="card__sub">Das Modell liest deine Dokumente, spielt die Agenten und schreibt den Bericht.</p>
        <label class="field">
          <span class="field__label">Anbieter</span>
          <select v-model="cfg.llm_provider" class="field__input">
            <option value="ollama">Ollama (auf diesem Rechner)</option>
            <option value="lmstudio">LM Studio (auf diesem Rechner)</option>
            <option value="local">Anderer OpenAI-kompatibler Server</option>
            <option value="openai">OpenAI</option>
          </select>
        </label>
        <template v-if="cfg.llm_provider === 'openai'">
          <label class="field"><span class="field__label">API-Schlüssel</span><input type="password" v-model="cfg.llm_api_key" class="field__input" placeholder="sk-…" autocomplete="off"></label>
          <label class="field"><span class="field__label">Adresse</span><input type="url" v-model="cfg.llm_base_url" class="field__input" placeholder="https://api.openai.com/v1"></label>
          <label class="field"><span class="field__label">Modell</span><input type="text" v-model="cfg.llm_model_name" class="field__input" placeholder="gpt-4o-mini"></label>
        </template>
        <template v-else>
          <label class="field"><span class="field__label">Adresse</span><input type="url" v-model="cfg.local_llm_base_url" class="field__input" placeholder="http://127.0.0.1:11434/v1"></label>
          <label class="field"><span class="field__label">Modell</span><input type="text" v-model="cfg.local_llm_model_name" class="field__input" placeholder="z. B. gemma4:12b"><span class="field__hint">Der Name, den `ollama list` anzeigt.</span></label>
          <label class="field"><span class="field__label">Schlüssel (nur falls der Server einen verlangt)</span><input type="password" v-model="cfg.local_llm_api_key" class="field__input" autocomplete="off"></label>
        </template>
      </section>

      <!-- Gedächtnis -->
      <section class="card">
        <h2 class="card__title">Gedächtnis der Agenten</h2>
        <p class="card__sub">Hier merkt sich MiroFish, wer wen kennt und was passiert ist.</p>
        <label class="field">
          <span class="field__label">Speicherort</span>
          <select v-model="cfg.memory_provider" class="field__input">
            <option value="obsidian">Auf diesem Rechner (empfohlen)</option>
            <option value="zep">Zep Cloud</option>
            <option value="hybrid">Beides</option>
          </select>
        </label>
        <label class="field" v-if="cfg.memory_provider !== 'obsidian'">
          <span class="field__label">Zep-API-Schlüssel</span>
          <input type="password" v-model="cfg.zep_api_key" class="field__input" autocomplete="off">
        </label>
        <p v-if="masked" class="notice">Gespeicherte Schlüssel werden maskiert angezeigt. Zum Ändern neu eingeben.</p>
      </section>

      <div class="actions">
        <button type="button" class="btn btn--primary" :disabled="saving" @click="save">{{ saving ? 'Speichert …' : 'Speichern' }}</button>
        <button type="button" class="btn" :disabled="testing" @click="test"><span v-if="testing" class="spin"></span>{{ testing ? 'Prüft …' : 'Verbindung prüfen' }}</button>
      </div>
      <p v-if="result" class="notice" :class="result.ok ? 'notice--ok' : 'notice--err'" role="status">{{ result.text }}</p>

      <!-- Darstellung -->
      <section class="card">
        <h2 class="card__title">Darstellung</h2>
        <button type="button" class="rowbtn" @click="showTheme = true">
          <span class="swatch"></span>
          <span class="rowbtn__text"><strong>Farben</strong><small>Eine von einer Million geprüften Farb-Combos</small></span>
          <span class="rowbtn__chev">›</span>
        </button>
      </section>

      <!-- Über -->
      <section class="card card--about">
        <img src="/logo-mark.svg" alt="" width="36" height="36" />
        <div>
          <strong>MiroFish</strong>
          <small>Schwarm-Simulation zur Vorhersage öffentlicher Reaktionen. Open Source (AGPL-3.0).</small>
          <a href="https://github.com/BEKO2210/MiroFish-DE" target="_blank" rel="noopener">Quellcode und Anleitung</a>
        </div>
      </section>
    </main>
    <ThemePicker :open="showTheme" @close="showTheme = false" />
    <MobileNav />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import AppHeader from '../components/AppHeader.vue'
import MobileNav from '../components/MobileNav.vue'
import ThemePicker from '../components/ThemePicker.vue'
import service from '../api/index'

const status = ref({ ready: false, llm_model: '', memory_provider: '' })
const cfg = ref({ llm_provider: 'ollama', llm_api_key: '', llm_base_url: '', llm_model_name: '', local_llm_base_url: '', local_llm_model_name: '', local_llm_api_key: '', zep_api_key: '', memory_provider: 'obsidian' })
const saving = ref(false), testing = ref(false), result = ref(null), showTheme = ref(false)
const memoryLabel = computed(() => ({ obsidian: 'auf diesem Rechner', zep: 'Zep Cloud', hybrid: 'beides' }[status.value.memory_provider] || status.value.memory_provider))
const masked = computed(() => Object.values(cfg.value).some(v => typeof v === 'string' && v.includes('...****')))

const load = async () => {
  try {
    const res = await service.get('/api/graph/system/status')
    if (res?.success) {
      status.value = { ready: true, llm_model: res.data.llm_model, memory_provider: res.data.memory_provider }
      if (res.data.config) cfg.value = { ...cfg.value, ...res.data.config }
    }
  } catch (e) { status.value.ready = false }
}
const save = async () => {
  saving.value = true; result.value = null
  try {
    const res = await service.post('/api/graph/system/config', cfg.value)
    if (res?.success) { result.value = { ok: true, text: 'Gespeichert.' }; await load() }
  } catch (e) { result.value = { ok: false, text: 'Speichern fehlgeschlagen: ' + (e.response?.data?.error || e.message) } }
  finally { saving.value = false }
}
const test = async () => {
  testing.value = true; result.value = null
  try {
    const res = await service.post('/api/graph/system/test-llm')
    if (res?.success) result.value = { ok: true, text: `Verbindung steht. Das Modell ${res.data.model} antwortet.` }
  } catch (e) { result.value = { ok: false, text: 'Keine Antwort vom Modell: ' + (e.response?.data?.error || e.message) } }
  finally { testing.value = false }
}
onMounted(load)
</script>

<style scoped>
.page { min-height: 100vh; background: var(--color-bg-canvas); color: var(--color-text-primary); }
.main { max-width: 680px; margin: 0 auto; padding: 20px 16px 96px; }
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
.card--about { display: flex; gap: 14px; align-items: flex-start; }
.card--about div { display: flex; flex-direction: column; gap: 4px; }
.card--about small { color: var(--color-text-muted); font-size: 13px; line-height: 1.45; }
.card--about a { color: var(--color-brand-primary); font-size: 14px; }
@media (min-width: 769px) { .main { padding: 32px 24px 64px; } }
</style>
