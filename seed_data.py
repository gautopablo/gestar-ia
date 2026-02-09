"""
Seed data for GESTAR IA ticket system.
This file contains all master data that should be loaded into the database
when the application starts in a fresh environment (e.g., online deployment).
"""

# Estados del sistema
ESTADOS = [
    ("Abierto",),
    ("En Progreso",),
    ("Cerrado",),
]

# Niveles de prioridad
PRIORIDADES = [
    ("Baja", 3),
    ("Media", 2),
    ("Alta", 1),
    ("Crítica", 0),
]

# Divisiones de la empresa
DIVISIONES = [
    ("Sellado",),
    ("Forja",),
    ("Distribución",),
]

# Plantas
PLANTAS = [
    ("UT3",),
    ("UT1",),
]

# Categorías principales
CATEGORIAS = [
    ("Mantenimiento",),
    ("IT",),
    ("Producción",),
    ("Mantenimiento Industrial",),
    ("Sistemas e IT",),
    ("Matricería y Herramental",),
    ("Calidad",),
    ("Producción y Logística",),
    ("Ingeniería de Procesos",),
    ("Calidad y Procesos",),
]

# Subcategorías (Nombre, CategoriaId)
# Nota: CategoriaId se resolverá dinámicamente basado en el nombre de la categoría
SUBCATEGORIAS = [
    ("Falla Eléctrica", "Mantenimiento"),
    ("Maquinaria (Prensas/Inyectoras)", "Mantenimiento Industrial"),
    ("Servicios Generales (Luz/Agua/Gas)", "Mantenimiento Industrial"),
    ("Neumática e Hidráulica", "Mantenimiento Industrial"),
    ("PLC y Automatización", "Mantenimiento Industrial"),
    ("Edificio / Infraestructura", "Mantenimiento Industrial"),
    ("Software de Gestión (ERP)", "Sistemas e IT"),
    ("Hardware (PCs/Impresoras)", "Sistemas e IT"),
    ("Redes y Conectividad", "Sistemas e IT"),
    ("Telefonía / Comunicaciones", "Sistemas e IT"),
    ("Cuentas de Usuario y Accesos", "Sistemas e IT"),
    ("Reparación de Matriz", "Matricería y Herramental"),
    ("Construcción de Insertos", "Matricería y Herramental"),
    ("Pulido y Ajuste", "Matricería y Herramental"),
    ("Cambio de Modelo (Set-up)", "Matricería y Herramental"),
    ("Afilado de Herramientas", "Matricería y Herramental"),
    ("No Conformidad de Producto", "Calidad"),
    ("Calibración de Instrumentos", "Calidad"),
    ("Auditoría de Proceso", "Calidad"),
    ("Mejora Continua (KAIZEN)", "Calidad"),
    ("Documentación Técnica", "Calidad"),
    ("Abastecimiento de Materia Prima", "Producción y Logística"),
    ("Movimiento de Materiales (Autoelevadores)", "Producción y Logística"),
    ("Embalaje y Packaging", "Producción y Logística"),
    ("Planificación y PCP", "Producción y Logística"),
    ("Scrap / Retrabajo", "Producción y Logística"),
    ("No Conformidad de Producto", "Calidad y Procesos"),
    ("Calibración de Instrumentos", "Calidad y Procesos"),
    ("Auditoría de Proceso", "Calidad y Procesos"),
    ("Mejora Continua (KAIZEN)", "Calidad y Procesos"),
    ("Documentación Técnica", "Calidad y Procesos"),
]

# Áreas (Nombre, DivisionNombre)
# Nota: DivisionId se resolverá dinámicamente basado en el nombre de la división
AREAS = [
    ("Prensa 1", "Forja"),
    ("Prensa 2", "Forja"),
    ("Prensa 3", "Forja"),
    ("Mantenimiento", "Forja"),
    ("Calidad", "Forja"),
    ("Producción", "Forja"),
    ("Sellado Línea 1", "Sellado"),
    ("Sellado Línea 2", "Sellado"),
    ("Mantenimiento", "Sellado"),
    ("Calidad", "Sellado"),
    ("Logística", "Distribución"),
    ("Almacén", "Distribución"),
]

# Usuarios (Username, Email, Role)
USERS = [
    ("gauto_pablo", "gautop@taranto.com.ar", "Administracion"),
    ("ranea_mauricio", "ranea@taranto.com.ar", "Administracion"),
    ("firmapaz_alfredo", "firmapaz@taranto.com.ar", "Analista"),
    ("leiva_mauricio", "leivam@taranto.com.ar", "Analista"),
    ("riveros_emanuel", "riveroe@taranto.com.ar", "Analista"),
    ("parra_francisco", "parraf@taranto.com.ar", "Analista"),
    ("vazquez_pilar", "vazquezp@taranto.com.ar", "Analista"),
    ("guillen_lucas", "guillen@taranto.com.ar", "Analista"),
    ("vera_juan", "veraj@taranto.com.ar", "Analista"),
    ("brochero_joaquin", "brocheroo@taranto.com.ar", "Analista"),
    ("cane_alejandro", "cane@taranto.com.ar", "Director"),
]

# Mapeo de usuarios a áreas y divisiones (Username, AreaNombre, DivisionNombre)
# Este mapeo se usa para inferir área/división cuando se sugiere un usuario
USER_AREA_DIVISION_MAP = {
    "gauto_pablo": {"area": "Ing. Procesos", "division": None},
    "ranea_mauricio": {"area": "Ing. Procesos", "division": None},
    "firmapaz_alfredo": {"area": "Ing. Procesos", "division": None},
    "leiva_mauricio": {"area": "Ing. Procesos", "division": None},
    "riveros_emanuel": {"area": "Ing. Procesos", "division": None},
    "parra_francisco": {"area": "Ing. Procesos", "division": None},
    "vazquez_pilar": {"area": "Sistemas", "division": None},
    "guillen_lucas": {"area": "Ing. Procesos", "division": None},
    "vera_juan": {"area": "GICASH", "division": None},
    "brochero_joaquin": {"area": "Ing. Procesos", "division": None},
    "cane_alejandro": {"area": "Direccion D", "division": None},
}
