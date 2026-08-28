# Spawns Renewal + grindable filter

Fecha: 2026-08-28  
Fuente: `data/raw/rathena/npc/re/mobs/` (servidor OzRo, renewal)  
Boss (`boss_monster`) excluido del conteo “normal”.

## Spawns crudos

| Métrica | Valor |
|---------|-------|
| Archivos | 102 |
| Líneas monster normales | 3 173 |
| Líneas boss | 64 |
| Mapas únicos | 357 |
| Mobs con spawn normal | 1 132 |

### Top mobs por cantidad total

FABRE (1020), PORING (861), LUNATIC (825), plantas, POPORING, ARGIOPE, METALING…

### Top mapas por densidad

`prt_fild08` (616: Poring/Fabre/Lunatic), variantes `prt_fild08a-d`, `moc_fild01` (Muka/Peco), `lhz_dun*`, `yuno_fild*`, `abbey02`…

## Cruce con dropeables Atlantis

| Set | N |
|-----|---|
| Dropeables | 1 115 |
| **Grindable** (algún mob droppeador tiene spawn normal) | **926** |
| No grindable por spawn | 189 |

Tipos grindable: cartas (357), diversos (261), cabezas, consumibles…

## Archivos

### Spawns (`staging/market/spawns/`)

| Archivo | Contenido |
|---------|-----------|
| `mobs_by_amount.json` | mobs ordenados por cantidad total + mapas |
| `maps_by_amount.json` | mapas + composición de mobs |
| `mob_companions_top100.json` | co-spawns (quién aparece junto a quién) |
| `spawns_normal.json` | todas las líneas parseadas |
| `summary.json` | métricas |

### Grind (`atlantis_playro/curated/`)

| Archivo | Contenido |
|---------|-----------|
| `grindable.json` / `grindable_ids.txt` | 926 ítems listos para sim de grind |
| `not_grindable_spawn.json` | dropeables sin spawn normal de sus mobs |

## Uso para bots

1. Elegir mapas densos o mobs con alto `total_amount`.
2. Ver `companions` para loot mixto realista en un mapa.
3. Oferta de bot = loot de ítems en `grindable_*` dropeados por esos mobs.
4. Precio venta ≈ Atlantis tendencia / LATAM median; compra a jugadores ≤ LATAM median.

## Pendiente

- Filtrar plantas / mobs especiales si no cuentan como grind.
- Excluir mapas de evento/instancia si no queremos farmear ahí.
- Simulación: kills/hora × drop rate × rates OzRo.
