"""
Construye el JSON de resultados enriquecidos para `otros` (73 filas).

`otros` es un cajon de sastre con tres grupos distintos:
  - llaveros (~40): merchandising de marca, no autopartes — usan template propio.
  - refacciones mal clasificadas (~22): autopartes reales sin descripcion fuente; se enriquecen
    con best-effort desde el titulo y se flaggean para reclasificar a refacciones_*.
  - spam crypto mining (~7): listings que son nombres de personas o entradas no-autoparte;
    se generan con CRITICAL flag para eliminar manualmente.
"""

import json
import os
import re
import unicodedata
from collections import Counter

HOJA = os.environ.get("EMBLER_HOJA", "ml_con_match")
BATCH_PATH = f"new-output_v2/{HOJA}/otros_batch.json"
OUTPUT_PATH = f"new-output_v2/{HOJA}/otros_batch_result.json"


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


def body_html(desc: str, compat_lista: str, antes: str, envio: str, faqs: list) -> str:
    parrafos = "".join(
        f"<p>{p.strip()}</p>" for p in desc.split("\n\n") if p.strip()
    )
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
        "<h2>Descripcion</h2>" + parrafos
        + compat_html
        + "<h2>Antes de Comprar</h2><p>" + antes + "</p>"
        + "<h2>Envio</h2><p>" + envio + "</p>"
        + devs_html
        + faq_html
    )


# ---------------------------------------------------------------------------
# Detector de marca de vehiculo desde el titulo
# ---------------------------------------------------------------------------

MARCAS_PATRONES = [
    ("BMW", r"\bbmw\b"),
    ("Mercedes-Benz", r"\bmercedes(?:[\s-]benz)?\b"),
    ("Audi", r"\baudi\b"),
    ("Volkswagen", r"\b(vw|volkswagen)\b"),
    ("Porsche", r"\bporsche\b"),
    ("Volvo", r"\bvolvo\b"),
    ("Mini", r"\bmini(?:[\s-]cooper)?\b"),
    ("Land Rover", r"\bland[\s-]?rover\b"),
    ("Jaguar", r"\bjaguar\b"),
    ("Range Rover", r"\brange\s?rover\b"),
    ("SEAT", r"\bseat\b"),
    ("Ferrari", r"\bferrari\b"),
    ("Maserati", r"\bmaserati\b"),
    ("Bentley", r"\bbentley\b"),
    ("Toyota", r"\btoyota\b"),
    ("Lexus", r"\blexus\b"),
    ("Chevrolet", r"\b(chevrolet|chevy)\b"),
    ("Renault", r"\brenault\b"),
    ("Jeep", r"\bjeep\b"),
    ("Ford", r"\bford\b"),
]


def marcas_titulo(titulo: str) -> list:
    t = titulo.lower()
    found = []
    for m, pat in MARCAS_PATRONES:
        if re.search(pat, t):
            found.append(m)
    return found


# ---------------------------------------------------------------------------
# Tipo: Llavero
# ---------------------------------------------------------------------------

def build_llavero(p: dict) -> dict:
    titulo = p["titulo"]
    sku = p["sku"]
    fila = p["_fila_original"]
    precio = p["precio"]
    marca_norm = p["marca_normalizada"]
    marca_raw = p["marca"]
    desc_orig = p["descripcion"]

    marcas_veh = marcas_titulo(titulo)
    marca_principal = marcas_veh[0] if marcas_veh else (marca_raw or "vehiculo europeo")

    # 5 parrafos
    p1 = (
        f"Llavero coleccionable con el emblema de {marca_principal}, fabricado en metal con acabado pulido "
        "y logotipo grabado. Esta pieza es un articulo de merchandising oficial-style: replica el logotipo "
        "de la marca con la fidelidad y el peso que distingue al original, sin ser una pieza falsificada. "
        "Cumple funcion practica como llavero del vehiculo y, al mismo tiempo, como objeto coleccionable para "
        "duenios entusiastas, clientes de talleres especializados o regalo para mecanicos y aficionados al "
        "automovilismo europeo."
    )

    if "doble vista" in titulo.lower() or "ambos lados" in (desc_orig or "").lower():
        p1 += (
            " Esta version trae el logotipo grabado en ambas caras del cuerpo del llavero, manteniendo la "
            "presentacion del emblema independientemente de la posicion del llavero en la mano o el bolsillo."
        )

    aplicacion = (
        f"Llavero generico para todos los modelos {marca_principal}"
        if marca_principal in ("BMW", "Mercedes-Benz", "Audi", "Volkswagen", "Porsche", "Volvo", "Mini", "Land Rover", "Jaguar", "Lexus", "Toyota", "Chevrolet", "Renault")
        else f"Llavero generico para vehiculos {marca_principal}"
    )

    p2 = (
        f"{aplicacion}. No tiene compatibilidad mecanica con un modelo o anio especifico — es un articulo "
        "decorativo que se usa con cualquier llave del vehiculo de la marca correspondiente, ya sea llave "
        "fisica tradicional, llave con control remoto o el porta-llave de smartkey moderno. Tampoco "
        "interfiere con el funcionamiento del transponder ni con los sistemas de seguridad del vehiculo. "
        f"Es independiente de la generacion del modelo: aplica igual para autos {marca_principal} de los "
        "anios noventa, dos mil o vehiculos nuevos."
    )

    p3 = (
        "Material y construccion: cuerpo en metal con acabado tipo cromado o satinado segun el modelo del "
        "llavero, anilla de acero inoxidable de tamano estandar y, en algunos modelos, ribete de cuero "
        "sintetico o eslabon flexible. Dimensiones aproximadas equivalentes a un llavero de coleccion "
        "estandar (entre 5 y 9 centimetros de largo segun el diseno). El logotipo se aplica por estampado, "
        "grabado laser o esmalte segun el acabado especifico — verifica las imagenes del listing para el "
        "detalle exacto del modelo que recibiras."
    )

    p4 = (
        "Se vende como pieza individual, en empaque de proteccion para evitar rayaduras durante el envio. "
        "Es un producto de merchandising, no autoparte: no requiere instalacion en el vehiculo ni "
        "compatibilidad mecanica. Util para llave principal, llave de respaldo, llaves de oficina o "
        "simplemente como pieza de coleccion para entusiastas. Tambien funciona como detalle corporativo "
        "para concesionarios, talleres o clubes de marca."
    )

    p5 = (
        "Producto de merchandising distribuido por Embler Autopartes Europeas, especialistas en venta de "
        "refacciones para BMW, Mercedes-Benz, Audi, Volkswagen, Porsche, Volvo, Mini Cooper y Jaguar. "
        "Sin garantia formal del vendedor por ser articulo de merchandising y no refaccion mecanica, pero "
        "aplican nuestras politicas de devolucion (30 dias, sin uso, en empaque original) en caso de "
        "defecto de fabrica o error de envio."
    )

    descripcion = "\n\n".join([p1, p2, p3, p4, p5])

    # caract_compatibilidad
    caract_compat = (
        f"Llavero generico de la marca {marca_principal}. No requiere compatibilidad mecanica — aplica "
        f"para cualquier modelo o anio {marca_principal}."
    )

    faqs = [
        {
            "pregunta": "¿Es un llavero original de la marca o una replica?",
            "respuesta": (
                "Es un articulo de merchandising-style con el logotipo de la marca, no una pieza con "
                "licencia oficial. Replica fielmente el emblema y mantiene la calidad del metal, pero no "
                "viene en empaque oficial del fabricante."
            ),
        },
        {
            "pregunta": "¿Funciona con la llave smartkey de mi vehiculo nuevo?",
            "respuesta": (
                "Si. El llavero es solo decorativo — se cuelga del aro junto a la llave y no interfiere "
                "con el transponder ni con el funcionamiento del sistema keyless."
            ),
        },
        {
            "pregunta": "¿Que material es el cuerpo del llavero?",
            "respuesta": (
                "Metal con acabado tipo cromado o satinado segun el modelo. La anilla es de acero "
                "inoxidable. Algunos modelos incluyen ribete de cuero sintetico."
            ),
        },
        {
            "pregunta": "¿Lo puedo usar de regalo?",
            "respuesta": (
                f"Si. Es un detalle apreciado por entusiastas de {marca_principal} y por mecanicos "
                "especializados en autos europeos. Se entrega en empaque de proteccion."
            ),
        },
    ]

    antes = (
        "Para garantizar el envio correcto, confirma con tu pedido la marca exacta del llavero (hay variantes "
        "para cada marca de vehiculo europeo). Si tienes dudas sobre el modelo del llavero o quieres ver "
        "fotos adicionales, escribenos antes de comprar."
    )
    envio = (
        "Tenemos stock disponible para entrega inmediata. Enviamos el mismo dia de tu pago a Ciudad de "
        "Mexico y a todo el pais via DHL o FedEx. Producto pequeno y ligero, costo de envio reducido."
    )

    titulo_limpio = title_clean(titulo)
    handle = slugify(f"{titulo_limpio}-{sku or fila}")
    seo_title = f"Llavero {marca_principal} | Embler"[:60]
    seo_desc = (
        f"Llavero coleccionable {marca_principal} en metal con logotipo grabado. "
        "Articulo de merchandising para entusiastas y mecanicos. Envio inmediato a todo Mexico."
    )[:155]
    image_alt = f"Llavero {marca_principal} metalico"[:125]

    body = body_html(descripcion, "", antes, envio, faqs[:5])

    revision = []
    if not sku:
        revision.append("[INCLUIR] SKU faltante — asignar antes de publicar.")
    if not marca_norm:
        revision.append("[ANALIZAR] Marca normalizada vacia — confirmar si el llavero es de la marca del titulo.")
    revision.append(
        "[ANALIZAR] Producto es merchandising (llavero), no autoparte. Considerar si va a la coleccion "
        "general de Embler o a una coleccion separada de Accesorios/Merchandising."
    )
    revision.append(REVISION_FIJA)

    return {
        "_fila_original": fila,
        "caract_marca": marca_norm or "Embler",
        "caract_origen": p["origen"] or "",
        "caract_tipo_vehiculo": "",  # no aplica
        "caract_compatibilidad": caract_compat,
        "seccion_descripcion": descripcion,
        "seccion_compatibilidades": "",
        "seccion_antes_de_comprar": antes,
        "seccion_envio": envio,
        "seccion_devoluciones": SECCION_DEVOLUCIONES,
        "seccion_faq": faqs,
        "productos_relacionados": [],
        "shopify_handle": handle,
        "shopify_title": titulo_limpio,
        "shopify_body_html": body,
        "shopify_product_category": "Vehicles & Parts > Vehicle Parts & Accessories",
        "shopify_type": "Accesorios",
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
        "revision_humana": "\n".join(revision),
    }


# ---------------------------------------------------------------------------
# Tipo: Refaccion sin descripcion (mal clasificada en otros)
# ---------------------------------------------------------------------------

REFACCION_PATRONES = [
    (r"junta\s+de?\s+(multiple|escape|cabeza|admision|tapa|punterias|carter|valvula)", "refacciones_motor", "Motor"),
    (r"junta\s+empaque", "refacciones_motor", "Motor"),
    (r"\b(termostato|bomba\s+(de\s+)?agua|polea\s+tensora|tensor\s+de\s+cadena|cadena\s+de\s+tiempo)", "refacciones_motor", "Motor"),
    (r"\b(arbol\s+de\s+levas|ciguenal|biela|piston|valvula|empaque)", "refacciones_motor", "Motor"),
    (r"\b(brida|conexion)\s+(bomba|agua)", "refacciones_motor", "Motor"),
    (r"\b(amortiguador|brazo\s+de\s+suspension|rotula|buje|barra\s+estabilizadora|resorte)", "refacciones_suspension", "Suspensión"),
    (r"\b(disco\s+de\s+freno|pastillas?\s+de\s+freno|caliper|balata|tambor)", "refacciones_frenos", "Frenos"),
    (r"\b(sensor|bobina|alternador|modulo|computadora|relay|fusible)", "refacciones_electrico", "Sistema Eléctrico"),
    (r"\b(faro|espejo|defensa|cofre|salpicadera|parrilla|calavera|moldura)", "refacciones_carroceria", "Carrocería"),
    (r"\bfiltro\b", "filtros", "Filtros"),
    (r"\b(embrague|clutch|convertidor)", "refacciones_transmision", "Transmisión"),
]


def detectar_subcategoria_implicita(titulo: str) -> tuple:
    """Devuelve (categoria_archivo_sugerida, shopify_type) o ('', '') si no se infiere."""
    t = titulo.lower()
    for patron, cat, st in REFACCION_PATRONES:
        if re.search(patron, t):
            return cat, st
    return "", "Refacciones"


def build_refaccion_sin_desc(p: dict) -> dict:
    titulo = p["titulo"]
    sku = p["sku"]
    fila = p["_fila_original"]
    precio = p["precio"]
    numero_parte = p["numero_parte"]
    oem = p["codigo_oem"]
    marca_norm = p["marca_normalizada"]
    marca_raw = p["marca"]
    tipo_veh = p["tipo_vehiculo"]
    garantia_raw = p["garantia"]

    cat_sugerida, shopify_type = detectar_subcategoria_implicita(titulo)
    marcas_veh = marcas_titulo(titulo)
    marca_principal = marcas_veh[0] if marcas_veh else "vehiculo europeo"

    # P1 — basado en el titulo
    p1 = (
        f"{title_clean(titulo)}. Refaccion para vehiculos europeos identificada por el titulo del listing. "
        "El listing original no incluye una descripcion detallada del producto, por lo que la informacion "
        "tecnica disponible se limita al nombre del producto y los modelos mencionados en el titulo. "
        "Antes de comprar te recomendamos confirmar con nuestro equipo el numero de parte exacto, codigo OEM "
        "y caracteristicas tecnicas (material, dimensiones, configuracion) contra el catalogo del proveedor "
        "para asegurar que es la pieza correcta para tu reparacion."
    )

    p2 = (
        f"Por las marcas y modelos mencionados en el titulo, aplica para vehiculos {marca_principal}. La "
        "descripcion del listing no esta estructurada en el bloque APLICA PARA estandar, asi que no se "
        "pudo extraer una lista detallada de configuraciones automaticamente. Para confirmar compatibilidad "
        "exacta — incluyendo anio, motor y configuracion regional — envianos tu numero de VIN y un asesor "
        "validara la pieza contra la base de datos del fabricante antes de procesar el pedido."
    )

    refs = []
    if numero_parte:
        refs.append(f"numero de parte: {numero_parte}")
    if oem and oem != numero_parte:
        refs.append(f"codigo OEM: {oem}")
    if refs:
        p3 = (
            "Especificaciones de referencia disponibles: "
            + "; ".join(refs)
            + ". Estos codigos se cruzan contra el catalogo OEM del fabricante. Sin descripcion detallada "
            "del listing, te recomendamos comparar visualmente la pieza con la original de tu vehiculo "
            "antes de instalar."
        )
    else:
        p3 = (
            "El listing no incluye numero de parte ni codigo OEM publicados. Antes de comprar, recomendamos "
            "consultar con un taller especializado para identificar el codigo OEM correcto y validar contra "
            "el catalogo del fabricante (ETKA para Audi/VW, ETIS para BMW, EPC para Mercedes)."
        )

    p4 = (
        "Se vende como pieza individual nueva. La presentacion exacta (caja del fabricante, bolsa "
        "antiestatica, kit con tornilleria) no se especifica en el listing — confirma con nuestro asesor "
        "antes de la compra si necesitas saber que viene exactamente en el empaque."
    )

    pos_marca = (
        f"Marca {marca_norm}, fabricante de refacciones para vehiculos europeos."
        if marca_norm
        else "Marca y fabricante por confirmar — el listing no especifica el fabricante de la refaccion."
    )
    gar_dias = "30"
    m = re.search(r"(\d+)\s*d[ií]as?", garantia_raw)
    if m:
        gar_dias = m.group(1)
    p5 = (
        f"{pos_marca} Garantia del vendedor de {gar_dias} dias contra defectos de fabrica. Embler Autopartes "
        "Europeas mantiene stock con entrega inmediata desde Ciudad de Mexico, ademas de soporte tecnico "
        "para verificacion de compatibilidad por VIN antes del envio."
    )

    descripcion = "\n\n".join([p1, p2, p3, p4, p5])

    caract_compat = (
        f"Aplica para vehiculos {marca_principal} mencionados en el titulo. "
        "Confirma compatibilidad exacta con tu numero de VIN antes de comprar."
    )

    faqs = [
        {
            "pregunta": "¿Por que el listing no tiene descripcion detallada?",
            "respuesta": (
                "Este listing fue publicado con datos minimos. Tenemos la pieza en stock pero la "
                "descripcion comercial completa esta pendiente de capturar. Antes de comprar, envianos "
                "tu numero de VIN y un asesor te confirma compatibilidad, especificaciones y referencias "
                "OEM."
            ),
        },
        {
            "pregunta": "¿Como confirmo que es la pieza correcta?",
            "respuesta": (
                "Envianos tu numero de VIN y, si tienes, el numero de parte de la pieza original que "
                "estas reemplazando. Validamos contra el catalogo del fabricante antes de procesar el "
                "pedido."
            ),
        },
        {
            "pregunta": "¿Puedo regresarla si no es la pieza correcta?",
            "respuesta": (
                "Si. Aplican nuestras politicas de devolucion (30 dias, sin uso, sin instalar, en empaque "
                "original). Por eso es importante validar compatibilidad antes de instalar."
            ),
        },
        {
            "pregunta": "¿Tiene garantia?",
            "respuesta": f"Garantia del vendedor de {gar_dias} dias contra defectos de fabrica.",
        },
    ]

    antes = (
        "Para garantizar que recibas la pieza correcta, necesitamos el numero de serie (VIN) de tu vehiculo "
        "antes de procesar el pedido. Este listing tiene informacion limitada por lo que la verificacion "
        "previa al envio es indispensable."
        + (f" Tambien puedes mencionar el numero de parte {numero_parte}." if numero_parte else "")
        + (f" Codigo OEM de referencia: {oem}." if oem and oem != numero_parte else "")
    )
    envio = (
        "Tenemos stock disponible para entrega inmediata. Enviamos el mismo dia de tu pago a Ciudad de "
        "Mexico y a todo el pais via DHL o FedEx, una vez confirmada la compatibilidad."
    )

    titulo_limpio = title_clean(titulo)
    handle = slugify(f"{titulo_limpio}-{sku or fila}")
    seo_title = f"{titulo_limpio[:48]} | Embler"[:60]
    seo_desc = (
        f"{titulo_limpio} — refaccion para vehiculos europeos. "
        "Verifica compatibilidad con VIN. Envio inmediato a todo Mexico."
    )[:155]
    image_alt = f"{titulo_limpio[:80]} para {marca_principal}"[:125]

    body = body_html(descripcion, "", antes, envio, faqs)

    revision = [
        "[BUSCAR] Descripcion completa del producto: el listing original esta vacio. Buscar en catalogo "
        "del proveedor o pedir ficha tecnica.",
    ]
    if not numero_parte and not oem:
        revision.append("[BUSCAR] Numero de parte y codigo OEM faltantes — buscar en catalogo del proveedor.")
    if cat_sugerida and cat_sugerida != "otros":
        revision.append(
            f"[ANALIZAR] Mal clasificada en `otros` — el titulo sugiere {cat_sugerida}. "
            "Considerar mover el producto a esa categoria antes de publicar."
        )
    revision.append(
        "[VERIFICAR] Compatibilidad inferida solo del titulo. Confirmar modelos, anios y configuraciones "
        "antes de publicar como activo."
    )
    if not sku:
        revision.append("[INCLUIR] SKU faltante — asignar antes de publicar.")
    revision.append(REVISION_FIJA)

    return {
        "_fila_original": fila,
        "caract_marca": marca_norm or "",
        "caract_origen": p["origen"] or "",
        "caract_tipo_vehiculo": tipo_veh,
        "caract_compatibilidad": caract_compat,
        "seccion_descripcion": descripcion,
        "seccion_compatibilidades": "",
        "seccion_antes_de_comprar": antes,
        "seccion_envio": envio,
        "seccion_devoluciones": SECCION_DEVOLUCIONES,
        "seccion_faq": faqs,
        "productos_relacionados": [],
        "shopify_handle": handle,
        "shopify_title": titulo_limpio,
        "shopify_body_html": body,
        "shopify_product_category": "Vehicles & Parts > Vehicle Parts & Accessories",
        "shopify_type": shopify_type,
        "shopify_tags": ", ".join(marcas_veh),
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
        "revision_humana": "\n".join(revision),
    }


# ---------------------------------------------------------------------------
# Tipo: Spam (criptomonedas / nombres de personas / no autopartes)
# ---------------------------------------------------------------------------

def build_spam(p: dict) -> dict:
    fila = p["_fila_original"]
    titulo = p["titulo"]
    cat = p["categoria"]
    precio = p["precio"]
    sku = p["sku"]

    revision = (
        "[ANALIZAR] CRITICAL: este listing NO ES UN PRODUCTO autoparte. "
        f"Categoria ML registrada: {cat[:80]}. "
        f"Titulo: {titulo}. "
        "Probablemente es un listing de prueba, error de publicacion o spam de la cuenta. "
        "ELIMINAR de Shopify y revisar en MercadoLibre si debe despublicarse.\n"
        + REVISION_FIJA
    )

    return {
        "_fila_original": fila,
        "caract_marca": "",
        "caract_origen": "",
        "caract_tipo_vehiculo": "",
        "caract_compatibilidad": "",
        "seccion_descripcion": (
            f"[LISTING NO ES UN PRODUCTO AUTOPARTE — REVISAR Y ELIMINAR]\n\n"
            f"El titulo de este listing es '{titulo}' y la categoria de MercadoLibre es '{cat}'. "
            "No corresponde al catalogo de autopartes de Embler. Probablemente es una publicacion "
            "incorrecta, prueba o spam que entro al cruce con Microsip. Este registro no debe publicarse "
            "en Shopify y debe revisarse manualmente en la cuenta de MercadoLibre."
        ),
        "seccion_compatibilidades": "",
        "seccion_antes_de_comprar": "",
        "seccion_envio": "",
        "seccion_devoluciones": "",
        "seccion_faq": [],
        "productos_relacionados": [],
        "shopify_handle": slugify(f"revisar-{titulo}-{fila}"),
        "shopify_title": f"[REVISAR] {title_clean(titulo)}",
        "shopify_body_html": (
            "<h2>Atencion</h2><p>Este registro no corresponde a un producto autoparte. "
            "Revisar manualmente y eliminar de Shopify.</p>"
        ),
        "shopify_product_category": "",
        "shopify_type": "",
        "shopify_tags": "",
        "shopify_published": "FALSE",
        "shopify_option1_name": "Title",
        "shopify_option1_value": "Default Title",
        "shopify_variant_sku": sku,
        "shopify_variant_price": precio,
        "shopify_variant_compare_price": "",
        "shopify_variant_weight": "",
        "shopify_variant_weight_unit": "kg",
        "shopify_image_src": "",
        "shopify_image_alt_text": "",
        "shopify_seo_title": "",
        "shopify_seo_description": "",
        "shopify_status": "draft",
        "revision_humana": revision,
    }


# ---------------------------------------------------------------------------
# Detector de tipo
# ---------------------------------------------------------------------------

def detectar_tipo(p: dict) -> str:
    titulo = p["titulo"].lower()
    sub = p["subcategoria"].lower()
    cat = p["categoria"].lower()

    # Spam: criptomonedas, mineria, o categoria fuera de autopartes
    if "criptomonedas" in cat or "minería" in sub:
        return "spam"
    # Llaveros
    if "llavero" in titulo or "llaveros" in sub:
        return "llavero"
    # Refaccion mal clasificada
    return "refaccion_sin_desc"


def construir_resultado(p: dict) -> dict:
    tipo = detectar_tipo(p)
    if tipo == "llavero":
        return build_llavero(p)
    elif tipo == "spam":
        return build_spam(p)
    else:
        return build_refaccion_sin_desc(p)


def main():
    with open(BATCH_PATH, encoding="utf-8") as f:
        data = json.load(f)
    productos = data["productos"]
    resultados = [construir_resultado(p) for p in productos]
    payload = {"resultados": resultados}
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Resultados generados: {len(resultados)} filas -> {OUTPUT_PATH}")
    word_counts = [len(r["seccion_descripcion"].split()) for r in resultados if r.get("seccion_descripcion")]
    if word_counts:
        print(f"  Palabras seccion_descripcion: min={min(word_counts)} max={max(word_counts)} avg={sum(word_counts)//len(word_counts)}")
    tipos = Counter(detectar_tipo(p) for p in productos)
    print(f"  Distribucion por tipo: {dict(tipos)}")


if __name__ == "__main__":
    main()
