"""
Live sync player - adjust subtitle sync in real-time while watching
"""
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import logging
import subprocess
import time
import tempfile

logger = logging.getLogger(__name__)


class LiveSyncPlayer:
    """Real-time subtitle sync adjustment player"""
    
    def __init__(self, parent, video_path, subtitle_path, initial_offset=0.0):
        self.parent = parent
        self.video_path = Path(video_path)
        self.subtitle_path = Path(subtitle_path)
        self.initial_offset = initial_offset
        self.current_offset = initial_offset
        self.temp_subtitle = None
        self.vlc_process = None
        
        self.window = tk.Toplevel(parent)
        self.window.title("Live Sync Tester")
        self.window.geometry("600x500")
        
        self.offset_var = tk.DoubleVar(value=initial_offset)
        self.auto_apply = tk.BooleanVar(value=True)
        
        self._setup_ui()
        self.window.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _setup_ui(self):
        """Setup player UI"""
        # Title
        title_label = ttk.Label(
            self.window,
            text="🎬 Live Sync Tester",
            font=('Arial', 14, 'bold')
        )
        title_label.pack(pady=10)
        
        # Info
        info_frame = ttk.LabelFrame(self.window, text="File", padding="10")
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(info_frame, text=f"Video: {self.video_path.name}", font=('Arial', 9)).pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Sottotitoli: {self.subtitle_path.name}", font=('Arial', 9)).pack(anchor=tk.W)
        
        # Instructions
        instructions_frame = ttk.LabelFrame(self.window, text="Come Usare", padding="10")
        instructions_frame.pack(fill=tk.X, padx=10, pady=5)
        
        instructions = (
            "1. Click 'Avvia Player' per aprire il video\n"
            "2. Usa i controlli sotto per regolare il sync LIVE\n"
            "3. I sottotitoli si aggiornano in tempo reale\n"
            "4. Quando perfetto: click 'Salva Offset'"
        )
        
        ttk.Label(
            instructions_frame,
            text=instructions,
            font=('Arial', 9),
            justify=tk.LEFT
        ).pack()
        
        # Player control
        player_frame = ttk.LabelFrame(self.window, text="Player", padding="10")
        player_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.start_button = ttk.Button(
            player_frame,
            text="▶ Avvia Player",
            command=self._start_player,
            width=20
        )
        self.start_button.pack(pady=5)
        
        self.stop_button = ttk.Button(
            player_frame,
            text="⏹ Chiudi Player",
            command=self._stop_player,
            state='disabled',
            width=20
        )
        self.stop_button.pack(pady=5)
        
        # Offset control frame
        control_frame = ttk.LabelFrame(self.window, text="Controlli Sync LIVE", padding="10")
        control_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Current offset display
        offset_display = ttk.Frame(control_frame)
        offset_display.pack(fill=tk.X, pady=5)
        
        ttk.Label(offset_display, text="Offset Corrente:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.offset_label = ttk.Label(
            offset_display,
            text=f"{self.initial_offset:+.2f}s",
            font=('Arial', 12, 'bold'),
            foreground='blue'
        )
        self.offset_label.pack(side=tk.LEFT, padx=10)
        
        # Quick adjust buttons
        quick_frame = ttk.LabelFrame(control_frame, text="Regolazione Rapida", padding="5")
        quick_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(quick_frame, text="Anticipa:", font=('Arial', 9)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(quick_frame, text="--1s", command=lambda: self._adjust(-1.0), width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="-0.5s", command=lambda: self._adjust(-0.5), width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="-0.1s", command=lambda: self._adjust(-0.1), width=8).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(quick_frame, text="  Ritarda:", font=('Arial', 9)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(quick_frame, text="+0.1s", command=lambda: self._adjust(0.1), width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="+0.5s", command=lambda: self._adjust(0.5), width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="+1s", command=lambda: self._adjust(1.0), width=8).pack(side=tk.LEFT, padx=2)
        
        # Slider for fine control
        slider_frame = ttk.LabelFrame(control_frame, text="Regolazione Fine", padding="5")
        slider_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(slider_frame, text="Usa lo slider per regolazioni precise:", font=('Arial', 9)).pack()
        
        self.offset_slider = ttk.Scale(
            slider_frame,
            from_=-10,
            to=10,
            variable=self.offset_var,
            orient=tk.HORIZONTAL,
            command=self._on_slider_change
        )
        self.offset_slider.pack(fill=tk.X, padx=10, pady=5)
        
        slider_labels = ttk.Frame(slider_frame)
        slider_labels.pack(fill=tk.X, padx=10)
        
        ttk.Label(slider_labels, text="-10s", font=('Arial', 8)).pack(side=tk.LEFT)
        ttk.Label(slider_labels, text="0s", font=('Arial', 8)).pack(side=tk.LEFT, expand=True)
        ttk.Label(slider_labels, text="+10s", font=('Arial', 8)).pack(side=tk.RIGHT)
        
        # Auto-apply checkbox
        ttk.Checkbutton(
            control_frame,
            text="🔄 Applica automaticamente (aggiorna player in tempo reale)",
            variable=self.auto_apply
        ).pack(pady=5)
        
        ttk.Button(
            control_frame,
            text="🔄 Applica Manualmente",
            command=self._apply_offset
        ).pack(pady=5)
        
        # Reset button
        ttk.Button(
            control_frame,
            text="↺ Reset a Offset Iniziale",
            command=self._reset_offset
        ).pack(pady=5)
        
        # Action buttons
        action_frame = ttk.Frame(self.window)
        action_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(
            action_frame,
            text="💾 Salva Offset",
            command=self._save_offset,
            width=20
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            action_frame,
            text="✗ Annulla",
            command=self._cancel,
            width=20
        ).pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_label = ttk.Label(
            self.window,
            text="Pronto. Avvia il player e regola il sync in tempo reale.",
            foreground='green'
        )
        self.status_label.pack(pady=5)
    
    def _adjust(self, amount):
        """Quick adjust offset by amount"""
        new_offset = self.offset_var.get() + amount
        self.offset_var.set(new_offset)
        self._on_slider_change(new_offset)
    
    def _on_slider_change(self, value):
        """Handle slider change"""
        try:
            offset = float(value)
            self.current_offset = offset
            self.offset_label.config(text=f"{offset:+.2f}s")
            
            if self.auto_apply.get() and self.vlc_process:
                self._apply_offset()
        except:
            pass
    
    def _apply_offset(self):
        """Apply current offset to subtitles and reload player"""
        try:
            offset = self.offset_var.get()
            
            # Create temp subtitle with offset
            from utils.video_processor import VideoProcessor
            processor = VideoProcessor()
            
            self.status_label.config(text=f"Applicando offset {offset:+.2f}s...", foreground='blue')
            
            # Create temporary subtitle
            temp_dir = Path(tempfile.gettempdir())
            temp_sub = temp_dir / f"live_sync_{int(time.time())}.srt"
            
            processor.sync_subtitles(
                self.subtitle_path,
                offset,
                temp_sub
            )
            
            if self.temp_subtitle and self.temp_subtitle.exists():
                try:
                    self.temp_subtitle.unlink()
                except:
                    pass
            
            self.temp_subtitle = temp_sub
            
            # Restart player if running
            if self.vlc_process:
                self._stop_player()
                time.sleep(0.5)
                self._start_player()
            
            self.status_label.config(text=f"✓ Offset applicato: {offset:+.2f}s", foreground='green')
            
        except Exception as e:
            logger.error(f"Error applying offset: {str(e)}")
            self.status_label.config(text=f"✗ Errore: {str(e)}", foreground='red')
    
    def _reset_offset(self):
        """Reset to initial offset"""
        self.offset_var.set(self.initial_offset)
        self._on_slider_change(self.initial_offset)
        if self.auto_apply.get():
            self._apply_offset()
    
    def _start_player(self):
        """Start VLC player"""
        try:
            # Apply current offset first
            self._apply_offset()
            
            # Find VLC
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
            
            if not vlc_exe:
                messagebox.showwarning(
                    "VLC non trovato",
                    "Installa VLC Media Player per usare il Live Sync Tester.\n\n"
                    "Download: https://www.videolan.org/vlc/"
                )
                return
            
            # Start VLC
            subtitle_file = self.temp_subtitle if self.temp_subtitle else self.subtitle_path
            
            self.vlc_process = subprocess.Popen([
                vlc_exe,
                str(self.video_path),
                f"--sub-file={subtitle_file}",
                "--sub-track=0"
            ])
            
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            self.status_label.config(text="▶ Player avviato! Regola il sync mentre guardi.", foreground='blue')
            
        except Exception as e:
            logger.error(f"Error starting player: {str(e)}")
            messagebox.showerror("Errore", f"Impossibile avviare player:\n{str(e)}")
    
    def _stop_player(self):
        """Stop VLC player"""
        try:
            if self.vlc_process:
                self.vlc_process.terminate()
                self.vlc_process = None
            
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.status_label.config(text="⏹ Player fermato.", foreground='gray')
            
        except Exception as e:
            logger.error(f"Error stopping player: {str(e)}")
    
    def _save_offset(self):
        """Save final offset"""
        offset = self.offset_var.get()
        
        if abs(offset - self.initial_offset) < 0.05:
            if not messagebox.askyesno(
                "Conferma",
                "L'offset è quasi uguale a quello iniziale.\n"
                f"Iniziale: {self.initial_offset:+.2f}s\n"
                f"Finale: {offset:+.2f}s\n\n"
                "Vuoi continuare comunque?"
            ):
                return
        
        self._stop_player()
        self.result = ('save', offset)
        self.window.destroy()
    
    def _cancel(self):
        """Cancel"""
        if messagebox.askyesno("Conferma", "Vuoi annullare? Le modifiche andranno perse."):
            self._stop_player()
            self.result = ('cancel', None)
            self.window.destroy()
    
    def _on_closing(self):
        """Handle window closing"""
        self._stop_player()
        
        # Cleanup temp files
        if self.temp_subtitle and self.temp_subtitle.exists():
            try:
                self.temp_subtitle.unlink()
            except:
                pass
        
        if not hasattr(self, 'result'):
            self.result = ('cancel', None)
    
    def get_result(self):
        """Get final offset"""
        self.result = None
        self.window.wait_window()
        return self.result if hasattr(self, 'result') and self.result else ('cancel', None)
