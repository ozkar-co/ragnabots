# Fuentes de mercado externo

Recolectar precios de servidores con datos públicos. **No analizamos jugadores locales** — llevamos poco tiempo y el snapshot DB sirve solo para schema/SQLite, no para patrones de juego.

## Fuentes evaluadas

| Fuente | API pública | Precios vending | NPC buy/sell | Drops/mobs | Rate ref. | Estado |
|--------|-------------|-----------------|--------------|------------|-----------|--------|
| [latam-tools](https://mercado.latam-tools.com.br) | Sí, sin key | Sí (FREYA/NIDHOGG) | No | No | bRO oficial LATAM | **probando** |
| [RagnaAPI](https://ragnapi.com) | Sí, sin key | No | No | Sí (iRO wiki) | iRO Renewal | **probando** |
| [Divine Pride](https://www.divine-pride.net/api) | Sí, requiere key | No | Sí | Sí | por región (iRO, etc.) | pendiente key |
| MyRag (myrag.kr) | No encontrada | Sí (scraping?) | No | No | kRO | no explorar aún |

### latam-tools — prioridad alta

- Base: `https://mercado.latam-tools.com.br/api/v1/`
- Endpoints útiles:
  - `GET /items/{id}?server=FREYA|NIDHOGG`
  - `GET /prices?items=501,909&server=FREYA` (batch, max 100)
- Devuelve: `offers.median`, `offers.min/max`, `market.avg` (histórico), `cheapest[]`
- **Limitación:** servidor bRO LATAM, rates distintos a OzRo (5x–100x custom). Usar como referencia relativa, no absoluta.
- **Ventaja:** precios reales de vending, actualizados por colecta.

### RagnaAPI — metadata para quests/NPCs

- Base: `https://ragnapi.com/api/v1/re-newal/`
- `items/{id}` — descripción, jobs equipables, drop_rate desde qué mob
- `monsters/{id}` — stats, drops con %
- **Sin precios de mercado ni NPC.** Complementa diseño de quests.

### Divine Pride — ancla NPC (pendiente)

- Requiere registro y `DIVINE_PRIDE_API_KEY`
- `GET /api/database/Item/{id}?apiKey=...` + header `x-server: iRO`
- Útil para `buyPrice` / `sellPrice` oficiales como piso/techo

## Ajuste de rates (borrador)

OzRo rates (ver `data/raw/server_rates.json`):
- common 5x, heal/use 10x, equip 15x, card 100x

Estrategia pendiente de validar en staging:
1. Ancla dura: NPC buy/sell del YAML local
2. Referencia mercado: latam_tools median (o Divine Pride si aplica)
3. Factor de escala por categoría si hace falta — **no asumir fórmula hasta comparar muestras**

## Ítems sin cobertura externa

Custom OzRo (`db/import/item_db.yml`):
- 35001–35005: monedas OzRo + MVP_Soul
- Solo precios definidos en YAML o diseño manual

## Criterio para promover a `data/`

Crear `data/market/` solo cuando una fuente pase revisión:

1. Muestra de ≥20 ítems representativos (consumibles, equip, etc, cards)
2. Comparación documentada vs NPC local
3. `sources.yaml` marcado como `promoted: true`
4. Entrada en `data/manifest.json`
