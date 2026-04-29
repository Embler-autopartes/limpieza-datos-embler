"""
Build script para refacciones_carroceria (597 filas).

Templates por tipo: parrilla, rejilla, espejo, faro, faro_niebla, calavera, defensa, salpicadera,
cofre, moldura, manija, puerta, limpiaparab, soporte_defensa, absorbedor, emblema, aero, tolva, otro.
"""

import json
import os
import re
import unicodedata
from collections import Counter

HOJA = os.environ.get("EMBLER_HOJA", "ml_con_match")
BATCH_PATH = f"new-output_v2/{HOJA}/refacciones_carroceria_batch.json"
OUTPUT_PATH = f"new-output_v2/{HOJA}/refacciones_carroceria_batch_result.json"


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
    raw_low = (marca_raw or "").lower()
    if "hella" in raw_low or "magneti" in raw_low:
        return (
            f"Marca {marca_norm or marca_raw}, proveedor OEM aleman/europeo de iluminacion automotriz. "
            "Suministra a la fabrica para BMW, Mercedes, Audi, VW y otros."
        )
    if "depo" in raw_low or "tyc" in raw_low:
        return (
            f"Marca {marca_norm or marca_raw}, fabricante taiwanes de iluminacion y carroceria con calidad "
            "aftermarket-OE. Es la opcion estandar de carroceria en talleres especializados."
        )
    if not marca_norm:
        return f"Marca de refaccion: {marca_raw or 'no especificada'}."
    return f"Marca {marca_norm}, fabricante de refacciones para vehiculos europeos."


# ---------------------------------------------------------------------------
# Templates por tipo
# ---------------------------------------------------------------------------

TIPO_DEFINICIONES = {
    "parrilla": {
        "rubro": "parrilla delantera",
        "shopify_type": "Carrocería",
        "p1": (
            "Parrilla delantera del vehiculo. Es el panel decorativo y funcional que cubre la apertura del "
            "frontal del cofre, permite el flujo de aire al radiador y al condensador del aire acondicionado, "
            "y define la estetica caracteristica de la marca. En BMW, las dos rejillas tipo riñon son "
            "elemento de identidad de marca; en Mercedes y Audi tambien tienen diseños distintivos por "
            "modelo. Esta fabricada en plastico ABS con acabado en laca o cromado segun el modelo, y se "
            "fija al frontal mediante clips y tornillos. Es pieza vulnerable a impactos por piedras, daños "
            "estacionarios o accidentes menores."
        ),
        "faq": [
            ("¿Es para mi modelo exacto?",
             "Las parrillas varian por modelo, anio y paquete (M Sport, AMG, S-Line). Verifica con tu "
             "numero de VIN porque hay diseños similares pero no intercambiables."),
            ("¿Viene pintada?",
             "El listing especifica el acabado. Algunas vienen en negro de fabrica, otras en cromo. Si "
             "necesitas otro color, debe pintarse en taller antes de instalar."),
            ("¿Es facil de instalar?",
             "Generalmente requiere desmontar la defensa delantera. Tiempo de instalacion: 30-60 minutos "
             "en taller. Recomendamos servicio profesional para evitar danar las clips de fijacion."),
            ("¿Trae los emblemas?",
             "La mayoria no incluye los emblemas — se reutilizan los originales del vehiculo. Verifica con "
             "el listing si necesitas emblemas nuevos."),
        ],
    },
    "rejilla": {
        "rubro": "rejilla / inserto de la parrilla",
        "shopify_type": "Carrocería",
        "p1": (
            "Rejilla o inserto del frontal del vehiculo. Son los paneles decorativos con patron de mallas "
            "(diamante, vertical, horizontal) que se insertan en la parrilla principal o en aperturas "
            "secundarias de la facia. Cumplen funcion estetica y dirigen el flujo de aire hacia los "
            "intercambiadores de calor. En BMW son comunes las rejillas de la parrilla central, las "
            "rejillas laterales de la facia (donde van los faros antiniebla), y las rejillas de "
            "ventilacion del cofre. Es pieza tipica de reemplazo cuando se daña por impactos o cuando se "
            "personaliza el frontal con un acabado distinto (ej. negro brillante en lugar de cromado)."
        ),
        "faq": [
            ("¿Es del lado izquierdo, derecho, o central?",
             "Verifica el listing. Algunas rejillas son simetricas (van en cualquier lado), otras tienen "
             "lado especifico. Confirma con tu numero de VIN si tienes duda."),
            ("¿Cuesta mucho la instalacion?",
             "La rejilla suele instalarse desde fuera con clips, sin desmontar la defensa. Tiempo: 15-30 "
             "minutos. Algunas posiciones (rejilla del cofre) requieren mas trabajo."),
        ],
    },
    "espejo": {
        "rubro": "espejo retrovisor / componente del espejo",
        "shopify_type": "Carrocería",
        "p1": (
            "Espejo retrovisor lateral o componente del espejo (cristal, carcasa, motor del espejo, "
            "direccional integrada). Los espejos modernos europeos integran multiples funciones: motor "
            "electrico de ajuste, calefactor del cristal, direccional, sensor de angulo muerto, sensor de "
            "lluvia, plegado electrico, y memoria de posicion. Una falla puede ser solo de uno de los "
            "elementos (cristal roto, calefactor sin funcionar, motor de ajuste atascado) sin necesidad de "
            "reemplazar el espejo completo. Verifica el listing para el componente exacto."
        ),
        "faq": [
            ("¿Es el espejo completo o solo el cristal?",
             "Verifica el titulo. 'Espejo' tipicamente incluye carcasa + cristal + motor; 'cristal del "
             "espejo' es solo la luna; 'direccional del espejo' es el LED ambar integrado."),
            ("¿Es del lado izquierdo o derecho?",
             "Confirma el lado en el listing. Lado izquierdo = lado del conductor (conduciendo en Mexico). "
             "Lado derecho = lado del pasajero."),
            ("¿Tiene calefactor?",
             "Los espejos modernos europeos premium si lo tienen. El listing especifica si esta version "
             "incluye calefactor. Verifica antes de comprar — el codigo de parte es distinto."),
            ("¿Lo necesito programar despues de instalar?",
             "Las funciones electricas (memoria, sensor angulo muerto) requieren codificacion al modulo "
             "del vehiculo en algunos casos. La mayoria solo necesitan conexion electrica."),
        ],
    },
    "faro": {
        "rubro": "faro delantero",
        "shopify_type": "Carrocería",
        "p1": (
            "Faro delantero del vehiculo. Proporciona iluminacion frontal en marcha nocturna, alta y baja "
            "intensidad, mas funciones auxiliares como direccionales, posicion (DRL) y, en faros premium "
            "modernos, iluminacion adaptativa que sigue la direccion del volante. Los faros pueden ser "
            "halogenos (mas economicos), HID/xenon (luz blanca brillante con balastra), o LED (vida util "
            "larga, eficiencia energetica). Es pieza vulnerable a impactos, daños por piedras, oxidacion "
            "del cristal exterior por UV, o entrada de humedad cuando los sellos se degradan."
        ),
        "faq": [
            ("¿Halogeno, xenon o LED?",
             "Verifica el codigo de parte exacto contra tu vehiculo — son tres tipos distintos no "
             "intercambiables. El xenon requiere balastra; el LED requiere modulo de control. El halogeno "
             "es el mas simple pero da menor iluminacion."),
            ("¿Trae las bombillas o LEDs?",
             "Algunos faros vienen con bombillas instaladas, otros vienen sin ellas. Confirma con el listing."),
            ("¿Necesito codificacion despues de instalar?",
             "Los faros LED modernos (BMW, Mercedes, Audi premium) requieren codificacion al modulo de "
             "iluminacion. Sin codificacion, pueden no encender o entrar en error."),
            ("¿Es del lado izquierdo o derecho?",
             "Confirma el lado. Faros L/R son distintos (no solo espejados — la curvatura interna del "
             "reflector cambia)."),
        ],
    },
    "faro_niebla": {
        "rubro": "faro antiniebla",
        "shopify_type": "Carrocería",
        "p1": (
            "Faro antiniebla (foglight) del vehiculo. Proporciona iluminacion adicional baja y amplia que "
            "mejora la visibilidad en niebla, lluvia intensa o polvo. Se monta en la facia delantera, "
            "tipicamente en aperturas dedicadas a cada lado. La luz es de patron horizontal ancho y bajo "
            "para no reflejarse en las gotas o particulas suspendidas. Puede ser halogena o LED segun el "
            "modelo y paquete del vehiculo."
        ),
        "faq": [
            ("¿Sirve para vehiculo sin faros antiniebla de fabrica?",
             "Generalmente no. La instalacion requiere cableado, switch y, en algunos modelos, "
             "codificacion al modulo de iluminacion. No es plug and play en autos sin la funcion de fabrica."),
            ("¿Es del lado izquierdo o derecho?",
             "Confirma con el listing. La mayoria son simetricos, pero hay modelos con foglights "
             "asimetricos."),
        ],
    },
    "calavera": {
        "rubro": "calavera / luz trasera",
        "shopify_type": "Carrocería",
        "p1": (
            "Calavera (luz trasera) del vehiculo. Integra luz de freno, posicion, direccional trasera, "
            "luz de reversa y, en algunos modelos, luz de niebla trasera. En vehiculos modernos europeos "
            "las calaveras son LED con diseños distintivos (ej. los 'L' de BMW Serie 3 F30, los OLED de "
            "Audi). Es pieza tipicamente afectada por impactos, oxidacion del cristal por UV, o entrada "
            "de humedad cuando los sellos se degradan. Algunos modelos tienen luces inner (en la cajuela) "
            "y outer (en la salpicadera trasera) que se compran por separado."
        ),
        "faq": [
            ("¿Es inner (cajuela) o outer (carrocer ia)?",
             "Confirma con el listing. Las inner se montan en la tapa de cajuela y se mueven con ella; las "
             "outer estan en la salpicadera fija. Cada una tiene codigo de parte distinto."),
            ("¿Es LED o bombillas convencionales?",
             "Verifica el codigo de parte. Los LED no son intercambiables con calaveras de bombillas "
             "tradicionales — el cableado y el modulo de control son distintos."),
            ("¿Trae los focos/leds?",
             "Tipicamente las calaveras LED vienen con los LEDs integrados (no se reemplazan). Las "
             "tradicionales pueden o no traer las bombillas — verifica el listing."),
        ],
    },
    "defensa": {
        "rubro": "defensa / parachoque (facia)",
        "shopify_type": "Carrocería",
        "p1": (
            "Defensa (parachoque o facia) del vehiculo. Es el panel de carroceria que cubre el frontal o "
            "la trasera, integra los faros, parrilla y soporte estructural contra impactos menores. En "
            "vehiculos modernos europeos la defensa es de plastico TPO o ABS pintado del color del auto, "
            "con espumas de absorcion de impacto detras y sensores de estacionamiento (PDC) y de angulo "
            "muerto integrados. Es pieza tipica de reemplazo en accidentes menores o cuando se daña por "
            "estacionarse contra topes y aceras."
        ),
        "faq": [
            ("¿Viene pintada del color de mi auto?",
             "No — la defensa viene en primer (gris/negro) lista para pintarse en taller del color exacto "
             "del vehiculo. La pintura se aplica antes de instalar."),
            ("¿Trae los sensores de estacionamiento (PDC)?",
             "No. Los sensores se transfieren del defensa original al nuevo. Si los originales estan "
             "danados, considera reemplazarlos como parte del trabajo."),
            ("¿Trae las bocas de los faros antiniebla?",
             "Generalmente si — las defensas tienen las aperturas para faros antiniebla, parrillas "
             "secundarias y sensores PDC ya hechas. Verifica con tu paquete (M Sport, AMG, S-Line) que "
             "coincida."),
            ("¿Cuanto se tarda la pintura?",
             "Trabajo de pintura de defensa toma 1-2 dias en taller especializado. Considera el plazo "
             "antes de comprar."),
        ],
    },
    "salpicadera": {
        "rubro": "salpicadera / guardafango / tolva",
        "shopify_type": "Carrocería",
        "p1": (
            "Salpicadera (guardafango o fender) o tolva interior. La salpicadera exterior es el panel de "
            "carroceria sobre la rueda delantera o trasera; la tolva (inner fender liner) es el panel de "
            "plastico interior que protege el compartimento del motor del agua, lodo y piedras. Ambas son "
            "piezas tipicas de reemplazo: la salpicadera por accidentes o impactos en el costado, la tolva "
            "por desgaste, rotura por golpes con piedras o degradacion del plastico."
        ),
        "faq": [
            ("¿Es salpicadera (carroceria) o tolva (interior)?",
             "Verifica el titulo. La salpicadera es panel exterior visible (se pinta), la tolva es panel "
             "interior plastico negro (no se pinta)."),
            ("¿Es del lado izquierdo o derecho?",
             "Confirma con el listing. Cada lado tiene codigo de parte distinto."),
            ("¿Viene pintada?",
             "Las salpicaderas exteriores vienen en primer y se pintan en taller del color del vehiculo. "
             "Las tolvas interiores son negras de fabrica, no se pintan."),
        ],
    },
    "cofre": {
        "rubro": "cofre / capot del motor",
        "shopify_type": "Carrocería",
        "p1": (
            "Cofre (capot, hood o bonnet) del vehiculo. Es el panel grande de carroceria que cubre el "
            "compartimento del motor y se abre para acceder al mantenimiento. En vehiculos europeos "
            "modernos puede ser de aluminio (BMW Serie 5, 7, X5, Audi A4, A6, A8) para reducir peso, o "
            "de acero estampado (modelos mas economicos). Las charnelas y el seguro deben transferirse "
            "del cofre original al nuevo."
        ),
        "faq": [
            ("¿Viene pintado?",
             "No — viene en primer y se pinta en taller del color exacto del vehiculo."),
            ("¿Es de aluminio o acero?",
             "Verifica el listing — es importante para el procedimiento de reparacion (soldadura aluminio "
             "vs acero) y para identificar el tipo correcto."),
            ("¿Trae las charnelas?",
             "Generalmente no. Las charnelas se transfieren del cofre original. Si las originales estan "
             "torcidas, comprarlas nuevas como parte del trabajo."),
        ],
    },
    "moldura": {
        "rubro": "moldura / embellecedor de carroceria",
        "shopify_type": "Carrocería",
        "p1": (
            "Moldura o embellecedor de carroceria. Son piezas decorativas que se montan en el exterior del "
            "vehiculo: bisel del faro, moldura del techo, embellecedor de la puerta, moldura del "
            "guardabarros, etc. Cumplen funcion estetica y, en algunos casos, protegen la carroceria de "
            "rayaduras menores. Las molduras cromadas son tipicas de Mini Cooper, BMW Serie 7 y Mercedes "
            "Clase E/S; las molduras negras son comunes en modelos M Sport, AMG y S-Line."
        ),
        "faq": [
            ("¿Es del lado izquierdo, derecho, o universal?",
             "Verifica el listing — algunas son simetricas, otras tienen lado especifico."),
            ("¿Como se instala?",
             "Tipicamente con clips a presion o cinta adhesiva 3M de doble cara. Algunas requieren clips "
             "nuevos (los originales se rompen al desmontar)."),
        ],
    },
    "manija": {
        "rubro": "manija / manilla de puerta",
        "shopify_type": "Carrocería",
        "p1": (
            "Manija (manilla, manija de puerta exterior) del vehiculo. Es la pieza que se acciona para "
            "abrir la puerta desde fuera, conectada al mecanismo de cierre de la puerta. En vehiculos "
            "europeos modernos puede integrar el sensor de proximidad para sistemas keyless (comfort "
            "access) que detecta la mano del usuario al acercarse. Falla tipica: rotura del mecanismo "
            "interno (no se abre la puerta), pintura descascarada por el uso, o falla del sensor "
            "keyless. Suele venir sin pintar."
        ),
        "faq": [
            ("¿Es del lado izquierdo o derecho?",
             "Confirma con el listing — cada lado tiene codigo de parte distinto."),
            ("¿Tiene sensor keyless?",
             "Verifica el codigo de parte. Las versiones con keyless integran un sensor capacitivo y un "
             "conector electrico, son codigos distintos."),
            ("¿Viene pintada?",
             "Generalmente no — viene en primer o sin pintar. Se pinta en taller del color exacto del "
             "vehiculo."),
        ],
    },
    "puerta": {
        "rubro": "puerta / panel de puerta",
        "shopify_type": "Carrocería",
        "p1": (
            "Puerta o panel de puerta del vehiculo. La puerta exterior es la estructura completa que se "
            "monta a las charnelas del marco; el panel interior es la cubierta plastica/acolchada visible "
            "desde la cabina. Pieza tipica de reemplazo despues de impactos laterales o cuando los paneles "
            "interiores se danan por uso. La puerta exterior viene sin componentes internos (cerradura, "
            "ventana, motor de la ventana) — todos se transfieren de la puerta original."
        ),
        "faq": [
            ("¿Trae componentes internos?",
             "No. La puerta exterior es solo la estructura. Cerradura, motor de ventana, vidrio y panel "
             "interior se transfieren de la original."),
            ("¿Viene pintada?",
             "No — viene en primer y se pinta en taller. Es trabajo de carroceria especializado."),
        ],
    },
    "limpiaparab": {
        "rubro": "componente del limpiaparabrisas",
        "shopify_type": "Carrocería",
        "p1": (
            "Componente del sistema de limpiaparabrisas (limpiabrisas, wiper). Puede ser brazo del "
            "limpiabrisas, motor del limpiabrisas, mecanismo de barras, o switch del control. El sistema "
            "incluye un motor electrico, un mecanismo de barras articuladas que mueve los brazos, y los "
            "brazos con sus plumas. Falla tipica: motor que se quema (limpiabrisas no se mueve), "
            "mecanismo de barras desgastado (brazos que no llegan a su posicion final), brazo doblado por "
            "impacto."
        ),
        "faq": [
            ("¿Por que no se mueve mi limpiabrisas?",
             "Causas comunes: motor quemado, fusible quemado, switch dañado, o mecanismo de barras "
             "desgastado. Diagnostico empieza revisando si el motor recibe voltaje al activar el switch."),
            ("¿Se cambia el motor o el conjunto?",
             "Depende del listing. Algunos vienen como conjunto motor + mecanismo, otros solo motor. "
             "Verifica antes de comprar."),
        ],
    },
    "soporte_defensa": {
        "rubro": "soporte / refuerzo de la defensa",
        "shopify_type": "Carrocería",
        "p1": (
            "Soporte o refuerzo de la defensa (bumper bracket, reinforcement bar). Es la estructura "
            "metalica o de espuma de absorcion de impacto que va detras de la facia delantera o trasera. "
            "Su funcion es absorber energia en impactos menores y proteger la estructura del vehiculo. "
            "Pieza tipica de reemplazo despues de accidentes — incluso cuando la defensa exterior parece "
            "intacta, el refuerzo puede estar deformado y debe cambiarse para asegurar la integridad "
            "estructural."
        ),
        "faq": [
            ("¿Por que cambiar el refuerzo si la defensa esta entera?",
             "El refuerzo absorbe la energia del impacto deformandose plasticamente. Una vez deformado, "
             "no recupera su capacidad de absorber otro impacto. Si hubo accidente, debe reemplazarse "
             "incluso si la defensa exterior se ve bien."),
            ("¿Es de metal o plastico?",
             "Depende del modelo. Los principales son de acero o aluminio; los absorbedores secundarios "
             "son de espuma de polipropileno expandido (EPP)."),
        ],
    },
    "absorbedor": {
        "rubro": "absorbedor de impacto / tope de defensa",
        "shopify_type": "Carrocería",
        "p1": (
            "Absorbedor de impacto (impact absorber, crash absorber) o tope de la defensa. Es el bloque "
            "de espuma EPP (polipropileno expandido) o estructura plastica que va entre la facia exterior "
            "y el refuerzo metalico, diseñado para absorber energia en impactos de baja velocidad. Pieza "
            "tipica de reemplazo despues de cualquier accidente, incluso menor, porque la espuma se "
            "deforma plasticamente y no recupera capacidad de absorcion."
        ),
        "faq": [
            ("¿Por que se cambia incluso en impactos pequeños?",
             "El material absorbe energia deformandose y no es elastico. Una vez deformado, queda "
             "permanentemente comprimido y no protege contra el siguiente impacto."),
        ],
    },
    "emblema": {
        "rubro": "emblema / logotipo de carroceria",
        "shopify_type": "Carrocería",
        "p1": (
            "Emblema o logotipo de carroceria. Pieza decorativa con el logo de la marca o modelo del "
            "vehiculo. Se monta en la parrilla, cofre, cajuela, salpicaderas o puertas segun el modelo. "
            "Estan fabricados en plastico cromado, metal pulido, o plastico esmaltado segun el acabado "
            "original. Es pieza pequeña pero visible que se reemplaza cuando el cromado se opaca, raya "
            "o se pica con los anos."
        ),
        "faq": [
            ("¿Como se instala?",
             "Con clips a presion (la mayoria) o cinta 3M de doble cara. Tipicamente toma 5-10 minutos."),
            ("¿Es original de la marca?",
             "Verifica el listing — algunos emblemas son OEM, otros son aftermarket de calidad similar. "
             "El acabado y la durabilidad varian."),
        ],
    },
    "aero": {
        "rubro": "componente aerodinamico (spoiler / aleron / faldon / lip)",
        "shopify_type": "Carrocería",
        "p1": (
            "Componente aerodinamico de carroceria (spoiler, aleron, faldon, lip). Pieza estetica y "
            "funcional que se monta en la defensa, cajuela o costado del vehiculo para alterar el flujo "
            "de aire a alta velocidad. Cumple funcion estetica deportiva y, en algunos casos, mejora la "
            "estabilidad reduciendo la sustentacion sobre el eje correspondiente. En modelos M, AMG, "
            "S-Line y JCW es elemento clave del kit estetico de fabrica."
        ),
        "faq": [
            ("¿Es para mi paquete (M Sport, AMG, S-Line)?",
             "Confirma con el listing. Los componentes aero varian por paquete — el de un BMW estandar no "
             "encaja en uno M Sport y viceversa."),
            ("¿Viene pintado?",
             "No — viene en negro o primer. Se pinta del color del vehiculo o se deja en negro segun el "
             "diseno deseado."),
        ],
    },
    "tolva": {
        "rubro": "tolva / inner fender liner",
        "shopify_type": "Carrocería",
        "p1": (
            "Tolva (inner fender liner, splash guard) del vehiculo. Es el panel de plastico que se monta "
            "en el interior del guardabarro, entre la rueda y el motor o cabina. Su funcion es bloquear "
            "el ingreso de agua, lodo, piedras y suciedad al compartimento del motor o a las cavidades "
            "interiores del vehiculo. Pieza tipica de reemplazo cuando se rompe por golpes con piedras, "
            "se desprende parcialmente, o se daña al subir topes o entrar a estacionamientos con vado "
            "alto."
        ),
        "faq": [
            ("¿Es del lado izquierdo o derecho?",
             "Confirma con el listing. Cada lado tiene codigo de parte distinto."),
            ("¿Es delantera o trasera?",
             "Las tolvas delanteras son las mas comunes (mayor exposicion). Tambien hay traseras en "
             "algunos modelos. Verifica el listing."),
        ],
    },
    "luna": {
        "rubro": "vidrio (luna) lateral o trasero",
        "shopify_type": "Carrocería",
        "p1": (
            "Cristal (luna) de carroceria. Puede ser de puerta lateral, trasera fija, o trasera abatible. "
            "Los vidrios modernos son templados o laminados segun la posicion (parabrisas siempre "
            "laminado, lunas laterales tipicamente templadas). Algunos integran calefactor electrico, "
            "antena de radio, o sensor de lluvia. Pieza tipica de reemplazo despues de roturas por "
            "vandalismo o impactos."
        ),
        "faq": [
            ("¿Trae el calefactor?",
             "Verifica el listing — el calefactor es un elemento adicional que aumenta el costo. Los "
             "vidrios sin calefactor tienen precio menor pero no son intercambiables."),
            ("¿Es para puerta o cuarto trasero (fijo)?",
             "Confirma la posicion exacta. Cada vidrio tiene curvatura y dimensiones especificas no "
             "intercambiables."),
        ],
    },
    "otro": {
        "rubro": "componente de carroceria",
        "shopify_type": "Carrocería",
        "p1": (
            "Componente de carroceria del vehiculo. Refaccion para vehiculos europeos. El listing "
            "especifica la pieza exacta y su posicion; si tienes dudas sobre compatibilidad o "
            "instalacion, envianos tu numero de VIN y un asesor te confirma los detalles."
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
    if "tolva" in t:
        return "tolva"
    if "luna" in t and "vidrio" not in t:
        return "luna"
    if "vidrio" in t or "cristal" in t:
        return "luna"
    if "faro" in t and ("niebla" in t or "antiniebla" in t or "fog" in t):
        return "faro_niebla"
    if "biofaro" in t or ("faro" in t and "giro" not in t and "espejo" not in t):
        return "faro"
    if "calavera" in t:
        return "calavera"
    if ("espejo" in t or "mirror" in t) and "calavera" not in t:
        return "espejo"
    if "direccional" in t and "espejo" in t:
        return "espejo"
    if "soporte" in t and ("defensa" in t or "facia" in t or "parachoq" in t):
        return "soporte_defensa"
    if "absorbedor" in t or "tope" in t and "defensa" in t:
        return "absorbedor"
    if "defensa" in t or "parachoque" in t or "bumper" in t or ("facia" in t and "spoiler" not in t and "moldura" not in t):
        return "defensa"
    if "parrilla" in t or "parrila" in t or "grill" in t:
        return "parrilla"
    if "rejilla" in t:
        return "rejilla"
    if "cofre" in t or "capot" in t:
        return "cofre"
    if "salpicadera" in t or "fender" in t or "guardafango" in t:
        return "salpicadera"
    if "puerta" in t and "manija" not in t:
        return "puerta"
    if "manija" in t or "manilla" in t or "handle" in t:
        return "manija"
    if "limpiabrisas" in t or "limpiaparab" in t or "wiper" in t:
        return "limpiaparab"
    if "emblema" in t or "logo" in t and "diamante" not in t:
        return "emblema"
    if "spoiler" in t or "aleron" in t or " lip " in t.replace(",", " ") or "faldon" in t:
        return "aero"
    if "moldura" in t or "embellecedor" in t or "bisel" in t:
        return "moldura"
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
            "Recomendamos confirmar con el numero de VIN antes de comprar — las piezas de carroceria "
            "varian frecuentemente por anio y por paquete (M Sport, AMG, S-Line, JCW)."
        )
    else:
        p2 = (
            "La descripcion original del listing menciona modelos compatibles pero no esta estructurada en el "
            "bloque APLICA PARA estandar, por lo que la lista no se pudo extraer automaticamente. "
            f"Por el titulo aplica a vehiculos {tipo_veh.lower() or 'tipo carro/camioneta'} de marcas europeas. "
            "Antes de comprar, envianos tu numero de VIN para que un asesor verifique modelo exacto, anio, "
            "paquete y configuracion contra el catalogo del proveedor."
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
            "antes de instalarla; comparalos contra el numero estampado en la pieza original de tu vehiculo."
        )
        if len(nps) > 1 or len(oems_list) > 1:
            p3_extras.append(
                "La presencia de varios numeros de parte indica consolidacion de referencias por anio "
                "o paquete; cualquiera aplica para la version actual."
            )
    else:
        p3_extras.append(
            "El listing no incluye numero de parte ni codigo OEM publicados. Antes de instalar, recomendamos "
            "comparar visualmente la pieza con la original o consultar con un taller especializado que tenga "
            "acceso al catalogo electronico del fabricante (ETKA para Audi/VW, ETIS para BMW)."
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
                "Vender en par es la presentacion estandar para piezas simetricas que se reemplazan al mismo tiempo, "
                "evitando diferencias de acabado o desgaste entre lados."
            )
        elif es_kit_local:
            p4 = (
                "Se entrega como kit completo en una sola caja con todos los componentes y la tornilleria de "
                "fijacion correspondiente."
            )
        else:
            tipo_pintura = ""
            if tipo in ("defensa", "salpicadera", "cofre", "puerta", "manija", "aero"):
                tipo_pintura = (
                    " La pieza se entrega en primer (acabado neutro listo para pintar) — debe pintarse en "
                    "taller del color exacto del vehiculo antes de instalar para que el acabado sea uniforme."
                )
            p4 = (
                "Se vende como pieza individual nueva, en empaque del fabricante. Producto no reciclado ni "
                "remanufacturado."
                + tipo_pintura
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
                "de procesar el pedido. Tambien puedes mencionar el paquete (M Sport, AMG, S-Line) y el "
                "anio del vehiculo."
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
            "Confirmar modelos, anios y paquete (M Sport, AMG, S-Line)."
        )
    if not numero_parte and not oem:
        revision.append("[BUSCAR] Numero de parte o codigo OEM faltantes.")
    if not sku:
        revision.append("[INCLUIR] SKU faltante — asignar antes de publicar.")
    if not marca_norm:
        revision.append("[ANALIZAR] Marca no identificada — confirmar fabricante.")
    if tipo in ("defensa", "salpicadera", "cofre", "puerta", "manija") and not lado:
        revision.append(
            "[VERIFICAR] Pieza de carroceria sin atributo 'Lado' especificado — confirmar L/R/Universal "
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
