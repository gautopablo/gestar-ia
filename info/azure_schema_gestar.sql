/*
Azure SQL bootstrap script for GESTAR
- Creates isolated schema: gestar
- Creates core tables used by the app
- Inserts seed/master data safely (idempotent)
*/

SET NOCOUNT ON;
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'gestar')
    EXEC('CREATE SCHEMA gestar');
GO

IF OBJECT_ID('gestar.Plantas', 'U') IS NULL
BEGIN
    CREATE TABLE gestar.Plantas (
        PlantaId INT IDENTITY(1,1) PRIMARY KEY,
        Nombre NVARCHAR(150) NOT NULL UNIQUE,
        Activo BIT NOT NULL CONSTRAINT DF_Plantas_Activo DEFAULT (1)
    );
END
GO

IF OBJECT_ID('gestar.Divisiones', 'U') IS NULL
BEGIN
    CREATE TABLE gestar.Divisiones (
        DivisionId INT IDENTITY(1,1) PRIMARY KEY,
        Nombre NVARCHAR(150) NOT NULL UNIQUE,
        Activo BIT NOT NULL CONSTRAINT DF_Divisiones_Activo DEFAULT (1)
    );
END
GO

IF OBJECT_ID('gestar.Areas', 'U') IS NULL
BEGIN
    CREATE TABLE gestar.Areas (
        AreaId INT IDENTITY(1,1) PRIMARY KEY,
        Nombre NVARCHAR(150) NOT NULL,
        DivisionId INT NULL,
        Activo BIT NOT NULL CONSTRAINT DF_Areas_Activo DEFAULT (1),
        CONSTRAINT FK_Areas_Divisiones FOREIGN KEY (DivisionId) REFERENCES gestar.Divisiones(DivisionId),
        CONSTRAINT UQ_Areas_Nombre_Division UNIQUE (Nombre, DivisionId)
    );
END
GO

IF OBJECT_ID('gestar.Categorias', 'U') IS NULL
BEGIN
    CREATE TABLE gestar.Categorias (
        CategoriaId INT IDENTITY(1,1) PRIMARY KEY,
        Nombre NVARCHAR(150) NOT NULL UNIQUE,
        Activo BIT NOT NULL CONSTRAINT DF_Categorias_Activo DEFAULT (1)
    );
END
GO

IF OBJECT_ID('gestar.Subcategorias', 'U') IS NULL
BEGIN
    CREATE TABLE gestar.Subcategorias (
        SubcategoriaId INT IDENTITY(1,1) PRIMARY KEY,
        Nombre NVARCHAR(200) NOT NULL,
        CategoriaId INT NOT NULL,
        Activo BIT NOT NULL CONSTRAINT DF_Subcategorias_Activo DEFAULT (1),
        CONSTRAINT FK_Subcategorias_Categorias FOREIGN KEY (CategoriaId) REFERENCES gestar.Categorias(CategoriaId),
        CONSTRAINT UQ_Subcategorias_Nombre_Categoria UNIQUE (Nombre, CategoriaId)
    );
END
GO

IF OBJECT_ID('gestar.Prioridades', 'U') IS NULL
BEGIN
    CREATE TABLE gestar.Prioridades (
        PrioridadId INT IDENTITY(1,1) PRIMARY KEY,
        Nombre NVARCHAR(50) NOT NULL UNIQUE,
        Nivel INT NOT NULL
    );
END
GO

IF OBJECT_ID('gestar.Estados', 'U') IS NULL
BEGIN
    CREATE TABLE gestar.Estados (
        EstadoId INT IDENTITY(1,1) PRIMARY KEY,
        Nombre NVARCHAR(50) NOT NULL UNIQUE
    );
END
GO

IF OBJECT_ID('gestar.Users', 'U') IS NULL
BEGIN
    CREATE TABLE gestar.Users (
        UserId INT IDENTITY(1,1) PRIMARY KEY,
        Username NVARCHAR(150) NOT NULL UNIQUE,
        Email NVARCHAR(255) NULL UNIQUE,
        Role NVARCHAR(80) NULL,
        Active BIT NOT NULL CONSTRAINT DF_Users_Active DEFAULT (1),
        CreatedAt DATETIME2 NOT NULL CONSTRAINT DF_Users_CreatedAt DEFAULT (SYSDATETIME())
    );
END
GO

IF OBJECT_ID('gestar.Tickets', 'U') IS NULL
BEGIN
    CREATE TABLE gestar.Tickets (
        TicketId INT IDENTITY(1,1) PRIMARY KEY,
        Title NVARCHAR(255) NULL,
        Description NVARCHAR(MAX) NULL,
        RequesterId INT NULL,
        SuggestedAssigneeId INT NULL,
        AssigneeId INT NULL,
        PlantaId INT NULL,
        AreaId INT NULL,
        CategoriaId INT NULL,
        SubcategoriaId INT NULL,
        PrioridadId INT NULL,
        EstadoId INT NULL,
        ConfidenceScore FLOAT NULL,
        OriginalPrompt NVARCHAR(MAX) NULL,
        AiProcessingTime INT NULL,
        ConversationId NVARCHAR(120) NULL,
        NeedByAt DATETIME2 NULL,
        CreatedAt DATETIME2 NOT NULL CONSTRAINT DF_Tickets_CreatedAt DEFAULT (SYSDATETIME()),
        UpdatedAt DATETIME2 NOT NULL CONSTRAINT DF_Tickets_UpdatedAt DEFAULT (SYSDATETIME()),
        CONSTRAINT FK_Tickets_Requester FOREIGN KEY (RequesterId) REFERENCES gestar.Users(UserId),
        CONSTRAINT FK_Tickets_SuggestedAssignee FOREIGN KEY (SuggestedAssigneeId) REFERENCES gestar.Users(UserId),
        CONSTRAINT FK_Tickets_Assignee FOREIGN KEY (AssigneeId) REFERENCES gestar.Users(UserId),
        CONSTRAINT FK_Tickets_Planta FOREIGN KEY (PlantaId) REFERENCES gestar.Plantas(PlantaId),
        CONSTRAINT FK_Tickets_Area FOREIGN KEY (AreaId) REFERENCES gestar.Areas(AreaId),
        CONSTRAINT FK_Tickets_Categoria FOREIGN KEY (CategoriaId) REFERENCES gestar.Categorias(CategoriaId),
        CONSTRAINT FK_Tickets_Subcategoria FOREIGN KEY (SubcategoriaId) REFERENCES gestar.Subcategorias(SubcategoriaId),
        CONSTRAINT FK_Tickets_Prioridad FOREIGN KEY (PrioridadId) REFERENCES gestar.Prioridades(PrioridadId),
        CONSTRAINT FK_Tickets_Estado FOREIGN KEY (EstadoId) REFERENCES gestar.Estados(EstadoId)
    );
END
GO

/* Seed data */
IF NOT EXISTS (SELECT 1 FROM gestar.Estados WHERE Nombre = N'Abierto') INSERT INTO gestar.Estados (Nombre) VALUES (N'Abierto');
IF NOT EXISTS (SELECT 1 FROM gestar.Estados WHERE Nombre = N'En Progreso') INSERT INTO gestar.Estados (Nombre) VALUES (N'En Progreso');
IF NOT EXISTS (SELECT 1 FROM gestar.Estados WHERE Nombre = N'Cerrado') INSERT INTO gestar.Estados (Nombre) VALUES (N'Cerrado');

IF NOT EXISTS (SELECT 1 FROM gestar.Prioridades WHERE Nombre = N'Baja') INSERT INTO gestar.Prioridades (Nombre, Nivel) VALUES (N'Baja', 3);
IF NOT EXISTS (SELECT 1 FROM gestar.Prioridades WHERE Nombre = N'Media') INSERT INTO gestar.Prioridades (Nombre, Nivel) VALUES (N'Media', 2);
IF NOT EXISTS (SELECT 1 FROM gestar.Prioridades WHERE Nombre = N'Alta') INSERT INTO gestar.Prioridades (Nombre, Nivel) VALUES (N'Alta', 1);
IF NOT EXISTS (SELECT 1 FROM gestar.Prioridades WHERE Nombre = N'Crítica') INSERT INTO gestar.Prioridades (Nombre, Nivel) VALUES (N'Crítica', 0);

IF NOT EXISTS (SELECT 1 FROM gestar.Divisiones WHERE Nombre = N'Sellado') INSERT INTO gestar.Divisiones (Nombre) VALUES (N'Sellado');
IF NOT EXISTS (SELECT 1 FROM gestar.Divisiones WHERE Nombre = N'Forja') INSERT INTO gestar.Divisiones (Nombre) VALUES (N'Forja');
IF NOT EXISTS (SELECT 1 FROM gestar.Divisiones WHERE Nombre = N'Distribución') INSERT INTO gestar.Divisiones (Nombre) VALUES (N'Distribución');

IF NOT EXISTS (SELECT 1 FROM gestar.Plantas WHERE Nombre = N'UT3') INSERT INTO gestar.Plantas (Nombre) VALUES (N'UT3');
IF NOT EXISTS (SELECT 1 FROM gestar.Plantas WHERE Nombre = N'UT1') INSERT INTO gestar.Plantas (Nombre) VALUES (N'UT1');

IF NOT EXISTS (SELECT 1 FROM gestar.Categorias WHERE Nombre = N'Mantenimiento') INSERT INTO gestar.Categorias (Nombre) VALUES (N'Mantenimiento');
IF NOT EXISTS (SELECT 1 FROM gestar.Categorias WHERE Nombre = N'IT') INSERT INTO gestar.Categorias (Nombre) VALUES (N'IT');
IF NOT EXISTS (SELECT 1 FROM gestar.Categorias WHERE Nombre = N'Producción') INSERT INTO gestar.Categorias (Nombre) VALUES (N'Producción');
IF NOT EXISTS (SELECT 1 FROM gestar.Categorias WHERE Nombre = N'Mantenimiento Industrial') INSERT INTO gestar.Categorias (Nombre) VALUES (N'Mantenimiento Industrial');
IF NOT EXISTS (SELECT 1 FROM gestar.Categorias WHERE Nombre = N'Sistemas e IT') INSERT INTO gestar.Categorias (Nombre) VALUES (N'Sistemas e IT');
IF NOT EXISTS (SELECT 1 FROM gestar.Categorias WHERE Nombre = N'Matricería y Herramental') INSERT INTO gestar.Categorias (Nombre) VALUES (N'Matricería y Herramental');
IF NOT EXISTS (SELECT 1 FROM gestar.Categorias WHERE Nombre = N'Calidad') INSERT INTO gestar.Categorias (Nombre) VALUES (N'Calidad');
IF NOT EXISTS (SELECT 1 FROM gestar.Categorias WHERE Nombre = N'Producción y Logística') INSERT INTO gestar.Categorias (Nombre) VALUES (N'Producción y Logística');
IF NOT EXISTS (SELECT 1 FROM gestar.Categorias WHERE Nombre = N'Ingeniería de Procesos') INSERT INTO gestar.Categorias (Nombre) VALUES (N'Ingeniería de Procesos');
IF NOT EXISTS (SELECT 1 FROM gestar.Categorias WHERE Nombre = N'Calidad y Procesos') INSERT INTO gestar.Categorias (Nombre) VALUES (N'Calidad y Procesos');

IF NOT EXISTS (SELECT 1 FROM gestar.Users WHERE Username = N'gauto_pablo') INSERT INTO gestar.Users (Username, Email, Role) VALUES (N'gauto_pablo', N'gautop@taranto.com.ar', N'Administracion');
IF NOT EXISTS (SELECT 1 FROM gestar.Users WHERE Username = N'ranea_mauricio') INSERT INTO gestar.Users (Username, Email, Role) VALUES (N'ranea_mauricio', N'ranea@taranto.com.ar', N'Administracion');
IF NOT EXISTS (SELECT 1 FROM gestar.Users WHERE Username = N'firmapaz_alfredo') INSERT INTO gestar.Users (Username, Email, Role) VALUES (N'firmapaz_alfredo', N'firmapaz@taranto.com.ar', N'Analista');
IF NOT EXISTS (SELECT 1 FROM gestar.Users WHERE Username = N'leiva_mauricio') INSERT INTO gestar.Users (Username, Email, Role) VALUES (N'leiva_mauricio', N'leivam@taranto.com.ar', N'Analista');
IF NOT EXISTS (SELECT 1 FROM gestar.Users WHERE Username = N'riveros_emanuel') INSERT INTO gestar.Users (Username, Email, Role) VALUES (N'riveros_emanuel', N'riveroe@taranto.com.ar', N'Analista');
IF NOT EXISTS (SELECT 1 FROM gestar.Users WHERE Username = N'parra_francisco') INSERT INTO gestar.Users (Username, Email, Role) VALUES (N'parra_francisco', N'parraf@taranto.com.ar', N'Analista');
IF NOT EXISTS (SELECT 1 FROM gestar.Users WHERE Username = N'vazquez_pilar') INSERT INTO gestar.Users (Username, Email, Role) VALUES (N'vazquez_pilar', N'vazquezp@taranto.com.ar', N'Analista');
IF NOT EXISTS (SELECT 1 FROM gestar.Users WHERE Username = N'guillen_lucas') INSERT INTO gestar.Users (Username, Email, Role) VALUES (N'guillen_lucas', N'guillen@taranto.com.ar', N'Analista');
IF NOT EXISTS (SELECT 1 FROM gestar.Users WHERE Username = N'vera_juan') INSERT INTO gestar.Users (Username, Email, Role) VALUES (N'vera_juan', N'veraj@taranto.com.ar', N'Analista');
IF NOT EXISTS (SELECT 1 FROM gestar.Users WHERE Username = N'brochero_joaquin') INSERT INTO gestar.Users (Username, Email, Role) VALUES (N'brochero_joaquin', N'brocheroo@taranto.com.ar', N'Analista');
IF NOT EXISTS (SELECT 1 FROM gestar.Users WHERE Username = N'cane_alejandro') INSERT INTO gestar.Users (Username, Email, Role) VALUES (N'cane_alejandro', N'cane@taranto.com.ar', N'Director');
GO

