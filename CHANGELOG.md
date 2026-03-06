# Changelog

Todos los cambios relevantes de este proyecto se documentan en este archivo.

## [0.8.0] - 2026-03-06
### Added
- Soporte dual de base de datos mediante `DB_MODE` (`azure` o `sqlite`) y `SQLITE_PATH`.
- Nuevo adaptador de base en `db_adapter.py` para unificar conexion y diferencias de dialecto.
- Esquema y seed para SQLite (`schema_sqlite.sql`, `seed_sqlite.sql`).
- Script de bootstrap SQLite (`scripts/bootstrap_sqlite.py`).
- Script de migracion Azure SQL -> SQLite con verificacion de conteos (`scripts/migrate_azure_to_sqlite.py`).
- Checklist de pruebas para modo SQLite en `info/TEST_CHECKLIST_SQLITE.md`.

### Changed
- `app.py` actualizado para ejecutar en Azure SQL o SQLite segun configuracion.
- `master_data_admin.py` adaptado para backend dual.
- `notification_assignment.py` adaptado para compatibilidad de worker en SQLite.
- Mensajes de estado en UI ajustados para mostrar backend activo.
- Header global de Streamlit visible para facilitar trabajo con panel lateral.

### Fixed
- Lectura de configuracion corregida para priorizar `st.secrets` solo si la clave existe y luego fallback a `.env`.
- Bootstrap SQLite robustecido para migrar bases legacy (columnas faltantes en `Users`).

## [0.7.0] - 2026-02-23
### Added
- Versionado formal inicial del proyecto con archivo `VERSION`.
- Registro de cambios inicial en `CHANGELOG.md`.
- Visualizacion de version de la app en el encabezado principal.
