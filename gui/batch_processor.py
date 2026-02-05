"""
Batch processing window for multiple videos
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
import logging

logger = logging.getLogger(__name__)


class BatchProcessorWindow:
    """Window for batch processing multiple videos"""
    
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.window = tk.Toplevel(parent)
        self.window.title("Elaborazione Batch - Più Video")
        self.window.geometry("800x600")

        self.video_list = []
        self.processing = False
        self.processing_lock = threading.Lock()  # Thread-safe flag protection
        self.current_index = 0
        self.current_cancellation_token = None  # Token for graceful cancellation

        self._setup_ui()
        
    def _setup_ui(self):
        """Setup batch processing UI"""
        # Title
        title_label = ttk.Label(
            self.window,
            text="📂 Elaborazione Batch",
            font=('Arial', 14, 'bold')
        )
        title_label.pack(pady=10)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.window)
        buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(
            buttons_frame,
            text="➕ Aggiungi Video",
            command=self._add_videos
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="🗑 Rimuovi Selezionati",
            command=self._remove_selected
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="🧹 Pulisci Tutti",
            command=self._clear_all
        ).pack(side=tk.LEFT, padx=5)
        
        # Video list frame
        list_frame = ttk.LabelFrame(self.window, text="Video da Elaborare", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Treeview for video list
        columns = ('status', 'name', 'progress')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', height=15)
        
        self.tree.heading('status', text='Stato')
        self.tree.heading('name', text='Nome File')
        self.tree.heading('progress', text='Progresso')
        
        self.tree.column('status', width=100)
        self.tree.column('name', width=400)
        self.tree.column('progress', width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Options frame
        options_frame = ttk.LabelFrame(self.window, text="Opzioni Comuni", padding="10")
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Language
        ttk.Label(options_frame, text="Lingua:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.language_var = tk.StringVar(value=self.controller.config.DEFAULT_LANGUAGE)
        ttk.Combobox(
            options_frame,
            textvariable=self.language_var,
            values=list(self.controller.config.LANGUAGES.keys()),
            state='readonly',
            width=15
        ).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Model
        ttk.Label(options_frame, text="Modello:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.model_var = tk.StringVar(value=self.controller.config.DEFAULT_WHISPER_MODEL)
        ttk.Combobox(
            options_frame,
            textvariable=self.model_var,
            values=self.controller.config.WHISPER_MODELS,
            state='readonly',
            width=15
        ).grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Format
        ttk.Label(options_frame, text="Formato:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.format_var = tk.StringVar(value=self.controller.config.DEFAULT_SUBTITLE_FORMAT)
        ttk.Combobox(
            options_frame,
            textvariable=self.format_var,
            values=self.controller.config.SUBTITLE_FORMATS,
            state='readonly',
            width=15
        ).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Progress frame
        progress_frame = ttk.Frame(self.window)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.overall_progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.overall_progress.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(
            progress_frame,
            text="Pronto. Aggiungi video per iniziare.",
            foreground='green'
        )
        self.status_label.pack()
        
        # Action buttons
        action_frame = ttk.Frame(self.window)
        action_frame.pack(pady=10)
        
        self.start_btn = ttk.Button(
            action_frame,
            text="▶ Elabora Tutti",
            command=self._start_batch,
            width=20
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(
            action_frame,
            text="⏹ Interrompi",
            command=self._stop_batch,
            state='disabled',
            width=20
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            action_frame,
            text="✖ Chiudi",
            command=self.window.destroy,
            width=20
        ).pack(side=tk.LEFT, padx=5)
        
    def _add_videos(self):
        """Add videos to batch list"""
        filetypes = [
            ('Video Files', ' '.join(f'*{ext}' for ext in self.controller.config.SUPPORTED_VIDEO_FORMATS)),
            ('All Files', '*.*')
        ]
        
        files = filedialog.askopenfilenames(
            title="Seleziona video da elaborare",
            filetypes=filetypes
        )
        
        for file in files:
            if file not in [v['path'] for v in self.video_list]:
                video_path = Path(file)
                self.video_list.append({
                    'path': file,
                    'status': 'In attesa',
                    'progress': '0%'
                })
                
                self.tree.insert('', 'end', values=(
                    '⏳ In attesa',
                    video_path.name,
                    '0%'
                ))
        
        self._update_status(f"{len(self.video_list)} video pronti per l'elaborazione")
        
    def _remove_selected(self):
        """Remove selected videos from list"""
        selected = self.tree.selection()
        for item in selected:
            idx = self.tree.index(item)
            if idx < len(self.video_list):
                del self.video_list[idx]
            self.tree.delete(item)
        
        self._update_status(f"{len(self.video_list)} video nella lista")
        
    def _clear_all(self):
        """Clear all videos from list"""
        if messagebox.askyesno("Conferma", "Vuoi rimuovere tutti i video dalla lista?"):
            self.video_list.clear()
            for item in self.tree.get_children():
                self.tree.delete(item)
            self._update_status("Lista svuotata")
            
    def _start_batch(self):
        """Start batch processing"""
        if not self.video_list:
            messagebox.showwarning("Attenzione", "Aggiungi almeno un video prima di iniziare!")
            return

        # Thread-safe flag update
        with self.processing_lock:
            if self.processing:
                logger.warning("Batch processing already running")
                return
            self.processing = True

        # Create cancellation token for this batch
        self.current_cancellation_token = self.controller.create_cancellation_token()

        self.current_index = 0
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')

        thread = threading.Thread(target=self._process_batch, daemon=True)
        thread.start()
        
    def _stop_batch(self):
        """Stop batch processing"""
        if messagebox.askyesno("Conferma", "Vuoi interrompere l'elaborazione batch?"):
            # Request cancellation via token for graceful stop
            if self.current_cancellation_token:
                self.current_cancellation_token.cancel()
                logger.info("Batch cancellation requested via token")

            # Thread-safe flag update
            with self.processing_lock:
                self.processing = False

            self._update_status("Interruzione richiesta...", 'orange')
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            
    def _process_batch(self):
        """Process all videos in batch"""
        from app_controller import OperationCancelledException

        total = len(self.video_list)
        completed = 0
        cancelled = False

        # Monitor memory before starting batch
        mem_manager = self.controller.memory_manager
        initial_mem = mem_manager.get_available_memory()
        logger.info(f"Starting batch with {initial_mem:.0f} MB available memory")

        for idx, video_info in enumerate(self.video_list):
            # Thread-safe check if still processing
            with self.processing_lock:
                if not self.processing:
                    cancelled = True
                    break

            self.current_index = idx
            video_path = video_info['path']

            try:
                # Update status
                self._update_tree_item(idx, '⏳ Elaborazione...', '0%')
                self._update_status(f"Elaborazione {idx + 1}/{total}: {Path(video_path).name}", 'blue')

                # Process video with cancellation token
                result = self.controller.generate_subtitles(
                    video_path=video_path,
                    language=self.language_var.get(),
                    output_format=self.format_var.get(),
                    model_name=self.model_var.get(),
                    progress_callback=lambda msg: self._log_progress(idx, msg),
                    cancellation_token=self.current_cancellation_token
                )

                if result:
                    self._update_tree_item(idx, '✓ Completato', '100%')
                    completed += 1
                else:
                    self._update_tree_item(idx, '✗ Fallito', '-')

            except OperationCancelledException:
                logger.info(f"Video {idx + 1} cancelled by user")
                self._update_tree_item(idx, '⚠️ Annullato', '-')
                cancelled = True
                break

            except Exception as e:
                logger.error(f"Error processing {video_path}: {str(e)}")
                self._update_tree_item(idx, f'✗ Errore: {str(e)[:30]}', '-')

            # Check memory after each video and warn if low
            current_mem = mem_manager.get_available_memory()
            if current_mem < 1000:  # Less than 1GB
                logger.warning(f"Low memory warning: {current_mem:.0f} MB available")
                self._update_status(f"⚠️ Memoria bassa ({current_mem:.0f} MB) - continuo...", 'orange')

                # Force garbage collection to free memory
                mem_manager.force_garbage_collection()
                current_mem = mem_manager.get_available_memory()
                logger.info(f"After GC: {current_mem:.0f} MB available")

            # Update overall progress
            progress = ((idx + 1) / total) * 100
            self.overall_progress['value'] = progress

        # Final status update
        with self.processing_lock:
            self.processing = False

        if cancelled:
            self._update_status(f"⚠️ Elaborazione interrotta ({completed}/{total} completati)", 'orange')
        else:
            self._update_status(f"✓ Elaborazione completata! ({completed}/{total} successi)", 'green')
            if completed == total:
                messagebox.showinfo("Completato", f"Elaborati tutti i {total} video con successo!")
            else:
                messagebox.showwarning("Completato con errori",
                                     f"Elaborati {completed}/{total} video.\nAlcuni video hanno generato errori.")

        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.current_cancellation_token = None
        
    def _update_tree_item(self, idx, status, progress):
        """Update tree item status"""
        try:
            items = self.tree.get_children()
            if idx < len(items):
                item = items[idx]
                current_values = self.tree.item(item, 'values')
                self.tree.item(item, values=(status, current_values[1], progress))
        except Exception as e:
            logger.error(f"Error updating tree item: {str(e)}")
            
    def _log_progress(self, idx, message):
        """Log progress for specific video"""
        # Extract percentage if present
        if '%' in message or 'completat' in message.lower():
            self._update_tree_item(idx, '⏳ Elaborazione...', message[:20])
            
    def _update_status(self, message, color='black'):
        """Update status label"""
        self.status_label.config(text=message, foreground=color)
