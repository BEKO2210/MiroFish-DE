# UX-Audit 2 – Umsetzung Codex

- `StepHeaderCompact.vue` und die spezifikationsgetreue `MobileStickyBar.vue` ergänzt; alle Schrittansichten zeigen mobil eine kompakte Fortschrittsanzeige, eine zweigliedrige Graph/Arbeitsbereich-Umschaltung und sichere Primäraktionen über dem Fußmenü.
- `GraphPanel.vue` auf `ResizeObserver`, automatisches Fit-to-View, Touch-Pan/Pinch-Zoom und maximal 300 Simulationsticks umgestellt. Kopfzeile, Statushinweise, Beschriftungen, Detail-Sheet, Akteurslegende und Punktraster wurden responsiv und tokenbasiert überarbeitet.
- Die Schrittseiten nutzen am Desktop die 50/50-Aufteilung Wissensgraph links und Arbeitsbereich rechts; der Nachfragen-Arbeitsbereich wurde für diese Breite optimiert. Mobil wird immer nur eine Ansicht gezeigt.
- Die mobilen Primäraktionen für Wissensgraph, Umgebung, Simulation, Bericht und Nachfragen wurden in feste Daumenzonen-Leisten verlegt; die entsprechenden E2E-Befunde und erwarteten Fehler für Prozess, Simulation und Interaktion wurden entfernt.
- Deutsche und englische i18n-Texte sowie die beabsichtigt geänderten Playwright-Snapshots wurden aktualisiert und visuell geprüft.
