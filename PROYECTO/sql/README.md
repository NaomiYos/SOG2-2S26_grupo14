# Consultas SQL

| Archivo | Uso |
|---|---|
| `consultas_calificacion.sql` | Consultas para mostrar en la calificación que los datos están en la base (PostgreSQL) |
| `init/01-base-rpa.sql` | Crea la base de staging `quetzalmart_rpa` al inicializar PostgreSQL |

`consultas_calificacion.sql` empieza con un **resumen** que compara cada requisito del enunciado con lo cargado
(`CUMPLE` / `FALTA`) y luego tiene una sección por módulo: ventas, cotizaciones, empleados, compras,
materiales, facturas y gestor documental. La sección 8 cubre la tienda en línea (catálogo, pedidos web,
clientes registrados, correos), el CRM y las facturas más recientes, que son las que se generan durante la calificación.
La sección 9 queda para el RPA.

## Ejecutar

Todo el archivo, desde `PROYECTO/infra` (local o dentro del servidor):

```bash
docker compose exec -T db psql -U odoo -d quetzalmart < ../sql/consultas_calificacion.sql
```

Desde otra máquina (DBeaver, pgAdmin o psql), con el puerto 5432 abierto a esa IP en el firewall:

```
host: <IP del servidor>   puerto: 5432   base: quetzalmart   usuario: odoo   contraseña: PG_PASSWORD de infra/.env
```

En DBeaver/pgAdmin se puede abrir el archivo y ejecutar cada consulta por separado (Ctrl+Enter sobre la consulta).
