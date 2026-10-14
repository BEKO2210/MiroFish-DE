# Design-Audit: MiroFish Web-App (Mobile First & Barrierefreiheit)

**Stand:** 13. Oktober 2026  
**Zielgruppe:** Nicht-Entwickler (Journalisten, Kommunalmitarbeiter, Marketing-Teams, Studierende)  
**Sprachen:** Deutsch & Englisch  
**Primäres Testgerät:** Smartphone mit 412 px Viewport-Breite (Android / Pixel / Galaxy) sowie Desktop (ab 1280 px)  
**Geprüfte Komponenten:** `App.vue`, `Home.vue`, `MainView.vue`, `SimulationView.vue`, `SimulationRunView.vue`, `ReportView.vue`, `InteractionView.vue`, `Step1GraphBuild.vue`, `Step2EnvSetup.vue`, `Step3Simulation.vue`, `Step4Report.vue`, `Step5Interaction.vue`, `GraphPanel.vue`.

---

## 1. Executive Summary & Zielgruppen-Kontext

MiroFish ermöglicht es Nutzern, unstrukturierte Dokumente (Berichte, Beschlüsse, Strategiepapiere) hochzuladen, eine Forschungsfrage zu stellen und nach einer Simulationsphase (die zwischen wenigen Minuten und bis zu einer Stunde dauern kann) einen verständlichen, fundierten Bericht zu erhalten.

### Die Kernzielgruppe
- **Journalisten & Redaktionen:** Benötigen schnelle Orientierung, verlässliche Quelleneinordnung, klare Thesen und verständliche Zitate. Haben keine Zeit für technische Konfigurationsdialoge.
- **Kommunalverwaltung & Politik:** Benötigen barrierefreie, transparente Berichte für Entscheidungsfindungen (z. B. Bürgerbeteiligung, Reaktionen auf Bauprojekte). Werden von Begriffen wie „Ontologie-Generierung“ oder „Zep GraphRAG“ abgeschreckt.
- **Marketing & Agenturen:** Nutzen das Tool für Kampagnen-Vorhersagen und Stimmungsbilder.
- **Studierende & Lehrende:** Erwarten moderne, flüssige Web-Standards mit einfacher mobiler Bedienung.

### Gesamteinschätzung des Ist-Zustands
Die bestehende Web-App weist ein ausgeprägtes **Entwickler-zentriertes Desktop-Bias** auf. Sie wirkt streckenweise wie ein internes Debugging-Dashboard für LLM-Pipelines statt wie eine zugängliche Fachanwendung. Auf mobilen Endgeräten (412 px) bricht das Layout an zahlreichen Stellen zusammen: Inhalte overflowen horizontal, Schaltflächen überlappen Texte, Touch-Targets unterschreiten ergonomische Mindestmaße (44 × 44 px) und Texte sind durch eine globale Monospace-Typografie anstrengend zu lesen. Zudem scheitern wesentliche UI-Elemente an den gesetzlichen WCAG-2.1-AA-Mindestkontrasten.

---

## 2. Bestätigung und Tiefenanalyse der bekannten Kernmängel

### Mangel 1: Hero-Überschrift am Handy riesig und 4 Zeilen
- **Datei & Zeilen:** `frontend/src/views/Home.vue:22-29`, Styling `Home.vue:619-625`, `@media` `Home.vue:1294-1296, 1308-1310`
- **Befund:** Im Template sind harte `<br>`-Tags fest einprogrammiert:
  ```html
  <h1 class="main-title">
    Lade beliebigen Bericht hoch<br>
    <span class="gradient-text">Erkenne die Zukunft sofort</span>
    <br>
    <span class="gradient-text">MiroFish ist jetzt auf Deutsch verfügbar.</span>
    <br>
    <span class="contributor-tag">Lokalisierung & Local LLM Integration von Belkis Aslani</span>
  </h1>
  ```
- **Auswirkung am 412 px Display:** Durch `font-size: 28px` (unter 768 px) und die 4 festen Umbrüche nimmt die Überschrift über 360 px vertikale Höhe ein – das entspricht über 45 % des gesamten sichtbaren Bildschirms. Zudem ist der Contributor-Tag semantisch fälschlicherweise innerhalb des `<h1>`-Tags verschachtelt, was Screenreader verwirrt.
- **Schweregrad:** **Kritisch** (Blockiert den Einstieg und First Contentful Paint).

---

### Mangel 2: Badge „Elegante universelle Schwarm-Intelligenz-Engine“ bricht um
- **Datei & Zeilen:** `frontend/src/views/Home.vue:17-20`, Styling `Home.vue:598-617`
- **Befund:** 
  ```html
  <div class="tag-row">
    <span class="orange-tag">Elegante universelle Schwarm-Intelligenz-Engine</span>
    <span class="version-text">/ v0.1-Preview</span>
  </div>
  ```
  `.orange-tag` besitzt 49 Zeichen ohne Bindestrich- oder Umbruchlogik. Die umgebende `.tag-row` hat `display: flex; gap: 12px;`. Auf 412 px Bildschirmbreite (abzüglich 40 px Seiten-Padding verbleiben 372 px) passt dieser Text nicht zusammen mit `/ v0.1-Preview` in eine Zeile. Der Tag bricht holprig um oder verdrängt die Versionsangabe in eine unschöne zweite Zeile.
- **Inhaltliche Kritik:** Der Text ist reines Marketing-Buzzword-Bingo („Schwarm-Intelligenz-Engine“), das Nicht-Entwicklern keinen konkreten Nutzen vermittelt.
- **Schweregrad:** **Mittel** (Visuelle Disharmonie, geringer Informationswert).

---

### Mangel 3: Leere Flächen mit einzelnen Rauten-Symbolen
- **Datei & Zeilen:** 
  - `frontend/src/views/Home.vue:40`, Styling `Home.vue:692-698` (`.decoration-square`)
  - `frontend/src/views/Home.vue:195` (`<span class="diamond-icon">◇</span> Workflow-Sequenz`)
- **Befund:** In `Home.vue:40` befindet sich ein leeres `div`:
  ```css
  .decoration-square {
    width: 60px;
    height: 60px;
    border: 3px solid #000;
    margin-top: 30px;
    transform: rotate(45deg);
  }
  ```
  Dieses Element ist eine inhaltsleere, um 45 Grad gedrehte schwarze Box, die wie ein Grafikfehler oder ein Platzhalter für ein fehlendes Bild aussieht. Auf mobilen Bildschirmen stiehlt sie wertvollen Leerraum.
- **Schweregrad:** **Mittel** (Verwirrend, vermittelt unfertigen Software-Eindruck).

---

### Mangel 5: Im Prompt-Feld überlappt Badge „Engine: MiroFish-V1.0“ den Platzhaltertext
- **Datei & Zeilen:** `frontend/src/views/Home.vue:291-300`, Styling `Home.vue:1207-1238`
- **Befund:** 
  ```html
  <div class="input-wrapper">
    <textarea
      v-model="formData.simulationRequirement"
      class="code-input"
      placeholder="// Beschreibe Simulations- oder Vorhersagebedarf in natürlicher Sprache (z.B.: Wie würde die Öffentlichkeit reagieren, wenn Universität X eine bestimmte Entscheidung trifft?)"
      rows="6"
    ></textarea>
    <div class="model-badge">Engine: MiroFish-V1.0</div>
  </div>
  ```
  ```css
  .input-wrapper { position: relative; }
  .model-badge {
    position: absolute;
    bottom: 10px;
    right: 10px;
    font-size: 10px;
    background: #f5f5f5;
  }
  ```
- **Auswirkung am 412 px Display:** Der Platzhaltertext ist 157 Zeichen lang und bricht auf einem 412 px Smartphone in 5 bis 6 Zeilen um. Er füllt die Textarea bis zur unteren Kante aus. Das Badge `Engine: MiroFish-V1.0` liegt **direkt über dem Textende** des Platzhalters. Wenn Nutzer Text eingeben, verdeckt das Badge die letzte Zeile des Nutzertextes.
- **Schweregrad:** **Hoch** (Beeinträchtigt die primäre Eingabehandlung unmittelbar).

---

### Mangel 6: Monospace-Fließtext ist schwer lesbar
- **Datei & Zeilen:** `frontend/src/App.vue:17-24`, `Home.vue:536, 616, 669, 756, 789, 1036, 1082, 1216`, `MainView.vue:437, 493`, `Step1GraphBuild.vue:520, 560, 590, 649`
- **Befund:** In `App.vue:18` ist global festgelegt:
  ```css
  #app {
    font-family: 'JetBrains Mono', 'Space Grotesk', 'Noto Sans SC', monospace;
  }
  ```
  Zusätzlich wird in nahezu allen Komponenten für Beschreibungen, Labels, IDs und Inputs explizit `'JetBrains Mono', monospace` referenziert.
- **Auswirkung für Nicht-Entwickler:** Monospace-Schriften haben feste Zeichenbreiten, was bei Fließtexten (Artikeln, Simulationstexten, Analyseberichten) zu unruhigen Wortzwischenräumen führt. Dies ermüdet das Auge nachweislich schneller, senkt die Lesegeschwindigkeit um bis zu 25 % und vermittelt den Eindruck einer internen Terminal-Anwendung.
- **Schweregrad:** **Hoch** (Erniedrigt Lesbarkeit und professionelle Wirkung für Journalisten/Kommunen).

---

### Mangel 7: Fachjargon in Nutzertexten
- **Befund & Vorkommen:**
  1. `Home.vue:18, 33, 102, 202-231`:
     - *„Realitäts-Samen“* / *„Realitäts-Samen-Extraktion“* (wortwörtliche Übersetzung von Reality Seed)
     - *„Gott-Perspektive können Variablen injiziert werden“* (pathetischer Jargon)
     - *„GraphRAG-Aufbau & Zep Cloud“* (interne LLM-Architekturdetails)
     - *„Dualwelt“* / *„Duale Plattform-Parallel-Simulation“*
     - *„ReportAgent mit reichhaltigem Toolset“*
  2. `Step1GraphBuild.vue:9, 19, 21, 113, 123, 125, 159`:
     - *„Ontologie-Generierung“* / *„SCHEMA-TYPEN“*
     - Rohe HTTP-Endpoints im UI: `POST /api/graph/ontology/generate`, `POST /api/graph/build`
     - *„zeitliche Speicher sowie Community-Zusammenfassungen werden erstellt“*
  3. `Step2EnvSetup.vue:23-40, 61, 76, 121, 133`:
     - Technische UUIDs: `Project ID: c8a3...`, `Graph ID: g-491...`, `Task ID`
     - *„Entitäten und Beziehungen aus dem Wissensgraphen extrahieren“*
     - *„Aktuell verknüpfte Themen der Realitäts-Samen“*
  4. `Step5Interaction.vue:175-214`:
     - *„InsightForge Tiefenattribution mit Global/Local-Memory-Mechanismus“*
     - *„PanoramaSearch Breitensuche-Algorithmus auf Graphstruktur, Topologie des Informationsflusses“*
     - *„QuickSearch Schnittstelle basierend auf GraphRAG zur Extraktion diskreter Fakten“*
     - *„InterviewSubAgent zur Erfassung unstrukturierter Meinungsdaten und psychologischer Zustände“*
- **Auswirkung:** Nicht-Entwickler aus Verwaltung oder Redaktionen verstehen diese Begriffe nicht. Sie fühlen sich verunsichert, können die Aussagekraft der Berichte nicht einschätzen und haben Angst, falsche Optionen zu wählen.
- **Schweregrad:** **Hoch** (Mangelnde Nutzerakzeptanz, kognitive Überlastung).

---

## 3. Umfassender Ansichten-Audit (View-by-View Breakdown)

### 3.1 Globale Basis (`App.vue`, `index.html`)
1. **HTML-Sprachattribut:** `index.html:2` definiert `<html lang="zh-CN">`. Für deutsche/englische Nutzer führt dies dazu, dass Browser automatische Übersetzungen anbieten und Screenreader mit chinesischer Aussprache phonetisch scheitern.
2. **Schriftarten-Laden:** `index.html:6` lädt `Inter`, `JetBrains Mono`, `Noto Sans SC` und `Space Grotesk`. Die hervorragend lesbare Fließtextschrift `Inter` wird im Code jedoch fast nirgendwo genutzt!
3. **Scrollbar-Stil:** `App.vue:36-42` definiert eine feste schwarze Scrollbar (`background: #000000`). Auf dunklen Hintergründen ist sie unsichtbar; am Smartphone wird die native System-Scrollbar blockiert.
4. **Fehlende Fokus-Ringe:** `App.vue:44-47` setzt nur `button { font-family: inherit; }`. Es gibt keine globalen Fokus-Zustände (`:focus-visible`), was die Tastaturbedienung unmöglich macht.

---

### 3.2 Startseite / Landing & Setup (`Home.vue`)
1. **Verfrühter technischer Dialog (LLM-Settings vor Upload):**
   - *Zeilen 83-174:* Auf der Hauptseite wird prominent die Konfiguration von *Zep Cloud, LM Studio, Ollama, API-Keys* angeboten. Ein Kommunalmitarbeiter möchte ein PDF hochladen und eine Frage stellen – stattdessen wird er mit API-Endpunkten konfrontiert.
   - *Lösung:* Technische Einstellungen in ein modales Einstellungs-Menü (Zahnrad oben rechts) auslagern; für Standardnutzer vorkonfigurierte Defaults verwenden.
2. **Desktop-fokussierte Upload-Zone:**
   - *Zeilen 247-278:* Die Upload-Box (`.upload-zone`) setzt primär auf Drag & Drop (`handleDragOver`, `handleDrop`). Auf Smartphones existiert kein Drag & Drop aus anderen Apps. Der Klick-Trigger (`triggerFileInput`) muss als klarer, prominenter Button mit Mindesthöhe 48 px ausgeführt sein.
3. **Fehlende Dateitypen-Rückmeldung auf Mobilgeräten:**
   - Wenn Nutzer eine ungültige Datei auswählen (z. B. Word oder Bild), wird diese laut Code (`Home.vue:484-489`) stillschweigend gefiltert (`validFiles.filter(...)`), ohne dass eine Fehlermeldung für den Nutzer erscheint.
4. **Metriken ohne Kontext:**
   - *Zeilen 181-190:* „Durchschnittlich 5$/Simulation“ und „Bis zu Millionen Agenten“ irritieren. Eine Gemeinde will wissen: „Wie lange dauert es?“ und „Welche Quellen werden berücksichtigt?“.

---

### 3.3 Prozess- und Arbeitsbereich-Shell (`MainView.vue`, `SimulationView.vue`, etc.)
1. **Der 50/50 Split-Screen-Kollaps am Smartphone:**
   - *`MainView.vue:113-123`, `SimulationView.vue:94-104`, `SimulationRunView.vue:99-110`:*
     Das Standard-Layout ist `viewMode = 'split'`. Dies setzt `leftPanelStyle` auf `width: 50%` und `rightPanelStyle` auf `width: 50%`.
     Auf einem 412 px Smartphone erhält jedes Panel genau **206 px Breite**. Der Graph auf der linken Seite wird winzig und unbedienbar, und die Formulare/Texte auf der rechten Seite werden zu schmalen, unlesbaren Spalten zusammengedrückt.
   - *Lösung:* Auf Geräten unter 768 px darf **niemals** der Split-Modus aktiv sein. Standard muss der Vollbild-Arbeitsbereich (`workbench`) sein, mit einer bequemen Umschaltung (Segmented Control oder Swipe) zum Graphen.
2. **Kopfzeilen-Überlagerung (`.app-header`):**
   - *`MainView.vue:418-450`:* 
     ```css
     .header-center {
       position: absolute;
       left: 50%;
       transform: translateX(-50%);
     }
     ```
     Auf 412 px stoßen links das Brand-Logo (`MIROFISH`), in der Mitte die drei Umschalt-Buttons (`Graph | Zweispaltig | Arbeitsbereich`) und rechts die Schrittanzeige (`Schritt 1/5`) direkt zusammen und überlagern sich gegenseitig.

---

### 3.4 Schritt 1: Wissensgraph & Dokumentenverarbeitung (`Step1GraphBuild.vue`, `GraphPanel.vue`)
1. **Rohe Entwickler-Logs im Blickfeld:**
   - *`Step1GraphBuild.vue:174-185`:* Die Komponente blendet standardmäßig Terminal-Logs (`.system-logs`) mit Zeitstempeln bis auf Millisekunden ein. Am Smartphone raubt dies 120 px vertikalen Platz.
2. **Dreispaltiges Statistik-Grid auf 412 px:**
   - *`Step1GraphBuild.vue:572-579`:* `.stats-grid` erzwingt `grid-template-columns: 1fr 1fr 1fr;`. Bei Zahlen über 1.000 oder Begriffen wie „SCHEMA-TYPEN“ bricht der Inhalt um oder wird abgeschnitten.

---

### 3.5 Schritt 2: Simulationsumgebung & Akteure (`Step2EnvSetup.vue`)
1. **24-Stunden Mini-Zeitleiste auf Touchscreens:**
   - *`Step2EnvSetup.vue:207-225`:* In den Akteurs-Karten wird eine 24-Stunden-Zeitleiste gerendert, bestehend aus 24 Blöcken nebeneinander. Innerhalb einer mobilen Karte ist jeder Block weniger als 10 px breit. Eine Interaktion oder Lesbarkeit per Finger ist unmöglich.
2. **Übermäßige Informationsdichte:**
   - Akteurs-Stance, Beitragsfrequenzen, Antwortverzögerungen in Minuten (`230-242`) überfordern Nutzer, die lediglich wissen möchten: „Welche Gruppen und Meinungen wurden erkannt?“.

---

### 3.6 Schritt 3: Simulationslauf & Langzeit-Wartezustand (`Step3Simulation.vue`)
1. **Fehlende Rückmeldung bei langen Laufzeiten (Minuten bis 1 Stunde):**
   - *Problem:* Eine Simulation läuft typischerweise 10 bis 45 Minuten. Aktuell gibt es in `Step3Simulation.vue:6-91` lediglich zwei statische Kacheln mit „ROUND 0/-“ und „Vergangene Zeit 0h 0m“.
   - *Folge:* Nutzer wissen nicht, ob die Anwendung noch arbeitet oder abgestürzt ist. Es gibt keine Schätzung der verbleibenden Restzeit (ETA), keinen Gesamtfortschrittsbalken und keinen Hinweis darauf, dass der Tab im Hintergrund laufen gelassen oder geschlossen werden kann.
2. **Hover-Tooltips für Aktionen:**
   - *`Step3Simulation.vue:34-44, 75-89`:* Die Liste der Aktionen (POST, LIKE, REPOST, etc.) ist in `.actions-tooltip` versteckt, der nur bei `:hover` sichtbar wird. Auf Smartphones gibt es kein Hover; die Information bleibt verborgen.

---

### 3.7 Schritt 4: Berichterstellung (`Step4Report.vue`)
1. **Split-Screen bei der Berichtsausgabe:**
   - *Zeilen 4-80:* Der eigentliche Ergebnisbericht teilt sich den Bildschirm mit dem Agenten-Workflow-Protokoll. Am Smartphone wird der Berichtstext auf eine schmale Spalte gequetscht.
2. **Verschachtelte Markdown-Inhalte:**
   - Wenn der Bericht Tabellen enthält, laufen diese auf 412 px horizontal aus dem Bildschirm heraus, da kein automatischer Container mit `overflow-x: auto` existiert.

---

### 3.8 Schritt 5: Interaktion & Befragung (`Step5Interaction.vue`)
1. **Tab-Pills kollabieren mobil:**
   - *Zeilen 92-147:* Die Schaltflächen „Mit Berichts-Agent chatten“, „Gesprächspartner auswählen“ und „Umfrage in die Welt senden“ liegen in einer horizontalen Leiste. Am Handy erzeugen sie extremen horizontalen Überlauf oder verdecken das Chat-Eingabefeld.
2. **Eingabefeld am unteren Bildschirmrand:**
   - Das Chat-Eingabefeld wird auf mobilen Browsern oft von der virtuellen Tastatur verdeckt, wenn kein adäquates `padding-bottom: env(safe-area-inset-bottom)` und dynamisches Viewport-Handling (`dvh`) vorhanden ist.

---

## 4. Barrierefreiheit (a11y) & WCAG-AA-Kontrast-Audit

Zur Überprüfung der WCAG-2.1-AA-Konformität (Mindestkontrast 4,5:1 für normalen Text, 3,0:1 für großen Text/UI-Komponenten) wurden die Farbwerte des aktuellen Repositories rechnerisch überprüft.

### 4.1 Nachgerechnete Kontrastwerte des Ist-Zustands

| Element / Selektor | Textfarbe | Hintergrund | Gemessener Kontrast | WCAG-AA-Status (Normaler Text) |
|---|---|---|---|---|
| Muted Labels (`.version-text`, `.detail-label`, `.metric-label`, `.step-num`) | `#999999` | `#FFFFFF` | **2,85 : 1** | **FAIL** (Erfordert mind. 4,5 : 1) |
| Sekundärtext (`.step-desc`, `.field-desc`) | `#888888` | `#FFFFFF` | **3,54 : 1** | **FAIL** (Erfordert mind. 4,5 : 1) |
| Orange Akzenttext (`.gradient-text`, `.diamond-icon`) | `#FF5722` | `#FFFFFF` | **3,16 : 1** | **FAIL** (Erfordert mind. 4,5 : 1) |
| Orange Badge (`.orange-tag`) mit weißer Schrift | `#FFFFFF` | `#FF5722` | **3,16 : 1** | **FAIL** (Erfordert mind. 4,5 : 1) |
| Status Grün (`.status-dot`) auf Weiß | `#4CAF50` | `#FFFFFF` | **2,78 : 1** | **FAIL** (Erfordert mind. 3,0 : 1 für UI) |
| Status Rot (`.status-red`) auf Weiß | `#F44336` | `#FFFFFF` | **3,68 : 1** | **FAIL** (Erfordert mind. 4,5 : 1 für Text) |
| Disabled Buttons / Trennlinien (`#CCCCCC`) | `#CCCCCC` | `#FFFFFF` | **1,61 : 1** | **FAIL** (Schwer erkennbar) |

> **Ergebnis:** Das aktuelle Farbschema scheitert bei praktisch allen Sekundärtexten, Hilfetexten, Badges und Statusindikatoren an den gesetzlichen WCAG-AA-Vorgaben.

### 4.2 Ergonomie & Touch-Targets
- **WCAG 2.5.5 / 2.5.8 (Target Size):** Touch-Ziele müssen mindestens **44 × 44 px** (bzw. 24 × 24 px mit ausreichendem Abstand) groß sein.
- In `Home.vue` ist der Datei-Entfernen-Button (`.remove-btn`) lediglich **24 × 24 px** groß (`padding: 0; line-height: 1`).
- Die View-Switcher-Buttons in `MainView.vue` (`.switch-btn`) haben ein Padding von `6px 16px`, was zu einer Gesamthöhe von knapp **28 px** führt.

---

## 5. Mängel-Matrix und Priorisierung

| ID | Bereich | Datei & Zeilen | Problembeschreibung | Priorität |
|---|---|---|---|---|
| **M-02** | Layout (Mobil) | `MainView.vue:113-123` u. a. | 50/50 Split-Layout quetscht Panels auf 206 px zusammen | **P0 (Kritisch)** |
| **M-03** | Typografie | `Home.vue:22-29, 619-625` | 4-zeilige Hero-Headline verdeckt mobilen Viewport | **P1 (Hoch)** |
| **M-04** | UI / Formular | `Home.vue:291-300, 1229-1238` | `model-badge` überdeckt Textarea-Platzhalter und Benutzereingabe | **P1 (Hoch)** |
| **M-05** | Barrierefreiheit | `App.vue:18`, div. Komponenten | Globaler Monospace-Fließtext behindert Lesbarkeit | **P1 (Hoch)** |
| **M-06** | Barrierefreiheit | Global (alle Styles) | Sekundär- und Akzentfarben verfehlen WCAG AA (z. B. `#999` mit 2,85:1) | **P1 (Hoch)** |
| **M-07** | UX / Feedback | `Step3Simulation.vue:6-91` | Fehlende Zeitschätzung (ETA) und Statusführung bei 10–60 Min. Laufzeit | **P1 (Hoch)** |
| **M-08** | Wording | Alle Step-Komponenten | Schwer verständlicher Jargon („Ontologie“, „GraphRAG“, „Dualwelt“) | **P1 (Hoch)** |
| **M-09** | Layout (Mobil) | `MainView.vue:418-450` | App-Header-Elemente (Logo, Tabs, Steps) überlappen sich auf 412 px | **P1 (Hoch)** |
| **M-10** | UI / Ästhetik | `Home.vue:40, 692-698` | Rauten-Grafik (`.decoration-square`) steht isoliert als Fremdkörper | **P2 (Mittel)** |
| **M-11** | UI / Text | `Home.vue:18, 598-611` | Badge bricht unsauber um, Buzzword-Text | **P2 (Mittel)** |
| **M-13** | Ergonomie | `Home.vue:1166-1179` | Löschen-Button mit 24×24 px zu klein für Touch-Bedienung | **P2 (Mittel)** |
| **M-14** | Information | `Step1GraphBuild.vue:19, 123` | Exponierung roher interner API-Pfade (`POST /api/...`) an Endnutzer | **P2 (Mittel)** |
