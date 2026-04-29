"""
Build script para refacciones_motor (4,743 filas).

Tipos: soporte_motor, junta_cabeza, junta_admision, junta_escape, junta_carter, junta_tapa_valvulas,
junta_otra, kit_juntas, multiple_admision, multiple_escape, cadena_tiempo, kit_cadena, tensor, banda,
polea, polea_tensora, bomba_agua, bomba_aceite, bomba_vacio, termostato, turbo, intercooler,
cuerpo_aceleracion, arbol_levas, engrane_levas, valvula_admision, valvula_escape, piston, biela,
reten_sello, filtro_aceite, carter, otro.
"""

import json
import os
import re
import unicodedata
from collections import Counter

HOJA = os.environ.get("EMBLER_HOJA", "ml_con_match")
BATCH_PATH = f"new-output_v2/{HOJA}/refacciones_motor_batch.json"
OUTPUT_PATH = f"new-output_v2/{HOJA}/refacciones_motor_batch_result.json"


SECCION_DEVOLUCIONES = (
    "Aceptamos devoluciones dentro de los 30 días posteriores a la entrega, sin importar el motivo. "
    "Para que tu devolución proceda, la pieza debe estar sin uso, sin instalar y en su empaque original.\n\n"
    "Asegura el ajuste perfecto: Una vez realizada tu compra, un asesor te contactará brevemente "
    "para validar la compatibilidad con tu número VIN y garantizar que recibas exactamente lo que tu auto necesita.\n\n"
    "Consulta nuestra politica completa aquí"
)

REVISION_FIJA = (
    "[INCLUIR] Peso y dimensiones para calculo de envio.\n"
    "[INCLUIR] Fotografias del producto."
)


def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")[:100]


def title_clean(t):
    return t.replace("&", "").rstrip().strip()


def antes_comprar(np, oem):
    base = (
        "Para garantizar que recibas la pieza correcta para tu vehiculo, necesitamos el numero "
        "de serie (VIN) de tu auto antes de procesar el pedido. Esto evita errores, tiempos perdidos "
        "y devoluciones innecesarias. Escribenos y con gusto confirmamos compatibilidad."
    )
    if np and oem and np != oem:
        base += f" Tambien puedes verificar con el numero de parte {np} o codigo OEM {oem}."
    elif np:
        base += f" Tambien puedes verificar con el numero de parte {np}."
    elif oem:
        base += f" Tambien puedes verificar con el codigo OEM {oem}."
    return base


def envio_text(es_kit, es_par):
    base = (
        "Tenemos stock disponible para entrega inmediata. "
        "Enviamos el mismo dia de tu pago a Ciudad de Mexico y a todo el pais via DHL o FedEx."
    )
    if es_par:
        base += " Este producto se vende como par completo."
    elif es_kit:
        base += " Este producto se vende como juego completo."
    return base


def body_html(desc, compat_lista, antes, envio, faqs):
    parrafos = "".join(f"<p>{p.strip()}</p>" for p in desc.split("\n\n") if p.strip())
    compat_html = ""
    if compat_lista.strip():
        items = [l.strip() for l in compat_lista.splitlines() if l.strip()]
        compat_html = "<h2>Compatibilidades</h2><ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"
    faq_html = "<h2>Preguntas Frecuentes</h2>" + "".join(
        f"<h3>{f['pregunta']}</h3><p>{f['respuesta']}</p>" for f in faqs
    )
    devs_html = "<h2>Politica de Devolucion</h2>" + "".join(
        f"<p>{p.strip()}</p>" for p in SECCION_DEVOLUCIONES.split("\n\n") if p.strip()
    )
    return (
        "<h2>Descripcion</h2>" + parrafos + compat_html
        + "<h2>Antes de Comprar</h2><p>" + antes + "</p>"
        + "<h2>Envio</h2><p>" + envio + "</p>"
        + devs_html + faq_html
    )


def marca_pos(marca_norm, marca_raw):
    if marca_norm == "Original Frey":
        return ("Marca Original Frey, importada y especializada en refacciones para vehiculos europeos premium "
                "con calidad equivalente al equipo original (OEM-grade aleman).")
    if marca_norm == "Embler":
        return ("Marca Embler, propia de Embler Autopartes Europeas, especializada en refacciones para BMW, "
                "Mercedes-Benz, Audi, Volkswagen, Porsche, Volvo, Mini Cooper y Jaguar.")
    raw_low = (marca_raw or "").lower()
    if "victor reinz" in raw_low or "elring" in raw_low or "ajusa" in raw_low:
        return (f"Marca {marca_norm or marca_raw}, proveedor OEM aleman de juntas y empaques de motor. "
                "Suministra a la fabrica para BMW, Mercedes, Audi, VW.")
    if "mahle" in raw_low or "behr" in raw_low:
        return (f"Marca {marca_norm or marca_raw}, proveedor OEM aleman de gestion termica del motor. "
                "Suministra a la fabrica para BMW, Mercedes, Audi, VW y otros vehiculos premium.")
    if any(b in raw_low for b in ("pierburg", "vaico", "febi", "corteco", "ina", "ruville")):
        return (f"Marca {marca_norm or marca_raw}, proveedor europeo de refacciones de motor con calidad "
                "aftermarket-OE equivalente al equipo original.")
    if not marca_norm:
        return f"Marca de refaccion: {marca_raw or 'no especificada'}."
    return f"Marca {marca_norm}, fabricante de refacciones para vehiculos europeos."


TIPO_DEFINICIONES = {
    "soporte_motor": {
        "rubro": "soporte (taco) de motor",
        "shopify_type": "Motor",
        "p1": (
            "Soporte (taco) de motor del vehiculo. Es el bloque de caucho-metal que sujeta el motor al "
            "chasis del vehiculo, absorbiendo las vibraciones del motor y manteniendo su alineacion con "
            "la transmision. En vehiculos europeos modernos premium, los soportes pueden ser hidraulicos "
            "(con camara de fluido para amortiguar mejor las vibraciones a baja frecuencia) o "
            "convencionales de caucho-metal solido. Pieza de desgaste tipica: el caucho se cuartea con "
            "los anos y aparecen vibraciones en ralenti, golpes al cambiar de marcha y movimiento "
            "excesivo del motor en aceleracion fuerte."
        ),
        "faq": [
            ("¿Sintomas de soporte de motor dañado?",
             "Vibracion en ralenti (especialmente con caja en D o R), golpes al cambiar de marcha o al "
             "pisar el acelerador, movimiento excesivo del motor al acelerar (visible al ver el motor "
             "moviendose lateralmente), sonido sordo al frenar."),
            ("¿Cambio el de la transmision al mismo tiempo?",
             "Es practica recomendada — los soportes envejecen juntos. Cambiar solo uno deja al otro "
             "como punto debil y la vibracion no desaparece."),
            ("¿Es del lado izquierdo o derecho?",
             "Confirma con el listing — los motores transversales y longitudinales tienen soportes "
             "asimetricos."),
            ("¿Es hidraulico o solido?",
             "Verifica el codigo de parte original. Los hidraulicos tienen la palabra 'hydromount' o "
             "'hidraulico' y son mas costosos. No son intercambiables con los convencionales."),
        ],
    },
    "junta_cabeza": {
        "rubro": "junta de cabeza del motor",
        "shopify_type": "Motor",
        "p1": (
            "Junta de cabeza del motor (head gasket). Es el sello critico entre el block del motor y la "
            "cabeza, manteniendo la estanqueidad de la camara de combustion y separando los conductos de "
            "aceite y refrigerante que cruzan ambos componentes. Las juntas modernas son metaloplasticas "
            "(MLS - Multi Layer Steel) o de fibra reforzada con bordes metalicos en las camaras. Una "
            "falla provoca mezcla de fluidos (aceite con refrigerante, refrigerante en la combustion), "
            "perdida de compresion entre cilindros, sobrecalentamiento del motor o fugas externas."
        ),
        "faq": [
            ("¿Sintomas de junta de cabeza dañada?",
             "Sobrecalentamiento del motor sin causa evidente, perdida progresiva de refrigerante, "
             "humo blanco continuo del escape, lechada en el aceite (mezcla con refrigerante), "
             "compresion baja en uno o mas cilindros, burbujas en el deposito de anticongelante."),
            ("¿Tornillos de cabeza nuevos?",
             "Obligatorio. Los tornillos de cabeza son TTY (torque-to-yield) y se deforman al apretarse "
             "al torque correcto. Reutilizarlos garantiza falla del nuevo sello en pocos kilometros."),
            ("¿Cambio el sello de la tapa de valvulas tambien?",
             "Es practica recomendada — al desarmar la cabeza es momento ideal para reemplazar todos los "
             "sellos asociados (junta de tapa, sellos de bujes, retenes de levas)."),
        ],
    },
    "junta_admision": {
        "rubro": "junta del colector de admision",
        "shopify_type": "Motor",
        "p1": (
            "Junta del colector de admision (intake manifold gasket). Sella la conexion entre el colector "
            "de admision y la cabeza del motor, evitando fugas de aire no medido (false air) que "
            "alterarian la mezcla aire-combustible. Es pieza de desgaste tipica que se reemplaza siempre "
            "que se desmonta el colector. Una junta dañada provoca codigos de mezcla pobre (P0171/P0174), "
            "ralenti irregular y perdida de potencia."
        ),
        "faq": [
            ("¿Cuando se reemplaza?",
             "Siempre que se desmonta el colector de admision. Tambien cuando hay codigos de mezcla pobre "
             "que apuntan a fuga del colector."),
            ("¿Trae los tornillos?",
             "Generalmente no — los tornillos del colector se reutilizan o se compran por separado."),
        ],
    },
    "junta_escape": {
        "rubro": "junta del colector de escape",
        "shopify_type": "Motor",
        "p1": (
            "Junta del colector de escape (exhaust manifold gasket). Sella la conexion entre el colector "
            "de escape y la cabeza del motor, conteniendo los gases de escape calientes (650-900 °C). "
            "Esta fabricada en material refractario (acero inoxidable + fibra ceramica) capaz de soportar "
            "ciclos termicos extremos. Falla tipica: aparece soplido caracteristico (ticking) cuando el "
            "motor esta frio y desaparece al calentarse, o se mantiene constante si la falla es severa."
        ),
        "faq": [
            ("¿Sintomas de junta de escape dañada?",
             "Soplido o tableteo metalico (especialmente en frio), olor a gases de escape en el motor, "
             "humo del compartimento del motor en frio."),
            ("¿Conviene cambiar los tornillos?",
             "Si — los tornillos del escape se oxidan con el calor y frecuentemente se rompen al "
             "desmontar. Considera tornillos nuevos."),
        ],
    },
    "junta_carter": {
        "rubro": "junta de carter de aceite",
        "shopify_type": "Motor",
        "p1": (
            "Junta del carter de aceite (oil pan gasket). Sella el carter (deposito inferior de aceite) "
            "contra el block del motor, evitando fugas de aceite. En vehiculos modernos europeos puede "
            "ser de caucho moldeado, papel reforzado, o sello liquido (RTV) directo. Falla tipica: gotas "
            "de aceite bajo el motor, manchas oscuras en el motor cerca del carter, nivel de aceite que "
            "baja con frecuencia."
        ),
        "faq": [
            ("¿Cuando reemplazar?",
             "Cuando hay fuga visible o de manera preventiva al hacer servicio mayor del motor."),
        ],
    },
    "junta_tapa_valvulas": {
        "rubro": "junta de tapa de valvulas (puntería)",
        "shopify_type": "Motor",
        "p1": (
            "Junta de tapa de valvulas (valve cover gasket, tambien 'tapa de punteria'). Sella la tapa "
            "superior de la cabeza del motor, conteniendo el aceite del sistema de lubricacion del tren "
            "de valvulas. En vehiculos europeos modernos son tipicamente de caucho moldeado integrado en "
            "la tapa o juntas de fibra. Pieza de desgaste muy comun — el caucho se endurece con los anos "
            "y aparecen fugas de aceite caracteristicas (manchas en la tapa, residuos en las bujias en "
            "BMW de 6 cilindros)."
        ),
        "faq": [
            ("¿Sintomas de junta de tapa dañada?",
             "Aceite en el pozo de las bujias (problema critico — daña las bobinas COP), manchas de "
             "aceite en el motor, olor a aceite quemado, codigos de fallo de combustion intermitentes."),
            ("¿Cambio los sellos de los pozos de bujias tambien?",
             "Si — vienen integrados con la junta de tapa de valvulas. Reemplazar todo en conjunto."),
            ("¿Trae los tornillos y arandelas?",
             "Las arandelas de los tornillos pueden tener junta integrada — verifica el listing."),
        ],
    },
    "kit_juntas": {
        "rubro": "kit de juntas de motor",
        "shopify_type": "Motor",
        "p1": (
            "Kit de juntas de motor (engine gasket set). Incluye todas las juntas y empaques del motor "
            "para overhaul completo o parcial: junta de cabeza, sellos de valvula, juntas de admision y "
            "escape, junta de tapa de punterias, juntas de carter y mas segun el alcance del kit. Es la "
            "presentacion economica para una reparacion mayor — comprar todas las juntas por separado "
            "cuesta significativamente mas."
        ),
        "faq": [
            ("¿Que incluye exactamente?",
             "Verifica el listing por el contenido especifico. Algunos kits son 'overhaul completo' "
             "(todas las juntas), otros son 'top end' (solo cabeza y arriba) o 'bottom end' (carter y "
             "abajo)."),
            ("¿Conviene comprar el kit completo?",
             "Si vas a desarmar el motor por mantenimiento mayor, el kit completo es la opcion mas "
             "economica y asegura que no falte ningun sello durante la operacion."),
        ],
    },
    "multiple_admision": {
        "rubro": "colector / multiple de admision",
        "shopify_type": "Motor",
        "p1": (
            "Colector (multiple) de admision del motor. Es el conducto que distribuye el aire de "
            "admision a los cilindros, tipicamente despues del filtro y el cuerpo de aceleracion. En "
            "vehiculos modernos europeos puede ser de aluminio fundido, magnesio (mas ligero) o plastico "
            "compuesto. En BMW M52/M54 integra el sistema DISA de admision variable; en motores TFSI/TSI "
            "integra el bypass y el colector de la valvula PCV. Pieza de reemplazo cuando se daña "
            "internamente (DISA roto, bypass agrietado) o cuando se carbonizan los conductos."
        ),
        "faq": [
            ("¿Sintomas de colector dañado?",
             "Codigos de mezcla pobre (P0171/P0174), ralenti irregular, perdida de potencia, ruido "
             "de aire al acelerar (fuga interna), tableteo del DISA en BMW M52/M54."),
            ("¿Trae las juntas?",
             "Verifica el listing. Algunos colectores vienen con juntas, otros se compran por separado."),
        ],
    },
    "multiple_escape": {
        "rubro": "colector / multiple de escape",
        "shopify_type": "Motor",
        "p1": (
            "Colector (multiple) de escape del motor. Recibe los gases calientes de la combustion desde "
            "cada cilindro y los conduce hacia el catalizador. Esta fabricado en hierro fundido (mas "
            "comun), acero inoxidable (deportivos) o headers tubulares (M, AMG). Pieza de desgaste por "
            "ciclos termicos extremos — falla tipica son grietas en zonas de fatiga, especialmente "
            "comunes en BMW de 6 cilindros."
        ),
        "faq": [
            ("¿Sintomas de colector de escape rajado?",
             "Soplido o tableteo metalico (especialmente en frio), olor a gases del compartimento, perdida "
             "de potencia, codigos de error de banco rico/pobre."),
        ],
    },
    "cadena_tiempo": {
        "rubro": "cadena de tiempo del motor",
        "shopify_type": "Motor",
        "p1": (
            "Cadena de tiempo (timing chain) del motor. Es la cadena metalica que conecta el cigueñal con "
            "los arboles de levas, sincronizando la apertura de las valvulas con el movimiento de los "
            "pistones. A diferencia de la banda de tiempo (timing belt), la cadena no requiere mantenimiento "
            "periodico programado, pero se desgasta con los anos y los kilometros, generando ruido de "
            "tableteo y, en casos graves, saltos de tiempo que dañan valvulas y pistones."
        ),
        "faq": [
            ("¿Sintomas de cadena desgastada?",
             "Ruido tipo tableteo o cascabel del motor (especialmente en frio), codigos de correlacion "
             "de levas (P0008-P0019), perdida de potencia, fallos de combustion."),
            ("¿Cuando reemplazar?",
             "No tiene intervalo fijo, pero cadenas que pasan los 200,000 km o muestran sintomas "
             "de desgaste deben reemplazarse para prevenir saltos catastroficos. En motores BMW N20/N26 "
             "y Mercedes M271 modernos, la cadena ha sido punto debil conocido."),
        ],
    },
    "kit_cadena": {
        "rubro": "kit completo de cadena de tiempo",
        "shopify_type": "Motor",
        "p1": (
            "Kit completo de cadena de tiempo. Incluye cadena, tensor hidraulico, guias deslizantes y "
            "engranes (sprockets) para reemplazo total del sistema de distribucion. Es la opcion "
            "recomendada cuando hay desgaste — cambiar solo la cadena sobre tensores y guias viejos "
            "garantiza un nuevo sintoma en pocos kilometros."
        ),
        "faq": [
            ("¿Que incluye?",
             "Cadena, tensor, guias y, en algunos kits, engranes de levas y bomba de aceite. Verifica "
             "el listing."),
            ("¿Es trabajo complejo?",
             "Si — el reemplazo del kit de cadena requiere desarmar buena parte del frente del motor. "
             "Trabajo de 8-12 horas en taller especializado."),
        ],
    },
    "tensor": {
        "rubro": "tensor de cadena / banda",
        "shopify_type": "Motor",
        "p1": (
            "Tensor (tensioner) hidraulico o mecanico de cadena de tiempo o banda. Mantiene la tension "
            "correcta sobre la cadena/banda, compensando el desgaste y absorbiendo variaciones de carga. "
            "Los tensores hidraulicos usan presion del aceite del motor para mantener la fuerza; los "
            "mecanicos usan resorte. Pieza de desgaste — falla tipica es tableteo de cadena en frio "
            "(tensor sin presion antes de cebarse) que persiste con el motor caliente cuando la falla "
            "es avanzada."
        ),
        "faq": [
            ("¿Sintomas de tensor desgastado?",
             "Tableteo de cadena en frio que mejora al calentarse (caso temprano), tableteo permanente "
             "(caso avanzado), codigos de correlacion de levas."),
            ("¿Cambio el tensor solo o el kit completo?",
             "Si la cadena tiene anos similares, kit completo. Si la cadena es nueva, solo el tensor."),
        ],
    },
    "banda": {
        "rubro": "banda de distribucion / accesorios",
        "shopify_type": "Motor",
        "p1": (
            "Banda (correa) de distribucion (timing belt) o de accesorios (serpentine belt). La de "
            "distribucion sincroniza el cigueñal con los arboles de levas en motores que la usan (algunos "
            "Audi-VW y motores diesel mas viejos). La de accesorios mueve alternador, bomba de "
            "direccion, compresor de A/C y bomba de agua en algunos motores. Las bandas son piezas de "
            "mantenimiento periodico — su rotura puede provocar dano del motor (en distribucion) o "
            "perdida de funciones (en accesorios)."
        ),
        "faq": [
            ("¿Cada cuanto se cambia la banda de distribucion?",
             "Tipicamente entre 90,000 y 150,000 km segun el motor. Consulta el manual."),
            ("¿La banda de accesorios tiene intervalo?",
             "Cada 80,000-100,000 km o cuando aparezcan grietas, peladuras o ruido de chillido."),
        ],
    },
    "polea_tensora": {
        "rubro": "polea tensora",
        "shopify_type": "Motor",
        "p1": (
            "Polea tensora del sistema de banda. Mantiene tension constante sobre la banda de accesorios "
            "(serpentine) o de distribucion, integrada con un tensor automatico (resorte o hidraulico). "
            "Pieza de desgaste tipica — el rodamiento interno se afloja con los anos y aparece chillido o "
            "vibracion al activarse."
        ),
        "faq": [
            ("¿Sintomas de polea tensora dañada?",
             "Chillido del frente del motor, vibracion, banda que se sale o se desgasta prematuramente."),
            ("¿Cambio con la banda?",
             "Si — cambiar tensor + banda es practica estandar."),
        ],
    },
    "polea": {
        "rubro": "polea (cigueñal / accesorios)",
        "shopify_type": "Motor",
        "p1": (
            "Polea del motor (de cigueñal o de accesorios). La polea de cigueñal (harmonic balancer) en "
            "vehiculos modernos integra un amortiguador de vibraciones de torsion (caucho vulcanizado) "
            "que se degrada con los anos. Las poleas de accesorios mueven alternador, bomba de direccion, "
            "compresor de A/C y bomba de agua. Falla tipica: caucho del balanceador agrietado o "
            "desprendido, polea desbalanceada."
        ),
        "faq": [
            ("¿Sintomas de polea de cigueñal dañada?",
             "Vibracion del frente del motor, ruido extraño, banda de accesorios que se sale, en casos "
             "extremos la polea exterior se desprende."),
        ],
    },
    "bomba_agua": {
        "rubro": "bomba de agua",
        "shopify_type": "Motor",
        "p1": (
            "Bomba de agua (water pump) del sistema de refrigeracion del motor. Hace circular el "
            "refrigerante a traves del block, cabeza, radiador, calefactor y demas componentes del "
            "circuito termico. Es accionada por la banda de accesorios, banda de distribucion, o "
            "directamente por la cadena de tiempo segun el motor. Pieza de desgaste — el sello "
            "(seal) interno falla con los anos y aparece fuga de refrigerante por el respiradero "
            "(weep hole) caracteristico."
        ),
        "faq": [
            ("¿Sintomas de bomba dañada?",
             "Fuga de refrigerante por el frente del motor (gota constante en el respiradero), "
             "sobrecalentamiento, ruido de chillido o moledora del frente, perdida progresiva de "
             "refrigerante."),
            ("¿Cuando cambiarla?",
             "Tipicamente cada 100,000-150,000 km. Si el motor tiene cadena de tiempo en el mismo "
             "compartimento (BMW N20/N26, Mercedes M271/M274), conviene cambiar bomba + cadena al mismo "
             "tiempo por costo de mano de obra."),
        ],
    },
    "bomba_aceite": {
        "rubro": "bomba de aceite",
        "shopify_type": "Motor",
        "p1": (
            "Bomba de aceite (oil pump) del motor. Genera la presion del sistema de lubricacion, "
            "enviando aceite filtrado a todos los puntos criticos: bancadas, bielas, arboles de levas, "
            "tensores hidraulicos, etc. Las bombas modernas son de engranes internos o de paletas, "
            "accionadas por el cigueñal directamente o por la cadena de tiempo. Pieza de falla critica "
            "— una bomba dañada provoca dano severo del motor por falta de lubricacion."
        ),
        "faq": [
            ("¿Sintomas de bomba de aceite dañada?",
             "Luz de presion de aceite encendida, lectura baja en el manometro, ruido tipo cascabel "
             "del motor (cojinetes secos), aceite que no llega al tren de valvulas."),
            ("¿Es trabajo complejo?",
             "Si — la bomba esta dentro del carter y requiere desarmar buena parte del fondo del motor."),
        ],
    },
    "bomba_vacio": {
        "rubro": "bomba de vacio",
        "shopify_type": "Motor",
        "p1": (
            "Bomba de vacio (vacuum pump) del motor. Genera vacio para el servofreno (booster) y otros "
            "actuadores neumaticos en motores que no producen vacio suficiente del colector de admision "
            "(diesel, motores turbo modernos). Falla tipica: pedal de freno duro (sin asistencia de "
            "vacio), fugas de aceite por el sello del eje, ruido de chillido."
        ),
        "faq": [
            ("¿Sintomas de bomba de vacio dañada?",
             "Pedal de freno duro, fugas de aceite por el lateral del motor, ruido de chillido. En "
             "diesels modernos puede tambien afectar la EGR y la valvula PCV."),
        ],
    },
    "termostato": {
        "rubro": "termostato del sistema de refrigeracion",
        "shopify_type": "Motor",
        "p1": (
            "Termostato del sistema de refrigeracion del motor. Es la valvula termica que regula el "
            "flujo de refrigerante hacia el radiador segun la temperatura del motor: cerrado en frio "
            "(motor calienta rapido) y abierto en operacion normal (refrigerante circula al radiador). "
            "En motores europeos modernos, el termostato puede ser convencional (cera) o electronico "
            "(controlado por la ECU para optimizar consumo y emisiones). Falla tipica: termostato "
            "atascado abierto (motor que no calienta) o cerrado (sobrecalentamiento)."
        ),
        "faq": [
            ("¿Sintomas de termostato dañado?",
             "Motor que no calienta (termostato abierto), sobrecalentamiento (termostato cerrado), "
             "calefaccion inconsistente, codigos de error del sistema de enfriamiento."),
            ("¿Trae la junta?",
             "Generalmente si — la junta esta integrada o viene en el empaque. Verifica el listing."),
        ],
    },
    "turbo": {
        "rubro": "turbocompresor",
        "shopify_type": "Motor",
        "p1": (
            "Turbocompresor (turbo) del motor. Sobrealimenta la admision aprovechando la energia de los "
            "gases de escape: una turbina en el escape mueve un compresor en la admision a alta "
            "velocidad (hasta 200,000 rpm), comprimiendo el aire que entra al motor para aumentar la "
            "potencia y eficiencia. Los turbos modernos europeos suelen ser twin-scroll o de geometria "
            "variable (VGT) en diesels. Pieza compleja con mantenimiento estricto — fallan tipicamente "
            "por falta de lubricacion, contaminacion del aceite, o fatiga termica de los rodamientos."
        ),
        "faq": [
            ("¿Sintomas de turbo dañado?",
             "Perdida de potencia (especialmente en aceleracion), humo azul/gris del escape (aceite que "
             "se quema), chillido o ruido extraño del turbo, codigos de baja presion de turbo."),
            ("¿Necesito alguna preparacion al instalar?",
             "Si — purgar el sistema de aceite, verificar filtro de aceite nuevo y cambio de aceite "
             "obligatorio. Sin estos pasos el turbo nuevo puede fallar en pocos miles de km."),
            ("¿Trae los empaques?",
             "Verifica el listing — algunos turbos vienen con kit de instalacion (juntas, tornilleria), "
             "otros se compran por separado."),
        ],
    },
    "intercooler": {
        "rubro": "intercooler",
        "shopify_type": "Motor",
        "p1": (
            "Intercooler (intercambiador de calor aire-aire o aire-agua) del sistema de turbocompresion. "
            "Enfria el aire comprimido que sale del turbo antes de entrar al motor, aumentando su "
            "densidad y mejorando la potencia y la eficiencia de la combustion. En vehiculos modernos "
            "europeos puede ser front-mount (delante del radiador) o integrado en el colector de "
            "admision (water-to-air). Pieza vulnerable a impactos por piedras y a obstruccion interna "
            "por aceite del turbo."
        ),
        "faq": [
            ("¿Sintomas de intercooler dañado?",
             "Perdida de potencia, codigos de baja presion de turbo, fugas visibles de aire o aceite, "
             "humo del compartimento."),
        ],
    },
    "cuerpo_aceleracion": {
        "rubro": "cuerpo de aceleracion electronico",
        "shopify_type": "Motor",
        "p1": (
            "Cuerpo de aceleracion electronico (drive-by-wire throttle body). Reemplaza el cuerpo "
            "mecanico tradicional con un sistema en el que el pedal del acelerador es solo un "
            "potenciometro y la apertura de la mariposa la realiza un motor electrico controlado por la "
            "ECU. Permite control preciso de la respuesta del motor, control de traccion y modulacion "
            "automatica para optimizar consumo y emisiones."
        ),
        "faq": [
            ("¿Sintomas de cuerpo dañado?",
             "Vehiculo en modo de emergencia, respuesta erratica del acelerador, ralenti irregular, "
             "codigos P0120-P0124 o P2100-P2106."),
            ("¿Necesita 'aprender' al instalarlo?",
             "Si — la mayoria de los vehiculos europeos requieren adaptacion al ECU con scanner."),
        ],
    },
    "arbol_levas": {
        "rubro": "arbol de levas / engrane de levas",
        "shopify_type": "Motor",
        "p1": (
            "Arbol de levas (camshaft) o engrane del arbol de levas. El arbol de levas controla la "
            "apertura y cierre de las valvulas de admision y escape sincronizado con el cigueñal "
            "atraves de la cadena/banda de tiempo. En motores con VVT/VANOS, los arboles tienen "
            "actuadores hidraulicos en el extremo que ajustan la posicion variable. Pieza de desgaste "
            "moderado — los engranes y los actuadores VVT son los componentes mas afectados con los anos."
        ),
        "faq": [
            ("¿Es el arbol completo o solo el engrane?",
             "Verifica el listing. El arbol completo es pieza estructural que rara vez se reemplaza; "
             "los engranes (incluyendo actuador VVT) son piezas mas comunes de cambio."),
            ("¿Sintomas de engrane VVT dañado?",
             "Codigos de correlacion de levas (P0008-P0019), tableteo del motor, perdida de potencia."),
        ],
    },
    "valvula": {
        "rubro": "valvula del motor",
        "shopify_type": "Motor",
        "p1": (
            "Valvula del motor (admision o escape). Controla el flujo de aire/mezcla hacia la camara de "
            "combustion y de gases de escape hacia el colector. Pieza estructural critica — solo se "
            "reemplaza durante reparacion mayor de la cabeza."
        ),
        "faq": [
            ("¿Cuando reemplazar?",
             "Solo durante overhaul completo de cabeza. Las valvulas dañadas (quemadas, dobladas) "
             "requieren reparacion del asiento valvular."),
        ],
    },
    "piston": {
        "rubro": "piston del motor",
        "shopify_type": "Motor",
        "p1": (
            "Piston del motor con bulones y aros. Pieza estructural del motor que se reemplaza solo "
            "durante reparacion mayor del block (overhaul). Los pistones modernos son de aleacion de "
            "aluminio forjado o fundido, con recubrimiento de friccion bajo en la falda."
        ),
        "faq": [
            ("¿Trae bulones y aros?",
             "Verifica el listing. Algunos vienen como conjunto completo (piston + bulon + aros), "
             "otros se compran por separado."),
        ],
    },
    "biela": {
        "rubro": "biela del motor",
        "shopify_type": "Motor",
        "p1": (
            "Biela del motor (connecting rod). Conecta el piston con el cigueñal, transmitiendo la "
            "fuerza de la combustion al ciguenal. Pieza estructural critica que se reemplaza solo "
            "durante reparacion mayor del block."
        ),
        "faq": [
            ("¿Cuando reemplazar?",
             "Solo durante overhaul mayor del block. Bielas dobladas o con desgaste de bocines requieren "
             "reemplazo completo."),
        ],
    },
    "reten_sello": {
        "rubro": "reten / sello",
        "shopify_type": "Motor",
        "p1": (
            "Reten o sello para componentes del motor. Su funcion es contener el aceite del componente "
            "(arbol de levas, ciguenal, bomba de aceite, eje del distribuidor) y bloquear el ingreso de "
            "polvo y agua. Esta fabricado en goma fluorada (Viton) o NBR con esqueleto metalico interior. "
            "Pieza de desgaste tipica que se reemplaza siempre que se desmonta el componente del que "
            "sella."
        ),
        "faq": [
            ("¿Cuando reemplazar?",
             "Siempre que haya fuga visible, o de manera preventiva cada vez que se desmonta el "
             "componente."),
        ],
    },
    "filtro_aceite": {
        "rubro": "filtro de aceite",
        "shopify_type": "Filtros",
        "p1": (
            "Filtro de aceite del motor. Atrapa particulas metalicas y contaminantes del aceite del "
            "motor para mantenerlo limpio durante el ciclo de servicio. Se reemplaza cada cambio de "
            "aceite (5,000-15,000 km segun el motor y aceite). Es pieza de mantenimiento periodico mas "
            "barata pero critica — un filtro saturado abre la valvula de bypass y deja pasar contaminantes."
        ),
        "faq": [
            ("¿Cada cuanto se cambia?",
             "Cada cambio de aceite. Nunca reutilizar."),
        ],
    },
    "carter": {
        "rubro": "carter / oil pan",
        "shopify_type": "Motor",
        "p1": (
            "Carter (oil pan) del motor. Es el deposito inferior que contiene el aceite de lubricacion. "
            "Esta fabricado en aluminio fundido (la mayoria de motores modernos), magnesio (BMW M3/M4 "
            "S-engines), o acero estampado (motores antiguos). Pieza tipica de reemplazo despues de "
            "impactos en el suelo (topes, baches profundos) o cuando los hilos del tapon de drenaje se "
            "barran."
        ),
        "faq": [
            ("¿Cuando reemplazar?",
             "Despues de impactos que rompen el carter, hilos del tapon barridos, o agrietamientos por "
             "fatiga."),
            ("¿Trae la junta?",
             "Verifica el listing — la junta del carter generalmente se compra por separado."),
        ],
    },
    "radiador": {
        "rubro": "radiador del motor",
        "shopify_type": "Motor",
        "p1": (
            "Radiador del motor (engine coolant radiator). Es el intercambiador de calor que recibe el "
            "liquido refrigerante caliente del motor y lo enfria forzando el paso de aire a traves de "
            "sus aletas. Fabricado en aluminio con tanques laterales en plastico o aluminio. Pieza "
            "vulnerable a impactos por piedras y a corrosion interna con los anos."
        ),
        "faq": [
            ("¿Sintomas de radiador dañado?",
             "Sobrecalentamiento del motor, fugas visibles de refrigerante, manchas verdes/anaranjadas "
             "bajo el motor, deposito de anticongelante que se vacia con frecuencia."),
            ("¿Cambio el termostato y bomba al mismo tiempo?",
             "Es practica recomendada en motores con kilometraje alto — los componentes del sistema de "
             "enfriamiento envejecen juntos."),
        ],
    },
    "ventilador": {
        "rubro": "ventilador del radiador",
        "shopify_type": "Motor",
        "p1": (
            "Ventilador electrico del radiador. Conjunto motor electrico + aspas + jaula que mueve aire "
            "forzado a traves del radiador y el condensador del A/C cuando el avance del vehiculo no es "
            "suficiente para enfriar (trafico, ralenti, alta temperatura ambiente). Pieza tipica de "
            "reemplazo cuando el motor electrico se quema, las aspas se rompen, o el modulo de control "
            "falla."
        ),
        "faq": [
            ("¿Sintomas de ventilador dañado?",
             "Motor sobrecalentando en trafico, A/C que enfria poco a baja velocidad, ruido fuerte de "
             "aspas, ventilador que no enciende cuando deberia."),
        ],
    },
    "manguera": {
        "rubro": "manguera del sistema de refrigeracion",
        "shopify_type": "Motor",
        "p1": (
            "Manguera del sistema de refrigeracion del motor. Transporta el liquido refrigerante "
            "(anticongelante) entre los componentes del circuito termico: radiador, bomba de agua, "
            "termostato, calefactor y motor. Esta fabricada en caucho EPDM con refuerzos textiles "
            "internos para soportar las temperaturas de operacion (hasta 130 °C) y la presion del "
            "sistema (1.0-1.5 bar). Pieza de mantenimiento periodico que se reemplaza cuando muestra "
            "grietas, abultamientos o fugas."
        ),
        "faq": [
            ("¿Cada cuanto se cambia?",
             "No tiene intervalo fijo. Inspeccionar cada servicio mayor — sintomas de cambio: grietas, "
             "abultamientos, manchas de refrigerante en las conexiones, endurecimiento del material."),
        ],
    },
    "deposito": {
        "rubro": "deposito de anticongelante",
        "shopify_type": "Motor",
        "p1": (
            "Deposito de anticongelante (expansion tank, coolant reservoir). Mantiene el liquido "
            "refrigerante en el sistema de enfriamiento del motor y absorbe la expansion termica. Falla "
            "tipica: rajadura del plastico por edad y calor, fuga visible bajo el motor, perdida "
            "progresiva de refrigerante."
        ),
        "faq": [
            ("¿Por que se rompe el deposito?",
             "El plastico se vuelve quebradizo por calor del motor + UV con los anos. Pieza tipica de "
             "reemplazo a partir de 100,000 km."),
        ],
    },
    "otro": {
        "rubro": "componente del motor",
        "shopify_type": "Motor",
        "p1": (
            "Componente del motor del vehiculo. Refaccion para vehiculos europeos. El listing especifica "
            "la pieza exacta y su posicion; si tienes dudas sobre compatibilidad o procedimiento de "
            "instalacion, envianos tu numero de VIN y un asesor te confirma los detalles antes de "
            "procesar el pedido."
        ),
        "faq": [
            ("¿Como confirmo que es la pieza correcta?",
             "Envianos tu numero de VIN y, si tienes, el numero de parte de la pieza original que estas "
             "reemplazando. Validamos contra el catalogo del fabricante."),
        ],
    },
}


def detectar_tipo(titulo):
    t = titulo.lower()
    if "soporte" in t and "motor" in t:
        return "soporte_motor"
    if "kit" in t and ("juntas" in t or "empaque" in t):
        return "kit_juntas"
    if "kit" in t and ("cadena" in t or "distribucion" in t):
        return "kit_cadena"
    if "junta" in t and ("cabeza" in t or "culata" in t):
        return "junta_cabeza"
    if "junta" in t and ("admision" in t or "multiple" in t and "admision" in t):
        return "junta_admision"
    if "junta" in t and "escape" in t:
        return "junta_escape"
    if "junta" in t and ("carter" in t or "oil pan" in t):
        return "junta_carter"
    if "junta" in t and ("punteria" in t or "punterias" in t or "tapa" in t and "valvula" in t or "tapa" in t and "levas" in t or "valve cover" in t):
        return "junta_tapa_valvulas"
    if "junta" in t and "cardan" not in t:
        return "junta_otra"  # → fallback a junta_admision template
    if "multiple" in t and "admision" in t:
        return "multiple_admision"
    if "multiple" in t and "escape" in t:
        return "multiple_escape"
    if "cadena" in t and ("tiempo" in t or "distribucion" in t):
        return "cadena_tiempo"
    if "tensor" in t and ("cadena" in t or "banda" in t or "distribucion" in t):
        return "tensor"
    if ("banda" in t or "correa" in t) and ("distribucion" in t or "accesorios" in t or "tiempo" in t):
        return "banda"
    if "polea" in t and ("tensora" in t or "tensor" in t):
        return "polea_tensora"
    if "polea" in t:
        return "polea"
    if "bomba" in t and "agua" in t:
        return "bomba_agua"
    if "bomba" in t and "aceite" in t:
        return "bomba_aceite"
    if "bomba" in t and "vacio" in t:
        return "bomba_vacio"
    if "termostato" in t:
        return "termostato"
    if "turbo" in t and "compresor" not in t.replace("turbocompresor", "turbo"):
        return "turbo"
    if "turbocompresor" in t or "turbocargador" in t:
        return "turbo"
    if "intercooler" in t:
        return "intercooler"
    if "cuerpo" in t and "aceleracion" in t:
        return "cuerpo_aceleracion"
    if ("arbol" in t and "levas" in t) or ("engrane" in t and "levas" in t):
        return "arbol_levas"
    if "valvula" in t and ("admision" in t or "escape" in t) and "egr" not in t and "vvt" not in t and "pcv" not in t:
        return "valvula"
    if "piston" in t:
        return "piston"
    if "biela" in t:
        return "biela"
    if "reten" in t or "sello" in t:
        return "reten_sello"
    if "filtro" in t and "aceite" in t:
        return "filtro_aceite"
    if "carter" in t and "junta" not in t:
        return "carter"
    if "radiador" in t and "aceite" not in t and "calefac" not in t:
        return "radiador"
    if ("ventilador" in t or "motoventilador" in t) and "radiador" in t:
        return "ventilador"
    if "manguera" in t and ("radiador" in t or "agua" in t or "refrigerante" in t):
        return "manguera"
    if "deposito" in t:
        return "deposito"
    return "otro"


JUNTA_OTRA_FALLBACK = TIPO_DEFINICIONES["junta_admision"]
TIPO_DEFINICIONES["junta_otra"] = JUNTA_OTRA_FALLBACK


def construir_resultado(p):
    titulo = p["titulo"]
    tipo = detectar_tipo(titulo)
    plantilla = TIPO_DEFINICIONES[tipo]

    fila = p["_fila_original"]
    sku = p["sku"]
    precio = p["precio"]
    np = p["numero_parte"]
    oem = p["codigo_oem"]
    garantia_raw = p["garantia"]
    tipo_veh = p["tipo_vehiculo"]
    marca_norm = p["marca_normalizada"]
    marca_raw = p["marca"]
    incluye = p["incluye_texto"]
    seccion_compat_lista = p["seccion_compatibilidades_propuesta"]
    caract_compat_pre = p["caract_compatibilidad_propuesta"]
    num_compat = p["num_compatibilidades"]
    marcas_veh = p["marcas_vehiculo"]
    lado = p["lado"]
    modelo = p.get("modelo_atributo", "")

    p1 = plantilla["p1"]

    primeros_modelos = []
    if seccion_compat_lista:
        primeros_modelos = [l.split(" — ")[0] for l in seccion_compat_lista.splitlines()[:4] if l.strip()]
    if num_compat > 0:
        marcas_str = ", ".join(marcas_veh)
        ejemplos = ""
        if primeros_modelos:
            ejemplos = (
                " Entre las configuraciones cubiertas se encuentran "
                + ", ".join(primeros_modelos[:3])
                + (", entre otras." if num_compat > 3 else ".")
            )
        codigo_motor = ""
        if modelo and any(c in modelo.upper() for c in ("N", "M", "B", "S")) and any(c.isdigit() for c in modelo):
            mm = re.search(r"\b([NMBSO]\d{2,3}[A-Z]?\d?)\b", modelo.upper())
            if mm:
                codigo_motor = f" El listing especifica codigo de motor {mm.group(1)}, util para confirmar compatibilidad sin VIN."
        p2 = (
            f"Aplica para {num_compat} configuraciones especificas de vehiculos europeos de las marcas "
            f"{marcas_str}, extraidas deterministicamente del bloque APLICA PARA del listing original."
            + ejemplos
            + " La lista completa con anios y motorizaciones aparece en la seccion de Compatibilidades de esta ficha."
            + codigo_motor
            + " Recomendamos confirmar con el numero de VIN antes de comprar — los componentes de motor varian por "
            "anio, version del motor (codigo) y opcionales como turbocompresion."
        )
    else:
        p2 = (
            "La descripcion original del listing menciona modelos compatibles pero no esta estructurada en el "
            "bloque APLICA PARA estandar, por lo que la lista no se pudo extraer automaticamente. "
            f"Por el titulo aplica a vehiculos {tipo_veh.lower() or 'tipo carro/camioneta'} de marcas europeas. "
            "Antes de comprar, envianos tu numero de VIN para que un asesor verifique modelo, anio, codigo de "
            "motor y configuracion contra el catalogo del proveedor — un error en componente de motor genera "
            "devolucion costosa."
        )

    refs = []
    nps = []
    if np:
        nps = [n.strip() for n in np.split(";") if n.strip()]
        if len(nps) > 1:
            refs.append(f"numeros de parte alternativos: {', '.join(nps[:4])}")
        else:
            refs.append(f"numero de parte: {np}")
    oems_list = []
    if oem and oem != np:
        oems_list = [o.strip() for o in re.split(r"[;\s]+", oem) if o.strip()]
        if len(oems_list) > 1:
            refs.append(f"codigos OEM: {', '.join(oems_list[:3])}")
        else:
            refs.append(f"codigo OEM: {oem}")
    p3_extras = []
    if refs:
        p3_extras.append(
            "Especificaciones de referencia: "
            + "; ".join(refs)
            + ". Estos codigos se cruzan contra el catalogo OEM del fabricante y permiten validar la pieza "
            "antes de instalarla; comparalos contra el numero estampado en la pieza original de tu vehiculo."
        )
        if len(nps) > 1 or len(oems_list) > 1:
            p3_extras.append(
                "La presencia de varios numeros de parte indica consolidacion de referencias por anio o paquete; "
                "cualquiera aplica para la version actual."
            )
    else:
        p3_extras.append(
            "El listing no incluye numero de parte ni codigo OEM publicados. Antes de instalar, recomendamos "
            "comparar visualmente la pieza con la original o consultar con un taller especializado."
        )
    if lado:
        p3_extras.append(f"Lado de instalacion: {lado}.")
    if modelo:
        p3_extras.append(f"Codigo de motor especificado en el listing: {modelo[:60]}.")
    if p.get("mc_nombre_match"):
        p3_extras.append(
            f"La referencia interna del catalogo Microsip es: {p['mc_nombre_match'][:80]}, "
            "util para taller que cruza con la red de proveedores."
        )
    p3 = " ".join(p3_extras)

    if incluye:
        p4 = (
            f"Este producto incluye los siguientes componentes: {incluye}. "
            "El kit se entrega en una sola caja para facilitar la trazabilidad durante la instalacion."
        )
    else:
        es_par_local = bool(re.search(r"\bpar\b", titulo, re.IGNORECASE))
        es_kit_local = bool(re.search(r"\b(kit|juego|set)\b", titulo, re.IGNORECASE))
        if es_par_local:
            p4 = (
                "Se entrega como par completo, ambos lados (izquierdo y derecho) en la misma caja. "
                "Recomendado por seguridad y por la importancia del balance de las dos piezas."
            )
        elif es_kit_local:
            p4 = (
                "Se entrega como kit completo en una sola caja con todos los componentes y la tornilleria de "
                "fijacion correspondiente. Reduce tiempos de inventario en taller y asegura compatibilidad."
            )
        else:
            p4 = (
                "Se vende como pieza individual nueva, en empaque del fabricante. Producto no reciclado ni "
                "remanufacturado. Para reparaciones de motor, considera reemplazar tambien componentes "
                "asociados (juntas, sellos, tornilleria) que envejecen al mismo ritmo — consulta con "
                "nuestro asesor."
            )

    pos = marca_pos(marca_norm, marca_raw)
    gar_dias = "30"
    m = re.search(r"(\d+)\s*d[ií]as?", garantia_raw)
    if m:
        gar_dias = m.group(1)
    p5 = (
        f"{pos} Garantia del vendedor de {gar_dias} dias contra defectos de fabrica. "
        "Embler Autopartes Europeas mantiene stock con entrega inmediata desde Ciudad de Mexico a todo el pais "
        "via DHL y FedEx, ademas de soporte tecnico para verificacion de compatibilidad por VIN antes del envio. "
        "Si despues de recibir la pieza notas que no corresponde a tu vehiculo, aplican nuestras politicas de "
        "devolucion (30 dias, sin uso, en empaque original)."
    )

    descripcion = "\n\n".join([p1, p2, p3, p4, p5])

    caract_compat = caract_compat_pre or (
        f"Compatible con los modelos {', '.join(marcas_veh) or 'mencionados en el titulo'}. "
        "Confirma compatibilidad exacta con tu numero de VIN antes de comprar."
    )

    faqs_base = [
        {
            "pregunta": "¿Como confirmo la compatibilidad con mi vehiculo?",
            "respuesta": (
                "Envianos el numero de serie (VIN) de tu auto y validamos la compatibilidad exacta antes "
                "de procesar el pedido. Tambien puedes mencionar el codigo de motor (N52, N63, M271, etc.) "
                "y el anio del vehiculo."
            ),
        },
    ]
    plantilla_faqs = [{"pregunta": q, "respuesta": a} for q, a in plantilla["faq"]]
    faqs = (faqs_base + plantilla_faqs)[:5]

    es_par = bool(re.search(r"\bpar\b", titulo, re.IGNORECASE))
    es_kit = bool(re.search(r"\b(kit|juego|set)\b", titulo, re.IGNORECASE)) or bool(incluye)
    antes = antes_comprar(np, oem)
    envio = envio_text(es_kit, es_par)

    titulo_limpio = title_clean(titulo)
    handle = slugify(f"{titulo_limpio}-{sku or fila}")
    seo_title = f"{titulo_limpio[:48]} | Embler"[:60]
    if seccion_compat_lista:
        primeros = [l.split(" — ")[0] for l in seccion_compat_lista.splitlines()[:3]]
        seo_models = f" Aplica a {', '.join(primeros)}." if primeros else ""
    else:
        seo_models = ""
    seo_desc = (
        f"{plantilla['rubro'].capitalize()} para vehiculos europeos.{seo_models} "
        f"Marca {marca_norm or marca_raw or 'no especificada'}. Envio inmediato a todo Mexico."
    )[:155]
    image_alt = f"{plantilla['rubro']} marca {marca_norm or marca_raw or ''}"[:125]

    body = body_html(descripcion, seccion_compat_lista, antes, envio, faqs)

    revision = []
    if num_compat == 0:
        revision.append(
            "[VERIFICAR] Compatibilidad inferida del titulo — la descripcion no incluye bloque APLICA PARA. "
            "Confirmar modelos, anios y codigo de motor."
        )
    if not np and not oem:
        revision.append("[BUSCAR] Numero de parte o codigo OEM faltantes.")
    if not sku:
        revision.append("[INCLUIR] SKU faltante — asignar antes de publicar.")
    if not marca_norm:
        revision.append("[ANALIZAR] Marca no identificada — confirmar fabricante.")
    if tipo == "soporte_motor" and not lado:
        revision.append(
            "[VERIFICAR] Soporte de motor sin atributo 'Lado' especificado — confirmar L/R/Universal "
            "antes de publicar."
        )
    revision.append(REVISION_FIJA)
    revision_text = "\n".join(revision)

    return {
        "_fila_original": fila,
        "caract_marca": marca_norm or "",
        "caract_origen": p["origen"] or "",
        "caract_tipo_vehiculo": tipo_veh,
        "caract_compatibilidad": caract_compat,
        "seccion_descripcion": descripcion,
        "seccion_compatibilidades": seccion_compat_lista,
        "seccion_antes_de_comprar": antes,
        "seccion_envio": envio,
        "seccion_devoluciones": SECCION_DEVOLUCIONES,
        "seccion_faq": faqs,
        "productos_relacionados": [],
        "shopify_handle": handle,
        "shopify_title": titulo_limpio,
        "shopify_body_html": body,
        "shopify_product_category": "Vehicles & Parts > Vehicle Parts & Accessories",
        "shopify_type": plantilla["shopify_type"],
        "shopify_tags": ", ".join(marcas_veh) if marcas_veh else "",
        "shopify_published": "TRUE",
        "shopify_option1_name": "Title",
        "shopify_option1_value": "Default Title",
        "shopify_variant_sku": sku,
        "shopify_variant_price": precio,
        "shopify_variant_compare_price": "",
        "shopify_variant_weight": "",
        "shopify_variant_weight_unit": "kg",
        "shopify_image_src": "",
        "shopify_image_alt_text": image_alt,
        "shopify_seo_title": seo_title,
        "shopify_seo_description": seo_desc,
        "shopify_status": "draft",
        "revision_humana": revision_text,
    }


def main():
    with open(BATCH_PATH, encoding="utf-8") as f:
        data = json.load(f)
    productos = data["productos"]
    resultados = [construir_resultado(p) for p in productos]
    payload = {"resultados": resultados}
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Resultados generados: {len(resultados)} filas -> {OUTPUT_PATH}")
    word_counts = [len(r["seccion_descripcion"].split()) for r in resultados]
    print(f"  Palabras seccion_descripcion: min={min(word_counts)} max={max(word_counts)} avg={sum(word_counts)//len(word_counts)}")
    tipos = Counter(detectar_tipo(p["titulo"]) for p in productos)
    print(f"  Distribucion por tipo: {dict(tipos)}")


if __name__ == "__main__":
    main()
