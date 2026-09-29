# Ejecutar los exámenes con distintos agentes

Cada carpeta de tarea contiene un `prompt.md`: ese es el examen que se entrega al agente. El mismo directorio declara en `task.json` los archivos de contexto, entradas y punto de partida. No uses `catalog.md` como prompt; es solo el índice de tareas.

## Flujo recomendado para herramientas web o de escritorio

Prepara una copia limpia del examen para cada ejecución:

```sh
python3 -m agentbench prepare --task data.clean-large-csv.v1 --agent "Nombre del producto y modelo" --rows 1000000 --seed 20260929
```

El comando crea `task-package.zip` y una copia exacta del `prompt.md`. El ZIP contiene el manifiesto, prompt, contexto, inputs y starter files; no incluye la respuesta de referencia del evaluador.

1. Abre una sesión nueva en la herramienta que quieres medir.
2. Sube el ZIP. Si esa herramienta no acepta ZIP, extráelo y adjunta todos los archivos que contiene.
3. Envía el `prompt.md` exacto que imprimió el comando. No lo resumas ni lo adaptes entre productos.
4. Descarga el artefacto que genere el agente y cópialo a `submission/` en la carpeta local del intento. Incluye `run-receipt.json`.
5. Llama a `evaluate` para puntuar el resultado y abre la galería:

```sh
python3 -m agentbench evaluate --run-id "ID impreso por prepare"
python3 -m agentbench report
python3 -m agentbench review --open
```

El reporte automático resume calidad y rutas de artefactos, no costes. Revisa tú el coste en el panel del proveedor. La galería abre vistas previas y enlaces a todos los archivos producidos; puedes añadir notas y una valoración de 1 a 5 y descargar `human-review.json`.

## Flujo para una CLI de agente

`python3 -m agentbench init` copia perfiles de ejemplo para Claude Code y Codex CLI. Configura los que tengas instalados y ejecuta el mismo ID, repeticiones, semilla y tamaño para cada agente:

```sh
python3 -m agentbench run --agent claude-code --task data.clean-large-csv.v1 --repetitions 5 --rows 1000000 --seed 20260929
python3 -m agentbench run --agent codex-cli --task data.clean-large-csv.v1 --repetitions 5 --rows 1000000 --seed 20260929
python3 -m agentbench report
python3 -m agentbench review --open
```

## Batería principal: tareas de varios minutos

`--all` ejecuta solo estas tareas. Cada una combina varios pasos y se ha dimensionado para requerir varios minutos; los rangos de `task.json` son estimaciones. El tiempo real se registra y puede variar entre productos.

- `data.clean-large-csv.v1`: limpieza en streaming de un millón de filas por defecto, normalización, validación, deduplicación, ordenación y resumen exacto.
- `review.python-security-defect.v1`: revisión de varios módulos con 12 defectos sembrados, sin falsos positivos.
- `python.workflow-scheduler.v1`: implementación modular de CLI y planificador determinista, con dependencias, concurrencia, reintentos, fallos, omisiones, validación y pruebas ocultas generadas.

## Calibración

Las tareas cortas siguen disponibles con `--task` para comprobar formato y funcionamiento, pero no forman parte de `--all`: `json.normalize-records.v1`, `python.fix-tax-calculation.v1`, `oneshot.ascii-pgm.v1`, `oneshot.xlsx-sales-report.v1`, `oneshot.png-artifact.v1`, `oneshot.mp4-artifact.v1` y `oneshot.audio-jingle.v1`.

Repite cada intento en una sesión limpia. Conserva modelo/versión, permisos, presupuesto de herramientas, límites, tamaño y semilla. Las tareas de imagen y vídeo solo tienen una comprobación técnica de archivo; su calidad visual no entra en el puntaje determinista actual.
