# Infraestructura

Odoo 18 Community + PostgreSQL 16 con Docker Compose. En el servidor se agrega Caddy para HTTPS.

## 1. Local

```bash
cp .env.example .env
cp config/odoo.conf.example config/odoo.conf   # cambiar admin_passwd y poner workers = 0 (en local no hay proxy)
docker compose up -d db
# Crear la base quetzalmart una sola vez (sin datos demo, en español):
docker compose run --rm odoo odoo -d quetzalmart -i base --without-demo=all --load-language=es_419 --stop-after-init
docker compose up -d
```

Abrir http://localhost:8069 · usuario `admin` / contraseña `admin` (cambiarla de inmediato).

## 2. Servidor en la nube

1. Droplet de DigitalOcean: imagen Marketplace **Docker on Ubuntu 24.04**, plan Basic 2 vCPU / 4 GB, región New York o San Francisco, acceso por llave SSH.
2. Dominio: `DOMAIN=<ip-con-guiones>.sslip.io` (sin registro) o un subdominio de DuckDNS apuntando a la IP.
3. Cloud Firewall: abrir 80 y 443 a todo público; 22 y 5432 solo a las IPs del equipo / de la calificación.
4. Si la imagen no trae Docker: `curl -fsSL https://get.docker.com | sh && sudo usermod -aG docker $USER`
5. Clonar el repo, entrar a `PROYECTO/infra`, crear `.env` (con `PG_BIND=0.0.0.0` y `DOMAIN`) y `config/odoo.conf`.
6. Crear la base como en el paso local y luego: `docker compose --profile prod up -d`
7. Comprobar `https://<dominio>` y la conexión SQL externa:
   `psql "host=<ip> port=5432 dbname=quetzalmart user=odoo"`

## 3. Operación

| Acción | Comando |
|---|---|
| Ver logs | `docker compose logs -f odoo` |
| Actualizar un módulo | `docker compose run --rm odoo odoo -d quetzalmart -u <modulo> --stop-after-init` |
| Respaldo de la base | `docker compose exec db pg_dump -U odoo -Fc quetzalmart > quetzalmart_$(date +%F).dump` |
| Restaurar | `docker compose exec -T db pg_restore -U odoo -d quetzalmart --clean < archivo.dump` |

El script `../sql/init/01-base-rpa.sql` crea la base de staging `quetzalmart_rpa`; solo corre cuando el volumen `pg-data` es nuevo.
