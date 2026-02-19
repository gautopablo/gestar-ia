# Plan de Implementacion: Logueo Real (Opcion 1)

## Objetivo

Implementar autenticacion real para la app usando:

- Azure App Service Authentication (Easy Auth).
- Microsoft Entra ID (single tenant, usuarios internos).

Resultado esperado:

- Solo usuarios autenticados pueden entrar a la app.
- Se elimina el selector manual de usuario.
- La app identifica al usuario logueado por su identidad de Entra ID.
- Si el usuario no existe en `gestar.Users`, se da de alta automaticamente con rol `Solicitante`.

## Alcance actual

- Entorno activo: `dev` (unico).
- URL app: `https://gestar.azurewebsites.net`.
- Este entorno se promovera a `prod` mas adelante.

## Configuracion aplicada (estado actual)

### 1) Entra ID - App Registration

- App registration: `gestar-ia-dev`.
- Supported account types: `My organization only`.
- Redirect URI (Web): `https://gestar.azurewebsites.net/.auth/login/aad/callback`.
- API permissions: `User.Read` y `email` (Microsoft Graph, delegated).
- Token configuration: optional claim `email` agregado.
- Ajuste clave para funcionamiento: habilitado `ID tokens (implicit and hybrid flows)`.

### 2) App Service - Authentication

- App Service authentication: `Enabled`.
- Restrict access: `Require authentication`.
- Unauthenticated requests: `Return HTTP 302 Found (Redirect to identity provider)`.
- Redirect provider: `Microsoft`.
- Identity provider configurado: `Microsoft (gestar-ia-dev)`.

### 3) Enterprise Application

- Enterprise app: `gestar-ia-dev`.
- Enabled for users to sign-in: `Yes`.
- Assignment required?: `No` (actualmente para facilitar primera etapa).

## Implementacion en app (`app.py`)

- Se removio el selector manual de usuario en header.
- Se toma identidad desde headers de Easy Auth:
  - `X-MS-CLIENT-PRINCIPAL-NAME`
  - `X-MS-CLIENT-PRINCIPAL-ID`
  - `X-MS-CLIENT-PRINCIPAL`
- Mapeo por email contra `gestar.Users`.
- Si no existe en `gestar.Users`, se auto-crea usuario `Active=1` con rol `Solicitante`.
- Se muestra el usuario logueado en cabecera (nombre/rol/email).

## Operacion diaria

### Login

- URL principal: `https://gestar.azurewebsites.net/`
- URL explicita de login (si se requiere):
  - `https://gestar.azurewebsites.net/.auth/login/aad?post_login_redirect_uri=/`

### Logout

- `https://gestar.azurewebsites.net/.auth/logout?post_logout_redirect_uri=/`

## Incidente resuelto en configuracion

Sintoma observado:

- Login completaba en Microsoft pero quedaba en `/.auth/login/aad/callback` con `401`.

Causa:

- Faltaba habilitar `ID tokens` en App Registration (`Authentication > Settings`).

Correccion aplicada:

- Se habilito `ID tokens (used for implicit and hybrid flows)`.

## Checklist de estado (dev)

- [x] App registration `gestar-ia-dev` creada.
- [x] Redirect URI de callback configurada.
- [x] Permisos `User.Read` + `email` configurados.
- [x] `ID tokens` habilitado.
- [x] Easy Auth activo en App Service.
- [x] `Require authentication` activo.
- [x] Selector manual de usuario removido.
- [x] Usuario autenticado mostrado en cabecera.
- [x] Auto-alta de usuario faltante con rol `Solicitante`.

## Pendientes

- Definir si se mantiene `Assignment required = No` o se restringe por grupo en etapa 2.
- Agregar boton de logout visible en la UI (opcional, ya existe URL funcional).
- Preparar estrategia de promocion a `prod`.

## Referencias internas

- Respaldo de datos de Azure/Entra y usuarios iniciales:
  - `info/RESPALDO_FASE0_AZURE_DEV.md`
