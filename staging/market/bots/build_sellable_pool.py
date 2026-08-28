#!/usr/bin/env python3
"""Construye el pool de ítems que los bots PUEDEN vender.

Reglas (aplican a todos los perfiles, no solo la muestra ×10):

  1. Está en grindable (drop + spawn normal) — o se pasa lista equivalente
  2. NO es comprable a NPC (npc_buyable_ids)
  3. Tipo mats: Etc / Healing / Usable / Delayconsume / Ammo
  4. Tiene precio LATAM
  5. Precio ≤ mats_max_price (cap absoluto — mata Orange@30k etc.)
  6. Si item_db.Buy existe: LATAM/Buy ≤ max_markup_ratio
     (mata Feather@10k con Buy=20 → ratio 500)
  7. total_sold LATAM ≥ min_sold

Cards se manejan aparte en preview_sim (no entran a este pool de mats).

Uso:
  python staging/market/bots/build_sellable_pool.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "pool"

GRINDABLE = ROOT / "staging/market/atlantis_playro/curated/grindable.json"
LATAM = ROOT / "staging/market/latam_tools/curated/ranked_market.json"
NPC_IDS = ROOT / "staging/market/npc_shops/npc_buyable_ids.txt"
ITEM_FILES = [
    ROOT / "data/raw/rathena/db/re/item_db_usable.yml",
    ROOT / "data/raw/rathena/db/re/item_db_equip.yml",
    ROOT / "data/raw/rathena/db/re/item_db_etc.yml",
    ROOT / "data/raw/rathena/db/import/item_db.yml",
]

RULES = {
    "require_grindable": True,
    "exclude_npc_buyable": True,
    "mat_types_yaml": {"Etc", "Healing", "Usable", "Delayconsume", "Ammo"},
    "mat_types_latam": {"diversos", "consumivel", None},  # soft; YAML type manda
    "mats_max_price": 12_000,  # cap LATAM — Feather 10k pasa precio, cae por ratio
    "max_markup_vs_yaml_buy": 50.0,  # LATAM/Buy; Feather 500× → out; Orange ~100× → out
    "min_latam_sold": 80,
    "min_latam_price": 300,
    "notes": (
        "Pool global para elegir muchos bots. Progreso lento: pocos ítems útiles "
        "por mapa + rates 1× + activity gate. Ajustar caps aquí, no ad-hoc por bot."
    ),
}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def load_items() -> dict[int, dict]:
    by_id: dict[int, dict] = {}
    for path in ITEM_FILES:
        if not path.exists():
            continue
        for it in yaml.safe_load(path.read_text()).get("Body") or []:
            by_id[it["Id"]] = it
    return by_id


def latam_price(row: dict) -> int | None:
    if row.get("offers_median") is not None:
        return int(row["offers_median"])
    if row.get("market_avg") is not None:
        return int(row["market_avg"])
    return None


def main() -> None:
    for p in [GRINDABLE, LATAM, NPC_IDS]:
        if not p.exists():
            fail(f"missing {p}")

    grind = {r["item_id"]: r for r in json.loads(GRINDABLE.read_text())}
    latam = {r["item_id"]: r for r in json.loads(LATAM.read_text())}
    npc = {
        int(x)
        for x in NPC_IDS.read_text().splitlines()
        if x.strip() and not x.strip().startswith("#")
    }
    items = load_items()

    rejected = {k: [] for k in [
        "not_grindable_skip",  # N/A — we iterate grindable
        "npc_buyable",
        "bad_type",
        "no_latam_price",
        "price_too_low",
        "price_cap",
        "markup_vs_buy",
        "low_sold",
    ]}
    accepted = []

    for iid, g in grind.items():
        name = g.get("name")
        if iid in npc:
            rejected["npc_buyable"].append(iid)
            continue
        it = items.get(iid) or {}
        ytype = it.get("Type") or "Etc"
        if ytype not in RULES["mat_types_yaml"]:
            rejected["bad_type"].append(iid)
            continue
        lt = latam.get(iid)
        if not lt:
            rejected["no_latam_price"].append(iid)
            continue
        price = latam_price(lt)
        if price is None:
            rejected["no_latam_price"].append(iid)
            continue
        if price < RULES["min_latam_price"]:
            rejected["price_too_low"].append(iid)
            continue
        if price > RULES["mats_max_price"]:
            rejected["price_cap"].append(
                {"item_id": iid, "name": name or it.get("Name"), "price": price}
            )
            continue
        buy = it.get("Buy")
        ratio = None
        if buy and buy > 0:
            ratio = price / buy
            if ratio > RULES["max_markup_vs_yaml_buy"]:
                rejected["markup_vs_buy"].append(
                    {
                        "item_id": iid,
                        "name": name or it.get("Name"),
                        "price": price,
                        "buy": buy,
                        "ratio": round(ratio, 1),
                    }
                )
                continue
        sold = lt.get("total_sold") or 0
        if sold < RULES["min_latam_sold"]:
            rejected["low_sold"].append(iid)
            continue

        accepted.append(
            {
                "item_id": iid,
                "name": name or it.get("Name"),
                "aegis": it.get("AegisName"),
                "type": ytype,
                "latam_price": price,
                "latam_total_sold": sold,
                "yaml_buy": buy,
                "markup_vs_buy": round(ratio, 2) if ratio is not None else None,
                "classic": g.get("classic"),
                "spawn_map_count": g.get("spawn_map_count"),
            }
        )

    accepted.sort(key=lambda r: -r["latam_total_sold"])
    OUT.mkdir(parents=True, exist_ok=True)

    rules_out = {
        "require_grindable": RULES["require_grindable"],
        "exclude_npc_buyable": RULES["exclude_npc_buyable"],
        "mat_types_yaml": sorted(RULES["mat_types_yaml"]),
        "mats_max_price": RULES["mats_max_price"],
        "max_markup_vs_yaml_buy": RULES["max_markup_vs_yaml_buy"],
        "min_latam_sold": RULES["min_latam_sold"],
        "min_latam_price": RULES["min_latam_price"],
        "notes": RULES["notes"],
    }
    summary = {
        "rules": rules_out,
        "grindable_in": len(grind),
        "npc_buyable_excluded": len(rejected["npc_buyable"]),
        "accepted_mats": len(accepted),
        "rejected_counts": {k: len(v) for k, v in rejected.items()},
        "rejected_price_cap_examples": rejected["price_cap"][:20],
        "rejected_markup_examples": rejected["markup_vs_buy"][:20],
    }
    (OUT / "sellable_rules.json").write_text(
        json.dumps(rules_out, indent=2, ensure_ascii=False) + "\n"
    )
    (OUT / "sellable_mats.json").write_text(
        json.dumps(accepted, indent=2, ensure_ascii=False) + "\n"
    )
    (OUT / "sellable_mat_ids.txt").write_text(
        "\n".join(str(r["item_id"]) for r in accepted) + "\n"
    )
    (OUT / "sellable_pool_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    (OUT / "rejected_detail.json").write_text(
        json.dumps(
            {
                "price_cap": rejected["price_cap"],
                "markup_vs_buy": rejected["markup_vs_buy"],
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )

    print(f"accepted mats: {len(accepted)} / grindable {len(grind)}")
    print("rejected:", summary["rejected_counts"])
    print("price_cap samples:", summary["rejected_price_cap_examples"][:8])
    print("markup samples:", summary["rejected_markup_examples"][:8])
    # confirm feather/orange out
    for iid, label in [(949, "Feather"), (582, "Orange"), (948, "Footskin"), (7003, "Anolian")]:
        ok = any(r["item_id"] == iid for r in accepted)
        print(f"  {label} ({iid}): {'IN' if ok else 'OUT'}")
    print(f"Wrote {OUT}/")


if __name__ == "__main__":
    main()
