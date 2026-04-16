import json
import unicodedata
import re
from collections import Counter

with open('output/refacciones_clima_batch.json', encoding='utf-8') as f:
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
    t = t.replace('Bmw', 'BMW').replace(' Vw ', ' VW ').replace('Mercedes', 'Mercedes').replace('Benz', 'Benz')
    return t[:255]

def get_tags(titulo, descripcion):
    # Only use title + compatibility lines from description (not boilerplate)
    # Strip boilerplate "ESPECIALISTAS EN ... BMW, MERCEDES..." from desc
    desc_clean = re.sub(
        r'ESPECIALISTAS EN.*?(?:VOLKSWAGEN|VOLVO|MINI COOPER).*?(\n|$)',
        '', descripcion, flags=re.IGNORECASE | re.DOTALL
    )
    # Only first 300 chars of cleaned desc to avoid noise
    text = (titulo + ' ' + desc_clean[:300]).upper()
    found = []
    mappings = [
        ('BMW', 'BMW'), ('MERCEDES', 'Mercedes-Benz'), ('AUDI', 'Audi'),
        ('VOLKSWAGEN', 'Volkswagen'), ('VW ', 'Volkswagen'), ('CRAFTER', 'Volkswagen'),
        ('SPRINTER', 'Mercedes-Benz'), ('PORSCHE', 'Porsche'), ('VOLVO', 'Volvo'),
        ('MINI', 'Mini'), ('LAND ROVER', 'Land Rover'), ('JAGUAR', 'Jaguar'),
        ('TESLA', 'Tesla'),
    ]
    for keyword, brand in mappings:
        if keyword in text and brand not in found:
            found.append(brand)
    return ', '.join(found)

def get_shopify_type(titulo):
    t = titulo.lower()
    if any(x in t for x in ['filtro', 'filter', 'cabina', 'polen']):
        return 'Filtros'
    if any(x in t for x in ['compresor', 'blower', 'soplador', 'motoventilador', 'ventilador',
                              'resistencia', 'sensor', 'banda de aire', 'condensador', 'calentador']):
        return 'Climatización'
    if 'valvula de bolsa' in t or 'bolsa de aire' in t:
        return 'Suspensión'
    if any(x in t for x in ['manguera', 'tubo', 'codo', 'banda', 'valvula', 'válvula']):
        return 'Motor'
    return 'Climatización'

def fix_origen(origen):
    if not origen:
        return ''
    o = origen.upper()
    if 'ALEMAN' in o or 'GERMAN' in o or 'IMPORT' in o:
        return 'Importado'
    return origen

def build_compat(titulo, compatibilidades, descripcion):
    if compatibilidades:
        return compatibilidades[:600]
    # Try to extract from description
    if descripcion:
        lines = [l.strip() for l in descripcion.split('\n') if l.strip()]
        model_lines = [l for l in lines if re.search(r'\b(BMW|Mercedes|Audi|VW|Porsche|Volvo|Lincoln)\b', l, re.I)
                       and any(c.isdigit() for c in l)]
        if model_lines:
            return ' | '.join(model_lines[:8])
    # Infer from title
    return f"Compatible con {titulo}. Confirma compatibilidad exacta con tu número de VIN antes de comprar."

def get_desc_category(titulo):
    t = titulo.lower()
    if 'compresor' in t:
        return 'compresor_ac'
    if 'motoventilador' in t or ('ventilador' in t and 'enfriamiento' in t):
        return 'motoventilador'
    if 'blower' in t or 'soplador' in t or 'motor soplador' in t or 'motor blower' in t:
        return 'blower'
    if 'ventilador' in t:
        return 'ventilador_ac'
    if 'resistencia' in t:
        return 'resistencia_ac'
    if 'condensador' in t:
        return 'condensador_ac'
    if 'filtro' in t and 'polen' in t:
        return 'filtro_polen'
    if 'banda' in t:
        return 'banda'
    if 'sensor' in t:
        return 'sensor_ac'
    if any(x in t for x in ['valvula', 'válvula']):
        return 'valvula'
    if any(x in t for x in ['manguera', 'tubo', 'codo', 'manguera']):
        return 'manguera'
    return 'general'

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
    shopify_type = get_shopify_type(titulo)

    handle_base = slugify(titulo)
    if not handle_base:
        handle_base = slugify(sku)
    handle = unique_handle(handle_base, used_handles)

    # OEM from desc
    oem_match = re.search(r'(?:OEM|N[uú]mero OEM|Num\. parte)[:\s]+([A-Z0-9\-]{6,})', desc_raw, re.IGNORECASE)
    if oem_match and not codigo_oem:
        codigo_oem = oem_match.group(1)

    caract_compat = build_compat(titulo, compatibilidades, desc_raw)

    tv = tipo_vehiculo
    if 'Auto' in tv or 'Carro' in tv or 'Camioneta' in tv:
        caract_tipo = 'Carro/Camioneta'
    elif tv:
        caract_tipo = tv
    else:
        caract_tipo = 'Carro/Camioneta'

    gar_str = re.sub(r'Garant[íi]a del vendedor:\s*', '', garantia).strip() if garantia else ''
    gar_txt = f"{gar_str} de garantía" if gar_str and gar_str != 'Sin garantía' else 'calidad garantizada'
    gar_faq = f"Sí, {gar_str} de garantía del vendedor." if gar_str and gar_str != 'Sin garantía' else 'Este producto no incluye garantía del fabricante.'

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
    unidad = p.get('unidad_venta', '') or ''
    envio = "Tenemos stock disponible para entrega inmediata. Enviamos el mismo dia de tu pago a Ciudad de Mexico y a todo el pais via DHL o FedEx."
    if 'juego' in unidad.lower() or 'kit' in unidad.lower():
        envio += f" Este producto se vende como {unidad.lower()} completo."

    dev = ("Aceptamos devoluciones dentro de los 30 días posteriores a la entrega, sin importar el motivo. "
           "Para que tu devolución proceda, la pieza debe estar sin uso, sin instalar y en su empaque original.\n\n"
           "Asegura el ajuste perfecto: Una vez realizada tu compra, un asesor te contactará brevemente para validar "
           "la compatibilidad con tu número VIN y garantizar que recibas exactamente lo que tu auto necesita.\n\n"
           "Consulta nuestra politica completa aquí")

    cat = get_desc_category(titulo)

    if cat == 'compresor_ac':
        sec_desc = (
            f"Compresor de aire acondicionado de reemplazo para {titulo}. "
            f"Componente principal del sistema de climatización, encargado de comprimir el refrigerante y mantener la temperatura interior del habitáculo.\n\n"
            f"Instalación directa como sustituto del compresor original, compatible con el sistema AC de fábrica. "
            f"Ideal para restaurar el funcionamiento del aire acondicionado sin modificar el sistema existente.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible este compresor?",
             "respuesta": f"Compatible con {titulo}. Te recomendamos confirmar con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye el compresor de aire acondicionado listo para instalar. Verifica en el listado si incluye empalmes o accesorios adicionales."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq},
            {"pregunta": "¿Cómo sé si mi compresor AC está fallando?",
             "respuesta": "Síntomas típicos: AC no enfría o enfría poco, ruidos al encender el AC, compresor no cicla. Confirma el diagnóstico antes de comprar."}
        ]
    elif cat == 'motoventilador':
        sec_desc = (
            f"Motoventilador eléctrico de reemplazo para {titulo}. "
            f"Encargado de mantener la temperatura óptima del radiador y del condensador del AC, activándose automáticamente según la temperatura del motor.\n\n"
            f"Reemplazo directo del conjunto original, compatible con el sistema de enfriamiento de fábrica.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye el motoventilador eléctrico completo como ensamble."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq},
            {"pregunta": "¿Cuándo falla el motoventilador?",
             "respuesta": "Síntomas: motor se sobrecalienta a baja velocidad, AC pierde eficiencia, ventilador no gira o gira lento. Confirma diagnóstico antes de comprar."}
        ]
    elif cat == 'blower':
        sec_desc = (
            f"Motor blower (soplador) de aire acondicionado y calefacción para {titulo}. "
            f"Responsable de impulsar el aire a través del sistema de climatización hacia el habitáculo.\n\n"
            f"Reemplazo directo del motor soplador original, instalación sin modificaciones.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye el motor blower de aire acondicionado como pieza individual."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq},
            {"pregunta": "¿Cómo sé si el blower está fallando?",
             "respuesta": "Síntomas: poco flujo de aire, ruidos al encender AC o calefacción, ventilador que no funciona en algunas velocidades."}
        ]
    elif cat == 'ventilador_ac':
        sec_desc = (
            f"Ventilador de aire acondicionado de reemplazo para {titulo}. "
            f"Componente del sistema de climatización que impulsa el aire frío o caliente hacia el interior del vehículo.\n\n"
            f"Reemplazo directo del ventilador original, compatible con el sistema de climatización de fábrica.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye?", "respuesta": "Se incluye el ventilador de AC como pieza individual."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]
    elif cat == 'resistencia_ac':
        sec_desc = (
            f"Resistencia (módulo de control de velocidades) del ventilador de aire acondicionado y calefacción para {titulo}. "
            f"Controla las diferentes velocidades del soplador del sistema de climatización.\n\n"
            f"Reemplazo directo de la resistencia original. Si el soplador solo funciona a velocidad máxima o no funciona en ciertas velocidades, esta es la pieza a reemplazar.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Cuándo se reemplaza la resistencia del AC?",
             "respuesta": "Cuando el ventilador solo funciona a velocidad máxima o no funciona en alguna velocidad específica."},
            {"pregunta": "¿Qué incluye?", "respuesta": "Se incluye la resistencia del ventilador AC como pieza individual."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]
    elif cat == 'condensador_ac':
        sec_desc = (
            f"Condensador de aire acondicionado de reemplazo para {titulo}. "
            f"Componente del sistema AC ubicado frente al radiador, encargado de disipar el calor del refrigerante.\n\n"
            f"Reemplazo directo del condensador original, compatible con el sistema AC de fábrica.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye?", "respuesta": "Se incluye el condensador de AC como pieza individual."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq},
            {"pregunta": "¿Cómo sé si el condensador está dañado?",
             "respuesta": "Síntomas: AC no enfría correctamente, fuga de refrigerante visible, condensador con golpes o corrosión visible."}
        ]
    elif cat == 'filtro_polen':
        sec_desc = (
            f"Filtro de habitáculo (filtro de polen/cabina) de reemplazo para {titulo}. "
            f"Filtra el aire que entra al habitáculo, eliminando polvo, polen, bacterias y partículas contaminantes.\n\n"
            f"Reemplazo directo del filtro original. Se recomienda cambiar cada 15,000-20,000 km o una vez al año.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Cada cuánto se cambia el filtro de cabina?",
             "respuesta": "Se recomienda cambiar cada 15,000-20,000 km o una vez al año, o antes si hay reducción del flujo de aire del AC/calefacción."},
            {"pregunta": "¿Qué incluye?", "respuesta": "Se incluye el filtro de habitáculo como pieza individual."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]
    elif cat == 'banda':
        sec_desc = (
            f"Banda de accesorios/aire acondicionado de reemplazo para {titulo}. "
            f"Transmite la potencia del motor hacia el compresor del AC y otros accesorios.\n\n"
            f"Reemplazo directo de la banda original. Se recomienda inspeccionar periódicamente y reemplazar ante signos de desgaste, grietas o pérdida de tensión.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Cuándo se reemplaza la banda de AC?",
             "respuesta": "Al detectar signos de desgaste, grietas, chirriados o cuando el AC pierde eficiencia por banda deslizante."},
            {"pregunta": "¿Qué incluye?", "respuesta": "Se incluye la banda como pieza individual."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]
    elif cat == 'sensor_ac':
        sec_desc = (
            f"Sensor de temperatura/presión del sistema de aire acondicionado para {titulo}. "
            f"Monitorea las condiciones del sistema AC y envía señales a la ECU para regular el funcionamiento óptimo del compresor y el flujo de refrigerante.\n\n"
            f"Reemplazo directo del sensor original, instalación sin modificaciones.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye?", "respuesta": "Se incluye el sensor de AC como pieza individual."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq},
            {"pregunta": "¿Cómo sé si el sensor de AC está fallando?",
             "respuesta": "Síntomas: AC no enfría bien, compresor no cicla correctamente, códigos de error relacionados con el sistema AC."}
        ]
    elif cat == 'valvula':
        sec_desc = (
            f"{titulo}. Componente del sistema de climatización o suspensión neumática que regula el flujo de aire o refrigerante según las condiciones de operación.\n\n"
            f"Reemplazo directo de la válvula original, compatible con el sistema de fábrica.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye?", "respuesta": "Se incluye la válvula como pieza individual."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]
    elif cat == 'manguera':
        sec_desc = (
            f"{titulo}. Manguera de reemplazo para el sistema de enfriamiento, calefacción o admisión de aire del vehículo. "
            f"Fabricada con materiales resistentes a las altas temperaturas y a los fluidos del motor.\n\n"
            f"Reemplazo directo de la manguera original, instalación sin modificaciones. Ideal para restaurar el sellado correcto del sistema de enfriamiento o calefacción.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Cuándo se reemplaza una manguera de radiador?",
             "respuesta": "Al detectar fugas de refrigerante, manguera hinchada, quebradiza o blanda. También se recomienda revisar al cambiar el refrigerante."},
            {"pregunta": "¿Qué incluye?", "respuesta": "Se incluye la manguera como pieza individual."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]
    else:
        sec_desc = (
            f"{titulo}. Componente del sistema de climatización o enfriamiento para vehículos europeos. "
            f"Reemplazo directo de la pieza original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye?", "respuesta": "Se incluye la pieza indicada en el título."},
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

    # Related (same type or same vehicle brand)
    related_skus = []
    for op in products:
        if op['sku'] != sku and op['sku'] not in related_skus:
            if (get_desc_category(op['titulo']) == cat or
                any(tag in get_tags(op['titulo'], op['descripcion'] or '') for tag in tags.split(', ') if tag)):
                related_skus.append(op['sku'])
    # Dedupe
    seen_r = []
    for s in related_skus:
        if s not in seen_r:
            seen_r.append(s)
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

with open('output/refacciones_clima_batch_result.json', 'w', encoding='utf-8') as f:
    json.dump({"resultados": resultados}, f, ensure_ascii=False, indent=2)

# Stats
type_count = Counter(r['shopify_type'] for r in resultados)
tag_count = Counter()
for r in resultados:
    for t in r['shopify_tags'].split(', '):
        if t:
            tag_count[t] += 1
dup_skus = {k: v for k, v in seen_skus.items() if v > 1}

print(f"Generados: {len(resultados)} productos")
print(f"SKUs unicos: {len(seen_skus)}, con duplicados: {len(dup_skus)}")
print(f"\nTipos Shopify:")
for t, c in type_count.most_common():
    print(f"  {t}: {c}")
print(f"\nTags (marcas de vehiculo):")
for t, c in tag_count.most_common():
    print(f"  {t}: {c}")
