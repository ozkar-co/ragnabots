# Inventario de datos (checklist M1)

**Estado:** 2026-08-28 — YAML local + LATAM FREYA completo. Ver [06-market-curation-plan.md](06-market-curation-plan.md).

## rAthena — archivos del servidor

Ruta base: `/home/oz/rathena` → `data/raw/rathena/`

- [x] YAML item/mob + imports + rates
- [x] 5 ítems custom OzRo (35001–35005)

## Mercado externo

- [x] Staging operativo (`fetch_batch.py`)
- [x] **LATAM FREYA completo** — 29,059 ítems escaneados
- [x] **Curación capa 1** — 5,328 con precio → `staging/market/latam_tools/curated/`
- [x] **Atlantis top 2,000** — 733 con stats históricas
- [x] **LATAM clásico ID&lt;10k** — 1,833; bot focus 202; ver `classic_deep_analysis.md`
- [x] Fetch Atlantis gaps clásicos — 688 nuevos → **1 421** con stats
- [x] **Dropeables** — 1 115 (normal 1 107) — `droppable_*.json/txt`
- [x] **Spawns renewal** — NPC `re/mobs` copiados; 1 132 mobs / 357 mapas
- [x] **Grindable** — 926 ítems (drop + spawn normal) — `grindable_*`
- [ ] Simulación de grind → oferta de bots
- [ ] Techo compra a jugadores (LATAM median)
- [ ] _(más adelante)_ más fetch / Divine Pride / data/market/

### Resultado LATAM FREYA (2026-08-28)

| Métrica | Valor |
|---------|-------|
| Escaneados | 29,059 |
| Con datos de precio | 5,328 |
| Con vending activo | 4,065 |
| No en mercado LATAM | 15,593 |
| Bulk local | `staging/market/latam_tools/bulk/FREYA/` (115 MB, gitignored) |
| Curado en git | `staging/market/latam_tools/curated/` |

### Resultado Atlantis top2000 (2026-08-28)

| Métrica | Valor |
|---------|-------|
| Solicitados (LATAM top) | 2,000 |
| Con stats (min/max/avg/sold) | **733** |
| Sin data en Atlantis | 1,267 (ítems modernos / no listados) |
| Duración | ~3.2 h |
| Bulk local | `staging/market/atlantis_playro/bulk/` (~8 MB) |
| Curado en git | `staging/market/atlantis_playro/curated/` |

## Base de datos MySQL

- [x] Snapshot schema reference
- [ ] Clon SQLite
- [ ] Vendings OzRo — bloqueado hasta autotrade

## Criterio de salida M1 (parcial)

1. [x] YAML y conf locales
2. [x] LATAM batch completo + curación capa 1–2
3. [ ] Atlantis top 2000
4. [ ] Diccionario precios en `data/market/`
5. [ ] Plan M2 simulación

## Usos del dataset

- **Bots:** capa 3 (~1k precios)
- **NPCs:** capa 4 (top 100–200 por tipo)
- **Quests:** ragnapi drops + precios capa 1–3
- **Referencia 30k:** completar gradual para casos puntuales
