#!/usr/bin/env python3
"""Extract all item IDs from local rAthena YAML into staging/market/item_ids_all.txt."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from batch_common import DEFAULT_IDS_FILE, MARKET_DIR, utc_now

_ID_LINE = re.compile(r"^\s+-\s+Id:\s+(\d+)\s*$", re.MULTILINE)
RATHENA_DB = MARKET_DIR.parents[1] / "data" / "raw" / "rathena" / "db"


def extract_ids(db_root: Path) -> list[int]:
    ids: set[int] = set()
    files = sorted(db_root.rglob("item_db*.yml"))
    if not files:
        raise SystemExit(f"no item_db*.yml under {db_root}")
    per_file: dict[str, int] = {}
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        found = {int(m) for m in _ID_LINE.findall(text)}
        if found:
            per_file[str(path.relative_to(db_root))] = len(found)
            ids |= found
    return sorted(ids), per_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract item IDs from rAthena YAML")
    parser.add_argument("--db-root", type=Path, default=RATHENA_DB)
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_IDS_FILE)
    parser.add_argument("--manifest", type=Path, default=MARKET_DIR / "item_ids_manifest.json")
    args = parser.parse_args()

    ids, per_file = extract_ids(args.db_root)
    args.output.write_text("\n".join(str(i) for i in ids) + "\n", encoding="utf-8")
    manifest = {
        "generated_at": utc_now(),
        "db_root": str(args.db_root),
        "total_ids": len(ids),
        "min_id": ids[0] if ids else None,
        "max_id": ids[-1] if ids else None,
        "files": per_file,
        "output": str(args.output),
    }
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(ids)} ids -> {args.output}")
    print(f"manifest -> {args.manifest}")


if __name__ == "__main__":
    main()
