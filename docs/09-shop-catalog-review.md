# Catálogo bots post-filtro NPC + lista comprables NPC

Fecha: 2026-08-28  
Ver también: [npc_shops/README](../staging/market/npc_shops/README.md)

## Cambio

Se extrajeron **923 ítems** de shops NPC del servidor OzRo.  
Los bots **ya no los venden** (`exclude_npc_buyable=True`). Oferta mats top **4**.

## Tiendas ahora (más útiles / temáticas)

| Bot | Mats | Cards |
|-----|------|-------|
| 01 Prontera | Feather, Clover, Fluff, Green Herb | Pupa ≥1M |
| 02 Spore | Red Herb, Strawberry, Mushroom Spore, Venom Canine | Spore/Snake/Wormtail |
| 03 Muka | Orange, Red Herb, Shell | Peco / Egg |
| 04 Ant Hell | Tooth of Bat, Worm Peeling, Shell, Sticky Mucus | Andre… |
| 05 Bigfoot | Bear Footskin, Quill, Rainbow Shell, Honey | Bigfoot/Caramel/Creamy |
| 06 Orco | Rough Oridecon, Cyfar, Voucher / Bat, Shell, Mucus | Orc cards |
| 07 Argiope | Bug Leg, Green Herb, Maneater Blossom | Argiope |
| 08 Byalan | Worm Peeling, Mucus, Nipper, Tentacle | Vadon/Hydra… |
| 09 Gator | Anolian Skin, Rough Oridecon, Maneater | Alligator… |
| 10 Sewers | Anolian Skin, Tooth of Bat, Little Evil Wing | Anolian |

Fuera por NPC: Phracon, Emveretarcon, Meat, Milk, Zargon, Garlet, Scell, Jellopy, Oridecon (Eden), etc.

## Pendiente de ojo humano

- **Orange @30k** LATAM en Muka — ¿dejar o tope más bajo?
- **Feather @10k** en Prontera — ¿útil o ruido LATAM?
- **Green/Red Herb** — no salieron como shop NPC en el parse; si en OzRo hay herbolario custom, añadir script y regenerar.
- Sewers sigue flojo (spend stub + poco loot útil).

## Spend

Sigue siendo placeholder `(3000+2×HP)×0.8` — no cambia con este filtro. Calibrar aparte.
