"""
Memory management utilities to prevent out-of-memory errors
"""
import logging
from typing import Tuple, Dict
import psutil
import gc

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manage memory resources and prevent OOM errors"""
    
    # Memory requirements for Whisper models (in MB)
    WHISPER_MODEL_MEMORY = {
        'tiny': 1000,      # ~1GB
        'base': 1500,      # ~1.5GB
        'small': 2500,     # ~2.5GB
        'medium': 5000,    # ~5GB
        'large': 10000,    # ~10GB
    }
    
    # Safety margin (in MB) to leave for system
    SAFETY_MARGIN_MB = 512  # 512MB safety margin (ragionevole per la maggior parte dei sistemi)
    
    def __init__(self):
        pass
    
    def get_available_memory(self) -> float:
        """
        Get available system memory in MB

        Returns:
            Available memory in MB
        """
        try:
            mem = psutil.virtual_memory()
            available_mb = mem.available / (1024 * 1024)
            return available_mb
        except Exception as e:
            logger.error(f"Error getting memory info: {str(e)}")
            return 0
    
    def get_total_memory(self):
        """
        Get total system memory in MB
        
        Returns:
            Total memory in MB
        """
        try:
            mem = psutil.virtual_memory()
            total_mb = mem.total / (1024 * 1024)
            return total_mb
        except Exception as e:
            logger.error(f"Error getting memory info: {str(e)}")
            return 0
    
    def get_memory_usage_percent(self):
        """
        Get current memory usage percentage
        
        Returns:
            Memory usage percentage (0-100)
        """
        try:
            mem = psutil.virtual_memory()
            return mem.percent
        except Exception as e:
            logger.error(f"Error getting memory usage: {str(e)}")
            return 0
    
    def check_memory_available(self, model_name: str = 'base') -> Tuple[bool, float, int, str]:
        """
        Check if enough memory is available for the specified Whisper model
        
        Args:
            model_name: Whisper model name
        
        Returns:
            Tuple of (is_available, available_mb, required_mb, message)
        """
        required_mb = self.WHISPER_MODEL_MEMORY.get(model_name, 1500)
        available_mb = self.get_available_memory()
        total_mb = self.get_total_memory()
        
        # Add safety margin to required memory
        total_required_mb = required_mb + self.SAFETY_MARGIN_MB
        
        is_available = available_mb >= total_required_mb
        
        if is_available:
            message = (
                f"✓ Memoria sufficiente per il modello '{model_name}'\n"
                f"  Richiesta: ~{required_mb} MB\n"
                f"  Disponibile: {available_mb:.0f} MB\n"
                f"  Totale sistema: {total_mb:.0f} MB"
            )
        else:
            message = (
                f"⚠️ ATTENZIONE: Memoria insufficiente per il modello '{model_name}'\n"
                f"  Richiesta: ~{required_mb} MB (+ {self.SAFETY_MARGIN_MB} MB margine)\n"
                f"  Disponibile: {available_mb:.0f} MB\n"
                f"  Totale sistema: {total_mb:.0f} MB\n"
                f"\n"
                f"SUGGERIMENTI:\n"
                f"  1. Chiudi altre applicazioni per liberare memoria\n"
                f"  2. Usa un modello più piccolo (tiny, base, small)\n"
                f"  3. Riavvia il computer per liberare memoria"
            )
        
        logger.info(f"Memory check for model '{model_name}': "
                   f"Required={required_mb}MB, Available={available_mb:.0f}MB, "
                   f"Result={'OK' if is_available else 'INSUFFICIENT'}")
        
        return is_available, available_mb, required_mb, message
    
    def suggest_best_model(self) -> Tuple[str, str]:
        """
        Suggest the best Whisper model based on available memory
        
        Returns:
            Tuple of (suggested_model, message)
        """
        available_mb = self.get_available_memory()
        
        # Find the largest model that fits in available memory
        models_sorted = sorted(self.WHISPER_MODEL_MEMORY.items(), 
                              key=lambda x: x[1], 
                              reverse=True)
        
        for model_name, required_mb in models_sorted:
            if available_mb >= (required_mb + self.SAFETY_MARGIN_MB):
                message = (
                    f"💡 Modello consigliato: '{model_name}'\n"
                    f"  Basato su memoria disponibile: {available_mb:.0f} MB\n"
                    f"  Requisiti modello: ~{required_mb} MB"
                )
                return model_name, message
        
        # If even tiny doesn't fit, still suggest it with warning
        message = (
            f"⚠️ Memoria molto limitata ({available_mb:.0f} MB)\n"
            f"  Modello consigliato: 'tiny' (minimo)\n"
            f"  ATTENZIONE: Potrebbero verificarsi problemi di memoria"
        )
        return 'tiny', message
    
    def force_garbage_collection(self):
        """
        Force garbage collection to free memory
        
        Returns:
            Number of objects collected
        """
        logger.info("Forcing garbage collection...")
        before_mb = self.get_available_memory()
        
        collected = gc.collect()
        
        after_mb = self.get_available_memory()
        freed_mb = after_mb - before_mb
        
        if freed_mb > 0:
            logger.info(f"Garbage collection freed ~{freed_mb:.0f} MB ({collected} objects)")
        else:
            logger.info(f"Garbage collection completed ({collected} objects)")
        
        return collected
    
    def log_memory_status(self):
        """Log current memory status"""
        try:
            mem = psutil.virtual_memory()
            total_gb = mem.total / (1024 ** 3)
            available_gb = mem.available / (1024 ** 3)
            used_gb = mem.used / (1024 ** 3)
            percent = mem.percent
            
            logger.info("=" * 60)
            logger.info("STATO MEMORIA:")
            logger.info(f"  Totale:      {total_gb:.2f} GB")
            logger.info(f"  Disponibile: {available_gb:.2f} GB")
            logger.info(f"  In uso:      {used_gb:.2f} GB ({percent:.1f}%)")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Error logging memory status: {str(e)}")
    
    def get_memory_info_dict(self) -> Dict[str, float]:
        """
        Get memory information as dictionary
        
        Returns:
            Dictionary with memory information
        """
        try:
            mem = psutil.virtual_memory()
            
            return {
                'total_mb': mem.total / (1024 * 1024),
                'available_mb': mem.available / (1024 * 1024),
                'used_mb': mem.used / (1024 * 1024),
                'percent': mem.percent,
                'total_gb': mem.total / (1024 ** 3),
                'available_gb': mem.available / (1024 ** 3),
                'used_gb': mem.used / (1024 ** 3),
            }
        except Exception as e:
            logger.error(f"Error getting memory info dict: {str(e)}")
            return {}
