"""
Build script para refacciones_otros (1,868 filas).

`refacciones_otros` es el cajon de sastre de refacciones de auto que no encajaron en motor/suspension/
frenos/electrico/carroceria/clima/transmision. Mezclado: chapas, actuadores, amortiguadores de cofre,
faros, calaveras, controladores de ventana, etc. Templates dedicados para los tipos mas comunes y
fallback generico.

Muchos productos aqui estan MAL CLASIFICADOS — se flaggean para mover a la categoria correcta.
"""

import json
import os
import re
import unicodedata
from collections import Counter

HOJA = os.environ.get("EMBLER_HOJA", "ml_con_match")
BATCH_PATH = f"new-output_v2/{HOJA}/refacciones_otros_batch.json"
OUTPUT_PATH = f"new-output_v2/{HOJA}/refacciones_otros_batch_result.json"


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


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:100]


def title_clean(t: str) -> str:
    return t.replace("&", "").rstrip().strip()


def antes_comprar(numero_parte: str, oem: str) -> str:
    base = (
        "Para garantizar que recibas la pieza correcta para tu vehiculo, necesitamos el numero "
        "de serie (VIN) de tu auto antes de procesar el pedido. Esto evita errores, tiempos perdidos "
        "y devoluciones innecesarias. Escribenos y con gusto confirmamos compatibilidad."
    )
    if numero_parte and oem and numero_parte != oem:
        base += f" Tambien puedes verificar con el numero de parte {numero_parte} o codigo OEM {oem}."
    elif numero_parte:
        base += f" Tambien puedes verificar con el numero de parte {numero_parte}."
    elif oem:
        base += f" Tambien puedes verificar con el codigo OEM {oem}."
    return base


def envio_text(es_kit: bool, es_par: bool) -> str:
    base = (
        "Tenemos stock disponible para entrega inmediata. "
        "Enviamos el mismo dia de tu pago a Ciudad de Mexico y a todo el pais via DHL o FedEx."
    )
    if es_par:
        base += " Este producto se vende como par completo."
    elif es_kit:
        base += " Este producto se vende como juego completo."
    return base


def body_html(desc: str, compat_lista: str, antes: str, envio: str, faqs: list) -> str:
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


def marca_posicionamiento(marca_norm: str, marca_raw: str) -> str:
    if marca_norm == "Original Frey":
        return (
            "Marca Original Frey, importada y especializada en refacciones para vehiculos europeos premium "
            "con calidad equivalente al equipo original (OEM-grade aleman)."
        )
    if marca_norm == "Embler":
        return (
            "Marca Embler, propia de Embler Autopartes Europeas, especializada en refacciones para BMW, "
            "Mercedes-Benz, Audi, Volkswagen, Porsche, Volvo, Mini Cooper y Jaguar."
        )
    if not marca_norm:
        return f"Marca de refaccion: {marca_raw or 'no especificada'}."
    return f"Marca {marca_norm}, fabricante de refacciones para vehiculos europeos."


# ---------------------------------------------------------------------------
# Templates por tipo
# ---------------------------------------------------------------------------

TIPO_DEFINICIONES = {
    "chapa_cerradura": {
        "rubro": "chapa de cerradura",
        "shopify_type": "Carrocería",
        "p1": (
            "Chapa de cerradura del vehiculo. Es el conjunto mecanico-electrico instalado en la puerta "
            "(delantera, trasera o cajuela) que recibe la llave o la senal del control remoto y libera el "
            "mecanismo de apertura. Las chapas modernas integran motor electrico (cierre centralizado), "
            "sensor de posicion (puerta abierta/cerrada para los testigos del tablero), y en algunos "
            "modelos sensor de antichoque (deadlock). Falla tipica: motor del actuador atascado o quemado "
            "(la chapa no abre/cierra electricamente), mecanismo mecanico desgastado, sensor de posicion "
            "que envia lectura incorrecta."
        ),
        "faq": [
            ("¿Sintomas de chapa dañada?",
             "Cierre centralizado que no funciona en una puerta, ruido extraño al cerrar, llave fisica "
             "que no gira, o testigo de puerta abierta encendido aunque este cerrada."),
            ("¿Es del lado izquierdo o derecho?",
             "Confirma con el listing — cada lado tiene codigo de parte distinto."),
            ("¿Necesito codificacion despues?",
             "En algunos vehiculos europeos modernos (BMW F-series, Mercedes con keyless), la chapa nueva "
             "requiere codificacion al modulo del vehiculo. Confirma con tu taller."),
        ],
    },
    "actuador_chapa": {
        "rubro": "actuador electrico de chapa",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Actuador electrico de la chapa de cerradura. Es el motor electrico DC con caja reductora "
            "que mueve internamente el mecanismo de cierre/apertura de la chapa cuando recibe la senal "
            "del modulo de control de cierre centralizado. Falla tipica: motor quemado por uso intenso o "
            "humedad, engranes plasticos rotos, o conector electrico con falsa conexion. Es punto debil "
            "tipico en BMW (especialmente las puertas traseras y la cajuela) y en algunos modelos Mini "
            "Cooper."
        ),
        "faq": [
            ("¿Sintomas de actuador dañado?",
             "Cierre centralizado que no funciona en una puerta, ruido de motor electrico atascado al "
             "presionar el boton, o no hay sonido alguno al activar el cierre."),
            ("¿Lo cambio sin desmontar la chapa completa?",
             "En algunos modelos si — el actuador se desensambla de la chapa principal. En otros se "
             "vende solo como parte del conjunto chapa completa."),
            ("¿Es del lado izquierdo o derecho?",
             "Confirma con el listing. Algunos actuadores son simetricos, otros son lado especifico."),
        ],
    },
    "amortiguador_cofre": {
        "rubro": "amortiguador de cofre / cajuela (resorte de gas)",
        "shopify_type": "Carrocería",
        "p1": (
            "Amortiguador de cofre o cajuela (gas strut, hood/trunk shock). Es el cilindro telescopico "
            "lleno de gas comprimido que mantiene el cofre o la tapa de cajuela abiertos sin caerse. "
            "Falla tipica: pierde gas con los anos y deja de soportar el peso (cofre que cae solo, "
            "cajuela que no se queda abierta), provocando inseguridad al manipular el motor o la cajuela. "
            "Es pieza de desgaste con vida util tipica de 8-12 anos. Se recomienda reemplazar siempre como "
            "par para evitar carga desbalanceada."
        ),
        "faq": [
            ("¿Sintomas de amortiguador desgastado?",
             "El cofre o la cajuela se cae sola al levantarlo, no se queda en posicion abierta, requiere "
             "fuerza para mantenerlo arriba mientras trabajas."),
            ("¿Se cambia uno o el par?",
             "Siempre el par. Ambos amortiguadores envejecen al mismo tiempo y cambiar solo uno deja la "
             "carga desbalanceada — el cofre se inclina hacia un lado al abrir."),
            ("¿Es del cofre o de cajuela?",
             "Confirma con el listing — son piezas distintas con codigos de parte distintos."),
        ],
    },
    "faro": {
        "rubro": "faro delantero",
        "shopify_type": "Carrocería",
        "p1": (
            "Faro delantero del vehiculo. Proporciona iluminacion frontal para conduccion nocturna, alta "
            "y baja intensidad, mas funciones auxiliares como direccionales, luz de posicion (DRL) y, en "
            "faros premium modernos, iluminacion adaptativa que sigue la direccion del volante. Los faros "
            "pueden ser halogenos (mas economicos), HID/xenon (luz blanca brillante con balastra), o "
            "LED/laser (vida util larga, eficiencia energetica). Pieza vulnerable a impactos por "
            "piedras, oxidacion del cristal exterior por UV, o entrada de humedad cuando los sellos se "
            "degradan."
        ),
        "faq": [
            ("¿Halogeno, xenon o LED?",
             "Verifica el codigo de parte exacto contra tu vehiculo — son tres tipos distintos no "
             "intercambiables. El xenon requiere balastra; el LED requiere modulo de control. El halogeno "
             "es el mas simple."),
            ("¿Necesito codificacion despues de instalar?",
             "Los faros LED modernos (BMW F-series, Mercedes con multibeam, Audi Matrix) requieren "
             "codificacion al modulo de iluminacion. Sin codificacion pueden no encender o entrar en error."),
            ("¿Es del lado izquierdo o derecho?",
             "Confirma el lado. Faros L/R son distintos (no solo espejados — la curvatura del reflector "
             "interno cambia)."),
            ("¿Trae las bombillas o LEDs?",
             "Algunos faros vienen con bombillas instaladas, otros sin ellas. Confirma con el listing."),
        ],
    },
    "calavera": {
        "rubro": "calavera (luz trasera)",
        "shopify_type": "Carrocería",
        "p1": (
            "Calavera (luz trasera) del vehiculo. Integra luz de freno, posicion, direccional trasera, "
            "luz de reversa y, en algunos modelos, luz de niebla trasera. En vehiculos modernos europeos "
            "las calaveras son LED con disenos distintivos. Pieza tipicamente afectada por impactos, "
            "oxidacion del cristal por UV, o entrada de humedad cuando los sellos se degradan. Algunos "
            "modelos tienen luces inner (en la cajuela) y outer (en la salpicadera) que se compran por "
            "separado."
        ),
        "faq": [
            ("¿Es inner (cajuela) o outer (carroceria)?",
             "Confirma con el listing. Las inner se montan en la tapa de cajuela; las outer en la "
             "salpicadera fija. Cada una tiene codigo de parte distinto."),
            ("¿Es LED o bombillas convencionales?",
             "Verifica el codigo de parte. Los LED no son intercambiables con las de bombillas tradicionales."),
            ("¿Es del lado izquierdo o derecho?",
             "Confirma el lado en el listing."),
        ],
    },
    "controlador_ventana": {
        "rubro": "regulador / motor de ventana",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Regulador o motor de ventana electrica (window regulator, window motor). Es el conjunto "
            "mecanico-electrico que sube y baja el cristal de la puerta. Esta compuesto por un motor "
            "electrico DC con caja reductora, conectado a un sistema de cables o brazos articulados que "
            "transmiten el movimiento al vidrio. Falla tipica: motor quemado (ventana que no se mueve), "
            "cables del regulador rotos (vidrio que se cae dentro de la puerta), engranes plasticos "
            "desgastados (ventana que sube/baja con dificultad o ruido)."
        ),
        "faq": [
            ("¿Sintomas de regulador dañado?",
             "Ventana que no sube/baja al activar el switch, ruido fuerte de engranes al accionarla, "
             "vidrio que se cae dentro de la puerta, ventana que se mueve a tirones."),
            ("¿Es del lado izquierdo o derecho?",
             "Confirma con el listing — cada lado es distinto. Tambien hay reguladores delanteros y "
             "traseros distintos."),
            ("¿Trae el motor o solo el regulador?",
             "Verifica el listing. Algunos vienen como conjunto motor + regulador, otros solo el regulador "
             "(reutilizando el motor original) o solo el motor."),
        ],
    },
    "electroventilador": {
        "rubro": "electroventilador del radiador",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Electroventilador del radiador (cooling fan, radiator fan assembly). Es el motor electrico "
            "con aspas que genera flujo de aire forzado a traves del radiador y el condensador del A/C "
            "cuando el avance del vehiculo no es suficiente para enfriar (trafico, ralenti, alta "
            "temperatura ambiente). Falla tipica: motor quemado, aspas rotas por impacto con objetos en "
            "el motor, o resistencia/modulo de control dañado (que afecta la velocidad variable)."
        ),
        "faq": [
            ("¿Sintomas de electroventilador dañado?",
             "Motor sobrecalentando en trafico, A/C que enfria poco a baja velocidad, ruido fuerte de "
             "aspas o vibracion del frente al activarse, ventilador que no enciende cuando deberia."),
            ("¿Trae la jaula y aspas?",
             "Algunos vienen como conjunto completo (motor + jaula + aspas + modulo de control), otros "
             "solo el motor. Confirma con el listing."),
        ],
    },
    "soporte_motor": {
        "rubro": "soporte / taco del motor",
        "shopify_type": "Suspensión",
        "p1": (
            "Soporte (taco) del motor. Es el bloque de caucho-metal que sujeta el motor al chasis del "
            "vehiculo, absorbiendo las vibraciones del motor y manteniendo su alineacion. Esta compuesto "
            "por un soporte metalico envuelto o conectado por elementos de caucho vulcanizado, en algunos "
            "casos con camara hidraulica para amortiguar mejor las vibraciones. Pieza de desgaste tipica: "
            "el caucho se cuartea con los anos y aparecen vibraciones en ralenti, golpes al cambiar de "
            "marcha y movimiento excesivo del motor en aceleracion."
        ),
        "faq": [
            ("¿Sintomas de soporte de motor dañado?",
             "Vibracion en ralenti (especialmente con caja en D o R), golpes al cambiar de marcha, "
             "movimiento excesivo del motor al acelerar, sonido sordo al frenar."),
            ("¿Cambio el de la transmision al mismo tiempo?",
             "Es practica recomendada — los soportes envejecen juntos."),
        ],
    },
    "tubo_agua": {
        "rubro": "tubo de agua / sistema de refrigeracion",
        "shopify_type": "Motor",
        "p1": (
            "Tubo de agua del sistema de refrigeracion del motor. Tubo rigido de aluminio o plastico "
            "reforzado que conduce el liquido refrigerante entre componentes del circuito termico. A "
            "diferencia de las mangueras de caucho, los tubos rigidos suelen estar integrados con "
            "conexiones complejas para llegar a zonas confinadas del compartimento del motor. Falla tipica: "
            "fuga por la junta o rotura del plastico por edad y golpes termicos."
        ),
        "faq": [
            ("¿Como se que mi tubo de agua esta dañado?",
             "Perdida progresiva de refrigerante, manchas blanquecinas (cristalizacion del anticongelante), "
             "calefaccion intermitente."),
            ("¿Trae los o-rings de sello?",
             "Verifica el listing — los o-rings se reemplazan siempre que se desmonta el tubo."),
        ],
    },
    "deposito": {
        "rubro": "deposito (anticongelante / lavaparabrisas)",
        "shopify_type": "Motor",
        "p1": (
            "Deposito de anticongelante (expansion tank, coolant reservoir) o de lavaparabrisas (washer "
            "fluid reservoir). El de anticongelante mantiene el liquido refrigerante en el sistema de "
            "enfriamiento del motor y absorbe la expansion termica; el de lavaparabrisas almacena el "
            "liquido para el sistema de limpieza del parabrisas. Falla tipica: rajadura del plastico por "
            "edad y calor (deposito de coolant), fuga visible bajo el motor."
        ),
        "faq": [
            ("¿Es de anticongelante o de lavaparabrisas?",
             "Verifica el titulo — son distintos. El de anticongelante esta en el motor (junto al "
             "radiador); el de lavaparabrisas en la salpicadera o frente del vehiculo."),
            ("¿Por que se rompe el deposito?",
             "El plastico se vuelve quebradizo por calor del motor + UV con los anos. Es pieza tipica de "
             "reemplazo a partir de 100,000 km."),
        ],
    },
    "soporte": {
        "rubro": "soporte / brazo / refuerzo de carroceria",
        "shopify_type": "Carrocería",
        "p1": (
            "Soporte, brazo o refuerzo estructural de carroceria. Pieza de fijacion o estructural que "
            "conecta componentes del vehiculo. Verifica el titulo del listing para identificar la "
            "posicion exacta y la funcion de la pieza."
        ),
        "faq": [
            ("¿Como confirmo que es la pieza correcta?",
             "Envianos tu numero de VIN y el numero de parte de la pieza original. Validamos contra el "
             "catalogo del fabricante."),
        ],
    },
    "reten_sello": {
        "rubro": "reten / sello",
        "shopify_type": "Motor",
        "p1": (
            "Reten o sello para componentes del motor o transmision. Su funcion es contener el aceite del "
            "componente y bloquear el ingreso de polvo y agua. Esta fabricado en goma fluorada (Viton) o "
            "NBR con esqueleto metalico interior. Pieza de desgaste tipica que se reemplaza siempre que "
            "se desmonta el componente del que sella."
        ),
        "faq": [
            ("¿Cuando reemplazar el reten?",
             "Siempre que haya fuga visible, o de manera preventiva cada vez que se desmonta el "
             "componente. Es barato comparado con el costo de mano de obra."),
        ],
    },
    "junta_motor": {
        "rubro": "junta / empaque del motor",
        "shopify_type": "Motor",
        "p1": (
            "Junta o empaque del motor. Componente de sellado que mantiene la estanqueidad entre dos "
            "superficies del motor (cabeza-block, colector-cabeza, tapa de valvulas-cabeza, etc.). Las "
            "juntas modernas son metaloplasticas o de fibra reforzada con elastomero, capaces de soportar "
            "la temperatura y presion de los gases de combustion. Pieza de desgaste tipica que se reemplaza "
            "siempre que se desarma el componente."
        ),
        "faq": [
            ("¿Cuando reemplazar la junta?",
             "Siempre que se desarma la pieza correspondiente (no se reutiliza). Tambien cuando hay fuga "
             "de aceite, refrigerante o gases de combustion por la zona."),
            ("¿Trae los tornillos?",
             "Generalmente no — los tornillos se reutilizan o se compran por separado. Algunos kits "
             "incluyen tornilleria especifica."),
        ],
    },
    "cojinete": {
        "rubro": "cojinete / balero",
        "shopify_type": "Motor",
        "p1": (
            "Cojinete (balero, rodamiento) para componentes mecanicos del vehiculo. Pieza de precision "
            "que reduce la friccion en partes giratorias o deslizantes. Hay distintos tipos: bolas, "
            "rodillos conicos, agujas, axiales. Cada uno tiene aplicacion especifica segun la carga y "
            "velocidad."
        ),
        "faq": [
            ("¿Como se que el balero esta dañado?",
             "Sintomas: ruido tipo zumbido o moledora que aumenta con la velocidad, vibracion, juego "
             "excesivo del componente sobre el que esta montado."),
        ],
    },
    "manija": {
        "rubro": "manija / manilla",
        "shopify_type": "Carrocería",
        "p1": (
            "Manija (manilla) exterior o interior del vehiculo. La exterior se acciona para abrir la "
            "puerta desde fuera; la interior desde dentro de la cabina. En modelos con keyless, la manija "
            "exterior puede integrar un sensor capacitivo. Pieza tipica de reemplazo cuando se rompe el "
            "mecanismo o se descascara la pintura/cromado."
        ),
        "faq": [
            ("¿Es interior o exterior?",
             "Confirma con el listing."),
            ("¿Es del lado izquierdo o derecho?",
             "Cada lado tiene codigo de parte distinto."),
        ],
    },
    "moldura": {
        "rubro": "moldura / embellecedor",
        "shopify_type": "Carrocería",
        "p1": (
            "Moldura o embellecedor de carroceria. Pieza decorativa exterior: moldura de techo, "
            "embellecedor de puerta, bisel de faro, etc. Cumple funcion estetica y protege la carroceria "
            "de rayaduras menores."
        ),
        "faq": [
            ("¿Es del lado izquierdo, derecho, o universal?",
             "Verifica el listing."),
            ("¿Como se instala?",
             "Tipicamente con clips a presion o cinta 3M de doble cara."),
        ],
    },
    "panal_radiador": {
        "rubro": "panal / radiador del motor",
        "shopify_type": "Motor",
        "p1": (
            "Panal del radiador (radiator core, heat exchanger). Es el intercambiador de calor que "
            "recibe el liquido refrigerante caliente del motor y lo enfria forzando el paso de aire a "
            "traves de sus aletas. Esta fabricado en aluminio con tanques laterales en plastico o "
            "aluminio. Pieza vulnerable a impactos por piedras y a corrosion interna con los anos."
        ),
        "faq": [
            ("¿Sintomas de radiador dañado?",
             "Sobrecalentamiento del motor, fugas visibles de refrigerante, manchas verdes/anaranjadas "
             "bajo el motor, deposito de anticongelante que se vacia con frecuencia."),
            ("¿Trae los tapones y conexiones?",
             "Verifica el listing — algunos vienen con tapas, otros se reutilizan las originales."),
        ],
    },
    "ventilador_radiador": {
        "rubro": "ventilador del radiador",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Ventilador del radiador (radiator fan). Conjunto motor electrico + aspas + jaula que mueve "
            "aire forzadamente a traves del radiador y el condensador del A/C cuando el avance del "
            "vehiculo no es suficiente para enfriar. Pieza tipica de reemplazo cuando el motor "
            "electrico se quema, las aspas se rompen, o el modulo de control falla."
        ),
        "faq": [
            ("¿Trae motor + aspas + jaula?",
             "Verifica el listing — algunos vienen como conjunto completo, otros solo motor."),
        ],
    },
    "otro": {
        "rubro": "componente del vehiculo",
        "shopify_type": "Refacciones",
        "p1": (
            "Componente del vehiculo. Refaccion para vehiculos europeos. El listing especifica la pieza "
            "exacta — verifica titulo, descripcion y atributos para identificar funcion y posicion. Si "
            "tienes dudas, envianos tu numero de VIN y un asesor te confirma compatibilidad y "
            "procedimiento de instalacion antes de procesar el pedido."
        ),
        "faq": [
            ("¿Como confirmo que es la pieza correcta?",
             "Envianos tu numero de VIN y, si tienes, el numero de parte de la pieza original que estas "
             "reemplazando. Validamos contra el catalogo del fabricante."),
        ],
    },
}


def detectar_tipo(titulo: str) -> str:
    t = titulo.lower()
    if "actuador" in t and "chapa" in t:
        return "actuador_chapa"
    if "chapa" in t and "cerradura" in t or "chapa puerta" in t:
        return "chapa_cerradura"
    if "amortiguador" in t and ("cofre" in t or "cajuela" in t):
        return "amortiguador_cofre"
    if "faro" in t and ("niebla" not in t and "espejo" not in t and "giro" not in t):
        return "faro"
    if "calavera" in t:
        return "calavera"
    if "controlador" in t and "ventana" in t or ("regulador" in t and "ventana" in t) or ("motor" in t and "ventana" in t):
        return "controlador_ventana"
    if "electroventilador" in t or ("ventilador" in t and "radiador" in t):
        return "ventilador_radiador"
    if "soporte" in t and "motor" in t and "ventana" not in t:
        return "soporte_motor"
    if "tubo" in t and ("agua" in t or "calefacc" in t):
        return "tubo_agua"
    if "deposito" in t:
        return "deposito"
    if "panal" in t and "radiador" in t:
        return "panal_radiador"
    if "radiador" in t and "aceite" not in t and "ventilador" not in t and "calefac" not in t:
        return "panal_radiador"
    if "reten" in t or "sello" in t:
        return "reten_sello"
    if "junta" in t and "cardan" not in t:
        return "junta_motor"
    if "cojinete" in t or "balero" in t or "rodamiento" in t:
        return "cojinete"
    if "manija" in t or "manilla" in t:
        return "manija"
    if "moldura" in t or "embellecedor" in t or "bisel" in t:
        return "moldura"
    if "soporte" in t:
        return "soporte"
    return "otro"


def construir_resultado(p: dict) -> dict:
    titulo = p["titulo"]
    tipo = detectar_tipo(titulo)
    plantilla = TIPO_DEFINICIONES[tipo]

    fila = p["_fila_original"]
    sku = p["sku"]
    precio = p["precio"]
    numero_parte = p["numero_parte"]
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
        p2 = (
            f"Aplica para {num_compat} configuraciones especificas de vehiculos europeos de las marcas "
            f"{marcas_str}, extraidas deterministicamente del bloque APLICA PARA del listing original."
            + ejemplos
            + " La lista completa con anios y motorizaciones aparece en la seccion de Compatibilidades de esta ficha. "
            "Recomendamos confirmar con el numero de VIN antes de comprar."
        )
    else:
        p2 = (
            "La descripcion original del listing menciona modelos compatibles pero no esta estructurada en el "
            "bloque APLICA PARA estandar, por lo que la lista no se pudo extraer automaticamente. "
            f"Por el titulo aplica a vehiculos {tipo_veh.lower() or 'tipo carro/camioneta'} de marcas europeas. "
            "Antes de comprar, envianos tu numero de VIN para verificar modelo exacto."
        )

    refs = []
    nps = []
    if numero_parte:
        nps = [n.strip() for n in numero_parte.split(";") if n.strip()]
        if len(nps) > 1:
            refs.append(f"numeros de parte alternativos: {', '.join(nps[:4])}")
        else:
            refs.append(f"numero de parte: {numero_parte}")
    oems_list = []
    if oem and oem != numero_parte:
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
            "antes de instalarla."
        )
        if len(nps) > 1 or len(oems_list) > 1:
            p3_extras.append(
                "La presencia de varios numeros de parte indica consolidacion de referencias por anio o paquete; "
                "cualquiera aplica para la version actual."
            )
    else:
        p3_extras.append(
            "El listing no incluye numero de parte ni codigo OEM publicados. Antes de instalar, recomendamos "
            "comparar visualmente la pieza con la original."
        )
    if lado:
        p3_extras.append(f"Lado de instalacion: {lado}.")
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
                "Recomendado por seguridad y balance entre ambos lados del vehiculo."
            )
        elif es_kit_local:
            p4 = (
                "Se entrega como kit completo en una sola caja con todos los componentes y la tornilleria de "
                "fijacion correspondiente. Reduce tiempos de inventario en taller."
            )
        else:
            p4 = (
                "Se vende como pieza individual nueva, en empaque del fabricante. Producto no reciclado ni "
                "remanufacturado. Si tu reparacion requiere reemplazar la pieza tambien en el lado opuesto "
                "del vehiculo, consulta con nuestro asesor."
            )

    pos = marca_posicionamiento(marca_norm, marca_raw)
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
                "de procesar el pedido. Tambien puedes mencionar el codigo de motor."
            ),
        },
    ]
    plantilla_faqs = [{"pregunta": q, "respuesta": a} for q, a in plantilla["faq"]]
    faqs = (faqs_base + plantilla_faqs)[:5]

    es_par = bool(re.search(r"\bpar\b", titulo, re.IGNORECASE))
    es_kit = bool(re.search(r"\b(kit|juego|set)\b", titulo, re.IGNORECASE)) or bool(incluye)
    antes = antes_comprar(numero_parte, oem)
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
            "Confirmar modelos y anios."
        )
    if not numero_parte and not oem:
        revision.append("[BUSCAR] Numero de parte o codigo OEM faltantes.")
    if not sku:
        revision.append("[INCLUIR] SKU faltante — asignar antes de publicar.")
    if not marca_norm:
        revision.append("[ANALIZAR] Marca no identificada — confirmar fabricante.")

    # Flag heavy: pieza mal clasificada
    cat_destino = {
        "chapa_cerradura": "refacciones_carroceria (Carrocería con sub-grupo cerraduras)",
        "actuador_chapa": "refacciones_electrico (Sistema Eléctrico)",
        "amortiguador_cofre": "refacciones_carroceria",
        "faro": "refacciones_carroceria",
        "calavera": "refacciones_carroceria",
        "controlador_ventana": "refacciones_electrico",
        "electroventilador": "refacciones_electrico",
        "ventilador_radiador": "refacciones_electrico",
        "soporte_motor": "refacciones_suspension",
        "tubo_agua": "refacciones_motor",
        "deposito": "refacciones_motor",
        "panal_radiador": "refacciones_motor",
        "junta_motor": "refacciones_motor",
        "reten_sello": "refacciones_motor",
        "manija": "refacciones_carroceria",
        "moldura": "refacciones_carroceria",
        "soporte": "refacciones_carroceria",
        "cojinete": "refacciones_motor",
    }
    if tipo in cat_destino:
        revision.append(
            f"[ANALIZAR] Mal clasificada en `refacciones_otros`. El titulo sugiere {cat_destino[tipo]}. "
            "Considerar mover el producto a esa categoria antes de publicar."
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
