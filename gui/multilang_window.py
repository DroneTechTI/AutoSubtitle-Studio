"""
Multi-language subtitle generation window
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class MultiLanguageWindow:
    """Window for generating subtitles in multiple languages"""
    
    def __init__(self, parent, controller, video_path=None):
        """
        Initialize multi-language window
        
        Args:
            parent: Parent window
            controller: Application controller
            video_path: Optional pre-selected video path
        """
        self.parent = parent
        self.controller = controller
        self.video_path = video_path
        self.window = None
        self.is_processing = False
        
        # Language selections
        self.selected_languages = {}
        
    def show(self):
        """Show the multi-language generation window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("🌍 Generazione Multi-Lingua - AutoSubtitle Studio")
        self.window.geometry("700x600")
        
        self._create_ui()
        
        logger.info("Multi-language window opened")
    
    def _create_ui(self):
        """Create the user interface"""
        # Header
        header_frame = ttk.Frame(self.window, padding="10")
        header_frame.pack(fill=tk.X)
        
        ttk.Label(
            header_frame,
            text="🌍 Generazione Sottotitoli Multi-Lingua",
            font=('Arial', 14, 'bold')
        ).pack()
        
        ttk.Label(
            header_frame,
            text="Genera sottotitoli in più lingue contemporaneamente",
            font=('Arial', 9),
            foreground='gray'
        ).pack(pady=5)
        
        # Video selection
        video_frame = ttk.LabelFrame(self.window, text="Video", padding="10")
        video_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.video_path_var = tk.StringVar(value=self.video_path or "")
        
        ttk.Label(video_frame, text="File Video:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        video_entry = ttk.Entry(video_frame, textvariable=self.video_path_var, width=50)
        video_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(
            video_frame,
            text="Sfoglia...",
            command=self._browse_video
        ).grid(row=0, column=2, padx=5, pady=5)
        
        video_frame.columnconfigure(1, weight=1)
        
        # Language selection
        lang_frame = ttk.LabelFrame(self.window, text="Lingue da Generare", padding="10")
        lang_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Quick selection buttons
        quick_frame = ttk.Frame(lang_frame)
        quick_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(quick_frame, text="Selezione rapida:").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            quick_frame,
            text="🇮🇹 IT + 🇬🇧 EN",
            command=lambda: self._quick_select(['it', 'en'])
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            quick_frame,
            text="🇪🇺 Europa",
            command=lambda: self._quick_select(['it', 'en', 'fr', 'de', 'es'])
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            quick_frame,
            text="Seleziona Tutto",
            command=self._select_all
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            quick_frame,
            text="Deseleziona Tutto",
            command=self._deselect_all
        ).pack(side=tk.LEFT, padx=2)
        
        # Language checkboxes in scrollable frame
        canvas = tk.Canvas(lang_frame, height=200)
        scrollbar = ttk.Scrollbar(lang_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Get supported languages
        languages = self.controller.multilang_generator.get_supported_languages()
        
        # Create checkboxes
        row = 0
        col = 0
        for lang_code, lang_name in sorted(languages.items(), key=lambda x: x[1]):
            var = tk.BooleanVar(value=False)
            self.selected_languages[lang_code] = var
            
            # Pre-select IT and EN
            if lang_code in ['it', 'en']:
                var.set(True)
            
            cb = ttk.Checkbutton(
                scrollable_frame,
                text=f"{lang_name} ({lang_code.upper()})",
                variable=var
            )
            cb.grid(row=row, column=col, sticky=tk.W, padx=10, pady=2)
            
            col += 1
            if col >= 3:  # 3 columns
                col = 0
                row += 1
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Options frame
        options_frame = ttk.LabelFrame(self.window, text="Opzioni", padding="10")
        options_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Model selection
        ttk.Label(options_frame, text="Modello Whisper:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.model_var = tk.StringVar(value="base")
        model_combo = ttk.Combobox(
            options_frame,
            textvariable=self.model_var,
            values=self.controller.config.WHISPER_MODELS,
            state='readonly',
            width=15
        )
        model_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Format selection
        ttk.Label(options_frame, text="Formato:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        self.format_var = tk.StringVar(value="srt")
        format_combo = ttk.Combobox(
            options_frame,
            textvariable=self.format_var,
            values=self.controller.config.SUBTITLE_FORMATS,
            state='readonly',
            width=10
        )
        format_combo.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Processing mode
        ttk.Label(options_frame, text="Modalità:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.mode_var = tk.StringVar(value="parallel")
        
        ttk.Radiobutton(
            options_frame,
            text="⚡ Parallela (veloce, usa più RAM)",
            variable=self.mode_var,
            value="parallel"
        ).grid(row=1, column=1, columnspan=2, sticky=tk.W, padx=5, pady=2)
        
        ttk.Radiobutton(
            options_frame,
            text="🔄 Sequenziale (lenta, meno RAM)",
            variable=self.mode_var,
            value="sequential"
        ).grid(row=2, column=1, columnspan=2, sticky=tk.W, padx=5, pady=2)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(self.window, text="Progresso", padding="10")
        progress_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(progress_frame, text="Pronto")
        self.status_label.pack(pady=5)
        
        # Buttons
        button_frame = ttk.Frame(self.window, padding="10")
        button_frame.pack(fill=tk.X)
        
        self.start_button = ttk.Button(
            button_frame,
            text="▶ Genera Sottotitoli",
            command=self._start_generation,
            width=20
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="❌ Chiudi",
            command=self.window.destroy,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        # Estimate time button
        ttk.Button(
            button_frame,
            text="⏱️ Stima Tempo",
            command=self._estimate_time,
            width=15
        ).pack(side=tk.RIGHT, padx=5)
    
    def _browse_video(self):
        """Browse for video file"""
        from tkinter import filedialog
        
        filetypes = [
            ('Video Files', ' '.join(f'*{ext}' for ext in self.controller.config.SUPPORTED_VIDEO_FORMATS)),
            ('All Files', '*.*')
        ]
        
        filename = filedialog.askopenfilename(
            title="Seleziona un file video",
            filetypes=filetypes
        )
        
        if filename:
            self.video_path_var.set(filename)
    
    def _quick_select(self, lang_codes):
        """Quick select specific languages"""
        # Deselect all first
        for var in self.selected_languages.values():
            var.set(False)
        
        # Select requested
        for code in lang_codes:
            if code in self.selected_languages:
                self.selected_languages[code].set(True)
    
    def _select_all(self):
        """Select all languages"""
        for var in self.selected_languages.values():
            var.set(True)
    
    def _deselect_all(self):
        """Deselect all languages"""
        for var in self.selected_languages.values():
            var.set(False)
    
    def _get_selected_languages(self):
        """Get list of selected language codes"""
        return [code for code, var in self.selected_languages.items() if var.get()]
    
    def _estimate_time(self):
        """Estimate processing time"""
        try:
            # Validate video
            if not self.video_path_var.get():
                messagebox.showwarning("Attenzione", "Seleziona un file video!")
                return
            
            video_path = Path(self.video_path_var.get())
            if not video_path.exists():
                messagebox.showerror("Errore", "File video non trovato!")
                return
            
            # Get selected languages
            languages = self._get_selected_languages()
            if not languages:
                messagebox.showwarning("Attenzione", "Seleziona almeno una lingua!")
                return
            
            # Get video duration
            import ffmpeg
            probe = ffmpeg.probe(str(video_path))
            duration = float(probe['format']['duration'])
            
            # Estimate time
            model = self.model_var.get()
            parallel = (self.mode_var.get() == "parallel")
            
            estimated_seconds = self.controller.multilang_generator.estimate_time(
                duration, len(languages), model, parallel
            )
            
            # Format time
            minutes = int(estimated_seconds // 60)
            seconds = int(estimated_seconds % 60)
            
            mode_text = "parallela" if parallel else "sequenziale"
            
            messagebox.showinfo(
                "Stima Tempo di Elaborazione",
                f"Video: {duration/60:.1f} minuti\n"
                f"Lingue: {len(languages)}\n"
                f"Modello: {model}\n"
                f"Modalità: {mode_text}\n"
                f"\n"
                f"⏱️ Tempo stimato: ~{minutes} minuti e {seconds} secondi\n"
                f"\n"
                f"Nota: Questa è una stima approssimativa.\n"
                f"Il tempo effettivo può variare in base al PC."
            )
            
        except Exception as e:
            logger.error(f"Error estimating time: {str(e)}")
            messagebox.showerror("Errore", f"Impossibile stimare il tempo:\n{str(e)}")
    
    def _start_generation(self):
        """Start multi-language subtitle generation"""
        try:
            # Validate video
            if not self.video_path_var.get():
                messagebox.showwarning("Attenzione", "Seleziona un file video!")
                return
            
            video_path = Path(self.video_path_var.get())
            if not video_path.exists():
                messagebox.showerror("Errore", "File video non trovato!")
                return
            
            # Get selected languages
            languages = self._get_selected_languages()
            if not languages:
                messagebox.showwarning("Attenzione", "Seleziona almeno una lingua!")
                return
            
            # Confirm
            lang_list = ", ".join([lang.upper() for lang in languages])
            if not messagebox.askyesno(
                "Conferma",
                f"Generare sottotitoli in {len(languages)} lingue?\n\n"
                f"Lingue: {lang_list}\n"
                f"Video: {video_path.name}\n\n"
                f"Questo potrebbe richiedere diversi minuti."
            ):
                return
            
            # Disable button
            self.start_button.config(state='disabled')
            self.is_processing = True
            
            # Start progress bar
            self.progress_bar.start(10)
            self.status_label.config(text="Generazione in corso...")
            
            # Run in thread
            thread = threading.Thread(
                target=self._generation_thread,
                args=(video_path, languages),
                daemon=True
            )
            thread.start()
            
        except Exception as e:
            logger.error(f"Error starting generation: {str(e)}")
            messagebox.showerror("Errore", str(e))
    
    def _generation_thread(self, video_path, languages):
        """Generation thread"""
        try:
            model = self.model_var.get()
            output_format = self.format_var.get()
            parallel = (self.mode_var.get() == "parallel")
            
            def progress_callback(message):
                self.window.after(0, lambda: self.status_label.config(text=message))
            
            # Generate
            results = self.controller.multilang_generator.generate_multiple_languages(
                video_path=video_path,
                languages=languages,
                model_name=model,
                output_format=output_format,
                progress_callback=progress_callback,
                parallel=parallel
            )
            
            # Update UI in main thread
            self.window.after(0, lambda: self._generation_complete(results))
            
        except Exception as e:
            logger.error(f"Error in generation thread: {str(e)}")
            self.window.after(0, lambda: self._generation_error(str(e)))
    
    def _generation_complete(self, results):
        """Handle generation completion"""
        try:
            self.progress_bar.stop()
            self.start_button.config(state='normal')
            self.is_processing = False
            
            if results:
                result_text = "\n".join([
                    f"• {lang.upper()}: {Path(path).name}"
                    for lang, path in results.items()
                ])
                
                messagebox.showinfo(
                    "✅ Generazione Completata!",
                    f"Sottotitoli generati con successo in {len(results)} lingue:\n\n"
                    f"{result_text}\n\n"
                    f"File salvati in: {self.controller.config.OUTPUT_DIR}"
                )
                
                self.status_label.config(text=f"✅ Completato: {len(results)} lingue")
            else:
                messagebox.showwarning(
                    "Attenzione",
                    "Nessun sottotitolo generato. Controlla i log per dettagli."
                )
                self.status_label.config(text="⚠️ Nessun risultato")
                
        except Exception as e:
            logger.error(f"Error in completion handler: {str(e)}")
    
    def _generation_error(self, error_message):
        """Handle generation error"""
        self.progress_bar.stop()
        self.start_button.config(state='normal')
        self.is_processing = False
        self.status_label.config(text="❌ Errore")
        
        messagebox.showerror(
            "Errore",
            f"Errore durante la generazione:\n\n{error_message}"
        )
