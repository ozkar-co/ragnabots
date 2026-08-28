# Preview sim bots — rates 1× · LATAM · kills/h · días

Fecha: 2026-08-28  
Script: `staging/market/bots/preview_sim.py`  
Salida: `staging/market/bots/sample/sim_summary.json` + `*.sim.json`

## Reglas acordadas

| Regla | Implementación |
|-------|----------------|
| Drop rates | **1×** (OzRo boost = beneficio jugadores, no bots) |
| Precios | **Solo LATAM** (`offers_median`, si no `market_avg`) |
| Atlantis | Solo filtro histórico de ítems — **no pricing** |
| Oferta mats | Top por `price × log(qty/día) × log(latam_sold)`; resto **descartado** |
| Cartas | Vende **1 de cada 2**; **máx. 1** listada en shop a la vez |
| Kills/h | `uptime(amount) × 3600 / (avg_hp/dPS + overhead)` |
| Horizonte | Proyección **1 / 3 / 7 / 10** días → calibrar |

## Parámetros actuales (`SIM` en el script)

```
dps=200  overhead=2.5s  dead_time=20% (travel 8% + restock 7% + idle 5%)
hours_per_day=3.5  mats_top_n=5  mats_max_price=100k
card_sell_fraction=0.5  card_shop_slots=1
prt_fild*: card_min_price=1M (junk out)
zeny_cost = (3000 + 2×avg_hp)/h × combat_frac
pause_grind @ 40% lote vendido · keep_shop @ 60%
```

**Runtime:** batch 1×/día; horas solo si hubo login ese día — [08-activity-gated-bots.md](08-activity-gated-bots.md).

## Kills/h efectivos (tras dead time 20%)

| Bot | Mapa | Combat k/h | Efectivo |
|-----|------|------------|----------|
| 01 Prontera | prt_fild08 | 1200 | **960** |
| 07 Argiope | mjolnir_11 | ~204 | **~163** |
| 10 Sewers | gl_sew04 | ~46 | **~37** |

Prontera: **4 cartas junk** descartadas (&lt;1M); queda Pupa Card (~1.9M) a ritmo muy bajo (~0.09 sellable / 10d).

## Proyección 10d (lote / spend / net)

| Bot | Lote esp. | Spend | Net | Cards | Pause@40% |
|-----|-----------|-------|-----|-------|-----------|
| 01 Prontera | ~130M | ~0.15M | ~130M | 0.09 | ~52M |
| 06 Orco | ~14M | ~0.27M | ~14M | 0.75 | ~5.5M |
| 09 Gator | ~4.9M | ~0.44M | ~4.5M | 0.39 | ~2.0M |
| 10 Sewers | ~2.4M | ~1.6M | ~0.76M | 0.09 | ~0.9M |

Sewers: gasto alto vs loot → candidato a descartar del pool generalista.

## Qué mirar para ajustar

1. ¿`hours_per_day=6` es demasiado? Probar 3–4.
2. ¿Cards en novice? Quizá `card_sell_fraction=0` bajo avg_lv≤20.
3. ¿Feather/Jellopy en oferta? Subir `mats_min_price` o exigir más `total_sold` relativo.
4. Cap kills 1200 aplasta diferencia en ultra-low HP — bajar `dps` o el cap si queremos más realismo newbie.

## Archivos

```bash
python staging/market/bots/preview_sim.py
```

- `sim_summary.json` — panorama
- `0N_*.sim.json` — detalle por bot (drops, descartados, proyección)
- Diseño estático previo: `design_sample.py` (referencia; pricing viejo OzRo/Atlantis)
