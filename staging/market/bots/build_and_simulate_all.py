#!/usr/bin/env python3
"""Genera bots para todos los mapas viables + simulación 100d + análisis.

1 bot ≈ 1 mapa (spawn combat ≥ umbral, ∩ pool vendible ≥ min_mats).
Tier por avg_level. Expert = diferido (no grind en sim base).

Uso:
  python staging/market/bots/build_and_simulate_all.py
"""

from __future__ import annotations

import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from design_sample import (  # noqa: E402
    HARVEST_PLANTS,
    MAPS_PATH,
    is_harvest_plant,
    load_items,
    load_mobs,
    tier_of,
)
from preview_sim import (  # noqa: E402
    SIM,
    accumulate_drops,
    dead_time_frac,
    kills_per_hour,
    load_latam,
    load_npc_buyable_ids,
    load_sellable_mat_ids,
    map_combat_mobs,
    select_offer,
    zeny_cost_per_hour,
)

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "all_bots"

# ---------------------------------------------------------------------------
ALL = {
    "min_combat_amount": 30,
    "min_sellable_mats": 2,  # si no, mapa no genera bot
    "mats_top_n": 4,
    "sim_days": 100,
    "hours_per_day": 3.5,  # mirror SIM; overwrite SIM for this run
    # Mapas a saltar (instancias / eventos / ep modernos densos)
    "skip_map_regex": r"^(1@|2@|3@|job_|quiz|poring_w|guild_|gld_|bat_|pvp_|force_|que_|e_|moc_pryd|treasure)",
    "include_expert_as_deferred": True,  # catalogar pero sim_days_grind=0
    "tier_unlock_active_days": {
        "novice": 0,
        "easy": 0,
        "mid": 7,
        "hard": 21,
        "expert": 999,  # diferido
    },
}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def skip_map(name: str) -> bool:
    return bool(re.search(ALL["skip_map_regex"], name))


def project_days_simple(
    offer: dict,
    kills_h: float,
    cost_h: float,
    days: int,
    hours_per_day: float,
) -> dict[str, Any]:
    kills = kills_h * hours_per_day * days
    spend = cost_h * hours_per_day * days
    mats = []
    mats_val = 0.0
    for m in offer["mats_for_sale"]:
        qty = m["p_per_map_kill"] * kills
        val = qty * m["latam_price"]
        mats.append(
            {
                "item_id": m["item_id"],
                "name": m["name"],
                "qty": round(qty, 2),
                "price": m["latam_price"],
                "stock_value": round(val, 2),
            }
        )
        mats_val += val
    cards = []
    cards_pipe = 0.0
    for c in offer["cards"]:
        dropped = c["p_per_map_kill"] * kills
        sellable = dropped * SIM["card_sell_fraction"]
        pipe = sellable * c["latam_price"]
        cards_pipe += pipe
        cards.append(
            {
                "item_id": c["item_id"],
                "name": c["name"],
                "dropped": round(dropped, 3),
                "sellable": round(sellable, 3),
                "price": c["latam_price"],
                "pipeline_value": round(pipe, 2),
            }
        )
    lot = mats_val + cards_pipe
    return {
        "days": days,
        "kills": round(kills, 1),
        "hours": round(hours_per_day * days, 1),
        "mats_stock": sorted(mats, key=lambda x: -x["stock_value"]),
        "mats_value": round(mats_val, 2),
        "cards": sorted(cards, key=lambda x: -x["sellable"]),
        "cards_sellable": round(sum(c["sellable"] for c in cards), 3),
        "cards_pipeline_value": round(cards_pipe, 2),
        "lot_expected": round(lot, 2),
        "zeny_spent": round(spend, 2),
        "net": round(lot - spend, 2),
        "pause_until_z": round(lot * SIM["pause_grind_until_sold_frac"], 2),
        "keep_shop_until_z": round(lot * SIM["shop_keep_until_sold_frac"], 2),
    }


def build_bot_for_map(
    map_name: str,
    spawn: dict,
    mobs: dict,
    items: dict,
    latam: dict,
    sellable_mats: set[int],
    npc_buyable: set[int],
) -> dict[str, Any] | None:
    if skip_map(map_name):
        return None
    # Soft check — avoid FailFast exit on empty combat maps
    has_combat = False
    for sm in spawn.get("mobs") or []:
        mob = mobs.get(sm["mob_id"])
        if mob and not is_harvest_plant(mob):
            has_combat = True
            break
    if not has_combat:
        return None
    combat, total, avg_lv, avg_hp, max_lv = map_combat_mobs(spawn, mobs)
    if total < ALL["min_combat_amount"]:
        return None

    kh = kills_per_hour(avg_hp, total)
    costs = zeny_cost_per_hour(avg_hp, kh["kills_per_hour"])
    hours = ALL["hours_per_day"]
    kills_day = kh["kills_per_hour"] * hours
    drops = accumulate_drops(combat, total, items, latam)

    # Forzar top_n desde ALL
    old_top = SIM["mats_top_n"]
    SIM["mats_top_n"] = ALL["mats_top_n"]
    card_min = SIM["card_min_price_by_map"].get(
        map_name, SIM["card_min_price_default"]
    )
    # novice fields: junk cards < 1M
    tier = tier_of(avg_lv)
    if tier == "novice" and card_min < 1_000_000:
        card_min = 1_000_000
    offer = select_offer(
        drops,
        kills_day,
        card_min_price=card_min,
        npc_buyable=npc_buyable,
        sellable_mats=sellable_mats,
    )
    SIM["mats_top_n"] = old_top

    if len(offer["mats_for_sale"]) < ALL["min_sellable_mats"]:
        return None

    deferred = tier == "expert" and ALL["include_expert_as_deferred"]
    unlock = ALL["tier_unlock_active_days"][tier]
    grind_days = 0 if deferred else ALL["sim_days"]

    sim100 = project_days_simple(
        offer,
        kh["kills_per_hour"],
        costs["zeny_cost_per_hour"],
        grind_days if grind_days else 1,  # placeholder; zero later
        hours,
    )
    if grind_days == 0:
        sim100 = {
            "days": 0,
            "kills": 0,
            "hours": 0,
            "mats_stock": [],
            "mats_value": 0,
            "cards": [],
            "cards_sellable": 0,
            "cards_pipeline_value": 0,
            "lot_expected": 0,
            "zeny_spent": 0,
            "net": 0,
            "pause_until_z": 0,
            "keep_shop_until_z": 0,
            "note": "expert deferred — no grind in base sim",
        }

    bot_id = f"map_{map_name}"
    return {
        "id": bot_id,
        "map": map_name,
        "tier": tier,
        "deferred": deferred,
        "unlock_after_active_days": unlock,
        "avg_level": round(avg_lv, 2),
        "max_level": max_lv,
        "avg_hp": int(avg_hp),
        "combat_amount": total,
        "kills_per_hour_combat": kh["kills_per_hour_combat"],
        "kills_per_hour": kh["kills_per_hour"],
        "dead_time_frac": kh["dead_time_frac"],
        "zeny_cost_per_hour": costs["zeny_cost_per_hour"],
        "mobs_top": [
            {
                "aegis": m["aegis"],
                "amount": m["amount"],
                "level": m["level"],
                "hp": m["hp"],
            }
            for m in sorted(combat, key=lambda x: -x["amount"])[:6]
        ],
        "sell_mats": [
            {
                "item_id": m["item_id"],
                "name": m["name"],
                "price": m["latam_price"],
                "p": m["p_per_map_kill"],
                "qty_per_day": m["qty_per_day"],
            }
            for m in offer["mats_for_sale"]
        ],
        "sell_cards": [
            {
                "item_id": c["item_id"],
                "name": c["name"],
                "price": c["latam_price"],
                "sellable_per_day": c["sellable_per_day"],
            }
            for c in offer["cards"][:5]
        ],
        "cards_junk_discarded": len(offer.get("cards_junk_discarded") or []),
        "sim_100d": sim100,
    }


def analyze(bots: list[dict]) -> dict[str, Any]:
    active = [b for b in bots if not b["deferred"]]
    deferred = [b for b in bots if b["deferred"]]
    by_tier = Counter(b["tier"] for b in bots)

    # item coverage: how many bots sell each item
    item_bots: dict[int, list[str]] = defaultdict(list)
    item_meta: dict[int, dict] = {}
    for b in active:
        for m in b["sell_mats"]:
            item_bots[m["item_id"]].append(b["map"])
            item_meta[m["item_id"]] = {
                "name": m["name"],
                "price": m["price"],
            }

    lot_vals = [b["sim_100d"]["lot_expected"] for b in active]
    nets = [b["sim_100d"]["net"] for b in active]
    kills = [b["sim_100d"]["kills"] for b in active]

    def pct(xs: list[float], p: float) -> float:
        if not xs:
            return 0.0
        s = sorted(xs)
        i = min(len(s) - 1, max(0, int(len(s) * p / 100)))
        return round(s[i], 2)

    # slow movers: low qty in 100d among sold mats
    slow = []
    for b in active:
        for m in b["sim_100d"]["mats_stock"]:
            if m["qty"] < 50:
                slow.append(
                    {
                        "map": b["map"],
                        "tier": b["tier"],
                        "item": m["name"],
                        "qty_100d": m["qty"],
                        "price": m["price"],
                    }
                )
    slow.sort(key=lambda x: x["qty_100d"])

    hot = []
    for b in active:
        for m in b["sim_100d"]["mats_stock"]:
            if m["qty"] >= 500:
                hot.append(
                    {
                        "map": b["map"],
                        "tier": b["tier"],
                        "item": m["name"],
                        "qty_100d": m["qty"],
                        "stock_value": m["stock_value"],
                    }
                )
    hot.sort(key=lambda x: -x["qty_100d"])

    multi = sorted(
        (
            {
                "item_id": iid,
                "name": item_meta[iid]["name"],
                "price": item_meta[iid]["price"],
                "bot_count": len(maps),
                "maps_sample": maps[:8],
            }
            for iid, maps in item_bots.items()
        ),
        key=lambda x: -x["bot_count"],
    )

    return {
        "bot_total": len(bots),
        "bots_active_sim": len(active),
        "bots_deferred_expert": len(deferred),
        "by_tier": dict(by_tier),
        "sim_days": ALL["sim_days"],
        "hours_per_day": ALL["hours_per_day"],
        "assumptions": {
            "activity": "sim assumes every day had ≥1 login (upper bound)",
            "sell_down": "after day 100 no new grind; shops sell remanente",
            "rates": "1x",
            "prices": "LATAM",
            "pool": "sellable_mat_ids",
        },
        "lot_100d": {
            "min": pct(lot_vals, 0),
            "p25": pct(lot_vals, 25),
            "p50": pct(lot_vals, 50),
            "p75": pct(lot_vals, 75),
            "p90": pct(lot_vals, 90),
            "max": pct(lot_vals, 100),
            "sum": round(sum(lot_vals), 2),
        },
        "net_100d": {
            "p50": pct(nets, 50),
            "sum": round(sum(nets), 2),
            "negative_bots": sum(1 for n in nets if n < 0),
        },
        "kills_100d": {
            "p50": pct(kills, 50),
            "sum": round(sum(kills), 1),
        },
        "unique_sell_mats": len(item_bots),
        "items_on_most_bots": multi[:25],
        "slow_stock_samples": slow[:30],
        "hot_stock_samples": hot[:30],
        "top_lot_bots": sorted(
            (
                {
                    "map": b["map"],
                    "tier": b["tier"],
                    "lot": b["sim_100d"]["lot_expected"],
                    "net": b["sim_100d"]["net"],
                    "mats": [m["name"] for m in b["sell_mats"]],
                }
                for b in active
            ),
            key=lambda x: -x["lot"],
        )[:20],
        "low_lot_bots": sorted(
            (
                {
                    "map": b["map"],
                    "tier": b["tier"],
                    "lot": b["sim_100d"]["lot_expected"],
                    "net": b["sim_100d"]["net"],
                    "mats": [m["name"] for m in b["sell_mats"]],
                }
                for b in active
            ),
            key=lambda x: x["lot"],
        )[:15],
    }


def main() -> None:
    # Align SIM hours with ALL
    SIM["hours_per_day"] = ALL["hours_per_day"]

    print("Loading data…")
    mobs = load_mobs()
    items = load_items()
    latam = load_latam()
    npc = load_npc_buyable_ids()
    pool = load_sellable_mat_ids()
    maps = json.loads(MAPS_PATH.read_text())
    print(
        f"  maps={len(maps)} pool={len(pool)} npc={len(npc)} "
        f"dead_time={dead_time_frac()}"
    )

    bots: list[dict] = []
    skipped = Counter()
    for spawn in maps:
        name = spawn["map"]
        if skip_map(name):
            skipped["regex_skip"] += 1
            continue
        bot = build_bot_for_map(name, spawn, mobs, items, latam, pool, npc)
        if bot is None:
            skipped["no_viable_offer_or_spawn"] += 1
            continue
        bots.append(bot)

    bots.sort(key=lambda b: (b["unlock_after_active_days"], b["avg_level"], b["map"]))
    OUT.mkdir(parents=True, exist_ok=True)

    catalog = {
        "generated": "build_and_simulate_all.py",
        "params": ALL,
        "sim_params_subset": {
            "drop_rate_mult": SIM["drop_rate_mult"],
            "hours_per_day": SIM["hours_per_day"],
            "dps": SIM["dps"],
            "dead_time_frac": dead_time_frac(),
            "mats_top_n": ALL["mats_top_n"],
            "card_sell_fraction": SIM["card_sell_fraction"],
        },
        "skipped": dict(skipped),
        "bot_count": len(bots),
        "bots": bots,
    }
    (OUT / "catalog.json").write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"
    )
    # compact index
    index = [
        {
            "id": b["id"],
            "map": b["map"],
            "tier": b["tier"],
            "deferred": b["deferred"],
            "unlock_after_active_days": b["unlock_after_active_days"],
            "avg_level": b["avg_level"],
            "avg_hp": b["avg_hp"],
            "combat_amount": b["combat_amount"],
            "kills_per_hour": b["kills_per_hour"],
            "sell_mats": [m["name"] for m in b["sell_mats"]],
            "sell_mat_ids": [m["item_id"] for m in b["sell_mats"]],
            "sell_cards": [c["name"] for c in b["sell_cards"]],
            "lot_100d": b["sim_100d"]["lot_expected"],
            "net_100d": b["sim_100d"]["net"],
            "cards_sellable_100d": b["sim_100d"]["cards_sellable"],
        }
        for b in bots
    ]
    (OUT / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n"
    )

    analysis = analyze(bots)
    (OUT / "analysis_100d.json").write_text(
        json.dumps(analysis, indent=2, ensure_ascii=False) + "\n"
    )

    # markdown summary
    md = []
    md.append("# Simulación all-bots 100d\n")
    md.append(f"Fecha: 2026-08-28  \nBots: **{analysis['bot_total']}** "
              f"(activos sim {analysis['bots_active_sim']}, "
              f"expert diferidos {analysis['bots_deferred_expert']})\n")
    md.append("## Por tier\n")
    for t, n in sorted(analysis["by_tier"].items(), key=lambda x: ALL["tier_unlock_active_days"].get(x[0], 0)):
        md.append(f"- **{t}**: {n} (unlock día activo ≥{ALL['tier_unlock_active_days'][t]})\n")
    md.append("\n## Lote esperado @100d (si hubo login cada día)\n")
    L = analysis["lot_100d"]
    md.append(f"- mediana {L['p50']/1e6:.1f}M · p25 {L['p25']/1e6:.1f}M · "
              f"p75 {L['p75']/1e6:.1f}M · suma {L['sum']/1e6:.0f}M\n")
    md.append(f"- nets negativos: {analysis['net_100d']['negative_bots']}\n")
    md.append("\n## Ítems en más bots\n")
    for row in analysis["items_on_most_bots"][:15]:
        md.append(f"- {row['name']} ×{row['bot_count']} bots @ {row['price']}z\n")
    md.append("\n## Top lotes\n")
    for row in analysis["top_lot_bots"][:10]:
        md.append(f"- `{row['map']}` ({row['tier']}): {row['lot']/1e6:.1f}M — {', '.join(row['mats'])}\n")
    md.append("\n## Notas\n")
    md.append("- Sim = cota superior (100 días con actividad).\n")
    md.append("- Tras día 100: solo vender remanente (sell-down).\n")
    md.append("- Expert diferidos: no aportan stock en esta corrida.\n")
    (OUT / "analysis_100d.md").write_text("".join(md))

    print(f"bots={len(bots)} skipped={dict(skipped)}")
    print(f"by_tier={dict(analysis['by_tier'])}")
    print(f"lot p50={analysis['lot_100d']['p50']:.0f} sum={analysis['lot_100d']['sum']:.0f}")
    print(f"Wrote {OUT}/")


if __name__ == "__main__":
    main()
