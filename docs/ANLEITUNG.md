# Anleitung: MiroFish für Gemeinderat, Verein und Bürgerinitiative

*English: [GUIDE.md](GUIDE.md)*

Diese Anleitung ist für Menschen gedacht, die keine Technik-Profis sind: Du sitzt im Gemeinderat, leitest einen Verein oder engagierst dich in einer Bürgerinitiative und willst vor einer Entscheidung durchspielen, wie Menschen reagieren könnten. Du brauchst dafür keine Vorkenntnisse. Die Einrichtung der Software steht in der [README](../README.md); hier geht es um die **Benutzung**.

---

## 1. Wofür MiroFish taugt – und wofür nicht

MiroFish lässt viele künstliche Rollen (Agenten) in einem digitalen Netzwerk über dein Thema diskutieren. Du lädst Dokumente hoch, stellst eine Frage und bekommst einen Bericht darüber, wie die Debatte verlaufen *könnte*.

**Es taugt dazu,**

- Argumente und Reaktionen verschiedener Gruppen zu sammeln, an die du selbst nicht gedacht hast,
- eine Entscheidung oder Ankündigung vorab „durchzuspielen“ und Schwachstellen zu finden,
- im Gremium eine Diskussion anzustoßen („Was wäre, wenn …?“),
- Rückfragen an simulierte Rollen zu stellen und so Blickwinkel zu verstehen.

**Es taugt nicht dazu,**

- die Zukunft vorherzusagen. Ein Bericht ist **keine Prognose**,
- Wahrscheinlichkeiten für die Wirklichkeit zu liefern („70 Prozent der Bürger sind dagegen“). Die Zahlen beschreiben nur, wie sich die Simulation verhält, nicht, wie echte Menschen handeln,
- Umfragen, Bürgerbeteiligung oder Gespräche mit echten Menschen zu ersetzen,
- ein „Ergebnis“ zu belegen, das du schon vorher glaubst. Wer suggestives Material hineingibt, bekommt es verstärkt zurück.

Die ausführliche, ehrliche Erklärung steht in [VERLAESSLICHKEIT.md](VERLAESSLICHKEIT.md). In der App findest du sie auch unter **Wie verlässlich ist das?**

![Der Leitfaden „Wie verlässlich ist das?“ in der App](../static/image/Screenshot/handy-leitfaden.png)

---

## 2. Gutes Ausgangsmaterial vorbereiten

Die Simulation ist nur so gut wie das, was du hochlädst. Die App liest PDF-, Markdown- und Textdateien.

**Ausgewogen sein.** Nimm sachliche Texte: den Beschlussentwurf, das Sitzungsprotokoll, einen Zeitungsbericht, die Stellungnahme der Verwaltung. Meide polemische Leserbriefe oder Flugblätter als einzige Quelle.

**Mehrere Sichtweisen abbilden.** Ist nur eine Seite im Material vertreten, kommt die Simulation fast zwangsläufig bei dieser Seite an. Lege also auch Argumente der Gegenseite bei: Handel *und* Anwohner, Verwaltung *und* Bürgerinitiative, Befürworter *und* Kritiker.

**Keine vertraulichen Daten.** Lade keine nicht-öffentlichen Protokolle, keine Namen von Privatpersonen, keine Adresslisten und keine Mitgliederdaten hoch. Prüfe vorher, ob du das Dokument auch öffentlich zeigen würdest. Wenn du ein Sprachmodell eines Cloud-Anbieters (etwa OpenAI) nutzt, verlassen die Texte deinen Rechner. Mehr dazu findest du unter **Einstellungen**.

**Nicht zu viel, nicht zu wenig.** Ein paar gut gewählte Seiten schlagen einen Aktenberg. Je mehr Material, desto länger dauert alles.

---

## 3. Eine gute Frage formulieren

Auf der Startseite gibst du bei **Deine Frage** an, was du wissen willst. Eine gute Frage hat:

- einen **konkreten Zeitraum** („in den ersten vier Wochen“, „in den ersten 48 Stunden“),
- **beobachtbare Reaktionen** – etwas, das man in Beiträgen lesen könnte (Argumente, Forderungen, Unterschriftensammlung, Beschwerden),
- **bestimmte Gruppen** („Anwohner, Einzelhandel, Pendler“),
- **keine Wertung** in der Formulierung.

| | Beispiel | Warum |
|---|---|---|
| ✅ gut | „Wie reagieren Anwohner und Einzelhandel in den ersten vier Wochen auf die neuen Parkgebühren?“ | Zeitraum, Gruppen und Reaktionen sind klar, die Frage ist neutral. |
| ✅ gut | „Welche Argumente äußern Gewerbetreibende, Pendler und Anwohner in den ersten 48 Stunden nach Veröffentlichung des Beschlusses?“ | Beobachtbar und breit angelegt. |
| ❌ schlecht | „Wann eskaliert der Protest gegen die unverschämten Gebühren?“ | Setzt Eskalation voraus und wertet. |
| ❌ schlecht | „Wird der Verein die Wahl gewinnen?“ | Das ist eine Prognose – dafür ist MiroFish nicht gebaut. |
| ❌ schlecht | „Was denken die Leute?“ | Kein Zeitraum, keine Gruppen, nichts Konkretes. |

---

## 4. Der Ablauf in fünf Schritten

Auf der Startseite klickst du auf **Neue Simulation**, lädst Dokumente hoch, schreibst deine Frage und drückst **Simulation starten**. Bleibt **Bis zum Bericht durchlaufen** eingeschaltet, laufen alle Schritte von allein. Du kannst die Seite schließen; unter **Verlauf** findest du alles wieder. Wer jeden Schritt selbst steuern will, wählt **Schritt für Schritt starten**.

![Die Startseite mit Dokumenten und Frage](../static/image/Screenshot/desktop-start.png)

Die Dauer hängt stark von Rechner, Sprachmodell und Textmenge ab. Als grobe Größenordnung auf einem normalen Rechner mit Grafikkarte: **gut eine halbe Stunde** für ein kurzes Dokument und eine simulierte Woche. Auf einem Rechner ohne Grafikkarte oder bei vielen Unterlagen kann es mehrere Stunden dauern. Ein Mehrfachlauf (siehe unten) dauert ein Vielfaches davon.

| Schritt | Name in der App | Was passiert (Alltagssprache) | Dauer (grob) |
|---|---|---|---|
| 1 | **Wissensgraph** | MiroFish liest deine Dokumente, legt fest, welche Rollen und Beziehungen vorkommen („Rollen und Beziehungen festlegen“) und baut daraus eine Art Landkarte: Wer ist wer, wer kennt wen? | wenige Minuten |
| 2 | **Agenten vorbereiten** | Zu jeder Rolle entsteht eine Person mit Lebenslauf, Haltung und Verhalten. | einige Minuten |
| 3 | **Simulation** | Die Personen schreiben Beiträge auf einem „Nachrichtenplatz“ und in einem „Themenforum“, lesen und antworten einander – über die simulierten Tage. | der längste Teil, oft 15 Minuten bis mehrere Stunden |
| 4 | **Bericht** | Ein Berichts-Agent wertet alle Beiträge aus und schreibt einen Bericht. | einige Minuten |
| 5 | **Nachfragen stellen** | Du kannst dem Bericht und den simulierten Personen Fragen stellen. | beliebig, nach Lust |

---

## 5. Den Bericht lesen

![Ein Bericht auf dem Desktop](../static/image/Screenshot/desktop-bericht.png)

**Ein Einzellauf ist ein denkbarer Verlauf.** Der Bericht beschreibt *eine* Simulation. Sie ist wie eine Theaterprobe mit Improvisation: Ein zweiter Durchgang wäre etwas anders verlaufen. Im Bericht steht deshalb „Szenario aus 1 Lauf“. Nutze Formulierungen wie „in der Simulation zeigte sich …“ und nicht „es wird passieren, dass …“.

**Der Abschnitt „Methodik und Grenzen“.** Im Bericht (siehe auch **So entstand der Bericht**) steht, wie der Bericht zustande kam: Zahl der Läufe, Zahl und Arten der Agenten, simulierte Zeit, Zahl der Beiträge und Kommentare, die verwendeten Sprachmodelle und der Zeitpunkt. Wirf dort immer einen Blick hin. Er zeigt dir auch gleich den wichtigsten Satz: *Ein einzelner Lauf zeigt einen möglichen Verlauf, keine Wahrscheinlichkeit.*

**Der Vorgabe-Abgleich: „Stand schon im Material“.** Manchmal wirkt ein Ergebnis wie eine kluge Voraussicht – dabei stand es schon in deinen Dokumenten. MiroFish vergleicht die Kernaussagen des Berichts mit deinem Ausgangsmaterial. Trifft das zu, steht dort **Stand schon im Material** (mit **Fundstelle anzeigen**). Das ist keine neue Erkenntnis, sondern eine Wiederholung. Im Inhaltsverzeichnis des Berichts heißt der Abschnitt **Vorgabe-Abgleich**.

**Zitate und Namen sind erfunden.** Die Personen existieren nicht. Gib ihre Aussagen nie als echte Zitate weiter.

---

## 6. Wann ein Mehrfachlauf sinnvoll ist

Ein Einzellauf zeigt nur einen Verlauf. Willst du wissen, ob etwas **öfter** vorkommt oder nur ein Zufallstreffer war, nutze den **Mehrfachlauf**: MiroFish wiederholt dieselbe Simulation mehrmals mit neuem Zufall. Das ist sinnvoll,

- wenn du dich auf ein Ergebnis stützen oder es im Gremium vorstellen willst,
- wenn der Einzellauf etwas Auffälliges zeigt (etwa eine Eskalation) und du wissen willst, ob das stabil ist,
- wenn du fragen willst: Entsteht das durch die Gruppendynamik – oder hätte es auch ohne sie so kommen können?

Er kostet aber viel Zeit (ein Vielfaches des Einzellaufs). Für ein erstes Kennenlernen reicht ein Einzellauf.

**So startest du ihn:** Öffne den fertigen Bericht und wähle **Mehrfachlauf starten**. Dort stellst du die **Anzahl Läufe**, die **Dauer je Lauf (Stunden)** und die **Vergleichsvarianten** ein. Unter **Eigene Fragen (optional)** kannst du ein Ereignis in Alltagssprache formulieren, das man in den Beiträgen erkennen kann, zum Beispiel „Es wird zu einer Unterschriftensammlung aufgerufen“. Die **Geschätzte Dauer** wird dir vor dem Start angezeigt.

Die wichtigsten Vergleichsvarianten:

- **Basis (immer dabei):** die volle Simulation mit allen Wechselwirkungen.
- **Ohne Vernetzung:** Die Personen sehen die Beiträge der anderen nicht. Tritt etwas auch hier auf, lag es nicht an der Gruppendynamik.
- **Ein einzelnes Sprachmodell (Nullmodell):** Hier schreibt nur ein Sprachmodell eine Geschichte – ohne Agenten. So siehst du, ob die aufwendige Simulation überhaupt etwas Neues zeigt.

### Zusammenfassung und Spannen lesen

In den Ergebnissen steht zum Beispiel: **„7 von 10 Läufen · Spanne 39–89 %“**.

- **„7 von 10 Läufen“** heißt: In 7 von 10 Simulationsdurchgängen kam das Ereignis vor.
- **Die Spanne** (Schwankungsbereich) zeigt, wie unsicher diese Zahl bei so wenigen Läufen ist. Sie ist **breit**, wenn du wenige Läufe hast. Das ist ehrlich so, kein Fehler.
- Nenne nie nur „70 Prozent“, sondern immer **„7 von 10 Läufen, Spanne 39–89 %“**.
- **Das sind keine Wahrscheinlichkeiten für die Wirklichkeit**, sondern nur Anteile der Läufe dieser Simulation.
- In der **Hauptfrage** sagt dir ein Satz, ob sich Simulation und Vergleichsvarianten unterscheiden. Steht dort „kein klarer Unterschied“, hat die Gruppendynamik nichts Besonderes beigetragen.
- **„nicht messbar“** oder **„Auswerter uneinig – Zahl nicht deuten“** bedeutet: Die beiden automatischen Prüfungen kamen zu unterschiedlichen Urteilen. Lies die Zahl dann nicht als Ergebnis.
- **„Stand schon im Material“** gilt auch hier: Das Ergebnis kam schon aus deinen Dokumenten.
- **Zusatzbeobachtungen (explorativ)** sind nur Hinweise, **nicht als Beleg verwenden**.

---

## 7. Nachfragen stellen

Im fünften Schritt, **Nachfragen stellen**, kannst du im Gespräch tiefer gehen:

- **Chat mit dem Berichts-Agenten:** Er beantwortet Fragen zum Bericht („Warum haben die Anwohner so reagiert?“) und recherchiert dafür in den Daten.
- **Mit einer beliebigen Person der Welt chatten:** Wähle eine simulierte Person und frage nach ihrer Haltung. Das ist hilfreich, um Blickwinkel zu verstehen.
- **Umfrage an simulierte Personen senden:** Du schickst dieselbe Frage an mehrere Personen auf einmal und siehst die Antworten nebeneinander.

Wichtig: Die Antworten kommen von **simulierten Rollen**. Das ist Anschauung und Ideengeber, keine Meinungsumfrage. Gib Antworten nicht als „so denken die Bürger“ weiter.

---

## 8. Ergebnisse weitergeben: die Checkliste

Bevor du etwas an Gremium, Mitglieder, Presse oder Öffentlichkeit weitergibst:

- [ ] **Neutrale Vorlage:** War dein Ausgangsmaterial sachlich und enthielt verschiedene Perspektiven?
- [ ] **Laufart benannt:** Machst du klar, ob es ein einzelnes Szenario (Einzellauf) oder Häufigkeiten (Mehrfachlauf) sind?
- [ ] **Keine Prognose-Sprache:** Schreibst du „mögliches Szenario in einer Simulation“ statt „Vorhersage für die Realität“?
- [ ] **Vorgaben geprüft:** Hast du beachtet, was schon wörtlich in deinem Material stand („Stand schon im Material“)?
- [ ] **Schwankungsbreite genannt:** Gibst du bei Mehrfachläufen die Spanne an (z. B. „7 von 10 Läufen, Spanne 39–89 %“) statt einer Einzelzahl?

Hilfreich zusätzlich: Nenne die Frage, das Material und das Datum. Gib an, dass die Personen und ihre Zitate erfunden sind. Und: Dein Ergebnis ersetzt keine Beteiligung echter Menschen.

---

## 9. Alte Läufe wiederfinden und aufräumen

Unter **Verlauf** siehst du alle bisherigen Simulationen mit Bericht und **Export** (alles als ZIP). Mit **Löschen** entfernst du eine Simulation samt Bericht und Daten dauerhaft. Das ist wichtig, wenn du sicher gehen willst, dass nichts liegen bleibt.

![Der Verlauf früherer Läufe](../static/image/Screenshot/handy-verlauf.png)
