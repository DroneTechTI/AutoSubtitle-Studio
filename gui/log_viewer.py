"""
Log viewer window for displaying application logs
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class LogViewerWindow:
    """Window for viewing and managing application logs"""
    
    def __init__(self, parent, log_file_path="subtitle_generator.log"):
        self.parent = parent
        self.log_file_path = Path(log_file_path)
        self.window = None
        self.auto_refresh = tk.BooleanVar(value=False)
        self.auto_scroll = tk.BooleanVar(value=True)
        self.filter_level = tk.StringVar(value="ALL")
        self.last_position = 0
        
    def show(self):
        """Show the log viewer window"""
        if self.window is not None and self.window.winfo_exists():
            self.window.lift()
            self.window.focus()
            return
        
        self.window = tk.Toplevel(self.parent)
        self.window.title("📋 Visualizza Log - Subtitle Generator")
        self.window.geometry("900x600")
        
        # Make window resizable
        self.window.rowconfigure(1, weight=1)
        self.window.columnconfigure(0, weight=1)
        
        self._create_toolbar()
        self._create_log_display()
        self._create_status_bar()
        
        # Load initial logs
        self.refresh_logs()
        
        # Setup auto-refresh if enabled
        self._schedule_refresh()
        
        logger.info("Log viewer window opened")
    
    def _create_toolbar(self):
        """Create toolbar with controls"""
        toolbar = ttk.Frame(self.window, padding="5")
        toolbar.grid(row=0, column=0, sticky="ew")
        
        # Refresh button
        ttk.Button(
            toolbar,
            text="🔄 Aggiorna",
            command=self.refresh_logs
        ).pack(side=tk.LEFT, padx=2)
        
        # Clear display button
        ttk.Button(
            toolbar,
            text="🗑️ Pulisci Vista",
            command=self.clear_display
        ).pack(side=tk.LEFT, padx=2)
        
        # Export button
        ttk.Button(
            toolbar,
            text="💾 Esporta Log",
            command=self.export_logs
        ).pack(side=tk.LEFT, padx=2)
        
        # Separator
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Filter by level
        ttk.Label(toolbar, text="Filtro:").pack(side=tk.LEFT, padx=2)
        filter_combo = ttk.Combobox(
            toolbar,
            textvariable=self.filter_level,
            values=["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            state="readonly",
            width=10
        )
        filter_combo.pack(side=tk.LEFT, padx=2)
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_logs())
        
        # Separator
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Auto-refresh checkbox
        ttk.Checkbutton(
            toolbar,
            text="Auto-aggiorna",
            variable=self.auto_refresh,
            command=self._schedule_refresh
        ).pack(side=tk.LEFT, padx=2)
        
        # Auto-scroll checkbox
        ttk.Checkbutton(
            toolbar,
            text="Auto-scroll",
            variable=self.auto_scroll
        ).pack(side=tk.LEFT, padx=2)
        
        # Open log file button
        ttk.Button(
            toolbar,
            text="📂 Apri File",
            command=self.open_log_file
        ).pack(side=tk.RIGHT, padx=2)
    
    def _create_log_display(self):
        """Create log display area"""
        frame = ttk.Frame(self.window)
        frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        
        # Create scrolled text widget
        self.log_text = scrolledtext.ScrolledText(
            frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
            selectbackground="#264f78"
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        # Configure text tags for different log levels
        self.log_text.tag_config("DEBUG", foreground="#608b4e")
        self.log_text.tag_config("INFO", foreground="#4fc1ff")
        self.log_text.tag_config("WARNING", foreground="#dcdcaa")
        self.log_text.tag_config("ERROR", foreground="#f48771")
        self.log_text.tag_config("CRITICAL", foreground="#ff0000", background="#400000")
        self.log_text.tag_config("TIMESTAMP", foreground="#858585")
        
        # Make read-only
        self.log_text.config(state=tk.DISABLED)
    
    def _create_status_bar(self):
        """Create status bar"""
        self.status_bar = ttk.Label(
            self.window,
            text="Pronto",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.grid(row=2, column=0, sticky="ew")
    
    def refresh_logs(self):
        """Refresh log display from file"""
        try:
            if not self.log_file_path.exists():
                self._update_status("File di log non trovato")
                return
            
            # Read log file
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Apply filter
            filter_level = self.filter_level.get()
            if filter_level != "ALL":
                filtered_lines = []
                for line in lines:
                    if filter_level in line:
                        filtered_lines.append(line)
                lines = filtered_lines
            
            # Update display
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            
            for line in lines:
                self._insert_colored_line(line)
            
            self.log_text.config(state=tk.DISABLED)
            
            # Auto-scroll to bottom
            if self.auto_scroll.get():
                self.log_text.see(tk.END)
            
            # Update status
            line_count = len(lines)
            file_size = self.log_file_path.stat().st_size / 1024  # KB
            self._update_status(f"{line_count} righe | {file_size:.1f} KB | Aggiornato: {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"Error refreshing logs: {str(e)}")
            self._update_status(f"Errore: {str(e)}")
    
    def _insert_colored_line(self, line):
        """Insert a log line with appropriate coloring"""
        # Detect log level
        level_tag = None
        for level in ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]:
            if level in line:
                level_tag = level
                break
        
        # Insert with color
        if level_tag:
            self.log_text.insert(tk.END, line, level_tag)
        else:
            self.log_text.insert(tk.END, line)
    
    def clear_display(self):
        """Clear the log display (not the file)"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self._update_status("Vista pulita")
    
    def export_logs(self):
        """Export logs to a file"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="Esporta Log",
                defaultextension=".txt",
                filetypes=[
                    ("File di testo", "*.txt"),
                    ("Tutti i file", "*.*")
                ],
                initialfile=f"log_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            
            if file_path:
                # Get current display content
                content = self.log_text.get(1.0, tk.END)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                messagebox.showinfo(
                    "Esportazione Completata",
                    f"Log esportato con successo in:\n{file_path}"
                )
                self._update_status(f"Log esportato: {Path(file_path).name}")
                
        except Exception as e:
            logger.error(f"Error exporting logs: {str(e)}")
            messagebox.showerror("Errore", f"Errore durante l'esportazione:\n{str(e)}")
    
    def open_log_file(self):
        """Open log file with default system editor"""
        try:
            import os
            import platform
            
            if not self.log_file_path.exists():
                messagebox.showwarning("File non trovato", "File di log non trovato")
                return
            
            system = platform.system()
            
            if system == "Windows":
                os.startfile(str(self.log_file_path))
            elif system == "Darwin":  # macOS
                os.system(f"open '{self.log_file_path}'")
            else:  # Linux
                os.system(f"xdg-open '{self.log_file_path}'")
            
            self._update_status("File di log aperto nell'editor esterno")
            
        except Exception as e:
            logger.error(f"Error opening log file: {str(e)}")
            messagebox.showerror("Errore", f"Impossibile aprire il file:\n{str(e)}")
    
    def _schedule_refresh(self):
        """Schedule automatic refresh"""
        if self.auto_refresh.get() and self.window and self.window.winfo_exists():
            self.refresh_logs()
            self.window.after(2000, self._schedule_refresh)  # Refresh every 2 seconds
    
    def _update_status(self, message):
        """Update status bar message"""
        self.status_bar.config(text=message)
    
    def close(self):
        """Close the log viewer window"""
        if self.window:
            self.window.destroy()
            self.window = None
