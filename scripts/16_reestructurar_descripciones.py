# -*- coding: utf-8 -*-
"""
Reestructura la columna Body (HTML) del catalogo Shopify:

1. Reordena las secciones <h2> a:
      Compatibilidades -> Antes de Comprar -> Envio ->
      Politica de Devolucion -> Descripcion -> Preguntas Frecuentes
   (cualquier otra seccion desconocida se conserva al final)

2. Limpia la seccion Descripcion para acortarla, quitando texto redundante
   que ya aparece en otras secciones:
      - Parrafos "Compatible con N configuraciones..."  -> se eliminan
        (ya esta en Compatibilidades)
      - Parrafo "Especificaciones de referencia: ..."   -> se deja solo la
        primera frase (los numeros de parte), se quita la explicacion generica
      - Parrafo "Marca Frey/Embler... garantia... DHL... devoluciones" -> se
        deja solo la primera frase (marca/calidad), se quita la logistica
        (ya esta en Envio y Politica de Devolucion)

Uso:
    python 16_reestructurar_descripciones.py --sample [N]   # muestra antes/despues
    python 16_reestructurar_descripciones.py --run          # genera CSV nuevo
"""
import csv
import re
import sys
import os

csv.field_size_limit(10 ** 9)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT = os.path.join(
    BASE, "Procesamiento de Catálogo", "outputs", "2026-06-12",
    "catalogo_completo_final.csv",
)
OUTPUT = os.path.join(
    BASE, "Procesamiento de Catálogo", "outputs", "2026-06-12",
    "catalogo_completo_final_reestructurado.csv",
)

# Orden deseado de las secciones
ORDER = [
    "Compatibilidades",
    "Antes de Comprar",
    "Envio",
    "Politica de Devolucion",
    "Descripcion",
    "Preguntas Frecuentes",
]


def split_sections(html):
    """Devuelve lista [(titulo, contenido_html), ...] y el preludio antes del 1er <h2>."""
    parts = re.split(r"(<h2>.*?</h2>)", html, flags=re.S)
    preludio = parts[0]
    sections = []
    for i in range(1, len(parts), 2):
        title = re.sub(r"</?h2>", "", parts[i]).strip()
        content = parts[i + 1] if i + 1 < len(parts) else ""
        sections.append((title, content))
    return preludio, sections


def first_sentence(text):
    """Primera frase (hasta el primer punto seguido de espacio o fin)."""
    m = re.match(r"\s*(.*?\.)(?:\s|$)", text, re.S)
    return m.group(1).strip() if m else text.strip()


def clean_descripcion(content):
    """Limpia el contenido de la seccion Descripcion segun las reglas."""
    paras = re.findall(r"<p>(.*?)</p>", content, re.S)
    out = []
    for p in paras:
        s = p.strip()
        low = s.lower()
        if low.startswith("compatible con"):
            # redundante con Compatibilidades -> eliminar
            continue
        if low.startswith("especificaciones de referencia"):
            # dejar solo la frase con los numeros de parte
            out.append(first_sentence(s))
            continue
        if low.startswith("marca original") or low.startswith("marca embler"):
            # dejar solo la frase de marca/calidad, quitar logistica
            out.append(first_sentence(s))
            continue
        out.append(s)
    return "".join("<p>%s</p>" % p for p in out)


def restructure(html):
    if not html or not html.strip():
        return html
    preludio, sections = split_sections(html)
    by_title = {}
    extras = []  # secciones desconocidas, en orden de aparicion
    for title, content in sections:
        if title == "Descripcion":
            content = clean_descripcion(content)
        if title in ORDER:
            by_title[title] = content
        else:
            extras.append((title, content))

    new = preludio
    for title in ORDER:
        if title in by_title:
            new += "<h2>%s</h2>%s" % (title, by_title[title])
    for title, content in extras:
        new += "<h2>%s</h2>%s" % (title, content)
    return new


def run_sample(n=4):
    """Imprime antes/despues de N productos diversos."""
    wanted_prefixes = ["Parrilla", "Balatas", "Sensor", "Disco", "Bobina", "Defensa"]
    shown = 0
    used = set()
    with open(INPUT, encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            b = row["Body (HTML)"]
            if not b.strip():
                continue
            title = row["Title"]
            key = next((p for p in wanted_prefixes if title.startswith(p)), None)
            if key is None or key in used:
                continue
            used.add(key)
            after = restructure(b)
            print("=" * 90)
            print("PRODUCTO:", title)
            print("LONGITUD:  antes %d  ->  despues %d  (%.0f%% del original)"
                  % (len(b), len(after), 100.0 * len(after) / len(b)))
            print("-" * 40, "ANTES", "-" * 40)
            print(b)
            print("-" * 40, "DESPUES", "-" * 38)
            print(after)
            print()
            shown += 1
            if shown >= n:
                break


def run_full():
    with open(INPUT, encoding="utf-8", newline="") as fin, \
         open(OUTPUT, "w", encoding="utf-8", newline="") as fout:
        r = csv.DictReader(fin)
        w = csv.DictWriter(fout, fieldnames=r.fieldnames)
        w.writeheader()
        changed = 0
        total = 0
        for row in r:
            total += 1
            b = row["Body (HTML)"]
            if b and b.strip():
                nb = restructure(b)
                if nb != b:
                    changed += 1
                row["Body (HTML)"] = nb
            w.writerow(row)
    print("Filas totales:", total)
    print("Body reestructurados:", changed)
    print("Salida:", OUTPUT)


if __name__ == "__main__":
    if "--run" in sys.argv:
        run_full()
    elif "--sample" in sys.argv:
        i = sys.argv.index("--sample")
        n = int(sys.argv[i + 1]) if i + 1 < len(sys.argv) and sys.argv[i + 1].isdigit() else 4
        run_sample(n)
    else:
        print(__doc__)
