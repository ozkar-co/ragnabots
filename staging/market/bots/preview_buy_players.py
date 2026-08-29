#!/usr/bin/env python3
"""Preview del job nocturno: bots compran a tiendas de jugadores.

Regla de oro:
  price > LATAM (offers_median else market_avg) → P=0 (nunca)

Probabilidad de intentar/completar compra (si price ≤ LATAM):
  ratio = price / latam
  P = p_max * (1 - ratio)^k     # barato → fácil; cerca del techo → difícil

Uso:
  python staging/market/bots/preview_buy_players.py
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "buy_preview"
LATAM = ROOT / "staging/market/latam_tools/curated/ranked_market.json"
POOL = ROOT / "staging/market/bots/pool/sellable_mats.json"

BUY = {
    "p_max": 0.85,  # techo de probabilidad (baratísimo)
    "k": 1.15,  # suave: facilitar venta; subir k = más exigente
    # Job nocturno
    "n_buyer_bots": (4, 10),
    "listings_per_bot": (2, 5),
    "qty_frac_of_stock": (0.05, 0.40),
    "qty_min": 1,
    "qty_max_hard": 80,
    "max_spend_frac_zeny": 0.30,
    "max_spend_absolute": 3_000_000,
    "bot_zeny_start": (80_000, 800_000),
    "monte_carlo_nights": 50,
    "seed": 42,
}


def latam_price(row: dict) -> int | None:
    if row.get("offers_median") is not None:
        return int(row["offers_median"])
    if row.get("market_avg") is not None:
        return int(row["market_avg"])
    return None


def buy_probability(price: float, latam: float) -> float:
    if latam <= 0:
        return 0.0
    if price > latam:
        return 0.0
    ratio = price / latam
    return BUY["p_max"] * ((1.0 - ratio) ** BUY["k"])


def main() -> None:
    random.seed(BUY["seed"])
    latam_rows = {
        r["item_id"]: r for r in json.loads(LATAM.read_text())
    }
    pool = json.loads(POOL.read_text())
    # Fake player shops: sample pool items at various markups vs LATAM
    listings = []
    for m in pool[:40]:
        ref = m["latam_price"]
        for mult, label in [
            (0.35, "ganga"),
            (0.55, "barato"),
            (0.75, "ok"),
            (0.92, "cerca_techo"),
            (1.05, "sobre_latam"),
        ]:
            price = max(1, int(ref * mult))
            stock = random.randint(10, 200)
            p = buy_probability(price, ref)
            listings.append(
                {
                    "item_id": m["item_id"],
                    "name": m["name"],
                    "latam": ref,
                    "player_price": price,
                    "mult": mult,
                    "label": label,
                    "stock": stock,
                    "p_buy": round(p, 4),
                }
            )

    # Curve table
    curve = []
    for pct in range(20, 105, 5):
        ratio = pct / 100.0
        price = 1000 * ratio
        curve.append(
            {
                "price_vs_latam_pct": pct,
                "p_buy": round(buy_probability(price, 1000), 4),
            }
        )

    # Simulate many nights for expected volume
    night_stats = []
    for night in range(BUY["monte_carlo_nights"]):
        n_bots = random.randint(*BUY["n_buyer_bots"])
        bought_value = 0
        bought_lines = 0
        skipped = {"over_latam": 0, "fail_roll": 0, "no_zeny": 0}
        events = []
        for _ in range(n_bots):
            zeny = random.randint(*BUY["bot_zeny_start"])
            budget = min(
                int(zeny * BUY["max_spend_frac_zeny"]),
                BUY["max_spend_absolute"],
                zeny,
            )
            spent = 0
            n_look = random.randint(*BUY["listings_per_bot"])
            picks = random.sample(listings, min(n_look, len(listings)))
            for listing in picks:
                if listing["player_price"] > listing["latam"]:
                    skipped["over_latam"] += 1
                    continue
                if random.random() > listing["p_buy"]:
                    skipped["fail_roll"] += 1
                    continue
                lo, hi = BUY["qty_frac_of_stock"]
                qty = int(listing["stock"] * random.uniform(lo, hi))
                qty = max(
                    BUY["qty_min"], min(qty, BUY["qty_max_hard"], listing["stock"])
                )
                cost = qty * listing["player_price"]
                if cost > budget - spent:
                    max_afford = (budget - spent) // listing["player_price"]
                    if max_afford < 1:
                        skipped["no_zeny"] += 1
                        continue
                    qty = min(qty, max_afford)
                    cost = qty * listing["player_price"]
                spent += cost
                bought_value += cost
                bought_lines += 1
                if night == 0:
                    events.append(
                        {
                            "item": listing["name"],
                            "label": listing["label"],
                            "price": listing["player_price"],
                            "latam": listing["latam"],
                            "p_buy": listing["p_buy"],
                            "qty": qty,
                            "cost": cost,
                        }
                    )
        night_stats.append(
            {
                "buyer_bots": n_bots,
                "purchase_lines": bought_lines,
                "zeny_spent": bought_value,
                "skipped": skipped,
            }
        )

    avg_lines = sum(n["purchase_lines"] for n in night_stats) / len(night_stats)
    avg_zeny = sum(n["zeny_spent"] for n in night_stats) / len(night_stats)
    nights_with_buy = sum(1 for n in night_stats if n["purchase_lines"] > 0)

    OUT.mkdir(parents=True, exist_ok=True)
    summary = {
        "rules": BUY,
        "formula": "P = p_max * (1 - price/latam)^k ; P=0 if price>latam",
        "curve": curve,
        "listing_examples": [
            {k: L[k] for k in ("name", "latam", "player_price", "mult", "label", "p_buy")}
            for L in listings[::5][:15]
        ],
        "night_0_sample": {
            **night_stats[0],
            "events_sample": events[:25],
        },
        "monte_carlo": {
            "nights": BUY["monte_carlo_nights"],
            "avg_purchase_lines": round(avg_lines, 2),
            "avg_zeny_spent": round(avg_zeny, 2),
            "nights_with_at_least_one_buy": nights_with_buy,
            "pct_nights_active": round(100 * nights_with_buy / len(night_stats), 1),
        },
    }
    (OUT / "buy_preview.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )

    print("Curve (price% LATAM → P):")
    for row in curve:
        bar = "#" * int(row["p_buy"] * 40)
        print(f"  {row['price_vs_latam_pct']:3}%  P={row['p_buy']:.2f}  {bar}")
    print(
        f"\nMonte Carlo {BUY['monte_carlo_nights']} nights: "
        f"avg {avg_lines:.1f} compras/noche, avg {avg_zeny:.0f}z, "
        f"{nights_with_buy}/{len(night_stats)} noches con ≥1 compra"
    )
    print(f"Night0: {night_stats[0]}")
    print(f"Wrote {OUT}/buy_preview.json")


if __name__ == "__main__":
    main()
