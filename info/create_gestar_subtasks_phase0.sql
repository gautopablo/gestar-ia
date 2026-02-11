/*
Fase 0 - Subtareas por Ticket
Script idempotente para Azure SQL Server.

Objetivo:
- Crear tabla gestar.Subtasks ligada a gestar.Tickets
- Mantener consistencia con catalogos actuales del esquema gestar
- No usar tablas del esquema dbo
*/

SET NOCOUNT ON;
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'gestar')
BEGIN
    THROW 50001, 'No existe el esquema gestar.', 1;
END
GO

IF OBJECT_ID('gestar.Tickets', 'U') IS NULL
BEGIN
    THROW 50002, 'No existe gestar.Tickets. No se puede crear gestar.Subtasks.', 1;
END
GO

IF OBJECT_ID('gestar.Users', 'U') IS NULL
BEGIN
    THROW 50003, 'No existe gestar.Users. No se puede crear gestar.Subtasks.', 1;
END
GO

IF OBJECT_ID('gestar.Estados', 'U') IS NULL
BEGIN
    THROW 50004, 'No existe gestar.Estados. No se puede crear gestar.Subtasks.', 1;
END
GO

IF OBJECT_ID('gestar.Subtasks', 'U') IS NULL
BEGIN
    CREATE TABLE gestar.Subtasks (
        SubtaskId INT IDENTITY(1,1) NOT NULL,
        TicketId INT NOT NULL,
        Title NVARCHAR(255) NOT NULL,
        Description NVARCHAR(MAX) NULL,
        AssigneeId INT NULL,
        EstadoId INT NULL,
        NeedByAt DATETIME2 NULL,
        CompletedAt DATETIME2 NULL,
        SortOrder INT NOT NULL CONSTRAINT DF_Subtasks_SortOrder DEFAULT (0),
        CreatedAt DATETIME2 NOT NULL CONSTRAINT DF_Subtasks_CreatedAt DEFAULT (SYSDATETIME()),
        CreatedBy INT NULL,
        UpdatedAt DATETIME2 NOT NULL CONSTRAINT DF_Subtasks_UpdatedAt DEFAULT (SYSDATETIME()),
        UpdatedBy INT NULL,

        CONSTRAINT PK_Subtasks PRIMARY KEY (SubtaskId),

        CONSTRAINT FK_Subtasks_Tickets
            FOREIGN KEY (TicketId) REFERENCES gestar.Tickets(TicketId),
        CONSTRAINT FK_Subtasks_Assignee
            FOREIGN KEY (AssigneeId) REFERENCES gestar.Users(UserId),
        CONSTRAINT FK_Subtasks_Estado
            FOREIGN KEY (EstadoId) REFERENCES gestar.Estados(EstadoId),
        CONSTRAINT FK_Subtasks_CreatedBy
            FOREIGN KEY (CreatedBy) REFERENCES gestar.Users(UserId),
        CONSTRAINT FK_Subtasks_UpdatedBy
            FOREIGN KEY (UpdatedBy) REFERENCES gestar.Users(UserId),

        CONSTRAINT CK_Subtasks_CompletedAfterNeedBy
            CHECK (
                CompletedAt IS NULL
                OR NeedByAt IS NULL
                OR CompletedAt >= NeedByAt
            )
    );
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_Subtasks_TicketId_SortOrder'
      AND object_id = OBJECT_ID('gestar.Subtasks')
)
BEGIN
    CREATE INDEX IX_Subtasks_TicketId_SortOrder
        ON gestar.Subtasks (TicketId, SortOrder, SubtaskId);
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_Subtasks_AssigneeId'
      AND object_id = OBJECT_ID('gestar.Subtasks')
)
BEGIN
    CREATE INDEX IX_Subtasks_AssigneeId
        ON gestar.Subtasks (AssigneeId);
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_Subtasks_EstadoId'
      AND object_id = OBJECT_ID('gestar.Subtasks')
)
BEGIN
    CREATE INDEX IX_Subtasks_EstadoId
        ON gestar.Subtasks (EstadoId);
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_Subtasks_NeedByAt'
      AND object_id = OBJECT_ID('gestar.Subtasks')
)
BEGIN
    CREATE INDEX IX_Subtasks_NeedByAt
        ON gestar.Subtasks (NeedByAt);
END
GO

-- Verificacion rapida
SELECT
    t.TABLE_SCHEMA,
    t.TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES t
WHERE t.TABLE_SCHEMA = 'gestar'
  AND t.TABLE_NAME = 'Subtasks';
GO

