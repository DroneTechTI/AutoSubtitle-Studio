"""
Subtitle preview and editing window
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SubtitlePreviewWindow:
    """Window for previewing and editing subtitles"""
    
    def __init__(self, parent, subtitle_path, controller):
        self.parent = parent
        self.subtitle_path = Path(subtitle_path)
        self.controller = controller
        self.segments = []
        self.modified = False
        
        self.window = tk.Toplevel(parent)
        self.window.title(f"Anteprima - {self.subtitle_path.name}")
        self.window.geometry("1000x700")
        
        self._load_subtitles()
        self._setup_ui()
        
    def _load_subtitles(self):
        """Load subtitle file"""
        try:
            with open(self.subtitle_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse SRT format
            if self.subtitle_path.suffix == '.srt':
                self.segments = self._parse_srt(content)
            elif self.subtitle_path.suffix == '.vtt':
                self.segments = self._parse_vtt(content)
            else:
                raise ValueError(f"Formato non supportato: {self.subtitle_path.suffix}")
                
            logger.info(f"Loaded {len(self.segments)} subtitle segments")
            
        except Exception as e:
            logger.error(f"Error loading subtitles: {str(e)}")
            messagebox.showerror("Errore", f"Impossibile caricare i sottotitoli:\n{str(e)}")
            self.window.destroy()
    
    def _parse_srt(self, content):
        """Parse SRT format"""
        segments = []
        blocks = content.strip().split('\n\n')
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                try:
                    # Index
                    index = int(lines[0])
                    
                    # Timecode
                    timecode = lines[1]
                    start, end = timecode.split(' --> ')
                    
                    # Text (may be multiple lines)
                    text = '\n'.join(lines[2:])
                    
                    segments.append({
                        'index': index,
                        'start': start.strip(),
                        'end': end.strip(),
                        'text': text
                    })
                except Exception as e:
                    logger.warning(f"Error parsing SRT block: {str(e)}")
                    
        return segments
    
    def _parse_vtt(self, content):
        """Parse VTT format"""
        segments = []
        lines = content.strip().split('\n')
        
        # Skip WEBVTT header
        start_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('WEBVTT'):
                start_idx = i + 1
                break
        
        blocks = '\n'.join(lines[start_idx:]).strip().split('\n\n')
        
        for idx, block in enumerate(blocks, start=1):
            lines = block.strip().split('\n')
            if len(lines) >= 2:
                try:
                    # First line might be index or timecode
                    if '-->' in lines[0]:
                        timecode = lines[0]
                        text = '\n'.join(lines[1:])
                    elif len(lines) >= 3 and '-->' in lines[1]:
                        timecode = lines[1]
                        text = '\n'.join(lines[2:])
                    else:
                        continue
                    
                    start, end = timecode.split(' --> ')
                    
                    segments.append({
                        'index': idx,
                        'start': start.strip(),
                        'end': end.strip(),
                        'text': text
                    })
                except Exception as e:
                    logger.warning(f"Error parsing VTT block: {str(e)}")
                    
        return segments
    
    def _setup_ui(self):
        """Setup preview UI"""
        # Title
        title_label = ttk.Label(
            self.window,
            text=f"👁 Anteprima: {self.subtitle_path.name}",
            font=('Arial', 12, 'bold')
        )
        title_label.pack(pady=10)
        
        # Info label
        info_label = ttk.Label(
            self.window,
            text=f"Totale segmenti: {len(self.segments)} | Doppio click per modificare",
            foreground='gray'
        )
        info_label.pack()
        
        # Toolbar
        toolbar = ttk.Frame(self.window)
        toolbar.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(
            toolbar,
            text="💾 Salva",
            command=self._save_changes
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            toolbar,
            text="🔍 Cerca",
            command=self._search
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            toolbar,
            text="⏱ Regola Timing",
            command=self._adjust_timing
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            toolbar,
            text="🌐 Traduci",
            command=self._translate
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            toolbar,
            text="📤 Esporta",
            command=self._export
        ).pack(side=tk.LEFT, padx=5)
        
        # Main content frame
        content_frame = ttk.Frame(self.window)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Treeview for subtitles
        columns = ('index', 'start', 'end', 'text')
        self.tree = ttk.Treeview(content_frame, columns=columns, show='headings', height=20)
        
        self.tree.heading('index', text='#')
        self.tree.heading('start', text='Inizio')
        self.tree.heading('end', text='Fine')
        self.tree.heading('text', text='Testo')
        
        self.tree.column('index', width=50)
        self.tree.column('start', width=120)
        self.tree.column('end', width=120)
        self.tree.column('text', width=600)
        
        scrollbar = ttk.Scrollbar(content_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click for editing
        self.tree.bind('<Double-1>', self._edit_segment)
        
        # Populate tree
        self._populate_tree()
        
        # Status bar
        self.status_label = ttk.Label(
            self.window,
            text=f"Pronto | {len(self.segments)} segmenti caricati",
            relief=tk.SUNKEN
        )
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)
        
    def _populate_tree(self):
        """Populate tree with subtitle segments"""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for segment in self.segments:
            # Truncate text for display
            text_preview = segment['text'].replace('\n', ' ')[:80]
            if len(segment['text']) > 80:
                text_preview += '...'
                
            self.tree.insert('', 'end', values=(
                segment['index'],
                segment['start'],
                segment['end'],
                text_preview
            ))
    
    def _edit_segment(self, event):
        """Edit selected segment"""
        selection = self.tree.selection()
        if not selection:
            return
            
        item = selection[0]
        idx = self.tree.index(item)
        
        if idx >= len(self.segments):
            return
            
        segment = self.segments[idx]
        
        # Create edit dialog
        edit_window = tk.Toplevel(self.window)
        edit_window.title(f"Modifica Segmento #{segment['index']}")
        edit_window.geometry("600x400")
        
        # Start time
        ttk.Label(edit_window, text="Inizio:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        start_entry = ttk.Entry(edit_window, width=20)
        start_entry.insert(0, segment['start'])
        start_entry.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        # End time
        ttk.Label(edit_window, text="Fine:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        end_entry = ttk.Entry(edit_window, width=20)
        end_entry.insert(0, segment['end'])
        end_entry.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Text
        ttk.Label(edit_window, text="Testo:").grid(row=2, column=0, sticky=tk.NW, padx=10, pady=5)
        text_widget = scrolledtext.ScrolledText(edit_window, width=50, height=15)
        text_widget.insert(1.0, segment['text'])
        text_widget.grid(row=2, column=1, padx=10, pady=5)
        
        # Save button
        def save_edit():
            self.segments[idx]['start'] = start_entry.get()
            self.segments[idx]['end'] = end_entry.get()
            self.segments[idx]['text'] = text_widget.get(1.0, tk.END).strip()
            self.modified = True
            self._populate_tree()
            edit_window.destroy()
            self.status_label.config(text="✏ Modificato (non salvato)")
        
        ttk.Button(edit_window, text="💾 Salva", command=save_edit).grid(
            row=3, column=0, columnspan=2, pady=10
        )
    
    def _save_changes(self):
        """Save changes to file"""
        if not self.modified:
            messagebox.showinfo("Info", "Nessuna modifica da salvare")
            return
            
        try:
            if self.subtitle_path.suffix == '.srt':
                self._save_srt()
            elif self.subtitle_path.suffix == '.vtt':
                self._save_vtt()
                
            self.modified = False
            self.status_label.config(text="✓ Salvato con successo")
            messagebox.showinfo("Successo", "Modifiche salvate!")
            
        except Exception as e:
            logger.error(f"Error saving: {str(e)}")
            messagebox.showerror("Errore", f"Impossibile salvare:\n{str(e)}")
    
    def _save_srt(self):
        """Save in SRT format"""
        content = []
        for segment in self.segments:
            content.append(str(segment['index']))
            content.append(f"{segment['start']} --> {segment['end']}")
            content.append(segment['text'])
            content.append('')
        
        with open(self.subtitle_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
    
    def _save_vtt(self):
        """Save in VTT format"""
        content = ['WEBVTT', '']
        for segment in self.segments:
            content.append(str(segment['index']))
            content.append(f"{segment['start']} --> {segment['end']}")
            content.append(segment['text'])
            content.append('')
        
        with open(self.subtitle_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
    
    def _search(self):
        """Search in subtitles"""
        search_window = tk.Toplevel(self.window)
        search_window.title("Cerca")
        search_window.geometry("400x150")
        
        ttk.Label(search_window, text="Cerca testo:").pack(pady=10)
        search_entry = ttk.Entry(search_window, width=40)
        search_entry.pack(pady=5)
        
        def do_search():
            query = search_entry.get().lower()
            if not query:
                return
                
            # Clear previous selection
            for item in self.tree.selection():
                self.tree.selection_remove(item)
            
            # Search and select matching items
            found = 0
            for idx, segment in enumerate(self.segments):
                if query in segment['text'].lower():
                    item = self.tree.get_children()[idx]
                    self.tree.selection_add(item)
                    if found == 0:  # Scroll to first match
                        self.tree.see(item)
                    found += 1
            
            self.status_label.config(text=f"🔍 Trovati {found} risultati per '{query}'")
        
        ttk.Button(search_window, text="🔍 Cerca", command=do_search).pack(pady=10)
    
    def _adjust_timing(self):
        """Adjust timing for all subtitles"""
        adjust_window = tk.Toplevel(self.window)
        adjust_window.title("Regola Timing")
        adjust_window.geometry("400x200")
        
        ttk.Label(
            adjust_window,
            text="Regola il timing di tutti i sottotitoli",
            font=('Arial', 10, 'bold')
        ).pack(pady=10)
        
        frame = ttk.Frame(adjust_window)
        frame.pack(pady=10)
        
        ttk.Label(frame, text="Sposta di:").grid(row=0, column=0, padx=5)
        offset_var = tk.DoubleVar(value=0.0)
        offset_entry = ttk.Entry(frame, textvariable=offset_var, width=10)
        offset_entry.grid(row=0, column=1, padx=5)
        ttk.Label(frame, text="secondi").grid(row=0, column=2, padx=5)
        
        ttk.Label(
            adjust_window,
            text="(Valori negativi anticipano, positivi ritardano)",
            foreground='gray'
        ).pack()
        
        def apply_offset():
            offset = offset_var.get()
            if offset == 0:
                return
                
            # This is a simplified version - in reality you'd need to parse and modify timestamps
            messagebox.showinfo(
                "Info",
                f"Funzionalità in sviluppo.\nOffset: {offset}s\n"
                "Usa un editor di sottotitoli professionale per modifiche precise del timing."
            )
        
        ttk.Button(adjust_window, text="Applica", command=apply_offset).pack(pady=10)
    
    def _translate(self):
        """Translate subtitles"""
        messagebox.showinfo(
            "Traduzione",
            "Funzionalità di traduzione disponibile nel menu principale.\n"
            "Usa 'Traduci' dopo aver chiuso questa finestra."
        )
    
    def _export(self):
        """Export subtitles in different format"""
        from tkinter import filedialog
        
        new_format = 'vtt' if self.subtitle_path.suffix == '.srt' else 'srt'
        
        new_path = filedialog.asksaveasfilename(
            title="Esporta come",
            defaultextension=f'.{new_format}',
            filetypes=[(f'{new_format.upper()} Files', f'*.{new_format}')]
        )
        
        if new_path:
            try:
                if new_format == 'srt':
                    # Convert to SRT
                    content = []
                    for segment in self.segments:
                        content.append(str(segment['index']))
                        # Convert VTT time to SRT time (. to ,)
                        start = segment['start'].replace('.', ',')
                        end = segment['end'].replace('.', ',')
                        content.append(f"{start} --> {end}")
                        content.append(segment['text'])
                        content.append('')
                    
                    with open(new_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(content))
                else:
                    # Convert to VTT
                    content = ['WEBVTT', '']
                    for segment in self.segments:
                        content.append(str(segment['index']))
                        # Convert SRT time to VTT time (, to .)
                        start = segment['start'].replace(',', '.')
                        end = segment['end'].replace(',', '.')
                        content.append(f"{start} --> {end}")
                        content.append(segment['text'])
                        content.append('')
                    
                    with open(new_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(content))
                
                messagebox.showinfo("Successo", f"Esportato in: {new_path}")
                
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile esportare:\n{str(e)}")
