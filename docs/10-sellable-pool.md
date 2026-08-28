# Pool vendible de bots (regla global)

Fecha: 2026-08-28  
Scripts:
```bash
python staging/market/bots/build_sellable_pool.py
python staging/market/bots/preview_sim.py
```

## Por qué

Los 10 bots de prueba no son el universo. Habrá **muchos** perfiles; el progreso debe ser **lento**.  
La oferta se decide con un **pool global**, no con hacks por bot.

## Embudo

```
grindable (926)
  − npc_buyable          → fuera Phracon/Meat/Zargon/Jellopy…
  − tipo ≠ mats          → fuera cards/equip (cards tienen regla aparte)
  − sin precio LATAM
  − price > 16_000       → fuera Orange@30k, Grape@193k…
  − price≥5000 y LATAM/Buy > 80  → fuera Feather@10k (Buy=20)
  − sold < 80
= ~108 mats vendibles
```

Cards: siguen reglas propias en `preview_sim` (1/2, min price por mapa, etc.).

## Reglas clave (`pool/sellable_rules.json`)

| Regla | Valor | Efecto |
|-------|-------|--------|
| `exclude_npc_buyable` | true | no compite con NPC |
| `mats_max_price` | 16 000 | Tooth of Bat OK; Orange OUT |
| `markup_only_if_price_ge` | 5 000 | no castiga herbs baratas |
| `max_markup_vs_yaml_buy` | 80 | Feather/Lemon/etc. OUT |
| `mats_top_n` (sim) | 4 | pocas cosas útiles por tienda |

## Muestra ×10 tras pool

| Bot | Mats |
|-----|------|
| Prontera | Clover, Fluff, Green Herb (+ …) |
| Spore | Red Herb, Strawberry, Mushroom Spore, Venom Canine |
| Bigfoot | Footskin, Quill, Honey |
| Orco / Gator / etc. | mats temáticos del pool |

Feather **OUT**, Orange **OUT**.

## Escalar a muchos bots

1. Elegir mapas del `map_tier_catalog` (novice→mid; hard tarde).
2. Intersectar drops del mapa ∩ `sellable_mat_ids`.
3. Si el mapa queda con &lt;2 mats vendibles → no usar ese mapa (o solo cards).
4. Replicar plantillas × N con offsets de precio/stock.

Así el catálogo crece sin reintroducir basura LATAM/NPC.
