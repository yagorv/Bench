# Revisión manual: Normalizar y deduplicar un millón de registros JSON

Desde esta carpeta ejecuta `python3 submission/normalize.py --input inputs/records.jsonl --output submission/result.jsonl`. Comprueba que el archivo de salida tenga 900,000 líneas con `wc -l`, que la primera y última línea sean objetos JSON válidos con `head -n 1` y `tail -n 1`, y que el código lea la entrada línea a línea. Revisa muestras de correos normalizados y el orden de IDs.
