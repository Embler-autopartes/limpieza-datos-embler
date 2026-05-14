"""
Genera un .md jerarquico con la estructura de menu basada en las Smart
Collections existentes en Shopify (source: Embler-Collections.xlsx).

Estructura: marca -> categoria (group) -> subcategoria (sub_group)
con el handle de la collection de cada nodo para enlazar el menu.

Output: menu/ESTRUCTURA-MENU.md
"""

from collections import defaultdict
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "outputs/collections-matrixify/source/Embler-Collections.xlsx"
OUT = ROOT / "menu/ESTRUCTURA-MENU.md"
SHEET = "Smart Collections"


def parse_collections():
    """handle -> {brand, group, sub_group, title}"""
    wb = openpyxl.load_workbook(SOURCE, data_only=True)
    ws = wb[SHEET]
    collections = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        handle, _cmd, title = row[0], row[1], row[2]
        rule_col, _, rule_cond = row[11], row[12], row[13]
        if not handle:
            continue
        if handle not in collections:
            collections[handle] = {"title": title, "brand": None, "group": None, "sub_group": None}
        if rule_col == "Metafield: global._brand":
            collections[handle]["brand"] = rule_cond
        elif rule_col == "Metafield: global.group":
            collections[handle]["group"] = rule_cond
        elif rule_col == "Metafield: global.sub_group":
            collections[handle]["sub_group"] = rule_cond
    return collections


def build_tree(collections):
    brand_only = {}
    brand_group = defaultdict(dict)
    leafs = defaultdict(lambda: defaultdict(list))
    for h, c in collections.items():
        b, g, sg = c["brand"], c["group"], c["sub_group"]
        if b and not g and not sg:
            brand_only[b] = h
        elif b and g and not sg:
            brand_group[b][g] = h
        elif b and g and sg:
            leafs[b][g].append((sg, h))
    return brand_only, brand_group, leafs


def render_md(brand_only, brand_group, leafs):
    out = []
    # Header
    out.append("# Estructura de menu Embler — basada en Smart Collections existentes")
    out.append("")
    out.append("Documento generado automaticamente desde "
               "`outputs/collections-matrixify/source/Embler-Collections.xlsx`.")
    out.append("")
    out.append("Refleja las **895 Smart Collections** activas en Shopify:")
    out.append(f"- **{len(brand_only)} marcas** (nivel 1 — collection padre por marca)")
    out.append(f"- **{sum(len(v) for v in brand_group.values())} categorias** (nivel 2 — marca + grupo)")
    out.append(f"- **{sum(len(sgs) for groups in leafs.values() for sgs in groups.values())} subcategorias** "
               "(nivel 3 — marca + grupo + sub-grupo)")
    out.append("")
    out.append("Cada nodo del menu enlaza al handle de la collection. La jerarquia recomendada del menu es:")
    out.append("")
    out.append("```")
    out.append("Marca (nivel 1)")
    out.append("  └── Categoria (nivel 2)")
    out.append("       └── Subcategoria (nivel 3)")
    out.append("```")
    out.append("")
    out.append("---")
    out.append("")

    # Index
    out.append("## Indice de marcas")
    out.append("")
    for brand in sorted(brand_only.keys()):
        anchor = brand.lower().replace(" ", "-").replace("-", "-")
        # use brand name as visible link, slug for anchor
        slug = brand.lower().replace(" ", "-")
        n_groups = len(brand_group.get(brand, {}))
        n_subs = sum(len(sgs) for sgs in leafs.get(brand, {}).values())
        out.append(f"- [{brand}](#{slug}) — {n_groups} categorias · {n_subs} subcategorias")
    out.append("")
    out.append("---")
    out.append("")

    # Per-brand sections
    for brand in sorted(brand_only.keys()):
        slug = brand.lower().replace(" ", "-")
        out.append(f"## {brand}")
        out.append("")
        out.append(f"**Handle de marca:** `{brand_only[brand]}`")
        out.append(f"**Metafield:** `global._brand = \"{brand}\"`")
        out.append("")

        groups = brand_group.get(brand, {})
        if not groups:
            out.append("_Sin categorias hijas._")
            out.append("")
            continue

        # For each group, list sub-groups
        for group in sorted(groups.keys()):
            group_handle = groups[group]
            sg_list = sorted(leafs.get(brand, {}).get(group, []))
            out.append(f"### {brand} — {group}")
            out.append("")
            out.append(f"**Handle:** `{group_handle}`")
            out.append(f"**Metafields:** `_brand = \"{brand}\"` + `group = \"{group}\"`")
            out.append("")
            if sg_list:
                out.append(f"**Subcategorias ({len(sg_list)}):**")
                out.append("")
                out.append("| Subcategoria | Handle |")
                out.append("|--------------|--------|")
                for sg, sg_handle in sg_list:
                    out.append(f"| {sg} | `{sg_handle}` |")
            else:
                out.append("_Sin subcategorias._")
            out.append("")

        out.append("---")
        out.append("")

    return "\n".join(out)


def main():
    collections = parse_collections()
    brand_only, brand_group, leafs = build_tree(collections)

    md = render_md(brand_only, brand_group, leafs)
    OUT.write_text(md, encoding="utf-8")
    print(f"Generado: {OUT.relative_to(ROOT)}")
    print(f"  Marcas: {len(brand_only)}")
    print(f"  Categorias totales: {sum(len(v) for v in brand_group.values())}")
    print(f"  Subcategorias totales: {sum(len(sgs) for g in leafs.values() for sgs in g.values())}")


if __name__ == "__main__":
    main()
