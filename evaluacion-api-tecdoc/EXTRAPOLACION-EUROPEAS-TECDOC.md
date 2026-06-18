# API TecDoc: qué validó la DEMO y cómo extrapola a marcas europeas

> **2026-06-11.** Conclusión del ciclo de pruebas con la cuenta DEMO (provider 25099).
> Decisión: NO pedir más datos al proveedor. La DEMO cumplió su propósito — comprobar
> que la API funciona y conocer la estructura de datos. La lógica de extrapolación
> "si funcionó con esto, funciona con lo otro" es válida y aquí se documenta por qué.

---

## 1. El principio: la API es la misma, solo cambia el contenido

TecDoc Pegasus 3.0 usa **un solo endpoint y un solo modelo de datos** para todos los
tipos de vehículo y todas las marcas. La DEMO viene cargada con:

| Dataset | Contenido DEMO | Equivalente al pagar |
|---|---|---|
| Artículos | 106,642 piezas de 5 marcas (ATE, SACHS, LEMFÖRDER, FEBI, INA) | Mismas + las marcas que se contraten |
| Vehículos tipo `K` (camiones) | 98,476 (IVECO, SCANIA, MB Trucks...) | — |
| Vehículos tipo `A` (ejes) | 7,191 (BPW, SAF...) | — |
| Vehículos tipo `P`/`V` (autos de pasajeros) | **0** | **BMW, Mercedes, Audi, VW, Porsche, Mini...** |

Los métodos, parámetros, paginación, facets, filtros y formato de respuesta son
**idénticos** entre tipos — lo comprobamos en vivo: el mismo `getLinkageTargets` que
regresa camiones con `linkageTargetType: "K"` regresa `total: 0` con `"P"` sin cambiar
nada más del request. Cuando el plan de pago incluya datos Passenger Car, los mismos
requests que hoy probamos con camiones regresarán los autos europeos.

---

## 2. Qué quedó COMPROBADO en vivo (no extrapolado — verificado)

| Capacidad | Evidencia |
|---|---|
| Autenticación (`X-Api-Key` header) | Todas las llamadas |
| Endpoint JSON (`TecdocToCatDLB.jsonEndpoint`) | Todas las llamadas |
| Catálogo de artículos completo | 106,642 artículos con OEM, specs, GTIN, imágenes |
| Contenido **en español** (lang `qd`) | Categorías, criterios y atributos traducidos |
| Búsqueda por nº de parte / OE / texto libre | `getArticles` searchType 0–4, 99 |
| Listado de vehículos | `getLinkageTargets` → 105,667 targets (K+A) |
| Filtro de vehículos por marca | `mfrIds: 80` → 6 targets Nissan ✅ |
| Facets (agregaciones con conteo) | `includeMfrFacets` → 79 marcas con conteos |
| Paginación | `perPage`/`page` en artículos y vehículos |
| Atributos técnicos por vehículo, en español | Ejes tipo A: ver §3 |
| Árbol de categorías/sistemas | `getShortCuts2`, facets de assembly groups |
| Autocompletado | `getAutoCompleteSuggestions` |

---

## 3. La estructura de datos de vehículo (observada de verdad)

### Registro mínimo (camiones K de la DEMO)

```json
{
  "linkageTargetId": 7782,
  "linkageTargetType": "K",
  "description": "TLO",
  "mfrId": 80,
  "mfrName": "NISSAN",
  "mfrShortName": "NISSA",
  "vehicleImages": [],
  "vehiclesInOperation": []
}
```

### Registro rico (ejes A de la DEMO) — la prueba de extrapolación

```json
{
  "linkageTargetId": 1,
  "linkageTargetType": "A",
  "description": "KH 10008",
  "mfrId": 885,
  "mfrName": "BPW",
  "vehicleModelSeriesId": 5173,
  "vehicleModelSeriesName": "KH",
  "beginYearMonth": "1988-01",
  "axleStyle": "Eje rígido",
  "axleType": "Eje remolque",
  "axleBody": "Eje hueco ectangular",
  "wheelMounting": "8 taladros",
  "axleLoadToKg": 10000,
  "brakeType": "Tambor"
}
```

**Lo que esto demuestra**: el objeto `linkageTarget` carga (a) la jerarquía
modelo-serie (`vehicleModelSeriesId/Name`), (b) vigencia temporal (`beginYearMonth`),
y (c) **atributos técnicos específicos del tipo de vehículo, traducidos al español**.
Para un auto de pasajeros (tipo `V`/`P`), esos atributos específicos son — según la
doc oficial (`WS Pegasus principales metodos.pdf`) — los de motorización:
`engineCode`, `kiloWattsTo/From`, `horsePowerTo/From`, `fuelType`, `bodyStyle`,
`driveType`, `capacityCC`, `beginYearMonth`/`endYearMonth`, etc. Mismo sobre, distinto
contenido.

### Cómo se verá un BMW (extrapolación campo a campo)

| Campo | DEMO (camión/eje) | Con plan Passenger Car |
|---|---|---|
| `linkageTargetType` | `"K"` / `"A"` | `"V"` (o `"P"`) |
| `mfrId` / `mfrName` | 80 / NISSAN | 16 / BMW (id ya verificado en `getManufacturers`) |
| `description` | `"309.111"` | `"320d"` (la motorización) |
| `vehicleModelSeriesName` | `"KH"` | `"3 (E90)"` |
| `beginYearMonth` | `"1988-01"` | `"2004-12"` |
| Atributos técnicos | `axleStyle`, `brakeType`, `axleLoadToKg` | `engineCode`, `kW/HP`, `fuelType`, `capacityCC` |

Los `manuId` de las marcas europeas **ya existen y ya los verificamos** en la DEMO
(`getManufacturers` regresa 147 marcas): AUDI=5, BMW=16, MERCEDES-BENZ=74,
NISSAN=80, VW=121. Solo les faltan los vehículos colgados debajo.

---

## 4. El flujo del buscador por vehículo — listo para conectar

El flujo completo quedó mapeado y los requests construidos/validados (el API los
acepta; solo regresan vacío por falta de datos P/V):

```
1. getManufacturers (country, linkingTargetType:"V")        → marcas        ✅ probado con datos
2. getLinkageTargets (mfrIds + includeVehicleModelSeriesFacets) → modelos   ✅ probado con datos (K)
3. getLinkageTargets (mfrIds + vehicleModelSeriesIds)       → motorizaciones ✅ estructura validada
4. getArticles (linkageTargetId + linkageTargetType)        → piezas        ⚠️ ver §5
```

Con datos P/V, el paso 2 con `mfrIds: 16` regresará las series de BMW igual que hoy
`mfrIds: 80` regresa los Nissan K.

---

## 5. Lo que la DEMO NO pudo validar (riesgo residual — honesto)

| Pendiente | Detalle | Mitigación |
|---|---|---|
| **`getArticles` filtrado por vehículo con resultados > 0** | Los artículos de la DEMO tienen `totalLinkages: 0` (sin vínculos pieza↔vehículo cargados). El request se acepta estructuralmente pero nunca vimos piezas regresar filtradas por un vehículo. | Es el método estrella de TecDoc (su negocio entero es ese vínculo). Validarlo el día 1 del plan de pago con el checklist de §6. |
| Cobertura de modelos europeos para país `mx` | No sabemos cuántos BMW/Mercedes trae el dataset MX de pasajeros ni qué tan atrás llegan los años. | Pedir a TecAlliance el reporte de cobertura PC para MX antes de firmar, o validarlo en las primeras 48h. |
| Detalle extendido `getVehicleByIds3` | En DEMO solo hace eco del `carId`. | Mismo checklist día 1. |

---

## 6. Checklist de aceptación al activar el plan de pago

Correr `test_modulo_vehiculos.py` (debe pasar de vacío a datos) y estos 4 requests:

```json
// 1. ¿Hay autos de pasajeros?  (esperado: total > 0)
{"getLinkageTargets": {"provider": <prod>, "linkageTargetCountry": "mx", "lang": "qd",
                       "linkageTargetType": "V", "perPage": 1, "page": 1}}

// 2. ¿Están los BMW con sus series?  (esperado: series E46/E90/F30...)
{"getLinkageTargets": {"provider": <prod>, "linkageTargetCountry": "mx", "lang": "qd",
                       "linkageTargetType": "V", "mfrIds": 16, "perPage": 100, "page": 1,
                       "includeVehicleModelSeriesFacets": true}}

// 3. ¿Un vehículo trae su ficha de motor?  (usar un linkageTargetId del paso 2)
{"getLinkageTargets": {"provider": <prod>, "linkageTargetCountry": "mx", "lang": "qd",
                       "linkageTargetIds": {"type": "V", "id": <id>}, "perPage": 1, "page": 1}}

// 4. EL CRÍTICO: ¿regresan piezas filtradas por ese vehículo?  (esperado: > 0 artículos)
{"getArticles": {"provider": <prod>, "articleCountry": "mx", "lang": "qd",
                 "linkageTargetId": <id>, "linkageTargetType": "V", "perPage": 10, "page": 1}}
```

Si el #4 regresa artículos de las marcas contratadas → el buscador por vehículo de
Embler es 100% viable y todo lo demás ya está probado.

---

## 7. Gotchas de la API aprendidos (ahorran días al implementar)

| Gotcha | Detalle |
|---|---|
| Auth solo por header | `X-Api-Key`. Ni `Authorization` ni key en body (dan 401). |
| País bloqueado por cuenta | Solo `mx` (ISO-2). `mex`, `am`, `de` → 400. Cada cuenta tiene su lista. |
| `linking` vs `linkage` | `linkingTargetType` en métodos de catálogo; `linkageTargetId/Type` en `getArticles`. |
| `countriesCarSelection` | Obligatorio en `getVehicleIdsByCriteria` y `getVehicleIdsByKTypeNumber`. |
| `typeNumber`, no `kTypeNumber` | En `getVehicleIdsByKTypeNumber`. |
| `legacyArticleId` | Vive en `article.genericArticles[].legacyArticleId`, no en la raíz. |
| **Omitir `linkageTargetType` ≠ filtro vacío** | `getLinkageTargets` sin tipo regresa TODO (105k); con un tipo sin datos regresa 0. Probar siempre sin tipo primero para ver qué hay en la cuenta. |
| Errores de validación vs entitlement | "Field X must be not null" = request mal construido; "not enabled for this account" = datos/permiso no provisionados. Capas distintas. |
| `getLinkageTargets` individual | Detalle de un vehículo: `"linkageTargetIds": {"type": "V", "id": 123}`. |
| Endpoint DLW | Existe `TecdocToCatDLW.jsonEndpoint` pero usa otro formato; el bueno es **DLB**. |

---

## 8. Archivos relacionados

| Archivo | Qué es |
|---|---|
| `DOCUMENTACION-API-TECDOC.md` | Bitácora completa de las pruebas (2026-06-10 y 06-11) |
| `test_modulo_vehiculos.py` | Script de diagnóstico re-ejecutable (sirve como checklist día 1) |
| `tecdoc_client.py` | Cliente Python con la config que funciona |
| `TecDoc_var.postman_collection.json` | Colección Postman del proveedor (Ricardo) |
| `WS Pegasus principales metodos.pdf` | Doc oficial de métodos — referencia de campos PC |
