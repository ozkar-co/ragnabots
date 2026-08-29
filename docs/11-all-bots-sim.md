# All-bots: cobertura de mapas + sim 100d

Fecha: 2026-08-28  
```bash
python staging/market/bots/build_and_simulate_all.py
```
Salida: `staging/market/bots/all_bots/`

## Qué se generó

| | |
|--|--|
| Regla | **1 bot ≈ 1 mapa** con ≥2 mats del pool vendible |
| Total bots | **246** |
| Activos en sim | **173** (novice→hard) |
| Expert diferidos | **73** (catalogados, grind=0 hasta unlock lejano) |
| Skip | instancias `1@…`, job_, etc. + mapas sin oferta |

### Por tier / unlock

| Tier | Bots | Unlock (días activos server) |
|------|------|------------------------------|
| novice | 24 | 0 |
| easy | 27 | 0 |
| mid | 53 | 7 |
| hard | 69 | 21 |
| expert | 73 | diferido |

## Sim 100d (cota superior)

Asume login **todos** los días × 3.5 h. En runtime real será menos.

| Métrica lote @100d | |
|--------------------|--|
| mediana | ~26M |
| p25 / p75 | ~11M / ~87M |
| suma (173 bots) | ~14.4B (teórica si todos activos siempre) |
| nets negativos | 14 (casi todos hard flojos) |

### Rotación (como querías)

- **Alta:** Sticky Mucus (59 bots), Green Herb (54), Rough Oridecon (50), Red Herb (41)…
- **Baja / meses quietos:** Cursed Seal, Gift Box, Old Blue Box en hard (pocas unidades @100d)

### Archivos

| Archivo | Uso |
|---------|-----|
| `index.json` | lista compacta id/mapa/tier/mats/lot |
| `catalog.json` | detalle completo por bot |
| `analysis_100d.json` / `.md` | análisis |

## Sell-down

Tras día 100: sin grind nuevo; tiendas venden remanente hasta gates / stock≈0 → desaparecen.  
Afinar mercado con datos guardados de ventas reales vs esta proyección.
