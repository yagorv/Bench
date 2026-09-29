# Formato de una prueba

Cada prueba es un **paquete** con tres partes. La herramienta de IA solo ve la primera.

```
<prueba>/
  TASK.md        ← lo único (más los fixtures) que recibe la herramienta: requisitos en estilo "User Story + Acceptance Criteria (WHEN/THEN/SHALL)"
  fixtures/      ← entradas de ejemplo VISIBLES (+ salida esperada de esas muestras)
  generate.py    ← genera con semilla: fixtures visibles + corpus OCULTO (entradas retenidas + oro)
  verify.py      ← evaluador determinista (solo stdlib): ejecuta el entregable y puntúa 0–1
  reference/     ← solución de referencia (demuestra que la tarea es resoluble; no se comparte)
```

## Reglas del `TASK.md`
1. **Autocontenido**: todo lo necesario está en el `.md` y en `fixtures/`. Sin URLs, sin servicios (nada de Bedrock, APIs ni internet), sin "usa tu criterio" en lo que se evalúa.
2. **Estilo de requisitos**: Introducción → contrato de datos → *Requirements* numerados, cada uno con *User Story* y *Acceptance Criteria* en forma `WHEN … THEN … SHALL …`.
3. **Contrato de ejecución explícito** (es lo que el verificador invoca): rutas de ficheros, nombres de CLI, flags, formato de entrada/salida, códigos de salida. Lo que no está en el contrato no se evalúa.
4. **Diccionarios normativos**: si la tarea depende de reglas (sinónimos de etiquetas, formatos de fecha, desempates), van *en el md*. El corpus oculto usa variantes **dentro** de esas reglas (no hay que adivinar nada).
5. **Último requisito siempre igual — Entorno, dependencias y seguridad**: Python 3.10+, solo biblioteca estándar, sin red, sin escribir fuera de las rutas de salida, idempotente, limpieza de temporales.
6. **Una sola respuesta final**: la herramienta termina con una línea resumen; el resultado se juzga por los ficheros, no por lo que diga.

## Reglas del verificador (para que sea 100 % determinista)
- Solo biblioteca estándar. Sin OCR, sin librerías de documentos, sin LLM-como-juez, sin red.
- Las entradas se generan con semilla (`random.Random(str)`: estable entre plataformas). Aritmética entera o `Decimal`; nunca comparaciones de floats sin tolerancia explícita.
- El entregable se ejecuta en **un subproceso por caso**, con `cwd` temporal, entorno mínimo, límite de tiempo y de memoria. Un cuelgue solo pierde ese caso.
- **Oráculos permitidos** (todos stdlib y verificados): implementación de referencia propia, `sqlite3`, `re`, `tomllib`, `json`, `difflib`, `zlib.crc32`, `unittest`. Las propiedades (ida y vuelta, invariantes, satisfacción de restricciones) se prefieren al "diff contra oro" cuando existan.
- **Antitrampas**: entradas retenidas (generalización), comprobación de que `TASK.md`/fixtures no se han modificado, escaneo AST de imports (solo stdlib), instantánea del sistema de ficheros antes/después, red bloqueada con un `sitecustomize` que hace fallar `socket`.
- **Selftest obligatorio** por prueba: (1) generación idéntica con misma semilla, (2) la referencia puntúa 1.0, (3) entrega vacía puntúa ~0, (4) el evaluador da el mismo JSON al repetirlo, (5) cada bug/mutante del catálogo es detectado.

## Puntuación
- `score ∈ [0,1]` = suma ponderada de comprobaciones; `passed` = todas al 100 %.
- Pruebas de **optimización** dan puntuación continua (p. ej. `coste_ref / coste`), con la factibilidad como requisito duro.
- Cada comprobación lleva nombre y detalle para diagnosticar *por qué* una herramienta pierde puntos.
- **Niveles** (L1/L2/L3): el mismo enunciado con más volumen, más variantes o más trampas. El nivel sube el coste sin cambiar la naturaleza de la tarea.
