from pathlib import Path

CACHE = Path("/srv/app/cache")

def read_cached(name: str) -> bytes:
    # Caller input is not constrained to a filename.
    return (CACHE / name).read_bytes()
