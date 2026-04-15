# Referencia Tecnica: Columnas y Reglas

## Tabla de columnas CSV

Los CSVs en `output/` tienen 39 columnas. Estas son las relevantes para generar contenido:

| Indice | Nombre CSV | Clave corta | Descripcion |
|--------|-----------|-------------|-------------|
| 3 | NOMBRE_ARTICULO_MC | nombre_tecnico | Nombre tecnico del ERP (ej: "JUEGO DE JUNTAS DE MOTOR COMPLETO BMW MOTOR N63 BMTSR") |
| 7 | UNIDAD_VENTA_MC | unidad_venta | Pieza, Juego, Kit, Par |
| 11 | Id_ML | id_ml | ID unico de MercadoLibre |
| 13 | Categoría_ML | categoria | Path jerarquico (ej: "Accesorios para Vehiculos > Refacciones Autos...") |
| 14 | Título_ML | titulo | Titulo comercial (ej: "Juego De Juntas De Motor Completo Bmw 750i 550i X5 X6 &") |
| 15 | Descripción_ML | descripcion | Descripcion larga existente. Tiene formato de marketplace con mayusculas y advertencias. |
| 17 | SKU_ML | sku | SKU del producto |
| 21 | Garantia_ML | garantia | Ej: "Garantía del vendedor: 30 días" |
| 24 | Compatibilidades_ML | compatibilidades | Texto multilínea con vehiculos. Solo 51% de productos lo tiene. |
| 25 | Compatibilidades Restricciones_ML | compat_restricciones | Restricciones. Solo 6.9% lo tiene. |
| 26 | Atributo_x000D_ Marca_ML | marca | Marca del producto (la refaccion, NO el vehiculo) |
| 27 | Atributo Número de parte_ML | numero_parte | Part number |
| 29 | Atributo_x000D_ Tipo de vehículo_ML | tipo_vehiculo | Carro/Camioneta, Moto, Linea Pesada |
| 30 | Atributo_x000D_ Origen_ML | origen | Origen del producto. Solo 51.5% lo tiene. |
| 31 | Atributo_x000D_ Código OEM_ML | codigo_oem | Codigo original del fabricante. Solo 64.6% lo tiene. |
| 16 | Precio_ML | precio | Precio de venta en MXN |
| 36 | marca_normalizada | marca_norm | Ya normalizada por el script de extraccion |
| 37 | subcategoria_limpia | subcategoria | Extraida del path de categoria |

## Formato de Compatibilidades_ML

Cuando existe, tiene este formato (cada linea es un vehiculo compatible):

```
MLM19657400 | BMW 550i 2013 Base México Asistida Cremallera RWD Sedan 4.4L V8 Gasolina Automática Transmisión 8 4 ABS 4 ruedas Asistido Disco Disco F10 N63B44A 32 Turbocargado Sin distribuidor Helicoidal Helicoidal
MLM15851558 | BMW 550i 2013 M Sport México Asistida RWD Sedan 4.4L V8 Gasolina Automática 8 4 Asistido Disco Disco 32 Turbocargado Helicoidal Helicoidal Inyección DOHC
```

Patron: `ID_ML | Marca Modelo Año Version Pais ...detalles_tecnicos...`

Los campos utiles son los primeros: Marca, Modelo, Año, Version, Motor (buscar patron como "4.4L V8" o "3.0L L6").

## Reglas de empaque estimado

Basadas en la categoria y tipo de producto:

| Tipo de producto | Empaque estimado | Notas de manejo |
|-----------------|------------------|-----------------|
| Juntas de motor completas, culatas, turbos | Caja reforzada | Fragil, evitar golpes |
| Amortiguadores, brazos de suspension, barras | Caja reforzada | Pieza pesada |
| Discos de freno, calipers, rotores | Caja reforzada | Pieza pesada |
| Bombas (agua, aceite, gasolina), alternadores | Caja | null |
| Sensores, bobinas, modulos electronicos | Caja | Componente electronico |
| Filtros (aceite, aire, gasolina) | Caja | null |
| Sellos, retenes, juntas individuales, o-rings | Bolsa | null |
| Tornilleria, clips, grapas | Bolsa | null |
| Espejos, faros, calaveras | Caja reforzada | Fragil |
| Mangueras, bandas | Bolsa o Caja | null |

## Normalizacion de marcas

Las marcas mas comunes y sus normalizaciones (ya aplicadas en col 36):

```
"ORIGINAL FREY GERMAN TECHNOLOGY QUALITY"     -> "Original Frey"
"ORIGINAL FREY GERMAN TECHNOLOGY GERMAN Q"    -> "Original Frey"
"ORIGINAL FREY GERMAN TECNHLOGY QUALITY"      -> "Original Frey"
"EMBLER AUTOPARTES EUROPEAS"                  -> "Embler"
```

Marcas menores se dejan en Title Case.

## Mapeo a columnas Shopify

Esta tabla muestra como cada columna Shopify se genera o mapea desde los datos existentes:

| Columna Shopify | Fuente | Generacion |
|----------------|--------|------------|
| Handle | Titulo_ML | Slugificar: minusculas, sin acentos, guiones |
| Title | Titulo_ML | Limpiar: quitar "&" final, Title Case, respetar siglas |
| Body (HTML) | seccion_descripcion + antes_de_comprar + envio + devoluciones + faq | Combinar en HTML con h2/p/h3 |
| Vendor | caract_marca (col 36 normalizada) | Directo |
| Product Category | Fijo | `Vehicles & Parts > Vehicle Parts & Accessories` |
| Type | subcategoria_limpia (col 37) | Mapear a: Motor, Frenos, Suspensión, Sistema Eléctrico, Carrocería, Filtros, Transmisión, Dirección, Accesorios, Tuning |
| Tags | Compatibilidades_ML + Titulo_ML | Extraer marcas de VEHICULO: BMW, Mercedes-Benz, Audi, Volkswagen, Porsche, Volvo, Mini, etc. |
| Published | Fijo | `TRUE` |
| Option1 Name | Fijo (mayoria) | `Title` (sin variantes reales) |
| Option1 Value | Fijo (mayoria) | `Default Title` |
| Variant SKU | SKU_ML (col 17) | Directo |
| Variant Price | Precio_ML (col 16) | Directo, sin simbolo moneda |
| Variant Compare At Price | — | Vacio (sin dato fuente) |
| Variant Inventory Qty | — | Vacio (sin dato fuente) |
| Variant Weight | — | Vacio (sin dato fuente) |
| Variant Weight Unit | Fijo | `kg` |
| Image Src | — | Vacio (sin URLs de imagenes) |
| Image Alt Text | Titulo + Marca producto + Marca vehiculo | Generar texto descriptivo, max 125 chars |
| SEO Title | Titulo + Marca vehiculo + "Embler" | Max 60 chars, formato: `{Producto} {Vehiculo} | Embler` |
| SEO Description | Descripcion resumida | Max 155 chars, incluir producto + vehiculo + call-to-action |
| Status | Fijo | `draft` (el humano activa despues de revisar) |

## Mapeo de subcategoria a shopify_type

| Palabras clave en subcategoria | shopify_type |
|-------------------------------|--------------|
| motor, juntas, culata, turbo, valvulas, admision, escape, enfriamiento, distribucion, carter, biela, ciguenal, arbol de levas | Motor |
| frenos, discos, pastillas, calipers, balatas, tambores | Frenos |
| suspension, amortiguadores, amortiguador, brazos, rotulas, bujes, barras, resortes, soportes | Suspensión |
| electrico, sensores, sensor, bobinas, alternador, modulos, computadora, relay, fusible, motor de arranque | Sistema Eléctrico |
| carroceria, faros, faro, espejos, espejo, defensas, cofre, salpicaderas, parrilla, calavera, moldura | Carrocería |
| filtros, filtro | Filtros |
| transmision, embrague, clutch, convertidor, volante motor | Transmisión |
| direccion, cremallera, bomba direccion, terminales | Dirección |
| accesorios | Accesorios |
| tuning | Tuning |

## Collections automaticas de Shopify

Las collections se generan automaticamente con la combinacion de Tag (marca vehiculo) + Product Type (categoria). Ejemplo:

| Collection | Regla Tag | Regla Type | Condicion |
|-----------|-----------|------------|-----------|
| BMW - Motor | Tag = BMW | Type = Motor | ALL conditions |
| BMW - Frenos | Tag = BMW | Type = Frenos | ALL conditions |
| Audi - Suspensión | Tag = Audi | Type = Suspensión | ALL conditions |
| Mercedes-Benz - Filtros | Tag = Mercedes-Benz | Type = Filtros | ALL conditions |

Marcas configuradas: BMW, Audi, Volvo, Mercedes-Benz, Porsche, Volkswagen.
Categorias configuradas: Motor, Frenos, Suspensión, Sistema Eléctrico, Carrocería, Filtros.

Es CRITICO que los valores de `shopify_type` y `shopify_tags` sean exactamente los de estas tablas para que las collections funcionen.
