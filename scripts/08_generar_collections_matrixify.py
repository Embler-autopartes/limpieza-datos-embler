"""
Genera el archivo Excel de Smart Collections para importar con Matrixify.

Lee outputs/2026-05-09-USAR-shopify-import/ para extraer combinaciones
unicas Marca x Grupo x Sub Grupo y arma 3 niveles de smart collections:

  Nivel 1: por Marca           (regla: Marca)
  Nivel 2: por Marca + Grupo   (reglas: Marca + Grupo)
  Nivel 3: por Marca + Grupo + Sub Grupo  (3 reglas)

Cada collection con N reglas ocupa N filas (mismo Handle/Title repetido).

Salida: outputs/YYYY-MM-DD-collections-matrixify/Embler-Collections.xlsx
"""
import csv
import os
import re
import unicodedata
from collections import defaultdict
from datetime import date
from pathlib import Path

from openpyxl import Workbook

csv.field_size_limit(2**31 - 1)

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "outputs" / "2026-05-09-USAR-shopify-import"
OUT_DIR = ROOT / "outputs" / f"{date.today().isoformat()}-collections-matrixify"
OUT_FILE = OUT_DIR / "Embler-Collections.xlsx"

COL_MARCA = "Marca (product.metafields.global._brand)"
COL_GRUPO = "Grupo (product.metafields.global.group)"
COL_SUB = "Sub grupo (product.metafields.global.sub_group)"

# --- Sintaxis de Matrixify para reglas con metafields ---
# Doc: https://matrixify.app/documentation/smart-collections/
# Formato correcto: "Metafield: <namespace>.<key>"  (sin "Product ", sin "[string]")
RULE_MARCA = "Metafield: global._brand"
RULE_GRUPO = "Metafield: global.group"
RULE_SUB = "Metafield: global.sub_group"

SORT_ORDER = "Best Selling"
COMMAND = "NEW"           # cambiar a MERGE si se quiere idempotencia en re-runs
MUST_MATCH = "all conditions"
PUBLISHED = True
PUBLISHED_SCOPE = "web"

HEADERS = [
    "Handle",
    "Command",
    "Title",
    "Body HTML",
    "Sort Order",
    "Template Suffix",
    "Published",
    "Published Scope",
    "Image Src",
    "Image Alt Text",
    "Must Match",
    "Rule: Product Column",
    "Rule: Relation",
    "Rule: Condition",
]


def slugify(text):
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def collect_tree():
    tree = defaultdict(lambda: defaultdict(set))
    for fname in sorted(SRC_DIR.glob("*.csv")):
        with fname.open(encoding="utf-8", newline="") as f:
            r = csv.DictReader(f)
            for row in r:
                if not row.get("Title", "").strip():
                    continue
                marca = (row.get(COL_MARCA) or "").strip()
                grupo = (row.get(COL_GRUPO) or "").strip()
                sub = (row.get(COL_SUB) or "").strip()
                if not marca:
                    continue
                tree[marca]  # asegurar nivel 1
                if grupo:
                    tree[marca][grupo]
                    if sub:
                        tree[marca][grupo].add(sub)
    return tree


def build_rows(tree):
    rows = []
    counts = {"l1": 0, "l2": 0, "l3": 0}

    for marca in sorted(tree.keys()):
        # Nivel 1
        h1 = slugify(marca)
        rows.append({
            "Handle": h1,
            "Command": COMMAND,
            "Title": marca,
            "Body HTML": "",
            "Sort Order": SORT_ORDER,
            "Template Suffix": "",
            "Published": PUBLISHED,
            "Published Scope": PUBLISHED_SCOPE,
            "Image Src": "",
            "Image Alt Text": "",
            "Must Match": MUST_MATCH,
            "Rule: Product Column": RULE_MARCA,
            "Rule: Relation": "Equals",
            "Rule: Condition": marca,
        })
        counts["l1"] += 1

        for grupo in sorted(tree[marca].keys()):
            h2 = f"{slugify(marca)}-{slugify(grupo)}"
            t2 = f"{marca} - {grupo}"
            rows.append({
                "Handle": h2,
                "Command": COMMAND, "Title": t2, "Body HTML": "",
                "Sort Order": SORT_ORDER, "Template Suffix": "",
                "Published": PUBLISHED, "Published Scope": PUBLISHED_SCOPE,
                "Image Src": "", "Image Alt Text": "",
                "Must Match": MUST_MATCH,
                "Rule: Product Column": RULE_MARCA,
                "Rule: Relation": "Equals",
                "Rule: Condition": marca,
            })
            rows.append({
                "Handle": h2,
                "Command": COMMAND, "Title": t2,
                "Sort Order": SORT_ORDER,
                "Published": PUBLISHED, "Published Scope": PUBLISHED_SCOPE,
                "Must Match": MUST_MATCH,
                "Rule: Product Column": RULE_GRUPO,
                "Rule: Relation": "Equals",
                "Rule: Condition": grupo,
            })
            counts["l2"] += 1

            for sub in sorted(tree[marca][grupo]):
                h3 = f"{slugify(marca)}-{slugify(grupo)}-{slugify(sub)}"
                t3 = f"{marca} - {grupo} - {sub}"
                rows.append({
                    "Handle": h3,
                    "Command": COMMAND, "Title": t3, "Body HTML": "",
                    "Sort Order": SORT_ORDER, "Template Suffix": "",
                    "Published": PUBLISHED, "Published Scope": PUBLISHED_SCOPE,
                    "Image Src": "", "Image Alt Text": "",
                    "Must Match": MUST_MATCH,
                    "Rule: Product Column": RULE_MARCA,
                    "Rule: Relation": "Equals",
                    "Rule: Condition": marca,
                })
                rows.append({
                    "Handle": h3,
                    "Command": COMMAND, "Title": t3,
                    "Sort Order": SORT_ORDER,
                    "Published": PUBLISHED, "Published Scope": PUBLISHED_SCOPE,
                    "Must Match": MUST_MATCH,
                    "Rule: Product Column": RULE_GRUPO,
                    "Rule: Relation": "Equals",
                    "Rule: Condition": grupo,
                })
                rows.append({
                    "Handle": h3,
                    "Command": COMMAND, "Title": t3,
                    "Sort Order": SORT_ORDER,
                    "Published": PUBLISHED, "Published Scope": PUBLISHED_SCOPE,
                    "Must Match": MUST_MATCH,
                    "Rule: Product Column": RULE_SUB,
                    "Rule: Relation": "Equals",
                    "Rule: Condition": sub,
                })
                counts["l3"] += 1

    return rows, counts


def detect_handle_collisions(rows):
    title_by_handle = defaultdict(set)
    for r in rows:
        title_by_handle[r["Handle"]].add(r["Title"])
    collisions = {h: ts for h, ts in title_by_handle.items() if len(ts) > 1}
    return collisions


def write_xlsx(rows):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "Smart Collections"
    ws.append(HEADERS)
    for r in rows:
        ws.append([r.get(h, "") for h in HEADERS])
    wb.save(OUT_FILE)


def main():
    print(f"Leyendo {SRC_DIR}...")
    tree = collect_tree()
    n_marcas = len(tree)
    n_grupos = sum(len(g) for g in tree.values())
    n_subs = sum(len(s) for g in tree.values() for s in g.values())
    print(f"  marcas={n_marcas}  grupos_unicos_x_marca={n_grupos}  subgrupos_x_marca_grupo={n_subs}")

    rows, counts = build_rows(tree)
    print(f"\nCollections:")
    print(f"  Nivel 1 (Marca):                {counts['l1']}")
    print(f"  Nivel 2 (Marca+Grupo):          {counts['l2']}")
    print(f"  Nivel 3 (Marca+Grupo+Sub):      {counts['l3']}")
    print(f"  TOTAL:                          {counts['l1']+counts['l2']+counts['l3']}")
    print(f"  Total filas en Excel:           {len(rows)}")

    collisions = detect_handle_collisions(rows)
    if collisions:
        print(f"\n!! HANDLES con multiples titulos (revisar): {len(collisions)}")
        for h, ts in list(collisions.items())[:5]:
            print(f"   {h} -> {ts}")
    else:
        print("\nOK: handles unicos por collection.")

    write_xlsx(rows)
    print(f"\nArchivo escrito: {OUT_FILE}")


if __name__ == "__main__":
    main()
