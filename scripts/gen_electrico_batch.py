import json
import unicodedata
import re

with open('output/refacciones_electrico_batch.json', encoding='utf-8') as f:
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
             ('Mini ', 'Mini '), ('Porsche', 'Porsche'), ('Ngk', 'NGK'),
             ('Bosch', 'Bosch'), ('Denso', 'Denso'), ('Nippondens', 'Nippondenso')]
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
    if 'buj' in t and ('precalentamiento' in t or 'diesel' in t or 'glow' in t):
        return 'bujia_precalentamiento'
    if 'buj' in t and ('iridio' in t or 'iridium' in t):
        return 'bujia_iridio'
    if 'buj' in t and 'platino' in t:
        return 'bujia_platino'
    if 'buj' in t:
        return 'bujia'
    if 'bobina' in t:
        return 'bobina'
    if 'cable' in t and ('buj' in t or 'encendid' in t):
        return 'cable_encendido'
    if 'solenoide' in t and ('arbol' in t or 'levas' in t or 'vanos' in t or 'vvt' in t or 'valvetronic' in t):
        return 'solenoide_vvt'
    if 'actuador' in t and ('vanos' in t or 'levas' in t or 'arbol' in t):
        return 'solenoide_vvt'
    if 'valvula' in t and ('vanos' in t or 'vvt' in t or 'valvetronic' in t or 'levas' in t or 'solenoide' in t or 'turbo' in t):
        return 'solenoide_vvt'
    if 'solenoide' in t:
        return 'solenoide_vvt'
    if 'polea' in t and 'alternador' in t:
        return 'polea_alternador'
    if 'polea' in t:
        return 'polea'
    if 'tensor' in t and ('supercargador' in t or 'supercharger' in t):
        return 'tensor_supercargador'
    if 'tensor' in t:
        return 'tensor'
    if 'alternador' in t or 'generador' in t:
        return 'alternador'
    if 'marcha' in t or 'arranque' in t or 'starter' in t:
        return 'arranque'
    if 'balastra' in t or 'modulo' in t:
        return 'modulo'
    if 'bateria' in t:
        return 'bateria'
    if 'motor actuador' in t or ('actuador' in t and 'tapa' in t):
        return 'actuador'
    return 'electrico_general'

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
    cat_counts[cat] = cat_counts.get(cat, 0) + 1

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
    extras = []
    if numero_parte:
        extras.append(f"número de parte {numero_parte}")
    if codigo_oem:
        extras.append(f"código OEM {codigo_oem}")
    if extras:
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
    if cat == 'bobina':
        # Count coils in title
        qty_match = re.search(r'^(\d+)\s+bobina', titulo.lower())
        qty = qty_match.group(1) if qty_match else ''
        qty_txt = f"Juego de {qty} bobinas de ignición" if qty else "Bobina de ignición"
        sec_desc = (
            f"{qty_txt} de encendido para {titulo}. "
            f"Genera el pulso de alta tensión que activa la bujía en el momento exacto del ciclo de encendido.\n\n"
            f"Instalación directa como reemplazo del componente original. Sin modificaciones al cableado.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible esta bobina?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": f"{'Se incluye el juego de ' + qty + ' bobinas.' if qty else 'Se incluye una bobina de encendido.'}"},
            {"pregunta": "¿Cómo sé si mi bobina está fallando?",
             "respuesta": "Síntomas comunes: motor que falla (misfire), vibración al ralentí, pérdida de potencia, luz de motor encendida con código P030X."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat in ('bujia', 'bujia_iridio', 'bujia_platino'):
        qty_match = re.search(r'^(?:kit\s+)?(\d+)\s+buj', titulo.lower())
        qty = qty_match.group(1) if qty_match else ''
        tipo_bujia = 'de iridio' if cat == 'bujia_iridio' else 'de platino' if cat == 'bujia_platino' else ''
        qty_txt = f"Juego de {qty} bujías {tipo_bujia}".strip() if qty else f"Bujía {tipo_bujia}".strip()
        beneficio = ("Mayor durabilidad y eficiencia de encendido gracias al electrodo de iridio de alto punto de fusión."
                     if cat == 'bujia_iridio' else
                     "Electrodo de platino para mayor vida útil y rendimiento de encendido estable."
                     if cat == 'bujia_platino' else
                     "Encendido preciso y confiable en cada ciclo de combustión.")
        sec_desc = (
            f"{qty_txt} de encendido para {titulo}. {beneficio}\n\n"
            f"Reemplazo directo de las bujías originales. Instalación directa sin modificaciones.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos son compatibles estas bujías?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": f"{'Se incluye el juego de ' + qty + ' bujías.' if qty else 'Se incluye una bujía.'}"},
            {"pregunta": "¿Cada cuánto se reemplazan las bujías?",
             "respuesta": ("Las bujías de iridio tienen vida útil de hasta 100,000 km en condiciones normales."
                           if cat == 'bujia_iridio' else
                           "Las bujías de platino duran entre 60,000 y 80,000 km en condiciones normales."
                           if cat == 'bujia_platino' else
                           "Se recomienda revisión cada 30,000-40,000 km. Consulta el manual de tu vehículo.")},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'bujia_precalentamiento':
        qty_match = re.search(r'^kit\s+(\d+)\s+buj', titulo.lower())
        qty = qty_match.group(1) if qty_match else ''
        sec_desc = (
            f"{'Juego de ' + qty + ' bujías' if qty else 'Bujías'} de precalentamiento para motor diésel {titulo}. "
            f"Precalienta la cámara de combustión para facilitar el arranque en frío del motor diésel.\n\n"
            f"Reemplazo directo del componente original. Instalación directa.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos son compatibles?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": f"{'Se incluye el juego de ' + qty + ' bujías de precalentamiento.' if qty else 'Se incluye la bujía de precalentamiento.'}"},
            {"pregunta": "¿Cuándo se reemplazan las bujías de precalentamiento?",
             "respuesta": "Se recomienda revisión entre 80,000 y 100,000 km, o cuando el motor tiene dificultades de arranque en frío o la luz de precalentamiento permanece encendida."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'cable_encendido':
        sec_desc = (
            f"Cable de encendido (cables de bujía) para {titulo}. "
            f"Conduce el pulso de alta tensión de la bobina a la bujía con mínima pérdida de señal.\n\n"
            f"Reemplazo directo del cableado original. Instalación sin modificaciones.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos son compatibles?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye el juego de cables de encendido completo."},
            {"pregunta": "¿Cómo sé si mis cables de encendido están fallando?",
             "respuesta": "Síntomas: fallas de encendido (misfire), consumo elevado, pérdida de potencia, chisporroteo visible en el motor de noche."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'solenoide_vvt':
        sistema = 'Valvetronic' if 'valvetronic' in titulo.lower() else 'VVT' if 'vvt' in titulo.lower() else 'VANOS' if 'vanos' in titulo.lower() else 'VVT/VANOS'
        sec_desc = (
            f"Solenoide/válvula de control del sistema de variación de distribución {sistema} para {titulo}. "
            f"Controla el flujo de aceite que ajusta el avance y retardo del árbol de levas según las condiciones de operación del motor.\n\n"
            f"Un solenoide fallido puede generar fallas de encendido, pérdida de potencia o códigos de error P0010-P0015. "
            f"Reemplazo directo del componente original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible este solenoide?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": f"¿Qué hace el sistema {sistema}?",
             "respuesta": f"El sistema {sistema} ajusta dinámicamente el tiempo de distribución del motor para optimizar potencia, torque y eficiencia de combustible según las RPM y carga."},
            {"pregunta": "¿Cómo sé si mi solenoide está fallando?",
             "respuesta": f"Síntomas: luz de motor encendida (códigos P0010, P0011, P0014, P0015), ralentí inestable, pérdida de potencia o ruido de traqueteo al arranque."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'alternador':
        sec_desc = (
            f"Alternador para {titulo}. "
            f"Genera la corriente eléctrica que carga la batería y alimenta todos los sistemas eléctricos del vehículo en marcha.\n\n"
            f"Reemplazo directo del alternador original. Instalación directa sin modificaciones al cableado.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible este alternador?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye el alternador como unidad individual."},
            {"pregunta": "¿Cómo sé si mi alternador está fallando?",
             "respuesta": "Síntomas: luz de batería encendida, luces tenues o parpadeantes, batería que se descarga frecuentemente, accesorios eléctricos con fallas."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'polea_alternador':
        sec_desc = (
            f"Polea de alternador (polea de rueda libre / OAP) para {titulo}. "
            f"Desacopla el alternador de forma momentánea para reducir vibraciones del sistema de accesorios y prolongar la vida útil de la correa.\n\n"
            f"Reemplazo directo de la polea original. Instalación sin modificaciones.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye la polea de alternador como unidad individual."},
            {"pregunta": "¿Cómo sé si mi polea de alternador está fallando?",
             "respuesta": "Síntomas: ruido de chirriado o traqueteo en el área del alternador, desgaste prematuro de la correa de accesorios, vibración del motor en aceleración."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'polea':
        sec_desc = (
            f"Polea de reenvío/guía de la correa de accesorios para {titulo}. "
            f"Guía y mantiene la tensión correcta de la correa del sistema de accesorios (dirección, A/C, alternador).\n\n"
            f"Reemplazo directo del componente original. Instalación directa.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye la polea como unidad individual."},
            {"pregunta": "¿Cómo sé si mi polea está fallando?",
             "respuesta": "Síntomas: ruido al girar el motor, vibración, desgaste lateral de la correa o correa que sale de su recorrido."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'tensor_supercargador':
        sec_desc = (
            f"Tensor de la correa del supercargador para {titulo}. "
            f"Mantiene la tensión correcta de la correa que acciona el compresor de sobrealimentación del motor.\n\n"
            f"Reemplazo directo del componente original. Instalación directa sin modificaciones.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye el tensor como unidad individual."},
            {"pregunta": "¿Cómo sé si mi tensor está fallando?",
             "respuesta": "Síntomas: ruido de chirriado en el área del supercargador, pérdida de presión de sobrealimentación, desgaste prematuro de la correa."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'tensor':
        sec_desc = (
            f"Tensor de correa para {titulo}. "
            f"Mantiene la tensión adecuada de la correa de accesorios o distribución para evitar deslizamiento y desgaste prematuro.\n\n"
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

    elif cat == 'arranque':
        sec_desc = (
            f"Motor de arranque (marcha) para {titulo}. "
            f"Acciona el motor de combustión interna durante el encendido mediante un piñón que engrana con la corona dentada del volante.\n\n"
            f"Reemplazo directo del motor de arranque original. Instalación directa.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye el motor de arranque como unidad completa."},
            {"pregunta": "¿Cómo sé si mi motor de arranque está fallando?",
             "respuesta": "Síntomas: clic al intentar arrancar, motor que gira lento o no gira al girar la llave, arranque intermitente o chirrido al encender."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'modulo':
        sec_desc = (
            f"{titulo}. Módulo o unidad electrónica de control para el sistema eléctrico del vehículo.\n\n"
            f"Reemplazo directo del componente original para {titulo}.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye el módulo/unidad electrónica como se indica en el título."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'bateria':
        sec_desc = (
            f"Batería auxiliar para {titulo}. "
            f"Batería de respaldo del sistema eléctrico de a bordo para vehículos con sistema de arranque-parada (Start/Stop) o sistemas de gestión eléctrica avanzados.\n\n"
            f"Instalación directa como reemplazo del componente original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye la batería auxiliar como unidad individual."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'actuador':
        sec_desc = (
            f"{titulo}. Motor actuador eléctrico para el sistema indicado.\n\n"
            f"Reemplazo directo del componente original. Instalación directa sin modificaciones.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye el motor actuador como unidad individual."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    else:  # electrico_general
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
        "shopify_type": "Sistema Eléctrico",
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

with open('output/refacciones_electrico_batch_result.json', 'w', encoding='utf-8') as f:
    json.dump({"resultados": resultados}, f, ensure_ascii=False, indent=2)

print(f"Generados: {len(resultados)} productos")
print(f"SKUs únicos: {len(seen_skus)}, con duplicados: {sum(1 for v in seen_skus.values() if v > 1)}")
print()
print("Categorías de producto:")
for cat, n in sorted(cat_counts.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {n}")
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
