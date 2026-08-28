# LATAM clásico — análisis profundo (ID &lt; 10k)

Fecha: 2026-08-28  
Filtro: **item_id &lt; 10000** (excluye moderno/custom LATAM; OzRo/Atlantis-like)  
Canvas: `latam-classic-deep-dive.canvas.tsx`

## Resumen

| Set | N |
|-----|---|
| LATAM con precio (todo) | 5,328 |
| **Clásicos ID &lt; 10k** | **1,833** |
| Excluidos ID ≥ 10k | 3,495 |
| Bot focus limpio | 202 |
| Gaps Atlantis a fetch (con offers) | 744 |

## Proporciones LATAM ÷ Atlantis (pares limpios)

| Grupo | N | Ratio mediano | Lectura |
|-------|---|---------------|---------|
| etc | 203 | **0.98** | casi 1:1 — mats confiables |
| consumable | 26 | **1.21** | LATAM un poco más caro |
| card | 86 | 0.54 | LATAM ~mitad |
| equip_weapon | 29 | 0.47 | LATAM más barato |
| equip_armor | 24 | 0.26 | LATAM mucho más barato |
| equip_acc | 22 | 0.17 | LATAM muy barato |

El “0.6× global” era promedio mezclado. **Para farm (etc) no hay dump de precio.**

## Regla de precios (bots)

```
sell = LATAM offers_median
buy  = max(NPC_sell_YAML, sell * 0.7)
si ratio L/A fuera de [0.3, 2.0] → outlier (no usar Atlantis avg a ciegas)
```

## Atlantis: por qué faltaban / qué falta

1. **1,267 del top2000 sin data** — casi todos ID ≥ 10k (modernos). Esperable.
2. **62 clásicos sin data** (Ogre Tooth, Tree Root…) — Atlantis no tiene historial; usar LATAM.
3. **1,265 clásicos nunca pedidos** (fuera del top2000 LATAM) — de ellos **744 con offers**; fetch prioritario.

## Archivos generados

| Archivo | Uso |
|---------|-----|
| `classic_lt10k_ids.txt` / `classic_lt10k_ranked.json` | Universo clásico |
| `bot_focus_classic.json` / `_ids.txt` | 202 ítems para bots |
| `atlantis_fetch_priority_offers.txt` | 744 a bajar de Atlantis |
| `atlantis_fetch_classic_gaps.txt` | 1,265 gaps totales |
| `classic_analysis_summary.json` | Métricas |

## Próximo comando

```bash
python staging/market/fetch_batch.py atlantis \
  --items-file staging/market/latam_tools/curated/atlantis_fetch_priority_offers.txt \
  --resume
```
