#!/usr/bin/env python3
"""
Prueba definitiva del modulo de vehiculos (2026-06-11).
Consolida las rondas v2-v7: requests 100% bien formados (cada error 400 de
parametro fue corregido hasta que el API acepto el request) para separar
"request mal construido" de "datos no habilitados en la cuenta".

Conclusion: los requests estan bien construidos; la cuenta DEMO 25099 no tiene
datos de vehiculos. Ver seccion en DOCUMENTACION-API-TECDOC.md.
"""
import json
import requests

ENDPOINT = "https://webservice.tecalliance.services/pegasus-3-0/services/TecdocToCatDLB.jsonEndpoint"
API_KEY = "2BeBXg6QmtGt4CMfNLSsgPX2VcPAHnbuKuf45oU7tQmYaCwHCYY4"
HEADERS = {"Content-Type": "application/json", "X-Api-Key": API_KEY}


def call(func_name, params, lang="qd"):
    body = {func_name: {"provider": 25099, "lang": lang, **params}}
    r = requests.post(ENDPOINT, json=body, headers=HEADERS, timeout=60)
    try:
        return r.json()
    except Exception:
        return {"_raw": r.text[:300], "_http": r.status_code}


def check(label, resp, esperado_vacio=True):
    s = json.dumps(resp, ensure_ascii=False)
    print(f"  {label}\n    -> {s[:250]}")


print("=" * 72)
print("CONTROL: la cuenta funciona (articulos)")
print("=" * 72)
r = call("getArticles", {"articleCountry": "mx", "searchQuery": "", "perPage": 0})
print(f"  getArticles total: {r.get('totalMatchingArticles')} (esperado ~106k)")

print()
print("=" * 72)
print("VEHICULOS — requests bien formados, todos aceptados (status 200)")
print("=" * 72)

# 1. Lista de modelos por marca (params completos, incl. countriesCarSelection)
check("getModelSeries (BMW, country+ccs+linkingTargetType)",
      call("getModelSeries", {"country": "mx", "countriesCarSelection": "mx",
                              "manuId": 16, "linkingTargetType": "P"}))

# 2. getLinkageTargets con linkageTargetCountry (el nombre correcto del param)
check("getLinkageTargets (linkageTargetCountry=mx, tipo P)",
      call("getLinkageTargets", {"linkageTargetCountry": "mx", "linkageTargetType": "P",
                                 "page": 1, "perPage": 3}))

# 3. Resolver vehiculo por descripcion (todos los params obligatorios)
check("getVehicleIdsByCriteria (VW Golf, ccs+carType+modelDescription)",
      call("getVehicleIdsByCriteria", {"country": "mx", "countriesCarSelection": "mx",
                                       "manuId": 121, "carType": "P",
                                       "modelDescription": "Golf"}))

# 4. Resolver por kType (param correcto: typeNumber, no kTypeNumber)
check("getVehicleIdsByKTypeNumber (typeNumber=9465 Golf IV, ccs+carType)",
      call("getVehicleIdsByKTypeNumber", {"country": "mx", "countriesCarSelection": "mx",
                                          "typeNumber": 9465, "carType": "P"}))

# 5. Linkage articulo->vehiculos con el legacyArticleId correcto
#    (vive en article.genericArticles[].legacyArticleId, NO en la raiz)
arts = call("getArticles", {"articleCountry": "mx", "searchQuery": "",
                            "dataSupplierIds": 32, "perPage": 1, "includeAll": True})
a = (arts.get("articles") or [{}])[0]
ga = (a.get("genericArticles") or [{}])[0]
legacy = ga.get("legacyArticleId")
print(f"  articulo control: {a.get('mfrName')} {a.get('articleNumber')}, "
      f"legacyArticleId={legacy}, linkageTargetTypes={ga.get('linkageTargetTypes')}")
check("getArticleLinkedAllLinkingTarget4 (articleId=legacy, tipo V)",
      call("getArticleLinkedAllLinkingTarget4", {"articleCountry": "mx", "country": "mx",
                                                 "linkingTargetType": "V",
                                                 "articleId": legacy}))

# 6. Conteo de linkages inline en getArticles
arts = call("getArticles", {"articleCountry": "mx", "searchQuery": "", "dataSupplierIds": 32,
                            "perPage": 50, "includeLinkages": True})
con = sum(1 for x in arts.get("articles", []) if x.get("totalLinkages"))
print(f"  getArticles includeLinkages: {con}/50 articulos con totalLinkages>0")

# 7. El mensaje de entitlement explicito (distinto a un error de validacion)
check("getArticles + linkageTargetId=28523 (request valido)",
      call("getArticles", {"articleCountry": "mx", "linkageTargetId": 28523,
                           "linkageTargetType": "P", "perPage": 2}))

print()
print("=" * 72)
print("RESTRICCION DE PAIS: solo 'mx' esta habilitado en la cuenta")
print("=" * 72)
for pais in ("am", "mex", "de"):
    r = call("getManufacturers", {"country": pais, "linkingTargetType": "P"})
    print(f"  country={pais!r}: {r.get('statusText', 'OK')}")
