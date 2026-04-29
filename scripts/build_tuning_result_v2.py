"""
Construye el JSON de resultados enriquecidos para tuning (110 filas) usando el flujo v2.

Lee new-output_v2/ml_con_match/tuning_batch.json (con campos pre-parseados) y produce
seccion_descripcion en 5 parrafos profesionales + seccion_compatibilidades + columnas Shopify
para cada producto.

Los productos de tuning se clasifican en tres tipos por palabras clave del titulo:
  - foco_xenon       (Foco/Focos Xenon Dx)
  - balastra_xenon   (Balastra/Modulo control)
  - cuerpo_aero      (Spoiler/Aleron/Faldon/Lip/Moldura facia)
  - moldura_cromada  (Moldura calavera, parrilla cromada, biseles)

Cada tipo usa una funcion dedicada que arma los 5 parrafos a partir de los datos del producto.
"""

import json
import os
import re
import unicodedata

HOJA = os.environ.get("EMBLER_HOJA", "ml_con_match")
BATCH_PATH = f"new-output_v2/{HOJA}/tuning_batch.json"
OUTPUT_PATH = f"new-output_v2/{HOJA}/tuning_batch_result.json"


# ---------------------------------------------------------------------------
# Secciones fijas
# ---------------------------------------------------------------------------

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


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:100]


def title_clean(t: str) -> str:
    return t.replace("&", "").rstrip().strip()


def body_html(desc: str, compat_lista: str, antes: str, envio: str, faqs: list) -> str:
    parrafos = "".join(
        f"<p>{p.strip()}</p>" for p in desc.split("\n\n") if p.strip()
    )
    compat_html = ""
    if compat_lista.strip():
        items = [l.strip() for l in compat_lista.splitlines() if l.strip()]
        compat_html = (
            "<h2>Compatibilidades</h2><ul>"
            + "".join(f"<li>{i}</li>" for i in items)
            + "</ul>"
        )
    faq_html = "<h2>Preguntas Frecuentes</h2>" + "".join(
        f"<h3>{f['pregunta']}</h3><p>{f['respuesta']}</p>" for f in faqs
    )
    devs_html = "<h2>Politica de Devolucion</h2>" + "".join(
        f"<p>{p.strip()}</p>" for p in SECCION_DEVOLUCIONES.split("\n\n") if p.strip()
    )
    return (
        "<h2>Descripcion</h2>"
        + parrafos
        + compat_html
        + "<h2>Antes de Comprar</h2><p>" + antes + "</p>"
        + "<h2>Envio</h2><p>" + envio + "</p>"
        + devs_html
        + faq_html
    )


# ---------------------------------------------------------------------------
# Posicionamiento de marca (reusable)
# ---------------------------------------------------------------------------

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
    if not marca_norm or marca_norm.lower() in ("", "no aplica"):
        return f"Marca de refaccion: {marca_raw or 'no especificada'}."
    if "osram" in (marca_norm + marca_raw).lower():
        return (
            "Marca Osram, fabricante OEM aleman de iluminacion automotriz. "
            "Calidad equivalente al equipo original; suministra a la fabrica para vehiculos europeos premium."
        )
    return f"Marca {marca_norm}, fabricante de refacciones para vehiculos europeos."


# ---------------------------------------------------------------------------
# Tipo: Foco Xenon
# ---------------------------------------------------------------------------

XENON_TIPOS = {
    "D1S": "D1S (lampara HID con ignitor integrado, conector PK32d-2). Common en BMW Serie 1, 3, 5, 7 y X1-X6 con faros de xenon.",
    "D2S": "D2S (lampara HID sin ignitor, conector P32d-2). Common en BMW E-series antiguos y modelos europeos premium 2000-2010.",
    "D3S": "D3S (lampara HID sin mercurio, conector PK32d-5). Estandar en Audi, VW, BMW F-series, Mercedes y otros premium 2010+.",
    "D4S": "D4S (lampara HID sin mercurio, conector P32d-5). Variante usada principalmente por marcas japonesas y algunos europeos.",
}


def detectar_xenon_tipo(titulo: str, modelo: str) -> str:
    text = (titulo + " " + modelo).upper()
    for t in ("D1S", "D2S", "D3S", "D4S"):
        if t in text:
            return t
    return ""


def detectar_kelvin(titulo: str, modelo: str) -> str:
    text = (titulo + " " + modelo)
    m = re.search(r"(\d{4})\s*[Kk]\b", text)
    if m:
        return m.group(1) + "K"
    if "4300" in text:
        return "4300K"
    if "7500" in text:
        return "7500K"
    return ""


def detectar_watts(titulo: str, modelo: str) -> str:
    text = (titulo + " " + modelo)
    m = re.search(r"(\d{2,3})\s*[Ww]\b", text)
    if m:
        return m.group(1) + "W"
    return ""


def build_foco_xenon(p: dict) -> dict:
    titulo = p["titulo"]
    modelo_attr = p.get("modelo_atributo", "")
    tipo = detectar_xenon_tipo(titulo, modelo_attr)
    kelvin = detectar_kelvin(titulo, modelo_attr)
    watts = detectar_watts(titulo, modelo_attr)

    desc_tipo = XENON_TIPOS.get(tipo, "lampara HID xenon de alta intensidad")
    espec_tecnicas = []
    if tipo:
        espec_tecnicas.append(f"tipo {tipo}")
    if kelvin:
        espec_tecnicas.append(f"temperatura de color {kelvin}")
    if watts:
        espec_tecnicas.append(f"potencia {watts}")
    espec_str = ", ".join(espec_tecnicas) if espec_tecnicas else "especificacion estandar HID"

    p1 = (
        f"Foco xenon HID (High Intensity Discharge) {espec_str} para vehiculos europeos. "
        "A diferencia de los focos halogenos convencionales, el xenon genera luz mediante un arco electrico "
        "entre dos electrodos en una camara presurizada con gas xenon, lo que produce luz mas blanca, mayor "
        "alcance y consumo electrico menor. Estos focos requieren una balastra electronica para arrancar y "
        "regular la corriente del arco; no son intercambiables con bombillas halogenas estandar sin la "
        "instalacion electrica correspondiente."
    )

    if tipo:
        p1 += f" Tipo {tipo}: {desc_tipo}"

    return _ensamblar(
        p, p1=p1,
        rubro="iluminacion xenon HID",
        nombre_base=f"Foco Xenon {tipo} para Vehiculos Europeos" if tipo else "Foco Xenon HID para Vehiculos Europeos",
        shopify_type="Iluminación",
        faqs_extra=[
            {
                "pregunta": f"¿Que es un foco {tipo or 'xenon'}?",
                "respuesta": (
                    f"Es una lampara HID xenon {desc_tipo if tipo else 'de descarga de alta intensidad'}. "
                    "Genera luz mediante un arco electrico entre electrodos en una camara con gas xenon, "
                    "produciendo iluminacion mas blanca y mayor alcance que los halogenos convencionales."
                ),
            },
            {
                "pregunta": "¿Necesita balastra para funcionar?",
                "respuesta": (
                    "Si. Los focos xenon HID requieren una balastra electronica que regula la corriente del "
                    f"arco y arranca el foco a alto voltaje. Si tu vehiculo ya tiene faros de xenon de fabrica, "
                    "ya tiene la balastra instalada."
                ),
            },
            {
                "pregunta": (
                    f"¿Que temperatura de color tiene?" if kelvin else "¿Que temperatura de color es?"
                ),
                "respuesta": (
                    f"{kelvin} — luz mas blanca y ligeramente azulada, similar a la luz del dia."
                    if kelvin
                    else "Verifica la especificacion del listing — la mayoria de focos D1S/D3S OEM son 4300K (luz blanca neutra)."
                ),
            },
            {
                "pregunta": "¿Se vende en par o por unidad?",
                "respuesta": (
                    "El listing es por unidad salvo que el titulo indique 'par' o 'kit'. "
                    "Te recomendamos cambiar ambos focos al mismo tiempo para que la temperatura de color "
                    "sea uniforme entre los dos faros."
                ),
            },
        ],
    )


# ---------------------------------------------------------------------------
# Tipo: Balastra Xenon
# ---------------------------------------------------------------------------

def build_balastra(p: dict) -> dict:
    titulo = p["titulo"]
    p1 = (
        "Balastra (modulo electronico de control de luz xenon) para faros HID de vehiculos europeos. "
        "Su funcion es arrancar y regular el arco electrico del foco xenon: convierte los 12V de la bateria "
        "en el alto voltaje (entre 20,000 y 30,000 V durante el arranque) que necesita la lampara para "
        "encender, y luego mantiene una corriente estable durante el funcionamiento. Sin balastra el foco "
        "xenon no puede funcionar; una balastra defectuosa provoca focos que parpadean, no encienden, o "
        "que cambian de color en operacion."
    )

    return _ensamblar(
        p, p1=p1,
        rubro="balastra control xenon",
        nombre_base="Balastra de Control de Luz Xenon HID para Vehiculos Europeos",
        shopify_type="Iluminación",
        faqs_extra=[
            {
                "pregunta": "¿Que hace una balastra?",
                "respuesta": (
                    "Convierte los 12V de la bateria en el alto voltaje (20,000-30,000 V) que necesita el "
                    "foco xenon para arrancar, y regula la corriente durante el funcionamiento. Sin balastra "
                    "el foco no enciende."
                ),
            },
            {
                "pregunta": "¿Como se que mi balastra esta fallando?",
                "respuesta": (
                    "Sintomas comunes: el foco xenon parpadea, tarda en encender, no enciende, cambia de "
                    "color o se apaga solo. Tambien puede aparecer un codigo de error en el panel del vehiculo."
                ),
            },
            {
                "pregunta": "¿Vale la pena cambiar las dos balastras al mismo tiempo?",
                "respuesta": (
                    "Si una falla, lo comun es que la del otro lado tenga uso similar. Cambiar ambas reduce "
                    "el riesgo de regresar al taller en pocos meses por la balastra opuesta."
                ),
            },
            {
                "pregunta": "¿Esta balastra es OEM?",
                "respuesta": (
                    "Verifica el numero de parte de tu balastra original contra el del listing. Las balastras "
                    "OEM tienen codigos consistentes con el fabricante del vehiculo (BMW, Audi, etc.)."
                ),
            },
        ],
    )


# ---------------------------------------------------------------------------
# Tipo: Cuerpo aerodinamico (spoiler / aleron / faldon / lip / moldura facia)
# ---------------------------------------------------------------------------

def detectar_aero_tipo(titulo: str) -> str:
    t = titulo.lower()
    if "lip" in t:
        return "lip"
    if "faldon" in t:
        return "faldon"
    if "aleron" in t:
        return "aleron"
    if "spoiler" in t:
        return "spoiler"
    if "moldura" in t or "facia" in t:
        return "moldura"
    return "componente aerodinamico"


def detectar_posicion(titulo: str) -> str:
    t = titulo.lower()
    if "delantero" in t or "delantera" in t:
        return "delantero"
    if "trasero" in t or "trasera" in t:
        return "trasero"
    if "inferior" in t:
        return "inferior"
    return ""


def build_cuerpo_aero(p: dict) -> dict:
    titulo = p["titulo"]
    tipo = detectar_aero_tipo(titulo)
    pos = detectar_posicion(titulo)

    descripcion_funcion = {
        "lip": (
            "Lip o labio aerodinamico: pieza inferior de la defensa que extiende el carenado hacia el suelo, "
            "reduciendo la cantidad de aire que pasa por debajo del vehiculo y mejorando la estabilidad a "
            "alta velocidad. Tambien aporta un acabado deportivo distintivo."
        ),
        "faldon": (
            "Faldon (rocker panel extension): pieza lateral de la defensa que extiende la linea inferior "
            "del vehiculo, dando un perfil mas bajo y agresivo. Cumple funcion estetica y mejora "
            "marginalmente el flujo de aire lateral."
        ),
        "aleron": (
            "Aleron de defensa: pieza aerodinamica que se monta en la defensa para generar carga aerodinamica "
            "(downforce) o redireccionar el flujo de aire. Cumple funcion estetica deportiva y, en "
            "configuraciones M/M Sport/M Performance, complementa el paquete aerodinamico de fabrica."
        ),
        "spoiler": (
            "Spoiler aerodinamico: pieza estetica y funcional que se instala en la carroceria para alterar "
            "el flujo de aire a alta velocidad, reduciendo la sustentacion sobre el eje correspondiente y "
            "mejorando la estabilidad. En modelos M/M Sport/M Performance es elemento clave del kit "
            "estetico de fabrica."
        ),
        "moldura": (
            "Moldura inferior de facia: panel de carroceria que cubre la parte baja de la defensa, "
            "protegiendo el material plastico interno y dando un acabado terminado al frente o trasera del "
            "vehiculo. Es pieza de carroceria estandar en BMW que se daña frecuentemente al rozar topes "
            "o aceras."
        ),
        "componente aerodinamico": (
            "Componente aerodinamico de carroceria que se monta sobre la defensa para mejorar la estetica "
            "y el comportamiento aerodinamico del vehiculo."
        ),
    }
    p1 = descripcion_funcion[tipo]
    if pos:
        p1 = f"{tipo.capitalize()} {pos}. " + p1

    return _ensamblar(
        p, p1=p1,
        rubro=f"{tipo} aerodinamico",
        nombre_base=titulo.replace("&", "").strip().rstrip(),
        shopify_type="Tuning",
        faqs_extra=[
            {
                "pregunta": f"¿Para que sirve el {tipo}?",
                "respuesta": descripcion_funcion[tipo].split(".")[0] + ".",
            },
            {
                "pregunta": "¿Es del lado izquierdo, derecho, o cubre ambos?",
                "respuesta": (
                    "Verifica el listing — algunos componentes son por lado y otros se venden como par o "
                    "pieza unica que cubre el ancho. Si tu titulo no especifica 'L' o 'R', "
                    "envianos tu numero de VIN y te confirmamos."
                ),
            },
            {
                "pregunta": "¿La pieza viene pintada?",
                "respuesta": (
                    "No. La pieza viene en color negro de fabrica (primer o plastico texturizado segun el "
                    "modelo). Si necesitas que coincida con el color de tu vehiculo, debe pintarse en taller "
                    "antes de instalar."
                ),
            },
            {
                "pregunta": "¿Es facil de instalar?",
                "respuesta": (
                    "La instalacion requiere desmontar la defensa o el panel correspondiente y atornillar "
                    "o clipsar la pieza nueva. Recomendamos llevarla a un taller de carroceria para asegurar "
                    "el ajuste y evitar daños a las clips de fijacion."
                ),
            },
        ],
    )


# ---------------------------------------------------------------------------
# Tipo: Moldura cromada (Mini Cooper, parrilla, etc.)
# ---------------------------------------------------------------------------

def build_moldura_cromada(p: dict) -> dict:
    titulo = p["titulo"]
    tlow = titulo.lower()
    if "calavera" in tlow:
        zona = "calavera"
        funcion = (
            "Moldura cromada decorativa de la calavera (luz trasera). Se instala como bisel sobre la luz "
            "de freno trasera para dar un acabado cromado distintivo, signature de la estetica Mini "
            "Cooper de la generacion R56-F56."
        )
    elif "parrilla" in tlow or "parrila" in tlow:
        zona = "parrilla"
        funcion = (
            "Marco cromado de la parrilla delantera. Reemplaza el aro decorativo del frente del vehiculo, "
            "frecuentemente dañado por impactos menores o oxidacion del cromado original."
        )
    else:
        zona = "moldura"
        funcion = (
            "Moldura cromada decorativa. Pieza de acabado estetico para el exterior del vehiculo, "
            "frecuentemente cambiada cuando el cromado original se opaca, raya o se pica."
        )

    p1 = (
        f"{funcion} El cromado se aplica sobre plastico ABS por proceso galvanico, replicando el acabado de "
        "la pieza OEM y manteniendo la durabilidad ante UV y lavado de auto. Su instalacion no requiere "
        "modificaciones — reemplaza la pieza original por clips o tornilleria estandar."
    )

    return _ensamblar(
        p, p1=p1,
        rubro=f"moldura cromada {zona}",
        nombre_base=titulo.replace("&", "").strip().rstrip(),
        shopify_type="Tuning",
        faqs_extra=[
            {
                "pregunta": "¿Es del lado izquierdo o derecho?",
                "respuesta": (
                    "Revisa el titulo — si dice 'piloto' o 'L' es el lado del conductor, 'copiloto' o 'R' "
                    "es el lado del pasajero. Si dice 'par' incluye ambos. Confirma con tu numero de VIN "
                    "ante la duda."
                ),
            },
            {
                "pregunta": "¿El cromado es pintura o galvanizado?",
                "respuesta": (
                    "Es cromado galvanico sobre plastico ABS, el mismo proceso de la pieza OEM. No es "
                    "pintura — resiste UV y lavado sin opacarse."
                ),
            },
            {
                "pregunta": "¿Necesito desarmar mucho para instalarla?",
                "respuesta": (
                    "Para molduras de calavera, normalmente se accede desde el interior de la cajuela "
                    "soltando el guarnecido y los clips de la luz. Para parrilla, se quita la defensa "
                    "delantera. Recomendamos taller de carroceria si no tienes experiencia."
                ),
            },
            {
                "pregunta": "¿Que garantia tiene?",
                "respuesta": "30 dias contra defectos de fabrica.",
            },
        ],
    )


# ---------------------------------------------------------------------------
# Ensamblador comun (parrafos 2-5 + secciones)
# ---------------------------------------------------------------------------

def _ensamblar(p: dict, p1: str, rubro: str, nombre_base: str, shopify_type: str,
               faqs_extra: list) -> dict:
    fila = p["_fila_original"]
    titulo = p["titulo"]
    sku = p["sku"] or "(sin SKU)"
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

    # P2 — aplicacion y compatibilidad
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
            "exactamente a tu version, configuracion y opcionales — algunos modelos comparten plataforma pero "
            "tienen variaciones segun region, paquete de equipamiento o anio de fabricacion."
        )
    else:
        p2 = (
            "La descripcion original del listing menciona modelos compatibles pero no esta estructurada en el "
            "bloque APLICA PARA estandar, por lo que la lista no se pudo extraer automaticamente. "
            f"Por el titulo aplica a vehiculos {tipo_veh.lower() or 'tipo carro/camioneta'} de marcas europeas. "
            "Antes de comprar, envianos tu numero de VIN para que un asesor verifique modelo exacto, anio y "
            "configuracion contra el catalogo del proveedor — un error de compatibilidad genera devolucion y "
            "tiempo perdido en el taller."
        )

    # P3 — especificaciones / referencias
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
            "antes de instalarla; comparalos contra el numero estampado en la pieza original de tu vehiculo "
            "para confirmar que es la correcta."
        )
        if len(nps) > 1 or len(oems_list) > 1:
            p3_extras.append(
                "La presencia de varios numeros de parte indica que el fabricante consolido referencias que "
                "antes se vendian por separado en distintos anios o paquetes; cualquiera de los listados "
                "aplica para la version actual."
            )
    else:
        p3_extras.append(
            "El listing no incluye numero de parte ni codigo OEM publicados. Antes de instalar, recomendamos "
            "comparar visualmente la pieza con la original del vehiculo o consultar con un taller especializado "
            "que tenga acceso al catalogo electronico del fabricante (ETKA para Audi/VW, ETIS para BMW)."
        )
    if p["lado"]:
        p3_extras.append(f"Lado de instalacion: {p['lado']}.")
    if p.get("mc_nombre_match"):
        p3_extras.append(
            f"La referencia interna del catalogo Microsip es: {p['mc_nombre_match'][:80]}, "
            "util para taller que cruza con la red de proveedores."
        )
    p3 = " ".join(p3_extras)

    # P4 — composicion / qué incluye
    if incluye:
        p4 = (
            f"Este producto incluye los siguientes componentes: {incluye}. "
            "El kit se entrega en una sola caja para facilitar la trazabilidad durante la instalacion y "
            "garantizar que todos los elementos provienen del mismo lote de fabricacion."
        )
    else:
        es_par_local = bool(re.search(r"\bpar\b", titulo, re.IGNORECASE))
        es_kit_local = bool(re.search(r"\b(kit|juego|set)\b", titulo, re.IGNORECASE))
        if es_par_local:
            p4 = (
                "Se entrega como par completo, ambos lados (izquierdo y derecho) en la misma caja. "
                "Vender en par es la presentacion estandar para piezas simetricas que se reemplazan al mismo "
                "tiempo (calaveras, focos, espejos, biseles), evitando diferencias de acabado entre el lado "
                "ya cambiado y el opuesto que aun tiene desgaste de uso."
            )
        elif es_kit_local:
            p4 = (
                "Se entrega como kit completo en una sola caja con todos los componentes y la tornilleria de "
                "fijacion correspondiente. La presentacion como kit reduce tiempos de inventario en taller y "
                "asegura que todas las piezas son compatibles entre si y provienen del mismo lote."
            )
        else:
            p4 = (
                "Se vende como pieza individual nueva, en empaque del fabricante. Producto no reciclado ni "
                "remanufacturado. Si tu reparacion requiere reemplazar la pieza tambien en el lado opuesto, "
                "consulta con nuestro asesor para confirmar disponibilidad y, en su caso, descuento por "
                "compra de las dos unidades."
            )

    # P5 — marca y garantia
    pos = marca_posicionamiento(marca_norm, marca_raw)
    gar_dias = "30"
    m = re.search(r"(\d+)\s*d[ií]as?", garantia_raw)
    if m:
        gar_dias = m.group(1)
    p5 = (
        f"{pos} Garantia del vendedor de {gar_dias} dias contra defectos de fabrica. "
        "Embler Autopartes Europeas mantiene stock con entrega inmediata desde Ciudad de Mexico a todo el "
        "pais via DHL y FedEx, ademas de soporte tecnico para verificacion de compatibilidad por VIN antes "
        "del envio. Si despues de recibir la pieza notas que no corresponde a tu vehiculo, aplican nuestras "
        "politicas de devolucion (30 dias, sin uso, en empaque original)."
    )

    descripcion = "\n\n".join([p1, p2, p3, p4, p5])

    # caract_compatibilidad
    caract_compat = caract_compat_pre or (
        f"Compatible con los modelos {', '.join(marcas_veh) or 'mencionados en el titulo'} del listing. "
        "Confirma compatibilidad exacta con tu numero de VIN antes de comprar."
    )

    # FAQs base + extra
    faqs = [
        {
            "pregunta": "¿Como confirmo la compatibilidad con mi vehiculo?",
            "respuesta": (
                "Envianos el numero de serie (VIN) de tu auto y validamos la compatibilidad exacta antes "
                "de procesar el pedido. Tambien puedes mencionar el codigo de motor y el modelo exacto."
            ),
        },
    ] + faqs_extra
    faqs = faqs[:5]

    # Secciones
    es_par = bool(re.search(r"\bpar\b", titulo, re.IGNORECASE))
    es_kit = bool(re.search(r"\b(kit|juego|set)\b", titulo, re.IGNORECASE)) or bool(incluye)
    antes = antes_comprar(numero_parte, oem)
    envio = envio_text(es_kit, es_par)

    # Shopify
    titulo_limpio = title_clean(titulo)
    handle_seed = f"{titulo_limpio}-{sku}-{fila}" if sku and sku != "(sin SKU)" else f"{titulo_limpio}-{fila}"
    handle = slugify(handle_seed)
    tags = ", ".join(marcas_veh) if marcas_veh else _tags_fallback(titulo)
    seo_title_base = (titulo_limpio[:48]).strip()
    seo_title = f"{seo_title_base} | Embler"[:60]
    if seccion_compat_lista:
        primeros = [l.split(" — ")[0] for l in seccion_compat_lista.splitlines()[:3]]
        seo_desc_models = f" Aplica a {', '.join(primeros)}." if primeros else ""
    else:
        seo_desc_models = ""
    seo_desc = (
        f"{rubro.capitalize()} para vehiculos europeos.{seo_desc_models} "
        f"Marca {marca_norm or marca_raw or 'no especificada'}. Envio inmediato a todo Mexico."
    )[:155]
    image_alt = f"{nombre_base[:80]} marca {marca_norm or marca_raw or ''}"[:125]

    body = body_html(descripcion, seccion_compat_lista, antes, envio, faqs)

    relacionados = _relacionados(p, marcas_veh)

    # revision_humana
    revision = []
    if num_compat == 0:
        revision.append(
            "[VERIFICAR] Compatibilidad inferida del titulo — la descripcion no incluye bloque APLICA PARA. "
            "Confirmar modelos y anios."
        )
    if not numero_parte and not oem:
        revision.append("[BUSCAR] Numero de parte o codigo OEM faltantes.")
    if not sku or sku == "(sin SKU)":
        revision.append("[INCLUIR] SKU faltante — asignar antes de publicar.")
    if not marca_norm:
        revision.append("[ANALIZAR] Marca no identificada — confirmar fabricante.")
    revision.append(REVISION_FIJA)
    revision_text = "\n".join(revision)

    return {
        "_fila_original": fila,
        "caract_marca": marca_norm,
        "caract_origen": p["origen"] or "",
        "caract_tipo_vehiculo": tipo_veh,
        "caract_compatibilidad": caract_compat,
        "seccion_descripcion": descripcion,
        "seccion_compatibilidades": seccion_compat_lista,
        "seccion_antes_de_comprar": antes,
        "seccion_envio": envio,
        "seccion_devoluciones": SECCION_DEVOLUCIONES,
        "seccion_faq": faqs,
        "productos_relacionados": relacionados,
        "shopify_handle": handle,
        "shopify_title": titulo_limpio,
        "shopify_body_html": body,
        "shopify_product_category": "Vehicles & Parts > Vehicle Parts & Accessories",
        "shopify_type": shopify_type,
        "shopify_tags": tags,
        "shopify_published": "TRUE",
        "shopify_option1_name": "Title",
        "shopify_option1_value": "Default Title",
        "shopify_variant_sku": sku if sku and sku != "(sin SKU)" else "",
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MARCAS_VALIDAS = ["BMW", "Mercedes-Benz", "Audi", "Volkswagen", "Porsche", "Volvo",
                  "Mini", "Land Rover", "Jaguar", "SEAT", "Smart", "Fiat",
                  "Alfa Romeo", "Bentley", "Rolls-Royce"]


def _tags_fallback(titulo: str) -> str:
    found = []
    t = titulo.upper()
    if "BMW" in t:
        found.append("BMW")
    if "MERCEDES" in t:
        found.append("Mercedes-Benz")
    if "AUDI" in t:
        found.append("Audi")
    if re.search(r"\b(VW|VOLKSWAGEN)\b", t):
        found.append("Volkswagen")
    if "PORSCHE" in t:
        found.append("Porsche")
    if "VOLVO" in t:
        found.append("Volvo")
    if "MINI" in t:
        found.append("Mini")
    if "LAND ROVER" in t:
        found.append("Land Rover")
    if "JAGUAR" in t:
        found.append("Jaguar")
    return ", ".join(found)


def _relacionados(p: dict, marcas_veh: list) -> list:
    """5 SKUs del mismo subcat + marca de vehiculo."""
    sku_actual = p["sku"]
    return []  # se completa post-hoc con index del catalogo si quisieramos


def detectar_tipo_producto(titulo: str, subcat: str) -> str:
    tlow = titulo.lower()
    sub = subcat.lower()
    if any(k in tlow for k in ("foco xenon", "focos xenon", "focos hid", "foco hid", "focos d1", "focos d2", "focos d3", "foco d1", "foco d2", "foco d3")):
        return "foco_xenon"
    if "balastra" in tlow or "modulo" in tlow:
        return "balastra"
    if any(k in tlow for k in ("spoiler", "aleron", "faldon", " lip ", " lip ", "facia", "moldura inferior", "moldura facia", "moldura spoiler")):
        return "cuerpo_aero"
    if "moldura" in tlow and ("cromo" in tlow or "calavera" in tlow or "parrilla" in tlow or "parrila" in tlow or "biseles" in tlow):
        return "moldura_cromada"
    if "ilumin" in sub:
        # caer a foco/balastra segun palabras clave
        if "foco" in tlow:
            return "foco_xenon"
        return "balastra"
    if "tuning exterior" in sub:
        return "cuerpo_aero"
    if "cromad" in sub:
        return "moldura_cromada"
    return "cuerpo_aero"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def construir_resultado(p: dict) -> dict:
    tipo = detectar_tipo_producto(p["titulo"], p.get("subcategoria", ""))
    if tipo == "foco_xenon":
        return build_foco_xenon(p)
    elif tipo == "balastra":
        return build_balastra(p)
    elif tipo == "cuerpo_aero":
        return build_cuerpo_aero(p)
    elif tipo == "moldura_cromada":
        return build_moldura_cromada(p)
    else:
        return build_cuerpo_aero(p)


def main():
    with open(BATCH_PATH, encoding="utf-8") as f:
        data = json.load(f)
    productos = data["productos"]
    resultados = [construir_resultado(p) for p in productos]
    payload = {"resultados": resultados}
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Resultados generados: {len(resultados)} filas -> {OUTPUT_PATH}")
    word_counts = [len(r["seccion_descripcion"].split()) for r in resultados if "seccion_descripcion" in r]
    if word_counts:
        print(f"  Palabras seccion_descripcion: min={min(word_counts)} max={max(word_counts)} avg={sum(word_counts)//len(word_counts)}")
    con_compat = sum(1 for r in resultados if r.get("seccion_compatibilidades", "").strip())
    print(f"  Con seccion_compatibilidades: {con_compat}/{len(resultados)}")
    # Distribucion por tipo
    from collections import Counter
    tipos = Counter(detectar_tipo_producto(p["titulo"], p.get("subcategoria", "")) for p in productos)
    print(f"  Distribucion por tipo: {dict(tipos)}")


if __name__ == "__main__":
    main()
