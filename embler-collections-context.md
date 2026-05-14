# Embler Autopartes — Contexto para creación masiva de Collections

> **Documento de handoff** para el agente que armará el script de generación de collections en Shopify.
> Última actualización: Mayo 9, 2026.
> Autor de contexto: Javier (RevOps consultant, Improvitz).

---

## 1. Resumen ejecutivo

Embler Autopartes es una tienda Shopify de refacciones para autos europeos premium (BMW, Mercedes-Benz, Audi, etc.) construida con un **tema Shopify hecho a medida** (no genérico). El desarrollador (Diego) terminó la fase de QA el 7 de mayo de 2026.

La tienda usa una **arquitectura de agrupación jerárquica de 3 niveles vía metafields personalizados**, no usa los campos nativos de Shopify (Category, Type, Vendor, Tags) para organizar productos.

**El job que hay que ejecutar:** crear ~715 smart collections en Shopify de forma masiva, una por cada combinación válida del árbol jerárquico Marca → Grupo → Sub grupo, para que el menú de navegación del sitio (~450-500 enlaces) pueda apuntar a cada una.

**Herramienta recomendada para la importación:** Matrixify (Shopify app), no MCP. La razón se explica en la sección 7.

**Output que necesita el siguiente agente:** un script Python que genere un archivo Excel (.xlsx) compatible con el template de Matrixify "Smart Collections", listo para importar.

---

## 2. Arquitectura de la tienda (lo que construyó Diego)

### 2.1 Lo que NO se usa en esta tienda

Diego documentó explícitamente que estos campos nativos de Shopify **están allí porque son default, pero no se usan** para la organización del catálogo:

- **Category**: no se usa. La jerarquía de 3 niveles fue construida a medida con metafields.
- **Type**: no se usa.
- **Vendor**: no se usa.
- **Tags**: no se usa para la experiencia de usuario, aunque el staff puede usarlo para organización interna sin afectar el frontend.

> Implicación para el script: **NO escribir nada en estos campos**. No usar Category/Type/Vendor/Tags como condiciones de las smart collections. Las únicas condiciones válidas son los 3 metafields jerárquicos.

### 2.2 Lo que SÍ se usa: 3 metafields jerárquicos

Cada producto debe tener llenos estos 3 metafields:

| Metafield | Nivel jerárquico | Ejemplo de valor |
|-----------|------------------|------------------|
| `Marca` | 1 (top) | `Mercedes Benz`, `BMW`, `Audi` |
| `Grupo` | 2 | `Motor`, `Suspensión`, `Dirección`, `Frenos` |
| `Sub grupo` | 3 (más específico) | `Anillos de motor`, `Bomba de agua`, `Caja de dirección` |

> **CRÍTICO — verificar antes de ejecutar el script:** los 3 metafields necesitan tener el toggle **"Smart collections"** activado en su definición (Settings > Custom data > Products > [metafield] > Options > Smart collections). Sin esto, no se pueden usar como condiciones de smart collections automatizadas. Shopify permite hasta 128 metafield definitions con este toggle activado, así que con 3 estamos muy por debajo del límite.

### 2.3 Cómo se llenan las collections automáticamente

Las **smart collections** de Shopify se alimentan solas: si una collection tiene la regla "Marca = BMW AND Grupo = Motor AND Sub grupo = Anillos de motor", cualquier producto con esos 3 metafields llenos con esos valores aparecerá automáticamente en esa collection. Si después se agregan más productos con esos valores, también entrarán solos.

**Esta es la pieza clave del proyecto:** las collections, una vez creadas, no requieren mantenimiento manual. El staff de Embler solo debe llenar los 3 metafields al crear/editar productos, y todo el resto se acomoda.

### 2.4 Otros metafields que existen en los productos (no son condiciones de collection)

Diego mostró en el PDF que los productos tienen metafields adicionales más allá de los 3 jerárquicos:

- Información de envío
- Características - Marca (ej: "Original Frey")
- Características - Origen (ej: "Importado")
- Características - Tipo de vehículo (ej: "Carro/Camioneta")
- Preguntas y respuestas
- Listado - Número de parte (ej: `0024206183;0024206283`)
- Filtros - Año (ej: `["2004","2005","2006"]`)
- Filtros - Marca de la pieza

> Estos NO son relevantes para crear collections. El script no los toca.

---

## 3. Aritmética del proyecto (cuántas collections crear)

### 3.1 Lo que dijo Diego (menú de navegación)

Diego estimó **"450+ items del menú"** con el cálculo: `7 marcas × 8 grupos × ~6-9 items por grupo`.

Esa cifra es de **enlaces del menú de navegación**, no de collections.

### 3.2 Conteo real de collections necesarias

Cada enlace del menú apunta a una collection, pero hay 3 niveles de profundidad. Las collections a crear son:

| Nivel | Fórmula | Conteo aprox |
|-------|---------|--------------|
| 1: por Marca | 11 marcas × 1 | **11 collections** |
| 2: por Marca + Grupo | 11 marcas × ~8 grupos | **~88 collections** |
| 3: por Marca + Grupo + Sub grupo | 11 marcas × ~8 grupos × ~7 subgrupos | **~616 collections** |
| **TOTAL** | | **~715 collections** |

> Shopify permite hasta **5000 smart collections**, así que estamos lejos del techo.
> El usuario mencionó "cerca de 800" — está en el rango correcto.

### 3.3 Marcas conocidas (de la captura del menú)

Las 11 marcas confirmadas en el header de la tienda:

1. BMW
2. Mercedes Benz
3. Audi
4. Mini Cooper
5. Porsche
6. Smart
7. Sprinter
8. Citroën
9. Peugeot
10. Renault
11. Volkswagen

> El usuario mencionó que "tiene muchas otras marcas que también hay que crear sus menús". Confirmar con el usuario si hay marcas adicionales antes de generar el archivo final.

### 3.4 Grupos conocidos (del PDF y de la captura BMW)

Los 8 grupos visibles en la columna de BMW:

1. Motor
2. Suspensión
3. Dirección
4. Enfriamiento
5. Frenos
6. Transmisión
7. Suspensión de aire
8. Colisión

> El usuario debe confirmar si todos los grupos aplican a todas las marcas (probablemente no — un Sprinter tiene "Suspensión de aire" pero un Smart no necesariamente).

### 3.5 Sub grupos conocidos (de la captura BMW)

Por cada grupo, el menú lista 4-5 subgrupos visibles + "Ver todos". Ejemplo BMW:

- **Motor**: Anillos de motor, Juntas/empaques/sellos de motor, Sensores de Distribución, Sensores de motor, Ver todos
- **Suspensión**: Amortiguador de suspensión, Base de amortiguador, Tornillo estabilizador, Balero maza, Ver todos
- **Dirección**: Caja de dirección, Bomba de dirección hidráulica, Bieleta de dirección, Terminal de dirección, Ver todos
- **Enfriamiento**: Bomba de agua, Depósito de anticongelante, Mangueras, Tomas de agua, Ver todos
- **Frenos**: Balatas de freno, Sensor de balata, Disco de freno, Sensor de frenos ABS, Ver todos
- **Transmisión**: Kit de clutch, Soporte de transmisión, Líquido de transmisión, Filtro de transmisión, Ver todos
- **Suspensión de aire**: Bolsa de aire de suspensión, Amortiguador de aire de suspensión, Compresor de aire de suspensión, Bloque de válvulas de suspensión, Ver todos
- **Colisión**: Faro, Calavera, Fascia, Cantonera, Ver todos

> "Ver todos" NO es un subgrupo — es un enlace que apunta a la collection nivel 2 (Marca + Grupo sin filtro de Sub grupo).

> El usuario debe proporcionar el **árbol completo y definitivo** (todas las marcas × todos los grupos × todos los subgrupos reales que aplican) antes de generar el script final. Idealmente como Google Sheet o CSV.

---

## 4. Cómo se ven las collections desde el frontend

El homepage y los menús dropdown están construidos con módulos del tema. Cada link en un mega menú apunta a un URL de tipo:

```
/collections/<handle>
```

Donde `<handle>` es generado por Shopify a partir del Title de la collection (slug en kebab-case). Por ejemplo:

- Collection "BMW" → `/collections/bmw`
- Collection "BMW - Motor" → `/collections/bmw-motor`
- Collection "BMW - Motor - Anillos de motor" → `/collections/bmw-motor-anillos-de-motor`

> **Recomendación de naming convention para los Titles** (ver sección 6 para más detalle).

---

## 5. Restricciones y límites técnicos de Shopify

| Límite | Valor | Relevancia |
|--------|-------|------------|
| Smart collections totales por tienda | 5,000 | OK, usaremos ~715 |
| Condiciones por smart collection | 60 | OK, usaremos máximo 3 (Marca, Grupo, Sub grupo) |
| Metafield definitions con "Smart collections" toggle | 128 (combinando product + variant) | OK, usaremos 3 |
| Max length del Title de collection | 255 chars | OK |
| Rate limit de Shopify Admin API | ~2 req/s (REST) o costo-basado en GraphQL | Relevante si se usa MCP — Matrixify lo maneja internamente |

---

## 6. Convención de naming propuesta para las collections

Para que los handles sean predecibles y el menú de navegación pueda construirse de forma sistemática, propongo este esquema:

| Nivel | Title pattern | Handle resultante (Shopify auto-genera) |
|-------|---------------|-----------------------------------------|
| 1 | `{Marca}` | `bmw`, `mercedes-benz` |
| 2 | `{Marca} - {Grupo}` | `bmw-motor`, `mercedes-benz-suspension` |
| 3 | `{Marca} - {Grupo} - {Sub grupo}` | `bmw-motor-anillos-de-motor` |

Ventajas:
- Predecibles: el script que arme el menú de navegación puede calcular el handle sin consultar la API.
- Únicos: la combinación marca+grupo+subgrupo es única por construcción.
- Legibles para el staff de Embler en el admin.

> **Confirmar con el usuario** si prefiere otro separador (ej: `/` o `>`) o si quiere los Titles más limpios sin la marca repetida (ej: solo "Motor" en lugar de "BMW - Motor"). Si elige la versión limpia, los handles necesitarán prefijo manual para evitar colisiones (porque "Motor" existe para todas las marcas).

---

## 7. Decisión de herramienta: Matrixify, no MCP

### 7.1 Por qué NO usar un MCP para esta importación

Aunque hay buenos MCPs de Shopify Admin (benwmerritt/shopify-mcp, @ajackus/shopify-mcp-server, GeLi2001/shopify-mcp), **no son la herramienta correcta para una operación masiva única** como esta:

- ~715 llamadas API secuenciales sujetas a rate limits.
- No hay checkpoint nativo si algo falla a la mitad — habría que construirlo.
- Consumo alto de tokens de Claude (cada llamada es contexto + respuesta).
- Más lento que un import dedicado.

El MCP es la herramienta correcta para **gestión continua día a día** (editar productos, ajustar metafields puntuales, crear collections one-off), no para batch loads.

### 7.2 Por qué SÍ Matrixify

[Matrixify](https://apps.shopify.com/excel-export-import) es la app estándar de Shopify para imports/exports masivos. Características relevantes:

- Soporta el sheet **"Smart Collections"** con todas las columnas necesarias: Title, Handle, Body HTML, Disjunctive (must match all/any), Rule: Column, Rule: Relation, Rule: Condition, Status, Published Scope, Sort Order, Template Suffix, Image Src, Metafields, Command, etc.
- Maneja el rate limiting internamente.
- Genera un **Import Results file** con los items que fallaron y la razón en la columna `Import Comment` — fácil de re-importar solo lo fallido.
- Soporta archivos hasta 20 GB (overkill para 715 filas, pero indica robustez).
- Soporta el comando por fila: `NEW`, `MERGE`, `UPDATE`, `REPLACE`, `DELETE`, `IGNORE`.

### 7.3 Cómo Matrixify maneja múltiples reglas por collection

**Punto crítico para el script:** una smart collection con 3 condiciones (Marca + Grupo + Sub grupo) **se representa como 3 filas en el Excel**, todas con el mismo Title (o Handle/ID), repitiendo el resto de columnas o dejándolas vacías excepto las columnas de Rule.

Estructura de cada fila de regla:

| Columna | Valor para nuestro caso |
|---------|-------------------------|
| `Rule: Column` | El metafield definition reference, formato: `product_metafield_definition` con un `condition_object_id` apuntando a la definition correspondiente. **Verificar el formato exacto exportando primero una smart collection manual de prueba.** |
| `Rule: Relation` | `EQUALS` |
| `Rule: Condition` | El valor (ej: "BMW", "Motor", "Anillos de motor") |

> **Antes de generar 715 filas, el siguiente agente debe primero crear UNA smart collection a mano en Shopify usando los 3 metafields como condición, y luego exportarla con Matrixify** para ver el formato exacto que Matrixify espera para reglas basadas en metafield definitions. Esa es la fuente de verdad del schema.

### 7.4 Disjunctive (must match all conditions)

Para que las collections tipo nivel-3 incluyan SOLO productos que cumplan los 3 criterios simultáneamente, el campo `Disjunctive` debe ser **`FALSE`** (que significa "all conditions must match" — sí, el naming de Shopify es contraintuitivo).

| Disjunctive | Significado |
|-------------|-------------|
| `FALSE` | Producto debe cumplir TODAS las condiciones (AND) |
| `TRUE` | Producto debe cumplir AL MENOS UNA condición (OR) |

> Para nuestras collections de nivel 1, 2 y 3: siempre `FALSE`.

---

## 8. Plan de ejecución para el siguiente agente

### Paso 1 — Validaciones previas (antes de tocar código)

1. **Confirmar con el usuario el árbol completo** del catálogo (todas las marcas × todos los grupos × todos los subgrupos). Idealmente como CSV/Sheet con 3 columnas.
2. **Confirmar que los 3 metafields (Marca, Grupo, Sub grupo) tienen el toggle "Smart collections" activado** en la tienda. Si no lo están, el usuario debe activarlos antes de cualquier import.
3. **Confirmar la convención de naming** del Title (sección 6).
4. **Crear UNA smart collection de prueba a mano** en el admin de Shopify con las 3 condiciones de metafield, y exportarla con Matrixify para conseguir el schema exacto del archivo. Anotar el `condition_object_id` que Matrixify usa para cada metafield definition.

### Paso 2 — Generar el archivo Excel

Construir un script Python (recomendado: `openpyxl` o `pandas` + `xlsxwriter`) que:

1. Lea el árbol del catálogo desde un input estructurado (CSV, JSON, o un dict hardcoded si el árbol es estable).
2. Genere las filas de las **collections nivel 1** (una por marca, con 1 regla cada una): `N_marcas` collections × 1 fila = `~11 filas`.
3. Genere las filas de las **collections nivel 2** (una por marca-grupo, con 2 reglas cada una): `~88 collections × 2 filas = ~176 filas`.
4. Genere las filas de las **collections nivel 3** (una por marca-grupo-subgrupo, con 3 reglas cada una): `~616 collections × 3 filas = ~1848 filas`.
5. Escriba todo en una hoja llamada exactamente **`Smart Collections`** (este nombre es obligatorio para Matrixify) en un archivo `.xlsx`.

**Total estimado de filas en el Excel: ~2,035 filas** (no 715, porque cada collection con N reglas ocupa N filas).

### Paso 3 — Columnas mínimas a incluir

Como mínimo:

- `Title` — único por collection (repetido en filas de la misma collection)
- `Handle` — opcional, Shopify lo auto-genera, pero conviene fijarlo para predictibilidad
- `Command` — `NEW` (o `MERGE` si se quiere idempotencia para re-runs)
- `Disjunctive` — `FALSE` para todas
- `Sort Order` — `BEST_SELLING` o `MANUAL` (definir con el usuario)
- `Status` — `ACTIVE`
- `Published Scope` — `web`
- `Rule: Column` — referencia al metafield definition (formato a confirmar)
- `Rule: Relation` — `EQUALS`
- `Rule: Condition` — valor literal (ej: "BMW")

### Paso 4 — Import en Matrixify y verificación

1. Subir el archivo a Matrixify en el admin de Shopify.
2. Esperar el análisis previo y confirmar que el conteo de items detectado coincide con lo esperado (~715 collections).
3. Ejecutar el import.
4. Descargar el Import Results file y revisar la columna `Import Comment` para fallas.
5. Si hay fallas, fijar la causa, filtrar las filas afectadas y re-importar solo esas.

### Paso 5 — Verificación post-import

- Verificar 5-10 collections random en el admin: ¿tienen las reglas correctas? ¿se llenaron con productos (asumiendo que los productos ya tienen los metafields)?
- Verificar que los handles son los esperados.
- Pasar al siguiente milestone: construir el menú de navegación con ~450 enlaces a estas collections.

---

## 9. Datos del usuario relevantes para el script

- **Lenguaje preferido del staff de Embler:** español. Los Titles, descriptions y handles pueden quedar en español.
- **El usuario tiene experiencia en Python** y stack actual (Claude Code, MacBook M3, n8n self-hosted en Railway). El script debe ser ejecutable localmente sin infra externa.
- **El usuario ya hizo bulk uploads grandes en este mismo proyecto** (5,000+ productos con multi-image CSV expansion, Cloudflare R2 hosting). Está cómodo con archivos grandes y debugging de imports.

---

## 10. Lo que NO está en este documento (decisiones pendientes con el usuario)

Antes de ejecutar, el siguiente agente debe pedirle al usuario:

1. **Árbol completo del catálogo** — el dato canónico de qué marcas / grupos / subgrupos existen y cuáles aplican a cada combinación. Sin esto no se puede generar el archivo final.
2. **¿Crear collections de nivel 1 (solo Marca) y nivel 2 (Marca + Grupo) o solo nivel 3?** El menú parece tener enlaces para los 3 niveles ("Ver todos" implica nivel 2, y los logos del header implican nivel 1). Confirmar.
3. **Sort order de los productos dentro de cada collection** (manual, best-selling, alfabético, precio asc/desc, etc.).
4. **¿Descripción / Body HTML por collection o vacío?** Para SEO podría convenir un párrafo de descripción por collection. Si sí, definir si se generan automáticamente desde un template (ej: "Encuentra repuestos de {Sub grupo} para tu {Marca}. Calidad de agencia, entrega el mismo día.") o si quedan vacías por ahora.
5. **¿Imagen de collection?** Por default Shopify usa la imagen del primer producto. Confirmar si esto es OK o si quieren imagen custom (lo que requeriría hosting + columna `Image Src` en el Excel).
6. **¿Marcas adicionales más allá de las 11 visibles en el header?** El usuario mencionó que tiene más marcas pendientes.

---

## 11. Referencias técnicas

- [Matrixify — Smart Collections template documentation](https://matrixify.app/documentation/smart-collections/)
- [Matrixify — Tutorial: Create Smart Collections in bulk](https://matrixify.app/tutorials/create-shopify-smart-collections-in-bulk-by-product-tags/)
- [Shopify Help — Smart collections with metafields](https://help.shopify.com/en/manual/custom-data/metafields/smart-collections)
- [Shopify Help — Conditions for smart collections](https://help.shopify.com/en/manual/products/collections/smart-collections/conditions)
- [Shopify Dev — SmartCollection REST resource](https://shopify.dev/docs/api/admin-rest/latest/resources/smartcollection)
- [Shopify Dev — Use metafield capabilities (Smart collection rules)](https://shopify.dev/docs/apps/build/custom-data/metafields/use-metafield-capabilities)

---

## 12. Para gestión continua post-import (no es parte de este job)

Una vez creadas las collections vía Matrixify, para el trabajo del día a día (editar productos, ajustar metafields, crear collections puntuales, debugging), la herramienta recomendada es el MCP **`benwmerritt/shopify-mcp`** corriendo en Claude Code. Características:

- 30+ tools cubriendo products, collections, inventory, draft orders, **metafields**, y bulk operations.
- OAuth flow con local token caching en `~/.shopify-mcp/tokens.json`.
- Conecta al Shopify Admin GraphQL API.

Instalación (referencia, no parte de este job):

```bash
npx shopify-mcp --oauth --domain=embler.myshopify.com --clientId=xxx --clientSecret=yyy
```

Configuración en `claude_desktop_config.json` o `.mcp.json` de Claude Code:

```json
{
  "mcpServers": {
    "shopify": {
      "command": "npx",
      "args": ["shopify-mcp", "--domain", "embler.myshopify.com"]
    }
  }
}
```

---

**Fin del documento de contexto.**
El siguiente agente: empieza por la **sección 8, paso 1**. No generes código hasta tener el árbol completo del catálogo y el schema confirmado de Matrixify para reglas de metafield.
