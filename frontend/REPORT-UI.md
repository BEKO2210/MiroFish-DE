# Bericht lesen

Änderungen an der Vorhersage-Ansicht (`Step4Report.vue`, `ReportView.vue`, neue Schlüssel in `de.json` / `en.json`).

- Lesespalte etwa 68 Zeichen, zentriert. Fließtext 17px auf dem Handy, 18px ab 1024px, Zeilenhöhe 1.7, Schrift `var(--font-body)`, Farbe `var(--color-text-primary)`. Überschriften in `var(--font-heading)`, Abstand davor größer als danach. Zeilen, die im Markdown nur fett sind, werden als Zwischenüberschrift gesetzt, ohne den Parser anzufassen. Absätze 1em. Listen eingerückt. Zitate und Agenten-Aussagen als Karte mit linker Linie `var(--color-brand-primary)`. Abschnittsnummern klein und gedämpft.
- Aufklapp-Pfeil der Abschnitte ist ein Button mit 44×44px.
- Werkzeugaufrufe, Agenten-Protokoll und Konsole liegen im zugeklappten Bereich „So entstand der Bericht“.
- Kopf: großer Titel, Zusammenfassung als Lead, darunter „Als Markdown herunterladen“ (`/api/report/<id>/download`) und „Drucken / PDF“ (`window.print()`).
- Druck: Navigation, Kopfzeile, Fußmenü, Knöpfe und Protokoll ausgeblendet. Text in den Farb-Tokens auf hellem Grund.
- Ab 1024px ein kleines Inhaltsverzeichnis, sticky neben dem Text. Ein Klick springt zum Abschnitt.
- Farben nur über die Variablen aus `tokens.css`. Parser, Lade-Logik und API-Aufrufe unverändert.
