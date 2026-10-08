# Evidencias · Carga masiva de datos

Los datos se cargan **en el servidor** con los scripts de `PROYECTO/datos/` por XML-RPC (sin dependencias, idempotentes
con External IDs `__qm__.*`). Así las facturas PDF quedan en `PROYECTO/facturas_pdf/` del servidor, que es la carpeta
que se muestra en la calificación.

```bash
cd ~/SOG2-2S26_grupo14/PROYECTO/datos
cp .env.example .env              # ODOO_URL=http://127.0.0.1:8069 y la contraseña del admin
tmux new -s carga                 # la carga sigue aunque se corte el SSH
python3 -u cargar_todo.py 2>&1 | tee ~/carga_todo.log
```

Duración en el servidor: 25 minutos.

## Pasos

| # | Captura | Qué muestra | Comando o menú |
|---|---|---|---|
| 1 | `01-carga-pasos-01-04.png` | Salida de los pasos 01 a 04: configuración del ERP, datos maestros, empleados y materiales | `tac ~/carga_todo.log \| sed '/=== 01_configurar_erp/q' \| tac \| less` |
| 2 | `02-carga-pasos-05-09.png` | Salida de los pasos 05 a 09: compras, ventas, cotizaciones, PDF de facturas y gestor documental, con el tiempo total | Igual que la anterior, al final del log |
| 3 | `03-resumen-sql.png` | Resumen de requisitos: las 10 filas en `CUMPLE` | `sed -n '12,35p' ../sql/consultas_calificacion.sql \| docker compose exec -T db psql -U odoo -d quetzalmart` |
| 4 | `04-facturas-pdf.png` | Carpeta `facturas_pdf/` del servidor con los 150 PDF | `ls ../facturas_pdf \| head` y `ls ../facturas_pdf \| wc -l` |
| 5 | `05-ventas.png` | 150 órdenes de venta confirmadas | Ventas > Órdenes > Órdenes (filtro *Órdenes de venta*) |
| 6 | `06-cotizaciones.png` | 12 cotizaciones a clientes | Ventas > Órdenes > Cotizaciones, agrupado por *Estado* |
| 6b | `06b-cotizaciones-proveedores.png` | 8 solicitudes de cotización a proveedores (4 por enviar y 4 enviadas) | Compras > Órdenes > Solicitudes de cotización |
| 7 | `07-compras-factura.png` | 100 órdenes de compra confirmadas, todas totalmente facturadas | Compras > Órdenes > Órdenes de compra (columna *Estado de facturación*) |
| 8 | `08-materiales.png` | 60 materiales de operación `MAT-` | Inventario > Productos > Productos, buscar `MAT-` |
| 9 | `09-clientes.png` | Clientes cargados | Contactos (vista de lista) |
| 10 | `10-empleados.png` | 35 empleados con cargo y departamento | Empleados (vista de lista) |
| 11 | `11-facturas.png` | Facturas de cliente publicadas y su estado de pago | Facturación > Clientes > Facturas |

## Incidencias durante la carga

En una base nueva, `01_configurar_erp.py` falló al cargar el plan contable de Guatemala:
`TypeError: AccountChartTemplate.try_loading() missing 1 required positional argument: 'company'`.

- **Causa**: al instalar `account`, Odoo cargó primero el plan genérico (`generic_coa`), que deja la moneda en USD.
  El script intenta cambiar al plan `gt`, pero `try_loading` no es un método `@api.model` en Odoo 18 y por XML-RPC
  necesita una lista de ids vacía como primer argumento.
- **Corrección aplicada en el servidor** (sin asientos contables todavía), y luego se volvió a ejecutar `cargar_todo.py`:

  ```python
  o.accion("account.chart.template", "try_loading", [], "gt", compania, install_demo=False)
  o.write("res.company", compania, {"currency_id": o.ref("base.GTQ")})
  ```

- Resultado: compañía en GTQ con el plan `gt` y el IVA 12 %.

La lista de precios "Predeterminado" se había creado en USD con el plan genérico, así que las 150 ventas, las
12 cotizaciones, las 150 facturas de cliente y los 113 cobros quedaron en USD (las compras sí en GTQ).
No había tasas de cambio USD, de modo que todo se registró a tasa 1 y solo estaba mal la etiqueta de la moneda.

- **Corrección** (2026-10-08, con respaldo previo `pg_dump`): `correccion_moneda_gtq.sql`, en una transacción que
  primero verifica que no haya tasas USD ni montos distintos, y cambia a GTQ la lista de precios, las órdenes, las
  facturas, los cobros, sus líneas contables y las conciliaciones. Luego `docker compose restart odoo` y
  `python3 08_exportar_facturas.py --todas` para regenerar los PDF.
- Resultado: 0 documentos en USD; ventas, facturas y cobros en GTQ.
