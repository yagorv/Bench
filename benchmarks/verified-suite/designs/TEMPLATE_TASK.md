# Requirements — <Nombre de la prueba>

## Introduction
<Qué sistema se construye o qué problema se resuelve, en 3–6 líneas. Diagrama de flujo de datos si hay varias piezas.>
<Declarar: sin red, sin servicios externos, sin librerías de terceros. Todo lo evaluable está definido en este documento.>

<Contrato de datos: formato exacto de las entradas y salidas (columnas, claves JSON, tipos, unidades).>

## Shared rules (normativas)
<Diccionarios, formatos, redondeos, desempates, orden. Cada regla con un ejemplo. Nada de “usa tu criterio” en lo que se evalúa.>

## Requirements

### Requirement 1 — <Título>
**User Story:** As a <rol>, I want <objetivo>, so <beneficio>.

#### Acceptance Criteria
1. WHEN <condición> THEN the system SHALL <comportamiento verificable>.
2. THE system SHALL <comportamiento siempre cierto>.
3. WHEN <caso de error> THEN the system SHALL <error exacto: mensaje, tipo, código de salida>.

### Requirement N — Command-line / API contract
<Invocaciones exactas, flags, salida por stdout/stderr, códigos de salida, rutas.>

### Requirement N+1 — Environment, dependencies, safety   (siempre presente)
1. Python 3.10+, solo biblioteca estándar.
2. Sin red, sin subprocesos, sin leer/escribir fuera de las rutas indicadas.
3. Idempotente; limpiar temporales.

## Deliverables and provided files
<Qué ficheros se entregan en `answer/` y cuáles se proporcionan (solo lectura). Aclarar si la evaluación usa entradas distintas de las muestras.>

---
### Lista de comprobación del autor (no incluir en el md que ve la herramienta)
- [ ] Cada criterio de aceptación tiene ≥ 1 comprobación en el verificador.
- [ ] Cada regla ambigua tiene un ejemplo y una única lectura posible.
- [ ] La solución de referencia (escrita sin mirar el verificador) puntúa 1.0.
- [ ] La entrega vacía puntúa ≈ 0; una entrega “tramposa” conocida (copiar muestras) no pasa del ~60 %.
- [ ] Mismo seed → mismos bytes; distinto seed → datos distintos; evaluador repetido → mismo JSON.
- [ ] Sin dependencias fuera de la stdlib en verificador ni referencia.
