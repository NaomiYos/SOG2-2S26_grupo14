# Carga de datos

Scripts que configuran Odoo y cargan los datos del proyecto por XML-RPC.
Son idempotentes (usan External IDs `__qm__.*`): se pueden ejecutar varias veces y sirven igual
en local y contra el servidor, cambiando solo `.env`.

## Uso

```bash
cp .env.example .env      # ajustar URL, base, usuario y contraseña de Odoo
python 01_configurar_erp.py
```

Requiere Python 3.10+ sin dependencias externas. En Windows, si la consola muestra mal los acentos: `python -X utf8 <script>`.

## Scripts

| Script | Qué hace |
|---|---|
| `odoo_cliente.py` | Conexión compartida y `upsert` por External ID |
| `01_configurar_erp.py` | Compañía QuetzalMart (GT, GTQ), módulos, plan contable GT con IVA 12 %, almacenes GT / MX / SV |
