# Atlantis Play-RO — notas de validación

Fuente: [atlantis.play-ro.com](http://atlantis.play-ro.com/index.php)

## Qué aporta

Resumen estadístico histórico por ítem (POST a `/index.php`):

| Campo | Ejemplo item 501 |
|-------|------------------|
| Precio mínimo | 0 |
| Precio máximo | 700,000 |
| Cantidad total vendida | 229,735 |
| Desviación estándar | 18,511 |
| Precio promedio | 50 |
| NPC buy | 50 |

Parámetros del formulario:
- `item` — ID o nombre
- `ant=ALL` — toda la data disponible (~20 años)
- `ref=ALL`, `carta=ALL`, `forja=ALL` — sin filtrar refine/cards/forge

## Ventajas vs latam-tools

- Histórico largo, volumen de transacciones (`total_sold`)
- `std_dev` útil para detectar ítems volátiles
- Incluye NPC buy/sell en la misma página
- Servidor privado clásico (Atlantis) — puede ser más cercano a OzRo que bRO LATAM

## Limitaciones

- Scraping HTML (sin API JSON) — frágil si cambian el layout
- `avg` puede estar distorsionado por outliers antiguos (ej. max 700k en red potion)
- Rate limit desconocido — **usar delays generosos**
- Ítems custom OzRo (35001+) probablemente sin data

## Recolección

```bash
# Prueba rápida
python staging/market/fetch_atlantis.py --items 501,909,1201

# Batch nocturno (reanudable)
python staging/market/fetch_atlantis.py \
  --items-file staging/market/atlantis_playro/item_ids.txt \
  --delay 3 --jitter 2 \
  --batch-pause-every 50 --batch-pause 60 \
  --resume
```

Defaults conservadores: 3s + jitter, pausa 60s cada 50 ítems.

## Validación pendiente

- [ ] Comparar `avg` vs `offers.median` latam-tools en 20 ítems
- [ ] Decidir si usar `avg`, mediana estimada, o percentil para price_dictionary
- [ ] Probar ítems equip/card con alta varianza
