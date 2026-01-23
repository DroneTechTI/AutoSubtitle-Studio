"""
Subtitle Generator - Main Entry Point
Application for automatic subtitle generation and downloading
"""
import sys
import logging
from pathlib import Path

# Setup logging with UTF-8 encoding to handle special characters
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('subtitle_generator.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Import application components
from app_controller import AppController
from gui.main_window import SubtitleGeneratorGUI
from utils.audio_extractor import check_ffmpeg_installed


def check_dependencies():
    """Check if all required dependencies are installed"""
    issues = []
    
    # Check FFmpeg
    logger.info("Checking FFmpeg installation...")
    if not check_ffmpeg_installed():
        issues.append(
            "FFmpeg non trovato!\n"
            "FFmpeg è necessario per estrarre l'audio dai video.\n\n"
            "Installazione:\n"
            "- Windows: Verrà installato automaticamente durante il setup\n"
            "- macOS: brew install ffmpeg\n"
            "- Linux: sudo apt install ffmpeg\n"
        )
    else:
        logger.info("✓ FFmpeg found")
    
    # Check Python version
    if sys.version_info < (3, 8):
        issues.append(
            f"Python {sys.version_info.major}.{sys.version_info.minor} non supportato!\n"
            "È richiesto Python 3.8 o superiore."
        )
    else:
        logger.info(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    return issues


def main():
    """Main application entry point"""
    try:
        logger.info("=" * 60)
        logger.info("Starting Subtitle Generator")
        logger.info("=" * 60)
        
        # Check dependencies
        issues = check_dependencies()
        if issues:
            error_msg = "\n\n".join(issues)
            logger.error(f"Dependency check failed:\n{error_msg}")
            
            # Show error in GUI if possible
            try:
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror(
                    "Errore - Dipendenze Mancanti",
                    error_msg + "\n\nEsegui setup.bat (Windows) o setup.sh (Linux/Mac) per installare le dipendenze."
                )
            except:
                print(error_msg)
            
            return 1
        
        # Initialize application controller
        logger.info("Initializing application...")
        controller = AppController()
        
        # Launch GUI
        logger.info("Starting GUI...")
        gui = SubtitleGeneratorGUI(controller)
        gui.run()
        
        # Cleanup on exit
        logger.info("Application closing...")
        controller.cleanup()
        
        logger.info("Application closed successfully")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        
        # Try to show error dialog
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Errore Fatale",
                f"Si è verificato un errore:\n\n{str(e)}\n\nControlla il file subtitle_generator.log per i dettagli."
            )
        except:
            print(f"Fatal error: {str(e)}")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
