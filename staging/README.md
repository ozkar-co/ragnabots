# Staging — datos en prueba

Carpeta **temporal** para recolectar y validar datos externos antes de promoverlos a `data/`.

## Flujo

```
Internet / API  →  staging/.../samples/  →  revisión manual  →  data/ (dataset canónico)
```

**No promover a `data/`** hasta verificar:
- El ítem existe en nuestro `item_db` (o documentar por qué es custom)
- Los precios tienen sentido vs NPC buy/sell local
- La fuente tiene cobertura aceptable para el ítem
- El rate del servidor referencia es documentado

## Estructura

```
staging/
├── README.md                 # este archivo
└── market/
    ├── README.md             # fuentes de mercado
    ├── sources.yaml          # catálogo de fuentes y estado
    ├── fetch_probe.py        # prueba rápida (APIs JSON)
    ├── fetch_atlantis.py     # batch nocturno Atlantis (HTML, resumable)
    ├── atlantis_playro/
    ├── latam_tools/samples/
    └── ragnapi/samples/
```

## Scripts

**Prueba rápida (APIs JSON):**

```bash
python staging/market/fetch_probe.py latam_tools --items 501,909 --server FREYA
python staging/market/fetch_probe.py ragnapi --items 501 --monsters 1002
```

**Batch nocturno Atlantis** ([play-ro.com](http://atlantis.play-ro.com/index.php)) — histórico ~20 años, stats min/max/avg/std:

```bash
python staging/market/fetch_atlantis.py --items 501,909 --delay 3
python staging/market/fetch_atlantis.py \
  --items-file staging/market/atlantis_playro/item_ids.txt \
  --delay 3 --jitter 2 --batch-pause-every 50 --batch-pause 60 --resume
```

Divine Pride (opcional, requiere API key):

```bash
export DIVINE_PRIDE_API_KEY=tu_key
python staging/market/fetch_probe.py divine_pride --items 501
```

## Qué va a git

- Estructura, docs, muestras pequeñas de verificación
- Descargas masivas o re-fetch frecuente: mantener local o en `staging/**/bulk/` (gitignored)

## Usos del dataset final (no solo bots)

| Uso | Fuentes típicas |
|-----|-----------------|
| Precios de bots / diccionario económico | atlantis_playro, latam_tools, Divine Pride |
| Diseño de NPC shops | NPC buy/sell local + mercado externo |
| Balance de quests (recompensas) | drops rAthena + precios mercado |
| Ítems custom OzRo | solo YAML local — sin fuente externa |
