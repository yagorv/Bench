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
python -m agentbench run --agent claude-code --task data.clean-large-csv.v1 --repetitions 5
python -m agentbench run --agent codex-cli --task data.clean-large-csv.v1 --repetitions 5
python -m agentbench report
python -m agentbench review --open
```

Los ejemplos llaman `claude -p` y `codex exec --json`; comprueba que esas herramientas estén instaladas y autenticadas. Para otra CLI añade su comando y argumentos como otro perfil. Consulta [adapters.md](adapters.md) si requiere un adaptador.

## Ejecutar ChatGPT, Devin u otra herramienta web

Este camino no depende de que el producto tenga una CLI compatible. Prepara el paquete de examen:

```sh
python -m agentbench prepare --task review.python-security-defect.v1 --agent "Nombre del producto y modelo"
```

1. Abre una conversación o sesión nueva y sube `task-package.zip`. Si la herramienta no acepta ZIP, descomprímelo y adjunta todos sus archivos.
2. Copia el `prompt.md` exacto impreso por el comando y envíalo. Ese mismo prompt también está dentro del ZIP.
3. Descarga la respuesta y coloca los archivos pedidos por el examen en la carpeta `submission/` que imprime el comando.
4. Ejecuta el evaluador y abre la galería de artefactos:

```sh
python -m agentbench evaluate --run-id "ID impreso por prepare"
python -m agentbench report
python -m agentbench review --open
```

El benchmark no agrega ni publica un informe de costes. Revisa el coste directamente en el panel del proveedor; `report` resume calidad y `review --open` permite inspeccionar los archivos.

Repite `prepare` una vez por intento. Los archivos de entrada ya están fijados y versionados; para que la comparación sea justa, usa la misma tarea, versión del modelo, configuración, permisos y límites. Inicia una conversación nueva para cada intento.

## Qué medir

`results/quality-summary.csv` resume aprobación y rutas de artefactos, sin costes. `python -m agentbench review --open` abre imágenes, vídeo y audio en una galería local y muestra vistas previas de código y texto. Puedes dejar una nota y una valoración de 1 a 5 por resultado y descargar `human-review.json`. Los archivos originales están en `results/runs/`. Revisa costes en el panel del proveedor.

La batería principal (`--all`) contiene tareas de varios minutos: limpiar un CSV fijo de un millón de filas, revisar un servicio Python de varios módulos con 12 defectos sembrados e implementar un planificador de flujos con dependencias, concurrencia, reintentos y pruebas ocultas. Las estimaciones de duración orientan; el tiempo real queda registrado y varía entre herramientas. Las tareas cortas de JSON, bug fix, imagen, vídeo, audio y Excel siguen disponibles como calibración usando `--task`. Las tareas de imagen y vídeo solo validan propiedades del archivo; todavía no puntúan si el resultado responde semánticamente al prompt.
