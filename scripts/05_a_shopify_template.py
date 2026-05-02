"""
Convierte CSVs de final-listo-shopify/ al schema exacto del export del theme Shopify
(export_shopify_estructura_sitio.csv) — 57 columnas + metafields.

Reglas confirmadas con Migue:
  - Sin variantes (Option1=Title / Default Title). Cada SKU es un producto.
  - filters.detail_2 (Año) es list-type. Expandir rangos a años individuales.
  - global.brand (Marca auto) es single. Usar la marca dominante (la primera del orden europeo).
  - page_info.detail_3 (Origen) acepta multiple.
  - Body reducido a Descripción + FAQ. Compatibilidades, antes-de-comprar, envío y devoluciones
    los renderiza el theme desde metafields o secciones globales.
  - SKU faltante → fallback a MC_SKU_match (parsear el primero, sin "*qty").
  - Stock inicial 0 + Inventory Policy=deny.

Output:
  final-shopify-estructura-sitio/<categoria>.csv

Estructura de filas (sin variantes):
  - Row 1 del producto: TODA la info (Title, Body, metafields, primera imagen img1, Image Position=1)
  - Rows 2..N: solo Handle + Image Src (img2, img3, ..., imgN) + Image Position (2..N).
    El resto de columnas vacías. El theme/Shopify hereda imagen al producto.

Uso:
  python scripts/05_a_shopify_template.py <categoria>
  python scripts/05_a_shopify_template.py all
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "final-listo-shopify"
DST_DIR = ROOT / "final-shopify-estructura-sitio"
DST_DIR.mkdir(exist_ok=True)

csv.field_size_limit(sys.maxsize)


# ---------------------------------------------------------------------------
# Schema target — 57 columnas exactas del export
# ---------------------------------------------------------------------------

TARGET_COLUMNS = [
    "Handle",
    "Title",
    "Body (HTML)",
    "Vendor",
    "Product Category",
    "Type",
    "Tags",
    "Published",
    "Option1 Name",
    "Option1 Value",
    "Option1 Linked To",
    "Option2 Name",
    "Option2 Value",
    "Option2 Linked To",
    "Option3 Name",
    "Option3 Value",
    "Option3 Linked To",
    "Variant SKU",
    "Variant Grams",
    "Variant Inventory Tracker",
    "Variant Inventory Qty",
    "Variant Inventory Policy",
    "Variant Fulfillment Service",
    "Variant Price",
    "Variant Compare At Price",
    "Variant Requires Shipping",
    "Variant Taxable",
    "Unit Price Total Measure",
    "Unit Price Total Measure Unit",
    "Unit Price Base Measure",
    "Unit Price Base Measure Unit",
    "Variant Barcode",
    "Image Src",
    "Image Position",
    "Image Alt Text",
    "Gift Card",
    "SEO Title",
    "SEO Description",
    "Filtros - Refacción (product.metafields.filters.detail_1)",
    "Filtros - Año (product.metafields.filters.detail_2)",
    "Filtros - Marca de la refacción (product.metafields.filters.detail_3)",
    "Marca del auto (product.metafields.global.brand)",
    "Información de envio (product.metafields.global.shipping)",
    "Listado - Número de parte (product.metafields.list.detail_1)",
    "Página - Ruta de navegación (product.metafields.page.breadcrumb)",
    "Características - Marca (product.metafields.page_info.detail_1)",
    "Características - Tipo de vehículo (product.metafields.page_info.detail_2)",
    "Características - Origen (product.metafields.page_info.detail_3)",
    "Complementary products (product.metafields.shopify--discovery--product_recommendation.complementary_products)",
    "Related products (product.metafields.shopify--discovery--product_recommendation.related_products)",
    "Related products settings (product.metafields.shopify--discovery--product_recommendation.related_products_display)",
    "Search product boosts (product.metafields.shopify--discovery--product_search_boost.queries)",
    "Variant Image",
    "Variant Weight Unit",
    "Variant Tax Code",
    "Cost per item",
    "Status",
]


# ---------------------------------------------------------------------------
# Slugs de marca para global.brand (single value)
# ---------------------------------------------------------------------------

BRAND_SLUG = {
    "BMW": "bmw",
    "Mercedes-Benz": "mercedes-benz",
    "Audi": "audi",
    "Volkswagen": "volkswagen",
    "Porsche": "porsche",
    "Volvo": "volvo",
    "Mini": "mini",
    "Land Rover": "land-rover",
    "Jaguar": "jaguar",
    "SEAT": "seat",
    "Smart": "smart",
    "Fiat": "fiat",
    "Alfa Romeo": "alfa-romeo",
    "Bentley": "bentley",
    "Rolls-Royce": "rolls-royce",
}

# Orden de prioridad cuando un producto aplica a varias marcas
BRAND_PRIORITY = list(BRAND_SLUG.keys())


# Tipo de refacción (filters.detail_1) — categoría cerrada PERO el theme acepta lo que pongamos.
# Mapeamos subcategoria_limpia → Tipo de refacción presentable.
TIPO_REFACCION_MAP = {
    "motor": "Motor",
    "suspension": "Suspensión",
    "suspensión": "Suspensión",
    "frenos": "Frenos",
    "transmision": "Transmisión",
    "transmisión": "Transmisión",
    "electrico": "Sistema Eléctrico",
    "eléctrico": "Sistema Eléctrico",
    "carroceria": "Carrocería",
    "carrocería": "Carrocería",
    "clima": "Clima y Aire Acondicionado",
    "accesorios": "Accesorios",
    "tuning": "Tuning",
    "herramientas": "Herramientas",
    "otros": "Otros",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

RX_YEAR_RANGE = re.compile(r"\b(19[8-9]\d|20[0-3]\d)\s*[-–—]\s*(19[8-9]\d|20[0-3]\d)\b")
RX_YEAR = re.compile(r"\b(19[8-9]\d|20[0-3]\d)\b")


def extract_years(*texts: str) -> list:
    years = set()
    for t in texts:
        if not t:
            continue
        # Normalizar conectores de rango
        normalized = (
            t.replace(" Al ", "-").replace(" al ", "-").replace(" AL ", "-")
             .replace(" A ", "-").replace(" a ", "-")
        )
        for m in RX_YEAR_RANGE.finditer(normalized):
            a, b = int(m.group(1)), int(m.group(2))
            if a <= b and (b - a) <= 30:
                for y in range(a, b + 1):
                    years.add(y)
        for m in RX_YEAR.finditer(normalized):
            years.add(int(m.group(1)))
    return sorted(years)


def detect_brands_in_text(text: str) -> list:
    """Detecta marcas de auto presentes en el texto, preservando orden de prioridad."""
    if not text:
        return []
    upper = text.upper()
    found = []
    for brand in BRAND_PRIORITY:
        # Match substrings (Mercedes, BMW, etc.)
        keys = [brand.upper(), brand.upper().replace("-", " ")]
        if brand == "Volkswagen":
            keys.append("VW")
        if brand == "Mercedes-Benz":
            keys += ["MERCEDES BENZ", "MERCEDES"]
        if any(k in upper for k in keys):
            if brand not in found:
                found.append(brand)
    return found


def pick_dominant_brand(row: dict) -> str:
    """Devuelve un slug único para global.brand."""
    # 1) shopify_tags ya viene con marca(s) primaria(s) — separadas por ", "
    tags = (row.get("shopify_tags") or "").strip()
    candidates = []
    if tags:
        for piece in re.split(r"[,;]+", tags):
            p = piece.strip()
            if p:
                candidates.append(p)

    # Si hay matches por nombre exacto a BRAND_PRIORITY, devuelve el primero (orden de prioridad)
    for brand in BRAND_PRIORITY:
        for c in candidates:
            if c.lower().replace("-", " ") == brand.lower().replace("-", " "):
                return BRAND_SLUG[brand]

    # 2) Detectar en compatibilidad / título
    text = " ".join([
        row.get("caract_compatibilidad", ""),
        row.get("seccion_compatibilidades", ""),
        row.get("shopify_title", ""),
        row.get("Título", "") or row.get("Titulo", ""),
    ])
    brands = detect_brands_in_text(text)
    if brands:
        return BRAND_SLUG[brands[0]]
    return ""


def pick_sku(row: dict) -> str:
    """SKU con fallback: shopify_variant_sku → SKU original → MC_SKU_match (parseado)."""
    for k in ("shopify_variant_sku", "SKU"):
        v = (row.get(k) or "").strip()
        if v:
            return v
    mc = (row.get("MC_SKU_match") or "").strip()
    if mc:
        # Formato típico: "2052400200 *1" o "2052400200 *1[A]"
        first = mc.split("|")[0].strip()
        first = re.split(r"\s*\*", first)[0].strip()
        return first
    return ""


def pick_numero_parte(row: dict) -> str:
    """Número de parte para list.detail_1. Toma Atributo Numero de parte; si no, OEM."""
    for k in ("Atributo Número de parte", "Atributo Numero de parte", "Atributo  Número de parte"):
        v = (row.get(k) or "").strip()
        if v:
            return v
    for k in ("Atributo Código OEM", "Atributo Codigo OEM", "Atributo  Código OEM"):
        v = (row.get(k) or "").strip()
        if v:
            return v
    return ""


def shopify_list(values: list) -> str:
    """Formato de Shopify CSV bulk import para metafields list.*: JSON array string."""
    if not values:
        return ""
    return json.dumps(values, ensure_ascii=False, separators=(",", ""))


def reduce_body(row: dict) -> str:
    """Body reducido: Descripción + FAQ. El theme renderiza compatibilidades/envío/devoluciones
    desde metafields/secciones globales, así que evitamos duplicación."""
    desc = (row.get("seccion_descripcion") or "").strip()

    # FAQ — viene como JSON array de {pregunta, respuesta}
    faq_raw = (row.get("seccion_faq") or "").strip()
    faqs = []
    if faq_raw:
        try:
            data = json.loads(faq_raw)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        q = (item.get("pregunta") or item.get("question") or "").strip()
                        a = (item.get("respuesta") or item.get("answer") or "").strip()
                        if q and a:
                            faqs.append((q, a))
        except (json.JSONDecodeError, TypeError):
            pass

    parts = []
    if desc:
        # Convertir saltos de línea en párrafos
        for p in re.split(r"\n\s*\n", desc):
            p = p.strip()
            if p:
                parts.append(f"<p>{p}</p>")
    if faqs:
        parts.append("<h3>Preguntas frecuentes</h3>")
        for q, a in faqs:
            parts.append(f"<p><strong>{q}</strong><br>{a}</p>")
    return "".join(parts)


def collect_image_urls(row: dict) -> list:
    urls = []
    for i in range(1, 21):
        u = (row.get(f"img{i}") or "").strip()
        if u:
            urls.append(u)
    return urls


def shipping_value(row: dict) -> str:
    """global.shipping — derivar de stock. Tenemos columnas raras como 'Stock: Tlalpan...'"""
    # Buscar cualquier columna que empiece con "Stock"
    has_stock = False
    for k, v in row.items():
        if k.startswith("Stock") and v and str(v).strip() not in ("0", "", "0.0"):
            try:
                if int(float(str(v))) > 0:
                    has_stock = True
                    break
            except (ValueError, TypeError):
                pass
    disp = (row.get("Disponibilidad de stock") or "").strip()
    if disp and disp not in ("0", "", "0.0"):
        try:
            if int(float(disp)) > 0:
                has_stock = True
        except (ValueError, TypeError):
            pass
    return "entregamos-hoy" if has_stock else ""


def origen_metafield(row: dict) -> str:
    """page_info.detail_3 — multi-valued. Default 'Tecnología Alemana' para autopartes europeas
    (todas las marcas que manejamos lo son), más caract_origen si existe."""
    values = ["Tecnología Alemana"]
    extra = (row.get("caract_origen") or "").strip()
    if extra and extra not in values:
        values.append(extra)
    return shopify_list(values)


def tipo_refaccion(row: dict) -> str:
    sub = (row.get("subcategoria_limpia") or "").strip().lower()
    if sub in TIPO_REFACCION_MAP:
        return TIPO_REFACCION_MAP[sub]
    # fallback: shopify_type
    t = (row.get("shopify_type") or "").strip()
    return t or "Otros"


def caract_marca_normalizado(row: dict) -> str:
    """page_info.detail_1 — Marca de la refacción para mostrar en ficha técnica.
    Usa caract_marca/marca_normalizada."""
    for k in ("caract_marca", "marca_normalizada"):
        v = (row.get(k) or "").strip()
        if v:
            return v
    return ""


# ---------------------------------------------------------------------------
# Construcción de filas
# ---------------------------------------------------------------------------

def build_main_row(src: dict) -> dict:
    """Construye la fila principal del producto (Image Position=1 con toda la metadata)."""
    handle = (src.get("shopify_handle") or "").strip()
    title = (src.get("shopify_title") or "").strip()
    body = reduce_body(src)

    images = collect_image_urls(src)
    first_image = images[0] if images else ""

    sku = pick_sku(src)
    price = (src.get("shopify_variant_price") or "").strip()

    # Años (list)
    years = extract_years(
        src.get("seccion_compatibilidades", ""),
        src.get("caract_compatibilidad", ""),
        src.get("shopify_title", ""),
        src.get("Título", "") or src.get("Titulo", ""),
    )
    years_meta = shopify_list([str(y) for y in years])

    brand_slug = pick_dominant_brand(src)
    tipo = tipo_refaccion(src)
    marca_refaccion = caract_marca_normalizado(src)
    numero_parte = pick_numero_parte(src)
    tipo_vehiculo = (src.get("caract_tipo_vehiculo") or "").strip()
    origen = origen_metafield(src)

    seo_title = (src.get("shopify_seo_title") or title)[:70]
    seo_desc = (src.get("shopify_seo_description") or "")[:320]
    alt = (src.get("shopify_image_alt_text") or title)

    return {
        "Handle": handle,
        "Title": title,
        "Body (HTML)": body,
        "Vendor": "Embler",
        "Product Category": "Uncategorized",
        "Type": "",
        "Tags": "",
        "Published": "TRUE",
        "Option1 Name": "Title",
        "Option1 Value": "Default Title",
        "Option1 Linked To": "",
        "Option2 Name": "",
        "Option2 Value": "",
        "Option2 Linked To": "",
        "Option3 Name": "",
        "Option3 Value": "",
        "Option3 Linked To": "",
        "Variant SKU": sku,
        "Variant Grams": "0",
        "Variant Inventory Tracker": "shopify",
        "Variant Inventory Qty": "0",
        "Variant Inventory Policy": "deny",
        "Variant Fulfillment Service": "manual",
        "Variant Price": price,
        "Variant Compare At Price": "",
        "Variant Requires Shipping": "true",
        "Variant Taxable": "true",
        "Unit Price Total Measure": "",
        "Unit Price Total Measure Unit": "",
        "Unit Price Base Measure": "",
        "Unit Price Base Measure Unit": "",
        "Variant Barcode": "",
        "Image Src": first_image,
        "Image Position": "1" if first_image else "",
        "Image Alt Text": alt if first_image else "",
        "Gift Card": "false",
        "SEO Title": seo_title,
        "SEO Description": seo_desc,
        "Filtros - Refacción (product.metafields.filters.detail_1)": tipo,
        "Filtros - Año (product.metafields.filters.detail_2)": years_meta,
        "Filtros - Marca de la refacción (product.metafields.filters.detail_3)": marca_refaccion,
        "Marca del auto (product.metafields.global.brand)": brand_slug,
        "Información de envio (product.metafields.global.shipping)": shipping_value(src),
        "Listado - Número de parte (product.metafields.list.detail_1)": numero_parte,
        "Página - Ruta de navegación (product.metafields.page.breadcrumb)": "",
        "Características - Marca (product.metafields.page_info.detail_1)": marca_refaccion,
        "Características - Tipo de vehículo (product.metafields.page_info.detail_2)": tipo_vehiculo,
        "Características - Origen (product.metafields.page_info.detail_3)": origen,
        "Complementary products (product.metafields.shopify--discovery--product_recommendation.complementary_products)": "",
        "Related products (product.metafields.shopify--discovery--product_recommendation.related_products)": "",
        "Related products settings (product.metafields.shopify--discovery--product_recommendation.related_products_display)": "",
        "Search product boosts (product.metafields.shopify--discovery--product_search_boost.queries)": "",
        "Variant Image": "",
        "Variant Weight Unit": "kg",
        "Variant Tax Code": "",
        "Cost per item": "",
        "Status": "draft",
    }


def build_image_row(handle: str, image_url: str, position: int) -> dict:
    """Filas extra para imágenes adicionales (img2..imgN). Solo Handle + Image Src + Image Position."""
    row = {col: "" for col in TARGET_COLUMNS}
    row["Handle"] = handle
    row["Image Src"] = image_url
    row["Image Position"] = str(position)
    return row


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def transform_file(category: str) -> dict:
    src_path = SRC_DIR / f"{category}.csv"
    dst_path = DST_DIR / f"{category}.csv"
    if not src_path.exists():
        raise FileNotFoundError(src_path)

    products = 0
    image_rows = 0
    seen_handles = set()

    with open(src_path, newline="", encoding="utf-8") as fin, \
         open(dst_path, "w", newline="", encoding="utf-8") as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=TARGET_COLUMNS, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()

        for src in reader:
            handle = (src.get("shopify_handle") or "").strip()
            if not handle:
                continue
            # Si ya existe el handle (caso raro de duplicado), skip
            if handle in seen_handles:
                continue
            seen_handles.add(handle)

            main = build_main_row(src)
            writer.writerow(main)
            products += 1

            images = collect_image_urls(src)
            for pos, url in enumerate(images[1:], start=2):
                writer.writerow(build_image_row(handle, url, pos))
                image_rows += 1

    return {
        "category": category,
        "src": str(src_path.relative_to(ROOT)),
        "dst": str(dst_path.relative_to(ROOT)),
        "products": products,
        "image_rows": image_rows,
        "total_rows": products + image_rows,
    }


CATEGORIES = [
    "accesorios",
    "herramientas",
    "otros",
    "refacciones_carroceria",
    "refacciones_clima",
    "refacciones_electrico",
    "refacciones_frenos",
    "refacciones_motor",
    "refacciones_otros",
    "refacciones_suspension",
    "refacciones_transmision",
    "tuning",
]


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/05_a_shopify_template.py <categoria|all>")
        sys.exit(2)
    arg = sys.argv[1]
    targets = CATEGORIES if arg == "all" else [arg]
    for cat in targets:
        stats = transform_file(cat)
        print(json.dumps(stats, ensure_ascii=False))


if __name__ == "__main__":
    main()
