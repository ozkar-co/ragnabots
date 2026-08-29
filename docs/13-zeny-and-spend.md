# Zeny interno y spend (gasto de combate)

Fecha: 2026-08-28  
Estado: **diseño aceptado — no implementado aún** (siguiente fase en pausa)  
Complementa: [08](08-activity-gated-bots.md) · [09](09-shop-catalog-review.md) · [12](12-buy-from-players.md)

## Contabilidad (regla de oro)

El zeny de los bots se lleva en un **ledger interno** (`bot_state.zeny`).  
La DB del servidor se toca lo mínimo:

| Acción | Qué tocamos en DB | Qué en ledger interno |
|--------|-------------------|------------------------|
| Grind (fase 3) | nada de zeny; opcional inject stock a cart/inv para shop | − spend; + loot en inventario lógico |
| Abrir/refrescar tienda | inject ítems a vender (`cart`/`vendings`) | stock lógico ↔ shop |
| Jugador compra en tienda bot | rAthena mueve zeny jugador → bot (autotrade) | **+** ese zeny al ledger (sync) |
| Bot compra a jugador | − zeny del char bot; − ítems vending jugador | **−** mismo monto en ledger |
| Spend (potions ficticias) | **nada** | solo − ledger |

**No crear zeny.** El único ingreso legítimo del bot es lo que los jugadores pagan al comprar en su tienda.  
Spend y compras a jugadores solo **restan**. Si el ledger llega a 0, no compra.

### Por qué ser estrictos al comprar a jugadores

Comprar a un jugador **transfiere** zeny bot → jugador. Si el bot no tenía ese zeny ganado de verdad (ventas), estaríamos mintando zeny para el jugador. Por eso:

- techo `price > LATAM` → nunca ([12](12-buy-from-players.md))
- `gasto ≤ ledger.zeny` (y ≤ char.zeny si ambos existen)
- budget diario acotado (~25–30%)
- sample pequeño de listings

Inventario del bot: **solo** para poner a la venta y para reflejar lo comprado si algún día guardamos mats; no es la fuente de verdad del zeny.

## Problema del spend actual

Fórmula vieja (placeholder lineal):

```
cost/h = (3000 + 2 × avg_hp) × combat_frac     # combat_frac ≈ 0.8
```

En los 173 bots activos (sim):

| Tier | cost/h med | min → max |
|------|------------|-----------|
| novice | ~2.5k | 2.5k → 2.8k |
| easy | ~3.3k | 2.8k → 4.4k |
| mid | ~5.1k | 4.0k → **10.5k** |
| hard | ~11.5k | 4.5k → **33.7k** |

Novices casi no “gastan”; hard/expert explotan con HP alto (ej. `nameless_n` ~19k HP → ~34k z/h). Extremos exagerados e inútiles para el flavor.

## Curva suavizada (acordada)

Novices gastan **un poco más**; hard/expert **mucho menos** (techo suave). Misma idea de “potions”, sin inventario de potions.

```
floor[tier] = novice 4200 | easy 4000 | mid 3700 | hard 3400 | expert 3100

cost/h = (floor[tier] + 1100 × ln(1 + avg_hp/100)) × combat_frac
```

`combat_frac = 1 − dead_time` (hoy 0.8).

### Efecto esperado (mismos bots, solo recalcular fórmula)

| Tier | cost/h med OLD → NEW | rango NEW (aprox) |
|------|----------------------|-------------------|
| novice | 2.5k → **~3.9k** | 3.7k – 4.5k |
| easy | 3.3k → **~4.8k** | 4.3k – 5.5k |
| mid | 5.1k → **~5.5k** | 5.1k – 6.4k |
| hard | 11.5k → **~6.3k** | 5.1k – 7.4k |

Extremo hard `nameless_n`: **34k → ~7.4k** z/h.  
Novice poring field: **2.5k → ~3.7k** z/h.

Tabla de referencia HP:

| avg_hp | old | soft novice | soft hard |
|--------|-----|-------------|-----------|
| 50 | 2.5k | 3.7k | 3.1k |
| 800 | 3.7k | 5.3k | 4.7k |
| 3000 | 7.2k | 6.4k | 5.7k |
| 12000 | 21.6k | 7.6k | 6.9k |

Spend sigue siendo **solo ledger** (no quita potions de la DB).  
Afecta: cuánto zeny queda para comprar a jugadores; `net` en sims.

## Qué no cambia

- Precios LATAM / techo de compra  
- Gates pause/shop  
- Inventario: inject venta / no modelar potions  

## Pendiente de código (NO ahora)

- [ ] Sustituir fórmula en `preview_sim.py` / `build_and_simulate_all.py`
- [ ] Regenerar `all_bots` + sample sims
- [ ] Schema ledger en `bot_state` (fase siguiente, en pausa)

## Parámetros (`spend_rules` — borrador)

```json
{
  "combat_frac": 0.8,
  "floor_by_tier": {
    "novice": 4200,
    "easy": 4000,
    "mid": 3700,
    "hard": 3400,
    "expert": 3100
  },
  "hp_log_scale": 1100,
  "hp_log_ref": 100,
  "formula": "(floor[tier] + hp_log_scale * ln(1 + avg_hp/hp_log_ref)) * combat_frac"
}
```
