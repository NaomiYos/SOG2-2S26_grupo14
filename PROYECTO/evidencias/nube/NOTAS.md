# Evidencias · Cuenta en la nube (AWS Lightsail)

Proveedor: **Amazon Web Services · Lightsail**. Servidor: instancia `quetzalmart-erp` (Ubuntu 24.04 LTS,
plan de 2 vCPU / 4 GB / 80 GB SSD, región Virginia `us-east-1`), con IP estática y acceso solo por llave SSH.
Docker se instala con el script de arranque de la instancia.

> En las capturas se tapan las IP públicas, las IP del equipo, el correo, el ID de la cuenta y los datos de pago.
> Las llaves que se ven son públicas; las privadas nunca salen de cada PC.
> La IP y el dominio `<ip-con-guiones>.sslip.io` se comparten solo por privado.

## Pasos

| # | Captura | Qué muestra | Dónde / comando |
|---|---|---|---|
| 1 | `01-creditos-aws.png` | Créditos disponibles, vencimiento y servicios aplicables | Billing and Cost Management > Créditos |
| 2 | `02-presupuesto.png` | Presupuesto con alerta por correo | Billing and Cost Management > Presupuestos |
| 3 | `03-instancia-imagen.png` | Región, plataforma Linux/Unix y Ubuntu 24.04 LTS | Lightsail > Create instance |
| 4 | `04-instancia-script.png` | Script de arranque: instala Docker y agrega la llave del Bloque 1 | Create instance > Add launch script |
| 5 | `05-instancia-llave.png` | Llave SSH propia cargada como par `id_ed25519` | Create instance > SSH key > Upload key |
| 6 | `06-instancia-nombre.png` | Nombre de la instancia `quetzalmart-erp`, una sola instancia | Create instance > Configure your instance |
| 7 | `07-instancia-creada.png` | Instancia en estado *Running*: 4 GB, 2 vCPU, 80 GB, Virginia (`us-east-1a`), dual-stack | Lightsail > Instances > quetzalmart-erp |
| 8 | `08-ip-estatica.png` | IP estática `StaticIp-1` asignada a la instancia (reemplaza la IP pública temporal) | Instancia > Networking > Attach static IP |
| 9 | `09-firewall.png` | Reglas de entrada (IPv4 e IPv6 en una sola tabla): 80, 443 y 22 a todos; 5432 restringido | Instancia > Networking > Firewall rules |
| 10 | `10-ssh-docker.png` | Sesión `ssh ubuntu@<ip>` con `docker --version`, `docker compose version` y las dos llaves en `authorized_keys` | Terminal local |

## Script de arranque

Se ejecuta una sola vez como `root` al crear la instancia:

```bash
#!/bin/bash
curl -fsSL https://get.docker.com | sh
usermod -aG docker ubuntu
echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPtK+x+rTZRLKgvM5gBhpMYahtaqk2nKoAWX/MAKJEag quetzalmart' >> /home/ubuntu/.ssh/authorized_keys
```

## Reglas del firewall

| Aplicación | Protocolo | Puerto | Origen |
|---|---|---|---|
| HTTP | TCP | 80 | Cualquier dirección (IPv4 e IPv6) |
| HTTPS | TCP | 443 | Cualquier dirección (IPv4 e IPv6) |
| SSH | TCP | 22 | Cualquier dirección y consola SSH de Lightsail: el acceso es solo con llave y las IP domésticas cambian |
| PostgreSQL | TCP | 5432 | Solo las IPv4 de los integrantes que consultan la base (las demás personas usan un túnel SSH) |

Para dar acceso a otra persona:

- **Sitio y Odoo (80/443)**: no hace falta nada, están abiertos.
- **SSH**: agregar su llave pública en `/home/ubuntu/.ssh/authorized_keys`.
- **Base de datos**: agregar su IPv4 a la regla del 5432 o, si ya tiene SSH, usar un túnel sin tocar el firewall:
  `ssh -N -L 5433:127.0.0.1:5432 ubuntu@<ip>` y conectar DBeaver o psql a `localhost:5433`
  (o la pestaña *SSH* de la conexión en DBeaver).

El firewall de Lightsail filtra antes de llegar al servidor. No se usa `ufw` para el 5432 porque los puertos
publicados por Docker no pasan por `ufw`.

## Verificación

```bash
ssh ubuntu@<ip>
docker --version
docker compose version
cat ~/.ssh/authorized_keys     # dos llaves: la propia y "quetzalmart"
```
