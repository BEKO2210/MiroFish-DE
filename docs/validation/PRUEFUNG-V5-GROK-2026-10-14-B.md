
# Prüfung V5, zweiter Durchgang (14.10.2026)

Nur gelesen, nichts im Repo geändert.

## Freigabe für einen GPU-Piloten

**Nein.** Drei Punkte liegen auf dem kritischen Pfad: die Entscheidungsregel widerspricht dem Skript, die Kaltfrage sieht den Ordnernamen, und der Rechenrahmen ist offen. Ein Start bricht ab, vervierfacht die GPU-Zeit oder schreibt ein ungedecktes „bestanden“.

## Die neun Punkte

1. **Protokoll: Inhalt festgeschrieben, Rahmen nicht.** Acht Ordner, Primärsatz, bekannte Ausgänge, Primäranalyse 7, Sensitivität 4. `PROTOKOLL-V5.md:15-49`, `111-113`; `faelle/README.md:7-45`. GPU-Rahmen offen (`PROTOKOLL-V5.md:105-107`).
2. **Zweitkodierung nur zur Hälfte.** KI 8/8, Kappa 1,0, keine zweite Person (`PROTOKOLL-V5.md:55`; `zweitkodierung/uebersicht.md:6-14`). Die drei Lücken-Neins bleiben in der Primäranalyse.
3. **Kappa ohne Varianz: erledigt.** Konstante Reihen liefern `null` (`ensemble.py:282-284`). Nicht-numerisches Kappa ist nicht messbar (`validate_case.py:522-525`). Leere Paare bleiben 0,0 (`ensemble.py:275-276`).
4. **Abbruch bei `known: true`: erledigt. Laufprüfung ≠ Gemini-Prüfung.** Stopp vor `prepare_simulation` (`validate_case.py:869-879`). Freiburg startet nicht (`846-860`). Kein Bogen hat `Ort:`. Die Identität fällt auf den Ordnernamen (`216`); `known` ist das Oder beider Fragen (`276`).
5. **T0: erledigt.** Februar-2022-Sätze gestrichen (`freiburg-…/quellen.md:77-78`). T0-Tabellen auch bei Kehl (`61`) und Kuppenheim (`56-78`).
6. **336 Stunden: erledigt.** Default `--hours` 336 (`validate_case.py:828`, `896`), übernommen in die Laufkonfiguration (`ensemble.py:713`).
7. **Seed-Wiederholung und Resume: im Normalfall erledigt.** Drei Versuche (`ensemble.py:48`, `2647-2685`), Resume setzt Unvollständiges fort (`1569-1596`). Nach drei erschöpften Versuchen steigt der Zähler nicht; das Skript ruft Resume nur zweimal (`validate_case.py:27`, `395-398`).
8. **Eine Primärfrage, `in_material`, Polarität: erledigt.** Genau ein `primaer: true` (`validate_case.py:125-126`). Akte-Flag erzwingt nicht messbar (`520-524`). Wertung liest nur `polarity` (`ensemble.py:365-374`). Zu weite Fenster und der Sammel-Brier zählen nicht (`187-189`, `30`).
9. **S gegen P: erledigt.** Tafel und Abstand je Fall (`validate_case.py:458-475`), Mittelwert mit Fall-Bootstrap (`663-676`). Holm am Primärvergleich bleibt leer (`ensemble.py:2397-2405`).

Mitgeprüft: Arme S/D/P (`validate_case.py:21`). Trockenlauf: sieben Läufe, Freiburg ohne Start, 336 h, Takt 240, `c1` (`test_validate_case_dry.py:249-316`). Refresh-Fix `blind_feed.py:28-58`, Arm nicht im Piloten.

## Neue Probleme

Die Steigung wird erst ab acht gewerteten Fällen berechnet (`validate_case.py:641`). Bei sieben Fällen ist sie immer `null`. Das Protokoll verlangt sie für „bestanden“ in [0,5; 1,5] (`PROTOKOLL-V5.md:121-125`). Das Skript hängt den Status nur an Skill und Kappa (`638-662`, `788-791`).

Kappa ≥ 0,6 kann in `GESAMT` nicht scheitern: Fälle darunter verlassen die Stichprobe vor dem Minimum (`617-650`). Leer wird „nicht prüfbar“.

Ohne `--ort` gehen Slugs wie `kehl-tram-baumfaellungen-2017` in die Kaltfrage. Ein Ja stoppt vor der GPU. `VALIDIERUNG.md:319-320` behauptet, der Ort komme aus dem Bogen. Der Beispielbefehl setzt weder Takt noch Seeds (`315`); der Default-Takt ist 60 (`validate_case.py:833`, `897`).

Karlsfeld trägt weiter „10 bis 20 Millionen Euro“ und „rund 1 Million“ Defizit (`ausgangslage.md:10-11`). Die externe Bogenprüfung hat das nicht erkannt.

## Pilotrahmen RTX 3070

Tragfähig, sobald er vor dem Start im Protokoll steht und der Aufruf ihn erzwingt: 7 Fälle, S/D/P, 5 Seeds, 240 Minuten, 336 Stunden. Freiburg nicht starten.

`ROADMAP.md:41`: 24 Runden dauern 10–20 Minuten. 336 Stunden bei 240 Minuten sind 84 Runden (`run_parallel_simulation.py:1276`), Faktor 3,5. Arm S: 35 Seeds × 35–70 Minuten = 20–41 Stunden. D und P: 70 × 5–10 Minuten = 6–12 Stunden. Vorbereitung 4–11, Klassifikation 3–8. Summe 33–72 GPU-Stunden, Mitte rund 50. 48 Stunden liegen in der Mitte. Seriell etwa zwei bis drei Tage, ohne Wiederholungen. Default-Takt 60: allein Arm S 82–164 Stunden.

Der Pilot kann sagen, ob das Skill-Intervall S gegen D auf dieser Stichprobe (4 Ja, 3 Quellenlücken-Nein) ganz unter 0 liegt und ob der Abstand S gegen P von 0 weg liegt. Er kann zeigen, ob das Primärergebnis bei diesem Takt Varianz hat.

Er trägt keine Kalibrierung, keine repräsentative Quote, keine menschliche Interrater-Reliabilität und keine belegte Abwesenheit in den drei Lücken-Fällen. Fünf Seeds rastern jede Rate in Sechsteln. Ein Intervall über 0 bei sieben Fällen belegt den Schwarmbeitrag über die Rollenzerlegung nicht. Sensitivität n=4 ersetzt das nicht.
