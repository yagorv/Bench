# Guía rápida en español

## Preparación

Instala Python 3.11 o posterior y descarga el repositorio. El ejecutor no necesita paquetes externos.

```sh
git clone https://github.com/yagorv/Bench.git
cd Bench
python -m agentbench list
```

En Windows puedes usar `py -3 -m agentbench ...` en lugar de `python -m agentbench ...`.

## Ejecutar Claude Code o Codex CLI

Instala e inicia sesión en la herramienta que quieras comparar. Crea la configuración local:

```sh
python -m agentbench init
```

Abre `.agentbench/agents.json` y deja solo los perfiles instalados, o añade otro con el formato de `.agentbench/agents.example.json`. Los perfiles de ejemplo ya fijan el mismo mensaje, carpeta de trabajo y límite de tiempo para cada producto. Ejecuta una tarea varias veces:

```sh
python -m agentbench run --agent claude-code --task data.clean-large-csv.v1 --repetitions 5 --rows 1000000 --seed 20260929
python -m agentbench run --agent codex-cli --task data.clean-large-csv.v1 --repetitions 5 --rows 1000000 --seed 20260929
python -m agentbench report
```

Los ejemplos llaman `claude -p` y `codex exec --json`; comprueba que esas herramientas estén instaladas y autenticadas. Para otra CLI añade su comando y argumentos como otro perfil. Consulta [adapters.md](adapters.md) si requiere un adaptador.

## Ejecutar ChatGPT, Devin u otra herramienta web

Este camino no depende de que el producto tenga una CLI compatible. Prepara el paquete de examen:

```sh
python -m agentbench prepare --task review.python-security-defect.v1 --agent "Nombre del producto y modelo"
```

1. Sube `task-package.zip` a una conversación o sesión nueva.
2. Copia el prompt exacto desde `prompt.txt` y envíalo junto al paquete.
3. Descarga la respuesta y coloca los archivos pedidos en la carpeta `submission/` que imprime el comando. Incluye `run-receipt.json`.
4. Copia coste, tokens y duración del panel de uso de esa ejecución y evalúa:

```sh
python -m agentbench evaluate --run-id "ID impreso por prepare" --provider-cost 0.12 --currency USD --input-tokens 12000 --output-tokens 2000 --wall-time-ms 95000 --usage-source "panel de uso del proveedor"
python -m agentbench report
```

Si el proveedor solo muestra créditos o ACU, indica la unidad con `--currency ACU`; no la presentes como euros o dólares. Si no muestra consumo por ejecución, omite las métricas que no ofrece. No conviertas el precio de una suscripción en coste por tarea.

Repite `prepare` una vez por intento. Para que la comparación sea justa, usa tarea, tamaño, semilla, versión del modelo, configuración, permisos y límites iguales. Inicia una conversación nueva para cada intento.

## Qué medir

`results/leaderboard.csv` muestra tasa de éxito, coste y tokens del proveedor cuando están disponibles, tiempo del proceso y variación del coste. Cada carpeta de `results/runs/` conserva el paquete, el prompt, los archivos producidos, el recibo del agente y `run.json`. El recibo del agente se conserva separado de los datos de consumo del proveedor.

La batería combina tareas cortas de calibración y tareas más exigentes: revisión con cuatro defectos sembrados y limpieza de hasta millones de filas. Las tareas de imagen y vídeo de esta versión solo validan propiedades del archivo; todavía no puntúan si la imagen o el vídeo responden bien al prompt.
