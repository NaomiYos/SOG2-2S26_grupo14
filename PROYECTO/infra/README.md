# Infraestructura

Odoo 18 Community + PostgreSQL 16 con Docker Compose. En el servidor se agrega Caddy para HTTPS.

## 1. Local

```bash
cp .env.example .env
cp config/odoo.conf.example config/odoo.conf   # cambiar admin_passwd y poner workers = 0 (en local no hay proxy)
sh obtener_addons.sh                           # módulos OCA (gestor documental) en ../addons/oca
docker compose up -d db
# Crear la base quetzalmart una sola vez (sin datos demo, en español):
docker compose run --rm odoo odoo -d quetzalmart -i base --without-demo=all --load-language=es_419 --stop-after-init
docker compose up -d
```

Abrir http://localhost:8069 · usuario `admin` / contraseña `admin` (cambiarla de inmediato).

## 2. Servidor en la nube

1. Instancia de AWS Lightsail `quetzalmart-erp`: Ubuntu 24.04 LTS, 2 vCPU / 4 GB / 80 GB, región Virginia (`us-east-1`),
   IP estática y acceso por llave SSH (usuario `ubuntu`). Detalle y capturas en `../evidencias/nube/`.
2. Dominio: `DOMAIN=<ip-con-guiones>.sslip.io` (sin registro; Caddy obtiene el certificado HTTPS solo).
3. Firewall de Lightsail: 80 y 443 a todo público; 22 abierto (solo entra quien tiene llave); 5432 solo a las IPs del equipo.
4. Docker lo instala el script de arranque de la instancia. Si falta: `curl -fsSL https://get.docker.com | sh && sudo usermod -aG docker $USER`.
   Agregar 2 GB de swap para que Odoo no se reinicie al generar los PDF.
5. Clonar el repo en `~/SOG2-2S26_grupo14`, entrar a `PROYECTO/infra`, crear `.env` (con `PG_BIND=0.0.0.0` y `DOMAIN`) y `config/odoo.conf`, y ejecutar `sh obtener_addons.sh`.
6. Crear la base como en el paso local y luego: `docker compose --profile prod up -d`
7. Comprobar `https://<dominio>` y la conexión SQL externa:
   `psql "host=<ip> port=5432 dbname=quetzalmart user=odoo"`

## 3. Operación

| Acción | Comando |
|---|---|
| Ver logs | `docker compose logs -f odoo` |
| Actualizar módulos OCA | `sh obtener_addons.sh && docker compose restart odoo` |
| Actualizar un módulo | `docker compose run --rm odoo odoo -d quetzalmart -u <modulo> --stop-after-init` |
| Respaldo de la base | `docker compose exec db pg_dump -U odoo -Fc quetzalmart > quetzalmart_$(date +%F).dump` |
| Restaurar | `docker compose exec -T db pg_restore -U odoo -d quetzalmart --clean < archivo.dump` |
| Respaldo de los adjuntos (imágenes, PDF, documentos) | `docker compose exec -T odoo tar czf - -C /var/lib/odoo filestore/quetzalmart > filestore_$(date +%F).tar.gz` |

En el servidor los respaldos se guardan en `~/respaldos/`. Antes de un cambio grande conviene además un snapshot de la
instancia en Lightsail (Instancia > Snapshots > Create snapshot).

El script `../sql/init/01-base-rpa.sql` crea la base de staging `quetzalmart_rpa`; solo corre cuando el volumen `pg-data` es nuevo.
