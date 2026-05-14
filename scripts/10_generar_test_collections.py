"""
Genera un Excel de prueba con ~8 smart collections para Matrixify.

Selecciona collections de los 3 niveles que apunten a productos ya
importados a Shopify (categorias: accesorios, herramientas, otros).
Asi se puede validar que las reglas conectan con los metafields antes
de subir el Excel completo de 895 collections.

Salida: outputs/YYYY-MM-DD-test-collections-matrixify/Embler-Collections-Test.xlsx
"""
import re
import unicodedata
from datetime import date
from pathlib import Path

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "outputs" / f"{date.today().isoformat()}-test-collections-matrixify"
OUT_FILE = OUT_DIR / "Embler-Collections-Test.xlsx"

RULE_MARCA = "Metafield: global._brand"
RULE_GRUPO = "Metafield: global.group"
RULE_SUB = "Metafield: global.sub_group"

SORT_ORDER = "Best Selling"
COMMAND = "NEW"
MUST_MATCH = "all conditions"
PUBLISHED = True
PUBLISHED_SCOPE = "web"

HEADERS = [
    "Handle", "Command", "Title", "Body HTML",
    "Sort Order", "Template Suffix", "Published", "Published Scope",
    "Image Src", "Image Alt Text",
    "Must Match", "Rule: Product Column", "Rule: Relation", "Rule: Condition",
]

# Lista de prueba: (nivel, marca, grupo, sub) — grupo/sub vacios = no aplica
TEST_COLLECTIONS = [
    # Nivel 1 (Marca) — recoge muchos productos de varias categorias
    (1, "BMW",            None, None),            # ~232 prods importados
    (1, "Mercedes-Benz",  None, None),            # ~87 prods importados
    # Nivel 2 (Marca + Grupo)
    (2, "BMW",            "Accesorios", None),    # ~76 prods
    (2, "BMW",            "Herramientas", None),  # ~14 prods
    (2, "Mercedes-Benz",  "Suspensión de aire", None),  # ~12 prods
    # Nivel 3 (Marca + Grupo + Sub)
    (3, "BMW",            "Accesorios", "Cantoneras"),  # ~55 prods
    (3, "BMW",            "Motor",       "Poleas"),     # ~19 prods
    (3, "Audi",           "Accesorios",  "Llaveros"),   # ~3 prods
]


def slugify(t):
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def base_row(handle, title):
    return {
        "Handle": handle, "Command": COMMAND, "Title": title, "Body HTML": "",
        "Sort Order": SORT_ORDER, "Template Suffix": "",
        "Published": PUBLISHED, "Published Scope": PUBLISHED_SCOPE,
        "Image Src": "", "Image Alt Text": "",
        "Must Match": MUST_MATCH,
    }


def rule_row(handle, title, col, cond):
    return {
        "Handle": handle, "Command": COMMAND, "Title": title,
        "Sort Order": SORT_ORDER,
        "Published": PUBLISHED, "Published Scope": PUBLISHED_SCOPE,
        "Must Match": MUST_MATCH,
        "Rule: Product Column": col, "Rule: Relation": "Equals", "Rule: Condition": cond,
    }


def build():
    rows = []
    for nivel, marca, grupo, sub in TEST_COLLECTIONS:
        if nivel == 1:
            h = slugify(marca); t = marca
            r = base_row(h, t)
            r.update({"Rule: Product Column": RULE_MARCA, "Rule: Relation": "Equals", "Rule: Condition": marca})
            rows.append(r)
        elif nivel == 2:
            h = f"{slugify(marca)}-{slugify(grupo)}"; t = f"{marca} - {grupo}"
            r = base_row(h, t)
            r.update({"Rule: Product Column": RULE_MARCA, "Rule: Relation": "Equals", "Rule: Condition": marca})
            rows.append(r)
            rows.append(rule_row(h, t, RULE_GRUPO, grupo))
        else:
            h = f"{slugify(marca)}-{slugify(grupo)}-{slugify(sub)}"
            t = f"{marca} - {grupo} - {sub}"
            r = base_row(h, t)
            r.update({"Rule: Product Column": RULE_MARCA, "Rule: Relation": "Equals", "Rule: Condition": marca})
            rows.append(r)
            rows.append(rule_row(h, t, RULE_GRUPO, grupo))
            rows.append(rule_row(h, t, RULE_SUB, sub))
    return rows


def main():
    rows = build()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    wb = Workbook(); ws = wb.active; ws.title = "Smart Collections"
    ws.append(HEADERS)
    for r in rows:
        ws.append([r.get(h, "") for h in HEADERS])
    wb.save(OUT_FILE)

    handles = {r["Handle"] for r in rows}
    print(f"Collections: {len(handles)}  filas: {len(rows)}")
    for nivel, marca, grupo, sub in TEST_COLLECTIONS:
        suffix = "" if not grupo else (f" - {grupo}" + ("" if not sub else f" - {sub}"))
        print(f"  N{nivel}  {marca}{suffix}")
    print(f"\nArchivo: {OUT_FILE}")


if __name__ == "__main__":
    main()
