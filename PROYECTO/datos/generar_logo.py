"""Genera el logo de QuetzalMart en imagenes/logo_quetzalmart.png (horizontal, fondo transparente).

Requiere Windows (fuentes Segoe UI) y Pillow. Uso: python generar_logo.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from generar_imagenes import VERDE_QUETZAL, emoji

DESTINO = Path(__file__).with_name("imagenes") / "logo_quetzalmart.png"
ROJO_QUETZAL = "#C8102E"


def main():
    alto = 300
    logo = Image.new("RGBA", (1600, alto), (0, 0, 0, 0))
    dibujo = ImageDraw.Draw(logo)
    dibujo.rounded_rectangle((10, 10, alto - 10, alto - 10), radius=60, fill=VERDE_QUETZAL)
    ave = emoji("\U0001F99C", 190)
    # Silueta blanca del ave sobre el cuadro verde.
    silueta = Image.new("RGBA", ave.size, "#FFFFFF")
    logo.paste(silueta, ((alto - ave.width) // 2, (alto - ave.height) // 2), ave.getchannel("A"))

    fuente = ImageFont.truetype("segoeuib.ttf", 150)
    x = alto + 40
    dibujo.text((x, alto / 2 - 18), "Quetzal", font=fuente, fill=VERDE_QUETZAL, anchor="lm")
    x += dibujo.textlength("Quetzal", font=fuente)
    dibujo.text((x, alto / 2 - 18), "Mart", font=fuente, fill=ROJO_QUETZAL, anchor="lm")
    lema = ImageFont.truetype("segoeui.ttf", 44)
    dibujo.text((alto + 46, alto - 40), "Calidad a precios accesibles", font=lema, fill="#4B5563", anchor="ls")

    logo = logo.crop(logo.getbbox())
    logo.save(DESTINO, optimize=True)
    print(f"Logo en {DESTINO}")


if __name__ == "__main__":
    main()
