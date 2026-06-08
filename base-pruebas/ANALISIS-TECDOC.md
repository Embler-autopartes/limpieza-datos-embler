# Análisis de la Base de Datos TecDoc — Suspension.7z

## Resumen ejecutivo

El archivo `Suspension.7z` contiene un **paquete de datos en formato TecDoc TAF v2.7** de
**ZF Friedrichshafen AG** (marca alemana, dueña de SACHS, BOGE, Lemförder y otras).
Es el estándar de facto en Europa para intercambio de datos de catálogos de autopartes.

Incluye datos de dos marcas para la categoría **Suspensión**:
- **BOGE** (amortiguadores)
- **SACHS** (amortiguadores, kits de clutch, módulos de volante de inercia)

El PDF `TecDoc-Data-Format_Version_2.7_EN_2.0.28.pdf` es la especificación oficial del
formato (207 páginas, TecAlliance GmbH, diciembre 2024).

---

## Estructura de archivos

```
Suspension.7z
├── 0014/           ← Carpeta = DLN del proveedor (Data Loader Number)
│   ├── 001.0014    ← Nombre = número de tabla, extensión = DLN
│   ├── 030.0014
│   └── ... (32 archivos)
└── 0032/
    ├── 001.0032
    ├── 030.0032
    └── ... (32 archivos)
```

**Convención de nombres:**
| Elemento | Ejemplo | Significado |
|----------|---------|-------------|
| Carpeta | `0014` | DLN: identificador único del proveedor en TecDoc |
| Nombre del archivo | `030` | Número de tabla TecDoc |
| Extensión | `.0014` | DLN repetido (confirma a qué proveedor pertenece) |

**DLNs en esta base:**
| DLN | Marca | Empresa | Categoría principal |
|-----|-------|---------|---------------------|
| 0014 | BOGE | ZF Friedrichshafen AG, ZF Aftermarket | Amortiguadores |
| 0032 | SACHS | ZF Friedrichshafen AG, ZF Aftermarket | Amortiguadores + clutch |

---

## Formato de los archivos (TAF)

- **Texto plano ASCII/UTF-8**, ancho fijo, registros separados por `CRLF`
- Cada registro tiene campos en posiciones exactas (byte offsets)
- El campo clave (número de artículo o ID) ocupa los primeros **22 caracteres**
  (con relleno de espacios a la izquierda si es más corto)
- Los campos siguientes son: **DLN** (4 chars) + **tabla** (3 chars) + datos específicos

Ejemplo de registro en Tabla 200 (artículo "000 217"):
```
000 217               0032200003200001100000000000000
│                     │   │  │        │
│                     │   │  │        └── Flags y datos adicionales
│                     │   │  └─────────── Número de artículo genérico TecDoc
│                     │   └────────────── Tabla 200
│                     └────────────────── DLN 0032 (SACHS)
└──────────────────────────────────────── Número de artículo SACHS (22 chars)
```

**Nota:** el formato TAF es el clásico. Desde 2020 existe también la variante CSV
(separador `;`, encabezados en primera fila). Los archivos aquí son TAF puro.

---

## Tablas presentes y conteo de registros

### A. Tablas de información del proveedor

| Tabla | Nombre | BOGE (0014) | SACHS (0032) |
|-------|--------|-------------|--------------|
| 001 | Encabezado del catálogo | 1 | 1 |
| 040 | Dirección principal del proveedor | 1 | 1 |
| 042 | Logo del proveedor | 1 | 1 |
| 043 | Direcciones de distribuidores | 42 | 43 (por país) |

**Tabla 001 — Encabezado (decodificado):**
```
BOGE:  DLN=0014, CatalogID=262, GeneradoEl=2026-05-26, Marca=BOGE,  Versión=2.70
SACHS: DLN=0032, CatalogID=262, GeneradoEl=2026-05-26, Marca=SACHS, Versión=2.70
```
Ambos fueron generados el **26 de mayo 2026**, versión 2.70 del catálogo ZF.

---

### B. Tablas de artículos (Article Data Tables)

| Tabla | Nombre oficial | BOGE | SACHS | Estado |
|-------|---------------|------|-------|--------|
| 030 | Article Master (nombre de línea) | 630 | 1,218 | ✅ Completo |
| 200 | Article Table (número de artículo) | 20 | 22 | ⚠️ Muestra |
| 201 | Price Information (precios) | 20 | 17 | ⚠️ Muestra |
| 202 | Article Country Restrictions | 20 | 20 | ⚠️ Muestra |
| 203 | Reference Numbers (OEM cross-ref) | 20 | 20 | ⚠️ Muestra |
| 204 | Superseding Articles (reemplazos) | 20 | 20 | ⚠️ Muestra |
| 205 | Parts Lists (listas de aplicación) | 20 | 14 | ⚠️ Muestra |
| 207 | Trade Numbers (números comerciales) | — | 86 | ✅ |
| 208 | Parts List Criteria (atributos técnicos) | 20 | 20 | ⚠️ Muestra |
| 209 | GTIN / códigos de barras | 20 | 27 | ⚠️ Muestra |
| 210 | Article Criteria (especificaciones) | 20 | 20 | ⚠️ Muestra |
| 211 | Article → Generic Article Allocation | 20 | 21 | ⚠️ Muestra |
| 212 | Country-Specific Article Data | 20 | 20 | ⚠️ Muestra |
| 215 | Parts Lists Country Restrictions | 19 | 8,126 | ✅ Completo (SACHS) |
| 217 | Graphics coordinates | 20 | — | ⚠️ Muestra |
| 222 | Accessory Lists | — | 8 | ⚠️ Muestra |
| 228 | Accessory Lists Criteria | — | 4,013 | ✅ Completo |
| 231 | Graphics / Documents (URLs) | 20 | 20 | ⚠️ Muestra |
| 232 | Allocation of Graphics to Articles | 20 | 20 | ⚠️ Muestra |
| 233 | Context Sensitive Graphics (hotspots) | 727 | — | ✅ Completo |

---

### C. Tablas de vinculación artículo-vehículo (Linkage Data Tables)

| Tabla | Nombre oficial | BOGE | SACHS | Estado |
|-------|---------------|------|-------|--------|
| 400 | Article Linkage (link artículo-vehículo) | 20 | 19 | ⚠️ Muestra |
| 404 | Sorting of the linkage | 20 | 21 | ⚠️ Muestra |
| 410 | Linkage attributes (atributos del link) | 20 | 20 | ⚠️ Muestra |
| 432 | Linkage-dependent Graphics/Documents | 20 | 4 | ⚠️ Muestra |

---

## Modelo de datos — cómo se relacionan las tablas

```
┌──────────────────────────────────────────────────────────────────┐
│                    CATÁLOGO TECDOC GLOBAL                        │
│  (TecAlliance — NO incluido en estos archivos)                   │
│                                                                  │
│  Tabla 120: Vehicle Types       Tabla 100: Manufacturers         │
│  Tabla 110: Model Series        Tabla 155: Engines               │
│  BMW Serie 3 (2005-2012)        → KType ID: 47002                │
└──────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼ referencia por KType ID
┌──────────────────────────────────────────────────────────────────┐
│                 DATOS DEL PROVEEDOR (estos archivos)             │
│                                                                  │
│  030: Artículo "000 006" → Línea: "Advantage"                   │
│   │                                                              │
│   ├── 200: Número de artículo SACHS: "000 006"                  │
│   ├── 201: Precio: €13.15, válido hasta 2026-06-30              │
│   ├── 203: OEM cross-ref: "500387621", "32-G25-0", "11 1500..." │
│   ├── 209: GTIN: 4013872367429 (código de barras)               │
│   ├── 210: Criterios técnicos (diámetro, carrera, etc.)         │
│   └── 400: Vehículo KType 47002 → "000 006" encaja aquí         │
│                                                                  │
│  205: Lista de aplicación "AUDI-80B3-FS001"                     │
│   └── 208: Criteria: posición instalación, lado derecho/izquierdo│
└──────────────────────────────────────────────────────────────────┘
```

---

## Tablas clave para el caso de uso de Embler

### 1. Tabla 030 — Article Master (nombres de línea)
Contiene la **descripción del artículo** (nombre de la línea de producto):

| DLN | Artículos | Líneas de producto |
|-----|-----------|-------------------|
| 0014 (BOGE) | 630 | `turbo` |
| 0032 (SACHS) | 1,218 | `Advantage`, `Super Touring`, `NIVOMAT`, `CDC`, `Performance`, `Service Kit`, `DMF Module`, `Clutch modul`, etc. |

El campo de nombre está en posiciones 41-100 del registro (60 chars).
El número de secuencia interno está en posiciones 33-40 (8 chars).

### 2. Tabla 200 — Article Table (números de artículo reales)
Los **números de parte** que el cliente usaría para pedir. Ejemplos SACHS extraídos:
```
000 006,  000 217,  000 331,  000 366,  000 369,  000 370,
001 001,  001370 000004,  00 1812 021 000,  0000 017 502...
```

### 3. Tabla 201 — Price Information (precios)
```
Artículo: "000 217"
Precio:   €13.15
Vigencia: 2026-04-01 a 2026-06-30
Unidad:   ST (Stück = pieza individual)
Moneda:   EUR

Artículo: "000 331"
Precio:   €24.87
Vigencia: 2026-04-01 a 2026-06-30
```
Hay dos periodos de precio: Q2 2026 (hasta jun-2026) y Q3 2026 (jul-2026 a mar-2027).

### 4. Tabla 203 — Reference Numbers (números OEM cruzados)
Articulo SACHS "000 006" tiene los siguientes números cruzados:
```
500387621     (número OEM — posiblemente Volkswagen/Audi)
32-G25-0      (número de otro fabricante)
11 1500 000 006  (número interno u OEM)
11 1500 115 728  (variante)
```
Estos son **críticos** para que el usuario ubique la pieza si ya tiene el número de otro fabricante.

### 5. Tabla 207 — Trade Numbers (números comerciales)
86 registros SACHS relacionan números alternos:
```
Artículo "3400 116 401" → Trade number "K384-4", "K384-8", "K3844", "K3848"
Artículo "3400 122 001" → Trade number "K432-16", "K43216"
```

### 6. Tabla 215 — Parts Lists Country Restrictions
**8,126 registros SACHS (datos COMPLETOS)**. Cada registro indica que una lista de
aplicación está disponible en un país específico:
```
"3000 954 318" disponible en: Brasil (BR), 2 variantes
"3000 954 396" disponible en: México (MEX), 1 variante
"3000 954 457" disponible en: México (MEX), 3 variantes
```
`3000 XXX XXX` es el **ID interno de lista de aplicación** de SACHS.
Hay **1,969 IDs de aplicación únicos** en esta tabla.

La presencia de `MEX` confirma que esta base incluye aplicaciones para México.

### 7. Tabla 228 — Accessory Lists Criteria
**4,013 registros SACHS (datos COMPLETOS)**. Vincula los **83 números de parte
reales** (los que se ven en el catálogo de SACHS) con criterios de búsqueda:
```
Parte: "105 807"   → criterio 100: "HA" (tipo de amortiguador delantero?)
Parte: "105 807"   → criterio 200: "05670" (código de aplicación)
Parte: "290 078"   → múltiples criterios
```

Los **83 números de parte SACHS** extraídos de tabla 228:
```
105 807,  110 026,  110 459,  110 933,  115 007,  115 009,  115 259,
170 426,  200 858,  230 965,
290 078,  290 079,
310 720,  310 950,  310 984,  310 987,  311 017,  311 346,  311 409...
316 606,  316 607,  316 927,  316 981,
317 XXX  (múltiples),
318 508,  319 039-044,
350 726,
556 277,  556 279,  556 882,  558 297,
560 094,  560 171,  560 286,  560 287,  560 288,  560 463,  560 634,
560 637,  560 681,  560 735
```
Estos son amortiguadores SACHS típicos para autos europeos.

### 8. Tabla 400 — Article Linkage (vinculación artículo-vehículo)
**LA tabla más importante** para el buscador de vehículos. Solo hay 19-20 registros
(muestra). Ejemplos SACHS:
```
Artículo "3182 600 111" → KType 47002 (vehículo TecDoc), 1 posición
Artículo "3182 654 213" → KType 47002, 2 posiciones (izq/der)
Artículo "993 751"      → KType 188  (probablemente Porsche 993)
```
Artículos "3182 XXX XXX" y "993 XXX" son referencias Porsche — confirma que
esta base incluye aplicaciones para vehículos Porsche.

### 9. Tabla 410 — Linkage Attributes
Atributos técnicos del link. Ejemplo:
```
Artículo "3182 600 111" en vehículo KType 47002:
  Atributo 0401 = "1"      (posición: eje delantero?)
  Atributo 038  = "F13"    (código de posición/lado)
```

### 10. Tabla 233 — Context Sensitive Graphics (diagramas interactivos)
**727 registros BOGE (completo)**. Define coordenadas de hotspots en diagramas
técnicos de suspensión. Formato del registro:
```
0014233 0014 00032 030001 001255 102680 113028 901990
DLN  Tabla    DiagID  PosNum  X1    Y1     X2    Y2
```
Permite mostrar un diagrama técnico del sistema de suspensión donde el usuario
hace clic en un punto y ve qué amortiguador BOGE aplica.

---

## Identificadores de vehículo — dos sistemas

Esta base usa **dos tipos de IDs de vehículo**:

### Sistema 1: IDs alfanuméricos (internos del proveedor)
```
Formato:  MARCA-MODELOCÓDIGO-TIPO+SECUENCIA
Ejemplos: AUDI-80B3-FS001
          AUDI-80B3-FB001, FB002, FB003... (distintas variantes)
          AUDI-80B3-RB001, RB002
```
- `AUDI` = marca del vehículo
- `80B3` = Audi 80, carrocería B3 (generación 1986-1991)
- `FS` = Front Strut (puntal delantero), `FB` = Front Bar, `RB` = Rear Bar
- `001`, `002`... = variante/configuración dentro de ese modelo

### Sistema 2: KType / IDs numéricos TecDoc
```
Ejemplos: 47002, 188, 3182...
```
Son los **KType numbers** del catálogo central de TecDoc (tabla 120 del catálogo
de referencia global). Para decodificarlos necesitas el catálogo de referencia
de TecAlliance — ej. KType 47002 podría ser "BMW 320d E46, 2001-2005".

---

## Limitación crítica: datos de vehículos no incluidos

Este paquete contiene **solo los datos del proveedor** (capítulo 4 de la spec).
Los datos de referencia de vehículos (capítulo 2 y 3 de la spec) NO están incluidos:

| Tabla TecDoc | Contenido | ¿Incluida? |
|--------------|-----------|------------|
| 100 | Fabricantes (BMW, Audi, VW...) | ❌ No |
| 110 | Series de modelos (Serie 3, A4...) | ❌ No |
| 120 | Tipos de vehículo (KType con años) | ❌ No |
| 155 | Motores | ❌ No |

**Consecuencia:** Con esta base sola, solo puedes buscar por número de parte.
Para hacer "¿qué amortiguador le queda a mi BMW 320d 2005?", necesitas además
el catálogo de referencia TecDoc que mapea (marca + modelo + año → KType number).

---

## Otros documentos en la carpeta

### `260605 WS QUO00000339-1.PDF`
Documento relacionado (probablemente cotización o lista de precios del proveedor).
Revisar para entender el contexto comercial de este paquete de datos.

---

## Resumen del volumen de datos

| Concepto | BOGE (0014) | SACHS (0032) | Total |
|----------|-------------|--------------|-------|
| Artículos (líneas de producto) | 630 | 1,218 | 1,848 |
| Números de parte únicos | ~630 | ~83 confirmados | ~700+ |
| Aplicaciones de vehículo (IDs) | ~19 (muestra) | 1,969 (completo) | 1,988+ |
| Links artículo-vehículo (tabla 400) | 20 (muestra) | 19 (muestra) | — |
| Números cruzados OEM (tabla 203) | 20 (muestra) | 20 (muestra) | — |
| Precios con vigencia | 20 (muestra) | 17 (muestra) | — |
| Restricciones por país | 19 | 8,126 | 8,145 |
| Países cubiertos confirmados | NAM (N. América) | MEX, BR | |

---

## Plan de uso para Embler

### Escenario A: Buscador de piezas por vehículo (objetivo principal)
**Datos necesarios:**
1. Esta base TecDoc (proveedor) ← **ya se tiene**
2. Catálogo de referencia TecDoc con tabla 120 (vehículos) ← **falta**

**Flujo:**
```
Usuario: "Tengo BMW Serie 3 E46, 2003, 320d"
           ↓
Buscar KType en tabla 120 → KType = XXXXX
           ↓
Consultar tabla 400 (Article Linkage) WHERE KType = XXXXX
           ↓
Obtener artículos que aplican → "000 217", "290 079", etc.
           ↓
Mostrar nombre + precio (tabla 201) + número OEM (tabla 203)
```

### Escenario B: Buscador por número de parte (más factible con datos actuales)
**Con datos actuales ya es posible:**
```
Usuario: "Tengo número de parte 290 079"
           ↓
Buscar en tabla 228 (Accessory Lists) o tabla 203 (Reference Numbers)
           ↓
Identificar artículo SACHS
           ↓
Mostrar info: precio, compatibilidades conocidas, OEM cross-refs
```

### Escenario C: Integración con catálogo Embler existente
Cruzar los **números OEM** en tabla 203 con los números de parte ya en el
catálogo de Embler (`CRUCE_ML_MC.xlsx`) para enriquecer datos o confirmar
compatibilidades de SACHS/BOGE en piezas ya listadas.

---

## Cómo parsear estos archivos (referencia técnica)

```python
def parse_taf_record(line_bytes, encoding='latin-1'):
    """Parsear un registro TAF de longitud fija."""
    s = line_bytes.decode(encoding)
    article_no = s[:22].strip()       # Número de artículo (clave primaria)
    dln        = s[22:26]             # DLN del proveedor
    table_no   = s[26:29]             # Número de tabla
    data       = s[29:]               # Datos específicos de la tabla
    return article_no, dln, table_no, data

def read_taf_file(path):
    """Leer todos los registros de un archivo TAF."""
    with open(path, 'rb') as f:
        content = f.read()
    lines = content.split(b'\r\n')
    return [l for l in lines if l.strip()]
```

Para la **Tabla 030** (Article Master), el campo de descripción empieza en posición 41:
```python
seq_number  = s[33:41].strip()   # Número de secuencia interno (8 chars)
description = s[41:101].strip()  # Nombre de línea de producto (60 chars)
```

---

## Glosario

| Término | Definición |
|---------|------------|
| TecDoc | Sistema de catálogos de autopartes, estándar europeo (TecAlliance GmbH) |
| TAF | TecDoc Attribute File — formato de texto de ancho fijo |
| DLN | Data Loader Number — ID único del proveedor en TecDoc |
| KType | Key Type — ID numérico de tipo de vehículo en TecDoc |
| GenArt | Generic Article — categoría estándar de pieza (ej: "amortiguador delantero") |
| Article Linkage | Vínculo directo artículo-vehículo (tabla 400) |
| Parts List | Lista de partes para una aplicación específica de vehículo |
| OEM cross-ref | Número de la pieza equivalente del fabricante original |
