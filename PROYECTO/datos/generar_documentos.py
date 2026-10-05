"""Genera los 15 documentos de ejemplo del gestor documental en PROYECTO/dms/documentos/.

- 5 facturas emitidas por proveedores (coinciden con las facturas de proveedor registradas en Odoo).
- 5 contratos de servicios de outsourcing.
- 5 contratos individuales de trabajo.

Las facturas se arman con los datos reales de Odoo, así que hay que correrlo después de
05_compras.py. Los PDF resultantes se suben al repo: el servidor no necesita reportlab.
Requiere: pip install reportlab
Uso: python generar_documentos.py
"""
from datetime import date, timedelta
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from catalogo import CARGOS, COMPRAS_CON_FACTURA_DIGITAL, CONTRATOS_LABORALES, OUTSOURCING, PROVEEDORES, empleados
from odoo_cliente import Odoo

RAIZ = Path(__file__).resolve().parent.parent / "dms" / "documentos"
LOGO = Path(__file__).with_name("imagenes") / "logo_quetzalmart.png"
VERDE = colors.HexColor("#0B7A4B")
EMPRESA = "QuetzalMart, S.A."
NIT_EMPRESA = "12345678"
REPRESENTANTE = "Miguel Barrios Gómez"
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
         "octubre", "noviembre", "diciembre"]

estilos = getSampleStyleSheet()
TITULO = ParagraphStyle("titulo", parent=estilos["Title"], fontSize=15, textColor=VERDE, spaceAfter=10)
TEXTO = ParagraphStyle("texto", parent=estilos["BodyText"], fontSize=10, leading=14, alignment=TA_JUSTIFY, spaceAfter=6)
PEQUENO = ParagraphStyle("pequeno", parent=TEXTO, fontSize=8.5, leading=11, textColor=colors.HexColor("#4B5563"))
CENTRO = ParagraphStyle("centro", parent=TEXTO, alignment=TA_CENTER)


def fecha_larga(texto):
    d = date.fromisoformat(texto)
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def quetzales(valor):
    return f"Q {valor:,.2f}"


def encabezado_quetzalmart():
    logo = Image(str(LOGO), width=6.2 * cm, height=6.2 * cm * 281 / 1190)
    logo.hAlign = "LEFT"
    return [logo, Spacer(1, 0.4 * cm)]


def firmas(izquierda, derecha):
    tabla = Table([["", ""], ["_______________________________", "_______________________________"],
                   [izquierda, derecha]], colWidths=[8.5 * cm, 8.5 * cm], rowHeights=[1.6 * cm, 0.5 * cm, None])
    tabla.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("FONTSIZE", (0, 0), (-1, -1), 9)]))
    return tabla


def guardar(archivo, contenido):
    archivo.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(archivo), pagesize=LETTER, leftMargin=2.2 * cm, rightMargin=2.2 * cm,
                      topMargin=1.8 * cm, bottomMargin=1.8 * cm, title=archivo.stem, author=EMPRESA).build(contenido)


def facturas_proveedores(odoo):
    nombres = []
    for xmlid in COMPRAS_CON_FACTURA_DIGITAL:
        compra = odoo.search_read("purchase.order", [("id", "=", odoo.ref(f"__qm__.{xmlid}"))], ["name", "partner_id"])[0]
        factura = odoo.search_read("account.move", [("invoice_origin", "=", compra["name"]), ("move_type", "=", "in_invoice")],
                                   ["ref", "invoice_date", "invoice_date_due", "amount_total", "amount_tax"])[0]
        lineas = odoo.search_read("account.move.line", [("move_id", "=", factura["id"]), ("display_type", "=", "product")],
                                  ["name", "quantity", "price_unit", "price_total"])
        codigo = next(c for c, p in PROVEEDORES.items() if p[0] == compra["partner_id"][1])
        nombre, _pais, ciudad, calle, _etiqueta = PROVEEDORES[codigo]
        nit = odoo.search_read("res.partner", [("id", "=", compra["partner_id"][0])], ["vat"])[0]["vat"]

        filas = [["Cant.", "Descripción", "Precio unitario", "Total"]]
        filas += [[f"{l['quantity']:.0f}", Paragraph(l["name"].split("\n")[0], PEQUENO), quetzales(l["price_unit"]),
                   quetzales(l["price_total"])] for l in lineas]
        filas += [["", "", "IVA incluido (12 %)", quetzales(factura["amount_tax"])],
                  ["", "", "TOTAL", quetzales(factura["amount_total"])]]
        tabla = Table(filas, colWidths=[1.6 * cm, 9 * cm, 3.4 * cm, 3.2 * cm], repeatRows=1)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2933")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (2, 0), (-1, -1), "RIGHT"), ("ALIGN", (0, 0), (0, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -3), 0.4, colors.HexColor("#9CA3AF")),
            ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"), ("LINEABOVE", (2, -1), (-1, -1), 1, colors.black),
        ]))
        serie = factura["ref"]
        contenido = [
            Paragraph(f"<b>{nombre}</b>", ParagraphStyle("prov", parent=TEXTO, fontSize=14, textColor=colors.HexColor("#1F2933"))),
            Paragraph(f"{calle}, {ciudad} · NIT {nit} · ventas@{codigo.lower()}.proveedores.example.com", PEQUENO),
            Spacer(1, 0.5 * cm),
            Paragraph(f"FACTURA SERIE A · No. {serie}", TITULO),
            Table([["Cliente:", f"{EMPRESA} (NIT {NIT_EMPRESA})", "Fecha de emisión:", factura["invoice_date"]],
                   ["Dirección:", "6a. Avenida 10-25, Zona 1, Guatemala", "Vencimiento:", factura["invoice_date_due"]],
                   ["Orden de compra:", compra["name"], "Condición:", "Crédito 30 días"]],
                  colWidths=[3 * cm, 7 * cm, 3.4 * cm, 3.8 * cm],
                  style=[("FONTSIZE", (0, 0), (-1, -1), 9), ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                         ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold")]),
            Spacer(1, 0.5 * cm), tabla, Spacer(1, 0.8 * cm),
            Paragraph("Sujeto a pagos trimestrales ISR. Documento tributario emitido para fines del proyecto académico QuetzalMart.", PEQUENO),
        ]
        archivo = RAIZ / "facturas_proveedores" / f"Factura_{codigo}_{serie}.pdf"
        guardar(archivo, contenido)
        nombres.append(archivo)
    return nombres


def contratos_outsourcing():
    nombres = []
    for codigo, (nombre, pais, ciudad, calle, servicio, cuota, sucursal, inicio) in OUTSOURCING.items():
        fin = (date.fromisoformat(inicio) + timedelta(days=364)).isoformat()
        clausulas = [
            ("PRIMERA. Objeto.", f"EL PROVEEDOR se obliga a prestar a QUETZALMART los servicios de {servicio} "
             f"en la sucursal {sucursal} de QUETZALMART, con personal propio, capacitado y debidamente identificado."),
            ("SEGUNDA. Plazo.", f"El presente contrato tiene vigencia del {fecha_larga(inicio)} al {fecha_larga(fin)}, "
             "prorrogable por períodos iguales si ninguna de las partes manifiesta lo contrario con treinta días de anticipación."),
            ("TERCERA. Precio y forma de pago.", f"QUETZALMART pagará una cuota mensual de {quetzales(cuota)} con IVA incluido, "
             "dentro de los quince días siguientes a la recepción de la factura correspondiente."),
            ("CUARTA. Relación laboral.", "El personal asignado por EL PROVEEDOR no tendrá relación laboral alguna con QUETZALMART; "
             "EL PROVEEDOR asume todas las obligaciones patronales, de seguridad social y prestaciones."),
            ("QUINTA. Confidencialidad.", "EL PROVEEDOR guardará reserva sobre la información de clientes, precios, inventarios y "
             "procesos de QUETZALMART a la que tenga acceso, aun después de terminado el contrato."),
            ("SEXTA. Niveles de servicio.", "EL PROVEEDOR atenderá los incidentes reportados en un máximo de veinticuatro horas. "
             "El incumplimiento reiterado será causa de terminación anticipada sin responsabilidad para QUETZALMART."),
            ("SÉPTIMA. Aceptación.", "Ambas partes aceptan el contenido íntegro del presente contrato y lo firman en dos ejemplares."),
        ]
        contenido = encabezado_quetzalmart() + [
            Paragraph(f"CONTRATO DE PRESTACIÓN DE SERVICIOS DE OUTSOURCING No. QM-OUT-{codigo}-2026", TITULO),
            Paragraph(f"En la ciudad de Guatemala, el {fecha_larga(inicio)}, comparecen por una parte {REPRESENTANTE}, "
                      f"en representación de <b>{EMPRESA}</b>, en adelante QUETZALMART; y por la otra parte el representante "
                      f"legal de <b>{nombre}</b>, con domicilio en {calle}, {ciudad}, en adelante EL PROVEEDOR, quienes "
                      "convienen en celebrar el presente contrato de servicios, sujeto a las cláusulas siguientes:", TEXTO),
        ]
        contenido += [Paragraph(f"<b>{titulo}</b> {texto}", TEXTO) for titulo, texto in clausulas]
        contenido += [Spacer(1, 0.6 * cm), firmas(f"{REPRESENTANTE}\nQuetzalMart, S.A.", f"Representante legal\n{nombre}")]
        archivo = RAIZ / "contratos_outsourcing" / f"Contrato_outsourcing_{codigo}_{pais.upper()}.pdf"
        guardar(archivo, contenido)
        nombres.append(archivo)
    return nombres


def contratos_empleados():
    nombres = []
    lista = empleados()
    for cargo, salario in CONTRATOS_LABORALES.items():
        e = next(x for x in lista if x["cargo"] == cargo)
        inicio = f"2026-0{1 + list(CONTRATOS_LABORALES).index(cargo)}-01"
        puesto = CARGOS[cargo][0]
        clausulas = [
            ("PRIMERA. Puesto.", f"EL TRABAJADOR prestará sus servicios en el puesto de <b>{puesto}</b>, en la sede "
             "Guatemala de QUETZALMART, desempeñando las atribuciones propias del cargo."),
            ("SEGUNDA. Inicio y plazo.", f"La relación de trabajo inicia el {fecha_larga(inicio)} por tiempo indefinido, "
             "con un período de prueba de dos meses conforme al Código de Trabajo de Guatemala."),
            ("TERCERA. Jornada.", "La jornada ordinaria será diurna, de lunes a sábado, sin exceder de cuarenta y cuatro horas semanales."),
            ("CUARTA. Salario.", f"EL TRABAJADOR devengará un salario mensual de {quetzales(salario)}, más la bonificación incentivo "
             "de ley, pagaderos en quincenas vencidas mediante depósito bancario."),
            ("QUINTA. Prestaciones.", "EL TRABAJADOR gozará de vacaciones, aguinaldo, bono 14, afiliación al IGSS y demás "
             "prestaciones establecidas en la legislación laboral vigente."),
            ("SEXTA. Obligaciones.", "EL TRABAJADOR se compromete a cumplir el reglamento interior de trabajo, las políticas de "
             "atención al cliente y de manejo de inventarios, y a guardar confidencialidad sobre la información de la empresa."),
        ]
        contenido = encabezado_quetzalmart() + [
            Paragraph(f"CONTRATO INDIVIDUAL DE TRABAJO No. QM-RH-{e['codigo']}-2026", TITULO),
            Paragraph(f"En la ciudad de Guatemala, el {fecha_larga(inicio)}, comparecen {REPRESENTANTE}, en representación de "
                      f"<b>{EMPRESA}</b>, en adelante QUETZALMART; y <b>{e['nombre']}</b>, con Documento Personal de "
                      f"Identificación {e['identificacion']}, en adelante EL TRABAJADOR, quienes celebran el presente contrato "
                      "individual de trabajo sujeto a las cláusulas siguientes:", TEXTO),
        ]
        contenido += [Paragraph(f"<b>{titulo}</b> {texto}", TEXTO) for titulo, texto in clausulas]
        contenido += [Spacer(1, 0.6 * cm), firmas(f"{REPRESENTANTE}\nQuetzalMart, S.A.", f"{e['nombre']}\nTrabajador(a)")]
        archivo = RAIZ / "contratos_empleados" / f"Contrato_laboral_{e['codigo']}_{cargo}.pdf"
        guardar(archivo, contenido)
        nombres.append(archivo)
    return nombres


def main():
    odoo = Odoo()
    archivos = facturas_proveedores(odoo) + contratos_outsourcing() + contratos_empleados()
    print(f"{len(archivos)} documentos en {RAIZ}")


if __name__ == "__main__":
    main()
