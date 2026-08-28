#!/usr/bin/env python3
"""Diseño pre-simulación: 10 bots muestra × mapas × drops ponderados × precios.

No simula kills/hora. Calcula:
  - dificultad del mapa (nivel ponderado por cantidad de spawn)
  - lista de mobs (lv, hp, amount)
  - P(item | kill en mapa) = Σ (amount_i / total) × min(1, rate×OzRo / 10000)
  - valor comercial Atlantis (avg) y LATAM (offers_median)

Uso:
  python staging/market/bots/design_sample.py
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "sample"

RATES_PATH = ROOT / "data/raw/server_rates.json"
MOB_RE = ROOT / "data/raw/rathena/db/re/mob_db.yml"
MOB_IMPORT = ROOT / "data/raw/rathena/db/import/mob_db.yml"
ITEM_FILES = [
    ROOT / "data/raw/rathena/db/re/item_db_usable.yml",
    ROOT / "data/raw/rathena/db/re/item_db_equip.yml",
    ROOT / "data/raw/rathena/db/re/item_db_etc.yml",
    ROOT / "data/raw/rathena/db/import/item_db.yml",
]
MAPS_PATH = ROOT / "staging/market/spawns/maps_by_amount.json"
ATLANTIS = ROOT / "staging/market/atlantis_playro/curated/ranked_atlantis.json"
LATAM = ROOT / "staging/market/latam_tools/curated/ranked_market.json"
GRINDABLE = ROOT / "staging/market/atlantis_playro/curated/grindable.json"

# Rate YAML: 100 = 1x. Drop Rate en mob_db es /10000.
RATE_KEYS = {
    "common": "item_rate_common",
    "heal": "item_rate_heal",
    "use": "item_rate_use",
    "equip": "item_rate_equip",
    "card": "item_rate_card",
}

# Item Type (rAthena) → bucket de rate OzRo
TYPE_BUCKET = {
    "Healing": "heal",
    "Usable": "use",
    "Delayconsume": "use",
    "Cash": "use",
    "Card": "card",
    "Armor": "equip",
    "Weapon": "equip",
    "Shadowgear": "equip",
    "Ammo": "common",
    "Etc": "common",
    "Petegg": "common",
    "Petarmor": "equip",
}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def load_yaml_body(path: Path) -> list[dict]:
    if not path.exists():
        fail(f"missing {path}")
    data = yaml.safe_load(path.read_text())
    return list((data or {}).get("Body") or [])


def tier_of(avg_lv: float) -> str:
    if avg_lv <= 20:
        return "novice"
    if avg_lv <= 40:
        return "easy"
    if avg_lv <= 70:
        return "mid"
    if avg_lv <= 100:
        return "hard"
    return "expert"


# Plantas de harvest / decorativas (no grind de combate).
# NO usar Race=Plant: en renewal Poring/Spore/Flora/etc. son Plant y sí se farmean.
HARVEST_PLANTS = {
    "RED_PLANT",
    "BLUE_PLANT",
    "GREEN_PLANT",
    "YELLOW_PLANT",
    "WHITE_PLANT",
    "SHINING_PLANT",
    "BLACK_MUSHROOM",
    "RED_MUSHROOM",
}


def is_harvest_plant(mob: dict) -> bool:
    name = (mob.get("AegisName") or "").upper()
    return name in HARVEST_PLANTS


@dataclass(frozen=True)
class BotSpec:
    id: str
    label: str
    maps: tuple[str, ...]
    tier_target: str
    loot_policy: str  # full | restricted | deferred
    notes: str


# Muestreo intencional: ~10 perfiles, escalables a ~20 plantillas × repetición → ~100.
BOTS: list[BotSpec] = [
    BotSpec(
        "01_poring_field",
        "Campo Prontera (newbie)",
        ("prt_fild08",),
        "novice",
        "full",
        "Loot denso clásico; referencia de volumen bajo valor.",
    ),
    BotSpec(
        "02_pay_spore",
        "Campo Payon (spore)",
        ("pay_fild08",),
        "novice",
        "full",
        "Segundo newbie; Spore/etc de Payon.",
    ),
    BotSpec(
        "03_desert_muka",
        "Desierto Muka",
        ("moc_fild01",),
        "easy",
        "full",
        "Alta densidad Muka/Peco; mats desierto.",
    ),
    BotSpec(
        "04_ant_hell",
        "Ant Hell",
        ("anthell01",),
        "easy",
        "full",
        "Dungeon fácil; huevos/hormigas.",
    ),
    BotSpec(
        "05_pay_bigfoot",
        "Payon Bigfoot",
        ("pay_fild07",),
        "easy",
        "full",
        "Campo mid-bajo; Bigfoot/Caramel.",
    ),
    BotSpec(
        "06_orc_village",
        "Aldea Orco",
        ("gef_fild10", "orcsdun01"),
        "mid",
        "full",
        "Dos mapas tema orco (campo + dungeon).",
    ),
    BotSpec(
        "07_mjolnir_spider",
        "Mjolnir Argiope",
        ("mjolnir_11",),
        "mid",
        "full",
        "Spiders densas; buen mix etc/card potencial.",
    ),
    BotSpec(
        "08_izlude_dungeon",
        "Byalan / Izlude Dun",
        ("iz_dun01",),
        "mid",
        "full",
        "Dungeon acuático clásico.",
    ),
    BotSpec(
        "09_comodo_gator",
        "Comodo Alligator",
        ("cmd_fild03",),
        "mid",
        "full",
        "Alligator/Anolian skin zona; alto volumen Atlantis histórico.",
    ),
    BotSpec(
        "10_sewers_anolian",
        "Glast Heim Sewers (restringido)",
        ("gl_sew04",),
        "expert",
        "restricted",
        "Hard/expert: solo mats/etc con mercado; sin equip raro ni cards "
        "como oferta masiva. Ejemplo de política restrictiva.",
    ),
]


def load_mobs() -> dict[int, dict]:
    mobs = {m["Id"]: m for m in load_yaml_body(MOB_RE)}
    for m in load_yaml_body(MOB_IMPORT):
        mid = m["Id"]
        mobs[mid] = {**mobs.get(mid, {}), **m}
    return mobs


def load_items() -> dict[str, dict]:
    """AegisName → {id, name, type, bucket, buy}."""
    by_name: dict[str, dict] = {}
    for path in ITEM_FILES:
        if not path.exists():
            continue
        for it in load_yaml_body(path):
            aegis = it.get("AegisName")
            if not aegis:
                continue
            itype = it.get("Type") or "Etc"
            by_name[aegis] = {
                "item_id": it["Id"],
                "name": it.get("Name") or aegis,
                "type": itype,
                "bucket": TYPE_BUCKET.get(itype, "common"),
                "npc_buy": it.get("Buy"),
            }
    if not by_name:
        fail("no items loaded")
    return by_name


def load_prices() -> tuple[dict[int, dict], dict[int, dict]]:
    at = {r["item_id"]: r for r in json.loads(ATLANTIS.read_text())}
    lt = {r["item_id"]: r for r in json.loads(LATAM.read_text())}
    return at, lt


def load_rates() -> dict[str, float]:
    raw = json.loads(RATES_PATH.read_text())["rates"]
    return {k: raw[RATE_KEYS[k]] / 100.0 for k in RATE_KEYS}


def effective_p(rate_raw: int, mult: float) -> float:
    """Probabilidad por kill tras rates OzRo, capped a 1.0."""
    return min(1.0, (rate_raw * mult) / 10000.0)


def analyze_map(
    map_name: str,
    spawn: dict,
    mobs: dict[int, dict],
    items: dict[str, dict],
    rates: dict[str, float],
    at: dict[int, dict],
    lt: dict[int, dict],
    *,
    exclude_plants: bool = True,
) -> dict[str, Any]:
    combat_mobs: list[dict] = []
    skipped_plants: list[dict] = []
    missing_mob: list[int] = []

    for sm in spawn["mobs"]:
        mid = sm["mob_id"]
        mob = mobs.get(mid)
        if not mob:
            missing_mob.append(mid)
            continue
        entry = {
            "mob_id": mid,
            "aegis": mob.get("AegisName") or sm["name"],
            "name": mob.get("Name") or sm["name"],
            "amount": sm["amount"],
            "level": mob.get("Level", 1),
            "hp": mob.get("Hp", 1),
            "race": mob.get("Race"),
            "element": mob.get("Element"),
            "is_harvest_plant": is_harvest_plant(mob),
            "drops": mob.get("Drops") or [],
        }
        if exclude_plants and entry["is_harvest_plant"]:
            skipped_plants.append(entry)
        else:
            combat_mobs.append(entry)

    total = sum(m["amount"] for m in combat_mobs)
    if total <= 0:
        fail(f"map {map_name}: no combat mobs after plant filter")

    wlvl = sum(m["amount"] * m["level"] for m in combat_mobs)
    whp = sum(m["amount"] * m["hp"] for m in combat_mobs)
    avg_lv = wlvl / total
    avg_hp = whp / total
    max_lv = max(m["level"] for m in combat_mobs)

    # Drops por mob: sumar rates del mismo AegisName (slots duplicados)
    # Luego ponderar por amount/total.
    item_acc: dict[int, dict[str, Any]] = {}

    for m in combat_mobs:
        weight = m["amount"] / total
        rates_by_aegis: dict[str, int] = defaultdict(int)
        for d in m["drops"]:
            aegis = d.get("Item")
            if not aegis:
                continue
            rates_by_aegis[aegis] += int(d.get("Rate") or 0)

        mob_drop_list = []
        for aegis, rate_raw in rates_by_aegis.items():
            meta = items.get(aegis)
            if not meta:
                continue
            bucket = meta["bucket"]
            mult = rates[bucket]
            p_kill = effective_p(rate_raw, mult)
            p_map = weight * p_kill
            iid = meta["item_id"]
            mob_drop_list.append(
                {
                    "item_id": iid,
                    "aegis": aegis,
                    "name": meta["name"],
                    "type": meta["type"],
                    "bucket": bucket,
                    "rate_raw": rate_raw,
                    "rate_mult": mult,
                    "p_per_kill_this_mob": round(p_kill, 6),
                }
            )
            acc = item_acc.get(iid)
            if not acc:
                acc = {
                    "item_id": iid,
                    "aegis": aegis,
                    "name": meta["name"],
                    "type": meta["type"],
                    "bucket": bucket,
                    "npc_buy": meta.get("npc_buy"),
                    "p_per_map_kill": 0.0,
                    "contributors": [],
                }
                item_acc[iid] = acc
            acc["p_per_map_kill"] += p_map
            acc["contributors"].append(
                {
                    "mob_id": m["mob_id"],
                    "aegis": m["aegis"],
                    "amount": m["amount"],
                    "weight": round(weight, 4),
                    "rate_raw": rate_raw,
                    "p_mob": round(p_kill, 6),
                    "p_contrib": round(p_map, 6),
                }
            )

        m["drop_summary"] = sorted(
            mob_drop_list, key=lambda x: -x["p_per_kill_this_mob"]
        )

    drops_out = []
    for acc in item_acc.values():
        iid = acc["item_id"]
        a = at.get(iid)
        l = lt.get(iid)
        p = acc["p_per_map_kill"]
        at_avg = a.get("avg") if a else None
        lt_med = l.get("offers_median") if l else None
        row = {
            **acc,
            "p_per_map_kill": round(p, 8),
            "atlantis_avg": at_avg,
            "atlantis_total_sold": a.get("total_sold") if a else None,
            "latam_offers_median": lt_med,
            "ev_atlantis_per_kill": round(p * at_avg, 2) if at_avg is not None else None,
            "ev_latam_per_kill": round(p * lt_med, 2) if lt_med is not None else None,
            "in_atlantis": a is not None,
            "in_latam": l is not None,
        }
        drops_out.append(row)

    drops_out.sort(
        key=lambda r: (
            -(r["ev_atlantis_per_kill"] or 0),
            -r["p_per_map_kill"],
        )
    )

    ev_at = sum(r["ev_atlantis_per_kill"] or 0 for r in drops_out)
    ev_lt = sum(r["ev_latam_per_kill"] or 0 for r in drops_out)
    priced = sum(1 for r in drops_out if r["in_atlantis"] or r["in_latam"])

    return {
        "map": map_name,
        "spawn_total_raw": spawn["total_amount"],
        "combat_total_amount": total,
        "plants_excluded_amount": sum(p["amount"] for p in skipped_plants),
        "plants_excluded": [
            {"aegis": p["aegis"], "amount": p["amount"]} for p in skipped_plants
        ],
        "missing_mob_ids": missing_mob,
        "avg_level": round(avg_lv, 2),
        "max_level": max_lv,
        "avg_hp": int(avg_hp),
        "tier": tier_of(avg_lv),
        "mobs": [
            {
                "mob_id": m["mob_id"],
                "aegis": m["aegis"],
                "name": m["name"],
                "amount": m["amount"],
                "weight": round(m["amount"] / total, 4),
                "level": m["level"],
                "hp": m["hp"],
                "race": m["race"],
                "element": m["element"],
                "drop_count": len(m["drop_summary"]),
                "drops": m["drop_summary"],
            }
            for m in sorted(combat_mobs, key=lambda x: -x["amount"])
        ],
        "drop_count": len(drops_out),
        "drop_priced_count": priced,
        "ev_atlantis_per_kill": round(ev_at, 2),
        "ev_latam_per_kill": round(ev_lt, 2),
        "drops": drops_out,
        "drops_top20": drops_out[:20],
    }


def apply_loot_policy(map_profile: dict, policy: str) -> dict:
    """Filtra drops visibles según política del bot (no cambia spawns)."""
    drops = map_profile["drops"]

    def mats_only(ds: list) -> list:
        return [
            d
            for d in ds
            if d["type"] in {"Etc", "Healing", "Usable", "Delayconsume", "Ammo"}
            and (d["in_atlantis"] or d["in_latam"])
        ]

    def no_card_equip(ds: list) -> list:
        return [
            d
            for d in ds
            if d["type"] not in {"Card", "Armor", "Weapon", "Shadowgear", "Petarmor"}
            and (d["in_atlantis"] or d["in_latam"])
        ]

    if policy == "full":
        # Oferta realista para generalistas: mats/consumibles con precio.
        # Card/equip se listan en el perfil completo pero no como stock masivo.
        kept = mats_only(drops)
        reason = (
            "oferta bot = mats/consumibles con precio; "
            "cards/equip quedan fuera del stock masivo (ver drops completos)"
        )
    elif policy == "restricted":
        kept = mats_only(drops)
        # Aún más estricto en expert: solo Etc con Atlantis total_sold alto si existe
        kept = [
            d
            for d in kept
            if d["type"] == "Etc"
            and (d.get("atlantis_total_sold") or 0) >= 1000
        ]
        reason = (
            "expert/hard: solo Etc con volumen Atlantis≥1k; sin consumibles/card/equip"
        )
    elif policy == "deferred":
        kept = []
        reason = "mapa diferido — no grindear con bots generalistas"
    else:
        fail(f"unknown loot_policy {policy}")

    ev_at = sum(d["ev_atlantis_per_kill"] or 0 for d in kept)
    ev_lt = sum(d["ev_latam_per_kill"] or 0 for d in kept)
    # Referencia: EV si vendiéramos TODO (inflado por cards 100x)
    ev_at_all = sum(d["ev_atlantis_per_kill"] or 0 for d in drops)
    mats = mats_only(drops)
    cards = [d for d in drops if d["type"] == "Card"]
    return {
        "policy": policy,
        "policy_reason": reason,
        "offer_drop_count": len(kept),
        "ev_atlantis_per_kill_offer": round(ev_at, 2),
        "ev_latam_per_kill_offer": round(ev_lt, 2),
        "ev_atlantis_per_kill_all_drops": round(ev_at_all, 2),
        "ev_atlantis_per_kill_mats_only": round(
            sum(d["ev_atlantis_per_kill"] or 0 for d in mats), 2
        ),
        "card_count": len(cards),
        "ev_atlantis_cards": round(
            sum(d["ev_atlantis_per_kill"] or 0 for d in cards), 2
        ),
        "offer_drops_top30": kept[:30],
        "offer_item_ids": [d["item_id"] for d in kept],
        "top_cards": [
            {
                "item_id": d["item_id"],
                "name": d["name"],
                "p": d["p_per_map_kill"],
                "atlantis_avg": d["atlantis_avg"],
                "ev_at": d["ev_atlantis_per_kill"],
            }
            for d in cards[:5]
        ],
    }


def main() -> None:
    for p in [RATES_PATH, MOB_RE, MAPS_PATH, ATLANTIS, LATAM]:
        if not p.exists():
            fail(f"missing {p}")

    print("Loading mobs/items/prices…")
    mobs = load_mobs()
    items = load_items()
    rates = load_rates()
    at, lt = load_prices()
    maps_idx = {m["map"]: m for m in json.loads(MAPS_PATH.read_text())}
    grindable_ids = {r["item_id"] for r in json.loads(GRINDABLE.read_text())}

    OUT.mkdir(parents=True, exist_ok=True)

    bots_out = []
    for spec in BOTS:
        map_profiles = []
        for map_name in spec.maps:
            spawn = maps_idx.get(map_name)
            if not spawn:
                fail(f"bot {spec.id}: map {map_name} not in spawns")
            profile = analyze_map(
                map_name, spawn, mobs, items, rates, at, lt, exclude_plants=True
            )
            policy_view = apply_loot_policy(profile, spec.loot_policy)
            # Marcar grindable overlap
            for d in profile["drops"]:
                d["in_grindable"] = d["item_id"] in grindable_ids
            map_profiles.append({**profile, "loot": policy_view})

        # Bot-level merge of offer items across maps (union)
        offer_ids: set[int] = set()
        for mp in map_profiles:
            offer_ids.update(mp["loot"]["offer_item_ids"])

        bots_out.append(
            {
                "id": spec.id,
                "label": spec.label,
                "tier_target": spec.tier_target,
                "loot_policy": spec.loot_policy,
                "notes": spec.notes,
                "maps": [mp["map"] for mp in map_profiles],
                "map_tiers": [mp["tier"] for mp in map_profiles],
                "map_avg_levels": [mp["avg_level"] for mp in map_profiles],
                "offer_item_count": len(offer_ids),
                "ev_atlantis_per_kill_by_map": [
                    mp["loot"]["ev_atlantis_per_kill_offer"] for mp in map_profiles
                ],
                "ev_latam_per_kill_by_map": [
                    mp["loot"]["ev_latam_per_kill_offer"] for mp in map_profiles
                ],
                "map_profiles": map_profiles,
            }
        )
        # Per-bot file (full detail)
        (OUT / f"{spec.id}.json").write_text(
            json.dumps(bots_out[-1], indent=2, ensure_ascii=False) + "\n"
        )
        print(
            f"  {spec.id}: maps={spec.maps} tiers={bots_out[-1]['map_tiers']} "
            f"offer_items={len(offer_ids)} "
            f"EV_at={bots_out[-1]['ev_atlantis_per_kill_by_map']}"
        )

    summary = {
        "generated": "design_sample.py",
        "assumptions": {
            "kill_weight": "proportional to spawn amount (harvest plants excluded only)",
            "harvest_plants_excluded": sorted(HARVEST_PLANTS),
            "note_race_plant": "Race=Plant NO se excluye (Poring/Spore/Flora son grindables)",
            "drop_formula": "P = Σ (amount_i/total) * min(1, rate_raw * ozro_mult / 10000)",
            "ozro_mults": rates,
            "prices": {
                "atlantis": "avg from ranked_atlantis",
                "latam": "offers_median from ranked_market",
            },
            "difficulty": {
                "novice": "avg_lv ≤ 20",
                "easy": "21–40",
                "mid": "41–70",
                "hard": "71–100",
                "expert": ">100",
            },
            "ev_caveat": (
                "EV Atlantis con policy=full está inflado por cards (100x) y "
                "equip (15x) × precios avg altos/ruidosos; usar policy "
                "restricted o EV solo-Etc para oferta de bot realista"
            ),
            "scale_plan": "10 sample → ~20 templates × replicas ≈ 100 bots; not all active",
        },
        "bot_count": len(bots_out),
        "bots": [
            {
                "id": b["id"],
                "label": b["label"],
                "tier_target": b["tier_target"],
                "loot_policy": b["loot_policy"],
                "maps": b["maps"],
                "map_tiers": b["map_tiers"],
                "map_avg_levels": b["map_avg_levels"],
                "offer_item_count": b["offer_item_count"],
                "ev_atlantis_per_kill_by_map": b["ev_atlantis_per_kill_by_map"],
                "ev_latam_per_kill_by_map": b["ev_latam_per_kill_by_map"],
                "ev_atlantis_all_by_map": [
                    mp["loot"]["ev_atlantis_per_kill_all_drops"]
                    for mp in b["map_profiles"]
                ],
                "ev_atlantis_cards_by_map": [
                    mp["loot"]["ev_atlantis_cards"] for mp in b["map_profiles"]
                ],
                "notes": b["notes"],
                # compact top drops per map for overview
                "maps_top_drops": [
                    {
                        "map": mp["map"],
                        "tier": mp["tier"],
                        "avg_level": mp["avg_level"],
                        "avg_hp": mp["avg_hp"],
                        "combat_amount": mp["combat_total_amount"],
                        "top_mobs": [
                            {
                                "aegis": m["aegis"],
                                "amount": m["amount"],
                                "level": m["level"],
                                "hp": m["hp"],
                            }
                            for m in mp["mobs"][:5]
                        ],
                        "top_offer": [
                            {
                                "item_id": d["item_id"],
                                "name": d["name"],
                                "type": d["type"],
                                "p": d["p_per_map_kill"],
                                "atlantis_avg": d["atlantis_avg"],
                                "latam_median": d["latam_offers_median"],
                                "ev_at": d["ev_atlantis_per_kill"],
                            }
                            for d in mp["loot"]["offer_drops_top30"][:8]
                        ],
                        "top_cards": mp["loot"]["top_cards"],
                    }
                    for mp in b["map_profiles"]
                ],
            }
            for b in bots_out
        ],
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )

    # Catalog of all maps by tier (for scaling to 20 templates)
    tier_catalog = defaultdict(list)
    for spawn in maps_idx.values():
        combat = []
        for sm in spawn["mobs"]:
            mob = mobs.get(sm["mob_id"])
            if not mob or is_harvest_plant(mob):
                continue
            combat.append((sm["amount"], mob.get("Level", 1), mob.get("Hp", 1)))
        if not combat:
            continue
        total = sum(a for a, _, _ in combat)
        avg_lv = sum(a * lv for a, lv, _ in combat) / total
        avg_hp = sum(a * hp for a, _, hp in combat) / total
        t = tier_of(avg_lv)
        if total < 40:
            continue
        tier_catalog[t].append(
            {
                "map": spawn["map"],
                "combat_amount": total,
                "avg_level": round(avg_lv, 1),
                "avg_hp": int(avg_hp),
                "max_level": max(lv for _, lv, _ in combat),
            }
        )
    for t in tier_catalog:
        tier_catalog[t].sort(key=lambda x: -x["combat_amount"])
    catalog = {
        "note": "Mapas candidatos (≥40 combat spawns, plants excluidos) por tier",
        "counts": {t: len(v) for t, v in tier_catalog.items()},
        "top_by_tier": {t: v[:25] for t, v in tier_catalog.items()},
    }
    (OUT / "map_tier_catalog.json").write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"
    )

    print(f"Wrote {OUT}/ ({len(bots_out)} bots + summary + catalog)")


if __name__ == "__main__":
    main()
