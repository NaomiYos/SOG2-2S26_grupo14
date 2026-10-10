# CLAUDE.md — SOG2 · Grupo 14 · Segundo Semestre 2026

Guía de trabajo en este repositorio.
Léela completa antes de tocar código. Todo el contenido del repo se escribe en **español**.

## Integrantes

| Carné | Nombre |
|---|---|
| 202001814 | Naomi Rashel Yos Cujcuj |
| 202200252 | Néstor Enrique Villatoro Avendaño |
| 202202882 | Diego René Chen Teyul |
| 202200309 | Eduardo Angel Tubac Simón |
| 202103763 | Jennifer Yulissa Lourdes Taperio Manuel |
| 202200041 | Daniel Eduardo Velasquez Avila |

## Estructura del repositorio

```
PROYECTO/           Proyecto único QuetzalMart (35 pts). Enunciado: PROYECTO/Proyecto Segundo Semestre 2026.pdf
  infra/            docker-compose (Odoo + PostgreSQL + Caddy), configuración del servidor
  addons/           Módulos de Odoo: OCA (dms, etc.) y módulos propios con prefijo qm_
  datos/            Generadores y cargadores de datos masivos (Python, idempotentes)
  sql/              Consultas SQL para la calificación + scripts de inicialización
  facturas_pdf/     PDF de las facturas de cliente (generados con datos/08_exportar_facturas.py; no se suben)
  dms/              Documentos de ejemplo para el gestor documental (facturas, contratos)
  web/              Personalización de la tienda en línea y eventos GA4
  ga4/              Configuración documentada de Google Analytics (segmentos, audiencias, exploraciones)
  rpa/              Proyecto UiPath + generador de carpetas Excel de prueba
  marketing/        Plantillas de correo y reglas de automatización
  evidencias/       Capturas de pantalla por componente (insumo para los manuales)
```

Crea las carpetas a medida que se usen; no subas carpetas vacías.

## El proyecto en una página

QuetzalMart: cadena de supermercados con sede en Guatemala y sucursales en México y El Salvador.
Se implementa sobre **Odoo Community en la nube**:

| Componente | Requisito mínimo verificable (por web **y** por consulta SQL) |
|---|---|
| Ventas | ≥150 ventas (distintos productos y clientes) · ≥20 cotizaciones a clientes y proveedores |
| Empleados | ≥35 empleados · 6 cargos · 5 departamentos |
| Compras | ≥100 compras con su factura · ≥60 materiales de operación para las sucursales |
| Facturas | ≥50 facturas; los PDF visibles en una carpeta (+ las generadas en la calificación) |
| Portal web | Catálogo (imagen, descripción, precio) · carrito (agregar/quitar, impuestos, envío) · pago seguro · factura por correo · integrado a ERP y CRM |
| Google Analytics 4 | Eventos `view_item`, `add_to_cart`, `begin_checkout`, `purchase` · conversión, adquisición, ingresos, más vendidos, abandono de carrito · 3 segmentos de usuario, 5 de eventos · 2 exploraciones · 3 audiencias (≥1 personalizada) |
| Gestor documental | Integrado a Odoo · ≥5 facturas de proveedor, 5 contratos de outsourcing, 5 contratos de empleado · etiquetas/categorías para filtrar |
| RPA (UiPath) | Recorre la jerarquía de carpetas, toma solo los Excel con hoja `clientes` y/o `productos`, consolida y carga a la base; visible en el sitio web y por SQL. Se ejecuta en vivo en la calificación |
| Marketing | El auxiliar se registra en la tienda, compra, recibe el correo de la compra y **después** un correo de campaña. Asuntos distintos, remitente que no sea correo personal de un integrante. Se evalúa vistosidad y originalidad |

Entregables adicionales: 3 manuales en PDF (instalación y módulos, diagramas de flujo, BI con datos de GA4)
y el archivo de consultas SQL preparado para la calificación.

### Campos que el RPA debe respetar

- **clientes**: Name, Company Type, Related Company, Email, Phone, Street, Street2, City, State, Zip, Country, Tax ID, Website, Tags, Reference, Notes
- **productos**: ID Externo, Name, Product Type, Internal Reference, Barcode, Sales Price, Cost, Weight, Sales Description, Product Values, Cantidad a la mano, Está publicado

Las carpetas de origen (`clientes - ...`, `proveedores - ...`, `reclamos - ...`, `registro - ...`, `productos - ...`)
y los archivos tienen nombres poco prácticos; **el criterio es el nombre de la hoja, no el de la carpeta ni el del archivo**.
El juego real de carpetas se entrega el día de la calificación, así que el robot no puede depender de rutas fijas.

## Decisiones técnicas

| Tema | Decisión | Motivo |
|---|---|---|
| ERP | Odoo **18.0 Community** (imagen Docker oficial `odoo:18.0`) | La documentación del curso apunta a 18.0 |
| Base de datos | PostgreSQL 16 en el mismo servidor en la nube | Odoo solo funciona sobre PostgreSQL; el enunciado menciona MySQL/Oracle/SQL Server como ejemplos. Si el auxiliar exige otro motor, se replica la información a ese motor, nunca se cambia el de Odoo |
| Nube | Instancia de AWS Lightsail (Ubuntu 24.04 con Docker, 2 vCPU / 4 GB, IP estática) con Docker Compose, Caddy para HTTPS y dominio `<ip>.sslip.io` | Simple, cubierto por créditos de AWS y reproducible |
| Sucursales | Una compañía con 3 almacenes: `GT` (central), `MX`, `SV` | Mantiene la operación consolidada para los reportes |
| Localización | Guatemala, moneda GTQ, IVA 12 % | Sede central |
| Gestor documental | Módulo OCA `dms` | `Documents` es exclusivo de Enterprise |
| Marketing | `mass_mailing` + reglas de automatización (`base_automation`) + plantillas de correo | `Marketing Automation` es exclusivo de Enterprise |
| Correo saliente | Brevo (SMTP, puerto 587) con remitente `ventas@adasystemsgt.com`: dominio de un integrante, autenticado en Brevo (DKIM y DMARC). Nunca una cuenta Gmail/Outlook creada para el proyecto ni el correo personal de un integrante | Foro: no se permite crear una cuenta de Gmail u Outlook; sí un dominio o un correo saliente configurado en Odoo |
| Analítica | GA4 con medición de comercio electrónico | Requisito explícito |
| RPA | UiPath Studio (Windows) recorre las carpetas, consolida las hojas `clientes` y `productos` y las carga con la pantalla **Importar** de Odoo (automatización del navegador). **Sin API de Odoo** | Foro: no se permite usar ninguna API de Odoo desde UiPath. El dato queda visible en la base y en el sitio web |
| Datos masivos | Scripts Python con XML-RPC y **External IDs** (`qm_...`) | Recargar no duplica registros |

Módulos Enterprise que **no** existen aquí: Documents, Marketing Automation, Studio, Sign, Knowledge. No los propongas.

## Aclaraciones del auxiliar (foro y rúbrica, `PROYECTO/enunciado/`)

Mandan sobre el enunciado cuando lo contradicen.

| Tema | Aclaración |
|---|---|
| Cotizaciones | 20 de venta **y** 20 de compra (no 20 en total) |
| Compras | Confirmadas y con su factura |
| Sucursales | Basta una compañía con 3 almacenes |
| Pago | Se acepta un método de pago en modo de prueba si GA4 registra el `purchase` |
| Base de datos | PostgreSQL; una sola base en la nube, todo centralizado. En la calificación se llevan las consultas listas |
| RPA | Sin API de Odoo. Hojas y archivos con el nombre exacto (`clientes`, `productos`). Encabezados iguales a los archivos de ejemplo del foro: `External ID` (no `ID Externo`). `Related Company` y `Product Values` siempre vienen vacías. Obligatorias: `External ID`, `Name`, `Product Type` (productos) y `Name`, `Company Type` (clientes) |
| Correo | No crear cuentas Gmail/Outlook para el proyecto. En la calificación se usan direcciones de temp-mail.org: si ahí no llegan, hace falta dominio (SPF, DKIM, DMARC) |
| Correo de compra | Debe traer **adjunto el recibo o la factura** (rúbrica 1.32) |
| Audiencias GA4 | Las 3 son adicionales a la de abandono de carrito: la de abandono de carrito **no cuenta** (rúbrica 1.26) |
| Entrega | Un `.zip` con los 3 manuales en PDF; el enlace de Odoo va en el Manual 1 |
| Terraform | Permitido para desplegar |

## Entorno local

Requisitos: Docker Desktop, Python 3.11+.

```bash
cd PROYECTO/infra
cp .env.example .env                        # rellenar contraseñas
cp config/odoo.conf.example config/odoo.conf  # rellenar admin_passwd
docker compose up -d                        # Odoo en http://localhost:8069
docker compose --profile prod up -d         # en el servidor: agrega Caddy con HTTPS
```

La base de Odoo se llama `quetzalmart`. Ningún script debe asumir otro nombre.

## Reglas de trabajo

1. **Secretos**: `.env`, `odoo.conf`, credenciales SMTP, llaves de API y de GA4 nunca se suben. Usa `.env.example` con valores de ejemplo.
2. **Todo lo que se carga en Odoo debe poder repetirse con un script** de `PROYECTO/datos/`. Nada de datos que solo existan porque alguien los tecleó a mano, salvo configuración de pantallas (que se documenta en `evidencias/`).
3. Cargadores **idempotentes**: buscar por External ID antes de crear.
4. Cada consulta que demuestre un requisito va en `PROYECTO/sql/consultas_calificacion.sql`, con un comentario que diga qué requisito comprueba y el resultado esperado.
5. Módulos propios de Odoo: prefijo `qm_`, en `PROYECTO/addons/`, con su `__manifest__.py` versionado `18.0.x.y.z`.
6. **Evidencias**: al terminar cada paso relevante, guarda capturas en `PROYECTO/evidencias/<componente>/` numeradas (`01-instalar-modulo.png`, `02-...`) y un `NOTAS.md` con los pasos en orden. Los manuales se arman con eso: si no hay captura, no existe para el manual.
7. Antes de terminar una tarea, verifica contra la tabla de requisitos mínimos y deja la consulta SQL que lo comprueba.

## Commits y ramas

- `main` siempre debe levantar. Cada componente se trabaja en su rama y se integra por Pull Request:
  `infra/...`, `erp/...`, `datos/...`, `dms/...`, `web/...`, `ga4/...`, `rpa/...`, `mkt/...`, `docs/...`
- Formato de commit (Conventional Commits, en español, imperativo, ≤72 caracteres en el título):

  ```
  tipo(alcance): descripción corta

  Detalle opcional: qué y por qué.
  ```

  - **tipo**: `feat`, `fix`, `docs`, `chore`, `refactor`, `data`, `test`
  - **alcance**: `infra`, `erp`, `ventas`, `compras`, `empleados`, `facturas`, `datos`, `sql`, `dms`, `web`, `ga4`, `rpa`, `mkt`, `docs`
  - Ejemplos: `feat(infra): docker-compose de Odoo 18 y PostgreSQL`, `data(ventas): cargar 150 órdenes de venta`, `feat(rpa): filtrar libros por nombre de hoja`
- Un commit = un cambio lógico. No mezclar infraestructura con datos ni con documentación.
- Nada de commits tipo `xd`, `cambios`, `update`.

## Estado del proyecto

Una sola tabla: actualízala en el mismo commit que completa o cambia cada componente.
Verificado en el servidor el 2026-10-09 (consultas de `sql/consultas_calificacion.sql` y revisión de reglas, correos y pagos).

| Componente | Estado | Qué falta |
|---|---|---|
| Nube: AWS Lightsail `quetzalmart-erp` (us-east-1), IP estática, firewall, SSH | Hecho (`evidencias/nube/`) | — |
| Despliegue: Odoo 18 + PostgreSQL 16 + Caddy con HTTPS en `<ip-con-guiones>.sslip.io`, 5432 restringido | Hecho (`evidencias/instalacion/`) | Respaldo en `~/respaldos/` del servidor; falta un snapshot de Lightsail |
| ERP: compañía en GTQ, plan GT, IVA 12 %, almacenes GT / MX / SV | Hecho (`datos/01_configurar_erp.py`, ya con las correcciones de `try_loading` y GTQ) | Capturas de `evidencias/modulos/` |
| Datos maestros, 35 empleados / 6 cargos / 5 departamentos, 60 materiales | Hecho (`datos/02` a `04`) | Capturas |
| 150 ventas, 100 compras con factura, 150 facturas de cliente y sus PDF | Hecho (`datos/05`, `06`, `08`) | Repetir capturas 05, 06 y 11 de `evidencias/carga_masiva/` |
| Cotizaciones: 20 de venta y 20 de compra | Hecho (`datos/07_cotizaciones.py`, ejecutado en el servidor) | Capturas |
| Gestor documental (OCA `dms`): 15 documentos, 3 carpetas, 12 etiquetas | Hecho (`datos/09`) | Capturas del filtrado por etiquetas |
| Consultas SQL | Secciones 0 a 9 hechas y probadas en el servidor | — |
| Tienda: 60 productos `QM-` publicados con imagen, descripción e IVA; envío estándar Q30; transferencia bancaria | Hecho (`datos/10`, `11` + configuración en pantalla) | Capturas en `evidencias/tienda/`; considerar Stripe en modo de prueba |
| Correo de la compra y de campaña (Brevo, `ventas@adasystemsgt.com`) | Funciona: correo de la compra con la factura y la orden en PDF; la campaña llega 3 min después (regla "Confirmar pedidos de la tienda", `datos/13_regla_confirmacion.py`) | Quitar el tercer correo "Orden pendiente" (sale de `odoobot@example.com`); remitente "quetzalito mart" → "QuetzalMart"; correo de la compañía `info@quetzalmart.com` (dominio ajeno); probar con temp-mail.org; capturas en `evidencias/mkt/` |
| Factura del pedido web por correo y en la carpeta de PDF | Hecho desde el 2026-10-09 (regla de `datos/13`: confirma, factura, publica y adjunta el PDF; probado con S00180) | Los 8 pedidos web anteriores siguen "por facturar"; PDF de las facturas nuevas en la carpeta (`datos/08`) |
| CRM | Sin datos (0 oportunidades) | Oportunidades de ejemplo y regla que cree una al registrarse en la tienda |
| Google Analytics 4 | En progreso (`ga4/configuracion.md`): eventos llegando con `addons/qm_ga4_ecommerce` | Segmentos, exploraciones, 3 audiencias (ninguna de abandono de carrito), exportes y capturas |
| RPA UiPath | Hecho (`rpa/QuetzalMartRPA/`, `rpa/README.md`): ensayo completo el 2026-10-09 con `carpeta_prueba` en 1 min (10 clientes, 8 productos, 5 existencias; verificado con la sección 9 y en la tienda). Usuario Robot RPA creado con `datos/14_configurar_rpa.py`. Los registros de prueba quedaron archivados | Resto de capturas de `evidencias/rpa/` (01 a 14). En la PC de la calificación: credencial `QuetzalMartRobotRPA`, extensión de Chrome con acceso a URL de archivos y sin el aviso de guardar contraseña |
| Manuales 1, 2 y 3 | Pendiente | Guía completa en `PROYECTO/evidencias/README_manuales.md` |
