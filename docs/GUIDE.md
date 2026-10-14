# Guide: MiroFish for town councils, clubs and citizens' initiatives

*Deutsch: [ANLEITUNG.md](ANLEITUNG.md)*

This guide is for people who are not tech professionals: you sit on a town council, run a club or are active in a citizens' initiative, and you want to play through how people might react before a decision is made. No prior knowledge needed. Installation is covered in the [README](../README-EN.md); this guide is about **using** the app. Button and menu names are quoted as they appear in the English interface.

---

## 1. What MiroFish is good for – and what it is not

MiroFish lets many artificial roles (agents) discuss your topic in a digital network. You upload documents, ask a question and get a report on how the debate *could* unfold.

**It is good for**

- collecting arguments and reactions of different groups that you had not thought of,
- rehearsing a decision or announcement in advance and spotting weak points,
- starting a discussion in a committee ("What if …?"),
- asking simulated roles follow-up questions to understand viewpoints.

**It is not good for**

- predicting the future. A report is **not a forecast**,
- giving real-world probabilities ("70 percent of residents are against it"). The numbers only describe how the simulation behaves, not how real people act,
- replacing surveys, public participation or conversations with real people,
- proving a "result" you already believe. Leading material comes back amplified.

The full, honest explanation is in [RELIABILITY.md](RELIABILITY.md). In the app, it is the **How reliable is this?** link.

![The guide "How reliable is it?" inside the app (German interface)](../static/image/Screenshot/handy-leitfaden.png)

---

## 2. Prepare good source material

The simulation is only as good as what you upload. The app reads PDF, Markdown and text files.

**Be balanced.** Use factual texts: the draft resolution, meeting minutes, a newspaper report, the administration's statement. Avoid polemical letters or flyers as the only source.

**Include several viewpoints.** If only one side is in the material, the simulation almost inevitably ends up on that side. Add the counter-arguments: retailers *and* residents, administration *and* initiative, supporters *and* critics.

**No confidential data.** Do not upload non-public minutes, names of private persons, address lists or member data. Ask yourself whether you would be comfortable showing the document publicly. If you use a cloud language model (e.g. OpenAI), your texts leave your computer. See **Settings** for details.

**Not too much, not too little.** A few well-chosen pages beat a pile of files. The more material, the longer everything takes.

---

## 3. Phrase a good question

On the start page you enter what you want to know under **Your question**. A good question has

- a **specific time frame** ("in the first four weeks", "in the first 48 hours"),
- **observable reactions** – something that could be read in posts (arguments, demands, a petition, complaints),
- **named groups** ("residents, retailers, commuters"),
- **no judgement** built into the wording.

| | Example | Why |
|---|---|---|
| ✅ good | "How do residents and retailers react in the first four weeks to the new parking fees?" | Time frame, groups and reactions are clear; neutral. |
| ✅ good | "Which arguments do business owners, commuters and residents voice in the first 48 hours after the resolution is published?" | Observable and broad. |
| ❌ bad | "When will the protest against the outrageous fees escalate?" | Presumes escalation and judges. |
| ❌ bad | "Will our club win the election?" | That is a forecast – MiroFish is not built for it. |
| ❌ bad | "What do people think?" | No time frame, no groups, nothing concrete. |

---

## 4. The five steps

On the start page click **New simulation**, upload documents, type your question and press **Start simulation**. If **Run through to the report** stays switched on, all steps run by themselves. You may close the page; everything can be found again under **History**. If you want to control each step yourself, choose **Start step by step**.

![The start page with documents and question (German interface)](../static/image/Screenshot/desktop-start.png)

Duration depends heavily on computer, language model and amount of text. As a rough order of magnitude on an ordinary computer with a graphics card: **a good half hour** for a short document and one simulated week. Without a graphics card or with lots of material it can take several hours. A multi-run (see below) takes many times longer.

| Step | Name in the app | What happens (plain language) | Duration (rough) |
|---|---|---|---|
| 1 | **Knowledge graph** | MiroFish reads your documents, decides which roles and relationships appear and builds a kind of map: who is who, who knows whom? | a few minutes |
| 2 | **Prepare agents** | Each role becomes a person with a background, attitude and behaviour. | some minutes |
| 3 | **Simulation** | The people write posts in a "News feed" and a "Topic forum", read and answer each other – over the simulated days. | the longest part, often 15 minutes to several hours |
| 4 | **Report** | A report agent evaluates all posts and writes a report. | some minutes |
| 5 | **Ask follow-up questions** | You can put questions to the report and to the simulated people. | as long as you like |

---

## 5. Reading the report

![A report on the desktop (German interface)](../static/image/Screenshot/desktop-bericht.png)

**A single run is one conceivable course of events.** The report describes *one* simulation. It is like a theatre rehearsal with improvisation: a second go would turn out a little differently. That is why the report says "Scenario from 1 run". Use wording like "in the simulation, … appeared" rather than "it will happen that …".

**The "Methods and limits" section.** The report (see also **How this report was made**) tells you how it came about: number of runs, number and types of agents, simulated time, number of posts and comments, the language models used and the time. Always take a look. It also shows the most important sentence: *A single run shows one possible trajectory, not a probability.*

**The source check: "Already present in source material".** Sometimes a result looks like clever foresight – yet it was already in your documents. MiroFish compares the key statements of the report with your source material. If they match, the report says **Already present in source material** (with **Show passage**). That is not a new insight but a repetition. In the report's table of contents this section is called **Source check**.

**Quotes and names are invented.** The people do not exist. Never pass their statements on as real quotes.

---

## 6. When a multi-run makes sense

A single run only shows one course of events. If you want to know whether something happens **often** or was a fluke, use the **multi-run**: MiroFish repeats the same simulation several times with fresh randomness. It makes sense

- if you want to rely on a result or present it to a committee,
- if the single run shows something striking (e.g. an escalation) and you want to know whether it is stable,
- if you want to ask: does this come from group dynamics – or could it have happened without them?

It takes much longer, though. For a first look, a single run is enough.

**How to start it:** open the finished report and choose **Start multi-run**. There you set the **Number of runs**, the **Hours per run** and the **Comparison variants**. Under **Your questions (optional)** you can phrase an event in everyday language that could be recognised in the posts, for example "A petition is called for". The **Estimated time** is shown before you start.

The most important comparison variants:

- **Baseline (always included):** the full simulation with all interaction.
- **No networking:** people cannot see each other's posts. If something happens here too, it was not caused by group dynamics.
- **A single language model (null model):** one language model simply writes a story – no agents. It shows whether the elaborate simulation shows anything new at all.

### Reading the summary and ranges

The results say something like **"7 of 10 runs · range 39–89%"**.

- **"7 of 10 runs"** means: in 7 of 10 simulation runs the event occurred.
- **The range** shows how uncertain this figure is with so few runs. It is **wide** with few runs. That is honest, not a bug.
- Never quote just "70 percent"; always say **"7 of 10 runs, range 39–89%"**.
- **These are not real-world probabilities**, only shares of the runs of this simulation.
- In the **main question**, one sentence tells you whether simulation and comparison variants differ. If it says there is no clear difference, group dynamics added nothing special.
- **"not measurable"** or **"Raters disagree – do not interpret this figure"** means: the two automatic checks reached different verdicts. Do not read the figure as a result.
- **"Already in the source material"** applies here too: the result came from your documents.
- **Additional observations (exploratory)** are only hints – **do not use as evidence**.

---

## 7. Ask follow-up questions

In the fifth step, **Ask follow-up questions**, you can dig deeper in conversation:

- **Chat with report agent:** it answers questions about the report ("Why did residents react like this?") and researches the data for it.
- **Chat with anyone in the world:** choose a simulated person and ask about their stance. This helps to understand viewpoints.
- **Send a survey to simulated people:** you send the same question to several people at once and see the answers side by side.

Important: the answers come from **simulated roles**. They are illustration and food for thought, not an opinion poll. Do not pass them on as "this is what residents think".

---

## 8. Sharing results: the checklist

Before you pass anything on to a committee, members, the press or the public:

- [ ] **Neutral material:** Was your source material factual and did it contain different perspectives?
- [ ] **Run type named:** Do you make clear whether it is a single scenario (single run) or frequencies (multi-run)?
- [ ] **No forecast language:** Do you write "possible scenario in a simulation" rather than "forecast for reality"?
- [ ] **Source check done:** Did you take into account what was already literally in your material ("Already present in source material")?
- [ ] **Range stated:** For multi-runs, do you give the range (e.g. "7 of 10 runs, range 39–89%") instead of a single figure?

Also helpful: state the question, the material and the date. Say that the people and their quotes are invented. And: your result does not replace the participation of real people.

---

## 9. Finding old runs and cleaning up

Under **History** you see all past simulations with their report and **Export** (everything as a ZIP). **Delete** removes a simulation with its report and data permanently. That is useful if you want to be sure nothing is left behind.

![History of earlier runs (German interface)](../static/image/Screenshot/handy-verlauf.png)
