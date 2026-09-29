# Fixed task context
The starting implementation is `submission/solution.py`. Keep its public function signature `calculate_total(price, quantity, tax_rate)`. Correct result is `round(price * quantity * (1 + tax_rate), 3)`. Negative quantity must raise `ValueError`. Only Python standard-library behavior is needed.
