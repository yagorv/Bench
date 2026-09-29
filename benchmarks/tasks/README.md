# Cápsulas de exámenes para agentes de IA

Cada carpeta es una cápsula: `prompt.md` es el examen en Markdown y los archivos de `context/`, `inputs/` y `starter/` son el material que recibe el agente. Puedes usar Claude Code, Codex, Devin, ChatGPT, Gemini u otra herramienta que acepte texto y archivos. No hace falta conectar el agente al ejecutor de este repositorio.

## Ejecutar un examen manualmente

1. Elige una tarea en [el catálogo](../catalog.md). Abre su `prompt.md` y entrega ese texto sin editarlo.
2. Adjunta los archivos indicados por `context_files`, `input_files` y `starter_files` en su `task.json`. Si la herramienta admite ZIP, puedes usar `python3 -m agentbench prepare --task ID --agent "nombre del agente"` para preparar una copia limpia.
3. No adjuntes `expected.json` ni la carpeta `grader/`: contienen material reservado para comprobar la entrega.
4. Pide que devuelva todos los archivos indicados por `output_files` en `task.json`. Para tareas de imagen, audio o vídeo, descarga el artefacto original, no solo una descripción o enlace.
5. Repite con una sesión nueva y los mismos archivos, prompt, semilla, tamaño de datos y configuración para cada agente.
6. Abre tú las salidas y compáralas. `python3 -m agentbench review --open` crea una galería local después de guardar los archivos de cada ejecución. Puedes dejar una valoración y notas por entrega. El coste y el tiempo los registras tú desde la herramienta usada.

## Dataset CSV

La prueba `data.clean-large-csv.v1` genera de forma reproducible un CSV de un millón de filas por defecto. Prepara una ejecución por agente con los mismos valores de `--rows` y `--seed`; el generador produce los mismos bytes. Puedes confirmar que los hashes `input_sha256` de `pending.json` coinciden.

```sh
python3 -m agentbench prepare --task data.clean-large-csv.v1 --agent "ronda-1" --rows 1000000 --seed 20260929
```

Cada ZIP contiene el prompt, contexto, datos y archivos de inicio, pero no el resultado esperado del evaluador. Usa una sesión nueva por agente.

## Cápsulas disponibles

### Tareas largas

- `data.clean-large-csv.v1`: analizar y limpiar un CSV grande, conservando un resultado canónico y un resumen verificable.
- `review.python-security-defect.v1`: revisar doce módulos y encontrar defectos sembrados sin falsos positivos.
- `python.workflow-scheduler.v1`: construir un programa modular desde una especificación precisa de CLI, dependencias, concurrencia, reintentos y fallos.

### Generación y calibración

- `oneshot.audio-jingle.v1`: crear un WAV de ocho segundos con una secuencia fija de dieciséis notas. El evaluador comprueba formato, duración y tono; tú puedes escucharlo.
- `oneshot.mp4-artifact.v1`: producir un vídeo de ocho segundos a partir de una secuencia temporal concreta. El evaluador revisa el contenedor; tú revisas el contenido y la animación.
- `oneshot.ascii-pgm.v1`: convertir una imagen de entrada a arte ASCII con una regla fija.
- `oneshot.png-artifact.v1`: generar una ilustración PNG que puedes inspeccionar en la galería.
- `oneshot.xlsx-sales-report.v1`: construir un libro Excel a partir de un CSV y revisar celdas, fórmulas y formato.
- `json.normalize-records.v1` y `python.fix-tax-calculation.v1`: comprobaciones breves de salida estructurada y reparación de código.

Las comprobaciones automáticas ayudan a detectar errores exactos; no sustituyen tu revisión visual o auditiva. El benchmark no genera una clasificación de costes.
