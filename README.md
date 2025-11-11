# Subtitulador Multilenguaje

Herramienta en Python para traducir archivos de subtítulos `.srt` entre múltiples idiomas mediante modelos de traducción neuronal (Facebook M2M100). Incluye una interfaz gráfica simple (Tkinter) que permite:

- Seleccionar el archivo `.srt` de entrada.
- Detectar automáticamente el idioma origen (opción `auto`).
- Elegir el idioma destino entre una lista amplia (es, en, de, fr, it, pt, ru, zh, ja, ko, etc.).
- Definir dónde guardar el archivo traducido.
- Traducir línea a línea mostrando diálogos informativos.
- Uso automático de GPU (CUDA) si está disponible, sino CPU.

## Características principales
- Traducción multilenguaje con un único modelo (M2M100 418M).
- Detección automática del idioma con `langdetect` y heurísticas de respaldo.
- Interfaz gráfica (sin necesidad de editar rutas manualmente).
- Carga perezosa del modelo (se descarga solo la primera vez).
- Manejo de errores por línea: si una línea falla, se conserva el texto original.
- Generación de nombre sugerido para el archivo de salida.

## Requisitos
Instala dependencias (ideal dentro de un entorno virtual):

```bash
pip install -r requirements.txt
```

Archivo `requirements.txt` incluye:
```
pysrt
transformers
sentencepiece
safetensors
torch
langdetect
```

Para mejor rendimiento en GPU instala PyTorch con soporte CUDA adecuado (ver https://pytorch.org/).

## Uso rápido

### Método 1: Script Python
```bash
python subtitulador.py
```
Se abrirá la ventana. Selecciona el `.srt`, deja `auto` para detectar idioma origen y elige destino. Pulsa "Traducir".

### Método 2: Archivo .BAT (Windows)
Doble clic en `ejecutar_subtitulador.bat`:
- Crea el entorno virtual `venv` si no existe.
- Instala dependencias.
- Ejecuta la aplicación.

## Idiomas soportados
La lista actual (códigos ISO 639-1) para destino incluye:
```
auto, en, es, de, ru, fr, it, pt, nl, pl, sv, no, da, fi, tr, el, ro, cs, uk, hu, bg, ar, he, hi, bn, id, ms, vi, th, zh, ja, ko
```
`auto` sólo se usa como origen (detectar). Si el idioma detectado no está en la lista se intentará una heurística; en caso extremo se asumirá `en`.

## Limitaciones actuales
- La detección de idioma depende de suficiente texto en el `.srt` (líneas vacías o muy cortas pueden afectar).
- El modelo M2M100 puede consumir memoria (418M parámetros). En equipos con poca RAM puede tardar en cargar.
- No hay barra de progreso todavía.
- No se optimiza la traducción por lotes (se podría agrupar líneas para acelerar).

## Posibles mejoras futuras
- Barra de progreso y tiempo estimado.
- Cache de traducciones repetidas.
- Traducción batch para acelerar (concatenar varias líneas y luego dividir).
- Opciones de normalización (capitalización, limpieza de tags HTML, etc.).
- Soporte para otros formatos (WEBVTT `.vtt`).
- Exportación masiva de múltiples archivos.

## Estructura del proyecto
```
subtitulador.py        # Lógica principal y GUI.
ejecutar_subtitulador.bat  # Script Windows para auto setup y ejecución.
requirements.txt       # Dependencias del proyecto.
README.md              # Este documento.
```

## Flujo interno simplificado
1. GUI solicita archivo `.srt`.
2. Si origen = `auto`, se extraen hasta ~50 líneas y se detecta idioma con `langdetect`.
3. Se carga el modelo M2M100 (una sola vez, cache global).
4. Se traduce cada línea forzando el token BOS del idioma destino.
5. Se escribe el nuevo `.srt` en la ruta seleccionada.

## Problemas comunes
- "No se ha podido resolver la importación 'langdetect'": Instala requerimientos (`pip install langdetect`).
- CUDA no se usa: Comprueba `torch.cuda.is_available()` y que instalaste la versión de PyTorch con soporte CUDA.
- Archivo con codificación distinta: Asegúrate de que el `.srt` esté en UTF-8 o ajusta la lectura en `pysrt.open()`.

## Licencia
Este proyecto usa modelos publicados por Facebook AI / HuggingFace bajo sus respectivas licencias. Revisa las condiciones de uso de cada modelo antes de uso comercial.

---
¿Necesitas añadir otra funcionalidad? Abre una issue o solicita ajustes.
