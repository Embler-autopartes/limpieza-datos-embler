"""
Build script para refacciones_frenos (1,000 filas).

Tipos detectados por keywords del titulo: balata, disco, caliper, sensor_abs, sensor_balata,
manguera_freno, cilindro, bomba_freno, liquido_freno, cable_freno, booster, tambor,
kit_caliper, kit_tornilleria, otro.
"""

import json
import os
import re
import unicodedata
from collections import Counter

HOJA = os.environ.get("EMBLER_HOJA", "ml_con_match")
BATCH_PATH = f"new-output_v2/{HOJA}/refacciones_frenos_batch.json"
OUTPUT_PATH = f"new-output_v2/{HOJA}/refacciones_frenos_batch_result.json"


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
    if "ate" in raw_low or "textar" in raw_low or "ferodo" in raw_low or "akebono" in raw_low or "brembo" in raw_low or "pagid" in raw_low:
        return (
            f"Marca {marca_norm or marca_raw}, proveedor OEM/OES especialista en sistemas de freno. "
            "Suministra a la fabrica para BMW, Mercedes, Audi, VW y otros vehiculos premium."
        )
    if "trw" in raw_low or "lucas" in raw_low:
        return (
            f"Marca {marca_norm or marca_raw}, proveedor europeo de sistemas de freno y direccion. "
            "Calidad OEM equivalente al equipo original."
        )
    if not marca_norm:
        return f"Marca de refaccion: {marca_raw or 'no especificada'}."
    return f"Marca {marca_norm}, fabricante de refacciones para vehiculos europeos."


# ---------------------------------------------------------------------------
# Templates por tipo
# ---------------------------------------------------------------------------

TIPO_DEFINICIONES = {
    "balata": {
        "rubro": "balatas (pastillas) de freno",
        "shopify_type": "Frenos",
        "p1": (
            "Balatas (pastillas, brake pads) de freno para sistema de freno de disco. Son las pastillas "
            "con material de friccion que se aprietan contra el disco de freno cuando se pisa el pedal, "
            "convirtiendo la energia cinetica del vehiculo en calor que se disipa al ambiente. Son pieza "
            "de desgaste tipica con vida util entre 30,000 y 80,000 km segun el estilo de manejo y el "
            "tipo de balata. Las balatas modernas para vehiculos europeos premium suelen ser semi-metalicas "
            "o ceramicas, con sensor de desgaste integrado en uno de los pares (delantero o trasero). El "
            "desgaste se manifiesta como chillido al frenar, vibracion en el pedal, recorrido del pedal "
            "mayor o luz de servicio del freno encendida."
        ),
        "faq": [
            ("¿Cada cuanto se cambian las balatas?",
             "Entre 30,000 y 80,000 km segun el estilo de manejo (uso urbano vs carretera) y el tipo de "
             "balata. Verifica el sensor de desgaste si tu vehiculo lo trae — la luz de servicio en el "
             "tablero indica que es momento de revisar."),
            ("¿Se cambian eje completo o cuatro a la vez?",
             "Por eje (delantero o trasero) — siempre las dos balatas del mismo eje al mismo tiempo. Se "
             "cambian todas las cuatro solo si todas estan al limite, lo cual no es comun (tipicamente "
             "las delanteras se gastan mas rapido)."),
            ("¿Cambio el sensor de desgaste tambien?",
             "Si el sensor original ya hizo contacto con el disco (luz encendida), debe reemplazarse. Si "
             "se cambia preventivamente sin que haya alarmado, el sensor puede reutilizarse."),
            ("¿Necesito cambiar los discos?",
             "Verifica el grosor de los discos contra el minimo del fabricante. Si estan al limite, "
             "cambialos junto con las balatas para evitar desgaste prematuro de las balatas nuevas."),
        ],
    },
    "disco": {
        "rubro": "disco de freno",
        "shopify_type": "Frenos",
        "p1": (
            "Disco de freno (rotor) para sistema de freno hidraulico. Es la pieza de hierro fundido o "
            "compuesto carbon-ceramico que gira con la rueda y proporciona la superficie contra la que se "
            "aprietan las balatas para detener el vehiculo. Los discos modernos europeos premium pueden "
            "ser ventilados (con canales internos para disipar calor), perforados o ranurados (para "
            "rendimiento mejorado), o de carbon-ceramico (en aplicaciones M, AMG o R deportivas). Es pieza "
            "de desgaste con vida util tipica de 60,000 a 120,000 km segun el estilo de manejo y la "
            "calidad del freno."
        ),
        "faq": [
            ("¿Cuando cambio los discos?",
             "Cuando el grosor cae por debajo del minimo del fabricante (estampado en el costado del "
             "disco), cuando aparecen ranuras profundas, cuando hay vibracion al frenar (disco "
             "alabeado), o cuando el desgaste es desigual."),
            ("¿Se cambian por eje?",
             "Si — siempre los dos discos del mismo eje al mismo tiempo, junto con las balatas. Cambiar "
             "solo uno provoca frenado desbalanceado y desgaste asimetrico."),
            ("¿Que diferencia hay entre disco solido, ventilado y perforado?",
             "Solido: una sola pieza, mas economico, para frenos traseros de vehiculos de calle. Ventilado: "
             "dos placas con canales internos, mejor disipacion termica, estandar para frenos delanteros. "
             "Perforado/ranurado: para rendimiento alto, mejor disipacion de gases y agua, mas caro."),
            ("¿Es ventilado o solido?",
             "Verifica el listing y el grosor original de tu disco. Los delanteros tipicamente son "
             "ventilados; los traseros pueden ser solidos o ventilados segun el modelo."),
        ],
    },
    "caliper": {
        "rubro": "caliper / pinza de freno",
        "shopify_type": "Frenos",
        "p1": (
            "Caliper (pinza, mordaza) de freno. Es el conjunto hidraulico que aloja las balatas y los "
            "pistones que las empujan contra el disco cuando se pisa el pedal. El caliper recibe la "
            "presion hidraulica de la bomba maestra a traves de la manguera de freno, y mediante uno o "
            "varios pistones internos transfiere esa presion a las balatas. Hay dos tipos principales: "
            "caliper flotante (un solo piston en un lado, comun en frenos traseros y vehiculos de calle) "
            "y caliper fijo (multiples pistones en ambos lados, comun en frenos delanteros de alto "
            "rendimiento BMW M, AMG, S-Line). Falla tipica: pistones atascados por oxido, fugas de liquido "
            "por sellos degradados, o caliper colgado por guias engranadas."
        ),
        "faq": [
            ("¿Sintomas de caliper dañado?",
             "El vehiculo tira hacia un lado al frenar (caliper opuesto colgado), una rueda se calienta "
             "mas que la otra (caliper sin retornar), pedal de freno blando o que cae al piso (fuga "
             "interna), chillido constante de un lado."),
            ("¿Se reconstruye o se reemplaza?",
             "Hay kits de reparacion (sellos, guias, polvera) que reconstruyen el caliper si los pistones "
             "y el cuerpo estan en buen estado. Si el cuerpo esta agrietado o muy oxidado, reemplazo "
             "completo."),
            ("¿Es del lado izquierdo o derecho?",
             "Confirma con el listing. Calipers L y R son distintos por la posicion del puerto hidraulico "
             "y el sangrador (bleeder)."),
            ("¿Trae las balatas?",
             "Generalmente no — el caliper se vende sin balatas. Considera comprarlas al mismo tiempo "
             "para hacer el servicio completo."),
        ],
    },
    "kit_caliper": {
        "rubro": "kit de reparacion del caliper",
        "shopify_type": "Frenos",
        "p1": (
            "Kit de reparacion del caliper (caliper repair kit, caliper rebuild kit). Incluye los sellos "
            "interiores del piston, las polveras (boots) que protegen contra polvo y agua, y en algunos "
            "casos las guias deslizantes (slide pins) y sus polveras. Reconstruir un caliper con este kit "
            "es la opcion economica cuando los pistones y el cuerpo del caliper estan en buen estado y "
            "solo los sellos se han degradado por edad o calor. Reduce el costo a una fraccion del "
            "caliper completo."
        ),
        "faq": [
            ("¿Cuando vale la pena reconstruir vs reemplazar?",
             "Reconstruir: cuando los pistones se mueven libremente y el cuerpo no esta agrietado ni muy "
             "oxidado. Reemplazar: cuando hay daños estructurales o pistones atascados por oxidacion "
             "interna severa."),
            ("¿Trae las polveras de los pistones?",
             "Si — el kit incluye las polveras (boots) y los sellos interiores. Algunos tambien las "
             "polveras de las guias deslizantes."),
            ("¿Necesito herramienta especial?",
             "Si — para extraer los pistones se necesita aire comprimido o una herramienta de extraccion. "
             "Recomendamos taller especializado para evitar dañar la guia del piston."),
        ],
    },
    "sensor_abs": {
        "rubro": "sensor ABS (velocidad de rueda)",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Sensor ABS (Anti-lock Braking System) o sensor de velocidad de rueda. Mide la velocidad "
            "rotacional de cada rueda y envia la lectura al modulo ABS, que la usa para detectar el "
            "bloqueo durante un frenado fuerte y modular la presion del freno para mantener la traccion. "
            "Tambien es la fuente de velocidad para los sistemas de control de estabilidad (ESP/DSC) y "
            "control de traccion (ASR/TCS). Una falla provoca testigo ABS encendido en el tablero, "
            "desactivacion del ABS y, en algunos vehiculos, del control de estabilidad."
        ),
        "faq": [
            ("¿Sintomas de sensor ABS dañado?",
             "Testigo ABS encendido en el tablero, codigo de error de la rueda afectada (RR, RL, FR, FL), "
             "perdida del control de estabilidad, lectura de velocidad incorrecta del velocimetro en "
             "algunos vehiculos."),
            ("¿Es del lado izquierdo o derecho?",
             "Confirma con el listing. Cada lado tiene codigo de parte distinto en algunos modelos; en "
             "otros son simetricos."),
            ("¿Es delantero o trasero?",
             "Verifica el listing. Los sensores delanteros y traseros son distintos — los traseros suelen "
             "tener cable mas largo."),
            ("¿Lo puedo cambiar yo?",
             "En la mayoria de los modelos europeos se accede facilmente desde la mangueta de la rueda "
             "con llave torx 30. En otros (especialmente integrados al cubo) requiere desmontar el cubo "
             "de rueda."),
        ],
    },
    "sensor_balata": {
        "rubro": "sensor de desgaste de balata",
        "shopify_type": "Frenos",
        "p1": (
            "Sensor de desgaste de balata (brake pad wear sensor). Es un sensor electrico simple que se "
            "incrusta en una de las balatas (delantera o trasera segun el modelo) y, cuando la balata se "
            "desgasta hasta el limite minimo, el material de friccion lo desgasta y corta el circuito "
            "electrico, encendiendo la luz de servicio de freno en el tablero. Es pieza de mantenimiento "
            "que se reemplaza cada vez que se cambian las balatas — una vez activado, el sensor queda "
            "abierto y debe reemplazarse junto con las balatas nuevas."
        ),
        "faq": [
            ("¿Cuantos sensores tiene mi vehiculo?",
             "Tipicamente uno o dos por eje. BMW y Mercedes suelen tener uno delantero y uno trasero "
             "(dos en total). Confirma con el listing."),
            ("¿Lo cambio aunque la luz no este encendida?",
             "Si — si vas a cambiar las balatas, reemplaza el sensor del eje correspondiente. Reutilizar "
             "un sensor activado deja la luz de servicio encendida."),
            ("¿Resetear la luz despues de cambiar?",
             "En la mayoria de los modelos europeos, la luz se apaga sola al detectar circuito completo. "
             "En algunos (BMW i-series modernos) requiere reseteo con scanner."),
        ],
    },
    "manguera_freno": {
        "rubro": "manguera de freno",
        "shopify_type": "Frenos",
        "p1": (
            "Manguera de freno (brake hose) flexible. Conecta las lineas rigidas del sistema de freno "
            "(que vienen del bloque ABS o de la bomba maestra) con cada caliper, permitiendo el "
            "movimiento de la suspension y la direccion. Esta fabricada con malla de acero trenzado y "
            "recubrimiento de caucho de alta presion, capaz de soportar las presiones tipicas del sistema "
            "(80-150 bar en frenado fuerte). Es pieza de desgaste tipica: el caucho se cuartea por edad y "
            "calor, lo que provoca abultamientos (que ceden bajo presion) o fugas. Es falla critica de "
            "seguridad."
        ),
        "faq": [
            ("¿Sintomas de manguera dañada?",
             "Pedal blando o que cae al piso bajo presion sostenida, fuga visible de liquido, "
             "abultamiento en la manguera al pisar el freno (caucho debilitado), nivel de liquido bajo "
             "con frecuencia."),
            ("¿Cuando reemplazarla preventivamente?",
             "Cada 6-8 anos como mantenimiento preventivo, especialmente en vehiculos que frenan mucho "
             "(uso urbano intenso) o en climas con mucha temperatura."),
            ("¿Trabajo seguro de hacer en casa?",
             "Requiere sangrar el sistema de freno despues del cambio. Si no tienes herramienta de sangrado "
             "y experiencia, lleva el vehiculo a taller — un sistema mal sangrado provoca pedal blando o "
             "freno sin presion."),
        ],
    },
    "cilindro": {
        "rubro": "cilindro de rueda / bomba maestra",
        "shopify_type": "Frenos",
        "p1": (
            "Cilindro de rueda (en frenos de tambor) o cilindro maestro (bomba maestra del sistema). El "
            "cilindro de rueda recibe la presion hidraulica y empuja las balatas contra el tambor; el "
            "cilindro maestro convierte la fuerza del pedal en presion hidraulica que distribuye a los "
            "cuatro frenos. Falla tipica: fuga interna (pedal que cae al piso lentamente), fuga externa "
            "(visible bajo el carro), o pistones atascados."
        ),
        "faq": [
            ("¿Es cilindro de rueda o bomba maestra?",
             "Verifica el titulo. La bomba maestra esta en el motor (junto al servofreno); los cilindros "
             "de rueda solo aplican en frenos de tambor traseros."),
            ("¿Necesito cambiar otros componentes?",
             "Si la bomba fallo por contaminacion del liquido, considera cambiar tambien las mangueras "
             "y purgar el sistema completo."),
        ],
    },
    "bomba_freno": {
        "rubro": "bomba maestra del freno",
        "shopify_type": "Frenos",
        "p1": (
            "Bomba maestra del freno (master cylinder). Convierte la fuerza mecanica del pedal de freno "
            "en presion hidraulica que se distribuye a los cuatro calipers/cilindros de rueda. Las bombas "
            "modernas son tandem (dos circuitos independientes para redundancia de seguridad: si uno falla, "
            "el otro mantiene la mitad del frenado). Falla tipica: pedal que cae al piso lentamente "
            "manteniendolo presionado (fuga interna), perdida progresiva de presion, contaminacion del "
            "liquido por sellos degradados."
        ),
        "faq": [
            ("¿Sintomas de bomba dañada?",
             "Pedal blando o que cae al piso lentamente, perdida de presion al frenar repetidamente, "
             "manchas de liquido en el servofreno o el firewall."),
            ("¿Necesita cebarse despues del cambio?",
             "Si — la bomba nueva debe cebarse fuera del vehiculo y luego sangrar el sistema completo. "
             "Trabajo de taller especializado."),
        ],
    },
    "liquido_freno": {
        "rubro": "liquido de freno",
        "shopify_type": "Frenos",
        "p1": (
            "Liquido de freno (brake fluid) hidraulico para el sistema de freno. Transmite la presion del "
            "pedal a los calipers y debe resistir las altas temperaturas del sistema sin hervir. Las "
            "especificaciones comunes son DOT 3, DOT 4, DOT 5.1 (todas a base de glicol, mas higroscopicas), "
            "y DOT 5 (a base de silicona, no higroscopico, no compatible con sistemas ABS estandar). El "
            "liquido absorbe humedad del ambiente con el tiempo, lo que reduce su punto de ebullicion y "
            "puede provocar 'vapor lock' (perdida de freno por vaporizacion bajo calor). Es mantenimiento "
            "periodico cambiarlo cada 2 anos."
        ),
        "faq": [
            ("¿Cada cuanto se cambia el liquido?",
             "Cada 2 anos para DOT 3/4 estandar; cada 1 ano si haces uso intensivo de freno (montaña, "
             "track, conduccion deportiva)."),
            ("¿DOT 4 vs DOT 5.1?",
             "DOT 5.1 tiene mayor punto de ebullicion y es mejor para conduccion deportiva. Compatible "
             "con DOT 3/4. NO confundir con DOT 5 (silicona) que es incompatible con sistemas con ABS."),
        ],
    },
    "cable_freno": {
        "rubro": "cable del freno de mano",
        "shopify_type": "Frenos",
        "p1": (
            "Cable del freno de mano (parking brake cable, handbrake cable). Conecta la palanca del freno "
            "de mano (o el pedal en algunos modelos) con los mecanismos de freno de las ruedas traseras. "
            "Esta fabricado en acero trenzado dentro de una funda de plastico o caucho. Falla tipica: "
            "desgaste interno (palanca que se levanta mucho sin frenar), oxidacion (cable atascado, freno "
            "que no se libera), o ruptura."
        ),
        "faq": [
            ("¿Sintomas de cable dañado?",
             "Palanca de freno de mano que se levanta mucho sin frenar, freno trasero que no se libera "
             "(rueda caliente), o ruptura visible del cable."),
            ("¿Se cambia el cable o todo el conjunto?",
             "Algunos modelos venden el cable solo, otros como conjunto (cable + funda + tensor). "
             "Verifica el listing."),
        ],
    },
    "booster": {
        "rubro": "servofreno (booster)",
        "shopify_type": "Frenos",
        "p1": (
            "Servofreno o booster del freno (vacuum brake booster). Es la unidad neumatica que asiste la "
            "fuerza del conductor sobre el pedal de freno, multiplicando varias veces la presion aplicada. "
            "Funciona con vacio del motor (en motores gasolina) o con bomba de vacio dedicada (motores "
            "diesel, modernos turbo). Falla tipica: pedal duro que requiere mucha fuerza, sonido de aire "
            "en el firewall al pisar el pedal, fuga de vacio del motor."
        ),
        "faq": [
            ("¿Sintomas de booster dañado?",
             "Pedal de freno duro que requiere mucha fuerza, sonido de aire al pisar el pedal, motor "
             "que tira mucho aire del IAT, vibracion al pisar el freno."),
            ("¿Es trabajo grande?",
             "El booster esta detras de la bomba maestra. Cambiarlo requiere desmontar la bomba y, en "
             "algunos modelos, panel del firewall. Trabajo de 3-5 horas en taller."),
        ],
    },
    "tambor": {
        "rubro": "tambor de freno",
        "shopify_type": "Frenos",
        "p1": (
            "Tambor de freno (brake drum). Sistema de freno tradicional usado principalmente en frenos "
            "traseros de vehiculos comerciales (Sprinter, Crafter) y modelos economicos. El tambor cilindrico "
            "gira con la rueda; cuando se aplica el freno, las balatas (zapatas en este caso) se expanden "
            "contra la cara interna del tambor por accion de los cilindros de rueda. Es sistema mas "
            "economico que el de disco pero menos eficiente — disipa peor el calor en frenado intenso."
        ),
        "faq": [
            ("¿Cuando se cambia el tambor?",
             "Cuando el diametro interior excede el maximo del fabricante (estampado en el tambor), "
             "cuando hay ranuras profundas, o cuando esta fisurado/agrietado."),
            ("¿Mi BMW/Audi tiene tambores?",
             "No es comun en autos de pasajeros europeos modernos — todos tienen disco de freno en las "
             "cuatro ruedas. Los tambores aplican principalmente a Mercedes Sprinter, VW Crafter (vans "
             "comerciales) y algunos modelos antiguos."),
        ],
    },
    "kit_tornilleria": {
        "rubro": "kit tornilleria / accesorios de freno",
        "shopify_type": "Frenos",
        "p1": (
            "Kit de tornilleria, abrazaderas o accesorios de fijacion para componentes del freno. Incluye "
            "elementos de instalacion (tornillos, clips, abrazaderas, espigas) que se reemplazan "
            "regularmente al hacer servicio de freno. Son piezas pequenas pero necesarias — los tornillos "
            "del disco son TTY (torque-to-yield) y deben reemplazarse cada vez; los clips de las balatas "
            "se deforman al desmontar y deben renovarse."
        ),
        "faq": [
            ("¿Que viene en el kit?",
             "Verifica el listing. Tipicamente: tornillos del disco al cubo, clips de las balatas, "
             "muelles de retorno (en frenos de tambor)."),
        ],
    },
    "otro": {
        "rubro": "componente del sistema de frenos",
        "shopify_type": "Frenos",
        "p1": (
            "Componente del sistema de freno del vehiculo. Refaccion para vehiculos europeos. El listing "
            "especifica la pieza exacta y su posicion; si tienes dudas sobre compatibilidad, envianos tu "
            "numero de VIN y un asesor te confirma los detalles antes de procesar el pedido."
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
    if "sensor" in t and ("balata" in t or "desgaste" in t or "pad wear" in t):
        return "sensor_balata"
    if "sensor" in t and "abs" in t:
        return "sensor_abs"
    if "kit" in t and ("caliper" in t or "pinza" in t or "mordaza" in t or "reparacion" in t and "freno" in t):
        return "kit_caliper"
    if ("balata" in t or "pastilla" in t or " pad " in t.replace(",", " ")) and "sensor" not in t:
        return "balata"
    if "disco" in t and "freno" in t:
        return "disco"
    if "caliper" in t or "pinza" in t and "freno" in t or "mordaza" in t:
        return "caliper"
    if "manguera" in t and "freno" in t:
        return "manguera_freno"
    if "bomba" in t and ("freno" in t or "maestra" in t):
        return "bomba_freno"
    if "cilindro" in t and ("rueda" in t or "freno" in t):
        return "cilindro"
    if "liquido" in t and "freno" in t:
        return "liquido_freno"
    if "cable" in t and ("freno" in t or ("mano" in t and "freno" in t)):
        return "cable_freno"
    if "servofreno" in t or "booster" in t and "freno" in t:
        return "booster"
    if "tambor" in t:
        return "tambor"
    if "kit" in t and "tornilleria" in t and "freno" in t:
        return "kit_tornilleria"
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
            "Recomendamos confirmar con el numero de VIN antes de comprar — los componentes de freno varian "
            "frecuentemente por anio, paquete (M Sport, AMG, S-Line) y configuracion."
        )
    else:
        p2 = (
            "La descripcion original del listing menciona modelos compatibles pero no esta estructurada en el "
            "bloque APLICA PARA estandar, por lo que la lista no se pudo extraer automaticamente. "
            f"Por el titulo aplica a vehiculos {tipo_veh.lower() or 'tipo carro/camioneta'} de marcas europeas. "
            "Antes de comprar, envianos tu numero de VIN para que un asesor verifique modelo exacto, anio, "
            "paquete de freno y configuracion contra el catalogo del proveedor."
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
                "Recomendado para componentes de freno por seguridad y por la importancia del balance "
                "entre los dos lados del eje."
            )
        elif es_kit_local:
            p4 = (
                "Se entrega como kit completo en una sola caja con todos los componentes y la tornilleria de "
                "fijacion correspondiente. Reduce tiempos de inventario en taller y asegura compatibilidad "
                "entre piezas."
            )
        else:
            p4 = (
                "Se vende como pieza individual nueva, en empaque del fabricante. Producto no reciclado ni "
                "remanufacturado. Para servicio de freno, recomendamos cambiar tambien la pieza del lado "
                "opuesto del eje al mismo tiempo para mantener el balance del frenado — consulta con "
                "nuestro asesor para confirmar disponibilidad."
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
                "de procesar el pedido. Tambien puedes mencionar el paquete de freno (M Sport, AMG, "
                "deportivo) y el anio del vehiculo."
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
    if tipo in ("caliper", "balata", "disco", "manguera_freno") and not lado:
        revision.append(
            "[VERIFICAR] Pieza de freno sin atributo 'Lado' especificado — confirmar L/R o eje "
            "(delantero/trasero) antes de publicar."
        )
    if tipo == "sensor_abs":
        revision.append(
            "[ANALIZAR] Producto es sensor electrico ABS — considerar si la categoria correcta es "
            "Sistema Electrico en lugar de Frenos para el shopify_type."
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
