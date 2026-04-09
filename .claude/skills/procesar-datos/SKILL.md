---
name: procesar-datos
description: |
  Enriquece CSVs de autopartes europeas con contenido para ecommerce y genera columnas listas para importar a Shopify.
  Produce contenido comercial (descripciones, FAQs, compatibilidad) MAS campos Shopify (handle, title, body HTML, type, tags, SEO).
  Usa este skill siempre que el usuario quiera procesar, enriquecer, o limpiar datos del catalogo de Embler.
  Se activa con frases como: "procesa los datos", "genera descripciones", "enriquece el catalogo", "procesar refacciones_motor",
  "genera el contenido para ecommerce", "limpia los CSVs", "procesa la categoria X", "genera para Shopify",
  o cualquier referencia a trabajar con los archivos CSV en output/.
  Tambien cuando el usuario pregunte por el estado de procesamiento o quiera continuar un batch pendiente.
---

# Procesar Datos Embler

Este skill transforma datos crudos de un catalogo de autopartes europeas (BMW, Mercedes-Benz, Audi, VW) en contenido listo para ecommerce. Toma los CSVs ya segmentados por categoria en `output/` y genera dos grupos de columnas:

1. **Columnas de contenido** — caracteristicas del producto + secciones editoriales (descripcion, FAQs, envio, etc.)
2. **Columnas Shopify** — campos listos para importar via CSV a Shopify (handle, title, body HTML, type, tags, SEO, etc.)

El output final de cada categoria es un CSV que contiene las columnas originales + contenido + Shopify, listo para ser importado.

## Argumento

- `/procesar-datos refacciones_motor` — procesa esa categoria
- `/procesar-datos` — lista categorias disponibles para que el usuario elija

Dado que son 13K+ productos y el procesamiento es intensivo (cada fila requiere generacion de texto), procesa una categoria a la vez y confirma con el usuario antes de empezar.

## Flujo de trabajo

### 1. Preparacion

1. Lee `CLAUDE.md` en la raiz del proyecto — contiene las reglas de inferencia y el contexto completo del negocio
2. Lista los CSVs en `output/` excluyendo los que ya tienen sufijo `_enriched`
3. Muestra al usuario las categorias con su cantidad de filas
4. Si ya existe un `_enriched.csv` parcialmente procesado, ofrece continuar desde donde quedo

### 2. Procesar por batches

Usa los scripts de Python del proyecto para manejar los datos de forma eficiente:

```bash
# Extraer batch como JSON ligero (solo campos relevantes + indice del catalogo)
python3 scripts/02_preparar_batch.py <categoria> <inicio> <cantidad>

# Guardar resultados procesados al CSV enriched
python3 scripts/03_guardar_batch.py <categoria> <ruta_resultados_json>
```

**Tamano de batch: 30-50 filas.** Este tamano balancea entre tener suficiente contexto para encontrar productos relacionados y no sobrecargar la ventana de contexto con datos. Para categorias chicas (<100 filas) se puede usar un solo batch.

El ciclo es:
1. Ejecuta `02_preparar_batch.py` para obtener el JSON del batch
2. Lee el JSON generado en `output/{categoria}_batch.json`
3. Genera las 5 columnas nuevas para cada producto (ver seccion siguiente)
4. Guarda los resultados como JSON y ejecuta `03_guardar_batch.py`
5. Reporta progreso: "Batch X/Y completado (N filas procesadas de M)"

### 3. Columnas a generar

Para la referencia tecnica detallada de columnas de entrada y reglas, lee `references/columnas_y_reglas.md` dentro del directorio del skill. Para un ejemplo completo de como debe verse el output, lee `references/ejemplo_output.md`.

Las columnas de output se dividen en dos grupos: **caracteristicas** (datos estructurados del producto) y **secciones de contenido** (texto para la ficha de ecommerce).

---

#### Caracteristicas (columnas individuales)

Estas se extraen/normalizan de los datos existentes. Cada una es su propia columna en el CSV:

**`caract_marca`** — Marca del producto (la refaccion, no el vehiculo). Usar `marca_normalizada` (col 36). Ej: "Original Frey", "Embler", "Mahle".

**`caract_origen`** — Origen del producto. Usar `Origen_ML` (col 30) si existe. Si no hay dato, dejar vacio. Ej: "Importado", "Nacional".

**`caract_tipo_vehiculo`** — Tipo de vehiculo al que aplica. Usar `Tipo de vehiculo_ML` (col 29). Ej: "Carro/Camioneta", "Moto/Cuatriciclo", "Linea Pesada".

**`caract_compatibilidad`** — Texto en parrafo describiendo los vehiculos compatibles. No es JSON, es texto legible para el cliente.

Si hay datos en Compatibilidades_ML: redactar un parrafo como "Aplica para los siguientes modelos BMW Serie 5 (550i 2013, 550i 2014), Serie 7 (750i 2012), X5 (xDrive50i 2014) con motor 4.4L V8 turbo." Agrupar por serie/familia cuando sean muchos modelos.

Si no hay compatibilidades pero el titulo menciona modelos: "Compatible con modelos BMW 325i, 330i, 530i, X3, X5 y Z4. Confirma compatibilidad exacta con tu numero de VIN antes de comprar."

Si no hay informacion: dejar vacio. No inventar — un error de compatibilidad genera devoluciones y perdida de confianza.

---

#### Secciones de contenido

**`seccion_descripcion`** (texto)

Descripcion comercial del producto para la ficha de ecommerce. Los datos de MercadoLibre vienen con formato de marketplace (MAYUSCULAS, advertencias tipo "PARA EVITARTE MOLESTIAS"), y el objetivo es transformarlos en texto profesional.

Estructura en 3 parrafos: que es y para que vehiculos / que incluye / marca y calidad. 100-250 palabras, espanol, tono tecnico-comercial. El cliente tipico es mecanico o conocedor de autos europeos.

Fuentes: titulo + descripcion existente + nombre tecnico del ERP + marca normalizada.

**`seccion_antes_de_comprar`** (texto)

Seccion fija con personalizacion minima. Redactar asi:

"Para garantizar que recibas la pieza correcta para tu vehiculo, necesitamos el numero de serie (VIN) de tu auto antes de procesar el pedido. Esto evita errores, tiempos perdidos y devoluciones innecesarias. Escribenos y con gusto confirmamos compatibilidad."

Si el producto tiene numero de parte o codigo OEM, agregar al final: "Tambien puedes verificar con el numero de parte [NUMERO] o codigo OEM [CODIGO]."

**`seccion_envio`** (texto)

Seccion fija:

"Tenemos stock disponible para entrega inmediata. Enviamos el mismo dia de tu pago a Ciudad de Mexico y a todo el pais via DHL o FedEx."

Si UNIDAD_VENTA_MC indica "Juego" o "Kit", agregar: "Este producto se vende como [juego/kit] completo."

**`seccion_faq`** (JSON array)

3-5 preguntas frecuentes especificas al producto:

```json
[{"pregunta": "...", "respuesta": "..."}]
```

Incluir siempre: compatibilidad, que incluye el producto, garantia. Agregar original-vs-generico y como-verificar solo si hay datos de origen, numero de parte o codigo OEM.

Las respuestas deben ser factuales — si no hay datos de compatibilidad detallada, la respuesta es "verifica con tu numero de VIN" en lugar de inventar vehiculos. Un cliente que compra la pieza equivocada genera una devolucion costosa.

**`productos_relacionados`** (JSON array de strings)

Hasta 5 SKUs del mismo CSV. El script `02_preparar_batch.py` incluye un indice de todo el catalogo de la categoria con SKU, titulo y subcategoria.

Criterios: misma subcategoria + misma marca de vehiculo (del titulo), o productos complementarios (ej: junta de motor -> retenes, sellos de valvula).

---

#### Columnas Shopify

Estas columnas se generan para importar directamente a Shopify via CSV. Siguen la estructura estandar de importacion de productos Shopify. Para la referencia completa del mapeo, lee `references/columnas_y_reglas.md`.

**`shopify_handle`** — URL slug del producto. Minusculas, sin acentos, guiones en lugar de espacios. Debe ser unico por producto. Se genera a partir del titulo limpio.

Reglas de generacion:
- Tomar el titulo, convertir a minusculas, quitar acentos
- Reemplazar espacios y caracteres especiales por guiones
- Eliminar guiones consecutivos y guiones al inicio/final
- Incluir marca del producto y numero de parte si existe para unicidad
- Ej: "Juego De Juntas De Motor Completo Bmw 750i 550i X5 X6 &" → `juego-juntas-motor-completo-bmw-750i-550i-x5-x6`

**`shopify_title`** — Titulo limpio del producto. Se genera a partir de `Titulo_ML`:
- Quitar el "&" o "& " al final (truncamiento de MercadoLibre)
- Capitalizar correctamente (Title Case)
- Mantener siglas y modelos en su formato original (BMW, X5, N63, E90)
- Max 255 caracteres
- Ej: "Juego De Juntas De Motor Completo Bmw 750i 550i X5 X6 &" → "Juego de Juntas de Motor Completo BMW 750i 550i X5 X6"

**`shopify_body_html`** — Descripcion completa en HTML que combina todas las secciones de contenido. Estructura:

```html
<h2>Descripcion</h2>
{seccion_descripcion convertida a parrafos <p>}

<h2>Antes de Comprar</h2>
<p>{seccion_antes_de_comprar}</p>

<h2>Envio</h2>
<p>{seccion_envio}</p>

<h2>Preguntas Frecuentes</h2>
{seccion_faq convertida a bloques <h3>pregunta</h3><p>respuesta</p>}
```

No usar estilos inline ni clases CSS — Shopify aplica los estilos del tema.

**`shopify_product_category`** — Siempre `Vehicles & Parts > Vehicle Parts & Accessories`. Es la taxonomia estandar de Shopify para Google Shopping.

**`shopify_type`** — Tipo de producto que alimenta las collections automaticas de la tienda. Se mapea desde la subcategoria del producto:

| Subcategoria (datos) | shopify_type |
|----------------------|--------------|
| motor, juntas, culata, turbo, valvulas, admision, escape, enfriamiento, distribucion | Motor |
| frenos, discos, pastillas, calipers | Frenos |
| suspension, amortiguadores, brazos, rotulas, bujes, barras | Suspensión |
| electrico, sensores, bobinas, alternador, modulos, computadora | Sistema Eléctrico |
| carroceria, faros, espejos, defensas, cofre, salpicaderas | Carrocería |
| filtros, aceite, aire, gasolina, cabina | Filtros |
| transmision, embrague, clutch, convertidor | Transmisión |
| direccion, cremallera, bomba direccion, terminales | Dirección |
| accesorios | Accesorios |
| tuning | Tuning |

Si la subcategoria no encaja en ninguna, usar el valor mas cercano o dejar la subcategoria en Title Case. Este campo alimenta las collections automaticas por categoria (ej: "BMW - Motor", "Audi - Frenos").

**`shopify_tags`** — Marcas de vehiculo compatibles, separadas por coma. Estas alimentan las collections automaticas por marca.

Extraer de:
1. Compatibilidades_ML (mas confiable — lista vehiculos con marca)
2. Titulo_ML (menciona marcas de vehiculos)
3. Nombre tecnico del ERP

Marcas validas para tags: `BMW`, `Mercedes-Benz`, `Audi`, `Volkswagen`, `Porsche`, `Volvo`, `Mini`, `Land Rover`, `Jaguar`, `Bentley`, `Rolls-Royce`.

Ej: Si un producto es compatible con BMW y Audi → `"BMW, Audi"`. Si solo BMW → `"BMW"`.

IMPORTANTE: Los tags son marcas de VEHICULO, no de producto. "Original Frey" NO es un tag.

**`shopify_published`** — Siempre `TRUE`. El campo `shopify_status` controla la visibilidad real.

**`shopify_option1_name`** / **`shopify_option1_value`** — La mayoria de los productos no tienen variantes reales. Usar:
- `Option1 Name`: `"Title"`, `Option1 Value`: `"Default Title"` — para productos sin variantes (mayoria)
- Si el producto claramente tiene posicion (izquierdo/derecho): `"Posición"` / `"Izquierdo"` o `"Derecho"` — pero esto requiere confirmacion humana, asi que por defecto usar "Title"/"Default Title"

**`shopify_variant_sku`** — Directo de `SKU_ML` (col 17). Si no hay SKU, dejar vacio y flaggear en revision_humana.

**`shopify_variant_price`** — Directo de `Precio_ML` (col 16). Sin simbolo de moneda, solo numero con decimales. Ej: `"450.00"`.

**`shopify_variant_compare_price`** — Precio tachado (antes). Dejar vacio — no hay datos fuente para derivar un precio de comparacion. Si el humano quiere agregar descuentos, lo hace manualmente.

**`shopify_variant_weight`** — Dejar vacio. No hay datos de peso. Ya se flaggea en revision_humana.

**`shopify_variant_weight_unit`** — Siempre `"kg"`.

**`shopify_image_src`** — Dejar vacio. No hay URLs de imagenes en los datos fuente. Ya se flaggea en revision_humana.

**`shopify_image_alt_text`** — Texto alternativo descriptivo para la imagen. Generar aunque no haya imagen (se usara cuando el humano suba la foto).

Formato: `"{Nombre del producto} {Marca producto} para {Marca vehiculo}"`. Max 125 caracteres.
Ej: `"Juego de juntas de motor completo Original Frey para BMW"`.

**`shopify_seo_title`** — Titulo optimizado para Google. Max 60 caracteres. Incluir nombre del producto + marca vehiculo + " | Embler".

Ej: `"Juntas Motor BMW 750i 550i Original Frey | Embler"` (49 chars)

Si supera 60 chars, acortar el nombre del producto. "| Embler" siempre va al final.

**`shopify_seo_description`** — Meta description para Google. Max 155 caracteres. Resumir que es, para que vehiculo(s), y marca. Incluir call-to-action.

Ej: `"Juego de juntas de motor completo para BMW 750i, 550i, X5. Marca Original Frey. Envio inmediato a todo Mexico."` (112 chars)

**`shopify_status`** — Estado del producto. Siempre `"draft"` por defecto. El humano cambia a `"active"` despues de revisar fotos, peso y revision_humana.

---

#### `revision_humana` (texto o vacio)

Esta columna es el puente entre el procesamiento automatico y la persona que revisa los datos. Funciona como una lista de pendientes especifica por producto: le dice al humano exactamente que falta y que accion tomar.

Si el producto tiene todos los datos completos y el contenido generado no necesita ajustes, deja esta columna vacia (string vacio "").

Cuando hay pendientes, usa el formato `[ACCION] detalle`. Las acciones posibles son:

- `[BUSCAR]` — Dato faltante que se podria obtener de otra fuente (catalogo del proveedor, ficha tecnica)
- `[VERIFICAR]` — Dato inferido que necesita confirmacion humana antes de publicarse
- `[INCLUIR]` — Informacion que se debe agregar manualmente (fotos, peso, dimensiones)
- `[REVISAR]` — Contenido generado que podria necesitar ajuste editorial
- `[ANALIZAR]` — Requiere decision de negocio (precio, clasificacion, si se publica)

Reglas para decidir que flaggear:

1. Sin compatibilidades Y sin modelos en titulo -> `[BUSCAR] Compatibilidad vehicular: no hay datos de vehiculos compatibles.`
2. Sin codigo OEM y sin numero de parte -> `[BUSCAR] Numero de parte o codigo OEM faltantes.`
3. Compatibilidad solo inferida del titulo -> `[VERIFICAR] Compatibilidad inferida del titulo — confirmar modelos y anos.`
4. Sin descripcion original -> `[REVISAR] Descripcion generada sin datos fuente — verificar precision.`
5. Producto sin SKU -> `[INCLUIR] SKU faltante — asignar antes de publicar.`
6. Marca no identificada o vacia -> `[ANALIZAR] Marca no identificada — confirmar fabricante.`
7. Siempre al final -> `[INCLUIR] Peso y dimensiones para calculo de envio.`
8. Siempre al final -> `[INCLUIR] Fotografias del producto.`

Items 7-8 aplican a todos los productos (ningun producto tiene peso/fotos en los datos), asi que van al final. Los items especificos del producto van primero porque requieren atencion individual. Separa cada flag con `\n`.

### 4. Formato de resultados

El JSON de resultados para `03_guardar_batch.py` debe tener esta estructura:

```json
{
  "resultados": [
    {
      "_fila_original": 0,
      "caract_marca": "Original Frey",
      "caract_origen": "Importado",
      "caract_tipo_vehiculo": "Carro/Camioneta",
      "caract_compatibilidad": "Aplica para BMW 550i (2013), 750i (2012), X5 xDrive50i (2014) con motor 4.4L V8 turbo.",
      "seccion_descripcion": "texto...",
      "seccion_antes_de_comprar": "Para garantizar que recibas la pieza correcta...",
      "seccion_envio": "Tenemos stock disponible para entrega inmediata...",
      "seccion_faq": [{"pregunta": "...", "respuesta": "..."}],
      "productos_relacionados": ["SKU1", "SKU2"],
      "shopify_handle": "juego-juntas-motor-completo-bmw-750i-550i-x5-x6",
      "shopify_title": "Juego de Juntas de Motor Completo BMW 750i 550i X5 X6",
      "shopify_body_html": "<h2>Descripcion</h2><p>texto...</p><h2>Antes de Comprar</h2><p>...</p>...",
      "shopify_product_category": "Vehicles & Parts > Vehicle Parts & Accessories",
      "shopify_type": "Motor",
      "shopify_tags": "BMW",
      "shopify_published": "TRUE",
      "shopify_option1_name": "Title",
      "shopify_option1_value": "Default Title",
      "shopify_variant_sku": "XB-N63B44-03",
      "shopify_variant_price": "1850.00",
      "shopify_variant_compare_price": "",
      "shopify_variant_weight": "",
      "shopify_variant_weight_unit": "kg",
      "shopify_image_src": "",
      "shopify_image_alt_text": "Juego de juntas de motor completo Original Frey para BMW",
      "shopify_seo_title": "Juntas Motor BMW 750i 550i Original Frey | Embler",
      "shopify_seo_description": "Juego de juntas de motor completo para BMW 750i, 550i, X5. Marca Original Frey. Envio inmediato a todo Mexico.",
      "shopify_status": "draft",
      "revision_humana": "[INCLUIR] Peso y dimensiones...\n[INCLUIR] Fotografias del producto."
    }
  ]
}
```

Guarda este JSON en `output/{categoria}_batch_result.json` antes de pasarlo al script.

### 5. Reporte final

Al terminar la categoria:
- Total de filas procesadas
- Ruta del archivo `output/{categoria}_enriched.csv`
- Estadisticas: % con compatibilidad estructurada, % con FAQs completas (5 preguntas), productos sin relacionados

## Contexto del negocio

Embler vende autopartes para vehiculos europeos (principalmente BMW, Mercedes-Benz). Las marcas de producto principales son Original Frey (61%) y Embler (21%) — estas son las marcas de la refaccion, no del vehiculo. Es importante no confundirlas: "BMW" es la marca del auto, "Original Frey" es quien fabrica la pieza de repuesto.

El cliente tipico busca refacciones especificas por modelo de auto, numero de parte, o tipo de pieza. El contenido generado debe ayudarle a:
1. Confirmar que la pieza es para su vehiculo
2. Entender que incluye el producto
3. Tener confianza en la calidad (marca, garantia)
