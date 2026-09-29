# Protocolo de ejecución y medición (igualdad de condiciones)

## Preparar (una vez por prueba/nivel/semilla)
```
python3 bench.py generate <prueba> --level 2 --seed 7 --out runs/<prueba>_L2_s7
```
Se crea `for_tool/` (lo que recibe la herramienta) y `hidden/` (nunca se comparte). Cada ejecución de cada herramienta parte de **una copia limpia** de `for_tool/`.

## Dar la tarea a la herramienta
| Tipo de herramienta | Qué se le da | Cómo se recoge el resultado |
|---|---|---|
| Agente con shell (Claude Code, Codex CLI, Cursor/agent, Aider…) | Carpeta `for_tool/` + `PROMPT_AGENT.txt` | Ficheros en `for_tool/answer/` |
| Chat con adjuntos (ChatGPT, Gemini, Claude.ai…) | `PROMPT_CHAT.txt` + los ficheros adjuntos | Guardar la respuesta en un fichero → `evaluate --response` extrae el bloque de código |
| Chat sin adjuntos | `PROMPT_CHAT_INLINE.txt` (datos incrustados; solo si caben) | Igual |

El **texto del prompt es idéntico** para todas las herramientas de la misma categoría. No se corrige, no se "ayuda", no se responde a preguntas: **0 intervenciones humanas** (si la herramienta pregunta, se responde "usa tu mejor interpretación de TASK.md").

## Condiciones que deben fijarse y anotarse
- Modelo exacto (id/versión), modo de razonamiento/esfuerzo, temperatura si se puede, herramientas habilitadas (shell, ejecución de código, navegador).
- Límites iguales: tiempo máximo, nº máximo de turnos/llamadas a herramientas, presupuesto máximo si la herramienta lo permite.
- Red: desactivada para la tarea (si la herramienta no puede desactivarla, anotarlo).
- **Repeticiones**: mínimo 3 por (herramienta, prueba, nivel) con la misma semilla; se reporta mediana y rango. Una sola ejecución no distingue herramientas.

## Evaluar y registrar
```
python3 bench.py evaluate <prueba> --dir runs/<...> [--response respuesta.md] \
    --tool "NombreHerramienta v1" --cost-usd 0.42 --input-tokens 81234 --output-tokens 9120 --minutes 6.5 --notes "thinking=high"
```
Añade una línea a `results.jsonl` con la puntuación del verificador y lo que tú midas del coste. Para agentes en CLI, `bench.py run --cmd "..."` automatiza ejecución + medición de tiempo (+ `--telemetry` con el coste si la herramienta lo exporta).

## Coste: qué medir (cada herramienta lo expone a su manera)
- **API/agentes con telemetría**: tokens de entrada, salida, caché (lectura/escritura) y razonamiento → coste en USD con la tarifa vigente; nº de turnos y de llamadas a herramientas.
- **Suscripciones/chats sin telemetría**: tokens estimados con el tokenizer del proveedor sobre prompt + respuesta, más tiempo de reloj; marcar `source: estimado`.
- Se reporta siempre **coste absoluto, coste por prueba superada y tiempo**, no solo puntuación.

## Informe
```
python3 bench.py report
```
Tabla por herramienta: puntuación media, % superadas, coste medio, **coste por tarea superada**, tiempo y **frontera de Pareto** (★ = nadie es a la vez mejor y más barato).

## Avisos
- El verificador **ejecuta código generado por una IA**. Ejecútalo en un contenedor/VM sin credenciales.
- Las semillas públicas se "queman" si acaban en datos de entrenamiento: guarda semillas privadas para comparativas serias y rota las públicas.
- Las pruebas de tiempo (timeouts) son la única fuente de variación entre máquinas; los límites son holgados a propósito.
