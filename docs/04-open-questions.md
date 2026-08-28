# Preguntas abiertas

Decisiones **intencionalmente aplazadas** hasta tener datos reales. Actualizar este archivo en cada iteración: mover preguntas resueltas a una sección "Resueltas" con la respuesta.

## Formato y estructura

| # | Pregunta | Contexto |
|---|----------|----------|
| 1 | ¿JSON, CSV o Parquet para artefactos en `data/`? | Depende del volumen tras inspección M1 |
| 2 | ¿Estructura de módulos Python? | Flat scripts vs paquete `src/` — decidir tras M1 |
| 3 | ¿Un script por etapa o CLI unificada? | KISS sugiere scripts separados al inicio |

## Datos y precios

| # | Pregunta | Contexto |
|---|----------|----------|
| 4 | ¿Qué fuente(s) de mercado externo usar? | latam-tools + RagnaAPI en staging; Divine Pride con key |
| 5 | ¿Cómo normalizar precios al rate custom del servidor? | Rates salen de conf, no asumir fórmula |
| 6 | ¿Hay ítems custom no presentes en DBs públicas? | Revisar item_db real |
| 7 | ¿Fórmula de drop efectivo coincide con `@mobinfo` en juego? | Validar muestra en M2 |

## Bots y jugadores

| # | Pregunta | Contexto |
|---|----------|----------|
| 8 | ¿Cuántos bots y qué roles? | Diseño manual — no basado en jugadores locales |
| 9 | ¿char_ids de bots ya existen en el servidor? | Revisar tabla `char` |
| 10 | ¿Priorizar compras a char_ids de familia? | Decisión de diseño M5 |
| 11 | ¿Coordenadas de vending? | Pendiente; dump vendings cuando haya autotrade |

## Simulación y auditoría

| # | Pregunta | Contexto |
|---|----------|----------|
| 12 | ¿Resolución temporal del sandbox (1h, 1d)? | Decidir en M2 |
| 13 | ¿Provider de IA para auditoría? | OpenAI, local, o solo métricas — M3 |
| 14 | ¿Umbral de "economía sana" antes de ir a producción? | Definir tras primeras simulaciones |

## Producción

| # | Pregunta | Contexto |
|---|----------|----------|
| 15 | ¿DRY_RUN por defecto hasta validar en clon SQLite? | Sí por principio FailFast |
| 16 | ¿Intervalo del market watcher? | M5, tras probar manualmente |
| 17 | ¿Registrar en zenylog/picklog las transacciones de bots? | Revisar si el servidor usa esos logs |

---

### #4 — Fuentes de mercado externo
**Respuesta:** LATAM completo (29k). Curar en capas: 5328 → 2000 → 1000 → 100-200 NPCs. Atlantis siguiente.
**Fecha:** 2026-08-28
**Etapa:** M1

### #8 — Perfiles de bots
**Respuesta:** No derivar de jugadores locales. Diseñar perfiles manualmente; precios desde mercado externo validado.
**Fecha:** 2026-08-27
**Etapa:** M1

### #11 — Vendings locales
**Respuesta:** Dump pendiente hasta tener tienda autotrade en OzRo.
**Fecha:** 2026-08-27
**Etapa:** M1

<!-- Formato para respuestas:
### #N — Título
**Respuesta:** ...
**Fecha:** YYYY-MM-DD
**Etapa:** M1
-->
