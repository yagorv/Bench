# Guía rápida en español

## Ejecutar un examen manualmente

No necesitas Python, una CLI ni preparar paquetes. Descarga o clona el repositorio y abre [`exams/`](../exams/). Cada subcarpeta es un examen listo para entregar.

1. Elige una tarea en `exams/README.md` y abre su carpeta.
2. En una conversación nueva del agente, envía `TASK.md` y todos los archivos de esa carpeta. El `README.md` incluido enumera los archivos que el agente debe devolverte.
3. Repite con la misma carpeta y configuración para cada herramienta. Registra el coste y el tiempo en el panel de cada producto.
4. Guarda los archivos recibidos con las rutas `submission/...` indicadas por la tarea.
5. Sigue la guía correspondiente de `exams/review-guides/` para abrir, escuchar o ejecutar el resultado.

Los paquetes de examen no incluyen respuestas esperadas ni evaluadores ocultos. No compartas con el agente ninguna carpeta fuera del examen elegido.

## Exámenes disponibles

Hay cuatro tareas largas diseñadas para requerir varios minutos de trabajo: limpiar un CSV fijo de un millón de filas, normalizar un millón de registros JSON Lines, revisar doce defectos en un servicio Python con varios módulos e implementar un planificador de flujos con dependencias, concurrencia y reintentos. Sus estimaciones son de 8–20 minutos.

También hay seis tareas de calibración más breves: corregir un cálculo fiscal, convertir una imagen PGM a ASCII, generar una imagen PNG, un vídeo, una melodía de audio y un libro Excel.

## Ejecutor local opcional

El repositorio conserva un ejecutor para automatizar algunos agentes compatibles con CLI o aplicar comprobaciones locales. Requiere Python 3.11 o posterior; no es necesario para entregar los exámenes manualmente. Consulta [adapters.md](adapters.md) y el [protocolo](protocol.md) si quieres usar ese modo.
