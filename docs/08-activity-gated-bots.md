# Runtime diario de bots (percepción = solo tiendas)

Fecha: 2026-08-28  
Estado: **diseño aceptado** (runtime aún no implementado)  
Complementa: [07-bot-design-sample.md](07-bot-design-sample.md)

## Principio

Los jugadores **solo perciben** a los bots a través de las **tiendas autotrade**.  
No hace falta simular presencia en mapas ni polls frecuentes. Un script **ligero, 1×/día** basta.

```
Jugador ve: tienda abierta / cerrada / movida / stock distinto
Nosotros tenemos: estado interno precalculado (inventario, zeny, lote, gates)
```

## Dos jobs diarios

### A — Mañana / tarde: grind + oferta (vender)

```
1. Contar jugadores reales que se conectaron HOY
   (ver sección Actividad — consulta simple)

2. Si count == 0 → no acreditar grind nuevo; opcionalmente
   dejar tiendas como están o caducar suave

3. Si count >= 1:
   - horas_bot = 3.5  (estándar 3~4; no hace falta duración exacta)
   - elegir al azar X bots del pool elegible
     (X = f(count); tiers altos requieren más días/horas acumuladas)
   - aplicar stats precalculadas × horas → Δ inventario, Δ zeny gasto
   - decidir abrir / cerrar / refrescar tiendas según gates
   - coordenadas: random dentro del área que definas (por ciudad/mapa)

4. Escribir solo lo visible: filas vendings / vending_items (+ zeny char)
```

### B — Noche: compras a jugadores

```
1. Leer tiendas autotrade de jugadores reales (vendings)

2. Por cada bot comprador elegible (con zeny > 0):
   - mirar ítems en rango de precio del diccionario (LATAM / YAML NPC)
   - comprar aleatoriamente pocas unidades
   - tope duro: no gastar más que su zeny actual
   - tope suave: máx % del zeny o máx N compras/noche

3. Así no hay comprador compulsivo ni exploit de zeny infinito
```

Ambos jobs son **batch**, no daemons. Fácil de cron-ear y de dry-run.

## Actividad del día (KISS)

No necesitamos “horas exactas conectado” con una sola query.

| Enfoque | Query / señal | Uso |
|---------|---------------|-----|
| **Elegido** | `COUNT` chars con `last_login` ∈ hoy (excl. bots) | ¿Hubo gente hoy? ¿Cuántos? |
| Opcional | `char.online` ahora | irrelevante para batch diario |
| Evitar | poll cada 5 min | overkill si solo se ve la tienda |

```text
jugadores_hoy = chars WHERE DATE(last_login) = CURDATE()
  AND account_id NOT IN (bot_accounts)
  AND char_id NOT IN (bot_chars)
  -- opcional: excluir chars que SOLO existen como autotrade vacío
```

Luego:

```text
horas_acreditadas_por_bot_activo = 3.5   # estándar 3~4
bots_despertados = f(jugadores_hoy)     # 0 si nadie; más si hay varios
```

Semanas vacías → sin progreso interno ni tiendas nuevas.  
Días con 1–5 jugadores → escala orgánica.

## Progresión por tier (percepción de “el server crece”)

Los bots de **tier más alto** no aparecen el día 1.

| Condición (ejemplo tunable) | Qué desbloquea |
|-----------------------------|----------------|
| `server_active_days >= 0` | novice / easy |
| `server_active_days >= 7` o `cum_player_days >= N` | mid |
| `server_active_days >= 21` | hard (si se usan) |
| expert | fuera del pool o muy tarde / restringido |

`server_active_days` = días con `jugadores_hoy >= 1`.  
Los jugadores verán primero mats baratos en Prontera/Payon; luego orcos, spiders, etc.

Misma idea para **diversidad de oferta**: el catálogo de la tienda refleja el tier desbloqueado + inventario acumulado.

## Tiendas: orgánico y barato

- Abrir / cerrar / refrescar stock **solo en el job diario**
- **Mover** la tienda a coords random dentro de un área fija (tú defines el polígono/bbox por ciudad)
- No quitar tienda hasta `vendido >= keep_shop_frac × lote_esperado` (o zeny equivalente)
- No volver a “grindear” ese bot hasta `vendido >= pause_frac × lote`
- Stagger: no abrir las 20 tiendas el mismo día; random subset

El jugador percibe: “ayer había un merchant aquí, hoy otro allá con stock distinto”.

## Compras nocturnas (anti-exploit)

| Regla | Detalle |
|-------|---------|
| Precio | solo si `precio_tienda ∈ [floor, ceiling]` del diccionario |
| Floor | ≈ NPC buy YAML o sell×0.5 (tunable) |
| Ceiling | LATAM `offers_median` (techo de compra a jugadores) |
| Zeny | `gasto <= bot.zeny`; nunca crédito infinito |
| Volumen | máx N ítems o % zeny por noche |
| Aleatorio | no comprar todo lo “barato”; sample |

El bot gasta zeny que **ganó vendiendo** (ciclo cerrado). Si no vendió, no compra.

## Datos precalculados vs runtime

| Pregen (`preview_sim` → tablas) | Runtime diario |
|---------------------------------|----------------|
| loot/h, gasto/h, oferta top, cards policy | × horas (3.5) × bots elegidos |
| gates pause/shop | comparar contra ventas reales del día (vending log o delta stock) |
| tier / mapas | filtro de elegibilidad |

No se resimula el combate en vivo: solo se aplica la fila precalculada.

## Escala ejemplo

| `jugadores_hoy` | Bots que acreditan grind | Tiendas tocadas (abrir/mover/cerrar) |
|-----------------|--------------------------|--------------------------------------|
| 0 | 0 | 0 (o solo caducar) |
| 1 | 2–4 | 1–3 |
| 2–3 | 5–8 | 3–5 |
| 4–5+ | 10–15 | 5–8 |

Pool ~100; activos por día << pool.

## Pendiente

- [ ] Áreas de vending (coords) por ciudad — las defines tú
- [ ] Confirmar `vendings` / autotrade en MySQL OzRo
- [ ] Schema: `bot_profiles`, `bot_hour_stats`, `bot_state`, `bot_shop_meta`
- [ ] Cron A (oferta) + Cron B (compras)
- [ ] Dry-run contra SQLite antes de prod
- [ ] Ajustar `hours_per_day` en sim a **3.5** (alineado con runtime)

## Ciclo de vida (acordado)

```
días 1..~100 (si hubo login):
  acreditar grind 3.5h × bots elegibles
  actualizar tiendas

después:
  sin grind nuevo
  solo vender remanente → desaparecen
```

Detalle de oferta por bot y spend: [09-shop-catalog-review.md](09-shop-catalog-review.md).
