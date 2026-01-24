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
    from utils.preferences_manager import PreferencesManager
    from services.translation_service import TranslationService
except ImportError:
    # For direct execution
    pass


class SubtitleGeneratorGUI:
    """Main application window"""
    
    def __init__(self, app_controller):
        self.controller = app_controller
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
        
        # Trace variables to auto-save preferences
        if self.preferences:
            self.language.trace_add('write', lambda *args: self.preferences.set('language', self.language.get()))
            self.whisper_model.trace_add('write', lambda *args: self.preferences.set('model', self.whisper_model.get()))
            self.subtitle_format.trace_add('write', lambda *args: self.preferences.set('format', self.subtitle_format.get()))
        
        self._setup_ui()
        
        # Save window geometry on close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Apri Video", command=self._browse_video)
        file_menu.add_command(label="File Recenti", command=self._show_recent_files)
        file_menu.add_separator()
        file_menu.add_command(label="Apri Cartella Output", command=self._open_output_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Esci", command=self._on_closing)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Strumenti", menu=tools_menu)
        tools_menu.add_command(label="Batch Processing", command=self._open_batch_processor)
        tools_menu.add_command(label="Integra Video", command=self._open_video_tools)
        tools_menu.add_command(label="Pulisci Sottotitoli", command=self._clean_subtitles)
        tools_menu.add_command(label="Statistiche Sottotitoli", command=self._show_subtitle_stats)
        tools_menu.add_separator()
        tools_menu.add_command(label="Confronta Sottotitoli", command=self._compare_subtitles)
        tools_menu.add_command(label="Unisci Sottotitoli", command=self._merge_subtitles)
        
        # Options menu
        options_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Opzioni", menu=options_menu)
        options_menu.add_command(label="Preferenze", command=self._show_preferences)
        options_menu.add_command(label="Pulisci Cache", command=self._clean_cache)
        options_menu.add_separator()
        options_menu.add_command(label="Verifica FFmpeg", command=self._check_ffmpeg)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aiuto", menu=help_menu)
        help_menu.add_command(label="Guida Rapida", command=self._show_quick_guide)
        help_menu.add_command(label="Shortcuts Tastiera", command=self._show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="Info", command=self._show_about)
        
    def _setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="🎬 Subtitle Generator", 
            font=('Arial', 16, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Video file selection
        ttk.Label(main_frame, text="File Video:", font=('Arial', 10)).grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        
        video_entry = ttk.Entry(main_frame, textvariable=self.video_path, width=50)
        video_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        browse_btn = ttk.Button(main_frame, text="Sfoglia...", command=self._browse_video)
        browse_btn.grid(row=1, column=2, padx=5, pady=5)
        
        # Drag and drop info
        info_label = ttk.Label(
            main_frame, 
            text="💡 Oppure trascina il video qui sopra",
            font=('Arial', 9, 'italic'),
            foreground='gray'
        )
        info_label.grid(row=2, column=0, columnspan=3, pady=2)
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15
        )
        
        # Mode selection
        ttk.Label(main_frame, text="Modalità:", font=('Arial', 10, 'bold')).grid(
            row=4, column=0, sticky=tk.W, pady=5
        )
        
        mode_frame = ttk.Frame(main_frame)
        mode_frame.grid(row=5, column=0, columnspan=3, pady=5)
        
        ttk.Radiobutton(
            mode_frame, 
            text="🤖 Auto-Genera (Intelligenza Artificiale)", 
            variable=self.mode, 
            value="auto",
            command=self._on_mode_change
        ).pack(anchor=tk.W, padx=20)
        
        ttk.Radiobutton(
            mode_frame, 
            text="🌐 Scarica da OpenSubtitles", 
            variable=self.mode, 
            value="download",
            command=self._on_mode_change
        ).pack(anchor=tk.W, padx=20, pady=5)
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15
        )
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Opzioni", padding="10")
        options_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
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
        ttk.Label(options_frame, text="Qualità Modello:").grid(row=2, column=0, sticky=tk.W, pady=5)
        
        self.model_combo = ttk.Combobox(
            options_frame,
            textvariable=self.whisper_model,
            values=self.controller.config.WHISPER_MODELS,
            state='readonly',
            width=15
        )
        self.model_combo.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        model_info = ttk.Label(
            options_frame,
            text="(tiny=veloce, large=migliore qualità)",
            foreground='gray',
            font=('Arial', 8)
        )
        model_info.grid(row=2, column=2, sticky=tk.W, padx=5)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progresso", padding="10")
        progress_frame.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            mode='indeterminate',
            length=400
        )
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.status_label = ttk.Label(
            progress_frame,
            text="Pronto. Seleziona un video per iniziare.",
            foreground='green'
        )
        self.status_label.grid(row=1, column=0, pady=5)
        
        # Log output
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=8,
            width=80,
            state='disabled',
            wrap=tk.WORD
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=10, column=0, columnspan=3, pady=10)
        
        self.start_btn = ttk.Button(
            buttons_frame,
            text="▶ Avvia",
            command=self._start_processing,
            width=15
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.cancel_btn = ttk.Button(
            buttons_frame,
            text="⏹ Annulla",
            command=self._cancel_processing,
            state='disabled',
            width=15
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=5)
        
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
        
        # Second row of buttons
        buttons_frame2 = ttk.Frame(main_frame)
        buttons_frame2.grid(row=11, column=0, columnspan=3, pady=5)
        
        ttk.Button(
            buttons_frame2,
            text="🗑 Pulisci Log",
            command=self._clear_log,
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
        
        # Configure row weights for resizing
        main_frame.rowconfigure(9, weight=1)
        
        # Initial mode setup
        self._on_mode_change()
        
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
    
    def _log(self, message):
        """Add message to log"""
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
    
    def _clear_log(self):
        """Clear log text"""
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
    
    def _update_status(self, message, color='black'):
        """Update status label"""
        self.status_label.config(text=message, foreground=color)
    
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
        
        # Start progress bar
        self.progress_bar.start(10)
        
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
                self._update_status("Download sottotitoli da OpenSubtitles...", 'blue')
                self._log("=== Inizio download sottotitoli ===")
                
                result = self.controller.download_subtitles(
                    video_path=video_path,
                    language=language,
                    progress_callback=self._log
                )
            
            if result:
                self._update_status("✓ Completato con successo!", 'green')
                self._log(f"✓ Sottotitoli salvati in: {result}")
                self.last_subtitle_path = result
                self.preview_btn.config(state='normal')
                
                # Update recent videos in preferences
                if self.preferences:
                    self.preferences.update_last_videos(video_path)
                
                messagebox.showinfo(
                    "Successo", 
                    f"Sottotitoli creati con successo!\n\n{result}"
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
            # Re-enable buttons
            self.progress_bar.stop()
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
        
        output_dir = self.controller.get_output_directory()
        
        try:
            if platform.system() == 'Windows':
                os.startfile(output_dir)
            elif platform.system() == 'Darwin':  # macOS
                os.system(f'open "{output_dir}"')
            else:  # Linux
                os.system(f'xdg-open "{output_dir}"')
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile aprire cartella:\n{str(e)}")
    
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
        """Show recent files menu"""
        if not self.preferences:
            return
        
        recent_window = tk.Toplevel(self.root)
        recent_window.title("File Recenti")
        recent_window.geometry("500x400")
        
        ttk.Label(recent_window, text="📁 File Recenti", font=('Arial', 12, 'bold')).pack(pady=10)
        
        listbox = tk.Listbox(recent_window, height=15)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for video in self.preferences.get_last_videos():
            listbox.insert(tk.END, video)
        
        def load_selected():
            selection = listbox.curselection()
            if selection:
                self.video_path.set(listbox.get(selection[0]))
                recent_window.destroy()
        
        ttk.Button(recent_window, text="Carica", command=load_selected).pack(pady=10)
    
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
