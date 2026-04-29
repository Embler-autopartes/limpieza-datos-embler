"""
Construye el JSON de resultados enriquecidos para herramientas (18 filas) usando el flujo v2:
  - Lee new-output_v2/ml_con_match/herramientas_batch.json (con campos pre-parseados)
  - Genera descripcion de 5 parrafos profesional (350-550 palabras)
  - Usa seccion_compatibilidades_propuesta cuando esta poblada; fallback al titulo si no
  - body_html incluye el bloque <h2>Compatibilidades</h2><ul> cuando hay datos

Output: new-output_v2/ml_con_match/herramientas_batch_result.json
"""

import json
import os
import re
import unicodedata

HOJA = os.environ.get("EMBLER_HOJA", "ml_con_match")
BATCH_PATH = f"new-output_v2/{HOJA}/herramientas_batch.json"
OUTPUT_PATH = f"new-output_v2/{HOJA}/herramientas_batch_result.json"


# ---------------------------------------------------------------------------
# Secciones fijas y helpers
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
    if numero_parte and oem:
        base += f" Tambien puedes verificar con el numero de parte {numero_parte} o codigo OEM {oem}."
    elif numero_parte:
        base += f" Tambien puedes verificar con el numero de parte {numero_parte}."
    elif oem:
        base += f" Tambien puedes verificar con el codigo OEM {oem}."
    return base


def envio_text(es_kit: bool) -> str:
    base = (
        "Tenemos stock disponible para entrega inmediata. "
        "Enviamos el mismo dia de tu pago a Ciudad de Mexico y a todo el pais via DHL o FedEx."
    )
    if es_kit:
        base += " Este producto se vende como juego completo."
    return base


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:80]


def title_clean(t: str) -> str:
    t = t.replace("&", "").strip().rstrip()
    return t


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
# Contenido por SKU (descripcion 5 parrafos + FAQs especificas)
# ---------------------------------------------------------------------------

CONTENIDO_SKU = {
    "H3ML": {
        "nombre": "Juego de Herramientas de Sincronización para Motores BMW N52 y N54",
        "shopify_type": "Herramientas",
        "tags_veh": "BMW",
        "marca_pos": (
            "Marca HT, fabricante especializado en herramienta de taller para motores europeos. "
            "Calidad profesional, durable y con tolerancias verificadas."
        ),
        "p1": (
            "Juego de herramientas de sincronización de motor diseñado especificamente para los motores "
            "BMW N52 y N54 de seis cilindros en linea (2.5L y 3.0L), incluyendo sus variantes N52N de aspiración "
            "natural y N54 bi-turbo. Su funcion es bloquear los arboles de levas y el volante motor en posicion "
            "de calado durante el cambio de la cadena de tiempo, las juntas de tapa de valvulas o cualquier "
            "intervencion que requiera preservar la sincronizacion del tren de valvulas. Sin estos utiles es "
            "practicamente imposible reinstalar la cadena en su posicion correcta."
        ),
        "p2": (
            "Esta familia de motores N52/N54 fue la columna vertebral de la oferta BMW de seis cilindros entre "
            "2004 y 2016. Aplica directamente a Serie 1 (125i, 130i, 135i), Serie 3 (325i, 330i, 335i), "
            "Serie 5 (525i, 530i, 535i), Serie 6 (630i), Serie 7 (740i, 740Li), X1 25i/28i, X3 2.5si/3.0si, "
            "X5 3.0i/3.0si, X6 3.5i y Z4 2.5si/3.0si/23i/35i/35is. La descripcion del listing concentra los "
            "modelos cubiertos pero no esta estructurada en bloque APLICA PARA — confirma con tu numero de VIN "
            "que el codigo de motor de tu vehiculo sea N52, N52N, N53 o N54 antes de comprar."
        ),
        "p3": (
            "Producto sin numero de parte ni codigo OEM publicados en el listing. La marca de la herramienta es "
            "HT con codigo interno BMW TOOLN54. No aplica un lado de instalacion porque es herramienta, no pieza."
        ),
        "p4": (
            "El juego se entrega como kit en una sola caja con los utiles para bloquear arboles de levas, "
            "fijar el volante motor y sostener el tensor de cadena durante la operacion. Esta composicion "
            "reemplaza el equivalente OEM 119590, 119600 y 119620 utilizado en taller BMW autorizado."
        ),
        "marca_default": True,
        "garantia_dias": 90,
        "faqs": [
            {
                "pregunta": "¿Cómo se que esta herramienta es para mi BMW?",
                "respuesta": (
                    "Verifica que tu motor sea N52, N52N, N53 o N54 (6 cilindros, 2.5 o 3.0 litros). "
                    "Estos motores se instalaron en Serie 1, 3, 5, 6, 7, X1, X3, X5, X6 y Z4 entre 2004 y 2016. "
                    "Confirma con tu numero de VIN antes de comprar."
                ),
            },
            {
                "pregunta": "¿Que incluye el juego?",
                "respuesta": (
                    "Los útiles para bloquear los arboles de levas, fijar el volante motor y "
                    "sostener el tensor de cadena durante el procedimiento de sincronizacion."
                ),
            },
            {
                "pregunta": "¿Sirve para cambiar la cadena de tiempo?",
                "respuesta": (
                    "Si. Permite mantener la sincronizacion del motor al desmontar y reinstalar la cadena, "
                    "evitando que se mueva la posicion de levas y ciguenal."
                ),
            },
            {
                "pregunta": "¿Es de uso profesional?",
                "respuesta": (
                    "Si. El procedimiento de calado del N52/N54 requiere conocimiento del motor BMW y "
                    "se realiza en taller especializado."
                ),
            },
            {
                "pregunta": "¿Qué garantia tiene?",
                "respuesta": "90 dias contra defectos de fabrica.",
            },
        ],
    },
    "DQ1ML": {
        "nombre": "Herramienta de Sincronización BMW 120i Motor N46/N46N (2005-2012)",
        "shopify_type": "Herramientas",
        "tags_veh": "BMW",
        "marca_pos": (
            "Marca Embler, propia de Embler Autopartes Europeas, especializada en refacciones y herramienta "
            "para vehiculos BMW, Mercedes-Benz, Audi y Volkswagen."
        ),
        "p1": (
            "Herramienta de sincronización de cadenas de distribucion para los motores BMW N46 y N46N de "
            "cuatro cilindros 2.0 litros. Su uso permite bloquear arboles de levas y volante motor durante "
            "el cambio de la cadena de tiempo o cualquier reparacion que afecte la sincronizacion del motor. "
            "Sin esta herramienta no es posible reinstalar la cadena con la posicion de calado correcta entre "
            "el ciguenal y los arboles de levas."
        ),
        "p2": (
            "Esta herramienta cubre el BMW 120i en sus dos variantes principales: 120i Basico (2005-2007) "
            "con motor N46 4 cilindros 2.0L, y BMW 120i Style (2008-2012) con motor N46N. La descripcion del "
            "listing detalla los anios cubiertos pero no esta estructurada en bloque APLICA PARA, por lo que "
            "se recomienda confirmar el codigo de motor (N46 o N46N) en la placa del motor con el numero de VIN "
            "antes de comprar. Aplica para vehiculos tipo Carro/Camioneta."
        ),
        "p3": (
            "Producto sin numero de parte ni codigo OEM publicados en el listing. El atributo de modelo "
            "registrado es 'BMW MOTOR N46 N46N'. Es una herramienta, por lo que no aplica un lado de "
            "instalacion."
        ),
        "p4": (
            "Se entrega como kit con los utiles necesarios para el calado del motor N46/N46N: pin de "
            "bloqueo del arbol de levas, fijador del volante motor y soporte del tensor. Reemplaza la "
            "funcion del set OEM BMW 11 9 590, manteniendo la geometria del calado durante la operacion."
        ),
        "marca_default": True,
        "garantia_dias": 90,
        "faqs": [
            {
                "pregunta": "¿Para que sirve esta herramienta?",
                "respuesta": (
                    "Mantiene calados los arboles de levas y el volante motor durante el cambio de cadena "
                    "de tiempo o cualquier intervencion que requiera desarmar la distribucion del N46/N46N."
                ),
            },
            {
                "pregunta": "¿Funciona con el N46N tambien?",
                "respuesta": (
                    "Si. Esta diseñada para los motores N46 (BMW 120i Basico 2005-2007) y N46N "
                    "(BMW 120i Style 2008-2012)."
                ),
            },
            {
                "pregunta": "¿Que garantia tiene?",
                "respuesta": "90 dias contra defectos de fabrica.",
            },
        ],
    },
    "DP9ML": {
        "nombre": "Kit Herramienta de Sincronización Doble Vanos BMW M52/M52TU/M54/M56",
        "shopify_type": "Herramientas",
        "tags_veh": "BMW",
        "marca_pos": (
            "Marca Embler, propia de Embler Autopartes Europeas, especializada en refacciones y herramienta "
            "para vehiculos BMW, Mercedes-Benz, Audi y Volkswagen."
        ),
        "p1": (
            "Kit de herramienta de sincronización para el sistema de doble VANOS (variable valve timing) "
            "de los motores BMW M52, M52TU, M54 y M56. VANOS es el sistema de variacion del arbol de levas "
            "que en estas versiones actua sobre admision y escape simultaneamente; el calado correcto requiere "
            "fijar ambos arboles en posicion antes de soltar la cadena. Esta herramienta provee los utiles "
            "especificos para bloquear cada arbol de levas y el volante motor durante el procedimiento."
        ),
        "p2": (
            "Aplica para la familia M52/M54 instalada entre 1997 y 2006: motores M52TUB25, M54B25, M52TUB28, "
            "M54B22 y M54B30 (2.2L, 2.5L, 2.8L y 3.0L de seis cilindros en linea). Cubre las plataformas E36 "
            "y E46 de Serie 3 (320i a 330i y sus variantes Ci/ti/xi), Serie 5 E39 y E60/E61 (520i a 530i), "
            "Serie 7 E38 (728i), Z3, Z4 (E85 2.2i/2.5i/3.0i), X3 E83 (2.5i/3.0i) y X5 E53 (3.0i). "
            "Confirma compatibilidad exacta con tu numero de VIN antes de comprar."
        ),
        "p3": (
            "Producto sin numero de parte ni codigo OEM publicados. Atributo de modelo registrado: "
            "ST160007 AT2074KAE. Equivalente funcional al set OEM BMW 11 3 240 + 11 9 340 utilizado en "
            "talleres autorizados."
        ),
        "p4": (
            "Se entrega como kit completo en una sola caja: pin de bloqueo del arbol de levas de admision, "
            "pin de bloqueo del arbol de levas de escape, fijador del volante motor y soporte del tensor "
            "de cadena. Es la combinacion minima para ejecutar el procedimiento de doble vanos sin riesgo "
            "de perder la sincronizacion entre arboles."
        ),
        "marca_default": True,
        "garantia_dias": 90,
        "faqs": [
            {
                "pregunta": "¿Que es doble vanos?",
                "respuesta": (
                    "VANOS es el sistema BMW de variacion del arbol de levas. En motores M52TU, M54 y M56 "
                    "actua sobre admision y escape (doble vanos). El kit permite calar ambos arboles simultaneamente."
                ),
            },
            {
                "pregunta": "¿Sirve para mi BMW Z3 / Z4?",
                "respuesta": (
                    "Si tu Z3 o Z4 monta motor M52, M52TU, M54 o M56 (revisar codigo de motor), si. "
                    "Confirma con tu numero de VIN."
                ),
            },
            {
                "pregunta": "¿Es para uso profesional?",
                "respuesta": (
                    "Si. El procedimiento de calado de doble vanos requiere conocimiento del motor BMW "
                    "y debe realizarse en taller especializado."
                ),
            },
            {
                "pregunta": "¿Que garantia tiene?",
                "respuesta": "90 dias contra defectos de fabrica.",
            },
        ],
    },
    "DR5ML": {
        "nombre": "Kit Herramienta de Sincronización Audi/VW V6 y V10",
        "shopify_type": "Herramientas",
        "tags_veh": "Audi, Volkswagen",
        "marca_pos": (
            "Marca HT, fabricante especializado en herramienta de taller para motores europeos. "
            "Calidad profesional con tolerancias verificadas para procedimientos de sincronizacion."
        ),
        "p1": (
            "Kit de herramienta de sincronización para los motores V6 y V10 de la gama Audi y Volkswagen. "
            "Permite bloquear arboles de levas y volante motor durante el cambio de cadena de tiempo "
            "y reparaciones internas que requieran preservar la sincronizacion del tren de valvulas. "
            "Estos motores tienen distribucion por cadena en la parte trasera del bloque, lo que hace "
            "indispensable el uso de utiles de calado para acceder y reinstalar la cadena correctamente."
        ),
        "p2": (
            "El bloque APLICA PARA del listing detalla 11 configuraciones especificas: Audi A4, A6, A8, "
            "Q7, R8, RS4, S5, S6 y S8 (modelos 2005-2009), Volkswagen Jetta (2005-2012) y Volkswagen "
            "Touareg (2007-2009). En particular el R8 monta el V10 5.2 FSI mientras que la familia A4-A8 "
            "y Touareg comparten plataforma V6 3.2 FSI / V8. La lista completa con anios y motorizaciones "
            "esta en la seccion de Compatibilidades de esta ficha."
        ),
        "p3": (
            "Producto sin numero de parte ni codigo OEM publicados. El atributo de modelo es "
            "'AUDI, VOLKSWAGEN HTD1014B', referencia interna del fabricante HT."
        ),
        "p4": (
            "Se entrega como kit en una sola caja: pines de bloqueo del arbol de levas de admision y de "
            "escape, fijador del volante motor y soporte del tensor de cadena. Suficiente para el "
            "procedimiento de calado del motor V6 FSI de Audi/VW; para el V10 del R8 puede requerir "
            "utiles complementarios segun el procedimiento de fabrica."
        ),
        "marca_default": True,
        "garantia_dias": 90,
        "faqs": [
            {
                "pregunta": "¿Sirve para Audi R8?",
                "respuesta": (
                    "Si, para R8 2008-2009 con motor V10. Confirma compatibilidad con tu numero de VIN."
                ),
            },
            {
                "pregunta": "¿Funciona con motor V6 3.2 FSI?",
                "respuesta": (
                    "Si. Cubre los motores V6 instalados en Audi A4, A6, A8, Q7, S5, S6 y VW Touareg "
                    "del periodo 2005-2009."
                ),
            },
            {
                "pregunta": "¿Como confirmo compatibilidad con mi Jetta?",
                "respuesta": (
                    "Aplica para VW Jetta 2005-2012 con motor V6. Verifica el codigo de motor con tu "
                    "numero de VIN — el Jetta 2.5L 5 cilindros usa otra herramienta distinta."
                ),
            },
            {
                "pregunta": "¿Que garantia tiene?",
                "respuesta": "90 dias contra defectos de fabrica.",
            },
        ],
    },
    "H25ML": {
        "nombre": "Juego de Herramientas de Sincronización Audi/VW 1.8 y 2.0 TFSI",
        "shopify_type": "Herramientas",
        "tags_veh": "Audi, Volkswagen",
        "marca_pos": (
            "Marca Embler, propia de Embler Autopartes Europeas, especializada en refacciones y herramienta "
            "para vehiculos BMW, Mercedes-Benz, Audi, Volkswagen, Porsche, Volvo, Mini Cooper y Jaguar."
        ),
        "p1": (
            "Juego de herramientas de sincronización para los motores Audi y Volkswagen de la familia EA888 "
            "TFSI (Turbocharged Fuel Stratified Injection) en cilindradas 1.8L y 2.0L de cuatro cilindros. "
            "Permite bloquear arboles de levas y volante motor durante el cambio de cadena de tiempo, juntas "
            "de tapa de valvulas y reparaciones de la cabeza. La cadena de tiempo del EA888 va en la parte "
            "trasera del bloque y requiere desmontar la transmision o la cabeza segun la version, por lo que "
            "el calado correcto del motor es critico antes de cualquier intervencion."
        ),
        "p2": (
            "Aplica para la gama Audi A3, A4, A5, A6, Q5 y TT (modelos 2012-2015) y la familia Volkswagen "
            "Beetle, CC, EOS, GTI, Jetta GLI y Tiguan (2012-2015) que monten el motor 2.0L TFSI; tambien "
            "cubre variantes 1.8 TFSI. La referencia interna del catalogo Microsip coincide con "
            "HERRAMIENTA SINCRONIZACION CADENAS MOTOR AUDI VW SEAT 1.8 2.0 TFSI (EMBLER) T&F. La descripcion "
            "del listing concentra modelos pero no esta estructurada en bloque APLICA PARA — verifica el "
            "codigo de motor (CDNB, CCZA, CAEB, CBFA, etc.) con tu VIN antes de comprar."
        ),
        "p3": (
            "Producto sin numero de parte ni codigo OEM publicados. La pieza Microsip equivalente es "
            "el SKU interno de Embler (T&F). Es una herramienta, no aplica un lado de instalacion."
        ),
        "p4": (
            "Se entrega como kit en una sola caja con los utiles para bloquear arboles de levas, fijar el "
            "volante motor y sostener el tensor de cadena. Reemplaza la funcion del set OEM Audi/VW T40133 "
            "y T10340 utilizado por el taller autorizado durante el procedimiento de calado del EA888."
        ),
        "marca_default": True,
        "garantia_dias": 90,
        "faqs": [
            {
                "pregunta": "¿Que motores cubre?",
                "respuesta": (
                    "Motores TFSI 1.8 y 2.0 litros, 4 cilindros, instalados en la gama Audi A3-A6, Q5, TT "
                    "y Volkswagen Beetle, CC, EOS, GTI, Jetta GLI y Tiguan del periodo 2012-2015."
                ),
            },
            {
                "pregunta": "¿Funciona en VW Tiguan?",
                "respuesta": "Si, cubre Tiguan 2013-2015 con motor 2.0L TFSI.",
            },
            {
                "pregunta": "¿Sirve para Audi Q5?",
                "respuesta": "Si, Audi Q5 2013-2015 con motor 2.0L TFSI.",
            },
            {
                "pregunta": "¿Que garantia tiene?",
                "respuesta": "90 dias contra defectos de fabrica.",
            },
        ],
    },
    "DR6ML": {
        "nombre": "Herramienta de Sincronización VW Bora 2.5 / Audi V6 y V10",
        "shopify_type": "Herramientas",
        "tags_veh": "Audi, Volkswagen",
        "marca_pos": (
            "Marca HT, fabricante especializado en herramienta de taller para motores europeos. "
            "Calidad profesional con tolerancias verificadas para procedimientos de sincronizacion."
        ),
        "p1": (
            "Herramienta de sincronización de motor para los motores V6 y V10 de Audi y Volkswagen, "
            "incluyendo el motor 2.5L de cinco cilindros del VW Bora. Permite bloquear arboles de levas y "
            "volante motor durante el cambio de la cadena de tiempo y reparaciones internas. Estos motores "
            "tienen distribucion por cadena en la parte trasera del bloque, asi que un calado incorrecto "
            "implica desmontar nuevamente caja o cabeza para corregir."
        ),
        "p2": (
            "El bloque APLICA PARA cubre 11 configuraciones de la familia Audi/VW: Audi A4, A6, A8, Q7, R8, "
            "RS4, S5, S6 y S8 (2005-2009), VW Jetta (2005-2012) y VW Touareg (2007-2009). Adicionalmente "
            "aplica al VW Bora 2.5 con motor 5 cilindros 2.5L. La lista completa con anios y motorizaciones "
            "esta en la seccion de Compatibilidades de esta ficha."
        ),
        "p3": (
            "Producto sin numero de parte ni codigo OEM publicados. El atributo de modelo es "
            "'AUDI, VOLKSWAGEN HTD1014B' (referencia interna del fabricante HT)."
        ),
        "p4": (
            "Se entrega como kit en una sola caja: pines de bloqueo del arbol de levas, fijador del volante "
            "motor y soporte del tensor de cadena. Suficiente para el procedimiento de calado del V6 FSI y "
            "del 2.5L 5 cilindros."
        ),
        "marca_default": True,
        "garantia_dias": 90,
        "faqs": [
            {
                "pregunta": "¿Sirve para Bora 2.5?",
                "respuesta": (
                    "Si, esta diseñada para el motor 2.5L 5 cilindros del Volkswagen Bora ademas de la "
                    "familia V6/V10."
                ),
            },
            {
                "pregunta": "¿Funciona con Audi R8?",
                "respuesta": "Si, R8 2008-2009 con motor V10.",
            },
            {
                "pregunta": "¿Que garantia tiene?",
                "respuesta": "90 dias contra defectos de fabrica.",
            },
        ],
    },
    "DQ6ML": {
        "nombre": "Juego Herramienta de Sincronización BMW N52/N52N/N54/N55 (Aspiración Natural y Turbo)",
        "shopify_type": "Herramientas",
        "tags_veh": "BMW",
        "marca_pos": (
            "Marca Embler, propia de Embler Autopartes Europeas, especializada en refacciones y herramienta "
            "para vehiculos BMW, Mercedes-Benz, Audi y Volkswagen. Equivalente funcional al set OEM BMW "
            "utilizado en taller autorizado."
        ),
        "p1": (
            "Juego de herramientas de sincronización de cadenas de tiempo para los motores BMW de seis "
            "cilindros en linea de la familia N52, N52N, N54 y N55. Cubre tanto las versiones de aspiración "
            "natural como las turbo (Bi-Turbo y Scroll Twin Turbo) instaladas en la mayoria de los BMW desde "
            "Serie 1 hasta X6. Permite bloquear arboles de levas y volante motor durante el cambio de cadena "
            "de tiempo, juntas de tapa de valvulas o cualquier intervencion que requiera mantener calado el "
            "motor."
        ),
        "p2": (
            "El bloque APLICA PARA del listing detalla 106 configuraciones especificas, agrupadas en BMW "
            "Serie 1 (M135i, 135i, M2 Coupe), Serie 2 (235i, M2, M235i Sport), Serie 3 (325i, 330i, 335i, "
            "335Ci), Serie 4 (435i Cabrio/Gran Coupe/M Sport), Serie 5 (525i, 528i, 530i, 535i), Serie 7 "
            "(740i), X1 25i, X3 35i, X4 35i/40i, X5 35i, X6 35i y Z4 35i/35is, en versiones aspiración "
            "natural, Bi-Turbo y Scroll Twin Turbo del periodo 2007 a 2019. La lista completa con anios y "
            "motorizaciones esta en la seccion de Compatibilidades."
        ),
        "p3": (
            "Producto sin numero de parte ni codigo OEM publicados en el listing. La referencia Microsip "
            "equivalente es HERRAMIENTA SINCRONIZACION CADENAS TIEMPO MOTOR BMW N52 N52N N54 N55 (EMBLER) "
            "T&F. Es una herramienta, no aplica un lado de instalacion."
        ),
        "p4": (
            "Se entrega como kit completo en una sola caja con los utiles para bloquear arboles de levas, "
            "fijar el volante motor y sostener el tensor de cadena durante la operacion. Esta composicion "
            "reemplaza la funcion del set OEM BMW 119590, 119600 y 119620 + utiles para N55 (turbo)."
        ),
        "marca_default": True,
        "garantia_dias": 30,
        "faqs": [
            {
                "pregunta": "¿Sirve para BMW M2?",
                "respuesta": (
                    "Si, BMW M2 2017-2019 con motor N55 6 cilindros 3.0L Scroll Twin Turbo."
                ),
            },
            {
                "pregunta": "¿Funciona con motor N54 Bi-Turbo?",
                "respuesta": (
                    "Si. Cubre las versiones N54 Bi-Turbo y N55 Scroll Twin Turbo, ademas de la familia "
                    "N52/N52N de aspiración natural."
                ),
            },
            {
                "pregunta": "¿Sirve para X3 35i?",
                "respuesta": (
                    "Si, BMW X3 35i 2012-2017 con motor N55 6 cilindros 3.0L Scroll Twin Turbo."
                ),
            },
            {
                "pregunta": "¿Como confirmo compatibilidad con tantas configuraciones?",
                "respuesta": (
                    "Revisa la seccion de Compatibilidades de esta ficha — incluye 106 configuraciones "
                    "con anio y motorizacion exactos. Si tu vehiculo no aparece, envianos tu VIN y "
                    "confirmamos."
                ),
            },
            {
                "pregunta": "¿Que garantia tiene?",
                "respuesta": "30 dias contra defectos de fabrica.",
            },
        ],
    },
    "HTD1050B+229": {
        "nombre": "Herramientas de Sincronización Volkswagen Tiguan Track and Fun (2.0 TFSI)",
        "shopify_type": "Herramientas",
        "tags_veh": "Volkswagen",
        "marca_pos": (
            "Marca HT, fabricante especializado en herramienta de taller para motores europeos. "
            "Referencia interna HTD1050B."
        ),
        "p1": (
            "Herramienta de sincronización de motor para el Volkswagen Tiguan Track and Fun (2013-2015) "
            "con motor 2.0L TFSI de cuatro cilindros (familia EA888). Permite bloquear arboles de levas y "
            "volante motor durante el cambio de cadena de tiempo y reparaciones internas. La cadena del "
            "EA888 esta en la parte trasera del bloque, lo que hace indispensable el calado correcto del "
            "motor para reinstalar la cadena en posicion."
        ),
        "p2": (
            "Aplica especificamente para Volkswagen Tiguan Track and Fun Sport Utility 2013-2015 con motor "
            "4 cilindros 2.0L TFSI. El motor 2.0 TFSI es comun a otras versiones del Tiguan y a la gama "
            "Audi/VW del mismo periodo, por lo que recomendamos verificar con el numero de VIN si se "
            "necesita para otra version. La descripcion del listing concentra los anios cubiertos pero no "
            "trae bloque APLICA PARA estructurado."
        ),
        "p3": (
            "El numero de parte interno publicado es HTD1050B+229. Sin codigo OEM disponible."
        ),
        "p4": (
            "Se entrega como kit con los utiles para bloquear arboles de levas, fijar el volante motor y "
            "sostener el tensor de cadena. Es la combinacion minima para el procedimiento de calado del "
            "EA888 2.0 TFSI."
        ),
        "marca_default": True,
        "garantia_dias": 90,
        "faqs": [
            {
                "pregunta": "¿Solo sirve para Tiguan Track and Fun?",
                "respuesta": (
                    "El producto se publico para esa version, pero el motor 2.0 TFSI es comun en otros "
                    "modelos. Recomendamos verificar con tu numero de VIN si tienes otra version."
                ),
            },
            {
                "pregunta": "¿Que garantia tiene?",
                "respuesta": "90 dias contra defectos de fabrica.",
            },
            {
                "pregunta": "¿Que numero de parte tiene?",
                "respuesta": "Referencia interna HTD1050B+229.",
            },
        ],
    },
    "EM1ML": {
        "nombre": "Juego de Herramientas de Sincronización BMW N51/N52/N53/N54",
        "shopify_type": "Herramientas",
        "tags_veh": "BMW",
        "marca_pos": (
            "Marca HT, fabricante especializado en herramienta de taller para motores europeos. "
            "Calidad profesional con tolerancias verificadas."
        ),
        "p1": (
            "Juego de herramientas de sincronización para la familia completa de motores BMW de seis "
            "cilindros N51, N52, N52N, N53 y N54. Cubre desde el N51 (especifico para mercados con "
            "regulacion de emisiones SULEV en Estados Unidos), hasta el N54 Bi-Turbo de alto rendimiento. "
            "Permite bloquear arboles de levas y volante motor durante el cambio de cadena de tiempo o "
            "reparaciones internas que requieran mantener la sincronizacion del motor."
        ),
        "p2": (
            "Aplica para la mayoria de los BMW de seis cilindros producidos entre 2004 y 2016: Serie 1 "
            "(125i, 130i, 135i), Serie 3 (325i, 330i, 335i), Serie 5 (525i, 530i, 535i), Serie 6 (630i), "
            "Serie 7 (740i, 740Li), X1 25i/28i, X3 2.5si/3.0si, X5 3.0i/3.0si, X6 3.5i y Z4 (2.5si, 3.0si, "
            "23i, 35i, 35is). La descripcion del listing detalla los modelos cubiertos pero no esta "
            "estructurada en bloque APLICA PARA — confirma el codigo de motor con tu VIN antes de comprar."
        ),
        "p3": (
            "Producto sin numero de parte ni codigo OEM publicados. El atributo de modelo registrado es "
            "'BMW TOOLN54'. Es una herramienta, no aplica un lado de instalacion."
        ),
        "p4": (
            "Se entrega como kit en una sola caja con los utiles para bloquear arboles de levas, fijar el "
            "volante motor y sostener el tensor de cadena. Esta version del juego incluye util adicional "
            "compatible con el N51 (mercado norteamericano SULEV) ademas del estandar N52/N53/N54."
        ),
        "marca_default": True,
        "garantia_dias": 90,
        "faqs": [
            {
                "pregunta": "¿Cubre el motor N51?",
                "respuesta": (
                    "Si. Esta version del juego incluye util para los motores N51 ademas de la familia "
                    "N52/N53/N54."
                ),
            },
            {
                "pregunta": "¿Funciona con BMW Z4 35is?",
                "respuesta": "Si, Z4 35is M Sport 2014-2016 con motor N54 6 cilindros 3.0L.",
            },
            {
                "pregunta": "¿Que garantia tiene?",
                "respuesta": "90 dias contra defectos de fabrica.",
            },
        ],
    },
    "DQ3ML": {
        "nombre": "Herramienta de Sincronización Mercedes-Benz C180 / C200 Kompressor (Motor M271)",
        "shopify_type": "Herramientas",
        "tags_veh": "Mercedes-Benz",
        "marca_pos": (
            "Marca HT, fabricante especializado en herramienta de taller para motores europeos. "
            "Calidad profesional con tolerancias verificadas para el procedimiento de calado del M271."
        ),
        "p1": (
            "Herramienta de sincronización de motor diseñada especificamente para el motor Mercedes-Benz "
            "M271 de cuatro cilindros 1.8 litros con sobrealimentacion Kompressor (compresor mecanico). "
            "Permite bloquear arboles de levas y volante motor durante el cambio de cadena de tiempo o "
            "intervenciones que requieran preservar la sincronizacion del motor. El M271 tiene un "
            "procedimiento de calado especifico distinto de los M271 EVO posteriores con turbo."
        ),
        "p2": (
            "Aplica para Mercedes-Benz C180 (2011-2014) y Mercedes-Benz C200 Kompressor (2011-2014), ambos "
            "con motor M271 1.8L Kompressor. La descripcion del listing detalla anios cubiertos pero no "
            "esta estructurada en bloque APLICA PARA. Confirma el codigo de motor exacto con tu numero de "
            "VIN: las versiones M271 EVO posteriores (con turbo en lugar de Kompressor) no son "
            "compatibles con esta herramienta."
        ),
        "p3": (
            "Producto sin numero de parte ni codigo OEM publicados. El atributo de modelo registrado es "
            "'MERCEDES'. Es una herramienta, no aplica un lado de instalacion."
        ),
        "p4": (
            "Se entrega como kit en una sola caja con los utiles para bloquear el arbol de levas, fijar "
            "el volante motor y sostener el tensor de cadena. Reemplaza la funcion del set OEM Mercedes "
            "para el procedimiento de calado del M271."
        ),
        "marca_default": True,
        "garantia_dias": 90,
        "faqs": [
            {
                "pregunta": "¿Sirve para Mercedes C200 Kompressor?",
                "respuesta": (
                    "Si, especificamente para la version 2011-2014 con motor M271 1.8L Kompressor."
                ),
            },
            {
                "pregunta": "¿Funciona en C180 sin Kompressor?",
                "respuesta": (
                    "Si, ambos C180 y C200 Kompressor del periodo 2011-2014 montan el mismo motor M271."
                ),
            },
            {
                "pregunta": "¿Sirve para C200 EVO con turbo?",
                "respuesta": (
                    "No directamente. Las versiones M271 EVO con turbo (2013+) tienen un procedimiento "
                    "de calado distinto y requieren herramienta diferente."
                ),
            },
            {
                "pregunta": "¿Que garantia tiene?",
                "respuesta": "90 dias contra defectos de fabrica.",
            },
        ],
    },
    "DP7ML": {
        "nombre": "Kit Herramienta de Sincronización Audi A4 / A6 V6 3.0 5V (Motores AVK / BBK)",
        "shopify_type": "Herramientas",
        "tags_veh": "Audi",
        "marca_pos": (
            "Marca Embler, propia de Embler Autopartes Europeas, especializada en refacciones y "
            "herramienta para vehiculos BMW, Mercedes-Benz, Audi y Volkswagen."
        ),
        "p1": (
            "Kit de seis piezas para el bloqueo de arboles de levas y la sincronización de cadenas de "
            "tiempo del motor Audi V6 3.0L 5V (cinco valvulas por cilindro), codigos AVK y BBK. Esta "
            "generacion del V6 Audi tiene un sistema de cadenas relativamente complejo con tres cadenas "
            "(principal, intermedia y de los arboles), lo que hace indispensable un kit completo de "
            "calado para no perder la sincronizacion durante reparaciones."
        ),
        "p2": (
            "Aplica para Audi A4 y Audi A6 (2000-2004) con motores 3.0L V6 5V (codigos AVK o BBK). El "
            "AVK fue la version posterior que reemplazo al BBK con mejoras de OBD-II. La descripcion del "
            "listing concentra los anios cubiertos pero no esta estructurada en bloque APLICA PARA — "
            "verifica el codigo de motor exacto en la placa del motor con tu numero de VIN antes de "
            "comprar."
        ),
        "p3": (
            "Producto sin numero de parte ni codigo OEM publicados. El atributo de modelo es 'AUDI'. La "
            "referencia Microsip equivalente es KIT 6 PZ. HERRAMIENTA BLOQUEO ARBOLES LEVAS "
            "SINCRONIZACION CADENAS AUDI WV 3.0 L."
        ),
        "p4": (
            "Se entrega como kit completo de 6 piezas: pines de bloqueo de arboles de levas (admision y "
            "escape, ambas bancadas), fijador del volante motor, soporte del tensor principal y "
            "soporte del tensor intermedio. Suficiente para el procedimiento de calado del V6 3.0 5V."
        ),
        "marca_default": True,
        "garantia_dias": 30,
        "faqs": [
            {
                "pregunta": "¿Que motores cubre?",
                "respuesta": (
                    "Motores Audi 3.0L V6 5V con codigos AVK o BBK instalados en A4 y A6 del periodo "
                    "2000-2004."
                ),
            },
            {
                "pregunta": "¿Sirve para A6 2004?",
                "respuesta": "Si, A6 2000-2004 con motor 3.0L V6 5V (AVK o BBK).",
            },
            {
                "pregunta": "¿Cuantas piezas trae el kit?",
                "respuesta": "Seis piezas, suficientes para el procedimiento completo de calado del motor V6 3.0L.",
            },
            {
                "pregunta": "¿Que garantia tiene?",
                "respuesta": "30 dias contra defectos de fabrica.",
            },
        ],
    },
    "H7ML": {
        "nombre": "Herramienta de Sincronización BMW 120i Motor N46/N46N (2005-2012)",
        "shopify_type": "Herramientas",
        "tags_veh": "BMW",
        "marca_pos": (
            "Marca Embler, propia de Embler Autopartes Europeas, especializada en refacciones y "
            "herramienta para vehiculos BMW, Mercedes-Benz, Audi y Volkswagen."
        ),
        "p1": (
            "Herramienta de sincronización de cadenas de distribucion para los motores BMW N46 y N46N "
            "instalados en el BMW 120i. Permite bloquear arboles de levas y volante motor durante el "
            "cambio de la cadena de tiempo o reparaciones de la cabeza. Sin esta herramienta es "
            "practicamente imposible reinstalar la cadena con el calado correcto entre el ciguenal y los "
            "arboles de levas."
        ),
        "p2": (
            "Aplica para BMW 120i Basico (2005-2007) con motor N46 4 cilindros 2.0L y BMW 120i Style "
            "(2008-2012) con motor N46N. La descripcion del listing detalla los anios cubiertos pero no "
            "esta estructurada en bloque APLICA PARA — confirma el codigo de motor (N46 o N46N) con tu "
            "numero de VIN antes de comprar. Aplica para vehiculos tipo Carro/Camioneta."
        ),
        "p3": (
            "Producto sin numero de parte ni codigo OEM publicados. El atributo de modelo es "
            "'BMW MOTOR N46 N46N'. La referencia Microsip equivalente es HERRAMIENTA SINCRONIZACION "
            "CADENAS MOTOR BMW MOTOR N46 N46N (EMBLER) T&F."
        ),
        "p4": (
            "Se entrega como kit con los utiles necesarios para el calado del motor N46/N46N: pin de "
            "bloqueo del arbol de levas, fijador del volante motor y soporte del tensor."
        ),
        "marca_default": True,
        "garantia_dias": 30,
        "faqs": [
            {
                "pregunta": "¿Para que sirve esta herramienta?",
                "respuesta": (
                    "Mantiene calado el motor N46/N46N durante el cambio de cadena de tiempo o cualquier "
                    "intervencion que requiera desarmar la distribucion."
                ),
            },
            {
                "pregunta": "¿Funciona con motor N46N?",
                "respuesta": (
                    "Si. Cubre tanto el N46 (BMW 120i Basico 2005-2007) como el N46N (120i Style "
                    "2008-2012)."
                ),
            },
            {
                "pregunta": "¿Que garantia tiene?",
                "respuesta": "30 dias contra defectos de fabrica.",
            },
        ],
    },
}


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def relacionados_para(sku_actual: str, marca_veh: str) -> list:
    grupos = {
        "BMW": ["H3ML", "DQ1ML", "DP9ML", "DQ6ML", "EM1ML", "H7ML"],
        "Audi": ["DR5ML", "H25ML", "DR6ML", "DP7ML"],
        "Volkswagen": ["DR5ML", "H25ML", "DR6ML", "HTD1050B+229"],
        "Mercedes-Benz": [],
    }
    primary = marca_veh.split(",")[0].strip()
    pool = grupos.get(primary, [])
    return [s for s in pool if s != sku_actual][:5]


def construir_resultado(producto: dict, todos: list) -> dict:
    sku = producto["sku"]
    contenido = CONTENIDO_SKU.get(sku)
    if not contenido:
        return _resultado_fallback(producto)

    fila = producto["_fila_original"]
    titulo_raw = producto["titulo"]
    precio = producto["precio"]
    numero_parte = producto["numero_parte"]
    oem = producto["codigo_oem"]
    garantia_raw = producto["garantia"]
    tipo_veh = producto["tipo_vehiculo"]
    marca_norm = producto["marca_normalizada"]
    marca_raw = producto["marca"]
    incluye = producto["incluye_texto"]
    seccion_compat_lista = producto["seccion_compatibilidades_propuesta"]
    caract_compat_pre = producto["caract_compatibilidad_propuesta"]
    num_compat = producto["num_compatibilidades"]

    # Construir descripcion 5 parrafos
    p1 = contenido["p1"]
    p2 = contenido["p2"]
    p3 = contenido["p3"]
    if incluye:
        p4 = f"Este juego incluye: {incluye}."
    else:
        p4 = contenido["p4"]
    p5 = f"{contenido['marca_pos']} Garantia de {contenido['garantia_dias']} dias contra defectos de fabrica."
    descripcion = "\n\n".join([p1, p2, p3, p4, p5])

    # caract_compatibilidad: usar pre-parseada si existe, sino fallback al titulo
    if caract_compat_pre:
        caract_compat = caract_compat_pre
    else:
        # Fallback: extraer modelos del titulo
        caract_compat = (
            f"Compatible con los modelos {contenido['tags_veh']} mencionados en el titulo. "
            "Confirma compatibilidad exacta con tu numero de VIN antes de comprar."
        )

    # FAQs
    faqs_base = [
        {
            "pregunta": "¿Como confirmo la compatibilidad con mi vehiculo?",
            "respuesta": (
                "Envianos el numero de serie (VIN) de tu auto y validamos la compatibilidad exacta "
                "antes de procesar el pedido. Tambien puedes mencionar el codigo de motor."
            ),
        },
    ]
    faqs = (faqs_base + contenido["faqs"])[:5]

    # Secciones
    es_kit = bool(re.search(r"\b(juego|kit|set|par)\b", titulo_raw, re.IGNORECASE)) or bool(incluye)
    antes = antes_comprar(numero_parte, oem)
    envio = envio_text(es_kit)

    # Shopify
    titulo_limpio = title_clean(titulo_raw)
    handle = slugify(f"{contenido['nombre']}-{sku}-{fila}")
    seo_title = f"{contenido['nombre'][:48]} | Embler"[:60]
    seo_desc_base = f"{contenido['nombre']}. Marca {marca_raw}."
    if seccion_compat_lista:
        primeros = [l.split(" — ")[0] for l in seccion_compat_lista.splitlines()[:3]]
        if primeros:
            seo_desc_base += f" Aplica a {', '.join(primeros)}."
    seo_desc = (seo_desc_base + " Envio inmediato a todo Mexico.")[:155]
    image_alt = f"{contenido['nombre']} marca {marca_raw}"[:125]

    body = body_html(descripcion, seccion_compat_lista, antes, envio, faqs)

    relacionados = relacionados_para(sku, contenido["tags_veh"])

    # revision_humana
    revision = []
    if num_compat == 0:
        revision.append(
            "[VERIFICAR] Compatibilidad inferida del titulo y nombre tecnico — la descripcion no incluye "
            "bloque APLICA PARA. Confirmar modelos y anios."
        )
    if not numero_parte and not oem:
        revision.append("[BUSCAR] Numero de parte o codigo OEM faltantes.")
    if marca_raw == "HT":
        revision.append("[ANALIZAR] Marca 'HT' — confirmar si es fabricante final o revendedor.")
    # SKU duplicado
    same_sku = [t["_fila_original"] for t in todos if t["sku"] == sku and t["_fila_original"] != fila]
    if same_sku:
        revision.append(
            f"[ANALIZAR] SKU duplicado: tambien presente en filas {same_sku}. Considerar consolidar en Shopify."
        )
    revision.append(REVISION_FIJA)
    revision_text = "\n".join(revision)

    return {
        "_fila_original": fila,
        "caract_marca": marca_norm,
        "caract_origen": producto["origen"] or "",
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
        "shopify_type": contenido["shopify_type"],
        "shopify_tags": contenido["tags_veh"],
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


def _resultado_fallback(producto: dict) -> dict:
    """Para SKUs sin contenido predefinido."""
    return {
        "_fila_original": producto["_fila_original"],
        "caract_marca": producto["marca_normalizada"],
        "revision_humana": "[REVISAR] SKU sin plantilla de contenido — generar manualmente.",
    }


def main():
    with open(BATCH_PATH, encoding="utf-8") as f:
        data = json.load(f)
    productos = data["productos"]
    resultados = [construir_resultado(p, productos) for p in productos]
    payload = {"resultados": resultados}
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Resultados generados: {len(resultados)} filas -> {OUTPUT_PATH}")
    # Stats
    word_counts = []
    for r in resultados:
        if "seccion_descripcion" in r:
            word_counts.append(len(r["seccion_descripcion"].split()))
    if word_counts:
        print(f"  Palabras en seccion_descripcion: min={min(word_counts)} max={max(word_counts)} avg={sum(word_counts)//len(word_counts)}")
    con_compat_lista = sum(
        1 for r in resultados if r.get("seccion_compatibilidades", "").strip()
    )
    print(f"  Con seccion_compatibilidades poblada: {con_compat_lista}/{len(resultados)}")


if __name__ == "__main__":
    main()
