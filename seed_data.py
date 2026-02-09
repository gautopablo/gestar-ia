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
    ("juan_perez", "juan@empresa.com", "Solicitante"),
    ("tecnico_1", "soporte@empresa.com", "Tecnico"),
    ("guillen_lucas", "guillen@taranto.com.ar", "Tecnico"),
    ("ranea_mauricio", "ranea@taranto.com.ar", "Tecnico"),
    ("garcia_martin", "garcia@taranto.com.ar", "Supervisor"),
    ("lopez_ana", "lopez@taranto.com.ar", "Solicitante"),
    ("rodriguez_carlos", "rodriguez@taranto.com.ar", "Tecnico"),
    ("fernandez_maria", "fernandez@taranto.com.ar", "Solicitante"),
]

# Mapeo de usuarios a áreas y divisiones (Username, AreaNombre, DivisionNombre)
# Este mapeo se usa para inferir área/división cuando se sugiere un usuario
USER_AREA_DIVISION_MAP = {
    "guillen_lucas": {"area": "Mantenimiento", "division": "Forja"},
    "ranea_mauricio": {"area": "Prensa 1", "division": "Forja"},
    "garcia_martin": {"area": "Producción", "division": "Forja"},
    "lopez_ana": {"area": "Sellado Línea 1", "division": "Sellado"},
    "rodriguez_carlos": {"area": "Mantenimiento", "division": "Sellado"},
    "fernandez_maria": {"area": "Logística", "division": "Distribución"},
}
