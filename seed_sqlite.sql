INSERT OR IGNORE INTO Estados (Nombre) VALUES
    ('Abierto'),
    ('En Progreso'),
    ('En Pausa'),
    ('Resuelto'),
    ('Cerrado'),
    ('Archivado');

INSERT OR IGNORE INTO Prioridades (Nombre, Nivel) VALUES
    ('Crítica', 0),
    ('Alta', 1),
    ('Media', 2),
    ('Baja', 3);

INSERT OR IGNORE INTO Divisiones (Nombre, Activo) VALUES
    ('Sellado', 1),
    ('Forja', 1),
    ('Distribución', 1);

INSERT OR IGNORE INTO Plantas (Nombre, Activo) VALUES
    ('UT1', 1),
    ('UT3', 1);

INSERT OR IGNORE INTO Categorias (Nombre, Activo) VALUES
    ('Mantenimiento', 1),
    ('IT', 1),
    ('Producción', 1);

INSERT OR IGNORE INTO Users (Username, Email, Role, Active) VALUES
    ('gauto_pablo', 'gautop@taranto.com.ar', 'Administrador', 1);
