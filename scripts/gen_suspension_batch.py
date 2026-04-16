import json
import unicodedata
import re

with open('output/refacciones_suspension_batch.json', encoding='utf-8') as f:
    data = json.load(f)

products = data['productos']
seen_skus = {}
used_handles = set()

def slugify(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text).strip('-')
    return text[:80]

def unique_handle(base, used):
    h = base
    i = 2
    while h in used:
        h = f"{base}-{i}"
        i += 1
    used.add(h)
    return h

def clean_title(t):
    t = re.sub(r'\s*&\s*$', '', t.strip())
    fixes = [('Bmw', 'BMW'), (' Vw ', ' VW '), ('Mercedes', 'Mercedes'),
             ('Mini ', 'Mini '), ('Porsche', 'Porsche'), ('Audi', 'Audi')]
    for old, new in fixes:
        t = t.replace(old, new)
    return t[:255]

def get_tags(titulo, descripcion):
    desc_clean = re.sub(
        r'ESPECIALISTAS EN.*?(?:VOLKSWAGEN|VOLVO|MINI COOPER).*?(\n|$)',
        '', descripcion, flags=re.IGNORECASE | re.DOTALL
    )
    text = (titulo + ' ' + desc_clean[:400]).upper()
    found = []
    mappings = [
        ('BMW', 'BMW'), ('MERCEDES', 'Mercedes-Benz'), ('AUDI', 'Audi'),
        ('VOLKSWAGEN', 'Volkswagen'), (' VW ', 'Volkswagen'),
        ('PORSCHE', 'Porsche'), ('VOLVO', 'Volvo'), ('MINI', 'Mini'),
        ('LAND ROVER', 'Land Rover'), ('JAGUAR', 'Jaguar'),
        ('SPRINTER', 'Mercedes-Benz'), ('CRAFTER', 'Volkswagen'),
        ('RANGE ROVER', 'Land Rover'), ('DISCOVERY', 'Land Rover'),
        ('CAYENNE', 'Porsche'), ('TOUAREG', 'Volkswagen'),
    ]
    for keyword, brand in mappings:
        if keyword in text and brand not in found:
            found.append(brand)
    return ', '.join(found)

def fix_origen(origen):
    if not origen:
        return ''
    o = origen.upper()
    if 'ALEMAN' in o or 'GERMAN' in o or 'IMPORT' in o:
        return 'Importado'
    return origen

def get_pos(titulo):
    t = titulo.lower()
    pos = ''
    if 'delantero' in t or 'delantera' in t or 'front' in t:
        pos = 'delantero'
    elif 'trasero' in t or 'trasera' in t or 'rear' in t:
        pos = 'trasero'
    return pos

def get_lado(titulo):
    t = titulo.lower()
    if 'izquierdo' in t or 'izquierda' in t or 'izq' in t:
        return 'izquierdo'
    if 'derecho' in t or 'derecha' in t or 'der' in t:
        return 'derecho'
    return ''

def get_cat(titulo):
    t = titulo.lower()
    # Air suspension components
    if 'bolsa' in t and 'aire' in t:
        return 'bolsa_aire'
    if 'amortiguador' in t and 'aire' in t:
        return 'amortiguador_aire'
    if 'compresor' in t and 'aire' in t:
        return 'compresor_aire'
    if 'bomba' in t and 'aire' in t and 'suspension' in t:
        return 'compresor_aire'
    if 'bloque' in t and ('valvula' in t or 'aire' in t or 'suspension' in t):
        return 'bloque_valvulas'
    if 'modulo' in t and ('suspension' in t or 'aire' in t):
        return 'modulo_suspension'
    if 'sensor' in t and ('altura' in t or 'nivel' in t or 'suspension' in t):
        return 'sensor_suspension'
    # Shock absorbers
    if 'amortiguador' in t:
        return 'amortiguador'
    # Steering
    if 'cremallera' in t or ('caja' in t and 'direccion' in t):
        return 'cremallera'
    if 'bomba' in t and 'direccion' in t:
        return 'bomba_direccion'
    if 'licuadora' in t or 'electrohidraul' in t or 'electrobomba' in t:
        return 'bomba_direccion'
    if 'bieleta' in t and 'direccion' in t:
        return 'bieleta_interna'
    if 'terminal' in t and ('direccion' in t or 'barra' in t or 'cremallera' in t):
        return 'terminal'
    if 'terminal' in t:
        return 'terminal'
    if 'sello' in t and 'direccion' in t:
        return 'sello_direccion'
    # Control arms
    if 'horquilla' in t:
        return 'horquilla'
    if 'brazo' in t and ('suspension' in t or 'control' in t or 'delantera' in t or 'trasera' in t):
        return 'brazo'
    # Joints / bushings
    if 'rotula' in t or 'rótula' in t:
        return 'rotula'
    if 'buje' in t:
        return 'buje'
    if 'goma' in t and ('barra' in t or 'estabilizadora' in t or 'buje' in t):
        return 'buje'
    if 'silentblock' in t or 'silent block' in t:
        return 'buje'
    if 'barra' in t and 'estabilizadora' in t:
        return 'barra_estabilizadora'
    if 'barra' in t and 'estab' in t:
        return 'barra_estabilizadora'
    if 'bieleta' in t:
        return 'bieleta_estabilizadora'
    # Springs
    if 'muelle' in t or 'resorte' in t or 'espiral' in t:
        return 'muelle'
    # Strut mount / top mount
    if 'copela' in t or ('soporte' in t and ('superior' in t or 'amortiguador' in t)):
        return 'copela'
    if 'soporte' in t and 'suspension' in t:
        return 'soporte_suspension'
    # Alignment
    if 'tornillo' in t and ('camber' in t or 'alineacion' in t or 'suspension' in t):
        return 'tornillo_alineacion'
    if 'tornillo' in t or 'perno' in t:
        return 'tornillo_suspension'
    # Misc
    if 'tope' in t or 'bump stop' in t:
        return 'tope'
    if 'fuelle' in t or 'guardapolvo' in t:
        return 'guardapolvo'
    if 'puntal' in t:
        return 'puntal'
    if 'cojinete' in t or 'rodamiento' in t:
        return 'cojinete'
    if 'eje' in t:
        return 'eje_suspension'
    if 'kit' in t and 'suspension' in t:
        return 'kit_suspension'
    return 'suspension_general'

def get_related(sku, products):
    seen = []
    for p in products:
        if p['sku'] != sku and p['sku'] not in seen:
            seen.append(p['sku'])
    return seen[:5]

resultados = []
cat_counts = {}

for p in products:
    sku = p['sku']
    titulo_raw = p['titulo']
    titulo = clean_title(titulo_raw)
    desc_raw = p['descripcion'] or ''
    marca = p['marca_normalizada'] or ''
    precio = p['precio'] or '0'
    garantia = p['garantia'] or ''
    origen = fix_origen(p['origen'])
    tipo_vehiculo = p['tipo_vehiculo'] or ''
    compatibilidades = p['compatibilidades'] or ''
    numero_parte = p['numero_parte'] or ''
    codigo_oem = p['codigo_oem'] or ''
    fila = p['_fila_original']

    seen_skus.setdefault(sku, 0)
    seen_skus[sku] += 1
    dup_count = seen_skus[sku]

    tags = get_tags(titulo_raw, desc_raw)
    cat = get_cat(titulo_raw)
    cat_counts[cat] = cat_counts.get(cat, 0) + 1

    handle_base = slugify(titulo)
    if not handle_base:
        handle_base = slugify(sku)
    handle = unique_handle(handle_base, used_handles)

    if compatibilidades:
        caract_compat = compatibilidades[:500]
    elif titulo:
        caract_compat = f"Compatible con {titulo}. Verifica compatibilidad exacta con tu número de VIN antes de comprar."
    else:
        caract_compat = ''

    tv = tipo_vehiculo
    if 'Auto' in tv or 'Carro' in tv or 'Camioneta' in tv:
        caract_tipo = 'Carro/Camioneta'
    elif tv:
        caract_tipo = tv
    else:
        caract_tipo = ''

    oem_match = re.search(r'(?:OEM|N[uú]mero OEM)[:\s]+([A-Z0-9]{8,})', desc_raw, re.IGNORECASE)
    if oem_match and not codigo_oem:
        codigo_oem = oem_match.group(1)

    garantia_str = re.sub(r'Garant[íi]a del vendedor:\s*', '', garantia).strip() if garantia else ''
    gar_txt = f"{garantia_str} de garantía del vendedor" if garantia_str and garantia_str != 'Sin garantía' else 'calidad garantizada'
    gar_faq = f"{garantia_str} de garantía del vendedor." if garantia_str and garantia_str != 'Sin garantía' else 'Este producto no incluye garantía del fabricante.'

    abc = ("Para garantizar que recibas la pieza correcta para tu vehículo, necesitamos el número de serie (VIN) "
           "de tu auto antes de procesar el pedido. Esto evita errores, tiempos perdidos y devoluciones innecesarias. "
           "Escríbenos y con gusto confirmamos compatibilidad.")
    extras = []
    if numero_parte: extras.append(f"número de parte {numero_parte}")
    if codigo_oem: extras.append(f"código OEM {codigo_oem}")
    if extras:
        abc += f" También puedes verificar con el {' o '.join(extras)}."

    envio = "Tenemos stock disponible para entrega inmediata. Enviamos el mismo dia de tu pago a Ciudad de Mexico y a todo el pais via DHL o FedEx."
    dev = ("Aceptamos devoluciones dentro de los 30 días posteriores a la entrega, sin importar el motivo. "
           "Para que tu devolución proceda, la pieza debe estar sin uso, sin instalar y en su empaque original.\n\n"
           "Asegura el ajuste perfecto: Una vez realizada tu compra, un asesor te contactará brevemente para validar "
           "la compatibilidad con tu número VIN y garantizar que recibas exactamente lo que tu auto necesita.\n\n"
           "Consulta nuestra politica completa aquí")

    pos = get_pos(titulo_raw)
    lado = get_lado(titulo_raw)
    pos_txt = f" {pos}" if pos else ''
    lado_txt = f" {lado}" if lado else ''
    par_txt = 'par de ' if 'par' in titulo.lower() else ''

    # ---- CONTENT TEMPLATES ----
    if cat == 'amortiguador':
        sec_desc = (
            f"Amortiguador{pos_txt}{lado_txt} para {titulo}. "
            f"Controla el rebote y la compresión de la suspensión para mantener el contacto del neumático con el pavimento, "
            f"garantizando estabilidad, comodidad y seguridad.\n\n"
            f"Instalación directa como reemplazo del amortiguador original. "
            f"{'Se incluye el par.' if par_txt else 'Se vende como unidad individual — verificar si necesita par.'}\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": f"¿Para qué vehículos es compatible este amortiguador?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": f"Se incluye el {par_txt}amortiguador{pos_txt}{lado_txt} como se indica en el título."},
            {"pregunta": "¿Cómo sé si mis amortiguadores están fallando?",
             "respuesta": "Síntomas: rebote excesivo al pasar topes, inestabilidad en curvas, desgaste disparejo de neumáticos, vehículo que se hunde al frenar o acelerar, ruido de golpe en la suspensión."},
            {"pregunta": "¿Se deben cambiar en par?",
             "respuesta": "Se recomienda cambiar ambos amortiguadores del mismo eje (delantero o trasero) al mismo tiempo para mantener el comportamiento simétrico del vehículo."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'amortiguador_aire':
        sec_desc = (
            f"Amortiguador de suspensión neumática (aire){pos_txt}{lado_txt} para {titulo}. "
            f"Conjunto completo que integra la bolsa de aire y el amortiguador hidráulico en una sola unidad para el sistema de suspensión neumática del vehículo.\n\n"
            f"Reemplazo directo del conjunto original. Compatible con el sistema de nivelación electrónica del vehículo.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": f"Se incluye el {par_txt}amortiguador neumático completo{pos_txt}{lado_txt}."},
            {"pregunta": "¿Cómo sé si mi amortiguador de aire está fallando?",
             "respuesta": "Síntomas: vehículo caído de un lado, compresor que trabaja constantemente, luz de suspensión en el tablero, altura irregular del vehículo."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'bolsa_aire':
        sec_desc = (
            f"Bolsa de aire (fuelle neumático){pos_txt}{lado_txt} para suspensión de {titulo}. "
            f"Componente flexible del sistema de suspensión neumática que soporta el peso del vehículo mediante presión de aire y amortigua las irregularidades del camino.\n\n"
            f"Reemplazo directo de la bolsa original. Instalación directa.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": f"Se incluye el {par_txt}fuelle/bolsa de aire{pos_txt}{lado_txt} como se indica en el título."},
            {"pregunta": "¿Cómo sé si mi bolsa de aire está fallando?",
             "respuesta": "Síntomas: vehículo caído de un lado o de la parte trasera, compresor de suspensión que trabaja constantemente, altura irregular o ruido de aire escapando."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'compresor_aire':
        sec_desc = (
            f"Compresor de suspensión neumática para {titulo}. "
            f"Genera y mantiene la presión de aire en el sistema de suspensión neumática para nivelar la altura del vehículo automáticamente.\n\n"
            f"Reemplazo directo del compresor original. Instalación directa.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
            {"pregunta": "¿Cómo sé si mi compresor está fallando?",
             "respuesta": "Síntomas: compresor que no activa, vehículo que no sube de altura, luz de suspensión encendida, ruido excesivo del compresor sin lograr nivelar."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'bloque_valvulas':
        sec_desc = (
            f"Bloque de válvulas de la suspensión neumática para {titulo}. "
            f"Distribuye el aire del compresor a cada bolsa/amortiguador de suspensión para mantener la nivelación automática del vehículo.\n\n"
            f"Reemplazo directo del componente original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
            {"pregunta": "¿Cómo sé si el bloque de válvulas está fallando?",
             "respuesta": "Síntomas: vehículo que no nivela correctamente, uno o varios lados caídos, compresor que trabaja sin efecto, fuga de aire."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'terminal':
        sec_desc = (
            f"Terminal de dirección (barra de conexión exterior){lado_txt} para {titulo}. "
            f"Conecta la cremallera de dirección con la mangueta de la rueda, transmitiendo el movimiento de dirección y permitiendo el giro de las ruedas.\n\n"
            f"Reemplazo directo. Se recomienda alineación tras la instalación.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
            {"pregunta": "¿Cómo sé si mi terminal de dirección está fallando?",
             "respuesta": "Síntomas: juego en la dirección, vibración del volante, desgaste irregular de neumáticos en el lado afectado, ruido de golpe al girar."},
            {"pregunta": "¿Se requiere alineación tras la instalación?",
             "respuesta": "Sí, siempre se recomienda hacer una alineación de ruedas después de cambiar terminales o cualquier componente de dirección/suspensión."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'bieleta_interna':
        sec_desc = (
            f"Bieleta interna de dirección para {titulo}. "
            f"Conecta el extremo interior de la cremallera con la barra de dirección, transmitiendo la fuerza de giro desde la cremallera hacia las ruedas.\n\n"
            f"Reemplazo directo. Se recomienda alineación tras la instalación.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
            {"pregunta": "¿Cómo sé si la bieleta interna está fallando?",
             "respuesta": "Síntomas: juego en la dirección, golpe o traqueteo al girar el volante, desgaste disparejo de neumáticos, imprecisión en la dirección."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'bieleta_estabilizadora':
        sec_desc = (
            f"Bieleta de barra estabilizadora para {titulo}. "
            f"Conecta la barra estabilizadora al brazo de suspensión o al amortiguador, transfiriendo fuerzas laterales para reducir el balanceo en curvas.\n\n"
            f"Reemplazo directo. Instalación directa.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
            {"pregunta": "¿Cómo sé si mi bieleta está fallando?",
             "respuesta": "Síntomas: ruido de golpe o traqueteo al pasar topes o en curvas, balanceo excesivo del vehículo."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'horquilla':
        pos_h = pos_txt if pos_txt else ''
        sup_inf = ' superior' if 'superior' in titulo.lower() else ' inferior' if 'inferior' in titulo.lower() else ''
        sec_desc = (
            f"Horquilla de suspensión{sup_inf}{pos_h}{lado_txt} para {titulo}. "
            f"Brazo de control que conecta la mangueta de la rueda a la carrocería, guiando el movimiento vertical de la rueda y manteniendo la geometría de suspensión.\n\n"
            f"Reemplazo directo. Se recomienda alineación tras la instalación.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
            {"pregunta": "¿Cómo sé si mi horquilla está fallando?",
             "respuesta": "Síntomas: ruido de golpe en la suspensión, desgaste desigual de llantas, vehículo que jala hacia un lado, sensación de holgura al maniobrar."},
            {"pregunta": "¿Se requiere alineación?",
             "respuesta": "Sí, siempre se requiere alineación de ruedas después de cambiar brazos de suspensión u horquillas."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'brazo':
        sup_inf = ' superior' if 'superior' in titulo.lower() else ' inferior' if 'inferior' in titulo.lower() else ''
        sec_desc = (
            f"Brazo de control de suspensión{sup_inf}{pos_txt}{lado_txt} para {titulo}. "
            f"Controla el movimiento vertical de la rueda mientras mantiene la geometría de suspensión correcta.\n\n"
            f"Reemplazo directo. Se recomienda alineación tras la instalación.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
            {"pregunta": "¿Cómo sé si el brazo de suspensión está fallando?",
             "respuesta": "Síntomas: ruido de golpe, desgaste irregular de neumáticos, vehículo que jala, holgura en la suspensión."},
            {"pregunta": "¿Requiere alineación?", "respuesta": "Sí, siempre."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'rotula':
        pos_r = pos_txt if pos_txt else ''
        sup_inf = ' superior' if 'superior' in titulo.lower() else ' inferior' if 'inferior' in titulo.lower() else ''
        sec_desc = (
            f"Rótula de suspensión{sup_inf}{pos_r}{lado_txt} para {titulo}. "
            f"Articulación esférica que conecta el brazo de suspensión con la mangueta, permitiendo el giro y movimiento vertical de la rueda simultáneamente.\n\n"
            f"Reemplazo directo. Se recomienda alineación tras la instalación.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
            {"pregunta": "¿Cómo sé si mi rótula está fallando?",
             "respuesta": "Síntomas: traqueteo o chasquido al maniobrar, vibración del volante, desgaste irregular de neumáticos, juego excesivo en la suspensión. En casos graves, puede provocar pérdida de control."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'buje':
        sec_desc = (
            f"Buje de suspensión{pos_txt}{lado_txt} para {titulo}. "
            f"Elemento de hule o poliuretano que absorbe vibraciones y permite el movimiento articulado controlado de los brazos y barras de suspensión.\n\n"
            f"Reemplazo directo del buje original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": f"Se incluye el {par_txt}buje indicado en el título."},
            {"pregunta": "¿Cómo sé si mis bujes están fallando?",
             "respuesta": "Síntomas: ruido de golpe al pasar topes, sensación de holgura en la suspensión, desgaste prematuro de neumáticos, comportamiento impreciso de la dirección."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'barra_estabilizadora':
        sec_desc = (
            f"Barra estabilizadora{pos_txt} para {titulo}. "
            f"Barra de torsión que conecta los dos lados de la suspensión para reducir el balanceo lateral del vehículo en curvas, mejorando la estabilidad.\n\n"
            f"Reemplazo directo de la barra original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
            {"pregunta": "¿Cómo sé si la barra estabilizadora está fallando?",
             "respuesta": "Síntomas: balanceo excesivo en curvas, ruido metálico de golpe lateral, comportamiento errático en maniobras rápidas."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'bomba_direccion':
        sec_desc = (
            f"Bomba de dirección hidráulica para {titulo}. "
            f"Genera la presión hidráulica que asiste el giro del volante reduciendo el esfuerzo necesario para maniobrar, especialmente a bajas velocidades.\n\n"
            f"Reemplazo directo de la bomba original. Se recomienda purgar el sistema hidráulico tras la instalación.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
            {"pregunta": "¿Cómo sé si mi bomba de dirección está fallando?",
             "respuesta": "Síntomas: dirección muy pesada especialmente en frío o a bajas RPM, ruido de quejido al girar el volante, fuga de líquido de dirección, nivel bajo en el depósito."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'cremallera':
        sec_desc = (
            f"Cremallera de dirección para {titulo}. "
            f"Convierte el movimiento giratorio del volante en movimiento lineal para dirigir las ruedas delanteras. "
            f"Sistema de dirección asistida{'hidráulica' if 'hidraul' in titulo.lower() else ' eléctrica' if 'electr' in titulo.lower() else ''}.\n\n"
            f"Reemplazo directo. Se requiere alineación tras la instalación.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
            {"pregunta": "¿Cómo sé si mi cremallera está fallando?",
             "respuesta": "Síntomas: juego excesivo en el volante, dirección que jala hacia un lado, ruido de golpe al girar, fuga de líquido de dirección."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'muelle':
        sec_desc = (
            f"Resorte/muelle de suspensión{pos_txt}{lado_txt} para {titulo}. "
            f"Soporta el peso del vehículo y absorbe las irregularidades del camino, trabajando en conjunto con el amortiguador.\n\n"
            f"Reemplazo directo del resorte original. Se recomienda cambiar en par por eje.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
            {"pregunta": "¿Cómo sé si mis resortes están fallando?",
             "respuesta": "Síntomas: vehículo más bajo de lo normal en un lado, rebote excesivo, ruido metálico al pasar topes, desgaste irregular de neumáticos."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'tornillo_alineacion':
        sec_desc = (
            f"Tornillo/perno de alineación (camber/toe) para {titulo}. "
            f"Permite ajustar los ángulos de alineación (camber, cáster o toe) de la suspensión para corregir la geometría de las ruedas.\n\n"
            f"Instalación directa como reemplazo del tornillo original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
            {"pregunta": "¿Se requiere alineación tras instalar?",
             "respuesta": "Sí, siempre se requiere una alineación de ruedas después de instalar tornillos de alineación."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'copela':
        sec_desc = (
            f"Copela (soporte superior de amortiguador) para {titulo}. "
            f"Soporte que fija el extremo superior del amortiguador a la carrocería, absorbiendo las cargas verticales y aislando las vibraciones.\n\n"
            f"Reemplazo directo de la copela original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
            {"pregunta": "¿Cómo sé si mi copela está fallando?",
             "respuesta": "Síntomas: ruido de golpe o traqueteo desde la parte superior de la suspensión, vibración en el volante, desgaste irregular de neumáticos."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    else:  # general: tornillo_suspension, guardapolvo, tope, puntal, cojinete, eje_suspension, modulo, sensor, sello, kit, suspension_general
        nombres = {
            'tornillo_suspension': 'tornillo/perno de suspensión',
            'guardapolvo': 'guardapolvo/fuelle de suspensión',
            'tope': 'tope de suspensión (bump stop)',
            'puntal': 'puntal de suspensión',
            'cojinete': 'cojinete/rodamiento de rueda',
            'eje_suspension': 'componente de eje de suspensión',
            'modulo_suspension': 'módulo de control de suspensión',
            'sensor_suspension': 'sensor de altura de suspensión',
            'sello_direccion': 'sello del sistema de dirección',
            'kit_suspension': 'kit de suspensión',
            'soporte_suspension': 'soporte de suspensión',
        }
        nombre = nombres.get(cat, 'componente de suspensión/dirección')
        sec_desc = (
            f"{titulo}. {nombre.capitalize()} para vehículos europeos.\n\n"
            f"Reemplazo directo del componente original. Instalación directa.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye la pieza indicada en el título."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    # Body HTML
    desc_html = ''.join(f'<p>{par}</p>' for par in sec_desc.split('\n\n') if par.strip())
    faq_html = ''.join(f'<h3>{f["pregunta"]}</h3><p>{f["respuesta"]}</p>' for f in faq)
    dev_html = dev.replace('\n\n', '</p><p>')
    body = (f"<h2>Descripcion</h2>{desc_html}"
            f"<h2>Antes de Comprar</h2><p>{abc}</p>"
            f"<h2>Envio</h2><p>{envio}</p>"
            f"<h2>Politica de Devolucion</h2><p>{dev_html}</p>"
            f"<h2>Preguntas Frecuentes</h2>{faq_html}")

    seo_title = f"{titulo[:48]} | Embler"
    if len(seo_title) > 60:
        seo_title = f"{titulo[:40]}... | Embler"
    seo_desc_str = f"{titulo[:100]}. Marca {marca}. Envío inmediato a todo México."
    if len(seo_desc_str) > 155:
        seo_desc_str = seo_desc_str[:152] + '...'
    img_alt = f"{titulo[:80]} {marca}"[:125]

    flags = []
    if not compatibilidades:
        flags.append("[VERIFICAR] Compatibilidad inferida del título — confirmar modelos y años exactos.")
    if not numero_parte and not codigo_oem:
        flags.append("[BUSCAR] Número de parte o código OEM faltantes.")
    if dup_count > 1:
        flags.append(f"[REVISAR] Listing {dup_count} del SKU {sku} — evaluar si se consolida con el listing principal.")
    flags.append("[INCLUIR] Peso y dimensiones para cálculo de envío.")
    flags.append("[INCLUIR] Fotografías del producto.")

    try:
        precio_fmt = f"{float(precio):.2f}"
    except Exception:
        precio_fmt = str(precio)

    resultados.append({
        "_fila_original": fila,
        "caract_marca": marca,
        "caract_origen": origen,
        "caract_tipo_vehiculo": caract_tipo,
        "caract_compatibilidad": caract_compat,
        "seccion_descripcion": sec_desc,
        "seccion_antes_de_comprar": abc,
        "seccion_envio": envio,
        "seccion_devoluciones": dev,
        "seccion_faq": faq,
        "productos_relacionados": get_related(sku, products),
        "shopify_handle": handle,
        "shopify_title": titulo,
        "shopify_body_html": body,
        "shopify_product_category": "Vehicles & Parts > Vehicle Parts & Accessories",
        "shopify_type": "Suspensión",
        "shopify_tags": tags,
        "shopify_published": "TRUE",
        "shopify_option1_name": "Title",
        "shopify_option1_value": "Default Title",
        "shopify_variant_sku": sku,
        "shopify_variant_price": precio_fmt,
        "shopify_variant_compare_price": "",
        "shopify_variant_weight": "",
        "shopify_variant_weight_unit": "kg",
        "shopify_image_src": "",
        "shopify_image_alt_text": img_alt,
        "shopify_seo_title": seo_title,
        "shopify_seo_description": seo_desc_str,
        "shopify_status": "draft",
        "revision_humana": "\n".join(flags)
    })

with open('output/refacciones_suspension_batch_result.json', 'w', encoding='utf-8') as f:
    json.dump({"resultados": resultados}, f, ensure_ascii=False, indent=2)

print(f"Generados: {len(resultados)} productos")
print(f"SKUs únicos: {len(seen_skus)}, con duplicados: {sum(1 for v in seen_skus.values() if v > 1)}")
print()
print("Top categorías:")
from collections import Counter
for cat, n in sorted(cat_counts.items(), key=lambda x: -x[1])[:20]:
    print(f"  {cat}: {n}")
print()
print("Tags:")
tag_counts = Counter()
for r in resultados:
    for tag in r['shopify_tags'].split(', '):
        if tag: tag_counts[tag] += 1
for tag, n in tag_counts.most_common():
    print(f"  {tag}: {n}")
