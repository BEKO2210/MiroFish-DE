# Konkrete Mobile- & Template-Fixes (Mobile First 412 px)

Dieses Dokument enthält für jeden im [Design-Audit](AUDIT.md) identifizierten Mangel den konkreten CSS- und Template-Fix mit exakter Dateiangabe, Selektoren und neuen Regeln.  
Entwickler können diese Codeblöcke direkt in die entsprechenden Vue-Komponenten übertragen.

---

## Mangel 1: Hero-Überschrift am Handy riesig und 4 Zeilen

- **Datei:** `frontend/src/views/Home.vue`
- **Zeilen im Ist-Zustand:** Template `Home.vue:22-29`, CSS `Home.vue:619-625`, `@media` `Home.vue:1294-1296, 1308-1310`
- **Problem:** Harte `<br>`-Tags und `font-size: 28px` erzeugen 4 riesige Zeilen (>360 px Höhe auf 412 px Geräten). Der Contributor-Tag liegt semantisch fehlerhaft im `<h1>`.

### Template-Fix:
```html
<!-- VORHER: -->
<h1 class="main-title">
  Lade beliebigen Bericht hoch<br>
  <span class="gradient-text">Erkenne die Zukunft sofort</span>
  <br>
  <span class="gradient-text">MiroFish ist jetzt auf Deutsch verfügbar.</span>
  <br>
  <span class="contributor-tag">Lokalisierung & Local LLM Integration von Belkis Aslani</span>
</h1>

<!-- NACHHER (Semantisch sauber, fließender Text ohne harte <br>): -->
<div class="hero-title-group">
  <h1 class="main-title">
    Dokumente verstehen. <span class="gradient-text">Reaktionen voraussehen.</span>
  </h1>
  <p class="hero-subtitle">
    MiroFish simuliert gesellschaftliche Meinungsdynamik auf Basis deiner Unterlagen.
  </p>
  <div class="contributor-tag" role="note">
    Lokalisierung & Open-Source-Integration
  </div>
</div>
```

### CSS-Fix (`Home.vue` `<style scoped>`):
```css
/* Ersetze .main-title und füge mobile Skalierung hinzu */
.main-title {
  font-family: var(--font-heading, 'Space Grotesk', sans-serif);
  font-size: clamp(1.5rem, 5vw + 0.5rem, 2.5rem); /* 24px mobil -> 40px desktop */
  font-weight: 700;
  line-height: 1.25;
  margin-bottom: var(--space-3, 12px);
  letter-spacing: -0.02em;
  color: var(--color-text-primary, #0F172A);
  word-wrap: break-word;
  hyphens: auto;
}

.hero-subtitle {
  font-family: var(--font-body, 'Inter', sans-serif);
  font-size: clamp(0.9375rem, 2vw + 0.5rem, 1.125rem); /* 15px mobil -> 18px desktop */
  line-height: 1.5;
  color: var(--color-text-secondary, #334155);
  margin-bottom: var(--space-4, 16px);
}

.contributor-tag {
  display: inline-flex;
  align-items: center;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-muted, #64748B);
  background: var(--color-bg-surface-subtle, #F1F5F9);
  padding: 4px 10px;
  border-radius: 9999px;
  border: 1px solid var(--color-border-subtle, #E2E8F0);
  margin-bottom: var(--space-4, 16px);
}

@media (max-width: 480px) {
  .main-title {
    font-size: 1.5rem; /* 24px auf 412px Geräten */
    line-height: 1.25;
  }
}
```

---

## Mangel 2: Badge „Elegante universelle Schwarm-Intelligenz-Engine“ bricht um

- **Datei:** `frontend/src/views/Home.vue`
- **Zeilen im Ist-Zustand:** Template `Home.vue:17-20`, CSS `Home.vue:598-617`
- **Problem:** 49 Zeichen ohne Bindestrich-Logik zusammen mit `/ v0.1-Preview` in einer Flex-Row sprengen die 372 px Nutzbreite des Handys.

### Template-Fix:
```html
<!-- VORHER: -->
<div class="tag-row">
  <span class="orange-tag">Elegante universelle Schwarm-Intelligenz-Engine</span>
  <span class="version-text">/ v0.1-Preview</span>
</div>

<!-- NACHHER (Kompakt, lesbar, verständlich): -->
<div class="tag-row">
  <span class="orange-tag">Szenario-Simulation</span>
  <span class="version-text">v0.1-Vorschau</span>
</div>
```

### CSS-Fix (`Home.vue` `<style scoped>`):
```css
.tag-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap; /* Verhindert horizontales Überlaufen */
  gap: var(--space-2, 8px);
  margin-bottom: var(--space-4, 16px);
}

.orange-tag {
  background: var(--color-brand-primary, #C2410C); /* WCAG-AA-konformes Terrakotta-Orange */
  color: #FFFFFF;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 600;
  border-radius: var(--radius-xs, 4px);
  white-space: nowrap;
}

.version-text {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-muted, #64748B); /* Kontrast 4.62:1 gegen Weiß */
  font-family: var(--font-mono, monospace);
}
```

---

## Mangel 3: Leere Flächen mit einzelnen Rauten-Symbolen

- **Datei:** `frontend/src/views/Home.vue:40`, `Home.vue:692-698` und `HistoryDatabase.vue:75`
- **Problem:** `.decoration-square` ist ein inhaltsleeres 60 × 60 px Quadrat mit 45 Grad Drehung, das Nutzer irritiert und Platz raubt. In der Dateiliste steht nur `◇`.

### Template-Fix in `Home.vue`:
```html
<!-- Zeile 40 ersatzlos entfernen oder durch funktionale Komponente ersetzen: -->
<!-- VORHER: <div class="decoration-square"></div> -->
<!-- NACHHER: Vollständig entfernt -->
```

### CSS-Fix in `Home.vue`:
```css
/* Selektor neutralisieren */
.decoration-square {
  display: none;
}
```

### Template-Fix in `HistoryDatabase.vue` (Zeile 73-77):
```html
<!-- VORHER: -->
<div class="files-empty" v-else>
  <span class="empty-file-icon">◇</span>
  <span class="empty-file-text">Keine Dateien</span>
</div>

<!-- NACHHER (Mit barrierefreiem Icon und klarem Text): -->
<div class="files-empty" v-else>
  <svg class="empty-file-icon" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
    <polyline points="14 2 14 8 20 8"></polyline>
  </svg>
  <span class="empty-file-text">Keine Dokumente verknüpft</span>
</div>
```

---

## Mangel 4: Karten der „Simulationsaufzeichnungen“ am Handy links/rechts abgeschnitten

- **Datei:** `frontend/src/components/HistoryDatabase.vue`
- **Zeilen im Ist-Zustand:** Skript `HistoryDatabase.vue:213-268`, CSS `HistoryDatabase.vue:655-687`
- **Problem:** Absolute JavaScript-Positionsberechnung mit `rowWidth = 1192 px` bei 4 Karten pro Zeile erzeugt 800 px horizontalen Überlauf am 412 px Handy. Fehlende `@media`-Queries.

### Skript-Fix (`HistoryDatabase.vue` `<script setup>`):
```javascript
// Zusätzliche reaktive Erkennung für mobile Ansicht
const isMobile = ref(false)

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

// getCardStyle anpassen: Auf Mobilgeräten keine absoluten Transforms anwenden!
const getCardStyle = (index) => {
  if (isMobile.value) {
    // Auf Mobilgeräten fließt die Karte normal im CSS-Grid/Flexbox
    return {
      position: 'relative',
      transform: 'none',
      width: '100%',
      opacity: 1,
      zIndex: 1
    }
  }

  // Bestehende Desktop-Logik nur für Bildschirme ab 768 px beibehalten:
  const total = projects.value.length
  // ... (bisheriger Desktop-Code)
}
```

### CSS-Fix (`HistoryDatabase.vue` `<style scoped>`):
```css
/* Container für Mobilgeräte als 1-spaltiges Grid konfigurieren */
@media (max-width: 767px) {
  .history-database {
    padding: var(--space-4, 16px) 0;
    overflow-x: hidden;
  }

  .section-header {
    padding: 0 var(--space-4, 16px);
    margin-bottom: var(--space-4, 16px);
  }

  .cards-container {
    display: grid !important;
    grid-template-columns: 1fr !important;
    gap: var(--space-3, 12px) !important;
    padding: 0 var(--space-4, 16px) !important;
    min-height: auto !important;
    width: 100% !important;
  }

  .project-card {
    position: relative !important;
    width: 100% !important;
    max-width: 100% !important;
    transform: none !important;
    border-radius: var(--radius-md, 8px) !important;
    margin-bottom: 0 !important;
    box-shadow: var(--shadow-sm, 0 1px 2px rgba(0,0,0,0.05)) !important;
  }

  /* Modal auf Mobilgeräten vollflächig anpassen */
  .modal-content {
    width: 100% !important;
    max-width: 95vw !important;
    max-height: 90vh !important;
    border-radius: var(--radius-lg, 12px) !important;
  }

  .modal-actions {
    flex-direction: column !important; /* 3 Buttons untereinander statt nebeneinander */
    gap: var(--space-2, 8px) !important;
    padding: var(--space-4, 16px) !important;
  }

  .modal-btn {
    width: 100% !important;
    flex-direction: row !important;
    justify-content: center !important;
    padding: 12px 16px !important;
    min-height: 48px !important;
  }
}
```

---

## Mangel 5: Im Prompt-Feld überlappt Badge „Engine: MiroFish-V1.0“ den Platzhaltertext

- **Datei:** `frontend/src/views/Home.vue`
- **Zeilen im Ist-Zustand:** Template `Home.vue:291-300`, CSS `Home.vue:1207-1238`
- **Problem:** `.model-badge` ist mit `position: absolute; bottom: 10px; right: 10px;` im `.input-wrapper` platziert und verdeckt den 5-zeiligen mobilen Platzhalter sowie den getippten Text.

### Template-Fix (`Home.vue`):
```html
<!-- VORHER:
<div class="input-wrapper">
  <textarea
    v-model="formData.simulationRequirement"
    class="code-input"
    placeholder="// Beschreibe Simulations- oder Vorhersagebedarf..."
  ></textarea>
  <div class="model-badge">Engine: MiroFish-V1.0</div>
</div>
-->

<!-- NACHHER (Badge wandert in eine strukturierte Meta-Leiste unter dem Textfeld): -->
<div class="prompt-container">
  <div class="input-wrapper">
    <textarea
      id="simulation-prompt"
      v-model="formData.simulationRequirement"
      class="prompt-textarea"
      placeholder="Beschreibe deine Fragestellung in natürlicher Sprache (z. B.: Wie reagiert die Bevölkerung, wenn eine neue Trasse beschlossen wird?)"
      rows="5"
      :disabled="loading"
      aria-label="Fragestellung für die Simulation"
    ></textarea>
  </div>
  <div class="input-meta-bar">
    <span class="char-count" v-if="formData.simulationRequirement.length > 0">
      {{ formData.simulationRequirement.length }} Zeichen
    </span>
    <span class="model-badge-inline">
      <span class="engine-dot" aria-hidden="true">●</span> Analyse-Engine: MiroFish V1
    </span>
  </div>
</div>
```

### CSS-Fix (`Home.vue` `<style scoped>`):
```css
.prompt-container {
  display: flex;
  flex-direction: column;
  gap: var(--space-2, 8px);
}

.input-wrapper {
  position: relative;
  width: 100%;
}

.prompt-textarea {
  width: 100%;
  padding: var(--space-4, 16px);
  border: 1px solid var(--color-border-default, #CBD5E1);
  border-radius: var(--radius-md, 8px);
  font-family: var(--font-body, 'Inter', sans-serif); /* Weg vom Monospace! */
  font-size: var(--font-size-body, 15px);
  line-height: 1.55;
  color: var(--color-text-primary, #0F172A);
  background: var(--color-bg-canvas, #FFFFFF);
  resize: vertical;
  min-height: 130px;
  box-sizing: border-box;
}

.prompt-textarea:focus {
  outline: none;
  border-color: var(--color-brand-primary, #C2410C);
  box-shadow: 0 0 0 3px rgba(194, 65, 12, 0.15);
}

/* Neue Leiste unterhalb des Textfeldes */
.input-meta-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: var(--color-text-muted, #64748B);
  padding: 0 var(--space-1, 4px);
}

.model-badge-inline {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-body, sans-serif);
  font-weight: 500;
  font-size: 12px;
  color: var(--color-text-muted, #64748B);
  background: var(--color-bg-surface-subtle, #F1F5F9);
  padding: 2px 8px;
  border-radius: var(--radius-xs, 4px);
  margin-left: auto;
}

.engine-dot {
  color: var(--color-success-text, #15803D);
  font-size: 8px;
}
```

---

## Mangel 6: Monospace-Fließtext in der gesamten App schwer lesbar

- **Datei:** `frontend/src/App.vue:17-24` und diverse Kindkomponenten
- **Problem:** `#app { font-family: 'JetBrains Mono', ... monospace; }` erzwingt globalen Monospace.

### CSS-Fix in `tokens.css` (wird automatisch wirksam) bzw. `App.vue`:
```css
/* In tokens.css bereits hinterlegt und via App.vue oder main.js nutzbar: */
#app {
  font-family: var(--font-body, 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif) !important;
  color: var(--color-text-primary, #0F172A) !important;
  background-color: var(--color-bg-canvas, #FFFFFF) !important;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Bestehende Monospace-Klassen in den Komponenten zähmen: */
.hero-desc,
.step-desc,
.field-desc,
.section-desc,
.card-desc,
.modal-requirement,
.detail-content,
.content-text {
  font-family: var(--font-body, 'Inter', sans-serif) !important;
  letter-spacing: normal !important;
}
```

---

## Mangel 7: Fachjargon in Nutzertexten

- **Dateien:** `Home.vue`, `Step1GraphBuild.vue`, `Step2EnvSetup.vue`, `Step3Simulation.vue`, `Step5Interaction.vue`
- **Problem:** Begriffe wie „Ontologie“, „GraphRAG“, „Dualwelt“, „Realitäts-Samen“, „Zep Cloud“ verwirren Nicht-Entwickler.

### Konkrete Template-Textersetzungen:

#### 1. In `Home.vue`:
- Zeile 176–178:  
  *Vorher:* „Vorhersage-Engine im Standby. Lade unstrukturierte Daten hoch, um die Simulationssequenz zu initialisieren.“  
  *Nachher:* **„Bereit zur Analyse. Lade deine Dokumente hoch, um die Simulation zu starten.“**
- Zeile 195–232 (Workflow-Titel & Beschreibungen):  
  - Step 01: *Vorher:* „Graphen-Aufbau / Realitäts-Samen-Extraktion & GraphRAG-Aufbau“  
    *Nachher:* **„Dokumenten-Analyse / Relevante Themen, Akteure und Fakten aus deinen Texten erfassen“**
  - Step 02: *Vorher:* „Umgebungsaufbau / Entitätsbeziehungs-Extraktion & Charakter-Generierung“  
    *Nachher:* **„Akteurs-Profile / Simulierte Personengruppen und Meinungsbilder erstellen“**
  - Step 03: *Vorher:* „Simulation starten / Duale Plattform-Parallel-Simulation“  
    *Nachher:* **„Diskussion simulieren / Reaktionen und Dynamiken auf zwei Plattformen durchspielen“**
  - Step 04: *Vorher:* „Berichtsgenerierung / ReportAgent mit reichhaltigem Toolset“  
    *Nachher:* **„Ergebnisbericht / Verständliche Zusammenfassung mit Kernaussagen und Zitaten“**
  - Step 05: *Vorher:* „Tiefe Interaktion / Gespräch mit beliebiger Person in der simulierten Welt“  
    *Nachher:* **„Vertiefende Fragen / Gezielte Nachfragen an Akteure oder den Analysebericht stellen“**
- Zeile 310:  
  *Vorher:* „Engine starten“  
  *Nachher:* **„Simulation starten“**

#### 2. In `Step1GraphBuild.vue`:
- Zeile 9:  
  *Vorher:* „Ontologie-Generierung“  
  *Nachher:* **„Themenstruktur aufbauen“**
- Zeile 19 & 123 (Entfernen interner REST-Endpoints):  
  *Vorher:* `<p class="api-note">POST /api/graph/ontology/generate</p>`  
  *Nachher:* `<p class="step-hint">Schritt 1 von 2: Hauptthemen und Beziehungen werden erkannt</p>`
- Zeile 113:  
  *Vorher:* „GraphRAG-Aufbau“  
  *Nachher:* **„Wissensbasis verknüpfen“**
- Zeile 132–141 (Metriken-Beschriftung):  
  *Vorher:* „SCHEMA-TYPEN“ / „Beziehungskanten“  
  *Nachher:* **„Erkannte Themenbereiche“ / „Verknüpfungen“**

---

## Mangel 8: Der 50/50 Split-Screen-Kollaps am Smartphone

- **Dateien:** `frontend/src/views/MainView.vue`, `SimulationView.vue`, `SimulationRunView.vue`, `ReportView.vue`, `InteractionView.vue`
- **Zeilen im Ist-Zustand:** `MainView.vue:89-90, 113-123`, CSS `MainView.vue:523-539`
- **Problem:** Bei `viewMode = 'split'` erhalten beide Panels auf 412 px jeweils 206 px Breite – beide Seiten sind unbrauchbar.

### Skript-Fix (`MainView.vue` `<script setup>`):
```javascript
// Auf Bildschirmen unter 768px niemals den 'split'-Modus als Standard erlauben:
onMounted(() => {
  if (window.innerWidth < 768) {
    viewMode.value = 'workbench' // Auf Mobilgeräten direkt der Arbeitsbereich
  }
})
```

### CSS-Fix (`MainView.vue` `<style scoped>`):
```css
/* Mobil-Regel erzwingt volle Breite für das jeweils aktive Panel */
@media (max-width: 767px) {
  .content-area {
    flex-direction: column !important;
    overflow-y: auto !important;
  }

  .panel-wrapper {
    width: 100% !important;
    height: auto !important;
    min-height: calc(100vh - 60px) !important;
    border-right: none !important;
  }

  /* Wenn split aktiv war, auf Handy automatisch den Arbeitsbereich zeigen */
  .panel-wrapper.left {
    display: none !important; /* Standardmäßig ausblenden */
  }

  /* Nur anzeigen, wenn Nutzer explizit auf 'Graph' geschaltet hat */
  .main-view[data-mobile-view="graph"] .panel-wrapper.left {
    display: block !important;
  }
  .main-view[data-mobile-view="graph"] .panel-wrapper.right {
    display: none !important;
  }
}
```

---

## Mangel 9: App-Header-Elemente kollidieren auf 412 px

- **Datei:** `frontend/src/views/MainView.vue` (sowie alle verwandten Views)
- **Zeilen im Ist-Zustand:** CSS `MainView.vue:418-450`
- **Problem:** `.header-center` ist absolut mittig fixiert und überlappt Brand-Logo und Workflow-Steps am Smartphone.

### CSS-Fix (`MainView.vue` `<style scoped>`):
```css
@media (max-width: 767px) {
  .app-header {
    height: auto !important;
    min-height: 56px !important;
    padding: var(--space-2, 8px) var(--space-4, 16px) !important;
    display: flex !important;
    flex-wrap: wrap !important; /* Erlaubt zweizeiligen Header */
    justify-content: space-between !important;
    gap: var(--space-2, 8px) !important;
  }

  .brand {
    font-size: 16px !important;
  }

  /* Absolute Zentrierung am Handy aufheben */
  .header-center {
    position: static !important;
    transform: none !important;
    order: 3 !important; /* Rutscht in die zweite Zeile */
    width: 100% !important;
  }

  .view-switcher {
    width: 100% !important;
    display: flex !important;
    justify-content: center !important;
  }

  .switch-btn {
    flex: 1 !important;
    text-align: center !important;
    min-height: 38px !important;
    padding: 8px 12px !important;
    font-size: 13px !important;
  }

  /* Den 'Zweispaltig'-Knopf am Handy komplett verstecken */
  .switch-btn:nth-child(2) {
    display: none !important;
  }

  .header-right {
    order: 2 !important;
    gap: var(--space-2, 8px) !important;
  }

  .workflow-step .step-name {
    display: none !important; /* Nur 'Schritt 1/5' anzeigen, Platz sparen */
  }
}
```

---

## Mangel 10: Fehlende Zeitschätzung und Statusführung bei langen Läufen (Minuten bis 1 Stunde)

- **Datei:** `frontend/src/components/Step3Simulation.vue`
- **Zeilen im Ist-Zustand:** Template `Step3Simulation.vue:6-91`
- **Problem:** Nur zwei passive Kacheln („ROUND 0/-“, „0h 0m“). Keine ETA, kein Fortschrittsbalken, keine Beruhigung bei 30-minütiger Laufzeit.

### Template-Fix (`Step3Simulation.vue`):
```html
<!-- Neue, vertrauenerweckende Status-Sektion über der Zeitleiste: -->
<div class="simulation-progress-banner" role="region" aria-label="Simulationsstatus">
  <div class="progress-banner-header">
    <div class="pulse-indicator" aria-hidden="true"></div>
    <div class="progress-title-group">
      <h2 class="progress-title">Simulation wird berechnet</h2>
      <p class="progress-subtitle">
        Runde {{ runStatus.twitter_current_round || 0 }} von {{ runStatus.total_rounds || 40 }}
      </p>
    </div>
    <div class="progress-eta-badge">
      <span>Noch ca. 15–20 Min.</span>
    </div>
  </div>

  <!-- Zugänglicher Fortschrittsbalken -->
  <div class="progress-bar-track" role="progressbar" :aria-valuenow="progressPercent" aria-valuemin="0" aria-valuemax="100">
    <div class="progress-bar-fill" :style="{ width: progressPercent + '%' }"></div>
  </div>

  <!-- Beruhigender Hintergrund-Hinweis -->
  <div class="background-resilience-note">
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
      <circle cx="12" cy="12" r="10"></circle>
      <polyline points="12 6 12 12 16 14"></polyline>
    </svg>
    <span>
      Du kannst dieses Browserfenster schließen. Die Simulation läuft serverseitig weiter. Bei Rückkehr steht dein Bericht bereit.
    </span>
  </div>
</div>
```

### CSS-Fix (`Step3Simulation.vue` `<style scoped>`):
```css
.simulation-progress-banner {
  background: var(--color-bg-surface-raised, #FFFFFF);
  border: 1px solid var(--color-border-subtle, #E2E8F0);
  border-radius: var(--radius-lg, 12px);
  padding: var(--space-4, 16px);
  margin-bottom: var(--space-4, 16px);
  box-shadow: var(--shadow-sm, 0 1px 3px rgba(0,0,0,0.05));
}

.progress-banner-header {
  display: flex;
  align-items: center;
  gap: var(--space-3, 12px);
  margin-bottom: var(--space-3, 12px);
}

.pulse-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--color-brand-primary, #C2410C);
  animation: pulse-ring 1.8s infinite ease-out;
  flex-shrink: 0;
}

@keyframes pulse-ring {
  0% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(194, 65, 12, 0.6); }
  70% { transform: scale(1.1); box-shadow: 0 0 0 8px rgba(194, 65, 12, 0); }
  100% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(194, 65, 12, 0); }
}

.progress-title {
  font-family: var(--font-heading, sans-serif);
  font-size: 16px;
  font-weight: 700;
  margin: 0;
  color: var(--color-text-primary, #0F172A);
}

.progress-subtitle {
  font-size: 13px;
  color: var(--color-text-secondary, #334155);
  margin: 0;
}

.progress-eta-badge {
  margin-left: auto;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-brand-primary, #C2410C);
  background: var(--color-brand-subtle, #FFF7ED);
  padding: 4px 10px;
  border-radius: var(--radius-full, 9999px);
  border: 1px solid var(--color-brand-border, #FDBA74);
  white-space: nowrap;
}

.progress-bar-track {
  width: 100%;
  height: 8px;
  background: var(--color-bg-surface-subtle, #F1F5F9);
  border-radius: var(--radius-full, 9999px);
  overflow: hidden;
  margin-bottom: var(--space-3, 12px);
}

.progress-bar-fill {
  height: 100%;
  background: var(--color-brand-primary, #C2410C);
  border-radius: var(--radius-full, 9999px);
  transition: width 0.4s ease;
}

.background-resilience-note {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2, 8px);
  font-size: 12px;
  line-height: 1.45;
  color: var(--color-text-muted, #64748B);
  background: var(--color-bg-surface, #F8FAFC);
  padding: 8px 12px;
  border-radius: var(--radius-sm, 6px);
}

.background-resilience-note svg {
  flex-shrink: 0;
  margin-top: 1px;
}
```

---

## Mangel 11: Touch-Targets unter 44 px (Löschen-Button, Switcher)

- **Dateien:** `Home.vue:1166-1179` (`.remove-btn`), `MainView.vue:452-468` (`.switch-btn`)
- **Problem:** Buttons mit 24 × 24 px verletzen WCAG 2.5.5 / 2.5.8 und sind auf Smartphones kaum treffbar.

### CSS-Fix in `Home.vue`:
```css
/* Datei-Entfernen-Button auf barrierefreie Mindestgröße erweitern */
.remove-btn {
  width: 44px !important;
  height: 44px !important;
  min-width: 44px !important;
  min-height: 44px !important;
  background: transparent !important;
  color: var(--color-error-text, #B91C1C) !important;
  border: 1px solid var(--color-border-subtle, #E2E8F0) !important;
  border-radius: var(--radius-sm, 6px) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  cursor: pointer !important;
  touch-action: manipulation;
}

.remove-btn:hover,
.remove-btn:focus-visible {
  background: var(--color-error-bg, #FEF2F2) !important;
  border-color: var(--color-error-border, #FECACA) !important;
}
```

---

## Mangel 12: WCAG-AA-Kontrast-Korrekturen für bestehende Utility-Klassen

- **Dateien:** Alle Komponenten
- **Problem:** Bisherige Grauwerte (`#999999`, `#888888`, `#9CA3AF`) und altes Orange (`#FF5722`) scheitern am Kontrasttest.

### Globaler CSS-Klassen-Fix (Drop-in):
```css
/* Ersetzt unlesbare #999/#888 Muted-Farben durch WCAG-AA-konforme Token */
.version-text,
.detail-label,
.field-desc,
.metric-label,
.step-num,
.console-meta,
.upload-hint,
.stat-label,
.divider-text,
.section-title {
  color: var(--color-text-muted, #64748B) !important; /* 4.62:1 gegen Weiß -> PASS */
}

/* Ersetzt Statuspunkte durch barrierefreie Farben */
.status-dot {
  color: var(--color-success-text, #15803D) !important; /* 5.02:1 -> PASS */
}

.status-red,
.status-dot.status-red {
  color: var(--color-error-text, #B91C1C) !important; /* 6.47:1 -> PASS */
}

/* Gradient-Text für Überschriften lesbarer gestalten */
.gradient-text {
  background: linear-gradient(90deg, #C2410C, #EA580C) !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  background-clip: text !important;
}
```
