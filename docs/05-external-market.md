# Mercado externo y staging

## Decisión: sin análisis de jugadores locales

Llevamos poco tiempo jugando. Los precios de referencia vienen de **servidores públicos con API o datos accesibles**, no del snapshot de chars/inventory local.

El dump de `vendings` propio queda **pendiente** hasta tener una tienda en autotrade.

## Carpetas

| Carpeta | Propósito | En git |
|---------|-----------|--------|
| `staging/market/` | Probes temporales, verificar fidelidad | sí (muestras pequeñas) |
| `staging/market/*/bulk/` | Descargas masivas | no (gitignored) |
| `data/market/` | Dataset validado y promovido | sí |
| `data/raw/` | YAML y conf del servidor OzRo | sí |

## Fuentes (resumen)

Detalle completo en [`staging/market/README.md`](../staging/market/README.md).

### Atlantis Play-RO (histórico largo)

```
POST http://atlantis.play-ro.com/index.php
  item=501&send=Buscar&ant=ALL&ref=ALL&carta=ALL&forja=ALL
```

- Estadísticas: min, max, avg, std_dev, total_sold (~20 años de data)
- NPC buy/sell en la misma respuesta
- Servidor privado clásico — posiblemente más cercano a OzRo que bRO LATAM
- **Scraping HTML** — usar `fetch_atlantis.py` con delays; ver `sources.yaml` defaults

```bash
python staging/market/fetch_atlantis.py --items 501,909 --delay 3
python staging/market/fetch_atlantis.py --items-file staging/market/atlantis_playro/item_ids.txt \
  --delay 3 --jitter 2 --batch-pause-every 50 --batch-pause 60 --resume
```

### latam-tools (vending actual)

```
GET https://mercado.latam-tools.com.br/api/v1/prices?items=501,909&server=FREYA
```

- Precios reales de vending (median, min, max, cheapest stores)
- Servidor bRO LATAM — rates distintos a OzRo
- Recolectar con: `python staging/market/fetch_probe.py latam_tools --items ...`

### RagnaAPI

```
GET https://ragnapi.com/api/v1/re-newal/items/{id}
GET https://ragnapi.com/api/v1/re-newal/monsters/{id}
```

- Metadata, drops, equip jobs — **útil para quests y NPCs**
- Sin precios de mercado

### Divine Pride (pendiente API key)

- NPC `buyPrice` / `sellPrice` como ancla
- Registro: https://www.divine-pride.net/api

## Proceso de validación antes de promover

Para cada fuente, documentar en `staging/market/<fuente>/notes.md`:

1. **Cobertura:** % de ítems de nuestro catálogo que responden
2. **Coherencia:** comparar 5–10 ítems vs NPC buy/sell del YAML local
3. **Outliers:** precios absurdos o `offers: null`
4. **Decisión:** `promoted` / `rejected` / `partial` en `sources.yaml`

Solo tras `validated` → copiar/normalizar a `data/market/`.

## Ajuste de rates OzRo

Rates propios en `data/raw/server_rates.json`. Las fuentes externas usan economías distintas:

| Categoría OzRo | Multiplicador |
|----------------|---------------|
| common | 5x |
| heal / use | 10x |
| equip | 15x |
| card | 100x |

**No hay fórmula fija aún.** Validar empíricamente en staging antes de definir `price_dictionary`.

## Ítems sin referencia externa

IDs 35001–35005 (monedas OzRo, MVP_Soul): definir precios manualmente en diseño de NPC/quest.

## Scripts de recolección

| Script | Fuente | Modo |
|--------|--------|------|
| `fetch_probe.py` | latam-tools, ragnapi, divine_pride | prueba rápida |
| `fetch_atlantis.py` | atlantis.play-ro.com | **batch nocturno**, resumable |

### Política anti-bloqueo (Atlantis y similares)

Defaults en `sources.yaml` → `atlantis_playro.batch_defaults`:

- `--delay 3` + `--jitter 2` → 3–5s entre requests
- `--batch-pause-every 50 --batch-pause 60` → pausa larga cada 50 ítems
- `--timeout 30` + 3 reintentos con backoff exponencial
- `--resume` → salta ítems ya en `bulk/items/` o `progress.json`
- User-Agent identificado (`RagnaBots-Staging/0.1`)

Para un catálogo de ~2000 ítems a 4s promedio: ~2.2 horas. A 5000 ítems: dejar corriendo toda la noche con pausas es seguro.

Salida bulk en `staging/market/atlantis_playro/bulk/` (gitignored).
