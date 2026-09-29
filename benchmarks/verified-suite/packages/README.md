# Paquetes congelados (nivel 1, semilla de ejemplo `20260929`)

Cada carpeta es **lo único que hay que darle a un agente**: un `TASK.md` autocontenido (requisitos y criterios de aceptación), los ficheros de datos que necesita y los prompts listos para pegar. No incluye la parte oculta del examen ni las respuestas. El agente no necesita nada más del repositorio.

| Paquete | Qué contiene | Entregable (dentro de `answer/`) |
|---|---|---|
| `t01_kite_interpreter_L1` | `TASK.md` con la especificación del lenguaje, 10 ejemplos | `solution.py` |
| `t02_kite_bugfix_L1` | `TASK.md`, `kite.py` con 3 bugs, 10 ejemplos | `kite.py` |
| `t03_formats_unification_L1` | `TASK.md`, `template.csv`, muestras con su salida esperada | `tools/txt_to_json.py`, `tools/sheet_to_json.py`, `tools/json_to_csv.py`, `tools/formats_common.py` |
| `t04_log_forensics_L1` | `TASK.md`, `input/app.log` (≈55k tokens) | `answers.json` |
| `t05_vrp_L1` | `TASK.md`, `instance.json` | `routes.json` |

## Cómo dárselo a un agente

1. Copia **solo la carpeta del paquete** a un sitio de trabajo nuevo (una copia por intento).
2. **Agente de línea de comandos** (Claude Code, Codex…): abre la terminal *dentro* de la copia y pásale el contenido de `PROMPT_AGENT.txt`. Escribirá el resultado en `answer/`.
3. **Chat** (ChatGPT, Gemini, Claude.ai…): en una conversación nueva pega `PROMPT_CHAT.txt` y adjunta los ficheros que lista. Si el paquete trae `PROMPT_CHAT_INLINE.txt`, ese ya lleva los datos incrustados y no hay que adjuntar nada. Guarda la respuesta del chat en los ficheros que pide dentro de `answer/`.
4. Mismo prompt, mismos ajustes y misma versión del modelo para todos los agentes que compares.

## Cómo puntuar

Desde `benchmarks/verified-suite/` (aquí sí hace falta el repositorio, porque regenera la parte oculta con la misma semilla):

```bash
python3 bench.py score t05_vrp --package RUTA/A/LA/COPIA --level 1 --seed 20260929 \
    --tool claude-code --cost-usd 0.31 --input-tokens 60000 --output-tokens 2500 --minutes 4
```

`score` primero comprueba que el paquete es idéntico al generado y avisa si el agente modificó ficheros de entrada o dejó ficheros fuera de `answer/`. La nota siempre se calcula contra los datos originales regenerados, no contra los que haya en la carpeta. `python3 bench.py report` resume los resultados.

## Comprobar que dos agentes recibieron lo mismo

```bash
cd packages && sha256sum -c SHA256SUMS
```

## Importante: la semilla de este repositorio es pública

Las respuestas de estos paquetes se pueden regenerar con la semilla `20260929` que está escrita aquí. Sirven para probar el flujo y para comparaciones informales. Para comparaciones serias genera paquetes nuevos con **una semilla que no publiques**:

```bash
python3 bench.py generate t05_vrp --level 1 --seed <TU_SEMILLA_PRIVADA> --out /ruta/privada/t05
# el paquete para el agente es /ruta/privada/t05/for_tool  (no compartas /ruta/privada/t05/hidden)
```
