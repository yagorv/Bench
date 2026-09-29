from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="flowbench")
    parser.add_argument("input")
    parser.add_argument("--output", required=True)
    parser.parse_args(argv)
    parser.error("workflow scheduler is not implemented")
    return 2
