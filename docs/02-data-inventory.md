# Inventario de datos (checklist M1)

Antes de escribir **cualquier** código de negocio, recolectar e inspeccionar estas fuentes.

**Estado:** 2026-08-27 — YAML local recolectado; mercado externo en `staging/`.

## rAthena — archivos del servidor

Ruta base: `/home/oz/rathena` → copiado en `data/raw/rathena/`

### Base de datos YAML

- [x] `db/item_db.yml` — header + imports a pre-re, re, import
- [x] `db/mob_db.yml` — drops con `Item`, `Rate`, `Index`
- [x] `db/mob_item_ratio.yml` — import vacío
- [x] `db/re/`, `db/import/` — catálogo completo + 5 ítems custom OzRo

### Configuración de rates

- [x] `conf/battle/drops.conf`, `exp.conf`
- [x] `conf/import/battle_conf.txt` → `data/raw/server_rates.json`

### Hallazgos YAML

```
Renewal YAML v3/v5
Custom items: 35001-35005 (monedas OzRo + MVP_Soul) — sin fuente externa
Custom mob: DRAINLIAR (1111) override en import/
Rates: common 5x, heal/use 10x, equip 15x, card 100x, mvp 5x
```

## Mercado externo (referencia de precios)

**No usamos datos de jugadores locales** para precios — poco historial de juego.

Flujo: `staging/market/` → validar → promover a `data/market/` (cuando esté listo).

Ver [05-external-market.md](05-external-market.md) y `staging/market/README.md`.

- [x] Explorar fuentes con API pública
- [x] Carpeta staging separada + script de prueba
- [ ] Validar fidelidad con muestra representativa (≥20 ítems)
- [ ] Decidir ajuste de rates vs OzRo
- [ ] Divine Pride API key (NPC buy/sell ancla)
- [ ] Promover fuentes validadas a `data/`

### Fuentes en prueba

| Fuente | API sin key | Qué aporta | Estado |
|--------|-------------|------------|--------|
| **atlantis_playro** | Sí (HTML) | histórico min/max/avg/std, total_sold, NPC | probing |
| latam-tools | Sí | vending median actual bRO LATAM | probing |
| RagnaAPI | Sí | drops, stats mobs, metadata ítems | probing |
| Divine Pride | No (key) | NPC buy/sell, DB oficial | pending_key |

### Hallazgos mercado (inicial)

```
latam-tools FREYA item 501: offers.median=30, jellopy 909 median~2098
RagnaAPI: sin precios mercado; útil para quests (drops, equip jobs)
Ítems custom 35001-35005: solo YAML local
Vendings OzRo: pendiente cuando haya autotrade activo
```

## Base de datos MySQL (solo schema / SQLite)

El snapshot DB local **no se usa para analizar jugadores**. Sirve para:
- Conocer schema real (`sql-files/main.sql`)
- Futuro clon SQLite para pruebas de inyección

- [x] Snapshot parcial en `data/raw/db_snapshot/` (schema reference)
- [ ] Clon SQLite local
- [ ] Vendings OzRo — **bloqueado** hasta tienda autotrade

| Tabla | Uso |
|-------|-----|
| `char`, `inventory`, etc. | solo schema; no análisis de patrones |
| `vendings` | pendiente dump propio |
| `login` | excluido (contraseñas) |

## Salida en `data/` vs `staging/`

| Ubicación | Contenido | Estado |
|-----------|-----------|--------|
| `data/raw/rathena/` | YAML + conf servidor | hecho |
| `data/raw/server_rates.json` | rates OzRo | hecho |
| `data/manifest.json` | inventario | hecho |
| `staging/market/*/samples/` | probes API externos | en curso |
| `data/market/` | dataset validado | pendiente |
| `data/items.*`, `data/mobs.*` | catálogos normalizados | pendiente |

## Usos del dataset (bots + diseño)

- **Bots:** diccionario de precios, simulación económica
- **NPCs:** precios de shop razonables vs mercado
- **Quests:** recompensas balanceadas vs drops y valor de ítems

## Criterio de salida M1

1. [x] YAML y conf locales
2. [x] Staging mercado externo operativo
3. [ ] Validación de muestras (documentar en `staging/market/`)
4. [ ] NPC buy/sell ancla (YAML local o Divine Pride)
5. [ ] Vendings propios (cuando aplique)
6. [ ] Catálogos normalizados en `data/`
7. [ ] Plan M2
