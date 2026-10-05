# Carga de datos

Scripts que configuran Odoo y cargan los datos del proyecto por XML-RPC.
Son idempotentes (usan External IDs `__qm__.*`): se pueden ejecutar varias veces y sirven igual
en local y contra el servidor, cambiando solo `.env`.

## Uso

```bash
cp .env.example .env      # ajustar URL, base, usuario y contraseña de Odoo
python 01_configurar_erp.py
python 02_datos_maestros.py
python 03_empleados.py
python 04_materiales.py
```

Los scripts de carga requieren Python 3.10+ sin dependencias externas. Usar `ODOO_URL=http://127.0.0.1:8069` en local: con `localhost` Windows intenta IPv6 primero y cada llamada tarda ~2 s. En Windows, si la consola muestra mal los acentos: `python -X utf8 <script>`.

## Scripts

| Script | Qué hace |
|---|---|
| `odoo_cliente.py` | Conexión compartida y `upsert` por External ID |
| `01_configurar_erp.py` | Compañía QuetzalMart (GT, GTQ), módulos, plan contable GT con IVA 12 %, almacenes GT / MX / SV |
| `catalogo.py` | Datos fuente: categorías, proveedores, 60 productos, 60 materiales, departamentos, cargos y generadores deterministas de 80 clientes y 35 empleados |
| `02_datos_maestros.py` | Etiquetas, categorías, proveedores, productos (imagen, EAN-13, precio, costo, peso, proveedor) y clientes |
| `03_empleados.py` | 3 lugares de trabajo, 5 departamentos con jefe, 6 cargos y 35 empleados con jefe directo |
| `04_materiales.py` | 60 materiales de operación (no se venden) en 5 subcategorías, con imagen, costo y proveedor |
| `generar_imagenes.py` | Regenera `imagenes/productos/*.jpg` de productos y materiales (solo Windows + `pip install pillow`); las imágenes ya están en el repo |

En la base, los nombres traducibles (productos, categorías, cargos, departamentos) se guardan como JSON:
en SQL usar `name->>'en_US'` (o `coalesce(name->>'es_419', name->>'en_US')`).
