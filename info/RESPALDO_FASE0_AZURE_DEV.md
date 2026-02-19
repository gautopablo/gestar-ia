# Respaldo Fase 0 - Azure (entorno actual)

Fecha de registro: 2026-02-19
Fuente: capturas de Azure Portal compartidas en chat.

## 1) App Service (Web App)

- Nombre app: `gestar`
- Tipo: `Web App`
- Resource Group: `rg-gestar-prod`
- Status: `Running`
- Location: `Central US`
- Subscription: `Azure subscription 1`
- Subscription ID: `da5a1931-c2b2-4223-bb42-095fd346da5e`
- Default domain / URL: `https://gestar.azurewebsites.net`
- App Service Plan: `ASP-rggestarprod-9b8b (F1: 1)`
- Operating System: `Linux`
- Health Check: `Not Configured`
- GitHub Project: `https://github.com/gautopablo/gestar-ia`

## 2) Microsoft Entra ID (tenant)

- Tenant Name: `TARANTO SAN JUAN SA`
- Tenant ID: `497911ba-d759-4094-8fb6-248c66c63885`
- Primary domain: `taranto.com.ar`
- License: `Microsoft Entra ID Free`
- Users: `729`
- Groups: `212`
- Applications: `9`
- Devices: `778`

## 3) Alcance de entorno (aclaracion para el plan)

- Entorno activo hoy: `dev (unico)`
- Estrategia actual: esta instancia se usara como base y luego se promovera a `prod`.
- QA separado: `pendiente / no aplica en esta etapa`.

## 4) Pendientes para completar Fase 0

- [ ] Confirmar usuario(s) piloto para prueba de login.
- [ ] Confirmar si el acceso sera por grupo (`GESTAR_IA_DEV_USERS`) o asignacion directa.
- [ ] Confirmar responsable tecnico para ejecutar Fase 1.

## 5) Usuarios piloto etapa 1 (tabla `gestar.Users`)

Consulta origen:

```sql
SELECT TOP (1000) * FROM [gestar].[Users]
```

Registros visibles en captura:

| UserId | Username         | Email                    | Role           | Active | CreatedAt                   |
|---|---|---|---|---|---|
| 1  | gauto_pablo      | gautop@taranto.com.ar    | Administracion | True   | 2026-02-09T14:05:10.9606588 |
| 2  | ranea_mauricio   | ranea@taranto.com.ar     | Administracion | True   | 2026-02-09T14:05:10.9606588 |
| 3  | firmapaz_alfredo | firmapaz@taranto.com.ar  | Analista       | True   | 2026-02-09T14:05:10.9606588 |
| 4  | leiva_mauricio   | leivam@taranto.com.ar    | Analista       | True   | 2026-02-09T14:05:10.9762763 |
| 5  | riveros_emanuel  | riveroe@taranto.com.ar   | Analista       | True   | 2026-02-09T14:05:10.9762763 |
| 6  | parrs_francisco  | parrsf@taranto.com.ar    | Analista       | True   | 2026-02-09T14:05:10.9762763 |
| 7  | vazquez_pilar    | vazquezp@taranto.com.ar  | Analista       | True   | 2026-02-09T14:05:10.9762763 |
| 8  | guillen_lucas    | guillen@taranto.com.ar   | Analista       | True   | 2026-02-09T14:05:10.9762763 |
| 9  | vera_juan        | veraj@taranto.com.ar     | Analista       | True   | 2026-02-09T14:05:10.9762763 |
| 10 | brochero_joaquin | brocheroo@taranto.com.ar | Analista       | True   | 2026-02-09T14:05:10.9919092 |
| 11 | cane_alejandro   | cane@taranto.com.ar      | Director       | True   | 2026-02-09T14:05:10.9919092 |

Notas:

- En la captura, la columna `AreaId` aparece sin valor visible para estos registros.
- Esta lista debe cruzarse con usuarios de Entra ID por `email` para el mapeo de login.

## 6) Fase 1 - Datos tomados de App Registration `gestar-ia-dev`

Fuente: captura de pantalla `Overview` en `App registrations`.

- Display name: `gestar-ia-dev`
- Application (client) ID: `a173501e-5d1f-4720-8bcd-210d5adb23bd`
- Object ID: `3ed54021-0ed6-44df-8289-fcc5b93d2da6`
- Directory (tenant) ID: `497911ba-d759-4094-8fb6-248c66c63885`
- Supported account types: `My organization only`
- Redirect URIs: `1 web, 0 spa, 0 public client`
- Managed application in local directory: `gestar-ia-dev`
- State: `Activated`
