#!/usr/bin/env python3
"""Preview de simulación — reglas de oferta de bots (pre-inyección).

Reglas (2026-08-28):
  - Rates de drop = 1x (boost OzRo = jugadores)
  - Precios = solo LATAM
  - Kills/hora ∝ densidad y ∝ 1/HP, luego × (1 - travel - restock - idle)
  - Gasto zeny/hora; pause grind hasta vender % del lote; shop hasta % vendido
  - Oferta mats: top valor×volumen; resto descartado
  - Cartas: 1 de cada 2; máx 1 en shop; Prontera min 1M (junk out)
  - Proyección 1/3/7/10 días (horas potenciales; activity gate aparte)

Uso:
  python staging/market/bots/preview_sim.py
"""

from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

# Reutilizar specs / loaders del diseño
sys.path.insert(0, str(Path(__file__).resolve().parent))
from design_sample import (  # noqa: E402
    BOTS,
    HARVEST_PLANTS,
    MAPS_PATH,
    OUT,
    is_harvest_plant,
    load_items,
    load_mobs,
    load_yaml_body,
    tier_of,
)

LATAM = Path(__file__).resolve().parents[3] / "staging/market/latam_tools/curated/ranked_market.json"
NPC_BUYABLE_IDS = (
    Path(__file__).resolve().parents[3]
    / "staging/market/npc_shops/npc_buyable_ids.txt"
)
SELLABLE_MAT_IDS = (
    Path(__file__).resolve().parents[3]
    / "staging/market/bots/pool/sellable_mat_ids.txt"
)

# ---------------------------------------------------------------------------
# Parámetros tunables — si a 10 días el stock es absurdo, tocar aquí
# ---------------------------------------------------------------------------
SIM = {
    "drop_rate_mult": 1.0,  # 1x — forzar rareza en bots
    "hours_per_day": 3.5,  # estándar runtime 3~4h; activity = ¿hubo login hoy?
    # Kills/h bruto: más HP → más tiempo; más spawn → más uptime.
    "dps": 200.0,
    "overhead_sec": 2.5,
    "full_uptime_amount": 100.0,
    "min_uptime": 0.20,
    "max_kills_per_hour": 1200.0,
    "min_kills_per_hour": 15.0,
    # Tiempo muerto (fracción de la hora de sesión que NO es combate)
    # travel = ir/volver al mapa; restock = vender NPC / storage / potions;
    # idle = AFK / dead time genérico dentro de la sesión.
    "dead_time_travel_frac": 0.08,
    "dead_time_restock_frac": 0.07,
    "dead_time_idle_frac": 0.05,
    # Gasto de zeny (generalista): potions/ammo/repair aproximado
    # cost_per_hour = base + k * avg_hp  (mapas duros gastan más)
    "zeny_cost_base_per_hour": 3_000,
    "zeny_cost_per_avg_hp": 2.0,  # 2z × avg_hp / hora de combate efectivo
    # Pausas / tienda
    "shop_open_after_hours": 1.0,  # tras acumular ≥1h de grind efectivo → puede abrir shop
    "pause_grind_until_sold_frac": 0.40,  # no vuelve a grindear hasta vender 40% del valor esperado del lote
    "shop_keep_until_sold_frac": 0.60,  # no cierra shop hasta 60% del esperado vendido
    "shop_keep_until_zeny_frac": 0.50,  # o hasta 50% del zeny esperado del lote
    # Oferta mats — pool global (build_sellable_pool.py); pocos por tienda
    "mats_top_n": 4,
    "use_sellable_pool": True,  # allowlist: grindable ∩ ¬NPC ∩ precio sano
    "exclude_npc_buyable": True,  # respaldo si pool no se usa
    "mats_min_price": 300,
    "mats_max_price": 16_000,
    "mats_min_total_sold": 80,
    "mats_require_offers": False,
    "mats_min_score_ratio": 0.12,
    "max_markup_vs_yaml_buy": 50.0,
    # Cartas
    "card_sell_fraction": 0.5,
    "card_shop_slots": 1,
    "card_require_offers": True,
    "card_max_price": 5_000_000,
    "card_min_price_default": 0,
    # Prontera / newbie: descartar cartas basura < 1M
    "card_min_price_by_map": {
        "prt_fild08": 1_000_000,
        "prt_fild01": 1_000_000,
        "prt_fild00": 1_000_000,
    },
    "days": [1, 3, 7, 10],
    "price_source": "latam_offers_median_else_market_avg",
}


def dead_time_frac() -> float:
    return (
        SIM["dead_time_travel_frac"]
        + SIM["dead_time_restock_frac"]
        + SIM["dead_time_idle_frac"]
    )


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def load_latam() -> dict[int, dict]:
    if not LATAM.exists():
        fail(f"missing {LATAM}")
    return {r["item_id"]: r for r in json.loads(LATAM.read_text())}


def load_npc_buyable_ids() -> set[int]:
    if not NPC_BUYABLE_IDS.exists():
        fail(
            f"missing {NPC_BUYABLE_IDS} — run "
            "python staging/market/npc_shops/extract_npc_shops.py first"
        )
    ids: set[int] = set()
    for line in NPC_BUYABLE_IDS.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            ids.add(int(line))
    return ids


def load_sellable_mat_ids() -> set[int]:
    if not SELLABLE_MAT_IDS.exists():
        fail(
            f"missing {SELLABLE_MAT_IDS} — run "
            "python staging/market/bots/build_sellable_pool.py first"
        )
    ids: set[int] = set()
    for line in SELLABLE_MAT_IDS.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            ids.add(int(line))
    return ids


def latam_price(row: dict | None, *, require_offers: bool) -> int | None:
    if not row:
        return None
    if require_offers:
        if not row.get("has_offers") or row.get("offers_median") is None:
            return None
        return int(row["offers_median"])
    if row.get("offers_median") is not None:
        return int(row["offers_median"])
    if row.get("market_avg") is not None:
        return int(row["market_avg"])
    return None


def kills_per_hour(avg_hp: float, combat_amount: int) -> dict[str, float]:
    """Kills/h bruto de combate, luego × (1 - dead_time)."""
    dps = SIM["dps"]
    overhead = SIM["overhead_sec"]
    t_kill = (avg_hp / dps) + overhead
    uptime = min(1.0, combat_amount / SIM["full_uptime_amount"])
    uptime = max(SIM["min_uptime"], uptime)
    raw = uptime * 3600.0 / t_kill
    combat_kills_h = max(
        SIM["min_kills_per_hour"], min(SIM["max_kills_per_hour"], raw)
    )
    dt = dead_time_frac()
    if dt >= 1.0:
        fail("dead_time fractions sum >= 1")
    effective = combat_kills_h * (1.0 - dt)
    return {
        "t_kill_sec": round(t_kill, 3),
        "uptime": round(uptime, 3),
        "kills_per_hour_combat": round(combat_kills_h, 1),
        "dead_time_frac": round(dt, 3),
        "kills_per_hour": round(effective, 1),
    }


def zeny_cost_per_hour(avg_hp: float, effective_kills_h: float) -> dict[str, float]:
    """Gasto proyectado por hora de sesión (no por hora de combate puro)."""
    # Escala con dificultad (HP) y un poco con ritmo de kills
    base = SIM["zeny_cost_base_per_hour"]
    hp_part = SIM["zeny_cost_per_avg_hp"] * avg_hp
    # Si hay mucho dead time, el gasto de combate baja un poco
    combat_frac = 1.0 - dead_time_frac()
    cost_h = (base + hp_part) * combat_frac
    return {
        "zeny_cost_per_hour": round(cost_h, 2),
        "zeny_cost_per_kill": round(cost_h / effective_kills_h, 4)
        if effective_kills_h > 0
        else None,
    }


def map_combat_mobs(
    spawn: dict, mobs: dict[int, dict]
) -> tuple[list[dict], int, float, float, int]:
    combat: list[dict] = []
    for sm in spawn["mobs"]:
        mob = mobs.get(sm["mob_id"])
        if not mob or is_harvest_plant(mob):
            continue
        combat.append(
            {
                "mob_id": sm["mob_id"],
                "aegis": mob.get("AegisName") or sm["name"],
                "name": mob.get("Name") or sm["name"],
                "amount": sm["amount"],
                "level": mob.get("Level", 1),
                "hp": mob.get("Hp", 1),
                "drops": mob.get("Drops") or [],
            }
        )
    if not combat:
        fail(f"no combat mobs on {spawn.get('map')}")
    total = sum(m["amount"] for m in combat)
    avg_lv = sum(m["amount"] * m["level"] for m in combat) / total
    avg_hp = sum(m["amount"] * m["hp"] for m in combat) / total
    max_lv = max(m["level"] for m in combat)
    return combat, total, avg_lv, avg_hp, max_lv


def accumulate_drops(
    combat: list[dict],
    total: int,
    items: dict[str, dict],
    latam: dict[int, dict],
) -> list[dict]:
    """P(item|kill) a 1x, con precio LATAM."""
    mult = SIM["drop_rate_mult"]
    acc: dict[int, dict[str, Any]] = {}

    for m in combat:
        weight = m["amount"] / total
        rates_by: dict[str, int] = defaultdict(int)
        for d in m["drops"]:
            aegis = d.get("Item")
            if aegis:
                rates_by[aegis] += int(d.get("Rate") or 0)

        for aegis, rate_raw in rates_by.items():
            meta = items.get(aegis)
            if not meta:
                continue
            p_mob = min(1.0, (rate_raw * mult) / 10000.0)
            p_map = weight * p_mob
            iid = meta["item_id"]
            lt = latam.get(iid)
            is_card = meta["type"] == "Card"
            price = latam_price(
                lt,
                require_offers=SIM["card_require_offers"]
                if is_card
                else SIM["mats_require_offers"],
            )
            if iid not in acc:
                acc[iid] = {
                    "item_id": iid,
                    "aegis": aegis,
                    "name": meta["name"],
                    "type": meta["type"],
                    "p_per_map_kill": 0.0,
                    "latam_price": price,
                    "latam_total_sold": (lt or {}).get("total_sold") or 0,
                    "has_offers": bool((lt or {}).get("has_offers")),
                }
            acc[iid]["p_per_map_kill"] += p_map
            if acc[iid]["latam_price"] is None and price is not None:
                acc[iid]["latam_price"] = price

    out = list(acc.values())
    for r in out:
        r["p_per_map_kill"] = round(r["p_per_map_kill"], 8)
    return out


def select_offer(
    drops: list[dict],
    kills_per_day: float,
    *,
    card_min_price: int,
    npc_buyable: set[int],
    sellable_mats: set[int],
) -> dict[str, Any]:
    """Separa cards vs mats; mats → top del pool vendible; cards → 1/2 + 1 slot."""
    use_pool = SIM["use_sellable_pool"]
    exclude_npc = SIM["exclude_npc_buyable"]

    cards_all = [d for d in drops if d["type"] == "Card"]
    cards_junk = [
        d
        for d in cards_all
        if d["latam_price"] is not None and d["latam_price"] < card_min_price
    ]
    cards = [
        d
        for d in cards_all
        if d["latam_price"] is not None
        and card_min_price <= d["latam_price"] <= SIM["card_max_price"]
    ]
    blocked = []
    mats_pool = []
    for d in drops:
        if d["type"] not in {"Etc", "Healing", "Usable", "Delayconsume", "Ammo"}:
            continue
        if d["latam_price"] is None:
            continue
        if use_pool:
            if d["item_id"] not in sellable_mats:
                blocked.append(
                    {
                        "item_id": d["item_id"],
                        "name": d["name"],
                        "price_latam": d["latam_price"],
                        "reason": "not_in_sellable_pool",
                    }
                )
                continue
        else:
            if exclude_npc and d["item_id"] in npc_buyable:
                blocked.append(
                    {
                        "item_id": d["item_id"],
                        "name": d["name"],
                        "price_latam": d["latam_price"],
                        "reason": "npc_buyable",
                    }
                )
                continue
            if not (
                SIM["mats_min_price"] <= d["latam_price"] <= SIM["mats_max_price"]
            ):
                continue
            if (d.get("latam_total_sold") or 0) < SIM["mats_min_total_sold"]:
                continue
        mats_pool.append(d)

    scored = []
    for d in mats_pool:
        qty_day = d["p_per_map_kill"] * kills_per_day
        sold = d.get("latam_total_sold") or 0
        score = d["latam_price"] * math.log1p(qty_day) * math.log1p(sold)
        scored.append({**d, "qty_per_day": round(qty_day, 4), "score": round(score, 2)})

    scored.sort(key=lambda x: -x["score"])
    if scored:
        best = scored[0]["score"]
        kept = [
            s
            for s in scored
            if s["score"] >= best * SIM["mats_min_score_ratio"]
        ][: SIM["mats_top_n"]]
    else:
        kept = []

    discarded = [
        {
            "item_id": s["item_id"],
            "name": s["name"],
            "price": s["latam_price"],
            "qty_per_day": s["qty_per_day"],
            "score": s["score"],
        }
        for s in scored
        if s["item_id"] not in {k["item_id"] for k in kept}
    ]

    card_rows = []
    for c in cards:
        drop_day = c["p_per_map_kill"] * kills_per_day
        sellable_day = drop_day * SIM["card_sell_fraction"]
        card_rows.append(
            {
                **c,
                "drop_per_day": round(drop_day, 4),
                "sellable_per_day": round(sellable_day, 4),
                "ev_latam_per_day_if_sold": round(
                    sellable_day * c["latam_price"], 2
                ),
            }
        )
    card_rows.sort(key=lambda x: -x["sellable_per_day"])

    return {
        "mats_for_sale": kept,
        "mats_discarded_count": len(discarded),
        "mats_discarded_top10": discarded[:10],
        "mats_blocked_pool": blocked[:40],
        "mats_blocked_pool_count": len(blocked),
        "mats_blocked_npc_buyable": [
            b for b in blocked if b.get("reason") == "npc_buyable"
        ][:30],
        "mats_blocked_npc_count": sum(
            1 for b in blocked if b.get("reason") == "npc_buyable"
        ),
        "cards": card_rows,
        "cards_junk_discarded": [
            {
                "item_id": c["item_id"],
                "name": c["name"],
                "price": c["latam_price"],
            }
            for c in cards_junk
        ],
        "card_min_price": card_min_price,
        "card_policy": {
            "sell_fraction": SIM["card_sell_fraction"],
            "shop_slots": SIM["card_shop_slots"],
            "min_price": card_min_price,
            "note": "acumula sellable; shop máx 1 carta; junk bajo min_price descartado",
        },
    }


def project_days(
    offer: dict,
    kills_h: float,
    cost_h: float,
) -> dict[str, Any]:
    hday = SIM["hours_per_day"]
    kills_day = kills_h * hday
    cost_day = cost_h * hday
    out = {}
    for days in SIM["days"]:
        kills = kills_day * days
        hours = hday * days
        spend = cost_day * days
        mats_stock = []
        mats_value = 0.0
        for m in offer["mats_for_sale"]:
            qty = m["p_per_map_kill"] * kills
            val = qty * m["latam_price"]
            mats_stock.append(
                {
                    "item_id": m["item_id"],
                    "name": m["name"],
                    "qty": round(qty, 2),
                    "price": m["latam_price"],
                    "stock_value": round(val, 2),
                }
            )
            mats_value += val

        cards_proj = []
        cards_pipeline = 0.0
        for c in offer["cards"]:
            dropped = c["p_per_map_kill"] * kills
            sellable = dropped * SIM["card_sell_fraction"]
            listed_expected = min(SIM["card_shop_slots"], sellable)
            pipe = sellable * c["latam_price"]
            cards_pipeline += pipe
            cards_proj.append(
                {
                    "item_id": c["item_id"],
                    "name": c["name"],
                    "dropped": round(dropped, 3),
                    "sellable": round(sellable, 3),
                    "shop_listed_cap": SIM["card_shop_slots"],
                    "expected_listed": round(listed_expected, 3),
                    "price": c["latam_price"],
                    "pipeline_value": round(pipe, 2),
                }
            )

        # Lote = mats + cards sellable value (esperado si se vende a LATAM)
        lot_expected = mats_value + cards_pipeline
        # Gates: zeny a vender antes de reabrir grind / cerrar shop
        pause_until = lot_expected * SIM["pause_grind_until_sold_frac"]
        keep_shop_until = max(
            lot_expected * SIM["shop_keep_until_sold_frac"],
            lot_expected * SIM["shop_keep_until_zeny_frac"],
        )
        net = lot_expected - spend

        out[str(days)] = {
            "days": days,
            "kills": round(kills, 1),
            "hours": round(hours, 1),
            "mats_stock": mats_stock,
            "mats_stock_value_latam": round(mats_value, 2),
            "cards": cards_proj,
            "cards_sellable_total": round(
                sum(c["sellable"] for c in cards_proj), 3
            ),
            "cards_pipeline_value": round(cards_pipeline, 2),
            "lot_expected_value": round(lot_expected, 2),
            "zeny_spent": round(spend, 2),
            "net_if_sold_at_latam": round(net, 2),
            "gates": {
                "pause_grind_until_sold_z": round(pause_until, 2),
                "keep_shop_until_sold_z": round(keep_shop_until, 2),
                "pause_frac": SIM["pause_grind_until_sold_frac"],
                "shop_keep_frac": SIM["shop_keep_until_sold_frac"],
            },
        }
    return out


def analyze_map(
    map_name: str,
    spawn: dict,
    mobs: dict[int, dict],
    items: dict[str, dict],
    latam: dict[int, dict],
    hours_share: float,
    npc_buyable: set[int],
    sellable_mats: set[int],
) -> dict[str, Any]:
    combat, total, avg_lv, avg_hp, max_lv = map_combat_mobs(spawn, mobs)
    kh = kills_per_hour(avg_hp, total)
    costs = zeny_cost_per_hour(avg_hp, kh["kills_per_hour"])
    kills_day = kh["kills_per_hour"] * SIM["hours_per_day"] * hours_share
    drops = accumulate_drops(combat, total, items, latam)
    card_min = SIM["card_min_price_by_map"].get(
        map_name, SIM["card_min_price_default"]
    )
    offer = select_offer(
        drops,
        kills_day,
        card_min_price=card_min,
        npc_buyable=npc_buyable,
        sellable_mats=sellable_mats,
    )

    ev_kill = sum(
        m["p_per_map_kill"] * m["latam_price"] for m in offer["mats_for_sale"]
    )

    return {
        "map": map_name,
        "tier": tier_of(avg_lv),
        "avg_level": round(avg_lv, 2),
        "max_level": max_lv,
        "avg_hp": int(avg_hp),
        "combat_amount": total,
        "hours_share": hours_share,
        "kills": kh,
        "costs": costs,
        "kills_per_day": round(kills_day, 1),
        "mobs": [
            {
                "aegis": m["aegis"],
                "amount": m["amount"],
                "level": m["level"],
                "hp": m["hp"],
                "weight": round(m["amount"] / total, 4),
            }
            for m in sorted(combat, key=lambda x: -x["amount"])[:8]
        ],
        "drop_types_count": len(drops),
        "ev_mats_offer_per_kill": round(ev_kill, 2),
        "ev_mats_offer_per_day": round(ev_kill * kills_day, 2),
        "offer": offer,
        "projection": project_days(
            offer,
            kh["kills_per_hour"] * hours_share,
            costs["zeny_cost_per_hour"] * hours_share,
        ),
    }


def main() -> None:
    print("Loading…")
    mobs = load_mobs()
    items = load_items()
    latam = load_latam()
    npc_buyable = load_npc_buyable_ids()
    sellable_mats = load_sellable_mat_ids()
    print(
        f"  npc_buyable={len(npc_buyable)} sellable_pool_mats={len(sellable_mats)}"
    )
    maps_idx = {m["map"]: m for m in json.loads(MAPS_PATH.read_text())}
    OUT.mkdir(parents=True, exist_ok=True)

    bots_out = []
    for spec in BOTS:
        nmaps = len(spec.maps)
        share = 1.0 / nmaps
        profiles = []
        for map_name in spec.maps:
            spawn = maps_idx.get(map_name)
            if not spawn:
                fail(f"missing map {map_name}")
            profiles.append(
                analyze_map(
                    map_name,
                    spawn,
                    mobs,
                    items,
                    latam,
                    share,
                    npc_buyable,
                    sellable_mats,
                )
            )

        # Merge proyección bot (suma mapas)
        merged_days = {}
        for days in SIM["days"]:
            key = str(days)
            mats_by_id: dict[int, dict] = {}
            cards_by_id: dict[int, dict] = {}
            kills = 0.0
            mats_val = 0.0
            cards_pipe = 0.0
            spend = 0.0
            for mp in profiles:
                proj = mp["projection"][key]
                kills += proj["kills"]
                mats_val += proj["mats_stock_value_latam"]
                cards_pipe += proj["cards_pipeline_value"]
                spend += proj["zeny_spent"]
                for m in proj["mats_stock"]:
                    cur = mats_by_id.get(m["item_id"])
                    if not cur:
                        mats_by_id[m["item_id"]] = dict(m)
                    else:
                        cur["qty"] = round(cur["qty"] + m["qty"], 2)
                        cur["stock_value"] = round(
                            cur["stock_value"] + m["stock_value"], 2
                        )
                for c in proj["cards"]:
                    cur = cards_by_id.get(c["item_id"])
                    if not cur:
                        cards_by_id[c["item_id"]] = dict(c)
                    else:
                        cur["dropped"] = round(cur["dropped"] + c["dropped"], 3)
                        cur["sellable"] = round(cur["sellable"] + c["sellable"], 3)
                        cur["pipeline_value"] = round(
                            cur["pipeline_value"] + c["pipeline_value"], 2
                        )
                        cur["expected_listed"] = min(
                            SIM["card_shop_slots"],
                            cur["sellable"],
                        )
            lot = mats_val + cards_pipe
            merged_days[key] = {
                "days": days,
                "kills": round(kills, 1),
                "mats_stock": sorted(
                    mats_by_id.values(), key=lambda x: -x["stock_value"]
                ),
                "mats_stock_value_latam": round(mats_val, 2),
                "cards": sorted(
                    cards_by_id.values(), key=lambda x: -x["sellable"]
                ),
                "cards_sellable_total": round(
                    sum(c["sellable"] for c in cards_by_id.values()), 3
                ),
                "cards_pipeline_value": round(cards_pipe, 2),
                "lot_expected_value": round(lot, 2),
                "zeny_spent": round(spend, 2),
                "net_if_sold_at_latam": round(lot - spend, 2),
                "gates": {
                    "pause_grind_until_sold_z": round(
                        lot * SIM["pause_grind_until_sold_frac"], 2
                    ),
                    "keep_shop_until_sold_z": round(
                        lot
                        * max(
                            SIM["shop_keep_until_sold_frac"],
                            SIM["shop_keep_until_zeny_frac"],
                        ),
                        2,
                    ),
                },
            }

        bot = {
            "id": spec.id,
            "label": spec.label,
            "tier_target": spec.tier_target,
            "notes": spec.notes,
            "maps": [p["map"] for p in profiles],
            "map_profiles": profiles,
            "projection_merged": merged_days,
            "day10": merged_days["10"],
        }
        bots_out.append(bot)
        (OUT / f"{spec.id}.sim.json").write_text(
            json.dumps(bot, indent=2, ensure_ascii=False) + "\n"
        )
        d10 = merged_days["10"]
        junk = sum(
            len(p["offer"].get("cards_junk_discarded") or []) for p in profiles
        )
        print(
            f"  {spec.id}: kills/10d={d10['kills']:.0f} "
            f"lot={d10['lot_expected_value']:.0f} spend={d10['zeny_spent']:.0f} "
            f"net={d10['net_if_sold_at_latam']:.0f} "
            f"cards={d10['cards_sellable_total']:.2f} junk_cards={junk} "
            f"k/h={[p['kills']['kills_per_hour'] for p in profiles]}"
        )

    summary = {
        "generated": "preview_sim.py",
        "rules": {
            "drop_rates": "1x (OzRo boost = player benefit, not bot)",
            "prices": "LATAM only (offers_median else market_avg)",
            "atlantis": "filter only — not used for pricing",
            "sell_mats": "top score; exclude NPC-buyable; rest discarded",
            "exclude_npc_buyable": True,
            "npc_buyable_source": "staging/market/npc_shops/npc_buyable_ids.txt",
            "sell_cards": "1 of every 2 dropped; max 1 listed; map min_price (prt≥1M)",
            "kills_model": "combat_kills * (1 - travel - restock - idle)",
            "zeny": "spend/hour; pause grind until sold frac of lot; keep shop until sold frac",
            "activity_gate": "see docs/08-activity-gated-bots.md — hours here are potential, not wall-clock",
        },
        "params": SIM,
        "dead_time_frac_total": dead_time_frac(),
        "harvest_plants_excluded": sorted(HARVEST_PLANTS),
        "bot_count": len(bots_out),
        "bots": [
            {
                "id": b["id"],
                "label": b["label"],
                "tier_target": b["tier_target"],
                "maps": b["maps"],
                "per_map": [
                    {
                        "map": p["map"],
                        "tier": p["tier"],
                        "avg_level": p["avg_level"],
                        "avg_hp": p["avg_hp"],
                        "combat_amount": p["combat_amount"],
                        "kills_per_hour_combat": p["kills"]["kills_per_hour_combat"],
                        "kills_per_hour": p["kills"]["kills_per_hour"],
                        "dead_time_frac": p["kills"]["dead_time_frac"],
                        "zeny_cost_per_hour": p["costs"]["zeny_cost_per_hour"],
                        "kills_per_day": p["kills_per_day"],
                        "card_min_price": p["offer"]["card_min_price"],
                        "cards_junk": len(p["offer"].get("cards_junk_discarded") or []),
                        "mats_blocked_pool": p["offer"].get(
                            "mats_blocked_pool_count", 0
                        ),
                        "mats_blocked_npc": p["offer"].get(
                            "mats_blocked_npc_count", 0
                        ),
                        "mats_for_sale": [
                            {
                                "name": m["name"],
                                "price": m["latam_price"],
                                "p": m["p_per_map_kill"],
                                "qty_day": m["qty_per_day"],
                                "score": m["score"],
                            }
                            for m in p["offer"]["mats_for_sale"]
                        ],
                        "cards_top": [
                            {
                                "name": c["name"],
                                "price": c["latam_price"],
                                "sellable_day": c["sellable_per_day"],
                            }
                            for c in p["offer"]["cards"][:3]
                        ],
                    }
                    for p in b["map_profiles"]
                ],
                "projection": {
                    d: {
                        "kills": b["projection_merged"][d]["kills"],
                        "mats_value": b["projection_merged"][d][
                            "mats_stock_value_latam"
                        ],
                        "cards_sellable": b["projection_merged"][d][
                            "cards_sellable_total"
                        ],
                        "cards_pipeline_z": b["projection_merged"][d][
                            "cards_pipeline_value"
                        ],
                        "lot_expected": b["projection_merged"][d][
                            "lot_expected_value"
                        ],
                        "zeny_spent": b["projection_merged"][d]["zeny_spent"],
                        "net": b["projection_merged"][d]["net_if_sold_at_latam"],
                        "pause_until_z": b["projection_merged"][d]["gates"][
                            "pause_grind_until_sold_z"
                        ],
                        "keep_shop_until_z": b["projection_merged"][d]["gates"][
                            "keep_shop_until_sold_z"
                        ],
                        "top_mats": [
                            f"{m['name']}×{m['qty']}"
                            for m in b["projection_merged"][d]["mats_stock"][:5]
                        ],
                    }
                    for d in ["1", "3", "7", "10"]
                },
            }
            for b in bots_out
        ],
    }
    (OUT / "sim_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    print(f"Wrote {OUT}/sim_summary.json + *.sim.json")


if __name__ == "__main__":
    main()
