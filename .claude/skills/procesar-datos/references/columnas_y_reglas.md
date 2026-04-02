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
