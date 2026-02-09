BEGIN TRANSACTION;

-- ============================================================================
-- Seeds de ejemplo basados en `info/maestros gestar.xlsx`
-- Compatibles con esquema SQLite actual (`app.py` / `database_schema.sql`)
-- Carga idempotente con INSERT OR IGNORE.
-- ============================================================================

-- 1) Divisiones
INSERT OR IGNORE INTO Divisiones (Nombre, Activo) VALUES ('Division Sellado', 1);
INSERT OR IGNORE INTO Divisiones (Nombre, Activo) VALUES ('División Dirección, Suspensión y Fricción', 1);

-- 2) Plantas
INSERT OR IGNORE INTO Plantas (Nombre, Activo) VALUES ('UT1', 1);
INSERT OR IGNORE INTO Plantas (Nombre, Activo) VALUES ('UT2', 1);
INSERT OR IGNORE INTO Plantas (Nombre, Activo) VALUES ('UT3', 1);
INSERT OR IGNORE INTO Plantas (Nombre, Activo) VALUES ('UT4', 1);
INSERT OR IGNORE INTO Plantas (Nombre, Activo) VALUES ('UT5', 1);

-- 3) Prioridades (normalizadas a niveles actuales)
INSERT OR IGNORE INTO Prioridades (Nombre, Nivel) VALUES ('Crítica', 0);
INSERT OR IGNORE INTO Prioridades (Nombre, Nivel) VALUES ('Alta', 1);
INSERT OR IGNORE INTO Prioridades (Nombre, Nivel) VALUES ('Media', 2);
INSERT OR IGNORE INTO Prioridades (Nombre, Nivel) VALUES ('Baja', 3);

-- 4) Categorías
INSERT OR IGNORE INTO Categorias (Nombre, Activo) VALUES ('Mantenimiento Industrial', 1);
INSERT OR IGNORE INTO Categorias (Nombre, Activo) VALUES ('Sistemas e IT', 1);
INSERT OR IGNORE INTO Categorias (Nombre, Activo) VALUES ('Matricería y Herramental', 1);
INSERT OR IGNORE INTO Categorias (Nombre, Activo) VALUES ('Calidad', 1);
INSERT OR IGNORE INTO Categorias (Nombre, Activo) VALUES ('Producción y Logística', 1);
INSERT OR IGNORE INTO Categorias (Nombre, Activo) VALUES ('Ingeniería de Procesos', 1);
INSERT OR IGNORE INTO Categorias (Nombre, Activo) VALUES ('Calidad y Procesos', 1);

-- 5) Áreas (mapeo de ejemplo por nombre para satisfacer FK DivisionId)
INSERT OR IGNORE INTO Areas (Nombre, DivisionId, Activo)
SELECT 'Dirección División', d.DivisionId, 1 FROM Divisiones d WHERE d.Nombre = 'División Dirección, Suspensión y Fricción';
INSERT OR IGNORE INTO Areas (Nombre, DivisionId, Activo)
SELECT 'Administración', d.DivisionId, 1 FROM Divisiones d WHERE d.Nombre = 'División Dirección, Suspensión y Fricción';
INSERT OR IGNORE INTO Areas (Nombre, DivisionId, Activo)
SELECT 'Capital Humano', d.DivisionId, 1 FROM Divisiones d WHERE d.Nombre = 'División Dirección, Suspensión y Fricción';
INSERT OR IGNORE INTO Areas (Nombre, DivisionId, Activo)
SELECT 'GICASH', d.DivisionId, 1 FROM Divisiones d WHERE d.Nombre = 'División Dirección, Suspensión y Fricción';
INSERT OR IGNORE INTO Areas (Nombre, DivisionId, Activo)
SELECT 'Ing. Desarrollo', d.DivisionId, 1 FROM Divisiones d WHERE d.Nombre = 'División Dirección, Suspensión y Fricción';
INSERT OR IGNORE INTO Areas (Nombre, DivisionId, Activo)
SELECT 'Ing. Procesos', d.DivisionId, 1 FROM Divisiones d WHERE d.Nombre = 'División Dirección, Suspensión y Fricción';
INSERT OR IGNORE INTO Areas (Nombre, DivisionId, Activo)
SELECT 'Sistemas', d.DivisionId, 1 FROM Divisiones d WHERE d.Nombre = 'División Dirección, Suspensión y Fricción';
INSERT OR IGNORE INTO Areas (Nombre, DivisionId, Activo)
SELECT 'Sin Definir', d.DivisionId, 1 FROM Divisiones d WHERE d.Nombre = 'División Dirección, Suspensión y Fricción';

INSERT OR IGNORE INTO Areas (Nombre, DivisionId, Activo)
SELECT 'Mantenimiento', d.DivisionId, 1 FROM Divisiones d WHERE d.Nombre = 'Division Sellado';
INSERT OR IGNORE INTO Areas (Nombre, DivisionId, Activo)
SELECT 'Abastecimiento y PCP', d.DivisionId, 1 FROM Divisiones d WHERE d.Nombre = 'Division Sellado';
INSERT OR IGNORE INTO Areas (Nombre, DivisionId, Activo)
SELECT 'Matricería', d.DivisionId, 1 FROM Divisiones d WHERE d.Nombre = 'Division Sellado';
INSERT OR IGNORE INTO Areas (Nombre, DivisionId, Activo)
SELECT 'Mecatrónica', d.DivisionId, 1 FROM Divisiones d WHERE d.Nombre = 'Division Sellado';
INSERT OR IGNORE INTO Areas (Nombre, DivisionId, Activo)
SELECT 'Producción UT1-2', d.DivisionId, 1 FROM Divisiones d WHERE d.Nombre = 'Division Sellado';
INSERT OR IGNORE INTO Areas (Nombre, DivisionId, Activo)
SELECT 'Producción UT3', d.DivisionId, 1 FROM Divisiones d WHERE d.Nombre = 'Division Sellado';
INSERT OR IGNORE INTO Areas (Nombre, DivisionId, Activo)
SELECT 'Producción UT4', d.DivisionId, 1 FROM Divisiones d WHERE d.Nombre = 'Division Sellado';
INSERT OR IGNORE INTO Areas (Nombre, DivisionId, Activo)
SELECT 'Producción UT5', d.DivisionId, 1 FROM Divisiones d WHERE d.Nombre = 'Division Sellado';

-- 6) Subcategorías (permitiendo mismo nombre en categorías distintas)
INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'Maquinaria (Prensas/Inyectoras)', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Mantenimiento Industrial';
INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'Servicios Generales (Luz/Agua/Gas)', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Mantenimiento Industrial';
INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'Neumática e Hidráulica', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Mantenimiento Industrial';
INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'PLC y Automatización', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Mantenimiento Industrial';
INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'Edificio / Infraestructura', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Mantenimiento Industrial';

INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'Software de Gestión (ERP)', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Sistemas e IT';
INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'Hardware (PCs/Impresoras)', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Sistemas e IT';
INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'Redes y Conectividad', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Sistemas e IT';
INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'Telefonía / Comunicaciones', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Sistemas e IT';
INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'Cuentas de Usuario y Accesos', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Sistemas e IT';

INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'Reparación de Matriz', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Matricería y Herramental';
INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'Construcción de Insertos', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Matricería y Herramental';
INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'Pulido y Ajuste', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Matricería y Herramental';
INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'Cambio de Modelo (Set-up)', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Matricería y Herramental';
INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'Afilado de Herramientas', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Matricería y Herramental';

INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'No Conformidad de Producto', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Calidad';
INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'Calibración de Instrumentos', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Calidad';
INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'Auditoría de Proceso', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Calidad';
INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'Mejora Continua (KAIZEN)', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Calidad';
INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'Documentación Técnica', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Calidad';

INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'Abastecimiento de Materia Prima', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Producción y Logística';
INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'Movimiento de Materiales (Autoelevadores)', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Producción y Logística';
INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'Embalaje y Packaging', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Producción y Logística';
INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'Planificación y PCP', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Producción y Logística';
INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'Scrap / Retrabajo', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Producción y Logística';

INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'No Conformidad de Producto', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Calidad y Procesos';
INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'Calibración de Instrumentos', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Calidad y Procesos';
INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'Auditoría de Proceso', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Calidad y Procesos';
INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'Mejora Continua (KAIZEN)', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Calidad y Procesos';
INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId, Activo)
SELECT 'Documentación Técnica', c.CategoriaId, 1 FROM Categorias c WHERE c.Nombre = 'Calidad y Procesos';

-- 7) Usuarios (ejemplo)
INSERT OR IGNORE INTO Users (Username, Email, Role, Active) VALUES ('gauto_pablo', 'gautop@taranto.com.ar', 'Administrador', 1);
INSERT OR IGNORE INTO Users (Username, Email, Role, Active) VALUES ('ranea_mauricio', 'ranea@taranto.com.ar', 'Administrador', 1);
INSERT OR IGNORE INTO Users (Username, Email, Role, Active) VALUES ('firmapaz_alfredo', 'firmapaz@taranto.com.ar', 'Analista', 1);
INSERT OR IGNORE INTO Users (Username, Email, Role, Active) VALUES ('leiva_mauricio', 'leivam@taranto.com.ar', 'Analista', 1);
INSERT OR IGNORE INTO Users (Username, Email, Role, Active) VALUES ('riveros_emilio', 'riveros@taranto.com.ar', 'Analista', 1);
INSERT OR IGNORE INTO Users (Username, Email, Role, Active) VALUES ('parra_francisco', 'parraf@taranto.com.ar', 'Analista', 1);
INSERT OR IGNORE INTO Users (Username, Email, Role, Active) VALUES ('vazquez_pilar', 'vazquezp@taranto.com.ar', 'Analista', 1);
INSERT OR IGNORE INTO Users (Username, Email, Role, Active) VALUES ('guillen_lucas', 'guillen@taranto.com.ar', 'Analista', 1);
INSERT OR IGNORE INTO Users (Username, Email, Role, Active) VALUES ('vera_juan', 'veraj@taranto.com.ar', 'Analista', 1);
INSERT OR IGNORE INTO Users (Username, Email, Role, Active) VALUES ('brochero_javier', 'brochero@taranto.com.ar', 'Analista', 1);
INSERT OR IGNORE INTO Users (Username, Email, Role, Active) VALUES ('alejandro_cane', 'cane@tartanto.com.ar', 'Director', 1);

COMMIT;
