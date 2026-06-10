# Documentación API TecDoc (Pegasus 3.0) — Embler

> Resultado de la investigación y pruebas en vivo del **2026-06-10**.
> Objetivo: determinar si con la API DEMO podemos construir el **buscador de partes por vehículo** (marca → modelo → año → piezas).

---

## TL;DR — Veredicto

| Pregunta | Respuesta |
|---|---|
| ¿La API funciona y autentica? | ✅ Sí, probado en vivo |
| ¿Tiene datos de artículos (partes)? | ✅ Sí — 106,641 artículos con OEM, specs, GTIN, categorías, **todo en español** |
| ¿Sirve para buscador **por número de parte / OEM**? | ✅ Sí, ya es viable |
| ¿Sirve para buscador **por vehículo (marca/modelo/año)**? | ❌ **No con esta cuenta** — el módulo de vehículos NO está habilitado |

**El bloqueo no es técnico ni de parámetros.** Usamos los métodos y ejemplos exactos de
la documentación oficial de TecAlliance y el servidor respondió textualmente:

> `"The requested linkage target is not enabled for this account"`

→ Hay que pedirle a TecAlliance que **habilite el módulo de Vehicle Linkage / Vehicle Data
para el provider 25099**, o confirmar que el plan de pago lo incluye.

---

## 1. Conexión (config verificada que FUNCIONA)

```
Endpoint (JSON):  https://webservice.tecalliance.services/pegasus-3-0/services/TecdocToCatDLB.jsonEndpoint
Método HTTP:      POST
Auth:             Header  X-Api-Key: <API_KEY>
Content-Type:     application/json
```

**Credenciales DEMO** (de `acceso-api.md`, vigencia 30 días desde el envío):

| Parámetro | Valor | Nota |
|---|---|---|
| API Key (header `X-Api-Key`) | `2BeBXg6QmtGt4CMfNLSsgPX2VcPAHnbuKuf45oU7tQmYaCwHCYY4` | |
| `provider` | `25099` | va en el body de cada request |
| `country` / `articleCountry` | `MX` (mayúscula) o `mx` (minúscula) | inconsistente entre métodos; ver notas |
| `lang` | `qd` | (también existe `qa`) |
| Marcas activas | ATE (3), SACHS (32), LEMFÖRDER (35), FEBI BILSTEIN (101), Schaeffler INA (204) | |

**Aprendizajes de autenticación (probados):**
- ✅ La auth es por header `X-Api-Key`. **NO** funciona con `Authorization` ni con la key en el body (dan `401 Access not allowed`).
- ✅ La IP del usuario (`201.152.115.203`) **no necesitó whitelist** — respondió directo.
- ⚠️ El código de país correcto es **`MX`** (ISO 2 letras), NO `mex`. Con `mex` da `400 wrong country code`. (La doc a veces muestra `mx` minúscula; ambos sirven en la mayoría de métodos.)

**Estructura del request (formato JSON Pegasus):**
```json
{
  "<nombreMetodo>": {
    "provider": 25099,
    "lang": "qd",
    ... parámetros específicos ...
  }
}
```

**Segundo endpoint:** existe `.../TecdocToCatDL**W**.jsonEndpoint` (DL**W**), pero usa otro
formato de request (dio `Unable to parse request`). No es para consultas de catálogo;
el bueno para nosotros es **DLB**.

---

## 2. Resultado de pruebas por método (provider 25099)

### ✅ Funcionan (datos disponibles)

| Método | Qué devuelve | Resultado en la prueba |
|---|---|---|
| `getManufacturers` | Fabricantes de auto | **147 marcas** (`linkingTargetType:"P"`) / 115 con `"V"` |
| `getArticles` | Catálogo de partes + detalle | **106,641 artículos** con OEM, specs, GTIN, categorías |
| `getGenericArticles` | Categorías genéricas de pieza | OK (en español) |
| `getShortCuts2` | Árbol de sistemas del auto | OK: "Carrocería", "Motor", "Transmisión de potencia", "Filtro"... |
| `getAutoCompleteSuggestions` | Autocompletado de búsqueda libre | OK: marcas + nombres de pieza en español |

### ❌ NO funcionan (módulo de vehículos no habilitado para esta cuenta)

| Método | Resultado |
|---|---|
| `getModelSeries` | `data:""` (vacío) para las 147 marcas, con `P` y `V`, con `MX` y `mx` |
| `getLinkageTargets` | `total: 0` — sin vehículos |
| `getVehicleIdsByCriteria` | vacío |
| `getArticles` con `linkageTargetId` | **`"The requested linkage target is not enabled for this account"`** ← prueba irrefutable |
| `getArticleLinkedAllLinkingTarget4` | `articleLinkages: ""` (vacío) |

---

## 3. El flujo del buscador POR VEHÍCULO (cómo SERÍA cuando se habilite)

Según la documentación oficial de TecAlliance (`WS Pegasus principales metodos.pdf`),
el flujo correcto es:

```
1. getLinkageTargets / getManufacturers
   → marcas de auto (mfrId).  Ej: BMW = 16

2. getModelSeries (manuId)   ó   getLinkageTargets (mfrIds + includeVehicleModelSeriesFacets)
   → modelos + años de construcción (modelId, yearOfConstrFrom/To)

3. getVehicleIdsByCriteria (manuId + modId/modelDescription)   ó   getLinkageTargets (mfrIds + vehicleModelSeriesIds)
   → el carId / linkageTargetId del vehículo exacto.  Ej: Nissan Tsuru = 28523

4. getVehicleByIds3 (carIds)
   → detalle de motor: cilindrada, HP, kW, combustible, tracción, años

5. getArticles (linkageTargetId + linkageTargetType)   ←  ⚠️ AQUÍ está el bloqueo actual
   → todas las piezas que aplican a ese vehículo
```

### ⚠️ Aprendizaje clave de nomenclatura (causó confusión en las pruebas)

Hay DOS parámetros con nombres casi idénticos. **No confundir:**

| Parámetro | Spelling | Uso |
|---|---|---|
| `linkingTargetType` | "in**king**" | tipo de objetivo (P/V/O) en métodos de catálogo de vehículos |
| `linkageTargetId` / `linkageTargetType` | "link**age**" | filtro de `getArticles` para traer piezas de UN vehículo |

En `getArticles` el filtro por vehículo es **`linkageTargetId`** (con "age"), no `linkingTargetId`.

### Tipos de vehículo (`linkingTargetType`)
| Código | Significado |
|---|---|
| `P` | Vehicle Type (Passenger + Motorcycle + LCV) — el más amplio |
| `V` | Passenger Car (solo autos; en `getArticles` filtra a marcas contratadas) |
| `O` | Commercial Vehicle + Tractor |
| `M` | Engine · `B` Motorcycle · `C` Commercial · `L` LCV · `T` Tractor · `A` Axle · `K` CV Body · `H` HMD |

---

## 4. Detalle de los datos de ARTÍCULO (lo que sí tenemos — muy valioso)

`getArticles` devuelve por cada pieza (ejemplo real ATE `03.0101-0014.2`):

- **`articleNumber`**, `mfrName` (marca de la pieza), `dataSupplierId`
- **`oemNumbers`**: cruces OEM con marca del auto (OPEL, VOLVO, KIA, MAZDA...) — *crítico para enriquecer catálogo*
- **`genericArticles`**: categoría en español ("Regulador de la fuerza de frenado", "Kit de freno") + `assemblyGroupName`
- **`articleCriteria`**: specs técnicas en español (peso, diámetro, lado de montaje, sistema de frenado...)
- **`gtins`**: códigos de barras
- **`tradeNumbers`**: números comerciales alternos
- **`misc`**: estatus del artículo, cantidades por empaque
- `replacesArticles` / `replacedByArticles`: reemplazos
- `legacyArticleId`: id numérico para encadenar con métodos de linkage

### Búsqueda de artículos (`getArticles`) — parámetros útiles
| Parámetro | Uso |
|---|---|
| `searchQuery` | texto a buscar |
| `searchType` | `0` Article Number (default), `1` OE Number, `2` Trade Number, `3` Comparable, `4` Replacement, `99` Free Text |
| `searchMatchType` | `exact` (default), `prefix`, `suffix`, `prefix_or_suffix` |
| `dataSupplierIds` | filtrar por marca de la pieza (ej. 101 = FEBI) |
| `assemblyGroupNodeIds` | filtrar por categoría/sistema |
| `linkageTargetId` + `linkageTargetType` | filtrar por vehículo *(requiere módulo habilitado)* |
| `includeAll` / `includeGTINs` / `includeOEMNumbers` / `includeArticleCriteria` | qué bloques traer |
| `perPage` / `page` | paginación (hasta 10,000 registros; `perPage:0` solo cuenta + facets) |
| `assemblyGroupFacetOptions` | devuelve el árbol de categorías con conteos |

---

## 5. Referencia de métodos (de la documentación oficial)

`TecdocToCatDLB.soapEndpoint?doc` lista **70 métodos**. Los principales:

| Categoría | Métodos |
|---|---|
| Fabricantes | `getManufacturers`, `getManufacturers2`, `getLinkageTargets` |
| Modelos y años | `getModelSeries`, `getModelSeries2`, `getLinkageTargets` |
| Resolver vehículo (carId) | `getVehicleIdsByCriteria`, `getVehicleIdsByKTypeNumber`, `getLinkageTargets` |
| Detalle vehículo/motor | `getVehicleByIds3`, `getVehicleByIds4`, `getMotorsByCarTypeManuIdTerm2`, `getMotorIdsByManuIdCriteria2` |
| Marcas de pieza | `getAmBrands` |
| Categorías / sistemas | `getShortCuts2`, `getChildNodesAllLinkingTarget2` |
| Artículos / partes | `getArticles` |
| Artículo → vehículos | `getArticleLinkedAllLinkingTargetManufacturer2`, `getArticleLinkedAllLinkingTarget4`, `getArticleLinkedAllLinkingTargetsByIds3` |
| Búsqueda libre | `getAutoCompleteSuggestions` |

### Enlaces oficiales
- Info / test client: https://webservice.tecalliance.services/pegasus-3-0/info/index.html
- Lista de 70 métodos: https://webservice.tecalliance.services/pegasus-3-0/services/TecdocToCatDLB.soapEndpoint?doc
- Docs (referencia por método): https://developer.tecalliance.cn/en/ y http://api.tecalliance.net.cn/en/api-reference/

---

## 6. Conclusión y siguiente paso

**Para el buscador por vehículo (el objetivo elegido):** la API es la correcta y el flujo
está claro, pero **falta habilitar el módulo de vehículos en la cuenta 25099**. No se puede
avanzar hasta resolver eso con el proveedor.

### Mensaje sugerido para el proveedor TecAlliance
> "Probando la API DEMO (provider 25099, endpoint Pegasus 3.0 DLB) los datos de artículo
> funcionan, pero los de vehículo no: `getModelSeries` y `getLinkageTargets` regresan vacío,
> y `getArticles` con `linkageTargetId` responde *'The requested linkage target is not enabled
> for this account'*. ¿Pueden habilitar el módulo de **Vehicle Linkage / Vehicle Data** para
> esta cuenta, o confirmar si el plan de producción lo incluye?"

### Mientras tanto, lo que SÍ se puede construir hoy con la DEMO
1. **Buscador por número de parte / OEM** — `getArticles` con `searchType` 0–4 ya jala.
2. **Enriquecimiento del catálogo Shopify** — usar `oemNumbers`, `articleCriteria` y categorías
   para llenar los gaps conocidos (los ~230 productos sin OEM, ~614 sin tipo de vehículo, etc.).
3. **Autocompletado de búsqueda** — `getAutoCompleteSuggestions`.

---

## 7. Archivos de esta carpeta

| Archivo | Qué es |
|---|---|
| `acceso-api.md` | Credenciales DEMO enviadas por el proveedor |
| `ANALISIS-TECDOC.md` | Análisis del paquete `Suspension.7z` (datos TAF de SACHS/BOGE) |
| `Suspension.7z` + `extracted/` | Datos de proveedor en formato TAF (solo artículos, sin vehículos) |
| `TecDoc-Data-Format_Version_2.7_EN_2.0.28.pdf` | Spec oficial del formato TAF (207 págs) |
| `WS Pegasus principales metodos.pdf` | **Doc oficial de métodos del API (31 págs) — la referencia clave** |
| `Web Services metodos y end points - TecDoc.pdf` | Endpoints y enlaces |
| `tecdoc_client.py` | Cliente Python consolidado con las pruebas (config que funciona) |
