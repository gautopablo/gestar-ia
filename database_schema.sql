/*
=============================================================================
SISTEMA DE GESTIÓN DE TICKETS ASISTIDO POR IA - ESQUEMA PROFESIONAL
=============================================================================
Descripción: Script de creación de base de datos optimizado para SQL Server/Azure SQL.
Características: Normalización 3NF, Auditoría, Jerarquía de Divisiones/Áreas y Soporte para IA.
*/

-- 1. Tablas Maestras (Lookups)
-- --------------------------------------------------------------------------

CREATE TABLE Plantas (
    PlantaId INT IDENTITY(1,1) PRIMARY KEY,
    Nombre NVARCHAR(100) NOT NULL UNIQUE,
    Activo BIT DEFAULT 1
);

CREATE TABLE Divisiones (
    DivisionId INT IDENTITY(1,1) PRIMARY KEY,
    Nombre NVARCHAR(100) NOT NULL UNIQUE,
    Activo BIT DEFAULT 1
);

CREATE TABLE Areas (
    AreaId INT IDENTITY(1,1) PRIMARY KEY,
    Nombre NVARCHAR(100) NOT NULL,
    DivisionId INT NOT NULL,
    Activo BIT DEFAULT 1,
    CONSTRAINT FK_Areas_Divisiones FOREIGN KEY (DivisionId) REFERENCES Divisiones(DivisionId)
);

CREATE TABLE Categorias (
    CategoriaId INT IDENTITY(1,1) PRIMARY KEY,
    Nombre NVARCHAR(100) NOT NULL UNIQUE,
    Activo BIT DEFAULT 1
);

CREATE TABLE Subcategorias (
    SubcategoriaId INT IDENTITY(1,1) PRIMARY KEY,
    Nombre NVARCHAR(100) NOT NULL,
    CategoriaId INT NOT NULL,
    Activo BIT DEFAULT 1,
    CONSTRAINT FK_Subcategorias_Categorias FOREIGN KEY (CategoriaId) REFERENCES Categorias(CategoriaId)
);

CREATE TABLE Prioridades (
    PrioridadId INT IDENTITY(1,1) PRIMARY KEY,
    Nombre NVARCHAR(50) NOT NULL UNIQUE,
    Nivel INT NOT NULL -- 1: Alta, 2: Media, 3: Baja
);

CREATE TABLE Estados (
    EstadoId INT IDENTITY(1,1) PRIMARY KEY,
    Nombre NVARCHAR(50) NOT NULL UNIQUE
);

-- 2. Entidades Principales
-- --------------------------------------------------------------------------

CREATE TABLE Users (
    UserId INT IDENTITY(1,1) PRIMARY KEY,
    Username NVARCHAR(100) NOT NULL UNIQUE,
    Email NVARCHAR(255) NOT NULL UNIQUE,
    Role NVARCHAR(50) NOT NULL, -- Admin, Tecnico, Solicitante
    Active BIT DEFAULT 1,
    CreatedAt DATETIME2 DEFAULT GETDATE()
);

CREATE TABLE Tickets (
    TicketId INT IDENTITY(1,1) PRIMARY KEY,
    Title NVARCHAR(200) NOT NULL,
    Description NVARCHAR(MAX) NOT NULL,
    RequesterId INT NOT NULL,
    AssigneeId INT NULL,
    
    -- Localización y Categoría
    PlantaId INT NOT NULL,
    AreaId INT NOT NULL,
    CategoriaId INT NOT NULL,
    SubcategoriaId INT NOT NULL,
    
    -- Clasificación
    PrioridadId INT NOT NULL,
    EstadoId INT NOT NULL,
    
    -- Metadatos de IA
    ConfidenceScore DECIMAL(5,2) NULL,
    OriginalPrompt NVARCHAR(MAX) NULL,
    AiProcessingTime INT NULL, -- en ms
    ConversationId NVARCHAR(100) NULL,
    
    -- Fechas
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    UpdatedAt DATETIME2 DEFAULT GETDATE(),
    ClosedAt DATETIME2 NULL,
    
    CONSTRAINT FK_Tickets_Requester FOREIGN KEY (RequesterId) REFERENCES Users(UserId),
    CONSTRAINT FK_Tickets_Assignee FOREIGN KEY (AssigneeId) REFERENCES Users(UserId),
    CONSTRAINT FK_Tickets_Plantas FOREIGN KEY (PlantaId) REFERENCES Plantas(PlantaId),
    CONSTRAINT FK_Tickets_Areas FOREIGN KEY (AreaId) REFERENCES Areas(AreaId),
    CONSTRAINT FK_Tickets_Categorias FOREIGN KEY (CategoriaId) REFERENCES Categorias(CategoriaId),
    CONSTRAINT FK_Tickets_Subcategorias FOREIGN KEY (SubcategoriaId) REFERENCES Subcategorias(SubcategoriaId),
    CONSTRAINT FK_Tickets_Prioridades FOREIGN KEY (PrioridadId) REFERENCES Prioridades(PrioridadId),
    CONSTRAINT FK_Tickets_Estados FOREIGN KEY (EstadoId) REFERENCES Estados(EstadoId)
);

CREATE TABLE Tasks (
    TaskId INT IDENTITY(1,1) PRIMARY KEY,
    TicketId INT NOT NULL,
    Description NVARCHAR(MAX) NOT NULL,
    IsDone BIT DEFAULT 0,
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    CONSTRAINT FK_Tasks_Tickets FOREIGN KEY (TicketId) REFERENCES Tickets(TicketId)
);

-- 3. Auditoría y Trazabilidad
-- --------------------------------------------------------------------------

CREATE TABLE TicketLogs (
    LogId INT IDENTITY(1,1) PRIMARY KEY,
    TicketId INT NOT NULL,
    UserId INT NULL, -- Quien hizo el cambio (NULL si fue la IA)
    IsAi BIT DEFAULT 0,
    FieldName NVARCHAR(100) NOT NULL,
    OldValue NVARCHAR(MAX) NULL,
    NewValue NVARCHAR(MAX) NULL,
    ChangedAt DATETIME2 DEFAULT GETDATE(),
    CONSTRAINT FK_TicketLogs_Tickets FOREIGN KEY (TicketId) REFERENCES Tickets(TicketId),
    CONSTRAINT FK_TicketLogs_Users FOREIGN KEY (UserId) REFERENCES Users(UserId)
);

-- 4. Datos Semilla (Lookups iniciales)
-- --------------------------------------------------------------------------

INSERT INTO Estados (Nombre) VALUES ('Abierto'), ('En Progreso'), ('En Pausa'), ('Resuelto'), ('Cerrado');

INSERT INTO Prioridades (Nombre, Nivel) VALUES ('Baja', 3), ('Media', 2), ('Alta', 1), ('Crítica', 0);

INSERT INTO Divisiones (Nombre) VALUES ('Sellado'), ('Forja'), ('Distribución');

INSERT INTO Categorias (Nombre) VALUES ('Mantenimiento Predictivo'), ('Soporte Técnico IT'), ('Producción');

-- Ejemplo de subcategorías y áreas
INSERT INTO Subcategorias (Nombre, CategoriaId) 
SELECT 'Falla Eléctrica', CategoriaId FROM Categorias WHERE Nombre = 'Mantenimiento Predictivo';

INSERT INTO Areas (Nombre, DivisionId)
SELECT 'Línea de Prensa 1', DivisionId FROM Divisiones WHERE Nombre = 'Forja';

-- 5. Índices Sugeridos
-- --------------------------------------------------------------------------
CREATE INDEX IX_Tickets_Estado ON Tickets(EstadoId);
CREATE INDEX IX_Tickets_Requester ON Tickets(RequesterId);
CREATE INDEX IX_Tickets_Conversation ON Tickets(ConversationId);
GO
