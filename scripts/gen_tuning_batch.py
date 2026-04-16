import json
import unicodedata
import re

with open('output/tuning_batch.json', encoding='utf-8') as f:
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
    fixes = [('Bmw', 'BMW'), ('Audi', 'Audi'), (' Vw ', ' VW '), ('Mercedes', 'Mercedes'),
             ('Mini ', 'Mini '), ('Porsche', 'Porsche'), ('Volvo', 'Volvo'), ('Jaguar', 'Jaguar')]
    for old, new in fixes:
        t = t.replace(old, new)
    return t[:255]

def get_type(subcat, titulo):
    subcat = (subcat or '').lower()
    titulo = (titulo or '').lower()
    if 'iluminaci' in subcat or 'balastra' in titulo or 'foco' in titulo or 'xenon' in titulo:
        return 'Sistema Eléctrico'
    return 'Tuning'

def get_tags(titulo, descripcion):
    text = (titulo + ' ' + descripcion).upper()
    found = []
    mappings = [
        ('BMW', 'BMW'), ('MERCEDES', 'Mercedes-Benz'), ('AUDI', 'Audi'),
        ('VOLKSWAGEN', 'Volkswagen'), ('VW ', 'Volkswagen'),
        ('PORSCHE', 'Porsche'), ('VOLVO', 'Volvo'), ('MINI', 'Mini'),
        ('LAND ROVER', 'Land Rover'), ('JAGUAR', 'Jaguar'),
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

def get_related(sku, products):
    seen = []
    for p in products:
        if p['sku'] != sku and p['sku'] not in seen:
            seen.append(p['sku'])
    return seen[:5]

resultados = []

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

    shopify_type = get_type(subcat, titulo_raw)
    tags = get_tags(titulo_raw, desc_raw)

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

    # Antes de comprar
    abc = "Para garantizar que recibas la pieza correcta para tu vehículo, necesitamos el número de serie (VIN) de tu auto antes de procesar el pedido. Esto evita errores, tiempos perdidos y devoluciones innecesarias. Escríbenos y con gusto confirmamos compatibilidad."
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

    garantia_str = re.sub(r'Garant[íi]a del vendedor:\s*', '', garantia).strip() if garantia else ''

    is_balastra = 'balastra' in titulo.lower()
    is_foco = re.search(r'\bfoco', titulo.lower())
    is_spoiler = any(x in titulo.lower() for x in ['spoiler', 'lip', 'faldon', 'aleron', 'moldura', 'esquina'])

    # Bulb type
    bulb = ''
    for b in ['D1S', 'D2S', 'D3S', 'D4S']:
        if b in titulo.upper():
            bulb = b
            break

    # Kelvin
    kelvin = ''
    k_match = re.search(r'(\d{4,5})\s*[Kk]', titulo)
    if k_match:
        kelvin = k_match.group(1) + 'K'

    gar_txt = f"{garantia_str} de garantía del vendedor" if garantia_str and garantia_str != 'Sin garantía' else 'calidad garantizada'
    gar_faq = f"{garantia_str} de garantía del vendedor." if garantia_str and garantia_str != 'Sin garantía' else 'Este producto no incluye garantía del fabricante.'

    if is_balastra:
        sec_desc = (
            f"Balastra (módulo electrónico de control) para faros de luz xenón HID{' tipo ' + bulb if bulb else ''}. "
            f"Regula la descarga eléctrica que alimenta el arco de luz del faro xenón, garantizando encendido estable y larga vida útil.\n\n"
            f"Reemplazo directo del módulo original para {titulo}. Instalación directa sin modificaciones.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible esta balastra?",
             "respuesta": f"Compatible con {titulo}. Te recomendamos confirmar con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": f"Se incluye una balastra{' tipo ' + bulb if bulb else ''} como pieza individual, lista para instalar."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq},
            {"pregunta": "¿Cómo sé si mi balastra original está fallando?",
             "respuesta": "Síntomas comunes: faro parpadeante, luz inestable, faro que no enciende o tarda en encender. Te recomendamos confirmar el diagnóstico antes de comprar."}
        ]
    elif is_foco:
        sec_desc = (
            f"Foco xenón HID{' tipo ' + bulb if bulb else ''}{', temperatura de color ' + kelvin if kelvin else ''}. "
            f"Reemplazo directo del bulbo xenón original para {titulo}.\n\n"
            f"Mayor luminosidad y mejor visibilidad que halógenos. Instalación directa en el faro original sin modificaciones.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": f"¿Qué temperatura de color tiene?",
             "respuesta": f"{'Temperatura de color ' + kelvin + '. ' if kelvin else ''}A mayor número de Kelvin la luz es más azulada; a menor número, más blanca/amarilla."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye el foco xenón. Verifica en el listado si incluye ignitor o se vende por separado."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]
    elif is_spoiler:
        sec_desc = (
            f"{titulo}. Pieza de diseño aerodinámico que mejora la apariencia exterior del vehículo con un acabado que complementa las líneas originales de fábrica.\n\n"
            f"Diseñada específicamente para este modelo y año, instalación directa. "
            f"Puede requerir pintura para igualar el color del vehículo.\n\n"
            f"Fabricada por {marca} con tecnología alemana. {gar_txt.capitalize()} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos aplica?",
             "respuesta": f"Aplica para {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye la pieza indicada en el título como unidad individual."},
            {"pregunta": "¿Requiere pintura?",
             "respuesta": "Las piezas de tuning exterior generalmente se entregan en color negro mate o material base y pueden requerir pintura para igualar el color original del vehículo."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]
    else:
        sec_desc = (
            f"{titulo}. Pieza de calidad para vehículos europeos, diseñada como reemplazo o accesorio directo.\n\n"
            f"Marca {marca}. {gar_txt.capitalize()} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos aplica?",
             "respuesta": f"Aplica para {titulo}. Confirma con tu número de VIN."},
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

with open('output/tuning_batch_result.json', 'w', encoding='utf-8') as f:
    json.dump({"resultados": resultados}, f, ensure_ascii=False, indent=2)

print(f"Generados: {len(resultados)} productos")
print(f"SKUs únicos: {len(seen_skus)}")
dup_skus = {k: v for k, v in seen_skus.items() if v > 1}
print(f"SKUs con duplicados: {len(dup_skus)}")
for k, v in sorted(dup_skus.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v} listings")
