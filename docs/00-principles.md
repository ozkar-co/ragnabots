# Principios del proyecto

Reglas que guían cada decisión de diseño e implementación. Si algo contradice estos principios, hay que justificarlo explícitamente.

## KISS (Keep It Simple, Stupid)

- Un solo entorno virtual (`.venv`), un solo `requirements.txt`.
- Sin `pyproject.toml`, sin monorepo, sin frameworks de CLI hasta que hagan falta.
- Scripts planos y módulos pequeños cuando exista código.
- No añadir abstracciones "por si acaso".

## DRY (Don't Repeat Yourself)

- Los datos de rAthena se recolectan **una vez** y viven en `data/` (versionados en git).
- No copiar el repo completo de rAthena al proyecto; apuntar a la ruta del servidor.
- Si dos scripts hacen lo mismo, fusionar; no duplicar parsers ni queries.

## Single Responsibility

- Un archivo/script = una responsabilidad clara.
- Ejemplos futuros: un módulo parsea YAML, otro calcula drops, otro escribe a DB.
- Evitar "god scripts" que ingestan, simulan e inyectan en el mismo archivo.

## FailFast

- Validar inputs al inicio de cada script.
- Si falta un archivo, un campo obligatorio o el schema no cuadra: **abortar** con mensaje claro.
- No continuar con valores por defecto silenciosos que enmascaren errores.
- En operaciones de DB: transacciones atómicas; si algo falla, rollback completo.

## Data-first

> No escribir un parser hasta haber abierto el YAML real con tus propios ojos.

La secuencia obligatoria es:

1. Recolectar datos del servidor (archivos + dump DB).
2. Inspeccionar y documentar lo que realmente existe.
3. Diseñar estructura de `data/` y código sobre esos hallazgos.

No asumir campos, formatos ni tablas basándose en documentación genérica de rAthena.

## Convenciones del repo

| Aspecto | Convención |
|---------|------------|
| Entorno | `.venv` en la raíz del proyecto |
| Dependencias | `requirements.txt` (añadir según necesidad) |
| Datos | `data/` — commitear artefactos procesados, no dumps crudos grandes |
| DB local | `*.db` en `.gitignore` — clon SQLite no va a git |
| Secretos | `.env` en `.gitignore` — credenciales MySQL nunca en git |
| Docs | `docs/` — memoria persistente del proyecto, actualizar en cada etapa |
| Commits | Pequeños, un propósito por commit |

## Audiencia

Servidor privado familiar (hermano + primos). El sistema debe sentirse natural para jugadores reales, no como un exploit o spam de tiendas vacías.
