"""
Construye el JSON de resultados enriquecidos para herramientas (18 filas).
Genera new-output/ml_con_match/herramientas_batch_result.json.
"""

import json
import os

OUTPUT_PATH = "new-output/ml_con_match/herramientas_batch_result.json"

# Secciones fijas reutilizables
SECCION_ENVIO_DEFAULT = (
    "Tenemos stock disponible para entrega inmediata. "
    "Enviamos el mismo dia de tu pago a Ciudad de Mexico y a todo el pais via DHL o FedEx."
)
SECCION_ENVIO_KIT = (
    SECCION_ENVIO_DEFAULT + " Este producto se vende como kit completo."
)
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


def body_html(desc: str, antes: str, envio: str, devoluciones: str, faqs: list) -> str:
    parrafos = "".join(f"<p>{p.strip()}</p>" for p in desc.split("\n\n") if p.strip())
    faq_html = "".join(
        f"<h3>{f['pregunta']}</h3><p>{f['respuesta']}</p>" for f in faqs
    )
    return (
        "<h2>Descripcion</h2>"
        + parrafos
        + "<h2>Antes de Comprar</h2><p>"
        + antes
        + "</p>"
        + "<h2>Envio</h2><p>"
        + envio
        + "</p>"
        + "<h2>Politica de Devolucion</h2>"
        + "".join(f"<p>{p.strip()}</p>" for p in devoluciones.split("\n\n") if p.strip())
        + "<h2>Preguntas Frecuentes</h2>"
        + faq_html
    )


# ---------- Datos especificos por producto -----------------------------------

# Cada entrada: contenido base. Las filas con misma SKU y description vacia
# heredan los textos de su SKU "padre".

PRODUCTOS = {
    # SKU H3ML (filas 0, 7) — Herramienta sincronizacion BMW N52/N54
    "H3ML": {
        "nombre": "Juego de Herramientas de Sincronización para Motores BMW N52/N52N/N53/N54",
        "tags_veh": "BMW",
        "compatibilidad": (
            "Aplica para motores BMW N52, N52N, N53 y N54 de 6 cilindros, 2.5L y 3.0L. "
            "Cubre Serie 1 (125i, 130i, 135i 2006-2012), Serie 3 (325i, 330i, 335i 2006-2012), "
            "Serie 5 (525i, 530i, 535i 2005-2010), Serie 6 (630i 2004-2007), Serie 7 (740i, 740Li 2010-2015), "
            "X1 (25i, 28i 2010-2012), X3 (2.5si, 3.0si 2007-2010), X5 (3.0i/3.0si 2006-2010), "
            "X6 (3.5i 2008-2014) y Z4 (2.5si, 3.0si, 23i, 35i, 35is 2007-2016). "
            "Confirma compatibilidad exacta con tu numero de VIN antes de comprar."
        ),
        "descripcion": (
            "Juego de herramientas de sincronización de motor diseñado especificamente para los motores "
            "BMW N52, N52N, N53 y N54 de 6 cilindros (2.5L y 3.0L). Permite bloquear arboles de levas "
            "y volante motor en posicion de calado para realizar el cambio de cadena de tiempo, juntas "
            "de tapa de valvulas, o reparaciones que requieran preservar la sincronizacion del motor.\n\n"
            "Incluye los útiles necesarios para el procedimiento completo: bloqueador de arboles de levas, "
            "fijador de volante motor y soporte de tensor de cadena. Compatible con la familia de motores "
            "BMW de 6 cilindros en linea instalados en Serie 1, 3, 5, 6, 7, X1, X3, X5, X6 y Z4 de los modelos "
            "2004 a 2016 segun configuracion.\n\n"
            "Producto importado por HT especializado en herramienta de taller para vehiculos europeos. "
            "Garantia de 90 dias contra defectos de fabrica."
        ),
        "shopify_type": "Herramientas",
        "faq_extra": [
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
                    "Incluye los útiles para bloquear arboles de levas, fijar el volante motor y "
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
                "pregunta": "¿Que garantia tiene?",
                "respuesta": "90 dias contra defectos de fabrica.",
            },
            {
                "pregunta": "¿Es de uso profesional?",
                "respuesta": (
                    "Si, esta herramienta esta pensada para mecanico especializado en vehiculos europeos. "
                    "Su uso requiere conocimiento del procedimiento de calado del motor BMW correspondiente."
                ),
            },
        ],
    },

    # SKU DQ1ML (fila 1) — Herramienta sincronizacion BMW 120i N46
    "DQ1ML": {
        "nombre": "Herramienta de Sincronización para BMW 120i Motor N46/N46N (2005-2012)",
        "tags_veh": "BMW",
        "compatibilidad": (
            "Aplica para BMW 120i Basico (2005-2007) con motor N46 4 cilindros 2.0L y BMW 120i Style (2008-2012) "
            "con motor N46N. Confirma compatibilidad exacta con tu numero de VIN antes de comprar."
        ),
        "descripcion": (
            "Herramienta de sincronizacion de cadenas de distribucion para los motores BMW N46 y N46N "
            "instalados en el BMW 120i. Permite mantener la posicion de calado del motor durante el "
            "cambio de cadena de tiempo o reparaciones de cabeza.\n\n"
            "Compatible con BMW 120i Basico 2005-2007 (motor N46, 4 cilindros 2.0L) y BMW 120i Style 2008-2012 "
            "(motor N46N). Diseñada para uso profesional en taller especializado.\n\n"
            "Marca Embler Autopartes Europeas. Garantia de 90 dias contra defectos de fabrica."
        ),
        "shopify_type": "Herramientas",
        "faq_extra": [
            {
                "pregunta": "¿Para que sirve esta herramienta?",
                "respuesta": (
                    "Mantiene calados los arboles de levas y el volante motor durante el cambio de cadena "
                    "de tiempo o cualquier intervencion que requiera desarmar la distribucion del motor N46/N46N."
                ),
            },
            {
                "pregunta": "¿Funciona con el N46N tambien?",
                "respuesta": (
                    "Si. Esta diseñada para los motores N46 (BMW 120i Basico 2005-2007) y N46N (BMW 120i Style 2008-2012)."
                ),
            },
            {
                "pregunta": "¿Que garantia tiene?",
                "respuesta": "90 dias contra defectos de fabrica.",
            },
        ],
    },

    # SKU DP9ML (fila 2) — Doble vanos BMW M52/M54
    "DP9ML": {
        "nombre": "Kit Herramienta de Sincronización Doble Vanos BMW M52/M52TU/M54/M56",
        "tags_veh": "BMW",
        "compatibilidad": (
            "Aplica para motores BMW M52, M52TU, M54 y M56 de 6 cilindros (2.2L, 2.5L, 2.8L y 3.0L). "
            "Cubre E36/E46 323i/325i/328i/330i, E36/7 Z3 2.2/2.5/2.8/3.0, E39 520i/523i/525i/528i/530i, "
            "E60/E61 520i/525i/530i, E38 728i, E83 X3 2.5i/3.0i, E85 Z4 2.2i/2.5i/3.0i y E53 X5 3.0i. "
            "Confirma compatibilidad exacta con tu numero de VIN antes de comprar."
        ),
        "descripcion": (
            "Kit de herramienta de sincronizacion de doble vanos diseñado para los motores BMW M52, M52TU, "
            "M54 y M56 de 6 cilindros. Permite ajustar y bloquear los arboles de levas en posicion correcta "
            "durante el calado del motor, indispensable al cambiar la cadena de tiempo o intervenir el "
            "sistema VANOS variable.\n\n"
            "Cubre la mayoria de los BMW de 6 cilindros producidos entre 1997 y 2006 con motores M52/M54: "
            "E36, E46, E39, E60/E61, E38, Z3, Z4, E83 X3 y E53 X5. Incluye los útiles especificos para "
            "el procedimiento de doble vanos.\n\n"
            "Marca Embler Autopartes Europeas. Garantia de 90 dias contra defectos de fabrica."
        ),
        "shopify_type": "Herramientas",
        "faq_extra": [
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

    # SKU DR5ML (filas 3, 9) — Sincronizacion Audi/VW V6 V10
    "DR5ML": {
        "nombre": "Kit Herramienta de Sincronización Audi/VW V6 y V10",
        "tags_veh": "Audi, Volkswagen",
        "compatibilidad": (
            "Aplica para Audi A4, A6, A8, Q7, R8, RS4, S5, S6, S8 (2005-2009), Volkswagen Jetta (2005-2012) "
            "y Volkswagen Touareg (2007-2009) con motores V6 y V10 5.4L. "
            "Confirma compatibilidad exacta con tu numero de VIN antes de comprar."
        ),
        "descripcion": (
            "Kit de herramienta de sincronizacion de motor diseñado para los motores V6 y V10 de Audi y "
            "Volkswagen. Permite calar arboles de levas y volante motor para el cambio de cadena de tiempo "
            "o reparaciones que requieran mantener la sincronizacion.\n\n"
            "Compatible con la gama Audi A4, A6, A8, Q7, R8, RS4, S5, S6 y S8 producidos entre 2005 y 2009, "
            "ademas de Volkswagen Jetta (2005-2012) y Touareg (2007-2009) con motores V6 y V10 5.4L.\n\n"
            "Marca HT, fabricante especializado en herramienta de taller para vehiculos europeos. "
            "Garantia de 90 dias contra defectos de fabrica."
        ),
        "shopify_type": "Herramientas",
        "faq_extra": [
            {
                "pregunta": "¿Sirve para Audi R8?",
                "respuesta": (
                    "Si, para R8 2008-2009 con motor V10. Confirma compatibilidad con tu numero de VIN."
                ),
            },
            {
                "pregunta": "¿Funciona con motor V6?",
                "respuesta": (
                    "Si. Cubre motores V6 instalados en Audi A4, A6, A8, Q7, S5, S6 y VW Touareg "
                    "del periodo 2005-2009."
                ),
            },
            {
                "pregunta": "¿Que garantia tiene?",
                "respuesta": "90 dias contra defectos de fabrica.",
            },
        ],
    },

    # SKU H25ML (filas 4, 5, 6) — Sincronizacion Audi/VW 1.8/2.0 TFSI
    "H25ML": {
        "nombre": "Juego de Herramientas de Sincronización Audi/VW 1.8 y 2.0 TFSI",
        "tags_veh": "Audi, Volkswagen",
        "compatibilidad": (
            "Aplica para Audi A3, A4, A5, A6, Q5, TT (2012-2015) y Volkswagen Beetle, CC, EOS, GTI, Jetta GLI, "
            "Tiguan (2012-2015) con motor 4 cilindros 2.0L TFSI. Tambien cubre variantes 1.8 TFSI. "
            "Confirma compatibilidad exacta con tu numero de VIN antes de comprar."
        ),
        "descripcion": (
            "Juego de herramientas de sincronizacion de motor especifico para los motores Audi y Volkswagen "
            "de 1.8 y 2.0 litros TFSI (4 cilindros). Permite bloquear arboles de levas y volante motor para "
            "el cambio de cadena de tiempo o reparaciones que requieran mantener la sincronizacion.\n\n"
            "Cubre la gama Audi A3, A4, A5, A6, Q5, TT (2012-2015) y la familia Volkswagen Beetle, CC, EOS, GTI, "
            "Jetta GLI y Tiguan (2012-2015) con motor TFSI. Coincide con el numero de parte interno T&F de "
            "Embler para el motor TFSI Audi/VW/SEAT 1.8/2.0.\n\n"
            "Marca Embler Autopartes Europeas. Garantia de 90 dias contra defectos de fabrica."
        ),
        "shopify_type": "Herramientas",
        "faq_extra": [
            {
                "pregunta": "¿Que motores cubre?",
                "respuesta": (
                    "Motores TFSI 1.8 y 2.0 litros, 4 cilindros, instalados en la gama Audi A3-A6, Q5, TT "
                    "y Volkswagen Beetle, CC, EOS, GTI, Jetta GLI y Tiguan del periodo 2012-2015."
                ),
            },
            {
                "pregunta": "¿Funciona en VW Tiguan 2014?",
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

    # SKU DR6ML (fila 8) — VW Bora 2.5 / Audi 3.2 5.4 V6 V10 (mismo descripcion que DR5ML — herramienta hermana)
    "DR6ML": {
        "nombre": "Herramienta de Sincronización VW Bora 2.5 / Audi 3.2 / V6 / V10",
        "tags_veh": "Audi, Volkswagen",
        "compatibilidad": (
            "Aplica para motores V6 y V10 de Audi y Volkswagen. Cubre Audi A4, A6, A8, Q7, R8, RS4, S5, S6, S8 "
            "(2005-2009), Volkswagen Jetta (2005-2012) y Volkswagen Touareg (2007-2009). "
            "Tambien aplica para Bora 2.5 con motor 5 cilindros. "
            "Confirma compatibilidad exacta con tu numero de VIN antes de comprar."
        ),
        "descripcion": (
            "Herramienta de sincronizacion de motor para los motores 2.5L 5 cilindros del VW Bora y la familia "
            "V6 y V10 de Audi/Volkswagen. Permite calar arboles de levas y volante motor durante el cambio "
            "de cadena de tiempo y reparaciones internas.\n\n"
            "Cubre la gama Audi A4, A6, A8, Q7, R8, RS4, S5, S6, S8 (2005-2009), VW Jetta (2005-2012), "
            "VW Touareg (2007-2009) y VW Bora 2.5 con motor 5 cilindros.\n\n"
            "Marca HT, fabricante especializado en herramienta de taller para vehiculos europeos. "
            "Garantia de 90 dias contra defectos de fabrica."
        ),
        "shopify_type": "Herramientas",
        "faq_extra": [
            {
                "pregunta": "¿Sirve para Bora 2.5?",
                "respuesta": (
                    "Si, esta diseñada para el motor 2.5L 5 cilindros del Volkswagen Bora ademas de la familia V6/V10."
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

    # SKU DQ6ML (filas 10, 11) — BMW N54/N55 motor scroll twin turbo
    "DQ6ML": {
        "nombre": "Juego Herramienta de Sincronización BMW N52/N52N/N54/N55",
        "tags_veh": "BMW",
        "compatibilidad": (
            "Aplica para motores BMW N52, N52N, N54 y N55 de 6 cilindros (2.5L y 3.0L), aspiracion natural, "
            "Bi-Turbo y Scroll Twin Turbo. Cubre BMW Serie 1 (M135i, 135i), Serie 2 (M2, 235i, M235i), "
            "Serie 3 (325i, 330i, 335i, 335Ci), Serie 4 (435i), Serie 5 (525i, 528i, 530i, 535i), "
            "Serie 7 (740i), X1 25i, X3 35i, X4 35i/40i, X5 35i, X6 35i y Z4 (2007-2019). "
            "Confirma compatibilidad exacta con tu numero de VIN antes de comprar."
        ),
        "descripcion": (
            "Juego de herramientas de sincronizacion de cadenas de tiempo diseñado para los motores BMW de "
            "6 cilindros N52, N52N, N54 y N55. Cubre tanto las versiones de aspiracion natural como las "
            "turbo (Bi-Turbo y Scroll Twin Turbo) instaladas en la mayoria de los BMW desde Serie 1 hasta X6.\n\n"
            "Indispensable para el cambio de cadena de tiempo, juntas de tapa de valvulas o cualquier intervencion "
            "que requiera mantener calado el motor. Compatible con BMW M135i, M2, 235i, 325i, 330i, 335i, 435i, "
            "525i a 535i, 740i, X1 25i, X3 35i, X4 35i/40i, X5 35i, X6 35i y Z4 35i/35is del periodo 2007 a 2019.\n\n"
            "Marca Embler Autopartes Europeas. Garantia de 30 dias contra defectos de fabrica."
        ),
        "shopify_type": "Herramientas",
        "faq_extra": [
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
                    "N52/N52N de aspiracion natural."
                ),
            },
            {
                "pregunta": "¿Sirve para X3 35i?",
                "respuesta": "Si, BMW X3 35i 2012-2017 con motor N55 6 cilindros 3.0L Scroll Twin Turbo.",
            },
            {
                "pregunta": "¿Que garantia tiene?",
                "respuesta": "30 dias contra defectos de fabrica.",
            },
        ],
    },

    # SKU HTD1050B+229 (fila 12) — Tiguan 2.0 TFSI especifico
    "HTD1050B+229": {
        "nombre": "Herramientas de Sincronización Volkswagen Tiguan Track and Fun 2013-2015 (2.0 TFSI)",
        "tags_veh": "Volkswagen",
        "compatibilidad": (
            "Aplica para Volkswagen Tiguan Track and Fun Sport Utility 2013-2015 con motor 4 cilindros 2.0L TFSI. "
            "Confirma compatibilidad exacta con tu numero de VIN antes de comprar."
        ),
        "descripcion": (
            "Herramienta de sincronizacion de motor para el Volkswagen Tiguan Track and Fun (2013-2015) con motor "
            "2.0L TFSI 4 cilindros. Permite calar arboles de levas y volante motor durante el cambio de cadena "
            "de tiempo y reparaciones internas.\n\n"
            "Especifica para la version Tiguan Track and Fun Sport Utility, basada en el mismo motor 2.0 TFSI "
            "compartido con otros modelos Audi/VW del periodo 2013-2015.\n\n"
            "Marca HT (referencia interna HTD1050B). Garantia de 90 dias contra defectos de fabrica."
        ),
        "shopify_type": "Herramientas",
        "faq_extra": [
            {
                "pregunta": "¿Solo sirve para Tiguan Track and Fun?",
                "respuesta": (
                    "El producto se publico para esa version, pero el motor 2.0 TFSI es comun en otros modelos. "
                    "Recomendamos verificar con tu numero de VIN si tienes otra version."
                ),
            },
            {
                "pregunta": "¿Que garantia tiene?",
                "respuesta": "90 dias contra defectos de fabrica.",
            },
            {
                "pregunta": "¿Que numero de parte tiene?",
                "respuesta": "Referencia interna HTD1050B.",
            },
        ],
    },

    # SKU EM1ML (fila 13) — BMW N51 N52 N53 N54 (mismo modelo lista que H3ML)
    "EM1ML": {
        "nombre": "Juego de Herramientas de Sincronización BMW N51/N52/N53/N54",
        "tags_veh": "BMW",
        "compatibilidad": (
            "Aplica para motores BMW N51, N52, N52N, N53 y N54 de 6 cilindros (2.5L y 3.0L). "
            "Cubre Serie 1 (125i, 130i, 135i 2006-2012), Serie 3 (325i, 330i, 335i 2006-2012), "
            "Serie 5 (525i, 530i, 535i 2005-2010), Serie 6 (630i 2004-2007), Serie 7 (740i, 740Li 2010-2015), "
            "X1 25i/28i (2010-2012), X3 2.5si/3.0si (2007-2010), X5 3.0i/3.0si (2006-2010), "
            "X6 3.5i (2008-2014) y Z4 2.5si/3.0si/23i/35i/35is (2007-2016). "
            "Confirma compatibilidad exacta con tu numero de VIN antes de comprar."
        ),
        "descripcion": (
            "Juego de herramientas de sincronizacion para la familia de motores BMW de 6 cilindros N51, N52, "
            "N52N, N53 y N54. Permite bloquear arboles de levas y volante motor durante el cambio de cadena "
            "de tiempo, juntas y reparaciones que requieran preservar el calado del motor.\n\n"
            "Cubre la mayoria de los BMW de 6 cilindros producidos entre 2004 y 2016 con motores N5x: "
            "Serie 1, 3, 5, 6, 7, X1, X3, X5, X6 y Z4 segun configuracion y año.\n\n"
            "Marca HT, fabricante especializado en herramienta de taller para vehiculos europeos. "
            "Garantia de 90 dias contra defectos de fabrica."
        ),
        "shopify_type": "Herramientas",
        "faq_extra": [
            {
                "pregunta": "¿Cubre el motor N51?",
                "respuesta": (
                    "Si. Esta version del juego incluye util para los motores N51 ademas de la familia N52/N53/N54."
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

    # SKU DQ3ML (fila 14) — Mercedes M271 1.8L
    "DQ3ML": {
        "nombre": "Herramienta de Sincronización Mercedes-Benz C180 / C200 Kompressor (M271)",
        "tags_veh": "Mercedes-Benz",
        "compatibilidad": (
            "Aplica para Mercedes-Benz C180 (2011-2014) y Mercedes-Benz C200 Kompressor (2011-2014), "
            "ambos con motor M271 4 cilindros 1.8L. "
            "Confirma compatibilidad exacta con tu numero de VIN antes de comprar."
        ),
        "descripcion": (
            "Herramienta de sincronizacion de motor diseñada para el motor Mercedes-Benz M271 de 4 cilindros "
            "1.8 litros con sobrealimentacion Kompressor. Permite calar el motor durante el cambio de cadena "
            "de tiempo o intervenciones que requieran preservar la sincronizacion.\n\n"
            "Compatible con Mercedes-Benz C180 (2011-2014) y C200 Kompressor (2011-2014), ambos con motor M271. "
            "Diseñada para uso profesional en taller especializado en vehiculos europeos.\n\n"
            "Marca HT. Garantia de 90 dias contra defectos de fabrica."
        ),
        "shopify_type": "Herramientas",
        "faq_extra": [
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
                "pregunta": "¿Que garantia tiene?",
                "respuesta": "90 dias contra defectos de fabrica.",
            },
        ],
    },

    # SKU DP7ML (filas 15, 17) — Audi A4 A6 V6 3.0 5V
    "DP7ML": {
        "nombre": "Kit Herramienta de Sincronización Audi A4 / A6 V6 3.0 5V (motores AVK / BBK)",
        "tags_veh": "Audi",
        "compatibilidad": (
            "Aplica para Audi A4 y Audi A6 (2000-2004) con motores 3.0L V6 5V (codigos AVK o BBK). "
            "Confirma compatibilidad exacta con tu numero de VIN antes de comprar."
        ),
        "descripcion": (
            "Kit de 6 piezas para el bloqueo de arboles de levas y la sincronizacion de cadenas de tiempo "
            "del motor Audi V6 3.0L 5V (codigos AVK y BBK). Permite calar el motor durante el cambio de "
            "cadenas de distribucion y reparaciones internas.\n\n"
            "Compatible con Audi A4 y Audi A6 (2000-2004) que monten el motor 3.0L V6 5V. Producto "
            "especifico para taller mecanico especializado en motores Audi.\n\n"
            "Marca Embler Autopartes Europeas. Garantia de 30 dias contra defectos de fabrica."
        ),
        "shopify_type": "Herramientas",
        "faq_extra": [
            {
                "pregunta": "¿Que motores cubre?",
                "respuesta": (
                    "Motores Audi 3.0L V6 5V con codigos AVK o BBK instalados en A4 y A6 del periodo 2000-2004."
                ),
            },
            {
                "pregunta": "¿Sirve para A6 2004?",
                "respuesta": "Si, A6 2000-2004 con motor 3.0L V6 5V (AVK o BBK).",
            },
            {
                "pregunta": "¿Que garantia tiene?",
                "respuesta": "30 dias contra defectos de fabrica.",
            },
        ],
    },

    # SKU H7ML (fila 16) — BMW 120i N46 (variante de DQ1ML)
    "H7ML": {
        "nombre": "Herramienta de Sincronización BMW 120i Motor N46/N46N (2005-2012)",
        "tags_veh": "BMW",
        "compatibilidad": (
            "Aplica para BMW 120i Basico (2005-2007) con motor N46 4 cilindros 2.0L y BMW 120i Style (2008-2012) "
            "con motor N46N 4 cilindros 2.0L. "
            "Confirma compatibilidad exacta con tu numero de VIN antes de comprar."
        ),
        "descripcion": (
            "Herramienta de sincronizacion de cadenas de distribucion para los motores N46 y N46N "
            "del BMW 120i. Mantiene calados arboles de levas y volante motor durante el cambio de cadena "
            "de tiempo o reparaciones de cabeza.\n\n"
            "Compatible con BMW 120i Basico (2005-2007, motor N46) y BMW 120i Style (2008-2012, motor N46N), "
            "ambos de 4 cilindros 2.0L. Diseñada para uso profesional en taller especializado.\n\n"
            "Marca Embler Autopartes Europeas. Garantia de 30 dias contra defectos de fabrica."
        ),
        "shopify_type": "Herramientas",
        "faq_extra": [
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
                    "Si. Cubre tanto el N46 (BMW 120i Basico 2005-2007) como el N46N (120i Style 2008-2012)."
                ),
            },
            {
                "pregunta": "¿Que garantia tiene?",
                "respuesta": "30 dias contra defectos de fabrica.",
            },
        ],
    },
}


# Mapeo fila -> sku usado para resolver duplicados
FILA_A_SKU = {
    0: "H3ML", 1: "DQ1ML", 2: "DP9ML", 3: "DR5ML", 4: "H25ML",
    5: "H25ML", 6: "H25ML", 7: "H3ML", 8: "DR6ML", 9: "DR5ML",
    10: "DQ6ML", 11: "DQ6ML", 12: "HTD1050B+229", 13: "EM1ML",
    14: "DQ3ML", 15: "DP7ML", 16: "H7ML", 17: "DP7ML",
}

# Mapeo fila -> datos especificos de la fila (titulo crudo, marca_norm, sku, precio, etc)
FILA_RAW = {
    0:  {"titulo_raw": "Herramienta Sincronizacion Bmw 125 325 X5 X6 X1 X3 Z4 525 &", "marca": "HT", "sku": "H3ML", "precio": "5689", "garantia_dias": 90, "tipo_veh": ""},
    1:  {"titulo_raw": "Herramieta De Sincronizacion Bmw 120i Basico 2005 Al 2007 H7", "marca": "Embler", "sku": "DQ1ML", "precio": "2469", "garantia_dias": 90, "tipo_veh": "Carro/Camioneta"},
    2:  {"titulo_raw": "Doble Vanos Bmw M52, M52tu, M54, M56 Tiempo Herramienta &", "marca": "Embler", "sku": "DP9ML", "precio": "5719", "garantia_dias": 90, "tipo_veh": ""},
    3:  {"titulo_raw": "Herramienta Sincronizacion Audi A4 Q7 A6 S5 S6 A8 Vw Jetta &", "marca": "HT", "sku": "DR5ML", "precio": "1169", "garantia_dias": 90, "tipo_veh": ""},
    4:  {"titulo_raw": "Herramientas Sincronizacion Audi A3 A4 Q5 A5 A6 Vw Tiguan &", "marca": "Embler", "sku": "H25ML", "precio": "3499", "garantia_dias": 90, "tipo_veh": ""},
    5:  {"titulo_raw": "Herramientas Sincronizacion Audi A3 A4 Q5 A5 A6 Vw Tiguan & Color Azul", "marca": "Embler", "sku": "H25ML", "precio": "3499", "garantia_dias": 90, "tipo_veh": ""},
    6:  {"titulo_raw": "Herramientas Sincronizacion Audi A3 A4 A5 A6 Q5 Tt Vw Bettle", "marca": "Embler", "sku": "H25ML", "precio": "3499", "garantia_dias": 90, "tipo_veh": ""},
    7:  {"titulo_raw": "Set Sincronización Bmw Para Motores N52 / N54 &", "marca": "HT", "sku": "H3ML", "precio": "5689", "garantia_dias": 90, "tipo_veh": ""},
    8:  {"titulo_raw": "Herramienta Sincronizar Vw Bora 2.5 Vw Audi 3.2 5.4 V6 V10 &", "marca": "HT", "sku": "DR6ML", "precio": "1169", "garantia_dias": 90, "tipo_veh": ""},
    9:  {"titulo_raw": "Kit Sincronizar Bora / Vw - 2.5 / Audi - 2.4, 3.2 &", "marca": "HT", "sku": "DR5ML", "precio": "1169", "garantia_dias": 90, "tipo_veh": ""},
    10: {"titulo_raw": "Herramienta Sincronizacion Motor Bmw 135 325 X5 X6 X1 X3 &", "marca": "Embler", "sku": "DQ6ML", "precio": "6499", "garantia_dias": 30, "tipo_veh": ""},
    11: {"titulo_raw": "Herramienta Sincronizacion Motor Bmw 135 325 X5 X6 X1 X3", "marca": "Embler", "sku": "DQ6ML", "precio": "6499", "garantia_dias": 30, "tipo_veh": ""},
    12: {"titulo_raw": "Herramientas Sincronizacion Volkswagen Tiguan Track And Fun Sport Utility 2013-2015 H25", "marca": "HT", "sku": "HTD1050B+229", "precio": "2719", "garantia_dias": 90, "tipo_veh": ""},
    13: {"titulo_raw": "Herramienta Sincronizacion Bmw Motor N51 N52 N53 N54 &", "marca": "HT", "sku": "EM1ML", "precio": "5689", "garantia_dias": 90, "tipo_veh": ""},
    14: {"titulo_raw": "Herramienta Sincronizacion Mercedes C200k C180 2011 - 2014 &", "marca": "HT", "sku": "DQ3ML", "precio": "2299", "garantia_dias": 90, "tipo_veh": ""},
    15: {"titulo_raw": "Herramienta Para Sincronización De Motor Audi 3.0 V6 5v &", "marca": "Embler", "sku": "DP7ML", "precio": "3119", "garantia_dias": 30, "tipo_veh": ""},
    16: {"titulo_raw": "Herramieta De Sincronizacion Bmw 120i 2005 Al 2011 &", "marca": "Embler", "sku": "H7ML", "precio": "2469", "garantia_dias": 30, "tipo_veh": "Carro/Camioneta"},
    17: {"titulo_raw": "Sincronizador De Tiempo Para Audi A4 A6 V6 3.0 Lts &", "marca": "Embler", "sku": "DP7ML", "precio": "3119", "garantia_dias": 30, "tipo_veh": ""},
}


def slugify(text: str) -> str:
    import re, unicodedata
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text


def title_clean(t: str) -> str:
    t = t.replace("&", "").strip()
    # Capitalizar de forma razonable
    return " ".join(w if w.isupper() and len(w) <= 4 else w for w in t.split())


def relacionados_para(sku_actual: str, marca_veh: str) -> list:
    # Hasta 5 SKUs distintos del mismo grupo de marca
    grupos = {
        "BMW": ["H3ML", "DQ1ML", "DP9ML", "DQ6ML", "EM1ML", "H7ML"],
        "Audi": ["DR5ML", "H25ML", "DR6ML", "DP7ML"],
        "Volkswagen": ["DR5ML", "H25ML", "DR6ML", "HTD1050B+229"],
        "Mercedes-Benz": [],
    }
    primary = marca_veh.split(",")[0].strip()
    pool = grupos.get(primary, [])
    return [s for s in pool if s != sku_actual][:5]


def construir_resultado(fila: int) -> dict:
    raw = FILA_RAW[fila]
    sku_grupo = FILA_A_SKU[fila]
    base = PRODUCTOS[sku_grupo]

    titulo_limpio = title_clean(raw["titulo_raw"])
    handle = slugify(f"{base['nombre']}-{raw['sku']}-{fila}")
    marca_veh = base["tags_veh"]

    faqs = [
        {
            "pregunta": "¿Como confirmo la compatibilidad con mi vehiculo?",
            "respuesta": (
                "Envianos el numero de serie (VIN) de tu auto y validamos la compatibilidad exacta antes "
                "de procesar el pedido. Tambien puedes mencionar el codigo de motor de tu vehiculo."
            ),
        },
        {
            "pregunta": "¿Cual es la garantia?",
            "respuesta": f"{raw['garantia_dias']} dias contra defectos de fabrica.",
        },
    ] + base["faq_extra"]
    faqs = faqs[:5]

    descripcion = base["descripcion"]
    antes = antes_comprar("", "")
    envio = SECCION_ENVIO_KIT if "kit" in base["nombre"].lower() or "juego" in base["nombre"].lower() else SECCION_ENVIO_DEFAULT

    body = body_html(descripcion, antes, envio, SECCION_DEVOLUCIONES, faqs)

    seo_title = f"{base['nombre'][:48]} | Embler"[:60]
    seo_desc = (
        f"{base['nombre']}. Marca {raw['marca']}. Envio inmediato a todo Mexico."
    )[:155]

    image_alt = f"{base['nombre']} marca {raw['marca']}"[:125]

    relacionados = relacionados_para(raw["sku"], marca_veh)

    revision = []
    # Sin compatibilidades_ml estructurada — todas las herramientas
    revision.append("[VERIFICAR] Compatibilidad inferida de la descripcion del producto.")
    if not base["faq_extra"]:
        revision.append("[REVISAR] FAQs minimas — agregar mas preguntas especificas si aplica.")
    # Marca HT no en mapeo conocido
    if raw["marca"] == "HT":
        revision.append("[ANALIZAR] Marca 'HT' — confirmar si es el fabricante final o un revendedor.")
    revision.append(REVISION_FIJA)
    revision_text = "\n".join(revision)

    # Detectar duplicados de SKU
    same_sku = [f for f, s in FILA_RAW.items() if s["sku"] == raw["sku"] and f != fila]
    if same_sku:
        revision_text = (
            f"[ANALIZAR] SKU duplicado: tambien presente en filas {same_sku}. Considerar consolidar.\n"
            + revision_text
        )

    return {
        "_fila_original": fila,
        "caract_marca": raw["marca"],
        "caract_origen": "",
        "caract_tipo_vehiculo": raw["tipo_veh"],
        "caract_compatibilidad": base["compatibilidad"],
        "seccion_descripcion": descripcion,
        "seccion_antes_de_comprar": antes,
        "seccion_envio": envio,
        "seccion_devoluciones": SECCION_DEVOLUCIONES,
        "seccion_faq": faqs,
        "productos_relacionados": relacionados,
        "shopify_handle": handle,
        "shopify_title": titulo_limpio,
        "shopify_body_html": body,
        "shopify_product_category": "Vehicles & Parts > Vehicle Parts & Accessories",
        "shopify_type": base["shopify_type"],
        "shopify_tags": marca_veh,
        "shopify_published": "TRUE",
        "shopify_option1_name": "Title",
        "shopify_option1_value": "Default Title",
        "shopify_variant_sku": raw["sku"],
        "shopify_variant_price": raw["precio"],
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
    resultados = [construir_resultado(i) for i in range(18)]
    payload = {"resultados": resultados}
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Resultados generados: {len(resultados)} filas -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
