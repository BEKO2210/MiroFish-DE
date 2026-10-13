# Aufräumen

Gelöscht wird nur unter dem Upload-Ordner (`backend/uploads`, `Config.UPLOAD_FOLDER`). Kennungen müssen zum Muster passen (`proj_` und `sim_` und `run_` mit Hex-Zeichen, `report_` mit Buchstaben und Ziffern, Graph-Ordner als UUID). Vor jedem `rmtree` wird der Pfad per `realpath` geprüft: er muss im Upload-Ordner liegen, und Symlinks nach draußen werden nicht verfolgt.

Die Funktionen in `backend/app/services/cleanup.py` geben die Liste der entfernten Dinge zurück. Dieselbe Liste steht in der API-Antwort unter `data.deleted` und im Log.

## Simulation löschen

`DELETE /api/simulation/<simulation_id>` ruft `delete_simulation_cascade` auf.

Läuft die Simulation in diesem Prozess noch, oder nutzt ein Durchlauf mit Status `running` sie, antwortet die Schnittstelle mit 409. Es wird nichts gelöscht.

Sonst entfernt der Aufruf:

- den laufenden Runner, falls der Durchlauf intern aufgeräumt wird (die Schaltfläche im Verlauf löscht keine laufende Simulation)
- den Ordner `simulations/<simulation_id>/`
- jeden Bericht unter `reports/<report_id>/`, dessen `metadata.json` oder `meta.json` diese `simulation_id` enthält
- jedes Durchlauf-Protokoll `pipelines/<run_id>.json` samt Upload-Ordner `pipelines/<run_id>/`, das auf diese Simulation zeigt

Das Projekt `projects/<project_id>/` und sein Graph folgen nur, wenn keine andere Simulation und kein laufender Durchlauf das Projekt noch brauchen. Die `project_id` und `graph_id` stehen in `state.json` oder `simulation_config.json`.

## Projekt und Graph

`delete_project_cascade` löscht den Projektordner (Uploads, `extracted_text.txt`, `project.json`) und den Graph-Speicher:

- lokaler Wissensgraph: der Ordner `simulations/<graph_id>/` (darin `vault/`), wenn `graph_id` eine UUID ist
- bei `MEMORY_PROVIDER` `zep` oder `hybrid` zusätzlich der Zep-Graph über `delete_graph` des Memory-Providers. Schlägt das fehl, steht der Fehler nur im Log. Das lokale Aufräumen läuft weiter.

## Durchlauf löschen

`DELETE /api/pipeline/<run_id>` ruft `delete_pipeline_cascade` auf.

Status `running`: Antwort 409, Protokoll, Uploads, Simulation und Projekt bleiben.

Sonst: Protokoll und Upload-Ordner weg, danach die zugehörige Simulation und — unter derselben Bedingung wie oben — das Projekt samt Graph. Gibt es noch keine Simulation, wird das Projekt direkt entfernt, wenn es niemand Laufendes mehr benutzt.

## Automatisch

Schlägt ein Durchlauf in `pipeline.py` fehl, wird der Fehler ins Protokoll geschrieben und ins Log gelegt. Direkt danach läuft `delete_pipeline_cascade`. Die Oberfläche bekommt den technischen Text nicht: der Eintrag ist weg, ein noch offener Lauf sieht beim nächsten Abruf 404 und zeigt „Dieser Durchlauf wurde abgebrochen und aufgeräumt.“

Beim Backend-Start markiert `mark_stale_runs` Durchläufe, die noch `running` sind. Ihr Thread ist mit dem Prozess verschwunden. Sie werden als abgebrochen gespeichert und genauso entfernt. Danach läuft `sweep_orphans()`.

## Verwaiste Reste

`sweep_orphans` (standardmäßig älter als 24 Stunden):

- Projekte ohne Simulation und ohne laufenden Durchlauf, deren `created_at` (sonst das Änderungsdatum des Ordners) älter als die Frist ist, inklusive Graph
- UUID-Ordner unter `simulations/`, auf die keine `project.json` mehr zeigt

Nicht angefasst werden: laufende Durchläufe, ihre Projekte und Simulationen, junge Projekte, Projekte mit Simulation, Ordner mit fremdem Namen.

## Verlauf

Im Verlauf hat jede Zeile, die nicht läuft, „Löschen“. Reine Durchlauf-Zeilen ohne Simulation gehen an `DELETE /api/pipeline/<run_id>`. Nach dem Löschen verschwindet die Zeile. Statt eines rohen Fehlertexts wie einem HTTP-Verbindungsfehler steht dort „Abgebrochen“.
