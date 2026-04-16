import json
import unicodedata
import re

with open('output/refacciones_frenos_batch.json', encoding='utf-8') as f:
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
    if 'balata' in t or 'pastilla' in t:
        if 'estacionamiento' in t or 'mano' in t or 'parking' in t:
            return 'balata_estacionamiento'
        if 'trasera' in t or 'trasero' in t:
            return 'balata_trasera'
        if 'delantera' in t or 'delantero' in t:
            return 'balata_delantera'
        return 'balata'
    if 'zapata' in t:
        return 'zapata'
    if 'disco' in t and ('freno' in t or 'brake' in t):
        if 'trasera' in t or 'trasero' in t:
            return 'disco_trasero'
        if 'delantera' in t or 'delantero' in t:
            return 'disco_delantero'
        return 'disco'
    if 'sensor' in t and 'abs' in t:
        if 'delantero' in t or 'delantera' in t:
            return 'sensor_abs_delantero'
        if 'trasero' in t or 'trasera' in t:
            return 'sensor_abs_trasero'
        return 'sensor_abs'
    if 'sensor' in t and ('desgaste' in t or 'wear' in t):
        return 'sensor_desgaste'
    if 'sensor' in t and ('velocidad' in t or 'rueda' in t or 'speed' in t):
        return 'sensor_velocidad_rueda'
    if 'sensor' in t and ('presion' in t or 'presión' in t):
        return 'sensor_presion'
    if 'sensor' in t and 'freno' in t:
        return 'sensor_desgaste'
    if 'interruptor' in t and ('freno' in t or 'luz' in t):
        return 'interruptor_freno'
    if 'caliper' in t or 'mordaza' in t or 'pinza' in t:
        return 'caliper'
    if 'cilindro' in t and ('rueda' in t or 'freno' in t):
        return 'cilindro_rueda'
    if 'bomba' in t and ('freno' in t or 'maestro' in t or 'maestra' in t):
        return 'bomba_freno'
    if 'servo' in t or 'buster' in t or 'amplificador' in t or ('valvula' in t and 'vacio' in t and 'booster' in t):
        return 'servofreno'
    if 'valvula' in t and 'vacio' in t:
        return 'valvula_vacio'
    if 'manguera' in t and 'freno' in t:
        return 'manguera_freno'
    if 'cable' in t and 'freno' in t:
        return 'cable_freno'
    if 'actuador' in t and 'freno' in t:
        return 'actuador_freno'
    if 'kit' in t and 'freno' in t:
        return 'kit_freno'
    if 'freno' in t and ('estacionamiento' in t or 'mano' in t or 'parking' in t):
        return 'freno_estacionamiento'
    if 'sensor' in t and 'angulo' in t:
        return 'sensor_angulo'
    return 'freno_general'

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
    if numero_parte:
        extras.append(f"número de parte {numero_parte}")
    if codigo_oem:
        extras.append(f"código OEM {codigo_oem}")
    if extras:
        abc += f" También puedes verificar con el {' o '.join(extras)}."

    envio = "Tenemos stock disponible para entrega inmediata. Enviamos el mismo dia de tu pago a Ciudad de Mexico y a todo el pais via DHL o FedEx."

    dev = ("Aceptamos devoluciones dentro de los 30 días posteriores a la entrega, sin importar el motivo. "
           "Para que tu devolución proceda, la pieza debe estar sin uso, sin instalar y en su empaque original.\n\n"
           "Asegura el ajuste perfecto: Una vez realizada tu compra, un asesor te contactará brevemente para validar "
           "la compatibilidad con tu número VIN y garantizar que recibas exactamente lo que tu auto necesita.\n\n"
           "Consulta nuestra politica completa aquí")

    # --- Content by category ---
    if cat in ('balata_delantera', 'balata_trasera', 'balata', 'balata_estacionamiento'):
        pos = 'delanteras' if cat == 'balata_delantera' else 'traseras' if cat == 'balata_trasera' else \
              'de estacionamiento' if cat == 'balata_estacionamiento' else ''
        # Check for ceramic/sport indicators
        tipo_mat = ''
        if 'ceramica' in titulo.lower() or 'ceramic' in titulo.lower():
            tipo_mat = ' cerámicas'
        elif 'sport' in titulo.lower() or 'performance' in titulo.lower():
            tipo_mat = ' de alto rendimiento'

        # Qty in kit
        qty_match = re.search(r'(?:kit\s+)?(\d+)\s+balatas?', titulo.lower())
        qty_txt = f"Juego de {qty_match.group(1)} balatas" if qty_match else "Balatas"

        sec_desc = (
            f"{qty_txt}{tipo_mat} de freno {pos} para {titulo}. "
            f"La pastilla de freno presiona contra el disco para generar la fricción que detiene el vehículo. "
            f"{'Compuesto cerámico de baja generación de polvo y operación silenciosa.' if 'ceramic' in tipo_mat else 'Compuesto de fricción balanceado para frenado progresivo y baja generación de polvo.'}\n\n"
            f"Instalación directa como reemplazo de las balatas originales. Se recomienda revisar y/o tornear los discos al cambiar balatas.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos son compatibles estas balatas?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": f"Se incluye el juego de balatas {pos} como se indica en el título. Generalmente incluye hardware de instalación (clips y pines)."},
            {"pregunta": "¿Cada cuánto se deben cambiar las balatas?",
             "respuesta": "Se recomienda inspección cada 20,000-30,000 km. Cambiar cuando el espesor sea menor a 3 mm o al escuchar chirrido metálico al frenar."},
            {"pregunta": "¿Se deben cambiar los discos también?",
             "respuesta": "No es obligatorio, pero se recomienda revisar el grosor y condición del disco. Si está desgastado o con ranuras profundas, cambiar ambos al mismo tiempo."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'zapata':
        sec_desc = (
            f"Zapatas de freno para {titulo}. "
            f"Sistema de freno de tambor — la zapata presiona el interior del tambor para generar la fricción que detiene el vehículo.\n\n"
            f"Instalación directa como reemplazo de las zapatas originales.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos son compatibles?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye el juego de zapatas de freno."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat in ('disco_delantero', 'disco_trasero', 'disco'):
        pos = 'delantero' if cat == 'disco_delantero' else 'trasero' if cat == 'disco_trasero' else ''
        # Check for ventilated/solid
        ventilado = 'ventilado' if 'ventilado' in titulo.lower() else ''
        # Detect diameter
        diam_match = re.search(r'(\d{2,3})\s*mm', titulo.lower())
        diam = f"{diam_match.group(1)} mm" if diam_match else ''

        sec_desc = (
            f"Disco de freno {pos}{' ventilado' if ventilado else ''}{', ' + diam if diam else ''} para {titulo}. "
            f"El disco {'ventilado' if ventilado else 'sólido'} sobre el que actúan las balatas para detener el vehículo mediante fricción. "
            f"{'El diseño ventilado disipa el calor con mayor eficiencia reduciendo el fade en frenadas repetidas.' if ventilado else ''}\n\n"
            f"Instalación directa como reemplazo del disco original. Se recomienda cambiar balatas al renovar discos.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible este disco?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": f"Se incluye {'el par de discos' if 'par' in titulo.lower() else 'el disco individual'} como se indica en el título."},
            {"pregunta": "¿Cuándo se deben cambiar los discos de freno?",
             "respuesta": "Cambiar cuando el espesor esté por debajo del mínimo grabado en el disco, presenten rayaduras profundas, deformación (pulsación al frenar), o al cambiar balatas si están desgastados."},
            {"pregunta": "¿Se deben cambiar las balatas también?",
             "respuesta": "Se recomienda cambiar balatas y discos al mismo tiempo para garantizar frenado parejo y máxima vida útil."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat in ('sensor_abs_delantero', 'sensor_abs_trasero', 'sensor_abs'):
        pos = 'delantero' if cat == 'sensor_abs_delantero' else 'trasero' if cat == 'sensor_abs_trasero' else ''
        lado_match = re.search(r'(izquierdo|derecho|izq|der)', titulo.lower())
        lado = lado_match.group(1) if lado_match else ''
        sec_desc = (
            f"Sensor ABS {pos}{' ' + lado if lado else ''} para {titulo}. "
            f"Sensor de velocidad de rueda que informa al módulo ABS la velocidad individual de cada rueda para evitar el bloqueo durante el frenado de emergencia.\n\n"
            f"Instalación directa como reemplazo del sensor original. Plug & play — conector directo al arnés original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible este sensor?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Cómo sé si mi sensor ABS está fallando?",
             "respuesta": "Síntomas: luz ABS encendida en el tablero, luz ESP/ESC activa, pérdida de la función ABS (las ruedas se bloquean al frenar fuerte). Escanear con OBD2 para confirmar el código C00XX."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye el sensor ABS con su conector. Verifica en el listado si incluye cable o anillo tónico (reluctor)."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat in ('sensor_desgaste', 'sensor_velocidad_rueda'):
        es_desgaste = cat == 'sensor_desgaste'
        sec_desc = (
            f"{'Sensor de desgaste de balatas' if es_desgaste else 'Sensor de velocidad de rueda'} para {titulo}. "
            f"{'Activa la luz de advertencia de frenos en el tablero cuando las balatas llegan al límite mínimo de desgaste.' if es_desgaste else 'Monitorea la velocidad de la rueda para los sistemas ABS, ESP y control de tracción.'}\n\n"
            f"Instalación directa como reemplazo del sensor original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye el sensor como se indica en el título."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'sensor_presion':
        sec_desc = (
            f"Sensor de presión de frenos para {titulo}. "
            f"Monitorea la presión hidráulica del circuito de frenos e informa al sistema ABS/ESP para optimizar la distribución de frenada.\n\n"
            f"Instalación directa como reemplazo del sensor original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Cómo sé si el sensor de presión de frenos está fallando?",
             "respuesta": "Síntomas: luz ABS o ESP encendida, códigos de falla relacionados con presión hidráulica, comportamiento errático del ABS."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'interruptor_freno':
        sec_desc = (
            f"Interruptor de luz de freno para {titulo}. "
            f"Activa las luces de stop al presionar el pedal de freno. También interactúa con el control de crucero y el sistema de encendido push-button.\n\n"
            f"Instalación directa como reemplazo del interruptor original. Plug & play.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Cómo sé si mi interruptor de freno está fallando?",
             "respuesta": "Síntomas: luces de stop que no encienden al frenar, control de crucero que no funciona, luz de check engine o ABS encendida, auto que no arranca con botón de arranque."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'caliper':
        lado_match = re.search(r'(izquierdo|derecho|izq|der)', titulo.lower())
        lado = lado_match.group(1) if lado_match else ''
        pos = 'delantero' if 'delant' in titulo.lower() else 'trasero' if 'trase' in titulo.lower() else ''
        sec_desc = (
            f"Caliper (mordaza) de freno {pos}{' ' + lado if lado else ''} para {titulo}. "
            f"Aloja los pistones hidráulicos que presionan las balatas contra el disco de freno al accionar el pedal.\n\n"
            f"Reemplazo directo del caliper original. Se recomienda purgar el sistema de frenos tras la instalación.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye el caliper como unidad individual. Las balatas y el disco se venden por separado."},
            {"pregunta": "¿Cómo sé si mi caliper está fallando?",
             "respuesta": "Síntomas: vehículo que jala hacia un lado al frenar, recalentamiento excesivo de una rueda, pérdida de líquido de frenos, pedal esponjoso o que va al piso."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'bomba_freno':
        sec_desc = (
            f"Bomba de frenos (cilindro maestro) para {titulo}. "
            f"Genera la presión hidráulica que activa los calipers y cilindros de rueda al presionar el pedal de freno.\n\n"
            f"Reemplazo directo del cilindro maestro original. Purgar el sistema de frenos tras la instalación.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Cómo sé si mi cilindro maestro está fallando?",
             "respuesta": "Síntomas: pedal de freno esponjoso o que llega al piso, frenado inconsistente, pérdida de líquido de frenos en el depósito, luz de freno encendida."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'servofreno':
        sec_desc = (
            f"Servofreno (booster) para {titulo}. "
            f"Amplifica la fuerza ejercida en el pedal de freno mediante vacío del motor, reduciendo el esfuerzo necesario para frenar.\n\n"
            f"Reemplazo directo del servofreno original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Cómo sé si mi servofreno está fallando?",
             "respuesta": "Síntomas: pedal de freno muy duro (requiere mucha fuerza), vehículo que no frena correctamente, ruido de silbido o chirrido al presionar el pedal."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'valvula_vacio':
        sec_desc = (
            f"Válvula de vacío del booster de frenos para {titulo}. "
            f"Regula el vacío que alimenta el servofreno para asistir el pedal de freno.\n\n"
            f"Reemplazo directo del componente original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye la válvula de vacío individual."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'manguera_freno':
        sec_desc = (
            f"Manguera de freno para {titulo}. "
            f"Conduce el líquido de frenos a presión desde la línea rígida al caliper, permitiendo el movimiento de la suspensión.\n\n"
            f"Reemplazo directo de la manguera original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Cómo sé si mi manguera de freno está fallando?",
             "respuesta": "Síntomas: hinchazón visible en la manguera, fuga de líquido de frenos, pedal esponjoso, caliper que no libera (manguera colapsada internamente)."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'cable_freno':
        sec_desc = (
            f"Cable de freno para {titulo}. "
            f"Cable de acero que transmite la fuerza del freno de mano/estacionamiento hasta los frenos traseros.\n\n"
            f"Reemplazo directo del cable original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye el cable de freno indicado en el título."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'freno_estacionamiento':
        sec_desc = (
            f"Freno de estacionamiento (freno de mano) para {titulo}. "
            f"Sistema que mantiene el vehículo fijo cuando está estacionado, actuando mecánicamente sobre los frenos traseros.\n\n"
            f"Reemplazo directo del componente original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el producto?",
             "respuesta": "Se incluye la pieza indicada en el título."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'actuador_freno':
        sec_desc = (
            f"Actuador de freno de estacionamiento eléctrico (EPB) para {titulo}. "
            f"Motor eléctrico que acciona el freno de estacionamiento electrónico del vehículo.\n\n"
            f"Reemplazo directo del actuador original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Cómo sé si mi actuador EPB está fallando?",
             "respuesta": "Síntomas: luz de freno de estacionamiento parpadeante, freno que no libera o no activa, mensaje de error EPB en el tablero."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'sensor_angulo':
        sec_desc = (
            f"Sensor de ángulo de giro (sensor de dirección) para {titulo}. "
            f"Mide el ángulo y la velocidad de giro del volante para los sistemas de estabilidad ESP/ESC y ABS.\n\n"
            f"Reemplazo directo del sensor original.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Cómo sé si el sensor de ángulo está fallando?",
             "respuesta": "Síntomas: luz ESP/ESC/ABS encendida, comportamiento errático del control de estabilidad, código de falla C00XX o C1281 (varía por marca)."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    elif cat == 'kit_freno':
        sec_desc = (
            f"Kit de frenos para {titulo}. "
            f"Kit completo que incluye los componentes indicados en el título para la renovación del sistema de frenos.\n\n"
            f"Instalar todos los componentes del kit al mismo tiempo para garantizar el funcionamiento correcto del sistema.\n\n"
            f"Marca {marca}, con {gar_txt} contra defectos de fabricación."
        )
        faq = [
            {"pregunta": "¿Para qué vehículos es compatible?",
             "respuesta": f"Compatible con {titulo}. Confirma con tu número de VIN antes de comprar."},
            {"pregunta": "¿Qué incluye el kit?",
             "respuesta": "Incluye los componentes indicados en el título y descripción. Verificar el contenido exacto en el listado."},
            {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}
        ]

    else:  # cilindro_rueda, freno_general
        sec_desc = (
            f"{titulo}. Componente del sistema de frenos para vehículos europeos.\n\n"
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
        "shopify_type": "Frenos",
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

with open('output/refacciones_frenos_batch_result.json', 'w', encoding='utf-8') as f:
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
