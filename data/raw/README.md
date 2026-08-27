# Datos crudos recolectados del servidor

Copiados desde `kansas` (172.26.0.1) el 2026-08-27.

## Estructura

```
raw/
├── rathena/          # YAML + conf + schema SQL del servidor
│   ├── db/           # item/mob DB con cadena import: pre-re → re → import
│   ├── conf/         # drops.conf, exp.conf, battle_conf.txt (rates custom)
│   └── sql-files/    # main.sql (schema completo rAthena)
├── db_snapshot/
│   └── 20260827_030000/
│       ├── sql/      # INSERTs por tabla (sin login)
│       └── json/     # mismo subset en JSON
└── server_rates.json # rates extraídos de battle_conf.txt
```

## Refrescar desde el servidor

```bash
# YAML/conf (ajustar fecha de backup)
scp oz@172.26.0.1:/home/oz/rathena/db/import/item_db.yml data/raw/rathena/db/import/
scp oz@172.26.0.1:/home/oz/ozro-backup/backups/YYYYMMDD_HHMMSS/sql/char.sql data/raw/db_snapshot/YYYYMMDD_HHMMSS/sql/
```

Ver `data/manifest.json` para inventario completo.

## Seguridad

- **No** copiar `login.sql` ni `full_backup.sql` al repo (contraseñas).
- El clon SQLite local (`*.db`) va en `.gitignore`.
