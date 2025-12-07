"""
Subtitulador con Interfaz Gráfica Moderna
=========================================
Versión con GUI mejorada usando CustomTkinter para una apariencia moderna.
Traduce archivos SRT y TXT usando el modelo M2M100 de Facebook.
"""

import subprocess
import sys
import os

# Obtener directorio del script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(SCRIPT_DIR, 'venv')

def obtener_python_venv():
    """Obtiene la ruta del ejecutable Python del venv."""
    if sys.platform == 'win32':
        return os.path.join(VENV_DIR, 'Scripts', 'python.exe')
    return os.path.join(VENV_DIR, 'bin', 'python')

def obtener_pip_venv():
    """Obtiene la ruta del pip del venv."""
    if sys.platform == 'win32':
        return os.path.join(VENV_DIR, 'Scripts', 'pip.exe')
    return os.path.join(VENV_DIR, 'bin', 'pip')

def estamos_en_venv():
    """Verifica si estamos ejecutando dentro del venv."""
    return sys.prefix == VENV_DIR or sys.executable == obtener_python_venv()

def crear_venv_si_no_existe():
    """Crea el entorno virtual si no existe."""
    if not os.path.exists(VENV_DIR):
        print("📁 Creando entorno virtual...")
        subprocess.check_call([sys.executable, '-m', 'venv', VENV_DIR])
        print("✅ Entorno virtual creado\n")
        return True
    return False

def detectar_gpu_nvidia():
    """Detecta si hay una GPU NVIDIA disponible sin necesitar PyTorch."""
    try:
        # Intentar ejecutar nvidia-smi
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split('\n')[0]
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass
    return None

def reiniciar_en_venv():
    """Reinicia el script dentro del venv."""
    python_venv = obtener_python_venv()
    if os.path.exists(python_venv):
        print(f"🔄 Reiniciando en entorno virtual...\n")
        os.execv(python_venv, [python_venv] + sys.argv)
    else:
        print("❌ Error: No se encontró Python en el venv")
        sys.exit(1)

def verificar_e_instalar_dependencias():
    """Verifica e instala las dependencias necesarias en el venv."""
    
    # Primero, asegurarnos de que existe el venv
    venv_nuevo = crear_venv_si_no_existe()
    
    # Si no estamos en el venv, reiniciar dentro de él
    if not estamos_en_venv():
        if venv_nuevo:
            print("📦 Preparando entorno virtual por primera vez...")
        reiniciar_en_venv()
        return
    
    # Detectar GPU antes de instalar nada
    gpu_nombre = detectar_gpu_nvidia()
    hay_gpu = gpu_nombre is not None
    
    if hay_gpu:
        print(f"🎮 GPU detectada: {gpu_nombre}")
    else:
        print("💻 No se detectó GPU NVIDIA, se usará CPU")
    
    # Lista de paquetes requeridos
    dependencias = [
        ('customtkinter', 'customtkinter'),
        ('transformers', 'transformers'),
        ('pysrt', 'pysrt'),
        ('langdetect', 'langdetect'),
        ('sentencepiece', 'sentencepiece'),
    ]
    
    faltantes = []
    torch_instalado = False
    torch_tiene_cuda = False
    
    print("\n🔍 Verificando dependencias...")
    
    # Verificar torch primero
    try:
        import torch
        torch_instalado = True
        torch_tiene_cuda = torch.cuda.is_available()
        if torch_tiene_cuda:
            print(f"  ✅ torch (CUDA: {torch.cuda.get_device_name(0)})")
        else:
            print(f"  ✅ torch (CPU)")
    except ImportError:
        print(f"  ❌ torch - No instalado")
        faltantes.append('torch')
    
    # Verificar otras dependencias
    for nombre_pip, nombre_import in dependencias:
        try:
            __import__(nombre_import)
            print(f"  ✅ {nombre_pip}")
        except ImportError:
            print(f"  ❌ {nombre_pip} - No instalado")
            faltantes.append(nombre_pip)
    
    pip_exe = obtener_pip_venv()
    necesita_reinicio = False
    
    # Instalar dependencias faltantes
    if faltantes:
        print(f"\n📦 Instalando {len(faltantes)} paquete(s) en el entorno virtual...")
        
        for paquete in faltantes:
            print(f"  Instalando {paquete}...")
            try:
                if paquete == 'torch':
                    if hay_gpu:
                        # Instalar PyTorch con CUDA
                        print("  (Con soporte GPU - esto puede tardar...)")
                        subprocess.check_call([
                            pip_exe, 'install',
                            'torch', 'torchvision', 'torchaudio',
                            '--index-url', 'https://download.pytorch.org/whl/cu124'
                        ])
                    else:
                        # Instalar PyTorch solo CPU (más ligero)
                        print("  (Solo CPU)")
                        subprocess.check_call([
                            pip_exe, 'install',
                            'torch', 'torchvision', 'torchaudio',
                            '--index-url', 'https://download.pytorch.org/whl/cpu'
                        ])
                else:
                    subprocess.check_call([pip_exe, 'install', paquete])
                print(f"  ✅ {paquete} instalado")
            except subprocess.CalledProcessError as e:
                print(f"  ❌ Error instalando {paquete}: {e}")
                input("\nPresiona Enter para salir...")
                sys.exit(1)
        
        necesita_reinicio = True
    
    # Si hay GPU pero torch no tiene CUDA, ofrecer reinstalar
    if hay_gpu and torch_instalado and not torch_tiene_cuda:
        print("\n⚠️  Tienes GPU pero PyTorch está instalado sin soporte CUDA")
        respuesta = input("¿Deseas reinstalar PyTorch con soporte GPU? (s/n): ").strip().lower()
        if respuesta == 's':
            print("\n📦 Reinstalando PyTorch con CUDA 12.4...")
            subprocess.check_call([
                pip_exe, 'install', '--upgrade', '--force-reinstall',
                'torch', 'torchvision', 'torchaudio',
                '--index-url', 'https://download.pytorch.org/whl/cu124'
            ])
            necesita_reinicio = True
    
    if necesita_reinicio:
        print("\n✅ Instalación completada. Reiniciando...")
        reiniciar_en_venv()
    
    print("\n✅ Todas las dependencias están instaladas")
    print(f"📂 Entorno virtual: {VENV_DIR}\n")

# Verificar dependencias antes de importar
verificar_e_instalar_dependencias()

# Ahora importamos todo
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import torch
import re
import pysrt
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer

try:
    import winsound
except Exception:
    winsound = None

# Configuración de tema
ctk.set_appearance_mode("dark")  # "dark", "light", "system"
ctk.set_default_color_theme("blue")

# Verificar disponibilidad de CUDA
CUDA_DISPONIBLE = torch.cuda.is_available()
GPU_NOMBRE = torch.cuda.get_device_name(0) if CUDA_DISPONIBLE else None

# Dispositivo por defecto (se puede cambiar en la UI)
device = torch.device('cuda' if CUDA_DISPONIBLE else 'cpu')

# Idiomas soportados
IDIOMAS = {
    'auto': '🔍 Detectar automáticamente',
    'en': '🇬🇧 Inglés',
    'es': '🇪🇸 Español',
    'de': '🇩🇪 Alemán',
    'ru': '🇷🇺 Ruso',
    'fr': '🇫🇷 Francés',
    'it': '🇮🇹 Italiano',
    'pt': '🇵🇹 Portugués',
    'nl': '🇳🇱 Neerlandés',
    'pl': '🇵🇱 Polaco',
    'sv': '🇸🇪 Sueco',
    'no': '🇳🇴 Noruego',
    'da': '🇩🇰 Danés',
    'fi': '🇫🇮 Finlandés',
    'tr': '🇹🇷 Turco',
    'el': '🇬🇷 Griego',
    'ro': '🇷🇴 Rumano',
    'cs': '🇨🇿 Checo',
    'uk': '🇺🇦 Ucraniano',
    'hu': '🇭🇺 Húngaro',
    'bg': '🇧🇬 Búlgaro',
    'ar': '🇸🇦 Árabe',
    'he': '🇮🇱 Hebreo',
    'hi': '🇮🇳 Hindi',
    'bn': '🇧🇩 Bengalí',
    'id': '🇮🇩 Indonesio',
    'ms': '🇲🇾 Malayo',
    'vi': '🇻🇳 Vietnamita',
    'th': '🇹🇭 Tailandés',
    'zh': '🇨🇳 Chino',
    'ja': '🇯🇵 Japonés',
    'ko': '🇰🇷 Coreano',
}

# Variables globales del modelo
_m2m_tokenizer = None
_m2m_model = None


class SubtituladorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuración de la ventana principal
        self.title("🎬 Subtitulador Traductor")
        self.geometry("800x650")
        self.minsize(700, 600)
        
        # Variables
        self.archivo_entrada = ctk.StringVar()
        self.archivo_salida = ctk.StringVar()
        self.idioma_origen = ctk.StringVar(value='auto')
        self.idioma_destino = ctk.StringVar(value='es')
        self.formato_salida = ctk.StringVar(value='srt')
        self.dispositivo_seleccionado = ctk.StringVar(value='cuda' if CUDA_DISPONIBLE else 'cpu')
        self.progreso = ctk.DoubleVar(value=0)
        self.traduciendo = False
        
        # Crear interfaz
        self.crear_interfaz()
        
    def crear_interfaz(self):
        # Frame principal con padding
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # ========== ENCABEZADO ==========
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        titulo = ctk.CTkLabel(
            header_frame, 
            text="🎬 Subtitulador Traductor",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        titulo.pack()
        
        subtitulo = ctk.CTkLabel(
            header_frame,
            text="Traduce subtítulos y archivos de texto con IA",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitulo.pack()
        
        # ========== SELECTOR DE DISPOSITIVO ==========
        dispositivo_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        dispositivo_frame.pack(pady=(10, 0))
        
        # Solo mostrar selector si hay GPU disponible
        if CUDA_DISPONIBLE:
            ctk.CTkLabel(
                dispositivo_frame,
                text="Procesador:",
                font=ctk.CTkFont(size=12)
            ).pack(side="left", padx=(0, 10))
            
            # Opciones de dispositivo (GPU y CPU)
            opciones_dispositivo = [f"🎮 GPU ({GPU_NOMBRE})", "💻 CPU"]
            
            self.combo_dispositivo = ctk.CTkComboBox(
                dispositivo_frame,
                values=opciones_dispositivo,
                width=300,
                height=30,
                font=ctk.CTkFont(size=12),
                command=self.on_dispositivo_change
            )
            self.combo_dispositivo.pack(side="left")
            self.combo_dispositivo.set(f"🎮 GPU ({GPU_NOMBRE})")
            
            # Label de estado del dispositivo
            self.label_dispositivo_estado = ctk.CTkLabel(
                dispositivo_frame,
                text="✅",
                font=ctk.CTkFont(size=14),
                text_color="#4CAF50"
            )
            self.label_dispositivo_estado.pack(side="left", padx=(10, 0))
        else:
            # Sin GPU, solo mostrar info
            self.combo_dispositivo = None
            self.label_dispositivo_estado = ctk.CTkLabel(
                dispositivo_frame,
                text="💻 Procesador: CPU",
                font=ctk.CTkFont(size=12),
                text_color="#FF9800"
            )
            self.label_dispositivo_estado.pack()
        
        # ========== SECCIÓN ARCHIVO ENTRADA ==========
        entrada_frame = ctk.CTkFrame(main_frame)
        entrada_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            entrada_frame,
            text="📂 Archivo de entrada",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        entrada_inner = ctk.CTkFrame(entrada_frame, fg_color="transparent")
        entrada_inner.pack(fill="x", padx=15, pady=(0, 15))
        
        self.entry_entrada = ctk.CTkEntry(
            entrada_inner,
            textvariable=self.archivo_entrada,
            placeholder_text="Selecciona un archivo .srt o .txt",
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.entry_entrada.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        btn_examinar_entrada = ctk.CTkButton(
            entrada_inner,
            text="📁 Examinar",
            command=self.seleccionar_entrada,
            width=120,
            height=40,
            font=ctk.CTkFont(size=13)
        )
        btn_examinar_entrada.pack(side="right")
        
        # ========== SECCIÓN ARCHIVO SALIDA ==========
        salida_frame = ctk.CTkFrame(main_frame)
        salida_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            salida_frame,
            text="💾 Archivo de salida",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        salida_inner = ctk.CTkFrame(salida_frame, fg_color="transparent")
        salida_inner.pack(fill="x", padx=15, pady=(0, 15))
        
        self.entry_salida = ctk.CTkEntry(
            salida_inner,
            textvariable=self.archivo_salida,
            placeholder_text="Ubicación del archivo traducido",
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.entry_salida.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        btn_examinar_salida = ctk.CTkButton(
            salida_inner,
            text="📁 Examinar",
            command=self.seleccionar_salida,
            width=120,
            height=40,
            font=ctk.CTkFont(size=13)
        )
        btn_examinar_salida.pack(side="right")
        
        # ========== SECCIÓN OPCIONES ==========
        opciones_frame = ctk.CTkFrame(main_frame)
        opciones_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            opciones_frame,
            text="⚙️ Opciones de traducción",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        # Grid de opciones
        opciones_grid = ctk.CTkFrame(opciones_frame, fg_color="transparent")
        opciones_grid.pack(fill="x", padx=15, pady=(0, 15))
        opciones_grid.columnconfigure((0, 1, 2), weight=1)
        
        # Idioma origen
        origen_frame = ctk.CTkFrame(opciones_grid, fg_color="transparent")
        origen_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            origen_frame,
            text="Idioma origen:",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w")
        
        self.combo_origen = ctk.CTkComboBox(
            origen_frame,
            values=list(IDIOMAS.values()),
            variable=self.idioma_origen,
            width=200,
            height=35,
            font=ctk.CTkFont(size=12),
            command=self.on_idioma_change
        )
        self.combo_origen.pack(fill="x", pady=(5, 0))
        self.combo_origen.set(IDIOMAS['auto'])
        
        # Idioma destino
        destino_frame = ctk.CTkFrame(opciones_grid, fg_color="transparent")
        destino_frame.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            destino_frame,
            text="Idioma destino:",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w")
        
        idiomas_destino = [v for k, v in IDIOMAS.items() if k != 'auto']
        self.combo_destino = ctk.CTkComboBox(
            destino_frame,
            values=idiomas_destino,
            variable=self.idioma_destino,
            width=200,
            height=35,
            font=ctk.CTkFont(size=12),
            command=self.on_idioma_change
        )
        self.combo_destino.pack(fill="x", pady=(5, 0))
        self.combo_destino.set(IDIOMAS['es'])
        
        # Formato salida
        formato_frame = ctk.CTkFrame(opciones_grid, fg_color="transparent")
        formato_frame.grid(row=0, column=2, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            formato_frame,
            text="Formato salida:",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w")
        
        self.combo_formato = ctk.CTkComboBox(
            formato_frame,
            values=["📺 SRT (Subtítulos)", "📄 TXT (Texto plano)"],
            variable=self.formato_salida,
            width=200,
            height=35,
            font=ctk.CTkFont(size=12),
            command=self.on_formato_change
        )
        self.combo_formato.pack(fill="x", pady=(5, 0))
        self.combo_formato.set("📺 SRT (Subtítulos)")
        
        # ========== BARRA DE PROGRESO ==========
        progreso_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        progreso_frame.pack(fill="x", pady=10)
        
        self.label_estado = ctk.CTkLabel(
            progreso_frame,
            text="⏳ Listo para traducir",
            font=ctk.CTkFont(size=13)
        )
        self.label_estado.pack(anchor="w", padx=5)
        
        self.barra_progreso = ctk.CTkProgressBar(progreso_frame, height=15)
        self.barra_progreso.pack(fill="x", pady=(5, 0))
        self.barra_progreso.set(0)
        
        # ========== BOTONES DE ACCIÓN ==========
        botones_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        botones_frame.pack(fill="x", pady=20)
        
        self.btn_traducir = ctk.CTkButton(
            botones_frame,
            text="🚀 Traducir",
            command=self.iniciar_traduccion,
            height=50,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#4CAF50",
            hover_color="#388E3C"
        )
        self.btn_traducir.pack(fill="x", pady=5)
        
        # Frame para botones secundarios
        btns_secundarios = ctk.CTkFrame(botones_frame, fg_color="transparent")
        btns_secundarios.pack(fill="x", pady=(10, 0))
        
        btn_tema = ctk.CTkButton(
            btns_secundarios,
            text="🌙 Cambiar tema",
            command=self.cambiar_tema,
            width=150,
            height=35,
            fg_color="gray30",
            hover_color="gray40"
        )
        btn_tema.pack(side="left", padx=(0, 10))
        
        btn_limpiar = ctk.CTkButton(
            btns_secundarios,
            text="🗑️ Limpiar",
            command=self.limpiar_campos,
            width=150,
            height=35,
            fg_color="gray30",
            hover_color="gray40"
        )
        btn_limpiar.pack(side="left")
        
        # ========== LOG DE ACTIVIDAD ==========
        log_frame = ctk.CTkFrame(main_frame)
        log_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        ctk.CTkLabel(
            log_frame,
            text="📋 Registro de actividad",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.log_text = ctk.CTkTextbox(
            log_frame,
            height=100,
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.log_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.log("Aplicación iniciada. Selecciona un archivo para comenzar.")
        
    def log(self, mensaje: str):
        """Añade un mensaje al log"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {mensaje}\n")
        self.log_text.see("end")
        
    def obtener_codigo_idioma(self, texto_completo: str) -> str:
        """Obtiene el código de idioma desde el texto del combobox"""
        for codigo, nombre in IDIOMAS.items():
            if nombre == texto_completo:
                return codigo
        return 'en'
        
    def seleccionar_entrada(self):
        """Abre diálogo para seleccionar archivo de entrada"""
        ruta = filedialog.askopenfilename(
            title='Selecciona el archivo a traducir',
            filetypes=[
                ('Subtítulos SRT', '*.srt'),
                ('Archivos de texto', '*.txt'),
                ('Todos los archivos', '*.*')
            ]
        )
        if ruta:
            self.archivo_entrada.set(ruta)
            self.log(f"Archivo seleccionado: {os.path.basename(ruta)}")
            
            # Detectar idioma
            _, ext = os.path.splitext(ruta.lower())
            idioma_detectado = self.detectar_idioma(ruta, ext)
            if idioma_detectado in IDIOMAS:
                self.combo_origen.set(IDIOMAS[idioma_detectado])
                self.log(f"Idioma detectado: {IDIOMAS.get(idioma_detectado, idioma_detectado)}")
            
            # Sugerir archivo de salida
            self.actualizar_ruta_salida()
            
    def seleccionar_salida(self):
        """Abre diálogo para seleccionar archivo de salida"""
        formato = self.combo_formato.get()
        if "SRT" in formato:
            ext = '.srt'
            ftypes = [('Subtítulos SRT', '*.srt'), ('Todos los archivos', '*.*')]
        else:
            ext = '.txt'
            ftypes = [('Archivos de texto', '*.txt'), ('Todos los archivos', '*.*')]
            
        nombre_inicial = None
        if self.archivo_entrada.get():
            nombre = os.path.splitext(os.path.basename(self.archivo_entrada.get()))[0]
            idioma_dest = self.obtener_codigo_idioma(self.combo_destino.get())
            nombre_inicial = f"{nombre}.{idioma_dest}{ext}"
            
        ruta = filedialog.asksaveasfilename(
            title='Guardar archivo traducido como',
            defaultextension=ext,
            initialfile=nombre_inicial,
            filetypes=ftypes
        )
        if ruta:
            self.archivo_salida.set(ruta)
            self.log(f"Archivo de salida: {os.path.basename(ruta)}")
            
    def actualizar_ruta_salida(self):
        """Actualiza la ruta de salida basándose en la entrada y opciones"""
        if not self.archivo_entrada.get():
            return
            
        ruta_entrada = self.archivo_entrada.get()
        directorio = os.path.dirname(ruta_entrada)
        nombre = os.path.splitext(os.path.basename(ruta_entrada))[0]
        idioma_dest = self.obtener_codigo_idioma(self.combo_destino.get())
        
        formato = self.combo_formato.get()
        ext = '.srt' if "SRT" in formato else '.txt'
        
        nueva_ruta = os.path.join(directorio, f"{nombre}.{idioma_dest}{ext}")
        self.archivo_salida.set(nueva_ruta)
        
    def on_idioma_change(self, *args):
        """Callback cuando cambia el idioma"""
        self.actualizar_ruta_salida()
        
    def on_formato_change(self, *args):
        """Callback cuando cambia el formato"""
        self.actualizar_ruta_salida()
        
    def on_dispositivo_change(self, *args):
        """Callback cuando cambia el dispositivo"""
        global _m2m_model, _m2m_tokenizer
        
        # Si no hay combo (solo CPU), no hacer nada
        if self.combo_dispositivo is None:
            return
            
        seleccion = self.combo_dispositivo.get()
        
        if "GPU" in seleccion:
            self.dispositivo_seleccionado.set('cuda')
            self.label_dispositivo_estado.configure(text="✅", text_color="#4CAF50")
            self.log("Dispositivo cambiado a: GPU (CUDA)")
        else:
            self.dispositivo_seleccionado.set('cpu')
            self.label_dispositivo_estado.configure(text="✅", text_color="#FF9800")
            self.log("Dispositivo cambiado a: CPU")
        
        # Limpiar modelo cargado para forzar recarga en nuevo dispositivo
        if _m2m_model is not None:
            _m2m_model = None
            _m2m_tokenizer = None
            self.log("Modelo descargado. Se recargará en el nuevo dispositivo.")
        
    def detectar_idioma(self, archivo: str, extension: str) -> str:
        """Detecta el idioma del archivo"""
        try:
            if extension == '.srt':
                subs = pysrt.open(archivo, encoding='utf-8')
                muestras = []
                for sub in subs:
                    if sub.text and sub.text.strip():
                        muestras.append(sub.text)
                    if len(muestras) >= 50:
                        break
                muestra = "\n".join(muestras)
            else:
                with open(archivo, 'r', encoding='utf-8', errors='ignore') as f:
                    muestra = f.read(5000)
                    
            try:
                from langdetect import detect
                code = detect(muestra)
                if code.startswith('zh'):
                    return 'zh'
                return code
            except Exception:
                pass
                
            # Heurísticas
            if any('\u0400' <= ch <= '\u04FF' for ch in muestra):
                return 'ru'
            if any(ch in 'äöüÄÖÜß' for ch in muestra):
                return 'de'
            if any(ch in 'áéíóúÁÉÍÓÚñÑ¿¡' for ch in muestra):
                return 'es'
            return 'en'
        except Exception:
            return 'en'
            
    def cambiar_tema(self):
        """Alterna entre tema claro y oscuro"""
        modo_actual = ctk.get_appearance_mode()
        nuevo_modo = "light" if modo_actual == "Dark" else "dark"
        ctk.set_appearance_mode(nuevo_modo)
        self.log(f"Tema cambiado a: {nuevo_modo}")
        
    def limpiar_campos(self):
        """Limpia todos los campos"""
        self.archivo_entrada.set("")
        self.archivo_salida.set("")
        self.combo_origen.set(IDIOMAS['auto'])
        self.combo_destino.set(IDIOMAS['es'])
        self.combo_formato.set("📺 SRT (Subtítulos)")
        self.barra_progreso.set(0)
        self.label_estado.configure(text="⏳ Listo para traducir")
        self.log("Campos limpiados")
        
    def actualizar_estado(self, texto: str, progreso: float = None):
        """Actualiza el estado y progreso desde cualquier hilo"""
        self.label_estado.configure(text=texto)
        if progreso is not None:
            self.barra_progreso.set(progreso)
        self.update_idletasks()
        
    def iniciar_traduccion(self):
        """Inicia el proceso de traducción en un hilo separado"""
        if self.traduciendo:
            messagebox.showwarning("Advertencia", "Ya hay una traducción en progreso")
            return
            
        # Validaciones
        ruta_entrada = self.archivo_entrada.get().strip()
        ruta_salida = self.archivo_salida.get().strip()
        
        if not ruta_entrada or not os.path.isfile(ruta_entrada):
            messagebox.showerror("Error", "Debes seleccionar un archivo .srt o .txt válido")
            return
            
        if not ruta_salida:
            messagebox.showerror("Error", "Debes indicar dónde guardar el archivo de salida")
            return
            
        src = self.obtener_codigo_idioma(self.combo_origen.get())
        tgt = self.obtener_codigo_idioma(self.combo_destino.get())
        
        if src == 'auto':
            _, ext = os.path.splitext(ruta_entrada.lower())
            src = self.detectar_idioma(ruta_entrada, ext)
            self.combo_origen.set(IDIOMAS.get(src, IDIOMAS['en']))
            self.log(f"Idioma detectado: {IDIOMAS.get(src, src)}")
            
        if src == tgt:
            messagebox.showerror("Error", "El idioma de origen y destino no pueden ser iguales")
            return
            
        # Deshabilitar botón
        self.btn_traducir.configure(state="disabled", text="⏳ Traduciendo...")
        self.traduciendo = True
        
        # Iniciar hilo
        threading.Thread(
            target=self.proceso_traduccion,
            args=(ruta_entrada, ruta_salida, src, tgt),
            daemon=True
        ).start()
        
    def proceso_traduccion(self, ruta_entrada: str, ruta_salida: str, src: str, tgt: str):
        """Proceso de traducción ejecutado en hilo separado"""
        global _m2m_tokenizer, _m2m_model
        
        try:
            # Obtener dispositivo seleccionado
            dispositivo_str = self.dispositivo_seleccionado.get()
            current_device = torch.device(dispositivo_str)
            
            # Cargar modelo
            self.after(0, lambda: self.actualizar_estado("🔄 Cargando modelo de traducción...", 0.1))
            self.after(0, lambda d=dispositivo_str: self.log(f"Cargando modelo M2M100 en {d.upper()}..."))
            
            model_name = 'facebook/m2m100_418M'
            if _m2m_tokenizer is None or _m2m_model is None:
                _m2m_tokenizer = M2M100Tokenizer.from_pretrained(model_name)
                _m2m_model = M2M100ForConditionalGeneration.from_pretrained(model_name)
                _m2m_model = _m2m_model.to(current_device)
                _m2m_model.eval()
            else:
                # Mover modelo al dispositivo correcto si ya está cargado
                _m2m_model = _m2m_model.to(current_device)
                
            self.after(0, lambda d=dispositivo_str: self.log(f"Modelo cargado en {d.upper()}"))
            self.after(0, lambda: self.actualizar_estado("📝 Procesando archivo...", 0.2))
            
            # Guardar referencia al dispositivo para las funciones de traducción
            self.current_device = current_device
            
            _, ext_in = os.path.splitext(ruta_entrada.lower())
            formato = self.combo_formato.get()
            es_srt_salida = "SRT" in formato
            
            if es_srt_salida:
                if ext_in == '.srt':
                    self.traducir_srt(ruta_entrada, ruta_salida, _m2m_tokenizer, _m2m_model, src, tgt)
                else:
                    raise Exception("La salida SRT desde TXT no está soportada. Usa formato TXT.")
            else:
                # Asegurar extensión .txt
                if not ruta_salida.lower().endswith('.txt'):
                    ruta_salida = os.path.splitext(ruta_salida)[0] + '.txt'
                    
                if ext_in == '.srt':
                    self.traducir_srt_a_txt(ruta_entrada, ruta_salida, _m2m_tokenizer, _m2m_model, src, tgt)
                else:
                    self.traducir_txt(ruta_entrada, ruta_salida, _m2m_tokenizer, _m2m_model, src, tgt)
                    
            # Completado
            self.after(0, lambda: self.actualizar_estado("✅ ¡Traducción completada!", 1.0))
            self.after(0, lambda: self.log(f"Archivo guardado: {ruta_salida}"))
            
            # Sonido de éxito
            try:
                if winsound:
                    winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass
                
            self.after(0, lambda: messagebox.showinfo(
                "¡Éxito!",
                f"Traducción completada.\n\nArchivo guardado en:\n{ruta_salida}"
            ))
            
        except Exception as e:
            self.after(0, lambda: self.actualizar_estado(f"❌ Error: {str(e)[:50]}...", 0))
            self.after(0, lambda: self.log(f"ERROR: {str(e)}"))
            try:
                if winsound:
                    winsound.MessageBeep(winsound.MB_ICONHAND)
            except Exception:
                pass
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
            
        finally:
            self.traduciendo = False
            self.after(0, lambda: self.btn_traducir.configure(state="normal", text="🚀 Traducir"))
            
    def traducir_texto(self, texto: str, tokenizer, model, src: str, tgt: str) -> str:
        """Traduce un texto corto"""
        current_device = getattr(self, 'current_device', torch.device('cpu'))
        tokenizer.src_lang = src
        inputs = tokenizer(texto, return_tensors='pt', padding=True, truncation=True)
        inputs = {k: v.to(current_device) for k, v in inputs.items()}
        forced_bos = tokenizer.get_lang_id(tgt)
        with torch.no_grad():
            traduccion = model.generate(**inputs, forced_bos_token_id=forced_bos, max_length=512)
        return tokenizer.batch_decode(traduccion, skip_special_tokens=True)[0]
        
    def traducir_srt(self, entrada: str, salida: str, tokenizer, model, src: str, tgt: str):
        """Traduce un archivo SRT"""
        subs = pysrt.open(entrada, encoding='utf-8')
        total = len(subs)
        
        for i, sub in enumerate(subs):
            try:
                sub.text = self.traducir_texto(sub.text, tokenizer, model, src, tgt)
            except Exception as e:
                self.after(0, lambda e=e: self.log(f"Advertencia: {str(e)[:50]}"))
                
            # Actualizar progreso
            progreso = 0.2 + (0.8 * (i + 1) / total)
            self.after(0, lambda p=progreso, i=i, t=total: 
                self.actualizar_estado(f"🔄 Traduciendo subtítulo {i+1}/{t}...", p))
                
        subs.save(salida, encoding='utf-8')
        
    def traducir_srt_a_txt(self, entrada: str, salida: str, tokenizer, model, src: str, tgt: str):
        """Extrae texto de SRT, traduce y guarda como TXT"""
        subs = pysrt.open(entrada, encoding='utf-8')
        lineas = []
        total = len(subs)
        
        for i, sub in enumerate(subs):
            try:
                texto_traducido = self.traducir_texto(sub.text, tokenizer, model, src, tgt)
                lineas.append(texto_traducido)
            except Exception:
                lineas.append(sub.text)
                
            progreso = 0.2 + (0.8 * (i + 1) / total)
            self.after(0, lambda p=progreso, i=i, t=total:
                self.actualizar_estado(f"🔄 Traduciendo {i+1}/{t}...", p))
                
        with open(salida, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lineas))
            
    def traducir_txt(self, entrada: str, salida: str, tokenizer, model, src: str, tgt: str):
        """Traduce un archivo TXT preservando saltos de línea"""
        with open(entrada, 'r', encoding='utf-8', errors='ignore') as f:
            lineas = f.read().splitlines(keepends=True)
            
        resultado = []
        total = len(lineas)
        
        for i, linea in enumerate(lineas):
            # Preservar fin de línea
            if linea.endswith('\r\n'):
                contenido, fin = linea[:-2], '\r\n'
            elif linea.endswith('\n'):
                contenido, fin = linea[:-1], '\n'
            else:
                contenido, fin = linea, ''
                
            if contenido.strip():
                try:
                    traducido = self.traducir_texto(contenido, tokenizer, model, src, tgt)
                except Exception:
                    traducido = contenido
            else:
                traducido = contenido
                
            resultado.append(traducido + fin)
            
            progreso = 0.2 + (0.8 * (i + 1) / total)
            self.after(0, lambda p=progreso, i=i, t=total:
                self.actualizar_estado(f"🔄 Traduciendo línea {i+1}/{t}...", p))
                
        with open(salida, 'w', encoding='utf-8') as f:
            f.write(''.join(resultado))


def main():
    app = SubtituladorApp()
    app.mainloop()


if __name__ == '__main__':
    main()
