"""
Sync tester window - test subtitle synchronization before embedding
"""
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import logging
import subprocess
import sys

logger = logging.getLogger(__name__)


class SyncTesterWindow:
    """Window for testing subtitle synchronization"""
    
    def __init__(self, parent, video_path, subtitle_path, offset):
        self.parent = parent
        self.video_path = Path(video_path)
        self.subtitle_path = Path(subtitle_path)
        self.offset = offset
        
        self.window = tk.Toplevel(parent)
        self.window.title("Test Sincronizzazione")
        self.window.geometry("600x400")
        
        self.result = None  # Will be 'accept', 'adjust', or 'cancel'
        self.adjustment = tk.DoubleVar(value=0.0)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup tester UI"""
        # Title
        title_label = ttk.Label(
            self.window,
            text="🧪 Test Sincronizzazione",
            font=('Arial', 14, 'bold')
        )
        title_label.pack(pady=10)
        
        # Info frame
        info_frame = ttk.LabelFrame(self.window, text="Informazioni", padding="10")
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(info_frame, text=f"Video: {self.video_path.name}", font=('Arial', 9)).pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text=f"Sottotitoli: {self.subtitle_path.name}", font=('Arial', 9)).pack(anchor=tk.W, pady=2)
        
        # Offset info with explanation
        offset_frame = ttk.Frame(info_frame)
        offset_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(offset_frame, text="Offset calcolato:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        
        offset_color = 'green' if abs(self.offset) < 0.5 else 'blue' if abs(self.offset) < 2 else 'orange'
        offset_label = ttk.Label(
            offset_frame,
            text=f"{self.offset:+.2f} secondi",
            font=('Arial', 10, 'bold'),
            foreground=offset_color
        )
        offset_label.pack(side=tk.LEFT, padx=10)
        
        # Explanation
        if self.offset > 0:
            explanation = f"I sottotitoli verranno RITARDATI di {self.offset:.2f}s"
        elif self.offset < 0:
            explanation = f"I sottotitoli verranno ANTICIPATI di {abs(self.offset):.2f}s"
        else:
            explanation = "I sottotitoli sono già perfettamente sincronizzati!"
        
        ttk.Label(
            info_frame,
            text=explanation,
            font=('Arial', 9),
            foreground='gray'
        ).pack(anchor=tk.W, pady=5)
        
        # Test instructions
        test_frame = ttk.LabelFrame(self.window, text="Come Testare", padding="10")
        test_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        instructions = (
            "1. Clicca 'Apri con VLC' per guardare il video\n"
            "2. Nel player, attiva i sottotitoli dal menu\n"
            "3. Controlla se sono sincronizzati con le voci\n"
            "4. Se sono perfetti: click 'Accetta'\n"
            "5. Se servono regolazioni: usa 'Regolazione Fine' sotto"
        )
        
        ttk.Label(
            test_frame,
            text=instructions,
            font=('Arial', 9),
            justify=tk.LEFT
        ).pack(pady=10)
        
        ttk.Button(
            test_frame,
            text="🎬 Apri con VLC (con sottotitoli)",
            command=self._open_with_vlc
        ).pack(pady=10)
        
        ttk.Label(
            test_frame,
            text="(Se VLC non si apre automaticamente, aprilo manualmente\n"
                 "e carica video + sottotitoli)",
            font=('Arial', 8),
            foreground='gray'
        ).pack()
        
        # Fine adjustment frame
        adjust_frame = ttk.LabelFrame(self.window, text="Regolazione Fine (opzionale)", padding="10")
        adjust_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(
            adjust_frame,
            text="Se serve un piccolo aggiustamento:",
            font=('Arial', 9)
        ).pack(anchor=tk.W)
        
        adj_control = ttk.Frame(adjust_frame)
        adj_control.pack(fill=tk.X, pady=5)
        
        ttk.Label(adj_control, text="Aggiusta di:").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(
            adj_control,
            from_=-5,
            to=5,
            increment=0.1,
            textvariable=self.adjustment,
            width=10
        ).pack(side=tk.LEFT, padx=5)
        ttk.Label(adj_control, text="secondi").pack(side=tk.LEFT, padx=5)
        
        ttk.Label(
            adjust_frame,
            text="(+valore = ritarda | -valore = anticipa)",
            font=('Arial', 8),
            foreground='gray'
        ).pack()
        
        # Buttons
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(
            button_frame,
            text="✓ Accetta e Integra",
            command=self._accept
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="🔧 Applica Regolazione",
            command=self._adjust
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="✗ Annulla",
            command=self._cancel
        ).pack(side=tk.LEFT, padx=5)
    
    def _open_with_vlc(self):
        """Open video with VLC and load subtitles"""
        try:
            # Try to find VLC
            vlc_paths = [
                r"C:\Program Files\VideoLAN\VLC\vlc.exe",
                r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
                "/usr/bin/vlc",
                "/Applications/VLC.app/Contents/MacOS/VLC"
            ]
            
            vlc_exe = None
            for path in vlc_paths:
                if Path(path).exists():
                    vlc_exe = path
                    break
            
            if vlc_exe:
                # Open VLC with video and subtitle file
                subprocess.Popen([
                    vlc_exe,
                    str(self.video_path),
                    f"--sub-file={self.subtitle_path}"
                ])
                logger.info(f"Opened VLC with video and subtitles")
            else:
                messagebox.showwarning(
                    "VLC non trovato",
                    "VLC non è stato trovato automaticamente.\n\n"
                    "Apri VLC manualmente e carica:\n"
                    f"Video: {self.video_path}\n"
                    f"Sottotitoli: {self.subtitle_path}"
                )
                
        except Exception as e:
            logger.error(f"Error opening VLC: {str(e)}")
            messagebox.showerror(
                "Errore",
                f"Impossibile aprire VLC:\n{str(e)}\n\n"
                "Apri VLC manualmente e carica video + sottotitoli"
            )
    
    def _accept(self):
        """Accept current offset"""
        final_offset = self.offset + self.adjustment.get()
        self.result = ('accept', final_offset)
        self.window.destroy()
    
    def _adjust(self):
        """Apply fine adjustment"""
        adjustment = self.adjustment.get()
        if adjustment == 0:
            messagebox.showwarning("Attenzione", "Inserisci un valore di regolazione!")
            return
        
        final_offset = self.offset + adjustment
        self.result = ('adjust', final_offset)
        self.window.destroy()
    
    def _cancel(self):
        """Cancel operation"""
        if messagebox.askyesno("Conferma", "Vuoi annullare l'integrazione?"):
            self.result = ('cancel', None)
            self.window.destroy()
    
    def get_result(self):
        """Get user's decision"""
        self.window.wait_window()
        return self.result
