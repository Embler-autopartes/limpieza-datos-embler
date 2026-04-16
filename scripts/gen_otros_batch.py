import json
import unicodedata
import re

with open('output/refacciones_otros_batch.json', encoding='utf-8') as f:
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

def get_cat(titulo, subcat):
    t = titulo.lower()
    s = (subcat or '').lower()

    # Filtros
    if 'filtro' in t or s.startswith('filtro'):
        if 'aceite' in t: return 'filtro_aceite'
        if 'aire' in t: return 'filtro_aire'
        if 'cabina' in t or 'habitaculo' in t or 'habitáculo' in t or 'carbon' in t or 'carbón' in t or 'Polen' in titulo: return 'filtro_cabina'
        if 'gasolina' in t or 'combustible' in t or 'fuel' in t: return 'filtro_combustible'
        if 'transmision' in t or 'atf' in t: return 'filtro_transmision'
        if 'diesel' in t: return 'filtro_diesel'
        return 'filtro_general'

    # Sensores de inyección / motor
    if 'sensor' in t:
        if 'oxigeno' in t or 'oxígeno' in t or ' o2' in t or 'lambda' in t or 'sonda' in t: return 'sensor_oxigeno'
        if 'maf' in t or 'flujo' in t and 'aire' in t or 'masa' in t and 'aire' in t: return 'sensor_maf'
        if 'arbol' in t or 'árbol' in t or 'levas' in t or 'camshaft' in t: return 'sensor_arbol'
        if 'ciguenal' in t or 'cigüeñal' in t or 'crank' in t: return 'sensor_ciguenial'
        if 'map' in t or ('presion' in t and 'multiple' in t) or ('presion' in t and 'admision' in t): return 'sensor_map'
        if 'temperatura' in t and ('refrigerante' in t or 'motor' in t or 'agua' in t): return 'sensor_temperatura'
        if 'presion' in t and ('aceite' in t or 'oil' in t): return 'sensor_presion_aceite'
        if 'presion' in t and ('llanta' in t or 'tpms' in t or 'neumatico' in t): return 'sensor_tpms'
        if 'presion' in t and ('ac' in t or 'refrigerant' in t or 'acondicionado' in t): return 'sensor_presion_ac'
        if 'velocidad' in t and ('rueda' in t or 'abs' in t): return 'sensor_abs'
        if 'detonacion' in t or 'knock' in t or 'golpeteo' in t: return 'sensor_detonacion'
        if 'nivel' in t and 'aceite' in t: return 'sensor_nivel_aceite'
        if 'angulo' in t or 'posicion' in t and 'ciguenal' in t: return 'sensor_posicion'
        if 'abs' in t: return 'sensor_abs'
        return 'sensor_general'

    # Válvulas
    if 'valvula' in t or 'válvula' in t:
        if 'egr' in t: return 'valvula_egr'
        if 'pcv' in t or 'ventilacion' in t and 'carter' in t or 'cárter' in t: return 'valvula_pcv'
        if 'mariposa' in t or 'throttle' in t or 'aceleracion' in t: return 'throttle_body'
        if 'turbo' in t or 'wastegate' in t or 'bypass' in t or 'diverter' in t: return 'valvula_turbo'
        if 'vanos' in t or 'vvt' in t or 'valvetronic' in t or 'arbol' in t or 'levas' in t: return 'valvula_vvt'
        return 'valvula_general'

    if 'cuerpo' in t and ('aceleracion' in t or 'mariposa' in t or 'throttle' in t): return 'throttle_body'

    # Inyectores
    if 'inyector' in t: return 'inyector'

    # Bomba de gasolina
    if 'bomba' in t and ('gasolina' in t or 'combustible' in t or 'fuel' in t): return 'bomba_gasolina'

    # Motoventiladores
    if 'motoventilador' in t or ('motor' in t and 'ventilador' in t) or 'electroventilador' in t: return 'motoventilador'
    if 'ventilador' in t and ('radiador' in t or 'enfriamiento' in t or 'electrico' in t or 'motor' in t): return 'motoventilador'

    # Iluminación
    if 'balastra' in t or ('modulo' in t and ('xenon' in t or 'hid' in t or 'led' in t)): return 'balastra'
    if 'faro' in t or 'farol' in t: return 'faro'
    if 'calavera' in t or ('luz' in t and 'trasera' in t): return 'calavera'
    if 'foco' in t or 'bombilla' in t or 'bulbo' in t or ('xenon' in t and 'foco' not in t): return 'bombilla'
    if 'led' in t and ('luz' in t or 'faro' in t or 'placa' in t): return 'bombilla'
    if s.startswith('ilumi'): return 'iluminacion_general'

    # Exterior
    if 'emblema' in t or 'logo' in t or 'insignia' in t: return 'emblema'
    if 'amortiguador' in t and ('cofre' in t or 'capot' in t or 'cajuela' in t or 'maletero' in t): return 'amortiguador_cofre'
    if 'limpiaparabrisas' in t or 'limpia parabrisas' in t or 'limpiador parabrisas' in t: return 'limpiaparabrisas'
    if 'bomba' in t and ('limpiaparabrisas' in t or 'chisguetero' in t or 'washer' in t): return 'bomba_chisguetero'
    if 'tapa' in t and ('deposito' in t or 'depósito' in t) and 'limpiaparabrisas' in t: return 'bomba_chisguetero'
    if 'parrilla' in t or 'rejilla' in t: return 'parrilla'
    if 'espejo' in t or 'retrovisor' in t: return 'espejo'
    if 'salpicadera' in t or 'guardafango' in t: return 'salpicadera'
    if 'manija' in t or 'tirador' in t: return 'manija'
    if 'tapon' in t and ('gasolina' in t or 'tanque' in t): return 'tapon_gasolina'
    if 'antena' in t: return 'antena'
    if 'cofre' in t or 'capo' in t or 'capot' in t: return 'cofre'

    # Habitáculo / habitaculo
    if 'controlador' in t and 'ventana' in t or 'switch' in t and ('ventana' in t or 'vidrio' in t or 'cristal' in t): return 'controlador_ventana'
    if 'botonera' in t or 'control maestro' in t: return 'controlador_ventana'
    if 'relevador' in t or 'rele' in t or 'relay' in t: return 'rele'
    if 'modulo' in t and ('freno' in t or 'actuador' in t): return 'modulo_freno'
    if 'unidad' in t and ('control' in t or 'freno' in t): return 'modulo_freno'

    # Cerraduras
    if s.startswith('cerradura') or 'cerradura' in t or 'chapa' in t: return 'cerradura'
    if 'cierre' in t and ('central' in t or 'puerta' in t): return 'cerradura'
    if 'actuador' in t and ('puerta' in t or 'cerradura' in t): return 'cerradura'

    # Varios
    if 'metal' in t and ('bancada' in t or 'centro' in t or 'estandar' in t): return 'metal_motor'
    if 'rampa' in t or 'riel' in t and 'inyector' in t: return 'rampa_inyectores'
    if 'bateria' in t: return 'bateria'

    return 'general'

def get_shopify_type(cat):
    filtros = {'filtro_aceite','filtro_aire','filtro_cabina','filtro_combustible','filtro_transmision','filtro_diesel','filtro_general'}
    motor = {'sensor_oxigeno','sensor_maf','sensor_arbol','sensor_ciguenial','sensor_map','sensor_temperatura',
             'sensor_presion_aceite','sensor_detonacion','sensor_nivel_aceite','sensor_posicion','sensor_general',
             'valvula_egr','valvula_pcv','valvula_turbo','valvula_vvt','valvula_general','throttle_body',
             'inyector','bomba_gasolina','rampa_inyectores','metal_motor','motoventilador'}
    electrico = {'balastra','bombilla','sensor_tpms','sensor_presion_ac','sensor_abs','controlador_ventana',
                 'rele','modulo_freno','bateria','iluminacion_general'}
    carroceria = {'emblema','amortiguador_cofre','limpiaparabrisas','bomba_chisguetero','parrilla','espejo',
                  'salpicadera','manija','tapon_gasolina','antena','cofre','cerradura','general'}
    iluminacion_type = {'faro','calavera'}
    if cat in filtros: return 'Filtros'
    if cat in motor: return 'Motor'
    if cat in electrico: return 'Sistema Eléctrico'
    if cat in iluminacion_type: return 'Carrocería'
    if cat in carroceria: return 'Carrocería'
    return 'Motor'

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
    cat = get_cat(titulo_raw, subcat)
    shopify_type = get_shopify_type(cat)
    cat_counts[cat] = cat_counts.get(cat, 0) + 1
    type_counts[shopify_type] = type_counts.get(shopify_type, 0) + 1

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
    if cat == 'filtro_aceite':
        sec_desc = (f"Filtro de aceite para {titulo}. Retiene partículas metálicas y contaminantes en suspensión en el aceite del motor, "
                    f"protegiendo superficies de desgaste como cojinetes, árbol de levas y cigüeñal.\n\n"
                    f"Reemplazo directo del filtro original. Se recomienda cambiar junto con el aceite del motor.\n\n"
                    f"Marca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cada cuánto se cambia el filtro de aceite?",
                "respuesta": "Cambiar en cada servicio de aceite, generalmente cada 8,000-15,000 km según el aceite y el vehículo. Consulta el manual de tu auto."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'filtro_aire':
        sec_desc = (f"Filtro de aire para {titulo}. Limpia el aire que entra al motor retirando polvo, insectos y partículas antes de la combustión, "
                    f"protegiendo los componentes internos del motor.\n\n"
                    f"Reemplazo directo del filtro original. Instalación directa en la caja del filtro de aire.\n\n"
                    f"Marca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cada cuánto se cambia el filtro de aire?",
                "respuesta": "Se recomienda revisión cada 20,000-30,000 km o cada año. En zonas con mucho polvo, cambiar con mayor frecuencia."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'filtro_cabina':
        sec_desc = (f"Filtro de cabina (filtro de habitáculo/polen) para {titulo}. Purifica el aire que entra al interior del vehículo "
                    f"reteniendo polvo, polen, esporas y partículas finas que circulan por el sistema de ventilación y A/C.\n\n"
                    f"Reemplazo directo. Se instala en la caja del filtro del sistema de climatización.\n\n"
                    f"Marca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cada cuánto se cambia el filtro de cabina?",
                "respuesta": "Se recomienda cambio cada 15,000-20,000 km o cada año. Si notas olores desagradables o flujo de aire reducido en el A/C, es momento de cambiarlo."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'filtro_combustible':
        sec_desc = (f"Filtro de combustible/gasolina para {titulo}. Retiene impurezas, sedimentos y agua del combustible antes de que lleguen a los inyectores, "
                    f"protegiendo el sistema de inyección.\n\n"
                    f"Reemplazo directo del filtro original.\n\n"
                    f"Marca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cada cuánto se cambia el filtro de gasolina?",
                "respuesta": "Se recomienda cambio cada 30,000-60,000 km. Síntomas de filtro saturado: pérdida de potencia, vacilaciones al acelerar, motor que se apaga."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat in ('filtro_transmision', 'filtro_diesel', 'filtro_general'):
        tipo_f = 'de transmisión' if cat == 'filtro_transmision' else 'diésel' if cat == 'filtro_diesel' else ''
        sec_desc = (f"Filtro {tipo_f} para {titulo}. Componente del sistema de filtración que retiene contaminantes para proteger los mecanismos internos.\n\n"
                    f"Reemplazo directo del filtro original.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'sensor_oxigeno':
        pos_match = re.search(r'(delantero|trasero|anterior|posterior|banco\s*\d|upstream|downstream)', titulo.lower())
        pos = pos_match.group(0) if pos_match else ''
        sec_desc = (f"Sensor de oxígeno (sonda lambda) {pos} para {titulo}. "
                    f"Mide el contenido de oxígeno en los gases de escape para que la ECU ajuste la mezcla aire-combustible en tiempo real, "
                    f"optimizando el rendimiento y reduciendo emisiones.\n\n"
                    f"Instalación directa. Plug & play — conector directo al arnés original.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si mi sensor de oxígeno está fallando?",
                "respuesta": "Síntomas: luz Check Engine (código P013X, P014X, P015X), mayor consumo de combustible, ralentí inestable, humo negro por el escape."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'sensor_maf':
        sec_desc = (f"Sensor MAF (medidor de flujo de masa de aire) para {titulo}. "
                    f"Mide la cantidad de aire que entra al motor para que la ECU calcule la cantidad exacta de combustible a inyectar.\n\n"
                    f"Instalación directa. Plug & play.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si mi sensor MAF está fallando?",
                "respuesta": "Síntomas: Check Engine (código P010X), pérdida de potencia, arranque difícil, mayor consumo, ralentí inestable."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'sensor_arbol':
        sec_desc = (f"Sensor de posición del árbol de levas (CMP) para {titulo}. "
                    f"Informa a la ECU la posición exacta del árbol de levas para sincronizar la inyección y el encendido con precisión.\n\n"
                    f"Instalación directa. Plug & play.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si mi sensor de árbol de levas está fallando?",
                "respuesta": "Síntomas: Check Engine (código P034X o P036X), motor que no arranca, fallas de encendido, consumo elevado."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'sensor_ciguenial':
        sec_desc = (f"Sensor de posición del cigüeñal (CKP) para {titulo}. "
                    f"Mide la posición y velocidad de rotación del cigüeñal para sincronizar la inyección de combustible y el encendido.\n\n"
                    f"Instalación directa. Plug & play.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si el sensor de cigüeñal está fallando?",
                "respuesta": "Síntomas: Check Engine (código P033X), motor que no arranca o arranca difícil, fallas intermitentes de encendido, motor que se apaga en marcha."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'sensor_temperatura':
        sec_desc = (f"Sensor de temperatura del refrigerante (ECT) para {titulo}. "
                    f"Informa a la ECU la temperatura del motor para ajustar la mezcla, el encendido y activar el ventilador de enfriamiento.\n\n"
                    f"Instalación directa. Plug & play.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si el sensor de temperatura está fallando?",
                "respuesta": "Síntomas: temperatura incorrecta en el tablero, ventilador que no activa correctamente, Check Engine (código P011X), arranque difícil en frío."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat in ('sensor_presion_aceite', 'sensor_map', 'sensor_detonacion', 'sensor_nivel_aceite',
                 'sensor_posicion', 'sensor_general', 'sensor_abs'):
        nombres = {
            'sensor_presion_aceite': 'presión de aceite',
            'sensor_map': 'presión del múltiple de admisión (MAP)',
            'sensor_detonacion': 'detonación (knock sensor)',
            'sensor_nivel_aceite': 'nivel de aceite',
            'sensor_posicion': 'posición',
            'sensor_abs': 'velocidad de rueda (ABS)',
            'sensor_general': '',
        }
        nombre = nombres.get(cat, '')
        sec_desc = (f"Sensor {nombre} para {titulo}. "
                    f"Componente electrónico que monitorea el parámetro indicado e informa a la ECU para optimizar el funcionamiento del motor.\n\n"
                    f"Instalación directa. Plug & play — conector directo al arnés original.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si el sensor está fallando?",
                "respuesta": "Síntomas típicos: luz Check Engine encendida con código de falla específico, comportamiento errático del motor o de los sistemas controlados por ese sensor."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat in ('sensor_tpms', 'sensor_presion_ac'):
        nombre = 'presión de llantas (TPMS)' if cat == 'sensor_tpms' else 'presión del sistema de A/C'
        sec_desc = (f"Sensor de {nombre} para {titulo}. "
                    f"Monitorea la presión del sistema indicado e informa al módulo de control correspondiente.\n\n"
                    f"Instalación directa como reemplazo del sensor original.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Qué incluye el producto?",
                "respuesta": "Se incluye el sensor como se indica en el título."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'valvula_egr':
        sec_desc = (f"Válvula EGR (recirculación de gases de escape) para {titulo}. "
                    f"Recircula una porción de los gases de escape hacia el múltiple de admisión para reducir la temperatura de combustión y las emisiones de NOx.\n\n"
                    f"Reemplazo directo de la válvula original.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si mi válvula EGR está fallando?",
                "respuesta": "Síntomas: Check Engine (código P040X), ralentí inestable, humo negro o azulado, pérdida de potencia, mayor consumo de combustible."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'valvula_pcv':
        sec_desc = (f"Válvula PCV (ventilación positiva del cárter) para {titulo}. "
                    f"Regula la ventilación de los gases del cárter hacia el múltiple de admisión, reduciendo emisiones y evitando acumulación de presión en el motor.\n\n"
                    f"Reemplazo directo. Instalación directa.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si mi válvula PCV está fallando?",
                "respuesta": "Síntomas: consumo elevado de aceite, humo azul por el escape, ralentí inestable, filtro de aire contaminado con aceite, mayor consumo de combustible."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'throttle_body':
        sec_desc = (f"Cuerpo de aceleración (mariposa) para {titulo}. "
                    f"Regula la cantidad de aire que entra al motor mediante una mariposa controlada electrónicamente (ETC) o mecánicamente.\n\n"
                    f"Reemplazo directo. Puede requerir calibración con escáner tras la instalación.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Requiere calibración tras instalar?",
                "respuesta": "Sí, los cuerpos de aceleración electrónicos generalmente requieren un procedimiento de calibración (reset TPS) con un escáner OBD2 para que la ECU aprenda la posición de referencia."},
               {"pregunta": "¿Cómo sé si mi cuerpo de aceleración está fallando?",
                "respuesta": "Síntomas: ralentí inestable o muy alto, aceleración brusca o cortada, Check Engine (código P012X o P021X), falta de respuesta del acelerador."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat in ('valvula_turbo', 'valvula_vvt', 'valvula_general'):
        tipo_v = 'de turbo/wastegate' if cat == 'valvula_turbo' else 'de VVT/VANOS' if cat == 'valvula_vvt' else ''
        sec_desc = (f"Válvula {tipo_v} para {titulo}. Componente de control del sistema indicado para optimizar el rendimiento del motor.\n\n"
                    f"Reemplazo directo de la válvula original.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Qué incluye el producto?", "respuesta": "Se incluye la válvula indicada en el título."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'inyector':
        sec_desc = (f"Inyector de combustible para {titulo}. "
                    f"Pulveriza el combustible en la cámara de combustión (o múltiple de admisión) en la cantidad y tiempo exactos determinados por la ECU.\n\n"
                    f"Reemplazo directo del inyector original. Se recomienda cambiar el juego completo cuando uno falla.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Qué incluye el producto?",
                "respuesta": "Verifica en el listado si se vende como inyector individual o como juego completo."},
               {"pregunta": "¿Cómo sé si mi inyector está fallando?",
                "respuesta": "Síntomas: falla de encendido (misfire), Check Engine (código P030X), consumo elevado, humo negro, ralentí inestable o vibración del motor."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'bomba_gasolina':
        sec_desc = (f"Bomba de gasolina para {titulo}. "
                    f"Suministra combustible desde el tanque hasta los inyectores a la presión adecuada para el correcto funcionamiento del sistema de inyección.\n\n"
                    f"Reemplazo directo de la bomba original.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si mi bomba de gasolina está fallando?",
                "respuesta": "Síntomas: motor que no arranca, pérdida de potencia a alta velocidad, motor que se apaga intermitentemente, ruido de zumbido desde el tanque."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'motoventilador':
        sec_desc = (f"Motoventilador (electroventilador) para {titulo}. "
                    f"Motor eléctrico con aspas que fuerza el paso de aire a través del radiador para mantener la temperatura del motor dentro del rango óptimo cuando el vehículo está detenido o a baja velocidad.\n\n"
                    f"Reemplazo directo del motoventilador original. Plug & play.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si mi motoventilador está fallando?",
                "respuesta": "Síntomas: motor que se sobrecalienta en tráfico o al ralentí, ventilador que no activa aunque el motor esté caliente, Check Engine con código de temperatura."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'balastra':
        sec_desc = (f"Balastra (módulo de control) para sistema de iluminación xenón/HID para {titulo}. "
                    f"Regula la corriente eléctrica de alta tensión que alimenta los faros xenón, garantizando encendido estable y larga vida útil del bulbo.\n\n"
                    f"Reemplazo directo de la balastra original.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si mi balastra está fallando?",
                "respuesta": "Síntomas: faro que parpadea, tarda mucho en encender, se apaga solo o no enciende del todo."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'faro':
        lado_match = re.search(r'(izquierdo|derecho|izq|der)', titulo.lower())
        lado = lado_match.group(1) if lado_match else ''
        sec_desc = (f"Faro{' ' + lado if lado else ''} para {titulo}. "
                    f"Conjunto óptico de iluminación delantera que incluye la carcasa, el reflector y el lente.\n\n"
                    f"Instalación directa como reemplazo del faro original. Verificar en el listado si incluye bombilla.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos aplica?",
                "respuesta": f"Aplica para {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Qué incluye el producto?",
                "respuesta": "Se incluye el conjunto del faro. Verificar en el listado si incluye bombillas o solo la carcasa."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'calavera':
        lado_match = re.search(r'(izquierda|derecha|izq|der)', titulo.lower())
        lado = lado_match.group(1) if lado_match else ''
        sec_desc = (f"Calavera (luz trasera){' ' + lado if lado else ''} para {titulo}. "
                    f"Conjunto de luces traseras (freno, direccional, reversa) de reemplazo directo.\n\n"
                    f"Instalación directa. Verificar si incluye arnés o solo la unidad.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos aplica?",
                "respuesta": f"Aplica para {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Qué incluye el producto?",
                "respuesta": "Se incluye el conjunto de calavera indicado. Verificar si incluye bombillas."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'bombilla':
        sec_desc = (f"Bombilla/bulbo de repuesto para {titulo}. "
                    f"Bulbo de reemplazo directo para el sistema de iluminación del vehículo.\n\n"
                    f"Verificar en el listado el tipo de socket y potencia compatible con tu vehículo.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Qué incluye el producto?",
                "respuesta": "Se incluye la bombilla/bulbo indicado en el título."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'iluminacion_general':
        sec_desc = (f"{titulo}. Componente del sistema de iluminación para vehículos europeos.\n\n"
                    f"Reemplazo directo del componente original.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos aplica?",
                "respuesta": f"Aplica para {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Qué incluye el producto?", "respuesta": "Se incluye la pieza indicada en el título."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'emblema':
        sec_desc = (f"{titulo}. Emblema o insignia de carrocería de reemplazo directo.\n\n"
                    f"Fijación mediante adhesivo de doble cara o clips según el modelo. Instalación directa.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos aplica?",
                "respuesta": f"Aplica para {titulo}. Confirma tamaño y modelo con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo se instala?",
                "respuesta": "Limpiar la superficie con alcohol isopropílico antes de aplicar. Usar adhesivo de doble cara incluido o el original del vehículo."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'amortiguador_cofre':
        elem = 'cofre' if 'cofre' in titulo.lower() else 'cajuela' if any(k in titulo.lower() for k in ['cajuela','maletero','baul']) else 'cofre/cajuela'
        sec_desc = (f"Amortiguador de {elem} (pistón de gas) para {titulo}. "
                    f"Sostiene el {elem} abierto mediante presión de gas sin necesidad de varilla de soporte.\n\n"
                    f"Reemplazo directo del pistón original. Instalación directa.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Qué incluye el producto?",
                "respuesta": f"Se incluye {'el par de amortiguadores' if 'par' in titulo.lower() else 'el amortiguador individual'} como se indica en el título."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'limpiaparabrisas':
        pos = 'delantero' if 'delantero' in titulo.lower() else 'trasero' if 'trasero' in titulo.lower() else ''
        sec_desc = (f"Pluma limpiaparabrisas {pos} para {titulo}. "
                    f"Remueve agua, nieve y suciedad del parabrisas para mantener la visibilidad al conducir.\n\n"
                    f"Reemplazo directo del limpiaparabrisas original. Instalación directa sin herramientas.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Qué incluye el producto?",
                "respuesta": f"Se incluye {'el par de plumas' if 'par' in titulo.lower() else 'la pluma individual'} indicada en el título."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'bomba_chisguetero':
        sec_desc = (f"Bomba de agua del limpiaparabrisas (chisguetero) para {titulo}. "
                    f"Suministra el líquido limpiaparabrisas a presión hacia las boquillas del parabrisas.\n\n"
                    f"Reemplazo directo de la bomba original. Instalación directa.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si la bomba está fallando?",
                "respuesta": "Síntomas: no sale líquido al activar los chisgueteros aunque haya líquido en el depósito, flujo débil o irregular."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'controlador_ventana':
        sec_desc = (f"{titulo}. Módulo o interruptor de control de ventanas eléctricas para el sistema de alzavidrios del vehículo.\n\n"
                    f"Reemplazo directo del módulo original. Plug & play.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Cómo sé si el módulo está fallando?",
                "respuesta": "Síntomas: ventanas que no responden al interruptor, funcionamiento errático, ventana que solo funciona con el interruptor de la puerta del copiloto pero no con el maestro."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'modulo_freno':
        sec_desc = (f"{titulo}. Módulo o actuador electrónico del sistema de freno de estacionamiento (EPB) eléctrico.\n\n"
                    f"Reemplazo directo del módulo original. Puede requerir inicialización con escáner especializado.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Requiere programación?",
                "respuesta": "En muchos casos requiere inicialización con herramienta de diagnóstico BMW/Mercedes compatible para activar el módulo nuevo."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'rele':
        sec_desc = (f"Relevador (relay) para {titulo}. "
                    f"Componente electrónico que activa o desactiva circuitos de alta corriente mediante una señal de baja corriente de la ECU o el módulo de control.\n\n"
                    f"Reemplazo directo. Instalación directa en el portafusibles.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Qué incluye el producto?", "respuesta": "Se incluye el relevador indicado en el título."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    elif cat == 'cerradura':
        sec_desc = (f"{titulo}. Componente del sistema de cierre centralizado o cerradura de puerta para vehículos europeos.\n\n"
                    f"Reemplazo directo del componente original.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos es compatible?",
                "respuesta": f"Compatible con {titulo}. Confirma con tu VIN antes de comprar."},
               {"pregunta": "¿Qué incluye el producto?", "respuesta": "Se incluye la pieza indicada en el título."},
               {"pregunta": "¿Tiene garantía?", "respuesta": gar_faq}]

    else:  # general, metal_motor, parrilla, espejo, manija, cofre, etc.
        sec_desc = (f"{titulo}. Refacción o accesorio para vehículos europeos.\n\n"
                    f"Reemplazo directo del componente original.\n\nMarca {marca}, con {gar_txt}.")
        faq = [{"pregunta": "¿Para qué vehículos aplica?",
                "respuesta": f"Aplica para {titulo}. Confirma con tu VIN antes de comprar."},
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

with open('output/refacciones_otros_batch_result.json', 'w', encoding='utf-8') as f:
    json.dump({"resultados": resultados}, f, ensure_ascii=False, indent=2)

print(f"Generados: {len(resultados)} productos")
print(f"SKUs únicos: {len(seen_skus)}, con duplicados: {sum(1 for v in seen_skus.values() if v > 1)}")
print()
print("Top categorías:")
from collections import Counter
for cat, n in sorted(cat_counts.items(), key=lambda x: -x[1])[:20]:
    print(f"  {cat}: {n}")
print()
print("Shopify types:")
for t, n in sorted(type_counts.items(), key=lambda x: -x[1]):
    print(f"  {t}: {n}")
print()
print("Tags:")
tag_counts = Counter()
for r in resultados:
    for tag in r['shopify_tags'].split(', '):
        if tag: tag_counts[tag] += 1
for tag, n in tag_counts.most_common():
    print(f"  {tag}: {n}")
