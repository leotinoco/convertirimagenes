# Changelog

Todas las novedades relevantes de este proyecto serán documentadas en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el versionado sigue [Versionado Semántico](https://semver.org/lang/es/).

## [1.7.1] - 2026-10-16

### Corregido
- 🐛 **Arranque con varias versiones de Python instaladas**: Las dependencias se instalan por intérprete, así que instalar un Python nuevo puede tomar el control del `PATH` y dejar la aplicación apuntando a uno sin paquetes, fallando con `ModuleNotFoundError: No module named 'customtkinter'`. `ConvertirImagenes.bat` ahora comprueba las dependencias antes de arrancar y, si faltan, muestra **qué intérprete está usando**, su versión y el comando exacto para instalarlas, en lugar de un traceback.

### Documentación
- 📚 Añadida al README la guía para diagnosticar y resolver ese caso.

## [1.7.0] - 2026-10-10

### Añadido
- ⚡ **Decodificación JPEG a escala reducida (`draft`)**: Cuando la salida es mucho más pequeña que el origen, se pide a libjpeg que decodifique directamente a 1/2, 1/4 u 1/8 en lugar de leer la imagen completa y reducirla después. Medido sobre 12 fotos de 4000×3000 a 1200px con 16 hilos:
  - **2.07x más rápido** generando una versión (51.4 → 24.8 ms por salida).
  - **2.73x más rápido** en doble conversión escritorio + móvil (45.1 → 16.5 ms por salida), porque la versión de 800px decodifica a 1/4 de escala.
  - **Peso idéntico** (−0.4%) y sin pérdida visual: el reescalado LANCZOS sigue partiendo de una resolución superior a la de destino. Comprobado además que pedir más holgura de decodificación no cambia el resultado, así que la escala elegida no sacrifica calidad.
  - Respeta la orientación EXIF: en fotos giradas un cuarto de vuelta los ejes se intercambian antes de calcular la escala, de modo que nunca se decodifica por debajo del objetivo.
- 🛡️ **Retiro automático de motores averiados**: Si un motor externo falla 3 veces seguidas (ffmpeg retirado del PATH, codificador ausente del build), se desactiva para el resto de la sesión y el lote continúa con el motor integrado. Antes, un lote de 500 imágenes con el motor roto lanzaba 500 procesos condenados y esperaba por cada uno antes de retroceder.

### Cambiado
- 🎚️ **Calidad predeterminada 65 → 50**: ajustada a la escala recalibrada que llegó con Pillow 12.3 (ver más abajo). Da el mismo resultado visual que el 65 anterior con archivos bastante más livianos, que es lo que busca una herramienta de optimización web. Si preferías el comportamiento anterior, sube el deslizador a ~60.

### Mejorado
- ⚡ **Reescalado innecesario evitado**: Si la imagen ya tiene el tamaño pedido, se omite la llamada a `resize`.

### Verificado
- ✅ **Python 3.15** (publicado el 9-10-2026): 61/61 pruebas e interfaz real en un entorno limpio instalado desde `requirements.txt`. Todas las dependencias tienen wheel para 3.15 (Pillow `cp315`), el AVIF nativo funciona y el Drag & Drop opera con el **Tcl/Tk 9.0** que trae esa versión. También verificado en **3.14** (Tk 8.6).
- ✅ **Mínimo mantenido en 3.10**: el código no usa sintaxis ni API posteriores (comprobado analizando todos los módulos contra la gramática de 3.10), así que subir el mínimo solo dejaría fuera usuarios sin aportar nada.

### Documentación
- 📚 Re-medida completa de la comparativa del README tras la optimización, con las dependencias exactas de `requirements.txt`.
- 📚 **Tabla de características al día**: el ahorro de SVT-AV1 se corrige a ~25% (venía de un cálculo con la base de peso anterior) y se indica la calidad predeterminada y el retiro automático de motores.
- 📚 **Documentado un cambio de comportamiento que llegó con la 1.6.0**: el salto a Pillow 12.3 trajo una libavif más reciente que **recalibró la escala de calidad AVIF**. El mismo valor produce archivos más pesados que en la 1.5.0 (q60: 46.3 → 66.2 KB). Medido a calidad visual igualada, ambas comprimen prácticamente igual, así que cambió el mapeo y no la eficiencia: **q50 hoy equivale al q60 de antes** (SSIM 0.9520 vs 0.9526). Quien venga de la 1.5.0 y usara 60 debería bajar el deslizador a ~50 para conservar el peso de siempre; el valor predeterminado ya se ajustó a 50 por este motivo.

## [1.6.0] - 2026-10-02

### Eliminado
- 🗑️ **Motor GPU NVIDIA (NVENC)**: las mediciones de la 1.5.0 lo dejaban sin caso de uso. Con 167 ms y 42.4 KB por imagen era ~3.5x más lento que el motor estándar en «Ultra Rápido» y más pesado que SVT-AV1 (36.8 KB), porque inicializar la sesión CUDA/NVENC cuesta más que comprimir una imagen pequeña. Además exigía una tarjeta NVIDIA: sin ella fallaba y la imagen salía con el motor estándar. Quedan dos motores que cubren lo necesario: **Estándar (CPU)**, el más rápido y sin programas externos, y **Máxima compresión (SVT-AV1)**, para el mínimo peso. Un ajuste antiguo con `nvenc` sigue convirtiendo, con el motor estándar.
- 🗑️ **Dependencia `pillow-avif-plugin`**: era un parche «hasta que Pillow tuviera soporte oficial», y Pillow lo trae desde la 11.3. Con Pillow 12.3 ambos usan la misma libavif 1.4.2 y generan archivos idénticos byte a byte. Solo se usa como respaldo si una instalación antigua de Pillow no tiene AVIF.

### Actualizado
- ⬆️ **Dependencias al día** (mínimos = versiones probadas): `customtkinter` 5.2.0 → **6.0.0**, `Pillow` 10.0.0 → **12.3.0**, `tkinterdnd2` 0.3.0 → **0.6.3**, `python-dotenv` 1.0.0 → **1.2.4**. `piexif` (1.1.3) y `darkdetect` (0.8.0) ya estaban en su última versión.
- ⬆️ **Drag & Drop en macOS con el paquete oficial**: `tkinterdnd2` 0.6.x incluye los binarios de Windows, Linux y macOS (Intel y Apple Silicon, también para Tcl 9), así que ya no hace falta el fork `tkinterdnd2-universal`.

### Corregido
- 🐛 **Pruebas que podían saltarse en silencio**: la suite comprobaba el soporte AVIF importando el plugin, así que sin él se saltaba casi todo el convertidor sin avisar. Ahora usa la misma detección que la app (AVIF nativo de Pillow o, en su defecto, el plugin).

### Verificado
- ✅ 49/49 pruebas en un entorno limpio instalado solo desde `requirements.txt` (Python 3.12, ffmpeg 6.1 con SVT-AV1).
- ✅ Interfaz real abierta con customtkinter 6.0.0: cambio de idioma, formato y motor, conversión con ambos motores (incluida una imagen con transparencia) y Drag & Drop cargado, sin errores ni advertencias.

## [1.5.0] - 2026-09-04

### Añadido
- ✨ **Motor de codificación seleccionable (solo AVIF)**: Nueva tarjeta que permite elegir entre tres codificadores, con el motor estándar siempre como predeterminado. Cifras medidas sobre fotos de 4000×3000 redimensionadas a 1200px, con 16 hilos:
  - **Estándar (CPU)** — motor integrado (libaom). El más rápido (48 ms/img, ~21 img/s con «Ultra Rápido») y el único que conserva EXIF/IPTC y transparencia.
  - **Máxima compresión (SVT-AV1)** — archivos **19% más livianos a igual calidad visual** (36.8 KB vs 45.6 KB a igual SSIM), a 198 ms/img (~5 img/s).
  - **GPU NVIDIA (experimental)** — codificador AV1 por hardware. 167 ms/img (~6 img/s) y 42.4 KB: supera al esfuerzo «Equilibrado», pero el motor estándar en «Ultra Rápido» sigue siendo ~3.5x más rápido, porque inicializar la sesión CUDA/NVENC cuesta más que comprimir una imagen pequeña.
- ✨ **Descripciones comparativas en la interfaz**: Cada motor muestra qué hace, qué resultado da (velocidad y peso con cifras reales) y cuándo conviene frente a los otros. Se avisa si falta ffmpeg o si el formato elegido no es AVIF.

### Mejorado
- ⚡ **Detección automática de ffmpeg**: Los motores externos se habilitan solos si ffmpeg está en el PATH; si no, aparecen marcados como no disponibles.
- 🛡️ **Retroceso seguro**: Si un motor externo falla, la imagen tiene transparencia o el formato no es AVIF, la conversión usa el motor estándar sin interrumpir el lote. `ConversionResult.engine` registra cuál se usó realmente.
- 🐛 **Sin ventanas emergentes**: Las llamadas a ffmpeg se lanzan con `CREATE_NO_WINDOW` en Windows para que no parpadee una consola por cada imagen.

### Documentación
- 📚 **Comparativa de métodos de conversión**: Nueva sección del README con mediciones reales (tiempo, peso, reducción y calidad SSIM) de cada formato de salida, nivel de calidad, esfuerzo de compresión y motor, con recomendaciones de cuándo usar cada uno.
- 📚 **CHANGELOG saneado**: Recuperada la nota introductoria que había quedado extraviada a mitad del archivo, añadida la referencia al formato *Keep a Changelog* / *Versionado Semántico*, y unificadas las dos secciones duplicadas que compartían el número `1.2.0`.
- 📚 **Pruebas**: Corregida la documentación de la suite, que se ejecuta con `unittest` (sin dependencias extra) y no requiere pytest.

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
- ✨ **Formato PNG**: Agregado soporte para salida PNG y ajustes de la interfaz para acomodarlo.
- ✨ **Conversión a JPG**: Agregada la opción de convertir archivos `.avif` y `.webp` a formato `.jpg`.
- ✨ **Selector de formato**: Integrado un control segmentado en la interfaz para alternar dinámicamente entre formatos de salida.
- ⚙️ **Aplanado de transparencia**: Fusión automática del canal alfa sobre un fondo blanco sólido al guardar en JPEG para evitar errores de codificación.
- 🛡️ **Prevención de colisiones**: Generación de nombres de archivo no destructivos (ej. `nombre_converted.jpg`) cuando se intenta convertir al mismo formato.

### Documentación
- 📚 Actualización de la documentación y exclusión de `.agents` del repositorio.

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
