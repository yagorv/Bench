#!/usr/bin/env python3
"""Create deterministic CSV shards for the data engineering benchmark."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

FIELDS = ["record_id", "user_id", "email", "event_time", "amount", "region", "status"]
REGIONS = ["north", "south", "east", "west", "central"]
STATUSES = ["created", "paid", "refunded", "cancelled"]
BASE_TIME = datetime(2020, 1, 1, tzinfo=timezone.utc)


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=1_000_000)
    parser.add_argument("--seed", type=int, default=20260929)
    parser.add_argument("--shard-rows", type=int, default=100_000)
    parser.add_argument("--output", type=Path, default=Path("work/data"))
    args = parser.parse_args()
    if args.rows < 1 or args.shard_rows < 1:
        parser.error("--rows and --shard-rows must be positive")

    args.output.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    shards = []
    emitted = 0
    shard_index = 0
    while emitted < args.rows:
        count = min(args.shard_rows, args.rows - emitted)
        path = args.output / f"events-{shard_index:05d}.csv"
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
            writer.writeheader()
            for offset in range(count):
                row_id = emitted + offset
                # The seeded corruption patterns make cleaning tasks repeatable.
                email = f"user{row_id % 250_000}@example.test"
                if row_id % 97 == 0:
                    email = f" User{row_id % 250_000}@EXAMPLE.TEST "
                if row_id % 997 == 0:
                    email = "not-an-email"
                timestamp = BASE_TIME + timedelta(seconds=rng.randrange(0, 200_000_000))
                writer.writerow({
                    "record_id": f"evt-{row_id:012d}",
                    "user_id": f"usr-{rng.randrange(1, 250_001):06d}",
                    "email": email,
                    "event_time": timestamp.isoformat().replace("+00:00", "Z"),
                    "amount": f"{rng.randrange(0, 2_000_000) / 100:.2f}",
                    "region": rng.choice(REGIONS),
                    "status": rng.choice(STATUSES),
                })
        shards.append({"path": path.name, "rows": count, "sha256": digest(path)})
        emitted += count
        shard_index += 1

    manifest = {
        "format_version": 1,
        "generator": "agent-benchmark-dataset-v1",
        "seed": args.seed,
        "rows": args.rows,
        "shard_rows": args.shard_rows,
        "schema": FIELDS,
        "shards": shards,
    }
    manifest_path = args.output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.rows:,} rows across {len(shards)} shards to {args.output}")
    print(f"Manifest SHA-256: {digest(manifest_path)}")


if __name__ == "__main__":
    main()
