import json
import unicodedata
import re
from collections import Counter

with open('output/refacciones_transmision_batch.json', encoding='utf-8') as f:
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
    t = re.sub(r'\s*&\s*\.?\s*$', '', t.strip())
    t = t.replace('Bmw', 'BMW').replace(' Vw ', ' VW ').replace('Audi ', 'Audi ')
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
        ('VOLKSWAGEN', 'Volkswagen'), ('VW ', 'Volkswagen'), ('CRAFTER', 'Volkswagen'),
        ('SPRINTER', 'Mercedes-Benz'), ('PORSCHE', 'Porsche'), ('VOLVO', 'Volvo'),
        ('MINI', 'Mini'), ('LAND ROVER', 'Land Rover'), ('JAGUAR', 'Jaguar'),
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
    if any(x in t for x in ['clutch', 'embrague', 'collarin', 'plato', 'disco clutch']):
        return 'clutch'
    if any(x in t for x in ['kit doble embrague', 'doble embrague']):
        return 'doble_embrague'
    if any(x in t for x in ['bomba clutch', 'cilindro maestro', 'cilindro clutch']):
        return 'bomba_clutch'
    if any(x in t for x in ['goma cardan', 'junta goma cardan', 'junta de goma cardan', 'goma card']):
        return 'goma_cardan'
    if any(x in t for x in ['soporte cardan', 'chumacera', 'balero cardan', 'soporte central cardan', 'soporte flecha cardan']):
        return 'soporte_cardan'
    if any(x in t for x in ['engrane', 'servomotor', 'engranes transfer']):
        return 'engrane_transfer'
    if any(x in t for x in ['soporte transmision', 'soporte trasmision', 'soporte caja', 'soporte de caja']):
        return 'soporte_transmision'
    if any(x in t for x in ['soporte transfer']):
        return 'soporte_transfer'
    if any(x in t for x in ['carter', 'cárter', 'filtro de transmision', 'filtro transmision', 'filtro aceite transm']):
        return 'filtro_transmision'
    if 'diferencial' in t:
        return 'diferencial'
    if any(x in t for x in ['flecha cardan', 'eje de transmision', 'eje transmision']):
        return 'flecha_eje'
    if any(x in t for x in ['reten', 'retén']):
        return 'reten'
    if any(x in t for x in ['volante cremallera']):
        return 'volante_cremallera'
    if any(x in t for x in ['volante motriz', 'volante de inercia', 'doble masa']):
        return 'volante_motriz'
    if any(x in t for x in ['cruceta']):
        return 'cruceta'
    if any(x in t for x in ['transfer', 'seminueva']):
        return 'transfer'
    if any(x in t for x in ['enfriador', 'enfriamiento transmision']):
        return 'enfriador'
    if any(x in t for x in ['sensor eje', 'sensor excentrico', 'sensor exc']):
        return 'sensor'
    if any(x in t for x in ['vanos', 'kit repuesto reparacion vanos']):
        return 'vanos'
    if any(x in t for x in ['chicote', 'articulacion chicote', 'conector transmision']):
        return 'chicote'
    if any(x in t for x in ['collarin hidraulico']):
        return 'collarin'
    return 'general'

def build_compat(titulo, compatibilidades, descripcion):
    if compatibilidades:
        return compatibilidades[:600]
    if descripcion:
        desc_clean = re.sub(
            r'ESPECIALISTAS EN.*?(?:VOLKSWAGEN|VOLVO|MINI COOPER).*?(\n|$)',
            '', descripcion, flags=re.IGNORECASE | re.DOTALL
        )
        lines = [l.strip() for l in desc_clean.split('\n') if l.strip()]
        model_lines = [l for l in lines if re.search(r'\b(BMW|Mercedes|Audi|VW|Porsche|Volvo|Mini|Sprinter|Crafter)\b', l, re.I)
                       and any(c.isdigit() for c in l)]
        if model_lines:
            return ' | '.join(model_lines[:8])
    return f"Compatible con {titulo}. Confirma compatibilidad con tu número de VIN antes de comprar."

resultados = []

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
    cat = get_cat(titulo)

    handle_base = slugify(titulo)
    if not handle_base:
        handle_base = slugify(sku) if sku else f'producto-{fila}'
    handle = unique_handle(handle_base, used_handles)

    oem_match = re.search(r'(?:OEM|N[uú]mero OEM|Num\. parte)[:\s]+([A-Z0-9\-]{6,})', desc_raw, re.IGNORECASE)
    if oem_match and not codigo_oem:
        codigo_oem = oem_match.group(1)

    caract_compat = build_compat(titulo, compatibilidades, desc_raw)
    caract_tipo = 'Carro/Camioneta' if tipo_vehiculo else 'Carro/Camioneta'

    gar_str = re.sub(r'Garant[íi]a del vendedor:\s*', '', garantia).strip() if garantia else ''
    gar_txt = f"{gar_str} de garantía" if gar_str and gar_str != 'Sin garantía' else 'calidad garantizada'
    gar_faq = f"Sí, {gar_str} de garantía del vendedor." if gar_str and gar_str != 'Sin garantía' else 'Este producto no incluye garantía del fabricante.'

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

    unidad = p.get('unidad_venta', '') or ''
    envio = "Tenemos stock disponible para entrega inmediata. Enviamos el mismo dia de tu pago a Ciudad de Mexico y a todo el pais via DHL o FedEx."
    if 'juego' in unidad.lower() or 'kit' in unidad.lower() or any(x in titulo.lower() for x in ['kit', 'juego']):
        envio += " Este producto se vende como kit completo."

    dev = ("Aceptamos devoluciones dentro de los 30 días posteriores a la entrega, sin importar el motivo. "
           "Para que tu devolución proceda, la pieza debe estar sin uso, sin instalar y en su empaque original.\n\n"
           "Asegura el ajuste perfecto: Una vez realizada tu compra, un asesor te contactará brevemente para validar "
           "la compatibilidad con tu número VIN y garantizar que recibas exactamente lo que tu auto necesita.\n\n"
           "Consulta nuestra politica completa aquí")

    descs = {
        'clutch': (
            f"Kit de clutch (embrague) de reemplazo para {titulo}. "
            f"Incluye los componentes necesarios para la sustitución completa del embrague, garantizando una transmisión de potencia óptima entre el motor y la caja de velocidades.\n\n"
            f"Reemplazo directo del clutch original. Ideal para restaurar el funcionamiento del embrague ante síntomas de patinamiento, dificultad para cambiar velocidades o desgaste avanzado.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        ),
        'doble_embrague': (
            f"Kit de doble embrague (DCT) de reemplazo para {titulo}. "
            f"Componente del sistema de transmisión automática de doble embrague, diseñado para la sustitución completa del conjunto.\n\n"
            f"Reemplazo directo del doble embrague original. Requiere instalación profesional especializada.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        ),
        'bomba_clutch': (
            f"Bomba/cilindro maestro de clutch de reemplazo para {titulo}. "
            f"Componente hidráulico que genera la presión necesaria para accionar el sistema de embrague.\n\n"
            f"Reemplazo directo del cilindro maestro original. Si el pedal de clutch se hunde hasta el piso o el embrague no desengrana correctamente, este suele ser el componente a revisar.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        ),
        'goma_cardan': (
            f"Junta/goma de cardan (disco flexible) de reemplazo para {titulo}. "
            f"Une la transmisión con el árbol de transmisión, absorbiendo vibraciones y desalineaciones. "
            f"Su desgaste genera vibraciones, ruidos y golpes al acelerar o desacelerar.\n\n"
            f"Reemplazo directo de la junta original, instalación sin modificaciones.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        ),
        'soporte_cardan': (
            f"Soporte/chumacera central de flecha de cardan para {titulo}. "
            f"Sostiene el árbol de transmisión en su punto medio, permitiendo la rotación suave. "
            f"Su desgaste genera vibraciones, ruidos y golpeteo en el tren de transmisión.\n\n"
            f"Reemplazo directo del soporte original, instalación sin modificaciones.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        ),
        'engrane_transfer': (
            f"Engrane/piñón para actuador del transfer para {titulo}. "
            f"Componente interno del sistema de tracción en las cuatro ruedas (4x4), parte del motor eléctrico del transfer.\n\n"
            f"Reemplazo directo del engrane original. El desgaste de este engrane genera códigos de error del transfer y pérdida del sistema 4x4.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        ),
        'soporte_transmision': (
            f"Soporte/taco de transmisión de reemplazo para {titulo}. "
            f"Aísla y absorbe las vibraciones de la caja de cambios hacia la carrocería, manteniendo la alineación correcta de la transmisión.\n\n"
            f"Reemplazo directo del soporte original. El desgaste genera vibraciones excesivas y golpeteo al cambiar velocidades.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        ),
        'soporte_transfer': (
            f"Soporte de transfer para {titulo}. "
            f"Fija y amortigua el conjunto del transfer a la carrocería, manteniendo su alineación correcta con el tren de transmisión.\n\n"
            f"Reemplazo directo del soporte original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        ),
        'filtro_transmision': (
            f"Filtro/cárter de aceite de transmisión automática de reemplazo para {titulo}. "
            f"Filtra las partículas del aceite de transmisión, protegiendo los componentes internos de la caja automática.\n\n"
            f"Reemplazo directo. Se recomienda cambiar junto con el aceite de transmisión según el intervalo del fabricante.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        ),
        'diferencial': (
            f"Diferencial de reemplazo para {titulo}. "
            f"Componente que distribuye la potencia entre las ruedas del mismo eje, permitiendo que giren a diferentes velocidades en curvas.\n\n"
            f"Reemplazo directo del diferencial original. Requiere instalación por mecánico especializado.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        ),
        'flecha_eje': (
            f"Flecha/eje de transmisión de reemplazo para {titulo}. "
            f"Transmite la potencia desde la caja de cambios hasta las ruedas. "
            f"Su desgaste genera vibraciones, ruidos y pérdida de tracción.\n\n"
            f"Reemplazo directo del eje original. Requiere instalación especializada.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        ),
        'reten': (
            f"Retén de transmisión de reemplazo para {titulo}. "
            f"Sella el aceite de transmisión evitando fugas por el eje de salida. "
            f"Su desgaste es la principal causa de fugas de aceite en la transmisión.\n\n"
            f"Reemplazo directo del retén original, instalación sencilla.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        ),
        'volante_cremallera': (
            f"Volante de cremallera (inercia de arranque) de reemplazo para {titulo}. "
            f"Componente del sistema de arranque que transfiere el movimiento del motor de arranque al motor de combustión.\n\n"
            f"Reemplazo directo del original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        ),
        'volante_motriz': (
            f"Volante motriz de doble masa de reemplazo para {titulo}. "
            f"Amortigua las vibraciones del motor hacia la transmisión, protegiendo los componentes de la caja de cambios. "
            f"Su desgaste genera ruidos, vibraciones y dificultad para cambiar velocidades.\n\n"
            f"Reemplazo directo del volante original. Requiere instalación profesional.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        ),
        'cruceta': (
            f"Cruceta de cardan de reemplazo para {titulo}. "
            f"Permite la articulación del árbol de transmisión en diferentes ángulos, transmitiendo el par motor de forma eficiente.\n\n"
            f"Reemplazo directo de la cruceta original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        ),
        'transfer': (
            f"Transfer/caja de transferencia para {titulo}. "
            f"Distribuye la potencia entre los ejes delantero y trasero en sistemas de tracción total (4x4/AWD).\n\n"
            f"Unidad de reemplazo. Requiere instalación por mecánico especializado en transmisiones.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        ),
        'enfriador': (
            f"Enfriador de aceite de transmisión de reemplazo para {titulo}. "
            f"Mantiene la temperatura óptima del aceite de transmisión, prolongando la vida de los componentes internos.\n\n"
            f"Reemplazo directo del enfriador original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        ),
        'sensor': (
            f"Sensor de eje/posición de transmisión para {titulo}. "
            f"Monitorea la posición o velocidad del eje para el correcto funcionamiento del sistema de gestión del motor y la transmisión.\n\n"
            f"Reemplazo directo del sensor original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        ),
        'vanos': (
            f"Kit de reparación del sistema VANOS para {titulo}. "
            f"El VANOS es el sistema de variación de fase de árbol de levas de BMW. "
            f"Este kit incluye los componentes de repuesto para restaurar el correcto funcionamiento del sistema.\n\n"
            f"Reemplazo directo de los componentes desgastados del VANOS original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        ),
        'chicote': (
            f"Chicote/articulación de selector de velocidades para {titulo}. "
            f"Conecta la palanca de cambios con la caja de velocidades, permitiendo el cambio preciso de marchas.\n\n"
            f"Reemplazo directo del chicote original. Su desgaste genera cambios imprecisos o la palanca no regresa a posición.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        ),
        'collarin': (
            f"Collarín hidráulico de clutch de reemplazo para {titulo}. "
            f"Acciona el mecanismo de desenganche del embrague al pisar el pedal de clutch.\n\n"
            f"Reemplazo directo del collarín original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        ),
        'general': (
            f"{titulo}. Componente del sistema de transmisión para vehículos europeos. "
            f"Reemplazo directo de la pieza original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        ),
    }

    sec_desc = descs.get(cat, descs['general'])

    faqs = {
        'clutch': [
            {"pregunta": "¿Qué incluye el kit de clutch?",
             "respuesta": "Incluye plato de presión, disco de embrague y collarín. Verifica en el listado los componentes específicos incluidos."},
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq},
            {"pregunta": "¿Cuáles son los síntomas de un clutch desgastado?",
             "respuesta": "Patinamiento al acelerar, dificultad para meter velocidades, olor a quemado al soltar el pedal, pedal de clutch muy alto o muy bajo."}
        ],
        'goma_cardan': [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Cuándo se reemplaza la goma de cardan?",
             "respuesta": "Al detectar vibraciones al acelerar/desacelerar, ruidos tipo golpeteo en el tren de transmisión, o fugas de aceite por la zona del cardan."},
            {"pregunta": "¿Qué incluye?", "respuesta": "Se incluye la junta/goma de cardan como pieza individual."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ],
        'soporte_cardan': [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Cuándo se reemplaza el soporte de cardan?",
             "respuesta": "Al detectar vibraciones en marcha, ruidos al acelerar, o movimiento excesivo del árbol de transmisión."},
            {"pregunta": "¿Qué incluye?", "respuesta": "Se incluye el soporte/chumacera de cardan como pieza individual."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ],
        'filtro_transmision': [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Cada cuánto se cambia el filtro de transmisión?",
             "respuesta": "Se recomienda cambiar junto con el aceite de transmisión, generalmente cada 60,000-80,000 km según el fabricante."},
            {"pregunta": "¿Qué incluye?", "respuesta": "Se incluye el filtro y/o cárter de transmisión. Verifica el listado para detalles."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ],
    }

    default_faq = [
        {"pregunta": "¿Para qué vehículos es compatible?",
         "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
        {"pregunta": "¿Qué incluye el producto?",
         "respuesta": "Se incluye la pieza indicada en el título. Verifica el listado para detalles específicos."},
        {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq},
        {"pregunta": "¿Requiere instalación especializada?",
         "respuesta": "Los componentes de transmisión requieren instalación por mecánico especializado en transmisiones de vehículos europeos."}
    ]

    faq = faqs.get(cat, default_faq)

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
    if not marca:
        flags.append("[ANALIZAR] Marca no identificada — confirmar fabricante.")
    if dup_count > 1:
        flags.append(f"[REVISAR] Listing {dup_count} del SKU {sku} — evaluar si se consolida con el listing principal.")
    flags.append("[INCLUIR] Peso y dimensiones para cálculo de envío.")
    flags.append("[INCLUIR] Fotografías del producto.")

    try:
        precio_fmt = f"{float(precio):.2f}"
    except Exception:
        precio_fmt = str(precio)

    # Related: same cat or same vehicle brand
    related_skus = []
    for op in products:
        if op['sku'] != sku and op['sku'] not in related_skus:
            op_cat = get_cat(op['titulo'])
            op_tags = get_tags(op['titulo'], op['descripcion'] or '')
            if op_cat == cat or any(t in op_tags for t in tags.split(', ') if t):
                related_skus.append(op['sku'])
    seen_r = list(dict.fromkeys(related_skus))
    related = seen_r[:5]

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
        "shopify_type": "Transmisión",
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

with open('output/refacciones_transmision_batch_result.json', 'w', encoding='utf-8') as f:
    json.dump({"resultados": resultados}, f, ensure_ascii=False, indent=2)

cat_count = Counter(get_cat(r['shopify_title']) for r in resultados)
tag_count = Counter()
for r in resultados:
    for t in r['shopify_tags'].split(', '):
        if t:
            tag_count[t] += 1
dup_skus = {k: v for k, v in seen_skus.items() if v > 1}

print(f"Generados: {len(resultados)} productos")
print(f"SKUs únicos: {len(seen_skus)}, con duplicados: {len(dup_skus)}")
print(f"\nCategorías de producto:")
for c, n in cat_count.most_common():
    print(f"  {c}: {n}")
print(f"\nTags (marcas vehículo):")
for t, n in tag_count.most_common():
    print(f"  {t}: {n}")
