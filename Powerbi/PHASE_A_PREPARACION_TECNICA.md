# Fase A - Preparacion Tecnica Power BI (Gestar)

## 1. Objetivo de la fase
Dejar lista la base técnica y operativa para construir el dataset en Power BI con Azure SQL como fuente oficial.

Resultado esperado de Fase A:
- conexión validada a Azure SQL
- usuario técnico de solo lectura definido
- alcance funcional acordado
- diccionario inicial de datos y métricas
- checklist de riesgos y permisos cerrada

## 2. Alcance de Fase A
Incluye:
- credenciales y conectividad
- inventario de tablas/campos
- definición de responsables
- definición de alcance de KPIs de v1
- criterios de validación para pasar a Fase B

No incluye:
- modelado DAX final
- diseño visual del reporte
- publicación en Power BI Service

## 3. Prerrequisitos
- Azure SQL activo y accesible.
- Esquema operativo: `gestar`.
- Tablas mínimas presentes:
  - `gestar.Tickets`
  - `gestar.Subtasks`
  - `gestar.TicketLogs`
  - catálogos (`Users`, `Estados`, `Prioridades`, `Areas`, `Divisiones`, `Plantas`, `Categorias`, `Subcategorias`)
- Owner funcional del tablero (negocio).
- Owner técnico (BI/IT).

## 4. Roles y responsables
- Sponsor funcional:
  - valida objetivos de negocio.
- Owner operativo:
  - define KPIs prioritarios y cortes de análisis.
- BI Developer:
  - construye modelo y reporte.
- DBA / Admin Azure SQL:
  - crea usuario/permiso de lectura y habilita conectividad.
- Seguridad IT:
  - valida acceso y cumplimiento.

## 5. Actividades detalladas

### A.1 Definir entorno objetivo
- Confirmar si el tablero leerá PROD, QA o ambos.
- Recomendación:
  - empezar por PROD si datos son confiables.
  - alternativamente usar QA para iterar diseño y luego cambiar origen.

Entregable:
- documento breve de entorno objetivo y justificación.

### A.2 Crear credencial técnica de solo lectura
- Crear login/usuario para Power BI con permisos mínimos.
- Permisos esperados:
  - `CONNECT`
  - `SELECT` sobre tablas `gestar` requeridas
- Evitar credenciales de administrador en BI.

Ejemplo de política:
- cuenta dedicada `pbi_gestar_reader`.
- contraseña gestionada por IT (vault/custodia corporativa).

Entregable:
- credenciales y alcance de permisos documentados.

### A.3 Validar conectividad de red
- Verificar firewall de Azure SQL para Power BI Service y/o gateway.
- Definir modo de acceso:
  - sin gateway (si Azure SQL público y permitido)
  - con On-premises Data Gateway (si política de red lo exige)
- Probar conexión desde Power BI Desktop.

Entregable:
- evidencia de conexión exitosa (captura o registro).

### A.4 Inventario técnico de fuentes
- Listar tablas/campos realmente necesarios para v1.
- Identificar claves y relaciones:
  - IDs, fechas, usuarios, estados, prioridades.
- Identificar campos problemáticos:
  - nulos, textos libres extensos, códigos no normalizados.

Entregable:
- inventario de tablas/campos v1 (tabular).

### A.5 Definir diccionario de negocio (versión inicial)
- Acordar definiciones de términos:
  - ticket abierto
  - ticket vencido
  - subtarea completada
  - backlog activo
- Acordar ventana temporal por defecto (ej. últimos 90 días).

Entregable:
- diccionario de métricas v0.1.

### A.6 Definir alcance funcional del MVP
- KPIs mínimos de v1:
  - tickets creados
  - tickets por estado
  - subtareas por estado
  - vencidos tickets/subtareas
  - carga por área/responsable
- Definir out-of-scope de v1 para no bloquear avance.

Entregable:
- backlog priorizado v1/v2.

### A.7 Validación de calidad de datos (diagnóstico)
- Checks SQL previos:
  - % nulos por campos clave (`EstadoId`, `NeedByAt`, `CreatedAt`, etc.)
  - integridad FK en `Subtasks.TicketId`
  - distribución de estados/prioridades
- Levantar issues y mitigaciones.

Entregable:
- informe de calidad inicial.

## 6. Checklist de cierre Fase A
- [ ] Conexión Power BI Desktop a Azure SQL validada.
- [ ] Usuario de lectura dedicado creado.
- [ ] Firewall/ruta de red resueltos.
- [ ] Inventario de tablas/campos v1 cerrado.
- [ ] Diccionario de métricas v0.1 aprobado.
- [ ] KPI MVP acordados con negocio.
- [ ] Riesgos de datos documentados.

## 7. Riesgos y mitigación
- Riesgo: timeout o bloqueos de red.
  - Mitigación: validar firewall + prueba repetible.
- Riesgo: métricas ambiguas.
  - Mitigación: diccionario firmado por negocio.
- Riesgo: permisos excesivos.
  - Mitigación: cuenta de solo lectura con alcance mínimo.
- Riesgo: calidad de datos insuficiente.
  - Mitigación: definir regla de exclusión/etiquetado desde Fase B.

## 8. Criterio de aceptación de Fase A
Fase A está completa cuando:
- cualquier BI developer puede conectarse de forma segura y estable
- existe una definición aprobada de KPIs y fuentes
- no hay bloqueantes técnicos para modelar en Fase B

## 9. Salidas para la Fase B
Inputs obligatorios para iniciar Fase B:
- credenciales + endpoint validados
- lista final de tablas/campos
- diccionario de métricas aprobado
- decisiones de alcance de MVP (incluye/excluye)

