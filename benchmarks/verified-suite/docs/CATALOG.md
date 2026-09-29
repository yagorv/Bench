# Catálogo de pruebas

**Correspondencia de identificadores** (catálogo → carpeta en `tasks/`): A1→`t03`, B1→`t01`, C1→`t02`, D1→`t04`, D3→`t05`.

Leyenda de **estado**: ✅ construida y validada (generador + verificador + referencia) · 📐 diseñada (contrato y verificación definidos; falta implementar generador/verificador).
**Coste** orientativo por ejecución (se mide, no se asume): S < 0,05 $ · M 0,05–0,5 $ · L 0,5–5 $ · XL > 5 $.
**Oráculo** = de dónde sale la verdad, siempre con la biblioteca estándar.

Las 27 pruebas cubren 7 capacidades distintas a propósito: una herramienta puede ser excelente escribiendo código y mala razonando sobre datos (o al revés), y el coste cambia mucho entre familias.

---
## Familia A — Construir un proyecto desde requisitos (CLI + entradas retenidas)
Se parece a tu ejemplo de *Formats Unification*: varios requisitos, un contrato de datos intermedio, CLIs con flags, y un verificador que ejecuta las herramientas sobre entradas **que la herramienta nunca ha visto**.

**A1 · Formats Unification (edición offline)** ✅ (`tasks/t03_formats_unification`)
- Hace: 3 CLIs (`txt_to_json`, `sheet_to_json`, `json_to_csv`) que unifican facturas en texto plano y hojas CSV/TSV caóticas (cabecera desplazada, bloques de metadatos, filas de totales, celdas agrupadas) en un CSV estándar de 14 columnas. Sin LLM: reglas y diccionarios normativos dentro del `.md`.
- Oráculo: generador con verdad conocida (renderiza cada layout desde registros reales).
- Puntúa: exactitud por campo, registros completos, comportamiento CLI (`-o -`, `--append`, `--strict`, códigos de salida), robustez, idempotencia byte a byte, solo-stdlib (AST). Niveles: 20 ficheros ocultos (L1) → 60 (L2, agrupación + subtotales + 3 delimitadores) → 120 (L3, layouts mezclados, CRLF/BOM/Latin-1, valores no parseables con avisos). Selftest: la referencia saca 1.000 con 11 semillas; romper una regla (forward-fill, filas resumen) baja la nota. Coste: L.

**A2 · minisql** 📐 — CLI `minisql "SELECT …" a.csv [b.csv]` con gramática especificada (WHERE con AND/OR/paréntesis/LIKE/IN/IS NULL, GROUP BY/HAVING, agregados, ORDER BY múltiple, LIMIT/OFFSET, INNER/LEFT JOIN).
- Oráculo: **`sqlite3`** con los mismos CSV cargados con tipos declarados. Puntúa: fracción de ~300 consultas generadas por gramática con resultado idéntico (ordenado o como multiconjunto según haya ORDER BY). Perilla: nº de tablas/joins, subconsultas (L3). Coste: L.

**A3 · toml-subset → JSON** 📐 — `toml2json` para un subconjunto especificado de TOML (tablas, arrays de tablas, cadenas básicas/literales/multilínea, enteros con `_`/hex, floats, bools, fechas, inline tables, claves con puntos). Entradas inválidas → exit 1.
- Oráculo: **`tomllib`**. Corpus: documentos generados + mutaciones que los invalidan. Puntúa: fracción idéntica (JSON canónico) + fracción de inválidos rechazados. Coste: M–L.

**A4 · logstat** 📐 — CLI de analítica de logs con subcomandos (`count`, `percentile`, `sessions`, `burst`, `top`) sobre 2k → 100k líneas con multilínea, zonas horarias mixtas, líneas corruptas y duplicados.
- Oráculo: generador con registros verdad (no re-parsea el texto). Puntúa: consultas exactas. Exige ejecutar código en L2+. Coste: L (mucho input).

**A5 · reconcile** 📐 — conciliación bancaria vs. libro mayor por etapas normativas (exacta, por referencia con tolerancia, pagos divididos), con tabla de tipos de cambio y desempates definidos → `matches.json`.
- Oráculo: implementación de referencia del algoritmo especificado. Puntúa: F1 de pares, listas de no conciliados, resumen. Coste: L.

**A6 · pkgresolve** 📐 — resolutor de dependencias con restricciones semver (`^ ~ >= < ||`), prereleases excluidas, versión más alta primero, backtracking; salida = plan de instalación o error con el paquete en conflicto.
- Oráculo: comprobación formal (todas las restricciones satisfechas, cierre completo) **+** igualdad con el plan de referencia (regla de desempate normativa). Coste: M–L.

**A7 · sheetcalc** 📐 — motor de hoja de cálculo: fórmulas (`+ - * / ^`, `SUM AVG MIN MAX IF AND OR ROUND CONCAT`), referencias A1/rangos/entre hojas, ciclos (`#CYCLE!`), errores que se propagan (`#DIV/0!`, `#REF!`, `#VALUE!`). Entrada/salida JSON.
- Oráculo: motor de referencia. Puntúa: celdas exactas. Perilla: tamaño del grafo (hasta 20k celdas → rendimiento). Coste: L.

**A8 · md-lite → HTML** 📐 — convertidor de un subconjunto de Markdown (encabezados, énfasis, listas anidadas, código, enlaces, tablas, citas, escapado) con reglas de anidación exactas.
- Oráculo: renderizador de referencia + normalización de espacios. Puntúa: documentos idénticos. Coste: M–L.

## Familia B — Implementar una especificación formal (API de librería)
**B1 · Kite interpreter** ✅ (`tasks/t01_kite_interpreter`) — intérprete de un lenguaje inventado (closures, dicts, errores exactos, división truncada, `true != 1`…) contra **348 programas ocultos** en 11 categorías. Oráculo: intérprete de referencia. Niveles: 1 (la semilla cambia los tests aleatorios). Coste: L.

**B2 · regex-engine** 📐 — `search(pattern, text) → (start, end) | None` para un subconjunto (clases, cuantificadores voraces/perezosos, alternancia, grupos, anclas, `{m,n}`) con **semántica de `re`**.
- Oráculo: **`re`**. ~2 000 casos aleatorios desde una gramática. Perilla: perezosos/ancoras/backtracking. Coste: M.

**B3 · stateful-models** 📐 — caché LRU con TTL, *token bucket* y cola de prioridad con reloj inyectado; 100 000 operaciones aleatorias comparadas paso a paso con un modelo de referencia. Coste: M.

**B4 · binary-codec** 📐 — contenedor binario (cabecera, TLV anidados, varints, CRC32) con `encode/decode`. Comprueba ida y vuelta, vectores dorados, y que la corrupción (bit-flips) produce el error tipado correcto. Coste: M.

**B5 · diff-patch** 📐 — `diff(a, b) → unified` y `patch(a, unified) → b`. Oráculo: propiedad de ida y vuelta (500 pares) y **calidad** = tamaño del diff frente a `difflib` (puntuación continua). Coste: M.

**B6 · event-sim** 📐 — simulación de eventos discretos (ascensores/colas de atención) con reglas de desempate normativas; salida = registro de eventos. Oráculo: simulador de referencia, comparación línea a línea. Coste: L.

## Familia C — Mantener y depurar código existente
**C1 · Kite bugfix** ✅ (`tasks/t02_kite_bugfix`) — intérprete de ~600 líneas con 3/6/10 bugs inyectados de un catálogo de 20; se entrega la especificación y el código. Oráculo: los mismos 348 tests. Puntúa: tests arreglados netos (las regresiones restan; entregar sin cambios = 0). Selftest: cada uno de los 20 bugs es detectado. Coste: M–L.

**C2 · legacy-refactor** 📐 — módulo de ~500 líneas sin tests → paquete refactorizado con API idéntica.
- Verificación: 200 casos dorados de comportamiento (obligatorios) **+** métricas por `ast`: función ≤ 40 líneas, complejidad ≤ 10 (contando ramas), sin bloques duplicados (hash de ventanas), 100 % de firmas públicas con *type hints*. Puntúa 50/50 y las métricas solo cuentan si el comportamiento es 100 %. Coste: L.

**C3 · project-bughunt** 📐 — proyecto de 25 módulos con 8 bugs cruzados (generados por mutación de un proyecto base), con la salida de los tests que fallan. Oráculo: tests ocultos. Coste: L.

**C4 · feature-add** 📐 — añadir 3 funcionalidades (requisitos EARS) a un proyecto dado, sin romper lo existente. Oráculo: tests ocultos por funcionalidad + regresión. Coste: L.

**C5 · api-migration** 📐 — migrar 40 ficheros de una API v1 a v2 (renombrados, cambio de firma, nuevo orden de argumentos). Verificación: tests de comportamiento + búsqueda por `ast` de usos v1 residuales. Coste: M–L.

## Familia D — Razonamiento y optimización con datos
**D1 · log-forensics** ✅ (`tasks/t04_log_forensics`) — 19 preguntas sobre un log de 1,7k / 13k / 64k líneas (≈55k / 425k / 2M tokens; zonas horarias mezcladas, desorden, duplicados, trazas, líneas corruptas) (percentiles por definición nearest-rank, sesiones con 30 min de inactividad, ráfagas en ventana deslizante…). Salida: `answers.json`. Oráculo: registros verdad del generador; la referencia parsea solo el texto y coincide con esa verdad. Coste: L.

**D2 · longdoc-multihop** 📐 — documento de 6k–200k palabras con distractores casi idénticos, correcciones posteriores ("ya no es X, ahora es Y") y preguntas de dos saltos. Exact-match. Es la prueba más sensible al coste de contexto. Coste: M → XL según nivel.

**D3 · vrp** ✅ (`tasks/t05_vrp`) — ruteo con capacidad y distancia máxima por ruta (30/80/200 clientes, distancia Manhattan entera). Factibilidad = requisito duro; puntuación continua `min(1, coste_ref/coste)` con referencia *savings + búsqueda local*. Distingue quien escribe un heurístico de quien "razona a ojo". Coste: M–L.

**D4 · timetable** 📐 — asignación de turnos con restricciones duras y blandas; puntuación = `1 − penalización/penalización_ref` (acotada). Coste: M–L.

**D5 · puzzles** 📐 — lote de 30 puzzles (sudoku 9×9 y 16×16 difíciles, killer, nonogramas) verificados por restricciones (sin necesitar solución única). Un chat sin código lo pasa mal; con código es fácil: mide *herramientas*, no solo modelo. Coste: M.

## Familia E — Calidad de tests y revisión
**E1 · write-tests (mutation testing)** 📐 — *diseño completo en `designs/E1_write_tests/`*. El agente escribe la suite `unittest` de un módulo dado; se puntúa por cuántos mutantes distintos de verdad mata. Coste: M–L.

**E2 · security-audit** 📐 — 12 ficheros con 15 vulnerabilidades sembradas (inyección SQL, path traversal, deserialización insegura, secretos en código, comparación no constante…) y señuelos limpios. Salida: hallazgos JSON `{file, function, class}`. Puntúa: precisión y *recall* (F1); cada falso positivo penaliza. Coste: M.

**E3 · code-review** 📐 — un *diff* de PR con 10 defectos sembrados (off-by-one, condición de carrera, error de manejo…) y cambios legítimos como señuelo. Salida: lista de defectos con línea. F1 con tolerancia ±2 líneas. Coste: M.

## Familia F — Operar sistemas (agentes con shell)
**F1 · ticket-ops** 📐 — un CLI simulado `tk` (estado determinista) con 60 tickets; reglas EARS de triage/asignación/escalado. El agente debe ejecutar los comandos. El CLI registra cada operación firmada: editar la base a mano invalida la ejecución. Verificación: estado final + registro de operaciones. Mide *uso de herramientas* además de razonamiento. Coste: M–L.

**F2 · tree-reorg** 📐 — script idempotente que reorganiza un árbol de 500 ficheros según reglas (con `--dry-run` que no toca nada y un informe). Verificación: instantánea final + segunda ejecución sin cambios + dry-run sin cambios. Coste: M.

## Familia G — Texto y extracción con reglas verificables
**G1 · constrained-long-form** 📐 — documento técnico de 1 500 palabras con ~25 restricciones comprobables por script (estructura, léxico obligatorio/prohibido, longitudes, orden, formato). Puntúa: fracción de restricciones. Mide obediencia sostenida. Coste: S–M.

**G2 · structured-extraction** 📐 — 200 correos/tickets con ruido → JSON según un esquema con reglas de normalización. Puntúa: acierto exacto por campo. No exige código. Coste: M–L.

---
## Primera ronda recomendada (10 pruebas, cubren todas las familias y clases de coste)
| # | Prueba | Por qué |
|---|---|---|
| 1 | **A1** formats-unification ✅ | Réplica de tu ejemplo: requisitos + CLIs + entradas retenidas |
| 2 | **A2** minisql | Oráculo `sqlite3`; implementación grande y con muchos rincones |
| 3 | **B1** Kite interpreter ✅ | Especificación → implementación completa |
| 4 | **C1** Kite bugfix ✅ | Lectura de código y precisión; mismos tests que B1 (comparable) |
| 5 | **C2** legacy-refactor | Calidad de código medible, no solo corrección |
| 6 | **D1** log-forensics ✅ | Análisis de datos a escala (coste de input) |
| 7 | **D3** vrp ✅ | Optimización con puntuación continua |
| 8 | **E1** write-tests | Metacapacidad: escribir tests que detecten fallos |
| 9 | **F1** ticket-ops | Uso de herramientas (agentes) |
| 10 | **G2** structured-extraction | Sin código: separa chats de agentes |

Combinar B1 y C1 es deliberado: el mismo conjunto de tests mide "escribir desde cero" frente a "arreglar lo existente".
