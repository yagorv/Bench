# E1 · Test Suite Author — diseño de la verificación (NO se comparte con la herramienta)

## Módulo bajo prueba
`shopcart.py` generado con semilla: 8–14 funciones públicas y una clase con estado (carrito), con reglas de precios en tablas (tramos de descuento por cantidad, cupones con mínimos y compatibilidad, IVA con redondeo *half-up* o *half-even* según el nivel, envío gratuito por umbral). Dinero en enteros (céntimos) para evitar floats. Cada regla del `SPEC.md` corresponde a código concreto → los mutantes se pueden anclar a reglas.

| Nivel | Líneas del módulo | Mutantes “matables” | Extras |
|---|---|---|---|
| L1 | ~150 | 40 | Solo funciones puras |
| L2 | ~300 | 100 | + clase con estado y errores |
| L3 | ~500 | 200 | + interacciones entre cupones/impuestos, redondeos encadenados |

## Mutantes (deterministas)
1. Operadores AST aplicados al módulo de referencia, en orden estable: cambio de comparador (`<`↔`<=`, `==`↔`!=`), cambio aritmético (`+`↔`-`, `*`↔`//`), constante ±1, negación de condición, eliminación de sentencia, retorno de otro valor, eliminación de una comprobación de error, intercambio de argumentos.
2. Se generan todos los posibles y se **seleccionan N con la semilla**.
3. **Filtro de mutantes equivalentes** (clave para la justicia): se ejecuta un *fuzz diferencial* propio (p. ej. 20 000 llamadas por función con entradas de una gramática con semilla, incluyendo valores en los umbrales) contra el original. Un mutante es **matable** solo si el fuzz encuentra una diferencia observable (valor, tipo o excepción). Los no observables se descartan.

## Puntuación
| Comprobación | Peso | Cómo |
|---|---|---|
| **Puerta**: pasa en el original | — | Si falla, se para con puntuación 0 (motivo: qué test falla) |
| Tasa de muerte | 80 | `mutantes matados / mutantes matables`. Un mutante “muere” si la suite (proceso propio, límite 30 s) termina con fallos/errores *distintos de* fallos de importación de la propia suite |
| Higiene | 10 | Fracción de tests con ≥ 1 aserción (AST), nombre `test_<f>_<x>` válido y sin duplicados |
| Cobertura de excepciones | 5 | Fracción de condiciones de error del spec cuyo mutante “no lanza” muere |
| Ligereza | 5 | Suite ≤ 500 líneas y < 10 s en el original |

## Antitrampas y determinismo
- **Sin leer el código**: el verificador ejecuta con `sys.addaudithook` y suspende (0) si un test abre el fichero fuente del módulo; escaneo AST rechaza `inspect`, `ast`, `dis`, `importlib.reload`, `sys.modules[...] =`, `unittest.mock.patch` sobre el módulo.
- **Sin tests “siempre rojos”**: la puerta del original lo impide. **Sin tests flaky**: la suite se ejecuta 2 veces en el original y en 5 mutantes; si difiere → penalización.
- **Sin dependencia del orden**: se ejecuta con el orden alfabético y con el inverso; el resultado debe coincidir.
- El mismo módulo con distinta semilla tiene reglas y umbrales distintos → sin memorizar.
- Todo se ejecuta en subprocesos con tiempo límite; los mutantes se cargan desde un directorio temporal distinto por mutante.

## Qué separa a las herramientas
Mucha suite “bonita” con caminos felices mata ~40 %; las que prueban umbrales exactos (Requirement 2.2) y excepciones específicas llegan a > 85 %. También mide si la herramienta *ejecuta* su suite para comprobar que pasa (la puerta), no solo si la escribe.
