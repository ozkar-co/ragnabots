# NPC shops — ítems comprables en el juego

Fecha: 2026-08-28  
Script: `python staging/market/npc_shops/extract_npc_shops.py`  
Fuente: `data/raw/rathena/npc/` (OzRo: merchants + dump `all_shop_lines.txt`)

## Para qué sirve

1. **Filtrar oferta de bots** — no vender lo que ya se compra a NPC (Phracon, Meat, Zargon…).
2. **DB para jugadores** — ítem → precio NPC → mapa/coords/nombre del NPC.

## Resultado

| Métrica | Valor |
|---------|-------|
| Líneas shop parseadas | ~442 |
| Ítems únicos comprables | **923** |

### Ejemplos (contaminaban bots)

| ID | Ítem | Precio NPC | Dónde |
|----|------|------------|-------|
| 1010 | Phracon | 200z | market_refine_* (ciudades) |
| 1011 | Emveretarcon | 1000z | idem |
| 517 | Meat | 50z | Butcher prontera/izlude/… |
| 912 | Zargon | 360z | geffen_in, yuno, lhz… |
| 910 | Garlet | 30z | traders |
| 519 | Milk | 25z | Milk Ranch |
| 909 | Jellopy | 6z | (shop sin mapa fijo / dump) |
| 984 | Oridecon | 200k | Eden marketshop |

**No** están en NPC shops: Rough Oridecon (756), Rough Elunium (757) → OK para bots.

## Archivos

| Archivo | Contenido |
|---------|-----------|
| `npc_buyable.json` | completo + hasta 40 locations/ítem |
| `npc_buyable_compact.json` | id, nombre, precio min/max, maps |
| `npc_buyable_ids.txt` | una id por línea (filtro bots) |
| `summary.json` | métricas |

## Regenerar

Tras traer más NPC scripts del servidor:

```bash
# opcional: refrescar dump
# ssh … 'grep -Rho … shop …' > data/raw/rathena/npc/all_shop_lines.txt
python staging/market/npc_shops/extract_npc_shops.py
python staging/market/bots/preview_sim.py
```
