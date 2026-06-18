#!/usr/bin/env python3
"""
PREVIEW del nuevo mega menu: Marca -> Sistema (TecDoc) -> Subgrupo (MX).
Reagrupa las collections (marca, grupo, subgrupo) existentes bajo su sistema TecDoc.
NO toca Shopify. Genera menu/MENU-TECDOC-PROPUESTA.md para confirmar.
"""
import csv
from collections import defaultdict
from pathlib import Path
import openpyxl

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "Procesamiento de Catálogo/outputs/collections-matrixify/source/Embler-Collections.xlsx"
HOMOL = Path(__file__).resolve().parent / "homologacion.csv"
OUT = ROOT / "menu" / "MENU-TECDOC-PROPUESTA.md"

BRAND_LABELS = [
    ("BMW","BMW"),("Mercedes Benz","Mercedes-Benz"),("Audi","Audi"),("Mini Cooper","Mini"),
    ("Porsche","Porsche"),("Smart","Smart"),("Volkswagen","Volkswagen"),("Bentley","Bentley"),
    ("Fiat","Fiat"),("Jaguar","Jaguar"),("Land Rover","Land Rover"),("Seat","Seat"),("Volvo","Volvo"),
]

# (grupo, subgrupo) -> sistema TecDoc
SIS = {}
for r in csv.DictReader(open(HOMOL, encoding="utf-8")):
    SIS[(r["grupo_embler"], r["subgrupo_embler"])] = r["tecdoc_sistema"]

def parse_collections():
    wb = openpyxl.load_workbook(SOURCE, data_only=True)
    ws = wb["Smart Collections"]
    cols = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        handle = row[0]; rule_col, _, rule_cond = row[11], row[12], row[13]
        if not handle: continue
        c = cols.setdefault(handle, {"brand": None, "group": None, "sub_group": None})
        if rule_col == "Metafield: global._brand": c["brand"] = rule_cond
        elif rule_col == "Metafield: global.group": c["group"] = rule_cond
        elif rule_col == "Metafield: global.sub_group": c["sub_group"] = rule_cond
    return cols

cols = parse_collections()
# brand -> sistema -> set(subgrupos)  (solo collections hoja con subgrupo)
tree = defaultdict(lambda: defaultdict(set))
sin_sis = set()
for h, c in cols.items():
    b, g, sg = c["brand"], c["group"], c["sub_group"]
    if not (b and g and sg): continue
    sis = SIS.get((g, sg))
    if not sis:
        sin_sis.add((g, sg)); continue
    tree[b][sis].add(sg)

lines = ["# Mega menú propuesto — Marca → Sistema (TecDoc) → Subgrupo\n",
         "Reagrupación de los subgrupos MX actuales bajo su sistema TecDoc. Los subgrupos (hojas)",
         "conservan su nombre y su collection actual; el nivel intermedio pasa de Grupo MX a **Sistema TecDoc**.\n"]
total_items = 0
for label, bkey in BRAND_LABELS:
    sismap = tree.get(bkey, {})
    if not sismap: continue
    n_sis = len(sismap); n_sub = sum(len(s) for s in sismap.values())
    total_items += 1 + n_sis + n_sub
    lines.append(f"\n## {label}  ({n_sis} sistemas, {n_sub} subgrupos)")
    for sis in sorted(sismap):
        subs = sorted(sismap[sis])
        lines.append(f"- **{sis}** ({len(subs)})")
        for sg in subs:
            lines.append(f"    - {sg}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"Marcas: {sum(1 for _,b in BRAND_LABELS if tree.get(b))}")
print(f"Items totales del menu (marca+sistema+subgrupo): {total_items}")
print(f"Combos (grupo,subgrupo) sin sistema en homologacion: {len(sin_sis)}")
if sin_sis:
    for k in sorted(sin_sis)[:10]: print("   ", k)
print(f"\nResumen por marca:")
for label, bkey in BRAND_LABELS:
    sm = tree.get(bkey, {})
    if sm:
        print(f"  {label:<14} {len(sm):>2} sistemas, {sum(len(s) for s in sm.values()):>3} subgrupos")
print(f"\nPreview: {OUT}")
