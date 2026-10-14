/** Statische Leitfäden (docs/VERLAESSLICHKEIT.md / RELIABILITY.md), ohne Sprach-Querverweis. */

export const reliabilityMarkdown = {
  de: `# Wie verlässlich ist MiroFish?

Wenn in deiner Kommune ein Beschluss ansteht oder dein Verein vor einer schwierigen Entscheidung steht, willst du wissen: Wie reagieren die Menschen? MiroFish simuliert solche Debatten mit künstlichen Rollen (Agenten), die in einem digitalen Netzwerk Beiträge verfassen und aufeinander reagieren.

Doch wie verlässlich sind diese Berichte? Dieser Leitfaden erklärt dir ohne Werbesprache und ohne Fachjargon, was die Simulation leistet und wo ihre Grenzen liegen.

---

### 1. Einzellauf: Ein mögliches Szenario, keine Vorhersage

Startest du MiroFish mit einem einfachen Durchlauf, erhältst du das Ergebnis eines **Einzellaufs**. Das gleicht einer Theaterprobe mit Improvisation: Die Darsteller haben feste Rollen und ein Thema, doch wie sich das Gespräch entwickelt, hängt vom Zufall ab.

Ein einzelner Lauf zeigt **einen denkbaren Verlauf unter vielen**, ausdrücklich **keine Prognose**. Selbst wenn in diesem Durchlauf ein Streit eskaliert, ist das kein Beweis dafür, dass dies in der Wirklichkeit geschieht – oder dass ein zweiter Durchlauf zum selben Ergebnis käme.

### 2. Mehrfachlauf: Häufigkeiten mit Schwankungsbereich

Um Zufallstreffer von stabilen Mustern zu unterscheiden, nutzt MiroFish den **Mehrfachlauf** (Ensemble). Dabei wiederholt das System dieselbe Simulation mehrfach – etwa zehnmal – mit identischen Rollen, aber neuen Zufallswerten.

Das Ergebnis ist keine starre Prozentzahl, sondern eine **Spanne** (ein statistischer Schwankungsbereich). Zählen wir in 7 von 10 Läufen den Ruf nach einem Bürgerentscheid, lautet das Ergebnis nicht „70 Prozent sicher“, sondern beispielsweise „zwischen 39 und 89 Prozent“. Diese Spanne verhindert falsche Gewissheit und zeigt ehrlich, wie breit die Ergebnisse bei wenigen Läufen noch streuen.

### 3. Die drei Vergleichsarten: Was treibt die Dynamik an?

Damit du erkennst, ob eine Entwicklung wirklich durch gegenseitiges Aufschaukeln entsteht, vergleicht MiroFish drei Varianten:

1. **Volle Simulation:** Alle virtuellen Akteure lesen Beiträge, folgen einander und reagieren aufeinander. Das bildet eine vernetzte Online-Debatte ab.
2. **Ohne Vernetzung (isoliert):** Die Figuren behalten ihre Rollen, können aber nur eigene Beiträge verfassen. Sie sehen keine Beiträge anderer und können auf niemanden reagieren. Tritt ein Ereignis auch hier auf, lag es nicht an der Gruppendynamik, sondern war bereits in den Rollenbeschreibungen angelegt.
3. **Einzelnes Sprachmodell (Nullmodell):** Hier gibt es weder Agenten noch ein Netzwerk. Ein einzelnes Sprachmodell liest deine Texte und schreibt eine fortlaufende Erzählung. Das zeigt, ob die aufwendige Simulation echten Mehrwert bringt oder nur Standardmuster wiederholt, die ein einzelnes Modell ohnehin parat hat.

### 4. Der Vorgabe-Abgleich: „Stand schon im Material“

Oft wird gefeiert, wenn eine Simulation ein Detail „treffend vorhersieht“ – etwa die Drohung mit einer Klage. Häufig stand dieser Punkt jedoch bereits im Text, den du hochgeladen hast.

MiroFish führt deshalb einen automatischen **Vorgabe-Abgleich** durch. Es gleicht die Kernaussagen des Berichts mit deinen Eingabedokumenten ab. Erkennt das System eine inhaltliche Übereinstimmung, markiert es das Ergebnis ehrlich: *„Stand schon im Ausgangsmaterial“*. So wird verhindert, dass eine bloße Wiederholung deiner Vorlage als neue Erkenntnis missverstanden wird.

### 5. Doppelte Prüfung: Warum der Auswerter kontrolliert wird

Am Ende müssen viele simulierte Beiträge ausgewertet werden. Ein Sprachmodell prüft dafür anhand einer Checkliste, ob bestimmte Ereignisse eingetreten sind.

Weil auch Auswerte-Modelle Fehler machen, prüft MiroFish jedes Ergebnis **doppelt** – mit zwei verschiedenen Durchläufen oder Modellen. Zudem gilt ein „Ja“ nur, wenn das Modell einen konkreten Beitragsbeleg im Datenprotokoll nachweisen kann. Weichen die beiden Prüfungen deutlich voneinander ab, stuft MiroFish das Ergebnis als **„nicht messbar“** ein. Das System sortiert unsichere Urteile aus, statt Scheingenauigkeit vorzutäuschen.

### 6. Was MiroFish ausdrücklich NICHT kann

MiroFish liefert **keine Wahrscheinlichkeiten für die reale Welt**.

Die Zahlen spiegeln wider, wie oft Sprachmodelle in einer geschützten digitalen Umgebung bestimmte Aussagen treffen. Echte Menschen handeln nach komplexen persönlichen Erfahrungen, wirtschaftlichen Zwängen und Emotionen, die kein Modell vollständig erfasst. Solange ein wissenschaftlicher Abgleich mit realen, historischen Fällen fehlt, darfst du ein Simulationsergebnis niemals als Eintrittswahrscheinlichkeit für die Wirklichkeit interpretieren.

### 7. Gute Fragen und neutrale Ausgangsdokumente

Eine Simulation ist immer nur so gut wie das Material, mit dem du sie fütterst. Suggestive Vorgaben verzerren das Ergebnis unvermeidlich:

* **Schlechtes Beispiel:**
  * *Material:* Ein polemischer Leserbrief über „Abzocke bei Parkgebühren“.
  * *Frage:* „Wann eskaliert der Protest gegen die unverschämten Gebühren?“
  * *Folge:* Die Frage erzwingt Streit. Die Simulation spiegelt lediglich deine Voreingenommenheit wider.
* **Gutes Beispiel:**
  * *Material:* Der sachliche Beschlussentwurf der Verwaltung mit Gegenargumenten von Handel und Anwohnern.
  * *Frage:* „Welche Argumente und Reaktionen äußern Gewerbetreibende, Pendler und Anwohner in den ersten 48 Stunden nach Veröffentlichung?“
  * *Folge:* Die Figuren können das breite Meinungsspektrum unvoreingenommen abbilden.

---

### Checkliste: Bevor du ein Ergebnis weitergibst

Prüfe diese fünf Punkte, bevor du Ergebnisse an Dritte, die Presse oder Gremien weiterreichst:

- [ ] **Neutrale Vorlage:** War dein Ausgangsmaterial sachlich und enthielt verschiedene Perspektiven?
- [ ] **Laufart benannt:** Machst du klar, ob es sich um ein einzelnes Szenario (Einzellauf) oder Häufigkeiten (Mehrfachlauf) handelt?
- [ ] **Keine Prognose-Sprache:** Verwendest du Formulierungen wie „mögliches Szenario in einer Simulation“ statt „Vorhersage für die Realität“?
- [ ] **Vorgaben geprüft:** Hast du beachtet, welche Ergebnisse bereits wörtlich in deiner Textvorlage standen?
- [ ] **Schwankungsbreite genannt:** Gibst du bei Mehrfachläufen die Spanne (z. B. 40 bis 90 Prozent) anstelle einer trügerischen Einzelzahl an?
`,

  en: `# How reliable is MiroFish?

When your municipality is facing a council decision or your community group has a tough choice to make, you want to know: How will people react? MiroFish simulates debates like these using artificial personas (agents) that post messages and interact with one another in a digital network.

But how reliable are these reports? Free of marketing hype and technical jargon, this guide explains what the simulation can deliver—and where its limits lie.

---

### 1. Single run: One possible scenario, not a forecast

If you start MiroFish with a basic run, you get the result of a **single run**. This is like an improv theater rehearsal: the actors have defined roles and a topic, but how the conversation unfolds depends on chance.

A single run shows **one plausible path among many**, and explicitly **not a forecast**. Even if an argument escalates in this run, that does not prove it would happen in the real world—or that a second run would produce the same outcome.

### 2. Ensemble run: Frequencies with a margin of uncertainty

To tell random flukes apart from consistent patterns, MiroFish uses an **ensemble run** (multiple runs). The system repeats the exact same simulation several times—say, ten times—with identical personas but fresh random seeds.

The result is not a rigid percentage, but a **range** (a statistical confidence interval). If we see calls for a local referendum in 7 out of 10 runs, the result isn't "70 percent certain," but rather something like "between 39 and 89 percent." This range prevents false certainty and honestly reflects just how widely results can vary with only a few runs.

### 3. The three comparison modes: What drives the dynamics?

To help you see whether a dynamic genuinely emerges from agents reacting to each other, MiroFish compares three variants:

1. **Full simulation:** All virtual agents read posts, follow each other, and react to one another. This mirrors a connected online debate.
2. **Without networking (isolated):** The personas keep their assigned roles, but can only author their own posts. They cannot see posts from others and cannot reply to anyone. If an event still occurs here, it was not driven by group dynamics, but was already baked into the role descriptions.
3. **Single language model (null model):** Here, there are neither agents nor a network. A single language model reads your documents and writes a continuous narrative. This shows whether the elaborate multi-agent simulation adds real value or simply repeats baseline patterns that a single model generates anyway.

### 4. Baseline check: "Already in source material"

People often celebrate when a simulation "accurately predicts" a detail—such as the threat of a lawsuit. Often, however, that point was already stated directly in the text you uploaded.

That is why MiroFish performs an automatic **baseline check**. It compares the key findings of the report against your input documents. If the system detects matching content, it flags the result honestly: *"Already present in source material"*. This keeps a simple echo of your prompt from being mistaken for a new insight.

### 5. Double verification: Why the evaluator is checked

At the end of a run, many simulated posts need to be evaluated. A language model uses a checklist to check whether specific events occurred.

Because evaluator models also make mistakes, MiroFish checks every result **twice**—using two separate runs or models. Furthermore, an event only counts as "Yes" if the model can cite concrete evidence from the message log. If the two reviews disagree substantially, MiroFish flags the result as **"unmeasurable"**. The system filters out uncertain judgments rather than faking false precision.

### 6. What MiroFish explicitly CANNOT do

MiroFish provides **no real-world probabilities**.

The numbers reflect how often language models make certain statements in a sandboxed digital environment. Real people act on complex personal experiences, economic constraints, and emotions that no model captures completely. Without scientific validation against real, historical cases, you must never interpret simulation results as real-world likelihoods.

### 7. Good prompts and balanced source documents

A simulation is only ever as good as the material you feed it. Leading or biased inputs will inevitably distort the results:

* **Poor example:**
  * *Material:* A polemical letter to the editor about "parking fee rip-offs."
  * *Question:* "When will protests escalate against these outrageous fees?"
  * *Consequence:* The question forces conflict. The simulation merely mirrors your own bias.
* **Good example:**
  * *Material:* An objective administrative proposal including counterarguments from local businesses and residents.
  * *Question:* "What arguments and reactions do shop owners, commuters, and residents voice in the first 48 hours after publication?"
  * *Consequence:* The personas can represent a broad, balanced spectrum of opinions.

---

### Checklist: Before sharing your results

Review these five points before passing results on to third parties, the press, or committees:

- [ ] **Neutral source material:** Was your input document balanced and did it include different perspectives?
- [ ] **Run type identified:** Have you made it clear whether this is an individual scenario (single run) or frequencies (ensemble run)?
- [ ] **No predictive language:** Are you using phrasing like "possible scenario in a simulation" rather than "real-world forecast"?
- [ ] **Checked against sources:** Have you noted which results were already mentioned verbatim in your source text?
- [ ] **Range reported:** For ensemble runs, are you citing the range (e.g., 40 to 90 percent) instead of a misleading single number?
`,
}
