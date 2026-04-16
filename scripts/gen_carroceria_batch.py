import json
import unicodedata
import re

with open('output/refacciones_carroceria_batch.json', encoding='utf-8') as f:
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
    if 'parrilla' in t or 'rejilla' in t or 'grille' in t:
        return 'parrilla'
    if 'espejo' in t or 'retrovisor' in t:
        return 'espejo'
    if 'defensa' in t or 'bumper' in t or 'paragolpe' in t or 'parachoques' in t:
        return 'defensa'
    if 'facia' in t or 'difusor' in t:
        return 'facia'
    if 'faro' in t or 'farol' in t or 'neblinero' in t or 'antiniebla' in t or 'niebla' in t:
        return 'faro'
    if 'calavera' in t or 'luz trasera' in t:
        return 'calavera'
    if 'cofre' in t or 'capo' in t or 'capot' in t:
        return 'cofre'
    if 'salpicadera' in t or 'guardafango' in t or 'aleta' in t:
        return 'salpicadera'
    if 'puerta' in t:
        return 'puerta'
    if 'manija' in t or 'tirador' in t:
        return 'manija'
    if 'moldura' in t or 'cantonera' in t:
        return 'moldura'
    if 'emblema' in t or 'logo' in t or 'insignia' in t:
        return 'emblema'
    if 'luna' in t or 'vidrio' in t or 'cristal' in t or 'parabrisas' in t:
        return 'vidrio'
    if 'tapon' in t and ('gasolina' in t or 'combustible' in t or 'tanque' in t):
        return 'tapon_gasolina'
    if 'bisagra' in t:
        return 'bisagra'
    if 'guardabarro' in t or 'faldon' in t or 'faldón' in t:
        return 'faldon'
    return 'carroceria_general'

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

    pintura_note = "Esta pieza puede requerir pintura para igualar el color original del vehículo. Generalmente se entrega en color base (negro o gris) sin pintar."

    # --- Content by category ---
    if cat == 'parrilla':
        # Detect type: delantera/trasera, superior/inferior, central
        pos = ''
        for kw in ['delantera', 'trasera', 'superior', 'inferior', 'central', 'lateral']:
            if kw in titulo.lower():
                pos = kw
                break
        sec_desc = (
            f"Parrilla{' ' + pos if pos else ''} para {titulo}. "
            f"Pieza de carrocería frontal que protege el radiador y los componentes del motor mientras define la estética característica del vehículo.\n\n"
            f"Instalación directa como reemplazo de la parrilla original. Encaja en los puntos de sujeción de fábrica. {pintura_note}\n\n"
            f"Fabricada por {marca} con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos aplica esta parrilla?",
             "respuesta": f"Aplica para {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye la parrilla indicada en el título como unidad individual."},
            {"pregunta": "¿Requiere pintura?",
             "respuesta": pintura_note},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'espejo':
        lado = ''
        for kw in ['izquierdo', 'derecho', 'izq', 'der', 'conductor', 'copiloto']:
            if kw in titulo.lower():
                lado = kw
                break
        electrico = 'eléctrico' if any(k in titulo.lower() for k in ['electrico', 'electr', 'power', 'abatible']) else ''
        sec_desc = (
            f"Espejo retrovisor lateral{' ' + lado if lado else ''}{' ' + electrico if electrico else ''} para {titulo}. "
            f"Carcasa y/o mecanismo de espejo retrovisor exterior de reemplazo con el ajuste y acabado correcto para el modelo indicado.\n\n"
            f"Instalación directa como reemplazo del espejo original. Verificar en el listado si incluye la carcasa, el mecanismo, o el conjunto completo.\n\n"
            f"Fabricado por {marca} con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos aplica este espejo?",
             "respuesta": f"Aplica para {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Verifica en el listado si incluye: carcasa exterior, cristal del espejo, mecanismo eléctrico o el conjunto completo."},
            {"pregunta": "¿Requiere pintura?",
             "respuesta": "Las carcasas de espejo generalmente se entregan sin pintar (negro o gris base) y requieren pintura para igualar el color del vehículo."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'defensa':
        pos = 'delantera' if any(k in titulo.lower() for k in ['delantera', 'front', 'frontal']) else \
              'trasera' if any(k in titulo.lower() for k in ['trasera', 'rear', 'posterior']) else ''
        sec_desc = (
            f"Defensa (parachoque) {pos} para {titulo}. "
            f"Pieza de carrocería exterior que protege la estructura del vehículo en impactos de baja velocidad y define la estética frontal o trasera.\n\n"
            f"Instalación directa como reemplazo de la defensa original. {pintura_note}\n\n"
            f"Fabricada por {marca} con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos aplica esta defensa?",
             "respuesta": f"Aplica para {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye la defensa (parachoque) indicada en el título. Verifica si incluye sensores de estacionamiento, bocinas u otros accesorios integrados."},
            {"pregunta": "¿Requiere pintura?",
             "respuesta": pintura_note},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'facia':
        pos = 'delantera' if any(k in titulo.lower() for k in ['delantera', 'front', 'frontal']) else \
              'trasera' if any(k in titulo.lower() for k in ['trasera', 'rear', 'posterior']) else ''
        es_difusor = 'difusor' in titulo.lower()
        tipo_txt = 'difusor de facia trasera' if es_difusor else f'facia {pos}'.strip()
        sec_desc = (
            f"{titulo.capitalize()}. {tipo_txt.capitalize()} para el vehículo indicado. "
            f"Pieza de carrocería exterior que complementa el diseño {'trasero' if 'traserr' in titulo.lower() or 'difusor' in titulo.lower() else 'frontal'} del vehículo.\n\n"
            f"Instalación directa como reemplazo del componente original. {pintura_note}\n\n"
            f"Fabricada por {marca} con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos aplica?",
             "respuesta": f"Aplica para {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": f"Se incluye la {tipo_txt} como se indica en el título."},
            {"pregunta": "¿Requiere pintura?",
             "respuesta": pintura_note},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'faro':
        es_neblinero = any(k in titulo.lower() for k in ['neblinero', 'antiniebla', 'niebla', 'fog'])
        tipo_faro = 'neblinero (antiniebla)' if es_neblinero else 'faro'
        lado = ''
        for kw in ['izquierdo', 'derecho', 'izq', 'der']:
            if kw in titulo.lower():
                lado = kw
                break
        sec_desc = (
            f"{tipo_faro.capitalize()}{' ' + lado if lado else ''} para {titulo}. "
            f"{'Faro auxiliar de niebla que mejora la visibilidad en condiciones de lluvia, niebla o polvo.' if es_neblinero else 'Faro principal de iluminación del vehículo.'}\n\n"
            f"Instalación directa como reemplazo del componente original. Verificar en el listado si incluye bombilla o solo la carcasa/conjunto.\n\n"
            f"Fabricado por {marca} con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos aplica este faro?",
             "respuesta": f"Aplica para {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Verifica en el listado si incluye: carcasa completa, lente, bombilla o si se vende solo el conjunto de carrocería del faro."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'calavera':
        lado = ''
        for kw in ['izquierda', 'derecha', 'izq', 'der']:
            if kw in titulo.lower():
                lado = kw
                break
        sec_desc = (
            f"Calavera (luz trasera){' ' + lado if lado else ''} para {titulo}. "
            f"Conjunto de luces traseras que incluye luz de freno, direccional y reversa.\n\n"
            f"Instalación directa como reemplazo del componente original. Verificar en el listado si incluye bombillas o solo el conjunto.\n\n"
            f"Fabricada por {marca} con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos aplica?",
             "respuesta": f"Aplica para {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Verifica en el listado el contenido exacto (conjunto completo, solo lente, o con arnés)."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'cofre':
        sec_desc = (
            f"Cofre (capó) para {titulo}. "
            f"Panel de carrocería superior que cubre el compartimento del motor.\n\n"
            f"Instalación directa como reemplazo del cofre original en los puntos de sujeción de fábrica. {pintura_note}\n\n"
            f"Fabricado por {marca} con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos aplica?",
             "respuesta": f"Aplica para {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye el cofre como panel de carrocería. Las bisagras y el soporte del cofre se venden por separado."},
            {"pregunta": "¿Requiere pintura?",
             "respuesta": pintura_note},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'salpicadera':
        lado = ''
        for kw in ['izquierda', 'derecha', 'izq', 'der', 'delantera', 'trasera']:
            if kw in titulo.lower():
                lado = kw
                break
        sec_desc = (
            f"Salpicadera (guardafango){' ' + lado if lado else ''} para {titulo}. "
            f"Panel de carrocería lateral que cubre el arco de la rueda.\n\n"
            f"Instalación directa como reemplazo de la salpicadera original. {pintura_note}\n\n"
            f"Fabricada por {marca} con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos aplica?",
             "respuesta": f"Aplica para {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye la salpicadera indicada en el título. Verificar si incluye molduras o se venden por separado."},
            {"pregunta": "¿Requiere pintura?",
             "respuesta": pintura_note},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'puerta':
        sec_desc = (
            f"{titulo}. Panel o componente de puerta para vehículos europeos.\n\n"
            f"Reemplazo directo del componente original. Instalación directa. {pintura_note if any(k in titulo.lower() for k in ['panel', 'puerta']) else ''}\n\n"
            f"Fabricado por {marca} con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos aplica?",
             "respuesta": f"Aplica para {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye la pieza indicada en el título."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'manija':
        lado = ''
        for kw in ['izquierda', 'derecha', 'izq', 'der', 'delantera', 'trasera', 'interior', 'exterior']:
            if kw in titulo.lower():
                lado = kw
                break
        sec_desc = (
            f"Manija{' ' + lado if lado else ''} para {titulo}. "
            f"Tirador de puerta de reemplazo directo.\n\n"
            f"Instalación directa como reemplazo del componente original.\n\n"
            f"Fabricada por {marca} con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos aplica?",
             "respuesta": f"Aplica para {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye la manija indicada en el título."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'moldura':
        sec_desc = (
            f"{titulo}. Moldura de carrocería exterior de reemplazo directo para el modelo indicado.\n\n"
            f"Instalación directa como reemplazo del componente original.\n\n"
            f"Fabricada por {marca} con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos aplica?",
             "respuesta": f"Aplica para {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye la moldura indicada en el título."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'emblema':
        sec_desc = (
            f"{titulo}. Emblema o insignia de carrocería de reemplazo directo.\n\n"
            f"Adhesivo o de clips según el modelo original. Instalación directa.\n\n"
            f"Fabricado por {marca} con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos aplica?",
             "respuesta": f"Aplica para {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Cómo se instala?",
             "respuesta": "La mayoría de emblemas utilizan adhesivo de doble cara o clips de retención. Limpiar la superficie antes de instalar."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'vidrio':
        sec_desc = (
            f"{titulo}. Vidrio o luna de carrocería de reemplazo directo para el modelo indicado.\n\n"
            f"Reemplazo directo del vidrio original. La instalación requiere silicón automotriz o soldadura de moldura según el tipo.\n\n"
            f"Fabricado por {marca} con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos aplica?",
             "respuesta": f"Aplica para {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye el vidrio/luna indicado. La moldura, caucho y silicón pueden no estar incluidos — verificar en el listado."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'tapon_gasolina':
        sec_desc = (
            f"Tapón de tanque de gasolina para {titulo}. "
            f"Tapa de llenado del depósito de combustible de reemplazo directo.\n\n"
            f"Instalación directa como reemplazo del tapón original.\n\n"
            f"Fabricado por {marca} con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos aplica?",
             "respuesta": f"Aplica para {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye el tapón de gasolina individual."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    else:  # bisagra, faldon, carroceria_general
        sec_desc = (
            f"{titulo}. Pieza de carrocería para vehículos europeos.\n\n"
            f"Reemplazo directo del componente original. Instalación directa.\n\n"
            f"Fabricada por {marca} con {gar_txt} contra defectos de fabricación."
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
    if cat in ('parrilla', 'defensa', 'facia', 'cofre', 'salpicadera'):
        flags.append("[VERIFICAR] Confirmar si la pieza requiere pintura o se entrega pintada en color original.")
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
        "shopify_type": "Carrocería",
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

with open('output/refacciones_carroceria_batch_result.json', 'w', encoding='utf-8') as f:
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
