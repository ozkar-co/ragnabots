#!/usr/bin/env python3
"""Backward-compatible wrapper — prefer: python staging/market/fetch_batch.py atlantis"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from batch_common import BatchOpts, DEFAULT_IDS_FILE, load_ids_file
from runners import run_atlantis


def main() -> None:
    p = argparse.ArgumentParser(description="Fetch Atlantis stats (use fetch_batch.py for all sources)")
    p.add_argument("--items", default="")
    p.add_argument("--items-file", type=Path, default=DEFAULT_IDS_FILE)
    p.add_argument("--delay", type=float, default=3.0)
    p.add_argument("--jitter", type=float, default=2.0)
    p.add_argument("--timeout", type=float, default=30.0)
    p.add_argument("--batch-pause-every", type=int, default=50)
    p.add_argument("--batch-pause", type=float, default=60.0)
    p.add_argument("--resume", action="store_true")
    p.add_argument("--limit", type=int, default=0)
    args = p.parse_args()

    if args.items:
        args.items_file.write_text(
            "\n".join(x for x in args.items.split(",") if x.strip()) + "\n",
            encoding="utf-8",
        )
    elif not args.items_file.exists():
        raise SystemExit(f"{args.items_file} missing — run fetch_batch.py extract-ids")

    opts = BatchOpts(
        delay=args.delay,
        jitter=args.jitter,
        timeout=args.timeout,
        batch_pause_every=args.batch_pause_every,
        batch_pause=args.batch_pause,
        resume=args.resume,
    )
    run_atlantis(args.items_file, opts, limit=args.limit or None)


if __name__ == "__main__":
    main()
