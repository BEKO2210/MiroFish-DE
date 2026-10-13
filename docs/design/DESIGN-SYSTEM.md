# Design-System: MiroFish „Editorial Clarity“

**Version:** 1.0.0  
**Datum:** 13. Oktober 2026  
**Fokus:** Mobil zuerst (412 px), barrierefrei (WCAG 2.1 AA), verständlich für Nicht-Entwickler  
**Sprachen:** Deutsch & Englisch  

---

## 1. Design-Richtung & Philosophie

### Name: „Editorial Clarity“ (Redaktionelle Klarheit)
MiroFish richtet sich an Fachleute aus **Journalismus, Kommunalverwaltung, Marketing und Wissenschaft**. Diese Nutzer suchen keine Programmierumgebung und kein futuristisches Science-Fiction-Dashboard, sondern ein vertrauenswürdiges, methodisch fundiertes Analysewerkzeug.

### Die vier Kernprinzipien:
1. **Redaktionelle Ruhe statt visueller Lärm:** Klare Schriften, großzügiger Weißraum, keine isolierten Schmuckelemente (wie gedrehte Rauten) ohne funktionalen Zweck.
2. **Mobil gleichwertig, nicht abgespeckt:** Jeder Kernschritt – vom Dokumenten-Upload über die Statusüberwachung bis zum Lesen des Berichts – muss auf einem 412 px Smartphone einhändig bedienbar sein.
3. **Transparenz ohne Fachchinesisch:** Die Software erklärt verständlich, was sie tut („Dokumente werden ausgewertet“ statt „Ontologie-Generierung & GraphRAG-Vektorisierung“).
4. **Verlässliche Orientierung bei langen Laufzeiten:** Läufe zwischen 10 und 60 Minuten erfordern beruhigende, transparente Fortschrittskommunikation mit klaren Phasen, Zeitangaben und Hintergrund-Garantie.

---

## 2. Typografie

Das System nutzt die bereits im Projekt geladenen Schriften `Inter` und `Space Grotesk`. Die Monospace-Schrift `JetBrains Mono` wird strikt auf technische Kennungen, Dateiendungen und Tabellenzahlen beschränkt.

### Schriftfamilien
- **Fließtext & UI:** `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`  
  *Einsatz:* Fließtexte, Buttons, Navigation, Formulare, Erklärungen, Ergebnisberichte. Extrem hohe Lesbarkeit, offene Punzen, hervorragende Ziffern.
- **Akzente & Überschriften:** `Space Grotesk, -apple-system, BlinkMacSystemFont, sans-serif`  
  *Einsatz:* Hero-Titel, Abschnitts-Überschriften (H1–H3), Schritt-Titel, Markenname. Verleiht redaktionelle Schärfe und Autorität ohne Verspieltheit.
- **Code & Datenwerte (isoliert):** `JetBrains Mono, SFMono-Regular, monospace`  
  *Einsatz:* UUIDs, Dateinamen (`beschluss.pdf`), Zählerstände (`12/48`), Rundenangaben.

### Typografische Hierarchie & Responsive Maßstab

| Rolle | Desktop (ab 1024 px) | Mobil (412 px) | Zeilenhöhe | Schnitt | Schriftart |
|---|---|---|---|---|---|
| **Display** | 40 px (2.5rem) | 26 px (1.625rem) | 1.2 | Bold (700) | `Space Grotesk` |
| **H1** | 32 px (2.0rem) | 22 px (1.375rem) | 1.25 | Bold (700) | `Space Grotesk` |
| **H2** | 24 px (1.5rem) | 18 px (1.125rem) | 1.3 | SemiBold (600) | `Space Grotesk` |
| **H3** | 18 px (1.125rem) | 16 px (1.0rem) | 1.35 | SemiBold (600) | `Space Grotesk` |
| **Body Large** | 18 px (1.125rem) | 16 px (1.0rem) | 1.6 | Regular (400) | `Inter` |
| **Body Base** | 16 px (1.0rem) | 15 px (0.9375rem)| 1.55 | Regular (400) | `Inter` |
| **Body Small** | 14 px (0.875rem) | 13 px (0.8125rem)| 1.5 | Regular (400) / Medium (500) | `Inter` |
| **Caption / Meta**| 12 px (0.75rem) | 12 px (0.75rem) | 1.4 | Medium (500) | `Inter` |
| **Tabular Data** | 14 px (0.875rem) | 13 px (0.8125rem)| 1.4 | Medium (500) | `JetBrains Mono` |

---

## 3. Farbpalette & Nachgerechnete WCAG-AA-Kontraste

Alle Farben wurden mathematisch auf Basis der relativen Leuchtdichte ($L$) berechnet ($CR = (L_1 + 0.05) / (L_2 + 0.05)$).  
**WCAG 2.1 AA Kriterien:** Mindestens **4,5 : 1** für normalen Text (<18 pt bzw. <24 px), mindestens **3,0 : 1** für großen Text und UI-Bedienelemente.

### 3.1 Helles Design (Light Mode - Standard)

| Token | Hex-Wert | Hintergrund-Kombination | Rechnerischer Kontrast | WCAG-AA-Bewertung |
|---|---|---|---|---|
| `--color-bg-canvas` | `#FFFFFF` | Basis | – | – |
| `--color-bg-surface` | `#F8FAFC` | Auf Canvas | – | Zarte Trennung |
| `--color-bg-surface-raised`| `#FFFFFF` | Auf Surface (Card) | – | Schattenbasiert |
| `--color-text-primary` | `#0F172A` | Auf `#FFFFFF` | **16,21 : 1** | **PASS (AAA)** |
| `--color-text-secondary` | `#334155` | Auf `#FFFFFF` | **11,10 : 1** | **PASS (AAA)** |
| `--color-text-muted` | `#64748B` | Auf `#FFFFFF` | **4,62 : 1** | **PASS (AA normal)** |
| `--color-border-subtle` | `#E2E8F0` | Auf `#FFFFFF` | 1,25 : 1 | Rein dekorativ |
| `--color-border-strong` | `#94A3B8` | Auf `#FFFFFF` | **3,02 : 1** | **PASS (AA UI-Element)** |
| `--color-brand-primary` | `#C2410C` | Auf `#FFFFFF` | **5,18 : 1** | **PASS (AA normal)** |
| `--color-brand-on-primary` | `#FFFFFF` | Auf `#C2410C` (Button) | **5,18 : 1** | **PASS (AA normal)** |
| `--color-brand-hover` | `#9A3412` | Auf `#FFFFFF` | **7,31 : 1** | **PASS (AAA)** |
| `--color-success-text` | `#15803D` | Auf `#FFFFFF` | **5,02 : 1** | **PASS (AA normal)** |
| `--color-success-bg` | `#F0FDF4` | Auf Surface | – | Beruhigend |
| `--color-error-text` | `#B91C1C` | Auf `#FFFFFF` | **6,47 : 1** | **PASS (AA normal)** |
| `--color-error-bg` | `#FEF2F2` | Auf Surface | – | Warnend |
| `--color-info-text` | `#1D4ED8` | Auf `#FFFFFF` | **6,70 : 1** | **PASS (AA normal)** |
| `--color-focus-ring` | `#C2410C` | 3 px Outline + 2 px Offset | **5,18 : 1** | Perfekt sichtbar |

> [!NOTE]
> Das alte knallige Orange (`#FF5722`) erreichte lediglich 3,16:1 und scheiterte an WCAG AA. Das neue Terrakotta-Orange (`#C2410C`) behält die warme Identität der Marke bei, übertrifft mit **5,18 : 1** aber sicher die gesetzliche Schwelle für barrierefreien Text und kontrastreiche Buttons.

### 3.2 Dunkles Design (Dark Mode - `[data-theme="dark"]`)

| Token | Hex-Wert | Hintergrund-Kombination | Rechnerischer Kontrast | WCAG-AA-Bewertung |
|---|---|---|---|---|
| `--color-bg-canvas` | `#0B0F17` | Basis | – | Tiefer Kontrast |
| `--color-bg-surface` | `#111827` | Auf Canvas | – | Weiche Schichtung |
| `--color-bg-surface-raised`| `#1F2937` | Auf Surface (Card) | – | 1,5 : 1 Differenz |
| `--color-text-primary` | `#F8FAFC` | Auf `#111827` | **16,98 : 1** | **PASS (AAA)** |
| `--color-text-secondary` | `#E2E8F0` | Auf `#111827` | **13,42 : 1** | **PASS (AAA)** |
| `--color-text-muted` | `#94A3B8` | Auf `#111827` | **6,61 : 1** | **PASS (AA normal)** |
| `--color-border-subtle` | `#1E293B` | Auf `#111827` | – | Trennung |
| `--color-border-strong` | `#475569` | Auf `#111827` | **3,15 : 1** | **PASS (AA UI-Element)** |
| `--color-brand-primary` | `#FB923C` | Auf `#111827` | **7,84 : 1** | **PASS (AAA)** |
| `--color-brand-on-primary` | `#0F172A` | Auf `#FB923C` (Button) | **7,84 : 1** | **PASS (AAA)** |
| `--color-success-text` | `#4ADE80` | Auf `#111827` | **10,18 : 1** | **PASS (AAA)** |
| `--color-error-text` | `#F87171` | Auf `#111827` | **6,41 : 1** | **PASS (AA normal)** |
| `--color-info-text` | `#60A5FA` | Auf `#111827` | **6,98 : 1** | **PASS (AA normal)** |

---

## 4. Abstands- und Rastersystem

Das Spacing basiert auf einem durchgängigen **8-Pixel-Raster** mit halber 4-Pixel-Stufe für feine Ausrichtungen.

### Abstandstoken
- `--space-1`: `4px` (Feinabstand, Badge-Polsterung innen)
- `--space-2`: `8px` (Icon-Abstand, Listen-Lücken)
- `--space-3`: `12px` (Kompakte Card-Innenabstände mobil)
- `--space-4`: `16px` (Standard-Padding mobil, Formularlücken)
- `--space-5`: `20px` (Card-Padding mobil)
- `--space-6`: `24px` (Card-Padding desktop, Sektionsabstand mobil)
- `--space-8`: `32px` (Sektionsabstand desktop)
- `--space-10`: `40px` (Große Abstände)
- `--space-12`: `48px` (Layout-Blöcke)
- `--space-16`: `64px` (Hero-Abstand desktop)

### Ergonomie auf Mobilgeräten (412 px)
- **Container-Innenabstand:** Genau **16 px** links und rechts. Auf einem 412 px Gerät ergibt dies einen nutzbaren Inhaltsbereich von **380 px**.
- **Touch-Target-Mindestmaß:** Gemäß WCAG 2.5.5 beträgt die Mindestgröße aller interaktiven Elemente (Buttons, Links, Checkboxen, File-Upload-Triggern) **44 × 44 px**.

---

## 5. Komponenten-Spezifikationen

### 5.1 Buttons (Schaltflächen)
- **Höhe:** Standard `44 px` (mobil), `40 px` (desktop kompakt).
- **Varianten:**
  1. **Primary Button:** Hintergrund `--color-brand-primary` (`#C2410C`), Text weiß (`#FFFFFF`), Schriftgewicht 600, Border-Radius `8px`. Mobil mit `width: 100%`.
  2. **Secondary Button:** Hintergrund `--color-bg-surface`, Rand 1px solid `--color-border-strong`, Text `--color-text-primary`.
  3. **Ghost / Link Button:** Kein Hintergrund, Text `--color-brand-primary`, unterstrichen bei Fokus/Hover.
  4. **Destructive Button:** Text `--color-error-text`, Hintergrund zart `--color-error-bg`.
- **Fokus-Zustand:** `outline: 2px solid var(--color-brand-primary); outline-offset: 2px;` bei `:focus-visible`.

### 5.2 Karten (Cards)
- **Projekt- und Verlaufs-Karten (`HistoryDatabase.vue`):**
  - **Mobil (unter 768 px):** Reines vertikales Scroll-Raster (`display: grid; grid-template-columns: 1fr; gap: 16px;`). Keine fächerförmigen JavaScript-Transformationen!
  - **Desktop (ab 1024 px):** Automatisch responsives Grid (`grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));`).
  - **Aufbau der Karte:**
    1. Header: Datum (`12. Okt 2026`) + Status-Pille (`Abgeschlossen` / `In Bearbeitung`).
    2. Titel: Fragestellung des Nutzers in 2–3 Zeilen (lesbar, `Inter SemiBold`, kein Monospace).
    3. Metadaten: Dateiname (`strategie.pdf`) mit Dokumenten-Icon.
    4. Footer: Direkte Aktions-Schaltfläche („Bericht lesen →“).

### 5.3 Formulare & Eingaben
- **Prompt-Eingabefeld (Fragestellung):**
  - Textarea erhält `min-height: 120px; font-family: var(--font-body); padding: 14px 16px;`.
  - **Badge-Entflechtung:** Das Engine-Badge („Modell: MiroFish V1“) wird **nicht mehr absolut in das Textfeld gelegt**. Es wandert in eine diskrete Statuszeile *unterhalb* oder *oberhalb* des Eingabefeldes:
    ```
    [ Label: Deine Frage an die Simulation                      ]
    [ Textarea: Wie reagiert die Öffentlichkeit auf ...         ]
    [ Statusleiste: Zeichen: 142 | Berechnungsmodell: Standard  ]
    ```
- **Datei-Upload-Zone:**
  - Mobil als vollwertige Touch-Fläche mit klarem Button: „Datei auswählen (PDF, Word, Text)“.
  - Nach Auswahl: Liste der Dateien mit klarem Dateinamen, Größe und einem **44 × 44 px** Entfernen-Button (`✕`).

### 5.4 Langzeit-Statusanzeige (für Läufe von Minuten bis 1 Stunde)
Bei Laufzeiten von bis zu 60 Minuten bricht die Geduld von Nutzern ohne transparente Rückmeldung zusammen.

#### Aufbau der Langzeit-Statuskomponente:
1. **Drei verständliche Phasen:**
   - *Phase 1:* Dokumente & Zusammenhänge erfassen (ca. 1–3 Min.)
   - *Phase 2:* Meinungsdynamik der Gruppen simulieren (ca. 10–45 Min.)
   - *Phase 3:* Analysebericht formulieren (ca. 2–4 Min.)
2. **Aktive Herzschlag-Visualisierung:**
   - Ein sanft pulsierender Fortschritts-Ring (kein nervöser Spinner).
   - Anzeige der **verstrichenen Zeit** (`14 Min. vergangen`) und einer **geschätzten Restzeit** (`ca. 10–15 Min. verbleibend`).
3. **Die „Hintergrund-Garantie“ (Beruhigung):**
   - Fester Hinweistext:  
     > *„Du kannst diesen Browser-Tab schließen oder das Smartphone weglegen. Die Simulation läuft zuverlässig auf unserem Server weiter. Wenn du später zurückkehrst, liegt dein fertiger Bericht bereit.“*
4. **Browser-Benachrichtigung (Opt-in):**
   - Ein-Klick-Button: `[ 🔔 Benachrichtigen, wenn fertig ]` (nutzt die HTML5 Notification API).

### 5.5 Schritt-Anzeige (Workflow Stepper)
- **Mobil (unter 768 px):**
  - Feste obere Statusleiste mit Fortschrittsbalken (z. B. 40 % bei Schritt 2).
  - Textformat: `Schritt 2 von 5: Akteure & Gruppen`.
- **Desktop:**
  - Vollständige horizontale 5-Stufen-Leiste:  
    `1. Dokumente` ➔ `2. Akteure` ➔ `3. Simulation` ➔ `4. Bericht` ➔ `5. Vertiefung`.

---

## 6. Sparsame Bewegung & Barrierefreie Animation

- **Animationsdauer:** Max. `180 ms` für Hover/Fokus, max. `250 ms` für Modals und Aufklappelemente.
- **Timing-Funktion:** `cubic-bezier(0.16, 1, 0.3, 1)` (flüssiges Abbremsen, kein Springen).
- **Reduzierte Bewegung (`prefers-reduced-motion`):**
  ```css
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
      scroll-behavior: auto !important;
    }
  }
  ```

---

## 7. Sprache, Tonalität & Übersetzungsmatrix (DE / EN)

### Tonalitäts-Richtlinien:
- **Ziel:** Konstruktiv, sachlich, auf Augenhöhe, respektvoll gegenüber der Zeit des Nutzers.
- **Vermeide Entwickler-Jargon:**
  - *Nein:* „Ontologie generieren“, „Zep GraphRAG Vektorisierung“, „Realitäts-Samen extrahieren“, „Gott-Perspektive“, „Dualwelt-Simulation“.
  - *Ja:* „Themenstruktur aufbauen“, „Wissensbasis verknüpfen“, „Ausgangsdaten erfassen“, „Szenario-Parameter festlegen“, „Social-Media-Diskussion simulieren“.

### Zweisprachige UI-Begriffe im Vergleich

| Kontext / Element | Alter Jargon-Text (DE) | Neuer Standard (Deutsch) | Neuer Standard (English) |
|---|---|---|---|
| **Hero-Tag** | Elegante universelle Schwarm-Intelligenz-Engine | Szenario-Simulation für fundierte Entscheidungen | Scenario simulation for informed decisions |
| **Hero-Überschrift** | Lade beliebigen Bericht hoch / Erkenne die Zukunft sofort | Dokumente verstehen. Reaktionen voraussehen. | Understand documents. Anticipate reactions. |
| **Schritt 1** | Ontologie-Generierung / GraphRAG-Aufbau | 1. Dokumente & Themen analysieren | 1. Analyze Documents & Topics |
| **Schritt 2** | Umgebungsaufbau / Entitäts-Extraktion | 2. Akteure & Gruppen vorbereiten | 2. Prepare Agents & Groups |
| **Schritt 3** | Duale Plattform-Parallel-Simulation | 3. Diskussionsverlauf simulieren | 3. Simulate Discussion Dynamics |
| **Schritt 4** | Berichtsgenerierung via ReportAgent | 4. Analysebericht erstellen | 4. Generate Analysis Report |
| **Schritt 5** | Tiefe Interaktion / Dialog mit Individuen | 5. Nachfragen & Vertiefen | 5. In-Depth Query & Follow-up |
| **Start-Button** | Engine starten / Initialisiere... | Simulation starten | Start Simulation |
| **Warte-Status** | Warten auf Ontologie-Generierung | Analyse wird vorbereitet... | Preparing analysis... |
| **Laufzeit-Status** | Parallele Dual-Simulation läuft | Simulation läuft (Schritt 2 von 3) | Simulation in progress (Step 2 of 3) |
| **Zeitangabe** | ROUND 14/40 • ACTS 182 | 14 von 40 Runden abgeschlossen | 14 of 40 rounds completed |
| **Historie-Header**| SIMULATIONSAUFZEICHNUNGEN | Gespeicherte Analysen | Saved Analyses |
| **Aktion Historie**| Wiedergabe im historischen Kontext | Bericht öffnen | Open Report |
| **Fehlermeldung** | Error 500: Task failed in Graph pipeline | Die Analyse konnte nicht abgeschlossen werden. Bitte prüfe deine Eingabedatei. | The analysis could not be completed. Please check your source file. |
