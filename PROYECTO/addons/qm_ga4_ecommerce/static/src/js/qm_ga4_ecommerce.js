/** @odoo-module **/
/**
 * Eventos de comercio electrónico de GA4 que Odoo 18 no emite (ver __manifest__.py).
 * Los datos del carrito vienen del div .o_qm_ga4 que agrega views/templates.xml.
 *
 * Depuración: abrir cualquier página con ?qm_ga4_debug=1 marca los eventos con debug_mode
 * para verlos en GA4 > Administrar > DebugView (?qm_ga4_debug=0 lo desactiva).
 */
import publicWidget from "@web/legacy/js/public/public_widget";

const PREFIJO = "qm_ga4_";

function sesion(accion, clave, valor) {
    try {
        if (accion === "leer") {
            return window.sessionStorage.getItem(PREFIJO + clave);
        }
        if (accion === "borrar") {
            window.sessionStorage.removeItem(PREFIJO + clave);
        } else {
            window.sessionStorage.setItem(PREFIJO + clave, valor);
        }
    } catch {
        // Navegación privada o almacenamiento bloqueado: los eventos se envían igual.
    }
    return null;
}

function enviar(evento, parametros) {
    if (typeof window.gtag !== "function") {
        return;
    }
    const datos = { ...parametros };
    if (sesion("leer", "debug") === "1") {
        datos.debug_mode = true;
    }
    window.gtag("event", evento, datos);
}

const debug = new URLSearchParams(window.location.search).get("qm_ga4_debug");
if (debug === "1") {
    sesion("guardar", "debug", "1");
} else if (debug === "0") {
    sesion("borrar", "debug");
}

publicWidget.registry.QmGa4Ecommerce = publicWidget.Widget.extend({
    selector: ".o_website_sale_checkout",
    events: {
        "change input.js_quantity[data-product-id]": "_onCambioCantidad",
        'click [name="o_payment_submit_button"]': "_onPagar",
    },

    start() {
        const nodo = this.el.querySelector(".o_qm_ga4");
        this.datos = nodo ? JSON.parse(nodo.dataset.qmGa4 || "{}") : {};
        this.lineas = {};
        for (const linea of this.datos.lineas || []) {
            this.lineas[linea.product_id] = { ...linea.item };
        }
        if (this.datos.lineas) {
            this._eventoDePagina(window.location.pathname);
        }
        return this._super(...arguments);
    },

    _base() {
        return {
            currency: this.datos.currency,
            value: this.datos.value,
            items: Object.values(this.lineas),
        };
    },

    /** Envía el evento solo una vez por pedido (recargar la página no lo duplica). */
    _unaVez(evento, parametros) {
        const clave = `${evento}_${this.datos.pedido}`;
        if (sesion("leer", clave)) {
            return;
        }
        sesion("guardar", clave, "1");
        enviar(evento, parametros);
    },

    _eventoDePagina(ruta) {
        if (ruta.startsWith("/shop/cart")) {
            enviar("view_cart", this._base());
        } else if (ruta.startsWith("/shop/checkout") || ruta.startsWith("/shop/address")) {
            this._unaVez("begin_checkout", this._base());
        } else if (ruta.startsWith("/shop/payment")) {
            // Un cliente con dirección guardada salta directo al pago.
            this._unaVez("begin_checkout", this._base());
            if (this.datos.shipping_tier) {
                this._unaVez("add_shipping_info", { ...this._base(), shipping_tier: this.datos.shipping_tier });
            }
        }
    },

    _onCambioCantidad(ev) {
        const input = ev.currentTarget;
        const item = this.lineas[input.dataset.productId];
        const nueva = parseFloat(input.value);
        if (!item || Number.isNaN(nueva) || nueva === item.quantity) {
            return;
        }
        const diferencia = nueva - item.quantity;
        const cambio = { ...item, quantity: Math.abs(diferencia) };
        enviar(diferencia < 0 ? "remove_from_cart" : "add_to_cart", {
            currency: this.datos.currency,
            value: cambio.price * cambio.quantity,
            items: [cambio],
        });
        item.quantity = nueva;
        if (nueva <= 0) {
            delete this.lineas[input.dataset.productId];
        }
    },

    _onPagar() {
        const metodo = this.el.querySelector('input[name="o_payment_radio"]:checked');
        enviar("add_payment_info", {
            ...this._base(),
            payment_type: metodo ? metodo.dataset.paymentMethodCode || metodo.dataset.providerCode || "" : "",
        });
    },
});

export default publicWidget.registry.QmGa4Ecommerce;
