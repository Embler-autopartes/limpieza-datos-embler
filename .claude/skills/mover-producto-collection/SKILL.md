---
name: mover-producto-collection
description: |
  Ajusta los metafields de un producto en Shopify (namespace `global`, keys `_brand`, `group`, `sub_group`)
  para sacarlo de una Smart Collection, agregarlo a otra, o moverlo entre collections. Las Smart Collections
  de Embler estan definidas por reglas que matchean exactamente esos 3 metafields, asi que cambiar el valor
  del metafield reasigna al producto automaticamente — no hace falta tocar la collection. Usa este skill
  siempre que el usuario quiera mover, sacar, agregar, o reasignar un producto a/de una collection, o
  corregir su clasificacion de marca / grupo / sub-grupo. Se activa con frases como: "saca este producto de
  BMW", "muevelo a Motor en lugar de Frenos", "este producto no deberia salir en Audi Llaveros", "cambia el
  sub-grupo a Pastillas", "quita la SKU X de la collection Y", "agrega este producto a la collection Z",
  "corrige los metafields de este SKU", "este producto esta en la collection equivocada", "asigna este
  producto al grupo Suspension", "reclasifica este producto", "deberia estar en Mercedes-Benz no en BMW".
  Tambien cuando el usuario pegue un listado pequeño (<=20) de productos a re-clasificar. Para volumenes
  mayores, la skill redirige a Matrixify en lugar de procesar uno por uno.
---

# Mover producto entre Smart Collections (Embler)

## Modelo mental: por que cambiar metafields mueve productos

Las Smart Collections de la tienda Embler **no se editan agregando o quitando productos manualmente**.
Cada collection es una regla que dice algo como:

```
Metafield: global._brand   Equals   "BMW"
Metafield: global.group    Equals   "Motor"
Metafield: global.sub_group Equals  "Poleas"
```

Shopify recalcula la membresia automaticamente: cualquier producto cuyos metafields satisfagan
**TODAS** las reglas de la collection aparece ahi. Por eso para mover un producto basta con cambiar
sus metafields — la collection no se toca, los productos se reordenan solos (suele tardar segundos,
a veces un minuto).

Esta jerarquia tiene 3 niveles que combinan asi:

| Nivel | Metafield | Ejemplo | Collections que controla |
|-------|-----------|---------|---------------------------|
| 1 | `global._brand` | `"BMW"` | Padre: `bmw` |
| 2 | `global._brand` + `global.group` | `"BMW"` + `"Motor"` | Sub-padre: `bmw-motor` |
| 3 | los 3 | `"BMW"` + `"Motor"` + `"Poleas"` | Hoja: `bmw-motor-poleas` |

**Consecuencia importante:** un producto con los 3 metafields aparece en LAS TRES collections
(brand, brand-group, brand-group-subgroup). Si quitas `_brand`, sale de todas. Si quitas solo
`sub_group`, sale de la hoja pero sigue en la brand y la brand-group.

## Cuando usar este skill vs Matrixify

| Escenario | Herramienta |
|-----------|-------------|
| 1 producto puntual | MCP Shopify (este skill) |
| 2-20 productos con cambios distintos | MCP Shopify uno por uno (este skill) |
| 20+ productos o el mismo cambio masivo | Matrixify (este skill genera el Excel) |
| Crear/editar la regla de la collection | Matrixify (fuera del alcance de este skill) |

Si el usuario menciona "todos los productos de X marca" o lista mas de 20, **detente** y propone
exportar a Excel para Matrixify en lugar de hacer 50+ llamadas MCP individuales.

## Metafields oficiales (definicion exacta)

| Namespace | Key | Tipo | Notas |
|-----------|-----|------|-------|
| `global` | `_brand` | `single_line_text_field` | Underscore al inicio. Marca del **vehiculo** (BMW, Audi, Mercedes-Benz, etc.), NO la marca del repuesto. |
| `global` | `group` | `single_line_text_field` | Grupo: Motor, Frenos, Suspension, Transmision, Carroceria, Accesorios, etc. |
| `global` | `sub_group` | `single_line_text_field` | Sub-grupo: Poleas, Bujias, Pastillas, etc. |

Los valores son **case-sensitive y exact-match** con la regla de la collection. `"BMW"` distinto
de `"bmw"`, y `"Mercedes-Benz"` distinto de `"Mercedes Benz"`. Si dudas del valor exacto, revisa
`outputs/collections-matrixify/source/Embler-Collections.xlsx` columna `Rule: Condition`.

## Workflow paso a paso

Para CADA producto a ajustar:

### 1. Identificar el producto

Pide al usuario o deduce del contexto: handle, SKU, o product ID. Si te dan titulo o nombre
parcial, usa `mcp__shopify__get-products` con `query` para buscar.

```
mcp__shopify__get-products(query: "sku:ABC123")
```

### 2. Leer el estado actual

Obten metafields actuales del producto. Usa `mcp__shopify__get-product-by-id` (incluye metafields)
o `get-products` con el handle.

Anota los 3 valores actuales (o ausencia de):
- `global._brand` actual
- `global.group` actual
- `global.sub_group` actual

### 3. Determinar las collections actuales (mental)

Con los 3 metafields actuales, deriva en que collections esta hoy. Ej. si tiene
`_brand=BMW, group=Motor, sub_group=Poleas`, esta en:
- `bmw` (marca)
- `bmw-motor` (marca-grupo)
- `bmw-motor-poleas` (marca-grupo-subgrupo)

### 4. Determinar el target

Pregunta o deduce: a que collection lo quieren mover, o de cual sacarlo. Traduce eso a los valores
que deben tener los 3 metafields **despues**.

Si el usuario pide algo ambiguo (ej. "saca este producto de BMW"), confirma: ¿lo sacamos de **todas**
las BMW (quitar `_brand`) o solo de la sub-collection especifica (cambiar `sub_group`)?

### 5. Computar el delta

Para cada metafield, decide:
- **Cambiar valor:** setea el nuevo valor.
- **Vaciar:** setea string vacio `""` o borra el metafield. Borrar es preferible para que la regla
  no haga match con productos que tengan ese metafield definido como vacio.
- **Dejar igual:** no lo incluyas en el update.

### 6. Aplicar el cambio

Usa `mcp__shopify__update-product` pasando solo los metafields que cambian:

```
mcp__shopify__update-product(
  id: "gid://shopify/Product/...",
  metafields: [
    {namespace: "global", key: "group", value: "Frenos", type: "single_line_text_field"},
    {namespace: "global", key: "sub_group", value: "Pastillas", type: "single_line_text_field"}
  ]
)
```

### 7. Verificar y reportar

Confirma al usuario:
- Producto: <titulo> (SKU: <sku>)
- Cambios aplicados: `_brand: BMW → BMW (sin cambio)`, `group: Motor → Frenos`, `sub_group: Poleas → Pastillas`
- Collections antes: `bmw`, `bmw-motor`, `bmw-motor-poleas`
- Collections ahora: `bmw`, `bmw-frenos`, `bmw-frenos-pastillas`
- Nota: Shopify recalcula la membresia automaticamente; puede tardar segundos.

## Reglas de inferencia y validacion

### Pregunta SIEMPRE antes de:
- **Cambiar `_brand`** — es un cambio mayor; saca al producto de toda la jerarquia de esa marca.
  Confirma con el usuario que es lo que quiere (no solo el grupo).
- **Aplicar un valor que no aparezca en la lista de collections existentes** — si el nuevo
  `group="Climatizacion"` no tiene una collection `bmw-climatizacion` definida, el producto puede
  quedar sin collection visible. Avisa al usuario.
- **Procesar mas de 5 productos en una sola tanda** — confirma el cambio para evitar errores masivos.

### Valida ANTES de aplicar:
- Que el valor target existe en al menos una collection (revisa el Excel source si dudas).
- Que el case y los acentos coinciden (`Suspension` vs `Suspensión` — en este catalogo se usa **sin** acento
  en los handles, pero los valores de metafield pueden tener acento; verifica contra el Excel).
- Que no estas tocando metafields fuera del namespace `global` por error.

### NO hagas sin permiso:
- Borrar productos.
- Cambiar precio, descripcion, titulo, SKU.
- Tocar metafields fuera de los 3 documentados.
- Tocar la definicion de la Smart Collection (su regla).

## Casos de uso comunes (ejemplos)

### Ejemplo 1: "Saca este producto de la collection BMW Llaveros"
- Pregunta de aclaracion: ¿solo de Llaveros (cambiar `sub_group`) o tambien de Accesorios y BMW?
- Si dicen "solo de Llaveros" → vaciar/cambiar `sub_group` (queda en `bmw` y `bmw-accesorios`).
- Si dicen "de todo BMW" → borrar `_brand` (sale de todas las BMW; queda solo en collections que
  no dependen de marca, si hubiera).

### Ejemplo 2: "Mueve esta SKU de Motor a Frenos"
- Cambiar `group` de `"Motor"` a `"Frenos"`.
- El `sub_group` probablemente tambien deba cambiar (un sub-grupo de Motor como "Poleas" no aplica
  a Frenos). Pregunta cual va.

### Ejemplo 3: "Este producto deberia estar en Mercedes-Benz, no en BMW"
- Cambiar `_brand` de `"BMW"` a `"Mercedes-Benz"`.
- `group` y `sub_group` probablemente se mantienen, pero confirma que existan collections
  `mercedes-benz-<group>-<sub_group>` (no todas las marcas tienen todos los grupos).

### Ejemplo 4: "Quita esta SKU de todas las collections"
- Borrar los 3 metafields. El producto queda sin Smart Collection asignada (visible en la tienda
  solo via busqueda, no en navegacion por categoria).

## Cuando frenar y proponer Matrixify

Si el usuario:
- Pega una lista de 20+ SKUs.
- Dice "todos los productos de marca X" sin acotar.
- Pide un cambio repetitivo sobre muchas filas (ej. "todos los `sub_group=Poleas` debe ser `Poleas de Cigueñal`").

Entonces **detente** y propone:
1. Genero un Excel de Matrixify con las columnas `Handle`, `Metafield: global._brand [single_line_text_field]`,
   `Metafield: global.group [single_line_text_field]`, `Metafield: global.sub_group [single_line_text_field]`.
2. El usuario sube ese Excel a Matrixify → Import.
3. Matrixify actualiza los metafields en bulk, Shopify recalcula las Smart Collections.

Estructura recomendada del Excel bulk:
```
Handle,Command,Metafield: global._brand [single_line_text_field],Metafield: global.group [single_line_text_field],Metafield: global.sub_group [single_line_text_field]
producto-handle,MERGE,BMW,Frenos,Pastillas
otro-handle,MERGE,Audi,Motor,
```

Usa `Command: MERGE` para actualizar solo los metafields listados sin tocar lo demas. Valor vacio
borra el metafield.

Guardar el Excel bajo `outputs/YYYY-MM-DD-collections-bulk-update/`.

## Referencias

- Catalogo de collections existentes: `outputs/collections-matrixify/source/Embler-Collections.xlsx`
- Errores conocidos de import: `outputs/collections-matrixify/errores/Embler-Collections-Errores.xlsx`
- Tools MCP disponibles: `mcp__shopify__get-product-by-id`, `mcp__shopify__get-products`,
  `mcp__shopify__update-product`. El MCP de Shopify NO expone tools de Smart Collections — para
  editar collections como tales, hay que usar Matrixify o el admin de Shopify.
