"""Command-line interface: mine log templates from a file or stdin."""
from __future__ import annotations
import argparse
import json
import sys
from typing import List, Optional

from .miner import TemplateMiner


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="logminer", description="Cluster raw log lines into templates.")
    parser.add_argument("file", nargs="?", help="log file to read (default: stdin)")
    parser.add_argument("-t", "--threshold", type=float, default=0.5,
                        help="positional similarity to merge (0..1, default 0.5)")
    parser.add_argument("-n", "--top", type=int, default=None, help="show only the top N templates")
    parser.add_argument("--no-mask", action="store_true", help="don't pre-mask variables")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--save", metavar="PATH",
                        help="write the trained miner to PATH (reload with TemplateMiner.from_json)")
    args = parser.parse_args(argv)

    miner = TemplateMiner(similarity_threshold=args.threshold, mask=not args.no_mask)
    src = open(args.file, encoding="utf-8", errors="replace") if args.file else sys.stdin
    try:
        for line in src:
            line = line.rstrip("\n")
            if line.strip():
                miner.add_log(line)
    finally:
        if args.file:
            src.close()

    if args.save:
        with open(args.save, "w", encoding="utf-8") as fh:
            fh.write(miner.to_json(indent=2))

    clusters = miner.top()
    if args.top is not None:
        clusters = clusters[: args.top]

    if args.json:
        print(json.dumps(
            [{"id": c.id, "count": c.count, "template": c.template_str()} for c in clusters],
            indent=2))
    else:
        if not clusters:
            print("(no log lines)")
            return 0
        width = max(len(str(c.count)) for c in clusters)
        for c in clusters:
            print(f"{str(c.count).rjust(width)}  {c.template_str()}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
