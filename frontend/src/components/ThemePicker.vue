<template>
  <Teleport to="body">
    <Transition name="sheet">
      <div v-if="open" class="sheet-backdrop" @click.self="$emit('close')">
        <section class="sheet" role="dialog" aria-modal="true" aria-labelledby="theme-title">
          <header class="sheet__head">
            <div>
              <h2 id="theme-title" class="sheet__title">{{ t('theme.title') }}</h2>
              <p class="sheet__sub">{{ t('theme.sub') }} <a :href="COMBO_SITE" target="_blank" rel="noopener">Combo Studio</a>, {{ t('theme.subTail') }}</p>
            </div>
            <button type="button" class="sheet__close" :aria-label="t('theme.close')" @click="$emit('close')">×</button>
          </header>

          <!-- Aktuelle Wahl -->
          <div class="current">
            <span class="swatch swatch--lg" :style="swatchStyle(current)"></span>
            <div class="current__text">
              <strong>{{ current.id ? t('theme.combo', { id: current.id }) : t('theme.default') }}</strong>
              <small>{{ current.aName }} · {{ current.bName }}</small>
            </div>
            <a v-if="current.id" :href="`${COMBO_SITE}/#${current.id}`" target="_blank" rel="noopener" class="linkbtn">{{ t('theme.card') }}</a>
          </div>
          <button v-if="!isDefault" type="button" class="resetbtn" @click="reset">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v5h5"/></svg>
            {{ t('theme.resetFull') }}
          </button>

          <!-- Modus -->
          <div class="seg" role="radiogroup" :aria-label="t('theme.modeAria')">
            <button type="button" :class="{ on: current.mode !== 'full' }" @click="setMode('soft')">{{ t('theme.soft') }}</button>
            <button type="button" :class="{ on: current.mode === 'full' }" @click="setMode('full')">{{ t('theme.full') }}</button>
          </div>

          <!-- Vorgaben -->
          <div class="grid">
            <button type="button" class="tile" :class="{ on: !current.id && current.b === DEFAULT_THEME.b }" @click="choose(DEFAULT_THEME)" :title="t('theme.default')">
              <span class="swatch" :style="swatchStyle(DEFAULT_THEME)"></span>
            </button>
            <button v-for="p in PRESETS" :key="p.id" type="button" class="tile" :class="{ on: current.id === p.id }" @click="choose(p)" :title="`#${p.id} ${p.aName} / ${p.bName}`">
              <span class="swatch" :style="swatchStyle(p)"></span>
            </button>
            <button type="button" class="tile tile--random" :disabled="busy" @click="random" :title="t('theme.random')" :aria-label="t('theme.random')">
              <span v-if="!busy">?</span><span v-else class="spin"></span>
            </button>
          </div>

          <!-- Eingabe -->
          <form class="row" @submit.prevent="submit">
            <input v-model="input" class="input" type="text" inputmode="numeric" :placeholder="t('theme.inputPh')" :aria-label="t('theme.inputAria')" />
            <button type="submit" class="btn" :disabled="busy || !input.trim()">{{ t('theme.load') }}</button>
          </form>
          <div class="row row--own">
            <label class="own">
              <input type="color" v-model="ownColor" @change="chooseOwn" />
              <span>{{ t('theme.own') }}</span>
            </label>
          </div>
          <p v-if="error" class="error" role="alert">{{ error }}</p>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { PRESETS, DEFAULT_THEME, COMBO_SITE, loadTheme, saveTheme, resetTheme, fetchCombo, randomComboId, parseComboInput } from '../theme'

defineProps({ open: Boolean })
defineEmits(['close'])
const { t } = useI18n()

const current = ref(loadTheme())
const input = ref('')
const ownColor = ref(current.value.b)
const busy = ref(false)
const isDefault = computed(() => !current.value.id && current.value.b === DEFAULT_THEME.b && current.value.a === DEFAULT_THEME.a && current.value.mode !== 'full')
const error = ref('')

const swatchStyle = (t) => ({ background: `linear-gradient(135deg, ${t.a} 50%, ${t.b} 50%)` })
const choose = (t) => {
  current.value = { ...t, mode: t.mode || current.value.mode || 'soft' }
  saveTheme(current.value)
  error.value = ''
}
const setMode = (m) => choose({ ...current.value, mode: m })
const reset = () => { current.value = { ...DEFAULT_THEME }; resetTheme() }
const chooseOwn = () => choose({ id: null, a: '#FFFFFF', aName: 'Weiß', b: ownColor.value.toUpperCase(), bName: t('theme.own') })

const random = async () => {
  busy.value = true; error.value = ''
  try { choose(await fetchCombo(randomComboId())) } catch (e) { error.value = e.message } finally { busy.value = false }
}
const submit = async () => {
  const p = parseComboInput(input.value)
  if (!p) { error.value = t('theme.badInput'); return }
  if (p.pair) { choose({ id: null, a: p.pair[0], aName: p.pair[0], b: p.pair[1], bName: p.pair[1] }); input.value = ''; return }
  busy.value = true; error.value = ''
  try { choose(await fetchCombo(p.id)); input.value = '' } catch (e) { error.value = e.message } finally { busy.value = false }
}
</script>

<style scoped>
.sheet-backdrop { position: fixed; inset: 0; z-index: 100; background: rgba(0,0,0,.35); display: flex; align-items: flex-end; justify-content: center; }
.sheet { width: 100%; max-width: 520px; max-height: 88vh; overflow-y: auto; background: var(--color-bg-surface-raised); color: var(--color-text-primary); border-radius: 20px 20px 0 0; padding: 18px 16px calc(20px + env(safe-area-inset-bottom)); box-shadow: 0 -8px 40px rgba(0,0,0,.2); }
.sheet__head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.sheet__title { font-family: var(--font-heading); font-size: 20px; margin: 0; }
.sheet__sub { margin: 4px 0 0; font-size: 13px; color: var(--color-text-muted); }
.sheet__sub a { color: var(--color-brand-primary); }
.sheet__close { width: 40px; height: 40px; border: 0; border-radius: 50%; background: var(--color-bg-surface-subtle); color: var(--color-text-secondary); font-size: 22px; cursor: pointer; flex: none; }

.current { display: flex; align-items: center; gap: 12px; margin-top: 16px; padding: 10px 12px; border: 1px solid var(--color-border-subtle); border-radius: 12px; }
.current__text { display: flex; flex-direction: column; flex: 1; min-width: 0; }
.current__text small { color: var(--color-text-muted); font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.swatch { display: inline-block; width: 40px; height: 40px; border-radius: 50%; border: 2px solid var(--color-border-subtle); flex: none; }
.swatch--lg { width: 44px; height: 44px; }

.resetbtn { width: 100%; margin-top: 10px; min-height: 44px; display: inline-flex; align-items: center; justify-content: center; gap: 8px; border: 1px solid var(--color-border-default); border-radius: 12px; background: var(--color-bg-surface); color: var(--color-text-primary); font: inherit; font-weight: 600; font-size: 14px; cursor: pointer; }
.resetbtn svg { width: 18px; height: 18px; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.resetbtn:active { transform: scale(.98); }
.seg { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; margin-top: 14px; padding: 4px; background: var(--color-bg-surface-subtle); border-radius: 12px; }
.seg button { min-height: 40px; border: 0; border-radius: 9px; background: transparent; font: inherit; font-weight: 600; color: var(--color-text-secondary); cursor: pointer; }
.seg button.on { background: var(--color-bg-surface-raised); color: var(--color-text-primary); box-shadow: 0 1px 3px rgba(0,0,0,.12); }

.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(52px, 1fr)); gap: 10px; margin-top: 16px; }
.tile { aspect-ratio: 1; min-height: 52px; border-radius: 14px; border: 2px solid transparent; background: var(--color-bg-surface-subtle); display: flex; align-items: center; justify-content: center; cursor: pointer; padding: 0; transition: transform .1s; }
.tile:active { transform: scale(.94); }
.tile.on { border-color: var(--color-brand-primary); }
.tile--random { font-family: var(--font-heading); font-size: 22px; font-weight: 700; color: var(--color-brand-primary); border: 2px dashed var(--color-border-default); }
.spin { width: 18px; height: 18px; border: 2px solid var(--color-border-default); border-top-color: var(--color-brand-primary); border-radius: 50%; animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.row { display: flex; gap: 8px; margin-top: 14px; align-items: center; }
.row--own { justify-content: space-between; }
.input { flex: 1; min-width: 0; min-height: 44px; font: inherit; font-size: 16px; padding: 0 12px; border: 1px solid var(--color-border-default); border-radius: 12px; background: var(--color-bg-surface-raised); color: inherit; }
.input:focus { outline: none; border-color: var(--color-brand-primary); box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-brand-primary) 15%, transparent); }
.btn { min-height: 44px; padding: 0 16px; border: 0; border-radius: 12px; background: var(--color-brand-primary); color: var(--color-brand-on-primary); font: inherit; font-weight: 600; cursor: pointer; }
.btn:disabled { opacity: .5; cursor: not-allowed; }
.own { display: inline-flex; align-items: center; gap: 10px; font-size: 14px; cursor: pointer; }
.own input { width: 36px; height: 36px; border: 1px solid var(--color-border-default); border-radius: 50%; padding: 0; background: none; cursor: pointer; }
.linkbtn { background: none; border: 0; color: var(--color-brand-primary); font: inherit; font-size: 14px; cursor: pointer; padding: 8px 0; text-decoration: underline; }
.error { margin: 10px 0 0; color: var(--color-error-text); font-size: 13px; }

.sheet-enter-active, .sheet-leave-active { transition: opacity .2s; }
.sheet-enter-active .sheet, .sheet-leave-active .sheet { transition: transform .25s cubic-bezier(.16,1,.3,1); }
.sheet-enter-from, .sheet-leave-to { opacity: 0; }
.sheet-enter-from .sheet, .sheet-leave-to .sheet { transform: translateY(40px); }

@media (min-width: 769px) {
  .sheet-backdrop { align-items: center; }
  .sheet { border-radius: 20px; padding: 24px; }
}
</style>
