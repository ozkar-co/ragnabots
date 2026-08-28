# Dropeables desde Atlantis (para simular grind)

Fecha: 2026-08-28  
Fuente: `ranked_atlantis.json` × `mob_db` OzRo (`re` + `import`)  
Spawn normal: **pendiente** (ahora solo “aparece en Drops/MvpDrops”)

## Resultado

| Set | N |
|-----|---|
| Atlantis con stats | 1 421 |
| **Dropeables** | **1 115** |
| → drop normal | 1 107 |
| → solo MVP prize | 8 |
| No dropeables | 306 |

Clásicos ID &lt; 10k: **1 013** dropeables · 181 no dropeables.

## Tipos (dropeables)

Dominan **carta** (385) y **diversos** (325) — alineado con lo que quieres para bots (vender loot + cards). Top volumen Atlantis: Anolian Skin, Starsand, Sharp Leaf, gemstones, Stem, Poison Spore, Empty Bottle, Blue Herb, Dead Branch.

## No dropeables (reservados para otras reglas)

Craft (Acid Bottle, Bottle Grenade), consumibles shop/cash, huevos, muchos headgears/visuales, munición especial, etc. No se descartan: más adelante reglas de craft/NPC/quest.

## Archivos

| Archivo | Contenido |
|---------|-----------|
| `droppable.json` / `droppable_ids.txt` | 1 115 con `drop_kind` + `drop_mob_count` |
| `droppable_normal_ids.txt` | solo Drops normales (sin mvp-only) |
| `non_droppable.json` / `_ids.txt` | 306 para reglas futuras |
| `droppable_item_to_mobs.json` | item_id → lista de mob_ids |
| `droppable_summary.json` | métricas |

## Siguiente (grind sim)

1. Usar `droppable_normal_ids.txt` como universo de loot de bots.
2. Más adelante: filtrar mobs con spawn normal (mapas / `mob_avail` / NPC spawn).
3. LATAM median = techo de compra a jugadores; Atlantis sold = prioridad de qué farmar/vender.
