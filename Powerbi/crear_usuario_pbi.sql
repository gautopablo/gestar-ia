-- 1) Crear usuario contenido (Azure SQL Database)
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'pbi_gestar_reader')
BEGIN
    CREATE USER [pbi_gestar_reader] WITH PASSWORD = 'Taranto_P8I_2026!';
END
GO

-- 2) Permiso mínimo de conexión
GRANT CONNECT TO [pbi_gestar_reader];
GO

-- 3) Solo lectura del esquema gestar
GRANT SELECT ON SCHEMA::gestar TO [pbi_gestar_reader];
GO

-- 4) (Opcional, más estricto) negar escritura explícitamente
DENY INSERT, UPDATE, DELETE, ALTER ON SCHEMA::gestar TO [pbi_gestar_reader];
GO
