# RagnaBots

Bots económicos para un servidor privado de Ragnarok Online (rAthena). El objetivo es dar vida al mercado: tiendas autotrade creíbles y compras razonables a jugadores reales, sin romper la economía del servidor.

Proyecto personal, mantenido por una sola persona. Enfoque **data-first**: primero datos reales, luego código.

## Estado actual

**M0** — Documentos de diseño. Sin código de negocio aún.

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
| [docs/04-open-questions.md](docs/04-open-questions.md) | Decisiones pendientes |

## Estructura

```
ragnabots/
├── docs/           # Memoria del proyecto (commitear)
├── data/           # Artefactos recolectados (M1+)
├── requirements.txt
└── README.md
```

## Próximo paso (M1)

Ejecutar el checklist de `docs/02-data-inventory.md`: recolectar YAML de rAthena, rates de config, clonar la DB del servidor, inspeccionar schema real. El código vendrá después.
