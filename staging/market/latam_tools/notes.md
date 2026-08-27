# latam-tools — notas de validación

## Probe inicial (2026-08-27)

Archivo: `samples/20260827T232539Z_batch_FREYA_501-909-1201-607.json`

| item_id | nombre | offers.median | market.avg | notas |
|---------|--------|---------------|------------|-------|
| 501 | Poção Vermelha | 30 | 521860 | histórico avg inflado vs vending actual |
| 909 | Jellopy | 2098 | 7431 | buena señal vending |
| 1201 | Faca +3 | 1999999 | 369999 | equip caro, pocas ofertas |
| 607 | ? | revisar | revisar | |

## Observaciones

- `market.avg` parece histórico de transacciones oficiales — puede divergir mucho de `offers.median`
- Para bots: preferir `offers.median` o `offers.min` cuando hay stock
- `offers: null` cuando no hay tiendas abiertas — no es error de API
- Servidor FREYA vs NIDHOGG: probar ambos para mismos ítems

## Pendiente validar

- [ ] Comparar 10 ítems comunes vs NPC sell del YAML local
- [ ] Probar batch de 50 ítems del catálogo OzRo
- [ ] Documentar factor de escala si hace falta vs OzRo rates
