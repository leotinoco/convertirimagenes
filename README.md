# ⚡ ConvertirImagenes — Advanced Multiplatform AVIF Converter

![Vista Previa de la Aplicación](img/app-optimizar-imagenes-desarrollo-web.avif)

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

Aplicación de escritorio profesional para la conversión masiva de imágenes a **AVIF**, optimizada para rendimiento y privacidad. Diseñada con una interfaz moderna y soporte multiplataforma nativo.

---

## ✨ Características Principales

| Característica | Descripción |
|---|---|
| **Formatos** | Entrada: `PNG`, `JPG`, `JPEG`, `WebP`. Salida: `AVIF` optimizado. |
| **Interfaz Moderna** | Basada en `CustomTkinter` con soporte de temas y diseño responsivo. |
| **Drag & Drop** | Soporte nativo robusto en Windows, macOS y Linux. |
| **Paralelismo** | Procesamiento multi-hilo adaptable al número de núcleos del CPU. |
| **Metadatos** | Preservación selectiva de EXIF e IPTC (Photoshop/Lightroom). |
| **Edición de Metadata** | Formulario integrado para modificar Autor, Título, Copyright y más. |
| **Redimensionado** | Redimensionado automático con preservación de relación de aspecto. |
| **Vista Previa** | Comparativa visual Antes/Después con tamaños y % de ahorro. |
| **Multilingüe** | Soporte completo para Español e Inglés (conmutación en caliente). |
| **Seguridad** | Auditoría DevSecOps: logs sanitizados, soporte para `.env` y rutas relativas. |

---

## 🚀 Instalación y Uso

### 1. Requisitos Previos
- **Python 3.10+**
- (Opcional) Un entorno virtual (recomendado): `python -m venv venv`

### 2. Instalación de Dependencias
```bash
pip install -r requirements.txt
```

### 3. Ejecución
```bash
python app.py
```

---

## 🛠️ Empaquetado (Crear Ejecutable)

El proyecto incluye un archivo `.spec` optimizado para **PyInstaller** que garantiza la inclusión de los binarios de Tcl/Tk necesarios para el Drag & Drop.

```bash
# Windows / macOS / Linux
pyinstaller ConvertirImagenes.spec
```

---

## 📁 Estructura del Proyecto

- `app.py`: Punto de entrada que inicializa logs y variables de entorno.
- `core/`: Motor de conversión (`ThreadPoolExecutor`), manejo de EXIF y validación de disco.
- `ui/`: Componentes de la interfaz (Main Window, DropZone, Modales de Metadatos).
- `utils/`: Utilidades de traducción (i18n), sanitización de rutas y gestión de logs.
- `ConvertirImagenes.spec`: Configuración experta para PyInstaller.

---

## 🛡️ Seguridad y Privacidad

- **Zero Leak Logging**: El sistema de logs utiliza una utilidad personalizada que evita la impresión de rutas absolutas de tu sistema (`C:\Users\Username\...`) en los informes de error.
- **Environment Variables**: Soporte para archivos `.env` (vía `python-dotenv`) para configuraciones locales sin exponer secretos.
- **Validación de Disco**: Verifica el espacio antes de procesar para evitar archivos corruptos.

---

## 🤝 Contribuciones

1. Haz un Fork del proyecto.
2. Crea una rama para tu mejora: `git checkout -b feature/MejoraIncreible`
3. Realiza tus cambios con **Conventional Commits** (formato: `feat: descripción`).
4. Haz un Push a la rama y abre un Pull Request.

---

Desarrollado con ❤️ para la optimización web.
