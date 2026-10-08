# Evidencias · Instalación en el servidor

Despliegue de Odoo 18 Community + PostgreSQL 16 + Caddy (HTTPS) con Docker Compose en la instancia de
AWS Lightsail `quetzalmart-erp` (ver `../nube/`). Se sigue la sección 2 de `PROYECTO/infra/README.md`.

> En las capturas se tapan la IP pública y el dominio; las contraseñas se muestran enmascaradas con `sed`.

## Pasos

| # | Captura | Qué muestra | Comando o menú |
|---|---|---|---|
| 1 | `01-swap.png` | Memoria de intercambio de 2 GB activa | `free -h` |
| 2 | `02-clonar-repo.png` | Repositorio clonado en el servidor | `git clone https://github.com/NaomiYos/SOG2-2S26_grupo14.git` |
| 3 | `03-env.png` | `.env` con `PG_BIND=0.0.0.0`, el dominio y la contraseña enmascarada | `sed -E 's/^(PG_PASSWORD=).*/\1********/' .env` |
| 4 | `04-odoo-conf.png` | `odoo.conf` con `workers = 2` y la clave maestra enmascarada | `sed -E 's/^(admin_passwd *= *).*/\1********/' config/odoo.conf` |
| 5 | `05-obtener-addons.png` | Descarga del módulo OCA `dms` en la versión fija | `mkdir -p ../addons` y `sh obtener_addons.sh` |
| 6 | `06-crear-base.png` | Creación de la base `quetzalmart` sin datos demo y en español | `docker compose run --rm odoo odoo -d quetzalmart -i base --without-demo=all --load-language=es_419 --stop-after-init` |
| 7 | `07-docker-compose-ps.png` | Contenedores `db`, `odoo` y `caddy` en ejecución | `docker compose --profile prod up -d` y `docker compose ps` |
| 8 | `08-sitio-https.png` | Pantalla de inicio de sesión de Odoo servida por HTTPS ("La conexión es segura", certificado de Let's Encrypt emitido por Caddy) | Navegador: `https://<ip-con-guiones>.sslip.io` |
| 9 | `09-login-odoo.png` | Primer inicio de sesión con `admin` / `admin`: Odoo avisa que se usa la contraseña predeterminada | Aplicaciones |
| 10 | `10-cambiar-contrasena.png` | Cambio de la contraseña inicial del administrador | Mi perfil > Seguridad de la cuenta > Cambiar contraseña |
| 11 | `11-psql-externo.png` | Conexión a PostgreSQL desde una PC del equipo | DBeaver o `psql "host=<ip> port=5432 dbname=quetzalmart user=odoo"` |

## Notas

- En un clon nuevo la carpeta `PROYECTO/addons/` no existe (git no guarda carpetas vacías y `addons/oca/` está
  en `.gitignore`), y `obtener_addons.sh` entra en ella antes de crearla. Por eso antes se ejecuta `mkdir -p ../addons`.

- El puerto 8069 de Odoo solo escucha en `127.0.0.1`; desde afuera se entra por Caddy (443), que también enruta
  `/websocket` al 8072. Por eso en el servidor `workers = 2`.
- La base de staging del RPA `quetzalmart_rpa` la crea `sql/init/01-base-rpa.sql` al inicializar el volumen de PostgreSQL.
- La memoria de intercambio evita que Odoo se reinicie por falta de memoria al generar los PDF de las facturas.
