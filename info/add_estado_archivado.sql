-- Alta idempotente del estado "Archivado"
IF NOT EXISTS (
    SELECT 1
    FROM gestar.Estados
    WHERE LOWER(LTRIM(RTRIM(Nombre))) = 'archivado'
)
BEGIN
    INSERT INTO gestar.Estados (Nombre) VALUES (N'Archivado');
END
