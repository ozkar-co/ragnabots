# RagnaBots

Bots económicos para un servidor privado de Ragnarok Online (rAthena). El objetivo es dar vida al mercado: tiendas autotrade creíbles y compras razonables a jugadores reales, sin romper la economía del servidor.

Proyecto personal, mantenido por una sola persona. Enfoque **data-first**: primero datos reales, luego código.

## Estado actual

**M1 en curso** — LATAM FREYA completo (29k escaneados, 5.3k con precio útil).

- `staging/market/latam_tools/curated/` — listas refinadas (commitear)
- `staging/market/latam_tools/bulk/` — bulk 115 MB (local, gitignored)
- Próximo: Atlantis sobre `top2000_ids.txt` — ver [docs/06-market-curation-plan.md](docs/06-market-curation-plan.md)

## Staging (mercado externo)

```bash
python staging/market/fetch_probe.py latam_tools --items 501,909,1201 --server FREYA
python staging/market/fetch_probe.py ragnapi --items 501 --monsters 1002
```

Ver [docs/05-external-market.md](docs/05-external-market.md).

## Cómo retomar

```bash
cd ragnabots
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Lee los docs en orden:

| Doc | Contenido |
|-----|-----------|
| [docs/00-principles.md](docs/00-principles.md) | KISS, DRY, SRP, FailFast, data-first |
| [docs/01-vision.md](docs/01-vision.md) | Objetivo, etapas, qué no es el proyecto |
| [docs/02-data-inventory.md](docs/02-data-inventory.md) | Checklist de datos a recolectar (M1) |
| [docs/03-server-snapshot.md](docs/03-server-snapshot.md) | Clon MySQL → SQLite para desarrollo |
| [docs/06-market-curation-plan.md](docs/06-market-curation-plan.md) | Curación por capas: 5k → 2k → 1k → NPCs |

## Estructura

```
ragnabots/
├── docs/           # Memoria del proyecto
├── data/           # Dataset validado (raw/ + market/ cuando se promueva)
├── staging/        # Probes temporales — revisar antes de data/
├── requirements.txt
└── README.md
```

## Próximo paso (M1)

1. Validar muestras en `staging/market/` (ver notas por fuente)
2. Obtener Divine Pride API key para NPC buy/sell
3. Ampliar batch de ítems representativos
4. Promover fuentes validadas a `data/market/`
5. Vendings OzRo cuando haya autotrade
