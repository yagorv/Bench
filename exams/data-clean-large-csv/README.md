# Stream-clean a fixed large CSV

**ID:** `data.clean-large-csv.v1`  
**Duración estimada:** 8–15 minutos

## Propósito del examen

Medir si el agente puede analizar y limpiar un CSV de un millón de filas sin cargarlo entero en memoria.

## Resultado esperado

Un programa Python, el CSV limpio con las filas válidas normalizadas y ordenadas, y un resumen JSON con los conteos.

El agente debe devolverte estos archivos con las rutas indicadas:

- `submission/solution.py`
- `submission/cleaned.csv`
- `submission/summary.json`

## Cómo entregarlo

Envía `TASK.md` y todos los archivos de esta carpeta en una conversación nueva. Esta carpeta incluye el contexto, las entradas y los archivos iniciales necesarios; no tienes que preparar nada.
