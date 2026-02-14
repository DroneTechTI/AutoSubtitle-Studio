"""
Main GUI window for Subtitle Generator
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

try:
    from gui.batch_processor import BatchProcessorWindow
    from gui.preview_window import SubtitlePreviewWindow
    from gui.video_tools_window import VideoToolsWindow
    from gui.log_viewer import LogViewerWindow
    from gui.multilang_window import MultiLanguageWindow
    from gui.opensubtitles_selector import OpenSubtitlesSelectorWindow
    from gui.tooltip import create_tooltip
    from utils.preferences_manager import PreferencesManager
    from utils.i18n import get_i18n, t
    from services.translation_service import TranslationService
except ImportError:
    # For direct execution
    pass


class SubtitleGeneratorGUI:
    """Main application window"""
    
    def __init__(self, app_controller):
        self.controller = app_controller
        self.i18n = get_i18n()
        self.root = tk.Tk()
        self.root.title(f"{self.controller.config.APP_NAME} v{self.controller.config.APP_VERSION}")
        
        # Create menu bar
        self._create_menu()
        
        # Load preferences
        try:
            self.preferences = PreferencesManager()
            saved_geometry = self.preferences.get('window_geometry', self.controller.config.WINDOW_SIZE)
            self.root.geometry(saved_geometry)
        except:
            self.preferences = None
            self.root.geometry(self.controller.config.WINDOW_SIZE)

        # Set minimum window size to ensure all controls are visible
        self.root.minsize(1000, 750)  # Reduced from 850 to prevent button hiding on small screens

        # Make window resizable
        self.root.resizable(True, True)

        # Variables
        self.video_path = tk.StringVar()
        self.mode = tk.StringVar(value="auto")
        
        # Load preferences or use defaults
        default_lang = self.preferences.get('language', self.controller.config.DEFAULT_LANGUAGE) if self.preferences else self.controller.config.DEFAULT_LANGUAGE
        default_model = self.preferences.get('model', self.controller.config.DEFAULT_WHISPER_MODEL) if self.preferences else self.controller.config.DEFAULT_WHISPER_MODEL
        default_format = self.preferences.get('format', self.controller.config.DEFAULT_SUBTITLE_FORMAT) if self.preferences else self.controller.config.DEFAULT_SUBTITLE_FORMAT
        
        self.language = tk.StringVar(value=default_lang)
        self.subtitle_format = tk.StringVar(value=default_format)
        self.whisper_model = tk.StringVar(value=default_model)
        self.is_processing = False
        self.last_subtitle_path = None

        # Session statistics
        self.session_stats = {
            'videos_processed': 0,
            'subtitles_generated': 0,
            'subtitles_downloaded': 0,
            'total_time_saved': 0,  # minutes
            'start_time': None
        }
        import time
        self.session_stats['start_time'] = time.time()

        # Progress tracking
        self.progress_data = {
            'current': 0,
            'total': 100,
            'start_time': None,
            'current_operation': ''
        }
        
        # Trace variables to auto-save preferences
        if self.preferences:
            self.language.trace_add('write', lambda *args: self.preferences.set('language', self.language.get()))
            self.whisper_model.trace_add('write', lambda *args: self.preferences.set('model', self.whisper_model.get()))
            self.subtitle_format.trace_add('write', lambda *args: self.preferences.set('format', self.subtitle_format.get()))
        
        self._setup_ui()

        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()

        # Save window geometry on close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Apri Video", command=self._browse_video, accelerator="Ctrl+O")
        file_menu.add_command(label="File Recenti", command=self._show_recent_files, accelerator="Ctrl+R")
        file_menu.add_separator()
        file_menu.add_command(label="Apri Cartella Output", command=self._open_output_folder, accelerator="Ctrl+Shift+O")
        file_menu.add_separator()
        file_menu.add_command(label="Esci", command=self._on_closing, accelerator="Ctrl+Q")
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Strumenti", menu=tools_menu)
        tools_menu.add_command(label="🌍 Multi-Lingua", command=self._open_multilang_window, accelerator="Ctrl+M")
        tools_menu.add_separator()
        tools_menu.add_command(label="Batch Processing", command=self._open_batch_processor, accelerator="Ctrl+B")
        tools_menu.add_command(label="Integra Video", command=self._open_video_tools, accelerator="Ctrl+V")
        tools_menu.add_command(label="Pulisci Sottotitoli", command=self._clean_subtitles)
        tools_menu.add_command(label="Statistiche Sottotitoli", command=self._show_subtitle_stats)
        tools_menu.add_separator()
        tools_menu.add_command(label="Confronta Sottotitoli", command=self._compare_subtitles)
        tools_menu.add_command(label="Unisci Sottotitoli", command=self._merge_subtitles)
        
        # Options menu
        options_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Opzioni", menu=options_menu)
        options_menu.add_command(label="Preferenze", command=self._show_preferences)
        options_menu.add_separator()
        
        # Language submenu
        language_menu = tk.Menu(options_menu, tearoff=0)
        options_menu.add_cascade(label="🌍 Lingua Interfaccia", menu=language_menu)
        
        current_lang = self.i18n.get_current_language()
        self.lang_var = tk.StringVar(value=current_lang)
        
        language_menu.add_radiobutton(
            label="🇮🇹 Italiano",
            variable=self.lang_var,
            value="it",
            command=lambda: self._change_ui_language("it")
        )
        language_menu.add_radiobutton(
            label="🇬🇧 English",
            variable=self.lang_var,
            value="en",
            command=lambda: self._change_ui_language("en")
        )
        
        options_menu.add_separator()
        options_menu.add_command(label="Pulisci Cache", command=self._clean_cache)
        options_menu.add_separator()
        options_menu.add_command(label="Verifica FFmpeg", command=self._check_ffmpeg)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Visualizza", menu=view_menu)
        view_menu.add_command(label="📋 Log Completo", command=self._show_log_viewer)
        view_menu.add_separator()
        view_menu.add_command(label="Aggiorna", command=self._refresh_view)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aiuto", menu=help_menu)
        help_menu.add_command(label="📖 Guida Completa (PDF)", command=self._open_full_guide)
        help_menu.add_command(label="⚡ Guida Rapida", command=self._show_quick_guide, accelerator="F1")
        help_menu.add_command(label="⌨️ Shortcuts Tastiera", command=self._show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="📂 Dove Vanno i File?", command=self._show_file_locations)
        help_menu.add_separator()
        help_menu.add_command(label="ℹ️ Info", command=self._show_about)

    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for common actions"""
        try:
            # File operations
            self.root.bind('<Control-o>', lambda e: self._browse_video())
            self.root.bind('<Control-O>', lambda e: self._browse_video())
            self.root.bind('<Control-r>', lambda e: self._show_recent_files())
            self.root.bind('<Control-R>', lambda e: self._show_recent_files())
            self.root.bind('<Control-Shift-O>', lambda e: self._open_output_folder())
            self.root.bind('<Control-Shift-o>', lambda e: self._open_output_folder())
            self.root.bind('<Control-q>', lambda e: self._on_closing())
            self.root.bind('<Control-Q>', lambda e: self._on_closing())

            # Generation/Preview
            self.root.bind('<Control-g>', lambda e: self._start_processing() if self.start_btn['state'] != 'disabled' else None)
            self.root.bind('<Control-G>', lambda e: self._start_processing() if self.start_btn['state'] != 'disabled' else None)
            self.root.bind('<Control-p>', lambda e: self._open_preview() if self.preview_btn['state'] != 'disabled' else None)
            self.root.bind('<Control-P>', lambda e: self._open_preview() if self.preview_btn['state'] != 'disabled' else None)

            # Tools
            self.root.bind('<Control-b>', lambda e: self._open_batch_processor())
            self.root.bind('<Control-B>', lambda e: self._open_batch_processor())
            self.root.bind('<Control-m>', lambda e: self._open_multilang_window())
            self.root.bind('<Control-M>', lambda e: self._open_multilang_window())
            self.root.bind('<Control-v>', lambda e: self._open_video_tools())
            self.root.bind('<Control-V>', lambda e: self._open_video_tools())

            # Help
            self.root.bind('<F1>', lambda e: self._show_help())

            logger.info("Keyboard shortcuts configured successfully")

        except Exception as e:
            logger.warning(f"Could not setup keyboard shortcuts: {str(e)}")

    def _setup_ui(self):
        """Setup the user interface with clean, modern layout"""
        # Main container with consistent padding
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights for responsive layout
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Title with better spacing
        title_label = ttk.Label(
            main_frame,
            text="🎬 AutoSubtitle Studio",
            font=('Arial', 18, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 5))

        # Subtitle
        subtitle_label = ttk.Label(
            main_frame,
            text="Generazione Automatica Sottotitoli con AI",
            font=('Arial', 9, 'italic'),
            foreground='#64748b'
        )
        subtitle_label.grid(row=1, column=0, columnspan=3, pady=(0, 10))

        # === NUOVO: Pannello informativo cartelle ===
        info_frame = ttk.LabelFrame(main_frame, text="📂 Percorsi Applicazione", padding="10")
        info_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        info_frame.columnconfigure(1, weight=1)

        # Output directory
        ttk.Label(
            info_frame,
            text="📝 Sottotitoli:",
            font=('Arial', 9, 'bold')
        ).grid(row=0, column=0, sticky=tk.W, pady=3)

        output_path_label = ttk.Label(
            info_frame,
            text=str(self.controller.config.OUTPUT_DIR),
            font=('Arial', 8),
            foreground='#2563eb',
            cursor='hand2'
        )
        output_path_label.grid(row=0, column=1, sticky=tk.W, padx=(5, 0), pady=3)
        output_path_label.bind('<Button-1>', lambda e: self._open_output_folder())
        create_tooltip(output_path_label, "Click per aprire la cartella dei sottotitoli generati")

        ttk.Button(
            info_frame,
            text="📂",
            command=self._open_output_folder,
            width=3
        ).grid(row=0, column=2, padx=5)

        # Models directory
        ttk.Label(
            info_frame,
            text="🤖 Modelli AI:",
            font=('Arial', 9, 'bold')
        ).grid(row=1, column=0, sticky=tk.W, pady=3)

        models_path_label = ttk.Label(
            info_frame,
            text=str(self.controller.config.MODELS_DIR),
            font=('Arial', 8),
            foreground='#16a34a',
            cursor='hand2'
        )
        models_path_label.grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=3)
        models_path_label.bind('<Button-1>', lambda e: self._open_folder(self.controller.config.MODELS_DIR))
        create_tooltip(models_path_label, "Click per aprire la cartella dei modelli Whisper")

        ttk.Button(
            info_frame,
            text="📂",
            command=lambda: self._open_folder(self.controller.config.MODELS_DIR),
            width=3
        ).grid(row=1, column=2, padx=5)

        # Temp directory
        ttk.Label(
            info_frame,
            text="🗂️ File Temp:",
            font=('Arial', 9, 'bold')
        ).grid(row=2, column=0, sticky=tk.W, pady=3)

        temp_path_label = ttk.Label(
            info_frame,
            text=str(self.controller.config.TEMP_DIR),
            font=('Arial', 8),
            foreground='#ea580c',
            cursor='hand2'
        )
        temp_path_label.grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=3)
        temp_path_label.bind('<Button-1>', lambda e: self._open_folder(self.controller.config.TEMP_DIR))
        create_tooltip(temp_path_label, "Click per aprire la cartella dei file temporanei")

        ttk.Button(
            info_frame,
            text="🗑️",
            command=self._clean_temp_folder,
            width=3
        ).grid(row=2, column=2, padx=5)
        create_tooltip(info_frame.grid_slaves(row=2, column=2)[0], "Pulisci file temporanei")

        # Info message
        ttk.Label(
            info_frame,
            text="💡 I sottotitoli generati vengono salvati nella cartella 'output_subtitles' nella directory dell'applicazione",
            font=('Arial', 8, 'italic'),
            foreground='#7c3aed',
            wraplength=650
        ).grid(row=3, column=0, columnspan=3, pady=(10, 0))

        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15
        )
        
        # Video file selection with enhanced UX
        video_label = ttk.Label(main_frame, text="File Video:", font=('Arial', 10, 'bold'))
        video_label.grid(row=4, column=0, sticky=tk.W, pady=5)

        # Make label clickable to browse
        video_label.bind('<Button-1>', lambda e: self._browse_video())
        video_label.bind('<Enter>', lambda e: video_label.config(cursor='hand2', foreground='blue'))
        video_label.bind('<Leave>', lambda e: video_label.config(cursor='', foreground='black'))

        # Entry with paste support
        video_entry = ttk.Entry(main_frame, textvariable=self.video_path, width=50)
        video_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)

        # Enable paste from clipboard
        video_entry.bind('<Control-v>', self._paste_video_path)
        video_entry.bind('<Control-V>', self._paste_video_path)

        # Drop zone hint
        create_tooltip(
            video_entry,
            "📋 Copia e incolla il percorso del video (Ctrl+V)\n"
            "📁 Oppure clicca 'Sfoglia' per selezionare\n"
            "🖱️ Doppio click sulla label per aprire selezione rapida"
        )

        browse_btn = ttk.Button(main_frame, text="📂 Sfoglia...", command=self._browse_video)
        browse_btn.grid(row=4, column=2, padx=5, pady=5)

        # Drag and drop info
        info_label = ttk.Label(
            main_frame,
            text="💡 Incolla il percorso (Ctrl+V) o clicca su Sfoglia per selezionare il video",
            font=('Arial', 8, 'italic'),
            foreground='#64748b'
        )
        info_label.grid(row=5, column=0, columnspan=3, pady=2)
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15
        )

        # Mode selection
        ttk.Label(main_frame, text="Modalità:", font=('Arial', 10, 'bold')).grid(
            row=7, column=0, sticky=tk.W, pady=5
        )

        mode_frame = ttk.Frame(main_frame)
        mode_frame.grid(row=8, column=0, columnspan=3, pady=5)
        
        auto_radio = ttk.Radiobutton(
            mode_frame,
            text="🤖 Auto-Genera con AI (Whisper - Offline)",
            variable=self.mode,
            value="auto",
            command=self._on_mode_change
        )
        auto_radio.pack(anchor=tk.W, padx=20)
        create_tooltip(
            auto_radio,
            "Genera sottotitoli usando l'intelligenza artificiale Whisper di OpenAI.\n"
            "• Funziona offline (nessuna connessione richiesta)\n"
            "• Supporta 90+ lingue\n"
            "• Qualità eccellente per audio chiaro\n"
            "• Tempo: 5-15 minuti per video da 1 ora\n"
            "• Richiede: 1.5-10 GB RAM (a seconda del modello)"
        )

        download_radio = ttk.Radiobutton(
            mode_frame,
            text="🌐 Scarica da OpenSubtitles (Online - Veloce)",
            variable=self.mode,
            value="download",
            command=self._on_mode_change
        )
        download_radio.pack(anchor=tk.W, padx=20, pady=5)
        create_tooltip(
            download_radio,
            "Scarica sottotitoli già esistenti dal database OpenSubtitles.\n"
            "• Richiede connessione internet\n"
            "• Richiede API key (configurare in config.py o .env)\n"
            "• Istantaneo (pochi secondi)\n"
            "• Qualità variabile (dipende dagli uploader)\n"
            "• Migliaia di film e serie TV disponibili"
        )
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=9, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15
        )

        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="⚙️ Opzioni di Generazione", padding="10")
        options_frame.grid(row=10, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        options_frame.columnconfigure(1, weight=1)
        
        # Language selection
        ttk.Label(options_frame, text="Lingua:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        language_combo = ttk.Combobox(
            options_frame, 
            textvariable=self.language,
            values=list(self.controller.config.LANGUAGES.keys()),
            state='readonly',
            width=15
        )
        language_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Language name display
        self.language_name_label = ttk.Label(
            options_frame, 
            text=self.controller.config.LANGUAGES.get(self.language.get(), ""),
            foreground='gray'
        )
        self.language_name_label.grid(row=0, column=2, sticky=tk.W, padx=5)
        language_combo.bind('<<ComboboxSelected>>', self._update_language_name)
        
        # Subtitle format
        ttk.Label(options_frame, text="Formato:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        format_combo = ttk.Combobox(
            options_frame,
            textvariable=self.subtitle_format,
            values=self.controller.config.SUBTITLE_FORMATS,
            state='readonly',
            width=15
        )
        format_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Whisper model (only for auto mode)
        ttk.Label(options_frame, text="Modello AI:").grid(row=2, column=0, sticky=tk.W, pady=5)

        self.model_combo = ttk.Combobox(
            options_frame,
            textvariable=self.whisper_model,
            values=self.controller.config.WHISPER_MODELS,
            state='readonly',
            width=15
        )
        self.model_combo.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

        # Memory indicator
        self.memory_indicator_label = ttk.Label(
            options_frame,
            text="",
            font=('Arial', 8),
            foreground='green'
        )
        self.memory_indicator_label.grid(row=2, column=2, sticky=tk.W, padx=5)

        # Update memory indicator when model changes
        self.model_combo.bind('<<ComboboxSelected>>', self._update_memory_indicator)

        # Model info row
        model_info = ttk.Label(
            options_frame,
            text="💡 tiny=veloce, base=bilanciato, small=qualità, medium/large=massima precisione",
            foreground='#64748b',
            font=('Arial', 8, 'italic')
        )
        model_info.grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))

        # Initial memory check
        self._update_memory_indicator()
        
        # Progress frame with enhanced visual feedback
        progress_frame = ttk.LabelFrame(main_frame, text="📊 Progresso Elaborazione", padding="10")
        progress_frame.grid(row=11, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        progress_frame.columnconfigure(0, weight=1)

        # Progress bar with determinate mode for percentage display
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode='determinate',
            maximum=100,
            length=400
        )
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)

        # Percentage label overlay on progress bar
        self.progress_percent_label = ttk.Label(
            progress_frame,
            text="0%",
            font=('Arial', 9, 'bold')
        )
        self.progress_percent_label.grid(row=0, column=0, pady=5)

        # Status label with operation details
        self.status_label = ttk.Label(
            progress_frame,
            text="Pronto. Seleziona un video per iniziare.",
            foreground='green'
        )
        self.status_label.grid(row=1, column=0, pady=5)

        # ETA label for time estimation
        self.eta_label = ttk.Label(
            progress_frame,
            text="",
            font=('Arial', 8),
            foreground='#64748b'
        )
        self.eta_label.grid(row=2, column=0, pady=(0, 5))
        
        # Log output
        log_frame = ttk.LabelFrame(main_frame, text="📋 Log Attività", padding="5")
        log_frame.grid(row=12, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=6,  # Reduced from 8 to leave more space for buttons
            width=80,
            state='disabled',
            wrap=tk.WORD
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Buttons frame - FIXED: Removed grid_propagate to allow proper resizing
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=13, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        # NOTE: grid_propagate(False) was causing buttons to be invisible!
        # The frame now auto-sizes to its content properly.
        
        self.start_btn = ttk.Button(
            buttons_frame,
            text="▶ AVVIA GENERAZIONE",
            command=self._start_processing,
            width=20
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        create_tooltip(
            self.start_btn,
            "Avvia la generazione o il download dei sottotitoli.\n"
            "Assicurati di aver:\n"
            "• Selezionato un video\n"
            "• Scelto la modalità (Auto o Download)\n"
            "• Configurato lingua e formato\n"
            "• Verificato la memoria disponibile (se Auto)"
        )

        self.cancel_btn = ttk.Button(
            buttons_frame,
            text="⏹ ANNULLA",
            command=self._cancel_processing,
            state='disabled',
            width=15
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=5)
        create_tooltip(
            self.cancel_btn,
            "Annulla l'operazione in corso.\n"
            "L'elaborazione si fermerà in modo sicuro\n"
            "al termine del segmento corrente."
        )
        
        # New buttons
        ttk.Button(
            buttons_frame,
            text="📂 Batch",
            command=self._open_batch_processor,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        self.preview_btn = ttk.Button(
            buttons_frame,
            text="👁 Anteprima",
            command=self._open_preview,
            state='disabled',
            width=15
        )
        self.preview_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="🌐 Traduci",
            command=self._translate_subtitles,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="🎬 Integra Video",
            command=self._open_video_tools,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="🌍 Multi-Lingua",
            command=self._open_multilang_window,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        # Second row of buttons - FIXED: Removed grid_propagate to allow proper resizing
        buttons_frame2 = ttk.Frame(main_frame)
        buttons_frame2.grid(row=14, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        # NOTE: grid_propagate(False) was causing buttons to be invisible!
        # The frame now auto-sizes to its content properly.
        
        ttk.Button(
            buttons_frame2,
            text="🗑 Pulisci Log",
            command=self._clear_log,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame2,
            text="📋 Visualizza Log",
            command=self._show_log_viewer,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame2,
            text="📁 Apri Cartella Output",
            command=self._open_output_folder,
            width=20
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame2,
            text="⚙ Preferenze",
            command=self._show_preferences,
            width=15
        ).pack(side=tk.LEFT, padx=5)

        # Add helpful tooltips for better UX
        self._add_tooltips()

        # Session statistics status bar
        self._create_status_bar(main_frame)

        # Configure row weights for resizing
        main_frame.rowconfigure(12, weight=1)  # Log frame can expand
        main_frame.rowconfigure(13, minsize=60, weight=0)  # Buttons row 1 - fixed height
        main_frame.rowconfigure(14, minsize=50, weight=0)  # Buttons row 2 - fixed height

        # Initial mode setup
        self._on_mode_change()

    def _add_tooltips(self):
        """Add helpful tooltips to widgets for better UX"""
        try:
            # Preview button tooltip
            create_tooltip(
                self.preview_btn,
                "👁️ Visualizza i sottotitoli generati\n\n"
                "Funzionalità:\n"
                "• Anteprima con timing preciso\n"
                "• Modifica diretta dei sottotitoli\n"
                "• Salvataggio immediato\n"
                "• Sincronizzazione visiva"
            )

            # Model selection tooltip (enhanced)
            create_tooltip(
                self.model_combo,
                "🤖 Scegli il modello Whisper AI:\n\n"
                "• tiny: Ultra veloce (1 GB RAM)\n"
                "  → Perfetto per test rapidi\n\n"
                "• base: Bilanciato (1.5 GB RAM) ✓ CONSIGLIATO\n"
                "  → Ottimo per uso quotidiano\n\n"
                "• small: Alta qualità (2.5 GB RAM)\n"
                "  → Buon compromesso qualità/velocità\n\n"
                "• medium: Qualità professionale (5 GB RAM)\n"
                "  → Per lingue complesse o audio difficile\n\n"
                "• large: Massima precisione (10 GB RAM)\n"
                "  → Qualità assoluta per progetti professionali"
            )

            # Language combo tooltip
            create_tooltip(
                self.language_name_label.master.winfo_children()[1],  # language combo
                "🌍 Seleziona la lingua del video\n\n"
                "Il modello AI rileva automaticamente la lingua,\n"
                "ma specificarla migliora la precisione.\n\n"
                "Supportate 90+ lingue!"
            )

            logger.info("Enhanced tooltips added successfully")

        except Exception as e:
            logger.warning(f"Could not add tooltips: {str(e)}")

    def _create_status_bar(self, parent):
        """Create session statistics status bar at bottom"""
        try:
            # Separator
            ttk.Separator(parent, orient='horizontal').grid(
                row=15, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 5)
            )

            # Status bar frame
            status_frame = ttk.Frame(parent, relief=tk.SUNKEN)
            status_frame.grid(row=16, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=0)

            # Session statistics labels
            self.stat_videos_label = ttk.Label(
                status_frame,
                text="📊 Video: 0",
                font=('Arial', 8),
                foreground='#2563eb'
            )
            self.stat_videos_label.pack(side=tk.LEFT, padx=10, pady=3)
            create_tooltip(
                self.stat_videos_label,
                "📊 Video elaborati in questa sessione\n\n"
                "Conta il numero di video per cui hai\n"
                "generato o scaricato sottotitoli."
            )

            self.stat_subtitles_label = ttk.Label(
                status_frame,
                text="📝 Sottotitoli: 0",
                font=('Arial', 8),
                foreground='#16a34a'
            )
            self.stat_subtitles_label.pack(side=tk.LEFT, padx=10)
            create_tooltip(
                self.stat_subtitles_label,
                "📝 Sottotitoli creati in questa sessione\n\n"
                "🤖 = Generati con AI\n"
                "🌐 = Scaricati da OpenSubtitles"
            )

            self.stat_time_label = ttk.Label(
                status_frame,
                text="⏱ Tempo risparmiato: 0 min",
                font=('Arial', 8),
                foreground='#ea580c'
            )
            self.stat_time_label.pack(side=tk.LEFT, padx=10)
            create_tooltip(
                self.stat_time_label,
                "⏱️ Tempo risparmiato in questa sessione\n\n"
                "Stima del tempo che avresti impiegato\n"
                "a creare manualmente i sottotitoli.\n\n"
                "Calcolo:\n"
                "• 15 min per sottotitolo generato\n"
                "• 5 min per sottotitolo scaricato"
            )

            self.stat_memory_label = ttk.Label(
                status_frame,
                text="💾 RAM: 0 MB",
                font=('Arial', 8),
                foreground='#7c3aed'
            )
            self.stat_memory_label.pack(side=tk.LEFT, padx=10)
            create_tooltip(
                self.stat_memory_label,
                "💾 Memoria RAM in uso dal sistema\n\n"
                "Monitoraggio in tempo reale dell'uso\n"
                "della memoria per evitare problemi."
            )

            # Session duration
            self.stat_session_label = ttk.Label(
                status_frame,
                text="🕐 Sessione: 0m",
                font=('Arial', 8),
                foreground='#64748b'
            )
            self.stat_session_label.pack(side=tk.RIGHT, padx=10)
            create_tooltip(
                self.stat_session_label,
                "🕐 Durata sessione corrente\n\n"
                "Tempo trascorso dall'apertura\n"
                "dell'applicazione."
            )

            # Update stats periodically
            self._update_stats_display()

            logger.info("Status bar created successfully")

        except Exception as e:
            logger.warning(f"Could not create status bar: {str(e)}")

    def _update_stats_display(self):
        """Update statistics display in status bar"""
        try:
            # Update counts
            videos = self.session_stats['videos_processed']
            subs_gen = self.session_stats['subtitles_generated']
            subs_down = self.session_stats['subtitles_downloaded']
            total_subs = subs_gen + subs_down

            self.stat_videos_label.config(text=f"📊 Video: {videos}")
            self.stat_subtitles_label.config(
                text=f"📝 Sottotitoli: {total_subs} ({subs_gen}🤖 + {subs_down}🌐)"
            )

            # Time saved estimate (15 min per subtitle generated manually)
            time_saved = self.session_stats['total_time_saved']
            self.stat_time_label.config(text=f"⏱ Tempo risparmiato: ~{time_saved} min")

            # Memory usage
            try:
                mem_info = self.controller.memory_manager.get_memory_info_dict()
                used_mb = mem_info.get('used_mb', 0)
                self.stat_memory_label.config(text=f"💾 RAM: {used_mb:.0f} MB")
            except:
                pass

            # Session duration
            import time
            session_duration = int((time.time() - self.session_stats['start_time']) / 60)
            self.stat_session_label.config(text=f"🕐 Sessione: {session_duration}m")

            # Schedule next update (every 10 seconds)
            self.root.after(10000, self._update_stats_display)

        except Exception as e:
            logger.debug(f"Error updating stats display: {str(e)}")

    def _increment_session_stats(self, stat_type, time_saved=0):
        """Increment session statistics"""
        try:
            if stat_type == 'video':
                self.session_stats['videos_processed'] += 1
            elif stat_type == 'subtitle_generated':
                self.session_stats['subtitles_generated'] += 1
                self.session_stats['total_time_saved'] += time_saved
            elif stat_type == 'subtitle_downloaded':
                self.session_stats['subtitles_downloaded'] += 1
                self.session_stats['total_time_saved'] += 5  # Estimated 5 min saved

            # Update display immediately
            self._update_stats_display()

        except Exception as e:
            logger.debug(f"Error incrementing stats: {str(e)}")

    def _paste_video_path(self, event=None):
        """Paste video path from clipboard"""
        try:
            # Get clipboard content
            clipboard_content = self.root.clipboard_get()

            # Clean up path (remove quotes if any)
            clipboard_content = clipboard_content.strip().strip('"').strip("'")

            # Validate it's a video file
            from pathlib import Path
            path = Path(clipboard_content)

            if path.exists() and path.suffix.lower() in self.controller.config.SUPPORTED_VIDEO_FORMATS:
                self.video_path.set(str(path))
                self._log(f"✓ Video incollato: {path.name}")
                logger.info(f"Video pasted from clipboard: {path}")
            else:
                # Try to set anyway, let user decide
                self.video_path.set(clipboard_content)
                if not path.exists():
                    messagebox.showwarning(
                        "Attenzione",
                        "Il file incollato non esiste o non è un formato video supportato.\n\n"
                        f"Percorso: {clipboard_content}\n\n"
                        "Verifica il percorso e riprova."
                    )

        except tk.TclError:
            messagebox.showinfo("Info", "Clipboard vuota o contenuto non valido")
        except Exception as e:
            logger.error(f"Error pasting video path: {str(e)}")

    def _browse_video(self):
        """Open file dialog to select video"""
        filetypes = [
            ('Video Files', ' '.join(f'*{ext}' for ext in self.controller.config.SUPPORTED_VIDEO_FORMATS)),
            ('All Files', '*.*')
        ]

        filename = filedialog.askopenfilename(
            title="Seleziona un file video",
            filetypes=filetypes
        )
        
        if filename:
            self.video_path.set(filename)
            self._log(f"Video selezionato: {Path(filename).name}")
    
    def _on_mode_change(self):
        """Handle mode change"""
        if self.mode.get() == "auto":
            self.model_combo.config(state='readonly')
        else:
            self.model_combo.config(state='disabled')
    
    def _update_language_name(self, event=None):
        """Update language name label"""
        lang_code = self.language.get()
        lang_name = self.controller.config.LANGUAGES.get(lang_code, "")
        self.language_name_label.config(text=lang_name)

    def _update_memory_indicator(self, event=None):
        """Update memory indicator based on selected model"""
        try:
            model = self.whisper_model.get()
            available_mb = self.controller.memory_manager.get_available_memory()
            is_available, _, required_mb, _ = self.controller.memory_manager.check_memory_available(model)

            if is_available:
                self.memory_indicator_label.config(
                    text=f"✓ RAM OK ({available_mb:.0f} MB / {required_mb} MB richiesti)",
                    foreground='#16a34a'
                )
            else:
                suggested_model, _ = self.controller.memory_manager.suggest_best_model()
                self.memory_indicator_label.config(
                    text=f"⚠️ RAM insufficiente ({available_mb:.0f} MB) - Usa '{suggested_model}'",
                    foreground='#dc2626'
                )

        except Exception as e:
            logger.debug(f"Error updating memory indicator: {str(e)}")
            self.memory_indicator_label.config(text="", foreground='black')
    
    def _log(self, message):
        """Add message to log and update progress if percentage found"""
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

        # Parse progress from message (format: "X/Y - message" or "[X%] message" or "X% - message")
        import re

        # Try to extract progress percentage
        # Format 1: "1/3 - Estrazione audio..."
        match = re.search(r'(\d+)/(\d+)', message)
        if match:
            current = int(match.group(1))
            total = int(match.group(2))
            self._update_progress(current, total)
            return

        # Format 2: "[90%] message" or "90% - message"
        match = re.search(r'[\[\(]?(\d+)%[\]\)]?', message)
        if match:
            percentage = int(match.group(1))
            self._update_progress(percentage, 100)
            return

        # Format 3: "Elaborazione segmento X/Y"
        match = re.search(r'segmento\s+(\d+)/(\d+)', message, re.IGNORECASE)
        if match:
            current = int(match.group(1))
            total = int(match.group(2))
            self._update_progress(current, total)
    
    def _clear_log(self):
        """Clear log text"""
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
    
    def _update_status(self, message, color='black'):
        """Update status label"""
        self.status_label.config(text=message, foreground=color)

    def _update_progress(self, current, total=100, operation="Elaborazione..."):
        """
        Update progress bar with percentage and ETA

        Args:
            current: Current progress value
            total: Total progress value (default 100)
            operation: Current operation description
        """
        try:
            import time

            # Calculate percentage
            if total > 0:
                percentage = int((current / total) * 100)
            else:
                percentage = 0

            percentage = max(0, min(100, percentage))  # Clamp to 0-100

            # Update progress bar
            self.progress_bar['value'] = percentage

            # Update percentage label
            self.progress_percent_label.config(text=f"{percentage}%")

            # Calculate ETA if progress started
            if self.progress_data['start_time'] and current > 0 and current < total:
                elapsed = time.time() - self.progress_data['start_time']
                rate = current / elapsed
                remaining = (total - current) / rate if rate > 0 else 0

                # Format ETA
                if remaining < 60:
                    eta_text = f"⏱ ETA: {int(remaining)}s"
                elif remaining < 3600:
                    eta_text = f"⏱ ETA: {int(remaining / 60)}m {int(remaining % 60)}s"
                else:
                    hours = int(remaining / 3600)
                    minutes = int((remaining % 3600) / 60)
                    eta_text = f"⏱ ETA: {hours}h {minutes}m"

                self.eta_label.config(text=eta_text)
            elif current == 0:
                self.eta_label.config(text="")
            elif current >= total:
                self.eta_label.config(text="✓ Completato!")

            # Update stored progress
            self.progress_data['current'] = current
            self.progress_data['total'] = total
            self.progress_data['current_operation'] = operation

            # Force GUI update
            self.root.update_idletasks()

        except Exception as e:
            logger.debug(f"Error updating progress: {str(e)}")

    def _start_progress(self, operation="Elaborazione..."):
        """Start progress tracking"""
        import time
        self.progress_data['start_time'] = time.time()
        self.progress_data['current_operation'] = operation
        self._update_progress(0, 100, operation)

    def _reset_progress(self):
        """Reset progress bar to initial state"""
        self.progress_bar['value'] = 0
        self.progress_percent_label.config(text="0%")
        self.eta_label.config(text="")
        self.progress_data = {
            'current': 0,
            'total': 100,
            'start_time': None,
            'current_operation': ''
        }
    
    def _start_processing(self):
        """Start subtitle generation/download"""
        # Validate input
        if not self.video_path.get():
            messagebox.showerror("Errore", "Seleziona un file video!")
            return
        
        video_file = Path(self.video_path.get())
        if not video_file.exists():
            messagebox.showerror("Errore", "Il file video non esiste!")
            return
        
        # Disable start button, enable cancel
        self.start_btn.config(state='disabled')
        self.cancel_btn.config(state='normal')
        self.is_processing = True

        # Start progress tracking with percentage
        mode = self.mode.get()
        operation = "Generazione sottotitoli..." if mode == "auto" else "Download sottotitoli..."
        self._start_progress(operation)

        # Run processing in separate thread
        thread = threading.Thread(target=self._process_video, daemon=True)
        thread.start()
    
    def _process_video(self):
        """Process video in background thread"""
        try:
            video_path = self.video_path.get()
            mode = self.mode.get()
            language = self.language.get()
            subtitle_format = self.subtitle_format.get()
            
            if mode == "auto":
                # Auto-generate subtitles
                self._update_status("Generazione automatica sottotitoli...", 'blue')
                self._log("=== Inizio generazione automatica ===")
                
                model = self.whisper_model.get()
                result = self.controller.generate_subtitles(
                    video_path=video_path,
                    language=language,
                    output_format=subtitle_format,
                    model_name=model,
                    progress_callback=self._log
                )
                
            else:
                # Download subtitles
                self._update_status("Ricerca sottotitoli su OpenSubtitles...", 'blue')
                self._log("=== Inizio ricerca sottotitoli ===")

                result = self.controller.download_subtitles(
                    video_path=video_path,
                    language=language,
                    progress_callback=self._log,
                    allow_selection=True  # Enable selection dialog
                )

                # Check if result is a list (multiple results found)
                if isinstance(result, list):
                    self._log(f"💡 Trovati {len(result)} sottotitoli - selezione manuale richiesta")
                    self._update_status("Seleziona sottotitolo desiderato...", 'orange')

                    # Show selection window
                    selector = OpenSubtitlesSelectorWindow(self.root, result, self.controller)
                    selected = selector.show()

                    if not selected:
                        self._update_status("Operazione annullata", 'orange')
                        self._log("✗ Selezione annullata dall'utente")
                        return

                    # Download the selected subtitle
                    self._log(f"Download sottotitolo selezionato...")
                    self._update_status("Download in corso...", 'blue')

                    # Download selected subtitle directly
                    try:
                        attributes = selected.get('attributes', {})
                        files = attributes.get('files', [])
                        if files and files[0].get('file_id'):
                            file_id = files[0]['file_id']
                            video_stem = Path(video_path).stem
                            output_path = self.controller.config.OUTPUT_DIR / f"{video_stem}.srt"

                            result = self.controller.opensubtitles.download_subtitle(file_id, output_path)
                        else:
                            raise Exception("File ID non disponibile per il download")
                    except Exception as e:
                        self._log(f"✗ Errore download: {str(e)}")
                        self._update_status("✗ Download fallito", 'red')
                        messagebox.showerror("Errore Download", f"Impossibile scaricare il sottotitolo:\n{str(e)}")
                        return

            if result:
                self._update_status("✓ Completato con successo!", 'green')
                self._log(f"✓ Sottotitoli salvati in: {result}")
                self.last_subtitle_path = result
                self.preview_btn.config(state='normal')

                # Update recent videos in preferences
                if self.preferences:
                    self.preferences.update_last_videos(video_path)

                # Update session statistics
                self._increment_session_stats('video')
                if mode == "auto":
                    # Estimate time saved: ~15 min per subtitle generated manually
                    self._increment_session_stats('subtitle_generated', time_saved=15)
                else:
                    # Download: ~5 min saved
                    self._increment_session_stats('subtitle_downloaded')

                messagebox.showinfo(
                    "Successo",
                    f"Sottotitoli creati con successo!\n\nFile: {Path(result).name}\nCartella: {Path(result).parent}"
                )
            else:
                self._update_status("✗ Operazione fallita", 'red')
                messagebox.showerror(
                    "Errore",
                    "Non è stato possibile completare l'operazione.\nControlla il log per i dettagli."
                )
                
        except Exception as e:
            logger.error(f"Error in processing: {str(e)}")
            self._update_status(f"✗ Errore: {str(e)}", 'red')
            self._log(f"✗ ERRORE: {str(e)}")
            messagebox.showerror("Errore", str(e))
            
        finally:
            # Re-enable buttons and reset progress
            self._reset_progress()
            self.start_btn.config(state='normal')
            self.cancel_btn.config(state='disabled')
            self.is_processing = False
    
    def _cancel_processing(self):
        """Cancel current processing"""
        if messagebox.askyesno("Conferma", "Vuoi annullare l'operazione in corso?"):
            self.is_processing = False
            self._update_status("Operazione annullata", 'orange')
            self._log("✗ Operazione annullata dall'utente")
    
    def _open_batch_processor(self):
        """Open batch processing window"""
        try:
            BatchProcessorWindow(self.root, self.controller)
        except Exception as e:
            logger.error(f"Error opening batch processor: {str(e)}")
            messagebox.showerror("Errore", f"Impossibile aprire elaborazione batch:\n{str(e)}")
    
    def _open_video_tools(self):
        """Open video tools window"""
        try:
            VideoToolsWindow(self.root, self.controller)
        except Exception as e:
            logger.error(f"Error opening video tools: {str(e)}")
            messagebox.showerror("Errore", f"Impossibile aprire strumenti video:\n{str(e)}")
    
    def _open_preview(self):
        """Open subtitle preview window"""
        if not self.last_subtitle_path:
            # Ask user to select a subtitle file
            filetypes = [
                ('Subtitle Files', '*.srt *.vtt'),
                ('All Files', '*.*')
            ]
            
            subtitle_file = filedialog.askopenfilename(
                title="Seleziona file sottotitoli",
                filetypes=filetypes
            )
            
            if not subtitle_file:
                return
                
            self.last_subtitle_path = subtitle_file
        
        try:
            SubtitlePreviewWindow(self.root, self.last_subtitle_path, self.controller)
        except Exception as e:
            logger.error(f"Error opening preview: {str(e)}")
            messagebox.showerror("Errore", f"Impossibile aprire anteprima:\n{str(e)}")
    
    def _translate_subtitles(self):
        """Translate subtitle file"""
        # Select input file
        input_file = filedialog.askopenfilename(
            title="Seleziona sottotitoli da tradurre",
            filetypes=[('Subtitle Files', '*.srt *.vtt'), ('All Files', '*.*')]
        )
        
        if not input_file:
            return
        
        # Create translation dialog
        translate_window = tk.Toplevel(self.root)
        translate_window.title("Traduci Sottotitoli")
        translate_window.geometry("500x300")
        
        ttk.Label(
            translate_window,
            text="🌐 Traduzione Sottotitoli",
            font=('Arial', 12, 'bold')
        ).pack(pady=10)
        
        ttk.Label(translate_window, text=f"File: {Path(input_file).name}").pack(pady=5)
        
        frame = ttk.Frame(translate_window)
        frame.pack(pady=20)
        
        # Source language
        ttk.Label(frame, text="Lingua Originale:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        source_lang = tk.StringVar(value='en')
        src_combo = ttk.Combobox(
            frame,
            textvariable=source_lang,
            values=list(TranslationService.get_supported_languages().keys()),
            state='readonly',
            width=15
        )
        src_combo.grid(row=0, column=1, padx=10, pady=5)
        
        # Target language
        ttk.Label(frame, text="Lingua Destinazione:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        target_lang = tk.StringVar(value='it')
        tgt_combo = ttk.Combobox(
            frame,
            textvariable=target_lang,
            values=list(TranslationService.get_supported_languages().keys()),
            state='readonly',
            width=15
        )
        tgt_combo.grid(row=1, column=1, padx=10, pady=5)
        
        # Progress
        progress = ttk.Progressbar(translate_window, mode='indeterminate')
        progress.pack(fill=tk.X, padx=20, pady=10)
        
        status_label = ttk.Label(translate_window, text="Pronto per la traduzione")
        status_label.pack(pady=5)
        
        def do_translate():
            # Ask for output file
            output_file = filedialog.asksaveasfilename(
                title="Salva sottotitoli tradotti",
                defaultextension=Path(input_file).suffix,
                filetypes=[('Subtitle Files', '*.srt *.vtt')]
            )
            
            if not output_file:
                return
            
            progress.start(10)
            status_label.config(text="Traduzione in corso...")
            
            def translate_thread():
                try:
                    translator = TranslationService(service='google')
                    
                    def update_progress(msg):
                        status_label.config(text=msg)
                    
                    result = translator.translate_subtitle_file(
                        input_file,
                        output_file,
                        source_lang.get(),
                        target_lang.get(),
                        progress_callback=update_progress
                    )
                    
                    progress.stop()
                    status_label.config(text="✓ Traduzione completata!")
                    messagebox.showinfo("Successo", f"Sottotitoli tradotti salvati in:\n{result}")
                    translate_window.destroy()
                    
                except Exception as e:
                    progress.stop()
                    status_label.config(text=f"✗ Errore: {str(e)}")
                    messagebox.showerror("Errore", f"Errore nella traduzione:\n{str(e)}")
            
            thread = threading.Thread(target=translate_thread, daemon=True)
            thread.start()
        
        ttk.Button(
            translate_window,
            text="🌐 Traduci",
            command=do_translate
        ).pack(pady=20)
    
    def _open_output_folder(self):
        """Open output folder in file explorer"""
        import os
        import platform
        import subprocess

        output_dir = self.controller.get_output_directory()

        try:
            if platform.system() == 'Windows':
                os.startfile(output_dir)
            elif platform.system() == 'Darwin':
                subprocess.Popen(['open', str(output_dir)])
            else:
                subprocess.Popen(['xdg-open', str(output_dir)])
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile aprire cartella:\n{str(e)}")

    def _open_folder(self, folder_path):
        """Open specified folder in file explorer"""
        import os
        import platform
        import subprocess

        try:
            folder_path = Path(folder_path)
            if not folder_path.exists():
                folder_path.mkdir(parents=True, exist_ok=True)

            if platform.system() == 'Windows':
                os.startfile(str(folder_path))
            elif platform.system() == 'Darwin':
                subprocess.Popen(['open', str(folder_path)])
            else:
                subprocess.Popen(['xdg-open', str(folder_path)])

            logger.info(f"Opened folder: {folder_path}")

        except Exception as e:
            logger.error(f"Error opening folder: {str(e)}")
            messagebox.showerror("Errore", f"Impossibile aprire cartella:\n{str(e)}")

    def _clean_temp_folder(self):
        """Clean temporary files folder"""
        if messagebox.askyesno(
            "Conferma Pulizia",
            "Vuoi eliminare tutti i file temporanei?\n\n"
            "Questa operazione è sicura e libera spazio su disco."
        ):
            try:
                temp_dir = self.controller.config.TEMP_DIR

                if temp_dir.exists():
                    files_deleted = 0
                    space_freed = 0

                    for file in temp_dir.glob("*"):
                        if file.is_file():
                            try:
                                size = file.stat().st_size
                                file.unlink()
                                files_deleted += 1
                                space_freed += size
                            except Exception as e:
                                logger.warning(f"Could not delete {file}: {str(e)}")

                    space_mb = space_freed / (1024 * 1024)

                    messagebox.showinfo(
                        "Pulizia Completata",
                        f"✓ File temporanei rimossi!\n\n"
                        f"File eliminati: {files_deleted}\n"
                        f"Spazio liberato: {space_mb:.2f} MB"
                    )

                    logger.info(f"Temp folder cleaned: {files_deleted} files, {space_mb:.2f} MB freed")
                    self._log(f"✓ Puliti {files_deleted} file temporanei ({space_mb:.1f} MB)")

                else:
                    messagebox.showinfo("Info", "Cartella temporanea vuota o inesistente")

            except Exception as e:
                logger.error(f"Error cleaning temp folder: {str(e)}")
                messagebox.showerror("Errore", f"Impossibile pulire cartella temporanea:\n{str(e)}")
    
    def _show_preferences(self):
        """Show preferences dialog"""
        if not self.preferences:
            messagebox.showinfo("Info", "Gestione preferenze non disponibile")
            return
        
        pref_window = tk.Toplevel(self.root)
        pref_window.title("Preferenze")
        pref_window.geometry("500x400")
        
        ttk.Label(
            pref_window,
            text="⚙ Preferenze Applicazione",
            font=('Arial', 12, 'bold')
        ).pack(pady=10)
        
        notebook = ttk.Notebook(pref_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # General tab
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="Generale")
        
        ttk.Label(general_frame, text="Lingua Predefinita:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        default_lang = tk.StringVar(value=self.preferences.get('language', 'it'))
        ttk.Combobox(
            general_frame,
            textvariable=default_lang,
            values=list(self.controller.config.LANGUAGES.keys()),
            state='readonly'
        ).grid(row=0, column=1, sticky=tk.W, padx=10, pady=10)
        
        ttk.Label(general_frame, text="Modello Predefinito:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        default_model = tk.StringVar(value=self.preferences.get('model', 'base'))
        ttk.Combobox(
            general_frame,
            textvariable=default_model,
            values=self.controller.config.WHISPER_MODELS,
            state='readonly'
        ).grid(row=1, column=1, sticky=tk.W, padx=10, pady=10)
        
        ttk.Label(general_frame, text="Formato Predefinito:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=10)
        default_format = tk.StringVar(value=self.preferences.get('format', 'srt'))
        ttk.Combobox(
            general_frame,
            textvariable=default_format,
            values=self.controller.config.SUBTITLE_FORMATS,
            state='readonly'
        ).grid(row=2, column=1, sticky=tk.W, padx=10, pady=10)
        
        # Recent files tab
        recent_frame = ttk.Frame(notebook)
        notebook.add(recent_frame, text="File Recenti")
        
        recent_listbox = tk.Listbox(recent_frame, height=15)
        recent_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for video in self.preferences.get_last_videos():
            recent_listbox.insert(tk.END, video)
        
        def clear_recent():
            if messagebox.askyesno("Conferma", "Vuoi cancellare la lista dei file recenti?"):
                self.preferences.set('last_videos', [])
                recent_listbox.delete(0, tk.END)
        
        ttk.Button(recent_frame, text="Cancella Lista", command=clear_recent).pack(pady=5)
        
        # Save button
        def save_prefs():
            self.preferences.set('language', default_lang.get())
            self.preferences.set('model', default_model.get())
            self.preferences.set('format', default_format.get())
            self.preferences.save_preferences()
            
            # Update current UI
            self.language.set(default_lang.get())
            self.whisper_model.set(default_model.get())
            self.subtitle_format.set(default_format.get())
            
            messagebox.showinfo("Successo", "Preferenze salvate!")
            pref_window.destroy()
        
        ttk.Button(pref_window, text="💾 Salva", command=save_prefs).pack(pady=10)
    
    def _show_recent_files(self):
        """Show recent files menu with enhanced UI"""
        if not self.preferences:
            messagebox.showinfo("Info", "Nessuna preferenza disponibile")
            return

        recent_videos = self.preferences.get_last_videos()

        recent_window = tk.Toplevel(self.root)
        recent_window.title("📁 Video Recenti")
        recent_window.geometry("700x450")
        recent_window.transient(self.root)

        # Header
        header_frame = ttk.Frame(recent_window, padding="10")
        header_frame.pack(fill=tk.X)

        ttk.Label(
            header_frame,
            text="📁 Video Elaborati Recentemente",
            font=('Arial', 13, 'bold')
        ).pack(side=tk.LEFT)

        ttk.Label(
            header_frame,
            text=f"({len(recent_videos)} video)",
            font=('Arial', 9),
            foreground='gray'
        ).pack(side=tk.LEFT, padx=10)

        # Info label
        info_frame = ttk.Frame(recent_window, padding="5")
        info_frame.pack(fill=tk.X)

        ttk.Label(
            info_frame,
            text="💡 Doppio click per caricare rapidamente | Click destro per opzioni",
            font=('Arial', 8, 'italic'),
            foreground='blue'
        ).pack()

        # Treeview with columns
        list_frame = ttk.Frame(recent_window, padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)

        columns = ('filename', 'path')
        tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', height=12)

        tree.heading('#0', text='#', anchor=tk.W)
        tree.heading('filename', text='Nome File', anchor=tk.W)
        tree.heading('path', text='Percorso', anchor=tk.W)

        tree.column('#0', width=40, stretch=False)
        tree.column('filename', width=250, stretch=True)
        tree.column('path', width=350, stretch=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Populate tree
        if recent_videos:
            for idx, video_path in enumerate(recent_videos, 1):
                path_obj = Path(video_path)
                filename = path_obj.name if path_obj.exists() else f"{path_obj.name} (❌ Non trovato)"
                tree.insert('', 'end', text=f"{idx}", values=(filename, str(video_path)))
        else:
            # Empty state
            tree.insert('', 'end', text="", values=("Nessun video recente", "Elabora un video per vederlo qui"))

        # Load selected function
        def load_selected(event=None):
            selection = tree.selection()
            if selection and recent_videos:
                item = selection[0]
                values = tree.item(item, 'values')
                video_path = values[1]

                # Check if file exists
                if Path(video_path).exists():
                    self.video_path.set(video_path)
                    recent_window.destroy()
                    logger.info(f"Loaded recent video: {video_path}")
                else:
                    messagebox.showerror(
                        "File Non Trovato",
                        f"Il video non esiste più:\n{video_path}\n\nRimuovilo dalla lista?"
                    )

        # Remove selected function
        def remove_selected():
            selection = tree.selection()
            if selection and recent_videos:
                item = selection[0]
                values = tree.item(item, 'values')
                video_path = values[1]

                if messagebox.askyesno("Conferma", f"Rimuovere dalla lista?\n\n{Path(video_path).name}"):
                    recent_videos.remove(video_path)
                    self.preferences.set('last_videos', recent_videos)
                    tree.delete(item)
                    logger.info(f"Removed from recent: {video_path}")

        # Clear all function
        def clear_all():
            if messagebox.askyesno("Conferma", "Vuoi cancellare tutta la cronologia video?"):
                self.preferences.set('last_videos', [])
                recent_window.destroy()
                logger.info("Recent videos cleared")

        # Bind double-click
        tree.bind('<Double-Button-1>', load_selected)

        # Buttons frame
        buttons_frame = ttk.Frame(recent_window, padding="10")
        buttons_frame.pack(fill=tk.X)

        ttk.Button(
            buttons_frame,
            text="✓ Carica Selezionato",
            command=load_selected,
            width=20
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            buttons_frame,
            text="🗑 Rimuovi",
            command=remove_selected,
            width=15
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            buttons_frame,
            text="🧹 Cancella Tutto",
            command=clear_all,
            width=15
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            buttons_frame,
            text="✖ Chiudi",
            command=recent_window.destroy,
            width=12
        ).pack(side=tk.RIGHT, padx=5)
    
    def _clean_subtitles(self):
        """Clean subtitle file from ads and formatting"""
        from tkinter import filedialog
        
        input_file = filedialog.askopenfilename(
            title="Seleziona sottotitoli da pulire",
            filetypes=[('Subtitle Files', '*.srt *.vtt')]
        )
        
        if not input_file:
            return
        
        # Options dialog
        options_window = tk.Toplevel(self.root)
        options_window.title("Opzioni Pulizia")
        options_window.geometry("400x300")
        
        ttk.Label(options_window, text="🧹 Cosa Vuoi Rimuovere?", font=('Arial', 11, 'bold')).pack(pady=10)
        
        remove_ads = tk.BooleanVar(value=True)
        remove_hi = tk.BooleanVar(value=False)
        remove_fmt = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(options_window, text="Pubblicità (URL, siti web)", variable=remove_ads).pack(anchor=tk.W, padx=20, pady=5)
        ttk.Checkbutton(options_window, text="Annotazioni HI [door], (sighs)", variable=remove_hi).pack(anchor=tk.W, padx=20, pady=5)
        ttk.Checkbutton(options_window, text="Tag formattazione <i>, {bold}", variable=remove_fmt).pack(anchor=tk.W, padx=20, pady=5)
        
        def do_clean():
            try:
                from utils.subtitle_cleaner import SubtitleCleaner
                cleaner = SubtitleCleaner()
                
                result = cleaner.clean_subtitle_file(
                    input_file,
                    remove_ads=remove_ads.get(),
                    remove_hi=remove_hi.get(),
                    remove_formatting=remove_fmt.get()
                )
                
                messagebox.showinfo("Successo", f"Sottotitoli puliti:\n{result}")
                options_window.destroy()
            except Exception as e:
                messagebox.showerror("Errore", str(e))
        
        ttk.Button(options_window, text="🧹 Pulisci", command=do_clean).pack(pady=20)
    
    def _show_subtitle_stats(self):
        """Show subtitle statistics"""
        from tkinter import filedialog
        
        subtitle_file = filedialog.askopenfilename(
            title="Seleziona sottotitoli da analizzare",
            filetypes=[('Subtitle Files', '*.srt *.vtt')]
        )
        
        if not subtitle_file:
            return
        
        try:
            from utils.subtitle_stats import SubtitleStats
            analyzer = SubtitleStats()
            stats = analyzer.analyze(subtitle_file)
            summary = analyzer.get_summary(stats)
            
            stats_window = tk.Toplevel(self.root)
            stats_window.title("Statistiche Sottotitoli")
            stats_window.geometry("500x400")
            
            ttk.Label(stats_window, text="📊 Statistiche", font=('Arial', 12, 'bold')).pack(pady=10)
            
            text_widget = tk.Text(stats_window, width=60, height=20, wrap=tk.WORD)
            text_widget.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
            text_widget.insert(1.0, summary)
            text_widget.config(state='disabled')
            
        except Exception as e:
            messagebox.showerror("Errore", str(e))
    
    def _compare_subtitles(self):
        """Compare two subtitle files"""
        from tkinter import filedialog
        
        file1 = filedialog.askopenfilename(title="Seleziona primo sottotitolo", filetypes=[('Subtitle Files', '*.srt *.vtt')])
        if not file1:
            return
        
        file2 = filedialog.askopenfilename(title="Seleziona secondo sottotitolo", filetypes=[('Subtitle Files', '*.srt *.vtt')])
        if not file2:
            return
        
        messagebox.showinfo("Info", f"Confronto tra:\n\n{Path(file1).name}\ne\n{Path(file2).name}\n\nFunzionalità in sviluppo!")
    
    def _merge_subtitles(self):
        """Merge multiple subtitle files"""
        from tkinter import filedialog
        
        files = filedialog.askopenfilenames(title="Seleziona sottotitoli da unire", filetypes=[('Subtitle Files', '*.srt *.vtt')])
        
        if len(files) < 2:
            messagebox.showwarning("Attenzione", "Seleziona almeno 2 file!")
            return
        
        messagebox.showinfo("Info", f"Unione di {len(files)} file.\n\nFunzionalità in sviluppo!")
    
    def _clean_cache(self):
        """Clean application cache"""
        if messagebox.askyesno("Conferma", "Vuoi pulire la cache dell'applicazione?\n(Modelli AI non saranno eliminati)"):
            try:
                import shutil
                cache_dir = self.controller.config.CACHE_DIR
                temp_dir = self.controller.config.TEMP_DIR
                
                if cache_dir.exists():
                    shutil.rmtree(cache_dir)
                    cache_dir.mkdir()
                
                if temp_dir.exists():
                    for file in temp_dir.glob("*"):
                        file.unlink()
                
                messagebox.showinfo("Successo", "Cache pulita!")
            except Exception as e:
                messagebox.showerror("Errore", str(e))
    
    def _check_ffmpeg(self):
        """Check FFmpeg installation"""
        from utils.audio_extractor import check_ffmpeg_installed
        
        if check_ffmpeg_installed():
            try:
                import subprocess
                result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
                version_info = result.stdout.split('\n')[0]
                messagebox.showinfo("FFmpeg", f"✓ FFmpeg installato!\n\n{version_info}")
            except:
                messagebox.showinfo("FFmpeg", "✓ FFmpeg è installato e funzionante!")
        else:
            messagebox.showerror("FFmpeg", "✗ FFmpeg non trovato!\n\nEsegui install_ffmpeg_windows.bat")
    
    def _show_quick_guide(self):
        """Show quick guide"""
        guide_text = """
🎬 GUIDA RAPIDA

GENERAZIONE AUTOMATICA:
1. Seleziona video
2. Scegli "Auto-Genera"
3. Seleziona lingua
4. Click "Avvia"
5. Attendi 5-10 minuti
6. Sottotitoli pronti!

DOWNLOAD OPENSUBTITLES:
1. Configura API key in config.py
2. Seleziona video
3. Scegli "Scarica"
4. Click "Avvia"

INTEGRAZIONE VIDEO:
1. Tools → Integra Video
2. Seleziona video e sottotitoli
3. Scegli Soft (consigliato) o Hard
4. Auto-sync attivo di default
5. Test con Live Player
6. Regola in tempo reale mentre guardi!

SHORTCUTS:
Ctrl+O: Apri video
Ctrl+B: Batch processing
Ctrl+I: Integra video
Ctrl+P: Preferenze
"""
        
        guide_window = tk.Toplevel(self.root)
        guide_window.title("Guida Rapida")
        guide_window.geometry("500x500")
        
        text_widget = tk.Text(guide_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(1.0, guide_text)
        text_widget.config(state='disabled')
    
    def _show_shortcuts(self):
        """Show keyboard shortcuts"""
        shortcuts_text = """
⌨️ KEYBOARD SHORTCUTS

FILE:
Ctrl+O: Apri video
Ctrl+R: File recenti

STRUMENTI:
Ctrl+B: Batch processing
Ctrl+I: Integra video
Ctrl+T: Traduci
Ctrl+E: Anteprima

AZIONI:
Ctrl+Enter: Avvia elaborazione
Ctrl+C: Annulla
Ctrl+L: Pulisci log

OPZIONI:
Ctrl+P: Preferenze
Ctrl+,: Impostazioni

HELP:
F1: Guida rapida
Ctrl+H: Shortcuts (questa finestra)
"""
        
        shortcuts_window = tk.Toplevel(self.root)
        shortcuts_window.title("Keyboard Shortcuts")
        shortcuts_window.geometry("400x500")
        
        text_widget = tk.Text(shortcuts_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(1.0, shortcuts_text)
        text_widget.config(state='disabled')
    
    def _open_multilang_window(self):
        """Open multi-language generation window"""
        try:
            video_path = self.video_path.get() if self.video_path.get() else None
            MultiLanguageWindow(self.root, self.controller, video_path)
        except Exception as e:
            logger.error(f"Error opening multi-language window: {str(e)}")
            messagebox.showerror("Errore", f"Impossibile aprire finestra multi-lingua:\n{str(e)}")
    
    def _change_ui_language(self, language_code):
        """Change UI language"""
        try:
            self.i18n.set_language(language_code)
            
            # Show restart message
            if language_code == 'it':
                messagebox.showinfo(
                    "Lingua Cambiata",
                    "Lingua interfaccia cambiata in Italiano!\n\n"
                    "Riavvia l'applicazione per applicare le modifiche."
                )
            else:
                messagebox.showinfo(
                    "Language Changed",
                    "Interface language changed to English!\n\n"
                    "Restart the application to apply changes."
                )
            
            logger.info(f"UI language changed to: {language_code}")
            
        except Exception as e:
            logger.error(f"Error changing language: {str(e)}")
            messagebox.showerror("Error", f"Cannot change language:\n{str(e)}")
    
    def _show_log_viewer(self):
        """Show log viewer window"""
        try:
            log_viewer = LogViewerWindow(self.root)
            log_viewer.show()
        except Exception as e:
            logger.error(f"Error opening log viewer: {str(e)}")
            messagebox.showerror("Errore", f"Impossibile aprire visualizzatore log:\n{str(e)}")
    
    def _refresh_view(self):
        """Refresh the main view"""
        # Refresh any visible data
        messagebox.showinfo("Info", "Vista aggiornata")
    
    def _show_about(self):
        """Show about dialog"""
        about_text = f"""
{self.controller.config.APP_NAME}
Version {self.controller.config.APP_VERSION}

Applicazione professionale per generazione e gestione
sottotitoli con intelligenza artificiale.

FUNZIONALITÀ:
• Generazione AI con Whisper (90+ lingue)
• Download da OpenSubtitles
• Batch processing
• Live sync adjustment
• Preview e editing
• Traduzione
• Integrazione video (soft/hard)
• E molto altro!

TECNOLOGIE:
• Python 3
• OpenAI Whisper
• FFmpeg
• tkinter

LICENZA: MIT
Copyright © 2026

Sviluppato con ❤️
"""

        messagebox.showinfo("About", about_text)

    def _open_full_guide(self):
        """Open full guide PDF or markdown"""
        guide_path = self.controller.config.BASE_DIR / "GUIDA_RAPIDA.md"

        if guide_path.exists():
            try:
                import os
                import platform

                if platform.system() == 'Windows':
                    os.startfile(str(guide_path))
                elif platform.system() == 'Darwin':  # macOS
                    os.system(f'open "{guide_path}"')
                else:  # Linux
                    os.system(f'xdg-open "{guide_path}"')

                logger.info("Opened full guide")

            except Exception as e:
                logger.error(f"Error opening guide: {str(e)}")
                messagebox.showerror("Errore", f"Impossibile aprire la guida:\n{str(e)}")
        else:
            messagebox.showwarning(
                "Guida Non Trovata",
                "Il file GUIDA_RAPIDA.md non è stato trovato.\n\n"
                "Dovrebbe trovarsi nella cartella principale dell'applicazione."
            )

    def _show_file_locations(self):
        """Show detailed file locations info"""
        locations_window = tk.Toplevel(self.root)
        locations_window.title("📂 Dove Vanno i File?")
        locations_window.geometry("700x500")
        locations_window.transient(self.root)

        # Header
        ttk.Label(
            locations_window,
            text="📂 Posizioni dei File",
            font=('Arial', 14, 'bold')
        ).pack(pady=15)

        # Main frame with info
        info_frame = ttk.Frame(locations_window, padding="20")
        info_frame.pack(fill=tk.BOTH, expand=True)

        sections = [
            {
                "icon": "📝",
                "title": "Sottotitoli Generati",
                "path": str(self.controller.config.OUTPUT_DIR),
                "description": "Tutti i sottotitoli creati vengono salvati qui.\nFormato: nome_video.srt o nome_video.vtt"
            },
            {
                "icon": "🤖",
                "title": "Modelli AI (Whisper)",
                "path": str(self.controller.config.MODELS_DIR),
                "description": "I modelli Whisper vengono scaricati automaticamente\ne salvati qui per uso futuro (non verranno riscaricati)."
            },
            {
                "icon": "🗂️",
                "title": "File Temporanei",
                "path": str(self.controller.config.TEMP_DIR),
                "description": "File audio estratti temporaneamente dai video.\nVengono eliminati automaticamente dopo l'elaborazione."
            },
            {
                "icon": "📦",
                "title": "Cache Applicazione",
                "path": str(self.controller.config.CACHE_DIR),
                "description": "Dati temporanei dell'applicazione.\nPuoi pulirla da: Opzioni → Pulisci Cache"
            }
        ]

        for idx, section in enumerate(sections):
            # Section frame
            section_frame = ttk.LabelFrame(
                info_frame,
                text=f"{section['icon']} {section['title']}",
                padding="10"
            )
            section_frame.pack(fill=tk.X, pady=10)

            # Path label (clickable)
            path_label = ttk.Label(
                section_frame,
                text=section['path'],
                font=('Arial', 9, 'bold'),
                foreground='#2563eb',
                cursor='hand2'
            )
            path_label.pack(anchor=tk.W, pady=(0, 5))
            path_label.bind('<Button-1>', lambda e, p=section['path']: self._open_folder(p))

            # Description
            ttk.Label(
                section_frame,
                text=section['description'],
                font=('Arial', 8),
                foreground='#64748b',
                wraplength=620,
                justify=tk.LEFT
            ).pack(anchor=tk.W)

            # Open button
            ttk.Button(
                section_frame,
                text="📂 Apri Cartella",
                command=lambda p=section['path']: self._open_folder(p),
                width=15
            ).pack(anchor=tk.E, pady=(5, 0))

        # Bottom info
        ttk.Label(
            info_frame,
            text="💡 Click sul percorso o sul pulsante per aprire la cartella",
            font=('Arial', 8, 'italic'),
            foreground='#7c3aed'
        ).pack(pady=(15, 0))

        # Close button
        ttk.Button(
            locations_window,
            text="✖ Chiudi",
            command=locations_window.destroy,
            width=15
        ).pack(pady=10)
    
    def _on_closing(self):
        """Handle window closing"""
        # Save window geometry
        if self.preferences:
            geometry = self.root.geometry()
            self.preferences.set('window_geometry', geometry)
            self.preferences.save_preferences()
        
        self.root.destroy()
    
    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()
