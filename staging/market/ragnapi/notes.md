# RagnaAPI — notas de validación

## Probe inicial (2026-08-27)

Archivo: `samples/20260827T232541Z_items-501-909_mobs-1002-1111.json`

## Qué aporta

- **Items:** descripción, jobs equipables, `drop_rate[]` con mob y %
- **Monsters:** stats, elemental, drops con rate

## Qué NO aporta

- Precios de vending
- NPC buy/sell
- Ítems custom OzRo (35001+)

## Uso previsto

- Diseño de quests: qué mobs dropean qué ítems
- NPCs que venden loot de zona X
- Complemento a YAML local (validar que IDs coinciden)

## Pendiente

- [ ] Cruzar drops RagnaAPI vs `mob_db.yml` local para Poring (1002)
- [ ] Ver si mob 1111 (Drainliar custom) difiere del import local
