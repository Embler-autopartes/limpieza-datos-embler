# -*- coding: utf-8 -*-
"""
Genera la sección Compatibilidades para los productos que NO la tienen,
parseando la columna cruda `Compatibilidades` (formato MercadoLibre) de los
archivos en `bases finales mayo/`. Match por shopify_handle == Handle.

Formato de salida (igual al catálogo):
   <h2>Compatibilidades</h2><ul><li>BMW X1 xDrive2.5i 2010-2013 — 6 cil 2.5L Aspiración natural</li>...</ul>

Uso:
    python scripts/19_compat_desde_bases.py --sample 8
    python scripts/19_compat_desde_bases.py --run     # reescribe el catálogo
"""
import csv
import re
import os
import sys
import glob
from collections import defaultdict, OrderedDict

csv.field_size_limit(10 ** 9)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEWDIR = os.path.join(BASE, "Procesamiento de Catálogo", "outputs",
                      "2026-06-17-descripciones-reescritas")
# lee la salida intermedia de scripts/18 y produce el archivo canónico
CATALOGO = os.path.join(NEWDIR, "catalogo_reescrito_intermedio.csv")
OUTPUT = os.path.join(NEWDIR, "catalogo_completo_final_reescrito.csv")
BASES = os.path.join(BASE, "bases finales mayo")

BRANDS = [
    ("Mercedes Benz", ("mercedes-benz", "mercedes benz", "mercedes")),
    ("Land Rover", ("land rover", "land-rover")),
    ("Alfa Romeo", ("alfa romeo",)),
    ("Rolls-Royce", ("rolls royce", "rolls-royce")),
    ("BMW", ("bmw",)),
    ("Audi", ("audi",)),
    ("Volkswagen", ("volkswagen", "vw")),
    ("Porsche", ("porsche", "porche")),
    ("Volvo", ("volvo",)),
    ("Mini", ("mini cooper", "mini")),
    ("Jaguar", ("jaguar",)),
    ("SEAT", ("seat",)),
    ("Smart", ("smart",)),
    ("Fiat", ("fiat",)),
    ("Bentley", ("bentley",)),
    ("Maserati", ("maserati",)),
    ("Aston Martin", ("aston martin", "aston-martin")),
    # No europeas (p. ej. bolsas de suspensión de aire para camionetas americanas)
    ("Cadillac", ("cadillac",)),
    ("Chevrolet", ("chevrolet", "chevy")),
    ("Ford", ("ford",)),
    ("Lincoln", ("lincoln",)),
    ("Jeep", ("jeep",)),
    ("Dodge", ("dodge",)),
    ("RAM", ("ram",)),
    ("Chrysler", ("chrysler",)),
    ("GMC", ("gmc",)),
    ("Buick", ("buick",)),
    ("Hummer", ("hummer",)),
    ("Pontiac", ("pontiac",)),
    ("Tesla", ("tesla",)),
    ("Toyota", ("toyota",)),
    ("Lexus", ("lexus",)),
    ("Honda", ("honda",)),
    ("Acura", ("acura",)),
    ("Nissan", ("nissan",)),
    ("Infiniti", ("infiniti",)),
    ("Mazda", ("mazda",)),
    ("Mitsubishi", ("mitsubishi",)),
    ("Subaru", ("subaru",)),
    ("Hyundai", ("hyundai",)),
    ("Kia", ("kia",)),
    ("Suzuki", ("suzuki",)),
    ("Peugeot", ("peugeot",)),
    ("Renault", ("renault",)),
    ("Citroën", ("citroen", "citroën")),
]
ASP = [
    ("scroll twin turbo", "Scroll Twin-Turbo"), ("twin turbo", "Twin-Turbo"),
    ("biturbo", "Bi-Turbo"), ("bi turbo", "Bi-Turbo"), ("bi-turbo", "Bi-Turbo"),
    ("turbocargado", "Turbo"), ("turbo", "Turbo"),
    ("aspirado", "Aspiración natural"),
]
RX_ENGINE = re.compile(r"(\d+(?:\.\d+)?)\s*L\s+([LVHWBR])(\d+)", re.I)
RX_YEAR = re.compile(r"\b(19|20)\d\d\b")
RX_MLM = re.compile(r"MLM\d+\s*\|?\s*", re.I)


def detect_brand(s):
    low = s.lower()
    for canon, variants in BRANDS:
        for v in variants:
            if low.startswith(v + " "):
                return canon, s[len(v):].strip()
    return None, s


def aspiracion(s):
    low = s.lower()
    for k, v in ASP:
        if k in low:
            base = v
            if "diesel" in low:
                base += "-Diésel" if "natural" not in v else " (Diésel)"
            return base
    if "diesel" in low:
        return "Diésel"
    return ""


def parse_entry(s):
    brand, resto = detect_brand(s)
    if not brand:
        return None
    ym = RX_YEAR.search(resto)
    if not ym:
        return None
    modelo = resto[:ym.start()].strip()
    anio = ym.group(0)
    cola = resto[ym.end():].strip()
    # trim = entre el anio y "Mexico"/"México" (o hasta el motor)
    mtrim = re.split(r"\bm[eé]xico\b", cola, maxsplit=1, flags=re.I)
    trim = mtrim[0].strip() if mtrim else ""
    em = RX_ENGINE.search(resto)
    disp = em.group(1) if em else ""
    cil = em.group(3) if em else ""
    asp = aspiracion(resto)
    # limpiar trim de ruido comun
    trim = re.sub(r"\b(asistida|cremallera|rwd|awd|fwd|4matic|xdrive|quattro)\b.*$", "",
                  trim, flags=re.I).strip()
    trim = re.sub(r"\s+", " ", trim).strip(" .-")
    modelo = re.sub(r"\s+", " ", modelo).strip()
    return {"brand": brand, "modelo": modelo, "trim": trim,
            "anio": int(anio), "disp": disp, "cil": cil, "asp": asp}


def split_raw(raw):
    parts = RX_MLM.split(raw)
    out = []
    for p in parts:
        p = p.strip()
        if p and detect_brand(p)[0]:
            out.append(p)
    return out


def collapse_years(years):
    ys = sorted(set(years))
    rangos = []
    i = 0
    while i < len(ys):
        j = i
        while j + 1 < len(ys) and ys[j + 1] == ys[j] + 1:
            j += 1
        rangos.append(str(ys[i]) if i == j else "%d-%d" % (ys[i], ys[j]))
        i = j + 1
    return ", ".join(rangos)


def bullets_from_raw(raw):
    veh = [parse_entry(e) for e in split_raw(raw)]
    veh = [v for v in veh if v]
    if not veh:
        return []
    grupos = OrderedDict()
    for v in veh:
        key = (v["brand"], v["modelo"], v["trim"], v["disp"], v["cil"], v["asp"])
        grupos.setdefault(key, []).append(v["anio"])
    lis = []
    for (brand, modelo, trim, disp, cil, asp), years in grupos.items():
        nombre = " ".join(x for x in (brand, modelo, trim) if x)
        rng = collapse_years(years)
        motor = ""
        if cil and disp:
            motor = " — %s cil %sL%s" % (cil, disp, (" " + asp) if asp else "")
        elif disp:
            motor = " — %sL%s" % (disp, (" " + asp) if asp else "")
        lis.append("%s %s%s" % (nombre, rng, motor))
    # dedupe preservando orden
    seen = set()
    return [x for x in lis if not (x in seen or seen.add(x))]


def load_compat_lookup():
    lut = {}
    for fp in glob.glob(os.path.join(BASES, "*.csv")):
        with open(fp, encoding="utf-8") as f:
            r = csv.DictReader(f)
            if "shopify_handle" not in r.fieldnames:
                continue
            for row in r:
                h = (row.get("shopify_handle") or "").strip()
                raw = (row.get("Compatibilidades") or "").strip()
                if h and raw and h not in lut:
                    lut[h] = raw
    return lut


def compat_html(raw):
    lis = bullets_from_raw(raw)
    if not lis:
        return ""
    html = "<h2>Compatibilidades</h2><ul>" + "".join(
        "<li>%s</li>" % x for x in lis) + "</ul>"
    return html.replace("Mercedes-Benz", "Mercedes Benz")


def insert_compat(body, html_compat):
    """Inserta Compatibilidades como primera sección (antes de Antes de Comprar)."""
    if "<h2>Compatibilidades</h2>" in body or not html_compat:
        return body
    m = re.search(r"<h2>", body)
    if not m:
        return html_compat + body
    return body[:m.start()] + html_compat + body[m.start():]


def run_sample(n=8):
    lut = load_compat_lookup()
    shown = 0
    with open(CATALOGO, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            b = r["Body (HTML)"]
            if not b.strip() or "<h2>Compatibilidades</h2>" in b:
                continue
            raw = lut.get(r["Handle"])
            if not raw:
                continue
            lis = bullets_from_raw(raw)
            if not lis:
                continue
            print("#### ", r["Title"][:60])
            for x in lis[:12]:
                print("   •", x)
            if len(lis) > 12:
                print("   … (%d más)" % (len(lis) - 12))
            print()
            shown += 1
            if shown >= n:
                break


def run_full():
    lut = load_compat_lookup()
    with open(CATALOGO, encoding="utf-8", newline="") as fin, \
         open(OUTPUT, "w", encoding="utf-8", newline="") as fout:
        r = csv.DictReader(fin)
        w = csv.DictWriter(fout, fieldnames=r.fieldnames)
        w.writeheader()
        rellenados = 0
        for row in r:
            b = row["Body (HTML)"]
            if b and b.strip() and "<h2>Compatibilidades</h2>" not in b:
                raw = lut.get(row["Handle"])
                if raw:
                    html = compat_html(raw)
                    if html:
                        row["Body (HTML)"] = insert_compat(b, html)
                        rellenados += 1
            w.writerow(row)
    print("Compatibilidades rellenadas:", rellenados)
    print("Salida:", OUTPUT)


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--run" in a:
        run_full()
    elif "--sample" in a:
        i = a.index("--sample")
        n = int(a[i + 1]) if i + 1 < len(a) and a[i + 1].isdigit() else 8
        run_sample(n)
    else:
        print(__doc__)
