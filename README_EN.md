# Multilingual Subtitle Translator

A Python tool to translate `.srt` subtitle files between many languages using neural machine translation (Facebook M2M100). It ships with a simple Tkinter GUI so you don’t have to type file paths.

- Pick the input `.srt` file.
- Auto-detect the source language ("auto" option).
- Choose the target language from a broad list (en, es, de, fr, it, pt, ru, zh, ja, ko, and more).
- Choose where to save the translated file.
- Translates line-by-line with informative dialogs.
- Automatically uses GPU (CUDA) if available, otherwise CPU.

## Key features
- Multilingual translation with a single model (M2M100 418M).
- Automatic language detection with `langdetect` and simple fallbacks.
- Simple GUI (no manual path editing).
- Lazy model download and caching on first run.
- Per-line error handling: if a line fails, the original text is preserved.
- Smart default output filename.

## Requirements
Install dependencies (recommended inside a virtual environment):

```pwsh
pip install -r requirements.txt
```

`requirements.txt` includes:
```
pysrt
transformers
sentencepiece
safetensors
torch
langdetect
```

For better performance on GPU, install the correct CUDA-enabled PyTorch (see https://pytorch.org/ for the matching wheel).

## Quick start

### Option 1: Run the Python script
```pwsh
python .\subtitulador.py
```
A window will open. Select the `.srt`, keep `auto` for source language detection, choose the target language, and click "Translate".

### Option 2: Windows .BAT
Double-click `ejecutar_subtitulador.bat`:
- Creates a `venv` if missing.
- Installs dependencies.
- Launches the app.

## Supported languages
Current (ISO 639-1) list for target includes:
```
auto, en, es, de, ru, fr, it, pt, nl, pl, sv, no, da, fi, tr, el, ro, cs, uk, hu, bg, ar, he, hi, bn, id, ms, vi, th, zh, ja, ko
```
`auto` is for source only (detect). If detection fails, simple heuristics are applied; as a last resort, English (`en`) is assumed.

## How it works
1. GUI asks for an `.srt` file.
2. If source = `auto`, up to ~50 non-empty lines are sampled and detected via `langdetect`.
3. The M2M100 model is loaded once and cached.
4. Each line is translated by forcing the target language BOS token.
5. The new `.srt` is written to the chosen location.

## Troubleshooting
- "Cannot resolve import 'langdetect'": install requirements (`pip install langdetect` or `pip install -r requirements.txt`).
- CUDA not used: check `torch.cuda.is_available()` and install a CUDA-enabled PyTorch build.
- File encoding issues: ensure `.srt` is UTF-8 or adjust `pysrt.open()` encoding.

## Project structure
```
subtitulador.py            # Main logic and GUI
Ejecutar_subtitulador.bat  # Windows script for auto-setup and run
requirements.txt           # Project dependencies
README.md                  # Spanish docs
README_EN.md               # English docs
```

## Limitations
- Language detection needs enough text; very short lines can reduce accuracy.
- M2M100 (418M params) is sizeable; first load may take time and memory.
- No progress bar yet.
- No batching; batching could speed up translation.

## Roadmap ideas
- Progress bar and ETA.
- Cache repeated segments.
- Batch translation (group lines, then split back).
- Text normalization options (capitalization, HTML tag cleanup).
- More formats (e.g., WEBVTT `.vtt`).
- Bulk translation of multiple files.

## License
This project uses models distributed by Facebook AI / HuggingFace under their respective licenses. Review model terms before commercial use.
