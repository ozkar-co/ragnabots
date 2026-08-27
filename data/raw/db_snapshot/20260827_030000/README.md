# Snapshot DB — 2026-08-27 03:00

Fuente: `/home/oz/ozro-backup/backups/20260827_030000/`

## Tablas incluidas

| Tabla | SQL | JSON | Filas aprox |
|-------|-----|------|-------------|
| char | sí | sí | 26 |
| inventory | sí | sí | 791 |
| cart_inventory | sí | sí | 13 |
| storage | sí | no | — |
| guild* | sí | no | guild activa |
| party | sí | no | — |
| quest | sí | no | — |

## Tablas NO incluidas en este backup

El script `ozro-backup` no exportó estas tablas en este snapshot:

- `vendings` / `vending_items` — mercado actual (vacío o no capturado)
- `zenylog` / `picklog` — logs de economía
- `login` — **excluido a propósito** (contraseñas)

Para vending en vivo habrá que hacer dump directo de MySQL o esperar backup con esas tablas.

## Notas de jugadores (referencia para bots)

- Mapa principal de actividad: **geffen**
- Hay un char GM (`Dios`) con zeny inflado — excluir de métricas económicas
- Existe char merchant `Vendedor` (char_id 150014) — candidato a estudiar patrón de tienda
- 13 filas en `cart_inventory` — pocos merchants activos con carro
