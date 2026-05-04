"""
Aplica correcciones al feedback de Migue (mayo 2026) sobre los CSVs en
final-shopify-estructura-sitio/:

1. Body (HTML): se acorta a un solo parrafo (la descripcion corta) para que el
   bloque del sidebar derecho del theme deje de mostrar el contenido largo y para
   que las FAQs no se dupliquen.
2. Caracteristicas - Origen: se limpia el JSON-list (`["Tecnología Alemana",...]`)
   a un string sencillo. Por defecto "Importado" para autopartes europeas.
3. Type: se llena con el nombre de la coleccion del theme. Para refacciones_otros
   se deriva de keywords del titulo.
4. Tags: marcas de VEHICULO compatibles (BMW, Mercedes-Benz, Audi, Porsche,
   Volkswagen, Mini, Volvo, Sprinter, Land Rover) extraidas del Title + Body
   HTML + metafield "Marca del auto".

Lee cada CSV de final-shopify-estructura-sitio/<categoria>.csv, escribe el
backup en final-shopify-estructura-sitio/_backup/<categoria>.csv y sobre-escribe
el original con las correcciones aplicadas.
"""

import csv
import json
import os
import re
import shutil
import sys

csv.field_size_limit(10**9)

BASE = os.path.join(os.path.dirname(__file__), "..", "final-shopify-estructura-sitio")
BASE = os.path.abspath(BASE)
BACKUP = os.path.join(BASE, "_backup")

FILE_TO_COLLECTION = {
    "accesorios.csv": "Accesorios",
    "herramientas.csv": "Herramientas",
    "otros.csv": "Otros",
    "refacciones_carroceria.csv": "Carrocería",
    "refacciones_clima.csv": "Sistema de enfriamiento",
    "refacciones_electrico.csv": "Sistema eléctrico",
    "refacciones_frenos.csv": "Frenos",
    "refacciones_motor.csv": "Motor",
    "refacciones_suspension.csv": "Suspensión",
    "refacciones_transmision.csv": "Transmisión",
    "tuning.csv": "Tuning",
    # refacciones_otros.csv: derivado por titulo
}

# Display names + keywords (lowercase, word-boundary ready) por marca de vehiculo.
# El orden importa porque "sprinter" deriva tambien Mercedes-Benz.
VEHICLE_BRAND_RULES = [
    ("BMW", [r"\bbmw\b"]),
    (
        "Mercedes-Benz",
        [
            r"\bmercedes\b", r"\bmercedes-benz\b", r"\bmercedez\b", r"\bmercede\b", r"\bsprinter\b",
            # Lineas Mercedes en titulos (cuando el body no tiene marca explicita).
            r"\bgl[abceks]\d", r"\bglk\d?", r"\bml\d{3}", r"\bcla\d", r"\bcls\d",
            r"\bslk\d", r"\bslc\d", r"\bsl\d{2,3}", r"\bamg\b",
        ],
    ),
    ("Sprinter", [r"\bsprinter\b"]),
    ("Audi", [r"\baudi\b"]),
    ("Porsche", [r"\bporsche\b", r"\bporche\b"]),
    ("Volkswagen", [r"\bvolkswagen\b", r"\bvw\b", r"\bjetta\b", r"\bcrafter\b", r"\btiguan\b", r"\btouareg\b", r"\bpassat\b", r"\bgolf\b", r"\bbeetle\b", r"\bvento\b", r"\bamarok\b"]),
    ("Mini", [r"\bmini\b"]),
    ("Volvo", [r"\bvolvo\b"]),
    ("Land Rover", [r"\bland\s*rover\b", r"\brange\s*rover\b", r"\bfreelander\b", r"\bdiscovery\b", r"\bdefender\b"]),
    ("Jaguar", [r"\bjaguar\b"]),
    ("Smart", [r"\bsmart\s*for(?:two|four)\b", r"\bsmart\s*car\b"]),
    ("Seat", [r"\bseat\s+(?:leon|ibiza|alhambra|toledo|ateca|arona|tarraco)\b"]),
    ("Bentley", [r"\bbentley\b"]),
    ("Fiat", [r"\bfiat\b"]),
]

MARCA_AUTO_TO_DISPLAY = {
    "bmw": "BMW",
    "mercedes-benz": "Mercedes-Benz",
    "mercedez-benz": "Mercedes-Benz",
    "audi": "Audi",
    "porsche": "Porsche",
    "volkswagen": "Volkswagen",
    "vw": "Volkswagen",
    "mini": "Mini",
    "volvo": "Volvo",
    "land-rover": "Land Rover",
    "land rover": "Land Rover",
    "sprinter": "Sprinter",
    "jaguar": "Jaguar",
    "smart": "Smart",
    "seat": "Seat",
    "bentley": "Bentley",
    "fiat": "Fiat",
}


# Refacciones_otros: keyword -> coleccion. Orden importa.
OTROS_RULES = [
    ("Afinación y filtros", [r"\bfiltro\s+de\s+aceite\b", r"\bfiltro\s+de\s+aire\b", r"\bfiltro\s+de\s+combustible\b", r"\bfiltro\s+de\s+gasolina\b", r"\bfiltro\s+polen\b", r"\bfiltro\s+habit", r"\bfiltro\s+secador\b", r"\bbujia\b"]),
    ("Iluminación", [r"\bcalavera\b", r"\bfaro\b", r"\bluz\b", r"\bfoco\b", r"\bbalastra\b", r"\bxen[oó]n\b"]),
    ("Sistema de enfriamiento", [r"\bmotoventilador\b", r"\bventilador\b", r"\bradiador\b", r"\bbomba\s+de\s+agua\b", r"\bdep[oó]sito\s+de\s+anticongelante\b"]),
    ("Sistema eléctrico", [r"\bsensor\b", r"\bm[oó]dulo\b", r"\bmodulo\b", r"\bcable\s+bater[ií]a\b", r"\bbater[ií]a\b", r"\bactuador\b", r"\bbolsa\s+de\s+seguridad\b", r"\b[aá]ngulo\s+de\s+giro\b", r"\bcerradura\b", r"\bchapa\b", r"\bllave\b", r"\bbobina\b", r"\bbater\b"]),
    ("Carrocería", [r"\bamortiguador\s+de\s*cofre\b", r"\bamortiguador\s+cofre\b", r"\belevador\b", r"\bregulador\s+ventana\b", r"\bcristal\b", r"\bventana\b", r"\bemblema\b", r"\bmoldura\b", r"\btolva\b", r"\bsalpicadera\b", r"\bbisagra\b", r"\brejilla\b", r"\btapa\s+combustible\b"]),
    ("Motor", [r"\binyector\b", r"\binyecci[oó]n\b", r"\bcig[uü]e[nñ]al\b", r"\b[aá]rbol\s+de\s+leva\b", r"\bjunta\b", r"\bsoporte\s+motor\b"]),
]


def clean_origen(val: str) -> str:
    if not val:
        return ""
    val = val.strip()
    if val.startswith("[") and val.endswith("]"):
        try:
            items = json.loads(val)
        except (ValueError, json.JSONDecodeError):
            items = []
        items = [s.strip() for s in items if isinstance(s, str) and s.strip()]
        # Heuristica: defaults a Importado para autopartes europeas (que es el caso del
        # 99% del catalogo). Si algun valor dice Nacional explicitamente, respetarlo.
        if any("nacional" in s.lower() for s in items):
            return "Nacional"
        return "Importado"
    if "nacional" in val.lower():
        return "Nacional"
    if "importado" in val.lower():
        return "Importado"
    # Strings tipo "TECNOLOGIA ALEMANA CALIDAD ORIGINAL" -> Importado.
    return "Importado"


def shorten_body(html: str) -> str:
    """Toma solo el primer parrafo. Elimina FAQ (<h3>...) y resto."""
    if not html:
        return ""
    # Cortar todo desde el primer <h3> (FAQ) en adelante.
    html = re.split(r"<h3", html, maxsplit=1, flags=re.IGNORECASE)[0]
    # Tomar primer <p>...</p>.
    m = re.search(r"<p>.*?</p>", html, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(0)
    # Sin parrafos? envolver primer 250 chars.
    txt = re.sub(r"<[^>]+>", "", html).strip()
    if not txt:
        return ""
    if len(txt) > 280:
        txt = txt[:277] + "..."
    return f"<p>{txt}</p>"


def derive_collection(filename: str, title: str, filtros_ref: str) -> str:
    if filename in FILE_TO_COLLECTION:
        return FILE_TO_COLLECTION[filename]
    if filename != "refacciones_otros.csv":
        return "Otros"
    title_l = title.lower()
    for col, patterns in OTROS_RULES:
        for pat in patterns:
            if re.search(pat, title_l, re.IGNORECASE):
                return col
    fr = (filtros_ref or "").strip()
    fr_map = {"Carrocería": "Carrocería", "Sistema Eléctrico": "Sistema eléctrico", "Motor": "Motor"}
    if fr in fr_map:
        return fr_map[fr]
    return "Otros"


def _tag_extraction_text(title: str, body_html: str) -> str:
    """Devuelve solo el titulo + el segmento 'de las marcas X' del bloque 'Aplica para...'.

    El body tiene dos fuentes ruidosas:
    - Parrafo 1: descripcion generica del tipo de parte que puede mencionar marcas
      de manera contextual (e.g., "comun en BMW y Mercedes con kilometrajes altos").
    - Parrafo 5: boilerplate de Embler que lista TODAS las marcas del catalogo.
    Solo el parrafo "Aplica para..." es deterministico (extraido del bloque
    "APLICA PARA LOS SIGUIENTES MODELOS:" del listing original) y dice exactamente
    a que marcas aplica.
    """
    pieces = [title]
    # Buscar "de las marcas BRAND, BRAND, ...," hasta la primera coma seguida de espacio+
    # palabra-no-marca (e.g., "extraidas") o un punto.
    for m in re.finditer(r"de\s+las\s+marcas\s+([^,\.]+(?:,\s*[A-ZÁÉÍÓÚÑa-záéíóúñ\-\s]+)*?)\s*,\s*extraida", body_html or "", re.IGNORECASE):
        pieces.append(m.group(1))
    if len(pieces) == 1:
        # Fallback si la frase exacta no aparece: usar el primer parrafo que contiene "Aplica".
        for p in re.findall(r"<p>(.*?)</p>", body_html or "", re.DOTALL | re.IGNORECASE):
            if re.search(r"aplica\s+para", p, re.IGNORECASE):
                pieces.append(p)
                break
    return " ".join(pieces).lower()


def derive_tags(title: str, body_html: str, marca_auto: str) -> str:
    text = f" {_tag_extraction_text(title, body_html)} "
    found = []
    for display, patterns in VEHICLE_BRAND_RULES:
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                if display not in found:
                    found.append(display)
                break
    # Anadir marca_auto si no esta (es el unico campo confiable cuando el body no menciona marcas).
    ma = (marca_auto or "").strip().lower()
    if ma in MARCA_AUTO_TO_DISPLAY:
        d = MARCA_AUTO_TO_DISPLAY[ma]
        if d not in found:
            found.append(d)
    return ", ".join(found)


def fix_file(filename: str) -> dict:
    src = os.path.join(BASE, filename)
    bkp = os.path.join(BACKUP, filename)
    shutil.copy2(src, bkp)

    with open(src, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # Cache por handle: si hay multiples filas con mismo handle (multi-imagen), solo la
    # primera tiene Title/Body/etc. Las filas adicionales solo tienen imagenes.
    counts = {"rows": len(rows), "main": 0, "type_set": 0, "tags_set": 0, "origen_fixed": 0, "body_shortened": 0}

    body_field = "Body (HTML)"
    type_field = "Type"
    tags_field = "Tags"
    origen_field = "Características - Origen (product.metafields.page_info.detail_3)"
    marca_auto_field = "Marca del auto (product.metafields.global.brand)"
    filtros_ref_field = "Filtros - Refacción (product.metafields.filters.detail_1)"

    for r in rows:
        if not r.get("Title"):
            # fila adicional de imagen, no tiene info de producto.
            continue
        counts["main"] += 1
        title = r["Title"]
        body = r.get(body_field, "")
        marca_auto = r.get(marca_auto_field, "")
        filtros_ref = r.get(filtros_ref_field, "")

        # Origen.
        old_origen = r.get(origen_field, "")
        new_origen = clean_origen(old_origen)
        if new_origen != old_origen:
            counts["origen_fixed"] += 1
        r[origen_field] = new_origen

        # Body short.
        new_body = shorten_body(body)
        if new_body != body:
            counts["body_shortened"] += 1
        r[body_field] = new_body

        # Type.
        coll = derive_collection(filename, title, filtros_ref)
        r[type_field] = coll
        counts["type_set"] += 1

        # Tags. Usamos new_body para no perder marcas mencionadas en el body antes de acortar.
        tags = derive_tags(title, body, marca_auto)
        r[tags_field] = tags
        if tags:
            counts["tags_set"] += 1

    with open(src, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return counts


def main():
    if not os.path.isdir(BACKUP):
        os.makedirs(BACKUP, exist_ok=True)
    target_files = sorted(f for f in os.listdir(BASE) if f.endswith(".csv") and f != "muestra_5_productos.csv")
    print(f"Procesando {len(target_files)} archivos en {BASE}")
    totals = {"rows": 0, "main": 0, "type_set": 0, "tags_set": 0, "origen_fixed": 0, "body_shortened": 0}
    for fn in target_files:
        c = fix_file(fn)
        for k in totals:
            totals[k] += c[k]
        print(f"  [{fn}] main={c['main']:5d} type_set={c['type_set']:5d} tags_set={c['tags_set']:5d} origen_fixed={c['origen_fixed']:5d} body_short={c['body_shortened']:5d}")
    print()
    print(f"TOTAL: main={totals['main']} type_set={totals['type_set']} tags_set={totals['tags_set']} origen_fixed={totals['origen_fixed']} body_short={totals['body_shortened']}")


if __name__ == "__main__":
    main()
