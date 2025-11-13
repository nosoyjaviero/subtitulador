import pysrt
from transformers import MarianMTModel, MarianTokenizer
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
from tkinter import Tk, filedialog, messagebox
from tkinter import ttk
import os
import torch
import re
try:
    import winsound  # Solo Windows
except Exception:
    winsound = None

# Selección de dispositivo: GPU (si disponible) o CPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


# Lista ampliada de idiomas comunes (códigos ISO 639-1 compatibles con M2M100)
IDIOMAS = {
    'auto': 'Detectar automáticamente',
    'en': 'Inglés',
    'es': 'Español',
    'de': 'Alemán',
    'ru': 'Ruso',
    'fr': 'Francés',
    'it': 'Italiano',
    'pt': 'Portugués',
    'nl': 'Neerlandés',
    'pl': 'Polaco',
    'sv': 'Sueco',
    'no': 'Noruego',
    'da': 'Danés',
    'fi': 'Finlandés',
    'tr': 'Turco',
    'el': 'Griego',
    'ro': 'Rumano',
    'cs': 'Checo',
    'uk': 'Ucraniano',
    'hu': 'Húngaro',
    'bg': 'Búlgaro',
    'ar': 'Árabe',
    'he': 'Hebreo',
    'hi': 'Hindi',
    'bn': 'Bengalí',
    'id': 'Indonesio',
    'ms': 'Malayo',
    'vi': 'Vietnamita',
    'th': 'Tailandés',
    'zh': 'Chino',
    'ja': 'Japonés',
    'ko': 'Coreano',
}


_m2m_tokenizer = None
_m2m_model = None


def cargar_modelo(src_lang: str = 'en', tgt_lang: str = 'es'):
    """Carga (o reutiliza) el modelo multilenguaje M2M100 para cualquier par soportado."""
    global _m2m_model, _m2m_tokenizer
    model_name = 'facebook/m2m100_418M'
    if _m2m_tokenizer is None or _m2m_model is None:
        _m2m_tokenizer = M2M100Tokenizer.from_pretrained(model_name)
        _m2m_model = M2M100ForConditionalGeneration.from_pretrained(model_name)
        _m2m_model = _m2m_model.to(device)
        _m2m_model.eval()
    return _m2m_tokenizer, _m2m_model, model_name


def traducir_texto(texto, tokenizer, model, src_lang: str, tgt_lang: str):
    """Traduce una cadena con M2M100 para src_lang->tgt_lang."""
    # Configurar idioma origen y decodificar hacia el idioma destino
    tokenizer.src_lang = src_lang
    inputs = tokenizer(texto, return_tensors='pt', padding=True, truncation=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    forced_bos = tokenizer.get_lang_id(tgt_lang)
    with torch.no_grad():
        traduccion = model.generate(**inputs, forced_bos_token_id=forced_bos, max_length=512)
    texto_traducido = tokenizer.batch_decode(traduccion, skip_special_tokens=True)[0]
    return texto_traducido


def _chunk_text_by_tokens(texto: str, tokenizer, max_tokens: int = 480) -> list:
    """Divide un texto largo en trozos con límite aproximado de tokens para el modelo."""
    piezas = re.split(r'(?:(?<=[\.!?])\s+|\n{2,})', texto or '')
    piezas = [p for p in piezas if p and p.strip()]
    chunks = []
    actual = ''
    for p in piezas:
        candidato = (actual + (' ' if actual else '') + p).strip()
        token_count = len(tokenizer(candidato, return_tensors='pt', truncation=False).input_ids[0])
        if token_count <= max_tokens:
            actual = candidato
        else:
            if actual:
                chunks.append(actual)
                actual = p.strip()
                token_count_p = len(tokenizer(actual, return_tensors='pt', truncation=False).input_ids[0])
                if token_count_p > max_tokens:
                    # fallback: cortar por caracteres (~3 chars por token aprox)
                    step = max(300, max_tokens * 3)
                    t = actual
                    while t:
                        chunks.append(t[:step])
                        t = t[step:]
                    actual = ''
            else:
                step = max(300, max_tokens * 3)
                t = p.strip()
                while t:
                    chunks.append(t[:step])
                    t = t[step:]
                actual = ''
    if actual:
        chunks.append(actual)
    return chunks


def traducir_texto_largo(texto: str, tokenizer, model, src_lang: str, tgt_lang: str, max_tokens: int = 480) -> str:
    """Traduce un texto largo troceándolo para respetar límites del modelo."""
    if not texto:
        return ''
    if src_lang == tgt_lang:
        return texto
    tokenizer.src_lang = src_lang
    forced_bos = tokenizer.get_lang_id(tgt_lang)
    partes = _chunk_text_by_tokens(texto, tokenizer, max_tokens=max_tokens)
    resultados = []
    for parte in partes:
        inputs = tokenizer(parte, return_tensors='pt', padding=True, truncation=True)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            out = model.generate(**inputs, forced_bos_token_id=forced_bos, max_length=512)
        resultados.append(tokenizer.batch_decode(out, skip_special_tokens=True)[0])
    return '\n'.join(resultados)


def _traducir_linea_preservando(long_line: str, tokenizer, model, src_lang: str, tgt_lang: str, max_tokens: int = 480) -> str:
    """Traduce una línea potencialmente larga. Si excede tokens, trocea y une sin añadir saltos nuevos."""
    # Caso trivial
    try:
        token_count = len(tokenizer(long_line, return_tensors='pt', truncation=False).input_ids[0])
    except Exception:
        token_count = 0
    if token_count and token_count <= max_tokens:
        return traducir_texto(long_line, tokenizer, model, src_lang, tgt_lang)
    # Trocear por tokens y unir con un espacio para no introducir \n extra
    partes = _chunk_text_by_tokens(long_line, tokenizer, max_tokens=max_tokens)
    traducidas = []
    for p in partes:
        traducidas.append(traducir_texto(p, tokenizer, model, src_lang, tgt_lang))
    return ' '.join(traducidas)


def traducir_txt_a_txt_preservando_lineas(archivo_txt: str, archivo_salida_txt: str, tokenizer, model,
                                         src_lang: str, tgt_lang: str, max_tokens: int = 480):
    """Traduce un .txt preservando exactamente los saltos de línea del archivo original."""
    with open(archivo_txt, 'r', encoding='utf-8', errors='ignore') as f:
        lineas = f.read().splitlines(keepends=True)

    out = []
    for ln in lineas:
        # Separar el fin de línea para preservarlo tal cual
        if ln.endswith('\r\n'):
            contenido, fin = ln[:-2], '\r\n'
        elif ln.endswith('\n'):
            contenido, fin = ln[:-1], '\n'
        else:
            contenido, fin = ln, ''

        if contenido.strip():
            if src_lang != tgt_lang:
                try:
                    traducida = _traducir_linea_preservando(contenido, tokenizer, model, src_lang, tgt_lang, max_tokens=max_tokens)
                except Exception:
                    traducida = contenido
            else:
                traducida = contenido
        else:
            traducida = contenido
        out.append(traducida + fin)

    with open(archivo_salida_txt, 'w', encoding='utf-8') as f:
        f.write(''.join(out))


def traducir_srt(archivo_entrada, archivo_salida, tokenizer, model, src_lang: str, tgt_lang: str):
    """Traduce un archivo .srt y lo guarda en archivo_salida usando src_lang->tgt_lang."""
    subs = pysrt.open(archivo_entrada, encoding='utf-8')

    for sub in subs:
        texto = sub.text
        try:
            sub.text = traducir_texto(texto, tokenizer, model, src_lang, tgt_lang)
        except Exception as e:
            print(f"[ADVERTENCIA] No se pudo traducir un segmento: {e}")
            sub.text = texto

    subs.save(archivo_salida, encoding='utf-8')


def detectar_idioma_archivo(archivo_entrada: str) -> str:
    """Detecta el idioma mayoritario del SRT usando 'langdetect' con heurísticas de respaldo."""
    try:
        subs = pysrt.open(archivo_entrada, encoding='utf-8')
        muestras = []
        for sub in subs:
            if sub.text and sub.text.strip():
                muestras.append(sub.text)
            if len(muestras) >= 50:
                break
        muestra = "\n".join(muestras)
        try:
            from langdetect import detect
            code = detect(muestra)
            # Normalizar ciertos códigos a equivalentes M2M100 si hace falta
            # p.ej. 'zh-cn' -> 'zh'
            if code.startswith('zh'):
                return 'zh'
            return code
        except Exception:
            pass
        # Heurísticas simples de respaldo
        if any('\u0400' <= ch <= '\u04FF' for ch in muestra):
            return 'ru'
        if any(ch in 'äöüÄÖÜß' for ch in muestra):
            return 'de'
        if any(ch in 'áéíóúÁÉÍÓÚñÑ' for ch in muestra):
            return 'es'
        return 'en'
    except Exception:
        # Si no se puede leer, asumir inglés
        return 'en'


def seleccionar_archivo_entrada():
    """Abre un diálogo para seleccionar el archivo de entrada (.srt o .txt)."""
    root = Tk()
    root.withdraw()
    # Traer ventana al frente en Windows
    try:
        root.call('wm', 'attributes', '.', '-topmost', True)
    except Exception:
        pass
    ruta = filedialog.askopenfilename(
        title='Selecciona el archivo a traducir (SRT o TXT)',
        filetypes=[('SubRip (*.srt)', '*.srt'), ('Texto (*.txt)', '*.txt'), ('Todos los archivos', '*.*')]
    )
    root.destroy()
    return ruta


def seleccionar_archivo_salida(nombre_sugerido: str):
    """Abre un diálogo para elegir dónde guardar el .srt de salida."""
    root = Tk()
    root.withdraw()
    try:
        root.call('wm', 'attributes', '.', '-topmost', True)
    except Exception:
        pass
    ruta = filedialog.asksaveasfilename(
        title='Guardar subtítulos traducidos como...',
        defaultextension='.srt',
        initialfile=nombre_sugerido,
        filetypes=[('SubRip (*.srt)', '*.srt'), ('Todos los archivos', '*.*')]
    )
    root.destroy()
    return ruta


def detectar_idioma_texto(texto: str) -> str:
    """Detecta el idioma mayoritario de un texto plano."""
    muestra = (texto or '').strip()
    if not muestra:
        return 'en'
    try:
        from langdetect import detect
        code = detect(muestra)
        if code.startswith('zh'):
            return 'zh'
        return code
    except Exception:
        pass
    # Heurísticas muy simples
    if any('\u0400' <= ch <= '\u04FF' for ch in muestra):
        return 'ru'
    if any(ch in 'äöüÄÖÜß' for ch in muestra):
        return 'de'
    if any(ch in 'áéíóúÁÉÍÓÚñÑ' for ch in muestra):
        return 'es'
    return 'en'


def _seconds_to_subrip_time(total_seconds: float) -> pysrt.SubRipTime:
    total_seconds = max(0.0, float(total_seconds))
    ms = int(round((total_seconds - int(total_seconds)) * 1000))
    total = int(total_seconds)
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    return pysrt.SubRipTime(hours=h, minutes=m, seconds=s, milliseconds=ms)


def _wrap_text_for_subtitle(texto: str, max_chars: int = 42) -> str:
    """Envuelve el texto en líneas de hasta max_chars (aprox), respetando palabras."""
    palabras = (texto or '').split()
    if not palabras:
        return ''
    lineas = []
    actual = ''
    for w in palabras:
        if not actual:
            actual = w
        elif len(actual) + 1 + len(w) <= max_chars:
            actual += ' ' + w
        else:
            lineas.append(actual)
            actual = w
    if actual:
        lineas.append(actual)
    return "\n".join(lineas)


def _segmentar_texto(texto: str, modo: str = 'oracion') -> list:
    """Segmenta texto en 'oracion' (por puntuación) o 'linea' (por saltos de línea)."""
    if modo == 'linea':
        segs = [ln.strip() for ln in (texto or '').splitlines()]
        return [s for s in segs if s]
    # 'oracion': separar por fin de oración simple y/o saltos de párrafo
    # Nota: es una heurística; para casos complejos se podría integrar NLTK/spacy.
    partes = re.split(r'(?<=[\.!?])\s+|\n{2,}', texto or '')
    segs = [p.strip() for p in partes if p and p.strip()]
    return segs


def traducir_txt_a_srt(archivo_txt: str, archivo_salida_srt: str, tokenizer, model,
                       src_lang: str, tgt_lang: str, duracion_seg: float = 3.0,
                       modo_segmentacion: str = 'oracion', max_chars_linea: int = 42):
    """Lee un .txt, lo segmenta, traduce (si procede) y guarda un .srt sintético."""
    with open(archivo_txt, 'r', encoding='utf-8', errors='ignore') as f:
        texto = f.read()

    segmentos = _segmentar_texto(texto, modo_segmentacion)
    subs = pysrt.SubRipFile()
    for i, seg in enumerate(segmentos):
        texto_seg = seg
        try:
            if src_lang and tgt_lang and src_lang != tgt_lang:
                texto_seg = traducir_texto(seg, tokenizer, model, src_lang, tgt_lang)
        except Exception as e:
            print(f"[ADVERTENCIA] Fallo traduciendo un segmento TXT: {e}")
            texto_seg = seg

        texto_envuelto = _wrap_text_for_subtitle(texto_seg, max_chars_linea)
        start = _seconds_to_subrip_time(i * float(duracion_seg))
        end = _seconds_to_subrip_time((i + 1) * float(duracion_seg))
        item = pysrt.SubRipItem(index=i + 1, start=start, end=end, text=texto_envuelto)
        subs.append(item)

    subs.save(archivo_salida_srt, encoding='utf-8')


def app_gui():
    root = Tk()
    root.title('Subtitulador traductor')
    try:
        root.call('wm', 'attributes', '.', '-topmost', True)
    except Exception:
        pass

    # Variables de UI
    var_in_path = Tk().StringVar() if hasattr(Tk, 'StringVar') else None
    # Preferir crear variables desde el mismo root
    from tkinter import StringVar
    var_in_path = StringVar()
    var_out_path = StringVar()
    var_src = StringVar()
    var_tgt = StringVar()
    var_out_fmt = StringVar()

    # Valores iniciales
    var_src.set('en')
    var_tgt.set('es')
    var_out_fmt.set('srt')

    # Layout
    frm = ttk.Frame(root, padding=12)
    frm.grid(row=0, column=0, sticky='nsew')
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    # Fila archivo entrada
    ttk.Label(frm, text='Archivo:').grid(row=0, column=0, sticky='w', padx=(0,8), pady=4)
    ent_in = ttk.Entry(frm, textvariable=var_in_path, width=60)
    ent_in.grid(row=0, column=1, sticky='ew', pady=4)
    def on_browse_in():
        path = filedialog.askopenfilename(title='Selecciona el archivo (SRT o TXT)', filetypes=[('SubRip (*.srt)', '*.srt'), ('Texto (*.txt)', '*.txt'), ('Todos los archivos', '*.*')])
        if path:
            var_in_path.set(path)
            # Detectar idioma según tipo de archivo
            _, ext = os.path.splitext(path.lower())
            if ext == '.srt':
                detected = detectar_idioma_archivo(path)
            elif ext == '.txt':
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        detected = detectar_idioma_texto(f.read())
                except Exception:
                    detected = 'en'
            else:
                detected = 'en'
            var_src.set(detected)
            # Sugerir salida con formato elegido
            base = os.path.basename(path)
            nombre, _ = os.path.splitext(base)
            fmt = (var_out_fmt.get().strip() or 'srt').lower()
            ext_out = '.srt' if fmt == 'srt' else '.txt'
            var_out_path.set(os.path.join(os.path.dirname(path), f"{nombre}.{var_tgt.get()}{ext_out}"))
    ttk.Button(frm, text='Examinar...', command=on_browse_in).grid(row=0, column=2, padx=(8,0), pady=4)

    # Fila archivo salida
    ttk.Label(frm, text='Guardar como:').grid(row=1, column=0, sticky='w', padx=(0,8), pady=4)
    ent_out = ttk.Entry(frm, textvariable=var_out_path, width=60)
    ent_out.grid(row=1, column=1, sticky='ew', pady=4)
    def on_browse_out():
        initialfile = None
        if var_in_path.get():
            nombre = os.path.splitext(os.path.basename(var_in_path.get()))[0]
            fmt = (var_out_fmt.get().strip() or 'srt').lower()
            ext_out = '.srt' if fmt == 'srt' else '.txt'
            initialfile = f"{nombre}.{var_tgt.get()}{ext_out}"
        fmt = (var_out_fmt.get().strip() or 'srt').lower()
        defext = '.srt' if fmt == 'srt' else '.txt'
        ftypes = [('SubRip (*.srt)', '*.srt'), ('Texto (*.txt)', '*.txt'), ('Todos los archivos', '*.*')]
        path = filedialog.asksaveasfilename(title='Guardar archivo como', defaultextension=defext, initialfile=initialfile, filetypes=ftypes)
        if path:
            var_out_path.set(path)
    ttk.Button(frm, text='Examinar...', command=on_browse_out).grid(row=1, column=2, padx=(8,0), pady=4)

    # Idiomas
    ttk.Label(frm, text='Idioma origen:').grid(row=2, column=0, sticky='w', padx=(0,8), pady=4)
    cb_src = ttk.Combobox(frm, textvariable=var_src, values=list(IDIOMAS.keys()), state='readonly', width=10)
    cb_src.grid(row=2, column=1, sticky='w', pady=4)

    ttk.Label(frm, text='Idioma destino:').grid(row=3, column=0, sticky='w', padx=(0,8), pady=4)
    cb_tgt = ttk.Combobox(frm, textvariable=var_tgt, values=[k for k in IDIOMAS.keys() if k != 'auto'], state='readonly', width=10)
    cb_tgt.grid(row=3, column=1, sticky='w', pady=4)

    def on_change_tgt(event=None):
        if var_in_path.get():
            nombre = os.path.splitext(os.path.basename(var_in_path.get()))[0]
            fmt = (var_out_fmt.get().strip() or 'srt').lower()
            ext_out = '.srt' if fmt == 'srt' else '.txt'
            var_out_path.set(os.path.join(os.path.dirname(var_in_path.get()), f"{nombre}.{var_tgt.get()}{ext_out}"))
    cb_tgt.bind('<<ComboboxSelected>>', on_change_tgt)

    # Formato salida
    ttk.Label(frm, text='Formato salida:').grid(row=4, column=0, sticky='w', padx=(0,8), pady=4)
    cb_fmt = ttk.Combobox(frm, textvariable=var_out_fmt, values=['srt', 'txt'], state='readonly', width=10)
    cb_fmt.grid(row=4, column=1, sticky='w', pady=4)
    def on_change_fmt(event=None):
        if var_in_path.get():
            nombre = os.path.splitext(os.path.basename(var_in_path.get()))[0]
            fmt = (var_out_fmt.get().strip() or 'srt').lower()
            ext_out = '.srt' if fmt == 'srt' else '.txt'
            var_out_path.set(os.path.join(os.path.dirname(var_in_path.get()), f"{nombre}.{var_tgt.get()}{ext_out}"))
    cb_fmt.bind('<<ComboboxSelected>>', on_change_fmt)

    # Botón traducir
    def on_translate():
        in_path = var_in_path.get().strip()
        out_path = var_out_path.get().strip()
        src = var_src.get().strip()
        tgt = var_tgt.get().strip()

        if not in_path or not os.path.isfile(in_path):
            messagebox.showerror('Error', 'Debes seleccionar un archivo .srt o .txt válido de entrada.')
            return
        if not out_path:
            messagebox.showerror('Error', 'Debes indicar dónde guardar el archivo de salida.')
            return
        if src != 'auto' and src == tgt:
            messagebox.showerror('Error', 'El idioma de origen y destino no pueden ser iguales.')
            return
        _, ext_in = os.path.splitext(in_path.lower())
        # Detección automática si procede
        if src == 'auto':
            if ext_in == '.srt':
                src = detectar_idioma_archivo(in_path)
            else:
                try:
                    with open(in_path, 'r', encoding='utf-8', errors='ignore') as f:
                        src = detectar_idioma_texto(f.read())
                except Exception:
                    src = 'en'
            var_src.set(src)
        # Cargar modelo solo si se necesita traducir
        tokenizer = model = None
        if src != tgt:
            try:
                tokenizer, model, model_name = cargar_modelo(src, tgt)
                print(f"Dispositivo: {'GPU (CUDA)' if device.type == 'cuda' else 'CPU'} | Modelo: {model_name}")
            except Exception as e:
                messagebox.showerror('Error cargando modelo', str(e))
                return
        try:
            messagebox.showinfo('Iniciando traducción', 'Esto puede tardar en el primer uso (descarga del modelo).')
        except Exception:
            pass
        try:
            out_fmt = (var_out_fmt.get().strip() or 'srt').lower()
            if out_fmt == 'srt':
                if ext_in == '.srt':
                    traducir_srt(in_path, out_path, tokenizer, model, src, tgt)
                elif ext_in == '.txt':
                    # Usuario quiere SRT desde TXT, pero ya no soportamos segmentación ni duración.
                    messagebox.showerror('No soportado', 'La salida SRT desde TXT ya no está soportada. Selecciona formato de salida TXT para preservar el texto tal cual.')
                    return
                else:
                    messagebox.showerror('Tipo no soportado', 'Solo se admiten archivos .srt o .txt.')
                    return
            elif out_fmt == 'txt':
                # Forzar extensión .txt si no la tiene
                if not out_path.lower().endswith('.txt'):
                    base, _ = os.path.splitext(out_path)
                    out_path = base + '.txt'
                    var_out_path.set(out_path)
                if ext_in == '.srt':
                    subs = pysrt.open(in_path, encoding='utf-8')
                    texto = '\n'.join(sub.text for sub in subs if sub.text)
                    if src != tgt and tokenizer is not None and model is not None:
                        texto_out = traducir_texto_largo(texto, tokenizer, model, src, tgt)
                    else:
                        texto_out = texto
                    with open(out_path, 'w', encoding='utf-8') as f:
                        f.write(texto_out)
                elif ext_in == '.txt':
                    # Traducción preservando líneas
                    if src != tgt and tokenizer is not None and model is not None:
                        traducir_txt_a_txt_preservando_lineas(in_path, out_path, tokenizer, model, src, tgt)
                    else:
                        # Solo copiar si no hay traducción
                        with open(in_path, 'r', encoding='utf-8', errors='ignore') as f:
                            contenido = f.read()
                        with open(out_path, 'w', encoding='utf-8') as f:
                            f.write(contenido)
                else:
                    messagebox.showerror('Tipo no soportado', 'Solo se admiten archivos .srt o .txt.')
                    return
            else:
                messagebox.showerror('Formato no soportado', 'Formato de salida desconocido.')
                return
            # Aviso sonoro y visual al completar
            try:
                if winsound is not None:
                    winsound.MessageBeep(winsound.MB_ICONASTERISK)
                else:
                    print('\a')  # campana estándar
            except Exception:
                pass
            messagebox.showinfo('Listo', f'Traducción completada. Guardado en:\n{out_path}')
        except Exception as e:
            try:
                if winsound is not None:
                    winsound.MessageBeep(winsound.MB_ICONHAND)
                else:
                    print('\a')
            except Exception:
                pass
            messagebox.showerror('Error durante la traducción', str(e))

    btn = ttk.Button(frm, text='Traducir', command=on_translate)
    btn.grid(row=5, column=1, sticky='w', pady=(8,0))

    # Expandir entry principal
    frm.columnconfigure(1, weight=1)
    root.mainloop()


if __name__ == '__main__':
    app_gui()