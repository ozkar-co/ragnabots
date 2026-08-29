# Runtime diario de bots (percepción = solo tiendas)

Fecha: 2026-08-28  
Estado: **diseño aceptado** (runtime aún no implementado)  
Complementa: [07-bot-design-sample.md](07-bot-design-sample.md) · [12-buy-from-players.md](12-buy-from-players.md)

## Principio

Los jugadores **solo perciben** a los bots a través de las **tiendas autotrade**.  
No hace falta simular presencia en mapas ni polls frecuentes. Un script **ligero, 1×/día** basta.

```
Jugador ve: tienda abierta / cerrada / movida / stock distinto
Nosotros tenemos: estado interno precalculado (inventario, zeny, lote, gates)
```

## Un solo job diario (orden fijo)

Un cron, tres fases en secuencia. Cada fase usa el estado que dejó la anterior.

```
1. COMPRA a jugadores   (si hay tiendas de jugadores)
2. TIENDAS              (abrir / cerrar / refrescar / mover)
3. GRIND                (solo bots elegibles)
```

### 1 — Compra a jugadores

Si **no** hay tiendas autotrade de jugadores → skip (no hay nada que comprar).

Si hay:

```
elegir N bots con zeny
  → sample 2–5 listings de jugadores
  → si price > LATAM: nunca
  → si no: comprar con P = 0.85*(1-price/LATAM)^1.15
  → qty random del stock, budget ≤ 30% zeny
```

Detalle y curva: [12-buy-from-players.md](12-buy-from-players.md).

Efecto: los bots gastan zeny **antes** de decidir tiendas/grind → el estado de zeny ya refleja compras del día.

### 2 — Abrir / cerrar / refrescar tiendas

Tras las compras (y ventas reales del día vía delta stock / vending log):

```
1. Contar jugadores_hoy (ver Actividad)
2. Evaluar gates por bot:
   - keep_shop: ¿seguir en vending o cerrar?
   - abrir / refrescar / mover coords (área que definas)
   - stagger: subset random, no tocar todas el mismo día
3. Escribir solo lo visible: vendings / vending_items (+ zeny char)
```

| Gate | Regla (tunable) |
|------|-----------------|
| Mantener tienda | hasta `vendido >= keep_shop_frac × lote` (~60%) |
| Cerrar / desaparecer | stock≈0 o ciclo sell-down terminado |
| Abrir nueva | bot con inventario, tier desbloqueado, slot libre |

Si `jugadores_hoy == 0`: no abrir tiendas nuevas; opcional caducar suave.

### 3 — Grind (recalcular)

Solo bots que cumplan **todas** las condiciones:

| Condición | |
|-----------|--|
| **No está en tienda** | bot con vending abierta no grindea |
| Tier desbloqueado | según `server_active_days` |
| No en pause_grind | `vendido < pause_frac × lote` (~40%) → sigue “vendiendo”, no acredita loot |
| Ciclo activo | día ≤ ~100 (después solo sell-down) |
| Elegido hoy | sample random X = f(`jugadores_hoy`) |

```
si jugadores_hoy == 0 → nadie grindea
si no:
  horas = 3.5
  para cada bot elegible del sample:
    aplicar loot/h × horas, gasto/h × horas → Δ inventario, Δ zeny
```

No se resimula combate: solo la fila precalculada × horas.

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
```

```text
horas_acreditadas_por_bot_activo = 3.5
bots_despertados = f(jugadores_hoy)     # 0 si nadie; más si hay varios
```

Semanas vacías → sin progreso interno ni tiendas nuevas.  
Días con 1–5 jugadores → escala orgánica.

## Progresión por tier

| Condición (ejemplo tunable) | Qué desbloquea |
|-----------------------------|----------------|
| `server_active_days >= 0` | novice / easy |
| `server_active_days >= 7` | mid |
| `server_active_days >= 21` | hard |
| expert | fuera del pool o muy tarde |

`server_active_days` = días con `jugadores_hoy >= 1`.

## Tiendas: orgánico y barato

- Abrir / cerrar / refrescar **solo en la fase 2** del job diario
- **Mover** coords random dentro del área fija (tú defines bbox por ciudad)
- Stagger: no abrir las 20 tiendas el mismo día

El jugador percibe: “ayer había un merchant aquí, hoy otro allá con stock distinto”.

## Compras (anti-exploit) — resumen

| Regla | Detalle |
|-------|---------|
| Techo | `price > LATAM` → nunca |
| Zeny | `gasto <= ledger.zeny` (y char si aplica); budget ~25–30% |
| Origen | solo zeny ganado vendiendo a jugadores — **no mintar** |
| Volumen | sample listings + caps qty |
| Skip | si no hay tiendas de jugadores |

Ledger + spend: [13-zeny-and-spend.md](13-zeny-and-spend.md).

## Datos precalculados vs runtime

| Pregen | Runtime diario |
|--------|----------------|
| loot/h, gasto/h, oferta, cards | × 3.5h × bots elegibles (fase 3) |
| gates pause/shop | ventas reales → fase 2 |
| LATAM ref | compras fase 1 |

## Escala ejemplo

| `jugadores_hoy` | Bots que acreditan grind | Tiendas tocadas |
|-----------------|--------------------------|-----------------|
| 0 | 0 | 0 (o solo caducar) |
| 1 | 2–4 | 1–3 |
| 2–3 | 5–8 | 3–5 |
| 4–5+ | 10–15 | 5–8 |

## Ciclo de vida

```
días 1..~100 (si hubo login):
  1 compra → 2 tiendas → 3 grind (elegibles)

después:
  1 compra → 2 tiendas (sell-down)
  sin grind nuevo → desaparecen al vaciar
```

## Pendiente

- [ ] Áreas de vending (coords) por ciudad — las defines tú
- [ ] Confirmar `vendings` / autotrade en MySQL OzRo
- [ ] Schema: `bot_profiles`, `bot_hour_stats`, `bot_state`, `bot_shop_meta`
- [ ] Un cron diario (3 fases)
- [ ] Dry-run contra SQLite antes de prod

Detalle oferta: [09-shop-catalog-review.md](09-shop-catalog-review.md).  
Zeny/spend: [13-zeny-and-spend.md](13-zeny-and-spend.md).
