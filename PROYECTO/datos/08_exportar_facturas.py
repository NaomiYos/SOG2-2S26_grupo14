"""Paso 8: exporta a PDF las facturas de cliente publicadas.

Guarda cada factura en PROYECTO/facturas_pdf/<INV_2026_00001>.pdf usando el mismo reporte
que imprime Odoo. Las ya exportadas se omiten, así que al volver a ejecutarlo después de la
calificación solo agrega las facturas nuevas (por ejemplo, las de compras en la tienda web).

Uso: python 08_exportar_facturas.py            # solo las nuevas
     python 08_exportar_facturas.py --todas    # vuelve a generar todas
"""
import http.cookiejar
import json
import sys
import urllib.request
from pathlib import Path

from odoo_cliente import Odoo

DESTINO = Path(__file__).resolve().parent.parent / "facturas_pdf"
REPORTE = "account.report_invoice"


def sesion_web(odoo):
    """Abre una sesión HTTP en Odoo (los reportes PDF no están disponibles por XML-RPC)."""
    navegador = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    cuerpo = json.dumps({"jsonrpc": "2.0", "params": {"db": odoo.db, "login": odoo.usuario, "password": odoo.password}}).encode()
    peticion = urllib.request.Request(f"{odoo.url}/web/session/authenticate", cuerpo, {"Content-Type": "application/json"})
    respuesta = json.load(navegador.open(peticion))
    if "error" in respuesta:
        sys.exit(f"No se pudo iniciar sesión web: {respuesta['error']['data']['message']}")
    return navegador


def main():
    todas = "--todas" in sys.argv
    odoo = Odoo()
    navegador = sesion_web(odoo)
    DESTINO.mkdir(exist_ok=True)

    facturas = odoo.search_read("account.move", [("move_type", "=", "out_invoice"), ("state", "=", "posted")], ["name"], order="name")
    nuevas = 0
    for factura in facturas:
        archivo = DESTINO / f"{factura['name'].replace('/', '_')}.pdf"
        if archivo.exists() and not todas:
            continue
        pdf = navegador.open(f"{odoo.url}/report/pdf/{REPORTE}/{factura['id']}").read()
        if not pdf.startswith(b"%PDF"):
            sys.exit(f"Odoo no devolvió un PDF para {factura['name']}")
        archivo.write_bytes(pdf)
        nuevas += 1
        if nuevas % 25 == 0:
            print(f"  {nuevas} exportadas...")

    total = len(list(DESTINO.glob("*.pdf")))
    print(f"Facturas PDF: {nuevas} nuevas, {total} en {DESTINO}")


if __name__ == "__main__":
    main()
