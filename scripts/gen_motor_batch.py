import json
import unicodedata
import re

with open('output/refacciones_motor_batch.json', encoding='utf-8') as f:
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

    # Juntas
    if 'junta' in t or 'empaque' in t:
        if 'culata' in t or ('cabeza' in t and 'motor' in t): return 'junta_culata'
        if 'tapa' in t and ('valvula' in t or 'punterias' in t or 'distribucion' in t): return 'junta_tapa'
        if 'multiple' in t or 'múltiple' in t or ('admision' in t) or ('escape' in t and 'junta' in t): return 'junta_multiple'
        if 'kit' in t or 'completo' in t or 'juego' in t: return 'kit_juntas'
        if 'enfriador' in t or 'radiador' in t: return 'junta_enfriador'
        if 'aceite' in t or 'filtro' in t: return 'junta_aceite'
        if 'turbo' in t: return 'junta_turbo'
        return 'junta_general'

    # Cooling system
    if 'radiador' in t: return 'radiador'
    if 'termostato' in t or 'termóstato' in t: return 'termostato'
    if 'bomba' in t and 'agua' in t: return 'bomba_agua'
    if 'manguera' in t: return 'manguera'
    if 'deposito' in t or 'depósito' in t: return 'deposito'
    if 'refrigerante' in t or 'anticongelante' in t: return 'refrigerante'
    if 'tubo' in t and ('agua' in t or 'refrigerante' in t or 'distribucion' in t): return 'tubo_agua'
    if 'bomba' in t and ('refrigerante' in t or 'auxiliar' in t): return 'bomba_agua'

    # Lubrication
    if 'enfriador' in t and 'aceite' in t: return 'enfriador_aceite'
    if 'bomba' in t and 'aceite' in t: return 'bomba_aceite'
    if 'reten' in t or 'retén' in t: return 'reten'
    if 'sello' in t and 'aceite' in t: return 'reten'
    if 'metal' in t and ('bancada' in t or 'biela' in t or 'centro' in t): return 'metal_motor'
    if 'tapa' in t and ('aceite' in t or 'filtro' in t): return 'tapa_aceite'
    if 'filtro' in t and 'aceite' in t: return 'filtro_aceite'
    if 'aceite' in t and 'junta' not in t: return 'aceite_motor'

    # Valves
    if 'valvula' in t or 'válvula' in t:
        if 'pcv' in t or ('ventilacion' in t and 'carter' in t) or 'cárter' in t: return 'valvula_pcv'
        if 'egr' in t: return 'valvula_egr'
        if 'turbo' in t or 'wastegate' in t or 'bypass' in t or 'diverter' in t or 'alivio' in t: return 'valvula_turbo'
        if 'vanos' in t or 'vvt' in t or 'valvetronic' in t or 'levas' in t: return 'valvula_vvt'
        if 'admision' in t or 'escape' in t: return 'valvula_motor'
        if 'solenoide' in t or 'aceite' in t or 'bomba' in t: return 'valvula_aceite'
        return 'valvula_general'
    if 'solenoide' in t and ('aceite' in t or 'vanos' in t or 'levas' in t): return 'valvula_vvt'
    if 'solenoide' in t: return 'valvula_general'

    # Fuel
    if 'bomba' in t and ('gasolina' in t or 'combustible' in t or 'fuel' in t): return 'bomba_gasolina'

    # Timing
    if ('tensor' in t or 'tensador' in t) and ('cadena' in t or 'distribuc' in t or 'tiempo' in t): return 'tensor_distribucion'
    if 'tensor' in t or 'tensador' in t: return 'tensor'
    if 'cadena' in t and ('distribuc' in t or 'tiempo' in t or 'levas' in t): return 'cadena_distribucion'
    if 'guia' in t or 'guía' in t: return 'guia_cadena'
    if 'kit' in t and ('cadena' in t or 'distribuc' in t or 'tiempo' in t): return 'kit_distribucion'
    if 'correa' in t and ('distribuc' in t or 'tiempo' in t): return 'correa_distribucion'
    if 'kit' in t and ('correa' in t or 'banda' in t) and ('distribuc' in t or 'tiempo' in t): return 'kit_distribucion'

    # Belt/pulleys
    if 'correa' in t or 'banda' in t and 'accesorio' in t: return 'correa'
    if 'polea' in t: return 'polea'

    # Engine components
    if 'turbo' in t or 'turbocargador' in t: return 'turbo'
    if 'intercooler' in t: return 'intercooler'
    if 'arbol' in t and 'levas' in t: return 'arbol_levas'
    if 'tapa' in t and ('valvula' in t or 'punterias' in t): return 'tapa_valvulas'
    if 'tapa' in t and 'distribucion' in t: return 'tapa_distribucion'
    if 'multiple' in t or 'múltiple' in t: return 'multiple'
    if 'culata' in t or ('cabeza' in t and 'motor' in t): return 'culata'
    if 'piston' in t or 'pistón' in t: return 'piston'
    if 'ciguenal' in t or 'cigüeñal' in t: return 'ciguenial'
    if 'soporte' in t and 'motor' in t: return 'soporte_motor'
    if 'soporte' in t and ('transmision' in t or 'caja' in t): return 'soporte_transmision'
    if 'soporte' in t: return 'soporte_motor'

    # Misc
    if 'herramienta' in t or 'sincronizac' in t: return 'herramienta'
    if 'engrane' in t: return 'engrane'
    if 'tapon' in t: return 'tapon'
    if 'liga' in t or 'abrazadera' in t: return 'liga'
    if 'kit' in t: return 'kit_motor'
    if 'sensor' in t: return 'sensor_motor'
    if 'tapa' in t: return 'tapa_general'

    return 'motor_general'

def get_shopify_type(cat):
    if cat in ('correa_distribucion', 'kit_distribucion', 'herramienta', 'kit_motor'): return 'Motor'
    return 'Motor'

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

    # ---- CONTENT TEMPLATES ----
    if cat == 'junta_culata':
        sec_desc = (f"Junta de culata (empaque de cabeza) para {titulo}. "
                    f"Sella la unión entre el bloque del motor y la culata, evitando fugas de gases de combustión, aceite y refrigerante. "
                    f"Es uno de los componentes de sellado más críticos del motor.\n\n"
                    f"Reemplazo directo de la junta original. Instalación requiere torque preciso según especificaciones del fabricante.\n\n"
                    f"Marca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma familia de motor con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si mi junta de culata está fallando?",
                "respuesta": "Síntomas: humo blanco por el escape, pérdida de refrigerante sin fuga visible, aceite con aspecto lechoso, motor que se sobrecalienta, pérdida de compresión."},
               {"pregunta": "¿Se recomienda cambiar otras juntas al mismo tiempo?",
                "respuesta": "Sí, se recomienda usar un kit completo de juntas de culata que incluye retenes y empaques auxiliares al hacer este trabajo."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'junta_tapa':
        sec_desc = (f"Junta de tapa de válvulas/distribución para {titulo}. "
                    f"Sella la tapa de la culata evitando fugas de aceite por la parte superior del motor.\n\n"
                    f"Reemplazo directo. Es común encontrar este tipo de fuga en motores con más de 80,000 km.\n\n"
                    f"Marca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si la junta de tapa de válvulas está fallando?",
                "respuesta": "Síntomas: manchas de aceite en la parte superior del motor, olor a aceite quemado, aceite acumulado alrededor de la tapa o en el múltiple de escape."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'junta_multiple':
        tipo_m = 'admisión' if 'admision' in titulo.lower() else 'escape' if 'escape' in titulo.lower() else 'múltiple'
        sec_desc = (f"Junta de múltiple de {tipo_m} para {titulo}. "
                    f"Sella la unión entre el múltiple de {tipo_m} y la culata, evitando fugas de gases {'que causarían pérdida de potencia y riesgos de incendio' if tipo_m == 'escape' else 'de admisión que afectan la mezcla aire-combustible'}.\n\n"
                    f"Reemplazo directo de la junta original.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si la junta del múltiple está fallando?",
                "respuesta": f"Síntomas: {'olor a quemado o humo cerca del motor, ruido de gases escapando, pérdida de potencia' if tipo_m == 'escape' else 'ralentí inestable, entrada de aire falsa, mayor consumo de combustible, Check Engine'}."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'kit_juntas':
        sec_desc = (f"Kit completo de juntas de motor para {titulo}. "
                    f"Incluye todas las juntas, empaques y retenes necesarios para la reconstrucción o reemplazo mayor de componentes del motor.\n\n"
                    f"Se recomienda instalar todas las juntas del kit al mismo tiempo para garantizar sellado completo.\n\n"
                    f"Marca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma familia de motor con tu VIN antes de comprar."},
               {"pregunta": "¿Qué incluye el kit?",
                "respuesta": "Incluye el juego de juntas indicado en el título. Verificar en el listado el contenido exacto (solo culata, motor superior, motor completo, etc.)."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat in ('junta_aceite', 'junta_enfriador', 'junta_turbo', 'junta_general'):
        nombres = {'junta_aceite': 'de base de filtro de aceite/enfriador',
                   'junta_enfriador': 'del enfriador de aceite',
                   'junta_turbo': 'del turbo',
                   'junta_general': ''}
        nom = nombres.get(cat, '')
        sec_desc = (f"Junta/empaque {nom} para {titulo}. "
                    f"Sello de goma o metal que evita fugas de aceite, refrigerante o gases en el punto indicado del motor.\n\n"
                    f"Reemplazo directo de la junta original.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Qué incluye el producto?",
                "respuesta": "Se incluye la junta/empaque indicado en el título."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'radiador':
        sec_desc = (f"Radiador de enfriamiento para {titulo}. "
                    f"Disipa el calor del refrigerante que circula por el motor, manteniendo la temperatura de operación dentro del rango óptimo.\n\n"
                    f"Reemplazo directo del radiador original. Verificar en el listado si incluye depósito de expansión.\n\n"
                    f"Marca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Qué incluye el producto?",
                "respuesta": "Se incluye el radiador. Verificar en el listado si incluye depósito de expansión, tapón o mangueras."},
               {"pregunta": "¿Cómo sé si mi radiador está fallando?",
                "respuesta": "Síntomas: motor que se sobrecalienta, pérdida de refrigerante, manchas de anticongelante debajo del vehículo, radiador con fisuras o corrosión visible."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'bomba_agua':
        es_auxiliar = 'auxiliar' in titulo.lower()
        sec_desc = (f"Bomba de agua {'auxiliar ' if es_auxiliar else ''}para {titulo}. "
                    f"{'Bomba eléctrica secundaria que ' if es_auxiliar else ''}Impulsa la circulación del refrigerante por todo el sistema de enfriamiento del motor para mantener la temperatura óptima de operación.\n\n"
                    f"Reemplazo directo de la bomba original.\n\nMarca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si mi bomba de agua está fallando?",
                "respuesta": "Síntomas: motor que se sobrecalienta, fuga de refrigerante cerca de la bomba, ruido de chirrido o traqueteo en el área de la bomba, testigo de temperatura encendido."},
               {"pregunta": "¿Se recomienda cambiar algo más al reemplazar la bomba?",
                "respuesta": "Sí, se recomienda cambiar el termostato, la junta de la bomba y revisar las mangueras al mismo tiempo."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'termostato':
        sec_desc = (f"Termostato de motor para {titulo}. "
                    f"Regula la circulación del refrigerante hacia el radiador según la temperatura del motor, acelerando el calentamiento en frío y evitando el sobrecalentamiento en operación.\n\n"
                    f"Reemplazo directo. Puede incluir carcasa según el modelo.\n\nMarca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si mi termostato está fallando?",
                "respuesta": "Síntomas: motor que tarda mucho en calentar (termostato abierto), sobrecalentamiento (termostato cerrado/atascado), temperatura del motor inestable en tablero."},
               {"pregunta": "¿Qué incluye el producto?",
                "respuesta": "Se incluye el termostato. Verificar en el listado si incluye carcasa o junta."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'manguera':
        tipo_m = ('del radiador' if 'radiador' in titulo.lower() else
                  'del turbo/intercooler' if 'turbo' in titulo.lower() or 'intercooler' in titulo.lower() else
                  'del sistema de enfriamiento')
        sec_desc = (f"Manguera {tipo_m} para {titulo}. "
                    f"Conduce el refrigerante entre los componentes del sistema de enfriamiento resistiendo la presión y temperatura del motor.\n\n"
                    f"Reemplazo directo de la manguera original.\n\nMarca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si mi manguera está fallando?",
                "respuesta": "Síntomas: fuga de refrigerante, manguera hinchada o agrietada, pérdida de presión en el sistema de enfriamiento, motor que se sobrecalienta."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'deposito':
        tipo_d = 'de expansión de refrigerante' if 'refrigerante' in titulo.lower() or 'anticongelante' in titulo.lower() else 'de fluido'
        sec_desc = (f"Depósito {tipo_d} para {titulo}. "
                    f"Recipiente de expansión que compensa los cambios de volumen del refrigerante según la temperatura del motor.\n\n"
                    f"Reemplazo directo del depósito original.\n\nMarca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Qué incluye el producto?",
                "respuesta": "Se incluye el depósito. Verificar si incluye tapón."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'refrigerante':
        qty_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:litros?|lts?|galon)', titulo.lower())
        qty = qty_match.group(0) if qty_match else ''
        color_match = re.search(r'(azul|rojo|verde|amarillo)', titulo.lower())
        color = f' {color_match.group(1)}' if color_match else ''
        sec_desc = (f"Refrigerante/anticongelante{color} para {titulo}. "
                    f"{'Presentación de ' + qty + '. ' if qty else ''}Protege el sistema de enfriamiento contra corrosión, congelación y sobrecalentamiento.\n\n"
                    f"Compatible con sistemas de enfriamiento de vehículos europeos. Verificar si es concentrado (mezclar 50/50) o listo para usar.\n\n"
                    f"Marca {marca}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Verifica el tipo de refrigerante recomendado por el fabricante de tu vehículo."},
               {"pregunta": "¿Se mezcla con agua?",
                "respuesta": "Si es concentrado, mezclar 50/50 con agua destilada. Si es listo para usar, aplicar directamente."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]
        abc = "Verifica en el listado la compatibilidad con tu vehículo antes de comprar. Si tienes dudas, escríbenos."

    elif cat == 'enfriador_aceite':
        sec_desc = (f"Enfriador de aceite para {titulo}. "
                    f"Intercambia calor entre el aceite del motor y el refrigerante para mantener la temperatura óptima del lubricante, prolongando su vida útil y protegiendo el motor.\n\n"
                    f"Reemplazo directo del enfriador original.\n\nMarca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si mi enfriador de aceite está fallando?",
                "respuesta": "Síntomas: aceite con aspecto lechoso (mezcla con refrigerante), pérdida de refrigerante sin fuga externa, aceite sucio más rápido de lo normal."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'bomba_aceite':
        sec_desc = (f"Bomba de aceite para {titulo}. "
                    f"Genera la presión de lubricación que circula el aceite por todos los conductos del motor para lubricar cojinetes, árbol de levas, cadena de distribución y demás componentes internos.\n\n"
                    f"Reemplazo directo de la bomba original.\n\nMarca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma familia de motor con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si la bomba de aceite está fallando?",
                "respuesta": "Síntomas: luz de presión de aceite encendida, presión de aceite baja según medidor, ruido de traqueteo metálico del motor, especialmente al arranque."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'bomba_gasolina':
        sec_desc = (f"Bomba de gasolina para {titulo}. "
                    f"Suministra el combustible desde el tanque hasta el riel de inyectores a la presión requerida por el sistema de inyección directa o multipunto.\n\n"
                    f"Reemplazo directo de la bomba original.\n\nMarca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si mi bomba de gasolina está fallando?",
                "respuesta": "Síntomas: motor que no arranca, pérdida de potencia a alta velocidad, motor que se apaga, consumo irregular, ruido de zumbido desde el tanque."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'reten':
        sec_desc = (f"Retén/sello de aceite para {titulo}. "
                    f"Sello de labio que evita fugas de aceite en los puntos de salida de ejes rotativos del motor (cigüeñal, árbol de levas, etc.).\n\n"
                    f"Reemplazo directo del retén original.\n\nMarca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si mi retén está fallando?",
                "respuesta": "Síntomas: fuga de aceite en la parte frontal o trasera del motor (retén de cigüeñal) o alrededor del árbol de levas, manchas de aceite debajo del vehículo."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'valvula_pcv':
        sec_desc = (f"Válvula PCV (ventilación del cárter) para {titulo}. "
                    f"Controla la ventilación de los gases del cárter hacia el múltiple de admisión, evitando presión interna excesiva y reduciendo emisiones.\n\n"
                    f"Reemplazo directo. Instalación directa.\n\nMarca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si la válvula PCV está fallando?",
                "respuesta": "Síntomas: mayor consumo de aceite, humo azul por el escape, filtro de aire contaminado con aceite, ralentí inestable, mayor consumo de combustible."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'valvula_vvt':
        sec_desc = (f"Válvula/solenoide de control VVT/VANOS para {titulo}. "
                    f"Controla el flujo de aceite que ajusta dinámicamente el avance del árbol de levas según las condiciones de operación del motor para optimizar potencia y eficiencia.\n\n"
                    f"Reemplazo directo del solenoide original.\n\nMarca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si el solenoide VVT está fallando?",
                "respuesta": "Síntomas: luz Check Engine (códigos P0010-P0015), ralentí inestable, pérdida de potencia, traqueteo al arrancar, mayor consumo."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'valvula_turbo':
        sec_desc = (f"Válvula de turbo/bypass para {titulo}. "
                    f"Regula la presión del turbo descargando el exceso de presión para proteger el compresor y mantener la presión de sobrealimentación dentro del rango correcto.\n\n"
                    f"Reemplazo directo de la válvula original.\n\nMarca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si la válvula de turbo está fallando?",
                "respuesta": "Síntomas: pérdida de presión de turbo, Check Engine, ruido inusual al soltar el acelerador, falta de potencia."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'valvula_motor':
        sec_desc = (f"Válvula de motor (admisión/escape) para {titulo}. "
                    f"Componente del tren de válvulas que controla la entrada de mezcla aire-combustible y la salida de gases de escape de la cámara de combustión.\n\n"
                    f"Reemplazo directo. La instalación requiere trabajo de culata.\n\nMarca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma familia de motor con tu VIN antes de comprar."},
               {"pregunta": "¿Qué incluye el producto?",
                "respuesta": "Se incluyen las válvulas indicadas en el título."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat in ('valvula_aceite', 'valvula_egr', 'valvula_general'):
        nombre_v = 'EGR (recirculación de gases de escape)' if cat == 'valvula_egr' else 'de control de aceite' if cat == 'valvula_aceite' else ''
        sec_desc = (f"Válvula {nombre_v} para {titulo}. "
                    f"{'Recircula gases de escape hacia la admisión para reducir emisiones de NOx.' if cat == 'valvula_egr' else 'Componente del sistema de control del motor.'}\n\n"
                    f"Reemplazo directo de la válvula original.\n\nMarca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Qué incluye el producto?", "respuesta": "Se incluye la válvula indicada en el título."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat in ('tensor_distribucion', 'tensor'):
        tipo_t = 'de cadena de distribución' if cat == 'tensor_distribucion' else 'de correa de accesorios'
        sec_desc = (f"Tensor {tipo_t} para {titulo}. "
                    f"Mantiene la tensión correcta de la {'cadena' if cat == 'tensor_distribucion' else 'correa'} para evitar saltos de tiempo o deslizamiento.\n\n"
                    f"Reemplazo directo del tensor original.\n\nMarca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma familia de motor con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si el tensor está fallando?",
                "respuesta": f"Síntomas: {'traqueteo de cadena al arrancar, luz de motor encendida, código de falla de timing' if cat == 'tensor_distribucion' else 'chirriado de correa, desgaste prematuro de correa'}."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'cadena_distribucion':
        sec_desc = (f"Cadena de distribución para {titulo}. "
                    f"Sincroniza la rotación del cigüeñal con el árbol (o árboles) de levas para mantener el tiempo correcto de apertura y cierre de válvulas.\n\n"
                    f"Reemplazo directo. Se recomienda cambiar tensores y guías al mismo tiempo.\n\n"
                    f"Marca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma familia de motor con tu VIN antes de comprar."},
               {"pregunta": "¿Cuándo se debe cambiar la cadena de distribución?",
                "respuesta": "Las cadenas de distribución son de larga duración pero fallan cuando los tensores se desgastan. Síntomas de cadena estirada: traqueteo al arrancar, pérdida de potencia, Check Engine con códigos de timing."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'guia_cadena':
        sec_desc = (f"Guía de cadena de distribución para {titulo}. "
                    f"Mantiene la trayectoria correcta de la cadena de distribución, reduciendo el desgaste y el ruido.\n\n"
                    f"Reemplazo directo. Se recomienda cambiar junto con tensores y cadena.\n\n"
                    f"Marca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma familia de motor con tu VIN antes de comprar."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'kit_distribucion':
        sec_desc = (f"Kit de distribución para {titulo}. "
                    f"Incluye todos los componentes necesarios para el reemplazo completo del sistema de distribución: cadena(s) o correa, tensores, guías y poleas.\n\n"
                    f"Instalar todos los componentes del kit al mismo tiempo para garantizar la sincronización y vida útil correctas.\n\n"
                    f"Marca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma familia de motor con tu VIN antes de comprar."},
               {"pregunta": "¿Qué incluye el kit?",
                "respuesta": "Incluye los componentes indicados en el título. Verificar el contenido exacto en la descripción."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'correa':
        es_dist = 'distribuc' in titulo.lower() or 'tiempo' in titulo.lower()
        sec_desc = (f"Correa {'de distribución' if es_dist else 'de accesorios'} para {titulo}. "
                    f"{'Sincroniza el cigüeñal con el árbol de levas para el correcto tiempo de válvulas.' if es_dist else 'Acciona los sistemas de accesorios del motor: alternador, A/C, bomba de dirección.'}\n\n"
                    f"Reemplazo directo. {'Se recomienda cambiar tensor y polea al mismo tiempo.' if es_dist else 'Inspeccionar tensor y poleas al reemplazar.'}\n\n"
                    f"Marca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cada cuánto se cambia?",
                "respuesta": f"{'Cambiar según el intervalo del fabricante, generalmente entre 60,000-100,000 km.' if es_dist else 'Inspeccionar cada 40,000-60,000 km o al aparecer grietas o desgaste visible.'}"},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'polea':
        sec_desc = (f"Polea de motor para {titulo}. "
                    f"Componente del sistema de transmisión por correa que guía, tensa o acciona los accesorios del motor.\n\n"
                    f"Reemplazo directo de la polea original.\n\nMarca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si la polea está fallando?",
                "respuesta": "Síntomas: chirriado o traqueteo en el área del motor, correa que sale del recorrido, vibración, rodamiento de la polea con juego."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'turbo':
        sec_desc = (f"Turbocompresor para {titulo}. "
                    f"Comprime el aire de admisión usando los gases de escape para aumentar la densidad del aire que entra al motor, "
                    f"incrementando potencia y eficiencia sin aumentar la cilindrada.\n\n"
                    f"Reemplazo directo del turbo original. Se recomienda cambiar el aceite y el filtro al instalar un turbo nuevo.\n\n"
                    f"Marca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma número de motor con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si mi turbo está fallando?",
                "respuesta": "Síntomas: pérdida notable de potencia, humo azul o negro por el escape, consumo excesivo de aceite, ruido de silbido o chirrido del turbo, Check Engine."},
               {"pregunta": "¿Qué cuidados requiere el turbo nuevo?",
                "respuesta": "Cambiar aceite y filtro antes de instalar. Al arrancar, dejar que el motor caliente 2 minutos antes de acelerar para que el aceite lubrique el turbo."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'intercooler':
        sec_desc = (f"Intercooler para {titulo}. "
                    f"Enfría el aire comprimido por el turbocompresor antes de que entre al motor. El aire más frío es más denso, lo que aumenta la cantidad de oxígeno disponible para la combustión.\n\n"
                    f"Reemplazo directo del intercooler original.\n\nMarca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si mi intercooler está fallando?",
                "respuesta": "Síntomas: pérdida de potencia del turbo, mayor temperatura de admisión, fuga de aceite por el intercooler (del turbo), pérdida de presión de sobrealimentación."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'arbol_levas':
        sec_desc = (f"Árbol de levas para {titulo}. "
                    f"Controla la apertura y cierre de las válvulas de admisión y/o escape del motor según el perfil de sus levas, sincronizado con el cigüeñal mediante la cadena de distribución.\n\n"
                    f"Reemplazo directo. La instalación requiere sincronización precisa del motor.\n\n"
                    f"Marca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma número de motor con tu VIN antes de comprar."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'tapa_valvulas':
        sec_desc = (f"Tapa de válvulas (tapa de puntería) para {titulo}. "
                    f"Cubre y protege el mecanismo de válvulas en la parte superior de la culata, conteniendo el aceite de lubricación.\n\n"
                    f"Reemplazo directo. Se recomienda cambiar la junta de tapa al mismo tiempo.\n\n"
                    f"Marca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Qué incluye el producto?",
                "respuesta": "Se incluye la tapa de válvulas. Verificar en el listado si incluye junta/empaque."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'soporte_motor':
        sec_desc = (f"Soporte de motor (mount) para {titulo}. "
                    f"Fija el motor/transmisión a la carrocería absorbiendo las vibraciones y torques del motor para aislarlos de la cabina.\n\n"
                    f"Reemplazo directo del soporte original.\n\nMarca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si mi soporte de motor está fallando?",
                "respuesta": "Síntomas: vibración excesiva en la cabina especialmente al ralentí, golpe al meter reversa o al acelerar, movimiento visible del motor."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'metal_motor':
        sec_desc = (f"Metales de motor (cojinetes de bancada/biela) para {titulo}. "
                    f"Superficies de deslizamiento que soportan el cigüeñal y las bielas, lubricadas por la presión de aceite del motor.\n\n"
                    f"Reemplazo directo. La instalación requiere trabajo de motor interno y verificación de tolerancias.\n\n"
                    f"Marca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma número de motor y medida con tu VIN antes de comprar."},
               {"pregunta": "¿Qué medidas incluye?",
                "respuesta": "Verificar en el listado si son medida estándar o sobremedida (0.25mm, 0.50mm, etc.)."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'culata':
        sec_desc = (f"Culata (cabeza de motor) para {titulo}. "
                    f"Componente que cierra la parte superior del bloque, contiene las cámaras de combustión, los árboles de levas, las válvulas y los conductos de admisión y escape.\n\n"
                    f"Reemplazo directo. La instalación requiere maquinado y torque de precisión.\n\n"
                    f"Marca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma número de motor con tu VIN antes de comprar."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat in ('piston', 'ciguenial'):
        nom = 'Pistón' if cat == 'piston' else 'Cigüeñal'
        sec_desc = (f"{nom} para {titulo}. "
                    f"Componente interno del motor de alto precisión. La instalación requiere trabajo especializado de motor.\n\n"
                    f"Marca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma número de motor y medida con tu VIN antes de comprar."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'multiple':
        tipo_mul = 'admisión' if 'admision' in titulo.lower() else 'escape' if 'escape' in titulo.lower() else 'de motor'
        sec_desc = (f"Múltiple de {tipo_mul} para {titulo}. "
                    f"{'Distribuye la mezcla aire-combustible a cada cilindro del motor.' if tipo_mul == 'admisión' else 'Colecta los gases de escape de cada cilindro hacia el sistema de escape.'}\n\n"
                    f"Reemplazo directo del múltiple original.\n\nMarca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    else:  # filtro_aceite, aceite_motor, tapa_aceite, tapa_distribucion, tapa_general, tubo_agua, soporte_transmision, herramienta, engrane, tapon, liga, sensor_motor, kit_motor, motor_general
        sec_desc = (f"{titulo}. Componente del sistema de motor para vehículos europeos.\n\n"
                    f"Reemplazo directo del componente original. Instalación directa.\n\n"
                    f"Marca {marca}, con {gar_txt} contra defectos de fabricación.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Qué incluye el producto?", "respuesta": "Se incluye la pieza indicada en el título."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

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
        "shopify_type": "Motor",
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

with open('output/refacciones_motor_batch_result.json', 'w', encoding='utf-8') as f:
    json.dump({"resultados": resultados}, f, ensure_ascii=False, indent=2)

print(f"Generados: {len(resultados)} productos")
print(f"SKUs únicos: {len(seen_skus)}, con duplicados: {sum(1 for v in seen_skus.values() if v > 1)}")
print()
print("Top categorías:")
from collections import Counter
for cat, n in sorted(cat_counts.items(), key=lambda x: -x[1])[:25]:
    print(f"  {cat}: {n}")
print()
print("Tags:")
tag_counts = Counter()
for r in resultados:
    for tag in r['shopify_tags'].split(', '):
        if tag: tag_counts[tag] += 1
for tag, n in tag_counts.most_common():
    print(f"  {tag}: {n}")
