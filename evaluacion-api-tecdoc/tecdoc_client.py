#!/usr/bin/env python3
"""
Cliente consolidado de la API TecDoc Pegasus 3.0 para Embler.
Config verificada en vivo el 2026-06-10. Ver DOCUMENTACION-API-TECDOC.md.

Uso:
    python3 tecdoc_client.py            # corre el diagnostico completo
"""
import json
import requests

ENDPOINT = "https://webservice.tecalliance.services/pegasus-3-0/services/TecdocToCatDLB.jsonEndpoint"
API_KEY = "2BeBXg6QmtGt4CMfNLSsgPX2VcPAHnbuKuf45oU7tQmYaCwHCYY4"
PROVIDER = 25099
COUNTRY = "MX"   # ISO 2 letras. NO usar "mex".
LANG = "qd"
HEADERS = {"Content-Type": "application/json", "X-Api-Key": API_KEY}


def call(func_name, params=None):
    """Llama un metodo Pegasus 3.0 via JSON endpoint y regresa el dict de respuesta."""
    body = {func_name: {"provider": PROVIDER, "lang": LANG, **(params or {})}}
    r = requests.post(ENDPOINT, json=body, headers=HEADERS, timeout=40)
    try:
        return r.json()
    except Exception:
        return {"_raw": r.text, "_http": r.status_code}


def _array(resp):
    d = resp.get("data", {})
    return d.get("array", []) if isinstance(d, dict) else (d if isinstance(d, list) else [])


# ----------------------------------------------------------------------
# Funciones de alto nivel (las que YA funcionan con la cuenta DEMO 25099)
# ----------------------------------------------------------------------
def fabricantes(linking_target_type="P"):
    """Marcas de vehiculo. linkingTargetType: P=amplio, V=autos."""
    return _array(call("getManufacturers", {"country": COUNTRY, "linkingTargetType": linking_target_type}))


def buscar_articulos(search_query, search_type=0, per_page=20, page=1):
    """Buscar piezas. searchType: 0=No.articulo,1=OE,2=Trade,3=Comparable,4=Replacement,99=texto libre."""
    return call("getArticles", {
        "articleCountry": COUNTRY, "searchQuery": search_query, "searchType": search_type,
        "includeAll": True, "perPage": per_page, "page": page,
    })


def categorias_sistemas(linking_target_type="P"):
    """Arbol de sistemas del auto (Carroceria, Motor, Frenos...)."""
    return _array(call("getShortCuts2", {"articleCountry": COUNTRY, "linkingTargetType": linking_target_type}))


def autocompletar(texto):
    return call("getAutoCompleteSuggestions", {"searchQuery": texto}).get("suggestions", [])


def piezas_por_vehiculo(car_id, linkage_target_type="P", per_page=20):
    """REQUIERE modulo de vehiculos habilitado (hoy NO lo esta para 25099).
    Filtro por vehiculo usa 'linkageTargetId' (con AGE), no 'linkingTargetId'."""
    return call("getArticles", {
        "articleCountry": COUNTRY, "linkageTargetId": car_id,
        "linkageTargetType": linkage_target_type, "perPage": per_page, "page": 1,
    })


# ----------------------------------------------------------------------
# Diagnostico
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("=== DIAGNOSTICO API TECDOC (provider %s) ===\n" % PROVIDER)

    mans = fabricantes()
    print(f"[OK] getManufacturers: {len(mans)} marcas")

    arts = buscar_articulos("", per_page=1)
    print(f"[OK] getArticles: {arts.get('totalMatchingArticles','?')} articulos totales")

    cats = categorias_sistemas()
    print(f"[OK] getShortCuts2: {len(cats)} sistemas -> {[c.get('shortCutName') for c in cats[:4]]}")

    sug = autocompletar("Z")
    print(f"[OK] getAutoCompleteSuggestions: {sug[:5]}")

    # Prueba del bloqueo de vehiculos
    veh = piezas_por_vehiculo(28523)  # Nissan Tsuru (ejemplo de la doc)
    estado = veh.get("statusText", f"{veh.get('totalMatchingArticles')} piezas")
    print(f"\n[VEHICULOS] piezas_por_vehiculo(28523) -> {estado}")
    if "not enabled" in str(estado):
        print("           => Modulo de vehiculos NO habilitado para esta cuenta.")
        print("           => Pedir a TecAlliance habilitar Vehicle Linkage / Vehicle Data.")
