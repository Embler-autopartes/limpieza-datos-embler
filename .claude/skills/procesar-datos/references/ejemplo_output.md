# Ejemplo Completo de Output

Este ejemplo muestra el output esperado del flujo unificado: descripcion tecnica de 5 parrafos + compatibilidades extraidas deterministicamente del bloque "APLICA PARA LOS SIGUIENTES MODELOS:" + INCLUYE parseado.

## Producto de entrada (datos completos)

JSON del batch (campos relevantes):

```json
{
  "_fila_original": 0,
  "id_ml": "MLM1234567",
  "categoria": "Accesorios para Vehículos > Refacciones Autos y Camionetas > Motor > Juntas",
  "titulo": "Juego De Juntas De Motor Completo Bmw 750i 550i X5 X6 &",
  "descripcion": "JUEGO DE JUNTAS DE MOTOR COMPLETO PARA BMW INCLUYE: JUNTA DE CABEZA SELLOS DE VALVULA JUNTAS DE ADMISION Y DE ESCAPE JUNTA DE TAPA DE PUNTERIAS MUY IMPORTANTE: PARA EVITARTE MOLESTIAS APLICA PARA LOS SIGUIENTES MODELOS: BMW 550i GRAN TURISMO 2011 AL 2014 8 CILINDROS 4.4 LITROS BI TURBO BMW 750Li 2010 AL 2013 8 CILINDROS 4.4 LITROS ASPIRACION NATURAL BMW X5 5.0i PREMIUM 2011 AL 2013 8 CILINDROS 4.4 LITROS BI TURBO BMW X6 50i M PERFORMANCE 2013 AL 2014 8 CILINDROS 4.4 LITROS BI TURBO ENVIOS A CDMX...",
  "precio": "1850",
  "sku": "XB-N63B44-03",
  "garantia": "Garantía del vendedor: 30 días",
  "marca": "ORIGINAL FREY GERMAN TECHNOLOGY QUALITY",
  "numero_parte": "XB-N63B44-03",
  "tipo_vehiculo": "Carro/Camioneta",
  "origen": "Importado",
  "codigo_oem": "11127571692",
  "modelo_atributo": "BMW N63",
  "lado": "",
  "mc_sku_match": "JJM-N63-001",
  "mc_nombre_match": "JUEGO DE JUNTAS DE MOTOR COMPLETO BMW MOTOR N63",
  "marca_normalizada": "Original Frey",
  "subcategoria": "juntas",
  "categoria_archivo": "refacciones_motor",

  // Pre-parseados deterministicamente desde la descripcion:
  "num_compatibilidades": 4,
  "marcas_vehiculo": ["BMW"],
  "caract_compatibilidad_propuesta": "Aplica para: BMW 550i: 550i Gran Turismo (2011-2014). BMW 750Li: 750Li (2010-2013). BMW X5: X5 5.0i Premium (2011-2013). BMW X6: X6 50i M Performance (2013-2014).",
  "seccion_compatibilidades_propuesta": "BMW 550i Gran Turismo 2011-2014 — 8 cil 4.4L Bi-Turbo\nBMW 750Li 2010-2013 — 8 cil 4.4L Aspiración natural\nBMW X5 5.0i Premium 2011-2013 — 8 cil 4.4L Bi-Turbo\nBMW X6 50i M Performance 2013-2014 — 8 cil 4.4L Bi-Turbo",
  "incluye_texto": "Junta de cabeza sellos de valvula juntas de admision y de escape junta de tapa de punterias"
}
```

## Output esperado

### caract_marca

```
Original Frey
```

### caract_origen

```
Importado
```

### caract_tipo_vehiculo

```
Carro/Camioneta
```

### caract_compatibilidad

(copiado de `caract_compatibilidad_propuesta`)

```
Aplica para: BMW 550i: 550i Gran Turismo (2011-2014). BMW 750Li: 750Li (2010-2013). BMW X5: X5 5.0i Premium (2011-2013). BMW X6: X6 50i M Performance (2013-2014).
```

### seccion_descripcion

(5 parrafos, ~400 palabras, tono tecnico-comercial)

```
Juego completo de juntas de motor para los modelos BMW equipados con motor N63 4.4L V8 biturbo. Esta familia de juntas constituye la totalidad de los sellos perimetrales del motor: junta de cabeza, sellos de valvula, juntas de colectores de admision y escape, y junta de tapa de punterias. Su funcion es mantener la estanqueidad entre las camaras de combustion, los conductos de aceite y los pasajes de refrigerante durante todo el ciclo termico del motor.

El N63 es el V8 biturbo de 4.4 litros que equipa la familia BMW Serie 5, Serie 7 y la gama X. Este juego cubre cuatro configuraciones especificas: 550i Gran Turismo (2011-2014), 750Li (2010-2013), X5 5.0i Premium (2011-2013) y X6 50i M Performance (2013-2014). El listado completo con anos y motorizaciones aparece en la seccion de Compatibilidades de esta ficha. Su construccion all-aluminum y la disposicion "hot V" del N63 — con turbocompresores ubicados en el angulo interior de las bancadas — somete a las juntas a un regimen termico exigente, por lo que el cambio del juego completo es practica recomendada al desarmar el motor por mantenimiento mayor.

Este juego se referencia con el numero de parte XB-N63B44-03 y el codigo OEM 11127571692, ambos validables contra el catalogo del fabricante. Producto importado. La referencia interna del ERP es JJM-N63-001 (SKU del catalogo Microsip), util si se cruza con la red de talleres aliados.

El kit incluye junta de cabeza, sellos de valvula, juntas de admision y de escape, y junta de tapa de punterias. Esta composicion permite ejecutar un cambio de junta de cabeza o un overhaul parcial sin comprar refacciones por separado, reduciendo tiempos de taller y asegurando que todos los componentes provengan del mismo lote. Se vende como kit completo en una sola caja.

Fabricado por Original Frey, marca importada especializada en refacciones para vehiculos europeos premium con calidad equivalente al equipo original (OEM-grade aleman). Garantia de 30 dias contra defectos de fabrica.
```

### seccion_compatibilidades

(copiado de `seccion_compatibilidades_propuesta` — una linea por configuracion, sin truncar)

```
BMW 550i Gran Turismo 2011-2014 — 8 cil 4.4L Bi-Turbo
BMW 750Li 2010-2013 — 8 cil 4.4L Aspiración natural
BMW X5 5.0i Premium 2011-2013 — 8 cil 4.4L Bi-Turbo
BMW X6 50i M Performance 2013-2014 — 8 cil 4.4L Bi-Turbo
```

### seccion_antes_de_comprar

```
Para garantizar que recibas la pieza correcta para tu vehiculo, necesitamos el numero de serie (VIN) de tu auto antes de procesar el pedido. Esto evita errores, tiempos perdidos y devoluciones innecesarias. Escribenos y con gusto confirmamos compatibilidad. Tambien puedes verificar con el numero de parte XB-N63B44-03 o codigo OEM 11127571692.
```

### seccion_envio

(detecto "JUEGO" en el titulo → menciono que es kit completo)

```
Tenemos stock disponible para entrega inmediata. Enviamos el mismo dia de tu pago a Ciudad de Mexico y a todo el pais via DHL o FedEx. Este producto se vende como kit completo.
```

### seccion_devoluciones

(texto fijo)

```
Aceptamos devoluciones dentro de los 30 días posteriores a la entrega, sin importar el motivo. Para que tu devolución proceda, la pieza debe estar sin uso, sin instalar y en su empaque original.

Asegura el ajuste perfecto: Una vez realizada tu compra, un asesor te contactará brevemente para validar la compatibilidad con tu número VIN y garantizar que recibas exactamente lo que tu auto necesita.

Consulta nuestra politica completa aquí
```

### seccion_faq

```json
[
  {
    "pregunta": "¿Es compatible con mi vehiculo?",
    "respuesta": "Este juego de juntas es compatible con BMW 550i Gran Turismo (2011-2014), 750Li (2010-2013), X5 5.0i Premium (2011-2013) y X6 50i M Performance (2013-2014), todos con motor N63 4.4L V8 biturbo. Verifica con tu numero de VIN antes de comprar."
  },
  {
    "pregunta": "¿Que incluye el juego de juntas?",
    "respuesta": "Junta de cabeza, sellos de valvula, juntas de admision y escape, y junta de tapa de punterias. Es un kit completo para overhaul parcial."
  },
  {
    "pregunta": "¿Tiene garantia?",
    "respuesta": "Si, garantia del vendedor por 30 dias contra defectos de fabrica."
  },
  {
    "pregunta": "¿Es una pieza original o generica?",
    "respuesta": "Es una refaccion Original Frey, marca alemana especializada en autopartes para vehiculos europeos premium con calidad equivalente al equipo original. Producto importado. Codigo OEM de referencia: 11127571692."
  },
  {
    "pregunta": "¿Como verifico que es la pieza correcta?",
    "respuesta": "Consulta el numero de parte XB-N63B44-03 o el codigo OEM 11127571692. Tambien puedes enviarnos tu numero de VIN y confirmamos compatibilidad."
  }
]
```

### productos_relacionados

```json
["MB2ML", "XB-N63B44-05", "RET-N63-01"]
```

---

### Columnas Shopify

### shopify_handle

```
juego-juntas-motor-completo-bmw-750i-550i-x5-x6-xb-n63b44-03
```

### shopify_title

```
Juego de Juntas de Motor Completo BMW 750i 550i X5 X6
```

### shopify_body_html

```html
<h2>Descripcion</h2>
<p>Juego completo de juntas de motor para los modelos BMW equipados con motor N63 4.4L V8 biturbo. Esta familia de juntas constituye la totalidad de los sellos perimetrales del motor: junta de cabeza, sellos de valvula, juntas de colectores de admision y escape, y junta de tapa de punterias. Su funcion es mantener la estanqueidad entre las camaras de combustion, los conductos de aceite y los pasajes de refrigerante durante todo el ciclo termico del motor.</p>
<p>El N63 es el V8 biturbo de 4.4 litros que equipa la familia BMW Serie 5, Serie 7 y la gama X. Este juego cubre cuatro configuraciones especificas: 550i Gran Turismo (2011-2014), 750Li (2010-2013), X5 5.0i Premium (2011-2013) y X6 50i M Performance (2013-2014). El listado completo con anos y motorizaciones aparece en la seccion de Compatibilidades de esta ficha.</p>
<p>Este juego se referencia con el numero de parte XB-N63B44-03 y el codigo OEM 11127571692, ambos validables contra el catalogo del fabricante. Producto importado.</p>
<p>El kit incluye junta de cabeza, sellos de valvula, juntas de admision y de escape, y junta de tapa de punterias. Se vende como kit completo en una sola caja.</p>
<p>Fabricado por Original Frey, marca importada especializada en refacciones para vehiculos europeos premium con calidad equivalente al equipo original. Garantia de 30 dias contra defectos de fabrica.</p>

<h2>Compatibilidades</h2>
<ul>
  <li>BMW 550i Gran Turismo 2011-2014 — 8 cil 4.4L Bi-Turbo</li>
  <li>BMW 750Li 2010-2013 — 8 cil 4.4L Aspiración natural</li>
  <li>BMW X5 5.0i Premium 2011-2013 — 8 cil 4.4L Bi-Turbo</li>
  <li>BMW X6 50i M Performance 2013-2014 — 8 cil 4.4L Bi-Turbo</li>
</ul>

<h2>Antes de Comprar</h2>
<p>Para garantizar que recibas la pieza correcta para tu vehiculo, necesitamos el numero de serie (VIN) de tu auto antes de procesar el pedido. Esto evita errores, tiempos perdidos y devoluciones innecesarias. Escribenos y con gusto confirmamos compatibilidad. Tambien puedes verificar con el numero de parte XB-N63B44-03 o codigo OEM 11127571692.</p>

<h2>Envio</h2>
<p>Tenemos stock disponible para entrega inmediata. Enviamos el mismo dia de tu pago a Ciudad de Mexico y a todo el pais via DHL o FedEx. Este producto se vende como kit completo.</p>

<h2>Politica de Devolucion</h2>
<p>Aceptamos devoluciones dentro de los 30 días posteriores a la entrega, sin importar el motivo. Para que tu devolución proceda, la pieza debe estar sin uso, sin instalar y en su empaque original.</p>
<p>Asegura el ajuste perfecto: Una vez realizada tu compra, un asesor te contactará brevemente para validar la compatibilidad con tu número VIN y garantizar que recibas exactamente lo que tu auto necesita.</p>
<p>Consulta nuestra politica completa aquí</p>

<h2>Preguntas Frecuentes</h2>
<h3>¿Es compatible con mi vehiculo?</h3>
<p>Este juego de juntas es compatible con BMW 550i Gran Turismo (2011-2014), 750Li (2010-2013), X5 5.0i Premium (2011-2013) y X6 50i M Performance (2013-2014), todos con motor N63 4.4L V8 biturbo. Verifica con tu numero de VIN antes de comprar.</p>
<h3>¿Que incluye el juego de juntas?</h3>
<p>Junta de cabeza, sellos de valvula, juntas de admision y escape, y junta de tapa de punterias. Es un kit completo para overhaul parcial.</p>
<h3>¿Tiene garantia?</h3>
<p>Si, garantia del vendedor por 30 dias contra defectos de fabrica.</p>
<h3>¿Es una pieza original o generica?</h3>
<p>Es una refaccion Original Frey, marca alemana especializada en autopartes para vehiculos europeos premium con calidad equivalente al equipo original. Producto importado. Codigo OEM de referencia: 11127571692.</p>
<h3>¿Como verifico que es la pieza correcta?</h3>
<p>Consulta el numero de parte XB-N63B44-03 o el codigo OEM 11127571692. Tambien puedes enviarnos tu numero de VIN y confirmamos compatibilidad.</p>
```

### shopify_product_category
```
Vehicles & Parts > Vehicle Parts & Accessories
```

### shopify_type
```
Motor
```

### shopify_tags
```
BMW
```
(de `marcas_vehiculo` extraido del bloque APLICA PARA)

### shopify_published
```
TRUE
```

### shopify_option1_name / shopify_option1_value
```
Title / Default Title
```

### shopify_variant_sku
```
XB-N63B44-03
```

### shopify_variant_price
```
1850.00
```

### shopify_variant_compare_price / shopify_variant_weight / shopify_image_src
(todos vacios)

### shopify_variant_weight_unit
```
kg
```

### shopify_image_alt_text
```
Juego de juntas de motor completo Original Frey para BMW
```

### shopify_seo_title
```
Juntas Motor BMW 750i 550i Original Frey | Embler
```
(49 caracteres)

### shopify_seo_description
```
Juego de juntas de motor para BMW 750i, 550i, X5. Marca Original Frey. Envio inmediato a todo Mexico.
```
(101 caracteres — incluye 3 modelos del bloque parseado)

### shopify_status
```
draft
```

### revision_humana

```
[INCLUIR] Peso y dimensiones para calculo de envio.
[INCLUIR] Fotografias del producto.
```

Este producto tiene todos los datos criticos: 4 compatibilidades parseadas, OEM, marca normalizada, numero de parte, INCLUYE detectado. Solo le faltan los universales (peso/fotos).

---

## Ejemplo SIN compatibilidades parseadas (datos limitados)

### Entrada

```json
{
  "_fila_original": 5,
  "titulo": "Sensor Map Bmw 325i 330i 530i X3 X5 Z4 &",
  "descripcion": "",
  "sku": "SEN-MAP-01",
  "precio": "650",
  "garantia": "Garantia del vendedor: 30 dias",
  "marca": "EMBLER",
  "numero_parte": "SEN-MAP-01",
  "tipo_vehiculo": "Carro/Camioneta",
  "origen": "",
  "codigo_oem": "",
  "modelo_atributo": "",
  "lado": "",
  "mc_nombre_match": "",
  "marca_normalizada": "Embler",
  "subcategoria": "sensores",

  "num_compatibilidades": 0,
  "marcas_vehiculo": [],
  "caract_compatibilidad_propuesta": "",
  "seccion_compatibilidades_propuesta": "",
  "incluye_texto": ""
}
```

### caract_compatibilidad

(no hay datos parseados; inferimos del titulo)

```
Compatible con modelos BMW 325i, 330i, 530i, X3, X5 y Z4. Confirma compatibilidad exacta con tu numero de VIN antes de comprar.
```

### seccion_descripcion

(5 parrafos pero algunos cortos por falta de datos)

```
Sensor MAP (Manifold Absolute Pressure) para diversos modelos BMW. Su funcion es medir la presion del aire en el colector de admision y enviar la lectura a la unidad de control electronico (ECU) del motor; con ese dato la ECU ajusta la mezcla aire-combustible y el avance de encendido en tiempo real. Una falla del sensor MAP suele manifestarse como ralenti irregular, perdida de potencia, marcha minima erratica o codigos de error en el sistema de admision.

Compatible con los modelos BMW 325i, 330i, 530i, X3, X5 y Z4 referenciados en el titulo del producto. La descripcion del listing no incluye un detalle de configuraciones por ano y motorizacion, por lo que es indispensable confirmar el ano y el codigo de motor del vehiculo con el numero de VIN antes de comprar — el sensor MAP varia segun la version de motor instalada.

Numero de parte interno: SEN-MAP-01. Sin codigo OEM disponible en este listing; recomendamos verificar la pieza original del vehiculo y compararla con el numero de parte antes de instalar.

Producto vendido como pieza individual.

Marca Embler, fabricante propio de Embler Autopartes Europeas, especializado en refacciones para BMW, Mercedes-Benz, Audi, Volkswagen, Porsche, Volvo, Mini Cooper y Jaguar. Garantia del vendedor por 30 dias contra defectos de fabrica.
```

### seccion_compatibilidades

(vacia — no hay bloque parseado)

```
```

### seccion_faq

```json
[
  {
    "pregunta": "¿Es compatible con mi vehiculo?",
    "respuesta": "El listing menciona BMW 325i, 330i, 530i, X3, X5 y Z4. Como hay multiples generaciones de cada modelo con motores distintos, envianos tu numero de VIN y confirmamos la pieza exacta antes de procesar tu pedido."
  },
  {
    "pregunta": "¿Tiene garantia?",
    "respuesta": "Si, garantia del vendedor por 30 dias contra defectos de fabrica."
  },
  {
    "pregunta": "¿Que es un sensor MAP?",
    "respuesta": "El sensor MAP (Manifold Absolute Pressure) mide la presion del colector de admision y envia esta informacion a la ECU para ajustar la mezcla de combustible y el tiempo de encendido."
  }
]
```

### shopify_body_html

(omitir el bloque `<h2>Compatibilidades</h2>` porque `seccion_compatibilidades` esta vacia)

```html
<h2>Descripcion</h2>
<p>Sensor MAP (Manifold Absolute Pressure) para diversos modelos BMW...</p>
<p>Compatible con los modelos BMW 325i, 330i, 530i...</p>
<p>Numero de parte interno: SEN-MAP-01...</p>
<p>Producto vendido como pieza individual.</p>
<p>Marca Embler... Garantia del vendedor por 30 dias contra defectos de fabrica.</p>

<h2>Antes de Comprar</h2>
<p>Para garantizar que recibas la pieza correcta...</p>

<h2>Envio</h2>
<p>Tenemos stock disponible para entrega inmediata...</p>

<h2>Politica de Devolucion</h2>
<p>...</p>

<h2>Preguntas Frecuentes</h2>
<h3>...</h3>
```

### shopify_tags

(no hay `marcas_vehiculo` parseadas — fallback al titulo)

```
BMW
```

### revision_humana

```
[BUSCAR] Compatibilidad vehicular: no se pudo extraer de la descripción y el titulo solo menciona modelos sin anos ni motorizaciones.
[BUSCAR] Codigo OEM faltante — buscar en catalogo del proveedor.
[BUSCAR] Origen del producto no especificado.
[VERIFICAR] Compatibilidad inferida del titulo — confirmar que los modelos BMW 325i, 330i, 530i, X3, X5, Z4 son correctos.
[REVISAR] Descripcion generada sin datos fuente — verificar precision.
[INCLUIR] Peso y dimensiones para calculo de envio.
[INCLUIR] Fotografias del producto.
```

Las acciones especificas van primero, las universales (peso/fotos) al final.
