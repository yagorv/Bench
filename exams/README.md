# Exámenes listos para entregar a agentes

Cada subcarpeta es un examen autocontenido: incluye enunciado, contexto, archivos de entrada y, si se necesita, código de inicio. No ejecutes comandos de preparación. Abre la carpeta que quieras y entrega `TASK.md` junto con el resto de sus archivos. Los agentes no necesitan recibir `benchmarks/tasks/`, respuestas esperadas ni evaluadores ocultos.

Abre una sesión nueva por agente y usa la misma carpeta y configuración al comparar herramientas. Pide que devuelva los archivos indicados en el `README.md` de la carpeta. Las instrucciones para abrir, escuchar o ejecutar cada resultado están en `review-guides/`; son para ti después de la ejecución.

| Carpeta | Tarea | Complejidad |
|---|---|---:|
| [`ascii-pgm/`](./ascii-pgm/) | `oneshot.ascii-pgm.v1` — Convert fixed PGM pixels to exact ASCII | Tarea breve |
| [`audio-jingle/`](./audio-jingle/) | `oneshot.audio-jingle.v1` — Synthesize the fixed eight-second jingle | 3–8 minutos |
| [`data-clean-large-csv/`](./data-clean-large-csv/) | `data.clean-large-csv.v1` — Stream-clean a fixed large CSV | 8–15 minutos |
| [`json-normalize/`](./json-normalize/) | `json.normalize-records.v1` — Normalizar y deduplicar un millón de registros JSON | 8–15 minutos |
| [`mp4-properties/`](./mp4-properties/) | `oneshot.mp4-artifact.v1` — Generate a valid short MP4 artifact | Tarea de calibración |
| [`png-properties/`](./png-properties/) | `oneshot.png-artifact.v1` — Generate a PNG artifact with fixed dimensions | Tarea de calibración |
| [`python-pr-review/`](./python-pr-review/) | `review.python-security-defect.v1` — Review a multi-module Python service for seeded defects | 10–20 minutos |
| [`python-tax-bug/`](./python-tax-bug/) | `python.fix-tax-calculation.v1` — Fix a seeded tax calculation bug | Tarea de calibración |
| [`workflow-scheduler/`](./workflow-scheduler/) | `python.workflow-scheduler.v1` — Implement a deterministic dependency-aware workflow scheduler | 10–20 minutos |
| [`xlsx-sales/`](./xlsx-sales/) | `oneshot.xlsx-sales-report.v1` — Build a deterministic sales workbook | Tarea de calibración |

Registra el tiempo y coste desde cada producto de IA. Al recibir los resultados, usa la guía de revisión correspondiente para inspeccionarlos manualmente.
