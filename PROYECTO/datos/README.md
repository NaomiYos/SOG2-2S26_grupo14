# Carga de datos

Scripts que configuran Odoo y cargan los datos del proyecto por XML-RPC.
Son idempotentes (usan External IDs `__qm__.*`): se pueden ejecutar varias veces y sirven igual
en local y contra el servidor, cambiando solo `.env`.

## Uso

```bash
cp .env.example .env      # ajustar URL, base, usuario y contraseña de Odoo
python cargar_todo.py     # ejecuta 01 a 09 en orden (~15 min en local)
```

Cada paso también se puede correr por separado (`python 05_compras.py`).
Después de la calificación, `python 08_exportar_facturas.py` agrega a la carpeta los PDF de las facturas nuevas.

Los scripts de carga requieren Python 3.10+ sin dependencias externas. Usar `ODOO_URL=http://127.0.0.1:8069` en local:
con `localhost` Windows intenta IPv6 primero y cada llamada tarda ~2 s.
En Windows, si la consola muestra mal los acentos: `python -X utf8 <script>`.

## Scripts

| Script | Qué hace |
|---|---|
| `odoo_cliente.py` | Conexión compartida y `upsert` por External ID |
| `operaciones.py` | Validar recepciones/entregas con fecha histórica, publicar y pagar facturas |
| `catalogo.py` | Datos fuente: categorías, proveedores, 60 productos, 60 materiales, departamentos, cargos y generadores deterministas de 80 clientes y 35 empleados |
| `01_configurar_erp.py` | Compañía QuetzalMart (GT, GTQ), módulos, plan contable GT con IVA 12 %, diarios en español, almacenes GT / MX / SV, logo, colores y diseño de documentos |
| `02_datos_maestros.py` | Etiquetas, categorías, proveedores, productos (imagen, EAN-13, precio, costo, peso, proveedor) y clientes |
| `03_empleados.py` | 3 lugares de trabajo, 5 departamentos con jefe, 6 cargos y 35 empleados con jefe directo |
| `04_materiales.py` | 60 materiales de operación (no se venden) en 5 subcategorías, con imagen, costo y proveedor |
| `05_compras.py` | 100 compras (abr-sep 2026) confirmadas, recibidas en GT / MX / SV y facturadas a 30 días; ~85 % pagadas. Deja inventario de los 60 productos en las 3 sucursales |
| `06_ventas.py` | 150 ventas (abr-oct 2026) a los 80 clientes, entregadas desde la sucursal del país del cliente y facturadas; ~80 % cobradas |
| `07_cotizaciones.py` | 20 cotizaciones sin confirmar: 12 a clientes y 8 solicitudes de presupuesto a proveedores |
| `08_exportar_facturas.py` | Exporta a `PROYECTO/facturas_pdf/` el PDF de cada factura de cliente publicada (omite las ya exportadas) |
| `09_gestor_documental.py` | Instala el gestor documental OCA `dms`: carpetas, grupo de acceso, 12 etiquetas en 4 categorías y los 15 PDF de `PROYECTO/dms/documentos/`, cada uno también adjunto a su factura, empleado o empresa de outsourcing |
| `cargar_todo.py` | Ejecuta todos los pasos anteriores en orden |
| `generar_imagenes.py` | Regenera `imagenes/productos/*.jpg` de productos y materiales (solo Windows + `pip install pillow`); las imágenes ya están en el repo |
| `generar_logo.py` | Regenera `imagenes/logo_quetzalmart.png` (solo Windows + Pillow) |
| `generar_documentos.py` | Regenera los 15 PDF de `PROYECTO/dms/documentos/` con datos de Odoo (`pip install reportlab`); ya están en el repo |

## Base nueva

El paso 09 necesita los módulos OCA descargados (`../infra/obtener_addons.sh`).

Al crear una base desde cero (ver `../infra/README.md`) el usuario es `admin` / `admin`.
Cambiar la contraseña en Odoo y ponerla en `ODOO_PASSWORD` antes de correr `cargar_todo.py`.

## Consultas SQL

En la base, los nombres traducibles (productos, categorías, cargos, departamentos, impuestos, diarios, etiquetas del gestor documental) se guardan como JSON:
usar `name->>'en_US'` (o `coalesce(name->>'es_419', name->>'en_US')`). El empleado del usuario
administrador también existe en la base: excluir `Administrator` al contar empleados.
