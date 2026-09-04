# Changelog

## [1.5.0] - 2026-09-04

### Añadido
- ✨ **Motor de codificación seleccionable (solo AVIF)**: Nueva tarjeta que permite elegir entre tres codificadores, con el motor estándar siempre como predeterminado.
  - **Estándar (CPU)** — motor integrado (libaom). El más rápido (~55 ms/img con «Ultra Rápido», ~18 img/s) y el único que conserva EXIF/IPTC y transparencia.
  - **Máxima compresión (SVT-AV1)** — archivos **~20% más livianos a igual calidad visual** (36.9 KB vs 45.9 KB medidos a igual SSIM), a cambio de ser ~8x más lento por imagen.
  - **GPU NVIDIA (experimental)** — codificador AV1 por hardware. Medido **más lento** que la CPU (~4 img/s vs ~18 img/s) porque inicializar la sesión CUDA/NVENC cuesta más que comprimir una imagen pequeña, y sin ventaja de peso. Se incluye para comparar.
- ✨ **Descripciones comparativas en la interfaz**: Cada motor muestra qué hace, qué resultado da (velocidad y peso con cifras reales) y cuándo conviene frente a los otros. Se avisa si falta ffmpeg o si el formato elegido no es AVIF.

### Mejorado
- ⚡ **Detección automática de ffmpeg**: Los motores externos se habilitan solos si ffmpeg está en el PATH; si no, aparecen marcados como no disponibles.
- 🛡️ **Retroceso seguro**: Si un motor externo falla, la imagen tiene transparencia o el formato no es AVIF, la conversión usa el motor estándar sin interrumpir el lote. `ConversionResult.engine` registra cuál se usó realmente.
- 🐛 **Sin ventanas emergentes**: Las llamadas a ffmpeg se lanzan con `CREATE_NO_WINDOW` en Windows para que no parpadee una consola por cada imagen.

## [1.4.0] - 2026-08-05

### Añadido
- ✨ **Ancho fijo con alto automático**: Nuevo modo de redimensionado "Ancho fijo" que ajusta el alto proporcionalmente **por cada imagen**, sin distorsión (ideal para estandarizar lotes a 1200px de ancho).
- ✨ **Doble conversión (escritorio + móvil)**: Opción de generar dos versiones por imagen en un solo lote (ej. 1200px para PC y 800px para móvil), aplicada de forma masiva a todos los archivos. El campo de ancho móvil siempre está editable y escribir un valor activa la segunda versión automáticamente (borrarlo la desactiva).
- ✨ **Sufijo automático de píxeles**: Los archivos de salida reciben `_1200px` / `_800px` según el ancho (ej. `fotografia40.jpg` → `fotografia40_1200px.avif`), combinable con el sufijo personalizado. En doble conversión se aplica siempre para evitar colisiones de nombres.
- ✨ **Vista previa del nombre de salida**: Ejemplo en vivo del nombre resultante según el archivo cargado, formato, sufijos y anchos elegidos.

### Mejorado
- ⚡ **Progreso por salida**: La barra de progreso y el resumen cuentan cada archivo generado (archivos × versiones).
- 🛡️ **Eliminar originales con variantes**: El botón de eliminar originales solo se habilita cuando **todas** las versiones de cada imagen se convirtieron con éxito.

## [1.3.0] - 2026-07-17

### Añadido
- ✨ **Formato WebP**: Nueva opción de salida WebP con compresión máxima (method 6) y soporte de transparencia.
- ✨ **Carpeta de destino**: Selector de carpeta de salida con opción de restablecer a "junto al original".
- ✨ **Sufijo de archivo**: Sufijo opcional para los archivos convertidos (ej. `foto-opt.avif`), sanitizado contra caracteres inseguros.
- ✨ **Barra de progreso y cancelación**: Progreso en tiempo real (n/total) y botón para cancelar la conversión en curso.
- ✨ **Resumen de lote**: Al finalizar se muestra el total convertido y el ahorro acumulado en disco.
- 🎨 **Rediseño visual**: Tema centralizado (`utils/theme.py`) con paleta moderna, tarjetas con bordes, radios consistentes y tipografía multiplataforma (Segoe UI / Helvetica Neue / DejaVu Sans).

### Mejorado
- ⚡ **Auto-orientación EXIF**: Los píxeles se rotan según el tag Orientation y el tag se restablece a 1, evitando fotos giradas o doblemente rotadas.
- ⚡ **JPEG optimizado**: Salida progresiva con `optimize=True` (mejor carga percibida en web y menor tamaño).
- ⚡ **AVIF nativo**: Si `pillow-avif-plugin` no está disponible, se usa el soporte AVIF nativo de Pillow ≥ 11.3.
- 🐛 **Núcleos de CPU**: El slider de núcleos ahora sí se aplica a la conversión (antes se ignoraba).
- 🛡️ **Validación de disco**: La verificación de espacio libre se ejecuta antes de cada lote (antes existía pero no se usaba).

### Seguridad
- 🛡️ **Anti decompression-bomb**: Las imágenes maliciosamente grandes fallan con un error controlado en lugar de agotar la RAM.
- 🛡️ **Explorador de archivos**: `explorer /select` ahora usa lista de argumentos (sin interpolación de strings), eliminando inyección de argumentos con nombres de archivo especiales.
- 🛡️ **.gitignore**: Cobertura ampliada a `.env.*` (manteniendo `.env.example`).

### Corregido
- 🐛 Test de ahorro frágil: la imagen sintética de prueba ahora incluye ruido fotográfico determinista.
- 🐛 Cambio de idioma ya no restablece las selecciones de velocidad y submuestreo.
- 🐛 Advertencia de escape inválido (`\P`) en `dnd_utils.py`.

## [1.2.1] - 2026-06-21

### Corregido
- actualiza extensiones válidas de arrastre y agrega pruebas unitarias

## [1.2.0] - 2026-06-21

### Añadido
- agrega soporte para formato PNG y ajusta la UI
- agrega opcion de conversion a JPG

### Documentación
- actualiza documentacion y excluye .agents

Todas las novedades relevantes de este proyecto serán documentadas en este archivo.

## [1.2.0] - 2026-06-06

### Añadido
- ✨ **Conversión a JPG**: Agregada la opción de convertir archivos `.avif` y `.webp` a formato `.jpg`.
- ✨ **Selector de formato**: Integrado un control segmentado en la interfaz para alternar dinámicamente entre formatos de salida (`AVIF` y `JPG`).
- ⚙️ **Aplanado de transparencia**: Fusión automática del canal alfa sobre un fondo blanco sólido al guardar en JPEG para evitar errores de codificación.
- 🛡️ **Prevención de colisiones**: Generación de nombres de archivo no destructivos (ej. `nombre_converted.jpg`) cuando se intenta convertir al mismo formato.


## [1.1.0] - 2026-04-13

### Añadido
- ✨ **Botón de eliminación**: Agregado botón para eliminar archivos originales (.png, .jpg, .jpeg) después de la conversión exitosa.
- 📦 **Compilación**: Sincronización del archivo `.spec` de PyInstaller para asegurar compilaciones consistentes.
- ✨ **Historial mejorado**: Rediseño del panel de historial con tablas estructuradas y mejores métricas de ahorro.
- ✨ **Previsualización**: Implementación de vista previa "Antes/Después" comparativa.
- ✨ **Drag & Drop**: Soporte nativo para arrastrar y soltar archivos en la interfaz.
- ✨ **Procesamiento paralelo**: Uso de hilos para conversión ultra-rápida aprovechando todos los núcleos del CPU.

### Corregido
- 🐛 **Transparencia**: Corrección en el manejo de canales alfa (transparencia) para archivos AVIF generados desde PNG.

### Tareas
- 🔧 Configuración inicial del repositorio y entorno de desarrollo.
- 📚 Actualización de README con previsualizaciones y documentación técnica.
