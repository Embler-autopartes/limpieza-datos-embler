#!/usr/bin/env python3
"""
PREVIEW LEAN del mega menu: Marca -> top N Sistemas TecDoc (por volumen) -> top 3 Subgrupos.
Usa conteos reales de _arbol_marca_grupo_subgrupo.json. NO toca Shopify.
"""
import csv, json
from collections import defaultdict
from pathlib import Path

ROOT = Path("..").resolve()
ARBOL = json.load(open(ROOT / "Procesamiento de Catálogo/outputs/_arbol_marca_grupo_subgrupo.json", encoding="utf-8"))
SIS = {}
for r in csv.DictReader(open("homologacion.csv", encoding="utf-8")):
    SIS[(r["grupo_embler"], r["subgrupo_embler"])] = r["tecdoc_sistema"]

CAP_SIS = 8   # sistemas por marca
CAP_SUB = 3   # subgrupos por sistema

BRAND_ORDER = ["BMW","Mercedes-Benz","Audi","Mini","Porsche","Smart","Volkswagen",
               "Bentley","Fiat","Jaguar","Land Rover","Seat","Volvo"]

OUT = ROOT / "menu" / "MENU-TECDOC-LEAN.md"
lines = [f"# Mega menú LEAN — Marca → Sistema (top {CAP_SIS}) → Subgrupo (top {CAP_SUB})\n",
         f"Tope: {CAP_SIS} sistemas/marca y {CAP_SUB} subgrupos/sistema, ambos por volumen de producto.",
         "Los sistemas/subgrupos fuera del tope NO desaparecen del catálogo ni de las collections; solo no salen en el menú.\n"]
total = 0
for b in BRAND_ORDER:
    gs = ARBOL.get(b)
    if not gs: continue
    # (sistema) -> (subgrupo -> count)
    sis = defaultdict(lambda: defaultdict(int))
    for g, subs in gs.items():
        for sg, n in subs.items():
            s = SIS.get((g, sg))
            if s: sis[s][sg] += n
    sis_tot = {s: sum(d.values()) for s, d in sis.items()}
    top_sis = sorted(sis_tot, key=lambda x: -sis_tot[x])[:CAP_SIS]
    total += 1 + len(top_sis)
    lines.append(f"\n## {b}")
    for s in top_sis:
        subs = sorted(sis[s].items(), key=lambda x: -x[1])[:CAP_SUB]
        total += len(subs)
        lines.append(f"- **{s}** ({sis_tot[s]} prod)")
        for sg, n in subs:
            lines.append(f"    - {sg} ({n})")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"Items totales del menu LEAN: {total}")
print(f"Preview: {OUT}")
