# How reliable is MiroFish?

*Deutsch: [VERLAESSLICHKEIT.md](VERLAESSLICHKEIT.md)*

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

At the end of a run, hundreds of simulated posts need to be evaluated. A language model uses a checklist to check whether specific events occurred.

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
