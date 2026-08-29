# Compra a jugadores (fase 1 del job diario)

Fecha: 2026-08-28  
Estado: **diseño + preview**  
Script: `python staging/market/bots/preview_buy_players.py`  
Complementa: [08-activity-gated-bots.md](08-activity-gated-bots.md) — orden: **compra → tiendas → grind**

## Contexto (lado venta — OK)

- Mucus/herb “basura”: dan flavor; novice se congela si no vende → otros bots despiertan.
- Green Herb: rotación alta (quest Rachel ~3k/jugador); puede salir de golpe.
- No hace falta optimizar eso ahora.

## Objetivo compra

Facilitar que el jugador **venda** a precio razonable.  
Solo los bots compran. No ser tacaños, pero **nunca** validar un exploit (precio > LATAM).

## Flujo (fase 1 del cron único)

Si no hay tiendas de jugadores → **skip** y seguir a fase 2 (tiendas).

```
1. Listar tiendas autotrade de jugadores (excl. bots)
2. n_bots = random(3..8)  # o f(jugadores_hoy)
3. Para cada bot comprador (zeny > 0):
     budget = min(zeny * 25%, cap absoluto, zeny)
     n_listings = random(1..4)
     elegir n_listings al azar de las tiendas
     para cada listing:
       si price > LATAM → skip (nunca)
       con probabilidad P(price, LATAM):
         qty = random fracción del stock (5–35%), cap 1..50
         qty = min(qty, lo que budget alcanza)
         comprar → restar zeny bot, quitar ítems vending, log
4. Dry-run primero; luego write MySQL
```

Luego el mismo script sigue con **tiendas** y **grind** ([08](08-activity-gated-bots.md)).

### Balance cantidad

No “cada ítem de la tienda”. Mejor:

| Enfoque | |
|---------|--|
| **Elegido** | Sample de **1–4 listings** por bot |
| Qty | Fracción random del stock listado (5–35%) + caps |
| Bots | 3–8 por corrida (escalar con actividad) |

Así una tienda grande no se vacía entera en un día, pero sí se mueve.

## Precio → probabilidad

```
ref = LATAM offers_median (else market_avg)

si price > ref:  P = 0          # NUNCA
si no:
  ratio = price / ref           # 0 = regalado, 1 = pegado al techo
  P = p_max * (1 - ratio)^k
```

Defaults preview: `p_max=0.85`, `k=1.15` (suave — facilitar venta).

| Precio vs LATAM | P aprox | Lectura |
|-----------------|---------|---------|
| 40% | ~0.47 | ganga |
| 60% | ~0.30 | barato |
| 75% | ~0.17 | ok |
| 90% | ~0.06 | cerca del techo |
| >100% | **0** | nunca |

Cerca del óptimo **cuesta vender** (pocas compras); lejos hacia abajo **sale fácil**.  
Eso empuja a los jugadores a poner precios competitivos sin castigar el techo LATAM.

### Floor opcional (después)

Si `price < NPC_buy * 0.5` (demasiado sospechoso), se puede capar qty — no urgente.

## Anti-exploit

| Regla | |
|-------|--|
| Techo | price > LATAM → nunca |
| Zeny | gasto ≤ zeny del bot; budget 25%/corrida |
| Volumen | caps qty + pocos listings |
| Aleatorio | no barremos toda oferta barata ordenada |

El zeny del bot viene de **haber vendido** antes (ciclo cerrado / ledger).  
Novice congelado sin ventas → ledger≈0 → no compra.  
Ver [13-zeny-and-spend.md](13-zeny-and-spend.md) — no mintar zeny.

## Preview

```bash
python staging/market/bots/preview_buy_players.py
# → staging/market/bots/buy_preview/buy_preview.json
```

Ajustar `p_max` / `k` / `n_buyer_bots` mirando la curva y una corrida simulada.

## Pendiente runtime

- [ ] Leer `vendings` / `vending_items` OzRo
- [ ] Diccionario precio = mismo LATAM del pool (+ cards/equip si se compran)
- [ ] Dry-run JSONL de compras
- [ ] Wire como **fase 1** del cron único ([08](08-activity-gated-bots.md))
