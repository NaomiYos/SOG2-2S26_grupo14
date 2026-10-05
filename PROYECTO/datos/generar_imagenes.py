"""Genera las imágenes de producto en imagenes/productos/<QM-0001>.jpg.

Solo hace falta correrlo si cambia el catálogo; las imágenes resultantes se suben al repo
para que la carga en el servidor no necesite Pillow ni las fuentes de Windows.
Requiere Windows (fuentes Segoe UI Emoji y Segoe UI Bold) y Pillow: pip install pillow
Uso: python generar_imagenes.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from catalogo import CATEGORIAS, PRODUCTOS, codigo_producto

TAM = 800
DESTINO = Path(__file__).with_name("imagenes") / "productos"
VERDE_QUETZAL = "#0B7A4B"


def emoji(caracter, alto):
    # Segoe UI Emoji es vectorial (COLR): se dibuja grande y se ajusta al alto pedido.
    fuente = ImageFont.truetype("seguiemj.ttf", alto)
    lienzo = Image.new("RGBA", (alto * 2, alto * 2), (0, 0, 0, 0))
    ImageDraw.Draw(lienzo).text((alto, alto), caracter, font=fuente, embedded_color=True, anchor="mm")
    lienzo = lienzo.crop(lienzo.getbbox())
    escala = alto / lienzo.height
    return lienzo.resize((round(lienzo.width * escala), alto), Image.LANCZOS)


def texto_ajustado(dibujo, texto, fuente, ancho_max):
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = f"{actual} {palabra}".strip()
        if dibujo.textlength(prueba, font=fuente) <= ancho_max:
            actual = prueba
        else:
            lineas.append(actual)
            actual = palabra
    return lineas + [actual]


def generar(indice, categoria, nombre, simbolo):
    nombre_categoria, fondo, _proveedor = CATEGORIAS[categoria]
    img = Image.new("RGB", (TAM, TAM), fondo)
    dibujo = ImageDraw.Draw(img)

    # Círculo claro detrás del producto
    dibujo.ellipse((150, 70, 650, 570), fill="#FFFFFF")
    icono = emoji(simbolo, 340)
    img.paste(icono, ((TAM - icono.width) // 2, 320 - icono.height // 2), icono)

    # Nombre del producto
    fuente = ImageFont.truetype("segoeuib.ttf", 46)
    lineas = texto_ajustado(dibujo, nombre, fuente, TAM - 120)[:2]
    y = 615 if len(lineas) == 1 else 595
    for linea in lineas:
        dibujo.text((TAM / 2, y), linea, font=fuente, fill="#1F2933", anchor="mm")
        y += 56

    # Franja de marca
    dibujo.rectangle((0, TAM - 70, TAM, TAM), fill=VERDE_QUETZAL)
    marca = ImageFont.truetype("segoeuib.ttf", 30)
    dibujo.text((40, TAM - 35), "QuetzalMart", font=marca, fill="#FFFFFF", anchor="lm")
    dibujo.text((TAM - 40, TAM - 35), nombre_categoria, font=ImageFont.truetype("segoeui.ttf", 26), fill="#FFFFFF", anchor="rm")

    img.save(DESTINO / f"{codigo_producto(indice)}.jpg", quality=85, optimize=True)


def main():
    DESTINO.mkdir(parents=True, exist_ok=True)
    for i, (categoria, nombre, simbolo, *_resto) in enumerate(PRODUCTOS):
        generar(i, categoria, nombre, simbolo)
    print(f"{len(PRODUCTOS)} imágenes en {DESTINO}")


if __name__ == "__main__":
    main()
