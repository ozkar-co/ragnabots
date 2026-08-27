# Inventario de datos (checklist M1)

Antes de escribir **cualquier** código de negocio, recolectar e inspeccionar estas fuentes. Marcar cada ítem conforme se complete.

## rAthena — archivos del servidor

Ruta base del servidor: `________________` (anotar en M1)

### Base de datos YAML

- [ ] `db/item_db.yml` — inspeccionar campos reales (id, name, type, buy, sell, weight, etc.)
- [ ] `db/mob_db.yml` — formato de drops en tu versión (Item, Rate, ¿estructura anidada?)
- [ ] `db/mob_item_ratio.yml` — ¿existe? ¿tiene overrides?
- [ ] Otros YAML relevantes descubiertos: ________________

### Configuración de rates

- [ ] `conf/battle/drops.conf` — item_rate_*, item_drop_*_min/max
- [ ] `conf/battle/exp.conf` — si afecta economía indirectamente
- [ ] `conf/battle/` — otros conf relevantes: ________________
- [ ] `conf/import/` — overrides que pisen los valores base

### Hallazgos de inspección (completar en M1)

```
# Pegar aquí notas tras abrir los archivos reales:
# - Versión de rAthena:
# - Campos inesperados en item_db:
# - Formato de drops en mob_db:
# - Rates personalizados encontrados:
```

## Mercado externo (referencia de precios)

- [ ] Explorar fuentes disponibles (Divine Pride API, RateMyServer, otras)
- [ ] Decidir cuál(es) usar
- [ ] Anotar rate del servidor de referencia vs rate propio
- [ ] Documentar limitaciones (rate limits, cobertura de ítems custom)

### Hallazgos

```
# Fuente elegida:
# Rate referencia vs propio:
# Ítems custom del servidor no cubiertos:
```

## Base de datos MySQL (clon)

Ver procedimiento en [03-server-snapshot.md](03-server-snapshot.md).

- [ ] Dump MySQL del servidor (completo o subset)
- [ ] Conversión/import a SQLite local para desarrollo
- [ ] Inspeccionar tablas críticas (ver abajo)

### Tablas a inspeccionar primero

| Tabla | Qué buscar |
|-------|------------|
| `char` | char_ids de familia, distribución de zeny, niveles |
| `inventory` | qué llevan los jugadores reales |
| `cart_inventory` | ítems en carros de merchants |
| `vendings` | tiendas activas, mapas, autotrade flag |
| `vending_items` | precios reales del mercado actual |
| `zenylog` | flujo de zeny (si existe historial útil) |
| `picklog` | transacciones de ítems (si existe) |

### Hallazgos de la DB

```
# Número de personajes activos:
# char_ids familia (hermano/primos):
# Vendings activas (count, mapas principales):
# Rango de precios observados vs NPC buy/sell:
# Anomalías o sorpresas en el schema:
```

## Salida esperada en `data/` (forma TBD)

**No decidir formato hasta completar la inspección.** Opciones a evaluar en M1:

| Formato | Cuándo tiene sentido |
|---------|---------------------|
| JSON | Catálogos pequeños, diccionarios |
| CSV | Tablas planas, fácil de inspeccionar a mano |
| Parquet | Solo si el volumen lo justifica |

Archivos candidatos (nombres y schema se definen tras inspección):

- `data/manifest.json` — fecha, hashes, fuentes usadas
- `data/items.*` — catálogo de ítems normalizado
- `data/mobs.*` — catálogo de mobs + drops
- `data/server_rates.json` — rates extraídos de conf
- `data/market_reference.*` — precios externos normalizados
- `data/price_dictionary.*` — piso/techo/mediana por ítem

## Criterio de salida de M1

M1 está listo cuando:

1. Todos los checkboxes de arriba están marcados o justificados como N/A.
2. Los hallazgos están documentados (secciones "Hallazgos").
3. El formato de `data/` está decidido con ejemplos reales.
4. Existe un plan concreto para M2 basado en datos, no en suposiciones.
