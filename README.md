# ⚡ ConvertirImagenes — Conversor Masivo de Imágenes para Web (AVIF · WebP · JPG · PNG)

![Vista Previa de la Aplicación](img/app-optimizar-imagenes-desarrollo-web.avif)

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![Version](https://img.shields.io/badge/version-1.4.0-orange)

Aplicación de escritorio profesional para la **conversión masiva de imágenes**, pensada como herramienta esencial del flujo de trabajo de desarrollo web: toma lotes grandes de imágenes (PNG, JPG, WebP, AVIF) y los convierte a formatos modernos y optimizados (**AVIF, WebP, JPG o PNG**) con control fino de calidad, metadatos y dimensiones. Interfaz moderna, procesamiento paralelo y soporte multiplataforma nativo.

---

## 🎯 ¿Para qué sirve?

Optimizar imágenes es uno de los pasos con mayor impacto en el rendimiento de una página web (LCP, peso total, Core Web Vitals). Esta herramienta resuelve ese paso completo en local, sin subir tus imágenes a servicios de terceros:

- Convierte cientos de imágenes en un solo lote usando todos los núcleos del CPU.
- Genera AVIF y WebP, los formatos con mejor compresión soportados por los navegadores modernos.
- Muestra el ahorro de peso por archivo y el ahorro total del lote.
- Redimensiona, renombra con sufijo y organiza la salida en la carpeta que elijas.
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
| **Metadatos** | Preservación selectiva de EXIF e IPTC, y editor integrado (Autor, Título, Copyright, fechas, descripción). |
| **Drag & Drop** | Soporte nativo robusto en Windows, macOS y Linux (rutas con espacios, URIs `file://`, multi-archivo). |
| **Vista previa** | Comparativa Antes/Después con dimensiones, tamaños y % de ahorro. |
| **Historial** | Tabla de conversiones con estado, chroma, tamaños, ahorro, hora y acceso directo al archivo. |
| **Multilingüe** | Español e Inglés con conmutación en caliente (conserva tus selecciones al cambiar). |
| **Interfaz moderna** | Tema oscuro centralizado (`utils/theme.py`) con tipografía adaptada a cada sistema operativo. |
| **Limpieza de originales** | Botón para eliminar los archivos originales tras una conversión 100% exitosa (con confirmación). |

---

## 🚀 Instalación y Uso

### 1. Requisitos previos

- **Python 3.10+**
- (Recomendado) Entorno virtual: `python -m venv venv`

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
3. Ajusta calidad, redimensionado, carpeta de destino y sufijo si lo necesitas.
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
└── tests/                  # Suite de pruebas (pytest) del motor y utilidades
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

## 🆕 Novedades de la versión 1.4.0

Resumen de la última actualización (detalle completo en [CHANGELOG.md](CHANGELOG.md)):

- **Modo "Ancho fijo"**: fijas el ancho (ej. 1200px) y el alto se calcula proporcionalmente por cada imagen, sin distorsión.
- **Doble conversión escritorio + móvil**: dos versiones por imagen en un solo lote (ej. 1200px y 800px), aplicada de forma masiva.
- **Sufijos automáticos de píxeles**: `fotografia40.jpg` → `fotografia40_1200px.avif` y `fotografia40_800px.avif`, combinables con el sufijo personalizado.
- **Vista previa del nombre de salida** en vivo, según formato, sufijos y anchos elegidos.
- **Progreso y limpieza de originales** coherentes con las variantes: se cuenta cada archivo generado y solo se pueden borrar los originales cuyas versiones se convirtieron todas con éxito.

---

## 🧪 Pruebas

```bash
pip install pytest
python -m pytest tests/ -q
```

La suite cubre el motor de conversión (AVIF/WebP/JPG, transparencia, presets, sufijos), la validación de disco y el parser de Drag & Drop.

---

## 🤝 Contribuciones

1. Haz un Fork del proyecto.
2. Crea una rama para tu mejora: `git checkout -b feature/MejoraIncreible`
3. Realiza tus cambios con **Conventional Commits** (formato: `feat: descripción`).
4. Haz un Push a la rama y abre un Pull Request.

---

Desarrollado con ❤️ para la optimización web.
