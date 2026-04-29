"""
Construye el JSON de resultados enriquecidos para refacciones_electrico (378 filas).

Tipos detectados por keywords del titulo. La logica de seleccion es por orden de especificidad.
"""

import json
import os
import re
import unicodedata
from collections import Counter

HOJA = os.environ.get("EMBLER_HOJA", "ml_con_match")
BATCH_PATH = f"new-output_v2/{HOJA}/refacciones_electrico_batch.json"
OUTPUT_PATH = f"new-output_v2/{HOJA}/refacciones_electrico_batch_result.json"


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
    if "ngk" in raw_low or "denso" in raw_low:
        return (
            f"Marca {marca_norm or marca_raw}, proveedor OEM japones de bujias, sensores y componentes "
            "electronicos automotrices. Suministra a la fabrica para BMW, Mercedes, Audi, VW y otros."
        )
    if "bosch" in raw_low:
        return (
            "Marca Bosch, proveedor OEM aleman de electronica y mecatronica automotriz. Calidad equivalente "
            "al equipo original instalado por el fabricante del vehiculo."
        )
    if "delphi" in raw_low:
        return (
            "Marca Delphi, proveedor OEM de electronica automotriz, sensores e inyectores. Calidad "
            "equivalente al equipo original."
        )
    if "hitachi" in raw_low:
        return (
            "Marca Hitachi, proveedor OEM japones de motores electricos automotrices (alternadores, "
            "motores de arranque) y sensores."
        )
    if "valeo" in raw_low:
        return (
            "Marca Valeo, proveedor OEM frances de sistemas electricos automotrices. Calidad equivalente al "
            "equipo original instalado por el fabricante del vehiculo."
        )
    if not marca_norm:
        return f"Marca de refaccion: {marca_raw or 'no especificada'}."
    return f"Marca {marca_norm}, fabricante de refacciones para vehiculos europeos."


# ---------------------------------------------------------------------------
# Templates por tipo
# ---------------------------------------------------------------------------

TIPO_DEFINICIONES = {
    "bujia": {
        "rubro": "bujia de encendido",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Bujia de encendido (spark plug) para motores de combustion interna a gasolina. Su funcion es "
            "generar la chispa electrica que inicia la combustion de la mezcla aire-combustible en cada "
            "ciclo del motor. La bujia recibe el alto voltaje de la bobina de encendido (entre 20,000 y "
            "40,000 V), lo conduce a traves de su electrodo central y salta hacia el electrodo de masa, "
            "encendiendo la mezcla. Las bujias modernas para vehiculos europeos premium suelen ser de "
            "iridio o doble platino, con vida util de 60,000 a 100,000 km segun el modelo. La degradacion "
            "se manifiesta como ralenti irregular, perdida de potencia, dificultad de arranque en frio, "
            "consumo de combustible elevado o codigos de error de fallo de combustion (P0300-P0306)."
        ),
        "faq": [
            ("¿Cada cuanto se cambian las bujias?",
             "Las de iridio: 100,000 km. Las de doble platino: 80,000 km. Las de cobre: 30,000 km. Verifica "
             "el manual de tu vehiculo, el intervalo varia por motor."),
            ("¿Se cambian todas al mismo tiempo?",
             "Si — siempre se cambian todas a la vez para que el motor tenga combustion balanceada en todos "
             "los cilindros. Cambiar una sola descompensa la mezcla."),
            ("¿Que diferencia hay entre iridio, platino y cobre?",
             "El iridio resiste mas erosion y dura mas (electrodo mas fino, chispa mas concentrada). El "
             "platino es intermedio. El cobre es mas barato pero se desgasta mas rapido. Los motores "
             "europeos modernos exigen iridio o platino — no usar cobre."),
            ("¿Es importante el torque de instalacion?",
             "Si — torque incorrecto puede dañar la rosca de la cabeza del motor (operacion costosa) o "
             "provocar fugas de compresion. Usa torquimetro y respeta los valores del fabricante."),
        ],
    },
    "cable_bujia": {
        "rubro": "kit de cables de bujia",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Kit de cables de bujia (spark plug wires) para motores de encendido distribuido. Conducen el "
            "alto voltaje desde la bobina de encendido (o el distribuidor) hasta cada bujia. Estan "
            "construidos con un nucleo conductor (alambre, fibra de carbono o ferrita) recubierto de "
            "aislante de silicona o EPDM resistente al calor del compartimento del motor. En vehiculos "
            "modernos COP (coil-on-plug) ya no aplican porque cada bujia tiene su propia bobina; los cables "
            "se mantienen en motores con sistema DIS (distributor-less ignition system) o con distribuidor "
            "convencional."
        ),
        "faq": [
            ("¿Sintomas de cables de bujia dañados?",
             "Ralenti irregular, sacudida del motor, perdida de potencia, codigos de error de fallo de "
             "combustion. Visualmente: cables rajados, aislamiento quemado o residuos de carbono."),
            ("¿Cuando se cambian?",
             "Cuando aparecen sintomas o de manera preventiva cada 80,000 a 100,000 km. Conviene cambiarlos "
             "junto con las bujias."),
            ("¿Es kit completo o cables individuales?",
             "El kit incluye los cables para todos los cilindros del motor. Verifica que la cantidad coincida "
             "con tu motor (4, 6 u 8 cilindros)."),
        ],
    },
    "bobina_encendido": {
        "rubro": "bobina de encendido",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Bobina de encendido (ignition coil) para motor de gasolina. Su funcion es elevar los 12V de la "
            "bateria a los 20,000-40,000 V que necesita la bujia para generar la chispa de encendido. La "
            "bobina contiene dos devanados (primario y secundario) con relacion de transformacion alta y un "
            "circuito de control que la activa en el momento exacto del ciclo de combustion. En vehiculos "
            "europeos modernos cada cilindro tiene su propia bobina (sistema COP - coil on plug), montada "
            "directamente sobre la bujia. Cuando una bobina falla, el cilindro correspondiente deja de "
            "encender, generando ralenti irregular y codigo P0300-P0306 segun el cilindro afectado."
        ),
        "faq": [
            ("¿Sintomas de bobina dañada?",
             "Ralenti irregular, sacudida del motor (especialmente en aceleracion), perdida de potencia, "
             "codigo de error P030X (X = numero del cilindro afectado), olor a combustible no quemado."),
            ("¿Se cambian todas al mismo tiempo?",
             "No es obligatorio, pero si una falla con altos kilometros, las demas suelen estar al limite. "
             "Cambiar todas previene fallas sucesivas."),
            ("¿Conviene cambiar tambien las bujias?",
             "Si — conviene cambiar bujias y bobinas como conjunto cuando ya hay desgaste de uno de los dos. "
             "El procedimiento de instalacion es el mismo."),
            ("¿Trae el capuchon (boot)?",
             "Algunas bobinas COP traen integrado el capuchon de goma que sella contra la bujia, otras lo "
             "tienen separado. Verifica con el listing y reemplaza el capuchon si esta dañado."),
        ],
    },
    "capuchon_bobina": {
        "rubro": "capuchon de bobina de encendido",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Capuchon (boot) de bobina de encendido. Es la pieza de goma o silicona que sella la bobina COP "
            "(coil on plug) contra la bujia y proporciona el aislamiento electrico para el alto voltaje. "
            "Tambien protege la conexion de la bobina al pozo de la bujia contra agua, aceite y suciedad. "
            "Es pieza de desgaste tipica: con el calor del motor el caucho se endurece y aparecen fugas "
            "electricas (arc-over) que provocan ralenti irregular y fallos de combustion intermitentes — "
            "puede ser dificil de diagnosticar porque los sintomas aparecen y desaparecen segun la "
            "humedad y temperatura ambiente."
        ),
        "faq": [
            ("¿Por que cambiar el capuchon y no la bobina entera?",
             "Si la bobina misma esta funcional pero el capuchon esta cuarteado, cambiar solo el capuchon "
             "ahorra costo. Es buena practica revisarlo cada vez que se cambian las bujias."),
            ("¿Es obvio cuando esta dañado?",
             "Visualmente: caucho rigido, cuarteaduras, residuos blancos en el labio del capuchon. "
             "Funcionalmente: fallos intermitentes que empeoran en humedad o lluvia."),
            ("¿Trae el resorte interior?",
             "El capuchon viene con el resorte que conecta la bobina con la bujia. Verifica el listing por "
             "el codigo de parte exacto."),
        ],
    },
    "tubo_bujia": {
        "rubro": "tubo / pozo de bujia",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Tubo o pozo de bujia (spark plug tube). Es el conducto de aluminio o plastico que crea el "
            "espacio profundo donde se aloja la bujia y la bobina COP, dentro de la tapa de valvulas del "
            "motor. Contiene tambien un sello en su base que impide que el aceite del motor entre al pozo "
            "y dañe la bobina o la conexion electrica. Cuando el sello falla, aparece aceite en el pozo de "
            "la bujia, lo que provoca arc-over electrico y fallos de combustion. Es problema tipico en BMW "
            "de seis cilindros con motores N51-N55 y M52/M54."
        ),
        "faq": [
            ("¿Como se que el tubo o sello esta dañado?",
             "Aceite visible en el pozo de la bujia al sacarla, fallos de combustion intermitentes "
             "(especialmente bajo carga), olor a aceite quemado del area del motor."),
            ("¿Cambio el tubo o solo el sello?",
             "Depende — si el tubo esta agrietado, todo el conjunto. Si solo el sello falla, cambia los "
             "sellos del tubo (suelen venderse en kit con la junta de tapa de valvulas)."),
        ],
    },
    "bujia_glow": {
        "rubro": "bujia precalentadora (glow plug)",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Bujia precalentadora (glow plug) para motor diesel. Su funcion es calentar la camara de "
            "combustion durante el arranque en frio para asegurar que el combustible diesel se autoencienda "
            "al ser comprimido. A diferencia de las bujias de gasolina (que generan chispa), las "
            "precalentadoras son resistencias electricas que se calientan al rojo cuando se les aplica "
            "corriente. Son indispensables en climas frios y en los primeros minutos de operacion del "
            "motor diesel; sin ellas el motor no arranca o arranca con dificultad expulsando humo blanco. "
            "Se instala una por cilindro."
        ),
        "faq": [
            ("¿Cuando se cambian las bujias precalentadoras?",
             "Cada 80,000-150,000 km segun el motor, o cuando aparece dificultad de arranque en frio. La "
             "computadora del motor detecta la falla y enciende el testigo de bujia precalentadora."),
            ("¿Se cambian todas o solo la dañada?",
             "Conviene cambiar todas al mismo tiempo. Las que aun funcionan suelen estar al limite y "
             "fallaran en pocos meses."),
            ("¿Mi Sprinter las necesita?",
             "Si — la Mercedes Sprinter, VW Crafter, BMW diesel, Audi TDI y todos los motores diesel modernos "
             "europeos las usan. Para mejor diagnostico considera scanner OBD."),
        ],
    },
    "alternador": {
        "rubro": "alternador",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Alternador (generador de corriente alterna) del sistema electrico del vehiculo. Es el "
            "encargado de producir la energia electrica que alimenta todos los sistemas del vehiculo en "
            "marcha y de mantener cargada la bateria. El alternador es accionado por la banda auxiliar del "
            "motor (serpentine belt) y contiene un rotor con bobinas de campo, un estator con bobinas de "
            "salida, un puente rectificador (diodos) que convierte la corriente alterna a continua, y un "
            "regulador de voltaje que mantiene los 13.8-14.4V de salida. Los alternadores modernos europeos "
            "tienen capacidades altas (140-220 amperes) para soportar la electronica del vehiculo, asistencia "
            "electrica de direccion, calefactores electricos y sistemas de informacion-entretenimiento."
        ),
        "faq": [
            ("¿Sintomas de alternador dañado?",
             "Bateria descargada al arrancar, luces que se atenuan en ralenti, testigo de bateria en el "
             "tablero, ruido de chillido o gemido del motor (rodamientos del alternador), olor a quemado."),
            ("¿Cuanto dura un alternador?",
             "Entre 150,000 y 250,000 km en uso normal. Dura mas en autos de uso continuo (carretera) que "
             "en autos de uso urbano con muchos arranques en frio."),
            ("¿Vale la pena el alternador remanufacturado o nuevo?",
             "Las opciones aftermarket nuevas de calidad equivalente OEM rinden igual que un OEM. Los "
             "remanufacturados son mas economicos pero tienen vida util mas corta."),
            ("¿Trae la polea?",
             "Algunos alternadores vienen con polea libre (overrunning alternator pulley, OAP) y otros sin "
             "ella. Confirma con el listing — si tu motor exige OAP por sistema serpentin, no instales uno "
             "con polea fija."),
        ],
    },
    "motor_arranque": {
        "rubro": "motor de arranque",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Motor de arranque (starter motor o marcha) del vehiculo. Su funcion es girar el motor de "
            "combustion interna durante el arranque hasta que entra en operacion autonoma. Esta compuesto "
            "por un motor electrico de corriente continua de alta potencia (1.5-2.5 kW) con un solenoide de "
            "engagement que empuja el pinion de arranque (Bendix) contra la corona del volante motor cuando "
            "se gira la llave. Es uno de los componentes que mas corriente consume del vehiculo en breve "
            "instante (300-600 amperes), por eso el cableado de arranque es de calibre grueso y la bateria "
            "debe estar en buen estado."
        ),
        "faq": [
            ("¿Sintomas de motor de arranque dañado?",
             "Click metalico al girar la llave sin que arranque (bobina del solenoide), giro lento del motor "
             "incluso con bateria buena, ruido de molienda metalica al arrancar (Bendix dañado), o que "
             "simplemente no responde al girar la llave."),
            ("¿Como diferenciarlo de bateria descargada?",
             "Bateria descargada: las luces del tablero se atenuan al girar la llave y no arranca. Motor "
             "de arranque dañado: las luces se mantienen encendidas pero el motor no gira o gira lento. "
             "Confirma con multimetro."),
            ("¿Cuanto tarda en cambiarlo?",
             "Entre 1 y 3 horas dependiendo del modelo. En BMW xDrive o motores transversales puede ser "
             "mas laborioso por la accesibilidad."),
        ],
    },
    "sensor_maf": {
        "rubro": "sensor de masa de aire (MAF)",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Sensor de masa de aire (MAF - Mass Air Flow). Mide la cantidad de aire que entra al colector "
            "de admision y envia la lectura a la ECU para que ajuste la cantidad de combustible que "
            "inyectan los inyectores. Los MAF modernos europeos son de hilo caliente (hot wire) o de pelicula "
            "caliente (hot film), donde un elemento calefactado ve su temperatura modificada por el flujo "
            "de aire que pasa a su alrededor. Es uno de los sensores mas criticos para el funcionamiento "
            "del motor: una falla genera mezcla incorrecta, perdida de potencia, ralenti irregular y "
            "consumo elevado."
        ),
        "faq": [
            ("¿Sintomas de MAF dañado?",
             "Ralenti irregular, perdida de potencia, consumo de combustible elevado, codigos P0101-P0103, "
             "humo negro del escape (mezcla rica) o tirones en aceleracion."),
            ("¿Se puede limpiar en lugar de cambiar?",
             "A veces si — limpiador especifico para sensores MAF puede recuperar uno sucio. Pero si el "
             "elemento sensor esta dañado, no hay limpieza que lo recupere."),
            ("¿Es comun en motores con turbo?",
             "Si — los motores turbo modernos tienen MAF antes del turbocompresor. Una pequeña fuga de aire "
             "despues del MAF (turbo o intercooler) tambien puede generar codigos similares."),
        ],
    },
    "sensor_map": {
        "rubro": "sensor de presion del colector (MAP)",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Sensor MAP (Manifold Absolute Pressure - presion absoluta del colector de admision). Mide la "
            "presion del aire en el colector y envia la lectura a la ECU para calcular la masa de aire por "
            "metodo speed-density (cuando no hay sensor MAF) o como complemento al MAF en motores turbo. "
            "Es indispensable para el control preciso del avance de encendido y la mezcla aire-combustible "
            "en motores con sobrealimentacion. La falla provoca ralenti irregular, codigos P0105-P0108 y "
            "perdida de potencia."
        ),
        "faq": [
            ("¿Sintomas de MAP dañado?",
             "Ralenti irregular, codigo P0105-P0108, perdida de potencia (especialmente en motores turbo), "
             "humo del escape o consumo elevado."),
            ("¿Donde esta ubicado?",
             "Tipicamente en el colector de admision, en motores turbo cerca del turbocompresor. Algunas "
             "veces integrado con el sensor de temperatura del aire de admision (IAT)."),
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
            ("¿Lo puedo cambiar yo?",
             "En muchos modelos europeos se accede facilmente desde la mangueta de la rueda con llave "
             "torx 30. En otros (especialmente integrados al cubo) requiere desmontar el cubo de rueda."),
            ("¿Por que aparece el testigo solo a veces?",
             "Los sensores ABS pueden ensuciarse con polvo de freno o oxidarse con el tiempo. Una limpieza "
             "del sensor y la rueda fonica puede recuperarlo, pero si el daño es interno requiere reemplazo."),
        ],
    },
    "sensor_ckp": {
        "rubro": "sensor de cigueñal (CKP)",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Sensor de posicion del cigueñal (CKP - Crankshaft Position). Es uno de los sensores mas "
            "criticos del motor: detecta la posicion y velocidad de rotacion del cigueñal, dato que la "
            "ECU usa como referencia maestra para todo el control del motor (sincronizacion de "
            "encendido, momento de inyeccion, deteccion de fallos de combustion). Se monta cerca del "
            "volante motor y lee los dientes de una rueda fonica fijada al cigueñal. Una falla provoca "
            "que el motor no arranque o se apague en marcha — es falla critica de drivability."
        ),
        "faq": [
            ("¿Sintomas de CKP dañado?",
             "Motor que no arranca, motor que se apaga en marcha (especialmente en caliente), tableteo "
             "intermitente, codigo P0335-P0339. La falla puede ser intermitente con calor del motor."),
            ("¿Con que frecuencia falla?",
             "Es un sensor relativamente robusto — se cambia tipicamente despues de 150,000-200,000 km, "
             "o cuando aparece la falla. La falla mas comun es por temperatura: fallan en caliente y "
             "vuelven a funcionar al enfriar."),
        ],
    },
    "sensor_cmp": {
        "rubro": "sensor de arbol de levas (CMP)",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Sensor de posicion del arbol de levas (CMP - Camshaft Position). Detecta la posicion del "
            "arbol de levas para que la ECU sepa en que ciclo de combustion esta cada cilindro y pueda "
            "controlar la inyeccion secuencial y, en motores con VANOS/VVT, la posicion de los arboles "
            "variables. Un sensor de levas dañado puede provocar arranque difícil, ralenti irregular o "
            "imposibilidad de variacion del avance. En motores con doble VANOS hay un sensor por arbol."
        ),
        "faq": [
            ("¿Sintomas de CMP dañado?",
             "Motor que arranca con dificultad, ralenti irregular, codigos P0340-P0349 segun el cilindro/banco. "
             "En BMW con VANOS: codigo P1004-P1006 si afecta al sistema variable."),
            ("¿Cuantos sensores CMP tiene mi motor?",
             "Motores 4 cilindros: tipicamente 1. Motores 6 cilindros con doble VANOS: 2. Motores V8/V10/V12: "
             "uno por banco (2 o mas)."),
        ],
    },
    "sensor_o2": {
        "rubro": "sensor de oxigeno / lambda",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Sensor de oxigeno (O2 sensor o lambda) del sistema de escape. Mide el contenido de oxigeno en "
            "los gases de escape para que la ECU ajuste la mezcla aire-combustible en bucle cerrado, "
            "manteniendola en la proporcion estequiometrica (lambda = 1) que optimiza la conversion del "
            "catalizador. Hay dos tipos por banco del motor: el sensor pre-catalizador (upstream) que se "
            "usa para el control de mezcla, y el sensor post-catalizador (downstream) que monitorea la "
            "eficiencia del convertidor catalitico. Los sensores modernos europeos son de banda ancha "
            "(LSU) con calefactor interno para alcanzar temperatura de operacion rapidamente."
        ),
        "faq": [
            ("¿Sintomas de sensor O2 dañado?",
             "Codigos P0130-P0167 segun el banco/posicion, consumo de combustible elevado, ralenti "
             "irregular, testigo de motor encendido, falla de prueba de emisiones."),
            ("¿Cada cuanto se cambia?",
             "Tipicamente 100,000-150,000 km. La sonda lambda envejece y pierde sensibilidad con el tiempo, "
             "incluso sin codigo de error explicito."),
            ("¿Pre-cat o post-cat?",
             "Verifica la posicion en el listing — son sensores distintos con codigos de parte distintos. "
             "El pre-cat es el critico para el control de mezcla."),
        ],
    },
    "sensor_temp": {
        "rubro": "sensor de temperatura",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Sensor de temperatura del refrigerante o del aire de admision. Mide la temperatura del "
            "componente correspondiente y envia la lectura a la ECU, que ajusta la mezcla, el avance de "
            "encendido y la activacion del ventilador de refrigeracion segun corresponda. El sensor de "
            "temperatura del refrigerante (ECT) es critico para el arranque en frio y la proteccion del "
            "motor contra sobrecalentamiento; el de temperatura del aire de admision (IAT) ajusta la "
            "mezcla segun la densidad del aire. Es una pieza pequeña pero cuya falla genera multiples "
            "sintomas indirectos."
        ),
        "faq": [
            ("¿Sintomas de sensor de temperatura dañado?",
             "Ralenti irregular, dificultad de arranque en frio, ventilador del radiador que no se "
             "activa o que se queda encendido permanentemente, indicador de temperatura erratico."),
            ("¿Cual es el ECT y cual el IAT?",
             "El ECT (Engine Coolant Temperature) suele estar en la cabeza del motor o en el termostato. "
             "El IAT (Intake Air Temperature) en el conducto de admision o integrado con el MAF."),
        ],
    },
    "sensor_tps": {
        "rubro": "sensor TPS (posicion del cuerpo de aceleracion)",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Sensor TPS (Throttle Position Sensor) del cuerpo de aceleracion. Mide el angulo de apertura "
            "del cuerpo de aceleracion (mariposa) y envia la lectura a la ECU para que ajuste la respuesta "
            "del motor a la peticion del conductor. En motores modernos con cuerpo de aceleracion "
            "electronico (drive-by-wire), el TPS forma parte del cuerpo y sus dos potenciometros redundantes "
            "permiten al sistema detectar fallas. Una falla provoca respuesta erratica del acelerador, "
            "ralenti irregular o entrada en modo de emergencia (limp mode)."
        ),
        "faq": [
            ("¿Sintomas de TPS dañado?",
             "Respuesta erratica del acelerador, ralenti irregular, perdida de potencia repentina, codigos "
             "P0120-P0124, vehiculo en modo de emergencia con potencia limitada."),
            ("¿El TPS se compra solo o con el cuerpo de aceleracion?",
             "En motores modernos con drive-by-wire, el TPS suele venir integrado en el cuerpo de "
             "aceleracion y no se vende por separado. En motores antiguos con cable, se cambia solo."),
        ],
    },
    "sensor_aceite": {
        "rubro": "sensor de aceite",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Sensor de aceite del motor. Hay tres tipos principales: sensor de presion (mide la presion del "
            "circuito de aceite, alarma cuando es insuficiente), sensor de nivel (mide la altura del aceite "
            "en el carter, alimenta el indicador del tablero), y sensor de calidad (mide la conductividad y "
            "temperatura del aceite en motores BMW modernos para el indicador 'Service' de cambio de aceite "
            "por condicion). Es pieza tipica de mantenimiento — un sensor de calidad dañado no permite "
            "resetear el indicador de servicio sin scanner especifico."
        ),
        "faq": [
            ("¿Que sensor de aceite es?",
             "Verifica el listing — los tres tipos (presion, nivel, calidad) tienen codigos de parte "
             "distintos. La posicion de instalacion tambien varia."),
            ("¿Es comun que falle?",
             "El sensor de calidad de BMW (oil condition sensor) es punto debil conocido — falla con el "
             "calor y la humedad acumulada. Los de presion y nivel son mas robustos."),
        ],
    },
    "sensor_otro": {
        "rubro": "sensor electrico del vehiculo",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Sensor electrico para el sistema de control del motor o del vehiculo. Los sensores envian "
            "informacion en tiempo real a la ECU para el control preciso de los sistemas: combustion, "
            "frenos, suspension, climatizacion. Una falla genera codigos de error especificos y puede "
            "provocar funcionamiento degradado o entrada del sistema en modo de emergencia. Verifica el "
            "titulo y codigo de parte para identificar exactamente la funcion del sensor."
        ),
        "faq": [
            ("¿Como se diagnostica una falla del sensor?",
             "Con scanner OBD-II o especifico de la marca (INPA para BMW, XENTRY para Mercedes, ETKA/ODIS "
             "para Audi-VW). El codigo de error indica el sensor afectado."),
            ("¿Cambio el sensor o solo el conector?",
             "A veces el problema es el conector electrico o el cableado. Si el codigo persiste despues de "
             "limpiar el conector, reemplaza el sensor."),
        ],
    },
    "modulo_ecu": {
        "rubro": "modulo electronico / ECU / DME",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Modulo electronico de control (ECU - Engine Control Unit; DME - Digital Motor Electronics en "
            "BMW; Motronic en Mercedes). Es el cerebro del motor: recibe las senales de todos los sensores, "
            "calcula los parametros de inyeccion, encendido, control de emisiones y comunica con los demas "
            "modulos del vehiculo a traves de la red CAN. Las fallas suelen requerir codificacion al VIN "
            "del vehiculo (procedimiento que solo realizan talleres con scanner especializado). Los modulos "
            "europeos modernos tienen proteccion contra robos integrada (EWS, DAS, Immobilizer) que "
            "obliga a sincronizarlos con el resto del sistema."
        ),
        "faq": [
            ("¿La ECU usada de otro vehiculo me sirve?",
             "No directamente — debe codificarse al VIN del vehiculo destino y sincronizar con el "
             "immobilizer. Algunos talleres especializados realizan este procedimiento; sin el, el motor no "
             "arranca."),
            ("¿Sintomas de ECU dañada?",
             "Motor que no arranca, codigos multiples sin patron logico, comunicacion CAN intermitente, "
             "modulos que aparecen y desaparecen del scanner."),
            ("¿Cuanto cuesta la codificacion?",
             "Varia segun el taller — generalmente entre 1500 y 5000 MXN para BMW/Mercedes/Audi-VW. "
             "Confirma costo total antes de comprar el modulo."),
        ],
    },
    "inyector": {
        "rubro": "inyector de combustible",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Inyector de combustible para motor de inyeccion electronica. Su funcion es atomizar el "
            "combustible al colector de admision (inyeccion indirecta) o directamente a la camara de "
            "combustion (inyeccion directa GDI/TFSI/TDI) en el momento exacto del ciclo del motor. Los "
            "inyectores modernos europeos son piezoelectricos o solenoidales con tolerancias muy precisas. "
            "Una falla provoca consumo elevado, humo negro/blanco del escape, perdida de potencia y "
            "fallos de combustion. La falla mas comun es obstruccion por residuos del combustible o "
            "desgaste de la valvula interna."
        ),
        "faq": [
            ("¿Sintomas de inyector dañado?",
             "Ralenti irregular, codigos de fallo de combustion, humo del escape, consumo elevado, olor a "
             "combustible no quemado, dificultad de arranque."),
            ("¿Conviene cambiar uno o todos?",
             "Los inyectores deben tener flujo balanceado entre cilindros. Si uno falla con altos kilometros, "
             "los demas pueden estar al limite — considera reemplazo del juego."),
            ("¿Necesita codificacion despues del reemplazo?",
             "Los inyectores piezoelectricos modernos (BMW, Mercedes, Audi-VW) requieren codificacion del "
             "valor de calibracion individual al modulo. Sin codificacion, el motor funciona con mezclas "
             "incorrectas."),
        ],
    },
    "bomba_gasolina": {
        "rubro": "bomba de gasolina",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Bomba de gasolina (fuel pump) del vehiculo. Su funcion es enviar el combustible del tanque al "
            "sistema de inyeccion a la presion requerida. Los vehiculos europeos modernos tienen "
            "configuraciones variadas: bomba primaria sumergida en el tanque + bomba de alta presion en el "
            "motor (sistemas GDI/TFSI/TDI), o bomba unica de baja presion (sistemas de inyeccion "
            "indirecta). Una falla provoca dificultad o imposibilidad de arranque, ruido del tanque al "
            "girar la llave (zumbido del motor de la bomba) o perdida de potencia bajo carga."
        ),
        "faq": [
            ("¿Sintomas de bomba de gasolina dañada?",
             "Motor que no arranca, motor que se apaga en marcha, ruido fuerte del tanque, perdida de "
             "potencia bajo carga (subidas, aceleraciones fuertes)."),
            ("¿Trae el flotador y filtro?",
             "Algunas bombas vienen como conjunto modular completo (modulo de bomba + flotador + filtro), "
             "otras solo el motor de la bomba. Verifica con el listing."),
            ("¿Es bomba primaria o de alta presion?",
             "Depende del sistema. Los listings tipicamente especifican 'bomba sumergible' (primaria) o "
             "'bomba alta presion' (HPFP, en motores GDI/TFSI/TDI)."),
        ],
    },
    "cuerpo_aceleracion": {
        "rubro": "cuerpo de aceleracion electronico",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Cuerpo de aceleracion electronico (drive-by-wire throttle body). Reemplaza el cuerpo de "
            "aceleracion mecanico tradicional con un sistema en el que el pedal del acelerador es solo un "
            "potenciometro y la apertura de la mariposa la realiza un motor electrico controlado por la "
            "ECU. Esto permite control preciso de la respuesta del motor, control de traccion y "
            "modulacion automatica para optimizar consumo y emisiones. El cuerpo integra el motor "
            "electrico, el sensor TPS doble redundante y, en algunos modelos, el sensor IAT y MAP. Una "
            "falla provoca entrada del motor en modo de emergencia con potencia limitada."
        ),
        "faq": [
            ("¿Sintomas de cuerpo de aceleracion dañado?",
             "Vehiculo en modo de emergencia (limp mode), respuesta erratica del acelerador, ralenti "
             "irregular, codigos P0120-P0124 o P2100-P2106."),
            ("¿Necesita 'aprender' al instalarlo?",
             "Si — la mayoria de los vehiculos europeos requieren un procedimiento de adaptacion del "
             "cuerpo nuevo a la ECU (basic settings) con scanner. Sin esta adaptacion, el ralenti queda "
             "irregular."),
        ],
    },
    "valvula_egr_pcv": {
        "rubro": "valvula EGR / PCV",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Valvula EGR (Exhaust Gas Recirculation) o PCV (Positive Crankcase Ventilation). La EGR "
            "recircula gases de escape al colector de admision para reducir emisiones de NOx, controlada "
            "electronicamente por la ECU. La PCV ventila los gases del carter del motor hacia la admision "
            "para que se quemen, evitando contaminacion ambiental. Ambas son valvulas de control de "
            "emisiones tipicamente afectadas por carbonizacion y desgaste con el tiempo, especialmente en "
            "motores diesel. Una falla provoca codigos de emisiones, ralenti irregular y consumo elevado."
        ),
        "faq": [
            ("¿Sintomas de EGR dañada?",
             "Codigo P0401-P0409, perdida de potencia, ralenti irregular, falla de prueba de emisiones, "
             "humo negro o gris del escape."),
            ("¿Se puede limpiar?",
             "A veces — limpieza con limpiador especifico puede recuperar una EGR carbonizada. Pero si el "
             "motor electrico interno o el sensor de posicion fallaron, requiere reemplazo."),
            ("¿Mi diesel la necesita?",
             "Si — la EGR es elemento clave del control de emisiones en diesel modernos. Su deshabilitacion "
             "(no recomendada en territorio mexicano) requiere reflasheo de la ECU."),
        ],
    },
    "valvula_vvt": {
        "rubro": "valvula solenoide VVT / VANOS",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Valvula solenoide VVT (Variable Valve Timing) o VANOS (BMW). Es la valvula electromagnetica "
            "que dirige el flujo de aceite hacia el actuador del arbol de levas variable, ajustando la "
            "posicion del arbol para optimizar potencia y consumo segun el regimen del motor. En BMW se "
            "llama VANOS solenoid; en Mercedes y Audi-VW se llama valvula VVT. Una falla provoca codigos "
            "de error del sistema variable (P0010-P0014, P1004-P1006), perdida de torque a bajas RPM o "
            "ralenti irregular."
        ),
        "faq": [
            ("¿Sintomas de valvula VVT dañada?",
             "Perdida de torque a bajas RPM, codigos P0010-P0014 (Audi/VW/Mercedes) o P1004-P1006 (BMW), "
             "ralenti irregular en caliente, humo del escape al arrancar."),
            ("¿Se cambia con el actuador VANOS?",
             "Si la valvula esta dañada pero el actuador (sello hidraulico del arbol) esta bien, solo la "
             "valvula. Si ambos tienen sintomas, considera kit de reparacion completo."),
            ("¿Tiene sentido limpiarla en lugar de reemplazar?",
             "A veces — la valvula puede atascarse por residuos del aceite. Limpieza con disolvente puede "
             "recuperarla, pero si el solenoide interno fallo, requiere reemplazo."),
        ],
    },
    "relay": {
        "rubro": "relay / rele electrico",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Relay (rele) electrico del vehiculo. Es un interruptor electromagnetico que permite a un "
            "circuito de baja corriente activar uno de alta corriente. Los vehiculos modernos tienen "
            "decenas de relays distintos: para luces, motor de arranque, bomba de gasolina, ventiladores, "
            "compresor de A/C, etc. Una falla provoca que el componente que controla el relay no funcione, "
            "o funcione de manera intermitente."
        ),
        "faq": [
            ("¿Como se que el relay esta fallando?",
             "El componente que activa no funciona, no escuchas el 'click' caracteristico al activarse, o "
             "el relay tiene aspecto quemado. Test con multimetro confirma."),
            ("¿Es comun la falla?",
             "Los relays son robustos pero los de alta corriente (motor de arranque, ventilador) se "
             "desgastan con el uso. Reemplazar es economico y rapido."),
        ],
    },
    "actuador_combustible": {
        "rubro": "motor actuador tapa de combustible",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Motor actuador de la tapa de combustible (fuel filler door actuator). Es el motor electrico "
            "que abre y cierra la tapa del deposito de combustible cuando se acciona el boton del tablero "
            "o el control remoto. Es pieza pequeña pero su falla provoca tapa atascada (no se puede "
            "cargar combustible) o tapa abierta permanentemente. Tipico en Mercedes-Benz y BMW modernos "
            "con tapa motorizada."
        ),
        "faq": [
            ("¿Por que mi tapa de combustible no abre?",
             "Tipicamente: actuador electrico dañado, motor dentro del actuador roto, conector "
             "desconectado, o palanca interna trabada. Si oyes el motor pero la tapa no se mueve, suele ser "
             "el mecanismo interno."),
            ("¿Lo puedo reemplazar yo?",
             "En la mayoria de los modelos se accede desde el interior del compartimento de equipaje "
             "soltando el panel lateral. Trabajo accesible para mecanico medio."),
        ],
    },
    "otro": {
        "rubro": "componente del sistema electrico",
        "shopify_type": "Sistema Eléctrico",
        "p1": (
            "Componente del sistema electrico o de encendido del vehiculo. Refaccion para vehiculos "
            "europeos. El listing especifica la funcion exacta del componente; si tienes dudas sobre la "
            "compatibilidad con tu modelo o el procedimiento de instalacion, envianos tu numero de VIN "
            "y un asesor te confirma los detalles antes de procesar el pedido."
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
    if "capuchon" in t and ("bobina" in t or "ignic" in t):
        return "capuchon_bobina"
    if "tubo" in t and "bujia" in t:
        return "tubo_bujia"
    if "bujia" in t and "precalent" in t:
        return "bujia_glow"
    if "cable" in t and "bujia" in t:
        return "cable_bujia"
    if "bujia" in t:
        return "bujia"
    if "bobina" in t and ("ignic" in t or "encend" in t):
        return "bobina_encendido"
    if "alternador" in t:
        return "alternador"
    if "motor de arranque" in t or "marcha" in t and "motor" in t and "encend" not in t:
        return "motor_arranque"
    if "starter" in t:
        return "motor_arranque"
    if "valvula" in t and ("vvt" in t or "vanos" in t or "solenoide" in t and "arbol" in t):
        return "valvula_vvt"
    if "valvula" in t and ("egr" in t or "pcv" in t):
        return "valvula_egr_pcv"
    if "sensor" in t and ("maf" in t or "masa de aire" in t or "flujo" in t):
        return "sensor_maf"
    if "sensor" in t and ("map" in t or ("presion" in t and "colector" in t)):
        return "sensor_map"
    if "sensor" in t and ("abs" in t or ("velocidad" in t and "rueda" in t)):
        return "sensor_abs"
    if "sensor" in t and ("ciguenal" in t or "cigüenal" in t or "cigueñal" in t or "cigueñ" in t or "crank" in t or "ckp" in t):
        return "sensor_ckp"
    if "sensor" in t and ("levas" in t or "cmp" in t or ("arbol" in t and "levas" in t)):
        return "sensor_cmp"
    if "sensor" in t and ("oxigeno" in t or "lambda" in t or "o2" in t):
        return "sensor_o2"
    if "sensor" in t and "temp" in t:
        return "sensor_temp"
    if "sensor" in t and ("posicion" in t or "tps" in t or "throttle" in t):
        return "sensor_tps"
    if "sensor" in t and "aceite" in t:
        return "sensor_aceite"
    if "sensor" in t:
        return "sensor_otro"
    if "modulo" in t or "computadora" in t or "ecu" in t or "dme" in t or "motronic" in t:
        return "modulo_ecu"
    if "inyector" in t:
        return "inyector"
    if "bomba" in t and ("gasolina" in t or "combustible" in t):
        return "bomba_gasolina"
    if "cuerpo" in t and "aceleracion" in t:
        return "cuerpo_aceleracion"
    if "relay" in t or "rele" in t:
        return "relay"
    if "tapa" in t and "combustible" in t and ("motor" in t or "actuador" in t):
        return "actuador_combustible"
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
        es_kit_local = bool(re.search(r"\b(kit|juego|set|\d+\s*p[ie]zas?)\b", titulo, re.IGNORECASE))
        if es_par_local:
            p4 = (
                "Se entrega como par completo, ambos lados (izquierdo y derecho) en la misma caja. "
                "Vender en par es la presentacion estandar para sensores y componentes simetricos."
            )
        elif es_kit_local:
            p4 = (
                "Se entrega como kit completo en una sola caja con todas las unidades necesarias para los "
                "cilindros del motor (4, 6 u 8 segun el modelo). Cambiar todo el kit asegura combustion "
                "balanceada entre cilindros."
            )
        else:
            p4 = (
                "Se vende como pieza individual nueva, en empaque del fabricante. Producto no reciclado ni "
                "remanufacturado. Si tu reparacion requiere reemplazar la pieza tambien en el lado opuesto "
                "o el conjunto completo (ej. todas las bobinas COP), consulta con nuestro asesor."
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
    es_kit = bool(re.search(r"\b(kit|juego|set|\d+\s*p[ie]zas?)\b", titulo, re.IGNORECASE)) or bool(incluye)
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
    if tipo == "modulo_ecu":
        revision.append(
            "[ANALIZAR] Modulos ECU/DME requieren codificacion al VIN del vehiculo destino. "
            "Confirmar con el cliente que tiene acceso a taller con scanner especializado."
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
