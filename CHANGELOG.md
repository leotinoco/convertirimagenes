# Changelog

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
