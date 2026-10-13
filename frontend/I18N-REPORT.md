# I18N-Bericht

## Umfang

- `vue-i18n` 9.14.5 mit Composition API (`legacy: false`) eingebunden.
- Deutsch ist die Standardsprache; ohne gespeicherte Auswahl wird bei einer englischen Browsersprache Englisch, sonst Deutsch verwendet.
- Der Sprachumschalter `DE | EN` speichert die Auswahl unter `localStorage.lang` und aktualisiert das `lang`-Attribut des Dokuments.
- Alle 15 Vue-Dateien unter `src/views/` und `src/components/` wurden vollständig geprüft, einschließlich `Step2EnvSetup.vue` und `Step4Report.vue`.
- Beide Sprachdateien enthalten jeweils **705 Übersetzungsschlüssel**. Alle statisch referenzierten Schlüssel sind in beiden Sprachen vorhanden.

## Bewusst nicht übersetzte Stellen

- Produkt-, Anbieter- und Werkzeugnamen sowie technische Kennungen, zum Beispiel `MiroFish`, `OpenAI`, `Zep`, `GraphRAG`, `Twitter`, `Reddit`, Modellnamen und IDs.
- API-Pfade, Router-Namen, Feldnamen, Aktionscodes und Backend-Statuswerte, weil sie Teil der technischen Schnittstelle sind.
- Regex-Literale, Parser-Bezeichner und Sentinel-Texte in `Step4Report.vue`, insbesondere Varianten von `(Keine Antwort auf dieser Plattform)`. Eine Übersetzung würde die Erkennung bestehender Backend-Ausgaben beschädigen.
- An das Backend gesendete Prompt- und Verlaufspräfixe, sofern sie nicht selbst in der Oberfläche angezeigt werden.
- Kommentare, CSS-Selektoren und Schriftfamilien, da sie keine sichtbaren UI-Texte sind.

## Prüfung

- `npm ci` erfolgreich.
- `npx vite build` erfolgreich (685 Module transformiert).
- Templates gezielt nach unter anderem `Weiter`, `Zurück`, `wird`, `Fehler`, `Bericht` und `Simulation` durchsucht; verbleibende Treffer sind Übersetzungsschlüssel, Kommentare, technische Werte oder die oben dokumentierten Parser-Literale.
- Script-Blöcke aller Vue-Dateien zusätzlich syntaktisch geprüft.

## Offene Punkte

Keine funktionalen offenen Punkte. Vite meldet lediglich bestehende Hinweise zur gemischten statischen/dynamischen Einbindung von `pendingUpload.js` sowie zur Chunk-Größe; beide sind unabhängig von der Internationalisierung.
