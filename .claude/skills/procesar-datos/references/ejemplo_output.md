# Ejemplo Completo de Output

## Producto de entrada (datos completos)

```json
{
  "nombre_tecnico": "JUEGO DE JUNTAS DE MOTOR COMPLETO BMW MOTOR N63 BMTSR",
  "unidad_venta": "Pieza",
  "id_ml": "MLM1234567",
  "categoria": "Accesorios para Vehículos > Refacciones Autos y Camionetas > Motor > Juntas",
  "titulo": "Juego De Juntas De Motor Completo Bmw 750i 550i X5 X6 &",
  "descripcion": "JUEGO DE JUNTAS DE MOTOR COMPLETO PARA BMW\n\nINCLUYE:\nJUNTA DE CABEZA\nSELLOS DE VALVULA\nJUNTAS DE ADMISION Y DE ESCAPE\nJUNTA DE TAPA DE PUNTERIAS\n\nMUY IMPORTANTE:\n\nPARA EVITARTE MOLESTIAS, PÉRDIDA DE TIEMPO Y DEVOLUCIONES INNECESARIAS; ANTES DE COMPRAR ES NECESARIO...",
  "sku": "XB-N63B44-03",
  "garantia": "Garantía del vendedor: 30 días",
  "compatibilidades": "MLM19657400 | BMW 550i 2013 Base México Asistida Cremallera RWD Sedan 4.4L V8 Gasolina...\nMLM15851558 | BMW 750i 2012 Base México...\nMLM15872008 | BMW X5 2014 xDrive50i México...",
  "marca": "ORIGINAL FREY GERMAN TECHNOLOGY QUALITY",
  "numero_parte": "XB-N63B44-03",
  "tipo_vehiculo": "Carro/Camioneta",
  "origen": "Importado",
  "codigo_oem": "11127571692",
  "marca_normalizada": "Original Frey",
  "subcategoria": "motor"
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

```
Aplica para los siguientes modelos BMW con motor N63 4.4L V8 turbo: Serie 5 (550i 2013), Serie 7 (750i 2012) y X5 (xDrive50i 2014). Verifica compatibilidad exacta con el VIN de tu vehiculo.
```

### seccion_descripcion

```
Juego de juntas de motor completo para vehiculos BMW equipados con motor N63, compatible con modelos como 550i, 750i, X5 y X6.

Este kit incluye junta de cabeza, sellos de valvula, juntas de admision y escape, y junta de tapa de punterias. Es una solucion completa para la reparacion o mantenimiento mayor del motor, evitando la necesidad de comprar cada junta por separado.

Fabricado por Original Frey, marca especializada en refacciones de calidad para vehiculos europeos. Producto importado con numero de parte XB-N63B44-03 y codigo OEM 11127571692, lo que facilita la verificacion de compatibilidad con tu vehiculo.
```

### seccion_antes_de_comprar

```
Para garantizar que recibas la pieza correcta para tu vehiculo, necesitamos el numero de serie (VIN) de tu auto antes de procesar el pedido. Esto evita errores, tiempos perdidos y devoluciones innecesarias. Escribenos y con gusto confirmamos compatibilidad. Tambien puedes verificar con el numero de parte XB-N63B44-03 o codigo OEM 11127571692.
```

### seccion_envio

```
Tenemos stock disponible para entrega inmediata. Enviamos el mismo dia de tu pago a Ciudad de Mexico y a todo el pais via DHL o FedEx.
```

### seccion_faq

```json
[
  {
    "pregunta": "¿Es compatible con mi vehiculo?",
    "respuesta": "Este juego de juntas es compatible con vehiculos BMW con motor N63 4.4L V8, incluyendo modelos como 550i (2013), 750i (2012) y X5 xDrive50i (2014). Verifica que tu vehiculo tenga el motor N63 antes de comprar."
  },
  {
    "pregunta": "¿Que incluye el juego de juntas?",
    "respuesta": "Incluye junta de cabeza, sellos de valvula, juntas de admision y escape, y junta de tapa de punterias."
  },
  {
    "pregunta": "¿Tiene garantia?",
    "respuesta": "Si, cuenta con garantia del vendedor por 30 dias."
  },
  {
    "pregunta": "¿Es una pieza original o generica?",
    "respuesta": "Es una refaccion de la marca Original Frey, especializada en autopartes para vehiculos europeos. Producto importado. Codigo OEM de referencia: 11127571692."
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

### revision_humana

```
[INCLUIR] Peso y dimensiones para calculo de envio.
[INCLUIR] Fotografias del producto.
```

Este producto tiene todos los datos criticos (compatibilidades, OEM, marca, numero de parte). Solo necesita los datos universales que faltan en todo el catalogo.

---

## Ejemplo SIN compatibilidades (producto con datos limitados)

### Entrada

```json
{
  "titulo": "Sensor Map Bmw 325i 330i 530i X3 X5 Z4 &",
  "descripcion": "",
  "compatibilidades": "",
  "codigo_oem": "",
  "numero_parte": "SEN-MAP-01",
  "origen": "",
  "marca_normalizada": "Embler",
  "tipo_vehiculo": "Carro/Camioneta",
  "unidad_venta": "Pieza",
  "garantia": "Garantia del vendedor: 30 dias"
}
```

### caract_marca
```
Embler
```

### caract_origen
```
```
(vacio — no hay dato)

### caract_tipo_vehiculo
```
Carro/Camioneta
```

### caract_compatibilidad
```
Compatible con modelos BMW 325i, 330i, 530i, X3, X5 y Z4. Confirma compatibilidad exacta con tu numero de VIN antes de comprar.
```

### seccion_antes_de_comprar
```
Para garantizar que recibas la pieza correcta para tu vehiculo, necesitamos el numero de serie (VIN) de tu auto antes de procesar el pedido. Esto evita errores, tiempos perdidos y devoluciones innecesarias. Escribenos y con gusto confirmamos compatibilidad. Tambien puedes verificar con el numero de parte SEN-MAP-01.
```

### seccion_envio
```
Tenemos stock disponible para entrega inmediata. Enviamos el mismo dia de tu pago a Ciudad de Mexico y a todo el pais via DHL o FedEx.
```

### seccion_faq

```json
[
  {
    "pregunta": "¿Es compatible con mi vehiculo?",
    "respuesta": "Este sensor MAP es compatible con diversos modelos BMW incluyendo 325i, 330i, 530i, X3, X5 y Z4. Para confirmar compatibilidad exacta, envianos tu numero de VIN."
  },
  {
    "pregunta": "¿Tiene garantia?",
    "respuesta": "Si, cuenta con garantia del vendedor por 30 dias."
  },
  {
    "pregunta": "¿Que es un sensor MAP?",
    "respuesta": "El sensor MAP (Manifold Absolute Pressure) mide la presion del colector de admision y envia esta informacion a la computadora del vehiculo para ajustar la mezcla de combustible y el tiempo de encendido."
  }
]
```

### revision_humana

```
[BUSCAR] Compatibilidad vehicular: solo se tienen modelos del titulo, sin anos ni motorizaciones. Consultar ficha tecnica del proveedor.
[BUSCAR] Codigo OEM faltante — buscar en catalogo del proveedor.
[BUSCAR] Origen del producto no especificado.
[VERIFICAR] Compatibilidad inferida del titulo — confirmar que los modelos 325i, 330i, 530i, X3, X5, Z4 son correctos.
[REVISAR] Descripcion generada sin datos fuente — verificar precision.
[INCLUIR] Peso y dimensiones para calculo de envio.
[INCLUIR] Fotografias del producto.
```

Este producto tiene varias carencias: sin compatibilidades detalladas, sin codigo OEM, sin origen, sin descripcion fuente. Las acciones especificas van primero, las universales al final.
