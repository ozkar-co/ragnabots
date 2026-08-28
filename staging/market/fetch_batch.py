#!/usr/bin/env python3
"""Unified batch fetcher for all external market sources.

  python staging/market/fetch_batch.py extract-ids
  python staging/market/fetch_batch.py atlantis --resume
  python staging/market/fetch_batch.py latam --server FREYA --resume
  python staging/market/fetch_batch.py ragnapi --resume
  python staging/market/fetch_batch.py divine_pride --resume
  python staging/market/fetch_batch.py all --resume --sources atlantis,latam,ragnapi
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow imports when run as script from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent))

from batch_common import BatchOpts, DEFAULT_IDS_FILE  # noqa: E402
from runners import run_atlantis, run_divine_pride, run_latam, run_ragnapi  # noqa: E402
from extract_item_ids import extract_ids, RATHENA_DB  # noqa: E402


def _batch_opts(args: argparse.Namespace) -> BatchOpts:
    return BatchOpts(
        delay=args.delay,
        jitter=args.jitter,
        timeout=args.timeout,
        batch_pause_every=args.batch_pause_every,
        batch_pause=args.batch_pause,
        retries=args.retries,
        resume=args.resume,
    )


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--items-file", type=Path, default=DEFAULT_IDS_FILE)
    p.add_argument("--delay", type=float, default=None)
    p.add_argument("--jitter", type=float, default=None)
    p.add_argument("--timeout", type=float, default=30.0)
    p.add_argument("--batch-pause-every", type=int, default=None)
    p.add_argument("--batch-pause", type=float, default=None)
    p.add_argument("--retries", type=int, default=3)
    p.add_argument("--resume", action="store_true")
    p.add_argument("--limit", type=int, default=0, help="Max items (0=all, for testing)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch fetch all market sources")
    sub = parser.add_subparsers(dest="command", required=True)

    p_extract = sub.add_parser("extract-ids", help="Build item_ids_all.txt from YAML")
    p_extract.add_argument("--db-root", type=Path, default=RATHENA_DB)

    defaults = {
        "atlantis": dict(delay=3.0, jitter=2.0, batch_pause_every=50, batch_pause=60.0),
        "latam": dict(delay=5.0, jitter=2.0, batch_pause_every=20, batch_pause=30.0),
        "ragnapi": dict(delay=2.0, jitter=1.0, batch_pause_every=100, batch_pause=45.0),
        "divine_pride": dict(delay=2.0, jitter=1.0, batch_pause_every=100, batch_pause=45.0),
    }

    for name in ("atlantis", "latam", "ragnapi", "divine_pride"):
        p = sub.add_parser(name)
        _add_common(p)
        d = defaults[name]
        p.set_defaults(delay=d["delay"], jitter=d["jitter"],
                       batch_pause_every=d["batch_pause_every"], batch_pause=d["batch_pause"])
        if name == "latam":
            p.add_argument("--server", default="FREYA", choices=["FREYA", "NIDHOGG"])
        if name == "divine_pride":
            p.add_argument("--region", default="iRO")

    p_all = sub.add_parser("all", help="Run multiple sources sequentially")
    _add_common(p_all)
    p_all.add_argument("--sources", default="atlantis,latam,ragnapi",
                       help="Comma-separated: atlantis,latam,ragnapi,divine_pride")
    p_all.add_argument("--server", default="FREYA", choices=["FREYA", "NIDHOGG"])
    p_all.add_argument("--region", default="iRO")
    p_all.set_defaults(delay=3.0, jitter=2.0, batch_pause_every=50, batch_pause=60.0)

    args = parser.parse_args()

    if args.command == "extract-ids":
        ids, per_file = extract_ids(args.db_root)
        DEFAULT_IDS_FILE.write_text("\n".join(str(i) for i in ids) + "\n", encoding="utf-8")
        print(f"wrote {len(ids)} ids -> {DEFAULT_IDS_FILE}")
        return

    if not args.items_file.exists():
        raise SystemExit(f"{args.items_file} missing — run: python staging/market/fetch_batch.py extract-ids")

    opts = _batch_opts(args)
    limit = args.limit or None

    if args.command == "atlantis":
        run_atlantis(args.items_file, opts, limit=limit)
    elif args.command == "latam":
        run_latam(args.items_file, opts, server=args.server, limit=limit)
    elif args.command == "ragnapi":
        run_ragnapi(args.items_file, opts, limit=limit)
    elif args.command == "divine_pride":
        run_divine_pride(args.items_file, opts, region=args.region, limit=limit)
    elif args.command == "all":
        for src in [s.strip() for s in args.sources.split(",") if s.strip()]:
            print(f"\n========== {src} ==========")
            if src == "atlantis":
                run_atlantis(args.items_file, opts, limit=limit)
            elif src == "latam":
                run_latam(args.items_file, opts, server=args.server, limit=limit)
            elif src == "ragnapi":
                run_ragnapi(args.items_file, opts, limit=limit)
            elif src == "divine_pride":
                run_divine_pride(args.items_file, opts, region=args.region, limit=limit)
            else:
                raise SystemExit(f"unknown source: {src}")


if __name__ == "__main__":
    main()
