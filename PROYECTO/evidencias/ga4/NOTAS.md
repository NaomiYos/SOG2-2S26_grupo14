# Evidencias · Google Analytics 4

Pasos detallados en `PROYECTO/ga4/configuracion.md`. Las capturas se toman en **Chrome** (Brave y los bloqueadores
de anuncios impiden que GA4 reciba los eventos).

| # | Captura | Qué muestra | Dónde |
|---|---|---|---|
| 1 | `01-propiedad.png` | Propiedad `QuetzalMart Tienda` con zona horaria Guatemala y moneda GTQ | Administrar > Detalles de la propiedad |
| 2 | `02-flujo-web.png` | Flujo web con la URL de la tienda y el ID de medición | Administrar > Flujos de datos |
| 3 | `03-odoo-id-medicion.png` | ID de medición en los ajustes del sitio web y barra de cookies desactivada | Odoo: Sitio web > Configuración > Ajustes |
| 4 | `04-modulo-qm-ga4.png` | Módulo `qm_ga4_ecommerce` instalado | Odoo: Aplicaciones, buscar `qm_ga4` |
| 5 | `05-collect-red.png` | Peticiones `collect` a GA4 con `en=view_item`, `en=add_to_cart`, etc. | Chrome: F12 > Red, filtro `collect` |
| 6 | `06-debugview.png` | Eventos de comercio electrónico en DebugView | Administrar > DebugView |
| 7 | `07-tiempo-real.png` | Usuarios y eventos en tiempo real | Informes > Tiempo real |
| 8 | `08-eventos-clave.png` | `purchase` y `begin_checkout` marcados como eventos clave | Administrar > Eventos clave |
| 9 | `09-audiencias.png` | Las 3 audiencias, con la personalizada *Abandonaron el carrito (7 días)* | Administrar > Audiencias |
| 10 | `10-audiencia-personalizada.png` | Condiciones de la audiencia personalizada | Administrar > Audiencias > la audiencia |
| 11 | `11-segmentos-usuario.png` | Los 3 segmentos de usuario | Explorar > exploración > Segmentos |
| 12 | `12-segmentos-eventos.png` | Los 5 segmentos de eventos | Explorar > exploración > Segmentos |
| 13 | `13-exploracion-embudo.png` | Embudo `view_item` > `add_to_cart` > `begin_checkout` > `purchase` con segmentos | Explorar > Embudo de compra |
| 14 | `14-exploracion-forma-libre.png` | Ingresos por fuente / medio y producto | Explorar > Ventas por canal y producto |
| 15 | `15-conversion.png` | Tasa de conversión | Informes > Interacción > Eventos clave |
| 16 | `16-adquisicion.png` | Adquisición de usuarios por fuente / medio | Informes > Adquisición > Adquisición de usuarios |
| 17 | `17-ingresos.png` | Ingresos totales en GTQ | Informes > Monetización > Descripción general |
| 18 | `18-mas-vendidos.png` | Productos más vendidos | Informes > Monetización > Compras de comercio electrónico |
| 19 | `19-abandono-carrito.png` | Abandono entre carrito y compra | Informes > Monetización > Recorrido de compra |

Las capturas 15 a 19 se toman cuando los informes estándar ya tengan datos (24-48 h después del tráfico).
