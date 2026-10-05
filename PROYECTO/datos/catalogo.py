"""Datos maestros de QuetzalMart: categorías, proveedores, productos y clientes.

Los clientes se generan con semilla fija para que cada ejecución produzca los mismos registros.
Los correos usan el dominio reservado example.com para que ninguna campaña llegue a terceros.
"""
import random
import unicodedata

# código de categoría: (nombre, color de fondo de la imagen, código de proveedor)
CATEGORIAS = {
    "ABA": ("Abarrotes", "#F6E7C8", "P01"),
    "BEB": ("Bebidas", "#CDEBF7", "P02"),
    "LAC": ("Lácteos y huevos", "#E6EEF9", "P03"),
    "PAN": ("Panadería", "#F7DCC0", "P04"),
    "CAR": ("Carnes y mariscos", "#F7D3D3", "P05"),
    "FYV": ("Frutas y verduras", "#D8F0CF", "P06"),
    "SNK": ("Snacks y dulces", "#F3D6EA", "P07"),
    "LIM": ("Limpieza del hogar", "#D3F0EC", "P08"),
    "CPE": ("Cuidado personal", "#E3DDF5", "P09"),
    "DES": ("Café y desayuno", "#EADBCB", "P10"),
}

# código: (nombre, país, ciudad, calle, etiqueta)
PROVEEDORES = {
    "P01": ("Distribuidora La Cosecha, S.A.", "gt", "Ciudad de Guatemala", "Calzada Roosevelt 22-43, Zona 11", "Proveedor nacional"),
    "P02": ("Embotelladora del Pacífico, S.A.", "gt", "Escuintla", "Km 58 Carretera al Pacífico", "Proveedor nacional"),
    "P03": ("Lácteos Los Altos, S.A.", "gt", "Quetzaltenango", "4a. Calle 15-20, Zona 3", "Proveedor nacional"),
    "P04": ("Panificadora San Martín, S.A.", "gt", "Mixco", "Calzada San Juan 32-10, Zona 7", "Proveedor nacional"),
    "P05": ("Cárnicos de Centroamérica, S.A. de C.V.", "sv", "Santa Tecla", "Carretera Panamericana Km 12", "Proveedor internacional"),
    "P06": ("Agroexportadora Verapaz, S.A.", "gt", "Cobán", "1a. Avenida 3-45, Zona 2", "Proveedor nacional"),
    "P07": ("Dulces y Botanas del Norte, S.A. de C.V.", "mx", "Monterrey", "Av. Constitución 2050, Centro", "Proveedor internacional"),
    "P08": ("Químicos Industriales Maya, S.A.", "gt", "Villa Nueva", "Km 17.5 Carretera al Pacífico", "Proveedor nacional"),
    "P09": ("Higiene Total de México, S.A. de C.V.", "mx", "Guadalajara", "Av. Vallarta 3233, Vallarta Poniente", "Proveedor internacional"),
    "P10": ("Café de Altura Antigua, S.A.", "gt", "Antigua Guatemala", "5a. Avenida Norte 30", "Proveedor nacional"),
    "P11": ("Empaques del Istmo, S.A.", "gt", "Ciudad de Guatemala", "Av. Petapa 45-60, Zona 12", "Proveedor de materiales"),
    "P12": ("Suministros de Oficina La Pluma, S.A.", "gt", "Ciudad de Guatemala", "10a. Calle 5-30, Zona 1", "Proveedor de materiales"),
    "P13": ("Refrigeración y Equipos Comerciales, S.A. de C.V.", "sv", "San Salvador", "Alameda Juan Pablo II 512", "Proveedor de materiales"),
    "P14": ("Uniformes y Seguridad Industrial, S.A. de C.V.", "mx", "Ciudad de México", "Calz. de Tlalpan 1924, Country Club", "Proveedor de materiales"),
}

# (categoría, nombre, emoji de la imagen, precio de venta Q, costo Q, peso kg, descripción)
PRODUCTOS = [
    ("ABA", "Arroz blanco 1 kg", "🍚", 12.50, 8.90, 1.0, "Arroz de grano largo, ideal para acompañar cualquier comida."),
    ("ABA", "Frijol negro 1 kg", "🫘", 14.00, 9.80, 1.0, "Frijol negro seleccionado, cosecha nacional."),
    ("ABA", "Aceite vegetal 1 L", "🫒", 24.90, 18.20, 0.92, "Aceite vegetal 100 % puro para freír y cocinar."),
    ("ABA", "Pasta spaghetti 400 g", "🍝", 6.50, 4.10, 0.4, "Pasta de sémola de trigo, cocción en 9 minutos."),
    ("ABA", "Harina de maíz 2 lb", "🌽", 9.75, 6.50, 0.9, "Harina de maíz nixtamalizado para tortillas y tamales."),
    ("ABA", "Sal yodada 1 kg", "🧂", 4.50, 2.60, 1.0, "Sal de mesa yodada y fluorada."),
    ("BEB", "Agua pura 600 ml", "💧", 4.00, 2.10, 0.6, "Agua purificada por ósmosis inversa."),
    ("BEB", "Gaseosa cola 2 L", "🥤", 15.50, 10.80, 2.1, "Bebida carbonatada sabor cola, tamaño familiar."),
    ("BEB", "Jugo de naranja 1 L", "🧃", 13.25, 8.90, 1.05, "Jugo de naranja sin azúcar añadida."),
    ("BEB", "Bebida energizante 473 ml", "⚡", 12.00, 7.80, 0.5, "Bebida energizante con cafeína y vitaminas B."),
    ("BEB", "Cerveza artesanal 355 ml", "🍺", 14.00, 9.20, 0.4, "Cerveza artesanal tipo ale, elaborada en Guatemala."),
    ("BEB", "Té frío de limón 500 ml", "🍋", 8.50, 5.40, 0.5, "Té negro con limón, listo para tomar."),
    ("LAC", "Leche entera 1 L", "🥛", 11.50, 8.10, 1.03, "Leche entera pasteurizada y homogeneizada."),
    ("LAC", "Queso fresco 1 lb", "🧀", 28.00, 19.50, 0.45, "Queso fresco artesanal de Quetzaltenango."),
    ("LAC", "Yogur de fresa 1 kg", "🍓", 22.75, 15.60, 1.0, "Yogur bebible con trozos de fresa."),
    ("LAC", "Mantequilla 250 g", "🧈", 18.50, 12.70, 0.25, "Mantequilla con sal, cremosa y untable."),
    ("LAC", "Crema 500 ml", "🍶", 16.90, 11.40, 0.5, "Crema pura de leche para acompañar frijoles y plátanos."),
    ("LAC", "Huevos 30 unidades", "🥚", 42.00, 31.50, 1.8, "Cartón de 30 huevos blancos grado A."),
    ("PAN", "Pan de molde blanco", "🍞", 17.50, 11.80, 0.6, "Pan de caja suave, 20 rebanadas."),
    ("PAN", "Pan francés 10 unidades", "🥖", 10.00, 6.20, 0.5, "Pan francés horneado cada mañana."),
    ("PAN", "Croissant de mantequilla 4 unidades", "🥐", 22.00, 14.30, 0.3, "Croissants hojaldrados elaborados con mantequilla."),
    ("PAN", "Pastel de chocolate", "🎂", 95.00, 58.00, 1.2, "Pastel de chocolate para 10 porciones."),
    ("PAN", "Galletas de avena", "🍪", 12.50, 7.90, 0.3, "Galletas de avena y pasas, paquete de 12."),
    ("PAN", "Tortillas de harina 10 unidades", "🫓", 14.50, 9.40, 0.45, "Tortillas de harina de trigo, ideales para burritos."),
    ("CAR", "Pechuga de pollo 1 lb", "🍗", 21.90, 15.80, 0.45, "Pechuga de pollo fresca sin hueso."),
    ("CAR", "Carne molida de res 1 lb", "🥩", 32.50, 24.10, 0.45, "Carne molida de res 90 % magra."),
    ("CAR", "Chorizo parrillero 6 unidades", "🌭", 29.75, 20.40, 0.5, "Chorizo de cerdo especial para asar."),
    ("CAR", "Tocino ahumado 250 g", "🥓", 26.50, 18.30, 0.25, "Tocino de cerdo ahumado con leña."),
    ("CAR", "Filete de tilapia 1 lb", "🐟", 38.00, 27.20, 0.45, "Filete de tilapia fresco, sin espinas."),
    ("CAR", "Camarón mediano 1 lb", "🦐", 69.00, 49.50, 0.45, "Camarón del Pacífico, limpio y congelado."),
    ("FYV", "Aguacate Hass unidad", "🥑", 6.50, 3.80, 0.25, "Aguacate Hass en su punto."),
    ("FYV", "Banano libra", "🍌", 3.50, 1.90, 0.45, "Banano nacional maduro."),
    ("FYV", "Tomate libra", "🍅", 5.25, 3.10, 0.45, "Tomate manzano fresco."),
    ("FYV", "Manzana roja libra", "🍎", 9.90, 6.40, 0.45, "Manzana roja importada, dulce y crujiente."),
    ("FYV", "Papa libra", "🥔", 4.75, 2.70, 0.45, "Papa blanca para cocer, freír u hornear."),
    ("FYV", "Brócoli unidad", "🥦", 8.25, 4.90, 0.4, "Brócoli fresco de Chimaltenango."),
    ("SNK", "Chocolate con leche 100 g", "🍫", 14.50, 9.10, 0.1, "Tableta de chocolate con leche."),
    ("SNK", "Papalinas clásicas 150 g", "🍟", 11.00, 6.80, 0.15, "Papas fritas en hojuelas con sal."),
    ("SNK", "Palomitas para microondas 3 unidades", "🍿", 16.25, 10.20, 0.3, "Palomitas de maíz con mantequilla."),
    ("SNK", "Dulces surtidos 500 g", "🍬", 19.90, 12.60, 0.5, "Bolsa de caramelos surtidos."),
    ("SNK", "Maní salado 200 g", "🥜", 10.50, 6.70, 0.2, "Maní tostado y salado."),
    ("SNK", "Helado de vainilla 1 L", "🍦", 34.00, 22.80, 0.6, "Helado cremoso sabor vainilla."),
    ("LIM", "Detergente en polvo 1 kg", "🧺", 27.50, 18.90, 1.0, "Detergente para ropa blanca y de color."),
    ("LIM", "Cloro 1 galón", "🫧", 18.75, 11.90, 3.8, "Blanqueador y desinfectante a base de cloro."),
    ("LIM", "Lavaplatos líquido 750 ml", "🧽", 15.90, 10.20, 0.8, "Lavaplatos concentrado aroma limón."),
    ("LIM", "Papel higiénico 12 rollos", "🧻", 48.00, 34.50, 1.2, "Papel higiénico doble hoja."),
    ("LIM", "Desinfectante multiusos 1 L", "🧴", 21.25, 13.80, 1.0, "Elimina el 99.9 % de bacterias."),
    ("LIM", "Bolsas para basura 20 unidades", "🗑️", 13.50, 8.40, 0.3, "Bolsas negras resistentes de 30 galones."),
    ("CPE", "Jabón de tocador 3 unidades", "🧼", 15.00, 9.70, 0.33, "Jabón humectante con aloe vera."),
    ("CPE", "Pasta dental 100 ml", "🪥", 13.75, 8.60, 0.13, "Pasta dental con flúor, protección total."),
    ("CPE", "Champú 400 ml", "🚿", 29.90, 19.80, 0.42, "Champú para todo tipo de cabello."),
    ("CPE", "Desodorante 150 ml", "🌿", 24.50, 16.10, 0.15, "Desodorante en aerosol, 48 horas."),
    ("CPE", "Toallas húmedas 80 unidades", "👶", 22.00, 14.20, 0.4, "Toallas húmedas hipoalergénicas para bebé."),
    ("CPE", "Rastrillos desechables 5 unidades", "🪒", 26.75, 17.30, 0.1, "Rastrillos de 3 hojas con banda lubricante."),
    ("DES", "Café molido de Antigua 454 g", "☕", 54.00, 36.50, 0.454, "Café 100 % arábica de Antigua Guatemala, tueste medio."),
    ("DES", "Cereal de maíz 500 g", "🥣", 31.50, 21.40, 0.5, "Hojuelas de maíz tostadas fortificadas."),
    ("DES", "Avena en hojuelas 400 g", "🌾", 11.25, 7.10, 0.4, "Avena integral en hojuelas."),
    ("DES", "Miel de abeja 500 g", "🍯", 38.50, 26.80, 0.5, "Miel de abeja pura de Huehuetenango."),
    ("DES", "Mermelada de fresa 400 g", "🫙", 19.75, 12.90, 0.4, "Mermelada de fresa natural."),
    ("DES", "Mezcla para panqueques 500 g", "🥞", 17.25, 11.30, 0.5, "Solo agregue agua o leche."),
]


def codigo_producto(indice):
    return f"QM-{indice + 1:04d}"


def ean13(indice):
    """EAN-13 válido con prefijo GS1 de Guatemala (740)."""
    base = f"740{1400:04d}{indice + 1:05d}"
    suma = sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(base))
    return base + str((10 - suma % 10) % 10)


NOMBRES = ["Ana", "Luis", "María", "José", "Carmen", "Carlos", "Lucía", "Jorge", "Sofía", "Miguel",
           "Andrea", "Fernando", "Gabriela", "Ricardo", "Valeria", "Javier", "Daniela", "Roberto",
           "Paola", "Héctor", "Mónica", "Alejandro", "Isabel", "Diego", "Rosa", "Francisco", "Elena",
           "Mario", "Claudia", "Sergio"]
APELLIDOS = ["López", "García", "Pérez", "Hernández", "Morales", "Ramírez", "Castillo", "Méndez",
             "Juárez", "Rodríguez", "Gómez", "Cruz", "Reyes", "Ortiz", "Flores", "Santos", "Chávez",
             "Mejía", "Aguilar", "Vásquez", "Martínez", "Rosales", "Cifuentes", "Barrios"]
EMPRESAS = ["Restaurante El Fogón", "Hotel Casa Maya", "Cafetería La Ceiba", "Colegio Monte Verde",
            "Tienda Doña Tere", "Comedor Los Volcanes", "Catering Sabores de Guate", "Abarrotería El Progreso",
            "Taquería El Güero", "Hostal Lago Azul", "Pupusería La Bendición", "Club Deportivo Aurora",
            "Clínica Santa Lucía", "Panadería La Espiga", "Distribuidora Tres Hermanos", "Oficinas Grupo Cenit",
            "Cafetería Universitaria", "Hotel Real del Puerto", "Minisúper La Esquina", "Banquetes Doña Chepita"]

# país: [(ciudad, departamento/estado como lo nombra Odoo, código postal)]
CIUDADES = {
    "gt": [("Ciudad de Guatemala", "Guatemala", "01001"), ("Mixco", "Guatemala", "01057"),
           ("Antigua Guatemala", "Sacatepéquez", "03001"), ("Quetzaltenango", "Quetzaltenango", "09001"),
           ("Escuintla", "Escuintla", "05001"), ("Cobán", "Alta Verapaz", "16001")],
    "mx": [("Ciudad de México", "Ciudad de México", "06000"), ("Guadalajara", "Jalisco", "44100"),
           ("Monterrey", "Nuevo León", "64000"), ("Tapachula", "Chiapas", "30700")],
    "sv": [("San Salvador", "San Salvador", "01101"), ("Santa Ana", "Santa Ana", "02201"),
           ("San Miguel", "San Miguel", "03301")],
}
CALLES = ["Avenida Reforma", "Calzada Aguilar Batres", "Boulevard Los Próceres", "Calle Real",
          "Avenida Las Américas", "Avenida Juárez", "Calle del Comercio", "Paseo Escalón"]
TELEFONO = {"gt": "+502 {} {}", "mx": "+52 55 {} {}", "sv": "+503 {} {}"}

ETIQUETAS_CLIENTE = ["Cliente frecuente", "Cliente nuevo", "Mayorista", "Minorista"]


def _slug(texto):
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return "".join(c for c in texto.lower() if c.isalnum() or c in ". ").replace(" ", ".")


def clientes(cantidad_personas=60, cantidad_empresas=20):
    """Lista determinista de clientes (personas y empresas) en GT, MX y SV."""
    rnd = random.Random(14)
    paises = ["gt"] * 5 + ["mx"] * 3 + ["sv"] * 2
    resultado = []
    usados = set()
    for i in range(cantidad_personas + cantidad_empresas):
        es_empresa = i >= cantidad_personas
        if es_empresa:
            nombre = EMPRESAS[i - cantidad_personas]
            correo = f"compras@{_slug(nombre).replace('.', '')}.example.com"
        else:
            while True:
                nombre = f"{rnd.choice(NOMBRES)} {rnd.choice(APELLIDOS)} {rnd.choice(APELLIDOS)}"
                if nombre not in usados:
                    break
            usados.add(nombre)
            partes = nombre.split()
            correo = f"{_slug(partes[0])}.{_slug(partes[1])}{i + 1}@example.com"
        pais = rnd.choice(paises)
        ciudad, estado, cp = rnd.choice(CIUDADES[pais])
        etiqueta = rnd.choice(["Mayorista", "Cliente frecuente"]) if es_empresa else rnd.choice(["Cliente frecuente", "Cliente nuevo", "Minorista"])
        resultado.append({
            "codigo": f"C{i + 1:03d}",
            "nombre": nombre,
            "empresa": es_empresa,
            "correo": correo,
            "telefono": TELEFONO[pais].format(rnd.randint(2000, 7999), rnd.randint(1000, 9999)),
            "calle": f"{rnd.choice(CALLES)} {rnd.randint(1, 40)}-{rnd.randint(10, 99)}",
            "ciudad": ciudad,
            "estado": estado,
            "cp": cp,
            "pais": pais,
            "etiqueta": etiqueta,
        })
    return resultado


# ---------------------------------------------------------------------------
# Materiales de operación (no se venden; las sucursales los compran y consumen)
# ---------------------------------------------------------------------------

# código: (nombre de subcategoría, color de fondo de la imagen, código de proveedor)
CATEGORIAS_MATERIAL = {
    "EMP": ("Empaque y despacho", "#FCE9D2", "P11"),
    "OFI": ("Caja y oficina", "#E4E9F2", "P12"),
    "LIN": ("Limpieza institucional", "#D6F2EF", "P08"),
    "EQU": ("Equipo y mantenimiento", "#E9E4D8", "P13"),
    "UNI": ("Uniformes y seguridad", "#F9E0E0", "P14"),
}

# (subcategoría, nombre, emoji de la imagen, costo Q, peso kg)
MATERIALES = [
    ("EMP", "Bolsa biodegradable mediana paquete 1000", "🛍️", 285.00, 8.0),
    ("EMP", "Bolsa de papel kraft paquete 500", "🛍️", 340.00, 12.0),
    ("EMP", "Caja de cartón corrugado paquete 25", "📦", 210.00, 15.0),
    ("EMP", "Cinta de embalaje transparente 6 rollos", "📦", 96.00, 1.2),
    ("EMP", "Film plástico para alimentos 300 m", "🧻", 145.00, 2.0),
    ("EMP", "Bandeja de duroport para carnes 500 unidades", "🍱", 260.00, 3.0),
    ("EMP", "Etiquetas para precios rollo 1000", "🏷️", 38.00, 0.3),
    ("EMP", "Etiquetas de código de barras rollo 2000", "🏷️", 75.00, 0.5),
    ("EMP", "Bolsa para hielo paquete 500", "🧊", 120.00, 2.0),
    ("EMP", "Malla para frutas rollo", "🍊", 88.00, 1.0),
    ("EMP", "Charola de cartón para huevos 100 unidades", "🥚", 150.00, 4.0),
    ("EMP", "Sello de seguridad para bolsas 1000 unidades", "🔒", 64.00, 0.4),
    ("OFI", "Rollo de papel térmico 80 mm caja 50", "🧾", 375.00, 10.0),
    ("OFI", "Papel bond carta resma 500 hojas", "📄", 42.00, 2.5),
    ("OFI", "Tóner para impresora láser", "🖨️", 650.00, 1.0),
    ("OFI", "Bolígrafos azules caja 50", "🖊️", 85.00, 0.6),
    ("OFI", "Folder manila carta caja 100", "📁", 95.00, 3.0),
    ("OFI", "Archivador de palanca", "📂", 32.00, 1.0),
    ("OFI", "Engrapadora de escritorio", "📎", 58.00, 0.4),
    ("OFI", "Calculadora de escritorio", "🧮", 120.00, 0.3),
    ("OFI", "Marcadores permanentes caja 12", "🖍️", 66.00, 0.3),
    ("OFI", "Bolsa para depósito bancario 100 unidades", "💰", 110.00, 0.8),
    ("OFI", "Libro de actas 300 folios", "📒", 75.00, 1.2),
    ("OFI", "Detector de billetes falsos", "💵", 450.00, 0.5),
    ("LIN", "Desinfectante industrial 5 galones", "🧴", 380.00, 20.0),
    ("LIN", "Jabón líquido para manos 1 galón", "🧼", 95.00, 4.0),
    ("LIN", "Papel toalla industrial 6 rollos", "🧻", 210.00, 6.0),
    ("LIN", "Papel higiénico jumbo 12 rollos", "🧻", 260.00, 8.0),
    ("LIN", "Bolsa para basura industrial 100 unidades", "🗑️", 175.00, 5.0),
    ("LIN", "Trapeador industrial", "🧹", 68.00, 1.2),
    ("LIN", "Escoba de cerdas duras", "🧹", 45.00, 0.8),
    ("LIN", "Cubeta con exprimidor", "🪣", 230.00, 3.0),
    ("LIN", "Guantes de nitrilo caja 100", "🧤", 85.00, 0.6),
    ("LIN", "Atomizador 1 L", "🫧", 18.00, 0.15),
    ("LIN", "Limpiavidrios 1 galón", "🪟", 72.00, 4.0),
    ("LIN", "Desengrasante para cocina 1 galón", "🍳", 110.00, 4.0),
    ("EQU", "Gas refrigerante R-404A cilindro", "❄️", 1450.00, 11.0),
    ("EQU", "Termómetro digital para refrigeradores", "🌡️", 95.00, 0.1),
    ("EQU", "Foco LED 18 W paquete 10", "💡", 280.00, 1.0),
    ("EQU", "Batería para báscula", "🔋", 65.00, 0.2),
    ("EQU", "Báscula digital 30 kg", "⚖️", 1250.00, 5.0),
    ("EQU", "Carretilla de carga", "🛒", 980.00, 18.0),
    ("EQU", "Canasta plástica para compras", "🧺", 45.00, 0.6),
    ("EQU", "Carrito de supermercado", "🛒", 1650.00, 20.0),
    ("EQU", "Lector de código de barras", "📟", 890.00, 0.4),
    ("EQU", "Extintor PQS 10 lb", "🧯", 420.00, 7.0),
    ("EQU", "Extensión eléctrica 10 m", "🔌", 110.00, 1.2),
    ("EQU", "Kit de herramientas de mantenimiento", "🧰", 760.00, 6.0),
    ("UNI", "Camisa polo con logo", "👕", 95.00, 0.3),
    ("UNI", "Delantal de cocina", "🥼", 62.00, 0.2),
    ("UNI", "Gorra con logo", "🧢", 48.00, 0.1),
    ("UNI", "Redecilla para cabello 100 unidades", "🧢", 55.00, 0.2),
    ("UNI", "Botas de seguridad", "🥾", 420.00, 1.5),
    ("UNI", "Chaleco reflectivo", "🦺", 45.00, 0.2),
    ("UNI", "Guantes de carga", "🧤", 35.00, 0.15),
    ("UNI", "Faja lumbar", "🦺", 110.00, 0.4),
    ("UNI", "Gafete de identificación 100 unidades", "🪪", 180.00, 0.5),
    ("UNI", "Botiquín de primeros auxilios", "⛑️", 350.00, 2.0),
    ("UNI", "Mascarilla desechable caja 50", "😷", 40.00, 0.3),
    ("UNI", "Señal de piso mojado", "🚧", 85.00, 1.5),
]


def codigo_material(indice):
    return f"MAT-{indice + 1:04d}"


# ---------------------------------------------------------------------------
# Recursos humanos
# ---------------------------------------------------------------------------

# código: nombre. ADM reutiliza el departamento "Administration" que crea Odoo.
DEPARTAMENTOS = {
    "ADM": "Administración",
    "VEN": "Ventas",
    "COM": "Compras",
    "LOG": "Logística e Inventario",
    "RRH": "Recursos Humanos",
}

# código: (nombre del cargo, departamento, plazas por sucursal GT/MX/SV)
CARGOS = {
    "GER": ("Gerente de Sucursal", "ADM", (1, 1, 1)),
    "CAJ": ("Cajero(a)", "VEN", (3, 3, 3)),
    "ASV": ("Asesor(a) de Ventas", "VEN", (4, 2, 2)),
    "CMP": ("Comprador(a)", "COM", (2, 1, 1)),
    "BOD": ("Bodeguero(a)", "LOG", (4, 2, 2)),
    "ARH": ("Analista de Recursos Humanos", "RRH", (2, 1, 0)),
}

NOMBRES_F = ["Ana", "María", "Carmen", "Lucía", "Sofía", "Andrea", "Gabriela", "Valeria", "Daniela",
             "Paola", "Mónica", "Isabel", "Rosa", "Elena", "Claudia", "Fernanda", "Karla", "Silvia"]
NOMBRES_M = ["Luis", "José", "Carlos", "Jorge", "Miguel", "Fernando", "Ricardo", "Javier", "Roberto",
             "Héctor", "Alejandro", "Diego", "Francisco", "Mario", "Sergio", "Óscar", "Pablo", "Raúl"]


def _identificacion(rnd, pais, nombre, apellidos):
    if pais == "gt":  # DPI
        return f"{rnd.randint(1000, 3999)} {rnd.randint(10000, 99999)} {rnd.randint(101, 2299):04d}"
    if pais == "mx":  # CURP simplificada
        return f"{_slug(apellidos[:2]).upper()}{_slug(nombre[0]).upper()}{rnd.randint(700101, 991231)}H{rnd.randint(10, 99)}"
    return f"0{rnd.randint(1000000, 9999999)}-{rnd.randint(0, 9)}"  # DUI


def empleados():
    """Lista determinista de 35 empleados repartidos por sucursal según CARGOS."""
    rnd = random.Random(35)
    resultado, usados = [], set()
    for codigo_cargo, (_cargo, departamento, plazas) in CARGOS.items():
        for sucursal, cantidad in zip(("GT", "MX", "SV"), plazas):
            for _ in range(cantidad):
                genero = rnd.choice(["female", "male"])
                while True:
                    nombre = rnd.choice(NOMBRES_F if genero == "female" else NOMBRES_M)
                    apellidos = f"{rnd.choice(APELLIDOS)} {rnd.choice(APELLIDOS)}"
                    if (nombre, apellidos) not in usados:
                        break
                usados.add((nombre, apellidos))
                numero = len(resultado) + 1
                pais = sucursal.lower()
                resultado.append({
                    "codigo": f"E{numero:03d}",
                    "nombre": f"{nombre} {apellidos}",
                    "genero": genero,
                    "cargo": codigo_cargo,
                    "departamento": departamento,
                    "sucursal": sucursal,
                    "correo": f"{_slug(nombre)}.{_slug(apellidos.split()[0])}{numero}@quetzalmart.com",
                    "movil": TELEFONO[pais].format(rnd.randint(3000, 5999), rnd.randint(1000, 9999)),
                    "identificacion": _identificacion(rnd, pais, nombre, apellidos),
                    "nacimiento": f"{rnd.randint(1975, 2004)}-{rnd.randint(1, 12):02d}-{rnd.randint(1, 28):02d}",
                    "estado_civil": rnd.choice(["single", "single", "married", "married", "cohabitant", "divorced"]),
                })
    return resultado


# ---------------------------------------------------------------------------
# Gestor documental
# ---------------------------------------------------------------------------

# Empresas de outsourcing: código: (razón social, país, ciudad, dirección, servicio, cuota mensual Q, sucursal, inicio)
OUTSOURCING = {
    "S01": ("Seguridad Integral Centinela, S.A.", "gt", "Ciudad de Guatemala", "Avenida Bolívar 31-50, Zona 3",
            "seguridad y vigilancia de instalaciones", 18500.00, "GT", "2026-01-01"),
    "S02": ("Limpieza Profesional Brillo, S.A. de C.V.", "sv", "San Salvador", "Calle Arce 1215, Centro",
            "limpieza y desinfección de áreas de venta y bodega", 6200.00, "SV", "2026-02-01"),
    "S03": ("Transportes Rápidos del Sur, S.A. de C.V.", "mx", "Tapachula", "Carretera Costera Km 4.5",
            "transporte y distribución de mercadería entre sucursales", 24000.00, "MX", "2026-03-01"),
    "S04": ("Maya Tech Soporte Informático, S.A.", "gt", "Ciudad de Guatemala", "Diagonal 6 12-42, Zona 10",
            "soporte técnico de puntos de venta, red y sistema ERP", 9800.00, "GT", "2026-04-01"),
    "S05": ("Pérez & Ruiz Contadores Asociados, S.A.", "gt", "Ciudad de Guatemala", "5a. Avenida 5-55, Zona 14",
            "contabilidad, planilla y asesoría fiscal", 7500.00, "GT", "2026-01-15"),
}

# Compras cuya factura del proveedor se digitaliza en el gestor documental.
COMPRAS_CON_FACTURA_DIGITAL = ["compra_001", "compra_002", "compra_003", "compra_004", "compra_005"]

# Cargos cuyo primer empleado (sede Guatemala) tiene su contrato en el gestor documental, y salario mensual Q.
CONTRATOS_LABORALES = {"GER": 14500.00, "CAJ": 4200.00, "ASV": 4800.00, "CMP": 6500.00, "BOD": 4000.00}
