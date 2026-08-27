# Clon del servidor: MySQL → SQLite

Procedimiento para crear una copia local de la DB de producción y usarla como sandbox de desarrollo. Los bots se diseñarán observando datos reales de jugadores existentes.

## Por qué clonar en lugar de inventar schema

- El schema real puede diferir de la documentación genérica de rAthena.
- Los jugadores reales (familia) dan patrones de referencia: precios, horarios, mapas.
- Probar escrituras en SQLite no afecta producción.
- FailFast: si el código no funciona contra el clon, no va a producción.

## Paso 1: Dump MySQL

Desde el servidor o con acceso remoto:

```bash
# Dump completo (ajustar credenciales y nombre de DB)
mysqldump -u USUARIO -p NOMBRE_DB > data/dumps/rathena_$(date +%Y%m%d).sql

# O subset de tablas relevantes (más liviano)
mysqldump -u USUARIO -p NOMBRE_DB \
  char inventory cart_inventory \
  vendings vending_items \
  zenylog picklog \
  > data/dumps/rathena_subset_$(date +%Y%m%d).sql
```

**Nota:** `data/dumps/` está en `.gitignore`. Solo commitear metadata (fecha, tablas incluidas) en `data/manifest.json`.

## Paso 2: Conversión a SQLite

Opciones (decidir en M1 tras ver tamaño del dump):

### Opción A: Herramienta automática

```bash
# Ejemplo con mysql2sqlite (instalar si hace falta en M1)
# pip install mysql-to-sqlite3  → añadir a requirements.txt entonces
mysql2sqlite -f data/dumps/rathena_subset_YYYYMMDD.sql -d rathena_local.db
```

### Opción B: Script puntual

Si la herramienta falla con tipos rAthena-específicos (ENUM, etc.), escribir un script mínimo que importe solo las tablas necesarias, adaptando tipos a SQLite.

### Opción C: Import directo con sqlite3

Para dumps pequeños, conversión manual de CREATE TABLE (cambiar tipos MySQL → SQLite).

## Paso 3: Ubicación del clon

| Archivo | Ubicación | En git? |
|---------|-----------|---------|
| Dump SQL crudo | `data/dumps/*.sql` | No (.gitignore) |
| SQLite local | `rathena_local.db` (raíz o `data/`) | No (.gitignore) |
| Metadata del snapshot | `data/manifest.json` | Sí |

Ejemplo de `data/manifest.json`:

```json
{
  "snapshot_date": "2026-08-27",
  "source": "mysql://servidor/ragnarok",
  "tables": ["char", "inventory", "cart_inventory", "vendings", "vending_items"],
  "char_count": null,
  "vending_count": null,
  "notes": "Completar tras inspección en M1"
}
```

## Paso 4: Inspección inicial

Tras importar, ejecutar queries exploratorias (anotar resultados en [02-data-inventory.md](02-data-inventory.md)):

```sql
-- Personajes y zeny
SELECT char_id, name, zeny, class, base_level
FROM char ORDER BY zeny DESC LIMIT 20;

-- Tiendas activas
SELECT v.id, v.char_id, c.name, v.map, v.x, v.y, v.title, v.autotrade
FROM vendings v JOIN char c ON v.char_id = c.char_id;

-- Precios del mercado actual
SELECT vi.price, ci.nameid, v.map, c.name AS seller
FROM vending_items vi
JOIN vendings v ON vi.vending_id = v.id
JOIN cart_inventory ci ON vi.cartinventory_id = ci.id
JOIN char c ON v.char_id = c.char_id
ORDER BY vi.price DESC LIMIT 50;
```

## Paso 5: Refrescar el clon

Repetir dump + conversión cuando:

- Cambie el schema (update de rAthena).
- Pasen varias semanas y los datos estén muy desactualizados.
- Se quiera validar contra estado reciente del mercado.

No automatizar el refresh hasta que el flujo manual esté probado.

## Tablas: prioridad para bots

### Críticas (siempre incluir en clon)

- `char` — zeny, identidad de bots y jugadores
- `cart_inventory` — ítems en carro de merchant
- `vendings` — tiendas abiertas
- `vending_items` — listados y precios

### Útiles (incluir si el dump no es enorme)

- `inventory` — qué farmean los jugadores reales
- `zenylog` — auditoría de flujo de zeny
- `picklog` — historial de transacciones de ítems

### Ignorar (salvo necesidad específica)

- `guild_*`, `party`, `mail`, `friends` — no relevantes para economía de bots
- `login`, `ipbanlist` — seguridad, no economía
- Logs masivos si el dump es >100MB

## Seguridad

- No commitear dumps ni `.db` con datos de jugadores.
- Si se comparte el repo, verificar que `.gitignore` cubre `*.db` y `data/dumps/`.
- Credenciales MySQL solo en `.env` (nunca en git).

## Preguntas abiertas (resolver en M1)

- [ ] ¿Tamaño real del dump completo vs subset?
- [ ] ¿Herramienta de conversión funciona con nuestro schema?
- [ ] ¿Hay tablas custom del servidor no estándar de rAthena?
- [ ] ¿char_ids de bots ya existen o hay que crearlos?
