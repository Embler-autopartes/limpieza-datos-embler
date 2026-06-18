#!/usr/bin/env python3
"""Extrae el arbol COMPLETO de categorias (assembly groups) de TecDoc.
Genera categorias_tecdoc.json con la jerarquia + conteo de articulos en nuestra data."""
import json, requests, warnings
warnings.filterwarnings("ignore")

ENDPOINT = "https://webservice.tecalliance.services/pegasus-3-0/services/TecdocToCatDLB.jsonEndpoint"
HEADERS = {"Content-Type": "application/json", "X-Api-Key": "2BeBXg6QmtGt4CMfNLSsgPX2VcPAHnbuKuf45oU7tQmYaCwHCYY4"}
BASE = {"provider": 25099, "lang": "qd"}

def call(fn, extra):
    r = requests.post(ENDPOINT, json={fn: {**BASE, **extra}}, headers=HEADERS, timeout=60)
    return r.json()

# 1) ShortCuts = sistemas de nivel superior
shortcuts = call("getShortCuts2", {"articleCountry": "MX", "linkingTargetType": "P"}).get("data", {}).get("array", [])
print(f"ShortCuts (sistemas nivel superior): {len(shortcuts)}")
for s in shortcuts:
    print(f"   {s['shortCutId']:>3}  {s['shortCutName']}")

# 2) Arbol COMPLETO de assembly groups via facets de getArticles (includeCompleteTree)
print("\nExtrayendo arbol completo de assembly groups...")
resp = call("getArticles", {
    "articleCountry": "MX", "perPage": 0, "page": 1,
    "assemblyGroupFacetOptions": {"enabled": True, "assemblyGroupType": "P", "includeCompleteTree": True},
})
facets = resp.get("assemblyGroupFacets", {})
nodes = facets.get("counts", [])
print(f"Total nodos en arbol (con articulos en nuestras 5 marcas): {len(nodes)}")

# Construir indice y jerarquia
by_id = {}
for n in nodes:
    by_id[n["assemblyGroupNodeId"]] = {
        "id": n["assemblyGroupNodeId"],
        "name": n.get("assemblyGroupName", ""),
        "parent": n.get("parentNodeId"),
        "count": n.get("count", n.get("ccount", 0)),
        "children": [],
    }
roots = []
for nid, node in by_id.items():
    p = node["parent"]
    if p in by_id:
        by_id[p]["children"].append(node)
    else:
        roots.append(node)

# Ordenar por nombre
def sort_tree(nodes):
    nodes.sort(key=lambda x: x["name"])
    for n in nodes:
        sort_tree(n["children"])
sort_tree(roots)

out = {
    "shortcuts": shortcuts,
    "total_nodos": len(nodes),
    "raices": len(roots),
    "arbol": roots,
}
with open("categorias_tecdoc.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\nRaices del arbol: {len(roots)}")

# Imprimir arbol resumido (2 niveles) para vista rapida
def show(nodes, depth=0, max_depth=1):
    for n in nodes:
        print("  " * depth + f"- {n['name']} (id={n['id']}, {n['count']} art)")
        if depth < max_depth:
            show(n["children"], depth + 1, max_depth)
print("\n=== ARBOL (2 niveles) ===")
show(roots, max_depth=1)
print("\nGuardado: categorias_tecdoc.json (arbol completo con todos los niveles)")
