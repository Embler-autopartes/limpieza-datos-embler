"""
Build script para refacciones_suspension (4,385 filas).

Tipos: amortiguador, amortiguador_aire, bolsa_aire, resorte, brazo, horquilla, rotula, buje,
barra_estabilizadora, bieleta, cubo, mangueta, cremallera, terminal_direccion, bomba_direccion,
soporte_amortiguador, columna_direccion, otro.
"""

import json
import os
import re
import unicodedata
from collections import Counter

HOJA = os.environ.get("EMBLER_HOJA", "ml_con_match")
BATCH_PATH = f"new-output_v2/{HOJA}/refacciones_suspension_batch.json"
OUTPUT_PATH = f"new-output_v2/{HOJA}/refacciones_suspension_batch_result.json"


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
    text = re.sub(r"[^a-z0-9]+", "-", text.lower())
    return re.sub(r"-+", "-", text).strip("-")[:100]


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
    if any(b in raw_low for b in ("bilstein", "sachs", "monroe", "kyb", "boge")):
        return (f"Marca {marca_norm or marca_raw}, proveedor OEM aleman/japones de amortiguadores y suspension. "
                "Suministra a la fabrica para BMW, Mercedes, Audi, VW.")
    if "lemforder" in raw_low or "trw" in raw_low:
        return (f"Marca {marca_norm or marca_raw}, proveedor OEM europeo de componentes de chasis y direccion. "
                "Calidad equivalente al equipo original.")
    if not marca_norm:
        return f"Marca de refaccion: {marca_raw or 'no especificada'}."
    return f"Marca {marca_norm}, fabricante de refacciones para vehiculos europeos."


TIPO_DEFINICIONES = {
    "amortiguador": {
        "rubro": "amortiguador de suspension",
        "shopify_type": "Suspensión",
        "p1": (
            "Amortiguador de suspension del vehiculo. Es la unidad hidraulica o hidraulico-neumatica que "
            "controla el movimiento del resorte y disipa la energia de las irregularidades del camino, "
            "manteniendo el contacto del neumatico con el suelo y evitando el rebote excesivo del chasis. "
            "Los amortiguadores modernos europeos pueden ser convencionales (gas mono-tubo o bi-tubo), "
            "adaptativos (con valvulas controladas electronicamente que ajustan la rigidez en tiempo real "
            "— sistemas EDC en BMW, ADS en Mercedes, magnetic ride en Audi), o de aire (suspension "
            "neumatica). Pieza de desgaste con vida util tipica entre 80,000 y 150,000 km segun el "
            "estilo de manejo y el estado del camino."
        ),
        "faq": [
            ("¿Sintomas de amortiguador desgastado?",
             "Rebote excesivo despues de un bache, vehiculo que se 'flota' al frenar, vibracion en la "
             "direccion al pasar irregularidades, fugas de aceite visibles en el cuerpo del amortiguador."),
            ("¿Se cambia uno o el par del eje?",
             "Siempre el par del mismo eje. Cambiar solo uno descompensa la respuesta de la suspension y "
             "provoca desgaste asimetrico de los neumaticos."),
            ("¿Es del lado izquierdo o derecho?",
             "En modelos premium con suspension adaptativa, los amortiguadores L/R pueden ser distintos. "
             "Verifica el listing y confirma con tu numero de VIN."),
            ("¿Necesito alineacion despues?",
             "Si — siempre que se cambian componentes de suspension recomendamos verificar y ajustar la "
             "alineacion."),
        ],
    },
    "amortiguador_aire": {
        "rubro": "amortiguador de aire / suspension neumatica",
        "shopify_type": "Suspensión",
        "p1": (
            "Amortiguador de aire (air strut, air suspension shock) de suspension neumatica. En vehiculos "
            "como BMW X5/X6/X7, Mercedes ML/GL/GLE/GLS/Clase S, Audi Q7, VW Touareg, Porsche Cayenne y "
            "Range Rover, los resortes helicoidales tradicionales se reemplazan por bolsas de aire "
            "presurizado controladas por la ECU de la suspension, lo que permite ajustar la altura del "
            "vehiculo segun condiciones de manejo. El amortiguador integra la bolsa de aire con el "
            "amortiguador hidraulico convencional. Es pieza de mantenimiento costoso pero critico — una "
            "fuga obliga al sistema a trabajar continuamente y descarga la bateria."
        ),
        "faq": [
            ("¿Sintomas de amortiguador de aire dañado?",
             "El vehiculo se baja de un lado o atras al estacionarse, compresor que trabaja "
             "constantemente, mensaje de error 'air suspension malfunction', altura desigual entre lados."),
            ("¿Cambio uno o el par?",
             "Siempre el par del mismo eje. Las diferencias de presion entre lados generan inclinacion."),
            ("¿Necesita codificacion?",
             "Algunos modelos modernos requieren calibracion del sistema neumatico despues del reemplazo. "
             "Confirma con tu taller con scanner especializado."),
        ],
    },
    "bolsa_aire": {
        "rubro": "bolsa de aire / fuelle de suspension neumatica",
        "shopify_type": "Suspensión",
        "p1": (
            "Bolsa de aire (air bag, air spring) de la suspension neumatica. Reemplaza el resorte "
            "helicoidal tradicional con una camara de caucho reforzado llena de aire presurizado, "
            "controlada por el compresor central y las valvulas del sistema neumatico. Aplica a BMW X5/"
            "X7, Mercedes Clase S/ML/GL, Audi Q7/A8, VW Touareg, Porsche Cayenne, Range Rover. Falla "
            "tipica: fuga por degradacion del caucho con los anos (vehiculo que se baja al estacionarse), "
            "rotura por fatiga o impacto, fuga por la junta superior o inferior."
        ),
        "faq": [
            ("¿Sintomas de bolsa de aire dañada?",
             "El vehiculo se baja del lado afectado al estacionarse, ruido de aire al activar el sistema, "
             "compresor que trabaja constantemente intentando compensar."),
            ("¿Cambio bolsa o todo el amortiguador?",
             "Si solo la bolsa fallo y el amortiguador esta bien, cambia solo la bolsa. Si ambos tienen "
             "anos, considera el conjunto completo."),
            ("¿Vienen los anillos de sello?",
             "Algunas vienen con sellos integrados, otras los anillos se compran por separado. Verifica "
             "con el listing."),
        ],
    },
    "resorte": {
        "rubro": "resorte / espiral de suspension",
        "shopify_type": "Suspensión",
        "p1": (
            "Resorte (espiral) de suspension. Es el muelle helicoidal de acero templado que soporta el "
            "peso del vehiculo y permite el movimiento vertical de la rueda sobre las irregularidades del "
            "camino. La rigidez (constante de resorte) define el comportamiento dinamico — los vehiculos "
            "deportivos M Sport, AMG, S-Line tienen resortes mas rigidos y mas cortos que los estandar "
            "para reducir el balanceo. Pieza tipica de reemplazo cuando el resorte se rompe (frecuente en "
            "climas con sal de carretera por corrosion) o cuando el vehiculo se asienta de un lado."
        ),
        "faq": [
            ("¿Sintomas de resorte roto?",
             "Vehiculo inclinado de un lado, ruido metalico al pasar baches, altura desigual entre los "
             "dos lados del eje, contacto del rebote con el chasis."),
            ("¿Cambio el par?",
             "Siempre el par del mismo eje. Resortes de distintos lotes tienen rigidez ligeramente "
             "distinta y descompensan."),
            ("¿Es estandar o paquete deportivo?",
             "Verifica con tu paquete (M Sport, AMG, S-Line). Los resortes son distintos — los deportivos "
             "son mas cortos y rigidos."),
        ],
    },
    "brazo": {
        "rubro": "brazo de suspension (control arm)",
        "shopify_type": "Suspensión",
        "p1": (
            "Brazo de suspension (control arm, wishbone) del vehiculo. Es el elemento estructural que "
            "conecta la mangueta de la rueda con el chasis del vehiculo, permitiendo el movimiento "
            "vertical de la suspension y manteniendo la geometria de la direccion. Los brazos modernos "
            "europeos suelen ser de aluminio fundido (mas ligeros) o acero estampado. Tienen "
            "rotulas integradas en uno o ambos extremos y bujes de caucho-metal en el lado del chasis. "
            "Pieza tipica de reemplazo cuando los bujes o las rotulas se desgastan, generando golpes al "
            "pasar baches y direccion vaga."
        ),
        "faq": [
            ("¿Sintomas de brazo desgastado?",
             "Golpes (clunks) al pasar baches, vibracion en la direccion, desgaste asimetrico de los "
             "neumaticos, direccion vaga o que tira hacia un lado."),
            ("¿Es del lado izquierdo o derecho?",
             "Confirma con el listing — cada lado tiene codigo de parte distinto."),
            ("¿Es delantero o trasero?",
             "Verifica el listing. Los brazos delanteros tipicamente son superiores e inferiores; los "
             "traseros pueden ser brazo lateral, brazo longitudinal, o brazo trasero."),
            ("¿Trae los bujes y rotulas?",
             "Generalmente si — los brazos se venden con bujes y rotulas integradas. Confirma con el "
             "listing."),
        ],
    },
    "horquilla": {
        "rubro": "horquilla / bandeja de suspension",
        "shopify_type": "Suspensión",
        "p1": (
            "Horquilla (bandeja, tijera) de suspension. Termino regional para el brazo de suspension "
            "estructurado en forma de Y o de A que conecta la rueda al chasis. La horquilla cumple la "
            "misma funcion que el brazo de control: mantener la posicion de la rueda y permitir el "
            "movimiento vertical de la suspension. En la mayoria de vehiculos europeos modernos, la "
            "suspension delantera tiene una horquilla inferior (lower control arm); en algunos modelos "
            "hay tambien una superior."
        ),
        "faq": [
            ("¿'Horquilla' y 'brazo de suspension' son lo mismo?",
             "Si — son terminos regionales para la misma pieza. 'Horquilla' o 'bandeja' es comun en "
             "Mexico y Sudamerica; 'control arm' o 'wishbone' en ingles."),
            ("¿Trae los bujes?",
             "Generalmente si. Verifica el listing por si el modelo aplica a una horquilla con bujes "
             "reemplazables independientes."),
        ],
    },
    "rotula": {
        "rubro": "rotula de suspension / direccion",
        "shopify_type": "Suspensión",
        "p1": (
            "Rotula (ball joint) de suspension o direccion. Es la junta esferica que permite el movimiento "
            "rotacional de la rueda al direccionar y al subir/bajar con la suspension. Esta compuesta por "
            "una bola metalica con vastago, capturada en una camara con sellos antiacaros y polvera "
            "exterior. Pieza tipica de desgaste — cuando el sello falla, entra agua y polvo, lo que "
            "acelera el desgaste de la bola y aparece juego en la suspension. Sintomas: golpes al pasar "
            "baches, direccion vaga, desgaste asimetrico de los neumaticos."
        ),
        "faq": [
            ("¿Sintomas de rotula desgastada?",
             "Golpes al pasar baches, vibracion en la direccion, desgaste irregular de los neumaticos, "
             "vehiculo que tira hacia un lado al frenar."),
            ("¿Es de suspension o de direccion?",
             "Confirma con el listing. Las rotulas de suspension estan en el extremo de los brazos; las "
             "de direccion en los terminales (tie rod ends)."),
            ("¿Puedo seguir manejando con rotula desgastada?",
             "Es riesgoso. Una rotula que se rompa completamente desconecta la rueda y puede provocar un "
             "accidente. Reemplazar cuanto antes."),
        ],
    },
    "buje": {
        "rubro": "buje / casquillo de suspension",
        "shopify_type": "Suspensión",
        "p1": (
            "Buje (bushing, casquillo) de suspension. Es la pieza de caucho-metal que aisla la conexion "
            "entre los componentes metalicos de la suspension (brazos, barras estabilizadoras, soportes), "
            "absorbiendo vibraciones y permitiendo movimientos limitados sin transferir golpes al chasis. "
            "Esta compuesto por un alma metalica interior y un cuerpo de caucho vulcanizado con o sin "
            "casquillo metalico exterior. Pieza de desgaste tipica — el caucho se cuartea con los anos y "
            "aparecen juegos que se manifiestan como golpes al pasar baches y desalineacion progresiva."
        ),
        "faq": [
            ("¿Sintomas de buje desgastado?",
             "Golpes (clunks) al pasar baches especialmente al frenar o acelerar, vibracion en la "
             "carroceria, desalineacion del eje (vehiculo tira hacia un lado)."),
            ("¿Donde esta el buje?",
             "Hay multiples bujes en cada eje: bujes del brazo de control, bujes de la barra "
             "estabilizadora, bujes del puente trasero. Verifica con el titulo y la posicion."),
            ("¿Vale la pena cambiarlo solo o todo el brazo?",
             "Si la rotula y el resto del brazo estan bien, el buje solo. Si son varios componentes con "
             "desgaste, el brazo completo."),
        ],
    },
    "barra_estabilizadora": {
        "rubro": "barra estabilizadora",
        "shopify_type": "Suspensión",
        "p1": (
            "Barra estabilizadora (anti-roll bar, sway bar) de suspension. Es la barra de torsion "
            "transversal que conecta los dos lados de un eje y reduce el balanceo lateral del vehiculo en "
            "curvas. Trabaja torsionando elasticamente — cuando un lado del vehiculo sube en una curva, "
            "transfiere fuerza al lado opuesto. Pieza estructural raramente se daña; lo mas comun es que "
            "fallen los bujes que la sujetan al chasis o las bieletas que la conectan al brazo de "
            "suspension."
        ),
        "faq": [
            ("¿Cuando se cambia la barra estabilizadora?",
             "Es muy raro que la barra misma se rompa. Lo comun es cambiar los bujes o las bieletas. "
             "Si la barra esta torcida por un impacto fuerte, si se reemplaza."),
        ],
    },
    "bieleta": {
        "rubro": "bieleta / tirante de la barra estabilizadora",
        "shopify_type": "Suspensión",
        "p1": (
            "Bieleta (tirante, sway bar link) de la barra estabilizadora. Es el tirante corto con dos "
            "rotulas en sus extremos que conecta cada lado del brazo de suspension con la barra "
            "estabilizadora, transmitiendo el movimiento entre ambos. Pieza tipica de desgaste — las "
            "rotulas se aflojan con los anos y aparece un golpeteo distintivo al pasar baches a baja "
            "velocidad. Es uno de los sintomas mas comunes en BMW y Mercedes con kilometrajes altos."
        ),
        "faq": [
            ("¿Sintomas de bieleta desgastada?",
             "Golpeteo metalico al pasar baches a baja velocidad (especialmente notorio en topes), ruido "
             "de tableteo en empedrados, sensacion de juego en la direccion."),
            ("¿Cambio el par?",
             "Si — siempre el par del mismo eje. Las bieletas envejecen al mismo tiempo."),
            ("¿Es facil de instalar?",
             "Generalmente accesible — se desmonta de extremo a extremo. Trabajo de 30-60 minutos en "
             "taller. Recomendamos verificar alineacion despues."),
        ],
    },
    "cubo": {
        "rubro": "cubo de rueda (con balero)",
        "shopify_type": "Suspensión",
        "p1": (
            "Cubo de rueda (wheel hub assembly) con balero integrado. Es el conjunto giratorio que "
            "soporta la rueda en su eje, conectando el rotor del freno y la rueda con la mangueta. "
            "Integra el balero (rodamiento) sellado de fabrica que permite el giro libre con minima "
            "friccion. En vehiculos con ABS, integra tambien la rueda fonica del sensor ABS. Pieza de "
            "desgaste tipica con vida util entre 100,000 y 250,000 km segun condiciones."
        ),
        "faq": [
            ("¿Sintomas de cubo dañado?",
             "Zumbido o moledora que aumenta con la velocidad (caracteristico cuando el balero falla), "
             "vibracion en la direccion, juego radial al mover la rueda con la mano, sensor ABS "
             "intermitente."),
            ("¿Trae el balero integrado?",
             "Si — los cubos modernos vienen con balero sellado de fabrica integrado. No se desarma."),
        ],
    },
    "mangueta": {
        "rubro": "mangueta de la rueda",
        "shopify_type": "Suspensión",
        "p1": (
            "Mangueta (steering knuckle, spindle) de la rueda. Es la pieza estructural que conecta el "
            "cubo de la rueda con los componentes de la suspension y la direccion (brazos de control, "
            "amortiguador, bieleta de direccion). En vehiculos modernos europeos esta fabricada en "
            "aluminio fundido (mas ligera) o acero forjado. Pieza estructural — se reemplaza solo si se "
            "daña por accidente o impacto severo."
        ),
        "faq": [
            ("¿Cuando se reemplaza la mangueta?",
             "Solo despues de impactos fuertes o accidentes. Es pieza estructural muy duradera."),
        ],
    },
    "cremallera": {
        "rubro": "cremallera de direccion",
        "shopify_type": "Dirección",
        "p1": (
            "Cremallera de direccion (steering rack). Es el componente principal del sistema de "
            "direccion: convierte el giro del volante en movimiento lateral de las ruedas a traves de un "
            "engranaje pinion-cremallera. Las cremalleras modernas son hidraulicas (asistidas por bomba "
            "de direccion) o electricas (con motor de asistencia integrado). Pieza compleja que falla "
            "tipicamente por fugas en los sellos del piston (cremalleras hidraulicas) o falla del motor "
            "asistente (cremalleras electricas)."
        ),
        "faq": [
            ("¿Sintomas de cremallera dañada?",
             "Direccion dura o sin asistencia, fugas de liquido (cremalleras hidraulicas), ruido al "
             "girar el volante, juego excesivo en el volante, mensaje de error de direccion."),
            ("¿Es hidraulica o electrica?",
             "Vehiculos europeos modernos (post-2010) suelen tener direccion electrica (EPS). Modelos "
             "anteriores son hidraulicas. Confirma con el listing — no son intercambiables."),
        ],
    },
    "terminal_direccion": {
        "rubro": "terminal de direccion (tie rod end)",
        "shopify_type": "Dirección",
        "p1": (
            "Terminal de direccion (tie rod end) del sistema de direccion. Es la junta esferica con "
            "rosca que conecta la cremallera de direccion con la mangueta de la rueda, transmitiendo el "
            "movimiento lateral de la cremallera al giro de la rueda. Pieza tipica de desgaste — la "
            "rotula interna se afloja con los anos y aparece juego en la direccion (volante con holgura "
            "antes de mover las ruedas)."
        ),
        "faq": [
            ("¿Sintomas de terminal desgastado?",
             "Juego excesivo en el volante, vibracion en la direccion, desgaste irregular de los "
             "neumaticos, vehiculo que tira hacia un lado."),
            ("¿Cambio el par?",
             "Conviene cambiar el par del mismo eje. Recomendamos alineacion despues del cambio."),
        ],
    },
    "bomba_direccion": {
        "rubro": "bomba de direccion hidraulica",
        "shopify_type": "Dirección",
        "p1": (
            "Bomba de direccion hidraulica (power steering pump). Genera la presion hidraulica que asiste "
            "el giro del volante, accionada por la banda auxiliar del motor. Pieza tipica de falla por "
            "desgaste interno (perdida de presion = direccion dura) o por contaminacion del liquido (que "
            "daña los sellos internos)."
        ),
        "faq": [
            ("¿Sintomas de bomba dañada?",
             "Direccion dura (sin asistencia), ruido de chillido o gemido al girar el volante, fuga "
             "visible bajo la bomba, nivel del liquido bajo con frecuencia."),
            ("¿Solo para direccion hidraulica?",
             "Si — los vehiculos con direccion electrica (EPS) no tienen bomba hidraulica."),
        ],
    },
    "soporte_amortiguador": {
        "rubro": "soporte / cojinete del amortiguador",
        "shopify_type": "Suspensión",
        "p1": (
            "Soporte de amortiguador (top mount, strut mount). Es el conjunto de fijacion superior del "
            "amortiguador al chasis, integrando un cojinete (en suspension delantera direccional) que "
            "permite el giro al direccionar, y elementos de caucho que aislan vibraciones. Pieza tipica "
            "de desgaste — el caucho se cuartea con los anos y el cojinete genera ruido al direccionar."
        ),
        "faq": [
            ("¿Sintomas de soporte desgastado?",
             "Ruido tipo crujido al direccionar (especialmente en parado o baja velocidad), golpes al "
             "pasar baches, vibracion en el chasis."),
            ("¿Cambio el par?",
             "Si — siempre el par del mismo eje. Cambiar solo uno descompensa la suspension."),
            ("¿Trae el cojinete?",
             "Verifica el listing. Algunos vienen con cojinete integrado, otros se compran por separado."),
        ],
    },
    "columna_direccion": {
        "rubro": "columna de direccion",
        "shopify_type": "Dirección",
        "p1": (
            "Columna de direccion (steering column). Es el eje que conecta el volante con la cremallera "
            "de direccion, atravesando el firewall del vehiculo. Las columnas modernas integran "
            "ajustadores telescopicos, cardan internos para absorber vibraciones, y en algunos modelos "
            "la cerradura del encendido y el sensor de angulo del volante. Pieza estructural raramente "
            "se daña; lo mas comun es falla del cardan (ruido al direccionar) o del mecanismo de ajuste."
        ),
        "faq": [
            ("¿Cuando se reemplaza la columna?",
             "Despues de accidentes severos, falla del cardan interno (ruido caracteristico al "
             "direccionar), o falla del mecanismo de ajuste telescopico."),
        ],
    },
    "tornilleria": {
        "rubro": "tornilleria / accesorios de fijacion",
        "shopify_type": "Suspensión",
        "p1": (
            "Tornilleria, abrazaderas o accesorios de fijacion para componentes de la suspension. "
            "Tipicamente: tornillos especiales del brazo de suspension (TTY torque-to-yield), tuercas de "
            "rotula con cierre, clips de fijacion. Estos tornillos especiales deben reemplazarse al "
            "desmontarse — no se reutilizan."
        ),
        "faq": [
            ("¿Por que reemplazar los tornillos?",
             "Los tornillos TTY se deforman elasticamente al apretarse al torque correcto y pierden "
             "su capacidad de mantener carga si se reutilizan."),
        ],
    },
    "cople": {
        "rubro": "cople de la columna de direccion",
        "shopify_type": "Dirección",
        "p1": (
            "Cople (junta universal, U-joint) de la columna de direccion. Permite la transmision del "
            "movimiento entre la columna y la cremallera con cierto angulo de desalineacion. Pieza tipica "
            "de desgaste — las junturas internas se aflojan con los anos y aparece ruido caracteristico "
            "al direccionar (clic-clic-clic)."
        ),
        "faq": [
            ("¿Sintomas de cople desgastado?",
             "Ruido tipo tableteo o crujido al direccionar (especialmente en parado), juego en la "
             "direccion antes de que las ruedas respondan."),
        ],
    },
    "otro": {
        "rubro": "componente de suspension / direccion",
        "shopify_type": "Suspensión",
        "p1": (
            "Componente del sistema de suspension o direccion del vehiculo. Refaccion para vehiculos "
            "europeos. El listing especifica la pieza exacta y su posicion; si tienes dudas sobre "
            "compatibilidad o instalacion, envianos tu numero de VIN y un asesor te confirma los detalles."
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
    if "amortiguador" in t and ("aire" in t or "neumatic" in t):
        return "amortiguador_aire"
    if "amortiguador" in t and "cofre" not in t and "cajuela" not in t:
        return "amortiguador"
    if "bolsa" in t and ("aire" in t or "suspension" in t):
        return "bolsa_aire"
    if "resorte" in t or "espiral" in t:
        return "resorte"
    if "horquilla" in t or "bandeja" in t or "tijera" in t:
        return "horquilla"
    if "brazo" in t and ("suspension" in t or "delante" in t or "trasero" in t or "recto" in t or "curvo" in t):
        return "brazo"
    if "rotula" in t:
        return "rotula"
    if "buje" in t or "casquillo" in t:
        return "buje"
    if "barra" in t and ("estabilizadora" in t or "estabilizador" in t):
        return "barra_estabilizadora"
    if "bieleta" in t or ("tirante" in t and "estabilizadora" in t):
        return "bieleta"
    if "cubo" in t and "rueda" in t:
        return "cubo"
    if "mangueta" in t:
        return "mangueta"
    if "cremallera" in t:
        return "cremallera"
    if "terminal" in t and "direccion" in t:
        return "terminal_direccion"
    if "bomba" in t and "direccion" in t:
        return "bomba_direccion"
    if "soporte" in t and "amortiguador" in t:
        return "soporte_amortiguador"
    if "columna" in t and "direccion" in t:
        return "columna_direccion"
    if "tornillo" in t and ("susp" in t or "rotula" in t):
        return "tornilleria"
    if "cople" in t and "direccion" in t:
        return "cople"
    return "otro"


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
            "Recomendamos confirmar con el numero de VIN antes de comprar — los componentes de suspension varian "
            "frecuentemente por anio, paquete (M Sport, AMG, S-Line) y opcionales (suspension adaptativa, neumatica)."
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
                "Recomendado para componentes de suspension por seguridad y por la importancia del balance "
                "entre los dos lados del eje — cambiar solo uno descompensa la respuesta de la suspension."
            )
        elif es_kit_local:
            p4 = (
                "Se entrega como kit completo en una sola caja con todos los componentes y la tornilleria de "
                "fijacion correspondiente."
            )
        else:
            p4 = (
                "Se vende como pieza individual nueva, en empaque del fabricante. Producto no reciclado ni "
                "remanufacturado. Para servicio de suspension, recomendamos cambiar tambien la pieza del lado "
                "opuesto del eje al mismo tiempo para mantener el balance — consulta con nuestro asesor."
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
                "de procesar el pedido. Tambien puedes mencionar el paquete (M Sport, AMG, S-Line) y "
                "opcionales como suspension adaptativa o neumatica."
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
            "Confirmar modelos y anios."
        )
    if not np and not oem:
        revision.append("[BUSCAR] Numero de parte o codigo OEM faltantes.")
    if not sku:
        revision.append("[INCLUIR] SKU faltante — asignar antes de publicar.")
    if not marca_norm:
        revision.append("[ANALIZAR] Marca no identificada — confirmar fabricante.")
    if tipo in ("amortiguador", "amortiguador_aire", "brazo", "horquilla", "rotula", "bieleta") and not lado:
        revision.append(
            "[VERIFICAR] Pieza de suspension sin atributo 'Lado' especificado — confirmar L/R/Universal/eje "
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
