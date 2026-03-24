# ConvertirImagenes — PNG/JPG → AVIF Converter

Aplicación de escritorio Windows para convertir imágenes PNG/JPG al formato moderno **AVIF** con interfaz gráfica completa.

## Características

| Característica | Detalles |
|---|---|
| Formatos entrada | PNG, JPG, JPEG |
| Formato salida | AVIF |
| Arrastre y soltado | Nativo (requiere `tkinterdnd2`) |
| Niveles de calidad | Alta · Media · Baja |
| Velocidad de codificación | Rápido · Bueno · Mejor |
| EXIF | Preservar o eliminar |
| Carpeta destino | Misma origen o personalizada |
| Preview | Antes / Después con tamaños |
| Progreso | Barra por lotes + cancelación |
| Historial | Últimas N conversiones |
| Validación | Espacio en disco antes de procesar |

## Instalación

```bash
# 1. Clonar / descargar el proyecto
cd convertirimagenes

# 2. Instalar dependencias
pip install -r requirements.txt
```

> **Nota:** `pillow-avif-plugin` descarga automáticamente binarios de libavif para Windows.  
> Si `tkinterdnd2` no está disponible, el drag-and-drop nativo se desactiva; el botón "Examinar" sigue funcionando.

## Uso

```bash
python app.py
```

1. Arrastra imágenes a la zona de destino **o** haz clic en **Examinar archivos**.
2. Selecciona el nivel de calidad (Alta / Media / Baja).
3. Ajusta la velocidad de codificación y opciones EXIF.
4. Opcionalmente elige una carpeta destino.
5. Haz clic en **▶ Convertir a AVIF**.

## Estructura del proyecto

```
convertirimagenes/
├── app.py                  # Entry point
├── requirements.txt
├── core/
│   ├── converter.py        # Motor de conversión AVIF
│   ├── disk_validator.py   # Validación de espacio en disco
│   └── exif_handler.py     # Manejo de metadatos EXIF
├── ui/
│   ├── main_window.py      # Ventana principal
│   ├── drop_zone.py        # Zona drag-and-drop
│   ├── preview_panel.py    # Preview antes/después
│   └── history_panel.py    # Historial de conversiones
├── utils/
│   └── file_utils.py       # Helpers de archivos
└── tests/
    ├── test_converter.py
    └── test_disk_validator.py
```

## Ejecutar pruebas

```bash
python -m pytest tests/ -v
```

## Presets de calidad

| Preset | `quality` | `speed` | Uso típico |
|--------|-----------|---------|------------|
| Alta   | 80        | 6       | Fotografía, archivado |
| Media  | 60        | 4       | Web general (recomendado) |
| Baja   | 30        | 2       | Miniaturas, máxima compresión |

## Requisitos

- Python 3.10+
- Windows 10/11
- `pillow-avif-plugin` (instala `libavif` automáticamente)
