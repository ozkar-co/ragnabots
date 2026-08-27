# Inventario de datos (checklist M1)

Antes de escribir **cualquier** código de negocio, recolectar e inspeccionar estas fuentes. Marcar cada ítem conforme se complete.

**Estado:** recolectado parcialmente el 2026-08-27 desde `kansas` (172.26.0.1). Ver `data/manifest.json` y `data/raw/`.

## rAthena — archivos del servidor

Ruta base del servidor: `/home/oz/rathena`

### Base de datos YAML

- [x] `db/item_db.yml` — header + imports a pre-re, re, import
- [x] `db/mob_db.yml` — header + imports; drops con `Item`, `Rate`, `Index`, `StealProtected`
- [x] `db/mob_item_ratio.yml` — existe; import vacío (solo Header)
- [x] Otros YAML relevantes: `db/re/item_db_{equip,etc,usable}.yml`, `db/re/mob_db.yml`, `db/pre-re/*.yml`

**Cadena de imports (importante):** los archivos raíz no tienen Body; cargan:
1. `db/pre-re/` (Prerenewal)
2. `db/re/` (Renewal) — bulk del catálogo (~10MB item DB)
3. `db/import/` — overrides custom del servidor

### Configuración de rates

- [x] `conf/battle/drops.conf` — base 100 = 1x
- [x] `conf/battle/exp.conf` — copiado
- [ ] `conf/battle/` — otros conf relevantes: pendiente revisar `items.conf`, `monster.conf`
- [x] `conf/import/battle_conf.txt` — **rates custom del servidor** (ver abajo)

### Hallazgos de inspección

```
Versión: rAthena YAML v3 (items), v5 (mobs) — Renewal
Custom items en import/: 5 entradas
Custom mobs en import/: 1 override (DRAINLIAR id 1111 con drops redefinidos)
mob_item_ratio import: vacío

Rates custom (battle_conf.txt → data/raw/server_rates.json):
  common: 5x | heal/use: 10x | equip: 15x | card: 100x | mvp/treasure: 5x

Drops en mob_db usan Rate sobre base 10000 (ej. Rate: 1500 = 15%)
```

## Mercado externo (referencia de precios)

- [ ] Explorar fuentes disponibles (Divine Pride API, RateMyServer, otras)
- [ ] Decidir cuál(es) usar
- [ ] Anotar rate del servidor de referencia vs rate propio
- [ ] Documentar limitaciones (rate limits, cobertura de ítems custom)

### Hallazgos

```
Fuente elegida: pendiente
Rate referencia vs propio: servidor custom (5x-100x según categoría)
Ítems custom: 5 en import/item_db.yml — no estarán en DBs públicas
```

## Base de datos MySQL (clon)

Ver procedimiento en [03-server-snapshot.md](03-server-snapshot.md).

- [x] Snapshot desde ozro-backup (`20260827_030000`) — SQL + JSON
- [ ] Conversión/import a SQLite local para desarrollo
- [x] Inspeccionar tablas críticas (parcial — sin vendings)

### Tablas a inspeccionar primero

| Tabla | Estado | Hallazgo |
|-------|--------|----------|
| `char` | copiado | 26 personajes; hub principal geffen |
| `inventory` | copiado | 791 filas |
| `cart_inventory` | copiado | 13 filas (pocos merchants) |
| `vendings` | **no en backup** | ozro-backup no exportó esta tabla |
| `vending_items` | **no en backup** | idem |
| `zenylog` | no en backup | — |
| `picklog` | no en backup | — |
| `login` | **excluido** | contiene contraseñas — no va a git |

### Hallazgos de la DB

```
Personajes: 26
Mapa principal: geffen (mayoría de chars)
Cart inventory: 13 filas — hay actividad merchant limitada
Char merchant existente: "Vendedor" (150014) — estudiar como referencia
GM "Dios" (150013) con zeny inflado — excluir de métricas económicas
Vendings: no disponibles en este snapshot — necesario dump directo MySQL
Schema referencia: data/raw/rathena/sql-files/main.sql
```

## Salida en `data/` (decisión parcial)

| Archivo | Estado | Formato |
|---------|--------|---------|
| `data/manifest.json` | hecho | JSON |
| `data/raw/server_rates.json` | hecho | JSON |
| `data/raw/rathena/**` | hecho | YAML/conf originales |
| `data/raw/db_snapshot/**` | hecho | SQL + JSON |
| `data/items.*` | pendiente | normalizar desde YAML |
| `data/mobs.*` | pendiente | normalizar desde YAML |
| `data/price_dictionary.*` | pendiente | requiere mercado externo + vending |

**Formato elegido por ahora:** JSON para metadata y snapshots; YAML crudo en `data/raw/`; normalización TBD.

## Criterio de salida de M1

1. [x] YAML y conf recolectados
2. [x] Snapshot DB parcial recolectado
3. [ ] Vendings obtenidos (dump MySQL directo)
4. [ ] Clon SQLite local creado
5. [ ] Mercado externo explorado
6. [ ] Catálogos normalizados (items, mobs)
7. [ ] Plan M2 basado en datos
