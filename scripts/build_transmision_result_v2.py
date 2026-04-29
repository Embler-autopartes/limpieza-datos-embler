"""
Construye el JSON de resultados enriquecidos para refacciones_transmision (192 filas).

Tipos detectados por keywords del titulo:
  - goma_cardan:        junta de goma del cardan / disco flex (Hardyscheibe)
  - soporte_cardan:     soporte / balero / chumacera del cardan
  - cruceta_cardan:     cruceta universal joint del cardan
  - kit_clutch:         kit completo de clutch (disco + plato + collarin)
  - disco_clutch:       solo disco de clutch
  - plato_clutch:       solo plato de presion
  - volante_motor:      volante de motor / dual mass flywheel
  - bomba_clutch:       bomba maestra/esclava del clutch hidraulico
  - filtro_trans:       filtro de aceite de la transmision
  - reten_sello:        retenes y sellos
  - soporte_trans:      soporte / taco de transmision
  - cremallera:         caja de cremallera / direccion (raro en transmision)
  - mecatronica:        modulos TCU / mecatronica DSG
  - transfer:           caja transfer / engrane / servo transfer
  - flecha:             flechas / ejes de transmision
  - vanos:              kit reparacion VANOS BMW (mal clasificado, es motor)
  - otro:               fallback generico
"""

import json
import os
import re
import unicodedata
from collections import Counter

HOJA = os.environ.get("EMBLER_HOJA", "ml_con_match")
BATCH_PATH = f"new-output_v2/{HOJA}/refacciones_transmision_batch.json"
OUTPUT_PATH = f"new-output_v2/{HOJA}/refacciones_transmision_batch_result.json"


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
    raw_low = (marca_raw or "").lower()
    if "luk" in raw_low:
        return (
            "Marca LuK, proveedor OEM aleman de embragues y volantes de motor (parte de Schaeffler Group). "
            "Suministra a la fabrica para BMW, Mercedes, Audi, VW y otros."
        )
    if "sachs" in raw_low or "zf" in raw_low:
        return (
            f"Marca {marca_norm}, proveedor OEM aleman de embragues, amortiguadores y componentes de "
            "transmision. Calidad equivalente al equipo original."
        )
    if "febi" in raw_low or "vaico" in raw_low or "corteco" in raw_low:
        return (
            f"Marca {marca_norm}, proveedor europeo de refacciones aftermarket-OE con calidad equivalente "
            "al equipo original."
        )
    return f"Marca {marca_norm}, fabricante de refacciones para vehiculos europeos."


# ---------------------------------------------------------------------------
# Templates por tipo
# ---------------------------------------------------------------------------

TIPO_DEFINICIONES = {
    "goma_cardan": {
        "rubro": "junta de goma del cardan (disco flex)",
        "shopify_type": "Transmisión",
        "p1": (
            "Junta de goma del cardan (en aleman 'Hardyscheibe' o 'Gelenkscheibe', en ingles 'flex disc' o "
            "'guibo'). Es el disco de caucho reforzado con seis perforaciones que conecta el cardan o eje "
            "propulsor con la transmision o el diferencial trasero, absorbiendo las vibraciones de torsion "
            "del giro y permitiendo cierto grado de desalineacion entre los ejes. Es pieza de desgaste tipica "
            "en BMW de traccion trasera y AWD: con los anos el caucho se cuartea, aparecen vibraciones a "
            "velocidades especificas (60-100 km/h) y se escucha un golpe metalico al acelerar/desacelerar. Es "
            "una falla critica de seguridad — si se rompe completamente, el cardan puede desprenderse en "
            "movimiento."
        ),
        "faq": [
            ("¿Sintomas de junta de goma del cardan dañada?",
             "Vibracion a velocidades especificas (tipicamente 60-100 km/h), golpe metalico (clunk) al "
             "acelerar/desacelerar, ruido sordo al cambiar de marcha, o vibracion mas fuerte en aceleracion "
             "media. Sintomas progresivos — empiezan suaves y empeoran con el tiempo."),
            ("¿Es seguro seguir manejando con la junta dañada?",
             "Es riesgoso. Una junta cuarteada puede romperse completamente y soltar el cardan en movimiento, "
             "lo que es muy peligroso. Recomendamos reemplazo cuanto antes."),
            ("¿Necesito alineacion despues de cambiarla?",
             "El cambio en si no afecta la alineacion del vehiculo. Pero al desmontar el cardan se altera el "
             "balanceo del conjunto, asi que recomendamos verificar el centro del cardan y la chumacera "
             "(soporte) al mismo tiempo."),
            ("¿Vienen con tornilleria?",
             "Algunos kits incluyen los seis tornillos especiales con torque controlado. Confirma con el "
             "listing — si no, los tornillos deben reemplazarse siempre con tornillos nuevos del fabricante."),
        ],
    },
    "soporte_cardan": {
        "rubro": "soporte / chumacera del cardan",
        "shopify_type": "Transmisión",
        "p1": (
            "Soporte central del cardan (chumacera, balero o center bearing). Es el conjunto de soporte y "
            "rodamiento que sujeta el cardan o eje propulsor en su punto medio, manteniendolo alineado y "
            "absorbiendo las vibraciones del giro a alta velocidad. Esta compuesto por un balero sellado "
            "envuelto en un anillo de caucho que se fija al chasis del vehiculo. Es pieza de desgaste tipica "
            "en cardanes de dos secciones (BMW de longitud larga, Mercedes Sprinter, VW Crafter): el caucho "
            "se cuartea y el balero se afloja, generando vibracion a velocidades especificas y golpes al "
            "acelerar."
        ),
        "faq": [
            ("¿Sintomas de chumacera del cardan dañada?",
             "Vibracion a 80-120 km/h, golpe sordo al acelerar/desacelerar bajo carga, ruido tipo gemido en "
             "aceleracion media. La vibracion es mas fuerte que la de la junta de goma."),
            ("¿Cambio chumacera y junta de goma juntas?",
             "Es practica recomendada cuando ya hay desgaste de uno de los dos. El procedimiento de instalacion "
             "es el mismo y los componentes envejecen juntos."),
            ("¿Trae el balero o solo el caucho de soporte?",
             "Algunos vienen como conjunto completo (caucho + balero), otros solo el caucho. Confirma con "
             "el numero de parte exacto antes de comprar."),
        ],
    },
    "cruceta_cardan": {
        "rubro": "cruceta del cardan (junta universal)",
        "shopify_type": "Transmisión",
        "p1": (
            "Cruceta del cardan (universal joint, U-joint). Es la junta articulada en forma de cruz que "
            "permite la transmision de torque entre dos ejes con desalineacion angular. Esta compuesta por "
            "un cuerpo en cruz con cuatro brazos terminados en copas con baleros de agujas. Es pieza de "
            "desgaste tipica en cardanes con junta universal: cuando se desgasta provoca vibracion en "
            "aceleracion, golpe metalico al cambiar de marcha y, en casos avanzados, sonido de chillido. "
            "Si se rompe completamente, el cardan se desprende — es falla critica de seguridad."
        ),
        "faq": [
            ("¿Sintomas de cruceta dañada?",
             "Vibracion en aceleracion (especialmente a velocidad constante), golpe metalico claro al "
             "cambiar de adelante a reversa, sonido de chillido o tableteo en marchas bajas."),
            ("¿Cuantas crucetas tiene un cardan?",
             "Depende del modelo. Cardanes cortos suelen tener una sola; los de dos secciones (sedanes "
             "largos) tienen dos. Cuando una falla, conviene revisar las dos al mismo tiempo."),
            ("¿Es comun cambiarla con la goma del cardan?",
             "Si — los componentes del cardan envejecen juntos y el procedimiento de desmontaje es similar. "
             "Considera kit cardan completo si el vehiculo tiene mas de 200,000 km."),
        ],
    },
    "kit_clutch": {
        "rubro": "kit de clutch (embrague) completo",
        "shopify_type": "Transmisión",
        "p1": (
            "Kit completo de clutch (embrague) para transmision manual. Es el conjunto de componentes que "
            "transmite el torque del motor a la caja de velocidades, permitiendo desconectar la transmision "
            "del motor para cambiar de marcha. Un kit estandar incluye disco de clutch (la pieza con material "
            "de friccion que se aprieta entre el volante y el plato), plato de presion (la canasta de muelles "
            "que aprieta el disco contra el volante), y collarin (rodamiento que actua sobre los dedos del "
            "plato cuando se pisa el pedal). Es pieza de desgaste con vida util tipica de 100,000 a 200,000 km "
            "segun el estilo de manejo."
        ),
        "faq": [
            ("¿Que incluye el kit?",
             "Disco de clutch, plato de presion y collarin. Algunos kits incluyen tambien el balero piloto "
             "y herramienta de centrado. Verifica el listing."),
            ("¿Necesito cambiar el volante motor tambien?",
             "Si tu volante motor es dual mass (DMF) y tiene mas de 150,000 km, considera reemplazarlo al "
             "mismo tiempo. Cambiar solo el clutch sobre un DMF dañado reduce drasticamente la vida del nuevo kit."),
            ("¿Sintomas de clutch desgastado?",
             "Pedal blando o que patina al acelerar (motor sube de vueltas pero el auto no acelera "
             "proporcionalmente), ruido al pisar el pedal, dificultad para meter primera o reversa, olor a "
             "quemado en aceleraciones."),
            ("¿Cuanto se tarda la instalacion?",
             "Entre 6 y 10 horas de mano de obra dependiendo del modelo. La caja de velocidades debe "
             "desmontarse para acceder al clutch."),
        ],
    },
    "disco_clutch": {
        "rubro": "disco de clutch",
        "shopify_type": "Transmisión",
        "p1": (
            "Disco de clutch (placa de fricci on del embrague) para transmision manual. Es la pieza con "
            "material de friccion que se aprieta entre el volante motor y el plato de presion, transmitiendo "
            "el torque del motor a la caja de velocidades. Tiene un cubo central con dientes interiores que "
            "encaja en el eje primario de la caja, y muelles de torsion en el cubo que absorben las "
            "vibraciones. Es pieza de desgaste — la vida util depende del estilo de manejo y del estado del "
            "plato y el volante."
        ),
        "faq": [
            ("¿Cambio solo el disco o el kit completo?",
             "Si solo el disco esta gastado y el plato/collarin estan en buen estado, puedes cambiar solo "
             "el disco. Pero como el procedimiento de instalacion requiere desmontar la caja, casi siempre "
             "compensa cambiar el kit completo."),
            ("¿De que material es la friccion?",
             "Material organico reforzado en la mayoria de los discos de calle. Aplicaciones de alto "
             "rendimiento usan material ceramico-metalico (mayor durabilidad pero menos progresivo)."),
        ],
    },
    "plato_clutch": {
        "rubro": "plato de presion del clutch",
        "shopify_type": "Transmisión",
        "p1": (
            "Plato de presion del clutch (canasta del embrague). Es la pieza con muelles de diafragma o de "
            "espirales que aprieta el disco de clutch contra el volante motor, permitiendo la transmision de "
            "torque cuando el pedal esta suelto. Cuando se pisa el pedal, los dedos del plato se levantan y "
            "liberan el disco, desacoplando motor y transmision. Es pieza de desgaste — los muelles se aflojan "
            "con los anos, reduciendo la fuerza de apriete y provocando que el clutch patine."
        ),
        "faq": [
            ("¿Sintomas de plato debilitado?",
             "Clutch que patina en aceleraciones fuertes (motor sube de RPM pero el auto no acelera), pedal "
             "que se siente blando o sin progresion."),
            ("¿Conviene cambiar plato sin disco?",
             "Solo si el disco esta nuevo o casi nuevo. Generalmente se cambian juntos por el costo de "
             "instalacion."),
        ],
    },
    "volante_motor": {
        "rubro": "volante motor (DMF cuando aplica)",
        "shopify_type": "Transmisión",
        "p1": (
            "Volante motor (flywheel). Es el disco de hierro fundido o acero que se monta directamente en "
            "el ciguenal y proporciona la masa rotativa que mantiene el motor girando entre pulsos de "
            "combustion. Tambien es la superficie de friccion contra la que el clutch aprieta el disco. Hay "
            "dos tipos: monomasa (single mass flywheel, SMF) — disco solido tradicional; y dual mass (dual "
            "mass flywheel, DMF) — dos discos conectados por muelles que absorben vibraciones de torsion del "
            "ciguenal, especialmente en motores diesel y turbo. El DMF es pieza de desgaste con vida util "
            "limitada a 150,000-250,000 km."
        ),
        "faq": [
            ("¿Como se que mi volante DMF necesita reemplazo?",
             "Sintomas: vibracion en ralenti, ruido de tableteo metalico al apagar el motor, dificultad para "
             "arrancar, olor a quemado del clutch incluso cuando es nuevo."),
            ("¿Puedo cambiar mi DMF por uno solido (SMF)?",
             "Hay kits de conversion DMF-SMF para algunos modelos, pero implican vibraciones aumentadas. "
             "No recomendado en autos de uso diario premium europeos."),
            ("¿Trae los tornillos de montaje?",
             "Los tornillos del volante motor son TTY (torque-to-yield) y deben reemplazarse siempre. "
             "Verifica si vienen incluidos en el kit."),
        ],
    },
    "filtro_trans": {
        "rubro": "filtro de aceite de la transmision",
        "shopify_type": "Transmisión",
        "p1": (
            "Filtro de aceite de la transmision automatica. Su funcion es atrapar particulas metalicas y "
            "contaminantes del aceite ATF para que no danen las solenoides, valvulas y embragues internos "
            "de la caja. Es pieza de mantenimiento periodico — el cambio de aceite ATF en transmisiones "
            "automaticas modernas (ZF 6HP/8HP, BMW, Mercedes 7G-Tronic) requiere obligatoriamente cambiar "
            "el filtro al mismo tiempo. Algunos filtros vienen integrados con la cuba de aceite (filter pan "
            "assembly), otros son piezas independientes."
        ),
        "faq": [
            ("¿Cada cuanto se cambia el filtro de transmision?",
             "Cada 80,000-100,000 km en transmisiones modernas, junto con el aceite ATF. Algunos fabricantes "
             "marcan el ATF como 'lifetime' (no requiere cambio), pero los talleres recomiendan cambio "
             "preventivo cada 80-100k km para alargar la vida de la caja."),
            ("¿Trae el sello de la cuba?",
             "La mayoria de los kits incluyen junta de la cuba y, en algunos casos, los tornillos. "
             "Verifica con el listing."),
            ("¿Que aceite ATF usar?",
             "Depende del modelo y anio. Las cajas ZF 8HP requieren aceite especifico (Lifeguard 8 o "
             "equivalente). Consulta el manual o el numero de parte del aceite original."),
        ],
    },
    "reten_sello": {
        "rubro": "reten / sello",
        "shopify_type": "Transmisión",
        "p1": (
            "Reten o sello para componentes de la transmision o eje motriz. Su funcion es contener el aceite "
            "del componente (caja de velocidades, diferencial, transmision automatica) y bloquear el ingreso "
            "de polvo y agua. Esta fabricado en goma fluorada (Viton) o NBR con esqueleto metalico interior. "
            "Es pieza de desgaste tipica que se reemplaza siempre que se desmonta el componente del que "
            "sella, ya que el labio interior se cuartea y pierde su capacidad de sellado."
        ),
        "faq": [
            ("¿Cuando reemplazar el reten?",
             "Siempre que haya fuga visible, o de manera preventiva cada vez que se desmonta el componente "
             "(diferencial, caja de velocidades). Es barato comparado con el costo de mano de obra."),
            ("¿De que material es?",
             "Goma fluorada (Viton) en aplicaciones de alta temperatura, NBR estandar en aplicaciones "
             "convencionales. Verifica si el listing especifica el material."),
        ],
    },
    "soporte_trans": {
        "rubro": "soporte / taco de transmision",
        "shopify_type": "Transmisión",
        "p1": (
            "Soporte de transmision (transmission mount). Es el bloque de caucho-metal que sujeta la caja "
            "de velocidades al chasis del vehiculo, absorbiendo las vibraciones de la transmision y manteniendo "
            "su alineacion con el motor. Esta compuesto por un soporte metalico envuelto o conectado por "
            "elementos de caucho vulcanizado, en algunos casos con camara hidraulica para amortiguar mejor "
            "las vibraciones. Es pieza de desgaste tipica: el caucho se cuartea con los anos y aparecen "
            "vibraciones en ralenti, golpes al cambiar de marcha y movimiento excesivo de la palanca de "
            "cambios."
        ),
        "faq": [
            ("¿Sintomas de soporte de transmision dañado?",
             "Vibracion en ralenti (especialmente con caja en D o R), golpes al cambiar de marcha o al pisar "
             "el clutch, palanca de cambios que se mueve mucho, sonido sordo al acelerar."),
            ("¿Cambio el del motor al mismo tiempo?",
             "Es practica recomendada — los soportes del motor y de la transmision envejecen juntos. Cambiar "
             "solo uno deja al otro como punto debil."),
        ],
    },
    "mecatronica": {
        "rubro": "mecatronica / modulo TCU de transmision",
        "shopify_type": "Transmisión",
        "p1": (
            "Modulo de mecatronica (TCU - Transmission Control Unit). Es la unidad electronica que controla "
            "la transmision automatica moderna: gestiona la activacion de los embragues internos, la presion "
            "del aceite ATF, las solenoides de cambio y la sincronizacion con la ECU del motor. En "
            "transmisiones DSG/S-tronic Volkswagen-Audi y ZF de BMW, la mecatronica integra solenoides, "
            "valvulas y modulo electronico en una sola unidad sumergida en aceite ATF. Es una pieza compleja "
            "y costosa cuyas fallas pueden requerir codificacion despues del reemplazo."
        ),
        "faq": [
            ("¿Sintomas de mecatronica dañada?",
             "Cambios bruscos o duros, transmision que entra en modo de emergencia (limp mode), codigos de "
             "error de transmision, vehiculo que no responde al pisar el acelerador. Diagnostico definitivo "
             "con scanner especifico."),
            ("¿Necesita codificacion despues del reemplazo?",
             "Si — la mecatronica nueva debe codificarse al VIN del vehiculo y al numero de motor. Sin "
             "codificacion, no funciona o entra en modo de emergencia."),
            ("¿Vale la pena reparar o reemplazar?",
             "Si los problemas son electronicos (solenoides), hay reparaciones especializadas. Si la falla "
             "es estructural (cuerpo de valvulas, baleros internos), el reemplazo completo es mas confiable."),
        ],
    },
    "transfer": {
        "rubro": "componente de la caja transfer (4WD/AWD)",
        "shopify_type": "Transmisión",
        "p1": (
            "Componente de la caja transfer del sistema 4WD/AWD. La caja transfer distribuye el torque de "
            "la transmision entre el eje delantero y trasero en vehiculos con traccion total. En BMW xDrive, "
            "Mercedes 4Matic y Audi quattro, la caja transfer incluye un servomotor electronico (transfer "
            "case actuator) que ajusta la distribucion de torque segun condiciones de manejo. Las fallas mas "
            "frecuentes son del servomotor (engrane interno, motor electrico) o de los baleros del eje "
            "primario."
        ),
        "faq": [
            ("¿Sintomas de servo transfer dañado?",
             "Codigo de error de la transmision (4WD malfunction), perdida de traccion en una rueda, "
             "vibracion en aceleracion fuerte, o ruido tipo zumbido al acelerar."),
            ("¿Es comun en BMW xDrive?",
             "Si — el servo transfer del xDrive es punto debil conocido. La pieza original es costosa, "
             "pero hay opciones aftermarket de calidad equivalente."),
        ],
    },
    "flecha": {
        "rubro": "flecha / eje propulsor de la transmision",
        "shopify_type": "Transmisión",
        "p1": (
            "Flecha (eje propulsor o axle shaft) de la transmision. Conecta la transmision con la rueda "
            "motriz, transmitiendo el torque y permitiendo el movimiento del eje a traves de juntas "
            "homocineticas (CV joints) que toleran el angulo cambiante por la suspension y la direccion. "
            "Es pieza de desgaste tipica: cuando una junta CV se daña aparece un golpe (clicking) al girar "
            "y a baja velocidad, especialmente en curvas."
        ),
        "faq": [
            ("¿Sintomas de flecha dañada?",
             "Click-click-click al acelerar en curvas (junta CV exterior), golpe sordo al acelerar/desacelerar "
             "(junta CV interior), grasa visible en la llanta o bajo el vehiculo (rotura del polvera)."),
            ("¿Cambio flecha o solo la junta CV?",
             "Hay kits de junta CV, pero la mayoria de los talleres recomiendan flecha completa por el costo "
             "de mano de obra similar y la garantia mejor."),
        ],
    },
    "vanos": {
        "rubro": "kit reparacion VANOS (admision variable)",
        "shopify_type": "Motor",  # VANOS es del motor, no transmision
        "p1": (
            "Kit de reparacion del sistema VANOS (Variable NOckenwellen Spreizung — variacion del arbol de "
            "levas) para motores BMW M52, M54 y M56. El sistema VANOS regula hidraulicamente la posicion del "
            "arbol de levas para optimizar potencia y consumo. El kit de reparacion reemplaza los sellos y "
            "anillos internos que se degradan con los anos, restaurando la funcion sin necesidad de "
            "reemplazar la unidad VANOS completa. Es trabajo especializado pero comun en talleres BMW."
        ),
        "faq": [
            ("¿Que problema soluciona el kit?",
             "Sellos VANOS desgastados que provocan codigos de error (P1004, P1006), perdida de torque a "
             "bajas RPM, ruido tipo cascabel al arrancar el motor, o consumo de aceite incrementado."),
            ("¿Es comun de reemplazar?",
             "Si — el kit VANOS es mantenimiento conocido en BMW M52/M54/M56 con mas de 150,000 km. "
             "Restaura el rendimiento original sin el costo de un VANOS completo."),
        ],
    },
    "otro": {
        "rubro": "componente de la transmision",
        "shopify_type": "Transmisión",
        "p1": (
            "Componente del sistema de transmision o tren motriz del vehiculo. Refaccion para vehiculos "
            "europeos — verifica el titulo y las especificaciones del listing para identificar exactamente "
            "la funcion de la pieza dentro del sistema. Si tienes dudas sobre la funcion exacta o como se "
            "monta, envianos tu numero de VIN y un asesor te confirma compatibilidad y procedimiento."
        ),
        "faq": [
            ("¿Como confirmo que es la pieza correcta?",
             "Envianos tu numero de VIN y, si tienes, el numero de parte de la pieza original que estas "
             "reemplazando. Validamos contra el catalogo del fabricante antes de procesar el pedido."),
        ],
    },
}


def detectar_tipo(titulo: str) -> str:
    t = titulo.lower()
    if ("junta" in t and "cardan" in t) or ("goma" in t and "cardan" in t):
        return "goma_cardan"
    if "soporte" in t and "cardan" in t or "balero" in t and "cardan" in t or "chumacera" in t or "chumasera" in t or "chumazera" in t:
        return "soporte_cardan"
    if "cruceta" in t and "cardan" in t:
        return "cruceta_cardan"
    if "kit" in t and ("clutch" in t or "embrague" in t):
        return "kit_clutch"
    if "disco" in t and ("clutch" in t or "embrague" in t):
        return "disco_clutch"
    if "plato" in t and ("clutch" in t or "embrague" in t or "presion" in t):
        return "plato_clutch"
    if "volante" in t and ("motor" in t or "doble" in t or "dual" in t):
        return "volante_motor"
    if "filtro" in t and ("transm" in t or "caja" in t):
        return "filtro_trans"
    if "reten" in t or "sello" in t:
        return "reten_sello"
    if "soporte" in t and ("transm" in t or "caja" in t):
        return "soporte_trans"
    if "mecatronic" in t or ("modulo" in t and ("tcu" in t or "transm" in t)):
        return "mecatronica"
    if "transfer" in t or ("servomotor" in t and "transfer" in t) or ("engrane" in t and "transfer" in t):
        return "transfer"
    if "flecha" in t or ("eje" in t and "transm" in t) or ("junta" in t and "homocinetica" in t):
        return "flecha"
    if "vanos" in t:
        return "vanos"
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
            "Recomendamos confirmar con el numero de VIN antes de comprar para asegurar que la pieza corresponde "
            "exactamente a tu version, configuracion y opcionales."
        )
    else:
        p2 = (
            "La descripcion original del listing menciona modelos compatibles pero no esta estructurada en el "
            "bloque APLICA PARA estandar, por lo que la lista no se pudo extraer automaticamente. "
            f"Por el titulo aplica a vehiculos {tipo_veh.lower() or 'tipo carro/camioneta'} de marcas europeas. "
            "Antes de comprar, envianos tu numero de VIN para que un asesor verifique modelo exacto, anio y "
            "configuracion contra el catalogo del proveedor."
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
                "La presencia de varios numeros de parte indica que el fabricante consolido referencias "
                "que antes se vendian por separado en distintos anios o paquetes; cualquiera aplica."
            )
    else:
        p3_extras.append(
            "El listing no incluye numero de parte ni codigo OEM publicados. Antes de instalar, recomendamos "
            "comparar visualmente la pieza con la original o consultar con un taller especializado que tenga "
            "acceso al catalogo electronico del fabricante (ETKA para Audi/VW, ETIS para BMW)."
        )
    if p["lado"]:
        p3_extras.append(f"Lado de instalacion: {p['lado']}.")
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
                "Vender en par es la presentacion estandar para piezas simetricas que se reemplazan al mismo tiempo."
            )
        elif es_kit_local:
            p4 = (
                "Se entrega como kit completo en una sola caja con todos los componentes y la tornilleria de "
                "fijacion correspondiente. Reduce tiempos de inventario en taller y asegura compatibilidad entre piezas."
            )
        else:
            p4 = (
                "Se vende como pieza individual nueva, en empaque del fabricante. Producto no reciclado ni "
                "remanufacturado. Si tu reparacion requiere reemplazar la pieza tambien en el lado opuesto o "
                "en componentes relacionados, consulta con nuestro asesor."
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
    if tipo == "vanos":
        revision.append(
            "[ANALIZAR] Producto es del sistema VANOS (motor), no transmision. Considerar mover a refacciones_motor."
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
