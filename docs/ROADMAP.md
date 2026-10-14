# Roadmap v2 – „so gut, dass es jeder gern benutzt"

Stand 14.10.2026. Reihenfolge = Priorität. Jeder Punkt gilt erst als erledigt, wenn er auf dem Handy (412 px)
und auf dem Desktop per Screenshot geprüft ist, der Build grün ist und die Konsole leer bleibt.

| # | Thema | Inhalt | Prüfung | Wer |
|---|-------|--------|---------|-----|
| 1 | App-Gerüst | Ein Kopf (Logo, Navigation, Farben), ein Fußmenü mit drei echten Zielen: Start, Verlauf, Einstellungen. Keine „Oben"-Taste, keine Platzhalter-Ziele. | Jede Seite zeigt denselben Kopf; Fußmenü markiert die aktive Seite | Claude |
| 2 | Startseite | Hero mit lebendiger Schwarm-Grafik (Canvas, reagiert auf Berührung, respektiert reduced-motion), Formular als Hauptobjekt, „So funktioniert es" als vier Kacheln mit Symbolen statt nummerierter Pillen. Keine Entwickler-Sprache (kein „läuft auf deinem Rechner", kein „0 €", keine Modellnamen). | Screenshots 412/1280, keine Konsolenfehler | Claude |
| 3 | Verlauf | Eigene Seite `/history`: Liste mit Status-Chip (Läuft/Fertig/Abgebrochen), Titel = Frage, Datum, Runden; Aktionen Bericht/Export/Löschen mit Bestätigungsblatt. Keine IDs, keine Monospace-Schrift, keine Rauten. | Löschen und Export am Handy getestet | Claude |
| 4 | Einstellungen | Eigene Seite `/settings`: Modell, Gedächtnis, Verbindung prüfen, Farben, Sprache, Über. Fachbegriffe erklärt. | Speichern + Verbindung prüfen funktionieren | Claude |
| 5 | Durchlauf | `/run/:id` bleibt, Details ohne technische Präfixe, Agentenzahl, Restzeit, Abschlussbild mit Link zum Bericht. | Vollständiger Durchlauf im UI bis Bericht | Claude |
| 6 | Farben | Fehler „Voll" nicht wählbar beheben; Akzent folgt der bunteren Farbe; Umschalter im Kopf jeder Seite; auch Karten/Felder in Combo-Farben statt Weiß; Knopf „Originalfarben wiederherstellen“. | Alle 12 Vorgaben + Zufall in beiden Modi geprüft | Claude |
| 7 | Backend-Neustart | Nach Abschluss des laufenden Berichts: Dienst neu starten (DELETE/Export/Pipeline-Fixes live). `progress_percent` = Minimum beider Plattformen. | `curl -X DELETE` liefert 200/404 statt 405 | Claude |
| 8 | Expertenseiten | Schritt-für-Schritt-Seiten (Graph, Umgebung, Simulation, Bericht, Interview) entschlacken: kein „dringend empfohlen", keine Debug-Protokolle, keine englischen Reste („INFO PLAZA", „TOPIC COMMUNITY", „POST", „ACTS"), Touchziele ≥ 44 px, Kopf einheitlich. | Screenshots jeder Seite mobil | codex (Worktree) |
| 9 | Bericht | Lesetypografie (max. 70 Zeichen Zeile, Zwischenüberschriften), Teilen/Export, Interview-Dialog mobil. | Screenshot mobil/desktop | Claude |
| 10 | Zweisprachig | i18n-Zweig (codex, 705 Schlüssel) in main mergen, neue Seiten nachziehen, Umschalter in Einstellungen + Kopf. | DE/EN-Wechsel ohne Reload-Fehler | Claude |
| 11 | Erststart für Fremde | `README`: ein Befehl bis zur laufenden App (Docker Compose), Einrichtungsassistent wenn kein Modell erreichbar. | Frische Maschine, Docker, Ollama → Startseite „Bereit" | Claude |
| 13 | Modelle automatisch | Backend fragt den Modellserver (Ollama `/api/tags` + `/api/ps`, OpenAI-kompatibel `/v1/models`) ab; Einstellungen zeigen eine Auswahlliste statt Freitext; Statusanzeige oben zeigt das tatsächlich geladene Modell, nichts fest codiert. | Liste = `ollama list`; Kopf zeigt geladenes Modell | Claude |
| 14 | Neuerungen aus dem Original | 666ghj/MiroFish seit unserem Stand sichten (≈300 Commits), Fehlerkorrekturen und Sicherheitsupdates übernehmen, die zu unserem lokalen Betrieb passen. | Liste übernommen/verworfen in docs/UPSTREAM.md, Build + Durchlauf grün | Claude |
| 12 | QA + Veröffentlichung | Jede Seite mobil/desktop, hell + dunkle Combos, Cursor-Review, `git push` public ohne private Daten. | Review-Protokoll in docs/QA.md | Claude + Cursor |

Erledigt (v2, 13.10.): 1 App-Gerüst, 2 Startseite, 3 Verlauf, 4 Einstellungen, 6 Farben, 7 Backend-Neustart, 10 Zweisprachig.
In Arbeit: 8 Expertenseiten (codex, Zweig `expert`).

Erledigt (v1): Lesbarkeit, Design-Tokens, Durchlauf-API, Löschen/Export-API, Logo, Farbsystem-Grundlage, Startseite v2, Durchlauf-Ansicht.

## Validierung (ab 13.10.2026) – vom Szenariogenerator zur prüfbaren Prognose

Anlass: externe Bewertung des Musterstadt-Berichts (4,5/10; „plausibel, aber nicht validiert“). Befund im Code: der
Bericht beschreibt Woche 1–4, simuliert wurden 24 Stunden in einem einzigen Lauf mit 13 Agenten; keine Seeds.

| # | Stufe | Inhalt | Prüfung | Wer |
|---|-------|--------|---------|-----|
| V1 | Ehrlicher Bericht | Abschnitt „Methodik und Grenzen“ deterministisch aus den Daten (Agentenzahl, Profile, Runden, simulierte Stunden, Modelle, Läufe, Aktionen je Plattform); Berichtsagent darf nicht über den simulierten Zeitraum hinaus erzählen; kalibrierte Sprache („in diesem Lauf“, keine „Beweise“, Forderung ≠ Ereignis); Einzellauf heißt „Szenario“, nicht „Prognose“ | Bericht des Hallenbad-Laufs neu erzeugt, Methodik-Zahlen = Datenbank | codex/Cursor |
| V2 | Reproduzierbarkeit | Seeds für Simulation (Python/NumPy/Empfehlung) und Sprachmodell (`seed`, Temperatur), Lauf-Manifest (Hash der Dokumente und Frage, Modelle, Seeds, Konfiguration, Code-Stand), Ereignis-Log als CSV/JSONL im Export | gleicher Seed → gleiche Aktionen (bis auf Modell-Nichtdeterminismus, gemessen) | codex/Cursor |
| V3 | Mehrfachlauf | N Läufe (Standard 10) mit derselben Agentenvorbereitung und verschiedenen Seeds; Ergebnis-Checkliste aus der Frage (z. B. „Bürgerentscheid gefordert“, „Koalition A+B“) per festem Klassifikator je Lauf; Häufigkeiten mit 95-%-Wilson-Intervall im Bericht | 10 Läufe Hallenbad, Tabelle mit Intervallen | Cursor |
| V4 | Gegenproben | Ablationen (ohne Vernetzung/Empfehlungen, ohne gewählte Akteursgruppe), Sensitivität (Eingriffsstärke als Variable), Nullmodell (ein einzelnes Modell schreibt die Geschichte aus denselben Dokumenten, gleiche Checkliste) | Unterschiede mit Intervallen; Nullmodell als Vergleichszeile | Cursor/codex |
| V5 | Abgleich mit der Wirklichkeit | 3–5 dokumentierte reale Fälle (z. B. Parkgebühren, Bäderschließungen) mit Material VOR dem Ereignis blind simulieren, Ergebnis gegen den tatsächlichen Verlauf werten (Trefferquote, Kalibrierung) | Fallsammlung mit Quellen, Auswertung | codex (Recherche) + Claude |

Rechenbudget auf pop-os (RTX 3070): ein 24-Stunden-Lauf mit ~14 Agenten ≈ 10–20 Min ohne Bericht (Vorbereitung wird
im Mehrfachlauf wiederverwendet). 10 Läufe ≈ 2–3 h, Ablationen 3×10 über Nacht; 100 Läufe ≈ 1–2 Tage pro Szenario.

### Stand Validierung 13.10.2026 abends (historisch)
- V1 + V2 erledigt und live (Methodik und Grenzen, Vorgabe-Abgleich, Szenario-Titel, Seeds, Manifest, events.jsonl).
- V3/V4 Maschine und Oberfläche live; erster echter Mehrfachlauf `ens_9c4647555d4b` (neutrales Hallenbad-Szenario,
  10 × 24 h, Basis / ohne Vernetzung / Nullmodell) läuft über Nacht.
- Offen V3b: **eigene Ja/Nein-Fragen** beim Start des Mehrfachlaufs ergänzen (z. B. „Es wird zu einer
  Unterschriftensammlung oder einem Bürgerbegehren aufgerufen“), da die automatische Checkliste nur aus der Frage
  abgeleitet wird. Die eigenen Fragen werden ebenfalls auf „stand schon im Material“ geprüft.
- Offen V4b: Sensitivität (Eingriffsstärke als Variable im Szenario), V5 Realitätsabgleich.

### Lehren aus dem ersten Nachtlauf (13./14.10.2026)
- Fehler 1: Klassifikation aller Beiträge in einer Anfrage → über 16k Kontext abgeschnitten (isoliert 0/10). Behoben:
  Stapel, Prüfprotokoll classification.json, „unklassifiziert“ statt stillem Nein.
- Fehler 2: Wechselwirkung ohne strukturellen Beleg („Debatte“ in isolierten Läufen). Behoben: interaction-Ergebnisse
  brauchen Kommentar/Zitat/Antwort zwischen den Gruppen aus der Datenbank.
- Fehler 3: Abwesenheits-Ergebnis widersprüchlich abgefragt (Definition beschrieb das Ausbleiben). Behoben.
- Offen V3c **Zuverlässigkeit des Messinstruments:** dieselben Daten ergaben in zwei Auswertungen teils stark
  verschiedene Raten (z. B. 1/10 → 6/10). Neu: jede Klassifikation zweifach (zweiter Seed bzw. zweites Modell, z. B.
  qwen3.5:9b), Übereinstimmung und Cohens Kappa je Ergebnis; Ergebnisse mit Kappa < 0,6 gelten als „nicht messbar“ und
  werden im Bericht nicht interpretiert. Zusätzlich Stichprobe von Belegen zur menschlichen Prüfung in der Oberfläche.

### Stand Validierung 14.10.2026 (aktuell)

**Erledigt**
- Ablation `blind_feed` (Feed ohne Suche/Trend/Fremdinteraktion; Nutzung je Lauf in `run_stats` gemessen).
- Rundentakt wählbar (`minutes_per_round` 60/120/240, Teilbarkeitsregel gegen abgeschnittene Stunden).
- Ehrliche Statistik-Ansicht: gepaarter exakter McNemar-Test, Holm-Korrektur nur für explorative Vergleiche, ein
  Primärergebnis als konfirmatorisch, Newcombe-Intervall als Sensitivität, Kappa je Ergebnis.
- Docker-Fremdtest (Erststart auf fremder Maschine).
- V5-Vorregistrierung: 7 Fälle primär; Freiburg gilt vorab als kontaminiert und wird nicht primär gewertet
  (Protokoll: `docs/validation/PROTOKOLL-V5.md`).
- KI-Zweitkodierung (zweiter Bewerter je Klassifikation, konservatives Endurteil, Dissens = „strittig“).

**Offen**
- V5-GPU-Pilot: Rahmen noch festzulegen; Schätzung ca. 48 GPU-Stunden bei 4-h-Takt und 5 Seeds.
- Menschliche Zweitkodierung (Stichprobe der Belege durch Menschen, Übereinstimmung mit der KI-Kodierung).
- Mindestens 25 Fälle für eine konfirmatorische Aussage (bisher 7 primär, also Pilotcharakter).
- Weiter offen aus früheren Stufen: V4b Sensitivität (Eingriffsstärke als Variable).
