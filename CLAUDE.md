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
| Correo saliente | Cuenta o dominio dedicado a QuetzalMart (SMTP), nunca el correo personal de un integrante | Requisito explícito |
| Analítica | GA4 con medición de comercio electrónico | Requisito explícito |
| RPA | UiPath Studio (Windows) → staging en la base `quetzalmart_rpa` → Odoo vía JSON-RPC | El dato queda visible en la base y en el sitio web |
| Datos masivos | Scripts Python con XML-RPC y **External IDs** (`qm_...`) | Recargar no duplica registros |

Módulos Enterprise que **no** existen aquí: Documents, Marketing Automation, Studio, Sign, Knowledge. No los propongas.

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

Actualiza esta tabla en el mismo commit que completa cada componente.

| Bloque | Componente | Estado |
|---|---|---|
| 2 | Cuenta en AWS, instancia Lightsail 4 GB, IP estática, firewall y acceso SSH para el Bloque 1 | Completado (`evidencias/nube/`): `quetzalmart-erp` en us-east-1 con Docker, IP estática, 5432 restringido |
| 2 | Despliegue en el servidor (Docker, Odoo, HTTPS, PostgreSQL accesible) y carga de datos con `datos/cargar_todo.py` | Completado (`evidencias/instalacion/`, `evidencias/carga_masiva/`): Odoo 18 con HTTPS en sslip.io, PostgreSQL accesible por IP, resumen SQL en CUMPLE, 150 PDF en el servidor; moneda corregida a GTQ |
| 2 | Evidencias de instalación, módulos y carga masiva en `PROYECTO/evidencias/` | Pendiente |
| 1 | ERP: módulos instalados y configurados (compañía, almacenes, impuestos) | Completado en local (`datos/01_configurar_erp.py`) |
| 1 | Datos maestros: productos (con imagen), clientes, proveedores | Completado en local (`datos/02_datos_maestros.py`): 60 productos, 80 clientes, 14 proveedores |
| 1 | Empleados, cargos y departamentos | Completado en local (`datos/03_empleados.py`): 35 empleados, 6 cargos, 5 departamentos |
| 1 | Ventas, cotizaciones, compras, materiales, facturas + 50 PDF | Completado en local (`datos/cargar_todo.py`): 150 ventas, 20 cotizaciones, 100 compras, 60 materiales, 250 facturas, 150 PDF |
| 1 | Gestor documental (OCA `dms`) con documentos y etiquetas | Completado en local (`datos/09_gestor_documental.py`): 15 documentos, 3 carpetas, 12 etiquetas |
| 1 | Consultas SQL de calificación | Completado (`sql/consultas_calificacion.sql`, secciones 0-7); el Bloque 2 agrega la sección 8 |
| 2 | Tienda en línea: catálogo, carrito, impuestos, envío, pago, factura por correo | Pendiente |
| 2 | Google Analytics 4: eventos, segmentos, exploraciones, audiencias | En progreso (`ga4/configuracion.md`, sección *Estado*): eventos de comercio electrónico llegando con `addons/qm_ga4_ecommerce`; faltan audiencias, segmentos, exploraciones y exportes |
| 2 | RPA UiPath | Pendiente |
| 2 | Marketing: correo de campaña posterior a la compra | Pendiente |
| — | Manuales 1, 2 y 3 | Pendiente |
