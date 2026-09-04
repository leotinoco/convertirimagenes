# ⚡ ConvertirImagenes — Conversor Masivo de Imágenes para Web (AVIF · WebP · JPG · PNG)

![Vista Previa de la Aplicación](img/app-optimizar-imagenes-desarrollo-web.avif)

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![Version](https://img.shields.io/badge/version-1.5.0-orange)

Aplicación de escritorio profesional para la **conversión masiva de imágenes**, pensada como herramienta esencial del flujo de trabajo de desarrollo web: toma lotes grandes de imágenes (PNG, JPG, WebP, AVIF) y los convierte a formatos modernos y optimizados (**AVIF, WebP, JPG o PNG**) con control fino de calidad, metadatos y dimensiones. Interfaz moderna, procesamiento paralelo y soporte multiplataforma nativo.

---

## 🎯 ¿Para qué sirve?

Optimizar imágenes es uno de los pasos con mayor impacto en el rendimiento de una página web (LCP, peso total, Core Web Vitals). Esta herramienta resuelve ese paso completo en local, sin subir tus imágenes a servicios de terceros:

- Convierte cientos de imágenes en un solo lote usando todos los núcleos del CPU.
- Genera AVIF y WebP, los formatos con mejor compresión soportados por los navegadores modernos.
- Muestra el ahorro de peso por archivo y el ahorro total del lote.
- Redimensiona a un ancho fijo y genera de una sola pasada las versiones de escritorio y móvil (ej. 1200px y 800px), con nombres diferenciados automáticamente.
- Renombra con sufijo y organiza la salida en la carpeta que elijas.
- Preserva o edita los metadatos (EXIF/IPTC) según lo necesites: mantener el copyright del cliente o limpiar datos innecesarios.

---

## ✨ Características

| Característica | Descripción |
|---|---|
| **Formatos** | Entrada: `PNG`, `JPG`, `JPEG`, `WebP`, `AVIF`. Salida: `AVIF`, `WebP`, `JPG` o `PNG` optimizados. |
| **Procesamiento paralelo** | Conversión multi-hilo con slider para elegir cuántos núcleos del CPU usar. |
| **Destino de salida** | Guardar junto al original o en una carpeta personalizada, con sufijo opcional (ej. `foto-opt.avif`). |
| **Progreso y cancelación** | Barra de progreso en tiempo real (n/total), botón de cancelar y resumen de ahorro total al finalizar. |
| **Auto-orientación EXIF** | Las fotos de móvil/cámara nunca salen giradas: los píxeles se rotan y el tag Orientation se restablece. |
| **Calidad configurable** | Slider de calidad 0–100, esfuerzo de compresión AVIF y submuestreo de color (4:2:0 / 4:4:4). |
| **Transparencia** | Canal alpha preservado en AVIF/WebP/PNG (con 4:4:4 forzado en AVIF); fusión sobre fondo blanco en JPG. |
| **JPEG progresivo** | Salida JPEG con `optimize` + `progressive` para mejor carga percibida en la web. |
| **Redimensionado** | Modo "Ancho fijo" con alto proporcional automático por imagen (sin distorsión), o ancho y alto personalizados. Redimensionado LANCZOS. |
| **Doble conversión** | Genera dos versiones por imagen en un solo lote (ej. 1200px escritorio + 800px móvil) con sufijos automáticos `_1200px` / `_800px` y vista previa del nombre de salida. |
| **Motor de codificación** | Tres codificadores AVIF seleccionables con descripción comparativa en la interfaz: estándar (CPU, el más rápido), SVT-AV1 (~20% menos peso a igual calidad) y GPU NVIDIA (experimental). |
| **Metadatos** | Preservación selectiva de EXIF e IPTC, y editor integrado (Autor, Título, Copyright, fechas, descripción). |
| **Drag & Drop** | Soporte nativo robusto en Windows, macOS y Linux (rutas con espacios, URIs `file://`, multi-archivo). |
| **Vista previa** | Comparativa Antes/Después con dimensiones, tamaños y % de ahorro. |
| **Historial** | Tabla de conversiones con estado, chroma, tamaños, ahorro, hora y acceso directo al archivo. |
| **Multilingüe** | Español e Inglés con conmutación en caliente (conserva tus selecciones al cambiar). |
| **Interfaz moderna** | Tema oscuro centralizado (`utils/theme.py`) con tipografía adaptada a cada sistema operativo. |
| **Limpieza de originales** | Botón para eliminar los archivos originales tras una conversión 100% exitosa (con confirmación). |

---

## 📊 Comparativa de métodos de conversión

Todas las cifras son **medidas reales**, no estimaciones. Metodología: 12 fotografías de 4000×3000 (JPG de **1171 KB** cada una) redimensionadas a **1200px de ancho**, con 16 hilos, en un Ryzen 7 3700X + RTX 5070. La calidad se mide con **SSIM** contra la imagen sin comprimir: 1.0000 sería idéntica, y por encima de ~0.95 la diferencia no se aprecia a simple vista en pantalla.

### Resumen: mismo resultado visual, distinto coste

Estas cinco filas producen prácticamente **la misma calidad** (SSIM ≈ 0.95). Lo que cambia es el peso y el tiempo:

| Método | Peso | Reducción | Tiempo | Velocidad | Calidad |
|---|---|---|---|---|---|
| **AVIF · SVT-AV1** | **36.8 KB** 🥇 | 96.9% | 198 ms | ~5 img/s | 0.9514 |
| AVIF · GPU NVENC | 42.4 KB | 96.4% | 167 ms | ~6 img/s | 0.9533 |
| AVIF · Estándar, esfuerzo Lento | 45.1 KB | 96.1% | 1279 ms | ~0.8 img/s | 0.9527 |
| AVIF · Estándar, esfuerzo Equilibrado | 45.6 KB | 96.1% | 251 ms | ~4 img/s | 0.9515 |
| **AVIF · Estándar, Ultra Rápido** | 47.0 KB | 96.0% | **48 ms** 🥇 | **~21 img/s** | 0.9491 |
| JPG q75 *(referencia)* | 97.7 KB | 91.7% | 39 ms | ~26 img/s | 0.9558 |

> **Lectura rápida:** AVIF pesa **menos de la mitad que JPG** con la misma calidad. Dentro de AVIF, «Ultra Rápido» es **26x más rápido** que «Lento» y solo pesa 2 KB más — el esfuerzo alto casi no compensa. Si quieres el mínimo peso posible, SVT-AV1 quita otro 19%.

### Efecto del esfuerzo de compresión (AVIF, calidad 60)

| Esfuerzo | Tiempo | Peso | Calidad |
|---|---|---|---|
| Lento (2) | 1279 ms | 45.1 KB | 0.9527 |
| Equilibrado (5) | 251 ms | 45.6 KB | 0.9515 |
| **Ultra Rápido (8)** | **48 ms** | 47.0 KB | 0.9491 |

Subir el esfuerzo multiplica el tiempo por 26 para ahorrar un 4% de peso. **Para lotes grandes, «Ultra Rápido» es casi siempre la elección correcta.**

### Efecto de la calidad (AVIF, esfuerzo Equilibrado)

| Calidad | Peso | Reducción | Calidad visual | Notas |
|---|---|---|---|---|
| 45 | 17.2 KB | 98.5% | 0.8986 | Artefactos visibles en degradados y cielos |
| **60** *(recomendado)* | 45.6 KB | 96.1% | 0.9515 | Punto dulce para web |
| 75 | 78.2 KB | 93.3% | 0.9737 | Para fotografía destacada o hero images |

### Comparativa entre formatos de salida

| Formato | Config | Peso | Reducción | Tiempo | Calidad | Cuándo usarlo |
|---|---|---|---|---|---|---|
| **AVIF** | q60 | **45.6 KB** | 96.1% | 251 ms | 0.9515 | Formato principal. La mejor compresión. |
| **WebP** | q75 | 53.6 KB | 95.4% | 74 ms | 0.9446 | Respaldo para navegadores sin AVIF. |
| WebP | q60 | 38.9 KB | 96.7% | 101 ms | 0.9286 | Calidad ya algo justa. |
| **JPG** | q75 | 97.7 KB | 91.7% | 39 ms | 0.9558 | Compatibilidad universal. |
| JPG | q85 | 136.7 KB | 88.3% | 51 ms | 0.9676 | Cuando no puedes usar formatos modernos. |
| **PNG** | sin pérdida | 1301.3 KB | **+11% MAYOR** | 132 ms | 0.9933 | Solo logos y gráficos de tintas planas. |

> ⚠️ **PNG no sirve para fotografías**: al ser sin pérdida, el resultado pesó *más que el JPG original*. Úsalo solo para logotipos, iconos y capturas con texto.

### Los tres motores de codificación AVIF

| | Estándar (CPU) | SVT-AV1 | GPU NVIDIA |
|---|---|---|---|
| **Velocidad** | 🥇 48 ms (Ultra Rápido) | 198 ms | 167 ms |
| **Peso** | 47.0 KB | 🥇 36.8 KB | 42.4 KB |
| **Conserva EXIF/IPTC** | ✅ Sí | ❌ No | ❌ No |
| **Soporta transparencia** | ✅ Sí | ❌ Usa el estándar | ❌ Usa el estándar |
| **Requiere ffmpeg** | No | Sí | Sí + GPU NVIDIA |
| **Ideal para** | El día a día | Peso mínimo | CPU saturada |

**Sobre la GPU:** el codificador AV1 por hardware funciona, pero no es la bala de plata que parece. Codificar una imagen de 1200px son milisegundos; lo caro es inicializar la sesión CUDA/NVENC, y eso se paga en cada imagen. Termina siendo más rápido que el esfuerzo «Equilibrado» pero **~3.5x más lento que el motor estándar en «Ultra Rápido»**. Los codificadores por hardware están pensados para video, donde ese arranque se amortiza entre miles de fotogramas.

---

## 🚀 Instalación y Uso

### 1. Requisitos previos

- **Python 3.10+**
- (Recomendado) Entorno virtual: `python -m venv venv`
- (Opcional) **ffmpeg** en el `PATH` — solo si quieres los motores de codificación alternativos (SVT-AV1 y GPU NVIDIA). Sin él la app funciona igual con el motor estándar.

### 2. Instalación de dependencias

```bash
pip install -r requirements.txt
```

> **macOS:** para Drag & Drop instala el fork universal: `pip install tkinterdnd2-universal`

### 3. Ejecución

```bash
python app.py
```

En Windows también puedes hacer doble clic en `ConvertirImagenes.bat`.

### 4. Flujo de trabajo típico

1. Arrastra tus imágenes (o usa **Examinar archivos**).
2. Elige el formato de salida (AVIF para máxima compresión, WebP para compatibilidad amplia).
3. Ajusta calidad, motor de codificación, redimensionado, carpeta de destino y sufijo si lo necesitas.
4. Pulsa **Convertir Todo** y observa el progreso y el ahorro total.
5. (Opcional) Elimina los originales cuando todo haya salido bien.

---

## 🛠️ Empaquetado (Crear Ejecutable)

El proyecto incluye un archivo `.spec` optimizado para **PyInstaller** que garantiza la inclusión de los binarios de Tcl/Tk necesarios para el Drag & Drop.

```bash
pyinstaller ConvertirImagenes.spec
```

---

## 📁 Arquitectura del Proyecto

```
convertirimagenes/
├── app.py                  # Punto de entrada: logging, .env, arranque de la UI
├── core/
│   ├── converter.py        # Motor de conversión (AVIF/WebP/JPG/PNG, paralelo, atómico)
│   ├── encoders.py         # Codificadores AVIF opcionales vía ffmpeg (SVT-AV1, NVENC)
│   ├── exif_handler.py     # Lectura/escritura EXIF + reset de orientación
│   └── disk_validator.py   # Validación de espacio libre antes de cada lote
├── ui/
│   ├── main_window.py      # Ventana principal (3 columnas responsivas)
│   ├── drop_zone.py        # Zona de arrastre + lista de archivos
│   ├── preview_panel.py    # Comparativa Antes/Después
│   ├── history_panel.py    # Tabla de historial con métricas
│   └── metadata_modal.py   # Editor de metadatos
├── utils/
│   ├── theme.py            # Tokens de diseño: colores, tipografía, radios
│   ├── i18n.py             # Traducciones ES/EN con StringVars reactivos
│   ├── file_utils.py       # Rutas de salida, sufijos sanitizados, tamaños
│   ├── dnd_utils.py        # Normalización multiplataforma del Drag & Drop
│   ├── dnd_bootstrap.py    # Carga diferida y segura de TkinterDnD2
│   └── logging_utils.py    # Logs sanitizados (sin rutas absolutas en producción)
└── tests/                  # Suite de pruebas (unittest) del motor y utilidades
```

Detalles técnicos relevantes:

- **Escritura atómica**: cada imagen se codifica a un archivo temporal y luego se mueve a su destino final, evitando archivos corruptos si el proceso se interrumpe.
- **Paralelismo**: `ThreadPoolExecutor` — Pillow libera el GIL durante la codificación, por lo que los hilos escalan bien y comparten memoria de forma segura.
- **AVIF con fallback nativo**: usa `pillow-avif-plugin` y, si no está disponible, el soporte AVIF nativo de Pillow ≥ 11.3.
- **UI desacoplada del trabajo**: la conversión corre en un hilo aparte y se comunica con la interfaz mediante una cola (`queue.Queue`) sondeada cada 80 ms — la ventana nunca se congela.

---

## 🛡️ Seguridad y Privacidad

- **100% local**: tus imágenes nunca salen de tu equipo.
- **Zero Leak Logging**: los logs evitan imprimir rutas absolutas del sistema (`C:\Users\...`) salvo en modo desarrollo (`DEV_MODE=true`).
- **Anti decompression-bomb**: las imágenes maliciosamente grandes producen un error controlado en lugar de agotar la memoria.
- **Sin inyección de argumentos**: las llamadas al explorador de archivos usan listas de argumentos, nunca strings interpolados.
- **Sufijos sanitizados**: el sufijo de salida se limpia de caracteres de ruta (`../`, `\`, `:`…) antes de usarse.
- **Variables de entorno**: soporte de `.env` (vía `python-dotenv`); `.gitignore` cubre `.env` y `.env.*` conservando `.env.example`.
- **Validación de disco**: verifica el espacio libre del volumen de destino antes de procesar el lote.

---

## 🆕 Novedades de la versión 1.5.0

Resumen de la última actualización (detalle completo en [CHANGELOG.md](CHANGELOG.md)):

- **Motor de codificación seleccionable** para AVIF, con descripciones en la interfaz que explican qué da cada uno:

  | Motor | Velocidad | Peso (foto 1200px) | Cuándo usarlo |
  |---|---|---|---|
  | **Estándar (CPU)** *(predeterminado)* | **~21 img/s** | 47.0 KB | Casi siempre. Único que conserva EXIF y transparencia. |
  | **SVT-AV1** | ~5 img/s | **36.8 KB (−19%)** | Cuando el peso importa más que el tiempo. |
  | **GPU NVIDIA** *(experimental)* | ~6 img/s | 42.4 KB | Si la CPU está saturada. |

  Los motores externos requieren **ffmpeg** en el PATH; si falta, la app lo detecta y sigue usando el estándar sin fallar. Ver la [comparativa completa](#-comparativa-de-métodos-de-conversión) con todas las mediciones.

- **Comparativa de métodos documentada**: nueva sección del README con tiempos, pesos y calidad (SSIM) medidos para cada formato, nivel de calidad, esfuerzo y motor.

### Versión 1.4.0

- **Modo "Ancho fijo"**: fijas el ancho (ej. 1200px) y el alto se calcula proporcionalmente por cada imagen, sin distorsión.
- **Doble conversión escritorio + móvil**: dos versiones por imagen en un solo lote (ej. 1200px y 800px), aplicada de forma masiva.
- **Sufijos automáticos de píxeles**: `fotografia40.jpg` → `fotografia40_1200px.avif` y `fotografia40_800px.avif`, combinables con el sufijo personalizado.
- **Vista previa del nombre de salida** en vivo, según formato, sufijos y anchos elegidos.
- **Progreso y limpieza de originales** coherentes con las variantes: se cuenta cada archivo generado y solo se pueden borrar los originales cuyas versiones se convirtieron todas con éxito.

---

## 🧪 Pruebas

La suite usa `unittest`, así que no necesita dependencias extra:

```bash
python -m unittest discover -s tests -v
```

También funciona con pytest si lo prefieres (`pip install pytest && python -m pytest tests/ -q`).

La suite cubre el motor de conversión (AVIF/WebP/JPG/PNG, transparencia, presets, sufijos), el redimensionado de ancho fijo y las variantes múltiples por archivo, la selección y el retroceso de los motores de codificación, la validación de disco y el parser de Drag & Drop. Las pruebas de los motores externos se saltan solas si ffmpeg no está instalado.

---

## 🤝 Contribuciones

1. Haz un Fork del proyecto.
2. Crea una rama para tu mejora: `git checkout -b feature/MejoraIncreible`
3. Realiza tus cambios con **Conventional Commits** (formato: `feat: descripción`).
4. Haz un Push a la rama y abre un Pull Request.

---

Desarrollado con ❤️ para la optimización web.
