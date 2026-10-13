# UX-Report: Wissensgraph & Schritt 1 (Feinschliff)

## Änderungen

### `GraphPanel.vue`
- Titel über `graph.wissensgraph` (i18n: Wissensgraph / Knowledge graph); Schlüssel `graph.graphBeziehungsvisualisierung` ebenfalls auf diese Texte gesetzt.
- Legende: Überschrift „Arten von Akteuren“ in `var(--color-text-secondary)`; auf allen Viewports einklappbar per Knopf „Legende“ (Desktop standardmäßig offen, Handy zu).
- Werkzeugleiste (Aktualisieren, Vollbild, Kanten-Schalter) in einer Zeile rechts im Panel-Kopf; Touchziele ≥ 44 px; am Handy unter dem Titel umbrechbar.
- Knotenbeschriftungen: `forceCollide`-Radius aus Textlänge; Halo mit `paint-order: stroke` und Strich `var(--color-bg-canvas)`; Labels bei Zoom < 0.6 ausgeblendet außer am ausgewählten Knoten.
- Fallback-Typ in der Legende: `graph.entity` → „Akteur“ / „Actor“.

### i18n (`de.json` / `en.json`)
- `step1.generierteEntitatstypen` / `generierteBeziehungstypen`: normale Schreibung („Arten von Akteuren/Beziehungen“, EN „Kinds of …“).
- `step1.basierendAufDerGeneriertenOntologieWerdenDokumente`: neuer Kurztext (Gedächtnis der Agenten).
- `graph.graphBeziehungsvisualisierung`: „Wissensgraph“ / „Knowledge graph“.

### `Step1GraphBuild.vue`
- Karte 03: Abzeichen bei `currentPhase >= 2` zeigt „Abgeschlossen“ (`common.completed`) in Erfolgsfarbe (`badge success`) statt „In Bearbeitung“.

## Abnahme
1. `cd frontend && npx vite build` — OK.
2. `cd e2e && npx playwright test` — Suite grün; visuelle Snapshots für `/process/proj_6fde53d0e82a` (handy/tablet/desktop) aktualisiert und geprüft.
3. Kein Eintrag in `e2e/BEFUNDE.md` betroffen (keine `test.fail()`-Entfernung nötig).
