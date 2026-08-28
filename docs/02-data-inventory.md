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
- [ ] Atlantis sobre top 2,000
- [ ] Refinar a top 1,000 + NPC focus 100–200
- [ ] Completar 29k gradual (atlantis/ragnapi, referencia)
- [ ] Divine Pride API key
- [ ] Promover a `data/market/`

### Resultado LATAM FREYA (2026-08-28)

| Métrica | Valor |
|---------|-------|
| Escaneados | 29,059 |
| Con datos de precio | 5,328 |
| Con vending activo | 4,065 |
| No en mercado LATAM | 15,593 |
| Bulk local | `staging/market/latam_tools/bulk/FREYA/` (115 MB, gitignored) |
| Curado en git | `staging/market/latam_tools/curated/` |

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
