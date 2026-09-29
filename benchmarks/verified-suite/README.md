# Verified suite: pruebas deterministas para comparar herramientas de IA (calidad **y** coste)

> Subproyecto autónomo de este repositorio, con su propio ejecutor (`bench.py`) y su propio registro (`results.jsonl`), independiente de `python3 -m agentbench`. Los comandos de este documento se ejecutan **desde esta carpeta**: `cd benchmarks/verified-suite`. Requiere Python 3.10+ y solo biblioteca estándar.

Cada prueba es un **`TASK.md` autocontenido** (requisitos al estilo *User Story + WHEN/THEN/SHALL*) más los ficheros que necesite. Lo ejecutas en la herramienta que quieras —agente de línea de comandos (Claude Code, Codex, Cursor…) o chat (ChatGPT, Gemini, Claude.ai…)— y un **verificador determinista en Python estándar** da una nota de 0 a 1. Tú mides el coste; la suite registra nota + coste + tiempo y calcula *coste por tarea superada* y la frontera de Pareto.

**Requisitos:** Python 3.10+. Nada más (ni pip, ni red, ni servicios). Para *evaluar* código generado por una IA, hazlo en un contenedor o VM: el verificador lo ejecuta.

**¿Solo quieres darle una tarea a un agente?** Usa los [paquetes congelados](packages/README.md): cada carpeta de `packages/` es un `TASK.md` autocontenido más sus datos, lista para copiar y entregar, y `bench.py score` la puntúa.

## ¿Qué funciona ya? — 5 pruebas de punta a punta

| Id | Prueba | Tipo | Niveles | Qué mide |
|---|---|---|---|---|
| `t01_kite_interpreter` | Implementar un intérprete de un lenguaje inventado desde su especificación | construir | 1 | 348 programas ocultos, comparación carácter a carácter |
| `t02_kite_bugfix` | Corregir un intérprete con 3/6/10 bugs inyectados | leer/depurar | 1–3 | tests arreglados netos (regresiones restan) |
| `t03_formats_unification` | Pipeline de 3 CLIs (txt→json, hoja→json, json→csv) desde requisitos | construir, requisitos largos | 1–3 | campos exactos sobre 20/60/120 ficheros ocultos, CLI, robustez, determinismo, solo-stdlib |
| `t04_log_forensics` | 19 preguntas exactas sobre un log ruidoso | análisis de datos a escala | 1–3 | respuestas exactas; el log pesa ≈55k / 425k / 2M tokens |
| `t05_vrp` | Ruteo de vehículos con capacidad y distancia máxima | optimización | 1–3 | `min(1, distancia_ref / distancia)`; infactible = 0 |

Los niveles cambian el **volumen** (y por tanto el coste), no la naturaleza de la tarea. Todo está generado por semilla: mismo `--seed` ⇒ mismos datos, otra semilla ⇒ otro examen (úsala para que las respuestas no se contaminen).

## Prueba en 1 minuto (sin ninguna IA)

```bash
python3 bench.py list
python3 bench.py demo            # recorre las 5 pruebas: entrega vacía = 0, solución de referencia = 1.0
```

Cada prueba se puede recorrer a mano:

```bash
python3 bench.py generate t05 --level 1 --seed 7 --out runs/vrp      # crea runs/vrp/for_tool (lo que ve la IA) y runs/vrp/hidden (solo evaluador)
python3 bench.py evaluate t05 --dir runs/vrp                         # sin entrega: 0
python3 bench.py reference t05 --dir runs/vrp                        # escribe la solución de referencia
python3 bench.py evaluate t05 --dir runs/vrp                         # 1.0
```

## Usarlo con una herramienta real

**Agente de línea de comandos** (ejecuta, mide tiempo, evalúa y registra en `results.jsonl`):

```bash
python3 bench.py run t03 --tool claude-code --level 2 --seed 11 --repeat 3 \
    --cmd 'claude -p "$(cat {prompt_file})" --dangerously-skip-permissions' \
    --telemetry telemetria.json          # opcional: {"cost_usd":..,"input_tokens":..,"output_tokens":..}
```
El comando se ejecuta dentro de `for_tool/`; el agente escribe en `answer/`. Si toca cualquier fichero fuera de `answer/`, la ejecución se invalida.

**Chat** (ChatGPT, Gemini, Claude.ai…):

```bash
python3 bench.py generate t04 --level 1 --seed 11 --out runs/logs
```
1. Abre una conversación nueva. Pega `runs/logs/for_tool/PROMPT_CHAT.txt` y **adjunta** los ficheros que lista. Si los datos caben (≤300 KB), `PROMPT_CHAT_INLINE.txt` los lleva incrustados y no hay que adjuntar nada.
2. Guarda la respuesta completa del chat en un fichero (`respuesta.md`). Si hay varios entregables (T03 tiene 4), el modelo los escribe en bloques de código precedidos por el nombre del fichero; la suite los separa sola.
3. `python3 bench.py evaluate t04 --dir runs/logs --response respuesta.md --tool chatgpt-5 --cost-usd 0.31 --input-tokens 60000 --output-tokens 2500 --minutes 2`

Después de varias ejecuciones: `python3 bench.py report` → tabla con nota media, % superadas, coste medio, **coste por tarea superada**, tiempo y frontera de Pareto (★).

Protocolo para que la comparación sea justa (mismo prompt por categoría, cero intervenciones humanas, ≥3 repeticiones, qué modelo/ajustes/límites registrar): `docs/RUN_PROTOCOL.md`.

## Cómo saber que la suite es fiable (`selftest`)

```bash
python3 bench.py selftest --task t03 --levels 1,2,3 --extra
```
Comprueba, por tarea y nivel: generación y evaluador deterministas, otra semilla ⇒ otros datos, **la solución de referencia saca 1.0**, entrega vacía ≈ 0 y comprobaciones propias de cada tarea (T02: cada uno de los 20 bugs se detecta; T03: las muestras cuadran con las reglas y romper una regla baja la nota). Si una prueba tuviera un hueco (una solución correcta que puntúa <1) aparecería aquí antes de usarla con nadie.

## Estructura

```
bench.py              CLI: list · generate · evaluate · reference · demo · run · report · selftest
suite_lib.py          utilidades (semillas, informe, aislamiento por proceso, anti-trampas)
tasks/tNN_*/task.py   una prueba = generate() + evaluate() + reference()
docs/CATALOG.md       catálogo de 27 pruebas en 7 familias (qué está hecho y qué solo diseñado)
docs/TASK_FORMAT.md   cómo escribir una prueba nueva · docs/RUN_PROTOCOL.md  protocolo de medición
designs/              plantilla y diseño de la prueba E1 (escribir tests), aún sin implementar
```

## Advertencias honestas
- El verificador **ejecuta código generado por la IA**: usa contenedor/VM.
- Semillas públicas ⇒ contaminación: usa semillas privadas para las rondas que importen.
- T01/T02 comparten los mismos tests (mide "escribir desde cero" frente a "arreglar").
- Idioma: todo lo que ve la herramienta (`TASK.md`, prompts) está en inglés; la salida del verificador, en español.
