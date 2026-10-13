# Roadmap „MiroFish wie eine App“ (Stand 13.10.2026)

Ziel: Am Handy wie eine native App, am Desktop vollwertig, deutsch und englisch, ohne Fachjargon, ohne Cloud.
Abnahme pro Punkt: Screenshot 412 px + 1280 px, keine Konsolenfehler, `npx vite build` grün, Funktion live geprüft.

| # | Thema | Wer | Status |
|---|---|---|---|
| P0 | Lesbarkeit: Dunkelmodus-Token zerstörte Kontrast (weißer Text auf Weiß) | Claude | erledigt |
| P1 | Startseite neu: Kopf, Erklärung in 3 Schritten, eine Karte „Neue Vorhersage“ (Datei, Frage, Start), Verlauf darunter; Marketingfloskeln raus | Claude | offen |
| P2 | Automatischer Durchlauf im UI: Schalter „bis zum Bericht“, Fortschrittsseite `/run/<id>` mit Stufen, Detail, Zeitschätzung, Link zum Bericht | Claude | offen |
| P3 | Schrittseiten (Prozess, Simulation, Lauf, Bericht, Interaktion): einspaltig mobil, Kopfzeile kompakt, Entwicklerinfos ausgeblendet, Tippflächen ≥ 44 px | Claude | teilweise |
| P4 | Bericht: Typografie, Export (ZIP/Markdown), Teilen | Claude | Export erledigt |
| P5 | Zweisprachigkeit DE/EN mit Umschalter | codex (Branch `i18n`) | läuft |
| P6 | Eigenes Logo (Bildmarke, Wortmarke, Favicon, OG-Bild) | codex | läuft |
| P7 | Texte ohne Jargon (Ontologie, GraphRAG, Dualwelt …) | Claude + grok-Texte | offen |
| P8 | Dunkelmodus bewusst (Komponenten mit Token-Hintergründen), erst wenn alle Seiten auf Token sind | Claude | später |
| P9 | Desktop-Feinschliff: Maximalbreiten, Zwei-Spalten nur wo sinnvoll | Claude | offen |
| P10 | QA-Durchlauf: jede Seite mobil + desktop, kompletter Lauf aus dem UI, Löschen/Export getestet, Review durch Cursor | Claude + Cursor | offen |
| P11 | README/API-Doku, öffentliche Version ohne private Daten gepusht | Claude | API-Doku erledigt |
