Aquí tienes un **Prompt Maestro** diseñado para que una IA (como ChatGPT, Claude o Gemini) actúe como un Arquitecto de Base de Datos Senior y genere el script SQL perfecto para tu proyecto.

Este prompt incorpora las mejores prácticas de normalización, auditoría para sistemas con IA y gestión de tickets extraídas de las fuentes analizadas,,.

Copia y pega el siguiente bloque:

***

### Prompt para Generar la Base de Datos

**Rol:** Eres un Arquitecto de Base de Datos Senior especializado en sistemas transaccionales (OLTP) y chatbots con IA.

**Objetivo:** Generar un script SQL completo (compatible con SQL Server/Azure SQL) para crear desde cero una base de datos optimizada para un "Sistema de Gestión de Tickets Asistido por IA".

**Contexto del Proyecto:**
Estoy desarrollando un sistema híbrido donde un chatbot recibe pedidos en lenguaje natural, una IA procesa la intención y extrae entidades, y un backend en Python guarda el ticket.
Actualmente tengo un esquema sucio donde uso mucho texto (`nvarchar`) en lugar de relaciones. Necesito profesionalizarlo.

**Instrucciones de Diseño (Requerimientos No Funcionales):**
1.  **Normalización (3NF):** Elimina cualquier redundancia. Los campos como `estado`, `prioridad`, `area`, `planta` y `categoria` NO deben ser texto en la tabla de tickets. Deben ser tablas maestras (Lookups) referenciadas por Foreign Keys (INT),.
2.  **Integridad Referencial:** Todas las relaciones deben tener `CONSTRAINT FK` explícitos.
3.  **Convenciones de Nombres:** Usa `snake_case` o `PascalCase` pero sé consistente. Tablas en plural (ej: `Tickets`), llaves primarias como `Id` o `TicketId`.
4.  **Auditoría y Trazabilidad:** Necesito una tabla de historial (`TicketLogs` o `AuditTrail`) que registre qué cambió, quién lo cambió (usuario o IA) y cuándo,.
5.  **Soporte para IA:** La tabla `Tickets` debe tener campos para almacenar metadatos de la IA, específicamente:
    *   `ConfidenceScore`: (decimal) Nivel de confianza de la predicción.
    *   `OriginalPrompt`: (text) Lo que escribió el usuario originalmente.
    *   `AiProcessingTime`: (int) Tiempo en ms (opcional).
    *   `ConversationId`: Para vincular con el chat de WhatsApp/Web.

**Entidades a Modelar (Basado en mi borrador anterior):**
1.  **Users:** Empleados, Técnicos y Administradores. Debe tener campo `Role` y `Active` (boolean).
2.  **Master Tables:** Crea tablas separadas para `Areas`, `Plantas`, `Categorias`, `Prioridades` y `Estados`. *Nota: Asegúrate de insertar scripts de datos semilla (INSERT) para los estados básicos (Abierto, En Progreso, Cerrado).*
3.  **Tickets:** La tabla central. Debe vincular al `RequesterId` (Solicitante) y `AssigneeId` (Técnico), ambos FK a `Users`.
4.  **Tasks:** (Opcional) Sub-tareas de un ticket.
5.  **TicketLogs:** Historial de cambios.

**Salida Esperada:**
*   Código DDL (CREATE TABLE...) optimizado.
*   Código DML inicial (INSERT INTO...) para poblar los catálogos básicos.
*   Explicación breve de por qué tomaste las decisiones de diseño (ej: índices).

***

### Por qué este prompt funciona (Justificación técnica)

1.  **Separa Datos Maestros (Lookups):**
    Al instruir explícitamente la creación de tablas para `Areas` y `Prioridades`, evitas el problema de tu modelo anterior donde guardabas texto. Esto permite que si mañana cambias el nombre del área "Mantenimiento" a "Infraestructura", solo lo cambies en un lugar y no en 10,000 tickets,.

2.  **Preparación para la IA:**
    Las fuentes indican que para mejorar los modelos de IA (aprendizaje continuo) necesitas analizar las fallas,. Al pedir campos como `ConfidenceScore` y `OriginalPrompt` en el diseño, estás preparando tu base de datos para futuras auditorías de calidad de la IA (ej: "Muéstrame todos los tickets donde la IA tuvo menos de 70% de confianza").

3.  **Trazabilidad (Logs):**
    Un sistema de tickets sin historial no sirve en entornos corporativos. El prompt pide una tabla de auditoría (`TicketLogs`), vital para saber si un ticket fue cerrado por un humano o automáticamente por el bot,.

4.  **Indexación:**
    Al pedir claves foráneas (`Foreign Keys`), la mayoría de los motores de base de datos modernos sugerirán o crearán índices automáticamente, lo cual es crucial para que las consultas de "Todos los tickets de Juan" sean rápidas.