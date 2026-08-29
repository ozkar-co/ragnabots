# Preguntas abiertas

Decisiones aplazadas. Las resueltas van abajo con respuesta.

## Abiertas (pocas)

| # | Pregunta | Contexto |
|---|----------|----------|
| 2 | ¿Scripts flat vs paquete `src/`? | KISS: flat en staging está bien por ahora |
| 5 | ¿Normalizar precios LATAM → rates OzRo? | Hoy usamos LATAM crudo; ajustar solo si se siente caro/barato in-game |
| 7 | ¿Drops 1× coinciden con `@mobinfo`? | Validar muestra cuando haya cliente |
| 9 | ¿char_ids de bots ya existen? | Revisar `char` al montar chars de bots |
| 11 | ¿Áreas / coords de vending? | **Tú** cuando montes el cliente + autotrade |

## Resueltas

### #4 — Fuentes de mercado
**Respuesta:** Nos quedamos con lo que tenemos: **LATAM** (precios), **Atlantis** (filtro histórico / grindable), **YAML NPC** OzRo, spawns rAthena. **Sin Divine Pride.** RagnaAPI solo si hace falta metadata puntual.
**Fecha:** 2026-08-28

### #8 — Perfiles de bots
**Respuesta:** Diseño manual; no derivar de jugadores locales. Precios LATAM.
**Fecha:** 2026-08-27

### #10 — “Priorizar familia”
**Respuesta:** **No aplica.** Era una idea temprana de comprar preferente a chars de la familia vs desconocidos. En servidor familiar todos son “familia”; los bots compran a **cualquier** jugador real con precio ≤ LATAM, sin favoritos.
**Fecha:** 2026-08-28

### #11 — Vendings locales
**Respuesta:** Aplazado hasta cliente + autotrade. Áreas de vending las defines tú entonces.
**Fecha:** 2026-08-28

### #12 — Resolución temporal
**Respuesta:** Batch **1×/día**. Ver [08](08-activity-gated-bots.md).
**Fecha:** 2026-08-28

### #14 — “Umbral economía sana”
**Respuesta:** **No métrica formal.** Era la idea M3 de un número mágico (“si inflación &lt; X → OK”). En la práctica: mirar tiendas, zeny de bots, y sentido común. Si algo se descontrola, se bajará sample/día o caps a mano.
**Fecha:** 2026-08-28

### #17 — zenylog / picklog
**Respuesta:** **No es decisión de diseño ahora.** Son tablas de log de rAthena (movimientos de zeny / picks). Solo importa al inyectar en MySQL: si queremos que las compras de bots aparezcan en esos logs para depurar. Default: no inventar filas ahí hasta que haga falta auditar.
**Fecha:** 2026-08-28

### #18 — Activity-gate + runtime
**Respuesta:** Un cron: compra → tiendas → grind. Ver [08](08-activity-gated-bots.md).
**Fecha:** 2026-08-28

### #13 / #16 — Auditoría IA / watcher
**Respuesta:** Aplazado a mucho más adelante (post-runtime). No bloquea.
**Fecha:** 2026-08-28

### #15 — DRY_RUN
**Respuesta:** Sí, por defecto hasta validar en clon.
**Fecha:** 2026-08-28
