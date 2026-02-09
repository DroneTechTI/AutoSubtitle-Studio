"""
Video tools window for subtitle integration and video processing
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
import logging

logger = logging.getLogger(__name__)


class VideoToolsWindow:
    """Window for video processing tools"""
    
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.window = tk.Toplevel(parent)
        self.window.title("Strumenti Video - Integrazione Sottotitoli")
        self.window.geometry("800x700")
        
        self.video_path = tk.StringVar()
        self.subtitle_path = tk.StringVar()
        self.processing = False
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup video tools UI"""
        # Title
        title_label = ttk.Label(
            self.window,
            text="🎬 Strumenti Video",
            font=('Arial', 14, 'bold')
        )
        title_label.pack(pady=10)
        
        # Video file selection
        video_frame = ttk.LabelFrame(self.window, text="File Video", padding="10")
        video_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Entry(video_frame, textvariable=self.video_path, width=60).pack(side=tk.LEFT, padx=5)
        ttk.Button(video_frame, text="Sfoglia...", command=self._browse_video).pack(side=tk.LEFT, padx=5)
        
        # Subtitle file selection
        subtitle_frame = ttk.LabelFrame(self.window, text="File Sottotitoli", padding="10")
        subtitle_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Entry(subtitle_frame, textvariable=self.subtitle_path, width=60).pack(side=tk.LEFT, padx=5)
        ttk.Button(subtitle_frame, text="Sfoglia...", command=self._browse_subtitle).pack(side=tk.LEFT, padx=5)
        
        # Separator
        ttk.Separator(self.window, orient='horizontal').pack(fill=tk.X, padx=10, pady=15)
        
        # Options notebook
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Tab 1: Embed Subtitles
        embed_frame = ttk.Frame(notebook)
        notebook.add(embed_frame, text="📥 Integra Sottotitoli")
        
        # Soft subtitles (MKV)
        soft_frame = ttk.LabelFrame(embed_frame, text="Sottotitoli Soft (attivabili/disattivabili)", padding="10")
        soft_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(
            soft_frame,
            text="I sottotitoli vengono aggiunti al video come traccia separata.\n"
                 "Puoi attivarli/disattivarli dal player video.\n"
                 "✓ Auto-sincronizzazione automatica prima dell'integrazione!",
            foreground='gray'
        ).pack(pady=5)
        
        # Auto-sync option
        self.auto_sync_before_embed = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            soft_frame,
            text="🤖 Sincronizza automaticamente prima di integrare",
            variable=self.auto_sync_before_embed
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        # Test sync option with radio buttons
        self.test_mode = tk.StringVar(value='live')
        
        test_frame = ttk.Frame(soft_frame)
        test_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(test_frame, text="Test Sync:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        
        ttk.Radiobutton(
            test_frame,
            text="🎮 Live (regola mentre guardi)",
            variable=self.test_mode,
            value='live'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            test_frame,
            text="🧪 Semplice (accetta/rifiuta)",
            variable=self.test_mode,
            value='simple'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            test_frame,
            text="⚡ Nessuno (veloce)",
            variable=self.test_mode,
            value='none'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(soft_frame, text="Lingua:").pack(anchor=tk.W, padx=10)
        self.soft_lang = tk.StringVar(value='ita')
        lang_combo = ttk.Combobox(
            soft_frame,
            textvariable=self.soft_lang,
            values=['ita', 'eng', 'spa', 'fra', 'deu', 'por', 'rus', 'jpn', 'chi'],
            width=10
        )
        lang_combo.pack(anchor=tk.W, padx=10, pady=5)
        
        ttk.Button(
            soft_frame,
            text="✨ Integra Soft (Consigliato)",
            command=self._embed_soft,
            width=30
        ).pack(pady=10)
        
        ttk.Label(
            soft_frame,
            text="✓ Formato output: MKV\n✓ Nessuna perdita qualità\n✓ Veloce (2-5 secondi)",
            foreground='green',
            font=('Arial', 9)
        ).pack()
        
        # Hard subtitles
        hard_frame = ttk.LabelFrame(embed_frame, text="Sottotitoli Hard (bruciati nel video)", padding="10")
        hard_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(
            hard_frame,
            text="I sottotitoli vengono bruciati permanentemente nel video.\n"
                 "Sempre visibili, non si possono disattivare.",
            foreground='gray'
        ).pack(pady=5)
        
        options_frame = ttk.Frame(hard_frame)
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(options_frame, text="Dimensione:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.hard_size = tk.IntVar(value=24)
        ttk.Spinbox(options_frame, from_=12, to=48, textvariable=self.hard_size, width=10).grid(row=0, column=1, padx=5)
        
        ttk.Label(options_frame, text="Colore:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.hard_color = tk.StringVar(value='white')
        color_combo = ttk.Combobox(
            options_frame,
            textvariable=self.hard_color,
            values=['white', 'yellow', 'black', 'red', 'green', 'blue'],
            width=10
        )
        color_combo.grid(row=0, column=3, padx=5)
        
        ttk.Label(options_frame, text="Posizione:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.hard_position = tk.StringVar(value='bottom')
        pos_combo = ttk.Combobox(
            options_frame,
            textvariable=self.hard_position,
            values=['bottom', 'top', 'middle'],
            width=10
        )
        pos_combo.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Button(
            hard_frame,
            text="🔥 Brucia Sottotitoli",
            command=self._embed_hard,
            width=30
        ).pack(pady=10)
        
        ttk.Label(
            hard_frame,
            text="⚠ Formato output: MP4\n⚠ Re-encoding video (può richiedere tempo)\n⚠ Sottotitoli permanenti",
            foreground='orange',
            font=('Arial', 9)
        ).pack()
        
        # Tab 2: Extract Subtitles
        extract_frame = ttk.Frame(notebook)
        notebook.add(extract_frame, text="📤 Estrai Sottotitoli")
        
        extract_info = ttk.Label(
            extract_frame,
            text="Estrai sottotitoli già presenti nel video",
            font=('Arial', 10)
        )
        extract_info.pack(pady=20)
        
        ttk.Label(extract_frame, text="Traccia sottotitoli (0 = prima):").pack(pady=5)
        self.extract_track = tk.IntVar(value=0)
        ttk.Spinbox(extract_frame, from_=0, to=10, textvariable=self.extract_track, width=10).pack(pady=5)
        
        ttk.Button(
            extract_frame,
            text="📤 Estrai Sottotitoli",
            command=self._extract_subtitles,
            width=30
        ).pack(pady=20)
        
        # Tab 3: Sync Subtitles
        sync_frame = ttk.Frame(notebook)
        notebook.add(sync_frame, text="⏱ Sincronizza")
        
        sync_info = ttk.Label(
            sync_frame,
            text="Regola il timing dei sottotitoli",
            font=('Arial', 10)
        )
        sync_info.pack(pady=20)
        
        # Auto-sync section
        auto_sync_frame = ttk.LabelFrame(sync_frame, text="Auto-Sincronizzazione Intelligente", padding="10")
        auto_sync_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(
            auto_sync_frame,
            text="Sincronizza automaticamente analizzando l'audio del video.\n"
                 "L'AI rileva le voci e calcola l'offset ottimale.",
            foreground='gray'
        ).pack(pady=5)
        
        ttk.Button(
            auto_sync_frame,
            text="🤖 Auto-Sincronizza (Consigliato)",
            command=self._auto_sync_subtitles,
            width=35
        ).pack(pady=10)
        
        ttk.Label(
            auto_sync_frame,
            text="✓ Usa AI per rilevare pattern vocali\n✓ Calcola offset automaticamente\n✓ Precisione al decimo di secondo",
            foreground='green',
            font=('Arial', 9)
        ).pack()
        
        ttk.Separator(sync_frame, orient='horizontal').pack(fill=tk.X, padx=10, pady=15)
        
        # Manual sync section
        manual_sync_frame = ttk.LabelFrame(sync_frame, text="Sincronizzazione Manuale", padding="10")
        manual_sync_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(
            manual_sync_frame,
            text="Conosci già l'offset? Inseriscilo manualmente:",
            foreground='gray'
        ).pack(pady=5)
        
        offset_frame = ttk.Frame(manual_sync_frame)
        offset_frame.pack(pady=10)
        
        ttk.Label(offset_frame, text="Offset (secondi):").pack(side=tk.LEFT, padx=5)
        self.sync_offset = tk.DoubleVar(value=0.0)
        ttk.Spinbox(
            offset_frame,
            from_=-60,
            to=60,
            increment=0.5,
            textvariable=self.sync_offset,
            width=10
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(
            manual_sync_frame,
            text="Positivo = ritarda | Negativo = anticipa",
            foreground='gray',
            font=('Arial', 9)
        ).pack(pady=5)
        
        ttk.Button(
            manual_sync_frame,
            text="⏱ Applica Offset Manuale",
            command=self._sync_subtitles,
            width=30
        ).pack(pady=10)
        
        # Tab 4: Video Info
        info_frame = ttk.Frame(notebook)
        notebook.add(info_frame, text="ℹ Info Video")
        
        ttk.Button(
            info_frame,
            text="🔍 Analizza Video",
            command=self._show_video_info,
            width=30
        ).pack(pady=20)
        
        self.info_text = tk.Text(info_frame, height=20, width=70, wrap=tk.WORD)
        self.info_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(self.window, text="Stato", padding="10")
        progress_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(
            progress_frame,
            text="Pronto. Seleziona video e sottotitoli.",
            foreground='green'
        )
        self.status_label.pack(pady=5)
        
        # Close button
        ttk.Button(
            self.window,
            text="✖ Chiudi",
            command=self.window.destroy
        ).pack(pady=10)
    
    def _browse_video(self):
        """Browse for video file"""
        filetypes = [
            ('Video Files', '*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.webm'),
            ('All Files', '*.*')
        ]
        filename = filedialog.askopenfilename(title="Seleziona Video", filetypes=filetypes)
        if filename:
            self.video_path.set(filename)
    
    def _browse_subtitle(self):
        """Browse for subtitle file"""
        filetypes = [
            ('Subtitle Files', '*.srt *.vtt'),
            ('All Files', '*.*')
        ]
        filename = filedialog.askopenfilename(title="Seleziona Sottotitoli", filetypes=filetypes)
        if filename:
            self.subtitle_path.set(filename)
    
    def _embed_soft(self):
        """Embed soft subtitles"""
        if not self._validate_files():
            return
        
        self.processing = True
        self.progress_bar.start(10)
        
        def process():
            try:
                from utils.video_processor import VideoProcessor
                from utils.auto_sync import AutoSync
                import tempfile
                
                subtitle_path = self.subtitle_path.get()
                
                offset = 0.0
                
                # Auto-sync if enabled
                if self.auto_sync_before_embed.get():
                    self.status_label.config(text="🤖 Auto-sincronizzazione in corso...", foreground='blue')
                    
                    try:
                        auto_sync = AutoSync()
                        synced_path, offset = auto_sync.auto_sync_subtitles(
                            subtitle_path,
                            self.video_path.get()
                        )
                        
                        if abs(offset) > 0.1:
                            subtitle_path = str(synced_path)
                            
                            # Test sync based on mode
                            test_mode = self.test_mode.get()
                            
                            if test_mode != 'none':
                                self.progress_bar.stop()
                                
                                if test_mode == 'live':
                                    # Live sync player
                                    self.status_label.config(text="🎮 Live Sync Tester...", foreground='blue')
                                    
                                    from gui.live_sync_player import LiveSyncPlayer
                                    live_player = LiveSyncPlayer(
                                        self.window,
                                        self.video_path.get(),
                                        subtitle_path,
                                        offset
                                    )
                                    result = live_player.get_result()
                                    
                                    if result[0] == 'cancel':
                                        self.status_label.config(text="✗ Operazione annullata", foreground='orange')
                                        return
                                    elif result[0] == 'save':
                                        # Apply final offset from live testing
                                        final_offset = result[1]
                                        if abs(final_offset - offset) > 0.05:
                                            from utils.video_processor import VideoProcessor
                                            processor = VideoProcessor()
                                            subtitle_path = str(processor.sync_subtitles(
                                                self.subtitle_path.get(),
                                                final_offset
                                            ))
                                            offset = final_offset
                                
                                elif test_mode == 'simple':
                                    # Simple tester
                                    self.status_label.config(text="🧪 Test sincronizzazione...", foreground='blue')
                                    
                                    from gui.sync_tester import SyncTesterWindow
                                    tester = SyncTesterWindow(
                                        self.window,
                                        self.video_path.get(),
                                        subtitle_path,
                                        offset
                                    )
                                    result = tester.get_result()
                                    
                                    if result[0] == 'cancel':
                                        self.status_label.config(text="✗ Operazione annullata", foreground='orange')
                                        return
                                    elif result[0] == 'adjust':
                                        from utils.video_processor import VideoProcessor
                                        processor = VideoProcessor()
                                        final_adjustment = result[1] - offset
                                        if abs(final_adjustment) > 0.05:
                                            subtitle_path = str(processor.sync_subtitles(
                                                subtitle_path,
                                                final_adjustment
                                            ))
                                            offset = result[1]
                                
                                self.progress_bar.start(10)
                            
                            self.status_label.config(
                                text=f"✓ Sincronizzati (offset: {offset:.2f}s). Integrazione...", 
                                foreground='blue'
                            )
                        else:
                            self.status_label.config(text="✓ Già sincronizzati. Integrazione...", foreground='blue')
                            
                    except Exception as e:
                        logger.warning(f"Auto-sync failed, proceeding without: {str(e)}")
                        self.status_label.config(text="⚠ Auto-sync fallito, continuo senza. Integrazione...", foreground='orange')
                
                else:
                    self.status_label.config(text="Integrazione sottotitoli soft in corso...", foreground='blue')
                
                # Embed subtitles
                processor = VideoProcessor()
                result = processor.embed_subtitles_soft(
                    self.video_path.get(),
                    subtitle_path,
                    language=self.soft_lang.get()
                )
                
                self.progress_bar.stop()
                self.status_label.config(text="✓ Completato!", foreground='green')
                
                message = f"Sottotitoli integrati con successo!\n\n{result}\n\n"
                message += "Puoi attivarli/disattivarli dal player video."
                
                if self.auto_sync_before_embed.get() and abs(offset) > 0.1:
                    message += f"\n\n✓ Auto-sincronizzati (offset: {offset:.1f}s)"
                
                messagebox.showinfo("Successo", message)
                
            except Exception as e:
                self.progress_bar.stop()
                self.status_label.config(text=f"✗ Errore: {str(e)}", foreground='red')
                messagebox.showerror("Errore", str(e))
            finally:
                self.processing = False
        
        threading.Thread(target=process, daemon=True).start()
    
    def _embed_hard(self):
        """Embed hard subtitles"""
        if not self._validate_files():
            return
        
        if not messagebox.askyesno(
            "Conferma",
            "Bruciare i sottotitoli nel video richiede tempo\n"
            "(può richiedere diversi minuti).\n\n"
            "I sottotitoli saranno permanenti e sempre visibili.\n\n"
            "Continuare?"
        ):
            return
        
        self.processing = True
        self.progress_bar.start(10)
        self.status_label.config(text="Bruciatura sottotitoli in corso (può richiedere tempo)...", foreground='blue')
        
        def process():
            try:
                from utils.video_processor import VideoProcessor
                processor = VideoProcessor()
                
                result = processor.embed_subtitles_hard(
                    self.video_path.get(),
                    self.subtitle_path.get(),
                    font_size=self.hard_size.get(),
                    font_color=self.hard_color.get(),
                    position=self.hard_position.get()
                )
                
                self.progress_bar.stop()
                self.status_label.config(text="✓ Completato!", foreground='green')
                messagebox.showinfo(
                    "Successo",
                    f"Sottotitoli bruciati con successo!\n\n{result}"
                )
                
            except Exception as e:
                self.progress_bar.stop()
                self.status_label.config(text=f"✗ Errore: {str(e)}", foreground='red')
                messagebox.showerror("Errore", str(e))
            finally:
                self.processing = False
        
        threading.Thread(target=process, daemon=True).start()
    
    def _extract_subtitles(self):
        """Extract subtitles from video"""
        if not self.video_path.get():
            messagebox.showwarning("Attenzione", "Seleziona un file video!")
            return
        
        self.processing = True
        self.progress_bar.start(10)
        self.status_label.config(text="Estrazione sottotitoli...", foreground='blue')
        
        def process():
            try:
                from utils.video_processor import VideoProcessor
                processor = VideoProcessor()
                
                result = processor.extract_subtitles(
                    self.video_path.get(),
                    track_index=self.extract_track.get()
                )
                
                self.progress_bar.stop()
                self.status_label.config(text="✓ Estratto!", foreground='green')
                messagebox.showinfo("Successo", f"Sottotitoli estratti:\n\n{result}")
                self.subtitle_path.set(str(result))
                
            except Exception as e:
                self.progress_bar.stop()
                self.status_label.config(text=f"✗ Errore: {str(e)}", foreground='red')
                messagebox.showerror("Errore", f"Impossibile estrarre sottotitoli:\n{str(e)}")
            finally:
                self.processing = False
        
        threading.Thread(target=process, daemon=True).start()
    
    def _auto_sync_subtitles(self):
        """Auto-sync subtitles with video"""
        if not self._validate_files():
            return
        
        self.processing = True
        self.progress_bar.start(10)
        self.status_label.config(text="🤖 Analisi audio e sincronizzazione automatica...", foreground='blue')
        
        def process():
            try:
                from utils.auto_sync import AutoSync
                
                auto_sync = AutoSync()
                result, offset = auto_sync.auto_sync_subtitles(
                    self.subtitle_path.get(),
                    self.video_path.get()
                )
                
                self.progress_bar.stop()
                self.status_label.config(text="✓ Auto-sincronizzati!", foreground='green')
                
                message = f"Sottotitoli sincronizzati automaticamente!\n\n"
                message += f"File: {result}\n"
                message += f"Offset applicato: {offset:.1f} secondi\n\n"
                
                if abs(offset) < 0.1:
                    message += "✓ I sottotitoli erano già perfettamente sincronizzati!"
                elif offset > 0:
                    message += f"✓ Ritardati di {offset:.1f}s per sincronizzarli"
                else:
                    message += f"✓ Anticipati di {abs(offset):.1f}s per sincronizzarli"
                
                messagebox.showinfo("Successo", message)
                self.subtitle_path.set(str(result))
                
            except Exception as e:
                self.progress_bar.stop()
                self.status_label.config(text=f"✗ Errore: {str(e)}", foreground='red')
                messagebox.showerror("Errore", f"Impossibile auto-sincronizzare:\n{str(e)}")
            finally:
                self.processing = False
        
        threading.Thread(target=process, daemon=True).start()
    
    def _sync_subtitles(self):
        """Sync subtitle timing manually"""
        if not self.subtitle_path.get():
            messagebox.showwarning("Attenzione", "Seleziona un file sottotitoli!")
            return
        
        try:
            from utils.video_processor import VideoProcessor
            processor = VideoProcessor()
            
            result = processor.sync_subtitles(
                self.subtitle_path.get(),
                self.sync_offset.get()
            )
            
            self.status_label.config(text="✓ Sincronizzato!", foreground='green')
            messagebox.showinfo("Successo", f"Sottotitoli sincronizzati:\n\n{result}")
            self.subtitle_path.set(str(result))
            
        except Exception as e:
            self.status_label.config(text=f"✗ Errore: {str(e)}", foreground='red')
            messagebox.showerror("Errore", str(e))
    
    def _show_video_info(self):
        """Show video information"""
        if not self.video_path.get():
            messagebox.showwarning("Attenzione", "Seleziona un file video!")
            return
        
        try:
            from utils.video_processor import VideoProcessor
            processor = VideoProcessor()
            
            info = processor.get_video_info(self.video_path.get())
            
            # Format info for display
            info_text = f"INFORMAZIONI VIDEO\n{'='*50}\n\n"
            info_text += f"File: {Path(self.video_path.get()).name}\n\n"
            
            if info.get('duration'):
                minutes = int(info['duration'] // 60)
                seconds = int(info['duration'] % 60)
                info_text += f"Durata: {minutes}:{seconds:02d}\n"
            
            if info.get('size'):
                size_mb = info['size'] / (1024 * 1024)
                info_text += f"Dimensione: {size_mb:.2f} MB\n"
            
            info_text += f"Formato: {info.get('format', 'N/A')}\n\n"
            
            if info.get('has_video'):
                info_text += f"VIDEO:\n"
                info_text += f"  Codec: {info.get('video_codec', 'N/A')}\n"
                info_text += f"  Risoluzione: {info.get('width', 0)}x{info.get('height', 0)}\n"
                info_text += f"  FPS: {info.get('fps', 0):.2f}\n\n"
            
            if info.get('has_audio'):
                info_text += f"AUDIO:\n"
                info_text += f"  Codec: {info.get('audio_codec', 'N/A')}\n"
                info_text += f"  Sample Rate: {info.get('sample_rate', 0)} Hz\n\n"
            
            if info.get('has_subtitles'):
                info_text += f"SOTTOTITOLI:\n"
                info_text += f"  Tracce trovate: {info.get('subtitle_count', 0)}\n"
            else:
                info_text += f"SOTTOTITOLI: Nessuna traccia presente\n"
            
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, info_text)
            
            self.status_label.config(text="✓ Info caricate", foreground='green')
            
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile analizzare video:\n{str(e)}")
    
    def _validate_files(self):
        """Validate required files"""
        if not self.video_path.get():
            messagebox.showwarning("Attenzione", "Seleziona un file video!")
            return False
        
        if not self.subtitle_path.get():
            messagebox.showwarning("Attenzione", "Seleziona un file sottotitoli!")
            return False
        
        if not Path(self.video_path.get()).exists():
            messagebox.showerror("Errore", "Il file video non esiste!")
            return False
        
        if not Path(self.subtitle_path.get()).exists():
            messagebox.showerror("Errore", "Il file sottotitoli non esiste!")
            return False
        
        return True
