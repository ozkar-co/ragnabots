# Staging — datos en prueba

Carpeta **temporal** para recolectar y validar datos externos antes de promoverlos a `data/`.

## Flujo

```
YAML local → item_ids_all.txt (~29k)
     ↓
fetch_batch.py (por fuente, resumable)
     ↓
staging/market/*/bulk/  →  revisión  →  data/market/
```

## Script principal: `fetch_batch.py`

```bash
# 1. Generar lista de todos los ítems del juego (desde YAML local)
python staging/market/fetch_batch.py extract-ids

# 2. Descargar por fuente (dejar corriendo de noche, --resume si se corta)
python staging/market/fetch_batch.py latam --server FREYA --resume
python staging/market/fetch_batch.py atlantis --resume
python staging/market/fetch_batch.py ragnapi --resume
export DIVINE_PRIDE_API_KEY=...
python staging/market/fetch_batch.py divine_pride --resume

# 3. Todo en secuencia
python staging/market/fetch_batch.py all --resume --sources atlantis,latam,ragnapi

# Prueba con pocos ítems
python staging/market/fetch_batch.py latam --limit 100 --delay 1
```

## Tiempos estimados (~29,059 ítems)

| Fuente | Modo | Delay default | Tiempo aprox |
|--------|------|---------------|--------------|
| **latam** | 100 ítems/request | 5s entre chunks (~291 chunks) | **~30 min** |
| **atlantis** | 1 ítem/request | 3–5s + pausa 60s/50 | **~33 h** |
| **ragnapi** | 1 ítem/request | 2–3s + pausa 45s/100 | **~22 h** |
| **divine_pride** | 1 ítem/request | 2–3s + pausa 45s/100 | **~22 h** |

Recomendación: correr **latam primero** (rápido), luego atlantis + ragnapi en paralelo en máquinas distintas o en secuencia varias noches.

## Anti-bloqueo (todas las fuentes)

- `--delay` + `--jitter` entre requests/chunks
- `--batch-pause-every N --batch-pause S` pausas largas periódicas
- `--resume` salta ítems ya en `bulk/items/` o `progress.json`
- `--timeout 30` + reintentos con backoff
- User-Agent identificado

## Estructura

```
staging/market/
├── fetch_batch.py          # CLI unificado
├── batch_common.py         # delays, progress, HTTP
├── runners.py              # lógica por fuente
├── extract_item_ids.py     # YAML → item_ids_all.txt
├── item_ids_all.txt        # ~29k IDs (gitignored, regenerable)
├── fetch_probe.py          # pruebas puntuales (legacy)
└── {atlantis,latam_tools,ragnapi,divine_pride}/
    └── bulk/               # gitignored
```

## Qué va a git

- Scripts, docs, `sources.yaml`, muestras pequeñas en `samples/`
- **No** `item_ids_all.txt`, **no** `bulk/`

## Usos del dataset

| Uso | Fuentes |
|-----|---------|
| Precios bots | atlantis + latam |
| NPC shops / quests | ragnapi + atlantis NPC + YAML local |
| Ítems custom OzRo (35001+) | solo YAML local |
