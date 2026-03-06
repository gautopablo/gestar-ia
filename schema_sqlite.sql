PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Plantas (
    PlantaId INTEGER PRIMARY KEY AUTOINCREMENT,
    Nombre TEXT NOT NULL UNIQUE,
    Activo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Divisiones (
    DivisionId INTEGER PRIMARY KEY AUTOINCREMENT,
    Nombre TEXT NOT NULL UNIQUE,
    Activo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Areas (
    AreaId INTEGER PRIMARY KEY AUTOINCREMENT,
    Nombre TEXT NOT NULL,
    DivisionId INTEGER,
    Activo INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (DivisionId) REFERENCES Divisiones (DivisionId)
);

CREATE TABLE IF NOT EXISTS Categorias (
    CategoriaId INTEGER PRIMARY KEY AUTOINCREMENT,
    Nombre TEXT NOT NULL UNIQUE,
    Activo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Subcategorias (
    SubcategoriaId INTEGER PRIMARY KEY AUTOINCREMENT,
    Nombre TEXT NOT NULL,
    CategoriaId INTEGER,
    Activo INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (CategoriaId) REFERENCES Categorias (CategoriaId)
);

CREATE TABLE IF NOT EXISTS Prioridades (
    PrioridadId INTEGER PRIMARY KEY AUTOINCREMENT,
    Nombre TEXT NOT NULL UNIQUE,
    Nivel INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS Estados (
    EstadoId INTEGER PRIMARY KEY AUTOINCREMENT,
    Nombre TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS Users (
    UserId INTEGER PRIMARY KEY AUTOINCREMENT,
    Username TEXT NOT NULL UNIQUE,
    Email TEXT UNIQUE,
    Role TEXT NOT NULL,
    Active INTEGER NOT NULL DEFAULT 1,
    AreaId INTEGER,
    DivisionId INTEGER,
    CreatedAt TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (AreaId) REFERENCES Areas (AreaId),
    FOREIGN KEY (DivisionId) REFERENCES Divisiones (DivisionId)
);

CREATE TABLE IF NOT EXISTS Tickets (
    TicketId INTEGER PRIMARY KEY AUTOINCREMENT,
    Title TEXT NOT NULL,
    Description TEXT NOT NULL,
    RequesterId INTEGER NOT NULL,
    SuggestedAssigneeId INTEGER,
    AssigneeId INTEGER,
    PlantaId INTEGER,
    AreaId INTEGER,
    CategoriaId INTEGER,
    SubcategoriaId INTEGER,
    PrioridadId INTEGER,
    EstadoId INTEGER,
    ConfidenceScore REAL,
    OriginalPrompt TEXT,
    AiProcessingTime INTEGER,
    ConversationId TEXT,
    NeedByAt TEXT,
    CreatedAt TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ClosedAt TEXT,
    FOREIGN KEY (RequesterId) REFERENCES Users (UserId),
    FOREIGN KEY (SuggestedAssigneeId) REFERENCES Users (UserId),
    FOREIGN KEY (AssigneeId) REFERENCES Users (UserId),
    FOREIGN KEY (PlantaId) REFERENCES Plantas (PlantaId),
    FOREIGN KEY (AreaId) REFERENCES Areas (AreaId),
    FOREIGN KEY (CategoriaId) REFERENCES Categorias (CategoriaId),
    FOREIGN KEY (SubcategoriaId) REFERENCES Subcategorias (SubcategoriaId),
    FOREIGN KEY (PrioridadId) REFERENCES Prioridades (PrioridadId),
    FOREIGN KEY (EstadoId) REFERENCES Estados (EstadoId)
);

CREATE TABLE IF NOT EXISTS TicketLogs (
    LogId INTEGER PRIMARY KEY AUTOINCREMENT,
    TicketId INTEGER NOT NULL,
    UserId INTEGER,
    IsAi INTEGER NOT NULL DEFAULT 0,
    FieldName TEXT NOT NULL,
    OldValue TEXT,
    NewValue TEXT,
    ChangedAt TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (TicketId) REFERENCES Tickets (TicketId),
    FOREIGN KEY (UserId) REFERENCES Users (UserId)
);

CREATE TABLE IF NOT EXISTS Subtasks (
    SubtaskId INTEGER PRIMARY KEY AUTOINCREMENT,
    TicketId INTEGER NOT NULL,
    Title TEXT NOT NULL,
    Description TEXT,
    AssigneeId INTEGER,
    EstadoId INTEGER,
    NeedByAt TEXT,
    CompletedAt TEXT,
    SortOrder INTEGER NOT NULL DEFAULT 0,
    CreatedAt TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CreatedBy INTEGER,
    UpdatedAt TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UpdatedBy INTEGER,
    FOREIGN KEY (TicketId) REFERENCES Tickets (TicketId),
    FOREIGN KEY (AssigneeId) REFERENCES Users (UserId),
    FOREIGN KEY (EstadoId) REFERENCES Estados (EstadoId),
    FOREIGN KEY (CreatedBy) REFERENCES Users (UserId),
    FOREIGN KEY (UpdatedBy) REFERENCES Users (UserId)
);

CREATE INDEX IF NOT EXISTS IX_Tickets_Estado ON Tickets (EstadoId);
CREATE INDEX IF NOT EXISTS IX_Tickets_Requester ON Tickets (RequesterId);
CREATE INDEX IF NOT EXISTS IX_Tickets_Conversation ON Tickets (ConversationId);
CREATE INDEX IF NOT EXISTS IX_TicketLogs_TicketId ON TicketLogs (TicketId, ChangedAt DESC);
CREATE INDEX IF NOT EXISTS IX_Subtasks_TicketId_SortOrder ON Subtasks (TicketId, SortOrder, SubtaskId);
