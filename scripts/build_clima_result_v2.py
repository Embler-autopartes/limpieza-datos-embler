"""
Construye el JSON de resultados enriquecidos para refacciones_clima (131 filas).

Tipos detectados por keywords del titulo:
  - manguera_radiador: mangueras de radiador, deposito anticongelante, refrigerante
  - codo_aceleracion:  codos del cuerpo de aceleracion (admision)
  - compresor:         compresores de aire acondicionado
  - condensador:       condensadores AC
  - evaporador:        evaporadores AC
  - resistor:          resistencias / herizos del soplador
  - ventilador:        motoventiladores / motores soplador
  - valvula_disa:      valvulas DISA del sistema de admision
  - valvula_bolsa:     valvulas de bolsa de aire suspension neumatica
  - valvula_expansion: valvulas de expansion AC
  - filtro_cabina:     filtros de polen / cabina
  - tubo_agua:         tubos de agua de calefaccion
  - servo_flap:        servos del flap de direccion de aire
  - sensor_clima:      sensores de temperatura cabina
  - switch_presion:    presostatos AC
"""

import json
import os
import re
import unicodedata
from collections import Counter

HOJA = os.environ.get("EMBLER_HOJA", "ml_con_match")
BATCH_PATH = f"new-output_v2/{HOJA}/refacciones_clima_batch.json"
OUTPUT_PATH = f"new-output_v2/{HOJA}/refacciones_clima_batch_result.json"


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
    if any(b in raw_low for b in ("mahle", "behr")):
        return (
            "Marca Mahle/Behr, proveedor OEM aleman de sistemas de gestion termica del motor (radiadores, "
            "intercoolers, valvulas EGR, filtros). Suministra a la fabrica para BMW, Mercedes, Audi, VW y otros."
        )
    if "valeo" in raw_low:
        return (
            "Marca Valeo, proveedor OEM frances de sistemas de gestion termica y limpiaparabrisas. "
            "Calidad equivalente al equipo original instalado por el fabricante del vehiculo."
        )
    if "bosch" in raw_low:
        return (
            "Marca Bosch, proveedor OEM aleman de electronica y mecatronica automotriz. Calidad "
            "equivalente al equipo original instalado por el fabricante del vehiculo."
        )
    if any(b in raw_low for b in ("febi", "vaico", "corteco")):
        return (
            f"Marca {marca_norm}, proveedor europeo de refacciones aftermarket-OE con calidad equivalente "
            "al equipo original. Especializada en gestion termica, suspension y motor."
        )
    return f"Marca {marca_norm}, fabricante de refacciones para vehiculos europeos."


# ---------------------------------------------------------------------------
# Templates por tipo
# ---------------------------------------------------------------------------

TIPO_DEFINICIONES = {
    "manguera_radiador": {
        "rubro": "manguera del sistema de refrigeracion",
        "shopify_type": "Motor",  # sistema de refrigeracion = motor
        "p1": (
            "Manguera del sistema de refrigeracion del motor. Su funcion es transportar el liquido refrigerante "
            "(anticongelante) entre los componentes del circuito termico: radiador, bomba de agua, termostato, "
            "calefactor de cabina y motor. Esta fabricada en caucho EPDM con refuerzos textiles internos para "
            "soportar las temperaturas de operacion del motor (hasta 130 °C en regimenes altos) y la presion del "
            "sistema (1.0 a 1.5 bar segun el modelo). Es una pieza de mantenimiento periodico que se reemplaza "
            "cuando muestra grietas, abultamientos, fugas en las conexiones o endurecimiento del material."
        ),
        "faq": [
            ("¿Cada cuanto se cambia una manguera de refrigeracion?",
             "No tiene un intervalo fijo, pero se recomienda inspeccionarla cada vez que se haga servicio mayor del motor. "
             "Sintomas de cambio: grietas en la superficie, abultamientos, manchas de refrigerante en las conexiones, "
             "endurecimiento del material o sobrecalentamiento del motor."),
            ("¿Es la pieza correcta para mi vehiculo?",
             "Verifica el numero de parte de tu manguera original y comparalo con el listing. Las mangueras varian "
             "por modelo, anio y motor — no son universales aunque parezcan similares."),
            ("¿Se vende con abrazaderas?",
             "El listing no incluye abrazaderas salvo que se especifique. Es buena practica reemplazarlas al mismo "
             "tiempo que la manguera para asegurar el sello correcto."),
        ],
    },
    "codo_aceleracion": {
        "rubro": "manguera de admision (codo del cuerpo de aceleracion)",
        "shopify_type": "Motor",
        "p1": (
            "Manguera o codo del cuerpo de aceleracion (intake boot). Es el ducto flexible que conecta el cuerpo "
            "de aceleracion (throttle body) con el colector de admision o, en motores con MAF, el conducto que "
            "viene del filtro de aire. Permite que el aire de admision pase del filtro a la camara de combustion "
            "y aisla mecanicamente la vibracion del motor. Esta fabricada en caucho EPDM o silicona reforzada para "
            "resistir las temperaturas (hasta 100 °C) y los pulsos de presion del sistema de admision. Es pieza "
            "de desgaste tipica: con los anos el caucho se endurece y aparecen grietas que provocan fugas de aire "
            "no medido (false air), generando codigos de error de mezcla pobre o ralenti irregular."
        ),
        "faq": [
            ("¿Como se que mi codo de admision esta dañado?",
             "Sintomas comunes: ralenti irregular, codigos de error de mezcla pobre (P0171, P0174), perdida de "
             "potencia en aceleracion, sonido de aire al acelerar. Inspecciona visualmente el codo buscando "
             "grietas, especialmente en los pliegues."),
            ("¿Es facil de instalar?",
             "Si — se sueltan las abrazaderas en cada extremo y se reemplaza la pieza. Tarda unos 15-30 minutos "
             "en taller. Recomendamos cambiar las abrazaderas tambien."),
            ("¿Vale la pena el OEM o sirve aftermarket?",
             "El caucho EPDM aftermarket de calidad rinde igual que el OEM. Lo importante es que las medidas "
             "de los extremos coincidan exactamente — por eso es critico verificar el numero de parte."),
        ],
    },
    "compresor": {
        "rubro": "compresor de aire acondicionado",
        "shopify_type": "Sistema de Aire Acondicionado",
        "p1": (
            "Compresor del sistema de aire acondicionado. Es el corazon del circuito A/C: comprime el refrigerante "
            "gaseoso (R134a o R1234yf segun el modelo y anio) elevando su presion y temperatura para que pueda "
            "ceder calor al ambiente en el condensador. Recibe el movimiento del motor a traves de la banda "
            "auxiliar y un embrague electromagnetico que lo activa cuando la ECU del aire acondicionado lo "
            "solicita. Es una pieza compleja con piston(es) o scroll, valvula de control de desplazamiento "
            "variable (en compresores modernos de capacidad variable) y un sistema de lubricacion interna con "
            "aceite refrigerante PAG. Una falla del compresor suele manifestarse como aire que no enfria, ruidos "
            "metalicos al activar el A/C, o fuga de refrigerante por el sello del eje."
        ),
        "faq": [
            ("¿Cuanto dura un compresor de A/C?",
             "Entre 8 y 12 anos en uso normal. Se acorta si el sistema funciona con baja carga de refrigerante "
             "(falta de lubricacion) o si entra contaminacion al circuito por mantenimiento incorrecto."),
            ("¿Necesito cambiar la valvula de expansion y el deshidratador al mismo tiempo?",
             "Es practica recomendada cuando se reemplaza el compresor por falla mecanica, especialmente si el "
             "compresor anterior solto particulas al sistema. La valvula de expansion y el filtro deshidratador "
             "previenen que esas particulas dañen el compresor nuevo."),
            ("¿El compresor viene con aceite y embrague?",
             "Verifica el listing — algunos compresores se entregan con la cantidad de aceite PAG correspondiente "
             "y con el embrague electromagnetico instalado, otros solo el cuerpo (compresor seco). Confirma con "
             "nuestro asesor antes de comprar."),
            ("¿Que tipo de refrigerante usa?",
             "Depende del modelo y anio del vehiculo: R134a en autos hasta ~2017, R1234yf en modelos posteriores. "
             "Verifica la etiqueta de tu sistema A/C antes de cargar refrigerante."),
        ],
    },
    "condensador": {
        "rubro": "condensador de aire acondicionado",
        "shopify_type": "Sistema de Aire Acondicionado",
        "p1": (
            "Condensador del sistema de aire acondicionado. Es el intercambiador de calor que recibe el "
            "refrigerante gaseoso a alta presion y temperatura desde el compresor, y lo enfria forzando el paso "
            "de aire ambiente a traves de sus aletas, condensandolo a estado liquido. Se ubica en el frente del "
            "vehiculo, delante del radiador del motor, donde recibe flujo de aire por el avance del vehiculo y "
            "por el ventilador electrico. Esta fabricado en aluminio con multiples microcanales internos para "
            "maximizar la superficie de intercambio termico. Es una pieza vulnerable a impactos por piedras y a "
            "obstruccion por suciedad acumulada entre las aletas — y a corrosion por humedad y sal en zonas "
            "costeras o con salado de carreteras en invierno."
        ),
        "faq": [
            ("¿Como se que mi condensador necesita reemplazo?",
             "Sintomas: aire acondicionado enfria poco a velocidad baja pero mejor en marcha (pobre ventilacion "
             "del condensador), fugas visibles de aceite/refrigerante en el frente del vehiculo, dano fisico "
             "por impactos."),
            ("¿Cuando cambio el deshidratador junto al condensador?",
             "Siempre que se abre el circuito A/C es buena practica reemplazar el filtro deshidratador, ya que "
             "absorbe humedad atmosferica en cuanto se expone."),
            ("¿Trae sensor de presion incluido?",
             "Algunos condensadores integran el switch de presion en el costado, otros se compran por separado. "
             "Confirma el numero de parte exacto antes de comprar."),
        ],
    },
    "evaporador": {
        "rubro": "evaporador de aire acondicionado",
        "shopify_type": "Sistema de Aire Acondicionado",
        "p1": (
            "Evaporador del sistema de aire acondicionado. Es el intercambiador de calor instalado dentro de la "
            "caja de climatizacion (HVAC) bajo el tablero, donde el refrigerante liquido a baja presion absorbe "
            "calor del aire que pasa por las aletas, evaporandose y enfriando el flujo de aire que entra a la "
            "cabina. Esta fabricado en aluminio con microcanales y aletas finas. Es susceptible a fugas por "
            "corrosion interna y a obstruccion del drenaje, lo que provoca olor a humedad y goteo de agua dentro "
            "de la cabina. Su reemplazo requiere desmontar el tablero del vehiculo, por lo que es una de las "
            "intervenciones mas laboriosas del sistema A/C."
        ),
        "faq": [
            ("¿Por que mi A/C huele mal?",
             "Lo mas comun es bacterias y hongos en el evaporador por humedad acumulada, no necesariamente que "
             "el evaporador este dañado. Antes de reemplazarlo, prueba un servicio de desinfeccion del HVAC y "
             "limpieza del drenaje del evaporador."),
            ("¿Cuanto se tarda el reemplazo?",
             "Es de las reparaciones mas largas del sistema A/C — entre 6 y 12 horas de mano de obra, ya que "
             "requiere desmontar buena parte del tablero. Costo de mano de obra alto, considera el presupuesto "
             "completo antes de comprar la pieza."),
            ("¿Trae sensor de temperatura del evaporador?",
             "Algunos modelos integran el sensor en el cuerpo del evaporador, otros lo tienen separado. "
             "Confirma con el numero de parte antes de comprar."),
        ],
    },
    "resistor": {
        "rubro": "resistencia (herizo) del soplador del aire acondicionado",
        "shopify_type": "Sistema de Aire Acondicionado",
        "p1": (
            "Resistencia (tambien llamada 'herizo' por su forma o 'modulo de control del soplador') del motor "
            "del soplador del aire acondicionado. Su funcion es regular la velocidad del ventilador del HVAC "
            "controlando la potencia electrica que recibe el motor; en sistemas de control manual lo hace por "
            "diferencia de resistencia entre los pasos de velocidad, en sistemas climatronic modernos lo hace "
            "por modulacion electronica (PWM). Es pieza de falla tipica: cuando se quema, el ventilador deja "
            "de funcionar en algunas velocidades (tipicamente las bajas) o se apaga completamente; tambien "
            "puede soltar olor a quemado y, en casos extremos, causar fundicion del conector del soplador."
        ),
        "faq": [
            ("¿Sintomas de una resistencia del soplador dañada?",
             "El ventilador funciona solo en velocidad maxima pero no en las bajas (o viceversa), no funciona "
             "del todo, hace ruido al iniciar o emite olor a quemado al activar el A/C."),
            ("¿Que diferencia hay entre 'herizo' y 'resistencia'?",
             "Son sinonimos. 'Herizo' (a veces escrito 'herizo' o 'erizo') es el termino mexicano coloquial por "
             "la forma de la pieza, con multiples disipadores en aletas que parecen erizo."),
            ("¿Es comun cambiar tambien el conector?",
             "Si la resistencia se quemo por sobrecalentamiento, frecuentemente el conector electrico tambien se "
             "daño. Inspeccionalo durante la instalacion — un conector dañado quema la resistencia nueva en pocas "
             "semanas."),
        ],
    },
    "ventilador": {
        "rubro": "motoventilador / motor del soplador",
        "shopify_type": "Sistema de Aire Acondicionado",
        "p1": (
            "Motor del ventilador (motoventilador o blower motor) del sistema de climatizacion. Hay dos tipos en "
            "el vehiculo: el motor del soplador interior (mueve el aire desde el evaporador hacia las salidas de "
            "la cabina) y el motoventilador electrico del frente del vehiculo (que enfria el radiador y el "
            "condensador A/C cuando el avance del vehiculo no es suficiente). Cuando falla el del soplador, no "
            "hay flujo de aire en la cabina aunque el A/C este encendido; cuando falla el del frente, el motor "
            "se sobrecalienta en trafico y el A/C deja de enfriar a baja velocidad."
        ),
        "faq": [
            ("¿Como se que mi motor de ventilador esta fallando?",
             "Soplador interior: no sale aire de las rejillas, ruido de chillido o tableteo, olor a quemado. "
             "Motoventilador frontal: motor sobrecalentando en trafico, A/C que enfria poco a baja velocidad, "
             "ventilador no enciende cuando deberia (audible al apagar el motor con A/C encendido)."),
            ("¿Trae la jaula del ventilador?",
             "Algunos kits incluyen el motor con la jaula montada, otros solo el motor. Confirma con el numero "
             "de parte exacto antes de comprar."),
            ("¿Sirve para BMW de cualquier anio?",
             "No. Cada modelo y generacion tiene su motor de ventilador especifico. Verifica con tu numero de "
             "VIN antes de comprar."),
        ],
    },
    "valvula_disa": {
        "rubro": "valvula DISA (control de admision variable)",
        "shopify_type": "Motor",
        "p1": (
            "Valvula DISA (Differential Air Intake System Actuator) del sistema de admision variable BMW. Su "
            "funcion es modificar la geometria del colector de admision en funcion del regimen del motor: a bajas "
            "RPM cierra una compuerta interna alargando el camino del aire, lo que mejora el torque a bajas; a "
            "altas RPM la abre, acortando el camino y favoreciendo el flujo a alta potencia. Es pieza tipica de "
            "los motores BMW M52, M54 y M56. Su falla provoca perdida de torque a bajas RPM, codigos de error "
            "(P1004, P1006), o ruidos extranos del colector. Es una de las primeras causas a revisar cuando un "
            "BMW de seis cilindros pierde potencia abajo y la solucion frecuentemente es reemplazar la valvula "
            "completa porque el actuador interno es rotativo y se desgasta con los anos."
        ),
        "faq": [
            ("¿Que es DISA y por que mi BMW la necesita?",
             "DISA es el sistema de admision variable que cambia la longitud del conducto de aire segun el "
             "regimen del motor para optimizar torque y potencia. Solo aplica a motores BMW M52, M54 y M56."),
            ("¿Sintomas de DISA dañada?",
             "Perdida de torque a bajas RPM (ralenti, primera/segunda marcha), codigos P1004 / P1006, ruido "
             "extraño del colector de admision, o tableteo metalico. En algunos casos la pieza se desarma "
             "internamente y suelta plastico al motor — caso critico que requiere atencion inmediata."),
            ("¿Vale la pena reparar la DISA o es mejor reemplazar?",
             "Hay kits de reparacion del actuador DISA, pero nuestra recomendacion es reemplazo completo. El "
             "ahorro del kit es marginal y el trabajo de instalacion es el mismo."),
        ],
    },
    "valvula_bolsa": {
        "rubro": "valvula de la bolsa de aire (suspension neumatica)",
        "shopify_type": "Suspensión",  # esto es realmente suspension, no clima
        "p1": (
            "Valvula de control de la bolsa de aire del sistema de suspension neumatica. Estos vehiculos (Audi "
            "Q7, Volkswagen Touareg, Porsche Cayenne, BMW X5) usan amortiguadores con resortes de aire en lugar "
            "de resortes helicoidales tradicionales, y un compresor central inyecta aire al sistema para mantener "
            "la altura del vehiculo. La valvula regula el flujo de aire entre el compresor y cada bolsa. Su "
            "falla provoca que el vehiculo se incline lateralmente al estacionarse, baje de altura "
            "progresivamente, o que el compresor trabaje constantemente intentando reponer presion."
        ),
        "faq": [
            ("¿Mi Q7/Touareg/Cayenne se baja al estacionarse, es normal?",
             "Es normal una pequeña baja al apagar el motor (algunos centimetros). Si baja de manera notable o "
             "se inclina hacia un lado, puede ser fuga en una valvula o bolsa de aire."),
            ("¿La valvula es la causa o es la bolsa?",
             "Para diagnosticar correctamente, un taller con scanner de presion neumatica debe revisar el sistema. "
             "La valvula y la bolsa pueden fallar por separado y los sintomas pueden parecerse."),
            ("¿Trae el o-ring de sello?",
             "Algunas vienen con sellos nuevos, otras no. Confirma con el listing antes de instalar — el o-ring "
             "se reemplaza siempre que se desmonta la valvula."),
        ],
    },
    "valvula_expansion": {
        "rubro": "valvula de expansion del aire acondicionado",
        "shopify_type": "Sistema de Aire Acondicionado",
        "p1": (
            "Valvula de expansion del sistema de aire acondicionado. Es el componente que regula el flujo de "
            "refrigerante liquido hacia el evaporador, generando el cambio de presion que provoca el cambio de "
            "estado liquido-gas (de ahi 'expansion') y el efecto refrigerante. Funciona como dosificador "
            "termostatico: ajusta la apertura segun la temperatura del refrigerante a la salida del evaporador. "
            "Es una pieza pequeña pero critica: si se obstruye o atasca, el A/C deja de enfriar; si esta abierta "
            "demas, el evaporador se congela. Es practica estandar reemplazarla cuando se cambia el compresor "
            "o se hace una reparacion mayor del circuito."
        ),
        "faq": [
            ("¿Como se que la valvula de expansion esta fallando?",
             "El A/C deja de enfriar de un momento a otro, o enfria intermitentemente, o el evaporador se "
             "congela bloqueando el flujo de aire. Diagnostico definitivo requiere medir presiones del sistema."),
            ("¿La cambio sola o con el compresor?",
             "Si el compresor fallo por contaminacion del sistema, cambia la valvula de expansion al mismo tiempo. "
             "El costo marginal es bajo y previene que las particulas residuales atasquen la valvula nueva."),
        ],
    },
    "filtro_cabina": {
        "rubro": "filtro de cabina (filtro de polen)",
        "shopify_type": "Filtros",
        "p1": (
            "Filtro de cabina (tambien llamado filtro de polen, antiacaros o filtro de habitaculo). Su funcion "
            "es atrapar polen, polvo, particulas suspendidas, esporas y, en filtros de carbon activado, olores y "
            "gases del trafico antes de que entren al sistema de climatizacion y a la cabina del vehiculo. Se "
            "ubica detras del compartimento de los pedales o detras de la guantera segun el modelo. Es pieza "
            "de mantenimiento periodico: se reemplaza cada 15,000 a 20,000 km o una vez al ano. Un filtro "
            "saturado reduce el flujo de aire del A/C y la calefaccion, aumenta el consumo electrico del soplador "
            "y deja pasar olores y particulas a la cabina."
        ),
        "faq": [
            ("¿Cada cuanto se cambia el filtro de cabina?",
             "Cada 15,000 a 20,000 km o una vez al ano, lo que ocurra primero. En zonas urbanas con mucho trafico "
             "o en epoca de polen, considerar cambiarlo antes."),
            ("¿Que diferencia hay entre filtro normal y de carbon activado?",
             "El de carbon activado, ademas de filtrar particulas, atrapa olores y gases (CO, NOx, ozono). Es "
             "recomendado en zonas urbanas con mucho trafico. El listing indica si el filtro es de carbon activado."),
            ("¿Yo lo puedo cambiar o necesito taller?",
             "En la mayoria de los modelos europeos el cambio toma 5 a 15 minutos sin herramientas especiales — "
             "se accede desde la guantera o desde el compartimento de pedales. Hay videos de YouTube por modelo."),
        ],
    },
    "tubo_agua": {
        "rubro": "tubo de agua del sistema de calefaccion / refrigeracion",
        "shopify_type": "Motor",
        "p1": (
            "Tubo de agua del sistema de calefaccion y refrigeracion del motor. Estos tubos rigidos de aluminio "
            "o plastico reforzado conducen el liquido refrigerante entre componentes del circuito termico — "
            "especialmente entre el motor, el calefactor de cabina y el deposito de expansion. A diferencia de "
            "las mangueras de caucho, los tubos rigidos suelen estar integrados con conexiones en T o codos "
            "complejos para llegar a zonas confinadas del compartimento del motor. Una falla tipica es la "
            "fuga por la junta o la rotura del plastico por edad y golpes termicos en motores BMW de seis "
            "cilindros (motores N51-N55, M52, M54)."
        ),
        "faq": [
            ("¿Como se que mi tubo de agua esta dañado?",
             "Sintomas: perdida progresiva de refrigerante, manchas blanquecinas (cristalizacion de "
             "anticongelante seco) sobre el tubo, calefaccion intermitente o que tarda en calentar."),
            ("¿Es comun cambiarlo solo o con el termostato?",
             "Si el motor tiene varios anios, considera reemplazar termostato y bomba de agua al mismo tiempo. "
             "Es trabajo similar y los componentes envejecen juntos."),
            ("¿Trae los o-rings de sello?",
             "Algunos vienen con o-rings nuevos integrados, otros no. Confirma con el listing — los o-rings se "
             "reemplazan siempre que se desmonta el tubo."),
        ],
    },
    "servo_flap": {
        "rubro": "servo / actuador del flap de direccion de aire",
        "shopify_type": "Sistema de Aire Acondicionado",
        "p1": (
            "Servo motor (actuador) del flap de direccion del aire de la climatizacion. Su funcion es mover las "
            "compuertas internas de la caja HVAC para dirigir el flujo de aire hacia las salidas correspondientes "
            "(parabrisas, panel central, piso, recirculacion interior/exterior, mezcla calor-frio). Cuando falla "
            "uno de estos servos, el aire sale por una salida fija y no responde al boton de seleccion del tablero. "
            "Sintoma comun en BMW y Mercedes con sistema climatronic: aire que solo sale por el parabrisas, o "
            "calefaccion que no se mezcla aunque el control diga 22 °C."
        ),
        "faq": [
            ("¿Sintomas de un servo flap dañado?",
             "El aire sale solo por una salida sin importar lo que selecciones, hace clic-clic-clic al cambiar "
             "el control, o no cambia entre frio y caliente."),
            ("¿Cual servo es el dañado?",
             "Hay varios servos en cada vehiculo (uno por cada flap independiente). Un scanner OBD-II especifico "
             "(INPA para BMW, XENTRY para Mercedes) puede identificar exactamente cual falla."),
            ("¿Es facil de reemplazar?",
             "Depende de su ubicacion. Algunos estan accesibles bajo el tablero; otros requieren desmontar la "
             "consola central o el tablero completo. Considera el costo de mano de obra antes de comprar la pieza."),
        ],
    },
    "sensor_clima": {
        "rubro": "sensor de temperatura del sistema de climatizacion",
        "shopify_type": "Sistema de Aire Acondicionado",
        "p1": (
            "Sensor de temperatura del sistema de climatizacion. Mide la temperatura del aire en algun punto del "
            "circuito (cabina, conducto de impulsion, evaporador, exterior) y envia la lectura a la unidad de "
            "control del climatronic, que ajusta automaticamente la velocidad del soplador, la mezcla de "
            "calor/frio y la activacion del compresor. Es una pieza pequeña pero critica para que la "
            "climatizacion automatica funcione correctamente. Una falla genera lecturas incorrectas y el "
            "sistema regula mal la temperatura solicitada."
        ),
        "faq": [
            ("¿Sintomas de sensor dañado?",
             "El A/C enfria o calienta de mas, no responde al ajuste del termostato, o el ventilador funciona "
             "a velocidad maxima sin razon. Diagnostico definitivo con scanner."),
            ("¿Donde esta ubicado?",
             "Depende del modelo. Comunmente: en el conducto del evaporador, en la rejilla del tablero (sensor "
             "interior), o detras del espejo retrovisor (sensor exterior). El listing especifica la posicion."),
        ],
    },
    "switch_presion": {
        "rubro": "switch de presion del aire acondicionado (presostato)",
        "shopify_type": "Sistema de Aire Acondicionado",
        "p1": (
            "Switch de presion (presostato) del sistema de aire acondicionado. Mide la presion del refrigerante "
            "en el lado de alta del circuito y envia la senal a la unidad de control del climatronic, que activa "
            "o desactiva el compresor y el ventilador del frente segun corresponda. Tambien actua como "
            "proteccion del compresor: si la presion es muy baja (carga insuficiente de refrigerante) o muy alta "
            "(condensador obstruido o sobrecarga), apaga el compresor para evitar dano interno. Sintomas de "
            "falla: A/C que no enciende aunque el sistema este cargado, o que enciende y apaga ciclicamente."
        ),
        "faq": [
            ("¿Sintomas de switch de presion dañado?",
             "A/C que no activa aunque tengas refrigerante cargado, o que cicla muy rapido (compresor que "
             "enciende y apaga cada pocos segundos). Diagnostico definitivo con manometros del A/C."),
            ("¿Se puede reemplazar sin descargar el sistema?",
             "Algunos switches tienen valvula Schrader interna que permite cambiarlos sin descargar el "
             "refrigerante. Otros requieren descarga previa. Consulta el procedimiento de tu modelo especifico."),
        ],
    },
    "calefactor": {
        "rubro": "calefactor / radiador de calefaccion de cabina",
        "shopify_type": "Sistema de Aire Acondicionado",
        "p1": (
            "Radiador de calefaccion de cabina (heater core). Es un pequeño intercambiador de calor instalado "
            "dentro de la caja HVAC bajo el tablero, donde el liquido refrigerante caliente del motor cede su "
            "calor al aire que entra a la cabina, proporcionando la calefaccion. Esta fabricado en aluminio o "
            "cobre con aletas finas. Falla tipica: fuga de refrigerante dentro de la cabina (huele dulce, deja "
            "humedad en la alfombra del pasajero) o falta de calefaccion aunque el motor este caliente. Su "
            "reemplazo requiere desmontar buena parte del tablero, similar al evaporador."
        ),
        "faq": [
            ("¿Como se que mi heater core esta dañado?",
             "Sintomas: olor dulce de anticongelante en la cabina, humedad bajo la alfombra del pasajero, "
             "vapor saliendo de las salidas de aire al encender la calefaccion, o falta de calefaccion."),
            ("¿Es trabajo largo?",
             "Si — entre 6 y 10 horas de mano de obra. Considera el presupuesto completo antes de comprar la "
             "pieza."),
        ],
    },
    "otro": {
        "rubro": "componente del sistema de climatizacion / refrigeracion",
        "shopify_type": "Sistema de Aire Acondicionado",
        "p1": (
            "Componente del sistema de climatizacion del vehiculo. Refaccion para vehiculos europeos — verifica "
            "el titulo y las especificaciones del listing para identificar exactamente la funcion de la pieza "
            "dentro del sistema (compresor, condensador, evaporador, valvulas, sensores, mangueras o "
            "componentes electronicos). Si tienes dudas sobre la funcion exacta de la pieza o como se monta, "
            "envianos tu numero de VIN y un asesor te confirma compatibilidad y procedimiento de instalacion."
        ),
        "faq": [
            ("¿Como confirmo que es la pieza correcta para mi sistema?",
             "Envianos tu numero de VIN y, si tienes, el numero de parte de la pieza original que estas "
             "reemplazando. Validamos contra el catalogo del fabricante."),
        ],
    },
}


def detectar_tipo(titulo: str) -> str:
    t = titulo.lower()
    if "manguera" in t and ("radiador" in t or "anticongelante" in t or "refrigerante" in t or "agua" in t):
        return "manguera_radiador"
    if ("manguera" in t or "codo" in t or "bota" in t) and "aceleracion" in t:
        return "codo_aceleracion"
    if "compresor" in t and "lincoln" in t:
        return "compresor"
    if "compresor" in t:
        return "compresor"
    if "condensador" in t:
        return "condensador"
    if "evaporador" in t:
        return "evaporador"
    if "resistencia" in t or "herizo" in t or "erizo" in t:
        return "resistor"
    if ("motoventilador" in t or "motor soplador" in t or "motor ventilador" in t or "ventilador" in t):
        return "ventilador"
    if "valvula" in t and "disa" in t:
        return "valvula_disa"
    if "valvula" in t and "bolsa" in t:
        return "valvula_bolsa"
    if "valvula" in t and "expansion" in t:
        return "valvula_expansion"
    if "filtro" in t and ("polen" in t or "cabina" in t):
        return "filtro_cabina"
    if "tubo" in t and ("agua" in t or "calefacc" in t):
        return "tubo_agua"
    if "servo" in t or ("motor" in t and "flap" in t):
        return "servo_flap"
    if "sensor" in t and ("temp" in t or "climat" in t):
        return "sensor_clima"
    if "switch" in t or "presostato" in t:
        return "switch_presion"
    if "calefactor" in t or "radiador" in t and "calefaccion" in t:
        return "calefactor"
    if "manguera" in t:
        return "manguera_radiador"  # fallback para mangueras genericas
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

    # P1 desde plantilla
    p1 = plantilla["p1"]

    # P2 — aplicacion
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

    # P3 — referencias
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

    # P4 — composicion
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
                "evitando diferencias de desgaste entre el lado ya cambiado y el opuesto."
            )
        elif es_kit_local:
            p4 = (
                "Se entrega como kit completo en una sola caja con todos los componentes y la tornilleria de "
                "fijacion correspondiente. Reduce tiempos de inventario en taller y asegura que todas las piezas "
                "son compatibles entre si."
            )
        else:
            p4 = (
                "Se vende como pieza individual nueva, en empaque del fabricante. Producto no reciclado ni "
                "remanufacturado. Si tu reparacion requiere reemplazar la pieza tambien en el lado opuesto o "
                "en componentes relacionados (sellos, abrazaderas, deshidratador), consulta con nuestro asesor."
            )

    # P5 — marca y garantia
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

    # caract_compatibilidad
    caract_compat = caract_compat_pre or (
        f"Compatible con los modelos {', '.join(marcas_veh) or 'mencionados en el titulo'}. "
        "Confirma compatibilidad exacta con tu numero de VIN antes de comprar."
    )

    # FAQs
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

    # Secciones
    es_par = bool(re.search(r"\bpar\b", titulo, re.IGNORECASE))
    es_kit = bool(re.search(r"\b(kit|juego|set)\b", titulo, re.IGNORECASE)) or bool(incluye)
    antes = antes_comprar(numero_parte, oem)
    envio = envio_text(es_kit, es_par)

    # Shopify
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

    # revision_humana
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
    if tipo == "valvula_bolsa":
        revision.append(
            "[ANALIZAR] Producto es de suspension neumatica, no de clima. Considerar mover a "
            "refacciones_suspension."
        )
    if tipo in ("codo_aceleracion", "valvula_disa"):
        revision.append(
            "[ANALIZAR] Producto es del sistema de admision, no de climatizacion. Considerar mover a "
            "refacciones_motor."
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
