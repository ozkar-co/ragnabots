# Catálogo de tiendas (muestra ×10) + explicación de spend

Fecha: 2026-08-28  
Fuente: `staging/market/bots/sample/*.sim.json` (`hours_per_day=3.5`, rates 1×, LATAM)

Ciclo de vida acordado: **~100 días de grind acreditado** → luego solo venden remanente hasta desaparecer.

---

## Cómo se calcula el spend (y por qué se ve raro)

Es un **heurístico placeholder**, no potions reales del item_db:

```
cost_por_hora = (3000 + 2 × avg_hp_mapa) × (1 − dead_time)
dead_time = 0.20
spend_día = cost_por_hora × 3.5
```

| Mapa | avg HP | spend/h | spend/kill | ¿Sensible? |
|------|--------|---------|------------|------------|
| prt_fild08 | 55 | ~2.5k | ~2.6z | Demasiado barato para 960 kills/h |
| mjolnir_11 | 3030 | ~7.2k | ~44z | Tirando a alto |
| gl_sew04 | 15179 | ~26.7k | **~727z** | Absurdo — por eso Sewers “quema” zeny |

**Por qué raro:**

1. Escala lineal con HP → mapas expert explotan el gasto.
2. No usa precios reales de Red Potion / Fly Wing / etc.
3. No escala con kills (un Poring a 960/h gasta ~igual por hora que si matara 100, salvo el factor HP).
4. Frente al **lote LATAM** (millones), el spend en novice/mid es ruido (~0.1–3% del lote). Solo en Sewers el spend come el margen.

**Propuesta de reemplazo (cuando calibramos):**

```
spend/kill ≈ precio_poción_efectiva × (avg_hp / heal_por_poción) + flywing_amortizado
# o simplemente: spend/h fijo por tier (novice 1k, easy 2k, mid 4k, hard 8k)
```

Hasta entonces: **no uses spend para juzgar realismo de tiendas**; úsalo solo como recordatorio de que hay que modelar gasto en serio.

---

## Qué hay en cada tienda (oferta mats + cards)

Precios = LATAM (`offers_median` o `market_avg`).  
Mats = top 5 por score valor×volumen. Cards = 1 de cada 2 dropeadas, máx 1 slot en shop.

### 01 Campo Prontera — `prt_fild08` (novice)

| Ítem | Precio LATAM | Notas |
|------|--------------|-------|
| Phracon | 45 666 | ¿Demasiado “refinado” para newbie farm? |
| Feather | 10 000 | Precio LATAM alto vs jellopy |
| Iron Ore | 11 000 | OK como drop raro |
| Jellopy | 2 099 | Clásico — debería dominar percepción |
| Clover | 1 800 | OK |
| **Card:** Pupa (~1.9M) | | Solo cards ≥1M; junk Poring/Fabre/Lunatic fuera |

**Realismo:** la tienda se ve rara si Phracon/Feather eclipsan Jellopy. Candidato: bajar score de ores o exigir mats “temáticos” del mapa.

### 02 Payon Spore — `pay_fild08`

| Ítem | Precio | |
|------|--------|--|
| Red Herb | 1 399 | OK |
| Strawberry | 1 299 | OK |
| Mushroom Spore | 900 | OK — volumen alto |
| Venom Canine | 1 288 | OK |
| Emveretarcon | 4 852 | Un poco “ore”, pero sale del spawn |
| Cards: Spore 50k, Snake 180k, Wormtail 1M | | Spore Card ~1 sellable/día → mucho a 100d |

### 03 Desierto Muka — `moc_fild01`

| Ítem | Precio | |
|------|--------|--|
| Orange | 29 998 | ¿LATAM inflado? |
| Phracon | 45 666 | Otra vez ore caro |
| Iron Ore | 11 000 | |
| Red Herb | 1 399 | |
| Shell | 3 500 | |
| Cards: Peco / Peco Egg (millones) | | Raras — OK |

### 04 Ant Hell — `anthell01`

| Ítem | Precio | |
|------|--------|--|
| Phracon | 45 666 | |
| Tooth of Bat | 14 960 | Temático OK |
| Iron Ore | 11 000 | |
| Worm Peeling | 4 999 | OK volumen |
| Shell | 3 500 | |
| Cards: Andre 4.9M, Andre Egg, Giearth | | |

### 05 Payon Bigfoot — `pay_fild07`

| Ítem | Precio | |
|------|--------|--|
| Bear's Footskin | 3 499 | Muy temático ✓ |
| Porcupine Quill | 9 900 | OK |
| Rainbow Shell | 10 000 | |
| Iron Ore | 11 000 | |
| Honey | 2 690 | ✓ |
| Cards: Bigfoot / Caramel / Creamy | | |

**De los más creíbles** del set.

### 06 Aldea Orco — `gef_fild10` + `orcsdun01`

**Campo:** Rough Oridecon, Milk, Cyfar, Orcish Voucher (+ Orc Warrior Card)  
**Dun:** Tooth of Bat, Shell, Sticky Mucus, Orc Claw (+ Orc Zombie/Skeleton cards)

**Creíble** — voucher/cyfar/claw/mucus huelen a orco.

### 07 Mjolnir Argiope — `mjolnir_11`

Cobweb, Bug Leg, Green Herb, Zargon, Scell (+ Argiope Card ~1M)

**Creíble** — spider kit.

### 08 Byalan — `iz_dun01`

Meat (29k ¿caro?), Worm Peeling, Crystal Blue, Garlet, Sticky Mucus  
Cards: Vadon, Hydra, Marina, Cornutus

**Mix OK**; Meat a 29k LATAM puede distorsionar.

### 09 Comodo Gator — `cmd_fild03`

Anolian Skin, Rough Oridecon, Zargon, Stem, Maneater Blossom  
Cards: Alligator, Mutant Dragonoid, Toad

**Creíble** (Anolian Skin es el hit histórico).

### 10 GH Sewers — `gl_sew04` (expert)

Oridecon, Anolian Skin, Tooth of Bat, Zargon, Crystal Arrow Quiver  
+ Anolian Card

**Descartable del pool generalista** (spend placeholder lo hunde; tier expert).

---

## Lectura rápida realismo

| Bot | ¿Tienda creíble? |
|-----|------------------|
| 05 Bigfoot, 06 Orco, 07 Argiope, 09 Gator | Sí |
| 02 Spore, 08 Byalan | Sí con matices (cards/Meat) |
| 01 Prontera, 03 Muka, 04 Ants | Phracon/ores/Orange roban el protagonismo |
| 10 Sewers | Fuera |

Ajustes fáciles si quieres: excluir Phracon/Emveretarcon/Iron Ore del score de newbie, o `mats_prefer_etc_from_map` / blacklist de ores en novice.

---

## Ciclo 100 días (acordado)

```
días 1..100 (si hubo login ese día):
  acreditar 3.5h × bots elegibles → inventario + spend
  abrir/mover/cerrar tiendas

día > 100 (por bot o global):
  no más grind
  solo vender remanente hasta gates / stock ~0 → desaparece
```

Calibración over-the-air si hace falta.
