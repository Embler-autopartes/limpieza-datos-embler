import json
import unicodedata
import re

with open('output/accesorios_batch.json', encoding='utf-8') as f:
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
        ('TOUAREG', 'Volkswagen'), ('CAYENNE', 'Porsche'),
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

def get_cat(titulo):
    t = titulo.lower()
    # Herramientas
    if 'herramienta' in t or 'sincronizaci' in t or 'sincronizar' in t or 'sincronizador' in t:
        return 'herramienta_sincro'
    # Carrocería exterior
    if 'cantonera' in t or ('moldura' in t and ('arco' in t or 'salpicadera' in t or 'rejilla' in t)):
        return 'cantonera'
    if 'moldura' in t or 'parrilla' in t:
        return 'moldura'
    # Suspensión
    if 'amortiguador' in t and 'aire' in t:
        return 'amortiguador_aire'
    if 'amortiguador' in t and ('banda' in t or 'tensor' in t):
        return 'tensor_banda'
    if 'amortiguador' in t:
        return 'amortiguador'
    if 'brazo' in t and 'suspension' in t:
        return 'brazo_suspension'
    if 'bloque' in t and ('valvula' in t or 'aire' in t or 'suspension' in t):
        return 'bloque_valvulas_aire'
    if 'horquilla' in t:
        return 'brazo_suspension'
    if 'goma' in t and ('buje' in t or 'barra' in t):
        return 'buje'
    if 'buje' in t:
        return 'buje'
    if 'muelle' in t and 'suspension' in t:
        return 'muelle'
    if 'caja' in t and 'direccion' in t or 'cremallera' in t and 'direccion' in t:
        return 'caja_direccion'
    # Frenos
    if 'balata' in t or 'pastilla' in t:
        return 'balata'
    if 'zapata' in t:
        return 'zapata'
    if 'disco' in t and 'freno' in t:
        return 'disco_freno'
    if 'sensor' in t and 'abs' in t:
        return 'sensor_abs'
    if 'actuador' in t and 'freno' in t:
        return 'actuador_freno'
    if 'seguro' in t and 'zapata' in t:
        return 'accesorio_freno'
    # Transmisión
    if 'cardan' in t or 'barra cardan' in t or 'flecha cardan' in t:
        return 'cardan'
    if 'eje' in t and ('transmision' in t or 'transm' in t):
        return 'eje_transmision'
    if 'eje' in t and 'direccion' in t:
        return 'eje_direccion'
    # Sistema eléctrico
    if 'sensor' in t and ('estacionamiento' in t or 'reversa' in t or 'parking' in t):
        return 'sensor_parking'
    if 'sensor' in t and ('nivel' in t or 'combustible' in t):
        return 'sensor'
    if 'marcha' in t or 'arranque' in t:
        return 'arranque'
    if 'cable' in t and 'bateria' in t:
        return 'cable_bateria'
    if 'rele' in t or 'relay' in t or 'releevador' in t or 'relevador' in t:
        return 'rele'
    if 'conector' in t:
        return 'conector'
    if 'calavera' in t or ('placa' in t and ('circuito' in t or 'luz' in t)):
        return 'iluminacion'
    if 'modulo' in t and ('control' in t or 'faro' in t or 'estacionamiento' in t):
        return 'modulo'
    if 'bujia' in t or 'bují' in t:
        return 'bujia'
    if 'bobina' in t:
        return 'bobina'
    # Motor
    if 'polea' in t and 'alternador' in t:
        return 'polea_alternador'
    if 'polea' in t:
        return 'polea'
    if 'tensor' in t and ('banda' in t or 'accesorio' in t or 'supercargador' in t):
        return 'tensor'
    if 'tensor' in t:
        return 'tensor'
    if 'radiador' in t:
        return 'radiador'
    if 'bomba' in t and 'agua' in t:
        return 'bomba_agua'
    if 'manguera' in t and ('radiador' in t or 'agua' in t or 'turbo' in t):
        return 'manguera'
    if 'kit' in t and ('cadena' in t or 'distribucion' in t):
        return 'kit_cadena'
    if 'filtro' in t:
        return 'filtro'
    if 'junta' in t or 'empaque' in t:
        return 'junta'
    if 'valvula' in t or 'solenoide' in t:
        return 'valvula'
    if 'metal' in t and ('bancada' in t or 'centro' in t):
        return 'metal_motor'
    if 'liga' in t and ('enfriador' in t or 'radiador' in t):
        return 'liga_enfriador'
    if 'enfriador' in t:
        return 'enfriador'
    if 'bomba' in t:
        return 'bomba'
    # Químicos
    if 'anticongelante' in t:
        return 'anticongelante'
    if 'aerosol' in t or 'lubricante' in t or 'limpiador' in t:
        return 'quimico'
    # Carrocería
    if 'chapa' in t or 'cerradura' in t or 'manija' in t:
        return 'cerradura'
    if 'rejilla' in t and 'faro' in t:
        return 'rejilla_faro'
    # Accesorios
    if 'porta vasos' in t or 'portavasos' in t:
        return 'accesorio_interior'
    if 'soporte' in t and 'gato' in t:
        return 'soporte_gato'
    if 'caja' in t and 'disco' in t:
        return 'accesorio_interior'
    if 'placa' in t and ('montaje' in t or 'recuperador' in t):
        return 'accesorio_exterior'
    return 'general'

def get_shopify_type(cat):
    map = {
        'herramienta_sincro': 'Herramientas',
        'cantonera': 'Carrocería',
        'moldura': 'Carrocería',
        'amortiguador_aire': 'Suspensión',
        'tensor_banda': 'Motor',
        'amortiguador': 'Suspensión',
        'brazo_suspension': 'Suspensión',
        'bloque_valvulas_aire': 'Suspensión',
        'buje': 'Suspensión',
        'muelle': 'Suspensión',
        'caja_direccion': 'Dirección',
        'balata': 'Frenos',
        'zapata': 'Frenos',
        'disco_freno': 'Frenos',
        'sensor_abs': 'Frenos',
        'actuador_freno': 'Frenos',
        'accesorio_freno': 'Frenos',
        'cardan': 'Transmisión',
        'eje_transmision': 'Transmisión',
        'eje_direccion': 'Transmisión',
        'sensor_parking': 'Sistema Eléctrico',
        'sensor': 'Sistema Eléctrico',
        'arranque': 'Sistema Eléctrico',
        'cable_bateria': 'Sistema Eléctrico',
        'rele': 'Sistema Eléctrico',
        'conector': 'Sistema Eléctrico',
        'iluminacion': 'Sistema Eléctrico',
        'modulo': 'Sistema Eléctrico',
        'bujia': 'Sistema Eléctrico',
        'bobina': 'Sistema Eléctrico',
        'polea_alternador': 'Motor',
        'polea': 'Motor',
        'tensor': 'Motor',
        'radiador': 'Motor',
        'bomba_agua': 'Motor',
        'manguera': 'Motor',
        'kit_cadena': 'Motor',
        'filtro': 'Filtros',
        'junta': 'Motor',
        'valvula': 'Motor',
        'metal_motor': 'Motor',
        'liga_enfriador': 'Motor',
        'enfriador': 'Motor',
        'bomba': 'Motor',
        'anticongelante': 'Motor',
        'quimico': 'Motor',
        'cerradura': 'Carrocería',
        'rejilla_faro': 'Carrocería',
        'accesorio_interior': 'Accesorios',
        'soporte_gato': 'Herramientas',
        'accesorio_exterior': 'Carrocería',
        'general': 'Accesorios',
    }
    return map.get(cat, 'Accesorios')

def get_related(sku, products):
    seen = []
    for p in products:
        if p['sku'] != sku and p['sku'] not in seen:
            seen.append(p['sku'])
    return seen[:5]

resultados = []
cat_counts = {}
type_counts = {}

for p in products:
    sku = p['sku']
    titulo_raw = p['titulo']
    titulo = clean_title(titulo_raw)
    desc_raw = p['descripcion'] or ''
    marca = p['marca_normalizada'] or ''
    subcat = p['subcategoria'] or ''
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
    shopify_type = get_shopify_type(cat)
    cat_counts[cat] = cat_counts.get(cat, 0) + 1
    type_counts[shopify_type] = type_counts.get(shopify_type, 0) + 1

    handle_base = slugify(titulo)
    if not handle_base:
        handle_base = slugify(sku)
    handle = unique_handle(handle_base, used_handles)

    # Compatibilidad
    if compatibilidades:
        caract_compat = compatibilidades[:500]
    elif titulo:
        caract_compat = f"Compatible con {titulo}. Verifica compatibilidad exacta con tu número de VIN antes de comprar."
    else:
        caract_compat = ''

    # Tipo vehiculo
    tv = tipo_vehiculo
    if 'Auto' in tv or 'Carro' in tv or 'Camioneta' in tv:
        caract_tipo = 'Carro/Camioneta'
    elif tv:
        caract_tipo = tv
    else:
        caract_tipo = ''

    # OEM from description
    oem_match = re.search(r'(?:OEM|N[uú]mero OEM)[:\s]+([A-Z0-9]{8,})', desc_raw, re.IGNORECASE)
    if oem_match and not codigo_oem:
        codigo_oem = oem_match.group(1)

    garantia_str = re.sub(r'Garant[íi]a del vendedor:\s*', '', garantia).strip() if garantia else ''
    gar_txt = f"{garantia_str} de garantía del vendedor" if garantia_str and garantia_str != 'Sin garantía' else 'calidad garantizada'
    gar_faq = f"{garantia_str} de garantía del vendedor." if garantia_str and garantia_str != 'Sin garantía' else 'Este producto no incluye garantía del fabricante.'

    # Antes de comprar
    abc = ("Para garantizar que recibas la pieza correcta para tu vehículo, necesitamos el número de serie (VIN) "
           "de tu auto antes de procesar el pedido. Esto evita errores, tiempos perdidos y devoluciones innecesarias. "
           "Escríbenos y con gusto confirmamos compatibilidad.")
    if cat in ('anticongelante', 'quimico'):
        abc = ("Verifica en el listado la compatibilidad con tu vehículo antes de comprar. "
               "Si tienes dudas, escríbenos y con gusto te orientamos.")
    elif cat == 'accesorio_interior':
        abc = ("Verifica que el modelo de tu vehículo corresponda con el indicado en el título. "
               "Escríbenos si tienes dudas de compatibilidad.")
    extras = []
    if numero_parte:
        extras.append(f"número de parte {numero_parte}")
    if codigo_oem:
        extras.append(f"código OEM {codigo_oem}")
    if extras and cat not in ('anticongelante', 'quimico', 'accesorio_interior'):
        abc += f" También puedes verificar con el {' o '.join(extras)}."

    # Envio
    envio = "Tenemos stock disponible para entrega inmediata. Enviamos el mismo dia de tu pago a Ciudad de Mexico y a todo el pais via DHL o FedEx."

    # Devoluciones
    dev = ("Aceptamos devoluciones dentro de los 30 días posteriores a la entrega, sin importar el motivo. "
           "Para que tu devolución proceda, la pieza debe estar sin uso, sin instalar y en su empaque original.\n\n"
           "Asegura el ajuste perfecto: Una vez realizada tu compra, un asesor te contactará brevemente para validar "
           "la compatibilidad con tu número VIN y garantizar que recibas exactamente lo que tu auto necesita.\n\n"
           "Consulta nuestra politica completa aquí")

    # --- Content by category ---
    if cat == 'herramienta_sincro':
        kit_match = re.search(r'(\d+)\s*pz', titulo.lower())
        pzs = f" ({kit_match.group(1)} piezas)" if kit_match else ''
        sec_desc = (
            f"Herramienta de sincronización de motor{pzs} para {titulo}. "
            f"Fija los árboles de levas y el cigüeñal en el punto de encendido correcto durante el reemplazo de la cadena o correa de distribución.\n\n"
            f"Indispensable para realizar el cambio de distribución correctamente sin riesgo de daño al motor. "
            f"Diseñada específicamente para los motores indicados.\n\n"
            f"Marca {marca}, con {gar_txt}."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos aplica esta herramienta?",
             "respuesta": f"Aplica para {titulo}. Confirma la familia de motor con tu número de VIN antes de comprar."},
            {"pregunta": "¿Para qué se usa esta herramienta?",
             "respuesta": "Se usa para fijar el motor en el punto muerto superior (TDC) durante el reemplazo de la cadena o correa de distribución, asegurando la sincronización correcta de válvulas y pistones."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": f"Se incluye el juego de herramientas de sincronización{pzs} como se indica en el título."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat in ('cantonera', 'moldura'):
        pos_match = re.search(r'(delantera|trasera|lateral|superior|inferior)', titulo.lower())
        pos = pos_match.group(1).capitalize() if pos_match else ''
        sec_desc = (
            f"{titulo}. Pieza de carrocería exterior{' — ' + pos if pos else ''} que protege y da acabado al arco del guardafango o moldura indicada.\n\n"
            f"Instalación directa como reemplazo del componente original. Puede requerir perforación de referencia según el modelo.\n\n"
            f"Fabricada por {marca} con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos aplica?",
             "respuesta": f"Aplica para {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye la pieza indicada en el título como unidad individual."},
            {"pregunta": "¿Requiere pintura o preparación?",
             "respuesta": "Las piezas de carrocería generalmente se entregan en color base/negro y pueden requerir pintura para igualar el color original del vehículo."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'amortiguador_aire':
        pos_match = re.search(r'(delantero|trasero|delantera|trasera)', titulo.lower())
        pos = pos_match.group(1) if pos_match else ''
        sec_desc = (
            f"Amortiguador de suspensión neumática (aire){' ' + pos if pos else ''} para {titulo}. "
            f"Reemplaza la bolsa de aire original que soporta y amortigua la suspensión hidro-neumática del vehículo.\n\n"
            f"Instalación directa como reemplazo del componente original. Compatible con el sistema de nivelación electrónico del vehículo.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": f"Se incluye {'el par de amortiguadores' if 'par' in titulo.lower() else 'el amortiguador'} de aire como se indica en el título."},
            {"pregunta": "¿Cómo sé si mi amortiguador de aire está fallando?",
             "respuesta": "Síntomas: vehículo caído de un lado, luz de suspensión encendida en el tablero, ruido al activarse el compresor de aire frecuentemente, viaje incómodo."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'amortiguador':
        pos_match = re.search(r'(delantero|trasero|delantera|trasera)', titulo.lower())
        pos = pos_match.group(1) if pos_match else ''
        lado_match = re.search(r'(izquierdo|derecho|izq|der)', titulo.lower())
        lado = lado_match.group(1) if lado_match else ''
        sec_desc = (
            f"Amortiguador de suspensión{' ' + pos if pos else ''}{' ' + lado if lado else ''} para {titulo}. "
            f"Controla el rebote y la compresión de la suspensión para mantener el contacto del neumático con el pavimento y garantizar estabilidad.\n\n"
            f"Instalación directa como reemplazo del amortiguador original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": f"Se incluye {'el par de amortiguadores' if 'par' in titulo.lower() else 'el amortiguador individual'} como se indica en el título."},
            {"pregunta": "¿Cómo sé si mi amortiguador está fallando?",
             "respuesta": "Síntomas: rebote excesivo al pasar topes, inestabilidad en curvas, desgaste disparejo de neumáticos, vehículo se hunde al frenar o acelerar."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'brazo_suspension':
        sec_desc = (
            f"{titulo}. Brazo de control o horquilla de suspensión que conecta la mangueta a la carrocería, "
            f"permitiendo el movimiento vertical de la rueda mientras mantiene la geometría de suspensión.\n\n"
            f"Reemplazo directo del componente original. Incluye rotula y/o buje según especificación del título.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye el brazo de suspensión indicado en el título."},
            {"pregunta": "¿Cómo sé si mi brazo de suspensión está fallando?",
             "respuesta": "Síntomas: ruido de golpe o tronido en la suspensión, desgaste irregular de llantas, vehículo jala hacia un lado, sensación de holgura en la dirección."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'bloque_valvulas_aire':
        sec_desc = (
            f"Bloque de válvulas de la suspensión neumática para {titulo}. "
            f"Distribuye el aire del compresor a cada bolsa de suspensión para mantener la altura de nivelación correcta.\n\n"
            f"Instalación directa como reemplazo del componente original. Compatible con el sistema de control de altura electrónico.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye el bloque de válvulas completo."},
            {"pregunta": "¿Cómo sé si mi bloque de válvulas está fallando?",
             "respuesta": "Síntomas: vehículo caído de uno o varios lados, luz de suspensión encendida, compresor de aire que trabaja constantemente sin lograr nivelar el vehículo."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'buje':
        sec_desc = (
            f"{titulo}. Buje de hule que absorbe vibraciones y permite el movimiento articulado de la barra estabilizadora o brazo de suspensión.\n\n"
            f"Reemplazo directo del buje original. Instalación directa.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": f"Se incluye {'el par de bujes' if 'par' in titulo.lower() else 'el buje'} como se indica en el título."},
            {"pregunta": "¿Cómo sé si mis bujes están fallando?",
             "respuesta": "Síntomas: ruido de golpe al pasar topes o hacer curvas, sensación de holgura en la suspensión, desgaste prematuro de neumáticos."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'caja_direccion':
        sec_desc = (
            f"Caja de dirección (cremallera) para {titulo}. "
            f"Convierte el movimiento giratorio del volante en movimiento lineal para mover las ruedas delanteras.\n\n"
            f"Reemplazo directo de la caja de dirección original. Puede ser eléctrica o hidráulica según el modelo.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye la caja de dirección completa."},
            {"pregunta": "¿Cómo sé si mi cremallera está fallando?",
             "respuesta": "Síntomas: juego excesivo en el volante, ruido al girar, fuga de aceite de dirección, dirección dura o que jala hacia un lado."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat in ('balata', 'zapata'):
        tipo = 'balatas (pastillas)' if cat == 'balata' else 'zapatas'
        pos_match = re.search(r'(delantero|trasero|delantera|trasera|estacionamiento|mano)', titulo.lower())
        pos = pos_match.group(1) if pos_match else ''
        sec_desc = (
            f"{'Balatas' if cat == 'balata' else 'Zapatas'} de freno{' ' + pos if pos else ''} para {titulo}. "
            f"{'Frena el disco mediante fricción de la pastilla contra el disco de freno.' if cat == 'balata' else 'Sistema de freno de tambor — la zapata presiona el interior del tambor para detener el vehículo.'}\n\n"
            f"Reemplazo directo del componente original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos son compatibles?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": f"Se incluye el juego de {tipo} {'delantero' if 'delant' in titulo.lower() else 'trasero' if 'trase' in titulo.lower() else ''} como se indica en el título."},
            {"pregunta": "¿Cuándo se deben cambiar?",
             "respuesta": "Se recomienda inspección cada 20,000-30,000 km. Cambio cuando el grosor de la pastilla sea menor a 3mm o al escuchar chirrido metálico al frenar."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'disco_freno':
        pos_match = re.search(r'(delantero|trasero|delantera|trasera)', titulo.lower())
        pos = pos_match.group(1) if pos_match else ''
        sec_desc = (
            f"Disco de freno{' ' + pos if pos else ''} para {titulo}. "
            f"El disco sobre el que actúan las pastillas de freno para detener el vehículo mediante fricción.\n\n"
            f"Reemplazo directo del disco original. Instalación directa.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": f"Se incluye {'el par de discos' if 'par' in titulo.lower() else 'el disco individual'} como se indica en el título."},
            {"pregunta": "¿Cuándo se deben cambiar los discos?",
             "respuesta": "Cambiar cuando el espesor esté por debajo del mínimo marcado en el disco, presenten rayaduras profundas, deformación (vibración al frenar), o al cambiar las balatas si están muy desgastados."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'sensor_parking':
        sec_desc = (
            f"Sensor de estacionamiento (parking sensor / PDC) para {titulo}. "
            f"Detecta obstáculos al estacionarse y emite señal sonora o visual al sistema de asistencia de estacionamiento del vehículo.\n\n"
            f"Reemplazo directo del sensor original. Instalación directa en el parachoque.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye el sensor de estacionamiento individual. Verifica en el listado si incluye más de uno."},
            {"pregunta": "¿Cómo sé si mi sensor de estacionamiento está fallando?",
             "respuesta": "Síntomas: beep constante al manejar sin obstáculos, sensor que no responde, mensaje de error PDC en el tablero."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'cardan':
        sec_desc = (
            f"Flecha/barra cardan para {titulo}. "
            f"Transmite el torque del diferencial a las ruedas traseras o entre ejes en vehículos de tracción total, compensando los cambios de ángulo de la suspensión.\n\n"
            f"Reemplazo directo del componente original. Incluye crucetas o juntas homocinéticas según especificación.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye la flecha/barra cardan completa como se indica en el título."},
            {"pregunta": "¿Cómo sé si mi cardan está fallando?",
             "respuesta": "Síntomas: vibración a velocidades específicas, ruido de traqueteo al acelerar o desacelerar, golpe al meter reversa."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'eje_transmision':
        sec_desc = (
            f"Eje de transmisión (semieje / flecha de velocidad constante) para {titulo}. "
            f"Transmite el torque del diferencial a la rueda delantera o trasera manteniendo el ángulo variable de la suspensión mediante juntas homocinéticas.\n\n"
            f"Reemplazo directo del eje original. Incluye juntas homocinéticas y guardapolvos.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye el eje de transmisión completo con juntas homocinéticas."},
            {"pregunta": "¿Cómo sé si mi eje de transmisión está fallando?",
             "respuesta": "Síntomas: traqueteo o clic al girar en curvas (especialmente abierto el volante), vibración al acelerar, grasa en el interior del arco de la llanta (guardapolvo roto)."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'anticongelante':
        qty_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:litros?|galon|lts?)', titulo.lower())
        qty = qty_match.group(0) if qty_match else ''
        color_match = re.search(r'(azul|rojo|verde|amarillo)', titulo.lower())
        color = color_match.group(1) if color_match else ''
        sec_desc = (
            f"Anticongelante{' ' + color if color else ''} para {titulo}. "
            f"{'Presentación de ' + qty + '.' if qty else ''} "
            f"Refrigerante de motor que protege contra la corrosión, la congelación y el sobrecalentamiento.\n\n"
            f"Compatible con sistemas de refrigeración de vehículos europeos. "
            f"Verifica en el listado la presentación exacta (concentrado o listo para usar).\n\n"
            f"Marca {marca}."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Verifica el color y tipo recomendado por el fabricante de tu vehículo antes de comprar."},
            {"pregunta": "¿Qué presentación incluye?",
             "respuesta": f"{'Se incluyen ' + qty + ' de anticongelante.' if qty else 'Verifica la cantidad exacta en el listado.'}"},
            {"pregunta": "¿Se mezcla con agua?",
             "respuesta": "Si es concentrado, mezclar 50/50 con agua destilada. Si es listo para usar (ready to use), aplicar directamente. Revisa la etiqueta del producto."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]
        abc = ("Verifica en el listado la compatibilidad con tu vehículo antes de comprar. "
               "Si tienes dudas sobre el tipo de anticongelante correcto, escríbenos.")

    elif cat in ('radiador', 'bomba_agua', 'manguera'):
        tipo_map = {'radiador': 'radiador de enfriamiento', 'bomba_agua': 'bomba de agua', 'manguera': 'manguera de radiador'}
        tipo_txt = tipo_map.get(cat, 'componente de enfriamiento')
        sec_desc = (
            f"{titulo.capitalize()}. {tipo_txt.capitalize()} para el sistema de refrigeración del motor.\n\n"
            f"Reemplazo directo del componente original. Instalación directa sin modificaciones.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": f"Se incluye el {tipo_txt} como se indica en el título."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'polea':
        sec_desc = (
            f"Polea de reenvío/guía de la correa de accesorios para {titulo}. "
            f"Guía y mantiene la tensión correcta de la correa del sistema de accesorios.\n\n"
            f"Reemplazo directo del componente original. Instalación directa.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye la polea como unidad individual."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'tensor':
        sec_desc = (
            f"Tensor de correa de accesorios para {titulo}. "
            f"Mantiene la tensión adecuada de la correa del sistema de accesorios para evitar deslizamiento y desgaste prematuro.\n\n"
            f"Reemplazo directo del componente original. Instalación directa.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye el tensor como unidad individual."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'tensor_banda':
        sec_desc = (
            f"Amortiguador/tensor de banda de accesorios para {titulo}. "
            f"Mantiene y amortigua la tensión de la correa de accesorios reduciendo vibraciones.\n\n"
            f"Reemplazo directo del componente original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye el tensor/amortiguador de banda como unidad individual."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'kit_cadena':
        sec_desc = (
            f"Kit de cadena de distribución para {titulo}. "
            f"Incluye todos los componentes necesarios para el reemplazo completo del sistema de distribución por cadena del motor.\n\n"
            f"Kit completo para sustitución del sistema de distribución. Instalar todos los componentes del kit al mismo tiempo.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma familia de motor con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el kit?",
             "respuesta": "Incluye cadena(s), piñones, tensores y guías según se indica en el título. Verifica el contenido exacto en la descripción del listado."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'filtro':
        tipo_filtro = 'de aire' if 'aire' in titulo.lower() else 'de aceite' if 'aceite' in titulo.lower() else 'de combustible' if 'combustible' in titulo.lower() or 'gasolina' in titulo.lower() else ''
        sec_desc = (
            f"Filtro {tipo_filtro} para {titulo}. "
            f"Retiene impurezas que podrían dañar el motor o afectar el rendimiento del vehículo.\n\n"
            f"Reemplazo directo del filtro original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": f"Se incluye el filtro {tipo_filtro} como se indica en el título."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat in ('junta', 'valvula', 'metal_motor', 'liga_enfriador', 'enfriador', 'bomba'):
        sec_desc = (
            f"{titulo}. Componente del sistema de motor para vehículos europeos.\n\n"
            f"Reemplazo directo del componente original. Instalación directa.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye la pieza indicada en el título."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat in ('arranque', 'cable_bateria', 'rele', 'conector', 'modulo', 'bujia', 'bobina', 'iluminacion', 'sensor_abs', 'sensor', 'actuador_freno', 'accesorio_freno'):
        sec_desc = (
            f"{titulo}. Componente del sistema eléctrico para vehículos europeos.\n\n"
            f"Reemplazo directo del componente original. Instalación directa.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye la pieza indicada en el título."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'quimico':
        sec_desc = (
            f"{titulo}. Producto químico automotriz para mantenimiento del vehículo.\n\n"
            f"Usar según las instrucciones del fabricante. Verifica compatibilidad con los materiales de tu vehículo.\n\n"
            f"Marca {marca}."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos aplica?",
             "respuesta": "Producto de uso general automotriz. Verifica la compatibilidad con los materiales de tu vehículo."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye el producto en la presentación indicada en el título."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat in ('cerradura', 'rejilla_faro', 'accesorio_exterior'):
        sec_desc = (
            f"{titulo}. Pieza de carrocería o accesorios exteriores para vehículos europeos.\n\n"
            f"Reemplazo directo del componente original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos aplica?",
             "respuesta": f"Aplica para {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye la pieza indicada en el título."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat in ('accesorio_interior', 'soporte_gato', 'muelle'):
        sec_desc = (
            f"{titulo}. Accesorio o herramienta para vehículos europeos.\n\n"
            f"Marca {marca}."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos aplica?",
             "respuesta": f"Aplica para {titulo}. Confirma compatibilidad con tu modelo antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye la pieza indicada en el título."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    else:  # general
        sec_desc = (
            f"{titulo}. Refacción o accesorio para vehículos europeos.\n\n"
            f"Reemplazo directo del componente original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos aplica?",
             "respuesta": f"Aplica para {titulo}. Confirma con tu número de VIN antes de comprar."},
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

    # SEO
    seo_title = f"{titulo[:48]} | Embler"
    if len(seo_title) > 60:
        seo_title = f"{titulo[:40]}... | Embler"
    seo_desc_str = f"{titulo[:100]}. Marca {marca}. Envío inmediato a todo México."
    if len(seo_desc_str) > 155:
        seo_desc_str = seo_desc_str[:152] + '...'

    img_alt = f"{titulo[:80]} {marca}"[:125]

    # Revision humana
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

    related = get_related(sku, products)

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
        "productos_relacionados": related,
        "shopify_handle": handle,
        "shopify_title": titulo,
        "shopify_body_html": body,
        "shopify_product_category": "Vehicles & Parts > Vehicle Parts & Accessories",
        "shopify_type": shopify_type,
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

with open('output/accesorios_batch_result.json', 'w', encoding='utf-8') as f:
    json.dump({"resultados": resultados}, f, ensure_ascii=False, indent=2)

print(f"Generados: {len(resultados)} productos")
print(f"SKUs únicos: {len(seen_skus)}, con duplicados: {sum(1 for v in seen_skus.values() if v > 1)}")
print()
print("Categorías de producto:")
for cat, n in sorted(cat_counts.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {n}")
print()
print("Shopify types:")
for t, n in sorted(type_counts.items(), key=lambda x: -x[1]):
    print(f"  {t}: {n}")
print()
print("Tags (marcas vehículo):")
from collections import Counter
tag_counts = Counter()
for r in resultados:
    for tag in r['shopify_tags'].split(', '):
        if tag:
            tag_counts[tag] += 1
for tag, n in tag_counts.most_common():
    print(f"  {tag}: {n}")
