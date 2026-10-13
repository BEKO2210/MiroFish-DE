# UX-AUDIT-2: MiroFish Swarm Intelligence Engine
## Priorisierte UX/UI-Spezifikation für Mobile (Samsung S23 Ultra, 412 px) und Desktop (1440 px)

---

### 1. Kurzurteil

MiroFish verfügt über eine leistungsfähige algorithmische Grundlage, scheitert in der aktuellen Fassung jedoch an elementaren ergonomischen Standards der mobilen Nutzung und lässt auf dem Desktop erhebliche Flächenpotenziale ungenutzt. Auf dem Smartphone (Samsung S23 Ultra, 412 px Viewport) überdeckt das fixierte Fußmenü systematisch primäre Interaktionselemente auf sämtlichen Unterseiten, während der Wissensgraph durch fehlerhafte Initialisierung leer bleibt oder durch kollidierende Schalterleisten unbedienbar wird. Die Desktop-Ansicht (1440 px) bildet die Arbeitsabläufe bisher als monotone, zentrierte Einspalten-Schläuche ab, anstatt die parallele Sichtung von Wissensgraph, Simulationsverlauf und Berichtsanalyse in einem professionellen Mehrspalten-Arbeitsraum zu ermöglichen. Typografische Brüche mit Schriftgrößen unter 11 px, unzureichende Kontrastwerte von 4,48:1 auf getönten Flächen sowie fehlende Barrierefreiheitsattribute bei Formularelementen untergraben das Vertrauen fachfremder Nutzer aus Kommunen, Presse und Marketing. Durch ein striktes 4/8-px-Abstandsraster, eine daumengerechte Aktionsleiste über dem Fußmenü, ein responsives Zwei-Spalten-Layout am Desktop und eine robuste D3-Graph-Überholung erreicht die Plattform das angestrebte Apple-Human-Interface-Niveau.

---

### 2. Befundtabelle

| Befund | Seite / Screenshot | Datei | Priorität | Lösung in einem Satz |
| :--- | :--- | :--- | :---: | :--- |
| **Fußmenü verdeckt Primäraktionen** | Startseite (`01-start-mobil.png`), Durchlauf (`04-durchlauf-mobil.png`), Prozess, Simulation, Interaktion | `frontend/src/App.vue`, `frontend/src/views/Home.vue`, `frontend/src/views/RunView.vue` | **P1** | Globalen Safe-Area-Abstand auf mobilen Inhaltscontainern etablieren und primäre Aktionen in eine standardisierte, fixierte Daumenzonen-Leiste oberhalb der `MobileNav` auslagern. |
| **Wissensgraph mobil leer (0×0 px)** | Wissensgraph Schritt 1 (`10-graphansicht-mobil.png`) | `frontend/src/views/MainView.vue`, `frontend/src/components/GraphPanel.vue` | **P1** | SVG-Initialisierung per `ResizeObserver` an die tatsächliche Sichtbarkeit binden und beim Umschalten zwischen Arbeitsbereich und Graph automatisch neu berechnen. |
| **Kollidierende Kopfleiste & Werkzeuge im Graph** | Wissensgraph mobil (`11-graph-ueberlappung-handy-belkis.jpg`) | `frontend/src/components/GraphPanel.vue` | **P1** | Kopfzeile mobil zweizeilig aufbauen: Titel „Wissensgraph“ in Zeile 1, darunter eine wrap-fähige Werkzeugleiste mit mind. 44 px Touch-Zielen ohne absolute Überlagerung. |
| **Unlesbarer Status-Hinweis im Graph** | Wissensgraph mobil (`11-graph-ueberlappung-handy-belkis.jpg`) | `frontend/src/components/GraphPanel.vue` | **P1** | Hinweis „Gedächtnis der Agenten wird aktualisiert“ mit `--color-bg-surface-raised` und `--color-text-primary` (Kontrast ≥ 4.5:1) kompakt an den oberen Rand verlagern. |
| **Formular-Selects & Dateiupload ohne Barrierefreiheit** | Startseite (`Home.vue`), Einstellungen (`03-einstellungen-mobil.png`) | `frontend/src/views/Home.vue`, `frontend/src/views/SettingsView.vue` | **P1** | Datei-Input mit echtem Label verknüpfen sowie allen Select-Feldern in den Einstellungen explizite `id`-, `for`- und `aria-label`-Attribute zuweisen. |
| **Knotennamen im Graph winzig und abgeschnitten** | Wissensgraph mobil (`11-graph-ueberlappung-handy-belkis.jpg`) | `frontend/src/components/GraphPanel.vue` | **P2** | Schriftgröße auf mind. 11 px anheben, Kürzung aufheben/erweitern, Pinch-Zoom/Pan aktivieren und Antippen mit einem Apple-inspirierten Detail-Sheet koppeln. |
| **Rote Riesenlegende blockiert Zeichenfläche** | Wissensgraph mobil (`11-graph-ueberlappung-handy-belkis.jpg`) | `frontend/src/components/GraphPanel.vue` | **P2** | Legende am Handy standardmäßig einklappen, mit neutraler Token-Farbe gestalten, in „Arten von Akteuren“ umbenennen und per Button öffnen. |
| **Startseite Desktop verschwendet Bildschirmbreite** | Startseite Desktop (`01-start-desktop.png`) | `frontend/src/views/Home.vue` | **P2** | Desktop-Layout ab 1024 px zweispaltig anordnen: Hero und Erklärung links, Eingabeformular mit Live-Status und Verlauf rechts. |
| **Verlauf Desktop als Endlosschlauch** | Verlauf Desktop (`02-verlauf-desktop.png`) | `frontend/src/views/HistoryView.vue` | **P2** | Einträge ab 1024 px als ergonomisches Zwei- bzw. Dreispalten-Kartenraster mit klarer Aktionsleiste und Metadaten-Hierarchie umsetzen. |
| **Einstellungen Desktop einspaltig gestreckt** | Einstellungen Desktop (`03-einstellungen-desktop.png`) | `frontend/src/views/SettingsView.vue` | **P2** | Formular zweispaltig strukturieren (Spalte 1: Sprachmodell & Gedächtnis; Spalte 2: Farbsystem, Sprache & Systeminformationen). |
| **Schritt-Navigation mobil überladen** | Alle Schritt-Seiten (`MainView.vue`, `SimulationView.vue` etc.) | `frontend/src/views/MainView.vue`, `frontend/src/components/StepProgressHeader.vue` | **P2** | Obere Leiste am Handy bereinigen: Sprachumschalter ausblenden, Schrittanzeige auf kompakte 5-Punkte-Progression reduzieren. |
| **Kontrastmangel Meta-Text auf Terracotta-Flächen** | Durchlauf (`04-durchlauf-mobil.png`), Startseite (`Home.vue`) | `frontend/src/assets/tokens.css`, `frontend/src/views/RunView.vue` | **P2** | Token `--color-brand-subtle` mit abgedunkeltem Sekundärtext koppeln, sodass der Kontrastwert von bisher 4,48:1 auf über 5.2:1 steigt. |
| **Punktraster im Graphhintergrund zu dominant** | Wissensgraph (`11-graph-ueberlappung-handy-belkis.jpg`) | `frontend/src/components/GraphPanel.vue` | **P3** | Hintergrund-Punkte auf 1 px verkleinern und Deckkraft über `--color-border-subtle` auf max. 20 % drosseln. |
| **Fließtext-Animationen ohne Bewegungsschutz** | Gesamte Anwendung | `frontend/src/assets/tokens.css`, `frontend/src/views/RunView.vue` | **P3** | Pulsierende Animationen und Spinner bei `prefers-reduced-motion: reduce` vollständig stilllegen und Mikro-Interaktionen nur bei Aktionen triggern. |

---

### 3. Detaillierte Spezifikation nach Seiten und Komponenten

#### 3.1 Wiederverwendbare Basiskomponenten

##### Komponente A: `MobileStickyBar.vue` (Feste Daumenzonen-Aktionsleiste)
* **Zweck**: Bietet auf allen Seiten die wichtigste Primäraktion im optimal erreichbaren unteren Daumenbereich des Samsung S23 Ultra, exakt über der `MobileNav`, ohne Inhalt zu verdecken.
* **Dateipfad**: `frontend/src/components/MobileStickyBar.vue`
* **Props**:
  * `primaryLabel` (String, Pflicht): Text der Hauptaktion.
  * `primaryDisabled` (Boolean, Standard `false`): Deaktivierungszustand.
  * `primaryLoading` (Boolean, Standard `false`): Ladezustand mit dezentem Spinner.
  * `secondaryLabel` (String, optional): Text einer alternativen Sekundäraktion (z. B. „Zurück“).
  * `secondaryDisabled` (Boolean, Standard `false`).
* **Events**: `@primary-click`, `@secondary-click`

```vue
<!-- frontend/src/components/MobileStickyBar.vue -->
<template>
  <aside class="mobile-sticky-bar" role="region" :aria-label="ariaLabel || primaryLabel">
    <div class="mobile-sticky-bar__container">
      <button
        v-if="secondaryLabel"
        type="button"
        class="sticky-btn sticky-btn--secondary"
        :disabled="secondaryDisabled || primaryLoading"
        @click="$emit('secondary-click')"
      >
        <span>{{ secondaryLabel }}</span>
      </button>

      <button
        type="button"
        class="sticky-btn sticky-btn--primary"
        :class="{ 'is-loading': primaryLoading }"
        :disabled="primaryDisabled || primaryLoading"
        @click="$emit('primary-click')"
      >
        <span v-if="primaryLoading" class="sticky-btn__spinner" aria-hidden="true"></span>
        <span class="sticky-btn__label">{{ primaryLabel }}</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
defineProps({
  primaryLabel: { type: String, required: true },
  primaryDisabled: { type: Boolean, default: false },
  primaryLoading: { type: Boolean, default: false },
  secondaryLabel: { type: String, default: '' },
  secondaryDisabled: { type: Boolean, default: false },
  ariaLabel: { type: String, default: '' }
})
defineEmits(['primary-click', 'secondary-click'])
</script>

<style scoped>
.mobile-sticky-bar {
  display: none;
}

@media (max-width: 768px) {
  .mobile-sticky-bar {
    display: block;
    position: fixed;
    left: 0;
    right: 0;
    bottom: calc(58px + env(safe-area-inset-bottom, 0px));
    z-index: 45;
    background: color-mix(in srgb, var(--color-bg-canvas) 92%, transparent);
    backdrop-filter: saturate(180%) blur(16px);
    -webkit-backdrop-filter: saturate(180%) blur(16px);
    border-top: 1px solid var(--color-border-subtle);
    padding: 8px 16px;
    box-shadow: 0 -4px 16px rgba(15, 23, 42, 0.06);
  }

  .mobile-sticky-bar__container {
    display: flex;
    align-items: center;
    gap: 10px;
    max-width: 600px;
    margin: 0 auto;
  }

  .sticky-btn {
    flex: 1;
    min-height: 48px;
    border-radius: var(--radius-lg, 12px);
    font-family: var(--font-body);
    font-size: 15px;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 0 16px;
    border: 1px solid transparent;
    cursor: pointer;
    touch-action: manipulation;
    transition: transform var(--transition-fast), opacity var(--transition-fast), background-color var(--transition-fast);
  }

  .sticky-btn:active:not(:disabled) {
    transform: scale(0.98);
  }

  .sticky-btn--primary {
    background: var(--color-brand-primary);
    color: var(--color-brand-on-primary);
    box-shadow: 0 2px 8px color-mix(in srgb, var(--color-brand-primary) 30%, transparent);
  }

  .sticky-btn--primary:disabled {
    background: var(--color-bg-surface-subtle);
    color: var(--color-text-muted);
    border-color: var(--color-border-subtle);
    box-shadow: none;
    cursor: not-allowed;
  }

  .sticky-btn--secondary {
    flex: 0 0 auto;
    min-width: 110px;
    background: var(--color-bg-surface-raised);
    color: var(--color-text-secondary);
    border-color: var(--color-border-default);
  }

  .sticky-btn__spinner {
    width: 16px;
    height: 16px;
    border: 2px solid color-mix(in srgb, currentColor 30%, transparent);
    border-top-color: currentColor;
    border-radius: 50%;
    animation: spin-sticky 0.8s linear infinite;
  }
}

@keyframes spin-sticky {
  to { transform: rotate(360deg); }
}

@media (prefers-reduced-motion: reduce) {
  .sticky-btn {
    transition: none !important;
  }
  .sticky-btn__spinner {
    animation-duration: 2s !important;
  }
}
</style>
```

---

##### Komponente B: `StepHeaderCompact.vue` (Ergonomische Schritt-Navigation 1–5)
* **Zweck**: Ersetzt die überfrachteten Header auf allen Schritt-Seiten am Smartphone durch eine daumengerechte Anzeige mit direkt antippbarem Schrittfortschritt.
* **Dateipfad**: `frontend/src/components/StepHeaderCompact.vue`

```vue
<!-- frontend/src/components/StepHeaderCompact.vue -->
<template>
  <div class="step-nav-bar">
    <div class="step-nav-bar__meta">
      <span class="step-nav-bar__badge">{{ $t('main.schritt') }} {{ currentStep }}/5</span>
      <h2 class="step-nav-bar__title">{{ stepNames[currentStep - 1] }}</h2>
    </div>
    <div class="step-nav-bar__dots" role="tablist" :aria-label="$t('main.schrittFortschritt')">
      <button
        v-for="step in 5"
        :key="step"
        type="button"
        class="step-dot"
        :class="{
          'is-active': step === currentStep,
          'is-passed': step < currentStep,
          'is-locked': step > maxUnlockedStep
        }"
        :aria-selected="step === currentStep"
        :disabled="step > maxUnlockedStep"
        @click="$emit('select-step', step)"
        :title="`${stepNames[step - 1]}`"
      >
        <span class="step-dot__circle"></span>
        <span class="sr-only">{{ stepNames[step - 1] }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  currentStep: { type: Number, required: true },
  maxUnlockedStep: { type: Number, default: 5 },
  stepNames: { type: Array, required: true }
})
defineEmits(['select-step'])
</script>

<style scoped>
.step-nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 4px 0;
}
.step-nav-bar__meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.step-nav-bar__badge {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--color-brand-primary);
  letter-spacing: 0.04em;
}
.step-nav-bar__title {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.step-nav-bar__dots {
  display: flex;
  align-items: center;
  gap: 6px;
}
.step-dot {
  min-width: 32px;
  min-height: 36px;
  padding: 0;
  background: transparent;
  border: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.step-dot:disabled {
  cursor: not-allowed;
  opacity: 0.35;
}
.step-dot__circle {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--color-border-strong);
  transition: all var(--transition-fast);
}
.step-dot.is-active .step-dot__circle {
  width: 22px;
  background: var(--color-brand-primary);
}
.step-dot.is-passed .step-dot__circle {
  background: var(--color-success-text);
}
</style>
```

---

#### 3.2 Komponente: `GraphPanel.vue` (Wissensgraph)

##### 1. Problemstellung & IST-Zustand (Screenshots 10 & 11)
* **Überlappung**: Der Toggle „Kantenbezeichnungen anzeigen“ ist absolut bei `top: 60px; right: 20px;` platziert. Da `.panel-header` am Handy (412 px) flexibel umbricht, liegt der Schalter direkt über dem Vollbild- und Aktualisieren-Button.
* **Leerer Zustand (Screenshot 10)**: Da der Tab „Graph“ beim Öffnen von `MainView.vue` mobil anfangs inaktiv ist (`width: 0%` via `workbench`), berechnet D3 `clientWidth = 0` und `clientHeight = 0`. Ein Wechsel auf den Tab löst keinen Resize-Event aus, wodurch das SVG dauerhaft leer bleibt.
* **Status-Badge unlesbar**: `.graph-building-hint` verwendet Textfarbe `var(--color-text-inverse)` (#FFFFFF) auf einer transparenten Fläche `color-mix(in srgb, var(--color-text-primary) 12%, transparent)`. Das resultiert in einem Kontrast von 1,2:1 und blockiert mittig den Blick auf Knoten.
* **Knotennamen**: Knotenbezeichnungen werden bei 8 Zeichen brutal mit `…` abgeschnitten (`Bürgerme…`).
* **Legende**: Eine statische Box mit roter Überschrift beansprucht über 40 % der vertikalen Höhe am Smartphone.
* **Hintergrund**: Das SVG-Punktraster ist zu dunkel und erzeugt visuelles Rauschen.

##### 2. Template-Überarbeitung
In `frontend/src/components/GraphPanel.vue`:

```html
<!-- Neues Header-Layout: Semantisch, responsiv und überlappungsfrei -->
<div class="panel-header">
  <div class="panel-header__row-top">
    <h2 class="panel-title">{{ $t('graph.wissensgraph') }}</h2>
    <button
      v-if="graphData && entityTypes.length"
      type="button"
      class="legend-toggle-btn"
      :class="{ 'is-active': showLegendMobile }"
      @click="showLegendMobile = !showLegendMobile"
      aria-haspopup="dialog"
      :aria-expanded="showLegendMobile"
    >
      <span class="legend-toggle-btn__dot" aria-hidden="true"></span>
      <span>{{ $t('graph.artenVonAkteuren') }}</span>
    </button>
  </div>

  <div class="panel-header__row-toolbar">
    <div class="header-tools">
      <button
        type="button"
        class="tool-btn"
        @click="$emit('refresh')"
        :disabled="loading"
        :aria-label="$t('graph.graphAktualisieren')"
      >
        <span class="icon-refresh" :class="{ 'spinning': loading }" aria-hidden="true">↻</span>
        <span class="btn-text">{{ $t('common.refresh') }}</span>
      </button>

      <button
        type="button"
        class="tool-btn"
        @click="$emit('toggle-maximize')"
        :aria-label="$t('graph.maximierenWiederherstellen')"
      >
        <span class="icon-maximize" aria-hidden="true">⛶</span>
        <span class="btn-text desktop-only">{{ $t('graph.fullscreen') }}</span>
      </button>
    </div>

    <!-- Kanten-Schalter sauber in die Werkzeugleiste integriert -->
    <div v-if="graphData" class="edge-labels-control">
      <label class="toggle-switch-compact" for="edge-label-toggle">
        <input id="edge-label-toggle" type="checkbox" v-model="showEdgeLabels" />
        <span class="slider" aria-hidden="true"></span>
        <span class="toggle-label">{{ $t('graph.kanten') }}</span>
      </label>
    </div>
  </div>
</div>

<!-- Dezentralisierter, hochkontrastiger Status-Banner am oberen Rand -->
<div
  v-if="currentPhase === 1 || isSimulating"
  class="graph-building-hint graph-building-hint--top"
  role="status"
  aria-live="polite"
>
  <span class="memory-pulse" aria-hidden="true"></span>
  <span class="hint-message">
    {{ isSimulating ? $t('graph.gedaechtnisWirdAktualisiert') : $t('graph.graphWirdAufgebaut') }}
  </span>
</div>

<!-- Einklappbares Legenden-Sheet mobil / Box desktop -->
<div
  v-if="graphData && entityTypes.length"
  class="graph-legend"
  :class="{ 'is-open-mobile': showLegendMobile }"
  role="region"
  :aria-label="$t('graph.artenVonAkteuren')"
>
  <div class="legend-header">
    <span class="legend-title">{{ $t('graph.artenVonAkteuren') }}</span>
    <button type="button" class="legend-close-btn mobile-only" @click="showLegendMobile = false" aria-label="Schließen">×</button>
  </div>
  <div class="legend-items">
    <div class="legend-item" v-for="type in entityTypes" :key="type.name">
      <span class="legend-dot" :style="{ background: type.color }"></span>
      <span class="legend-label">{{ type.name }}</span>
    </div>
  </div>
</div>
```

##### 3. Script-Anpassungen (D3 Fit-to-View, Touch, Truncation & ResizeObserver)
In `frontend/src/components/GraphPanel.vue`:

```javascript
// Zusätzliche reaktive Variablen
const showLegendMobile = ref(false)
let resizeObserver = null

// Auto-Fit Funktion für alle Bildschirmgrößen
const zoomToFit = (paddingPercent = 0.9) => {
  if (!graphSvg.value || !graphContainer.value) return
  const svg = d3.select(graphSvg.value)
  const g = svg.select('g')
  if (g.empty()) return

  const bounds = g.node().getBBox()
  const parent = graphContainer.value
  const fullWidth = parent.clientWidth
  const fullHeight = parent.clientHeight

  if (bounds.width === 0 || bounds.height === 0 || fullWidth === 0 || fullHeight === 0) return

  const midX = bounds.x + bounds.width / 2
  const midY = bounds.y + bounds.height / 2

  const scale = Math.max(0.2, Math.min(1.8, paddingPercent / Math.max(bounds.width / fullWidth, bounds.height / fullHeight)))
  const translate = [fullWidth / 2 - scale * midX, fullHeight / 2 - scale * midY]

  svg.transition()
    .duration(400)
    .call(
      d3.zoom().transform,
      d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale)
    )
}

// Robuste D3-Touch & Zoom Konfiguration
const initD3Zoom = (svg, g, width, height) => {
  const zoomBehavior = d3.zoom()
    .scaleExtent([0.15, 3.5])
    .filter((event) => {
      // Pinch-Zoom und Multi-Touch zulassen
      if (event.touches && event.touches.length > 1) return true
      // Standard-Mausrad oder Ein-Finger-Pan auf dem Hintergrund zulassen
      return !event.ctrlKey && !event.button
    })
    .on('zoom', (event) => {
      g.attr('transform', event.transform)
    })

  svg.call(zoomBehavior)
  // Bei Touchstart Standard-Scroll des Browsers auf dem SVG verhindern
  svg.style('touch-action', 'none')
}

// Optimiertes Labeling: Bis zu 16 Zeichen auf Mobilgeräten anzeigen
const formatNodeLabel = (name) => {
  if (!name) return ''
  const limit = window.innerWidth <= 768 ? 14 : 20
  return name.length > limit ? name.substring(0, limit) + '…' : name
}

// Behebung des leeren Graphen mobil via ResizeObserver
onMounted(() => {
  if (graphContainer.value) {
    resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        if (entry.contentRect.width > 0 && entry.contentRect.height > 0) {
          renderGraph()
          setTimeout(() => zoomToFit(0.88), 300)
        }
      }
    })
    resizeObserver.observe(graphContainer.value)
  }
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
})
```

##### 4. Fertige CSS-Regeln für `GraphPanel.vue`
```css
/* Subtiles Punktraster über Tokens */
.graph-panel {
  position: relative;
  width: 100%;
  height: 100%;
  background-color: var(--color-bg-canvas);
  background-image: radial-gradient(var(--color-border-strong) 1px, transparent 1px);
  background-size: 28px 28px;
  overflow: hidden;
}

/* Kopfbereich: Keine absoluten Einzelbuttons mehr */
.panel-header {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 15;
  padding: 12px 16px;
  background: color-mix(in srgb, var(--color-bg-canvas) 85%, transparent);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--color-border-subtle);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.panel-header__row-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.panel-title {
  font-family: var(--font-heading);
  font-size: 15px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0;
}

.panel-header__row-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}

.header-tools {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tool-btn {
  min-height: 44px;
  min-width: 44px;
  padding: 0 12px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-default);
  background: var(--color-bg-surface-raised);
  color: var(--color-text-secondary);
  font-size: 13px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  box-shadow: var(--shadow-sm);
  touch-action: manipulation;
}

.tool-btn:hover {
  background: var(--color-bg-surface);
  border-color: var(--color-border-strong);
  color: var(--color-text-primary);
}

/* Kompakter Kanten-Schalter */
.edge-labels-control {
  display: flex;
  align-items: center;
}

.toggle-switch-compact {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 44px;
  cursor: pointer;
  user-select: none;
}

.toggle-switch-compact input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-switch-compact .slider {
  width: 38px;
  height: 22px;
  border-radius: 999px;
  background: var(--color-border-strong);
  position: relative;
  transition: background-color var(--transition-fast);
}

.toggle-switch-compact .slider::before {
  content: "";
  position: absolute;
  top: 3px;
  left: 3px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #FFFFFF;
  transition: transform var(--transition-fast);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.toggle-switch-compact input:checked + .slider {
  background: var(--color-brand-primary);
}

.toggle-switch-compact input:checked + .slider::before {
  transform: translateX(16px);
}

.toggle-switch-compact .toggle-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
}

/* Status-Hinweis: Barrierefrei oben platziert */
.graph-building-hint--top {
  position: absolute;
  top: 110px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 12;
  background: var(--color-bg-surface-raised);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border-default);
  box-shadow: var(--shadow-md);
  padding: 6px 14px;
  border-radius: var(--radius-full);
  font-size: 13px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  pointer-events: none;
  max-width: 90%;
  text-align: center;
}

.memory-pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-brand-primary);
  animation: pulse-dot 1.4s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.85); }
}

/* Legende mobil als Sheet, Desktop als feste Box */
.legend-toggle-btn {
  min-height: 36px;
  padding: 0 10px;
  border-radius: var(--radius-full);
  border: 1px solid var(--color-border-default);
  background: var(--color-bg-surface-raised);
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.legend-toggle-btn__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--color-brand-primary);
}

.graph-legend {
  position: absolute;
  bottom: 16px;
  left: 16px;
  z-index: 14;
  background: var(--color-bg-surface-raised);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  padding: 12px 16px;
  box-shadow: var(--shadow-md);
  max-width: 320px;
}

.legend-title {
  display: block;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}

@media (max-width: 768px) {
  .graph-legend {
    display: none;
    left: 8px;
    right: 8px;
    bottom: calc(64px + env(safe-area-inset-bottom));
    max-width: none;
    border-radius: var(--radius-xl);
  }

  .graph-legend.is-open-mobile {
    display: block;
    animation: slide-up 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  }

  .legend-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  .legend-close-btn {
    border: none;
    background: transparent;
    font-size: 20px;
    color: var(--color-text-muted);
    min-width: 36px;
    min-height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

@media (min-width: 1024px) {
  .panel-header {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    padding: 14px 20px;
  }
  .panel-header__row-top {
    flex: 0 0 auto;
  }
  .panel-header__row-toolbar {
    flex: 0 0 auto;
    gap: 16px;
  }
  .legend-toggle-btn {
    display: none;
  }
  .graph-legend {
    display: block !important;
  }
}
```

---

#### 3.3 Startseite (`Home.vue` & `/`)

##### 1. Mobil-Verhalten (Samsung S23 Ultra, 412 px)
* **Problem**: Der CTA „Vorhersage starten“ (`.cta`) befindet sich am Ende des Formulars und wird durch das feste Fußmenü (`MobileNav`) teilweise oder ganz verdeckt (`01-start-mobil.png`). Zudem fehlt dem Dateiupload ein barrierefreies Label.
* **Lösung**: 
  1. Das Dateiupload-Element erhält ein sichtbares oder strikt referenziertes Label (`<label for="doc-upload" class="sr-only">Dokumente hochladen</label>`).
  2. Der Primärbutton wird mobil in die wiederverwendbare `MobileStickyBar` gespiegelt und im Formular mobil ausgeblendet.
  3. Der Inhaltsbereich erhält einen unteren Innenabstand von `padding-bottom: calc(130px + env(safe-area-inset-bottom))`.
  4. Die Hero-Typografie wird auf `clamp(28px, 7vw, 42px)` gedrosselt, um Platz für die Daumenzone zu schaffen.

##### 2. Desktop-Verhalten (≥ 1024 px / 1440 px)
* **Problem**: Eine zentrierte 760-px-Spalte inmitten eines riesigen weißen Freiraums (`01-start-desktop.png`).
* **Lösung**: Zweispaltiges Layout ab 1024 px:
  * **Linke Spalte (50 %)**: Hero-Titel, Schwarm-Leitgedanke, interaktive Schwarm-Canvas und der 4-Schritte-Erklärungsblock („So funktioniert es“).
  * **Rechte Spalte (50 %)**: Prominente Vorhersage-Karte („Neue Vorhersage“) mit Drag-and-Drop, Fragenfeld, Schalter und CTA, gefolgt von den letzten Durchläufen („Zuletzt“).

##### 3. CSS-Änderungen für `frontend/src/views/Home.vue`
```css
/* Responsives Layout-Grid */
.home-layout-grid {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

@media (min-width: 1024px) {
  .home-layout-grid {
    display: grid;
    grid-template-columns: 1.05fr 0.95fr;
    gap: 40px;
    max-width: 1360px;
    margin: 0 auto;
    padding: 32px 32px 64px;
    align-items: start;
  }

  .home-col--left {
    display: flex;
    flex-direction: column;
    gap: 32px;
    position: sticky;
    top: 76px;
  }

  .home-col--right {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  .hero {
    min-height: auto;
    border-bottom: 0;
    padding: 0;
    background: transparent;
  }

  .hero__inner {
    padding: 0;
    max-width: none;
  }

  .main {
    max-width: none;
    padding: 0;
    margin: 0;
  }
}

/* Mobil Daumenzone Absicherung */
@media (max-width: 768px) {
  .main {
    padding-bottom: calc(130px + env(safe-area-inset-bottom));
  }

  .form .cta--inline {
    display: none; /* In der Daumenzone via MobileStickyBar */
  }
}

/* WCAG AA Kontrast-Korrektur auf getönten Flächen */
.live {
  background: var(--color-brand-subtle);
  border: 1px solid var(--color-brand-border);
}

.live__meta {
  color: var(--color-text-secondary) !important; /* Ersetzt #64748B (4.48:1) durch #334155 (> 7:1) */
  font-size: 13px;
  font-weight: 500;
}
```

---

#### 3.4 Verlauf (`HistoryView.vue` & `/history`)

##### 1. Mobil-Verhalten
* **Problem**: Karten sind vertikal dicht gedrängt; Löschen- und Exportieren-Buttons haben auf dem S23 Ultra zu kleine Abstände und stoßen an das Fußmenü.
* **Lösung**: Touch-Ziele auf exakt 48 px Mindesthöhe setzen, Farbkontraste der Aktions-Icons auf `--color-text-primary` schärfen und am Seitenende einen Puffer von `calc(80px + env(safe-area-inset-bottom))` verankern.

##### 2. Desktop-Verhalten (≥ 1024 px)
* **Problem**: Die Liste streckt sich unnötig auf 880 px und wirkt wie ein Mobil-Layout im Vollbild.
* **Lösung**: Transformation in ein 2- bzw. 3-Spalten-Kartenraster (`grid-template-columns: repeat(auto-fill, minmax(380px, 1fr))`). Jede Karte erhält eine klare visuelle Dreiteilung: Status-Header, 2-zeiliger Frage-Ausschnitt, getrennte Aktionsleiste im Kartenfuß.

##### 3. CSS-Änderungen für `frontend/src/views/HistoryView.vue`
```css
@media (max-width: 768px) {
  .main {
    padding-bottom: calc(84px + env(safe-area-inset-bottom));
  }
  
  .act {
    min-height: 48px; /* Touch-Target Apple Standard */
  }
}

@media (min-width: 1024px) {
  .main {
    max-width: 1360px;
    padding: 32px 32px 80px;
  }

  .list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
    gap: 20px;
  }

  .row {
    transition: transform var(--transition-fast), box-shadow var(--transition-fast);
  }

  .row:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
    border-color: var(--color-border-strong);
  }

  .row__main {
    min-height: 140px;
  }
}
```

---

#### 3.5 Einstellungen (`SettingsView.vue` & `/settings`)

##### 1. Barrierefreiheit (e2e-Befund)
* **Problem**: Select-Boxen für Haupt- und Agentenmodell besitzen kein referenziertes `<label>`-Tag (nur ungebundene `<span>`), was Screenreader und automatisierte Tests bemängeln.
* **Lösung**:
  ```html
  <div class="field">
    <div class="field__row">
      <label for="select-main-model" class="field__label">{{ t('settings.mainModel') }}</label>
      <button type="button" class="linkbtn linkbtn--sm" @click="scan">{{ t('settings.rescan') }}</button>
    </div>
    <select id="select-main-model" v-model="cfg.local_llm_model_name" class="field__input">
      <option v-for="m in withCurrent(models, cfg.local_llm_model_name)" :key="m.name" :value="m.name">{{ optionLabel(m) }}</option>
    </select>
  </div>
  ```

##### 2. Mobil- & Desktop-Struktur
* **Mobil**: Die Aktionsbuttons „Speichern“ und „Verbindung prüfen“ werden am Handy per `MobileStickyBar` im Daumenbereich fixiert, sodass kein Scrollen zum Bestätigen nötig ist.
* **Desktop (≥ 1024 px)**: Zwei Spalten mit logischer Gliederung:
  * Spalte 1: Modell-Konfiguration (Provider, Basis-URL, Modellwahl).
  * Spalte 2: Gedächtnis/Speicherort, Farbsystem und Sprachwahl.

##### 3. CSS-Änderungen für `frontend/src/views/SettingsView.vue`
```css
@media (max-width: 768px) {
  .main {
    padding-bottom: calc(130px + env(safe-area-inset-bottom));
  }
  .actions--inline {
    display: none;
  }
}

@media (min-width: 1024px) {
  .main {
    max-width: 1200px;
    padding: 32px 32px 80px;
  }

  .settings-grid {
    display: grid;
    grid-template-columns: 1.1fr 0.9fr;
    gap: 28px;
    align-items: start;
  }
}
```

---

#### 3.6 Durchlauf (`RunView.vue` & `/run/:pipelineId`)

##### 1. Mobil-Verhalten (`04-durchlauf-mobil.png`)
* **Problem**: Der Button „Simulation ansehen“ und der Begleittext werden vollständig vom Fußmenü überlagert.
* **Lösung**:
  1. Sobald `state.simulation_id` oder `state.report_id` verfügbar sind, bindet die Seite die `MobileStickyBar` ein (`primaryLabel = t('run.openSim')` bzw. `t('run.openReport')`).
  2. Der Fließtext „Du kannst diese Seite schließen...“ wird typografisch mit mindestens 13 px über der Leiste gerendert.

##### 2. CSS-Änderungen für `frontend/src/views/RunView.vue`
```css
@media (max-width: 768px) {
  .main {
    padding-bottom: calc(120px + env(safe-area-inset-bottom));
  }
  .actions {
    display: none; /* Aufruf über MobileStickyBar */
  }
}

@media (min-width: 1024px) {
  .main {
    max-width: 860px;
    padding: 40px 32px 80px;
  }

  .timeline {
    margin-top: 32px;
  }
}
```

---

#### 3.7 Schritt-Seiten 1 bis 5 (`MainView.vue`, `SimulationView.vue`, `SimulationRunView.vue`, `ReportView.vue`, `InteractionView.vue`)

##### 1. Gemeinsame Header-Architektur am Smartphone
* **Problem**: Headerzeilen brechen unkontrolliert um, der Desktop-Sprachumschalter verschwendet Platz und die 3-Wege-Umschaltung („Graph / Zweispaltig / Arbeitsbereich“) wirkt überladen.
* **Lösung**:
  * Mobil nur 2 Modi: `Graph` und `Arbeitsbereich` als iOS-inspiriertes Segmented Control mit 44 px Höhe.
  * Sprachumschalter mobil rigoros ausblenden (gehört in Einstellungen).
  * Schrittanzeige per `StepHeaderCompact.vue` einbinden.

##### 2. Desktop-Verhalten (≥ 1024 px)
* **Standard**: Ein sauberes 50/50 Split-Layout:
  * **Linke Bildschirmhälfte**: Wissensgraph (`GraphPanel.vue`) mit freiem Zoom, automatischem Fitting und Akteurslegende.
  * **Rechte Bildschirmhälfte**: Arbeitsbereich des jeweiligen Schritts (Step 1 Ontologie, Step 2 Agenten, Step 3 Live-Feed, Step 4 Bericht, Step 5 Dialog).

##### 3. CSS-Änderungen für die Schritt-Seiten
```css
@media (max-width: 768px) {
  .app-header {
    min-height: auto;
    padding: 8px 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .view-switcher {
    width: 100%;
    display: grid;
    grid-template-columns: 1fr 1fr;
    background: var(--color-bg-surface-subtle);
    border-radius: var(--radius-md);
    padding: 3px;
  }

  .switch-btn {
    min-height: 40px;
    font-size: 13px;
    font-weight: 600;
  }

  /* Split-Modus am Smartphone komplett deaktivieren */
  [data-mode="split"] {
    display: none !important;
  }

  .content-area {
    height: calc(100dvh - 110px - 58px - env(safe-area-inset-bottom));
  }
}

@media (min-width: 1024px) {
  .app-header {
    height: 64px;
    padding: 0 24px;
  }

  .content-area {
    display: flex;
    height: calc(100vh - 64px);
  }

  .panel-wrapper.left {
    width: 50% !important;
    border-right: 1px solid var(--color-border-subtle);
    display: block !important;
  }

  .panel-wrapper.right {
    width: 50% !important;
    display: block !important;
  }
}
```

---

### 4. Liste „Nicht tun“ (Qualitäts-Leitplanken)

Zur Wahrung des angestrebten Apple-Human-Interface-Niveaus und zur Vermeidung von Fehlern im Entwicklungsprozess gelten folgende verbindliche Verbote:

1. **Keine Farbcodes hardcoden**: Niemals HEX-, RGB- oder HSL-Farbwerte direkt in `.vue`-Styles schreiben. Alle Farben müssen über die CSS-Variablen aus `tokens.css` bzw. `theme.js` bezogen werden, da der Nutzer Themes und Farbkombinationen frei wählen kann.
2. **Keine fixierten Bedienelemente ohne Safe-Area-Puffer**: Niemals Fußleisten oder Sticky-Buttons mit statischem `bottom: 0px` definieren; zwingend immer `calc(x + env(safe-area-inset-bottom))` verwenden, um Überschneidungen mit Gestenleisten (Samsung/Android/iOS) zu verhindern.
3. **Keine Textgrößen unter 11 px**: Weder in D3-Knotenbeschriftungen noch in Metadaten dürfen Schriften kleiner als 11 px (bzw. 13 px für Fließtext) gerendert werden. Nicht-Entwickler auf mobilen Geräten müssen Inhalte mühelos erfassen können.
4. **Keine Split-View (Zweispaltigkeit) auf Bildschirmen ≤ 768 px**: Niemals versuchen, Graph und Arbeitsbereich gleichzeitig nebeneinander auf einem 412 px breiten Display darzustellen. Es darf mobil ausschließlich eine saubere Umschaltung zwischen Vollbild-Graph und Vollbild-Arbeitsbereich geben.
5. **Keine dauerhaften Animationen ohne Nutzeranlass**: Keine endlos rotierenden oder atmenden Hintergründe, es sei denn, ein echter Ladevorgang ist aktiv. Alle Übergänge müssen bei `prefers-reduced-motion: reduce` auf 0,01 ms gesetzt werden.
6. **Keine reinen Hover-Interaktionen**: Wichtige Aktionen oder Detail-Informationen dürfen niemals hinter `:hover`-Zuständen verborgen werden, da Touchscreens kein Hover unterstützen. Jede Information muss per Antippen zugänglich sein.
7. **Kein Monospace für lesbare Texte**: Monospace-Schriften (`JetBrains Mono`) sind ausschließlich für Hash-Werte, UUIDs und Code-Snippets reserviert. Überschriften (`Space Grotesk`) und Fließtexte (`Inter`) müssen eine ruhige, redaktionelle Leserlichkeit wahren.
8. **Keine blocking D3-Simulationen im Hauptthread**: Graph-Physiksimulationen dürfen nicht unendlich weiterlaufen, sondern müssen nach spätestens 300 Ticks stoppen (`alphaMin(0.005)`), um Akkulaufzeit und Reaktionsfähigkeit auf Mobilgeräten zu schonen.
