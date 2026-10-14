
# Freigabeprüfung V5, dritter Durchgang (14.10.2026)

Nur gelesen, Stand `main` `fc3dfba`. Nichts im Repo geändert. Pytest nicht ausgeführt.

## Entscheidung

**(a) Probelauf mit synthetischem Fall: ja.** **(b) Pilot: nein.**

Der Probelauf kann kein „bestanden“ schreiben: `build_summary` setzt den Status fest auf „Probelauf, nicht gewertet“ (`validate_case.py:1057-1059`). Fall `docs/validation/probe`, 2 Seeds, nicht in den 7 `case_ids`. Vorher `.env` wie `.env.example` (Provider `ollama`, drei Modelle). Im Repo liegt keine `.env`; ohne sie ist der Provider `openai` und die Modellprüfung im Dienst entfällt (`ensemble.py:1441-1442`, `config.py:41`).

Der Pilot bleibt zu. Drei Messfehler können das Urteil verfälschen. Keiner öffnet ein ungedecktes „bestanden“. Zwei schreiben ein falsches „nicht bestanden“, einer lässt einen leeren Schwarm in die Rate.

## F1–F14

| # | Stand | Beleg |
|---|---|---|
| F1 | zu | Stapelausfall setzt `unclassified` (`ensemble.py:2227-2233`, `2445-2449`). Gesamtausfall wirft (`2386-2387`, `2542-2543`). Resume verwirft solche Seeds (`2852-2858`). Zeile in `GESAMT`: `3154`. |
| F2 | zu | Gewertet nur bei exakt den 7 Rahmenfällen (`validate_case.py:934-945`). Sonst „nicht prüfbar“, außer Skill(S,D) liegt ganz unter 0: das ist so protokolliert (`PROTOKOLL-V5.md:155`). |
| F3 | zu | Bestanden nur wenn beide Skill-Intervalle ganz über 0 liegen (`906-910`, `927-929`). Der Abstand der Ja-Anteile ist Bericht, nicht Kriterium. Wortlaut gleich Protokoll `149-156`. |
| F4 | zu | Fremde JSON scheitern an `_frame_rejection` (`1006-1016`). Eine Datei je Fallname. `ensemble_ids` in `GESAMT` (`1067-1068`). |
| F5 | zu | GET und HTTP 5xx, Backoff 30 min (`validate_case.py:95`, `155-172`). Treiber: 4 Versuche (`run_pilot_v5.py:145-179`). |
| F6 | zu, Rest | Vor dem Versuch `/api/tags`, bis 30 min (`ensemble.py:60`, `1493-1506`). Ausfall zählt den Versuch zurück (`3051-3062`). Flattern hält die Schleife offen. `attempts_exhausted`: manueller Reset (`PROTOKOLL-V5.md:180`). |
| F7 | weitgehend zu | Freitext, beide Modelle, Prompt gespeichert (`validate_case.py:337-340`, `430-433`, `1275-1280`). Ordnername verboten (`1277`). Gescannt werden `text_de` und `quelle`, nicht `quellen.md` (`376-381`; Protokoll `:46`). Die Zahl `14` aus der versteckten Frage ist ein starker Treffer (`390-399`) und kann den Probelauf sperren. |
| F8 | zu | `text_model` und `arm_model` gleich Agentenmodell (`validate_case.py:560-565`). Der Integrationstest prüft `arm_models` (`test_pilot_integration.py:332-334`). |
| F9 | weitgehend zu | `strict_second_rater`, kein Fallback (`ensemble.py:1708-1709`, `2361-2362`). Mindestens 4 von 5 (`validate_case.py:761-763`). Die 10-%-Stichprobe steht im Kodierbuch (`PROTOKOLL-V5.md:61`), nicht in den vier Bedingungen. Verschiedene Modellnamen prüft der Code nicht. |
| F10 | offen | `min_posts` Standard 1, Quote über 0,5 verwirft (`ensemble.py:59`, `2874-2888`). Ohne `actions.jsonl` ist die Quote 0 (`1059-1067`). `_terminate_owned_orphan` braucht `current` (`1837-1841`); `mark_stale_runs` löscht es (`1910`). Der OASIS-Prozess überlebt. `sweep_orphans` löscht Daten, keine PIDs (`cleanup.py:478`). |
| F11 | zu | Treiber 40 GB (`run_pilot_v5.py:23`, `69-71`). Dienst bricht unter 5 GiB ab (`ensemble.py:58`, `1508-1514`). |
| F12 | zu | Proberahmen, Status erzwungen. Degeneriertes Kappa ist `null` (`ensemble.py:291-293`) und damit „nicht prüfbar“. Leere Paare bleiben 0,0 (`284-285`), siehe N1. |
| F13 | zu | `blind_feed` aus dem Protokoll (`PROTOKOLL-V5.md:107`). Rahmenarme nur S, D und P. |
| F14 | Rest | Karlsfeld trägt Größenordnungen, keine Exaktbeträge (`ausgangslage.md:10-13`). Ob das 12B-Modell den Fall daraus kennt, prüft erst die Kaltfrage beim Start. |

## Punkte aus dem zweiten Durchgang

Die Steigung ist kein Bestehenskriterium mehr (`PROTOKOLL-V5.md:156`; Prüfung nur ab 25 Fällen, `validate_case.py:931-933`). Kappa unter 0,6 setzt „Instrument unzuverlässig“, bevor die Fallmenge geprüft wird (`949-950`). Ohne `kaltfrage_ort` bricht der Lauf ab; der Slug geht nicht ans Modell (`311-334`). JSON und Skript sind gleichgezogen (`1315-1318`). Freiburg hat `kontaminiert` und fehlt in `case_ids`.

## Neue Punkte, deshalb kein Pilot

**N1.** Keine Bewerterpaare ergeben Kappa 0,0 (`ensemble.py:284-285`). Fehlt die Primärfrage in jeder Antwort und der Rest ist klassifiziert, bleibt der Seed gültig. `GESAMT` wertet das als Instrumentversagen (`validate_case.py:879-882`, `949-950`). Das Protokoll will dafür „nicht prüfbar“ (`PROTOKOLL-V5.md:155-156`).

**N2.** Nach SIGKILL setzt der Neustart den Lauf auf fehlgeschlagen und löscht `current`. Der Waisenprozess wird nicht beendet. Resume startet den Seed neu, die GPU bleibt doppelt belegt.

**N3.** Ein Basislauf ohne Aktionslog und mit einem Beitrag besteht das Qualitätstor. Die Klassifikation sieht fast nur Leere und tendiert zu Nein. Das geht in die Rate ein, sobald Kappa Varianz hat.

Vor dem Pilot: N1 leere Paare als `kappa: null`. N3 ohne Aktionslog den Seed wiederholen. N2 die PID aus `run_state.json` auch nach gelöschtem `current` beenden.

Der Probelauf zeigt Varianz und die Kaltfrage. Bricht sie wegen „14“ ab, stehen Prompt und Antwort im State.
