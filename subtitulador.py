import pysrt
from transformers import MarianMTModel, MarianTokenizer
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
from tkinter import Tk, filedialog, messagebox
from tkinter import ttk
import os
import torch
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
    """Abre un diálogo para seleccionar el archivo .srt de entrada."""
    root = Tk()
    root.withdraw()
    # Traer ventana al frente en Windows
    try:
        root.call('wm', 'attributes', '.', '-topmost', True)
    except Exception:
        pass
    ruta = filedialog.askopenfilename(
        title='Selecciona el archivo SRT a traducir',
        filetypes=[('SubRip (*.srt)', '*.srt'), ('Todos los archivos', '*.*')]
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

    # Valores iniciales
    var_src.set('en')
    var_tgt.set('es')

    # Layout
    frm = ttk.Frame(root, padding=12)
    frm.grid(row=0, column=0, sticky='nsew')
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    # Fila archivo entrada
    ttk.Label(frm, text='Archivo SRT:').grid(row=0, column=0, sticky='w', padx=(0,8), pady=4)
    ent_in = ttk.Entry(frm, textvariable=var_in_path, width=60)
    ent_in.grid(row=0, column=1, sticky='ew', pady=4)
    def on_browse_in():
        path = filedialog.askopenfilename(title='Selecciona el archivo SRT', filetypes=[('SubRip (*.srt)', '*.srt'), ('Todos los archivos', '*.*')])
        if path:
            var_in_path.set(path)
            # Detectar idioma
            detected = detectar_idioma_archivo(path)
            var_src.set(detected)
            # Sugerir salida
            base = os.path.basename(path)
            nombre, _ = os.path.splitext(base)
            var_out_path.set(os.path.join(os.path.dirname(path), f"{nombre}.{var_tgt.get()}.srt"))
    ttk.Button(frm, text='Examinar...', command=on_browse_in).grid(row=0, column=2, padx=(8,0), pady=4)

    # Fila archivo salida
    ttk.Label(frm, text='Guardar como:').grid(row=1, column=0, sticky='w', padx=(0,8), pady=4)
    ent_out = ttk.Entry(frm, textvariable=var_out_path, width=60)
    ent_out.grid(row=1, column=1, sticky='ew', pady=4)
    def on_browse_out():
        initialfile = None
        if var_in_path.get():
            nombre = os.path.splitext(os.path.basename(var_in_path.get()))[0]
            initialfile = f"{nombre}.{var_tgt.get()}.srt"
        path = filedialog.asksaveasfilename(title='Guardar subtítulos como', defaultextension='.srt', initialfile=initialfile, filetypes=[('SubRip (*.srt)', '*.srt'), ('Todos los archivos', '*.*')])
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
            var_out_path.set(os.path.join(os.path.dirname(var_in_path.get()), f"{nombre}.{var_tgt.get()}.srt"))
    cb_tgt.bind('<<ComboboxSelected>>', on_change_tgt)

    # Botón traducir
    def on_translate():
        in_path = var_in_path.get().strip()
        out_path = var_out_path.get().strip()
        src = var_src.get().strip()
        tgt = var_tgt.get().strip()

        if not in_path or not os.path.isfile(in_path):
            messagebox.showerror('Error', 'Debes seleccionar un archivo .srt válido de entrada.')
            return
        if not out_path:
            messagebox.showerror('Error', 'Debes indicar dónde guardar el archivo de salida.')
            return
        if src != 'auto' and src == tgt:
            messagebox.showerror('Error', 'El idioma de origen y destino no pueden ser iguales.')
            return
        # Detección automática si procede
        if src == 'auto':
            src = detectar_idioma_archivo(in_path)
            var_src.set(src)
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
            traducir_srt(in_path, out_path, tokenizer, model, src, tgt)
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
    btn.grid(row=4, column=1, sticky='w', pady=(8,0))

    # Expandir entry principal
    frm.columnconfigure(1, weight=1)
    root.mainloop()


if __name__ == '__main__':
    app_gui()