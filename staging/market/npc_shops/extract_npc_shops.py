#!/usr/bin/env python3
"""Extrae ítems comprables a NPC (shop/marketshop/itemshop) con precio y ubicación.

Fuente: data/raw/rathena/npc/ (shops.txt, refine, dump all_shop_lines.txt, …)
Precio -1 → Buy del item_db renewal (+ import).

Salida: staging/market/npc_shops/

Uso:
  python staging/market/npc_shops/extract_npc_shops.py
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
NPC_ROOT = ROOT / "data/raw/rathena/npc"
OUT = Path(__file__).resolve().parent
ITEM_FILES = [
    ROOT / "data/raw/rathena/db/re/item_db_usable.yml",
    ROOT / "data/raw/rathena/db/re/item_db_equip.yml",
    ROOT / "data/raw/rathena/db/re/item_db_etc.yml",
    ROOT / "data/raw/rathena/db/import/item_db.yml",
]

# map,x,y,dir \t type \t name \t sprite,items...
# - \t marketshop \t name \t sprite,items...
LINE_RE = re.compile(
    r"^(?P<map>[^\t,]+?)(?:,(?P<x>\d+),(?P<y>\d+),(?P<dir>\d+))?"
    r"\t(?P<stype>shop|marketshop|itemshop)\t"
    r"(?P<npc>[^\t]+)\t"
    r"(?P<body>.+)$"
)
ITEM_RE = re.compile(r"^(\d+):(-?\d+)(?::(\d+))?$")


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def load_items() -> dict[int, dict]:
    by_id: dict[int, dict] = {}
    for path in ITEM_FILES:
        if not path.exists():
            continue
        data = yaml.safe_load(path.read_text())
        for it in (data or {}).get("Body") or []:
            by_id[it["Id"]] = {
                "item_id": it["Id"],
                "aegis": it.get("AegisName"),
                "name": it.get("Name") or it.get("AegisName"),
                "type": it.get("Type") or "Etc",
                "buy": it.get("Buy"),
                "sell": it.get("Sell"),
            }
    if not by_id:
        fail("no items loaded")
    return by_id


def iter_shop_files() -> list[Path]:
    files = []
    dump = NPC_ROOT / "all_shop_lines.txt"
    if dump.exists():
        files.append(dump)
    for p in NPC_ROOT.rglob("*.txt"):
        if p.name == "all_shop_lines.txt":
            continue
        # skip mobs
        if "/mobs/" in str(p).replace("\\", "/"):
            continue
        files.append(p)
    return files


def parse_body_items(body: str) -> list[tuple[int, int, int | None]]:
    """sprite_or_fa ken,id:price[:stock],... → list (id, price_raw, stock)."""
    parts = body.split(",")
    if not parts:
        return []
    # first token is sprite / FAKE_NPC / -1 — skip unless it looks like item
    start = 1
    if ITEM_RE.match(parts[0].strip()):
        start = 0
    out = []
    for tok in parts[start:]:
        tok = tok.strip()
        m = ITEM_RE.match(tok)
        if not m:
            continue
        iid = int(m.group(1))
        price = int(m.group(2))
        stock = int(m.group(3)) if m.group(3) else None
        out.append((iid, price, stock))
    return out


def main() -> None:
    if not NPC_ROOT.exists():
        fail(f"missing {NPC_ROOT}")
    items = load_items()
    # item_id -> list of shop occurrences
    locs: dict[int, list[dict]] = defaultdict(list)
    seen_line: set[str] = set()
    shop_count = 0

    for path in iter_shop_files():
        text = path.read_text(errors="replace")
        for raw in text.splitlines():
            line = raw.strip()
            if not line or line.startswith("//"):
                continue
            if "\tshop\t" not in line and "\tmarketshop\t" not in line and "\titemshop\t" not in line:
                continue
            # dedupe dump vs files
            key = line
            if key in seen_line:
                continue
            seen_line.add(key)
            m = LINE_RE.match(line)
            if not m:
                continue
            stype = m.group("stype")
            npc = m.group("npc")
            map_name = m.group("map")
            x = int(m.group("x")) if m.group("x") else None
            y = int(m.group("y")) if m.group("y") else None
            parsed = parse_body_items(m.group("body"))
            if not parsed:
                continue
            shop_count += 1
            src = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else path.name
            for iid, price_raw, stock in parsed:
                meta = items.get(iid)
                buy_db = meta.get("buy") if meta else None
                if price_raw < 0:
                    price = buy_db
                    price_source = "item_db.Buy"
                else:
                    price = price_raw
                    price_source = "shop_script"
                locs[iid].append(
                    {
                        "map": map_name if map_name != "-" else None,
                        "x": x,
                        "y": y,
                        "npc": npc,
                        "shop_type": stype,
                        "price": price,
                        "price_raw": price_raw,
                        "price_source": price_source,
                        "stock_cap": stock,
                        "source_file": src,
                    }
                )

    catalog = []
    for iid, occurrences in sorted(locs.items()):
        meta = items.get(iid) or {
            "item_id": iid,
            "aegis": None,
            "name": f"#{iid}",
            "type": None,
            "buy": None,
            "sell": None,
        }
        prices = [o["price"] for o in occurrences if o["price"] is not None]
        # unique locations (map+npc)
        uniq = []
        seen_loc = set()
        for o in occurrences:
            k = (o["map"], o["x"], o["y"], o["npc"])
            if k in seen_loc:
                continue
            seen_loc.add(k)
            uniq.append(o)
        catalog.append(
            {
                "item_id": iid,
                "aegis": meta.get("aegis"),
                "name": meta.get("name"),
                "type": meta.get("type"),
                "npc_buy_yaml": meta.get("buy"),
                "shop_price_min": min(prices) if prices else None,
                "shop_price_max": max(prices) if prices else None,
                "shop_price_typical": prices[0] if prices else None,
                "location_count": len(uniq),
                "locations": uniq[:40],  # cap for file size; full in locations file
                "locations_total": len(uniq),
            }
        )

    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "shop_lines_parsed": shop_count,
        "unique_items": len(catalog),
        "note": "Ítems que un jugador puede comprar a NPC shop/marketshop/itemshop. "
        "Usar para excluir de oferta de bots y para DB de jugadores.",
        "sources": [
            "data/raw/rathena/npc/all_shop_lines.txt",
            "data/raw/rathena/npc/**/merchants/*.txt",
        ],
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    (OUT / "npc_buyable.json").write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"
    )
    (OUT / "npc_buyable_ids.txt").write_text(
        "\n".join(str(c["item_id"]) for c in catalog) + "\n"
    )
    # compact for bots filter
    compact = [
        {
            "item_id": c["item_id"],
            "name": c["name"],
            "aegis": c["aegis"],
            "price_min": c["shop_price_min"],
            "price_max": c["shop_price_max"],
            "maps": sorted(
                {loc["map"] for loc in c["locations"] if loc.get("map")}
            )[:20],
        }
        for c in catalog
    ]
    (OUT / "npc_buyable_compact.json").write_text(
        json.dumps(compact, indent=2, ensure_ascii=False) + "\n"
    )

    # highlight items that were polluting bot shops
    watch = {1010, 1011, 517, 912, 910, 911, 519, 984, 985, 756, 757, 909}
    print(f"shops={shop_count} items={len(catalog)}")
    print("watchlist (bot pollutants):")
    by_id = {c["item_id"]: c for c in catalog}
    for iid in sorted(watch):
        c = by_id.get(iid)
        if not c:
            print(f"  {iid}: NOT in NPC shops")
            continue
        maps = [loc["map"] for loc in c["locations"] if loc.get("map")][:5]
        print(
            f"  {iid} {c['name']}: price={c['shop_price_min']}-{c['shop_price_max']} "
            f"locs={c['locations_total']} maps={maps}"
        )
    print(f"Wrote {OUT}/")


if __name__ == "__main__":
    main()
