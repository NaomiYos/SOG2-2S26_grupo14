"""Paso 12: plantillas de correo de QuetzalMart (compra y campaña posterior a la compra).

1. Sube a Odoo, como adjuntos públicos, las imágenes que usan los correos. Quedan en una
   dirección fija: <url de Odoo>/qm/<archivo> (por ejemplo /qm/logo.jpg).
   Las busca en PROYECTO/marketing/imagenes/ y, si no están ahí, en PROYECTO/evidencias/.
2. Lee los HTML de PROYECTO/marketing/plantillas/ y crea o actualiza las plantillas de
   correo sobre el modelo Pedido de venta (sale.order).

Es idempotente: usa External IDs. Se puede ejecutar varias veces.

Uso: python -X utf8 12_plantillas_correo.py "QuetzalMart <ventas@su-dominio.com>"
El remitente debe ser exactamente el verificado en Brevo (no se guarda en el repo).
"""
import base64
import mimetypes
import re
import sys
from pathlib import Path

from odoo_cliente import Odoo

RAIZ = Path(__file__).resolve().parent.parent  # PROYECTO/
CARPETA_PLANTILLAS = RAIZ / "marketing" / "plantillas"
CARPETA_IMAGENES = RAIZ / "marketing" / "imagenes"
CARPETA_EVIDENCIAS = RAIZ / "evidencias"
PREFIJO_URL = "/qm/"

# id externo: (nombre de la plantilla, archivo HTML, asunto)
PLANTILLAS = {
    "plantilla_correo_compra": (
        "QuetzalMart - Confirmación de compra",
        "correo_compra.html",
        "¡Gracias por tu compra en QuetzalMart! Pedido {{ object.name }}",
    ),
    "plantilla_correo_campana": (
        "QuetzalMart - Campaña posterior a la compra",
        "correo_campana.html",
        "Tu súper favorito te espera en QuetzalMart",
    ),
}


def buscar_imagen(nombre):
    ruta = CARPETA_IMAGENES / nombre
    if ruta.exists():
        return ruta
    if CARPETA_EVIDENCIAS.exists():
        for candidata in CARPETA_EVIDENCIAS.rglob(nombre):
            return candidata
    return None


def subir_imagen(odoo, nombre, ruta):
    """Adjunto público con dirección fija /qm/<nombre>, igual en cualquier base."""
    odoo.upsert("ir.attachment", "img_" + re.sub(r"\W", "_", nombre), {
        "name": nombre,
        "type": "binary",
        "datas": base64.b64encode(ruta.read_bytes()).decode(),
        "mimetype": mimetypes.guess_type(nombre)[0] or "image/jpeg",
        "public": True,
        "url": PREFIJO_URL + nombre,
    })


def main():
    if len(sys.argv) < 2:
        raise SystemExit('Falta el remitente. Uso: python -X utf8 12_plantillas_correo.py "QuetzalMart <ventas@su-dominio.com>"')
    remitente = sys.argv[1]

    odoo = Odoo()
    modelo = odoo.search("ir.model", [("model", "=", "sale.order")], limit=1)[0]

    htmls = {}
    for clave, (nombre, archivo, asunto) in PLANTILLAS.items():
        ruta = CARPETA_PLANTILLAS / archivo
        if not ruta.exists():
            raise SystemExit(f"No se encontró {ruta}")
        htmls[clave] = ruta.read_text(encoding="utf-8")

    # Imágenes que los HTML piden en /qm/<archivo>
    nombres = sorted({n for html in htmls.values() for n in re.findall(PREFIJO_URL + r"([\w.\-]+\.(?:jpg|jpeg|png|gif|webp))", html)})
    faltantes = []
    for nombre in nombres:
        ruta = buscar_imagen(nombre)
        if ruta is None:
            faltantes.append(nombre)
            continue
        subir_imagen(odoo, nombre, ruta)
        print(f"Imagen subida: {PREFIJO_URL}{nombre}")
    if faltantes:
        print("AVISO: no se encontraron estas imágenes (el correo mostrará el texto alternativo):")
        for nombre in faltantes:
            print(f"  - {nombre}")

    for clave, (nombre, archivo, asunto) in PLANTILLAS.items():
        plantilla = odoo.upsert("mail.template", clave, {
            "name": nombre,
            "model_id": modelo,
            "email_from": remitente,
            "partner_to": "{{ object.partner_id.id }}",
        })
        # Asunto y cuerpo son campos traducibles: se escriben en inglés (base) y en español.
        for idioma in ("en_US", "es_419"):
            odoo.call("mail.template", "write", [plantilla], {"subject": asunto, "body_html": htmls[clave]},
                      context={"lang": idioma})
        print(f"Plantilla lista: {nombre} (id {plantilla})")


if __name__ == "__main__":
    main()