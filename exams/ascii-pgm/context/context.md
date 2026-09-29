# Fixed task context
Input `inputs/portrait.pgm` is ASCII plain PGM (P2). Pixels are row-major. The exact ramp, darkest to lightest, is `@%#*+=-:. ` (the last character is a space). For each value `p` and maximum `m`, use index `min(9, p * 9 // (m + 1))`. Remove trailing spaces from each rendered line. Keep all rows and terminate the file with one newline.
