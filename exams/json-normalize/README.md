# Normalizar y deduplicar un millón de registros JSON

**ID:** `json.normalize-records.v1`  
**Duración estimada:** 8–15 minutos

## Propósito del examen

Medir si el agente puede transformar y ordenar un millón de registros, normalizando correos y resolviendo filas inválidas y duplicadas sin cargar toda la entrada en memoria.

## Resultado esperado

Un programa Python ejecutable que lea JSON Lines y produzca otro archivo JSON Lines con 900,000 registros válidos, únicos y ordenados por ID.

El agente debe devolverte estos archivos con las rutas indicadas:

- `submission/result.jsonl`
- `submission/normalize.py`

## Cómo entregarlo

Envía `TASK.md` y todos los archivos de esta carpeta en una conversación nueva. Esta carpeta incluye el contexto y el millón de registros de entrada; no tienes que preparar nada.
