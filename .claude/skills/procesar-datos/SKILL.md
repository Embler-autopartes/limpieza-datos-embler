---
name: procesar-datos
description: |
  Enriquece CSVs de autopartes europeas con contenido para ecommerce y genera columnas listas para importar a Shopify.
  Produce contenido comercial profundo (descripcion tecnica de 5 parrafos, FAQs, compatibilidad COMPLETA extraida del bloque
  "APLICA PARA LOS SIGUIENTES MODELOS:" de la descripcion) MAS campos Shopify (handle, title, body HTML con seccion de
  compatibilidades, type, tags, SEO). Usa este skill siempre que el usuario quiera procesar, enriquecer, o limpiar datos
  del catalogo de Embler. Se activa con frases como: "procesa los datos", "genera descripciones", "enriquece el catalogo",
  "procesar refacciones_motor", "genera el contenido para ecommerce", "limpia los CSVs", "procesa la categoria X",
  "genera para Shopify", o cualquier referencia a trabajar con los archivos CSV en new-output/. Tambien cuando el usuario
  pregunte por el estado de procesamiento o quiera continuar un batch pendiente.
---

# Procesar Datos Embler

Este skill transforma datos crudos de un catalogo de autopartes europeas (BMW, Mercedes-Benz, Audi, VW, Porsche, etc.) en contenido listo para ecommerce. Toma los CSVs ya segmentados por categoria en `new-output/<hoja>/` y genera dos grupos de columnas:

1. **Columnas de contenido** — caracteristicas del producto + secciones editoriales (descripcion tecnica larga, compatibilidad completa, FAQs, envio, devoluciones).
2. **Columnas Shopify** — campos listos para importar via CSV a Shopify (handle, title, body HTML con bloque de compatibilidades, type, tags, SEO).

Este skill **fusiona** el flujo original `procesar-datos` con `corregir-datos`: las compatibilidades se extraen deterministicamente del bloque `"APLICA PARA LOS SIGUIENTES MODELOS:"` dentro de `descripcion` (no de la columna `Compatibilidades` de ML, que viene incompleta), y la descripcion comercial usa el bloque `"INCLUYE:"` cuando esta presente. Asi el output sale correcto desde el primer pase, sin necesidad de un pase de correccion posterior.

El output final de cada categoria es un CSV en `new-output/<hoja>/<categoria>_enriched.csv` con las columnas originales + contenido + Shopify.

## Argumento

- `/procesar-datos refacciones_motor` — procesa esa categoria de `ml_con_match` (default).
- `/procesar-datos refacciones_motor ml_sin_match` — procesa esa categoria de `ml_sin_match`.
- `/procesar-datos` — lista categorias disponibles para que el usuario elija.

Dado que son 13K+ productos y el procesamiento es intensivo, procesa una categoria a la vez y confirma con el usuario antes de empezar.

## Estructura de carpetas

```
new-output/
  ml_con_match/         (13,960 filas — fuente principal, productos publicados con match Microsip)
  ml_sin_match/         (847 filas — productos publicados sin match Microsip)
```

Las hojas `ml_ambiguos_revisar` y `mc_sin_match` quedan fuera de alcance.

## Flujo de trabajo

### 1. Preparacion

1. Lee `CLAUDE.md` en la raiz del proyecto — contiene el contexto del negocio.
2. Lista los CSVs en `new-output/<hoja>/` excluyendo los que tienen sufijo `_enriched`, `_batch.json` o `_batch_result.json`.
3. Muestra al usuario las categorias con su cantidad de filas.
4. Si ya existe un `_enriched.csv` parcialmente procesado, ofrece continuar desde donde quedo.

### 2. Procesar por batches

Usa los scripts de Python del proyecto (todos en `scripts/`):

```bash
# Extraer batch como JSON ligero (campos relevantes + indice del catalogo + compatibilidades pre-parseadas)
python scripts/02_preparar_batch_v2.py <categoria> <inicio> <cantidad> [<hoja>]

# Guardar resultados procesados al CSV enriched
python scripts/03_guardar_batch_v2.py <categoria> <ruta_resultados_json> [<hoja>]
```

`02_preparar_batch_v2.py` ya hace el parseo deterministico del bloque `APLICA PARA LOS SIGUIENTES MODELOS:` y `INCLUYE:` desde la descripcion ML, usando `lib_compat_parser.py`. El JSON del batch incluye, por cada producto, estos campos pre-extraidos:

- `caract_compatibilidad_propuesta` — parrafo agrupado por serie (listo para usar tal cual).
- `seccion_compatibilidades_propuesta` — lista completa, una linea por modelo (lista cruda).
- `marcas_vehiculo` — list ordenada de marcas extraidas (BMW, Audi, etc.) — usar para `shopify_tags`.
- `incluye_texto` — prosa limpia de lo que incluye el producto si era kit/juego (string vacio si no aplica).
- `num_compatibilidades` — cantidad de configuraciones encontradas.

**Tamano de batch: 30-50 filas.** Para categorias chicas (<100 filas) un solo batch.

El ciclo:
1. Ejecuta `02_preparar_batch_v2.py` para obtener el JSON del batch.
2. Lee el JSON generado en `new-output/<hoja>/{categoria}_batch.json`.
3. Genera las columnas nuevas para cada producto (siguiente seccion).
4. Guarda los resultados como JSON en `new-output/<hoja>/{categoria}_batch_result.json` y ejecuta `03_guardar_batch_v2.py`.
5. Reporta progreso: "Batch X/Y completado (N filas procesadas de M)".

### 3. Columnas a generar

Para la referencia tecnica detallada de columnas de entrada y reglas, lee `references/columnas_y_reglas.md`. Para un ejemplo completo, lee `references/ejemplo_output.md`.

Las columnas se dividen en: **caracteristicas** (datos estructurados), **secciones de contenido** (texto editorial), y **columnas Shopify** (campos del importador).

---

#### Caracteristicas (columnas individuales)

**`caract_marca`** — Marca del producto (la refaccion, no el vehiculo). Usar el campo `marca_normalizada`. Ej: "Original Frey", "Embler", "Mahle".

**`caract_origen`** — Origen del producto. Usar `origen` si existe. Si no hay dato, dejar vacio. Ej: "Importado", "Nacional".

**`caract_tipo_vehiculo`** — Tipo de vehiculo al que aplica. Usar `tipo_vehiculo`. Ej: "Carro/Camioneta", "Moto/Cuatriciclo", "Linea Pesada".

**`caract_compatibilidad`** — Texto en parrafo describiendo los vehiculos compatibles, agrupados por marca y serie.

**Regla principal:** si `caract_compatibilidad_propuesta` viene poblada en el batch, usala tal cual (ya esta agrupada y normalizada). Si quieres mejorar redaccion, manten todos los modelos y anios — no inventes ni omitas.

**Si `caract_compatibilidad_propuesta` esta vacia** (no se encontro el bloque `APLICA PARA LOS SIGUIENTES MODELOS:` en la descripcion):
- Si el `titulo` menciona modelos: "Compatible con modelos BMW 325i, 330i, 530i, X3, X5 y Z4. Confirma compatibilidad exacta con tu numero de VIN antes de comprar."
- Si no hay nada: dejar vacio. **No inventar** — un error de compatibilidad genera devoluciones y perdida de confianza.

---

#### Secciones de contenido

**`seccion_descripcion`** (texto)

Esta es la columna de contenido mas importante. Define como el cliente entiende y compra el producto. Los datos de MercadoLibre vienen con formato de marketplace (MAYUSCULAS, advertencias, listas sin formato), y el objetivo es transformarlos en una **ficha tecnica profesional**.

**Longitud:** 350-550 palabras en espanol, distribuidas en **5 parrafos**. Sin titulos ni listas dentro del texto — todo en parrafos corridos. El HTML lo agrega `shopify_body_html`.

**Tono:** tecnico-comercial. El cliente tipico es mecanico de autos europeos o duenio que sabe de motores. Usar terminologia precisa (codigos de motor N52/N63/M271/B47, plataformas E46/E90/F30/W205/B8, sistemas mecanicos, terminos en espanol mexicano). **Evitar relleno comercial vacio** ("la mejor calidad", "100% garantizado", "calidad superior"). Cada afirmacion debe estar respaldada por un dato real del input.

**Estructura (5 parrafos):**

1. **Identificacion tecnica de la pieza** (60-90 palabras). Que es exactamente la pieza, su funcion mecanica dentro del sistema, y a que familia/sistema pertenece. Si es un sensor MAP, explicar que mide la presion del colector y para que la usa la ECU; si es una junta de cabeza, que sella la camara de combustion y previene fugas; si es un amortiguador, su rol en la dinamica del chasis. Fuentes: `titulo`, `mc_nombre_match` (nombre tecnico ERP — suele ser mas preciso que el titulo ML), `categoria` (path completo), `subcategoria`, `modelo_atributo` (frecuentemente trae codigo de motor).

2. **Aplicacion y compatibilidad** (80-120 palabras). Resumen de las familias/series compatibles. Si `num_compatibilidades > 0`, mencionar el numero total de configuraciones y referirse al cliente a la **seccion de compatibilidades** de la ficha para el detalle ("Aplica para X configuraciones de la familia BMW Serie 5, X3 y X5 — ver detalle en compatibilidades"). Si `num_compatibilidades == 0`, listar los modelos del titulo y pedir verificar con VIN. Mencionar codigos de motor y plataformas/chasis cuando aparezcan en `modelo_atributo`, `mc_nombre_match` o el bloque parseado. Fuentes: `caract_compatibilidad_propuesta`, `marcas_vehiculo`, `num_compatibilidades`, `modelo_atributo`, `tipo_vehiculo`, `titulo`.

3. **Especificaciones tecnicas y referencias cruzadas** (50-80 palabras). Numero de parte, codigo OEM, lado de instalacion (izquierdo/derecho/par), origen. Si hay `mc_nombre_match` Microsip distinto del titulo ML, mencionar la referencia interna del ERP cuando sea util al cliente. Si no hay numero de parte ni OEM, omite el parrafo o resume con "Verifica con tu numero de VIN para confirmar la pieza correcta" en lugar de inventar codigos. Fuentes: `numero_parte`, `codigo_oem`, `lado`, `origen`, `mc_sku_match`, `mc_nombre_match`.

4. **Que incluye / como es la pieza** (50-90 palabras). Si hay `incluye_texto` poblado, redactarlo como parrafo: "Este juego incluye: junta de cabeza, sellos de valvula, juntas de admision y escape, junta de tapa de punterias." Si no hay `incluye_texto` pero el `titulo` o `mc_nombre_match` mencionan "JUEGO", "KIT", "PAR", "SET", indicarlo igual ("Se vende como kit completo"). Si es pieza individual, describir caracteristicas mecanicas relevantes inferibles del nombre tecnico (tipo de fijacion, configuracion). **No inventar dimensiones ni pesos.** Fuentes: `incluye_texto`, `titulo`, `mc_nombre_match`.

5. **Marca, posicionamiento y garantia** (60-90 palabras). Marca normalizada con contexto:
   - **Original Frey**: marca importada especializada en refacciones para vehiculos europeos premium, fabricacion alemana con calidad equivalente al equipo original (OEM-grade).
   - **Embler**: marca propia de Embler Autopartes Europeas, especializada en BMW, Mercedes-Benz, Audi, Volkswagen, Porsche, Volvo, Mini Cooper y Jaguar.
   - **Mahle, Bosch, Hella, Lemforder, Pierburg, Bilstein, Sachs, ZF, Febi, Corteco, Vaico**: proveedores OEM/OES (suministran a la fabrica original); mencionar que es la misma calidad que la pieza original del vehiculo.
   - Marcas desconocidas: mencionar la marca tal cual sin posicionamiento inventado.
   Cerrar con la garantia exacta extraida de `garantia` (normalmente "Garantia del vendedor: 30 dias" o "90 dias"). Convertir a redaccion natural: "Garantia de 30 dias contra defectos de fabrica." Fuentes: `marca_normalizada`, `marca`, `garantia`.

**Reglas duras:**

- **No inventar datos.** Si un campo esta vacio, no rellenar con texto generico — saltar el parrafo o resumir lo disponible.
- **No copiar literalmente texto en MAYUSCULAS** de la descripcion ML. Reescribir en mayusculas y minusculas normales.
- **No incluir advertencias** del estilo "PARA EVITARTE MOLESTIAS, PIDE TU VIN" — eso va en `seccion_antes_de_comprar`.
- **No incluir info de envio o devoluciones** — esas tienen sus propias secciones.
- Sin emojis, sin signos de admiracion seguidos.
- Espanol neutro de Mexico.
- Si la `descripcion` ML original es rica en datos tecnicos, refraseala manteniendo todos los datos pero con redaccion profesional. **No descartes datos tecnicos.**
- Si la `descripcion` ML esta vacia o es muy corta, apoyate en `titulo` + `mc_nombre_match` + atributos para construir los 5 parrafos. Si aun asi quedan parrafos sin material, que sean cortos antes que rellenos con basura.

---

**`seccion_compatibilidades`** (texto, lista por linea)

**NUEVA columna**. Lista completa de vehiculos compatibles, una linea por configuracion, exactamente como aparece en el catalogo. **No omitir ninguno**, no truncar.

**Regla:** copiar tal cual `seccion_compatibilidades_propuesta` del batch JSON. Si esta vacio, dejar la columna vacia (y agregar un flag a `revision_humana`).

Formato de cada linea: `Marca Modelo Anios — N cil X.XL Tipo-Motor`. Ejemplo:
```
BMW 550i Gran Turismo 2011-2014 — 8 cil 4.4L Bi-Turbo
BMW X5 5.0i Premium 2011-2013 — 8 cil 4.4L Bi-Turbo
BMW 750Li 2010-2013 — 8 cil 4.4L Aspiración natural
```

Esta lista se renderiza como `<ul>` dentro del `shopify_body_html` bajo el titulo "Compatibilidades".

---

**`seccion_antes_de_comprar`** (texto)

Seccion semi-fija. Redactar:

> "Para garantizar que recibas la pieza correcta para tu vehiculo, necesitamos el numero de serie (VIN) de tu auto antes de procesar el pedido. Esto evita errores, tiempos perdidos y devoluciones innecesarias. Escribenos y con gusto confirmamos compatibilidad."

Si el producto tiene `numero_parte` o `codigo_oem`, agregar al final: "Tambien puedes verificar con el numero de parte [NUMERO] o codigo OEM [CODIGO]."

---

**`seccion_envio`** (texto)

Texto fijo:

> "Tenemos stock disponible para entrega inmediata. Enviamos el mismo dia de tu pago a Ciudad de Mexico y a todo el pais via DHL o FedEx."

Si el `titulo` o `mc_nombre_match` contienen "JUEGO" / "KIT" / "PAR" / "SET", o si `incluye_texto` esta poblado, agregar: "Este producto se vende como [juego/kit/par/set] completo."

---

**`seccion_devoluciones`** (texto fijo, no modificar)

```
Aceptamos devoluciones dentro de los 30 días posteriores a la entrega, sin importar el motivo. Para que tu devolución proceda, la pieza debe estar sin uso, sin instalar y en su empaque original.

Asegura el ajuste perfecto: Una vez realizada tu compra, un asesor te contactará brevemente para validar la compatibilidad con tu número VIN y garantizar que recibas exactamente lo que tu auto necesita.

Consulta nuestra politica completa aquí
```

---

**`seccion_faq`** (JSON array)

3-5 preguntas frecuentes especificas del producto:

```json
[{"pregunta": "...", "respuesta": "..."}]
```

Incluir siempre: compatibilidad, que incluye el producto (si es kit), garantia. Agregar original-vs-generico y como-verificar solo si hay datos de origen, numero de parte o codigo OEM. Si `num_compatibilidades > 5`, una FAQ tipo "¿Como confirmo compatibilidad con mi modelo exacto?" referenciando la seccion de compatibilidades + VIN.

Las respuestas deben ser **factuales** — si no hay datos detallados, la respuesta es "verifica con tu numero de VIN" en lugar de inventar vehiculos. Un cliente que compra la pieza equivocada genera una devolucion costosa.

---

**`productos_relacionados`** (JSON array de strings)

Hasta 5 SKUs del mismo CSV. El batch JSON incluye `indice_catalogo` con SKU, titulo, subcategoria y marca_normalizada de cada producto.

Criterios: misma subcategoria + misma marca de vehiculo (por interseccion con `marcas_vehiculo`), o productos complementarios (ej: junta de motor → retenes, sellos de valvula).

---

#### Columnas Shopify

Para la referencia completa del mapeo, lee `references/columnas_y_reglas.md`.

**`shopify_handle`** — URL slug del producto. Reglas:
- Tomar `shopify_title` (ya limpio), convertir a minusculas, quitar acentos.
- Reemplazar espacios y caracteres especiales por guiones, eliminar guiones consecutivos.
- Para garantizar unicidad cuando el SKU se repite entre listings ML, anadir el SKU al final.
- Ej: titulo "Juego de Juntas de Motor BMW 750i 550i", sku "XB-N63-03" → `juego-juntas-motor-bmw-750i-550i-xb-n63-03`.

**`shopify_title`** — Titulo limpio del producto:
- Quitar el "&" o "& " final (truncamiento de ML).
- Capitalizacion correcta: primera letra de cada palabra significativa en mayuscula, articulos/preposiciones en minuscula.
- Mantener siglas y modelos en formato original: BMW, X5, N63, E90, 550i, 750Li.
- Max 255 caracteres.
- Ej: "Juego De Juntas De Motor Completo Bmw 750i 550i X5 X6 &" → "Juego de Juntas de Motor Completo BMW 750i 550i X5 X6"

**`shopify_body_html`** — Descripcion completa en HTML que combina las secciones. Estructura:

```html
<h2>Descripcion</h2>
{seccion_descripcion convertida a parrafos <p>}

<h2>Compatibilidades</h2>
<ul>
  <li>{cada linea de seccion_compatibilidades como <li>}</li>
  ...
</ul>

<h2>Antes de Comprar</h2>
<p>{seccion_antes_de_comprar}</p>

<h2>Envio</h2>
<p>{seccion_envio}</p>

<h2>Politica de Devolucion</h2>
{seccion_devoluciones convertida a parrafos <p>}

<h2>Preguntas Frecuentes</h2>
{seccion_faq convertida a bloques <h3>pregunta</h3><p>respuesta</p>}
```

Si `seccion_compatibilidades` esta vacia, omitir el bloque `<h2>Compatibilidades</h2>` completo (no dejar `<ul></ul>` vacio). Sin estilos inline ni clases CSS — Shopify aplica el tema.

**`shopify_product_category`** — Siempre `Vehicles & Parts > Vehicle Parts & Accessories`.

**`shopify_type`** — Tipo que alimenta las collections automaticas. Mapear desde `subcategoria`:

| Palabras clave | shopify_type |
|---|---|
| motor, juntas, culata, turbo, valvulas, admision, escape, enfriamiento, distribucion, carter, biela, ciguenal, arbol de levas | Motor |
| frenos, discos, pastillas, calipers, balatas, tambores | Frenos |
| suspension, amortiguadores, brazos, rotulas, bujes, barras, resortes, soportes | Suspensión |
| electrico, sensores, bobinas, alternador, modulos, computadora, relay, fusible, motor de arranque | Sistema Eléctrico |
| carroceria, faros, espejos, defensas, cofre, salpicaderas, parrilla, calavera, moldura | Carrocería |
| filtros | Filtros |
| transmision, embrague, clutch, convertidor, volante motor | Transmisión |
| direccion, cremallera, terminales | Dirección |
| accesorios | Accesorios |
| tuning | Tuning |
| caja de herramientas, extracci, herramientas | Herramientas |

**`shopify_tags`** — Marcas de vehiculo compatibles, separadas por coma. **Usar `marcas_vehiculo` del batch directamente** (ya viene ordenada y normalizada). Si esta vacio, fallback a parsear marcas del titulo.

Marcas validas: `BMW`, `Mercedes-Benz`, `Audi`, `Volkswagen`, `Porsche`, `Volvo`, `Mini`, `Land Rover`, `Jaguar`, `SEAT`, `Smart`, `Fiat`, `Alfa Romeo`, `Bentley`, `Rolls-Royce`.

Ej: si `marcas_vehiculo` = `["BMW", "Audi"]` → `"BMW, Audi"`.

**IMPORTANTE:** los tags son marcas de VEHICULO, no de producto. "Original Frey" NO es un tag.

**`shopify_published`** — Siempre `TRUE`. La visibilidad real la controla `shopify_status`.

**`shopify_option1_name`** / **`shopify_option1_value`** — Para productos sin variantes (mayoria): `"Title"` / `"Default Title"`. Si el producto tiene `lado` ("Izquierdo"/"Derecho"), considerar `"Posición"` / `"Izquierdo"` o `"Derecho"`, pero esto requiere validacion humana — por defecto usar Title/Default Title.

**`shopify_variant_sku`** — Directo de `sku`. Si esta vacio, flaggear en `revision_humana`.

**`shopify_variant_price`** — Directo de `precio`. Sin simbolo de moneda, numero con decimales. Ej: `"1850.00"`.

**`shopify_variant_compare_price`** — Vacio.

**`shopify_variant_weight`** — Vacio (sin dato fuente).

**`shopify_variant_weight_unit`** — Siempre `"kg"`.

**`shopify_image_src`** — Vacio (sin URLs).

**`shopify_image_alt_text`** — Texto alt descriptivo. Formato: `"{Nombre del producto} {Marca producto} para {Marca vehiculo}"`. Max 125 caracteres. Ej: `"Juego de juntas de motor completo Original Frey para BMW"`.

**`shopify_seo_title`** — Max 60 caracteres. Formato: `{Producto corto} {Vehiculo} | Embler`. Ej: `"Juntas Motor BMW 750i 550i Original Frey | Embler"` (49 chars). Si supera 60, acortar producto, "| Embler" siempre al final.

**`shopify_seo_description`** — Max 155 caracteres. Resumir que es + para que vehiculo(s) + marca + call-to-action. Si hay compatibilidades parseadas, incluir hasta 3 modelos. Ej: `"Juego de juntas de motor para BMW 750i, 550i, X5. Marca Original Frey. Envio inmediato a todo Mexico."` (108 chars).

**`shopify_status`** — Siempre `"draft"` por defecto. El humano lo activa despues de revisar fotos/peso/revision_humana.

---

#### `revision_humana` (texto o vacio)

Lista de pendientes especifica por producto en formato `[ACCION] detalle`. Acciones:

- `[BUSCAR]` — Dato faltante obtenible de otra fuente (catalogo del proveedor).
- `[VERIFICAR]` — Dato inferido que necesita confirmacion humana.
- `[INCLUIR]` — Informacion para agregar manualmente (fotos, peso).
- `[REVISAR]` — Contenido generado que podria necesitar ajuste editorial.
- `[ANALIZAR]` — Decision de negocio (precio, clasificacion).

**Reglas:**

1. `num_compatibilidades == 0` Y sin modelos en titulo → `[BUSCAR] Compatibilidad vehicular: no se pudo extraer de la descripción y el titulo no menciona modelos.`
2. `num_compatibilidades == 0` pero el titulo SI menciona modelos → `[VERIFICAR] Compatibilidad inferida del titulo — confirmar modelos y anos.`
3. Sin `codigo_oem` Y sin `numero_parte` → `[BUSCAR] Numero de parte o codigo OEM faltantes.`
4. Sin `descripcion` original → `[REVISAR] Descripcion generada sin datos fuente — verificar precision.`
5. Sin `sku` → `[INCLUIR] SKU faltante — asignar antes de publicar.`
6. `marca_normalizada` vacia o desconocida → `[ANALIZAR] Marca no identificada — confirmar fabricante.`
7. SKU duplicado en otras filas del mismo batch (mismo SKU en varios listings ML) → `[ANALIZAR] SKU duplicado: tambien presente en filas X. Considerar consolidar en Shopify.`
8. **Siempre al final** → `[INCLUIR] Peso y dimensiones para calculo de envio.`
9. **Siempre al final** → `[INCLUIR] Fotografias del producto.`

Items 8-9 aplican a todos los productos. Items 1-7 son especificos. Separa cada flag con `\n`.

### 4. Formato de resultados

El JSON de resultados para `03_guardar_batch_v2.py`:

```json
{
  "resultados": [
    {
      "_fila_original": 0,
      "caract_marca": "Original Frey",
      "caract_origen": "Importado",
      "caract_tipo_vehiculo": "Carro/Camioneta",
      "caract_compatibilidad": "Aplica para: BMW 550i: 550i Gran Turismo (2011-2014). BMW 750i: 750Li (2010-2013). BMW X5: X5 5.0i Premium (2011-2013).",
      "seccion_descripcion": "Parrafo 1...\n\nParrafo 2...\n\nParrafo 3...\n\nParrafo 4...\n\nParrafo 5...",
      "seccion_compatibilidades": "BMW 550i Gran Turismo 2011-2014 — 8 cil 4.4L Bi-Turbo\nBMW 750Li 2010-2013 — 8 cil 4.4L Aspiración natural\nBMW X5 5.0i Premium 2011-2013 — 8 cil 4.4L Bi-Turbo",
      "seccion_antes_de_comprar": "Para garantizar que recibas la pieza correcta...",
      "seccion_envio": "Tenemos stock disponible para entrega inmediata...",
      "seccion_devoluciones": "Aceptamos devoluciones dentro de los 30 días...",
      "seccion_faq": [{"pregunta": "...", "respuesta": "..."}],
      "productos_relacionados": ["SKU1", "SKU2"],
      "shopify_handle": "juego-juntas-motor-bmw-750i-550i-x5-x6-xb-n63b44-03",
      "shopify_title": "Juego de Juntas de Motor Completo BMW 750i 550i X5 X6",
      "shopify_body_html": "<h2>Descripcion</h2><p>...</p><h2>Compatibilidades</h2><ul><li>...</li></ul>...",
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
      "shopify_seo_description": "Juego de juntas de motor para BMW 750i, 550i, X5. Marca Original Frey. Envio inmediato a todo Mexico.",
      "shopify_status": "draft",
      "revision_humana": "[INCLUIR] Peso y dimensiones para calculo de envio.\n[INCLUIR] Fotografias del producto."
    }
  ]
}
```

Guarda este JSON en `new-output/<hoja>/{categoria}_batch_result.json` antes de pasarlo al script.

### 5. Reporte final

Al terminar la categoria, reporta:
- Total de filas procesadas.
- Ruta del CSV: `new-output/<hoja>/{categoria}_enriched.csv`.
- Estadisticas:
  - % con `num_compatibilidades > 0` (esperado 80-95%).
  - % con `incluye_texto` poblado (bajo — solo kits).
  - Distribucion de palabras en `seccion_descripcion` (deberia caer entre 350-550).
  - Productos con `revision_humana` no vacia.

## Contexto del negocio

Embler vende autopartes para vehiculos europeos (principalmente BMW, Mercedes-Benz). Las marcas de producto principales son Original Frey (61%) y Embler (21%) — son las marcas de la refaccion, no del vehiculo. No confundir: "BMW" es la marca del auto, "Original Frey" es quien fabrica la pieza.

El cliente tipico busca refacciones especificas por modelo, numero de parte, o tipo de pieza. El contenido debe ayudarle a:
1. Confirmar que la pieza es para su vehiculo (compatibilidades, VIN).
2. Entender que incluye el producto (kit vs pieza individual).
3. Tener confianza en la calidad (marca, garantia, codigo OEM).

**Orden de confianza para el dato de compatibilidad** (de mayor a menor):
1. Bloque `APLICA PARA LOS SIGUIENTES MODELOS:` en `descripcion` ✓ (lo que pre-extrae `02_preparar_batch_v2.py`).
2. Titulo del producto (menciones casuales).
3. Columna `Compatibilidades` cruda — **descartada, esta incompleta** (en ML actua como requisito de publicacion, no como catalogo fiel).
