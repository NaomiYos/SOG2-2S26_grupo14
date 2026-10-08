# Google Analytics 4 · Tienda en línea de QuetzalMart

Medición de comercio electrónico de la tienda de Odoo con GA4. Las capturas de cada paso van en
`PROYECTO/evidencias/ga4/` y los gráficos y CSV exportados en `PROYECTO/ga4/exportes/` (insumo del Manual 3).

> El ID de medición (`G-XXXXXXXXXX`) no es secreto (viaja en cada página), pero las credenciales de la cuenta de Google sí:
> no se suben al repo. Al resto del equipo se le da acceso como *Lector* desde Administrar > Administración de acceso.

## Estado (para quien continúe)

| Parte | Estado |
|---|---|
Actualizado el 2026-10-08.

| Parte | Estado |
|---|---|
| Propiedad GA4 y flujo web; ID de medición `G-34SH2SJWGK` en Odoo | Hecho |
| Barra de cookies desactivada (consentimiento concedido) | Hecho |
| Módulo `qm_ga4_ecommerce` instalado en el servidor | Hecho |
| Eventos llegando a GA4 (peticiones `collect` en Chrome e Informes > Tiempo real) | Hecho |
| `purchase` como evento clave | Hecho (GA4 lo marca por defecto) |
| `begin_checkout` como evento clave | Pendiente: la lista de Eventos de una propiedad nueva tarda hasta 24 h; luego se marca con la estrella de su fila |
| Tráfico con enlaces UTM y compras de prueba (sección 3) | En curso: enlaces enviados al grupo |
| 3 audiencias, 1 personalizada (sección 6) | Pendiente: revisar en Administrar > Audiencias si ya existen; crearlas cuanto antes, solo cuentan usuarios desde su creación |
| 3 segmentos de usuario y 5 de eventos (sección 4) | Pendiente |
| 2 exploraciones (sección 5) | Pendiente: se ven vacías hasta que haya datos procesados |
| Exportes (sección 7) y capturas (`PROYECTO/evidencias/ga4/NOTAS.md`) | Pendiente |

Lo que se configura dentro de GA4 no queda en el repo: para continuar, pedir acceso a la propiedad con rol *Editor*
(Administrar > Administración de acceso a la cuenta) y dejar capturas de cada paso en `PROYECTO/evidencias/ga4/`.

### Problemas conocidos

| Síntoma | Causa y solución |
|---|---|
| DebugView en 0 dispositivos y Tag Assistant no encuentra la etiqueta | El navegador bloquea Google Analytics: **Brave** (Shields), uBlock, AdBlock o Edge con prevención de seguimiento *Estricta*. Usar Chrome sin bloqueadores; quien genere tráfico con un bloqueador no cuenta en GA4 |
| DebugView no muestra `view_item`, `add_to_cart` ni `purchase` | Esos los emite Odoo sin la marca de depuración de `?qm_ga4_debug=1`. Usar Tag Assistant (tagassistant.google.com) o verlos en Informes > Tiempo real |
| Administrar > Eventos dice "Verás tus primeros informes de eventos aquí en un plazo de 24 horas" | Normal en una propiedad nueva. Para confirmar que llegan: Informes > Tiempo real, o F12 > Red > filtro `collect` |
| *Nuevo evento clave* pide una URL | Ese botón crea eventos clave a partir de una página. Los eventos existentes se marcan desde Administrar > Eventos con la estrella de su fila |
| En audiencias o segmentos no aparece un evento en la lista | Escribir el nombre a mano (`add_to_cart`, `purchase`); GA4 lo acepta aunque aún no lo haya procesado |

## 1. Conexión

1. En analytics.google.com: Administrar > Crear > Cuenta `QuetzalMart` > Propiedad `QuetzalMart Tienda`,
   zona horaria Guatemala, moneda **Quetzal (GTQ)**, sector *Compras*.
2. Flujo de datos > Web > URL `https://<ip-con-guiones>.sslip.io`, nombre `Tienda Odoo`, con *Medición mejorada* activa.
   Copiar el **ID de medición**.
3. En Odoo: Sitio web > Configuración > Ajustes > *Google Analytics* > pegar el ID de medición > Guardar.
4. En la misma pantalla, desactivar la **Barra de cookies**. Odoo inicia gtag con el consentimiento denegado y solo lo
   concede si el visitante acepta las cookies o si la barra está desactivada; con el consentimiento denegado GA4 no
   muestra a los usuarios en los informes.
5. Instalar el módulo `qm_ga4_ecommerce` (sección 2).

## 2. Eventos de comercio electrónico

| Evento | Cuándo se envía | Lo emite |
|---|---|---|
| `view_item` | Al abrir la página de un producto | Odoo 18 |
| `add_to_cart` | Al agregar un producto desde su página | Odoo 18 |
| `add_to_cart` | Al subir la cantidad dentro del carrito | `qm_ga4_ecommerce` |
| `view_cart` | Al abrir `/shop/cart` | `qm_ga4_ecommerce` |
| `remove_from_cart` | Al bajar la cantidad o eliminar una línea del carrito | `qm_ga4_ecommerce` |
| `begin_checkout` | Al entrar al checkout (dirección o, si ya la tiene, pago); una vez por pedido | `qm_ga4_ecommerce` |
| `add_shipping_info` | En la página de pago, con el método de envío elegido (`shipping_tier`) | `qm_ga4_ecommerce` |
| `add_payment_info` | Al presionar *Pagar*, con el método de pago (`payment_type`) | `qm_ga4_ecommerce` |
| `purchase` | En la página de confirmación del pedido (`transaction_id`, `value`, `tax`, `shipping`) | Odoo 18 |

Todos llevan `currency` (GTQ), `value` e `items` (`item_id`, `item_name`, `item_category`, `price`, `quantity`).
Odoo 18 no emite `begin_checkout` (solo una visita de página virtual `/stats/ecom/customer_checkout`), por eso existe el módulo.

**Instalación en el servidor** (desde `PROYECTO/infra`, el módulo ya está en `addons_path` porque vive en `PROYECTO/addons/`):

```bash
docker compose run --rm odoo odoo -d quetzalmart -i qm_ga4_ecommerce --stop-after-init
docker compose restart odoo
```

**Verificación**: abrir la tienda con `?qm_ga4_debug=1` (por ejemplo `https://<dominio>/shop?qm_ga4_debug=1`), recorrer
producto > carrito > checkout > pago y revisar Administrar > **DebugView**: deben aparecer los 9 eventos con sus parámetros.
`?qm_ga4_debug=0` desactiva el modo de depuración en ese navegador.

**Evento clave**: `purchase` ya viene marcado como evento clave en GA4 (Administrar > Eventos clave). Marcar también
`begin_checkout` para medir la conversión intermedia.

## 3. Indicadores que pide el enunciado

Los informes estándar tardan 24-48 h en mostrar datos; *Tiempo real* y *DebugView* son inmediatos.

| Indicador | Dónde se ve |
|---|---|
| Tasa de conversión | Informes > Interacción > Eventos clave > `purchase`, columna *Tasa de eventos clave de usuario*. También en la exploración de embudo (sección 5): % de usuarios que llegan a `purchase` |
| Adquisición de usuarios | Informes > Adquisición > Adquisición de usuarios, por *Fuente / medio del primer usuario* (llegan `facebook`, `email` y `google` gracias a los enlaces con UTM) |
| Total de ingresos | Informes > Monetización > Descripción general, tarjeta *Ingresos totales* (en GTQ) |
| Productos más vendidos | Informes > Monetización > Compras de comercio electrónico, ordenado por *Artículos comprados* |
| Abandono de carrito | Informes > Monetización > Recorrido de compra (o el embudo de la sección 5): % de abandono entre `add_to_cart` / `begin_checkout` y `purchase` |

### Enlaces con UTM para generar tráfico

| Canal | Enlace |
|---|---|
| Facebook | `https://<dominio>/shop?utm_source=facebook&utm_medium=social&utm_campaign=lanzamiento_tienda` |
| Correo | `https://<dominio>/shop?utm_source=email&utm_medium=email&utm_campaign=bienvenida` |
| Google | `https://<dominio>/shop?utm_source=google&utm_medium=cpc&utm_campaign=marca` |

Usar cada enlace desde dispositivos y navegadores distintos (celular, PC, ventana privada), con recorridos completos y
carritos abandonados a propósito, para que los segmentos y el embudo tengan datos.

## 4. Segmentos

Se crean dentro de una exploración: Explorar > (exploración) > Segmentos > **+**.

**Segmentos de usuarios (3)**

| Nombre | Condición |
|---|---|
| Compradores | Usuarios con el evento `purchase` |
| Abandonaron el carrito | Usuarios con `add_to_cart` **y sin** `purchase` (excluir usuarios con `purchase`) |
| Llegaron por campaña | Usuarios con *Fuente del primer usuario* = `facebook` o `email` o `google` |

**Segmentos de eventos (5)**

| Nombre | Condición |
|---|---|
| Vistas de producto | Evento `view_item` |
| Agregados al carrito | Evento `add_to_cart` |
| Inicio de pago | Evento `begin_checkout` |
| Compras | Evento `purchase` |
| Eliminados del carrito | Evento `remove_from_cart` |

## 5. Exploraciones (2)

1. **Embudo de compra** (Explorar > Exploración de embudo): pasos `view_item` → `add_to_cart` → `begin_checkout` → `purchase`,
   embudo abierto, desglose por *Categoría de dispositivo*, comparando los segmentos *Compradores*, *Abandonaron el carrito*
   y *Llegaron por campaña*. Muestra la tasa de conversión y el abandono en cada paso.
2. **Ventas por canal y producto** (Explorar > Forma libre): filas *Fuente / medio de la sesión*, columnas *Nombre del
   artículo*, valores *Ingresos de artículos* y *Artículos comprados*, con los segmentos de eventos *Compras* y
   *Agregados al carrito*.

## 6. Audiencias (3)

Administrar > Audiencias > Audiencia nueva.

| Audiencia | Tipo | Definición |
|---|---|---|
| Compradores | Sugerida (*Compradores*) | Usuarios con `purchase` |
| Usuarios recientes de la tienda | Sugerida (*Usuarios recientemente activos*) | Activos en los últimos 7 días |
| **Abandonaron el carrito (7 días)** | **Personalizada** | Incluir usuarios con `add_to_cart`; excluir de forma temporal a quienes tengan `purchase`; duración de pertenencia 7 días |

Las audiencias empiezan a acumular usuarios desde su creación (no hacia atrás): crearlas el primer día.

## 7. Exportes

Desde cada informe o exploración: Compartir > Descargar archivo > CSV o PDF, guardados en `PROYECTO/ga4/exportes/`
con nombres como `01-ingresos.csv`, `02-adquisicion.csv`, `03-mas-vendidos.csv`, `04-embudo.pdf`, `05-forma-libre.pdf`.
