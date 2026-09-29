# Revisión manual: Fix a seeded tax calculation bug

Ejecuta `PYTHONPATH=submission python3 -c "from solution import calculate_total; print(calculate_total(12.5, 3, 0.2))"`; debe imprimir `45.0`. Comprueba también que `PYTHONPATH=submission python3 -c "from solution import calculate_total; calculate_total(1, -1, 0)"` lance `ValueError`.
