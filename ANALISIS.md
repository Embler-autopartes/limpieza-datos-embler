# Analisis de Datos - Embler Autopartes

## Resumen del Proyecto

Limpieza y enriquecimiento de datos de un catalogo de autopartes europeas (BMW, Mercedes-Benz, etc.) para uso en ecommerce. Los datos provienen de dos sistemas: **Microsip** (ERP/inventario) y **MercadoLibre** (marketplace).

## Archivos Disponibles

| Archivo | Filas | Columnas | Descripcion |
|---------|-------|----------|-------------|
| `CRUCE_MICROSIP_MERCADOLIBRE (2).xlsx` | 13,363 | 36 | **SELECCIONADO** - Cruce completo de ambas fuentes |
| `temp_MERCADOLIBRE.xlsx` | 13,961 | 24 | Solo datos de MercadoLibre |
| `temp_MICROSIP_LIMPIO.xlsx` | 10,818 | 11 | Solo datos de Microsip (inventario) |

### Por que se eligio el archivo CRUCE

- Combina datos de inventario (Microsip: SKU, claves, estatus) con datos comerciales (ML: titulo, descripcion, precio, compatibilidades)
- Tiene la mayor riqueza de datos por fila (36 columnas)
- Ya tiene el matching hecho entre ambos sistemas via `CLAVE_MATCH`

## Estructura de Columnas del Input

### Columnas Microsip (sufijo _MC) - Datos de inventario
| Columna | Completitud | Descripcion |
|---------|-------------|-------------|
| ARTICULO_ID_MC | 100% | ID interno del articulo |
| SKU_MC | 99.9% | Codigo SKU del producto |
| CLAVE_PRINCIPAL_MC | 99.9% | Clave primaria del articulo |
| NOMBRE_ARTICULO_MC | 100% | Nombre tecnico del producto |
| ESTATUS_MC | 100% | Estado del articulo (A=Activo) |
| NUM_CLAVES_ALTERNAS_MC | 100% | Cantidad de claves alternas |
| CLAVES_ALTERNAS_TODAS_MC | 92.9% | Listado de claves alternas |
| UNIDAD_VENTA_MC | 99.9% | Unidad de venta (Pieza, Juego, etc.) |
| ES_ALMACENABLE_MC | 100% | Si se almacena fisicamente |
| LINEA_ARTICULO_ID_MC | 100% | ID de linea de articulo |
| TODAS_LAS_CLAVES_MC | 100% | Todas las claves combinadas |

### Columnas MercadoLibre (sufijo _ML) - Datos comerciales
| Columna | Completitud | Descripcion |
|---------|-------------|-------------|
| Id_ML | 100% | ID de publicacion en ML |
| Situacion Catalogo_ML | 100% | Estado en el catalogo de ML |
| Categoria_ML | 100% | Categoria en ML (42 unicas) |
| Titulo_ML | 100% | Titulo de la publicacion |
| Descripcion_ML | 99.5% | Descripcion larga del producto |
| Precio_ML | 100% | Precio de venta |
| SKU_ML | 97.2% | SKU asignado en ML |
| Estado_ML | 100% | Estado de la publicacion |
| Stock_ML | 100% | Cantidad en stock |
| Disponibilidad de stock_ML | 100% | Disponibilidad |
| Garantia_ML | 100% | Informacion de garantia |
| Tags_ML | 100% | Etiquetas de ML |
| URL Publicacion_ML | 100% | Link a la publicacion |
| Compatibilidades_ML | 51.1% | Vehiculos compatibles (texto largo) |
| Compatibilidades Restricciones_ML | 6.9% | Restricciones de compatibilidad |
| Marca_ML | 99.1% | Marca del producto |
| Numero de parte_ML | 99.0% | Numero de parte |
| Tipo de vehiculo_ML | 95.6% | Tipo (Carro, Moto, Linea Pesada) |
| Origen_ML | 51.5% | Origen del producto |
| Codigo OEM_ML | 64.6% | Codigo OEM |
| Modelo_ML | 17.0% | Modelo del vehiculo |
| Lado_ML | 4.2% | Lado de instalacion |

### Columnas de Matching
| Columna | Completitud | Descripcion |
|---------|-------------|-------------|
| CLAVES_COMBINADAS_ML | 100% | Claves combinadas de ML |
| CLAVE_MATCH | 100% | Clave usada para el cruce |

## Perfil de Datos

### Distribucion por Categoria
- **96.6%** son Refacciones para Autos y Camionetas
- 42 categorias unicas en total
- Categorias menores: accesorios, tuning, motos, linea pesada, herramientas

### Marcas Principales (262 unicas)
- ORIGINAL FREY GERMAN TECHNOLOGY QUALITY: 5,464 (40.9%)
- EMBLER AUTOPARTES EUROPEAS: 2,788 (20.9%)
- ORIGINAL FREY GERMAN TECHNOLOGY GERMAN Q: 2,727 (20.4%)
- Otras: Mahle, Febi, Ossca, SENP, etc.

### Tipo de Vehiculo
- Carro/Camioneta: 12,631 (95%)
- Linea Pesada: 79
- Moto/Cuatriciclo: 54

### Calidad de Datos - Problemas Detectados
1. **Descripciones repetitivas**: Muchas descripciones siguen un template generico de ML
2. **Compatibilidades incompletas**: Solo 51% tiene datos de compatibilidad
3. **Columnas casi vacias**: Color manguera intercooler (0.04%), Lado (4.2%), Modelo (17%)
4. **Marcas inconsistentes**: Variaciones de "ORIGINAL FREY" con diferentes sufijos
5. **Nombres tecnicos**: Los nombres de Microsip son codigos tecnicos, no nombres comerciales

## Estrategia de Procesamiento

### Procesamiento por Categorias (chunks)

Dado el volumen (13,363 filas), se procesan en chunks por **categoria principal**:

1. **Chunk 1 - Refacciones Autos** (~12,914 filas) - Se subdivide por subcategoria
2. **Chunk 2 - Accesorios** (~80 filas)
3. **Chunk 3 - Tuning** (~83 filas)
4. **Chunk 4 - Motos** (~58 filas)
5. **Chunk 5 - Linea Pesada** (~56 filas)
6. **Chunk 6 - Otros** (~172 filas)

Para el Chunk 1 (muy grande), se subdivide por **subcategoria de refaccion**:
- Motor, Suspension, Frenos, Transmision, Sistema Electrico, etc.

### Columnas de Output (nuevas, generadas con IA)

| Columna Output | Fuente | Inferible? |
|----------------|--------|------------|
| `descripcion_ecommerce` | Titulo_ML + Descripcion_ML + Nombre_MC | SI - reescribir para ecommerce |
| `info_envio` | Unidad_venta + Peso (NO disponible) | PARCIAL - solo unidad, peso no disponible |
| `faq_producto` | Descripcion_ML + Compatibilidades + Garantia | SI - generar FAQs contextuales |
| `productos_relacionados` | Categoria + Marca + Tipo vehiculo | SI - por similitud de categoria/marca |
| `compatibilidad_estructurada` | Compatibilidades_ML | PARCIAL - solo 51% tiene datos |
| `nombre_comercial` | Titulo_ML + Nombre_MC | SI - limpiar y humanizar |
| `marca_normalizada` | Marca_ML | SI - normalizar variaciones |
| `subcategoria` | Categoria_ML | SI - extraer subcategoria limpia |
| `palabras_clave_seo` | Titulo + Descripcion + Compatibilidad | SI - extraer keywords |

### Reglas de Inferencia

#### Se PUEDE inferir:
- **Descripcion general**: Del titulo + descripcion existente + nombre tecnico. Se puede reescribir en tono comercial.
- **FAQs**: De la descripcion (instrucciones de compra), garantia, tipo de producto y compatibilidad.
- **Productos relacionados**: Por categoria + marca + tipo de vehiculo. Productos en la misma subcategoria para el mismo tipo de vehiculo.
- **Compatibilidad**: Si existe el campo Compatibilidades_ML, se puede estructurar. Si no, se puede inferir parcialmente del titulo (modelos mencionados).
- **Marca normalizada**: Unificar variaciones de ORIGINAL FREY, etc.
- **Subcategoria limpia**: Extraer del path de categoria de ML.
- **Keywords SEO**: Del titulo, nombre tecnico y compatibilidades.

#### NO se puede inferir (datos faltantes):
- **Peso y dimensiones**: No estan en ninguna fuente. Necesario para info de envio completa.
- **Imagenes**: No hay URLs de imagenes en los datos.
- **Tiempo de entrega**: Depende de logistica, no esta en datos.
- **Especificaciones tecnicas detalladas**: Material, tolerancias, etc. no disponibles.
- **Precio de envio**: Depende de ubicacion y peso.
- **Lado de instalacion**: Solo 4.2% tiene este dato, no se puede inventar.
- **Codigo OEM completo**: 64.6% lo tiene, no se puede generar para el resto.
