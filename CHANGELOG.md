# Changelog

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
